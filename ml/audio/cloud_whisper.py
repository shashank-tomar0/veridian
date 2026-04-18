import httpx
import structlog
from typing import Optional
from backend.config import settings

logger = structlog.get_logger()

class GroqWhisperDetector:
    """Cloud-based audio transcription using Groq's Whisper Large V3."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.url = "https://api.groq.com/openai/v1/audio/transcriptions"

    async def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """Transcribe audio file to text and identify language."""
        try:
            async with httpx.AsyncClient() as client:
                with open(audio_path, "rb") as f:
                    files = {"file": (audio_path, f)}
                    data = {
                        "model": "whisper-large-v3-turbo",
                        "response_format": "json",
                        "temperature": "0.0",
                        "prompt": "Full verbatim transcription including all claims. Do not summarize. If silent, return empty string."
                    }
                    if language and language != "auto":
                        data["language"] = language

                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    response = await client.post(
                        self.url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=120.0
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    text = result.get("text", "").strip()
                    
                    # Clean common hallucinations
                    hallucinations = ["...", "Thank you.", "Subtitles by", "Subtitled by", "Stay tuned"]
                    for h in hallucinations:
                        if text == h or text.startswith(h + " "):
                            text = ""
                    
                    # Final dot cleanup
                    if all(c in ". " for c in text):
                        text = ""

                    return {
                        "text": text,
                        "language": result.get("language", "unknown"),
                        "success": True
                    }

        except Exception as e:
            logger.error("whisper_transcription_error", error=str(e))
            return {"text": "", "language": "unknown", "success": False, "error": str(e)}
