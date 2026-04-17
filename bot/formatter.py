from PIL import Image, ImageDraw, ImageFont
import io

class TrustReceiptFormatter:
    def __init__(self):
        # We would load a rich font in production
        pass

    def format_text(self, verdict_data: dict) -> str:
        """Formats for WhatsApp / Telegram text messages"""
        v = verdict_data.get("verdict", "UNVERIFIABLE").upper()
        
        indicators = {
            "TRUE": "🟢 *VERIFIED TRUE*",
            "FALSE": "🔴 *VERIFIED FALSE*",
            "MISLEADING": "⚠️ *MISLEADING*",
            "UNVERIFIABLE": "⚪ *UNVERIFIABLE*"
        }
        
        badge = indicators.get(v, indicators["UNVERIFIABLE"])
        claim = verdict_data.get("claim", "")
        reasoning = verdict_data.get("reasoning", "")
        
        # Build message
        msg = f"{badge}\n\n"
        msg += f"*Claim:* _{claim}_\n\n"
        msg += f"*Analysis:* {reasoning}\n\n"
        
        sources = verdict_data.get("evidence_used", [])
        if sources:
            msg += "*Sources:*\n"
            for s in sources:
                msg += f"• {s}\n"
                
        msg += "\n_Powered by Veridian Response Engine_"
        return msg

    def generate_card(self, verdict_data: dict) -> bytes:
        """Generates a PIL image trust card (PNG buffer)"""
        # Create a simple generic canvas
        width, height = 800, 400
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Draw verdict bar
        v = verdict_data.get("verdict", "UNVERIFIABLE").upper()
        colors = {
            "TRUE": (46, 204, 113),
            "FALSE": (231, 76, 60),
            "MISLEADING": (241, 196, 15),
            "UNVERIFIABLE": (149, 165, 166)
        }
        bar_color = colors.get(v, colors["UNVERIFIABLE"])
        
        draw.rectangle([0, 0, width, 20], fill=bar_color)
        
        # Draw text (fallback to default font)
        try:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_body = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            
        draw.text((30, 50), f"VERDICT: {v}", fill=bar_color, font=font_title)
        
        claim_text = verdict_data.get("claim", "Unknown claim")
        draw.text((30, 110), f"Claim: {claim_text[:60]}...", fill=(255, 255, 255), font=font_body)
        
        reason = verdict_data.get("reasoning", "")
        draw.text((30, 150), reason[:120] + ("..." if len(reason) > 120 else ""), fill=(200, 200, 200), font=font_body)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

formatter = TrustReceiptFormatter()
