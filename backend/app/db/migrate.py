from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _ensure_users_name_column(conn) -> None:
    """Add users.name on databases created before this column existed."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if columns and "name" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''"
        )


def apply_schema(conn) -> None:
    """Apply the SQL schema to the given connection."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    _ensure_users_name_column(conn)
    conn.commit()
