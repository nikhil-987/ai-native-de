# The Failure Registry

The failure registry holds every defect, trap, and Fabric-specific failure mode that has affected data pipeline runs. It is the single home for that knowledge.

## Schema of an Entry

Each entry has these fields:

- **FL-NNN** — entry identifier
- **Signature** — exact string or exception class to recognize it by
- **Layer** — `bronze` | `silver` | `gold` | `semantic` | `orchestrator` | `any` | `tooling`
- **Cause** — why it happens
- **Fix** — the form that works
- **First seen** — context where it occurred

---

### FL-001 — `array_remove` with a null literal
**Signature** `null typed values cannot be used as arguments` / `AnalysisException` on `array_remove`
**Layer** any
**Cause** `F.array_remove(arr, None)` passes an untyped null; Spark refuses to match it against `array<string>`.
**Fix** `F.filter(arr, lambda x: x.isNotNull())`
**First seen** Silver transformations.

### FL-002 — window function inside `CASE WHEN`
**Signature** analysis error naming a window expression inside a `CASE`/`when`
**Layer** any
**Cause** `F.when(cond, F.count("*").over(w))` nests a window in a conditional, which Spark does not allow.
**Fix** materialise the window in its own column, then test that column:
`.withColumn("_cnt", F.count("*").over(w)).withColumn("flag", cond & (F.col("_cnt") > 1))`
**First seen** Silver transformation logic.

### FL-003 — `isin()` given Columns
**Signature** type/resolution error on `isin`
**Layer** any
**Cause** `isin` accepts literals, not `Column` objects.
**Fix** compare directly — `col == F.lit(v)` — or pass plain Python values.
**First seen** Silver transformation logic.

### FL-004 — `to_date` raises instead of returning null
**Signature** `SparkUpgradeException: [INCONSISTENT_BEHAVIOR_CROSS_VERSION.PARSE_DATETIME_BY_NEW_PARSER]`, caused by `java.time.format.DateTimeParseException: Text '...' could not be parsed`
**Layer** silver, gold
**Cause** Under Fabric's default `timeParserPolicy`, a value that does not match the format aborts the write. It does not yield null. So `F.coalesce(F.to_date(s, fmt1), F.to_date(s, fmt2))` never reaches `fmt2` — it dies on the first row that misses `fmt1`.
**Fix** gate every format with a regex that matches it exactly, and set the policy as a backstop:
```python
d = F.coalesce(*[F.when(s.rlike(rx), F.to_date(s, fmt)) for rx, fmt in PATTERNS])
spark.conf.set("spark.sql.legacy.timeParserPolicy", "CORRECTED")
```
The observed layouts for a given feed belong in that LOB's `registered_business_rules.md`, not here.
**First seen** Silver date parsing.

### FL-005 — date before the 1582 calendar cutover
**Signature** `SparkUpgradeException: [INCONSISTENT_BEHAVIOR_CROSS_VERSION.WRITE_ANCIENT_DATETIME]` inside `TASK_WRITE_FAILED`
**Layer** silver, gold
**Cause** A date earlier than 1582-10-15 means something different under the Julian and Gregorian calendars, so Spark will not write it to Parquet until told which to assume.
**Fix** set all four to `CORRECTED`, which stores exactly the parsed value with no rebase:
```python
for k in ("spark.sql.parquet.datetimeRebaseModeInWrite",
          "spark.sql.parquet.int96RebaseModeInWrite",
          "spark.sql.parquet.datetimeRebaseModeInRead",
          "spark.sql.parquet.int96RebaseModeInRead"):
    spark.conf.set(k, "CORRECTED")
```
Report the out-of-range values in the summary. Do not null them unless a business rule says so.
**First seen** Silver date parsing.

### FL-006 — the traceback dies with the session
**Signature** `Session ... is in a terminal state ... Livy state: killed` when reading `/statements`; job status only says *"System cancelled the Spark session due to statement execution failures"*
**Layer** tooling
**Cause** Fabric tears the Livy session down on failure. The per-cell output is then unreachable through every API, so a failed run tells you nothing.
**Fix** Mandatory in every generated notebook. Wrap each table block so the exception is recorded and the run reaches the summary cell, which writes the traceback to `Files/_logs/<stage>_<run_id>.log` before re-raising:
```python
def record_error(stage, exc):
    import traceback
    ERRORS.append((stage, "".join(traceback.format_exception(
        type(exc), exc, exc.__traceback__))))
```
**First seen** Notebook tooling and execution tracing.

### FL-007 — running the previous definition
**Signature** a fix that provably works appears to have no effect
**Layer** tooling
**Cause** `updateDefinition` is a long-running operation returning `202`. Start the job before it reaches `Succeeded` and the run may execute the old code.
**Fix** poll `/v1/operations/{id}` to `Succeeded`, then read the definition back and grep for a string unique to the new version. Note Fabric returns the part as `notebook-content.py` even when `.ipynb` was uploaded — do not key on the filename.
**First seen** Notebook update API deployment.

### FL-008 — `dd/MM` versus `MM/dd`
**Signature** none — no error, wrong data
**Layer** silver
**Cause** Accepting both readings silently transposes day and month on every date where both are valid. This never fails; it just quietly produces wrong answers.
**Fix** determine the order from a value that disambiguates it (a first component above 12) and support **one**. A null beats a wrong date. Record the decision and its evidence in that LOB's `registered_business_rules.md`.
**First seen** Silver date parsing ambiguity.

