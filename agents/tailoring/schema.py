"""Pydantic models for the Resume Tailoring Agent's two-step chain."""

from pydantic import BaseModel, Field


class TailoredExperience(BaseModel):
    title: str = ""
    company: str = ""
    bullets: list[str] = Field(default_factory=list)


class RewriteResult(BaseModel):
    tailored_experience: list[TailoredExperience] = Field(default_factory=list)
    tailored_skills: list[str] = Field(default_factory=list)


class TruthfulnessFlag(BaseModel):
    bullet: str
    concern: str


class TruthfulnessCheck(BaseModel):
    flags: list[TruthfulnessFlag] = Field(default_factory=list)
