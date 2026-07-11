import pytest

from app.repositories.users_repository import (
    DuplicateEmailError,
    create_user,
    get_user_by_email,
    get_user_by_id,
)


def test_create_user_and_get_by_email_and_id(db_conn):
    created = create_user(db_conn, "User@Example.com", "hashed-password", "Test User")

    by_email = get_user_by_email(db_conn, "user@example.com")
    by_id = get_user_by_id(db_conn, created["id"])

    assert created == by_email == by_id
    assert created["email"] == "user@example.com"
    assert created["name"] == "Test User"
    assert created["password_hash"] == "hashed-password"
    assert created["created_at"] is not None


def test_create_user_duplicate_email_raises(db_conn):
    create_user(db_conn, "user@example.com", "hash-one", "Test User")

    with pytest.raises(DuplicateEmailError):
        create_user(db_conn, "USER@example.com", "hash-two", "Test User")


def test_get_user_by_email_unknown_returns_none(db_conn):
    assert get_user_by_email(db_conn, "missing@example.com") is None


def test_get_user_by_id_unknown_returns_none(db_conn):
    assert get_user_by_id(db_conn, 999) is None
