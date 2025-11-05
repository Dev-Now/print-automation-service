# Auto-Print Service

**Automated Brother MFC-L2750DW Printer Management**

A Windows service that automatically connects to your Brother printer via WiFi Direct and manages print jobs with smart queue management, failure recovery, and automatic archival.

---

## Features

✅ **Automatic WiFi Connection** - Connects to printer WiFi Direct when printer is turned on  
✅ **Smart Print Queue** - Drop PDFs/DOCX files in a folder, they print automatically  
✅ **DOCX Support** - Automatically converts DOCX to PDF before printing  
✅ **Failure Recovery** - Retries failed jobs up to 3 times with smart handling  
✅ **Auto Archival** - Successfully printed files moved to PRINTED folder with timestamp  
✅ **Comprehensive Logging** - All operations logged with timestamps  
✅ **Windows Service** - Starts automatically with system boot  
✅ **Configurable** - Easy JSON configuration for all settings  

---

## Requirements

- **Operating System**: Windows 10/11
- **Python**: 3.11 or higher
- **Printer**: Brother MFC-L2750DW with WiFi Direct enabled
- **Network**: Ethernet connection (for maintaining internet while connected to printer WiFi)
- **Drivers**: Brother MFC-L2750DW printer drivers installed

---

## Installation

### 1. Clone or Download the Project

```powershell
cd D:\Programming
git clone <repository-url> auto-print
cd auto-print
```

### 2. Install Python Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 3. Configure the Service

**Copy the configuration template:**

```powershell
# Copy template to create your config
copy config\config.json.template config\config.json
```

**Edit `config/config.json` with your printer details:**

```json
{
  "printer": {
    "wifi_ssid": "DIRECT-xx-Brother MFC-L2750DW",
    "wifi_password": "your_printer_wifi_password",
    "name": "Brother MFC-L2750DW"
  }
}
```

**To find your printer WiFi details:**
1. Turn on your Brother MFC-L2750DW
2. On printer panel: Menu → Network → WLAN → Wi-Fi Direct
3. Note the SSID and password
4. Update `config/config.json` with these values

**Note:** The `config.json` file contains your WiFi password and is excluded from version control for security.

### 4. Test the Service (Optional)

Before installing as a service, test it manually:

```powershell
python src\main.py
```

- Drop a PDF file into the `print_jobs` folder
- Check if it prints automatically
- Press `Ctrl+C` to stop

### 5. Install as Windows Service

```powershell
# Run as Administrator
python install_service.py
```

### 6. Start the Service

```powershell
# Start service
net start AutoPrintService

# Check service status
sc query AutoPrintService
```

---

## Usage

### Printing Files

1. **Turn on** your Brother MFC-L2750DW printer
2. **Drop** PDF or DOCX files into the `print_jobs` folder
3. **DOCX files** are automatically converted to PDF before printing
4. **Wait** - Files print automatically with your configured settings
5. **Done** - Printed files moved to `print_jobs/PRINTED` folder
6. **DOCX originals** moved to `print_jobs/CONVERTED` folder after conversion

That's it! No manual WiFi connection or print dialog configuration needed.

### Checking Logs

View print history and errors:

```powershell
# View latest logs
Get-Content logs\log.txt -Tail 50

# Watch logs in real-time
Get-Content logs\log.txt -Wait
```

### Stopping the Service

```powershell
net stop AutoPrintService
```

### Uninstalling the Service

```powershell
python uninstall_service.py
```

---

## Configuration

The service uses `config/config.json` for all settings. A documented template is provided at `config/config.json.template`.

### Quick Setup

```powershell
# Copy template and edit with your details
copy config\config.json.template config\config.json
notepad config\config.json
```

### Configuration Sections

Edit `config/config.json` to customize behavior:

### Printer Settings

```json
"printer": {
  "wifi_ssid": "DIRECT-xx-Brother MFC-L2750DW",
  "wifi_password": "12345678",
  "name": "Brother MFC-L2750DW",
  "discovery_timeout": 30,
  "connection_timeout": 60
}
```

### Print Settings

```json
"print_settings": {
  "duplex": true,              // Print on both sides
  "duplex_mode": "DuplexVertical",  // Flip on long edge
  "toner_save": true,          // Enable toner save mode
  "color": false,              // Black and white only
  "copies": 1,
  "paper_size": "A4"           // A4 or Letter
}
```

### Per-Document Settings (Optional)

Create `print_jobs/config.json` to override settings for specific documents:

```json
[
  {
    "doc": "invoice.pdf",
    "print_settings": {
      "duplex": false,
      "copies": 2
    }
  },
  {
    "doc": "presentation.pdf", 
    "print_settings": {
      "copies": 3,
      "toner_save": false
    }
  }
]
```

**Features:**
- Override any default setting for specific files
- Only specify settings you want to change
- File is automatically reloaded when modified
- Example file: `print_jobs/config.json.example`

### Behavior Settings

