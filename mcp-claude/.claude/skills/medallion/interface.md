# Interface — the gated conversation

This file is the medallion skill's conversation script. It decides **what is asked and when**. `SKILL.md` and the method files decide **how the work is done**. `client_config.md` holds global configuration patterns. All dataset and target names are resolved dynamically at runtime without static config files.

The user mostly answers with a short token: `y`/`n`/`skip`, a number, `APPROVE`/`DECLINE` or `UPLOAD`/`SKIP`. At Gate G2, the user may also write in a custom target name. The flow never advances on anything else.

---

## Global rules — apply at every gate

1. **One gate per turn.** Ask one gate, then STOP and wait for the reply. Never run two gates in one turn. Never answer a gate on the user's behalf. Never treat silence, a question or free text as consent.
   A turn may carry the *output* of the gate just answered, followed by the *next* gate. That is still one question.
2. **Valid replies only.** Matching ignores case and surrounding whitespace.

   | Gate type | Accepts |
   |---|---|
   | Yes/No | `y` · `n` |
   | Run Prompt | `y` (yes) · `n` (no) · `skip` (s - skip running and move to next stage) |
   | Target Name | `y` · `n` · `<Custom_Name>` (custom target name string) |
   | Choice | `1` · `2` · … (only numbers that are on the list shown) |
   | Approval | `APPROVE` · `DECLINE` |
   | Upload | `UPLOAD` followed by an attached file or a path · `SKIP` |

   On anything else, reply with one line, *"Please reply with one of: <options>"*, then repeat the gate exactly. Do not guess what was meant, and do not act on free text. `UPLOAD` without a file or path gets *"Attach the file or give its path."* and the gate stays open.
3. **Every gate ends with its options in brackets:** `[y/n]`, `[y/n/skip]`, `[1/2/3]`, `[APPROVE/DECLINE]`, `[UPLOAD/SKIP]`, `[y/n/<Custom_Name>]`.
4. **The issues loop.** A `DECLINE` at any gate, or an `n` at a review gate, always gets this exact question:

   > What issues did you find? (describe, or reference table/column/cell)

   That question is free-text and is the only place free text is expected. Then: fix the issues, show **what changed** (a diff, or a before/after table), and repeat the **same** gate. Loop until `APPROVE`. Never move on after a `DECLINE`.
5. **Asynchronous Background Execution Protocol (`[y/n/skip]`).**
   - On `y` (or `yes`) at any run prompt: Submit item asynchronously to Fabric in the background and receive `<run_id>`. Immediately respond with:
     > Execution of <Item> submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]
     - **`1` (Move to next stage)**: Background job continues running in Fabric to completion (recording status in `dbo.project_status`). Proceed immediately to the next stage gate.
     - **`2` (Poll background status)**: Perform a non-blocking check on Fabric API for job completion.
       - On success: Output completion status and duration -> proceed seamlessly to the next stage.
       - On failure: Read error log, match failure registry (`failure_registry.md`), and prompt *"Execution failed due to <error>. Generate updated version with fix? [y/n]"*. `y` regenerates fix -> DE approval -> deployment -> run prompt. `n` outputs thank-you message and stops chat session.
     - **`3` (Stop)**: Outputs *"Thank you! Chat session stopped cleanly."* and stops the chat conversation session. **Crucially, it does NOT cancel or stop the background Fabric job**; the job continues executing independently in Fabric to completion, and its outcome is recorded in `dbo.project_status`.
   - On `skip` (or `s`) at any run prompt: Output *"Execution skipped as requested. Moving directly to the next stage."* and proceed seamlessly to the next stage gate.
   - On `n` (or `no`) at any gate or `SKIP` at upload gates: Output *"Thank you!"* and stop chat session cleanly.
6. **Zero-Config Dynamic Resolution.** All target folder names (`{target_folder_name}` / `{target}`), workspaces, raw lakehouses, target lakehouses (`<Target>_LH`), schemas, notebook names (`Bronze_<Target>`, `Silver_<Target>`, `Gold_<Target>`, `Refresh_Semantic_Model`), pipelines (`<Target>_Medallion_Orchestrator`), and semantic models (`<Target>_Gold_Model`) are resolved dynamically at runtime without requiring static configuration files.

### Conventions used below

