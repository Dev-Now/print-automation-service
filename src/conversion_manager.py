"""
Conversion Manager
Handles document conversion (DOCX to PDF) using Gotenberg
"""

import requests
from pathlib import Path
from datetime import datetime
from utils.helpers import safe_move_file


class ConversionManager:
    """Manages document conversion operations using Gotenberg API"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Get Gotenberg URL from config
        self.gotenberg_url = config.get('gotenberg', {}).get('url', 'http://localhost:3000')
        self.gotenberg_timeout = config.get('gotenberg', {}).get('timeout', 30)
        
        # Get paths
        project_root = Path(__file__).parent.parent
        paths = config.get_paths()
        self.print_jobs_path = project_root / paths.get('print_jobs')
        self.converted_dir = self.print_jobs_path / 'CONVERTED'
        self.converted_dir.mkdir(exist_ok=True)
        
        # Check Gotenberg availability
        self.gotenberg_available = self._check_gotenberg_available()
        
        # Log Gotenberg availability
        if self.gotenberg_available:
            self.logger.info(f"Gotenberg is available at {self.gotenberg_url}")
        else:
            self.logger.warning(f"Gotenberg not available at {self.gotenberg_url} - DOCX conversion will not be available")
            self.logger.warning("Please ensure Gotenberg Docker container is running:")
            self.logger.warning("  docker run -d -p 3000:3000 gotenberg/gotenberg:8")
    
    def _check_gotenberg_available(self):
        """Check if Gotenberg service is available"""
        try:
            response = requests.get(f"{self.gotenberg_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Gotenberg health check failed: {e}")
            return False
    
    def convert_docx_to_pdf(self, docx_path):
        """
        Convert DOCX file to PDF using Gotenberg API
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Path to converted PDF file, or None if conversion failed
        """
        try:
            if not self.gotenberg_available:
                self.logger.error("Gotenberg service not available")
                self.logger.error("Please ensure Gotenberg is running:")
                self.logger.error("  docker run -d -p 3000:3000 gotenberg/gotenberg:8")
                return None
            
            # Generate PDF filename in the same directory
            pdf_path = docx_path.with_suffix('.pdf')
            
            # Check if PDF already exists
            if pdf_path.exists():
                self.logger.warning(f"PDF already exists: {pdf_path.name}, overwriting...")
            
            self.logger.info(f"Converting {docx_path.name} to PDF using Gotenberg...")
            
            # Prepare the file for upload
            with open(docx_path, 'rb') as f:
                files = {
                    'files': (docx_path.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                }
                
                # Set PDF conversion options
                data = {
                    'pdfFormat': 'PDF/A-1a',  # Use PDF/A format for better compatibility
                    'landscape': 'false',
                }
                
                # Call Gotenberg API
                endpoint = f"{self.gotenberg_url}/forms/libreoffice/convert"
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=self.gotenberg_timeout
                )
            
            # Check response
            if response.status_code == 200:
                # Save the PDF
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    self.logger.info(f"Successfully converted to {pdf_path.name}")
                    return pdf_path
                else:
                    self.logger.error("Conversion failed - PDF not created or empty")
                    return None
            else:
                self.logger.error(f"Gotenberg conversion failed with status {response.status_code}")
                self.logger.error(f"Response: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Conversion timed out after {self.gotenberg_timeout} seconds")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("Could not connect to Gotenberg service")
            self.logger.error("Please ensure Gotenberg is running:")
            self.logger.error("  docker run -d -p 3000:3000 gotenberg/gotenberg:8")
            return None
        except Exception as e:
            self.logger.error(f"Error converting DOCX to PDF: {e}")
            return None

    
    def handle_original_docx(self, docx_path):
        """
        Move original DOCX file to CONVERTED subdirectory after conversion
        
        Args:
            docx_path: Path to original DOCX file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            converted_path = self.converted_dir / docx_path.name
            
            # If file already exists in CONVERTED, append timestamp
            if converted_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_parts = docx_path.stem, timestamp, docx_path.suffix
                converted_path = self.converted_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            
            if safe_move_file(docx_path, converted_path):
                self.logger.info(f"Moved original DOCX to: CONVERTED/{converted_path.name}")
                return True
            else:
                self.logger.warning(f"Could not move original DOCX: {docx_path.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling original DOCX: {e}")
            return False
    
    def is_conversion_enabled(self):
        """Check if DOCX conversion is enabled in configuration"""
        return self.config.get_behavior().get('convert_docx_to_pdf', True)
    
    def is_available(self):
        """Check if conversion is available (Gotenberg service is running)"""
        return self.gotenberg_available
