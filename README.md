# AI Career Agent

An AI-powered career assistant that analyzes a candidate's resume, ingests job
descriptions from public job board APIs, scores fit between resume and job,
tailors resume content for a specific role, drafts a cover letter, and tracks
applications in a dashboard.

Built as a portfolio-level, **eval-first** multi-agent system: matching
quality is measured against a hand-labeled golden set with correlation
metrics and regression tracking, not just "it seems to work." Single-user,
local-first, no auth required.

**Explicitly out of scope:** browser automation / auto-apply to real job
platforms, and scraping LinkedIn/Indeed/Glassdoor. Both carry ToS and
account-ban risk on platforms the user is actively using for their own job
search — noted as future work only, not implemented here.

## Status

This project is built one phase at a time. Phases 0-2 are done and verified
end-to-end. Phases 3-6 are fully built and locally wiring-tested (mocked LLM
calls), but are still going through live, real-LLM verification in the
browser/CLI before being marked fully done.

| Phase | Description | Status |
|---|---|---|
| 0 | Foundation — repo scaffold, SQLite schema, LLM client, health check | ✅ Done |
| 1 | Resume Analysis Agent — PDF/DOCX → structured JSON | ✅ Done |
| 2 | Job Ingestion Agent — Greenhouse & Lever APIs → structured JSON | ✅ Done |
| 3 | Matching & Ranking Agent — fit scoring + golden-set eval harness | 🔶 Built, verifying live |
| 4 | Resume Tailoring Agent — rewrite + truthfulness guard | 🔶 Built, verifying live |
| 5 | Cover Letter Agent | 🔶 Built, verifying live |
| 6 | Tracking Dashboard (Next.js) | 🔶 Built, verifying live |

## Architecture

```
Next.js Frontend (frontend/)
      │  fetch, CORS to :3000
      ▼
FastAPI Backend (backend/)  ────────────────────┐
      │                                         │
      ▼                                         ▼
LangGraph Agent Orchestrator             SQLite (resumes, resume_versions,
   │        │        │        │           jobs, matches, applications)
   ▼        ▼        ▼        ▼
Resume   Job      Matching  Tailoring   Cover Letter
Analysis Ingestion Agent    Agent       Agent
Agent    Agent        │        │             │
   │        │         ▼        ▼             ▼
   └────┬───┴──── ChromaDB (resume + job embeddings)
        ▼
  NVIDIA NIM LLM client (swappable provider, backend/llm_client.py)
```

Each agent (`agents/resume_analysis`, `agents/job_ingestion`,
`agents/matching`, `agents/tailoring`, `agents/cover_letter`) is a
self-contained LangGraph subgraph with its own state schema, testable in
isolation — no agent calls another agent's internals directly; only the
FastAPI routers in `backend/routers/` sequence them.

