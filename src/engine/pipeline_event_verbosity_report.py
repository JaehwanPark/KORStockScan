from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.threshold_cycle_registry import threshold_family_for_stage
from src.engine.pipeline_event_summary import (
    IDENTITY_CONTRACT,
    IDENTITY_MODULUS,
    PRODUCER_SUMMARY_STAGES,
    PRODUCER_MAX_FLUSH_SEC,
    PRODUCER_TIMING_CONTRACT,
    producer_health_path,
    producer_manifest_fingerprint,
    payload_has_lossless_authority,
    default_reason_label,
    load_summary_rows,
    producer_summary_paths,
    update_and_load_pipeline_event_summaries,
)

REPORT_DIRNAME = "pipeline_event_verbosity"
KST = ZoneInfo("Asia/Seoul")
FLUSH_GRACE_SEC = 120


def _producer_timing(manifest: dict[str, Any], target_date: str) -> dict[str, Any]:
    """Operational measurements, never an inferred baseline delta or EV."""
    missing = {"status": "missing_or_unbound", "runtime_latency_improvement": None}
    pid = manifest.get("last_writer_pid")
    if (
        type(pid) is not int
        or pid <= 0
        or manifest.get("timing_contract") != PRODUCER_TIMING_CONTRACT
    ):
        return missing
    path = producer_health_path(_summary_dir(), target_date, pid)
    receipt = _read_json(path)
    if not (
        receipt.get("timing_contract") == PRODUCER_TIMING_CONTRACT
        and receipt.get("target_date") == target_date
        and receipt.get("writer_pid") == pid
        and receipt.get("manifest_sha256") == producer_manifest_fingerprint(manifest)
        and receipt.get("runtime_effect") is False
        and receipt.get("allowed_runtime_apply") is False
    ):
        return missing
    count = receipt.get("submit_sample_count")
    total = receipt.get("submit_count")
    if (
        type(count) is not int
        or not 0 <= count <= 2048
        or type(total) is not int
        or total < count
        or receipt.get("schema_version") != 1
        or receipt.get("duration_scope")
        != "summary_and_canonical_manifest_publish_excludes_health_receipt"
        or receipt.get("submit_sample_window") != "last_2048_process_calls"
        or receipt.get("submit_duration_scope")
        != "summary_submit_only_excludes_raw_writer_and_orders"
    ):
        return {**missing, "status": "invalid_measurement"}
    for key in (
        "last_flush_duration_ms",
        "submit_p95_ms",
        "submit_p99_ms",
        "submit_max_ms",
    ):
        value = receipt.get(key)
        if key != "last_flush_duration_ms" and count == 0 and value is None:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            return {**missing, "status": "invalid_measurement"}
    if (
        count
        and not receipt["submit_p95_ms"]
        <= receipt["submit_p99_ms"]
        <= receipt["submit_max_ms"]
    ):
        return {**missing, "status": "invalid_measurement"}
    return {
        **receipt,
        "status": (
            "observed_no_comparable_baseline"
            if count
            else "observed_publish_no_submit_sample"
        ),
        "path": str(path),
        "runtime_latency_improvement": None,
    }


