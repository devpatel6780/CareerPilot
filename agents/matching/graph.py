"""Matching & Ranking Agent: given a resume_id + job_id (and their structured
JSON), computes an embedding similarity score and an LLM-judged fit score in
parallel, then combines them into a single weighted match score. Self
-contained per agent — routers invoke run_match(), never reach into this
graph.
"""

import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm_client import generate

from .schema import MatchJudgment
from .similarity import resume_job_similarity

EMBEDDING_WEIGHT = 0.4
LLM_WEIGHT = 0.6

PROMPT_TEMPLATE = """You are an expert technical recruiter judging fit between a candidate's resume and a job posting.

Resume (structured):
{resume_json}

Job posting (structured):
{job_json}

Rules:
- fit_score: 0-100, how well this candidate's actual resume matches this specific job's actual requirements. Base it only on the content given below, not general assumptions about the role.
- strengths: specific ways the candidate's resume matches this job's requirements/skills — cite what's actually present in both.
- gaps: specific requirements or skills from the job posting the resume shows no evidence of.
- missing_skills: specific required_skills (or nice_to_have_skills) from the job posting that don't appear anywhere in the resume's skills or experience bullets.
- Do not invent resume content or job requirements not present in the text above.
"""


class MatchState(TypedDict):
    resume: dict
    job: dict
    resume_id: int
    job_id: int
    embedding_score: float | None
    judgment: MatchJudgment | None
    match_score: float
    rationale: dict


def _score_embedding(state: MatchState) -> dict:
    score = resume_job_similarity(state["resume_id"], state["job_id"])
    return {"embedding_score": score}


def _judge_llm(state: MatchState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        resume_json=json.dumps(state["resume"], indent=2),
        job_json=json.dumps(state["job"], indent=2),
    )
    judgment = generate(prompt, schema=MatchJudgment)
    return {"judgment": judgment}


def _combine(state: MatchState) -> dict:
    judgment = state["judgment"]
    embedding_score = state["embedding_score"]

    if embedding_score is None:
        # No stored embeddings on one side (e.g. nothing to embed) -> fall back to the LLM score alone.
        match_score = float(judgment.fit_score)
    else:
        match_score = EMBEDDING_WEIGHT * embedding_score + LLM_WEIGHT * judgment.fit_score
    match_score = max(0.0, min(100.0, round(match_score, 1)))

    rationale = {
        "strengths": judgment.strengths,
        "gaps": judgment.gaps,
        "embedding_similarity": embedding_score,
        "llm_fit_score": judgment.fit_score,
    }
    return {"match_score": match_score, "rationale": rationale}


def _build_graph():
    graph = StateGraph(MatchState)
    graph.add_node("score_embedding", _score_embedding)
    graph.add_node("judge_llm", _judge_llm)
    graph.add_node("combine", _combine)
    graph.add_edge(START, "score_embedding")
    graph.add_edge(START, "judge_llm")
    graph.add_edge("score_embedding", "combine")
    graph.add_edge("judge_llm", "combine")
    graph.add_edge("combine", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def run_match(resume_id: int, job_id: int, resume: dict, job: dict) -> dict:
    result = get_graph().invoke(
        {
            "resume": resume,
            "job": job,
            "resume_id": resume_id,
            "job_id": job_id,
            "embedding_score": None,
            "judgment": None,
            "match_score": 0.0,
            "rationale": {},
        }
    )
    return {
        "match_score": result["match_score"],
        "rationale": result["rationale"],
        "missing_skills": result["judgment"].missing_skills,
        "strengths": result["judgment"].strengths,
    }
