from flask import Flask
from flask_cors import CORS

from app.config import Config, TestConfig
from app.db import init_db
from app.db.connection import close_db
from app.routes.auth_routes import auth_bp, init_auth_routes
from app.routes.dashboard_routes import dashboard_bp
from app.routes.feedback_routes import feedback_bp
from app.routes.onboarding_routes import onboarding_bp
from app.utils.response import success_response


def create_app(config_class=None):
    """Build and configure the Flask app."""
    app = Flask(__name__)

    resolved_config = config_class or Config
    if isinstance(config_class, str) and config_class == "testing":
        resolved_config = TestConfig

    app.config.from_object(resolved_config)
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

    return app
