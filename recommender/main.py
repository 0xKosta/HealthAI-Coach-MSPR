"""
Etape 4 - Micro-service de recommandation (livrable CDC : micro-service + NoSQL).

API FastAPI separee (port 8001) de l'API principale (port 8000).
- charge model.pkl au demarrage
- POST /recommend : recoit un profil -> renvoie le workout_type predit
- log chaque reco dans MongoDB (Atlas gratuit)
- GET /recommendations/{user_id} : historique des recos depuis MongoDB

Lancer : uvicorn recommender.main:app --port 8001 --reload
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"
MONGO_URI = os.getenv("MONGO_URI")  # mongodb+srv://... (Atlas gratuit)

app = FastAPI(
    title="HealthAI Coach - Moteur de recommandation",
    description="Micro-service ML qui predit un type d'entrainement (port 8001).",
    version="1.0.0",
)

# chargees au demarrage
_bundle = joblib.load(MODEL_PATH)
_model = _bundle["model"]
_encoders = _bundle["encoders"]
_features = _bundle["features"]

# connexion Mongo optionnelle : si pas d'URI on tourne quand meme (mode demo)
_collection = None
if MONGO_URI:
    from pymongo import MongoClient
    _client = MongoClient(MONGO_URI)
    _collection = _client["healthai"]["recommendations"]


class Profil(BaseModel):
    user_id: int
    age: int
    gender: str            # male / female
    bmi: float
    body_fat_pct: float
    goal: str              # weight_loss / muscle_gain / sleep_improvement / maintenance
    duration_min: int
    calories_burned: float


@app.get("/health")
def health():
    return {"status": "ok", "service": "recommender", "model": _bundle["model_name"]}


@app.post("/recommend")
def recommend(profil: Profil):
    # on encode gender/goal avec les memes encoders que pour l'entrainement
    try:
        gender_enc = int(_encoders["gender"].transform([profil.gender])[0])
        goal_enc = int(_encoders["goal"].transform([profil.goal])[0])
    except ValueError:
        raise HTTPException(status_code=400,
                            detail="gender ou goal inconnu du modele.")

    ligne = pd.DataFrame([{
        "age": profil.age,
        "gender": gender_enc,
        "bmi": profil.bmi,
        "body_fat_pct": profil.body_fat_pct,
        "goal": goal_enc,
        "duration_min": profil.duration_min,
        "calories_burned": profil.calories_burned,
    }])[_features]

    pred = str(_model.predict(ligne)[0])

    # log dans Mongo si dispo
    doc = {
        "user_id": profil.user_id,
        "workout_type": pred,
        "profil": profil.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    if _collection is not None:
        _collection.insert_one(dict(doc))

    return {"user_id": profil.user_id, "recommended_workout_type": pred}


@app.get("/recommendations/{user_id}")
def history(user_id: int):
    if _collection is None:
        raise HTTPException(status_code=503,
                            detail="MongoDB non configure (variable MONGO_URI).")
    docs = list(
        _collection.find({"user_id": user_id}, {"_id": 0})
        .sort("created_at", -1)
    )
    return {"user_id": user_id, "count": len(docs), "recommendations": docs}
