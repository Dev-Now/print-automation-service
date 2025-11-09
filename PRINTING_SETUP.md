# Printing Setup Guide

The auto-print service uses **Ghostscript** or **SumatraPDF** for reliable duplex printing with full control over print settings **without changing system-wide printer defaults**.

## Critical Requirement

⚠️ **The printing tools MUST be in your system PATH**. The service does not use hardcoded installation paths - this allows you to install the tools wherever you prefer.

## How It Works

The service tries printing methods in order until one succeeds:

1. **Ghostscript** (RECOMMENDED) - Full control over ALL settings
2. **SumatraPDF** (ALTERNATIVE) - Lightweight, limited settings
3. **No fallback** - Job fails if neither tool is available unless `print_with_system_default_settings` is enabled in config.

## Settings Support Matrix

| Setting | Ghostscript | SumatraPDF | Notes |
|---------|-------------|------------|-------|
| `duplex` | ✅ Full | ✅ Yes | Both support duplex printing |
| `duplex_mode` | ✅ Yes | ❌ No | Vertical vs Horizontal flip |
| `copies` | ✅ Yes | ❌ No | Multiple copies |
| `paper_size` | ✅ Yes | ✅ Yes | A4, Letter, etc. |
| `color` | ✅ Yes | ❌ No | Color vs Monochrome |
| `toner_save` | ✅ Yes | ❌ No | Reduced quality/toner |

**Recommendation:** Install **Ghostscript** to guarantee all settings work correctly.

## Recommended Setup: Ghostscript

**Ghostscript** is the most reliable option - it supports ALL print settings.

### Install Ghostscript

1. Download from: https://ghostscript.com/releases/gsdnld.html
2. Choose the Windows 64-bit version (or 32-bit for older systems)
3. **Run the installer** (default location or your preferred folder)
4. **Add to PATH** (installer usually does this automatically)

### Verify Installation and PATH

```powershell
# Test if Ghostscript is in PATH
gswin64c -version

# If command not found, manually add to PATH:
# Windows Settings → System → About → Advanced system settings
# → Environment Variables → System variables → Path → Edit → New
# → Add: C:\Program Files\gs\gs10.02.1\bin (or your install location)
```

5. Restart the auto-print service after adding to PATH

## Alternative: SumatraPDF

SumatraPDF is lighter weight but supports fewer settings (only duplex and paper size).

### Install SumatraPDF

1. Download from: https://www.sumatrapdfreader.org/download-free-pdf-viewer
2. Choose the installer version
3. **Run the installer** (default location or your preferred folder)
4. **Add to PATH** if not automatically added

### Verify Installation and PATH

```powershell
# Test if SumatraPDF is in PATH
SumatraPDF -?

# If command not found, manually add to PATH:
# Add: C:\Program Files\SumatraPDF (or your install location)
```

⚠️ **Note:** SumatraPDF does NOT support copies, color mode, or toner save via command-line. You'll see warnings in logs if these settings are configured.

## Adding Tools to PATH Manually

If the installer doesn't add the tool to PATH automatically:

1. Find where you installed the tool (e.g., `C:\Program Files\gs\gs10.02.1\bin`)
2. Open: **Windows Settings** → **System** → **About**
3. Click: **Advanced system settings**
4. Click: **Environment Variables**
5. Under **System variables**, find and select **Path**, then click **Edit**
6. Click **New** and paste the installation directory path
7. Click **OK** on all dialogs
8. **Restart PowerShell/Command Prompt** (and the service)

## Verify Duplex is Working

1. **Check the logs** after printing:
   ```powershell
   Get-Content logs\log.txt -Tail 50
   ```
   
   Look for:
   ```
   [INFO] Printing with settings: duplex=True, duplex_mode=DuplexVertical, ...
   [INFO] Printed successfully using Ghostscript
   ```

2. **Test with a multi-page PDF:**
   - Drop a 4-page PDF into the `print_jobs` folder
   - It should print on 2 sheets (front and back)

3. **If it still prints single-sided:**
   - Verify tool is in PATH: `gswin64c -version` or `SumatraPDF -?`
   - Check logs for errors
   - Verify your printer physically supports duplex