### FL-009 — MERGE on a non-unique key
**Signature** `DeltaUnsupportedOperationException` — multiple source rows matched one target row
**Layer** bronze, silver
**Cause** A business key that looks unique but is not (e.g. sentinel values or uncleaned duplicates).
**Fix** never row-merge on a business key until uniqueness is **proven on the actual data**. Prefer snapshot `overwrite`, which is also what makes a stage idempotent and safe for orchestrator resume.
**First seen** Raw CSV key analysis.

### FL-010 — phantom trailing columns
**Signature** columns named `_c6`, `_c7`, `_c8` in a Bronze table
**Layer** bronze
**Cause** A header line ending in `,,,`. Spark names the unnamed columns positionally.
**Fix** test the **raw** Spark name, not the sanitized one — sanitization strips the leading underscore, so `_c6` arrives as `c6` and `^_c\d+$` never matches:
```python
def is_phantom(raw, clean):
    return clean == "" or re.fullmatch(r"_c\d+", raw) is not None
```
**First seen** Bronze raw file loading.

### FL-011 — CSV read as the wrong encoding
**Signature** no error; a mangled character such as `Lloyd?s` where `Lloyd's` belongs
**Layer** bronze
**Cause** A cp1252 file read as UTF-8. Byte `0x92` is a curly apostrophe in windows-1252 and invalid in UTF-8.
**Fix** confirm the encoding per file rather than assuming; record it in the Source Registry.
**First seen** Bronze CSV encoding verification.

### FL-012 — newlines inside quoted CSV fields
**Signature** row count higher than the source's real record count
**Layer** bronze
**Cause** Without `multiLine`, Spark splits a quoted field containing a newline into extra rows.
**Fix** default every CSV source to `multiLine: True` until proven unnecessary, and verify the count against an independent parse.
**First seen** Bronze CSV parsing.

### FL-013 — display name already in use
**Signature** HTTP 409 `ItemDisplayNameAlreadyInUse`
**Layer** tooling
**Cause** Item display names are unique per type across the **whole workspace**, not per folder. A name used in another folder blocks yours.
**Fix** list workspace items first. If the name is taken by an item that is not this LOB's, never invent a suffix and never overwrite it. Ask a choice gate.
**First seen** Workspace Lakehouse provisioning.

### FL-014 — schemas cannot be added to an existing lakehouse
**Signature** no way to create `Tables/<Schema>` in a lakehouse that was not schema-enabled
**Layer** tooling
**Cause** `enableSchemas` is a creation-time property and is **not** retrofittable.
**Fix** always create with `creationPayload: {"enableSchemas": true}`. If an existing lakehouse lacks it, the only route is a new lakehouse.
**First seen** Lakehouse creation.

### FL-015 — job sits at `NotStarted` — not a failure
**Signature** status `NotStarted` for many minutes, sometimes over an hour
**Layer** tooling
**Cause** Trial and small SKUs queue Spark jobs behind any `InProgress` Livy session, including sessions started by other people.
**Fix** wait, and say so. Check `GET /v1/workspaces/{ws}/spark/livySessions` to show what is holding the capacity. Never cancel a session you did not start.
**First seen** Spark session queuing.

### FL-016 — validating a column after `withColumn` has replaced it
**Signature** none — no error, a count that is always 0, or a `rows_failed` larger than the row count
**Layer** silver, gold
**Cause** Two variants of the same mistake:
1. `df = df.withColumn("premium", to_money("premium"))` and *then* testing `F.col("premium").isNull() & _clean("premium").isNotNull()`. After the assignment `premium` **is** the typed column, so the test compares it against itself and can only return 0.
2. Reporting `rows_failed` as a sum of null cells across several columns.

**Fix** Measure a conversion failure on the **source** frame, before the column is overwritten:
```python
def conv_failures(src_df, col, typed):
    return (src_df.select(_clean(col).alias("_s"), typed.alias("_t"))
                  .filter(F.col("_s").isNotNull() & F.col("_t").isNull()).count())
```
**First seen** Silver validation reporting.

### FL-017 — YAML key `on` read as boolean `True`
**Signature** `KeyError: 'on'` (also `'off'`, `'yes'`, `'no'`, `'y'`, `'n'`) on a dict loaded from YAML
**Layer** gold, tooling
**Cause** PyYAML implements YAML 1.1, where bare `on`/`off`/`yes`/`no` are booleans, including when used as mapping keys.
**Fix** never use those words as bare keys in a model file (`join_on:`, `date:`).
**First seen** Gold model YAML parsing.

### FL-018 — dimension constancy counts NULL as a second value
**Signature** `ValueError: <dim>: attributes vary within [<key>] without an approved G10 rule`
**Layer** gold
**Cause** Constancy test mapped NULL to a sentinel value, so NULL counted as a second value when attributes were partially populated across row types.
**Fix** Test constancy with `countDistinct(F.col(a))`: NULL is absence, not variation.
**First seen** Gold dimension generation.

### FL-019 — Direct Lake data source rejected at deploy
**Signature** `Dataset_Import_FailedToImportDataset` … `Direct Lake mode requires a Direct Lake data source`
**Layer** semantic model
**Cause** The named expression's `AzureStorage.DataLake` URL was not resolved to a plain workspace/lakehouse ID URL (literal braces left around IDs).
**Fix** Substitute the resolved IDs into the expression at deploy and assert final text holds no `{` or `}`.
**First seen** Semantic model deployment.
