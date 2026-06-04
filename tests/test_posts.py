# tests/test_posts.py — feed social, likes, commentaires

import io

import pytest


@pytest.fixture(autouse=True)
def isolate_post_upload_dir(tmp_path, monkeypatch):
    """N'écrit pas dans media/posts/ du repo (fichiers hors Git)."""
    upload_dir = tmp_path / "posts"
    upload_dir.mkdir()
    monkeypatch.setattr("api.routers.posts.MEDIA_DIR", upload_dir)


@pytest.fixture
def auth_headers(premium_auth_headers):
    return premium_auth_headers


@pytest.fixture
def second_user_headers(client, created_user):
    from api.models import UserAuth
    from api.routers.auth import create_token, hash_password
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    account = db.query(UserAuth).filter(UserAuth.email == "second.feed@test.local").first()
    if not account:
        account = UserAuth(
            user_id=None,
            email="second.feed@test.local",
            password_hash=hash_password("testpass"),
            first_name="Bob",
            last_name="Feed",
            role="user",
            plan="free",
        )
        db.add(account)
        db.commit()
        db.refresh(account)
    token = create_token(account.id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_feed_requires_auth(client):
    assert client.get("/posts/").status_code == 401


def test_create_and_list_post(client, auth_headers):
    response = client.post(
        "/posts/",
        data={"content": "Premier succès !"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Premier succès !"
    assert body["like_count"] == 0
    assert body["comment_count"] == 0
    assert body["liked_by_me"] is False

    feed = client.get("/posts/", headers=auth_headers)
    assert feed.status_code == 200
    assert len(feed.json()) >= 1
    assert feed.json()[0]["content"] == "Premier succès !"


def test_create_post_without_content_or_media_fails(client, auth_headers):
    response = client.post("/posts/", data={}, headers=auth_headers)
    assert response.status_code == 422


def test_toggle_like(client, auth_headers):
    post = client.post(
        "/posts/",
        data={"content": "Like me"},
        headers=auth_headers,
    ).json()
    post_id = post["id"]

    like = client.post(f"/posts/{post_id}/like", headers=auth_headers)
    assert like.status_code == 200
    assert like.json()["liked"] is True
    assert like.json()["like_count"] == 1

    feed = client.get("/posts/", headers=auth_headers).json()
    row = next(p for p in feed if p["id"] == post_id)
    assert row["liked_by_me"] is True
    assert row["like_count"] == 1

    unlike = client.post(f"/posts/{post_id}/like", headers=auth_headers)
    assert unlike.json()["liked"] is False
    assert unlike.json()["like_count"] == 0


def test_comments_on_post(client, auth_headers, second_user_headers):
    post_id = client.post(
        "/posts/",
        data={"content": "Besoin de motivation"},
        headers=auth_headers,
    ).json()["id"]

    c1 = client.post(
        f"/posts/{post_id}/comments",
        json={"content": "Bravo !"},
        headers=auth_headers,
    )
    assert c1.status_code == 201
    assert c1.json()["content"] == "Bravo !"

    c2 = client.post(
        f"/posts/{post_id}/comments",
        json={"content": "Continue !"},
        headers=second_user_headers,
    )
    assert c2.status_code == 201

    listed = client.get(f"/posts/{post_id}/comments", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2
    assert listed.json()[0]["content"] == "Bravo !"

    feed = client.get("/posts/", headers=auth_headers).json()
    row = next(p for p in feed if p["id"] == post_id)
    assert row["comment_count"] == 2


def test_delete_post_forbidden_for_other_user(client, auth_headers, second_user_headers):
    post_id = client.post(
        "/posts/",
        data={"content": "Mon post"},
        headers=auth_headers,
    ).json()["id"]

    forbidden = client.delete(f"/posts/{post_id}", headers=second_user_headers)
    assert forbidden.status_code == 403

    ok = client.delete(f"/posts/{post_id}", headers=auth_headers)
    assert ok.status_code == 204


def test_create_post_with_image(client, auth_headers):
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = client.post(
        "/posts/",
        data={"content": "Photo repas"},
        files={"media": ("meal.png", io.BytesIO(png), "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["media_url"] is not None
    assert response.json()["media_type"] == "image"
