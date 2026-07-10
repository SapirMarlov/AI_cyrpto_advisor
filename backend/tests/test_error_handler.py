def test_unknown_route_returns_safe_not_found_envelope(client):
    response = client.get("/api/does-not-exist")
    payload = response.get_json()
    body = response.get_data(as_text=True)

    assert response.status_code == 404
    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_found"
    assert "Traceback" not in body


def test_unhandled_exception_returns_safe_envelope(app, client):
    @app.get("/api/_test_boom")
    def boom():
        raise RuntimeError("secret internals must not leak")

    # TESTING=True re-raises by default; force the errorhandler path.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    response = client.get("/api/_test_boom")
    payload = response.get_json()
    body = response.get_data(as_text=True)

    assert response.status_code == 500
    assert payload["ok"] is False
    assert payload["data"] is None
    assert payload["error"]["code"] == "internal_error"
    assert payload["error"]["message"] == "An unexpected error occurred"
    assert "secret internals" not in body
    assert "Traceback" not in body
    assert "RuntimeError" not in body
