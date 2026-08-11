from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.engine.pipeline_event_summary import (
    PRODUCER_SUMMARY_STAGES,
    default_reason_label,
    load_summary_rows,
    producer_summary_paths,
    update_and_load_pipeline_event_summaries,
)

REPORT_DIRNAME = "pipeline_event_verbosity"


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _summary_dir() -> Path:
    return DATA_DIR / "pipeline_event_summaries"


def report_paths(target_date: str) -> tuple[Path, Path]:
    report_dir = DATA_DIR / "report" / REPORT_DIRNAME
    return (
        report_dir / f"pipeline_event_verbosity_{target_date}.json",
        report_dir / f"pipeline_event_verbosity_{target_date}.md",
    )


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _line_count_and_stage_bytes(raw_path: Path) -> dict[str, Any]:
    raw_path = existing_or_gzip_path(raw_path)
    if not raw_path.exists():
        return {
            "exists": False,
            "raw_size_bytes": 0,
            "raw_storage_size_bytes": 0,
            "raw_line_count": 0,
            "high_volume_line_count": 0,
            "high_volume_bytes": 0,
            "high_volume_stage_counts": {},
            "high_volume_stage_bytes": {},
        }
    raw_line_count = 0
    raw_stream_bytes = 0
    high_volume_line_count = 0
    high_volume_bytes = 0
    stage_counts: Counter[str] = Counter()
    stage_bytes: Counter[str] = Counter()
    latest_emitted_at = ""
    earliest_eligible_event_at = ""
    latest_eligible_event_at = ""
    with open_text_auto(raw_path, errors="replace") as handle:
        for raw_line in handle:
            raw_stream_bytes += len(raw_line.encode("utf-8"))
            line = raw_line.strip()
            if not line:
                continue
            raw_line_count += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                not isinstance(payload, dict)
                or payload.get("event_type") != "pipeline_event"
            ):
                continue
            emitted_at = _safe_str(payload.get("emitted_at"))
            latest_emitted_at = max(latest_emitted_at, emitted_at)
            stage = _safe_str(payload.get("stage"))
            if stage not in PRODUCER_SUMMARY_STAGES:
                continue
            if emitted_at:
                earliest_eligible_event_at = (
                    min(earliest_eligible_event_at, emitted_at)
                    if earliest_eligible_event_at
                    else emitted_at
                )
                latest_eligible_event_at = max(latest_eligible_event_at, emitted_at)
            line_bytes = len(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
                    "utf-8"
                )
            )
            high_volume_line_count += 1
            high_volume_bytes += line_bytes
            stage_counts[stage] += 1
            stage_bytes[stage] += line_bytes
    raw_storage_size = int(raw_path.stat().st_size)
    raw_size = raw_stream_bytes
    return {
        "exists": True,
        "raw_size_bytes": raw_size,
        "raw_storage_size_bytes": raw_storage_size,
        "raw_line_count": raw_line_count,
        "high_volume_line_count": high_volume_line_count,
        "high_volume_bytes": high_volume_bytes,
        "high_volume_line_share_pct": (
            round((high_volume_line_count / raw_line_count) * 100.0, 2)
            if raw_line_count
            else 0.0
        ),
        "high_volume_byte_share_pct": (
            round((high_volume_bytes / raw_size) * 100.0, 2) if raw_size else 0.0
        ),
        "high_volume_stage_counts": dict(sorted(stage_counts.items())),
        "high_volume_stage_bytes": dict(sorted(stage_bytes.items())),
        "latest_pipeline_event_at": latest_emitted_at or None,
        "earliest_eligible_event_at": earliest_eligible_event_at or None,
        "latest_eligible_event_at": latest_eligible_event_at or None,
    }


def _summary_counts(
    rows: list[dict[str, Any]],
) -> tuple[Counter[str], Counter[str], int]:
    stage_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    total = 0
    for row in rows:
        stage = _safe_str(row.get("stage"))
        if stage not in PRODUCER_SUMMARY_STAGES:
            continue
        count = int(row.get("event_count") or 0)
        if count <= 0:
            continue
        stage_counts[stage] += count
        total += count
        if stage.startswith("blocked_"):
            blocker_counts[_safe_str(row.get("reason_label")) or f"{stage}:-"] += count
    return stage_counts, blocker_counts, total


