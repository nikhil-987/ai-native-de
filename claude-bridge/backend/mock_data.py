"""Mock data and interactive Medallion flow simulation for testing without Claude or Azure CLI."""

import json
import re
import time
import uuid

MOCK_WORKSPACES = [
    {"id": "11111111-1111-1111-1111-111111111111", "name": "Adrosonic Medallion Demo Workspace"},
    {"id": "22222222-2222-2222-2222-222222222222", "name": "Contoso Enterprise Analytics"},
    {"id": "33333333-3333-3333-3333-333333333333", "name": "Sales & Retail Operations"},
]

MOCK_LAKEHOUSES = [
    {"id": "aaaaaa11-1111-1111-1111-111111111111", "name": "Sales_RAW_LH", "folder": None},
    {"id": "bbbbbb22-2222-2222-2222-222222222222", "name": "Finance_RAW_LH", "folder": "Finance_Dept"},
    {"id": "cccccc33-3333-3333-3333-333333333333", "name": "Customer_360_LH", "folder": "CRM_Analytics"},
]

MOCK_RAW_FOLDERS = [
    {"name": "2026/10/10", "path": "Files/2026/10/10"},
    {"name": "sales_transactions_v1", "path": "Files/sales_transactions_v1"},
    {"name": "customer_profiles_delta", "path": "Files/customer_profiles_delta"},
]

MOCK_PROJECTS = {
    "projects": [
        {
            "name": "Marine_Analytics",
            "icon": "🚢",
            "lakehouse": "Marine_LH",
            "lakehouse_id": "aaaaaa11-1111-1111-1111-111111111111",
            "folder": "Marine",
            "readable": True,
            "completion": 70,
            "bucket": "in_progress",
            "current_gate": "G11",
            "next_action": "Upload client-style STTM document for Gold modeling",
            "stages": {
                "profile": "done",
                "bronze": "done",
                "silver": "done",
                "gold": "pending",
                "orchestrator": "pending",
                "semantic_model": "pending",
            },
            "updated_at": "2026-10-10T21:10:00Z",
        },
        {
            "name": "Automobile_Claims",
            "icon": "🚗",
            "lakehouse": "Automobile_LH",
            "lakehouse_id": "bbbbbb22-2222-2222-2222-222222222222",
            "folder": "Automobile",
            "readable": True,
            "completion": 85,
            "bucket": "in_progress",
            "current_gate": "G13",
            "next_action": "Create Data Factory Orchestrator Pipeline",
            "stages": {
                "profile": "done",
                "bronze": "done",
                "silver": "done",
                "gold": "done",
                "orchestrator": "in_progress",
                "semantic_model": "pending",
            },
            "updated_at": "2026-10-10T20:45:00Z",
        },
        {
            "name": "Finance_Ledger_Bronze",
            "icon": "💼",
            "lakehouse": "Finance_RAW_LH",
            "lakehouse_id": "cccccc33-3333-3333-3333-333333333333",
            "folder": "Finance_Dept",
            "readable": True,
            "completion": 45,
            "bucket": "in_progress",
            "current_gate": "G8",
            "next_action": "Upload Silver business rules file (business_rules.xlsx)",
            "stages": {
                "profile": "done",
                "bronze": "done",
                "silver": "pending",
                "gold": "pending",
                "orchestrator": "pending",
                "semantic_model": "pending",
            },
            "updated_at": "2026-10-10T20:15:00Z",
        },
        {
            "name": "Sales_Analytics_Medallion",
            "icon": "📈",
            "lakehouse": "Sales_RAW_LH",
            "lakehouse_id": "dddddd44-4444-4444-4444-444444444444",
            "folder": None,
            "readable": True,
            "completion": 100,
            "bucket": "completed",
            "current_gate": "G15",
            "next_action": "Pipeline complete. All Fabric items deployed and verified.",
            "stages": {
                "profile": "done",
                "bronze": "done",
                "silver": "done",
                "gold": "done",
                "orchestrator": "done",
                "semantic_model": "done",
            },
            "updated_at": "2026-10-10T18:30:00Z",
        },
        {
            "name": "Customer_360_LH",
            "icon": "👤",
            "lakehouse": "Customer_360_LH",
            "lakehouse_id": "eeeeee55-5555-5555-5555-555555555555",
            "folder": "CRM_Analytics",
            "readable": True,
            "completion": 90,
            "bucket": "in_progress",
            "current_gate": "G14",
            "next_action": "Create Direct Lake Semantic Model",
            "stages": {
                "profile": "done",
                "bronze": "done",
                "silver": "done",
                "gold": "done",
                "orchestrator": "done",
                "semantic_model": "in_progress",
            },
            "updated_at": "2026-10-10T19:20:00Z",
        },
    ]
}

def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


MOCK_SESSIONS: dict[str, dict] = {}
LATEST_MOCK_SESSION_ID: str = "demo-session-default"


