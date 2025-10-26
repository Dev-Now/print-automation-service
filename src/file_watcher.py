"""
File Watcher
Monitors print_jobs directory for new files
"""

import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.helpers import is_allowed_file


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
                # TODO: Convert DOCX to PDF before printing
                # For now, add to queue directly
                self.queue.add_job(filepath)
            else:
                self.logger.warning(f"DOCX conversion disabled, skipping: {filepath.name}")
        else:
            # PDF file
            self.logger.info(f"New PDF file detected: {filepath.name}")
            self.queue.add_job(filepath)
    
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
            
            for filepath in self.watch_path.iterdir():
                if filepath.is_file() and is_allowed_file(filepath, allowed_extensions):
                    self.logger.info(f"Found existing file: {filepath.name}")
                    self.queue.add_job(filepath)
                    
        except Exception as e:
            self.logger.error(f"Error scanning existing files: {e}")
    
    def stop(self):
        """Stop watching directory"""
        self.observer.stop()
        self.observer.join()
        self.logger.info("File watcher stopped")
