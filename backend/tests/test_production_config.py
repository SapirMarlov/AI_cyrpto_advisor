import pytest

from app import create_app
from app.config import DEFAULT_SECRET_KEY, Config


def test_health_route_with_testing_config():
    app = create_app("testing")
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_production_rejects_default_secret_key(monkeypatch):
    """Production must not boot with the hardcoded default SECRET_KEY."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    monkeypatch.setattr(Config, "ENV", "production")
    monkeypatch.setattr(Config, "DEBUG", False)
    monkeypatch.setattr(Config, "SECRET_KEY", DEFAULT_SECRET_KEY)
    monkeypatch.setattr(Config, "TESTING", False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(Config)


def test_production_accepts_custom_secret_key(monkeypatch, tmp_path):
    """Production boots when SECRET_KEY is overridden."""
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setattr(Config, "ENV", "production")
    monkeypatch.setattr(Config, "DEBUG", False)
    monkeypatch.setattr(Config, "SECRET_KEY", "a-strong-production-secret-key")
    monkeypatch.setattr(Config, "TESTING", False)
    monkeypatch.setattr(Config, "DATABASE_PATH", str(tmp_path / "prod.db"))

    app = create_app(Config)
    assert app.config["SECRET_KEY"] != DEFAULT_SECRET_KEY
    client = app.test_client()
    assert client.get("/api/health").status_code == 200
