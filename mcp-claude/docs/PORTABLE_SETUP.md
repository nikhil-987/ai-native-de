# Portable Setup Guide: AI Native Data Engineering with Fabric MCP & Azure CLI

This guide explains how to set up and run the `mcp-claude` medallion skills on **any laptop or machine** (Windows, macOS, or Linux) using **VS Code** or **Google Antigravity**, paired with the official **Fabric MCP Server** and **Azure CLI (`az login`)**.

> [!NOTE]
> **No Client Secrets Required**: Authentication relies entirely on your interactive Azure user account via Azure CLI (`az login`). You do NOT need service principal client IDs or client secrets.

---

## Prerequisites

1. **AI Assistant IDE**:
   - [Google Antigravity](https://antigravity.google) or [VS Code](https://code.visualstudio.com/) with AI agent support.
2. **Microsoft Fabric & Azure Account**:
   - Access to a Fabric workspace with Contributor/Admin permissions.
3. **Azure CLI**:
   - Installed on your machine ([Azure CLI Installation Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)).

---

## Step 1: Clone the Repositories

In your target working directory on the laptop, clone both repositories:

```bash
# Clone the medallion skills repository
git clone https://github.com/your-org/mcp-claude.git

# Clone the official Microsoft Fabric MCP Server repository
git clone https://github.com/microsoft/fabric-mcp-server.git
```

---

## Step 2: Configure Environment Variables (Optional)

1. Navigate to the `mcp-claude` folder.
2. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

3. Open `.env` and set optional workspace or raw lakehouse parameters:

```env
# Microsoft Fabric Workspace Credentials (Optional if auto-resolving single workspace)
FABRIC_WORKSPACE_ID=your-workspace-guid-or-name

# Default Raw Lakehouse Configuration
RAW_LAKEHOUSE_NAME=
SOURCE_TIMEZONE=Asia/Kolkata
```

---

## Step 3: Open in Antigravity or VS Code

Open the `mcp-claude` folder in Antigravity or VS Code:

- **Antigravity**: `File` -> `Open Folder...` -> Select `mcp-claude`.
- **VS Code**: `code mcp-claude`

Ensure the Fabric MCP Server tools (`onelake_*`, `datafactory_*`, `core_*`) are enabled in your MCP configuration.

---

## Step 4: Run the Medallion Execution Flow

In the AI chat interface (Antigravity or VS Code), start the execution flow by typing:

```text
START
```

### Execution & Authentication Flow:

1. **Welcome Message & Connectivity Check (G0)**:
   - Displays:
     ```text
     Welcome to AI Native Data Engineering
     ```
   - Simultaneously checks active Fabric connectivity using Azure CLI account status (`az account show`).
   - **If connection IS active**: Proceeds directly to G0b (Workspace Selection).
   - **If connection is NOT active**: Asks **G0a**:
     ```text
     Fabric workspace connection is not active. Would you like to authenticate using Azure CLI (`az login`)? [y/n]
     ```

2. **Azure CLI Login (G0a)**:
   - If you reply `y`: Prompts/executes `az login` to authenticate interactively in your browser. Upon successful authentication, re-checks connectivity and proceeds to G0b.
   - If you reply `n`: Outputs *"Fabric workspace connection is not active. Thank you!"* and stops execution.

3. **Workspace Listing & Selection (G0b)**:
   - Connects at tenant level using `onelake_list-workspaces` and lists all accessible workspaces:
     ```text
     Select Workspace: press 1 for Insurance_Analytics_WS, 2 for Production_Medallion_WS or S to stop [1/2/S]
     ```
   - If you enter a workspace number/name: AI confirms selected workspace (*"Selected workspace: Insurance_Analytics_WS."*) and asks G1.
   - If you reply `S` (stop): AI outputs *"Thank you!"* and stops execution.

4. **Listing & Selecting Source Lakehouse (G1)**:
   - Asks: *"Should I list the lakehouses in Insurance_Analytics_WS? [y/n]"*. User replies `y`.
   - Lists lakehouses (`1. Landing_Raw_LH, 2. External_Ingest_LH`). User selects `1` (`Landing_Raw_LH`).

5. **Selecting Project Action (G1a)**:
   - Asks: *"Select Action: press 1 to Start a new project, 2 to Resume an existing project, 3 to Stop [1/2/3]"*.
   - If `1` (Start new project): Lists raw LOB folders in `Landing_Raw_LH`. User selects `1` (`Automobile`).
   - If `2` (Resume existing project): Performs 2-tier project discovery (root lakehouses and workspace folders for `dbo.project_status`), displays structured Project Stage Summary (Stage: `current_project_stage`, Status: `overall_project_status`, Gate: `current_gate`, Next Action: `next_action_required`, Completion: `completion_percentage` %), and prompts directly at `current_gate`.

6. **Target Folder Resolution & Directory Creation Gate (G2)**:
   - AI prompts for Target Folder Name:
     ```text
     Target Resolution: Enter or confirm target folder name (Suggested: Automobile): [y/n/<target_folder_name>]
     ```
   - If `y` or `<target_folder_name>`: AI creates target folder `Automobile` containing directly `Automobile_LH`, `notebooks`, `orchestrator`, `semantic model`. Creation of Target Lakehouse `Automobile_LH` is deferred until notebook or orchestrator execution.
   - If `n`: AI outputs *"Thank you!"* and stops.

7. **Show File Details Gate (G2b)**:
   - Asks: *"Target folder Automobile created (Target Lakehouse Automobile_LH will be created on notebook/orchestrator execution). Show details of the files in folder Automobile of Source Lakehouse Landing_Raw_LH? [y/n]"*.
   - If `y`: AI lists file details (sizes, paths, target table mappings) and proceeds to G4 (Profiling).
   - If `n`: AI outputs *"Thank you!"* and stops.

8. **Proceed through Gates (G4–G15)**:
   - Each gate explicitly asks confirmation; declining outputs *"Thank you!"* and stops. Target Lakehouses created are tracked as Project Directories for the "Resume an existing project" flow.
   - **Asynchronous Background Execution & Post-Submission Choices (G7a, G10a, G12c, G13c, G14c)**:
     - At any run gate, replying `y` submits the execution job asynchronously to Fabric in the background and returns a `<run_id>`.
     - The AI immediately presents 3 post-submission options:
       ```text
       Select action: press 1 to Move to next stage immediately, 2 to Poll background execution status, 3 to Stop chat session [1/2/3]
       ```
       - **Option 1 (Move to next stage)**: Proceeds directly to the next phase (or handoff) without waiting for background completion.
       - **Option 2 (Poll status)**: Periodically checks Fabric API for job completion, then proceeds to the next stage upon success.
       - **Option 3 (Stop chat session)**: Cleanly terminates the active chat session with *"Thank you! Chat session stopped cleanly."*
         > [!IMPORTANT]
         > **Background Job Persistence**: Selecting Option `3` stops the chat interface session, but **does NOT cancel or stop the background Fabric job**. The execution job continues running independently in OneLake / Data Factory to completion, recording its final status in `dbo.project_status`.
     - **`skip` Token**: Replying `skip` at any run gate bypasses job submission entirely and moves directly to the next stage.
   - **Clean Notebook Generation Standards**: Generated PySpark notebooks automatically incorporate all engine-level safety guardrails (date rebase policies, regex parsing, Livy error logging) from `failure_registry.md`, but emit clean enterprise code comments rather than raw internal `FL-NNN` tracking tags.
