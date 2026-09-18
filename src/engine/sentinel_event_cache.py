from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.utils.jsonl_io import existing_or_gzip_path

PayloadParser = Callable[[dict[str, Any]], dict[str, Any] | None]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tmp_path.replace(path)


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


def update_and_load_cached_event_rows(
    *,
    raw_path: Path,
    cache_dir: Path,
    cache_name: str,
    target_date: str,
    schema_version: int,
    parse_payload: PayloadParser,
    verified_schema_migration: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Maintain a slim append-only cache for sentinel pipeline-event scans.

    The raw pipeline stream is lossless and can be very large intraday. Sentinels
    only need a filtered subset of fields, so this cache parses new raw bytes
    since the previous run and rereads the slimmer sentinel-owned cache.
    """

    raw_path = existing_or_gzip_path(raw_path)
    if not raw_path.exists():
        return [], {
            "enabled": True,
            "status": "raw_missing",
            "raw_path": str(raw_path),
            "cache_event_count": 0,
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path, meta_path = _cache_paths(cache_dir, cache_name, target_date)
    stat = raw_path.stat()
    is_gzip_raw = raw_path.suffix == ".gz"
    raw_inode = getattr(stat, "st_ino", None)

    meta = _read_json(meta_path)
    raw_offset = int(meta.get("raw_offset") or 0)
    raw_size = max(int(stat.st_size), raw_offset) if is_gzip_raw else int(stat.st_size)
    migration = verified_schema_migration or {}
    generation = {"device": stat.st_dev, "inode": stat.st_ino, "size_bytes": stat.st_size,
                  "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns}
    if migration and migration.get("raw_generation") != generation:
        raise ValueError("verified_cache_schema_source_changed")
    schema_migrated = bool(migration and migration.get("population_proof") == "verified_zero_stage_census"
        and int(meta.get("schema_version") or 0) == migration.get("from_schema")
        and raw_offset == raw_size and not is_gzip_raw)
    stale_cache = (
        (int(meta.get("schema_version") or 0) != schema_version and not schema_migrated)
        or str(meta.get("raw_path") or "") != str(raw_path)
        or int(meta.get("raw_inode") or -1) != int(raw_inode or -1)
        or raw_offset > raw_size
        or not cache_path.exists()
    )
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
                parsed = parse_payload(payload) if isinstance(payload, dict) else None
                if parsed is not None:
                    cache_handle.write(
                        json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    appended_cache_rows += 1
                last_good_offset = raw_handle.tell()
                if last_good_offset <= line_start:
                    break

    rows: list[dict[str, Any]] = []
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8", errors="replace") as cache_handle:
            for raw_line in cache_handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)

    if schema_migrated and len(rows) != meta.get("cache_event_count"):
        raise ValueError("verified_cache_schema_population_changed")
    if migration:
        current = raw_path.stat()
        if generation != {"device": current.st_dev, "inode": current.st_ino, "size_bytes": current.st_size,
                          "mtime_ns": current.st_mtime_ns, "ctime_ns": current.st_ctime_ns}:
            raise ValueError("verified_cache_schema_source_changed")
    final_stat_size = int(raw_path.stat().st_size) if raw_path.exists() else raw_size
    final_raw_size = (
        max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
    )
    new_meta = {
        "schema_version": schema_version,
        "raw_path": str(raw_path),
        "raw_inode": raw_inode,
        "raw_offset": last_good_offset,
        "raw_size": final_raw_size,
        "cache_path": str(cache_path),
        "cache_event_count": len(rows),
        "appended_raw_lines": appended_raw_lines,
        "appended_cache_rows": appended_cache_rows,
        "decode_errors": decode_errors,
        "rebuilt": stale_cache,
        "schema_migration_receipt": migration if schema_migrated else meta.get("schema_migration_receipt"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(meta_path, new_meta)
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
