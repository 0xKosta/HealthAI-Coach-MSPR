import logging
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl import config, extract, load, simulate, transform

ROOT = Path(__file__).resolve().parent.parent


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
    load.upsert_exercises(engine, df_clean)
    return rep


def run_users_and_workouts(engine):
    rep_users = transform.QualityReport(source="users")
    rep_sess = transform.QualityReport(source="workout_sessions")
    n_users_total = 0
    n_sess_total = 0
    id_offset = 0

    for chunk in extract.extract_gym_chunks():
        rows_in = len(chunk)

        df_users, ru = transform.transform_users(chunk, id_offset=id_offset)
        if load.has_user_auth_rows(engine):
            n_ins = load.insert_users_skip_existing(engine, df_users, config.TBL_USERS)
        else:
            n_ins = load.insert(engine, df_users, config.TBL_USERS)
        n_users_total += n_ins
        rep_users.merge(ru)

        df_sess, rs = transform.transform_workout_sessions(chunk, id_offset=id_offset)

        # name -> user_id
        name_to_id = load.fetch_id_map(engine, config.TBL_USERS, "name")
        df_sess["user_id"] = df_sess["name"].map(name_to_id)
        df_sess = df_sess.dropna(subset=["user_id"])
        df_sess["user_id"] = df_sess["user_id"].astype(int)
        df_sess = df_sess.drop(columns=["name"])

        load.insert(engine, df_sess, config.TBL_WORKOUT_SESSIONS)
        n_sess_total += len(df_sess)
        rep_sess.merge(rs)

        id_offset += rows_in

    return rep_users, rep_sess, n_users_total, n_sess_total


def _ensure_food_users_exist(engine, log):
    """Crée des users génériques pour matcher les food_logs."""
    if not config.NUTRITION_CSV.exists():
        return

    n_nutr = 0
    for chunk in pd.read_csv(config.NUTRITION_CSV,
                              chunksize=config.CHUNK_SIZE,
                              on_bad_lines="warn"):
        n_nutr += len(chunk)

    name_to_id = load.fetch_id_map(engine, config.TBL_USERS, "name")
    existing = len(name_to_id)
    if n_nutr <= existing:
        return

    rows = [{
        "name": f"User_{i+1:06d}",
        "age": 30,
        "gender": "other",
        "weight_kg": 70.0,
        "height_cm": 170.0,
        "bmi": None,
        "body_fat_pct": None,
        "goal": "maintenance",
    } for i in range(existing, n_nutr)]

    df = pd.DataFrame(rows)
    load.insert(engine, df, config.TBL_USERS)
    log.info(f"{len(df)} users génériques créés pour les food_logs.")


def run_foods_and_logs(engine):
    rep_foods = transform.QualityReport(source="foods")
    rep_logs = transform.QualityReport(source="food_logs")
    n_foods_total = 0
    n_logs_total = 0
    id_offset = 0

    all_foods = []
    logs_buffer = []

    for chunk in extract.extract_nutrition_chunks():
        rows_in = len(chunk)

        df_foods, rf = transform.transform_foods(chunk)
        all_foods.append(df_foods)
        rep_foods.merge(rf)

        df_logs, rl = transform.transform_food_logs(chunk, id_offset=id_offset)
        logs_buffer.append(df_logs)
        rep_logs.merge(rl)

        id_offset += rows_in

    if all_foods:
        df_foods_all = pd.concat(all_foods, ignore_index=True)
        before = len(df_foods_all)
        df_foods_all = df_foods_all.drop_duplicates(subset=["name"])
        rep_foods.dropped_duplicates += before - len(df_foods_all)
        load.insert(engine, df_foods_all, config.TBL_FOODS)
        n_foods_total = len(df_foods_all)

    name_to_uid = load.fetch_id_map(engine, config.TBL_USERS, "name")
    food_to_fid = load.fetch_id_map(engine, config.TBL_FOODS, "name")

    for df_logs in logs_buffer:
        if df_logs.empty:
            continue
        df_logs = df_logs.copy()
        df_logs["user_id"] = df_logs["name"].map(name_to_uid)
        df_logs["food_id"] = df_logs["food_name"].map(food_to_fid)
        df_logs = df_logs.dropna(subset=["user_id", "food_id"])
        df_logs["user_id"] = df_logs["user_id"].astype(int)
        df_logs["food_id"] = df_logs["food_id"].astype(int)
        df_logs = df_logs.drop(columns=["name", "food_name"])
        load.insert(engine, df_logs, config.TBL_FOOD_LOGS)
        n_logs_total += len(df_logs)

    return rep_foods, rep_logs, n_foods_total, n_logs_total


