"""
WiFi Manager
Handles WiFi connection to Brother printer (WiFi Direct)
"""

import time
import subprocess
import re


class WiFiManager:
    """Manages WiFi connection to printer"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.printer_ssid = config.get_printer_config().get('wifi_ssid')
        self.printer_password = config.get_printer_config().get('wifi_password')
        self.connection_timeout = config.get_printer_config().get('connection_timeout', 60)
        self.connected = False
    
    def is_connected(self):
        """Check if connected to printer WiFi"""
        try:
            # Check current WiFi connection
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Check if connected to printer SSID
                if self.printer_ssid in result.stdout:
                    self.connected = True
                    return True
            
            self.connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking WiFi connection: {e}")
            self.connected = False
            return False
    
    def scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Check if printer SSID is available
                return self.printer_ssid in result.stdout
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error scanning WiFi networks: {e}")
            return False
    
    def connect(self):
        """Connect to printer WiFi"""
        try:
            self.logger.info(f"Attempting to connect to {self.printer_ssid}...")
            
            # Check if printer WiFi is available
            if not self.scan_networks():
                self.logger.warning(f"Printer WiFi '{self.printer_ssid}' not found. Is the printer on?")
                return False
            
            # Create WiFi profile if needed
            self._create_wifi_profile()
            
            # Connect to WiFi
            result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'name={self.printer_ssid}'],
                capture_output=True,
                text=True,
                timeout=self.connection_timeout
            )
            
            if result.returncode == 0:
                # Wait a moment for connection to establish
                time.sleep(3)
                
                # Verify connection
                if self.is_connected():
                    self.logger.info(f"Successfully connected to {self.printer_ssid}")
                    self._set_connection_priority()
                    return True
            
            self.logger.error(f"Failed to connect to {self.printer_ssid}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to WiFi: {e}")
            return False
    
    def _create_wifi_profile(self):
        """Create WiFi profile for printer connection"""
        # TODO: Implement WiFi profile creation with XML
        # This will create a persistent WiFi profile so Windows remembers the connection
        pass
    
    def _set_connection_priority(self):
        """Set connection priority to prevent auto-disconnect"""
        try:
            # Set network as unmetered (no internet expected)
            subprocess.run(
                ['netsh', 'wlan', 'set', 'profileparameter',
                 f'name={self.printer_ssid}', 'cost=unrestricted'],
                capture_output=True,
                timeout=10
            )
            
            self.logger.debug(f"Set connection priority for {self.printer_ssid}")
            
        except Exception as e:
            self.logger.warning(f"Could not set connection priority: {e}")
    
    def disconnect(self):
        """Disconnect from printer WiFi"""
        try:
            subprocess.run(
                ['netsh', 'wlan', 'disconnect'],
                capture_output=True,
                timeout=10
            )
            self.connected = False
            self.logger.info("Disconnected from printer WiFi")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from WiFi: {e}")
