# Client Configuration

Every client-specific setting for the medallion skill lives here. `SKILL.md`, `interface.md` and the method files are generic and 100% zero-config.

**Onboarding a new client or environment means editing this file or `.env`, never `SKILL.md`.** No static dataset/LOB markdown config files are required.

## Precedence

When a setting appears in more than one place, the most specific one wins:

1. the reply given at a gate (for example the workspace selected at G0b, the Target Name selected/typed at G2, or lakehouses picked at G13a/b)
2. environment variables (loaded from `.env` or process environment: `FABRIC_WORKSPACE_ID`, `RAW_LAKEHOUSE_NAME`, etc.)
3. this file (`client_config.md`)
4. dynamic discovery via Azure CLI identity (`az account show`) and Fabric MCP Server (`onelake_list-workspaces`, `onelake_list-items`)

## Settings

```yaml
# ---- portable environment & workspace resolution ------------------------
workspace: ""                       # blank = resolve dynamically from tenant workspace listing at G0b,
                                    # or fallback to FABRIC_WORKSPACE_ID env var
workspace_folder: ""                # blank = workspace root
raw_lakehouse: ""                   # blank = resolved dynamically at runtime when user selects Source Lakehouse at G1
source_timezone: "Asia/Kolkata"     # decides "today" for the raw <yyyy>/<MM>/<dd> partition
control_schema: "dbo"               # load_control, dq_rule_results, transformation_exceptions

# ---- Authentication & Fabric MCP Server integration ---------------------
# Authentication is interactive via Azure CLI (`az login`).
# Operations in Fabric use Fabric MCP Server tools:
# - Workspace & Lakehouse items: onelake_list-workspaces, onelake_list-items, core_search-catalog
# - OneLake Data Access: onelake_list-files, onelake_download-file, onelake_upload-file
# - Pipeline & Datafactory: datafactory_create-pipeline, datafactory_run-pipeline, datafactory_get-pipeline

# Placeholders: {target} resolved dataset/target name from Gate G2,
#               {layer} bronze|silver|gold, {Layer} Bronze|Silver|Gold
target_folder_pattern: "{Target}"               # target folder containing directly {Target}_LH, notebooks, orchestrator, semantic model
lakehouse_pattern: "{Target}_LH"                 # target lakehouse per target (creation deferred to execution)
schema_pattern: "{layer}"                    # -> bronze, silver, gold
notebook_pattern: "{Layer}_{Target}"            # -> Bronze_Marine, Silver_Marine, Gold_Marine (no numerical prefixes)
semantic_model_pattern: "{Target}_Gold_Model"
pipeline_pattern: "{Target}_Medallion_Orchestrator"
refresh_notebook: "Refresh_Semantic_Model"   # shared by every target dataset
table_pattern: "{entity}"                     # Bronze/Silver: exact match to raw source filename stem; Gold: client-style STTM

# ---- load behaviour -----------------------------------------------------
watermark_default: "partition_mtime" # partition_mtime | column | cdc_merge  (SKILL.md, Bronze load semantics)
scd_default: ""                     # blank = ask at G11 | SCD1 | SCD2_DELTA_HISTORY | SCD2_MERGE

# ---- generic transformation settings (basic_transformation_logic.md) ---
null_tokens: []                     # §5 configurable tokens mapped to NULL, e.g. ["N/A", "NA", "-"]
money_type: "DECIMAL(20,2)"         # §8
rate_type: "DECIMAL(18,6)"          # §8, §12
percentage_form: "fraction"         # §12: fraction (0.05) | points (5.00)
```

## Rule overrides

These are client-wide overrides applied to every dataset/target. They outrank basic transformation logic, but an uploaded rules document (G8) outranks them (`basic_transformation_logic.md` §1).

| Id | Applies to | Column or pattern | Override | Reason |
|---|---|---|---|---|
| _none_ | | | | |
