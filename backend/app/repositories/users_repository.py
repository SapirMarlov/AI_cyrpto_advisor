import sqlite3


class DuplicateEmailError(Exception):
    pass


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "password_hash": row["password_hash"],
        "created_at": row["created_at"],
    }


def create_user(conn: sqlite3.Connection, email: str, password_hash: str) -> dict:
    normalized_email = _normalize_email(email)

    try:
        cursor = conn.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
            """,
            (normalized_email, password_hash),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise DuplicateEmailError(f"Email already exists: {normalized_email}") from exc

    return get_user_by_id(conn, cursor.lastrowid)


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict | None:
    normalized_email = _normalize_email(email)
    row = conn.execute(
        "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
        (normalized_email,),
    ).fetchone()

    if row is None:
        return None

    return _row_to_dict(row)


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    if row is None:
        return None

    return _row_to_dict(row)
