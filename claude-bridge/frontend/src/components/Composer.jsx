import { useEffect, useRef, useState } from "react";
import { LuPaperclip, LuSend, LuSquare } from "react-icons/lu";
import { uploadFile } from "../lib/api.js";
import { RUN_GATES } from "../lib/flow.js";
import { Alert, Button, IconButton, Spinner, cx } from "./ui.jsx";

const UPPER = (v) => v.toUpperCase();

// After a run is submitted in the background: [1/2/3]. The Fabric job keeps running on 1 and 3.
const POST_RUN_LABELS = {
  1: "1 · Next stage (job keeps running)",
  2: "2 · Check status",
  3: "3 · End chat (job keeps running)",
};

const CHIP = {
  base: "max-w-full cursor-pointer truncate rounded-full border px-3 py-1 text-[13px] font-medium transition",
  neutral: "border-line bg-panel text-ink hover:border-accent",
  good: "border-transparent bg-good-soft text-good hover:brightness-95",
  bad: "border-transparent bg-bad-soft text-bad hover:brightness-95",
  primary: "border-transparent bg-accent-soft text-accent hover:brightness-95",
};

function chipTone(v, gate) {
  const u = UPPER(v);
  if (gate === "POST_RUN") return u === "1" ? "good" : u === "3" ? "bad" : "neutral";
  if (u === "SKIP" && RUN_GATES[gate]) return "neutral";
  if (u === "APPROVE" || u === "Y") return "good";
  if (u === "DECLINE" || u === "N" || u === "S" || u === "SKIP") return "bad";
  if (u === "UPLOAD") return "primary";
  return "neutral";
}

function chipLabel(o, gate, suggested) {
  const u = UPPER(o.value);
  if (gate === "POST_RUN" && POST_RUN_LABELS[u]) return POST_RUN_LABELS[u];
  if (RUN_GATES[gate]) {
    if (u === "Y") return gate === "G14c" ? "Refresh now (background)" : "Run now (background)";
    if (u === "SKIP") return "Skip to next stage";
    if (u === "N") return "Don't run · stop (item stays deployed)";
  }
  if (u === "Y") {
    if (gate === "G0a") return "Yes, run az login";
    if (gate === "G2") return suggested ? `Yes, use ${suggested}` : "Yes, use suggested name";
    return "Yes";
  }
  if (u === "N") return "No";
  if (u === "S") return "Stop";
  if (u === "UPLOAD") return gate === "G11" ? "Upload STTM…" : gate === "G8" ? "Upload business rules…" : "Upload file…";
  return o.label ? `${o.value} · ${o.label}` : o.value;
}

export default function Composer({ flow, options, suggested, busy, onSend, onStop, onNewRun, hasMessages, compact = false }) {
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef(null);
  const textarea = useRef(null);
  const wantsUpload = options?.options.some((o) => UPPER(o.value) === "UPLOAD");
  const activeRuns = flow.runs.filter((r) => r.status === "submitted" || r.status === "running").length;

  useEffect(() => { if (!busy) textarea.current?.focus(); }, [busy]);

  function send(text = input) {
    if (!text.trim() || busy) return;
    onSend(text);
    setInput("");
    if (textarea.current) textarea.current.style.height = "auto";
  }

  async function onFile(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploading(true);
    try {
      const d = await uploadFile(file);
      if (wantsUpload) send(`UPLOAD ${d.path}`);
      else setInput((v) => `${v}${v ? " " : ""}${d.path}`);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  }

  const onChip = (v) => (UPPER(v) === "UPLOAD" ? fileInput.current?.click() : send(v));

  const placeholder =
    flow.gate === "ISSUES" ? "Describe the issues (table / column / cell)…"
      : options?.allowsCustom ? "Press y for suggested folder, or type custom name…"
      : wantsUpload ? "Attach file, or reply SKIP…"
      : hasMessages ? "Reply to step, or type START…"
      : "Type START to begin…";

  return (
    <footer className={cx("shrink-0 border-t border-line bg-panel", compact ? "p-2" : "px-3 pb-[max(16px,env(safe-area-inset-bottom))] pt-3 sm:px-6")}>
      <div className={cx(compact ? "w-full space-y-2" : "mx-auto max-w-[940px] space-y-2.5")}>
        {flow.ended && !busy && (
          <div className="flex flex-wrap items-center justify-between gap-2.5 rounded-lg bg-good-soft px-3 py-2 font-medium text-good">
            <span>
              Session stopped cleanly.
              {activeRuns > 0 && <> {activeRuns} Fabric {activeRuns === 1 ? "job is" : "jobs are"} still running in the background; resume the project later to see the outcome.</>}
            </span>
            <Button variant="primary" size="sm" onClick={onNewRun}>New project</Button>
          </div>
        )}
        {!busy && flow.gate === "ISSUES" && (
          <Alert tone="warn">Issues loop: describe what is wrong. Claude will fix it, show the diff and repeat the step.</Alert>
        )}
        {!busy && flow.gate === "POST_RUN" && (
          <Alert tone="warn">The run is in Fabric now. Moving on or ending the chat does not cancel it; its outcome is written to dbo.project_status.</Alert>
        )}
        {!busy && options?.options.length > 0 && (
          <div className="flex max-h-32 flex-wrap items-center gap-1.5 overflow-y-auto">
            <span className="mr-0.5 text-xs text-muted">Reply:</span>
            {options.options.map((o) => (
              <button key={o.value} className={cx(CHIP.base, CHIP[chipTone(o.value, flow.gate)])} onClick={() => onChip(o.value)}>
                {chipLabel(o, flow.gate, suggested)}
              </button>
            ))}
            {options.allowsCustom && <span className="text-xs text-muted">or type a custom folder name</span>}
          </div>
        )}
        <div className="flex items-end gap-2 rounded-xl border border-line bg-bg p-1.5 focus-within:border-accent">
          <IconButton title="Attach business rules / STTM document" onClick={() => fileInput.current?.click()} disabled={!!busy || uploading}>
            {uploading ? <Spinner /> : <LuPaperclip />}
          </IconButton>
          <input type="file" ref={fileInput} hidden onChange={onFile} accept=".xlsx,.xls,.csv,.docx,.pdf,.md,.txt,.json,.yaml,.yml" />
          <textarea
            ref={textarea}
            rows={1}
            value={input}
            placeholder={placeholder}
            className="max-h-[200px] min-w-0 flex-1 resize-none border-0 bg-transparent px-1 py-2 text-[15px] text-ink outline-none placeholder:text-muted/70"
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
            }}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          />
          {busy
            ? <Button variant="danger" onClick={onStop}><LuSquare /> Stop</Button>
            : <Button variant="primary" onClick={() => send()} disabled={!input.trim()}><LuSend /> Send</Button>}
        </div>
      </div>
    </footer>
  );
}
