# AI Career Agent — Autonomous Resume/Job Matching & Tailoring System

## Working Agreement — Read This First

**This project is built one phase at a time. Do not proceed past a phase's
"Done when" criteria without explicit user confirmation, even if running in
auto-accept / yolo mode.**

Rules for the build agent:
- After completing a phase, STOP. Do not start the next phase automatically.
- Summarize what was built, how it maps to the phase's done-criteria, and
  how the user can verify it themselves (exact command to run, endpoint to
  hit, or UI action to try).
- Wait for the user to explicitly say "continue" / "approved" / "start
  Phase N" before touching the next phase.
- If you finish a phase and are unsure whether something counts as "done,"
  say so and ask — do not silently mark it done and move on.
- Never bundle two phases into one commit/session even if they seem small
  or related.

## Overview
An AI-powered career assistant that analyzes a candidate's resume, ingests job
descriptions from public job board APIs, scores fit between resume and job,
tailors resume content for a specific role, and tracks applications in a
dashboard. Built as a portfolio-level, eval-first multi-agent system —
architecture and rigor mirror the RAG Evaluation Harness (golden sets,
retrieval/matching metrics, regression tracking) rather than a simple chatbot
wrapper. Single-user, local-first, no auth required.

**Explicitly out of scope for this build:** browser automation / auto-apply
to real job platforms, and scraping LinkedIn/Indeed. Both carry ToS and
account-ban risk on platforms the user is actively using for their own job
search. These are noted as "future work" only.

## Tech Stack & Architecture

- **Backend:** FastAPI (Python) — consistent with prior projects, good async
  support for multi-agent tool calling.
- **AI Framework:** LangGraph for agent orchestration — matches the RAG
  project's pattern, gives explicit state graphs per agent instead of opaque
  chains.
- **LLM:** NVIDIA NIM free tier as primary (consistent with RAG project).
  Design the LLM client as a thin abstraction layer (single `llm_client.py`
  with a swappable provider) so Claude/GPT can be added later without
  touching agent logic.
- **Vector DB:** ChromaDB — same as RAG project, stores resume/job embeddings
  for similarity search.
- **Relational DB:** SQLite (local-first, zero setup; matches single-user
  scope). Schema designed so a future Postgres swap is a connection-string
  change, not a rewrite.
- **Job Ingestion:** Greenhouse Job Board API (`boards-api.greenhouse.io`)
  and Lever Postings API (`api.lever.co/v0/postings/{company}`) — both are
  public, unauthenticated, ToS-safe endpoints designed for external
  consumption.
- **Frontend:** Next.js (React) — full app per user preference, serves the
  tracking dashboard and job/resume upload UI.
- **Embeddings:** all-MiniLM-L6-v2 (via sentence-transformers), consistent
  with RAG project.

### Architecture sketch

```
Next.js Frontend
      │
      ▼
FastAPI Backend  ──────────────────────────────┐
      │                                        │
      ▼                                        ▼
LangGraph Agent Orchestrator            SQLite (users, resumes,
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

Each agent is a LangGraph subgraph with its own state schema, callable
independently and testable in isolation — no agent directly calls another
agent's internals, only the orchestrator sequences them.

## Functional Requirements (by phase)

### Phase 0 — Foundation
**Build:**
- Repo scaffold: `backend/` (FastAPI), `frontend/` (Next.js), `agents/`
  (LangGraph agents), `eval/` (golden sets + metrics scripts)
- SQLite schema (see Data & Inputs below)
- `llm_client.py` abstraction wrapping NVIDIA NIM calls
- `.env.example` with `NVIDIA_NIM_API_KEY` placeholder
- Health-check endpoint (`GET /health`)

**Done when:** `uvicorn main:app` runs, `/health` returns 200, SQLite tables
exist and are inspectable, a test call through `llm_client.py` returns a
completion from NVIDIA NIM.

---

### Phase 1 — Resume Analysis Agent
**Build:**
- `POST /resume/upload` — accepts PDF/DOCX, extracts raw text
  (use `pypdf`/`python-docx`, not OCR — assume text-based resumes)
- LangGraph agent: raw text → structured JSON matching the Resume Schema
  (below), via a single structured-output LLM call with the schema as a
  strict JSON-mode prompt
- Store structured resume in SQLite (`resumes` table) and embed key sections
  (skills, experience bullets) into ChromaDB, one collection per resume
  version, tagged with `resume_id`

**Done when:** Uploading a real resume returns a structured JSON profile
with populated skills/experience/education/projects arrays, and the same
data is queryable from SQLite and embedded in ChromaDB.

---

### Phase 2 — Job Ingestion Agent
**Build:**
- `POST /jobs/ingest/greenhouse/{company}` — calls
  `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`, pulls open
  listings
- `POST /jobs/ingest/lever/{company}` — calls
  `https://api.lever.co/v0/postings/{company}`
