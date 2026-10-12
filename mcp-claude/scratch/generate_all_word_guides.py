import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = r"c:\Users\nikhi\Downloads\mcp-claude"

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
    run.font.size = Pt(22)
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

# ---------------------------------------------------------
# DOCUMENT 1: 01_Setup_And_Data_Profiling_Explanation.docx
# ---------------------------------------------------------
def generate_doc_1():
    doc = Document()
    add_header(doc, "01. Setup, Environment Connection & Data Profiling", "Zero-Config Medallion Architecture — Comprehensive Setup & Profiling Reference")

    add_heading_1(doc, "1. Architecture & Tenant Handshake Protocol (Gates G0 – G1a)")
    doc.add_paragraph(
        "The initialization phase validates tenant connectivity, workspace context, and raw source lakehouses in Microsoft Fabric. "
        "The process begins with an Azure CLI connection check (Gate G0). If authentication is active, the system fetches available workspaces (Gate G0b). "
        "The user selects a target workspace, and the system queries OneLake storage via Fabric REST APIs to discover raw source lakehouses (Gate G1)."
    )
    doc.add_paragraph(
        "At Gate G1a (Select Action), the user chooses between two distinct execution workflows:\n"
        "1. Start a New Project: Scans raw source lakehouse folders and initiates a fresh medallion build.\n"
        "2. Resume an Existing Project: Performs 2-tier project discovery in the workspace (checking root lakehouses and workspace target folders for dbo.project_status), "
        "queries dbo.project_status in the selected project, determines completed stages (COMPLETED/SKIPPED), orders by updated_at DESC, and prompts at the exact pending gate (G-pending)."
    )

    add_heading_1(doc, "2. Zero-Config Dynamic Target Resolution (Gates G2 – G2b)")
    doc.add_paragraph(
        "Prior medallion architectures required static configuration directories (.claude/skills/medallion/lob/<lob>.md) and static datasets. "
        "The Zero-Config Medallion Architecture completely eliminates static LOB config files and datasets folders. Instead, target resolution happens dynamically at Gate G2:"
    )
    add_callout(doc, 
        "Dynamic Target Resolution at Gate G2:\n"
        "1. The AI inspects the selected raw source folder (e.g. 'Marine') and derives a clean target folder name (<Derived_Name>).\n"
        "2. The AI prompts: 'Target Resolution: Enter or confirm target folder name (Suggested: <Derived_Name>): [y/n/<target_folder_name>]'\n"
        "3. User Options:\n"
        "   - 'y': Accepts derived target folder name (<Derived_Name>).\n"
        "   - '<target_folder_name>': Overrides with a custom write-in target folder name.\n"
        "   - 'n': Displays a courteous thank-you message and stops execution cleanly.\n"
        "4. Creation: The AI creates target folder <target_folder_name> containing directly <target_folder_name>_LH, notebooks, orchestrator, semantic model. Target Lakehouse creation is deferred until notebook/orchestrator execution."
    )

    add_heading_1(doc, "3. Deep Dive into Data Profiling Architecture (Gates G4 – G5)")
    doc.add_paragraph(
        "Data profiling is executed via an isolated, read-only PySpark Livy session over the raw source files. "
        "The profiling engine scans every source file without modifying raw data or writing persistent files. It captures 8 critical data attributes:"
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

    add_heading_1(doc, "4. Master Gate Dictionary (G0 – G5)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G0", "Start", "Welcome to AI Native Data Engineering", "N/A", "Checks Azure CLI status. Active -> G0b; Inactive -> G0a."],
        ["G0a", "Start", "Fabric workspace connection is not active. Authenticate via Azure CLI?", "[y/n]", "y runs az login -> G0b; n prints thank-you exit message."],
        ["G0b", "Setup", "Select Workspace: press 1 for <W1>, 2 for <W2> or S to stop", "[1/2/.../S]", "Sets active {workspace} context. S exits cleanly."],
        ["G1", "Setup", "Should I list the lakehouses in {workspace}?", "[y/n]", "y lists lakehouses for source selection. n exits cleanly."],
        ["G1a", "Setup", "Select Action: 1 Start new project, 2 Resume, 3 Stop", "[1/2/3]", "1 lists raw folders. 2 performs 2-tier project discovery (checking root lakehouses and target folders for dbo.project_status) to resume at G-pending. 3 exits."],
        ["G2", "Setup", "Target Resolution: Enter or confirm target folder name (Suggested: <Derived_Name>):", "[y/n/<target_folder_name>]", "y accepts derived name; <target_folder_name> sets custom folder. Creates target folder <target_folder_name> (<target_folder_name>_LH, notebooks, orchestrator, semantic model). Target LH creation deferred. n exits."],
        ["G2b", "Setup", "Target folder created (Target LH created on execution). Show file details in folder <folder>?", "[y/n]", "y displays file sizes, partition paths, and raw stem table mappings. n exits."],
        ["G4", "Profile", "Run data profiling on <Target> raw tables?", "[y/n]", "y runs read-only Livy session profiling. n exits."],
        ["G5", "Profile", "Are you satisfied with the data profile?", "[APPROVE/DECLINE]", "APPROVE saves attributes in session memory -> G6. DECLINE runs issues loop."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.5), Inches(0.8), Inches(2.5), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "5. Data Profiling PySpark Implementation Snippet")
    code = (
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
    add_code_block(doc, code)

    add_heading_1(doc, "6. End-to-End Execution Walkthrough & Transcript")
    transcript = (
        "USER: START\n"
        "AI: Welcome to AI Native Data Engineering on Microsoft Fabric.\n"
        "Checking Fabric workspace authentication...\n"
        "Active Connection Verified: User logged into Tenant 'DataSonic Global'.\n\n"
        "G0b: Select Workspace: press 1 for Production_Analytics, 2 for DataSonic_Workspace, or S to stop.\n"
        "USER: 2\n"
        "AI: Workspace set to 'DataSonic_Workspace'.\n\n"
        "G1: Should I list the lakehouses in DataSonic_Workspace? [y/n]\n"
        "USER: y\n"
        "AI: Available Lakehouses:\n"
        "1. Raw_Insurance_LH\n"
        "2. Financial_Landing_LH\n\n"
        "G1a: Select Action: 1 Start new project, 2 Resume existing project, 3 Stop\n"
        "USER: 1\n"
        "AI: Selected Action: Start new project. Scanning folders in Raw_Insurance_LH...\n"
        "Discovered Raw Source Folder: 'Marine'\n\n"
        "G2: Target Resolution: Enter or confirm target folder name (Suggested: Marine): [y/n/<target_folder_name>]\n"
        "USER: y\n"
        "AI: Target folder 'Marine' created (Target Lakehouse 'Marine_LH' will be created on notebook/orchestrator execution).\n\n"
        "G2b: Show file details in folder 'Marine'? [y/n]\n"
        "USER: y\n"
        "AI: File Details in Raw_Insurance_LH/Files/Marine:\n"
        "- marine_policy.csv (14.2 MB, 15,420 rows) -> Stem: marine_policy\n"
        "- marine_claim.csv (4.8 MB, 4,310 rows) -> Stem: marine_claim\n\n"
        "G4: Run data profiling on Marine raw tables? [y/n]\n"
        "USER: y\n"
        "AI: Executing read-only Livy profiling session on marine_policy and marine_claim...\n"
        "Profiling Summary:\n"
        "- marine_policy: 15,420 rows, 18 columns. Key candidate: policy_no. Date format detected: yyyy/MM/dd.\n"
        "- marine_claim: 4,310 rows, 12 columns. Key candidate: claim_id. Date format detected: yyyy/MM/dd.\n\n"
        "G5: Are you satisfied with the data profile? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: Data profile approved. Profile attributes stored in session execution memory. Ready for Bronze layer generation (Gate G6)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "01_Setup_And_Data_Profiling_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 2: 02_Bronze_Layer_Raw_Landing_Explanation.docx
# ---------------------------------------------------------
def generate_doc_2():
    doc = Document()
    add_header(doc, "02. Bronze Layer Raw Landing Architecture", "Zero-Config Medallion Architecture — Gates G6 to G7a")

    add_heading_1(doc, "1. Bronze Layer Design Principles")
    doc.add_paragraph(
        "The Bronze layer is responsible for landing raw source files into high-performance Delta tables inside the Target Lakehouse (<Target>_LH). "
        "It operates under 4 strict data engineering principles:"
    )
    doc.add_paragraph(
        "1. All-String Primitive Landing (inferSchema=False): Raw CSV/JSON files are ingested strictly as strings. No data type casting occurs in Bronze, preventing ingestion job failures caused by source schema drift.\n"
        "2. Un-Prefixed Source Stem Naming: Table names match raw file stems directly (e.g., marine_policy.csv -> bronze.marine_policy). Legacy prefixes (01_bronze_) are completely dropped.\n"
        "3. Single-Point Column Sanitization (sanitize()): Column names are standardized once at Bronze landing (lowercase, spaces/hyphens to _, % to pct). Downstream Silver/Gold layers inherit these names without re-sanitizing.\n"
        "4. Streamlined Audit Metadata: Exactly 3 audit columns (_source_file, _ingestion_timestamp, _batch_id) are appended to every landed row."
    )

    add_heading_1(doc, "2. Single Control Table Integration (dbo.project_status)")
    doc.add_paragraph(
        "The Medallion architecture operates under a 100% Single Control Table Architecture. "
        "Execution progress, project stage progression, runtime telemetry, and fail-fast reconciliation tracebacks are recorded directly in the Delta table dbo.project_status within the Target Lakehouse:"
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

    add_heading_1(doc, "3. Gate Dictionary (G6 – G7a)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G6", "Bronze", "Generate Bronze notebook for <Target> into schema {bronze_schema}?", "[y/n]", "y generates Bronze_<Target> with un-prefixed stem names. n exits cleanly."],
        ["G7", "Bronze", "DE review – approve Bronze notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Bronze_<Target> to Fabric. DECLINE triggers interactive code issues loop."],
        ["G7a", "Bronze", "Run Bronze notebook now?", "[y/n]", "y executes Bronze_<Target> via Fabric API, appends status to dbo.project_status. Success -> G8; Failure -> Error recovery loop; n -> Exit thank-you message."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "4. Production PySpark Notebook Template (Bronze_<Target>)")
    code = (
        "# ── PARAMETERS ────────────────────────────────────────────────────────\n"
        "target                = \"Marine\"\n"
        "source_lakehouse_name = \"Raw_Insurance_LH\"\n"
        "target_lakehouse_name = \"Marine_LH\"\n"
        "batch_id              = \"run_001\"\n\n"
        "# ── SETUP SPARK & LOGGING ─────────────────────────────────────────────\n"
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
        "# ── CORE BRONZE LANDING LOOP ──────────────────────────────────────────\n"
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
    add_code_block(doc, code)

    add_heading_1(doc, "5. Real-World Execution Walkthrough & Transcript")
    transcript = (
        "G6: Generate Bronze notebook for Marine into schema 'bronze'? [y/n]\n"
        "USER: y\n"
        "AI: Generating notebook 'Bronze_Marine'...\n"
        "Notebook Code Summary:\n"
        "- Tables targeted: bronze.marine_policy, bronze.marine_claim\n"
        "- Audit columns added: _source_file, _ingestion_timestamp, _batch_id\n"
        "- Storage mode: overwrite per source stem\n\n"
        "G7: DE review – approve Bronze notebook? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: Notebook 'Bronze_Marine' deployed to Fabric workspace 'DataSonic_Workspace'.\n\n"
        "G7a: Run Bronze notebook now? [y/n]\n"
        "USER: y\n"
        "AI: Executing Bronze_Marine in Fabric...\n"
        "Execution Outcome: COMPLETED (Duration: 14s)\n"
        "Tables Written:\n"
        "- bronze.marine_policy: 15,420 rows loaded\n"
        "- bronze.marine_claim: 4,310 rows loaded\n"
        "Status appended to dbo.project_status: (run_001, bronze, COMPLETED, 2026-10-06 09:15:00)\n\n"
        "Bronze layer finished successfully. Proceeding to Silver layer (Gate G8)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "02_Bronze_Layer_Raw_Landing_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 3: 03_Silver_Layer_Cleansing_Business_Logic_Explanation.docx
# ---------------------------------------------------------
def generate_doc_3():
    doc = Document()
    add_header(doc, "03. Silver Layer Cleansing & Business Logic Architecture", "Zero-Config Medallion Architecture — Gates G8 to G10a")

    add_heading_1(doc, "1. Silver Layer Transformation Principles")
    doc.add_paragraph(
        "The Silver layer reads raw string tables from the Bronze schema (`bronze.<stem>`), applies data type standardization, "
        "cleanses string tokens, enforces business rules, and outputs validated, clean tables into schema `silver` (`silver.<stem>`)."
    )
    doc.add_paragraph(
        "Key Transformation Disciplines:\n"
        "1. Closed Schema Contract: No temporary calculation or debug columns are written to Silver. Columns match the approved Silver contract.\n"
        "2. Fail-Safe Type Casting: Type conversions use regex-gated parsing or try_cast(). Unparseable bad values become SQL NULL and are logged in dbo.transformation_exceptions.\n"
        "3. Zero Fake Data Fabrication: Invalid numbers or dates are NEVER coerced into 0, FALSE, or today's date.\n"
        "4. Null Token Normalization: Empty strings (''), whitespace ('   '), and tokens like 'N/A' or 'NULL' are standardized to SQL NULL.\n"
        "5. Traceability Comments: Code blocks are explicitly tagged with authority markers (# BR-xxx for uploaded rules, # Basic §x for basic logic)."
    )

    add_heading_1(doc, "2. Precedence Hierarchy")
    headers = ["Level", "Authority Source", "Rule Scope & Precedence"]
    prec_data = [
        ["1 (Highest)", "Uploaded Business Rules", "Explicit user/client uploaded rule document at Gate G8 (UPLOAD)"],
        ["2", "Client Rule Overrides", "Global client overrides in client_config.md"],
        ["3", "Default Business Rules", "Standard domain business rules registered in system"],
        ["4", "Basic Transformation Logic", "Generic LOB-independent rules in basic_transformation_logic.md"],
        ["5 (Lowest)", "Failure Registry", "Historical defect fixes in failure_registry.md (must never reintroduce)"]
    ]
    build_table(doc, headers, prec_data, [Inches(1.2), Inches(2.2), Inches(3.4)])

    add_heading_1(doc, "3. Gate Dictionary (G8 – G10a)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G8", "Silver", "Upload business rules for Silver", "[UPLOAD/SKIP]", "UPLOAD parses rules document -> G9. SKIP prints thank-you message and stops execution."],
        ["G9", "Silver", "Generate Silver notebook for <Target>?", "[y/n]", "y generates Silver_<Target> applying merged rule set. n exits cleanly."],
        ["G10", "Silver", "DE review – approve Silver notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Silver_<Target> to Fabric. DECLINE triggers issues loop."],
        ["G10a","Silver", "Run Silver notebook now?", "[y/n]", "y executes Silver_<Target>, appends status to dbo.project_status. Success -> G11; Failure -> Recovery prompt; n -> Exit thank-you message."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "4. Production PySpark Notebook Template (Silver_<Target>)")
    code = (
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
        "    # Read Bronze\n"
        "    df_policy = spark.read.table(\"bronze.marine_policy\")\n"
        "    \n"
        "    # ── Basic §5: Blank -> NULL Normalisation ─────────────────────────\n"
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
        "    \n"
        "    df_silver_policy.write.format(\"delta\").mode(\"overwrite\").saveAsTable(\"silver.marine_policy\")\n"
        "    write_project_status(\"silver\", \"COMPLETED\")\n"
        "except Exception as e:\n"
        "    write_project_status(\"silver\", \"FAILED\", str(e))\n"
        "    raise e"
    )
    add_code_block(doc, code)

    add_heading_1(doc, "5. Real-World Execution Walkthrough & Transcript")
    transcript = (
        "G8: Upload business rules for Silver [UPLOAD/SKIP]\n"
        "USER: UPLOAD\n"
        "AI: Uploaded file 'marine_business_rules.json' received and validated.\n"
        "Parsed 4 custom business rules: BR-001 (Policy Status), BR-002 (Claim Deductible), BR-003 (Vessel Category), BR-004 (Currency FX).\n\n"
        "G9: Generate Silver notebook for Marine? [y/n]\n"
        "USER: y\n"
        "AI: Generating notebook 'Silver_Marine'...\n\n"
        "G10: DE review – approve Silver notebook? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: Notebook 'Silver_Marine' deployed to Fabric workspace 'DataSonic_Workspace'.\n\n"
        "G10a: Run Silver notebook now? [y/n]\n"
        "USER: y\n"
        "AI: Executing Silver_Marine in Fabric...\n"
        "Execution Outcome: COMPLETED (Duration: 18s)\n"
        "Tables Written:\n"
        "- silver.marine_policy: 15,420 rows cleansed\n"
        "- silver.marine_claim: 4,310 rows cleansed\n"
        "Status appended to dbo.project_status: (run_001, silver, COMPLETED, 2026-10-06 09:17:00)\n\n"
        "Silver layer finished successfully. Proceeding to Gold layer (Gate G11)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "03_Silver_Layer_Cleansing_Business_Logic_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 4: 04_Gold_Layer_Dimensional_Modeling_Explanation.docx
# ---------------------------------------------------------
def generate_doc_4():
    doc = Document()
    add_header(doc, "04. Gold Layer Dimensional Modeling Architecture", "Zero-Config Medallion Architecture — Gates G11 to G12c")

    add_heading_1(doc, "1. Gold Layer Star-Schema Design Principles")
    doc.add_paragraph(
        "The Gold layer transforms cleansed Silver data into a Kimball-style star schema (Dimensions and Facts) inside schema `gold`. "
        "It provides optimized star-schema tables for Direct Lake reporting in Power BI."
    )
    doc.add_paragraph(
        "Core Senior DE Standards:\n"
        "1. Deterministic SHA-256 Surrogate Keys (<entity>_sk): Primary keys are generated deterministically using SHA-256 hashes of natural key columns (sha256(concat_ws('||', natural_keys))). Non-deterministic auto-increment sequences (monotonically_increasing_id) are strictly forbidden.\n"
        "2. Client STTM Driven: Gold table names, dimensional attributes, and fact measures are derived directly from the Data Engineer's uploaded STTM (Source-to-Target Mapping) document at Gate G11.\n"
        "3. Default 'Unknown' Row Pattern: Every dimension table prepends a synthetic 'UNKNOWN' record (_sk = 'UNKNOWN' or -1) to prevent orphaned fact records from breaking referential integrity in Power BI.\n"
        "4. Grain Verification Assertions: Before writing to Delta, notebooks explicitly assert that row counts equal distinct surrogate key counts."
    )

    add_heading_1(doc, "2. Gate Dictionary (G11 – G12c)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G11", "Gold", "Upload client-style STTM document for Gold modeling", "[UPLOAD/SKIP]", "UPLOAD parses STTM -> G12. SKIP prints thank-you message and stops execution."],
        ["G12", "Gold", "Approve Gold model and generate Gold notebook?", "[APPROVE/DECLINE]", "APPROVE generates gold_model.yaml & Gold_<Target> notebook. DECLINE triggers model issues loop."],
        ["G12b","Gold", "DE review – approve Gold notebook?", "[APPROVE/DECLINE]", "APPROVE deploys Gold_<Target> to Fabric. DECLINE triggers code issues loop."],
        ["G12c","Gold", "Run Gold notebook now?", "[y/n]", "y executes Gold_<Target>, appends status to dbo.project_status. Success -> G13 (Orchestrator); Failure -> Recovery prompt; n -> Exit thank-you message."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "3. Production PySpark Notebook Template (Gold_<Target>)")
    code = (
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
        "    \n"
        "    # Build dim_policy with SHA-256 SK\n"
        "    df_dim_policy = (df_policy_silver\n"
        "                     .withColumn(\"policy_sk\", gen_sk([\"policy_no\"]))\n"
        "                     .select(\"policy_sk\", \"policy_no\", \"insured_name\", \"policy_status\"))\n"
        "    \n"
        "    # Add UNKNOWN row\n"
        "    unknown_row = spark.createDataFrame([(\"UNKNOWN\", \"UNKNOWN\", \"Unknown Insured\", \"UNKNOWN\")], df_dim_policy.schema)\n"
        "    df_dim_policy_final = df_dim_policy.unionByName(unknown_row).distinct()\n"
        "    \n"
        "    # Grain assertion\n"
        "    assert df_dim_policy_final.count() == df_dim_policy_final.select(\"policy_sk\").distinct().count(), \"Grain error!\"\n"
        "    \n"
        "    df_dim_policy_final.write.format(\"delta\").mode(\"overwrite\").saveAsTable(\"gold.dim_policy\")\n"
        "    write_project_status(\"gold\", \"COMPLETED\")\n"
        "except Exception as e:\n"
        "    write_project_status(\"gold\", \"FAILED\", str(e))\n"
        "    raise e"
    )
    add_code_block(doc, code)

    add_heading_1(doc, "4. Real-World Execution Walkthrough & Transcript")
    transcript = (
        "G11: Upload client-style STTM document for Gold modeling [UPLOAD/SKIP]\n"
        "USER: UPLOAD\n"
        "AI: Uploaded file 'marine_sttm.xlsx' parsed successfully.\n"
        "Gold Model Spec Generated:\n"
        "- Dimensions: gold.dim_policy, gold.dim_vessel\n"
        "- Facts: gold.fact_claim\n"
        "- Measures: Total_Claims, Total_Claim_Amount, Loss_Ratio\n\n"
        "G12: Approve Gold model and generate Gold notebook? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: Model specification written to gold_model.yaml. Generating notebook 'Gold_Marine'...\n\n"
        "G12b: DE review – approve Gold notebook? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: Notebook 'Gold_Marine' deployed to Fabric workspace 'DataSonic_Workspace'.\n\n"
        "G12c: Run Gold notebook now? [y/n]\n"
        "USER: y\n"
        "AI: Executing Gold_Marine in Fabric...\n"
        "Execution Outcome: COMPLETED (Duration: 22s)\n"
        "Tables Written:\n"
        "- gold.dim_policy: 14,801 rows (including UNKNOWN record)\n"
        "- gold.dim_vessel: 8,921 rows (including UNKNOWN record)\n"
        "- gold.fact_claim: 4,310 rows loaded with valid foreign SKs\n"
        "Status appended to dbo.project_status: (run_001, gold, COMPLETED, 2026-10-06 09:30:00)\n\n"
        "Gold layer finished successfully. Proceeding to Orchestrator Pipeline (Gate G13)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "04_Gold_Layer_Dimensional_Modeling_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 5: 05_Orchestration_WrapUp_Explanation.docx
# ---------------------------------------------------------
def generate_doc_5():
    doc = Document()
    add_header(doc, "05. Orchestrator Pipeline Architecture", "Zero-Config Medallion Architecture — Gates G13 to G13c")

    add_heading_1(doc, "1. Fabric Data Factory Orchestrator Pipeline Principles")
    doc.add_paragraph(
        "The Data Factory Orchestrator Pipeline (`<Target>_Medallion_Orchestrator`) represents Stage 4 of the workflow. "
        "It automates sequential execution of the Bronze, Silver, and Gold notebooks in Microsoft Fabric."
    )
    doc.add_paragraph(
        "Key Design Standards:\n"
        "1. Stage 4 Positioning: The Orchestrator Pipeline is ALWAYS created and deployed before constructing the Direct Lake Semantic Model (Stage 5).\n"
        "2. Un-Prefixed Pipeline Naming: Follows the exact pattern `<Target>_Medallion_Orchestrator` (e.g. Marine_Medallion_Orchestrator).\n"
        "3. Sequential Dependencies: Executes Bronze_<Target> -> Silver_<Target> -> Gold_<Target> sequentially using activity dependency wires.\n"
        "4. Status Logging: Upon completion or failure, the pipeline appends a stage execution row to dbo.project_status."
    )

    add_heading_1(doc, "2. Gate Dictionary (G13 – G13c)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G13", "Orchestrator", "Create orchestrator pipeline (<Target>_Medallion_Orchestrator)?", "[y/n]", "y prompts G13a/b and deploys Orchestrator Pipeline. n exits cleanly."],
        ["G13a/b","Orchestrator", "Source Lakehouse? / Target Lakehouse?", "[1/2/...]", "Sets source raw lakehouse and target medallion lakehouse parameters."],
        ["G13c","Orchestrator", "Run orchestrator now?", "[y/n]", "y executes Orchestrator Pipeline via Fabric API, appends status to dbo.project_status. Success -> G14; Failure -> Recovery prompt; n -> Exit thank-you message."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "3. Fabric Pipeline JSON Definition Snippet")
    code = (
        "{\n"
        "  \"name\": \"Marine_Medallion_Orchestrator\",\n"
        "  \"properties\": {\n"
        "    \"activities\": [\n"
        "      {\n"
        "        \"name\": \"Execute_Bronze_Marine\",\n"
        "        \"type\": \"TridentNotebook\",\n"
        "        \"typeProperties\": { \"notebookId\": \"Bronze_Marine\" }\n"
        "      },\n"
        "      {\n"
        "        \"name\": \"Execute_Silver_Marine\",\n"
        "        \"type\": \"TridentNotebook\",\n"
        "        \"typeProperties\": { \"notebookId\": \"Silver_Marine\" },\n"
        "        \"dependsOn\": [ { \"activity\": \"Execute_Bronze_Marine\", \"dependencyConditions\": [\"Succeeded\"] } ]\n"
        "      },\n"
        "      {\n"
        "        \"name\": \"Execute_Gold_Marine\",\n"
        "        \"type\": \"TridentNotebook\",\n"
        "        \"typeProperties\": { \"notebookId\": \"Gold_Marine\" },\n"
        "        \"dependsOn\": [ { \"activity\": \"Execute_Silver_Marine\", \"dependencyConditions\": [\"Succeeded\"] } ]\n"
        "      }\n"
        "    ]\n"
        "  }\n"
        "}"
    )
    add_code_block(doc, code)

    add_heading_1(doc, "4. Real-World Execution Walkthrough & Transcript")
    transcript = (
        "G13: Create orchestrator pipeline (Marine_Medallion_Orchestrator)? [y/n]\n"
        "USER: y\n"
        "AI: G13a: Select Source Lakehouse: 1. Raw_Insurance_LH\n"
        "USER: 1\n"
        "AI: G13b: Select Target Lakehouse: 1. Marine_LH\n"
        "USER: 1\n"
        "AI: Deploying Data Factory Orchestrator Pipeline 'Marine_Medallion_Orchestrator' to Fabric...\n\n"
        "G13c: Run orchestrator now? [y/n]\n"
        "USER: y\n"
        "AI: Triggering Orchestrator Pipeline Marine_Medallion_Orchestrator execution...\n"
        "Activity 1: Execute_Bronze_Marine -> COMPLETED (12s)\n"
        "Activity 2: Execute_Silver_Marine -> COMPLETED (16s)\n"
        "Activity 3: Execute_Gold_Marine -> COMPLETED (20s)\n"
        "Pipeline Execution Status: COMPLETED (Total Duration: 48s)\n"
        "Status appended to dbo.project_status: (run_001, orchestrator, COMPLETED, 2026-10-06 09:32:00)\n\n"
        "Orchestrator Pipeline finished successfully. Proceeding to Direct Lake Semantic Model (Gate G14)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "05_Orchestration_WrapUp_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 6: 06_Semantic_Model_Layer_Explanation.docx
# ---------------------------------------------------------
def generate_doc_6():
    doc = Document()
    add_header(doc, "06. Direct Lake Semantic Model Architecture", "Zero-Config Medallion Architecture — Gates G14 to G14c")

    add_heading_1(doc, "1. Direct Lake Semantic Model Principles")
    doc.add_paragraph(
        "The Direct Lake Semantic Model (`<Target>_Gold_Model`) represents Stage 5 in the workflow (after Orchestrator Pipeline deployment). "
        "It provides high-performance zero-copy Power BI reporting directly over Gold Delta parquet files in OneLake."
    )
    doc.add_paragraph(
        "Core Architecture Features:\n"
        "1. Model Naming: Named explicitly as `<Target>_Gold_Model` (e.g. Marine_Gold_Model).\n"
        "2. TMDL Representation: Constructed using Tabular Model Definition Language (TMDL), defining tables, surrogate key relationships, and DAX measures.\n"
        "3. Automated Dataset Refresh: Executed via REST API (`POST /v1/workspaces/{workspace_id}/datasets/{dataset_id}/refreshes`).\n"
        "4. Status Logging: Appends status row to `dbo.project_status` in Target Lakehouse upon refresh completion."
    )

    add_heading_1(doc, "2. Gate Dictionary (G14 – G14c)")
    headers = ["Gate", "Stage", "Prompt / Question", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G14", "Semantic", "Generate Direct Lake semantic model on <Target> Gold?", "[y/n]", "y builds Direct Lake model definition <Target>_Gold_Model -> G14b. n exits cleanly."],
        ["G14b","Semantic", "Approve semantic model?", "[APPROVE/DECLINE]", "APPROVE deploys <Target>_Gold_Model TMDL definition to Fabric. DECLINE triggers issues loop."],
        ["G14c","Semantic", "Refresh semantic model dataset now?", "[y/n]", "y triggers Direct Lake dataset refresh & DAX verification queries, appends status to dbo.project_status. Success -> G15; Failure -> Recovery prompt; n -> Exit thank-you message."]
    ]
    build_table(doc, headers, gates_data, [Inches(0.6), Inches(0.8), Inches(2.4), Inches(1.0), Inches(2.0)])

    add_heading_1(doc, "3. TMDL Definition Snippet & DAX Measures")
    code = (
        "// TMDL Definition for Marine_Gold_Model\n"
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
    add_code_block(doc, code)

    add_heading_1(doc, "4. Real-World Execution Walkthrough & Transcript")
    transcript = (
        "G14: Generate Direct Lake semantic model on Marine Gold? [y/n]\n"
        "USER: y\n"
        "AI: Building Direct Lake Semantic Model definition 'Marine_Gold_Model'...\n"
        "Model Definition Summary:\n"
        "- Mode: Direct Lake over Gold Delta tables\n"
        "- Tables Included: dim_policy, dim_vessel, fact_claim\n"
        "- Relationships: Active surrogate key joins (fact_claim[policy_sk] -> dim_policy[policy_sk])\n"
        "- Measures: Total_Claims, Total_Claim_Amount, Loss_Ratio\n\n"
        "G14b: Approve semantic model? [APPROVE/DECLINE]\n"
        "USER: APPROVE\n"
        "AI: The Direct Lake Semantic Model 'Marine_Gold_Model' is deployed to Fabric.\n\n"
        "G14c: Refresh semantic model dataset now? [y/n]\n"
        "USER: y\n"
        "AI: Triggering dataset refresh for Marine_Gold_Model...\n"
        "Refresh Status: Succeeded (Duration: 8s)\n"
        "Running DAX verification queries...\n"
        "Verification Outcome:\n"
        "- DAX Query 1 (Total Claims): PASSED (4,310 claims matched)\n"
        "- DAX Query 2 (Loss Ratio Calculation): PASSED\n"
        "Status appended to dbo.project_status: (run_001, semantic_model, COMPLETED, 2026-10-06 09:33:00)\n\n"
        "Semantic model refreshed and verified. Proceeding to Session Close (Gate G15)."
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "06_Semantic_Model_Layer_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 7: 07_Medallion_Skill_Explanation.docx
# ---------------------------------------------------------
def generate_doc_7():
    doc = Document()
    add_header(doc, "07. Medallion Skill Engine & Full Architecture", "Zero-Config Medallion Architecture — Master Single-Gate Engine Reference")

    add_heading_1(doc, "1. Core Engine Design")
    doc.add_paragraph(
        "The Medallion Skill Engine is a single-gate conversational program that orchestrates the entire medallion lifecycle on Microsoft Fabric. "
        "It eliminates static LOB directories, filesystem log files (Files/_logs/), and rigid cell indices. Target lakehouses are dynamically named at Gate G2."
    )

    add_heading_1(doc, "2. Master Gate Sequence (G0 – G15)")
    headers = ["Stage", "Gate", "Prompt / Action", "Key Rules & Behavior"]
    gates_data = [
        ["Setup", "G0 - G2b", "Handshake, Workspace, Source LH, Dynamic Target Folder Name & Creation, File listing", "G2 accepts derived target folder name or custom write-in. Creates target folder <target_folder_name> (<target_folder_name>_LH, notebooks, orchestrator, semantic model). Target LH creation deferred."],
        ["Profile", "G4 - G5", "Read-only profiling & approval", "Profiles types, nulls, candidate keys, date formats, encodings live. Holds attributes in memory."],
        ["Bronze", "G6 - G7a", "Bronze_<Target> notebook generation, DE approval, run prompt", "Table names match raw source stems. Initial overwrite / snapshot watermark. Appends to dbo.project_status."],
        ["Silver", "G8 - G10a", "Rules upload/skip, Silver_<Target> notebook generation, DE approval, run prompt", "UPLOAD parses rules; SKIP exits with thank-you. Table names match raw stems. Appends to dbo.project_status."],
        ["Gold", "G11 - G12c", "Client STTM upload/skip, Gold_<Target> notebook generation, DE approval, run prompt", "UPLOAD parses client STTM for Gold table names & measures; SKIP exits with thank-you. Appends to dbo.project_status."],
        ["Orchestrator", "G13 - G13c", "Orchestrator creation (Stage 4), picks, deployment, run prompt", "Deploys <Target>_Medallion_Orchestrator before Semantic Model. Appends to dbo.project_status."],
        ["Semantic", "G14 - G14c", "Direct Lake model creation (Stage 5), DE approval, refresh prompt", "Deploys <Target>_Gold_Model TMDL & executes dataset refresh. Appends to dbo.project_status."],
        ["Close", "G15", "Summary report & Process another dataset?", "Displays Medallion summary matrix. y loops to G2; n stops cleanly."]
    ]
    build_table(doc, headers, gates_data, [Inches(1.0), Inches(1.0), Inches(2.6), Inches(2.4)])

    add_heading_1(doc, "3. Complete End-to-End Master Execution Transcript")
    transcript = (
        "[Complete Marine Master Execution Sequence]\n"
        "G0-G2b: Connected to DataSonic 3 -> Source: Raw_Insurance_LH -> Action 1 (Start new project) -> Folder: Marine -> Dynamic Target Resolved: Marine -> Created Target: Marine_LH -> File details displayed.\n"
        "G4-G5: Data Profiling satisfied -> Profiling attributes stored in execution memory.\n"
        "G6-G7a: Deployed & Executed Bronze_Marine -> Status COMPLETED -> Loaded bronze.marine_policy (15,420 rows), bronze.marine_claim (4,310 rows).\n"
        "G8-G10a: Uploaded marine_business_rules.json -> Deployed & Executed Silver_Marine -> Status COMPLETED -> Loaded silver.marine_policy (15,420 rows), silver.marine_claim (4,310 rows).\n"
        "G11-G12c: Uploaded marine_sttm.xlsx -> Deployed & Executed Gold_Marine -> Status COMPLETED -> Loaded gold.dim_policy (14,801 rows), gold.dim_vessel (8,921 rows), gold.fact_claim (4,310 rows).\n"
        "G13-G13c: Deployed & Executed Marine_Medallion_Orchestrator -> Status COMPLETED.\n"
        "G14-G14c: Deployed & Refreshed Marine_Gold_Model -> Status COMPLETED.\n\n"
        "dbo.project_status History Table:\n"
        "+----------+---------------+-----------+---------------------+---------------+\n"
        "| run_id   | stage         | status    | updated_at          | error_message |\n"
        "+----------+---------------+-----------+---------------------+---------------+\n"
        "| run_001  | bronze        | COMPLETED | 2026-10-06 09:15:00 | null          |\n"
        "| run_001  | silver        | COMPLETED | 2026-10-06 09:17:00 | null          |\n"
        "| run_001  | gold          | COMPLETED | 2026-10-06 09:30:00 | null          |\n"
        "| run_001  | orchestrator  | COMPLETED | 2026-10-06 09:32:00 | null          |\n"
        "| run_001  | semantic_model| COMPLETED | 2026-10-06 09:33:00 | null          |\n"
        "+----------+---------------+-----------+---------------------+---------------+\n\n"
        "Process another dataset? [y/n]\n"
        "USER: n\n"
        "AI: Session closed for Marine. Thank you!"
    )
    add_callout(doc, transcript)

    target_path = os.path.join(OUTPUT_DIR, "07_Medallion_Skill_Explanation.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

# ---------------------------------------------------------
# DOCUMENT 8: MCP_Claude_Setup_And_Usage_Guide.docx (Un-numbered Master Guide)
# ---------------------------------------------------------
def generate_doc_8():
    doc = Document()
    add_header(doc, "Zero-Config Medallion Architecture on Microsoft Fabric", "End-to-End Master Setup, Environment Onboarding & Usage Guide")

    add_heading_1(doc, "1. Executive Summary & Core Design Principles")
    doc.add_paragraph("This master guide provides end-to-end setup, environment configuration, system onboarding, gate dictionary, and execution instructions for running the Zero-Config Medallion Architecture on Microsoft Fabric.")

    add_callout(doc, "Zero-Config Principles: Dynamic Target Resolution at Gate G2 (y to accept derived target name or write in custom dataset target name), zero static config files (lob/ or datasets/), zero Files/_logs/ dumps (dbo.project_status 5-column table), un-prefixed notebooks (Bronze_<Target>, Silver_<Target>, Gold_<Target>, Refresh_Semantic_Model), source-matching raw file stem Delta tables, client STTM Gold tables, Stage 4 Orchestrator Pipeline preceding Stage 5 Direct Lake Semantic Model, [y/n] post-deployment execution prompts, and UPLOAD/SKIP thank-you exit policies.")

    add_heading_1(doc, "2. System Setup & Prerequisites (New System Setup)")
    doc.add_paragraph("Follow these 4 sequential steps to set up the environment on a new machine or system:")

    p1 = doc.add_paragraph(style='List Bullet')
    r1 = p1.add_run("Step 1: Copy the mcp-claude Workspace Folder\n")
    r1.bold = True
    p1.add_run("Copy or transfer the entire mcp-claude directory onto the new machine. This repository contains the architecture definitions, documentation suite, and workspace configuration.")

    p2 = doc.add_paragraph(style='List Bullet')
    r2 = p2.add_run("Step 2: Clone / Set Up Fabric Skills Repository\n")
    r2.bold = True
    p2.add_run("Clone or place the fabric skills repository into .claude/skills/medallion/ within the mcp-claude workspace folder. Ensure SKILL.md, interface.md, client_config.md, and notebook_standards.md are present.")

    p3 = doc.add_paragraph(style='List Bullet')
    r3 = p3.add_run("Step 3: Configure IDE & AI Assistant (Antigravity / VS Code)\n")
    r3.bold = True
    p3.add_run("Launch Google Antigravity IDE or VS Code with an AI Assistant plugin (Gemini Code Assist, Claude, or Antigravity extension). Open the mcp-claude workspace folder as the root directory.")

    p4 = doc.add_paragraph(style='List Bullet')
    r4 = p4.add_run("Step 4: Authenticate Fabric Access via Azure CLI\n")
    r4.bold = True
    p4.add_run("Open an embedded terminal in Antigravity or VS Code and execute 'az login' to authenticate with your Azure / Microsoft Fabric tenant. Verify active subscription and workspace permissions.")

    add_heading_1(doc, "3. Master Gate Dictionary (G0 – G15)")
    headers = ["Gate", "Stage", "User Question / Prompt", "Options", "Execution Behavior & Outcome"]
    gates_data = [
        ["G0", "Start", "Welcome to AI Native Data Engineering", "N/A", "Checks Azure CLI connection. Active -> G0b; Inactive -> G0a."],
        ["G0a", "Start", "Fabric workspace connection is not active. Authenticate via Azure CLI?", "[y/n]", "y runs az login -> G0b; n prints thank-you message and stops."],
        ["G0b", "Setup", "Select Workspace: press 1 for <W1>, 2 for <W2> or S to stop", "[1/2/.../S]", "Sets {workspace} context. S prints thank-you message."],
        ["G1a", "Setup", "Select Action: 1 Start new project, 2 Resume, 3 Stop", "[1/2/3]", "1 asks G1 to select Source Lakehouse; 2 reads dbo.project_status to resume at G-pending; 3 stops."],
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

    add_heading_1(doc, "4. End-to-End Execution Walkthrough & Output Examples")
    doc.add_paragraph("The complete sequential Marine execution transcript and output examples are provided below:")

    transcript_text = (
        "USER: START\n"
        "AI: Welcome to AI Native Data Engineering\n"
        "G0-G2b: Connected -> Selected DataSonic 3 -> Source: Raw_Insurance_LH -> Action 1 (Start new project) -> Folder: Marine -> Dynamic Target Resolved: Marine -> Created Target: Marine_LH.\n"
        "G4-G5: Live Data Profiling completed -> Attributes saved in execution memory.\n"
        "G6-G7a: Deployed & Executed Bronze_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G8-G10a: Uploaded marine_business_rules.json -> Deployed & Executed Silver_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G11-G12c: Uploaded marine_sttm.xlsx -> Deployed & Executed Gold_Marine -> Status COMPLETED in dbo.project_status.\n"
        "G13-G13c: Deployed & Executed Marine_Medallion_Orchestrator -> Status COMPLETED in dbo.project_status.\n"
        "G14-G14c: Deployed & Refreshed Marine_Gold_Model -> Status COMPLETED in dbo.project_status.\n"
        "G15: Session closed for Marine. Thank you!"
    )
    add_callout(doc, transcript_text)

    target_path = os.path.join(OUTPUT_DIR, "MCP_Claude_Setup_And_Usage_Guide.docx")
    doc.save(target_path)
    print(f"Generated {target_path}")

if __name__ == "__main__":
    print("Generating dbo.project_status Word documentation suite...")
    generate_doc_1()
    generate_doc_2()
    generate_doc_3()
    generate_doc_4()
    generate_doc_5()
    generate_doc_6()
    generate_doc_7()
    generate_doc_8()
    print("All 8 Word documentation files successfully generated!")
