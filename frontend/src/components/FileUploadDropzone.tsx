import { useCallback, useRef, useState } from "react";
import { MaterialIcon } from "./icons/MaterialIcon";

const ACCEPT =
  ".txt,.docx,.pdf,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

type Props = {
  disabled?: boolean;
  onFile: (file: File) => void;
  onTextFallback?: () => void;
  compact?: boolean;
};

export function FileUploadDropzone({
  disabled,
  onFile,
  onTextFallback,
  compact = false,
}: Props) {
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const pick = useCallback(
    (f: File | undefined) => {
      if (!f || disabled) return;
      onFile(f);
    },
    [disabled, onFile],
  );

  const py = compact ? "py-8" : "py-14";

  return (
    <div className="flex flex-col items-center">
      <div
        role="button"
        tabIndex={0}
        aria-label="Tải tệp TXT, DOCX hoặc PDF"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") fileRef.current?.click();
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragOver(false);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          pick(e.dataTransfer.files?.[0]);
        }}
        onClick={() => !disabled && fileRef.current?.click()}
        className={`flex w-full max-w-md cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 ${py} transition-colors ${
          disabled
            ? "cursor-not-allowed opacity-50"
            : dragOver
              ? "border-primary bg-primary-container/30"
              : "border-outline-variant bg-white hover:border-primary/50"
        }`}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-container text-primary">
          <MaterialIcon name="upload_file" size="lg" />
        </div>
        <p className="text-center text-sm font-semibold text-on-surface">
          Tải tệp để tóm tắt
        </p>
        <p className="text-center text-xs text-on-surface-variant">
          Kéo thả hoặc chọn · .txt, .docx, .pdf
        </p>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept={ACCEPT}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          pick(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {onTextFallback ? (
        <button
          type="button"
          disabled={disabled}
          onClick={onTextFallback}
          className="mt-4 text-xs font-medium text-primary hover:underline"
        >
          Hoặc nhập văn bản / link
        </button>
      ) : null}
    </div>
  );
}
