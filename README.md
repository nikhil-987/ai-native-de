# AI Native Data Engineering Studio

An end-to-end AI Native Data Engineering platform and console for automating Microsoft Fabric Medallion architectures (Bronze → Silver → Gold → Orchestrator → Semantic Model).

## Repository Architecture

```text
ai-native-de/
├── claude-bridge/          # Full-stack Web Studio (FastAPI backend + React Vite frontend)
│   ├── backend/            # FastAPI orchestration, Fabric REST/MCP integration, Claude Code bridge
│   ├── frontend/           # Modern React interactive UI console
│   ├── setup.ps1 / .sh     # Automated environment setup scripts
│   └── start.ps1 / .sh     # Single-command local runtime starters
│
└── mcp-claude/             # Medallion core & agents configuration
    ├── .claude/            # Medallion skills, agent rules & instructions
    ├── docs/               # Architecture diagrams, gates, end-to-end flowcharts
    ├── scratch/            # Guide and documentation generators
    └── uploads/            # Schemas and sample data payloads
```

## Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- Azure CLI (`az`) logged in with access to your Microsoft Fabric workspace

### 2. Setup & Run
Navigate to `claude-bridge` and run the setup and start scripts:

**Windows (PowerShell):**
```powershell
cd claude-bridge
.\setup.ps1
.\start.ps1
```

**Linux / macOS:**
```bash
cd claude-bridge
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

The Web Studio interface will be accessible at `http://localhost:8000`.
