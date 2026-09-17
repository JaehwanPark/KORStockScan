"""Optional research cache LRU with live-process pins and bounded disk receipts."""

from collections import OrderedDict
from datetime import datetime
from threading import RLock
import os
from pathlib import Path
import shutil
import stat
import tempfile
import time
from src.engine.monitoring import research_closed_loop as loop


def _identity(pid):
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
        return [
            Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            raw.rsplit(")", 1)[1].split()[19],
        ]
    except FileNotFoundError:
        return None
    except OSError:
        return ["unreadable"]


def _safe(root, path):
    try:
        relative = path.absolute().relative_to(root.absolute())
    except ValueError:
        return False
    if ".." in relative.parts or root.is_symlink():
        return False
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return False
    return path.name.endswith(".json.z")


_PINNED = set()


def _open_catalog(root):
    import sqlite3

    database = root / ".optional_cache_catalog.sqlite3"
    if any(
        Path(str(database) + suffix).is_symlink()
        for suffix in ("", "-journal", "-wal", "-shm")
    ):
        raise ValueError("optional_cache_catalog_symlink")
    root.mkdir(parents=True, exist_ok=True)
    fd = os.open(database, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    before = os.fstat(fd)
    try:
        db = sqlite3.connect(database, timeout=5, check_same_thread=False)
        after = database.lstat()
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            db.close()
            raise ValueError("optional_cache_catalog_changed")
    finally:
        os.close(fd)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS entries (path TEXT PRIMARY KEY, size INTEGER NOT NULL, access_ns INTEGER NOT NULL, scope TEXT NOT NULL)"
        )
        db.execute("CREATE INDEX IF NOT EXISTS cache_lru ON entries(access_ns)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS pins (scope TEXT, pid INTEGER, identity TEXT, persistent INTEGER DEFAULT 0, PRIMARY KEY(scope,pid))"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value INTEGER)"
        )
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        boot_row = db.execute(
            "SELECT value FROM metadata WHERE key='boot_id'"
        ).fetchone()
        if boot_row is None or boot_row[0] != boot:
            # Optional bytes are re-inventoried after a host reboot. NORMAL WAL
            # survives process TERM; power-loss cache loss is only a safe miss.
            db.execute("DELETE FROM entries")
            for existing in root.rglob("*.json.z"):
                if _safe(root, existing):
                    info = existing.lstat()
                    if stat.S_ISREG(info.st_mode):
                        key = str(existing.absolute().relative_to(root.absolute()))
                        db.execute(
                            "INSERT OR REPLACE INTO entries VALUES (?,?,?,?)",
                            (
                                key,
                                info.st_size,
                                info.st_mtime_ns,
                                str(Path(key).parent),
                            ),
                        )
            db.execute("INSERT OR REPLACE INTO metadata VALUES ('initialized',1)")
            db.execute("INSERT OR REPLACE INTO metadata VALUES ('boot_id', ?)", (boot,))
            db.execute(
                "INSERT OR REPLACE INTO metadata VALUES ('charged_bytes', (SELECT COALESCE(SUM(size),0) FROM entries))"
            )
            db.commit()
    except Exception:
        db.close()
        raise
    return db


class _Catalog:
    def __init__(self, connection):
        self.connection = connection
        self.borrowers = 1
        self.pooled = False

    def execute(self, *args):
        import sqlite3

        try:
            return self.connection.execute(*args)
        except sqlite3.Error as exc:
            raise ValueError("optional_cache_catalog_invalid") from exc

    def commit(self):
        import sqlite3

        try:
            self.connection.commit()
        except sqlite3.Error as exc:
            raise ValueError("optional_cache_catalog_commit_failed") from exc

    def close(self):
        with _POOL_LOCK:
            self.borrowers -= 1
            if not self.pooled:
                self.release()

    def release(self):
        self.connection.close()


_DATABASES = OrderedDict()
_POOL_LOCK = RLock()
_FULL_ROOTS = set()


def _catalog(root):
    import sqlite3

    key = (str(root.absolute()), os.getpid())
    database = root / ".optional_cache_catalog.sqlite3"
    with _POOL_LOCK:
        cached = _DATABASES.get(key)
        if cached is not None:
            info = database.lstat()
            if (
                any(
                    Path(str(database) + suffix).is_symlink()
                    for suffix in ("", "-journal", "-wal", "-shm")
                )
                or (info.st_dev, info.st_ino) != cached[0]
            ):
                raise ValueError("optional_cache_catalog_replaced")
            _DATABASES.move_to_end(key)
            cached[1].borrowers += 1
            return cached[1]
        try:
            connection = _open_catalog(root)
        except sqlite3.Error as exc:
            raise ValueError("optional_cache_catalog_invalid") from exc
        info = database.lstat()
        value = _Catalog(connection)
        if len(_DATABASES) >= 8:
            for old_key, (_, old) in list(_DATABASES.items()):
                if old.borrowers == 0:
                    _DATABASES.pop(old_key)
                    old.release()
                    break
        if len(_DATABASES) < 8:
            value.pooled = True
            _DATABASES[key] = (info.st_dev, info.st_ino), value
        return value


