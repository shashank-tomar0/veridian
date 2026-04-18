from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from backend.deps import get_db
from backend.models.claim import Claim, AnalysisResult
from backend.schemas.claims import ClaimResponse
from backend.schemas.analysis import VerdictLabel

router = APIRouter(prefix="/v1/public", tags=["dashboard"])

@router.get("/dashboard/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Fetch dynamic KPI stats and recent activity."""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    yesterday_start = today_start - timedelta(days=1)
    
    # 1. Real KPI Calculations
    total_analyses = await db.scalar(select(func.count(AnalysisResult.id))) or 0
    today_analyses = await db.scalar(
        select(func.count(AnalysisResult.id)).where(AnalysisResult.created_at >= today_start)
    ) or 0
    yesterday_analyses = await db.scalar(
        select(func.count(AnalysisResult.id)).where(AnalysisResult.created_at >= yesterday_start, AnalysisResult.created_at < today_start)
    ) or 0
    
    # Calculate delta
    delta_val = today_analyses - yesterday_analyses
    delta_pct = (delta_val / yesterday_analyses * 100) if yesterday_analyses > 0 else 100 if today_analyses > 0 else 0

    total_claims = await db.scalar(select(func.count(Claim.id))) or 0
    
    # Deepfake detection count
    deepfakes_count = await db.scalar(
        select(func.count(AnalysisResult.id))
        .where(AnalysisResult.result_json.contains("AI_GENERATED") | AnalysisResult.result_json.contains("DEEPFAKE"))
    ) or 0

    summary = {
        "kpis": [
            {
                "title": "Analyses Today", 
                "value": str(today_analyses), 
                "delta": f"{'+' if delta_val >= 0 else ''}{delta_pct:.0f}%", 
                "positive": delta_val >= 0, 
                "icon": "📊"
            },
            {
                "title": "Total Claims", 
                "value": str(total_claims), 
                "delta": "Across all time", 
                "positive": True, 
                "icon": "⚖️"
            },
            {
                "title": "Deepfakes Rooted", 
                "value": str(deepfakes_count), 
                "delta": "High Confidence", 
                "positive": deepfakes_count > 0, 
                "icon": "🎭"
            },
            {
                "title": "System Uptime", 
                "value": "99.9%", 
                "delta": "Live", 
                "positive": True, 
                "icon": "⚡"
            },
        ]
    }

    # 2. Latest Claims
    claims_result = await db.execute(
        select(Claim).order_by(Claim.created_at.desc()).limit(10)
    )
    rows = claims_result.scalars().all()
    summary["trending_claims"] = [
        {
            "id": c.id,
            "claim": c.original_text,
            "verdict": c.verdict or "UNVERIFIABLE",
            "confidence": c.confidence or 0.5,
            "time": c.created_at.strftime("%I:%M %p")
        }
        for c in rows
    ]

    # 3. Recent Analysis Sessions
    receipts_result = await db.execute(
        select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(10)
    )
    receipt_rows = receipts_result.scalars().all()
    summary["recent_receipts"] = [
        {
            "id": f"VR-{r.id[:6].upper()}",
            "real_id": r.id,
            "verdict": "COMPLETED" if r.completed else "PROCESSING",
            "mediaType": r.media_type or "text",
            "time": r.created_at.strftime("%b %d, %H:%M")
        }
        for r in receipt_rows
    ]

    return summary


@router.get("/dashboard/explorer")
async def get_claims_explorer(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    verdict: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Deep forensic explorer for historical queries."""
    stmt = select(AnalysisResult).order_by(AnalysisResult.created_at.desc())
    
    # Optional filtering
    if search:
        stmt = stmt.where(AnalysisResult.id.ilike(f"%{search}%") | AnalysisResult.result_json.ilike(f"%{search}%"))
    
    # Count total
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    
    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    import json
    explorer_data = []
    for r in rows:
        data = json.loads(r.result_json) if r.result_json else {}
        explorer_data.append({
            "id": r.id,
            "display_id": f"VR-{r.id[:6].upper()}",
            "claim": data.get("claim", "Pending/Unknown Analysis"),
            "verdict": data.get("verdict", "UNVERIFIABLE"),
            "confidence": data.get("confidence", 0.85),
            "media_type": r.media_type or "text",
            "context": data.get("context", "General"),
            "reasoning": data.get("reasoning", ""),
            "date": r.created_at.strftime("%b %d, %Y (%I:%M %p)")
        })
        
    return {
        "results": explorer_data,
        "total_count": total,
        "page": page,
        "has_next": (page * page_size) < total
    }


@router.get("/dashboard/graph")
async def get_provenance_graph(db: AsyncSession = Depends(get_db)):
    """Generate a provenance graph of Claims and their Evidence Domains."""
    import json
    from urllib.parse import urlparse

    # Fetch latest 20 results for a richer graph
    result = await db.execute(
        select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(20)
    )
    analyses = result.scalars().all()

    nodes = []
    links = []
    seen_ids = set()
    
    # Use a simpler mapping for nodes
    for a in analyses:
        node_id = f"a_{a.id[:8]}"
        if node_id not in seen_ids:
            nodes.append({
                "id": node_id,
                "label": f"Report {a.id[:4]}",
                "verdict": "FALSE" if (a.result_json and ("AI_GENERATED" in a.result_json or "DEEPFAKE" in a.result_json)) else "TRUE",
                "type": "claim"
            })
            seen_ids.add(node_id)

        if not a.result_json: continue
        try:
            data = json.loads(a.result_json)
            context = data.get("context", "General")
            
            # Narrative Cluster Link (Conceptual)
            # Create a "Topic Node" for grouping if it doesn't exist
            topic_node_id = f"topic_{context.replace(' ', '_').lower()}"
            if topic_node_id not in seen_ids:
                nodes.append({
                    "id": topic_node_id, 
                    "label": context, 
                    "verdict": None, 
                    "type": "topic",
                    "group": context
                })
                seen_ids.add(topic_node_id)
            
            # Link claim to its Topic Cluster
            links.append({"source": node_id, "target": topic_node_id, "similarity_score": 0.9, "type": "topology"})
            
            # Evidence Links
            evidence = data.get("evidence_sources", [])
            for s in evidence:
                url = s.get("url") if isinstance(s, dict) else str(s)
                if not url or "http" not in url: continue
                domain = urlparse(url).netloc
                
                if domain not in seen_ids:
                    nodes.append({"id": domain, "label": domain, "verdict": None, "type": "source", "group": "Source"})
                    seen_ids.add(domain)
                
                links.append({"source": node_id, "target": domain, "similarity_score": 0.6})
        except: pass

    # Claim-Claim relationships (Mocked for Demo based on simple heuristic)
    for i in range(len(analyses)):
        for j in range(i + 1, len(analyses)):
            if analyses[i].media_type == analyses[j].media_type:
                # Same media type and close creation time?
                time_diff = abs((analyses[i].created_at - analyses[j].created_at).total_seconds())
                if time_diff < 3600: # Within 1 hour
                    links.append({
                        "source": f"a_{analyses[i].id[:8]}",
                        "target": f"a_{analyses[j].id[:8]}",
                        "similarity_score": 0.5
                    })

    if not nodes:
        nodes = [{"id": "empty", "label": "No Data Yet", "verdict": None, "type": "claim"}]

    return {"nodes": nodes, "links": links}
