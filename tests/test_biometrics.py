# tests/test_biometrics.py — validation biométrique utilisateur
import pytest

from api.biometrics import (
    AGE_MAX,
    AGE_MIN,
    compute_bmi,
    validate_age,
    validate_bmi_from_metrics,
    validate_user_biometrics,
)


class TestBiometricsUnit:
    def test_user_response_legacy_age_zero_lists_issues(self):
        from datetime import date

        from api.schemas import UserResponse

        response = UserResponse(
            id=1,
            name="Legacy",
            age=0,
            weight_kg=70.0,
            height_cm=170.0,
            created_at=date(2026, 1, 1),
        )
        assert response.age == 0
        assert len(response.profile_issues) >= 1
        assert "âge" in response.profile_issues[0].lower()

    def test_compute_bmi_standard(self):
        assert compute_bmi(70, 170) == pytest.approx(24.22, abs=0.01)

    def test_validate_age_null_ok(self):
        assert validate_age(None) is None

    def test_validate_age_too_young(self):
        assert validate_age(AGE_MIN - 1) is not None

    def test_validate_age_too_old(self):
        assert validate_age(AGE_MAX + 1) is not None

    def test_validate_age_in_range(self):
        assert validate_age(30) is None

    def test_validate_bmi_extreme(self):
        # 300 kg, 90 cm → IMC très élevé
        assert validate_bmi_from_metrics(300, 90) is not None

    def test_validate_user_biometrics_valid(self):
        assert validate_user_biometrics(age=30, weight_kg=70, height_cm=170) is None


class TestBiometricsApi:
    """Tests API — réutilise la fixture `client` de test_routes."""

    def test_create_user_valid_bmi_computed(self, client, admin_headers):
        payload = {
            "name": "Valid User",
            "age": 25,
            "weight_kg": 70,
            "height_cm": 175,
        }
        res = client.post("/users/", json=payload, headers=admin_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["bmi"] == pytest.approx(22.86, abs=0.01)

    def test_create_user_age_too_young_returns_400(self, client, admin_headers):
        res = client.post(
            "/users/", json={"name": "Young", "age": 17}, headers=admin_headers
        )
        assert res.status_code == 400
        assert "âge" in res.json()["detail"].lower()

    def test_create_user_height_out_of_range_returns_400(self, client, admin_headers):
        res = client.post(
            "/users/",
            json={"name": "Tall", "age": 30, "height_cm": 50, "weight_kg": 70},
            headers=admin_headers,
        )
        assert res.status_code == 400
        assert "taille" in res.json()["detail"].lower()

    def test_create_user_weight_out_of_range_returns_400(self, client, admin_headers):
        res = client.post(
            "/users/",
            json={"name": "Light", "age": 30, "weight_kg": 10, "height_cm": 170},
            headers=admin_headers,
        )
        assert res.status_code == 400
        assert "poids" in res.json()["detail"].lower()

    def test_create_user_bmi_out_of_range_returns_400(self, client, admin_headers):
        res = client.post(
            "/users/",
            json={"name": "Extreme", "age": 30, "weight_kg": 300, "height_cm": 90},
            headers=admin_headers,
        )
        assert res.status_code == 400
        assert "imc" in res.json()["detail"].lower()

    def test_update_user_invalid_age_returns_400(
        self, client, created_user, admin_headers
    ):
        uid = created_user["id"]
        res = client.put(
            f"/users/{uid}",
            json={
                "name": created_user["name"],
                "age": 15,
                "gender": created_user.get("gender"),
                "weight_kg": created_user.get("weight_kg"),
                "height_cm": created_user.get("height_cm"),
                "goal": created_user.get("goal"),
            },
            headers=admin_headers,
        )
        assert res.status_code == 400
