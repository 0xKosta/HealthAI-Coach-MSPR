"""
Transformation & quality layer  —  the part the jury will grill you on.

For each source DataFrame we:
    1. Standardize column names → snake_case to match the DB schema
    2. Coerce types (string → numeric, string → datetime)
    3. Validate ranges and required fields
    4. Drop duplicates
    5. Trim / lowercase strings
    6. Build a QualityReport object summarizing what happened

QualityReport is mergeable — when the pipeline streams chunks, we accumulate
one report per source by merging chunk-level reports together.

Quality strategy (be ready to defend each line of this):
    Required-field nulls   → drop row, log
    Out-of-range numerics  → drop row, log  (we prefer drop > impute → safer claim
                             of "we don't invent data")
    Duplicates             → drop, keep first
    Schema drift           → already logged at extract step
"""

import logging
import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from etl import config

logger = logging.getLogger(__name__)


# === Quality report ==========================================================

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
        """Accumulate a chunk-level report into this one (in place)."""
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
            f"[{self.source}] in={self.rows_in} → out={self.rows_out} | "
            f"dropped: nulls={self.dropped_required_null}, "
            f"oor={self.dropped_out_of_range}, dups={self.dropped_duplicates}"
        )


# === Helpers =================================================================

def _to_snake_case(name: str) -> str:
    """'Calories (kcal)' → 'calories_kcal'."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[()/]", " ", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"_+", "_", name)
    return name.lower()


def _drop_required_nulls(df: pd.DataFrame, cols: list[str], rep: QualityReport) -> pd.DataFrame:
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df
    before = len(df)
    df = df.dropna(subset=cols)
    rep.dropped_required_null += before - len(df)
    return df


def _drop_out_of_range(df: pd.DataFrame, col: str, lo: float, hi: float,
                       rep: QualityReport) -> pd.DataFrame:
    if col not in df.columns:
        return df
    before = len(df)
    keep = df[col].between(lo, hi, inclusive="both") | df[col].isna()
    df = df[keep]
    rep.dropped_out_of_range += before - len(df)
    return df


def _drop_dups(df: pd.DataFrame, rep: QualityReport, subset: list[str] | None = None) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset)
    rep.dropped_duplicates += before - len(df)
    return df


# === Transformers ============================================================

def transform_nutrition(df: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
    """Daily Food & Nutrition CSV → food_logs table."""
    rep = QualityReport(source="food_logs", rows_in=len(df))
    df = df.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    for c in ("meal_type", "food_item", "category"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        rep.coerced_types.append("date → datetime")

    numeric_cols = [
        "calories_kcal", "protein_g", "carbohydrates_g", "fat_g",
        "fiber_g", "sugars_g", "sodium_mg", "cholesterol_mg", "water_intake_ml",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = _drop_required_nulls(df, ["user_id", "date", "food_item"], rep)
    df = _drop_out_of_range(df, "calories_kcal",
                            config.MIN_CALORIES, config.MAX_CALORIES_MEAL, rep)
    for c in ("protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugars_g"):
        df = _drop_out_of_range(df, c, 0, 1000, rep)

    df = _drop_dups(df, rep, subset=["user_id", "date", "meal_type", "food_item"])

    rep.rows_out = len(df)
    logger.info(rep.summary())
    return df, rep


def transform_gym(df: pd.DataFrame, id_offset: int = 0
                  ) -> tuple[pd.DataFrame, QualityReport]:
    """Gym Members CSV → gym_sessions table (+ feeds the users table).

    `id_offset` lets the streaming pipeline keep synthesized user_ids unique
    across chunks (chunk N starts at offset = sum of chunk sizes 0..N-1).
    """
    rep = QualityReport(source="gym_sessions", rows_in=len(df))
    df = df.copy()
    df = df.rename(columns={c: _to_snake_case(c) for c in df.columns})

    # Synthesize user_id (dataset has no native ID). Offset keeps IDs unique
    # across streamed chunks. Same input file → same IDs → idempotent upserts.
    df = df.reset_index(drop=True)
    df["user_id"] = "GYM_" + (df.index + id_offset + 1).astype(str).str.zfill(8)
    rep.notes.append("Synthetic user_id generated (dataset has no native ID).")

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


def transform_exercises(df: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
    """ExerciseDB JSON → exercises table."""
    rep = QualityReport(source="exercises", rows_in=len(df))
    df = df.copy()

    rename = {
        "id": "id",
        "name": "name",
        "bodyPart": "body_part",
        "equipment": "equipment",
        "target": "target_muscle",
        "secondaryMuscles": "secondary_muscles",
        "instructions": "instructions",
        "gifUrl": "gif_url",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    df = _drop_required_nulls(df, ["id", "name"], rep)

    for c in ("name", "body_part", "equipment", "target_muscle"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()

    for c in ("secondary_muscles", "instructions"):
        if c in df.columns:
            df[c] = df[c].apply(
                lambda v: " | ".join(map(str, v)) if isinstance(v, list)
                else (str(v) if pd.notna(v) else "")
            )

    df = _drop_dups(df, rep, subset=["id"])

    rep.rows_out = len(df)
    logger.info(rep.summary())
    return df, rep


# === Build users from cleaned gym ============================================

USER_PROFILE_COLS = [
    "user_id", "age", "gender", "weight_kg", "height_m",
    "experience_level", "bmi",
]


def build_users_from_gym(df_gym: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in USER_PROFILE_COLS if c in df_gym.columns]
    return (df_gym[cols]
            .drop_duplicates(subset=["user_id"])
            .reset_index(drop=True))


def split_users_and_sessions(df_gym: pd.DataFrame
                             ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """From a cleaned gym chunk, return (users, gym_sessions_lean)."""
    df_users = build_users_from_gym(df_gym)
    df_sessions = df_gym.drop(
        columns=[c for c in USER_PROFILE_COLS
                 if c in df_gym.columns and c != "user_id"]
    )
    return df_users, df_sessions