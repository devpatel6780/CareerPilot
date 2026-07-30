import sys
from pathlib import Path

# `agents/` lives at the repo root (sibling of `backend/`), so make it
# importable when running with cwd=backend, as the project's run commands do.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.init_db import init_db
from routers.applications import router as applications_router
from routers.cover_letter import router as cover_letter_router
from routers.jobs import router as jobs_router
from routers.match import router as match_router
from routers.resume import router as resume_router
from routers.tailor import router as tailor_router

app = FastAPI(title="AI Career Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(match_router)
app.include_router(tailor_router)
app.include_router(cover_letter_router)
app.include_router(applications_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
