# tests/test_ai_requests.py — historique IA (admin)

import uuid

import pytest

from api.ai_request_service import build_advice_record, persist_ai_request
from api.models import User, UserAuth
from api.routers.auth import create_token, hash_password

from tests.conftest import TestingSessionLocal


@pytest.fixture
def history_user_id():
    db = TestingSessionLocal()
    user = User(
        name="Alice Historique",
        age=30,
        gender="female",
        weight_kg=65.0,
        height_cm=170.0,
        goal="weight_loss",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    db.close()
    return uid


@pytest.fixture
def history_admin_headers(history_user_id):
    suffix = uuid.uuid4().hex[:8]
    db = TestingSessionLocal()
    account = UserAuth(
        user_id=history_user_id,
        email=f"admin.hist.{suffix}@test.local",
        password_hash=hash_password("testpass"),
        first_name="Admin",
        last_name="Hist",
        role="admin",
        plan="free",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def history_premium_headers(history_user_id):
    suffix = uuid.uuid4().hex[:8]
    db = TestingSessionLocal()
    account = UserAuth(
        user_id=history_user_id,
        email=f"user.hist.{suffix}@test.local",
        password_hash=hash_password("testpass"),
        first_name="User",
        last_name="Hist",
        role="user",
        plan="premium",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def _seed_advice_row(user_id: int) -> int:
    db = TestingSessionLocal()
    try:
        row = persist_ai_request(
            db,
            **build_advice_record(user_id, "Test", "Conseil de test pour l'historique."),
        )
        return row.id
    finally:
        db.close()


def test_list_ai_requests_requires_auth(client, history_user_id):
    _seed_advice_row(history_user_id)
    response = client.get(f"/ai-requests/?user_id={history_user_id}")
    assert response.status_code == 401


def test_list_ai_requests_forbidden_for_user(
    client, history_user_id, history_premium_headers
):
    _seed_advice_row(history_user_id)
    response = client.get(
        f"/ai-requests/?user_id={history_user_id}",
        headers=history_premium_headers,
    )
    assert response.status_code == 403


def test_list_ai_requests_admin_ok(client, history_user_id, history_admin_headers):
    _seed_advice_row(history_user_id)
    response = client.get(
        f"/ai-requests/?user_id={history_user_id}",
        headers=history_admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    row = data[0]
    assert row["user_id"] == history_user_id
    assert row["request_type"] == "advice"
    assert row["output_json"]["advice"]
    assert response.headers.get("X-Total-Count") is not None


def test_list_ai_requests_filter_type(client, history_user_id, history_admin_headers):
    _seed_advice_row(history_user_id)
    response = client.get(
        f"/ai-requests/?user_id={history_user_id}&request_type=workout_plan",
        headers=history_admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == []
