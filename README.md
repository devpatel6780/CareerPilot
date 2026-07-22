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
| 2 | Job Ingestion Agent — Greenhouse & Lever APIs → structured JSON | ✅ Done |
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

Backend foundation (Phase 0), the Resume Analysis Agent (Phase 1), and the Job Ingestion Agent (Phase 2) exist so far.

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

Ingest jobs from a real company's Greenhouse or Lever board, then list them:
```bash
curl.exe -X POST "http://localhost:8000/jobs/ingest/greenhouse/{company}?limit=20"
curl.exe -X POST "http://localhost:8000/jobs/ingest/lever/{company}?limit=20"
curl.exe http://localhost:8000/jobs
```

Score fit between a resume and a job (both must already be ingested):
```bash
curl.exe -X POST http://localhost:8000/match -H "Content-Type: application/json" -d "{\"resume_id\": 1, \"job_id\": 1}"
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

## Matching Agent eval (Phase 3)

`POST /match` scores a resume/job pair with a combined score: 40% embedding
similarity (cosine, between mean-pooled ChromaDB vectors for that resume and
job) + 60% LLM-judged fit score (0-100, with structured `strengths`/`gaps`/
`missing_skills`). Weights live as constants in `agents/matching/graph.py`.

To evaluate matching quality against your own judgment:

1. Ingest a resume and a mix of relevant/irrelevant jobs so you have real
   `resume_id`/`job_id` pairs to label.
2. Copy `eval/golden_set.example.json` to `eval/golden_set.json` and, for
   15-20 real pairs, fill in `human_label` (`good_fit`/`weak_fit`/`poor_fit`)
   and optionally `human_missing_skills` (skills you can see the job needs
   that the resume doesn't have).
3. Run the eval script:
   ```bash
   backend/.venv/Scripts/python eval/run_matching_eval.py
   ```
   It reports Spearman correlation between the system's score and your
   labels, precision/recall on missing-skill detection vs. what you listed,
   and a 3-class confusion matrix (score thresholds: ≥70 good, ≥40 weak,
   else poor — see `GOOD_FIT_THRESHOLD`/`WEAK_FIT_THRESHOLD` in the script).
   Each run is saved as a timestamped JSON file under `eval/results/`, so
   later runs after a prompt/weight change are diffable against earlier ones.

## Roadmap detail

- **Tailoring Agent (Phase 4):** two-step chain — rewrite bullets to close
  keyword/skill gaps, then a separate truthfulness-guard LLM call that flags
  (not silently deletes) any claim not traceable to the original resume.
- **Tracking Dashboard (Phase 6):** resume upload, job ingestion by company
  slug, match results, and a manually-updated application status tracker
  (Not Applied / Applied / Interview / Rejected / Offer) — no auto-apply.
