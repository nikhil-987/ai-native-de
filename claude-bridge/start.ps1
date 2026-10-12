# ==============================================================================
# AI Data Engineering Studio - Portable Startup Script (Windows PowerShell)
# ==============================================================================
param(
    [string]$HostIp = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Dev = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Starting ADROSONIC AI Data Engineering Studio" -ForegroundColor Cyan
Write-Host "  Endpoint: http://localhost:$Port" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

if ($Dev) {
    Write-Host "Starting Vite Dev Server in parallel on http://localhost:5173..." -ForegroundColor Yellow
    Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory (Join-Path $ScriptDir "frontend")
}

# Run FastAPI backend server
$env:HOST = $HostIp
$env:PORT = $Port.ToString()
python (Join-Path $ScriptDir "backend\server.py")
