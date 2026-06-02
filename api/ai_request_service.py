# Persistance historique IA (table ai_requests) + stockage local des photos repas

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from api.models import AiRequest

MEDIA_ROOT = Path("media")
AI_PHOTOS_DIR = MEDIA_ROOT / "ai-photos"
SUMMARY_MAX_LEN = 500

MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def truncate_summary(text: str | None, max_len: int = SUMMARY_MAX_LEN) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1] + "…"


def photo_media_url(photo_path: str | None) -> str | None:
    if not photo_path:
        return None
    return f"/media/{photo_path.lstrip('/')}"


def save_meal_photo(
    user_id: int,
    request_id: int,
    image_bytes: bytes,
    mime_type: str,
) -> str:
    """Écrit l'image sur disque ; retourne le chemin relatif (sous media/)."""
    ext = MIME_EXTENSIONS.get(mime_type, ".jpg")
    folder = AI_PHOTOS_DIR / str(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{request_id}{ext}"
    full_path = folder / filename
    full_path.write_bytes(image_bytes)
    return f"ai-photos/{user_id}/{filename}"


def persist_ai_request(
    db: Session,
    *,
    user_id: int,
    request_type: str,
    status: str = "success",
    input_summary: str | None = None,
    output_summary: str | None = None,
    input_json: dict[str, Any] | None = None,
    output_json: dict[str, Any] | None = None,
    photo_path: str | None = None,
    from_cache: bool = False,
    error_message: str | None = None,
) -> AiRequest:
    row = AiRequest(
        user_id=user_id,
        request_type=request_type,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        input_json=input_json,
        output_json=output_json,
        photo_path=photo_path,
        from_cache=from_cache,
        error_message=error_message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def attach_meal_photo(
    db: Session,
    row: AiRequest,
    user_id: int,
    image_bytes: bytes,
    mime_type: str,
) -> AiRequest:
    relative = save_meal_photo(user_id, row.id, image_bytes, mime_type)
    row.photo_path = relative
    db.commit()
    db.refresh(row)
    return row


# — Builders résumés / JSON par type —────────────────────────────────────────

def build_advice_record(
    user_id: int,
    user_name: str,
    advice: str,
    *,
    from_cache: bool = False,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "request_type": "advice",
        "input_summary": "Conseil personnalisé (profil + dernière métrique)",
        "output_summary": truncate_summary(advice),
        "input_json": {"source": "dashboard"},
        "output_json": {"user_name": user_name, "advice": advice},
        "from_cache": from_cache,
    }


def build_photo_record(
    user_id: int,
    user_name: str,
    foods_detected: list[str],
    macros: dict[str, Any],
    advice: str,
    mime_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    foods_preview = ", ".join(foods_detected[:5]) if foods_detected else "—"
    cal = macros.get("calories", "—")
    return {
        "user_id": user_id,
        "request_type": "analyze_photo",
        "input_summary": f"Photo repas ({mime_type.split('/')[-1].upper()})",
        "output_summary": truncate_summary(f"{foods_preview} · {cal} kcal"),
        "input_json": {"mime": mime_type, "size_bytes": size_bytes},
        "output_json": {
            "user_name": user_name,
            "foods_detected": foods_detected,
            "macros": macros,
            "advice": advice,
        },
    }


def build_workout_record(
    user_id: int,
    user_name: str,
    equipment: str,
    days_per_week: int,
    plan: str,
    *,
    equipment_label: str | None = None,
    from_cache: bool = False,
) -> dict[str, Any]:
    equip_fr = equipment_label or equipment
    return {
        "user_id": user_id,
        "request_type": "workout_plan",
        "input_summary": f"{equip_fr} · {days_per_week} j/semaine",
        "output_summary": truncate_summary(plan),
        "input_json": {"equipment": equipment, "days_per_week": days_per_week},
        "output_json": {"user_name": user_name, "plan": plan},
        "from_cache": from_cache,
    }


def build_trend_record(
    user_id: int,
    user_name: str,
    analysis: str,
    metrics_count: int,
    *,
    from_cache: bool = False,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "request_type": "biometric_trend",
        "input_summary": "Analyse tendances biométriques (30 jours)",
        "output_summary": truncate_summary(analysis),
        "input_json": {"period_days": 30, "metrics_count": metrics_count},
        "output_json": {"user_name": user_name, "analysis": analysis},
        "from_cache": from_cache,
    }


def build_meal_plan_record(
    user_id: int,
    user_name: str,
    budget_euros: float,
    allergies: list[str],
    plan: str,
    *,
    from_cache: bool = False,
) -> dict[str, Any]:
    allergies_txt = ", ".join(allergies) if allergies else "aucune"
    return {
        "user_id": user_id,
        "request_type": "meal_plan",
        "input_summary": f"Plan repas · {budget_euros:.0f} €/sem. · allergies : {allergies_txt}",
        "output_summary": truncate_summary(plan),
        "input_json": {"budget_euros": budget_euros, "allergies": allergies},
        "output_json": {"user_name": user_name, "plan": plan},
        "from_cache": from_cache,
    }


def macros_to_dict(macros: Any) -> dict[str, Any]:
    if hasattr(macros, "model_dump"):
        return macros.model_dump()
    if isinstance(macros, dict):
        return macros
    return dict(macros)
