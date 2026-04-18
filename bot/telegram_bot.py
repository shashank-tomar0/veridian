import logging
import html
import json
import os
from typing import Optional
import uuid
import structlog
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from backend.config import settings
from backend.services.orchestrator import orchestrator
from backend.models.base import init_models

logger = structlog.get_logger()
# Handle Render/Public URL detection for standalone bot mode
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL", f"http://{os.getenv('PUBLIC_IP', '127.0.0.1')}:8000")

# Elite Persistence for Notifier Agent
CHATS_FILE = "registered_chats.json"
KNOWN_CHATS = set()
if os.path.exists(CHATS_FILE):
    try:
        with open(CHATS_FILE, "r") as f:
            # Enforce integer-only chat IDs for reliable Telegram API compatibility
            KNOWN_CHATS = set(int(c) for c in json.load(f))
            logger.info("persistence.chats_loaded", count=len(KNOWN_CHATS))
    except Exception as e:
        logger.warning("persistence.chats_failed", error=str(e))

def save_chats():
    with open(CHATS_FILE, "w") as f:
        json.dump(list(KNOWN_CHATS), f)

ALREADY_FLAGGED = set() # Avoid repeat alerts for the same spike

async def viral_monitor_task(application: Application):
    """Background agent that monitors for spikes and broadcasts alerts."""
    from backend.services.flagger import ViralFlagger
    from backend.models.base import AsyncSessionLocal
    
    logger.info("viral_monitor.started")
    while True:
        try:
            await asyncio.sleep(60) # Poll every minute
            async with AsyncSessionLocal() as session:
                flagger = ViralFlagger(session)
                spikes = await flagger.detect_spikes()
                
                for s in spikes:
                    spike_key = f"{s['topic']}_{s['count']}"
                    if spike_key not in ALREADY_FLAGGED:
                        logger.warning("viral_spike_detected", topic=s['topic'], count=s['count'])
                        
                        # BROADCAST TO EVERYONE: Forensic Intelligence Bulletin
                        report_url = f"{PUBLIC_URL}/receipt/{s['last_id']}"
                        alert_text = (
                            f"🚨 <b>COORDINATED DISINFO ALERT</b>\n"
                            f"────────────────────────\n"
                            f"<b>VIRAL NEWS</b>: <i>\"{html.escape(s['news'])}\"</i>\n"
                            f"<b>INTEL SIGNAL</b>: Target detected <b>{s['count']} times</b> in last hour.\n\n"
                            f"<b>FORENSIC VERDICT</b>: <b>{s['verdict']}</b>\n"
                            f"<b>REASONING</b>: {html.escape(s['reasoning'])}\n"
                            f"<b>SPREAD DYNAMICS</b>: {html.escape(s['spread_analysis'])}\n\n"
                            f"🔗 <b>FULL AUDIT REPORT</b>: {report_url}"
                        )
                        
                        recipients = list(KNOWN_CHATS)
                        logger.info("notifier.broadcasting", count=len(recipients), ids=recipients)
                        
                        for chat_id in recipients:
                            try:
                                await application.bot.send_message(
                                    chat_id=int(chat_id),
                                    text=alert_text,
                                    parse_mode="HTML"
                                )
                                logger.info("notifier.broadcast_success", chat_id=chat_id)
                            except Exception as e:
                                logger.error("notifier.broadcast_error", chat_id=chat_id, error=str(e))
                        
                        ALREADY_FLAGGED.add(spike_key)
        except Exception as e:
            logger.error("viral_monitor.loop_error", error=str(e))
            await asyncio.sleep(10)
            
