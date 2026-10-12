# Adrosonic · AI Native Data Engineering Console

A web app for running the **medallion** flow (Bronze → Silver → Gold → Orchestrator → Semantic Model
on Microsoft Fabric) from a browser instead of the VS Code chat.

```
React app (frontend/)  →  FastAPI backend (backend/server.py)  →  Claude Code CLI  →  Fabric MCP server / Fabric REST / az / Livy
                                                               runs inside the mcp-claude project folder
```

The backend runs **Claude Code** in headless mode inside your `mcp-claude` project folder. Claude
therefore uses the same `medallion` skill, `fabric` agent, Fabric MCP server and Azure login as the
VS Code chat. The app is completely portable and can run on your local machine or a cloud VM.

---

## ⚡ Portable Quick Start (Any System or VM)

See the full **[Portable Setup Guide (PORTABLE_SETUP.md)](./PORTABLE_SETUP.md)** for detailed cloud VM instructions.

### Windows:
```powershell
.\setup.ps1      # Installs Python/Node deps, builds UI bundle
.\start.ps1      # Launches Studio at http://localhost:8000
```

### Linux / macOS / Azure Cloud VM:
```bash
chmod +x setup.sh start.sh
./setup.sh       # Installs Python/Node deps, builds UI bundle
./start.sh       # Launches Studio at http://localhost:8000
```

### Docker:
```bash
docker compose up --build -d
```

---

## 1. What you need

Install these on the new machine first.

| Requirement | Version | Check with | Notes |
|---|---|---|---|
| **Python** | 3.10 or newer | `python --version` | Tick "Add Python to PATH" when installing on Windows |
| **Node.js** (includes npm) | 18 or newer (20 LTS recommended) | `node --version` | Builds the frontend; many MCP servers also start through `npx` |
| **Claude Code CLI** | latest | `claude --version` | See step 2.1 |
| **Azure CLI** | latest | `az version` | Used to sign in to Fabric |
| **Fabric MCP server** | latest | `claude mcp list` | The skill lists workspaces, lakehouses and files and creates pipelines through its `onelake_*`, `core_*` and `datafactory_*` tools. See step 2.7 |
| **The `mcp-claude` project folder** | — | — | Must contain `.claude/skills/medallion/` |
| `mcp-claude\.env` (optional) | — | — | Copy of `.env.example`: default workspace, raw lakehouse and timezone. See step 2.6 |
| A **Claude subscription** (Pro / Max / Team) or an Anthropic API key | — | — | Claude Code needs one of these |
| Access to the **Microsoft Fabric** workspace | — | — | Your Azure account must be able to see the workspace |

---

## 2. One-time setup

### 2.1 Install and sign in to Claude Code

```
npm install -g @anthropic-ai/claude-code
claude
```

When `claude` starts the first time, follow the prompts to log in, then type `/exit`.

Check it works without a window:

```
claude -p "Say hello"
```

You should get a short reply. If it asks you to log in, run `claude` again and finish the login.

### 2.2 Sign in to Azure

```
az login
az account show
```

`az account show` should print your account and tenant. You can also sign in later from the app's
sidebar (**Sign in with az login**). No client secrets or service principals are needed.

### 2.3 Unzip the app

Unzip the folder anywhere, for example:

```
C:\Users\<you>\Downloads\claude-bridge\
├── backend\
│   ├── server.py
│   ├── fabric.py
│   └── requirements.txt
├── frontend\
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src\
└── README.md
```

> **If the zip contains `frontend\node_modules` or `backend\__pycache__`, delete them.** They were built for the
> original machine and can break on a different system. `npm install` recreates `node_modules`.

### 2.4 Install the backend (Python)

Open a terminal in the unzipped `claude-bridge\backend` folder:

```
cd "C:\Users\<you>\Downloads\claude-bridge\backend"
python -m pip install -r requirements.txt
```

Optional: to keep these packages separate from the rest of your Python setup, use a virtual
environment.

```
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux
python -m pip install -r requirements.txt
```

