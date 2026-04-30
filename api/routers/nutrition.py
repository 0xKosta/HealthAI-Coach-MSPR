# api/routers/nutrition.py
# CRUD pour Food et FoodLog
# Préfixe monté dans main.py : /nutrition

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Food, FoodLog
from api.schemas import FoodCreate, FoodResponse, FoodLogCreate, FoodLogResponse

router = APIRouter()


# =============================================================================
# FOODS — catalogue des aliments
# =============================================================================

@router.get(
    "/foods",
    response_model=list[FoodResponse],
    summary="Lister les aliments",
    description="Retourne la liste paginée du catalogue nutritionnel.",
)
def list_foods(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    return db.query(Food).offset(skip).limit(limit).all()


@router.get(
    "/foods/{food_id}",
    response_model=FoodResponse,
    summary="Récupérer un aliment",
    description="Retourne les valeurs nutritionnelles d'un aliment par son identifiant.",
)
def get_food(food_id: int, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aliment introuvable")
    return food


@router.post(
    "/foods",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un aliment",
    description="Ajoute un nouvel aliment au catalogue nutritionnel.",
)
def create_food(payload: FoodCreate, db: Session = Depends(get_db)):
    food = Food(**payload.model_dump())
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.put(
    "/foods/{food_id}",
    response_model=FoodResponse,
    summary="Mettre à jour un aliment",
    description="Met à jour tous les champs d'un aliment existant.",
)
def update_food(food_id: int, payload: FoodCreate, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aliment introuvable")
    for field, value in payload.model_dump().items():
        setattr(food, field, value)
    db.commit()
    db.refresh(food)
    return food


@router.delete(
    "/foods/{food_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un aliment",
    description="Supprime un aliment du catalogue. Échoue si des food_logs y font référence (RESTRICT).",
)
def delete_food(food_id: int, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aliment introuvable")
    db.delete(food)
    db.commit()


# =============================================================================
# FOOD LOGS — journal alimentaire journalier
# =============================================================================

@router.get(
    "/logs",
    response_model=list[FoodLogResponse],
    summary="Lister les entrées du journal alimentaire",
    description="Retourne la liste paginée de toutes les entrées du journal alimentaire.",
)
def list_food_logs(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    return db.query(FoodLog).offset(skip).limit(limit).all()


@router.get(
    "/logs/{log_id}",
    response_model=FoodLogResponse,
    summary="Récupérer une entrée du journal alimentaire",
    description="Retourne une entrée du journal alimentaire par son identifiant.",
)
def get_food_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    return log


@router.post(
    "/logs",
    response_model=FoodLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un repas",
    description=(
        "Crée une entrée dans le journal alimentaire. "
        "`calories_consumed` peut être pré-calculé par l'ETL : `(calories_per_100g / 100) * quantity_g`."
    ),
)
def create_food_log(payload: FoodLogCreate, db: Session = Depends(get_db)):
    log = FoodLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.put(
    "/logs/{log_id}",
    response_model=FoodLogResponse,
    summary="Mettre à jour une entrée du journal alimentaire",
    description="Met à jour tous les champs d'une entrée du journal alimentaire existante.",
)
def update_food_log(log_id: int, payload: FoodLogCreate, db: Session = Depends(get_db)):
    log = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    for field, value in payload.model_dump().items():
        setattr(log, field, value)
    db.commit()
    db.refresh(log)
    return log


@router.delete(
    "/logs/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une entrée du journal alimentaire",
    description="Supprime une entrée du journal alimentaire.",
)
def delete_food_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(FoodLog).filter(FoodLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    db.delete(log)
    db.commit()
