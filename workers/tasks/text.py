"""Text analysis Celery task.

Runs Binoculars AI-text detection + MuRIL semantic manipulation classifier
and returns combined detection results.
"""

from __future__ import annotations

import time

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="workers.tasks.text.analyze_text",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def analyze_text(self, analysis_id: str, text: str, language: str = "auto") -> dict:
    """Run text-modality detectors on the provided text.

    Pipeline:
      1. Binoculars zero-shot AI text detection
      2. MuRIL semantic manipulation classification
    """
    start = time.perf_counter()
    logger.info("task.text.start", analysis_id=analysis_id, text_len=len(text), language=language)

    results: dict = {
        "analysis_id": analysis_id,
        "modality": "text",
        "detections": [],
        "extracted_text": text,
        "language": language,
    }

    try:
        # ── Binoculars ───────────────────────────────────────────────────
        try:
            from ml.text.binoculars import BinocularsDetector

            bino = BinocularsDetector()
            bino_result = bino.predict(text)
            results["detections"].append({
                "model": "Binoculars",
                "score": bino_result.score,
                "verdict": bino_result.verdict,
                "metadata": bino_result.metadata,
            })
            logger.info("task.text.binoculars_done", analysis_id=analysis_id, score=bino_result.score)
        except Exception as exc:
            logger.error("task.text.binoculars_error", analysis_id=analysis_id, error=str(exc))

        # ── MuRIL ────────────────────────────────────────────────────────
        try:
            from ml.text.muril_classifier import MurilClassifier

            muril = MurilClassifier()
            muril_result = muril.predict(text)
            results["detections"].append({
                "model": "MuRIL",
                "score": muril_result.score,
                "verdict": muril_result.verdict,
                "metadata": muril_result.metadata,
            })
            logger.info("task.text.muril_done", analysis_id=analysis_id, score=muril_result.score)
        except Exception as exc:
            logger.error("task.text.muril_error", analysis_id=analysis_id, error=str(exc))

    except Exception as exc:
        logger.error("task.text.fatal", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    duration = round((time.perf_counter() - start) * 1000, 2)
    results["processing_time_ms"] = duration
    logger.info("task.text.complete", analysis_id=analysis_id, duration_ms=duration)

    return results
