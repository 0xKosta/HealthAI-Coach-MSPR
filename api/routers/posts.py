# api/routers/posts.py
# Feed social — publications, likes, commentaires

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Post, PostComment, PostLike, UserAuth
from api.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

MEDIA_DIR = Path("media/posts")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo


class PostResponse(BaseModel):
    id: int
    author_id: int
    first_name: str
    last_name: str
    avatar_url: str | None = None
    content: str | None
    media_url: str | None
    media_type: str | None
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    first_name: str
    last_name: str
    avatar_url: str | None = None
    content: str
    created_at: str

    class Config:
        from_attributes = True


class LikeToggleResponse(BaseModel):
    post_id: int
    liked: bool
    like_count: int


def _post_to_response(post: Post, current_user_id: int, db: Session) -> PostResponse:
    like_count = (
        db.query(func.count(PostLike.id)).filter(PostLike.post_id == post.id).scalar() or 0
    )
    comment_count = (
        db.query(func.count(PostComment.id)).filter(PostComment.post_id == post.id).scalar()
        or 0
    )
    liked_by_me = (
        db.query(PostLike.id)
        .filter(PostLike.post_id == post.id, PostLike.user_id == current_user_id)
        .first()
        is not None
    )
    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        first_name=post.author.first_name,
        last_name=post.author.last_name,
        avatar_url=post.author.avatar_url,
        content=post.content,
        media_url=post.media_url,
        media_type=post.media_type,
        like_count=like_count,
        comment_count=comment_count,
        liked_by_me=liked_by_me,
        created_at=str(post.created_at),
        updated_at=str(post.updated_at) if post.updated_at else None,
    )


def _get_post_or_404(post_id: int, db: Session) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post introuvable.")
    return post


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
        .join(UserAuth, Post.author_id == UserAuth.id)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_post_to_response(p, current_user.id, db) for p in posts]


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une publication (texte + média optionnel)",
)
async def create_post(
    content: str | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    if not content and not media:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Un post doit contenir au moins un texte ou un média.",
        )

    media_url = None
    media_type_str = None

    if media and media.filename:
        if media.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Type non supporté : {media.content_type}. Acceptés : JPEG, PNG, WebP, MP4.",
            )

        raw_bytes = await media.read()
        if len(raw_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Fichier trop volumineux (max 50 Mo).",
            )

        ext = ALLOWED_TYPES[media.content_type]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = MEDIA_DIR / filename
        filepath.write_bytes(raw_bytes)

        media_url = f"/media/posts/{filename}"
        media_type_str = "image" if media.content_type.startswith("image/") else "video"

    post = Post(
        author_id=current_user.id,
        content=content,
        media_url=media_url,
        media_type=media_type_str,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return _post_to_response(post, current_user.id, db)


@router.post(
    "/{post_id}/like",
    response_model=LikeToggleResponse,
    summary="Aimer / retirer son like sur une publication",
)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    post = _get_post_or_404(post_id, db)
    existing = (
        db.query(PostLike)
        .filter(PostLike.post_id == post.id, PostLike.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(PostLike(post_id=post.id, user_id=current_user.id))
        db.commit()
        liked = True

    like_count = (
        db.query(func.count(PostLike.id)).filter(PostLike.post_id == post.id).scalar() or 0
    )
    return LikeToggleResponse(post_id=post.id, liked=liked, like_count=like_count)


@router.get(
    "/{post_id}/comments",
    response_model=list[CommentResponse],
    summary="Commentaires d'une publication",
)
def list_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    _ = current_user
    post = _get_post_or_404(post_id, db)
    comments = (
        db.query(PostComment)
        .join(UserAuth, PostComment.author_id == UserAuth.id)
        .filter(PostComment.post_id == post.id)
        .order_by(PostComment.created_at.asc(), PostComment.id.asc())
        .all()
    )
    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_id=c.author_id,
            first_name=c.author.first_name,
            last_name=c.author.last_name,
            avatar_url=c.author.avatar_url,
            content=c.content,
            created_at=str(c.created_at),
        )
        for c in comments
    ]


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un commentaire",
)
def create_comment(
    post_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    post = _get_post_or_404(post_id, db)
    comment = PostComment(
        post_id=post.id,
        author_id=current_user.id,
        content=body.content.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        content=comment.content,
        created_at=str(comment.created_at),
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
    post = _get_post_or_404(post_id, db)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres publications.",
        )

    if post.media_url:
        filepath = Path(post.media_url.lstrip("/"))
        if filepath.exists():
            filepath.unlink()

    db.delete(post)
    db.commit()
