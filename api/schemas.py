# api/schemas.py
# Schémas Pydantic v2 — générés à partir de api/models.py
# Conventions :
#   - XxxCreate  : données acceptées en entrée (POST/PUT) — sans id ni champs auto-générés
#   - XxxResponse: données renvoyées en sortie (GET)      — avec id, compatible SQLAlchemy

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# USER
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# =============================================================================

class UserCreate(BaseModel):
    """Données requises pour créer ou mettre à jour un utilisateur (POST / PUT /users)."""

    name: str = Field(..., max_length=100)
    age: int = Field(..., ge=0, le=120)
    gender: Optional[Literal["male", "female", "other"]] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    bmi: Optional[float] = Field(None, description="Calculé à l'ingestion par le pipeline ETL")
    body_fat_pct: Optional[float] = Field(None, ge=0, le=100)
    goal: Optional[Literal["weight_loss", "muscle_gain", "sleep_improvement", "maintenance"]] = None


class UserResponse(UserCreate):
    """Données renvoyées par l'API pour un utilisateur (GET /users, GET /users/{id})."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: date


# =============================================================================
# FOOD
# Source : Daily Food & Nutrition Dataset (Kaggle, CSV)
# =============================================================================

class FoodCreate(BaseModel):
    """Données requises pour créer ou mettre à jour un aliment (POST / PUT /nutrition/foods)."""

    name: str = Field(..., max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    calories_per_100g: float = Field(..., ge=0, description="Valeur calorique pour 100g de produit")
    proteins_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fats_g: Optional[float] = Field(None, ge=0)
    fiber_g: Optional[float] = Field(None, ge=0)


class FoodResponse(FoodCreate):
    """Données renvoyées par l'API pour un aliment (GET /nutrition/foods)."""

    model_config = ConfigDict(from_attributes=True)

    id: int


# =============================================================================
# EXERCISE
# Source : ExerciseDB (GitHub, JSON)
# Internationalisation : champs _fr ajoutés en v1.3 pour la liste déroulante EN/FR
# =============================================================================

class ExerciseCreate(BaseModel):
    """Données requises pour créer ou mettre à jour un exercice (POST / PUT /exercises)."""

    # Champs anglais (source)
    name: str = Field(..., max_length=200)
    type: Optional[str] = Field(None, max_length=100)
    muscle_group: Optional[str] = Field(None, max_length=100)
    equipment: Optional[str] = Field(None, max_length=100)
    level: Optional[Literal["beginner", "intermediate", "expert"]] = None
    instructions: Optional[str] = None

    # Champs français (traduction automatique deep-translator)
    name_fr: Optional[str] = Field(None, max_length=200)
    type_fr: Optional[str] = Field(None, max_length=100)
    muscle_group_fr: Optional[str] = Field(None, max_length=100)
    equipment_fr: Optional[str] = Field(None, max_length=100)
    level_fr: Optional[str] = Field(None, max_length=50)
    instructions_fr: Optional[str] = None

    # Médias
    gif_url:   Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None


class ExerciseResponse(ExerciseCreate):
    """Données renvoyées par l'API pour un exercice (GET /exercises).

    Le front-end utilise le paramètre ?lang=fr pour afficher les champs _fr
    à la place des champs anglais dans la liste déroulante de langue.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int


# =============================================================================
# FOOD LOG
# Journal alimentaire journalier par utilisateur
# =============================================================================

class FoodLogCreate(BaseModel):
    """Données requises pour enregistrer un repas (POST / PUT /nutrition/logs)."""

    user_id: int
    food_id: int
    log_date: Optional[date] = None       # Défaut côté BDD : CURRENT_DATE
    meal_type: Optional[Literal["breakfast", "lunch", "dinner", "snack"]] = None
    quantity_g: float = Field(..., gt=0)
    calories_consumed: Optional[float] = Field(
        None, ge=0,
        description="Calculé par ETL : (foods.calories_per_100g / 100) * quantity_g"
    )


class FoodLogResponse(FoodLogCreate):
    """Données renvoyées par l'API pour une entrée du journal alimentaire (GET /nutrition/logs)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    log_date: date                        # Toujours présent en sortie


# =============================================================================
# WORKOUT SESSION
# Sessions d'entraînement d'un utilisateur
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# =============================================================================

class WorkoutSessionCreate(BaseModel):
    """Données requises pour créer une session d'entraînement (POST / PUT /exercises/sessions)."""

    user_id: int
    session_date: Optional[date] = None  # Défaut côté BDD : CURRENT_DATE
    duration_min: Optional[int] = Field(None, gt=0)
    calories_burned: Optional[float] = Field(None, ge=0)
    avg_bpm: Optional[float] = Field(None, gt=0, description="Fréquence cardiaque moyenne durant la session")
    max_bpm: Optional[float] = Field(None, gt=0, description="Fréquence cardiaque maximale atteinte")


class WorkoutSessionResponse(WorkoutSessionCreate):
    """Données renvoyées par l'API pour une session d'entraînement (GET /exercises/sessions)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_date: date                   # Toujours présent en sortie


# =============================================================================
# SESSION EXERCISE
# Table de liaison N-N entre workout_sessions et exercises
# =============================================================================

class SessionExerciseCreate(BaseModel):
    """Données requises pour associer un exercice à une session (POST / PUT /exercises/sessions/{id}/exercises)."""

    session_id: int
    exercise_id: int
    sets: Optional[int] = Field(None, gt=0)
    reps: Optional[int] = Field(None, gt=0)
    duration_sec: Optional[int] = Field(
        None, gt=0,
        description="Durée en secondes, pour exercices chronométrés (planche, cardio...)"
    )


class SessionExerciseResponse(SessionExerciseCreate):
    """Données renvoyées par l'API pour un exercice d'une session (GET /exercises/sessions/{id}/exercises)."""

    model_config = ConfigDict(from_attributes=True)

    id: int


# =============================================================================
# BIOMETRIC METRIC
# Suivi biométrique dans le temps, séparé du profil statique users
# =============================================================================

class BiometricMetricCreate(BaseModel):
    """Données requises pour enregistrer une mesure biométrique (POST / PUT /metrics)."""

    user_id: int
    record_date: Optional[date] = None   # Défaut côté BDD : CURRENT_DATE
    weight_kg: Optional[float] = Field(None, gt=0)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    resting_bpm: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, description="Observations libres : fatigue, maladie, conditions particulières")


class BiometricMetricResponse(BiometricMetricCreate):
    """Données renvoyées par l'API pour une mesure biométrique (GET /metrics)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    record_date: date                    # Toujours présent en sortie
