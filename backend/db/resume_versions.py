"""SQLite persistence for the resume_versions table."""

import json
import sqlite3

from db.init_db import DB_PATH


def insert_resume_version(resume_id: int, job_id: int, tailored_text: str, diff: list) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO resume_versions (resume_id, job_id, tailored_text, diff_json) VALUES (?, ?, ?, ?)",
            (resume_id, job_id, tailored_text, json.dumps(diff)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_resume_version(version_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """SELECT id, created_at, resume_id, job_id, tailored_text, diff_json
               FROM resume_versions WHERE id = ?""",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {
        "id": row[0],
        "created_at": row[1],
        "resume_id": row[2],
        "job_id": row[3],
        "tailored_text": row[4],
        "diff": json.loads(row[5]) if row[5] else [],
    }


def list_resume_versions() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """SELECT id, created_at, resume_id, job_id, tailored_text, diff_json
               FROM resume_versions ORDER BY id DESC"""
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "resume_id": row[2],
            "job_id": row[3],
            "tailored_text": row[4],
            "diff": json.loads(row[5]) if row[5] else [],
        }
        for row in rows
    ]
