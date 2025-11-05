# Auto-Print Service Implementation Plan
# Project: Automated Brother Printer Management System
# Date: October 26, 2025
# Printer Model: Brother MFC-L2750DW (WiFi Direct)

## Overview

This document outlines the step-by-step implementation plan for building an automated printer service that handles WiFi connection, print queue management, and failure recovery.

---

## Architecture

### Project Structure
```
auto-print/
├── src/
│   ├── main.py                    # Entry point & service loop
│   ├── wifi_manager.py            # WiFi connection handling
│   ├── printer_manager.py         # Printer discovery & control
│   ├── print_queue_manager.py     # Job queue & retry logic
│   ├── file_watcher.py            # Monitor print directory
│   ├── config_manager.py          # Load & validate config
│   └── utils/
│       ├── logger.py              # Logging utilities
│       └── helpers.py             # Common helper functions
├── config/
│   └── config.json                # User-editable settings
├── print_jobs/                    # User drops PDFs here
│   └── PRINTED/                   # Archive folder
├── logs/
│   └── log.txt                    # Operation logs
├── tests/                         # Unit tests
│   └── test_*.py
├── requirements.txt               # Python dependencies
├── install_service.py             # Service installer script
├── uninstall_service.py           # Service uninstaller script
├── ProjectRequirements.md         # Project requirements doc
├── ImplementationPlan.md          # This file
└── README.md                      # User documentation
```

### Technology Stack
- **Language**: Python 3.11+
- **Core Libraries**:
  - `pywin32` (win32print, win32api, win32service) - Windows APIs
  - `pywifi` - WiFi management
  - `watchdog` - File system monitoring
  - `pandoc` - DOCX to PDF conversion (system dependency)
- **Service Manager**: NSSM or pywin32 service wrapper

---

## Implementation Phases

### Phase 1: Core Infrastructure Setup ✓
**Goal**: Establish project foundation

#### Tasks:
1. ✓ Create project directory structure
2. ✓ Set up Python virtual environment
3. ✓ Create requirements.txt for dependencies
4. ✓ Implement config_manager.py
   - Load and validate config.json
   - Provide default values
   - Handle missing/invalid configs
5. ✓ Implement logger.py
   - Console and file logging
   - Timestamp formatting
   - Log rotation support
6. ✓ Create initial config.json template
7. ✓ Set up basic main.py entry point

#### Deliverables:
- Working Python environment
- Config loading system
- Logging system
- Basic service skeleton

#### Testing:
- Config loads successfully
- Logs write to file
- Invalid config handled gracefully

---

### Phase 2: WiFi Management
**Goal**: Automatic printer WiFi connection

#### Tasks:
1. Implement wifi_manager.py
   - Scan for WiFi networks
   - Detect printer WiFi Direct SSID
   - Connect to printer WiFi with password
   - Handle connection failures
   - Prevent auto-disconnect (set connection priority)
2. Add WiFi connection monitoring
3. Implement reconnection logic
4. Windows network profile management
   - Set "no internet expected" flag
   - Disable auto-switching

#### Technical Approach:
```python
# Using pywifi or subprocess + netsh commands
# netsh wlan show networks
# netsh wlan connect name="DIRECT-xx-Brother" ssid="DIRECT-xx-Brother"
# netsh wlan set profileparameter name="DIRECT-xx-Brother" cost=unrestricted
```

#### Deliverables:
- Auto-connect to printer WiFi
- Stable connection maintained
- Reconnection on failure

#### Testing:
- Connect when printer turns on
- Stay connected during print job
- Reconnect after temporary disconnect
- Maintain internet via Ethernet

---

### Phase 3: Printer Communication
**Goal**: Discover and control Brother printer

#### Tasks:
1. Implement printer_manager.py
   - Discover printer on network (mDNS/Bonjour or IP scan)
   - List available printers
   - Select Brother MFC-L2750DW
   - Verify printer is ready
2. Configure print settings
   - Set duplex mode (DuplexVertical for long edge)
   - Enable toner save mode
   - Set black & white (grayscale)
   - Set paper size
3. Send test print job
4. Monitor print job status
5. Handle printer errors (out of paper, jam, etc.)

#### Technical Approach:
```python
# Using win32print
import win32print
import win32api

# Get printer handle
printer_handle = win32print.OpenPrinter(printer_name)

# Set printer settings via DEVMODE structure
# Send document with configured settings
```

#### Deliverables:
- Printer discovery working
- Print settings configured correctly
- Test print successful

