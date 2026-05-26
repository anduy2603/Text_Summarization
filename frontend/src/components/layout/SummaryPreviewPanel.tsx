import { useState } from "react";
import { exportSummaryAsDocx } from "../../api";
import { ENGINE_LABELS } from "../../lib/engineLabels";
import { formatDocumentMetaLine } from "../../lib/documentRecord";
import { splitSummaryBullets } from "../../lib/workspace";
import type { ChatSession } from "../../types/session";
import { CopyButton } from "../CopyButton";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  session: ChatSession | null;
  processing: boolean;
  layout?: "sidebar" | "sheet";
};

export function SummaryPreviewPanel({ session, processing, layout = "sidebar" }: Props) {
  const wrapperClass =
    layout === "sheet"
      ? "flex min-h-0 flex-1 flex-col"
      : "hidden w-[400px] shrink-0 flex-col overflow-hidden border-l border-outline-variant bg-white xl:flex";

  const assistant = session
    ? session.messages
        .slice()
        .reverse()
        .find((m): m is Extract<typeof m, { role: "assistant" }> => m.role === "assistant")
    : null;

  const doc = session?.document;
  const summary = doc?.summary?.trim() ?? assistant?.content?.trim() ?? "";
  const stats = assistant?.stats ?? null;
  const bullets = summary ? splitSummaryBullets(summary) : [];
  const detail =
    bullets.length > 0 && summary.length > bullets.join(" ").length + 40 ? summary : null;

  if (!session) {
    return (
      <aside className={wrapperClass}>
        <PreviewEmpty message="Chọn một tài liệu để xem tóm tắt" />
      </aside>
    );
  }

  if (processing) {
    return (
      <aside className={wrapperClass}>
        <PreviewEmpty message="Đang tạo bản tóm tắt…" spinner />
      </aside>
    );
  }

  if (!summary) {
    const err = session.messages
      .slice()
      .reverse()
      .find(
        (m): m is Extract<typeof m, { role: "system"; tone: "error" }> =>
          m.role === "system" && m.tone === "error",
      );
    return (
      <aside className={wrapperClass}>
        <PreviewEmpty
          message={err?.content ?? "Tài liệu chưa có bản tóm tắt."}
          isError={Boolean(err)}
        />
      </aside>
    );
  }

  return (
    <aside className={wrapperClass}>
      <div
        className={`flex items-center justify-between border-b border-outline-variant ${layout === "sheet" ? "px-4 py-2" : "p-6"}`}
      >
        <span className="text-sm font-bold uppercase tracking-wide text-outline">
          Xem trước tóm tắt
        </span>
        <div className="flex gap-1">
          <CopyButton text={summary} variant="icon" />
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto custom-scrollbar ${layout === "sheet" ? "p-4" : "p-6"}`}>
        {layout === "sidebar" ? (
          <div className="mb-6 flex h-32 w-full items-center justify-center rounded-xl bg-gradient-to-br from-primary-container/20 to-surface-container">
            <MaterialIcon name="analytics" className="text-primary opacity-80" size="lg" />
          </div>
        ) : null}

        <h2 className={`font-semibold leading-snug text-on-surface ${layout === "sheet" ? "mb-2 text-base" : "mb-4 text-xl"}`}>
          {session.title}
        </h2>

        {/* Metrics badges */}
        <div className="mb-4 flex flex-wrap gap-2">
          {stats?.engineName ? (
            <Badge
              icon="memory"
              label={ENGINE_LABELS[stats.engineName] ?? stats.engineName}
              highlight
            />
          ) : null}
          {stats?.compressionPct != null ? (
            <Badge icon="analytics" label={`${Math.round(stats.compressionPct)}% nén`} />
          ) : null}
          <Badge icon="schedule" label={`${estimateRead(summary)} phút đọc`} />
          {doc?.fileType ? <Badge icon="fact_check" label={doc.fileType} /> : null}
          {doc && doc.selectedSentenceCount != null && doc.sourceSentenceCount != null ? (
            <Badge
              icon="format_list_numbered"
              label={`${doc.selectedSentenceCount}/${doc.sourceSentenceCount} câu`}
            />
          ) : null}
          {stats?.latencyMs != null ? (
            <Badge icon="bolt" label={`${stats.latencyMs} ms`} />
          ) : null}
        </div>

        {doc ? (
          <p className="mb-4 text-xs text-on-surface-variant">
            {formatDocumentMetaLine(doc)}
            {" · "}
            {formatCreatedAt(doc.createdAt)}
          </p>
        ) : null}

        <div className="space-y-3 leading-relaxed text-on-surface-variant">
          <h4 className="text-sm font-bold text-on-surface">Điểm cốt lõi:</h4>
          <ul className="list-disc space-y-2 pl-5 text-sm">
            {bullets.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
          {detail && layout === "sidebar" ? (
            <>
              <h4 className="mt-4 text-sm font-bold text-on-surface">Phân tích chi tiết:</h4>
              <p className="line-clamp-4 text-sm">{detail}</p>
            </>
          ) : null}
        </div>
      </div>

      {layout === "sidebar" ? (
        <div className="border-t border-outline-variant bg-surface-container-low p-4">
          <ExportButtons title={session.title} summary={summary} />
        </div>
      ) : null}
    </aside>
  );
}

function ExportButtons({ title, summary }: { title: string; summary: string }) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleTxt = () => {
    const blob = new Blob([summary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.slice(0, 40).replace(/[^\wÀ-ɏ\s-]/g, "") || "tom-tat"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDocx = async () => {
    setExporting(true);
    setExportError(null);
    const result = await exportSummaryAsDocx(title, summary);
    setExporting(false);
    if ("error" in result) {
      setExportError(result.error);
      return;
    }
    const url = URL.createObjectURL(result.blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.slice(0, 40).replace(/[^\wÀ-ɏ\s-]/g, "") || "tom-tat"}.docx`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleTxt}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-outline-variant py-2.5 text-sm font-medium text-on-surface hover:bg-surface-container"
        >
          <MaterialIcon name="download" size="sm" />
          TXT
        </button>
        <button
          type="button"
          onClick={handleDocx}
          disabled={exporting}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
        >
          {exporting ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <MaterialIcon name="download" size="sm" />
          )}
          DOCX
        </button>
      </div>
      {exportError ? (
        <p className="text-xs text-error">{exportError}</p>
      ) : null}
    </div>
  );
}

function Badge({ icon, label, highlight }: { icon: string; label: string; highlight?: boolean }) {
  return (
    <div
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1 ${
        highlight ? "bg-primary-container/30" : "bg-surface-container"
      }`}
    >
      <MaterialIcon name={icon} className="text-primary" size="sm" />
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

function estimateRead(summary: string): number {
  return Math.max(1, Math.ceil(summary.length / 450));
}

function formatCreatedAt(ts: number): string {
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(ts));
}

function PreviewEmpty({
  message,
  spinner,
  isError,
}: {
  message: string;
  spinner?: boolean;
  isError?: boolean;
}) {
  return (
    <>
      <div className="border-b border-outline-variant p-4 md:p-6">
        <span className="text-sm font-bold uppercase tracking-wide text-outline">
          Xem trước tóm tắt
        </span>
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
        {spinner ? (
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        ) : (
          <MaterialIcon
            name={isError ? "error" : "summarize"}
            className={isError ? "text-error" : "text-outline"}
            size="lg"
          />
        )}
        <p className={`text-sm ${isError ? "text-error" : "text-on-surface-variant"}`}>{message}</p>
      </div>
    </>
  );
}
