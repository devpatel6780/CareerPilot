# AI Career Agent

An AI-powered career assistant that analyzes a candidate's resume, ingests job
descriptions from public job board APIs, scores fit between resume and job,
tailors resume content for a specific role, and tracks applications in a
dashboard.

Built as a portfolio-level, **eval-first** multi-agent system: matching
quality is measured against a hand-labeled golden set with correlation
metrics and regression tracking, not just "it seems to work." Single-user,
local-first, no auth required.

**Explicitly out of scope:** browser automation / auto-apply to real job
platforms, and scraping LinkedIn/Indeed/Glassdoor. Both carry ToS and
account-ban risk on platforms the user is actively using for their own job
search — noted as future work only, not implemented here.

## Status

This project is built one phase at a time, with each phase fully working
before the next starts.

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation — repo scaffold, SQLite schema, LLM client, health check | ✅ Done |
| 1 | Resume Analysis Agent — PDF/DOCX → structured JSON | ✅ Done |
| 2 | Job Ingestion Agent — Greenhouse & Lever APIs → structured JSON | ⬜ Not started |
| 3 | Matching & Ranking Agent — fit scoring + golden-set eval harness | ⬜ Not started |
| 4 | Resume Tailoring Agent — rewrite + truthfulness guard | ⬜ Not started |
| 5 | Cover Letter Agent | ⬜ Not started |
| 6 | Tracking Dashboard (Next.js) | ⬜ Not started |

## Architecture

```
Next.js Frontend
      │
      ▼
FastAPI Backend  ──────────────────────────────┐
      │                                        │
      ▼                                        ▼
LangGraph Agent Orchestrator            SQLite (resumes, resume_versions,
   │        │        │        │          jobs, matches, applications)
   ▼        ▼        ▼        ▼
Resume   Job      Matching  Tailoring
Analysis Ingestion Agent    Agent
Agent    Agent        │        │
   │        │         ▼        ▼
   └────┬───┘    ChromaDB (resume + job embeddings)
        ▼
  NVIDIA NIM LLM client (swappable provider)
```

Each agent is a self-contained LangGraph subgraph with its own state schema,
testable in isolation — no agent calls another agent's internals directly,
only the orchestrator sequences them.

**Stack:**
- **Backend:** FastAPI (Python)
- **Agent orchestration:** LangGraph — explicit state graphs per agent instead of opaque chains
- **LLM:** NVIDIA NIM (free tier), behind a swappable `llm_client.py` abstraction so other providers can be added without touching agent logic
- **Vector DB:** ChromaDB, for resume/job embedding similarity search
- **Relational DB:** SQLite (local-first; schema designed so a future Postgres swap is a connection-string change)
- **Job ingestion:** [Greenhouse Job Board API](https://boards-api.greenhouse.io) and [Lever Postings API](https://api.lever.co) — public, unauthenticated, ToS-safe endpoints
- **Frontend:** Next.js (React)
- **Embeddings:** `all-MiniLM-L6-v2` via `sentence-transformers`

## Running locally

Backend foundation (Phase 0) and the Resume Analysis Agent (Phase 1) exist so far.

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv\Scripts\pip on native Windows shells

# create .env at the repo root with your key
# NVIDIA_NIM_API_KEY=your_key_here

# initialize the SQLite schema (idempotent, safe to re-run)
.venv/Scripts/python db/init_db.py

# run the API
.venv/Scripts/python -m uvicorn main:app --reload --port 8000
curl http://localhost:8000/health
```

`/health` should return `{"status": "ok"}`.

Upload a resume (PDF or DOCX) to get back its structured profile:
```bash
curl.exe -F "file=@path/to/resume.pdf" http://localhost:8000/resume/upload
```

## Data model

**Resume Schema** (structured output of the Resume Analysis Agent, Phase 1):
```json
{
  "contact": {"name": "", "email": "", "location": ""},
  "skills": ["string"],
  "experience": [
    {"title": "", "company": "", "start_date": "", "end_date": "",
     "bullets": ["string"]}
  ],
  "education": [{"degree": "", "institution": "", "graduation_date": ""}],
  "projects": [{"name": "", "description": "", "technologies": ["string"]}],
  "achievements": ["string"]
}
```

**Job Schema** (structured output of the Job Ingestion Agent, Phase 2):
```json
{
  "title": "", "company": "", "location": "", "source": "greenhouse|lever",
  "source_url": "",
  "requirements": ["string"], "required_skills": ["string"],
  "nice_to_have_skills": ["string"], "responsibilities": ["string"],
  "raw_description": ""
}
```

**SQLite tables:** `resumes`, `resume_versions`, `jobs`, `matches`,
`applications` — each with an `id` and `created_at`, with foreign keys
linking match → resume + job, and application → match + resume_version.

## Roadmap detail

- **Matching Agent (Phase 3):** hand-labeled golden set of 15-20 real
  resume/JD pairs (good-fit / weak-fit / poor-fit), scored via embedding
  similarity + LLM-judged fit with structured rationale. `eval/` will hold
  the eval script reporting Spearman correlation against human labels,
  precision/recall on missing-skill detection, and a confusion matrix —
  with results timestamped for regression tracking across prompt changes.
- **Tailoring Agent (Phase 4):** two-step chain — rewrite bullets to close
  keyword/skill gaps, then a separate truthfulness-guard LLM call that flags
  (not silently deletes) any claim not traceable to the original resume.
- **Tracking Dashboard (Phase 6):** resume upload, job ingestion by company
  slug, match results, and a manually-updated application status tracker
  (Not Applied / Applied / Interview / Rejected / Offer) — no auto-apply.
