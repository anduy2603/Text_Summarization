import { useMemo } from "react";
import { ENGINE_LABELS } from "../lib/engineLabels";
import { lastAssistantMessage } from "../lib/workspace";
import { ratingsSummary } from "../lib/ratings";
import { MaterialIcon } from "./icons/MaterialIcon";
import type { ChatSession } from "../types/session";

type Props = { sessions: ChatSession[] };

type Stats = {
  total: number;
  byEngine: [string, number][];
  byFileType: [string, number][];
  avgCompression: number | null;
  avgLatency: number | null;
  ratings: { up: number; down: number; total: number };
};

function computeStats(sessions: ChatSession[]): Stats {
  const completed = sessions.filter((s) => {
    const a = lastAssistantMessage(s);
    return a && a.content.trim();
  });

  const byEngine: Record<string, number> = {};
  const byFileType: Record<string, number> = {};
  let totalCompression = 0;
  let compressionCount = 0;
  let totalLatency = 0;
  let latencyCount = 0;

  for (const s of completed) {
    const stats = lastAssistantMessage(s)?.stats ?? null;

    if (stats?.engineName) {
      byEngine[stats.engineName] = (byEngine[stats.engineName] ?? 0) + 1;
    }
    if (stats?.compressionPct != null) {
      totalCompression += stats.compressionPct;
      compressionCount++;
    }
    if (stats?.latencyMs != null) {
      totalLatency += stats.latencyMs;
      latencyCount++;
    }

    const ft =
      s.document?.fileType ??
      (() => {
        const u = s.messages.find((m) => m.role === "user");
        if (!u) return "TEXT";
        if (u.kind === "file") return u.fileName.split(".").pop()?.toUpperCase() ?? "FILE";
        if (u.kind === "url") return "URL";
        return "TEXT";
      })();
    byFileType[ft] = (byFileType[ft] ?? 0) + 1;
  }

  return {
    total: completed.length,
    byEngine: Object.entries(byEngine).sort((a, b) => b[1] - a[1]),
    byFileType: Object.entries(byFileType).sort((a, b) => b[1] - a[1]),
    avgCompression: compressionCount > 0 ? Math.round(totalCompression / compressionCount) : null,
    avgLatency: latencyCount > 0 ? Math.round(totalLatency / latencyCount) : null,
    ratings: ratingsSummary(),
  };
}

const ENGINE_COLORS: Record<string, string> = {
  hybrid: "bg-violet-500",
  "phobert-extractive": "bg-blue-500",
  textrank: "bg-emerald-500",
  tfidf: "bg-amber-500",
  vit5: "bg-rose-500",
};

const FILETYPE_COLORS: Record<string, string> = {
  PDF: "bg-red-400",
  DOCX: "bg-blue-400",
  TXT: "bg-gray-400",
  URL: "bg-emerald-400",
  TEXT: "bg-violet-400",
};

