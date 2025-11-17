# Auto-Print Service - Start Service
# Run this script as Administrator

$ServiceName = "AutoPrintService"

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Error { Write-Host $args -ForegroundColor Red }

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "ERROR: This script must be run as Administrator!"
    exit 1
}

Write-Info "Starting $ServiceName..."
Start-Service -Name $ServiceName

if ($?) {
    Start-Sleep -Seconds 1
    $status = (Get-Service -Name $ServiceName).Status
    Write-Success "Service started successfully! Status: $status"
} else {
    Write-Error "Failed to start service"
    exit 1
}
