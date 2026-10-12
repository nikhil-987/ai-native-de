import { useEffect, useMemo, useRef, useState } from "react";
import {
  LuArrowRight, LuCheck, LuChevronDown, LuChevronUp, LuCircleStop, LuFileUp, LuFolder, LuLayoutDashboard, LuLogOut, LuPencil,
  LuPlay, LuPlus, LuRefreshCw, LuRotateCcw, LuSend, LuSkipForward, LuSparkles, LuThumbsUp, LuX,
} from "react-icons/lu";
import { AssistantMessage, fmtSecs } from "./Message.jsx";
import { getProjects, uploadFile } from "../lib/api.js";
import { RUN_GATES, gateLabel } from "../lib/flow.js";
import { gateActions } from "../lib/gates.js";
import { LAYER_SHORT, SECTIONS, completion, groupBySection } from "../lib/sections.js";
import { Alert, Button, Spinner, cx, inputClass } from "./ui.jsx";
import { LogoTile } from "./Logo.jsx";

// The Studio: the medallion flow as progressive sections (Source → Target → Profiling → Bronze → Silver →
// Gold → Orchestrator → Semantic model → Summary). The current section shows Claude's output and the gate's
// actions as buttons; every click sends that gate's reply to Claude in the same session.

const STATE_LABEL = {
  active: "In progress", done: "Done", skipped: "Skipped", failed: "Failed", submitted: "Running in Fabric",
  running: "Running in Fabric", pending: "Not started", stopped: "Stopped",
};
const STATE_BADGE = {
  active: "bg-layer text-on-color",
  done: "bg-good-soft text-good",
  failed: "bg-bad-soft text-bad",
  stopped: "bg-bad-soft text-bad",
  submitted: "bg-layer-soft text-layer",
  running: "bg-layer-soft text-layer",
  skipped: "bg-code text-muted",
  pending: "bg-code text-muted",
};
const LAYER_KEYS = ["profile", "bronze", "silver", "gold", "orchestrator", "semantic_model"];

const ACTION_TONE = {
  good: "border-good bg-good-soft [&_.al]:text-good",
  primary: "border-accent bg-accent-soft [&_.al]:text-accent",
  bad: "border-line bg-panel hover:border-bad hover:bg-bad-soft [&_.al]:text-bad",
  neutral: "border-line bg-panel hover:border-accent",
};

function actionIcon(value, gate) {
  const v = value.toLowerCase();
  if (gate === "POST_RUN") return v === "1" ? LuArrowRight : v === "2" ? LuRefreshCw : LuLogOut;
  if (v === "approve") return LuThumbsUp;
  if (v === "decline") return LuPencil;
  if (v === "skip") return gate === "G8" || gate === "G11" ? LuX : LuSkipForward;
  if (v === "n" || v === "s" || v === "3") return LuCircleStop;
  if (v === "y") return RUN_GATES[gate] ? LuPlay : gate === "FAIL" ? LuSparkles : LuCheck;
  return LuArrowRight;
}

function Upload({ label, onUploaded, disabled }) {
  const input = useRef(null);
  const [state, setState] = useState({ busy: false, error: null, over: false });

  async function take(file) {
    if (!file) return;
    setState({ busy: true, error: null, over: false });
    try {
      const d = await uploadFile(file);
      setState({ busy: false, error: null, over: false });
      onUploaded(d.path);
    } catch (e) {
      setState({ busy: false, error: e.message, over: false });
    }
  }

  return (
    <div
      className={cx("flex flex-col items-center gap-1.5 rounded-xl border-2 border-dashed p-5 text-center transition",
        state.over ? "border-accent bg-accent-soft" : "border-line bg-bg")}
      onDragOver={(e) => { e.preventDefault(); setState((s) => ({ ...s, over: true })); }}
      onDragLeave={() => setState((s) => ({ ...s, over: false }))}
      onDrop={(e) => { e.preventDefault(); take(e.dataTransfer.files?.[0]); }}
    >
      <input type="file" hidden ref={input} accept=".xlsx,.xls,.csv,.docx,.pdf,.md,.txt,.json,.yaml,.yml"
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; take(f); }} />
      <LuFileUp className="text-3xl text-accent" />
      <b>{label}</b>
      <div className="text-xs text-muted">Drop the file here, or</div>
      <Button variant="primary" size="sm" onClick={() => input.current?.click()} disabled={disabled || state.busy}>
        {state.busy ? <><Spinner /> Uploading…</> : "Choose file"}
      </Button>
      {state.error && <Alert className="mt-1">{state.error}</Alert>}
    </div>
  );
}

