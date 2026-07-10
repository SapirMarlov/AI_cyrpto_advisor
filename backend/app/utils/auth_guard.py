from functools import wraps

from flask import current_app, g, request

from app.db.connection import get_db
from app.services import auth_service
from app.utils.response import error_response


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = request.cookies.get(current_app.config["SESSION_COOKIE_NAME"])
        if not token:
            return error_response("unauthorized", "Authentication required", 401)

        user = auth_service.resolve_session(
            get_db(),
            token,
            current_app.config["SESSION_IDLE_SECONDS"],
            current_app.config["SESSION_ABSOLUTE_SECONDS"],
        )
        if user is None:
            return error_response("unauthorized", "Authentication required", 401)

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped
