# Insurance Medallion on Microsoft Fabric: End-to-End Guide

> **Who this is for:** an engineer joining the project who needs to understand it, run it and extend it.
> **Last updated:** 24 Sep 2026.
>
> **How to read it**
>
> - **Part 1: Understand** (§1–§6). Read it top to bottom on your first day. It explains what the
>   project does, how the pieces fit together, and exactly what happens from `START` to a Power BI model.
> - **Part 2: Do** (§7). Run it yourself.
> - **Part 3: Reference** (§8–§15). Look things up when you need them: scripts, config, IDs, known
>   gaps, glossary.
>
> All diagrams are plain text, so they render in any Markdown viewer, including VS Code's preview.
> Links are relative to this file (`docs/`). Line numbers refer to the files as they were on 24 Sep 2026.

---

## Contents

**Part 1: Understand**

1. [What this project is](#1-what-this-project-is)
2. [Five ideas you need first](#2-five-ideas-you-need-first)
3. [Architecture](#3-architecture)
4. [Repository map](#4-repository-map)
5. [The end-to-end flow, stage by stage](#5-the-end-to-end-flow-stage-by-stage)
6. [Where each LOB stands today](#6-where-each-lob-stands-today)

**Part 2: Do**

7. [How to run it](#7-how-to-run-it)

**Part 3: Reference**

8. [Full step-by-step trace with sources](#8-full-step-by-step-trace-with-sources)
9. [Other implementations (Tracks B and C)](#9-other-implementations-tracks-b-and-c)
10. [Agents & skills catalogue](#10-agents--skills-catalogue)
11. [Scripts reference (`MCP_Claude/`)](#11-scripts-reference-mcp_claude)
12. [Configuration & auth](#12-configuration--auth)
13. [Standards vs. skill vs. reality](#13-standards-vs-skill-vs-reality)
14. [Known gaps, risks & open questions](#14-known-gaps-risks--open-questions)
15. [Glossary](#15-glossary)

**Evidence markers** used in tables:

| Marker | Meaning |
|---|---|
| **[live]** | Checked against the Fabric workspace on 24 Sep 2026 with read-only calls |
| **[code]** | From the repository only; not checked against Fabric |
| **[unknown]** | Cannot be determined from the repo or a read-only call (see §14.3) |

---

# Part 1: Understand

## 1. What this project is

**In one sentence:** you chat with Claude Code, and it builds a Bronze → Silver → Gold data
warehouse plus a Power BI model for insurance data inside Microsoft Fabric, stopping for your
approval before any new code goes live.

**The 30-second version**

- There is **no application to deploy**. The repository holds *instructions* (Markdown "skills") and helper scripts. **Claude Code is the runtime.** It reads the instructions, generates Fabric notebooks, and deploys and runs them through Fabric's APIs.
- The data is raw CSV files sitting in dataset folders under `Files/<Folder>/` in a shared raw lakehouse `<Source_Lakehouse>` in workspace **DataSonic 3**.
- For each dataset target `{target}` (resolved at Gate G2), the flow builds one Target Lakehouse, `<Target>_LH`, with a schema per layer:

  | Layer | What it holds | Built by notebook |
  |---|---|---|
  | **Bronze** | a faithful copy of raw CSVs (all columns as text, sanitized column names) | `Bronze_<Target>` |
  | **Silver** | cleaned, typed data with business rules applied | `Silver_<Target>` |
  | **Gold** | a star schema (dimensions + facts) derived from STTM mappings | `Gold_<Target>` |
  | **Semantic model** | a Power BI Direct Lake model over Gold, `<Target>_Gold_Model` | `Refresh_Semantic_Model` (refresh only) |

- You drive it by typing **`START`** in Claude Code and answering a fixed set of single-gate questions.
- **Zero-Config Architecture:** No static `.md` config files (`lob/` or `datasets/`) are required. Candidate keys, date formats, encodings, and missing value tokens are detected live during data profiling (G4/G5), while Silver rules (G8) and Gold STTM mappings (G11) are uploaded live.

---

## 2. Five ideas you need first

| Idea | What it means here |
|---|---|
| **Skill** | A Markdown instruction file that Claude Code loads and follows. The main one is [`.claude/skills/medallion/SKILL.md`](../.claude/skills/medallion/SKILL.md). It *is* the program. |
| **Dynamic Target Resolution** | Target Name `{target}` is derived automatically by the AI at Gate G2 from the raw folder stem, or custom write-in provided by the user. |
| **Approval cases A / B / C** | Before building any layer, Claude checks whether the notebook exists and whether its input changed. **A** = new notebook, **B** = input changed, **C** = nothing changed. A and B need your approval; C just runs. See §5.2. |
| **Generated, never stored** | Notebooks are **not** kept in the repo. They are regenerated from the spec files (registry, uploaded rules, `gold_model.yaml`, failure registry). The spec files are the source of truth. |
| **Failure registry** | [`failure_registry.md`](../.claude/skills/medallion/failure_registry.md) lists every failure that has already cost a run (FL-001…FL-017), with its fix. Every generated notebook is checked against it before you see it. |

---

## 3. Architecture

### 3.1 The big picture

```text
 ┌──────────────────────────── YOUR MACHINE ─────────────────────────────┐
 │                                                                       │
 │   ┌──────────┐   "START", answers,   ┌───────────────────────────┐    │
 │   │ Engineer │ ────── approvals ───► │       Claude Code         │    │
 │   │  (you)   │ ◄──── questions, ──── │  running the "medallion"  │    │
 │   └──────────┘   notebooks, results  │          skill            │    │
 │                                      └──┬─────────────────────┬──┘    │
 │                         reads as files  │                     │       │
 │               ┌─────────────────────────┘                     │       │
 │               ▼                                               │       │
 │   ┌─────────────────────────────────────┐                     │       │
 │   │ .claude/skills/medallion/           │  HOW: generic flow  │       │
 │   │   flow, rules, failure registry     │  for any dataset    │       │
 │   └─────────────────────────────────────┘                     │       │
 │                                                               │       │
 │           two ways out to Fabric:                             │       │
 │     ┌─────────────────────────────┐    ┌──────────────────────┴────┐  │
 │     │ fabric-mcp-server (MCP)     │    │ Bash: az CLI token + curl │  │
 │     │ list files, make folders    │    │ create items, run jobs,   │  │
 │     │ (configured in .mcp.json)   │    │ poll, read definitions    │  │
 │     └──────────────┬──────────────┘    └──────────────┬────────────┘  │
 └────────────────────┼──────────────────────────────────┼───────────────┘
                      │                                  │
                      ▼                                  ▼
 ┌──────────────── MICROSOFT FABRIC: workspace "DataSonic 3" ────────────┐
 │                                                                       │
 │   OneLake (files + Delta tables)      Fabric REST API / Power BI API  │
 │                                                                       │
 │   <Source_Lakehouse> ──► <Target>_LH ──► <Target>_Gold_Model
 │   (CSVs)     Bronze/Silver/Gold      (Power BI, Direct Lake)          │
 │                                                                       │
 │   Notebooks Bronze/Silver/Gold_<Target> Pipeline <Target>_Medallion_Orchestrator
 └───────────────────────────────────────────────────────────────────────┘
```

Everything runs as **your own `az login` identity**. There is no service principal and no stored secret.

### 3.2 How the data moves inside Fabric

```text
  <Source_Lakehouse>  (shared raw lakehouse, one folder per dataset)
  Files/<Folder>/<yyyy>/<MM>/<dd>/*.csv   (only today's folder is read)
         │
         │  Bronze_<Target> copy as-is: every column as text, sanitized names (table names match source file stem),
         │                    4 audit columns, overwrite (skip if file unchanged)
         ▼
  ┌── <Target>_LH  (one per dataset target, schema-enabled) ────────┐
  │                                                                          │
  │   bronze.<source_stem>                                                   │
  │         │                                                                │
  │         │  Silver_<Target> business rules + basic cleanup, typed,        │
  │         │                    rows never dropped, per-rule counts logged  │
  │         ▼                                                                │
  │   silver.<source_stem>                                                   │
  │         │                                                                │
  │         │  Gold_<Target>   grain guard, then dimensions and facts        │
  │         ▼                                                                │
  │   gold.<client_sttm_table>                                               │
  │                                                                          │
  │   dbo.project_status          single central control table (project stage, status, gate, telemetry)│
  └──────────────────────────────┬───────────────────────────────────────────┘
                                 │  Direct Lake: reads the Gold Delta tables directly
                                 ▼
  <Target>_Gold_Model   Power BI semantic model (refreshed by Refresh_Semantic_Model)
```

Example: automobile → `<Source_Lakehouse>/Files/automobile/` → `Automobile_LH.Bronze.auto_policy` →
`Silver.auto_policy` → (Gold not built yet).

### 3.3 How Claude Code reaches Fabric

| Need | Mechanism | Defined in |
|---|---|---|
| List workspaces, items, OneLake files; create `Tables/<Layer>` directories | fabric MCP tools (`onelake_list-files`, `onelake_create-directory`, …) | [SKILL.md:384](../.claude/skills/medallion/SKILL.md#L384), [.mcp.json](../.mcp.json) |
| Create lakehouses, notebooks, semantic models; move items; run and poll jobs | Fabric REST through Bash with `az account get-access-token --resource https://api.fabric.microsoft.com`. (The MCP's `core_create-item` can't target a folder or enable schemas, hence REST.) | [SKILL.md:424-447](../.claude/skills/medallion/SKILL.md#L424-L447) |
| Read CSV headers cheaply | OneLake DFS ranged `GET` (`Range: bytes=0-2600`) with a `https://storage.azure.com` token | [SKILL.md:456-463](../.claude/skills/medallion/SKILL.md#L456-L463) |
| Derive Gold star schema (grain) | STTM-driven and Schema-driven derivation from Silver schemas and user-uploaded STTM document | [gold_grain_modelling.md](../.claude/skills/medallion/gold_grain_modelling.md) |
| Refresh the semantic model and check it with DAX | Power BI REST (refresh, `executeQueries`) | [semantic_model_generation.md:175-181](../.claude/skills/medallion/semantic_model_generation.md#L175-L181) |

---

## 4. Repository map

```text
mcp-claude/
│
├── .claude/                              ◄ START HERE: what Claude Code actually runs
│   ├── skills/medallion/
│   │   ├── SKILL.md                      the whole flow: handshake, cases, per-layer rules
│   │   ├── basic_transformation_logic.md generic Silver cleanup (business rules outrank it)
│   │   ├── failure_registry.md           every past failure and its fix (FL-001…FL-017)
│   │   ├── gold_grain_modelling.md       how Gold is derived from STTM + Silver schemas
│   │   └── semantic_model_generation.md  Gold → Power BI model (rules S1–S10)
│   └── agents/fabric.agent.md            unfilled template; ignore
│
├── .agents/                              per-LOB specs + older standards
│   ├── skills/<lob>_medallion/           one folder per LOB: automobile, marine, home, aviation
│   │   ├── SKILL.md                      bindings + domain specifications
│   │   ├── registered_business_rules.md  approved Silver rules = the Silver spec
│   │   ├── gold/gold_model.yaml          registered Gold + semantic model (marine only)
│   │   ├── business_rules.md             ┐
│   │   ├── dq_rules.md                   ├ background vocabulary, not executed
│   │   ├── relationships.md              ┘
│   │   └── bronze/ silver/ gold/SKILL.md ⚠ stale: describe an older design
│   ├── skills/*-cli, e2e-medallion-…     copies of Microsoft vendor skills (reference)
│   ├── common/*.md                       ⚠ older standards, partly overridden (see §13)
│   ├── templates/                        notebook + orchestrator templates
│   ├── AGENTS.md, agents/                ⚠ legacy: written for a previous AI assistant
│   └── mcp_config.json                   HTTP MCP config (which client reads it is unknown)
│
├── MCP_Claude/                           ⚠ legacy "Track B": Raw → Bronze_Layer Python scripts
├── skills-for-fabric/                    vendor clone of Microsoft's skills-for-fabric
├── docs/END_TO_END_FLOW.md               this document
├── .mcp.json                             registers fabric-mcp-server with Claude Code
├── .vscode/mcp.json                      HTTP MCP config for VS Code clients (not Claude Code)
└── hdr.txt, hdr2.txt                     dead files (old HTTP response headers)
```

**Suggested reading order for a new joiner**

1. This document, Part 1.
2. [`.claude/skills/medallion/SKILL.md`](../.claude/skills/medallion/SKILL.md): the flow itself.
3. [`.agents/skills/marine_medallion/`](../.agents/skills/marine_medallion): the one LOB that is
   complete. Look at `SKILL.md`, `registered_business_rules.md` and `gold/gold_model.yaml`.
4. [`failure_registry.md`](../.claude/skills/medallion/failure_registry.md): what has gone wrong before.
5. [`gold_grain_modelling.md`](../.claude/skills/medallion/gold_grain_modelling.md) and
   [`semantic_model_generation.md`](../.claude/skills/medallion/semantic_model_generation.md) when you work on Gold.

Treat anything marked ⚠ as out of date. Where it disagrees with `.claude/skills/medallion/`, the
medallion skill wins.

---

## 5. The end-to-end flow, stage by stage

### 5.1 The flow at a glance

```text
  You type START
        │
        ▼
  ┌──────────────────────────────────┐
  │ 0. HANDSHAKE                     │  greeting → "list LOBs?" → "what to do?" → "all or one LOB?"
  └────────────────┬─────────────────┘
                   ▼
  ┌──────────────────────────────────┐
  │ 1. BRONZE      Bronze_<Lob>   │ ◆  ingest the raw CSVs as they are
  └────────────────┬─────────────────┘
                   │  "Do you want me to proceed with the silver layer ?"
                   ▼
  ┌──────────────────────────────────┐
  │ 2. SILVER      Silver_<Lob>   │ ◆  apply the business rules document
  └────────────────┬─────────────────┘
                   │  "Do you want me to proceed with the gold layer ?"
                   ▼
  ┌──────────────────────────────────┐
  │ 3. GOLD        Gold_<Lob>     │ ◆  profile grain → model review → star schema
  └────────────────┬─────────────────┘
                   │  "Do you want me to proceed with orchestrator pipeline ?"
                   ▼
  ┌──────────────────────────────────┐
  │ 4. ORCHESTRATOR (Fabric pipeline)│ ◆  scheduled Bronze → Silver → Gold → Refresh_Semantic_Model
  └────────────────┬─────────────────┘
                   │  "Do you want me to proceed with semantic model ?"
                   ▼
  ┌──────────────────────────────────┐
  │ 5. SEMANTIC    <Lob>_Gold_Model  │ ◆  Direct Lake model + DAX verification
  └──────────────────────────────────┘

  ◆ = approval gate. You approve only when the notebook/definition is new (Case A)
      or its input changed (Case B). Unchanged work (Case C) runs without asking.
```

Each layer ends with a closing line (*The tables are created/updated in the \<layer\> layer*) and
per-table row counts, `skipped` included. If you choose "all LOBs", each layer runs for every LOB
**one after another**. A failed LOB doesn't stop the others, and the handoff question is asked only
once, after every LOB has succeeded.

### 5.2 The approval model: Cases A, B and C

This decision is made **before** every layer, and it is the heart of the design.

```text
                      Does this layer's notebook already exist in Fabric?
                           │                                   │
                           no                                  yes
                           ▼                                   ▼
                     ┌───────────┐                  Has its input changed?
                     │  CASE A   │                  ─────────────────────
                     │ new       │                  Bronze / Silver : sanitized CSV headers
                     │           │                                    vs. target table columns
                     │ show the  │                  Gold            : grain fingerprint
                     │ full      │                                    vs. gold_model.yaml
                     │ notebook, │                  Semantic model  : semantic_model_hash
                     │ ask to    │                        │                    │
                     │ approve   │                       yes                   no
                     └───────────┘                        ▼                    ▼
                                                   ┌────────────┐      ┌─────────────────┐
                                                   │  CASE B    │      │  CASE C         │
                                                   │  changed   │      │  unchanged      │
                                                   │            │      │                 │
                                                   │ show the   │      │ run immediately,│
                                                   │ DIFF, ask  │      │ no approval     │
                                                   │ to approve │      │                 │
                                                   └────────────┘      └─────────────────┘
```

- A new file modification time is **not** a change. Only the column set (or, for Gold, the grain) counts.
- The approval question names the layer's job: *This is the **ingestion** notebook…* (Bronze),
  *…**Transformation** notebook…* (Silver), *…**Dimensional Model** notebook…* (Gold),
  *This is the **Semantic Model definition**…*, *This is the **orchestrator pipeline**…*.
- **One approval covers one notebook.** Approving `Bronze_Automobile` says nothing about `Bronze_Marine`.

**What never needs approval:** discovering LOBs, profiling sources, creating the LOB lakehouse,
creating the `Bronze`/`Silver` schema folder, placing items in folders, and running an unchanged
notebook (Case C). The `Gold` schema is never created directly: only the approved Gold notebook
creates it when it runs.

Source: [SKILL.md:243-321](../.claude/skills/medallion/SKILL.md#L243-L321).

### 5.3 Stage 0: the handshake

The conversation is fixed. Claude asks one line at a time and waits for your reply.

| # | Claude says (exactly) | You reply | What happens |
|---|---|---|---|
| 1 | *Welcome to AI Native Data Engineering* | (after you typed `START`) | nothing else is printed |
| 2 | *Should I list the LOB's present in Raw Lakehouse?* | `yes` / `no` | on yes: lists `<Source_Lakehouse>/Files/` and prints a numbered LOB list |
| 3 | *what you want me to do !* | `show me the bronze layer` (or silver / gold) | picks the layer |
| 4 | *Should I process with all the LOB's or you have any specific one ?* | `all`, a LOB name, or its number | picks the scope. Other LOBs are left untouched |

If your first message already names a layer and a LOB (*"build bronze for marine"*), the matching
questions are skipped. Source: [SKILL.md:15-109](../.claude/skills/medallion/SKILL.md#L15-L109).

### 5.4 Stage 1: Raw → Bronze

**Goal:** land every raw CSV in a Delta table exactly as it is. No business logic and no data
quality rules are applied here.

| | |
|---|---|
| **Input** | `<Source_Lakehouse>/Files/<LobFolder>/<yyyy>/<MM>/<dd>/*.csv` for **today's date only**. The folder is found from the LOB name at runtime, ignoring case, and is never configured |
| **Output** | `<Lob>_LH.Bronze.<entity>`, rows in `dbo.load_control`, a log in `Files/_logs/` |
| **Notebook** | `Bronze_<Lob>` (one per LOB, loops over discovered CSV files) |

**What Claude does**

1. **Reads the specs:** the LOB's `SKILL.md` and `failure_registry.md`.
2. **Resolves or creates the lakehouse** `<Lob>_LH` by exact name. If it's missing, it
   creates it with `enableSchemas: true` (this can't be switched on later). Only a Bronze build may
   create the lakehouse.
3. **Creates `Tables/Bronze`** if it doesn't exist.
4. **Profiles the sources** with cheap ranged header reads. It checks for known hazards: embedded
   newlines (`multiLine`), non-UTF-8 files (cp1252), phantom trailing columns (`_c6`…), mixed date
   formats, sentinel values, non-unique keys, and missing "modified" columns.
5. **Names the tables** directly by sanitizing raw file stems into un-prefixed snake_case names (e.g. `policy.csv` → `policy`).
6. **Decides the case** (A/B/C, §5.2), then generates the notebook, shows it and waits for approval if needed.
7. **Deploys** the notebook (`POST notebooks` or `updateDefinition`), waits for the operation to
   finish, and reads it back to confirm the new version is live in Microsoft Fabric (without running it immediately).
8. **Reports** that the notebook is deployed, then asks *Do you want me to proceed with the silver layer ?*

**Rules that matter**

- Every column is read as a **string**. Typing happens in Silver.
- Column names go through `sanitize()`: newlines → space, `%` → `pct`, anything non-alphanumeric →
  `_`, lower case. Source spellings are kept (`CHASIS NO` → `chasis_no`). **Changing `sanitize()`
  renames every downstream column**, so treat it as a contract.
- Every write is a full **overwrite**, so reruns can't duplicate data. There's no MERGE because the
  source keys aren't unique (FL-009).
  - `initial` (first load) and `full` (reference feeds) always overwrite.
  - `snapshot` (transaction feeds) **skips** the table if the watermark `<yyyy>/<MM>/<dd>|<mtime>` hasn't changed, so a new day's folder always reloads.
- If today's folder is missing or empty, nothing is loaded or overwritten and the run ends `SKIPPED`. It never falls back to an older date.
- Four audit columns are added: `_source_file`, `_ingestion_timestamp`, `_batch_id`, `_source_mtime`.

Source: [SKILL.md:454-554](../.claude/skills/medallion/SKILL.md#L454-L554).

### 5.5 Stage 2: Bronze → Silver

**Goal:** turn Bronze into clean, typed tables by applying the **business rules document**, and
record how every rule performed, without dropping or flagging any row.

| | |
|---|---|
| **Input** | `Bronze.*` + a business rules document (uploaded now, or the registered one) |
| **Output** | `Silver.<lob_code>_<entity>`, status and metrics in `dbo.project_status` |
| **Notebook** | `Silver_<Lob>` |

**What Claude does**

1. **Asks for the rules.** It checks `.agents/skills/<lob>_medallion/registered_business_rules.md`:
   - no registered rules → *Please upload the Business Rule Document*
   - registered rules exist → *Please upload the Business Rule Document or should I process with the registered Business Rules ?*
2. **Reads** the rules, [`basic_transformation_logic.md`](../.claude/skills/medallion/basic_transformation_logic.md)
   and the failure registry.
3. **Generates** `Silver_<Lob>` with **one commented block per rule id**. Blocks that come from the
   generic logic rather than the rules are marked *basic*, so a reviewer can tell them apart.
4. **Approval → deploy → run**, exactly as in Bronze.
5. **Reports** row counts and stage-level execution status (read back from `dbo.project_status`), plus any rule that could not run and why.
6. **Offers to register the rules** (*Do you want to register these Business Rules for future
   processing ?*), but only if you uploaded a new document. On yes, it overwrites `registered_business_rules.md`.
7. Asks *Do you want me to proceed with the gold layer ?*

**Rules that matter**

- **Priority when sources disagree:** business rules → Bronze contracts → Silver column contract →
  basic transformation logic. The failure registry applies throughout.
- **Never invent a rule.** If the document is silent on something the layer needs, Claude asks that one question.
- **Rows are never dropped or marked.** Rule outcomes are counts in `dbo.dq_rule_results`.
- **The column contract is closed:** business columns + the 4 Bronze audit columns +
  `_silver_run_id` + `_silver_timestamp`. A rule that would need a new column is recorded as `BLOCKED`.
- Rule statuses: `RUN` (fully evaluated), `PARTIAL` (evaluated without some marker or reference
  data), `BLOCKED` (cannot run), `GOLD` (deferred to Gold).
- **Skip logic:** a table is skipped only when **both** the Bronze data version (`source_version`)
  **and** the rule set (`rules_hash`) are unchanged. New rules on old data still rebuild.
- Generic cleanup includes trimming, blank → NULL, identifiers kept as strings, dates parsed only
  when the format is known (never a `dd/MM` vs `MM/dd` guess), `DECIMAL` for money, and no currency conversion.

Source: [SKILL.md:139-241](../.claude/skills/medallion/SKILL.md#L139-L241), [:556-635](../.claude/skills/medallion/SKILL.md#L556-L635).

### 5.6 Stage 3: Silver → Gold

**Goal:** build a star schema that matches what the Silver data *actually* looks like, and rebuild
it only when that shape (the "grain") changes.

| | |
|---|---|
| **Input** | `Silver.*` + (if present) the registered `gold/gold_model.yaml` |
| **Output** | `Gold.<lob_code>_dim_*`, `Gold.<lob_code>_fact_*`, status & metrics in `dbo.project_status`, updated `gold_model.yaml` |
| **Notebook** | `Gold_<Lob>` |

**What Claude does**

1. **Resolves the lakehouse** and stops if it's missing. It creates **nothing** yet, not even the `Gold` schema.
2. **Profiles the grain** by running `grain_profile()` from [`grain_profile.py`](../.claude/skills/medallion/grain_profile.py)
   on each Silver table in a Spark session (read-only). This finds:
   - **row types:** subsets of rows that differ in which columns are filled
   - **the grain key:** the smallest set of columns that makes a row unique
   - **functional dependencies:** which columns belong in which dimension
   - **measure additivity:** whether a number can be summed per row, or only once per parent
   - **surprises** against the expectations in `relationships.md`
   - cross-table match rates and **fan-out**, i.e. whether a join would multiply rows
3. **Computes the grain fingerprint** (a hash of that structure) and compares it with the one in
   `gold_model.yaml` to pick the case (A/B/C).
4. **Case A or B: model review.** Claude shows the profile, the fingerprint, the proposed YAML, an
   ER diagram, the fan-out table and open questions. **You decide:**
   - the SCD strategy (SCD1, or SCD2 from Delta history, or SCD2 via merge)
   - how to treat duplicates (rule G10)
   - every semantic surprise
   - any derived-measure formula the rules leave open
5. **Generates** the YAML and `Gold_<Lob>`, and asks *This is the Dimensional Model notebook, do you approve it?*
6. **Runs** the notebook. It passes through four gates:

   ```text
   Gate 1  SKIP CHECK    Silver unchanged and MODEL_VERSION unchanged? → write nothing, report "skipped"
   Gate 2  GRAIN GUARD   live fingerprint ≠ approved one?            → stop with GRAIN_DRIFT, write nothing
   Gate 3  SCHEMA        CREATE SCHEMA IF NOT EXISTS Gold
   Gate 4  BUILD         dimensions first, then facts (asserting fan-out = 1.0 & GOLD-RECON-SUM assertions; failures log to dbo.project_status)
   ```

7. **Reports** row counts, reconciliation, derived-measure statuses and orphan counts, then asks
   *Do you want to register this Gold model for future processing ?* On yes, `gold_model.yaml` is
   marked `REGISTERED` with version, fingerprint, date and run id.

**Modelling rules G1–G10** ([gold_grain_modelling.md:195-259](../.claude/skills/medallion/gold_grain_modelling.md#L195-L259)):
one fact per grain · dimensions from functional dependencies, conformed across facts · each measure
lives at its own grain · degenerate dimensions · fan-out must be 1.0 · one role-playing date
dimension · SHA-256 surrogate keys plus an `UNKNOWN` member · currency safety, no FX · derived
measures · duplicate treatment is **asked**, never silent.

Source: [SKILL.md:637-708](../.claude/skills/medallion/SKILL.md#L637-L708), [gold_grain_modelling.md](../.claude/skills/medallion/gold_grain_modelling.md).

### 5.7 Stage 4: Orchestrator Pipeline

**Goal:** construct and deploy the Fabric Data Factory orchestrator pipeline `<Lob>_Medallion_Orchestrator` to execute the end-to-end Medallion workflow (`Bronze_<Lob>` → `Silver_<Lob>` → `Gold_<Lob>` → `Refresh_Semantic_Model`).

1. Asks user for creation approval (G13), then prompts for Source Lakehouse (G13a) and Target Lakehouse (G13b).
2. Deploys `<Lob>_Medallion_Orchestrator` to Fabric workspace.
3. Prompts G13c *"Run orchestrator now? [y/n/skip]"*.
   - On `y`: Submits the job asynchronously to Fabric in the background and returns `<run_id>`. Immediately presents post-submission options:
     ```text
     Select action: press 1 to Move to next stage immediately, 2 to Poll background execution status, 3 to Stop chat session [1/2/3]
     ```
     - **Option 1**: Moves immediately to Stage 5 without waiting.
     - **Option 2**: Polls background execution status until completion.
     - **Option 3**: Stops the chat conversation session cleanly. *Note: Stopping the chat session does NOT cancel or stop the background Fabric execution; the job continues running independently in Fabric.*
   - On `skip`: Bypasses job execution entirely and proceeds directly to Stage 5.
   - On `n`: Outputs thank-you message and stops.

```text
  <Lob>_Medallion_Orchestrator
  parameters: start_from_stage (bronze|silver|gold), load_type; batch_id = pipeline RunId

  Validate_Parameters
        │
        ▼
  Bronze_<Lob>        runs if start_from_stage = bronze
        │
        ▼
  Silver_<Lob>        runs if start_from_stage = bronze or silver
        │
        ▼
  Gold_<Lob>          always runs
        │
        ▼
  Switch on the Gold notebook's exitValue.status
        │
        ├── Succeeded   ──► Refresh_Semantic_Model   (semantic-link reframe of <Lob>_Gold_Model)
        ├── GRAIN_DRIFT ──► fail the run                (a human must re-model Gold)
        └── SKIPPED     ──► do nothing
```

### 5.8 Stage 5: Gold → Semantic Model

**Goal:** publish the Gold star schema as a Direct Lake Power BI model `<Lob>_Gold_Model` that people can build reports on.

1. Generates Direct Lake semantic model definition `<Lob>_Gold_Model` from Gold tables (G14).
2. DE review approval gate (G14b). Deploys `<Lob>_Gold_Model` to Fabric.
3. Prompts G14c *"Refresh semantic model dataset now? [y/n/skip]"*.
   - On `y`: Submits dataset refresh asynchronously in the background (`<run_id>`) and presents post-submission choices `[1/2/3]` (1 Move to handoff, 2 Poll status, 3 Stop chat session while background refresh continues).
   - On `skip`: Bypasses refresh and proceeds directly to Handoff (G15).
   - On `n`: Outputs thank-you message and stops.

### 5.9 When a run fails

Every generated notebook catches errors per table, writes the traceback to
`Files/_logs/<stage>_<run_id>.log`, and **then** re-raises. Without that file the cause is lost,
because Fabric kills the Spark session on failure.

```text
  run fails
     │
     ▼
  read Files/_logs/<stage>_<run_id>.log
     │
     ▼
  is the error already in failure_registry.md?
     │                                   │
    yes                                  no
     ▼                                   ▼
  apply the recorded fix (FL-0NN),    diagnose and fix it, APPEND a new FL entry
  say which entry it was              to failure_registry.md, then re-run
     │                                   │
     └──────────────► re-run ◄───────────┘
```

Where each kind of lesson goes: Spark/Delta/Fabric mechanics go in `failure_registry.md`, which is 100% dataset-independent and shared by all LOBs. Data-specific lessons (a feed's date layouts, sentinels, junk keys, encodings) go in that LOB's `registered_business_rules.md`. When generating notebooks, the AI applies all `failure_registry.md` guardrail fixes but emits clean, human-readable PySpark comments instead of raw `FL-NNN` tracking tags. Source: [SKILL.md:788-825](../.claude/skills/medallion/SKILL.md#L788-L825).

### 5.10 If a notebook is deleted

Nothing is lost, because notebooks are regenerated from the spec:

| To rebuild | Read, in order |
|---|---|
| Bronze / Silver | `failure_registry.md` → `<lob>_medallion/registered_business_rules.md` → `<lob>_medallion/SKILL.md` |
| Gold | `failure_registry.md` → `gold_grain_modelling.md` + `grain_profile.py` → `<lob>_medallion/gold/gold_model.yaml` |

The result behaves the same (same tables, columns and counts), though the code won't match byte
for byte. A regenerated Gold notebook with an unchanged model and fingerprint is still Case C.

---

## 6. Where each LOB stands today

| Stage | automobile | marine | home | aviation |
|---|---|---|---|---|
| Raw data in `<Source_Lakehouse>` | ⚠️ `Files/automobile`, 4 CSVs, **flat (legacy, not yet dated)** | ✅ `Files/Marine/2026/09/25`, 4 CSVs | ❌ no folder | ❌ no folder |
| Domain specs *(code)* | ✅ 4 entities, `lob_code=auto` | ✅ 2 entities, `lob_code=marine` | ❌ empty | ❌ empty |
| Lakehouse | ✅ `Automobile_LH` | ✅ `Marine_LH` | ❌ | ❌ |
| Bronze | ✅ 4 tables, `Bronze_Automobile` | ✅ 2 tables, `Bronze_Marine` | ❌ | ❌ |
| Registered rules *(code)* | ✅ `BRD-1.0`, 34 rules (11 BLOCKED) | ✅ `MAR-BRS-1.0`, 45 rules | ❌ placeholder | ❌ placeholder |
| Silver | ✅ 4 tables, `Silver_Automobile` | ✅ 2 tables, `Silver_Marine` | ❌ | ❌ |
| Gold | ❌ not built ¹ | ✅ v2.0.0 registered, 10 tables, `Gold_Marine` | ❌ | ❌ |
| Semantic model | ❌ | ✅ `Marine_Gold_Model` | ❌ | ❌ |
| Orchestrator | ❌ ¹ | ✅ `Marine_Medallion_Orchestrator` | ❌ | ❌ |
| Layer sub-skills *(code)* | ⚠️ stale | ⚠️ bronze/silver stale, gold current | ⚠️ stale | ⚠️ stale |

All rows were verified live on 24 Sep 2026 except those marked *(code)*.
¹ Fabric does contain `Gold_Dimensional_Model_Automobile` and `00_Automobile_Medallion_Orchestrator`,
but they belong to the unexplained "Track C" (§9.2), not to this flow.

**What's live for marine** (the reference LOB):

- **Bronze / Silver:** `marine_policy`, `marine_claim`. Files are cp1252-encoded, and the raw folder
  is `Marine` with a capital M.
- **Gold:** dimensions policy, vessel, customer, broker, facility, claim, date. Facts
  `marine_fact_policy_risk`, `marine_fact_claim_vessel`, `marine_fact_claim_settlement_txn`.
  Fingerprint `353916f47265cf05`, SCD1. `MAR-GOLD-005` is BLOCKED.
- **Semantic model:** 10 tables, 25 relationships (5 inactive date roles), 41 measures,
  "54/54 DAX checks PASS" as recorded in the YAML.

**Automobile rules:** automobile has 11 BLOCKED rules, and 3 of its results are flagged as measurement artefacts.

---

# Part 2: Do

## 7. How to run it

### 7.1 Prerequisites

1. **Fabric access:** Contributor (or higher) on workspace **DataSonic 3**, which has a capacity.
   Raw CSVs must be in `<Source_Lakehouse>/Files/<lob>/<yyyy>/<MM>/<dd>/`, one folder per day.
2. **Tools:** Azure CLI, Node.js (for `npx`), Claude Code, Python 3.12+. For
   `check_sql_endpoint.py` only: `pip install pyodbc` and ODBC Driver 18 for SQL Server.
3. **Sign in:**

   ```powershell
   az login
   az account show --query "{user:user.name, tenant:tenantId}" -o json
   ```

### 7.2 Build a LOB with the medallion skill (the main path)

1. Open the repo root in Claude Code. When asked, approve the project MCP server
   `fabric-mcp-server`, then confirm it with `/mcp`.
2. Type `START` and answer in order: `yes` → `show me the bronze layer` → `automobile` (or a number, or `all`).
3. **Case A/B:** review the notebook and approve it. **Case C** runs without asking.
4. At *Do you want me to proceed with the silver layer ?* answer `yes`. Then either upload the
   business rules document or answer `process with the registered Business Rules`.
5. Approve the Transformation notebook. If you uploaded a new document, you can register the rules.
6. At *Do you want me to proceed with the gold layer ?* answer `yes`. Answer the model-review
   questions (SCD strategy, G10, surprises, blocked formulas), approve the Dimensional Model
   notebook, then register the model.
7. The semantic model step follows automatically. Approve the definition, then register it.
8. Optional: ask for the orchestrator and approve it (*This is the orchestrator pipeline, do you approve it?*).

### 7.3 Add a new LOB

1. Upload its CSVs to `<Source_Lakehouse>/Files/<lob>/<yyyy>/<MM>/<dd>/` (year, month and day, with zero-padded month and day).
2. Create `.agents/skills/<lob>_medallion/` by copying the `home_medallion` layout: `SKILL.md`
   (bindings and domain specification) and `registered_business_rules.md` (placeholder).
3. Run the flow. The first Bronze build proposes table names dynamically. No change to the generic skill is needed.

### 7.4 Legacy path: `Bronze_Layer` scripts (Track B)

Only needed if you work on Track B (§9.1).

> ⚠️ Every command except the first **writes to Fabric**. `test_incremental.py rewind` **deletes** Bronze rows.

```powershell
cd MCP_Claude
python fabric.py                               # read-only: resolve ws / Raw / Bronze_Layer
python profile_sources.py                      # creates + runs NB_Profile_Raw_Sources
python deploy_bronze_ingestion.py deploy       # creates/updates 3 notebooks + pipeline
python deploy_bronze_ingestion.py setup        # seeds load_control (add 'reset' to wipe state)
python run_pipeline.py                         # auto: initial or incremental per load_control
python q.py -f validate_bronze.sql             # creates + runs NB_Bronze_Query
python final_checks.py                         # runs the pipeline twice (auto, then initial)
python check_sql_endpoint.py                   # read-only TDS check
# incremental test (destructive):
python test_incremental.py rewind; python run_pipeline.py; python test_incremental.py verify
```

---

# Part 3: Reference

## 8. Full step-by-step trace with sources

Every step of the main flow, with the file and lines that drive it. All steps are **[code]**.
Where the live workspace shows the step's outcome, that is noted.

| # | Step | What happens | Driven by |
|---|---|---|---|
| 1 | **Trigger** | Claude Code auto-loads project skills from `.claude/skills/`. The `medallion` description says to use it when the user types `START` or asks for a layer. | [SKILL.md:1-4](../.claude/skills/medallion/SKILL.md#L1-L4) |
| 2 | **Greeting** | Reply exactly *Welcome to AI Native Data Engineering* and nothing else. | [SKILL.md:21-27](../.claude/skills/medallion/SKILL.md#L21-L27) |
| 3 | **Offer LOB list** | Ask *Should I list the LOB's present in Raw Lakehouse?*. On yes, list the raw lakehouse's `Files/` and number the subfolders. The name `<Source_Lakehouse>` appears only in the LOB bindings and the parameter example; the skill never pins it. | [SKILL.md:29-58](../.claude/skills/medallion/SKILL.md#L29-L58), [SKILL.md:395](../.claude/skills/medallion/SKILL.md#L395), [automobile SKILL.md:88](../.agents/skills/automobile_medallion/SKILL.md#L88). <Source_Lakehouse> holds `automobile/` and `Marine/` only **[live]** |
| 4 | **Ask what to do** | *what you want me to do !* The user names a layer. | [SKILL.md:60-67](../.claude/skills/medallion/SKILL.md#L60-L67) |
| 5 | **Ask scope** | *Should I process with all the LOB's or you have any specific one ?* "All" runs sequentially; one LOB leaves the others untouched. A failed LOB doesn't stop the others. | [SKILL.md:69-109](../.claude/skills/medallion/SKILL.md#L69-L109) |
| 6 | **LOB discovery** | Folder name → `<lob>_medallion` skill. Its files are read from disk; they are not invocable skills. | [SKILL.md:328-342](../.claude/skills/medallion/SKILL.md#L328-L342), [SKILL.md:751-771](../.claude/skills/medallion/SKILL.md#L751-L771) |
| 7 | **Resolve or create the lakehouse** | `GET items?type=Lakehouse` by exact name `<Lob>_LH`. If missing, `POST lakehouses` with `folderId` and `enableSchemas:true`, poll the LRO, then re-query. Only a Bronze build may create it. | [SKILL.md:344-370](../.claude/skills/medallion/SKILL.md#L344-L370), FL-013/FL-014 in [failure_registry.md:200-217](../.claude/skills/medallion/failure_registry.md#L200-L217). `Automobile_LH` and `Marine_LH` exist **[live]** |
| 8 | **Provision the schema** | `onelake_create-directory Tables/Bronze` (or `Silver`). Never `Gold`: only the approved Gold run creates it. | [SKILL.md:372-385](../.claude/skills/medallion/SKILL.md#L372-L385) |
| 9 | **Profile the source** | Ranged header reads; check the hazard table (multiLine, cp1252, phantom `_c\d+` columns, mixed date formats, sentinels, non-unique keys, no modified column). | [SKILL.md:454-478](../.claude/skills/medallion/SKILL.md#L454-L478) |
| 10 | **Name tables** | Derive table names dynamically by sanitizing raw file stems into un-prefixed snake_case names. | [SKILL.md:480-501](../.claude/skills/medallion/SKILL.md#L480-L501) |
| 11 | **Decide the approval case** | Bronze/Silver: sanitized source headers vs. target columns minus audit columns. A = no notebook, B = changed, C = unchanged. An mtime change is not a schema change. | [SKILL.md:243-305](../.claude/skills/medallion/SKILL.md#L243-L305) |
| 12 | **Generate the notebook** | One notebook per LOB per layer; a `parameters` cell with names, never GUIDs; ids resolved at runtime with `notebookutils.lakehouse.get`; per-table failure capture; `notebook.exit(...)`. Checked against every failure-registry entry before display. | [SKILL.md:387-422](../.claude/skills/medallion/SKILL.md#L387-L422), [SKILL.md:773-825](../.claude/skills/medallion/SKILL.md#L773-L825) |
| 13 | **Approval gate** | Cases A/B: show the full notebook (A) or the diff (B) and ask the layer-specific question. Case C: print the fixed line and run. Provisioning never needs approval; the orchestrator needs its own. | [SKILL.md:247-321](../.claude/skills/medallion/SKILL.md#L247-L321) |
| 14 | **Deploy** | `POST notebooks` (ipynb, InlineBase64) or `updateDefinition`; poll the LRO to `Succeeded`; read the definition back and grep for a unique string (FL-007). | [SKILL.md:433-447](../.claude/skills/medallion/SKILL.md#L433-L447), [SKILL.md:821-825](../.claude/skills/medallion/SKILL.md#L821-L825) |
| 15 | **Execute** | `POST jobs/instances?jobType=RunNotebook`, then poll. `NotStarted` for 30+ minutes can be capacity queueing (FL-015); check `livySessions`. | [SKILL.md:442-452](../.claude/skills/medallion/SKILL.md#L442-L452) |
| 16 | **Validate and report** | *The tables are created/updated in the \<layer\> layer* plus per-table row counts (`skipped` shown). Then the handoff question, only after success, asked once for all LOBs. | [SKILL.md:111-137](../.claude/skills/medallion/SKILL.md#L111-L137) |
| 17 | **Failure handling** | Read `Files/_logs/<stage>_<run_id>.log`, match it against the registry, apply the recorded fix. For a new failure, fix it and append a registry entry before re-running. | [SKILL.md:788-808](../.claude/skills/medallion/SKILL.md#L788-L808), [failure_registry.md:15-24](../.claude/skills/medallion/failure_registry.md#L15-L24). Logs exist for automobile and marine runs **[live]** |
| 18 | **Business rules intake (Silver)** | Check `registered_business_rules.md`, then ask one of two exact lines. On a document: *Business Rule document received...*; on registered rules: *Processing with the registered Business Rules.* | [SKILL.md:139-195](../.claude/skills/medallion/SKILL.md#L139-L195) |
| 19 | **Silver build** | One commented block per rule id; blocks derived from generic logic are marked *basic*; the rules outrank the basic logic; closed column contract; counts go to `dbo.dq_rule_results`. | [SKILL.md:197-221](../.claude/skills/medallion/SKILL.md#L197-L221), [SKILL.md:556-635](../.claude/skills/medallion/SKILL.md#L556-L635), [basic_transformation_logic.md](../.claude/skills/medallion/basic_transformation_logic.md) |
| 20 | **Register rules** | Only after an uploaded document: offer to overwrite `registered_business_rules.md`. | [SKILL.md:223-241](../.claude/skills/medallion/SKILL.md#L223-L241) |
| 21 | **Gold** | Case decided by grain fingerprint. A: profile → model review → YAML + notebook → approval. B: YAML diff, notebook diff and a grain-change explanation. C: run. The notebook runs gates 1–4. Then register the model. | [SKILL.md:637-708](../.claude/skills/medallion/SKILL.md#L637-L708), [gold_grain_modelling.md](../.claude/skills/medallion/gold_grain_modelling.md), [grain_profile.py](../.claude/skills/medallion/grain_profile.py) |
| 22 | **Semantic model** | Runs automatically after a successful, registered Gold run. Rules S1–S10 → `semantic_model:` block → TMDL → `POST semanticModels` → reframe → DAX verification → register. | [SKILL.md:710-732](../.claude/skills/medallion/SKILL.md#L710-L732), [semantic_model_generation.md](../.claude/skills/medallion/semantic_model_generation.md). `Marine_Gold_Model` exists **[live]** |
| 23 | **Orchestrator** | `<Lob>_Medallion_Orchestrator` from the template: Bronze → Silver → Gold → `Switch` on the Gold exit status → `Refresh_Semantic_Model`. Needs separate approval. | [SKILL.md:734-749](../.claude/skills/medallion/SKILL.md#L734-L749), [orchestrator_template.json](../.agents/templates/orchestrator_template.json). `Marine_Medallion_Orchestrator` matches the template activity for activity **[live]** |

### 8.1 Layer implementation details (Track A)

**Bronze (`Bronze_<Lob>`)**

| Aspect | Implementation | Source |
|---|---|---|
| Sources | `<Source_Lakehouse>/Files/<LobFolder>/<yyyy>/<MM>/<dd>/*.csv`, today only. Automobile: 4 files; marine: 2 files (folder `Marine`) **[live]** | [automobile SKILL.md:187-194](../.agents/skills/automobile_medallion/SKILL.md#L187-L194), [marine SKILL.md:189-199](../.agents/skills/marine_medallion/SKILL.md#L189-L199) |
| Read options | all columns string; `multiLine=true` by default; per-file encoding (cp1252 for `auto_broker` and `marine_policy`) | [SKILL.md:465-478](../.claude/skills/medallion/SKILL.md#L465-L478) |
| Column naming | `sanitize()`; phantom columns dropped by testing the **raw** `_c\d+` name; source spellings kept | [SKILL.md:523-549](../.claude/skills/medallion/SKILL.md#L523-L549) |
| Load modes | `initial` / `full` → overwrite; `snapshot` → skip if file mtime unchanged, else overwrite. No MERGE (FL-009) | [SKILL.md:503-521](../.claude/skills/medallion/SKILL.md#L503-L521) |
| Incremental logic | Watermark = **source file mtime**; no row-level filters. Example: marine run `20260924073107_e698f0b5` recorded both tables `Skipped` **[live]** | [SKILL.md:475](../.claude/skills/medallion/SKILL.md#L475), [SKILL.md:505-512](../.claude/skills/medallion/SKILL.md#L505-L512) |
| Load control | Live schema: `run_id, stage, table_name, status, load_mode, rows_written, watermark_value, started_at, ended_at, error_message, rule_ids, rules_hash, grain_fingerprint, model_version, source_version`. `started_at`/`ended_at` are **strings**. 44 rows in marine **[live]** | spec at [SKILL.md:552-554](../.claude/skills/medallion/SKILL.md#L552-L554) |
| Live tables | `Automobile_LH.Bronze`: `auto_policy`, `auto_claim`, `auto_broker`, `auto_facility_insurer`. `Marine_LH.Bronze`: `marine_policy`, `marine_claim` **[live]** | |

**Silver (`Silver_<Lob>`)**

| Aspect | Implementation | Source |
|---|---|---|
| Rule priority | 1. business rules; 2. Bronze contracts; 3. Silver column contract; 4. `basic_transformation_logic.md`; 5. failure registry (cross-cutting) | [basic_transformation_logic.md:17-45](../.claude/skills/medallion/basic_transformation_logic.md#L17-L45) |
| Generic cleansing | trim, blank → NULL (configurable `N/A`/`UNKNOWN`), identifiers stay strings, regex-gated date parsing, `DECIMAL` money, booleans only when identified, no FX, an invalid value never becomes 0 or FALSE | [basic_transformation_logic.md:106-411](../.claude/skills/medallion/basic_transformation_logic.md#L106-L411) |
| DQ outcome storage | Rows never marked or dropped; per-rule counts → `dbo.dq_rule_results`; aggregated conversion failures → `dbo.transformation_exceptions`. Marine `dbo` has both; automobile only `dq_rule_results` **[live]** | [SKILL.md:586-635](../.claude/skills/medallion/SKILL.md#L586-L635), [basic_transformation_logic.md:390-411](../.claude/skills/medallion/basic_transformation_logic.md#L390-L411) |
| Load semantics | overwrite + `overwriteSchema`; skip only when `source_version` **and** `rules_hash` are unchanged | [SKILL.md:556-584](../.claude/skills/medallion/SKILL.md#L556-L584) |
| `rules_hash` recipe | `sha256(json.dumps([rules_version] + [[rule_id, status] ...], sort_keys=True))[:16]` | [automobile registered_business_rules.md:13-17](../.agents/skills/automobile_medallion/registered_business_rules.md#L13-L17) |

**Where the Silver rules come from, per LOB**

| LOB | Rules that actually drive Silver | Background reference (not executed directly) |
|---|---|---|
| automobile | [`registered_business_rules.md`](../.agents/skills/automobile_medallion/registered_business_rules.md): `BRD-1.0-2026-09-16`, hash `a0a6ef40f17b9097`, 34 rules (`BR-POL/CLM/BRK/FAC/INT/REG/FIN-*`): 13 RUN, 10 PARTIAL, 11 BLOCKED | [`business_rules.md`](../.agents/skills/automobile_medallion/business_rules.md) (`AUT-BR-*`), [`dq_rules.md`](../.agents/skills/automobile_medallion/dq_rules.md), [`relationships.md`](../.agents/skills/automobile_medallion/relationships.md) |
| marine | [`registered_business_rules.md`](../.agents/skills/marine_medallion/registered_business_rules.md): `MAR-BRS-1.0-2026-09-23`, hash `81b8b88bda770bcc`, 45 rules (`MAR-POL/CLM/XREF/GOLD-*`): 31 RUN, 8 PARTIAL, 6 Gold-deferred | `business_rules.md` (`BR-001..070`), `dq_rules.md` (`DQ-001..075`), `relationships.md` (`REL-*`, `AI-REL-*`) |
| home | none registered (placeholder) | `business_rules.md`, `dq_rules.md`, `relationships.md` |
| aviation | none registered (placeholder) | `business_rules.md` (`BR-001..057`), `dq_rules.md` (`DQ-001..048`), `relationships.md` |

The IDs in a registered file come from the uploaded document, not from the generic `business_rules.md`
(for example `BR-POL-001` vs. `AUT-BR-POL-001`).

**Gold (`Gold_<Lob>`)**

| Aspect | Implementation | Source |
|---|---|---|
| Grain discovery | `grain_profile(df, cfg)`: row types → minimal grain key → functional dependencies (`fd_threshold` 0.995, `fd_min_groups` 30) → additivity (`ROW` or `REPEATS_WITHIN:<parent>`) → surprises. `grain_links()` gives cross-table match %, cardinality and fan-out | [grain_profile.py:288-451](../.claude/skills/medallion/grain_profile.py#L288-L451), [gold_grain_modelling.md:93-165](../.claude/skills/medallion/gold_grain_modelling.md#L93-L165) |
| Fingerprint | `sha256(canonical structure JSON)[:16]`, excluding counts and values; `GRAIN_PROFILE_VERSION = "1.2"` | [grain_profile.py:26](../.claude/skills/medallion/grain_profile.py#L26), [:454-463](../.claude/skills/medallion/grain_profile.py#L454-L463) |
| Notebook gates | skip check → grain guard → `CREATE SCHEMA` → build → `GOLD-RECON-*` | [gold_grain_modelling.md:297-341](../.claude/skills/medallion/gold_grain_modelling.md#L297-L341), skeleton [gold_notebook_template.py](../.agents/templates/gold_notebook_template.py) |
| Live notebook (marine) | `Gold_Marine`, 12 cells; `parameters` cell with names only; MODEL cell pins `MODEL_VERSION = "2.0.0"` and `APPROVED_FINGERPRINT = "353916f47265cf05"`; `grain_profile.py` 1.2 embedded; exits with `status` ∈ `Succeeded / SKIPPED / GRAIN_DRIFT` **[live]** | |
| Relationships | Taken from the profile; `relationships.md` supplies names and expectations only. Joins that fan out are rejected (marine claim→policy on `policy_no`: fan-out 1.9095) | [marine gold_model.yaml:289-291](../.agents/skills/marine_medallion/gold/gold_model.yaml#L289-L291) |
| Registered model (marine) | v2.0.0 `REGISTERED` 2026-09-23, SCD1, all 10 tables present, superseded v1 facts absent **[live]** | [gold_model.yaml](../.agents/skills/marine_medallion/gold/gold_model.yaml) |
| Semantic model (marine) | `Marine_Gold_Model`, hash `27bfb26324b26691`, registered 2026-09-24; the item description quotes the same hash **[live]** | [gold_model.yaml:304-1425](../.agents/skills/marine_medallion/gold/gold_model.yaml#L304-L1425) |

---

## 9. Other implementations (Tracks B and C)

Three Bronze implementations exist in the workspace, and they **do not agree**. Only Track A has
Silver and Gold on top of it.

| Track | Where defined | Target | Status |
|---|---|---|---|
| **A. Medallion skill** (this guide) | `.claude/skills/medallion/` + LOB Source Registries | `<Lob>_LH.Bronze.<lob_code>_<entity>` | current; automobile and marine loaded **[live]** |
| **B. `MCP_Claude/` pipeline** | [`MCP_Claude/`](../MCP_Claude) | `Bronze_Layer.<file-derived name>` (e.g. `claim_details`) | earlier work, still deployed **[live]** |
| **C. "Strict Raw_LH Lakehouse Isolation"** | **not in this repo** | unknown | items `00_Automobile_Medallion_Orchestrator`, `Bronze_Ingestion_Automobile`, `Silver_Transformations_Automobile`, `Gold_Dimensional_Model_Automobile` exist **[live]**; origin **[unknown]** |

### 9.1 Track B: `MCP_Claude/` (`PL_Raw_To_Bronze_Ingestion`)

```text
  Raw lakehouse: Files/Automobile Dataset/*.csv
        │
        ▼
  PL_Raw_To_Bronze_Ingestion  (Fabric pipeline)
        │
        ▼
  Lookup_Load_Config          reads Bronze_Layer.load_control (config + state)
        │
        ▼
  ForEach_Source_Table        sequential, one iteration per CSV
        │
        ▼
  If_Initial_Load             force_load_type = 'initial'  OR  load_status ≠ 'SUCCESS' ?
        │
        ├── yes ──► Ingest_Initial      ┐  both run NB_Raw_To_Bronze_Ingest
        └── no  ──► Ingest_Incremental  ┘
                          │
                          ▼  on Succeeded
                    Commit_Load_State_*       NB_Bronze_Update_Load_Control writes the new watermark
                          │
                          ▼
                    Bronze_Layer.<table>  +  load_control updated
```

| Aspect | Implementation | Source |
|---|---|---|
| Source | `Raw` lakehouse, `Files/Automobile Dataset/` (4 CSVs) **[live]** | [nb_setup_load_control.py:22](../MCP_Claude/notebooks/nb_setup_load_control.py#L22) |
| Target | `Bronze_Layer`: `claim_details`, `policy_details`, `broker_data_with_toba_fields`, `broker_data_with_facility_names`, `load_control` **[live]** | [nb_setup_load_control.py:35-80](../MCP_Claude/notebooks/nb_setup_load_control.py#L35-L80) |
| Load control | Combined **config + state** table, one row per source. Uses sentinel strings instead of NULL (`(not applicable)`, `(pending first load)`, `(none)`, `NOT_LOADED`) | [nb_setup_load_control.py:24-100](../MCP_Claude/notebooks/nb_setup_load_control.py#L24-L100) |
| Pipeline activities | As diagrammed; initial when `force_load_type=='initial'` or `load_status != 'SUCCESS'`; all notebook activities share `sessionTag` `adrosonic_bronze_ingest` | [deploy_bronze_ingestion.py:115-214](../MCP_Claude/deploy_bronze_ingestion.py#L115-L214) |
| Incremental logic | Watermark pre-filter `wm >= last_wm`, then a **row-hash anti-join** against existing Bronze, and the rest **appended**. The facility file has no watermark, so it is always a full-scan anti-join. A changed source row is appended as a new version | [nb_raw_to_bronze_ingest.py:181-238](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L181-L238) |
| Watermark safety | Ingest returns `proposed_watermark`; commit writes it only if `status==SUCCESS` and `validation.passed`. On failure: `load_status='FAILED'` and re-raise | [nb_raw_to_bronze_ingest.py:273-291](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L273-L291), [nb_update_load_control.py:19-51](../MCP_Claude/notebooks/nb_update_load_control.py#L19-L51) |
| Column naming | Source names **kept** (spaces, `(`, `%`) via Delta column mapping `name` mode | [nb_raw_to_bronze_ingest.py:59-62](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L59-L62), [:226-236](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L226-L236) |
| Audit columns | `load_timestamp`, `source_table`, `load_type` | [nb_raw_to_bronze_ingest.py:210-213](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L210-L213) |
| Validation | In-notebook row-count, column-presence and metadata-null checks | [nb_raw_to_bronze_ingest.py:245-271](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L245-L271) |

**Track A and Track B are not interchangeable.** They differ in lakehouse, table names, column
names, audit columns, `load_control` schema and write semantics (overwrite vs. append). Nothing
reads `Bronze_Layer` downstream **[code]**.

### 9.2 Track C

Four automobile items labelled "Strict Raw_LH Lakehouse Isolation" exist in Fabric, but nothing in
this repo generates them. Where they came from, and whether they are still used, is an open question (§14.3).

---

## 10. Agents & skills catalogue

### 10.1 Agents

| Agent | Location | Loaded by | Status |
|---|---|---|---|
| `fabric` | [`.claude/agents/fabric.agent.md`](../.claude/agents/fabric.agent.md) | Claude Code (appears as a subagent) | ❌ **unfilled template**: placeholder description, tools `Read, Grep, Glob, Bash`, no instructions |
| Insurance Data Engineer | [`.agents/agents/InsuranceDataEngineer.agent.md`](../.agents/agents/InsuranceDataEngineer.agent.md) + [`.agents/AGENTS.md`](../.agents/AGENTS.md) | Not a Claude Code location. Believed to be written for a **previous AI assistant** (links point to `d:/MCP/mcp-antigravity/...`) | ⚠️ **legacy**: 9-phase lifecycle with a single `CONFIRM DEPLOY AND EXECUTE` gate, instead of per-notebook approval; points to a missing `insurance-medallion` skill |
| AutomobileInsuranceMedallion | `skills-for-fabric/agents/AutomobileInsuranceMedallion.agent.md` (**untracked file in the vendor clone**) | unknown | ⚠️ stale (`LH_automobile`, folder `MCP-demo`); references missing `adrosonic-*` skills; lost on the next vendor update |

### 10.2 Skills

| Skill | Location | Trigger | Outputs | Notes |
|---|---|---|---|---|
| **medallion** (the one that runs) | [`.claude/skills/medallion/`](../.claude/skills/medallion) | `START`, or "show/build/generate \<layer\> for \<lob\>" | lakehouse + schema, notebooks `01/02/03/04`, Delta tables, `dbo` logs, `gold_model.yaml`, semantic model, orchestrator, `registered_business_rules.md` | Consistent with `naming_standards.md`, `gold_modelling.md` and `orchestration.md` §4–5. **Overrides** `bronze_patterns.md`, `silver_data_quality.md`, `audit_logging.md`, `error_handling.md`, `notebook_standards.md` (see §13) |
| · `basic_transformation_logic.md` | same folder | every Silver build | generic transforms, marked *basic* | |
| · `failure_registry.md` | same folder | before every notebook display; on every failure | fixes FL-001…FL-017 | |
| · `gold_grain_modelling.md` + `grain_profile.py` | same folder | any Gold work | profile, fingerprint, `gold_model.yaml`, `Gold_<Lob>` | |
| · `semantic_model_generation.md` | same folder | after a registered, successful Gold run | TMDL, `<Lob>_Gold_Model`, `Refresh_Semantic_Model` | defers to vendor `semantic-model-authoring` for mechanics |
| `<lob>_medallion` ×4 | `.agents/skills/{automobile,home,marine,aviation}_medallion/` | read as files by `medallion`; not invocable ([SKILL.md:753-755](../.claude/skills/medallion/SKILL.md#L753-L755)) | bindings, registered rules, `gold_model.yaml` (marine) | defer to `medallion` via the "Medallion Build Contract" |
| Copied vendor skills ×8 | `.agents/skills/{activator,deployment-pipelines-authoring,e2e-medallion-architecture,git-integration-operations,search-consumption,spark,sqldw,variable-library}-cli` | reference only | — | byte-identical to `skills-for-fabric/skills/` v0.3.14. Their `../../common/*.md` links don't resolve under `.agents/` |
| Vendor `semantic-model-authoring` | `skills-for-fabric/skills/semantic-model-authoring/` | referenced for TMDL/REST mechanics | — | apart from `e2e-medallion-architecture` ([SKILL.md:771](../.claude/skills/medallion/SKILL.md#L771)), the only vendor skill the custom flow names |

---

## 11. Scripts reference (`MCP_Claude/`)

All scripts belong to **Track B**. They import [`fabric.py`](../MCP_Claude/fabric.py) and hardcode
workspace `DataSonic 3`, source lakehouse `Raw` and target `Bronze_Layer`
([fabric.py:24-26](../MCP_Claude/fabric.py#L24-L26)). Run them from inside `MCP_Claude/`, because
they use sibling imports. **Every script except `fabric.py` and `check_sql_endpoint.py` writes to Fabric.**

| File | Purpose | How to run | Writes to Fabric |
|---|---|---|---|
| [`fabric.py`](../MCP_Claude/fabric.py) | Helper library: az token cache (10 min), retrying `_request`, `poll_lro`, exact-name `resolve_item`/`find_item`, `onelake_list/read`, `build_ipynb`, `upsert_notebook`, `upsert_pipeline`, `run_job`, `poll_instance`. Windows-only (`shell=True`, [:40-44](../MCP_Claude/fabric.py#L40-L44)) | `python fabric.py` (prints ids) | no |
| [`profile_sources.py`](../MCP_Claude/profile_sources.py) | Stage 0: reads the 4 Raw CSVs, finds watermark candidates | `python profile_sources.py` | creates + runs `NB_Profile_Raw_Sources`; writes `Files/_ingestion/profile.json` |
| [`profile.json`](../MCP_Claude/profile.json) | Output of the above (2026-09-11) | — | — |
| [`deploy_bronze_ingestion.py`](../MCP_Claude/deploy_bronze_ingestion.py) | Builds and deploys 3 notebooks + the pipeline, substituting `__WS__/__RAW__/__BRONZE__` with **GUIDs** | `deploy` · `setup` · `setup reset` | yes; also rewrites local `PL_Raw_To_Bronze_Ingestion.pipeline.json` |
| [`notebooks/nb_setup_load_control.py`](../MCP_Claude/notebooks/nb_setup_load_control.py) | Seeds/refreshes `Bronze_Layer.load_control` (state kept unless `p_reset_state=true`) | via `deploy ... setup` | yes |
| [`notebooks/nb_raw_to_bronze_ingest.py`](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py) | Per-table engine: INITIAL overwrite or INCREMENTAL watermark + anti-join append | pipeline activity | yes |
| [`notebooks/nb_update_load_control.py`](../MCP_Claude/notebooks/nb_update_load_control.py) | Commits watermark and state after a successful ingest | pipeline activity | yes |
| [`PL_Raw_To_Bronze_Ingestion.pipeline.json`](../MCP_Claude/PL_Raw_To_Bronze_Ingestion.pipeline.json) | Snapshot of the deployed pipeline (contains GUIDs). Pipeline exists (id `28c395d8-…`) **[live]** | not run directly | — |
| [`run_pipeline.py`](../MCP_Claude/run_pipeline.py) | Run / attach to / list runs of the pipeline | `python run_pipeline.py` · `initial` · `attach` · `recent` | yes (runs) |
| [`q.py`](../MCP_Claude/q.py) | **Arbitrary** Spark SQL against `Bronze_Layer` through a throwaway notebook. Used by `test_incremental.py` and `final_checks.py` | `python q.py "SELECT ..."` · `-f validate_bronze.sql` | creates + runs `NB_Bronze_Query` |
| [`validate_bronze.sql`](../MCP_Claude/validate_bronze.sql) | Three validation queries | `python q.py -f validate_bronze.sql` | via q.py |
| [`test_incremental.py`](../MCP_Claude/test_incremental.py) | Incremental test. `rewind` **DELETEs** Bronze rows after a cutoff and rewinds watermarks; `verify` checks they come back | `rewind` → `run_pipeline.py` → `verify` | yes, destructive |
| [`incremental_expectations.json`](../MCP_Claude/incremental_expectations.json) | Output of `rewind` (336 / 1,466 / 116 rows) | — | — |
| [`final_checks.py`](../MCP_Claude/final_checks.py) | Acceptance: auto re-run appends 0; initial re-run doesn't duplicate; SQL endpoint item exists | `python final_checks.py` · `1` · `1skiprun` | yes (runs pipeline twice) |
| [`check_sql_endpoint.py`](../MCP_Claude/check_sql_endpoint.py) | Proves tables and spaced/`%` column names are readable over TDS | `python check_sql_endpoint.py` | no (needs `pyodbc` + ODBC Driver 18) |
| [`build_pipeline.ps1`](../MCP_Claude/build_pipeline.ps1) | **Superseded** Copy-activity pipeline generator (hardcoded GUIDs, [:15-17](../MCP_Claude/build_pipeline.ps1#L15-L17)) | `& .\MCP_Claude\build_pipeline.ps1` | no |
| [`Bronze_Copy_Ingestion.pipeline.json`](../MCP_Claude/Bronze_Copy_Ingestion.pipeline.json) | **Superseded** Copy pipeline; not deployed **[live]** | — | — |
| `__pycache__/` | compiled `fabric`, `q` (CPython 3.13) | — | dead artefact |

---

## 12. Configuration & auth

### 12.1 MCP servers

| File | Server | Transport | Used by | Notes |
|---|---|---|---|---|
| [`.mcp.json`](../.mcp.json) | `fabric-mcp-server` | stdio: `npx -y @microsoft/fabric-mcp@latest server start --mode all` | **Claude Code** (project MCP) **[live]** | `@latest` is unpinned. Needs Node.js. Auth comes from the local Azure credential chain **[unknown: exact chain]** |
| [`.vscode/mcp.json`](../.vscode/mcp.json) | `fabric` | HTTP `https://api.fabric.microsoft.com/v1/mcp/core` | VS Code MCP clients (e.g. Copilot) | not read by Claude Code |
| [`.agents/mcp_config.json`](../.agents/mcp_config.json) | `fabric` | same HTTP endpoint | unknown client **[unknown]** | identical to `.vscode/mcp.json`; the old hardcoded token has been removed |
| `skills-for-fabric/.mcp.json` | `FabricIQ`, `powerbi-modeling-mcp`, `fabric-sqlendpoint` | HTTP | vendor; not loaded from the project root | `semantic_model_generation.md` assumes `powerbi-modeling-mcp` is **not** available |

### 12.2 Tokens

| Audience | Used for |
|---|---|
| `https://api.fabric.microsoft.com` | Fabric REST (create, run, poll) ([SKILL.md:429-431](../.claude/skills/medallion/SKILL.md#L429-L431)) |
| `https://storage.azure.com` | OneLake DFS reads ([SKILL.md:460](../.claude/skills/medallion/SKILL.md#L460)) |
| `https://analysis.windows.net/powerbi/api` | semantic model refresh and DAX checks |
| `https://database.windows.net` | `check_sql_endpoint.py` only |

- All tokens come from `az account get-access-token`. The scripts cache each audience for 10 minutes
  and force-refresh on 401 ([fabric.py:31-49](../MCP_Claude/fabric.py#L31-L49), [:79-84](../MCP_Claude/fabric.py#L79-L84)).
- There is no service principal and there are no stored secrets.
- **Secrets scan (24 Sep 2026):** no tokens, keys or passwords in custom files. `.agents/mcp_config.json`
  once held another user's short-lived AAD **access** token. It has been removed and expired long ago,
  so no revocation is needed. Optional hygiene: older versions may still exist in OneDrive *Version
  history*. Escalate only if the file ever held a refresh token or client secret.

### 12.3 Identifiers

**Resolve by name.** These GUIDs are for orientation only. Never copy them into a notebook or skill.

| Item | Name | Id | Evidence |
|---|---|---|---|
| Workspace | `DataSonic 3` | `1296a62d-7e36-4481-a586-686e8d4b0ccc` | [live] |
| LOB lakehouse | `Automobile_LH` | `c8eb3621-a6c5-47ca-850d-d8c0a851e400` | [live] |
| LOB lakehouse | `Marine_LH` | `dc404cfe-ff08-483a-82cc-04c5d9773a3f` | [live] |
| Raw (Track A) | `<Source_Lakehouse>` | not captured | [live] |
| Raw (Track B) | `Raw` | `bcaba904-7010-4377-9804-d61f36c03bec` | code + [live] |
| Bronze (Track B) | `Bronze_Layer` | `a046d38d-0240-4ede-8225-6c2df3fb4338` | code + [live] |
| Semantic model | `Marine_Gold_Model` | `dcd787e0-dd7d-47fd-bb3d-af3669727011` | [live] |
| Workspace folder | `MCP-demo` (per the registered-rules files) | — | [code] |

### 12.4 Environment assumptions

- Windows + PowerShell 5.1 (`shell=True` in `fabric.py`).
- Python 3.12/3.13. There's **no `requirements.txt`**; the standard library is enough except for `pyodbc`.
- Capacity in the Southeast Asia region. The trial/small SKU queues Spark jobs (FL-015).
- Several people edit the workspace live, so names are re-resolved on every run.

---

## 13. Standards vs. skill vs. reality

The older standards in `.agents/common/` predate the medallion skill. **Where they disagree, the
medallion skill is authoritative.**

| Topic | `.agents/common/*` standard | Medallion skill (authoritative) | Actually implemented / observed |
|---|---|---|---|
| Lakehouse | `<Lob>_LH`, one per LOB ([naming_standards.md:11](../.agents/common/naming_standards.md#L11)) | same | Track A ✅ [live]; Track B uses `Raw`/`Bronze_Layer` |
| Notebooks | `Bronze_<Lob>` … ([naming_standards.md:13-15](../.agents/common/naming_standards.md#L13-L15)); orchestration diagram still shows per-entity `Bronze_Policy` ([orchestration.md:11-34](../.agents/common/orchestration.md#L11-L34)) | one per LOB per layer | Track A ✅ [live]; Track B `NB_*`; LOB sub-skills say `Bronze_<SourceEntity>` |
| Pipeline | `<LOB>_Medallion_Orchestrator` | same | `Marine_Medallion_Orchestrator` [live] |
| Tables | `<lob_code>_<entity>`; Gold `<lob_code>_dim_/_fact_` | same | ✅ Track A [live]; Track B uses file-derived names |
| Bronze audit columns | `_source_file, _ingestion_timestamp, _batch_id` ([bronze_patterns.md:11-14](../.agents/common/bronze_patterns.md#L11-L14)) | + `_source_mtime` | Track B: `load_timestamp, source_table, load_type` |
| Bronze writes | initial overwrite + incremental **append** ([bronze_patterns.md:32-55](../.agents/common/bronze_patterns.md#L32-L55)) | **overwrite only**; mtime skip | Track A overwrite; Track B append + anti-join |
| Silver | snake_case renames, **SCD2**, `_transformation_timestamp`, `dq_decision_log` ([silver_data_quality.md:10-21](../.agents/common/silver_data_quality.md#L10-L21), [:66-83](../.agents/common/silver_data_quality.md#L66-L83)) | no renames, closed contract, no SCD, `dbo.dq_rule_results` | medallion ✅ [live]; [silver template](../.agents/templates/silver_notebook_template.py) still implements SCD2 |
| `load_control` | `table_name, layer, batch_id, load_type, watermark_column, ... execution_status` ([audit_logging.md:11-26](../.agents/common/audit_logging.md#L11-L26)) | `run_id, stage, table_name, status, load_mode, ...` | live schema matches the skill plus extra columns [live]; Bronze/Silver templates write the old schema |
| Error log path | `Files/_debug/last_run_error.txt` ([error_handling.md:15](../.agents/common/error_handling.md#L15)) | `Files/_logs/<stage>_<run_id>.log` (FL-006) | `_logs` ✅ [live], written on **every** run, not only on failure |
| Error exit | `notebook.exit({"status":"FAILED",...})` then raise | capture per table, write log, re-raise | Track B deliberately doesn't exit on failure ([nb_raw_to_bronze_ingest.py:285-288](../MCP_Claude/notebooks/nb_raw_to_bronze_ingest.py#L285-L288)) |
| Orchestration | `batch_id=@pipeline().RunId`, retry 0, `Switch` on `exitValue.status` ([orchestration.md:48-69](../.agents/common/orchestration.md#L48-L69)); load_type `auto/initial/incremental` | resume from the failed stage ([SKILL.md:736-739](../.claude/skills/medallion/SKILL.md#L736-L739)) | Live `Marine_Medallion_Orchestrator`: default `start_from_stage="bronze"`, **no automatic resume**; accepts `auto/initial/full/snapshot`, **rejects `incremental`** ([orchestrator_template.json:6-22](../.agents/templates/orchestrator_template.json#L6-L22)) [live] |
| Utilities | `notebookutils` | `notebookutils` with `mssparkutils` fallback | Track B uses `mssparkutils.notebook.exit` |

---

## 14. Known gaps, risks & open questions

### 14.1 Ranked findings

**Critical**

1. **Three Bronze implementations coexist with incompatible contracts** (Tracks A, B, C; §9). They
   differ in names, audit columns, `load_control` schema and write mode. Nobody can tell from the repo
   which one is authoritative for automobile, and the owner isn't sure either (24 Sep 2026).
   **Decision outstanding.**
2. **The runtime code is not under version control.** The project root isn't a git repo and sits
   in OneDrive. Notebooks are never stored by design ([SKILL.md:827-853](../.claude/skills/medallion/SKILL.md#L827-L853)),
   and the spec files are overwritten in place. The live notebooks and orchestrator exist only in a
   workspace that several people edit.

**High**

3. **The stale standards would build the wrong system if followed.** `.agents/AGENTS.md`,
   `InsuranceDataEngineer.agent.md`, `common/{bronze_patterns, silver_data_quality, audit_logging,
   error_handling, notebook_standards}.md`, the Bronze/Silver templates, and every LOB `bronze/` and
   `silver/` sub-skill (plus the automobile/home/aviation `gold/` sub-skills) still prescribe
   per-entity notebooks, append/MERGE, SCD2 in Silver, `Files/_debug` and a different `load_control`
   schema ([AGENTS.md:140](../.agents/AGENTS.md#L140)).
4. **The medallion skill is wrong about marine.** It says only automobile has registered rules
   ([SKILL.md:155-156](../.claude/skills/medallion/SKILL.md#L155-L156)), but marine has a full set
   and a registered Gold model.
5. **Supposedly read-only helpers write to Fabric.** `q.py` runs arbitrary SQL, DML included, and
   `profile_sources.py` creates and runs a notebook. `test_incremental.py rewind` deletes Bronze rows.
   None of them asks for confirmation.
6. **Hardcoded GUIDs and names** in [`build_pipeline.ps1:15-17`](../MCP_Claude/build_pipeline.ps1#L15-L17),
   both pipeline JSONs, the deployed Track B notebooks ([deploy_bronze_ingestion.py:33-35](../MCP_Claude/deploy_bronze_ingestion.py#L33-L35))
   and `hdr*.txt`. This breaks the project's own "a stored GUID is a defect" rule.

**Medium**

7. **Broken references:** LOB skills link to `file:///d:/MCP/mcp-antigravity/...` and
   `file:///c:/Users/nikhi/...` ([SKILL.md:764-767](../.claude/skills/medallion/SKILL.md#L764-L767)).
   Vendor copies link to missing `../../common/COMMON-*.md`, and `AGENTS.md` loads a missing
   `insurance-medallion/SKILL.md`. Automobile's registered rules point to a SKILL.md section that
   now lives in `failure_registry.md` ([registered_business_rules.md:197-198](../.agents/skills/automobile_medallion/registered_business_rules.md#L197-L198)).
8. **`.claude/agents/fabric.agent.md` is an unfilled template.** Because it's registered as a
   subagent, it can be picked by mistake.
9. **A project file sits in the vendor clone:** `skills-for-fabric/agents/AutomobileInsuranceMedallion.agent.md`
   is untracked, so it'll be lost on update.
10. **LOB SKILL.md files contradict the skill on Gold provisioning.** They say "show me the gold →
    create `Tables/Gold`" ([automobile SKILL.md:105](../.agents/skills/automobile_medallion/SKILL.md#L105))
    against "create nothing" ([SKILL.md:379-382](../.claude/skills/medallion/SKILL.md#L379-L382)).
    Their prompt strings also differ from the skill's.
11. **`gold_model.yaml` shape drift:** the spec says `entities:` map
    ([gold_grain_modelling.md:361-375](../.claude/skills/medallion/gold_grain_modelling.md#L361-L375)),
    while marine uses `dimensions:`/`facts:` lists.
12. **Three MCP configs, one unpinned** (`@microsoft/fabric-mcp@latest`).
13. **Portability:** `fabric.py`'s `subprocess.run(list, shell=True)` only works on Windows.
14. **Raw folder case:** marine's folder is `Marine`, but the LOB mapping is lower-case
    ([marine SKILL.md:191-192](../.agents/skills/marine_medallion/SKILL.md#L191-L192)). It works
    only because the model lower-cases it.
15. **Track B keeps multiple versions per business row** (changed rows are appended), and no consumer dedupes them.
16. **SQL built by string concatenation** in Track B notebooks. Exposure is low because the inputs come from the control table.
17. **The orchestrator doesn't match the skill** **[live]**. There's no automatic resume
    (`start_from_stage` defaults to `bronze`), and `load_type=incremental` fails validation. The
    repo's Gold **template** exits without `status` ([gold_notebook_template.py:74](../.agents/templates/gold_notebook_template.py#L74)),
    so a Gold notebook regenerated from it for a new LOB would break the `Switch`. The live
    `Gold_Marine` is fine.

**Low**

18. **Dead or stale files:** `hdr.txt`, `hdr2.txt`, `__pycache__/` folders, `build_pipeline.ps1` +
    `Bronze_Copy_Ingestion.pipeline.json`, and the run outputs `profile.json` and `incremental_expectations.json`.
    Live leftovers: `transformation_NB`, `NB_Bronze_Query`, `NB_Bronze_Incremental_Rewind`, `NB_Profile_Raw_Sources`.
19. **No automated tests** for `grain_profile.py` or `sanitize()`, and no `requirements.txt`.
20. **Silver template defects** (stale anyway) ([silver_notebook_template.py:62](../.agents/templates/silver_notebook_template.py#L62), [:76](../.agents/templates/silver_notebook_template.py#L76)).
21. **Automobile `dbo` has no `transformation_exceptions` table** [live], because automobile Silver
    predates that rule.
22. **Vendor telemetry header** `x-ms-fabric-skill` is not sent by `fabric.py` or the skill's curl examples.

### 14.2 `PROJECT_OVERVIEW.md` vs. the code

> **Note:** `PROJECT_OVERVIEW.md` is **no longer in the repository** (checked 24 Sep 2026). This
> table is kept in case a copy exists elsewhere. If it's gone for good, delete this section.

| # | Overview says | Code / live state |
|---|---|---|
| 1 | "Last verified 9 September 2026" | Silver, Gold and a semantic model were built since (22–24 Sep) [live] |
| 2 | `.agents/skills/` holds 13 skills including 5 `adrosonic-*` | 12 folders: 4 `*_medallion` + 8 vendor copies; no `adrosonic-*` |
| 3 | Repo layout omits `.claude/` | `.claude/skills/medallion` is the main skill |
| 4 | `MCP_Claude/` = `build_pipeline.ps1` + one JSON | 17 files + `notebooks/` (§11) |
| 5 | `skills-for-fabric/agents/` has 5 personas | 6 files; one is an untracked project file |
| 6 | `.agents/mcp_config.json` has a stale token; no `.mcp.json` | No token now; root `.mcp.json` configures `fabric-mcp-server` |
| 7 | "Fabric MCP server wired into Claude Code ❌" | Wired via `.mcp.json` [live] |
| 8 | Lakehouses: `Raw`, `Bronze_Layer`, … | Active flow uses `<Source_Lakehouse>` and `<Lob>_LH` |
| 9 | Silver, Gold, semantic model "NOT BUILT" | Automobile Silver; marine Silver + Gold + model [live] |
| 10 | Bronze audit cols `_ingestion_timestamp, _load_type, _source_table` | Track B: `load_timestamp, source_table, load_type`; Track A: `_source_file, _ingestion_timestamp, _batch_id, _source_mtime` |
| 11 | `load_control` columns `load_type_last_run, watermark_column, …` | Neither track matches |
| 12 | Detail in `adrosonic-raw-to-bronze-ingestion/SKILL.md` | File doesn't exist |
| 13 | `transformation_NB` is both "source of truth" and "superseded" | Self-contradictory; not in the repo (still live) |
| 14 | `Bronze_Copy_Ingestion_Pipeline` deployed | Not in the workspace [live] |
| 15 | All PySpark in one notebook `transformation_NB` | One notebook per LOB per layer |
| 16 | Failed records go to `<table>_quarantine` | No quarantine; counts go to `dbo.dq_rule_results` |
| 17 | The BI skill must never deploy anything | `semantic_model_generation.md` deploys after approval |
| 18 | raw-to-bronze does "no renaming" yet "sanitizes to snake_case" | Track B keeps names; Track A sanitizes |
| 19 | Facility phantom columns kept as `c6/c7/c8` | Both engines drop them (FL-010) |
| 20 | §7.5 cites `adrosonic-*` line numbers | Files don't exist |
| 21 | "Rebuild and redeploy" = `build_pipeline.ps1` | Superseded; current is `deploy_bronze_ingestion.py deploy` |
| 22 | "Where to start reading" lists `adrosonic-*` | Start with `.claude/skills/medallion/SKILL.md` |
| 23 | "the only workspace of the seven visible" | 4 visible to the reviewing identity [live] **[unknown]** |

### 14.3 Open questions and decisions

**Resolved on 24 Sep 2026**

| Question | Outcome |
|---|---|
| Does the live Gold notebook emit the `status` the orchestrator switches on? | **Yes** (finding 17) |
| Was the old token in `.agents/mcp_config.json` revoked? | Not needed: it was a short-lived access token, long expired (§12.2) |
| Is `.agents/AGENTS.md` / `InsuranceDataEngineer.agent.md` still used? | Believed to be for a previous AI assistant. Treat it as legacy |

**Still open**

- **Which Bronze track is authoritative for automobile** (A, B or C)? Suggested default: Track A,
  because it's the only one with Silver on top and the only one the current skill maintains.
- Where Track C came from and whether it's still used.
- Whether `Marine_Medallion_Orchestrator` has ever run end to end (job history not read).
- Which client, if any, reads `.agents/mcp_config.json`.
- The Livy-session mechanics used for grain profiling (not written down).
- What item `1d5d645b-…` in `hdr*.txt` was.

---

## 15. Glossary

| Term | Meaning |
|---|---|
| **LOB** | Line of business: automobile, home, marine, aviation. Each has one raw folder, one skill folder and one lakehouse |
| **Medallion** | The Bronze (raw copy) → Silver (clean) → Gold (modelled) layering pattern |
| **`<Source_Lakehouse>`** | Shared raw lakehouse; each `Files/<lob>/` subfolder is a LOB, holding one `<yyyy>/<MM>/<dd>/` folder per day |
| **`<Lob>_LH`** | Schema-enabled lakehouse per LOB holding `Bronze`, `Silver`, `Gold`, `dbo` |
| **Skill** | A Markdown instruction file Claude Code loads and follows |
| **MCP** | Model Context Protocol: how Claude Code gets tools such as `fabric-mcp-server` |
| **Handshake** | The fixed 4-question opening of the medallion skill |
| **Case A / B / C** | New notebook (approve) / changed input (approve the diff) / unchanged (run, no approval) |
| **`sanitize()`** | The Bronze column-naming contract; changing it renames every downstream column |
| **Snapshot / full / initial** | Bronze load modes; all overwrite, and `snapshot` skips when the file mtime is unchanged |
| **Registered business rules** | `registered_business_rules.md`: the approved rule set, its hash and data-specific pins. Silver is regenerated from it |
| **`rules_hash`** | 16-hex hash of the rules version + rule statuses; together with `source_version`, it decides the Silver skip |
| **Silver column contract** | Closed list: business columns + 4 Bronze audit + `_silver_run_id`, `_silver_timestamp` |
| **RUN / PARTIAL / BLOCKED / GOLD** | Rule statuses: fully evaluated / evaluated without some marker or reference data / cannot run / deferred to Gold |
| **`dq_rule_results`** | `dbo` log of per-rule and reconciliation counts |
| **`transformation_exceptions`** | `dbo` log of aggregated conversion failures |
| **Grain / grain key** | What one row means; the minimal columns that make a row unique |
| **Row type / discriminator** | A subset of rows with a distinct null pattern, and the column that identifies it |
| **Additivity (`ROW`, `REPEATS_WITHIN:p`)** | Whether a measure can be summed per row, or only once per parent `p` |
| **Fan-out** | How many rows a join produces per input row; must be 1.0 for Gold joins |
| **Grain fingerprint** | `sha256` of the structural profile; a change forces Gold Case B, and at runtime it triggers `GRAIN_DRIFT` |
| **G1–G10 / S1–S10** | Gold modelling rules / semantic-model generation rules |
| **SCD1 / SCD2** | Slowly changing dimension: overwrite history / keep history as rows |
| **`UNKNOWN` member** | Dimension row (sk = sha256('UNKNOWN')) that orphan or null foreign keys point to |
| **FL-0NN** | Failure-registry entry id |
| **Direct Lake / reframe** | Power BI mode that reads Delta directly; a refresh re-points it at the latest Delta version |
| **TMDL** | Tabular Model Definition Language: the text format of the semantic model definition |
| **LRO** | Fabric long-running operation (`202` + `Location`, poll `/operations/{id}`) |
| **Livy session** | A Spark session opened over the API; used for grain profiling |
| **Track A / B / C** | Medallion-skill implementation / `MCP_Claude` Bronze_Layer pipeline / unexplained "Strict Raw_LH" items |
| **Row-hash anti-join** | Track B incremental dedupe: keep only rows whose SHA-256 hash isn't already in Bronze |
