#!/usr/bin/env bash
# ==============================================================================
# AI Data Engineering Studio - Portable Setup Script (Linux / macOS / Cloud VM)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=================================================================="
echo "  ADROSONIC · AI Data Engineering Studio - Portable Setup (POSIX) "
echo "=================================================================="
echo ""

# 1. Check Python
echo "[1/6] Checking Python installation..."
if command -v python3 &>/dev/null; then
    PY_BIN="python3"
elif command -v python &>/dev/null; then
    PY_BIN="python"
else
    echo "  ✗ Python 3.10+ is required but not found in PATH."
    echo "    On Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi
echo "  ✓ Found: $($PY_BIN --version)"

# 2. Check Node.js
echo "[2/6] Checking Node.js installation..."
if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo "  ✗ Node.js 18+ is required but not found in PATH."
    echo "    Install Node.js: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
    exit 1
fi
echo "  ✓ Found Node: $(node --version), npm: $(npm --version)"

# 3. Check Azure CLI
echo "[3/6] Checking Azure CLI..."
if command -v az &>/dev/null; then
    echo "  ✓ Azure CLI is installed: $(az --version | head -n 1)"
    if az account show &>/dev/null; then
        USER_NAME=$(az account show --query user.name -o tsv 2>/dev/null || echo "Active")
        echo "  ✓ Logged in as: $USER_NAME"
    else
        echo "  ! Azure CLI is installed but not logged in. Run: az login (or az login --use-device-code for headless VM)"
    fi
else
    echo "  ! Azure CLI ('az') not found in PATH."
    echo "    Install Azure CLI: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo "    (App will run in Demo/Mock mode until Azure CLI is installed)"
fi

# 4. Check Claude Code CLI
echo "[4/6] Checking Claude Code CLI..."
if command -v claude &>/dev/null; then
    echo "  ✓ Claude Code CLI found: $(claude --version 2>/dev/null || echo 'installed')"
else
    echo "  ! Claude Code CLI ('claude') not found in PATH."
    echo "    To install: sudo npm install -g @anthropic-ai/claude-code"
    echo "    (App will run in Demo/Mock mode until Claude CLI is installed)"
fi

# 5. Check Medallion Skills (mcp-claude)
echo "[5/7] Checking Medallion Skills repository (AI Data Engineering Studio/mcp-claude)..."
FOUND_SKILL=false
MCP_CLAUDE_PATH=""
for CAND in "$SCRIPT_DIR/../mcp-claude" "$SCRIPT_DIR/mcp-claude" "$HOME/AI Data Engineering Studio/mcp-claude" "$HOME/Downloads/AI Data Engineering Studio/mcp-claude" "$HOME/mcp-claude" "$HOME/Downloads/mcp-claude"; do
    if [ -d "$CAND/.claude/skills/medallion" ]; then
        RESOLVED=$(cd "$CAND" && pwd)
        echo "  ✓ Medallion skills detected at: $RESOLVED"
        FOUND_SKILL=true
        MCP_CLAUDE_PATH="$RESOLVED"
        break
    fi
done

if [ "$FOUND_SKILL" = false ]; then
    echo "  ! Could not automatically locate 'mcp-claude' containing '.claude/skills/medallion'."
    echo "    Expected sibling layout: 'AI Data Engineering Studio/mcp-claude'"
fi

# 6. Check Microsoft Fabric MCP Server (fabric-mcp-server)
echo "[6/7] Checking Microsoft Fabric MCP repository (AI Data Engineering Studio/fabric-mcp-server)..."
FOUND_FABRIC_MCP=false
for CAND in "$SCRIPT_DIR/../fabric-mcp-server" "$SCRIPT_DIR/fabric-mcp-server" "$HOME/AI Data Engineering Studio/fabric-mcp-server" "$HOME/Downloads/AI Data Engineering Studio/fabric-mcp-server" "$HOME/fabric-mcp-server" "$HOME/Downloads/fabric-mcp-server"; do
    if [ -d "$CAND" ]; then
        RESOLVED_MCP=$(cd "$CAND" && pwd)
        echo "  ✓ Fabric MCP server detected at: $RESOLVED_MCP"
        FOUND_FABRIC_MCP=true
        break
    fi
done

if [ "$FOUND_FABRIC_MCP" = false ]; then
    echo "  ! 'fabric-mcp-server' not found locally as sibling directory."
    echo "    To clone locally into 'AI Data Engineering Studio':"
    echo "      git clone https://github.com/microsoft/fabric-mcp-server.git ../fabric-mcp-server"
    echo "    (Note: Claude Code can also run it on-demand via: npx -y @microsoft/fabric-mcp)"
fi

# If Claude CLI is installed, check MCP server registration
if command -v claude &>/dev/null && [ "$FOUND_SKILL" = true ]; then
    if claude mcp list 2>&1 | grep -iq "fabric"; then
        echo "  ✓ Fabric MCP server is registered in Claude Code."
    else
        echo "  ! 'fabric' MCP server not yet added to Claude Code."
        echo "    To register, run:"
        echo "      cd $MCP_CLAUDE_PATH && claude mcp add fabric -- npx -y @microsoft/fabric-mcp"
    fi
fi

# 7. Install Python & Frontend dependencies
echo "[7/7] Installing dependencies (backend Python packages & frontend node_modules)..."

# Backend Python dependencies (fastapi, uvicorn, python-dotenv, python-multipart, deltalake, pyarrow)
echo "  -> Installing Python backend packages (fastapi, uvicorn, python-dotenv, deltalake, pyarrow)..."
$PY_BIN -m pip install --quiet --upgrade pip 2>/dev/null || true
$PY_BIN -m pip install --quiet -r "$SCRIPT_DIR/backend/requirements.txt"
echo "  ✓ Backend Python packages installed."

# Frontend node_modules (react, vite, tailwindcss, react-icons, marked) and production build
echo "  -> Installing Frontend node_modules (react, vite, tailwindcss, react-icons, marked)..."
cd "$SCRIPT_DIR/frontend"
npm install --silent
echo "  ✓ Frontend node_modules installed."
echo "  -> Building frontend production bundle (Vite build -> dist)..."
npm run build
cd "$SCRIPT_DIR"
echo "  ✓ Frontend production build completed."

# Create .env if not exists
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "  ✓ Created .env from .env.example"
fi

echo ""
echo "=================================================================="
echo "  Setup Complete! You can now start the studio by running:"
echo "    ./start.sh"
echo "  or open in your browser at: http://localhost:8000"
echo "=================================================================="
echo ""