If you use one, activate it every time before you start the server.

### 2.5 Build the frontend (React)

```
cd frontend
npm install
npm run build
cd ..
```

This creates `frontend\dist`, which the backend serves. Run `npm run build` again whenever you change the
React code.

### 2.6 Tell the backend where the `mcp-claude` project is

By default the backend looks for the project at:

```
<your home folder>\Downloads\mcp-claude final\mcp-claude
```

If your project is anywhere else, set `PROJECT_DIR` to its folder: the folder that contains `.claude`.
Set it in the same terminal you will start the server from.

**Windows PowerShell**
```
$env:PROJECT_DIR = "C:\path\to\mcp-claude"
```

**Windows Command Prompt**
```
set PROJECT_DIR=C:\path\to\mcp-claude
```

**macOS / Linux**
```
export PROJECT_DIR="/path/to/mcp-claude"
```

To set it permanently on Windows, run `setx PROJECT_DIR "C:\path\to\mcp-claude"` once, then open a
new terminal.

**Optional `.env` in the project.** The skill reads `mcp-claude\.env` for defaults. Copy
`.env.example` to `.env` and fill in what you want fixed; leave a value blank to choose it in the chat.

| Variable | Used for |
|---|---|
| `FABRIC_WORKSPACE_ID` / `FABRIC_WORKSPACE_NAME` | Default workspace (otherwise you pick one at G0b) |
| `RAW_LAKEHOUSE_NAME` | Default source lakehouse (otherwise you pick one at G1) |
| `SOURCE_TIMEZONE` | Decides "today" for the raw `<yyyy>/<MM>/<dd>` partition |

The sidebar shows whether `.env` was found and which workspace it names.

### 2.7 Register the Fabric MCP server with Claude Code

The skill reaches Fabric through the Fabric MCP server (see `mcp-claude\docs\PORTABLE_SETUP.md`).
Claude Code in the app must see it, so register it at **user** scope (or add an `.mcp.json` to the
`mcp-claude` folder). Name it `fabric` so the app can recognise it:

```
claude mcp add --scope user fabric -- <command that starts the Fabric MCP server>
```

Use the start command from the Fabric MCP server's own README. Then check it:

```
cd "C:\path\to\mcp-claude"
claude mcp list
```

The `fabric` line should end with **Connected**.

---

## 3. Start the app

From the `claude-bridge\backend` folder:

```
cd backend
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000** in your browser.

Keep the terminal open while you use the app. To stop it, press **Ctrl+C** in that terminal.

### Quick test

1. Open the **Connections** tab and press **Test all connections**. Claude Code, project folder, Azure
   CLI and Fabric MCP server should all be green (the MCP check takes a few seconds). `.env` is
   optional.
2. Open the **Dashboard**. Pick your workspace; the three tiles fill in with the project counts
   (a few seconds per scan).
3. Press **＋ Start new project**, pick a lakehouse and a raw folder, and press **Start project**. The
   Studio opens and, after a short wait, asks you to confirm the suggested target folder. If you see
   that, the setup is complete.

You can also check the backend directly: http://127.0.0.1:8000/api/health and
http://127.0.0.1:8000/api/mcp

---

## 4. Developing the frontend (optional)

To see React changes as soon as you save, run the backend and the Vite dev server in two terminals.

**Terminal 1: backend**
```
cd "C:\Users\<you>\Downloads\claude-bridge\backend"
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

**Terminal 2: frontend**
```
cd "C:\Users\<you>\Downloads\claude-bridge\frontend"
npm run dev
```

Open **http://127.0.0.1:5173**. Requests to `/api` are forwarded to the backend on port 8000. When
you're done, run `npm run build` so port 8000 serves the new version.

---

## 5. Using the app

