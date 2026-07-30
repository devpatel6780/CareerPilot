"""SQLite persistence for the applications table."""

import sqlite3

from db.init_db import DB_PATH


def insert_application(match_id: int, resume_version_id: int | None, status: str = "Not Applied") -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO applications (match_id, resume_version_id, status) VALUES (?, ?, ?)",
            (match_id, resume_version_id, status),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_application_status(application_id: int, status: str, date_applied: str | None = None) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "UPDATE applications SET status = ?, date_applied = COALESCE(?, date_applied) WHERE id = ?",
            (status, date_applied, application_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def list_applications() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """SELECT a.id, a.created_at, a.status, a.date_applied,
                      a.match_id, a.resume_version_id,
                      j.company, j.title, m.match_score
               FROM applications a
               JOIN matches m ON m.id = a.match_id
               JOIN jobs j ON j.id = m.job_id
               ORDER BY a.id DESC"""
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "status": row[2],
            "date_applied": row[3],
            "match_id": row[4],
            "resume_version_id": row[5],
            "company": row[6],
            "title": row[7],
            "match_score": row[8],
        }
        for row in rows
    ]
