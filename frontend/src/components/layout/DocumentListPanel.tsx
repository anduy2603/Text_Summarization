import { useState } from "react";
import { LENGTH_PRESETS, type LengthPresetId } from "../../constants";
import type { DocumentListItem } from "../../types/workspace";
import { FileUploadDropzone } from "../FileUploadDropzone";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  projectName: string;
  documents: DocumentListItem[];
  selectedId: string | null;
  searchQuery: string;
  onSelect: (sessionId: string) => void;
  onDelete?: (sessionId: string) => void;
  onNewSummary: () => void;
  onUploadFile?: (file: File) => void;
  onNewSummaryFromFile?: (file: File, preset: LengthPresetId) => void;
  uploadBusy?: boolean;
};

function statusBadgeClass(status: DocumentListItem["status"]): string {
  if (status === "completed") return "bg-primary-fixed text-on-primary-fixed-variant";
  if (status === "error") return "bg-red-50 text-red-700";
  if (status === "processing") return "bg-blue-50 text-blue-700";
  return "bg-yellow-50 text-yellow-700";
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "picture_as_pdf";
  if (ext === "docx" || ext === "doc") return "article";
  return "text_snippet";
}

function PendingFileCard({
  file,
  preset,
  onPresetChange,
  onConfirm,
  onCancel,
  busy,
}: {
  file: File;
  preset: LengthPresetId;
  onPresetChange: (p: LengthPresetId) => void;
  onConfirm: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-5 px-4 py-12">
      {/* File card */}
      <div className="flex w-full max-w-md items-center gap-3 rounded-2xl border border-primary/20 bg-primary-fixed px-4 py-3.5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
          <MaterialIcon name={fileIcon(file.name)} size="sm" className="text-primary" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-on-surface">{file.name}</p>
          <p className="text-xs text-on-surface-variant">{formatFileSize(file.size)}</p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="shrink-0 rounded-lg p-1 text-on-surface-variant transition-colors hover:bg-primary/10 hover:text-on-surface"
          aria-label="Hủy"
        >
          <MaterialIcon name="close" size="sm" />
        </button>
      </div>

      {/* Preset selector */}
      <div className="w-full max-w-md">
        <p className="mb-2.5 text-center text-xs font-semibold text-on-surface-variant">
          Chọn độ dài bản tóm tắt
        </p>
        <div className="flex gap-2">
          {LENGTH_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              disabled={busy}
              onClick={() => onPresetChange(p.id)}
              className={`flex flex-1 flex-col items-center rounded-xl border px-3 py-3 transition-all duration-150 active:scale-[0.97] ${
                preset === p.id
                  ? "border-primary bg-primary text-white shadow-sm"
                  : "border-outline-variant bg-surface-container-lowest text-on-surface-variant hover:border-primary/40 hover:bg-surface-container"
              }`}
            >
              <span className="text-sm font-bold">{p.label}</span>
              <span className={`text-[10px] ${preset === p.id ? "text-white/80" : "text-outline"}`}>
                ~{p.sentences} câu
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex w-full max-w-md flex-col gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={onConfirm}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-primary/90 active:scale-[0.97] disabled:opacity-60"
        >
          <MaterialIcon name="auto_awesome" size="sm" />
          Bắt đầu tóm tắt
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onCancel}
          className="w-full rounded-xl py-2.5 text-xs font-medium text-on-surface-variant transition-colors hover:text-on-surface"
        >
          Hủy, chọn tệp khác
        </button>
      </div>
    </div>
  );
}

