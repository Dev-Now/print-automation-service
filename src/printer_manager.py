"""
Printer Manager
Discovers and communicates with Brother MFC-L2750DW printer
"""

import win32print
import win32api
import time
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
    
    def print_file(self, filepath):
        """
        Print a file with configured settings
        
        Args:
            filepath: Path to PDF file to print
            
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
            
            # Configure print settings
            # TODO: Apply duplex, toner save, and other settings via DEVMODE
            
            # Submit print job using Windows API
            win32api.ShellExecute(
                0,
                "print",
                str(filepath),
                f'/d:"{self.printer_name}"',
                ".",
                0
            )
            
            self.logger.info(f"Print job submitted: {filepath.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error printing file {filepath}: {e}")
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
