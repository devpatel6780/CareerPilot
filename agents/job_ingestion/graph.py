"""Job Ingestion Agent: a single-node LangGraph subgraph that turns a raw
job description into structured requirements/skills/responsibilities via one
structured-output LLM call through llm_client. Self-contained per agent —
routers invoke analyze_job(), never reach into this graph.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llm_client import generate

from .schema import JobExtraction

PROMPT_TEMPLATE = """You are a job description parser. Extract the job description text below into the required structured schema.

Rules:
- Only use information explicitly present in the text. Never invent requirements or skills not mentioned.
- requirements: list each distinct requirement/qualification as its own short string (e.g. "3+ years of Python experience", "Bachelor's degree in Computer Science").
- required_skills: list each explicitly required skill/tool/technology as a short separate string, not a full sentence.
- nice_to_have_skills: list skills/tools the text explicitly describes as preferred, a plus, or nice-to-have. Do not put a skill here unless the text distinguishes it from the required ones.
- responsibilities: list each distinct day-to-day responsibility/duty as its own short string.
- If a category has no clearly matching content in the text, leave its list empty — do not guess.

Job description text:
---
{raw_text}
---
"""


class JobAnalysisState(TypedDict):
    raw_text: str
    extraction: JobExtraction | None


def _structure_job(state: JobAnalysisState) -> dict:
    prompt = PROMPT_TEMPLATE.format(raw_text=state["raw_text"])
    extraction = generate(prompt, schema=JobExtraction)
    return {"extraction": extraction}


def _build_graph():
    graph = StateGraph(JobAnalysisState)
    graph.add_node("structure_job", _structure_job)
    graph.add_edge(START, "structure_job")
    graph.add_edge("structure_job", END)
    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def analyze_job(raw_text: str) -> JobExtraction:
    result = get_graph().invoke({"raw_text": raw_text, "extraction": None})
    return result["extraction"]
