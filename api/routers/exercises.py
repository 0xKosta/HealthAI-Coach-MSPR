# api/routers/exercises.py
# CRUD pour Exercise, WorkoutSession et SessionExercise
# Préfixe monté dans main.py : /exercises

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Exercise, WorkoutSession, SessionExercise
from api.schemas import (
    ExerciseCreate, ExerciseResponse,
    WorkoutSessionCreate, WorkoutSessionResponse,
    SessionExerciseCreate, SessionExerciseResponse,
)

router = APIRouter()


# =============================================================================
# EXERCISES — catalogue des exercices sportifs
# =============================================================================

@router.get(
    "/",
    response_model=list[ExerciseResponse],
    summary="Lister les exercices",
    description="Retourne la liste paginée du catalogue d'exercices (1300+ entrées depuis ExerciseDB).",
)
def list_exercises(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    return db.query(Exercise).offset(skip).limit(limit).all()


@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Récupérer un exercice",
    description="Retourne les détails d'un exercice par son identifiant.",
)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    return exercise


@router.post(
    "/",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un exercice",
    description="Ajoute un nouvel exercice au catalogue.",
)
def create_exercise(payload: ExerciseCreate, db: Session = Depends(get_db)):
    exercise = Exercise(**payload.model_dump())
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.put(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Mettre à jour un exercice",
    description="Met à jour tous les champs d'un exercice existant.",
)
def update_exercise(exercise_id: int, payload: ExerciseCreate, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    for field, value in payload.model_dump().items():
        setattr(exercise, field, value)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un exercice",
    description="Supprime un exercice. Échoue si des session_exercises y font référence (RESTRICT).",
)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    db.delete(exercise)
    db.commit()


# =============================================================================
# WORKOUT SESSIONS — sessions d'entraînement
# =============================================================================

@router.get(
    "/sessions",
    response_model=list[WorkoutSessionResponse],
    summary="Lister les sessions d'entraînement",
    description="Retourne la liste paginée de toutes les sessions d'entraînement.",
)
def list_sessions(
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    return db.query(WorkoutSession).offset(skip).limit(limit).all()


@router.get(
    "/sessions/{session_id}",
    response_model=WorkoutSessionResponse,
    summary="Récupérer une session d'entraînement",
    description="Retourne les détails d'une session d'entraînement par son identifiant.",
)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    return session


@router.post(
    "/sessions",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une session d'entraînement",
    description="Enregistre une nouvelle session d'entraînement pour un utilisateur.",
)
def create_session(payload: WorkoutSessionCreate, db: Session = Depends(get_db)):
    session = WorkoutSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put(
    "/sessions/{session_id}",
    response_model=WorkoutSessionResponse,
    summary="Mettre à jour une session d'entraînement",
    description="Met à jour tous les champs d'une session d'entraînement existante.",
)
def update_session(session_id: int, payload: WorkoutSessionCreate, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    for field, value in payload.model_dump().items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une session d'entraînement",
    description="Supprime une session et tous les exercices associés (CASCADE).",
)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    db.delete(session)
    db.commit()


# =============================================================================
# SESSION EXERCISES — exercices d'une session (table de liaison N-N)
# =============================================================================

@router.get(
    "/sessions/{session_id}/exercises",
    response_model=list[SessionExerciseResponse],
    summary="Lister les exercices d'une session",
    description="Retourne la liste paginée des exercices pratiqués lors d'une session donnée.",
)
def list_session_exercises(
    session_id: int,
    skip: int = Query(0, ge=0, description="Nombre d'entrées à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'entrées à retourner"),
    db: Session = Depends(get_db),
):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    return (
        db.query(SessionExercise)
        .filter(SessionExercise.session_id == session_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post(
    "/sessions/{session_id}/exercises",
    response_model=SessionExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un exercice à une session",
    description="Associe un exercice à une session existante avec ses paramètres (sets, reps, durée).",
)
def add_session_exercise(
    session_id: int,
    payload: SessionExerciseCreate,
    db: Session = Depends(get_db),
):
    session = db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    data = payload.model_dump()
    data["session_id"] = session_id
    entry = SessionExercise(**data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete(
    "/sessions/{session_id}/exercises/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer un exercice d'une session",
    description="Supprime l'association entre un exercice et une session.",
)
def delete_session_exercise(session_id: int, entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(SessionExercise)
        .filter(SessionExercise.id == entry_id, SessionExercise.session_id == session_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrée introuvable")
    db.delete(entry)
    db.commit()
