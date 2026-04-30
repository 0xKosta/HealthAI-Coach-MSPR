# api/routers/metrics.py
# CRUD pour BiometricMetric + endpoint /stats avec agrégats globaux
# Préfixe monté dans main.py : /metrics

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import BiometricMetric, User
from api.schemas import BiometricMetricCreate, BiometricMetricResponse

router = APIRouter()


# =============================================================================
# BIOMETRIC METRICS — suivi biométrique dans le temps
# =============================================================================

@router.get(
    "/",
    response_model=list[BiometricMetricResponse],
    summary="Lister les mesures biométriques",
    description="Retourne la liste paginée de toutes les mesures biométriques enregistrées.",
)
def list_metrics(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    return db.query(BiometricMetric).offset(skip).limit(limit).all()


@router.get(
    "/{metric_id}",
    response_model=BiometricMetricResponse,
    summary="Récupérer une mesure biométrique",
    description="Retourne une mesure biométrique par son identifiant.",
)
def get_metric(metric_id: int, db: Session = Depends(get_db)):
    metric = db.query(BiometricMetric).filter(BiometricMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesure introuvable")
    return metric


@router.post(
    "/",
    response_model=BiometricMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer une mesure biométrique",
    description=(
        "Crée une nouvelle mesure biométrique pour un utilisateur. "
        "Conçu pour l'historique temporel : plusieurs enregistrements par utilisateur sont attendus."
    ),
)
def create_metric(payload: BiometricMetricCreate, db: Session = Depends(get_db)):
    metric = BiometricMetric(**payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.put(
    "/{metric_id}",
    response_model=BiometricMetricResponse,
    summary="Mettre à jour une mesure biométrique",
    description="Met à jour tous les champs d'une mesure biométrique existante.",
)
def update_metric(metric_id: int, payload: BiometricMetricCreate, db: Session = Depends(get_db)):
    metric = db.query(BiometricMetric).filter(BiometricMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesure introuvable")
    for field, value in payload.model_dump().items():
        setattr(metric, field, value)
    db.commit()
    db.refresh(metric)
    return metric


@router.delete(
    "/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une mesure biométrique",
    description="Supprime une mesure biométrique.",
)
def delete_metric(metric_id: int, db: Session = Depends(get_db)):
    metric = db.query(BiometricMetric).filter(BiometricMetric.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesure introuvable")
    db.delete(metric)
    db.commit()


# =============================================================================
# STATS — agrégats globaux sur la population utilisateurs
# =============================================================================

@router.get(
    "/stats",
    summary="Statistiques globales",
    description=(
        "Retourne des agrégats calculés sur l'ensemble des utilisateurs : "
        "moyenne d'âge, moyenne de BMI, et répartition par objectif (goal)."
    ),
)
def get_stats(db: Session = Depends(get_db)):
    # Agrégats de base sur la table users
    agg = db.query(
        func.avg(User.age).label("avg_age"),
        func.avg(User.bmi).label("avg_bmi"),
        func.count(User.id).label("total_users"),
    ).one()

    # Répartition des objectifs : nombre d'utilisateurs par valeur de goal
    goal_rows = (
        db.query(User.goal, func.count(User.id).label("count"))
        .filter(User.goal.isnot(None))
        .group_by(User.goal)
        .all()
    )
    goal_distribution = {row.goal: row.count for row in goal_rows}

    return {
        "total_users": agg.total_users,
        "avg_age": round(agg.avg_age, 2) if agg.avg_age is not None else None,
        "avg_bmi": round(agg.avg_bmi, 2) if agg.avg_bmi is not None else None,
        "goal_distribution": goal_distribution,
    }
