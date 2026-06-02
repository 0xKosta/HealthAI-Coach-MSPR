# api/routers/users.py
# CRUD complet pour la ressource User
# Préfixe monté dans main.py : /users

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.biometrics import resolve_bmi, validate_user_biometrics
from api.database import get_db
from api.models import User, UserAuth
from api.schemas import UserCreate, UserResponse

router = APIRouter()


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
    description="Retourne le profil d'un utilisateur par son identifiant.",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
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
    summary="Créer un utilisateur",
    description="Crée un nouveau profil utilisateur. L'IMC est recalculé automatiquement côté serveur.",
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name)
    _apply_user_payload(user, payload)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Mettre à jour un utilisateur",
    description="Met à jour tous les champs d'un utilisateur existant.",
)
def update_user(user_id: int, payload: UserCreate, db: Session = Depends(get_db)):
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
    summary="Supprimer un utilisateur",
    description="Supprime un utilisateur et toutes ses données liées (CASCADE).",
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
