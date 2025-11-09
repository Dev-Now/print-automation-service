# Auto-Print Service

**Automated Brother MFC-L2750DW Printer Management**

__Note__: The service should also work for other printers with minor to no changes.

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
- **Docker**: Docker Desktop for Windows (for DOCX to PDF conversion via Gotenberg)

---

## Installation

### 1. Clone or Download the Project

```powershell
cd D:\Programming
git clone <repository-url> auto-print
cd auto-print
```

### 2. Install System Dependencies

**Install Docker Desktop:**

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Start the Gotenberg container for document conversion:

```powershell
docker run -d -p 3000:3000 --name gotenberg --restart unless-stopped gotenberg/gotenberg:8
```

For detailed Gotenberg setup instructions, see [GOTENBERG_SETUP.md](GOTENBERG_SETUP.md).

**Install Printing Tools for Duplex Support:**

⚠️ **CRITICAL:** Tools must be in your system PATH. Install to any location you prefer.

**Option 1: Ghostscript (RECOMMENDED)** - Supports ALL print settings:
- Download: https://ghostscript.com/releases/gsdnld.html
- Install Windows 64-bit version (installer adds to PATH automatically)
- Verify: `gswin64c -version`

**Option 2: SumatraPDF** - Lightweight, limited settings (duplex + paper size only):
- Download: https://www.sumatrapdfreader.org/download-free-pdf-viewer
- Install and ensure it's added to PATH
- Verify: `SumatraPDF -?`

**Settings Support:**
- Ghostscript: ✅ duplex, duplex_mode, copies, paper_size, color, toner_save
- SumatraPDF: ✅ duplex, paper_size | ❌ copies, color, toner_save

See [PRINTING_SETUP.md](PRINTING_SETUP.md) for detailed setup, PATH configuration, and troubleshooting.

### 3. Install Python Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r Requirements.txt
```

### 4. Configure the Service

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
3. Note the SSID and password (optional)
4. Update `config/config.json` with these values

**Note:** The `config.json` file contains your WiFi password and is excluded from version control for security.

Note also that the password is optional and only added for future automatic profile creation; The service will attempt to connect without a password using the saved profile (recommended) but you first have to connect manually once and make sure the connection is remembered.

### 5. Test the Service (Optional)

Before installing as a service, test it manually:

```powershell
python src\main.py
```

- Drop a PDF or DOCX file into the `print_jobs` folder
- Check if it converts/prints automatically
- Press `Ctrl+C` to stop

**Note:** Make sure Docker Desktop is running and the Gotenberg container is started before testing DOCX conversion.

### 6. Install as Windows Service

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
- No external network access required
- Consider excluding `config/config.json` from version control (use `.gitignore`)

---

## Future Enhancements

Possible future features:
- Profile creation for automatic WiFi setup
- Multiple printer support
- Scheduled printing
- Web interface for monitoring

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
- [Gotenberg](https://gotenberg.dev/) - High-quality DOCX to PDF conversion
- [Docker](https://www.docker.com/) - Container platform for running Gotenberg

---

**Version**: 1.0.0  
**Last Updated**: November 9, 2025
