from __future__ import annotations

import gzip
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.utils.jsonl_io import existing_or_gzip_path

PayloadParser = Callable[[dict[str, Any]], dict[str, Any] | None]


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
    fd, name = tempfile.mkstemp(prefix='.sentinel-meta-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
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


def _reset_cache(cache_path: Path, meta_path: Path) -> None:
    cache_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)


def update_and_load_cached_event_rows(**kwargs):
    """Serialize the optional cache, cursor and compressed-index transaction."""
    import fcntl
    cache_dir = Path(kwargs['cache_dir'])
    cache_dir.mkdir(parents=True, exist_ok=True)
    _, meta_path = _cache_paths(cache_dir, kwargs['cache_name'], kwargs['target_date'])
    with meta_path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
    if max_append_bytes is not None and (type(max_append_bytes) is not int
            or not 0 < max_append_bytes <= 32 * 1024 * 1024):
        raise ValueError('sentinel_append_byte_budget_invalid')
    if not raw_path.exists():
        return [], {
            "enabled": True,
            "status": "raw_missing",
            "raw_path": str(raw_path),
            "cache_event_count": 0,
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path, meta_path = _cache_paths(cache_dir, cache_name, target_date)
    from src.engine.monitoring.sentinel_compact_store import stamp as cache_stamp
    stat = raw_path.stat()
    before_cache_stamp = cache_stamp(cache_path) if cache_path.exists() else None
    is_gzip_raw = raw_path.suffix == ".gz"
    raw_inode = getattr(stat, "st_ino", None)

    meta = _read_json(meta_path)
    raw_offset = int(meta.get("raw_offset") or 0)
    raw_size = max(int(stat.st_size), raw_offset) if is_gzip_raw else int(stat.st_size)
    migration = verified_schema_migration or {}
    generation = {"device": stat.st_dev, "inode": stat.st_ino, "size_bytes": stat.st_size,
                  "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns}
    forward = bool(migration and migration.get("population_proof") == "forward_only_stage_extension")
    if forward and not (
        migration.get("from_schema") == int(meta.get("schema_version") or 0)
        and migration.get("to_schema") == schema_version
        and migration.get("raw_offset") == raw_offset
        and 0 <= raw_offset <= raw_size and not is_gzip_raw
        and str(meta.get("raw_path")) == str(raw_path)
        and meta.get("raw_inode") == raw_inode
        and (migration.get("raw_generation") or {}).get("device") == stat.st_dev
        and (migration.get("raw_generation") or {}).get("inode") == stat.st_ino
        and stat.st_size >= (migration.get("raw_generation") or {}).get("size_bytes", raw_size + 1)
        and (stat.st_size > migration["raw_generation"]["size_bytes"]
             or (stat.st_mtime_ns == migration["raw_generation"].get("mtime_ns")
                 and stat.st_ctime_ns == migration["raw_generation"].get("ctime_ns")))
        and migration.get("historical_stage_coverage") == "not_backfilled_before_raw_offset"
        and cache_path.exists()
    ):
        raise ValueError("forward_cache_schema_source_changed")
    if migration and not forward and migration.get("raw_generation") != generation:
        raise ValueError("verified_cache_schema_source_changed")
    schema_migrated = forward or bool(migration and migration.get("population_proof") == "verified_zero_stage_census"
        and int(meta.get("schema_version") or 0) == migration.get("from_schema")
        and raw_offset == raw_size and not is_gzip_raw)
    stale_cache = (
        (int(meta.get("schema_version") or 0) != schema_version and not schema_migrated)
        or str(meta.get("raw_path") or "") != str(raw_path)
        or int(meta.get("raw_inode") or -1) != int(raw_inode or -1)
        or raw_offset > raw_size
        or not cache_path.exists()
        or (meta.get('raw_generation') and raw_size == meta.get('raw_size')
            and meta['raw_generation'] != generation)
    )
    if (compact_index and not stale_cache and meta.get('cache_generation')
            and before_cache_stamp != meta['cache_generation']):
        raise ValueError('sentinel_cache_generation_changed')
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
                    remaining = max_append_bytes - (line_start-raw_offset)
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
                if compact_index and cache_name == 'buy_funnel_sentinel_events' and schema_version in (19,20):
                    from src.engine.monitoring.sentinel_source_window import _epoch
                    try:
                        if not isinstance(payload,dict):
                            raise ValueError('source_window_raw_not_object')
                        _epoch(payload.get('emitted_at'))
                    except (ValueError,TypeError,OverflowError):
                        decode_errors += 1
                        last_good_offset = raw_handle.tell()
                        continue
                parsed = parse_payload(payload) if isinstance(payload, dict) else None
                if parsed is not None:
                    if compact_index and project_loaded_payload is not None:
                        original = parsed
                        parsed = project_loaded_payload(parsed)
                        if (not isinstance(parsed, dict) or any(parsed.get(k) != v
                                for k, v in original.items() if k != 'fields')):
                            raise ValueError('sentinel_cache_projection_population_changed')
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
    projection_applied = meta.get('cache_projection_version')
    projection_skip = None
    rewrite = bool(project_loaded_payload and cache_projection_version
                   and projection_applied != cache_projection_version)
    reusable_projection = (compact_index and not stale_cache and not rewrite
        and not meta.get('cache_projection_skip_reason')
        and meta.get('cache_generation') == before_cache_stamp
        and before_cache_stamp is not None)
    if reusable_projection:
        row_count = int(meta['cache_event_count']) + appended_cache_rows
    else:
        temporary = None
        try:
            before_cache = cache_path.stat()
            writer = None
            if rewrite:
                fd, temporary = tempfile.mkstemp(prefix='.sentinel-projection-', dir=cache_path.parent)
                writer = os.fdopen(fd, 'w', encoding='utf-8')
            try:
                with cache_path.open('r', encoding='utf-8', errors='replace') as cache_handle:
                    for raw_line in cache_handle:
                        if '\ufffd' in raw_line:
                            projection_skip = 'unverified_cache_encoding_preserved'
                        if not raw_line.strip():
                            continue
                        try:
                            row = json.loads(raw_line, object_pairs_hook=decode_object)
                        except json.JSONDecodeError:
                            projection_skip = 'malformed_cached_row_preserved'
                            continue
                        if not isinstance(row, dict):
                            projection_skip = 'nonobject_cached_row_preserved'
                            continue
                        if project_loaded_payload is not None:
                            original = row
                            row = project_loaded_payload(row)
                            if (not isinstance(row, dict) or any(row.get(key) != value
                                    for key, value in original.items() if key != 'fields')):
                                raise ValueError('sentinel_cache_projection_population_changed')
                        row_count += 1
                        if load_rows and not compact_index:
                            rows.append(row)
                        if writer is not None:
                            writer.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
                if writer is not None:
                    writer.flush()
                    os.fsync(writer.fileno())
            finally:
                if writer is not None:
                    writer.close()
            after_cache = cache_path.stat()
            if project_loaded_payload is not None and any(getattr(before_cache, key) != getattr(after_cache, key)
                    for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
                raise ValueError('sentinel_cache_changed_during_projection')
            # Validate migration and raw custody before replacing an optional cache.
            if schema_migrated and row_count != int(meta.get('cache_event_count') or 0) + appended_cache_rows:
                raise ValueError('verified_cache_schema_population_changed')
            if migration and not forward:
                current = raw_path.stat()
                if generation != {'device': current.st_dev, 'inode': current.st_ino, 'size_bytes': current.st_size,
                                  'mtime_ns': current.st_mtime_ns, 'ctime_ns': current.st_ctime_ns}:
                    raise ValueError('verified_cache_schema_source_changed')
            if forward:
                current = raw_path.stat()
                if current.st_dev != stat.st_dev or current.st_ino != raw_inode or current.st_size < last_good_offset:
                    raise ValueError('forward_cache_schema_source_changed')
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
    if (final_stat.st_dev != stat.st_dev or final_stat.st_ino != stat.st_ino
            or (not is_gzip_raw and final_stat.st_size < last_good_offset)):
        raise ValueError('sentinel_raw_generation_changed_during_load')
    final_stat_size = int(final_stat.st_size)
    final_raw_size = (
        max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
    )
    new_meta = {
        'raw_generation': {'device': final_stat.st_dev, 'inode': final_stat.st_ino,
                           'size_bytes': final_stat.st_size, 'mtime_ns': final_stat.st_mtime_ns,
                           'ctime_ns': final_stat.st_ctime_ns},
        'cache_generation': cache_stamp(cache_path),
        'compact_index_enabled': compact_index,
        'cache_body_rescanned': not reusable_projection,
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
        "schema_migration_receipt": migration if schema_migrated else meta.get("schema_migration_receipt"),
        "cache_projection_version": projection_applied,
        "cache_projection_skip_reason": projection_skip,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    if compact_index and cache_name == 'buy_funnel_sentinel_events' and schema_version in (19, 20):
        from src.engine.monitoring.sentinel_source_window import maintain
        new_meta['source_window_projection'] = maintain(cache_path,
            before_cache_stamp if reusable_projection else None, new_meta,
            previous_state=meta.get('source_window_projection'))
    _write_json(meta_path, new_meta)
    if compact_index and load_rows:
        # Seal the durable native cache before optional acceleration. Index
        # failure leaves a verified cache that the next call can rebuild from;
        # it does not publish a report or advance an uncommitted index cursor.
        from src.engine.monitoring.sentinel_compact_store import indexed_rows
        rows = list(indexed_rows(cache_path, expected_count=row_count,
            previous_stamp=before_cache_stamp if reusable_projection else None))
        new_meta['materialized_event_count'] = len(rows)
    return rows, {
        "enabled": True,
        "status": "ok",
        **new_meta,
    }


def load_verified_day_projection(*, raw_path, cache_dir, cache_name, parser_version,
                                 parse_payload):
    """Immutable day facts; a changed shard rebuilds only that shard.

    This stricter profile leaves the existing intraday append cache untouched.
    Economic policy/cost hashes belong to replay, not to these lossless facts.
    """
    import hashlib
    import os
    import tempfile
    import fcntl

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                        allow_nan=False).encode()).hexdigest()

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
            cache_valid = (isinstance(body, dict) and body.get("generation") == before
                and body.get("parser_version") == parser_version
                and body.get("raw_path") == str(raw_path.resolve())
                and isinstance(body.get("rows"), list) and isinstance(body.get("census"), dict)
                and isinstance(body.get("source_sha256"), str) and len(body["source_sha256"]) == 64
                and cached.get("body_sha256") == digest(body))
        except (ValueError, TypeError):
            cache_valid = False
        if cache_valid:
            return body["rows"], {**body["census"], "raw_scanned": False,
                                  "source_sha256": body["source_sha256"]}
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
        body = {"generation": before, "parser_version": parser_version,
                "raw_path": str(raw_path.resolve()), "source_sha256": hasher.hexdigest(),
                "rows": rows, "census": counts}
        if owns_lock and complete and before == after:
            fd, temporary = tempfile.mkstemp(prefix=cache_path.name + ".", dir=cache_dir)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    json.dump({"body": body, "body_sha256": digest(body)}, output,
                              separators=(",", ":"), allow_nan=False)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, cache_path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return rows, {**counts, "raw_scanned": True, "source_sha256": hasher.hexdigest(),
                      "checkpoint_complete": complete and before == after}