| Area | What it does |
|---|---|
| **Dashboard** (Home) | Executive overview, system health status, Total/Completed/In-progress KPI tiles, recent workspace activity feed, and **Start New Project** wizard. |
| **Project Catalog** (Projects) | Catalog of all workspace projects with status, search, layer chips, and direct **Resume** action. |
| **Studio** | The progressive Medallion flow (Source → Target → Profiling → Bronze → Silver → Gold → Orchestrator → Semantic model → Summary). Features a **minimal progress header** with active workspace name, an interactive **In-Studio Project Switcher Dropdown** to seamlessly switch between projects, and compact completion percentage. |
| **Monitoring** | Full-featured tabular observability hub for Microsoft Fabric runs (Notebooks, Data Pipelines, Semantic Models). Displays Project Name, Run ID (with copy & Fabric Monitor deep-links), item type, status badges, trigger timestamps, real-time filters, keyword search, and pagination. |
| **Orchestrator** | Displays the Data Factory orchestrator pipeline once created: sequential activities (Bronze → Silver → Gold → Refresh Semantic Model), lakehouses, and execution status. |
| **Semantic Model** | Visualizes Direct Lake Power BI model tables, relationships, and DAX measures. |
| **Conversation Drawer** | Universal slide-out drawer rendering Claude's internal execution steps, tool invocations, and chat interface. Starts **collapsed by default** and toggles open across all pages via the top-right button. |
| **Floating Controls** | Top-right floating controls: Stop Run, Notification Center (real-time badge & toast alerts), Conversation toggle, Mockups/Live Engine mode switcher, and Dark/Light theme toggle. |
| **Connections** | Accessible from the sidebar; configure and test Azure CLI authentication, Claude Code CLI login / Anthropic API Key (with logged-in user display), Fabric MCP server, and workspace defaults. |

**New project.** After the workspace and **1 Start a new project**, you pick the source lakehouse and
raw data folder (G1), then confirm the suggested **target folder name** or type your own (G2). Claude
creates the target folder with `<Target>_LH`, `notebooks`, `orchestrator` and `semantic model` inside
it. The target lakehouse itself is only created in Fabric on the first notebook or orchestrator run,
so the sidebar marks it "created on first run" until then.

**Resume.** **2 Resume an existing project** looks for projects in the workspace (lakehouses at the
workspace root and project folders that contain `dbo.project_status`). Pick one and the sidebar shows
its stage, status, current gate, next action and completion %. The flow continues at that gate.

**Run prompts.** Bronze, Silver, Gold, the orchestrator and the semantic model refresh each ask
`[y/n/skip]`:

| Reply | What happens |
|---|---|
| **Run now** (`y`) | The run is submitted to Fabric in the background and gets a run ID. Claude then asks `[1/2/3]`: **1** next stage, **2** check status, **3** end the chat. With 1 and 3 the Fabric job keeps running and writes its outcome to `dbo.project_status` |
| **Skip to next stage** (`skip`) | Nothing runs; the flow moves to the next stage |
| **Don't run · stop** (`n`) | The item stays deployed but is not run, and the session ends |

Every background run appears under **Background runs** in the sidebar. When Claude has reported the
workspace and item IDs, **check status** asks Fabric directly, without going through the chat. If a
run fails, Claude matches the error against the failure registry and offers a fixed version.

**Approvals.** Claude runs its own steps without asking: Fabric API calls, `az` commands, scripts
and file writes. **Your decisions at each gate** (y/n/skip, APPROVE/DECLINE, UPLOAD/SKIP, 1/2/3)
still wait for you.

The conversation is saved in your browser, so a page refresh keeps it. Use **clear** in the sidebar
or **Start new run** to begin again.

---

## 6. Settings (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `PROJECT_DIR` | `<home>\Downloads\mcp-claude final\mcp-claude` | Path to the `mcp-claude` project. A folder saved on the **Connections** page (stored in `studio.json` next to `server.py` in `backend/`) takes priority |
| `PERMISSION_MODE` | `bypassPermissions` | How Claude handles tool permissions. `bypassPermissions` approves everything. `acceptEdits` approves only file edits, so most Fabric calls get blocked |

