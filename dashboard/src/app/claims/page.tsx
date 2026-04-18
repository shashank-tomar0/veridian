"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

/**
 * Claims — Active Intelligence Log.
 * Real-time feed of all queries processed by the Veridian Bot.
 */

export default function ClaimsPage() {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function fetchClaims() {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/v1/public/dashboard/explorer?page=${page}&search=${search}`);
        const json = await res.json();
        setData(json.results || []);
        setTotal(json.total_count || 0);
      } catch (err) {
        console.error("Explorer fetch failed:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchClaims();
  }, [page, search]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-1">
           <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-glow"></div>
           <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest">Live Intelligence Feed</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Intelligence Log</h1>
        <p className="mt-1 text-gray-500">
          Historical archive of all verified forensic queries
        </p>
      </header>

      {/* ── Search ─────────────────────────────────────────────────── */}
      <div className="glass-card mb-6 p-4">
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search claim content or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 min-w-[200px] rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-emerald-500/50 transition-all"
          />
        </div>
      </div>

      {/* ── Claims Table ─────────────────────────────────────────────── */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-20 text-center animate-pulse text-gray-600">Syncing with Forensic Database...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800/60 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                <th className="px-6 py-4">Forensic Query</th>
                <th className="px-6 py-4 w-28 text-center">Verdict</th>
                <th className="px-6 py-4 w-28">Confidence</th>
                <th className="px-6 py-4 w-32">Temporal Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/40">
              {data.map((c, i) => (
                <Link key={c.id} href={`/receipt/${c.id}`} legacyBehavior>
                  <tr className="transition-colors hover:bg-gray-800/30 cursor-pointer group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-mono text-gray-600 group-hover:text-emerald-500/70 transition-colors uppercase">{c.display_id}</span>
                        <span className="text-[10px] bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">{c.media_type}</span>
                      </div>
                      <p className="text-sm font-medium leading-snug">
                        {c.claim}
                      </p>
                      <p className="mt-1 text-xs text-gray-600 truncate max-w-lg">
                        {c.context} — {c.reasoning}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <VerdictBadge verdict={c.verdict} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 meter-track">
                          <div
                            className={`meter-fill ${c.verdict === 'FALSE' ? 'bg-red-400' : 'bg-emerald-400'}`}
                            style={{ width: `${c.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {(c.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {c.date}
                    </td>
                  </tr>
                </Link>
              ))}
              {data.length === 0 && (
                <tr>
                   <td colSpan={4} className="p-20 text-center text-gray-500 italic">No forensic records found matching this search.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Pagination ───────────────────────────────────────────────── */}
      <div className="mt-6 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          Total Queries: {total}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 disabled:opacity-30"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={data.length < 20}
            className="rounded-lg px-4 py-2 text-sm text-gray-400 hover:bg-gray-800 disabled:opacity-30"
          >
            Next Page
          </button>
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
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-tight uppercase ${cls}`}
    >
      {verdict}
    </span>
  );
}