- `<Target>` is the capitalized resolved dataset/target name (e.g. `Marine`, `Automobile`, `Customer360`). `{target}` and `{target_folder_name}` refer to its target directory name.
- `{bronze_schema}`, `{silver_schema}`, `{gold_schema}`, `{lakehouse}`, `{raw_lakehouse}` are resolved dynamically from `client_config.md` for the chosen target. Always show the resolved value, never the placeholder.
- **Silent work.** Listing, resolving ids and reading files that a gate needs are done without asking. Creating the target folder `<target_folder_name>` (containing directly `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`) is done at G2. Creation of the Target Lakehouse item `<target_folder_name>_LH` in Fabric is deferred until a notebook or orchestrator pipeline is executed. Creating or updating a notebook, pipeline or semantic model **always** waits for its approval gate.

---

## The gates

### G0 — Start & Fabric Connection Check

Trigger: the user types `START`.

1. Display the welcome message:

   > Welcome to AI Native Data Engineering

2. Simultaneously check if the Fabric workspace connection is active:
   - Check Azure CLI account status (`az account show`) or token / identity check via Fabric MCP Server (`onelake_list-workspaces`).

3. Connectivity outcome:
   - **If Fabric workspace connection IS active**: Proceed to G0b in the same turn.
   - **If Fabric workspace connection is NOT active**: Ask G0a in the same turn:
     > Fabric workspace connection is not active. Would you like to authenticate using Azure CLI (`az login`)? [y/n]

### G0a — Azure CLI Authentication

> Fabric workspace connection is not active. Would you like to authenticate using Azure CLI (`az login`)? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Initiate Azure CLI login (`az login`). Upon completion, re-check Fabric workspace connection. If active, proceed to G0b. If failed, output *"Authentication failed. Thank you!"* and stop. | G0b (if active) / **STOP** (if failed) |
| `n` | Output *"Fabric workspace connection is not active. Thank you!"* and stop execution. | **STOP** |

### G0b — List & Select Workspace

Connect at the tenant level via Fabric MCP Server (`onelake_list-workspaces`) to fetch the names of all accessible workspaces. Display the workspace names numbered `1.`, `2.`, … alongside an option `S` to stop:

> Select Workspace: press 1 for <Workspace_1>, 2 for <Workspace_2> or S to stop [1/2/.../S]

| Reply | Do | Next |
|---|---|---|
| a listed workspace number or workspace name | Set `{workspace}` to the selected workspace. Confirm in one line: *"Selected workspace: {workspace}."* and ask G1a in the same turn. | G1a |
| `S` (or `stop`) | Output *"Thank you!"* and stop execution. | **STOP** |

### G1a — Select Project Action (Asked Immediately After Workspace Selection)

> Select Action: press 1 to Start a new project, 2 to Resume an existing project, 3 to Stop [1/2/3]

| Reply | Do | Next |
|---|---|---|
| `1` (Start a new project) | Ask G1 to offer and select Source Lakehouse `{raw_lakehouse}` in `{workspace}`. | G1 |
| `2` (Resume an existing project) | Perform 2-tier project discovery in `{workspace}`: (1) check standalone lakehouses at workspace root for table `dbo.project_status` (Standalone Lakehouse Projects), (2) check workspace folders (`<target_folder_name>`) for a lakehouse containing `dbo.project_status` (Project Folders). Display discovered projects for user selection. User selects a project. AI inspects `dbo.project_status`, displays structured Project Stage Summary table (Stage: `current_project_stage`, Status: `overall_project_status`, Gate: `current_gate`, Next Action: `next_action_required`, Completion: `completion_percentage` %), and prompts directly at `G-pending` (`current_gate`). If no project contains `dbo.project_status`, inform user and transition to G1. | G-pending |
| `3` (Stop) | Output *"Thank you!"* and stop execution. | **STOP** |

### G1 — Offer & Select Source Lakehouse

> Should I list the lakehouses in {workspace}? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | List the lakehouses present in `{workspace}` using Fabric MCP Server (`onelake_list-items`). Prompt user to select Source Lakehouse: *"Select Source Lakehouse: press 1 for <Lakehouse_1>, 2 for <Lakehouse_2> [1/2]"*. Set `{raw_lakehouse}` to selected lakehouse. Connect to `{raw_lakehouse}` using Fabric MCP Server (`onelake_list-files`) and list all available raw data folders under `Files/` (e.g. `1. Automobile`, `2. Marine`, `3. Home`, `4. Customer360`). Prompt user: *"Select Raw Data Folder / Dataset: press 1 for Automobile, 2 for Marine [1/2]"*. | G2 |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G2 — Dynamic Target Folder Name & Target Directory Resolution Gate

