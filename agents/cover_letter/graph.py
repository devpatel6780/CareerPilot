"""Cover Letter Agent: a single-node LangGraph subgraph that turns a resume
+ job + tone preference into a cover letter, grounded only in resume content
(same truthfulness constraint as the Tailoring Agent — no fabricated claims).
"""

import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm_client import generate

from .schema import CoverLetter

PROMPT_TEMPLATE = """You are a cover letter writer. Write a cover letter for the candidate below, for the specific job below, in a {tone} tone.

Rules:
- Only reference experience, skills, and achievements that are explicitly present in the candidate's resume below. Never invent employers, technologies, metrics, or accomplishments.
- Make it specific to this job — reference its actual title/company/requirements, not generic filler.
- Keep it to 3-4 paragraphs.

Candidate resume (structured):
{resume_json}

Target job (structured):
{job_json}
"""


class CoverLetterState(TypedDict):
    resume: dict
    job: dict
    tone: str
    result: CoverLetter | None


def _write_cover_letter(state: CoverLetterState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        tone=state["tone"],
        resume_json=json.dumps(state["resume"], indent=2),
        job_json=json.dumps(state["job"], indent=2),
    )
    result = generate(prompt, schema=CoverLetter)
    return {"result": result}


def _build_graph():
    graph = StateGraph(CoverLetterState)
    graph.add_node("write_cover_letter", _write_cover_letter)
    graph.add_edge(START, "write_cover_letter")
    graph.add_edge("write_cover_letter", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def generate_cover_letter(resume: dict, job: dict, tone: str = "professional") -> str:
    result = get_graph().invoke({"resume": resume, "job": job, "tone": tone, "result": None})
    return result["result"].cover_letter
