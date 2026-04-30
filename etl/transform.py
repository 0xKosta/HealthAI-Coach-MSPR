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
    coerced_types: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def merge(self, other: "QualityReport") -> "QualityReport":
        self.rows_in += other.rows_in
        self.rows_out += other.rows_out
        self.dropped_required_null += other.dropped_required_null
        self.dropped_out_of_range += other.dropped_out_of_range
        self.dropped_duplicates += other.dropped_duplicates
        for t in other.coerced_types:
            if t not in self.coerced_types:
                self.coerced_types.append(t)
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


def transform_nutrition(df, id_offset=0):
    rep = QualityReport(source="food_logs", rows_in=len(df))
    df = df.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    # user_id et date absents du dataset, on les génère
    df = df.reset_index(drop=True)
    df["user_id"] = "FOOD_" + (df.index + id_offset + 1).astype(str).str.zfill(8)
    today = date.today()
    df["date"] = [today - timedelta(days=int(i)) for i in (df.index + id_offset)]
    df["date"] = pd.to_datetime(df["date"])
    rep.notes.append("user_id et date générés (absents du dataset).")
    rep.coerced_types.append("date -> datetime")

    for c in ("meal_type", "food_item", "category"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    numeric_cols = [
        "calories_kcal", "protein_g", "carbohydrates_g", "fat_g",
        "fiber_g", "sugars_g", "sodium_mg", "cholesterol_mg", "water_intake_ml",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = _drop_required_nulls(df, ["food_item"], rep)
    df = _drop_out_of_range(df, "calories_kcal",
                            config.MIN_CALORIES, config.MAX_CALORIES_MEAL, rep)
    for c in ("protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugars_g"):
        df = _drop_out_of_range(df, c, 0, 1000, rep)

    df = _drop_dups(df, rep, subset=["user_id", "date", "meal_type", "food_item"])

    rep.rows_out = len(df)
    logger.info(rep.summary())
    return df, rep


def transform_gym(df, id_offset=0):
    rep = QualityReport(source="gym_sessions", rows_in=len(df))
    df = df.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    # user_id absent du dataset, on le génère
    df = df.reset_index(drop=True)
    df["user_id"] = "GYM_" + (df.index + id_offset + 1).astype(str).str.zfill(8)
    rep.notes.append("user_id généré (absent du dataset).")

    for c in ("gender", "workout_type"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    numeric_cols = [
        "age", "weight_kg", "height_m",
        "max_bpm", "avg_bpm", "resting_bpm",
        "session_duration_hours", "calories_burned", "fat_percentage",
        "water_intake_liters", "workout_frequency_days_week",
        "experience_level", "bmi",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = _drop_required_nulls(df, ["age", "gender", "weight_kg", "height_m"], rep)
    df = _drop_out_of_range(df, "age", config.MIN_AGE, config.MAX_AGE, rep)
    df = _drop_out_of_range(df, "weight_kg",
                            config.MIN_WEIGHT_KG, config.MAX_WEIGHT_KG, rep)
    df = _drop_out_of_range(df, "height_m",
                            config.MIN_HEIGHT_M, config.MAX_HEIGHT_M, rep)
    df = _drop_out_of_range(df, "calories_burned",
                            0, config.MAX_CALORIES_SESSION, rep)
    for c in ("max_bpm", "avg_bpm", "resting_bpm"):
        df = _drop_out_of_range(df, c, config.MIN_BPM, config.MAX_BPM, rep)

    df = _drop_dups(df, rep)

    rep.rows_out = len(df)
    logger.info(rep.summary())
    return df, rep


def transform_exercises(df):
    rep = QualityReport(source="exercises", rows_in=len(df))
    df = df.copy()

    rename = {
        "id": "id",
        "name": "name",
        "force": "force",
        "level": "level",
        "mechanic": "mechanic",
        "equipment": "equipment",
        "primaryMuscles": "primary_muscles",
        "secondaryMuscles": "secondary_muscles",
        "instructions": "instructions",
        "category": "category",
        "images": "images",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df = _drop_required_nulls(df, ["id", "name"], rep)

    for c in ("name", "force", "level", "mechanic", "equipment", "category"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    # Listes JSON aplaties en texte séparé par " | "
    for c in ("primary_muscles", "secondary_muscles", "instructions", "images"):
        if c in df.columns:
            df[c] = df[c].apply(
                lambda v: " | ".join(map(str, v)) if isinstance(v, list)
                else (str(v) if pd.notna(v) else "")
            )

    df = _drop_dups(df, rep, subset=["id"])

    rep.rows_out = len(df)
    logger.info(rep.summary())
    return df, rep


USER_PROFILE_COLS = [
    "user_id", "age", "gender", "weight_kg", "height_m",
    "experience_level", "bmi",
]


def build_users_from_gym(df_gym):
    cols = [c for c in USER_PROFILE_COLS if c in df_gym.columns]
    return (df_gym[cols]
            .drop_duplicates(subset=["user_id"])
            .reset_index(drop=True))


def split_users_and_sessions(df_gym):
    df_users = build_users_from_gym(df_gym)
    df_sessions = df_gym.drop(
        columns=[c for c in USER_PROFILE_COLS
                 if c in df_gym.columns and c != "user_id"]
    )
    return df_users, df_sessions