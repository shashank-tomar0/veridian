/**
 * Analyze — Manual submission page for single-item analysis.
 */
"use client";

import { useState } from "react";

type MediaType = "text" | "image" | "audio" | "video";

export default function AnalyzePage() {
  const [mediaType, setMediaType] = useState<MediaType>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("auto");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    analysis_id: string;
    status: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = typeof window !== "undefined" ? localStorage.getItem("veridian_token") : null;

      const resp = await fetch(`${apiUrl}/v1/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          text: text || undefined,
          media_url: url || undefined,
          media_type: mediaType,
          language,
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setResult(data);
      }
    } catch (err) {
      console.error("Submit error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const mediaTypes: { type: MediaType; icon: string; label: string }[] = [
    { type: "text", icon: "📝", label: "Text" },
    { type: "image", icon: "🖼️", label: "Image" },
    { type: "audio", icon: "🎙️", label: "Audio" },
    { type: "video", icon: "🎬", label: "Video" },
  ];

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Analyze</h1>
        <p className="mt-1 text-gray-500">
          Submit content for misinformation analysis
        </p>
      </header>

      {/* Media type selector */}
      <div className="glass-card mb-6 p-2">
        <div className="flex gap-1">
          {mediaTypes.map((mt) => (
            <button
              key={mt.type}
              onClick={() => setMediaType(mt.type)}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-medium transition-all ${
                mediaType === mt.type
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "text-gray-500 hover:bg-gray-800/60 hover:text-gray-300"
              }`}
            >
              <span>{mt.icon}</span>
              {mt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <div className="glass-card p-6 space-y-5">
          {/* Text input */}
          {(mediaType === "text" || mediaType === "image") && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-400">
                {mediaType === "text" ? "Text / Claim" : "Caption"}
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={mediaType === "text" ? 6 : 3}
                className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-3 text-sm text-gray-100 placeholder-gray-600 outline-none resize-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
                placeholder={
                  mediaType === "text"
                    ? "Paste the claim, article, or social media post you want to verify..."
                    : "Optional caption or context for the image..."
                }
                id="analysis-text"
              />
            </div>
          )}

          {/* URL input */}
          {mediaType !== "text" && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-400">
                Media URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
                placeholder="https://example.com/media-file"
                id="analysis-url"
              />
              <p className="mt-1.5 text-xs text-gray-600">
                {mediaType === "image" && "Supports: JPG, PNG, WebP (max 10MB)"}
                {mediaType === "audio" && "Supports: WAV, MP3, OGG (max 50MB)"}
                {mediaType === "video" && "Supports: MP4, WebM, AVI (max 200MB)"}
              </p>
            </div>
          )}

          {/* File upload */}
          {mediaType !== "text" && (
            <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-gray-700 p-8 hover:border-gray-500 transition-colors cursor-pointer">
              <div className="text-center">
                <span className="text-3xl block mb-2">
                  {mediaType === "image" ? "🖼️" : mediaType === "audio" ? "🎙️" : "🎬"}
                </span>
                <p className="text-sm text-gray-400">
                  Drop file here or{" "}
                  <span className="text-emerald-400 underline">browse</span>
                </p>
              </div>
            </div>
          )}

          {/* Language */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-400">
              Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2.5 text-sm text-gray-300 outline-none focus:border-emerald-500/50 transition-all"
              id="analysis-language"
            >
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="es">Spanish</option>
              <option value="ar">Arabic</option>
              <option value="fr">French</option>
              <option value="pt">Portuguese</option>
              <option value="zh">Chinese</option>
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting || (!text && !url)}
            className="w-full rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 py-3 text-sm font-semibold text-gray-950 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-40"
            id="submit-analysis"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-pulse-glow">⟳</span> Submitting...
              </span>
            ) : (
              "Submit for Analysis"
            )}
          </button>
        </div>
      </form>

      {/* Result card */}
      {result && (
        <div className="mt-6 glass-card p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/15">
              <span className="text-emerald-400">✓</span>
            </div>
            <div>
              <h3 className="text-sm font-semibold">Analysis Queued</h3>
              <p className="text-xs text-gray-500">
                Processing will complete in 2-30 seconds
              </p>
            </div>
          </div>
          <div className="rounded-lg bg-gray-900/60 p-3 font-mono text-xs text-gray-400">
            <span className="text-gray-600">analysis_id:</span>{" "}
            {result.analysis_id}
            <br />
            <span className="text-gray-600">status:</span>{" "}
            <span className="text-emerald-400">{result.status}</span>
          </div>
          <a
            href={`/receipt/${result.analysis_id}`}
            className="mt-3 inline-block text-sm text-emerald-400 hover:underline"
          >
            View Trust Receipt →
          </a>
        </div>
      )}
    </div>
  );
}
