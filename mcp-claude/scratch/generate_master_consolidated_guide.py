import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = r"c:\Users\nikhi\Downloads\mcp-claude"
MASTER_FILE_PATH = os.path.join(OUTPUT_DIR, "Medallion_Architecture_Master_End_To_End_Guide.docx")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header(doc, title_text, subtitle_text):
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(title_text)
    run.font.name = "Calibri"
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 51, 102)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle.add_run(subtitle_text)
    sub_run.font.name = "Calibri"
    sub_run.font.size = Pt(13)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(102, 102, 102)

    doc.add_paragraph() # Spacer

def add_heading_1(doc, text):
    h = doc.add_heading(text, level=1)
    h.runs[0].font.color.rgb = RGBColor(0, 51, 102)
    return h

def add_heading_2(doc, text):
    h = doc.add_heading(text, level=2)
    h.runs[0].font.color.rgb = RGBColor(51, 102, 153)
    return h

def add_callout(doc, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    set_cell_background(cell, "F0F4F8")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r.font.italic = True
    r.font.color.rgb = RGBColor(0, 51, 102)
    doc.add_paragraph()

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    set_cell_background(cell, "1E1E1E")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    p = cell.paragraphs[0]
    r = p.add_run(code_text)
    r.font.name = "Consolas"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(220, 220, 220)
    doc.add_paragraph()

def build_table(doc, headers, data, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    hdr_cells = table.rows[0].cells
    for idx, text in enumerate(headers):
        hdr_cells[idx].width = widths[idx]
        p = hdr_cells[idx].paragraphs[0]
        r = p.add_run(text)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr_cells[idx], "003366")
        set_cell_margins(hdr_cells[idx])

    for row_data in data:
        row_cells = table.add_row().cells
        for idx, text in enumerate(row_data):
            row_cells[idx].width = widths[idx]
            p = row_cells[idx].paragraphs[0]
            r = p.add_run(str(text))
            r.font.size = Pt(9.5)
            set_cell_margins(row_cells[idx], top=60, bottom=60, left=100, right=100)
    doc.add_paragraph()

def generate_master_guide():
    doc = Document()
    add_header(doc, "Zero-Config Medallion Architecture on Microsoft Fabric", "Master Technical Specification & End-to-End Consolidated Architecture Guide")

    # =========================================================================
    # PART 1: EXECUTIVE OVERVIEW & SYSTEM SETUP
    # =========================================================================
    add_heading_1(doc, "Part 1: Executive Overview & Environment Onboarding")
    doc.add_paragraph(
        "This master specification provides the complete consolidated technical guide for the Zero-Config Medallion Architecture on Microsoft Fabric. "
        "The architecture automates raw data landing, business rule transformations, dimensional star-schema modeling, workflow orchestration, and semantic model publishing through an interactive conversational gate protocol."
    )
    add_callout(doc,
        "Core Zero-Config Principles:\n"
        "1. Zero Static Configuration: Eliminates lob/ and datasets/ static configuration folders.\n"
        "2. Dynamic Target Resolution (Gate G2): Automatically suggests <Derived_Name> based on raw folder scan. The user can press 'y' or type custom write-in target folder name. Creates target folder <target_folder_name> (<target_folder_name>_LH, notebooks, orchestrator, semantic model). Target Lakehouse creation is deferred until notebook/orchestrator execution.\n"
        "3. Zero Filesystem Log Dumps: Eliminates Files/_logs/ directories. Pipeline progress and stage status are tracked directly in dbo.project_status in <Target>_LH.\n"
        "4. Un-Prefixed Notebook Naming: Follows Bronze_<Target>, Silver_<Target>, Gold_<Target>, and Refresh_Semantic_Model.\n"
        "5. Source-Matching Delta Tables: Bronze and Silver Delta table names match raw source filename stems directly.\n"
        "6. Stage Ordering: Stage 4 Orchestrator Pipeline (<Target>_Medallion_Orchestrator) precedes Stage 5 Direct Lake Semantic Model (<Target>_Gold_Model)."
    )

    add_heading_2(doc, "1.1 System Setup & Environment Prerequisites (New System Setup)")
    p1 = doc.add_paragraph(style='List Bullet')
    p1.add_run("Step 1: Copy mcp-claude Folder: ").bold = True
    p1.add_run("Copy or transfer the entire mcp-claude directory onto the target machine. This repository contains the architecture definitions, documentation suite, and workspace configuration.")

    p2 = doc.add_paragraph(style='List Bullet')
    p2.add_run("Step 2: Clone / Set Up Fabric Skills Repository: ").bold = True
    p2.add_run("Clone or place the fabric skills repository into .claude/skills/medallion/ within the mcp-claude workspace folder. Ensure SKILL.md, interface.md, client_config.md, and notebook_standards.md are present.")

    p3 = doc.add_paragraph(style='List Bullet')
    p3.add_run("Step 3: Configure IDE & AI Assistant (Antigravity / VS Code): ").bold = True
    p3.add_run("Launch Google Antigravity IDE or VS Code with an AI Assistant plugin (Gemini Code Assist, Claude, or Antigravity extension). Open the mcp-claude workspace folder as the root directory.")

    p4 = doc.add_paragraph(style='List Bullet')
    p4.add_run("Step 4: Authenticate Fabric Access via Azure CLI: ").bold = True
    p4.add_run("Open an embedded terminal in Antigravity or VS Code and execute 'az login' to authenticate with your Azure / Microsoft Fabric tenant. Verify active subscription and workspace permissions.")

    add_heading_2(doc, "1.2 Single Control Table Specification (dbo.project_status)")
    doc.add_paragraph(
        "The Medallion architecture operates under a 100% Single Control Table Architecture. All execution progress, project stage progression, runtime telemetry, and fail-fast reconciliation tracebacks are recorded directly in the Delta table dbo.project_status within the Target Lakehouse (<Target>_LH):"
    )
    add_code_block(doc,
        "CREATE TABLE dbo.project_status (\n"
        "    -- Project Scope & Metadata\n"
        "    project_name           STRING,    -- Target project folder name (e.g. 'Automobile', 'Marine')\n"
        "    run_id                 STRING,    -- Pipeline/notebook execution GUID\n"
        "    stage                  STRING,    -- bronze | silver | gold | orchestrator | semantic_model\n"
        "    artifact_name          STRING,    -- Item name (e.g. 'Bronze_Automobile', 'Marine_Medallion_Orchestrator')\n"
        "    \n"
        "    -- High-Level Project Stage & Gate Awareness\n"
        "    current_project_stage  STRING,    -- 0_INIT | 1_BRONZE | 2_SILVER | 3_GOLD | 4_ORCHESTRATED | 5_COMPLETED\n"
        "    overall_project_status STRING,    -- IN_PROGRESS | PAUSED_AT_GATE | COMPLETED | FAILED\n"
        "    current_gate           STRING,    -- Active gate ID (e.g. 'G7a', 'G10a', 'G12c', 'G13c', 'G14c')\n"
        "    next_action_required   STRING,    -- 'Approve Silver Execution', 'Review Gold STTM Mapping', etc.\n"
        "    completion_percentage  INT,       -- 0, 20, 40, 60, 80, 100\n"
        "    \n"
        "    -- Execution Lifecycle & Audit Telemetry\n"
        "    status                 STRING,    -- SUBMITTED | RUNNING | COMPLETED | FAILED | SKIPPED | CANCELLED\n"
        "    load_type              STRING,    -- INITIAL | FULL | INCREMENTAL | SNAPSHOT\n"
        "    triggered_by           STRING,    -- DE_CHAT_SESSION | FABRIC_ORCHESTRATOR | CRON_SCHEDULE\n"
        "    started_at             TIMESTAMP, -- Job start timestamp\n"
        "    updated_at             TIMESTAMP, -- Last update / completion timestamp\n"
        "    duration_seconds       INT,       -- Runtime duration in seconds\n"
        "    tables_processed       INT,       -- Number of tables processed in this stage\n"
        "    records_processed      BIGINT,    -- Input rows processed\n"
        "    records_failed         BIGINT,    -- DQ exceptions / failed rows\n"
        "    error_message          STRING,    -- High-level failure reason if FAILED\n"
        "    log_file_path          STRING     -- Path to diagnostic log file in OneLake\n"
        ");"
    )

    # =========================================================================
    # PART 2: INITIALIZATION, HANDSHAKE & DATA PROFILING (G0 - G5)
    # =========================================================================
    add_heading_1(doc, "Part 2: Handshake, Target Resolution & Data Profiling (Gates G0 – G5)")
    doc.add_paragraph(
        "The initialization phase validates tenant connectivity, workspace context, and raw source lakehouses in Microsoft Fabric. "
        "At Gate G1a (Select Action), the user can either Start a New Project or Resume an Existing Project (which queries dbo.project_status to resume at G-pending)."
    )

    add_heading_2(doc, "2.1 Deep Dive into Data Profiling Architecture")
    doc.add_paragraph(
        "Data profiling is executed via an isolated, read-only PySpark Livy session over the raw source files. "
        "It scans raw files and captures 8 critical data attributes:"
    )
    headers = ["Attribute", "Profiling Description", "Target Medallion Impact"]
    prof_data = [
        ["Row Counts", "Total record counts per source file", "Establishes baseline watermark for Bronze landing checks"],
        ["Physical Data Types", "Inferred source storage types (string, int, float)", "Confirms all-string landing strategy in Bronze"],
        ["NULL Counts & Pct", "Missing value counts and null ratios", "Configures blank-to-null token rules in Silver"],
        ["Distinct Cardinality", "Unique record counts per column", "Identifies candidate business keys for Gold dimensions"],
        ["Min / Max Bounds", "Numerical range bounds and string length bounds", "Detects boundary outliers and numeric scale/precision"],
        ["Date / Time Layouts", "Identifies date formats (yyyy/MM/dd, MM/dd/yyyy, ISO8601)", "Configures regex-gated date parsing strategy in Silver"],
        ["Character Encodings", "Detects text encodings (UTF-8, ASCII, Latin-1)", "Prevents character corruption in Bronze string landing"],
        ["Raw File Stem Mapping", "Extracts table stems (e.g. marine_policy.csv -> marine_policy)", "Sets un-prefixed Delta table names in Bronze and Silver"]
    ]
    build_table(doc, headers, prof_data, [Inches(1.5), Inches(3.2), Inches(2.1)])

    add_heading_2(doc, "2.2 Read-Only Profiling PySpark Implementation")
    code_prof = (
        "# Read-Only Data Profiling Engine (Livy Session)\n"
        "from pyspark.sql import functions as F\n\n"
        "def profile_raw_table(df, table_name):\n"
        "    total_count = df.count()\n"
        "    profile_results = []\n"
        "    for col_name, data_type in df.dtypes:\n"
        "        null_count = df.filter(F.col(col_name).isNull() | (F.trim(F.col(col_name)) == '')).count()\n"
        "        distinct_count = df.select(col_name).distinct().count()\n"
        "        profile_results.append({\n"
        "            'column': col_name,\n"
        "            'type': data_type,\n"
        "            'null_pct': round((null_count / total_count) * 100, 2),\n"
        "            'cardinality': distinct_count\n"
        "        })\n"
        "    return profile_results"
    )
    add_code_block(doc, code_prof)

    # =========================================================================
    # PART 3: BRONZE LAYER RAW LANDING (G6 - G7a)
    # =========================================================================
    add_heading_1(doc, "Part 3: Bronze Layer Raw Landing Architecture (Gates G6 – G7a)")
    doc.add_paragraph(
        "The Bronze layer lands raw source files into high-performance Delta tables inside the Target Lakehouse (<Target>_LH). "
        "It enforces all-string primitive landing (inferSchema=False), un-prefixed source stem table names (bronze.<stem>), single-point column sanitization (sanitize()), and 3 standard audit metadata columns (_source_file, _ingestion_timestamp, _batch_id)."
    )

    add_heading_2(doc, "3.1 Production PySpark Notebook Template (Bronze_<Target>)")
    code_brz = (
        "# ── PARAMETERS ────────────────────────────────────────────────────────\n"
        "target                = \"Marine\"\n"
        "source_lakehouse_name = \"Raw_Insurance_LH\"\n"
        "target_lakehouse_name = \"Marine_LH\"\n"
        "batch_id              = \"run_001\"\n\n"
        "from pyspark.sql import functions as F\n"
        "import datetime\n\n"
        "def write_project_status(stage, status, error_msg=None):\n"
        "    status_df = spark.createDataFrame([(\n"
        "        batch_id, stage, status, datetime.datetime.now(), error_msg\n"
        "    )], [\"run_id\", \"stage\", \"status\", \"updated_at\", \"error_message\"])\n"
        "    status_df.write.format(\"delta\").mode(\"append\").saveAsTable(\"dbo.project_status\")\n\n"
        "def sanitize(df):\n"
        "    for c in df.columns:\n"
        "        clean_name = c.strip().lower().replace(\"%\", \"pct\").replace(\" \", \"_\").replace(\"-\", \"_\")\n"
        "        df = df.withColumnRenamed(c, clean_name)\n"
        "    return df\n\n"
        "try:\n"
        "    tables = [\"marine_policy\", \"marine_claim\"]\n"
        "    for t in tables:\n"
        "        raw_path = f\"Files/Marine/{t}.csv\"\n"
        "        df_raw = spark.read.option(\"header\", \"true\").option(\"inferSchema\", \"false\").csv(raw_path)\n"
        "        df_bronze = (sanitize(df_raw)\n"
        "                     .withColumn(\"_source_file\", F.input_file_name())\n"
        "                     .withColumn(\"_ingestion_timestamp\", F.current_timestamp())\n"
        "                     .withColumn(\"_batch_id\", F.lit(batch_id)))\n"
        "        df_bronze.write.format(\"delta\").mode(\"overwrite\").saveAsTable(f\"bronze.{t}\")\n"
        "    write_project_status(\"bronze\", \"COMPLETED\")\n"
        "except Exception as e:\n"
        "    write_project_status(\"bronze\", \"FAILED\", str(e))\n"
        "    raise e"
    )
    add_code_block(doc, code_brz)

    # =========================================================================
    # PART 4: SILVER LAYER CLEANSING & BUSINESS LOGIC (G8 - G10a)
    # =========================================================================
    add_heading_1(doc, "Part 4: Silver Layer Cleansing & Business Logic Architecture (Gates G8 – G10a)")
    doc.add_paragraph(
        "The Silver layer reads raw string tables from schema bronze, applies data type standardization, cleanses string tokens, "
        "enforces business rules, and outputs clean tables into schema silver (silver.<stem>)."
    )

    add_heading_2(doc, "4.1 5-Level Rule Precedence Hierarchy")
    headers = ["Level", "Authority Source", "Rule Scope & Precedence"]
    prec_data = [
        ["1 (Highest)", "Uploaded Business Rules", "Explicit user/client uploaded rule document at Gate G8 (UPLOAD)"],
        ["2", "Client Rule Overrides", "Global client overrides in client_config.md"],
        ["3", "Default Business Rules", "Standard domain business rules registered in system"],
        ["4", "Basic Transformation Logic", "Generic LOB-independent rules in basic_transformation_logic.md"],
        ["5 (Lowest)", "Failure Registry", "Historical defect fixes in failure_registry.md (must never reintroduce)"]
    ]
    build_table(doc, headers, prec_data, [Inches(1.2), Inches(2.2), Inches(3.4)])

    add_heading_2(doc, "4.2 Production PySpark Notebook Template (Silver_<Target>)")
    code_slv = (
        "# ── PARAMETERS ────────────────────────────────────────────────────────\n"
        "target                = \"Marine\"\n"
        "target_lakehouse_name = \"Marine_LH\"\n"
        "batch_id              = \"run_001\"\n\n"
        "from pyspark.sql import functions as F\n"
        "import datetime\n\n"
        "def write_project_status(stage, status, error_msg=None):\n"
        "    status_df = spark.createDataFrame([(\n"
        "        batch_id, stage, status, datetime.datetime.now(), error_msg\n"
        "    )], [\"run_id\", \"stage\", \"status\", \"updated_at\", \"error_message\"])\n"
        "    status_df.write.format(\"delta\").mode(\"append\").saveAsTable(\"dbo.project_status\")\n\n"
        "try:\n"
        "    df_policy = spark.read.table(\"bronze.marine_policy\")\n"
        "    clean_str = lambda c: F.when(F.trim(F.col(c)).isin(\"\", \"N/A\", \"NULL\"), None).otherwise(F.trim(F.col(c)))\n"
        "    \n"
        "    # ── BR-001: Standardise Policy Status & Dates ───────────────────────\n"
        "    df_silver_policy = (\n"
        "        df_policy\n"
        "        .withColumn(\"policy_no\", clean_str(\"policy_no\"))\n"
        "        .withColumn(\"insured_name\", clean_str(\"insured_name\"))\n"
        "        .withColumn(\"sum_insured\", F.col(\"sum_insured\").cast(\"decimal(18,2)\"))\n"
        "        .withColumn(\"effective_date\", F.when(F.col(\"effective_date\").rlike(r\"^\\d{4}/\\d{2}/\\d{2}$\"), \n"
        "                                             F.to_date(\"effective_date\", \"yyyy/MM/dd\")).otherwise(None))\n"
        "        .withColumn(\"policy_status\", F.when(F.col(\"policy_status\").isin(\"A\", \"ACT\"), F.lit(\"ACTIVE\")).otherwise(F.lit(\"INACTIVE\")))\n"
        "    )\n"
        "    df_silver_policy.write.format(\"delta\").mode(\"overwrite\").saveAsTable(\"silver.marine_policy\")\n"
        "    write_project_status(\"silver\", \"COMPLETED\")\n"
        "except Exception as e:\n"
        "    write_project_status(\"silver\", \"FAILED\", str(e))\n"
        "    raise e"
    )
    add_code_block(doc, code_slv)

    # =========================================================================
    # PART 5: GOLD LAYER DIMENSIONAL MODELING (G11 - G12c)
    # =========================================================================
    add_heading_1(doc, "Part 5: Gold Layer Dimensional Modeling Architecture (Gates G11 – G12c)")
    doc.add_paragraph(
        "The Gold layer structures cleansed Silver data into a Kimball-style star schema (Dimensions and Facts) inside schema gold. "
        "Primary keys use deterministic SHA-256 surrogate keys (<entity>_sk), every dimension prepends a default 'UNKNOWN' row, and primary key grain integrity is verified before writing."
    )

    add_heading_2(doc, "5.1 Production PySpark Notebook Template (Gold_<Target>)")
    code_gld = (
        "# ── PARAMETERS ────────────────────────────────────────────────────────\n"
        "target                = \"Marine\"\n"
        "target_lakehouse_name = \"Marine_LH\"\n"
        "batch_id              = \"run_001\"\n\n"
        "from pyspark.sql import functions as F\n"
        "import datetime\n\n"
        "def write_project_status(stage, status, error_msg=None):\n"
        "    status_df = spark.createDataFrame([(\n"
        "        batch_id, stage, status, datetime.datetime.now(), error_msg\n"
        "    )], [\"run_id\", \"stage\", \"status\", \"updated_at\", \"error_message\"])\n"
        "    status_df.write.format(\"delta\").mode(\"append\").saveAsTable(\"dbo.project_status\")\n\n"
        "def gen_sk(cols):\n"
        "    return F.sha2(F.concat_ws(\"||\", *[F.coalesce(F.trim(F.col(c)), F.lit(\"\")) for c in cols]), 256)\n\n"
        "try:\n"
        "    df_policy_silver = spark.read.table(\"silver.marine_policy\")\n"
        "    df_dim_policy = (df_policy_silver\n"
        "                     .withColumn(\"policy_sk\", gen_sk([\"policy_no\"]))\n"
        "                     .select(\"policy_sk\", \"policy_no\", \"insured_name\", \"policy_status\"))\n"
        "    \n"
        "    # Prepend UNKNOWN record\n"
        "    unknown_row = spark.createDataFrame([(\"UNKNOWN\", \"UNKNOWN\", \"Unknown Insured\", \"UNKNOWN\")], df_dim_policy.schema)\n"
        "    df_dim_policy_final = df_dim_policy.unionByName(unknown_row).distinct()\n"
        "    \n"
        "    # Grain assertion\n"
        "    assert df_dim_policy_final.count() == df_dim_policy_final.select(\"policy_sk\").distinct().count(), \"Grain error!\"\n"
        "    df_dim_policy_final.write.format(\"delta\").mode(\"overwrite\").saveAsTable(\"gold.dim_policy\")\n"
        "    write_project_status(\"gold\", \"COMPLETED\")\n"
        "except Exception as e:\n"
        "    write_project_status(\"gold\", \"FAILED\", str(e))\n"
        "    raise e"
    )
    add_code_block(doc, code_gld)

    # =========================================================================
    # PART 6: WORKFLOW ORCHESTRATION PIPELINE (G13 - G13c)
    # =========================================================================
    add_heading_1(doc, "Part 6: Orchestrator Pipeline Architecture (Gates G13 – G13c)")
    doc.add_paragraph(
        "The Data Factory Orchestrator Pipeline (<Target>_Medallion_Orchestrator) represents Stage 4 of the workflow (preceding Semantic Model creation). "
        "It automates sequential execution of Bronze_<Target> -> Silver_<Target> -> Gold_<Target> using Data Factory notebook activity dependencies."
    )

    add_heading_2(doc, "6.1 Fabric Data Factory Pipeline JSON Spec")
    code_pipe = (
        "{\n"
        "  \"name\": \"Marine_Medallion_Orchestrator\",\n"
        "  \"properties\": {\n"
        "    \"activities\": [\n"
        "      { \"name\": \"Execute_Bronze_Marine\", \"type\": \"TridentNotebook\", \"typeProperties\": { \"notebookId\": \"Bronze_Marine\" } },\n"
        "      { \"name\": \"Execute_Silver_Marine\", \"type\": \"TridentNotebook\", \"typeProperties\": { \"notebookId\": \"Silver_Marine\" },\n"
        "        \"dependsOn\": [ { \"activity\": \"Execute_Bronze_Marine\", \"dependencyConditions\": [\"Succeeded\"] } ] },\n"
        "      { \"name\": \"Execute_Gold_Marine\", \"type\": \"TridentNotebook\", \"typeProperties\": { \"notebookId\": \"Gold_Marine\" },\n"
        "        \"dependsOn\": [ { \"activity\": \"Execute_Silver_Marine\", \"dependencyConditions\": [\"Succeeded\"] } ] }\n"
        "    ]\n"
        "  }\n"
        "}"
    )
    add_code_block(doc, code_pipe)

    # =========================================================================
    # PART 7: DIRECT LAKE SEMANTIC MODEL (G14 - G14c)
    # =========================================================================
    add_heading_1(doc, "Part 7: Direct Lake Semantic Model Architecture (Gates G14 – G14c)")
    doc.add_paragraph(
        "The Direct Lake Semantic Model (<Target>_Gold_Model) represents Stage 5 in the workflow. "
        "It delivers zero-copy Power BI performance directly over Gold Delta parquet files in OneLake using TMDL definitions."
    )

    add_heading_2(doc, "7.1 TMDL Definition & DAX Measures Snippet")
    code_tmdl = (
        "model Model\n"
        "    culture: en-US\n\n"
        "table dim_policy\n"
        "    column policy_sk\n"
        "        dataType: string\n"
        "        sourceColumn: policy_sk\n"
        "    column policy_no\n"
        "        dataType: string\n"
        "        sourceColumn: policy_no\n\n"
        "table fact_claim\n"
        "    column claim_amount\n"
        "        dataType: decimal\n"
        "        sourceColumn: claim_amount\n"
        "    measure Total_Claims = COUNT(fact_claim[claim_id])\n"
        "    measure Total_Claim_Amount = SUM(fact_claim[claim_amount])\n"
        "    measure Loss_Ratio = DIVIDE([Total_Claim_Amount], SUM(dim_policy[sum_insured]), 0)"
    )
    add_code_block(doc, code_tmdl)

    # =========================================================================
    # PART 8: MASTER GATE DICTIONARY & FULL TRANSCRIPT (G0 - G15)
    # =========================================================================
    add_heading_1(doc, "Part 8: Master Gate Dictionary & Continuous Master Transcript (Gates G0 – G15)")
    doc.add_paragraph("The table below details all 27 conversational gates across the complete medallion lifecycle:")

    headers = ["Gate", "Stage", "User Question / Prompt", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G0", "Start", "Welcome to AI Native Data Engineering", "N/A", "Checks Azure CLI connection. Active -> G0b; Inactive -> G0a."],
        ["G0a", "Start", "Fabric workspace connection is not active. Authenticate via Azure CLI?", "[y/n]", "y runs az login -> G0b; n prints thank-you message and stops."],
        ["G0b", "Setup", "Select Workspace: press 1 for <W1>, 2 for <W2> or S to stop", "[1/2/.../S]", "Sets {workspace} context. S prints thank-you message."],
        ["G1a", "Setup", "Select Action: 1 Start new project, 2 Resume, 3 Stop", "[1/2/3]", "1 asks G1 to select Source Lakehouse; 2 performs 2-tier project discovery (root lakehouses & target folders for dbo.project_status) to resume at G-pending; 3 stops."],
        ["G1", "Setup", "Should I list the lakehouses in {workspace}?", "[y/n]", "y lists lakehouses, user selects Source Lakehouse {raw_lakehouse}, and lists raw folders -> G2; n stops."],
        ["G2", "Setup", "Target Resolution: Enter or confirm target folder name (Suggested: <Derived_Name>):", "[y/n/<target_folder_name>]", "y accepts derived name; <target_folder_name> sets custom folder name. Creates target folder <target_folder_name> (<target_folder_name>_LH, notebooks, orchestrator, semantic model). Target LH creation deferred. n stops."],
        ["G2b", "Setup", "Target folder created (Target LH created on execution). Show file details in folder <folder>?", "[y/n]", "y displays file sizes, partition paths, and raw stem table mappings. n stops."],
        ["G4", "Profile", "Run data profiling on <Target> raw tables?", "[y/n]", "y runs read-only Livy session profiling. n stops."],
        ["G5", "Profile", "Are you satisfied with the data profile?", "[APPROVE/DECLINE]", "APPROVE holds attributes in memory -> G6. DECLINE runs issues loop."],
        ["G6", "Bronze", "Generate Bronze notebook for <Target> into schema {bronze_schema}?", "[y/n]", "y generates Bronze_<Target> (table names match raw stems). n stops."],
        ["G7", "Bronze", "DE review – approve Bronze notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Bronze_<Target> to Fabric. DECLINE runs issues loop."],
        ["G7a", "Bronze", "Run Bronze notebook now?", "[y/n/skip]", "y submits Bronze_<Target> asynchronously in background -> prompts [1/2/3] (1 move to next stage, 2 poll status, 3 stop chat session); skip moves directly to G8; n stops."],
        ["G8", "Silver", "Upload business rules for Silver", "[UPLOAD/SKIP]", "UPLOAD parses rules & outputs Business Rules Understanding Summary -> G9; SKIP stops."],
        ["G9", "Silver", "Generate Silver notebook for <Target>?", "[y/n]", "y generates Silver_<Target> (source stem table names). n stops."],
        ["G10", "Silver", "DE review – approve Silver notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Silver_<Target> & registers rules. DECLINE runs issues loop."],
        ["G10a","Silver", "Run Silver notebook now?", "[y/n/skip]", "y submits Silver_<Target> asynchronously in background -> prompts [1/2/3] (1 move to next stage, 2 poll status, 3 stop chat session); skip moves directly to G11; n stops."],
        ["G11", "Gold", "Upload client-style STTM document for Gold modeling", "[UPLOAD/SKIP]", "UPLOAD parses STTM & outputs STTM Understanding Summary -> G12; SKIP stops."],
        ["G12", "Gold", "Approve Gold model and generate Gold notebook?", "[APPROVE/DECLINE]", "APPROVE writes gold_model.yaml & generates Gold_<Target>. DECLINE runs model issues loop."],
        ["G12b","Gold", "DE review – approve Gold notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Gold_<Target> to Fabric. DECLINE runs code issues loop."],
        ["G12c","Gold", "Run Gold notebook now?", "[y/n/skip]", "y submits Gold_<Target> asynchronously in background -> prompts [1/2/3] (1 move to next stage, 2 poll status, 3 stop chat session); skip moves directly to G13; n stops."],
        ["G13", "Orchestrator", "Create orchestrator pipeline (<Target>_Medallion_Orchestrator)?", "[y/n]", "y prompts G13a/b, deploys Orchestrator Pipeline to Fabric. n stops."],
        ["G13a/b","Orchestrator", "Source Lakehouse? / Target Lakehouse?", "[1/2/...]", "Sets source raw lakehouse and target medallion lakehouse."],
        ["G13c","Orchestrator", "Run orchestrator now?", "[y/n/skip]", "y submits Orchestrator Pipeline asynchronously in background -> prompts [1/2/3] (1 move to next stage, 2 poll status, 3 stop chat session); skip moves directly to G14; n stops."],
        ["G14", "Semantic", "Generate Direct Lake semantic model on <Target> Gold?", "[y/n]", "y builds Direct Lake semantic model <Target>_Gold_Model -> G14b. n stops."],
        ["G14b","Semantic", "Approve semantic model?", "[APPROVE/DECLINE]", "APPROVE deploys <Target>_Gold_Model TMDL definition to Fabric. DECLINE runs issues loop."],
        ["G14c","Semantic", "Refresh semantic model dataset now?", "[y/n/skip]", "y submits dataset refresh asynchronously in background -> prompts [1/2/3] (1 move to next stage, 2 poll status, 3 stop chat session); skip moves directly to G15; n stops."],
        ["G15", "Close", "Process another dataset?", "[y/n]", "Displays summary matrix. y resets to G2; n stops cleanly."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.2)])

    add_heading_2(doc, "8.1 Complete End-to-End Master Execution Transcript")
    transcript = (
        "[Complete Continuous Marine Dataset Run]\n"
        "USER: START\n"
        "AI: Welcome to AI Native Data Engineering\n"
        "G0-G2b: Connected to DataSonic 3 -> Source: Raw_Insurance_LH -> Action 1 (Start new project) -> Folder: Marine -> Dynamic Target Resolved: Marine -> Created Target: Marine_LH.\n"
        "G4-G5: Live Data Profiling completed -> Attributes saved in execution memory.\n"
        "G6-G7a: Deployed & Executed Bronze_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G8-G10a: Uploaded marine_business_rules.json -> Deployed & Executed Silver_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G11-G12c: Uploaded marine_sttm.xlsx -> Deployed & Executed Gold_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G13-G13c: Deployed & Executed Marine_Medallion_Orchestrator -> Status COMPLETED in dbo.project_status.\n"
        "G14-G14c: Deployed & Refreshed Marine_Gold_Model -> Status COMPLETED in dbo.project_status.\n"
        "G15: Process another dataset? [y/n]\n"
        "USER: n\n"
        "AI: Session closed for Marine. Thank you!"
    )
    add_callout(doc, transcript)

    doc.save(MASTER_FILE_PATH)
    print(f"Master Consolidated Guide generated at: {MASTER_FILE_PATH}")

if __name__ == "__main__":
    generate_master_guide()
