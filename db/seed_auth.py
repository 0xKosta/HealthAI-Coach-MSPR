#!/usr/bin/env python3
"""
HealthAI Coach — Seed 100 comptes démo dans user_auth (MSPR 3)

Lie chaque compte à un users.id existant (les 100 premiers par ordre d'id).
Idempotent : réinsérer met à jour le password_hash si le compte existe déjà.

Usage (depuis la racine du projet, .env configuré) :
    python db/seed_auth.py

Mot de passe démo pour tous les comptes : 1234
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

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

FIRST_NAMES = [
    "Jean", "Marie", "Lucas", "Emma", "Hugo", "Léa", "Louis", "Chloé",
    "Gabriel", "Manon", "Arthur", "Camille", "Jules", "Sarah", "Adam",
    "Inès", "Raphaël", "Julie", "Noah", "Clara",
]

LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier",
]

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _demo_email(index: int) -> str:
    return f"demo{index:03d}@{EMAIL_DOMAIN}"


def _avatar_url(index: int) -> str:
    return f"https://api.dicebear.com/7.x/avataaars/svg?seed=demo{index:03d}"


def seed_auth(limit: int = SEED_COUNT) -> tuple[int, int]:
    """
    Retourne (lignes_insérées_ce_run, total_user_auth_en_base).
    """
    password_hash = _hash_password(DEMO_PASSWORD)
    engine = get_engine()

    with engine.connect() as conn:
        users = conn.execute(
            text("SELECT id FROM users ORDER BY id LIMIT :lim"),
            {"lim": limit},
        ).fetchall()

    if not users:
        raise RuntimeError(
            "Aucun utilisateur dans la table users. Lancez d'abord l'ETL "
            "(python -m etl.pipeline)."
        )

    if len(users) < limit:
        logger.warning(
            "Seulement %s users en base (objectif %s). Seed sur les ids disponibles.",
            len(users),
            limit,
        )

    inserted = 0
    with engine.begin() as conn:
        for i, (user_id,) in enumerate(users, start=1):
            first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
            result = conn.execute(
                text(
                    """
                    INSERT INTO user_auth (
                        user_id, email, password_hash,
                        first_name, last_name, avatar_url
                    )
                    VALUES (
                        :user_id, :email, :password_hash,
                        :first_name, :last_name, :avatar_url
                    )
                    ON CONFLICT (user_id) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        updated_at = NOW()
                    """
                ),
                {
                    "user_id": user_id,
                    "email": _demo_email(i),
                    "password_hash": password_hash,
                    "first_name": first,
                    "last_name": last,
                    "avatar_url": _avatar_url(i),
                },
            )
            if result.rowcount:
                inserted += 1

        total = conn.execute(text("SELECT COUNT(*) FROM user_auth")).scalar_one()

    return inserted, total


def main() -> None:
    logger.info("Seed user_auth — mot de passe démo : %s", DEMO_PASSWORD)
    inserted, total = seed_auth()
    logger.info(
        "Terminé : %s nouvelle(s) ligne(s) insérée(s) ce run, %s compte(s) au total dans user_auth.",
        inserted,
        total,
    )
    if total < SEED_COUNT:
        logger.warning(
            "Objectif %s comptes non atteint. Vérifiez le nombre de users ou relancez après ETL.",
            SEED_COUNT,
        )


if __name__ == "__main__":
    main()
