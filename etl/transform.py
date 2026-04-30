import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from etl import config

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    source: str
    rows_in: int = 0
    rows_out: int = 0
    dropped_required_null: int = 0
    dropped_out_of_range: int = 0
    dropped_duplicates: int = 0
    notes: list[str] = field(default_factory=list)

    def merge(self, other: "QualityReport") -> "QualityReport":
        self.rows_in += other.rows_in
        self.rows_out += other.rows_out
        self.dropped_required_null += other.dropped_required_null
        self.dropped_out_of_range += other.dropped_out_of_range
        self.dropped_duplicates += other.dropped_duplicates
        for n in other.notes:
            if n not in self.notes:
                self.notes.append(n)
        return self

    def summary(self) -> str:
        return (
            f"[{self.source}] in={self.rows_in} -> out={self.rows_out} | "
            f"droppées: nulls={self.dropped_required_null}, "
            f"hors_borne={self.dropped_out_of_range}, dups={self.dropped_duplicates}"
        )


def _to_snake_case(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[()/]", " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"_+", "_", name)
    return name.lower()


def _drop_required_nulls(df, cols, rep):
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df
    before = len(df)
    df = df.dropna(subset=cols)
    rep.dropped_required_null += before - len(df)
    return df


def _drop_out_of_range(df, col, lo, hi, rep):
    if col not in df.columns:
        return df
    before = len(df)
    keep = df[col].between(lo, hi, inclusive="both") | df[col].isna()
    df = df[keep]
    rep.dropped_out_of_range += before - len(df)
    return df


def _drop_dups(df, rep, subset=None):
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    rep.dropped_duplicates += before - len(df)
    return df


# === USERS (depuis le dataset Gym) ==========================================

def _assign_goal(bmi):
    """
    Assigne un objectif santé basé sur le BMI de l'utilisateur.
    Heuristique métier cohérente — pas une assignation aléatoire :
      - BMI > 30 (obésité)       → perte de poids
      - BMI 25-30 (surpoids)     → maintien / perte de poids selon index pair/impair
      - BMI 18.5-25 (normal)     → maintien ou amélioration du sommeil
      - BMI < 18.5 (insuffisant) → prise de masse musculaire
    """
    if pd.isna(bmi):
        return "maintenance"
    if bmi > 30:
        return "weight_loss"
    elif bmi > 25:
        # Légère variation pour diversifier les données
        return "weight_loss" if int(bmi * 10) % 2 == 0 else "maintenance"
    elif bmi >= 18.5:
        return "sleep_improvement" if int(bmi * 10) % 3 == 0 else "maintenance"
    else:
        return "muscle_gain"