export function DocumentListPanel({
  projectName,
  documents,
  selectedId,
  searchQuery,
  onSelect,
  onDelete,
  onNewSummary,
  onUploadFile,
  onNewSummaryFromFile,
  uploadBusy = false,
}: Props) {
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreset, setPendingPreset] = useState<LengthPresetId>("medium");

  const q = searchQuery.trim().toLowerCase();
  const filtered = q
    ? documents.filter(
        (d) =>
          d.title.toLowerCase().includes(q) ||
          d.formatLabel.toLowerCase().includes(q),
      )
    : documents;

  const handleFilePicked = (file: File) => {
    if (onNewSummaryFromFile) {
      setPendingPreset("medium");
      setPendingFile(file);
    } else {
      onUploadFile?.(file);
    }
  };

  const handleConfirm = () => {
    if (!pendingFile) return;
    onNewSummaryFromFile?.(pendingFile, pendingPreset);
    setPendingFile(null);
  };

  return (
    <section className="flex min-w-0 flex-1 flex-col bg-background">
      <div className="flex items-center justify-between border-b border-outline-variant px-4 py-4 md:px-6 md:py-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-on-surface md:text-2xl">
            {projectName}
          </h1>
          <p className="mt-0.5 text-sm text-on-surface-variant">
            {filtered.length} tài liệu
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-lg border border-outline-variant px-3 py-1.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface active:scale-[0.97] lg:hidden"
            onClick={onNewSummary}
            aria-label="Tóm tắt mới"
          >
            <MaterialIcon name="add" size="sm" />
            <span className="hidden sm:inline">Mới</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-5">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-4 py-4 text-center">
            {pendingFile ? (
              <PendingFileCard
                file={pendingFile}
                preset={pendingPreset}
                onPresetChange={setPendingPreset}
                onConfirm={handleConfirm}
                onCancel={() => setPendingFile(null)}
                busy={uploadBusy}
              />
            ) : (
              <FileUploadDropzone
                disabled={uploadBusy}
                onFile={handleFilePicked}
                onTextFallback={onNewSummary}
              />
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {pendingFile ? (
              <div className="mb-2 rounded-2xl border border-outline-variant bg-surface-container-lowest">
                <PendingFileCard
                  file={pendingFile}
                  preset={pendingPreset}
                  onPresetChange={setPendingPreset}
                  onConfirm={handleConfirm}
                  onCancel={() => setPendingFile(null)}
                  busy={uploadBusy}
                />
              </div>
            ) : null}
            {filtered.map((doc) => {
              const selected = doc.sessionId === selectedId;
              const canDelete = doc.status !== "processing" && !!onDelete;
              return (
                <div key={doc.sessionId} className="group relative">
                  <button
                    type="button"
                    onClick={() => onSelect(doc.sessionId)}
                    className={`flex w-full items-center gap-3 rounded-xl p-3.5 text-left transition-all duration-150 active:scale-[0.995] ${
                      canDelete ? "pr-10" : ""
                    } ${
                      selected
                        ? "ambient-shadow border border-primary/30 bg-surface-container-lowest ring-1 ring-primary/20"
                        : "border border-outline-variant bg-surface-container-lowest hover:border-primary/30 hover:bg-white"
                    }`}
                  >
                    <div
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                        selected
                          ? "bg-primary/10 text-primary"
                          : "bg-surface-container text-on-surface-variant"
                      }`}
                    >
                      {doc.status === "processing" ? (
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                      ) : (
                        <MaterialIcon name={doc.icon} size="sm" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-sm font-semibold text-on-surface">{doc.title}</h3>
                      <div className="mt-1 flex items-center gap-3">
                        <span className="text-xs text-on-surface-variant">{doc.dateLabel}</span>
                        <span className="rounded-md bg-surface-container px-1.5 py-0.5 text-[10px] font-bold text-on-surface-variant">
                          {doc.formatLabel}
                        </span>
                        {doc.status === "processing" ? (
                          <span className="text-[10px] text-primary">Đang xử lý…</span>
                        ) : null}
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1.5 transition-opacity duration-150 group-hover:opacity-0">
                      {doc.compressionLabel ? (
                        <span
                          className={`rounded-md px-2 py-0.5 text-[10px] font-bold ${statusBadgeClass(doc.status)}`}
                        >
                          {doc.compressionLabel}
                        </span>
                      ) : null}
                      <span className="text-[10px] text-outline">
                        {doc.readMinutes != null ? `${doc.readMinutes} phút đọc` : "—"}
                      </span>
                    </div>
                  </button>

                  {canDelete ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(doc.sessionId);
                      }}
                      aria-label="Xóa tài liệu"
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-on-surface-variant opacity-0 transition-all duration-150 hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                    >
                      <MaterialIcon name="delete" size="sm" />
                    </button>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
