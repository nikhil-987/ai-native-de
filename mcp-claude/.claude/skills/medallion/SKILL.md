---
name: medallion
description: Gated, approval-driven Medallion builder for Microsoft Fabric. Use when the user types START, or asks to profile raw data or to build a bronze, silver or gold layer, a semantic model or an orchestrator for any dataset folder. Runs a step-by-step chat defined in interface.md. Each gate accepts only y/n/skip, target write-in, a number, APPROVE/DECLINE or UPLOAD/SKIP. The flow is: select workspace, select project action (start new/resume/stop), select source lakehouse, target dataset name, profile raw tables live, then generate and deploy Bronze, Silver, Gold, Orchestrator, and Semantic Model, requesting DE approval for each layer.
---
# Fabric Medallion Builder

Builds Bronze → Silver → Gold → Orchestrator → Semantic Model for any dataset at a time in Microsoft Fabric, through a gated conversation.

**Nothing in this skill is hardcoded to a client, a dataset, a lakehouse or a GUID.** Every name is resolved at runtime from `client_config.md` and live Fabric listings. The same zero-config flow serves every dataset domain.

## How this skill runs

1. **Read [`.env`](../../.env) & [`client_config.md`](client_config.md).** Holds environment variables (`FABRIC_WORKSPACE_ID`, `RAW_LAKEHOUSE_NAME`, etc.), the raw lakehouse name, timezone, naming patterns for lakehouses, schemas, notebooks, models and pipelines, watermark and SCD defaults, and client-wide rule overrides.
2. **Authenticate via Azure CLI (`az login`) & Discover via Fabric MCP Server.** Authentication uses interactive user identity (`az login` / `az account show`), eliminating client secrets. At G0b, the skill connects to Fabric at the tenant level using `onelake_list-workspaces` to list all accessible workspaces and prompt for user selection. Immediately after workspace selection, G1a asks the user to choose their action (1 Start a new project, 2 Resume an existing project, 3 Stop).
3. **Follow [`interface.md`](interface.md).** It is the conversation: the gates G0–G15, their exact wording, the replies each accepts, and the issues loop. **Every question put to the user comes from that file.**
4. **At G2, resolve Target Folder Name & create Target Directory structure.** Based on raw folder selection from Source Lakehouse `{raw_lakehouse}`, AI automatically suggests Target Folder Name `<Derived_Name>`. User can reply `y` or enter a custom target folder name (`<target_folder_name>`). Creates target folder `<target_folder_name>` in `{workspace}` containing directly `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`, and requests file details approval (G2b). Creation of Target Lakehouse `<Target>_LH` in Fabric is deferred until notebook or orchestrator execution.
5. **Live Runtime Data Profiling (G4/G5)**: Candidate keys, encodings, null percentages, date layouts, and missing value tokens are detected live during a Livy Spark session on raw source files. Approved attributes are held dynamically in execution memory.
6. **Understanding Summaries after Uploads (G8 & G11)**:
   - **G8 (`UPLOAD`)**: After parsing uploaded business rules, the AI presents a structured **"Understanding of Uploaded Business Rules"** summary (rule IDs, target columns, transformations, and 5-level precedence mapping) before proceeding to G9.
   - **G11 (`UPLOAD`)**: After parsing the uploaded STTM document, the AI presents a structured **"Understanding of Uploaded STTM Document"** summary (derived Dimensions/Facts, SHA-256 surrogate keys, measures, and joins) before proceeding to G12.
7. **Execution & Skip Protocol (`[y/n/skip]`)**: Every run prompt (`Bronze` G7a, `Silver` G10a, `Gold` G12c, `Orchestrator` G13c, `Semantic Model` G14c) presents options `[y/n/skip]`. Replying `y` submits the item to Fabric asynchronously in the background and prompts post-submission choices `[1/2/3]` (1 Move to next stage, 2 Poll background status, 3 Stop chat session cleanly while job runs independently in Fabric). Replying `skip` (or `s`) bypasses execution for that layer and moves directly to the next stage.
8. **Write every notebook to [`notebook_standards.md`](notebook_standards.md)**: follow the per-layer narrative step-by-step section flow (Bronze, Silver, Gold), the Single-Responsibility Cell Principle (One Cell = One Logic), vertical PySpark method chaining, explicit constants, and fail-fast assertions.
9. **Before displaying any notebook**, check it against [`failure_registry.md`](failure_registry.md) and the checklist in `notebook_standards.md`.

