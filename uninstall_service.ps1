# Auto-Print Service - Uninstallation Script
# This script removes the Auto-Print Service Windows Service
# Run this script as Administrator

param(
    [string]$NssmPath = "C:\Tools\nssm\nssm.exe"
)

$ErrorActionPreference = "Stop"
$ServiceName = "AutoPrintService"

# Color output functions
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "ERROR: This script must be run as Administrator!"
    Write-Info "Right-click PowerShell and select 'Run as Administrator', then run this script again."
    exit 1
}

Write-Info "=========================================="
Write-Info "  Auto-Print Service Uninstallation"
Write-Info "=========================================="
Write-Host ""

# Check if NSSM exists
if (-not (Test-Path $NssmPath)) {
    Write-Warning "NSSM not found at: $NssmPath"
    Write-Info "Attempting to remove service using sc.exe..."
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq "Running") {
            Write-Info "Stopping service..."
            Stop-Service -Name $ServiceName -Force
            Start-Sleep -Seconds 2
        }
        
        Write-Info "Removing service..."
        sc.exe delete $ServiceName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Service removed successfully!"
        } else {
            Write-Error "Failed to remove service"
            exit 1
        }
    } else {
        Write-Warning "Service '$ServiceName' not found"
    }
    exit 0
}

# Check if service exists
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Warning "Service '$ServiceName' is not installed"
    exit 0
}

# Confirm uninstallation
Write-Warning "This will permanently remove the '$ServiceName' service."
$response = Read-Host "Are you sure you want to continue? (y/N)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Info "Uninstallation cancelled."
    exit 0
}

# Stop service if running
$serviceStatus = & $NssmPath status $ServiceName 2>$null
if ($serviceStatus -eq "SERVICE_RUNNING") {
    Write-Info "Stopping service..."
    & $NssmPath stop $ServiceName
    Start-Sleep -Seconds 3
    Write-Success "Service stopped"
}

# Remove service
Write-Info "Removing service..."
& $NssmPath remove $ServiceName confirm

if ($LASTEXITCODE -eq 0) {
    Write-Success "Service removed successfully!"
    Write-Info ""
    Write-Info "Note: Log files and configuration have been preserved"
    Write-Info "To reinstall, run: .\install_service.ps1"
} else {
    Write-Error "Failed to remove service"
    exit 1
}

Write-Info ""
Write-Success "Uninstallation complete!"
