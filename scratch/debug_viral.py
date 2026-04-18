import asyncio
import json
from sqlalchemy import select
from backend.models.base import AsyncSessionLocal
from backend.models.claim import AnalysisResult

async def check_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(10)
        )
        analyses = result.scalars().all()
        print(f"Total recent analyses: {len(analyses)}")
        for a in analyses:
            data = json.loads(a.result_json) if a.result_json else {}
            verdict = data.get("overall_verdict", "N/A")
            context = data.get("context", "N/A")
            print(f"ID: {a.id[:8]} | Completed: {a.completed} | Verdict: {verdict} | Context: {context}")

if __name__ == "__main__":
    asyncio.run(check_db())
