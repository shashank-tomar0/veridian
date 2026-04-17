/**
 * Receipt Detail Page — displays a full Trust Receipt by analysis_id.
 * Linked from extension overlay and dashboard receipt cards.
 */

import TrustReceipt from "../../components/TrustReceipt";

// Demo data — in production this fetches from /v1/analyze/{id}
const DEMO_RECEIPT = {
  analysisId: "550e8400-e29b-41d4-a716-446655440000",
  overallVerdict: "FALSE",
  overallConfidence: 0.94,
  mediaType: "text",
  processingTimeMs: 2847,
  createdAt: "Apr 17, 2026 09:12 UTC",
  claimVerdicts: [
    {
      claim_text: "Government announces free electricity for all citizens starting next month",
      verdict: "FALSE",
      confidence: 0.94,
      reasoning:
        "No official government press release, gazette notification, or ministerial statement confirms this claim. The Ministry of Power's official website and social media accounts contain no such announcement. Multiple fact-checking organizations have debunked similar viral claims in the past 30 days.",
      evidence_used: [
        {
          source_url: "https://powermin.gov.in",
          source_name: "Ministry of Power (Official)",
          excerpt: "No press release matching this claim found in the official archive for 2026.",
          relevance_score: 0.96,
        },
        {
          source_url: "https://factcheck.afp.com/doc.afp.com.34YM9P2",
          source_name: "AFP Fact Check",
          excerpt: "Similar claims about free electricity have circulated repeatedly since 2023 with no basis in government policy.",
          relevance_score: 0.89,
        },
        {
          source_url: "https://pib.gov.in",
          source_name: "Press Information Bureau",
          excerpt: "No matching press briefing or fact check from PIB confirms this announcement.",
          relevance_score: 0.84,
        },
      ],
    },
    {
      claim_text: "The initiative will cost ₹2.5 lakh crore annually",
      verdict: "UNVERIFIABLE",
      confidence: 0.62,
      reasoning:
        "While the fiscal estimate appears plausible based on India's current electricity subsidy budget, the claim cannot be verified because no such initiative exists. The figure may have been fabricated to lend credibility to the primary false claim.",
      evidence_used: [
        {
          source_url: "https://www.indiabudget.gov.in",
          source_name: "Union Budget 2026-27",
          excerpt: "Current electricity subsidy allocation is ₹97,000 crore, making a ₹2.5 lakh crore figure theoretically possible but unannounced.",
          relevance_score: 0.71,
        },
      ],
    },
  ],
};

interface ReceiptPageProps {
  params: Promise<{ id: string }>;
}

export default async function ReceiptPage({ params }: ReceiptPageProps) {
  const { id } = await params;

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* Back link */}
      <a
        href="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        ← Back to Dashboard
      </a>

      <TrustReceipt {...DEMO_RECEIPT} />

      {/* ── Detection Scores ──────────────────────────────────────── */}
      <div className="mt-8 glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Detection Scores</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <DetectionCard model="Binoculars" score={0.12} verdict="Human-written" category="text" />
          <DetectionCard model="MuRIL" score={0.34} verdict="Low manipulation" category="text" />
          <DetectionCard model="ClaimBuster" score={0.89} verdict="Check-worthy" category="claims" />
        </div>
      </div>

      {/* ── Timeline ──────────────────────────────────────────────── */}
      <div className="mt-8 glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Processing Timeline</h3>
        <div className="space-y-4">
          <TimelineItem
            step="Received"
            time="0ms"
            status="completed"
            detail="Analysis request queued"
          />
          <TimelineItem
            step="Text Analysis"
            time="342ms"
            status="completed"
            detail="Binoculars + MuRIL detectors"
          />
          <TimelineItem
            step="Claim Extraction"
            time="890ms"
            status="completed"
            detail="2 check-worthy claims identified"
          />
          <TimelineItem
            step="Evidence Retrieval"
            time="1,420ms"
            status="completed"
            detail="3 sources from Qdrant + 5 from Tavily"
          />
          <TimelineItem
            step="LLM Verification"
            time="2,340ms"
            status="completed"
            detail="Claude 3.5 Sonnet verdict generation"
          />
          <TimelineItem
            step="Receipt Generated"
            time="2,847ms"
            status="completed"
            detail="Trust Receipt VR-8847 created"
          />
        </div>
      </div>

      {/* ── Share section ─────────────────────────────────────────── */}
      <div className="mt-8 flex items-center justify-center gap-4">
        <button className="rounded-lg bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors">
          📋 Copy Link
        </button>
        <button className="rounded-lg bg-gray-800 px-5 py-2.5 text-sm font-medium text-gray-300 hover:bg-gray-700 transition-colors">
          📄 Export PDF
        </button>
        <button className="rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 px-5 py-2.5 text-sm font-semibold text-gray-950 hover:opacity-90 transition-opacity">
          🔗 Share Receipt
        </button>
      </div>
    </div>
  );
}

function DetectionCard({
  model,
  score,
  verdict,
  category,
}: {
  model: string;
  score: number;
  verdict: string;
  category: string;
}) {
  const color = score > 0.7 ? "text-red-400" : score > 0.4 ? "text-yellow-400" : "text-emerald-400";

  return (
    <div className="rounded-lg bg-gray-900/40 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{model}</span>
        <span className="text-xs text-gray-600 uppercase">{category}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>
        {(score * 100).toFixed(0)}%
      </div>
      <p className="mt-1 text-xs text-gray-500">{verdict}</p>
      <div className="mt-2 meter-track">
        <div
          className={`meter-fill ${
            score > 0.7 ? "bg-red-400" : score > 0.4 ? "bg-yellow-400" : "bg-emerald-400"
          }`}
          style={{ width: `${score * 100}%` }}
        />
      </div>
    </div>
  );
}

function TimelineItem({
  step,
  time,
  status,
  detail,
}: {
  step: string;
  time: string;
  status: string;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 text-xs">
          ✓
        </div>
        <div className="h-full w-px bg-gray-800/60 mt-1" />
      </div>
      <div className="flex-1 pb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">{step}</span>
          <span className="text-xs text-gray-600 font-mono">{time}</span>
        </div>
        <p className="mt-0.5 text-xs text-gray-500">{detail}</p>
      </div>
    </div>
  );
}
