import { useState } from "react";
import {
  LuActivity, LuArrowLeft, LuBoxes, LuHouse, LuLayoutDashboard, LuMessageSquare, LuPlug, LuRefreshCw, LuWand, LuX,
} from "react-icons/lu";
import { getRunStatus } from "../lib/api.js";
import { LAYER_COLORS } from "../lib/sections.js";
import { Button, IconButton, Pill, STATUS_TONE, Spinner, StatusDot, cx } from "./ui.jsx";
import { Logo } from "./Logo.jsx";

function Section({ title, children }) {
  return (
    <section className="rounded-xl bg-nav-card p-3">
      <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-[.08em] text-nav-muted">{title}</h4>
      {children}
    </section>
  );
}

function RunList({ runs }) {
  const [checked, setChecked] = useState({});

  async function check(run) {
    setChecked((c) => ({ ...c, [run.run_id]: { ...c[run.run_id], loading: true, error: null } }));
    try {
      const d = await getRunStatus(run);
      setChecked((c) => ({ ...c, [run.run_id]: { loading: false, status: d.status, error: d.error } }));
    } catch (e) {
      setChecked((c) => ({ ...c, [run.run_id]: { ...c[run.run_id], loading: false, error: e.message } }));
    }
  }

  return (
    <ul className="grid gap-1.5">
      {runs.map((r) => {
        const c = checked[r.run_id] || {};
        const status = c.status || r.status;
        const canCheck = r.workspace_id && r.item_id && r.run_id;
        return (
          <li key={r.run_id || r.item} className={cx("min-w-0 rounded-lg border border-nav-line bg-nav px-2.5 py-1.5 text-[12.5px]", LAYER_COLORS[r.stage])}>
            <div className="flex items-center justify-between gap-2">
              <b className="flex min-w-0 items-center gap-1.5 truncate font-medium text-nav-strong" title={r.item}>
                <span className="size-2 shrink-0 rounded-full bg-layer" />{r.item || r.stage}
              </b>
              {status && <Pill tone={STATUS_TONE[status] || "neutral"} className="!text-[9.5px]">{status}</Pill>}
            </div>
            <div className="mt-0.5 flex justify-between gap-2 font-mono text-[11.5px] text-nav-muted">
              <span title={r.run_id}>Run {r.run_id ? r.run_id.slice(0, 8) : "—"}</span>
              {canCheck && (
                <button className="inline-flex cursor-pointer items-center gap-1 font-sans text-accent hover:underline" onClick={() => !c.loading && check(r)}>
                  {c.loading ? <Spinner /> : <LuRefreshCw />} {c.loading ? "checking" : "check status"}
                </button>
              )}
            </div>
            {c.error && <div className="mt-1 break-words text-xs text-bad">{c.error}</div>}
          </li>
        );
      })}
    </ul>
  );
}

