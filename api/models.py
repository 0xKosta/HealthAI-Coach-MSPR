# Modèles SQLAlchemy — générés à partir de db/init.sql (Rôle B)
# Ordre : tables sans FK d'abord, puis tables dépendantes, puis table de liaison

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


# =============================================================================
# TABLE : users
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# Contient les profils statiques des utilisateurs
# =============================================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10))
    weight_kg: Mapped[float | None] = mapped_column(Float)
    height_cm: Mapped[float | None] = mapped_column(Float)
    bmi: Mapped[float | None] = mapped_column(Float)  # Calculé à l'ingestion par le pipeline ETL
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    goal: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())

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
    food_logs: Mapped[list[FoodLog]] = relationship(back_populates="user", cascade="all, delete-orphan")
    workout_sessions: Mapped[list[WorkoutSession]] = relationship(back_populates="user", cascade="all, delete-orphan")
    biometric_metrics: Mapped[list[BiometricMetric]] = relationship(back_populates="user", cascade="all, delete-orphan")


# =============================================================================
# TABLE : foods
# Source : Daily Food & Nutrition Dataset (Kaggle, CSV)
# Catalogue des aliments avec valeurs nutritionnelles pour 100g
# =============================================================================
class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))  # ex : fruits, légumes, viandes, céréales...
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False)  # Valeur calorique pour 100g de produit
    proteins_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fats_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint("calories_per_100g >= 0", name="ck_foods_calories_per_100g"),
        CheckConstraint("proteins_g >= 0",        name="ck_foods_proteins_g"),
        CheckConstraint("carbs_g >= 0",           name="ck_foods_carbs_g"),
        CheckConstraint("fats_g >= 0",            name="ck_foods_fats_g"),
        CheckConstraint("fiber_g >= 0",           name="ck_foods_fiber_g"),
    )

    # Relations
    food_logs: Mapped[list[FoodLog]] = relationship(back_populates="food")


# =============================================================================
# TABLE : exercises
# Source : ExerciseDB (GitHub, JSON)
# Catalogue de 1300+ exercices sportifs
# =============================================================================
class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Champs en anglais (source ExerciseDB)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str | None] = mapped_column(String(100))
    muscle_group: Mapped[str | None] = mapped_column(String(100))
    equipment: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str | None] = mapped_column(String(50))
    instructions: Mapped[str | None] = mapped_column(Text)

    # Champs traduits en français (v1.3 — internationalisation EN/FR)
    name_fr: Mapped[str | None] = mapped_column(String(200))
    type_fr: Mapped[str | None] = mapped_column(String(100))
    muscle_group_fr: Mapped[str | None] = mapped_column(String(100))
    equipment_fr: Mapped[str | None] = mapped_column(String(100))
    level_fr: Mapped[str | None] = mapped_column(String(50))
    instructions_fr: Mapped[str | None] = mapped_column(Text)

    # Médias
    gif_url: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "level IN ('beginner', 'intermediate', 'expert')",
            name="ck_exercises_level"
        ),
    )

    # Relations
    session_exercises: Mapped[list[SessionExercise]] = relationship(back_populates="exercise")


# =============================================================================
# TABLE : food_logs
# Historique des repas journaliers par utilisateur
# Relation N-N résolue : un utilisateur -> plusieurs entrées par jour
# =============================================================================
class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id: Mapped[int] = mapped_column(Integer, ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    meal_type: Mapped[str | None] = mapped_column(String(20))  # breakfast, lunch, dinner, snack
    quantity_g: Mapped[float] = mapped_column(Float, nullable=False)
    calories_consumed: Mapped[float | None] = mapped_column(Float)  # Calculé par ETL : (calories_per_100g / 100) * quantity_g

    __table_args__ = (
        CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="ck_food_logs_meal_type"
        ),
        CheckConstraint("quantity_g > 0",          name="ck_food_logs_quantity_g"),
        CheckConstraint("calories_consumed >= 0",  name="ck_food_logs_calories_consumed"),
    )

    # Relations
    user: Mapped[User] = relationship(back_populates="food_logs")
    food: Mapped[Food] = relationship(back_populates="food_logs")


# =============================================================================
# TABLE : workout_sessions
# Sessions d'entraînement d'un utilisateur
# Source : Gym Members Exercise Dataset (Kaggle, CSV)
# =============================================================================
class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    duration_min: Mapped[int | None] = mapped_column(Integer)
    calories_burned: Mapped[float | None] = mapped_column(Float)
    avg_bpm: Mapped[float | None] = mapped_column(Float)  # Fréquence cardiaque moyenne durant la session
    max_bpm: Mapped[float | None] = mapped_column(Float)  # Fréquence cardiaque maximale atteinte

    __table_args__ = (
        CheckConstraint("duration_min > 0",    name="ck_workout_sessions_duration_min"),
        CheckConstraint("calories_burned >= 0", name="ck_workout_sessions_calories_burned"),
        CheckConstraint("avg_bpm > 0",         name="ck_workout_sessions_avg_bpm"),
        CheckConstraint("max_bpm > 0",         name="ck_workout_sessions_max_bpm"),
    )

    # Relations
    user: Mapped[User] = relationship(back_populates="workout_sessions")
    session_exercises: Mapped[list[SessionExercise]] = relationship(back_populates="session", cascade="all, delete-orphan")


# =============================================================================
# TABLE : session_exercises
# Table de liaison N-N entre workout_sessions et exercises
# Porte les données propres à chaque occurrence (sets, reps, durée)
# =============================================================================
class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[int | None] = mapped_column(Integer)
    duration_sec: Mapped[int | None] = mapped_column(Integer)  # Durée en secondes, pour exercices chronométrés (planche, cardio...)

    __table_args__ = (
        CheckConstraint("sets > 0",         name="ck_session_exercises_sets"),
        CheckConstraint("reps > 0",         name="ck_session_exercises_reps"),
        CheckConstraint("duration_sec > 0", name="ck_session_exercises_duration_sec"),
    )

    # Relations
    session: Mapped[WorkoutSession] = relationship(back_populates="session_exercises")
    exercise: Mapped[Exercise] = relationship(back_populates="session_exercises")


# =============================================================================
# TABLE : biometric_metrics
# Suivi biométrique dans le temps, séparé du profil statique users
# Les données évoluent dans le temps → table dédiée pour l'historique
# =============================================================================
class BiometricMetric(Base):
    __tablename__ = "biometric_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    weight_kg: Mapped[float | None] = mapped_column(Float)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    resting_bpm: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)  # Observations libres : fatigue, maladie, conditions particulières

    __table_args__ = (
        CheckConstraint("weight_kg > 0",                       name="ck_biometric_weight_kg"),
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24", name="ck_biometric_sleep_hours"),
        CheckConstraint("resting_bpm > 0",                     name="ck_biometric_resting_bpm"),
    )

    # Relations
    user: Mapped[User] = relationship(back_populates="biometric_metrics")

# =============================================================================
# TABLE : user_auth  (authentification réseau social)
# =============================================================================
class UserAuth(Base):
    __tablename__ = "user_auth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])


# =============================================================================
# TABLE : posts  (publications du feed social)
# =============================================================================
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_auth.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

    author: Mapped[UserAuth] = relationship(back_populates="posts")