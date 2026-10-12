# Portable Setup Guide: AI Data Engineering Studio

This guide explains how to set up and run the **AI Data Engineering Studio** on **any new system**, laptop, or **Virtual Machine (VM)** (Windows, Ubuntu, macOS, or Azure Cloud VM).

> 📄 **Word Document**: A fully styled, publication-ready Word Document version of this guide is available at [`AI_Data_Engineering_Studio_Portable_Setup_Guide.docx`](./AI_Data_Engineering_Studio_Portable_Setup_Guide.docx).

---

## 📋 The 6 Portable Assets

To set up and run this Studio on any new machine, you need:

| # | Asset | Description | How It's Handled |
|---|---|---|---|
| **1** | **`mcp-claude` Folder** | Contains `.claude/skills/medallion/` & `.claude/agents/fabric.agent.md` | Auto-detected if placed as sibling or configured via `MCP_CLAUDE_DIR` |
| **2** | **Fabric Skills Repo** | Microsoft Fabric MCP Server tools (`onelake_*`, `datafactory_*`) | Either cloned locally as sibling or registered via `npx -y @microsoft/fabric-mcp` |
| **3** | **This App (`claude-bridge`)** | React frontend + FastAPI backend (`frontend/` & `backend/`) | Cloned inside the root directory |
| **4** | **Fabric Account** | Access to at least one Fabric Workspace with Contributor rights | Verified automatically via Azure CLI |
| **5** | **Azure CLI (`az`)** | Official Microsoft Azure command-line tool | Authenticates interactively (`az login`) — **zero client secrets needed** |
| **6** | **Claude Account / CLI** | Claude Code CLI (`claude`) | Authenticated via `claude login` or `ANTHROPIC_API_KEY` |

---

## 🗂️ Standard Directory Layout: `AI Data Engineering Studio`

All three repositories sit side-by-side as siblings inside a common parent folder named **`AI Data Engineering Studio/`**:

```text
AI Data Engineering Studio/
├── claude-bridge/              # 1. This Web Studio app (frontend + backend)
│   ├── backend/
│   │   ├── server.py           # FastAPI backend & static SPA host
│   │   ├── fabric.py           # OneLake / Fabric REST token client
│   │   ├── mock_data.py        # Demo mode simulation streams
│   │   └── requirements.txt    # Python backend package dependencies
│   ├── frontend/
│   │   ├── src/                # React components & Medallion UX
│   │   ├── package.json        # Node.js dependencies
│   │   └── vite.config.js      # Vite build & proxy config
│   ├── setup.ps1 / setup.sh    # Automated cross-platform setup scripts
│   └── start.ps1 / start.sh    # One-command startup scripts
│
├── mcp-claude/                 # 2. Medallion skills repository
│   ├── .claude/
│   │   ├── agents/fabric.agent.md
│   │   └── skills/medallion/
│   └── .env.example
│
└── fabric-mcp-server/          # 3. Microsoft Fabric MCP server (cloned here)
```

### Initial Clone Setup (One-time):
In your target working folder:
```bash
# Create the parent studio directory
mkdir "AI Data Engineering Studio" && cd "AI Data Engineering Studio"

# 1. Clone this Studio web app
git clone <claude-bridge-repo-url> claude-bridge

# 2. Clone the medallion skills repository
git clone <mcp-claude-repo-url> mcp-claude

# 3. Clone the official Microsoft Fabric MCP Server repository
git clone https://github.com/microsoft/fabric-mcp-server.git fabric-mcp-server
```

*(Note: The setup scripts automatically detect `../mcp-claude` and `../fabric-mcp-server` without any manual path configuration).*

---

## 📦 Package Setup Details: Backend & Frontend

### 1. Backend Python Packages Setup

The backend is built with Python (3.10+) and FastAPI.

#### Packages Overview (`backend/requirements.txt`):
- **`fastapi>=0.110`**: High-performance asynchronous REST API framework providing endpoints for chat streaming, workspace listings, and status polling.
- **`uvicorn>=0.29`**: ASGI web server powering the FastAPI backend.
- **`python-dotenv>=1.0.0`**: Automatic environment variable loading from root `.env`.
- **`python-multipart>=0.0.9`**: Multipart form data parser for uploading business rules spreadsheets (`business_rules.xlsx`) and STTM mappings (`marine_sttm.xlsx`).
- **`pydantic>=2.6`**: Request/response schema validation and type safety.
- **`deltalake>=0.18` & `pyarrow>=14`**: Direct local reading and parsing of OneLake Delta tables (`dbo.project_status`) without needing a heavy Spark engine running on the host.

