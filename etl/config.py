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

TBL_USERS = "users"
TBL_FOODS = "foods"
TBL_EXERCISES = "exercises"
TBL_FOOD_LOGS = "food_logs"
TBL_WORKOUT_SESSIONS = "workout_sessions"

CHUNK_SIZE = int(os.getenv("ETL_CHUNK_SIZE", "50000"))

# Base URL des images d'exercices (chemins relatifs dans le JSON ExerciseDB)
EXERCISE_IMAGE_BASE_URL = (
    "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
)
# Base URL d'une recherche YouTube (le dataset ne contient pas de vidéos)
EXERCISE_VIDEO_SEARCH_BASE_URL = (
    "https://www.youtube.com/results?search_query="
)

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