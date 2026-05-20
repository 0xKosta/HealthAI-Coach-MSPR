# api/routers/coach.py
# Endpoint IA — conseil personnalisé via OpenAI GPT
# Préfixe monté dans main.py : /coach

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.ai_client import client
from api.database import get_db
from api.models import User, BiometricMetric

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# SCHÉMAS — requête et réponse
# =============================================================================

class CoachRequest(BaseModel):
    user_id: int = Field(..., description="Identifiant de l'utilisateur en base")

    class Config:
        json_schema_extra = {
            "example": {"user_id": 1}
        }


class CoachResponse(BaseModel):
    user_id: int
    user_name: str
    advice: str


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
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur {payload.user_id} introuvable",
        )

    last_metric = (
        db.query(BiometricMetric)
        .filter(BiometricMetric.user_id == user.id)
        .order_by(BiometricMetric.record_date.desc())
        .first()
    )

    goal_labels = {
        "weight_loss":       "perte de poids",
        "muscle_gain":       "prise de muscle",
        "sleep_improvement": "amélioration du sommeil",
        "maintenance":       "maintien de la forme",
    }
    goal_fr = goal_labels.get(user.goal or "", user.goal or "non renseigné")

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

    bmi_context = f", un IMC de {user.bmi:.1f}" if user.bmi else ""
    prompt = (
        f"Tu es un coach santé bienveillant et expert. "
        f"L'utilisateur s'appelle {user.name}, il a {user.age} ans{bmi_context}, "
        f"son objectif est : {goal_fr}.{metric_context} "
        f"Donne-lui un conseil personnalisé, concret et motivant en français, "
        f"en 3 à 5 phrases maximum."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        advice_text = response.choices[0].message.content
    except Exception as exc:
        logger.error("Erreur OpenAI : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur OpenAI : {exc}",
        )

    return CoachResponse(
        user_id=user.id,
        user_name=user.name,
        advice=advice_text,
    )