## Troubleshooting

### "No suitable printing tool found"
**Cause:** Neither Ghostscript nor SumatraPDF found in PATH

**Solution:**
```powershell
# Check what's in your PATH
$env:PATH -split ';' | Select-String -Pattern 'gs|Sumatra'

# If empty, install and add to PATH as shown above
```

### "Ghostscript not found in PATH"
Even though installed, the executable isn't findable.

**Solution:**
1. Find the installation: `Get-ChildItem "C:\Program Files" -Recurse -Filter "gswin64c.exe"`
2. Add that directory to PATH (see instructions above)
3. Restart PowerShell and service

### Prints are still single-sided
1. Verify your Brother MFC-L2750DW has duplex unit installed (check printer specs)
2. Check config: `"duplex": true` in `config/config.json`
3. Test manually with Ghostscript:
   ```powershell
   gswin64c -dNOPAUSE -dBATCH -sDEVICE=mswinpr2 `
     -sOutputFile="%printer%Brother MFC-L2750DW series" `
     -dDuplex=true -dTumble=false `
     test.pdf
   ```

### "SumatraPDF does not support copies via command-line"
This is expected. SumatraPDF has limited command-line options.

**Solution:** Install Ghostscript for full settings support.

### Tool installed but service says "not found"
**Cause:** Service started before PATH was updated

**Solution:**
```powershell
# Restart the service to pick up new PATH
Restart-Service AutoPrintService

# Or if running manually, restart the script
```

## Troubleshooting

### "All printing methods failed"
Install either Ghostscript or SumatraPDF as shown above.

### Prints are still single-sided
1. Verify your printer model has a duplex unit installed
2. Check Windows printer preferences to ensure duplex is enabled
3. Test manually with Ghostscript:
   ```powershell
   gswin64c -dNOPAUSE -dBATCH -sDEVICE=mswinpr2 `
     -sOutputFile="%printer%Brother MFC-L2750DW" `
     -dDuplex=true -dTumble=false `
     test.pdf
   ```

### Using Adobe Reader
Adobe Reader's command-line interface is limited and will use the printer's default duplex setting. To ensure duplex works with Adobe:
1. Open Windows Settings → Devices → Printers & scanners
2. Select your Brother printer → Manage → Printing preferences
3. Set duplex as the default
4. Apply and save

## Configuration

Your current config (`config/config.json`):
```json
"print_settings": {
  "duplex": true,                    // Enable two-sided printing
  "duplex_mode": "DuplexVertical",   // Long edge flip (most common)
  "toner_save": true,                // Reduce print quality to save toner
  "color": false,                    // Monochrome (black & white)
  "copies": 1,                       // Number of copies
  "paper_size": "A4"                 // Paper size
}
```

**Duplex modes:**
- `DuplexVertical` - Long edge binding (flip on long side) - **DEFAULT for documents**
- `DuplexHorizontal` - Short edge binding (flip on short side) - For landscape booklets

## Which Method is Best?

| Feature | Ghostscript | SumatraPDF |
|---------|-------------|------------|
| **Duplex** | ✅ Full control | ✅ Basic |
| **Duplex Mode** | ✅ Vertical/Horizontal | ❌ No control |
| **Copies** | ✅ Yes | ❌ No |
| **Paper Size** | ✅ Yes | ✅ Yes |
| **Color/Mono** | ✅ Yes | ❌ No |
| **Toner Save** | ✅ Yes | ❌ No |
| **Speed** | Fast | Very Fast |
| **Size** | ~80 MB | ~15 MB |
| **Recommendation** | ⭐ **INSTALL THIS** | Backup option |

## Quick Installation Commands

### Ghostscript (Recommended)
```powershell
# 1. Download installer
Start-Process "https://ghostscript.com/releases/gsdnld.html"

# 2. After installation, verify:
gswin64c -version

# 3. If not found, add to PATH manually (see above section)
```

### SumatraPDF (Alternative)
```powershell
# 1. Download installer
Start-Process "https://www.sumatrapdfreader.org/download-free-pdf-viewer"

# 2. After installation, verify:
SumatraPDF -?

# 3. If not found, add to PATH manually (see above section)
```
