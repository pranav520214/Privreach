# Privreach Web UI Launcher
# Launches the Three-Plane Research Operating Environment in the default web browser

$repoRoot = $PSScriptRoot
$pythonExe = Join-Path $repoRoot 'venv\Scripts\python.exe'
$webScript = Join-Path $repoRoot 'privreach\web_ui.py'

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '  PRIVREACH OS - THREE-PLANE WEB WORKSTATION (PORT 7860)' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

$env:PYTHONPATH = $repoRoot

# Open browser after a brief delay
Start-Process "http://127.0.0.1:7860"

Write-Host '[*] Starting Web UI on http://127.0.0.1:7860...' -ForegroundColor Green
& $pythonExe $webScript
