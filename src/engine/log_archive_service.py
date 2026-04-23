"""Daily monitor snapshot and per-date log archive helpers."""

from __future__ import annotations

import gzip
import json
import os
import time
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
MONITOR_SNAPSHOT_MANIFEST_DIR = MONITOR_SNAPSHOT_DIR / "manifests"
SERVER_COMPARISON_REPORT_DIR = DATA_DIR / "report" / "server_comparison"
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_SNAPSHOT_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
SERVER_COMPARISON_REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _env_float(name: str, default: float = 0.0) -> float:
    raw_value = str(os.getenv(name, "")).strip()
    if not raw_value:
        return default
    try:
        return max(0.0, float(raw_value))
    except Exception:
        return default


def _stage_io_delay_sec(base_delay: float, snapshot_kind: str) -> float:
    delay_map = {
        "performance_tuning": _env_float("MONITOR_SNAPSHOT_PERFORMANCE_TUNING_IO_DELAY_SEC", base_delay),
        "server_comparison": _env_float(
            "MONITOR_SNAPSHOT_SERVER_COMPARISON_IO_DELAY_SEC",
            base_delay,
        ),
    }
    return delay_map.get(snapshot_kind, base_delay)


def _snapshot_path(kind: str, target_date: str) -> Path:
    safe_kind = str(kind or "").strip().lower().replace("-", "_")
    return MONITOR_SNAPSHOT_DIR / f"{safe_kind}_{target_date}.json"


def _snapshot_manifest_path(target_date: str, profile: str) -> Path:
    safe_profile = str(profile or "full").strip().lower().replace("-", "_")
    return MONITOR_SNAPSHOT_MANIFEST_DIR / f"monitor_snapshot_manifest_{target_date}_{safe_profile}.json"


def load_monitor_snapshot(kind: str, target_date: str) -> dict | None:
    """파일 우선으로 모니터 스냅샷을 로드하고, 필요할 때만 legacy DB를 조회합니다."""
    path = _snapshot_path(kind, target_date)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            pass
    return load_monitor_snapshot_prefer_db(kind, target_date, prefer_file_for_past=True)


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


