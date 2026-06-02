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


# Fenêtre glissante historique IA (jours) + quota max d'entrées par module
HISTORY_WINDOW_DAYS: dict[str, int] = {
    "free": 0,
    "premium": 7,
    "premium_plus": 30,
}
HISTORY_MAX_ENTRIES: dict[str, int] = {
    "free": 0,
    "premium": 20,
    "premium_plus": 50,
}

HISTORY_ACCESS_DENIED_DETAIL = (
    "L'historique IA est réservé aux offres Premium (7 jours) et Premium+ (30 jours)."
)


def history_unlimited(role: str) -> bool:
    return role in ("admin", "demo")


def get_history_policy(role: str, plan: str) -> tuple[int, int]:
    """Retourne (fenêtre en jours glissants, quota max). (0, 0) = pas d'accès."""
    if history_unlimited(role):
        return 0, 0  # signalé côté routeur comme illimité
    return HISTORY_WINDOW_DAYS.get(plan, 0), HISTORY_MAX_ENTRIES.get(plan, 0)
