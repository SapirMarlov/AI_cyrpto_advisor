import secrets
import sqlite3


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sessions row to a dict."""
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "created_at": row["created_at"],
        "last_active_at": row["last_active_at"],
    }


def create_session(conn: sqlite3.Connection, user_id: int) -> dict:
    """Create a new session token for the user."""
    token = secrets.token_urlsafe(32)
    conn.execute(
        """
        INSERT INTO sessions (id, user_id)
        VALUES (?, ?)
        """,
        (token, user_id),
    )
    conn.commit()
    return get_session(conn, token)


def get_session(conn: sqlite3.Connection, token: str) -> dict | None:
    """Find a session by token, or return None."""
    row = conn.execute(
        """
        SELECT id, user_id, created_at, last_active_at
        FROM sessions
        WHERE id = ?
        """,
        (token,),
    ).fetchone()

    if row is None:
        return None

    return _row_to_dict(row)


def touch_session(conn: sqlite3.Connection, token: str) -> None:
    """Update the session last-active time."""
    conn.execute(
        """
        UPDATE sessions
        SET last_active_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (token,),
    )
    conn.commit()


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    """Delete one session by token."""
    conn.execute("DELETE FROM sessions WHERE id = ?", (token,))
    conn.commit()


def delete_sessions_for_user(conn: sqlite3.Connection, user_id: int) -> None:
    """Delete all sessions for a user."""
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
