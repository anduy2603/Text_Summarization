import type { ChatMessage } from "../types/chat";
import type { ChatSession } from "../types/session";
import type { DocumentListItem, DocumentStatus, Project } from "../types/workspace";
import type { UserSummaryStats } from "../userMetadata";
import { sessionHasUserMessages } from "./chatHistory";

import { DEFAULT_PROJECT_ID } from "../constants";

const PROJECTS_KEY = "vietsum_projects_v1";
export { DEFAULT_PROJECT_ID };
const SEED_PROJECTS: Project[] = [
  { id: DEFAULT_PROJECT_ID, name: "Dự án của tôi", createdAt: Date.now() },
];

export function newProjectId(): string {
  return `proj_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function loadProjects(): Project[] {
  try {
    const raw = localStorage.getItem(PROJECTS_KEY);
    if (!raw) return SEED_PROJECTS;
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) return SEED_PROJECTS;
    return parsed.filter(
      (p): p is Project =>
        typeof p === "object" &&
        p !== null &&
        typeof (p as Project).id === "string" &&
        typeof (p as Project).name === "string",
    ) as Project[];
  } catch {
    return SEED_PROJECTS;
  }
}

export function saveProjects(projects: Project[]): void {
  try {
    localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects));
  } catch {
    /* ignore */
  }
}

export function ensureSessionProject(session: ChatSession): ChatSession {
  if (session.projectId) return session;
  return { ...session, projectId: DEFAULT_PROJECT_ID };
}

function formatLabelFromMessage(msg: ChatMessage | undefined, stats: UserSummaryStats | null): string {
  if (stats?.formatLabel) return stats.formatLabel;
  if (!msg || msg.role !== "user") return "TEXT";
  if (msg.kind === "file") {
    const ext = msg.fileName.split(".").pop()?.toUpperCase();
    return ext && ext.length <= 5 ? ext : "FILE";
  }
  if (msg.kind === "url") return "URL";
  return "TEXT";
}

function iconForFormat(format: string): DocumentListItem["icon"] {
  if (format === "URL") return "language";
  return "description";
}

function formatDate(ts: number): string {
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(ts));
}

export function estimateReadMinutes(text: string): number {
  const len = text.trim().length;
  if (len < 80) return 1;
  return Math.max(1, Math.ceil(len / 450));
}

export function lastAssistantMessage(session: ChatSession): Extract<ChatMessage, { role: "assistant" }> | null {
  for (let i = session.messages.length - 1; i >= 0; i--) {
    const m = session.messages[i];
    if (m.role === "assistant") return m;
  }
  return null;
}

export function documentStatus(
  session: ChatSession,
  processingId: string | null,
): DocumentStatus {
  if (processingId === session.id) return "processing";
  const hasUser = sessionHasUserMessages(session.messages);
  if (!hasUser) return "pending";
  const last = session.messages[session.messages.length - 1];
  if (last?.role === "system" && last.tone === "error") return "error";
  if (lastAssistantMessage(session)) return "completed";
  return "pending";
}

export function sessionToDocumentItem(
  session: ChatSession,
  processingId: string | null,
): DocumentListItem {
  const doc = session.document;
  const firstUser = session.messages.find((m) => m.role === "user");
  const assistant = lastAssistantMessage(session);
  const stats = assistant?.stats ?? null;
  const formatLabel = doc?.fileType ?? formatLabelFromMessage(firstUser, stats);
  const status = documentStatus(session, processingId);
  const dateTs = doc?.createdAt ?? session.createdAt;

  let compressionLabel: string | null = null;
  if (stats?.compressionPct != null) {
    compressionLabel = `Tóm tắt: ${Math.round(stats.compressionPct)}%`;
  } else if (status === "completed") {
    compressionLabel = "Đã hoàn tất";
  } else if (status === "error") {
    compressionLabel = "Lỗi";
  } else if (status === "processing") {
    compressionLabel = "Đang xử lý…";
  } else {
    compressionLabel = "Chờ xử lý";
  }

  const readMinutes =
    assistant?.content.trim() ? estimateReadMinutes(assistant.content) : null;

  return {
    sessionId: session.id,
    title: doc?.filename ?? session.title,
    dateLabel: formatDate(dateTs),
    formatLabel,
    status,
    compressionLabel,
    readMinutes,
    icon: iconForFormat(formatLabel),
  };
}

export function sessionsForProject(sessions: ChatSession[], projectId: string): ChatSession[] {
  return sessions
    .filter((s) => (s.projectId ?? DEFAULT_PROJECT_ID) === projectId)
    .filter((s) => sessionHasUserMessages(s.messages))
    .sort((a, b) => b.updatedAt - a.updatedAt);
}

export function splitSummaryBullets(summary: string): string[] {
  const lines = summary
    .split(/\n+/)
    .map((l) => l.replace(/^[\s•\-*]+/, "").trim())
    .filter(Boolean);
  if (lines.length >= 2) return lines.slice(0, 8);
  const sentences = summary
    .split(/(?<=[.!?…])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20);
  return sentences.slice(0, 6);
}
