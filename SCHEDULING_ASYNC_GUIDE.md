# Scheduling & Async Features Documentation

## Overview
This document explains the scheduling and async capabilities added to the System Manager CLI.

## Features

### 1. Task Scheduling
Schedule automated tasks to run periodically in the background.

**Supported Tasks:**
- `health` - Monitor system health (CPU, RAM, Disk)
- `backup` - Create automatic backups
- `cleanup` - Organize and clean files
- `report` - Generate log analysis reports

**Time Units:**
- `seconds` - Run every N seconds
- `minutes` - Run every N minutes
- `hours` - Run every N hours
- `days` - Run every N days

### 2. Async Operations
Execute multiple tasks concurrently without blocking.

---

## CLI Commands

### Schedule a Task
The `schedule-task` command allows full control from the CLI, but for
many users it's easier to use the interactive wizard (also invoked during
`python main.py setup`).  The wizard behaves like setting an alarm on your
phone: pick an operation, choose a time and recurrence (daily/weekly/monthly)
and the task will be registered.

You can still use the direct command as shown below:
```bash
python main.py schedule-task --task TASK_TYPE --interval INT --unit UNIT [OPTIONS]
```

**Examples:**

Health check every 30 minutes:
```bash
python main.py schedule-task --task health --interval 30 --unit minutes
```

Backup every day:
```bash
python main.py schedule-task --task backup --interval 1 --unit days --folder "C:\backups"
```

Daily cleanup at 2AM (run scheduler during off-peak hours):
```bash
python main.py schedule-task --task cleanup --interval 24 --unit hours --folder "C:\temp"
```

Hourly log analysis:
```bash
python main.py schedule-task --task report --interval 1 --unit hours --log-path "C:\logs"
```

### Start the Scheduler
```bash
python main.py start-scheduler
```
- Starts the background scheduler
- Runs all scheduled tasks
- Press Ctrl+C to stop
- Tasks continue running until stopped

### Stop the Scheduler
```bash
python main.py stop-scheduler
```
- Stops the background scheduler
- Saves current state

### List Schedule Tasks
```bash
python main.py list-tasks
```
- Shows all scheduled tasks
- Displays task IDs, intervals, clock time, and any weekday/month restrictions
- Shows next run times

### Remove a Scheduled Task
```bash
python main.py remove-task
```
- Interactive menu to select and remove tasks
- Prompts for confirmation

### Run Async Demo
```bash
python main.py run-async-demo
```
- Demonstrates async capabilities
- Runs 3 concurrent health checks
- Shows results

---

## Python Module Usage

### Using TaskScheduler Class

```python
from scheduler import TaskScheduler

# Create scheduler instance
scheduler = TaskScheduler()

# Add a task
def my_task():
    print("Task running!")

scheduler.add_task('task1', my_task, interval=30, unit='minutes')

# Start the scheduler
scheduler.start()

# List tasks
tasks = scheduler.list_tasks()
print(tasks)

# Get next run times
next_runs = scheduler.get_next_runs()

# Remove a task
scheduler.remove_task('task1')

# Stop the scheduler
scheduler.stop()
```

### Using Async Tasks

```python
from async_tasks import (
    async_health_check,
    async_backup,
    async_cleanup,
    run_concurrent_tasks,
    batch_health_checks,
    batch_backups
)
import asyncio

# Run single async task
result = asyncio.run(async_health_check())

# Run multiple tasks concurrently
results = asyncio.run(run_concurrent_tasks(
    async_health_check(),
    async_health_check(),
    async_health_check()
))

# Batch operations
health_results = asyncio.run(batch_health_checks(count=5))

backup_results = asyncio.run(batch_backups(
    folders=['/path1', '/path2', '/path3']
))

cleanup_results = asyncio.run(batch_cleanups(
    folders=['/temp1', '/temp2']
))
```

### Creating Custom Scheduled Tasks

```python
from scheduler import TaskScheduler

scheduler = TaskScheduler()

def custom_backup():
    print("Running custom backup...")
    # Your backup code here

scheduler.add_task(
    task_id='custom_backup',
    task_func=custom_backup,
    interval=2,
    unit='hours'
)

scheduler.start()
```

---

## Common Scenarios

