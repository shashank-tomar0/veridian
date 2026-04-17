"""Claim verification Celery task.

Invokes the LangGraph verification agent to extract claims, score
checkworthiness, retrieve evidence, and produce verdicts.
"""

from __future__ import annotations

import asyncio
import time

import structlog
from celery import shared_task

logger = structlog.get_logger()


def _run_async(coro):
    """Run an async coroutine from synchronous Celery context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(
    bind=True,
    name="workers.tasks.verify.verify_claims",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def verify_claims(self, upstream_result: dict | list | None, analysis_id: str) -> dict:
    """Run the LangGraph verification agent on extracted text / claims.

    Args:
        upstream_result: The result dict from an upstream task (text analysis),
            or a list of results from a group. Contains extracted_text and language.
        analysis_id: Unique analysis identifier.
    """
    start = time.perf_counter()
    logger.info("task.verify.start", analysis_id=analysis_id)

    # Normalise upstream result (could be a single dict or list from group)
    text = ""
    language = "auto"

    if isinstance(upstream_result, list):
        for r in upstream_result:
            if isinstance(r, dict):
                text += r.get("extracted_text", "") + " "
                language = r.get("language", language)
    elif isinstance(upstream_result, dict):
        text = upstream_result.get("extracted_text", "")
        language = upstream_result.get("language", "auto")

    text = text.strip()

    if not text:
        logger.warning("task.verify.no_text", analysis_id=analysis_id)
        return {
            "analysis_id": analysis_id,
            "verdicts": [],
            "status": "skipped",
            "reason": "No text content to verify",
        }

    try:
        from workers.verification.agent import VerificationAgent

        agent = VerificationAgent()

        initial_state = {
            "analysis_id": analysis_id,
            "transcribed_text": text,
            "language": language,
            "extracted_claims": [],
            "current_claim_index": 0,
            "verdicts": [],
        }

        final_state = _run_async(agent.workflow.ainvoke(initial_state))

        verdicts = final_state.get("verdicts", [])

        logger.info(
            "task.verify.complete",
            analysis_id=analysis_id,
            claims_verified=len(verdicts),
        )

        return {
            "analysis_id": analysis_id,
            "verdicts": verdicts,
            "claims_count": len(final_state.get("extracted_claims", [])),
            "status": "completed",
        }

    except Exception as exc:
        logger.error("task.verify.error", analysis_id=analysis_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        duration = round((time.perf_counter() - start) * 1000, 2)
        logger.info("task.verify.duration", analysis_id=analysis_id, duration_ms=duration)
