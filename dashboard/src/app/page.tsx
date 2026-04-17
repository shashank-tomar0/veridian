/**
 * Dashboard — Main page with KPI cards, trending claims, and recent receipts.
 */

export default function DashboardPage() {
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
        <KPICard
          title="Analyses Today"
          value="1,284"
          delta="+12%"
          positive
          icon="📊"
        />
        <KPICard
          title="Claims Verified"
          value="847"
          delta="+8%"
          positive
          icon="✅"
        />
        <KPICard
          title="Deepfakes Detected"
          value="23"
          delta="+156%"
          positive={false}
          icon="🎭"
        />
        <KPICard
          title="Avg Response Time"
          value="2.4s"
          delta="-18%"
          positive
          icon="⚡"
        />
      </div>

      {/* ── Two-column content ──────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trending Claims */}
        <div className="lg:col-span-2">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4">Trending Claims</h2>
            <div className="space-y-3">
              <ClaimRow
                claim="Government announces free electricity for all citizens"
                verdict="FALSE"
                confidence={0.94}
                time="12m ago"
              />
              <ClaimRow
                claim="New study shows coffee prevents cancer"
                verdict="MISLEADING"
                confidence={0.78}
                time="34m ago"
              />
              <ClaimRow
                claim="Central bank confirms interest rate unchanged"
                verdict="TRUE"
                confidence={0.97}
                time="1h ago"
              />
              <ClaimRow
                claim="Viral image of flooding is from a different country"
                verdict="FALSE"
                confidence={0.91}
                time="2h ago"
              />
              <ClaimRow
                claim="Celebrity endorses cryptocurrency scheme"
                verdict="FALSE"
                confidence={0.88}
                time="3h ago"
              />
            </div>
          </div>
        </div>

        {/* Recent Trust Receipts */}
        <div className="lg:col-span-1">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4">Recent Receipts</h2>
            <div className="space-y-4">
              <ReceiptCard
                id="VR-8847"
                verdict="FALSE"
                mediaType="video"
                time="5m ago"
              />
              <ReceiptCard
                id="VR-8846"
                verdict="TRUE"
                mediaType="text"
                time="18m ago"
              />
              <ReceiptCard
                id="VR-8845"
                verdict="MISLEADING"
                mediaType="image"
                time="42m ago"
              />
              <ReceiptCard
                id="VR-8844"
                verdict="FALSE"
                mediaType="audio"
                time="1h ago"
              />
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
}: {
  id: string;
  verdict: string;
  mediaType: string;
  time: string;
}) {
  const mediaIcons: Record<string, string> = {
    text: "📝",
    image: "🖼️",
    audio: "🎙️",
    video: "🎬",
  };

  return (
    <div className="flex items-center gap-3 rounded-lg bg-gray-900/40 px-4 py-3 transition-colors hover:bg-gray-800/60 cursor-pointer">
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
