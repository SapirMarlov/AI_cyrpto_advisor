import os
from pathlib import Path


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    TESTING = False
    DEBUG = ENV == "development"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path("backend") / "instance" / "app.db"))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    SESSION_COOKIE_NAME = "session_id"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV == "production"
    SESSION_IDLE_SECONDS = 86400
    SESSION_ABSOLUTE_SECONDS = 604800
    LOGIN_RATE_MAX_ATTEMPTS = 5
    LOGIN_RATE_WINDOW_SECONDS = 900


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    DATABASE_PATH = os.getenv(
        "TEST_DATABASE_PATH",
        "file:memdb1?mode=memory&cache=shared",
    )
    SESSION_COOKIE_SECURE = False
