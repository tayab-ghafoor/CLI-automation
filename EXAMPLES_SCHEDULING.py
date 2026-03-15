"""
Example: Using Scheduling and Async Features
Practical examples of how to use the new scheduling and async capabilities
"""

# Example 1: Simple Scheduled Health Check
# ==================================================
if __name__ == "__main__":
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Create scheduler
    scheduler = TaskScheduler()
    
    # Define a simple task
    def check_health_simple():
        logger.info("Health check running...")
    
    # Schedule it to run every 30 minutes
    scheduler.add_task(
        task_id="health_check",
        task_func=check_health_simple,
        interval=30,
        unit="minutes"
    )
    
    # Start the scheduler
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler stopped.")


# Example 2: Async Concurrent Operations
# ==================================================
async def example_concurrent_operations():
    """
    Run multiple health checks concurrently
    This demonstrates the performance benefit of async
    """
    from system_manager_cli.Primary_Project_Code.async_tasks import batch_health_checks, batch_backups
    import asyncio
    
    # Run 5 health checks at the same time
    # Instead of waiting 5 sequential checks (slow)
    # Async runs them concurrently (fast)
    
    print("Running 5 concurrent health checks...")
    results = await batch_health_checks(count=5)
    
    for i, result in enumerate(results, 1):
        print(f"Check {i}: CPU={result.get('cpu')}%, RAM={result.get('memory')}%")


# Example 3: Scheduled Backup with Custom Logic
# ==================================================
def example_scheduled_backup():
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler, create_task_wrapper
    from system_manager_cli.Primary_Project_Code.backup_manager import BackupManager
    import logging
    
    scheduler = TaskScheduler()
    logger = logging.getLogger(__name__)
    
    def smart_backup(folder_path, compress=True, max_backups=7):
        """Custom backup function with more options"""
        try:
            backup_mgr = BackupManager(folder_path)
            backup_path = backup_mgr.create_backup(compress=compress)
            logger.info(f"Smart backup created: {backup_path}")
            
            # Cleanup old backups if needed
            backups = backup_mgr.list_backups()
            if len(backups) > max_backups:
                logger.info(f"Too many backups, cleaning up old ones")
                # Delete oldest backups
        except Exception as e:
            logger.error(f"Smart backup failed: {e}")
    
    # Create task wrapper with arguments
    task = create_task_wrapper(
        smart_backup,
        folder_path="D:\\important_data",
        compress=True,
        max_backups=7
    )
    
    # Schedule to run daily (24 hours)
    scheduler.add_task(
        task_id="daily_backup",
        task_func=task,
        interval=24,
        unit="hours"
    )
    
    scheduler.start()


# Example 4: Multiple Scheduled Tasks
# ==================================================
def example_multiple_tasks():
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler
    from system_manager_cli.Primary_Project_Code.health_monitor import HealthMonitor
    from system_manager_cli.Primary_Project_Code.file_organizer import FileOrganizer
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    
    logger = get_logger(__name__)
    scheduler = TaskScheduler()
    
    # Task 1: Health monitoring
    def monitor_health():
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        is_healthy = (
            results.get('cpu', 0) < 80 and
            results.get('memory', 0) < 85 and
            results.get('disk', 0) < 90
        )
        if is_healthy:
            logger.info("System healthy ✅")
        else:
            logger.warning("System resource usage high ⚠️")
    
    # Task 2: File cleanup
    def cleanup_files():
        try:
            organizer = FileOrganizer("C:\\Temp")
            organizer.organize_files(rename=True, delete_dups=True)
            logger.info("Temp files cleaned ✅")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    # Task 3: Weekly reports
    def generate_weekly_report():
        logger.info("Generating weekly report...")
        # Your report generation code here
    
    # Schedule all tasks
    scheduler.add_task("health", monitor_health, interval=30, unit="minutes")
    scheduler.add_task("cleanup", cleanup_files, interval=2, unit="hours")
    scheduler.add_task("report", generate_weekly_report, interval=7, unit="days")
    
    # Start scheduler
    scheduler.start()
    
    # Display scheduled tasks
    print("\n📋 Scheduled Tasks:")
    for task_id, schedule_info in scheduler.list_tasks().items():
        print(f"  • {task_id}: {schedule_info}")
    
    print("\n⏱️  Next Runs:")
    for run_info in scheduler.get_next_runs():
        print(f"  • Next run in {run_info['idle_seconds']:.0f} seconds")


# Example 5: Run Async Tasks with Results
# ==================================================
async def example_async_with_results():
    """
    Run async tasks and collect results for processing
    """
    from system_manager_cli.Primary_Project_Code.async_tasks import batch_backups, batch_cleanups, run_concurrent_tasks
    import asyncio
    
    folders_to_backup = [
        "D:\\Documents",
        "D:\\Photos",
        "D:\\Projects"
    ]
    
    folders_to_clean = [
        "C:\\Temp",
        "C:\\Windows\\Temp"
    ]
    
    # Backup multiple folders concurrently
    print("Starting concurrent backups...")
    backup_results = await batch_backups(folders_to_backup, compress=True)
    
    for folder, backup_path in backup_results.items():
        status = "✅ Success" if backup_path else "❌ Failed"
        print(f"  {folder}: {status}")
    
    # Cleanup folders concurrently
    print("\nStarting concurrent cleanup...")
    cleanup_results = await batch_cleanups(folders_to_clean)
    
    for folder, success in cleanup_results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {folder}: {status}")


