# api/models.py
# Modèles SQLAlchemy — générés à partir de db/init.sql (Rôle B)
# Ordre : tables sans FK d'abord, puis tables dépendantes, puis table de liaison

from sqlalchemy import (
    Column, Integer, Float, String, Text, Date, CheckConstraint,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


# =============================================================================
# TABLE : users
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# Contient les profils statiques des utilisateurs
# =============================================================================
class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(100), nullable=False)
    age          = Column(Integer, nullable=False)
    gender       = Column(String(10))
    weight_kg    = Column(Float)
    height_cm    = Column(Float)
    bmi          = Column(Float)                    # Calculé à l'ingestion par le pipeline ETL
    body_fat_pct = Column(Float)
    goal         = Column(String(50))
    created_at   = Column(Date, nullable=False, server_default=func.current_date())

    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120",              name="ck_users_age"),
        CheckConstraint("gender IN ('male', 'female', 'other')", name="ck_users_gender"),
        CheckConstraint("weight_kg > 0",                        name="ck_users_weight_kg"),
        CheckConstraint("height_cm > 0",                        name="ck_users_height_cm"),
        CheckConstraint("body_fat_pct >= 0 AND body_fat_pct <= 100", name="ck_users_body_fat_pct"),
        CheckConstraint(
            "goal IN ('weight_loss', 'muscle_gain', 'sleep_improvement', 'maintenance')",
            name="ck_users_goal"
        ),
    )

    # Relations
    food_logs         = relationship("FoodLog",         back_populates="user", cascade="all, delete-orphan")
    workout_sessions  = relationship("WorkoutSession",  back_populates="user", cascade="all, delete-orphan")
    biometric_metrics = relationship("BiometricMetric", back_populates="user", cascade="all, delete-orphan")


# =============================================================================
# TABLE : foods
# Source : Daily Food & Nutrition Dataset (Kaggle, CSV)
# Catalogue des aliments avec valeurs nutritionnelles pour 100g
# =============================================================================
class Food(Base):
    __tablename__ = "foods"

    id                = Column(Integer, primary_key=True)
    name              = Column(String(200), nullable=False)
    category          = Column(String(100))         # ex : fruits, légumes, viandes, céréales...
    calories_per_100g = Column(Float, nullable=False)  # Valeur calorique pour 100g de produit
    proteins_g        = Column(Float)
    carbs_g           = Column(Float)
    fats_g            = Column(Float)
    fiber_g           = Column(Float)

    __table_args__ = (
        CheckConstraint("calories_per_100g >= 0", name="ck_foods_calories_per_100g"),
        CheckConstraint("proteins_g >= 0",        name="ck_foods_proteins_g"),
        CheckConstraint("carbs_g >= 0",           name="ck_foods_carbs_g"),
        CheckConstraint("fats_g >= 0",            name="ck_foods_fats_g"),
        CheckConstraint("fiber_g >= 0",           name="ck_foods_fiber_g"),
    )

    # Relations
    food_logs = relationship("FoodLog", back_populates="food")


# =============================================================================
# TABLE : exercises
# Source : ExerciseDB (GitHub, JSON)
# Catalogue de 1300+ exercices sportifs
# =============================================================================
class Exercise(Base):
    __tablename__ = "exercises"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(200), nullable=False)
    type         = Column(String(100))              # cardio, strength, flexibility, balance...
    muscle_group = Column(String(100))              # Groupe musculaire principal ciblé
    equipment    = Column(String(100))              # barbell, dumbbell, bodyweight, cable...
    level        = Column(String(50))               # beginner, intermediate, expert
    instructions = Column(Text)

    __table_args__ = (
        CheckConstraint(
            "level IN ('beginner', 'intermediate', 'expert')",
            name="ck_exercises_level"
        ),
    )

    # Relations
    session_exercises = relationship("SessionExercise", back_populates="exercise")


