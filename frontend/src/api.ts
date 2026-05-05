const FALLBACK_ENGINES = ["tfidf", "textrank", "phobert-extractive"];

export function apiBase(): string {
  return import.meta.env.VITE_API_BASE?.replace(/\/$/, "") ?? "http://127.0.0.1:8000/api/v1";
}

export type EnginesPayload = {
  supported_engines: string[];
  planned_engines?: string[];
  default_engine?: string | null;
};

export async function fetchEngines(): Promise<{
  engines: string[];
  planned: string[];
  defaultEngine: string | null;
  warning: string | null;
}> {
  const fallbackDefault = FALLBACK_ENGINES[0] ?? null;
  try {
    const resp = await fetch(`${apiBase()}/engines`, { signal: AbortSignal.timeout(10_000) });
    if (!resp.ok) {
      return {
        engines: FALLBACK_ENGINES,
        planned: [],
        defaultEngine: fallbackDefault,
        warning: `Engines request failed (${resp.status}). Using fallback list.`,
      };
    }
    const payload = (await resp.json()) as EnginesPayload;
    const raw = payload.supported_engines;
    const engines =
      Array.isArray(raw) ? raw.map((e) => String(e).trim()).filter(Boolean) : [];
    if (engines.length > 0) {
      const apiDefault =
        typeof payload.default_engine === "string" && payload.default_engine.trim()
          ? payload.default_engine.trim()
          : null;
      const defaultEngine =
        apiDefault && engines.includes(apiDefault) ? apiDefault : engines[0] ?? fallbackDefault;
      return {
        engines,
        planned: Array.isArray(payload.planned_engines)
          ? payload.planned_engines.map((e) => String(e))
          : [],
        defaultEngine,
        warning: null,
      };
    }
    return {
      engines: FALLBACK_ENGINES,
      planned: [],
      defaultEngine: fallbackDefault,
      warning: "Backend returned empty engine capabilities. Using fallback.",
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      engines: FALLBACK_ENGINES,
      planned: [],
      defaultEngine: fallbackDefault,
      warning: `Cannot load engine capabilities: ${msg}`,
    };
  }
}

export async function fetchHealth(): Promise<{ ok: true; status: string } | { ok: false; message: string }> {
  try {
    const resp = await fetch(`${apiBase()}/health`, { signal: AbortSignal.timeout(10_000) });
    if (!resp.ok) {
      return { ok: false, message: `Health check HTTP ${resp.status}` };
    }
    const data = (await resp.json()) as { status?: string };
    return { ok: true, status: data.status ?? "unknown" };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { ok: false, message: `Cannot connect backend: ${msg}` };
  }
}

export type SummarizeResponse = {
  summary: string;
  metadata: Record<string, unknown>;
};

async function readErrorDetail(resp: Response): Promise<string> {
  try {
    const body = await resp.json();
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return JSON.stringify(detail);
    return resp.statusText || String(resp.status);
  } catch {
    return resp.statusText || String(resp.status);
  }
}

export async function summarizeText(body: {
  text: string;
  max_sentences: number;
  engine: string;
}): Promise<SummarizeResponse | { error: string }> {
  try {
    const resp = await fetch(`${apiBase()}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: body.text,
        max_sentences: body.max_sentences,
        engine: body.engine,
      }),
      signal: AbortSignal.timeout(60_000),
    });
    if (!resp.ok) {
      const detail = await readErrorDetail(resp);
      return { error: `Summarize failed (${resp.status}): ${detail}` };
    }
    return (await resp.json()) as SummarizeResponse;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { error: `Summarize failed: ${msg}` };
  }
}

export async function summarizeFile(
  file: File,
  params: { max_sentences: number; engine: string },
): Promise<SummarizeResponse | { error: string }> {
  try {
    const qs = new URLSearchParams({
      max_sentences: String(params.max_sentences),
      engine: params.engine,
    });
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${apiBase()}/summarize/file?${qs.toString()}`, {
      method: "POST",
      body: form,
      signal: AbortSignal.timeout(120_000),
    });
    if (!resp.ok) {
      const detail = await readErrorDetail(resp);
      return { error: `Summarize failed (${resp.status}): ${detail}` };
    }
    return (await resp.json()) as SummarizeResponse;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { error: `Summarize failed: ${msg}` };
  }
}

export async function summarizeUrl(
  url: string,
  params: { max_sentences: number; engine: string },
): Promise<SummarizeResponse | { error: string }> {
  try {
    const qs = new URLSearchParams({
      max_sentences: String(params.max_sentences),
      engine: params.engine,
    });
    const resp = await fetch(`${apiBase()}/summarize/url?${qs.toString()}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(120_000),
    });
    if (!resp.ok) {
      const detail = await readErrorDetail(resp);
      return { error: `Summarize failed (${resp.status}): ${detail}` };
    }
    return (await resp.json()) as SummarizeResponse;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { error: `Summarize failed: ${msg}` };
  }
}
