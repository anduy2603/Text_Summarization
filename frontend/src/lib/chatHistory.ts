import type { ChatMessage } from "../types/chat";
import type { SummaryDocumentRecord } from "../types/documentRecord";
import type { ChatSession } from "../types/session";
import { documentRecordFromSession } from "./documentRecord";
import { DEFAULT_PROJECT_ID } from "../constants";

const STORAGE_KEY_V1 = "vietsum_chat_history_v1";
const STORAGE_KEY = "vietsum_chat_history_v2";
const MAX_SESSIONS = 80;
/** Do not persist long pasted article text in chat messages. */
const MAX_TEXT_MESSAGE_CHARS = 120;
const MAX_URL_MESSAGE_CHARS = 200;
const MAX_SUMMARY_IN_MESSAGE = 8000;

function truncate(s: string, max: number): string {
  const t = s.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max)}…`;
}

export function newSessionId(): string {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function sanitizeMessageForStorage(msg: ChatMessage): ChatMessage {
  if (msg.role === "user" && msg.kind === "text") {
    const raw = msg.content.trim();
    if (raw.length <= MAX_TEXT_MESSAGE_CHARS) {
      return { ...msg, content: raw };
    }
    return {
      ...msg,
      content: `Văn bản (${raw.length.toLocaleString("vi-VN")} ký tự)`,
    };
  }
  if (msg.role === "user" && msg.kind === "url") {
    return { ...msg, url: truncate(msg.url, MAX_URL_MESSAGE_CHARS) };
  }
  if (msg.role === "assistant") {
    return {
      ...msg,
      content: truncate(msg.content, MAX_SUMMARY_IN_MESSAGE),
    };
  }
  return msg;
}

export function sanitizeDocumentForStorage(doc: SummaryDocumentRecord): SummaryDocumentRecord {
  return {
    ...doc,
    filename: doc.filename ? truncate(doc.filename, 200) : null,
    fileType: doc.fileType.slice(0, 16),
    summary: truncate(doc.summary, MAX_SUMMARY_IN_MESSAGE),
  };
}

export function sanitizeSessionForStorage(session: ChatSession): ChatSession {
  const doc = session.document ? sanitizeDocumentForStorage(session.document) : undefined;
  return {
    ...session,
    title: truncate(session.title, 80),
    preview: truncate(session.preview, 120),
    document: doc,
    messages: session.messages.map(sanitizeMessageForStorage),
  };
}

export function titleFromFirstUserMessage(msg: ChatMessage): string {
  if (msg.role !== "user") return "Cuộc hội thoại";
  if (msg.kind === "file") return truncate(msg.fileName, 42);
  if (msg.kind === "url") {
    try {
      const u = new URL(msg.url);
      return truncate(u.hostname + u.pathname.replace(/\/$/, ""), 42);
    } catch {
      return truncate(msg.url, 42);
    }
  }
  if (msg.kind === "text") return truncate(msg.content, 42);
  return truncate(msg.content, 42);
}

export function previewFromMessages(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role === "assistant" && m.content.trim()) {
      return truncate(m.content, 72);
    }
  }
  for (const m of messages) {
    if (m.role === "user") {
      if (m.kind === "file") return `Tệp: ${m.fileName}`;
      if (m.kind === "url") return truncate(m.url, 72);
      if (m.kind === "text") return truncate(m.content, 72);
    }
  }
  return "";
}

export function enrichSession(session: ChatSession): ChatSession {
  const document = session.document ?? documentRecordFromSession(session) ?? undefined;
  const firstUser = session.messages.find((m) => m.role === "user");
  const titleFromDoc =
    document?.filename && document.filename !== "Cuộc mới"
      ? truncate(document.filename, 42)
      : null;
  const title =
    titleFromDoc ??
    (session.title && session.title !== "Cuộc mới"
      ? session.title
      : firstUser
        ? titleFromFirstUserMessage(firstUser)
        : "Cuộc mới");
  const preview =
    (document?.summary ? truncate(document.summary, 72) : "") ||
    previewFromMessages(session.messages) ||
    session.preview;
  return { ...session, title, preview, document };
}

export function createEmptySession(projectId?: string): ChatSession {
  const now = Date.now();
  return {
    id: newSessionId(),
    title: "Cuộc mới",
    preview: "",
    projectId,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function parseSessions(raw: string): ChatSession[] {
  const parsed = JSON.parse(raw) as unknown;
  if (!Array.isArray(parsed)) return [];
  return parsed
    .filter((s): s is ChatSession => {
      return (
        typeof s === "object" &&
        s !== null &&
        typeof (s as ChatSession).id === "string" &&
        Array.isArray((s as ChatSession).messages)
      );
    })
    .map((s) => enrichSession(ensureSessionProject(s as ChatSession)))
    .sort((a, b) => b.updatedAt - a.updatedAt);
}

export function loadSessions(): ChatSession[] {
  try {
    const v2 = localStorage.getItem(STORAGE_KEY);
    if (v2) return parseSessions(v2);

    const v1 = localStorage.getItem(STORAGE_KEY_V1);
    if (v1) {
      const migrated = parseSessions(v1);
      saveSessions(migrated);
      return migrated;
    }
    return [];
  } catch {
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  try {
    const trimmed = sessions
      .map((s) => sanitizeSessionForStorage(enrichSession(s)))
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, MAX_SESSIONS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    /* quota or private mode */
  }
}

export function sessionHasUserMessages(messages: ChatMessage[]): boolean {
  return messages.some((m) => m.role === "user");
}

export function ensureSessionProject(session: ChatSession): ChatSession {
  if (session.projectId) return session;
  return { ...session, projectId: DEFAULT_PROJECT_ID };
}
