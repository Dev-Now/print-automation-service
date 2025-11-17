# Auto-Print Service - NSSM Installation Script
# This script installs the Auto-Print Service as a Windows Service using NSSM
# Run this script as Administrator

param(
    [string]$NssmPath = "C:\Tools\nssm\nssm.exe",
    [switch]$DownloadNssm = $false
)

$ErrorActionPreference = "Stop"
$ServiceName = "AutoPrintService"
$ServiceDisplayName = "Auto-Print Service"
$ServiceDescription = "Brother MFC-L2750DW Automated Printer Management"

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
Write-Info "  Auto-Print Service Installation"
Write-Info "=========================================="
Write-Host ""

# Get script directory (project root)
$ProjectRoot = $PSScriptRoot
$SrcPath = Join-Path $ProjectRoot "src"
$MainScript = Join-Path $SrcPath "main.py"

# Verify main.py exists
if (-not (Test-Path $MainScript)) {
    Write-Error "ERROR: main.py not found at: $MainScript"
    exit 1
}

# Find Python executable
Write-Info "Looking for Python installation..."
$PythonExe = $null

# Try common Python locations
$PythonLocations = @(
    (Get-Command python -ErrorAction SilentlyContinue).Source,
    (Get-Command python3 -ErrorAction SilentlyContinue).Source,
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)

foreach ($location in $PythonLocations) {
    if ($location -and (Test-Path $location)) {
        $PythonExe = $location
        break
    }
}

if (-not $PythonExe) {
    Write-Error "ERROR: Python not found!"
    Write-Info "Please install Python 3.11+ and add it to PATH"
    exit 1
}

Write-Success "Found Python: $PythonExe"

# Verify Python version
try {
    $PythonVersion = & $PythonExe --version 2>&1
    Write-Info "Python version: $PythonVersion"
} catch {
    Write-Error "ERROR: Could not verify Python version"
    exit 1
}

# Download NSSM if requested
if ($DownloadNssm) {
    Write-Info "Downloading NSSM..."
    $NssmDir = "C:\Tools\nssm"
    $NssmZip = "$env:TEMP\nssm.zip"
    $NssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    
    try {
        # Create directory
        New-Item -ItemType Directory -Force -Path $NssmDir | Out-Null
        
        # Download NSSM
        Write-Info "Downloading from $NssmUrl..."
        Invoke-WebRequest -Uri $NssmUrl -OutFile $NssmZip -UseBasicParsing
        
        # Extract
        Write-Info "Extracting NSSM..."
        Expand-Archive -Path $NssmZip -DestinationPath $env:TEMP -Force
        
        # Copy appropriate architecture
        $arch = if ([Environment]::Is64BitOperatingSystem) { "win64" } else { "win32" }
        Copy-Item "$env:TEMP\nssm-2.24\$arch\nssm.exe" -Destination $NssmDir -Force
        
        $NssmPath = Join-Path $NssmDir "nssm.exe"
        Write-Success "NSSM downloaded to: $NssmPath"
        
        # Cleanup
        Remove-Item $NssmZip -Force -ErrorAction SilentlyContinue
        Remove-Item "$env:TEMP\nssm-2.24" -Recurse -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Error "ERROR: Failed to download NSSM: $_"
        Write-Info "Please download manually from https://nssm.cc/download"
        exit 1
    }
}

# Verify NSSM exists
if (-not (Test-Path $NssmPath)) {
    Write-Error "ERROR: NSSM not found at: $NssmPath"
    Write-Info ""
    Write-Info "Please either:"
    Write-Info "  1. Download NSSM from https://nssm.cc/download and extract to C:\Tools\nssm\"
    Write-Info "  2. Run this script with -DownloadNssm flag to download automatically"
    Write-Info "     Example: .\install_service.ps1 -DownloadNssm"
    exit 1
}

Write-Success "Found NSSM: $NssmPath"

# Check if service already exists
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Warning "Service '$ServiceName' already exists!"
    $response = Read-Host "Do you want to reinstall? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Info "Installation cancelled."
        exit 0
    }
    
    Write-Info "Stopping and removing existing service..."
    & $NssmPath stop $ServiceName
    Start-Sleep -Seconds 2
    & $NssmPath remove $ServiceName confirm
    Start-Sleep -Seconds 2
}

# Install service
Write-Info ""
Write-Info "Installing service..."
& $NssmPath install $ServiceName $PythonExe $MainScript

if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: Failed to install service"
    exit 1
}

Write-Success "Service installed successfully!"

# Configure service
Write-Info "Configuring service..."

# Set working directory
& $NssmPath set $ServiceName AppDirectory $ProjectRoot

# Set display name and description
& $NssmPath set $ServiceName DisplayName $ServiceDisplayName
& $NssmPath set $ServiceName Description $ServiceDescription

# Set startup type to automatic
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Configure logging
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

$StdoutLog = Join-Path $LogDir "service_stdout.log"
$StderrLog = Join-Path $LogDir "service_stderr.log"

& $NssmPath set $ServiceName AppStdout $StdoutLog
& $NssmPath set $ServiceName AppStderr $StderrLog

# Rotate logs
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateOnline 1
& $NssmPath set $ServiceName AppRotateBytes 10485760  # 10 MB

# Set restart behavior
& $NssmPath set $ServiceName AppThrottle 1500  # Milliseconds before restart
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000  # 5 seconds delay

Write-Success "Service configured successfully!"

# Ask to start service
Write-Info ""
$startNow = Read-Host "Do you want to start the service now? (Y/n)"
if ($startNow -ne "n" -and $startNow -ne "N") {
    Write-Info "Starting service..."
    & $NssmPath start $ServiceName
    
    if ($LASTEXITCODE -eq 0) {
        Start-Sleep -Seconds 2
        $serviceStatus = & $NssmPath status $ServiceName
        Write-Success "Service started: $serviceStatus"
    } else {
        Write-Warning "Failed to start service. Check logs for details."
    }
}

# Display summary
Write-Info ""
Write-Info "=========================================="
Write-Info "  Installation Complete!"
Write-Info "=========================================="
Write-Info ""
Write-Info "Service Name:    $ServiceName"
Write-Info "Display Name:    $ServiceDisplayName"
Write-Info "Python:          $PythonExe"
Write-Info "Script:          $MainScript"
Write-Info "Working Dir:     $ProjectRoot"
Write-Info "Logs:            $LogDir"
Write-Info ""
Write-Info "Management Commands:"
Write-Info "  Start:         .\start_service.ps1"
Write-Info "  Stop:          .\stop_service.ps1"
Write-Info "  Restart:       .\restart_service.ps1"
Write-Info "  Status:        .\status_service.ps1"
Write-Info "  Uninstall:     .\uninstall_service.ps1"
Write-Info ""
Write-Info "Or use services.msc to manage the service through Windows GUI"
Write-Info ""
Write-Success "Installation successful!"
