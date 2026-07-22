"""SQLite persistence for the jobs table."""

import json
import sqlite3

from db.init_db import DB_PATH


def insert_job(
    title: str, company: str, location: str, source: str, source_url: str, structured: dict
) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            """INSERT INTO jobs (title, company, location, source, source_url, structured_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, company, location, source, source_url, json.dumps(structured)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_job(job_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """SELECT id, created_at, title, company, location, source, source_url, structured_json
               FROM jobs WHERE id = ?""",
            (job_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {
        "id": row[0],
        "created_at": row[1],
        "title": row[2],
        "company": row[3],
        "location": row[4],
        "source": row[5],
        "source_url": row[6],
        "structured": json.loads(row[7]) if row[7] else None,
    }


def list_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """SELECT id, created_at, title, company, location, source, source_url, structured_json
               FROM jobs ORDER BY id DESC"""
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "title": row[2],
            "company": row[3],
            "location": row[4],
            "source": row[5],
            "source_url": row[6],
            "structured": json.loads(row[7]) if row[7] else None,
        }
        for row in rows
    ]
