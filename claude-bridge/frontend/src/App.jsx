import { useEffect, useMemo, useRef, useState } from "react";
import {
  LuArrowLeft, LuArrowRight, LuCircleStop, LuMessageSquare, LuMoon, LuNetwork, LuPlug, LuSun, LuWorkflow, LuX,
} from "react-icons/lu";
import Sidebar from "./components/Sidebar.jsx";
import Composer from "./components/Composer.jsx";
import Studio from "./components/Studio.jsx";
import ConversationPanel from "./components/ConversationPanel.jsx";
import { HomePage, ProjectsPage } from "./components/Dashboard.jsx";
import Connections from "./components/Connections.jsx";
import { OrchestratorPanel, SemanticModelPanel } from "./components/ArtifactPanels.jsx";
import { MonitoringPanel } from "./components/MonitoringPanel.jsx";
import { NotificationCenter, NotificationToast } from "./components/NotificationCenter.jsx";
import { AssistantMessage, UserMessage, fmtSecs } from "./components/Message.jsx";
import { Button, IconButton, Spinner, cx } from "./components/ui.jsx";
import { LogoTile } from "./components/Logo.jsx";
import { assistantText, useClaudeSession } from "./hooks/useClaudeSession.js";
import { useNotifications } from "./hooks/useNotifications.js";
import { useTheme } from "./hooks/useTheme.js";
import { getHealth, getMcp, getWorkspaces } from "./lib/api.js";
import { STAGES, deriveFlow, gateLabel, parseOptions, stageOf, stripUiState, suggestedTarget } from "./lib/flow.js";
import { loadPref, savePref } from "./lib/storage.js";

const MOBILE = "(max-width: 767px)";

function launchPrompt(l) {
  const lines = [
    "START",
    "",
    "Configuration selections:",
    `- Workspace: "${l.workspace.name}" (id ${l.workspace.id})`,
  ];
  if (l.mode === "new") {
    lines.push(
      "- Action: Start a new project",
      `- Source Lakehouse: "${l.lakehouse.name}" (id ${l.lakehouse.id})` +
        `${l.lakehouse.folder ? `, in folder "${l.lakehouse.folder}"` : ", at the workspace root"}; Raw Data Folder: "${l.folder.name}"`,
      "",
      "Apply these choices and proceed with target directory resolution and data profiling.",
    );
  } else if (l.mode === "resume") {
    const p = l.project;
    lines.push(
      "- Action: Resume an existing project",
      `- Project to resume: "${p.name}", lakehouse "${p.lakehouse}" (id ${p.lakehouse_id})` +
        `${p.folder ? ` in folder "${p.folder}"` : " at the workspace root"}`,
      "",
      "Apply these choices, read that project's dbo.project_status, show the Project Stage Summary, and continue at its current pending stage.",
    );
  } else {
    lines.push("", "Begin project setup and select action.");
  }
  return lines.join("\n");
}

