def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_login_required_allows_valid_session(client):
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert signup_response.status_code == 201

    me_response = client.get("/api/auth/me")
    me_payload = me_response.get_json()

    assert me_response.status_code == 200
    assert me_payload["data"]["user"]["email"] == "user@example.com"


def test_login_required_rejects_expired_session(client, app):
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )
    cookie_header = signup_response.headers.get("Set-Cookie")
    token = cookie_header.split("session_id=")[1].split(";")[0]

    with app.app_context():
        from app.db.connection import get_db

        db = get_db()
        db.execute(
            "UPDATE sessions SET last_active_at = '2000-01-01 00:00:00' WHERE id = ?",
            (token,),
        )
        db.commit()

    client.set_cookie("session_id", token)
    response = client.get("/api/auth/me")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["error"]["code"] == "unauthorized"
