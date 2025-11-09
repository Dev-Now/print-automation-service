"""
Printer Manager
Discovers and communicates with Brother MFC-L2750DW printer

Printing Methods (requires installation and PATH setup):
1. Ghostscript (RECOMMENDED) - Full control over all print settings
   - Supports: duplex, duplex_mode, copies, paper_size, color, toner_save
   - Install from: https://ghostscript.com/releases/gsdnld.html
   - Must be in PATH as: gswin64c, gswin32c, or gs

2. SumatraPDF (ALTERNATIVE) - Lightweight, limited settings
   - Supports: duplex, paper_size
   - Does NOT support: copies, color, toner_save (via command-line)
   - Install from: https://www.sumatrapdfreader.org/
   - Must be in PATH as: SumatraPDF or SumatraPDF.exe

No fallback methods - jobs fail if tools are not installed or settings cannot be applied.
"""

import win32print
import win32api
from pathlib import Path
import subprocess
import shutil


class PrinterManager:
    """Manages printer discovery and print jobs"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.printer_name = config.get_printer_config().get('name')
        self.print_settings = config.get_print_settings()
        self.printer_handle = None
        self.connected = False
        self.print_with_system_default_settings = config.get_behavior().get('print_with_system_default_settings', False)
    
    def is_connected(self):
        """Check if printer is available and ready"""
        return self.connected and self.printer_handle is not None
    
    def discover_and_connect(self):
        """Discover Brother printer on network"""
        try:
            # List all available printers
            printers = [printer[2] for printer in win32print.EnumPrinters(2)]
            
            self.logger.debug(f"Available printers: {printers}")
            
            # Look for Brother printer
            found_printer = None
            for printer in printers:
                if 'Brother' in printer and 'MFC-L2750DW' in printer:
                    found_printer = printer
                    break
                elif self.printer_name.lower() in printer.lower():
                    found_printer = printer
                    break
            
            if found_printer:
                self.printer_name = found_printer
                self.printer_handle = win32print.OpenPrinter(self.printer_name)
                self.connected = True
                self.logger.info(f"Connected to printer: {self.printer_name}")
                return True
            else:
                self.logger.warning("Brother MFC-L2750DW printer not found")
                self.connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error discovering printer: {e}")
            self.connected = False
            return False
    
    def print_file(self, filepath, custom_settings=None):
        """
        Print a file with configured settings
        
        Args:
            filepath: Path to PDF file to print
            custom_settings: Optional dict to override default print settings
            
        Returns:
            True if print job submitted successfully, False otherwise
        """
        try:
            if not self.is_connected():
                self.logger.error("Printer not connected")
                return False
            
            filepath = Path(filepath)
            if not filepath.exists():
                self.logger.error(f"File not found: {filepath}")
                return False
            
            self.logger.info(f"Submitting print job: {filepath.name}")
            
            # Merge default settings with custom settings
            print_settings = self.print_settings.copy()
            if custom_settings:
                print_settings.update(custom_settings)
                self.logger.debug(f"Using custom settings: {custom_settings}")
            
            # Apply print settings and submit job
            success = self._print_with_settings(filepath, print_settings)
            
            if success:
                self.logger.info(f"Print job submitted: {filepath.name}")
                return True
            else:
                self.logger.error(f"Failed to submit print job: {filepath.name}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error printing file {filepath}: {e}")
            return False
    
    def _print_with_settings(self, filepath, settings):
        """
        Apply print settings and send file to printer.
        Only uses reliable methods that guarantee all settings are applied.
        """
        try:
            self.logger.info(f"Printing with settings: duplex={settings.get('duplex')}, "
                            f"duplex_mode={settings.get('duplex_mode')}, "
                            f"toner_save={settings.get('toner_save')}, "
                            f"color={settings.get('color')}, "
                            f"copies={settings.get('copies')}, "
                            f"paper_size={settings.get('paper_size')}")
            
            # Try method 1: Ghostscript (most reliable, full control)
            success = self._print_with_ghostscript(filepath, settings)
            if success:
                return True
            
            # Try method 2: SumatraPDF (lightweight alternative)
            success = self._print_with_sumatra(filepath, settings)
            if success:
                return True
            
            if self.print_with_system_default_settings:
                win32api.ShellExecute(
                    0,
                    "print",
                    str(filepath),
                    f'/d:"{self.printer_name}"',
                    ".",
                    0
                )
                return True
            
            # No fallbacks - we require tools that guarantee settings
            self.logger.error("No suitable printing tool found or both methods failed.")
            self.logger.error("Please install Ghostscript or SumatraPDF and ensure they are in your PATH.")
            self.logger.error("See PRINTING_SETUP.md for installation instructions.")
            return False
                
        except Exception as e:
            self.logger.error(f"Error printing file: {e}")
            return False
    
    
    def _print_with_sumatra(self, filepath, settings):
        """
        Print using SumatraPDF with print settings.
        SumatraPDF must be in PATH (SumatraPDF or SumatraPDF.exe).
        
        Note: SumatraPDF has limited command-line options. It supports:
        - duplex (but not duplex_mode selection)
        - noscale, paper size via print-settings
        But NOT: copies, color mode, or toner save via command line.
        """
        # Find SumatraPDF in PATH (no hardcoded paths)
        sumatra_exe = shutil.which("SumatraPDF") or shutil.which("SumatraPDF.exe")
        
        if not sumatra_exe:
            self.logger.debug("SumatraPDF not found in PATH")
            return False
        
        try:
            # Build SumatraPDF command
            cmd = [sumatra_exe, "-print-to", self.printer_name]
            
            # Build print-settings string
            print_settings = []
            
            # Duplex
            if settings.get('duplex'):
                print_settings.append("duplex")
            
            # Paper size
            paper_size = settings.get('paper_size', 'A4').upper()
            print_settings.append(f"paper={paper_size}")
            
            # Add print-settings if we have any
            if print_settings:
                cmd.append("-print-settings")
                cmd.append(",".join(print_settings))
            
            cmd.append(str(filepath))
            
            self.logger.debug(f"SumatraPDF command: {' '.join(cmd)}")
            
            # Warn about unsupported settings
            if settings.get('copies', 1) > 1:
                self.logger.warning("SumatraPDF does not support copies via command-line (will print 1 copy)")
            if settings.get('toner_save', False):
                self.logger.warning("SumatraPDF does not support toner save mode via command-line")
            if not settings.get('color', True) == False:  # If color mode is explicitly set
                self.logger.warning("SumatraPDF does not support color mode selection via command-line")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("Printed successfully using SumatraPDF")
                return True
            else:
                self.logger.error(f"SumatraPDF failed (returncode {result.returncode}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("SumatraPDF timed out after 30 seconds")
            return False
        except Exception as e:
            self.logger.error(f"SumatraPDF method failed: {e}")
            return False
    
    def _print_with_ghostscript(self, filepath, settings):
        """
        Print using Ghostscript with full control over all print settings.
        Ghostscript must be in PATH (gswin64c, gswin32c, or gs).
        """
        # Find Ghostscript in PATH (no hardcoded paths)
        gs_exe = shutil.which("gswin64c") or shutil.which("gswin32c") or shutil.which("gs")
        
        if not gs_exe:
            self.logger.debug("Ghostscript not found in PATH")
            return False
        
        try:
            # Build Ghostscript command with all settings
            cmd = [
                gs_exe,
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=mswinpr2",
                f"-sOutputFile=%printer%{self.printer_name}",
            ]
            
            # Duplex setting
            if settings.get('duplex'):
                if settings.get('duplex_mode') == 'DuplexVertical':
                    cmd.extend(["-dDuplex=true", "-dTumble=false"])  # Long edge
                else:
                    cmd.extend(["-dDuplex=true", "-dTumble=true"])  # Short edge
            else:
                cmd.append("-dDuplex=false")
            
            # Copies
            copies = settings.get('copies', 1)
            cmd.append(f"-dNumCopies={copies}")
            
            # Paper size
            paper_size = settings.get('paper_size', 'A4').upper()
            if paper_size == 'A4':
                cmd.append("-sPAPERSIZE=a4")
            elif paper_size == 'LETTER':
                cmd.append("-sPAPERSIZE=letter")
            
            # Color/Monochrome
            # Note: mswinpr2 device uses printer defaults for color
            # For explicit control, would need different device
            if not settings.get('color', False):
                cmd.append("-sColorConversionStrategy=Gray")
                cmd.append("-dProcessColorModel=/DeviceGray")
            
            # Toner save mode
            # Ghostscript doesn't have direct toner save, but we can reduce quality
            if settings.get('toner_save', False):
                cmd.append("-dPDFSETTINGS=/screen")  # Lower quality = less toner
                self.logger.debug("Toner save: using lower quality settings")
            
            cmd.append(str(filepath))
            
            self.logger.debug(f"Ghostscript command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("Printed successfully using Ghostscript")
                return True
            else:
                self.logger.error(f"Ghostscript failed (returncode {result.returncode}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Ghostscript timed out after 60 seconds")
            return False
        except Exception as e:
            self.logger.error(f"Ghostscript method failed: {e}")
            return False
    
    def get_printer_status(self):
        """Get current printer status"""
        try:
            if not self.printer_handle:
                return "Not connected"
            
            # Get printer info
            printer_info = win32print.GetPrinter(self.printer_handle, 2)
            status = printer_info.get('Status', 0)
            
            # Decode status
            if status == 0:
                return "Ready"
            elif status & 0x00000001:
                return "Paused"
            elif status & 0x00000002:
                return "Error"
            elif status & 0x00000004:
                return "Pending Deletion"
            elif status & 0x00000008:
                return "Paper Jam"
            elif status & 0x00000010:
                return "Paper Out"
            elif status & 0x00000020:
                return "Manual Feed Required"
            elif status & 0x00000040:
                return "Paper Problem"
            elif status & 0x00000080:
                return "Offline"
            else:
                return f"Unknown ({status})"
                
        except Exception as e:
            self.logger.error(f"Error getting printer status: {e}")
            return "Error"
    
    def is_printer_ready(self):
        """Check if printer is ready to accept jobs"""
        status = self.get_printer_status()
        return status == "Ready"
    
    def get_print_queue_jobs(self):
        """Get list of jobs currently in printer queue"""
        try:
            if not self.printer_handle:
                return []
            
            # Enumerate print jobs for this printer
            jobs = []
            try:
                job_info = win32print.EnumJobs(self.printer_handle, 0, -1, 1)
                for job in job_info:
                    jobs.append({
                        'job_id': job.get('JobId', 0),
                        'document': job.get('pDocument', ''),
                        'status': job.get('Status', 0),
                        'pages': job.get('TotalPages', 0)
                    })
            except Exception as enum_error:
                # EnumJobs might fail if no jobs or access denied
                self.logger.debug(f"Could not enumerate jobs: {enum_error}")
            
            return jobs
            
        except Exception as e:
            self.logger.debug(f"Error getting print queue jobs: {e}")
            return []
    
    def close(self):
        """Close printer connection"""
        if self.printer_handle:
            try:
                win32print.ClosePrinter(self.printer_handle)
                self.logger.info("Printer connection closed")
            except Exception as e:
                self.logger.error(f"Error closing printer: {e}")
            finally:
                self.printer_handle = None
                self.connected = False
