"""Veridian API — FastAPI entrypoint.

Production-grade async API with structured logging, JWT auth,
request-ID tracing, and modular router composition.
"""

from __future__ import annotations

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.qdrant import qdrant_service
from backend.db.graph import graph_service
from backend.db.cache import cache_service
from backend.middleware.request_id import RequestIdMiddleware

# ── Routers ──────────────────────────────────────────────────────────────────
from backend.routers import (
    analyze,
    auth,
    claims,
    health,
    image,
    metrics,
    voiceprint,
    webhooks,
    dashboard,
    receipts,
)

logger = structlog.get_logger()


# ── Structured logging configuration ────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


# ── Application lifespan ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hooks."""
    try:
        await qdrant_service.initialize_collections()
        logger.info("application_startup", message="Veridian API started with Qdrant clusters")
    except Exception as e:
        logger.warning("application_startup_warning", message=f"Qdrant not available: {e}. Fact-checking Layer 7 will be disabled, but SQLite reports remain accessible.")
    
    yield
    
    try:
        await cache_service.close()
        await graph_service.close()
    except Exception:
        pass
    logger.info("application_shutdown", message="Veridian API stopped")


# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Veridian Misinformation Response Engine",
    description="AI-native multimodal misinformation detection and counter-narrative platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware stack (order matters: outermost = first executed) ─────────────
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(claims.router)
app.include_router(voiceprint.router)
app.include_router(image.router)
app.include_router(metrics.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(receipts.router)
