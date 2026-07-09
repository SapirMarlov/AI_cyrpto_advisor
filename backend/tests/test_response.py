from flask import Flask

from app.utils.response import error_response, success_response


def test_success_response_helper_shape():
    app = Flask(__name__)
    with app.app_context():
        response, status_code = success_response({"value": 1}, status_code=201)
        assert status_code == 201
        assert response.get_json() == {"ok": True, "data": {"value": 1}, "error": None}


def test_error_response_helper_shape():
    app = Flask(__name__)
    with app.app_context():
        response, status_code = error_response(
            "INVALID_PAYLOAD",
            "Payload is invalid",
            status_code=422,
        )
        assert status_code == 422
        assert response.get_json() == {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_PAYLOAD", "message": "Payload is invalid"},
        }
