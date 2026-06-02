# tests/test_permissions.py
from api.permissions import can_use_ai, is_admin_role


def test_is_admin_role():
    assert is_admin_role("admin") is True
    assert is_admin_role("user") is False
    assert is_admin_role("demo") is False


def test_can_use_ai_free_user():
    assert can_use_ai("user", "free") is False


def test_can_use_ai_premium():
    assert can_use_ai("user", "premium") is True
    assert can_use_ai("user", "premium_plus") is True


def test_can_use_ai_admin_demo_without_premium():
    assert can_use_ai("admin", "free") is True
    assert can_use_ai("demo", "free") is True
