"""Trust Receipt generation Celery task.

Assembles the final Trust Receipt from all detection and verification results,
renders a shareable card image via Pillow, and delivers it via webhook or
messaging channel.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import structlog
from celery import shared_task

logger = structlog.get_logger()


def _aggregate_verdict(verdicts: list[dict]) -> tuple[str, float]:
    """Determine overall verdict from individual claim verdicts."""
    if not verdicts:
        return "UNVERIFIABLE", 0.0

    verdict_weights = {"FALSE": 3, "MISLEADING": 2, "TRUE": 1, "UNVERIFIABLE": 0}

    max_weight = 0
    max_verdict = "UNVERIFIABLE"
    confidences: list[float] = []

    for v in verdicts:
        label = v.get("verdict", "UNVERIFIABLE").upper()
        conf = v.get("confidence", 0.0)
        confidences.append(conf)

        weight = verdict_weights.get(label, 0)
        if weight > max_weight:
            max_weight = weight
            max_verdict = label

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return max_verdict, round(avg_confidence, 3)


def _aggregate_detection_scores(results: dict | list) -> list[dict[str, Any]]:
    """Flatten detection scores from upstream task results."""
    detections: list[dict[str, Any]] = []

    items = results if isinstance(results, list) else [results]
    for item in items:
        if isinstance(item, dict):
            for det in item.get("detections", []):
                detections.append(det)
    return detections


@shared_task(
    bind=True,
    name="workers.tasks.receipt.generate_receipt",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def generate_receipt(self, verification_result: dict | None, analysis_id: str) -> dict:
    """Assemble and deliver a Trust Receipt.

    Args:
        verification_result: Output from verify_claims task.
        analysis_id: Unique analysis identifier.
    """
    start = time.perf_counter()
    logger.info("task.receipt.start", analysis_id=analysis_id)

    try:
        verdicts = []
        if isinstance(verification_result, dict):
            verdicts = verification_result.get("verdicts", [])

        overall_verdict, overall_confidence = _aggregate_verdict(verdicts)

        # Build Trust Receipt payload
        receipt: dict[str, Any] = {
            "analysis_id": analysis_id,
            "overall_verdict": overall_verdict,
            "overall_confidence": overall_confidence,
            "claim_verdicts": verdicts,
            "detection_scores": _aggregate_detection_scores(verification_result or {}),
            "status": "completed",
        }

        # ── Render card image ────────────────────────────────────────────
        try:
            from bot.formatter import formatter

            card_bytes = formatter.generate_card({
                "verdict": overall_verdict,
                "claim": verdicts[0].get("claim", "Analysis complete") if verdicts else "No claims found",
                "reasoning": verdicts[0].get("reasoning", "") if verdicts else "",
            })
            receipt["card_size_bytes"] = len(card_bytes)
            logger.info("task.receipt.card_generated", analysis_id=analysis_id, size=len(card_bytes))
        except Exception as exc:
            logger.warning("task.receipt.card_error", analysis_id=analysis_id, error=str(exc))

        # ── Cache result ─────────────────────────────────────────────────
        try:
            import asyncio
            from backend.db.cache import cache_service

            asyncio.run(cache_service.cache_analysis_result(analysis_id, receipt))
            logger.info("task.receipt.cached", analysis_id=analysis_id)
        except Exception as exc:
            logger.warning("task.receipt.cache_error", analysis_id=analysis_id, error=str(exc))

        # ── Deliver via webhook (if configured) ──────────────────────────
        # The callback_url would come from the original analysis metadata
        # stored in DB. For now, we log completion.

        duration = round((time.perf_counter() - start) * 1000, 2)
        receipt["processing_time_ms"] = duration

        logger.info(
            "task.receipt.complete",
            analysis_id=analysis_id,
            verdict=overall_verdict,
            confidence=overall_confidence,
            duration_ms=duration,
        )

        return receipt

    except Exception as exc:
        logger.error("task.receipt.error", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
