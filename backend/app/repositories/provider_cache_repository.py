from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_expires_at(value: str) -> datetime:
    # Stored as ISO-8601; accept trailing Z.
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def get_cached(conn: sqlite3.Connection, cache_key: str) -> dict | None:
    """
    Return {"payload": dict, "expired": bool, "expires_at": str} or None if missing.
    Stale (expired) entries are still returned so callers can use them as fallback.
    """
    row = conn.execute(
        """
        SELECT cache_key, payload_json, expires_at, created_at
        FROM provider_cache
        WHERE cache_key = ?
        """,
        (cache_key,),
    ).fetchone()

    if row is None:
        return None

    expires_at = _parse_expires_at(row["expires_at"])
    expired = _utc_now() >= expires_at

    return {
        "payload": json.loads(row["payload_json"]),
        "expired": expired,
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
    }


def set_cached(
    conn: sqlite3.Connection,
    cache_key: str,
    payload: dict,
    ttl_seconds: int,
) -> None:
    expires_at = (_utc_now() + timedelta(seconds=ttl_seconds)).isoformat()
    payload_json = json.dumps(payload)

    conn.execute(
        """
        INSERT INTO provider_cache (cache_key, payload_json, expires_at, created_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(cache_key) DO UPDATE SET
            payload_json = excluded.payload_json,
            expires_at = excluded.expires_at,
            created_at = CURRENT_TIMESTAMP
        """,
        (cache_key, payload_json, expires_at),
    )
    conn.commit()
