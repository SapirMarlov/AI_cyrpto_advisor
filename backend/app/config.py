import os
from pathlib import Path


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    TESTING = False
    DEBUG = ENV == "development"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path("backend") / "instance" / "app.db"))


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    DATABASE_PATH = os.getenv("TEST_DATABASE_PATH", ":memory:")
