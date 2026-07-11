from flask import Blueprint, current_app, g, make_response, request

from app.db.connection import get_db
from app.repositories.preferences_repository import get_preferences
from app.services import auth_service
from app.services.auth_service import EmailExistsError
from app.services.rate_limiter import LoginRateLimiter
from app.utils.auth_guard import login_required
from app.utils.response import error_response, success_response
from app.utils.validation import ValidationError, validate_auth_payload

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
login_rate_limiter = None


def init_auth_routes(app):
    """Create the login rate limiter from app config."""
    global login_rate_limiter
    login_rate_limiter = LoginRateLimiter(
        max_attempts=app.config["LOGIN_RATE_MAX_ATTEMPTS"],
        window_seconds=app.config["LOGIN_RATE_WINDOW_SECONDS"],
    )


def _set_session_cookie(response, token: str):
    """Attach the session cookie to a response."""
    response.set_cookie(
        current_app.config["SESSION_COOKIE_NAME"],
        token,
        httponly=current_app.config["SESSION_COOKIE_HTTPONLY"],
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        max_age=current_app.config["SESSION_ABSOLUTE_SECONDS"],
    )
    return response


def _clear_session_cookie(response):
    """Clear the session cookie on a response."""
    response.set_cookie(
        current_app.config["SESSION_COOKIE_NAME"],
        "",
        httponly=current_app.config["SESSION_COOKIE_HTTPONLY"],
        secure=current_app.config["SESSION_COOKIE_SECURE"],
        samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        max_age=0,
    )
    return response


def _auth_response(user: dict, token: str, status_code: int):
    """Build a success response with a session cookie."""
    response = make_response(success_response({"user": user}, status_code))
    return _set_session_cookie(response, token)


@auth_bp.post("/signup")
def signup():
    """Register a new user and start a session."""
    try:
        data = validate_auth_payload(
            request.get_json(silent=True),
            {"email", "password", "name"},
        )
    except ValidationError as exc:
        return error_response("validation_error", exc.message, 400)

    try:
        result = auth_service.signup(
            get_db(),
            data["email"],
            data["password"],
            data["name"],
        )
    except EmailExistsError:
        return error_response("email_exists", "Email is already registered", 409)

    return _auth_response(result["user"], result["token"], 201)


@auth_bp.post("/login")
def login():
    """Log in an existing user and start a session."""
    try:
        data = validate_auth_payload(request.get_json(silent=True), {"email", "password"})
    except ValidationError as exc:
        return error_response("validation_error", exc.message, 400)

    client_ip = request.remote_addr or "unknown"
    if not login_rate_limiter.check_allowed(client_ip, data["email"]):
        return error_response("rate_limited", "Too many login attempts. Try again later.", 429)

    result = auth_service.login(get_db(), data["email"], data["password"])
    if result is None:
        login_rate_limiter.record_failure(client_ip, data["email"])
        return error_response("invalid_credentials", "Invalid email or password", 401)

    login_rate_limiter.reset(client_ip, data["email"])
    return _auth_response(result["user"], result["token"], 200)


@auth_bp.post("/logout")
@login_required
def logout():
    """End the current session and clear the cookie."""
    token = request.cookies.get(current_app.config["SESSION_COOKIE_NAME"])
    auth_service.logout(get_db(), token)

    response = make_response(success_response({"loggedOut": True}))
    return _clear_session_cookie(response)


@auth_bp.get("/me")
@login_required
def me():
    """Return the current user and onboarding status."""
    preferences = get_preferences(get_db(), g.current_user["id"])
    onboarding_completed = bool(
        preferences and preferences.get("onboarding_completed")
    )
    return success_response(
        {
            "user": g.current_user,
            "onboarding_completed": onboarding_completed,
        }
    )
