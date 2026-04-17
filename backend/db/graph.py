"""Neo4j async graph service for claim provenance and campaign detection."""

from __future__ import annotations

from typing import Any

import structlog
from neo4j import AsyncGraphDatabase

from backend.config import settings

logger = structlog.get_logger()


class GraphService:
    def __init__(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self.driver.close()

    # ── Claim CRUD ───────────────────────────────────────────────────────────

    async def add_claim(self, claim_id: str, original_text: str, verdict: str | None = None) -> None:
        query = """
        MERGE (c:Claim {id: $claim_id})
        SET c.original_text = $text,
            c.verdict = $verdict,
            c.created_at = datetime()
        RETURN c
        """
        async with self.driver.session() as session:
            await session.run(query, claim_id=claim_id, text=original_text, verdict=verdict)
        logger.info("graph.add_claim", claim_id=claim_id)

    async def link_claims_by_similarity(self, claim_id_1: str, claim_id_2: str, score: float) -> None:
        query = """
        MATCH (c1:Claim {id: $id1})
        MATCH (c2:Claim {id: $id2})
        MERGE (c1)-[s:SIMILAR_TO]->(c2)
        SET s.score = $score, s.updated_at = datetime()
        """
        async with self.driver.session() as session:
            await session.run(query, id1=claim_id_1, id2=claim_id_2, score=score)

    # ── Provenance tracing ───────────────────────────────────────────────────

    async def get_claim_provenance(self, claim_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Trace the origin path of a claim through the similarity graph.

        Returns a list of connected claims ordered by relationship depth.
        """
        query = """
        MATCH path = (origin:Claim {id: $claim_id})-[:SIMILAR_TO*1..$max_depth]-(related:Claim)
        RETURN related.id AS id,
               related.original_text AS text,
               related.verdict AS verdict,
               related.created_at AS created_at,
               length(path) AS depth
        ORDER BY depth ASC
        """
        results: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            cursor = await session.run(query, claim_id=claim_id, max_depth=max_depth)
            async for record in cursor:
                results.append({
                    "id": record["id"],
                    "text": record["text"],
                    "verdict": record["verdict"],
                    "created_at": str(record["created_at"]) if record["created_at"] else None,
                    "depth": record["depth"],
                })
        logger.info("graph.provenance", claim_id=claim_id, related_count=len(results))
        return results

    # ── Campaign detection ───────────────────────────────────────────────────

    async def detect_coordinated_campaigns(
        self, min_cluster_size: int = 3, min_similarity: float = 0.7
    ) -> list[dict[str, Any]]:
        """Detect clusters of highly similar claims that may indicate coordinated campaigns.

        Uses a community-detection approach: find densely connected subgraphs
        where all edges have similarity >= min_similarity.
        """
        query = """
        MATCH (c1:Claim)-[s:SIMILAR_TO]->(c2:Claim)
        WHERE s.score >= $min_sim
        WITH c1, collect(DISTINCT c2) AS neighbors, collect(DISTINCT s.score) AS scores
        WHERE size(neighbors) >= $min_size
        RETURN c1.id AS anchor_id,
               c1.original_text AS anchor_text,
               [n IN neighbors | n.id] AS member_ids,
               [n IN neighbors | n.original_text] AS member_texts,
               scores,
               size(neighbors) AS cluster_size
        ORDER BY cluster_size DESC
        LIMIT 20
        """
        campaigns: list[dict[str, Any]] = []
        async with self.driver.session() as session:
            cursor = await session.run(query, min_sim=min_similarity, min_size=min_cluster_size)
            async for record in cursor:
                campaigns.append({
                    "anchor_id": record["anchor_id"],
                    "anchor_text": record["anchor_text"],
                    "member_ids": record["member_ids"],
                    "cluster_size": record["cluster_size"],
                    "avg_similarity": sum(record["scores"]) / len(record["scores"]) if record["scores"] else 0,
                })
        logger.info("graph.campaigns_detected", count=len(campaigns))
        return campaigns

    # ── Add source node ──────────────────────────────────────────────────────

    async def add_source(self, source_url: str, claim_id: str, credibility: float = 0.5) -> None:
        """Link a source URL to a claim node."""
        query = """
        MERGE (s:Source {url: $url})
        SET s.credibility = $cred
        WITH s
        MATCH (c:Claim {id: $claim_id})
        MERGE (c)-[:SOURCED_FROM]->(s)
        """
        async with self.driver.session() as session:
            await session.run(query, url=source_url, claim_id=claim_id, cred=credibility)


graph_service = GraphService()
