import { formatDocumentMetaLine } from "../lib/documentRecord";
import type { ChatSession } from "../types/session";
import { MaterialIcon } from "./icons/MaterialIcon";

type Props = {
  open: boolean;
  sessions: ChatSession[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
};

export function HistoryDrawer({
  open,
  sessions,
  activeId,
  onSelect,
  onDelete,
  onClose,
}: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[55] lg:hidden" role="presentation">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <aside className="absolute bottom-0 left-0 top-16 flex w-full max-w-sm flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-outline-variant px-4 py-3">
          <h2 className="font-semibold">Lịch sử tóm tắt</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-2 hover:bg-surface-container">
            <MaterialIcon name="close" size="sm" />
          </button>
        </div>
        <ul className="flex-1 overflow-y-auto custom-scrollbar p-2">
          {sessions.length === 0 ? (
            <li className="px-4 py-8 text-center text-sm text-on-surface-variant">Chưa có lịch sử</li>
          ) : (
            sessions.map((s) => (
              <li key={s.id} className="mb-1">
                <button
                  type="button"
                  onClick={() => {
                    onSelect(s.id);
                    onClose();
                  }}
                  className={`flex w-full flex-col rounded-lg px-3 py-2.5 text-left ${
                    s.id === activeId ? "bg-primary-fixed" : "hover:bg-surface-container-low"
                  }`}
                >
                  <span className="truncate text-sm font-medium">{s.title}</span>
                  {s.document ? (
                    <span className="mt-0.5 text-xs text-on-surface-variant">
                      {formatDocumentMetaLine(s.document)}
                    </span>
                  ) : null}
                  {s.preview ? (
                    <span className="mt-0.5 line-clamp-2 text-xs text-on-surface-variant">
                      {s.preview}
                    </span>
                  ) : null}
                </button>
                <button
                  type="button"
                  className="ml-3 text-xs text-error"
                  onClick={() => onDelete(s.id)}
                >
                  Xóa
                </button>
              </li>
            ))
          )}
        </ul>
      </aside>
    </div>
  );
}