```json
"behavior": {
  "job_timeout_minutes": 10,        // Max time per print job
  "max_retries": 3,                 // Retry failed jobs 3 times
  "check_interval_seconds": 5,      // How often to check for new jobs
  "convert_docx_to_pdf": true,      // Auto-convert DOCX files
  "allowed_extensions": [".pdf", ".docx"]
}
```

### Network Settings

```json
"network": {
  "maintain_internet": true,
  "wifi_check_interval_seconds": 30,
  "reconnect_attempts": 5
}
```

---

## Troubleshooting

### Service Won't Start

1. **Check logs**: `logs\log.txt`
2. **Verify Python**: `python --version` (should be 3.11+)
3. **Check dependencies**: `pip install -r requirements.txt`
4. **Run as admin**: Service installation requires administrator privileges

### Printer Not Found

1. **Verify printer is on** and WiFi Direct is enabled
2. **Check SSID** in config matches printer's WiFi Direct SSID
3. **Install drivers**: Brother MFC-L2750DW drivers must be installed
4. **Manual test**: Try connecting to printer WiFi manually first

### WiFi Disconnects

1. **Check Ethernet**: Ensure internet comes from Ethernet, not WiFi
2. **Windows settings**: 
   - Settings → Network & Internet → WiFi
   - Turn off "Connect automatically when in range" for other networks
3. **Network profile**: The service sets printer WiFi as "unrestricted"

### Files Not Printing

1. **Check queue**: Files should appear in logs when detected
2. **Verify file type**: Only `.pdf` and `.docx` allowed
3. **Check permissions**: Ensure service can read/write to folders
4. **Printer status**: Check printer for paper jam, out of paper, etc.

### Print Job Stuck

- Jobs automatically timeout after 10 minutes (configurable)
- Failed jobs retry up to 3 times automatically
- Check `logs\log.txt` for error details

---

## Project Structure

```
auto-print/
├── src/
│   ├── main.py                  # Service entry point
│   ├── config_manager.py        # Configuration loader
│   ├── wifi_manager.py          # WiFi connection management
│   ├── printer_manager.py       # Printer communication
│   ├── print_queue_manager.py   # Job queue and retry logic
│   ├── file_watcher.py          # File system monitoring
│   └── utils/
│       ├── logger.py            # Logging utilities
│       └── helpers.py           # Helper functions
├── config/
│   └── config.json              # User configuration
├── print_jobs/                  # Drop files here to print
│   ├── PRINTED/                 # Archived printed files
│   └── CONVERTED/               # Original DOCX files after conversion
├── logs/
│   └── log.txt                  # Application logs
├── requirements.txt             # Python dependencies
├── install_service.py           # Service installer
├── uninstall_service.py         # Service uninstaller
└── README.md                    # This file
```

---

## Log Format

Logs include:
- **Timestamp**: When event occurred
- **Level**: INFO, WARNING, ERROR
- **Message**: What happened

Example:
```
[2025-10-26 14:30:45] INFO: Service started
[2025-10-26 14:30:50] INFO: WiFi connected to DIRECT-xx-Brother
[2025-10-26 14:31:00] INFO: Connected to printer: Brother MFC-L2750DW
[2025-10-26 14:31:15] INFO: → QUEUED: report.pdf
[2025-10-26 14:31:16] INFO: ⟳ PRINTING: report.pdf
[2025-10-26 14:32:30] INFO: ✓ PRINTED: report.pdf
[2025-10-26 14:32:31] INFO: Archived: report.pdf → report_20251026_143231.pdf
```

---

## Development

### Running in Development Mode

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run service directly (not as Windows service)
python src\main.py
```

### Running Tests

```powershell
pytest tests/
```

### Adding Features

The modular architecture makes it easy to extend:
- **WiFi**: Edit `src/wifi_manager.py`
- **Printing**: Edit `src/printer_manager.py`
- **Queue Logic**: Edit `src/print_queue_manager.py`
- **File Handling**: Edit `src/file_watcher.py`

---

## Security Notes

- Printer WiFi password stored in `config/config.json` (not encrypted)
- Service runs with user privileges (not SYSTEM)
- No external network access required
- Consider excluding `config/config.json` from version control (use `.gitignore`)

---

## Future Enhancements

Possible future features:
- Web interface for monitoring
- Email/mobile notifications
- Multiple printer support
- Scheduled printing
- Color printing support
- Custom print profiles per document

---

## Support

For issues or questions:
1. Check `logs/log.txt` for error details
2. Review this README's Troubleshooting section
3. Verify configuration in `config/config.json`
4. Test printer connectivity manually

---

## License

This project is provided as-is for personal use.

---

## Acknowledgments

Built with:
- [PyWin32](https://github.com/mhammond/pywin32) - Windows API access
- [Watchdog](https://github.com/gorakhargosh/watchdog) - File system monitoring
- [PyPDF2](https://github.com/py-pdf/PyPDF2) - PDF processing
- [docx2pdf](https://github.com/AlJohri/docx2pdf) - DOCX conversion

---

**Version**: 1.0.0  
**Last Updated**: October 26, 2025
