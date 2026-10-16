"""Explicit, bounded reuse of file digests; never cache a validator verdict.

Observer, transition and postclose CLIs opt in. Postclose reuse is memory-only
and ends with the invocation; it never loads or publishes a digest store.
All semantic checks,
file discovery and publication still run. Default library callers do full
native validation. Metadata trust is limited to local, same-owner storage;
this is not protection against an administrator changing the filesystem.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import resource
import stat
import tempfile
import time
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ACTIVE = ContextVar('explicit_validation_digest_session', default=None)
MIN_BYTES = 1024 * 1024
MAX_BYTES = 512 * 1024
MAX_ENTRIES = 4096
MAX_GENERATIONS = 32
KST = ZoneInfo('Asia/Seoul')


class ValidationDeferred(Exception):
    """Resource contention, not a policy/source verdict."""


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _sha(value):
    return hashlib.sha256(_encode(value)).hexdigest()


def _thread_io():
    # Thread counters avoid inherited/reaped child I/O double counting.
    import threading
    try:
        fields = dict(line.split(':', 1) for line in Path(
            f'/proc/self/task/{threading.get_native_id()}/io').read_text().splitlines())
        return {k:int(fields[k]) for k in ('rchar', 'read_bytes', 'write_bytes')}
    except (OSError, KeyError, ValueError):
        return None


def _local_filesystem(path):
    resolved = Path(path).resolve()
    matches = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        before, after = line.split(' - ', 1)
        mount = before.split()[4]
        for encoded, actual in ((r'\040',' '),(r'\011','\t'),(r'\134','\\')):
            mount = mount.replace(encoded,actual)
        if resolved.is_relative_to(mount):
            matches.append((len(mount), after.split()[0]))
    return bool(matches) and max(matches)[1] in {'ext2','ext3','ext4','xfs','btrfs','tmpfs','overlay'}


def identity(path):
    """File and lexical ancestry, including symlink replacement and permission."""
    path = Path(path).absolute()
    resolved = path.resolve(strict=True)
    s = resolved.stat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('digest_source_not_regular')
    parents = []
    for node in (path, *path.parents, *resolved.parents):
        item = node.lstat()
        row = [str(node), item.st_dev, item.st_ino, item.st_mode, item.st_uid]
        if stat.S_ISLNK(item.st_mode):
            row += [item.st_ctime_ns, os.readlink(node)]
        parents.append(row)
    return [str(path), str(resolved), s.st_dev, s.st_ino, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns, s.st_mode, s.st_uid, parents]


@contextmanager
def bounded_lock(path, seconds=2, *, private=True):
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or (private and s.st_mode & 0o077):
            raise ValueError('digest_lock_untrusted')
        end = time.monotonic() + seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= end:
                    raise ValidationDeferred('validation_deferred:resource_wait')
                time.sleep(min(0.05, max(0, end-time.monotonic())))
        yield
    finally:
        os.close(fd)


class DigestSession:
    def __init__(self, data_root, day, *, role, generation, ttl=None):
        if role not in {'observer', 'transition', 'postclose'}:
            raise ValueError('digest_role_invalid')
        if datetime.fromisoformat(day).date().isoformat() != day:
            raise ValueError('digest_date_invalid')
        self.ttl = {'observer': 21600, 'transition': 120, 'postclose': 600}[role]
        if ttl is not None:
            self.ttl = min(self.ttl, ttl)
        self.data_root = Path(data_root).absolute()
        self.directory = self.data_root/'runtime/validation_digests'/role
        self.binding = dict(schema='validation_file_digests_v1', role=role, day=day,
            lexical_root=str(self.data_root), resolved_root=str(self.data_root.resolve(strict=role != 'postclose')),
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), generation=generation)
        if role == 'postclose':
            self.binding['pid'] = os.getpid()
        self.key = _sha(self.binding)
        self.path = self.directory/(self.key+'.json')
        self.entries = {}
        self._loaded_entries_sha = None
        self.stats = dict(full_reads=0, full_bytes=0, reused_reads=0, reused_bytes=0,
                          cache_status='unused', role=role, generation_sha256=self.key,
                          pid=os.getpid(), wall_seconds=0.0, thread_io_delta=None)

    def _prepare(self):
        if not _local_filesystem(self.data_root):
            raise ValueError('digest_storage_not_local')
        base = self.data_root/'runtime'
        base.mkdir(parents=True, exist_ok=True)
        for p in (base/'validation_digests', self.directory):
            p.mkdir(mode=0o700, exist_ok=True)
            s = p.lstat()
            if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.getuid() or s.st_mode & 0o077:
                raise ValueError('digest_directory_untrusted')
        if self.directory.resolve() != self.data_root.resolve()/'runtime/validation_digests'/self.binding['role']:
            raise ValueError('digest_directory_alias_rejected')

    def _load(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            with os.fdopen(fd, 'rb') as stream:
                s = os.fstat(stream.fileno())
                if s.st_uid != os.getuid() or s.st_mode & 0o077 or not stat.S_ISREG(s.st_mode) or s.st_size > MAX_BYTES:
                    raise ValueError('digest_entry_untrusted')
                value = json.loads(stream.read(MAX_BYTES+1))
            payload = value['payload']
            if value['sha256'] != _sha(payload) or payload['binding'] != self.binding:
                raise ValueError('digest_entry_binding_invalid')
            entries = payload['entries']
            if not isinstance(entries, dict) or len(entries) > MAX_ENTRIES:
                raise ValueError('digest_entry_limit')
            self.entries = entries
            self._loaded_entries_sha = _sha(entries)
            self.stats['cache_status'] = 'loaded'
        except (OSError, ValueError, KeyError, TypeError):
            self.stats['cache_status'] = 'cold_or_invalid'
            self.entries = {}
            self._loaded_entries_sha = None

    def digest(self, path):
        if self.binding['role'] == 'postclose' and self.binding['pid'] != os.getpid():
            return None  # A fork cannot inherit invocation-local digest authority.
        path = Path(path).absolute()
        before = identity(path)
        if before[4] < MIN_BYTES:
            return None
        # Only native data dependencies. Code and control-plane small files are
        # read normally; optional file discovery is never memoized.
        if (not Path(before[1]).is_relative_to(self.data_root.resolve())
                or before[2] != self.data_root.stat().st_dev):
            return None
        key = str(path)
        now = time.time()
        entry = self.entries.get(key, {})
        if (isinstance(entry, dict) and entry.get('identity') == before
                and isinstance(entry.get('created'), (int, float))
                and 0 <= now-entry['created'] <= self.ttl
                and re.fullmatch('[0-9a-f]{64}', str(entry.get('digest', '')))):
            if identity(path) != before:
                raise ValueError('digest_source_changed')
            self.stats['reused_reads'] += 1
            self.stats['reused_bytes'] += before[4]
            return entry['digest']
        with path.open('rb') as stream:
            observed = hashlib.file_digest(stream, 'sha256').hexdigest()
        if identity(path) != before:
            raise ValueError('digest_source_changed')
        self.stats['full_reads'] += 1
        self.stats['full_bytes'] += before[4]
        if len(self.entries) < MAX_ENTRIES or key in self.entries:
            self.entries[key] = dict(identity=before, digest=observed, created=now)
        return observed

    def _save(self):
        now = time.time()
        self.entries = {k:v for k,v in self.entries.items() if isinstance(v, dict)
                        and isinstance(v.get('created'), (int,float)) and 0 <= now-v['created'] <= self.ttl}
        if self._loaded_entries_sha == _sha(self.entries):
            return  # A warm read must not introduce periodic fsync writes.
        payload = dict(binding=self.binding, entries=self.entries)
        raw = _encode(dict(payload=payload, sha256=_sha(payload)))
        if len(raw) > MAX_BYTES:
            self.stats['cache_status'] = 'size_limit_full_fallback'
            return
        fd, name = tempfile.mkstemp(dir=self.directory, prefix='.digest-')
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(raw); out.flush(); os.fsync(out.fileno())
            os.replace(name, self.path)
            fd = os.open(self.directory, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            Path(name).unlink(missing_ok=True)
        # Only publication/retention holds the role-wide lock. Never delete a lock.
        files = sorted((p for p in self.directory.glob('*.json')
                        if re.fullmatch('[0-9a-f]{64}.json', p.name) and not p.is_symlink()),
                       key=lambda p:p.stat().st_mtime_ns, reverse=True)
        for p in files[MAX_GENERATIONS:]:
            p.unlink(missing_ok=True)

    @contextmanager
    def activate(self):
        if self.binding['role'] == 'postclose':
            # A new postclose invocation must not inherit a persistent observer
            # or transition cache. Nested native checks share this invocation.
            active = ACTIVE.get()
            if (active is not None and active.binding == self.binding):
                yield active
                return
            try:
                local = self.data_root.is_dir() and _local_filesystem(self.data_root)
            except (OSError, ValueError):
                local = False
            if not local:
                self.stats['cache_status'] = 'storage_unavailable_full_fallback'
                token = ACTIVE.set(None)
                try:
                    yield self
                finally:
                    ACTIVE.reset(token)
                return
            self.stats['cache_status'] = 'invocation_memory_only'
            with self._measure_active():
                try:
                    yield self
                finally:
                    self.entries.clear()
            return
        active = ACTIVE.get()
        if active is not None and active.binding['role'] != 'postclose':
            yield active
            return
        try:
            self._prepare()
        except (OSError, ValueError):
            self.stats['cache_status'] = 'storage_unavailable_full_fallback'
            yield self
            return
        with ExitStack() as stack:
            try:
                stack.enter_context(bounded_lock(self.directory/(self.key+'.lock')))
            except (OSError, ValueError):
                self.stats['cache_status'] = 'lock_unavailable_full_fallback'
                yield self
                return
            self._load()
            with self._measure_active():
                try:
                    yield self
                finally:
                    try:
                        with bounded_lock(self.directory/'store.lock'):
                            self._save()
                    except (OSError, ValueError, TypeError, ValidationDeferred):
                        self.stats['cache_status'] = 'publication_failed_no_persistent_reuse'

    @contextmanager
    def _measure_active(self):
        token = ACTIVE.set(self)
        started, io_before = time.monotonic(), _thread_io()
        try:
            yield
        finally:
            ACTIVE.reset(token)
            self.stats['wall_seconds'] += time.monotonic()-started
            self.stats['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            after = _thread_io()
            if io_before is not None and after is not None:
                prior = self.stats['thread_io_delta'] or dict.fromkeys(after,0)
                self.stats['thread_io_delta'] = {k:prior[k]+after[k]-io_before[k] for k in after}


def reused_digest(path):
    session = ACTIVE.get()
    return session.digest(path) if session is not None else None


@contextmanager
def postclose_session(data_root, day):
    """Share content digests, never validator verdicts, within one invocation."""
    with DigestSession(data_root, day, role='postclose', generation={}).activate() as session:
        yield session


def code_generation():
    root = Path(__file__).resolve().parents[3]
    files = ['src/engine/infrastructure/validation_digest_session.py',
             'src/engine/scalping/mechanistic_entry_runtime_policy.py',
             'src/engine/scalping/continuous_reversal_postclose.py',
             'src/engine/lifecycle/holding_window_generation.py',
             'src/engine/automation/runtime_policy_bootstrap.py',
             'src/engine/automation/intraday_release_handoff.py',
             'src/engine/monitoring/submission_bottleneck_monitor.py']
    return dict(root=str(root), code={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files})


@contextmanager
def transition_session(data_root, day, session_id=None, pid=None):
    if session_id is None:
        yield None
        return
    if not re.fullmatch('[0-9a-f]{32}', session_id):
        raise ValueError('validation_session_id_invalid')
    generation = dict(code=code_generation(), transition=session_id, phase='prestart')
    if pid is not None:
        proc = Path('/proc')/str(int(pid))
        generation.update(phase='post_launch', pid=int(pid), cwd=str((proc/'cwd').resolve(strict=True)),
                          start=proc.joinpath('stat').read_text().rsplit(')',1)[1].split()[19])
    with DigestSession(data_root, day, role='transition', generation=generation).activate() as session:
        yield session
