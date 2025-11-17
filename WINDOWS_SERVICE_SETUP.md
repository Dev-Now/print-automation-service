# Windows Service Setup Guide

This guide walks you through converting the Auto-Print Service into a Windows Service using **NSSM (Non-Sucking Service Manager)**.

## 📋 Prerequisites

- Windows 10/11 or Windows Server
- Python 3.11+ installed
- Administrator privileges
- All Python dependencies installed (see `Requirements.txt`)

## 🚀 Quick Installation

### Option 1: Automatic Setup (Recommended)

Run the installation script as **Administrator**:

```powershell
# Auto-download NSSM and install service
.\install_service.ps1 -DownloadNssm

# Or if you already have NSSM installed
.\install_service.ps1
```

**That's it!** The service will be installed and configured automatically.

---

### Option 2: Manual Setup

1. **Download NSSM**
   - Go to https://nssm.cc/download
   - Download the latest version
   - Extract `nssm.exe` to `C:\Tools\nssm\`

2. **Run Installation Script**
   ```powershell
   # Run as Administrator
   .\install_service.ps1
   ```

---

## 🎮 Service Management

Use the provided PowerShell scripts (run as Administrator):

### Start Service
```powershell
.\start_service.ps1
```

### Stop Service
```powershell
.\stop_service.ps1
```

### Restart Service
```powershell
.\restart_service.ps1
```

### Check Status
```powershell
# Basic status
.\status_service.ps1

# Status with recent logs
.\status_service.ps1 -ShowLogs

# Status with more log lines
.\status_service.ps1 -ShowLogs -LogLines 50
```

### Uninstall Service
```powershell
.\uninstall_service.ps1
```

---

## 📊 Using Windows Services Manager

You can also manage the service through the Windows GUI:

1. Press `Win + R`
2. Type `services.msc` and press Enter
3. Find **"Auto-Print Service"** in the list
4. Right-click to Start, Stop, or configure

---

## 📝 Configuration

### Service Details

- **Service Name:** `AutoPrintService`
- **Display Name:** Auto-Print Service
- **Description:** Brother MFC-L2750DW Automated Printer Management
- **Startup Type:** Automatic (starts with Windows)
- **Recovery:** Automatically restarts on failure

### Log Files

Logs are stored in the `logs/` directory:

- **`log.txt`** - Main application log (from your Python logger)
- **`service_stdout.log`** - Service standard output
- **`service_stderr.log`** - Service error output

Logs automatically rotate when they reach 10 MB.

### Auto-Restart Configuration

The service is configured to automatically restart if it crashes:
- **Restart Delay:** 5 seconds
- **Throttle Time:** 1.5 seconds (prevents rapid restart loops)

---

## 🔧 Troubleshooting

### Service Won't Start

1. **Check Python Path**
   ```powershell
   python --version
   ```
   Ensure Python 3.11+ is installed and in PATH

2. **Check Dependencies**
   ```powershell
   pip install -r Requirements.txt
   ```

3. **View Logs**
   ```powershell
   .\status_service.ps1 -ShowLogs
   ```

4. **Test Script Manually**
   ```powershell
   python src\main.py
   ```
   If it works manually but not as a service, check the service logs.

### Service Starts but Doesn't Work

1. **Check Application Log**
   ```powershell
   Get-Content logs\log.txt -Tail 50
   ```

2. **Verify Configuration**
   - Ensure `config/config.json` exists and is valid
   - Check Gotenberg Docker container is running (if using DOCX conversion)
   - Verify WiFi credentials are correct

3. **Check Permissions**
   - Service runs under Local System account by default
   - May need network/folder permissions for WiFi and file operations

### Change Service User Account

By default, the service runs as Local System. To run under a different account:

```powershell
# Using NSSM
C:\Tools\nssm\nssm.exe set AutoPrintService ObjectName "DOMAIN\Username" "Password"

# Or use services.msc GUI:
# 1. Open services.msc
# 2. Right-click "Auto-Print Service" > Properties
# 3. Log On tab > "This account" > Enter credentials
```

### View Detailed Service Status

```powershell
# Using NSSM
C:\Tools\nssm\nssm.exe status AutoPrintService

# Using Windows
Get-Service AutoPrintService | Format-List *

# View Event Viewer logs
eventvwr.msc
# Navigate to: Windows Logs > Application
# Filter by source: "AutoPrintService"
```

---

## 🔄 Updating the Service

After making code changes:

1. **Stop the service**
   ```powershell
   .\stop_service.ps1
   ```

2. **Update your code**
   - Edit Python files as needed
   - Test manually: `python src\main.py`

3. **Restart the service**
   ```powershell
   .\start_service.ps1
   ```

No need to reinstall unless you change Python executable location.

---

## 🎯 Advanced Configuration

### Custom NSSM Location

If NSSM is installed elsewhere:

```powershell
.\install_service.ps1 -NssmPath "D:\Tools\nssm.exe"
```

### Change Service Configuration

Use NSSM to modify settings:

```powershell
# Edit service configuration GUI
C:\Tools\nssm\nssm.exe edit AutoPrintService

# Set environment variables
C:\Tools\nssm\nssm.exe set AutoPrintService AppEnvironmentExtra VAR=value

# Change restart delay (milliseconds)
C:\Tools\nssm\nssm.exe set AutoPrintService AppRestartDelay 10000

# Set process priority
C:\Tools\nssm\nssm.exe set AutoPrintService AppPriority NORMAL_PRIORITY_CLASS
```

---

## 📦 What NSSM Does

NSSM handles all the Windows Service complexity for you:

- ✅ Registers your Python script as a Windows Service
- ✅ Automatically restarts on crashes
- ✅ Starts on Windows boot
- ✅ Captures logs (stdout/stderr)
- ✅ Manages process lifecycle
- ✅ Provides graceful shutdown
- ✅ No code changes required

---

## 🆚 Comparison with pywin32 Approach

| Feature | NSSM | pywin32 |
|---------|------|---------|
| **Code Changes** | None required | Requires wrapper code |
| **Setup Complexity** | Very simple | Moderate |
| **Debugging** | Easy (logs to files) | More complex |
| **Restart Handling** | Automatic | Manual implementation |
| **Maintenance** | Minimal | Requires service updates |
| **Best For** | Quick deployment, any Python app | Full control, enterprise apps |

**Recommendation:** Start with NSSM. Switch to pywin32 only if you need advanced service integration or custom event handling.

---

## 📚 Additional Resources

- **NSSM Documentation:** https://nssm.cc/usage
- **Service Logs:** `logs/` directory
- **Configuration:** `config/config.json`
- **Windows Services:** Run `services.msc`
- **Event Viewer:** Run `eventvwr.msc`

---

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] Service appears in `services.msc`
- [ ] Service starts successfully
- [ ] Logs are being written to `logs/` directory
- [ ] WiFi connection to printer works
- [ ] Files in `print_jobs/` are detected and printed
- [ ] DOCX conversion works (if Gotenberg is running)
- [ ] Service survives system restart

---

## 🆘 Getting Help

If you encounter issues:

1. Check status with logs: `.\status_service.ps1 -ShowLogs`
2. Test manually: `python src\main.py`
3. Review Event Viewer for system-level errors
4. Check all prerequisites are met
5. Verify file permissions in project directory

---

## 📝 Notes

- The service runs under **Local System** account by default
- Configuration changes require service restart
- Log files rotate automatically at 10 MB
- Service has 5-second delay before restart on failure
- All scripts require Administrator privileges

---

**Installation created:** November 2025  
**NSSM Version:** 2.24+ recommended  
**Python Version:** 3.11+ required
