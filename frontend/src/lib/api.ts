const API_BASE = typeof window === "undefined" ? "http://127.0.0.1:8000/api" : "/api";

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/apix/summary`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function fetchTimeseries(range = "30d", interval = "daily") {
  const res = await fetch(`${API_BASE}/apix/timeseries?range=${range}&interval=${interval}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch timeseries");
  return res.json();
}

export async function fetchRoutes() {
  const res = await fetch(`${API_BASE}/routes`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch routes");
  return res.json();
}

export async function fetchRouteLeadTime(routeCode: string) {
  const res = await fetch(`${API_BASE}/routes/${routeCode}/lead-time`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch route lead time");
  return res.json();
}

export async function fetchRecentAnomalies(limit = 10) {
  const res = await fetch(`${API_BASE}/anomalies/recent?limit=${limit}`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch anomalies");
  return res.json();
}

export async function fetchSystemHealth() {
  const res = await fetch(`${API_BASE}/system/health`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch system health");
  return res.json();
}
