"""GET /v1/metrics — Prometheus-compatible metrics endpoint."""

from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.auth.jwt import require_permission
from backend.models.user import User
from backend.schemas.auth import Permission

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["metrics"])

# ── In-memory counters (swap for prometheus_client in prod) ──────────────────
_metrics: dict[str, float] = {
    "analyses_total": 0,
    "analyses_completed": 0,
    "analyses_failed": 0,
    "avg_processing_ms": 0.0,
    "active_workers": 0,
}


class MetricsResponse(BaseModel):
    analyses_total: float = 0
    analyses_completed: float = 0
    analyses_failed: float = 0
    avg_processing_ms: float = 0.0
    active_workers: float = 0
    uptime_seconds: float = 0.0
    cache_hit_rate: float = 0.0


_start_time = time.time()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    user: User = Depends(require_permission(Permission.ADMIN)),
):
    """Return operational metrics. Admin-only."""
    return MetricsResponse(
        **_metrics,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


def increment_metric(name: str, value: float = 1.0) -> None:
    """Utility to bump a metric counter from anywhere in the codebase."""
    if name in _metrics:
        _metrics[name] += value