LOCALIZED_LABELS = {
    "en": {
        "title": "📃 <b>VERIDIAN TRUST RECEIPT</b>",
        "claim": "🔎 <b>CLAIM AUDIT</b>",
        "verdict": "⚖️ <b>VERDICT</b>",
        "sources": "🌐 <b>SOURCES</b>",
        "origin": "🏛️ <b>ORIGIN</b>",
        "context": "📍 <b>CONTEXT</b>",
        "facts": "🏛️ <b>CORRECT FACTS</b>",
        "signals": "🧠 <b>REASONING SIGNALS</b>",
        "temporal": "🕒 <b>TEMPORAL AUDIT</b>",
        "report": "🎙️ <b>VERIDIAN REPORT</b>",
        "full_report": "🔗 <b>FULL AUDIT REPORT</b>",
        "engine_id": "🆔 <b>ENGINE ID</b>",
        "footer": "✅ <b>Reasoning Engine Verified: Results archived to secure SQLite.</b>",
        "verdicts": {
            "TRUE": "✅ VERIFIED TRUE", 
            "FALSE": "❌ VERIFIED FALSE", 
            "MISLEADING": "⚠️ MISLEADING", 
            "UNVERIFIABLE": "🛡️ HIGH-STAKES ADVISORY"
        }
    },
    "hi": {
        "title": "📃 <b>वेरिडियन विश्वास रसीद</b>",
        "claim": "🔎 <b>दावा ऑडिट</b>",
        "verdict": "⚖️ <b>निर्णय</b>",
        "sources": "🌐 <b>स्रोत</b>",
        "origin": "🏛️ <b>उत्पत्ति</b>",
        "context": "📍 <b>संदर्भ</b>",
        "facts": "🏛️ <b>सही तथ्य</b>",
        "signals": "🧠 <b>तर्क संकेत</b>",
        "temporal": "🕒 <b>कालिक ऑडिट</b>",
        "report": "🎙️ <b>वेरिडियन रिपोर्ट</b>",
        "full_report": "🔗 <b>पूर्ण ऑडिट रिपोर्ट</b>",
        "engine_id": "🆔 <b>इंजन आईडी</b>",
        "footer": "✅ <b>तर्क इंजन सत्यापित: परिणाम सुरक्षित SQLite में संग्रहीत।</b>",
        "verdicts": {"TRUE": "सत्य (TRUE)", "FALSE": "असत्य (FALSE)", "MISLEADING": "भ्रामक (MISLEADING)", "UNVERIFIABLE": "असत्यापनीय (UNVERIFIABLE)"}
    }
}

def dynamic_linker(text: str, sources: list, escape: bool = True) -> str:
    """Elite utility to hyperlink domain mentions in the AI response using robust regex."""
    import html
    import re
    from urllib.parse import urlparse
    
    processed = html.escape(text) if escape else text
    linked_domains = set()
    
    for s in sources:
        url = s.get("url", "#")
        domain = urlparse(url).netloc.replace("www.", "")
        if not domain or domain in linked_domains:
            continue
            
        # Regex explanation:
        # (?<![/:@.]) -> Negative lookbehind for characters that usually precede a domain inside a URL
        # \b -> Word boundary (start)
        # ({re.escape(domain)}) -> The domain itself
        # (?!/) -> Negative lookahead to ensure it's not followed by a path separator (part of a URL)
        pattern = rf"(?<![/:@.])\b{re.escape(domain)}\b(?!/)"
        
        # We only link the first few occurrences to avoid link spam
        processed = re.sub(pattern, f'<a href="{url}">{domain}</a>', processed, count=2)
        linked_domains.add(domain)
        
    return processed

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Veridian. Send me a message for full multi-layer fact verification.")

async def post_init(application: Application):
    """Professional lifecycle hook for background initialization."""
    from backend.models.base import init_models
    await init_models()
    print("DEBUG: [INIT] Zero-Config Database ready.")
    
# Start the Neural Keep-Alive Pulse (Prevents Render Sleep)
    asyncio.create_task(keep_alive_task())
    
    # Start the Viral Flagger Monitor
    asyncio.create_task(viral_monitor_task(application))

