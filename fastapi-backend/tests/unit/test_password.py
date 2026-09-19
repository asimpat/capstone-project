from app.security.hash_password import (
    hash_password,
    verify_password,
)


def test_password_hash_is_different_from_original():
    password = "Password123"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_correct_password_is_valid():
    password = "Password123"

    hashed_password = hash_password(password)

    assert verify_password(
        password,
        hashed_password
    ) is True


def test_wrong_password_is_invalid():
    password = "Password123"

    hashed_password = hash_password(password)

    assert verify_password(
        "WrongPassword123",
        hashed_password
    ) is False