After user selects a raw data folder from Source Lakehouse `{raw_lakehouse}`:

1. AI automatically derives suggested Target Folder Name `<Derived_Name>` from the raw folder stem.
2. AI resolves Target Lakehouse name as `<Target>_LH` (e.g. `Marine_LH`). The Target Lakehouse item is **NOT** created upfront at G2; its creation is deferred until notebook or orchestrator execution.
3. Upon folder confirmation, AI creates target folder `<target_folder_name>` in workspace `{workspace}` containing directly: `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`.

> Target Resolution: Enter or confirm target folder name (Suggested: <Derived_Name>): [y/n/<target_folder_name>]

| Reply | Do | Next |
|---|---|---|
| `y` | Set `{target_folder_name}` and `{target}` to `<Derived_Name>`. Create target folder `<Derived_Name>` in workspace `{workspace}` containing directly `<Derived_Name>_LH`, `notebooks`, `orchestrator`, `semantic model`. Confirm: *"Target folder <Derived_Name> created (Target Lakehouse <Derived_Name>_LH will be created on notebook/orchestrator execution)."* | G2b |
| `<target_folder_name>` (e.g. `Marine_Claims_V2`) | Set `{target_folder_name}` and `{target}` to `<target_folder_name>`. Create target folder `<target_folder_name>` in workspace `{workspace}` containing directly `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`. Confirm: *"Target folder <target_folder_name> created (Target Lakehouse <target_folder_name>_LH will be created on notebook/orchestrator execution)."* | G2b |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G2b — Show File Details Confirmation Gate

> Target folder {target_folder_name} created (Target Lakehouse {target_folder_name}_LH will be created on notebook/orchestrator execution). Show details of the files in folder <folder> of Source Lakehouse {raw_lakehouse}? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | List and display file details (file names, sizes, partition paths, and target table mappings - table names match source file stem) for folder `<folder>` in Source Lakehouse `{raw_lakehouse}`. | G4 |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G4 — Data Profiling

> Run data profiling on <Target> raw tables? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Run read-only profiling (types, nulls, distinct counts, candidate keys, date formats, encodings). Profiling results are stored dynamically in memory for notebook generation. | G5 |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G5 — Approve the Profile

> Are you satisfied with the data profile? [APPROVE/DECLINE]

- `APPROVE`: Mark Profile `✔` and proceed to G6.
- `DECLINE`: Run issues loop. Re-profile with correction.

### G6 — Generate Bronze Notebook

> Generate Bronze notebook for <Target> into schema `{bronze_schema}`? [y/n]

- `y`: Generate `Bronze_<Target>` with raw file stem table naming, show notebook code summary, ask G7.
- `n`: Output *"Thank you!"* and stop execution.

### G7 — DE Approves Bronze Notebook

> DE review – approve Bronze notebook? [APPROVE/DECLINE]

- `APPROVE`: Create or update (deploy) `Bronze_<Target>` in Fabric. Show *"The Bronze notebook `Bronze_<Target>` is deployed to Fabric."* Ask G7a.
- `DECLINE`: Run issues loop, fix notebook, repeat G7.

### G7a — Run Bronze Notebook Execution Gate

> Run Bronze notebook now? [y/n/skip]

| Reply | Do | Next |
|---|---|---|
| `y` (or `yes`) | Submit `Bronze_<Target>` to Fabric asynchronously in background, receive `<run_id>`. Respond: *"Execution of Bronze_<Target> submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]"*. `1` proceeds to G8 (job continues running in Fabric). `2` checks job status (success -> G8; failure -> recovery prompt). `3` stops chat session cleanly while job runs independently in Fabric. | Post-submission `[1/2/3]` |
| `skip` (or `s`) | Output *"Bronze notebook execution skipped as requested. Moving directly to Silver layer."* Proceed to G8. | G8 |
| `n` (or `no`) | Output *"Thank you! Artifact deployed to Fabric. Execution skipped as requested."* and stop execution. | **STOP** |

### G8 — Upload Silver Business Rules Gate

> Upload business rules for Silver [UPLOAD/SKIP]