def _as_kst(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
        return (
            parsed.replace(tzinfo=KST)
            if parsed.tzinfo is None
            else parsed.astimezone(KST)
        )
    except (ValueError, TypeError):
        return None


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


def report_is_reusable(target_date: str) -> bool:
    report = _read_json(report_paths(target_date)[0])
    policy = report.get("policy") or {}
    return bool(
        report.get("schema_version") == 2
        and report.get("report_type") == "pipeline_event_verbosity"
        and report.get("target_date") == target_date
        and report.get("state")
        in {
            "blocked",
            "source_quality_blocked",
            "v2_shadow_no_eligible_events",
            "v2_shadow_missing",
            "producer_manifest_invalid",
            "producer_summary_invalid",
            "v2_shadow_partial_coverage",
            "v2_shadow_parity_fail",
            "v2_shadow_flush_timeout",
            "legacy_identity_evidence_missing",
            "no_suppressible_events",
            "v2_shadow_parity_pass",
        }
        and isinstance(policy, dict)
        and policy.get("runtime_effect") is False
        and policy.get("allowed_runtime_apply") is False
        and policy.get("raw_suppression_enabled") is False
    )


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _line_count_and_stage_bytes(
    raw_path: Path, target_date: str | None = None
) -> dict[str, Any]:
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
    suppressible_count = 0
    suppressible_bytes = 0
    invalid_count = 0
    incomplete_tail = False
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
            if not raw_line.endswith("\n"):
                incomplete_tail = True
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                invalid_count += 1
                continue
            if not isinstance(payload, dict):
                invalid_count += 1
                continue
            if payload.get("event_type") != "pipeline_event":
                continue
            emitted_at = _safe_str(payload.get("emitted_at"))
            emitted_dt = _as_kst(emitted_at)
            if emitted_dt is None:
                invalid_count += 1
                continue
            latest_emitted_at = max(latest_emitted_at, emitted_at)
            stage = _safe_str(payload.get("stage"))
            if stage not in PRODUCER_SUMMARY_STAGES:
                continue
            if target_date and emitted_dt.date().isoformat() != target_date:
                invalid_count += 1
                continue
            if emitted_at:
                earliest_eligible_event_at = (
                    min(earliest_eligible_event_at, emitted_at)
                    if earliest_eligible_event_at
                    else emitted_at
                )
                latest_eligible_event_at = max(latest_eligible_event_at, emitted_at)
            line_bytes = len(raw_line.encode("utf-8"))
            high_volume_line_count += 1
            high_volume_bytes += line_bytes
            stage_counts[stage] += 1
            stage_bytes[stage] += line_bytes
            if not payload_has_lossless_authority(
                payload, threshold_family_for_stage(stage, payload.get("fields"))
            ):
                suppressible_count += 1
                suppressible_bytes += line_bytes
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
        "potential_suppressible_event_count": suppressible_count,
        "potential_suppressible_bytes": suppressible_bytes,
        "lossless_preserved_event_count": high_volume_line_count - suppressible_count,
        "invalid_source_line_count": invalid_count,
        "incomplete_tail": incomplete_tail,
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


def _identity_counts(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, tuple[int, int]], int]:
    """Partition/order-independent multiset evidence; counts alone are not parity."""
    values: dict[str, tuple[int, int]] = {}
    invalid = 0
    for row in rows:
        try:
            count = row["event_count"]
            digest = row["evidence_hash_sum"]
            if (
                type(count) is not int
                or count <= 0
                or row.get("identity_contract") != IDENTITY_CONTRACT
                or not isinstance(digest, str)
                or len(digest) != 64
            ):
                raise ValueError("invalid identity contract")
            hashed = int(digest, 16)
            if not 0 <= hashed < IDENTITY_MODULUS:
                raise ValueError("invalid digest")
            key = json.dumps(
                [
                    row.get(name)
                    for name in (
                        "target_date",
                        "bucket_start",
                        "bucket_end",
                        "pipeline",
                        "stage",
                        "stock_code",
                        "stock_name",
                        "strategy",
                        "market",
                        "reason_label",
                        "actual_order_submitted",
                    )
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            old_count, old_hash = values.get(key, (0, 0))
            values[key] = (old_count + count, (old_hash + hashed) % IDENTITY_MODULUS)
        except (KeyError, TypeError, ValueError):
            invalid += 1
    return values, invalid


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
        timestamp = _as_kst(value)
        if timestamp is None:
            return ""
        parsed.append(timestamp)
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
        if (end := _as_kst(row.get("bucket_end"))) is not None
        and end <= _as_kst(watermark)
    ]


def build_pipeline_event_verbosity_report(
    target_date: str, *, as_of: datetime | None = None
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    datetime.strptime(target_date, "%Y-%m-%d")
    now = _as_kst((as_of or datetime.now(KST)).isoformat())
    raw_path = existing_or_gzip_path(_pipeline_events_path(target_date))
    raw_stamp_before = (
        (raw_path.stat().st_size, raw_path.stat().st_mtime_ns)
        if raw_path.exists()
        else None
    )
    raw_stats = _line_count_and_stage_bytes(raw_path, target_date)
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
    producer_stamp_before = (
        (producer_actual_path.stat().st_size, producer_actual_path.stat().st_mtime_ns)
        if producer_actual_path.exists()
        else None
    )
    producer_manifest = _read_json(producer_manifest_path)
    producer_decode_error = None
    try:
        producer_rows = load_summary_rows(
            producer_path, include_samples=False, strict=True
        )
    except ValueError as exc:
        producer_rows = []
        producer_decode_error = str(exc)
    raw_identity, raw_identity_invalid = _identity_counts(raw_summary_rows)
    producer_identity, producer_identity_invalid = _identity_counts(producer_rows)
    legacy_identity_rows = sum(
        1
        for row in producer_rows
        if row.get("schema_version") == 1
        and row.get("identity_contract") != IDENTITY_CONTRACT
    )
    identity_ok = (
        not (raw_identity_invalid or producer_identity_invalid)
        and raw_identity == producer_identity
    )
    raw_stage, raw_blocker, raw_total = _summary_counts(raw_summary_rows)
    producer_stage, producer_blocker, producer_total = _summary_counts(producer_rows)
    producer_stamp_after = (
        (producer_actual_path.stat().st_size, producer_actual_path.stat().st_mtime_ns)
        if producer_actual_path.exists()
        else None
    )
    manifest_valid = (
        bool(producer_manifest)
        and type(producer_manifest.get("summary_event_count")) is int
        and producer_manifest["summary_event_count"] == producer_total
    )
    interval = producer_manifest.get("flush_interval_sec", 60)
    interval_valid = type(interval) is int and 0 <= interval <= PRODUCER_MAX_FLUSH_SEC
    manifest_valid = manifest_valid and interval_valid
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
    common_raw_identity, common_raw_invalid = _identity_counts(comparison_raw_rows)
    common_producer_identity, common_producer_invalid = _identity_counts(
        comparison_producer_rows
    )
    common_identity_ok = (
        not (common_raw_invalid or common_producer_invalid)
        and common_raw_identity == common_producer_identity
    )
    completed_mismatch = bool(
        comparison_stage_diff
        or comparison_blocker_diff
        or (
            not (common_raw_invalid or common_producer_invalid)
            and not common_identity_ok
        )
    )
    raw_stamp_after = (
        (raw_path.stat().st_size, raw_path.stat().st_mtime_ns)
        if raw_path.exists()
        else None
    )
    source_changing = (
        raw_stamp_before != raw_stamp_after
        or producer_stamp_before != producer_stamp_after
    )
    latest_dt = _as_kst(raw_coverage_end)
    # Legacy evidence uses the reviewed default, not an infinite grace period.
    # Longer supported intervals get one full interval plus scheduler margin.
    flush_allowance_sec = (
        max(FLUSH_GRACE_SEC, interval + 60) if interval_valid else None
    )
    flush_deadline = (
        latest_dt + timedelta(seconds=flush_allowance_sec)
        if latest_dt and flush_allowance_sec is not None
        else None
    )
    flush_expired = bool(flush_deadline and now > flush_deadline)
    common_watermark_ok = bool(
        producer_exists
        and producer_start_complete
        and comparison_raw_total > 0
        and not comparison_stage_diff
        and not comparison_blocker_diff
        and comparison_raw_total == comparison_producer_total
        and common_identity_ok
    )
    no_eligible_events = (
        raw_total == 0
        and producer_total == 0
        and not raw_stats.get("high_volume_line_count")
    )
    parity_ok = bool(
        (no_eligible_events and raw_stats.get("exists"))
        or (
            producer_exists
            and producer_start_complete
            and not producer_pending_flush
            and not stage_diff
            and not blocker_diff
            and raw_total == producer_total
            and identity_ok
            and manifest_valid
        )
    ) and not (
        source_changing
        or producer_decode_error
        or raw_stats.get("invalid_source_line_count")
        or raw_stats.get("incomplete_tail")
    )
    # Raw suppression has no reviewed consumer contract and is not a runtime
    # promotion queue. A diagnostic repair needs neither EV nor trading floors.
    previous_pass_count = 0
    suppress_candidate = False
    if not raw_path.exists():
        state = "blocked"
        recommended = "raw_missing"
    elif source_changing:
        state, recommended = "source_snapshot_changed", "retry_stable_source_snapshot"
    elif raw_stats.get("invalid_source_line_count"):
        state, recommended = "source_quality_blocked", "repair_source_contract"
    elif raw_stats.get("incomplete_tail"):
        state, recommended = "source_quality_blocked", "repair_source_contract"
    elif producer_decode_error:
        state, recommended = "producer_summary_invalid", "repair_source_contract"
    elif no_eligible_events:
        state = "v2_shadow_no_eligible_events"
        recommended = "observe_no_eligible_events"
    elif not producer_exists or not manifest_exists:
        state = "v2_shadow_missing"
        recommended = "open_shadow_order"
    elif not manifest_valid:
        state, recommended = "producer_manifest_invalid", "repair_source_contract"
    elif not producer_start_complete:
        state = "v2_shadow_partial_coverage"
        recommended = "repair_source_contract"
    elif completed_mismatch:
        state, recommended = "v2_shadow_parity_fail", "block_suppress_and_fix_shadow"
    elif producer_pending_flush and flush_expired:
        state, recommended = "v2_shadow_flush_timeout", "repair_source_contract"
    elif producer_pending_flush:
        state = "v2_shadow_pending_flush"
        recommended = "observe_pending_next_flush"
    elif raw_identity_invalid or producer_identity_invalid > legacy_identity_rows:
        state, recommended = "producer_summary_invalid", "repair_source_contract"
    elif producer_identity_invalid:
        state, recommended = (
            "legacy_identity_evidence_missing",
            "collect_after_contract_upgrade",
        )
    elif not parity_ok:
        state = "v2_shadow_parity_fail"
        recommended = "block_suppress_and_fix_shadow"
    elif raw_stats.get("potential_suppressible_event_count", 0) == 0:
        state, recommended = "no_suppressible_events", "keep_lightweight_summary"
    else:
        state = "v2_shadow_parity_pass"
        recommended = "observe"

    report = {
        "schema_version": 2,
        "report_type": "pipeline_event_verbosity",
        "target_date": target_date,
        "generated_at": now.isoformat(timespec="seconds"),
        "state": state,
        "recommended_workorder_state": recommended,
        "policy": {
            "runtime_effect": False,
            "decision_authority": "diagnostic_aggregation",
            "raw_suppression_enabled": False,
            "allowed_runtime_apply": False,
            "suppression_status": "disabled_no_consumer_preserving_contract",
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
            "manifest_valid": manifest_valid,
            "decode_error": producer_decode_error,
            "manifest_mode": producer_manifest.get("mode"),
            "row_count": len(producer_rows),
            "event_count": producer_total,
            "stage_counts": dict(sorted(producer_stage.items())),
            "blocker_top": dict(producer_blocker.most_common(10)),
            "manifest_payload": producer_manifest,
        },
        "parity": {
            "ok": parity_ok,
            "identity_contract": IDENTITY_CONTRACT,
            "identity_ok": identity_ok,
            "identity_invalid_rows": raw_identity_invalid + producer_identity_invalid,
            "common_identity_ok": common_identity_ok,
            "completed_window_mismatch": completed_mismatch,
            "flush_deadline": flush_deadline.isoformat() if flush_deadline else None,
            "flush_interval_sec": interval,
            "flush_allowance_sec": flush_allowance_sec,
            "flush_interval_valid": interval_valid,
            "flush_expired": flush_expired,
            "source_snapshot_changed": source_changing,
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
        "optimization": {
            "metric_role": "ops_volume_diagnostic",
            "decision_authority": "diagnostic_aggregation",
            "window_policy": "exact_date_stable_source",
            "sample_floor": "no_trade_or_ev_floor; valid source and consumer conservation",
            "primary_decision_metric": "potential_suppressible_bytes",
            "source_quality_gate": "raw_valid_and_identity_parity",
            "forbidden_uses": [
                "runtime_apply",
                "profitability_inference",
                "safety_relaxation",
            ],
            "state": (
                "no_suppressible_events"
                if raw_stats.get("exists")
                and not raw_stats.get("invalid_source_line_count")
                and not raw_stats.get("incomplete_tail")
                and not source_changing
                and raw_stats.get("potential_suppressible_event_count", 0) == 0
                else "needs_source_or_consumer_review"
            ),
            "raw_reduction_bytes": 0,
            "runtime_latency_improvement": None,
            "runtime_observation": _producer_timing(producer_manifest, target_date),
            "economic_effect": "not_measured",
            "producer_storage_bytes": (
                producer_actual_path.stat().st_size
                if producer_actual_path.exists()
                else 0
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
            f"- potential_suppressible_event_count: `{raw.get('potential_suppressible_event_count')}`",
            f"- potential_suppressible_bytes (not realized savings): `{raw.get('potential_suppressible_bytes')}`",
            f"- identity_ok: `{parity.get('identity_ok')}`",
            f"- flush_deadline / expired: `{parity.get('flush_deadline')}` / `{parity.get('flush_expired')}`",
            f"- optimization: `{report.get('optimization', {}).get('state')}`; raw reduction 0; runtime/economic benefit unmeasured",
            f"- producer timing (measured, not improvement): `{json.dumps(report.get('optimization', {}).get('runtime_observation', {}), ensure_ascii=False)}`",
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
            "- 원본 생략 경로는 소비자 보존 계약 미구현으로 비활성이다. 양수 EV/실체결/2일 대기를 진단 수리 조건으로 붙이지 않는다.",
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
    parser.add_argument(
        "--check-reusable",
        action="store_true",
        help="Read-only schema/date/terminal cache check; never regenerate.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.check_reusable:
        return 0 if report_is_reusable(args.target_date) else 1
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
