/**
 * Claims — Paginated claim browser with filters.
 */

export default function ClaimsPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Claims Browser</h1>
        <p className="mt-1 text-gray-500">
          Search and filter verified claims across all languages and categories
        </p>
      </header>

      {/* ── Filters ──────────────────────────────────────────────────── */}
      <div className="glass-card mb-6 p-4">
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search claims..."
            className="flex-1 min-w-[200px] rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
            id="claims-search"
          />
          <select
            className="rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2 text-sm text-gray-300 outline-none focus:border-emerald-500/50"
            id="verdict-filter"
          >
            <option value="">All Verdicts</option>
            <option value="TRUE">✅ True</option>
            <option value="FALSE">❌ False</option>
            <option value="MISLEADING">⚠️ Misleading</option>
            <option value="UNVERIFIABLE">❓ Unverifiable</option>
          </select>
          <select
            className="rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2 text-sm text-gray-300 outline-none focus:border-emerald-500/50"
            id="language-filter"
          >
            <option value="">All Languages</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="es">Spanish</option>
            <option value="ar">Arabic</option>
          </select>
          <input
            type="date"
            className="rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2 text-sm text-gray-300 outline-none focus:border-emerald-500/50"
            id="date-filter"
          />
        </div>
      </div>

      {/* ── Claims Table ─────────────────────────────────────────────── */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800/60 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              <th className="px-6 py-4">Claim</th>
              <th className="px-6 py-4 w-28">Verdict</th>
              <th className="px-6 py-4 w-28">Confidence</th>
              <th className="px-6 py-4 w-24">Language</th>
              <th className="px-6 py-4 w-32">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/40">
            {MOCK_CLAIMS.map((claim, i) => (
              <tr
                key={i}
                className="transition-colors hover:bg-gray-800/30 cursor-pointer"
              >
                <td className="px-6 py-4">
                  <p className="text-sm font-medium leading-snug">
                    {claim.text}
                  </p>
                  <p className="mt-1 text-xs text-gray-600 truncate max-w-lg">
                    {claim.reasoning}
                  </p>
                </td>
                <td className="px-6 py-4">
                  <VerdictBadge verdict={claim.verdict} />
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-16 meter-track">
                      <div
                        className="meter-fill bg-gradient-to-r from-emerald-400 to-cyan-400"
                        style={{ width: `${claim.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {(claim.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-400">
                  {claim.language}
                </td>
                <td className="px-6 py-4 text-xs text-gray-500">
                  {claim.date}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ───────────────────────────────────────────────── */}
      <div className="mt-6 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          Showing 1–10 of 847 claims
        </span>
        <div className="flex gap-1">
          {[1, 2, 3, "...", 85].map((p, i) => (
            <button
              key={i}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                p === 1
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "text-gray-500 hover:bg-gray-800/60 hover:text-gray-300"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const cls =
    verdict === "TRUE"
      ? "badge-true"
      : verdict === "FALSE"
      ? "badge-false"
      : verdict === "MISLEADING"
      ? "badge-misleading"
      : "badge-unverifiable";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}
    >
      {verdict}
    </span>
  );
}

const MOCK_CLAIMS = [
  { text: "Government announces free electricity nationwide", verdict: "FALSE", confidence: 0.94, language: "EN", date: "Apr 17, 2026", reasoning: "No official government source confirms this claim." },
  { text: "New study proves coffee prevents all types of cancer", verdict: "MISLEADING", confidence: 0.78, language: "EN", date: "Apr 17, 2026", reasoning: "The study only showed minor correlation, not causation." },
  { text: "Central bank confirms interest rate will remain unchanged", verdict: "TRUE", confidence: 0.97, language: "EN", date: "Apr 17, 2026", reasoning: "Confirmed via official press release." },
  { text: "Viral flood photo is from Bangladesh, not current location", verdict: "FALSE", confidence: 0.91, language: "HI", date: "Apr 16, 2026", reasoning: "Reverse image search traces photo to 2019 Bangladesh floods." },
  { text: "Celebrity allegedly endorses new crypto investment platform", verdict: "FALSE", confidence: 0.88, language: "EN", date: "Apr 16, 2026", reasoning: "Celebrity's official accounts deny any endorsement." },
  { text: "Vaccine reduces hospitalization by 90%", verdict: "TRUE", confidence: 0.95, language: "EN", date: "Apr 16, 2026", reasoning: "Multiple peer-reviewed studies confirm this statistic." },
  { text: "Earthquake predicted for major city next week", verdict: "FALSE", confidence: 0.99, language: "ES", date: "Apr 15, 2026", reasoning: "No seismological agency has issued any such prediction." },
  { text: "AI-generated deepfake of politician goes viral", verdict: "TRUE", confidence: 0.92, language: "EN", date: "Apr 15, 2026", reasoning: "Forensic analysis confirms deepfake manipulation." },
];
