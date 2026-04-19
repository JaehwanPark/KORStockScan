"""Daily monitor snapshot and per-date log archive helpers."""

from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.utils.constants import DATA_DIR
from src.engine.dashboard_data_repository import (
    load_monitor_snapshot_prefer_db,
    upsert_monitor_snapshot,
)


LOG_ARCHIVE_DIR = DATA_DIR / "log_archive"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
SERVER_COMPARISON_REPORT_DIR = DATA_DIR / "report" / "server_comparison"
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
SERVER_COMPARISON_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _snapshot_path(kind: str, target_date: str) -> Path:
    safe_kind = str(kind or "").strip().lower().replace("-", "_")
    return MONITOR_SNAPSHOT_DIR / f"{safe_kind}_{target_date}.json"


def load_monitor_snapshot(kind: str, target_date: str) -> dict | None:
    """DB 우선, 당일 파일 우선으로 모니터 스냅샷을 로드합니다."""
    return load_monitor_snapshot_prefer_db(kind, target_date)


def save_monitor_snapshot(kind: str, target_date: str, payload: dict) -> Path:
    path = _snapshot_path(kind, target_date)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    # DB에도 저장 (병행)
    try:
        upsert_monitor_snapshot(kind, target_date, payload)
    except Exception as e:
        # DB 저장 실패는 로그만 남기고 파일 저장은 유지
        import logging
        logging.getLogger(__name__).warning("DB 저장 실패 (스냅샷 %s %s): %s", kind, target_date, e)
    return path


def _relative_to_repo(path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        return str(path.relative_to(repo_root))
    except Exception:
        return str(path)


def _upsert_generated_block(
    path: Path,
    *,
    block_id: str,
    content: str,
    insert_before: str | None = None,
) -> bool:
    if not path.exists():
        return False

    start_marker = f"<!-- {block_id}_START -->"
    end_marker = f"<!-- {block_id}_END -->"
    block = f"{start_marker}\n{content.rstrip()}\n{end_marker}"
    original = path.read_text(encoding="utf-8")

    if start_marker in original and end_marker in original:
        start = original.index(start_marker)
        end = original.index(end_marker) + len(end_marker)
        updated = f"{original[:start].rstrip()}\n\n{block}\n{original[end:].lstrip()}"
    elif insert_before and insert_before in original:
        updated = original.replace(insert_before, f"{block}\n\n{insert_before}", 1)
    else:
        updated = f"{original.rstrip()}\n\n{block}\n"

    path.write_text(updated, encoding="utf-8")
    return True


def _save_server_comparison_artifacts(target_date: str) -> dict[str, str] | None:
    from src.engine.server_report_comparison import (
        build_snapshot_summary,
        compare_server_reports,
        render_checklist_append_block,
        render_markdown_report,
    )

    comparison = compare_server_reports(
        target_date=target_date,
        remote_base_url="https://songstockscan.ddns.net",
        since_time="09:00:00",
        include_sections=("trade_review", "performance_tuning", "post_sell_feedback", "entry_pipeline_flow"),
    )
    summary = build_snapshot_summary(comparison)
    comparison_snapshot_path = save_monitor_snapshot("server_comparison", target_date, comparison)

    report_path = SERVER_COMPARISON_REPORT_DIR / f"server_comparison_{target_date}.md"
    report_path.write_text(render_markdown_report(comparison), encoding="utf-8")

    checklist_path = DOCS_DIR / f"{target_date}-stage2-todo-checklist.md"
    checklist_updated = False
    if checklist_path.exists():
        checklist_block = render_checklist_append_block(
            comparison,
            report_relpath=_relative_to_repo(report_path),
        )
        checklist_updated = _upsert_generated_block(
            checklist_path,
            block_id="AUTO_SERVER_COMPARISON",
            content=checklist_block,
            insert_before=f"## {target_date} 장후 체크리스트 (15:30~)",
        )

    return {
        "server_comparison_snapshot": str(comparison_snapshot_path),
        "server_comparison_report": str(report_path),
        "server_comparison_checklist_updated": str(checklist_updated).lower(),
        "server_comparison_summary_generated_at": str(summary.get("generated_at") or ""),
    }


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
    from src.engine.add_blocked_lock_report import build_add_blocked_lock_report
    from src.engine.buy_pause_guard import evaluate_buy_pause_guard
    from src.engine.sniper_missed_entry_counterfactual import build_missed_entry_counterfactual_report
    from src.engine.sniper_performance_tuning_report import build_performance_tuning_report
    from src.engine.sniper_post_sell_feedback import build_post_sell_feedback_report
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

    post_sell_feedback = build_post_sell_feedback_report(
        target_date=target_date,
        evaluate_now=True,
    )
    post_sell_feedback.setdefault("meta", {})
    post_sell_feedback["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    post_sell_feedback["meta"]["snapshot_kind"] = "post_sell_feedback"
    missed_entry_counterfactual = build_missed_entry_counterfactual_report(
        target_date=target_date,
    )
    missed_entry_counterfactual.setdefault("meta", {})
    missed_entry_counterfactual["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    missed_entry_counterfactual["meta"]["snapshot_kind"] = "missed_entry_counterfactual"
    add_blocked_lock = build_add_blocked_lock_report(target_date=target_date)
    add_blocked_lock.setdefault("meta", {})
    add_blocked_lock["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    add_blocked_lock["meta"]["snapshot_kind"] = "add_blocked_lock"
    buy_pause_guard = evaluate_buy_pause_guard(target_date, send_alert=True)
    trade_review["meta"]["buy_pause_guard"] = buy_pause_guard
    performance_tuning["meta"]["buy_pause_guard"] = buy_pause_guard
    post_sell_feedback["meta"]["buy_pause_guard"] = buy_pause_guard
    missed_entry_counterfactual["meta"]["buy_pause_guard"] = buy_pause_guard
    add_blocked_lock["meta"]["buy_pause_guard"] = buy_pause_guard

    trade_review_path = save_monitor_snapshot("trade_review", target_date, trade_review)
    performance_path = save_monitor_snapshot("performance_tuning", target_date, performance_tuning)
    post_sell_path = save_monitor_snapshot("post_sell_feedback", target_date, post_sell_feedback)
    missed_entry_counterfactual_path = save_monitor_snapshot("missed_entry_counterfactual", target_date, missed_entry_counterfactual)
    add_blocked_lock_path = save_monitor_snapshot("add_blocked_lock", target_date, add_blocked_lock)
    result = {
        "trade_review": str(trade_review_path),
        "performance_tuning": str(performance_path),
        "post_sell_feedback": str(post_sell_path),
        "missed_entry_counterfactual": str(missed_entry_counterfactual_path),
        "add_blocked_lock": str(add_blocked_lock_path),
    }
    try:
        server_comparison = _save_server_comparison_artifacts(target_date)
    except Exception as exc:
        result["server_comparison_error"] = f"{type(exc).__name__}: {exc}"
        return result

    if server_comparison:
        result.update(server_comparison)
    return result