function BarRow({
  label,
  count,
  max,
  color,
}: {
  label: string;
  count: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 truncate text-right text-xs font-medium text-on-surface-variant">
        {label}
      </span>
      <div className="flex flex-1 items-center gap-2">
        <div className="h-5 flex-1 overflow-hidden rounded-full bg-surface-container">
          <div
            className={`h-full rounded-full transition-all duration-500 ${color}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="w-6 text-right text-xs font-bold text-on-surface">{count}</span>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  sub,
}: {
  icon: string;
  value: string;
  label: string;
  sub?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5 rounded-2xl border border-outline-variant bg-surface-container-lowest p-5">
      <div className="flex items-center gap-2 text-on-surface-variant">
        <MaterialIcon name={icon} size="sm" />
        <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-3xl font-bold text-on-surface">{value}</p>
      {sub ? <p className="text-xs text-on-surface-variant">{sub}</p> : null}
    </div>
  );
}

export function StatsPage({ sessions }: Props) {
  const stats = useMemo(() => computeStats(sessions), [sessions]);
  const maxEngine = stats.byEngine[0]?.[1] ?? 1;
  const maxFileType = stats.byFileType[0]?.[1] ?? 1;
  const satisfactionPct =
    stats.ratings.total > 0
      ? Math.round((stats.ratings.up / stats.ratings.total) * 100)
      : null;

  if (stats.total === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-background p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-container">
          <MaterialIcon name="bar_chart" className="text-outline" size="lg" />
        </div>
        <p className="text-sm font-semibold text-on-surface">Chưa có dữ liệu thống kê</p>
        <p className="max-w-xs text-xs text-on-surface-variant">
          Tóm tắt ít nhất một tài liệu để xem thống kê sử dụng.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar bg-background p-6 md:p-8">
      <div className="mx-auto max-w-3xl space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-on-surface">Thống kê sử dụng</h1>
          <p className="mt-1 text-sm text-on-surface-variant">Tổng quan từ lịch sử tóm tắt của bạn</p>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard
            icon="description"
            value={String(stats.total)}
            label="Tài liệu"
            sub="đã tóm tắt"
          />
          <StatCard
            icon="compress"
            value={stats.avgCompression != null ? `${stats.avgCompression}%` : "—"}
            label="Tỷ lệ nén TB"
            sub="nội dung so với gốc"
          />
          <StatCard
            icon="bolt"
            value={stats.avgLatency != null ? `${stats.avgLatency} ms` : "—"}
            label="Độ trễ TB"
            sub="thời gian xử lý"
          />
          <StatCard
            icon="thumb_up"
            value={satisfactionPct != null ? `${satisfactionPct}%` : "—"}
            label="Hài lòng"
            sub={
              stats.ratings.total > 0
                ? `${stats.ratings.up}👍 · ${stats.ratings.down}👎 (${stats.ratings.total} đánh giá)`
                : "Chưa có đánh giá"
            }
          />
        </div>

        {/* Engine distribution */}
        {stats.byEngine.length > 0 ? (
          <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6">
            <div className="mb-4 flex items-center gap-2">
              <MaterialIcon name="memory" size="sm" className="text-primary" />
              <h2 className="text-sm font-bold text-on-surface">Phân bố Engine sử dụng</h2>
            </div>
            <div className="space-y-3">
              {stats.byEngine.map(([engine, count]) => (
                <BarRow
                  key={engine}
                  label={ENGINE_LABELS[engine] ?? engine}
                  count={count}
                  max={maxEngine}
                  color={ENGINE_COLORS[engine] ?? "bg-primary"}
                />
              ))}
            </div>
          </div>
        ) : null}

        {/* File type distribution */}
        {stats.byFileType.length > 0 ? (
          <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6">
            <div className="mb-4 flex items-center gap-2">
              <MaterialIcon name="folder" size="sm" className="text-primary" />
              <h2 className="text-sm font-bold text-on-surface">Loại tệp đã tóm tắt</h2>
            </div>
            <div className="space-y-3">
              {stats.byFileType.map(([ft, count]) => (
                <BarRow
                  key={ft}
                  label={ft}
                  count={count}
                  max={maxFileType}
                  color={FILETYPE_COLORS[ft] ?? "bg-surface-container-high"}
                />
              ))}
            </div>
          </div>
        ) : null}

        {/* Top engine callout */}
        {stats.byEngine[0] ? (
          <div className="flex items-center gap-4 rounded-2xl border border-primary/20 bg-primary-fixed px-6 py-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
              <MaterialIcon name="emoji_events" className="text-primary" size="sm" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
                Engine được dùng nhiều nhất
              </p>
              <p className="text-base font-bold text-on-surface">
                {ENGINE_LABELS[stats.byEngine[0][0]] ?? stats.byEngine[0][0]}
                <span className="ml-2 text-sm font-normal text-on-surface-variant">
                  ({stats.byEngine[0][1]} lần · {Math.round((stats.byEngine[0][1] / stats.total) * 100)}% tổng số)
                </span>
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
