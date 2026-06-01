#!/usr/bin/env python3
"""
HealthAI Coach — Seed comptes user_auth (MSPR 3)

Crée un compte auth pour chaque profil users existant (100 premiers par id).
Prénom / nom / email sont dérivés du profil users (name, id) — pas de faux noms.

Usage (depuis la racine du projet, .env configuré) :
    python db/seed_auth.py

Mot de passe démo pour tous les comptes : 1234
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import NamedTuple

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from etl.load import get_engine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEMO_PASSWORD = "1234"
SEED_COUNT = 100
EMAIL_DOMAIN = "healthai-coach.demo"

class UserProfile(NamedTuple):
    id: int
    name: str
    gender: str | None
    goal: str | None
    age: int | None


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _names_from_users_name(name: str) -> tuple[str, str]:
    """
    Reprend le profil users.name tel quel (cohérent avec le dashboard / API users).
    Si le nom contient un espace : prénom + nom de famille.
    """
    name = (name or "").strip() or "Utilisateur"
    parts = name.split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _email_for_user(user_id: int, name: str) -> str:
    """Email stable, lié à l'id users (évite les décalages après ETL)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or f"user-{user_id}"
    return f"{slug}.{user_id}@{EMAIL_DOMAIN}"


def _fetch_users(engine, limit: int) -> list[UserProfile]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, gender, goal, age
                FROM users
                ORDER BY id
                LIMIT :lim
                """
            ),
            {"lim": limit},
        ).fetchall()
    return [
        UserProfile(
            id=r[0],
            name=r[1],
            gender=r[2],
            goal=r[3],
            age=r[4],
        )
        for r in rows
    ]


def seed_auth(limit: int = SEED_COUNT) -> tuple[int, int]:
    """
    Retourne (lignes touchées ce run, total user_auth en base).
    """
    password_hash = _hash_password(DEMO_PASSWORD)
    engine = get_engine()
    users = _fetch_users(engine, limit)

    if not users:
        raise RuntimeError(
            "Aucun utilisateur dans la table users. Lancez d'abord l'ETL "
            "(python -m etl.pipeline)."
        )

    if len(users) < limit:
        logger.warning(
            "Seulement %s users en base (objectif %s).",
            len(users),
            limit,
        )

    touched = 0
    with engine.begin() as conn:
        for u in users:
            first_name, last_name = _names_from_users_name(u.name)
            email = _email_for_user(u.id, u.name)
            result = conn.execute(
                text(
                    """
                    INSERT INTO user_auth (
                        user_id, email, password_hash,
                        first_name, last_name
                    )
                    VALUES (
                        :user_id, :email, :password_hash,
                        :first_name, :last_name
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        email = EXCLUDED.email,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        password_hash = EXCLUDED.password_hash,
                        updated_at = NOW()
                    """
                ),
                {
                    "user_id": u.id,
                    "email": email,
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if result.rowcount:
                touched += 1
            logger.debug(
                "user_id=%s users.name=%r → %s %s <%s>",
                u.id,
                u.name,
                first_name,
                last_name,
                email,
            )

        total = conn.execute(text("SELECT COUNT(*) FROM user_auth")).scalar_one()

    return touched, total


def main() -> None:
    logger.info("Seed user_auth depuis users — mot de passe démo : %s", DEMO_PASSWORD)
    touched, total = seed_auth()
    logger.info(
        "Terminé : %s ligne(s) insérée(s) ou mise(s) à jour, %s compte(s) au total.",
        touched,
        total,
    )
    if total < SEED_COUNT:
        logger.warning(
            "Objectif %s comptes non atteint. Vérifiez le nombre de users ou relancez après ETL.",
            SEED_COUNT,
        )


if __name__ == "__main__":
    main()
