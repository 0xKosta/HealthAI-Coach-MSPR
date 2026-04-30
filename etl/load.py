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


def truncate_all(engine):
    """Vide toutes les tables ETL avant chargement (idempotence par
    re-création complète)."""
    tables = [
        "session_exercises",
        "food_logs",
        "biometric_metrics",
        "workout_sessions",
        "exercises",
        "foods",
        "users",
    ]
    with engine.begin() as conn:
        for t in tables:
            conn.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;"))
    logger.info("toutes les tables ETL ont été tronquées.")


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


def fetch_id_map(engine, table, key_col):
    """Retourne un dict {valeur_clé: id} pour résoudre les FK."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(f'SELECT id, "{key_col}" FROM {table}')
        ).all()
    return {r[1]: r[0] for r in rows}