def run_session_exercises(engine, log):
    """Données simulées : le dataset Gym n'a pas la liste des exercices par
    session, seulement un type agrégé. On échantillonne dans le catalogue
    exercises selon le workout_type."""
    with engine.connect() as conn:
        workouts = pd.read_sql(
            text("SELECT id, user_id, session_date FROM workout_sessions"),
            conn,
        )
        exercises = pd.read_sql(
            text("SELECT id, type FROM exercises"),
            conn,
        )

    # Récupérer workout_type depuis le CSV brut (non gardé en BDD).
    # Aligné par ordre : N-ième user (par name User_NNNNNN) = N-ième ligne CSV.
    raw_gym = extract.extract_gym()
    raw_gym = raw_gym.reset_index(drop=True)
    raw_gym.columns = [c.strip().lower().replace(" ", "_") for c in raw_gym.columns]
    if "workout_type" not in raw_gym.columns:
        log.warning("workout_type absent du CSV gym, fallback type='strength'")
        raw_gym["workout_type"] = "strength"

    # Joindre via l'ordre user_id : workout_sessions.user_id correspond aux
    # ids users dans l'ordre d'insertion = ordre du CSV.
    # On reconstruit l'index : user_id min + offset = ligne CSV.
    if workouts.empty:
        log.info("aucune workout_session, simulation session_exercises ignorée.")
        return 0
    min_user_id = workouts["user_id"].min()
    workouts["csv_idx"] = workouts["user_id"] - min_user_id
    workouts = workouts[workouts["csv_idx"] < len(raw_gym)]
    workouts["workout_type"] = workouts["csv_idx"].map(
        lambda i: str(raw_gym.iloc[int(i)]["workout_type"]).lower().strip()
    )

    df = simulate.simulate_session_exercises(workouts, exercises)
    if df.empty:
        log.info("session_exercises : aucune ligne à insérer.")
        return 0

    load.insert(engine, df, config.TBL_SESSION_EXERCISES)
    return len(df)


def run_biometric_metrics(engine, log):
    """Données simulées : historique temporel absent du dataset, on génère
    SIM_BIOMETRIC_DAYS jours par user."""
    with engine.connect() as conn:
        users = pd.read_sql(
            text("SELECT id, name, weight_kg FROM users ORDER BY id"),
            conn,
        )

    if users.empty:
        log.info("aucun user, simulation biometric_metrics ignorée.")
        return 0

    raw_gym = extract.extract_gym()
    raw_gym = raw_gym.reset_index(drop=True)
    raw_gym.columns = [c.strip().lower().replace(" ", "_") for c in raw_gym.columns]

    df = simulate.simulate_biometric_metrics(users, raw_gym)
    if df.empty:
        log.info("biometric_metrics : aucune ligne à insérer.")
        return 0

    load.insert(engine, df, config.TBL_BIOMETRIC_METRICS)
    return len(df)


def main():
    setup_logging()
    log = logging.getLogger("pipeline")
    log.info("=== Pipeline ETL: début ===")
    log.info(f"taille des chunks = {config.CHUNK_SIZE}")

    try:
        engine = load.get_engine()

        if load.has_user_auth_rows(engine):
            log.info(
                "user_auth détecté — sauvegarde automatique avant ETL "
                "(users / comptes sociaux non tronqués)."
            )
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "backup_db.py"), "backup"],
                cwd=ROOT,
                check=False,
            )

        # Idempotence : tables ETL vidées ; users préservés si MSPR3 social actif.
        load.truncate_all(engine)

        rep_ex = run_exercises(engine)
        log.info(rep_ex.summary())

        rep_u, rep_s, n_u, n_s = run_users_and_workouts(engine)
        log.info(rep_u.summary())
        log.info(rep_s.summary())
        log.info(f"{n_u} users / {n_s} workout_sessions chargés")

        _ensure_food_users_exist(engine, log)

        rep_f, rep_fl, n_f, n_fl = run_foods_and_logs(engine)
        log.info(rep_f.summary())
        log.info(rep_fl.summary())
        log.info(f"{n_f} foods / {n_fl} food_logs chargés")

        n_se = run_session_exercises(engine, log)
        log.info(f"{n_se} session_exercises simulés et chargés")

        n_bm = run_biometric_metrics(engine, log)
        log.info(f"{n_bm} biometric_metrics simulés et chargés")

        log.info("=== Pipeline ETL: OK ===")
        return 0

    except Exception as e:
        log.exception(f"Pipeline ETL: ÉCHEC: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())