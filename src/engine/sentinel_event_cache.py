from __future__ import annotations

import gzip
import json
import os
import tempfile
import hashlib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from src.utils.jsonl_io import existing_or_gzip_path

PayloadParser = Callable[[dict[str, Any]], dict[str, Any] | None]
ARCHIVE_SCHEMA = "sentinel_closed_cache_archive_v1"
KST = ZoneInfo("Asia/Seoul")


def _cache_object_decoder():
    """Share bounded immutable strings without changing JSON values or rows.

    A daily cache repeats the same field names and short enum values thousands
    of times. Pools belong to this one read, never to runtime/policy state.
    Unknown or large strings still decode normally; containers remain distinct.
    """
    keys: dict[str, str] = {}
    values: dict[str, str] = {}

    def decode(pairs):
        result = {}
        for key, value in pairs:
            if len(key) <= 192:
                if key in keys:
                    key = keys[key]
                elif len(keys) < 2048:
                    keys[key] = key
            if isinstance(value, str) and len(value) <= 192:
                if value in values:
                    value = values[value]
                elif len(values) < 8192:
                    values[value] = value
            result[key] = value
        return result

    return decode


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    fd, name = tempfile.mkstemp(prefix=".sentinel-meta-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _cache_paths(
    cache_dir: Path, cache_name: str, target_date: str
) -> tuple[Path, Path]:
    safe_name = "".join(
        ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cache_name
    )
    return (
        cache_dir / f"{safe_name}_{target_date}.jsonl",
        cache_dir / f"{safe_name}_{target_date}.meta.json",
    )


def reject_missing_archived_raw(cache_dir: Path, cache_name: str, target_date: str) -> None:
    """Do not interpret a missing bound source as a valid empty population."""
    cache, _ = _cache_paths(cache_dir, cache_name, target_date)
    receipt = Path(str(cache) + ".archive.json")
    if receipt.exists() or receipt.is_symlink():
        raise ValueError("sentinel_archive_raw_missing")


def _reset_cache(cache_path: Path, meta_path: Path) -> None:
    cache_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)


