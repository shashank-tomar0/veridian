"use client";

import { useEffect, useState } from "react";

/**
 * Dashboard — Main page with KPI cards, trending claims, and recent receipts.
 * Now connected to the actual Veridian Backend.
 */

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSummary() {
      try {
        const res = await fetch("http://localhost:8000/v1/public/dashboard/summary");
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-8 animate-pulse">
         <div className="h-8 w-48 bg-gray-800 rounded mb-10"></div>
         <div className="grid gap-5 grid-cols-4 mb-10">
            {[1,2,3,4].map(i => <div key={i} className="h-24 bg-gray-900 rounded-xl"></div>)}
         </div>
         <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 h-64 bg-gray-900 rounded-xl"></div>
            <div className="lg:col-span-1 h-64 bg-gray-900 rounded-xl"></div>
         </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* ── Hero ────────────────────────────────────────────────────── */}
      <header className="mb-10">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-gray-500">
          Real-time misinformation monitoring and response
        </p>
      </header>

      {/* ── KPI Cards ───────────────────────────────────────────────── */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-10">
        {data?.kpis?.map((kpi: any, idx: number) => (
          <KPICard
            key={idx}
            title={kpi.title}
            value={kpi.value}
            delta={kpi.delta}
            positive={kpi.positive}
            icon={kpi.icon}
          />
        ))}
      </div>

      {/* ── Two-column content ──────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trending Claims */}
        <div className="lg:col-span-2">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4">Trending Claims</h2>
            <div className="space-y-3">
              {data?.trending_claims?.length > 0 ? (
                data.trending_claims.map((c: any) => (
                  <ClaimRow
                    key={c.id}
                    claim={c.claim}
                    verdict={c.verdict}
                    confidence={c.confidence}
                    time={c.time}
                  />
                ))
              ) : (
                <p className="text-sm text-gray-500 py-4 italic">No claims processed yet. Send a claim to the bot!</p>
              )}
            </div>
          </div>
        </div>

        {/* Recent Trust Receipts */}
        <div className="lg:col-span-1">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Receipts</h2>
            <div className="space-y-4">
              {data?.recent_receipts?.length > 0 ? (
                data.recent_receipts.map((r: any) => (
                  <ReceiptCard
                    key={r.real_id}
                    id={r.id}
                    verdict={r.verdict}
                    mediaType={r.mediaType}
                    time={r.time}
                    onLink={() => window.location.href = `/receipt/${r.real_id}`}
                  />
                ))
              ) : (
                <p className="text-sm text-gray-500 py-4 italic">No receipts generated yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function KPICard({
  title,
  value,
  delta,
  positive,
  icon,
}: {
  title: string;
  value: string;
  delta: string;
  positive: boolean;
  icon: string;
}) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-500">{title}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <span
        className={`mt-1 inline-block text-xs font-medium ${
          positive ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {delta} vs yesterday
      </span>
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
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {verdict}
    </span>
  );
}

function ClaimRow({
  claim,
  verdict,
  confidence,
  time,
}: {
  claim: string;
  verdict: string;
  confidence: number;
  time: string;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg bg-gray-900/40 px-4 py-3 transition-colors hover:bg-gray-800/60">
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">{claim}</p>
        <div className="mt-1.5 flex items-center gap-3">
          <VerdictBadge verdict={verdict} />
          <div className="w-20">
            <div className="meter-track">
              <div
                className="meter-fill bg-gradient-to-r from-emerald-400 to-cyan-400"
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </div>
          <span className="text-xs text-gray-600">{(confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
      <span className="text-xs text-gray-600 whitespace-nowrap">{time}</span>
    </div>
  );
}

function ReceiptCard({
  id,
  verdict,
  mediaType,
  time,
  onLink,
}: {
  id: string;
  verdict: string;
  mediaType: string;
  time: string;
  onLink?: () => void;
}) {
  const mediaIcons: Record<string, string> = {
    text: "📝",
    image: "🖼️",
    audio: "🎙️",
    video: "🎬",
  };

  return (
    <div 
      onClick={onLink}
      className="flex items-center gap-3 rounded-lg bg-gray-900/40 px-4 py-3 transition-colors hover:bg-gray-800/60 cursor-pointer border border-transparent hover:border-emerald-500/20"
    >
      <span className="text-lg">{mediaIcons[mediaType] || "📄"}</span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{id}</span>
          <VerdictBadge verdict={verdict} />
        </div>
        <span className="text-xs text-gray-600">{time}</span>
      </div>
    </div>
  );
}