# =============================================================================
# TABLE : food_logs
# Historique des repas journaliers par utilisateur
# Relation N-N résolue : un utilisateur -> plusieurs entrées par jour
# =============================================================================
class FoodLog(Base):
    __tablename__ = "food_logs"

    id                = Column(Integer, primary_key=True)
    user_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id           = Column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    log_date          = Column(Date, nullable=False, server_default=func.current_date())
    meal_type         = Column(String(20))          # breakfast, lunch, dinner, snack
    quantity_g        = Column(Float, nullable=False)
    calories_consumed = Column(Float)               # Calculé par ETL : (calories_per_100g / 100) * quantity_g

    __table_args__ = (
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_food_logs_meal_type"
        ),
        CheckConstraint("quantity_g > 0",          name="ck_food_logs_quantity_g"),
        CheckConstraint("calories_consumed >= 0",  name="ck_food_logs_calories_consumed"),
    )

    # Relations
    user = relationship("User", back_populates="food_logs")
    food = relationship("Food", back_populates="food_logs")


# =============================================================================
# TABLE : workout_sessions
# Sessions d'entraînement d'un utilisateur
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# =============================================================================
class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_date    = Column(Date, nullable=False, server_default=func.current_date())
    duration_min    = Column(Integer)
    calories_burned = Column(Float)
    avg_bpm         = Column(Float)                 # Fréquence cardiaque moyenne durant la session
    max_bpm         = Column(Float)                 # Fréquence cardiaque maximale atteinte

    __table_args__ = (
        CheckConstraint("duration_min > 0",    name="ck_workout_sessions_duration_min"),
        CheckConstraint("calories_burned >= 0", name="ck_workout_sessions_calories_burned"),
        CheckConstraint("avg_bpm > 0",         name="ck_workout_sessions_avg_bpm"),
        CheckConstraint("max_bpm > 0",         name="ck_workout_sessions_max_bpm"),
    )

    # Relations
    user              = relationship("User", back_populates="workout_sessions")
    session_exercises = relationship("SessionExercise", back_populates="session", cascade="all, delete-orphan")


# =============================================================================
# TABLE : session_exercises
# Table de liaison N-N entre workout_sessions et exercises
# Porte les données propres à chaque occurrence (sets, reps, durée)
# =============================================================================
class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id           = Column(Integer, primary_key=True)
    session_id   = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"),  nullable=False)
    exercise_id  = Column(Integer, ForeignKey("exercises.id",        ondelete="RESTRICT"), nullable=False)
    sets         = Column(Integer)
    reps         = Column(Integer)
    duration_sec = Column(Integer)                  # Durée en secondes, pour exercices chronométrés (planche, cardio...)

    __table_args__ = (
        CheckConstraint("sets > 0",         name="ck_session_exercises_sets"),
        CheckConstraint("reps > 0",         name="ck_session_exercises_reps"),
        CheckConstraint("duration_sec > 0", name="ck_session_exercises_duration_sec"),
    )

    # Relations
    session  = relationship("WorkoutSession", back_populates="session_exercises")
    exercise = relationship("Exercise",       back_populates="session_exercises")


# =============================================================================
# TABLE : biometric_metrics
# Suivi biométrique dans le temps, séparé du profil statique users
# Les données évoluent dans le temps → table dédiée pour l'historique
# =============================================================================
class BiometricMetric(Base):
    __tablename__ = "biometric_metrics"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_date  = Column(Date, nullable=False, server_default=func.current_date())
    weight_kg    = Column(Float)
    sleep_hours  = Column(Float)
    resting_bpm  = Column(Float)
    notes        = Column(Text)                     # Observations libres : fatigue, maladie, conditions particulières

    __table_args__ = (
        CheckConstraint("weight_kg > 0",                       name="ck_biometric_weight_kg"),
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24", name="ck_biometric_sleep_hours"),
        CheckConstraint("resting_bpm > 0",                     name="ck_biometric_resting_bpm"),
    )

    # Relations
    user = relationship("User", back_populates="biometric_metrics")
