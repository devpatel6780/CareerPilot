"""Resume Tailoring endpoint: given resume_id + job_id, rewrite resume
bullets toward the job's terminology (Tailoring Agent), run the
truthfulness guard, and store the resulting version.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.tailoring.graph import tailor_resume
from db.jobs import get_job
from db.resume_versions import insert_resume_version
from db.resumes import get_resume

router = APIRouter(tags=["tailor"])


class TailorRequest(BaseModel):
    resume_id: int
    job_id: int


@router.post("/resume/tailor")
def create_tailored_resume(payload: TailorRequest):
    resume = get_resume(payload.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail=f"No resume with id {payload.resume_id}")

    job = get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job with id {payload.job_id}")

    result = tailor_resume(resume["structured"], job["structured"])

    version_id = insert_resume_version(
        payload.resume_id, payload.job_id, result["tailored_text"], result["diff"]
    )

    return {
        "resume_version_id": version_id,
        "tailored_experience": result["tailored_experience"],
        "tailored_skills": result["tailored_skills"],
        "diff": result["diff"],
        "truthfulness_flags": result["truthfulness_flags"],
    }
