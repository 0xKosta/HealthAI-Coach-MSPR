import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = ROOT_DIR / "logs"

for d in (RAW_DIR, PROCESSED_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

NUTRITION_CSV = RAW_DIR / "daily_food_nutrition_dataset.csv"
GYM_CSV = RAW_DIR / "gym_members_exercise_tracking.csv"
EXERCISES_JSON = RAW_DIR / "exercises.json"

DATABASE_URL = os.getenv("DATABASE_URL")

# Doivent correspondre à init.sql
TBL_USERS = "users"
TBL_FOOD_LOGS = "food_logs"
TBL_GYM_SESSIONS = "gym_sessions"
TBL_EXERCISES = "exercises"

CHUNK_SIZE = int(os.getenv("ETL_CHUNK_SIZE", "50000"))

# Clés utilisées par ON CONFLICT lors de l'upsert
CONFLICT_KEYS: dict[str, list[str]] = {
    TBL_USERS:        ["user_id"],
    TBL_FOOD_LOGS:    ["user_id", "date", "meal_type", "food_item"],
    TBL_GYM_SESSIONS: ["user_id"],
    TBL_EXERCISES:    ["id"],
}

MAX_NULL_RATE = 0.30
MIN_AGE, MAX_AGE = 10, 100
MIN_WEIGHT_KG, MAX_WEIGHT_KG = 30, 250
MIN_HEIGHT_M, MAX_HEIGHT_M = 1.0, 2.5
MIN_CALORIES = 0
MAX_CALORIES_MEAL = 5000
MAX_CALORIES_SESSION = 3000
MIN_BPM, MAX_BPM = 30, 250

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "etl.log"