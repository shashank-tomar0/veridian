/**
 * Analyze — Manual submission page for single-item analysis.
 */
"use client";

import { useState } from "react";
import Link from "next/link";

type MediaType = "text" | "image" | "audio" | "video";

export default function AnalyzePage() {
  const [mediaType, setMediaType] = useState<MediaType>("text");
  const [text, setText] = useState("");
  const [language, setLanguage] = useState("auto");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    analysis_id: string;
    status: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = typeof window !== "undefined" ? localStorage.getItem("veridian_token") : null;

      let resp;
      if (selectedFile) {
        const formData = new FormData();
        formData.append("media_file", selectedFile);
        formData.append("media_type", mediaType);
        formData.append("text", text);
        formData.append("language", language);

        resp = await fetch(`${apiUrl}/v1/analyze/upload`, {
          method: "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: formData,
        });
      } else {
        resp = await fetch(`${apiUrl}/v1/analyze`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            text: text || undefined,
            media_type: mediaType,
            language,
          }),
        });
      }

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

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-emerald-500/30">
      <main className="mx-auto max-w-7xl px-6 py-12">
        <header className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Multimodal <span className="text-emerald-500">Analysis</span>
          </h1>
          <p className="mt-4 text-lg text-gray-400 max-w-2xl">
            Upload images, audio, or video for high-fidelity misinformation detection 
            using the Veridian Reasoning Engine.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Input Section */}
          <div className="space-y-6 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl shadow-2xl">
            <div className="flex flex-wrap gap-2">
              {["text", "image", "audio", "video"].map((type) => (
                <button
                  key={type}
                  onClick={() => { setMediaType(type as MediaType); setSelectedFile(null); }}
                  className={`rounded-full px-5 py-2 text-sm font-medium transition-all duration-300 ${
                    mediaType === type
                      ? "bg-emerald-500 text-black shadow-[0_0_20px_rgba(16,185,129,0.3)]"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Claim Context / Caption
                </label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Enter the claim text or context..."
                  className="w-full rounded-xl border border-white/10 bg-black/40 p-4 text-white placeholder-gray-600 outline-none transition-all focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50"
                  rows={4}
                />
              </div>

              {mediaType !== "text" && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                    Source File
                  </label>
                  <div
                    onClick={() => document.getElementById("file-input")?.click()}
                    className={`group relative flex aspect-video cursor-pointer items-center justify-center rounded-2xl border-2 border-dashed transition-all duration-500 ${
                      selectedFile
                        ? "border-emerald-500/50 bg-emerald-500/5 shadow-[inset_0_0_40px_rgba(16,185,129,0.05)]"
                        : "border-white/10 bg-white/[0.02] hover:border-emerald-500/30 hover:bg-emerald-500/[0.02]"
                    }`}
                  >
                    <input
                      type="file"
                      id="file-input"
                      className="hidden"
                      accept={
                        mediaType === "image" ? "image/*" :
                        mediaType === "audio" ? "audio/*" :
                        "video/*"
                      }
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    />
                    <div className="text-center px-4">
                      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white/5 text-3xl transition-transform duration-500 group-hover:scale-110 group-hover:bg-emerald-500/10">
                        {selectedFile ? "📄" : (mediaType === "image" ? "🖼️" : mediaType === "audio" ? "🎙️" : "🎬")}
                      </div>
                      <p className="font-medium text-gray-300 truncate max-w-[200px] mx-auto">
                        {selectedFile ? selectedFile.name : "Choose file or drag & drop"}
                      </p>
                      <p className="mt-1 text-xs text-gray-500">
                        {mediaType.toUpperCase()} file supported
                      </p>
                      {selectedFile && (
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                          className="mt-4 rounded-full bg-red-500/10 px-4 py-1 text-[10px] font-bold uppercase tracking-widest text-red-400 transition-colors hover:bg-red-500/20"
                        >
                          Change File
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting || (mediaType !== "text" && !selectedFile && !text)}
                className="w-full rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 py-4 font-bold text-black transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] disabled:opacity-50 disabled:grayscale"
              >
                {submitting ? "ORCHESTRATING ANALYSIS..." : "START VERIFICATION"}
              </button>
            </form>
          </div>

          {/* Result Section */}
          <div className="flex items-center justify-center rounded-2xl border border-white/5 bg-gradient-to-tr from-white/[0.02] to-transparent p-12">
            {!result ? (
              <div className="text-center">
                <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-emerald-500/5 text-4xl animate-pulse">
                  ⚖️
                </div>
                <h3 className="text-xl font-semibold">Ready for Analysis</h3>
                <p className="mt-2 text-gray-500 max-w-xs mx-auto">
                  Submit text or media to trigger the multi-layer fact-checking pipeline.
                </p>
              </div>
            ) : (
              <div className="w-full space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center ring-1 ring-emerald-500/10">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500 text-black text-2xl shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                    ✓
                  </div>
                  <h3 className="text-2xl font-bold">Analysis Incoming</h3>
                  <p className="text-gray-400 mt-2">ID: <code className="text-emerald-400">{result.analysis_id.slice(0, 8)}</code></p>
                  
                  <div className="mt-8 flex flex-col gap-3">
                    <Link 
                      href={`/receipt/${result.analysis_id}`}
                      className="inline-flex items-center justify-center rounded-xl bg-white px-6 py-3 font-bold text-black transition-transform hover:scale-105"
                    >
                      View Live Trust Report →
                    </Link>
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest leading-relaxed">
                      Results appear live as reasoning concludes
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
