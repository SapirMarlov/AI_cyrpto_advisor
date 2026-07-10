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

    # Provider settings
    PROVIDER_HTTP_TIMEOUT = float(os.getenv("PROVIDER_HTTP_TIMEOUT", "5"))
    PROVIDER_CACHE_TTL = int(os.getenv("PROVIDER_CACHE_TTL", "300"))
    PRICE_PROVIDER = os.getenv("PRICE_PROVIDER", "coingecko")
    NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "cryptopanic")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
    MEME_PROVIDER = os.getenv("MEME_PROVIDER", "reddit_gemini")
    CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    REDDIT_MEME_SUBREDDITS = os.getenv(
        "REDDIT_MEME_SUBREDDITS",
        "cryptocurrencymemes,CryptoMemes,bitcoin",
    )
    REDDIT_USER_AGENT = os.getenv(
        "REDDIT_USER_AGENT",
        "AICryptoAdvisor/0.1 (educational; contact: local-dev)",
    )


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    DATABASE_PATH = os.getenv(
        "TEST_DATABASE_PATH",
        "file:memdb1?mode=memory&cache=shared",
    )
    SESSION_COOKIE_SECURE = False
    PROVIDER_HTTP_TIMEOUT = 2.0
    PROVIDER_CACHE_TTL = 60
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "test-gemini-key")
    CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "test-cryptopanic-key")
