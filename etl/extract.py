import json
import logging
from typing import Iterator

import pandas as pd

from etl import config

logger = logging.getLogger(__name__)


EXPECTED_NUTRITION_COLS = {
    "Food_Item", "Category", "Meal_Type",
    "Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fat (g)",
    "Fiber (g)", "Sugars (g)", "Sodium (mg)", "Cholesterol (mg)",
    "Water_Intake (ml)",
}
EXPECTED_GYM_COLS = {
    "Age", "Gender", "Weight (kg)", "Height (m)",
    "Max_BPM", "Avg_BPM", "Resting_BPM", "Session_Duration (hours)",
    "Calories_Burned", "Workout_Type", "Fat_Percentage",
    "Water_Intake (liters)", "Workout_Frequency (days/week)",
    "Experience_Level", "BMI",
}
EXPECTED_EXERCISE_KEYS = {
    "id", "name", "force", "level", "mechanic", "equipment",
    "primaryMuscles", "secondaryMuscles", "instructions", "category", "images",
}


def _check_schema(actual: set, expected: set, source: str) -> None:
    missing = expected - actual
    extra = actual - expected
    if missing:
        logger.warning(f"[{source}] colonnes manquantes: {sorted(missing)}")
    if extra:
        logger.info(f"[{source}] colonnes en plus: {sorted(extra)}")


def extract_nutrition() -> pd.DataFrame:
    path = config.NUTRITION_CSV
    if not path.exists():
        raise FileNotFoundError(f"CSV nutrition introuvable: {path}")
    df = pd.read_csv(path)
    logger.info(f"[nutrition] {len(df)} lignes lues")
    _check_schema(set(df.columns), EXPECTED_NUTRITION_COLS, "nutrition")
    return df


def extract_gym() -> pd.DataFrame:
    path = config.GYM_CSV
    if not path.exists():
        raise FileNotFoundError(f"CSV gym introuvable: {path}")
    df = pd.read_csv(path)
    logger.info(f"[gym] {len(df)} lignes lues")
    _check_schema(set(df.columns), EXPECTED_GYM_COLS, "gym")
    return df


def extract_exercises() -> pd.DataFrame:
    path = config.EXERCISES_JSON
    if not path.exists():
        raise FileNotFoundError(f"JSON exercises introuvable: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Le JSON doit être une liste.")
    df = pd.DataFrame(data)
    logger.info(f"[exercises] {len(df)} exercices lus")
    _check_schema(set(df.columns), EXPECTED_EXERCISE_KEYS, "exercises")
    return df


def extract_nutrition_chunks(chunksize: int | None = None) -> Iterator[pd.DataFrame]:
    path = config.NUTRITION_CSV
    if not path.exists():
        raise FileNotFoundError(f"CSV nutrition introuvable: {path}")
    chunksize = chunksize or config.CHUNK_SIZE
    total = 0
    schema_checked = False
    for chunk in pd.read_csv(path, chunksize=chunksize):
        if not schema_checked:
            _check_schema(set(chunk.columns), EXPECTED_NUTRITION_COLS, "nutrition")
            schema_checked = True
        total += len(chunk)
        yield chunk
    logger.info(f"[nutrition] {total} lignes streamées")


def extract_gym_chunks(chunksize: int | None = None) -> Iterator[pd.DataFrame]:
    path = config.GYM_CSV
    if not path.exists():
        raise FileNotFoundError(f"CSV gym introuvable: {path}")
    chunksize = chunksize or config.CHUNK_SIZE
    total = 0
    schema_checked = False
    for chunk in pd.read_csv(path, chunksize=chunksize):
        if not schema_checked:
            _check_schema(set(chunk.columns), EXPECTED_GYM_COLS, "gym")
            schema_checked = True
        total += len(chunk)
        yield chunk
    logger.info(f"[gym] {total} lignes streamées")