- LangGraph agent: raw job description text → structured JSON matching the
  Job Schema (below)
- Store in SQLite (`jobs` table) + embed into ChromaDB (`jobs` collection)
- `GET /jobs` — list ingested jobs

**Done when:** Given a real company slug (e.g. `stripe`, `notion` for
Greenhouse; a valid Lever company), the endpoint returns 5+ structured job
postings with populated requirements/skills fields.

---

### Phase 3 — Matching & Ranking Agent (centerpiece — build with eval from day one)
**Build:**
- LangGraph agent: given `resume_id` + `job_id`, compute:
  - Embedding similarity score (cosine, resume vs. job in ChromaDB)
  - LLM-judged fit score (0-100) with structured rationale: strengths,
    gaps, missing keywords
  - Combined match score (weighted blend, weights configurable)
- `POST /match` — returns `{match_score, rationale, missing_skills[],
  strengths[]}`
- **Golden eval set:** hand-label 15-20 resume/JD pairs (use the user's own
  resume against 15-20 real Greenhouse/Lever postings) as
  good-fit / weak-fit / poor-fit
- `eval/run_matching_eval.py` — scores the matcher against the golden set,
  reports:
  - Correlation (Spearman) between system score and human label
  - Precision/recall on "missing skill" detection vs. manually identified gaps
  - Confusion matrix if treating fit as a 3-class label
- Store eval results with timestamp for regression tracking (same pattern
  as RAG project's regression comparison tooling)

**Done when:** `/match` returns a score + rationale for a real resume/job
pair, and `run_matching_eval.py` produces a metrics report showing the
system's fit judgments meaningfully correlate with human labels (target:
Spearman ρ > 0.6 as a starting bar — document actual result, don't force
this number).

---

### Phase 4 — Resume Tailoring Agent
**Build:**
- LangGraph agent, two-step chain:
  1. Rewrite step: given resume + target job's missing keywords/gaps,
     rewrite relevant bullets to better match, optimize for ATS keyword
     presence
  2. Truthfulness-guard step: separate LLM call comparing tailored output
     against original resume, flagging any claim not traceable to the
     original (dates, technologies, metrics, responsibilities) — reject or
     flag-for-review any hallucinated additions
- `POST /resume/tailor` — `{resume_id, job_id}` → tailored resume text +
  diff (original vs. tailored) + list of any truthfulness flags
- Store each tailored version in SQLite (`resume_versions` table) linked to
  the job it was tailored for

**Done when:** Tailoring a real resume against a real job produces a
modified version with at least 3 concrete bullet-level changes, and the
truthfulness guard correctly flags at least one deliberately-injected false
claim in a test case.

---

### Phase 5 — Cover Letter Agent (stretch, build after 0-4 are solid)
**Build:**
- LangGraph agent: `{resume_id, job_id, tone_preference}` → cover letter
  text, grounded only in resume content (same truthfulness constraint as
  Phase 4)
- `POST /cover-letter/generate`

**Done when:** Generates a coherent, job-specific cover letter referencing
actual resume content (not generic filler) for a real job posting.

