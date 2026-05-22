# tests/test_routes.py
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app

# =============================================================================
# Config — SQLite en mémoire
# =============================================================================

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(create_tables):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def created_user(client):
    """Utilisateur créé une fois, réutilisé dans tous les tests qui en ont besoin."""
    payload = {
        "name": "Alice Martin",
        "age": 30,
        "gender": "female",
        "weight_kg": 65.0,
        "height_cm": 170.0,
        "goal": "weight_loss",
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    return response.json()


# =============================================================================
# /health
# =============================================================================

def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "HealthAI Coach API"}


# =============================================================================
# /users
# =============================================================================

def test_list_users_returns_200(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_valid_returns_201(client, created_user):
    assert created_user["name"] == "Alice Martin"
    assert created_user["age"] == 30
    assert "id" in created_user


def test_create_user_negative_age_returns_422(client):
    response = client.post("/users/", json={"name": "Bob", "age": -5})
    assert response.status_code == 422


def test_get_user_not_found_returns_404(client):
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utilisateur introuvable"


def test_get_user_by_id(client, created_user):
    uid = created_user["id"]
    response = client.get(f"/users/{uid}")
    assert response.status_code == 200
    assert response.json()["id"] == uid


# =============================================================================
# /nutrition/foods
# =============================================================================

@pytest.fixture(scope="session")
def created_food(client):
    payload = {
        "name": "Poulet grillé",
        "category": "viandes",
        "calories_per_100g": 165.0,
        "proteins_g": 31.0,
        "carbs_g": 0.0,
        "fats_g": 3.6,
    }
    response = client.post("/nutrition/foods", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


def test_list_foods(client):
    response = client.get("/nutrition/foods")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_food(client, created_food):
    assert created_food["name"] == "Poulet grillé"
    assert "id" in created_food


def test_get_food_not_found(client):
    response = client.get("/nutrition/foods/99999")
    assert response.status_code == 404


# =============================================================================
# /exercises
# =============================================================================

@pytest.fixture(scope="session")
def created_exercise(client):
    payload = {
        "name": "Squat",
        "type": "strength",
        "muscle_group": "quadriceps",
        "equipment": "barbell",
        "level": "intermediate",
    }
    response = client.post("/exercises/", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


def test_list_exercises(client):
    response = client.get("/exercises/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_exercise(client, created_exercise):
    assert created_exercise["name"] == "Squat"
    assert "id" in created_exercise


def test_get_exercise_not_found(client):
    response = client.get("/exercises/99999")
    assert response.status_code == 404


# =============================================================================
# /metrics
# =============================================================================

@pytest.fixture(scope="session")
def created_metric(client, created_user):
    payload = {
        "user_id": created_user["id"],
        "weight_kg": 64.5,
        "sleep_hours": 7.5,
        "resting_bpm": 62.0,
    }
    response = client.post("/metrics/", json=payload)
    assert response.status_code in (200, 201)
    return response.json()


def test_list_metrics(client):
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_metric(client, created_metric):
    assert "id" in created_metric


def test_get_metric_not_found(client):
    response = client.get("/metrics/99999")
    assert response.status_code == 404


# =============================================================================
# /coach — mock OpenAI
# =============================================================================
# On ne fait JAMAIS d'appel réel à OpenAI dans les tests.
# On remplace le client OpenAI par un MagicMock qui retourne
# une réponse prédéfinie. C'est le pattern standard pour tester
# du code qui dépend d'une API externe.

def _mock_openai_response(text: str):
    """Construit un faux objet de réponse OpenAI."""
    mock_choice = MagicMock()
    mock_choice.message.content = text
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_coach_advice_user_not_found(client):
    response = client.post("/coach/advice", json={"user_id": 99999})
    assert response.status_code == 404


def test_coach_advice_success(client, created_user):
    mock_resp = _mock_openai_response("Continuez vos efforts, vous êtes sur la bonne voie !")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/advice", json={"user_id": created_user["id"]})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == created_user["id"]
    assert "advice" in data
    assert len(data["advice"]) > 0


def test_coach_workout_plan_success(client, created_user):
    mock_resp = _mock_openai_response("## Programme semaine\n**Lundi** : Squat 3x10")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/workout-plan", json={
            "user_id": created_user["id"],
            "equipment": "dumbbell",
            "days_per_week": 3,
        })
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert len(data["plan"]) > 0


def test_coach_biometric_trend_no_data(client, created_user):
    # L'utilisateur n'a pas de métriques dans la fenêtre 30j → 404 attendu
    # (les métriques créées dans created_metric ont une date d'aujourd'hui,
    # ce test vérifie le cas sans données)
    response = client.post("/coach/biometric-trend", json={"user_id": 99999})
    assert response.status_code == 404


def test_coach_biometric_trend_success(client, created_user, created_metric):
    mock_resp = _mock_openai_response("Tendance positive sur le poids. Continuez ainsi.")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/biometric-trend", json={"user_id": created_user["id"]})
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data