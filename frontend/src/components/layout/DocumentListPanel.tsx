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
  if (status === "completed") return "bg-primary-fixed text-on-primary-fixed-variant";
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
          <div className="flex flex-col items-center justify-center px-4 py-16 text-center">
            {onUploadFile ? (
              <FileUploadDropzone
                disabled={uploadBusy}
                onFile={onUploadFile}
                onTextFallback={onNewSummary}
              />
            ) : (
              <>
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-container">
                  <MaterialIcon name="folder_open" className="text-outline" size="lg" />
                </div>
                <p className="mb-1 text-sm font-semibold text-on-surface">Chưa có tài liệu</p>
                <p className="mb-5 text-xs text-on-surface-variant">Tải tệp để bắt đầu tóm tắt</p>
                <button
                  type="button"
                  onClick={onNewSummary}
                  className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-primary/90 active:scale-[0.97]"
                >
                  Tải tệp lên
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filtered.map((doc) => {
              const selected = doc.sessionId === selectedId;
              return (
                <button
                  key={doc.sessionId}
                  type="button"
                  onClick={() => onSelect(doc.sessionId)}
                  className={`flex w-full items-center gap-3 rounded-xl p-3.5 text-left transition-all duration-150 active:scale-[0.995] ${
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
                    <MaterialIcon name={doc.icon} size="sm" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate text-sm font-semibold text-on-surface">{doc.title}</h3>
                    <div className="mt-1 flex items-center gap-3">
                      <span className="text-xs text-on-surface-variant">{doc.dateLabel}</span>
                      <span className="rounded-md bg-surface-container px-1.5 py-0.5 text-[10px] font-bold text-on-surface-variant">
                        {doc.formatLabel}
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1.5">
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
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