| Reply | Do | Next |
|---|---|---|
| `UPLOAD <file>` | Parse business rules document, output a structured **"Understanding of Uploaded Business Rules"** summary (rule IDs, target columns, transformation logic, and 5-level precedence mapping). Ask G9 in the same turn. | G9 |
| `SKIP` | Output *"Thank you!"* and stop execution. | **STOP** |

### G9 — Generate Silver Notebook

> Generate Silver notebook for <Target>? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Generate `Silver_<Target>` notebook (tables matched to Bronze/raw filenames, rules applied). Show rules matrix & notebook code. Ask G10. | G10 |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G10 — DE Approves Silver Notebook

> DE review – approve Silver notebook? [APPROVE/DECLINE]

- `APPROVE`: Create or update (deploy) `Silver_<Target>` in Fabric. Show *"The Silver notebook `Silver_<Target>` is deployed to Fabric."* Ask G10a.
- `DECLINE`: Run issues loop, fix notebook, repeat G10.

### G10a — Run Silver Notebook Execution Gate

> Run Silver notebook now? [y/n/skip]

| Reply | Do | Next |
|---|---|---|
| `y` (or `yes`) | Submit `Silver_<Target>` to Fabric asynchronously in background, receive `<run_id>`. Respond: *"Execution of Silver_<Target> submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]"*. `1` proceeds to G11 (job continues running in Fabric). `2` checks job status (success -> G11; failure -> recovery prompt). `3` stops chat session cleanly while job runs independently in Fabric. | Post-submission `[1/2/3]` |
| `skip` (or `s`) | Output *"Silver notebook execution skipped as requested. Moving directly to Gold layer."* Proceed to G11. | G11 |
| `n` (or `no`) | Output *"Thank you! Artifact deployed to Fabric. Execution skipped as requested."* and stop execution. | **STOP** |

### G11 — Upload Client-Style STTM Gate (Gold Layer)

> Upload client-style STTM (Source-to-Target Mapping) document for Gold modeling [UPLOAD/SKIP]

| Reply | Do | Next |
|---|---|---|
| `UPLOAD <file>` | Parse STTM document, output a structured **"Understanding of Uploaded STTM Document"** summary (derived star-schema Dimensions/Facts, SHA-256 surrogate keys, business measures/formulas, and joins). Ask G12 in the same turn. | G12 |
| `SKIP` | Output *"Thank you!"* and stop execution. | **STOP** |

### G12 — Approve Gold Model & Generate Notebook

> Approve the Gold model and generate Gold notebook? [APPROVE/DECLINE]

- `APPROVE`: Write `gold_model.yaml`, generate `Gold_<Target>` notebook using STTM mappings, ask G12b.
- `DECLINE`: Run issues loop on model, repeat G12.

### G12b — DE Review of Gold Notebook

> DE review – approve Gold notebook? [APPROVE/DECLINE]

- `APPROVE`: Create or update (deploy) `Gold_<Target>` in Fabric. Show *"The Gold notebook `Gold_<Target>` is deployed to Fabric."* Ask G12c.
- `DECLINE`: Run issues loop, fix notebook, repeat G12b.

### G12c — Run Gold Notebook Execution Gate

> Run Gold notebook now? [y/n/skip]

| Reply | Do | Next |
|---|---|---|
| `y` (or `yes`) | Submit `Gold_<Target>` to Fabric asynchronously in background, receive `<run_id>`. Respond: *"Execution of Gold_<Target> submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]"*. `1` proceeds to G13 (job continues running in Fabric). `2` checks job status (success -> G13; failure -> recovery prompt). `3` stops chat session cleanly while job runs independently in Fabric. | Post-submission `[1/2/3]` |
| `skip` (or `s`) | Output *"Gold notebook execution skipped as requested. Moving directly to Orchestrator stage."* Proceed to G13. | G13 |
| `n` (or `no`) | Output *"Thank you! Artifact deployed to Fabric. Execution skipped as requested."* and stop execution. | **STOP** |

### G13 — Fabric Orchestrator Pipeline Creation Gate

