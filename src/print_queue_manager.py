"""
Print Queue Manager
Manages print job queue, retries, and file archival
"""

import time
import json
from pathlib import Path
from datetime import datetime
from collections import deque
from utils.helpers import generate_archive_filename, safe_move_file
from utils.logger import log_print_job


class PrintJob:
    """Represents a print job"""
    
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filename = self.filepath.name
        self.status = 'QUEUED'
        self.attempts = 0
        self.max_attempts = 3
        self.queued_time = datetime.now()
        self.start_time = None
        self.error = None
        self.custom_settings = None  # Per-document print settings
    
    def __repr__(self):
        return f"PrintJob({self.filename}, attempts={self.attempts}, status={self.status})"


class PrintQueueManager:
    """Manages the print job queue"""
    
    def __init__(self, config, logger, printer_manager, conversion_manager):
        self.config = config
        self.logger = logger
        self.printer = printer_manager
        self.converter = conversion_manager
        self.queue = deque()
        self.current_job = None
        
        # Configuration
        self.max_retries = config.get_behavior().get('max_retries', 3)
        self.job_timeout_minutes = config.get_behavior().get('job_timeout_minutes', 10)
        self.paths = config.get_paths()
        self.allowed_extensions = config.get_behavior().get('allowed_extensions', ['.pdf', '.docx'])
        
        # Get absolute paths
        project_root = Path(__file__).parent.parent
        self.archive_path = project_root / self.paths.get('archive')
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # Path to per-document config file
        self.print_jobs_path = project_root / self.paths.get('print_jobs')
        self.doc_config_path = self.print_jobs_path / 'config.json'
        
        # Cache for document-specific settings
        self._doc_settings_cache = None
        self._doc_settings_mtime = 0
        
        # Discover and queue existing files
        self._discover_existing_files()
    
    def _discover_existing_files(self):
        """Discover and queue existing PDF/DOCX files in print_jobs directory"""
        try:
            if not self.print_jobs_path.exists():
                self.logger.warning(f"Print jobs directory does not exist: {self.print_jobs_path}")
                return
            
            # Find all files with allowed extensions
            existing_files = []
            for ext in self.allowed_extensions:
                existing_files.extend(self.print_jobs_path.glob(f"*{ext}"))
            
            if existing_files:
                self.logger.info(f"Discovered {len(existing_files)} existing file(s) in print_jobs directory")
                for filepath in sorted(existing_files):  # Sort for consistent ordering
                    if filepath.is_file():
                        self._process_discovered_file(filepath)
            else:
                self.logger.info("No existing files found in print_jobs directory")
                
        except Exception as e:
            self.logger.error(f"Error discovering existing files: {e}")
    
    def _process_discovered_file(self, filepath):
        """Process a discovered file - handle DOCX conversion or queue PDF directly"""
        try:
            # Handle DOCX files
            if filepath.suffix.lower() == '.docx':
                if self.converter.is_conversion_enabled():
                    self.logger.info(f"Converting discovered DOCX file: {filepath.name}")
                    pdf_path = self.converter.convert_docx_to_pdf(filepath)
                    
                    if pdf_path:
                        self.logger.info(f"Converted {filepath.name} to {pdf_path.name}")
                        self.add_job(pdf_path)
                        
                        # Handle original DOCX file
                        self.converter.handle_original_docx(filepath)
                    else:
                        self.logger.error(f"Failed to convert {filepath.name}, skipping")
                else:
                    self.logger.warning(f"DOCX conversion disabled, skipping: {filepath.name}")
            else:
                # PDF file
                self.logger.info(f"Queueing existing file: {filepath.name}")
                self.add_job(filepath)
                
        except Exception as e:
            self.logger.error(f"Error processing discovered file {filepath.name}: {e}")
    
    def add_job(self, filepath):
        """Add a new print job to the queue"""
        job = PrintJob(filepath)
        job.max_attempts = self.max_retries
        
        # Load per-document settings if available
        job.custom_settings = self._get_document_settings(job.filename)
        if job.custom_settings:
            self.logger.info(f"Loaded custom settings for {job.filename}: {job.custom_settings}")
        
        self.queue.append(job)
        log_print_job(self.logger, job.filename, 'QUEUED')
        self.logger.info(f"Queue size: {len(self.queue)}")
    
    def _get_document_settings(self, filename):
        """Get custom print settings for a specific document"""
        try:
            # Check if config file exists
            if not self.doc_config_path.exists():
                return None
            
            # Check if we need to reload the config (file modified)
            current_mtime = self.doc_config_path.stat().st_mtime
            if current_mtime != self._doc_settings_mtime:
                self._load_document_settings()
                self._doc_settings_mtime = current_mtime
            
            # Find settings for this document
            if self._doc_settings_cache:
                for doc_config in self._doc_settings_cache:
                    if doc_config.get('doc') == filename:
                        return doc_config.get('print_settings', {})
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error loading document settings: {e}")
            return None
    
    def _load_document_settings(self):
        """Load document-specific settings from config file"""
        try:
            with open(self.doc_config_path, 'r', encoding='utf-8') as f:
                self._doc_settings_cache = json.load(f)
            
            # Validate structure
            if not isinstance(self._doc_settings_cache, list):
                self.logger.error("Document config must be an array of objects")
                self._doc_settings_cache = None
                return
            
            # Log loaded configs
            doc_count = len(self._doc_settings_cache)
            if doc_count > 0:
                docs = [cfg.get('doc', 'unnamed') for cfg in self._doc_settings_cache]
                self.logger.info(f"Loaded settings for {doc_count} documents: {docs}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in document config: {e}")
            self._doc_settings_cache = None
        except Exception as e:
            self.logger.error(f"Error reading document config: {e}")
            self._doc_settings_cache = None
    
    def process_queue(self):
        """Process the next job in the queue"""
        # Check if currently printing
        if self.current_job:
            if self._is_job_timeout():
                self.logger.warning(f"Job timeout: {self.current_job.filename}")
                self._handle_job_failure("Print job timeout")
                return
            else:
                # Still printing, wait
                return
        
        # Get next job from queue
        if not self.queue:
            return  # Queue is empty
        
        job = self.queue.popleft()
        self.current_job = job
        
        # Attempt to print
        self._print_job(job)
    
    def _print_job(self, job):
        """Attempt to print a job"""
        try:
            job.attempts += 1
            job.start_time = datetime.now()
            job.status = 'PRINTING'
            
            log_print_job(
                self.logger,
                job.filename,
                'PRINTING' if job.attempts == 1 else 'RETRYING',
                attempt=job.attempts,
                max_attempts=job.max_attempts
            )
            
            # Send to printer with custom settings
            success = self.printer.print_file(job.filepath, job.custom_settings)
            
            if success:
                # Monitor job completion with printer status polling
                completion_result = self._monitor_job_completion(job)
                if completion_result == "SUCCESS":
                    self._handle_job_success(job)
                elif completion_result == "TIMEOUT":
                    self._handle_job_failure("Print job timeout - printer did not complete job within time limit")
                else:  # ERROR
                    self._handle_job_failure(f"Printer error during printing: {completion_result}")
            else:
                self._handle_job_failure("Failed to submit print job")
                
        except Exception as e:
            self.logger.error(f"Error printing job: {e}", exc_info=True)
            self._handle_job_failure(str(e))
    
    def _monitor_job_completion(self, job):
        """
        Monitor printer status until job completes, fails, or times out
        
        Returns:
            "SUCCESS" - Job completed successfully
            "TIMEOUT" - Job timed out (10 minutes)
            "ERROR_TYPE" - Specific printer error (e.g., "Paper Jam", "Out of Paper")
        """
        self.logger.info(f"Monitoring print job completion: {job.filename}")
        
        start_time = datetime.now()
        timeout_seconds = self.job_timeout_minutes * 60
        check_interval = self.config.get_behavior().get('job_monitor_interval_seconds', 5)
        
        # Initial wait to let the job start processing
        time.sleep(3)
        
        while True:
            try:
                # Check if we've exceeded the timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    self.logger.warning(f"Job monitoring timeout after {self.job_timeout_minutes} minutes")
                    return "TIMEOUT"
                
                # Get current printer status
                status = self.printer.get_printer_status()
                self.logger.debug(f"Printer status: {status} (elapsed: {elapsed:.1f}s)")
                
                # Check for immediate error conditions
                error_statuses = [
                    "Paper Jam", "Paper Out", "Paper Problem", 
                    "Offline", "Error", "Manual Feed Required"
                ]
                
                if status in error_statuses:
                    self.logger.error(f"Printer error detected: {status}")
                    return status
                
                # Check if printer is ready (potentially job completed)
                if status == "Ready":
                    # Additional check: see if there are any jobs in the printer queue
                    if self._printer_queue_empty():
                        self.logger.info(f"Job completed successfully after {elapsed:.1f}s")
                        return "SUCCESS"
                    else:
                        self.logger.debug("Printer ready but jobs still in queue")
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring job completion: {e}")
                # Continue monitoring despite errors, but log them
                time.sleep(check_interval)
    
    def _printer_queue_empty(self):
        """Check if printer queue is empty (no pending jobs)"""
        try:
            # Get print jobs for this printer
            jobs = self.printer.get_print_queue_jobs()
            return len(jobs) == 0
        except Exception as e:
            self.logger.debug(f"Could not check printer queue: {e}")
            # If we can't check the queue, assume it's empty and rely on printer status
            return True
    
    def _handle_job_success(self, job):
        """Handle successful print job"""
        job.status = 'SUCCESS'
        log_print_job(self.logger, job.filename, 'SUCCESS')
        
        # Archive the file
        self._archive_file(job)
        
        # Clear current job
        self.current_job = None
    
    def _handle_job_failure(self, error_message):
        """Handle failed print job"""
        job = self.current_job
        if not job:
            return
        
        job.status = 'FAILED'
        job.error = error_message
        
        # Check if we should retry
        if job.attempts < job.max_attempts:
            log_print_job(
                self.logger,
                job.filename,
                'FAILED',
                error=error_message,
                attempt=job.attempts,
                max_attempts=job.max_attempts
            )
            # Add back to end of queue for retry
            self.queue.append(job)
            self.logger.info(f"Job will be retried: {job.filename}")
        else:
            log_print_job(
                self.logger,
                job.filename,
                'FAILED',
                error=f"{error_message} - Max retries exceeded",
                attempt=job.attempts,
                max_attempts=job.max_attempts
            )
            self.logger.error(f"Job permanently failed: {job.filename}")
        
        # Clear current job
        self.current_job = None
    
    def _is_job_timeout(self):
        """Check if current job has timed out"""
        if not self.current_job or not self.current_job.start_time:
            return False
        
        elapsed = (datetime.now() - self.current_job.start_time).total_seconds()
        timeout_seconds = self.job_timeout_minutes * 60
        
        return elapsed > timeout_seconds
    
    def _archive_file(self, job):
        """Move printed file to archive folder"""
        try:
            # Generate archive filename with timestamp
            archive_filename = generate_archive_filename(job.filename)
            archive_filepath = self.archive_path / archive_filename
            
            # Move file
            if safe_move_file(job.filepath, archive_filepath):
                self.logger.info(f"Archived: {job.filename} → {archive_filename}")
            else:
                self.logger.warning(f"Could not archive file: {job.filename}")
                
        except Exception as e:
            self.logger.error(f"Error archiving file: {e}")
    
    def get_queue_size(self):
        """Get current queue size"""
        return len(self.queue)
    
    def stop(self):
        """Stop processing queue"""
        self.logger.info("Stopping queue manager...")
        # Could save queue state here for recovery
