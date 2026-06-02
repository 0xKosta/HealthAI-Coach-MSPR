# Auth JWT — register / login / me
# Préfixe monté dans main.py : /auth

import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt as _bcrypt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import User, UserAuth
from api.permissions import can_use_ai
from api.biometrics import resolve_bmi, validate_user_biometrics
from api.schemas import ProfileUpdateRequest, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# =============================================================================
# CONFIG JWT + CRYPTO
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "changez-moi-en-production")
ALGORITHM = "HS256"
EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "7"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# =============================================================================
# UTILITAIRES
# =============================================================================

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_auth_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_auth_id), "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserAuth:
    """Dépendance FastAPI — extrait et valide le token JWT, retourne l'utilisateur."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserAuth).filter(UserAuth.id == int(user_id_str)).first()
    if user is None:
        raise credentials_exception
    return user


# =============================================================================
# SCHÉMAS
# =============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "alice.martin@demo.com",
                "password": "Demo2026!",
                "first_name": "Alice",
                "last_name": "Martin",
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    user_id: int | None  # Profil santé lié (users.id) — null si compte sans profil
    role: str  # user | admin | demo
    plan: str  # free | premium | premium_plus
    can_use_ai: bool  # dérivé de role + plan


def _me_response(account: UserAuth) -> MeResponse:
    return MeResponse(
        id=account.id,
        email=account.email,
        first_name=account.first_name,
        last_name=account.last_name,
        avatar_url=account.avatar_url,
        user_id=account.user_id,
        role=account.role,
        plan=account.plan,
        can_use_ai=can_use_ai(account.role, account.plan),
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserAuth).filter(UserAuth.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email.",
        )

    # Création couplée, en une seule transaction :
    #   1. un profil santé `users` VIDE (à compléter ensuite par l'utilisateur)
    #   2. le compte `user_auth` lié à ce profil (user_id obligatoire en base)
    try:
        # Nom au même format que les profils existants : User_000974 (id sur 6 chiffres).
        # On insère d'abord pour obtenir l'id auto-généré, puis on fixe le nom.
        profile = User(name="")
        db.add(profile)
        db.flush()  # obtient profile.id sans valider la transaction
        profile.name = f"User_{profile.id:06d}"

        account = UserAuth(
            user_id=profile.id,
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            role="user",
            plan="free",
        )
        db.add(account)
        db.commit()
        db.refresh(account)
    except Exception:
        db.rollback()
        raise

    token = create_token(account.id)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Se connecter — retourne un token JWT",
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm utilise "username" comme champ email (standard OAuth2)
    user = db.query(UserAuth).filter(UserAuth.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(user.id)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Profil de l'utilisateur connecté",
)
def me(current_user: UserAuth = Depends(get_current_user)):
    return _me_response(current_user)
    
# =============================================================================
# SCHÉMAS supplémentaires
# =============================================================================

class UserAuthPublic(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    avatar_url: str | None
    # Données du profil santé lié (peut être null si pas de lien)
    user_id: int | None
    user_goal: str | None
    user_age: int | None


class UpdateMeRequest(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    avatar_url: str | None = None


# =============================================================================
# CRUD user_auth
# =============================================================================

@router.get(
    "/users/",
    response_model=list[UserAuthPublic],
    summary="Liste tous les comptes (avec profil santé lié)",
)
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    users = db.query(UserAuth).offset(skip).limit(limit).all()
    return [
        UserAuthPublic(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            avatar_url=u.avatar_url,
            user_id=u.user_id,
            user_goal=u.user.goal if u.user_id and u.user else None,
            user_age=u.user.age if u.user_id and u.user else None,
        )
        for u in users
    ]


@router.get(
    "/users/{user_auth_id}",
    response_model=UserAuthPublic,
    summary="Récupérer un compte par son ID",
)
def get_user(
    user_auth_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    u = db.query(UserAuth).filter(UserAuth.id == user_auth_id).first()
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte introuvable.",
        )
    return UserAuthPublic(
        id=u.id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        avatar_url=u.avatar_url,
        user_id=u.user_id,
        user_goal=u.user.goal if u.user_id and u.user else None,
        user_age=u.user.age if u.user_id and u.user else None,
    )


@router.put(
    "/me",
    response_model=MeResponse,
    summary="Modifier son propre profil",
)
def update_me(
    payload: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url

    db.commit()
    db.refresh(current_user)

    return _me_response(current_user)


# =============================================================================
# PROFIL SANTÉ DE L'UTILISATEUR CONNECTÉ (table users liée)
# Sécurisé : on ne touche QUE le profil lié au compte du token.
# =============================================================================

def _get_linked_profile(current_user: UserAuth, db: Session) -> User:
    """Retourne le profil users lié au compte connecté, ou lève une 404."""
    if not current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil santé n'est lié à ce compte.",
        )
    profile = db.query(User).filter(User.id == current_user.user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil santé introuvable.",
        )
    return profile


@router.get(
    "/me/profile",
    response_model=UserResponse,
    summary="Récupérer le profil santé de l'utilisateur connecté",
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return _get_linked_profile(current_user, db)


@router.put(
    "/me/profile",
    response_model=UserResponse,
    summary="Mettre à jour son profil santé (IMC recalculé automatiquement)",
)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    profile = _get_linked_profile(current_user, db)

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    err = validate_user_biometrics(
        age=profile.age,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
    )
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    profile.bmi = resolve_bmi(profile.weight_kg, profile.height_cm)

    db.commit()
    db.refresh(profile)
    return profile


# =============================================================================
# SUPPRESSION DE COMPTE (RGPD — droit à l'effacement, art. 17)
# =============================================================================

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer définitivement son compte (RGPD)",
)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    """Suppression totale et définitive du compte de l'utilisateur connecté.

    Conforme au droit à l'effacement (art. 17 RGPD). Supprimer la ligne `users`
    liée déclenche, via les contraintes ON DELETE CASCADE, l'effacement de
    toutes les données associées : compte d'authentification (user_auth),
    profil santé, métriques biométriques, séances d'entraînement (et exercices
    de séance), journaux alimentaires et publications.
    Si aucun profil santé n'est lié, seul le compte user_auth est supprimé.
    """
    try:
        if current_user.user_id:
            profile = db.query(User).filter(User.id == current_user.user_id).first()
            # La suppression du profil parent cascade jusqu'à user_auth.
            db.delete(profile if profile else current_user)
        else:
            db.delete(current_user)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return None