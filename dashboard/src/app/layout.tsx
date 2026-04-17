import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Veridian — Misinformation Response Engine",
  description:
    "AI-native multimodal misinformation detection and counter-narrative platform for journalists and fact-checkers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <div className="min-h-screen bg-gray-950 text-gray-100">
          {/* ── Navigation ─────────────────────────────────────────────── */}
          <nav className="sticky top-0 z-50 border-b border-gray-800/60 bg-gray-950/80 backdrop-blur-xl">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
              <a href="/" className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center text-sm font-bold text-gray-950">
                  V
                </div>
                <span className="text-lg font-semibold tracking-tight">
                  Veridian
                </span>
              </a>

              <div className="hidden md:flex items-center gap-1">
                <NavLink href="/" label="Dashboard" />
                <NavLink href="/analyze" label="Analyze" />
                <NavLink href="/claims" label="Claims" />
                <NavLink href="/graph" label="Graph" />
                <NavLink href="/batch" label="Batch" />
              </div>

              <div className="flex items-center gap-3">
                <a
                  href="/login"
                  className="rounded-lg bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 px-4 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/30 transition-colors"
                >
                  Sign In
                </a>
              </div>
            </div>
          </nav>

          {/* ── Main content ───────────────────────────────────────────── */}
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="rounded-lg px-3 py-2 text-sm font-medium text-gray-400 transition-colors hover:bg-gray-800/60 hover:text-gray-100"
    >
      {label}
    </a>
  );
}
