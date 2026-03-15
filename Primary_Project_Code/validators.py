"""
Validation utilities for System Manager CLI
"""
import os
from pathlib import Path
from typing import Optional
from .config import Config
from .exceptions import (
    PathError,
    PermissionError,
    DiskSpaceError,
    ConfigurationError
)
from .backup_manager import BackupManager


def validate_path_exists(path_str: str, path_type: str = "directory") -> Path:
    """
    Validate that a path exists and is of the correct type
    
    Args:
        path_str: Path to validate
        path_type: 'directory', 'file', or 'any'
        
    Returns:
        Path object if valid
        
    Raises:
        PathError: If path doesn't exist or is wrong type
    """
    try:
        path = Path(path_str)
        
        if not path.exists():
            raise PathError(f"Path does not exist: {path_str}\nPlease provide a valid path.")
        
        if path_type == "directory" and not path.is_dir():
            raise PathError(f"Path is not a directory: {path_str}")
        if path_type == "file" and not path.is_file():
            raise PathError(f"Path is not a file: {path_str}")
        if path_type not in {"directory", "file", "any"}:
            raise PathError(f"Unsupported path type '{path_type}' for: {path_str}")

        return path
    except PathError:
        raise
    except Exception as e:
        raise PathError(f"Invalid path: {path_str}\nError: {str(e)}")


def validate_path_readable(path: Path) -> None:
    """
    Validate that a path is readable
    
    Raises:
        PermissionError: If path is not readable
    """
    if not os.access(path, os.R_OK):
        raise PermissionError(
            f"No read permission for path: {path}\n"
            f"Please check file permissions or run with elevated privileges."
        )


def validate_path_writable(path: Path) -> None:
    """
    Validate that a path is writable
    
    Raises:
        PermissionError: If path is not writable
    """
    if not os.access(path, os.W_OK):
        raise PermissionError(
            f"No write permission for path: {path}\n"
            f"Please check file permissions or run with elevated privileges."
        )


def validate_disk_space(path: Path, required_bytes: int) -> None:
    """
    Validate that sufficient disk space is available
    
    Args:
        path: Path to check disk space for
        required_bytes: Bytes required
        
    Raises:
        DiskSpaceError: If insufficient space available
    """
    try:
        import shutil
        stat = shutil.disk_usage(path)
        
        if stat.free < required_bytes:
            available_gb = stat.free / (1024**3)
            required_gb = required_bytes / (1024**3)
            raise DiskSpaceError(
                f"Insufficient disk space at {path}\n"
                f"Required: {required_gb:.2f} GB, Available: {available_gb:.2f} GB"
            )
    except DiskSpaceError:
        raise
    except Exception as e:
        raise DiskSpaceError(f"Error checking disk space: {str(e)}")


def validate_folder_not_empty(path: Path) -> None:
    """
    Validate that a folder is not empty
    
    Raises:
        PathError: If folder is empty
    """
    if not any(path.iterdir()):
        raise PathError(f"Folder is empty: {path}\nNothing to process.")


def validate_config_email() -> None:
    """
    Validate email configuration is set
    
    Raises:
        ConfigurationError: If email config is missing
    """
    required_fields = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']
    missing = [field for field in required_fields if not getattr(Config, field)]
    
    if missing:
        raise ConfigurationError(
            f"Email configuration incomplete. Missing fields: {', '.join(missing)}\n"
            f"Set these in your .env file:\n"
            f"  EMAIL_SENDER=your_email@gmail.com\n"
            f"  EMAIL_PASSWORD=your_app_password\n"
            f"  EMAIL_RECIPIENT=recipient@gmail.com"
        )


def validate_backup_drive() -> None:
    """
    Validate backup drive is accessible
    
    Raises:
        PathError: If backup drive is not accessible
    """
    try:
        backup_drive = Path(Config.BACKUP_DRIVE)
        if not backup_drive.exists():
            raise PathError(
                f"Backup drive not found: {Config.BACKUP_DRIVE}\n"
                f"Configure BACKUP_DRIVE in .env file or ensure the drive is mounted."
            )
        validate_path_writable(backup_drive)
    except PathError:
        raise
    except Exception as e:
        raise PathError(f"Error validating backup drive: {str(e)}")


def get_folder_size(path: Path) -> int:
    """
    Calculate total size of a folder in bytes
    
    Args:
        path: Path to folder
        
    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    # Skip files we can't access
                    pass
    except Exception as e:
        raise PathError(f"Error calculating folder size: {str(e)}")
    return total
