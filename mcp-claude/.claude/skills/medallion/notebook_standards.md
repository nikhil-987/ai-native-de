# Notebook Standards (Senior Data Engineering Specification)

How every generated notebook is **laid out, commented and formatted**: Bronze, Silver, Gold, and the shared semantic-model refresh notebook. `SKILL.md`, `basic_transformation_logic.md` and `gold_grain_modelling.md` say *what* a notebook does. This file says *how it reads*.

> **Core Engineering Philosophy:** *Bronze preserves. Silver trusts. Gold explains.*

It is dataset-independent. A new dataset target inherits it with no edit.

---

## 1. Common Notebook Structure & Single-Responsibility Cell Principle

Every production notebook is structured around two core engineering principles:

1. **Per-Layer Narrative Step-by-Step Flow**: Logical progression moving from raw data collection to cleansing, business rule application, validation assertions, schema creation, Delta table writing, and exit telemetry.
2. **Single-Responsibility Cell Principle (One Cell = One Logic)**: Every distinct logical step is placed in its **own dedicated Python code cell**, preceded by its **own dedicated Markdown Sub-Header Cell**. Code is **never** smashed into single giant cells.

---

### A. Bronze Layer Notebook Layout (`Bronze_<Target>`)

```text
Section 0  [Markdown] 📌 Notebook Banner & Metadata (Purpose, Source, Target, Load Strategy)
Section 1a [Python]   ⚙️ Imports & Spark Session Setup
Section 1b [Python]   ⚙️ Parameters & Centralized Table/Path Constants
Section 2  [Python]   📥 Collect Data from Raw Source Files (inferSchema=false, ranged header read)
Section 3  [Python]   🔄 Apply Load Strategy (initial/full/snapshot) & Audit Metadata (_source_file, _ingestion_timestamp, _batch_id)
Section 4  [Python]   🏗️ Create & Provision Bronze Tables (CREATE SCHEMA IF NOT EXISTS bronze)
Section 5a [Python]   📤 Write to Bronze Delta Tables & Execute Ingestion Validation Assertions
Section 5b [Python]   ✅ Print Summary Banner & Exit Status Row to dbo.project_status
```

---

### B. Silver Layer Notebook Layout (`Silver_<Target>`)

```text
Section 0  [Markdown] 📌 Notebook Banner & Metadata (Purpose, Business Rules BR-xxx, Target Grain)
Section 1a [Python]   ⚙️ Imports & Spark Session Setup
Section 1b [Python]   ⚙️ Parameters & Centralized Regex/Mask Constants
Section 2  [Python]   📥 Collect Data from Bronze Layer (bronze.<entity>)
Section 3a [Python]   🧹 Data Cleansing & Blank Token Normalization (trim, uppercase, "" -> NULL)
Section 3b [Python]   🔄 Business Transformations (BR-xxx Vertical Method Chaining)
Section 3c [Python]   📅 Safe Type Casting & Regex Date Parsing (rlike guards)
Section 3d [Python]   🪟 Explicit Window Deduplication Logic (orderBy watermark desc)
Section 3e [Python]   🛡️ Drop Temporary Audit Metadata & Validate Closed Schema Contract
Section 4  [Python]   🏗️ Create & Provision Silver Tables (CREATE SCHEMA IF NOT EXISTS silver)
Section 5a [Python]   📤 Write Clean Delta Tables (silver.<entity>)
Section 5b [Python]   ✅ Execute Assertions, Print Summary Banner & Exit Status Row to dbo.project_status
```

---

### C. Gold Layer Notebook Layout (`Gold_<Target>`)