def archived_cache_binding(cache_path: Path, meta: dict[str, Any], *, allow_original=False) -> dict[str, Any]:
    """Read a producer-issued archive; historical unsealed gzip is never enrolled."""
    from src.engine.monitoring.sentinel_compact_store import (
        REVIEWED_ARCHIVE_ISSUERS,
        stamp,
    )

    cache_path = Path(cache_path)
    receipt_path = Path(str(cache_path) + ".archive.json")
    if cache_path.is_symlink() or receipt_path.is_symlink() or (cache_path.exists() and not allow_original):
        raise ValueError("sentinel_archive_namespace_changed")
    receipt_before = stamp(receipt_path)
    if receipt_before[2] > 128 * 1024:
        raise ValueError("sentinel_archive_receipt_oversized")
    with receipt_path.open("rb") as handle:
        raw = handle.read(128 * 1024 + 1)
    receipt = json.loads(raw)
    seal = receipt.get("receipt_sha256")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    expected = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                           allow_nan=False).encode()).hexdigest()
    meta_path = cache_path.with_suffix(".meta.json")
    meta_raw = meta_path.read_bytes()
    raw_logical = Path(meta.get("raw_path") or "")
    if raw_logical.parent.name == "pipeline_events":
        from src.utils.pipeline_event_logger import _late_pipeline_event_path

        late = _late_pipeline_event_path(raw_logical)
        if late.exists() or late.is_symlink():
            raise ValueError("sentinel_archive_late_source_unverified")
    if (receipt.get("schema") != ARCHIVE_SCHEMA or seal != expected
        or receipt.get("logical_path") != str(cache_path)
        or receipt.get("meta_sha256") != hashlib.sha256(meta_raw).hexdigest()
        or json.loads(meta_raw) != meta
        or meta.get("closed_archive_contract") != ARCHIVE_SCHEMA
        or receipt.get("source_generation") != meta.get("cache_generation")
        or receipt.get("logical_size") != meta["cache_generation"][2]
        or receipt.get("cache_event_count") != meta.get("cache_event_count")
        or receipt.get("raw_late_absent") is not True
        or receipt.get("issuer_code_sha256") not in (
            REVIEWED_ARCHIVE_ISSUERS | {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        )
        or receipt.get("runtime_effect") is not False
        or (cache_path.exists() and stamp(cache_path) != receipt.get("source_generation"))
        or stamp(receipt_path) != receipt_before):
        raise ValueError("sentinel_archive_receipt_invalid")
    # This admits only byte identity into the existing invocation owner;
    # each caller still independently validates source semantics and scope.
    from src.engine.infrastructure.validation_digest_session import ACTIVE

    session = ACTIVE.get()
    if session is not None and session.binding["role"] in {"postclose", "transition"}:
        archive = Path(str(cache_path) + ".gz")
        fd = os.open(archive, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            generation = [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]
            if (not __import__("stat").S_ISREG(info.st_mode) or info.st_nlink != 1
                or generation != receipt.get("archive_generation")
                or stamp(archive) != generation or stamp(receipt_path) != receipt_before):
                raise ValueError("sentinel_archive_generation_changed")
            session.admit_native_generation(
                archive, dict(path=archive.name, size=info.st_size, sha256=receipt["archive_sha256"]),
                generation, proof_sha256=seal)
        finally:
            os.close(fd)
    return {key: receipt[key] for key in (
        "source_generation", "logical_sha256", "logical_size", "archive_sha256", "archive_generation"
    )}


def _archive_raw_generation_matches(meta, raw_path, raw_stat, cache_dir):
    """Accept an exact original raw generation or its native indexed successor."""
    expected = meta.get("raw_generation") or {}
    actual = dict(device=raw_stat.st_dev, inode=raw_stat.st_ino,
                  size_bytes=raw_stat.st_size, mtime_ns=raw_stat.st_mtime_ns,
                  ctime_ns=raw_stat.st_ctime_ns)
    logical = Path(meta.get("raw_path") or "")
    if logical.parent.name == "pipeline_events":
        from src.utils.pipeline_event_logger import _late_pipeline_event_path

        late = _late_pipeline_event_path(logical)
        if late.exists() or late.is_symlink():
            raise ValueError("sentinel_archive_late_source_unverified")
    if str(raw_path) == str(logical) and actual == expected:
        return True
    if raw_path != Path(str(logical) + ".gz") or raw_path.is_symlink():
        return False
    from src.engine.automation import main_trailing_source_store as trailing

    data_root = Path(cache_dir).resolve().parent.parent
    generation = trailing._archive_generation(data_root, logical)
    original = [expected.get(k) for k in ("device", "inode", "size_bytes", "mtime_ns", "ctime_ns")]
    return (generation.get("source_stat") == original
            and generation.get("size") == expected.get("size_bytes")
            and meta.get("raw_offset") == expected.get("size_bytes"))


@contextmanager
def _raw_producer_rotation_lease(logical: Path):
    """Exclude native raw append and generation rotation during cache custody."""
    if logical.parent.name != "pipeline_events":
        yield
        return
    import fcntl
    import stat
    from src.utils.jsonl_io import jsonl_artifact_generation_lock
    from src.utils.pipeline_event_logger import _pipeline_event_partition_lock_path, _late_pipeline_event_path

    lock_path = _pipeline_event_partition_lock_path(logical)
    late = _late_pipeline_event_path(logical)
    with jsonl_artifact_generation_lock(logical, exclusive=False, blocking=False, create_parent=False):
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o640)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("sentinel_archive_raw_lock_invalid")
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            if (lock_path.stat().st_dev, lock_path.stat().st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("sentinel_archive_raw_lock_changed")
            if late.exists() or late.is_symlink():
                raise ValueError("sentinel_archive_late_source_unverified")
            yield
            after = os.fstat(fd)
            if (late.exists() or late.is_symlink()
                or (lock_path.stat().st_dev, lock_path.stat().st_ino) != (after.st_dev, after.st_ino)):
                raise ValueError("sentinel_archive_raw_lock_changed")
        finally:
            os.close(fd)


def _holding_history_claims_cache(data_root: Path, cache: Path) -> bool:
    """Inspect native immutable receipts while the historical owner is locked."""
    from datetime import date
    from src.engine.scalping.entry_split_monitor_projection import _read, _digest

    directory = data_root / "report/holding_exit_sentinel/historical_resolutions"
    if directory.is_symlink():
        raise ValueError("sentinel_archive_historical_resolution_retained")
    if not directory.exists():
        return False
    before = directory.stat()
    claimed = False
    for path in directory.iterdir():
        if path.name == "collection_witnesses" and path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise ValueError("sentinel_archive_historical_resolution_unverified")
        value, _ = _read(path, 262144)
        sources = value.get("sources")
        resolution = value.get("resolution") or {}
        if (value.get("schema") != "holding_historical_resolution_receipt_v1"
            or value.get("receipt_sha256") != _digest({k: v for k, v in value.items() if k != "receipt_sha256"})
            or not isinstance(sources, dict) or not isinstance(resolution, dict)
            or not isinstance(value.get("code"), dict)
            or not isinstance(value.get("accepted_position_ids"), list)
            or not isinstance(value.get("report_sha256"), str)
            or len(value["report_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in value["report_sha256"])):
            raise ValueError("sentinel_archive_historical_resolution_unverified")
        try:
            day = date.fromisoformat(resolution["source_date"]).isoformat()
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError("sentinel_archive_historical_resolution_unverified") from exc
        historical_cache = data_root / "runtime/sentinel_event_cache" / f"holding_exit_sentinel_events_{day}.jsonl"
        if str(historical_cache) not in sources:
            raise ValueError("sentinel_archive_historical_resolution_unverified")
        if any(str(cache) + suffix in sources for suffix in ("", ".gz", ".gz.archive_receipt.json")):
            claimed = True
    if directory.stat() != before:
        raise ValueError("sentinel_archive_historical_resolution_changed")
    return claimed


def archive_closed_cache(data_root: Path, cache_name: str, target_date: str, *, now=None):
    """Retire a new closed cache only after its native postclose and index prove it.

    Runs under the existing writer lock. A legacy plain/gzip pair is never
    promoted by file name. Original bytes remain until all checks and archive
    publication have succeeded; changed raw generations cannot be appended.
    """
    import fcntl
    from contextlib import ExitStack
    from datetime import date, time
    from src.engine.automation import postclose_done_controller as controller
    from src.engine.automation import next_preopen_readiness as readiness
    from src.engine.monitoring.sentinel_compact_store import stamp
    from src.engine.monitoring.sentinel_source_window import _native_index_state
    from src.engine.infrastructure.log_retention import DocumentReferences, open_owned_inodes

    data_root = Path(data_root).resolve(strict=True)
    current = now or datetime.now(KST)
    day = date.fromisoformat(target_date)
    if (current.tzinfo is None or day.isoformat() != target_date
        or cache_name not in {"buy_funnel_sentinel_events", "holding_exit_sentinel_events"}
        or current.astimezone(KST).date().isoformat() <= readiness.target_after_postclose(
            target_date, now=datetime.combine(day, time.min, tzinfo=KST))):
        raise ValueError("sentinel_archive_not_closed")
    cache, meta_path = _cache_paths(data_root / "runtime/sentinel_event_cache", cache_name, target_date)
    if any(path.is_symlink() for path in (cache, meta_path, *cache.parents)):
        raise ValueError("sentinel_archive_path_invalid")
    with ExitStack() as stack:
        if cache_name == "holding_exit_sentinel_events":
            history_dir = data_root / "report/holding_exit_sentinel"
            history_dir.mkdir(parents=True, exist_ok=True)
            if any(path.is_symlink() for path in (history_dir, *history_dir.parents)):
                raise ValueError("sentinel_archive_historical_path_invalid")
            history_lock_path = history_dir / ".historical_resolution.lock"
            history_lock = stack.enter_context(os.fdopen(
                os.open(history_lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), "a+b"))
            fcntl.flock(history_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (history_lock_path.stat().st_dev, history_lock_path.stat().st_ino) != (
                os.fstat(history_lock.fileno()).st_dev, os.fstat(history_lock.fileno()).st_ino):
                raise ValueError("sentinel_archive_historical_lock_changed")
        lock = stack.enter_context(meta_path.with_suffix(".lock").open("a"))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        meta_raw = meta_path.read_bytes()
        meta = json.loads(meta_raw)
        stack.enter_context(_raw_producer_rotation_lease(Path(meta["raw_path"])))
        if not cache.exists() and not cache.is_symlink():
            from src.engine.monitoring import sentinel_compact_store as store

            binding = archived_cache_binding(cache, meta)
            raw_path = existing_or_gzip_path(Path(meta["raw_path"]))
            raw_stat = raw_path.stat()
            if not _archive_raw_generation_matches(meta, raw_path, raw_stat, cache.parent):
                raise ValueError("sentinel_archive_source_unverified")
            logical, size = hashlib.sha256(), 0
            with store._verified_archive(cache, binding) as (physical, _, _):
                with gzip.GzipFile(fileobj=physical, mode="rb") as decoded:
                    for block in iter(lambda: decoded.read(1024 * 1024), b""):
                        logical.update(block)
                        size += len(block)
            receipt_path = Path(str(cache) + ".archive.json")
            receipt_before = stamp(receipt_path)
            receipt_raw = receipt_path.read_bytes()
            if (size != binding["logical_size"] or logical.hexdigest() != binding["logical_sha256"]
                or meta_path.read_bytes() != meta_raw or raw_path.stat() != raw_stat
                or not _archive_raw_generation_matches(meta, raw_path, raw_stat, cache.parent)
                or stamp(receipt_path) != receipt_before or archived_cache_binding(cache, meta) != binding):
                raise ValueError("sentinel_archive_existing_generation_changed")
            return json.loads(receipt_raw)
        initial = stamp(cache)
        documents = DocumentReferences(data_root.parent)
        documents.require_unreferenced([str(cache), cache.name])
        if tuple(initial[:2]) in open_owned_inodes():
            raise ValueError("sentinel_archive_source_open")
        # The historical-resolution owner binds physical source identities.
        # Existing evidence is never silently reclassified as a logical receipt.
        if cache_name == "holding_exit_sentinel_events" and _holding_history_claims_cache(data_root, cache):
            raise ValueError("sentinel_archive_historical_resolution_retained")
        raw_path = existing_or_gzip_path(Path(meta["raw_path"]))
        raw_stat = raw_path.stat()
        if (meta.get("closed_archive_contract") != ARCHIVE_SCHEMA
            or meta.get("cache_generation") != initial
            or not _archive_raw_generation_matches(meta, raw_path, raw_stat, cache.parent)
            or meta.get("raw_offset") != meta.get("raw_size")
            or meta.get("cache_projection_skip_reason")
            or type(meta.get("cache_event_count")) is not int
            or str(cache) != meta.get("cache_path")):
            raise ValueError("sentinel_archive_source_unverified")
        controller_path = data_root / "report/postclose_done_controller" / f"postclose_done_controller_{target_date}.json"
        if controller.done_terminal_receipt_issues(controller_path, target_date,
                                                   started_after_ns=0, generation_only=True):
            raise ValueError("sentinel_archive_postclose_unverified")
        # Holding's summary-only writer intentionally leaves the optional
        # compact index absent; the full round-trip population verification
        # below remains mandatory. The entry window requires its index.
        index = cache.with_suffix(".compact.sqlite")
        if meta.get("compact_index_enabled") and (
            cache_name == "buy_funnel_sentinel_events" or index.exists() or index.is_symlink()
        ):
            _native_index_state(cache, initial, meta["cache_event_count"])
        archive = Path(str(cache) + ".gz")
        receipt_path = Path(str(cache) + ".archive.json")
        intent_path = Path(str(cache) + ".archive-intent.json")
        if any(path.is_symlink() for path in (archive, receipt_path, intent_path)):
            raise ValueError("sentinel_archive_namespace_changed")
        if ((archive.exists() or receipt_path.exists()) and not intent_path.exists()) or (
            receipt_path.exists() and not archive.exists()
        ):
            raise ValueError("sentinel_archive_existing_generation")
        fd, temp_name = tempfile.mkstemp(prefix=".sentinel-archive-", dir=cache.parent)
        temp = Path(temp_name)
        try:
            logical = hashlib.sha256()
            row_count = 0
            with cache.open("rb") as source, os.fdopen(fd, "wb") as physical:
                with gzip.GzipFile(filename="", fileobj=physical, mode="wb", mtime=0) as encoded:
                    for line in source:
                        if not line.endswith(b"\n"):
                            raise ValueError("sentinel_archive_partial_line")
                        try:
                            row = json.loads(line)
                        except (ValueError, UnicodeDecodeError) as exc:
                            raise ValueError("sentinel_archive_malformed_row") from exc
                        if not isinstance(row, dict):
                            raise ValueError("sentinel_archive_nonobject_row")
                        row_count += 1
                        logical.update(line)
                        encoded.write(line)
                    if row_count != meta["cache_event_count"]:
                        raise ValueError("sentinel_archive_population_changed")
                physical.flush()
                os.fsync(physical.fileno())
            decoded = hashlib.sha256()
            size = 0
            with gzip.open(temp, "rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    decoded.update(block)
                    size += len(block)
            if (size != initial[2] or logical.digest() != decoded.digest()
                or stamp(cache) != initial or meta_path.read_bytes() != meta_raw
                or raw_path.stat() != raw_stat
                or not _archive_raw_generation_matches(meta, raw_path, raw_stat, cache.parent)):
                raise ValueError("sentinel_archive_roundtrip_or_source_changed")
            with temp.open("rb") as handle:
                intended_archive_sha = hashlib.file_digest(handle, "sha256").hexdigest()
            intent = dict(schema="sentinel_closed_cache_archive_intent_v1", logical_path=str(cache),
                          source_generation=initial, logical_size=size,
                          logical_sha256=logical.hexdigest(), archive_sha256=intended_archive_sha,
                          meta_sha256=hashlib.sha256(meta_raw).hexdigest(),
                          cache_event_count=meta["cache_event_count"])
            if intent_path.exists():
                if intent_path.stat().st_size > 128 * 1024:
                    raise ValueError("sentinel_archive_intent_changed")
                prior_intent = json.loads(intent_path.read_bytes())
                seal = prior_intent.pop("intent_sha256", None)
                expected_seal = hashlib.sha256(json.dumps(prior_intent, sort_keys=True,
                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                old_name = prior_intent.pop("temporary_archive_basename", None)
                old_identity = prior_intent.pop("temporary_archive_identity", None)
                if (seal != expected_seal or prior_intent != intent
                    or not isinstance(old_name, str) or Path(old_name).name != old_name
                    or not old_name.startswith(".sentinel-archive-")
                    or not isinstance(old_identity, list) or len(old_identity) != 2):
                    raise ValueError("sentinel_archive_intent_changed")
                owned_temp = cache.parent / old_name
            else:
                temp_stat = temp.stat()
                old_identity = [temp_stat.st_dev, temp_stat.st_ino]
                owned_temp = temp
                intent["temporary_archive_basename"] = temp.name
                intent["temporary_archive_identity"] = old_identity
                intent["intent_sha256"] = hashlib.sha256(json.dumps(intent, sort_keys=True,
                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                intent_fd, intent_name = tempfile.mkstemp(prefix=".sentinel-intent-", dir=cache.parent)
                try:
                    with os.fdopen(intent_fd, "w", encoding="utf-8") as output:
                        json.dump(intent, output, sort_keys=True, separators=(",", ":"), allow_nan=False)
                        output.flush()
                        os.fsync(output.fileno())
                    os.link(intent_name, intent_path)
                    directory = os.open(cache.parent, os.O_DIRECTORY)
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                finally:
                    Path(intent_name).unlink(missing_ok=True)
            if archive.exists():
                previous = stamp(archive)
                archive_stat = archive.stat()
                if archive_stat.st_nlink == 2:
                    if owned_temp.is_symlink() or not owned_temp.is_file():
                        raise ValueError("sentinel_archive_temporary_link_unverified")
                    temp_stat = owned_temp.stat()
                    if ([temp_stat.st_dev, temp_stat.st_ino] != old_identity
                        or (archive_stat.st_dev, archive_stat.st_ino) != (temp_stat.st_dev, temp_stat.st_ino)
                        or temp_stat.st_nlink != 2):
                        raise ValueError("sentinel_archive_temporary_link_unverified")
                    owned_temp.unlink()
                    previous = stamp(archive)
                elif archive_stat.st_nlink != 1:
                    raise ValueError("sentinel_archive_temporary_link_unverified")
                with archive.open("rb") as handle:
                    existing_sha = hashlib.file_digest(handle, "sha256").hexdigest()
                if existing_sha != intended_archive_sha or stamp(archive) != previous:
                    raise ValueError("sentinel_archive_existing_generation")
            else:
                if owned_temp.is_symlink() or not owned_temp.is_file():
                    raise ValueError("sentinel_archive_temporary_link_unverified")
                owned_stat = owned_temp.stat()
                if ([owned_stat.st_dev, owned_stat.st_ino] != old_identity
                    or owned_stat.st_nlink != 1):
                    raise ValueError("sentinel_archive_temporary_link_unverified")
                with owned_temp.open("rb") as handle:
                    if hashlib.file_digest(handle, "sha256").hexdigest() != intended_archive_sha:
                        raise ValueError("sentinel_archive_temporary_link_unverified")
                os.link(owned_temp, archive)
                owned_temp.unlink()
            temp.unlink(missing_ok=True)
            if archive.stat().st_nlink != 1:
                raise ValueError("sentinel_archive_temporary_link_unverified")
            archive_generation = stamp(archive)
            with archive.open("rb") as handle:
                archive_sha = hashlib.file_digest(handle, "sha256").hexdigest()
            body = dict(schema=ARCHIVE_SCHEMA, logical_path=str(cache),
                        source_generation=initial, logical_size=size,
                        logical_sha256=logical.hexdigest(), archive_generation=archive_generation,
                        archive_sha256=archive_sha, meta_sha256=hashlib.sha256(meta_raw).hexdigest(),
                        cache_event_count=meta["cache_event_count"], raw_late_absent=True,
                        issuer_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        runtime_effect=False)
            body["receipt_sha256"] = hashlib.sha256(json.dumps(body, sort_keys=True,
                separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            if receipt_path.exists():
                if receipt_path.stat().st_size > 128 * 1024 or json.loads(receipt_path.read_bytes()) != body:
                    raise ValueError("sentinel_archive_receipt_changed")
            else:
                receipt_fd, receipt_name = tempfile.mkstemp(prefix=".sentinel-receipt-", dir=cache.parent)
                try:
                    with os.fdopen(receipt_fd, "w", encoding="utf-8") as receipt:
                        json.dump(body, receipt, sort_keys=True, separators=(",", ":"), allow_nan=False)
                        receipt.flush()
                        os.fsync(receipt.fileno())
                    os.link(receipt_name, receipt_path)
                finally:
                    Path(receipt_name).unlink(missing_ok=True)
            if (stamp(cache) != initial or stamp(archive) != archive_generation or archive.stat().st_nlink != 1
                or meta_path.read_bytes() != meta_raw or raw_path.stat() != raw_stat
                or not _archive_raw_generation_matches(meta, raw_path, raw_stat, cache.parent)
                or tuple(initial[:2]) in open_owned_inodes()):
                raise ValueError("sentinel_archive_source_changed_before_unlink")
            documents.require_unreferenced([str(cache), cache.name])
            cache.unlink()
            directory = os.open(cache.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return body
        finally:
            temp.unlink(missing_ok=True)


def update_and_load_cached_event_rows(**kwargs):
    """Serialize the optional cache, cursor and compressed-index transaction."""
    import fcntl
    from contextlib import ExitStack

    cache_dir = Path(kwargs["cache_dir"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path, meta_path = _cache_paths(cache_dir, kwargs["cache_name"], kwargs["target_date"])
    with meta_path.with_suffix(".lock").open("a") as lock, ExitStack() as stack:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = Path(str(cache_path) + ".archive.json")
        if receipt.exists() or receipt.is_symlink():
            meta = _read_json(meta_path)
            if not isinstance(meta, dict) or not isinstance(meta.get("raw_path"), str):
                raise ValueError("sentinel_archive_source_unverified")
            stack.enter_context(_raw_producer_rotation_lease(Path(meta["raw_path"])))
        return _update_and_load_cached_event_rows(**kwargs)


def _update_and_load_cached_event_rows(
    *,
    raw_path: Path,
    cache_dir: Path,
    cache_name: str,
    target_date: str,
    schema_version: int,
    parse_payload: PayloadParser,
    verified_schema_migration: dict[str, Any] | None = None,
    project_loaded_payload: PayloadParser | None = None,
    cache_projection_version: str | None = None,
    load_rows: bool = True,
    compact_index: bool = False,
    max_append_bytes: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Maintain a slim append-only cache for sentinel pipeline-event scans.

    The raw pipeline stream is lossless and can be very large intraday. Sentinels
    only need a filtered subset of fields, so this cache parses new raw bytes
    since the previous run and rereads the slimmer sentinel-owned cache.
    Maintenance may use load_rows=False: no rows are materialized, while the
    metadata still records the full population. Report callers use the default.
    """

    raw_path = existing_or_gzip_path(raw_path)
    if max_append_bytes is not None and (
        type(max_append_bytes) is not int
        or not 0 < max_append_bytes <= 32 * 1024 * 1024
    ):
        raise ValueError("sentinel_append_byte_budget_invalid")
    if not raw_path.exists():
        reject_missing_archived_raw(cache_dir, cache_name, target_date)
        return [], {
            "enabled": True,
            "status": "raw_missing",
            "raw_path": str(raw_path),
            "cache_event_count": 0,
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path, meta_path = _cache_paths(cache_dir, cache_name, target_date)
    from src.engine.monitoring.sentinel_compact_store import stamp as cache_stamp
    entirely_new_cache = not any(
        path.exists() or path.is_symlink()
        for path in (cache_path, meta_path, Path(str(cache_path) + ".gz"),
                     Path(str(cache_path) + ".archive.json"))
    )

    archive_receipt = Path(str(cache_path) + ".archive.json")
    if archive_receipt.exists() or archive_receipt.is_symlink():
        from src.engine.monitoring import sentinel_compact_store as store

        meta = _read_json(meta_path)
        binding = archived_cache_binding(cache_path, meta, allow_original=True)
        stat = raw_path.stat()
        if (verified_schema_migration or meta.get("schema_version") != schema_version
            or not _archive_raw_generation_matches(meta, raw_path, stat, cache_dir)
            or meta.get("raw_offset") != meta.get("raw_size")
            or (cache_projection_version and
                meta.get("cache_projection_version") != cache_projection_version)):
            raise ValueError("sentinel_archive_raw_or_schema_changed")
        if cache_path.exists():
            # A receipt can be committed before unlink completes. Preserve the
            # original consumer while proving both representations remain the
            # same transaction; do not append to a closed generation here.
            archive = Path(str(cache_path) + ".gz")
            if archive.is_symlink() or store.stamp(archive) != binding["archive_generation"]:
                raise ValueError("sentinel_archive_generation_changed")
            with archive.open("rb") as source:
                archive_sha = hashlib.file_digest(source, "sha256").hexdigest()
            if archive_sha != binding["archive_sha256"] or store.stamp(archive) != binding["archive_generation"]:
                raise ValueError("sentinel_archive_digest_mismatch")
            logical, rows, count = hashlib.sha256(), [], 0
            with cache_path.open("rb") as source:
                for line in source:
                    if not line.endswith(b"\n"):
                        raise ValueError("sentinel_archive_partial_line")
                    logical.update(line)
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("sentinel_archive_nonobject_row")
                    count += 1
                    if load_rows:
                        if project_loaded_payload is not None:
                            original = row
                            row = project_loaded_payload(row)
                            if not isinstance(row, dict) or any(
                                row.get(k) != v for k, v in original.items() if k != "fields"
                            ):
                                raise ValueError("sentinel_cache_projection_population_changed")
                        rows.append(row)
            if (count != meta["cache_event_count"] or logical.hexdigest() != binding["logical_sha256"]
                or store.stamp(cache_path) != binding["source_generation"]
                or raw_path.stat() != stat
                or not _archive_raw_generation_matches(meta, raw_path, stat, cache_dir)):
                raise ValueError("sentinel_archive_source_changed_during_read")
            return rows, {"enabled": True, "status": "ok", **meta,
                          "materialized_event_count": len(rows)}
        rows = []
        if compact_index and load_rows:
            rows = list(store.indexed_rows(cache_path, previous_stamp=None,
                         expected_count=meta["cache_event_count"], archive_binding=binding))
        else:
            with store._verified_archive(cache_path, binding) as (physical, _, _):
                if load_rows:
                    logical = hashlib.sha256()
                    count = 0
                    with gzip.GzipFile(fileobj=physical, mode="rb") as stream:
                        for line in stream:
                            logical.update(line)
                            count += len(line)
                            try:
                                row = json.loads(line)
                            except (ValueError, UnicodeDecodeError):
                                continue
                            if isinstance(row, dict):
                                if project_loaded_payload is not None:
                                    original = row
                                    row = project_loaded_payload(row)
                                    if not isinstance(row, dict) or any(
                                        row.get(k) != v for k, v in original.items() if k != "fields"
                                    ):
                                        raise ValueError("sentinel_cache_projection_population_changed")
                                rows.append(row)
                    if (count != binding["logical_size"] or logical.hexdigest() != binding["logical_sha256"]
                        or len(rows) != meta["cache_event_count"]):
                        raise ValueError("sentinel_archive_population_changed")
        if raw_path.stat() != stat or not _archive_raw_generation_matches(meta, raw_path, stat, cache_dir):
            raise ValueError("sentinel_archive_raw_changed_during_read")
        return rows, {"enabled": True, "status": "ok", **meta,
                      "archive_binding": binding, "materialized_event_count": len(rows)}

    stat = raw_path.stat()
    before_cache_stamp = cache_stamp(cache_path) if cache_path.exists() else None
    is_gzip_raw = raw_path.suffix == ".gz"
    raw_inode = getattr(stat, "st_ino", None)

    meta = _read_json(meta_path)
    window_issuer = None
    if (compact_index and cache_name == "buy_funnel_sentinel_events"
        and schema_version in (19, 20, 21, 22)
        and isinstance(meta.get("source_window_projection"), dict)):
        from src.engine.monitoring import sentinel_source_window

        if meta["source_window_projection"].get("contract") != sentinel_source_window._contract():
            # Continue with the actual issued writer until the predecessor's
            # last reader has migrated. Resolve it before any cache mutation.
            window_issuer = sentinel_source_window._predecessor_issuer(
                cache_dir.parent.parent, meta["source_window_projection"].get("contract")
            )
    raw_offset = int(meta.get("raw_offset") or 0)
    raw_size = max(int(stat.st_size), raw_offset) if is_gzip_raw else int(stat.st_size)
    migration = verified_schema_migration or {}
    generation = {
        "device": stat.st_dev,
        "inode": stat.st_ino,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
    }
    forward = bool(
        migration
        and migration.get("population_proof") == "forward_only_stage_extension"
    )
    if forward and not (
        migration.get("from_schema") == int(meta.get("schema_version") or 0)
        and migration.get("to_schema") == schema_version
        and migration.get("raw_offset") == raw_offset
        and 0 <= raw_offset <= raw_size
        and not is_gzip_raw
        and str(meta.get("raw_path")) == str(raw_path)
        and meta.get("raw_inode") == raw_inode
        and (migration.get("raw_generation") or {}).get("device") == stat.st_dev
        and (migration.get("raw_generation") or {}).get("inode") == stat.st_ino
        and stat.st_size
        >= (migration.get("raw_generation") or {}).get("size_bytes", raw_size + 1)
        and (
            stat.st_size > migration["raw_generation"]["size_bytes"]
            or (
                stat.st_mtime_ns == migration["raw_generation"].get("mtime_ns")
                and stat.st_ctime_ns == migration["raw_generation"].get("ctime_ns")
            )
        )
        and migration.get("historical_stage_coverage")
        == "not_backfilled_before_raw_offset"
        and cache_path.exists()
    ):
        raise ValueError("forward_cache_schema_source_changed")
    if migration and not forward and migration.get("raw_generation") != generation:
        raise ValueError("verified_cache_schema_source_changed")
    schema_migrated = forward or bool(
        migration
        and migration.get("population_proof") == "verified_zero_stage_census"
        and int(meta.get("schema_version") or 0) == migration.get("from_schema")
        and raw_offset == raw_size
        and not is_gzip_raw
    )
    stale_cache = (
        (int(meta.get("schema_version") or 0) != schema_version and not schema_migrated)
        or str(meta.get("raw_path") or "") != str(raw_path)
        or int(meta.get("raw_inode") or -1) != int(raw_inode or -1)
        or raw_offset > raw_size
        or not cache_path.exists()
        or (
            meta.get("raw_generation")
            and raw_size == meta.get("raw_size")
            and meta["raw_generation"] != generation
        )
    )
    if (
        compact_index
        and not stale_cache
        and meta.get("cache_generation")
        and before_cache_stamp != meta["cache_generation"]
    ):
        raise ValueError("sentinel_cache_generation_changed")
    if stale_cache:
        _reset_cache(cache_path, meta_path)
        raw_offset = 0

    appended_raw_lines = 0
    appended_cache_rows = 0
    decode_errors = 0
    last_good_offset = raw_offset
    raw_opener = gzip.open if is_gzip_raw else open
    with raw_opener(raw_path, "rb") as raw_handle:
        raw_handle.seek(raw_offset)
        with cache_path.open("a", encoding="utf-8") as cache_handle:
            while True:
                line_start = raw_handle.tell()
                if max_append_bytes is not None:
                    remaining = max_append_bytes - (line_start - raw_offset)
                    if remaining <= 0:
                        break
                    raw_bytes = raw_handle.readline(remaining)
                else:
                    raw_bytes = raw_handle.readline()
                if not raw_bytes:
                    break
                appended_raw_lines += 1
                if not raw_bytes.endswith(b"\n"):
                    # Avoid advancing past a partially-written final line.
                    break
                raw_line = raw_bytes.decode("utf-8", errors="replace")
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError:
                    decode_errors += 1
                    last_good_offset = raw_handle.tell()
                    continue
                if (
                    compact_index
                    and cache_name == "buy_funnel_sentinel_events"
                    and schema_version in (19, 20, 21, 22)
                ):
                    from src.engine.monitoring.sentinel_source_window import _epoch

                    try:
                        if not isinstance(payload, dict):
                            raise ValueError("source_window_raw_not_object")
                        _epoch(payload.get("emitted_at"))
                    except (ValueError, TypeError, OverflowError):
                        decode_errors += 1
                        last_good_offset = raw_handle.tell()
                        continue
                parsed = parse_payload(payload) if isinstance(payload, dict) else None
                if parsed is not None:
                    if compact_index and project_loaded_payload is not None:
                        original = parsed
                        parsed = project_loaded_payload(parsed)
                        if not isinstance(parsed, dict) or any(
                            parsed.get(k) != v
                            for k, v in original.items()
                            if k != "fields"
                        ):
                            raise ValueError(
                                "sentinel_cache_projection_population_changed"
                            )
                    cache_handle.write(
                        json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    appended_cache_rows += 1
                last_good_offset = raw_handle.tell()
                if last_good_offset <= line_start:
                    break
            if appended_cache_rows:
                cache_handle.flush()
                os.fsync(cache_handle.fileno())

    rows: list[dict[str, Any]] = []
    row_count = 0
    decode_object = _cache_object_decoder()
    projection_applied = meta.get("cache_projection_version")
    projection_skip = None
    rewrite = bool(
        project_loaded_payload
        and cache_projection_version
        and projection_applied != cache_projection_version
    )
    reusable_projection = (
        compact_index
        and not stale_cache
        and not rewrite
        and not meta.get("cache_projection_skip_reason")
        and meta.get("cache_generation") == before_cache_stamp
        and before_cache_stamp is not None
    )
    if reusable_projection:
        row_count = int(meta["cache_event_count"]) + appended_cache_rows
    else:
        temporary = None
        try:
            before_cache = cache_path.stat()
            writer = None
            if rewrite:
                fd, temporary = tempfile.mkstemp(
                    prefix=".sentinel-projection-", dir=cache_path.parent
                )
                writer = os.fdopen(fd, "w", encoding="utf-8")
            try:
                with cache_path.open(
                    "r", encoding="utf-8", errors="replace"
                ) as cache_handle:
                    for raw_line in cache_handle:
                        if "\ufffd" in raw_line:
                            projection_skip = "unverified_cache_encoding_preserved"
                        if not raw_line.strip():
                            continue
                        try:
                            row = json.loads(raw_line, object_pairs_hook=decode_object)
                        except json.JSONDecodeError:
                            projection_skip = "malformed_cached_row_preserved"
                            continue
                        if not isinstance(row, dict):
                            projection_skip = "nonobject_cached_row_preserved"
                            continue
                        if project_loaded_payload is not None:
                            original = row
                            row = project_loaded_payload(row)
                            if not isinstance(row, dict) or any(
                                row.get(key) != value
                                for key, value in original.items()
                                if key != "fields"
                            ):
                                raise ValueError(
                                    "sentinel_cache_projection_population_changed"
                                )
                        row_count += 1
                        if load_rows and not compact_index:
                            rows.append(row)
                        if writer is not None:
                            writer.write(
                                json.dumps(
                                    row, ensure_ascii=False, separators=(",", ":")
                                )
                                + "\n"
                            )
                if writer is not None:
                    writer.flush()
                    os.fsync(writer.fileno())
            finally:
                if writer is not None:
                    writer.close()
            after_cache = cache_path.stat()
            if project_loaded_payload is not None and any(
                getattr(before_cache, key) != getattr(after_cache, key)
                for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            ):
                raise ValueError("sentinel_cache_changed_during_projection")
            # Validate migration and raw custody before replacing an optional cache.
            if (
                schema_migrated
                and row_count
                != int(meta.get("cache_event_count") or 0) + appended_cache_rows
            ):
                raise ValueError("verified_cache_schema_population_changed")
            if migration and not forward:
                current = raw_path.stat()
                if generation != {
                    "device": current.st_dev,
                    "inode": current.st_ino,
                    "size_bytes": current.st_size,
                    "mtime_ns": current.st_mtime_ns,
                    "ctime_ns": current.st_ctime_ns,
                }:
                    raise ValueError("verified_cache_schema_source_changed")
            if forward:
                current = raw_path.stat()
                if (
                    current.st_dev != stat.st_dev
                    or current.st_ino != raw_inode
                    or current.st_size < last_good_offset
                ):
                    raise ValueError("forward_cache_schema_source_changed")
            if rewrite and projection_skip is None:
                os.chmod(temporary, before_cache.st_mode & 0o777)
                os.replace(temporary, cache_path)
                projection_applied = cache_projection_version
                directory = os.open(cache_path.parent, os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)

    final_stat = raw_path.stat()
    if (
        final_stat.st_dev != stat.st_dev
        or final_stat.st_ino != stat.st_ino
        or (not is_gzip_raw and final_stat.st_size < last_good_offset)
    ):
        raise ValueError("sentinel_raw_generation_changed_during_load")
    final_stat_size = int(final_stat.st_size)
    final_raw_size = (
        max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
    )
    new_meta = {
        "raw_generation": {
            "device": final_stat.st_dev,
            "inode": final_stat.st_ino,
            "size_bytes": final_stat.st_size,
            "mtime_ns": final_stat.st_mtime_ns,
            "ctime_ns": final_stat.st_ctime_ns,
        },
        "cache_generation": cache_stamp(cache_path),
        "compact_index_enabled": compact_index,
        "cache_body_rescanned": not reusable_projection,
        "schema_version": schema_version,
        "raw_path": str(raw_path),
        "raw_inode": raw_inode,
        "raw_offset": last_good_offset,
        "raw_size": final_raw_size,
        "cache_path": str(cache_path),
        "cache_event_count": row_count,
        "materialized_event_count": len(rows),
        "appended_raw_lines": appended_raw_lines,
        "appended_cache_rows": appended_cache_rows,
        "decode_errors": decode_errors,
        "rebuilt": stale_cache,
        "schema_migration_receipt": (
            migration if schema_migrated else meta.get("schema_migration_receipt")
        ),
        "cache_projection_version": projection_applied,
        "cache_projection_skip_reason": projection_skip,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    # Only generations first produced by this writer for the live target day
    # can later be enrolled. Existing historical physical receipts stay native.
    if (stale_cache and entirely_new_cache and target_date == datetime.now(KST).date().isoformat()) or (
        not stale_cache and meta.get("closed_archive_contract") == ARCHIVE_SCHEMA
    ):
        new_meta["closed_archive_contract"] = ARCHIVE_SCHEMA
    if (
        compact_index
        and cache_name == "buy_funnel_sentinel_events"
        and schema_version in (19, 20, 21, 22)
    ):
        from src.engine.monitoring.sentinel_source_window import maintain

        if window_issuer is not None:
            maintain = window_issuer.maintain

        new_meta["source_window_projection"] = maintain(
            cache_path,
            before_cache_stamp if reusable_projection else None,
            new_meta,
            previous_state=meta.get("source_window_projection"),
        )
    _write_json(meta_path, new_meta)
    if compact_index and load_rows:
        # Seal the durable native cache before optional acceleration. Index
        # failure leaves a verified cache that the next call can rebuild from;
        # it does not publish a report or advance an uncommitted index cursor.
        from src.engine.monitoring.sentinel_compact_store import indexed_rows

        rows = list(
            indexed_rows(
                cache_path,
                expected_count=row_count,
                previous_stamp=before_cache_stamp if reusable_projection else None,
            )
        )
        new_meta["materialized_event_count"] = len(rows)
    return rows, {
        "enabled": True,
        "status": "ok",
        **new_meta,
    }


def load_verified_day_projection(
    *, raw_path, cache_dir, cache_name, parser_version, parse_payload
):
    """Immutable day facts; a changed shard rebuilds only that shard.

    This stricter profile leaves the existing intraday append cache untouched.
    Economic policy/cost hashes belong to replay, not to these lossless facts.
    """
    import hashlib
    import os
    import tempfile
    import fcntl

    def digest(value):
        return hashlib.sha256(
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()

    def generation():
        s = raw_path.stat()
        return [s.st_dev, s.st_ino, s.st_ctime_ns, s.st_mtime_ns, s.st_size]

    raw_path = Path(raw_path)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(raw_path.resolve()).encode()).hexdigest()[:24]
    cache_path = cache_dir / f"{cache_name}-{key}.json"
    # One source lock, unique temporary file, atomic completed publication.
    with (cache_dir / f"{cache_name}-{key}.lock").open("a") as lock:
        owns_lock = True
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            owns_lock = False
        before = generation()
        cached = _read_json(cache_path)
        cached = cached if isinstance(cached, dict) else {}
        body = cached.get("body")
        try:
            cache_valid = (
                isinstance(body, dict)
                and body.get("generation") == before
                and body.get("parser_version") == parser_version
                and body.get("raw_path") == str(raw_path.resolve())
                and isinstance(body.get("rows"), list)
                and isinstance(body.get("census"), dict)
                and isinstance(body.get("source_sha256"), str)
                and len(body["source_sha256"]) == 64
                and cached.get("body_sha256") == digest(body)
            )
        except (ValueError, TypeError):
            cache_valid = False
        if cache_valid:
            return body["rows"], {
                **body["census"],
                "raw_scanned": False,
                "source_sha256": body["source_sha256"],
            }
        rows, counts = [], {"raw_event_count": 0, "decode_errors": 0}
        hasher = hashlib.sha256()
        complete = True
        opener = gzip.open if raw_path.suffix == ".gz" else open
        with opener(raw_path, "rb") as handle:
            for line in handle:
                hasher.update(line)
                if not line.endswith(b"\n"):
                    complete = False
                    break
                try:
                    payload = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    counts["decode_errors"] += 1
                    continue
                if not isinstance(payload, dict):
                    continue
                counts["raw_event_count"] += 1
                parsed = parse_payload(payload)
                if isinstance(parsed, dict) and "_census" in parsed:
                    for name, count in parsed["_census"].items():
                        counts[name] = counts.get(name, 0) + count
                elif parsed is not None:
                    rows.append(parsed)
        after = generation()
        body = {
            "generation": before,
            "parser_version": parser_version,
            "raw_path": str(raw_path.resolve()),
            "source_sha256": hasher.hexdigest(),
            "rows": rows,
            "census": counts,
        }
        if owns_lock and complete and before == after:
            fd, temporary = tempfile.mkstemp(
                prefix=cache_path.name + ".", dir=cache_dir
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    json.dump(
                        {"body": body, "body_sha256": digest(body)},
                        output,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, cache_path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return rows, {
            **counts,
            "raw_scanned": True,
            "source_sha256": hasher.hexdigest(),
            "checkpoint_complete": complete and before == after,
        }
