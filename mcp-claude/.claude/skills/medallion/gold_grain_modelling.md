# Gold Layer Dimensional Modelling

This file defines how Gold is built for every dataset behind gates G11–G12 of `interface.md`. Nothing in it hardcodes a domain, a table prefix, or a column value.

Schema, lakehouse, and notebook names are resolved dynamically from `client_config.md`.

## Lakehouse Structure — One Target Lakehouse per Dataset

```text
{lakehouse}                        schema-enabled, resolved by name at runtime
├── Tables/{bronze_schema}   <source_stem>
├── Tables/{silver_schema}   <source_stem>                  ← Gold reads here
├── Tables/{gold_schema}     <client_sttm_table>            ← Gold writes here
└── Tables/{control_schema}  project_status
```

| Item | Convention |
|---|---|
| Gold tables (Dimensions & Facts) | Derived based on the **client-style STTM (Source-to-Target Mapping)** document/specification provided by the DE during Gold modeling (e.g. `dim_<entity>`, `fact_<business_process>`, or specific client-styled target names defined in the STTM). |

---

## Gold Model Derivation Flow (G11 - G12)

At G11/G12, Gold star schemas are derived by analyzing Silver layer table schemas, entity relationships, and analytics inputs:

1. **Schema Inspection**: Read Silver schema definitions in `{silver_schema}` to identify entity keys, attributes, and foreign key relationships.
2. **Inputs & ERD (G11a)**: Parse uploaded client-style STTM document to extract target table names, grain keys, transformations, and measure formulas.
3. **Model Review (G12)**: Present proposed star schema, grain fingerprint, SCD strategy (SCD1/SCD2), and surrogate keys (`SHA-256` + `UNKNOWN` member).
4. **Notebook Generation (G12b)**: Generate `Gold_<Target>` notebook.
5. **Execution (G12c)**: Execute `Gold_<Target>` notebook. On completion, append `COMPLETED` row to `dbo.project_status`.
