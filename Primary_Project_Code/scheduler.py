"""
Task Scheduler Module
Provides scheduling and async capabilities for system tasks
"""

# guard against workspace modules shadowing the standard library
import sys, importlib
try:
    sys.modules['string'] = importlib.import_module('string')
except ImportError:
    pass

# Add the parent directory to sys.path to enable importing main
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import schedule
import threading
import time
import asyncio
import sys
from typing import Callable, Dict, Any
from datetime import datetime
from .logger import get_logger
from .email_notifier import EmailNotifier
from pathlib import Path

logger = get_logger(__name__)


def _resolve_main_module():
    """Return the loaded main module regardless of launch style."""
    runtime_main = sys.modules.get("__main__")
    if runtime_main and getattr(runtime_main, "__file__", "").endswith("main.py"):
        return runtime_main

    for name in ("main", "system_manager_cli.main"):
        mod = sys.modules.get(name)
        if mod is not None:
            return mod
    return None


class TaskScheduler:
    """Manages scheduled tasks and background operations"""
    
    def __init__(self):
        self.scheduler = schedule.Scheduler()
        self.is_running = False
        self.worker_thread = None
        self.tasks: Dict[str, Dict[str, Any]] = {}
        # persistence file for scheduled tasks
        self._data_file = Path(__file__).parent / 'data' / 'scheduled_tasks.json'
        # ensure data directory
        self._data_file.parent.mkdir(exist_ok=True)
        # load any previously saved tasks
        try:
            self._load_saved_tasks()
        except Exception:
            logger.debug("No saved scheduled tasks found or failed to load")
    
    def add_task(
        self,
        task_id: str,
        task_func: Callable,
        interval: int = 1,
        unit: str = 'seconds',
        *,
        at_time: str | None = None,
        weekday: str | None = None,
        day_of_month: int | None = None,
    ) -> None:
        """
        Add a scheduled task.  This is a thin wrapper around ``schedule`` with
        a few convenience options to mimic an alarm clock.

        The original implementation only supported ``every(interval).unit``
        which made it difficult to schedule jobs at a particular clock time or
        on a specific weekday.  The new parameters allow those common patterns:

        * ``at_time`` – run the task each time the interval elapses at the
          specified ``HH:MM`` string (24‑hour clock).
        * ``weekday`` – for weekly schedules only; one of
          ``monday``…``sunday``.  This property is passed through to the
          ``schedule`` job object (``schedule.every().monday`` etc.).
        * ``day_of_month`` – if provided the task will be wrapped so that it
          only executes on that day of the month.  ``schedule`` does not have
          native monthly support, so we run the job daily and guard with a
          simple date check.

        Args:
            task_id: Unique identifier for the task
            task_func: Function to execute
            interval: How often to run (numeric value)
            unit: ``'seconds'``, ``'minutes'``, ``'hours'`` or ``'days'``
            at_time: Optional clock time in ``HH:MM`` format
            weekday: Optional weekday name for weekly jobs
            day_of_month: Optional day in month (1–31) for monthly jobs

        Raises:
            ValueError: If ``unit`` is invalid or ``weekday`` is not recognised
        """
        valid_units = ['seconds', 'minutes', 'hours', 'days', 'weeks']
        if unit not in valid_units:
            raise ValueError(f"Invalid unit. Must be one of: {valid_units}")

        # build base job
        job = getattr(self.scheduler.every(interval), unit)

        # weekly specialisation
        if weekday:
            if weekday.lower() not in (
                'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday'
            ):
                raise ValueError("""Invalid weekday. Must be one of monday–sunday""")
            # schedule.every().monday etc. ignores the previous unit, so we
            # create a fresh job object
            job = getattr(self.scheduler.every(), weekday.lower())

        if at_time:
            job = job.at(at_time)

        # run tasks in their own thread so blocking work (network waits) won't
        # block the scheduler loop. Wrap the function to start a thread.
        def _run_in_thread():
            try:
                threading.Thread(target=task_func, daemon=True).start()
            except Exception as e:
                logger.error(f"Failed to start task thread: {e}")

        # wrap for monthly behaviour if requested
        if day_of_month is not None:
            def _wrapper():
                if datetime.now().day == day_of_month:
                    return _run_in_thread()
            job = job.do(_wrapper)
        else:
            job = job.do(_run_in_thread)

        self.tasks[task_id] = {
            'job': job,
            'interval': interval,
            'unit': unit,
            'func': task_func,
            'at_time': at_time,
            'weekday': weekday,
            'day_of_month': day_of_month,
        }
        # persist task metadata for restart recovery when possible
        try:
            self._save_task_metadata(task_id)
        except Exception as e:
            logger.debug(f"Could not persist task metadata: {e}")
        logger.info(f"Task scheduled: {task_id} (every {interval} {unit}"
                    + (f" at {at_time}" if at_time else "") + ")")
    
    def remove_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.scheduler.cancel_job(self.tasks[task_id]['job'])
            del self.tasks[task_id]
            self._save_all_tasks()  # update persistence after removal
            logger.info(f"task removed: {task_id}")
            return True
        logger.warning(f"Task not found: {task_id}")
        return False
        # """
        # Remove a scheduled task
        
        # Args:
        #     task_id: ID of task to remove
        
        # Returns:
        #     bool: True if task was removed, False if not found
        # """
        # if task_id in self.tasks:
        #     self.scheduler.cancel_job(self.tasks[task_id]['job'])
        #     del self.tasks[task_id]
        #     logger.info(f"Task removed: {task_id}")
        #     return True
        # logger.warning(f"Task not found: {task_id}")
        # return False
    
    def start(self) -> None:
        """Start the scheduler in background thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.worker_thread.start()
            logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Background thread that runs scheduled tasks"""
        while self.is_running:
            try:
                self.scheduler.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
    
    # ----------------------------- Persistence -----------------------------
    def _save_all_tasks(self) -> None:
        try:
            data = {}
            for tid, info in self.tasks.items():
                # store only serializable metadata
                entry = {
                    'interval': info.get('interval'),
                    'unit': info.get('unit'),
                    'at_time': info.get('at_time'),
                    'weekday': info.get('weekday'),
                    'day_of_month': info.get('day_of_month'),
                }
                # if task was created via add_named_task store action metadata
                if info.get('action_name'):
                    entry['action_name'] = info.get('action_name')
                    entry['action_args'] = info.get('action_args', [])
                    entry['action_kwargs'] = info.get('action_kwargs', {})
                    if info.get('user_email'):
                        entry['user_email'] = info.get('user_email')
                else:
                    # fallback to func name (may not restore if it's a lambda)
                    entry['func_name'] = getattr(info.get('func'), '__name__', None)
                data[tid] = entry
            with open(self._data_file, 'w') as f:
                import json
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save scheduled tasks: {e}")

    def _save_task_metadata(self, task_id: str) -> None:
        # convenience to save the whole set after changes
        self._save_all_tasks()

    def _load_saved_tasks(self) -> None:
        import json
        if not self._data_file.exists():
            return
        try:
            with open(self._data_file, 'r') as f:
                saved = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read saved scheduled tasks: {e}")
            return

        for tid, meta in saved.items():
            try:
                def _resolve_action(action_name: str):
                    mod = _resolve_main_module()
                    if mod and hasattr(mod, action_name):
                        return getattr(mod, action_name)
                    return None

                # if action_name is present, restore with args
                if meta.get('action_name'):
                    action_name = meta.get('action_name')
                    action_args = meta.get('action_args', [])
                    action_kwargs = meta.get('action_kwargs', {})
                    resolved_func = _resolve_action(action_name)
                    # build a no-arg wrapper that calls the function with saved args
                    def _make_wrapper(f, a, kw, task_identifier, action_identifier):
                        def _wrapper():
                            try:
                                if f is not None:
                                    return f(*a, **kw)
                                # lazy resolution avoids import order issues during app startup
                                lazy_func = _resolve_action(action_identifier)
                                if lazy_func is None:
                                    raise RuntimeError(f"Action '{action_identifier}' is not available")
                                return lazy_func(*a, **kw)
                            except Exception as e:
                                logger.error(f"Scheduled task {task_identifier} failed: {e}")
                        return _wrapper

                    wrapper = _make_wrapper(
                        resolved_func,
                        action_args,
                        action_kwargs,
                        tid,
                        action_name
                    )
                    self.add_task(
                        tid,
                        wrapper,
                        interval=meta.get('interval', 1),
                        unit=meta.get('unit', 'days'),
                        at_time=meta.get('at_time'),
                        weekday=meta.get('weekday'),
                        day_of_month=meta.get('day_of_month')
                    )
                    # if a user_email was saved, notify them that a run may have been missed
                    user_email = meta.get('user_email')
                    if not user_email:
                        try:
                            from .config import Config
                            user_email = Config.EMAIL_RECIPIENT
                        except Exception:
                            user_email = None
                    if meta.get('at_time') and user_email:
                        try:
                            # check if the scheduled time for today has already passed
                            hh, mm = map(int, meta.get('at_time').split(':'))
                            scheduled_dt = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
                            if scheduled_dt < datetime.now():
                                # send a gentle reminder to open the application to run missed tasks
                                subj = 'Scheduled Task Missed - Please Open Application'
                                body = f"A scheduled task ('{action_name}') was set for {meta.get('at_time')} but the application was not running. Please open the System Manager CLI to allow the task to run."
                                try:
                                    EmailNotifier._send_email(user_email, subj, body)
                                except Exception:
                                    logger.debug("Could not send missed-task reminder email")
                        except Exception:
                            pass
                    # store action metadata so other code can see it
                    self.tasks[tid]['action_name'] = action_name
                    self.tasks[tid]['action_args'] = action_args
                    self.tasks[tid]['action_kwargs'] = action_kwargs
                    # re-save metadata so func_name placeholders are replaced
                    # with durable action_name/action_args entries.
                    try:
                        self._save_task_metadata(tid)
                    except Exception:
                        logger.debug("Could not refresh restored task metadata")
                    logger.info(f"Restored scheduled task: {tid} (action: {action_name})")
                else:
                    # fallback: try restoring by func_name
                    func_name = meta.get('func_name')
                    main_mod = _resolve_main_module()
                    func = getattr(main_mod, func_name) if main_mod and func_name and hasattr(main_mod, func_name) else None
                    if func is None:
                        logger.debug(f"Skipping restore for task {tid}: function {func_name} unavailable")
                        continue
                    self.add_task(
                        tid,
                        func,
                        interval=meta.get('interval', 1),
                        unit=meta.get('unit', 'days'),
                        at_time=meta.get('at_time'),
                        weekday=meta.get('weekday'),
                        day_of_month=meta.get('day_of_month')
                    )
                    logger.info(f"Restored scheduled task: {tid}")
            except Exception as e:
                logger.error(f"Failed to restore task {tid}: {e}")
    
    def send_task_completion_email(self, task_id: str, user_email: str, 
                                  task_description: str = "", status: str = "SUCCESS") -> bool:
        """
        Send task completion notification email
        
        Args:
            task_id: ID of the task
            user_email: User's email address
            task_description: Description of what the task does
            status: Task status (SUCCESS, WARNING, FAILED)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            task_info = self.tasks.get(task_id, {})
            if not task_info:
                logger.warning(f"Task {task_id} not found for email notification; using fallback schedule text")
                schedule_time = "Configured schedule"
            else:
                schedule_time = f"Every {task_info['interval']} {task_info['unit']}"
                if task_info.get('at_time'):
                    schedule_time += f" at {task_info['at_time']}"
                if task_info.get('weekday'):
                    schedule_time = f"Every {task_info['weekday']}"
            
            execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return EmailNotifier.send_task_completion_email(
                user_email,
                task_id,
                task_description,
                schedule_time,
                execution_time,
                status
            )
        
        except Exception as e:
            logger.error(f"Failed to send task completion email: {e}")
            return False
    
    def list_tasks(self) -> Dict[str, str]:
        """
        Return all scheduled tasks
        
        The schedule info string now includes clock time and any
        weekday/day‑of‑month restrictions so the user can easily see when
        jobs will execute.

        Returns:
            dict: Task IDs as keys, schedule info as values
        """
        output: Dict[str, str] = {}
        for task_id, data in self.tasks.items():
            parts = [f"every {data['interval']} {data['unit']}" ]
            if data.get('at_time'):
                parts.append(f"at {data['at_time']}")
            if data.get('weekday'):
                parts.append(f"on {data['weekday']}")
            if data.get('day_of_month') is not None:
                parts.append(f"(day {data['day_of_month']})")
            output[task_id] = " ".join(parts)
        return output
    
    def get_next_runs(self) -> list:
        """
        Get next run times for all jobs currently registered with the
        scheduler.  ``schedule`` does not expose ``idle_seconds`` consistently
        across versions, so we compute the delta ourselves.

        Returns:
            list: Each entry contains ``job`` object, ``next_run`` datetime and
            ``idle_seconds`` (int).
        """
        next_runs = []
        import datetime as _dt

        for job in self.scheduler.jobs:
            next_run = getattr(job, 'next_run', None)
            idle = None
            if next_run:
                delta = next_run - _dt.datetime.now()
                idle = int(delta.total_seconds()) if delta.total_seconds() > 0 else 0
            next_runs.append({
                'job': job,
                'next_run': next_run,
                'idle_seconds': idle
            })
        return next_runs
    
    def clear_all(self) -> None:
        """Clear all scheduled tasks"""
        self.scheduler.clear()
        self.tasks.clear()
        logger.info("All scheduled tasks cleared")


class AsyncTaskRunner:
    """Helper class for running async tasks"""
    
    @staticmethod
    async def run_concurrent(*coros):
        """
        Run multiple coroutines concurrently
        
        Args:
            *coros: Coroutines to run
        
        Returns:
            List of results from all coroutines
        """
        return await asyncio.gather(*coros)
    
    @staticmethod
    def run_async(coro):
        """
        Run a coroutine and return result
        
        Args:
            coro: Coroutine to run
        
        Returns:
            Result from the coroutine
        """
        return asyncio.run(coro)


def schedule_task(task_id: str, task_func: Callable, interval: int, unit: str = 'seconds', *,
                  at_time: str | None = None, weekday: str | None = None,
                  day_of_month: int | None = None) -> None:
    """
    Convenient wrapper around ``TaskScheduler.add_task`` for simple scripts.
    See ``TaskScheduler.add_task`` for the full parameter list.
    """
    scheduler = TaskScheduler()
    scheduler.add_task(task_id, task_func, interval, unit,
                       at_time=at_time, weekday=weekday,
                       day_of_month=day_of_month)


def create_task_wrapper(func: Callable, *args, **kwargs) -> Callable:
    """
    Create a wrapper around a function with arguments for scheduling.

    This helper is useful when you want to register a job that requires
    parameters; ``schedule`` only accepts callables with no arguments.
    """
    def wrapper():
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
    return wrapper


# ---------------------------------------------------------------------------
# interactive helpers
# ---------------------------------------------------------------------------

def interactive_remove_task(scheduler: TaskScheduler) -> None:
    """Interactive flow to remove scheduled tasks.
     1. Ask Y/N
     2. Show all tasks 
     3. Let user select 
     4. Ask conformation
     5. Remove
     6. Save
    """
    import click
    # step 1: Ask user
    remove_choice = click.confirm("Do you want to remove scheduled tasks?", default=False)
    if not remove_choice:
        click.secho("Operation cancelled.", fg="yellow")
        return
    # step 2: Show all tasks
    tasks = scheduler.list_tasks()
    if not tasks:
        click.secho("No Sheduled task found", fg="yellow")
        return
    click.secho("\n📋 Scheduled Tasks:", fg="cyan", bold=True)
    task_ids = list(tasks.keys())
    for index, task_id in enumerate(task_ids, start=1):
        click.secho(f"{index}. {task_id} - {tasks[task_id]}", fg="white")
        
    # step 3: Let user select
    try:
        choice = click.prompt("\n Enter the number of the task to remove ", type=int)
    except Exception:
        click.secho("Invalid Input.", fg="red")
        return
    if choice < 1 or choice > len(task_ids):
        click.secho("Invalid Selection.", fg="red")
        return
    selected_task_id = task_ids[choice - 1]
    # step 4: conformation 
    conform_delete = click.confirm(f"Are you sure you want to delete '{selected_task_id}'?", default=False)
    if not conform_delete:
        click.secho("Deletion Cancelled.", fg="yellow")
        return
    # step 5: Remove
    removed = scheduler.remove_task(selected_task_id)
    if removed:
        click.secho("Task removed successfully!", fg="green")
    else:
        click.secho("Failed to remove task.", fg="red")


def _build_schedule_description(
    frequency: str,
    time_str: str,
    weekday: str | None = None,
    day_of_month: int | None = None,
) -> str:
    """Create a readable schedule string used in notifications and persistence."""
    if frequency == 'weekly' and weekday:
        return f"every {weekday} at {time_str}"
    if frequency == 'monthly' and day_of_month is not None:
        return f"day {day_of_month} of every month at {time_str}"
    return f"every day at {time_str}"


def _task_display_details(task_id: str, task_info: Dict[str, Any]) -> Dict[str, str]:
    """Return user-facing details for a scheduled task."""
    action_name = task_info.get('action_name')
    raw_name = action_name or task_id.split('_')[0]
    name = raw_name.replace('scheduled_', '').replace('_', ' ').title()

    action_args = task_info.get('action_args', [])
    path_value = "N/A"
    if raw_name.endswith('backup') or raw_name == 'backup':
        if action_args:
            sources = action_args[0]
            if isinstance(sources, (list, tuple)):
                path_value = ", ".join(str(path) for path in sources) if sources else "N/A"
            else:
                path_value = str(sources)
    elif (raw_name.endswith('cleanup') or raw_name == 'cleanup') and action_args:
        path_value = str(action_args[0])
    elif (raw_name.endswith('log_analysis') or raw_name == 'report') and action_args:
        path_value = str(action_args[0])

    time_value = task_info.get('at_time') or "N/A"
    if task_info.get('weekday'):
        time_value = f"{task_info['weekday'].title()} {time_value}"
    elif task_info.get('day_of_month') is not None:
        time_value = f"Day {task_info['day_of_month']} {time_value}"

    return {
        'name': name,
        'time': time_value,
        'path': path_value,
    }


def view_tasks(scheduler: TaskScheduler) -> None:
    """Display scheduled tasks in a simple table."""
    import click

    if not scheduler.tasks:
        click.secho("No scheduled tasks found.", fg="yellow")
        return

    rows = []
    for index, task_id in enumerate(scheduler.tasks.keys(), start=1):
        details = _task_display_details(task_id, scheduler.tasks[task_id])
        rows.append([
            str(index),
            details['name'],
            details['time'],
            details['path'],
        ])

    headers = ["ID", "Name", "Time", "Path"]
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    separator = "-" * len(header_line)

    click.secho("\nScheduled Tasks", fg="cyan", bold=True)
    click.echo(header_line)
    click.echo(separator)
    for row in rows:
        click.echo(" | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)))


def interactive_edit_task(scheduler: TaskScheduler) -> None:
    """Allow the user to edit the run schedule of an existing task."""
    import click

    if not scheduler.tasks:
        click.secho("No scheduled tasks found.", fg="yellow")
        return

    view_tasks(scheduler)
    task_ids = list(scheduler.tasks.keys())

    try:
        choice = click.prompt("\nEnter the ID of the task to edit", type=int)
    except Exception:
        click.secho("Invalid input.", fg="red")
        return

    if choice < 1 or choice > len(task_ids):
        click.secho("Invalid selection.", fg="red")
        return

    task_id = task_ids[choice - 1]
    task_info = scheduler.tasks[task_id]
    details = _task_display_details(task_id, task_info)
    click.secho(f"Editing task: {details['name']}", fg="cyan")

    frequency = click.prompt(
        "Select new frequency",
        type=click.Choice(['daily', 'weekly', 'monthly']),
        default='weekly' if task_info.get('weekday') else 'monthly' if task_info.get('day_of_month') is not None else 'daily'
    )
    time_str = click.prompt(
        "Enter new time (HH:MM)",
        default=task_info.get('at_time') or "00:00"
    )

    weekday = None
    day_of_month = None
    if frequency == 'weekly':
        weekday = click.prompt(
            "Select weekday",
            type=click.Choice(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']),
            default=(task_info.get('weekday') or 'monday')
        )
    elif frequency == 'monthly':
        default_day = task_info.get('day_of_month') if task_info.get('day_of_month') is not None else 1
        day_of_month = click.prompt("Enter day of month", type=int, default=default_day)

    if not click.confirm(f"Save changes to '{details['name']}'?", default=True):
        click.secho("Edit cancelled.", fg="yellow")
        return

    preserved = {
        'func': task_info['func'],
        'action_name': task_info.get('action_name'),
        'action_args': list(task_info.get('action_args', [])),
        'action_kwargs': dict(task_info.get('action_kwargs', {})),
        'user_email': task_info.get('user_email'),
    }

    interval = 7 if frequency == 'weekly' else 1
    scheduler.scheduler.cancel_job(task_info['job'])
    del scheduler.tasks[task_id]
    scheduler.add_task(
        task_id,
        preserved['func'],
        interval=interval,
        unit='days',
        at_time=time_str,
        weekday=weekday,
        day_of_month=day_of_month,
    )

    updated_task = scheduler.tasks[task_id]
    if preserved['action_name']:
        updated_task['action_name'] = preserved['action_name']
    updated_task['action_kwargs'] = preserved['action_kwargs']
    if preserved['user_email']:
        updated_task['user_email'] = preserved['user_email']

    if preserved['action_args']:
        updated_args = preserved['action_args']
        if len(updated_args) > 1 and isinstance(updated_args[1], str):
            updated_args[1] = _build_schedule_description(
                frequency,
                time_str,
                weekday=weekday,
                day_of_month=day_of_month,
            )
        updated_task['action_args'] = updated_args

    scheduler._save_task_metadata(task_id)
    click.secho("Task updated successfully!", fg="green")


def interactive_schedule(scheduler: TaskScheduler) -> None:
    """Ask the user a series of questions and register a scheduled job.

    The flow mimics a mobile alarm configuration: pick an operation, choose
    when it should run (daily/weekly/monthly), and specify a clock time.
    """
    import click

    click.secho("\n📅 Schedule a task", fg='cyan', bold=True)

    choices = ['health', 'backup', 'cleanup', 'report']
    task = click.prompt("Which operation do you want to setup?", type=click.Choice(choices))

    folder = None
    backup_sources = None
    log_path = None
    if task == 'backup':
        raw_sources = click.prompt("Enter file/folder path(s) to backup (comma-separated for multiple)")
        backup_sources = [path.strip() for path in raw_sources.split(',') if path.strip()]
        if not backup_sources:
            click.secho("❌ At least one backup path is required", fg='red')
            return
        invalid_sources = [path for path in backup_sources if not Path(path).exists()]
        if invalid_sources:
            click.secho(f"❌ Invalid backup path(s): {', '.join(invalid_sources)}", fg='red')
            return
    elif task == 'cleanup':
        folder = click.prompt("Enter the folder path", type=click.Path(exists=True))
    elif task == 'report':
        log_path = click.prompt("Enter the log file or folder path", type=click.Path(exists=True))

    frequency = click.prompt(
        "Do you want the task to run every day, weekly or monthly?",
        type=click.Choice(['daily', 'weekly', 'monthly']),
        default='daily'
    )

    time_str = click.prompt("At what time? (HH:MM, 24‑hour format)", default="00:00")

    weekday = None
    day_of_month = None
    if frequency == 'weekly':
        weekday = click.prompt(
            "Which day of the week?",
            type=click.Choice(['monday','tuesday','wednesday','thursday','friday','saturday','sunday']),
            default='monday'
        )
    elif frequency == 'monthly':
        day_of_month = click.prompt("Which day of the month?", type=int, default=1)

    google_drive_choice = False
    google_drive_email = None

    main_mod = _resolve_main_module()
    if main_mod is None:
        # fallback imports when scheduler is used independently from main
        try:
            import main as main_mod  # type: ignore[assignment]
        except Exception:
            import main as main_mod  # type: ignore[assignment]

    # build the callable that will actually run
    if task == 'health':
        action = getattr(main_mod, 'scheduled_health_check')
    elif task == 'backup':
        google_drive_choice = click.confirm(
            "Do you want to backup data to Google Drive?",
            default=False
        )
        if google_drive_choice:
            login_email = getattr(main_mod, 'current_user', {}).get('email') if hasattr(main_mod, 'current_user') else None
            prompt_fn = getattr(main_mod, '_prompt_google_drive_email', None)
            if callable(prompt_fn):
                google_drive_email = prompt_fn(login_email)
            else:
                google_drive_email = click.prompt("Enter email to use for Google Drive backup").strip()
        scheduled_backup = getattr(main_mod, 'scheduled_backup')
        action = lambda sources=tuple(backup_sources or []), gd=google_drive_choice, ge=google_drive_email: scheduled_backup(list(sources), use_google_drive=gd, drive_email=ge)  # type: ignore[assignment]
    elif task == 'cleanup':
        scheduled_cleanup = getattr(main_mod, 'scheduled_cleanup')
        action = lambda folder=folder: scheduled_cleanup(folder)  # type: ignore[assignment]
    else:  # report
        scheduled_log_analysis = getattr(main_mod, 'scheduled_log_analysis')
        action = lambda log_path=log_path: scheduled_log_analysis(log_path)  # type: ignore[assignment]

    task_id = f"{task}_{frequency}_{int(time.time())}"
    # 'weeks' unit is not supported, so use days with interval=7 for weekly
    interval = 7 if frequency == 'weekly' else 1
    scheduler.add_task(
        task_id,
        action,
        interval=interval,
        unit='days',  # always use 'days' as base unit
        at_time=time_str,
        weekday=weekday,
        day_of_month=day_of_month,
    )

    # persist action metadata so the scheduler can restore and notify users
    try:
        import main as main_mod
        # record who scheduled the task if available
        user_email = getattr(main_mod, 'current_user', {}).get('email') if hasattr(main_mod, 'current_user') else None
    except Exception:
        user_email = None
    if not user_email:
        try:
            from .config import Config
            user_email = Config.EMAIL_RECIPIENT
        except Exception:
            user_email = None

    # build a human-readable schedule description
    schedule_desc = _build_schedule_description(
        frequency,
        time_str,
        weekday=weekday,
        day_of_month=day_of_month,
    )

    # store action metadata on the scheduler task entry
    if task_id in scheduler.tasks:
        action_name_map = {
            'health': 'scheduled_health_check',
            'backup': 'scheduled_backup',
            'cleanup': 'scheduled_cleanup',
            'report': 'scheduled_log_analysis',
        }
        scheduler.tasks[task_id]['action_name'] = action_name_map[task]
        # save the concrete parameters so we can rebuild the wrapper
        if task == 'backup':
            scheduler.tasks[task_id]['action_args'] = [backup_sources or [], schedule_desc, user_email, google_drive_choice, google_drive_email]
        elif task == 'cleanup':
            scheduler.tasks[task_id]['action_args'] = [folder, schedule_desc, user_email]
        elif task == 'report':
            scheduler.tasks[task_id]['action_args'] = [log_path, schedule_desc]
        elif task == 'health':
            scheduler.tasks[task_id]['action_args'] = [schedule_desc]
        else:
            scheduler.tasks[task_id]['action_args'] = []
        scheduler.tasks[task_id]['action_kwargs'] = {}
        if user_email:
            scheduler.tasks[task_id]['user_email'] = user_email
        # save metadata to disk
        try:
            scheduler._save_task_metadata(task_id)
        except Exception:
            logger.debug("Failed to persist interactive schedule metadata")

    if task == 'backup':
        click.secho(
            f"✅ Scheduled '{task}' for {len(backup_sources or [])} item(s) ({frequency} at {time_str})",
            fg='green'
        )
    else:
        click.secho(f"✅ Scheduled '{task}' ({frequency} at {time_str})", fg='green')
    scheduler.start()

# ...... ..Sheduler Menu..........
def scheduler_menu(scheduler: TaskScheduler) -> None:
    import click
    while True:
        click.secho("\n sheduler Menu ", fg="cyan", bold=True)
        click.echo("1. shedule Task")
        click.echo("2. View Scheduled Tasks")
        click.echo("3. Edit Scheduled Tasks")
        click.echo("4. Remove task")
        click.echo("5. Back")
        
        choice = click.prompt(" select an option (1-5)", type=int)
        if choice == 1 :
            interactive_schedule(scheduler)
        elif choice == 2:
            view_tasks(scheduler)
        elif choice == 3:
            interactive_edit_task(scheduler)
        elif choice == 4:
            interactive_remove_task(scheduler)
        elif choice == 5:
            break
        else:
            click.secho("Invalid option!", fg="red")
