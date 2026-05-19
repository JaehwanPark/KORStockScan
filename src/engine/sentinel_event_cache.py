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
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _cache_paths(cache_dir: Path, cache_name: str, target_date: str) -> tuple[Path, Path]:
    safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in cache_name)
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
    stale_cache = (
        int(meta.get("schema_version") or 0) != schema_version
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
                    cache_handle.write(json.dumps(parsed, ensure_ascii=False, separators=(",", ":")) + "\n")
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

    final_stat_size = int(raw_path.stat().st_size) if raw_path.exists() else raw_size
    final_raw_size = max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
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
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(meta_path, new_meta)
    return rows, {
        "enabled": True,
        "status": "ok",
        **new_meta,
    }
