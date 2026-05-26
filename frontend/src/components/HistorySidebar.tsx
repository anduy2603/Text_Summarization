import type { ChatSession } from "../types/session";

type Props = {
  sessions: ChatSession[];
  activeId: string;
  sidebarOpen: boolean;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onCloseMobile: () => void;
};

function formatWhen(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const sameDay =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();
  if (sameDay) {
    return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

export function HistorySidebar({
  sessions,
  activeId,
  sidebarOpen,
  onSelect,
  onNewChat,
  onDelete,
  onCloseMobile,
}: Props) {
  const withContent = sessions.filter((s) => s.messages.some((m) => m.role === "user"));

  return (
    <>
      <div
        className={`history-backdrop ${sidebarOpen ? "visible" : ""}`}
        aria-hidden={!sidebarOpen}
        onClick={onCloseMobile}
      />
      <aside className={`history ${sidebarOpen ? "open" : ""}`} aria-label="Lịch sử hội thoại">
        <div className="history-head">
          <span className="history-title">Lịch sử</span>
          <button type="button" className="history-new" onClick={onNewChat}>
            + Mới
          </button>
        </div>

        <ul className="history-list">
          {withContent.length === 0 ? (
            <li className="history-empty">Chưa có cuộc hội thoại. Gửi nội dung để lưu lịch sử.</li>
          ) : (
            withContent.map((s) => (
              <li key={s.id}>
                <div className={`history-item ${s.id === activeId ? "active" : ""}`}>
                  <button
                    type="button"
                    className="history-item-main"
                    onClick={() => {
                      onSelect(s.id);
                      onCloseMobile();
                    }}
                  >
                    <span className="history-item-title">{s.title}</span>
                    {s.preview ? (
                      <span className="history-item-preview">{s.preview}</span>
                    ) : (
                      <span className="history-item-preview muted">Chưa có tóm tắt</span>
                    )}
                    <span className="history-item-time">{formatWhen(s.updatedAt)}</span>
                  </button>
                  <button
                    type="button"
                    className="history-item-delete"
                    aria-label={`Xóa ${s.title}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(s.id);
                    }}
                  >
                    ×
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
      </aside>
    </>
  );
}
