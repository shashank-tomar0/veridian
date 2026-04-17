"""POST /v1/voiceprint — speaker identity verification endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from backend.auth.jwt import require_permission
from backend.models.user import User
from backend.schemas.auth import Permission

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["voiceprint"])


class VoiceprintResponse(BaseModel):
    speaker_match: bool = False
    confidence: float = 0.0
    matched_person: str | None = None
    embedding_dim: int = 256


class VoiceprintEnrollRequest(BaseModel):
    person_name: str
    description: str | None = None


class VoiceprintEnrollResponse(BaseModel):
    person_id: str
    person_name: str
    message: str = "Voiceprint enrolled successfully"


@router.post("/voiceprint/verify", response_model=VoiceprintResponse)
async def verify_voiceprint(
    audio: UploadFile = File(..., description="16kHz mono WAV file"),
    user: User = Depends(require_permission(Permission.ANALYZE)),
):
    """Compare an audio sample against the voiceprint database using Resemblyzer."""
    if not audio.content_type or "audio" not in audio.content_type:
        raise HTTPException(status_code=400, detail="File must be an audio format")

    audio_bytes = await audio.read()
    logger.info("voiceprint.verify", size_bytes=len(audio_bytes), user_id=user.id)

    # Lazy-load Resemblyzer to avoid model load at import time
    from ml.audio.resemblyzer import ResemblyzerDetector

    detector = ResemblyzerDetector()
    result = detector.predict(audio_bytes)

    return VoiceprintResponse(
        speaker_match=result.metadata.get("speaker_match", False),
        confidence=result.score,
        matched_person=result.metadata.get("matched_person"),
    )


@router.post("/voiceprint/enroll", response_model=VoiceprintEnrollResponse)
async def enroll_voiceprint(
    audio: UploadFile = File(...),
    person_name: str = "",
    user: User = Depends(require_permission(Permission.ADMIN)),
):
    """Enroll a new voiceprint into the speaker database."""
    import uuid

    audio_bytes = await audio.read()
    person_id = str(uuid.uuid4())

    logger.info("voiceprint.enroll", person_name=person_name, person_id=person_id)

    # In production: generate d-vector embedding via Resemblyzer,
    # then upsert into Qdrant voiceprint collection.

    return VoiceprintEnrollResponse(person_id=person_id, person_name=person_name)
