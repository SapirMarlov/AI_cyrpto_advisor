from datetime import datetime, timedelta, timezone

import bcrypt

from app.repositories.sessions_repository import (
    create_session,
    delete_session,
    delete_sessions_for_user,
    get_session,
    touch_session,
)
from app.repositories.users_repository import DuplicateEmailError, create_user, get_user_by_email, get_user_by_id


class EmailExistsError(Exception):
    """Raised when signup uses an email that already exists."""


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _parse_timestamp(value: str) -> datetime:
    """Parse a stored UTC timestamp."""
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _public_user(user: dict) -> dict:
    """Return only public user fields."""
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


def signup(conn, email: str, password: str, name: str) -> dict:
    """Create a user and a new session."""
    try:
        user = create_user(conn, email, hash_password(password), name)
    except DuplicateEmailError as exc:
        raise EmailExistsError(str(exc)) from exc

    session = create_session(conn, user["id"])
    return {"user": _public_user(user), "token": session["id"]}


def login(conn, email: str, password: str) -> dict | None:
    """Log in with email and password, or return None."""
    user = get_user_by_email(conn, email)
    if user is None or not verify_password(password, user["password_hash"]):
        return None

    session = create_session(conn, user["id"])
    return {"user": _public_user(user), "token": session["id"]}


def logout(conn, token: str) -> None:
    """Delete the session for the given token."""
    delete_session(conn, token)


def resolve_session(
    conn,
    token: str,
    idle_seconds: int,
    absolute_seconds: int,
) -> dict | None:
    """Validate a session and return the public user, or None."""
    session = get_session(conn, token)
    if session is None:
        return None

    now = datetime.now(timezone.utc)
    created_at = _parse_timestamp(session["created_at"])
    last_active_at = _parse_timestamp(session["last_active_at"])

    if (now - created_at) > timedelta(seconds=absolute_seconds):
        delete_session(conn, token)
        return None

    if (now - last_active_at) > timedelta(seconds=idle_seconds):
        delete_session(conn, token)
        return None

    touch_session(conn, token)
    user = get_user_by_id(conn, session["user_id"])
    if user is None:
        delete_session(conn, token)
        return None

    return _public_user(user)
