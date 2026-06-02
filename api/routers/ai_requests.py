# Lecture de l'historique des requêtes IA (admin + utilisateur sur son profil)

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.ai_request_service import photo_media_url
from api.database import get_db
from api.models import AiRequest, UserAuth
from api.permissions import (
    HISTORY_ACCESS_DENIED_DETAIL,
    get_history_policy,
    history_unlimited,
)
from api.routers.auth import get_current_user
from api.schemas import AiRequestResponse

router = APIRouter()

ADMIN_DEFAULT_LIMIT = 100


def _to_response(row: AiRequest) -> AiRequestResponse:
    data = AiRequestResponse.model_validate(row)
    return data.model_copy(update={"photo_url": photo_media_url(row.photo_path)})


def _set_history_headers(
    response: Response | None,
    *,
    count_in_window: int,
    limit_max: int,
    window_days: int,
    window_since: datetime | None,
    returned: int,
) -> None:
    if response is None:
        return
    response.headers["X-Total-Count"] = str(returned)
    response.headers["X-History-Count"] = str(count_in_window)
    response.headers["X-History-Limit"] = str(limit_max)
    response.headers["X-History-Days"] = str(window_days)
    if window_since is not None:
        response.headers["X-History-Since"] = window_since.isoformat()


@router.get(
    "/",
    response_model=list[AiRequestResponse],
    summary="Historique des requêtes IA",
    description=(
        "Liste chronologique des appels coach IA pour un utilisateur. "
        "Admin : accès complet. Utilisateur : son profil uniquement, fenêtre glissante "
        "(Premium 7 j / 20 entrées, Premium+ 30 j / 50 entrées par type)."
    ),
)
def list_ai_requests(
    user_id: int = Query(..., description="Profil utilisateur (users.id)"),
    request_type: Optional[
        Literal[
            "advice",
            "analyze_photo",
            "workout_plan",
            "biometric_trend",
            "meal_plan",
        ]
    ] = Query(None, description="Filtrer par type de requête"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    response: Response = None,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    if not history_unlimited(current_user.role):
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez consulter que votre propre historique IA.",
            )
        window_days, max_entries = get_history_policy(
            current_user.role, current_user.plan
        )
        if window_days <= 0 or max_entries <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=HISTORY_ACCESS_DENIED_DETAIL,
            )
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        query = db.query(AiRequest).filter(
            AiRequest.user_id == user_id,
            AiRequest.created_at >= since,
        )
        if request_type:
            query = query.filter(AiRequest.request_type == request_type)
        count_in_window = query.count()
        fetch_limit = min(limit, max_entries)
        rows = (
            query.order_by(AiRequest.created_at.desc(), AiRequest.id.desc())
            .offset(skip)
            .limit(fetch_limit)
            .all()
        )
        _set_history_headers(
            response,
            count_in_window=count_in_window,
            limit_max=max_entries,
            window_days=window_days,
            window_since=since,
            returned=len(rows),
        )
        return [_to_response(row) for row in rows]

    # Admin / demo : pas de fenêtre ni quota
    query = db.query(AiRequest).filter(AiRequest.user_id == user_id)
    if request_type:
        query = query.filter(AiRequest.request_type == request_type)
    total = query.count()
    effective_limit = min(limit, ADMIN_DEFAULT_LIMIT)
    rows = (
        query.order_by(AiRequest.created_at.desc(), AiRequest.id.desc())
        .offset(skip)
        .limit(effective_limit)
        .all()
    )
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-History-Count"] = str(total)
        response.headers["X-History-Limit"] = "0"
        response.headers["X-History-Days"] = "0"
    return [_to_response(row) for row in rows]
