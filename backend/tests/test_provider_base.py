from datetime import datetime, timedelta, timezone

from app.config import TestConfig
from app.providers.base_provider import BaseProvider, run_provider
from app.repositories import provider_cache_repository as cache_repo


class FakeSuccessProvider(BaseProvider):
    section = "prices"
    name = "fake_success"

    def fetch(self, context: dict) -> dict:
        return {"coins": {"bitcoin": {"usd": 100.0}}}

    def static_fallback(self, context: dict) -> dict:
        return {"coins": {}}


class FakeFailProvider(BaseProvider):
    section = "prices"
    name = "fake_fail"

    def fetch(self, context: dict) -> dict:
        raise TimeoutError("upstream timeout")

    def static_fallback(self, context: dict) -> dict:
        return {"coins": {"bitcoin": {"usd": None}}, "fallback": True}


def test_run_provider_success_caches_fresh_data(db_conn):
    provider = FakeSuccessProvider()
    context = {"user_id": 1, "cache_suffix": "daily"}

    result = run_provider(provider, context, db_conn, TestConfig)

    assert result["error"] is None
    assert result["stale"] is False
    assert result["data"]["coins"]["bitcoin"]["usd"] == 100.0

    cached = cache_repo.get_cached(db_conn, provider.cache_key(context))
    assert cached is not None
    assert cached["expired"] is False
    assert cached["payload"]["coins"]["bitcoin"]["usd"] == 100.0


def test_run_provider_exception_uses_static_fallback(db_conn):
    provider = FakeFailProvider()
    context = {"user_id": 2}

    result = run_provider(provider, context, db_conn, TestConfig)

    assert result["stale"] is False
    assert result["error"]["code"] == "provider_error"
    assert "timeout" in result["error"]["message"]
    assert result["data"]["fallback"] is True


def test_run_provider_exception_uses_stale_cache(db_conn):
    provider = FakeFailProvider()
    context = {"user_id": 3}
    key = provider.cache_key(context)
    stale_payload = {"coins": {"ethereum": {"usd": 50.0}}, "from_cache": True}

    # Insert an already-expired cache row.
    expires_at = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    db_conn.execute(
        """
        INSERT INTO provider_cache (cache_key, payload_json, expires_at)
        VALUES (?, ?, ?)
        """,
        (key, '{"coins": {"ethereum": {"usd": 50.0}}, "from_cache": true}', expires_at),
    )
    db_conn.commit()

    result = run_provider(provider, context, db_conn, TestConfig)

    assert result["stale"] is True
    assert result["error"]["code"] == "provider_error"
    assert result["data"] == stale_payload


def test_provider_cache_set_and_get_fresh(db_conn):
    cache_repo.set_cached(db_conn, "news:test:1", {"items": [1]}, ttl_seconds=60)
    cached = cache_repo.get_cached(db_conn, "news:test:1")

    assert cached is not None
    assert cached["expired"] is False
    assert cached["payload"] == {"items": [1]}


def test_provider_cache_missing_returns_none(db_conn):
    assert cache_repo.get_cached(db_conn, "missing-key") is None
