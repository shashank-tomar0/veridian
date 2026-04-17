"""Integration tests for the analysis pipeline using test fixtures."""

from __future__ import annotations

import pytest


class TestAnalysisPipeline:
    """Integration tests for the full Celery task chain.

    These tests use mock brokers and test fixtures.
    Real model inference is disabled in CI.
    """

    def test_text_analysis_task_returns_result(self):
        """Verify text analysis returns well-formed result dict."""
        from workers.tasks.text import analyze_text

        result = analyze_text.apply(
            args=["test-analysis-001", "The earth is flat.", "en"]
        ).get(timeout=30)

        assert result["analysis_id"] == "test-analysis-001"
        assert result["modality"] == "text"
        assert "detections" in result

    def test_verify_claims_skips_empty_text(self):
        """Verify claims task handles empty text gracefully."""
        from workers.tasks.verify import verify_claims

        upstream = {"extracted_text": "", "language": "en"}
        result = verify_claims.apply(args=[upstream, "test-verify-001"]).get(timeout=10)

        assert result["status"] == "skipped"

    def test_receipt_generation_with_no_verdicts(self):
        """Trust receipt handles empty verdict list."""
        from workers.tasks.receipt import generate_receipt

        result = generate_receipt.apply(args=[{"verdicts": []}, "test-receipt-001"]).get(timeout=10)

        assert result["overall_verdict"] == "UNVERIFIABLE"
        assert result["status"] == "completed"

    def test_receipt_generation_with_false_verdict(self):
        """Trust receipt correctly identifies FALSE as dominant verdict."""
        from workers.tasks.receipt import generate_receipt

        verification = {
            "verdicts": [
                {"claim": "X is Y", "verdict": "FALSE", "confidence": 0.9, "reasoning": "Evidence contradicts"},
                {"claim": "A is B", "verdict": "TRUE", "confidence": 0.8, "reasoning": "Evidence supports"},
            ]
        }
        result = generate_receipt.apply(args=[verification, "test-receipt-002"]).get(timeout=10)

        assert result["overall_verdict"] == "FALSE"
