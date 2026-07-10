EXPECTED_QUESTION_IDS = [
    "interested_assets",
    "investor_type",
    "content_preferences",
]

VALID_ANSWERS = {
    "interested_assets": ["bitcoin", "ethereum"],
    "investor_type": "hodler",
    "content_preferences": ["market_news", "fun"],
}


def test_questions_requires_authentication(client):
    response = client.get("/api/onboarding/questions")
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_questions_returns_expected_shape(client):
    _authenticate(client, "onboard@example.com")

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


def test_answers_requires_authentication(client):
    response = client.post(
        "/api/onboarding/answers",
        json={"answers": VALID_ANSWERS},
    )
    payload = response.get_json()

    assert response.status_code == 401
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unauthorized"


def test_save_answers_happy_path(client):
    _authenticate(client, "save@example.com")

    response = client.post(
        "/api/onboarding/answers",
        json={"answers": VALID_ANSWERS},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["data"]["onboarding_completed"] is True
    assert payload["data"]["preferences"]["onboarding_completed"] is True
    assert payload["data"]["preferences"]["answers"] == VALID_ANSWERS


def test_save_answers_rejects_unexpected_fields(client):
    _authenticate(client, "unexpected@example.com")

    response = client.post(
        "/api/onboarding/answers",
        json={"answers": VALID_ANSWERS, "user_id": 99},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "Unexpected fields" in payload["error"]["message"]


def test_save_answers_rejects_missing_question(client):
    _authenticate(client, "missing@example.com")
    incomplete = {
        "interested_assets": ["bitcoin"],
        "investor_type": "hodler",
    }

    response = client.post(
        "/api/onboarding/answers",
        json={"answers": incomplete},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "content_preferences" in payload["error"]["message"]


def test_save_answers_rejects_invalid_option_id(client):
    _authenticate(client, "invalid-option@example.com")
    invalid = {
        **VALID_ANSWERS,
        "investor_type": "swing_trader",
    }

    response = client.post(
        "/api/onboarding/answers",
        json={"answers": invalid},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "Invalid option" in payload["error"]["message"]


def test_save_answers_rejects_wrong_types(client):
    _authenticate(client, "wrong-type@example.com")

    single_as_list = {
        **VALID_ANSWERS,
        "investor_type": ["hodler"],
    }
    response = client.post(
        "/api/onboarding/answers",
        json={"answers": single_as_list},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "must be a string" in payload["error"]["message"]

    multi_as_string = {
        **VALID_ANSWERS,
        "interested_assets": "bitcoin",
    }
    response = client.post(
        "/api/onboarding/answers",
        json={"answers": multi_as_string},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "validation_error"
    assert "non-empty list" in payload["error"]["message"]


def test_me_reflects_onboarding_completion(client):
    _authenticate(client, "me-flag@example.com")

    before = client.get("/api/auth/me").get_json()
    assert before["data"]["onboarding_completed"] is False

    client.post(
        "/api/onboarding/answers",
        json={"answers": VALID_ANSWERS},
    )

    after = client.get("/api/auth/me").get_json()
    assert after["data"]["onboarding_completed"] is True
    assert after["data"]["user"]["email"] == "me-flag@example.com"


def _authenticate(client, email: str) -> None:
    signup_response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123"},
    )
    client.set_cookie(
        "session_id",
        _extract_cookie_value(signup_response.headers.get("Set-Cookie")),
    )


def _extract_cookie_value(set_cookie_header: str) -> str:
    return set_cookie_header.split("session_id=")[1].split(";")[0]
