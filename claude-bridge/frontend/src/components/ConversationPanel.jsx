import { useEffect, useRef } from "react";
import {
  LuBot, LuMessageSquare, LuPanelRightClose, LuRotateCcw, LuTerminal, LuTrash2, LuX,
} from "react-icons/lu";
import { AssistantMessage, UserMessage } from "./Message.jsx";
import Composer from "./Composer.jsx";
import { IconButton } from "./ui.jsx";

export default function ConversationPanel({
  messages,
  flow,
  options,
  suggested,
  busy,
  onSend,
  onStop,
  onClear,
  onClose,
  health,
  isOpen = true,
}) {
  const scroller = useRef(null);
  const isNearBottomRef = useRef(true);

  const handleScroll = (e) => {
    const el = e.currentTarget;
    if (!el) return;
    // Considered near bottom if within 80px of the bottom edge
    isNearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  useEffect(() => {
    const el = scroller.current;
    if (el && isNearBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, busy]);

  if (!isOpen) return null;

  return (
    <div className="flex h-full w-[360px] shrink-0 flex-col border-l border-line bg-panel transition-all sm:w-[400px] xl:w-[440px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line px-3.5 py-2.5 bg-bg/50">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex size-7 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <LuMessageSquare className="text-sm" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="truncate text-xs font-bold text-ink">Conversation</h3>
              <span className="rounded bg-code px-1.5 py-0.2 text-[10px] font-mono text-muted">Execution Trace</span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-muted">
              <span className="size-1.5 rounded-full bg-good" />
              <span>Internal steps & tools visible</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && onClear && (
            <IconButton onClick={onClear} aria-label="Clear Conversation" title="Clear conversation history">
              <LuRotateCcw className="text-xs" />
            </IconButton>
          )}
          {onClose && (
            <IconButton onClick={onClose} aria-label="Hide Conversation Panel" title="Collapse conversation panel">
              <LuPanelRightClose className="text-sm" />
            </IconButton>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div ref={scroller} onScroll={handleScroll} className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3.5 space-y-3.5">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center text-muted">
            <div className="mb-3 flex size-11 items-center justify-center rounded-2xl bg-accent-soft text-accent">
              <LuTerminal className="text-lg" />
            </div>
            <h4 className="mb-1 text-xs font-bold text-ink">Claude Execution & Chat Feed</h4>
            <p className="max-w-[240px] text-[11.5px] text-muted">
              Internal processing steps, auto-approved tool runs, bash, Livy statements, and conversation replies appear here in real time.
            </p>
          </div>
        ) : (
          messages.map((m, i) =>
            m.role === "user" ? (
              <UserMessage key={i} text={m.text} />
            ) : (
              <AssistantMessage
                key={i}
                msg={m}
                live={!!busy && i === messages.length - 1}
                hideTools={false}
              />
            )
          )
        )}
      </div>

      {/* Composer at Bottom */}
      <div className="shrink-0 border-t border-line bg-bg/40 p-2">
        <Composer
          flow={flow}
          options={options}
          suggested={suggested}
          busy={busy}
          onSend={onSend}
          onStop={onStop}
          hasMessages={messages.length > 0}
          compact
        />
      </div>
    </div>
  );
}
