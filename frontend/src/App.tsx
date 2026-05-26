import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchEngines, fetchHealth, type SummarizeOptions } from "./api";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { EngineCompareModal } from "./components/EngineCompareModal";
import { HistoryDrawer } from "./components/HistoryDrawer";
import { DocumentListPanel } from "./components/layout/DocumentListPanel";
import { MobileBottomNav, type MobileTab } from "./components/layout/MobileBottomNav";
import { ProjectSidebar } from "./components/layout/ProjectSidebar";
import { SummaryPreviewPanel } from "./components/layout/SummaryPreviewPanel";
import { TopNavBar } from "./components/layout/TopNavBar";
import { NewSummaryModal } from "./components/NewSummaryModal";
import { SettingsSheet } from "./components/SettingsSheet";
import { buildDocumentRecord } from "./lib/documentRecord";
import { LENGTH_PRESETS, type LengthPresetId } from "./constants";
import { newChatId } from "./lib/chatDisplay";
import {
  createEmptySession,
  enrichSession,
  loadSessions,
  previewFromMessages,
  saveSessions,
  sessionHasUserMessages,
  titleFromFirstUserMessage,
} from "./lib/chatHistory";
import { isHttpUrl } from "./lib/inputDetect";
import { toFriendlyError } from "./lib/friendlyError";
import { summarizeUserMessage } from "./lib/summarizeInput";
import {
  DEFAULT_PROJECT_ID,
  ensureSessionProject,
  loadProjects,
  sessionToDocumentItem,
  sessionsForProject,
} from "./lib/workspace";
import type { ChatMessage } from "./types/chat";
import type { ChatSession } from "./types/session";
import type { Project } from "./types/workspace";

function patchSession(
  sessions: ChatSession[],
  sessionId: string,
  patch: Partial<ChatSession> | ((s: ChatSession) => ChatSession),
): ChatSession[] {
  return sessions.map((s) => {
    if (s.id !== sessionId) return s;
    const next = typeof patch === "function" ? patch(s) : { ...s, ...patch };
    return enrichSession({ ...next, updatedAt: Date.now() });
  });
}