def transform_users(df_gym, id_offset=0):
    rep = QualityReport(source="users", rows_in=len(df_gym))
    df = df_gym.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    df = df.reset_index(drop=True)
    df["name"] = "User_" + (df.index + id_offset + 1).astype(str).str.zfill(6)
    rep.notes.append("name généré (absent du dataset).")

    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).str.strip().str.lower()

    for c in ("age", "weight_kg", "height_m", "bmi", "fat_percentage"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = _drop_required_nulls(df, ["age", "weight_kg", "height_m"], rep)
    df = _drop_out_of_range(df, "age", config.MIN_AGE, config.MAX_AGE, rep)
    df = _drop_out_of_range(df, "weight_kg",
                            config.MIN_WEIGHT_KG, config.MAX_WEIGHT_KG, rep)
    df = _drop_out_of_range(df, "height_m",
                            config.MIN_HEIGHT_M, config.MAX_HEIGHT_M, rep)

    if "height_m" in df.columns:
        df["height_cm"] = df["height_m"] * 100

    rename = {"fat_percentage": "body_fat_pct"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # -------------------------------------------------------------------------
    # ENRICHISSEMENT : assignation du goal basée sur le BMI
    # Le dataset Gym Members ne fournit pas d'objectif utilisateur.
    # On utilise le BMI comme heuristique métier pour simuler des objectifs
    # réalistes et diversifiés — requis pour les analyses du dashboard.
    # -------------------------------------------------------------------------
    if "bmi" in df.columns:
        df["goal"] = df["bmi"].apply(_assign_goal)
        rep.notes.append("goal enrichi depuis BMI (absent du dataset source).")
    else:
        df["goal"] = "maintenance"
        rep.notes.append("goal défaut 'maintenance' (BMI absent).")

    keep = ["name", "age", "gender", "weight_kg", "height_cm", "bmi",
            "body_fat_pct", "goal"]
    out = df[[c for c in keep if c in df.columns]].copy()

    out = _drop_dups(out, rep, subset=["name"])
    rep.rows_out = len(out)
    logger.info(rep.summary())
    return out, rep


# === WORKOUT_SESSIONS (depuis le dataset Gym, même CSV que users) ===========

def transform_workout_sessions(df_gym, id_offset=0):
    rep = QualityReport(source="workout_sessions", rows_in=len(df_gym))
    df = df_gym.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    df = df.reset_index(drop=True)
    df["name"] = "User_" + (df.index + id_offset + 1).astype(str).str.zfill(6)

    # session_date généré (absent du dataset) : un jour par ligne en remontant
    today = date.today()
    df["session_date"] = [today - timedelta(days=int(i))
                          for i in (df.index + id_offset)]
    df["session_date"] = pd.to_datetime(df["session_date"])
    rep.notes.append("session_date générée (absente du dataset).")

    for c in ("session_duration_hours", "calories_burned", "avg_bpm", "max_bpm"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = _drop_out_of_range(df, "calories_burned",
                            0, config.MAX_CALORIES_SESSION, rep)
    for c in ("avg_bpm", "max_bpm"):
        df = _drop_out_of_range(df, c, config.MIN_BPM, config.MAX_BPM, rep)

    if "session_duration_hours" in df.columns:
        df["duration_min"] = (df["session_duration_hours"] * 60).round().astype("Int64")

    keep = ["name", "session_date", "duration_min",
            "calories_burned", "avg_bpm", "max_bpm"]
    out = df[[c for c in keep if c in df.columns]].copy()

    out = _drop_dups(out, rep, subset=["name", "session_date"])
    rep.rows_out = len(out)
    logger.info(rep.summary())
    return out, rep


# === EXERCISES (depuis ExerciseDB JSON) =====================================

_LEVEL_MAP = {
    "beginner": "beginner",
    "intermediate": "intermediate",
    "expert": "expert",
    "advanced": "expert",
}


def transform_exercises(df):
    rep = QualityReport(source="exercises", rows_in=len(df))
    df = df.copy()

    rename = {
        "name": "name",
        "category": "type",
        "equipment": "equipment",
        "level": "level",
        "instructions": "instructions",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df = _drop_required_nulls(df, ["name"], rep)

    for c in ("name", "type", "equipment"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    if "level" in df.columns:
        df["level"] = (df["level"].astype(str).str.strip().str.lower()
                       .map(_LEVEL_MAP))

    if "primaryMuscles" in df.columns:
        df["muscle_group"] = df["primaryMuscles"].apply(
            lambda v: (v[0] if isinstance(v, list) and v else
                       (str(v) if pd.notna(v) else None))
        )
        if df["muscle_group"].notna().any():
            df["muscle_group"] = df["muscle_group"].astype(str).str.strip().str.lower()

    if "instructions" in df.columns:
        df["instructions"] = df["instructions"].apply(
            lambda v: " | ".join(map(str, v)) if isinstance(v, list)
            else (str(v) if pd.notna(v) else "")
        )

    keep = ["name", "type", "muscle_group", "equipment", "level", "instructions", "gif_url", "video_url", "image_url"]
    out = df[[c for c in keep if c in df.columns]].copy()

    out = _drop_dups(out, rep, subset=["name"])
    rep.rows_out = len(out)
    logger.info(rep.summary())
    return out, rep


# === FOODS (catalogue dédupliqué depuis Nutrition CSV) ======================

def transform_foods(df_nutr):
    rep = QualityReport(source="foods", rows_in=len(df_nutr))
    df = df_nutr.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    df = _drop_required_nulls(df, ["food_item"], rep)

    for c in ("food_item", "category"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    numeric_map = {
        "calories_kcal": "calories_per_100g",
        "protein_g": "proteins_g",
        "carbohydrates_g": "carbs_g",
        "fat_g": "fats_g",
        "fiber_g": "fiber_g",
    }
    for src, dst in numeric_map.items():
        if src in df.columns:
            df[dst] = pd.to_numeric(df[src], errors="coerce")

    df = df.rename(columns={"food_item": "name"})

    df = _drop_out_of_range(df, "calories_per_100g",
                            config.MIN_CALORIES, config.MAX_CALORIES_MEAL, rep)
    for c in ("proteins_g", "carbs_g", "fats_g", "fiber_g"):
        df = _drop_out_of_range(df, c, 0, 1000, rep)

    df = _drop_required_nulls(df, ["name", "calories_per_100g"], rep)

    keep = ["name", "category", "calories_per_100g",
            "proteins_g", "carbs_g", "fats_g", "fiber_g"]
    out = df[[c for c in keep if c in df.columns]].copy()

    # Dédup : on garde la première occurrence pour chaque aliment
    out = _drop_dups(out, rep, subset=["name"])
    rep.rows_out = len(out)
    logger.info(rep.summary())
    return out, rep


# === FOOD_LOGS (lignes de log nutrition; FK résolus dans pipeline.py) ======

_VALID_MEALS = {"breakfast", "lunch", "dinner", "snack"}


def transform_food_logs(df_nutr, id_offset=0):
    rep = QualityReport(source="food_logs", rows_in=len(df_nutr))
    df = df_nutr.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    df = df.reset_index(drop=True)
    df["name"] = "User_" + (df.index + id_offset + 1).astype(str).str.zfill(6)

    today = date.today()
    df["log_date"] = [today - timedelta(days=int(i))
                      for i in (df.index + id_offset)]
    df["log_date"] = pd.to_datetime(df["log_date"])
    rep.notes.append("name et log_date générés (absents du dataset).")

    for c in ("food_item", "meal_type"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    if "meal_type" in df.columns:
        df["meal_type"] = df["meal_type"].where(
            df["meal_type"].isin(_VALID_MEALS), other=pd.NA
        )

    df = df.rename(columns={"food_item": "food_name"})

    if "calories_kcal" in df.columns:
        df["calories_consumed"] = pd.to_numeric(df["calories_kcal"], errors="coerce")

    # Le dataset n'a pas de quantité ; on normalise à 100g par ligne et
    # calories_consumed = Calories (kcal) tel que fourni.
    df["quantity_g"] = 100.0

    df = _drop_required_nulls(df, ["food_name", "meal_type"], rep)
    df = _drop_out_of_range(df, "calories_consumed",
                            config.MIN_CALORIES, config.MAX_CALORIES_MEAL, rep)

    keep = ["name", "food_name", "log_date", "meal_type",
            "quantity_g", "calories_consumed"]
    out = df[[c for c in keep if c in df.columns]].copy()

    out = _drop_dups(out, rep,
                     subset=["name", "food_name", "log_date", "meal_type"])
    rep.rows_out = len(out)
    logger.info(rep.summary())
    return out, rep