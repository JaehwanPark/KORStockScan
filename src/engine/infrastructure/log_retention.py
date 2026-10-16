"""Writer-owned operational log retention, separate from research/raw custody.

Only registered closed generations are mutable. Unknown historical files and
unregistered temporary evidence remain protected. No trading authority.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import math
import stat
import subprocess
import time
import uuid

SCHEMA = "closed_operational_log_v1"
DAY = 86400
MAX_METADATA = 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def signature(path):
    s = Path(path).lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise ValueError("regular_single_link_required")
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def read_json(path):
    path = Path(path)
    signature(path)
    if path.stat().st_size > MAX_METADATA:
        raise ValueError("metadata_size_limit")
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("metadata_object_required")
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp." + uuid.uuid4().hex)
    try:
        with temp.open("x") as out:
            json.dump(value, out, sort_keys=True, allow_nan=False)
            out.write("\n"); out.flush(); os.fsync(out.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def owner_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("lock_not_regular")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def register_generation(active, closed, *, owner, source_sha256=None, archive_sha256=None):
    active, closed = Path(active).absolute(), Path(closed).absolute()
    active = active.parent.resolve(strict=True) / active.name
    closed = closed.parent.resolve(strict=True) / closed.name
    if active.parent != closed.parent or active == closed or not owner:
        raise ValueError("generation_owner_invalid")
    if (active.parent / '.retention').is_symlink():
        raise ValueError('retention_directory_symlink')
    sig = signature(closed)
    value = dict(schema=SCHEMA, owner=owner, active_path=str(active),
                 path=str(closed), signature=sig, closed_at=time.time(),
                 retention_days=30, max_generations=10, max_owner_bytes=200*1024**2,
                 source_sha256=source_sha256, archive_sha256=archive_sha256,
                 state="closed", runtime_effect=False, order_authority=False)
    key = hashlib.sha256(str(closed).encode()).hexdigest()
    atomic_json(active.parent / ".retention" / (key + ".json"), value)
    return value


def close_module_generation(active, *, owner):
    """Called under the module writer's flock, with its stream already closed."""
    active = Path(active)
    if not active.exists():
        return
    signature(active)
    closed = active.with_name(active.name + ".closed_" + uuid.uuid4().hex)
    os.rename(active, closed)
    # A crash before the manifest leaves an unknown protected file, not a loss.
    register_generation(active, closed, owner=owner)


_FD_CENSUS = '''import os, stat, json
from pathlib import Path
result = set()
for process in Path('/proc').iterdir():
    if not process.name.isdigit(): continue
    try:
        for fd in (process/'fd').iterdir():
            try:
                s = fd.stat()
                if stat.S_ISREG(s.st_mode): result.add((s.st_dev,s.st_ino))
            except (FileNotFoundError, ProcessLookupError): pass
    except (FileNotFoundError, ProcessLookupError): pass
print(json.dumps(sorted(result)))
'''


def open_owned_inodes():
    """Read-only all-UID FD census; unreadable descriptors never mean closed."""
    result = set()
    if not Path("/proc").is_dir():
        raise ValueError("proc_inventory_unavailable")
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            for fd in (process / "fd").iterdir():
                try:
                    s = fd.stat(); result.add((s.st_dev, s.st_ino))
                except FileNotFoundError:
                    pass
        except (FileNotFoundError, ProcessLookupError):
            pass
        except PermissionError:
            # Hardened same-UID services can also deny ptrace. Escalate only
            # this constant read-only census, never the cleanup or filenames.
            run = subprocess.run(['sudo', '-n', '/usr/bin/python3', '-c', _FD_CENSUS],
                                 capture_output=True, text=True, timeout=5, check=True)
            rows = json.loads(run.stdout)
            if (len(run.stdout) > MAX_METADATA or not isinstance(rows, list)
                    or any(not isinstance(row,list) or len(row)!=2
                           or any(type(v) is not int or v<0 for v in row) for row in rows)):
                raise ValueError('fd_census_invalid')
            return {tuple(row) for row in rows}
    return result


def retention_pins(workspace):
    path = Path(workspace) / "data/config/log_retention_pins.json"
    if not path.exists() and not path.is_symlink():
        return set()
    obj = read_json(path)
    if obj.get("schema") != "operational_retention_pins_v1":
        raise ValueError("retention_pins_invalid")
    pins = obj.get("pins")
    if not isinstance(pins, list) or any(not isinstance(x, str) or not x for x in pins):
        raise ValueError("retention_pins_invalid")
    return set(pins)


