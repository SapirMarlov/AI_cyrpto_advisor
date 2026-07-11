from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_vercel_json_rewrites_api_to_render():
    raw = (ROOT / "frontend" / "vercel.json").read_text(encoding="utf-8")
    assert '"/api/:path*"' in raw
    assert "onrender.com/api/:path*" in raw


def test_render_yaml_uses_sqlite_persistent_disk():
    raw = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "mountPath: /var/data" in raw
    assert "DATABASE_PATH" in raw
    assert "/var/data/app.db" in raw
    assert "gunicorn" in raw
    assert "--workers 1" in raw
    assert "FLASK_ENV" in raw
    assert "SECRET_KEY" in raw


def test_env_example_documents_database_path():
    raw = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")
    assert "DATABASE_PATH" in raw
    assert "/var/data/app.db" in raw
