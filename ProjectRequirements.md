# Auto-Print Service Requirements Documentation

**Project**: Automated Brother Printer Management System  
**Date**: October 26, 2025  
**Printer Model**: Brother MFC-L2750DW

---

## 1. USER REQUIREMENTS

### 1.1 Automatic Printer Connection
- User turns on Brother MFC-L2750DW printer (WiFi Direct)
- Background service automatically discovers printer
- Service connects to printer WiFi automatically
- Connection maintains stability (no disconnection due to "no internet")
- User maintains internet connection via Ethernet cable

### 1.2 Automated Print Queue Management
- User drops PDF/DOCX files into designated print_jobs directory
- Service automatically detects new files
- Service prints documents one by one in queue order
- DOCX files are converted to PDF before printing

### 1.3 Smart Failure Recovery
- Monitor each print job for completion
- Detect stuck jobs (timeout: 10 minutes)
- Automatic retry mechanism (max 3 attempts per job)
- Failed jobs retry after completing other queued jobs
- Comprehensive error logging

### 1.4 File Management
- Successfully printed documents moved to PRINTED archive folder
- Archive maintains original filename with timestamp
- Failed jobs remain in queue for retry or manual intervention

### 1.5 Logging & Audit Trail
- All print operations logged to log.txt
- Log entries include:
  * Timestamp
  * Filename
  * Print status (success/failure/retry)
  * Error messages (if any)

### 1.6 Service Behavior
- Service starts automatically on computer startup
- Runs as Windows background service
- Minimal resource usage when idle
- Graceful shutdown handling

### 1.7 Configuration Management
- User-editable config.json file
- Default print settings configurable:
  * Enable/disable toner save (ink saving mode)
  * Enable/disable duplex printing (both sides)
  * Duplex mode always set to "flip on long edge"
- Per-job configuration overrides (future enhancement)

### 1.8 File Type Restrictions
- Only PDF and DOCX files accepted
- Other file types ignored or rejected with warning
- DOCX files auto-converted to PDF before printing

---

## 2. TECHNICAL REQUIREMENTS

### 2.1 Hardware
- Brother MFC-L2750DW printer with WiFi Direct
- Windows computer with:
  * Ethernet connection for internet
  * WiFi adapter for printer connection
  * Sufficient storage for print queue and archives

### 2.2 Software
- Windows 10/11 operating system
- Python 3.11 or higher
- Brother printer drivers installed
- Required Python libraries (see requirements.txt)

### 2.3 Network
- Printer WiFi Direct SSID and password
- Stable Ethernet connection for internet
- WiFi adapter available for printer connection

### 2.4 Print Settings
- Black and white printing only
- Duplex printing (both sides, flip on long edge)
- Toner save mode enabled
- Paper size: Letter/A4 (auto-detect)

---

## 3. NON-FUNCTIONAL REQUIREMENTS

### 3.1 Reliability
- Service uptime: 99%+ when computer is running
- Automatic recovery from transient failures
- No manual intervention required for normal operations

### 3.2 Performance
- Print job detection: < 5 seconds
- Printer discovery: < 30 seconds
- WiFi connection: < 60 seconds
- Resource usage: < 50MB RAM, < 1% CPU when idle

### 3.3 Usability
- Simple drop-and-forget workflow
- Clear log messages for troubleshooting
- Easy configuration via JSON file
- No technical knowledge required for daily use

### 3.4 Maintainability
- Clean, modular code structure
- Comprehensive logging for debugging
- Easy to update configuration
- Simple service installation/uninstallation

---

## 4. SECURITY CONSIDERATIONS

- Printer WiFi password stored securely in config
- No external network access required (local only)
- File permissions restricted to user account
- Service runs with minimal required privileges

---

## 5. FUTURE ENHANCEMENTS (Out of Scope)

- Web interface for remote monitoring
- Mobile app notifications
- Multiple printer support
- Advanced scheduling (print at specific times)
- Email notifications for job completion
- Per-document configuration overrides
- Color printing support
- Scan-to-folder automation

---

## 6. SUCCESS CRITERIA

The project is successful when:

1. ✅ User can drop PDF into folder and walk away
2. ✅ Printer automatically connects when powered on
3. ✅ Documents print with correct settings (duplex, toner save)
4. ✅ Failed jobs retry automatically
5. ✅ All operations logged clearly
6. ✅ Service starts with Windows automatically
7. ✅ Zero manual intervention for 95%+ of print jobs
