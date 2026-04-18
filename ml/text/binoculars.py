import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ml.base import DetectionResult
from backend.config import settings

logger = logging.getLogger(__name__)

class BinocularsDetector:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=settings.groq_api_key,
            temperature=0.0,
            request_timeout=60.0
        )
        self._is_loaded = True

    def load_model(self):
        # No-op for cloud API
        pass

    async def predict(self, text: str) -> DetectionResult:
        """Async version for better performance."""
        sys_msg = SystemMessage(content="""You are a world-class AI text detector. 
Analyze the input text for patterns typical of large language models (predictability, consistent sentence length, generic transitions).

CRITICAL CONTEXT: 
- Short, universally known factual sentences (e.g. "Water boils at 100 degrees", "Narendra Modi is the PM") are highly predictable by nature. 
- DO NOT flag such factual consensus as AI simply because it is predictable. 
- Flag only generative patterns: unnecessary hedging, perfectly rhythmic generic prose, or repetitive instructional style.

Output ONLY a JSON object: {"ai_score": float (0.0-1.0), "is_ai": boolean}""")
        
        try:
            resp = await self.llm.ainvoke([sys_msg, HumanMessage(content=text)])
            import json
            res = json.loads(resp.content)
            score = res.get("ai_score", 0.0)
            return DetectionResult(
                score=score,
                metadata={"engine": "groq-cloud", "method": "heuristic-analysis"},
                verdict="AI" if res.get("is_ai", False) else "HUMAN"
            )
        except Exception as e:
            logger.error(f"Binoculars API Error: {e}")
            return DetectionResult(score=0.0, metadata={"error": str(e)}, verdict="HUMAN")