#### Manual Installation Steps:
```bash
cd "AI Data Engineering Studio/claude-bridge"

# (Optional but recommended) Create and activate a Python virtual environment:
# On Windows:
python -m venv .venv
.\.venv\Scripts\activate

# On Linux / macOS / Cloud VM:
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install all backend dependencies:
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### 2. Frontend Node.js Packages Setup

The frontend is a single-page application built with React 18, Vite 5, and Tailwind CSS v4.

#### Packages Overview (`frontend/package.json`):
- **`react` & `react-dom` (`^18.3.1`)**: Component-based UI framework powering the Studio's stage-by-stage gates and interactive panels.
- **`vite` (`^5.4.0`)**: Next-generation frontend tooling providing rapid Hot Module Replacement (HMR) and production bundling.
- **`@tailwindcss/vite` & `tailwindcss` (`^4.3.3`)**: Modern Tailwind CSS v4 styling with ADROSONIC branding tokens (Navy `#152337`, Cyan `#00CCFF`, Montserrat font family).
- **`react-icons` (`^5.7.0`)**: Comprehensive iconography for Fabric lakehouses, Medallion layer badges (Bronze, Silver, Gold), pipelines, and connections.
- **`marked` (`^12.0.2`) & `dompurify` (`^3.1.6`)**: Markdown parser and HTML sanitizer for safe rendering of streaming Claude Code responses, tables, and syntax-highlighted code.

#### Manual Installation Steps:
```bash
cd "AI Data Engineering Studio/claude-bridge/frontend"

# 1. Install all npm modules:
npm install

# 2. Build the production bundle:
# This compiles the React app into frontend/dist, which FastAPI directly serves at port 8000
npm run build

# (Optional) For development with live Hot Module Replacement:
# Starts Vite dev server on http://localhost:5173 with proxy forwarding /api to http://127.0.0.1:8000
npm run dev
```

---

## 🚀 Quick Setup (Automated)

### Option A: Windows (Local or VM)