#### Testing:
- Print test PDF with duplex
- Verify toner save mode active
- Confirm long-edge flipping
- Handle printer offline scenario

---

### Phase 4: Queue & File Management
**Goal**: Automated file detection and processing

#### Tasks:
1. Implement file_watcher.py
   - Monitor print_jobs folder
   - Detect new PDF/DOCX files
   - Ignore other file types
   - Handle file system events
2. Implement print_queue_manager.py
   - Maintain print job queue (FIFO)
   - Track job status (pending, printing, completed, failed)
   - Handle concurrent file additions
3. Add DOCX to PDF conversion
   - Validate DOCX file
   - Convert to PDF
   - Use converted PDF for printing
   - Clean up temporary files
4. Implement file archival
   - Move printed files to PRINTED folder
   - Add timestamp to archived filename
   - Handle filename conflicts
5. PDF validation
   - Check if file is valid PDF
   - Verify not corrupted
   - Log validation errors

#### Technical Approach:
```python
# Using watchdog for file monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Using pandoc via subprocess for DOCX conversion
import subprocess
subprocess.run(['pandoc', 'input.docx', '-o', 'output.pdf'])
```

#### Deliverables:
- Auto-detect new files
- Print queue working
- DOCX conversion working
- Archive system working

#### Testing:
- Drop PDF → auto prints
- Drop DOCX → converts and prints
- Multiple files queued correctly
- Files archived after printing

---

### Phase 5: Reliability & Error Handling
**Goal**: Robust failure recovery

#### Tasks:
1. Implement job timeout detection
   - Track print job start time
   - Monitor for 10-minute timeout
   - Cancel stuck jobs
2. Add retry logic
   - Track retry count per job
   - Retry failed jobs (max 3 times)
   - Move job to end of queue on retry
   - Log retry attempts
3. Handle printer errors
   - Detect paper jam, out of paper, etc.
   - Pause queue until resolved
   - Resume automatically when ready
4. Handle network errors
   - WiFi disconnect during print
   - Printer offline
   - Automatic recovery
5. Implement graceful shutdown
   - Save queue state
   - Clean up resources
   - Log shutdown event
6. Add detailed logging
   - Job lifecycle events
   - Error details with stack traces
   - Performance metrics

#### Deliverables:
- Jobs timeout and retry
- Max 3 retry attempts
- Graceful error recovery
- Comprehensive logging

#### Testing:
- Simulate stuck job (timeout)
- Turn printer off mid-job
- Disconnect WiFi during print
- Paper jam scenario
- Verify retries work correctly

---

### Phase 6: Windows Service Integration
**Goal**: Run as background service on startup

#### Tasks:
1. Create service wrapper
   - Use pywin32 servicemanager
   - Implement service lifecycle (start, stop, pause)
   - Handle service events
2. Create install_service.py
   - Register service with Windows
   - Set auto-start on boot
   - Configure service parameters
3. Create uninstall_service.py
   - Stop service
   - Unregister from Windows
   - Clean up resources
4. Add service management
   - Start/stop commands
   - Status checking
   - Restart on failure
5. Test service behavior
   - Auto-start on boot
   - Run in background
   - Survive user logout

#### Technical Approach:
```python
# Using pywin32 service framework
import win32serviceutil
import win32service
import win32event
import servicemanager

class AutoPrintService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AutoPrintService"
    _svc_display_name_ = "Auto Print Service"
    _svc_description_ = "Automated Brother Printer Management"
```

**Alternative**: Use NSSM (Non-Sucking Service Manager)
- Simpler installation
- Better error handling
- Easier debugging

#### Deliverables:
- Working Windows service
- Auto-start on boot
- Service management scripts

#### Testing:
- Service installs correctly
- Auto-starts on reboot
- Survives user logout
- Can be stopped/started manually
- Logs work from service context

---

## Configuration Schema

### config.json Structure
```json
{
  "printer": {
    "wifi_ssid": "DIRECT-xx-Brother MFC-L2750DW",
    "wifi_password": "your_wifi_password",
    "name": "Brother MFC-L2750DW",
    "discovery_timeout": 30,
    "connection_timeout": 60
  },
  "print_settings": {
    "duplex": true,
    "duplex_mode": "DuplexVertical",
    "toner_save": true,
    "color": false,
    "copies": 1,
    "paper_size": "Letter"
  },
  "paths": {
    "print_jobs": "./print_jobs",
    "archive": "./print_jobs/PRINTED",
    "logs": "./logs"
  },
  "behavior": {
    "job_timeout_minutes": 10,
    "max_retries": 3,
    "check_interval_seconds": 5,
    "convert_docx_to_pdf": true,
    "allowed_extensions": [".pdf", ".docx"]
  },
  "network": {
    "maintain_internet": true,
    "wifi_check_interval_seconds": 30,
    "reconnect_attempts": 5
  },
  "logging": {
    "level": "INFO",
    "max_file_size_mb": 10,
    "backup_count": 5
  }
}
```

