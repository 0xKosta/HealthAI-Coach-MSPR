# Utilitaires pour les endpoints coach IA :
#   - Cache en mémoire avec TTL
#   - Rate limiter par utilisateur (fenêtre glissante)
#   - Réponses de fallback si OpenAI est indisponible

import hashlib
import json
import time
from collections import defaultdict, deque
from typing import Any, Optional


# =============================================================================
# CACHE EN MÉMOIRE AVEC TTL
# =============================================================================
# TTL = Time To Live : durée pendant laquelle une réponse reste valide.
# Après expiration, le prochain appel recontacte vraiment OpenAI.
#
# Principe : chaque réponse est stockée avec l'heure à laquelle elle a été
# créée. Au moment de la lire, on vérifie si elle n'est pas trop vieille.

class TTLCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Retourne la valeur si elle existe et n'est pas expirée, sinon None."""
        if key not in self._store:
            return None
        value, created_at = self._store[key]
        if time.time() - created_at > self._ttl:
            del self._store[key]  # nettoyage paresseux
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Stocke une valeur avec l'heure actuelle comme timestamp."""
        self._store[key] = (value, time.time())

    @staticmethod
    def make_key(**kwargs) -> str:
        """Génère une clé unique et déterministe depuis des paramètres.
        
        Ex : make_key(user_id=1, equipment="dumbbell") → hash MD5 stable.
        On utilise MD5 ici uniquement pour raccourcir la clé, pas pour la sécurité.
        """
        raw = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()


# Une instance de cache par endpoint — TTL différents selon la fraîcheur attendue
advice_cache  = TTLCache(ttl_seconds=3600)  # conseil : valable 1h
workout_cache = TTLCache(ttl_seconds=3600)  # programme : valable 1h
trend_cache   = TTLCache(ttl_seconds=1800)  # tendances : valable 30min (données plus dynamiques)


# =============================================================================
# RATE LIMITER — fenêtre glissante par utilisateur
# =============================================================================
# Principe de la fenêtre glissante :
#   On garde l'horodatage de chaque appel dans une file (deque).
#   Avant chaque nouvel appel, on supprime les timestamps plus vieux que
#   la fenêtre. Si la file est pleine → refus.
#
# Avantage sur une fenêtre fixe (ex: reset à minuit) : plus juste,
# un utilisateur ne peut jamais faire 2× le quota en changeant de minute.

class RateLimiter:
    def __init__(self, max_calls: int = 10, window_seconds: int = 3600):
        self._max_calls = max_calls
        self._window = window_seconds
        # defaultdict évite de vérifier si la clé existe avant d'ajouter
        self._calls: dict[int, deque] = defaultdict(deque)

    def is_allowed(self, user_id: int) -> bool:
        """Retourne True si l'appel est autorisé, et l'enregistre.
        Retourne False si le quota est atteint (sans enregistrer l'appel).
        """
        now = time.time()
        queue = self._calls[user_id]

        # Purger les appels hors fenêtre
        while queue and now - queue[0] > self._window:
            queue.popleft()

        if len(queue) >= self._max_calls:
            return False

        queue.append(now)
        return True

    def remaining(self, user_id: int) -> int:
        """Nombre d'appels restants pour cet utilisateur dans la fenêtre."""
        now = time.time()
        queue = self._calls[user_id]
        while queue and now - queue[0] > self._window:
            queue.popleft()
        return max(0, self._max_calls - len(queue))


# Instance unique partagée par tous les endpoints coach
coach_limiter = RateLimiter(max_calls=10, window_seconds=3600)


# =============================================================================
# FALLBACK — réponses de secours si OpenAI est indisponible
# =============================================================================
# Plutôt que de renvoyer une erreur 502 froide, on retourne un message
# utile et contextuel selon l'objectif de l'utilisateur.

