"""
File Watcher
Monitors directory for new files and adds them to print queue
"""

import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.helpers import is_allowed_file


def check_pandoc_available():
    """Check if pandoc is installed and available"""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


PANDOC_AVAILABLE = check_pandoc_available()


class PrintJobHandler(FileSystemEventHandler):
    """Handles file system events for print jobs"""
    
    def __init__(self, config, logger, queue_manager):
        super().__init__()
        self.config = config
        self.logger = logger
        self.queue = queue_manager
        self.allowed_extensions = config.get_behavior().get('allowed_extensions', ['.pdf', '.docx'])
        self.convert_docx = config.get_behavior().get('convert_docx_to_pdf', True)
    
    def on_created(self, event):
        """Handle file creation event"""
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Ignore files in PRINTED subdirectory
        if 'PRINTED' in filepath.parts:
            return
        
        # Check if file type is allowed
        if not is_allowed_file(filepath, self.allowed_extensions):
            self.logger.warning(f"Ignored unsupported file: {filepath.name}")
            return
        
        # Wait a moment to ensure file is fully written
        time.sleep(1)
        
        # Handle DOCX files
        if filepath.suffix.lower() == '.docx':
            if self.convert_docx:
                self.logger.info(f"New DOCX file detected: {filepath.name}")
                pdf_path = self._convert_docx_to_pdf(filepath)
                if pdf_path:
                    self.logger.info(f"Converted {filepath.name} to {pdf_path.name}")
                    self.queue.add_job(pdf_path)
                    # Optionally move or delete the original DOCX file
                    self._handle_original_docx(filepath)
                else:
                    self.logger.error(f"Failed to convert {filepath.name}, skipping")
            else:
                self.logger.warning(f"DOCX conversion disabled, skipping: {filepath.name}")
        else:
            # PDF file
            self.logger.info(f"New PDF file detected: {filepath.name}")
            self.queue.add_job(filepath)
    
    def _convert_docx_to_pdf(self, docx_path):
        """Convert DOCX file to PDF using pandoc"""
        try:
            if not PANDOC_AVAILABLE:
                self.logger.error("Pandoc not available. Please install pandoc from https://pandoc.org/installing.html")
                self.logger.error("Or install via chocolatey: choco install pandoc")
                return None
            
            # Generate PDF filename in the same directory
            pdf_path = docx_path.with_suffix('.pdf')
            
            # Check if PDF already exists
            if pdf_path.exists():
                self.logger.warning(f"PDF already exists: {pdf_path.name}, overwriting...")
            
            self.logger.info(f"Converting {docx_path.name} to PDF using pandoc...")
            
            # Use pandoc to convert DOCX to PDF
            # --pdf-engine=wkhtmltopdf can be used for better formatting if installed
            # For now, use default engine
            cmd = [
                'pandoc',
                str(docx_path),
                '-o', str(pdf_path),
                '--pdf-engine=wkhtmltopdf',  # Better formatting
                '--margin-top=20mm',
                '--margin-bottom=20mm', 
                '--margin-left=20mm',
                '--margin-right=20mm'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Verify the PDF was created
                    if pdf_path.exists() and pdf_path.stat().st_size > 0:
                        self.logger.info(f"Successfully converted to {pdf_path.name}")
                        return pdf_path
                    else:
                        self.logger.error(f"Pandoc conversion failed - PDF not created or empty")
                        return None
                else:
                    # If wkhtmltopdf is not available, try with default engine
                    self.logger.warning("wkhtmltopdf not available, trying with default PDF engine...")
                    cmd_fallback = [
                        'pandoc',
                        str(docx_path),
                        '-o', str(pdf_path)
                    ]
                    
                    result = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
                        self.logger.info(f"Successfully converted to {pdf_path.name} (basic formatting)")
                        return pdf_path
                    else:
                        self.logger.error(f"Pandoc conversion failed: {result.stderr}")
                        return None
                        
            except subprocess.TimeoutExpired:
                self.logger.error("Pandoc conversion timed out")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting DOCX to PDF: {e}")
            return None
    
    def _handle_original_docx(self, docx_path):
        """Handle the original DOCX file after conversion"""
        try:
            # Option 1: Move to a 'converted' subdirectory
            converted_dir = docx_path.parent / 'CONVERTED'
            converted_dir.mkdir(exist_ok=True)
            
            converted_path = converted_dir / docx_path.name
            docx_path.rename(converted_path)
            self.logger.info(f"Moved original DOCX to: {converted_path}")
            
            # Option 2: Delete the original (uncomment if preferred)
            # docx_path.unlink()
            # self.logger.info(f"Deleted original DOCX: {docx_path.name}")
            
        except Exception as e:
            self.logger.warning(f"Could not move original DOCX file: {e}")
            # Continue anyway - the important part (conversion) succeeded
    
    def on_modified(self, event):
        """Handle file modification event"""
        # We might want to handle file modifications
        # For now, ignore them
        pass


class FileWatcher:
    """Watches the print_jobs directory for new files"""
    
    def __init__(self, config, logger, queue_manager):
        self.config = config
        self.logger = logger
        self.queue = queue_manager
        
        # Get watch directory
        project_root = Path(__file__).parent.parent
        self.watch_path = project_root / config.get_paths().get('print_jobs')
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        # Set up observer
        self.event_handler = PrintJobHandler(config, logger, queue_manager)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.watch_path), recursive=False)
        
        # Start watching
        self.observer.start()
        self.logger.info(f"Watching directory: {self.watch_path}")
        
        # Scan for existing files
        self._scan_existing_files()
    
    def _scan_existing_files(self):
        """Scan for existing files in the print_jobs directory"""
        try:
            allowed_extensions = self.config.get_behavior().get('allowed_extensions', ['.pdf', '.docx'])
            convert_docx = self.config.get_behavior().get('convert_docx_to_pdf', True)
            
            for filepath in self.watch_path.iterdir():
                if filepath.is_file() and is_allowed_file(filepath, allowed_extensions):
                    self.logger.info(f"Found existing file: {filepath.name}")
                    
                    # Handle existing DOCX files
                    if filepath.suffix.lower() == '.docx' and convert_docx:
                        pdf_path = self.event_handler._convert_docx_to_pdf(filepath)
                        if pdf_path:
                            self.logger.info(f"Converted existing {filepath.name} to {pdf_path.name}")
                            self.queue.add_job(pdf_path)
                            self.event_handler._handle_original_docx(filepath)
                        else:
                            self.logger.error(f"Failed to convert existing {filepath.name}")
                    elif filepath.suffix.lower() == '.pdf':
                        # Regular PDF file
                        self.queue.add_job(filepath)
                    # If DOCX conversion is disabled, skip DOCX files
                    
        except Exception as e:
            self.logger.error(f"Error scanning existing files: {e}")
    
    def stop(self):
        """Stop watching directory"""
        self.observer.stop()
        self.observer.join()
        self.logger.info("File watcher stopped")
