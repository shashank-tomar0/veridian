"""Data ingestion script — loads fact-checking corpus into Qdrant.

Usage:
    python -m scripts.ingest_corpus --source <path_or_url> --collection fact_corpus
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
import uuid
from pathlib import Path

import structlog

logger = structlog.get_logger()


async def ingest_csv(filepath: str, collection: str) -> int:
    """Read a CSV fact corpus and upsert embeddings into Qdrant."""
    from qdrant_client.http.models import PointStruct
    from backend.db.qdrant import qdrant_service

    rows_ingested = 0

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        batch: list[PointStruct] = []
        for row in reader:
            text = row.get("text") or row.get("claim") or row.get("content", "")
            if not text:
                continue

            # Generate a placeholder embedding (in production: use sentence-transformers)
            import hashlib

            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            import numpy as np

            rng = np.random.RandomState(seed)
            embedding = rng.randn(1024).tolist()

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "source": row.get("source", ""),
                    "label": row.get("label", ""),
                    "language": row.get("language", "en"),
                },
            )
            batch.append(point)

            if len(batch) >= 100:
                await qdrant_service.client.upsert(
                    collection_name=collection,
                    points=batch,
                )
                rows_ingested += len(batch)
                logger.info("ingest.batch", count=rows_ingested, collection=collection)
                batch = []

        # Flush remaining
        if batch:
            await qdrant_service.client.upsert(
                collection_name=collection,
                points=batch,
            )
            rows_ingested += len(batch)

    return rows_ingested


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest fact corpus into Qdrant")
    parser.add_argument("--source", required=True, help="Path to CSV file")
    parser.add_argument("--collection", default="fact_corpus", help="Qdrant collection name")
    args = parser.parse_args()

    if not Path(args.source).exists():
        logger.error("file_not_found", path=args.source)
        sys.exit(1)

    from backend.db.qdrant import qdrant_service

    await qdrant_service.initialize_collections()
    count = await ingest_csv(args.source, args.collection)
    logger.info("ingest.complete", total_rows=count, collection=args.collection)


if __name__ == "__main__":
    asyncio.run(main())
