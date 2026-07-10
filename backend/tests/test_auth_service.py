from app.repositories.sessions_repository import create_session, get_session
from app.repositories.users_repository import create_user
from app.services import auth_service
from app.services.auth_service import EmailExistsError


def test_hash_and_verify_password_round_trip():
    password_hash = auth_service.hash_password("secure-password")

    assert password_hash != "secure-password"
    assert auth_service.verify_password("secure-password", password_hash) is True
    assert auth_service.verify_password("wrong-password", password_hash) is False


def test_verify_password_fails_safely_on_malformed_hash():
    assert auth_service.verify_password("secure-password", "not-a-valid-hash") is False


def test_signup_creates_user_and_session(db_conn):
    result = auth_service.signup(db_conn, "user@example.com", "password123")

    assert result["user"]["email"] == "user@example.com"
    assert result["token"]
    assert get_session(db_conn, result["token"]) is not None


def test_signup_duplicate_email_raises(db_conn):
    auth_service.signup(db_conn, "user@example.com", "password123")

    try:
        auth_service.signup(db_conn, "USER@example.com", "password456")
        assert False, "Expected EmailExistsError"
    except EmailExistsError:
        pass


def test_login_returns_user_for_valid_credentials(db_conn):
    auth_service.signup(db_conn, "user@example.com", "password123")

    result = auth_service.login(db_conn, "user@example.com", "password123")

    assert result is not None
    assert result["user"]["email"] == "user@example.com"
    assert result["token"]


def test_login_returns_none_for_invalid_credentials(db_conn):
    auth_service.signup(db_conn, "user@example.com", "password123")

    assert auth_service.login(db_conn, "user@example.com", "wrong-password") is None
    assert auth_service.login(db_conn, "missing@example.com", "password123") is None


def test_logout_deletes_session(db_conn):
    result = auth_service.signup(db_conn, "user@example.com", "password123")

    auth_service.logout(db_conn, result["token"])

    assert get_session(db_conn, result["token"]) is None


def test_resolve_session_returns_user_for_valid_session(db_conn):
    result = auth_service.signup(db_conn, "user@example.com", "password123")

    user = auth_service.resolve_session(db_conn, result["token"], 86400, 604800)

    assert user == {"id": result["user"]["id"], "email": "user@example.com"}


def test_resolve_session_rejects_idle_expired_session(db_conn):
    result = auth_service.signup(db_conn, "user@example.com", "password123")
    db_conn.execute(
        "UPDATE sessions SET last_active_at = '2000-01-01 00:00:00' WHERE id = ?",
        (result["token"],),
    )
    db_conn.commit()

    user = auth_service.resolve_session(db_conn, result["token"], 60, 604800)

    assert user is None
    assert get_session(db_conn, result["token"]) is None


def test_resolve_session_rejects_absolute_expired_session(db_conn):
    result = auth_service.signup(db_conn, "user@example.com", "password123")
    db_conn.execute(
        """
        UPDATE sessions
        SET created_at = '2000-01-01 00:00:00', last_active_at = '2000-01-01 00:00:00'
        WHERE id = ?
        """,
        (result["token"],),
    )
    db_conn.commit()

    user = auth_service.resolve_session(db_conn, result["token"], 86400, 60)

    assert user is None
    assert get_session(db_conn, result["token"]) is None
