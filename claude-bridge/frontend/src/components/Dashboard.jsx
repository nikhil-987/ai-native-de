import { useEffect, useMemo, useState } from "react";
import {
  LuActivity, LuArrowRight, LuBoxes, LuCheck, LuCircleCheck, LuDatabase, LuFolder, LuFolderOpen, LuHourglass, LuPlay,
  LuPlus, LuRefreshCw, LuRotateCcw, LuSearch, LuWand, LuX, LuPlug, LuShieldCheck,
} from "react-icons/lu";
import { getLakehouses, getProjects, getRawFolders, getWorkspaces } from "../lib/api.js";
import { gateLabel } from "../lib/flow.js";
import { LAYER_COLORS, relTime } from "../lib/sections.js";
import { LayerChips, ProgressBar } from "./Layers.jsx";
import { Alert, Button, Card, CardTitle, IconButton, Pill, Spinner, cx, inputClass } from "./ui.jsx";

const BUCKET = {
  completed: { label: "Completed", tone: "good", bar: "border-t-good" },
  in_progress: { label: "In progress", tone: "warn", bar: "border-t-gold" },
  failed: { label: "Failed", tone: "bad", bar: "border-t-bad" },
  unknown: { label: "Status unknown", tone: "neutral", bar: "border-t-line" },
};
const ACTIVITY_TONE = { COMPLETED: "good", FAILED: "bad", CANCELLED: "bad", RUNNING: "info", SUBMITTED: "info", SKIPPED: "neutral" };

const KPI = {
  total: { icon: LuBoxes, text: "text-accent", bar: "bg-accent", ring: "ring-accent-soft border-accent", hover: "hover:border-accent" },
  completed: { icon: LuCircleCheck, text: "text-good", bar: "bg-good", ring: "ring-good-soft border-good", hover: "hover:border-good" },
  progress: { icon: LuHourglass, text: "text-gold", bar: "bg-gold", ring: "ring-gold-soft border-gold", hover: "hover:border-gold" },
};

function Kpi({ kind, label, value, sub, active, onClick, loading }) {
  const k = KPI[kind];
  const Icon = k.icon;
  return (
    <button onClick={onClick}
      className={cx("relative flex cursor-pointer flex-col gap-0.5 overflow-hidden rounded-lg border bg-panel px-5 py-4 text-left shadow-card transition",
        active ? `ring-[3px] ${k.ring}` : `border-line ${k.hover}`)}>
      <span className={cx("absolute inset-y-0 left-0 w-[5px]", k.bar)} />
      <span className="flex items-center justify-between text-xs font-semibold uppercase tracking-[.07em] text-muted">
        {label}<Icon className={cx("text-xl", k.text)} />
      </span>
      <span className={cx("flex min-h-11 items-center text-[28px] font-extrabold leading-tight sm:text-[36px]", k.text)}>
        {loading ? <span className="skeleton inline-block h-9 w-14" /> : value ?? "—"}
      </span>
      <span className="text-[12.5px] text-muted">{sub || " "}</span>
    </button>
  );
}

