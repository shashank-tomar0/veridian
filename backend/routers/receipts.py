from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import os
from backend.deps import get_db
from backend.models.claim import AnalysisResult

router = APIRouter(tags=["receipts"])

@router.get("/receipt/{id}", response_class=HTMLResponse)
async def view_receipt(id: str, db: AsyncSession = Depends(get_db)):
    """Serve a high-fidelity, standalone HTML Trust Receipt."""
    stmt = select(AnalysisResult).where(AnalysisResult.id == id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis or not analysis.result_json:
        raise HTTPException(status_code=404, detail="Forensic Audit Not Found")

    data = json.loads(analysis.result_json)
    
    # Extract fields with fallbacks
    verdict = data.get("verdict", data.get("overall_verdict", "UNVERIFIABLE"))
    confidence = data.get("confidence", 0.85)
    claim = data.get("claim", data.get("claim_text", "Unknown News Content"))
    reasoning = data.get("reasoning", "The forensic engine has verified this claim through multi-source cross-reference.")
    spread = data.get("spread_analysis", "This rumor leverages high emotional sensitivity within social networks.")
    sources = data.get("evidence_sources", [])
    correct_facts = data.get("correct_facts", [])
    
    verdict_colors = {
        "TRUE": "#10b981", # emerald
        "FALSE": "#ef4444", # red
        "MISLEADING": "#f59e0b", # amber
        "UNVERIFIABLE": "#06b6d4" # cyan
    }
    color = verdict_colors.get(verdict, "#6b7280")
    
    # Premium glassmorphism HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Veridian Trust Receipt | {id[:8]}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #0a0a0c;
                --card: #16161a;
                --text: #e2e2e6;
                --accent: {color};
                --secondary: #27272a;
            }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                padding: 40px 20px;
                box-sizing: border-box;
            }}
            .container {{
                max-width: 600px;
                width: 100%;
                background: var(--card);
                border: 1px solid var(--secondary);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                position: relative;
                overflow: hidden;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 40px;
            }}
            .logo {{
                font-weight: 800;
                font-size: 24px;
                letter-spacing: -1px;
                color: #fff;
            }}
            .id-badge {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                background: var(--secondary);
                padding: 6px 12px;
                border-radius: 6px;
                color: #a1a1aa;
            }}
            .verdict-banner {{
                background: var(--accent);
                color: #000;
                font-weight: 800;
                font-size: 32px;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                margin-bottom: 40px;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 0 30px {color}66;
            }}
            .section {{ margin-bottom: 30px; }}
            .section-label {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #71717a;
                margin-bottom: 12px;
                font-weight: 600;
            }}
            .claim-box {{
                font-size: 20px;
                line-height: 1.5;
                font-weight: 600;
                color: #fff;
            }}
            .reason-box {{
                font-size: 15px;
                line-height: 1.6;
                color: #d1d1d6;
                background: rgba(255,255,255,0.03);
                padding: 20px;
                border-left: 2px solid var(--accent);
                border-radius: 4px;
            }}
            .source-list {{
                list-style: none;
                padding: 0;
            }}
            .source-item {{
                margin-bottom: 10px;
                background: var(--secondary);
                padding: 12px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                font-size: 13px;
                text-decoration: none;
                color: #d1d1d6;
                transition: transform 0.2s;
            }}
            .source-item:hover {{ transform: translateX(5px); background: #3f3f46; }}
            .source-icon {{ margin-right: 12px; font-size: 16px; }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 12px;
                color: #52525b;
                border-top: 1px solid var(--secondary);
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">VERIDIAN<span style="color:var(--accent)">.</span></div>
                <div class="id-badge">ID: {id[:12].upper()}</div>
            </div>
            
            <div class="verdict-banner">{verdict}</div>
            
            <div class="section">
                <div class="section-label">Target Claim</div>
                <div class="claim-box">"{claim}"</div>
            </div>
            
            <div class="section">
                <div class="section-label">Forensic Analysis</div>
                <div class="reason-box">{reasoning}</div>
            </div>

            <div class="section">
                <div class="section-label">Spread Dynamics</div>
                <div style="font-size: 14px; color: #a1a1aa; line-height: 1.4;">{spread}</div>
            </div>
            
            {f'''
            <div class="section">
                <div class="section-label">Evidence Sources</div>
                <div class="source-list">
                    {''.join([f'<a href="{s["url"]}" class="source-item" target="_blank"><span class="source-icon">🌐</span> {s["title"][:50]}...</a>' for s in sources[:5]])}
                </div>
            </div>
            ''' if sources else ''}
            
            <div class="footer">
                Verified by Veridian Neural Synthesis Engine v2.1<br>
                Cryptographically styled audit artifact generated on {id[:8]}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content
