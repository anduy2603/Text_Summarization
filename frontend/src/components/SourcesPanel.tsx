import { useRef, useState } from "react";
import type { SourceItem } from "../types/sources";
import { sourceKindIcon } from "../lib/sources";

type AddMode = "file" | "text" | "url";

type Props = {
  sources: SourceItem[];
  activeId: string | null;
  busy: boolean;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onAddFile: (file: File) => void;
  onAddText: (text: string) => void;
  onAddUrl: (url: string) => void;
};

function isHttpUrl(value: string): boolean {
  try {
    const u = new URL(value.trim());
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export function SourcesPanel({
  sources,
  activeId,
  busy,
  onSelect,
  onRemove,
  onAddFile,
  onAddText,
  onAddUrl,
}: Props) {
  const [showAdd, setShowAdd] = useState(false);
  const [addMode, setAddMode] = useState<AddMode>("file");
  const [draftText, setDraftText] = useState("");
  const [draftUrl, setDraftUrl] = useState("");
  const [addErr, setAddErr] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const active = sources.find((s) => s.id === activeId) ?? null;

  const resetAddForm = () => {
    setDraftText("");
    setDraftUrl("");
    setAddErr(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onConfirmAdd = () => {
    setAddErr(null);
    if (addMode === "file") {
      setAddErr("Chọn tệp .txt, .docx hoặc .pdf bên dưới.");
      return;
    }
    if (addMode === "text") {
      const t = draftText.trim();
      if (!t) {
        setAddErr("Nhập hoặc dán văn bản.");
        return;
      }
      onAddText(t);
      resetAddForm();
      setShowAdd(false);
      return;
    }
    const url = draftUrl.trim();
    if (!url || !isHttpUrl(url)) {
      setAddErr("URL phải bắt đầu bằng http:// hoặc https://");
      return;
    }
    onAddUrl(url);
    resetAddForm();
    setShowAdd(false);
  };

  const onFileChosen = (file: File | null) => {
    if (!file) return;
    onAddFile(file);
    resetAddForm();
    setShowAdd(false);
  };

  return (
    <aside className="panel sources-panel" aria-label="Nguồn tài liệu">
      <div className="panel-head">
        <h2 className="panel-title">Nguồn</h2>
        <button
          type="button"
          className="btn-add-source"
          disabled={busy}
          onClick={() => setShowAdd((v) => !v)}
          aria-expanded={showAdd}
        >
          + Thêm
        </button>
      </div>

      {showAdd ? (
        <div className="add-source-box">
          <div className="mode-tabs" role="tablist" aria-label="Loại nguồn">
            {(
              [
                ["file", "Tệp"],
                ["text", "Văn bản"],
                ["url", "Link"],
              ] as const
            ).map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                role="tab"
                aria-selected={addMode === mode}
                className={`mode-tab ${addMode === mode ? "active" : ""}`}
                onClick={() => {
                  setAddMode(mode);
                  setAddErr(null);
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {addMode === "file" ? (
            <button
              type="button"
              className="composer-file-pick small"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
            >
              Chọn tệp…
            </button>
          ) : addMode === "url" ? (
            <input
              type="url"
              className="composer-input"
              placeholder="https://…"
              value={draftUrl}
              onChange={(e) => setDraftUrl(e.target.value)}
              disabled={busy}
            />
          ) : (
            <textarea
              className="composer-textarea small"
              rows={4}
              placeholder="Dán văn bản tiếng Việt…"
              value={draftText}
              onChange={(e) => setDraftText(e.target.value)}
              disabled={busy}
            />
          )}

          <input
            ref={fileInputRef}
            type="file"
            className="file-input-hidden"
            accept=".txt,.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            onChange={(e) => onFileChosen(e.target.files?.[0] ?? null)}
          />

          {addMode !== "file" ? (
            <button type="button" className="btn secondary full-width" disabled={busy} onClick={onConfirmAdd}>
              Thêm vào notebook
            </button>
          ) : null}

          {addErr ? <p className="add-err muted small">{addErr}</p> : null}
        </div>
      ) : null}

      <ul className="source-list" role="list">
        {sources.length === 0 ? (
          <li className="source-empty muted small">Chưa có nguồn. Nhấn + Thêm để bắt đầu.</li>
        ) : (
          sources.map((src) => (
            <li key={src.id}>
              <button
                type="button"
                className={`source-card ${activeId === src.id ? "active" : ""}`}
                onClick={() => onSelect(src.id)}
                aria-current={activeId === src.id ? "true" : undefined}
              >
                <span className="source-card-icon" aria-hidden>
                  {sourceKindIcon(src.kind)}
                </span>
                <span className="source-card-body">
                  <span className="source-card-title">{src.title}</span>
                  <span className="source-card-meta muted small">
                    {src.status === "summarizing"
                      ? "Đang tóm tắt…"
                      : src.status === "error"
                        ? "Lỗi"
                        : src.status === "summarized"
                          ? "Đã tóm tắt"
                          : "Sẵn sàng"}
                  </span>
                </span>
                <span
                  role="button"
                  tabIndex={0}
                  className="source-remove"
                  aria-label={`Xóa ${src.title}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(src.id);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      e.stopPropagation();
                      onRemove(src.id);
                    }
                  }}
                >
                  ×
                </span>
              </button>
            </li>
          ))
        )}
      </ul>

      {active ? (
        <div className="source-preview">
          <h3 className="preview-title">Xem trước</h3>
          <p className="preview-text muted small">{active.preview}</p>
          {active.lastSummary ? (
            <p className="preview-summary muted small">
              <strong>Tóm tắt gần nhất:</strong> {active.lastSummary.slice(0, 160)}
              {active.lastSummary.length > 160 ? "…" : ""}
            </p>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
