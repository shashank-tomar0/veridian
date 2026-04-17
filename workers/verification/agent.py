import httpx
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tavily import TavilyClient
import asyncio
import json

from backend.config import settings
from backend.db.qdrant import qdrant_service

class AgentState(TypedDict):
    analysis_id: str
    transcribed_text: str
    language: str
    extracted_claims: List[Dict[str, Any]]
    current_claim_index: int
    verdicts: List[Dict[str, Any]]

class VerificationAgent:
    def __init__(self):
        # We use a fast model from Groq
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile", 
            api_key=settings.groq_api_key,
            temperature=0.0
        )
        self.tavily_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("extract_claims", self.extract_claims)
        workflow.add_node("process_claim", self.process_claim)
        workflow.add_node("store_results", self.store_results)

        workflow.set_entry_point("extract_claims")
        workflow.add_edge("extract_claims", "process_claim")
        
        # We loop over extracted claims inside `process_claims` or via conditional edges.
        # Simplification: `process_claim` handles the orchestration loop array mapping.
        workflow.add_conditional_edges(
            "process_claim",
            self.should_continue,
            {
                "continue": "process_claim",
                "done": "store_results"
            }
        )
        
        workflow.add_edge("store_results", END)

        return workflow.compile()

    async def extract_claims(self, state: AgentState) -> dict:
        sys_msg = SystemMessage(content="You are a strict exact-data extractor. Extract falsifiable claims from the text. Output plain JSON list of objects: [{'claim_text': '...', 'context': '...'}]")
        h_msg = HumanMessage(content=f"Text: {state['transcribed_text']}\nLanguage: {state['language']}")
        
        resp = await self.llm.ainvoke([sys_msg, h_msg])
        try:
            claims = json.loads(resp.content)
        except Exception:
            claims = [{"claim_text": state["transcribed_text"], "context": "auto"}]
            
        return {"extracted_claims": claims, "current_claim_index": 0, "verdicts": []}

    async def _score_worthiness(self, text: str) -> float:
        if not settings.huggingface_hub_token:
            return 1.0
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(api_key=settings.huggingface_hub_token)
            
            # Using a more standard approach for HF Inference API
            result = client.text_classification(
                text, 
                model="whispAI/ClaimBuster-DeBERTaV2"
            )
            
            if result:
                for r in result:
                    label = str(r.get("label", "")).upper()
                    if label in ["CFS", "CHECK-WORTHY", "LABEL_1"]:
                        return r.get("score", 0.0)
                return result[0].get("score", 0.0)
                
        except Exception as e:
            # FALLBACK: Use Groq LLM to estimate check-worthiness if HF is down
            try:
                sys_msg = SystemMessage(content="Rate the check-worthiness (falsifiability) of the text from 0.0 to 1.0. Output ONLY the number.")
                resp = await self.llm.ainvoke([sys_msg, HumanMessage(content=text)])
                return float(resp.content.strip())
            except:
                pass
        return 0.5

    async def _retrieve_evidence(self, text: str) -> List[str]:
        evidence = []
        if self.tavily_client:
            try:
                # Optimized search with higher result count for better provenance tracing
                res = self.tavily_client.search(query=text, search_depth="advanced", max_results=5)
                for r in res.get("results", []):
                    title = r.get("title", "No Title")
                    date = r.get("published_date", "No Date")
                    evidence.append(f"Source [{r['url']}] Title: {title} | Date: {date} | Content: {r['content']}")
            except Exception:
                pass
        return evidence

    async def process_claim(self, state: AgentState) -> dict:
        idx = state["current_claim_index"]
        claim = state["extracted_claims"][idx]
        text = claim.get("claim_text", "")
        
        # 1. Score Worthiness
        score = await self._score_worthiness(text)
        
        if score < 0.6: # Relaxed threshold for local testing
            verdict = {
                "claim": text,
                "verdict": "UNVERIFIABLE",
                "confidence": 1.0,
                "reasoning": f"Claimworthiness score too low ({round(score, 2)}). Sentence might be an opinion or non-factual.",
                "evidence_used": []
            }
        else:
            # 2. Retrieve Evidence
            evidence = await self._retrieve_evidence(text)
            
            # 3. LLM Verification (Layer 3-5 reasoning)
            sys_msg = SystemMessage(content="""You are an elite, production-grade misinformation intelligence analyst.
Your task is to analyze the claim against the provided evidence to produce a "Trust Receipt."

REASONING GUIDELINES:
- ORIGIN (Layer 4): Look for the EARLIEST date or platform mentioned in the evidence. If the evidence mentions a specific bill (e.g., "Women Reservation Bill 2023"), trace its inception.
- CONTEXT (Layer 5): Explain WHY this is trending (e.g., "Parliament Special Session", "Upcoming State Elections").
- VERDICT: Must be TRUE, FALSE, MISLEADING, or UNVERIFIABLE.

Output JSON with EXACTLY these keys:
{
  "verdict": "string",
  "confidence": float (0.0-1.0),
  "reasoning": "Detailed breakdown of facts",
  "origin": "e.g. First surfaced in Sep 2023 via LiveMint and Official Gazette.",
  "context": "e.g. Circulating due to the 128th Constitutional Amendment Bill discussions.",
  "whatsapp_response": "A 3-5 sentence paragraph suitable for WhatsApp forwarding, with citations embedded like [LiveMint](url)."
}""")
            h_msg = HumanMessage(content=f"Claim: {text}\n\nEvidence:\n" + "\n".join(evidence))
            
            resp = await self.llm.ainvoke([sys_msg, h_msg])
            
            try:
                verdict = json.loads(resp.content)
                verdict["claim"] = text
                verdict["evidence_sources"] = evidence 
            except Exception:
                verdict = {
                    "claim": text, 
                    "verdict": "UNVERIFIABLE", 
                    "confidence": 0.0, 
                    "reasoning": "Analysis parsing failed",
                    "origin": "Unknown",
                    "context": "General misinformation",
                    "whatsapp_response": "We are currently verifying this claim. Please rely on official government sources.",
                    "evidence_sources": evidence
                }
                
        verdicts = state["verdicts"][:]
        verdicts.append(verdict)
        
        return {"verdicts": verdicts, "current_claim_index": idx + 1}

    def should_continue(self, state: AgentState) -> str:
        if state["current_claim_index"] >= len(state["extracted_claims"]):
            return "done"
        return "continue"

    async def store_results(self, state: AgentState) -> dict:
        from backend.models.base import AsyncSessionLocal
        from backend.models.claim import Claim, AnalysisResult
        
        async with AsyncSessionLocal() as session:
            try:
                # Create Analysis Entry
                analysis = AnalysisResult(
                    id=state["analysis_id"],
                    media_hash="local_text",
                    media_type="text",
                    status="completed",
                    completed=True
                )
                session.add(analysis)
                
                # Create Individual Claim Entries
                for v in state["verdicts"]:
                    claim_obj = Claim(
                        original_text=v["claim"],
                        verdict=v["verdict"],
                        confidence=v["confidence"],
                        reasoning=v["reasoning"],
                        # We store the evidence used as a newline separated string in reasoning or metadata if needed
                    )
                    session.add(claim_obj)
                
                await session.commit()
            except Exception as e:
                print(f"Error persisting to SQLite: {e}")
                await session.rollback()
        
        return {"completed": True}

# Singleton instance
verification_agent = VerificationAgent()
