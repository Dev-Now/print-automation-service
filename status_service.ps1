# Auto-Print Service - Check Status
# Shows detailed service status and recent logs

param(
    [switch]$ShowLogs = $false,
    [int]$LogLines = 20
)

$ServiceName = "AutoPrintService"

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Info "=========================================="
Write-Info "  Auto-Print Service Status"
Write-Info "=========================================="
Write-Host ""

# Check if service exists
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Error "Service '$ServiceName' is not installed"
    Write-Info "To install, run: .\install_service.ps1"
    exit 1
}

# Display service information
Write-Info "Service Name:     $($service.Name)"
Write-Info "Display Name:     $($service.DisplayName)"

# Status with color
Write-Host -NoNewline "Status:           "
switch ($service.Status) {
    "Running" { Write-Success $service.Status }
    "Stopped" { Write-Error $service.Status }
    default { Write-Warning $service.Status }
}

Write-Info "Startup Type:     $($service.StartType)"

# Get process info if running
if ($service.Status -eq "Running") {
    try {
        $process = Get-Process | Where-Object { $_.Id -eq (Get-CimInstance -ClassName Win32_Service -Filter "Name='$ServiceName'").ProcessId }
        if ($process) {
            Write-Info "Process ID:       $($process.Id)"
            Write-Info "Memory (MB):      $([math]::Round($process.WorkingSet64 / 1MB, 2))"
            Write-Info "CPU Time:         $($process.TotalProcessorTime.ToString('hh\:mm\:ss'))"
            Write-Info "Start Time:       $($process.StartTime)"
        }
    } catch {
        # Silent fail if we can't get process info
    }
}

# Show logs if requested
if ($ShowLogs -or $service.Status -ne "Running") {
    Write-Host ""
    Write-Info "=========================================="
    Write-Info "  Recent Logs (last $LogLines lines)"
    Write-Info "=========================================="
    
    $LogDir = Join-Path $PSScriptRoot "logs"
    $MainLog = Join-Path $LogDir "log.txt"
    $StdoutLog = Join-Path $LogDir "service_stdout.log"
    $StderrLog = Join-Path $LogDir "service_stderr.log"
    
    if (Test-Path $MainLog) {
        Write-Host ""
        Write-Info "--- Application Log (log.txt) ---"
        Get-Content $MainLog -Tail $LogLines -ErrorAction SilentlyContinue
    }
    
    if (Test-Path $StdoutLog) {
        Write-Host ""
        Write-Info "--- Service Output (service_stdout.log) ---"
        Get-Content $StdoutLog -Tail $LogLines -ErrorAction SilentlyContinue
    }
    
    if (Test-Path $StderrLog) {
        $errContent = Get-Content $StderrLog -ErrorAction SilentlyContinue
        if ($errContent) {
            Write-Host ""
            Write-Warning "--- Service Errors (service_stderr.log) ---"
            $errContent | Select-Object -Last $LogLines
        }
    }
}

Write-Host ""
Write-Info "Tip: Use -ShowLogs flag to view recent logs"
Write-Info "     Example: .\status_service.ps1 -ShowLogs -LogLines 50"
