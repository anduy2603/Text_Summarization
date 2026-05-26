import { useCallback, useRef, useState } from "react";
import { LENGTH_PRESETS, type LengthPresetId } from "../constants";
import { MaterialIcon } from "./icons/MaterialIcon";

const ACCEPT =
  ".txt,.docx,.pdf,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

type Props = {
  open: boolean;
  busy: boolean;
  onClose: () => void;
  onSubmit: (input: { text: string; file: File | null }, lengthPreset: LengthPresetId) => void;
};

export function NewSummaryModal({ open, busy, onClose, onSubmit }: Props) {
  const [draft, setDraft] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [lengthPreset, setLengthPreset] = useState<LengthPresetId>("medium");
  const [showTextFallback, setShowTextFallback] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const pickFile = useCallback((f: File | undefined) => {
    if (!f) return;
    setFile(f);
    setDraft("");
    setShowTextFallback(false);
  }, []);

  if (!open) return null;

  const handleSubmit = () => {
    if (!file && !draft.trim()) return;
    onSubmit({ text: draft.trim(), file }, lengthPreset);
  };

  const resetAndClose = () => {
    if (busy) return;
    setDraft("");
    setFile(null);
    setShowTextFallback(false);
    setDragOver(false);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      role="presentation"
      onClick={resetAndClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-6 shadow-xl sm:rounded-2xl"
        role="dialog"
        aria-labelledby="new-summary-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="new-summary-title" className="text-lg font-semibold">
            Tải tệp để tóm tắt
          </h2>
          <button
            type="button"
            onClick={resetAndClose}
            disabled={busy}
            className="rounded-lg p-2 text-on-surface-variant hover:bg-surface-container"
            aria-label="Đóng"
          >
            <MaterialIcon name="close" size="sm" />
          </button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Độ dài tóm tắt">
          {LENGTH_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              disabled={busy}
              onClick={() => setLengthPreset(p.id)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                lengthPreset === p.id
                  ? "bg-primary text-white"
                  : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {file ? (
          <div className="mb-4 flex items-center justify-between rounded-xl border border-primary/30 bg-primary-container/20 px-4 py-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-on-surface">{file.name}</p>
              <p className="text-xs text-on-surface-variant">
                {(file.size / 1024).toFixed(0)} KB · TXT, DOCX hoặc PDF
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => setFile(null)}
              className="ml-2 shrink-0 text-xs font-medium text-primary"
            >
              Đổi tệp
            </button>
          </div>
        ) : (
          <div
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") fileRef.current?.click();
            }}
            onDragEnter={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setDragOver(false);
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              pickFile(e.dataTransfer.files?.[0]);
            }}
            onClick={() => fileRef.current?.click()}
            className={`mb-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed px-6 py-10 transition-colors ${
              dragOver
                ? "border-primary bg-primary-container/30"
                : "border-outline-variant bg-surface-container-low hover:border-primary/50"
            }`}
          >
            <MaterialIcon name="upload_file" size="lg" className="text-primary" />
            <p className="text-center text-sm font-medium text-on-surface">
              Kéo thả hoặc chọn tệp
            </p>
            <p className="text-center text-xs text-on-surface-variant">
              Hỗ trợ .txt, .docx, .pdf (tối đa theo giới hạn máy chủ)
            </p>
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          onChange={(e) => {
            pickFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        {!file ? (
          <div className="mb-4">
            {!showTextFallback ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => setShowTextFallback(true)}
                className="text-xs font-medium text-primary hover:underline"
              >
                Hoặc nhập văn bản / dán link bài báo
              </button>
            ) : (
              <>
                <label className="mb-1 block text-xs font-medium text-on-surface-variant" htmlFor="draft-text">
                  Văn bản hoặc URL
                </label>
                <textarea
                  id="draft-text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={busy}
                  placeholder="Dán văn bản hoặc link http(s)…"
                  rows={4}
                  className="w-full resize-y rounded-xl border border-outline-variant px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setShowTextFallback(false);
                    setDraft("");
                  }}
                  className="mt-2 text-xs text-on-surface-variant hover:underline"
                >
                  Quay lại tải tệp
                </button>
              </>
            )}
          </div>
        ) : null}

        <button
          type="button"
          disabled={busy || (!file && !draft.trim())}
          onClick={handleSubmit}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {busy ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Đang tóm tắt…
            </>
          ) : (
            <>
              <MaterialIcon name="auto_awesome" size="sm" />
              {file ? "Tóm tắt tệp" : "Tóm tắt"}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
