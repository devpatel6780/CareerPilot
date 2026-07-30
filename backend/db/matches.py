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


def get_match(match_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """SELECT m.id, m.created_at, m.resume_id, m.job_id, m.match_score, m.rationale_json,
                      j.title, j.company
               FROM matches m JOIN jobs j ON j.id = m.job_id
               WHERE m.id = ?""",
            (match_id,),
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
        "match_score": row[4],
        "rationale": json.loads(row[5]) if row[5] else None,
        "job_title": row[6],
        "job_company": row[7],
    }


def list_matches() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """SELECT m.id, m.created_at, m.resume_id, m.job_id, m.match_score, m.rationale_json,
                      j.title, j.company
               FROM matches m JOIN jobs j ON j.id = m.job_id
               ORDER BY m.id DESC"""
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "resume_id": row[2],
            "job_id": row[3],
            "match_score": row[4],
            "rationale": json.loads(row[5]) if row[5] else None,
            "job_title": row[6],
            "job_company": row[7],
        }
        for row in rows
    ]
