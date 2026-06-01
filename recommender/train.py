"""
Etape 2 - Entrainement (Competences 2, 3, 4).

On entraine 2 RandomForest (100 vs 200 arbres), on compare en cross-validation
(cv=5) et on sauvegarde le meilleur dans recommender/model.pkl.

    python -m recommender.train
"""

from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from recommender.prepare_data import prepare

MODEL_OUT = Path(__file__).resolve().parent / "model.pkl"


def train():
    data = prepare()
    X_train, y_train = data["X_train"], data["y_train"]
    X_full, y_full = data["X_full"], data["y_full"]

    # deux versions du modele -> Competence 6 (ajustement n_estimators)
    candidats = {
        "rf_100": RandomForestClassifier(n_estimators=100, random_state=42),
        "rf_200": RandomForestClassifier(n_estimators=200, random_state=42),
    }

    best_name, best_model, best_score = None, None, -1.0
    for name, model in candidats.items():
        model.fit(X_train, y_train)
        scores = cross_val_score(model, X_full, y_full, cv=5)
        moyenne = scores.mean()
        print(f"{name} -> cv accuracy = {moyenne:.3f} (+/- {scores.std():.3f})")
        if moyenne > best_score:
            best_name, best_model, best_score = name, model, moyenne

    # on sauvegarde le modele + les encoders + l'ordre des features
    bundle = {
        "model": best_model,
        "model_name": best_name,
        "encoders": data["encoders"],
        "features": data["features"],
        "classes": list(best_model.classes_),
    }
    joblib.dump(bundle, MODEL_OUT)
    print(f"\nMeilleur modele : {best_name} (cv={best_score:.3f})")
    print(f"Sauvegarde -> {MODEL_OUT}")


if __name__ == "__main__":
    train()
