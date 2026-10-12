#!/usr/bin/env bash
# ==============================================================================
# AI Data Engineering Studio - Portable Startup Script (Linux / macOS / Cloud VM)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo ""
echo "=================================================================="
echo "  Starting ADROSONIC AI Data Engineering Studio"
echo "  Endpoint: http://localhost:$PORT (or http://<VM-IP>:$PORT)"
echo "=================================================================="
echo ""

PY_BIN="python3"
if ! command -v python3 &>/dev/null; then
    PY_BIN="python"
fi

export HOST
export PORT
exec $PY_BIN "$SCRIPT_DIR/backend/server.py"
