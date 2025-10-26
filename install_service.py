"""
Service Installation Script
Installs Auto-Print as a Windows service
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("ERROR: pywin32 is required to install as a service")
    print("Please install dependencies first: pip install -r requirements.txt")
    sys.exit(1)

from src.main import AutoPrintService


class AutoPrintWindowsService(win32serviceutil.ServiceFramework):
    """Windows Service wrapper for Auto-Print"""
    
    _svc_name_ = "AutoPrintService"
    _svc_display_name_ = "Auto-Print Service"
    _svc_description_ = "Automated Brother MFC-L2750DW printer management service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.service = None
    
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.service:
            self.service.stop()
    
    def SvcDoRun(self):
        """Run the service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.service = AutoPrintService()
            self.service.start()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service failed: {e}")


def install_service():
    """Install the Windows service"""
    try:
        print("Installing Auto-Print Service...")
        win32serviceutil.InstallService(
            AutoPrintWindowsService._svc_reg_class_,
            AutoPrintWindowsService._svc_name_,
            AutoPrintWindowsService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=AutoPrintWindowsService._svc_description_
        )
        print("✓ Service installed successfully")
        print("  Service will start automatically on system boot")
        print("\nTo start the service now, run:")
        print("  net start AutoPrintService")
        
    except Exception as e:
        print(f"✗ Failed to install service: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # No arguments, install service
        install_service()
    else:
        # Pass to service manager
        win32serviceutil.HandleCommandLine(AutoPrintWindowsService)


if __name__ == "__main__":
    main()
