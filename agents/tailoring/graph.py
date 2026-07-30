"""Resume Tailoring Agent: a two-step LangGraph chain.

1. Rewrite: given the resume + target job, rewrite bullets to better match
   the job's terminology/keywords, using only facts already present in the
   original resume (no new tools/metrics/responsibilities).
2. Truthfulness guard: a separate LLM call comparing the tailored bullets
   against the original resume, flagging (not deleting) any claim not
   traceable to the original — dates, technologies, metrics, responsibilities.

check_truthfulness() is exposed standalone so it can be exercised directly
against a deliberately-injected false claim, independent of the rewrite step.
"""

import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm_client import generate

from .schema import RewriteResult, TailoredExperience, TruthfulnessCheck

REWRITE_PROMPT = """You are a resume editor. Rewrite the candidate's experience bullets and skills below to better align with the target job's terminology and keywords — WITHOUT inventing anything.

Rules:
- Only rephrase, reorder, or re-emphasize facts already present in the original resume. Never add a tool, technology, metric, responsibility, or outcome that isn't already stated in the original bullet.
- If a bullet has nothing legitimate to align with the job, return it unchanged.
- Keep the same number of bullets, in the same order, for each experience entry.
- tailored_skills: the original skills list, optionally reordered to foreground ones relevant to this job — do not add skills not in the original list.

Original resume (structured):
{resume_json}

Target job (structured):
{job_json}
"""

TRUTHFULNESS_PROMPT = """You are a truthfulness auditor. Compare the TAILORED bullets below against the ORIGINAL resume text. Flag any claim in the tailored bullets — a technology, tool, metric, responsibility, or date — that is NOT traceable to the original resume text.

Rules:
- Only flag claims that are actually new or inconsistent with the original. Rephrasing existing facts is fine and should not be flagged.
- Be specific in `concern` about what part of the claim isn't supported by the original.
- If nothing is fabricated, return an empty list.

Original resume text:
---
{original_text}
---

Tailored bullets:
---
{tailored_text}
---
"""


class TailoringState(TypedDict):
    resume: dict
    job: dict
    rewrite: RewriteResult | None
    truthfulness: TruthfulnessCheck | None


def _rewrite(state: TailoringState) -> dict:
    prompt = REWRITE_PROMPT.format(
        resume_json=json.dumps(state["resume"], indent=2),
        job_json=json.dumps(state["job"], indent=2),
    )
    rewrite = generate(prompt, schema=RewriteResult)
    return {"rewrite": rewrite}


def _flatten_experience_text(experience: list[dict]) -> str:
    lines = []
    for entry in experience:
        lines.append(f"{entry.get('title', '')} at {entry.get('company', '')}:")
        lines.extend(f"- {bullet}" for bullet in entry.get("bullets", []))
    return "\n".join(lines)


def _flatten_tailored_text(tailored_experience: list[TailoredExperience]) -> str:
    lines = []
    for entry in tailored_experience:
        lines.append(f"{entry.title} at {entry.company}:")
        lines.extend(f"- {bullet}" for bullet in entry.bullets)
    return "\n".join(lines)


def check_truthfulness(original_experience: list[dict], tailored_experience: list[TailoredExperience]) -> TruthfulnessCheck:
    prompt = TRUTHFULNESS_PROMPT.format(
        original_text=_flatten_experience_text(original_experience),
        tailored_text=_flatten_tailored_text(tailored_experience),
    )
    return generate(prompt, schema=TruthfulnessCheck)


def _truthfulness_guard(state: TailoringState) -> dict:
    check = check_truthfulness(state["resume"].get("experience", []), state["rewrite"].tailored_experience)
    return {"truthfulness": check}


def _build_graph():
    graph = StateGraph(TailoringState)
    graph.add_node("rewrite", _rewrite)
    graph.add_node("truthfulness_guard", _truthfulness_guard)
    graph.add_edge(START, "rewrite")
    graph.add_edge("rewrite", "truthfulness_guard")
    graph.add_edge("truthfulness_guard", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def _compute_diff(original_experience: list[dict], tailored_experience: list[TailoredExperience]) -> list[dict]:
    tailored_by_key = {(e.company, e.title): e for e in tailored_experience}
    diff = []
    for entry in original_experience:
        key = (entry.get("company", ""), entry.get("title", ""))
        tailored = tailored_by_key.get(key)
        if tailored is None:
            continue
        original_bullets = entry.get("bullets", [])
        for i, original_bullet in enumerate(original_bullets):
            tailored_bullet = tailored.bullets[i] if i < len(tailored.bullets) else original_bullet
            if tailored_bullet.strip() != original_bullet.strip():
                diff.append(
                    {
                        "company": key[0],
                        "title": key[1],
                        "bullet_index": i,
                        "original": original_bullet,
                        "tailored": tailored_bullet,
                    }
                )
    return diff


def tailor_resume(resume: dict, job: dict) -> dict:
    result = get_graph().invoke({"resume": resume, "job": job, "rewrite": None, "truthfulness": None})
    rewrite: RewriteResult = result["rewrite"]
    truthfulness: TruthfulnessCheck = result["truthfulness"]

    return {
        "tailored_experience": [e.model_dump() for e in rewrite.tailored_experience],
        "tailored_skills": rewrite.tailored_skills,
        "tailored_text": _flatten_tailored_text(rewrite.tailored_experience),
        "diff": _compute_diff(resume.get("experience", []), rewrite.tailored_experience),
        "truthfulness_flags": [f.model_dump() for f in truthfulness.flags],
    }
