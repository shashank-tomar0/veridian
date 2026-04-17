"""Image analysis Celery task.

Runs ELA + DIRE + CLIP-context detectors and optionally performs
reverse image search and provenance tracing.
"""

from __future__ import annotations

import time

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="workers.tasks.image.analyze_image",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def analyze_image(
    self,
    analysis_id: str,
    image_path: str,
    caption: str = "",
) -> dict:
    """Run image-modality detectors.

    Pipeline:
      1. Error Level Analysis (ELA)
      2. DIRE diffusion reconstruction error
      3. CLIP out-of-context detection (if caption provided)
    """
    start = time.perf_counter()
    logger.info("task.image.start", analysis_id=analysis_id, image_path=image_path)

    results: dict = {
        "analysis_id": analysis_id,
        "modality": "image",
        "detections": [],
    }

    try:
        # ── ELA ──────────────────────────────────────────────────────────
        try:
            from ml.image.ela_detector import ELADetector

            ela = ELADetector()
            ela_result = ela.predict(image_path)
            results["detections"].append({
                "model": "ELA",
                "score": ela_result.score,
                "verdict": ela_result.verdict,
                "metadata": {k: v for k, v in ela_result.metadata.items() if k != "ela_heatmap_base64"},
            })
            logger.info("task.image.ela_done", analysis_id=analysis_id, score=ela_result.score)
        except Exception as exc:
            logger.error("task.image.ela_error", analysis_id=analysis_id, error=str(exc))

        # ── DIRE ─────────────────────────────────────────────────────────
        try:
            from ml.image.dire_detector import DIREDetector

            dire = DIREDetector()
            dire_result = dire.predict(image_path)
            results["detections"].append({
                "model": "DIRE",
                "score": dire_result.score,
                "verdict": dire_result.verdict,
                "metadata": dire_result.metadata,
            })
            logger.info("task.image.dire_done", analysis_id=analysis_id, score=dire_result.score)
        except Exception as exc:
            logger.error("task.image.dire_error", analysis_id=analysis_id, error=str(exc))

        # ── CLIP context ─────────────────────────────────────────────────
        if caption:
            try:
                from ml.image.clip_context import CLIPContextDetector

                clip = CLIPContextDetector()
                clip_result = clip.predict(image_path, caption)
                results["detections"].append({
                    "model": "CLIP-Context",
                    "score": clip_result.score,
                    "verdict": clip_result.verdict,
                    "metadata": clip_result.metadata,
                })
                logger.info("task.image.clip_done", analysis_id=analysis_id, score=clip_result.score)
            except Exception as exc:
                logger.error("task.image.clip_error", analysis_id=analysis_id, error=str(exc))

    except Exception as exc:
        logger.error("task.image.fatal", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    duration = round((time.perf_counter() - start) * 1000, 2)
    results["processing_time_ms"] = duration
    logger.info("task.image.complete", analysis_id=analysis_id, duration_ms=duration)

    return results
