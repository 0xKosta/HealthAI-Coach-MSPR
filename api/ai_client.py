# api/ai_client.py
# Client OpenAI centralisé — mode mock pour démo offline (OPENAI_MOCK=true)

import os

from dotenv import load_dotenv

load_dotenv()

MOCK_MODE = os.getenv("OPENAI_MOCK", "").strip().lower() in ("1", "true", "yes")
_api_key = os.getenv("OPENAI_API_KEY", "").strip()

client = None

if MOCK_MODE:
    client = None
elif not _api_key:
    raise ValueError(
        "OPENAI_API_KEY est absente du fichier .env "
        "(ou activez OPENAI_MOCK=true pour la démo hors ligne)."
    )
else:
    from openai import OpenAI

    client = OpenAI(api_key=_api_key)


def should_persist_ai_history() -> bool:
    """Historique IA : enregistrer uniquement les vraies réponses (pas en mode démo offline)."""
    return not MOCK_MODE