export default function Sidebar({ flow, health, busy, tab, setTab, onNewRun, onConnections, sessionId, onClear, hasMessages, onClose, onToggleCollapse }) {
  const mcp = health?.mcp;
  const env = health?.env;

  const navItems = [
    { key: "home", label: "Home", icon: LuHouse },
    { key: "projects", label: "Projects", icon: LuBoxes },
    { key: "studio", label: "Studio", icon: LuWand, live: hasMessages && !flow.ended },
    { key: "monitoring", label: "Monitoring", icon: LuActivity },
  ];

  return (
    <aside className="sidenav flex h-full min-h-0 flex-col gap-3.5 overflow-y-auto overscroll-contain border-r border-nav-line bg-nav px-4 py-[18px] text-nav-ink">
      <div className="flex items-center gap-2 pb-2 border-b border-nav-line/40">
        <div className="min-w-0 flex-1">
          <Logo variant="sidenav" className="h-7 w-auto max-w-[210px]" />
          <div className="mt-1.5 text-[12px] font-medium leading-snug text-nav-muted">AI Data Engineering Studio</div>
        </div>
        <IconButton className="text-nav-ink md:hidden" onClick={onClose} aria-label="Close menu"><LuX /></IconButton>
        {onToggleCollapse && (
          <IconButton
            className="hidden text-nav-ink md:grid hover:bg-nav-card hover:text-white"
            onClick={onToggleCollapse}
            aria-label="Collapse sidebar"
            title="Collapse sidebar"
          >
            <LuArrowLeft />
          </IconButton>
        )}
      </div>

      <nav className="grid gap-1">
        {navItems.map((n) => {
          const Icon = n.icon;
          const active = tab === n.key;
          return (
            <button key={n.key} onClick={() => { setTab(n.key); if (onClose) onClose(); }}
              className={cx(
                "flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-[13.5px] font-medium transition",
                active ? "bg-[var(--brand-navy-800,#1A2C47)] text-white shadow-sm" : "text-nav-ink hover:bg-nav-card hover:text-white"
              )}>
              <div className="flex items-center gap-2.5">
                <Icon className={cx("text-base", active ? "text-[var(--brand-cyan-300,#00CCFF)]" : "text-nav-muted")} />
                <span>{n.label}</span>
              </div>
            </button>
          );
        })}
      </nav>

      <Section title="System & Configuration">
        {health?.demo_mode && (
          <div className="mb-2 flex items-center justify-between rounded-lg border border-accent/40 bg-nav px-2.5 py-1 text-[11px] font-semibold text-accent">
            <span>Demo Mode Active</span>
          </div>
        )}
        <div className="grid gap-1 text-[13px]">
          <div className="flex min-w-0 items-center justify-between gap-1.5">
            <div className="flex min-w-0 items-center gap-2 truncate">
              <StatusDot state={health?.claude_auth?.authenticated ? "on" : health?.claude ? "idle" : "off"} />
              <span className="truncate">
                Claude Code ·{" "}
                <span className="text-nav-muted">
                  {health?.claude_auth?.authenticated ? (health.claude_auth.user_name || health.claude_auth.user || "Signed in") : "Not signed in"}
                </span>
              </span>
            </div>
            {!health?.claude_auth?.authenticated && (
              <button
                onClick={onConnections}
                className="shrink-0 text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                title="Sign in to Claude in Connections"
              >
                Sign in
              </button>
            )}
          </div>
          <div className="flex min-w-0 items-center justify-between gap-1.5">
            <div className="flex min-w-0 items-center gap-2 truncate">
              <StatusDot state={health?.az_user ? "on" : "off"} />
              <span className="truncate">{health?.az_user ? <>Azure CLI · <span className="text-nav-muted">{health.az_user}</span></> : "Azure CLI not signed in"}</span>
            </div>
            {!health?.az_user && (
              <button
                onClick={onConnections}
                className="shrink-0 text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                title="Sign in to Azure in Connections"
              >
                Sign in
              </button>
            )}
          </div>
          <div className="flex items-center gap-2" title={mcp?.servers?.map((s) => `${s.name}: ${s.status}`).join("\n") || ""}>
            <StatusDot state={mcp ? (mcp.fabric ? "on" : "off") : "wait"} />
            {!mcp ? "Fabric MCP server · checking…" : mcp.fabric ? "Fabric MCP server" : "Fabric MCP server not found"}
          </div>
          <div className="flex min-w-0 items-center gap-2">
            <StatusDot state={env?.exists ? "on" : "idle"} />
            <span className="truncate">{env?.exists ? <>.env · <span className="text-nav-muted">{env.workspace || "workspace chosen at start"}</span></> : ".env not set (optional)"}</span>
          </div>
        </div>
        <Button variant="nav" size="sm" className="mt-2.5 w-full" onClick={onConnections}>
          <LuPlug /> Connections Settings
        </Button>
      </Section>

      {flow.runs.length > 0 && <Section title="Active Monitors"><RunList runs={flow.runs} /></Section>}

      {flow.created.length > 0 && (
        <Section title="Created in Fabric">
          <ul className="list-disc space-y-0.5 pl-4 text-[12.5px]">{flow.created.map((c) => <li key={c} className="break-all">{c}</li>)}</ul>
        </Section>
      )}
    </aside>
  );
}
