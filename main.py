#!/usr/bin/env python3
"""
System Manager CLI Tool
A comprehensive command-line tool for system monitoring, file management, backups, and log analysis
"""

import sys
from pathlib import Path

# Add the project root to sys.path so imports work from anywhere
current = Path(__file__).parent
while current != current.parent and not (current / "Primary_Project_Code").exists():
    current = current.parent
project_root = current
sys.path.insert(0, str(project_root))

from sched import scheduler

import click
from typing import Optional, Callable, Any, cast

# make sure the standard library's "string" module is used
# (there is a conflicting string.py in the workspace root)
import importlib, sys
try:
    sys.modules['string'] = importlib.import_module('string')
except ImportError:
    pass

import schedule
import threading
import time
import asyncio
from datetime import datetime
from Primary_Project_Code.config import Config
from Primary_Project_Code.health_monitor import HealthMonitor
from Primary_Project_Code.file_organizer import FileOrganizer
from Primary_Project_Code.backup_manager import BackupManager
from Primary_Project_Code.log_analyzer import LogAnalyzer
from Primary_Project_Code.logger import get_logger
from Primary_Project_Code.auth import auth_manager
from Primary_Project_Code.scheduler import scheduler_menu
from Primary_Project_Code.email_notifier import EmailNotifier
from Primary_Project_Code.exceptions import (
    CliException,
    ConfigurationError,
    PathError,
    PermissionError,
    BackupError,
    FileOrganizationError,
    DiskSpaceError,
    LogAnalysisError,
    HealthMonitorError
)
from Primary_Project_Code.validators import (
    validate_path_exists,
    validate_path_readable,
    validate_path_writable,
    validate_disk_space,
    validate_folder_not_empty,
    validate_backup_drive,
    get_folder_size
)

logger = get_logger(__name__)

# Global user context for tracking logged-in user
current_user = {
    'email': None,
    'name': None,
    'token': None
}


def _calculate_backup_item_size(path: Path) -> int:
    """Return the size of a single backup target."""
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return get_folder_size(path)
    return 0


def _describe_backup_target(path: Path) -> str:
    """Return a human-readable target description."""
    if path.is_file():
        return "single file"
    if path.is_dir():
        return "folder"
    return "path"


def _prepare_backup_sources(sources: tuple[str, ...]) -> list[Path]:
    """Validate and normalize one or more backup source paths."""
    normalized_sources: list[Path] = []
    seen: set[Path] = set()

    for source in sources:
        source_path = validate_path_exists(source, path_type="any")
        validate_path_readable(source_path)
        resolved_source = source_path.resolve()
        if resolved_source in seen:
            continue
        seen.add(resolved_source)
        normalized_sources.append(source_path)

    if not normalized_sources:
        raise PathError("At least one file or folder path is required for backup.")

    return normalized_sources


