"""POST /v1/image — standalone image analysis endpoints."""

from __future__ import annotations

import io
import tempfile
import uuid

import structlog
from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel, Field

from backend.auth.jwt import require_permission
from backend.models.user import User
from backend.schemas.analysis import DetectionScore
from backend.schemas.auth import Permission

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["image"])


class ImageAnalysisResponse(BaseModel):
    analysis_id: str
    detections: list[DetectionScore] = Field(default_factory=list)
    overall_forgery_score: float = 0.0
    ai_generated_score: float = 0.0
    context_mismatch_score: float = 0.0


@router.post("/image/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    caption: str = "",
    user: User = Depends(require_permission(Permission.ANALYZE)),
):
    """Run ELA + DIRE + CLIP detectors on an uploaded image."""
    analysis_id = str(uuid.uuid4())
    content = await image.read()

    # Write to temp file for detectors that expect a path
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    detections: list[DetectionScore] = []

    # ELA
    try:
        from ml.image.ela_detector import ELADetector
        ela = ELADetector()
        ela_result = ela.predict(tmp_path)
        detections.append(DetectionScore(
            model_name="ELA",
            score=ela_result.score,
            verdict=ela_result.verdict,
            metadata={"ela_heatmap": "available"},
        ))
    except Exception as e:
        logger.error("image.ela_failed", error=str(e), analysis_id=analysis_id)

    # DIRE
    try:
        from ml.image.dire_detector import DIREDetector
        dire = DIREDetector()
        dire_result = dire.predict(tmp_path)
        detections.append(DetectionScore(
            model_name="DIRE",
            score=dire_result.score,
            verdict=dire_result.verdict,
            metadata=dire_result.metadata,
        ))
    except Exception as e:
        logger.error("image.dire_failed", error=str(e), analysis_id=analysis_id)

    # CLIP (if caption provided)
    if caption:
        try:
            from ml.image.clip_context import CLIPContextDetector
            clip = CLIPContextDetector()
            clip_result = clip.predict(tmp_path, caption)
            detections.append(DetectionScore(
                model_name="CLIP-Context",
                score=clip_result.score,
                verdict=clip_result.verdict,
                metadata=clip_result.metadata,
            ))
        except Exception as e:
            logger.error("image.clip_failed", error=str(e), analysis_id=analysis_id)

    # Aggregate scores
    ela_score = next((d.score for d in detections if d.model_name == "ELA"), 0.0)
    dire_score = next((d.score for d in detections if d.model_name == "DIRE"), 0.0)
    clip_score = next((d.score for d in detections if d.model_name == "CLIP-Context"), 0.0)

    # Cleanup
    import os
    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    return ImageAnalysisResponse(
        analysis_id=analysis_id,
        detections=detections,
        overall_forgery_score=ela_score,
        ai_generated_score=dire_score,
        context_mismatch_score=clip_score,
    )
