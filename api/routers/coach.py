# Endpoints IA — coaching personnalisé via OpenAI GPT
# Préfixe monté dans main.py : /coach

import json
import logging
import base64
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.ai_client import client
from api.database import get_db
from api.models import User, BiometricMetric, WorkoutSession

from api.coach_utils import (
    advice_cache, workout_cache, trend_cache,
    coach_limiter,
    get_fallback_advice, FALLBACK_WORKOUT, FALLBACK_TREND,
    TTLCache,
    validate_image_base64,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# UTILITAIRE INTERNE
# =============================================================================

def _get_user_or_404(user_id: int, db: Session) -> User:
    """Récupère un utilisateur par son ID ou lève une 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur {user_id} introuvable",
        )
    return user


GOAL_LABELS = {
    "weight_loss":       "perte de poids",
    "muscle_gain":       "prise de muscle",
    "sleep_improvement": "amélioration du sommeil",
    "maintenance":       "maintien de la forme",
}


# =============================================================================
# SCHÉMAS — requêtes et réponses
# =============================================================================

class CoachRequest(BaseModel):
    user_id: int = Field(..., description="Identifiant de l'utilisateur en base")

    class Config:
        json_schema_extra = {"example": {"user_id": 1}}


class CoachResponse(BaseModel):
    user_id: int
    user_name: str
    advice: str


# ── Analyse photo ─────────────────────────────────────────────────────────────

class PhotoRequest(BaseModel):
    user_id: int = Field(..., description="Identifiant de l'utilisateur")
    image_base64: str = Field(..., description="Image encodée en base64 (JPEG ou PNG)")

    class Config:
        json_schema_extra = {"example": {"user_id": 1, "image_base64": "<base64>"}}


class Macros(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


class PhotoResponse(BaseModel):
    user_id: int
    user_name: str
    foods_detected: List[str]
    macros: Macros
    advice: str


# ── Programme d'entraînement ──────────────────────────────────────────────────

EQUIPMENT_LABELS = {
    "none":       "poids du corps uniquement (aucun matériel)",
    "dumbbell":   "haltères",
    "barbell":    "barre olympique",
    "machine":    "machines de salle",
    "resistance": "élastiques de résistance",
    "full":       "équipement complet (salle de sport)",
}


class WorkoutRequest(BaseModel):
    user_id: int = Field(..., description="Identifiant de l'utilisateur")
    equipment: str = Field(
        "none",
        description="Matériel disponible : none | dumbbell | barbell | machine | resistance | full",
    )
    days_per_week: int = Field(
        3,
        ge=1,
        le=7,
        description="Nombre de séances par semaine (1–7)",
    )

    class Config:
        json_schema_extra = {"example": {"user_id": 1, "equipment": "dumbbell", "days_per_week": 3}}


class WorkoutResponse(BaseModel):
    user_id: int
    user_name: str
    plan: str


# ── Tendances biométriques ────────────────────────────────────────────────────

class TrendResponse(BaseModel):
    user_id: int
    user_name: str
    analysis: str


# =============================================================================
# ENDPOINT — POST /coach/advice
# =============================================================================

@router.post(
    "/advice",
    response_model=CoachResponse,
    summary="Conseil personnalisé IA",
    description=(
        "Génère un conseil de coaching santé personnalisé via OpenAI GPT "
        "à partir du profil et de la dernière mesure biométrique de l'utilisateur."
    ),
)
def get_ai_advice(payload: CoachRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(payload.user_id, db)

    # — Rate limiting —
    if not coach_limiter.is_allowed(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota atteint : 10 appels IA par heure. "
                   f"Réessayez dans quelques minutes.",
        )

    # — Cache —
    cache_key = TTLCache.make_key(endpoint="advice", user_id=user.id)
    cached = advice_cache.get(cache_key)
    if cached:
        logger.info("Cache hit — /coach/advice user_id=%s", user.id)
        return CoachResponse(user_id=user.id, user_name=user.name, advice=cached)

    # — Construction du prompt (inchangée) —
    last_metric = (
        db.query(BiometricMetric)
        .filter(BiometricMetric.user_id == user.id)
        .order_by(BiometricMetric.record_date.desc())
        .first()
    )
    goal_fr = GOAL_LABELS.get(user.goal or "", user.goal or "non renseigné")
    metric_context = ""
    if last_metric:
        parts = []
        if last_metric.weight_kg:
            parts.append(f"poids actuel {last_metric.weight_kg:.1f} kg")
        if last_metric.sleep_hours:
            parts.append(f"sommeil {last_metric.sleep_hours:.1f} h/nuit")
        if last_metric.resting_bpm:
            parts.append(f"fréquence cardiaque au repos {last_metric.resting_bpm:.0f} bpm")
        if parts:
            metric_context = " Dernières données biométriques : " + ", ".join(parts) + "."
    bmi_context = f", un IMC de {user.bmi:.1f}" if user.bmi is not None else ""
    prompt = (
        f"Tu es un coach santé bienveillant et expert. "
        f"L'utilisateur s'appelle {user.name}, il a {user.age} ans{bmi_context}, "
        f"son objectif est : {goal_fr}.{metric_context} "
        f"Donne-lui un conseil personnalisé, concret et motivant en français, "
        f"en 3 à 5 phrases maximum."
    )

    # — Appel OpenAI avec fallback —
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        advice_text = response.choices[0].message.content
        advice_cache.set(cache_key, advice_text)  # mise en cache
    except Exception as exc:
        logger.error("Erreur OpenAI /advice : %s", exc, exc_info=True)
        advice_text = get_fallback_advice(user.goal)  # fallback au lieu de 502

    return CoachResponse(user_id=user.id, user_name=user.name, advice=advice_text)


# =============================================================================
# ENDPOINT — POST /coach/analyze-photo
# =============================================================================

@router.post(
    "/analyze-photo",
    response_model=PhotoResponse,
    summary="Analyse photo de repas (Vision IA)",
    description=(
        "Soumet une photo de repas encodée en base64 à GPT-4o Vision. "
        "Retourne les aliments détectés, une estimation des macronutriments "
        "et un conseil nutritionnel adapté à l'objectif de l'utilisateur."
    ),
)
def analyze_photo(payload: PhotoRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(payload.user_id, db)
    goal_fr = GOAL_LABELS.get(user.goal or "", user.goal or "non renseigné")

    try:
        image_bytes, mime_type = validate_image_base64(payload.image_base64)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    # On demande à GPT-4o de répondre exclusivement en JSON structuré.
    # Le "system" message cadre le format de sortie attendu.
    system_prompt = (
        "Tu es un nutritionniste expert et un assistant IA. "
        "Tu réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, "
        "sans balises markdown, sans explication. "
        "Le JSON doit avoir exactement ces clés : "
        "\"foods_detected\" (liste de strings en français), "
        "\"macros\" (objet avec calories:int, protein_g:float, carbs_g:float, fat_g:float), "
        "\"advice\" (string, conseil nutritionnel en français, 2 à 4 phrases)."
    )

    user_prompt = (
        f"Analyse cette photo de repas. "
        f"L'utilisateur s'appelle {user.name}, son objectif est : {goal_fr}. "
        f"Identifie les aliments visibles, estime les macros pour la portion visible, "
        f"puis donne un conseil nutritionnel adapté à son objectif."
    )

    raw = ""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # gpt-4o-mini ne supporte pas Vision de façon fiable
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                # L'API OpenAI attend ce format exact pour le base64
                                "url": f"data:{mime_type};base64,{image_b64}",
                                "detail": "low",  # "low" = moins de tokens, assez pour identifier des aliments
                            },
                        },
                    ],
                },
            ],
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()

        # GPT peut parfois envelopper le JSON dans des backticks malgré le system prompt
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

    except json.JSONDecodeError as exc:
        logger.error("Réponse GPT non parseable : %s", raw, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La réponse GPT n'est pas un JSON valide. Réessayez.",
        )
    except Exception as exc:
        logger.error("Erreur OpenAI /analyze-photo : %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return PhotoResponse(
        user_id=user.id,
        user_name=user.name,
        foods_detected=parsed.get("foods_detected", []),
        macros=Macros(**parsed["macros"]),
        advice=parsed.get("advice", ""),
    )


# =============================================================================
# ENDPOINT — POST /coach/workout-plan
# =============================================================================

@router.post(
    "/workout-plan",
    response_model=WorkoutResponse,
    summary="Programme d'entraînement personnalisé",
    description=(
        "Génère un programme d'entraînement hebdomadaire via GPT-4o-mini, "
        "adapté à l'objectif de l'utilisateur, au matériel disponible "
        "et au nombre de séances souhaité."
    ),
)
def get_workout_plan(payload: WorkoutRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(payload.user_id, db)

    if not coach_limiter.is_allowed(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quota atteint : 10 appels IA par heure.",
        )

    cache_key = TTLCache.make_key(
        endpoint="workout",
        user_id=user.id,
        equipment=payload.equipment,
        days=payload.days_per_week,
    )
    cached = workout_cache.get(cache_key)
    if cached:
        logger.info("Cache hit — /coach/workout-plan user_id=%s", user.id)
        return WorkoutResponse(user_id=user.id, user_name=user.name, plan=cached)

    goal_fr = GOAL_LABELS.get(user.goal or "", user.goal or "non renseigné")
    equipment_fr = EQUIPMENT_LABELS.get(payload.equipment, payload.equipment)
    last_metric = (
        db.query(BiometricMetric)
        .filter(BiometricMetric.user_id == user.id)
        .order_by(BiometricMetric.record_date.desc())
        .first()
    )
    bio_context = ""
    if last_metric:
        parts = []
        if last_metric.weight_kg:
            parts.append(f"poids {last_metric.weight_kg:.1f} kg")
        if last_metric.resting_bpm:
            parts.append(f"FC repos {last_metric.resting_bpm:.0f} bpm")
        if parts:
            bio_context = " Données récentes : " + ", ".join(parts) + "."
    bmi_context = f", IMC {user.bmi:.1f}" if user.bmi is not None else ""
    prompt = (
        f"Tu es un coach sportif expert. "
        f"Génère un programme d'entraînement hebdomadaire en français, formaté en Markdown. "
        f"Profil : {user.name}, {user.age} ans{bmi_context}, objectif {goal_fr}.{bio_context} "
        f"Matériel disponible : {equipment_fr}. "
        f"Nombre de séances par semaine : {payload.days_per_week}. "
        f"Inclure : jours, exercices avec séries/répétitions, temps de repos, conseil récupération."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        plan_text = response.choices[0].message.content
        workout_cache.set(cache_key, plan_text)
    except Exception as exc:
        logger.error("Erreur OpenAI /workout-plan : %s", exc, exc_info=True)
        plan_text = FALLBACK_WORKOUT

    return WorkoutResponse(user_id=user.id, user_name=user.name, plan=plan_text)


# =============================================================================
# ENDPOINT — POST /coach/biometric-trend
# =============================================================================

@router.post(
    "/biometric-trend",
    response_model=TrendResponse,
    summary="Analyse des tendances biométriques (30 jours)",
    description=(
        "Récupère les 30 derniers jours de métriques biométriques de l'utilisateur "
        "et demande à GPT d'analyser les tendances (poids, sommeil, FC repos) "
        "avec des conseils adaptés à l'objectif."
    ),
)
def get_biometric_trend(payload: CoachRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(payload.user_id, db)

    if not coach_limiter.is_allowed(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quota atteint : 10 appels IA par heure.",
        )

    cache_key = TTLCache.make_key(endpoint="trend", user_id=user.id)
    cached = trend_cache.get(cache_key)
    if cached:
        logger.info("Cache hit — /coach/biometric-trend user_id=%s", user.id)
        return TrendResponse(user_id=user.id, user_name=user.name, analysis=cached)

    since = date.today() - timedelta(days=30)
    metrics = (
        db.query(BiometricMetric)
        .filter(
            BiometricMetric.user_id == user.id,
            BiometricMetric.record_date >= since,
        )
        .order_by(BiometricMetric.record_date.asc())
        .all()
    )
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune donnée biométrique sur les 30 derniers jours.",
        )

    goal_fr = GOAL_LABELS.get(user.goal or "", user.goal or "non renseigné")
    data_lines = []
    for m in metrics:
        parts = [f"Date: {m.record_date}"]
        if m.weight_kg:
            parts.append(f"poids={m.weight_kg:.1f}kg")
        if m.sleep_hours:
            parts.append(f"sommeil={m.sleep_hours:.1f}h")
        if m.resting_bpm:
            parts.append(f"FC_repos={m.resting_bpm:.0f}bpm")
        data_lines.append(" | ".join(parts))

    prompt = (
        f"Tu es un coach santé expert. "
        f"Données biométriques 30 jours de {user.name} (objectif : {goal_fr}) :\n\n"
        f"{chr(10).join(data_lines)}\n\n"
        f"Analyse les tendances, identifie les évolutions positives et points d'attention, "
        f"donne 2–3 conseils concrets. Markdown accepté. 200 mots max."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        analysis_text = response.choices[0].message.content
        trend_cache.set(cache_key, analysis_text)
    except Exception as exc:
        logger.error("Erreur OpenAI /biometric-trend : %s", exc, exc_info=True)
        analysis_text = FALLBACK_TREND

    return TrendResponse(user_id=user.id, user_name=user.name, analysis=analysis_text)