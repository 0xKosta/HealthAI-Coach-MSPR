# Feed social — GET / POST / DELETE
# Préfixe monté dans main.py : /posts

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Post, UserAuth
from api.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Dossier de stockage des médias — créé automatiquement si absent
MEDIA_DIR = Path("media/posts")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo


# =============================================================================
# SCHÉMAS
# =============================================================================

class PostResponse(BaseModel):
    id: int
    user_auth_id: int
    first_name: str
    last_name: str
    avatar_url: str | None
    caption: str | None
    media_url: str | None
    media_type: str | None
    created_at: str

    class Config:
        from_attributes = True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/",
    response_model=list[PostResponse],
    summary="Feed — liste des publications (anti-chronologique)",
)
def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    posts = (
        db.query(Post)
        .join(UserAuth, Post.user_auth_id == UserAuth.id)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        PostResponse(
            id=p.id,
            user_auth_id=p.user_auth_id,
            first_name=p.author.first_name,
            last_name=p.author.last_name,
            avatar_url=p.author.avatar_url,
            caption=p.caption,
            media_url=p.media_url,
            media_type=p.media_type,
            created_at=str(p.created_at),
        )
        for p in posts
    ]


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une publication (texte + média optionnel)",
)
async def create_post(
    caption: str | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    if not caption and not media:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Un post doit contenir au moins un texte ou un média.",
        )

    media_url = None
    media_type_str = None

    if media and media.filename:
        # Validation du type MIME
        if media.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Type de fichier non supporté : {media.content_type}. "
                       f"Formats acceptés : JPEG, PNG, WebP, MP4.",
            )

        # Lecture et validation de la taille
        content = await media.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux (max 50 Mo).",
            )

        # Sauvegarde avec nom UUID pour éviter les collisions
        ext = ALLOWED_TYPES[media.content_type]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = MEDIA_DIR / filename
        filepath.write_bytes(content)

        media_url = f"/media/posts/{filename}"
        media_type_str = "image" if media.content_type.startswith("image/") else "video"

    post = Post(
        user_auth_id=current_user.id,
        caption=caption,
        media_url=media_url,
        media_type=media_type_str,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return PostResponse(
        id=post.id,
        user_auth_id=post.user_auth_id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        caption=post.caption,
        media_url=post.media_url,
        media_type=post.media_type,
        created_at=str(post.created_at),
    )


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une publication (auteur uniquement)",
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post introuvable.")

    # Seul l'auteur peut supprimer son post
    if post.user_auth_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres publications.",
        )

    # Supprimer le fichier média si présent
    if post.media_url:
        filepath = Path(post.media_url.lstrip("/"))
        if filepath.exists():
            filepath.unlink()

    db.delete(post)
    db.commit()