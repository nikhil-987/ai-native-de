import { useEffect, useState } from "react";
import { LuBot, LuCheck, LuCloud, LuCopy, LuExternalLink, LuFolderCog, LuKey, LuPlugZap, LuRefreshCw, LuSave, LuSettings2, LuUndo2 } from "react-icons/lu";
import {
  azLogin, azLoginPoll, azLoginStart, azLogout, claudeLogin, claudeLogout, connectFabricMcp,
  getConfig, getClaudeStatus, getHealth, getMcp, installClaudeCli, saveClaudeApiKey, saveConfig,
} from "../lib/api.js";
import { Alert, Button, Card, Field, Spinner, cx, inputClass } from "./ui.jsx";

// Configure everything the medallion flow needs before (or between) runs.

const ENV_FIELDS = [
  { key: "FABRIC_WORKSPACE_NAME", label: "Default workspace name", hint: "Blank: select when starting a project" },
  { key: "FABRIC_WORKSPACE_ID", label: "Default workspace ID", hint: "Optional GUID" },
  { key: "RAW_LAKEHOUSE_NAME", label: "Default raw (source) lakehouse", hint: "Blank: select when starting a project" },
  { key: "SOURCE_TIMEZONE", label: "Source timezone", hint: "e.g. Asia/Kolkata; decides today's raw partition" },
];

function Status({ ok, wait, children }) {
  return (
    <span className={cx("inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-semibold", wait ? "text-muted" : ok ? "text-good" : "text-warn")}>
      {wait ? <Spinner /> : <span className="size-2 rounded-full bg-current" />}
      {children}
    </span>
  );
}

function ConnCard({ title, icon: Icon, status, children }) {
  return (
    <Card className="flex flex-col gap-2.5">
      <div className="flex items-center gap-2.5">
        <span className="grid size-8 shrink-0 place-items-center rounded-[9px] bg-accent-soft text-base text-accent"><Icon /></span>
        <h3 className="min-w-0 flex-1 text-sm font-bold">{title}</h3>
        {status}
      </div>
      {children}
    </Card>
  );
}

const Note = ({ children }) => <p className="text-xs text-muted">{children}</p>;
const KV = ({ k, v }) => (
  <div className="flex justify-between gap-2.5 border-b border-line py-1.5 text-[13.5px] last:border-b-0">
    <span className="text-muted">{k}</span><b className="break-all text-right font-medium">{v}</b>
  </div>
);

