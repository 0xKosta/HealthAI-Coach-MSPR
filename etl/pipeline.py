import logging
import sys

from etl import config, extract, load, transform


def setup_logging():
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run_exercises(engine):
    df = extract.extract_exercises()
    df_clean, rep = transform.transform_exercises(df)
    load.upsert(engine, df_clean, config.TBL_EXERCISES)
    return rep


def run_gym(engine):
    agg = transform.QualityReport(source="gym_sessions")
    users_total = 0
    sessions_total = 0
    id_offset = 0

    for chunk in extract.extract_gym_chunks():
        rows_in = len(chunk)
        df_clean, rep = transform.transform_gym(chunk, id_offset=id_offset)
        id_offset += rows_in

        df_users, df_sessions = transform.split_users_and_sessions(df_clean)
        users_total += load.upsert(engine, df_users, config.TBL_USERS)
        sessions_total += load.upsert(engine, df_sessions, config.TBL_GYM_SESSIONS)

        agg.merge(rep)

    return agg, users_total, sessions_total


def run_nutrition(engine):
    agg = transform.QualityReport(source="food_logs")
    total = 0
    id_offset = 0
    for chunk in extract.extract_nutrition_chunks():
        rows_in = len(chunk)
        df_clean, rep = transform.transform_nutrition(chunk, id_offset=id_offset)
        id_offset += rows_in
        total += load.upsert(engine, df_clean, config.TBL_FOOD_LOGS)
        agg.merge(rep)
    return agg, total


def main():
    setup_logging()
    log = logging.getLogger("pipeline")
    log.info("=== Pipeline ETL: début ===")
    log.info(f"taille des chunks = {config.CHUNK_SIZE}")

    try:
        engine = load.get_engine()

        ex_rep = run_exercises(engine)
        log.info(ex_rep.summary())

        gym_rep, n_users, n_sessions = run_gym(engine)
        log.info(gym_rep.summary())
        log.info(f"{n_users} users / {n_sessions} gym_sessions chargés")

        nutr_rep, n_food = run_nutrition(engine)
        log.info(nutr_rep.summary())
        log.info(f"{n_food} food_logs chargés")

        log.info("=== Pipeline ETL: OK ===")
        return 0

    except Exception as e:
        log.exception(f"Pipeline ETL: ÉCHEC: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())