"""Audio analysis Celery task.

Runs RawNet2 spoof detection + Resemblyzer speaker verification +
Whisper transcription.
"""

from __future__ import annotations

import time

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="workers.tasks.audio.analyze_audio",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def analyze_audio(self, analysis_id: str, audio_path: str) -> dict:
    """Run audio-modality detectors.

    Pipeline:
      1. RawNet2 voice spoof detection
      2. Resemblyzer speaker identity verification
      3. Whisper transcription (for downstream claim extraction)
    """
    start = time.perf_counter()
    logger.info("task.audio.start", analysis_id=analysis_id, audio_path=audio_path)

    results: dict = {
        "analysis_id": analysis_id,
        "modality": "audio",
        "detections": [],
        "transcription": "",
    }

    try:
        # ── RawNet2 ──────────────────────────────────────────────────────
        try:
            from ml.audio.rawnet2 import RawNet2Detector

            rawnet = RawNet2Detector()
            rawnet_result = rawnet.predict(audio_path)
            results["detections"].append({
                "model": "RawNet2",
                "score": rawnet_result.score,
                "verdict": rawnet_result.verdict,
                "metadata": rawnet_result.metadata,
            })
            logger.info("task.audio.rawnet2_done", analysis_id=analysis_id, score=rawnet_result.score)
        except Exception as exc:
            logger.error("task.audio.rawnet2_error", analysis_id=analysis_id, error=str(exc))

        # ── Resemblyzer ──────────────────────────────────────────────────
        try:
            from ml.audio.resemblyzer import ResemblyzerDetector

            resemblyzer = ResemblyzerDetector()
            resemblyzer_result = resemblyzer.predict(audio_path)
            results["detections"].append({
                "model": "Resemblyzer",
                "score": resemblyzer_result.score,
                "verdict": resemblyzer_result.verdict,
                "metadata": resemblyzer_result.metadata,
            })
            logger.info(
                "task.audio.resemblyzer_done",
                analysis_id=analysis_id,
                speaker_match=resemblyzer_result.metadata.get("speaker_match"),
            )
        except Exception as exc:
            logger.error("task.audio.resemblyzer_error", analysis_id=analysis_id, error=str(exc))

        # ── Whisper transcription ────────────────────────────────────────
        try:
            import whisper

            model = whisper.load_model("base")
            transcript = model.transcribe(audio_path)
            results["transcription"] = transcript.get("text", "")
            results["language"] = transcript.get("language", "unknown")
            logger.info(
                "task.audio.whisper_done",
                analysis_id=analysis_id,
                transcript_len=len(results["transcription"]),
            )
        except ImportError:
            logger.warning("task.audio.whisper_not_available", analysis_id=analysis_id)
        except Exception as exc:
            logger.error("task.audio.whisper_error", analysis_id=analysis_id, error=str(exc))

    except Exception as exc:
        logger.error("task.audio.fatal", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    duration = round((time.perf_counter() - start) * 1000, 2)
    results["processing_time_ms"] = duration
    logger.info("task.audio.complete", analysis_id=analysis_id, duration_ms=duration)

    return results
