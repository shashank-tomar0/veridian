import base64
import structlog
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from backend.config import settings
from ml.base import DetectionResult

logger = structlog.get_logger()

class GroqVisionDetector:
    """Cloud-based image analysis using Groq's Llama 3.2 Vision model."""
    
    def __init__(self):
        self.model = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            api_key=settings.groq_api_key,
            temperature=0.0
        )

    async def predict(self, image_path: str, caption: str = "") -> DetectionResult:
        """Analyze image content to identify potential misinformation or AI generation."""
        try:
            # Normalize path for Windows
            import os
            abs_image_path = os.path.abspath(image_path)
            
            # Read and encode image to base64
            with open(abs_image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            prompt = (
                "You are the Veridian High-Fidelity OCR & Vision Engine. \n\n"
                "STEP 1: TRANSCRIPTION TASK\n"
                "Meticulously transcribe ALL visible text, headlines, and articles from this image. \n"
                "WRAP YOUR TRANSCRIPTION IN [TRANSCRIPTION]...[/TRANSCRIPTION] TAGS.\n\n"
                "STEP 2: ANALYSIS\n"
                "1. Identify signs of AI generation (artifacts, unnatural textures).\n"
                "2. Detect potential misinformation cues.\n"
                "3. Summarize the core message or 'main claim' found in the text.\n\n"
                "Provide your response in a structured format."
            )
            if caption:
                prompt += f"\nUser provided caption: '{caption}'"

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ]
            )

            response = await self.model.ainvoke([message])
            analysis_text = response.content or ""
            
            # FORENSIC LOGGING
            logger.info("vision_raw_response", analysis_len=len(analysis_text), raw_snippet=analysis_text[:200])

            # Heuristic score
            is_ai = any(word in analysis_text.lower() for word in ["ai-generated", "artificial", "synthetic", "manipulated"])
            score = 0.85 if is_ai else 0.05
            
            return DetectionResult(
                score=score,
                verdict="AI_GENERATED" if is_ai else "VERIFIED_MEDIA",
                metadata={
                    "analysis": analysis_text,
                    "confidence": 0.9,
                    "model": "llama-4-scout"
                }
            )
        except Exception as e:
            error_str = str(e)
            if "decommissioned" in error_str.lower():
                logger.error("vision_decommission_critical", error=error_str, advice="Switch to meta-llama/llama-4-scout-17b-16e-instruct")
            else:
                logger.error("vision_analysis_error", error=error_str)
                
            return DetectionResult(score=0, verdict="ERROR", metadata={"error": error_str})
