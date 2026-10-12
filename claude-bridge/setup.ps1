# ==============================================================================
# AI Data Engineering Studio - Portable Setup Script (Windows PowerShell)
# ==============================================================================

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  ADROSONIC - AI Data Engineering Studio - Portable Setup" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Check Python
Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVer = python --version 2>&1
    Write-Host "  [OK] Found: $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "  [!] Python 3.10+ is required but not found in PATH." -ForegroundColor Red
    Write-Host "      Install from: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 2. Check Node.js
Write-Host "[2/7] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVer = node --version 2>&1
    $npmVer = npm --version 2>&1
    Write-Host "  [OK] Found Node: $nodeVer, npm: $npmVer" -ForegroundColor Green
} catch {
    Write-Host "  [!] Node.js 18+ is required but not found in PATH." -ForegroundColor Red
    Write-Host "      Install from: https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# 3. Check Azure CLI
Write-Host "[3/7] Checking Azure CLI..." -ForegroundColor Yellow
$azFound = $false
try {
    $azVer = az version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $azFound = $true
        Write-Host "  [OK] Azure CLI is installed." -ForegroundColor Green
        
        $azAccount = az account show 2>&1
        if ($LASTEXITCODE -eq 0) {
            $user = ($azAccount | ConvertFrom-Json).user.name
            Write-Host "  [OK] Logged in as: $user" -ForegroundColor Green
        } else {
            Write-Host "  [!] Azure CLI installed but not logged in. Please run: az login" -ForegroundColor Yellow
        }
    }
} catch {
    # Azure CLI not in PATH
}

if (-not $azFound) {
    Write-Host "  [!] Azure CLI ('az') not found in PATH. Install from: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host "      (App will run in Demo/Mock mode until Azure CLI is installed)" -ForegroundColor Gray
}

# 4. Check Claude Code CLI
Write-Host "[4/7] Checking Claude Code CLI..." -ForegroundColor Yellow
$claudeFound = $false
try {
    $claudeVer = claude --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $claudeFound = $true
        Write-Host "  [OK] Claude Code CLI found: $claudeVer" -ForegroundColor Green
    }
} catch {
    # Claude CLI not in PATH
}

if (-not $claudeFound) {
    Write-Host "  [*] Claude Code CLI ('claude') not found in PATH." -ForegroundColor Yellow
    Write-Host "      To install: npm install -g @anthropic-ai/claude-code" -ForegroundColor Gray
    Write-Host "      (App will run in Demo/Mock mode until Claude CLI is installed)" -ForegroundColor Gray
}

# 5. Check Medallion Skills (mcp-claude)
Write-Host "[5/7] Checking Medallion Skills repository (AI Data Engineering Studio\mcp-claude)..." -ForegroundColor Yellow
$mcpClaudeCandidates = @(
    (Join-Path $ScriptDir "..\mcp-claude"),
    (Join-Path $ScriptDir "mcp-claude"),
    (Join-Path $env:USERPROFILE "AI Data Engineering Studio\mcp-claude"),
    (Join-Path $env:USERPROFILE "Downloads\AI Data Engineering Studio\mcp-claude"),
    (Join-Path $env:USERPROFILE "Downloads\mcp-claude")
)

$foundSkill = $false
$mcpClaudePath = $null
foreach ($cand in $mcpClaudeCandidates) {
    $skillPath = Join-Path $cand ".claude\skills\medallion"
    if (Test-Path $skillPath) {
        $mcpClaudePath = (Resolve-Path $cand).Path
        Write-Host "  [OK] Medallion skills detected at: $mcpClaudePath" -ForegroundColor Green
        $foundSkill = $true
        break
    }
}

if (-not $foundSkill) {
    Write-Host "  [!] Could not automatically locate 'mcp-claude' containing '.claude/skills/medallion'." -ForegroundColor Yellow
    Write-Host "      Expected sibling layout: 'AI Data Engineering Studio\mcp-claude'" -ForegroundColor Gray
}

# 6. Check Microsoft Fabric MCP Server (fabric-mcp-server)
Write-Host "[6/7] Checking Microsoft Fabric MCP repository (AI Data Engineering Studio\fabric-mcp-server)..." -ForegroundColor Yellow
$fabricMcpCandidates = @(
    (Join-Path $ScriptDir "..\fabric-mcp-server"),
    (Join-Path $ScriptDir "fabric-mcp-server"),
    (Join-Path $env:USERPROFILE "AI Data Engineering Studio\fabric-mcp-server"),
    (Join-Path $env:USERPROFILE "Downloads\AI Data Engineering Studio\fabric-mcp-server"),
    (Join-Path $env:USERPROFILE "Downloads\fabric-mcp-server")
)

$foundFabricMcp = $false
foreach ($cand in $fabricMcpCandidates) {
    if (Test-Path $cand) {
        $resolvedMcp = (Resolve-Path $cand).Path
        Write-Host "  [OK] Fabric MCP server detected at: $resolvedMcp" -ForegroundColor Green
        $foundFabricMcp = $true
        break
    }
}

if (-not $foundFabricMcp) {
    Write-Host "  [*] 'fabric-mcp-server' not found locally as sibling directory." -ForegroundColor Yellow
    Write-Host "      To clone locally into 'AI Data Engineering Studio':" -ForegroundColor Gray
    Write-Host "        git clone https://github.com/microsoft/fabric-mcp-server.git ..\fabric-mcp-server" -ForegroundColor Cyan
    Write-Host "      (Note: Claude Code can also run it on-demand via: npx -y @microsoft/fabric-mcp)" -ForegroundColor Gray
}

# 7. Install Python & Frontend dependencies
Write-Host "[7/7] Installing dependencies (backend Python & frontend node_modules)..." -ForegroundColor Yellow

# Backend Python packages (FastAPI, Uvicorn, Pydantic, python-dotenv, python-multipart, deltalake, pyarrow)
Write-Host "  -> Installing Backend Python packages (fastapi, uvicorn, python-dotenv, deltalake, pyarrow)..." -ForegroundColor Gray
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r (Join-Path $ScriptDir "backend\requirements.txt")
Write-Host "  [OK] Backend Python packages installed." -ForegroundColor Green

# Frontend node_modules (React 18, Vite 5, TailwindCSS v4, React-Icons, Marked, DOMPurify)
Write-Host "  -> Installing Frontend node_modules (react, vite, tailwindcss, react-icons, marked)..." -ForegroundColor Gray
Push-Location (Join-Path $ScriptDir "frontend")
npm install --silent
Write-Host "  [OK] Frontend node_modules installed." -ForegroundColor Green
Write-Host "  -> Building frontend production bundle (Vite build -> dist)..." -ForegroundColor Gray
try {
    npm run build
    Write-Host "  [OK] Frontend production build completed." -ForegroundColor Green
} finally {
    Pop-Location
}

# Create .env if not exists
$envFile = Join-Path $ScriptDir ".env"
$envExample = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "  [OK] Created .env from .env.example" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "  Setup Complete! You can now start the studio by running:" -ForegroundColor Green
Write-Host "    .\start.ps1" -ForegroundColor Cyan
Write-Host "  or open in your browser at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
