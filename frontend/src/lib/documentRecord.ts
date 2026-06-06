import type { ChatMessage } from "../types/chat";
import type { SummaryDocumentRecord } from "../types/documentRecord";
import type { ChatSession } from "../types/session";
import type { UserSummaryStats } from "../userMetadata";

const FILE_TYPE_LABELS: Record<string, string> = {
  txt: "TXT",
  docx: "DOCX",
  pdf: "PDF",
  text: "TEXT",
  url: "URL",
};

export function normalizeFileType(
  sourceType: string | null | undefined,
  fileName?: string | null,
): string {
  if (sourceType) {
    const key = sourceType.toLowerCase();
    return FILE_TYPE_LABELS[key] ?? key.toUpperCase();
  }
  if (fileName) {
    const ext = fileName.split(".").pop()?.toLowerCase();
    if (ext === "txt") return "TXT";
    if (ext === "docx") return "DOCX";
    if (ext === "pdf") return "PDF";
  }
  return "TEXT";
}

export function resolveFilename(
  input: { file: File | null; text: string },
  stats: UserSummaryStats,
): string | null {
  if (input.file?.name?.trim()) return input.file.name.trim();
  if (stats.fileName?.trim()) return stats.fileName.trim();
  const text = input.text.trim();
  if (text && /^https?:\/\//i.test(text)) {
    try {
      const u = new URL(text);
      return u.hostname + u.pathname.replace(/\/$/, "") || u.hostname;
    } catch {
      return text.slice(0, 80);
    }
  }
  if (text) return "Văn bản dán";
  return null;
}

export function buildDocumentRecord(params: {
  input: { file: File | null; text: string };
  summary: string;
  stats: UserSummaryStats;
  metadata: Record<string, unknown>;
  createdAt?: number;
}): SummaryDocumentRecord {
  const { input, summary, stats, metadata, createdAt } = params;
  const sourceType =
    typeof metadata.source_type === "string" ? metadata.source_type : null;

  const sourceSentenceCount =
    stats.sourceSentences ??
    (typeof metadata.sentence_count === "number" ? metadata.sentence_count : null);

  const selectedSentenceCount =
    stats.selectedSentences ??
    (typeof metadata.selected_sentence_count === "number"
      ? metadata.selected_sentence_count
      : typeof metadata.resolved_target_k === "number"
        ? metadata.resolved_target_k
        : null);

  return {
    filename: resolveFilename(input, stats),
    fileType: normalizeFileType(sourceType, stats.fileName ?? input.file?.name),
    summary: summary.trim(),
    sourceSentenceCount,
    selectedSentenceCount,
    createdAt: createdAt ?? Date.now(),
  };
}

export function documentRecordFromSession(session: ChatSession): SummaryDocumentRecord | null {
  if (session.document?.summary?.trim()) {
    return session.document;
  }
  const assistant = session.messages
    .slice()
    .reverse()
    .find((m): m is Extract<ChatMessage, { role: "assistant" }> => m.role === "assistant");
  if (!assistant?.content.trim()) return null;

  const firstUser = session.messages.find((m) => m.role === "user");
  let fileType = "TEXT";
  let filename: string | null = session.title || null;

  if (firstUser?.role === "user") {
    if (firstUser.kind === "file") {
      filename = firstUser.fileName;
      fileType = normalizeFileType(null, firstUser.fileName);
    } else if (firstUser.kind === "url") {
      fileType = "URL";
      try {
        const u = new URL(firstUser.url);
        filename = u.hostname;
      } catch {
        filename = "Link";
      }
    } else if (firstUser.kind === "text") {
      fileType = "TEXT";
      filename = filename ?? "Văn bản dán";
    }
  }

  const stats = assistant.stats;
  return {
    filename,
    fileType: stats?.formatLabel ?? fileType,
    summary: assistant.content.trim(),
    sourceSentenceCount: stats?.sourceSentences ?? null,
    selectedSentenceCount: stats?.selectedSentences ?? null,
    createdAt: session.createdAt,
  };
}

export function formatDocumentMetaLine(doc: SummaryDocumentRecord): string {
  const parts: string[] = [doc.fileType];
  if (doc.filename) parts.push(doc.filename);
  if (doc.selectedSentenceCount != null && doc.sourceSentenceCount != null) {
    parts.push(`${doc.selectedSentenceCount}/${doc.sourceSentenceCount} câu`);
  }
  return parts.join(" · ");
}
