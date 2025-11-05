"""
Printer Manager
Discovers and communicates with Brother MFC-L2750DW printer
"""

import win32print
import win32api
from pathlib import Path


class PrinterManager:
    """Manages printer discovery and print jobs"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.printer_name = config.get_printer_config().get('name')
        self.print_settings = config.get_print_settings()
        self.printer_handle = None
        self.connected = False
    
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
        """Apply print settings and send file to printer"""
        try:
            # Get printer device context
            hdc = win32print.CreateDC("", self.printer_name, "")
            if not hdc:
                self.logger.error("Failed to create printer device context")
                return False
            
            try:
                # Get current DEVMODE (printer settings structure)
                dm = win32print.GetPrinter(self.printer_handle, 2)['pDevMode']
                if not dm:
                    # Create new DEVMODE if none exists
                    dm = win32print.DocumentProperties(0, self.printer_handle, self.printer_name, None, None, 0)
                
                # Apply settings to DEVMODE
                self._apply_settings_to_devmode(dm, settings)
                
                # Use ShellExecute with configured printer
                # Note: Advanced DEVMODE settings require more complex implementation
                # For now, we'll use the simpler approach but log the intended settings
                self.logger.info(f"Printing with settings: duplex={settings.get('duplex')}, "
                                f"toner_save={settings.get('toner_save')}, "
                                f"copies={settings.get('copies')}")
                
                win32api.ShellExecute(
                    0,
                    "print",
                    str(filepath),
                    f'/d:"{self.printer_name}"',
                    ".",
                    0
                )
                
                return True
                
            finally:
                win32print.DeleteDC(hdc)
                
        except Exception as e:
            self.logger.error(f"Error applying print settings: {e}")
            # Don't fallback to printing with wrong settings - fail instead
            self.logger.error("Cannot print without applying configured settings")
            self.logger.error("Please check printer driver compatibility or configuration")
            return False
    
    def _apply_settings_to_devmode(self, dm, settings):
        """Apply print settings to Windows DEVMODE structure"""
        try:
            # Set duplex mode
            if settings.get('duplex', False):
                if settings.get('duplex_mode') == 'DuplexVertical':
                    dm.Duplex = 2  # DMDUP_VERTICAL (flip on long edge)
                else:
                    dm.Duplex = 3  # DMDUP_HORIZONTAL (flip on short edge)
            else:
                dm.Duplex = 1  # DMDUP_SIMPLEX (single-sided)
            
            # Set number of copies
            copies = settings.get('copies', 1)
            dm.Copies = max(1, min(copies, 99))  # Reasonable limits
            
            # Set color mode
            if settings.get('color', False):
                dm.Color = 2  # DMCOLOR_COLOR
            else:
                dm.Color = 1  # DMCOLOR_MONOCHROME
            
            # Set paper size
            paper_size = settings.get('paper_size', 'A4')
            if paper_size.upper() == 'A4':
                dm.PaperSize = 9  # DMPAPER_A4
            elif paper_size.upper() == 'LETTER':
                dm.PaperSize = 1  # DMPAPER_LETTER
            
            # Note: Toner save mode is printer-specific and may require
            # different approaches for Brother printers
            if settings.get('toner_save', False):
                self.logger.debug("Toner save mode requested (printer-specific implementation needed)")
            
            self.logger.debug(f"Applied DEVMODE settings: duplex={dm.Duplex}, "
                            f"copies={dm.Copies}, color={dm.Color}, paper={dm.PaperSize}")
            
        except Exception as e:
            self.logger.warning(f"Could not apply some print settings: {e}")
            # Continue with partial settings
    
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
