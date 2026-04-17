/**
 * Veridian API client — typed HTTP calls to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface AnalyzeRequest {
  text?: string;
  media_url?: string;
  media_type: "text" | "image" | "audio" | "video";
  language?: string;
  callback_url?: string;
}

interface AnalyzeResponse {
  analysis_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  message?: string;
}

interface ClaimVerdict {
  claim_text: string;
  verdict: string;
  confidence: number;
  reasoning: string;
  evidence_used: {
    source_url?: string;
    source_name?: string;
    excerpt: string;
    relevance_score?: number;
  }[];
}

interface TrustReceipt {
  analysis_id: string;
  overall_verdict: string;
  overall_confidence: number;
  claim_verdicts: ClaimVerdict[];
  detection_scores: {
    model_name: string;
    score: number;
    verdict?: string;
  }[];
  media_type: string;
  processing_time_ms: number;
  created_at: string;
}

interface ClaimListResponse {
  claims: {
    id: string;
    original_text: string;
    language: string;
    verdict: string;
    confidence: number;
    reasoning: string;
    created_at: string;
  }[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

interface GraphResponse {
  nodes: { id: string; label: string; verdict: string }[];
  edges: { source: string; target: string; similarity_score: number }[];
}

class VeridianClient {
  private token: string | null = null;

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const resp = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!resp.ok) {
      const error = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(error.detail || `API Error: ${resp.status}`);
    }

    return resp.json() as T;
  }

  // ── Auth ─────────────────────────────────────────────────────────
  async login(email: string, password: string): Promise<TokenPair> {
    const tokens = await this.request<TokenPair>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.token = tokens.access_token;
    return tokens;
  }

  async register(
    email: string,
    password: string,
    fullName: string,
    organization?: string
  ): Promise<unknown> {
    return this.request("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        organization,
      }),
    });
  }

  async refresh(refreshToken: string): Promise<TokenPair> {
    const tokens = await this.request<TokenPair>("/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    this.token = tokens.access_token;
    return tokens;
  }

  setToken(token: string): void {
    this.token = token;
  }

  // ── Analysis ─────────────────────────────────────────────────────
  async analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>("/v1/analyze", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  async getAnalysisStatus(
    analysisId: string
  ): Promise<{ analysis_id: string; status: string; trust_receipt?: TrustReceipt }> {
    return this.request(`/v1/analyze/${analysisId}`);
  }

  // ── Claims ───────────────────────────────────────────────────────
  async getClaims(params?: {
    page?: number;
    page_size?: number;
    verdict?: string;
    language?: string;
    search_query?: string;
  }): Promise<ClaimListResponse> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    return this.request(`/v1/claims?${query}`);
  }

  async getClaimGraph(limit = 50): Promise<GraphResponse> {
    return this.request(`/v1/claims/graph?limit=${limit}`);
  }

  // ── Health ───────────────────────────────────────────────────────
  async health(): Promise<{ status: string; service: string }> {
    return this.request("/v1/health");
  }

  async ready(): Promise<Record<string, string>> {
    return this.request("/v1/ready");
  }
}

export const api = new VeridianClient();
export type {
  AnalyzeRequest,
  AnalyzeResponse,
  TrustReceipt,
  ClaimVerdict,
  ClaimListResponse,
  GraphResponse,
  TokenPair,
};
