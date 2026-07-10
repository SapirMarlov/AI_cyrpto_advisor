def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_signup_login_me_and_logout_flow(client):
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )
    signup_payload = signup_response.get_json()
    signup_cookie = signup_response.headers.get("Set-Cookie")

    assert signup_response.status_code == 201
    assert signup_payload["ok"] is True
    assert signup_payload["data"]["user"]["email"] == "user@example.com"
    assert "session_id=" in signup_cookie

    client.delete_cookie("session_id")
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401

    client.set_cookie("session_id", _extract_cookie_value(signup_cookie))
    me_response = client.get("/api/auth/me")
    me_payload = me_response.get_json()

    assert me_response.status_code == 200
    assert me_payload["data"]["user"]["email"] == "user@example.com"

    logout_response = client.post("/api/auth/logout")
    logout_payload = logout_response.get_json()

    assert logout_response.status_code == 200
    assert logout_payload["data"]["loggedOut"] is True

    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401


def test_login_with_valid_credentials(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    payload = login_response.get_json()

    assert login_response.status_code == 200
    assert payload["data"]["user"]["email"] == "user@example.com"
    assert "session_id=" in login_response.headers.get("Set-Cookie")


def test_login_with_invalid_credentials_returns_401(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "invalid_credentials"


def test_signup_duplicate_email_returns_409(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/signup",
        json={"email": "USER@example.com", "password": "password456"},
    )
    payload = response.get_json()

    assert response.status_code == 409
    assert payload["error"]["code"] == "email_exists"


def test_signup_validation_error_for_short_password(client):
    response = client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "short"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"


def test_signup_rejects_unexpected_fields(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "user@example.com",
            "password": "password123",
            "user_id": 99,
        },
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "Unexpected fields" in payload["error"]["message"]


def test_login_rate_limited_after_repeated_failures(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    for _ in range(5):
        client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    payload = response.get_json()

    assert response.status_code == 429
    assert payload["error"]["code"] == "rate_limited"


def _extract_cookie_value(set_cookie_header: str) -> str:
    return set_cookie_header.split("session_id=")[1].split(";")[0]
