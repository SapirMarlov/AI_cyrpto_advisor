from app import create_app


def test_create_app():
    app = create_app("testing")
    assert app is not None
    assert app.config["TESTING"] is True


def test_health_route_returns_success_envelope():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/api/health")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload == {"ok": True, "data": {"status": "healthy"}, "error": None}
