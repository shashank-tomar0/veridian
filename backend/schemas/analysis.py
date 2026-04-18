"""Pydantic v2 schemas for analysis endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerdictLabel(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    MISLEADING = "MISLEADING"
    UNVERIFIABLE = "UNVERIFIABLE"


# ── Request Schemas ──────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Submit media or text for misinformation analysis."""
    media_url: str | None = Field(None, description="MinIO / pre-signed URL of media artifact")
    text: str | None = Field(None, description="Raw text to analyse")
    media_type: MediaType = Field(..., description="Modality of the input")
    language: str = Field("auto", description="ISO-639 language code or 'auto'")
    callback_url: str | None = Field(None, description="Webhook URL for result delivery")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"json_schema_extra": {
        "examples": [{
            "text": "The government announced free electricity for all citizens starting next month.",
            "media_type": "text",
            "language": "en",
        }]
    }}


class AnalyzeResponse(BaseModel):
    """Returned immediately on POST /v1/analyze."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: AnalysisStatus = AnalysisStatus.PENDING
    message: str = "Analysis queued successfully"


# ── Detection Result Schemas ─────────────────────────────────────────────────

class DetectionScore(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str = Field(..., description="Detector that produced the score")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0‒1")
    verdict: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    source_url: str | None = None
    source_name: str | None = None
    excerpt: str = ""
    relevance_score: float = 0.0


class ClaimVerdict(BaseModel):
    claim_text: str
    verdict: VerdictLabel = VerdictLabel.UNVERIFIABLE
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    evidence_used: list[EvidenceItem] = Field(default_factory=list)
    checkworthiness_score: float = 0.0


class TrustReceipt(BaseModel):
    """The unified output artifact containing all detection + verification results."""
    analysis_id: str
    overall_verdict: VerdictLabel = VerdictLabel.UNVERIFIABLE
    overall_confidence: float = 0.0
    detection_scores: list[DetectionScore] = Field(default_factory=list)
    claim_verdicts: list[ClaimVerdict] = Field(default_factory=list)
    media_type: MediaType = MediaType.TEXT
    language: str = "auto"
    processing_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    receipt_image_url: str | None = None


class AnalysisStatusResponse(BaseModel):
    """Polling response for GET /v1/analyze/{analysis_id}."""
    analysis_id: str
    status: AnalysisStatus
    trust_receipt: TrustReceipt | None = None
    error: str | None = None
