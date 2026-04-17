"""GET /v1/claims — paginated claim browser with filters."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import get_current_user
from backend.deps import get_db
from backend.models.claim import Claim
from backend.models.user import User
from backend.schemas.analysis import VerdictLabel
from backend.schemas.claims import (
    ClaimFilter,
    ClaimGraphEdge,
    ClaimGraphNode,
    ClaimGraphResponse,
    ClaimListResponse,
    ClaimResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/v1", tags=["claims"])


@router.get("/claims", response_model=ClaimListResponse)
async def list_claims(
    language: str | None = None,
    verdict: VerdictLabel | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search_query: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated claim browser with optional filters."""
    stmt = select(Claim)

    if language:
        stmt = stmt.where(Claim.language == language)
    if verdict:
        stmt = stmt.where(Claim.verdict == verdict.value)
    if search_query:
        stmt = stmt.where(Claim.original_text.ilike(f"%{search_query}%"))

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    claims = [
        ClaimResponse(
            id=c.id,
            original_text=c.original_text,
            language=c.language,
            checkworthiness_score=c.checkworthiness_score,
            verdict=VerdictLabel(c.verdict) if c.verdict else None,
            confidence=c.confidence,
            reasoning=c.reasoning,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in rows
    ]

    return ClaimListResponse(
        claims=claims,
        total_count=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/claims/graph", response_model=ClaimGraphResponse)
async def get_claims_graph(
    limit: int = Query(50, ge=5, le=200),
    user: User = Depends(get_current_user),
):
    """Return the claim relationship subgraph for D3.js visualisation."""
    from backend.db.graph import graph_service

    nodes: list[ClaimGraphNode] = []
    edges: list[ClaimGraphEdge] = []

    async with graph_service.driver.session() as session:
        # Fetch claim nodes
        node_result = await session.run(
            "MATCH (c:Claim) RETURN c.id AS id, c.original_text AS text, "
            "c.verdict AS verdict LIMIT $limit",
            limit=limit,
        )
        async for record in node_result:
            nodes.append(ClaimGraphNode(
                id=record["id"],
                label=record["text"][:80] if record["text"] else "",
                verdict=VerdictLabel(record["verdict"]) if record["verdict"] else None,
            ))

        # Fetch similarity edges
        edge_result = await session.run(
            "MATCH (c1:Claim)-[s:SIMILAR_TO]->(c2:Claim) "
            "RETURN c1.id AS src, c2.id AS tgt, s.score AS score LIMIT $limit",
            limit=limit * 2,
        )
        async for record in edge_result:
            edges.append(ClaimGraphEdge(
                source=record["src"],
                target=record["tgt"],
                similarity_score=record["score"],
            ))

    return ClaimGraphResponse(nodes=nodes, edges=edges)
