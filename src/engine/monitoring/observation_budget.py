"""Bound one observer's computation; never alter a trading process deadline."""

from contextlib import contextmanager
import signal
import threading
import time


class ObservationDeadline(BaseException):
    """Do not let a permissive source parser turn timeout into empty evidence."""


@contextmanager
def computation_budget(deadline):
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("observer_budget_requires_main_thread")
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise RuntimeError("observer_budget_timer_already_owned")

    def expired(signum, frame):
        raise ObservationDeadline("validation_deferred:deadline")

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ObservationDeadline("validation_deferred:deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
