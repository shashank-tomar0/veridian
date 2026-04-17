"""Unit tests for ML image detectors."""

from __future__ import annotations

import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from ml.base import DetectionResult


@pytest.fixture
def sample_image_path():
    """Create a temporary test image."""
    img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    img.save(path, "JPEG")
    yield path
    os.unlink(path)


class TestELADetector:
    def test_predict_returns_result(self, sample_image_path):
        from ml.image.ela_detector import ELADetector

        d = ELADetector()
        result = d.predict(sample_image_path)
        assert isinstance(result, DetectionResult)
        assert 0.0 <= result.score <= 1.0
        assert "ela_heatmap_base64" in result.metadata

    def test_init_already_loaded(self):
        from ml.image.ela_detector import ELADetector

        d = ELADetector()
        assert d._is_loaded is True  # ELA has no model weights


class TestDIREDetector:
    def test_init_defaults(self):
        from ml.image.dire_detector import DIREDetector

        d = DIREDetector()
        assert d.model_id == "lsml/DIRE"
        assert d._is_loaded is False

    def test_predict_with_fallback(self, sample_image_path):
        from ml.image.dire_detector import DIREDetector

        d = DIREDetector()
        result = d.predict(sample_image_path)
        assert isinstance(result, DetectionResult)
        assert result.verdict in ("AI_GENERATED", "LIKELY_REAL")


class TestCLIPContextDetector:
    def test_init_defaults(self):
        from ml.image.clip_context import CLIPContextDetector

        d = CLIPContextDetector()
        assert d.model_id == "openai/clip-vit-large-patch14"
        assert d._is_loaded is False
