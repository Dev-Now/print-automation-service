"""
Helper Utilities
Common helper functions used across the application
"""

import os
from pathlib import Path
from datetime import datetime


def get_timestamp():
    """Get current timestamp in standard format"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def get_file_extension(filepath):
    """Get file extension in lowercase"""
    return Path(filepath).suffix.lower()


def is_allowed_file(filepath, allowed_extensions):
    """Check if file has an allowed extension"""
    ext = get_file_extension(filepath)
    return ext in allowed_extensions


def generate_archive_filename(original_filename):
    """Generate archived filename with timestamp"""
    path = Path(original_filename)
    timestamp = get_timestamp()
    return f"{path.stem}_{timestamp}{path.suffix}"


def ensure_directory(directory):
    """Ensure directory exists, create if needed"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def safe_delete_file(filepath):
    """Safely delete a file if it exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False


def safe_move_file(source, destination):
    """Safely move a file from source to destination"""
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        source_path.rename(dest_path)
        return True
    except Exception as e:
        return False


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