Dataset and naming settings (workspace, raw lakehouse, timezone, lakehouse / notebook / pipeline name
patterns, watermark and SCD defaults) are not app settings. They live in `mcp-claude\.env` and
`mcp-claude\.claude\skills\medallion\client_config.md`.

To use another port, change `--port 8000` in the start command, for example `--port 8080`. If you use
`npm run dev`, also update the proxy address in `frontend\vite.config.js`.

---

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| Connections shows **Claude Code: Not found** | Install Claude Code (step 2.1). Open a new terminal so the PATH updates, check `claude --version`, then restart the server |
| Connections shows **Skill not found** | Enter the folder containing `.claude\skills\medallion` under **Project folder** and press **Save folder** (or set `PROJECT_DIR`, step 2.6) |
| Page says **"UI not built"** | Run `npm install` and `npm run build` in `frontend\` (step 2.5) |
| `'python' is not recognized` | Reinstall Python with "Add to PATH" ticked, or use `py -m uvicorn ...` instead |
| `No module named fastapi` | Run `python -m pip install -r requirements.txt` inside `backend/`, and activate the virtual environment if you made one |
| `npm install` fails or the build errors | Delete `frontend\node_modules` and `frontend\package-lock.json`, check `node --version` is 18 or newer, then run `npm install` again |
| **Port 8000 is already in use** | Another copy is running. Windows: `netstat -ano \| findstr :8000`, then `taskkill /PID <pid> /F`. Or start on another port |
| Sidebar shows **Azure CLI not signed in** | Click **Sign in with az login** in the sidebar, or run `az login` in a terminal |
| Sidebar shows **Fabric MCP server not found**, or Claude can't list workspaces or lakehouses | Register the server (step 2.7) and check `claude mcp list` in the `mcp-claude` folder shows it as Connected. Then click **recheck** in the sidebar. The server must be named with `fabric` in it for the sidebar to recognise it |
| Claude says the Fabric connection is not active | Run `az account show`. Make sure your account can see the Fabric workspace |
| The target lakehouse isn't in Fabric after G2 | Expected. Only the target folder is created at G2; `<Target>_LH` is created on the first notebook or orchestrator run |
| A job is still running after the chat stopped | Expected after **3** at a run prompt. Click **check status** under **Background runs**, or start a new run and choose **2 Resume an existing project** to see the outcome from `dbo.project_status` |
| Dashboard says **Not signed in** or shows a 401 error | Sign in on the Connections page (or `az login`), then press **Refresh** |
| Dashboard counts projects but every card says **Status unknown** | The server can't read `project_status`. Run `python -m pip install -r requirements.txt` inside `backend/` (installs `deltalake`) and restart the server |
| A project is missing from the dashboard | Its lakehouse must contain `Tables/dbo/project_status` (or `Tables/project_status`); the table is written by the first notebook run. Press **Refresh** to rescan |
| **check status** says the IDs must be GUIDs, or the link is missing | Claude hasn't reported the workspace or item ID for that run. Reply **2** at the `[1/2/3]` prompt to check through the chat instead |
| Claude replies with a login or authentication error | Run `claude` in a terminal and log in again |
| Replies take a long time | Each message starts Claude Code fresh, so simple replies take a few seconds. Profiling and deploying can take several minutes; the timer in the top bar shows progress, and **Stop** cancels. Runs themselves happen in the background in Fabric |

---

## 8. Security notes

- The server listens on `127.0.0.1` only, so other computers cannot reach it. Don't change it to
  `0.0.0.0` or put it on a shared server.
- With the default `bypassPermissions`, Claude can run any command on this machine as you. Only use
  it with projects and documents you trust.
- Usage counts against the Claude subscription or API key that Claude Code is logged in with.
- Using one person's Claude subscription to serve other people is not allowed. For a shared
  deployment, use an Anthropic API key and the Claude API.

---

## 9. Project structure

| Path | What it does |
|---|---|
| `backend/server.py` | FastAPI backend: `/api/chat` (streams Claude's reply), `/api/stop`, `/api/upload`, `/api/az/login`, `/api/health` (also reports `mcp-claude\.env`), `/api/config` (GET / PUT the project folder and `.env` defaults), `/api/mcp` (Fabric MCP server status), `/api/runs/{run_id}` (Fabric job or semantic model refresh status through `az rest`), `/api/fabric/workspaces`, `/api/fabric/lakehouses`, `/api/fabric/raw-folders`, `/api/fabric/projects` (dashboard and wizard); serves the built React app |
| `backend/fabric.py` | Read-only Fabric REST and OneLake lookups with your `az login` token: workspaces, lakehouses with their folders, raw folders under `Files/`, project discovery and `project_status` reading (via `deltalake`). Project scans are cached for 2 minutes; **Refresh** rescans |
| `backend/studio.json` | Created when you save a project folder on the Connections page |
| `backend/requirements.txt` | Python packages for the backend |
| `frontend/package.json` | Frontend packages and the `dev` / `build` scripts |
| `frontend/vite.config.js` | Vite build settings and the dev-server proxy to the backend |
| `frontend/src/App.jsx` | Page layout and tabs (Chat, Flow map, Orchestrator, Semantic Model) |
| `frontend/src/hooks/useClaudeSession.js` | Sends prompts and turns the streamed reply into chat messages |
| `frontend/src/hooks/useTheme.js` | Light / dark mode |
| `frontend/src/lib/flow.js` | Gate list and stages; reads the flow status out of Claude's replies |
| `frontend/src/lib/gates.js` | Studio guide for each gate: what it does and what each button means (mirrors `interface.md`) |
| `frontend/src/components/Dashboard.jsx` | Dashboard: workspace picker, project counts, project cards, recent activity, new-project wizard |
| `frontend/src/components/Studio.jsx` | The Studio's progressive sections and action buttons |
| `frontend/src/lib/sections.js` | Studio sections, layer colours, and how replies map onto sections |
| `frontend/src/components/Connections.jsx` | The Connections page |
| `frontend/src/components/` | Also the sidebar, chat messages, composer, flow map, orchestrator and semantic model panels |
| `frontend/src/styles.css` | Tailwind CSS v4 entry: light / dark colour tokens (exposed as Tailwind colours such as `bg-panel`, `text-muted`, `bg-gold-soft`), the layer colours (`.bronze`, `.silver`, `.gold`, `.orch`, `.semantic` set `bg-layer` / `text-layer`), dark mode on `data-theme`, and the styles for Claude's Markdown output. Components are styled with Tailwind utility classes; icons come from `react-icons` (Lucide set) |
| `frontend/src/components/ui.jsx` | Shared buttons, cards, pills, alerts, fields and spinner |
| `frontend/public/adrosonic-logo.svg` (or `.png`) | The Adrosonic logo shown in the sidebar. Optional `adrosonic-mark.svg` / `.png` (square symbol) is used for avatars and the browser tab; without it the full logo is used. Rebuild after adding them |
| `frontend/src/components/Logo.jsx` | Loads those logo files, with a text fallback when none is present |
| `frontend/src/components/Layers.jsx` | Layer chips and the bronze → silver → gold progress bar |

**How the app tracks the flow.** The backend adds a short instruction to Claude's system prompt
(`UI_PROTOCOL` in `backend/server.py`). Claude then ends each reply with a hidden line describing the current
gate (including `PROJECT` for picking a project to resume and `POST_RUN` for the `[1/2/3]` choice
after a run), the project and target folder, stage statuses, background runs, the resume summary from
`dbo.project_status`, the orchestrator and the semantic model; the app hides that line from the chat.
If the line is missing, the app falls back to matching gate questions and run messages. If you reword
a gate question in `mcp-claude/.claude/skills/medallion/interface.md`, update its pattern in
`frontend/src/lib/flow.js` too, and its button wording in `frontend/src/lib/gates.js`.

The skill files in `mcp-claude/.claude/` are not modified by this app.
