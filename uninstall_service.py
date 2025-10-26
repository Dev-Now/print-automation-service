"""
Service Uninstallation Script
Uninstalls Auto-Print Windows service
"""

import sys

try:
    import win32serviceutil
    import win32service
except ImportError:
    print("ERROR: pywin32 is required to uninstall the service")
    print("Please install dependencies first: pip install -r requirements.txt")
    sys.exit(1)


SERVICE_NAME = "AutoPrintService"


def uninstall_service():
    """Uninstall the Windows service"""
    try:
        print(f"Uninstalling {SERVICE_NAME}...")
        
        # Stop service if running
        try:
            print("Stopping service...")
            win32serviceutil.StopService(SERVICE_NAME)
            print("✓ Service stopped")
        except Exception as e:
            print(f"  Service may not be running: {e}")
        
        # Remove service
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"✓ {SERVICE_NAME} uninstalled successfully")
        
    except Exception as e:
        print(f"✗ Failed to uninstall service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    uninstall_service()
