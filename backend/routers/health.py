"""GET /v1/health — health and readiness probes."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "veridian-core"
    version: str = "0.1.0"
    timestamp: str = ""


class ReadinessResponse(BaseModel):
    status: str = "ok"
    postgres: str = "unknown"
    redis: str = "unknown"
    qdrant: str = "unknown"


@router.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe — always returns OK if the process is running."""
    return HealthResponse(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/v1/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness probe — verifies downstream dependencies."""
    status_map: dict[str, str] = {}

    # Redis
    try:
        from backend.db.cache import cache_service
        await cache_service.redis.ping()
        status_map["redis"] = "ok"
    except Exception:
        status_map["redis"] = "unavailable"

    # Postgres
    try:
        from backend.models.base import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status_map["postgres"] = "ok"
    except Exception:
        status_map["postgres"] = "unavailable"

    # Qdrant
    try:
        from backend.db.qdrant import qdrant_service
        await qdrant_service.client.get_collections()
        status_map["qdrant"] = "ok"
    except Exception:
        status_map["qdrant"] = "unavailable"

    overall = "ok" if all(v == "ok" for v in status_map.values()) else "degraded"

    return ReadinessResponse(status=overall, **status_map)
