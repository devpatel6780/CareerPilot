"""Job Ingestion endpoints: Greenhouse/Lever -> structured JSON (Job
Ingestion LangGraph agent) -> SQLite + ChromaDB.
"""

from fastapi import APIRouter, HTTPException, Query

from agents.job_ingestion.errors import CompanyNotFound
from agents.job_ingestion.graph import analyze_job
from agents.job_ingestion.greenhouse import fetch_greenhouse_jobs
from agents.job_ingestion.lever import fetch_lever_jobs
from db.jobs import insert_job, list_jobs
from vector_store import embed_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _ingest(raw_jobs: list[dict]) -> list[dict]:
    ingested = []
    for raw_job in raw_jobs:
        extraction = analyze_job(raw_job["raw_description"])
        structured = {
            "title": raw_job["title"],
            "company": raw_job["company"],
            "location": raw_job["location"],
            "source": raw_job["source"],
            "source_url": raw_job["source_url"],
            "requirements": extraction.requirements,
            "required_skills": extraction.required_skills,
            "nice_to_have_skills": extraction.nice_to_have_skills,
            "responsibilities": extraction.responsibilities,
            "raw_description": raw_job["raw_description"],
        }
        job_id = insert_job(
            structured["title"],
            structured["company"],
            structured["location"],
            structured["source"],
            structured["source_url"],
            structured,
        )
        embed_job(job_id, structured)
        ingested.append({"job_id": job_id, "job": structured})
    return ingested


@router.post("/ingest/greenhouse/{company}")
def ingest_greenhouse(company: str, limit: int = Query(20, ge=1, le=100)):
    try:
        raw_jobs = fetch_greenhouse_jobs(company, limit=limit)
    except CompanyNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ingested": len(raw_jobs), "jobs": _ingest(raw_jobs)}


@router.post("/ingest/lever/{company}")
def ingest_lever(company: str, limit: int = Query(20, ge=1, le=100)):
    try:
        raw_jobs = fetch_lever_jobs(company, limit=limit)
    except CompanyNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ingested": len(raw_jobs), "jobs": _ingest(raw_jobs)}


@router.get("")
def get_jobs():
    return {"jobs": list_jobs()}
