# Semantic Model Generation

The semantic model is the **last step of every LOB's medallion build**. It is
generated from the LOB's **registered** `gold_model.yaml`, never inferred from the
lakehouse, and regenerated only when that model changes. Nothing here names a LOB,
a table, a column value or a row count. A LOB contributes only its registered
`gold_model.yaml` and, inside it, a small `semantic_model_config` block of naming
inputs.

For the Fabric and TMDL mechanics, see
`skills-for-fabric/skills/semantic-model-authoring/SKILL.md` and its references:
`direct-lake-guidelines.md`, `tmdl-guidelines.md`, `modeling-guidelines.md`,
`naming-conventions.md`, `semantic-model-rest-api.md` and
`semantic-model-ai-readiness.md`. Follow that skill's telemetry header and tool
selection priority. Without `powerbi-modeling-mcp` the path is TMDL plus REST
(Tier 2).

## Naming and location

| Item | Convention |
|---|---|
| Semantic model | `{semantic_model}` from `client_config.md` → `semantic_model_pattern`, one per LOB (`semantic_model_config.name` may pin it) |
| Folder | the same workspace folder as the LOB's Bronze, Silver and Gold notebooks |
| Storage mode | **Direct Lake** over `{lakehouse}`, schema `{gold_schema}` |
| Named expression | `DirectLake - <model name>`, `AzureStorage.DataLake` on OneLake |
| Source of truth | `gold_model.yaml` → a generated `semantic_model:` block (committed) → TMDL (generated at deploy, never stored) |

Workspace and lakehouse ids are resolved by name at deploy time, and only then
substituted into the named expression. No GUID is ever stored in the repo.

## When it runs

It runs on the `y` at **G13** (`interface.md`), after G12b has run and registered
the Gold model, for the one LOB selected at G2.

| Condition | Semantic model step |
|---|---|
| Gold run `Succeeded` and `gold_model.yaml` `REGISTERED` | build the definition, decide the case (below), and ask G13b |
| Gold `Failed`, or `GRAIN_DRIFT`, or the model is not registered | **does not run**. Say why in one line at G13, leave the existing semantic model untouched, and go to G14. |
| Gold `SKIPPED` (nothing moved) | Case C: G13b approves a refresh only |

### Preconditions (read-only)

Stop and report if any of these fails:

- `gold_model.yaml` is `REGISTERED`.
- Every Gold table it names exists, with the columns it names.
- The last `dbo.load_control` row with `stage='gold'` and `table_name='__run__'` is
  `Succeeded`, with `grain_fingerprint` and `model_version` equal to the YAML's.
- The YAML's `superseded_tables` are absent.

## Rules S1–S11 — from gold_model.yaml to a semantic model

Every object records the rule that produced it.

- **S1. Tables.**
  - Every dimension, the date dimension and every fact becomes one Direct Lake
    table (`EntityPartitionSource`, `mode: directLake`, `schemaName` = the Gold
    schema).
  - No other tables. No calculated tables or calculated columns: derived
    measures are already materialised in Gold.
  - Names: facts are plural and dimensions singular, as business words without
    `Fact`/`Dim` prefixes. Columns use readable names (see S8).
  - Data types come from the live Delta schema:
    - string → `string`, boolean → `boolean`, int/bigint → `int64`
    - date/timestamp → `dateTime`, with `formatString: "yyyy/MM/dd"` for a
      date and `"yyyy/MM/dd HH:mm:ss"` for a timestamp (the standard in
      `notebook_standards.md` §5). The date table uses the same formats.
    - decimal with scale ≤ 4 → `decimal`; decimal with scale > 4 → `double`
      (fixed decimal holds 4 decimals)
- **S2. Relationships.**
  - One per fact `foreign_keys` entry: fact `<entity>_sk` → dimension
    `<entity>_sk`, many-to-one, single direction.
  - Surrogate keys only, never natural keys. G5 has already proven fan-out 1.0.
  - No many-to-many relationships and no bidirectional filtering.
- **S3. Role-playing date (G6).**
  - One date table, with `dataCategory: Time` and a Year > Quarter > Month > Day
    hierarchy.
  - Per fact, the **first** entry of `date_roles` in the YAML is the active
    relationship. That is the stated rule, and the list is shown at approval.
  - Every other role gets an inactive relationship, plus a row-count measure and
    the fact's first money measure wrapped in `USERELATIONSHIP`. An inactive
    relationship without such a measure is a defect.
  - Raw role columns on the fact are hidden, because dates are analysed through
    the date table.
  - `isKey` is not set: the G7 `UNKNOWN` date row carries a NULL date.