export default function App() {
  const { messages, sessionId, model, setModel, busy, send, stop, clear, mockMode, setMockMode } = useClaudeSession();
  const { theme, toggleTheme } = useTheme();
  const [health, setHealth] = useState(null);
  const [tab, setTab] = useState("home");
  const [workspace, setWorkspaceState] = useState(() => loadPref("workspace"));
  const [launch, setLaunchState] = useState(() => loadPref("launch"));
  const [wizardOpen, setWizardOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);          // phone drawer
  const [navCollapsed, setNavCollapsed] = useState(false); // desktop sidebar
  const [connectionsOpen, setConnectionsOpen] = useState(false); // Connections drawer from Sidenav
  const [chatPanelOpen, setChatPanelOpen] = useState(false); // Right-hand conversation panel (collapsed by default)
  const [now, setNow] = useState(Date.now());

  const setWorkspace = (w) => { setWorkspaceState(w); savePref("workspace", w); };
  const setLaunch = (l) => { setLaunchState(l); savePref("launch", l); };

  useEffect(() => { savePref("hasSession", messages.length > 0); }, [messages.length]);
  useEffect(() => {
    getHealth().then((h) => setHealth((prev) => ({ ...h, mcp: prev?.mcp }))).catch(() => setHealth({ claude: false }));
    getMcp()
      .then((m) => setHealth((h) => ({ ...h, mcp: m })))
      .catch((e) => setHealth((h) => ({ ...h, mcp: { servers: [], fabric: false, error: e.message } })));
    getWorkspaces()
      .then((d) => {
        if (!workspace && d?.workspaces?.length) {
          const pick = d.workspaces.find((w) => w.id === d.default) || d.workspaces[0];
          if (pick) setWorkspace({ id: pick.id, name: pick.name });
        }
      })
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [busy]);

  useEffect(() => {
    const mq = window.matchMedia(MOBILE);
    const onChange = () => { if (!mq.matches) setNavOpen(false); };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const toggleNav = () => {
    if (window.matchMedia(MOBILE).matches) setNavOpen((v) => !v);
    else setNavCollapsed((v) => !v);
  };

  const assistantTexts = useMemo(
    () => messages.filter((m) => m.role === "assistant").map(assistantText),
    [messages],
  );
  const flow = useMemo(() => deriveFlow(assistantTexts), [assistantTexts]);
  const lastText = assistantTexts[assistantTexts.length - 1] || "";
  const options = !busy && flow.gate !== "ISSUES" && lastText ? parseOptions(stripUiState(lastText)) : null;
  const suggested = flow.gate === "G2" ? suggestedTarget(stripUiState(lastText)) : null;

  const {
    notifications,
    unreadCount,
    activeToast,
    dismissToast,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
  } = useNotifications(flow);

  const go = (t) => {
    if (t === "chat") {
      setTab("studio");
      setChatPanelOpen(true);
    } else if (t === "runs") {
      setTab("monitoring");
    } else {
      setTab(t);
    }
    setNavOpen(false);
  };
  const confirmReplace = () =>
    !messages.length || flow.ended || window.confirm("Leave the current project session? Its conversation will be cleared (Fabric jobs keep running).");

  function begin(l) {
    if (busy || !confirmReplace()) return;
    setLaunch(l);
    go("studio");
    send(launchPrompt(l), { fresh: true });
  }
  const startProject = ({ workspace: w, lakehouse, folder }) => begin({ mode: "new", workspace: w, lakehouse, folder });
  const resumeProject = ({ workspace: w, project }) => begin({ mode: "resume", workspace: w, project });
  const guidedStart = (w) => {
    if (busy || !confirmReplace()) return;
    setLaunch(w ? { mode: "guided", workspace: w } : null);
    go("studio");
    send(w ? launchPrompt({ mode: "guided", workspace: w }) : "START", { fresh: true });
  };
  const newProject = () => { setWizardOpen(true); go("projects"); };

  const scrollArea = "min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pt-12 pb-4 sm:px-6 sm:pt-14 sm:pb-5";

  return (
    <div className={cx("grid h-dvh overflow-hidden transition-[grid-template-columns] duration-200",
      navCollapsed ? "md:grid-cols-[0_minmax(0,1fr)]" : "md:grid-cols-[290px_minmax(0,1fr)]")}>
      <div className={cx(
        "fixed inset-y-0 left-0 z-30 w-[min(320px,86vw)] transition-transform duration-200 md:static md:z-auto md:w-auto md:min-w-0 md:translate-x-0 md:overflow-hidden",
        navOpen ? "translate-x-0 shadow-2xl" : "-translate-x-[105%]",
        navCollapsed && "md:invisible",
      )}>
        <Sidebar
          flow={flow}
          health={health}
          busy={busy}
          tab={tab}
          setTab={go}
          onNewRun={newProject}
          onConnections={() => setConnectionsOpen(true)}
          sessionId={sessionId}
          onClear={() => { if (confirmReplace()) { clear(); setLaunch(null); } }}
          hasMessages={messages.length > 0}
          onClose={() => setNavOpen(false)}
          onToggleCollapse={toggleNav}
        />
      </div>
      <div onClick={() => setNavOpen(false)}
        className={cx("fixed inset-0 z-20 bg-black/40 transition-opacity md:hidden", navOpen ? "opacity-100" : "pointer-events-none opacity-0")} />

      {/* Sidenav Connections Overlay Modal */}
      {connectionsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs">
          <div className="relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-line bg-panel shadow-2xl">
            <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
              <h3 className="text-base font-bold">Connections Settings</h3>
              <IconButton onClick={() => setConnectionsOpen(false)} aria-label="Close Connections"><LuX /></IconButton>
            </div>
            <div className="overflow-y-auto p-5">
              <Connections health={health} setHealth={setHealth} model={model} setModel={setModel} busy={busy} />
            </div>
          </div>
        </div>
      )}

      <main className="relative flex h-full min-h-0 min-w-0 flex-1 overflow-hidden">
        {/* Main Content Area & Conversation Panel */}
        <div className="flex h-full min-h-0 min-w-0 flex-1 overflow-hidden">
          {/* Active Tab View */}
          <div className="relative flex-1 min-w-0 h-full overflow-hidden flex flex-col">
            {/* Floating Top-Left Button to Expand Sidebar (shown only when sidebar is collapsed) */}
            {navCollapsed && (
              <div className="absolute top-3 left-3 z-30">
                <IconButton
                  onClick={toggleNav}
                  aria-label="Expand sidebar"
                  title="Expand sidebar"
                  className="border border-line bg-panel/95 text-ink shadow-sm hover:border-accent backdrop-blur-xs"
                >
                  <LuArrowRight />
                </IconButton>
              </div>
            )}

            {/* Floating Top-Right Action Controls (Zero top header bar clutter) */}
            <div className="absolute top-3 right-4 z-30 flex items-center gap-2">
              {busy && (
                <div className="flex items-center gap-2 whitespace-nowrap rounded-lg border border-line bg-panel/95 px-2.5 py-1 text-xs text-muted backdrop-blur-xs shadow-xs">
                  <Spinner className="text-accent" /> {fmtSecs(now - busy.started)}
                  <Button variant="ghost" size="xs" onClick={stop}><LuCircleStop /> Stop</Button>
                </div>
              )}
              <NotificationCenter
                notifications={notifications}
                unreadCount={unreadCount}
                onMarkAsRead={markAsRead}
                onMarkAllAsRead={markAllAsRead}
                onRemove={removeNotification}
                onClearAll={clearAll}
                onNavigateToMonitoring={() => go("monitoring")}
              />
              <button
                onClick={() => setChatPanelOpen(!chatPanelOpen)}
                className={cx(
                  "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold cursor-pointer transition shadow-xs backdrop-blur-xs",
                  chatPanelOpen
                    ? "border-accent/60 bg-accent-soft text-accent"
                    : "border-line bg-panel/95 text-muted hover:text-ink hover:border-accent"
                )}
                title={chatPanelOpen ? "Collapse Conversation Panel" : "Show Conversation Panel on Right"}
              >
                <LuMessageSquare className="text-xs" />
                <span>Conversation</span>
                {messages.length > 0 && (
                  <span className="rounded-full bg-accent/20 px-1.5 py-0.2 text-[10px] font-mono">{messages.length}</span>
                )}
              </button>
              <button
                onClick={() => setMockMode(!mockMode)}
                className={cx(
                  "hidden sm:inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold cursor-pointer transition shadow-xs backdrop-blur-xs",
                  mockMode
                    ? "border-accent/60 bg-accent-soft text-accent"
                    : "border-line bg-panel/95 text-muted hover:text-ink hover:border-accent"
                )}
                title={mockMode ? "Mockups Simulation Mode Active (Click to switch to Live Engine)" : "Live Cloud Engine Active (Click to switch to Mockup Simulation)"}
              >
                <span>{mockMode ? "🧪 Mockups Mode" : "⚡ Live Engine"}</span>
              </button>
              <IconButton
                className="border border-line bg-panel/95 shadow-xs backdrop-blur-xs"
                onClick={toggleTheme}
                aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              >
                {theme === "dark" ? <LuSun /> : <LuMoon />}
              </IconButton>
            </div>

            {/* Active Tab Pages */}
            {tab === "home" && (
              <div className={scrollArea}>
                <HomePage health={health} workspace={workspace} setWorkspace={setWorkspace}
                  session={{ messages, flow, busy }} wizardOpen={wizardOpen} setWizardOpen={setWizardOpen}
                  onStart={startProject} onResume={resumeProject} onGuided={guidedStart}
                  onOpenStudio={() => go("studio")} onConnections={() => setConnectionsOpen(true)}
                  onGoToProjects={() => go("projects")} mockMode={mockMode} setMockMode={setMockMode} />
              </div>
            )}
            {tab === "projects" && (
              <div className={scrollArea}>
                <ProjectsPage health={health} workspace={workspace} setWorkspace={setWorkspace}
                  session={{ messages, flow, busy }} wizardOpen={wizardOpen} setWizardOpen={setWizardOpen}
                  onStart={startProject} onResume={resumeProject} onGuided={guidedStart}
                  onConnections={() => setConnectionsOpen(true)} />
              </div>
            )}
            {(tab === "studio" || tab === "chat") && (
              <Studio
                flow={flow}
                messages={messages}
                options={options}
                suggested={suggested}
                launch={launch}
                busy={busy}
                now={now}
                workspace={workspace}
                setWorkspace={setWorkspace}
                onResumeProject={resumeProject}
                onStartProject={startProject}
                onNewProject={newProject}
                onDashboard={() => go("home")}
                onGoToProjects={() => go("projects")}
                onGuided={() => guidedStart(workspace)}
                mockMode={mockMode}
                setMockMode={setMockMode}
                onSend={send}
                onStop={stop}
              />
            )}
            {(tab === "monitoring" || tab === "runs") && (
              <div className={scrollArea}>
                <MonitoringPanel flow={flow} onOpenStudio={() => go("studio")} />
              </div>
            )}
            {tab === "orchestrator" && <div className={scrollArea}><OrchestratorPanel flow={flow} onGoToChat={() => go("studio")} /></div>}
            {tab === "semantic" && <div className={scrollArea}><SemanticModelPanel flow={flow} onGoToChat={() => go("studio")} /></div>}
          </div>

          {/* Right-Hand Side: Conversation & Claude Execution Trace (Opens across ALL views including Projects!) */}
          <ConversationPanel
            messages={messages}
            flow={flow}
            options={options}
            suggested={suggested}
            busy={busy}
            onSend={send}
            onStop={stop}
            onClear={() => { if (confirmReplace()) { clear(); setLaunch(null); } }}
            onClose={() => setChatPanelOpen(false)}
            health={health}
            isOpen={chatPanelOpen}
          />
        </div>
      </main>

      {/* Real-time Execution Toast Notification */}
      <NotificationToast
        toast={activeToast}
        onDismiss={dismissToast}
        onNavigateToMonitoring={() => go("monitoring")}
      />
    </div>
  );
}
