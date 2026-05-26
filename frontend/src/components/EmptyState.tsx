type Action = "text" | "link";

type Props = {
  onAction: (action: Action) => void;
};

const ACTIONS: { id: Action; label: string; hint: string }[] = [
  { id: "text", label: "Dán văn bản", hint: "Nội dung tiếng Việt" },
  { id: "link", label: "Dán link", hint: "Bài báo trực tuyến" },
];

export function EmptyState({ onAction }: Props) {
  return (
    <div className="empty">
      <h2 className="empty-title">Tóm tắt văn bản tiếng Việt</h2>
      <p className="empty-desc">
        Gõ hoặc dán link bên dưới. Đính kèm TXT, DOCX, PDF bằng biểu tượng 📎 trong ô chat.
      </p>
      <div className="empty-actions">
        {ACTIONS.map((a) => (
          <button key={a.id} type="button" className="empty-action" onClick={() => onAction(a.id)}>
            <span className="empty-action-label">{a.label}</span>
            <span className="empty-action-hint">{a.hint}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