# Example 6: Conditional Scheduled Tasks
# ==================================================
def example_conditional_tasks():
    """
    Schedule tasks that run conditionally based on system state
    """
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler
    from system_manager_cli.Primary_Project_Code.health_monitor import HealthMonitor
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    
    logger = get_logger(__name__)
    scheduler = TaskScheduler()
    
    def conditional_backup():
        """Only backup if system isn't busy"""
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        
        cpu_usage = results.get('cpu', 0)
        
        if cpu_usage < 30:  # CPU usage below 30%
            logger.info("System idle, starting backup...")
            # Perform backup
        else:
            logger.info(f"System busy (CPU: {cpu_usage}%), skipping backup")
    
    scheduler.add_task(
        "conditional_backup",
        conditional_backup,
        interval=1,
        unit="hours"
    )
    scheduler.start()


# Example 7: Error Handling in Scheduled Tasks
# ==================================================
def example_error_handling():
    """
    Properly handle errors in scheduled tasks
    """
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    from system_manager_cli.Primary_Project_Code.exceptions import BackupError
    
    logger = get_logger(__name__)
    scheduler = TaskScheduler()
    
    def robust_task():
        """Task with comprehensive error handling"""
        try:
            # Your task code here
            logger.info("Task started")
            
            # Simulate work
            result = "Task completed successfully"
            logger.info(result)
            
        except BackupError as e:
            logger.error(f"Backup error: {e}")
            # Handle backup-specific errors
            
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            # Handle permission issues
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            # Handle any other errors
    
    scheduler.add_task("robust", robust_task, interval=1, unit="hours")
    scheduler.start()


# Example 8: Real-world Monitoring Setup
# ==================================================
def example_production_setup():
    """
    Real-world example of a complete monitoring setup
    """
    from system_manager_cli.Primary_Project_Code.scheduler import TaskScheduler
    from system_manager_cli.Primary_Project_Code.health_monitor import HealthMonitor
    from system_manager_cli.Primary_Project_Code.backup_manager import BackupManager
    from system_manager_cli.Primary_Project_Code.file_organizer import FileOrganizer
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    
    logger = get_logger(__name__)
    scheduler = TaskScheduler()
    
    # Configuration
    BACKUP_FOLDER = "D:\\Data"
    TEMP_FOLDERS = ["C:\\Temp", "C:\\Windows\\Temp"]
    ALERT_EMAIL = "admin@example.com"
    
    # Task 1: Monitor system every 15 minutes
    def system_monitor():
        monitor = HealthMonitor()
        results = monitor.check_system_health()
        
        cpu = results.get('cpu', 0)
        ram = results.get('memory', 0)
        disk = results.get('disk', 0)
        
        logger.info(f"System Status - CPU: {cpu}%, RAM: {ram}%, Disk: {disk}%")
        
        # Alert if thresholds exceeded
        if cpu > 90 or ram > 90 or disk > 95:
            logger.critical("⚠️  System resources critically low!")
            # Send alert email
    
    # Task 2: Daily backup at 2 AM
    def daily_backup():
        try:
            backup_mgr = BackupManager(BACKUP_FOLDER)
            backup_path = backup_mgr.create_backup(compress=True)
            logger.info(f"Daily backup completed: {backup_path}")
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")
    
    # Task 3: Hourly temp cleanup
    def hourly_cleanup():
        for folder in TEMP_FOLDERS:
            try:
                organizer = FileOrganizer(folder)
                organizer.organize_files(rename=False, delete_dups=True)
                logger.info(f"Cleaned {folder}")
            except Exception as e:
                logger.error(f"Cleanup failed for {folder}: {e}")
    
    # Schedule all tasks
    scheduler.add_task("monitor", system_monitor, interval=15, unit="minutes")
    scheduler.add_task("backup", daily_backup, interval=24, unit="hours")
    scheduler.add_task("cleanup", hourly_cleanup, interval=1, unit="hours")
    
    # Start scheduler
    scheduler.start()
    logger.info("Production monitoring setup started")
    
    return scheduler


# Run examples
if __name__ == "__main__":
    import asyncio
    
    print("System Manager CLI - Scheduling & Async Examples")
    print("=" * 50)
    print("\nExample 1: Simple Scheduled Health Check")
    print("Example 2: Async Concurrent Operations")
    print("Example 3: Scheduled Backup with Custom Logic")
    print("Example 4: Multiple Scheduled Tasks")
    print("Example 5: Run Async Tasks with Results")
    print("Example 6: Conditional Scheduled Tasks")
    print("Example 7: Error Handling in Scheduled Tasks")
    print("Example 8: Real-world Monitoring Setup")
    print("\nUncomment the example you want to run in __main__")
