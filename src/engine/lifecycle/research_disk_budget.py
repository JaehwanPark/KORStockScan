"""Task-local peak disk reservations for offline research generations.

Reservations include concurrent disposable databases and atomic old/new files.
Referenced evidence is never evicted to admit another job.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_CURRENT=ContextVar('research_disk_budget',default=None)
LIMIT=4*1024*1024*1024
INDEX_LIMIT=512*1024*1024


class Budget:
    def __init__(self,root,*,durable_limit=LIMIT,temp_limit=LIMIT):
        self.root=Path(root).resolve();self.durable_limit=durable_limit;self.temp_limit=temp_limit
        self.durable_bytes=0;self.temp_reserved=0;self.atomic_reserved=0;self.peak_reserved=0
        self.seen={}
        self.include(self.root)
    def include(self,root):
        for path in Path(root).resolve().rglob('*'):
            if path.is_symlink(): raise ValueError('research_disk_symlink_invalid')
            if path.is_file() and str(path) not in self.seen:
                self.seen[str(path)]=path.stat().st_size;self.durable_bytes+=path.stat().st_size
        self._check()
    def _check(self):
        if self.durable_bytes>self.durable_limit or self.temp_reserved+self.atomic_reserved>self.temp_limit:
            raise ValueError('research_combined_disk_budget_exceeded')
        self.peak_reserved=max(self.peak_reserved,self.durable_bytes+self.temp_reserved+self.atomic_reserved)
    def reclaim_missing(self):
        # Only account deletion already performed by a private temporary-dir
        # owner. This method has no deletion or evidence-eviction authority.
        for name in list(self.seen):
            if not Path(name).exists(): self.durable_bytes-=self.seen.pop(name)
    @contextmanager
    def atomic(self,path,size):
        path=Path(path).resolve();name=str(path)
        if name not in self.seen and path.exists():
            # A shared run may write to a sibling generation/root. Include
            # existing bytes before its old/new atomic replacement as well.
            if path.is_symlink():raise ValueError('research_disk_symlink_invalid')
            self.seen[name]=path.stat().st_size;self.durable_bytes+=self.seen[name]
        previous=self.seen.get(name,0)
        self.atomic_reserved+=size
        # During rename the old file and the full temporary new file coexist.
        try:
            self._check()
            if self.durable_bytes-previous+size>self.durable_limit:
                raise ValueError('research_combined_disk_budget_exceeded')
            yield
            self.durable_bytes+=size-previous;self.seen[name]=size;self._check()
        finally: self.atomic_reserved-=size
    @contextmanager
    def temporary(self,size):
        self.temp_reserved+=size
        try: self._check();yield
        finally: self.temp_reserved-=size


@contextmanager
def use(root,**limits):
    existing=_CURRENT.get()
    if existing is not None:
        existing.include(root)
        yield existing;return
    budget=Budget(root,**limits);token=_CURRENT.set(budget)
    try: yield budget
    finally: _CURRENT.reset(token)


@contextmanager
def atomic(path,size):
    budget=_CURRENT.get()
    if budget is None: yield;return
    with budget.atomic(path,size): yield


@contextmanager
def temporary(size=INDEX_LIMIT):
    budget=_CURRENT.get()
    if budget is None: yield size;return
    with budget.temporary(size): yield size


def reclaim_missing():
    budget=_CURRENT.get()
    if budget is not None: budget.reclaim_missing()
