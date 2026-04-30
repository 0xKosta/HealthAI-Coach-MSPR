# tests/test_routes.py
# Tests d'intégration — FastAPI TestClient + SQLite en mémoire
#
# La base SQLite en mémoire remplace Supabase pendant les tests :
#   - isolation totale (aucune donnée de prod touchée)
#   - pas de fichier .env requis
#   - tables recréées proprement avant chaque session de test
#
# Lancer : pytest tests/

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base, get_db
from api.main import app

# =============================================================================
# Configuration — base SQLite en mémoire
# =============================================================================

SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_URL,
    # check_same_thread=False requis par SQLite en contexte multi-thread (TestClient)
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Remplace get_db() par une session SQLite pour tous les tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Fixtures pytest
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Crée toutes les tables SQLite une fois pour la session de tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(create_tables):
    """Client HTTP de test avec la dépendance BDD substituée."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# =============================================================================
# Tests — /health
# =============================================================================

def test_health_returns_200(client):
    """GET /health doit retourner 200 et confirmer que le service est opérationnel."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "HealthAI Coach API"}


# =============================================================================
# Tests — /users
# =============================================================================

def test_list_users_returns_200(client):
    """GET /users/ doit retourner 200 avec une liste (vide au départ)."""
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_valid_returns_201(client):
    """POST /users/ avec un payload valide doit retourner 201 et l'utilisateur créé."""
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
    data = response.json()
    assert data["name"] == "Alice Martin"
    assert data["age"] == 30
    assert "id" in data
    assert "created_at" in data


def test_create_user_negative_age_returns_422(client):
    """POST /users/ avec age=-5 doit être rejeté par Pydantic (422 Unprocessable Entity)."""
    payload = {
        "name": "Bob Invalide",
        "age": -5,
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 422


def test_get_user_not_found_returns_404(client):
    """GET /users/99999 doit retourner 404 si l'utilisateur n'existe pas."""
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Utilisateur introuvable"