```text
Section 0  [Markdown] 📌 Notebook Banner & Metadata (Purpose, Star Schema Architecture, STTM Mapping, Grain)
Section 1a [Python]   ⚙️ Imports, Spark Session Setup & SHA-256 Key Helper Functions
Section 1b [Python]   ⚙️ Parameters & Centralized Table Constants
Section 2  [Python]   📥 Collect Data from Silver Layer (silver.<entity>)
Section 3  [Python]   🔄 Apply STTM & Business Transformations (Derived Attributes, Mappings)
Section 4  [Python]   📊 Apply Measures & KPIs (Financial Aggregations, Ratio DIVIDE Recomputations)
Section 5a [Python]   🏗️ Build Dimensions (gold.dim_*) with SHA-256 Surrogate Keys (*_sk)
Section 5b [Python]   ➕ Union Synthetic UNKNOWN (-1) Members into Dimension Tables
Section 5c [Python]   🏗️ Build Facts (gold.fact_*) with Foreign Key Lookups
Section 6a [Python]   🏗️ Create & Provision Gold Schema (CREATE SCHEMA IF NOT EXISTS gold)
Section 6b [Python]   🛡️ Fail-Fast Reconciliation Assertions (assert gold_rows == silver_rows & gold_sum == silver_sum)
Section 7a [Python]   📤 Write Dimension & Fact Tables to Gold Delta Schema
Section 7b [Python]   ✅ Print Reconciliation Summary Banner & Exit Status Row to dbo.project_status
```

---

## 2. Configuration Standards

Table names, paths, thresholds, and configurable values are declared explicitly at the top of Section 1 rather than hardcoded in loops:

```python
# ── PARAMETERS & CONFIGURATION ────────────────────────────────────────
target                = "Marine"
source_lakehouse_name = "{raw_lakehouse}"
target_lakehouse_name = "Marine_Medallion_LH"
batch_id              = "{run_id}"

# Explicit Table Constants
SOURCE_TABLE          = "bronze.marine_policy"
TARGET_TABLE          = "silver.marine_policy"
```

---

## 3. Layer-Specific Standards

### A. Bronze Layer (Raw Landing & Ingestion)
* **Goal:** Preserve raw source truth safely without ingestion failures.
* **Rules:**
  1. **All-String Landing:** Read raw files with `inferSchema=false` (all columns as `StringType`). Explicit `StructType` schemas may be used when deterministic schema enforcement is required.
  2. **Single-Point Sanitization:** Apply `sanitize()` once in Bronze (lowercase, spaces/hyphens to `_`, `%` to `pct`). Downstream layers inherit these names.
  3. **Un-Prefixed Table Names:** Write directly to `bronze.<source_stem>`.
  4. **Standard Metadata:** Append `_source_file`, `_ingestion_timestamp`, `_batch_id`.
  5. **Technical Validation:** Assert raw DataFrame is not empty (`assert df.count() > 0`) and required source columns exist before writing.

### B. Silver Layer (Cleansing & Trusted Business Logic)
* **Goal:** Cleanse, standardize types, handle nulls, and enforce business rules.
* **Rules:**
  1. **Closed Schema Contract:** Drop temporary calculation columns before writing to Silver Delta tables.
  2. **Fail-Safe Type Casting:** Use regex-gated parsing (`rlike`) or `try_cast()`.
  3. **Zero Data Fabrication:** `NULL` values must NEVER be converted to `0`, `FALSE`, or arbitrary default dates unless an explicit business rule mandates it.
  4. **Blank Token Normalization:** Convert `""`, `"  "`, `"N/A"`, `"NULL"` to SQL `NULL`.
  5. **Explicit Window Deduplication:** Use window functions (`row_number().over(Window.partitionBy(keys).orderBy(watermark.desc()))`) and comment the rule rationale.
  6. **No `select("*")`:** Explicitly select target columns after multi-table joins.

### C. Gold Layer (Dimensional Star-Schema Modeling)
* **Goal:** Business-ready dimensional models (Dimensions & Facts) optimized for Power BI Direct Lake.
* **Rules:**
  1. **Explicit Grain Declaration:** Top of notebook MUST state: `# Grain: One row per <entity>`.
  2. **Deterministic SHA-256 Surrogate Keys:** Compute `<entity>_sk` using `sha256(concat_ws('||', natural_keys))`. Never use `monotonically_increasing_id()`.
  3. **Synthetic `UNKNOWN` Row:** Union a default `'UNKNOWN'` record into dimension tables to prevent orphan fact joins.
  4. **Automated Grain Integrity Assertion:** Execute pre-write assertion:
     `assert df_gold.count() == df_gold.select("<entity>_sk").distinct().count()`
  5. **Traceable Metrics:** Name measures clearly (`total_premium`, `claim_count`, `loss_ratio`).

---

## 4. Single Control Table Specification (`dbo.project_status`)

