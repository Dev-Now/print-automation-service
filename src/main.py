"""
Auto-Print Service - Main Entry Point
Brother MFC-L2750DW Automated Printer Management
"""

import sys
import time
import signal
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from config_manager import ConfigManager
from wifi_manager import WiFiManager
from printer_manager import PrinterManager
from conversion_manager import ConversionManager
from print_queue_manager import PrintQueueManager
from file_watcher import FileWatcher


class AutoPrintService:
    """Main service class for automated printing"""
    
    def __init__(self):
        self.running = False
        self.logger = None
        self.config = None
        self.wifi_manager = None
        self.printer_manager = None
        self.conversion_manager = None
        self.queue_manager = None
        self.file_watcher = None
        
    def start(self):
        """Start the auto-print service"""
        print("Starting Auto-Print Service...")
        
        try:
            # Initialize logger
            self.logger = setup_logger()
            self.logger.info("=" * 60)
            self.logger.info("Auto-Print Service Starting")
            self.logger.info("=" * 60)
            
            # Load configuration
            self.config = ConfigManager()
            self.logger.info("Configuration loaded successfully")
            
            # Initialize components
            self.wifi_manager = WiFiManager(self.config, self.logger)
            self.printer_manager = PrinterManager(self.config, self.logger)
            self.conversion_manager = ConversionManager(self.config, self.logger)
            self.queue_manager = PrintQueueManager(self.config, self.logger, self.printer_manager, self.conversion_manager)
            self.file_watcher = FileWatcher(self.config, self.logger, self.queue_manager, self.conversion_manager)
            
            # Start monitoring
            self.running = True
            self.logger.info("Service initialized successfully")
            self.logger.info("Monitoring for printer and print jobs...")
            
            # Main service loop
            self.run_loop()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start service: {e}", exc_info=True)
            else:
                print(f"ERROR: Failed to start service: {e}")
            sys.exit(1)
    
    def run_loop(self):
        """Main service loop"""
        check_interval = self.config.get('network', {}).get('wifi_check_interval_seconds', 10)
        
        while self.running:
            try:
                # Check WiFi connection
                if not self.wifi_manager.is_connected():
                    self.logger.info("Printer WiFi not connected. Attempting to connect...")
                    self.wifi_manager.connect()
                
                # Check printer availability
                if self.wifi_manager.is_connected() and not self.printer_manager.is_connected():
                    self.logger.info("Discovering printer...")
                    self.printer_manager.discover_and_connect()
                
                # Process print queue
                if self.printer_manager.is_connected():
                    self.queue_manager.process_queue()
                
                # Sleep until next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(check_interval)
    
    def stop(self):
        """Stop the service gracefully"""
        self.logger.info("Stopping Auto-Print Service...")
        self.running = False
        
        if self.file_watcher:
            self.file_watcher.stop()
        
        if self.queue_manager:
            self.queue_manager.stop()
        
        self.logger.info("Service stopped successfully")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received...")
    if service:
        service.stop()
    sys.exit(0)


# Global service instance
service = None


def main():
    """Main entry point"""
    global service
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start service
    service = AutoPrintService()
    service.start()


if __name__ == "__main__":
    main()
