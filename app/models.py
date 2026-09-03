from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    education: str | None = None
    income: float | None = Field(default=None, ge=0)
    occupation: str | None = None
    region: str | None = None
    landholding_acres: float | None = Field(default=None, ge=0)
    enterprise_type: str | None = None


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    role: Literal["citizen", "analyst"] = "citizen"
    profile: UserProfile | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class Citation(BaseModel):
    source_id: str
    title: str
    url: str
    excerpt: str
    relevance: float


class ClaimAudit(BaseModel):
    claim: str
    status: Literal["supported", "partially_supported", "unsupported"]
    evidence_source_ids: list[str] = Field(default_factory=list)
    note: str


class DocumentIn(BaseModel):
    title: str
    domain: str
    agency: str
    source_url: str
    text: str = Field(min_length=20)
    effective_date: str | None = None
    version: str = "1.0"
