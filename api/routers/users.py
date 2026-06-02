# api/routers/users.py
# CRUD complet pour la ressource User
# Préfixe monté dans main.py : /users

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.biometrics import resolve_bmi, validate_user_biometrics
from api.database import get_db
from api.models import User
from api.schemas import UserCreate, UserResponse

router = APIRouter()


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
    response: Response = None,
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        search = q.strip()
        if search:
            like = f"%{search}%"
            query = query.filter(User.name.ilike(like))
    total_count = query.count()
    if response is not None:
        response.headers["X-Total-Count"] = str(total_count)
    return query.order_by(User.id).offset(skip).limit(limit).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Récupérer un utilisateur",
    description="Retourne le profil d'un utilisateur par son identifiant.",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return user


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
    return user


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
    return user


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
