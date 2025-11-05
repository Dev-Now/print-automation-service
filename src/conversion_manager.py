"""
Conversion Manager
Handles document conversion (DOCX to PDF) using Pandoc
"""

import subprocess
from pathlib import Path
from datetime import datetime
from utils.helpers import safe_move_file


class ConversionManager:
    """Manages document conversion operations"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.pandoc_available = self._check_pandoc_available()
        
        # Get paths
        project_root = Path(__file__).parent.parent
        paths = config.get_paths()
        self.print_jobs_path = project_root / paths.get('print_jobs')
        self.converted_dir = self.print_jobs_path / 'CONVERTED'
        self.converted_dir.mkdir(exist_ok=True)
        
        # Log pandoc availability
        if self.pandoc_available:
            self.logger.info("Pandoc is available for DOCX conversion")
        else:
            self.logger.warning("Pandoc not found - DOCX conversion will not be available")
    
    def _check_pandoc_available(self):
        """Check if pandoc is installed and available"""
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def convert_docx_to_pdf(self, docx_path):
        """
        Convert DOCX file to PDF using pandoc
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Path to converted PDF file, or None if conversion failed
        """
        try:
            if not self.pandoc_available:
                self.logger.error("Pandoc not available. Please install pandoc from https://pandoc.org/installing.html")
                self.logger.error("Or install via chocolatey: choco install pandoc")
                return None
            
            # Generate PDF filename in the same directory
            pdf_path = docx_path.with_suffix('.pdf')
            
            # Check if PDF already exists
            if pdf_path.exists():
                self.logger.warning(f"PDF already exists: {pdf_path.name}, overwriting...")
            
            self.logger.info(f"Converting {docx_path.name} to PDF using pandoc...")
            
            # Try with wkhtmltopdf engine first for better formatting
            success = self._convert_with_wkhtmltopdf(docx_path, pdf_path)
            
            if not success:
                # Fallback to default engine
                success = self._convert_with_default_engine(docx_path, pdf_path)
            
            if success and pdf_path.exists() and pdf_path.stat().st_size > 0:
                self.logger.info(f"Successfully converted to {pdf_path.name}")
                return pdf_path
            else:
                self.logger.error(f"Conversion failed - PDF not created or empty")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting DOCX to PDF: {e}")
            return None
    
    def _convert_with_wkhtmltopdf(self, docx_path, pdf_path):
        """Try conversion with wkhtmltopdf engine"""
        try:
            # First try: pandoc with wkhtmltopdf and margins
            cmd = [
                'pandoc',
                str(docx_path),
                '-o', str(pdf_path),
                '--pdf-engine=wkhtmltopdf',
                '--pdf-engine-opt=--margin-top',
                '--pdf-engine-opt=20mm',
                '--pdf-engine-opt=--margin-bottom',
                '--pdf-engine-opt=20mm',
                '--pdf-engine-opt=--margin-left',
                '--pdf-engine-opt=20mm',
                '--pdf-engine-opt=--margin-right',
                '--pdf-engine-opt=20mm'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.debug("Converted with wkhtmltopdf engine (with margins)")
                return True
            
            # Second try: simpler command without margins
            self.logger.debug("Trying wkhtmltopdf without custom margins...")
            cmd_simple = [
                'pandoc',
                str(docx_path),
                '-o', str(pdf_path),
                '--pdf-engine=wkhtmltopdf'
            ]
            
            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.debug("Converted with wkhtmltopdf engine (default margins)")
                return True
            else:
                self.logger.debug(f"wkhtmltopdf failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Pandoc conversion timed out")
            return False
        except Exception as e:
            self.logger.debug(f"wkhtmltopdf conversion failed: {e}")
            return False
    
    def _convert_with_default_engine(self, docx_path, pdf_path):
        """Fallback conversion using HTML intermediate with wkhtmltopdf"""
        try:
            # Convert DOCX to HTML first (always works with pandoc alone)
            self.logger.info("Converting via HTML intermediate...")
            html_path = docx_path.with_suffix('.html')
            
            cmd_html = [
                'pandoc',
                str(docx_path),
                '-o', str(html_path),
                '--standalone'
            ]
            
            result = subprocess.run(cmd_html, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.logger.error(f"DOCX to HTML conversion failed: {result.stderr}")
                return False
            
            # Convert HTML to PDF using wkhtmltopdf directly
            self.logger.debug("Converting HTML to PDF with wkhtmltopdf...")
            cmd_pdf = [
                'wkhtmltopdf',
                '--quiet',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--margin-right', '20mm',
                str(html_path),
                str(pdf_path)
            ]
            
            result = subprocess.run(cmd_pdf, capture_output=True, text=True, timeout=30)
            
            # Clean up HTML file
            try:
                html_path.unlink()
            except:
                pass
            
            if result.returncode == 0:
                self.logger.info("Converted successfully via HTML intermediate")
                return True
            else:
                self.logger.error(f"wkhtmltopdf conversion failed: {result.stderr}")
                self.logger.error("Please ensure wkhtmltopdf is installed: choco install wkhtmltopdf")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Conversion timed out")
            # Clean up HTML file if it exists
            try:
                if html_path.exists():
                    html_path.unlink()
            except:
                pass
            return False
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            return False
    
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
        """Check if conversion is available (pandoc installed)"""
        return self.pandoc_available
