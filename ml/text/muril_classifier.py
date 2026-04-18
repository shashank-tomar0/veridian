import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ml.base import DetectionResult
from backend.config import settings

logger = logging.getLogger(__name__)

class MurilClassifier:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",  # Ultra-fast model for classification
            api_key=settings.groq_api_key,
            temperature=0.0,
            request_timeout=60.0
        )
        self._is_loaded = True

    def load_model(self):
        # No-op for cloud API
        pass

    async def predict(self, text: str) -> DetectionResult:
        """Async version for better performance in the bot."""
        sys_msg = SystemMessage(content="""You are an expert in spotting semantic manipulation and code-mixing inconsistencies in news text.
Analyze the provided text and determine if it has been MANIPULATED (e.g., semantic drift, out-of-context phrases, code-mixing errors).
Output ONLY a JSON object: {"manipulated_score": float (0.0-1.0), "verdict": "AUTHENTIC"|"MANIPULATED"}""")
        
        try:
            resp = await self.llm.ainvoke([sys_msg, HumanMessage(content=text)])
            import json
            res = json.loads(resp.content)
            score = res.get("manipulated_score", 0.0)
            return DetectionResult(
                score=score,
                metadata={"engine": "groq-cloud", "model": "llama-3.1-8b"},
                verdict=res.get("verdict", "AUTHENTIC")
            )
        except Exception as e:
            logger.error(f"MuRIL API Error: {e}")
            return DetectionResult(score=0.0, metadata={"error": str(e)}, verdict="AUTHENTIC")
