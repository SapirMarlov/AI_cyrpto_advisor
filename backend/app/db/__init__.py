from pathlib import Path

from app.db.connection import get_connection
from app.db.migrate import apply_schema


def init_db(app) -> None:
    database_path = app.config["DATABASE_PATH"]

    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(database_path)
    try:
        apply_schema(conn)
    finally:
        conn.close()