---

## Error Handling Strategy

### Error Categories:
1. **Transient Errors** (retry automatically)
   - Printer temporarily offline
   - WiFi connection dropped
   - Printer busy

2. **Recoverable Errors** (retry with backoff)
   - Print job timeout
   - Network timeout
   - File temporarily locked

3. **Permanent Errors** (log and skip)
   - Invalid PDF file
   - Corrupted document
   - Unsupported file type
   - Max retries exceeded

### Logging Format:
```
[2025-10-26 14:30:45] INFO: Service started
[2025-10-26 14:30:50] INFO: WiFi connected to DIRECT-xx-Brother
[2025-10-26 14:31:00] INFO: Printer discovered: Brother MFC-L2750DW
[2025-10-26 14:31:15] INFO: New file detected: report.pdf
[2025-10-26 14:31:16] INFO: Printing: report.pdf (1/1)
[2025-10-26 14:32:30] SUCCESS: Printed and archived: report.pdf
[2025-10-26 14:35:00] ERROR: Print timeout: invoice.pdf (attempt 1/3)
[2025-10-26 14:35:05] INFO: Retrying: invoice.pdf
```

---

## Testing Strategy

### Unit Tests:
- Config loading and validation
- WiFi connection logic
- Printer discovery
- File detection and filtering
- Queue management
- Retry logic

### Integration Tests:
- End-to-end print workflow
- Error recovery scenarios
- Service lifecycle

### Manual Tests:
- Printer power on/off cycles
- Network interruption handling
- Various document types
- Service restart behavior

---

## Development Workflow

### Phase Completion Criteria:
Each phase must meet these criteria before moving to next phase:
1. All tasks completed
2. Unit tests pass
3. Manual testing successful
4. Code reviewed and refactored
5. Documentation updated
6. User approval received

### Version Control:
- Commit after each completed task
- Tag after each phase completion
- Document breaking changes

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Windows blocks WiFi auto-connect | High | Use netsh commands, set connection priority |
| Printer driver incompatibility | High | Test with Brother drivers, use standard PCL/PS |
| Print job status unreliable | Medium | Implement timeout-based detection |
| Service crashes on error | High | Comprehensive exception handling |
| Config file corrupted | Medium | Validate on load, provide defaults |
| Files locked by other processes | Low | Retry with backoff, log warning |

---

## Success Metrics

### Performance:
- Print job detection: < 5 seconds
- Printer connection: < 60 seconds
- Job completion logging: < 1 second

### Reliability:
- Successful print rate: > 95%
- Auto-recovery rate: > 90%
- Service uptime: > 99%

### Usability:
- Zero-config for standard use case
- Clear error messages
- Easy troubleshooting via logs

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|----------------|------------|
| Phase 1: Infrastructure | 2-3 hours | Low |
| Phase 2: WiFi Management | 4-6 hours | High |
| Phase 3: Printer Control | 4-6 hours | Medium |
| Phase 4: Queue Management | 3-4 hours | Medium |
| Phase 5: Error Handling | 3-4 hours | Medium |
| Phase 6: Service Integration | 2-3 hours | Medium |
| **Total** | **18-26 hours** | - |

*Note: Timeline assumes familiarity with Python and Windows APIs*

---

## Next Steps

1. ✓ Create project structure
2. ✓ Document requirements
3. ✓ Create implementation plan
4. → Set up Python environment and dependencies
5. → Begin Phase 1 implementation

---

## Notes

- WiFi Direct typically uses SSID format: `DIRECT-xx-Brother MFC-L2750DW`
- Brother MFC-L2750DW supports PCL6 and BR-Script3 (PostScript)
- Default WiFi Direct password is usually 8 digits (check printer panel)
- Windows may require "Run as Administrator" for WiFi management
- Consider using NSSM for service wrapper (simpler than pywin32)

---

## Resources

- Brother MFC-L2750DW User Manual
- Windows Print Spooler API Documentation
- PyWin32 Documentation
- pywifi GitHub Repository
- Windows netsh Command Reference