def document_references(workspace, names):
    """Bounded current document scan; overflow protects the entire collection."""
    referenced = set(); total = 0
    for path in (Path(workspace) / "docs").rglob("*.md"):
        if path.is_symlink():
            raise ValueError("document_reference_symlink")
        total += path.stat().st_size
        if total > 128*1024**2:
            raise ValueError("document_reference_scan_limit")
        raw = path.read_text(errors="strict")
        referenced.update(name for name in names if name in raw)
    return referenced


def maintain_logs(workspace, *, apply=False, now=None, time_budget=20):
    workspace = Path(workspace).resolve(); logdir = workspace / "logs"
    now = time.time() if now is None else now
    started = time.monotonic()
    report = dict(schema="operational_log_retention_v1", status="complete", deleted=0,
                  deleted_bytes=0, compressed=0, retained_bytes=0, deferred=[], errors=[],
                  runtime_effect=False, order_authority=False)
    if logdir.is_symlink() or (logdir / '.retention').is_symlink():
        raise ValueError('retention_directory_symlink')
    with owner_lock(logdir / ".retention/maintenance.lock"):
        pins = retention_pins(workspace); rows = []
        for meta in sorted((logdir / ".retention").glob("*.json")):
            try:
                r = read_json(meta)
                p = Path(r["path"])
                if (r.get("schema") != SCHEMA or p.parent != logdir.absolute()
                        or Path(r["active_path"]).parent != logdir.absolute()
                        or p == Path(r["active_path"]) or not r.get("owner")):
                    raise ValueError("generation_binding_invalid")
                if r.get("state") == "deleted":
                    continue
                if (type(r.get('closed_at')) not in (int, float) or not math.isfinite(r['closed_at'])
                        or r['closed_at'] <= 0
                        or any(type(r.get(k)) is not int or r[k] <= 0
                               for k in ('retention_days','max_generations','max_owner_bytes'))):
                    raise ValueError('generation_policy_invalid')
                if r.get('state') == 'delete_pending' and not p.exists():
                    if apply: atomic_json(meta, dict(r, state='deleted', deletion_recovered_at=now))
                    continue
                if r.get("state") not in {"closed", "delete_pending"}:
                    raise ValueError("generation_state_invalid")
                rows.append((meta, r, p))
            except (OSError, ValueError, KeyError) as exc:
                report["errors"].append(dict(path=str(meta), reason=str(exc)))
        refs = document_references(workspace, {p.name for _, _, p in rows})
        opened = open_owned_inodes(); grouped = {}
        for meta, r, p in rows:
            grouped.setdefault(r["active_path"], []).append((meta, r, p))
        for owner_rows in grouped.values():
            owner_rows.sort(key=lambda x: x[1]["closed_at"], reverse=True)
            kept_bytes = 0
            for index, (meta, r, p) in enumerate(owner_rows):
                try:
                    sig = signature(p)
                    if sig != r["signature"]:
                        raise ValueError("generation_changed")
                    kept_bytes += sig[2]
                    reason = None
                    if time.monotonic()-started >= time_budget:
                        reason = "time_budget"
                    elif (sig[0], sig[1]) in opened:
                        reason = "open_inode"
                    elif (str(p) in pins or p.name in pins or r.get("source_sha256") in pins
                          or r.get("archive_sha256") in pins or p.name in refs):
                        reason = "pinned_or_referenced"
                    expired = now-r["closed_at"] > int(r["retention_days"])*DAY
                    over_limit = index >= int(r["max_generations"]) or kept_bytes > int(r["max_owner_bytes"])
                    if not expired and not over_limit:
                        reason = reason or "within_retention"
                    if reason:
                        report["retained_bytes"] += sig[2]
                        if reason != "within_retention":
                            report["deferred"].append(dict(path=str(p), reason=reason, bytes=sig[2],
                                                           review_due_epoch=now+DAY))
                        continue
                    # Verify a recorded content digest when present. A module
                    # closed generation instead has its immutable inode receipt.
                    expected = r.get("archive_sha256") or r.get("source_sha256")
                    if expected and digest(p) != expected:
                        raise ValueError("generation_digest_mismatch")
                    if apply:
                        if signature(p) != sig or (sig[0], sig[1]) in open_owned_inodes():
                            raise ValueError("generation_changed_or_opened")
                        # Persist intent before unlink; restart can reconcile a
                        # completed deletion without inventing a new generation.
                        if retention_pins(workspace) != pins or document_references(workspace, {p.name}):
                            raise ValueError('retention_authority_changed')
                        atomic_json(meta, dict(r, state='delete_pending', delete_started_at=now))
                        p.unlink()
                        atomic_json(meta, dict(r, state="deleted", deleted_at=now,
                                               deletion_reason="expired" if expired else "owner_capacity"))
                    report["deleted"] += 1; report["deleted_bytes"] += sig[2]
                except (OSError, ValueError, KeyError) as exc:
                    report["errors"].append(dict(path=str(p), reason=str(exc)))
        known = {str(p) for _, _, p in rows}
        report["unknown_retained_bytes"] = sum(p.stat().st_size for p in logdir.iterdir()
            if p.is_file() and not p.is_symlink() and str(p) not in known)
    if report["errors"]:
        report["status"] = "failed"
    return report


