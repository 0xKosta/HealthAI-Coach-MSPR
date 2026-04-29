# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="HealthAI Coach API",
    description="""
    API REST du backend métier HealthAI Coach.

    Gère les données de nutrition, fitness et utilisateurs
    pour la plateforme de coaching santé personnalisé.
    """,
    version="1.0.0",
    contact={"name": "Équipe HealthAI Coach"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Les routers seront inclus ici une fois les fichiers complétés
# from api.routers import users, nutrition, exercises, metrics
# app.include_router(users.router, prefix="/users", tags=["Utilisateurs"])
# app.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
# app.include_router(exercises.router, prefix="/exercises", tags=["Exercices"])
# app.include_router(metrics.router, prefix="/metrics", tags=["Métriques"])

@app.get("/health", tags=["Santé"], summary="Vérifier l'état de l'API")
def health_check():
    """
    Endpoint de santé — vérifie que l'API est opérationnelle.
    Utilisé pour valider le déploiement et monitorer le service.
    """
    return {"status": "ok", "service": "HealthAI Coach API"}
