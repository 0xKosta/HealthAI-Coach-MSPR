"""
Etape 1 - Preparation des donnees (Competence 1).

On charge users + workout_sessions, on join sur user_id, on garde les features
demandees, on encode gender/goal, puis train_test_split.
Le resultat est sauvegarde dans recommender/data/prepared.pkl pour train.py.

    python -m recommender.prepare_data
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parent.parent
DATA_OUT = Path(__file__).resolve().parent / "data" / "prepared.pkl"

FEATURES = ["age", "gender", "bmi", "body_fat_pct", "goal",
            "duration_min", "calories_burned"]
TARGET = "workout_type"


def load_and_merge():
    users = pd.read_csv(ROOT / "users_rows.csv")
    sessions = pd.read_csv(ROOT / "workout_sessions_rows.csv")

    # join : chaque session recupere le profil de son user
    df = sessions.merge(users, left_on="user_id", right_on="id",
                        suffixes=("_session", "_user"))

    # si l'export Supabase n'a pas workout_type, on s'arrete proprement
    if TARGET not in df.columns:
        raise ValueError(
            "Colonne 'workout_type' absente. Reexporter workout_sessions avec "
            "cette colonne, ou relancer recommender._gen_sample_data pour la demo."
        )
    return df


def prepare():
    df = load_and_merge()
    df = df[FEATURES + [TARGET]].dropna()

    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    # encodage des colonnes texte (gender, goal) -> on garde les encoders
    # pour pouvoir transformer un nouveau profil dans main.py
    encoders = {}
    for col in ("gender", "goal"):
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    bundle = {
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "X_full": X, "y_full": y,
        "encoders": encoders,
        "features": FEATURES,
    }
    joblib.dump(bundle, DATA_OUT)
    print(f"OK -> {len(X)} lignes | train={len(X_train)} test={len(X_test)}")
    print(f"Classes : {sorted(y.unique())}")
    print(f"Sauvegarde -> {DATA_OUT}")
    return bundle


if __name__ == "__main__":
    prepare()