def _pin(db, scope):
    import json

    db.execute(
        "INSERT OR REPLACE INTO pins(scope,pid,identity) VALUES (?,?,?)",
        (scope, os.getpid(), json.dumps(_identity(os.getpid()))),
    )


def touch(path, *, root):
    """Pin one reader scope once; later reads avoid catalog I/O entirely."""
    root, path = Path(root), Path(path)
    if not _safe(root, path):
        return False
    scope = str(path.parent.absolute().relative_to(root.absolute()))
    key = (str(root.absolute()), scope, os.getpid())
    if key in _PINNED:
        return True
    try:
        with loop.writer_lock(root):
            db = _catalog(root)
            try:
                if (
                    db.execute(
                        "SELECT 1 FROM entries WHERE path=?",
                        (str(path.absolute().relative_to(root.absolute())),),
                    ).fetchone()
                    is None
                ):
                    return False
                _pin(db, scope)
                db.execute(
                    "UPDATE entries SET access_ns=? WHERE scope=?",
                    (time.time_ns(), scope),
                )
                db.commit()
            finally:
                db.close()
        if len(_PINNED) >= 8192:
            _PINNED.clear()
        _PINNED.add(key)
        return True
    except (OSError, ValueError, TypeError):
        return False


def write(path, raw, *, cache_root, soft_cap, reserve):
    import json

    root, path = Path(cache_root), Path(path)
    if not _safe(root, path):
        raise ValueError("optional_cache_scope_or_symlink_invalid")
    full_key = (str(root.absolute()), os.getpid(), soft_cap)
    if full_key in _FULL_ROOTS and not path.exists():
        return False
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free - len(raw) < reserve:
        return False
    with loop.writer_lock(root):
        db = _catalog(root)
        try:
            key = str(path.absolute().relative_to(root.absolute()))
            scope = str(Path(key).parent)
            current = path.lstat() if path.exists() else None
            if current and not stat.S_ISREG(current.st_mode):
                return False
            old_size = db.execute(
                "SELECT size FROM entries WHERE path=?", (key,)
            ).fetchone()
            old_size = old_size[0] if old_size else 0
            charge_row = db.execute(
                "SELECT value FROM metadata WHERE key='charged_bytes'"
            ).fetchone()
            if charge_row is None:
                charged = db.execute(
                    "SELECT COALESCE(SUM(size),0) FROM entries"
                ).fetchone()[0]
            else:
                charged = charge_row[0]
            if type(charged) is not int or charged < 0:
                return False
            needed = charged + max(0, len(raw) - old_size) - soft_cap
            victims, reclaimed = [], 0
            if needed > 0:
                pinned = set()
                identities = {}
                for group, pid, identity, persistent in db.execute(
                    "SELECT scope,pid,identity,persistent FROM pins"
                ):
                    if pid not in identities:
                        identities[pid] = _identity(pid)
                    if (
                        persistent
                        or identities[pid] == json.loads(identity)
                        or identities[pid] == ["unreadable"]
                    ):
                        pinned.add(group)
                for name, size, group in db.execute(
                    "SELECT path,size,scope FROM entries ORDER BY access_ns"
                ):
                    target = root / name
                    if name == key or group in pinned or not _safe(root, target):
                        continue
                    try:
                        info = target.lstat()
                    except FileNotFoundError:
                        info = None
                    if info is not None and (
                        not stat.S_ISREG(info.st_mode) or info.st_size != size
                    ):
                        continue
                    victims.append((name, target, size, info))
                    reclaimed += size
                    if reclaimed >= needed:
                        break
                if reclaimed < needed:
                    if len(_FULL_ROOTS) >= 64:
                        _FULL_ROOTS.clear()
                    _FULL_ROOTS.add(full_key)
                    return False
                for name, target, size, info in victims:
                    if info is not None:
                        now = target.lstat()
                        if (
                            now.st_dev,
                            now.st_ino,
                            now.st_size,
                            now.st_mtime_ns,
                            now.st_ctime_ns,
                        ) != (
                            info.st_dev,
                            info.st_ino,
                            info.st_size,
                            info.st_mtime_ns,
                            info.st_ctime_ns,
                        ):
                            return False
                for name, target, size, info in victims:
                    if info is not None:
                        target.unlink()
                    db.execute("DELETE FROM entries WHERE path=?", (name,))
                    charged -= size
            _pin(db, scope)
            db.execute(
                "INSERT OR REPLACE INTO entries VALUES (?,?,?,?)",
                (key, len(raw), time.time_ns(), scope),
            )
            db.execute(
                "INSERT OR REPLACE INTO metadata VALUES ('charged_bytes', ?)",
                (charged - old_size + len(raw),),
            )
            # Commit reservation first; interruption is conservatively charged.
            db.commit()
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".day-cache-", dir=path.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                os.replace(temporary, path)
                ledger_path = root / ".optional_cache_bytes.json"
                try:
                    ledger = loop.read_object(ledger_path)
                except (OSError, ValueError, RecursionError):
                    ledger = {}
                # This JSON is optional telemetry; SQLite owns the byte charge.
                ledger = {
                    name: ledger[name]
                    for name in ("evicted_bytes", "written_bytes")
                    if type(ledger.get(name)) is int and ledger[name] >= 0
                }
                ledger.update(
                    schema=loop.SCHEMA,
                    charged_bytes=charged - old_size + len(raw),
                    evicted_bytes=ledger.get("evicted_bytes", 0) + reclaimed,
                    written_bytes=ledger.get("written_bytes", 0) + len(raw),
                    updated_at=datetime.now().astimezone().isoformat(),
                )
                # Optional metadata is atomic, not a durable policy receipt.
                _atomic_optional_metadata(ledger_path, ledger)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        finally:
            db.close()
    return True


