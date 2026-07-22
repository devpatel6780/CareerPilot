"""Pydantic model for the LLM-judged half of the Matching Agent's output."""

from pydantic import BaseModel, Field


class MatchJudgment(BaseModel):
    fit_score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
