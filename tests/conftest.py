# tests/conftest.py — fixtures partagées pour les tests API
import os

os.environ.setdefault("OPENAI_API_KEY", "pytest-dummy-openai-key")
# Avant import api.database : create_engine() exige une URL (pas de .env en CI)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app

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


@pytest.fixture
def premium_auth_headers(created_user):
    """Compte user_auth Premium lié au profil de test + token JWT."""
    from api.models import UserAuth
    from api.routers.auth import create_token, hash_password

    db = TestingSessionLocal()
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == created_user["id"]).first()
    )
    if not account:
        account = UserAuth(
            user_id=created_user["id"],
            email="premium.coach@test.local",
            password_hash=hash_password("testpass"),
            first_name="Premium",
            last_name="Tester",
            role="user",
            plan="premium",
        )
        db.add(account)
    else:
        account.plan = "premium"
        account.role = "user"
    db.commit()
    db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(created_user):
    """Compte admin (IA sans Premium, accès à tout profil)."""
    from api.models import UserAuth
    from api.routers.auth import create_token, hash_password

    db = TestingSessionLocal()
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == created_user["id"]).first()
    )
    if not account:
        account = UserAuth(
            user_id=created_user["id"],
            email="admin.coach@test.local",
            password_hash=hash_password("testpass"),
            first_name="Admin",
            last_name="Coach",
            role="admin",
            plan="free",
        )
        db.add(account)
    else:
        account.role = "admin"
        account.plan = "free"
    db.commit()
    db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def created_user(create_tables):
    """Profil santé de test — créé en base (POST /users/ exige un admin JWT)."""
    from api.models import User
    from api.schemas import UserResponse

    db = TestingSessionLocal()
    user = User(
        name="Alice Martin",
        age=30,
        gender="female",
        weight_kg=65.0,
        height_cm=170.0,
        goal="weight_loss",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    data = UserResponse.model_validate(user).model_dump(mode="json")
    db.close()
    return data


@pytest.fixture
def admin_headers(created_user):
    """JWT admin pour les routes /users/* réservées au back-office."""
    from api.models import UserAuth
    from api.routers.auth import create_token, hash_password

    db = TestingSessionLocal()
    account = (
        db.query(UserAuth).filter(UserAuth.user_id == created_user["id"]).first()
    )
    if not account:
        account = UserAuth(
            user_id=created_user["id"],
            email="admin.tests@healthai-coach.local",
            password_hash=hash_password("testpass"),
            first_name="Admin",
            last_name="Tests",
            role="admin",
            plan="free",
        )
        db.add(account)
    else:
        account.role = "admin"
    db.commit()
    db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}