export default function App() {
  const [projects] = useState<Project[]>(() => loadProjects());
  const [activeProjectId, setActiveProjectId] = useState<string>(
    () => loadProjects()[0]?.id ?? DEFAULT_PROJECT_ID,
  );
  const [sessions, setSessions] = useState<ChatSession[]>(() =>
    loadSessions().map(ensureSessionProject),
  );
  const [activeId, setActiveId] = useState<string>("");
  const [processingId, setProcessingId] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [newModalOpen, setNewModalOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>("home");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const [lengthPreset, setLengthPreset] = useState<LengthPresetId>("medium");
  const [useAdvancedLength, setUseAdvancedLength] = useState(false);
  const [engineOptions, setEngineOptions] = useState<string[]>(["textrank"]);
  const [engine, setEngine] = useState("textrank");
  const [maxSentences, setMaxSentences] = useState(2);
  const [showRawMetadata, setShowRawMetadata] = useState(false);
  const [debugOverrides, setDebugOverrides] = useState(false);
  const [defaultEngine, setDefaultEngine] = useState("textrank");
  const [lastMetadata, setLastMetadata] = useState<Record<string, unknown> | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  const activeProject = projects.find((p) => p.id === activeProjectId) ?? projects[0];
  const projectSessions = useMemo(
    () => sessionsForProject(sessions, activeProjectId),
    [sessions, activeProjectId],
  );

  const documents = useMemo(
    () => projectSessions.map((s) => sessionToDocumentItem(s, processingId)),
    [projectSessions, processingId],
  );

  const selectedSession: ChatSession | null = (() => {
    const direct = sessions.find((s) => s.id === activeId);
    if (direct) return direct;
    const firstId = projectSessions[0]?.id;
    if (!firstId) return null;
    return sessions.find((s) => s.id === firstId) ?? null;
  })();

  const allWithContent = useMemo(
    () => sessions.filter((s) => sessionHasUserMessages(s.messages)),
    [sessions],
  );

  const docCountByProject = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of allWithContent) {
      const pid = s.projectId ?? DEFAULT_PROJECT_ID;
      counts[pid] = (counts[pid] ?? 0) + 1;
    }
    return counts;
  }, [allWithContent]);

  useEffect(() => {
    saveSessions(allWithContent);
  }, [allWithContent]);

  useEffect(() => {
    if (!activeId && projectSessions.length > 0) {
      setActiveId(projectSessions[0].id);
    }
  }, [activeId, projectSessions]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const { engines, defaultEngine, defaultMaxSentences } = await fetchEngines();
      if (cancelled) return;
      if (engines.length > 0) setEngineOptions(engines);
      const resolved =
        defaultEngine && engines.includes(defaultEngine) ? defaultEngine : (engines[0] ?? "textrank");
      setDefaultEngine(resolved);
      setEngine(resolved);
      if (defaultMaxSentences >= 1) {
        setMaxSentences(defaultMaxSentences);
        const match = LENGTH_PRESETS.find((p) => p.sentences === defaultMaxSentences);
        if (match) setLengthPreset(match.id);
      }
    })();
    void fetchHealth().then((r) => {
      if (!cancelled) setApiOk(r.ok);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const buildOptions = useCallback(
    (preset?: LengthPresetId): SummarizeOptions => {
      const id = preset ?? lengthPreset;
      const p = LENGTH_PRESETS.find((x) => x.id === id);
      const opts: SummarizeOptions = useAdvancedLength
        ? { max_sentences: maxSentences }
        : { max_sentences: p?.sentences ?? 2 };
      if (debugOverrides && engine.trim() && engine !== defaultEngine) {
        opts.engine = engine.trim();
      }
      if (debugOverrides && useAdvancedLength) {
        opts.max_sentences = maxSentences;
      }
      return opts;
    },
    [debugOverrides, defaultEngine, engine, lengthPreset, maxSentences, useAdvancedLength],
  );

  const runSummarize = useCallback(
    async (
      sessionId: string,
      input: { text: string; file: File | null },
      preset: LengthPresetId,
    ) => {
      const { text, file } = input;

      let userMsg: ChatMessage;
      if (file) {
        userMsg = { id: newChatId(), role: "user", kind: "file", fileName: file.name };
      } else if (isHttpUrl(text)) {
        userMsg = { id: newChatId(), role: "user", kind: "url", url: text };
      } else {
        const trimmed = text.trim();
        const display =
          trimmed.length > 120
            ? `Văn bản (${trimmed.length.toLocaleString("vi-VN")} ký tự)`
            : trimmed;
        userMsg = { id: newChatId(), role: "user", kind: "text", content: display };
      }

      setSessions((prev) =>
        patchSession(prev, sessionId, (s) => {
          const nextMessages = [...s.messages, userMsg];
          return {
            ...s,
            messages: nextMessages,
            title: titleFromFirstUserMessage(userMsg),
            preview: previewFromMessages(nextMessages),
            projectId: s.projectId ?? activeProjectId,
          };
        }),
      );

      setProcessingId(sessionId);
      setActiveId(sessionId);
      setNewModalOpen(false);

      try {
        const result = await summarizeUserMessage({ file, text }, buildOptions(preset));
        if (!result.ok) {
          setLastMetadata(null);
          setSessions((prev) =>
            patchSession(prev, sessionId, (s) => ({
              ...s,
              messages: [
                ...s.messages,
                {
                  id: newChatId(),
                  role: "system",
                  content: toFriendlyError(result.error),
                  tone: "error",
                },
              ],
            })),
          );
          return;
        }
        setLastMetadata(result.metadata);
        const summaryText = result.summary || "(Không tạo được bản tóm tắt.)";
        const document = buildDocumentRecord({
          input: { file, text },
          summary: summaryText,
          stats: result.stats,
          metadata: result.metadata,
          createdAt: Date.now(),
        });
        setSessions((prev) =>
          patchSession(prev, sessionId, (s) => {
            const nextMessages = [
              ...s.messages,
              {
                id: newChatId(),
                role: "assistant" as const,
                content: summaryText,
                stats: result.stats,
              },
            ];
            return enrichSession({
              ...s,
              messages: nextMessages,
              document,
              preview: document.summary.slice(0, 72) + (document.summary.length > 72 ? "…" : ""),
              title: document.filename ?? s.title,
            });
          }),
        );
      } finally {
        setProcessingId(null);
      }
    },
    [activeProjectId, buildOptions],
  );

  const onNewSummary = useCallback(
    (input: { text: string; file: File | null }, preset: LengthPresetId) => {
      const fresh = enrichSession({
        ...createEmptySession(activeProjectId),
        projectId: activeProjectId,
      });
      setSessions((prev) => [fresh, ...prev]);
      setActiveId(fresh.id);
      void runSummarize(fresh.id, input, preset);
    },
    [activeProjectId, runSummarize],
  );

  const onUploadFile = useCallback(
    (file: File) => {
      onNewSummary({ text: "", file }, "short");
    },
    [onNewSummary],
  );

  const onDeleteSession = useCallback(
    (id: string) => {
      const target = sessions.find((s) => s.id === id);
      if (!target) return;
      setPendingDeleteId(id);
    },
    [sessions],
  );

  const confirmDelete = useCallback(() => {
    if (!pendingDeleteId) return;
    const id = pendingDeleteId;
    setPendingDeleteId(null);
    const remaining = sessions.filter((s) => s.id !== id);
    setSessions(remaining);
    if (id === activeId) {
      const next = sessionsForProject(remaining, activeProjectId)[0];
      setActiveId(next?.id ?? "");
    }
  }, [pendingDeleteId, sessions, activeId, activeProjectId]);

  const showMobilePreview = mobileTab === "home" && Boolean(selectedSession);

  return (
    <div className="flex h-full flex-col overflow-hidden bg-background">
      <TopNavBar
        apiOk={apiOk}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSettings={() => setSettingsOpen(true)}
        onCompare={() => setCompareOpen(true)}
      />

      <main className="flex min-h-0 flex-1 pt-16 pb-20 lg:pb-0">
        {(mobileTab === "home" || mobileTab === "projects") && (
          <ProjectSidebar
            projects={projects}
            activeProjectId={activeProjectId}
            docCountByProject={docCountByProject}
            onSelectProject={(id) => {
              setActiveProjectId(id);
              const first = sessionsForProject(sessions, id)[0];
              setActiveId(first?.id ?? "");
              setMobileTab("home");
            }}
            onNewSummary={() => setNewModalOpen(true)}
            onOpenHistory={() => setHistoryOpen(true)}
          />
        )}

        {mobileTab === "home" && (
          <>
            <DocumentListPanel
              projectName={activeProject?.name ?? "Dự án"}
              documents={documents}
              selectedId={activeId || null}
              searchQuery={searchQuery}
              onSelect={setActiveId}
              onNewSummary={() => setNewModalOpen(true)}
              onUploadFile={onUploadFile}
              uploadBusy={processingId !== null}
            />
            <SummaryPreviewPanel
              session={selectedSession}
              processing={processingId === activeId}
            />
          </>
        )}

        {mobileTab === "history" && (
          <section className="flex flex-1 flex-col overflow-hidden bg-background p-4 lg:hidden">
            <h2 className="mb-4 text-lg font-semibold">Lịch sử tóm tắt</h2>
            <ul className="flex-1 space-y-2 overflow-y-auto custom-scrollbar">
              {allWithContent.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveProjectId(s.projectId ?? DEFAULT_PROJECT_ID);
                      setActiveId(s.id);
                      setMobileTab("home");
                    }}
                    className={`w-full rounded-xl border px-4 py-3 text-left ${
                      s.id === activeId ? "border-primary bg-primary-fixed" : "border-outline-variant bg-white"
                    }`}
                  >
                    <div className="truncate text-sm font-medium">{s.title}</div>
                    {s.preview ? (
                      <div className="mt-1 line-clamp-2 text-xs text-on-surface-variant">{s.preview}</div>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        {mobileTab === "projects" && (
          <section className="flex flex-1 flex-col gap-2 overflow-y-auto bg-surface-container-low p-4 lg:hidden">
            <p className="px-2 text-xs font-bold uppercase tracking-wider text-outline">Dự án của bạn</p>
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setActiveProjectId(p.id);
                  const first = sessionsForProject(sessions, p.id)[0];
                  setActiveId(first?.id ?? "");
                  setMobileTab("home");
                }}
                className={`flex items-center gap-3 rounded-lg px-3 py-3 text-left ${
                  p.id === activeProjectId ? "active-project" : "bg-white text-on-surface-variant"
                }`}
              >
                <span className="text-sm font-medium">{p.name}</span>
                <span className="ml-auto text-xs text-outline">{docCountByProject[p.id] ?? 0}</span>
              </button>
            ))}
            <button
              type="button"
              onClick={() => setNewModalOpen(true)}
              className="mt-4 rounded-xl bg-primary-container py-3 text-sm font-medium text-on-primary-container"
            >
              + Tải tệp tóm tắt
            </button>
          </section>
        )}

        {mobileTab === "profile" && (
          <section className="flex flex-1 flex-col items-center justify-center gap-4 p-8 lg:hidden">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-container text-xl font-bold text-on-primary-container">
              VS
            </div>
            <p className="text-sm text-on-surface-variant">VietSum · Đa định dạng · Tiếng Việt</p>
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="rounded-xl bg-primary px-6 py-2.5 text-sm font-medium text-white"
            >
              Cài đặt
            </button>
          </section>
        )}
      </main>

      {showMobilePreview ? (
        <div className="fixed inset-x-0 bottom-20 z-40 flex max-h-[42vh] flex-col overflow-hidden rounded-t-2xl border-t border-outline-variant bg-white shadow-2xl xl:hidden">
          <SummaryPreviewPanel
            session={selectedSession}
            processing={processingId === activeId}
            layout="sheet"
          />
        </div>
      ) : null}

      <MobileBottomNav active={mobileTab} onChange={setMobileTab} />

      <HistoryDrawer
        open={historyOpen}
        sessions={allWithContent}
        activeId={activeId}
        onSelect={(id) => {
          const s = sessions.find((x) => x.id === id);
          if (s?.projectId) setActiveProjectId(s.projectId);
          setActiveId(id);
        }}
        onDelete={onDeleteSession}
        onClose={() => setHistoryOpen(false)}
      />

      <EngineCompareModal
        open={compareOpen}
        engineOptions={engineOptions}
        onClose={() => setCompareOpen(false)}
      />

      <ConfirmDialog
        open={!!pendingDeleteId}
        title="Xóa tài liệu"
        message={`Xóa «${sessions.find((s) => s.id === pendingDeleteId)?.title ?? ""}» khỏi lịch sử? Hành động này không thể hoàn tác.`}
        onConfirm={confirmDelete}
        onCancel={() => setPendingDeleteId(null)}
      />

      <NewSummaryModal
        open={newModalOpen}
        busy={processingId !== null}
        onClose={() => setNewModalOpen(false)}
        onSubmit={onNewSummary}
      />

      <SettingsSheet
        open={settingsOpen}
        engineOptions={engineOptions}
        engine={engine}
        maxSentences={maxSentences}
        showRawMetadata={showRawMetadata}
        lastMetadata={lastMetadata}
        onClose={() => setSettingsOpen(false)}
        onEngine={(v) => {
          setDebugOverrides(true);
          setEngine(v);
        }}
        onMaxSentences={(n) => {
          setDebugOverrides(true);
          setUseAdvancedLength(true);
          setMaxSentences(n);
        }}
        onShowRawMetadata={setShowRawMetadata}
      />
    </div>
  );
}
