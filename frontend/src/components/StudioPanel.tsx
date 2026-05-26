import { LENGTH_PRESETS, type LengthPresetId } from "../constants";
import type { SourceItem } from "../types/sources";
import { sourceKindIcon } from "../lib/sources";

type Props = {
  activeSource: SourceItem | null;
  lengthPreset: LengthPresetId;
  busy: boolean;
  showAdvanced: boolean;
  engineOptions: string[];
  engine: string;
  maxSentences: number;
  showRawMetadata: boolean;
  lastMetadata: Record<string, unknown> | null;
  onLengthPreset: (id: LengthPresetId) => void;
  onSummarize: () => void;
  onAdvancedToggle: (open: boolean) => void;
  onEngine: (v: string) => void;
  onMaxSentences: (n: number) => void;
  onShowRawMetadata: (v: boolean) => void;
};

export function StudioPanel({
  activeSource,
  lengthPreset,
  busy,
  showAdvanced,
  engineOptions,
  engine,
  maxSentences,
  showRawMetadata,
  lastMetadata,
  onLengthPreset,
  onSummarize,
  onAdvancedToggle,
  onEngine,
  onMaxSentences,
  onShowRawMetadata,
}: Props) {
  return (
    <aside className="panel studio-panel" aria-label="Studio tóm tắt">
      <div className="panel-head">
        <h2 className="panel-title">Studio</h2>
        <p className="panel-sub muted small">Tạo bản tóm tắt từ nguồn đã chọn</p>
      </div>

      {activeSource ? (
        <div className="studio-active-source">
          <span className="studio-source-icon" aria-hidden>
            {sourceKindIcon(activeSource.kind)}
          </span>
          <span className="studio-source-title">{activeSource.title}</span>
        </div>
      ) : (
        <p className="studio-hint muted small">Thêm và chọn một nguồn để bật tóm tắt.</p>
      )}

      <div className="field-label">Độ dài</div>
      <div className="length-chips studio-chips" role="group" aria-label="Độ dài tóm tắt">
        {LENGTH_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            className={`length-chip ${lengthPreset === preset.id ? "active" : ""}`}
            aria-pressed={lengthPreset === preset.id}
            disabled={busy}
            onClick={() => onLengthPreset(preset.id)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        className="btn primary studio-summarize"
        disabled={busy || !activeSource}
        onClick={onSummarize}
      >
        {busy ? "Đang tóm tắt…" : "Tạo tóm tắt"}
      </button>

      <p className="studio-note muted small">
        Hệ thống tự đọc TXT, DOCX, PDF hoặc trích văn bản từ link, rồi tóm tắt bằng engine mặc định
        (TextRank).
      </p>

      <details
        className="advanced-panel"
        open={showAdvanced}
        onToggle={(e) => onAdvancedToggle((e.target as HTMLDetailsElement).open)}
      >
        <summary>Thực nghiệm</summary>
        <div className="advanced-body">
          <label className="field-label" htmlFor="max-sent">
            max_sentences: <strong>{maxSentences}</strong>
          </label>
          <input
            id="max-sent"
            type="range"
            min={1}
            max={10}
            value={maxSentences}
            onChange={(e) => onMaxSentences(Number(e.target.value))}
            className="slider"
          />
          <label className="field-label" htmlFor="engine">
            Engine
          </label>
          <select id="engine" className="select" value={engine} onChange={(e) => onEngine(e.target.value)}>
            {engineOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={showRawMetadata}
              onChange={(e) => onShowRawMetadata(e.target.checked)}
            />
            Metadata JSON (lần gần nhất)
          </label>
          {showRawMetadata && lastMetadata ? (
            <pre className="meta-json studio-meta">{JSON.stringify(lastMetadata, null, 2)}</pre>
          ) : null}
        </div>
      </details>
    </aside>
  );
}