_FALLBACK_ADVICE: dict[str, str] = {
    "weight_loss": (
        "Le service IA est temporairement indisponible. "
        "En attendant : maintenez un déficit calorique modéré (300–500 kcal/j), "
        "privilégiez les protéines et légumes, et restez actif chaque jour."
    ),
    "muscle_gain": (
        "Le service IA est temporairement indisponible. "
        "En attendant : visez 1,6–2,2 g de protéines par kg de poids corporel, "
        "progressez en charges et accordez-vous 48h de récupération entre les séances musculaires."
    ),
    "sleep_improvement": (
        "Le service IA est temporairement indisponible. "
        "En attendant : couchez-vous à heure fixe, évitez les écrans 1h avant le sommeil "
        "et limitez la caféine après 14h."
    ),
    "maintenance": (
        "Le service IA est temporairement indisponible. "
        "En attendant : continuez à équilibrer alimentation et activité physique, "
        "et variez vos entraînements pour rester motivé."
    ),
}

FALLBACK_WORKOUT = (
    "Le service de génération de programme est temporairement indisponible.\n\n"
    "Programme de remplacement général :\n\n"
    "**Lundi** — Haut du corps : 3×10 pompes · 3×12 tractions · 3×15 dips\n"
    "**Mercredi** — Bas du corps : 3×15 squats · 3×12 fentes · 3×20 mollets\n"
    "**Vendredi** — Full body : 3×10 burpees · 3×12 mountain climbers · 3×15 abdos\n\n"
    "*Repos : 60–90s entre les séries. Hydratez-vous bien.*"
)

FALLBACK_TREND = (
    "L'analyse IA des tendances est temporairement indisponible. "
    "Consultez directement les graphiques pour suivre l'évolution "
    "de votre poids, de votre sommeil et de votre fréquence cardiaque au repos."
)


def get_fallback_advice(goal: Optional[str]) -> str:
    """Retourne le fallback adapté à l'objectif, ou le fallback maintenance par défaut."""
    return _FALLBACK_ADVICE.get(goal or "", _FALLBACK_ADVICE["maintenance"])

# Cache pour meal-plan
meal_cache = TTLCache(ttl_seconds=3600)  # 1h

FALLBACK_MEAL = (
    "Le service de génération de plan repas est temporairement indisponible.\n\n"
    "Plan de remplacement général (environ 1800 kcal/j) :\n\n"
    "**Petit-déjeuner** : flocons d'avoine + fruits + yaourt nature\n"
    "**Déjeuner** : protéine maigre (poulet/poisson) + légumes + féculent complet\n"
    "**Dîner** : soupe de légumes + œufs ou légumineuses + pain complet\n"
    "**Collation** : poignée de fruits secs + fruit frais\n\n"
    "*Adaptez les portions à votre objectif.*"
)


# =============================================================================
# VALIDATION IMAGE (analyze-photo)
# =============================================================================

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 Mo — aligné avec le frontend


def _detect_image_mime(data: bytes) -> str | None:
    """Détecte le type réel via les magic bytes, indépendamment du MIME déclaré."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image_base64(image_base64: str) -> tuple[bytes, str]:
    """
    Décode et valide une image base64.
    Rejette le texte brut, le base64 invalide ou les formats non supportés.
    """
    import base64
    import binascii
    import re

    raw = image_base64.strip()
    if raw.startswith("data:"):
        if "," not in raw:
            raise ValueError("Data URL invalide.")
        raw = raw.split(",", 1)[1]

    if not re.fullmatch(r"[A-Za-z0-9+/=\s]+", raw):
        raise ValueError("Le contenu doit être une image encodée en base64 valide.")

    try:
        data = base64.b64decode(raw, validate=True)
    except binascii.Error as exc:
        raise ValueError("Encodage base64 invalide.") from exc

    if not data:
        raise ValueError("Image vide.")

    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image trop volumineuse (max 10 Mo).")

    mime = _detect_image_mime(data)
    if not mime:
        raise ValueError("Le fichier doit être une image JPEG, PNG, WebP ou GIF.")

    return data, mime