export function ProjectCard({ p, onResume, disabled }) {
  const b = BUCKET[p.bucket] || BUCKET.unknown;
  const pct = Math.max(0, Math.min(100, Number(p.completion) || 0));
  const pathText = p.folder ? `${p.folder}/${p.lakehouse}` : p.lakehouse;
  const stageLabel = p.stages?.semantic_model === "done" || p.stages?.orchestrator === "done" ? "Orchestrated"
    : p.stages?.gold === "done" ? "Gold Layer"
    : p.stages?.silver === "done" ? "Silver Layer"
    : p.stages?.bronze === "done" ? "Bronze Layer"
    : "Not Started";

  return (
    <Card as="article" className={cx("flex flex-col gap-3 border-t-4 shadow-card hover:shadow-lg transition", b.bar)}>
      <header className="flex items-start justify-between gap-2.5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg shrink-0">{p.icon || "📂"}</span>
            <h3 className="truncate text-base font-bold text-ink" title={p.name}>{p.name}</h3>
          </div>
          <div className="mt-1 flex min-w-0 items-center gap-1.5 text-xs text-muted" title={`Path: ${pathText}`}>
            <LuFolder className="shrink-0 text-accent" />
            <span className="truncate font-mono text-[11.5px]">Path: {pathText}</span>
          </div>
        </div>
        <Pill tone={b.tone}>{b.label}</Pill>
      </header>

      <div className="flex items-center justify-between text-xs font-semibold">
        <span className="text-muted">Current Layer: <b className="text-ink">{stageLabel} ({pct}%)</b></span>
        <span className="text-muted">{relTime(p.updated_at)}</span>
      </div>

      <LayerChips stages={p.stages} />

      {p.readable ? (
        <>
          <ProgressBar pct={pct} />
          {(p.current_gate || p.next_action) && (
            <div className="flex flex-col gap-1 rounded-xl border border-line bg-bg p-2.5 text-[12.5px]">
              <div className="flex items-center gap-2">
                <span className="text-[10.5px] font-bold uppercase tracking-wider text-muted">Status:</span>
                <code className="shrink-0 rounded bg-accent-soft px-1.5 py-0.5 text-[11px] font-bold text-accent">
                  {p.bucket === "completed" ? "COMPLETED" : (p.current_gate ? gateLabel(p.current_gate) : "IN PROGRESS")}
                </code>
              </div>
              <div className="text-muted leading-tight">
                <span className="font-semibold text-ink">Action: </span>
                {p.next_action || (p.current_gate ? gateLabel(p.current_gate) : "Ready to proceed")}
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-muted">{p.error || "Status table found; delta log unavailable."}</p>
      )}

      <footer className="mt-auto flex justify-end pt-1">
        <Button variant={p.bucket === "completed" ? "ghost" : "primary"} size="sm" className="w-full sm:w-auto" onClick={() => onResume(p)} disabled={disabled}>
          {p.bucket === "completed" ? <><LuRotateCcw /> Reopen Project: {p.name}</> : <><LuPlay /> Resume Project: {p.name}</>}
        </Button>
      </footer>
    </Card>
  );
}

function Choice({ icon: Icon, title, sub, selected, onClick }) {
  return (
    <button onClick={onClick}
      className={cx("flex min-w-0 cursor-pointer items-center gap-3 rounded-xl border-[1.5px] p-3 text-left transition hover:border-accent hover:bg-accent-soft",
        selected ? "border-accent bg-accent-soft" : "border-line bg-bg")}>
      <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-source-soft text-lg text-source"><Icon /></span>
      <span className="flex min-w-0 flex-col">
        <b className="truncate">{title}</b>
        <span className="truncate text-xs text-muted">{sub}</span>
      </span>
    </button>
  );
}

export function Wizard({ workspace, onStart, onGuided, onClose, disabled }) {
  const [step, setStep] = useState(0);
  const [lakehouses, setLakehouses] = useState(null);
  const [folders, setFolders] = useState(null);
  const [lakehouse, setLakehouse] = useState(null);
  const [folder, setFolder] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    setLakehouses(null); setError(null);
    getLakehouses(workspace.id).then((d) => setLakehouses(d.lakehouses)).catch((e) => setError(e.message));
  }, [workspace.id]);

  function pickLakehouse(lh) {
    setLakehouse(lh); setFolder(null); setFolders(null); setError(null); setStep(1);
    getRawFolders(workspace.id, lh.id).then((d) => setFolders(d.folders)).catch((e) => setError(e.message));
  }

  const shown = (lakehouses || []).filter((l) => !filter || `${l.name} ${l.folder || ""}`.toLowerCase().includes(filter.toLowerCase()));
  const steps = ["Source lakehouse", "Raw data folder", "Confirm"];
  const grid = "grid max-h-[360px] grid-cols-[repeat(auto-fill,minmax(min(230px,100%),1fr))] gap-2.5 overflow-y-auto p-0.5";

  return (
    <Card className="flex flex-col gap-3.5 border-2 border-accent shadow-2xl">
      <div className="flex items-start justify-between gap-2.5">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[.08em] text-accent">Start new project · {workspace.name}</div>
          <h2 className="mt-0.5 text-lg font-bold">{steps[step]}</h2>
        </div>
        <IconButton onClick={onClose} aria-label="Close"><LuX /></IconButton>
      </div>

      <ol className="flex flex-wrap gap-1.5">
        {steps.map((s, i) => (
          <li key={s}>
            <button disabled={i > step} onClick={() => setStep(i)}
              className={cx("flex cursor-pointer items-center gap-2 rounded-full py-1 pl-1 pr-3 text-[13px] font-semibold transition disabled:cursor-default disabled:opacity-60",
                i < step ? "bg-good-soft text-good" : i === step ? "bg-accent text-white" : "bg-code text-muted")}>
              <b className={cx("grid size-[22px] place-items-center rounded-full text-[11.5px]", i === step ? "bg-white/25" : "bg-panel")}>
                {i < step ? <LuCheck /> : i + 1}
              </b>
              {s}
            </button>
          </li>
        ))}
      </ol>

      {error && <Alert>{error}</Alert>}

      {step === 0 && (
        <>
          <div className="relative">
            <LuSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input className={cx(inputClass, "pl-9")} placeholder="Filter lakehouses…" value={filter} onChange={(e) => setFilter(e.target.value)} />
          </div>
          {!lakehouses && !error && <div className="flex items-center gap-2 text-muted"><Spinner /> Loading lakehouses…</div>}
          <div className={grid}>
            {shown.map((lh) => (
              <Choice key={lh.id} icon={LuDatabase} title={lh.name} sub={lh.folder ? `Folder ${lh.folder}` : "Workspace root"}
                selected={lakehouse?.id === lh.id} onClick={() => pickLakehouse(lh)} />
            ))}
          </div>
          {lakehouses && !shown.length && <p className="text-muted">No lakehouses match.</p>}
        </>
      )}

      {step === 1 && (
        <>
          <p className="text-xs text-muted">Top-level folders under <code>Files/</code> in <b className="text-ink">{lakehouse?.name}</b>.</p>
          {!folders && !error && <div className="flex items-center gap-2 text-muted"><Spinner /> Reading Files/…</div>}
          <div className={grid}>
            {(folders || []).map((f) => (
              <Choice key={f.name} icon={LuFolderOpen} title={f.name} sub={`Files/${f.name}`}
                selected={folder?.name === f.name} onClick={() => { setFolder(f); setStep(2); }} />
            ))}
          </div>
          {folders && !folders.length && <p className="text-muted">No folders under Files/ in this lakehouse.</p>}
        </>
      )}

      {step === 2 && (
        <div className="flex flex-col gap-4">
          <div className="grid w-full grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-2.5">
            {[["Workspace", workspace.name], ["Source Lakehouse", lakehouse?.name], ["Raw Folder", `Files/${folder?.name}`]].map(([k, v]) => (
              <div key={k} className="flex min-w-0 flex-col rounded-xl border border-line bg-bg px-3 py-2.5">
                <span className="text-[11.5px] font-semibold uppercase tracking-wide text-muted">{k}</span>
                <b className="break-words text-sm text-ink">{v}</b>
              </div>
            ))}
          </div>

          {/* Target Directory Resolution Card (Screen 1.2) */}
          <div className="rounded-xl border border-line bg-bg p-4 flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-accent">Target Directory Resolution</h4>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="flex flex-col gap-1 text-xs font-semibold text-muted">
                Target Folder Name
                <input className={inputClass} value={folder?.name || "Automobile_Analytics"} readOnly />
              </label>
              <label className="flex flex-col gap-1 text-xs font-semibold text-muted">
                Target Lakehouse Item
                <input className={cx(inputClass, "bg-code")} value={`${folder?.name || "Automobile_Analytics"}_LH`} readOnly />
              </label>
            </div>
            <div className="rounded-lg bg-code p-3 font-mono text-xs text-muted">
              <div className="font-semibold text-ink">Directory Tree Structure:</div>
              <div>/{folder?.name || "Automobile_Analytics"}/</div>
              <div>├── {folder?.name || "Automobile_Analytics"}_LH (Target Lakehouse - Created on first run)</div>
              <div>├── notebooks/</div>
              <div>├── orchestrator/</div>
              <div>└── semantic model/</div>
            </div>
          </div>

          {/* Raw File Details Preview Table (Screen 1.3) */}
          <div className="rounded-xl border border-line bg-panel p-3.5">
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">Discovered Raw Files Preview</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-line bg-code text-muted">
                    <th className="p-2">Raw File</th>
                    <th className="p-2">Size</th>
                    <th className="p-2">Partition Path</th>
                    <th className="p-2">Target Table Mapping</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  <tr><td className="p-2 font-mono">policy_data.csv</td><td className="p-2">14.2 MB</td><td className="p-2 font-mono">Files/{folder?.name}</td><td className="p-2 font-mono text-accent">bronze.policy_data</td></tr>
                  <tr><td className="p-2 font-mono">customer_master.csv</td><td className="p-2">8.6 MB</td><td className="p-2 font-mono">Files/{folder?.name}</td><td className="p-2 font-mono text-accent">bronze.customer_master</td></tr>
                  <tr><td className="p-2 font-mono">claims_ledger.csv</td><td className="p-2">22.1 MB</td><td className="p-2 font-mono">Files/{folder?.name}</td><td className="p-2 font-mono text-accent">bronze.claims_ledger</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <Button variant="primary" size="lg" className="w-full sm:w-auto" disabled={disabled} onClick={() => onStart({ workspace, lakehouse, folder })}>
            <LuPlay /> Confirm & Create Target Folder
          </Button>
        </div>
      )}

      <div className="border-t border-dashed border-line pt-2.5">
        <Button variant="link" className="inline-flex items-center gap-1.5 text-[12.5px]" onClick={onGuided} disabled={disabled}>
          <LuWand /> Let Claude walk me through these choices instead
        </Button>
      </div>
    </Card>
  );
}

