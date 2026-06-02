# Auth JWT — register / login / me
# Préfixe monté dans main.py : /auth

import logging
import os
from datetime import datetime, timedelta
from typing import Literal

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


def require_admin(current_user: UserAuth = Depends(get_current_user)) -> UserAuth:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return current_user


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


class AdminCreateAccountRequest(BaseModel):
    """Mêmes champs que l'inscription — création par un admin."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    plan: Literal["free", "premium", "premium_plus"] = "free"
    role: Literal["user", "admin", "demo"] = "user"


class AdminUpdateAccountRequest(BaseModel):
    """Mise à jour du compte user_auth lié à un profil santé (users.id)."""

    email: EmailStr | None = None
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    plan: Literal["free", "premium", "premium_plus"] | None = None
    role: Literal["user", "admin", "demo"] | None = None


class AdminCreateAccountResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    user_id: int
    role: str
    plan: str


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

def _create_account_with_empty_profile(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "user",
    plan: str = "free",
) -> UserAuth:
    """Compte user_auth + profil users vide (comme à l'inscription)."""
    existing = db.query(UserAuth).filter(UserAuth.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email.",
        )
    try:
        profile = User(name="")
        db.add(profile)
        db.flush()
        profile.name = f"User_{profile.id:06d}"

        account = UserAuth(
            user_id=profile.id,
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            plan=plan,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    account = _create_account_with_empty_profile(
        db,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    token = create_token(account.id)
    return TokenResponse(access_token=token)


@router.post(
    "/admin/users",
    response_model=AdminCreateAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte utilisateur (admin)",
    description=(
        "Crée un compte user_auth (prénom, nom, email, mot de passe) et un profil "
        "santé users vide, comme à l'inscription. Les données biométriques se "
        "complètent ensuite."
    ),
)
def admin_create_user(
    payload: AdminCreateAccountRequest,
    db: Session = Depends(get_db),
    _admin: UserAuth = Depends(require_admin),
):
    account = _create_account_with_empty_profile(
        db,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        plan=payload.plan,
    )
    return AdminCreateAccountResponse(
        id=account.id,
        email=account.email,
        first_name=account.first_name,
        last_name=account.last_name,
        user_id=account.user_id,
        role=account.role,
        plan=account.plan,
    )


@router.put(
    "/admin/users/{profile_user_id}",
    response_model=AdminCreateAccountResponse,
    summary="Modifier le compte lié à un profil (admin)",
    description=(
        "Met à jour user_auth (email, prénom, nom, plan, rôle) pour le profil "
        "santé identifié par profile_user_id (users.id)."
    ),
)
def admin_update_user_account(
    profile_user_id: int,
    payload: AdminUpdateAccountRequest,
    db: Session = Depends(get_db),
    current_admin: UserAuth = Depends(require_admin),
):
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == profile_user_id).first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte de connexion n'est lié à ce profil.",
        )

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun champ à mettre à jour.",
        )

    if "email" in data and data["email"] != account.email:
        existing = (
            db.query(UserAuth)
            .filter(UserAuth.email == data["email"], UserAuth.id != account.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un compte existe déjà avec cet email.",
            )
        account.email = data["email"]

    if "first_name" in data:
        account.first_name = data["first_name"]
    if "last_name" in data:
        account.last_name = data["last_name"]
    if "plan" in data:
        account.plan = data["plan"]
    if "role" in data:
        if (
            account.id == current_admin.id
            and data["role"] != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous ne pouvez pas retirer votre propre rôle administrateur.",
            )
        account.role = data["role"]

    db.commit()
    db.refresh(account)
    return AdminCreateAccountResponse(
        id=account.id,
        email=account.email,
        first_name=account.first_name,
        last_name=account.last_name,
        user_id=account.user_id,
        role=account.role,
        plan=account.plan,
    )


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
# Parcours « mon profil » : lecture/écriture uniquement sur le profil lié au token.
# Les admins qui gèrent un autre utilisateur passent par PUT /users/{id} (router users).
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