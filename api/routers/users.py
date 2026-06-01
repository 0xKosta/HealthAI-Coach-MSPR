# api/routers/users.py
# CRUD complet pour la ressource User
# Préfixe monté dans main.py : /users

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

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


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur",
    description="Crée un nouveau profil utilisateur. Le champ `bmi` peut être pré-calculé par l'ETL.",
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(**payload.model_dump())
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
    for field, value in payload.model_dump().items():
        setattr(user, field, value)
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