- **S4. Base measures, driven by additivity in the YAML.**
  - A row count per fact, and a count per dimension that excludes `UNKNOWN`.
  - A `ROW` measure (or one that is one-value-per-row at its own fact) gets
    `SUM`. A measure additive only at a coarser key is summed only on the fact
    that holds it at that grain.
  - Ratios are recomputed from their inputs as `DIVIDE(sum numerator, sum
    denominator)`, over the rows where the materialised ratio is valid. If the
    numerator is not persisted, it is rebuilt as `SUMX(ratio × denominator)`.
    Ratios are **never** summed or averaged.
  - Day counts get average, minimum and maximum, never a sum.
  - Indicators get count measures (`# <things> (<indicator>)`), never a sum of
    booleans. NULL is not counted.
- **S5. Currency safety (G8).**
  - Every monetary measure returns BLANK unless exactly one value of the fact's
    currency column is in context. NULL counts as its own value, so UNKNOWN
    currency never totals with a known one.
  - A measure with a literal currency (for example GBP) is never mixed, so it
    needs no guard.
  - Each fact with a currency column gets `# Currencies (<fact>)`, the currency
    check. No FX conversion.
- **S6. Alternative measures (G1).** Measures that are nullable alternatives on
  one fact stay separate measures. They are never combined, coalesced or
  equated.
- **S7. UNKNOWN members (G7).** They stay visible and labelled `UNKNOWN`, so
  orphan totals remain explainable. They are never filtered out of the model.
  Only the dimension counts exclude them.
- **S8. Visibility, naming and format.**
  - Hidden: every `*_sk`, every `_gold_*` column, every column a measure
    aggregates, and every fact natural key that duplicates a joined dimension's
    key. Use `isAvailableInMdx: false` on keys and audit columns.
  - `summarizeBy: none` everywhere, and `discourageImplicitMeasures` on the
    model.
  - Readable names: `_` becomes a space and words are capitalised, with a
    generic word map (`sk`→Key, `id`→ID, `no`→Number, `txn`→Transaction) plus
    the LOB's `semantic_model_config` (`acronyms`, `words`, `phrases`,
    `table_names`).
  - Visible names are unique across the model. A visible dimension column whose
    name a visible fact column also uses is prefixed with the dimension name.
  - Formats: money `#,##0.00`; ratios `0.00%`; days and counts `#,##0`.
  - Month is numeric, so it sorts naturally. Add a sort-by only when a text
    month exists in Gold.
- **S9. Blocked derived measures.** No measure is generated for them. They are
  listed in the model description.
- **S10. Descriptions (AI readiness).**
  - Every table gets its grain and Gold source. Every measure gets its rule id
    and how it is computed. Every fact lists the business-rule ids it carries.
  - Use `///` descriptions, front-loaded and at most 200 characters, since
    Copilot reads only the first 200.
  - AI instructions, synonyms and verified answers are **user actions** in
    Power BI "Prep data for AI". Recommend them; never claim they were applied.
- **S11. Hierarchies.**
  - The date hierarchy is S3.
  - A dimension hierarchy is created only where the grain profile **proves**
    it: each level functionally depends on the level below it
    (`dependencies` in `grain_structure`, at or above `fd_threshold`).
    Examples: country > region > port, or make > model.
  - A hierarchy that `lob/<lob>.md` or the G11a analytics inputs ask for, but
    the data does not prove, is listed at G13b as `NOT CREATED` with the
    failing level. It is never forced.
  - Hide the level columns only when the hierarchy is their sole intended use.

## The `semantic_model:` block and its hash

The generator writes a `semantic_model:` block to the end of `gold_model.yaml`. It
holds the name, storage mode, source, `gold_model_version`, `grain_fingerprint`,
the tables (Gold table, kind, description, columns with source and type),
relationships (active or inactive, and their rule), measures (DAX, format, rule,
description, folder), hidden columns, blocked rules and `semantic_model_hash`.

`semantic_model_hash` is `sha256` of the block's canonical JSON (sorted keys,
without `registered` and without the hash itself), first 16 hex characters. The
same hash is written into the model as the annotation `semantic_model_hash`, so a
deployed model can be matched to its block.

## Approval cases

