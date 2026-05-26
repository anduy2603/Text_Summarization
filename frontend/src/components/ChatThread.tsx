import { useEffect, useRef } from "react";
import { formatStatsLine } from "../lib/chatDisplay";
import type { ChatMessage } from "../types/chat";
import { CopyButton } from "./CopyButton";
import { EmptyState } from "./EmptyState";

type Props = {
  messages: ChatMessage[];
  busy: boolean;
  isEmpty: boolean;
  onEmptyAction: (action: "text" | "link") => void;
};

export function ChatThread({ messages, busy, isEmpty, onEmptyAction }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  return (
    <div className="thread" role="log" aria-live="polite" aria-label="Hội thoại">
      <div className={`thread-inner ${isEmpty && !busy ? "thread-inner--empty" : ""}`}>
        {isEmpty && !busy ? <EmptyState onAction={onEmptyAction} /> : null}

        {!isEmpty
          ? messages.map((msg) => {
              if (msg.role === "system") {
                return (
                  <div key={msg.id} className="msg-row system">
                    <div className="msg-bubble system-bubble" role="alert">
                      {msg.content}
                    </div>
                  </div>
                );
              }
              if (msg.role === "user") {
                return (
                  <div key={msg.id} className="msg-row user">
                    <div className="msg-bubble user-bubble">
                      {msg.kind === "file" ? (
                        <span className="msg-file">{msg.fileName}</span>
                      ) : msg.kind === "url" ? (
                        <span className="msg-file">{msg.url}</span>
                      ) : (
                        <p className="msg-text">{msg.content}</p>
                      )}
                    </div>
                  </div>
                );
              }

              const statsLine = formatStatsLine(msg.stats);
              return (
                <div key={msg.id} className="msg-row assistant">
                  <div className="msg-bubble assistant-bubble">
                    <div className="msg-assistant-head">
                      <span className="msg-assistant-label">Bản tóm tắt</span>
                      <CopyButton text={msg.content} />
                    </div>
                    <p className="msg-text">{msg.content}</p>
                    {statsLine ? <p className="msg-meta">{statsLine}</p> : null}
                  </div>
                </div>
              );
            })
          : null}

        {busy ? (
          <div className="msg-row assistant">
            <div className="msg-bubble assistant-bubble typing" aria-busy="true">
              <span className="typing-label">Đang tóm tắt</span>
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        ) : null}

        <div ref={endRef} className="thread-anchor" />
      </div>
    </div>
  );
}
