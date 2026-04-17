/**
 * Overlay — React component rendered on flagged elements.
 * Shows a shield icon with color-coded verdict; click opens full Trust Receipt.
 */

import { useState } from "react";

interface OverlayProps {
  verdict: string;
  confidence: number;
  claimText: string;
  analysisId: string;
}

export default function VeridianOverlay({
  verdict,
  confidence,
  claimText,
  analysisId,
}: OverlayProps) {
  const [expanded, setExpanded] = useState(false);

  const config: Record<string, { color: string; bg: string; icon: string }> = {
    TRUE: { color: "#34d399", bg: "rgba(52,211,153,0.1)", icon: "🛡️" },
    FALSE: { color: "#f87171", bg: "rgba(248,113,113,0.1)", icon: "🛡️" },
    MISLEADING: { color: "#fbbf24", bg: "rgba(251,191,36,0.1)", icon: "🛡️" },
    UNVERIFIABLE: { color: "#94a3b8", bg: "rgba(148,163,184,0.1)", icon: "🛡️" },
  };

  const c = config[verdict] || config.UNVERIFIABLE;

  return (
    <div
      style={{
        position: "fixed",
        fontFamily: "Inter, system-ui, sans-serif",
        zIndex: 99999,
      }}
    >
      {/* Shield icon */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: 32,
          height: 32,
          borderRadius: "50%",
          border: `2px solid ${c.color}`,
          background: c.bg,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 16,
          transition: "transform 0.15s ease",
        }}
        title={`Veridian: ${verdict}`}
      >
        {c.icon}
      </button>

      {/* Expanded popup */}
      {expanded && (
        <div
          style={{
            position: "absolute",
            top: 40,
            right: 0,
            width: 320,
            background: "#0f0f14",
            border: `1px solid ${c.color}33`,
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 16px 48px rgba(0,0,0,0.5)",
            color: "#e5e7eb",
            fontSize: 13,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <span style={{ color: c.color, fontWeight: 700, fontSize: 14 }}>
              {verdict}
            </span>
            <span style={{ color: "#6b7280", fontSize: 12 }}>
              {(confidence * 100).toFixed(0)}% confidence
            </span>
          </div>

          <p style={{ color: "#9ca3af", lineHeight: 1.5, marginBottom: 12 }}>
            "{claimText}"
          </p>

          {/* Confidence bar */}
          <div
            style={{
              height: 4,
              borderRadius: 999,
              background: "rgba(255,255,255,0.06)",
              overflow: "hidden",
              marginBottom: 12,
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${confidence * 100}%`,
                background: c.color,
                borderRadius: 999,
                transition: "width 0.4s ease",
              }}
            />
          </div>

          <a
            href={`http://localhost:3000/receipt/${analysisId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "block",
              textAlign: "center",
              padding: "8px 0",
              background: `${c.color}20`,
              borderRadius: 8,
              color: c.color,
              textDecoration: "none",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            View Full Trust Receipt →
          </a>
        </div>
      )}
    </div>
  );
}
