"""Single consumption of an operator Main restart flag across bot threads."""
import fcntl
from pathlib import Path
from src.utils.constants import PROJECT_ROOT


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
