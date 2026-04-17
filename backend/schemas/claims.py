"""Pydantic v2 schemas for claims endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.schemas.analysis import VerdictLabel, EvidenceItem


class ClaimCategory(str, Enum):
    POLITICAL = "political"
    HEALTH = "health"
    SCIENCE = "science"
    FINANCIAL = "financial"
    SOCIAL = "social"
    OTHER = "other"


class ClaimFilter(BaseModel):
    """Query parameters for paginated claim browsing."""
    language: str | None = None
    verdict: VerdictLabel | None = None
    category: ClaimCategory | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    search_query: str | None = None


class ClaimResponse(BaseModel):
    """Single claim record returned by the API."""
    id: str
    original_text: str
    language: str | None = None
    category: ClaimCategory | None = None
    checkworthiness_score: float | None = None
    verdict: VerdictLabel | None = None
    confidence: float | None = None
    reasoning: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    source_analysis_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ClaimListResponse(BaseModel):
    """Paginated list of claims."""
    claims: list[ClaimResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class ClaimGraphNode(BaseModel):
    """Node in the claim relationship graph."""
    id: str
    label: str
    verdict: VerdictLabel | None = None
    velocity: float = 0.0
    size: float = 1.0


class ClaimGraphEdge(BaseModel):
    """Edge between claim nodes."""
    source: str
    target: str
    similarity_score: float


class ClaimGraphResponse(BaseModel):
    """Neo4j subgraph for the D3.js force simulation."""
    nodes: list[ClaimGraphNode]
    edges: list[ClaimGraphEdge]
