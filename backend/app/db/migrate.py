from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def apply_schema(conn) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
