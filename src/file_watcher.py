"""
File Watcher
Monitors print_jobs directory for new files
"""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.helpers import is_allowed_file

try:
    from docx2pdf import convert
    DOCX2PDF_AVAILABLE = True
except ImportError:
    DOCX2PDF_AVAILABLE = False


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
        """Convert DOCX file to PDF"""
        try:
            if not DOCX2PDF_AVAILABLE:
                self.logger.error("docx2pdf library not available. Install with: pip install docx2pdf")
                return None
            
            # Generate PDF filename in the same directory
            pdf_path = docx_path.with_suffix('.pdf')
            
            # Check if PDF already exists
            if pdf_path.exists():
                self.logger.warning(f"PDF already exists: {pdf_path.name}, overwriting...")
            
            self.logger.info(f"Converting {docx_path.name} to PDF...")
            
            # Convert DOCX to PDF
            convert(str(docx_path), str(pdf_path))
            
            # Verify the PDF was created
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                self.logger.info(f"Successfully converted to {pdf_path.name}")
                return pdf_path
            else:
                self.logger.error(f"Conversion failed - PDF not created or empty")
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