def _coerce_backup_sources_arg(sources: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Normalize a scheduled backup sources argument into a tuple of paths."""
    if isinstance(sources, (list, tuple)):
        normalized = tuple(str(path).strip() for path in sources if str(path).strip())
    else:
        normalized = tuple(path.strip() for path in str(sources).split(',') if path.strip())

    if not normalized:
        raise PathError("At least one file or folder path is required for backup.")

    return normalized


def _run_backup_operation(
    sources: tuple[str, ...],
    backup_drive: Optional[str],
    format: str,
    list_backups: bool,
) -> None:
    """Backup one or more files/folders with automatic path detection."""
    source_paths = _prepare_backup_sources(sources)

    if backup_drive:
        backup_dest = validate_path_exists(backup_drive, path_type="directory")
        validate_path_writable(backup_dest)
    else:
        validate_backup_drive()

    if list_backups:
        for source_path in source_paths:
            backup_mgr = BackupManager(str(source_path), backup_drive)
            backup_mgr.list_backups()
        return

    total_size = sum(_calculate_backup_item_size(source_path) for source_path in source_paths)
    required_space = total_size * 1.5
    backup_path = Path(backup_drive or Config.BACKUP_DRIVE)
    validate_disk_space(backup_path, int(required_space))

    if format.lower() == 'auto':
        click.echo(f"\nSources selected: {len(source_paths)}")
        click.echo(f"Total size: {total_size / (1024**2):.2f} MB")
        click.echo("\nChoose backup format:")
        click.echo("  [1] ZIP (compressed, smaller size, need to extract to view)")
        click.echo("  [2] Folder/File copy (uncompressed, browse directly)\n")
        choice = click.prompt("Select format", type=click.Choice(['1', '2']), default='1')
        use_zip = (choice == '1')
    else:
        use_zip = (format.lower() == 'zip')

    format_name = "ZIP" if use_zip else "Folder/File copy"
    click.echo(f"\nStarting backup for {len(source_paths)} item(s) using {format_name} format")

    completed_backups = 0
    for source_path in source_paths:
        item_size = _calculate_backup_item_size(source_path)
        if source_path.is_file():
            click.echo(f"Backing up single file: {source_path}")
        elif source_path.is_dir():
            click.echo(f"Backing up folder: {source_path}")
        else:
            click.echo(f"Backing up path: {source_path}")
        click.echo(f"  Size: {item_size / (1024**2):.2f} MB")

        backup_mgr = BackupManager(str(source_path), backup_drive)
        backup_result = backup_mgr.create_backup(compress=use_zip)
        backup_mgr.display_backup_status(backup_result)

        if not backup_result:
            click.secho(f"Backup failed for: {source_path}", fg='red')
            continue

        completed_backups += 1
        logger.info(f"Backup created successfully: {backup_result}")

        if is_user_logged_in():
            user_email = current_user.get('email')
            if user_email:
                try:
                    backup_mgr.send_backup_email(user_email, backup_result, "Manual")
                except Exception as e:
                    logger.error(f"Failed to send backup email: {e}")

    if completed_backups == len(source_paths):
        click.secho("Backup completed for all selected items!", fg='green')
    elif completed_backups:
        click.secho(
            f"Backup completed for {completed_backups} of {len(source_paths)} selected items.",
            fg='yellow'
        )
    else:
        raise BackupError("Backup failed for all selected items.")


def make_click_progress_callback(label: str) -> Callable[[float, str], None]:
    """Build a simple terminal progress renderer for cloud uploads."""
    state = {'last_percent': -1}

    def _callback(percent: float, _detail: str = "") -> None:
        current = max(0, min(100, int(percent)))
        if current <= state['last_percent']:
            return
        state['last_percent'] = current
        width = 28
        filled = int((current / 100) * width)
        bar = "#" * filled + "-" * (width - filled)
        click.echo(f"\r{label} [{bar}] {current:3d}%", nl=False)
        if current >= 100:
            click.echo("")

    return _callback


def make_log_progress_callback(label: str) -> Callable[[float, str], None]:
    """Log upload progress in 10% increments to keep scheduled logs readable."""
    state = {'bucket': -1}

    def _callback(percent: float, _detail: str = "") -> None:
        bucket = int(max(0, min(100, percent)) // 10) * 10
        if bucket <= state['bucket']:
            return
        state['bucket'] = bucket
        logger.info(f"{label}: {bucket}%")

    return _callback

def is_user_logged_in() -> bool:
    """Check if a user is currently logged in"""
    return current_user['email'] is not None


def _complete_login(login_result: dict[str, str]) -> None:
    """Store login state for the current session."""
    current_user['email'] = login_result['email']
    current_user['name'] = login_result['name']
    current_user['token'] = login_result['token']


def _run_password_reset_flow(default_email: str = "") -> bool:
    """Run the forgot-password flow and return True on successful reset."""
    reset_email = click.prompt('Enter your registered email', default=default_email)
    reset_result = auth_manager.request_password_reset(reset_email)

    if not reset_result['success']:
        click.secho(reset_result['message'], fg='red')
        logger.warning(f"Password reset request failed for {reset_email}: {reset_result['message']}")
        return False

    click.secho(reset_result['message'], fg='green')
    reset_code = click.prompt('Enter code')

    while True:
        new_password = click.prompt(
            'Enter new password (min 8 chars, 1 uppercase, 1 digit)',
            hide_input=True
        )
        confirm_password = click.prompt('Confirm password', hide_input=True)

        if new_password != confirm_password:
            click.secho("Passwords don't match. Try again.", fg='red')
            continue
        break

    reset_password_result = auth_manager.reset_password_with_code(
        reset_email,
        reset_code,
        new_password,
    )

    if reset_password_result['success']:
        click.secho(reset_password_result['message'], fg='green')
        return True

    click.secho(reset_password_result['message'], fg='red')
    logger.warning(
        f"Password reset verification failed for {reset_email}: "
        f"{reset_password_result['message']}"
    )
    return False


def _prompt_login_with_reset() -> dict[str, Any]:
    """Prompt for login and offer a password reset flow on authentication failure."""
    while True:
        email = click.prompt('📧 Enter your email')
        password = click.prompt('🔐 Enter your password', hide_input=True)

        result = auth_manager.login(email, password)
        if result['success']:
            return result

        user_exists = email in auth_manager.users
        failure_message = "Incorrect password" if user_exists else result['message']
        click.secho(f"\n{failure_message}", fg='red')
        logger.warning(f"Login failed for {email}: {result['message']}")

        click.echo("\n1. Try Again")
        click.echo("2. Forgot Password\n")
        choice = click.prompt("Select option", type=click.Choice(['1', '2']), default='1')

        if choice == '1':
            continue

        _run_password_reset_flow(email)
        return {'success': False, 'message': 'Password reset flow completed'}

def require_login(func):
    """Decorator to require login for commands"""
    def wrapper(*args, **kwargs):
        if not is_user_logged_in():
            click.secho("❌ You must login first!", fg='red')
            return
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# Ensure directories exist
try:
    Config.ensure_directories()
except Exception as e:
    click.secho(f"Warning: Could not create directories: {e}", fg='yellow')
    logger.warning(f"Directory creation warning: {e}")


# ==================== SCHEDULER & ASYNC FUNCTIONALITY ====================


from Primary_Project_Code.scheduler import TaskScheduler

# global scheduler instance used throughout the CLI
task_scheduler = TaskScheduler()
# start scheduler loop as soon as CLI starts so restored tasks can run
task_scheduler.start()

# ==================== ASYNC HELPER FUNCTIONS ====================

async def async_health_check():
    """Async version of health check"""
    try:
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        logger.info(f"Async health check: CPU={results.get('cpu')}%, "
                   f"RAM={results.get('memory')}%, Disk={results.get('disk')}%")
        return results
    except Exception as e:
        logger.error(f"Async health check failed: {e}")
        return None


async def async_backup(source_folder: str):
    """Async version of backup operation"""
    try:
        backup_mgr = BackupManager(source_folder)
        backup_path = backup_mgr.create_backup(compress=True)
        logger.info(f"Async backup completed: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Async backup failed: {e}")
        return None


async def run_async_tasks(*tasks):
    """Run multiple async tasks concurrently"""
    return await asyncio.gather(*tasks)


# ==================== SYNCHRONOUS TASK WRAPPERS ====================

def scheduled_health_check(schedule_desc: str = ""):
    """Wrapper for scheduled health checks"""
    try:
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Scheduled health check - "
                   f"CPU: {results.get('cpu')}%, RAM: {results.get('memory')}%")

        # email notification for task completion
        if is_user_logged_in():
            user_email = current_user.get('email')
            if user_email:
                task_scheduler.send_task_completion_email(
                    task_id=schedule_desc or "health",
                    user_email=user_email,
                    task_description="System health check",
                    scheduled_time=schedule_desc or "",
                    execution_time=timestamp,
                    status="SUCCESS"
                )
    except Exception as e:
        logger.error(f"Scheduled health check failed: {e}")


def scheduled_backup(
    folder_path: str | list[str] | tuple[str, ...],
    schedule_desc: str = "",
    user_email: str | None = None,
    use_google_drive: bool = False,
    remote_name: str = "gdrive",
):
    """Wrapper for scheduled backup

    This wrapper will wait for internet connectivity if required, perform
    the backup, and notify the user via email even when they are not
    interactively logged in.
    """
    try:
        source_args = _coerce_backup_sources_arg(folder_path)
        source_paths = _prepare_backup_sources(source_args)
        sources_display = ", ".join(str(path) for path in source_paths)

        # helper to check internet connectivity
        import socket
        def _has_internet(timeout: float = 3.0) -> bool:
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=timeout)
                return True
            except Exception:
                return False

        # if user_email was not provided, try to use currently logged-in user
        if not user_email and is_user_logged_in():
            user_email = current_user.get('email')
        # final fallback to configured default recipient
        if not user_email:
            user_email = Config.EMAIL_RECIPIENT

        validate_backup_drive()
        total_size = sum(_calculate_backup_item_size(source_path) for source_path in source_paths)
        validate_disk_space(Path(Config.BACKUP_DRIVE), int(total_size * 1.5))

        # Wait for connectivity only when cloud upload is requested.
        if use_google_drive and not _has_internet():
            logger.warning("No internet connectivity detected for scheduled cloud backup. Waiting until connection is restored...")
            wait_start = datetime.now()
            while not _has_internet():
                time.sleep(10)
            wait_end = datetime.now()
            logger.info(f"Internet restored after {int((wait_end-wait_start).total_seconds())}s; proceeding with cloud backup")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        completed_backups = 0

        for source_path in source_paths:
            backup_mgr = BackupManager(str(source_path))
            backup_path = backup_mgr.create_backup(compress=True)
            logger.info(f"[{timestamp}] Scheduled backup completed: {backup_path}")

            if not backup_path:
                logger.error(f"Scheduled backup failed for {source_path}")
                continue

            completed_backups += 1

            if use_google_drive:
                progress_cb = make_log_progress_callback(
                    f"Scheduled cloud upload ({remote_name}) - {source_path.name}"
                )
                uploaded = backup_mgr.upload_to_rclone(
                    backup_path,
                    remote_name,
                    '/System Backups',
                    progress_callback=progress_cb
                )
                if uploaded:
                    logger.info(
                        f"Scheduled backup uploaded to Google Drive remote '{remote_name}': {backup_path}"
                    )
                else:
                    logger.error(
                        f"Scheduled backup upload to Google Drive remote '{remote_name}' failed for {backup_path}"
                    )

            if user_email:
                try:
                    backup_mgr.send_scheduled_backup_email(
                        user_email,
                        schedule_desc or "Scheduled Backup",
                        backup_path,
                        schedule_desc or ""
                    )
                except Exception as e:
                    logger.error(f"Failed to send scheduled backup email: {e}")

        # always send a generic task completion email for scheduled tasks
        if user_email:
            status = "SUCCESS" if completed_backups == len(source_paths) else "WARNING" if completed_backups else "FAILED"
            task_scheduler.send_task_completion_email(
                task_id=schedule_desc or "backup",
                user_email=user_email,
                task_description=f"Backup of {sources_display}",
                status=status
            )
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")


def scheduled_cleanup(folder_path: str, schedule_desc: str = "", user_email: str | None = None):
    """Wrapper for scheduled cleanup

    Performs the cleanup and sends a task completion email to the
    specified user_email if provided (or the logged-in user).
    """
    try:
        if not user_email and is_user_logged_in():
            user_email = current_user.get('email')

        organizer = FileOrganizer(folder_path)
        organizer.organize_files(rename=True, delete_dups=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Scheduled cleanup completed: {folder_path}")

        if user_email:
            task_scheduler.send_task_completion_email(
                task_id=schedule_desc or "cleanup",
                user_email=user_email,
                task_description=f"Cleanup of {folder_path}",
                scheduled_time=schedule_desc or "",
                execution_time=timestamp,
                status="SUCCESS"
            )
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")


def scheduled_log_analysis(log_path: str, schedule_desc: str = ""):
    """Wrapper for scheduled log analysis"""
    try:
        analyzer = LogAnalyzer()
        path = Path(log_path)
        if path.is_file():
            analyzer.analyze_log_file(log_path)
        else:
            analyzer.analyze_folder(log_path)
        analyzer.export_to_csv()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Scheduled log analysis completed")

        if is_user_logged_in():
            user_email = current_user.get('email')
            if user_email:
                task_scheduler.send_task_completion_email(
                    task_id=schedule_desc or "log_analysis",
                    user_email=user_email,
                    task_description=f"Log analysis on {log_path}",
                    scheduled_time=schedule_desc or "",
                    execution_time=timestamp,
                    status="SUCCESS"
                )
    except Exception as e:
        logger.error(f"Scheduled log analysis failed: {e}")



def handle_error(error: Exception, operation_name: str, context: Optional[str] = None) -> None:
    """
    Centralized error handling with appropriate logging and user feedback
    
    Args:
        error: The exception that occurred
        operation_name: Name of the operation that failed
        context: Additional context information
    """
    if isinstance(error, (ConfigurationError, PathError, PermissionError, DiskSpaceError)):
        click.secho(f"❌ {operation_name} failed:\n{str(error)}", fg='red')
    else:
        click.secho(f"❌ {operation_name} failed: {str(error)}", fg='red')
        if context:
            click.secho(f"   Context: {context}", fg='yellow')
    
    logger.error(f"{operation_name} failed - {type(error).__name__}: {str(error)}", exc_info=True)


@click.group()
def cli():
    """System Manager CLI - Your go-to tool for system management"""
    pass


def _offer_schedule_after_registration(email: str, password: str) -> None:
    """Optionally log in the new user and launch the scheduling wizard."""
    if not click.confirm("Do you want to login now and schedule a backup/task?", default=True):
        return

    login_result = auth_manager.login(email, password)
    if not login_result.get('success'):
        click.secho(
            "Registration succeeded, but auto-login failed. Please login and schedule manually.",
            fg='yellow'
        )
        logger.warning(
            f"Auto-login failed after registration for {email}: {login_result.get('message')}"
        )
        return

    current_user['email'] = login_result.get('email')
    current_user['name'] = login_result.get('name')
    current_user['token'] = login_result.get('token')
    click.secho(f"Logged in as {current_user['name']}", fg='green')

    from Primary_Project_Code.scheduler import interactive_schedule
    interactive_schedule(task_scheduler)


@cli.command()
def register():
    """Register a new user account"""
    click.secho("\n" + "="*50, fg='cyan')
    click.secho("📝 User Registration", fg='cyan')
    click.secho("="*50 + "\n", fg='cyan')
    
    email = click.prompt('📧 Enter your email')
    full_name = click.prompt('👤 Enter your full name (optional)', default='')
    
    while True:
        password = click.prompt('🔐 Enter password (min 8 chars, 1 uppercase, 1 digit)', hide_input=True)
        confirm_password = click.prompt('🔐 Confirm password', hide_input=True)
        
        if password != confirm_password:
            click.secho("❌ Passwords don't match. Try again.", fg='red')
            continue
        break
    
    result = auth_manager.register_user(email, password, full_name)
    
    if result['success']:
        click.secho(f"\n✅ {result['message']}", fg='green')
        click.secho(f"You can now login with: {email}\n", fg='green')
        logger.info(f"New user registered: {email}")
        _offer_schedule_after_registration(email, password)
    else:
        click.secho(f"\n❌ {result['message']}", fg='red')
        logger.warning(f"Registration failed for {email}: {result['message']}")


@cli.command()
def login():
    """Login to your account"""
    click.secho("\n" + "="*50, fg='cyan')
    click.secho("🔐 User Login", fg='cyan')
    click.secho("="*50 + "\n", fg='cyan')
    
    result = _prompt_login_with_reset()
    
    if result['success']:
        _complete_login(result)
        click.secho(f"\n✅ Welcome {result['name']}!", fg='green')
        click.secho(f"You are now logged in.\n", fg='green')
        logger.info(f"User logged in: {result['email']}")
        
        # Show menu after login
        click.pause()
        interactive_menu()


@cli.command()
def logout():
    """Logout from your account"""
    if not is_user_logged_in():
        click.secho("❌ You are not logged in.", fg='red')
        return
    
    email = current_user['email']
    if email:
        result = auth_manager.logout(email)
        
        if result['success']:
            current_user['email'] = None
            current_user['name'] = None
            current_user['token'] = None
            click.secho("✅ Logged out successfully!", fg='green')
            logger.info(f"User logged out: {email}")
        else:
            click.secho(f"❌ {result['message']}", fg='red')


@cli.command(name='reset-password')
def reset_password() -> None:
    """Reset your password using an emailed reset code."""
    click.secho("\n" + "="*50, fg='cyan')
    click.secho("Password Reset", fg='cyan')
    click.secho("="*50 + "\n", fg='cyan')
    _run_password_reset_flow()


@cli.command()
@click.option('--current', is_flag=True, help='Show current password (verify it)')
def change_password(current):
    """Change your password"""
    if not is_user_logged_in():
        click.secho("❌ You must login first!", fg='red')
        return
    
    email = current_user['email']
    if not email:
        click.secho("❌ User email not found!", fg='red')
        return
    
    if current:
        # Verify current password
        password = click.prompt('🔐 Enter your current password', hide_input=True)
        user = auth_manager.users.get(email)
        if user and not auth_manager.verify_password(password, user['password_hash']):
            click.secho("❌ Current password is incorrect.", fg='red')
            return
    
    while True:
        new_password = click.prompt('🔐 Enter new password (min 8 chars, 1 uppercase, 1 digit)', hide_input=True)
        confirm_password = click.prompt('🔐 Confirm new password', hide_input=True)
        
        if new_password != confirm_password:
            click.secho("❌ Passwords don't match. Try again.", fg='red')
            continue
        break
    
    old_password = click.prompt('🔐 Enter your current password to confirm', hide_input=True)
    result = auth_manager.change_password(email, old_password, new_password)
    
    if result['success']:
        click.secho(f"✅ {result['message']}", fg='green')
        logger.info(f"Password changed for user: {email}")
    else:
        click.secho(f"❌ {result['message']}", fg='red')


@cli.command()
def show_profile():
    """Show your profile information"""
    if not is_user_logged_in():
        click.secho("❌ You must login first!", fg='red')
        return
    
    email = current_user['email']
    user = auth_manager.users.get(email)
    
    if user:
        click.secho("\n" + "="*50, fg='cyan')
        click.secho("👤 Your Profile", fg='cyan')
        click.secho("="*50 + "\n", fg='cyan')
        click.secho(f"Email: {user['email']}")
        click.secho(f"Name: {user.get('full_name', 'N/A')}")
        click.secho(f"Created: {user.get('created_at', 'N/A')}")
        click.secho(f"Last Login: {user.get('last_login', 'Never')}\n")
        logger.info(f"Profile viewed by: {email}")
    else:
        click.secho("❌ User not found.", fg='red')


@cli.command()
@click.option('--email', is_flag=True, help='Send email alerts if issues found')
def check_health_cli(email: bool) -> None:
    """
    Check system health
    
    Monitors CPU usage, RAM usage, and disk space.
    Sends email alerts if thresholds are exceeded.
    """
    if not is_user_logged_in():
        click.secho("❌ You must login first!", fg='red')
        return
    
    try:
        if email:
            try:
                from Primary_Project_Code.validators import validate_config_email
                validate_config_email()
            except ConfigurationError as e:
                handle_error(e, "Email configuration validation")
                click.secho("⚠️  Continuing without email alerts...", fg='yellow')
                email = False
        
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        monitor.display_health(results)
        
        logger.info("System health check completed successfully")
        click.pause()
    except Exception as e:
        handle_error(e, "Health check")



@cli.command()
@click.argument('folder_path', type=click.Path(exists=True))
@click.option('--rename', is_flag=True, default=True, help='Clean and rename files')
@click.option('--delete-duplicates', is_flag=True, default=True, help='Delete duplicate files')
@click.option('--report', is_flag=True, default=True, help='Generate report file')
@click.option('--dry-run', is_flag=True, help='Preview changes without executing')
def clean_temp(folder_path: str, rename: bool, delete_duplicates: bool, report: bool, dry_run: bool) -> None:
    """
    Clean and organize a temporary folder
    
    FOLDER_PATH: Path to the folder to organize
    
    Features:
    - Organizes files by type (Images, Documents, Videos, etc.)
    - Renames files in a clean format
    - Detects and deletes duplicate files
    - Generates a report file
    """
    try:
        # Validate path
        folder = validate_path_exists(folder_path, path_type="directory")
        validate_path_readable(folder)
        validate_path_writable(folder)
        
        # Check if folder has files
        validate_folder_not_empty(folder)
        
        if dry_run:
            click.secho(f"🔍 DRY RUN MODE - No changes will be made", fg='cyan')
        
        click.echo(f"🔄 Organizing files in: {folder_path}")
        
        organizer = FileOrganizer(folder_path)
        
        if organizer.organize_files(rename=rename, delete_dups=delete_duplicates):
            organizer.display_summary()
            
            if report:
                organizer.generate_report()
            
            logger.info("File organization completed successfully")
            click.secho("✅ File organization completed!", fg='green')
        else:
            click.secho("❌ File organization failed - no files were processed", fg='red')
            logger.warning(f"File organization incomplete for: {folder_path}")
    
    except PathError as e:
        handle_error(e, "File organization", f"Path: {folder_path}")
    except PermissionError as e:
        handle_error(e, "File organization", f"Path: {folder_path}")
    except FileOrganizationError as e:
        handle_error(e, "File organization")
    except Exception as e:
        handle_error(e, "File organization", f"Path: {folder_path}")


@cli.command()
@click.argument('sources', nargs=-1, type=click.Path(exists=True))
@click.option('--backup-drive', type=click.Path(exists=True), help='Backup drive path', default=None)
@click.option('--format', type=click.Choice(['zip', 'folder', 'auto'], case_sensitive=False), default='auto', help='Backup format: zip, folder, or auto (ask)')
@click.option('--list', 'list_backups', is_flag=True, help='List existing backups')
def backup_folder(sources: tuple[str, ...], backup_drive: Optional[str], format: str, list_backups: bool) -> None:
    """
    Backup important files or folders
    
    SOURCES: One or more file/folder paths to backup
    
    Features:
    - Backup a single file, a single folder, or multiple files/folders
    - Automatically detects whether each path is a file or a folder
    - Choose between ZIP (compressed) or folder (browse-able) format
    - Keeps only the last 7 backups
    - Logs all operations
    """
    try:
        _run_backup_operation(sources, backup_drive, format, list_backups)
        return
        # Validate source (file or directory)
        source_path = validate_path_exists(source, path_type="any")
        validate_path_readable(source_path)
        
        # Validate backup drive
        if backup_drive:
            backup_dest = validate_path_exists(backup_drive, path_type="directory")
            validate_path_writable(backup_dest)
        else:
            validate_backup_drive()
        
        if list_backups:
            try:
                backup_mgr = BackupManager(source, backup_drive)
                backup_mgr.list_backups()
                return
            except Exception as e:
                handle_error(e, "List backups")
                return
        
        # Calculate required disk space
        if source_path.is_file():
            item_size = source_path.stat().st_size
            is_file = True
        else:
            item_size = get_folder_size(source_path)
            is_file = False
        
        required_space = item_size * 1.5
        backup_path = Path(backup_drive or Config.BACKUP_DRIVE)
        
        try:
            validate_disk_space(backup_path, int(required_space))
        except DiskSpaceError as e:
            handle_error(e, "Backup validation")
            return
        
        # Determine backup format
        use_zip = None
        if format.lower() == 'auto':
            click.echo(f"\n📦 Backing up: {source}")
            click.echo(f"   Size: {item_size / (1024**2):.2f} MB")
            click.echo("\n💾 Choose backup format:")
            click.echo("   [1] ZIP (compressed, smaller size, need to extract to view)")
            click.echo("   [2] Folder (uncompressed, browse files directly on Drive)\n")
            choice = click.prompt("Select format", type=click.Choice(['1', '2']), default='1')
            use_zip = (choice == '1')
        else:
            use_zip = (format.lower() == 'zip')
        
        format_name = "ZIP" if use_zip else "Folder"
        click.echo(f"\n📦 Starting backup ({format_name} format): {source}")
        click.echo(f"   Size: {item_size / (1024**2):.2f} MB")
        
        backup_mgr = BackupManager(source, backup_drive)
        backup_path = backup_mgr.create_backup(compress=use_zip)
        backup_mgr.display_backup_status(backup_path)
        
        if backup_path:
            logger.info(f"Backup created successfully: {backup_path}")
            click.secho("✅ Backup completed!", fg='green')

            # send email if user is logged in and has an email
            if is_user_logged_in():
                user_email = current_user.get('email')
                if user_email:
                    try:
                        backup_mgr.send_backup_email(user_email, backup_path, "Manual")
                    except Exception as e:
                        logger.error(f"Failed to send backup email: {e}")
        else:
            click.secho("❌ Backup failed - no backup path returned", fg='red')
    
    except PathError as e:
        handle_error(e, "Backup operation")
    except PermissionError as e:
        handle_error(e, "Backup operation")
    except DiskSpaceError as e:
        handle_error(e, "Backup operation")
    except BackupError as e:
        handle_error(e, "Backup operation")
    except Exception as e:
        handle_error(e, "Backup operation")


@cli.command()
@click.argument('backup_path', type=click.Path(exists=True))
@click.option('--remote', default='gdrive', help='Rclone remote name (gdrive, onedrive, dropbox, etc.)')
@click.option('--remote-path', default='/System Backups', help='Path on remote to upload to')
@click.option('--list-remotes', is_flag=True, help='List available Rclone remotes')
def upload_backup_cloud(backup_path: str, remote: str, remote_path: str, list_remotes: bool) -> None:
    """
    Upload a backup to cloud storage using Rclone.
    If targeting Google Drive (remote named `gdrive`), the user will be asked
    to confirm the email address to associate with the Drive upload; an
    alternate address may be entered.
    
    BACKUP_PATH: Path to the backup file or folder
    
    Features:
    - Upload to Google Drive, OneDrive, Dropbox, S3, and more
    - Requires Rclone to be installed and configured
    - Supports multiple cloud remotes
    
    Examples:
      upload-backup-cloud /path/to/backup.zip --remote gdrive
      upload-backup-cloud /path/to/backup --remote onedrive --remote-path /MyBackups
    """
    if not is_user_logged_in():
        click.secho("❌ You must login first!", fg='red')
        return
    
    try:
        # Show available remotes if requested
        if list_remotes:
            from Primary_Project_Code.rclone_manager import rclone_manager
            click.secho("\n📋 Available Rclone Remotes:", fg='cyan', bold=True)
            click.echo("-" * 50)
            remotes = rclone_manager.list_remotes()
            if remotes:
                for r in remotes:
                    click.echo(f"  • {r}")
                click.echo("-" * 50 + "\n")
            else:
                click.secho("No remotes configured. Run 'rclone config' to set up.\n", fg='yellow')
            return
        
        # Validate backup path
        backup_file = validate_path_exists(backup_path, path_type="any")
        validate_path_readable(backup_file)
        
        click.echo(f"📦 Preparing to upload backup: {backup_path}")
        click.echo(f"   Remote: {remote}")
        click.echo(f"   Remote path: {remote_path}")

        # if using Google Drive remote, confirm email to use
        chosen_email = None
        if 'gdrive' in remote.lower():
            current_email = current_user.get('email', '')
            if current_email:
                confirm = click.confirm(
                    f"Do you want to backup data on this email ({current_email})?",
                    default=True
                )
                if confirm:
                    chosen_email = current_email
                else:
                    chosen_email = click.prompt(
                        "Enter alternative email to use for Drive backup",
                        default=current_email
                    )
            else:
                # not logged in? Shouldn't happen because require login earlier
                chosen_email = click.prompt("Enter email to use for Drive backup")
            click.echo(f"Using email for Drive backup: {chosen_email}\n")
            logger.info(f"Drive backup email selected: {chosen_email}")

        backup_mgr = BackupManager(".")  # Dummy source folder
        
        click.echo(f"\n🔄 Uploading backup to '{remote}'...")
        progress_cb = make_click_progress_callback(f"Uploading to {remote}")
        success = backup_mgr.upload_to_rclone(
            backup_file,
            remote,
            remote_path,
            progress_callback=progress_cb
        )
        
        if success:
            success_msg = "✅ Backup uploaded successfully!"
            if chosen_email:
                success_msg += f" (Drive email: {chosen_email})"
            click.secho(success_msg, fg='green')
            click.secho(f"📍 Location: {remote}:{remote_path}\n", fg='green')
            logger.info(f"Backup uploaded to {remote} email={chosen_email}")
        else:
            click.secho("❌ Upload failed", fg='red')
            click.secho("💡 Make sure Rclone is installed and the remote is configured.\n", fg='yellow')
            logger.warning(f"Failed to upload backup to {remote}")
    
    except PathError as e:
        handle_error(e, "Backup upload", f"Path: {backup_path}")
    except Exception as e:
        handle_error(e, "Backup upload")


@cli.command()
@click.argument('log_source', type=click.Path(exists=True))
@click.option('--export', is_flag=True, default=True, help='Export results to CSV')
def generate_report(log_source: str, export: bool) -> None:
    """
    Generate system report from log files
    
    LOG_SOURCE: Path to log file or folder containing log files
    
    Features:
    - Reads server log files
    - Detects errors and warnings
    - Counts failed login attempts
    - Generates CSV summary report
    """
    try:
        # Validate log source exists
        log_path = validate_path_exists(log_source, path_type="any")
        validate_path_readable(log_path)
        
        click.echo(f"📊 Analyzing logs from: {log_source}")
        
        analyzer = LogAnalyzer()
        
        try:
            if log_path.is_file():
                success = analyzer.analyze_log_file(log_source)
            else:
                success = analyzer.analyze_folder(log_source)
        except Exception as e:
            raise LogAnalysisError(f"Error analyzing logs: {str(e)}")
        
        if success:
            analyzer.display_summary()
            
            if export:
                try:
                    csv_file = analyzer.export_to_csv()
                    if csv_file:
                        click.secho(f"✅ Report exported to: {csv_file}", fg='green')
                    else:
                        click.secho("⚠️  No data to export", fg='yellow')
                except Exception as e:
                    click.secho(f"⚠️  Warning: Could not export to CSV: {e}", fg='yellow')
                    logger.warning(f"CSV export failed: {e}")
            
            logger.info("Log analysis completed successfully")
            click.secho("✅ Report generation completed!", fg='green')
        else:
            click.secho("❌ No logs found in the specified path", fg='red')
            logger.warning(f"No logs found: {log_source}")
    
    except PathError as e:
        handle_error(e, "Report generation", f"Source: {log_source}")
    except PermissionError as e:
        handle_error(e, "Report generation", f"Source: {log_source}")
    except LogAnalysisError as e:
        handle_error(e, "Report generation")
    except Exception as e:
        handle_error(e, "Report generation", f"Source: {log_source}")


@cli.command()
def setup() -> None:
    """Setup the CLI tool configuration"""
    click.echo("🔧 Setting up System Manager CLI...")
    
    Config.ensure_directories()
    
    click.echo("\nDirectories created/verified:")
    click.echo(f"  • Logs: {Config.LOGS_DIR}")
    click.echo(f"  • Reports: {Config.REPORTS_DIR}")
    
    click.echo("\n⚠️  Important: Configure your email settings in .env file for alerts:")
    click.echo("  EMAIL_SENDER=your_email@gmail.com")
    click.echo("  EMAIL_PASSWORD=your_app_password")
    click.echo("  EMAIL_RECIPIENT=recipient@gmail.com")

    # scheduling guidance
    click.secho("\n🕘 Task Scheduling", fg='cyan')
    click.echo("You may schedule recurring operations using the built-in wizard.")
    click.echo("This works much like setting an alarm on your phone – pick an")
    click.echo("operation (backup, health check, cleanup, or report), specify the")
    click.echo("time it should run, and choose a recurrence (daily, weekly, monthly).")
    click.echo("To schedule a task now, answer 'yes' to the prompt below.")
    if click.confirm("Do you want to schedule a task now?", default=False):
        from Primary_Project_Code.scheduler import interactive_schedule
        interactive_schedule(task_scheduler)

    click.echo("\n✅ Setup completed!")


# ==================== SCHEDULER COMMANDS ====================

@cli.command()
@click.option('--task', type=click.Choice(['health', 'backup', 'cleanup', 'report']), 
              help='Type of task to schedule')
@click.option('--interval', type=int, default=1, help='How often to run')
@click.option('--unit', type=click.Choice(['seconds', 'minutes', 'hours', 'days', 'weeks']), 
              default='hours', help='Time unit')
@click.option('--time', 'time_str', type=str, help='Clock time for the job (HH:MM)')
@click.option('--frequency', type=click.Choice(['daily','weekly','monthly']), default='daily',
              help='High‑level frequency (used together with --time)')
@click.option('--weekday', type=click.Choice(['monday','tuesday','wednesday','thursday','friday','saturday','sunday']),
              help='Weekday when --frequency=weekly')
@click.option('--day', 'day_of_month', type=int, help='Day of month when --frequency=monthly')
@click.option('--folder', type=click.Path(exists=True), help='Folder path (for backup/cleanup)')
@click.option('--log-path', type=click.Path(exists=True), help='Log path (for report task)')
def schedule_task(task: str, interval: int, unit: str, time_str: Optional[str],
                 frequency: str, weekday: Optional[str], day_of_month: Optional[int],
                 folder: Optional[str], 
                 log_path: Optional[str]) -> None:
    """
    Schedule automated tasks to run periodically
    
    Examples:
      schedule-task --task health --interval 30 --unit minutes
      schedule-task --task backup --interval 1 --unit days --folder /path/to/folder
      schedule-task --task cleanup --interval 2 --unit hours --folder /path/to/folder
    """
    try:
        if not task:
            click.secho("❌ Error: --task is required", fg='red')
            return

        task_id = f"{task}_{int(time.time())}"

        # build descriptive schedule string for emails
        schedule_desc = f"{interval} {unit}"
        if time_str:
            schedule_desc += f" at {time_str}"
        if frequency == 'weekly' and weekday:
            schedule_desc = f"every {weekday}"
        elif frequency == 'monthly' and day_of_month:
            schedule_desc = f"day {day_of_month} of every month"

        user_email = current_user.get('email') if is_user_logged_in() else None
        if not user_email:
            user_email = Config.EMAIL_RECIPIENT

        if task == 'health':
            task_scheduler.add_task(
                task_id,
                scheduled_health_check,
                interval,
                unit,
                at_time=time_str,
                weekday=weekday if frequency == 'weekly' else None,
                day_of_month=day_of_month if frequency == 'monthly' else None,
            )
            if task_id in task_scheduler.tasks:
                task_scheduler.tasks[task_id]['action_name'] = 'scheduled_health_check'
                task_scheduler.tasks[task_id]['action_args'] = [schedule_desc]
                task_scheduler.tasks[task_id]['action_kwargs'] = {}
                if user_email:
                    task_scheduler.tasks[task_id]['user_email'] = user_email
            click.secho(f"✅ Health check scheduled: every {interval} {unit}", fg='green')

        elif task == 'backup':
            if not folder:
                click.secho("❌ Error: --folder is required for backup task", fg='red')
                return

            google_drive_choice = click.confirm(
                "Do you want to backup data on Google drive? (Y/N)",
                default=False
            )

            if time_str:
                task_scheduler.add_task(
                    task_id,
                    lambda f=folder, sd=schedule_desc, ue=user_email, gd=google_drive_choice: scheduled_backup(f, sd, ue, gd),
                    interval,
                    unit,
                    at_time=time_str,
                    weekday=weekday if frequency == 'weekly' else None,
                    day_of_month=day_of_month if frequency == 'monthly' else None,
                )
            else:
                task_scheduler.add_task(
                    task_id,
                    lambda f=folder, sd=schedule_desc, ue=user_email, gd=google_drive_choice: scheduled_backup(f, sd, ue, gd),
                    interval,
                    unit,
                )
            if task_id in task_scheduler.tasks:
                task_scheduler.tasks[task_id]['action_name'] = 'scheduled_backup'
                task_scheduler.tasks[task_id]['action_args'] = [folder, schedule_desc, user_email, google_drive_choice]
                task_scheduler.tasks[task_id]['action_kwargs'] = {}
                if user_email:
                    task_scheduler.tasks[task_id]['user_email'] = user_email
            click.secho(f"✅ Backup scheduled: {folder} every {interval} {unit}", fg='green')

        elif task == 'cleanup':
            if not folder:
                click.secho("❌ Error: --folder is required for cleanup task", fg='red')
                return
            if time_str:
                task_scheduler.add_task(
                    task_id,
                    lambda f=folder, sd=schedule_desc: scheduled_cleanup(f, sd),
                    interval,
                    unit,
                    at_time=time_str,
                    weekday=weekday if frequency == 'weekly' else None,
                    day_of_month=day_of_month if frequency == 'monthly' else None,
                )
            else:
                task_scheduler.add_task(
                    task_id,
                    lambda f=folder, sd=schedule_desc: scheduled_cleanup(f, sd),
                    interval,
                    unit,
                )
            if task_id in task_scheduler.tasks:
                task_scheduler.tasks[task_id]['action_name'] = 'scheduled_cleanup'
                task_scheduler.tasks[task_id]['action_args'] = [folder, schedule_desc, user_email]
                task_scheduler.tasks[task_id]['action_kwargs'] = {}
                if user_email:
                    task_scheduler.tasks[task_id]['user_email'] = user_email
            click.secho(f"✅ Cleanup scheduled: {folder} every {interval} {unit}", fg='green')

        elif task == 'report':
            if not log_path:
                click.secho("❌ Error: --log-path is required for report task", fg='red')
                return
            if time_str:
                task_scheduler.add_task(
                    task_id,
                    lambda lp=log_path, sd=schedule_desc: scheduled_log_analysis(lp, sd),
                    interval,
                    unit,
                    at_time=time_str,
                    weekday=weekday if frequency == 'weekly' else None,
                    day_of_month=day_of_month if frequency == 'monthly' else None,
                )
            else:
                task_scheduler.add_task(
                    task_id,
                    lambda lp=log_path, sd=schedule_desc: scheduled_log_analysis(lp, sd),
                    interval,
                    unit,
                )
            if task_id in task_scheduler.tasks:
                task_scheduler.tasks[task_id]['action_name'] = 'scheduled_log_analysis'
                task_scheduler.tasks[task_id]['action_args'] = [log_path, schedule_desc]
                task_scheduler.tasks[task_id]['action_kwargs'] = {}
                if user_email:
                    task_scheduler.tasks[task_id]['user_email'] = user_email
            click.secho(f" Log analysis scheduled: {log_path} every {interval} {unit}", fg='green')

        if task_id in task_scheduler.tasks:
            try:
                task_scheduler._save_task_metadata(task_id)
            except Exception as persist_error:
                logger.warning(f"Could not persist schedule metadata for {task_id}: {persist_error}")

        task_scheduler.start()
        logger.info(f"Task scheduled: {task_id}")

    except Exception as e:
        handle_error(e, "Task scheduling")


@cli.command()
def schedule_interactive() -> None:
    """Launch the scheduling wizard (also offered during setup).

    This command drives the same alarm‑style interactive workflow used by
    the `setup` action.  It asks which operation to schedule, when it
    should run and how often (daily/weekly/monthly), then registers the task
    with the global scheduler instance.
    """
    try:
        from Primary_Project_Code.scheduler import interactive_schedule
        interactive_schedule(task_scheduler)
    except Exception as e:
        handle_error(e, "Interactive scheduling")


@cli.command()
def start_scheduler() -> None:
    """Start the background task scheduler"""
    try:
        task_scheduler.start()
        click.secho(" Scheduler started successfully!", fg='green')
        click.secho(" Tip: Scheduler runs in background. Press Ctrl+C to continue.", fg='cyan')
        
        # Keep the scheduler running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.secho("\n  Scheduler stopped by user", fg='yellow')
    
    except Exception as e:
        handle_error(e, "Scheduler startup")


@cli.command()
def stop_scheduler() -> None:
    """Stop the background task scheduler"""
    try:
        task_scheduler.stop()
        click.secho(" Scheduler stopped successfully!", fg='green')
        logger.info("Scheduler stopped via CLI")
    
    except Exception as e:
        handle_error(e, "Scheduler shutdown")


@cli.command()
def list_tasks() -> None:
    """List all scheduled tasks"""
    try:
        tasks = task_scheduler.list_tasks()
        
        if not tasks:
            click.secho("❌ No tasks scheduled yet", fg='yellow')
            return
        
        click.secho("\n📋 Scheduled Tasks:", fg='cyan', bold=True)
        click.echo("-" * 50)
        
        for task_id, schedule_info in tasks.items():
            click.echo(f"  • {task_id}: {schedule_info}")
        
        click.echo("-" * 50)
        
        next_runs = task_scheduler.get_next_runs()
        if next_runs:
            click.secho("\n⏱️  Next Runs:", fg='cyan', bold=True)
            for run_info in next_runs:
                idle = run_info['idle_seconds']
                click.echo(f"  • Next run in: {idle:.0f} seconds")
    
    except Exception as e:
        handle_error(e, "Task listing")


@cli.command()
def remove_task() -> None:
    """Remove a scheduled task by ID"""
    try:
        tasks = task_scheduler.list_tasks()
        
        if not tasks:
            click.secho("❌ No tasks scheduled yet", fg='yellow')
            return
        
        click.secho("\n📋 Available Tasks:", fg='cyan')
        task_ids = list(tasks.keys())
        
        for i, task_id in enumerate(task_ids, 1):
            click.echo(f"  {i}. {task_id} ({tasks[task_id]})")
        
        choice = click.prompt("Select task to remove (number)", type=int)
        
        if 1 <= choice <= len(task_ids):
            task_id = task_ids[choice - 1]
            if task_scheduler.remove_task(task_id):
                click.secho(f"✅ Task removed: {task_id}", fg='green')
                logger.info(f"Task removed: {task_id}")
            else:
                click.secho(f"❌ Failed to remove task: {task_id}", fg='red')
        else:
            click.secho("❌ Invalid selection", fg='red')
    
    except Exception as e:
        handle_error(e, "Task removal")


@cli.command()
@click.option('--monitor', is_flag=True, default=False, help='Monitor task execution')
def run_async_demo(monitor: bool) -> None:
    """
    Run async demo - execute multiple tasks concurrently
    
    Demonstrates async/await capabilities for parallel operations
    """
    try:
        click.secho("🚀 Running async task demo...", fg='cyan')
        
        # Create async tasks
        health_task = async_health_check()
        
        # Run multiple health checks concurrently
        results = asyncio.run(run_async_tasks(health_task, health_task, health_task))
        
        click.secho("✅ Async demo completed!", fg='green')
        click.echo(f"\n📊 Results: Ran 3 concurrent health checks")
        
        if results[0]:
            result = results[0]
            click.echo(f"  • CPU Usage: {result.get('cpu', 'N/A')}%")
            click.echo(f"  • RAM Usage: {result.get('memory', 'N/A')}%")
            click.echo(f"  • Disk Usage: {result.get('disk', 'N/A')}%")
        
        logger.info("Async demo completed successfully")
    
    except Exception as e:
        handle_error(e, "Async demo execution")


def interactive_menu() -> None:
    """Interactive menu for users who don't want to type commands"""
    # Check if user is logged in, if not show login menu
    if not is_user_logged_in():
        while True:
            click.clear()
            click.secho("\n" + "="*50, fg='cyan')
            click.secho("   SYSTEM MANAGER CLI - Welcome", fg='cyan', bold=True)
            click.secho("="*50 + "\n", fg='cyan')
            
            click.echo("1. Login 🔐")
            click.echo("2. Register 📝")
            click.echo("3. Exit ❌\n")
            
            choice = click.prompt("Select an option", type=click.Choice(['1', '2', '3']))
            
            if choice == '1':
                click.clear()
                click.secho("\n" + "="*50, fg='cyan')
                click.secho("🔐 User Login", fg='cyan')
                click.secho("="*50 + "\n", fg='cyan')
                
                result = _prompt_login_with_reset()
                
                if result['success']:
                    _complete_login(result)
                    click.secho(f"\n✅ Welcome {result['name']}!", fg='green')
                    click.secho(f"You are now logged in.\n", fg='green')
                    logger.info(f"User logged in: {result['email']}")
                    click.pause()
                    break  # Exit login loop to show main menu
                click.pause()
            
            elif choice == '2':
                click.clear()
                click.secho("\n" + "="*50, fg='cyan')
                click.secho("📝 User Registration", fg='cyan')
                click.secho("="*50 + "\n", fg='cyan')
                
                email = click.prompt('📧 Enter your email')
                full_name = click.prompt('👤 Enter your full name (optional)', default='')
                
                while True:
                    password = click.prompt('🔐 Enter password (min 8 chars, 1 uppercase, 1 digit)', hide_input=True)
                    confirm_password = click.prompt('🔐 Confirm password', hide_input=True)
                    
                    if password != confirm_password:
                        click.secho("❌ Passwords don't match. Try again.", fg='red')
                        continue
                    break
                
                result = auth_manager.register_user(email, password, full_name)
                
                if result['success']:
                    click.secho(f"\n✅ {result['message']}", fg='green')
                    click.secho(f"You can now login with: {email}\n", fg='green')
                    logger.info(f"New user registered: {email}")
                    _offer_schedule_after_registration(email, password)
                    click.pause()
                else:
                    click.secho(f"\n❌ {result['message']}", fg='red')
                    logger.warning(f"Registration failed for {email}: {result['message']}")
                    click.pause()
            
            elif choice == '3':
                click.secho("👋 Goodbye!", fg='cyan')
                return
    
    # Main menu for logged-in users
    while True:
        click.clear()
        click.secho("\n" + "="*50, fg='cyan')
        click.secho("   SYSTEM MANAGER CLI - Interactive Menu", fg='cyan', bold=True)
        click.secho("="*50 + "\n", fg='cyan')
        click.secho(f"   Logged in as: {current_user['name']}", fg='yellow')
        click.secho("="*50 + "\n", fg='cyan')
        
        click.echo("1. Check System Health 🏥")
        click.echo("2. Clean Temporary Files 🧹")
        click.echo("3. Backup Files/Folders 💾")
        click.echo("4. Generate System Report 📊")
        click.echo("5. Scheduler Menu ⏰")
        click.echo("6. View Profile 👤")
        click.echo("7. Change Password 🔐")
        click.echo("8. Logout ❌")
        click.echo("9. Exit 🚪")
        
        choice = click.prompt("Select an option", type=click.Choice(['1', '2', '3', '4', '5', '6', '7', '8', '9']))
        
        if choice == '1':
            click.clear()
            try:
                monitor = HealthMonitor()
                results = monitor.check_system_health()
                monitor.display_health(results)
                logger.info("System health check completed")
                click.secho("✅ Health check completed!", fg='green')
            except HealthMonitorError as e:
                handle_error(e, "System health check")
            except Exception as e:
                handle_error(e, "System health check")
            click.pause()
            
        elif choice == '2':
            click.clear()
            folder_path = click.prompt("Enter folder path to clean")
            if not folder_path.strip():
                click.secho("❌ Folder path cannot be empty", fg='red')
                click.pause()
                continue
                
            try:
                folder = validate_path_exists(folder_path, path_type="directory")
                compress = click.confirm("Compress backup to ZIP?", default=True)
                validate_path_writable(folder)
                validate_folder_not_empty(folder)
                
                click.echo(f"🔄 Organizing files in: {folder_path}")
                organizer = FileOrganizer(folder_path)
                if organizer.organize_files(rename=True, delete_dups=True):
                    organizer.display_summary()
                    organizer.generate_report()
                    logger.info("File organization completed successfully")
                    click.secho("✅ File organization completed!", fg='green')
                else:
                    click.secho("❌ File organization failed - no files processed", fg='red')
            except PathError as e:
                handle_error(e, "File organization")
            except PermissionError as e:
                handle_error(e, "File organization")
            except FileOrganizationError as e:
                handle_error(e, "File organization")
            except Exception as e:
                handle_error(e, "File organization")
            click.pause()
            
        elif choice == '3':
            click.clear()
            raw_sources = click.prompt("Enter file/folder path(s) to backup (comma-separated for multiple)")
            if not raw_sources.strip():
                click.secho("❌ Backup path cannot be empty", fg='red')
                click.pause()
                continue
                
            try:
                sources = tuple(path.strip() for path in raw_sources.split(',') if path.strip())
                compress = click.confirm("Compress backup to ZIP?", default=True)
                backup_format = 'zip' if compress else 'folder'
                _run_backup_operation(sources, None, backup_format, False)

                click.secho("\n" + "="*50, fg='cyan')
                click.secho("☁️  Cloud Backup (via Rclone)", fg='cyan')
                click.secho("="*50 + "\n", fg='cyan')

                backup_to_cloud = click.confirm(
                    "Do you want to backup to cloud storage (Google Drive, OneDrive, etc.)?",
                    default=False
                )

                if backup_to_cloud:
                    click.echo("\nAvailable Cloud Remotes (configured via rclone):")
                    click.echo("  • gdrive   - Google Drive")
                    click.echo("  • onedrive - Microsoft OneDrive")
                    click.echo("  • dropbox  - Dropbox")
                    click.echo("  • s3       - Amazon S3")
                    click.echo("  • b2       - Backblaze B2")
                    click.echo("\nTo configure a new remote, run: rclone config\n")

                    remote_name = click.prompt("Enter remote name (default: gdrive)", default='gdrive')
                    source_paths = _prepare_backup_sources(sources)
                    upload_successes = 0

                    for source_path in source_paths:
                        backup_mgr = BackupManager(str(source_path))
                        existing_backups = backup_mgr.get_existing_backups()
                        if not existing_backups:
                            logger.warning(f"No backup found to upload for {source_path}")
                            continue

                        latest_backup = existing_backups[0]
                        click.echo(f"\nUploading backup for '{source_path.name}' to '{remote_name}'...")
                        progress_cb = make_click_progress_callback(f"Uploading {source_path.name}")
                        upload_result = backup_mgr.upload_to_rclone(
                            latest_backup,
                            remote_name,
                            '/System Backups',
                            progress_callback=progress_cb
                        )

                        if upload_result:
                            upload_successes += 1
                            logger.info(f"Backup uploaded to Rclone remote '{remote_name}': {latest_backup}")
                        else:
                            logger.warning(f"Rclone upload to '{remote_name}' failed for {latest_backup}")

                    if upload_successes == len(source_paths):
                        click.secho(f"All backups uploaded to '{remote_name}' successfully!", fg='green')
                    elif upload_successes:
                        click.secho(
                            f"Uploaded {upload_successes} of {len(source_paths)} backup(s) to '{remote_name}'",
                            fg='yellow'
                        )
                    else:
                        click.secho("Failed to upload to cloud storage", fg='yellow')
                        click.secho("Make sure Rclone is installed and the remote is configured\n", fg='yellow')

                click.pause()
                continue
                
                try:
                    validate_backup_drive()
                except PathError as e:
                    click.secho(f"⚠️  {e}", fg='yellow')
                    click.pause()
                    continue
                
                # Check disk space
                folder_size = get_folder_size(folder)
                required_space = folder_size * 1.5
                backup_path = Path(Config.BACKUP_DRIVE)
                
                try:
                    validate_disk_space(backup_path, int(required_space))
                except DiskSpaceError as e:
                    click.secho(f"❌ {e}", fg='red')
                    click.pause()
                    continue
                
                compress = click.confirm("Compress backup to ZIP?", default=True)
                backup_mgr = BackupManager(source_folder)
                backup_result = backup_mgr.create_backup(compress=compress)
                
                if backup_result:
                    click.secho("✅ Backup created successfully!", fg='green')
                    logger.info("Backup completed successfully")
                    # Send manual backup email notification for logged-in user.
                    user_email = current_user.get('email')
                    if user_email:
                        try:
                            backup_mgr.send_backup_email(str(user_email), backup_result, "Manual")
                        except Exception as e:
                            logger.error(f"Failed to send backup email: {e}")
                    
                    # Ask about cloud backup
                    click.secho("\n" + "="*50, fg='cyan')
                    click.secho("☁️  Cloud Backup (via Rclone)", fg='cyan')
                    click.secho("="*50 + "\n", fg='cyan')
                    
                    backup_to_cloud = click.confirm(
                        "Do you want to backup to cloud storage (Google Drive, OneDrive, etc.)?",
                        default=False
                    )
                    
                    if backup_to_cloud:
                        click.echo("\nAvailable Cloud Remotes (configured via rclone):")
                        click.echo("  • gdrive   - Google Drive")
                        click.echo("  • onedrive - Microsoft OneDrive")
                        click.echo("  • dropbox  - Dropbox")
                        click.echo("  • s3       - Amazon S3")
                        click.echo("  • b2       - Backblaze B2")
                        click.echo("\nTo configure a new remote, run: rclone config\n")
                        
                        remote_name = click.prompt("Enter remote name (default: gdrive)", default='gdrive')
                        
                        click.echo(f"\n🔄 Uploading backup to '{remote_name}'...")
                        progress_cb = make_click_progress_callback(f"Uploading to {remote_name}")
                        upload_result = backup_mgr.upload_to_rclone(
                            backup_result,
                            remote_name,
                            '/System Backups',
                            progress_callback=progress_cb
                        )
                        
                        if upload_result:
                            click.secho(f"✅ Backup uploaded to '{remote_name}' successfully!", fg='green')
                            click.secho(f"📁 Remote name: {remote_name}\n", fg='green')
                            logger.info(f"Backup uploaded to Rclone remote '{remote_name}'")
                        else:
                            click.secho("❌ Failed to upload to cloud storage", fg='yellow')
                            click.secho("💡 Make sure Rclone is installed and the remote is configured\n", fg='yellow')
                            logger.warning(f"Rclone upload to '{remote_name}' failed")
                    else:
                        click.secho("Backup saved locally only.", fg='yellow')
                else:
                    click.secho("❌ Backup failed!", fg='red')
            except PathError as e:
                handle_error(e, "Backup operation")
            except PermissionError as e:
                handle_error(e, "Backup operation")
            except BackupError as e:
                handle_error(e, "Backup operation")
            except Exception as e:
                handle_error(e, "Backup operation")
            click.pause()
            
        elif choice == '4':
            click.clear()
            log_path = click.prompt("Enter log file or folder path")
            if not log_path.strip():
                click.secho("❌ Path cannot be empty", fg='red')
                click.pause()
                continue
            try:
                path = validate_path_exists(log_path, path_type="any")
                validate_path_readable(path)
                
                analyzer = LogAnalyzer()
                if path.is_file():
                    analyzer.analyze_log_file(log_path)
                else:
                    analyzer.analyze_folder(log_path)
                analyzer.display_summary()
                analyzer.export_to_csv()
                logger.info("Report generated successfully")
                click.secho("✅ Report generated!", fg='green')
            except PathError as e:
                handle_error(e, "Report generation")
            except PermissionError as e:
                handle_error(e, "Report generation")
            except LogAnalysisError as e:
                handle_error(e, "Report generation")
            except Exception as e:
                handle_error(e, "Report generation")
            click.pause()

        elif choice == '5':
            click.clear()
            scheduler_menu(task_scheduler)
            
        elif choice == '6':
            click.clear()
            email = current_user['email']
            user = auth_manager.users.get(email)
            
            if user:
                click.secho("\n" + "="*50, fg='cyan')
                click.secho("👤 Your Profile", fg='cyan')
                click.secho("="*50 + "\n", fg='cyan')
                click.secho(f"Email: {user['email']}")
                click.secho(f"Name: {user.get('full_name', 'N/A')}")
                click.secho(f"Created: {user.get('created_at', 'N/A')}")
                click.secho(f"Last Login: {user.get('last_login', 'Never')}\n")
                logger.info(f"Profile viewed by: {email}")
            else:
                click.secho("❌ User not found.", fg='red')
            click.pause()
            
        elif choice == '7':
            click.clear()
            click.secho("\n" + "="*50, fg='cyan')
            click.secho("🔐 Change Password", fg='cyan')
            click.secho("="*50 + "\n", fg='cyan')
            
            email = cast(str, current_user['email'])
            if not email:
                click.secho("❌ User email not found!", fg='red')
                click.pause()
                continue
                
            old_password = click.prompt('🔐 Enter your current password', hide_input=True)
            
            while True:
                new_password = click.prompt('🔐 Enter new password (min 8 chars, 1 uppercase, 1 digit)', hide_input=True)
                confirm_password = click.prompt('🔐 Confirm new password', hide_input=True)
                
                if new_password != confirm_password:
                    click.secho("❌ Passwords don't match. Try again.", fg='red')
                    continue
                break
            
            result = auth_manager.change_password(email, old_password, new_password)
            
            if result['success']:
                click.secho(f"\n✅ {result['message']}", fg='green')
                logger.info(f"Password changed for user: {email}")
            else:
                click.secho(f"\n❌ {result['message']}", fg='red')
            click.pause()
            
        elif choice == '8':
            email = cast(str, current_user['email'])
            if not email:
                click.secho("❌ User email not found!", fg='red')
                click.pause()
                continue
                
            result = auth_manager.logout(email)
            
            if result['success']:
                current_user['email'] = None
                current_user['name'] = None
                current_user['token'] = None
                click.secho("✅ Logged out successfully!", fg='green')
                logger.info(f"User logged out: {email}")
                click.pause()
                interactive_menu()  # Return to login menu
                return
            else:
                click.secho(f"❌ {result['message']}", fg='red')
                click.pause()
            
        elif choice == '9':
            click.secho("👋 Goodbye!", fg='cyan')
            break


if __name__ == '__main__':
    import sys
    
    def main() -> None:
        """Main entry point for the CLI application"""
        # If no arguments provided, show interactive menu
        if len(sys.argv) == 1:
            interactive_menu()
        else:
            cli()
    
    main()



