"""
Logger Utility
Sets up logging for the application
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(name='AutoPrint', log_dir='logs', level='INFO', max_size_mb=10, backup_count=5):
    """
    Set up application logger with file and console handlers
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup log files to keep
    
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    project_root = Path(__file__).parent.parent.parent
    log_path = project_root / log_dir
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / 'log.txt'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_print_job(logger, filename, status, error=None, attempt=1, max_attempts=3):
    """
    Log a print job event in a standardized format
    
    Args:
        logger: Logger instance
        filename: Name of the file being printed
        status: Status (QUEUED, PRINTING, SUCCESS, FAILED, RETRYING)
        error: Error message if failed
        attempt: Current attempt number
        max_attempts: Maximum attempts allowed
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if status == 'SUCCESS':
        logger.info(f"✓ PRINTED: {filename}")
    elif status == 'FAILED':
        if error:
            logger.error(f"✗ FAILED: {filename} - {error} (Attempt {attempt}/{max_attempts})")
        else:
            logger.error(f"✗ FAILED: {filename} (Attempt {attempt}/{max_attempts})")
    elif status == 'RETRYING':
        logger.warning(f"↻ RETRYING: {filename} (Attempt {attempt}/{max_attempts})")
    elif status == 'QUEUED':
        logger.info(f"→ QUEUED: {filename}")
    elif status == 'PRINTING':
        logger.info(f"⟳ PRINTING: {filename}")
    else:
        logger.info(f"{status}: {filename}")
