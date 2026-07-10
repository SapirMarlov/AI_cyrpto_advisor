"""Start Flask for Playwright e2e with env supplied by playwright.config.ts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import create_app  # noqa: E402


def main() -> None:
    """Reset the e2e DB file if needed, then run the API on 127.0.0.1:5000."""
    database_path = os.environ.get("DATABASE_PATH")
    if database_path and not database_path.startswith("file:"):
        db_file = Path(database_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        if db_file.exists():
            db_file.unlink()

    app = create_app()
    app.run(host="127.0.0.1", port=5000, use_reloader=False)


if __name__ == "__main__":
    main()
