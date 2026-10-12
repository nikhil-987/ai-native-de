import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_document():
    doc = Document()

    # Brand Colors
    NAVY = RGBColor(21, 35, 55)        # #152337 Deep Brand Navy
    CYAN = RGBColor(0, 163, 224)       # #00A3E0 Brand Cyan / Accent
    DARK_TEXT = RGBColor(30, 41, 59)   # #1E293B Text Slate 800
    MUTED = RGBColor(100, 116, 139)    # #64748B Slate 500
    LIGHT_BG = "F8FAFC"                # #F8FAFC Table alternating row
    NAVY_HEX = "152337"
    BORDER_HEX = "CBD5E1"
    CALLOUT_BG = "F1F5F9"
    CODE_BG = "F8F9FA"

    # Set 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.text = "AI Data Engineering Studio · End-to-End Portable Setup Guide"
        hp.runs[0].font.name = "Calibri"
        hp.runs[0].font.size = Pt(8.5)
        hp.runs[0].font.color.rgb = MUTED
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.text = "ADROSONIC · Driven by Core, Delivered by Innovation  |  Confidential"
        fp.runs[0].font.name = "Calibri"
        fp.runs[0].font.size = Pt(8.5)
        fp.runs[0].font.color.rgb = MUTED

    def set_cell_background(cell, color_hex):
        tcPr = cell._element.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        tcPr.append(shd)

    def set_table_borders(table, border_color=BORDER_HEX):
        tblPr = table._element.xpath('w:tblPr')
        if tblPr:
            borders = parse_xml(
                f'<w:tblBorders {nsdecls("w")}>'
                f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
                f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
                f'<w:left w:val="none"/>'
                f'<w:right w:val="none"/>'
                f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
                f'<w:insideV w:val="none"/>'
                f'</w:tblBorders>'
            )
            tblPr[0].append(borders)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(17)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = CYAN
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_p(text, bold_prefix=None, space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(10.5)
            r_pre.font.bold = True
            r_pre.font.color.rgb = DARK_TEXT
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = DARK_TEXT
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.font.name = "Calibri"
            r_pre.font.size = Pt(10.5)
            r_pre.font.bold = True
            r_pre.font.color.rgb = DARK_TEXT
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = DARK_TEXT
        return p

    def add_callout(title, message, border_color="00A3E0"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, CALLOUT_BG)
        cell.width = Inches(6.5)

        tcPr = cell._element.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:top w:val="none"/>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
            f'<w:bottom w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(2)
        r_title = cp.add_run(f"📌 {title}\n")
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(11)
        r_title.font.bold = True
        r_title.font.color.rgb = NAVY

        r_msg = cp.add_run(message)
        r_msg.font.name = "Calibri"
        r_msg.font.size = Pt(10)
        r_msg.font.color.rgb = DARK_TEXT
        
        empty_p = doc.add_paragraph()
        empty_p.paragraph_format.space_after = Pt(6)

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, CODE_BG)
        cell.width = Inches(6.5)

        tcPr = cell._element.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:left w:val="single" w:sz="14" w:space="0" w:color="00A3E0"/>'
            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'<w:right w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(6)
        cp.paragraph_format.space_after = Pt(6)
        cp.paragraph_format.line_spacing = 1.05
        
        lines = code_text.strip().split("\n")
        for i, line in enumerate(lines):
            r = cp.add_run(line + ("\n" if i < len(lines) - 1 else ""))
            r.font.name = "Consolas"
            r.font.size = Pt(9.0)
            r.font.color.rgb = RGBColor(15, 23, 42)

        empty_p = doc.add_paragraph()
        empty_p.paragraph_format.space_after = Pt(6)

    # ----------------------------------------------------
    # COVER / HEADER SECTION
    # ----------------------------------------------------
    # Logo insertion if available
    logo_path = os.path.join("frontend", "public", "adrosonic-mark.png")
    if os.path.exists(logo_path):
        top_tbl = doc.add_table(rows=1, cols=2)
        top_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c_logo = top_tbl.cell(0, 0)
        c_title = top_tbl.cell(0, 1)
        c_logo.width = Inches(1.2)
        c_title.width = Inches(5.3)

        p_logo = c_logo.paragraphs[0]
        p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_logo.add_run().add_picture(logo_path, width=Inches(1.0))

        p_hdr = c_title.paragraphs[0]
        p_hdr.paragraph_format.space_before = Pt(4)
        r_t1 = p_hdr.add_run("ADROSONIC\n")
        r_t1.font.name = "Calibri"
        r_t1.font.size = Pt(12)
        r_t1.font.bold = True
        r_t1.font.color.rgb = CYAN

        r_t2 = p_hdr.add_run("AI Data Engineering Studio\n")
        r_t2.font.name = "Calibri"
        r_t2.font.size = Pt(22)
        r_t2.font.bold = True
        r_t2.font.color.rgb = NAVY

        r_t3 = p_hdr.add_run("End-to-End Portable Setup, Deployment & Architecture Guide")
        r_t3.font.name = "Calibri"
        r_t3.font.size = Pt(13)
        r_t3.font.color.rgb = MUTED
    else:
        title_p = doc.add_paragraph()
        title_p.paragraph_format.space_before = Pt(18)
        title_p.paragraph_format.space_after = Pt(2)
        r_main_title = title_p.add_run("AI Data Engineering Studio")
        r_main_title.font.name = "Calibri"
        r_main_title.font.size = Pt(24)
        r_main_title.font.bold = True
        r_main_title.font.color.rgb = NAVY

        sub_p = doc.add_paragraph()
        sub_p.paragraph_format.space_after = Pt(8)
        r_subtitle = sub_p.add_run("End-to-End Portable Setup, Deployment & Architecture Guide")
        r_subtitle.font.name = "Calibri"
        r_subtitle.font.size = Pt(14)
        r_subtitle.font.color.rgb = CYAN

    # Metadata Summary Box
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    
    metadata = [
        ("Target Environments", "Local Workstations (Windows, macOS), On-Premises VMs, Azure Linux VMs (Ubuntu 22.04/24.04), Docker Containers"),
        ("Architecture Pattern", "3-Tier Sibling Workspace (Studio App + Medallion Skills + Fabric MCP Server)"),
        ("Identity Model", "Zero Client Secrets · Interactive Azure CLI OAuth & Fabric Bearer Token Delegation"),
        ("Document Version", "1.0.0 (Production Ready Release)")
    ]

    for idx, (label, val) in enumerate(metadata):
        c0 = meta_tbl.cell(idx, 0)
        c1 = meta_tbl.cell(idx, 1)
        c0.width = Inches(2.0)
        c1.width = Inches(4.5)
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_before = Pt(2)
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(label)
        r0.font.name = "Calibri"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = NAVY

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_before = Pt(2)
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(val)
        r1.font.name = "Calibri"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = DARK_TEXT

    set_table_borders(meta_tbl)

    div_p = doc.add_paragraph()
    div_p.paragraph_format.space_before = Pt(10)
    div_p.paragraph_format.space_after = Pt(14)
    r_div = div_p.add_run("—" * 60)
    r_div.font.color.rgb = MUTED

    # ----------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY
    # ----------------------------------------------------
    add_h1("1. Executive Summary & Architecture Overview")
    add_p(
        "The AI Data Engineering Studio is an agentic, enterprise-grade engineering workspace designed to automate "
        "and govern the complete lifecycle of Microsoft Fabric Medallion Architecture implementations. By integrating "
        "a reactive React 18 single-page application, an asynchronous FastAPI backend server, the Anthropic Claude Code "
        "CLI execution runtime, and the official Microsoft Fabric Model Context Protocol (MCP) Server, the Studio empowers "
        "data teams to design, validate, provision, and transform OneLake delta assets through conversational and structured visual interfaces."
    )
    add_p(
        "A foundational design objective of the platform is zero-friction portability. The entire software stack can be "
        "replicated onto any developer workstation, remote client VM, or cloud server without hardcoding absolute paths, "
        "without requesting tenant-level Service Principal secrets, and without modifying a single line of application source code."
    )

    add_callout(
        "Core Value: Zero Enterprise Secrets Friction",
        "The Studio operates entirely on interactive Azure CLI OAuth tokens ('az login'). Any data engineer with existing "
        "contributor permissions to a Fabric Workspace in the Power BI / Fabric web portal can immediately execute projects "
        "without requesting Azure App Registrations, Client Secrets, or tenant admin approvals."
    )

    # ----------------------------------------------------
    # SECTION 2: THE 6 CORE PORTABLE ASSETS
    # ----------------------------------------------------
    add_h1("2. The 6 Core Portable Assets & Prerequisites")
    add_p("To stand up the Studio on any new target environment, the user requires only six core assets:")

    assets_table = doc.add_table(rows=7, cols=3)
    assets_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    assets_table.autofit = False
    set_table_borders(assets_table)

    headers = ["#", "Asset Name", "Description & Portability Mechanism"]
    col_widths = [Inches(0.5), Inches(2.0), Inches(4.0)]

    for c_idx, h_text in enumerate(headers):
        cell = assets_table.cell(0, c_idx)
        cell.width = col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    asset_data = [
        ("1", "mcp-claude Repository", "Contains the Medallion Skills (.claude/skills/medallion/) and agent prompt (fabric.agent.md). Auto-discovered as a sibling directory or configured via MCP_CLAUDE_DIR."),
        ("2", "fabric-mcp-server Repository", "Official Microsoft Fabric MCP Server tools (onelake_*, datafactory_*). Cloned as a sibling directory or auto-resolved via npx -y @microsoft/fabric-mcp."),
        ("3", "claude-bridge Repository", "The Web Studio application codebase, containing the React 18/Tailwind CSS frontend and FastAPI/Uvicorn backend."),
        ("4", "Microsoft Fabric Account", "Valid access to at least one Fabric Workspace with Contributor rights. Automatically validated via Azure CLI token calls."),
        ("5", "Azure CLI (az)", "Official Microsoft Azure CLI (2.50+). Handles OAuth login (az login or az login --use-device-code) with zero client secrets needed."),
        ("6", "Claude Account / CLI", "Anthropic Claude Code CLI (claude). Authenticated via claude login or an ANTHROPIC_API_KEY environment variable.")
    ]

    for row_idx, data in enumerate(asset_data, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = assets_table.cell(row_idx, c_idx)
            cell.width = col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.bold = True

    p_after_t1 = doc.add_paragraph()
    p_after_t1.paragraph_format.space_after = Pt(8)

    # ----------------------------------------------------
    # SECTION 3: DIRECTORY STRUCTURE
    # ----------------------------------------------------
    add_h1("3. Standard Directory Structure: 'AI Data Engineering Studio'")
    add_p(
        "To ensure automatic cross-repository discovery without hardcoded paths, all three repositories sit "
        "side-by-side as siblings inside a top-level parent directory named 'AI Data Engineering Studio':"
    )

    add_code_block(
        "AI Data Engineering Studio/\n"
        "├── claude-bridge/              # 1. This Web Studio app (frontend + backend)\n"
        "│   ├── backend/\n"
        "│   │   ├── server.py           # FastAPI backend server & static SPA host\n"
        "│   │   ├── fabric.py           # OneLake / Fabric REST token client\n"
        "│   │   ├── mock_data.py        # Demo mode simulation streams\n"
        "│   │   └── requirements.txt    # Python backend package dependencies\n"
        "│   ├── frontend/\n"
        "│   │   ├── src/                # React components & Medallion UX\n"
        "│   │   ├── public/             # Brand logos (adrosonic-sidebar.png, etc.)\n"
        "│   │   ├── package.json        # Frontend Node.js dependencies\n"
        "│   │   └── vite.config.js      # Vite build & API proxy config\n"
        "│   ├── setup.ps1 / setup.sh    # Automated cross-platform setup scripts\n"
        "│   └── start.ps1 / start.sh    # One-command startup scripts\n"
        "│\n"
        "├── mcp-claude/                 # 2. Medallion skills repository\n"
        "│   ├── .claude/\n"
        "│   │   ├── agents/fabric.agent.md\n"
        "│   │   └── skills/medallion/\n"
        "│   └── .env.example\n"
        "│\n"
        "└── fabric-mcp-server/          # 3. Microsoft Fabric MCP server (cloned here)\n"
        "    ├── src/                    # OneLake & Data Factory tool definitions\n"
        "    └── package.json"
    )

    add_h2("Initial Clone Sequence (One-Time Setup)")
    add_p("Execute the following commands in your destination directory:")
    add_code_block(
        "# Create the parent directory\n"
        "mkdir \"AI Data Engineering Studio\" && cd \"AI Data Engineering Studio\"\n\n"
        "# 1. Clone this Studio web app\n"
        "git clone <claude-bridge-repo-url> claude-bridge\n\n"
        "# 2. Clone the medallion skills repository\n"
        "git clone <mcp-claude-repo-url> mcp-claude\n\n"
        "# 3. Clone the official Microsoft Fabric MCP Server repository\n"
        "git clone https://github.com/microsoft/fabric-mcp-server.git fabric-mcp-server"
    )

    # ----------------------------------------------------
    # SECTION 4: PACKAGE SETUP DETAILS
    # ----------------------------------------------------
    add_h1("4. Package Setup Details: Backend & Frontend")

    add_h2("4.1 Backend Python Packages Breakdown")
    add_p(
        "The backend runtime requires Python 3.10+ and FastAPI. It orchestrates API requests, SSE chat streams, "
        "Azure token renewal, OneLake Delta table parsing, and subprocess management."
    )

    py_pkg_table = doc.add_table(rows=8, cols=3)
    py_pkg_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    py_pkg_table.autofit = False
    set_table_borders(py_pkg_table)

    py_headers = ["Package Name", "Version", "Role & Functional Responsibility in Studio"]
    py_col_widths = [Inches(1.8), Inches(1.1), Inches(3.6)]

    for c_idx, h_text in enumerate(py_headers):
        cell = py_pkg_table.cell(0, c_idx)
        cell.width = py_col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    py_data = [
        ("fastapi", ">=0.110.0", "Asynchronous web framework providing high-throughput REST endpoints, Server-Sent Events (SSE) streaming for Claude Code execution, and CORS handling."),
        ("uvicorn[standard]", ">=0.29.0", "Asynchronous ASGI web server powering FastAPI and serving compiled production frontend assets directly at port 8000."),
        ("python-dotenv", ">=1.0.0", "Loads environment variables automatically from the project root .env file without polluting the global operating system registry."),
        ("python-multipart", ">=0.0.9", "Parses multipart/form-data payloads when uploading STTM mapping workbooks (.xlsx) and business rules spreadsheets."),
        ("pydantic", ">=2.6.0", "Guarantees strict request/response data validation and gate transition state models across the studio."),
        ("deltalake", ">=0.18.0", "Enables direct, zero-Spark local reading and schema inspection of OneLake Delta tables (e.g. dbo.project_status) via native Rust bindings."),
        ("pyarrow", ">=14.0.0", "Columnar memory format backing deltalake, providing instant conversion of Parquet files to Python dicts without launching Spark clusters.")
    ]

    for row_idx, data in enumerate(py_data, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = py_pkg_table.cell(row_idx, c_idx)
            cell.width = py_col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.name = "Consolas"
                r.font.bold = True

    p_after_t2 = doc.add_paragraph()
    p_after_t2.paragraph_format.space_after = Pt(6)

    add_h3("Backend Virtual Environment & Installation Commands")
    add_p("Windows PowerShell:", bold_prefix="• ")
    add_code_block(
        "cd \"AI Data Engineering Studio\\claude-bridge\"\n"
        "python -m venv .venv\n"
        ".\\.venv\\Scripts\\activate\n"
        "python -m pip install --upgrade pip\n"
        "pip install -r backend/requirements.txt"
    )

    add_p("Linux / macOS / Cloud VM:", bold_prefix="• ")
    add_code_block(
        "cd \"AI Data Engineering Studio/claude-bridge\"\n"
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "python3 -m pip install --upgrade pip\n"
        "pip install -r backend/requirements.txt"
    )

    add_h2("4.2 Frontend Node.js Ecosystem & Package Breakdown")
    add_p(
        "The frontend is a single-page application built with React 18, Vite 5, and Tailwind CSS v4. "
        "It provides the interactive stage-by-stage gates and real-time streaming feedback."
    )

    node_pkg_table = doc.add_table(rows=6, cols=3)
    node_pkg_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    node_pkg_table.autofit = False
    set_table_borders(node_pkg_table)

    node_headers = ["Package Name", "Version", "Role & Functional Responsibility in UI"]
    node_col_widths = [Inches(1.8), Inches(1.1), Inches(3.6)]

    for c_idx, h_text in enumerate(node_headers):
        cell = node_pkg_table.cell(0, c_idx)
        cell.width = node_col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    node_data = [
        ("react & react-dom", "^18.3.1", "Declarative UI framework managing wizard gate progression, session runs, and terminal output state."),
        ("vite", "^5.4.0", "Frontend build tool providing instant Hot Module Reloading (HMR) and optimized single-bundle production compilation."),
        ("@tailwindcss/vite & tailwindcss", "^4.3.3", "Modern Tailwind CSS v4 styling with Adrosonic brand tokens (Deep Navy #152337, Cyan #00CCFF, and clean dark layout)."),
        ("react-icons", "^5.7.0", "Iconography library for Fabric lakehouse items, Medallion layer badges (Bronze, Silver, Gold), and job status indicators."),
        ("marked & dompurify", "^12.0.2 / ^3.1.6", "Parses streaming Markdown text from Claude Code and sanitizes generated HTML to prevent XSS vulnerabilities.")
    ]

    for row_idx, data in enumerate(node_data, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = node_pkg_table.cell(row_idx, c_idx)
            cell.width = node_col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.name = "Consolas"
                r.font.bold = True

    p_after_t3 = doc.add_paragraph()
    p_after_t3.paragraph_format.space_after = Pt(6)

    add_h3("Frontend Installation & Compilation Commands")
    add_code_block(
        "cd \"AI Data Engineering Studio/claude-bridge/frontend\"\n\n"
        "# 1. Install all Node.js dependencies\n"
        "npm install\n\n"
        "# 2. Build production assets into frontend/dist (Served directly by FastAPI at port 8000)\n"
        "npm run build\n\n"
        "# 3. (Optional) Start local Vite dev server with Hot Module Reloading\n"
        "npm run dev"
    )

    # ----------------------------------------------------
    # SECTION 5: STEP-BY-STEP DEPLOYMENT RUNBOOKS
    # ----------------------------------------------------
    add_h1("5. Step-by-Step Deployment Runbooks")

    add_h2("5.1 Option A: Windows Workstation or Windows Server VM")
    add_bullet("Download and install Python 3.10+ from python.org. Crucial: Check 'Add python.exe to PATH' during installation.", "1. Prerequisites (Python): ")
    add_bullet("Download and install Node.js 18+ LTS from nodejs.org.", "2. Prerequisites (Node.js): ")
    add_bullet("Install Azure CLI via MSI installer or 'winget install Microsoft.AzureCLI'.", "3. Prerequisites (Azure CLI): ")
    add_bullet("Authenticate your Microsoft account: run 'az login' in PowerShell.", "4. Authentication: ")
    add_bullet("Execute automated setup: Navigate to 'claude-bridge' and run '.\\setup.ps1'.", "5. Automated Setup: ")
    add_bullet("Launch Studio: Run '.\\start.ps1'. Access http://localhost:8000 in your browser.", "6. Launch Studio: ")

    add_h2("5.2 Option B: Linux & Azure Cloud Virtual Machines (Ubuntu 22.04 / 24.04 LTS)")
    add_p("Deploying to an Azure Ubuntu VM or remote cloud instance:")
    add_code_block(
        "# 1. Update system packages & install base dependencies\n"
        "sudo apt update && sudo apt install -y python3 python3-pip python3-venv nodejs npm git curl\n\n"
        "# 2. Install official Microsoft Azure CLI\n"
        "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash\n\n"
        "# 3. Authenticate with Azure CLI (Device Code mode for headless remote SSH)\n"
        "az login --use-device-code\n\n"
        "# 4. (Optional) Install Claude Code CLI\n"
        "sudo npm install -g @anthropic-ai/claude-code\n"
        "claude login\n\n"
        "# 5. Run the automated setup script\n"
        "cd \"AI Data Engineering Studio/claude-bridge\"\n"
        "chmod +x setup.sh start.sh\n"
        "./setup.sh\n\n"
        "# 6. Launch the studio server\n"
        "./start.sh"
    )

    add_h2("5.3 Production Daemon: Systemd Service Configuration (Linux)")
    add_p("To run the Studio as an unattended, auto-restarting background service on Linux VMs, create a systemd unit file:")
    add_code_block(
        "# /etc/systemd/system/fabric-studio.service\n"
        "[Unit]\n"
        "Description=AI Data Engineering Studio Web Service\n"
        "After=network.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        "User=ubuntu\n"
        "WorkingDirectory=/home/ubuntu/AI Data Engineering Studio/claude-bridge\n"
        "ExecStart=/home/ubuntu/AI Data Engineering Studio/claude-bridge/.venv/bin/python server.py\n"
        "Restart=always\n"
        "RestartSec=5\n"
        "Environment=PORT=8000\n"
        "Environment=HOST=0.0.0.0\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target"
    )
    add_p("Enable and start the service with: 'sudo systemctl enable --now fabric-studio'.")

    add_h2("5.4 Option C: Docker & Containerized Deployment")
    add_p("If Docker is installed on the host machine, you can launch the complete Studio without installing Python or Node.js:")
    add_code_block(
        "cd \"AI Data Engineering Studio/claude-bridge\"\n"
        "docker compose up --build -d"
    )
    add_p("The container automatically mounts '~/.azure' to preserve your interactive login tokens and maps port 8000.")

    # ----------------------------------------------------
    # SECTION 6: AUTHENTICATION & IDENTITY ARCHITECTURE
    # ----------------------------------------------------
    add_h1("6. Authentication & Identity Architecture: Zero-Secret Model")
    add_p(
        "A major challenge in enterprise cloud automation is credential management. Traditional systems require Service "
        "Principals, Client Secrets, and Azure Active Directory App Registrations that frequently require weeks of security "
        "approvals. The AI Data Engineering Studio eliminates this bottleneck through an interactive OAuth token delegation pipeline."
    )

    add_h2("6.1 Azure CLI Authentication: Dual Sign-In Options (Inside & Outside the App)")
    add_callout(
        "Zero Enterprise Secrets: How Azure Token Delegation Works",
        "1. Interactive Token Delegation: The platform acquires short-lived Azure bearer tokens directly via your active az session ('az account get-access-token --resource https://api.fabric.microsoft.com').\n"
        "2. No Service Principals: Any engineer with existing Contributor rights to a Fabric Workspace can use the Studio immediately without tenant admin secret requests.\n"
        "3. Ephemeral Bearer Headers: Tokens are held only in temporary memory to query workspaces, validate lakehouse paths, and inspect OneLake tables.\n"
        "4. Fabric MCP Tool Execution: Claude Code runs with 'bypassPermissions', calling Fabric tools (onelake_*, datafactory_*) on behalf of the signed-in engineer."
    )

    add_h3("Option A: Outside the App (Terminal Startup Prompt)")
    add_p(
        "When starting the backend server from the command line ('python server.py', '.\\start.ps1', or './start.sh'), "
        "the runtime automatically verifies whether an active Azure session exists. If not signed in, an interactive prompt appears:"
    )
    add_code_block(
        ">>> AZURE CLI AUTHENTICATION SETUP <<<\n"
        "Azure CLI is not signed in yet. Would you like to authenticate now?\n"
        "  [1] Interactive browser login ('az login')\n"
        "  [2] Device code login ('az login --use-device-code')\n"
        "  [3] Skip for now (continue to Studio UI & sign in from the web page)\n"
        "Select an option [1/2/3, default: 3]:"
    )
    add_bullet("Option [1]: Opens the system browser locally on the host to complete standard interactive OAuth.", "Standard Browser OAuth: ")
    add_bullet("Option [2]: Displays the Microsoft device login URL and verification code for headless SSH or remote terminal sessions.", "Device Code Mode: ")
    add_bullet("Option [3]: Skips terminal authentication, booting the web server immediately so you can sign in anytime via the browser UI.", "Deferred Sign-In: ")

    add_h3("Option B: Inside the App (Web Studio UI · Automatic Browser Tab & Polling)")
    add_p(
        "Users can authenticate, re-authenticate, or switch Azure identities directly inside the web interface without touching the terminal:"
    )
    add_bullet("Navigate to 'Connections Settings' from the left sidebar and locate the 'Azure CLI' card.", "1. Open Connections: ")
    add_bullet("Click '[Sign in with Azure CLI]'. The Studio immediately launches the non-blocking device flow and opens the official Microsoft sign-in page ('https://login.microsoft.com/device') in a new browser tab.", "2. Automated Tab Launch: ")
    add_bullet("The verification code (e.g. 'HSYGGFHLA') is displayed prominently on screen and copied to your clipboard automatically. A fallback '[Open Login Tab]' button and '[Copy Code]' button are available if popups are restricted.", "3. On-Screen Code & Copy: ")
    add_bullet("The Studio polls in the background every 2 seconds. The moment sign-in is approved on Microsoft's page, the card updates to 'Connected & Authorized' with your account email.", "4. Auto-Completion Detection: ")
    add_bullet("A '[Sign out]' button is provided to revoke active tokens and disconnect on demand.", "5. Sign Out: ")

    add_h2("6.2 Claude Authentication: Dual Sign-In Options (Inside & Outside the App)")
    add_p(
        "To maximize flexibility across local workstations, remote jump boxes, and headless cloud VMs, the Studio "
        "implements two distinct, complementary mechanisms to authenticate Claude Code:"
    )

    add_h3("Option A: Outside the App (Terminal Startup Pre-Flight Check)")
    add_p(
        "When starting the backend server from the command line ('python server.py', '.\\start.ps1', or './start.sh'), "
        "the runtime automatically checks whether Claude is authenticated (via OAuth tokens or an active API key). "
        "If not authenticated, it presents an interactive choice directly in your terminal session:"
    )
    add_code_block(
        ">>> CLAUDE AUTHENTICATION SETUP <<<\n"
        "Claude is not signed in yet. Would you like to authenticate now?\n"
        "  [1] Sign in with Claude CLI browser login ('claude login')\n"
        "  [2] Enter Anthropic API Key (sk-ant-...)\n"
        "  [3] Skip for now (continue to Studio UI & sign in from the web page)\n"
        "Select an option [1/2/3, default: 3]:"
    )
    add_bullet("Option [1]: Launches the browser-based OAuth flow ('claude login') without leaving your terminal.", "Terminal OAuth: ")
    add_bullet("Option [2]: Prompts for an Anthropic API Key ('sk-ant-...'), securely appends it to '.env', and immediately activates it.", "Terminal API Key: ")
    add_bullet("Option [3]: Skips terminal authentication, booting the web server immediately so you can sign in anytime via the browser UI.", "Deferred Sign-In: ")

    add_h3("Option B: Inside the App (Web Studio UI)")
    add_p(
        "Users can manage their Claude credentials directly inside the web application at any time without accessing the host terminal:"
    )
    add_bullet("Navigate to 'Connections Settings' from the left sidebar (or click the 'Sign in' link beside Claude Code).", "1. Open Connections: ")
    add_bullet("Dynamic Binary Discovery: The Studio automatically resolves the Claude CLI binary across your system PATH and global npm directories (%APPDATA%\\npm\\claude.cmd, %LOCALAPPDATA%, /usr/local/bin, etc.) without requiring server restarts.", "2. Dynamic Path Resolution: ")
    add_bullet("1-Click Automated Installation: If Claude CLI is not yet installed on the machine, click '[Install Claude CLI]' on the connection card. The backend automatically installs @anthropic-ai/claude-code via npm and refreshes status.", "3. 1-Click CLI Installation: ")
    add_bullet("Under the 'Claude Code' card, click '[Sign in with Claude CLI]' to trigger interactive authentication in your browser. The Studio automatically detects sign-in completion.", "4. Interactive CLI Sign-In: ")
    add_bullet("Alternatively, paste your Anthropic API Key ('sk-ant-...') into the direct key field and click '[Save Key]'. The backend saves it to '.env' and activates it in real time.", "5. Direct API Key Entry: ")
    add_bullet("The connection card displays 'Connected & Ready' with the authenticated user's full name (e.g. 'Nikhil Kumar Gupta'), masked key details ('sk-ant-...xxxx') or account email, and provides a 'Sign out' button to revoke credentials on demand.", "6. Live Status & User Identity: ")

    add_h2("6.3 Navigation Architecture: Default Home View on Page Reload")
    add_p(
        "To ensure a clean, predictable workflow when accessing the Studio or refreshing the browser, the application "
        "is configured to always land on the Home page by default on every page load and reload (F5 / browser refresh). "
        "From the Home page, users can review system connection health, initiate a New Medallion Flow, or switch to the "
        "Studio workspace at any time to resume existing sessions."
    )

    # ----------------------------------------------------
    # SECTION 7: CONFIGURATION REFERENCE (.ENV)
    # ----------------------------------------------------
    add_h1("7. Configuration Reference (.env)")
    add_p(
        "The application reads configuration parameters from an optional '.env' file located in the root of the "
        "'claude-bridge' directory. All settings feature sensible defaults that auto-resolve to sibling directories."
    )

    env_table = doc.add_table(rows=7, cols=4)
    env_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    env_table.autofit = False
    set_table_borders(env_table)

    env_headers = ["Variable Name", "Default Value", "Allowed Values", "Description"]
    env_col_widths = [Inches(1.8), Inches(1.3), Inches(1.2), Inches(2.2)]

    for c_idx, h_text in enumerate(env_headers):
        cell = env_table.cell(0, c_idx)
        cell.width = env_col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    env_data = [
        ("MCP_CLAUDE_DIR", "../mcp-claude", "Valid folder path", "Path to the Medallion Skills repository."),
        ("FABRIC_MCP_DIR", "../fabric-mcp-server", "Valid folder path", "Path to the cloned Microsoft Fabric MCP Server."),
        ("HOST", "0.0.0.0", "0.0.0.0 / 127.0.0.1", "Network interface binding. 0.0.0.0 allows remote VM access."),
        ("PORT", "8000", "1 - 65535", "HTTP listening port for the web server."),
        ("PERMISSION_MODE", "bypassPermissions", "bypassPermissions, default", "Auto-approves tool execution while waiting on gates."),
        ("DEMO_MODE", "false", "true / false", "Simulates Fabric responses for offline testing without Azure.")
    ]

    for row_idx, data in enumerate(env_data, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = env_table.cell(row_idx, c_idx)
            cell.width = env_col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.name = "Consolas"
                r.font.bold = True

    p_after_t4 = doc.add_paragraph()
    p_after_t4.paragraph_format.space_after = Pt(6)

    # ----------------------------------------------------
    # SECTION 8: CLOUD NETWORKING & SECURITY
    # ----------------------------------------------------
    add_h1("8. Cloud Networking, Firewalls & Port Rules")
    add_p(
        "When deploying the Studio on an Azure Virtual Machine, AWS EC2 instance, or GCP Compute Engine, "
        "the cloud provider's firewall must be configured to permit inbound traffic on port 8000."
    )

    add_h2("Azure Network Security Group (NSG) Configuration")
    add_bullet("In the Azure Portal, locate your Virtual Machine and open 'Networking'.", "1. Locate NSG: ")
    add_bullet("Click 'Add inbound port rule'.", "2. Add Rule: ")
    add_bullet("Set Source to 'Any' (or specify your corporate public IP for enhanced security).", "3. Source: ")
    add_bullet("Set Destination port ranges to '8000'. Set Protocol to 'TCP'.", "4. Port: ")
    add_bullet("Set Action to 'Allow', Priority to '300', and Name to 'Allow-FabricStudio-8000'.", "5. Action: ")
    add_bullet("Access the Studio in your browser at 'http://<VM_PUBLIC_IP>:8000'.", "6. Access: ")

    # ----------------------------------------------------
    # SECTION 9: OPERATIONAL VERIFICATION & HEALTH CHECKS
    # ----------------------------------------------------
    add_h1("9. Operational Verification & Health Testing")
    add_p(
        "Once the server is running, you can immediately verify operational health via the built-in diagnostic endpoint:"
    )
    add_code_block("curl http://localhost:8000/api/health")
    add_p("A healthy system returns an HTTP 200 payload similar to:")
    add_code_block(
        "{\n"
        "  \"project_dir\": \"C:\\\\Users\\\\...\\\\mcp-claude\",\n"
        "  \"skill_found\": true,\n"
        "  \"fabric_mcp_found\": true,\n"
        "  \"claude\": true,\n"
        "  \"az_installed\": true,\n"
        "  \"az_user\": \"engineer@domain.com\",\n"
        "  \"permission_mode\": \"bypassPermissions\",\n"
        "  \"demo_mode\": false\n"
        "}"
    )

    # ----------------------------------------------------
    # SECTION 10: TROUBLESHOOTING & FAQ MATRIX
    # ----------------------------------------------------
    add_h1("10. Comprehensive Troubleshooting & Diagnostic Matrix")

    trouble_table = doc.add_table(rows=8, cols=3)
    trouble_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    trouble_table.autofit = False
    set_table_borders(trouble_table)

    tr_headers = ["Observed Issue / Symptom", "Root Cause Analysis", "Resolution & Remediation Steps"]
    tr_col_widths = [Inches(1.8), Inches(2.0), Inches(2.7)]

    for c_idx, h_text in enumerate(tr_headers):
        cell = trouble_table.cell(0, c_idx)
        cell.width = tr_col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    trouble_data = [
        ("Azure CLI Not Signed In", "Active az session expired or az login was never executed on this user profile.", "Run 'az login' (or 'az login --use-device-code' on headless SSH terminals), or click Sign in directly in the UI."),
        ("Claude CLI Not Found in PATH", "npm global bin directory is not in environment PATH.", "Click '[Install Claude CLI]' in the UI or run 'npm i -g @anthropic-ai/claude-code'. Alternatively, enter Anthropic API Key directly."),
        ("Demo Mode Active", "Claude CLI or Medallion Skills folder was not discovered at the expected sibling path.", "Verify 'claude --version' returns output, and ensure mcp-claude sits directly beside claude-bridge."),
        ("Page Reload Landing", "User reloaded or refreshed browser window (F5).", "By design, refreshing the page always returns to the Home view. Click Studio or New Medallion Flow to proceed."),
        ("HTTP 503 / UI Not Built", "The frontend has not been compiled into production HTML/JS assets.", "Execute 'cd frontend && npm install && npm run build'. Verify frontend/dist/index.html exists."),
        ("Missing Python Modules", "FastAPI or deltalake dependencies were not installed into the active Python environment.", "Activate your virtual environment and run 'pip install -r backend/requirements.txt'."),
        ("Port 8000 Address Already in Use", "Another instance of server.py or another web server is bound to port 8000.", "Specify a different port via environment variable or flag: 'PORT=8080 ./start.sh' or '.\\start.ps1 -Port 8080'.")
    ]

    for row_idx, data in enumerate(trouble_data, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = trouble_table.cell(row_idx, c_idx)
            cell.width = tr_col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.bold = True

    # ----------------------------------------------------
    # SECTION 11: INTERACTIVE MOCKUPS MODE & END-TO-END TESTING
    # ----------------------------------------------------
    add_h1("11. Interactive Mockups Mode & End-to-End Simulation")
    add_p(
        "To enable developers, solution architects, and stakeholders to test and demonstrate the entire Medallion Architecture workflow without requiring active Microsoft Fabric workspace permissions or Claude CLI tokens, the Studio includes a high-fidelity Interactive Mockups Mode."
    )

    add_h2("11.1 Dual Execution Modes")
    add_bullet(
        "Mockups Mode (Default): Simulates the full step-by-step project progression from raw ingestion through Direct Lake Power BI semantic models with realistic PySpark Delta code, schemas, and live status transitions."
    )
    add_bullet(
        "Live Engine Mode: Executes real-time requests using the local Claude Code CLI and Fabric REST API / MCP server."
    )
    add_p(
        "Users can toggle between modes at any time using the header toggle button (🧪 Mockups Mode vs ⚡ Live Engine) or the interactive badge in the Studio banner."
    )

    add_h2("11.2 End-to-End 'Start a New Project' Test Flow")
    add_p(
        "When running in Mockups Mode, clicking 'Start a New Project' walks through all 18+ architectural gates with interactive clickable decision chips:"
    )

    mock_table = doc.add_table(rows=8, cols=3)
    mock_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    mock_table.autofit = False
    set_table_borders(mock_table)

    m_headers = ["Medallion Stage", "Gate ID & Prompt", "Simulated Output & User Action"]
    m_col_widths = [Inches(1.8), Inches(2.2), Inches(2.5)]

    for c_idx, h_text in enumerate(m_headers):
        cell = mock_table.cell(0, c_idx)
        cell.width = m_col_widths[c_idx]
        set_cell_background(cell, NAVY_HEX)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(h_text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    mock_steps = [
        ("Target Resolution", "Gates G2 & G2b", "Resolves destination Lakehouse and displays source raw file inventory. Click [y] to confirm."),
        ("Data Profiling", "Gates G4 & G5", "Executes Spark data profiling, infers column schemas, null counts, and cardinality. Click [APPROVE]."),
        ("Bronze Ingestion", "Gates G6, G7 & G7a", "Generates raw-to-bronze Delta notebook, creates Lakehouse table, runs job. Click [y] then [NEXT]."),
        ("Silver Cleansing", "Gates G8, G9 & G10", "Maps business rules document, dedupes records, validates data quality. Click [APPROVE] then [NEXT]."),
        ("Gold Modeling", "Gates G11, G12 & G12c", "Designs Star Schema dimensional models (Fact & Conformed Dimensions). Click [APPROVE] then [NEXT]."),
        ("Orchestrator Pipeline", "Gates G13 & G13c", "Constructs Data Factory orchestration pipeline with sequential activity triggers. Click [y] then [NEXT]."),
        ("Semantic Model", "Gates G14, G14b & G15", "Generates Direct Lake Power BI semantic model, DAX measures, and final 100% Medallion Dashboard.")
    ]

    for row_idx, data in enumerate(mock_steps, start=1):
        bg = LIGHT_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(data):
            cell = mock_table.cell(row_idx, c_idx)
            cell.width = m_col_widths[c_idx]
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = DARK_TEXT
            if c_idx == 0:
                r.font.bold = True

    # ----------------------------------------------------
    # SECTION 12: MODERN UI ARCHITECTURE, MONITORING & OBSERVABILITY HUB
    # ----------------------------------------------------
    add_h1("12. Modern UI Architecture, Monitoring & Observability Hub")
    add_p(
        "The AI Data Engineering Studio is architected with a decluttered, responsive, and developer-centric "
        "user experience designed to maximize productivity and eliminate visual clutter during intensive engineering tasks."
    )

    add_h2("12.1 Decluttered Floating Header Controls")
    add_p(
        "The legacy full-width top header banner has been completely eliminated in favor of an unobstructed view canvas. "
        "All primary actions are cleanly grouped as responsive floating pill controls in the top-right corner:"
    )
    add_bullet(
        "Active Run Stop Button: Displays dynamically during active agent runs with real-time execution duration.",
        "🛑 Stop Control: "
    )
    add_bullet(
        "Real-Time Notification Center: Displays real-time badge count for background notebook, pipeline, and model runs.",
        "🔔 Notifications: "
    )
    add_bullet(
        "Universal Conversation Drawer: One-click toggle for the Claude Execution Trace panel. Starts collapsed by default for zero distraction.",
        "💬 Conversation Drawer: "
    )
    add_bullet(
        "Simulation Mode Toggle: Seamless toggle between 🧪 Mockups Mode and ⚡ Live Engine.",
        "⚡ Mode Switcher: "
    )
    add_bullet(
        "Theme Preference: Instant transition between Dark Mode and Light Mode with persistent local storage.",
        "🌙/☀️ Theme Switcher: "
    )

    add_h2("12.2 Minimal Studio Header & In-Studio Project Switching")
    add_p(
        "To prevent layout wrapping and clutter when the conversation panel is open on the right, the large progress card "
        "has been replaced with a compact, single-line minimal header:"
    )
    add_bullet(
        "Workspace Badge: Displays the active Fabric workspace name (e.g. 📁 nikhil's_workspace).",
        "Workspace Indicator: "
    )
    add_bullet(
        "Interactive Project Switcher: An integrated dropdown selector displaying the current project name. Clicking the project name "
        "reveals all projects in the workspace along with their status, lakehouse location, and completion percentage, allowing users "
        "to switch between projects or start a new project instantly without navigating away from the Studio.",
        "Project Switcher: "
    )
    add_bullet(
        "Medallion Completion Indicator: A sleek horizontal progress bar and percentage readout (0% to 100%) providing clean visibility.",
        "Progress Indicator: "
    )

    add_h2("12.3 Tabular Monitoring Hub & Pagination")
    add_p(
        "The Monitoring section provides deep observability across all Microsoft Fabric executions (Notebooks, Data Pipelines, Semantic Models):"
    )
    add_bullet(
        "Tabular View: Dense, structured table displaying Project Name, Run ID (with copy button and direct Microsoft Fabric Monitor deep link), "
        "Item Type, Status Badge (Succeeded, In Progress, Failed, Cancelled), Trigger Time, and live actions.",
        "Observability Table: "
    )
    add_bullet(
        "Global Filters: Filter runs by status (All, Succeeded, In Progress, Failed) and item type (Notebooks, Data Pipelines).",
        "Status & Type Filters: "
    )
    add_bullet(
        "Keyword Search: Instant search across Run IDs, Project names, and Item names.",
        "Real-Time Search: "
    )
    add_bullet(
        "Client-Side Pagination: Clean 10-item-per-page pagination with responsive previous/next controls ensuring smooth performance.",
        "Pagination: "
    )

    add_h2("12.4 Notification System & Live Execution Toasts")
    add_bullet(
        "Execution Toasts: Pop-up toast notifications automatically appear at the bottom-right when Fabric jobs succeed or fail, "
        "featuring a 1-click shortcut button to view the run directly in the Monitoring section.",
        "Real-Time Toasts: "
    )
    add_bullet(
        "Notification Drawer: Accessible via the bell icon in the top-right header, maintaining an actionable history of completed and failed jobs.",
        "Notification History: "
    )

    # Save Document
    output_filename = "AI_Data_Engineering_Studio_Portable_Setup_Guide.docx"
    doc.save(output_filename)
    print(f"Document successfully created and saved to {output_filename}")

    # Also copy to artifacts directory
    artifact_dir = r"C:\Users\nikhi\.gemini\antigravity\brain\856e649e-da69-41b6-8478-dd263fe8a1bc"
    if os.path.exists(artifact_dir):
        import shutil
        dest = os.path.join(artifact_dir, output_filename)
        shutil.copy2(output_filename, dest)
        print(f"Document successfully copied to artifact directory: {dest}")

if __name__ == "__main__":
    create_document()