def save_monitor_snapshot_manifest(target_date: str, *, profile: str, snapshots: dict[str, str]) -> Path:
    manifest_path = _snapshot_manifest_path(target_date, profile)
    tracked_paths = {
        key: value
        for key, value in (snapshots or {}).items()
        if isinstance(value, str) and value.startswith("/")
    }
    payload = {
        "target_date": target_date,
        "profile": str(profile or "full"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_kinds": sorted(tracked_paths.keys()),
        "snapshot_paths": tracked_paths,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


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
    return save_monitor_snapshots_for_date_with_profile(
        target_date,
        profile="full",
        io_delay_sec=0.0,
        include_server_comparison=True,
    )


def save_monitor_snapshots_for_date_with_profile(
    target_date: str,
    *,
    profile: str = "full",
    io_delay_sec: float = 0.0,
    include_server_comparison: bool | None = None,
) -> dict[str, str]:
    from src.engine.add_blocked_lock_report import build_add_blocked_lock_report
    from src.engine.buy_pause_guard import evaluate_buy_pause_guard
    from src.engine.sniper_missed_entry_counterfactual import build_missed_entry_counterfactual_report
    from src.engine.sniper_performance_tuning_report import build_performance_tuning_report
    from src.engine.sniper_post_sell_feedback import build_post_sell_feedback_report
    from src.engine.sniper_trade_review_report import build_trade_review_report
    from src.engine.wait6579_ev_cohort_report import build_wait6579_ev_cohort_report

    normalized_profile = str(profile or "full").strip().lower()
    if normalized_profile not in {"full", "intraday_light"}:
        raise ValueError(f"Unsupported monitor snapshot profile: {profile}")
    server_comparison_policy_enabled = os.getenv("KORSTOCKSCAN_ENABLE_SERVER_COMPARISON", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if include_server_comparison is None:
        include_server_comparison = normalized_profile == "full" and server_comparison_policy_enabled

    sleep_sec = max(0.0, float(io_delay_sec))
    trend_env_name = (
        "MONITOR_SNAPSHOT_INTRADAY_TREND_MAX_DATES"
        if normalized_profile == "intraday_light"
        else "MONITOR_SNAPSHOT_FULL_TREND_MAX_DATES"
    )
    trend_max_dates = None
    trend_env_value = os.getenv(trend_env_name, "").strip()
    if trend_env_value:
        try:
            trend_max_dates = int(trend_env_value)
        except Exception:
            trend_max_dates = None
    snapshot_order = (
        (
            "trade_review",
            lambda: build_trade_review_report(
                target_date=target_date,
                since_time=None,
                top_n=300,
                scope="entered",
            ),
        ),
        (
            "performance_tuning",
            lambda: build_performance_tuning_report(
                target_date=target_date,
                since_time=None,
                trend_max_dates=trend_max_dates,
            ),
        ),
        (
            "wait6579_ev_cohort",
            lambda: build_wait6579_ev_cohort_report(
                target_date=target_date,
            ),
        ),
        (
            "post_sell_feedback",
            lambda: build_post_sell_feedback_report(
                target_date=target_date,
                evaluate_now=True,
            ),
        ),
        (
            "missed_entry_counterfactual",
            lambda: build_missed_entry_counterfactual_report(
                target_date=target_date,
            ),
        ),
        (
            "add_blocked_lock",
            lambda: build_add_blocked_lock_report(
                target_date=target_date,
            ),
        ),
    )
    allowed_by_profile = {
        "full": {
            "trade_review",
            "performance_tuning",
            "wait6579_ev_cohort",
            "post_sell_feedback",
            "missed_entry_counterfactual",
            "add_blocked_lock",
        },
        "intraday_light": {
            "trade_review",
            "performance_tuning",
            "wait6579_ev_cohort",
        },
    }

    send_alert = normalized_profile == "full"
    buy_pause_guard = evaluate_buy_pause_guard(target_date, send_alert=send_alert)
    result: dict[str, str] = {
        "profile": normalized_profile,
        "io_delay_sec": f"{sleep_sec:.3f}",
    }
    result["io_delay_sec_per_stage"] = json.dumps(
        {
            "default": f"{sleep_sec:.3f}",
            "performance_tuning": f"{_stage_io_delay_sec(sleep_sec, 'performance_tuning'):.3f}",
            "server_comparison": f"{_stage_io_delay_sec(sleep_sec, 'server_comparison'):.3f}",
        }
    )
    if trend_max_dates is not None:
        result["trend_max_dates"] = str(trend_max_dates)

    selected_kinds = allowed_by_profile[normalized_profile]
    selected_entries = [item for item in snapshot_order if item[0] in selected_kinds]
    for idx, (snapshot_kind, build_fn) in enumerate(selected_entries):
        stage_delay = _stage_io_delay_sec(sleep_sec, snapshot_kind)
        if idx > 0 and stage_delay > 0:
            time.sleep(stage_delay)
        payload = build_fn()
        payload.setdefault("meta", {})
        payload["meta"]["saved_snapshot_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload["meta"]["snapshot_kind"] = snapshot_kind
        payload["meta"]["buy_pause_guard"] = buy_pause_guard
        result[snapshot_kind] = str(save_monitor_snapshot(snapshot_kind, target_date, payload))

    def _finalize_snapshot_manifest() -> dict[str, str]:
        manifest_path = save_monitor_snapshot_manifest(
            target_date,
            profile=normalized_profile,
            snapshots=result,
        )
        result["snapshot_manifest"] = str(manifest_path)
        return result

    if not include_server_comparison:
        if not server_comparison_policy_enabled:
            result["server_comparison_status"] = "policy_disabled"
        return _finalize_snapshot_manifest()

    try:
        comparison_delay = _stage_io_delay_sec(sleep_sec, "server_comparison")
        if comparison_delay > 0:
            time.sleep(comparison_delay)
        server_comparison = _save_server_comparison_artifacts(target_date)
    except Exception as exc:
        result["server_comparison_error"] = f"{type(exc).__name__}: {exc}"
        return _finalize_snapshot_manifest()

    if server_comparison:
        result.update(server_comparison)
    return _finalize_snapshot_manifest()
