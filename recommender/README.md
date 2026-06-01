# Moteur de recommandation sportive — MSPR 2

Predit le type d'entrainement (`workout_type`) a partir du profil utilisateur, et
expose le tout via un micro-service FastAPI separe.

## Lancer

```bash
pip install -r recommender/requirements.txt

# (optionnel) regenerer les CSV de demo si on n'a pas exporte Supabase
python -m recommender._gen_sample_data

python -m recommender.train       # entraine + sauvegarde model.pkl
python -m recommender.evaluate    # metriques + matrice de confusion + compa 100/200

# micro-service (port 8001, separe de l'API principale sur 8000)
uvicorn recommender.main:app --port 8001 --reload
```

Pour Mongo : copier l'URI Atlas dans `.env` (variable `MONGO_URI`). Sans Mongo
l'API tourne quand meme, elle ne log juste pas l'historique.

## Endpoints (port 8001)

- `POST /recommend` — profil utilisateur → `workout_type` predit
- `GET /recommendations/{user_id}` — historique des recos (MongoDB)
- `GET /health`

Exemple :

```bash
curl -X POST http://localhost:8001/recommend -H "Content-Type: application/json" -d '{
  "user_id": 1, "age": 25, "gender": "male", "bmi": 22.5,
  "body_fat_pct": 15, "goal": "muscle_gain",
  "duration_min": 60, "calories_burned": 400
}'
```

## Correspondance grille

| Competence | Fichier |
| --- | --- |
| 1 — Preparer les donnees | `prepare_data.py` |
| 2 — Framework | `requirements.txt` (scikit-learn) |
| 3 — Coder le modele | `train.py` (RandomForest) |
| 4 — Entrainement | `cross_val_score` dans `train.py` |
| 5 — Test + metriques | `evaluate.py` |
| 6 — Ajuster le modele | compa `n_estimators` 100 vs 200 |

Notebook de soutenance : `notebooks/ml_recommendation.ipynb`
