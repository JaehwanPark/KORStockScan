"""Daily monitor snapshot and per-date log archive helpers."""

from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.utils.constants import DATA_DIR


LOG_ARCHIVE_DIR = DATA_DIR / "log_archive"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"

LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _snapshot_path(kind: str, target_date: str) -> Path:
    safe_kind = str(kind or "").strip().lower().replace("-", "_")
    return MONITOR_SNAPSHOT_DIR / f"{safe_kind}_{target_date}.json"


def load_monitor_snapshot(kind: str, target_date: str) -> dict | None:
    path = _snapshot_path(kind, target_date)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_monitor_snapshot(kind: str, target_date: str, payload: dict) -> Path:
    path = _snapshot_path(kind, target_date)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def archived_log_path(log_path: Path, target_date: str) -> Path:
    return LOG_ARCHIVE_DIR / str(target_date) / f"{log_path.name}.gz"


def _iter_raw_candidate_paths(log_path: Path) -> list[Path]:
    candidates = [log_path]
    candidates.extend(
        sorted(
            [path for path in log_path.parent.glob(f"{log_path.name}.*") if path.suffix != ".gz"],
            key=lambda path: path.name,
        )
    )
    return candidates


def _read_matching_lines(path: Path, *, target_date: str, marker: str | None = None) -> list[str]:
    if not path.exists() or not path.is_file():
        return []

    opener = gzip.open if path.suffix == ".gz" else open
    lines: list[str] = []
    with opener(path, "rt", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            if f"[{target_date}" not in raw_line:
                continue
            if marker and marker not in raw_line:
                continue
            lines.append(raw_line.strip())
    return lines


def iter_target_log_lines(
    log_paths: Iterable[Path],
    *,
    target_date: str,
    marker: str | None = None,
) -> list[str]:
    lines: list[str] = []
    for log_path in log_paths:
        raw_lines: list[str] = []
        for candidate in _iter_raw_candidate_paths(log_path):
            raw_lines.extend(_read_matching_lines(candidate, target_date=target_date, marker=marker))
        if raw_lines:
            lines.extend(raw_lines)
            continue
        archive_path = archived_log_path(log_path, target_date)
        lines.extend(_read_matching_lines(archive_path, target_date=target_date, marker=marker))
    return lines


def archive_target_date_logs(target_date: str, log_paths: Iterable[Path]) -> list[dict]:
    archived: list[dict] = []
    for log_path in log_paths:
        lines: list[str] = []
        for candidate in _iter_raw_candidate_paths(log_path):
            lines.extend(_read_matching_lines(candidate, target_date=target_date))
        if not lines:
            continue

        archive_path = archived_log_path(log_path, target_date)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        payload = "\n".join(lines).strip()
        if payload:
            payload = f"{payload}\n"
        with gzip.open(archive_path, "wt", encoding="utf-8") as handle:
            handle.write(payload)
        archived.append(
            {
                "log_name": log_path.name,
                "path": str(archive_path),
                "line_count": len(lines),
                "archived_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": archive_path.stat().st_size if archive_path.exists() else 0,
            }
        )
    return archived


def save_monitor_snapshots_for_date(target_date: str) -> dict[str, str]:
    from src.engine.sniper_performance_tuning_report import build_performance_tuning_report
    from src.engine.sniper_post_sell_feedback import (
        evaluate_post_sell_candidates,
        post_sell_feedback_summary_to_dict,
    )
    from src.engine.sniper_trade_review_report import build_trade_review_report

    trade_review = build_trade_review_report(
        target_date=target_date,
        since_time=None,
        top_n=300,
        scope="entered",
    )
    trade_review.setdefault("meta", {})
    trade_review["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trade_review["meta"]["snapshot_kind"] = "trade_review"

    performance_tuning = build_performance_tuning_report(
        target_date=target_date,
        since_time=None,
    )
    performance_tuning.setdefault("meta", {})
    performance_tuning["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    performance_tuning["meta"]["snapshot_kind"] = "performance_tuning"

    post_sell_feedback = post_sell_feedback_summary_to_dict(
        evaluate_post_sell_candidates(target_date=target_date)
    )
    post_sell_feedback.setdefault("meta", {})
    post_sell_feedback["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    post_sell_feedback["meta"]["snapshot_kind"] = "post_sell_feedback"

    trade_review_path = save_monitor_snapshot("trade_review", target_date, trade_review)
    performance_path = save_monitor_snapshot("performance_tuning", target_date, performance_tuning)
    post_sell_path = save_monitor_snapshot("post_sell_feedback", target_date, post_sell_feedback)
    return {
        "trade_review": str(trade_review_path),
        "performance_tuning": str(performance_path),
        "post_sell_feedback": str(post_sell_path),
    }
