"""Resume upload endpoint: PDF/DOCX -> raw text -> structured profile
(Resume Analysis LangGraph agent) -> SQLite + ChromaDB.
"""

from fastapi import APIRouter, HTTPException, UploadFile

from agents.resume_analysis.extract import UnsupportedResumeFormat, extract_text
from agents.resume_analysis.graph import analyze_resume
from db.resumes import insert_resume
from vector_store import embed_resume

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile):
    content = await file.read()

    try:
        raw_text = extract_text(file.filename or "", content)
    except UnsupportedResumeFormat as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in this file — scanned/image-based resumes aren't supported.",
        )

    profile = analyze_resume(raw_text)
    structured = profile.model_dump()

    resume_id = insert_resume(raw_text, structured)
    embed_resume(resume_id, structured)

    return {"resume_id": resume_id, "resume": structured}
