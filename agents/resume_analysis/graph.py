"""Resume Analysis Agent: a single-node LangGraph subgraph that turns raw
resume text into a structured ResumeProfile via one structured-output LLM
call through llm_client. Self-contained per agent — the orchestrator (routers
in later phases) invokes analyze_resume(), never reaches into this graph.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm_client import generate

from .schema import ResumeProfile

PROMPT_TEMPLATE = """You are a precise resume parser. Extract the resume text below into the required structured schema.

Rules:
- Only use information explicitly present in the resume text. Never invent, infer, or reason about anything ambiguous.
- contact.name: the candidate's name, usually the very first line of the resume — extract it even if spacing looks unusual due to PDF text extraction (e.g. "DEV P ATEL" means the name is "Dev Patel").
- contact.email: the candidate's own email address, found near their name/contact line at the top of the resume (not any other email mentioned elsewhere).
- contact.location: at most 6 words, taken only from a short location string written near the candidate's name/contact line (e.g. "Milwaukee, WI") — this is the candidate's own location, never a former employer's office location from the experience section. If you cannot state it in 6 words or fewer, or it isn't clearly stated near the candidate's name/contact line, leave it "" instead of guessing or explaining.
- skills: list EVERY individual skill, tool, language, and technology mentioned anywhere in the resume (especially any "Skills"/"Technical Skills" section) as short separate strings, not sentences.
- experience: include EVERY job entry found in the resume, each with its exact title, company, start_date, end_date, and every one of its bullet points as a separate string in `bullets`. Do not skip any job.
- education, projects, achievements: extract fully and exactly as written; do not skip any entries.
- Every field in the output must be short and factual — copied or lightly reformatted from the resume text. Never write full sentences of commentary, reasoning, or explanation into any field; if you're unsure, leave the field empty instead.

Resume text:
---
{raw_text}
---
"""


class ResumeAnalysisState(TypedDict):
    raw_text: str
    resume_profile: ResumeProfile | None


def _structure_resume(state: ResumeAnalysisState) -> dict:
    prompt = PROMPT_TEMPLATE.format(raw_text=state["raw_text"])
    profile = generate(prompt, schema=ResumeProfile)
    return {"resume_profile": profile}


def _build_graph():
    graph = StateGraph(ResumeAnalysisState)
    graph.add_node("structure_resume", _structure_resume)
    graph.add_edge(START, "structure_resume")
    graph.add_edge("structure_resume", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def analyze_resume(raw_text: str) -> ResumeProfile:
    result = get_graph().invoke({"raw_text": raw_text, "resume_profile": None})
    return result["resume_profile"]
