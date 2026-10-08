"""One original reversal budget; no admission, policy or order authority."""
from dataclasses import dataclass
import math
import time


def claim_deadline_epoch(claim):
    if claim is None:
        return None
    try:
        epoch = claim['snapshot'][0]['epoch']
        if isinstance(epoch, bool) or not math.isfinite(float(epoch)):
            return 0.0
        return float(epoch) + 5.0
    except (KeyError, TypeError, IndexError, ValueError):
        return 0.0  # Malformed input cannot acquire a renewed budget.


@dataclass(frozen=True)
class EntryDeadline:
    epoch: float
    perf: float

    @classmethod
    def create(cls, claim=None, caller_epoch=None, caller_perf=None):
        values = [v for v in (claim_deadline_epoch(claim), caller_epoch) if v is not None]
        if not values:
            return None
        if any(isinstance(v, bool) or not math.isfinite(float(v)) for v in values):
            raise ValueError('entry_machine_input_deadline_invalid')
        epoch = min(map(float, values))
        now = time.time()
        # Source wall-clock validity remains the native validator's job.
        perf = time.perf_counter() + max(0.0, epoch - now)
        if caller_perf is not None:
            if isinstance(caller_perf, bool) or not math.isfinite(float(caller_perf)):
                raise ValueError('entry_machine_input_deadline_invalid')
            perf = min(perf, float(caller_perf))
        return cls(epoch, perf)

    def remaining(self):
        return max(0.0, min(self.epoch - time.time(), self.perf - time.perf_counter()))

    def require(self):
        if self.remaining() <= 0:
            raise ValueError('entry_machine_input_deadline_expired')

    def transport_ms(self, existing_ms, reserve_sec=0.0):
        # No minimum timeout may enlarge the remaining claim budget.
        value = int(min(float(existing_ms), (self.remaining() - reserve_sec) * 1000))
        if value < 1:
            raise ValueError('entry_machine_input_deadline_expired')
        return value