def _atomic_optional_metadata(path, value):
    import json

    fd, temporary = tempfile.mkstemp(prefix=".cache-bytes-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, sort_keys=True, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def capacity_receipt(directory, source_date, report_root):
    """Stat only this loop's facts/reports; never scan growing raw contents."""
    root, report_root = Path(directory), Path(report_root)
    raw = sum(
        p.lstat().st_size
        for p in (root / "facts").glob(f"*{source_date:%Y%m%d}*")
        if not p.is_symlink() and p.is_file()
    )
    projection = sum(
        p.lstat().st_size
        for p in root.glob(f"*{source_date}*.json")
        if not p.is_symlink() and p.is_file()
    )
    reports = 0
    for family in (
        "widget_symbol_signal_policy_research",
        "low_price_two_leg_expanded_candidate_research",
        "machine_research_closed_loop",
    ):
        reports += sum(
            p.lstat().st_size
            for p in (report_root / family).glob(f"*{source_date}*")
            if not p.is_symlink() and p.is_file()
        )
    try:
        ledger = loop.read_object(
            root / "cache" / ".optional_cache_bytes.json", limit=16 * 1024**2
        )
    except (FileNotFoundError, ValueError):
        ledger = {}
    cache_bytes = ledger.get("charged_bytes", 0)
    free = shutil.disk_usage(root).free
    daily = raw + projection + reports
    return dict(
        scope="additional_closed_loop_research_storage_metadata_only",
        source_date=str(source_date),
        daily_native_bytes=daily,
        raw_bytes=raw,
        projection_bytes=projection,
        cache_bytes=cache_bytes,
        report_bytes=reports,
        available_bytes=free,
        optional_cache_soft_cap_bytes=2 * 1024**3,
        free_reserve_bytes=10 * 1024**3,
        reserve_passed=free >= 10 * 1024**3,
        cache_evicted_bytes=ledger.get("evicted_bytes", 0),
        source_retention="existing_retention_unchanged_no_finite_retention_override",
        forecast_horizon_days=30,
        forecast_additional_bytes_at_current_daily_rate=daily * 30,
        forecast_basis="same_daily_growth_scenario_not_measured_future_growth",
        **loop.AUTHORITY,
    )


def read(path, *, root, max_bytes=32 * 1024**2):
    """Bounded decode while the reader is pinned; optional errors are misses."""
    import json
    import zlib

    path, root = Path(path), Path(root)
    if not touch(path, root=root):
        return None
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            raw = handle.read(max_bytes + 1)
            opened = os.fstat(handle.fileno())
        after = path.lstat()
        identity = lambda info: (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        )
        if identity(before) != identity(opened) or identity(before) != identity(after):
            return None
        decoder = zlib.decompressobj()
        raw = decoder.decompress(raw, max_bytes)
        if not decoder.eof or decoder.unused_data:
            return None
        return json.loads(raw)
    except (OSError, ValueError, RecursionError, zlib.error):
        return None


def pin_persistent_paths(root, paths):
    """Explicit optional live/rollback references remain protected until released."""
    import json

    root = Path(root)
    with loop.writer_lock(root):
        db = _catalog(root)
        try:
            for path in paths:
                path = Path(path)
                if not _safe(root, path):
                    raise ValueError("optional_persistent_pin_scope_invalid")
                scope = str(path.parent.absolute().relative_to(root.absolute()))
                db.execute(
                    "INSERT OR REPLACE INTO pins VALUES (?,?,?,1)",
                    (scope, 0, json.dumps(None)),
                )
            db.commit()
        finally:
            db.close()
