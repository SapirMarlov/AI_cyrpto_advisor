from flask import Flask

from app.config import Config, TestConfig
from app.db import init_db
from app.db.connection import close_db
from app.routes.auth_routes import auth_bp, init_auth_routes
from app.utils.response import success_response


def create_app(config_class=None):
    app = Flask(__name__)

    resolved_config = config_class or Config
    if isinstance(config_class, str) and config_class == "testing":
        resolved_config = TestConfig

    app.config.from_object(resolved_config)
    init_db(app)
    app.teardown_appcontext(close_db)
    app.register_blueprint(auth_bp)
    init_auth_routes(app)

    @app.get("/api/health")
    def health_check():
        return success_response({"status": "healthy"})

    return app
