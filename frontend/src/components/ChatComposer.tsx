import { useRef } from "react";
import { LENGTH_PRESETS, type LengthPresetId } from "../constants";

type Props = {
  draft: string;
  pendingFile: File | null;
  lengthPreset: LengthPresetId;
  busy: boolean;
  hasConversation: boolean;
  onDraftChange: (v: string) => void;
  onLengthPreset: (id: LengthPresetId) => void;
  onFileSelect: (file: File | null) => void;
  onSend: () => void;
};

export function ChatComposer({
  draft,
  pendingFile,
  lengthPreset,
  busy,
  hasConversation,
  onDraftChange,
  onLengthPreset,
  onFileSelect,
  onSend,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy) onSend();
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelect(f);
  };

  return (
    <div className="composer" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <div className="composer-length" role="group" aria-label="Độ dài tóm tắt">
        {LENGTH_PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`composer-length-btn ${lengthPreset === p.id ? "active" : ""}`}
            disabled={busy}
            onClick={() => onLengthPreset(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {pendingFile ? (
        <div className="composer-file">
          <span className="composer-file-name">{pendingFile.name}</span>
          <button
            type="button"
            className="composer-file-remove"
            aria-label="Bỏ tệp"
            disabled={busy}
            onClick={() => {
              onFileSelect(null);
              if (fileRef.current) fileRef.current.value = "";
            }}
          >
            ×
          </button>
        </div>
      ) : null}

      <div className="composer-bar">
        <button
          type="button"
          className="composer-attach"
          title="Đính kèm tệp"
          disabled={busy}
          onClick={() => fileRef.current?.click()}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>

        <textarea
          ref={textareaRef}
          className="composer-input"
          rows={1}
          placeholder={
            hasConversation
              ? "Gửi thêm văn bản, tệp hoặc link khác…"
              : "Nhập văn bản hoặc dán link bài báo…"
          }
          value={draft}
          disabled={busy}
          onChange={(e) => {
            onDraftChange(e.target.value);
            resizeTextarea();
          }}
          onKeyDown={onKeyDown}
          onInput={resizeTextarea}
        />

        <button
          type="button"
          className="composer-submit"
          aria-label="Tóm tắt"
          disabled={busy || (!draft.trim() && !pendingFile)}
          onClick={onSend}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden>
            <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" />
          </svg>
        </button>
      </div>

      <input
        id="composer-file-input"
        ref={fileRef}
        type="file"
        className="sr-only"
        accept=".txt,.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
        onChange={(e) => onFileSelect(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
