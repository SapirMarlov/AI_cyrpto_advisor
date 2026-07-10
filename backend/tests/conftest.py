import pytest

from app.db.connection import get_connection
from app.db.migrate import apply_schema


@pytest.fixture
def db_conn():
    conn = get_connection(":memory:")
    apply_schema(conn)
    yield conn
    conn.close()
