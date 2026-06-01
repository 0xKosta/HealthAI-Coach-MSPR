"""
Etape 3 - Evaluation (Competences 5 et 6).

Affiche le classification_report (precision, rappel, F1, accuracy), la matrice
de confusion, et la comparaison avant/apres ajustement (100 vs 200 arbres) sur
le jeu de test.

    python -m recommender.evaluate
"""

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)

from recommender.prepare_data import prepare
from recommender.train import MODEL_OUT


def evaluate():
    data = prepare()
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]

    # modele final sauvegarde par train.py
    bundle = joblib.load(MODEL_OUT)
    model = bundle["model"]
    y_pred = model.predict(X_test)

    print("=== Rapport de classification (modele final :",
          bundle["model_name"], ") ===")
    print(classification_report(y_test, y_pred))

    print("=== Matrice de confusion ===")
    print("Classes :", list(model.classes_))
    print(confusion_matrix(y_test, y_pred))

    # Competence 6 : compa avant/apres ajustement n_estimators
    print("\n=== Comparaison ajustement n_estimators (sur le test) ===")
    for n in (100, 200):
        m = RandomForestClassifier(n_estimators=n, random_state=42)
        m.fit(X_train, y_train)
        acc = accuracy_score(y_test, m.predict(X_test))
        print(f"n_estimators={n} -> accuracy test = {acc:.3f}")


if __name__ == "__main__":
    evaluate()
