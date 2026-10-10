"""One resident-data budget shared by local postclose research families.

Claims cover raw plus a conservative Python decode/feature expansion. They
are process-local data accounting, not a new worker, provider quota or policy
approval. Overflow requests sealed partitions/checkpoints explicitly.
"""
import threading

LIMIT_BYTES = 64 * 1024 * 1024
_LOCK = threading.Lock()
_USED = 0


class Claim:
    def __init__(self, size):
        global _USED
        self.size = 0
        if type(size) is not int or size < 0:
            raise ValueError('research_input_claim_invalid')
        with _LOCK:
            if _USED + size > LIMIT_BYTES:
                raise ValueError('shared_research_budget_partition_resume_required')
            _USED += size
            self.size = size

    def close(self):
        global _USED
        with _LOCK:
            _USED -= self.size
            self.size = 0

    def grow(self, size):
        """Admit the next streaming index/row before retaining it."""
        global _USED
        if type(size) is not int or size < 0:
            raise ValueError('research_input_claim_invalid')
        with _LOCK:
            if _USED + size > LIMIT_BYTES:
                raise ValueError('shared_research_budget_partition_resume_required')
            _USED += size
            self.size += size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


def health():
    with _LOCK:
        return {'used_bytes':_USED, 'limit_bytes':LIMIT_BYTES}