Where each method file is used:

| Gate | Method |
|---|---|
| G1–G4 | this file: **Dynamic resolution**, **Profiling** |
| G6–G7 | this file: **Table naming**, **Bronze load semantics** |
| G8–G10 | [`basic_transformation_logic.md`](basic_transformation_logic.md) + this file: **Silver load semantics**, **Silver column contract** |
| G11–G12 | [`gold_grain_modelling.md`](gold_grain_modelling.md) |
| G13 | this file: **Orchestration**; `failure_registry.md` → *Orchestrator failure path* |
| G14 | [`semantic_model_generation.md`](semantic_model_generation.md) |
| every notebook (G7, G10, G12b, G13c refresh notebook) | [`notebook_standards.md`](notebook_standards.md): layout, comments, codes, metadata columns, date/time format |

### Resolved names used throughout

For the selected dataset, these names are computed from `client_config.md` patterns and G2 Target Name resolution:

| Name | Pattern key | Example (Target = Marine) |
|---|---|---|
| `{raw_lakehouse}` | `raw_lakehouse` | Selected Source Lakehouse at G1 (e.g. `Raw_Insurance_LH`) |
| `{target}` / `{Target}` | resolved target name | `Marine` (or custom write-in name) |
| `{lakehouse}` | `lakehouse_pattern` | `Marine_LH` (Target Lakehouse, deferred creation) |
| `{bronze_schema}` · `{silver_schema}` · `{gold_schema}` | `schema_pattern` | `bronze` · `silver` · `gold` |
| `{control_schema}` | `control_schema` | `dbo` |
| `{notebook:bronze}` · `{notebook:silver}` · `{notebook:gold}` | `notebook_pattern` | `Bronze_Marine` · `Silver_Marine` · `Gold_Marine` |
| `{pipeline}` | `pipeline_pattern` | `Marine_Medallion_Orchestrator` |
| `{semantic_model}` | `semantic_model_pattern` | `Marine_Gold_Model` |

## The approval cases

Before every DE review gate (G7, G10, G12b, G14b), decide which case applies. **The case changes only what the gate shows, never whether it is asked.** Every review gate is always asked. DE `APPROVE` deploys the item to Fabric without automatically running it.

| Case | Condition | Shown at the gate |
|---|---|---|
| **A** | the item does not exist | the complete notebook or definition |
| **B** | the item exists, and its input changed | the diff against the existing item, plus a plain-language account of what moved in the input |
| **C** | the item exists, and its input is unchanged | *"Unchanged since last approval — APPROVE deploys the approved version."* plus a summary |

After `APPROVE`, the item is deployed to Fabric. Execution is prompted separately with `[y/n/skip]`.

### What "input changed" means per layer

| Layer | Compared | Changed when |
|---|---|---|
| Bronze | today's raw headers after `sanitize()` and the set of files in the partition, against the Bronze table columns (minus the audit columns) | a column or a file differs, or the target table is missing |
| Silver | the Bronze column lists **and** the `rules_hash` of the rule set chosen at G8, against the last successful `stage='silver'` row in `project_status` | either one differs |
| Gold | the live **grain fingerprint**, and the configured schemas, against the registered `gold_model.yaml` | see **Gold — grain-adaptive** |
| Semantic | `model_version` + `grain_fingerprint` + `semantic_model_hash` | see `semantic_model_generation.md` |

## Approval rules — which gate authorises what

