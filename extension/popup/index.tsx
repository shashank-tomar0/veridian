/**
 * Extension popup — page trust summary, recent flags, manual submit.
 */

import { useState } from "react";

interface FlagEntry {
  text: string;
  verdict: string;
  confidence: number;
}

function Popup() {
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [flags] = useState<FlagEntry[]>([
    { text: "Free electricity for all citizens", verdict: "FALSE", confidence: 0.94 },
    { text: "New miracle cure for diabetes", verdict: "MISLEADING", confidence: 0.78 },
  ]);

  const handleSubmit = async () => {
    setSubmitting(true);
    // In production: POST current page URL to Veridian API
    setTimeout(() => setSubmitting(false), 2000);
  };

  const verdictColors: Record<string, string> = {
    TRUE: "#34d399",
    FALSE: "#f87171",
    MISLEADING: "#fbbf24",
    UNVERIFIABLE: "#94a3b8",
  };

  return (
    <div
      style={{
        width: 360,
        fontFamily: "Inter, system-ui, sans-serif",
        background: "#0a0a0f",
        color: "#e5e7eb",
        padding: 20,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "linear-gradient(135deg, #34d399, #06b6d4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: 14,
            color: "#0a0a0f",
          }}
        >
          V
        </div>
        <div>
          <h1 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Veridian</h1>
          <p style={{ fontSize: 11, color: "#6b7280", margin: 0 }}>
            Misinformation Shield
          </p>
        </div>
      </div>

      {/* Page trust score */}
      <div
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 12,
          padding: 16,
          marginBottom: 16,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: "#9ca3af" }}>Page Trust Score</span>
          <span style={{ fontSize: 18, fontWeight: 700, color: "#fbbf24" }}>72%</span>
        </div>
        <div
          style={{
            height: 4,
            borderRadius: 999,
            background: "rgba(255,255,255,0.06)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: "72%",
              background: "linear-gradient(90deg, #fbbf24, #f59e0b)",
              borderRadius: 999,
            }}
          />
        </div>
        <p style={{ fontSize: 10, color: "#6b7280", marginTop: 6 }}>
          2 claims flagged on this page
        </p>
      </div>

      {/* Recent flags */}
      <div style={{ marginBottom: 16 }}>
        <h3
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: "#6b7280",
            textTransform: "uppercase",
            letterSpacing: 1,
            marginBottom: 8,
          }}
        >
          Flagged Content
        </h3>
        {flags.map((flag, i) => (
          <div
            key={i}
            style={{
              background: "rgba(255,255,255,0.02)",
              borderRadius: 8,
              padding: 10,
              marginBottom: 6,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: verdictColors[flag.verdict] || "#94a3b8",
                flexShrink: 0,
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <p
                style={{
                  fontSize: 12,
                  margin: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {flag.text}
              </p>
              <span style={{ fontSize: 10, color: verdictColors[flag.verdict] }}>
                {flag.verdict} · {(flag.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Manual submit */}
      <div>
        <h3
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: "#6b7280",
            textTransform: "uppercase",
            letterSpacing: 1,
            marginBottom: 8,
          }}
        >
          Manual Check
        </h3>
        <div style={{ display: "flex", gap: 6 }}>
          <input
            type="text"
            placeholder="Paste URL or claim..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={{
              flex: 1,
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "rgba(255,255,255,0.03)",
              padding: "8px 12px",
              fontSize: 12,
              color: "#e5e7eb",
              outline: "none",
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              borderRadius: 8,
              background: "linear-gradient(135deg, #34d399, #06b6d4)",
              color: "#0a0a0f",
              padding: "8px 16px",
              fontSize: 12,
              fontWeight: 600,
              border: "none",
              cursor: "pointer",
              opacity: submitting ? 0.6 : 1,
            }}
          >
            {submitting ? "..." : "Check"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Popup;