// 🏠 HOME PAGE View
export function HomePage({ health, workspace, setWorkspace, session, wizardOpen, setWizardOpen, onStart, onResume, onGuided, onOpenStudio, onConnections, onGoToProjects, mockMode, setMockMode }) {
  const [workspaces, setWorkspaces] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getWorkspaces().then((d) => {
      setWorkspaces(d.workspaces);
      if (!workspace && d.workspaces.length) {
        const pick = d.workspaces.find((w) => w.id === d.default) || d.workspaces[0];
        setWorkspace({ id: pick.id, name: pick.name });
      }
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!workspace) return;
    setLoading(true);
    getProjects(workspace.id, false)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [workspace?.id]);

  const c = data?.counts;
  const busy = !!session.busy;

  return (
    <div className="mx-auto flex max-w-[1240px] flex-col gap-6">
      {/* Welcome & Executive Banner */}
      <div className="relative flex flex-col justify-between overflow-hidden rounded-2xl border border-line bg-gradient-to-r from-[var(--brand-navy-900,#152337)] to-[var(--brand-navy-800,#1A2C47)] p-6 text-white shadow-xl sm:flex-row sm:items-center">
        <div className="max-w-[640px]">
          <div className="mb-1 text-xs font-bold uppercase tracking-widest text-[var(--brand-cyan-300,#00CCFF)]">
            ADROSONIC · AI Data Engineering Studio
          </div>
          <h1 className="mb-2 text-2xl font-extrabold sm:text-3xl">Driven by Core, Delivered by Innovation</h1>
          <p className="text-sm text-nav-text">
            Autonomous Medallion Architecture Engine for Microsoft Fabric. Build, deploy, and monitor Bronze, Silver, Gold Data Pipelines & Direct Lake Semantic Models.
          </p>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-2.5 sm:mt-0">
          <Button variant="primary" size="lg" onClick={() => setWizardOpen(true)} disabled={!workspace || busy}>
            <LuPlus /> Start New Project
          </Button>
          <Button variant="ghost" size="lg" className="border border-white/20 bg-white/10 text-white hover:bg-white/20" onClick={onGoToProjects} disabled={!workspace || busy}>
            <LuPlay /> Resume Existing Project
          </Button>
        </div>
      </div>

      {mockMode && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-accent/40 bg-accent-soft px-4 py-2.5 text-xs text-accent">
          <div className="flex items-center gap-2">
            <span className="font-bold uppercase tracking-wider">🧪 Mockups Mode Active:</span>
            <span>End-to-end interactive simulation is enabled. Click <b>Start New Project</b> to test every Medallion stage from Bronze to Gold & Semantic Model.</span>
          </div>
          {setMockMode && (
            <button onClick={() => setMockMode(false)} className="text-[11px] underline font-semibold cursor-pointer hover:text-ink">
              Switch to Live Engine
            </button>
          )}
        </div>
      )}

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
        <Kpi kind="total" label="Total Projects" value={c?.total} loading={loading} sub={data ? `${data.lakehouses_scanned} lakehouses scanned` : null} onClick={onGoToProjects} />
        <Kpi kind="completed" label="Completed" value={c?.completed} loading={loading} sub={c?.total ? `${Math.round((c.completed / c.total) * 100)}% complete` : null} onClick={onGoToProjects} />
        <Kpi kind="progress" label="In Progress" value={c?.in_progress} loading={loading} sub={c?.failed ? `${c.failed} failed` : "Active pipelines"} onClick={onGoToProjects} />
      </div>

      {wizardOpen && workspace && (
        <Wizard workspace={workspace} disabled={busy}
          onStart={(choice) => { setWizardOpen(false); onStart(choice); }}
          onGuided={() => { setWizardOpen(false); onGuided(workspace); }}
          onClose={() => setWizardOpen(false)} />
      )}

      {/* Recent Activity Grid */}
      <div className="w-full">
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <CardTitle icon={LuActivity}>Recent Workspace Activity</CardTitle>
            <Button variant="ghost" size="xs" onClick={onGoToProjects}>View All Projects <LuArrowRight /></Button>
          </div>
          {!data?.activity?.length ? <p className="text-xs text-muted">{loading ? "Loading activity…" : "No runs recorded yet."}</p> : (
            <ul className="grid gap-3">
              {data.activity.slice(0, 6).map((a, i) => (
                <li key={i} className={cx("flex min-w-0 items-start gap-2.5", LAYER_COLORS[String(a.stage || "").toLowerCase()] || "source")}>
                  <span className="mt-1.5 size-2.5 shrink-0 rounded-full bg-layer ring-[3px] ring-layer-soft" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <b className="truncate text-[13px] font-semibold" title={a.artifact || ""}>{a.artifact || a.stage}</b>
                      {a.status && <Pill tone={ACTIVITY_TONE[String(a.status).toUpperCase()] || "neutral"} className="!text-[9.5px]">{a.status}</Pill>}
                    </div>
                    <div className="text-xs text-muted">
                      {a.project} · {relTime(a.when)}
                      {a.duration_seconds != null && ` · ${a.duration_seconds}s`}
                      {a.records_processed != null && ` · ${Number(a.records_processed).toLocaleString()} rows`}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

// 📁 PROJECTS CATALOG View
export function ProjectsPage({ health, workspace, setWorkspace, session, wizardOpen, setWizardOpen, onStart, onResume, onGuided, onConnections }) {
  const [workspaces, setWorkspaces] = useState(null);
  const [wsError, setWsError] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    getWorkspaces()
      .then((d) => {
        setWorkspaces(d.workspaces);
        const keep = workspace && d.workspaces.find((w) => w.id === workspace.id);
        if (!keep) {
          const pick = d.workspaces.find((w) => w.id === d.default) || d.workspaces[0];
          if (pick) setWorkspace({ id: pick.id, name: pick.name });
        }
      })
      .catch((e) => setWsError(e.message));
  }, [health?.az_user]); // eslint-disable-line react-hooks/exhaustive-deps

  function load(refresh = false) {
    if (!workspace) return;
    setLoading(true); setError(null);
    getProjects(workspace.id, refresh)
      .then(setData)
      .catch((e) => { setError(e.message); setData(null); })
      .finally(() => setLoading(false));
  }
  useEffect(() => { setData(null); load(); }, [workspace?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const projects = useMemo(() => {
    const list = data?.projects || [];
    return list.filter((p) =>
      (filter === "all" || (filter === "in_progress" ? p.bucket === "in_progress" || p.bucket === "failed" : p.bucket === filter))
      && (!search || `${p.name} ${p.lakehouse} ${p.folder || ""}`.toLowerCase().includes(search.toLowerCase())));
  }, [data, filter, search]);

  const busy = !!session.busy;

  return (
    <div className="mx-auto flex max-w-[1240px] flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="mb-1 text-[22px] font-bold">Project Catalog</h2>
          <p className="max-w-[620px] text-muted">Medallion projects in workspace: every lakehouse holding a <code>project_status</code> table.</p>
        </div>
        <div className="flex w-full flex-wrap items-end gap-2 sm:w-auto">
          <label className="flex w-full flex-col gap-1 text-[11px] font-semibold uppercase tracking-wider text-muted sm:w-auto">
            Workspace
            <select value={workspace?.id || ""} disabled={!workspaces}
              className={cx(inputClass, "bg-panel font-medium normal-case tracking-normal sm:min-w-[220px]")}
              onChange={(e) => { const w = workspaces.find((x) => x.id === e.target.value); setWorkspace({ id: w.id, name: w.name }); }}>
              {!workspaces && <option value="">{wsError ? "Unavailable" : "Loading…"}</option>}
              {workspaces?.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
          </label>
          <Button variant="ghost" onClick={() => load(true)} disabled={loading || !workspace}>
            {loading ? <Spinner /> : <LuRefreshCw />} Refresh
          </Button>
          <Button variant="primary" onClick={() => setWizardOpen(true)} disabled={!workspace || busy}><LuPlus /> Start new project</Button>
        </div>
      </div>

      {wizardOpen && workspace && (
        <Wizard workspace={workspace} disabled={busy}
          onStart={(choice) => { setWizardOpen(false); onStart(choice); }}
          onGuided={() => { setWizardOpen(false); onGuided(workspace); }}
          onClose={() => setWizardOpen(false)} />
      )}

      <div className="mb-1 flex flex-wrap justify-between gap-2.5">
        <div className="flex gap-0.5 rounded-xl bg-code p-[3px]">
          {[["all", "All Projects"], ["in_progress", "In Progress"], ["completed", "Completed"]].map(([k, l]) => (
            <button key={k} onClick={() => setFilter(k)}
              className={cx("cursor-pointer rounded-lg px-3 py-1.5 text-[13px] font-semibold transition",
                filter === k ? "bg-panel text-ink shadow-card" : "text-muted hover:text-ink")}>{l}</button>
          ))}
        </div>
        <div className="relative w-full sm:w-64">
          <LuSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input className={cx(inputClass, "bg-panel pl-9")} placeholder="Search projects…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {loading && !data && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(min(300px,100%),1fr))] gap-3.5">
          {[0, 1, 2].map((i) => <div key={i} className="skeleton h-48 rounded-2xl" />)}
        </div>
      )}

      {data && projects.length === 0 && (
        <div className="rounded-2xl border-2 border-dashed border-line px-4 py-8 text-center text-muted">
          <p className="mb-3">{data.projects.length ? "No projects match this filter." : "No projects in this workspace yet."}</p>
          {!data.projects.length && <Button variant="primary" onClick={() => setWizardOpen(true)} disabled={busy}><LuPlus /> Start the first project</Button>}
        </div>
      )}

      <div className="grid grid-cols-[repeat(auto-fill,minmax(min(300px,100%),1fr))] gap-3.5">
        {projects.map((p) => (
          <ProjectCard key={p.lakehouse_id} p={p} disabled={busy} onResume={(proj) => onResume({ workspace, project: proj })} />
        ))}
      </div>
    </div>
  );
}

export default function Dashboard(props) {
  return <HomePage {...props} />;
}
