/**
 * TrustReceipt — Rich display component for verdict cards.
 */

interface Evidence {
  source_url?: string;
  source_name?: string;
  excerpt: string;
  relevance_score?: number;
}

interface ClaimVerdict {
  claim_text: string;
  verdict: string;
  confidence: number;
  reasoning: string;
  evidence_used: Evidence[];
}

interface TrustReceiptProps {
  analysisId: string;
  overallVerdict: string;
  overallConfidence: number;
  claimVerdicts: ClaimVerdict[];
  mediaType: string;
  processingTimeMs: number;
  createdAt: string;
}

export default function TrustReceipt({
  analysisId,
  overallVerdict,
  overallConfidence,
  claimVerdicts,
  mediaType,
  processingTimeMs,
  createdAt,
}: TrustReceiptProps) {
  const verdictConfig: Record<string, { color: string; bg: string; icon: string; border: string }> = {
    TRUE: { color: "text-emerald-400", bg: "bg-emerald-500/10", icon: "✅", border: "border-emerald-500/30" },
    FALSE: { color: "text-red-400", bg: "bg-red-500/10", icon: "❌", border: "border-red-500/30" },
    MISLEADING: { color: "text-yellow-400", bg: "bg-yellow-500/10", icon: "⚠️", border: "border-yellow-500/30" },
    UNVERIFIABLE: { color: "text-slate-400", bg: "bg-slate-500/10", icon: "❓", border: "border-slate-500/30" },
  };

  const vc = verdictConfig[overallVerdict] || verdictConfig.UNVERIFIABLE;

  const mediaIcons: Record<string, string> = {
    text: "📝", image: "🖼️", audio: "🎙️", video: "🎬",
  };

  return (
    <div className="glass-card overflow-hidden max-w-2xl mx-auto">
      {/* ── Verdict header bar ──────────────────────────────────────── */}
      <div className={`${vc.bg} border-b ${vc.border} px-6 py-5`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{vc.icon}</span>
            <div>
              <h2 className={`text-xl font-bold ${vc.color}`}>
                {overallVerdict}
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Trust Receipt #{analysisId.slice(0, 8)}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Confidence</span>
              <span className={`text-lg font-bold ${vc.color}`}>
                {(overallConfidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="mt-1 w-24">
              <div className="meter-track">
                <div
                  className={`meter-fill ${
                    overallVerdict === "TRUE" ? "bg-emerald-400" :
                    overallVerdict === "FALSE" ? "bg-red-400" :
                    overallVerdict === "MISLEADING" ? "bg-yellow-400" :
                    "bg-slate-400"
                  }`}
                  style={{ width: `${overallConfidence * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Claim verdicts ──────────────────────────────────────────── */}
      <div className="p-6 space-y-4">
        {claimVerdicts.map((cv, i) => (
          <div key={i} className="rounded-lg bg-gray-900/40 p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <p className="text-sm font-medium leading-snug">
                "{cv.claim_text}"
              </p>
              <span
                className={`shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                  cv.verdict === "TRUE" ? "badge-true" :
                  cv.verdict === "FALSE" ? "badge-false" :
                  cv.verdict === "MISLEADING" ? "badge-misleading" :
                  "badge-unverifiable"
                }`}
              >
                {cv.verdict}
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              {cv.reasoning}
            </p>

            {/* Evidence cards */}
            {cv.evidence_used.length > 0 && (
              <div className="mt-3 space-y-2">
                <span className="text-xs text-gray-600 font-semibold uppercase tracking-wider">
                  Evidence
                </span>
                {cv.evidence_used.map((ev, j) => (
                  <div
                    key={j}
                    className="rounded border border-gray-800/60 bg-gray-950/50 p-3"
                  >
                    <p className="text-xs text-gray-400">{ev.excerpt}</p>
                    {ev.source_url && (
                      <a
                        href={ev.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-block text-xs text-emerald-400 hover:underline"
                      >
                        {ev.source_name || ev.source_url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ── Footer metadata ────────────────────────────────────────── */}
      <div className="border-t border-gray-800/60 px-6 py-3 flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center gap-4">
          <span>{mediaIcons[mediaType] || "📄"} {mediaType}</span>
          <span>⚡ {processingTimeMs}ms</span>
        </div>
        <div className="flex items-center gap-3">
          <span>{createdAt}</span>
          <button
            className="rounded-md bg-gray-800 px-3 py-1 text-gray-400 hover:text-gray-200 transition-colors"
            id="share-receipt"
          >
            Share
          </button>
        </div>
      </div>
    </div>
  );
}
