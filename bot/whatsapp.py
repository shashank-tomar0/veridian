from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import httpx
import uuid
import structlog
from backend.config import settings
from workers.tasks.analyze import analyze_media

logger = structlog.get_logger()
router = APIRouter()

@router.get("/webhooks/whatsapp")
async def verify_webhook(request: Request):
    """WhatsApp Cloud API Verification"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return int(challenge)
        raise HTTPException(status_code=403, detail="Verification failed")
    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/webhooks/whatsapp")
async def handle_webhook(request: Request):
    """Handle incoming messages"""
    body = await request.json()
    
    if body.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}
        
    try:
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for msg in messages:
                    sender_id = msg.get("from")
                    msg_type = msg.get("type")
                    
                    analysis_id = str(uuid.uuid4())
                    metadata = {"sender": sender_id, "channel": "whatsapp"}
                    
                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                        metadata["text"] = text_body
                        analyze_media.delay(analysis_id, "", "text", metadata)
                        
                    elif msg_type in ["image", "video", "audio"]:
                        media_id = msg.get(msg_type, {}).get("id")
                        caption = msg.get(msg_type, {}).get("caption", "")
                        metadata["caption"] = caption
                        metadata["media_id"] = media_id
                        
                        # In production, we'd fetch the media via Graph API using media_id:
                        # headers = {"Authorization": f"Bearer {settings.whatsapp_api_token}"}
                        # Retrieve binary payload, upload to MinIO, and dispatch:
                        media_stub_url = f"minio://veridian-media/whatsapp/{media_id}"
                        analyze_media.delay(analysis_id, media_stub_url, msg_type, metadata)
                        
                    logger.info("whatsapp.message_dispatched", analysis_id=analysis_id, msg_type=msg_type)
    except Exception as e:
        logger.error("whatsapp.webhook_error", error=str(e))
        
    return {"status": "ok"}
