from unittest.mock import patch

from app.providers.base_provider import BaseProvider


class _OkProvider(BaseProvider):
    def __init__(self, section: str, payload: dict):
        self.section = section
        self.name = f"fake_{section}"
        self._payload = payload

    def fetch(self, context: dict) -> dict:
        return self._payload

    def static_fallback(self, context: dict) -> dict:
        return {"fallback": True, "section": self.section}


class _FailProvider(BaseProvider):
    def __init__(self, section: str):
        self.section = section
        self.name = f"fail_{section}"

    def fetch(self, context: dict) -> dict:
        raise RuntimeError(f"{self.section} exploded")

    def static_fallback(self, context: dict) -> dict:
        return {"fallback": True, "section": self.section}


def _authenticate(client, email: str) -> None:
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123"},
    )
    set_cookie = signup_response.headers.get("Set-Cookie")
    client.set_cookie(
        "session_id",
        set_cookie.split("session_id=")[1].split(";")[0],
    )


def test_dashboard_requires_authentication(client):
    response = client.get("/api/dashboard/daily")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_dashboard_mixed_provider_outcomes(client):
    _authenticate(client, "dash@example.com")
    client.post(
        "/api/onboarding/answers",
        json={
            "answers": {
                "interested_assets": ["bitcoin"],
                "investor_type": "hodler",
                "content_preferences": ["fun"],
            }
        },
    )

    fake_registry = {
        "prices": _OkProvider("prices", {"prices": {"bitcoin": {"usd": 1.0}}}),
        "news": _FailProvider("news"),
        "insight": _OkProvider("insight", {"insight_text": "ok", "generated_by": "fake"}),
        "meme": _OkProvider(
            "meme",
            {
                "title": "meme",
                "image_url": "https://example.com/m.jpg",
                "selected_by": "fake",
            },
        ),
    }

    with patch(
        "app.services.dashboard_service.build_registry",
        return_value=fake_registry,
    ):
        response = client.get("/api/dashboard/daily")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["error"] is None

    sections = payload["data"]["sections"]
    assert set(sections.keys()) == {"news", "prices", "insight", "meme"}
    assert "generated_at" in payload["data"]

    assert sections["prices"]["error"] is None
    assert sections["prices"]["data"]["prices"]["bitcoin"]["usd"] == 1.0
    assert sections["insight"]["error"] is None
    assert sections["meme"]["error"] is None

    # One provider failure must not block the response.
    assert sections["news"]["error"]["code"] == "provider_error"
    assert sections["news"]["data"]["fallback"] is True
    assert sections["news"]["data"]["section"] == "news"


def test_dashboard_all_success(client):
    _authenticate(client, "dash-ok@example.com")

    fake_registry = {
        "prices": _OkProvider("prices", {"prices": {"ethereum": {"usd": 2.0}}}),
        "news": _OkProvider("news", {"items": [{"title": "n", "url": "u", "source": "s"}]}),
        "insight": _OkProvider("insight", {"insight_text": "hi", "generated_by": "fake"}),
        "meme": _OkProvider("meme", {"title": "m", "image_url": "i", "selected_by": "fake"}),
    }

    with patch(
        "app.services.dashboard_service.build_registry",
        return_value=fake_registry,
    ):
        response = client.get("/api/dashboard/daily")

    payload = response.get_json()
    assert response.status_code == 200
    for section in payload["data"]["sections"].values():
        assert section["error"] is None
        assert section["stale"] is False
        assert section["data"] is not None
