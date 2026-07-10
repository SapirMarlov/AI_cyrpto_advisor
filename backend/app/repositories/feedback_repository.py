import sqlite3

VALID_ITEM_TYPES = {"news", "insight", "meme"}
VALID_VOTE_TYPES = {"up", "down"}


class InvalidVoteError(Exception):
    pass


def _validate_vote(item_type: str, vote_type: str) -> None:
    if item_type not in VALID_ITEM_TYPES:
        raise InvalidVoteError(f"Invalid item_type: {item_type}")
    if vote_type not in VALID_VOTE_TYPES:
        raise InvalidVoteError(f"Invalid vote_type: {vote_type}")


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "item_id": row["item_id"],
        "item_type": row["item_type"],
        "vote_type": row["vote_type"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def save_vote(
    conn: sqlite3.Connection,
    user_id: int,
    item_id: str,
    item_type: str,
    vote_type: str,
) -> dict:
    _validate_vote(item_type, vote_type)

    conn.execute(
        """
        INSERT INTO feedback_votes (user_id, item_id, item_type, vote_type, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, item_type, item_id) DO UPDATE SET
            vote_type = excluded.vote_type,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, item_id, item_type, vote_type),
    )
    conn.commit()

    row = conn.execute(
        """
        SELECT id, user_id, item_id, item_type, vote_type, created_at, updated_at
        FROM feedback_votes
        WHERE user_id = ? AND item_type = ? AND item_id = ?
        """,
        (user_id, item_type, item_id),
    ).fetchone()

    return _row_to_dict(row)


def get_votes_for_user(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, user_id, item_id, item_type, vote_type, created_at, updated_at
        FROM feedback_votes
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_id,),
    ).fetchall()

    return [_row_to_dict(row) for row in rows]
