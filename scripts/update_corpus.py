"""Corpus update script — refreshes the Qdrant fact corpus from external APIs.

Usage:
    python -m scripts.update_corpus --source google_factcheck
"""

from __future__ import annotations

import argparse
import asyncio

import httpx
import structlog

logger = structlog.get_logger()


async def fetch_google_factcheck(query: str = "latest", max_results: int = 100) -> list[dict]:
    """Fetch claims from Google Fact Check Tools API."""
    results: list[dict] = []
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"query": query, "pageSize": min(max_results, 100)})
        if resp.status_code == 200:
            data = resp.json()
            for claim in data.get("claims", []):
                results.append({
                    "text": claim.get("text", ""),
                    "claimant": claim.get("claimant", ""),
                    "source": claim.get("claimReview", [{}])[0].get("url", "") if claim.get("claimReview") else "",
                    "rating": claim.get("claimReview", [{}])[0].get("textualRating", "") if claim.get("claimReview") else "",
                })
        else:
            logger.warning("factcheck_api.error", status=resp.status_code)

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Update fact corpus")
    parser.add_argument("--source", default="google_factcheck", choices=["google_factcheck"])
    parser.add_argument("--query", default="latest")
    args = parser.parse_args()

    claims = await fetch_google_factcheck(args.query)
    logger.info("corpus_update.fetched", count=len(claims), source=args.source)

    # In production, this would upsert embeddings into Qdrant
    # For now, log the count
    for claim in claims[:5]:
        logger.info("corpus_update.sample", text=claim.get("text", "")[:100])


if __name__ == "__main__":
    asyncio.run(main())