1. **Install System Prerequisites**:
   - [Python 3.10+](https://www.python.org/downloads/) (Tick "Add python.exe to PATH")
   - [Node.js 18+](https://nodejs.org/) (Includes `npm`)
   - [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

2. **Authenticate**:
   ```powershell
   az login
   claude login     # (Optional: If Claude CLI is installed via npm i -g @anthropic-ai/claude-code)
   ```

3. **Run Automated Setup**:
   ```powershell
   cd "AI Data Engineering Studio\claude-bridge"
   .\setup.ps1
   ```
   *`setup.ps1` automatically checks Python, Node, Azure CLI, Claude CLI, detects `mcp-claude` and `fabric-mcp-server`, installs backend Python packages, installs frontend node modules, and builds the production bundle.*

4. **Start the Studio**:
   ```powershell
   .\start.ps1
   ```
   Open **http://localhost:8000** in your browser.

---

### Option B: Linux / macOS / Azure Cloud VM (Ubuntu)

1. **Install System Prerequisites**:
   ```bash
   # Ubuntu / Debian VM:
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv nodejs npm git curl

   # Install Azure CLI:
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # (Optional) Install Claude Code CLI:
   sudo npm install -g @anthropic-ai/claude-code
   ```

2. **Authenticate**:
   ```bash
   # For Headless / Remote SSH VMs, use device code authentication:
   az login --use-device-code

   # Authenticate Claude:
   claude login
   # OR export ANTHROPIC_API_KEY="your-api-key"
   ```

3. **Run Automated Setup**:
   ```bash
   cd "AI Data Engineering Studio/claude-bridge"
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

4. **Start the Studio**:
   ```bash
   ./start.sh
   ```
   Open **http://localhost:8000** (or `http://<VM-PUBLIC-IP>:8000`).

---

### Option C: Docker / Container Deployment

If your VM has Docker installed, you can spin up the entire studio with zero manual package installation:

```bash
cd "AI Data Engineering Studio/claude-bridge"
docker compose up --build -d
```
*(Mounts Azure credentials from `~/.azure`, `mcp-claude`, and `fabric-mcp-server` from the parent directory).*

---

## 🔐 Authentication & Identity Model

### 1. Azure CLI Authentication: Dual Sign-In Options (Inside & Outside the App)
> [!NOTE]
> **No Client Secrets or Service Principals Required**
> The platform uses interactive Azure CLI OAuth tokens (`az account get-access-token --resource https://api.fabric.microsoft.com`).
> Any user who can access Fabric in the Power BI / Fabric web portal can run this Studio immediately without requesting enterprise tenant administrator secrets.

#### Option A: Outside the App (Terminal Startup Prompt)
When starting the backend server (`python server.py`, `.\start.ps1`, or `./start.sh`):
1. The server checks your active Azure CLI session (`az account show`).
2. If not yet signed in, an interactive terminal prompt appears:
   ```text
   >>> AZURE CLI AUTHENTICATION SETUP <<<
   Azure CLI is not signed in yet. Would you like to authenticate now?
     [1] Interactive browser login ('az login')
     [2] Device code login ('az login --use-device-code')
     [3] Skip for now (continue to Studio UI & sign in from the web page)
   Select an option [1/2/3, default: 3]:
   ```
3. Selecting **`1`** launches standard interactive browser login on your local terminal.
4. Selecting **`2`** displays the Microsoft device code URL and verification code.
5. Selecting **`3`** continues startup so you can sign in anytime inside the web application.

#### Option B: Inside the App (Web Studio UI · Seamless Browser Login)
You can authenticate or switch Azure accounts directly inside the web interface without touching the terminal:
1. In the left sidebar under **System & Configuration**, click **Connections Settings** (or the **Sign in** button next to Azure CLI).
2. Click **`[Sign in with Azure CLI]`**:
   - The Studio automatically opens the official Microsoft authentication page (`https://login.microsoft.com/device`) in a new browser tab.
   - The unique verification code (e.g. `HSYGGFHLA`) is displayed on screen and automatically copied to your clipboard.
   - If your browser blocked popups, click the on-screen **`[Open Login Tab]`** button and **`[Copy Code]`**.
   - Paste the code in your Microsoft tab and sign in with your corporate Fabric account.
   - The Studio polls in the background and automatically updates to **`Signed in as user@domain.com`** upon completion!
3. Click **`Sign out`** anytime to clear cached bearer tokens and disconnect.

---

### 2. Claude Authentication: Dual Sign-In Options (Inside & Outside the App)

The platform supports two flexible ways to authenticate Claude Code:

#### Option A: Outside the App (Terminal Startup Prompt)
When starting the backend server (`python server.py`, `.\start.ps1`, or `./start.sh`):
1. The server performs a pre-flight authentication check.
2. If Claude is not yet authenticated, an interactive prompt appears directly in your terminal:
   ```text
   >>> CLAUDE AUTHENTICATION SETUP <<<
   Claude is not signed in yet. Would you like to authenticate now?
     [1] Sign in with Claude CLI browser login ('claude login')
     [2] Enter Anthropic API Key (sk-ant-...)
     [3] Skip for now (continue to Studio UI & sign in from the web page)
   Select an option [1/2/3, default: 3]:
   ```
3. Selecting **`1`** initiates the browser-based OAuth flow (`claude login`).
4. Selecting **`2`** lets you paste your `ANTHROPIC_API_KEY` (automatically stored into `.env` and activated).
5. Selecting **`3`** proceeds immediately so you can sign in anytime from the browser UI or test in Demo Mode.

#### Option B: Inside the App (Web Studio UI)
You can manage Claude authentication directly in the running web application without opening a terminal:
1. In the sidebar under **System & Configuration**, click **Connections Settings** (or the **Sign in** badge next to Claude Code).
2. Under the **Claude Code** card:
   - **Automatic Dynamic Detection**: The Studio dynamically locates the Claude CLI binary across your system PATH and global npm directories (`%APPDATA%\npm\claude.cmd`, `%LOCALAPPDATA%`, `/usr/local/bin`, etc.) without requiring server restarts.
   - **1-Click Installation**: If Claude CLI is not yet installed, click **`[Install Claude CLI]`** right on the card. The backend automatically installs `@anthropic-ai/claude-code` via npm and refreshes status.
   - **Sign in with Claude CLI**: Click **`[Sign in with Claude CLI]`** to launch interactive authentication in your browser. The Studio automatically detects sign-in completion.
   - **Direct Anthropic API Key**: Alternatively, paste your `ANTHROPIC_API_KEY` (`sk-ant-...`) and click **`[Save Key]`**. The backend securely saves it to `.env` and activates it in real-time.
   - **Connection Status & User Identity**: Displays `Connected & Ready`, along with the authenticated user's full name (e.g., `Nikhil Kumar Gupta`) and account email or masked API key (`sk-ant-...xxxx`).
   - **Sign Out**: Click **Sign out** anytime to revoke credentials or switch accounts.

---

## 🧭 Modern UI Architecture & Navigation

The Studio features a clean, high-performance interface optimized for developer workflows:

### 1. Decluttered Floating Controls
- **Zero-Clutter Header**: Removed legacy full-width header bars. Page views utilize maximum vertical screen real estate.
- **Top-Right Floating Actions**:
  - 🛑 **Stop Execution Button**: Displayed dynamically during active agent runs.
  - 🔔 **Notification Center**: Bell icon with real-time unread badge tracking background Fabric runs.
  - 💬 **Conversation Drawer Toggle**: Opens the Claude Execution Trace panel; shows unread step count.
  - 🧪 **Mockups / Live Engine Toggle**: One-click switch between simulated mockups and live cloud execution.
  - 🌙 / ☀️ **Theme Toggle**: Fast dark/light mode toggle with persistent local preference.

### 2. Sidenav & Universal Conversation Drawer
- **Sidebar Tabs**:
  - 🏠 **Home**: Executive overview, system health status, and quick-start actions.
  - 📁 **Projects**: Catalog of all workspace projects with status, search, and layer chips.
  - ⚡ **Studio**: Autonomous Medallion flow with progressive gate actions and in-studio project switching.
  - 📊 **Monitoring**: Full-featured tabular observability hub (replaced legacy Background Runs).
  - 🔀 **Orchestrator**: Direct view of Data Factory pipeline orchestration status.
  - 📐 **Semantic Model**: Direct Lake Power BI model status and DAX measures.
- **Collapsible Sidenav**: Click the collapse arrow (`←`) in the sidebar header to collapse down to icons on desktop; click the floating expand button (`→`) to restore.
- **Universal Conversation Drawer**: Starts **collapsed by default** to keep focus on engineering artifacts. When opened, it slides in smoothly across **all tabs** without reloading the page or truncating layouts.

### 3. Minimal Studio Header & In-Studio Project Switching
- **Compact Progress Header**: Replaced bulky cards with a minimal horizontal bar showing:
  - 📁 **Workspace Name**: Current Microsoft Fabric workspace badge.
  - 📂 **Project Switcher Dropdown**: Interactive project selector displaying the active project name. Clicking it opens a dropdown of all projects in the workspace (with status and % completion), allowing instant project switching or starting new projects directly from Studio!
  - 📈 **Medallion Completion**: Clean progress bar and percentage readout.

### 4. Tabular Monitoring Hub & Pagination
- Replaced card-based run views with a dense, searchable **Monitoring Table**:
  - Columns: **Project Name**, **Run ID** (with copy button and direct deep-link to Microsoft Fabric Monitor), **Item Type** (Notebook, Data Pipeline, Semantic Model), **Status** (Succeeded, In Progress, Failed, Cancelled), **Trigger Time**, and **Actions**.
  - **Filter Pills**: All, Succeeded, In Progress, Failed, Notebooks, Pipelines.
  - **Live Search**: Instant keyword search by Run ID, Project Name, or Item Name.
  - **Pagination**: 10 items per page with responsive previous/next navigation.

### 5. Notification Center & Real-Time Execution Toasts
- **Real-Time Notification Drawer**: Tracks background execution statuses of Notebooks, Data Pipelines, and Semantic Models.
- **Execution Toasts**: Interactive notifications appear at the bottom right upon job completion or failure, with a 1-click **"View in Monitoring"** button.
- **Notification Management**: Mark individual alerts as read, dismiss toasts, or clear all history.

---

## ⚙️ Configuration Reference (`.env`)

You can customize `.env` in the `claude-bridge` root:

```env
# 1. Standard 3-Repository Layout Paths (Defaults auto-resolve to siblings):
MCP_CLAUDE_DIR=../mcp-claude
FABRIC_MCP_DIR=../fabric-mcp-server

# 2. Network Binding (0.0.0.0 allows remote VM access)
HOST=0.0.0.0
PORT=8000

# 3. Tool Permission Mode (auto-approves tool execution while waiting on Medallion gates)
PERMISSION_MODE=bypassPermissions

# 4. Optional custom binary paths
# CLAUDE_BIN=/usr/local/bin/claude
# AZ_BIN=/usr/bin/az
```

---

## 🌐 Virtual Machine (VM) Cloud Networking Note

When deploying on an **Azure Virtual Machine** or **AWS EC2**:
1. In your cloud portal, navigate to your VM's **Network Security Group (NSG)**.
2. Add an **Inbound Port Rule**:
   - **Port**: `8000`
   - **Protocol**: `TCP`
   - **Action**: `Allow`
3. Access the Studio in your local browser at: `http://<YOUR_VM_PUBLIC_IP>:8000`.

---

## 🛠️ Verification & Troubleshooting Checklist

| Symptom | Cause | Solution |
|---|---|---|
| **Azure CLI Not Signed In** | `az login` expired or not run | Run `az login` (or `az login --use-device-code` on headless VMs), or click Sign in directly in the UI. |
| **Claude CLI Not Found in PATH** | npm global bin directory not in environment PATH | Click **[Install Claude CLI]** in the UI, or run `npm i -g @anthropic-ai/claude-code`. Alternatively, enter your Anthropic API Key directly. |
| **Demo Mode Active** | Claude CLI or Medallion skills not found | Verify Claude is authenticated and `mcp-claude/.claude/skills/medallion` exists. |
| **Page Reload Landing** | User refreshed browser window | By design, refreshing the page always returns to the **Home** view. Click **Studio** or **New Medallion Flow** to proceed. |
| **UI Not Built (503 error)** | `frontend/dist` is missing | Run `cd frontend && npm install && npm run build`. |
| **Missing Python packages** | Dependencies not installed in active environment | Run `pip install -r backend/requirements.txt`. |
| **Port 8000 in use** | Another service is using 8000 | Run with custom port: `PORT=8080 ./start.sh` or `.\start.ps1 -Port 8080`. |

---

## 🧪 Interactive Mockups Mode vs Live Engine Mode

To enable developers, stakeholders, and data engineers to test the complete Medallion lifecycle without active Microsoft Fabric workspaces or Claude credits, the Studio includes a built-in **Interactive Mockups Mode**.

### 1. Seamless Mode Switching
At the top right of the application header, a dedicated toggle button lets you switch modes instantly:
- **`🧪 Mockups Mode`** (Default): Simulates the full end-to-end project lifecycle with realistic PySpark Delta code, schemas, and live progress transitions.
- **`⚡ Live Engine`**: Direct execution connecting to local Claude CLI and Microsoft Fabric REST API / MCP server.

### 2. Testing "Start a New Project" End-to-End
1. In the Studio sidebar, click **Home** or **Studio**.
2. Click **Start a New Project** (or type `Start a new project` into the composer).
3. Follow the guided interactive flow through every architectural gate:
   - **Gate G2 & G2b**: Target directory & Lakehouse resolution, raw files inventory.
   - **Gate G4 & G5**: Spark profiling, schema inference, null/cardinality analysis.
   - **Gate G6 & G7 / G7a**: Bronze layer notebook generation, Delta Lake ingestion job run.
   - **Gate G8 & G9**: Silver business rules mapping, deduplication & data cleansing.
   - **Gate G10 & G10a**: Silver Delta notebook execution & validation.
   - **Gate G11 & G12 / G12b / G12c**: Gold dimensional modeling (Star Schema, STTM, Conformed Dimensions, Fact tables).
   - **Gate G13 & G13c**: Fabric Data Factory orchestration pipeline build & trigger.
   - **Gate G14 & G14b / G14c**: Direct Lake Semantic Model generation, relationships, DAX measures, and Power BI refresh.
   - **Gate G15**: Final Medallion Summary Dashboard with 100% completion metrics.
4. Each step presents interactive action chips (`[y/n]`, `[APPROVE/DECLINE]`, `[NEXT]`), allowing you to click directly or type responses.

