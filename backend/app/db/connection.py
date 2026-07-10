import sqlite3

from flask import current_app, g


def get_connection(database_path: str) -> sqlite3.Connection:
    if database_path.startswith("file:"):
        conn = sqlite3.connect(database_path, uri=True)
    else:
        conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = get_connection(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()
