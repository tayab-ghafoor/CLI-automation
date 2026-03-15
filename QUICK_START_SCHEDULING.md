# Scheduling & Async Quick Start Guide

## Installation

```bash
# Install the schedule package
pip install schedule

# Or install from requirements.txt
pip install -r requirements.txt
```

## Quick Start (5 minutes)

### 1. Schedule a Health Check
```bash
# Check system health every 30 minutes
python main.py schedule-task --task health --interval 30 --unit minutes
```

### 2. Start the Scheduler
```bash
# This starts the background task scheduler
python main.py start-scheduler
```

Press `Ctrl+C` when you want to stop.

### 3. Check Scheduled Tasks
```bash
# See all tasks and next run times
python main.py list-tasks
```

### 4. Remove a Task
```bash
# Interactive menu to select and remove tasks
python main.py remove-task
```

## Common Commands

### Health Monitoring
```bash
# Check every 15 minutes
python main.py schedule-task --task health --interval 15 --unit minutes

# Start scheduler
python main.py start-scheduler
```

### Daily Backups
```bash
# Backup every 24 hours (daily)
python main.py schedule-task --task backup --interval 1 --unit days --folder "D:\data"

# Start scheduler
python main.py start-scheduler
```

### Hourly Cleanup
```bash
# Clean temp files every 2 hours
python main.py schedule-task --task cleanup --interval 2 --unit hours --folder "C:\Temp"

# Start scheduler
python main.py start-scheduler
```

### Log Analysis
```bash
# Analyze logs every hour
python main.py schedule-task --task report --interval 1 --unit hours --log-path "C:\logs"

# Start scheduler
python main.py start-scheduler
```

## Demo: Async Capabilities

```bash
# Run a demo of concurrent operations
python main.py run-async-demo
```

This will:
- Run 3 health checks at the same time
- Show the results
- Demonstrate async/await performance benefits

## Using in Python Code

### Simple Scheduling
```python
from scheduler import TaskScheduler

# Create scheduler
scheduler = TaskScheduler()

# Add task
def my_task():
    print("Running task!")

scheduler.add_task("my_task", my_task, interval=5, unit="minutes")

# Start
scheduler.start()
```

### Async Operations
```python
from async_tasks import batch_health_checks
import asyncio

# Run 5 health checks concurrently
results = asyncio.run(batch_health_checks(count=5))
```

## Important Notes

1. **Scheduler runs in background** - Once started, tasks run continuously
2. **Tasks are logged** - Check `logs/` folder for execution details
3. **Errors are handled** - Failed tasks are logged but don't stop the scheduler
4. **CPU friendly** - Scheduler uses minimal resources when idle

## Troubleshooting

### Task not running?
```bash
# Check if task exists
python main.py list-tasks

# Check logs
cat system_manager_cli/logs/*.log
```

### Need to stop everything?
```bash
# Stop scheduler
python main.py stop-scheduler

# Or press Ctrl+C if running start-scheduler
```

### What happens to tasks when I exit?
- Tasks stop running
- Scheduler saves state
- Restart with `start-scheduler` to resume

## Next Steps

1. Read [SCHEDULING_ASYNC_GUIDE.md](SCHEDULING_ASYNC_GUIDE.md) for detailed documentation
2. Check [EXAMPLES_SCHEDULING.py](EXAMPLES_SCHEDULING.py) for code examples
3. Review the modules:
   - `scheduler.py` - Task scheduling logic
   - `async_tasks.py` - Async operations
   - `main.py` - CLI commands

## Performance Tips

- ✅ Health checks: 15-60 minutes
- ✅ Backups: 4-24 hours
- ✅ Cleanup: 2-24 hours
- ❌ Avoid: Less than 10 seconds
- ❌ Avoid: Too many concurrent backups

## Support

For issues or questions, check:
1. Log files in `system_manager_cli/logs/`
2. [SCHEDULING_ASYNC_GUIDE.md](SCHEDULING_ASYNC_GUIDE.md) - Full documentation
3. [EXAMPLES_SCHEDULING.py](EXAMPLES_SCHEDULING.py) - Code examples
