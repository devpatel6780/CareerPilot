"""Matching & Ranking endpoint: given resume_id + job_id, score fit via the
Matching Agent (embedding similarity + LLM judgment + weighted combine).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.matching.graph import run_match
from db.jobs import get_job
from db.matches import get_match, insert_match, list_matches
from db.resumes import get_resume

router = APIRouter(tags=["match"])


class MatchRequest(BaseModel):
    resume_id: int
    job_id: int


@router.post("/match")
def create_match(payload: MatchRequest):
    resume = get_resume(payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail=f"No resume with id {payload.resume_id}")

    job = get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {payload.job_id}")

    result = run_match(payload.resume_id, payload.job_id, resume["structured"], job["structured"])
    match_id = insert_match(payload.resume_id, payload.job_id, result["match_score"], result["rationale"])

    return {
        "match_id": match_id,
        "match_score": result["match_score"],
        "rationale": result["rationale"],
        "missing_skills": result["missing_skills"],
        "strengths": result["strengths"],
    }


@router.get("/matches")
def get_matches():
    return {"matches": list_matches()}


@router.get("/matches/{match_id}")
def get_one_match(match_id: int):
    match = get_match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No match with id {match_id}")
    return match
