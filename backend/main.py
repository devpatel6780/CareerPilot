import sys
from pathlib import Path

# `agents/` lives at the repo root (sibling of `backend/`), so make it
# importable when running with cwd=backend, as the project's run commands do.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI

from db.init_db import init_db
from routers.jobs import router as jobs_router
from routers.match import router as match_router
from routers.resume import router as resume_router

app = FastAPI(title="AI Career Agent")
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(match_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
