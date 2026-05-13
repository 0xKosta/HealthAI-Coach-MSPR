"""
Simulation des tables sans source de données réelle.

Deux tables ne sont pas alimentables depuis les datasets choisis :
  - session_exercises : le dataset Gym a un type de workout agrégé, pas la
    liste des exercices avec sets/reps.
  - biometric_metrics : le dataset Gym donne un snapshot ; pas d'historique
    temporel.

On simule de manière DÉTERMINISTE (seed par id) pour que les ré-exécutions
produisent les mêmes données — cohérent avec l'idempotence du pipeline.
"""

import logging
import random
from datetime import timedelta

import pandas as pd

from etl import config

logger = logging.getLogger(__name__)


# Correspondance entre le workout_type du dataset Gym et la colonne 'type'
# (= "category" d'ExerciseDB après transform).
_WORKOUT_TO_EXERCISE_TYPE = {
    "cardio": ["cardio"],
    "strength": ["strength", "powerlifting", "olympic weightlifting"],
    "yoga": ["stretching"],
    "hiit": ["cardio", "strength"],
    "weightlifting": ["strength", "powerlifting", "olympic weightlifting"],
    "running": ["cardio"],
    "walking": ["cardio"],
}


def simulate_session_exercises(workouts_df, exercises_df):
    """
    Pour chaque workout_session, sélectionne 3 à 5 exercices du catalogue
    correspondant au type de workout. Sets/reps/duration tirés dans des
    plages réalistes selon le type d'exercice.

    workouts_df : DataFrame avec colonnes 'id' et 'workout_type'
    exercises_df : DataFrame avec colonnes 'id' et 'type'

    Retourne un DataFrame prêt pour insertion dans session_exercises.
    """
    if workouts_df.empty or exercises_df.empty:
        return pd.DataFrame(columns=[
            "session_id", "exercise_id", "sets", "reps", "duration_sec"
        ])

    # Index par type pour pioche rapide
    by_type = {}
    for ex_type, group in exercises_df.groupby("type"):
        by_type[str(ex_type).lower()] = group["id"].tolist()
    all_ids = exercises_df["id"].tolist()

    rows = []
    for _, w in workouts_df.iterrows():
        session_id = int(w["id"])
        wtype = str(w.get("workout_type", "")).lower().strip()

        # Trouver le pool d'exercices candidats
        candidate_types = _WORKOUT_TO_EXERCISE_TYPE.get(wtype, [])
        pool = []
        for t in candidate_types:
            pool.extend(by_type.get(t, []))
        if not pool:
            pool = all_ids  # fallback

        # Seed déterministe : ré-exécution produit le même résultat
        rng = random.Random(session_id)
        n_ex = rng.randint(config.SIM_EXERCISES_PER_SESSION_MIN,
                           config.SIM_EXERCISES_PER_SESSION_MAX)
        n_ex = min(n_ex, len(pool))
        chosen = rng.sample(pool, n_ex)

        is_cardio = wtype in ("cardio", "running", "walking", "hiit", "yoga")
        for ex_id in chosen:
            if is_cardio:
                rows.append({
                    "session_id": session_id,
                    "exercise_id": int(ex_id),
                    "sets": None,
                    "reps": None,
                    "duration_sec": rng.randint(60, 600),
                })
            else:
                rows.append({
                    "session_id": session_id,
                    "exercise_id": int(ex_id),
                    "sets": rng.randint(3, 5),
                    "reps": rng.randint(6, 15),
                    "duration_sec": None,
                })

    df = pd.DataFrame(rows)
    logger.info(f"[session_exercises] {len(df)} lignes simulées pour "
                f"{len(workouts_df)} sessions.")
    return df


def simulate_biometric_metrics(users_df, gym_df):
    """
    Pour chaque user, génère SIM_BIOMETRIC_DAYS lignes (1 par jour) en
    remontant depuis la date de leur session de workout (ou aujourd'hui).

    Variations déterministes seedées par user_id :
      - weight_kg : +/- 2% autour du poids profil
      - sleep_hours : tirage dans [6, 9]
      - resting_bpm : +/- 5 autour du resting_bpm gym (60 si absent)

    users_df : DataFrame avec colonnes 'id', 'name', 'weight_kg'
    gym_df : DataFrame brut du Gym Members (pour récupérer resting_bpm)
        avec colonnes 'resting_bpm' (snake_case) ; aligné par index sur users_df.

    Retourne un DataFrame prêt pour insertion dans biometric_metrics.
    """
    if users_df.empty:
        return pd.DataFrame(columns=[
            "user_id", "record_date", "weight_kg",
            "sleep_hours", "resting_bpm", "notes"
        ])

    # Aligner resting_bpm sur les users par position (les deux viennent du même
    # CSV ligne par ligne, dans le même ordre).
    resting_lookup = {}
    if gym_df is not None and not gym_df.empty and "resting_bpm" in gym_df.columns:
        gym_reset = gym_df.reset_index(drop=True)
        for i, name in enumerate(users_df["name"].tolist()):
            if i < len(gym_reset):
                val = gym_reset.iloc[i].get("resting_bpm")
                if pd.notna(val):
                    resting_lookup[name] = float(val)

    today = pd.Timestamp.today().normalize()
    rows = []
    for _, u in users_df.iterrows():
        uid = int(u["id"])
        base_weight = float(u["weight_kg"]) if pd.notna(u.get("weight_kg")) else 70.0
        base_resting = resting_lookup.get(u["name"], 60.0)

        rng = random.Random(uid)
        for d in range(config.SIM_BIOMETRIC_DAYS):
            record_date = (today - timedelta(days=d)).date()
            weight = round(base_weight * rng.uniform(0.98, 1.02), 2)
            sleep = round(rng.uniform(6.0, 9.0), 1)
            resting = round(base_resting + rng.uniform(-5, 5), 1)
            # Borner pour respecter les CHECK de la BDD
            resting = max(40.0, min(120.0, resting))
            rows.append({
                "user_id": uid,
                "record_date": record_date,
                "weight_kg": weight,
                "sleep_hours": sleep,
                "resting_bpm": resting,
                "notes": None,
            })

    df = pd.DataFrame(rows)
    logger.info(f"[biometric_metrics] {len(df)} lignes simulées pour "
                f"{len(users_df)} users sur {config.SIM_BIOMETRIC_DAYS} jours.")