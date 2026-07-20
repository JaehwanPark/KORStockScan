"""File-backed dashboard data repository.

Legacy PostgreSQL raw dashboard tables were removed from the operating path.
Canonical sources are JSON/JSONL files, monitor snapshot manifests, Parquet,
and DuckDB-derived analytics.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import date
from pathlib import Path

from src.utils.constants import DATA_DIR

logger = logging.getLogger(__name__)

PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"


def _existing_or_gzip_path(path: Path) -> Path:
    if path.exists():
        return path
    gz_path = Path(f"{path}.gz")
    if gz_path.exists():
        return gz_path
    return path


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load_monitor_snapshot_file_first(kind: str, target_date: str) -> dict | None:
    """Load a monitor snapshot from the canonical JSON/GZip file source."""
    try:
        target_dt = date.fromisoformat(str(target_date))
    except ValueError:
        logger.warning("Invalid date format: %s", target_date)
        return None
    if target_dt > date.today():
        return None
    return _load_monitor_snapshot_from_file(kind, target_date)


def _load_monitor_snapshot_from_file(kind: str, target_date: str) -> dict | None:
    path = _existing_or_gzip_path(MONITOR_SNAPSHOT_DIR / f"{kind}_{target_date}.json")
    if not path.exists():
        return None
    try:
        with _open_text(path) as handle:
            return json.load(handle)
    except Exception as exc:
        logger.error("Failed to load monitor snapshot from file %s: %s", path, exc)
        return None


def _list_snapshot_kinds(target_date: str) -> list[str]:
    kinds = set()
    for path in MONITOR_SNAPSHOT_DIR.glob(f"*_{target_date}.json*"):
        if path.suffix not in {".json", ".gz"}:
            continue
        stem = path.name
        if stem.endswith(".gz"):
            stem = stem[:-3]
        if stem.endswith(".json"):
            stem = stem[:-5]
        maybe_kind = stem[: -(len(target_date) + 1)]
        if maybe_kind:
            kinds.add(maybe_kind)
    return sorted(kinds)


def load_pipeline_events(
    target_date: str,
    *,
    include_file_for_today: bool = True,
    prefer_file_for_past: bool = False,
    prefer_file_for_today: bool = False,
) -> list[dict]:
    """Return pipeline events from the canonical JSONL/GZip file source.

    Compatibility flags are accepted for existing callers. With legacy DB
    storage removed, same-day calls with include_file_for_today=False return no
    rows because there is no alternate DB source.
    """
    del prefer_file_for_past, prefer_file_for_today
    try:
        target_dt = date.fromisoformat(str(target_date))
    except ValueError:
        logger.warning("Invalid date format: %s", target_date)
        return []

    today = date.today()
    if target_dt > today:
        return []
    if target_dt == today and not include_file_for_today:
        return []
    return _load_pipeline_events_from_file(target_date)


def _load_pipeline_events_from_file(target_date: str) -> list[dict]:
    path = _existing_or_gzip_path(
        PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    )
    events = []
    if not path.exists():
        return events
    try:
        with _open_text(path) as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    events.append(json.loads(stripped))
                except json.JSONDecodeError:
                    pass
    except Exception as exc:
        logger.error("Failed to read pipeline events file %s: %s", path, exc)
    return events
