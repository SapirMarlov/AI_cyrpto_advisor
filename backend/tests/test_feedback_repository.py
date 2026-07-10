import sqlite3

import pytest

from app.repositories.feedback_repository import (
    InvalidVoteError,
    get_votes_for_user,
    save_vote,
)
from app.repositories.users_repository import create_user


def _create_user(db_conn, email: str) -> dict:
    return create_user(db_conn, email, "hashed-password")


def test_save_vote_inserts_new_vote(db_conn):
    user = _create_user(db_conn, "vote@example.com")

    saved = save_vote(db_conn, user["id"], "news-123", "news", "up")

    assert saved["user_id"] == user["id"]
    assert saved["item_id"] == "news-123"
    assert saved["item_type"] == "news"
    assert saved["vote_type"] == "up"
    assert saved["created_at"] is not None
    assert saved["updated_at"] is not None


def test_save_vote_replaces_existing_vote(db_conn):
    user = _create_user(db_conn, "replace@example.com")

    first = save_vote(db_conn, user["id"], "insight-1", "insight", "up")
    second = save_vote(db_conn, user["id"], "insight-1", "insight", "down")

    assert first["id"] == second["id"]
    assert second["vote_type"] == "down"
    assert second["updated_at"] >= first["updated_at"]


def test_get_votes_for_user_returns_only_scoped_votes(db_conn):
    user_a = _create_user(db_conn, "votes-a@example.com")
    user_b = _create_user(db_conn, "votes-b@example.com")

    save_vote(db_conn, user_a["id"], "news-1", "news", "up")
    save_vote(db_conn, user_a["id"], "meme-1", "meme", "down")
    save_vote(db_conn, user_b["id"], "news-2", "news", "up")

    votes_a = get_votes_for_user(db_conn, user_a["id"])
    votes_b = get_votes_for_user(db_conn, user_b["id"])

    assert len(votes_a) == 2
    assert {vote["item_id"] for vote in votes_a} == {"news-1", "meme-1"}
    assert len(votes_b) == 1
    assert votes_b[0]["item_id"] == "news-2"


def test_save_vote_invalid_item_type_raises_before_db(db_conn):
    user = _create_user(db_conn, "invalid-item@example.com")

    with pytest.raises(InvalidVoteError):
        save_vote(db_conn, user["id"], "bad-1", "price", "up")


def test_save_vote_invalid_vote_type_raises_before_db(db_conn):
    user = _create_user(db_conn, "invalid-vote@example.com")

    with pytest.raises(InvalidVoteError):
        save_vote(db_conn, user["id"], "news-1", "news", "sideways")


def test_save_vote_invalid_item_type_raises_integrity_error_at_db(db_conn):
    user = _create_user(db_conn, "db-check@example.com")

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO feedback_votes (user_id, item_id, item_type, vote_type)
            VALUES (?, ?, ?, ?)
            """,
            (user["id"], "raw-1", "price", "up"),
        )
        db_conn.commit()
