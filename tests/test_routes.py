# tests/test_routes.py
import json
import pytest
from unittest.mock import MagicMock, patch

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

def test_list_users_returns_200(client, admin_headers):
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_valid_returns_201(client, created_user):
    assert created_user["name"] == "Alice Martin"
    assert created_user["age"] == 30
    assert "id" in created_user


def test_create_user_invalid_age_returns_400(client, admin_headers):
    response = client.post(
        "/users/", json={"name": "Bob", "age": 17}, headers=admin_headers
    )
    assert response.status_code == 400
    assert "âge" in response.json()["detail"].lower()


def test_get_user_not_found_returns_404(client, admin_headers):
    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Utilisateur introuvable"


def test_get_user_by_id(client, created_user, admin_headers):
    uid = created_user["id"]
    response = client.get(f"/users/{uid}", headers=admin_headers)
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


def test_coach_advice_requires_auth(client, created_user):
    response = client.post("/coach/advice", json={"user_id": created_user["id"]})
    assert response.status_code == 401


def test_coach_advice_free_plan_forbidden(client, created_user):
    from tests.conftest import TestingSessionLocal
    from api.models import UserAuth
    from api.routers.auth import create_token, hash_password

    db = TestingSessionLocal()
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == created_user["id"]).first()
    )
    if not account:
        account = UserAuth(
            user_id=created_user["id"],
            email="free.coach@test.local",
            password_hash=hash_password("testpass"),
            first_name="Free",
            last_name="User",
            role="user",
            plan="free",
        )
        db.add(account)
    else:
        account.plan = "free"
        account.role = "user"
    db.commit()
    db.refresh(account)
    headers = {"Authorization": f"Bearer {create_token(account.id)}"}
    db.close()

    response = client.post(
        "/coach/advice",
        json={"user_id": created_user["id"]},
        headers=headers,
    )
    assert response.status_code == 403
    assert "premium" in response.json()["detail"].lower()


def test_coach_advice_user_not_found(client, admin_auth_headers):
    response = client.post(
        "/coach/advice",
        json={"user_id": 99999},
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_coach_advice_success(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response("Continuez vos efforts, vous êtes sur la bonne voie !")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post(
            "/coach/advice",
            json={"user_id": created_user["id"]},
            headers=premium_auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == created_user["id"]
    assert "advice" in data
    assert len(data["advice"]) > 0


def test_coach_advice_uses_auth_first_name(client, created_user):
    """Le prompt IA doit utiliser le prénom user_auth, pas User_XXXXXX."""
    from tests.conftest import TestingSessionLocal
    from api.models import User, UserAuth
    from api.routers.auth import create_token, hash_password

    db = TestingSessionLocal()
    profile = db.query(User).filter(User.id == created_user["id"]).first()
    profile.name = "User_000099"
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == profile.id).first()
    )
    if not account:
        account = UserAuth(
            user_id=profile.id,
            email="alice.coach@test.local",
            password_hash=hash_password("testpass"),
            first_name="Alice",
            last_name="Martin",
            role="user",
            plan="premium",
        )
        db.add(account)
    else:
        account.first_name = "Alice"
        account.plan = "premium"
        account.role = "user"
    db.commit()
    db.refresh(account)
    headers = {"Authorization": f"Bearer {create_token(account.id)}"}
    db.close()

    from api.routers import coach as coach_module
    coach_module.advice_cache._store.clear()

    mock_resp = _mock_openai_response("Bonjour Alice !")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post(
            "/coach/advice",
            json={"user_id": created_user["id"]},
            headers=headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["user_name"] == "Alice"
    prompt = mock_client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
    assert "Alice" in prompt
    assert "User_000099" not in prompt
    assert "tutoyant" in prompt.lower() or "tu " in prompt.lower()


def test_coach_workout_plan_success(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response("## Programme semaine\n**Lundi** : Squat 3x10")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/workout-plan", json={
            "user_id": created_user["id"],
            "equipment": "dumbbell",
            "days_per_week": 3,
        }, headers=premium_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert len(data["plan"]) > 0


def test_coach_biometric_trend_no_data(client, admin_auth_headers):
    response = client.post(
        "/coach/biometric-trend",
        json={"user_id": 99999},
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_coach_biometric_trend_success(client, created_user, created_metric, premium_auth_headers):
    mock_resp = _mock_openai_response("Tendance positive sur le poids. Continuez ainsi.")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post(
            "/coach/biometric-trend",
            json={"user_id": created_user["id"]},
            headers=premium_auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data

def test_coach_meal_plan_success(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response(
        "## Plan repas semaine\n**Lundi** : Petit-déj : flocons d'avoine..."
    )
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/meal-plan", json={
            "user_id": created_user["id"],
            "budget_euros": 50.0,
            "allergies": ["gluten"],
        }, headers=premium_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert len(data["plan"]) > 0


def test_coach_meal_plan_user_not_found(client, admin_auth_headers):
    response = client.post("/coach/meal-plan", json={
        "user_id": 99999,
        "budget_euros": 50.0,
        "allergies": [],
    }, headers=admin_auth_headers)
    assert response.status_code == 404


# PNG 1x1 valide (base64)
VALID_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_coach_analyze_photo_rejects_text_base64(client, created_user, premium_auth_headers):
    import base64

    text_b64 = base64.b64encode(b"ceci nest pas une image").decode()
    response = client.post("/coach/analyze-photo", json={
        "user_id": created_user["id"],
        "image_base64": text_b64,
    }, headers=premium_auth_headers)
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_coach_analyze_photo_not_a_meal(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response(json.dumps({
        "is_meal": False,
        "foods_detected": [],
        "macros": {"calories": 0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0},
        "advice": "",
    }))
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/analyze-photo", json={
            "user_id": created_user["id"],
            "image_base64": VALID_PNG_B64,
        }, headers=premium_auth_headers)
    assert response.status_code == 422
    assert "repas" in response.json()["detail"].lower()


def test_coach_analyze_photo_gpt_refusal(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response("Je ne peux pas t'aider avec ça.")
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/analyze-photo", json={
            "user_id": created_user["id"],
            "image_base64": VALID_PNG_B64,
        }, headers=premium_auth_headers)
    assert response.status_code == 422
    assert "repas" in response.json()["detail"].lower()


def test_coach_analyze_photo_success(client, created_user, premium_auth_headers):
    mock_resp = _mock_openai_response(json.dumps({
        "is_meal": True,
        "foods_detected": ["salade"],
        "macros": {"calories": 120, "protein_g": 5.0, "carbs_g": 10.0, "fat_g": 7.0},
        "advice": "Repas équilibré.",
    }))
    with patch("api.routers.coach.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_resp
        response = client.post("/coach/analyze-photo", json={
            "user_id": created_user["id"],
            "image_base64": VALID_PNG_B64,
        }, headers=premium_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["foods_detected"] == ["salade"]
    assert data["macros"]["calories"] == 120


def test_coach_analyze_photo_offline_fallback(client, created_user, premium_auth_headers):
    from api.models import AiRequest

    with patch("api.ai_client.MOCK_MODE", True):
        with patch("api.routers.coach.client", None):
            response = client.post("/coach/analyze-photo", json={
                "user_id": created_user["id"],
                "image_base64": VALID_PNG_B64,
            }, headers=premium_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["foods_detected"] == []
    assert "indisponible" in data["advice"].lower()

    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        count = db.query(AiRequest).filter(
            AiRequest.user_id == created_user["id"],
            AiRequest.request_type == "analyze_photo",
        ).count()
        assert count == 0
    finally:
        db.close()
