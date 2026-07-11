from app.repositories.sessions_repository import (
    create_session,
    delete_session,
    get_session,
    touch_session,
)
from app.repositories.users_repository import create_user


def test_create_and_get_session(db_conn):
    user = create_user(db_conn, "user@example.com", "hash", "Test User")
    session = create_session(db_conn, user["id"])

    fetched = get_session(db_conn, session["id"])

    assert fetched is not None
    assert fetched["id"] == session["id"]
    assert fetched["user_id"] == user["id"]
    assert fetched["created_at"] is not None
    assert fetched["last_active_at"] is not None


def test_touch_session_updates_last_active_at(db_conn):
    user = create_user(db_conn, "user@example.com", "hash", "Test User")
    session = create_session(db_conn, user["id"])

    db_conn.execute(
        "UPDATE sessions SET last_active_at = '2000-01-01 00:00:00' WHERE id = ?",
        (session["id"],),
    )
    db_conn.commit()

    touch_session(db_conn, session["id"])
    updated = get_session(db_conn, session["id"])

    assert updated["last_active_at"] != "2000-01-01 00:00:00"


def test_delete_session_removes_record(db_conn):
    user = create_user(db_conn, "user@example.com", "hash", "Test User")
    session = create_session(db_conn, user["id"])

    delete_session(db_conn, session["id"])

    assert get_session(db_conn, session["id"]) is None
