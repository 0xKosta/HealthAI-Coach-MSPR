# Lecture de l'historique des requêtes IA (back-office admin)

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from api.ai_request_service import photo_media_url
from api.database import get_db
from api.models import AiRequest
from api.routers.auth import require_admin
from api.schemas import AiRequestResponse

router = APIRouter()


def _to_response(row: AiRequest) -> AiRequestResponse:
    data = AiRequestResponse.model_validate(row)
    return data.model_copy(update={"photo_url": photo_media_url(row.photo_path)})


@router.get(
    "/",
    response_model=list[AiRequestResponse],
    summary="Historique des requêtes IA (admin)",
    description=(
        "Liste chronologique des appels coach IA pour un utilisateur. "
        "Tri du plus récent au plus ancien. Réservé aux administrateurs."
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
    _admin=Depends(require_admin),
):
    query = db.query(AiRequest).filter(AiRequest.user_id == user_id)
    if request_type:
        query = query.filter(AiRequest.request_type == request_type)
    total = query.count()
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    rows = (
        query.order_by(AiRequest.created_at.desc(), AiRequest.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_to_response(row) for row in rows]
