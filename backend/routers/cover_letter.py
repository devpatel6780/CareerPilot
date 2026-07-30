"""Cover Letter endpoint: given resume_id + job_id (+ optional tone),
generate a job-specific cover letter grounded only in resume content.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.cover_letter.graph import generate_cover_letter
from db.jobs import get_job
from db.resumes import get_resume

router = APIRouter(tags=["cover-letter"])


class CoverLetterRequest(BaseModel):
    resume_id: int
    job_id: int
    tone_preference: str = "professional"


@router.post("/cover-letter/generate")
def create_cover_letter(payload: CoverLetterRequest):
    resume = get_resume(payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail=f"No resume with id {payload.resume_id}")

    job = get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {payload.job_id}")

    cover_letter = generate_cover_letter(resume["structured"], job["structured"], payload.tone_preference)

    return {"cover_letter": cover_letter}
