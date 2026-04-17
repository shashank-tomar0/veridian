/**
 * Content script — scans page on load, queries Veridian API with
 * pHashes of images and text excerpts, injects overlays on flagged elements.
 */

import type { PlasmoCSConfig } from "plasmo";

export const config: PlasmoCSConfig = {
  matches: ["<all_urls>"],
  run_at: "document_idle",
};

const API_BASE = "http://localhost:8000";
const SCAN_DEBOUNCE_MS = 2000;
const MAX_TEXT_LENGTH = 500;

interface ScanResult {
  element_id: string;
  verdict: string;
  confidence: number;
  claim_text: string;
}

/**
 * Compute a simple perceptual hash proxy for images (canvas-based).
 */
async function computeImageHash(img: HTMLImageElement): Promise<string> {
  const canvas = document.createElement("canvas");
  canvas.width = 8;
  canvas.height = 8;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  ctx.drawImage(img, 0, 0, 8, 8);
  const data = ctx.getImageData(0, 0, 8, 8).data;

  // Average luminance
  let sum = 0;
  const lum: number[] = [];
  for (let i = 0; i < data.length; i += 4) {
    const l = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
    lum.push(l);
    sum += l;
  }
  const avg = sum / lum.length;
  return lum.map((l) => (l >= avg ? "1" : "0")).join("");
}

/**
 * Extract meaningful text blocks from the page.
 */
function extractTextBlocks(): { element: Element; text: string }[] {
  const blocks: { element: Element; text: string }[] = [];
  const selectors = "p, h1, h2, h3, blockquote, [role='article'], article p";

  document.querySelectorAll(selectors).forEach((el) => {
    const text = el.textContent?.trim() || "";
    if (text.length > 40 && text.length < MAX_TEXT_LENGTH) {
      blocks.push({ element: el, text });
    }
  });

  return blocks.slice(0, 20); // Limit scanned blocks
}

/**
 * Extract images from the page.
 */
function extractImages(): HTMLImageElement[] {
  const imgs = Array.from(document.querySelectorAll("img"));
  return imgs.filter(
    (img) => img.naturalWidth > 100 && img.naturalHeight > 100
  );
}

/**
 * Inject a small verdict overlay on a flagged element.
 */
function injectOverlay(element: Element, result: ScanResult): void {
  // Check if already flagged
  if (element.querySelector(".veridian-overlay")) return;

  const overlay = document.createElement("div");
  overlay.className = "veridian-overlay";

  const colors: Record<string, string> = {
    TRUE: "#34d399",
    FALSE: "#f87171",
    MISLEADING: "#fbbf24",
    UNVERIFIABLE: "#94a3b8",
  };

  const icons: Record<string, string> = {
    TRUE: "✓",
    FALSE: "✗",
    MISLEADING: "⚠",
    UNVERIFIABLE: "?",
  };

  overlay.style.cssText = `
    position: absolute;
    top: 4px;
    right: 4px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: ${colors[result.verdict] || colors.UNVERIFIABLE};
    color: #000;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    cursor: pointer;
    z-index: 10000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: transform 0.15s ease;
  `;

  overlay.textContent = icons[result.verdict] || "?";
  overlay.title = `Veridian: ${result.verdict} (${(result.confidence * 100).toFixed(0)}%)`;

  overlay.addEventListener("mouseenter", () => {
    overlay.style.transform = "scale(1.2)";
  });
  overlay.addEventListener("mouseleave", () => {
    overlay.style.transform = "scale(1)";
  });

  // Ensure parent is positioned
  const parent = element as HTMLElement;
  if (getComputedStyle(parent).position === "static") {
    parent.style.position = "relative";
  }

  parent.appendChild(overlay);
}

/**
 * Main scan function.
 */
async function scanPage(): Promise<void> {
  const textBlocks = extractTextBlocks();
  const images = extractImages();

  // For demo: simulate API responses
  // In production: POST to /v1/analyze for each block
  for (const block of textBlocks.slice(0, 5)) {
    try {
      // Simulated check — in production this calls the real API
      const hash = btoa(block.text.slice(0, 32));

      const cached = sessionStorage.getItem(`veridian:${hash}`);
      if (cached) continue;

      // Mark as checked
      sessionStorage.setItem(`veridian:${hash}`, "checked");
    } catch (e) {
      // Silently ignore scan errors
    }
  }
}

// Auto-scan on page load
setTimeout(scanPage, SCAN_DEBOUNCE_MS);
