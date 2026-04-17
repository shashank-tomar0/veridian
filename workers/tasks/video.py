"""Video analysis Celery task.

Decomposes video into frames + audio, then runs FaceForensics++ deepfake
detection, temporal consistency analysis, SyncNet lip-sync verification,
and pipes the extracted audio through the audio analysis task.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time

import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="workers.tasks.video.analyze_video",
    max_retries=3,
    default_retry_delay=120,
    acks_late=True,
)
def analyze_video(self, analysis_id: str, video_path: str) -> dict:
    """Run video-modality detectors.

    Pipeline:
      1. Extract audio track via ffmpeg
      2. FaceForensics++ deepfake detection
      3. Temporal consistency analysis
      4. SyncNet lip-sync verification
      5. Audio analysis on extracted track
    """
    start = time.perf_counter()
    logger.info("task.video.start", analysis_id=analysis_id, video_path=video_path)

    results: dict = {
        "analysis_id": analysis_id,
        "modality": "video",
        "detections": [],
        "audio_results": None,
    }

    # ── Extract audio track ──────────────────────────────────────────────
    audio_path = None
    try:
        audio_fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(audio_fd)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-ar", "16000", "-ac", "1", "-vn",
                audio_path,
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )
        logger.info("task.video.audio_extracted", analysis_id=analysis_id, audio_path=audio_path)
    except Exception as exc:
        logger.warning("task.video.audio_extraction_failed", analysis_id=analysis_id, error=str(exc))
        audio_path = None

    try:
        # ── FaceForensics++ ──────────────────────────────────────────────
        try:
            from ml.video.faceforensics import FaceForensicsDetector

            ff = FaceForensicsDetector()
            ff_result = ff.predict(video_path)
            results["detections"].append({
                "model": "FaceForensics++",
                "score": ff_result.score,
                "verdict": ff_result.verdict,
                "metadata": ff_result.metadata,
            })
            logger.info("task.video.faceforensics_done", analysis_id=analysis_id, score=ff_result.score)
        except Exception as exc:
            logger.error("task.video.faceforensics_error", analysis_id=analysis_id, error=str(exc))

        # ── Temporal consistency ─────────────────────────────────────────
        try:
            from ml.video.temporal import TemporalConsistencyDetector

            temp = TemporalConsistencyDetector()
            temp_result = temp.predict(video_path)
            results["detections"].append({
                "model": "TemporalConsistency",
                "score": temp_result.score,
                "verdict": temp_result.verdict,
                "metadata": temp_result.metadata,
            })
            logger.info("task.video.temporal_done", analysis_id=analysis_id, score=temp_result.score)
        except Exception as exc:
            logger.error("task.video.temporal_error", analysis_id=analysis_id, error=str(exc))

        # ── SyncNet ──────────────────────────────────────────────────────
        try:
            from ml.video.syncsnet import SyncNetDetector

            sync = SyncNetDetector()
            sync_result = sync.predict(video_path)
            results["detections"].append({
                "model": "SyncNet",
                "score": sync_result.score,
                "verdict": sync_result.verdict,
                "metadata": sync_result.metadata,
            })
            logger.info("task.video.syncnet_done", analysis_id=analysis_id, score=sync_result.score)
        except Exception as exc:
            logger.error("task.video.syncnet_error", analysis_id=analysis_id, error=str(exc))

        # ── Audio sub-analysis ───────────────────────────────────────────
        if audio_path and os.path.exists(audio_path):
            try:
                from workers.tasks.audio import analyze_audio

                results["audio_results"] = analyze_audio(analysis_id, audio_path)
            except Exception as exc:
                logger.error("task.video.audio_analysis_error", analysis_id=analysis_id, error=str(exc))

    except Exception as exc:
        logger.error("task.video.fatal", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))
    finally:
        # Cleanup temp audio
        if audio_path:
            try:
                os.unlink(audio_path)
            except OSError:
                pass

    duration = round((time.perf_counter() - start) * 1000, 2)
    results["processing_time_ms"] = duration
    logger.info("task.video.complete", analysis_id=analysis_id, duration_ms=duration)

    return results
