"""
Scalable Postgres loader.

Strategy:  COPY → STAGING → UPSERT
=================================

For each chunk we:

    1. Create an UNLOGGED staging table that mirrors the target's columns.
       UNLOGGED = no WAL writes → much faster, fine because it's scratch.
    2. Stream the DataFrame via Postgres COPY FROM STDIN. COPY is the
       fastest path to insert bulk data into Postgres — typically 10–50×
       faster than row-by-row INSERT. We pipe pandas → CSV in memory →
       psycopg2.cursor.copy_expert.
    3. Run a single
           INSERT INTO target (...) SELECT ... FROM staging
           ON CONFLICT (<key cols>) DO UPDATE SET <non-key cols> = EXCLUDED.<...>
       which is bulk-set-based AND idempotent.
    4. Drop the staging table.

Why this scales:
    - O(rows in *this chunk*) per run, not O(total dataset)
    - Memory bound by chunk size, not by file size
    - One transaction per chunk → small rollback exposure
    - Target table is never empty (TRUNCATE pattern would cause readers to
      see an empty table mid-load)

Why it's idempotent:
    Same source data → same row keys → ON CONFLICT DO UPDATE leaves the
    target in the same final state regardless of how many times you re-run.

Pre-requisites in init.sql (Role B):
    Each table named in CONFLICT_KEYS must have a matching PRIMARY KEY or
    UNIQUE constraint, otherwise ON CONFLICT raises
    "no unique or exclusion constraint matching the ON CONFLICT specification".
"""

import io
import logging
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from etl import config

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    if not config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure it in .env locally or as "
            "a GitHub Actions secret in CI."
        )
    return create_engine(
        config.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
        # Keep one connection — the pipeline is single-threaded.
        pool_size=1,
        max_overflow=0,
    )


# === COPY helpers ============================================================

def _copy_from_dataframe(conn: Connection, df: pd.DataFrame, target: str) -> int:
    """Stream `df` into `target` via COPY FROM STDIN. Returns row count."""
    if df.empty:
        return 0

    buf = io.StringIO()
    # na_rep='\\N' + NULL '\N' below = unambiguous NULL marker, distinct from
    # legitimate empty strings.
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)

    cols = ", ".join(f'"{c}"' for c in df.columns)
    sql = f"COPY {target} ({cols}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"

    # Get the DBAPI (psycopg2) cursor for copy_expert.
    raw_conn = conn.connection
    with raw_conn.cursor() as cur:
        cur.copy_expert(sql, buf)
    return len(df)


# === Upsert via staging =====================================================

def _upsert_chunk(conn: Connection, df: pd.DataFrame, table: str,
                  keys: list[str]) -> int:
    if df.empty:
        return 0

    staging = f"_stg_{table}"
    cols = list(df.columns)
    col_list = ", ".join(f'"{c}"' for c in cols)
    conflict = ", ".join(f'"{k}"' for k in keys)
    update_cols = [c for c in cols if c not in keys]

    # Staging = same shape as target, but unlogged + temporary
    conn.execute(text(f"DROP TABLE IF EXISTS {staging};"))
    conn.execute(text(
        f"CREATE UNLOGGED TABLE {staging} "
        f"(LIKE {table} INCLUDING DEFAULTS);"
    ))

    _copy_from_dataframe(conn, df, staging)

    if update_cols:
        update_set = ", ".join(
            f'"{c}" = EXCLUDED."{c}"' for c in update_cols
        )
        merge_sql = (
            f"INSERT INTO {table} ({col_list}) "
            f"SELECT {col_list} FROM {staging} "
            f"ON CONFLICT ({conflict}) DO UPDATE SET {update_set};"
        )
    else:
        # All columns are part of the key → nothing meaningful to update on conflict
        merge_sql = (
            f"INSERT INTO {table} ({col_list}) "
            f"SELECT {col_list} FROM {staging} "
            f"ON CONFLICT ({conflict}) DO NOTHING;"
        )
    conn.execute(text(merge_sql))
    conn.execute(text(f"DROP TABLE {staging};"))
    return len(df)


def upsert(engine: Engine, df: pd.DataFrame, table: str) -> int:
    """Upsert one DataFrame into `table`. Wraps the chunk in a transaction."""
    keys = config.CONFLICT_KEYS.get(table)
    if not keys:
        raise ValueError(
            f"No conflict keys defined for table {table!r}. "
            f"Add one in config.CONFLICT_KEYS."
        )
    if df.empty:
        logger.warning(f"[{table}] empty dataframe, skipping load.")
        return 0

    with engine.begin() as conn:
        n = _upsert_chunk(conn, df, table, keys)
    logger.info(f"[{table}] upserted {n} rows.")
    return n


def upsert_stream(engine: Engine, table: str,
                  chunks: Iterable[pd.DataFrame]) -> int:
    """Upsert any iterable of DataFrame chunks into `table`. Returns total rows."""
    total = 0
    for i, df in enumerate(chunks, 1):
        if df.empty:
            continue
        n = upsert(engine, df, table)
        total += n
        logger.debug(f"[{table}] chunk {i}: +{n} (running total {total})")
    return total