def maintain_tmp(workspace, *, apply=False, now=None, time_budget=10):
    with owner_lock(Path(workspace)/'tmp/.operational_retention.lock'):
        return _maintain_tmp_locked(workspace, apply=apply, now=now, time_budget=time_budget)


def _maintain_tmp_locked(workspace, *, apply=False, now=None, time_budget=10):
    """Delete only explicit expired run manifests; unknown audit/worktrees stay."""
    workspace = Path(workspace); root = workspace / "tmp"
    now = time.time() if now is None else now
    start = time.monotonic(); total = 0; count = 0; manifests = []
    report = dict(status="complete", deleted=0, deleted_bytes=0, errors=[], deferred=[],
                  total_bytes=0, inventory_complete=True, excluded_directories=[], limit_bytes=8*1024**3)
    pins = retention_pins(workspace)
    for parent, dirs, files in os.walk(root, followlinks=False):
        # Never enter worktrees or packages; their entire lifetime is external.
        if ".git" in dirs or ".git" in files:
            report["excluded_directories"].append(str(parent)); dirs[:] = []; continue
        dirs[:] = [d for d in dirs if d not in {".venv", "node_modules"} and not (Path(parent)/d).is_symlink()]
        for name in files:
            p = Path(parent)/name
            try:
                if not p.is_symlink(): total += p.stat().st_size
                if name.endswith(".retention.json") and not p.is_symlink(): manifests.append(p)
                count += 1
            except FileNotFoundError:
                pass
        if count > 100000 or time.monotonic()-start > time_budget:
            report["inventory_complete"] = False; break
    # Capacity includes protected worktrees/packages; they are excluded only
    # from deletion discovery. Bounded census failures remain explicitly unknown.
    report['capacity_inventory_basis'] = 'du_apparent_bytes_no_symlink_follow_v1'
    try:
        census = subprocess.run(['du', '-sb', '--one-file-system', '--', str(root)],
                                capture_output=True, text=True, timeout=10, check=True)
        total = int(census.stdout.split()[0])
        report['capacity_inventory_complete'] = True
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        report['capacity_inventory_complete'] = False
    report.update(total_bytes=total, capacity_warning=total > report["limit_bytes"], file_count=count)
    refs = document_references(workspace, {str(p.parent.relative_to(workspace)) for p in manifests})
    opened = open_owned_inodes()
    for manifest in manifests:
        try:
            r = read_json(manifest)
            if (r.get("schema") != "temporary_run_retention_v1" or not r.get("owner")
                    or r.get("closed") is not True or r.get("pinned") is not False
                    or type(r.get("expires_at")) not in (int, float)
                    or not 0 < r["expires_at"] < now):
                continue
            if str(manifest.parent.relative_to(workspace)) in refs:
                report['deferred'].append(dict(path=str(manifest), reason='document_reference')); continue
            files = r.get("files")
            if (not isinstance(files, dict) or len(files) > 1000
                    or any(not isinstance(name, str) or Path(name).name != name
                           or not isinstance(sha, str) or len(sha) != 64 for name, sha in files.items())):
                raise ValueError("tmp_manifest_files_invalid")
            deleted = r.get('deleted_files', {})
            if (not isinstance(deleted, dict)
                    or any(name not in files or sha != files[name] for name, sha in deleted.items())):
                raise ValueError('tmp_deletion_progress_invalid')
            pending = r.get('delete_pending')
            if pending is not None and (not isinstance(pending, str) or pending not in files):
                raise ValueError('tmp_deletion_intent_invalid')
            verified = []
            for relative, sha in files.items():
                p = manifest.parent / relative
                if (p == manifest or Path(relative).is_absolute() or '..' in Path(relative).parts or p.is_symlink()
                        or p.resolve().parent != manifest.parent.resolve()
                        or str(p) in pins or sha in pins):
                    raise ValueError("tmp_path_pinned_or_invalid")
                if relative in deleted:
                    if p.exists(): raise ValueError('tmp_deleted_path_reappeared')
                    continue
                if relative == pending and not p.exists():
                    deleted[relative] = sha
                    continue
                sig = signature(p)
                if (sig[0], sig[1]) in opened or digest(p) != sha:
                    raise ValueError("tmp_open_or_changed")
                verified.append((p, sig))
            if apply:
                for p, sig in verified:
                    if time.monotonic()-start >= time_budget:
                        report['deferred'].append(dict(path=str(manifest), reason='time_budget'))
                        break
                    if signature(p) != sig or (sig[0],sig[1]) in open_owned_inodes():
                        raise ValueError("tmp_changed_before_delete")
                    if (retention_pins(workspace) != pins or document_references(workspace,
                            {p.name, str(manifest.parent.relative_to(workspace))})):
                        raise ValueError('tmp_retention_authority_changed')
                    atomic_json(manifest, dict(r, deleted_files=deleted, delete_pending=p.name))
                    p.unlink()
                    deleted[p.name] = files[p.name]
                    atomic_json(manifest, dict(r, deleted_files=deleted, delete_pending=None))
                    report['deleted'] += 1
                    report['deleted_bytes'] += sig[2]
                if len(deleted) == len(files):
                    atomic_json(manifest, dict(r, closed=False, deleted_files=deleted, delete_pending=None,
                                               deleted_at=now, disposition="deleted_verified_files"))
            else:
                report['deleted'] += len(verified)
                report['deleted_bytes'] += sum(s[2] for _,s in verified)
        except (OSError, ValueError, KeyError) as exc:
            report['deferred'].append(dict(path=str(manifest), reason=str(exc)))
    state = workspace / "data/report/log_retention/tmp_capacity.json"
    if state.exists():
        before = read_json(state)
        elapsed = now-before.get('at', now)
        comparable = (before.get('capacity_inventory_basis') == report['capacity_inventory_basis']
                      and before.get('capacity_inventory_complete') is True
                      and report['capacity_inventory_complete'] is True)
        report['growth_bytes'] = total-before.get('total_bytes', total) if comparable else None
        report['growth_interval_seconds'] = elapsed
        report['growth_warning'] = comparable and 0 < elapsed <= DAY*2 and report['growth_bytes'] > 2*1024**3
    if apply:
        atomic_json(state, dict(report, at=now))
    return report


