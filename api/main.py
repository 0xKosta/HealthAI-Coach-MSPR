# api/main.py
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import users, nutrition, exercises, metrics, coach
from api.routers import users, nutrition, exercises, metrics, coach, auth, posts

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
    expose_headers=["X-Total-Count"],
)

app.include_router(users.router,     prefix="/users",     tags=["Utilisateurs"])
app.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
app.include_router(exercises.router, prefix="/exercises", tags=["Exercices"])
app.include_router(metrics.router,   prefix="/metrics",   tags=["Métriques"])
app.include_router(coach.router,     prefix="/coach",     tags=["Coach IA"])
app.include_router(auth.router,  prefix="/auth",  tags=["Authentification"])
app.include_router(posts.router, prefix="/posts", tags=["Feed Social"])


def _is_user_biometric_route(path: str, method: str) -> bool:
    """Routes où les erreurs de validation biométrique renvoient 400."""
    normalized = path.rstrip("/") or "/"
    if method not in ("POST", "PUT", "PATCH"):
        return False
    if normalized == "/auth/me/profile":
        return True
    if normalized == "/users":
        return True
    return bool(re.match(r"^/users/\d+$", normalized))


def _validation_error_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Données invalides."
    msg = errors[0].get("msg", "Données invalides.")
    if msg.startswith("Value error, "):
        return msg[len("Value error, ") :]
    return msg


@app.exception_handler(RequestValidationError)
async def biometric_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    if _is_user_biometric_route(request.url.path, request.method):
        return JSONResponse(
            status_code=400,
            content={"detail": _validation_error_message(exc)},
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


#serving des fichiers médias uploadés
from fastapi.staticfiles import StaticFiles
from pathlib import Path
Path("media").mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/health", tags=["Santé"], summary="Vérifier l'état de l'API")
def health_check():
    """
    Endpoint de santé — vérifie que l'API est opérationnelle.
    Utilisé pour valider le déploiement et monitorer le service.
    """
    return {"status": "ok", "service": "HealthAI Coach API"}
