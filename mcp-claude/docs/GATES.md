# Medallion Gates — Reference

The medallion skill builds Bronze → Silver → Gold → Orchestrator → Semantic Model for any dataset at a time in Microsoft Fabric. It runs as a conversation with **gates**. At each gate the flow stops until you reply.

Source of truth: [`.claude/skills/medallion/interface.md`](../.claude/skills/medallion/interface.md) (wording and flow) and [`SKILL.md`](../.claude/skills/medallion/SKILL.md) (the work behind each gate). If this page and those files disagree, those files win.

---

## How gates work

| Rule | Detail |
|---|---|
| One gate per turn | The flow asks one question and waits. Silence, questions or free text are never taken as consent. |
| Short replies only | Accepted tokens: `y`/`n`, choice numbers, `APPROVE`/`DECLINE`, `UPLOAD`/`SKIP`, or custom write-in target name at G2. Anything else gets *"Please reply with one of: …"* and the gate is repeated. |
| Issues loop | `DECLINE` (or `n` at a review gate) always asks *"What issues did you find?"*. The fix is shown as a diff and the **same** gate is asked again, until `APPROVE`. |
| Execution & Failure loop | On `y` to run prompt: submit item asynchronously in background, return `<run_id>`, and prompt post-submission choices `[1/2/3]` (1 Move to next stage, 2 Poll status, 3 Stop chat session cleanly while job runs independently in Fabric). On failure: read log, match failure registry, prompt *"Execution failed due to <error>. Generate updated version with fix? [y/n]"*. |
| Zero-Config Dynamic Resolution | Target names (`{target}`), workspaces, lakehouses, schemas, notebook names (`Bronze_<Target>`, `Silver_<Target>`, `Gold_<Target>`, `Refresh_Semantic_Model`), pipelines (`<Target>_Medallion_Orchestrator`), and semantic models (`<Target>_Gold_Model`) are resolved dynamically at runtime without requiring static configuration files. |
| Restart | Typing `START` at any point restarts from G0. Items already created in Fabric are kept. |

### Gate types

| Type | Accepts |
|---|---|
| Yes/No | `y` · `n` |
| Run Prompt | `y` (yes) · `n` (no) · `skip` (s - skip running now and move directly to next stage) |
| Target Name | `y` · `n` · `<Custom_Name>` (custom target name string) |
| Choice | `1` · `2` · … (only numbers shown) |
| Approval | `APPROVE` · `DECLINE` |
| Upload | `UPLOAD` + file or path · `SKIP` |

---

## Gate list

