"""Unit tests for backend schemas and auth."""

from __future__ import annotations

import pytest

from backend.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    DetectionScore,
    MediaType,
    TrustReceipt,
    VerdictLabel,
)
from backend.schemas.auth import Permission, TokenRequest, UserCreate
from backend.schemas.claims import ClaimFilter, ClaimListResponse


class TestAnalysisSchemas:
    def test_analyze_request_text(self):
        req = AnalyzeRequest(text="Test claim", media_type=MediaType.TEXT)
        assert req.media_type == MediaType.TEXT
        assert req.language == "auto"

    def test_analyze_request_requires_media_type(self):
        with pytest.raises(Exception):
            AnalyzeRequest(text="Test")  # missing media_type

    def test_analyze_response_defaults(self):
        resp = AnalyzeResponse()
        assert resp.status.value == "pending"
        assert resp.analysis_id  # auto-generated UUID

    def test_detection_score_bounds(self):
        ds = DetectionScore(model_name="test", score=0.5)
        assert ds.score == 0.5

        with pytest.raises(Exception):
            DetectionScore(model_name="test", score=1.5)  # out of bounds

    def test_trust_receipt_structure(self):
        tr = TrustReceipt(analysis_id="test-123")
        assert tr.overall_verdict == VerdictLabel.UNVERIFIABLE
        assert tr.detection_scores == []


class TestAuthSchemas:
    def test_token_request_password_min_length(self):
        with pytest.raises(Exception):
            TokenRequest(email="test@example.com", password="short")  # < 8 chars

    def test_user_create_defaults(self):
        u = UserCreate(
            email="test@example.com",
            password="longpassword",
            full_name="Test User",
        )
        assert u.permission == Permission.READ


class TestClaimsSchemas:
    def test_claim_filter_defaults(self):
        f = ClaimFilter()
        assert f.page == 1
        assert f.page_size == 20

    def test_claim_list_response(self):
        r = ClaimListResponse(claims=[], total_count=0, page=1, page_size=20, has_next=False)
        assert r.total_count == 0
