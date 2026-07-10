import sqlite3

from app.repositories.feedback_repository import InvalidVoteError, save_vote as repo_save_vote


def save_vote(
    conn: sqlite3.Connection,
    current_user_id: int,
    item_id: str,
    item_type: str,
    vote_type: str,
) -> dict:
    """Persist a feedback vote for the current user."""
    return repo_save_vote(
        conn,
        user_id=current_user_id,
        item_id=item_id,
        item_type=item_type,
        vote_type=vote_type,
    )


__all__ = ["InvalidVoteError", "save_vote"]
