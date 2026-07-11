from app.repositories.preferences_repository import get_preferences, save_preferences
from app.repositories.users_repository import create_user


def _create_user(db_conn, email: str) -> dict:
    return create_user(db_conn, email, "hashed-password", "Test User")


def test_save_preferences_creates_row(db_conn):
    user = _create_user(db_conn, "prefs@example.com")
    answers = {"risk_tolerance": "moderate", "experience": "beginner"}

    saved = save_preferences(db_conn, user["id"], answers, False)

    assert saved["user_id"] == user["id"]
    assert saved["answers"] == answers
    assert saved["onboarding_completed"] is False
    assert saved["updated_at"] is not None


def test_save_preferences_upserts_existing_row(db_conn):
    user = _create_user(db_conn, "upsert@example.com")

    first = save_preferences(
        db_conn,
        user["id"],
        {"risk_tolerance": "low"},
        False,
    )
    second = save_preferences(
        db_conn,
        user["id"],
        {"risk_tolerance": "high", "experience": "advanced"},
        True,
    )

    assert second["user_id"] == user["id"]
    assert second["answers"] == {"risk_tolerance": "high", "experience": "advanced"}
    assert second["onboarding_completed"] is True
    assert second["updated_at"] >= first["updated_at"]


def test_get_preferences_unknown_user_returns_none(db_conn):
    assert get_preferences(db_conn, 999) is None


def test_get_preferences_is_scoped_to_user(db_conn):
    user_a = _create_user(db_conn, "user-a@example.com")
    user_b = _create_user(db_conn, "user-b@example.com")

    save_preferences(db_conn, user_a["id"], {"risk_tolerance": "low"}, True)

    assert get_preferences(db_conn, user_a["id"]) is not None
    assert get_preferences(db_conn, user_b["id"]) is None
