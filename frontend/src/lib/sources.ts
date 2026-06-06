import {
  summarizeFile,
  summarizeText,
  summarizeUrl,
  type SummarizeOptions,
} from "../api";
import type { SourceItem, SourceKind } from "../types/sources";
import { formatUserSummaryStats } from "../userMetadata";

const PREVIEW_MAX = 320;

export function newSourceId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function truncatePreview(text: string, max = PREVIEW_MAX): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max)}…`;
}

export function sourceKindIcon(kind: SourceKind): string {
  if (kind === "file") return "📄";
  if (kind === "url") return "🔗";
  return "📝";
}

export function buildPreviewFromMetadata(metadata: Record<string, unknown>): string {
  const sentences =
    typeof metadata.sentence_count === "number" ? metadata.sentence_count : null;
  const chars =
    typeof metadata.cleaned_char_length === "number" ? metadata.cleaned_char_length : null;
  const fmt =
    typeof metadata.source_type === "string" ? metadata.source_type.toUpperCase() : null;
  const parts: string[] = [];
  if (fmt) parts.push(fmt);
  if (sentences != null) parts.push(`${sentences} câu`);
  if (chars != null) parts.push(`${chars.toLocaleString("vi-VN")} ký tự`);
  return parts.length > 0 ? `Đã đọc: ${parts.join(" · ")}` : "Đã xử lý nguồn.";
}

export function createSourceFromFile(file: File): SourceItem {
  return {
    id: newSourceId(),
    kind: "file",
    title: file.name,
    createdAt: Date.now(),
    status: "ready",
    preview: `Tệp · ${Math.round(file.size / 1024)} KB`,
    file,
  };
}

export function createSourceFromText(text: string): SourceItem {
  const trimmed = text.trim();
  return {
    id: newSourceId(),
    kind: "text",
    title: truncatePreview(trimmed, 48) || "Văn bản",
    createdAt: Date.now(),
    status: "ready",
    preview: truncatePreview(trimmed),
    text: trimmed,
  };
}

export function createSourceFromUrl(url: string): SourceItem {
  const u = url.trim();
  let title = u;
  try {
    const parsed = new URL(u);
    title = parsed.hostname + parsed.pathname.slice(0, 40);
  } catch {
    /* keep full url */
  }
  return {
    id: newSourceId(),
    kind: "url",
    title: truncatePreview(title, 56),
    createdAt: Date.now(),
    status: "ready",
    preview: truncatePreview(u, 120),
    url: u,
  };
}

export async function summarizeSourceItem(
  source: SourceItem,
  options: SummarizeOptions,
): Promise<
  | { ok: true; summary: string; metadata: Record<string, unknown>; stats: ReturnType<typeof formatUserSummaryStats> }
  | { ok: false; error: string }
> {
  if (source.kind === "file") {
    if (!source.file) return { ok: false, error: "Thiếu tệp đính kèm." };
    const result = await summarizeFile(source.file, options);
    if ("error" in result) return { ok: false, error: result.error };
    return {
      ok: true,
      summary: result.summary,
      metadata: result.metadata ?? {},
      stats: formatUserSummaryStats(result.metadata ?? {}, source.file.name),
    };
  }
  if (source.kind === "url") {
    if (!source.url) return { ok: false, error: "Thiếu URL." };
    const result = await summarizeUrl(source.url, options);
    if ("error" in result) return { ok: false, error: result.error };
    return {
      ok: true,
      summary: result.summary,
      metadata: result.metadata ?? {},
      stats: formatUserSummaryStats(result.metadata ?? {}),
    };
  }
  if (!source.text) return { ok: false, error: "Thiếu nội dung văn bản." };
  const result = await summarizeText({ text: source.text, ...options });
  if ("error" in result) return { ok: false, error: result.error };
  return {
    ok: true,
    summary: result.summary,
    metadata: result.metadata ?? {},
    stats: formatUserSummaryStats(result.metadata ?? {}),
  };
}
