"""Pydantic model for the LLM-derived portion of the Job Schema in
ai-career-agent-build-spec.md. title/company/location/source/source_url/
raw_description come straight from the job board API, not the LLM.
"""

from pydantic import BaseModel, Field


class JobExtraction(BaseModel):
    requirements: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
