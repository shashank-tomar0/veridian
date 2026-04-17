"""Unit tests for audio and video ML modules."""

from __future__ import annotations

import io
import struct
import wave

import numpy as np
import pytest

from ml.base import DetectionResult


@pytest.fixture
def sample_wav_bytes():
    """Generate a 1-second 16kHz mono WAV in memory."""
    sample_rate = 16000
    duration = 1.0
    samples = (np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration))) * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestRawNet2Detector:
    def test_init(self):
        from ml.audio.rawnet2 import RawNet2Detector

        d = RawNet2Detector()
        assert d._is_loaded is False
        assert d.sample_rate == 16000

    def test_predict_from_bytes(self, sample_wav_bytes):
        from ml.audio.rawnet2 import RawNet2Detector

        d = RawNet2Detector()
        result = d.predict(sample_wav_bytes)
        assert isinstance(result, DetectionResult)
        assert 0.0 <= result.score <= 1.0
        assert result.verdict in ("SPOOFED", "GENUINE")


class TestResemblyzerDetector:
    def test_init(self):
        from ml.audio.resemblyzer import ResemblyzerDetector

        d = ResemblyzerDetector()
        assert d.embedding_dim == 256

    def test_predict_unknown_speaker(self, sample_wav_bytes):
        from ml.audio.resemblyzer import ResemblyzerDetector

        d = ResemblyzerDetector()
        result = d.predict(sample_wav_bytes)
        assert isinstance(result, DetectionResult)
        assert result.verdict == "SPEAKER_UNKNOWN"

    def test_enroll_and_match(self, sample_wav_bytes):
        from ml.audio.resemblyzer import ResemblyzerDetector

        d = ResemblyzerDetector()
        d.enroll("TestUser", sample_wav_bytes)
        result = d.predict(sample_wav_bytes)
        assert result.metadata.get("speaker_match") is True


class TestTemporalConsistencyDetector:
    def test_init(self):
        from ml.video.temporal import TemporalConsistencyDetector

        d = TemporalConsistencyDetector()
        assert d._is_loaded is True

    def test_predict_no_video(self):
        from ml.video.temporal import TemporalConsistencyDetector

        d = TemporalConsistencyDetector()
        result = d.predict("nonexistent_video.mp4")
        assert isinstance(result, DetectionResult)
        assert result.score == 0.0
