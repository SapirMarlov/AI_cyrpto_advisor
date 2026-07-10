import json
import sqlite3


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "user_id": row["user_id"],
        "answers": json.loads(row["answers_json"]),
        "onboarding_completed": bool(row["onboarding_completed"]),
        "updated_at": row["updated_at"],
    }


def save_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    answers: dict,
    onboarding_completed: bool,
) -> dict:
    answers_json = json.dumps(answers)

    conn.execute(
        """
        INSERT INTO user_preferences (user_id, answers_json, onboarding_completed, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            answers_json = excluded.answers_json,
            onboarding_completed = excluded.onboarding_completed,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, answers_json, int(onboarding_completed)),
    )
    conn.commit()

    return get_preferences(conn, user_id)


def get_preferences(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT user_id, answers_json, onboarding_completed, updated_at
        FROM user_preferences
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    if row is None:
        return None

    return _row_to_dict(row)
