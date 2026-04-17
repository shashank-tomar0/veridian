"""Global pytest fixtures for the Veridian test suite."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    """Set safe default env vars for all tests."""
    defaults = {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/15",
        "CELERY_BROKER_URL": "redis://localhost:6379/14",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/13",
        "QDRANT_URL": "http://localhost:6333",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "test",
        "JWT_SECRET_KEY": "test-secret-key-for-unit-tests-only",
        "JWT_ALGORITHM": "HS256",
        "ANTHROPIC_API_KEY": "test-key",
        "TAVILY_API_KEY": "test-key",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
    }
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.incr.return_value = 1
    mock.expire.return_value = True
    return mock


@pytest.fixture
def mock_db_session():
    """Mock async SQLAlchemy session."""
    session = MagicMock()
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def sample_text():
    """Sample misinformation text for testing."""
    return "The government has announced that all electricity will be free starting next month for every citizen."


@pytest.fixture
def sample_analysis_id():
    """Standard test analysis ID."""
    return "test-550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_trust_receipt():
    """Complete trust receipt fixture for testing."""
    return {
        "analysis_id": "test-550e8400",
        "overall_verdict": "FALSE",
        "overall_confidence": 0.94,
        "claim_verdicts": [
            {
                "claim": "Free electricity for all citizens",
                "verdict": "FALSE",
                "confidence": 0.94,
                "reasoning": "No official source confirms this claim.",
            },
        ],
        "detection_scores": [
            {"model": "Binoculars", "score": 0.12, "verdict": "HUMAN_WRITTEN"},
            {"model": "MuRIL", "score": 0.34, "verdict": "AUTHENTIC"},
        ],
        "status": "completed",
    }
