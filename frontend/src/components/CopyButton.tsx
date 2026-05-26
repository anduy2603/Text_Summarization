import { useCallback, useState } from "react";
import { MaterialIcon } from "./icons/MaterialIcon";

type Props = {
  text: string;
  label?: string;
  variant?: "button" | "icon";
};

export function CopyButton({ text, label = "Sao chép", variant = "button" }: Props) {
  const [copied, setCopied] = useState(false);

  const onCopy = useCallback(async () => {
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        setCopied(true);
        window.setTimeout(() => setCopied(false), 2000);
      } finally {
        document.body.removeChild(ta);
      }
    }
  }, [text]);

  if (variant === "icon") {
    return (
      <button
        type="button"
        onClick={() => void onCopy()}
        className="rounded-lg p-2 text-on-surface-variant transition-colors hover:bg-surface-container"
        aria-label={copied ? "Đã sao chép" : label}
        title={copied ? "Đã sao chép" : label}
      >
        <MaterialIcon name={copied ? "check" : "content_copy"} size="sm" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => void onCopy()}
      className="inline-flex items-center gap-1.5 rounded-lg border border-outline-variant px-3 py-1.5 text-xs font-medium text-on-surface-variant hover:bg-surface-container"
    >
      <MaterialIcon name={copied ? "check" : "content_copy"} size="sm" />
      {copied ? "Đã sao chép" : label}
    </button>
  );
}
