def test_health_includes_cors_headers_for_allowed_origin(client, app):
    origin = app.config["CORS_ORIGINS"][0]
    response = client.get("/api/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == origin
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_preflight_allows_credentialed_requests(client, app):
    origin = app.config["CORS_ORIGINS"][0]
    response = client.options(
        "/api/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("Access-Control-Allow-Origin") == origin
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"
