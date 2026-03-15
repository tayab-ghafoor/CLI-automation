"""
Async Tasks Module
Contains async implementations of system operations
"""

import asyncio
from typing import Optional, Dict, Any
from .health_monitor import HealthMonitor
from .backup_manager import BackupManager
from .file_organizer import FileOrganizer
from .log_analyzer import LogAnalyzer
from .logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


async def async_health_check() -> Optional[Dict[str, Any]]:
    """
    Async version of health check
    Runs system health monitoring without blocking
    
    Returns:
        dict: Health check results with CPU, RAM, and disk info
    """
    try:
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        logger.info(f"Async health check: CPU={results.get('cpu')}%, "
                   f"RAM={results.get('memory')}%, Disk={results.get('disk')}%")
        return results
    except Exception as e:
        logger.error(f"Async health check failed: {e}")
        return None


async def async_backup(source_folder: str, compress: bool = True) -> Optional[str]:
    """
    Async version of backup operation
    Creates a backup without blocking
    
    Args:
        source_folder: Path to folder to backup
        compress: Whether to compress the backup
    
    Returns:
        str: Path to created backup or None if failed
    """
    try:
        backup_mgr = BackupManager(source_folder)
        backup_path = backup_mgr.create_backup(compress=compress)
        logger.info(f"Async backup completed: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Async backup failed: {e}")
        return None


async def async_cleanup(folder_path: str, rename: bool = True, 
                       delete_dups: bool = True) -> bool:
    """
    Async version of file cleanup
    Organizes files without blocking
    
    Args:
        folder_path: Path to folder to clean up
        rename: Whether to rename files
        delete_dups: Whether to delete duplicates
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        organizer = FileOrganizer(folder_path)
        result = organizer.organize_files(rename=rename, delete_dups=delete_dups)
        logger.info(f"Async cleanup completed: {folder_path}")
        return result
    except Exception as e:
        logger.error(f"Async cleanup failed: {e}")
        return False


async def async_log_analysis(log_path: str) -> bool:
    """
    Async version of log analysis
    Analyzes logs without blocking
    
    Args:
        log_path: Path to log file or folder
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        analyzer = LogAnalyzer()
        from pathlib import Path
        path = Path(log_path)
        
        if path.is_file():
            result = analyzer.analyze_log_file(log_path)
        else:
            result = analyzer.analyze_folder(log_path)
        
        analyzer.export_to_csv()
        logger.info(f"Async log analysis completed: {log_path}")
        return result
    except Exception as e:
        logger.error(f"Async log analysis failed: {e}")
        return False


async def run_concurrent_tasks(*tasks):
    """
    Run multiple async tasks concurrently
    
    Args:
        *tasks: Async tasks (coroutines) to run
    
    Returns:
        list: Results from all tasks
    """
    return await asyncio.gather(*tasks, return_exceptions=True)


async def run_with_timeout(coro, timeout_seconds: float):
    """
    Run a coroutine with timeout
    
    Args:
        coro: Coroutine to run
        timeout_seconds: Max seconds to wait
    
    Returns:
        Result from coroutine or None if timed out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Task timed out after {timeout_seconds} seconds")
        return None


def execute_async_task(coro):
    """
    Execute an async coroutine and return result
    Useful for calling async functions from sync code
    
    Args:
        coro: Coroutine to execute
    
    Returns:
        Result from the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context, create a new loop
            return asyncio.run(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)


# Batch async operations for efficiency

async def batch_health_checks(count: int = 3) -> list:
    """
    Run multiple health checks concurrently
    
    Args:
        count: Number of health checks to run
    
    Returns:
        list: Results from all health checks
    """
    tasks = [async_health_check() for _ in range(count)]
    return await run_concurrent_tasks(*tasks)


async def batch_backups(folders: list, compress: bool = True) -> dict:
    """
    Backup multiple folders concurrently
    
    Args:
        folders: List of folder paths to backup
        compress: Whether to compress backups
    
    Returns:
        dict: Results with folder paths and backup paths
    """
    tasks = [async_backup(folder, compress) for folder in folders]
    results = await run_concurrent_tasks(*tasks)
    return {folder: result for folder, result in zip(folders, results)}


async def batch_cleanups(folders: list) -> dict:
    """
    Clean up multiple folders concurrently
    
    Args:
        folders: List of folder paths to clean
    
    Returns:
        dict: Results with folder paths and success status
    """
    tasks = [async_cleanup(folder) for folder in folders]
    results = await run_concurrent_tasks(*tasks)
    return {folder: result for folder, result in zip(folders, results)}
