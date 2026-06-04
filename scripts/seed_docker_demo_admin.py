#!/usr/bin/env python3
"""
Compte administrateur de démonstration — Docker Compose uniquement.

Ne pas exécuter contre Supabase prod. Activé via SEED_DOCKER_DEMO_ADMIN=true sur le service api.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEMO_EMAIL = os.getenv("DEMO_ADMIN_EMAIL", "admin@admin.com")
DEMO_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "admin")
DEMO_FIRST_NAME = os.getenv("DEMO_ADMIN_FIRST_NAME", "admin")
# last_name NOT NULL en BDD — chaîne vide si non renseigné
DEMO_LAST_NAME = os.getenv("DEMO_ADMIN_LAST_NAME", "")
DEMO_ROLE = "admin"
DEMO_PLAN = os.getenv("DEMO_ADMIN_PLAN", "premium_plus")


def main() -> int:
    if os.getenv("SEED_DOCKER_DEMO_ADMIN", "").lower() not in ("1", "true", "yes"):
        return 0

    from api.database import SessionLocal
    from api.models import User, UserAuth
    from api.routers.auth import hash_password

    db = SessionLocal()
    try:
        existing = db.query(UserAuth).filter(UserAuth.email == DEMO_EMAIL).first()
        if existing:
            if existing.role != DEMO_ROLE:
                existing.role = DEMO_ROLE
                db.commit()
                logger.info("Compte démo %s : rôle mis à jour en admin.", DEMO_EMAIL)
            else:
                logger.info("Compte démo admin déjà présent (%s).", DEMO_EMAIL)
            return 0

        profile = User(name="")
        db.add(profile)
        db.flush()
        profile.name = f"User_{profile.id:06d}"

        account = UserAuth(
            user_id=profile.id,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            first_name=DEMO_FIRST_NAME,
            last_name=DEMO_LAST_NAME or "",
            avatar_url=None,
            role=DEMO_ROLE,
            plan=DEMO_PLAN,
        )
        db.add(account)
        db.commit()
        logger.info(
            "Compte admin démo créé : %s (profil users.id=%s, plan=%s).",
            DEMO_EMAIL,
            profile.id,
            DEMO_PLAN,
        )
        return 0
    except Exception:
        db.rollback()
        logger.exception("Échec seed admin Docker.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
