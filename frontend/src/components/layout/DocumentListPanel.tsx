import type { DocumentListItem } from "../../types/workspace";
import { FileUploadDropzone } from "../FileUploadDropzone";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  projectName: string;
  documents: DocumentListItem[];
  selectedId: string | null;
  searchQuery: string;
  onSelect: (sessionId: string) => void;
  onNewSummary: () => void;
  onUploadFile?: (file: File) => void;
  uploadBusy?: boolean;
};

function statusBadgeClass(status: DocumentListItem["status"]): string {
  if (status === "completed") return "bg-[#EEF2FF] text-on-primary-fixed-variant";
  if (status === "error") return "bg-red-50 text-red-700";
  if (status === "processing") return "bg-blue-50 text-blue-700";
  return "bg-yellow-50 text-yellow-700";
}

export function DocumentListPanel({
  projectName,
  documents,
  selectedId,
  searchQuery,
  onSelect,
  onNewSummary,
  onUploadFile,
  uploadBusy = false,
}: Props) {
  const q = searchQuery.trim().toLowerCase();
  const filtered = q
    ? documents.filter(
        (d) =>
          d.title.toLowerCase().includes(q) ||
          d.formatLabel.toLowerCase().includes(q),
      )
    : documents;

  return (
    <section className="flex min-w-0 flex-1 flex-col bg-background">
      <div className="flex items-end justify-between border-b border-outline-variant p-4 md:p-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-on-surface md:text-[28px]">
            {projectName}
          </h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            {filtered.length} tài liệu trong dự án này
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-lg border border-outline-variant p-2 text-on-surface-variant transition-colors hover:bg-surface-container lg:hidden"
            onClick={onNewSummary}
            aria-label="Tóm tắt mới"
          >
            <MaterialIcon name="add" size="sm" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-6">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-4 py-10 text-center">
            <p className="mb-6 text-sm font-medium text-on-surface">Chưa có tài liệu trong dự án</p>
            {onUploadFile ? (
              <FileUploadDropzone
                disabled={uploadBusy}
                onFile={onUploadFile}
                onTextFallback={onNewSummary}
              />
            ) : (
              <>
                <MaterialIcon name="folder_open" className="mb-3 text-outline" size="lg" />
                <button
                  type="button"
                  onClick={onNewSummary}
                  className="mt-4 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
                >
                  Tải tệp để tóm tắt
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filtered.map((doc) => {
              const selected = doc.sessionId === selectedId;
              return (
                <button
                  key={doc.sessionId}
                  type="button"
                  onClick={() => onSelect(doc.sessionId)}
                  className={`flex w-full items-center gap-4 rounded-xl p-4 text-left transition-all ${
                    selected
                      ? "ambient-shadow border-2 border-primary bg-white"
                      : "border border-outline-variant bg-white hover:border-primary/50"
                  }`}
                >
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg ${
                      selected ? "bg-primary-container/10 text-primary" : "bg-surface-container text-outline"
                    }`}
                  >
                    <MaterialIcon name={doc.icon} size="lg" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-medium">{doc.title}</h3>
                    <div className="mt-1 flex items-center gap-4">
                      <span className="text-xs text-on-surface-variant">{doc.dateLabel}</span>
                      <span className="rounded-full bg-surface-container px-2 py-0.5 text-[10px] font-bold text-primary">
                        {doc.formatLabel}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    {doc.compressionLabel ? (
                      <span
                        className={`rounded px-2 py-1 text-[10px] font-bold ${statusBadgeClass(doc.status)}`}
                      >
                        {doc.compressionLabel}
                      </span>
                    ) : null}
                    <span className="text-[10px] text-outline">
                      {doc.readMinutes != null ? `Đọc: ${doc.readMinutes} phút` : "—"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