def prune_metrics(workspace, *, apply=False, now=None):
    """Three calendar days, under the sampler's exact append lock; invalid stays."""
    workspace = Path(workspace); source = workspace/'logs/system_metric_samples.jsonl'
    now = time.time() if now is None else now
    report = dict(status='complete', pruned=0, retained=0, invalid_retained=0, retention_days=3)
    if not source.exists(): return report
    with owner_lock(workspace/'tmp/system_metric_samples.lock'):
        sig = signature(source)
        if sig[2] > 128*1024**2: raise ValueError('metric_size_limit')
        temp = source.with_name(source.name+'.prune.'+uuid.uuid4().hex)
        try:
            with source.open('rb') as src, temp.open('xb') as out:
                for raw in src:
                    expired = False
                    try:
                        row = json.loads(raw)
                        at = datetime.fromisoformat(row['ts'])
                        if at.tzinfo is None: raise ValueError('metric_naive_time')
                        expired = at.timestamp() < now-3*DAY
                    except (ValueError, KeyError, TypeError):
                        report['invalid_retained'] += 1
                    if expired: report['pruned'] += 1
                    else: out.write(raw); report['retained'] += 1
                out.flush(); os.fsync(out.fileno())
            if signature(source) != sig: raise ValueError('metric_changed_without_lock')
            if apply:
                os.chmod(temp, source.stat().st_mode & 0o777)
                os.replace(temp, source)
        finally: temp.unlink(missing_ok=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--terminal", type=Path)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--include-tmp", action="store_true")
    parser.add_argument("--include-metrics", action="store_true")
    parser.add_argument("--register-active", type=Path)
    parser.add_argument("--register-closed", type=Path)
    parser.add_argument("--owner")
    parser.add_argument("--source-sha256")
    parser.add_argument("--archive-sha256")
    args = parser.parse_args(argv)
    if args.register_active:
        register_generation(args.register_active, args.register_closed, owner=args.owner,
                            source_sha256=args.source_sha256, archive_sha256=args.archive_sha256)
        return 0
    try:
        result = maintain_logs(args.workspace, apply=args.apply)
        if args.include_tmp:
            result['tmp'] = maintain_tmp(args.workspace, apply=args.apply)
        if args.include_metrics:
            result['metrics'] = prune_metrics(args.workspace, apply=args.apply)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = dict(status="failed", errors=[str(exc)])
    result.update(run_id=args.run_id, finished_at=datetime.now(timezone.utc).isoformat(),
                  apply=args.apply, lane="closed_operational_logs")
    if args.terminal:
        atomic_json(args.terminal, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