def stream_mock_chat(prompt: str, run_id: str, session_id: str | None = None):
    """Simulates realistic Claude Code Medallion responses with complete gate-by-gate progression."""
    global LATEST_MOCK_SESSION_ID

    sid = session_id or LATEST_MOCK_SESSION_ID
    if sid not in MOCK_SESSIONS:
        if not session_id:
            sid = f"demo-session-{uuid.uuid4().hex[:8]}"
        MOCK_SESSIONS[sid] = {
            "gate": "INIT",
            "branch": "new",
            "target": "Sales_Analytics_Demo",
            "target_lakehouse": "Sales_Analytics_Demo_LH",
            "workspace": "Adrosonic Medallion Demo Workspace",
            "source_lakehouse": "Sales_RAW_LH",
            "folder": "Files/2026/10/10",
            "target_lakehouse_created": False,
            "stages": {
                "profile": "pending",
                "bronze": "pending",
                "silver": "pending",
                "gold": "pending",
                "orchestrator": "pending",
                "semantic_model": "pending",
            },
            "created": [],
            "runs": [],
            "project": None,
            "resume_next": None,
            "orchestrator": None,
            "semantic_model": None,
            "post_run_for": None,
        }

    LATEST_MOCK_SESSION_ID = sid
    sess = MOCK_SESSIONS[sid]
    target_name = sess["target"]
    p = prompt.strip().lower()

    yield sse_event("start", {"run_id": run_id})
    yield sse_event("init", {"session_id": sid, "model": "claude-3-5-sonnet (Demo Mode)"})
    time.sleep(0.15)
    yield sse_event("text_start", {})

    # ----------------------------------------------------
    # 1. RESUME EXISTING PROJECT FLOW
    # ----------------------------------------------------
    if "g1a action: 2" in p or "resume an existing project" in p or "project to resume" in p:
        proj_name = "Marine_Analytics"
        m = re.search(r'project to resume:\s*"([^"]+)"', prompt, re.IGNORECASE)
        if m:
            proj_name = m.group(1)

        sess["target"] = proj_name
        sess["branch"] = "resume"

        if "finance" in proj_name.lower():
            sess["gate"] = "G8"
            sess["stages"] = {"profile": "done", "bronze": "done", "silver": "in_progress", "gold": "pending", "orchestrator": "pending", "semantic_model": "pending"}
            sess["created"] = ["Finance_RAW_LH", "Bronze_Finance_Ledger"]
            sess["runs"] = [{"stage": "bronze", "item": "Bronze_Finance_Ledger", "run_id": "run-b02", "status": "completed"}]
            text = (
                f"### 🔄 Project Resumed: {proj_name}\n"
                f"- **Location**: `Finance_Dept/Finance_RAW_LH`\n"
                f"- **Last Active**: `2026-10-10 20:15:00 UTC`\n"
                f"- **Current Pending Step**: Silver Business Rules Upload\n"
                f"- **Next Action Required**: Upload client-style business rules spreadsheet (`business_rules.xlsx`) for Silver data cleansing.\n\n"
                f"### Silver Business Rules Studio\n"
                f"Bronze layer is indexed. Ready to parse Silver cleansing rules.\n\n"
                f"Upload business rules document (`business_rules.xlsx`) for Silver, or press SKIP. [UPLOAD/SKIP]"
            )
        elif "auto" in proj_name.lower():
            sess["gate"] = "G13"
            sess["stages"] = {"profile": "done", "bronze": "done", "silver": "done", "gold": "done", "orchestrator": "in_progress", "semantic_model": "pending"}
            sess["created"] = ["Automobile_LH", "Bronze_Automobile", "Silver_Automobile", "Gold_Automobile"]
            sess["runs"] = [
                {"stage": "bronze", "item": "Bronze_Automobile", "run_id": "run-b03", "status": "completed"},
                {"stage": "silver", "item": "Silver_Automobile", "run_id": "run-s03", "status": "completed"},
                {"stage": "gold", "item": "Gold_Automobile", "run_id": "run-g03", "status": "completed"},
            ]
            text = (
                f"### 🔄 Project Resumed: {proj_name}\n"
                f"- **Location**: `Automobile/Automobile_LH`\n"
                f"- **Current Pending Step**: Data Factory Orchestrator Creation\n\n"
                f"### Data Factory Orchestrator Pipeline\n"
                f"All Medallion PySpark notebooks (`Bronze`, `Silver`, `Gold`) are deployed.\n\n"
                f"Create the orchestrator pipeline now? [y/n]"
            )
        elif "customer" in proj_name.lower():
            sess["gate"] = "G14"
            sess["stages"] = {"profile": "done", "bronze": "done", "silver": "done", "gold": "done", "orchestrator": "done", "semantic_model": "in_progress"}
            sess["created"] = ["Customer_360_LH", "Bronze_Customer", "Silver_Customer", "Gold_Customer", "Customer_360_Orchestrator"]
            sess["orchestrator"] = {"name": "Customer_360_Orchestrator", "status": "deployed", "activities": ["Bronze_Customer", "Silver_Customer", "Gold_Customer"]}
            text = (
                f"### 🔄 Project Resumed: {proj_name}\n"
                f"- **Location**: `CRM_Analytics/Customer_360_LH`\n"
                f"- **Current Pending Step**: Direct Lake Semantic Model\n\n"
                f"### Direct Lake Semantic Model\n"
                f"Gold tables (`fact_customer_360`, `dim_customer`, `dim_segment`) are ready.\n\n"
                f"Generate Direct Lake semantic model now? [y/n]"
            )
        elif "sales" in proj_name.lower() and "medallion" in proj_name.lower():
            sess["gate"] = "G15"
            sess["stages"] = {"profile": "done", "bronze": "done", "silver": "done", "gold": "done", "orchestrator": "done", "semantic_model": "done"}
            text = (
                f"### 🔄 Project Resumed: {proj_name} (100% Completed)\n"
                f"- **Location**: `Sales_RAW_LH`\n"
                f"- **Current Status**: Complete — Medallion Summary & Handover\n\n"
                f"All pipeline stages successfully executed & validated.\n\n"
                f"Process another dataset in this workspace, or close session? [y/n]"
            )
        else:
            # Default Marine Analytics: Paused at Gold STTM (G11)
            sess["gate"] = "G11"
            sess["stages"] = {"profile": "done", "bronze": "done", "silver": "done", "gold": "in_progress", "orchestrator": "pending", "semantic_model": "pending"}
            sess["created"] = ["Marine_LH", "Bronze_Marine", "Silver_Marine"]
            sess["runs"] = [
                {"stage": "bronze", "item": "Bronze_Marine", "run_id": "run-b05", "status": "completed"},
                {"stage": "silver", "item": "Silver_Marine", "run_id": "run-s05", "status": "completed"},
            ]
            text = (
                f"### 🔄 Project Resumed: {proj_name}\n"
                f"- **Location**: `Marine/Marine_LH`\n"
                f"- **Current Pending Step**: Gold STTM Upload & Dimensional Modeling\n\n"
                f"### Gold STTM Upload & Dimensional Modeling\n"
                f"Bronze and Silver layers are cleansed and verified.\n\n"
                f"Upload client-style STTM document (`marine_sttm.xlsx`), or press SKIP. [UPLOAD/SKIP]"
            )

    # ----------------------------------------------------
    # 2. START A NEW PROJECT (INITIAL LAUNCH PROMPT)
    # ----------------------------------------------------
    elif "choices already made" in p or "g1a action: 1" in p or (sess["gate"] == "INIT" and "start" in p):
        target_name = "Sales_Analytics_Demo"
        m = re.search(r'raw data folder:\s*"([^"]+)"', prompt, re.IGNORECASE)
        if m:
            folder_clean = re.sub(r"[^\w_]", "_", m.group(1).split("/")[-1])
            if folder_clean:
                target_name = f"{folder_clean.capitalize()}_Analytics"

        sess["target"] = target_name
        sess["target_lakehouse"] = f"{target_name}_LH"
        sess["branch"] = "new"
        sess["gate"] = "G2"
        sess["stages"] = {"profile": "pending", "bronze": "pending", "silver": "pending", "gold": "pending", "orchestrator": "pending", "semantic_model": "pending"}
        sess["created"] = []
        sess["runs"] = []

        text = (
            f"### Connection & Environment Verified\n"
            f"- Workspace: `Adrosonic Medallion Demo Workspace`\n"
            f"- Source Lakehouse: `Sales_RAW_LH`\n"
            f"- Raw Data Folder: `Files/2026/10/10`\n\n"
            f"### Target Directory Resolution\n"
            f"Suggested project folder structure in OneLake:\n"
            f"```\n"
            f"/{target_name}/\n"
            f"├── {target_name}_LH (Target Lakehouse, created on first run)\n"
            f"├── notebooks/\n"
            f"├── orchestrator/\n"
            f"└── semantic model/\n"
            f"```\n"
            f"Please confirm or provide a custom target folder name. (Suggested: `{target_name}`) [y/<custom>/n]"
        )

    # ----------------------------------------------------
    # 3. SEQUENTIAL MEDALLION GATE ADVANCEMENT
    # ----------------------------------------------------
    elif sess["gate"] == "G2":
        # User confirmed or customized target name
        if p not in ("y", "yes") and len(prompt.strip()) > 1 and not p.startswith("start"):
            custom = re.sub(r"[^\w\- ]", "_", prompt.strip())
            if custom:
                sess["target"] = custom
                sess["target_lakehouse"] = f"{custom}_LH"
                target_name = custom

        sess["gate"] = "G2b"
        text = (
            f"Target directory resolved: `/{target_name}/`.\n\n"
            f"### Raw File Details Preview\n"
            f"Discovered 3 raw files under `Files/2026/10/10/`:\n\n"
            f"| Raw File | Size | Partition Path | Target Delta Table |\n"
            f"|---|---|---|---|\n"
            f"| `policy_data.csv` | 14.2 MB | `2026/10/10` | `bronze.policy_data` |\n"
            f"| `customer_master.csv` | 8.6 MB | `2026/10/10` | `bronze.customer_master` |\n"
            f"| `claims_ledger.csv` | 22.1 MB | `2026/10/10` | `bronze.claims_ledger` |\n\n"
            f"Show details of the files and begin Data Profiling? [y/n]"
        )

    elif sess["gate"] == "G2b":
        sess["gate"] = "G4"
        sess["stages"]["profile"] = "in_progress"
        text = (
            f"Raw file structures verified.\n\n"
            f"### Spark Data Profiling & Schema Inference\n"
            f"Ready to profile raw tables in a read-only Livy session:\n"
            f"- Row counts and schema validation\n"
            f"- Null percentages per column\n"
            f"- Candidate primary keys and unique identifiers\n"
            f"- Date and timestamp formatting\n\n"
            f"Run data profiling now? [y/n]"
        )

    elif sess["gate"] == "G4":
        sess["gate"] = "G5"
        sess["stages"]["profile"] = "done"
        text = (
            f"### Data Profiling Results & Quality Metrics\n"
            f"Read-only Spark profiling completed successfully on raw dataset:\n\n"
            f"| Table | Rows | Null % | Candidate Primary Key | Date Formats | Encoding |\n"
            f"|---|---|---|---|---|---|\n"
            f"| `policy_data` | 125,000 | 0.02% | `policy_id` | `yyyy-MM-dd` | UTF-8 |\n"
            f"| `customer_master` | 45,200 | 0.00% | `customer_id` | `yyyy-MM-dd` | UTF-8 |\n"
            f"| `claims_ledger` | 89,400 | 0.15% | `claim_id` | `yyyy-MM-dd HH:mm:ss` | UTF-8 |\n\n"
            f"#### Column Type Audit\n"
            f"- `policy_id`: String (100% unique, candidate PK)\n"
            f"- `customer_id`: String (foreign key to `customer_master`)\n"
            f"- `premium_amount`: Decimal(18,2) [numeric valid: 99.98%]\n"
            f"- `policy_start_date`: Date (`yyyy-MM-dd`)\n\n"
            f"Are you satisfied with the data profile? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G5":
        sess["gate"] = "G6"
        sess["stages"]["bronze"] = "in_progress"
        text = (
            f"Data profile approved. Attribute registry updated.\n\n"
            f"### Bronze Layer Delta Ingestion\n"
            f"Bronze layer objective:\n"
            f"- Land raw CSV files as Delta tables under `Tables/dbo/`\n"
            f"- Preserve all fields as string on read (no early type errors)\n"
            f"- Append audit metadata: `_ingested_at`, `_source_file`, `_batch_id`\n\n"
            f"Generate Bronze notebook now? [y/n]"
        )

    elif sess["gate"] == "G6":
        sess["gate"] = "G7"
        text = (
            f"### Review Bronze Ingestion Notebook\n"
            f"Generated notebook: `Bronze_{target_name}.ipynb`\n\n"
            f"```python\n"
            f"# Bronze Ingestion Notebook: Bronze_{target_name}.ipynb\n"
            f"from pyspark.sql.functions import current_timestamp, input_file_name, lit\n\n"
            f"def ingest_to_bronze(source_path, target_table):\n"
            f"    df = spark.read.option('header', 'true').option('inferSchema', 'false').csv(source_path)\n"
            f"    df_bronze = (df\n"
            f"        .withColumn('_ingested_at', current_timestamp())\n"
            f"        .withColumn('_source_file', input_file_name())\n"
            f"        .withColumn('_batch_id', lit('20261010_01')))\n"
            f"    df_bronze.write.format('delta').mode('append').saveAsTable(f'Tables/dbo/{{target_table}}')\n"
            f"    print(f'Ingested {{df_bronze.count()}} records into Tables/dbo/{{target_table}}')\n\n"
            f"ingest_to_bronze('Files/2026/10/10/policy_data.csv', 'bronze_policy')\n"
            f"ingest_to_bronze('Files/2026/10/10/customer_master.csv', 'bronze_customer')\n"
            f"ingest_to_bronze('Files/2026/10/10/claims_ledger.csv', 'bronze_claims')\n"
            f"```\n\n"
            f"Do you approve Bronze notebook for Fabric deployment? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G7":
        sess["gate"] = "G7a"
        sess["created"] = [f"{target_name}_LH", f"Bronze_{target_name}"]
        sess["target_lakehouse_created"] = True
        text = (
            f"`Bronze_{target_name}` notebook deployed to Fabric under folder `/{target_name}/`.\n"
            f"Target Lakehouse `{target_name}_LH` initialized.\n\n"
            f"### Run Bronze Ingestion Notebook\n"
            f"Run Bronze notebook now in the background? [y/skip/n]"
        )

    elif sess["gate"] == "G7a":
        if "skip" in p:
            # Skip run -> directly to G8
            sess["gate"] = "G8"
            sess["stages"]["bronze"] = "done"
            sess["stages"]["silver"] = "in_progress"
            text = (
                f"Execution skipped. Notebook `Bronze_{target_name}` remains deployed.\n\n"
                f"### Silver Cleansing & Business Rules Mapping\n"
                f"Upload business rules document (`business_rules.xlsx`) for Silver, or press SKIP. [UPLOAD/SKIP]"
            )
        else:
            sess["gate"] = "POST_RUN"
            sess["post_run_for"] = "bronze"
            sess["stages"]["bronze"] = "done"
            sess["runs"].append({"stage": "bronze", "item": f"Bronze_{target_name}", "run_id": "run-b01", "status": "completed"})
            text = (
                f"Execution of `Bronze_{target_name}` submitted to Fabric in the background (Run ID: `run-b01`).\n"
                f"- Job Status: `Completed (125,000 rows landed)`\n"
                f"- Duration: `38 seconds`\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )

    elif sess["gate"] == "POST_RUN":
        post_stage = sess.get("post_run_for", "bronze")
        if p in ("2", "status", "check"):
            text = (
                f"Polled Fabric job execution: All tasks finished with code 0 (Success).\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )
        elif post_stage == "bronze":
            sess["gate"] = "G8"
            sess["stages"]["silver"] = "in_progress"
            text = (
                f"Bronze layer completed and verified.\n\n"
                f"### Silver Cleansing & Business Rules Mapping\n"
                f"Silver layer enforces enterprise data hygiene:\n"
                f"- Strong data type casting & timestamp parsing\n"
                f"- Duplicate record filtering based on candidate primary keys\n"
                f"- Value standardization and null imputation\n\n"
                f"Upload business rules document (`business_rules.xlsx`) for Silver, or press SKIP. [UPLOAD/SKIP]"
            )
        elif post_stage == "silver":
            sess["gate"] = "G11"
            sess["stages"]["gold"] = "in_progress"
            text = (
                f"Silver layer cleansed and verified.\n\n"
                f"### Gold Star-Schema Dimensional Modeling\n"
                f"Gold layer requires Source-to-Target Mapping (STTM) for star-schema dimensional modeling:\n"
                f"- Star schema fact & dimension definitions\n"
                f"- Surrogate key generation & conformed hierarchies\n"
                f"- Business KPI measures and aggregations\n\n"
                f"Upload client-style STTM document (`sttm.xlsx` / `marine_sttm.xlsx`), or press SKIP. [UPLOAD/SKIP]"
            )
        elif post_stage == "gold":
            sess["gate"] = "G13"
            sess["stages"]["orchestrator"] = "in_progress"
            text = (
                f"Gold dimensional tables deployed and verified.\n\n"
                f"### Data Factory Orchestrator Pipeline\n"
                f"Build a Data Factory pipeline DAG that chains the notebooks sequentially:\n"
                f"`Bronze_{target_name}` ➔ `Silver_{target_name}` ➔ `Gold_{target_name}` ➔ `Refresh_Semantic_Model`\n\n"
                f"Create the orchestrator pipeline now? [y/n]"
            )
        elif post_stage == "orchestrator":
            sess["gate"] = "G14"
            sess["stages"]["semantic_model"] = "in_progress"
            text = (
                f"Orchestrator pipeline execution succeeded.\n\n"
                f"### Direct Lake Semantic Model\n"
                f"Generate a Power BI Direct Lake Semantic Model pointing directly to the Gold delta tables in OneLake.\n"
                f"Sub-second query performance without data duplication.\n\n"
                f"Generate Direct Lake semantic model now? [y/n]"
            )
        elif post_stage == "semantic_model":
            sess["gate"] = "G15"
            text = (
                f"### 🏆 Medallion Architecture Final Summary Dashboard\n"
                f"All pipeline stages, notebooks, orchestrator DAG, and Direct Lake semantic model are fully operational in Microsoft Fabric!\n\n"
                f"| Layer | Schema | Table Name | Rows Processed | Fabric Execution Status |\n"
                f"|---|---|---|---|---|\n"
                f"| Bronze | `dbo` | `bronze_policy` | 125,000 | `✔ Deployed & Ingested` |\n"
                f"| Silver | `dbo` | `silver_policy` | 124,980 | `✔ Deployed & Cleansed` |\n"
                f"| Gold | `dbo` | `gold_fact_sales` | 124,980 | `✔ Deployed & Modeled` |\n\n"
                f"#### Deployed Fabric Artifacts\n"
                f"- Target Lakehouse: `{target_name}_LH`\n"
                f"- Notebooks: `Bronze_{target_name}`, `Silver_{target_name}`, `Gold_{target_name}`\n"
                f"- Data Factory Pipeline: `{target_name}_Medallion_Orchestrator`\n"
                f"- Direct Lake Semantic Model: `{target_name}_Gold_Model`\n\n"
                f"Project status logged to `dbo.project_status`. Completion rate: **100%**.\n\n"
                f"Process another dataset in this workspace, or close session? [y/n]"
            )

    elif sess["gate"] == "G8":
        sess["gate"] = "G9"
        text = (
            f"Business rules file validated and registered.\n\n"
            f"### Silver Business Rules Transformation Matrix\n"
            f"| Rule ID | Table | Column | Cleansing & Transformation Logic | Action |\n"
            f"|---|---|---|---|---|\n"
            f"| `BR-01` | `policy_data` | `policy_id` | Unique Primary Key constraint | Deduplicate keeping latest `_ingested_at` |\n"
            f"| `BR-02` | `policy_data` | `premium_amount` | Must be numeric > 0 | Cast Decimal(18,2); quarantine negatives |\n"
            f"| `BR-03` | `customer_master` | `email` | Trim, lowercase, valid email pattern | Standardize text |\n"
            f"| `BR-04` | `claims_ledger` | `claim_date` | Convert String to Timestamp | `to_timestamp(claim_date, 'yyyy-MM-dd')` |\n\n"
            f"Generate Silver notebook with these rules applied? [y/n]"
        )

    elif sess["gate"] == "G9":
        sess["gate"] = "G10"
        text = (
            f"### Review Silver Cleansing Notebook\n"
            f"Generated notebook: `Silver_{target_name}.ipynb`\n\n"
            f"```python\n"
            f"# Silver Cleansing & Standardization Notebook: Silver_{target_name}.ipynb\n"
            f"from pyspark.sql.functions import col, to_date, row_number, trim, lower\n"
            f"from pyspark.sql.window import Window\n"
            f"from delta.tables import DeltaTable\n\n"
            f"df_bronze = spark.read.table('Tables/dbo/bronze_policy')\n\n"
            f"# Deduplicate on policy_id\n"
            f"w = Window.partitionBy('policy_id').orderBy(col('_ingested_at').desc())\n"
            f"df_silver = (df_bronze\n"
            f"    .withColumn('_rn', row_number().over(w))\n"
            f"    .filter(col('_rn') == 1).drop('_rn')\n"
            f"    .withColumn('premium_amount', col('premium_amount').cast('decimal(18,2)'))\n"
            f"    .withColumn('policy_start_date', to_date(col('policy_start_date'), 'yyyy-MM-dd'))\n"
            f"    .filter(col('premium_amount') > 0))\n\n"
            f"# SCD-1 Merge into Silver Delta Table\n"
            f"silver_table = DeltaTable.forName(spark, 'Tables/dbo/silver_policy')\n"
            f"(silver_table.alias('tgt')\n"
            f"    .merge(df_silver.alias('src'), 'tgt.policy_id = src.policy_id')\n"
            f"    .whenMatchedUpdateAll()\n"
            f"    .whenNotMatchedInsertAll()\n"
            f"    .execute())\n"
            f"```\n\n"
            f"Do you approve Silver notebook for Fabric deployment? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G10":
        sess["gate"] = "G10a"
        sess["created"].append(f"Silver_{target_name}")
        text = (
            f"`Silver_{target_name}` notebook deployed to Fabric.\n\n"
            f"### Run Silver Cleansing Notebook\n"
            f"Run Silver notebook now in the background? [y/skip/n]"
        )

    elif sess["gate"] == "G10a":
        if "skip" in p:
            sess["gate"] = "G11"
            sess["stages"]["silver"] = "done"
            sess["stages"]["gold"] = "in_progress"
            text = (
                f"Execution skipped. Notebook `Silver_{target_name}` remains deployed.\n\n"
                f"### Gold Star-Schema Dimensional Modeling\n"
                f"Upload client-style STTM document (`marine_sttm.xlsx`), or press SKIP. [UPLOAD/SKIP]"
            )
        else:
            sess["gate"] = "POST_RUN"
            sess["post_run_for"] = "silver"
            sess["stages"]["silver"] = "done"
            sess["runs"].append({"stage": "silver", "item": f"Silver_{target_name}", "run_id": "run-s01", "status": "completed"})
            text = (
                f"Execution of `Silver_{target_name}` submitted to Fabric in the background (Run ID: `run-s01`).\n"
                f"- Job Status: `Completed (124,980 cleansed records merged)`\n"
                f"- Duration: `52 seconds`\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )

    elif sess["gate"] == "G11":
        sess["gate"] = "G12"
        text = (
            f"STTM document analyzed and mapped successfully.\n\n"
            f"### Approve Gold Star-Schema Architecture\n"
            f"- **Fact Table**: `gold_fact_sales` (Grain: Individual policy transaction)\n"
            f"  - Keys: `sales_key` (SK), `customer_key` (FK), `product_key` (FK)\n"
            f"  - Measures: `premium_amount`, `tax_amount`, `net_amount`\n"
            f"- **Dimension Tables**:\n"
            f"  - `gold_dim_customer` (Demographics, status, region)\n"
            f"  - `gold_dim_product` (Product name, category, risk tier)\n"
            f"  - `gold_dim_date` (Year, Quarter, Month, Weekday)\n\n"
            f"Approve the Gold model and generate the Gold notebook? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G12":
        sess["gate"] = "G12b"
        text = (
            f"### Review Gold Dimensional Notebook\n"
            f"Generated notebook: `Gold_{target_name}.ipynb`\n\n"
            f"```python\n"
            f"# Gold Star Schema Notebook: Gold_{target_name}.ipynb\n"
            f"from pyspark.sql.functions import col, md5, concat_ws\n\n"
            f"df_silver = spark.read.table('Tables/dbo/silver_policy')\n"
            f"df_cust = spark.read.table('Tables/dbo/silver_customer')\n\n"
            f"# Generate Dimension Customer\n"
            f"dim_cust = df_cust.select('customer_id', 'customer_name', 'region').distinct()\n"
            f"dim_cust.write.format('delta').mode('overwrite').saveAsTable('Tables/dbo/gold_dim_customer')\n\n"
            f"# Generate Fact Sales with MD5 Surrogate Key\n"
            f"fact_sales = (df_silver\n"
            f"    .join(dim_cust, 'customer_id', 'left')\n"
            f"    .withColumn('sales_key', md5(concat_ws('_', col('policy_id'), col('policy_start_date'))))\n"
            f"    .select('sales_key', 'policy_id', 'customer_id', 'premium_amount', 'policy_start_date'))\n"
            f"fact_sales.write.format('delta').mode('overwrite').saveAsTable('Tables/dbo/gold_fact_sales')\n"
            f"```\n\n"
            f"Do you approve Gold notebook for Fabric deployment? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G12b":
        sess["gate"] = "G12c"
        sess["created"].append(f"Gold_{target_name}")
        text = (
            f"`Gold_{target_name}` notebook deployed to Fabric.\n\n"
            f"### Run Gold Dimensional Notebook\n"
            f"Run Gold notebook now in the background? [y/skip/n]"
        )

    elif sess["gate"] == "G12c":
        if "skip" in p:
            sess["gate"] = "G13"
            sess["stages"]["gold"] = "done"
            sess["stages"]["orchestrator"] = "in_progress"
            text = (
                f"Execution skipped. Notebook `Gold_{target_name}` remains deployed.\n\n"
                f"### Data Factory Orchestrator Pipeline\n"
                f"Create the orchestrator pipeline now? [y/n]"
            )
        else:
            sess["gate"] = "POST_RUN"
            sess["post_run_for"] = "gold"
            sess["stages"]["gold"] = "done"
            sess["runs"].append({"stage": "gold", "item": f"Gold_{target_name}", "run_id": "run-g01", "status": "completed"})
            text = (
                f"Execution of `Gold_{target_name}` submitted to Fabric in the background (Run ID: `run-g01`).\n"
                f"- Job Status: `Completed (Gold star-schema tables generated)`\n"
                f"- Duration: `48 seconds`\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )

    elif sess["gate"] == "G13":
        sess["gate"] = "G13c"
        sess["created"].append(f"{target_name}_Medallion_Orchestrator")
        sess["orchestrator"] = {
            "name": f"{target_name}_Medallion_Orchestrator",
            "status": "deployed",
            "activities": [f"Bronze_{target_name}", f"Silver_{target_name}", f"Gold_{target_name}", "Refresh_Semantic_Model"],
            "source_lakehouse": sess["source_lakehouse"],
            "target_lakehouse": sess["target_lakehouse"],
        }
        text = (
            f"Data Factory Pipeline deployed: `{target_name}_Medallion_Orchestrator`!\n\n"
            f"### Run Orchestrator Pipeline\n"
            f"Activities DAG Configured:\n"
            f"1. `Bronze_{target_name}` (Notebook Activity)\n"
            f"2. `Silver_{target_name}` (Notebook Activity, dependsOn Bronze)\n"
            f"3. `Gold_{target_name}` (Notebook Activity, dependsOn Silver)\n"
            f"4. `Refresh_Semantic_Model` (Web Refresh Activity, dependsOn Gold)\n\n"
            f"Run the orchestrator pipeline now in Fabric? [y/skip/n]"
        )

    elif sess["gate"] == "G13c":
        if "skip" in p:
            sess["gate"] = "G14"
            sess["stages"]["orchestrator"] = "done"
            sess["stages"]["semantic_model"] = "in_progress"
            text = (
                f"Pipeline run skipped. Pipeline `{target_name}_Medallion_Orchestrator` remains deployed.\n\n"
                f"### Direct Lake Semantic Model\n"
                f"Generate Direct Lake semantic model now? [y/n]"
            )
        else:
            sess["gate"] = "POST_RUN"
            sess["post_run_for"] = "orchestrator"
            sess["stages"]["orchestrator"] = "done"
            sess["runs"].append({"stage": "orchestrator", "item": f"{target_name}_Medallion_Orchestrator", "run_id": "orch-run-01", "status": "completed"})
            sess["orchestrator"]["status"] = "succeeded"
            sess["orchestrator"]["last_run"] = {"status": "succeeded", "start": "Just now", "duration": "1m 24s", "run_id": "orch-run-01"}
            text = (
                f"Execution of `{target_name}_Medallion_Orchestrator` submitted to Fabric in the background (Run ID: `orch-run-01`).\n"
                f"- Job Status: `Completed (All 4 activities succeeded)`\n"
                f"- Duration: `1m 24s`\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )

    elif sess["gate"] == "G14":
        sess["gate"] = "G14b"
        text = (
            f"### Review Direct Lake Semantic Model Definition\n"
            f"Model Name: `{target_name}_Gold_Model`\n"
            f"Mode: **Direct Lake**\n\n"
            f"- **Tables**:\n"
            f"  - `gold_fact_sales` (Fact Table, 14 columns)\n"
            f"  - `gold_dim_customer` (Dimension Table, 8 columns)\n"
            f"  - `gold_dim_product` (Dimension Table, 6 columns)\n"
            f"- **Relationships**:\n"
            f"  - `gold_fact_sales.customer_id -> gold_dim_customer.customer_id` (1:* Active)\n"
            f"- **DAX Measures**:\n"
            f"  - `Total Sales Amount = SUM(gold_fact_sales[premium_amount])`\n"
            f"  - `Total Policies Count = COUNTROWS(gold_fact_sales)`\n\n"
            f"Do you approve the semantic model for Fabric deployment? [APPROVE/DECLINE]"
        )

    elif sess["gate"] == "G14b":
        sess["gate"] = "G14c"
        sess["created"].append(f"{target_name}_Gold_Model")
        sess["semantic_model"] = {
            "name": f"{target_name}_Gold_Model",
            "status": "deployed",
            "mode": "Direct Lake",
            "tables": [
                {"name": "gold_fact_sales", "type": "fact", "columns": 14},
                {"name": "gold_dim_customer", "type": "dim", "columns": 8},
                {"name": "gold_dim_product", "type": "dim", "columns": 6},
            ],
            "relationships": ["gold_fact_sales.customer_id -> gold_dim_customer.customer_id"],
            "measures": ["Total Sales Amount", "Total Policies Count"],
        }
        text = (
            f"`{target_name}_Gold_Model` deployed to Fabric workspace.\n\n"
            f"### Refresh Semantic Model Dataset\n"
            f"Refresh semantic model dataset now? [y/skip/n]"
        )

    elif sess["gate"] == "G14c":
        if "skip" in p:
            sess["gate"] = "G15"
            sess["stages"]["semantic_model"] = "done"
            text = (
                f"Dataset refresh skipped. Model remains deployed.\n\n"
                f"### 🏆 Medallion Architecture Final Summary Dashboard\n"
                f"All stages completed! Process another dataset in this workspace, or close session? [y/n]"
            )
        else:
            sess["gate"] = "POST_RUN"
            sess["post_run_for"] = "semantic_model"
            sess["stages"]["semantic_model"] = "done"
            sess["runs"].append({"stage": "semantic_model", "item": f"{target_name}_Gold_Model", "run_id": "ref-run-01", "status": "completed", "kind": "refresh"})
            sess["semantic_model"]["status"] = "refreshed"
            sess["semantic_model"]["last_refresh"] = {"status": "completed", "time": "Just now", "run_id": "ref-run-01"}
            text = (
                f"Dataset refresh for `{target_name}_Gold_Model` submitted to Fabric in the background (Run ID: `ref-run-01`).\n"
                f"- Refresh Status: `Completed (Direct Lake frame synced)`\n"
                f"- Duration: `12 seconds`\n\n"
                f"Choose next action: [1/2/3]\n"
                f"1 for Next stage, 2 for Check status, 3 for End chat"
            )

    elif sess["gate"] == "G15":
        if "y" in p:
            # Start fresh dataset
            sess["gate"] = "G2"
            sess["target"] = "Sales_Analytics_Phase2"
            sess["target_lakehouse"] = "Sales_Analytics_Phase2_LH"
            text = (
                f"### Target Directory Resolution\n"
                f"Starting next dataset in workspace.\n\n"
                f"Please confirm or provide a custom target folder name. (Suggested: `Sales_Analytics_Phase2`) [y/<custom>/n]"
            )
        else:
            text = "Chat session stopped cleanly. All Fabric items remain deployed in your workspace. Thank you!"

    else:
        # Fallback progression
        sess["gate"] = "G2"
        text = (
            f"### Target Directory Resolution\n"
            f"Please confirm target folder name. (Suggested: `{target_name}`) [y/<custom>/n]"
        )

    # ----------------------------------------------------
    # BUILD UI STATE
    # ----------------------------------------------------
    state = {
        "gate": sess["gate"],
        "branch": sess.get("branch", "new"),
        "workspace": sess.get("workspace", "Adrosonic Medallion Demo Workspace"),
        "source_lakehouse": sess.get("source_lakehouse", "Sales_RAW_LH"),
        "folder": sess.get("folder", "Files/2026/10/10"),
        "target": sess["target"],
        "target_folder": sess["target"],
        "target_lakehouse": sess.get("target_lakehouse", f"{sess['target']}_LH"),
        "target_lakehouse_created": sess.get("target_lakehouse_created", False),
        "stages": sess["stages"],
        "created": sess.get("created", []),
        "runs": sess.get("runs", []),
        "project": sess.get("project"),
        "resume_next": sess.get("resume_next"),
        "orchestrator": sess.get("orchestrator"),
        "semantic_model": sess.get("semantic_model"),
    }

    # Stream text chunk by chunk
    lines = text.split("\n")
    for line in lines:
        yield sse_event("text", {"text": line + "\n"})
        time.sleep(0.02)

    yield sse_event("text", {"text": f"\n<!--ui-state {json.dumps(state)}-->"})
    yield sse_event("done", {
        "session_id": sid,
        "result": text,
        "is_error": False,
        "duration_ms": 250,
    })
