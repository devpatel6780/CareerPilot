"""SQLite persistence for the resumes table."""

import json
import sqlite3

from db.init_db import DB_PATH


def insert_resume(raw_text: str, structured: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO resumes (raw_text, structured_json) VALUES (?, ?)",
            (raw_text, json.dumps(structured)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_resume(resume_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT id, created_at, raw_text, structured_json FROM resumes WHERE id = ?",
            (resume_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {
        "id": row[0],
        "created_at": row[1],
        "raw_text": row[2],
        "structured": json.loads(row[3]) if row[3] else None,
    }
