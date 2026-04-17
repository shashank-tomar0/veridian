"""Shared FastAPI dependency-injection providers."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.cache import cache_service
from backend.db.graph import graph_service
from backend.db.qdrant import qdrant_service
from backend.models.base import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, auto-closing on exit."""
    async with AsyncSessionLocal() as session:
        yield session


def get_cache():
    """Return the singleton Redis cache service."""
    return cache_service


def get_graph():
    """Return the singleton Neo4j graph service."""
    return graph_service


def get_qdrant():
    """Return the singleton Qdrant vector service."""
    return qdrant_service
