EXPECTED_QUESTION_IDS = [
    "interested_assets",
    "investor_type",
    "content_preferences",
]


def test_questions_requires_authentication(client):
    response = client.get("/api/onboarding/questions")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_questions_returns_expected_shape(client):
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": "onboard@example.com", "password": "password123"},
    )
    client.set_cookie(
        "session_id",
        _extract_cookie_value(signup_response.headers.get("Set-Cookie")),
    )

    response = client.get("/api/onboarding/questions")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["error"] is None

    questions = payload["data"]["questions"]
    assert len(questions) == 3
    assert [question["id"] for question in questions] == EXPECTED_QUESTION_IDS

    for question in questions:
        assert isinstance(question["prompt"], str) and question["prompt"]
        assert question["type"] in {"single", "multi"}
        assert isinstance(question["options"], list) and question["options"]
        for option in question["options"]:
            assert isinstance(option["id"], str) and option["id"]
            assert isinstance(option["label"], str) and option["label"]


def _extract_cookie_value(set_cookie_header: str) -> str:
    return set_cookie_header.split("session_id=")[1].split(";")[0]
