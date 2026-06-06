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
      className="fixed inset-0 z-[60] flex items-end justify-center bg-black/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      role="presentation"
      onClick={resetAndClose}
    >
      <div
        className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-surface-container-lowest p-6 shadow-xl ring-1 ring-outline-variant/50 sm:rounded-2xl"
        role="dialog"
        aria-labelledby="new-summary-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 id="new-summary-title" className="text-base font-bold text-on-surface">
              Tóm tắt tài liệu mới
            </h2>
            <p className="mt-0.5 text-xs text-on-surface-variant">TXT, DOCX, PDF hoặc link bài báo</p>
          </div>
          <button
            type="button"
            onClick={resetAndClose}
            disabled={busy}
            className="rounded-lg p-1.5 text-on-surface-variant transition-colors hover:bg-surface-container active:scale-[0.95]"
            aria-label="Đóng"
          >
            <MaterialIcon name="close" size="sm" />
          </button>
        </div>

        <div className="mb-5">
          <p className="mb-2 text-xs font-semibold text-on-surface-variant">Độ dài tóm tắt</p>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Độ dài tóm tắt">
            {LENGTH_PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                disabled={busy}
                onClick={() => setLengthPreset(p.id)}
                className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all duration-150 active:scale-[0.96] ${
                  lengthPreset === p.id
                    ? "bg-primary text-white shadow-sm"
                    : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {file ? (
          <div className="mb-5 flex items-center gap-3 rounded-xl border border-primary/20 bg-primary-fixed px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <MaterialIcon name="description" size="sm" className="text-primary" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-on-surface">{file.name}</p>
              <p className="text-xs text-on-surface-variant">
                {(file.size / 1024).toFixed(0)} KB
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => setFile(null)}
              className="shrink-0 rounded-lg px-2.5 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/10 active:scale-[0.97]"
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
            className={`mb-5 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-10 transition-all duration-200 ${
              dragOver
                ? "border-primary bg-primary-fixed scale-[1.01]"
                : "border-outline-variant bg-surface-container-low hover:border-primary/40 hover:bg-surface-container"
            }`}
          >
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl transition-colors ${dragOver ? "bg-primary/10" : "bg-surface-container"}`}>
              <MaterialIcon name="upload_file" size="lg" className={dragOver ? "text-primary" : "text-outline"} />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-on-surface">
                {dragOver ? "Thả tệp vào đây" : "Kéo thả hoặc chọn tệp"}
              </p>
              <p className="mt-1 text-xs text-on-surface-variant">
                Hỗ trợ .txt, .docx, .pdf
              </p>
            </div>
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
          <div className="mb-5">
            {!showTextFallback ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => setShowTextFallback(true)}
                className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant transition-colors hover:text-primary"
              >
                <MaterialIcon name="link" size="sm" />
                Hoặc nhập văn bản / dán link bài báo
              </button>
            ) : (
              <>
                <label className="mb-1.5 block text-xs font-semibold text-on-surface-variant" htmlFor="draft-text">
                  Văn bản hoặc URL
                </label>
                <textarea
                  id="draft-text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={busy}
                  placeholder="Dán văn bản hoặc link http(s)…"
                  rows={4}
                  className="w-full resize-y rounded-xl border border-outline-variant bg-background px-4 py-3 text-sm transition-colors focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15"
                />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setShowTextFallback(false);
                    setDraft("");
                  }}
                  className="mt-2 text-xs text-on-surface-variant hover:text-on-surface"
                >
                  ← Quay lại tải tệp
                </button>
              </>
            )}
          </div>
        ) : null}

        <button
          type="button"
          disabled={busy || (!file && !draft.trim())}
          onClick={handleSubmit}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-primary/90 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
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