The Medallion architecture operates under a **100% Single Control Table Architecture**. All stage execution status, project stage progression, runtime telemetry, and error tracebacks are recorded exclusively in `dbo.project_status` within the Target Lakehouse (`<Target>_LH`). No secondary control tables (such as `dq_rule_results`) or filesystem log directories exist.

```sql
CREATE TABLE dbo.project_status (
    -- Project Scope & Metadata
    project_name           STRING,    -- Target project folder name (e.g. 'Automobile', 'Marine')
    run_id                 STRING,    -- Pipeline/notebook execution GUID
    stage                  STRING,    -- bronze | silver | gold | orchestrator | semantic_model
    artifact_name          STRING,    -- Item name (e.g. 'Bronze_Automobile', 'Marine_Medallion_Orchestrator')
    
    -- High-Level Project Stage & Gate Awareness
    current_project_stage  STRING,    -- 0_INIT | 1_BRONZE | 2_SILVER | 3_GOLD | 4_ORCHESTRATED | 5_COMPLETED
    overall_project_status STRING,    -- IN_PROGRESS | PAUSED_AT_GATE | COMPLETED | FAILED
    current_gate           STRING,    -- Active gate ID (e.g. 'G7a', 'G10a', 'G12c', 'G13c', 'G14c')
    next_action_required   STRING,    -- 'Approve Silver Execution', 'Review Gold STTM Mapping', etc.
    completion_percentage  INT,       -- 0, 20, 40, 60, 80, 100
    
    -- Execution Lifecycle & Audit Telemetry
    status                 STRING,    -- SUBMITTED | RUNNING | COMPLETED | FAILED | SKIPPED | CANCELLED
    load_type              STRING,    -- INITIAL | FULL | INCREMENTAL | SNAPSHOT
    triggered_by           STRING,    -- DE_CHAT_SESSION | FABRIC_ORCHESTRATOR | CRON_SCHEDULE
    started_at             TIMESTAMP, -- Job start timestamp
    updated_at             TIMESTAMP, -- Last update / completion timestamp
    duration_seconds       INT,       -- Runtime duration in seconds
    tables_processed       INT,       -- Number of tables processed in this stage
    records_processed      BIGINT,    -- Input rows processed
    records_failed         BIGINT,    -- DQ exceptions / failed rows
    error_message          STRING,    -- High-level failure reason if FAILED
    log_file_path          STRING     -- Path to diagnostic log file in OneLake
);
```

---

## 5. Error Handling & Performance Standards

1. **No Silent Error Swallowing:** Never use bare `try/except: pass`. Failures must log to `dbo.project_status` with status `'FAILED'` and raise a descriptive exception.
2. **Spark Native Transformations:** Use Spark-native functions (`F.when`, `F.col`); avoid row-by-row Python loops or converting large DataFrames to pandas.
3. **Filter Early:** Apply filter conditions before complex joins.

---

## 6. AI Notebook Generation Principles

When generating notebooks, the AI assistant MUST evaluate inputs using this strict hierarchy:

$$\text{Business Requirements} \rightarrow \text{Business Rules} \rightarrow \text{STTM} \rightarrow \text{Target Grain} \rightarrow \text{DQ Rules} \rightarrow \text{Notebook Standards}$$

### A. Clean Enterprise Code Commenting Standards
- **Engine Guardrails**: The AI assistant MUST apply all engine-level safety patterns from `failure_registry.md` (e.g., date rebase policies, Livy exception handlers, regex date guards, idempotent overwrites).
- **No Internal Tag Output**: The AI assistant MUST NOT emit raw internal tracking tags (such as `# Applied FL-005` or `# Applied FL-009`) into generated notebook code.
- **Enterprise Comments**: Replace internal tags with clean, human-readable PySpark docstrings and comments (e.g., `# Configure PySpark datetime rebase policy to support legacy sentinel dates`).

### B. Dataset vs. Engine Boundary Separation
- **`failure_registry.md`**: Holds generic, engine-level Spark, Delta, and Fabric platform rules. It is **100% dataset-independent**.
- **`registered_business_rules.md`**: Holds dataset-specific rules (encodings, feed-specific date layouts, custom sentinels, business key mappings). Dataset-specific rules belong exclusively in business rules / profiling metadata.

If required business requirements or target grains are underspecified, the AI assistant MUST raise the gap to the user rather than fabricating logic.
