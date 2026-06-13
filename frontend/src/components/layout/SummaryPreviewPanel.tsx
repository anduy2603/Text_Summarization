import { useState } from "react";
import { exportSummaryAsDocx } from "../../api";
import { LENGTH_PRESETS, type LengthPresetId } from "../../constants";
import { ENGINE_LABELS } from "../../lib/engineLabels";
import { formatDocumentMetaLine } from "../../lib/documentRecord";
import { getRating, setRating, type Rating } from "../../lib/ratings";
import { splitSummaryBullets } from "../../lib/workspace";
import type { ChatSession } from "../../types/session";
import { CopyButton } from "../CopyButton";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  session: ChatSession | null;
  processing: boolean;
  layout?: "sidebar" | "sheet";
  onRetry?: (sessionId: string, preset: LengthPresetId) => void;
};

export function SummaryPreviewPanel({ session, processing, layout = "sidebar", onRetry }: Props) {
  const wrapperClass =
    layout === "sheet"
      ? "flex min-h-0 flex-1 flex-col"
      : "hidden w-[380px] shrink-0 flex-col overflow-hidden border-l border-outline-variant bg-surface-container-lowest lg:flex";

  const assistant = session
    ? session.messages
        .slice()
        .reverse()
        .find((m): m is Extract<typeof m, { role: "assistant" }> => m.role === "assistant")
    : null;

  const doc = session?.document;
  const summary = doc?.summary?.trim() ?? assistant?.content?.trim() ?? "";
  const stats = assistant?.stats ?? null;
  const isHybrid = stats?.engineName === "hybrid";
  const parsed = summary ? parseHybridSummary(summary) : null;
  const bullets = summary
    ? (parsed ? parsed.bullets : splitSummaryBullets(summary))
    : [];
  const hybridLead = parsed?.lead ?? null;

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
        className={`flex items-center justify-between border-b border-outline-variant ${layout === "sheet" ? "px-4 py-2.5" : "px-5 py-3.5"}`}
      >
        <span className="text-xs font-semibold text-on-surface-variant">
          Xem trước tóm tắt
        </span>
        <div className="flex items-center gap-1">
          <RatingButtons sessionId={session.id} />
          <CopyButton text={summary} variant="icon" />
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto custom-scrollbar ${layout === "sheet" ? "p-4" : "p-5"}`}>
        <h2 className={`font-bold leading-snug text-on-surface ${layout === "sheet" ? "mb-3 text-sm" : "mb-3 text-lg"}`}>
          {session.title}
        </h2>

        {/* Metadata badges */}
        <div className="mb-3 flex flex-wrap gap-1.5">
          {stats?.engineName ? (
            <Badge
              icon="memory"
              label={ENGINE_LABELS[stats.engineName] ?? stats.engineName}
              highlight
            />
          ) : null}
          {doc?.fileType ? <Badge icon="description" label={doc.fileType} /> : null}
          {stats?.compressionPct != null ? (
            <Badge icon="compress" label={`Nén ${Math.round(stats.compressionPct)}%`} />
          ) : null}
          {doc && doc.selectedSentenceCount != null && doc.sourceSentenceCount != null ? (
            <Badge
              icon="format_list_numbered"
              label={`${doc.selectedSentenceCount}/${doc.sourceSentenceCount} câu`}
            />
          ) : null}
          <Badge icon="schedule" label={`${estimateRead(summary)} phút đọc`} />
          {stats?.latencyMs != null ? (
            <Badge icon="bolt" label={`${stats.latencyMs} ms`} />
          ) : null}
        </div>

        {doc ? (
          <p className="mb-4 text-[11px] text-on-surface-variant">
            {formatDocumentMetaLine(doc)}
            {" · "}
            {formatCreatedAt(doc.createdAt)}
          </p>
        ) : null}

        {/* Summary content */}
        <div className="space-y-3 leading-relaxed">
          {isHybrid && hybridLead ? (
            <>
              <div>
                <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-outline">
                  Điểm cốt lõi
                </p>
                <p className="text-sm text-on-surface">{hybridLead}</p>
              </div>
              {bullets.length > 0 ? (
                <div>
                  <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-outline">
                    Ý chính
                  </p>
                  <ul className="space-y-1.5">
                    {bullets.map((line, i) => (
                      <li key={i} className="flex gap-2 text-sm text-on-surface-variant">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                        <span>{line}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </>
          ) : (
            <ul className="space-y-2">
              {bullets.map((line, i) => (
                <li key={i} className="flex gap-2 text-sm text-on-surface-variant">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {layout === "sidebar" ? (
        <div className="border-t border-outline-variant bg-surface-container-low p-4 space-y-3">
          {onRetry ? (
            <RetryBar sessionId={session.id} onRetry={onRetry} />
          ) : null}
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
      <p className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-outline">
        Xuất tóm tắt
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleTxt}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-outline-variant py-2.5 text-sm font-medium text-on-surface transition-all duration-200 hover:bg-surface-container active:scale-[0.97]"
        >
          <MaterialIcon name="download" size="sm" />
          TXT
        </button>
        <button
          type="button"
          onClick={handleDocx}
          disabled={exporting}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:bg-primary/90 active:scale-[0.97] disabled:opacity-60"
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
      className={`flex items-center gap-1 rounded-md px-2 py-1 ${
        highlight ? "bg-primary-fixed text-on-primary-fixed-variant" : "bg-surface-container text-on-surface-variant"
      }`}
    >
      <MaterialIcon name={icon} className={highlight ? "text-primary" : "text-outline"} size="sm" />
      <span className="text-[11px] font-medium">{label}</span>
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

function parseHybridSummary(text: string): { lead: string; bullets: string[] } | null {
  if (!text.includes("Điểm cốt lõi:") && !text.includes("Ý chính:")) return null;
  const parts = text.split(/\n+Ý chính:\s*\n*/);
  const lead = (parts[0] ?? "")
    .replace(/^Điểm cốt lõi:\s*\n*/i, "")
    .trim();
  const bullets = (parts[1] ?? "")
    .split(/\n+/)
    .map((l) => l.replace(/^[\s\-•*]+/, "").trim())
    .filter(Boolean);
  return { lead, bullets };
}

function RetryBar({
  sessionId,
  onRetry,
}: {
  sessionId: string;
  onRetry: (id: string, preset: LengthPresetId) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      {open ? (
        <div className="rounded-xl border border-outline-variant bg-surface-container p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-outline">
            Tóm tắt lại với độ dài
          </p>
          <div className="flex gap-2">
            {LENGTH_PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  onRetry(sessionId, p.id);
                  setOpen(false);
                }}
                className="flex flex-1 flex-col items-center rounded-lg border border-outline-variant bg-surface-container-lowest py-2 text-xs font-semibold text-on-surface transition-all hover:border-primary/40 hover:bg-primary-fixed active:scale-[0.97]"
              >
                {p.label}
                <span className="text-[10px] font-normal text-outline">~{p.sentences} câu</span>
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="mt-2 w-full text-center text-[10px] text-on-surface-variant hover:text-on-surface"
          >
            Hủy
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-outline-variant py-2 text-xs font-medium text-on-surface-variant transition-all hover:bg-surface-container hover:text-on-surface active:scale-[0.97]"
        >
          <MaterialIcon name="refresh" size="sm" />
          Tóm tắt lại
        </button>
      )}
    </div>
  );
}

function RatingButtons({ sessionId }: { sessionId: string }) {
  const [rating, setRatingState] = useState<Rating | null>(() => getRating(sessionId));

  const handleRate = (value: Rating) => {
    const next = rating === value ? null : value;
    setRating(sessionId, next);
    setRatingState(next);
  };

  return (
    <div className="flex gap-0.5">
      <button
        type="button"
        title="Tóm tắt tốt"
        onClick={() => handleRate("up")}
        className={`rounded-lg p-1.5 transition-colors ${
          rating === "up"
            ? "bg-emerald-50 text-emerald-600"
            : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
        }`}
      >
        <MaterialIcon name="thumb_up" size="sm" />
      </button>
      <button
        type="button"
        title="Tóm tắt chưa tốt"
        onClick={() => handleRate("down")}
        className={`rounded-lg p-1.5 transition-colors ${
          rating === "down"
            ? "bg-red-50 text-red-500"
            : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
        }`}
      >
        <MaterialIcon name="thumb_down" size="sm" />
      </button>
    </div>
  );
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
      <div className="border-b border-outline-variant px-5 py-3.5">
        <span className="text-xs font-semibold text-on-surface-variant">
          Xem trước tóm tắt
        </span>
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
        {spinner ? (
          <div className="h-7 w-7 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        ) : (
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-2xl ${isError ? "bg-red-50" : "bg-surface-container"}`}
          >
            <MaterialIcon
              name={isError ? "error" : "article"}
              className={isError ? "text-error" : "text-outline"}
              size="lg"
            />
          </div>
        )}
        <p className={`text-sm ${isError ? "text-error" : "text-on-surface-variant"}`}>{message}</p>
      </div>
    </>
  );
}
