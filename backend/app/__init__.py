from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.config import DEFAULT_SECRET_KEY, Config, TestConfig
from app.db import init_db
from app.db.connection import close_db
from app.routes.auth_routes import auth_bp, init_auth_routes
from app.routes.dashboard_routes import dashboard_bp
from app.routes.feedback_routes import feedback_bp
from app.routes.onboarding_routes import onboarding_bp
from app.utils.response import error_response, success_response


def create_app(config_class=None):
    """Build and configure the Flask app."""
    app = Flask(__name__)

    resolved_config = config_class or Config
    if isinstance(config_class, str) and config_class == "testing":
        resolved_config = TestConfig

    app.config.from_object(resolved_config)
    if (
        app.config.get("ENV") == "production"
        and not app.config.get("TESTING")
        and app.config.get("SECRET_KEY") == DEFAULT_SECRET_KEY
    ):
        raise RuntimeError(
            "SECRET_KEY must be set to a non-default value when FLASK_ENV=production"
        )
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
    )
    init_db(app)
    app.teardown_appcontext(close_db)
    app.register_blueprint(auth_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(feedback_bp)
    init_auth_routes(app)

    @app.get("/api/health")
    def health_check():
        """Return a simple health status."""
        return success_response({"status": "healthy"})

    @app.errorhandler(404)
    def not_found(_exc):
        """Return a safe envelope for unknown routes."""
        return error_response("not_found", "Resource not found", 404)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        """Return a safe envelope for unhandled errors (no stack traces)."""
        if isinstance(exc, HTTPException):
            status = exc.code or 500
            if status == 404:
                return error_response("not_found", "Resource not found", 404)
            return error_response(
                "http_error",
                exc.description or "Request failed",
                status,
            )
        app.logger.exception("Unhandled exception")
        return error_response(
            "internal_error",
            "An unexpected error occurred",
            500,
        )

    return app
