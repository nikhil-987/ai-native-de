import { useMemo } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { LuCircleCheck, LuCircleX, LuTerminal } from "react-icons/lu";
import { stripUiState } from "../lib/flow.js";
import { Alert, Spinner, cx } from "./ui.jsx";
import { LogoTile } from "./Logo.jsx";

export const fmtSecs = (ms) =>
  ms < 60000 ? `${Math.round(ms / 1000)}s` : `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;

function Markdown({ text }) {
  const __html = useMemo(
    () => DOMPurify.sanitize(marked.parse(stripUiState(text || ""), { gfm: true, breaks: true })),
    [text],
  );
  return <div className="md" dangerouslySetInnerHTML={{ __html }} />;
}

function ToolGroup({ tools, live }) {
  const running = tools.find((t) => t.status === "running");
  const failed = tools.filter((t) => t.status === "error").length;
  return (
    <details className="group my-2 rounded-lg border border-line bg-code text-[12.5px]" open={live && !!running}>
      <summary className="flex cursor-pointer items-center gap-2 overflow-hidden px-3 py-1.5 text-muted [&::-webkit-details-marker]:hidden">
        {running ? (
          <>
            <Spinner className="text-accent" />
            <span className="shrink-0 font-semibold">{running.name}</span>
            <code className="truncate">{running.detail.slice(0, 100)}</code>
          </>
        ) : (
          <>
            <LuTerminal className="shrink-0" />
            {tools.length} step{tools.length > 1 ? "s" : ""} run · auto-approved
            {failed > 0 && <span className="text-bad">· {failed} failed</span>}
          </>
        )}
      </summary>
      <ul className="max-h-60 space-y-1 overflow-y-auto px-3 pb-2 pt-1">
        {tools.map((t) => (
          <li key={t.id} className="flex items-start gap-2">
            {t.status === "ok" ? <LuCircleCheck className="mt-0.5 shrink-0 text-good" />
              : t.status === "error" ? <LuCircleX className="mt-0.5 shrink-0 text-bad" />
              : <Spinner className="mt-0.5 text-accent" />}
            <div className="min-w-0">
              <b className="font-semibold">{t.name}</b> <code className="break-all text-muted">{t.detail}</code>
              {t.error && <div className="mt-0.5 break-words text-xs text-bad">{t.error}</div>}
            </div>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function UserMessage({ text }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-accent px-3.5 py-2 text-white sm:max-w-[70%]">{text}</div>
    </div>
  );
}

// `bare` drops the avatar and bubble (used inside Studio sections).
// `hideTools` hides internal processing steps/tools (so they appear only in the Conversation panel).
export function AssistantMessage({ msg, live, bare, hideTools = false }) {
  // Merge consecutive tool calls into one collapsible group unless hidden.
  const parts = [];
  for (const s of msg.segments) {
    if (s.type === "tool") {
      if (!hideTools) {
        const prev = parts[parts.length - 1];
        if (prev?.type === "tools") prev.tools.push(s);
        else parts.push({ type: "tools", tools: [s] });
      }
    } else if (stripUiState(s.text).trim()) parts.push(s);
  }
  const body = (
    <>
      {parts.map((p, i) =>
        p.type === "tools" ? <ToolGroup key={i} tools={p.tools} live={live} /> : <Markdown key={i} text={p.text} />)}
      {live && !parts.length && (
        <div className="flex items-center gap-2 text-xs text-muted py-1">
          <Spinner className="text-accent" />
          <span>{hideTools ? "Processing in background (see Conversation for live steps)…" : "Working…"}</span>
        </div>
      )}
      {msg.error && <Alert className="mt-2.5">{msg.error}</Alert>}
      {msg.meta?.duration_ms && (
        <div className="mt-2 text-[11.5px] text-muted">{fmtSecs(msg.meta.duration_ms)}{msg.meta.model ? ` · ${msg.meta.model}` : ""}</div>
      )}
    </>
  );
  if (bare) return <div className="min-w-0">{body}</div>;
  return (
    <div className="flex gap-2.5 sm:gap-3">
      <LogoTile className="size-7 sm:size-8" />
      <div className={cx("min-w-0 flex-1 rounded-2xl rounded-tl-sm border border-line bg-panel px-3 py-2.5 shadow-card sm:px-4 sm:py-3")}>{body}</div>
    </div>
  );
}
