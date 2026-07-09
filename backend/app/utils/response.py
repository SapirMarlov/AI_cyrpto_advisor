from flask import jsonify


def success_response(data, status_code=200):
    return jsonify({"ok": True, "data": data, "error": None}), status_code


def error_response(code, message, status_code=400):
    return (
        jsonify(
            {
                "ok": False,
                "data": None,
                "error": {"code": code, "message": message},
            }
        ),
        status_code,
    )
