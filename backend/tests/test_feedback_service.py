import pytest

from app.repositories.users_repository import create_user
from app.services.feedback_service import InvalidVoteError, save_vote
from app.utils.validation import ValidationError, validate_feedback_vote


def _create_user(db_conn, email: str) -> dict:
    return create_user(db_conn, email, "hashed-password")


def test_save_vote_persists_and_returns_stored_vote(db_conn):
    user = _create_user(db_conn, "service-vote@example.com")

    saved = save_vote(db_conn, user["id"], "news-abc", "news", "up")

    assert saved["user_id"] == user["id"]
    assert saved["item_id"] == "news-abc"
    assert saved["item_type"] == "news"
    assert saved["vote_type"] == "up"
    assert saved["id"] is not None
    assert saved["created_at"] is not None
    assert saved["updated_at"] is not None


def test_save_vote_replaces_existing_vote(db_conn):
    user = _create_user(db_conn, "service-replace@example.com")

    first = save_vote(db_conn, user["id"], "meme-1", "meme", "up")
    second = save_vote(db_conn, user["id"], "meme-1", "meme", "down")

    assert first["id"] == second["id"]
    assert second["vote_type"] == "down"
    assert second["updated_at"] >= first["updated_at"]


def test_save_vote_invalid_item_type_raises(db_conn):
    user = _create_user(db_conn, "service-bad-item@example.com")

    with pytest.raises(InvalidVoteError):
        save_vote(db_conn, user["id"], "x-1", "price", "up")


def test_save_vote_invalid_vote_type_raises(db_conn):
    user = _create_user(db_conn, "service-bad-vote@example.com")

    with pytest.raises(InvalidVoteError):
        save_vote(db_conn, user["id"], "news-1", "news", "sideways")


def test_validate_feedback_vote_happy_path():
    cleaned = validate_feedback_vote(
        {"item_id": "  news-1  ", "item_type": "news", "vote_type": "up"}
    )

    assert cleaned == {
        "item_id": "news-1",
        "item_type": "news",
        "vote_type": "up",
    }


def test_validate_feedback_vote_rejects_unexpected_fields():
    with pytest.raises(ValidationError, match="Unexpected fields"):
        validate_feedback_vote(
            {
                "item_id": "news-1",
                "item_type": "news",
                "vote_type": "up",
                "user_id": 99,
            }
        )


def test_validate_feedback_vote_rejects_empty_item_id():
    with pytest.raises(ValidationError, match="item_id"):
        validate_feedback_vote(
            {"item_id": "   ", "item_type": "news", "vote_type": "up"}
        )


def test_validate_feedback_vote_rejects_invalid_enums():
    with pytest.raises(ValidationError, match="item_type"):
        validate_feedback_vote(
            {"item_id": "x", "item_type": "price", "vote_type": "up"}
        )

    with pytest.raises(ValidationError, match="vote_type"):
        validate_feedback_vote(
            {"item_id": "x", "item_type": "news", "vote_type": "sideways"}
        )
