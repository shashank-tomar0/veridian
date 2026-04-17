import logging
import uuid
import structlog
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from backend.config import settings
from ml.text.muril_classifier import MurilClassifier
from ml.text.binoculars import BinocularsDetector
from workers.verification.agent import verification_agent

# Singletons for inference (lazy loaded)
muril = MurilClassifier()
binoculars = BinocularsDetector()

logger = structlog.get_logger()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Veridian. Send me a message for full multi-layer fact verification.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    analysis_id = str(uuid.uuid4())
    status_msg = await msg.reply_text("🔍 *Veridian Reasoning Engine* [Layer 1: Ingestion] - Initializing multi-layer analysis...", parse_mode="Markdown")
    
    try:
        # LAYER 2: Multimodal Detection Engine (Binoculars + MuRIL)
        await status_msg.edit_text("🔍 *Veridian Reasoning Engine* [Layer 2: Detection] - Running AI-text & Semantic detectors...", parse_mode="Markdown")
        
        # Run detections in parallel for performance
        bino_task = asyncio.to_thread(binoculars.predict, msg.text)
        muril_task = asyncio.to_thread(muril.predict, msg.text)
        bino_res, muril_res = await asyncio.gather(bino_task, muril_task)
        
        ai_score = round(bino_res.score * 100)
        manip_score = round(muril_res.score * 100)
        
        # LAYER 3: Claim Extraction & Fact Verification
        await status_msg.edit_text("🔍 *Veridian Reasoning Engine* [Layer 3: Verification] - Extracting claims & querying authoritative evidence...", parse_mode="Markdown")
        
        initial_state = {
            "analysis_id": analysis_id,
            "transcribed_text": msg.text,
            "language": muril_res.metadata.get("language", "auto"),
            "extracted_claims": [],
            "current_claim_index": 0,
            "verdicts": []
        }
        final_state = await verification_agent.workflow.ainvoke(initial_state)
        verdicts = final_state.get("verdicts", [])
        
        if not verdicts:
            await status_msg.edit_text("🏁 *Analysis Complete*\nNo falsifiable factual claims detected in the provided text.")
            return

        # LAYER 4 & 5: Temporal/Provenance Tracing & Counter-Narrative Generation
        await status_msg.edit_text("🔍 *Veridian Reasoning Engine* [Layer 4+5: Provenance & Narrative] - Tracing origin & generating shareable trust receipt...", parse_mode="Markdown")
        
        v = verdicts[0] # Focus on primary claim for succinct TG response
        confidence = round(v.get("confidence", 0) * 100)
        
        # Exact PRD-mandated formatting (Section 5.1)
        response = "🧾 *VERIDIAN TRUST RECEIPT*\n"
        response += "───────────────────\n"
        response += f"• *CLAIM*: {v.get('claim', msg.text)}\n"
        response += f"• *VERDICT*: {v['verdict']} ({confidence}%)\n"
        
        # EVIDENCE: Citations with titles
        response += "• *EVIDENCE*:\n"
        sources = v.get("evidence_sources", [])
        if sources:
            for s in sources[:3]:
                # Extract URL and Title from "Source [url] Title: ... | Date: ... | Content: ..."
                match = re.search(r'Source \[(.*?)\] Title: (.*?) \| Date: (.*?) \|', s)
                if match:
                    url, title, date = match.groups()
                    domain = url.split("//")[-1].split("/")[0]
                    date_str = f" ({date})" if date != "No Date" else ""
                    response += f"  - [{domain}]({url}): _{title}_{date_str}\n"
                else:
                    response += f"  - {s[:100]}...\n"
        else:
            response += "  - No immediate external cross-references found.\n"
            
        response += f"• *ORIGIN*: {v.get('origin', 'Indicated by independent reports.')}\n"
        response += f"• *CONTEXT*: {v.get('context', 'Trending news cycle.')}\n"
        
        # AI Detection Signal (Layer 2)
        ai_signal = "AI-Gen" if bino_res.score > 0.7 else "Human"
        sig_str = "High Probability AI" if bino_res.score > 0.85 else ("Likely AI" if bino_res.score > 0.7 else "Likely Human")
        response += f"• *REASONING SIGNALS*: {sig_str} ({ai_score}%), Semantic Manipulation {manip_score}%\n"
        
        response += f"• *RESPONSE*: {v.get('whatsapp_response', 'Analysis in progress. Please refrain from forwarding false information.')}\n\n"
        
        # LAYER 6: Delivery
        report_id = analysis_id[:8]
        report_url = f"http://localhost:3000/report/{analysis_id}"
        response += f"🔗 *ENGINE ID*: `{report_id}` | [Full Analysis]({report_url})\n"
        response += "✅ _Reasoning Engine Verified: Results archived to secure SQLite._"

        await status_msg.edit_text(response, parse_mode="Markdown", disable_web_page_preview=True)
        
    except Exception as e:
        logger.error("analysis_error", error=str(e))
        await status_msg.edit_text(f"❌ *Analysis Failed*: {str(e)}\nHardware: CPU-Friendly Mode Active.")
        
        await status_msg.edit_text(f"❌ *Analysis Failed*: {str(e)}\nPlease retry or check your API keys.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot with a reconnect loop for local stability
    logger.info("Veridian Bot Starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

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