> Create the orchestrator pipeline (<Target>_Medallion_Orchestrator)? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Ask G13a and G13b to confirm Source & Target Lakehouses. Construct Data Factory pipeline connecting `Bronze_<Target>` -> `Silver_<Target>` -> `Gold_<Target>` -> `Refresh_Semantic_Model`. Deploy pipeline `<Target>_Medallion_Orchestrator` to Fabric. Show *"The Fabric Orchestrator Pipeline `<Target>_Medallion_Orchestrator` is deployed to Fabric."* Ask G13c. | G13a / G13b -> G13c |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

**G13a — Select Source Lakehouse for Pipeline**
> Source Lakehouse? (pick number from list) [1/2/…]

**G13b — Select Target Lakehouse for Pipeline**
> Target Lakehouse? (pick number from list) [1/2/…]

### G13c — Run Fabric Orchestrator Pipeline Gate

> Run orchestrator now? [y/n/skip]

| Reply | Do | Next |
|---|---|---|
| `y` (or `yes`) | Submit pipeline `<Target>_Medallion_Orchestrator` to Fabric asynchronously in background, receive `<run_id>`. Respond: *"Execution of Orchestrator Pipeline submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]"*. `1` proceeds to G14 (job continues running in Fabric). `2` checks job status (success -> G14; failure -> recovery prompt). `3` stops chat session cleanly while job runs independently in Fabric. | Post-submission `[1/2/3]` |
| `skip` (or `s`) | Output *"Orchestrator pipeline execution skipped as requested. Moving directly to Semantic Model stage."* Proceed to G14. | G14 |
| `n` (or `no`) | Output *"Thank you! Artifact deployed to Fabric. Execution skipped as requested."* and stop execution. | **STOP** |

### G14 — Direct Lake Semantic Model Creation Gate

> Generate Direct Lake semantic model on <Target> Gold? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Build Direct Lake semantic model `<Target>_Gold_Model` definition from Gold tables. Ask G14b. | G14b |
| `n` | Output *"Thank you!"* and stop execution. | **STOP** |

### G14b — Approve & Deploy Direct Lake Semantic Model

> Approve semantic model? [APPROVE/DECLINE]

- `APPROVE`: Create or update (deploy) `<Target>_Gold_Model` in Fabric workspace. Show *"The Direct Lake Semantic Model `<Target>_Gold_Model` is deployed to Fabric."* Ask G14c.
- `DECLINE`: Run issues loop, fix definition, repeat G14b.

### G14c — Refresh Semantic Model Dataset Gate

> Refresh semantic model dataset now? [y/n/skip]

| Reply | Do | Next |
|---|---|---|
| `y` (or `yes`) | Submit dataset refresh for `<Target>_Gold_Model` to Fabric asynchronously in background, receive `<run_id>`. Respond: *"Dataset refresh for <Target>_Gold_Model submitted to Fabric in the background (Run ID: <run_id>). Press 1 to Move to next stage, 2 to Poll background execution status, 3 to Stop [1/2/3]"*. `1` proceeds to G15 (refresh continues in Fabric). `2` checks status (success -> G15; failure -> recovery prompt). `3` stops chat session cleanly while refresh runs independently in Fabric. | Post-submission `[1/2/3]` |
| `skip` (or `s`) | Output *"Semantic model dataset refresh skipped as requested. Proceeding to Session Close."* Proceed to G15. | G15 |
| `n` (or `no`) | Output *"Thank you! Artifact deployed to Fabric. Execution skipped as requested."* and stop execution. | **STOP** |

### G15 — Close & Summary

Show the Target Medallion Summary:

| Layer | Schema | Table | Rows | Status |
|---|---|---|---|---|
| Bronze | `{bronze_schema}` | `<Source_Stem>` | `<Count>` | `✔ Deployed & Executed` |
| Silver | `{silver_schema}` | `<Source_Stem>` | `<Count>` | `✔ Deployed & Executed` |
| Gold | `{gold_schema}` | `<Client_STTM_Table>` | `<Count>` | `✔ Deployed & Executed` |

Show created items:
- Notebooks: `Bronze_<Target>`, `Silver_<Target>`, `Gold_<Target>`, `Refresh_Semantic_Model`
- Pipeline: `<Target>_Medallion_Orchestrator`
- Semantic Model: `<Target>_Gold_Model`

Then ask:

> Process another dataset? [y/n]

| Reply | Do | Next |
|---|---|---|
| `y` | Return to G2. | G2 |
| `n` | Output *"Session closed for <Target>. Thank you!"* and stop execution. | **STOP** |
