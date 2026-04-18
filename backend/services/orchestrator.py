import uuid
import asyncio
import json
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any

import structlog
from backend.models.base import AsyncSessionLocal
from backend.models.claim import AnalysisResult
from workers.verification.agent import verification_agent

# Detectors
from ml.image.cloud_vision import GroqVisionDetector
from ml.audio.cloud_whisper import GroqWhisperDetector
from ml.audio.rawnet2 import RawNet2Detector
from ml.video.faceforensics import FaceForensicsDetector
from ml.video.syncsnet import SyncNetDetector
from ml.video.temporal import TemporalConsistencyDetector
from backend.services.scraper import scraper_service

logger = structlog.get_logger()

class AnalysisOrchestrator:
    """Unified service for processing text and multimodal claims."""
    
    def __init__(self):
        self.vision_detector = GroqVisionDetector()
        self.whisper_detector = GroqWhisperDetector()
        self.spoof_detector = RawNet2Detector()
        self.deepfake_detector = FaceForensicsDetector()
        self.sync_detector = SyncNetDetector()
        self.temporal_detector = TemporalConsistencyDetector()
        self.memory_store = {} # Stateless fallback

    async def analyze(
        self, 
        media_type: str, 
        text: Optional[str] = None, 
        file_path: Optional[str] = None,
        language: str = "auto",
        analysis_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Main entry point for any analysis request.
        Returns the analysis_id.
        """
        if not analysis_id:
            analysis_id = str(uuid.uuid4())

        # 1. Initialize Record in DB (with Stateless Fallback)
        try:
            async with AsyncSessionLocal() as session:
                record = AnalysisResult(
                    id=analysis_id,
                    media_hash=analysis_id, # Fallback hash
                    media_type=media_type,
                    status="processing",
                    completed=False
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.warning("orchestrator.db_fallback", error=str(e))
            self.memory_store[analysis_id] = {
                "status": "processing",
                "completed": False,
                "result_json": None
            }

        # 2. Run Background Analysis (don't block the caller)
        asyncio.create_task(self._process_pipeline(analysis_id, media_type, text, file_path, language, progress_callback))
        
        return analysis_id

    async def _process_pipeline(self, analysis_id: str, media_type: str, text: str, file_path: str, language: str, progress_callback: Optional[callable] = None):
        """Asynchronous execution of the multimodal pipeline."""
        logger.info("orchestrator.pipeline_start", analysis_id=analysis_id, media_type=media_type)
        
        transcribed_text = text or ""
        confidence = 0.5
        metadata = {}

        try:
            # --- MODAL SPECIFIC DETECTION ---
            if media_type == "image" and file_path:
                abs_fp = os.path.abspath(file_path)
                res = await self.vision_detector.predict(abs_fp, caption=text)
                analysis_body = res.metadata.get("analysis", "")
                
                # Surgical extraction from tags
                import re
                match = re.search(r"\[TRANSCRIPTION\](.*?)\[/TRANSCRIPTION\]", analysis_body, re.DOTALL | re.IGNORECASE)
                ocr_text = match.group(1).strip() if match else analysis_body
                
                # NO-EMPTY GUARD: If OCR/Analysis failed, fall back to caption or prompt-aware description
                if not ocr_text or len(ocr_text) < 5:
                    logger.warning("orchestrator.vision_empty", analysis_id=analysis_id)
                    ocr_text = text or "Image provided (No OCR text extracted)"

                transcribed_text = f"{ocr_text}\n\n[User Caption]: {text}" if text else ocr_text
                metadata["vision_analysis"] = res.metadata
                confidence = res.score
            
            elif (media_type == "audio" or media_type == "voice") and file_path:
                # 1. Transcription (Whisper)
                whisper_res = await self.whisper_detector.transcribe(file_path, language=language)
                transcribed_text = whisper_res.get("text", "")
                
                # 2. Spoof Detection (RawNet2)
                spoof_res = self.spoof_detector.predict(file_path)
                
                metadata["audio_analysis"] = {
                    "transcript": transcribed_text,
                    "language": whisper_res.get("language"),
                    "spoof_score": spoof_res.score,
                    "spoof_verdict": spoof_res.verdict
                }
            
            elif media_type == "video" and file_path:
                # 1. Transcription (Whisper)
                whisper_res = await self.whisper_detector.transcribe(file_path, language=language)
                audio_text = whisper_res.get("text", "")
                
                # 2. Visual OCR (Multi-Frame Peek)
                ocr_text_parts = []
                try:
                    import cv2
                    cap = cv2.VideoCapture(file_path)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    
                    # Peeks at 2s, 10s, 20s, 40s, 60s
                    peek_times_ms = [2000, 10000, 20000, 40000, 60000]
                    
                    for ms in peek_times_ms:
                        if (ms / 1000) * fps > total_frames: continue
                        cap.set(cv2.CAP_PROP_POS_MSEC, ms)
                        ret, frame = cap.read()
                        if ret:
                            import tempfile
                            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                                cv2.imwrite(tmp.name, frame)
                                # Deep Forensic OCR Prompt
                                vision_prompt = "FORENSIC REQUIREMENT: Extract EVERY SINGLE WORD visible on screen. List all headlines, news tickers, and provocative banners. NEVER summarize. Output ONLY the raw text."
                                res = await self.vision_detector.predict(tmp.name, caption=vision_prompt)
                                
                                import re
                                match = re.search(r"TRANSCRIPTION(?:\]|)(.*?)(?:\[/TRANSCRIPTION\]|$)", res.metadata.get("analysis", ""), re.DOTALL | re.IGNORECASE)
                                part = match.group(1).strip() if match else res.metadata.get("analysis", "")
                                if part and part not in ocr_text_parts:
                                    ocr_text_parts.append(part)
                            os.unlink(tmp.name)
                    cap.release()
                    ocr_text = "\n---\n".join(ocr_text_parts)
                except Exception as e:
                    logger.error("orchestrator.video_ocr_error", error=str(e))

                # Clean fusion components of noise/repeated dots from Whisper hallucinations
                clean_ocr = re.sub(r'[\.\s]{3,}$', '', ocr_text).strip()
                clean_audio = re.sub(r'[\.\s]{3,}$', '', audio_text).strip()
                
                visual_part = f"[VISUAL TEXT ON SCREEN]:\n{clean_ocr}" if clean_ocr else ""
                audio_part = f"[AUDIO TRANSCRIPT]:\n{clean_audio}" if clean_audio else "[AUDIO TRANSCRIPT]: No clear speech detected."
                
                fusion_parts = []
                # Add Media Context Label
                fusion_parts.append(f"🔍 [MEDIA FORENSIC CONTEXT]: Video Analysis (Multi-Stream)")
                if visual_part: fusion_parts.append(visual_part)
                fusion_parts.append(audio_part)
                if text: fusion_parts.append(f"[USER CAPTION]:\n{text}")
                
                transcribed_text = "\n\n".join(fusion_parts)
                
                language = whisper_res.get("language", "en")
                
                # 3. Deepfake Detection (FaceForensics)
                deepfake_res = self.deepfake_detector.predict(file_path)
                
                # 4. Lip-Sync Analysis (SyncNet)
                sync_res = self.sync_detector.predict(file_path)
                
                # 5. Temporal Consistency Analysis
                temporal_res = self.temporal_detector.predict(file_path)
                
                metadata["video_analysis"] = {
                    "caption": text,
                    "ocr_text": ocr_text,
                    "transcript": audio_text,
                    "deepfake_score": deepfake_res.score,
                    "deepfake_verdict": deepfake_res.verdict,
                    "sync_score": sync_res.score,
                    "sync_verdict": sync_res.verdict,
                    "temporal_score": temporal_res.score,
                    "temporal_verdict": temporal_res.verdict,
                    "video_metadata": {**deepfake_res.metadata, **temporal_res.metadata}
                }

            elif media_type == "url" and text:
                # 1. Scrape the URL
                scrap_res = await scraper_service.extract(text)
                if scrap_res["success"]:
                    transcribed_text = f"[ARTICLE TITLE]: {scrap_res['title']}\n\n[ARTICLE CONTENT]:\n{scrap_res['text']}"
                    metadata["url_analysis"] = {
                        "title": scrap_res["title"],
                        "author": scrap_res["author"],
                        "date": scrap_res["date"]
                    }
                else:
                    transcribed_text = f"URL Scraping Failed: {scrap_res.get('error', 'Unknown Error')}"
                    metadata["url_analysis"] = {"error": scrap_res.get("error")}

            # --- VERIFICATION LAYER (AGENT) ---
            initial_state = {
                "analysis_id": analysis_id,
                "transcribed_text": transcribed_text or text or "Unknown media content",
                "language": language,
                "extracted_claims": [],
                "current_claim_index": 0,
                "verdicts": [],
                "detections": metadata
            }
            
            # Verify claims sequentially
            for i, claim in enumerate(initial_state["extracted_claims"]):
                if progress_callback:
                    await progress_callback(i + 1, len(initial_state["extracted_claims"]))
                
                state = await verification_agent.verify_claim({
                    "extracted_claims": initial_state["extracted_claims"],
                    "current_claim_index": i,
                    "verdicts": initial_state["verdicts"],
                    "language": initial_state["language"]
                })
                initial_state["verdicts"] = state["verdicts"]

            # This calls AgentState workflow which saves to DB in store_results node
            final_state = await verification_agent.workflow.ainvoke(initial_state)
            
            # Sync to memory store for stateless failover
            self.memory_store[analysis_id] = {
                "status": "completed",
                "completed": True,
                "result_json": json.dumps({
                    "overall_verdict": final_state.get("verdicts", [{}])[0].get("verdict", "UNKNOWN") if final_state.get("verdicts") else "UNKNOWN",
                    "overall_confidence": final_state.get("verdicts", [{}])[0].get("confidence", 0.0) if final_state.get("verdicts") else 0.0,
                    "claim_verdicts": final_state.get("verdicts", []),
                    "detections": final_state.get("detections", {})
                })
            }
            
            logger.info("orchestrator.pipeline_complete", analysis_id=analysis_id)

        except Exception as e:
            logger.error("orchestrator.pipeline_error", analysis_id=analysis_id, error=str(e))
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                result = await session.execute(select(AnalysisResult).where(AnalysisResult.id == analysis_id))
                record = result.scalar_one_or_none()
                if record:
                    record.status = "failed"
                    await session.commit()

    async def get_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Poll the database for analysis completion and results, with memory fallback."""
        try:
            from sqlalchemy import select
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AnalysisResult).where(AnalysisResult.id == analysis_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    return {
                        "status": record.status,
                        "completed": record.completed,
                        "result_json": record.result_json
                    }
        except Exception as e:
            logger.warning("orchestrator.status_db_failed", error=str(e))

        # Memory Fallback
        return self.memory_store.get(analysis_id)

orchestrator = AnalysisOrchestrator()
