"""
Petit script pour générer des CSV de démo si on n'a pas encore exporté
les vraies tables depuis Supabase (boutton "Export to CSV" -> fichiers _rows.csv).

Les colonnes collent au schéma de api/models.py.
On garde workout_type dans workout_sessions (colonne d'origine du dataset Gym
Members de Kaggle) parce que c'est notre cible à prédire.

A lancer une seule fois : python -m recommender._gen_sample_data
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproductible

ROOT = Path(__file__).resolve().parent.parent
N_USERS = 220

GENDERS = ["male", "female"]
GOALS = ["weight_loss", "muscle_gain", "sleep_improvement", "maintenance"]
WORKOUTS = ["Cardio", "Strength", "Yoga", "HIIT"]

# proba de workout_type selon le goal -> donne un vrai signal a apprendre
GOAL_TO_WORKOUT = {
    "weight_loss":       [0.45, 0.10, 0.10, 0.35],
    "muscle_gain":       [0.10, 0.65, 0.05, 0.20],
    "sleep_improvement": [0.30, 0.10, 0.50, 0.10],
    "maintenance":       [0.30, 0.30, 0.20, 0.20],
}


def pick_workout(goal, body_fat):
    weights = list(GOAL_TO_WORKOUT[goal])
    # un gros taux de masse grasse pousse un peu plus vers cardio/hiit
    if body_fat > 28:
        weights[0] += 0.10
        weights[3] += 0.10
    return random.choices(WORKOUTS, weights=weights, k=1)[0]


def main():
    users = []
    sessions = []
    biometrics = []
    today = date.today()

    for uid in range(1, N_USERS + 1):
        gender = random.choice(GENDERS)
        age = random.randint(18, 59)
        height_cm = round(random.uniform(155, 195), 1)
        weight_kg = round(random.uniform(50, 110), 1)
        bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
        body_fat = round(random.uniform(10, 35), 1)
        goal = random.choice(GOALS)

        users.append({
            "id": uid,
            "name": f"User_{uid:06d}",
            "age": age,
            "gender": gender,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "bmi": bmi,
            "body_fat_pct": body_fat,
            "goal": goal,
            "created_at": (today - timedelta(days=random.randint(0, 300))).isoformat(),
        })

        # 1 a 3 sessions par user
        for _ in range(random.randint(1, 3)):
            wtype = pick_workout(goal, body_fat)
            duration = random.randint(30, 110)
            # calories liees au type + duree (un peu de bruit)
            base = {"Cardio": 9, "HIIT": 11, "Strength": 6, "Yoga": 4}[wtype]
            calories = round(duration * base + random.uniform(-40, 40), 1)
            avg_bpm = round(random.uniform(110, 165), 1)
            sessions.append({
                "id": len(sessions) + 1,
                "user_id": uid,
                "session_date": (today - timedelta(days=random.randint(0, 200))).isoformat(),
                "duration_min": duration,
                "calories_burned": max(calories, 0),
                "avg_bpm": avg_bpm,
                "max_bpm": round(avg_bpm + random.uniform(10, 40), 1),
                "workout_type": wtype,
            })

        biometrics.append({
            "id": uid,
            "user_id": uid,
            "record_date": today.isoformat(),
            "weight_kg": weight_kg,
            "sleep_hours": round(random.uniform(5, 9), 1),
            "resting_bpm": round(random.uniform(55, 80), 1),
            "notes": "",
        })

    _write(ROOT / "users_rows.csv", users)
    _write(ROOT / "workout_sessions_rows.csv", sessions)
    _write(ROOT / "biometric_metrics_rows.csv", biometrics)
    print(f"OK -> {len(users)} users, {len(sessions)} sessions, {len(biometrics)} biometrics")


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
