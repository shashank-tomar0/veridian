"""POST /v1/analyze — submit media for misinformation analysis."""

from __future__ import annotations

import uuid

import structlog
import shutil
import tempfile
import os

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import get_current_user, require_permission
from backend.deps import get_db, get_cache
from backend.db.cache import CacheService
from backend.models.claim import AnalysisResult
from backend.services.orchestrator import orchestrator
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
):
    """Lite: Submit for cloud analysis via Orchestrator."""
    analysis_id = await orchestrator.analyze(
        media_type=body.media_type.value,
        text=body.text,
        language=body.language
    )
    return AnalyzeResponse(analysis_id=analysis_id)


@router.post("/analyze/upload", response_model=AnalyzeResponse)
async def upload_analysis(
    media_file: UploadFile = File(...),
    media_type: str = Form(...),
    text: Optional[str] = Form(None),
    language: str = Form("auto"),
    user: User = Depends(require_permission(Permission.ANALYZE)),
):
    """Premium Lite: Upload media directly and analyze via cloud orchestration."""
    # 1. Save to temp file
    suffix = os.path.splitext(media_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(media_file.file, tmp)
        file_path = tmp.name

    # 2. Dispatch to Orchestrator
    analysis_id = await orchestrator.analyze(
        media_type=media_type,
        text=text,
        file_path=file_path,
        language=language
    )

    logger.info("analysis.upload_submitted", analysis_id=analysis_id, media_type=media_type)
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

    # If completed, pull from SQL (primary for lite) or Redis (cache)
    trust_receipt = None
    if record.completed:
        # Priority 1: SQL result_json (Always available in Lite)
        if record.result_json:
            import json
            from backend.schemas.analysis import TrustReceipt
            trust_receipt = TrustReceipt(**json.loads(record.result_json))
        # Priority 2: Redis Cache (Speed)
        else:
            cached = await cache.get_cached_result(record.media_hash)
            if cached:
                from backend.schemas.analysis import TrustReceipt
                trust_receipt = TrustReceipt(**cached)

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus(record.status),
        trust_receipt=trust_receipt,
    )