export default function Connections({ health, setHealth, model, setModel, busy }) {
  const [config, setConfig] = useState(null);
  const [offline, setOffline] = useState(false);
  const [dir, setDir] = useState("");
  const [env, setEnv] = useState({});
  const [userName, setUserName] = useState("");
  const [claudeKey, setClaudeKey] = useState("");
  const [azAuth, setAzAuth] = useState(null); // { url, code, sessionId }
  const [copiedCode, setCopiedCode] = useState(false);
  const [msg, setMsg] = useState({}); // section -> { ok, text }
  const [working, setWorking] = useState({}); // section -> bool

  const note = (k, ok, text) => setMsg((m) => ({ ...m, [k]: { ok, text } }));
  const work = (k, v) => setWorking((w) => ({ ...w, [k]: v }));

  function applyConfig(c) {
    setConfig(c);
    setDir(c.project_dir || "");
    setEnv(c.env?.values || {});
    if (c.user_name) setUserName(c.user_name);
  }

  useEffect(() => {
    getConfig().then(applyConfig).catch(() => setOffline(true));
  }, []);

  async function testAll() {
    work("all", true);
    try {
      const [h, c] = await Promise.all([getHealth(), getConfig()]);
      setHealth((prev) => ({ ...h, mcp: prev?.mcp }));
      applyConfig(c);
      setOffline(false);
      const m = await getMcp(true);
      setHealth((prev) => ({ ...prev, mcp: m }));
    } catch {
      setOffline(true);
    } finally {
      work("all", false);
    }
  }

  async function saveDir() {
    work("dir", true);
    try {
      applyConfig(await saveConfig({ project_dir: dir }));
      note("dir", true, "Saved. New runs use this project folder.");
      testAll();
    } catch (e) {
      note("dir", false, e.message);
    } finally {
      work("dir", false);
    }
  }

  async function saveEnv() {
    work("env", true);
    try {
      applyConfig(await saveConfig({ env }));
      note("env", true, "Saved to .env in the project folder. The skill reads it at the start of each run.");
      getHealth().then((h) => setHealth((prev) => ({ ...h, mcp: prev?.mcp }))).catch(() => {});
    } catch (e) {
      note("env", false, e.message);
    } finally {
      work("env", false);
    }
  }

  async function signIn() {
    work("az", true);
    setAzAuth(null);
    note("az", true, "Initiating Azure sign-in…");
    try {
      const data = await azLoginStart();
      if (data.status === "completed") {
        setHealth((h) => ({ ...h, az_user: data.az_user }));
        note("az", true, `Signed in as ${data.az_user}.`);
        work("az", false);
        return;
      }
      if (data.url && data.code) {
        setAzAuth({ url: data.url, code: data.code, sessionId: data.session_id });
        // Automatically open the login page in a new browser tab
        try {
          window.open(data.url, "_blank");
        } catch {}
        // Copy code to clipboard automatically
        if (navigator?.clipboard?.writeText) {
          navigator.clipboard.writeText(data.code).catch(() => {});
        }
        note("az", true, `Code: ${data.code} · Opening Microsoft sign-in tab…`);

        // Start polling for completion
        const interval = setInterval(async () => {
          try {
            const p = await azLoginPoll(data.session_id);
            if (p.status === "completed") {
              clearInterval(interval);
              setHealth((h) => ({ ...h, az_user: p.az_user }));
              setAzAuth(null);
              work("az", false);
              note("az", true, `Successfully signed in as ${p.az_user}.`);
            } else if (p.status === "error") {
              clearInterval(interval);
              setAzAuth(null);
              work("az", false);
              note("az", false, p.error || "Azure authentication failed.");
            }
          } catch {
            // Keep polling
          }
        }, 2000);
      }
    } catch (e) {
      work("az", false);
      note("az", false, e.message);
    }
  }

  async function signOutAz() {
    work("az", true);
    try {
      await azLogout();
      setHealth((h) => ({ ...h, az_user: null }));
      setAzAuth(null);
      note("az", true, "Signed out of Azure CLI.");
    } catch (e) {
      note("az", false, e.message);
    } finally {
      work("az", false);
    }
  }

  function copyCode() {
    if (azAuth?.code && navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(azAuth.code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 3000);
    }
  }

  async function autoConnectMcp() {
    work("mcpConnect", true);
    note("mcp", true, "Registering Microsoft Fabric MCP Server with Claude Code…");
    try {
      const res = await connectFabricMcp();
      if (res.ok) {
        setHealth((h) => ({ ...h, mcp: res.data || { fabric: true, servers: [{ name: "fabric", connected: true, status: "✓ Connected" }] } }));
        note("mcp", true, "Fabric MCP server successfully registered and connected!");
      } else {
        note("mcp", false, res.message || "Failed to register Fabric MCP server.");
      }
    } catch (e) {
      note("mcp", false, e.message || "Error registering Fabric MCP.");
    } finally {
      work("mcpConnect", false);
    }
  }

  async function recheckMcp() {
    work("mcp", true);
    try {
      const m = await getMcp(true);
      setHealth((h) => ({ ...h, mcp: m }));
    } catch (e) {
      note("mcp", false, e.message);
    } finally {
      work("mcp", false);
    }
  }

  async function installClaude() {
    work("claudeInstall", true);
    note("claude", true, "Installing Claude CLI via npm (@anthropic-ai/claude-code)... Please wait ~30-60 seconds.");
    try {
      const res = await installClaudeCli();
      if (res.ok) {
        setHealth((h) => ({ ...h, claude: true, claude_auth: res.status }));
        note("claude", true, "Claude CLI installed successfully! You can now sign in.");
      } else {
        note("claude", false, res.output || "Installation completed with warnings. Checking CLI status...");
        const st = await getClaudeStatus();
        setHealth((h) => ({ ...h, claude: !!st.installed, claude_auth: st }));
      }
    } catch (e) {
      note("claude", false, e.message || "Failed to install Claude CLI.");
    } finally {
      work("claudeInstall", false);
    }
  }

  async function signInClaude() {
    work("claude", true);
    note("claude", true, "Launching Claude sign-in window… Please complete authorization in your browser.");
    try {
      const res = await claudeLogin();
      if (!res.ok) {
        note("claude", false, res.message || "Failed to initiate Claude sign-in.");
        work("claude", false);
        return;
      }
      note("claude", true, res.message || "Sign-in launched. Authorize in the browser/terminal window.");
      
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const st = await getClaudeStatus();
          if (st.authenticated) {
            clearInterval(interval);
            setHealth((h) => ({ ...h, claude: true, claude_auth: st }));
            work("claude", false);
            note("claude", true, `Signed in to Claude successfully (${st.user || "OAuth"}).`);
          } else if (attempts >= 40) {
            clearInterval(interval);
            work("claude", false);
          }
        } catch {
          if (attempts >= 40) {
            clearInterval(interval);
            work("claude", false);
          }
        }
      }, 2500);
    } catch (e) {
      work("claude", false);
      note("claude", false, e.message);
    }
  }

  async function saveApiKey() {
    if (!claudeKey.trim()) return;
    work("claudeKey", true);
    try {
      const res = await saveClaudeApiKey(claudeKey.trim());
      setHealth((h) => ({ ...h, claude_auth: res.status }));
      setClaudeKey("");
      note("claude", true, "Anthropic API Key saved to .env and activated!");
    } catch (e) {
      note("claude", false, e.message);
    } finally {
      work("claudeKey", false);
    }
  }

  async function saveUserName() {
    if (!userName.trim()) return;
    work("userName", true);
    try {
      const cfg = await saveConfig({ user_name: userName.trim() });
      applyConfig(cfg);
      const h = await getHealth();
      setHealth((prev) => ({ ...h, mcp: prev?.mcp }));
      note("claude", true, `Logged in user name updated to "${userName.trim()}".`);
    } catch (e) {
      note("claude", false, e.message);
    } finally {
      work("userName", false);
    }
  }

  async function signOutClaude() {
    work("claude", true);
    try {
      const res = await claudeLogout();
      setHealth((h) => ({ ...h, claude_auth: res.status }));
      note("claude", true, "Signed out of Claude. Key removed.");
    } catch (e) {
      note("claude", false, e.message);
    } finally {
      work("claude", false);
    }
  }

  const Msg = ({ k }) => (msg[k] ? <Alert tone={msg[k].ok ? "good" : "bad"}>{msg[k].text}</Alert> : null);
  const mcp = health?.mcp;
  const envDirty = config && ENV_FIELDS.some((f) => (env[f.key] || "") !== (config.env?.values?.[f.key] || ""));
  const dirDirty = config && dir.trim() !== config.project_dir;

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="mb-1 text-[22px] font-bold">Connections</h2>
          <p className="text-muted">Everything the medallion flow needs. Set these once; the Studio uses them for every run.</p>
        </div>
        <Button variant="primary" onClick={testAll} disabled={working.all}>
          {working.all ? <><Spinner /> Testing…</> : <><LuRefreshCw /> Test all connections</>}
        </Button>
      </div>

      {offline && (
        <Alert>
          The backend isn't reachable. Start it from the <code>claude-bridge</code> folder with
          <code> python -m uvicorn server:app --host 127.0.0.1 --port 8000</code>, then press <b>Test all connections</b>.
        </Alert>
      )}

      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(320px,100%),1fr))] items-start gap-4">
        <ConnCard title="Project folder (mcp-claude)" icon={LuFolderCog}
          status={<Status ok={!!config?.skill_found} wait={!config && !offline}>{config?.skill_found ? "Medallion skill found" : "Skill not found"}</Status>}>
          <Note>The folder that contains <code>.claude/skills/medallion</code>. Claude Code runs here.</Note>
          <Field label="Path">
            <input className={inputClass} value={dir} onChange={(e) => setDir(e.target.value)} placeholder="C:\Users\you\Downloads\mcp-claude final\mcp-claude" disabled={offline} />
          </Field>
          {config && <Note>Source: {config.project_dir_source === "studio" ? "saved in the Studio" : config.project_dir_source === "env" ? "PROJECT_DIR environment variable" : "default location"}</Note>}
          <div><Button variant="primary" size="sm" onClick={saveDir} disabled={!dirDirty || working.dir || !!busy}><LuSave /> Save folder</Button></div>
          <Msg k="dir" />
        </ConnCard>

        <ConnCard title="Fabric defaults (.env)" icon={LuSettings2}
          status={<Status ok={!!config?.env?.exists} wait={!config && !offline}>{config?.env?.exists ? ".env found" : "No .env (optional)"}</Status>}>
          <Note>Optional defaults the skill reads from <code>.env</code> in the project folder. Leave blank to choose during the flow.</Note>
          {ENV_FIELDS.map((f) => (
            <Field key={f.key} label={f.label} hint={f.key}>
              <input className={inputClass} value={env[f.key] || ""} placeholder={f.hint} disabled={offline || !config?.skill_found}
                onChange={(e) => setEnv((v) => ({ ...v, [f.key]: e.target.value }))} />
            </Field>
          ))}
          <div className="flex flex-wrap gap-2">
            <Button variant="primary" size="sm" onClick={saveEnv} disabled={!envDirty || working.env}><LuSave /> Save to .env</Button>
            {envDirty && <Button variant="ghost" size="sm" onClick={() => setEnv(config.env?.values || {})}><LuUndo2 /> Undo changes</Button>}
          </div>
          <Msg k="env" />
        </ConnCard>

        <ConnCard title="Azure CLI" icon={LuCloud}
          status={<Status ok={!!health?.az_user} wait={!health}>{health?.az_user ? "Signed in" : health?.az_installed === false ? "Not installed" : "Not signed in"}</Status>}>
          <Note>Fabric is reached with your own Azure identity (<code>az login</code>); no client secrets.</Note>
          {health?.az_user && (
            <>
              <KV k="Account" v={health.az_user} />
              <KV k="Status" v="Connected & Authorized" />
            </>
          )}

          <div className="mt-2 flex flex-col gap-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="primary" size="sm" onClick={signIn} disabled={working.az || offline || health?.az_installed === false}>
                {working.az && !azAuth ? <><Spinner /> Contacting Azure…</> : working.az ? <><Spinner /> Waiting for approval…</> : health?.az_user ? "Sign in as different user" : "Sign in with Azure CLI"}
              </Button>
              {health?.az_user && (
                <Button variant="ghost" size="sm" onClick={signOutAz} disabled={working.az}>
                  Sign out
                </Button>
              )}
            </div>

            {azAuth && (
              <div className="rounded-xl border border-accent/40 bg-nav p-3.5 shadow-sm">
                <div className="mb-1 text-xs font-semibold text-accent">Sign-In Code (Microsoft Device Login):</div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-lg bg-code px-3 py-1.5 font-mono text-base font-bold tracking-wider text-white">
                    {azAuth.code}
                  </span>
                  <Button variant="nav" size="sm" onClick={copyCode}>
                    {copiedCode ? <><LuCheck className="text-good" /> Copied!</> : <><LuCopy /> Copy Code</>}
                  </Button>
                  <a
                    href={azAuth.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-accent/50 bg-accent/15 px-3 py-1.5 text-xs font-semibold text-accent hover:bg-accent/25 transition"
                  >
                    Open Login Tab <LuExternalLink />
                  </a>
                </div>
                <p className="mt-2 text-xs text-muted">
                  A Microsoft sign-in tab was opened. Enter code <b>{azAuth.code}</b> and approve to complete sign-in. This Studio will automatically detect completion.
                </p>
              </div>
            )}
          </div>
          <Msg k="az" />
        </ConnCard>

        <ConnCard title="Fabric MCP server" icon={LuPlugZap}
          status={<Status ok={!!mcp?.fabric} wait={!mcp || working.mcp}>{!mcp ? "Checking…" : mcp.fabric ? "Connected" : "Not connected"}</Status>}>
          <Note>
            The skill lists workspaces, lakehouses and files and creates pipelines through this server.
            Register it with Claude Code under a name containing <code>fabric</code>:
          </Note>
          <pre className="overflow-x-auto rounded-lg border border-line bg-code px-2.5 py-2 text-xs select-all font-mono">claude mcp add --scope user fabric -- npx -y @microsoft/fabric-mcp server start</pre>
          {mcp?.servers?.length > 0 && (
            <ul className="grid gap-1 text-[13px]">
              {mcp.servers.map((s) => (
                <li key={s.name} className="flex flex-wrap items-center gap-2">
                  <span className={cx("size-2 rounded-full", s.connected ? "bg-good" : "bg-warn")} /><b>{s.name}</b><span className="text-xs text-muted">{s.status}</span>
                </li>
              ))}
            </ul>
          )}
          {mcp?.error && <Alert>{mcp.error}</Alert>}
          <div className="flex flex-wrap items-center gap-2">
            {!mcp?.fabric && (
              <Button variant="primary" size="sm" onClick={autoConnectMcp} disabled={working.mcpConnect || offline}>
                {working.mcpConnect ? <><Spinner /> Connecting MCP…</> : <><LuPlugZap /> Auto-Connect Fabric MCP</>}
              </Button>
            )}
            <Button variant={mcp?.fabric ? "primary" : "ghost"} size="sm" onClick={recheckMcp} disabled={working.mcp || offline}>
              {working.mcp ? <><Spinner /> Checking…</> : <><LuRefreshCw /> Recheck</>}
            </Button>
          </div>
          <Msg k="mcp" />
        </ConnCard>

        <ConnCard title="Claude Code" icon={LuBot}
          status={
            <Status ok={!!health?.claude_auth?.authenticated} wait={!health}>
              {health?.claude_auth?.authenticated
                ? health?.claude_auth?.user_name || health?.claude_auth?.user || "Authenticated"
                : (health?.claude_auth?.installed ?? health?.claude)
                ? "Not authenticated"
                : "CLI not found"}
            </Status>
          }>
          <Note>Runs headless in the project folder with the medallion skill and fabric agent.</Note>
          {health?.claude_auth?.authenticated && (
            <>
              <KV k="Status" v="Connected & Ready" />
              <KV k="Logged-in User" v={health.claude_auth.user_name || "Nikhil Kumar Gupta"} />
              {health.claude_auth.user_email && <KV k="Account / Email" v={health.claude_auth.user_email} />}
              <KV k="Auth method" v={health.claude_auth.auth_method === "api_key" ? "Anthropic API Key" : "Claude CLI OAuth"} />
            </>
          )}
          <Field label="Model">
            <select className={inputClass} value={model} onChange={(e) => setModel(e.target.value)} disabled={!!busy}>
              <option value="">Claude Code default</option>
              <option value="claude-opus-5-5">Claude Opus 5.5</option>
              <option value="claude-sonnet-5-5">Claude Sonnet 5.5</option>
            </select>
          </Field>
          <KV k="Tool permissions" v={health?.permission_mode || "—"} />
          <Note>Approval decisions always wait for you; tool calls are auto-approved with <code>bypassPermissions</code>.</Note>

          <div className="mt-3 flex flex-col gap-2.5 rounded-lg border border-line bg-nav p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">User & Authentication</span>
              {health?.claude_auth?.authenticated && (
                <button className="text-xs text-bad hover:underline cursor-pointer" onClick={signOutClaude} disabled={working.claude}>
                  Sign out
                </button>
              )}
            </div>

            <Field label="Logged-in User Name" hint="Display name used across Studio sessions">
              <div className="flex items-center gap-2">
                <input
                  className={inputClass}
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder={health?.claude_auth?.user_name || "Nikhil Kumar Gupta"}
                  disabled={offline}
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={saveUserName}
                  disabled={working.userName || !userName.trim() || userName === config?.user_name}
                >
                  <LuSave /> Save
                </Button>
              </div>
            </Field>

            {!(health?.claude_auth?.installed ?? health?.claude) && (
              <div className="rounded-lg border border-warn/30 bg-warn/10 p-2.5 text-xs text-warn flex flex-col gap-2">
                <span>Claude CLI is not found in PATH. You can enter an Anthropic API Key below, or install the CLI automatically:</span>
                <div>
                  <Button variant="primary" size="sm" onClick={installClaude} disabled={working.claudeInstall || offline}>
                    {working.claudeInstall ? <><Spinner /> Installing Claude CLI…</> : <><LuBot /> Install Claude CLI</>}
                  </Button>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={signInClaude}
                disabled={working.claude || offline || !(health?.claude_auth?.installed ?? health?.claude)}
              >
                {working.claude ? <><Spinner /> Signing in…</> : <><LuBot /> Sign in with Claude CLI</>}
              </Button>
            </div>
            <div className="flex flex-col gap-1.5 pt-1">
              <label className="text-xs font-medium text-muted">Or enter Anthropic API Key directly:</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  className={cx(inputClass, "font-mono text-xs")}
                  placeholder="sk-ant-api03-..."
                  value={claudeKey}
                  onChange={(e) => setClaudeKey(e.target.value)}
                  disabled={offline}
                />
                <Button variant="nav" size="sm" onClick={saveApiKey} disabled={!claudeKey.trim() || working.claudeKey}>
                  {working.claudeKey ? <Spinner /> : <><LuKey /> Save Key</>}
                </Button>
              </div>
            </div>
          </div>
          <Msg k="claude" />
        </ConnCard>
      </div>
    </div>
  );
}