### Scenario 1: Daily Backup at Night
```bash
# Schedule backup every 24 hours
python main.py schedule-task --task backup --interval 24 --unit hours --folder "D:\important_data"

# Start scheduler and keep it running
python main.py start-scheduler
```

### Scenario 2: Hourly Health Checks with Alerts
```bash
# Schedule health monitoring every hour
python main.py schedule-task --task health --interval 1 --unit hours

# Start with email alerts (configure .env first)
python main.py start-scheduler
```

### Scenario 3: Cleanup Large Temp Folders
```bash
# Hourly cleanup every 2 hours
python main.py schedule-task --task cleanup --interval 2 --unit hours --folder "C:\Windows\Temp"

# Start scheduler
python main.py start-scheduler
```

### Scenario 4: Multiple Monitoring Tasks
```bash
# Schedule multiple tasks
python main.py schedule-task --task health --interval 30 --unit minutes
python main.py schedule-task --task report --interval 1 --unit hours --log-path "C:\logs"
python main.py schedule-task --task cleanup --interval 6 --unit hours --folder "C:\temp"

# Start scheduler (all tasks run in background)
python main.py start-scheduler
```

---

## Advanced Usage

### Task Wrapper for Arguments
```python
from scheduler import TaskScheduler, create_task_wrapper

def backup_with_compression(folder, compress=True):
    # Your code here
    pass

scheduler = TaskScheduler()

# Create wrapper to pass arguments
task = create_task_wrapper(backup_with_compression, "D:\data", compress=True)
scheduler.add_task('backup_task', task, interval=1, unit='days')
scheduler.start()
```

### Running with Timeout
```python
from async_tasks import run_with_timeout, async_backup
import asyncio

# Run backup with 5 minute timeout
result = asyncio.run(run_with_timeout(
    async_backup("C:\folder"),
    timeout_seconds=300
))
```

---

## Logging

All scheduled tasks log their execution:

```
[2024-02-21 14:30:45] Scheduled health check - CPU: 45%, RAM: 60%
[2024-02-21 14:31:00] Scheduled backup completed: C:\backups\backup_20240221_143100.zip
[2024-02-21 14:32:15] Scheduled cleanup completed: C:\temp
```

Check logs in: `system_manager_cli/logs/`

---

## Best Practices

1. **Use Reasonable Intervals**
   - Health checks: 15-60 minutes
   - Backups: 1-24 hours
   - Cleanup: 2-24 hours

2. **Monitor Resources**
   - Check CPU/RAM usage with health checks
   - Avoid too many concurrent tasks
   - Monitor available disk space for backups

3. **Error Handling**
   - All failures are logged
   - Tasks continue running even if one fails
   - Check logs for issues

4. **Testing**
   - Use `run-async-demo` to test setup
   - Start with short intervals during testing
   - Verify tasks run before deploying

5. **Performance**
   - Async tasks run concurrently without blocking
   - Scheduler uses minimal CPU while idle
   - Background thread allows main app to continue

---

## Troubleshooting

### Task Not Running
1. Check if scheduler is started: `python main.py list-tasks`
2. Verify task was created successfully
3. Check logs for errors: `system_manager_cli/logs/`

### High CPU Usage
1. Check task interval is not too short
2. Verify tasks aren't running too long
3. Reduce concurrent task count

### Backups Failing
1. Verify destination folder has write permissions
2. Check available disk space
3. Ensure source folder exists

### Log Analysis Issues
1. Verify log file format is supported
2. Check file permissions
3. Ensure disk space for reports

---

## Architecture

```
scheduler.py
├── TaskScheduler (background scheduling)
├── AsyncTaskRunner (concurrent execution)
└── Helper functions

async_tasks.py
├── async_health_check()
├── async_backup()
├── async_cleanup()
├── async_log_analysis()
├── Batch operations
└── Timeout handling

main.py
├── schedule-task command
├── start-scheduler command
├── stop-scheduler command
├── list-tasks command
├── remove-task command
└── run-async-demo command
```

---

## Files Modified

- `requirements.txt` - Added `schedule==1.2.0`
- `main.py` - Added scheduler commands and async helpers
- `scheduler.py` - New module for task scheduling
- `async_tasks.py` - New module for async operations
