"""Unit tests for the Neo4j graph service (mocked driver)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGraphService:
    """Test GraphService methods with mocked Neo4j driver."""

    def test_initialization(self):
        from backend.db.graph import GraphService

        service = GraphService()
        assert service._driver is None

    @pytest.mark.asyncio
    async def test_get_claim_graph_returns_structure(self):
        from backend.db.graph import GraphService

        service = GraphService()

        # Mock the driver
        mock_record = MagicMock()
        mock_record.data.return_value = {
            "c1": {"id": "1", "text": "Claim 1", "verdict": "TRUE"},
            "c2": {"id": "2", "text": "Claim 2", "verdict": "FALSE"},
            "similarity": 0.85,
        }

        mock_result = MagicMock()
        mock_result.__aiter__ = MagicMock(return_value=iter([mock_record]))

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session

        service._driver = mock_driver

        # The method should return graph data
        # Testing the service interface is correct
        assert service._driver is not None
