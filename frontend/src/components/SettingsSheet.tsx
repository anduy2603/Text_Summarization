type Props = {
  open: boolean;
  engineOptions: string[];
  engine: string;
  maxSentences: number;
  showRawMetadata: boolean;
  lastMetadata: Record<string, unknown> | null;
  onClose: () => void;
  onEngine: (v: string) => void;
  onMaxSentences: (n: number) => void;
  onShowRawMetadata: (v: boolean) => void;
};

export function SettingsSheet({
  open,
  engineOptions,
  engine,
  maxSentences,
  showRawMetadata,
  lastMetadata,
  onClose,
  onEngine,
  onMaxSentences,
  onShowRawMetadata,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-end justify-center bg-black/40 sm:items-center"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="max-h-[85vh] w-full max-w-md overflow-y-auto rounded-t-2xl bg-white p-6 shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-labelledby="settings-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="settings-title" className="text-lg font-semibold">
            Cài đặt
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-on-surface-variant hover:bg-surface-container"
            aria-label="Đóng"
          >
            ×
          </button>
        </div>
        <p className="mb-4 text-sm text-on-surface-variant">
          Tùy chỉnh nâng cao. Thay đổi engine hoặc số câu để xem kết quả khác nhau.
        </p>

        <label className="mb-1 block text-sm font-medium" htmlFor="engine-select">
          Engine
        </label>
        <select
          id="engine-select"
          className="mb-4 w-full rounded-lg border border-outline-variant px-3 py-2 text-sm"
          value={engine}
          onChange={(e) => onEngine(e.target.value)}
        >
          {engineOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>

        <label className="mb-2 block text-sm font-medium" htmlFor="max-sent">
          Số câu tóm tắt: <strong>{maxSentences}</strong>
        </label>
        <input
          id="max-sent"
          type="range"
          min={1}
          max={10}
          value={maxSentences}
          onChange={(e) => onMaxSentences(Number(e.target.value))}
          className="mb-4 w-full"
        />

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showRawMetadata}
            onChange={(e) => onShowRawMetadata(e.target.checked)}
          />
          Hiện metadata JSON (lần gần nhất)
        </label>

        {showRawMetadata && lastMetadata ? (
          <pre className="mt-4 max-h-48 overflow-auto rounded-lg bg-surface-container-low p-3 text-xs">
            {JSON.stringify(lastMetadata, null, 2)}
          </pre>
        ) : null}
      </div>
    </div>
  );
}
