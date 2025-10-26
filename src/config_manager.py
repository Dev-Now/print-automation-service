"""
Configuration Manager
Loads and validates configuration from config.json
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            # Default to config/config.json relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_sections = ['printer', 'print_settings', 'paths', 'behavior']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate printer config
        printer = self.config.get('printer', {})
        if not printer.get('wifi_ssid'):
            raise ValueError("Printer WiFi SSID is required")
        if not printer.get('name'):
            raise ValueError("Printer name is required")
        
        # Ensure paths exist or can be created
        self._ensure_paths()
    
    def _ensure_paths(self):
        """Create required directories if they don't exist"""
        paths = self.config.get('paths', {})
        project_root = Path(__file__).parent.parent
        
        for key, path_str in paths.items():
            path = project_root / path_str
            path.mkdir(parents=True, exist_ok=True)
    
    def get(self, section, default=None):
        """Get configuration section"""
        return self.config.get(section, default)
    
    def get_printer_config(self):
        """Get printer configuration"""
        return self.config.get('printer', {})
    
    def get_print_settings(self):
        """Get print settings"""
        return self.config.get('print_settings', {})
    
    def get_paths(self):
        """Get configured paths"""
        return self.config.get('paths', {})
    
    def get_behavior(self):
        """Get behavior settings"""
        return self.config.get('behavior', {})
    
    def get_network_config(self):
        """Get network configuration"""
        return self.config.get('network', {})
    
    def get_logging_config(self):
        """Get logging configuration"""
        return self.config.get('logging', {})
