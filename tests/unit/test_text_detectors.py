"""Unit tests for ML text detectors — mock inference (no real model load)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ml.base import DetectionResult


class TestBinocularsDetector:
    """Tests for Binoculars zero-shot AI text detector."""

    def test_init_defaults(self):
        from ml.text.binoculars import BinocularsDetector

        d = BinocularsDetector()
        assert d.observer_model_id == "tiiuae/falcon-7b"
        assert d.performer_model_id == "tiiuae/falcon-7b-instruct"
        assert d._is_loaded is False

    def test_init_custom_config(self):
        from ml.text.binoculars import BinocularsDetector

        d = BinocularsDetector(config={"threshold": 0.7})
        assert d.config["threshold"] == 0.7

    @patch("ml.text.binoculars.AutoModelForCausalLM")
    @patch("ml.text.binoculars.AutoTokenizer")
    def test_predict_returns_detection_result(self, mock_tok, mock_model):
        from ml.text.binoculars import BinocularsDetector

        d = BinocularsDetector()
        d._is_loaded = True
        d.tokenizer = MagicMock()
        d.observer_model = MagicMock()
        d.performer_model = MagicMock()

        import torch

        # Mock tokenizer
        d.tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}

        # Mock model outputs
        mock_output = MagicMock()
        mock_output.loss = torch.tensor(2.0)
        d.observer_model.return_value = mock_output
        d.performer_model.return_value = mock_output

        result = d.predict("Test text for AI detection")
        assert isinstance(result, DetectionResult)
        assert 0.0 <= result.score <= 1.0


class TestMurilClassifier:
    """Tests for MuRIL semantic manipulation classifier."""

    def test_init_defaults(self):
        from ml.text.muril_classifier import MurilClassifier

        m = MurilClassifier()
        assert m.model_id == "google/muril-base-cased"
        assert m._is_loaded is False

    @patch("ml.text.muril_classifier.AutoModelForSequenceClassification")
    @patch("ml.text.muril_classifier.AutoTokenizer")
    def test_predict_returns_score(self, mock_tok, mock_model):
        import torch
        from ml.text.muril_classifier import MurilClassifier

        m = MurilClassifier()
        m._is_loaded = True
        m.tokenizer = MagicMock()
        m.model = MagicMock()
        m.device = "cpu"

        m.tokenizer.return_value = {
            "input_ids": torch.tensor([[1, 2, 3]]),
            "attention_mask": torch.tensor([[1, 1, 1]]),
        }

        mock_out = MagicMock()
        mock_out.logits = torch.tensor([[0.3, 0.7]])
        m.model.return_value = mock_out

        result = m.predict("Test manipulation text")
        assert isinstance(result, DetectionResult)
        assert result.verdict in ("MANIPULATED", "AUTHENTIC")