---

### Phase 6 — Tracking Dashboard (Next.js frontend)
**Build:**
- Pages: Resume upload, Job list (ingested jobs + ingest-new-company form),
  Match results (score + rationale per job), Application tracker (table:
  company, role, date applied, resume version used, status)
- `application_status` is manually updated by the user via the UI (no
  auto-apply) — dropdown: Not Applied / Applied / Interview / Rejected /
  Offer
- Simple CRUD against the FastAPI backend, no auth (single-user, local)

**Done when:** User can upload a resume, ingest jobs from a real company,
view match scores, generate a tailored resume, and manually log an
application status change — all from the UI, no direct API calls needed.

## Data & Inputs

**Resume Schema (structured JSON, output of Phase 1):**
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

**Job Schema (structured JSON, output of Phase 2):**
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
`applications` — each with an `id`, `created_at`, and foreign keys linking
match → resume + job, application → match + resume_version.

**Data volume:** small (single user, tens of resumes/jobs) — no need for
indexing beyond SQLite defaults or ChromaDB's built-in ANN search.

## Step-by-Step Build Plan

1. Scaffold repo structure, install deps (`fastapi`, `uvicorn`, `langgraph`,
   `langchain-nvidia-ai-endpoints`, `chromadb`, `sentence-transformers`,
   `pypdf`, `python-docx`, `httpx`)
2. Write SQLite schema + migration script (`init_db.py`)
3. Write `llm_client.py`: wraps NVIDIA NIM chat completion, exposes
   `generate(prompt, schema=None)` with optional JSON-mode structured output
4. Build Resume Analysis Agent → test against 2-3 real resumes
5. Build Job Ingestion Agent → test against 2 real Greenhouse companies and
   1 real Lever company
6. Build Matching Agent → build golden eval set → build eval script → run
   and record baseline metrics
7. Build Tailoring Agent + truthfulness guard → test against injected-lie
   test case
8. Build Cover Letter Agent
9. Build Next.js frontend, wire to all endpoints
10. End-to-end manual test: upload resume → ingest jobs → view matches →
    tailor resume → generate cover letter → log application status

## Edge Cases & Constraints

- **Resume parsing:** assume text-based PDF/DOCX; scanned/image resumes are
  out of scope (no OCR pipeline in v1).
- **Job board coverage:** not all companies use Greenhouse or Lever — the
  ingestion agent should fail gracefully (404 handling) with a clear error
  if a company slug isn't found on either platform, not a crash.
- **Rate limits:** NVIDIA NIM free tier has request limits — add basic retry
  with backoff in `llm_client.py`, and cache structured extraction results
  so re-running eval doesn't re-call the LLM unnecessarily.
- **Truthfulness guard is a soft filter, not a hard block:** flag suspicious
  claims for user review rather than silently deleting content — false
  positives are safer than false negatives here, but no auto-editing without
  visibility.
- **No auto-apply, no scraping of LinkedIn/Indeed/Glassdoor** — explicitly
  out of scope, do not implement even as a "nice to have."
- **No auth/multi-tenancy** — single local user, no login system.
- **Cost:** NVIDIA NIM free tier only for v1; leave a clean seam
  (`llm_client.py`) for adding paid providers later, but don't build
  provider-switching UI now.

## Definition of Done

- All 6 phases (0-5, cover letter optional but included) functional
  end-to-end through the Next.js UI
- Matching Agent has a documented eval report (`eval/results/`) with
  golden-set correlation metrics, not just "it seems to work"
- Tailoring Agent's truthfulness guard has at least one passing test case
  proving it catches a fabricated claim
- README documents: architecture diagram, how to run locally, how to run
  the eval script, and the golden-set methodology (this doubles as your
  LinkedIn/portfolio writeup material)
- A short regression check: re-running the matching eval after any prompt
  change to the Matching Agent should be a single script call, with results
  diffable against the previous run (same pattern as the RAG project)
