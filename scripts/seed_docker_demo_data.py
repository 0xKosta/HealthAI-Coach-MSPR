#!/usr/bin/env python3
"""
Jeu de données de démonstration Docker — 10 users, auth, exercices, séances, biométrie.

Source : db/seed/docker_demo_data.json (export Supabase allégé).
Ne pas exécuter contre Supabase prod. Activé via SEED_DOCKER_DEMO_DATA=true.

Le feed social (posts/likes) reste hors seed — démo manuelle à l'oral.
L'admin (admin@admin.com) est créé après ce seed par seed_docker_demo_admin.py.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = ROOT / "db" / "seed" / "docker_demo_data.json"
MARKER_EMAIL = "tom.thomas.1@healthai-coach.demo"

SECTION_ALIASES = {
    "exercices": "exercises",
}


def _parse_sections(path: Path) -> dict[str, list]:
    text = path.read_text(encoding="utf-8")
    sections: dict[str, list] = {}
    for match in re.finditer(r"//\s*(\w+)\s*\n", text):
        name = match.group(1).strip()
        start = match.end()
        next_comment = re.search(r"\n//\s*\w+\s*\n", text[start:])
        end = start + next_comment.start() if next_comment else len(text)
        block = text[start:end].strip()
        arr_start = block.find("[")
        arr_end = block.rfind("]")
        if arr_start < 0 or arr_end <= arr_start:
            raise ValueError(f"Section // {name} : tableau JSON introuvable")
        sections[name] = json.loads(block[arr_start : arr_end + 1])
    return sections


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _row_without_idx(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "idx"}


def _reset_sequences(db, tables: list[tuple[str, str]]) -> None:
    from sqlalchemy import text

    for table, column in tables:
        db.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', '{column}'),
                    COALESCE((SELECT MAX({column}) FROM {table}), 1)
                )
                """
            )
        )


def main() -> int:
    if os.getenv("SEED_DOCKER_DEMO_DATA", "").lower() not in ("1", "true", "yes"):
        return 0

    if not DATA_FILE.is_file():
        logger.error("Fichier introuvable : %s", DATA_FILE)
        return 1

    from api.database import SessionLocal
    from api.models import BiometricMetric, Exercise, User, UserAuth, WorkoutSession

    db = SessionLocal()
    try:
        if db.query(UserAuth).filter(UserAuth.email == MARKER_EMAIL).first():
            logger.info("Jeu de démo déjà présent (%s).", MARKER_EMAIL)
            return 0

        raw = _parse_sections(DATA_FILE)
        sections = {SECTION_ALIASES.get(k, k): v for k, v in raw.items()}

        for row in sections.get("users", []):
            data = _row_without_idx(row)
            created = data.pop("created_at", None)
            db.add(
                User(
                    id=data["id"],
                    name=data["name"],
                    age=data.get("age"),
                    gender=data.get("gender"),
                    weight_kg=data.get("weight_kg"),
                    height_cm=data.get("height_cm"),
                    bmi=data.get("bmi"),
                    body_fat_pct=data.get("body_fat_pct"),
                    goal=data.get("goal"),
                    created_at=_parse_date(created) or date.today(),
                )
            )
        db.flush()
        logger.info("users : %d profils", len(sections.get("users", [])))

        for row in sections.get("user_auth", []):
            data = _row_without_idx(row)
            created = data.pop("created_at", None)
            data.pop("updated_at", None)
            db.add(
                UserAuth(
                    id=data["id"],
                    user_id=data["user_id"],
                    email=data["email"],
                    password_hash=data["password_hash"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    avatar_url=data.get("avatar_url"),
                    role=data.get("role", "user"),
                    plan=data.get("plan", "free"),
                    created_at=_parse_date(created) or date.today(),
                )
            )
        db.flush()
        logger.info("user_auth : %d comptes (.demo, mot de passe ETL : 1234)", len(sections.get("user_auth", [])))

        for row in sections.get("exercises", []):
            data = _row_without_idx(row)
            db.add(Exercise(**data))
        db.flush()
        logger.info("exercises : %d entrées", len(sections.get("exercises", [])))

        for row in sections.get("workout_sessions", []):
            data = _row_without_idx(row)
            session_date = data.pop("session_date")
            db.add(
                WorkoutSession(
                    id=data["id"],
                    user_id=data["user_id"],
                    session_date=_parse_date(session_date) or date.today(),
                    duration_min=data.get("duration_min"),
                    calories_burned=data.get("calories_burned"),
                    avg_bpm=data.get("avg_bpm"),
                    max_bpm=data.get("max_bpm"),
                )
            )
        db.flush()
        logger.info("workout_sessions : %d séances", len(sections.get("workout_sessions", [])))

        for row in sections.get("biometric_metrics", []):
            data = _row_without_idx(row)
            record_date = data.pop("record_date")
            db.add(
                BiometricMetric(
                    id=data["id"],
                    user_id=data["user_id"],
                    record_date=_parse_date(record_date) or date.today(),
                    weight_kg=data.get("weight_kg"),
                    sleep_hours=data.get("sleep_hours"),
                    resting_bpm=data.get("resting_bpm"),
                    notes=data.get("notes"),
                )
            )
        db.flush()
        logger.info("biometric_metrics : %d mesures", len(sections.get("biometric_metrics", [])))

        _reset_sequences(
            db,
            [
                ("users", "id"),
                ("user_auth", "id"),
                ("exercises", "id"),
                ("workout_sessions", "id"),
                ("biometric_metrics", "id"),
            ],
        )
        db.commit()
        logger.info("Seed démo Docker terminé (sans feed — posts à créer en live).")
        return 0
    except Exception:
        db.rollback()
        logger.exception("Échec seed données démo Docker.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
