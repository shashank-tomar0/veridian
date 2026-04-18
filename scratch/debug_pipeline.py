import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from workers.verification.agent import verification_agent

async def test_pipeline():
    print("--- START PIPELINE DEBUG ---")
    test_text = "pm modi is india's pm"
    
    initial_state = {
        "analysis_id": "debug-test-123",
        "transcribed_text": test_text,
        "language": "en",
        "extracted_claims": [],
        "current_claim_index": 0,
        "verdicts": []
    }
    
    try:
        final_state = await verification_agent.workflow.ainvoke(initial_state)
        print("\n--- FINAL VERDICT ---")
        for v in final_state.get("verdicts", []):
            print(f"Claim: {v['claim']}")
            print(f"Verdict: {v['verdict']} ({v.get('confidence', 0)*100}%)")
            print(f"Reasoning: {v.get('reasoning')}")
            print(f"Origin: {v.get('origin')}")
    except Exception as e:
        print(f"\n--- FATAL ERROR ---\n{e}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