**Stack:**
- **Backend:** FastAPI (Python)
- **Agent orchestration:** LangGraph — explicit state graphs per agent instead of opaque chains
- **LLM:** NVIDIA NIM (`meta/llama-3.1-70b-instruct`, free tier), behind a swappable `llm_client.py` abstraction so other providers can be added without touching agent logic. Structured output is pinned to `temperature=0, seed=0` for deterministic extraction.
- **Vector DB:** ChromaDB (`backend/chroma_db/`, gitignored), for resume/job embedding similarity search
- **Relational DB:** SQLite (local-first; schema designed so a future Postgres swap is a connection-string change)
- **Job ingestion:** [Greenhouse Job Board API](https://boards-api.greenhouse.io) and [Lever Postings API](https://api.lever.co) — public, unauthenticated, ToS-safe endpoints
- **Frontend:** Next.js 15 (App Router, TypeScript, React 19), plain `fetch`-based API client — no extra state-management library
- **Embeddings:** `all-MiniLM-L6-v2` via `sentence-transformers`, loaded lazily so the API can boot even if the model isn't reachable yet

## Running locally

Two servers, two terminals.

**Backend:**
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

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000`. The backend must be running on port 8000 — CORS
is configured for `http://localhost:3000` only.

## API reference

| Endpoint | Purpose |
|---|---|
| `POST /resume/upload` | PDF/DOCX → structured Resume Schema, stored in SQLite + embedded in ChromaDB |
| `GET /resume` | List uploaded resumes |
| `POST /jobs/ingest/greenhouse/{company}?limit=` | Ingest open listings from a Greenhouse board |
| `POST /jobs/ingest/lever/{company}?limit=` | Ingest open listings from a Lever board |
| `GET /jobs` | List ingested jobs |
| `POST /match` | Score a `resume_id`/`job_id` pair (embedding similarity + LLM judgment) |
| `GET /matches` / `GET /matches/{id}` | List / fetch past matches |
| `POST /resume/tailor` | Rewrite resume bullets toward a job + truthfulness-check the result |
| `POST /cover-letter/generate` | Generate a job-specific cover letter grounded in resume content |
| `POST /applications` | Track an application from a match (+ optional tailored resume version) |
| `GET /applications` | List tracked applications |
| `PATCH /applications/{id}` | Update application status (Not Applied/Applied/Interview/Rejected/Offer) |

Example calls:
```bash
curl.exe -F "file=@path/to/resume.pdf" http://localhost:8000/resume/upload
curl.exe -X POST "http://localhost:8000/jobs/ingest/greenhouse/stripe?limit=10"
curl.exe http://localhost:8000/jobs

# PowerShell: use single quotes around the JSON body, or Invoke-RestMethod
curl.exe -X POST http://localhost:8000/match -H "Content-Type: application/json" -d '{"resume_id": 1, "job_id": 1}'
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

**SQLite tables:**
- `resumes` (`id`, `created_at`, `raw_text`, `structured_json`)
- `jobs` (`id`, `created_at`, `title`, `company`, `location`, `source`, `source_url`, `structured_json`)
- `matches` (`id`, `created_at`, `resume_id` → `resumes`, `job_id` → `jobs`, `match_score`, `rationale_json`)
- `resume_versions` (`id`, `created_at`, `resume_id` → `resumes`, `job_id` → `jobs`, `tailored_text`, `diff_json`) — one row per tailoring run
- `applications` (`id`, `created_at`, `match_id` → `matches`, `resume_version_id` → `resume_versions` (nullable), `status`, `date_applied`)

**ChromaDB collections:** one `resume_{id}` collection per resume version
(skills + experience bullets), and a single shared `jobs` collection (all
jobs' requirements/skills/responsibilities), each document tagged with
`resume_id` or `job_id` metadata.

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
   Target bar: Spearman ρ > 0.6 (documented, not forced).

## Tailoring Agent truthfulness guard (Phase 4)

`POST /resume/tailor` runs a two-step chain: a rewrite step (bullets
reworded toward the job's terminology, using only facts already in the
original resume) followed by a separate truthfulness-guard LLM call that
flags — never silently deletes — any claim in the tailored output not
traceable to the original resume.

`eval/test_truthfulness_guard.py` is a standalone regression check: it feeds
the guard a tailored bullet with a deliberately fabricated claim ("led a
team of 12 engineers... using Kubernetes," neither present in the original)
and confirms the guard catches it:
```bash
backend/.venv/Scripts/python eval/test_truthfulness_guard.py
```

## Frontend (Phase 6)

Four pages under `frontend/app/`:
- **Resume** (`/`) — upload a PDF/DOCX, view extracted skills/experience, list past uploads
- **Jobs** (`/jobs`) — ingest a company's Greenhouse/Lever board by slug, list ingested jobs
- **Matches** (`/matches`) — pick a resume + job, run a match, then tailor the resume and/or generate a cover letter from the same result, and track the application
- **Tracker** (`/tracker`) — table of tracked applications with a status dropdown (Not Applied/Applied/Interview/Rejected/Offer) — manually updated only, no auto-apply

`frontend/lib/api.ts` is the single fetch-based client the pages call into;
`NEXT_PUBLIC_API_BASE_URL` overrides the default `http://localhost:8000` if
needed.