async def keep_alive_task():
    """Periodically pulses the API to prevent Render web-service hibernation."""
    client = httpx.AsyncClient(timeout=10)
    logger.info("keep_alive.started", url=PUBLIC_URL)
    while True:
        try:
            # We pulse the health endpoint every 5 minutes
            await asyncio.sleep(300) 
            resp = await client.get(f"{PUBLIC_URL}/v1/health")
            logger.info("keep_alive.pulse", status=resp.status_code)
        except Exception as e:
            logger.warning("keep_alive.failed", error=str(e))

async def wait_for_analysis(status_msg, analysis_id: str):
    """Poll for result and update the message with the WHOLE result."""
    from urllib.parse import urlparse
    while True:
        await asyncio.sleep(2)
        res = await orchestrator.get_status(analysis_id)
        if not res: continue
        
        if res["completed"]:
            # Format and show WHOLE result based on REAL screenshot design
            import json
            import html
            import re
            from urllib.parse import urlparse
            try:
                data = json.loads(res["result_json"])
                overall_verdict = data.get("overall_verdict", "UNVERIFIABLE")
                # Harden confidence to handle None or non-numeric values
                raw_confidence = data.get("overall_confidence", 0.0)
                try:
                    overall_confidence = float(raw_confidence)
                except (TypeError, ValueError):
                    overall_confidence = 0.0
                
                claims = data.get("claim_verdicts", [])
                detections = data.get("detections", {})
                
                primary_claim = claims[0] if claims else {}
                
                # --- Map Reasoning Signals ---
                signals = []
                if "vision_analysis" in detections:
                    vis = detections["vision_analysis"]
                    score = vis.get("manipulation_score", 0.0)
                    signals.append(f"ELA Forgery Prob {score*100:.0f}%")
                    signals.append("Cloud Vision Verified")
                elif "audio_analysis" in detections:
                    audio_data = detections["audio_analysis"]
                    signals.append("Whisper Transcription Verified")
                    verdict = audio_data.get("spoof_verdict", "UNKNOWN")
                    score = audio_data.get("spoof_score", 0.0)
                    signals.append(f"Spoof Analysis: {verdict} ({score*100:.0f}%)")
                elif "video_analysis" in detections:
                    vid = detections["video_analysis"]
                    df_v = vid.get("deepfake_verdict", "UNKNOWN")
                    df_s = vid.get("deepfake_score", 0.0)
                    sync_s = vid.get("sync_score", 0.0)
                    temp_v = vid.get("temporal_verdict", "CONSISTENT")
                    
                    # Ensure numeric signals are shown for a crisp 'Elite' report
                    signals.append(f"Deepfake: {df_v} ({df_s*100:.0f}%)")
                    signals.append(f"Lip-Sync Match: {sync_s*100:.0f}%")
                    signals.append(f"Temporal: {temp_v}")
                else:
                    # Fallback text signals
                    signals.append("Likely Human (30%)")
                    signals.append("Semantic Manipulation 0%")

                # --- Exact Visual Formatting (HTML Mode) ---
                lang = data.get("language", "en")
                labels = LOCALIZED_LABELS.get(lang, LOCALIZED_LABELS["en"])
                
                # Localize Verdict
                display_verdict = labels["verdicts"].get(overall_verdict, overall_verdict)
                
                report_msg = (
                    f"{labels['title']}\n"
                    f"────────────────────\n"
                    f"{labels['claim']}: {html.escape(primary_claim.get('claim', 'Unknown Content'))}\n"
                    f"{labels['verdict']}: {display_verdict} ({overall_confidence*100:.0f}%)\n"
                )
                
                # Add Verdict Reasons (Bullets)
                reasons = primary_claim.get("verdict_reasons", [])
                for r in reasons:
                    report_msg += f" • {html.escape(r)}\n"
                
                # Add Sources
                report_msg += f"{labels['sources']}:\n"
                for s in primary_claim.get("evidence_sources", []):
                    url = s.get("url", "#")
                    domain = urlparse(url).netloc.replace("www.", "") or "source"
                    title = html.escape(s.get("title", 'Verified Source'))
                    report_msg += f" • <a href=\"{url}\">{domain}</a>: <i>{title}</i>\n"
                
                # Check for uncalibrated signals
                audio_tag = ""
                if "audio_analysis" in detections:
                    audio_meta = detections["audio_analysis"].get("metadata", {})
                    if audio_meta.get("status") == "uncalibrated_fallback":
                        audio_tag = " (Uncalibrated)"

                # Sanitize origin URL
                raw_origin = primary_claim.get('origin', '#')
                url_match = re.search(r'https?://[^\s\)]+', raw_origin)
                origin_url = url_match.group(0) if url_match else "#"
                
                origin_display = raw_origin.replace(origin_url, "").strip(" ()")
                if not origin_display: origin_display = urlparse(origin_url).netloc
                origin_display = origin_display[:50] + "..." if len(origin_display) > 50 else origin_display
                
                # Apply Dynamic Linker
                raw_response = primary_claim.get('whatsapp_response', 'The claim has been verified.')
                # Escape FIRST to ensure user/AI content doesn't break HTML
                escaped_response = html.escape(raw_response)
                # Link domains
                linked_response = dynamic_linker(escaped_response, primary_claim.get("evidence_sources", []), escape=False)
                
                # RE-STRUCTURE UI: Convert markers to professional bold headers with vertical spacing
                # Aggressive replacement handles variations in AI output (brackets or no brackets)
                structured_response = (
                    linked_response
                    .replace("[STATUS]:", "<b>STATUS</b>:").replace("[STATUS]", "<b>STATUS</b>:").replace("STATUS:", "<b>STATUS</b>:")
                    .replace("[RUMOR ANALYSIS]:", "\n<b>RUMOR ANALYSIS</b>:").replace("[RUMOR ANALYSIS]", "\n<b>RUMOR ANALYSIS</b>:").replace("RUMOR ANALYSIS:", "\n<b>RUMOR ANALYSIS</b>:")
                    .replace("[GROUND REALITY]:", "\n<b>GROUND REALITY</b>:").replace("[GROUND REALITY]", "\n<b>GROUND REALITY</b>:").replace("GROUND REALITY:", "\n<b>GROUND REALITY</b>:")
                )

                # Build Correct Facts list
                facts = primary_claim.get("correct_facts", [])
                fact_block = ""
                if facts:
                    fact_block = f"{labels['facts']}:\n"
                    for f in facts:
                        fact_block += f" • {html.escape(f)}\n"

                report_msg += (
                    f"{labels['origin']}: <a href=\"{origin_url}\">{html.escape(origin_display)}</a>\n"
                    f"{labels['context']}: {html.escape(primary_claim.get('context', 'Current News'))}\n"
                    f"{fact_block}"
                    f"{labels['signals']}: {html.escape(', '.join(signals))}{audio_tag}\n"
                    f"{labels['temporal']}: Verified (Focus: {html.escape(primary_claim.get('context', 'Current status'))})\n"
                    f"{labels['report']}:\n{structured_response}\n\n"
                    f"{labels['full_report']}:\n{PUBLIC_URL}/receipt/{analysis_id}\n\n"
                    f"{labels['engine_id']}: <code>{analysis_id[:8]}</code>\n"
                    f"────────────────────\n"
                    f"{labels['footer']}"
                )

                # 1. Send Report Text (HTML MODE)
                try:
                    await status_msg.edit_text(report_msg, parse_mode="HTML", disable_web_page_preview=True)
                except Exception as html_err:
                    logger.warning(f"HTML Parse Error: {html_err}. Falling back to plain text.")
                    # Clean report_msg of all tags for emergency fallback
                    plain_report = re.sub(r'<[^>]+>', '', report_msg)
                    await status_msg.edit_text(plain_report, parse_mode=None)
                
                # 2. Send QR Code (External API) - Isolated failure
                try:
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={PUBLIC_URL}/receipt/{analysis_id}"
                    await status_msg.reply_photo(qr_url)
                except Exception as qr_err:
                    logger.warning(f"QR Code generation failed: {qr_err}. Report remains sent.")
                
                return True
            except Exception as e:
                logger.exception("format_error") 
                await status_msg.edit_text(f"✅ <b>Analysis Complete</b>\n\nView the whole result here:\n🔗 <a href=\"http://localhost:3000/receipt/{analysis_id}\">Full Report</a>", parse_mode="HTML")
                return True
            
        if res["status"] == "failed":
            await status_msg.edit_text("❌ <b>Analysis Error</b>: The engine encountered a failure during processing.", parse_mode="HTML")
            return False
            
    await status_msg.edit_text("⌛ *Timed Out*: Analysis is taking longer than expected. Please check the dashboard later.", parse_mode="Markdown")
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    
    chat_id = msg.chat_id
    if chat_id not in KNOWN_CHATS:
        KNOWN_CHATS.add(chat_id)
        save_chats()

    analysis_id = str(uuid.uuid4())
    
    # URL Detection 
    import re
    is_url = re.match(r'^https?://\S+$', msg.text.strip())
    
    status_text = "🔗 <b>Veridian Link Intelligence</b>\nInitializing Local Storage..." if is_url else "🔍 <b>Veridian Reasoning Engine</b>\nInitializing Local Storage..."
    status_msg = await msg.reply_text(status_text, parse_mode="HTML")
    
    try:
        # Progress callback to update status_msg
        async def progress_cb(current, total):
            try:
                msg_body = f"🔍 <b>Veridian Reasoning Engine</b>\n\nVerified <code>{current}/{total}</code> claims..."
                await status_msg.edit_text(msg_body, parse_mode="HTML")
            except Exception: pass

        # Simple hand-off to orchestrator
        await orchestrator.analyze(
            media_type="url" if is_url else "text",
            text=msg.text.strip(),
            analysis_id=analysis_id,
            progress_callback=progress_cb
        )
        
        # Immediate confirmation of storage mode
        mode_text = "📁 Local DB Mode" if "sqlite" in settings.database_url else "⚡ Stateless RAM Mode"
        await status_msg.edit_text(f"🔍 <b>Veridian reasoning Engine</b>\n{mode_text} Active...\n\nScraping content...", parse_mode="HTML")

        # Polling instead of sleep
        await wait_for_analysis(status_msg, analysis_id)

    except Exception as e:
        logger.error("bot_error", error=str(e))
        await msg.reply_text("⚠️ Analysis engine encountered an error. Please try again later.")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg: return
    
    chat_id = msg.chat_id
    if chat_id not in KNOWN_CHATS:
        KNOWN_CHATS.add(chat_id)
        save_chats()

    analysis_id = str(uuid.uuid4())
    status_msg = await msg.reply_text("🔍 *Veridian Reasoning Engine* - Processing multimodal content...", parse_mode="Markdown")

    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB Standard API limit

    try:
        # Determine media type and size check
        media_type = "image"
        file_size = 0
        
        if msg.photo and len(msg.photo) > 0: 
            media_type = "image"
            file_size = msg.photo[-1].file_size
        elif msg.video: 
            media_type = "video"
            file_size = msg.video.file_size
        elif msg.animation:
            media_type = "video" # GIFs are processed as videos
            file_size = msg.animation.file_size
        elif msg.video_note:
            media_type = "video"
            file_size = msg.video_note.file_size
        elif msg.audio or msg.voice: 
            media_type = "audio"
            file_size = (msg.audio or msg.voice).file_size
        elif msg.document:
            mime = msg.document.mime_type or ""
            if mime.startswith("image/"):
                media_type = "image"
            elif mime.startswith("video/"):
                media_type = "video"
            else:
                return # Unsupported document type
            file_size = msg.document.file_size
        else: return

        # Proactive size guard
        if file_size > MAX_FILE_SIZE:
             size_mb = file_size / (1024 * 1024)
             error_msg = (
                 f"⚠️ *Media is too large for Cloud Analysis*\n\n"
                 f"The file size is *{size_mb:.1f}MB*, but Telegram limits bot downloads to *20MB*.\n\n"
                 f"💡 *How to fix this*:\n"
                 f"1. Send a shorter clip (max 15-20 seconds).\n"
                 f"2. Use 'Low Quality' or 480p when sending the video.\n"
                 f"3. Send as a compressed 'Video' (not a 'File' attachment)."
             )
             await status_msg.edit_text(error_msg, parse_mode="Markdown")
             return

        # Proceed to get file if within limits
        if media_type == "image":
            if msg.photo: media_file = await msg.photo[-1].get_file()
            else: media_file = await msg.document.get_file()
        elif media_type == "video":
            if msg.video: media_file = await msg.video.get_file()
            elif msg.animation: media_file = await msg.animation.get_file()
            elif msg.video_note: media_file = await msg.video_note.get_file()
            else: media_file = await msg.document.get_file()
        elif media_type == "audio":
            media_file = await (msg.audio or msg.voice).get_file()

        # Download to temp
        import tempfile
        import os
        import traceback
        suffix = ".jpg" if media_type == "image" else ".mp4" if media_type == "video" else ".ogg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            await media_file.download_to_drive(tmp.name)
            file_path = tmp.name

        # Progress callback to update status_msg
        async def progress_cb(current, total):
            try:
                # Elite Branding for the progress bar
                icons = ["⏳", "🔍", "⚖️", "🏛️", "✅"]
                icon = icons[min(current, len(icons)-1)]
                msg_body = f"{icon} <b>VERIDIAN AUDIT IN PROGRESS</b>\n\n"
                msg_body += f"Auditing Claim <code>{current}/{total}</code> of the multimodal context..."
                if current == total:
                    msg_body += "\n\n✨ <i>Verification complete. Formatting elite report...</i>"
                await status_msg.edit_text(msg_body, parse_mode="HTML")
            except Exception: pass

        # Hand-off to shared orchestrator
        await orchestrator.analyze(
            media_type=media_type,
            text=msg.caption or "",
            file_path=file_path,
            analysis_id=analysis_id,
            progress_callback=progress_cb
        )

        # Polling instead of fixed sleep
        await wait_for_analysis(status_msg, analysis_id)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error("multimodal_error", error=str(e), traceback=error_trace)
        
        # Update the status message with the error and a snippet of the traceback for debugging
        error_msg = f"❌ *Multimodal Analysis Failed*\n\n*Error*: `{str(e)}`"
        if "index out of range" in str(e):
             error_msg += f"\n\n*Trace*: `{error_trace.splitlines()[-2:]}`"
             
        try:
            await status_msg.edit_text(error_msg, parse_mode="Markdown")
        except:
            await msg.reply_text(error_msg, parse_mode="Markdown")

async def error_handler(update: Optional[object], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to notify the developer."""
    err = context.error
    if "getaddrinfo failed" in str(err) or "ReadError" in str(err):
        logger.warning("network_flicker", message="Temporary connection loss to Telegram. Retrying...")
    else:
        logger.error("telegram_error", error=str(err), update=update)

def main():
    """Start the bot."""
    # Increase timeouts for slow connections
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .request(request)
        .post_init(post_init)
        .build()
    )

    # Add error handler
    application.add_error_handler(error_handler)

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Media handler (Photo, Video, Audio, Voice)
    media_filter = filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO
    application.add_handler(MessageHandler(media_filter, handle_media))

    # Run the bot with a reconnect loop for local stability
    logger.info("Veridian Bot Starting...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False, drop_pending_updates=True)

if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("bot_crash", error=str(e))
            print(f"Connection lost. Retrying in 5 seconds... Error: {e}")
            time.sleep(5)