| Gate | Stage | Question | Type | What happens |
|---|---|---|---|---|
| **G0** | Start | *(user types `START`)* | — | Shows welcome message, checks Fabric connection (proceeds to G0b if active, asks G0a if inactive). |
| **G0a** | Start | Fabric workspace connection is not active. Would you like to authenticate using Azure CLI (`az login`)? | Yes/No | `y` prompts/executes `az login` to authenticate; `n` stops with thank you message. |
| **G0b** | Setup | Select Workspace: press 1 for ..., 2 for ... or S to stop | Choice | Lists tenant-level workspaces. User selects workspace (proceeds to G1a); `S` stops with thank you message. |
| **G1a** | Setup | Select Action: press 1 to Start a new project, 2 to Resume an existing project, 3 to Stop | Choice | `1` asks G1 to select Source Lakehouse; `2` lists discovered projects (checking root lakehouses and workspace folders for `dbo.project_status`), displays structured Project Stage Summary (Stage: `current_project_stage`, Status: `overall_project_status`, Gate: `current_gate`, Next Action: `next_action_required`, Completion: `completion_percentage` %), and prompts to resume at `current_gate`; `3` stops with thank you message. |
| **G1** | Setup | Should I list the lakehouses in {workspace}? | Yes/No | `y` lists lakehouses, prompts user to select Source Lakehouse `{raw_lakehouse}`, and lists raw folders (proceeds to G2); `n` stops with thank you message. |
| **G2** | Setup | Target Resolution: Enter or confirm target folder name (Suggested: <Derived_Name>): [y/n/<target_folder_name>] | Target Folder | `y` accepts derived name; `<target_folder_name>` sets custom name. Creates target folder `<target_folder_name>` containing directly `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`. Target Lakehouse creation is deferred until notebook/orchestrator execution. `n` stops. |
| **G2b** | Setup | Target folder {target_folder_name} created (Target Lakehouse {target_folder_name}_LH will be created on execution). Show details of the files in folder <folder>? | Yes/No | `y` lists file details (sizes, paths, mappings - table names match raw source file stem); `n` stops with thank you message. |
| **G4** | Profile | Run data profiling on <Target> raw tables? | Yes/No | Read-only profiling: types, nulls, distinct counts, candidate keys, date formats, encodings. `n` stops with thank you message. |
| **G5** | Profile | Are you satisfied with the data profile? | Approval | `APPROVE` marks Profile ✔ and holds profiling attributes in memory. |
| **G6** | Bronze | Generate Bronze notebook for <Target> into schema `{bronze_schema}`? | Yes/No | Generates `Bronze_<Target>` (table names match raw file stem); `n` stops with thank you message. |
| **G7** | Bronze | DE review – approve Bronze notebook? | Approval | Deploys `Bronze_<Target>` in Fabric. Proceeds to G7a. |
| **G7a** | Bronze | Run Bronze notebook now? | Run Prompt | `y` submits `Bronze_<Target>` to Fabric asynchronously in background -> prompts `[1/2/3]` (1 move to next stage, 2 poll status, 3 stop chat session); `skip` moves directly to G8; `n` stops. |
| **G8** | Silver | Upload business rules for Silver | Upload | `UPLOAD` parses rules, outputs structured **Understanding Summary** of business rules (proceeds to G9); `SKIP` stops with thank you message. |
| **G9** | Silver | Generate Silver notebook for <Target>? | Yes/No | Generates `Silver_<Target>` notebook (table names match raw file stem); `n` stops with thank you message. |
| **G10** | Silver | DE review – approve Silver notebook? | Approval | Deploys `Silver_<Target>` in Fabric. Proceeds to G10a. |
| **G10a** | Silver | Run Silver notebook now? | Run Prompt | `y` submits `Silver_<Target>` to Fabric asynchronously in background -> prompts `[1/2/3]` (1 move to next stage, 2 poll status, 3 stop chat session); `skip` moves directly to G11; `n` stops. |
| **G11** | Gold | Upload client-style STTM document for Gold modeling | Upload | `UPLOAD` parses STTM document, outputs structured **Understanding Summary** of STTM entities/measures/keys (proceeds to G12); `SKIP` stops with thank you message. |
| **G12** | Gold | Approve the Gold model and generate Gold notebook? | Approval | Marks `gold_model.yaml` `APPROVED` and generates `Gold_<Target>` notebook; `DECLINE` runs issues loop. |
| **G12b** | Gold | DE review – approve Gold notebook? | Approval | Deploys `Gold_<Target>` in Fabric. Proceeds to G12c. |
| **G12c** | Gold | Run Gold notebook now? | Run Prompt | `y` submits `Gold_<Target>` to Fabric asynchronously in background -> prompts `[1/2/3]` (1 move to next stage, 2 poll status, 3 stop chat session); `skip` moves directly to G13; `n` stops. |
| **G13** | Orchestrator | Create the orchestrator pipeline (<Target>_Medallion_Orchestrator)? | Yes/No | `y` asks G13a/G13b, creates and deploys Data Factory orchestrator pipeline `<Target>_Medallion_Orchestrator`; `n` stops with thank you message. |
| **G13a** | Orchestrator | Source Lakehouse? | Choice | Selects raw lakehouse. |
| **G13b** | Orchestrator | Target Lakehouse? | Choice | Selects target lakehouse holding bronze/silver/gold schemas. |
| **G13c** | Orchestrator | Run orchestrator now? | Run Prompt | `y` submits orchestrator pipeline to Fabric asynchronously in background -> prompts `[1/2/3]` (1 move to next stage, 2 poll status, 3 stop chat session); `skip` moves directly to G14; `n` stops. |
| **G14** | Semantic | Generate Direct Lake semantic model on <Target> Gold? | Yes/No | Builds Direct Lake semantic model `<Target>_Gold_Model` definition from Gold tables; `n` stops with thank you message. |
| **G14b** | Semantic | Approve semantic model? | Approval | Deploys `<Target>_Gold_Model` in Fabric. Proceeds to G14c. |
| **G14c** | Semantic | Refresh semantic model dataset now? | Run Prompt | `y` submits dataset refresh to Fabric asynchronously in background -> prompts `[1/2/3]` (1 move to next stage, 2 poll status, 3 stop chat session); `skip` moves directly to G15; `n` stops. |
| **G15** | Close | Process another dataset? | Yes/No | Shows Medallion summary table and created items. `y` resets to G2; `n` stops with thank you message. |

