/**
 * Batch — Bulk submission UI with CSV upload and progress tracker.
 */
"use client";

import { useState } from "react";

interface BatchJob {
  id: string;
  filename: string;
  totalRows: number;
  processedRows: number;
  status: "uploading" | "processing" | "completed" | "failed";
  startedAt: string;
}

export default function BatchPage() {
  const [jobs, setJobs] = useState<BatchJob[]>([
    {
      id: "batch-001",
      filename: "election_claims_2026.csv",
      totalRows: 1250,
      processedRows: 1250,
      status: "completed",
      startedAt: "Apr 17, 2026 09:12",
    },
    {
      id: "batch-002",
      filename: "health_misinfo_q1.csv",
      totalRows: 890,
      processedRows: 547,
      status: "processing",
      startedAt: "Apr 17, 2026 10:45",
    },
  ]);

  const [dragActive, setDragActive] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    // In production: upload file, create batch job
  };

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Batch Analysis</h1>
        <p className="mt-1 text-gray-500">
          Upload CSV files for bulk misinformation analysis
        </p>
      </header>

      {/* ── Upload zone ──────────────────────────────────────────────── */}
      <div
        className={`glass-card mb-8 flex flex-col items-center justify-center p-12 border-2 border-dashed transition-all cursor-pointer ${
          dragActive
            ? "border-emerald-500/60 bg-emerald-500/5"
            : "border-gray-700 hover:border-gray-500"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        id="upload-zone"
      >
        <div className="text-4xl mb-4">📤</div>
        <p className="text-lg font-medium">
          Drop CSV file here or{" "}
          <span className="text-emerald-400 underline underline-offset-4">
            browse
          </span>
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Supports CSV with columns: text, media_url, language, category
        </p>
      </div>

      {/* ── Column mapping preview ───────────────────────────────────── */}
      <div className="glass-card mb-8 p-6">
        <h2 className="text-lg font-semibold mb-4">Column Mapping</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {["Text / Claim", "Media URL", "Language", "Category"].map(
            (col) => (
              <div key={col}>
                <label className="text-xs text-gray-500 mb-1 block">
                  {col}
                </label>
                <select
                  className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-3 py-2 text-sm text-gray-300 outline-none focus:border-emerald-500/50"
                  id={`map-${col.toLowerCase().replace(/\s/g, "-")}`}
                >
                  <option>— Auto-detect —</option>
                  <option>Column A</option>
                  <option>Column B</option>
                  <option>Column C</option>
                </select>
              </div>
            )
          )}
        </div>
        <button
          className="mt-6 rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 px-6 py-2.5 text-sm font-semibold text-gray-950 transition-all hover:opacity-90 active:scale-[0.98]"
          id="start-batch"
        >
          Start Batch Analysis
        </button>
      </div>

      {/* ── Active batches ───────────────────────────────────────────── */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold mb-4">Batch Jobs</h2>
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="flex items-center gap-4 rounded-lg bg-gray-900/40 px-5 py-4"
            >
              <StatusIcon status={job.status} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">{job.filename}</span>
                  <span className="text-xs text-gray-600">{job.id}</span>
                </div>
                <div className="mt-2">
                  <div className="meter-track">
                    <div
                      className={`meter-fill ${
                        job.status === "completed"
                          ? "bg-emerald-400"
                          : job.status === "failed"
                          ? "bg-red-400"
                          : "bg-gradient-to-r from-emerald-400 to-cyan-400"
                      }`}
                      style={{
                        width: `${(job.processedRows / job.totalRows) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="mt-1 flex justify-between text-xs text-gray-500">
                    <span>
                      {job.processedRows} / {job.totalRows} rows
                    </span>
                    <span>{job.startedAt}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/15">
          <span className="text-emerald-400">✓</span>
        </div>
      );
    case "processing":
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/15 animate-pulse-glow">
          <span className="text-cyan-400">⟳</span>
        </div>
      );
    case "failed":
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/15">
          <span className="text-red-400">✗</span>
        </div>
      );
    default:
      return (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-500/15">
          <span className="text-gray-400">↑</span>
        </div>
      );
  }
}
