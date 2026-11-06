/**
 * DRIFTGUARD 2.0 API Client
 */

export const API_BASE = typeof window !== "undefined" ? "" : "http://127.0.0.1:8000";

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;
  const res = await fetch(fullUrl, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error ${res.status}: ${errorBody || res.statusText}`);
  }

  return res.json();
}

export const api = {
  // Overview
  getOverviewSummary: () => fetchJson<{ data: any }>("/api/v1/overview/summary"),
  getOverviewTrends: () => fetchJson<{ data: any }>("/api/v1/overview/trends"),
  getOverviewAlerts: (limit = 10) => fetchJson<{ data: any[] }>(`/api/v1/overview/alerts?limit=${limit}`),

  // Transactions
  getTransactions: (params?: { limit?: number; offset?: number; decision?: string; action?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    if (params?.decision) q.set("decision", params.decision);
    if (params?.action) q.set("action", params.action);
    if (params?.search) q.set("search", params.search);
    return fetchJson<{ total: number; data: any[]; page: number; limit: number }>(`/api/v1/transactions?${q.toString()}`);
  },
  getTransactionDetail: (id: string) => fetchJson<{ data: any }>(`/api/v1/transactions/${id}`),

  // Investigations
  getCases: () => fetchJson<{ cases: any[] }>("/api/v1/investigations/cases"),
  getCaseDetail: (id: string) => fetchJson<{ case: any }>(`/api/v1/investigations/cases/${id}`),
  submitCaseAction: (id: string, action: string, notes: string) =>
    fetchJson(`/api/v1/investigations/cases/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action, notes }),
    }),

  // Entities
  getEntityGraph: (limit = 60) => fetchJson<{ nodes: any[]; links: any[]; categories: any[] }>(`/api/v1/entities/graph?limit=${limit}`),
  getEntityProfile: (id: string) => fetchJson<any>(`/api/v1/entities/${id}`),

  // Experts
  getExpertsStatus: () => fetchJson<{ total_experts: number; total_weight: number; experts: any[] }>("/api/v1/experts/status"),
  updateExpertWeights: (weights: Record<string, number>) =>
    fetchJson("/api/v1/experts/weights", {
      method: "POST",
      body: JSON.stringify(weights),
    }),
  evaluateTransaction: (payload: any) =>
    fetchJson<{ data: any }>("/api/v1/experts/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Responses
  getPolicies: () => fetchJson<{ policies: any[] }>("/api/v1/responses/policies"),
  getActionsSummary: () => fetchJson<{ summary: any }>("/api/v1/responses/actions"),
  simulatePolicy: (threshold_block: number, threshold_review: number) =>
    fetchJson<{ simulation: any }>("/api/v1/responses/simulate", {
      method: "POST",
      body: JSON.stringify({ threshold_block, threshold_review }),
    }),
  getWatchlist: () => fetchJson<{ watchlist: any[] }>("/api/v1/responses/watchlist"),
  addToWatchlist: (entity_id: string, type: string, reason: string) =>
    fetchJson("/api/v1/responses/watchlist", {
      method: "POST",
      body: JSON.stringify({ entity_id, type, reason }),
    }),

  // Models
  getActiveModel: () => fetchJson<any>("/api/v1/models/active"),
  getBenchmark: () => fetchJson<any>("/api/v1/models/benchmark"),
  getModelHistory: () => fetchJson<{ models: any[] }>("/api/v1/models/history"),

  // Drift
  getDriftSummary: () => fetchJson<any>("/api/v1/drift/summary"),
  getFeatureDrift: () => fetchJson<{ features: any[] }>("/api/v1/drift/features"),
  getDriftEvents: (limit = 50) => fetchJson<{ events: any[] }>(`/api/v1/drift/events?limit=${limit}`),

  // Simulation
  getSimulationState: () => fetchJson<{ state: any }>("/api/v1/simulation/state"),
  startSimulation: (scenario: string, speed: number) =>
    fetchJson("/api/v1/simulation/start", {
      method: "POST",
      body: JSON.stringify({ scenario, speed }),
    }),
  pauseSimulation: () => fetchJson("/api/v1/simulation/pause", { method: "POST" }),
  stepSimulation: (count: number, scenario: string) =>
    fetchJson<{ results: any[] }>("/api/v1/simulation/step", {
      method: "POST",
      body: JSON.stringify({ count, scenario }),
    }),
  injectAttack: (scenario: string, tamper = false) =>
    fetchJson<{ result: any }>("/api/v1/simulation/inject", {
      method: "POST",
      body: JSON.stringify({ scenario, tamper }),
    }),
  resetSimulation: () => fetchJson("/api/v1/simulation/reset", { method: "POST" }),
  getScenarios: () => fetchJson<{ scenarios: any[] }>("/api/v1/simulation/scenarios"),

  // System
  getSystemHealth: () => fetchJson<any>("/api/v1/system/health"),
  getKeys: () => fetchJson<any>("/api/v1/system/keys"),
  getDbStats: () => fetchJson<any>("/api/v1/system/db-stats"),

  // Experiments
  getExperimentList: async () => {
    const res = await fetch(`${API_BASE}/api/v1/experiments/`);
    return res.json();
  },
  getLatestExperiment: async () => {
    const res = await fetch(`${API_BASE}/api/v1/experiments/latest/result`);
    return res.json();
  },
  runExperiment: async (seed = 42, name = "Moving Target Attack Simulation") => {
    const res = await fetch(`${API_BASE}/api/v1/experiments/run?seed=${seed}&name=${encodeURIComponent(name)}`, {
      method: "POST",
    });
    return res.json();
  },
};
