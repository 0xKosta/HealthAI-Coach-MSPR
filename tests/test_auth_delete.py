# tests/test_auth_delete.py — suppression de compte RGPD


def test_admin_delete_user_with_linked_account(client, admin_auth_headers):
    """Admin : user_auth puis users (évite FK RESTRICT sur user_auth → users)."""
    from api.models import User, UserAuth
    from tests.conftest import TestingSessionLocal

    reg = client.post(
        "/auth/register",
        json={
            "email": "todelete.by.admin@healthai-coach.demo",
            "password": "testpass12",
            "first_name": "To",
            "last_name": "Delete",
        },
    )
    assert reg.status_code == 201

    db = TestingSessionLocal()
    account = (
        db.query(UserAuth)
        .filter(UserAuth.email == "todelete.by.admin@healthai-coach.demo")
        .first()
    )
    profile_id = account.user_id
    db.close()

    res = client.delete(f"/users/{profile_id}", headers=admin_auth_headers)
    assert res.status_code == 204

    db = TestingSessionLocal()
    assert db.query(User).filter(User.id == profile_id).first() is None
    assert (
        db.query(UserAuth)
        .filter(UserAuth.email == "todelete.by.admin@healthai-coach.demo")
        .first()
        is None
    )
    db.close()


def test_delete_my_account_with_profile(client):
    """Suppression : user_auth puis profil users (évite user_id NULL).

    Compte dédié (inscription) pour ne pas supprimer le created_user de session
    utilisé par les autres tests.
    """
    from api.models import User, UserAuth
    from tests.conftest import TestingSessionLocal

    email = "delete.self@healthai-coach.demo"
    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "testpass12",
            "first_name": "Self",
            "last_name": "Delete",
        },
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    db = TestingSessionLocal()
    account = db.query(UserAuth).filter(UserAuth.email == email).first()
    profile_id = account.user_id
    db.close()

    res = client.delete("/auth/me", headers=headers)
    assert res.status_code == 204

    db = TestingSessionLocal()
    assert db.query(User).filter(User.id == profile_id).first() is None
    assert db.query(UserAuth).filter(UserAuth.email == email).first() is None
    db.close()
