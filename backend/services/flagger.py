import json
import structlog
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.claim import AnalysisResult, Claim

logger = structlog.get_logger()

class ViralFlagger:
    """Agent that monitors for coordinate misinformation campaigns."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def detect_spikes(self, window_minutes: int = 60, threshold: int = 3):
        """
        Detect coordinated misinformation spikes using AI context clustering.
        Triggers after 'threshold' (default 3) similar fake/misleading claims.
        """
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=window_minutes)
        logger.info("flagger.scanning", window_start=start_time.isoformat())

        # 1. Fetch recent completed analyses joined with original claim text
        from sqlalchemy.orm import selectinload
        stmt = (
            select(AnalysisResult)
            .where(AnalysisResult.created_at >= start_time)
            .where(AnalysisResult.completed == True)
        )
        result = await self.db.execute(stmt)
        analyses = result.scalars().all()

        if len(analyses) < threshold:
            return []

        # 2. Context-Aware Clustering
        buckets = {}
        for a in analyses:
            if not a.result_json: continue
            try:
                data = json.loads(a.result_json)
                verdict = data.get("verdict", data.get("overall_verdict", "UNVERIFIABLE"))
                
                # We monitor FALSE and MISLEADING for viral coordination alerts
                if verdict not in ["FALSE", "MISLEADING"]:
                    continue

                # Use a normalized cluster key
                raw_topic = data.get("context", data.get("topic", "General Updates"))
                cluster_key = "".join(filter(str.isalnum, raw_topic.lower()))[:30]
                
                if not cluster_key: cluster_key = "general"
                
                # Use a more resilient approach to find the 'news' text
                news_text = data.get("claim") or data.get("claim_text") or data.get("original_text") or raw_topic
                
                if cluster_key not in buckets:
                    buckets[cluster_key] = {
                        "items": [], 
                        "display_topic": raw_topic,
                        "news": news_text,
                        "verdict": verdict,
                        "spread_analysis": data.get("spread_analysis", "Coordinated dissemination targeting social or political tension.")
                    }
                buckets[cluster_key]["items"].append(a)
            except Exception as e: 
                logger.error("flagger.cluster_error", error=str(e))
                continue

        spikes = []
        for key, bucket in buckets.items():
            items = bucket["items"]
            if len(items) >= threshold:
                # INTELLIGENT SELECTION: Pick the analysis with the best/longest reasoning
                # to avoid showing fallbacks if a better audit exists in the cluster.
                best_item = items[-1]
                best_reasoning = "Check full report for multi-source verification."
                best_spread = bucket["spread_analysis"]
                
                for item in items:
                    try:
                        d = json.loads(item.result_json)
                        r = d.get("reasoning", "")
                        s = d.get("spread_analysis", "")
                        if len(r) > len(best_reasoning):
                            best_reasoning = r
                            best_item = item
                        if len(s) > len(best_spread) and "Coordinated" not in s:
                            best_spread = s
                    except: continue

                spikes.append({
                    "topic": bucket["display_topic"],
                    "news": bucket["news"],
                    "count": len(items),
                    "verdict": f"VERIFIED {bucket['verdict']}",
                    "reasoning": best_reasoning,
                    "spread_analysis": best_spread,
                    "last_id": best_item.id
                })

        return spikes
