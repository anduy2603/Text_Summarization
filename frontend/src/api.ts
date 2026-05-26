const FALLBACK_ENGINES = ["tfidf", "textrank", "phobert-extractive", "vit5"];

export function apiBase(): string {
  return import.meta.env.VITE_API_BASE?.replace(/\/$/, "") ?? "http://127.0.0.1:8000/api/v1";
}

export type EnginesPayload = {
  supported_engines: string[];
  planned_engines?: string[];
  default_engine?: string | null;
  default_max_sentences?: number;
};

export type SummarizeOptions = {
  /** Omit to use backend SUMMARY_MAX_SENTENCES (product default). */
  max_sentences?: number;
  /** Omit to use backend SUMMARY_ENGINE (product default). */
  engine?: string;
};

export async function fetchEngines(): Promise<{
  engines: string[];
  planned: string[];
  defaultEngine: string | null;
  defaultMaxSentences: number;
  warning: string | null;
}> {
  const fallbackDefault = "textrank";
  const fallbackMaxSentences = 2;
  try {
    const resp = await fetch(`${apiBase()}/engines`, { signal: AbortSignal.timeout(10_000) });
    if (!resp.ok) {
      return {
        engines: FALLBACK_ENGINES,
        planned: [],
        defaultEngine: fallbackDefault,
        defaultMaxSentences: fallbackMaxSentences,
        warning: `Engines request failed (${resp.status}). Using fallback list.`,
      };
    }
    const payload = (await resp.json()) as EnginesPayload;
    const raw = payload.supported_engines;
    const engines =
      Array.isArray(raw) ? raw.map((e) => String(e).trim()).filter(Boolean) : [];
    const defaultMaxSentences =
      typeof payload.default_max_sentences === "number" && payload.default_max_sentences >= 1
        ? payload.default_max_sentences
        : fallbackMaxSentences;
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
        defaultMaxSentences,
        warning: null,
      };
    }
    return {
      engines: FALLBACK_ENGINES,
      planned: [],
      defaultEngine: fallbackDefault,
      defaultMaxSentences: fallbackMaxSentences,
      warning: "Backend returned empty engine capabilities. Using fallback.",
    };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      engines: FALLBACK_ENGINES,
      planned: [],
      defaultEngine: fallbackDefault,
      defaultMaxSentences: fallbackMaxSentences,
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

function appendSummarizeQuery(qs: URLSearchParams, options?: SummarizeOptions): void {
  if (options?.max_sentences != null) {
    qs.set("max_sentences", String(options.max_sentences));
  }
  if (options?.engine?.trim()) {
    qs.set("engine", options.engine.trim());
  }
}

export async function summarizeText(
  body: { text: string } & SummarizeOptions,
): Promise<SummarizeResponse | { error: string }> {
  const { text, ...options } = body;
  try {
    const payload: Record<string, unknown> = { text };
    if (options.max_sentences != null) payload.max_sentences = options.max_sentences;
    if (options.engine?.trim()) payload.engine = options.engine.trim();

    const resp = await fetch(`${apiBase()}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
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
  options?: SummarizeOptions,
): Promise<SummarizeResponse | { error: string }> {
  try {
    const qs = new URLSearchParams();
    appendSummarizeQuery(qs, options);
    const query = qs.toString();
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(
      `${apiBase()}/summarize/file${query ? `?${query}` : ""}`,
      {
        method: "POST",
        body: form,
        signal: AbortSignal.timeout(120_000),
      },
    );
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

export async function exportSummaryAsDocx(
  title: string,
  summary: string,
): Promise<{ blob: Blob } | { error: string }> {
  try {
    const resp = await fetch(`${apiBase()}/export/docx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, summary }),
      signal: AbortSignal.timeout(30_000),
    });
    if (!resp.ok) {
      const detail = await readErrorDetail(resp);
      return { error: `Export thất bại (${resp.status}): ${detail}` };
    }
    const blob = await resp.blob();
    return { blob };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { error: `Export thất bại: ${msg}` };
  }
}

export async function summarizeUrl(
  url: string,
  options?: SummarizeOptions,
): Promise<SummarizeResponse | { error: string }> {
  try {
    const qs = new URLSearchParams();
    appendSummarizeQuery(qs, options);
    const query = qs.toString();
    const resp = await fetch(`${apiBase()}/summarize/url${query ? `?${query}` : ""}`, {
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
