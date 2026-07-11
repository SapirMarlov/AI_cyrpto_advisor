def test_vote_requires_authentication(client):
    response = client.post(
        "/api/feedback/vote",
        json={"item_id": "news-1", "item_type": "news", "vote_type": "up"},
    )
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_vote_happy_path(client):
    _authenticate(client, "vote-happy@example.com")

    response = client.post(
        "/api/feedback/vote",
        json={"item_id": "news-1", "item_type": "news", "vote_type": "up"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["error"] is None
    assert payload["data"]["item_id"] == "news-1"
    assert payload["data"]["item_type"] == "news"
    assert payload["data"]["vote_type"] == "up"
    assert payload["data"]["user_id"] is not None
    assert payload["data"]["id"] is not None


def test_vote_rejects_unexpected_user_id_field(client):
    _authenticate(client, "vote-user-id@example.com")

    response = client.post(
        "/api/feedback/vote",
        json={
            "item_id": "news-1",
            "item_type": "news",
            "vote_type": "up",
            "user_id": 99,
        },
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "Unexpected fields" in payload["error"]["message"]


def test_vote_rejects_invalid_item_type(client):
    _authenticate(client, "vote-bad-item@example.com")

    response = client.post(
        "/api/feedback/vote",
        json={"item_id": "x-1", "item_type": "price", "vote_type": "up"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "item_type" in payload["error"]["message"]


def test_vote_rejects_invalid_vote_type(client):
    _authenticate(client, "vote-bad-type@example.com")

    response = client.post(
        "/api/feedback/vote",
        json={"item_id": "news-1", "item_type": "news", "vote_type": "sideways"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "vote_type" in payload["error"]["message"]


def test_vote_rejects_missing_or_empty_item_id(client):
    _authenticate(client, "vote-empty-id@example.com")

    missing = client.post(
        "/api/feedback/vote",
        json={"item_type": "news", "vote_type": "up"},
    )
    missing_payload = missing.get_json()

    assert missing.status_code == 400
    assert missing_payload["error"]["code"] == "validation_error"
    assert "item_id" in missing_payload["error"]["message"]

    empty = client.post(
        "/api/feedback/vote",
        json={"item_id": "  ", "item_type": "news", "vote_type": "up"},
    )
    empty_payload = empty.get_json()

    assert empty.status_code == 400
    assert empty_payload["error"]["code"] == "validation_error"
    assert "item_id" in empty_payload["error"]["message"]


def test_vote_replace_on_repeat(client):
    _authenticate(client, "vote-replace@example.com")

    first = client.post(
        "/api/feedback/vote",
        json={"item_id": "insight-1", "item_type": "insight", "vote_type": "up"},
    )
    first_payload = first.get_json()

    second = client.post(
        "/api/feedback/vote",
        json={"item_id": "insight-1", "item_type": "insight", "vote_type": "down"},
    )
    second_payload = second.get_json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first_payload["data"]["id"] == second_payload["data"]["id"]
    assert second_payload["data"]["vote_type"] == "down"
    assert second_payload["data"]["updated_at"] >= first_payload["data"]["updated_at"]


def _authenticate(client, email: str) -> None:
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123", "name": "Test User"},
    )
    client.set_cookie(
        "session_id",
        _extract_cookie_value(signup_response.headers.get("Set-Cookie")),
    )


def _extract_cookie_value(set_cookie_header: str) -> str:
    return set_cookie_header.split("session_id=")[1].split(";")[0]
