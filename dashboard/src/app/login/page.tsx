/**
 * Login — JWT authentication page for the journalist dashboard.
 */
"use client";

import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/v1/auth/login" : "/v1/auth/register";
      const body =
        mode === "login"
          ? { email, password }
          : { email, password, full_name: email.split("@")[0] };

      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `Error: ${resp.status}`);
      }

      const data = await resp.json();

      if (mode === "login" && data.access_token) {
        localStorage.setItem("veridian_token", data.access_token);
        localStorage.setItem("veridian_refresh", data.refresh_token);
        window.location.href = "/";
      } else if (mode === "register") {
        setMode("login");
        setError("");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-6">
      <div className="w-full max-w-md">
        {/* Logo + title */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400 to-cyan-500">
            <span className="text-2xl font-bold text-gray-950">V</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {mode === "login"
              ? "Sign in to your Veridian dashboard"
              : "Join the Veridian fact-checking network"}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="glass-card p-6 space-y-5">
          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block text-sm font-medium text-gray-400"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
              placeholder="journalist@newsorg.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-gray-400"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-900/60 px-4 py-2.5 text-sm text-gray-100 placeholder-gray-600 outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30 transition-all"
              placeholder="Min. 8 characters"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 py-2.5 text-sm font-semibold text-gray-950 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
            id="auth-submit"
          >
            {loading
              ? "Processing..."
              : mode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
              className="text-sm text-gray-500 hover:text-emerald-400 transition-colors"
            >
              {mode === "login"
                ? "Don't have an account? Register"
                : "Already have an account? Sign in"}
            </button>
          </div>
        </form>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-gray-700">
          Protected by Veridian Security · TLS 1.3 · AES-256
        </p>
      </div>
    </div>
  );
}
