# tests/test_history_policy.py
from api.permissions import get_history_policy, history_unlimited


def test_history_unlimited_admin():
    assert history_unlimited("admin") is True
    assert history_unlimited("user") is False


def test_get_history_policy_premium():
    days, limit = get_history_policy("user", "premium")
    assert days == 7
    assert limit == 20


def test_get_history_policy_premium_plus():
    days, limit = get_history_policy("user", "premium_plus")
    assert days == 30
    assert limit == 50


def test_get_history_policy_free():
    days, limit = get_history_policy("user", "free")
    assert days == 0
    assert limit == 0
