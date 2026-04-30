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


def _upsert_chunk(conn, df, table, keys):
    if df.empty:
        return 0

    staging = f"_stg_{table}"
    cols = list(df.columns)
    col_list = ", ".join(f'"{c}"' for c in cols)
    conflict = ", ".join(f'"{k}"' for k in keys)
    update_cols = [c for c in cols if c not in keys]

    # Table de staging temporaire
    conn.execute(text(f"DROP TABLE IF EXISTS {staging};"))
    conn.execute(text(
        f"CREATE UNLOGGED TABLE {staging} (LIKE {table} INCLUDING DEFAULTS);"
    ))

    _copy_from_dataframe(conn, df, staging)

    if update_cols:
        update_set = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)
        merge_sql = (
            f"INSERT INTO {table} ({col_list}) "
            f"SELECT {col_list} FROM {staging} "
            f"ON CONFLICT ({conflict}) DO UPDATE SET {update_set};"
        )
    else:
        merge_sql = (
            f"INSERT INTO {table} ({col_list}) "
            f"SELECT {col_list} FROM {staging} "
            f"ON CONFLICT ({conflict}) DO NOTHING;"
        )
    conn.execute(text(merge_sql))
    conn.execute(text(f"DROP TABLE {staging};"))
    return len(df)


def upsert(engine, df, table):
    keys = config.CONFLICT_KEYS.get(table)
    if not keys:
        raise ValueError(f"Pas de clés définies pour {table!r}.")
    if df.empty:
        logger.warning(f"[{table}] dataframe vide, ignoré.")
        return 0
    with engine.begin() as conn:
        n = _upsert_chunk(conn, df, table, keys)
    logger.info(f"[{table}] {n} lignes upsertées.")
    return n


def upsert_stream(engine, table, chunks):
    total = 0
    for i, df in enumerate(chunks, 1):
        if df.empty:
            continue
        n = upsert(engine, df, table)
        total += n
        logger.debug(f"[{table}] chunk {i}: +{n} (total {total})")
    return total