/**
 * Background service worker — handles API calls, caches results per domain,
 * and manages auth token refresh.
 */

const API_BASE = "http://localhost:8000";
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

interface CacheEntry {
  data: unknown;
  timestamp: number;
}

const resultCache = new Map<string, CacheEntry>();

/**
 * Get or refresh auth token from storage.
 */
async function getAuthToken(): Promise<string | null> {
  const result = await chrome.storage.local.get(["veridian_token", "veridian_refresh_token", "veridian_token_exp"]);
  const now = Date.now();

  if (result.veridian_token && result.veridian_token_exp > now) {
    return result.veridian_token;
  }

  // Try refresh
  if (result.veridian_refresh_token) {
    try {
      const resp = await fetch(`${API_BASE}/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: result.veridian_refresh_token }),
      });

      if (resp.ok) {
        const data = await resp.json();
        await chrome.storage.local.set({
          veridian_token: data.access_token,
          veridian_refresh_token: data.refresh_token,
          veridian_token_exp: now + data.expires_in * 1000,
        });
        return data.access_token;
      }
    } catch (e) {
      console.error("Veridian: token refresh failed", e);
    }
  }

  return null;
}

/**
 * Make an authenticated API call with caching.
 */
async function apiCall(endpoint: string, body?: unknown): Promise<unknown> {
  const cacheKey = endpoint + (body ? JSON.stringify(body) : "");

  // Check cache
  const cached = resultCache.get(cacheKey);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
    return cached.data;
  }

  const token = await getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${API_BASE}${endpoint}`, {
    method: body ? "POST" : "GET",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`);
  }

  const data = await resp.json();

  // Cache the result
  resultCache.set(cacheKey, { data, timestamp: Date.now() });

  return data;
}

/**
 * Listen for messages from content scripts.
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "VERIDIAN_ANALYZE") {
    apiCall("/v1/analyze", message.payload)
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // async response
  }

  if (message.type === "VERIDIAN_CHECK_STATUS") {
    apiCall(`/v1/analyze/${message.analysisId}`)
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }
});

export {};
