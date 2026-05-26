import { useEffect, useRef } from "react";
import { formatStatsLine } from "../lib/chatDisplay";
import type { ChatMessage } from "../types/chat";

type Props = {
  messages: ChatMessage[];
  busy: boolean;
  activeSourceTitle: string | null;
};

export function ChatPanel({ messages, busy, activeSourceTitle }: Props) {
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  return (
    <section className="panel chat-panel" aria-label="Hội thoại">
      <div className="panel-head">
        <h2 className="panel-title">Chat</h2>
        {activeSourceTitle ? (
          <p className="panel-sub muted small">
            Nguồn đang chọn: <strong>{activeSourceTitle}</strong>
          </p>
        ) : (
          <p className="panel-sub muted small">Chọn một nguồn bên trái để tóm tắt.</p>
        )}
      </div>

      <div className="chat-thread" role="log" aria-live="polite">
        {messages.map((msg) => {
          if (msg.role === "system") {
            return (
              <div key={msg.id} className="chat-row system">
                <div className="bubble system-error">{msg.content}</div>
              </div>
            );
          }
          if (msg.role === "user") {
            return (
              <div key={msg.id} className="chat-row user">
                <div className="bubble user-bubble">
                  {msg.kind === "action" ? (
                    <p className="bubble-text">{msg.content}</p>
                  ) : msg.kind === "text" ? (
                    <p className="bubble-text">{msg.content}</p>
                  ) : msg.kind === "file" ? (
                    <p className="bubble-text">
                      <span className="bubble-icon" aria-hidden>
                        📄
                      </span>{" "}
                      {msg.fileName}
                    </p>
                  ) : (
                    <p className="bubble-text">
                      <span className="bubble-icon" aria-hidden>
                        🔗
                      </span>{" "}
                      {msg.url}
                    </p>
                  )}
                </div>
              </div>
            );
          }
          const statsLine = formatStatsLine(msg.stats);
          return (
            <div key={msg.id} className="chat-row assistant">
              <div className="bubble assistant-bubble">
                {msg.sourceTitle ? (
                  <p className="bubble-label muted small">Tóm tắt · {msg.sourceTitle}</p>
                ) : (
                  <p className="bubble-label muted small">Bản tóm tắt</p>
                )}
                <p className="bubble-text summary-text">{msg.content}</p>
                {statsLine ? <p className="bubble-meta muted small">{statsLine}</p> : null}
              </div>
            </div>
          );
        })}
        {busy ? (
          <div className="chat-row assistant">
            <div className="bubble assistant-bubble typing" aria-busy="true">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="sr-only">Đang tóm tắt…</span>
            </div>
          </div>
        ) : null}
        <div ref={chatEndRef} />
      </div>
    </section>
  );
}