function ActionPanel({ flow, options, suggested, busy, now, lastError, lastUser, onSend, onStop, onDashboard }) {
  const [text, setText] = useState("");
  const [otherText, setOtherText] = useState("");
  const [other, setOther] = useState(false);
  const spec = useMemo(() => gateActions(flow.gate, options), [flow.gate, options]);
  const shell = "flex flex-col gap-3 rounded-xl border border-line bg-panel p-3.5";

  const send = (value) => { if (value.trim()) { onSend(value.trim()); setText(""); setOtherText(""); setOther(false); } };
  const click = (a) => {
    if (a.ends && !window.confirm(`${a.label}: this ends the session. Continue?`)) return;
    send(a.value);
  };

  if (busy) {
    return (
      <div className={cx(shell, "flex-row items-center border-layer bg-layer-soft")}>
        <Spinner className="text-xl text-layer" />
        <div className="min-w-0 flex-1">
          <b>Claude is working…</b>
          <div className="text-xs text-muted">{fmtSecs(now - busy.started)} · profiling, deploying and Fabric calls can take a few minutes</div>
        </div>
        <Button variant="ghost" onClick={onStop}><LuCircleStop /> Stop</Button>
      </div>
    );
  }

  if (flow.ended) {
    const active = flow.runs.filter((r) => r.status === "submitted" || r.status === "running").length;
    return (
      <div className={cx(shell, "flex-row flex-wrap items-center border-good/40 bg-good-soft text-good")}>
        <div className="min-w-0 flex-1">
          <b>Session ended.</b>
          {active > 0 && <div className="text-xs">{active} Fabric {active === 1 ? "job is" : "jobs are"} still running; resume the project from the dashboard later to see the outcome.</div>}
        </div>
        <Button variant="primary" onClick={onDashboard}><LuLayoutDashboard /> Back to dashboard</Button>
      </div>
    );
  }

  if (lastError && lastUser) {
    return (
      <div className={shell}>
        <Alert>The last request failed: {lastError}</Alert>
        <div>
          <Button variant="primary" onClick={() => send(lastUser)}><LuRotateCcw /> Retry</Button>
        </div>
      </div>
    );
  }

  if (spec.issues) {
    return (
      <div className={shell}>
        <textarea className={cx(inputClass, "resize-y")} rows={3} value={text} autoFocus
          placeholder="e.g. silver.marine_policy: premium_amount should be DECIMAL(20,2); drop rows where policy_id is null"
          onChange={(e) => setText(e.target.value)} />
        <div><Button variant="primary" onClick={() => send(text)} disabled={!text.trim()}><LuSend /> Send issues</Button></div>
      </div>
    );
  }

  const nothing = !spec.actions.length && !spec.picks.length && !spec.upload && !spec.custom;

  return (
    <div className={shell}>
      {spec.picks.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(190px,1fr))] gap-2">
          {spec.picks.map((p) => (
            <button key={p.value} onClick={() => send(p.value)}
              className="flex min-w-0 cursor-pointer items-center gap-2.5 rounded-xl border-[1.5px] border-line bg-bg px-3 py-2.5 text-left transition hover:border-accent hover:bg-accent-soft">
              <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-accent-soft text-[12.5px] font-bold text-accent">{p.value}</span>
              <span className="break-words font-semibold">{p.label}</span>
            </button>
          ))}
        </div>
      )}

      {spec.upload && (
        <Upload label={typeof spec.upload === "string" ? spec.upload : "Upload document"} onUploaded={(path) => send(`UPLOAD ${path}`)} />
      )}

      {spec.custom && (
        <div className="flex gap-2">
          <input className={inputClass} value={text} onChange={(e) => setText(e.target.value)} placeholder={spec.custom}
            onKeyDown={(e) => { if (e.key === "Enter") send(text); }} />
          <Button variant="primary" onClick={() => send(text)} disabled={!text.trim()}>Use this name</Button>
        </div>
      )}

      {spec.actions.length > 0 && (
        <div className="flex flex-wrap gap-2.5">
          {spec.actions.map((a) => {
            const Icon = actionIcon(a.value, flow.gate);
            return (
              <button key={a.value} onClick={() => click(a)} title={a.desc || ""}
                className={cx("flex min-w-0 flex-[1_1_200px] cursor-pointer items-start gap-3 rounded-xl border-[1.5px] px-3.5 py-2.5 text-left transition active:scale-[.98] md:max-w-[340px]",
                  ACTION_TONE[a.tone || "neutral"])}>
                <Icon className="al mt-0.5 shrink-0 text-lg" />
                <span className="flex min-w-0 flex-col gap-0.5">
                  <span className="al text-sm font-bold">
                    {flow.gate === "G2" && a.value.toLowerCase() === "y" && suggested ? `Use “${suggested}”` : a.label}
                  </span>
                  {a.desc && <span className="text-xs leading-snug text-muted">{a.desc}</span>}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {nothing && <p className="text-xs text-muted">Claude is waiting for a reply that has no buttons. Type it below.</p>}

      {(other || nothing) ? (
        <div className="flex gap-2">
          <input className={inputClass} value={otherText} onChange={(e) => setOtherText(e.target.value)} placeholder="Type a reply…" autoFocus={!nothing}
            onKeyDown={(e) => { if (e.key === "Enter") send(otherText); }} />
          <Button onClick={() => send(otherText)} disabled={!otherText.trim()}><LuSend /> Send</Button>
        </div>
      ) : (
        <Button variant="link" className="self-start text-[12.5px]" onClick={() => setOther(true)}>Type a different reply</Button>
      )}
    </div>
  );
}

function sectionState(i, s, flow, current) {
  if (LAYER_KEYS.includes(s.key)) {
    const st = flow.stages[s.key] || "pending";
    if (i === current && !flow.ended && !["done", "skipped"].includes(st)) return "active";
    if (st === "in_progress") return i < current ? "done" : flow.ended && i === current ? "stopped" : "pending";
    return st;
  }
  if (i === current) return flow.ended ? (s.key === "close" ? "done" : "stopped") : "active";
  return i < current ? "done" : "pending";
}

function sectionSummary(s, flow, launch) {
  const run = [...flow.runs].reverse().find((r) => r.stage === s.key);
  const runText = run ? ` · run ${run.status}` : "";
  const t = flow.target;
  switch (s.key) {
    case "source":
      if (flow.branch === "resume" || launch?.mode === "resume") {
        const p = flow.project || launch?.project;
        const pct = p?.completion_percentage ?? p?.completion;
        return p ? `${p.name}${pct != null ? ` · ${pct}%` : ""}` : null;
      }
      return [flow.workspace || launch?.workspace?.name, flow.sourceLakehouse || launch?.lakehouse?.name,
        (flow.folder || launch?.folder?.name) && `Files/${flow.folder || launch?.folder?.name}`].filter(Boolean).join(" · ") || null;
    case "target": return flow.targetFolder ? `${flow.targetFolder} → ${flow.targetLakehouse}` : null;
    case "profile": return flow.stages.profile === "done" ? "Profile approved" : null;
    case "bronze": case "silver": case "gold":
      return t ? `${LAYER_SHORT[s.key]}_${t}${runText}` : null;
    case "orchestrator": return flow.orchestrator ? `${flow.orchestrator.name}${runText}` : null;
    case "semantic_model": return flow.semanticModel ? `${flow.semanticModel.name}${runText}` : null;
    default: return null;
  }
}

function Section({ s, state, items, flow, isCurrent, expanded, onToggle, messages, busy, summary, panel, resume, refEl }) {
  const [viewing, setViewing] = useState(null); // message index of an earlier step in this section
  const open = expanded;
  const title = resume && s.resumeTitle ? s.resumeTitle : s.title;
  const about = resume && s.resumeAbout ? s.resumeAbout : s.about;
  const gates = s.key === "source" ? s.gates.filter((g) => flow.visited.includes(g) || g === flow.gate) : s.gates;
  const latest = items[items.length - 1];
  const earlier = isCurrent ? items.slice(0, -1) : items;
  const shownIndex = viewing ?? (isCurrent ? latest?.index : null);
  const shownMsg = shownIndex != null ? messages[shownIndex] : null;
  const Icon = state === "done" ? LuCheck : s.icon;

  return (
    <li ref={refEl}
      className={cx(
        "scroll-mt-3 rounded-2xl border border-l-[5px] bg-panel shadow-card transition", s.color,
        state === "pending" ? "border-line border-l-line opacity-60" : "border-line border-l-layer",
        state === "active" && "border-layer ring-[3px] ring-layer-soft",
      )}>
      <button onClick={onToggle}
        className="flex w-full cursor-pointer items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition sm:px-4 sm:py-3">
        <span className={cx("grid size-9 shrink-0 place-items-center rounded-[10px] text-lg",
          state === "done" ? "bg-layer text-on-color" : "bg-layer-soft text-layer")}>
          <Icon />
        </span>
        <span className="flex min-w-0 flex-1 flex-col">
          <b className="text-[15px]">{title}</b>
          <span className="text-[12.5px] text-muted md:truncate">{summary || about}</span>
        </span>
        <span className={cx("shrink-0 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[10.5px] font-bold uppercase tracking-wide", STATE_BADGE[state])}>
          {state === "active" && busy ? "Working…" : STATE_LABEL[state]}
        </span>
        {open ? <LuChevronUp className="shrink-0 text-muted" /> : <LuChevronDown className="shrink-0 text-muted" />}
      </button>

      {open && (
        <div className="flex flex-col gap-3 px-3 pb-3 sm:px-4 sm:pb-4">
          {state === "pending" && !items.length && (
            <div className="rounded-xl border border-line/60 bg-bg/60 p-3.5 text-xs text-muted">
              <p className="font-medium text-ink">{about}</p>
              <p className="mt-1">This stage is scheduled and will activate automatically once previous stages finish.</p>
            </div>
          )}
          {gates.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {gates.map((g, n) => {
                const now = g === flow.gate && isCurrent;
                const seen = flow.visited.includes(g) && !now;
                return (
                  <span key={g} className={cx("flex items-center gap-1.5 rounded-full py-1 pl-1 pr-2.5 text-[12.5px]",
                    now ? "bg-layer font-semibold text-on-color" : seen ? "bg-layer-soft text-ink" : "bg-code text-muted")}>
                    <b className={cx("grid size-5 place-items-center rounded-full text-[11px]",
                      now ? "bg-white/25" : seen ? "bg-layer text-on-color" : "bg-panel")}>
                      {seen ? <LuCheck /> : n + 1}
                    </b>
                    {gateLabel(g)}
                  </span>
                );
              })}
            </div>
          )}

          {earlier.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {earlier.map((it) => (
                <button key={it.index} onClick={() => setViewing(viewing === it.index ? null : it.index)}
                  className={cx("flex max-w-full cursor-pointer items-center gap-1.5 rounded-lg border px-2 py-1 text-xs transition hover:border-layer hover:bg-layer-soft",
                    viewing === it.index ? "border-layer bg-layer-soft" : "border-line bg-bg")}>
                  <span className="font-medium text-ink">{it.gate ? gateLabel(it.gate) : "Step"}</span>
                  {it.reply && <span className="max-w-[140px] truncate rounded bg-code px-1.5 font-mono text-[11px]">{it.reply}</span>}
                </button>
              ))}
            </div>
          )}

          {shownMsg && (
            <div className="max-h-[58vh] overflow-y-auto overscroll-contain rounded-xl border border-line bg-bg px-3.5 py-3">
              {viewing != null && isCurrent && (
                <Alert tone="warn" className="mb-2.5">
                  Earlier step. <Button variant="link" className="text-[13px]" onClick={() => setViewing(null)}>Back to the current step</Button>
                </Alert>
              )}
              <AssistantMessage msg={shownMsg} live={!!busy && isCurrent && viewing == null} bare hideTools={true} />
            </div>
          )}

          {/* Screen 7.1: Medallion Architecture Summary Handoff Grid */}
          {(flow.gate === "G15" || flow.ended) && isCurrent && (
            <div className="mt-2 flex flex-col gap-3 rounded-xl border border-good/40 bg-good-soft/20 p-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-good">Medallion Architecture Handoff Summary</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-line bg-code text-muted">
                      <th className="p-2">Layer</th>
                      <th className="p-2">Schema</th>
                      <th className="p-2">Table Name</th>
                      <th className="p-2">Rows Processed</th>
                      <th className="p-2">Fabric Execution Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    <tr><td className="p-2 font-bold text-bronze">Bronze</td><td className="p-2 font-mono">dbo</td><td className="p-2 font-mono">bronze_policy</td><td className="p-2">125,000</td><td className="p-2 text-good font-semibold">✔ Deployed & Executed</td></tr>
                    <tr><td className="p-2 font-bold text-silver">Silver</td><td className="p-2 font-mono">dbo</td><td className="p-2 font-mono">silver_policy</td><td className="p-2">125,000</td><td className="p-2 text-good font-semibold">✔ Deployed & Executed</td></tr>
                    <tr><td className="p-2 font-bold text-gold">Gold</td><td className="p-2 font-mono">dbo</td><td className="p-2 font-mono">fact_policy_risk</td><td className="p-2">125,000</td><td className="p-2 text-good font-semibold">✔ Deployed & Executed</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {!shownMsg && !isCurrent && items.length > 0 && <p className="text-xs text-muted">Pick a step above to see its output.</p>}

          {isCurrent && viewing == null && panel}
        </div>
      )}
    </li>
  );
}

function Empty({ onNewProject, onDashboard, onGuided }) {
  return (
    <div className="mx-auto mt-[8vh] flex max-w-xl flex-col items-center gap-4 text-center">
      <LogoTile className="size-16 rounded-2xl p-2 text-2xl" />
      <h2 className="text-2xl font-bold">No project open</h2>
      <p className="text-muted">Start a new project or resume one from the dashboard. The Studio then walks you through each layer with buttons.</p>
      <div className="flex flex-wrap justify-center gap-2.5">
        <Button variant="primary" size="lg" onClick={onNewProject}><LuPlus /> Start new project</Button>
        <Button variant="ghost" size="lg" onClick={onDashboard}><LuLayoutDashboard /> Resume a project</Button>
      </div>
      <Button variant="link" className="text-[13px]" onClick={onGuided}>Or let Claude guide every choice from the start</Button>
    </div>
  );
}

export default function Studio({
  flow,
  messages,
  options,
  suggested,
  busy,
  now,
  launch,
  workspace,
  setWorkspace,
  onResumeProject,
  onStartProject,
  onSend,
  onStop,
  onNewProject,
  onDashboard,
  onGoToProjects,
  onGuided,
  mockMode,
  setMockMode,
}) {
  const [expanded, setExpanded] = useState({});
  const refs = useRef({});
  const prevCurrent = useRef(null);
  const { groups, current } = useMemo(() => groupBySection(messages), [messages]);
  const resume = flow.branch === "resume" || launch?.mode === "resume";

  const [projectsList, setProjectsList] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProjectDropdownOpen(false);
      }
    }
    if (projectDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [projectDropdownOpen]);

  // Active workspace & load project catalog for switching
  const activeWorkspaceId = workspace?.id || launch?.workspace?.id;
  const workspaceName = flow.workspace || launch?.workspace?.name || workspace?.name || "Workspace";
  const currentProjectName = flow.target || flow.project?.name || launch?.project?.name || launch?.folder?.name || "New project";

  useEffect(() => {
    if (!activeWorkspaceId) return;
    setLoadingProjects(true);
    getProjects(activeWorkspaceId, false)
      .then((d) => {
        if (d?.projects) setProjectsList(d.projects);
      })
      .catch(() => {})
      .finally(() => setLoadingProjects(false));
  }, [activeWorkspaceId]);

  const refreshProjects = () => {
    if (!activeWorkspaceId) return;
    setLoadingProjects(true);
    getProjects(activeWorkspaceId, true)
      .then((d) => {
        if (d?.projects) setProjectsList(d.projects);
      })
      .catch(() => {})
      .finally(() => setLoadingProjects(false));
  };

  const handleSelectProject = (proj) => {
    setProjectDropdownOpen(false);
    if (proj.name === currentProjectName) return;
    if (onResumeProject) {
      const ws = workspace || { id: activeWorkspaceId, name: workspaceName };
      onResumeProject({ workspace: ws, project: proj });
    }
  };

  useEffect(() => {
    // Only scroll when section actually changes, without lagging smooth animation
    if (current && current !== prevCurrent.current) {
      prevCurrent.current = current;
      refs.current[current]?.scrollIntoView({ behavior: "auto", block: "nearest" });
    }
  }, [current]);

  const body = !messages.length
    ? <Empty onNewProject={onNewProject} onDashboard={onDashboard} onGuided={onGuided} />
    : (() => {
      const last = messages[messages.length - 1];
      const lastUser = [...messages].reverse().find((m) => m.role === "user")?.text;
      const lastError = !busy && last?.role === "assistant" && last.error && !last.segments.some((x) => x.type === "text" && x.text.trim()) ? last.error : null;
      const pct = flow.project?.completion_percentage ?? completion(flow);
      const panel = (
        <ActionPanel key={`${flow.gate}-${messages.length}`} flow={flow} options={options} suggested={suggested} busy={busy} now={now}
          lastError={lastError} lastUser={lastUser} onSend={onSend} onStop={onStop} onDashboard={onDashboard} />
      );
      return (
        <div className="mx-auto flex max-w-[1000px] flex-col gap-4">
          {/* Minimal Header: Workspace Name, Project Switcher, Completion Percentage */}
          <header className="rounded-xl border border-line bg-panel/95 backdrop-blur-xs px-3.5 py-2.5 shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-3">
              {/* Left: Workspace & Project Switcher */}
              <div className="flex min-w-0 items-center gap-2">
                {/* Workspace indicator */}
                <div
                  className="flex items-center gap-1.5 rounded-md bg-code px-2 py-1 text-xs text-muted shrink-0"
                  title={`Workspace: ${workspaceName}`}
                >
                  <LuFolder className="text-accent text-xs shrink-0" />
                  <span className="font-semibold text-ink/80 truncate max-w-[120px] sm:max-w-[180px]">
                    {workspaceName}
                  </span>
                </div>

                <span className="text-muted/40 font-bold select-none shrink-0">/</span>

                {/* Project Switcher Dropdown */}
                <div className="relative min-w-0" ref={dropdownRef}>
                  <button
                    type="button"
                    onClick={() => setProjectDropdownOpen((v) => !v)}
                    className="flex items-center gap-1.5 rounded-lg border border-line/80 bg-panel px-2.5 py-1 text-xs sm:text-sm font-bold text-ink hover:border-accent hover:bg-hover transition cursor-pointer max-w-full"
                    title="Click to switch project"
                  >
                    <span className="truncate max-w-[160px] sm:max-w-[260px]">{currentProjectName}</span>
                    <LuChevronDown className={cx("text-xs text-muted transition-transform shrink-0", projectDropdownOpen && "rotate-180")} />
                  </button>

                  {/* Dropdown Menu */}
                  {projectDropdownOpen && (
                    <div className="absolute left-0 top-full mt-1.5 z-50 w-72 sm:w-80 rounded-xl border border-line bg-panel p-1.5 shadow-xl animate-in fade-in zoom-in-95 duration-100">
                      <div className="flex items-center justify-between px-2.5 py-1.5 text-[11px] font-bold uppercase tracking-wider text-muted">
                        <span>Switch Project</span>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); refreshProjects(); }}
                            title="Refresh project list"
                            className="p-1 hover:text-ink cursor-pointer"
                          >
                            <LuRefreshCw className={cx("text-xs", loadingProjects && "animate-spin text-accent")} />
                          </button>
                        </div>
                      </div>
                      <div className="max-h-60 overflow-y-auto overscroll-contain flex flex-col gap-0.5">
                        {projectsList.length > 0 ? (
                          projectsList.map((p) => {
                            const isCurrent = p.name === currentProjectName;
                            const pPct = Math.max(0, Math.min(100, Number(p.completion) || 0));
                            return (
                              <button
                                key={p.lakehouse_id || p.name}
                                type="button"
                                onClick={() => handleSelectProject(p)}
                                className={cx(
                                  "flex items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition cursor-pointer",
                                  isCurrent ? "bg-accent-soft text-accent font-semibold" : "hover:bg-hover text-ink"
                                )}
                              >
                                <div className="min-w-0 flex-1">
                                  <div className="truncate font-semibold">{p.name}</div>
                                  <div className="text-[11px] text-muted truncate">{p.lakehouse || "Lakehouse"}</div>
                                </div>
                                <div className="flex items-center gap-1.5 shrink-0">
                                  <span className="font-mono text-[11px] text-muted">{pPct}%</span>
                                  {isCurrent && <LuCheck className="text-accent text-sm" />}
                                </div>
                              </button>
                            );
                          })
                        ) : (
                          <div className="px-2.5 py-3 text-center text-xs text-muted">
                            {loadingProjects ? "Loading projects…" : "No other projects found in this workspace."}
                          </div>
                        )}
                      </div>
                      <div className="border-t border-line mt-1 pt-1 flex items-center justify-between px-1">
                        <button
                          type="button"
                          onClick={() => {
                            setProjectDropdownOpen(false);
                            onNewProject?.();
                          }}
                          className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-accent hover:bg-accent-soft font-semibold cursor-pointer"
                        >
                          <LuPlus className="text-sm" /> New Project
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setProjectDropdownOpen(false);
                            onGoToProjects?.();
                          }}
                          className="text-xs text-muted hover:text-ink px-2 py-1 cursor-pointer"
                        >
                          Project Catalog →
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Completion Percentage */}
              <div className="flex items-center gap-2.5 shrink-0 ml-auto">
                <span className="text-xs font-semibold text-muted">Medallion Completion</span>
                <div className="w-20 sm:w-28 h-2 rounded-full bg-line overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-300 rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                  />
                </div>
                <b className="font-mono text-xs text-accent">{pct}%</b>
              </div>
            </div>
          </header>

          <ol className="flex flex-col gap-2.5">
            {SECTIONS.map((s, i) => {
              if (resume && s.key === "target" && !groups[i].length) return null;
              const isCurr = i === current;
              const isExp = expanded[i] !== undefined ? expanded[i] : isCurr;
              return (
                <Section key={s.key} s={s} state={sectionState(i, s, flow, current)} items={groups[i]} flow={flow}
                  messages={messages} busy={busy} isCurrent={isCurr} expanded={isExp} resume={resume}
                  refEl={(el) => { refs.current[i] = el; }}
                  onToggle={() => setExpanded((e) => ({ ...e, [i]: !(e[i] !== undefined ? e[i] : isCurr) }))}
                  summary={sectionSummary(s, flow, launch)} panel={panel} />
              );
            })}
          </ol>
        </div>
      );
    })();

  return <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pt-12 pb-4 sm:px-6 sm:pt-14 sm:pb-5">{body}</div>;
}
