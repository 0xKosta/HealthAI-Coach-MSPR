"""
End-to-end ETL orchestrator — streaming variant.

Run from the repo root:
    python -m etl.pipeline

Memory profile:
    For each CSV source we hold *one chunk* in RAM at a time
    (default 50 000 rows, configurable via ETL_CHUNK_SIZE).
    ExerciseDB JSON is small and fixed (~1300 entries) → loaded whole.

Per-chunk lifecycle:
    extract chunk → transform chunk → upsert chunk → release memory

Exit codes:
    0  = pipeline completed successfully
    1  = something failed (see logs/etl.log)
"""

import logging
import sys

from etl import config, extract, load, transform


def setup_logging() -> None:
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_exercises(engine) -> transform.QualityReport:
    """ExerciseDB: small fixed file → load whole."""
    df = extract.extract_exercises()
    df_clean, rep = transform.transform_exercises(df)
    load.upsert(engine, df_clean, config.TBL_EXERCISES)
    return rep


def run_gym(engine) -> tuple[transform.QualityReport, int, int]:
    """Gym Members: streamed.

    Per chunk: clean → split into (users, gym_sessions) → upsert each.
    Synthesized user_ids stay unique across chunks via id_offset.
    """
    agg = transform.QualityReport(source="gym_sessions")
    users_total = 0
    sessions_total = 0
    id_offset = 0

    for chunk in extract.extract_gym_chunks():
        rows_in = len(chunk)
        df_clean, rep = transform.transform_gym(chunk, id_offset=id_offset)
        id_offset += rows_in   # next chunk's IDs continue from here

        df_users, df_sessions = transform.split_users_and_sessions(df_clean)

        users_total += load.upsert(engine, df_users, config.TBL_USERS)
        sessions_total += load.upsert(engine, df_sessions, config.TBL_GYM_SESSIONS)

        agg.merge(rep)

    return agg, users_total, sessions_total


def run_nutrition(engine) -> tuple[transform.QualityReport, int]:
    """Daily Nutrition: streamed."""
    agg = transform.QualityReport(source="food_logs")
    total = 0
    for chunk in extract.extract_nutrition_chunks():
        df_clean, rep = transform.transform_nutrition(chunk)
        total += load.upsert(engine, df_clean, config.TBL_FOOD_LOGS)
        agg.merge(rep)
    return agg, total


def main() -> int:
    setup_logging()
    log = logging.getLogger("pipeline")
    log.info("=== ETL pipeline start ===")
    log.info(f"chunk size = {config.CHUNK_SIZE} rows")

    try:
        engine = load.get_engine()

        # Order matters because of FKs: users come from gym, so do gym first
        # if food_logs has an FK to users (Role B's choice — see README).
        ex_rep = run_exercises(engine)
        log.info(ex_rep.summary())

        gym_rep, n_users, n_sessions = run_gym(engine)
        log.info(gym_rep.summary())
        log.info(f"loaded {n_users} users / {n_sessions} gym_sessions")

        nutr_rep, n_food = run_nutrition(engine)
        log.info(nutr_rep.summary())
        log.info(f"loaded {n_food} food_logs")

        log.info("=== ETL pipeline OK ===")
        return 0

    except Exception as e:
        log.exception(f"ETL pipeline FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())