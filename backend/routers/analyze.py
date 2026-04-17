"""POST /v1/analyze — submit media for misinformation analysis."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import get_current_user, require_permission
from backend.deps import get_db, get_cache
from backend.db.cache import CacheService
from backend.models.claim import AnalysisResult
from backend.models.user import User
from backend.schemas.analysis import (
    AnalysisStatus,
    AnalysisStatusResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)
from backend.schemas.auth import Permission
from workers.tasks.analyze import analyze_media

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def submit_analysis(
    body: AnalyzeRequest,
    user: User = Depends(require_permission(Permission.ANALYZE)),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Submit media or text for asynchronous misinformation analysis.

    Returns an analysis_id immediately; poll GET /v1/analyze/{id} or register
    a callback_url for webhook delivery.
    """
    # Rate-limit check
    allowed = await cache.rate_limit_check(user.id, user.permission)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for your tier")

    analysis_id = str(uuid.uuid4())

    # Persist pending record
    record = AnalysisResult(
        id=analysis_id,
        media_hash=str(uuid.uuid4()),  # computed from actual content in prod
        media_type=body.media_type.value,
        status="pending",
    )
    db.add(record)
    await db.commit()

    # Dispatch Celery task chain
    metadata = {
        "text": body.text or "",
        "callback_url": body.callback_url,
        "user_id": user.id,
        **body.metadata,
    }
    analyze_media.delay(analysis_id, body.media_url or "", body.media_type.value, metadata)

    logger.info("analysis.submitted", analysis_id=analysis_id, media_type=body.media_type.value)

    return AnalyzeResponse(analysis_id=analysis_id)


@router.get("/analyze/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
):
    """Poll for the status / result of a submitted analysis."""
    from sqlalchemy import select

    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == analysis_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # If completed, try to pull cached Trust Receipt
    trust_receipt = None
    if record.completed:
        cached = await cache.get_cached_result(record.media_hash)
        if cached:
            from backend.schemas.analysis import TrustReceipt
            trust_receipt = TrustReceipt(**cached)

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus(record.status),
        trust_receipt=trust_receipt,
    )