The case is decided by `model_version` + `grain_fingerprint` +
`semantic_model_hash`, compared with `semantic_model.registered` in the YAML.
It decides what is shown before **G13b** (*"Approve semantic model?
[APPROVE/DECLINE]"*). G13b is asked in every case.

| Case | Condition | Shown before G13b | On `APPROVE` |
|---|---|---|---|
| **A** | no `{semantic_model}` exists, and none is registered | the `semantic_model:` block, the full TMDL, a Mermaid diagram of relationships (active solid, inactive dashed), the measure list and the hierarchies | deploy, refresh, verify, register |
| **B** | the Gold model changed (new `model_version` or fingerprint), so the hash differs | the YAML diff of the block, the TMDL diff, and, in plain language, which tables, relationships, measures and hierarchies appear, disappear or change | update, refresh, verify, register |
| **C** | same hash as registered | *"Gold model is unchanged — APPROVE refreshes the registered Semantic Model."* plus its table and measure counts | Direct Lake refresh (reframe) only, then verify |

- **Before approval**, nothing is created, updated or refreshed in Fabric.
- **DECLINE** runs the issues loop: fix the definition, show the change, and
  repeat G13b.
- **A Gold Case B that was approved** always leads into a semantic-model
  Case B.

## Deploy (after approval)

1. Check the display name is free (FL-013). For Case B, update the existing item
   instead.
2. Case A: `POST /v1/workspaces/{ws}/semanticModels` with `folderId` and the TMDL
   parts. Case B: `updateDefinition` with **all** parts, never including
   `.platform`.
   - Poll the long-running operation to `Succeeded`. **Deploy exactly once**: a
     retried create makes a duplicate. If a duplicate appears, delete it
     before doing anything else.
   - Read the definition back and grep it for the `semantic_model_hash`
     (FL-007).
3. Refresh (reframe) through the Power BI refresh API and poll it to completion.
   On a credential error, **stop** and tell the user to configure the data
   source credentials in the Power BI service. Never loop.

## Verification (DAX against the deployed model)

Use `executeQueries` (Power BI API, audience `https://analysis.windows.net/powerbi/api`):

- Row count per fact = the Gold table count in the last gold `load_control` run.
- Every monetary measure, sliced by the fact's currency column, equals the
  matching `GOLD-RECON-SUM` or `GOLD-RECON-REPEAT` figure in `dbo.dq_rule_results`
  for that run. The UNKNOWN/NULL currency bucket is compared separately.
- Every ratio measure is checked against a direct computation from the Gold
  table, to a relative tolerance of 1e-6.
- A money measure with more than one currency in context returns BLANK.
- Every inactive date role measure returns a non-blank value.
- Rows carrying the UNKNOWN member of each dimension equal the orphan and
  null-key counts from `GOLD-RECON-ORPHAN`.

Report, in this order:
- the closing line *The semantic model is created* (or *updated*, or
  *refreshed*)
- tables with their row counts
- relationships (active or inactive)
- verification results
- blocked items

**G13b `APPROVE` is also the registration**, so there is no separate question.
After a successful verification, fill `semantic_model.registered` with `date`,
`item`, `semantic_model_hash`, `model_version` and `grain_fingerprint`. If
verification fails, mark Semantic `✖`. Report the failing checks, fix them, and
repeat G13b. Do not register a model that failed verification.

## Orchestration

The pipeline built at G14 runs a **refresh only** after `{notebook:gold}`. It
never regenerates the model, and it runs only when the Gold notebook's exit
`status` is `Succeeded`, never on `SKIPPED` or `GRAIN_DRIFT`. Regeneration
happens only through G13 and G13b.

The refresh runs in **`{refresh_notebook}`** (`client_config.md`; default
`Refresh_Semantic_Model`). It is one generic notebook, shared by every LOB,
generated rather than stored, and it lives in the same folder as the layer
notebooks. When it does not exist yet, G14 generates it along with the pipeline.

- Parameters: `target`, `lakehouse_name`, `model_name`, `batch_id`, `wait_timeout_minutes`.
- It resolves the model by name with semantic-link (`sempy.fabric`), calls `refresh_dataset(refresh_type="full")` (a reframe, for Direct Lake), and polls `get_refresh_execution_details` until the refresh completes.
- It runs as the pipeline's identity, so **no Power BI connection** is needed.
- It fails if the model does not exist, because it never creates one.
- It appends a status row to `dbo.project_status` with `stage='semantic_model'`, `status='COMPLETED'`, and `updated_at`.
- It exits with `{batch_id, stage, status, model, refresh_request_id}`.