def _diff_counter(left: Counter[str], right: Counter[str]) -> dict[str, dict[str, int]]:
    diff: dict[str, dict[str, int]] = {}
    for key in sorted(set(left) | set(right)):
        left_count = int(left.get(key, 0))
        right_count = int(right.get(key, 0))
        if left_count != right_count:
            diff[key] = {
                "raw_derived": left_count,
                "producer": right_count,
                "delta": right_count - left_count,
            }
    return diff


def _previous_parity_pass_count(target_date: str) -> int:
    try:
        current = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        return 0
    count = 0
    for offset in (1, 2, 3, 4, 5):
        candidate = (current - timedelta(days=offset)).isoformat()
        json_path, _ = report_paths(candidate)
        payload = _read_json(json_path)
        if payload.get("state") in {"v2_shadow_parity_pass", "suppress_candidate"}:
            count += 1
        elif payload:
            break
    return count


def _producer_coverage(
    rows: list[dict[str, Any]], manifest: dict[str, Any]
) -> tuple[str, str]:
    first_event_at = _safe_str(manifest.get("coverage_first_event_at"))
    last_event_at = _safe_str(manifest.get("coverage_last_event_at"))
    if not first_event_at:
        first_values = [
            _safe_str(row.get("first_seen"))
            for row in rows
            if _safe_str(row.get("first_seen"))
        ]
        first_event_at = min(first_values) if first_values else ""
    if not last_event_at:
        last_values = [
            _safe_str(row.get("last_seen"))
            for row in rows
            if _safe_str(row.get("last_seen"))
        ]
        last_event_at = max(last_values) if last_values else ""
    return first_event_at, last_event_at


def _common_completed_minute_watermark(*coverage_ends: str) -> str:
    parsed: list[datetime] = []
    for value in coverage_ends:
        if not value:
            continue
        try:
            parsed.append(datetime.fromisoformat(value))
        except ValueError:
            return ""
    if len(parsed) != len(coverage_ends):
        return ""
    watermark = min(parsed).replace(second=0, microsecond=0)
    return watermark.isoformat(timespec="seconds")


def _rows_through_watermark(
    rows: list[dict[str, Any]], watermark: str
) -> list[dict[str, Any]]:
    if not watermark:
        return []
    return [
        row
        for row in rows
        if _safe_str(row.get("bucket_end"))
        and _safe_str(row.get("bucket_end")) <= watermark
    ]


