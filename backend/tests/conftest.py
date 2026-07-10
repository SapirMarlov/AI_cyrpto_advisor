import pytest

from app import create_app
from app.db.connection import get_connection
from app.db.migrate import apply_schema


@pytest.fixture
def db_conn():
    conn = get_connection(":memory:")
    apply_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def app(tmp_path):
    from app.db import init_db

    app = create_app("testing")
    app.config["DATABASE_PATH"] = str(tmp_path / "test.db")
    init_db(app)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
