# Basic Transformation Logic

Common, **LOB-independent** transformations considered for every insurance
dataset: marine, automobile, aviation, home, and any LOB added later. The
medallion skill reads it on every Silver build (gates G8–G10 in `interface.md`),
and it needs no per-LOB edit. Every "configured" value below comes from
`client_config.md`, or from `lob/<lob>.md` → *Overrides*.

This file holds generic data-engineering transformations only — column-name
standardisation, whitespace, blank→null, type standardisation, dates,
timestamps, numerics, booleans, strings, duplicates, schema consistency.

**It contains no business rules and never will.** A rule about what a policy,
claim, premium or vessel *means* belongs to that LOB's business rules document,
not here.

---

## 1. Precedence — read this before anything else

**Business rules always win.** Uploaded, client-wide or LOB default, it makes
no difference: any business rule outranks this file.

When a business rule and this file disagree, **ignore this file and follow the
business rule.** Do not blend them, do not apply the basic form "as well", and
do not treat the basic form as a fallback the rule forgot to mention. Say in the
run report which basic transformation the rule displaced, so the divergence is
visible rather than silent.

The full order, highest first. G8 shows the merged rule set in this order, and
every conflict along with which side won:

| # | Authority | Governs |
|---|---|---|
| 1 | **Uploaded rules** — the document given at G8 `UPLOAD` | what transformation to apply to a column, and what a value means |
| 2 | **Client rule overrides** — `client_config.md` → *Rule overrides* | the same, client-wide |
| 3 | **LOB default rules** — `lob/<lob>.md` → *Default business rules* (the LOB's `registered_business_rules.md`) | the same, for this LOB. This is the only rule set when G8 is `SKIP` |
| 4 | **Bronze contracts** in `SKILL.md` — `sanitize()`, phantom drops, all-string, load semantics | column naming and Bronze load shape |
| 5 | **Silver column contract** in `SKILL.md` | which columns may exist at all |
| 6 | **This file**, with its configured values | everything not settled above |
| 7 | `failure_registry.md` | cuts across all of the above: a registered failure must never be reintroduced by any of them |

An uploaded document outranks a registered set because it is newer. G10
`APPROVE` then makes it the registered set.

Two of these need spelling out, because they are the ones that bite:

- **Business rules (1–3) outrank this file on *what to do*.** If the rules say
  `commission = 5` means `0.05`, that is the transformation, whatever §12 below
  suggests.
- **The Silver column contract outranks everything on *what columns exist*.**
  It is closed. Neither a business rule nor this file may add a column to a
  Silver table. A transformation that can only be expressed by adding a column
  is not performed; the finding is logged instead (see §23).

---

## 2. Core design principle — metadata-driven, never name-driven

Inspect the **actual source schema** and decide which generic transformations
apply. Never assume a column exists, and never key behaviour off a hardcoded
name such as `POLICY_NO`, `CLAIM_NO`, `PREMIUM`, `VESSEL_NAME`,
`VEHICLE_REGISTRATION` or `PROPERTY_VALUE`.

Deciding that a column called `premium` is *a numeric-looking field that should
be typed as decimal* is this file's job. Deciding that it is **the written
premium inclusive of IPT** is the business rules' job. Keep that line sharp:
this file may recognise **shape**, never **meaning**.

A column's semantic category is inferred from profiling its values, from
metadata, and from configuration — not from its name alone. Where the category
is genuinely ambiguous, treat it as text and say so, rather than guessing.

---

## 3. Column name standardisation

Target convention: lowercase `snake_case`, no leading or trailing whitespace,
no special characters, no unnecessary punctuation, no repeated underscores.

```
"Policy Number"       -> policy_number
"POLICY_NO"           -> policy_no
"Policy-No"           -> policy_no
"Claim Date"          -> claim_date
"Premium Amount (£)"  -> premium_amount
```

Rules: trim, lowercase, spaces and hyphens to `_`, drop unsupported special
characters, collapse consecutive underscores, avoid reserved SQL keywords where
possible, **preserve semantic meaning**, and never rename a column merely to
make it look business-specific.

> **Bronze's `sanitize()` has already done this, and it wins.**
> Column naming happens once, in Bronze, under the `sanitize()` contract in
> `SKILL.md`. Silver reads the names Bronze produced and **must not re-standardise
> them.** Renaming in Silver breaks every downstream layer written against the
> Bronze names.
>
> Two places `sanitize()` deliberately differs from the convention above, and it
> is right both times:
> - `%` becomes `pct` **before** punctuation is stripped, so `"Commission (%)"`
>   becomes `commission_pct` rather than colliding with a sibling column.
> - Source spelling is preserved: `"CHASIS NO"` becomes `chasis_no`, not
>   `chassis_no`. Correcting a source's spelling is a rename, which is forbidden.
>
> Treat §3 as the rule for a **new** source being profiled into Bronze for the
> first time, and as documentation thereafter. Never as licence to rename.

Two source columns that standardise to the same name are a **source problem to
report**, not to silently disambiguate.

---

## 4. String standardisation

Apply to textual fields: trim leading whitespace, trim trailing whitespace,
normalise repeated internal whitespace, remove unnecessary control characters.

```
"   London   Market   "  ->  "London Market"
```

**Do not blanket-apply `UPPER()` or `LOWER()`.** Casing can carry meaning.
Normalise case only when the field is clearly a code or status field (§15), or
a business or reference rule requires it.

---

## 5. Blank value → NULL

**Mandatory, always:**

| Source | Result |
|---|---|
| `""` | NULL |
| `" "` | NULL |
| `"   "` (whitespace only) | NULL |

**Configurable, never automatic:**

`N/A` · `NA` · `NULL` · `null` · `None` · `UNKNOWN` · `NOT AVAILABLE`

These are converted **only** where a configured mapping
(`client_config.md` → `null_tokens`) or a business rule says so. `UNKNOWN` is frequently a legitimate business value — a policyholder whose
nationality is genuinely unknown is not the same as one whose nationality was
never captured. Collapsing the two destroys information that cannot be
recovered.

---

## 6. Data type standardisation

Inspect the source type and the values, then choose the target type.

| Data category | Preferred type |
|---|---|
| Identifier | String |
| Text | String |
| Integer | Integer / Long |
| Decimal | Decimal |
| Monetary amount | Decimal |
| Date | Date |
| Timestamp | Timestamp |
| Boolean | Boolean |
| Percentage | Decimal |
| Code | String |

**Identifiers stay strings even when they contain only digits.**

```
Policy Number = 00001234    ->  "00001234", never 1234
```

Leading zeros may be meaningful, and an identifier is never an arithmetic
quantity. Columns that are normally identifiers rather than measures: policy
number, claim number, customer id, broker id, vehicle registration, IMO number,
postcode, contract id, UMR.

---

## 7. Numeric standardisation

```
"1000"    -> 1000
"1000.50" -> 1000.50
" 2500 "  -> 2500
```

Formatting characters may be stripped **where configured**:

```
"1,250.50" -> 1250.50
"£1,250"   -> 1250
```

A currency symbol is not simply discarded when the currency interpretation is
ambiguous — see §13.

**An invalid numeric never becomes zero.**

```
premium = "ABC"
   ->  premium = NULL, and an exception recorded (§23)
```

`NULL` and `0` are different facts. The source value stays traceable, which in
this architecture it always is: Bronze holds every column as an unmodified
string and is never deleted, so the original is one join away.

---

## 8. Decimal precision

Financial values — premium, claim amount, sum insured, insured value,
commission, tax — use `DECIMAL(p,s)` with the configured precision and scale
(`money_type`, `rate_type`), unless a business rule sets another.

**Never a floating-point type** where exact decimal representation matters.
Binary floating point cannot represent most decimal fractions exactly, and the
error compounds across aggregation.

---

## 9. Date standardisation

Parse strings into real date types using a **controlled** strategy. Determine
the expected source format from, in order: metadata, profiling, configuration,
explicit source specification.

**Never guess between `dd/MM` and `MM/dd`.**

```
01/02/2026   ->  1 February?  or  January 2?
```

Both readings are valid, so accepting both silently transposes day and month on
every date where both fit. This never raises an error; it just produces wrong
answers. Resolve it from a value that disambiguates — a first component above 12
proves day-first — and then support **one** layout.

If ambiguity remains after all four sources: `date = NULL`, record the
exception, and do not guess. A null beats a wrong date.

**Target format: `yyyy/MM/dd`.** Whatever layout a source uses (`dd/MM/yyyy`,
`MM/dd/yyyy`, `yyyy-MM-dd`, `dd-MMM-yyyy`, …), it is parsed into a real `date`
column. That column is displayed, printed and logged as `yyyy/MM/dd`, and the
semantic model formats it the same way. Do not store dates as formatted
strings: a string sorts and filters wrongly and breaks the date table. See
`notebook_standards.md` §5.

> **Gate every format with a regex that matches it exactly.** Under Fabric's
> default `timeParserPolicy`, `to_date` **raises** on a non-matching value
> instead of returning null, so a plain `coalesce` across formats dies on the
> first row that misses the first format. See `FL-004` in `failure_registry.md`
> for the form that works. The layouts observed in a given feed belong in that
> LOB's `lob/<lob>.md` → *Known quirks* and its `registered_business_rules.md`,
> not here.

---

## 10. Timestamp standardisation

```
2026-01-15 10:30:00
2026-01-15T10:30:00
15/01/2026 10:30
```

Standardise where parsing is deterministic, under the same discipline as §9.

**Preserve timezone information when supplied.** Do not convert timezone unless
the target standard explicitly requires it — an arbitrary shift is a silent
data change.

**Target format: `yyyy/MM/dd HH:mm:ss`.** Parse into a real `timestamp`,
truncated to whole seconds (`F.date_trunc("second", ts)`), and display it as
`yyyy/MM/dd HH:mm:ss` (24-hour). A source time with minutes only
(`15/01/2026 10:30`) gets `:00` seconds. See `notebook_standards.md` §5.

---

## 11. Boolean standardisation

`Y`/`N` · `YES`/`NO` · `TRUE`/`FALSE` · `1`/`0` · `T`/`F` may normalise to
`TRUE`/`FALSE` — **only where the field has been identified as boolean.**

Fields that often are: war risk included, delegated authority, general average,
active.

```
Status = "ACTIVE"
```

is **not** boolean merely because it looks affirmative. A status is a code with
more than two possible values, and flattening it to a boolean throws the rest
away.

---

## 12. Percentage standardisation

```
5%    5    0.05    5.0
```

These are **not** automatically equivalent. Determine the source representation
before converting anything.

If the source specification says `commission = 5` means 5%, the standardised
form may be `0.05` or `5.00` depending on the canonical schema
(`percentage_form`). **Configurable, and stated explicitly** — never inferred
from the magnitude of the values.

---

## 13. Currency standardisation

Normalise to a controlled representation, **reference-data driven and
deterministic**:

```
GBP · £ · Pound · British Pound · UKP   ->  GBP
USD · US Dollar                         ->  USD
```

`$` alone is **ambiguous** — USD, CAD, AUD, SGD, HKD and others all use it — and
must not be resolved automatically.

**No FX conversion** unless an explicit business rule instructs it. Converting
currency without an approved rate and rate date is fabrication.

---

## 14. Identifier standardisation

Cast to string, trim, **preserve leading zeros**, preserve source identity.

Never perform arithmetic or numerical aggregation on an identifier. Summing
policy numbers is meaningless; averaging them is worse.

---

## 15. Case standardisation

Configurable, and it depends on the semantic category:

| Category | Example | Treatment |
|---|---|---|
| Free text | `John Smith` | leave as-is |
| Code | `gbp` / `GBP` / `Gbp` | may become `GBP` |
| Status | `active` / `Active` / `ACTIVE` | may become `ACTIVE` |
| Identifier | `ab00123x` | leave as-is |

Distinguish the categories first. Do not apply `UPPER()` to every column.

---

## 16. Special character handling

Normalise where appropriate:

```
" ABC-123 "  ->  "ABC-123"
```

But **never blanket-strip**. Vehicle registration, policy number, UMR and
postcode legitimately contain special characters, and removing them corrupts
the value. The transformation is semantic and configurable, never destructive.

---

## 18. Null handling

`NULL` · `0` · `FALSE` · `UNKNOWN` · `NOT APPLICABLE` are **five different
facts** and are never interchangeable.

```
Premium  = NULL   does NOT mean  Premium  = 0
War Risk = NULL   does NOT mean  War Risk = FALSE
```

Mandatory across every LOB, with no exception and no configuration that can
switch it off.

---

## 23. Invalid data handling

```
Source value
     |
Can it be deterministically standardised?
     |
   YES ------------------> standardised value
     |
    NO
     |
     +--> preserve the source value
     +--> set the standardised value to NULL
     +--> record an exception
```

**Never**, unless an explicit business rule permits it:

| Forbidden | Why |
|---|---|
| invalid value → `0` | invents a measurement that was never taken |
| invalid value → `FALSE` | invents a negative answer |
| invalid date → current date | invents an event |
| missing id → generated random id | invents an entity, and silently breaks every join |

### Where an exception goes

The Silver column contract is closed, so an exception **cannot** be written as a
`*_conversion_error` or `*_parse_error` column on the Silver table. It is
written to **`dbo.transformation_exceptions`** instead — a log in `dbo`, beside
`load_control` and `dq_rule_results`, not a data table:

```
run_id, stage, table_name, column_name, source_value_sample,
attempted_type, reason, occurrences, detected_at
```

Aggregate by `(table, column, reason, source_value)` with a count and a sample
rather than one row per failure — a column that fails to parse usually fails on
tens of thousands of rows, and the hundredth identical row teaches nothing.

**Traceability is not lost by this.** Bronze holds every column as an
unmodified string, is overwritten but never deleted, and carries `_batch_id`, so
the exact source value behind any null is always one join away. The exception
log says *which column, which reason, how many*; Bronze says *which rows*.

Logs append, because they are logs. Data tables always overwrite.

---

## 24. Transformation order

```
 1. Read source
 2. Profile source
 3. Identify schema
 4. Standardise column names        <-- BRONZE only, via sanitize()
 5. Standardise whitespace
 6. Convert blanks to NULL
 7. Detect semantic data types
 8. Standardise identifiers
 9. Standardise dates / timestamps
10. Standardise numeric values
11. Standardise boolean values
12. Standardise codes / currency where deterministic
13. Produce transformed dataset
```

Mapped onto the medallion layers:

| Steps | Layer | Note |
|---|---|---|
| 1–3 | Bronze and Silver both profile | never trust a template's assumed schema |
| 4 | **Bronze only** | `sanitize()` runs once; Silver never renames |
| 5–13 | **Silver** | Bronze changes no values, ever — it is all-string by design |

Bronze applying steps 5–13 would be a defect: its job is to land the source
faithfully so that a transformation error is always recoverable.

---

## 25. What this file must never do

- Apply marine-, automobile-, aviation- or home-specific rules
- Infer business meaning from a column name alone
- Create business relationships, or decide policy/claim grain
- Deduplicate business records without an approved key
  *(see `FL-009`: uncleaned business keys containing sentinels, blanks, or
  duplicates — a key that looks unique and is not)*
- Calculate a business metric without a business rule
- Perform FX conversion without an approved rule
- Infer a missing business value
- Change a business status without a mapping
- Automatically reject records
- Delete records because of data-quality issues
- Generate fake identifiers
- Replace NULL with zero or false
- Modify source data
- **Add a column to a Silver table** — the contract is closed

---

## 26. Decision logic

```
FOR each source table:

    Profile table

    FOR each column:

        Identify physical datatype
        Identify likely semantic category

        IF string:      trim whitespace; blank -> NULL
        IF identifier:  cast to string; preserve leading zeros
        IF numeric:     standardise representation; apply configured precision
        IF date:        parse using known/configured formats, regex-gated
        IF timestamp:   parse and standardise; preserve timezone
        IF boolean:     normalise configured representations only
        IF code/status: apply configured reference mapping
        IF currency:    normalise via currency reference data

        IF a business rule covers this column:
            apply the business rule INSTEAD
            report which basic transformation it displaced

        IF the transformation is ambiguous:
            preserve source
            record exception in dbo.transformation_exceptions
            do NOT guess

    Validate the resulting schema
    Preserve lineage

END
```

---

## Applying this to a Silver build

1. **Set the agenda from G8.**
   - `UPLOAD`: the uploaded rules, merged with client overrides and LOB default
     rules in §1 order.
   - `SKIP`: the LOB default rules only. If none are registered, only this file
     applies.
2. Read this file for everything the rules leave unsaid, using the configured
   values.
3. Check the result against `failure_registry.md` before showing it at G10.
4. In the notebook, keep the sources of truth visually separate. Comment each
   block with its origin:
   - a rule id (`BR-…`, `<LOB>-…`) for a business rule
   - `override <id>` for a client override
   - `basic §N` for a section of this file

   A reviewer must be able to tell at a glance which is which. Each code is
   also explained, with its meaning and source file, in the header comment of
   the cell that uses it and in the notebook's header cell
   (`notebook_standards.md` §3).
5. In the G9 summary and the G10 report, name any basic transformation a
   business rule displaced.

## A note on the section numbering

The numbering follows the source document as supplied, which has no sections
17 or 19–22. The gaps are preserved so that a reference to "§12" or "§23" means
the same thing in both documents. They are not omissions.
