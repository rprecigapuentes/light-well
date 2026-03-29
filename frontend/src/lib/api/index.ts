import type { DailyViewResponse, InsightResponse, AskResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function apiFetch<T>(path: string): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      return { ok: false, error: `HTTP ${res.status}: ${text}` };
    }
    const data: T = await res.json();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export function getDayData(
  start: string,
  end: string
): Promise<ApiResult<DailyViewResponse>> {
  return apiFetch(`/data?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
}

export function getDayInsight(
  start: string,
  end: string
): Promise<ApiResult<InsightResponse>> {
  return apiFetch(`/insight?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
}

export function askDay(
  start: string,
  end: string,
  question: string
): Promise<ApiResult<AskResponse>> {
  return apiFetch(
    `/ask?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&question=${encodeURIComponent(question)}`
  );
}