def build_pipeline_event_verbosity_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    raw_path = existing_or_gzip_path(_pipeline_events_path(target_date))
    raw_stats = _line_count_and_stage_bytes(raw_path)
    raw_summary_rows, raw_summary_meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=_summary_dir(),
        target_date=target_date,
        reason_labeler=default_reason_label,
        include_samples=False,
        summary_stages=PRODUCER_SUMMARY_STAGES,
        summary_profile="producer_parity",
    )
    producer_path, producer_manifest_path = producer_summary_paths(
        _summary_dir(), target_date
    )
    producer_actual_path = existing_or_gzip_path(producer_path)
    producer_manifest = _read_json(producer_manifest_path)
    producer_rows = load_summary_rows(producer_path, include_samples=False)
    raw_stage, raw_blocker, raw_total = _summary_counts(raw_summary_rows)
    producer_stage, producer_blocker, producer_total = _summary_counts(producer_rows)
    stage_diff = _diff_counter(raw_stage, producer_stage)
    blocker_diff = _diff_counter(raw_blocker, producer_blocker)
    producer_exists = producer_actual_path.exists() and bool(producer_rows)
    manifest_exists = producer_manifest_path.exists()
    producer_updated_at = _safe_str(producer_manifest.get("updated_at"))
    raw_coverage_start = _safe_str(raw_stats.get("earliest_eligible_event_at"))
    raw_coverage_end = _safe_str(raw_stats.get("latest_eligible_event_at"))
    producer_coverage_start, producer_coverage_end = _producer_coverage(
        producer_rows, producer_manifest
    )
    producer_start_complete = bool(
        producer_exists
        and raw_coverage_start
        and producer_coverage_start
        and producer_coverage_start <= raw_coverage_start
    )
    producer_pending_flush = bool(
        producer_exists
        and manifest_exists
        and raw_coverage_end
        and producer_coverage_end
        and raw_coverage_end > producer_coverage_end
        and (not producer_updated_at or raw_coverage_end > producer_updated_at)
    )
    comparison_watermark = _common_completed_minute_watermark(
        raw_coverage_end, producer_coverage_end
    )
    comparison_raw_rows = _rows_through_watermark(
        raw_summary_rows, comparison_watermark
    )
    comparison_producer_rows = _rows_through_watermark(
        producer_rows, comparison_watermark
    )
    (
        comparison_raw_stage,
        comparison_raw_blocker,
        comparison_raw_total,
    ) = _summary_counts(comparison_raw_rows)
    (
        comparison_producer_stage,
        comparison_producer_blocker,
        comparison_producer_total,
    ) = _summary_counts(comparison_producer_rows)
    comparison_stage_diff = _diff_counter(
        comparison_raw_stage, comparison_producer_stage
    )
    comparison_blocker_diff = _diff_counter(
        comparison_raw_blocker, comparison_producer_blocker
    )
    common_watermark_ok = bool(
        producer_exists
        and producer_start_complete
        and comparison_raw_total > 0
        and not comparison_stage_diff
        and not comparison_blocker_diff
        and comparison_raw_total == comparison_producer_total
    )
    no_eligible_events = raw_total == 0
    parity_ok = bool(
        no_eligible_events
        or (
            producer_exists
            and producer_start_complete
            and not producer_pending_flush
            and not stage_diff
            and not blocker_diff
            and raw_total == producer_total
        )
    )
    previous_pass_count = _previous_parity_pass_count(target_date)
    suppress_candidate = bool(parity_ok and previous_pass_count >= 1)
    if not raw_path.exists():
        state = "blocked"
        recommended = "raw_missing"
    elif no_eligible_events:
        state = "v2_shadow_no_eligible_events"
        recommended = "observe_no_eligible_events"
    elif not producer_exists or not manifest_exists:
        state = "v2_shadow_missing"
        recommended = "open_shadow_order"
    elif not producer_start_complete:
        state = "v2_shadow_partial_coverage"
        recommended = "observe_next_full_coverage_day"
    elif producer_pending_flush:
        state = "v2_shadow_pending_flush"
        recommended = "observe_pending_next_flush"
    elif not parity_ok:
        state = "v2_shadow_parity_fail"
        recommended = "block_suppress_and_fix_shadow"
    elif suppress_candidate:
        state = "suppress_candidate"
        recommended = "open_suppress_guard_order"
    else:
        state = "v2_shadow_parity_pass"
        recommended = "observe"

    report = {
        "schema_version": 1,
        "report_type": "pipeline_event_verbosity",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "state": state,
        "recommended_workorder_state": recommended,
        "policy": {
            "runtime_effect": False,
            "decision_authority": "diagnostic_aggregation",
            "raw_suppression_enabled": False,
            "forbidden_uses": [
                "runtime_threshold_or_order_guard_mutation",
                "real_execution_quality_inference",
                "primary_ev_decision",
            ],
        },
        "raw_stream": {
            "path": str(raw_path),
            **raw_stats,
        },
        "raw_derived_summary": {
            "path": raw_summary_meta.get("summary_path"),
            "manifest": raw_summary_meta.get("manifest_path"),
            "status": raw_summary_meta.get("status"),
            "row_count": raw_summary_meta.get("summary_row_count"),
            "event_count": raw_total,
            "stage_counts": dict(sorted(raw_stage.items())),
            "blocker_top": dict(raw_blocker.most_common(10)),
        },
        "producer_summary": {
            "path": str(producer_actual_path),
            "manifest_path": str(producer_manifest_path),
            "exists": producer_exists,
            "manifest_exists": manifest_exists,
            "manifest_mode": producer_manifest.get("mode"),
            "row_count": len(producer_rows),
            "event_count": producer_total,
            "stage_counts": dict(sorted(producer_stage.items())),
            "blocker_top": dict(producer_blocker.most_common(10)),
            "manifest_payload": producer_manifest,
        },
        "parity": {
            "ok": parity_ok,
            "stage_diff": stage_diff,
            "blocker_diff": blocker_diff,
            "raw_derived_event_count": raw_total,
            "producer_event_count": producer_total,
            "previous_parity_pass_count": previous_pass_count,
            "suppress_eligibility": suppress_candidate,
            "producer_pending_flush": producer_pending_flush,
            "producer_start_complete": producer_start_complete,
            "raw_coverage_start": raw_coverage_start or None,
            "raw_coverage_end": raw_coverage_end or None,
            "producer_coverage_start": producer_coverage_start or None,
            "producer_coverage_end": producer_coverage_end or None,
            "no_eligible_events": no_eligible_events,
            "producer_updated_at": producer_updated_at or None,
            "latest_pipeline_event_at": raw_stats.get("latest_pipeline_event_at"),
            "comparison_scope": "completed_common_minute",
            "comparison_watermark": comparison_watermark or None,
            "common_watermark_ok": common_watermark_ok,
            "comparison_stage_diff": comparison_stage_diff,
            "comparison_blocker_diff": comparison_blocker_diff,
            "comparison_raw_derived_event_count": comparison_raw_total,
            "comparison_producer_event_count": comparison_producer_total,
            "raw_tail_excluded_event_count": raw_total - comparison_raw_total,
            "producer_tail_excluded_event_count": (
                producer_total - comparison_producer_total
            ),
        },
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    raw = report.get("raw_stream") if isinstance(report.get("raw_stream"), dict) else {}
    parity = report.get("parity") if isinstance(report.get("parity"), dict) else {}
    producer = (
        report.get("producer_summary")
        if isinstance(report.get("producer_summary"), dict)
        else {}
    )
    return "\n".join(
        [
            f"# Pipeline Event Verbosity {report.get('target_date')}",
            "",
            "## 판정",
            "",
            f"- state: `{report.get('state')}`",
            f"- recommended_workorder_state: `{report.get('recommended_workorder_state')}`",
            f"- runtime_effect: `{report.get('policy', {}).get('runtime_effect')}`",
            f"- raw_suppression_enabled: `{report.get('policy', {}).get('raw_suppression_enabled')}`",
            "",
            "## 근거",
            "",
            f"- raw_size_bytes: `{raw.get('raw_size_bytes')}`",
            f"- raw_storage_size_bytes: `{raw.get('raw_storage_size_bytes')}`",
            f"- raw_line_count: `{raw.get('raw_line_count')}`",
            f"- high_volume_line_count: `{raw.get('high_volume_line_count')}`",
            f"- high_volume_byte_share_pct: `{raw.get('high_volume_byte_share_pct')}`",
            f"- producer_summary_exists: `{producer.get('exists')}`",
            f"- producer_manifest_mode: `{producer.get('manifest_mode') or '-'}`",
            f"- parity_ok: `{parity.get('ok')}`",
            f"- raw_derived_event_count: `{parity.get('raw_derived_event_count')}`",
            f"- producer_event_count: `{parity.get('producer_event_count')}`",
            f"- producer_start_complete: `{parity.get('producer_start_complete')}`",
            f"- producer_pending_flush: `{parity.get('producer_pending_flush')}`",
            f"- common_watermark_ok: `{parity.get('common_watermark_ok')}`",
            f"- comparison_watermark: `{parity.get('comparison_watermark')}`",
            f"- raw_tail_excluded_event_count: `{parity.get('raw_tail_excluded_event_count')}`",
            f"- coverage raw/producer: `{parity.get('raw_coverage_start')}` / `{parity.get('producer_coverage_start')}`",
            f"- previous_parity_pass_count: `{parity.get('previous_parity_pass_count')}`",
            "",
            "## 금지선",
            "",
            "- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.",
            "- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.",
            "",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build pipeline event verbosity/compaction report."
    )
    parser.add_argument(
        "--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d")
    )
    parser.add_argument("--print-json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = build_pipeline_event_verbosity_report(args.target_date)
    result = {
        "status": "success",
        "target_date": args.target_date,
        "state": report.get("state"),
        "artifacts": {
            "json": str(report_paths(args.target_date)[0]),
            "markdown": str(report_paths(args.target_date)[1]),
        },
    }
    print(
        json.dumps(
            result if args.print_json else result,
            ensure_ascii=False,
            indent=2 if args.print_json else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
