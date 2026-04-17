"""Master analysis task — dispatches modality-specific Celery chains."""

from __future__ import annotations

import structlog
from celery import chain, group, shared_task

from workers.celery_app import celery_app

logger = structlog.get_logger()


@shared_task(
    bind=True,
    name="workers.tasks.analyze.analyze_media",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def analyze_media(
    self,
    analysis_id: str,
    media_url: str,
    media_type: str,
    metadata: dict,
) -> dict:
    """Master orchestration task.

    Reads the media artifact, determines modality, and dispatches the
    appropriate Celery task chain (parallel detectors → verification → receipt).
    """
    logger.info(
        "analyze_media.start",
        analysis_id=analysis_id,
        media_type=media_type,
        task_id=self.request.id,
    )

    from workers.tasks.text import analyze_text
    from workers.tasks.image import analyze_image
    from workers.tasks.audio import analyze_audio
    from workers.tasks.video import analyze_video
    from workers.tasks.verify import verify_claims
    from workers.tasks.receipt import generate_receipt

    try:
        if media_type == "text":
            text_content = metadata.get("text", "")
            return chain(
                analyze_text.s(analysis_id, text_content, metadata.get("language", "auto")),
                verify_claims.s(analysis_id),
                generate_receipt.s(analysis_id),
            ).apply_async().id

        elif media_type == "image":
            # In production: download from media_url (MinIO) to temp path
            image_path = metadata.get("local_path", "temp/image_to_analyze.jpg")
            text_content = metadata.get("caption", metadata.get("text", ""))

            parallel = group(
                analyze_image.s(analysis_id, image_path, text_content),
                analyze_text.s(analysis_id, text_content, "auto"),
            )
            return chain(
                parallel,
                verify_claims.s(analysis_id),
                generate_receipt.s(analysis_id),
            ).apply_async().id

        elif media_type == "audio":
            audio_path = metadata.get("local_path", "temp/audio_to_analyze.wav")
            return chain(
                analyze_audio.s(analysis_id, audio_path),
                verify_claims.s(analysis_id),
                generate_receipt.s(analysis_id),
            ).apply_async().id

        elif media_type == "video":
            video_path = metadata.get("local_path", "temp/video_to_analyze.mp4")
            return chain(
                analyze_video.s(analysis_id, video_path),
                verify_claims.s(analysis_id),
                generate_receipt.s(analysis_id),
            ).apply_async().id

        else:
            logger.warning("analyze_media.unsupported", analysis_id=analysis_id, media_type=media_type)
            return {"status": "failed", "reason": f"Unsupported media type: {media_type}"}

    except Exception as exc:
        logger.error("analyze_media.error", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