| Action | Authorised by |
|---|---|
| List lakehouses, list raw files, profile, profile the Silver grain | the `y` at G1 / G3 / G4 / G11. Read-only, no approval needed. |
| Create target folder `<target_folder_name>` (`<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`) | the `y` / custom folder name write-in at G2 |
| Create Target Lakehouse `<Target>_LH` | deferred until first execution (`y` at G7a, G10a, G12c, or G13c) |
| Create `{silver_schema}`, only if it does not exist | the `y` at G9 |
| Create `{gold_schema}` | created when Gold notebook is executed |
| Save live profiling attributes to memory | G5 `APPROVE` |
| Create or update (deploy) the Bronze notebook | G7 `APPROVE` |
| Run Bronze notebook | G7a `y` (background submit -> `[1/2/3]`: 1 move next, 2 poll status, 3 stop chat session cleanly); `skip` moves next; `n` stops |
| Create or update (deploy) the Silver notebook; register uploaded rules | G10 `APPROVE` (G8 `SKIP` thank-you exit) |
| Run Silver notebook | G10a `y` (background submit -> `[1/2/3]`: 1 move next, 2 poll status, 3 stop chat session cleanly); `skip` moves next; `n` stops |
| Mark `gold_model.yaml` `APPROVED` | G12 `APPROVE` (G11 `SKIP` thank-you exit) |
| Create or update (deploy) the Gold notebook; mark model `REGISTERED` | G12b `APPROVE` |
| Run Gold notebook | G12c `y` (background submit -> `[1/2/3]`: 1 move next, 2 poll status, 3 stop chat session cleanly); `skip` moves next; `n` stops |
| Create or update (deploy) the pipeline | the `y` at G13, plus G13a/G13b picks |
| Run the pipeline (executes all deployed notebooks) | G13c `y` (background submit -> `[1/2/3]`: 1 move next, 2 poll status, 3 stop chat session cleanly); `skip` moves next; `n` stops |
| Deploy or register the semantic model definition | G14b `APPROVE` |
| Refresh semantic model dataset | G14c `y` (background submit -> `[1/2/3]`: 1 move next, 2 poll status, 3 stop chat session cleanly); `skip` moves next; `n` stops |

Never ask twice for the same thing. Never create, update or run an item before the gate that authorises it. **Approval is registration.** There is no separate "register?" question for rules, the Gold model or the semantic model.

## Dynamic resolution — resolve, never hardcode

Resolve every identifier at runtime. A lakehouse that is deleted and recreated gets a **new GUID**, so any stored GUID is a latent bug.

### 1. Discover the Raw Folder & Resolve Target Name

**G2 decides which dataset target is built, and it is always exactly one.** Another dataset comes afterwards, through G15 → G2.

1. Resolve the workspace from `client_config.md` → `workspace`. If it is blank: list tenant workspaces at G0b.
2. Immediately at G1a, ask user for Project Action (Start new project / Resume existing project / Stop).
   - If **Resume an existing project**: Perform 2-tier project discovery in `{workspace}`:
     a. **Standalone Lakehouses**: Check root workspace lakehouses for table `dbo.project_status`.
     b. **Project Folders**: Check workspace folders (`<target_folder_name>`) for a nested lakehouse item (`<target_folder_name>_LH`) containing table `dbo.project_status`.
     c. Display discovered projects for selection, query `dbo.project_status` in the selected project, display a structured Project Stage Summary table (Stage: `current_project_stage`, Status: `overall_project_status`, Gate: `current_gate`, Next Action: `next_action_required`, Completion: `completion_percentage` %), and prompt directly at `G-pending` (`current_gate`).
3. If Start new project: G1 lists `{raw_lakehouse}/Files/`. Each top-level subdirectory is a candidate raw folder (`Files/Marine` → `Marine`). Skip `_`-prefixed system folders.
4. At G2, AI derives suggested Target Folder Name `<Derived_Name>`. User can reply `y` or enter a custom target folder name (`<target_folder_name>`).
5. Target folder `<target_folder_name>` is created in workspace containing directly `<target_folder_name>_LH`, `notebooks`, `orchestrator`, `semantic model`. Target Lakehouse `<Target>_LH` creation is deferred until notebook/orchestrator execution.

### 2. Table Naming Semantics

- **Bronze & Silver Tables**: Delta table names match the exact raw filename stem from OneLake (e.g. `marine_policy.csv` → `marine_policy`, `marine_claim.csv` → `marine_claim`).
- **Gold Tables**: Delta table names and measures match the client-style STTM document uploaded at G11 (e.g., `dim_policy`, `dim_vessel`, `fact_claim`).
