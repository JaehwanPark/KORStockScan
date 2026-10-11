"""Host admission for postclose research; no runtime or order authority.

Heavy jobs reserve both existing dispatcher slots. Inherited descriptors prove
a dispatcher reservation; an environment flag alone never waives admission.
The caller takes its job writer lock before this resource lock.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import stat
import time
from contextvars import ContextVar

ENV_KEY = 'POSTCLOSE_RESEARCH_RESERVATION'
HEAVY_STAGES = frozenset({'pre_submit_delay', 'main_trailing_all_scope', 'initial_entry_quantity_refresh', 'main_stop_confirmation'})
_LOCAL_OWNER=ContextVar('postclose_research_reservation_owner',default=None)


def start_ticks(pid):
    # The comm field can contain spaces and parentheses.
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]


class Reservation:
    def __init__(self, handles, *, data_root, stage, day):
        self.handles = handles
        self.data_root = Path(data_root).resolve()
        self.stage, self.day = stage, day

    @property
    def pass_fds(self):
        return tuple(handle.fileno() for handle in self.handles)

    def environment(self):
        return {ENV_KEY: json.dumps({
            'schema': 'postclose_research_reservation_v1', 'parent_pid': os.getpid(),
            'parent_start_ticks': start_ticks(os.getpid()), 'stage': self.stage,
            'day': self.day, 'data_root': str(self.data_root),
            'slots': [{'fd': handle.fileno(), 'path': str(Path(handle.name).resolve())}
                      for handle in self.handles]}, separators=(',', ':'))}

    def close(self):
        for handle in self.handles:
            handle.close()
        self.handles.clear()

    @contextmanager
    def worker(self):
        """A synchronous native adapter shares actual dispatcher lock FDs."""
        token=_LOCAL_OWNER.set(self)
        try:yield
        finally:_LOCAL_OWNER.reset(token)


def inherited(data_root, stage, day, *, env=None):
    value = (os.environ if env is None else env).get(ENV_KEY)
    if not value:
        return False
    try:
        value = json.loads(value)
        parent = value['parent_pid']
        slots = value['slots']
        root = Path(data_root).resolve()
        if (value['schema'] != 'postclose_research_reservation_v1'
                or type(parent) is not int or parent != os.getppid()
                or start_ticks(parent) != value['parent_start_ticks']
                or value['data_root'] != str(root) or value['stage'] != stage
                or value['day'] != day or len(slots) != (2 if stage in HEAVY_STAGES else 1)):
            raise ValueError('research_reservation_identity_invalid')
        observed = set()
        for slot in slots:
            fd = slot['fd']
            path = Path(slot['path'])
            if (type(fd) is not int or fd < 3 or path not in {
                    root / 'runtime/postclose_stage_slots' / f'{n}.lock' for n in range(2)}
                    or path in observed or path.is_symlink()):
                raise ValueError('research_reservation_descriptor_invalid')
            observed.add(path)
            current = os.fstat(fd)
            original = Path(f'/proc/{parent}/fd/{fd}').stat()
            disk = path.stat()
            if (not stat.S_ISREG(current.st_mode) or
                    (current.st_dev, current.st_ino) != (disk.st_dev, disk.st_ino)
                    or (original.st_dev, original.st_ino) != (disk.st_dev, disk.st_ino)):
                raise ValueError('research_reservation_descriptor_invalid')
            with path.open('a+b') as probe:
                try:
                    fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                raise ValueError('research_reservation_lock_not_held')
        return True
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise ValueError('research_reservation_unverified') from exc


def acquire(data_root, stage, day):
    """One nonblocking attempt. Never wait while holding a subset of slots."""
    directory = Path(data_root).resolve() / 'runtime/postclose_stage_slots'
    if directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
        raise ValueError('research_admission_path_invalid')
    directory.mkdir(parents=True, exist_ok=True)
    weight = 2 if stage in HEAVY_STAGES else 1
    handles = []
    try:
        for n in range(2):
            path = directory / f'{n}.lock'
            if path.is_symlink():
                raise ValueError('research_admission_path_invalid')
            handle = path.open('a+b')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                if weight == 2:
                    return None
                continue
            handles.append(handle)
            if len(handles) == weight:
                result = Reservation(handles, data_root=data_root, stage=stage, day=day)
                handles = []
                return result
        return None
    finally:
        for handle in handles:
            handle.close()


@contextmanager
def direct_job(data_root, stage, day, *, timeout=60):
    """Direct CLI/profile uses dispatcher writer -> slots order."""
    local=_LOCAL_OWNER.get()
    if local is not None:
        if (local.data_root!=Path(data_root).resolve() or local.stage!=stage or local.day!=day
            or len(local.handles)!=(2 if stage in HEAVY_STAGES else 1)):
            raise ValueError('research_local_owner_identity_invalid')
        names={Path(handle.name).resolve() for handle in local.handles}
        expected={local.data_root/'runtime/postclose_stage_slots'/f'{n}.lock' for n in range(2)}
        if len(names)!=len(local.handles) or not names.issubset(expected):
            raise ValueError('research_local_owner_descriptor_invalid')
        for handle in local.handles:
            actual=os.fstat(handle.fileno());disk=Path(handle.name).stat()
            if (actual.st_dev,actual.st_ino)!=(disk.st_dev,disk.st_ino):
                raise ValueError('research_local_owner_descriptor_invalid')
            with Path(handle.name).open('a+b') as probe:
                try:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                raise ValueError('research_local_owner_lock_not_held')
        yield;return
    if inherited(data_root, stage, day):
        yield
        return
    root = Path(data_root).resolve()
    writer = root / 'report/postclose_stage_terminal' / day / f'{stage}.lock'
    if writer.is_symlink() or any(p.is_symlink() for p in writer.parents):
        raise ValueError('research_writer_path_invalid')
    writer.parent.mkdir(parents=True, exist_ok=True)
    with writer.open('a+b') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('research_existing_stage_writer') from exc
        deadline = time.monotonic() + timeout
        reservation = acquire(root, stage, day)
        while reservation is None and time.monotonic() < deadline:
            time.sleep(min(.25, max(0, deadline-time.monotonic())))
            reservation = acquire(root, stage, day)
        if reservation is None:
            raise ValueError('research_resource_admission_timeout')
        try:
            yield
        finally:
            reservation.close()
