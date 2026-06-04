# api/routers/users.py
# CRUD profil santé (table users) — préfixe /users
#
# Deux parcours distincts :
#   • Utilisateur connecté : lit son profil (GET /users/{id} si id = le sien) et le
#     modifie via /auth/me/profile (PUT). Pas d'écriture sur /users/{id}.
#   • Admin : liste, crée, modifie et supprime n'importe quel profil via /users
#     (facilite la gestion back-office).

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.biometrics import resolve_bmi, validate_user_biometrics
from api.database import get_db
from api.models import User, UserAuth
from api.routers.auth import get_current_user, require_admin
from api.schemas import UserCreate, UserResponse

router = APIRouter()


def _ensure_profile_access(current_user: UserAuth, user_id: int) -> None:
    """Lecture d'un profil : admin ou propriétaire du profil lié au compte."""
    if current_user.role == "admin":
        return
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas accéder à ce profil.",
        )


def _to_user_response(user: User, auth: UserAuth | None = None) -> UserResponse:
    response = UserResponse.model_validate(user)
    if auth is None:
        auth = user.auth_account
    if not auth:
        return response
    return response.model_copy(
        update={
            "first_name": auth.first_name,
            "last_name": auth.last_name,
            "email": auth.email,
            "plan": auth.plan,
            "role": auth.role,
        }
    )


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Lister les utilisateurs",
    description="Retourne la liste paginée de tous les utilisateurs enregistrés.",
)
def list_users(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    q: str | None = Query(None, description="Filtre de recherche sur le nom/prénom"),
    plan: Literal["free", "premium", "premium_plus"] | None = Query(
        None, description="Filtre sur l'offre user_auth"
    ),
    sort: Literal["id_asc", "created_desc", "created_asc"] = Query(
        "id_asc", description="Tri par identifiant ou date de création du profil"
    ),
    response: Response = None,
    db: Session = Depends(get_db),
    _admin: UserAuth = Depends(require_admin),
):
    query = db.query(User, UserAuth).outerjoin(UserAuth, UserAuth.user_id == User.id)
    if q:
        search = q.strip()
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    User.name.ilike(like),
                    UserAuth.first_name.ilike(like),
                    UserAuth.last_name.ilike(like),
                )
            )
    if plan:
        query = query.filter(UserAuth.plan == plan)
    total_count = query.count()
    if response is not None:
        response.headers["X-Total-Count"] = str(total_count)
    if sort == "created_desc":
        query = query.order_by(User.created_at.desc(), User.id.desc())
    elif sort == "created_asc":
        query = query.order_by(User.created_at.asc(), User.id.asc())
    else:
        query = query.order_by(User.id)
    rows = query.offset(skip).limit(limit).all()
    return [_to_user_response(user, auth) for user, auth in rows]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Récupérer un utilisateur",
    description=(
        "Admin : tout profil. Utilisateur connecté : uniquement son propre profil "
        "(user_id du token). Pour modifier son profil, utiliser PUT /auth/me/profile."
    ),
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    _ensure_profile_access(current_user, user_id)
    row = (
        db.query(User, UserAuth)
        .outerjoin(UserAuth, UserAuth.user_id == User.id)
        .filter(User.id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    user, auth = row
    return _to_user_response(user, auth)


def _apply_user_payload(user: User, payload: UserCreate) -> None:
    data = payload.model_dump(exclude={"bmi"})
    err = validate_user_biometrics(
        age=data.get("age"),
        weight_kg=data.get("weight_kg"),
        height_cm=data.get("height_cm"),
    )
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    for field, value in data.items():
        setattr(user, field, value)
    user.bmi = resolve_bmi(user.weight_kg, user.height_cm)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un profil santé seul (admin)",
    description=(
        "Réservé aux administrateurs. Préférer POST /auth/admin/users pour un compte "
        "complet (user_auth + profil vide). Cet endpoint crée uniquement la table users."
    ),
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: UserAuth = Depends(require_admin),
):
    user = User(name=payload.name)
    _apply_user_payload(user, payload)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Mettre à jour un utilisateur (admin)",
    description="Réservé aux administrateurs. Les utilisateurs modifient leur profil via PUT /auth/me/profile.",
)
def update_user(
    user_id: int,
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: UserAuth = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    _apply_user_payload(user, payload)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur (admin)",
    description=(
        "Supprime le profil santé users et le compte user_auth lié. "
        "Ordre : user_auth d'abord (posts, likes, commentaires en CASCADE), "
        "puis users — même contrainte RESTRICT que DELETE /auth/me."
    ),
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: UserAuth = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if current_admin.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supprimez votre propre compte via le profil connecté, pas depuis l'admin.",
        )

    account = db.query(UserAuth).filter(UserAuth.user_id == user_id).first()
    try:
        if account:
            db.delete(account)
            db.flush()
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de supprimer ce profil. Réessayez ou contactez le support.",
        )
