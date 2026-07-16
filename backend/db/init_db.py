"""Creates (or updates) the SQLite schema for the career agent database."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "career_agent.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db(db_path: Path = DB_PATH) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
