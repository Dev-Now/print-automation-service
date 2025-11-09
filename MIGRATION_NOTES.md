# Migration to Gotenberg - Summary

## Overview
Successfully migrated the auto-print service from Pandoc-based DOCX to PDF conversion to Gotenberg for cleaner, higher-quality PDF output.

## Changes Made

### 1. **conversion_manager.py** - Complete Rewrite
- **Removed**: Pandoc and wkhtmltopdf subprocess calls
- **Added**: HTTP-based Gotenberg API integration using `requests` library
- **Key improvements**:
  - Cleaner PDF output using LibreOffice rendering (via Gotenberg)
  - PDF/A-1a format for better compatibility
  - Better error handling with connection timeouts
  - Health check to verify Gotenberg availability
  - Same public interface maintained (backward compatible)

### 2. **Requirements.txt** - Updated Dependencies
- **Removed**: Pandoc installation references
- **Added**: Gotenberg Docker container instructions
- **Updated**: `requests` library now explicitly required for Gotenberg API calls

### 3. **Configuration Files** - New Gotenberg Section
- **config.json**: Added `gotenberg` section with URL and timeout settings
- **config.json.template**: Added documented Gotenberg configuration with helpful comments
- **Default settings**:
  - URL: `http://localhost:3000`
  - Timeout: 30 seconds

### 4. **Documentation**
- **GOTENBERG_SETUP.md** (NEW): Comprehensive guide for installing and managing Gotenberg
  - Quick start instructions
  - Docker commands
  - Troubleshooting section
  - Performance notes
  - Advanced configuration options
- **README.md**: Updated to reference Gotenberg instead of Pandoc
  - Updated requirements section
  - Replaced Pandoc installation with Docker/Gotenberg setup
  - Updated acknowledgments

## Benefits of Gotenberg

1. **Better PDF Quality**: Uses LibreOffice for conversion, providing professional-quality output
2. **Consistent Rendering**: Docker container ensures consistent behavior across environments
3. **No System Dependencies**: No need to install Pandoc, wkhtmltopdf, or other system tools
4. **Better Error Handling**: Clear HTTP responses with proper status codes
5. **Easy Management**: Simple Docker commands for start/stop/restart
6. **Resource Efficient**: Only runs when needed, minimal memory footprint

## Setup Requirements

Users now need to:
1. Install Docker Desktop for Windows
2. Run the Gotenberg container: `docker run -d -p 3000:3000 --name gotenberg --restart unless-stopped gotenberg/gotenberg:8`
3. Ensure Docker Desktop is running when using the auto-print service

## Backward Compatibility

- All existing code that uses `ConversionManager` continues to work without changes
- Same method signatures (`convert_docx_to_pdf`, `is_available`, etc.)
- Same return values and error handling patterns
- Configuration file is backward compatible (Gotenberg section is optional but recommended)

## Testing Checklist

- [ ] Verify Gotenberg container starts successfully
- [ ] Test DOCX to PDF conversion with sample documents
- [ ] Verify error handling when Gotenberg is not running
- [ ] Check log output for appropriate messages
- [ ] Test the full print workflow with DOCX files
- [ ] Verify PDFs are clean and properly formatted

## Rollback Plan (if needed)

If you need to revert to Pandoc:
1. Restore the old `conversion_manager.py` from git history
2. Install Pandoc: `choco install pandoc`
3. Remove the Gotenberg section from config files
4. Stop the Gotenberg container: `docker stop gotenberg && docker rm gotenberg`
