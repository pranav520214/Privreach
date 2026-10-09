# Privreach OS Patching & Updation Utility
param(
    [switch]$Check,
    [string]$Apply,
    [string]$Rollback,
    [switch]$Snapshots,
    [switch]$Status
)

$repoRoot = $PSScriptRoot
$pythonExe = Join-Path $repoRoot 'venv\Scripts\python.exe'
$updaterScript = Join-Path $repoRoot 'privreach\updater\cli.py'

$env:PYTHONPATH = $repoRoot

if ($Check) {
    & $pythonExe $updaterScript check
} elseif ($Apply) {
    & $pythonExe $updaterScript apply $Apply
} elseif ($Rollback) {
    & $pythonExe $updaterScript rollback $Rollback
} elseif ($Snapshots) {
    & $pythonExe $updaterScript snapshots
} else {
    & $pythonExe $updaterScript status
}
