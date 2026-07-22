"""SQLite persistence for the matches table."""

import json
import sqlite3

from db.init_db import DB_PATH


def insert_match(resume_id: int, job_id: int, match_score: float, rationale: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO matches (resume_id, job_id, match_score, rationale_json) VALUES (?, ?, ?, ?)",
            (resume_id, job_id, match_score, json.dumps(rationale)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
