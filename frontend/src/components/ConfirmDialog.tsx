type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  open,
  title = "Xác nhận",
  message,
  confirmLabel = "Xóa",
  cancelLabel = "Hủy",
  onConfirm,
  onCancel,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center bg-black/40 p-4"
      role="presentation"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-labelledby="confirm-title"
        aria-modal="true"
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="confirm-title" className="mb-2 text-base font-semibold text-on-surface">
          {title}
        </h3>
        <p className="mb-6 text-sm text-on-surface-variant">{message}</p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-xl border border-outline-variant py-2.5 text-sm font-medium text-on-surface hover:bg-surface-container"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 rounded-xl bg-error py-2.5 text-sm font-medium text-white hover:opacity-90"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
