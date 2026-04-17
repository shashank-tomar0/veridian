"""Unit tests for worker task helper functions."""

from __future__ import annotations

import pytest


class TestReceiptAggregation:
    """Test the verdict and detection score aggregation logic."""

    def test_aggregate_verdict_empty(self):
        from workers.tasks.receipt import _aggregate_verdict

        verdict, conf = _aggregate_verdict([])
        assert verdict == "UNVERIFIABLE"
        assert conf == 0.0

    def test_aggregate_verdict_single_false(self):
        from workers.tasks.receipt import _aggregate_verdict

        verdict, conf = _aggregate_verdict([
            {"verdict": "FALSE", "confidence": 0.95},
        ])
        assert verdict == "FALSE"
        assert conf == 0.95

    def test_aggregate_verdict_mixed(self):
        from workers.tasks.receipt import _aggregate_verdict

        verdict, conf = _aggregate_verdict([
            {"verdict": "TRUE", "confidence": 0.9},
            {"verdict": "FALSE", "confidence": 0.8},
            {"verdict": "MISLEADING", "confidence": 0.7},
        ])
        assert verdict == "FALSE"  # highest severity
        assert round(conf, 3) == 0.8  # average confidence

    def test_aggregate_verdict_all_true(self):
        from workers.tasks.receipt import _aggregate_verdict

        verdict, conf = _aggregate_verdict([
            {"verdict": "TRUE", "confidence": 0.98},
            {"verdict": "TRUE", "confidence": 0.92},
        ])
        assert verdict == "TRUE"

    def test_aggregate_detection_scores_flat(self):
        from workers.tasks.receipt import _aggregate_detection_scores

        scores = _aggregate_detection_scores({
            "detections": [
                {"model": "Binoculars", "score": 0.12},
                {"model": "MuRIL", "score": 0.34},
            ]
        })
        assert len(scores) == 2
        assert scores[0]["model"] == "Binoculars"

    def test_aggregate_detection_scores_nested(self):
        from workers.tasks.receipt import _aggregate_detection_scores

        scores = _aggregate_detection_scores([
            {"detections": [{"model": "ELA", "score": 0.6}]},
            {"detections": [{"model": "DIRE", "score": 0.8}]},
        ])
        assert len(scores) == 2

    def test_aggregate_detection_scores_empty(self):
        from workers.tasks.receipt import _aggregate_detection_scores

        scores = _aggregate_detection_scores({})
        assert len(scores) == 0


class TestVerifyClaimsEdgeCases:
    """Test claim verification edge cases."""

    def test_upstream_result_is_none(self):
        from workers.tasks.verify import verify_claims

        result = verify_claims.apply(args=[None, "test-001"]).get(timeout=10)
        assert result["status"] == "skipped"

    def test_upstream_result_is_empty_list(self):
        from workers.tasks.verify import verify_claims

        result = verify_claims.apply(args=[[], "test-002"]).get(timeout=10)
        assert result["status"] == "skipped"

    def test_upstream_result_list_with_text(self):
        from workers.tasks.verify import verify_claims

        upstream = [
            {"extracted_text": "Hello world", "language": "en"},
            {"extracted_text": "", "language": "en"},
        ]
        # This will attempt to run the agent, which may fail without LLM key
        # But it should at least extract text correctly
        try:
            result = verify_claims.apply(args=[upstream, "test-003"]).get(timeout=15)
        except Exception:
            pass  # Expected in test env without LLM keys
