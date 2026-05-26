import { useState } from "react";
import { summarizeText } from "../api";
import { ENGINE_LABELS, engineLabel } from "../lib/engineLabels";
import { MaterialIcon } from "./icons/MaterialIcon";

type CompareResult = {
  engine: string;
  summary: string | null;
  compressionPct: number | null;
  latencyMs: number | null;
  selectedSentences: number | null;
  sourceSentences: number | null;
  error: string | null;
  loading: boolean;
};

type Props = {
  open: boolean;
  engineOptions: string[];
  onClose: () => void;
};

export function EngineCompareModal({ open, engineOptions, onClose }: Props) {
  const defaultEngines = engineOptions.slice(0, 2);
  const [inputText, setInputText] = useState("");
  const [maxSentences, setMaxSentences] = useState(3);
  const [engines, setEngines] = useState<[string, string]>([
    defaultEngines[0] ?? "tfidf",
    defaultEngines[1] ?? "textrank",
  ]);
  const [results, setResults] = useState<CompareResult[] | null>(null);
  const [running, setRunning] = useState(false);

  if (!open) return null;

  const handleClose = () => {
    if (running) return;
    setResults(null);
    setInputText("");
    onClose();
  };

  const runCompare = async () => {
    const text = inputText.trim();
    if (!text || running) return;

    setRunning(true);
    setResults(
      engines.map((e) => ({
        engine: e,
        summary: null,
        compressionPct: null,
        latencyMs: null,
        selectedSentences: null,
        sourceSentences: null,
        error: null,
        loading: true,
      })),
    );

    const settled = await Promise.all(
      engines.map(async (engine): Promise<CompareResult> => {
        const resp = await summarizeText({ text, engine, max_sentences: maxSentences });
        if ("error" in resp) {
          return { engine, summary: null, compressionPct: null, latencyMs: null, selectedSentences: null, sourceSentences: null, error: resp.error, loading: false };
        }
        const meta = resp.metadata ?? {};
        const compressionPct =
          typeof meta.compression_ratio_chars === "number"
            ? Math.round(meta.compression_ratio_chars * 1000) / 10
            : null;
        const latencyMs =
          typeof meta.summarizer_latency_ms === "number" ? meta.summarizer_latency_ms : null;
        const selectedSentences =
          typeof meta.selected_sentence_count === "number" ? meta.selected_sentence_count : null;
        const sourceSentences =
          typeof meta.sentence_count === "number" ? meta.sentence_count : null;
        return { engine, summary: resp.summary, compressionPct, latencyMs, selectedSentences, sourceSentences, error: null, loading: false };
      }),
    );

    setResults(settled);
    setRunning(false);
  };

  const canRun = inputText.trim().length > 20 && !running;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      role="presentation"
      onClick={handleClose}
    >
      <div
        role="dialog"
        aria-labelledby="compare-title"
        className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-outline-variant px-6 py-4">
          <div>
            <h2 id="compare-title" className="text-lg font-semibold">So sánh Engine</h2>
            <p className="text-xs text-on-surface-variant">Chạy cùng văn bản qua nhiều engine và xem kết quả song song</p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={running}
            className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container"
            aria-label="Đóng"
          >
            <MaterialIcon name="close" size="sm" />
          </button>
        </div>

        {/* Body */}
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-6">
          {/* Input */}
          <div>
            <label className="mb-1 block text-sm font-medium text-on-surface" htmlFor="compare-text">
              Văn bản cần so sánh
            </label>
            <textarea
              id="compare-text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={running}
              placeholder="Dán văn bản tiếng Việt vào đây (tối thiểu 20 ký tự)…"
              rows={4}
              className="w-full resize-y rounded-xl border border-outline-variant px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
            />
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-end gap-4">
            {engines.map((eng, idx) => (
              <div key={idx} className="flex-1 min-w-[140px]">
                <label className="mb-1 block text-xs font-medium text-on-surface-variant">
                  Engine {idx + 1}
                </label>
                <select
                  value={eng}
                  disabled={running}
                  onChange={(e) => {
                    const next = [...engines] as [string, string];
                    next[idx] = e.target.value;
                    setEngines(next);
                  }}
                  className="w-full rounded-lg border border-outline-variant px-3 py-2 text-sm disabled:opacity-60"
                >
                  {engineOptions.map((opt) => (
                    <option key={opt} value={opt}>{engineLabel(opt)}</option>
                  ))}
                </select>
              </div>
            ))}

            <div className="min-w-[120px]">
              <label className="mb-1 block text-xs font-medium text-on-surface-variant">
                Số câu: <strong>{maxSentences}</strong>
              </label>
              <input
                type="range"
                min={1}
                max={8}
                value={maxSentences}
                disabled={running}
                onChange={(e) => setMaxSentences(Number(e.target.value))}
                className="w-full disabled:opacity-60"
              />
            </div>

            <button
              type="button"
              onClick={runCompare}
              disabled={!canRun}
              className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            >
              {running ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Đang chạy…
                </>
              ) : (
                <>
                  <MaterialIcon name="compare" size="sm" />
                  So sánh
                </>
              )}
            </button>
          </div>

          {/* Results */}
          {results && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {results.map((r) => (
                <ResultCard key={r.engine} result={r} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultCard({ result }: { result: CompareResult }) {
  const ENGINE_COLORS: Record<string, string> = {
    tfidf: "bg-blue-50 text-blue-700",
    textrank: "bg-emerald-50 text-emerald-700",
    "phobert-extractive": "bg-violet-50 text-violet-700",
    vit5: "bg-orange-50 text-orange-700",
    hybrid: "bg-primary-container/30 text-primary",
  };
  const colorClass = ENGINE_COLORS[result.engine] ?? "bg-surface-container text-on-surface-variant";

  return (
    <div className="flex flex-col rounded-xl border border-outline-variant bg-white p-4">
      {/* Engine badge */}
      <div className="mb-3 flex items-center gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${colorClass}`}>
          {ENGINE_LABELS[result.engine] ?? result.engine}
        </span>
        {result.latencyMs != null && (
          <span className="text-xs text-on-surface-variant">{result.latencyMs} ms</span>
        )}
      </div>

      {/* Stats row */}
      {!result.error && !result.loading && (
        <div className="mb-3 flex flex-wrap gap-2">
          {result.compressionPct != null && (
            <Chip icon="analytics" label={`Tỉ lệ nén ${result.compressionPct}%`} />
          )}
          {result.selectedSentences != null && result.sourceSentences != null && (
            <Chip icon="format_list_numbered" label={`${result.selectedSentences}/${result.sourceSentences} câu`} />
          )}
        </div>
      )}

      {/* Content */}
      {result.loading ? (
        <div className="flex flex-1 items-center justify-center py-6">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : result.error ? (
        <div className="flex items-start gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700">
          <MaterialIcon name="error" size="sm" className="shrink-0 mt-0.5" />
          <span>{result.error}</span>
        </div>
      ) : (
        <p className="text-sm leading-relaxed text-on-surface-variant">{result.summary}</p>
      )}
    </div>
  );
}

function Chip({ icon, label }: { icon: string; label: string }) {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-surface-container px-2 py-0.5">
      <MaterialIcon name={icon} size="sm" className="text-primary" />
      <span className="text-[10px] font-medium">{label}</span>
    </div>
  );
}
