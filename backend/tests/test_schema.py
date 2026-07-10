import sqlite3

import pytest

from app.db.connection import get_connection
from app.db.migrate import apply_schema


EXPECTED_TABLES = {"users", "user_preferences", "feedback_votes", "provider_cache"}


def _get_table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def test_apply_schema_creates_all_tables():
    conn = get_connection(":memory:")
    try:
        apply_schema(conn)
        assert _get_table_names(conn) == EXPECTED_TABLES
    finally:
        conn.close()


def test_apply_schema_is_idempotent():
    conn = get_connection(":memory:")
    try:
        apply_schema(conn)
        first_tables = _get_table_names(conn)

        apply_schema(conn)
        second_tables = _get_table_names(conn)

        assert first_tables == second_tables == EXPECTED_TABLES
    finally:
        conn.close()


def test_users_email_unique_constraint_exists():
    conn = get_connection(":memory:")
    try:
        apply_schema(conn)
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("user@example.com", "hash-one"),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ("user@example.com", "hash-two"),
            )
            conn.commit()
    finally:
        conn.close()


def test_feedback_votes_unique_constraint_exists():
    conn = get_connection(":memory:")
    try:
        apply_schema(conn)
        indexes = conn.execute("PRAGMA index_list(feedback_votes)").fetchall()
        index_names = {row["name"] for row in indexes}

        assert "sqlite_autoindex_feedback_votes_1" in index_names
    finally:
        conn.close()
