"""Single consumption of an operator Main restart flag across bot threads."""

import fcntl
from pathlib import Path
from src.utils.constants import PROJECT_ROOT

# Both restart claimants share one cooperative stop; only Main owns process exit.
_SHUTDOWN_REQUESTED = False


def request_shutdown(*_args):
    """Also safe as a Python main-thread SIGTERM handler."""
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True


def shutdown_requested():
    return _SHUTDOWN_REQUESTED


def finish_main_shutdown(engine_thread=None):
    """Wait for the engine's native finally/collector close before summary drain.

    No kill fallback: the ordered driver retains its own bounded stop deadline
    and leaves a failed transition held if a producer cannot finish.
    """
    request_shutdown()
    if engine_thread is not None:
        engine_thread.join()
    from src.utils.pipeline_event_logger import (
        drain_pipeline_event_summary_before_termination,
    )

    drain_pipeline_event_summary_before_termination()


def consume_restart_request(restart_flag_path, *, main_bot_pid, lock_path=None):
    path = Path(restart_flag_path)
    lock_path = Path(lock_path or PROJECT_ROOT / "tmp/main_bot_restart_guard.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if not path.exists():
            return {"claimed": False, "allowed": False, "reason": "flag_absent"}
        request = path.read_text(encoding="utf-8")[:512].strip()
        path.unlink()
        return {"claimed": True, "allowed": True, "request": request}
