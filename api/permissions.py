# Rôles (droits app) et plans (offre commerciale) — user_auth

from typing import Literal

Role = Literal["user", "admin", "demo"]
Plan = Literal["free", "premium", "premium_plus"]

ROLES: frozenset[str] = frozenset({"user", "admin", "demo"})
PLANS: frozenset[str] = frozenset({"free", "premium", "premium_plus"})

AI_PREMIUM_REQUIRED_DETAIL = (
    "Les fonctionnalités IA nécessitent l'offre Premium (9,99 €/mois) ou Premium+."
)


def is_admin_role(role: str) -> bool:
    return role == "admin"


def can_use_ai(role: str, plan: str) -> bool:
    """Accès coach IA : Premium+ ou rôles internes (admin, demo)."""
    if role in ("admin", "demo"):
        return True
    return plan in ("premium", "premium_plus")
