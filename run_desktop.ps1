# Privreach OS Native Desktop Workstation Launcher
# Starts local high-performance REST engine and launches WinUI 3 Fluent Workstation

$Host.UI.RawUI.WindowTitle = 'Privreach OS Native Desktop Launcher'

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '  PRIVREACH OS - NATIVE FLUENT DESKTOP WORKSTATION v2.0' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

$repoRoot = $PSScriptRoot
$pythonExe = Join-Path $repoRoot 'venv\Scripts\python.exe'
$serverScript = Join-Path $repoRoot 'privreach\desktop_server.py'
$desktopProj = Join-Path $repoRoot 'PrivreachDesktop\PrivreachDesktop.csproj'

# 1. Check if backend server is running on port 8765
$portListening = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
if (-not $portListening) {
    Write-Host '[1/2] Starting Local AI Engine & Knowledge Vault Server...' -ForegroundColor Yellow
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $pythonExe
    $psi.Arguments = ('"{0}" 127.0.0.1 8765' -f $serverScript)
    $psi.WorkingDirectory = $repoRoot
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    $psi.EnvironmentVariables['PYTHONPATH'] = $repoRoot
    [System.Diagnostics.Process]::Start($psi) | Out-Null
    Start-Sleep -Seconds 2
} else {
    Write-Host '[1/2] Local Engine already online on port 8765.' -ForegroundColor Green
}

$desktopExe = Join-Path $repoRoot 'PrivreachDesktop\bin\x64\Debug\net8.0-windows10.0.26100.0\win-x64\PrivreachDesktop.exe'

# 2. Launch Native WinUI 3 Application
$runningApp = Get-Process PrivreachDesktop -ErrorAction SilentlyContinue
if ($runningApp) {
    Write-Host "[*] Stopping existing PrivreachDesktop instance (PID $($runningApp.Id)) for fresh launch..." -ForegroundColor Yellow
    Stop-Process -Name PrivreachDesktop -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
}

Write-Host '[2/2] Launching WinUI 3 Native Workstation...' -ForegroundColor Yellow
winapp run $desktopProj --detach --json | Out-Null

Write-Host '[OK] Privreach Workstation launched successfully!' -ForegroundColor Green
Write-Host 'Zero-Trust Air-Gapped Operation | CPU Embeddings + 4GB VRAM' -ForegroundColor Gray
