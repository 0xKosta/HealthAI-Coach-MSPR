import io
import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from etl import config

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL non défini.")
    return create_engine(
        config.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
        pool_size=1,
        max_overflow=0,
    )


def _copy_from_dataframe(conn, df, target):
    if df.empty:
        return 0
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    cols = ", ".join(f'"{c}"' for c in df.columns)
    sql = f"COPY {target} ({cols}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    raw_conn = conn.connection
    with raw_conn.cursor() as cur:
        cur.copy_expert(sql, buf)
    return len(df)


def has_user_auth_rows(engine) -> bool:
    """True si la couche MSPR3 (user_auth) est peuplée — ne pas TRUNCATE users."""
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = 'public' AND table_name = 'user_auth'"
                ")"
            )
        ).scalar()
        if not exists:
            return False
        return conn.execute(text("SELECT COUNT(*) FROM user_auth")).scalar_one() > 0


def truncate_all(engine):
    """Vide les tables ETL avant chargement (idempotence par re-création).

    - exercises : jamais tronquée (upsert + traductions FR).
    - users : jamais tronquée si user_auth contient des lignes (MSPR3 social),
      sinon TRUNCATE users CASCADE comme avant.
    """
    tables = [
        "session_exercises",
        "food_logs",
        "biometric_metrics",
        "workout_sessions",
        "foods",
    ]
    preserve_users = has_user_auth_rows(engine)
    if not preserve_users:
        tables.append("users")

    with engine.begin() as conn:
        for t in tables:
            conn.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;"))
    if preserve_users:
        logger.info(
            "tables ETL tronquées (users et user_auth préservés — comptes sociaux MSPR3)."
        )
    else:
        logger.info("toutes les tables ETL ont été tronquées (exercises préservée).")


def insert(engine, df, table):
    """Insertion simple via COPY. Pas d'upsert : init.sql n'a pas de
    contraintes UNIQUE, donc la stratégie d'idempotence est TRUNCATE + INSERT."""
    if df.empty:
        logger.warning(f"[{table}] dataframe vide, ignoré.")
        return 0
    with engine.begin() as conn:
        n = _copy_from_dataframe(conn, df, table)
    logger.info(f"[{table}] {n} lignes insérées.")
    return n


def insert_users_skip_existing(engine, df, table: str = "users") -> int:
    """Insère uniquement les users dont le name n'existe pas encore (mode MSPR3)."""
    if df.empty:
        return 0
    existing = fetch_id_map(engine, table, "name")
    df_new = df[~df["name"].isin(existing.keys())]
    if df_new.empty:
        logger.info(f"[{table}] aucun nouvel utilisateur (noms déjà en base).")
        return 0
    skipped = len(df) - len(df_new)
    if skipped:
        logger.info(f"[{table}] {skipped} utilisateur(s) ignoré(s) (déjà en base).")
    return insert(engine, df_new, table)


def upsert_exercises(engine, df):
    """Upsert des exercices : met à jour les colonnes EN, préserve les
    colonnes FR existantes (name_fr, type_fr, muscle_group_fr,
    equipment_fr, level_fr, instructions_fr) si déjà renseignées.
    Utilise une table temporaire + INSERT ... ON CONFLICT (name)."""
    if df.empty:
        logger.warning("[exercises] dataframe vide, ignoré.")
        return 0

    fr_cols = ["type_fr", "muscle_group_fr", "equipment_fr", "level_fr"]
    en_cols = ["name", "type", "muscle_group", "equipment", "level",
               "instructions", "gif_url", "video_url", "image_url"]
    all_cols = en_cols + [c for c in fr_cols if c in df.columns]
    df_insert = df[[c for c in all_cols if c in df.columns]].copy()

    cols_sql = ", ".join(f'"{c}"' for c in df_insert.columns)
    update_en = ", ".join(
        f'"{c}" = EXCLUDED."{c}"'
        for c in en_cols if c != "name" and c in df_insert.columns
    )
    # Pour les colonnes FR : on garde la valeur existante si elle est déjà
    # renseignée, sinon on prend celle de l'ETL (issue des maps statiques).
    update_fr = ", ".join(
        f'"{c}" = COALESCE(exercises."{c}", EXCLUDED."{c}")'
        for c in fr_cols if c in df_insert.columns
    )
    updates = ", ".join(filter(None, [update_en, update_fr]))

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TEMP TABLE exercises_staging
            (LIKE exercises INCLUDING DEFAULTS)
            ON COMMIT DROP
        """))
        raw_conn = conn.connection
        buf = __import__("io").StringIO()
        df_insert.to_csv(buf, index=False, header=False, na_rep="\\N")
        buf.seek(0)
        with raw_conn.cursor() as cur:
            cur.copy_expert(
                f"COPY exercises_staging ({cols_sql}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')",
                buf,
            )
        conn.execute(text(f"""
            INSERT INTO exercises ({cols_sql})
            SELECT {cols_sql} FROM exercises_staging
            ON CONFLICT (name) DO UPDATE SET {updates}
        """))

    logger.info(f"[exercises] {len(df_insert)} lignes upsertées (FR préservé).")
    return len(df_insert)


def fetch_id_map(engine, table, key_col):
    """Retourne un dict {valeur_clé: id} pour résoudre les FK."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(f'SELECT id, "{key_col}" FROM {table}')
        ).all()
    return {r[1]: r[0] for r in rows}