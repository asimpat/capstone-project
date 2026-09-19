from types import SimpleNamespace

import pytest

from app.security.tokens import (
    generate_access_token,
    generate_refresh_token,
    verify_access_token,
    verify_refresh_token,
)


@pytest.fixture
def test_user():
    return SimpleNamespace(
        id="test-user-123",
        role="user",
        tier="free",
    )


def test_access_token(test_user):
    token = generate_access_token(test_user)

    payload = verify_access_token(token)

    assert payload["sub"] == test_user.id
    assert payload["role"] == test_user.role
    assert payload["tier"] == test_user.tier
    assert payload["type"] == "access"


def test_refresh_token(test_user):
    token = generate_refresh_token(test_user)

    payload = verify_refresh_token(token)

    assert payload["sub"] == test_user.id
    assert payload["role"] == test_user.role
    assert payload["tier"] == test_user.tier
    assert payload["type"] == "refresh"
