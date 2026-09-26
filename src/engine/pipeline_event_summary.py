from __future__ import annotations

import hashlib
import inspect
import fcntl
import gzip
import json
import logging
import math
import os
import time
import threading
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from functools import wraps
from itertools import chain
from typing import Any, Callable

from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

ReasonLabeler = Callable[[str, dict[str, str]], str]
IgnorePredicate = Callable[[dict[str, Any]], bool]

SUMMARY_SCHEMA_VERSION = 2
PRODUCER_SUMMARY_SCHEMA_VERSION = 2
PRODUCER_PARITY_DETAIL_LEVEL = "counts_identity_v2"
IDENTITY_CONTRACT = "canonical_payload_sha256_sum_v1"
IDENTITY_MODULUS = 1 << 256
PRODUCER_MAX_GROUPS = 4096
PRODUCER_MAX_FLUSH_SEC = 3600
PRODUCER_TIMING_CONTRACT = "producer_publish_and_submit_v1"
DEFAULT_SUMMARY_DETAIL_LEVEL = "diagnostic_full_v1"
HIGH_VOLUME_OBSERVATION_STAGES = frozenset(
    {
        "rising_missed_nxt_post_block_price_sample",
        "rising_missed_tp1_candidate_blocked",
        "rising_missed_tp1_candidate_deferred",
        "rising_missed_tp1_counterfactual_submit_safety",
        "rising_missed_watch_not_rising_skipped",
        "scalping_scanner_fast_precheck",
        "scalping_scanner_heavy_eval_completion",
        "scalping_scanner_heavy_eval_lag",
        "scalping_scanner_promotion_latency_trace",
        "scalping_scanner_runtime_queue_lag",
        "scalping_scanner_runtime_target_attach",
        "scalping_scanner_watching_runtime_skip",
        "scalp_trailing_mechanical_input",
    }
)
HIGH_VOLUME_SUMMARY_FIELD_PRIORITY = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "source_quality_route",
    "runtime_effect",
    "allowed_runtime_apply",
    "actual_order_submitted",
    "broker_order_forbidden",
    "reason",
    "block_reason",
    "decision",
    "action",
    "strategy",
    "market",
    "market_type",
    "effective_venue",
    "venue_resolution",
    "source_signature",
    "runtime_record_id",
    "heavy_queue_wait_sec",
    "heavy_handler_duration_sec",
    "heavy_end_to_end_sec",
    "heavy_eval_outcome",
    "scanner_promotion_id",
    "scanner_promotion_reason",
    "scanner_promotion_emitted_epoch",
    "fast_precheck_result",
    "fast_precheck_reason",
    "fast_precheck_lag_sec",
    "skip_reason",
    "trace_phase",
    "queue_rank",
    "scanner_queue_rank",
    "queue_lag_sec",
    "heavy_queue_wait_sec",
    "promotion_to_trace_sec",
    "promotion_to_last_0b_sec",
    "last_0b_to_trace_sec",
    "rising_missed_tp1_evaluation_id",
    "rising_missed_nxt_post_block_price_observation_state",
    "rising_missed_nxt_post_block_price_source",
    "rising_missed_nxt_post_block_price_source_reason",
    "rising_missed_nxt_post_block_fresh_sample",
    "rising_missed_nxt_post_block_elapsed_sec",
    "rising_missed_nxt_post_block_sample_attempt_count",
    "current_price",
    "ws_curr",
)
SUMMARY_STAGES = frozenset(
    {
        "strength_momentum_observed",
        "blocked_strength_momentum",
        "blocked_swing_score_vpw",
        "blocked_overbought",
        "blocked_swing_gap",
    }
)
EXECUTION_SUMMARY_STAGES = frozenset({
    "pre_submit_delay_committed", "pre_submit_delay_quote_observed",
    "pre_submit_delay_intent_terminal",
    "entry_execution_sizing_plan", "entry_execution_sizing_plan_block",
    "entry_ai_economic_plan_observed", "entry_ai_economic_source_gap",
    "entry_ai_economic_decision_available", "entry_machine_watch_terminal",
    "entry_quantity_leg_four_arm_evaluation", "order_leg_sent", "order_leg_fail",
    "order_leg_no_response", "order_bundle_submitted", "order_bundle_failed",
})
CANCEL_WAIT_SUMMARY_STAGES = frozenset({
    "entry_cancel_wait_submission", "entry_order_cancel_requested",
    "entry_order_cancel_confirmed", "entry_order_cancel_failed",
})
LOSSLESS_ORDER_STAGES = EXECUTION_SUMMARY_STAGES | CANCEL_WAIT_SUMMARY_STAGES
PRODUCER_SUMMARY_STAGES = SUMMARY_STAGES | HIGH_VOLUME_OBSERVATION_STAGES | LOSSLESS_ORDER_STAGES

NUMERIC_FIELD_LIMIT = 64
SAMPLE_HASH_LIMIT = 2
SAMPLE_FIRST_LIMIT = 2
SAMPLE_LAST_LIMIT = 2
SAMPLE_FIELD_LIMIT = 24
SAMPLE_FIELD_VALUE_MAX_CHARS = 160
SAMPLE_FIELD_PRIORITY = (
    "reason",
    "block_reason",
    "blocked_reason",
    "decision",
    "action",
    "strategy",
    "selected_strategy",
    "entry_strategy",
    "origin_strategy",
    "trade_type",
    "market",
    "market_type",
    "actual_order_submitted",
    "broker_order_forbidden",
    "broker_order_submitted",
    "score",
    "ai_score",
    "current_ai_score",
    "buy_ratio",
    "exec_buy_ratio",
    "window_buy_value",
    "latest_strength",
    "strength",
    "gap_pct",
    "distance_pct",
)
NUMERIC_FIELD_EXCLUDED_NAMES = {
    "id",
    "record_id",
    "stock_code",
    "code",
    "종목코드",
}
KEY_FIELD_CANDIDATES = {
    "strategy": (
        "strategy",
        "selected_strategy",
        "entry_strategy",
        "origin_strategy",
        "trade_type",
    ),
    "market": ("market", "market_type", "market_name", "universe", "market_code"),
}
ACTUAL_ORDER_FIELD_CANDIDATES = (
    "actual_order_submitted",
    "broker_order_submitted",
    "order_submitted",
)


@dataclass(frozen=True)
class SummaryEvent:
    emitted_at: datetime
    pipeline: str
    stage: str
    stock_name: str
    stock_code: str
    record_id: str
    fields: dict[str, str]
    reason_label: str
    strategy: str
    market: str
    actual_order_submitted: str
    raw_offset_start: int
    raw_offset_end: int
    evidence_hash: int = 0
    execution_projection_hash: int = 0


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def checkpoint_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        {k: v for k, v in payload.items() if k != "checkpoint_digest"},
        sort_keys=True, ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}.{threading.get_ident()}")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)


ROLLUP_KEY_FIELDS = (
    "target_date", "bucket_start", "bucket_end", "pipeline", "stage", "stock_code",
    "stock_name", "strategy", "market", "reason_label", "actual_order_submitted",
)


ROLLUP_BUCKET_FIELDS = (
    "target_date", "bucket_start", "bucket_end", "pipeline", "stage", "reason_label", "actual_order_submitted",
)
ROLLUP_CONTRACT = "bucket_stage_full_payload_and_partition_multiset_v1"


def partition_hash_sum(row):
    if row.get("rollup_contract") == ROLLUP_CONTRACT:
        return int(row["partition_hash_sum"], 16)
    key = json.dumps([row.get(name) for name in ROLLUP_KEY_FIELDS], ensure_ascii=False, separators=(",", ":"))
    return (int(hashlib.sha256(key.encode()).hexdigest(), 16) * row["event_count"]) % IDENTITY_MODULUS


def merge_identity_rows(previous, appended):
    """Compact full hash multisets, preserving original partition dimensions.

    This is a report checkpoint only. It never replaces diagnostic samples,
    execution projections or raw custody. Payload and partition hashes are
    independently reconciled; coalescing is not sampling.
    """
    groups = {}
    for row in chain(previous, appended):
        key = tuple(row.get(name) for name in ROLLUP_BUCKET_FIELDS)
        partition = partition_hash_sum(row)
        if key not in groups:
            groups[key] = {name: row.get(name) for name in ROLLUP_BUCKET_FIELDS}
            groups[key].update(event_count=0, evidence_hash_sum="0" * 64,
                               partition_hash_sum="0" * 64, rollup_contract=ROLLUP_CONTRACT,
                               identity_contract=IDENTITY_CONTRACT, first_seen=row.get("first_seen"), last_seen=row.get("last_seen"))
        old = groups[key]
        old["event_count"] += row["event_count"]
        old["evidence_hash_sum"] = f"{(int(old['evidence_hash_sum'], 16) + int(row['evidence_hash_sum'], 16)) % IDENTITY_MODULUS:064x}"
        old["partition_hash_sum"] = f"{(int(old['partition_hash_sum'], 16) + partition) % IDENTITY_MODULUS:064x}"
        old["first_seen"] = min(old.get("first_seen") or "", row.get("first_seen") or "")
        old["last_seen"] = max(old.get("last_seen") or "", row.get("last_seen") or "")
    return list(groups.values())


def _with_summary_generation_lock(method):
    @wraps(method)
    def locked(*args, **kwargs):
        summary_dir = kwargs["summary_dir"]
        summary_dir.mkdir(parents=True, exist_ok=True)
        _, manifest = _summary_paths(summary_dir, kwargs["target_date"], profile=kwargs.get("summary_profile", "default"))
        with manifest.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return method(*args, **kwargs)
    return locked


def _summary_paths(
    summary_dir: Path, target_date: str, *, profile: str = "default"
) -> tuple[Path, Path]:
    safe_profile = _safe_str(profile) or "default"
    if safe_profile not in {"default", "producer_parity"}:
        raise ValueError(f"unsupported pipeline event summary profile: {safe_profile}")
    suffix = "" if safe_profile == "default" else f"_{safe_profile}"
    return (
        summary_dir / f"pipeline_event_summary{suffix}_{target_date}.jsonl",
        summary_dir / f"pipeline_event_summary{suffix}_manifest_{target_date}.json",
    )


def producer_summary_paths(summary_dir: Path, target_date: str) -> tuple[Path, Path]:
    return (
        summary_dir / f"pipeline_event_producer_summary_{target_date}.jsonl",
        summary_dir / f"pipeline_event_producer_summary_manifest_{target_date}.json",
    )


def producer_health_path(summary_dir: Path, target_date: str, pid: int) -> Path:
    return summary_dir / f"pipeline_event_producer_health_{target_date}_{pid}.json"


def producer_manifest_fingerprint(manifest: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _parse_iso_datetime(value: str) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _first_field(fields: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = _safe_str(fields.get(name))
        if value:
            return value
    return ""


def field_first(fields: dict[str, str], names: tuple[str, ...]) -> str:
    return _first_field(fields, names)


def default_reason_label(stage: str, fields: dict[str, str]) -> str:
    if stage == "ai_confirmed_terminal_no_budget":
        terminal_reason = _first_field(
            fields,
            (
                "terminal_reason",
                "reason",
                "block_reason",
                "blocked_reason",
                "source_stage",
            ),
        )
        if terminal_reason:
            return f"ai_terminal:{terminal_reason}"
        action = _first_field(fields, ("ai_action", "action", "decision"))
        score = _first_field(fields, ("ai_score", "score", "current_ai_score"))
        if action or score:
            return f"ai_terminal:{action or 'unknown'}_score_{score or '-'}"
        return "ai_terminal:unknown_terminal_reason"
    if stage == "blocked_ai_score":
        score = _first_field(fields, ("score", "ai_score", "current_ai_score"))
        reason = _first_field(
            fields, ("reason", "block_reason", "blocked_reason", "decision")
        )
        if (
            "ai_score_50_buy_hold_override" in reason
            or fields.get("ai_score_50_buy_hold_override") == "True"
        ):
            return "blocked_ai_score:ai_score_50_buy_hold_override"
        if score:
            return f"blocked_ai_score:score_{score}"
    if stage == "latency_block":
        reason = _first_field(fields, ("reason", "latency_danger_reasons", "decision"))
        return f"latency_block:{reason or '-'}"
    if stage in {
        "pre_submit_price_guard_block",
        "entry_ai_price_canary_skip_order",
        "entry_ai_price_canary_fallback",
        "scale_in_price_guard_block",
    }:
        reason = _first_field(
            fields, ("reason", "block_reason", "resolution_reason", "action")
        )
        return f"{stage}:{reason or '-'}"
    if stage == "wait65_79_ev_candidate":
        score = _first_field(fields, ("ai_score", "score", "current_ai_score"))
        return f"wait65_79_ev_candidate:score_{score or '-'}"
    reason = _first_field(fields, ("reason", "block_reason", "decision", "action"))
    return f"{stage}:{reason or '-'}"


def _actual_order_text(payload: dict[str, Any], fields: dict[str, str]) -> str:
    for name in ACTUAL_ORDER_FIELD_CANDIDATES:
        if name in fields:
            return _boolish_text(fields.get(name))
        if name in payload:
            return _boolish_text(payload.get(name))
    return "unknown"


def _project_summary_fields(stage: str, fields: dict[str, str]) -> dict[str, str]:
    if stage not in HIGH_VOLUME_OBSERVATION_STAGES:
        return fields
    projected = {
        key: fields[key] for key in HIGH_VOLUME_SUMMARY_FIELD_PRIORITY if key in fields
    }
    omitted_field_count = max(0, len(fields) - len(projected))
    if omitted_field_count <= 0:
        return fields
    projected["summary_field_projection"] = "high_volume_diagnostic_v1"
    projected["full_field_count"] = str(len(fields))
    projected["omitted_field_count"] = str(omitted_field_count)
    return projected


def _boolish_text(value: Any) -> str:
    text = _safe_str(value)
    lowered = text.lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return "true"
    if lowered in {"0", "false", "f", "no", "n"}:
        return "false"
    return text or "unknown"


def truthy(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "t", "yes", "y", "on"}


def _try_float(value: str) -> float | None:
    text = _safe_str(value)
    if not text:
        return None
    lowered = text.lower()
    if lowered in {"true", "false", "none", "null", "nan", "inf", "-inf"}:
        return None
    cleaned = text.replace(",", "")
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _is_numeric_field_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in NUMERIC_FIELD_EXCLUDED_NAMES:
        return False
    if lowered.endswith("_id") or lowered.endswith("_code") or lowered.endswith("_at"):
        return False
    if "time" in lowered or "date" in lowered:
        return False
    return True


def _compact_sample(event: SummaryEvent) -> dict[str, Any]:
    return {
        "emitted_at": event.emitted_at.isoformat(timespec="seconds"),
        "pipeline": event.pipeline,
        "stage": event.stage,
        "stock_name": event.stock_name,
        "stock_code": event.stock_code,
        "record_id": event.record_id,
        "raw_offset": event.raw_offset_start,
        "fields": _compact_sample_fields(event.fields),
    }


def _compact_sample_fields(fields: dict[str, str]) -> dict[str, str]:
    compact: dict[str, str] = {}
    for key in SAMPLE_FIELD_PRIORITY:
        if key in fields:
            compact[key] = _truncate_field_value(fields[key])
        if len(compact) >= SAMPLE_FIELD_LIMIT:
            return compact
    for key in sorted(fields):
        if key in compact:
            continue
        compact[key] = _truncate_field_value(fields[key])
        if len(compact) >= SAMPLE_FIELD_LIMIT:
            break
    return compact


def _truncate_field_value(value: str) -> str:
    text = _safe_str(value)
    if len(text) <= SAMPLE_FIELD_VALUE_MAX_CHARS:
        return text
    return text[:SAMPLE_FIELD_VALUE_MAX_CHARS] + "...<truncated>"


class _SummaryAggregate:
    def __init__(
        self,
        *,
        bucket_start: datetime,
        bucket_end: datetime,
        pipeline: str,
        stage: str,
        stock_code: str,
        stock_name: str,
        strategy: str,
        market: str,
        reason_label: str,
        actual_order_submitted: str,
        sample_per_bucket: int = 6,
        include_diagnostics: bool = True,
    ) -> None:
        self.bucket_start = bucket_start
        self.bucket_end = bucket_end
        self.pipeline = pipeline
        self.stage = stage
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.strategy = strategy
        self.market = market
        self.reason_label = reason_label
        self.actual_order_submitted = actual_order_submitted
        self.sample_per_bucket = max(1, min(int(sample_per_bucket or 1), 6))
        self.include_diagnostics = bool(include_diagnostics)
        self.event_count = 0
        self.evidence_hash_sum = 0
        self.execution_projection_hash_sum = 0
        self.first_seen: datetime | None = None
        self.last_seen: datetime | None = None
        self.first_record_id = ""
        self.last_record_id = ""
        self.first_raw_offset: int | None = None
        self.last_raw_offset: int | None = None
        self.field_presence_counts: Counter[str] = Counter()
        self.numeric_stats: dict[str, dict[str, float | int]] = {}
        self.second_counts: Counter[str] = Counter()
        self.first_samples: list[dict[str, Any]] = []
        self.last_samples: deque[dict[str, Any]] = deque(maxlen=SAMPLE_LAST_LIMIT)
        self.hash_samples: list[tuple[int, dict[str, Any]]] = []

    def add(self, event: SummaryEvent) -> None:
        self.event_count += 1
        self.execution_projection_hash_sum = (self.execution_projection_hash_sum + event.execution_projection_hash) % IDENTITY_MODULUS
        self.evidence_hash_sum = (
            self.evidence_hash_sum + event.evidence_hash
        ) % IDENTITY_MODULUS
        if self.first_seen is None:
            self.first_seen = event.emitted_at
            self.first_record_id = event.record_id
            self.first_raw_offset = event.raw_offset_start
        self.first_seen = min(self.first_seen, event.emitted_at)
        self.last_seen = max(self.last_seen or event.emitted_at, event.emitted_at)
        self.last_record_id = event.record_id
        self.last_raw_offset = event.raw_offset_end
        if not self.include_diagnostics:
            return
        self.second_counts[
            event.emitted_at.replace(microsecond=0).isoformat(timespec="seconds")
        ] += 1
        sample = _compact_sample(event)
        if len(self.first_samples) < SAMPLE_FIRST_LIMIT:
            self.first_samples.append(sample)
        self.last_samples.append(sample)
        sample_hash = int(
            hashlib.sha256(
                f"{event.stage}|{event.record_id}|{event.raw_offset_start}|{event.emitted_at.isoformat()}".encode(
                    "utf-8"
                )
            ).hexdigest(),
            16,
        )
        self.hash_samples.append((sample_hash, sample))
        self.hash_samples.sort(key=lambda item: item[0])
        if len(self.hash_samples) > SAMPLE_HASH_LIMIT:
            self.hash_samples = self.hash_samples[:SAMPLE_HASH_LIMIT]

        for key, value in event.fields.items():
            self.field_presence_counts[key] += 1
            if not _is_numeric_field_name(key):
                continue
            numeric = _try_float(value)
            if numeric is None:
                continue
            if key not in self.numeric_stats:
                if len(self.numeric_stats) >= NUMERIC_FIELD_LIMIT:
                    continue
                self.numeric_stats[key] = {
                    "count": 0,
                    "min": numeric,
                    "max": numeric,
                    "sum": 0.0,
                }
            stats = self.numeric_stats[key]
            stats["count"] = int(stats["count"]) + 1
            stats["min"] = min(float(stats["min"]), numeric)
            stats["max"] = max(float(stats["max"]), numeric)
            stats["sum"] = float(stats["sum"]) + numeric

    def _sample_events(self) -> list[dict[str, Any]]:
        by_offset: dict[int, dict[str, Any]] = {}
        ordered_samples = (
            self.first_samples
            + [sample for _, sample in self.hash_samples]
            + list(self.last_samples)
        )
        for sample in ordered_samples:
            offset = int(sample.get("raw_offset") or 0)
            by_offset.setdefault(offset, sample)
        ordered = [by_offset[offset] for offset in sorted(by_offset)]
        if len(ordered) <= self.sample_per_bucket:
            return ordered
        if self.sample_per_bucket == 1:
            return ordered[:1]
        # Keep both temporal boundaries.  A plain prefix slice made small
        # sample limits lose the final state that explains how the bucket
        # closed.
        middle_limit = self.sample_per_bucket - 2
        return ordered[:1] + ordered[1:-1][:middle_limit] + ordered[-1:]

    def to_row(self, *, target_date: str, summary_detail_level: str) -> dict[str, Any]:
        row = {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "summary_detail_level": summary_detail_level,
            "target_date": target_date,
            "bucket_start": self.bucket_start.isoformat(timespec="seconds"),
            "bucket_end": self.bucket_end.isoformat(timespec="seconds"),
            "pipeline": self.pipeline,
            "stage": self.stage,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "strategy": self.strategy,
            "market": self.market,
            "reason_label": self.reason_label,
            "actual_order_submitted": self.actual_order_submitted,
            "event_count": self.event_count,
            "identity_contract": IDENTITY_CONTRACT,
            "evidence_hash_sum": f"{self.evidence_hash_sum:064x}",
            **({"execution_projection_identity_contract": "lossless_execution_projection_v1",
                "execution_projection_hash_sum": f"{self.execution_projection_hash_sum:064x}"}
               if self.stage in LOSSLESS_ORDER_STAGES else {}),
            "first_seen": (self.first_seen.isoformat() if self.first_seen else None),
            "last_seen": (self.last_seen.isoformat() if self.last_seen else None),
            "metric_role": "ops_volume_diagnostic",
            "decision_authority": "diagnostic_aggregation",
            "runtime_effect": False,
            "forbidden_uses": [
                "runtime_threshold_or_order_guard_mutation",
                "real_execution_quality_inference",
                "primary_ev_decision",
            ],
        }
        if not self.include_diagnostics:
            return row
        numeric_stats = {}
        for key, stats in sorted(self.numeric_stats.items()):
            count = int(stats["count"])
            numeric_stats[key] = {
                "count": count,
                "min": float(stats["min"]),
                "max": float(stats["max"]),
                "sum": float(stats["sum"]),
                "avg": float(stats["sum"]) / count if count else 0.0,
            }
        samples = self._sample_events()
        row.update(
            {
                "first_record_id": self.first_record_id,
                "last_record_id": self.last_record_id,
                "field_presence_counts": dict(
                    sorted(self.field_presence_counts.items())
                ),
                "numeric_stats": numeric_stats,
                "second_counts": dict(sorted(self.second_counts.items())),
                "first_raw_offset": self.first_raw_offset,
                "last_raw_offset": self.last_raw_offset,
                "sample_raw_offsets": [
                    int(sample.get("raw_offset") or 0) for sample in samples
                ],
                "sample_events": samples,
            }
        )
        return row


def is_summary_target_stage(stage: str) -> bool:
    return _safe_str(stage) in SUMMARY_STAGES


def payload_has_lossless_authority(
    payload: dict[str, Any], threshold_family: str | None = None
) -> bool:
    stage = _safe_str(payload.get("stage")).lower()
    from src.engine.automation.submit_drought_contract import UPSTREAM_TERMINAL_STAGES

    # Terminal BUY blockers are exact-attempt inputs, even without a threshold
    # family. Summary-only compaction would destroy their identity and ordering.
    if stage in UPSTREAM_TERMINAL_STAGES:
        return True
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
    if threshold_family:
        return True
    if any(
        token in stage
        for token in (
            "order_submitted",
            "order_bundle_submitted",
            "order_sent",
            "order_cancel",
            "order_failed",
            "order_rejected",
            "sell_order",
            "buy_order",
            "fill",
            "filled",
            "exit",
            "hard_stop",
            "protect",
            "emergency",
            "safety",
        )
    ):
        return True
    for key in ("actual_order_submitted", "broker_order_submitted", "order_submitted"):
        if truthy(payload.get(key)) or truthy(fields.get(key)):
            return True
    for key in fields:
        lowered = str(key).lower()
        if "source_quality" in lowered or "provenance" in lowered:
            return True
    return False


def _summary_event_from_payload(
    payload: dict[str, Any],
    *,
    reason_labeler: ReasonLabeler,
    ignore_payload: IgnorePredicate | None,
    line_start: int,
    line_end: int,
    summary_stages: frozenset[str] = SUMMARY_STAGES,
) -> SummaryEvent | None:
    if ignore_payload is not None and ignore_payload(payload):
        return None
    if _safe_str(payload.get("event_type")) != "pipeline_event":
        return None
    stage = _safe_str(payload.get("stage"))
    if stage not in summary_stages:
        return None
    emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
    if emitted_at is None:
        return None
    if emitted_at.tzinfo is not None:
        emitted_at = emitted_at.astimezone(ZoneInfo("Asia/Seoul"))
    raw_fields = payload.get("fields") or {}
    full_fields = (
        {str(k): _safe_str(v) for k, v in raw_fields.items()}
        if isinstance(raw_fields, dict)
        else {}
    )
    record_id = payload.get("record_id")
    if record_id in (None, "", 0):
        record_id = full_fields.get("id") or ""
    strategy = _first_field(full_fields, KEY_FIELD_CANDIDATES["strategy"])
    market = _first_field(full_fields, KEY_FIELD_CANDIDATES["market"])
    reason_label = reason_labeler(stage, full_fields)
    actual_order_submitted = _actual_order_text(payload, full_fields)
    fields = _project_summary_fields(stage, full_fields)
    return SummaryEvent(
        emitted_at=emitted_at,
        pipeline=_safe_str(payload.get("pipeline")),
        stage=stage,
        stock_name=_safe_str(payload.get("stock_name")),
        stock_code=_safe_str(payload.get("stock_code"))[:6],
        record_id=_safe_str(record_id),
        fields=fields,
        reason_label=reason_label,
        strategy=strategy,
        market=market,
        actual_order_submitted=actual_order_submitted,
        raw_offset_start=line_start,
        raw_offset_end=line_end,
        execution_projection_hash=(int(execution_projection_identity(payload), 16)
            if stage in LOSSLESS_ORDER_STAGES else 0),
        evidence_hash=int.from_bytes(
            hashlib.sha256(
                json.dumps(
                    payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).digest(),
            "big",
        ),
    )


def execution_projection_identity(payload):
    """Same lossless economic envelope on raw and compact sides."""
    keys = ("pipeline", "stage", "stock_name", "stock_code", "record_id", "fields", "emitted_at", "emitted_date")
    value = {key: payload.get(key) for key in keys}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def summary_event_from_payload(
    payload: dict[str, Any],
    *,
    reason_labeler: ReasonLabeler = default_reason_label,
    ignore_payload: IgnorePredicate | None = None,
    line_start: int = 0,
    line_end: int = 0,
    summary_stages: frozenset[str] = SUMMARY_STAGES,
) -> SummaryEvent | None:
    return _summary_event_from_payload(
        payload,
        reason_labeler=reason_labeler,
        ignore_payload=ignore_payload,
        line_start=line_start,
        line_end=line_end,
        summary_stages=summary_stages,
    )


def _aggregate_key(event: SummaryEvent) -> tuple[str, ...]:
    bucket_start = event.emitted_at.replace(second=0, microsecond=0)
    return (
        bucket_start.isoformat(timespec="seconds"),
        event.pipeline,
        event.stage,
        event.stock_code,
        event.stock_name,
        event.strategy,
        event.market,
        event.reason_label,
        event.actual_order_submitted,
    )


def _new_aggregate(
    event: SummaryEvent,
    *,
    sample_per_bucket: int = 6,
    include_diagnostics: bool = True,
) -> _SummaryAggregate:
    bucket_start = event.emitted_at.replace(second=0, microsecond=0)
    bucket_end = bucket_start + timedelta(minutes=1)
    return _SummaryAggregate(
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        pipeline=event.pipeline,
        stage=event.stage,
        stock_code=event.stock_code,
        stock_name=event.stock_name,
        strategy=event.strategy,
        market=event.market,
        reason_label=event.reason_label,
        actual_order_submitted=event.actual_order_submitted,
        sample_per_bucket=sample_per_bucket,
        include_diagnostics=include_diagnostics,
    )


def _load_summary_rows(
    summary_path: Path, *, include_samples: bool = True, strict: bool = False
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary_path = existing_or_gzip_path(summary_path)
    if not summary_path.exists():
        return rows
    with open_text_auto(summary_path, errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                if strict:
                    raise ValueError("invalid producer summary JSONL")
                continue
            if strict and (
                not raw_line.endswith("\n")
                or not isinstance(payload, dict)
                or type(payload.get("event_count")) is not int
                or payload["event_count"] <= 0
                or _parse_iso_datetime(payload.get("bucket_start")) is None
                or _parse_iso_datetime(payload.get("bucket_end")) is None
            ):
                raise ValueError("invalid producer summary row")
            if isinstance(payload, dict):
                if not include_samples:
                    rows.append(_slim_summary_row(payload))
                else:
                    rows.append(payload)
    return rows


def _rehydrate_summary_for_append(summary_path: Path) -> None:
    """Restore an archived summary before an explicit historical append/rebuild."""

    if summary_path.exists():
        return
    archived_path = Path(f"{summary_path}.gz")
    if not archived_path.exists():
        return
    tmp_path = summary_path.with_name(f"{summary_path.name}.tmp.{os.getpid()}")
    try:
        with gzip.open(archived_path, "rb") as source, tmp_path.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        os.replace(tmp_path, summary_path)
        archived_path.unlink()
    finally:
        tmp_path.unlink(missing_ok=True)


def load_summary_rows(
    path: Path, *, include_samples: bool = True, strict: bool = False
) -> list[dict[str, Any]]:
    return _load_summary_rows(path, include_samples=include_samples, strict=strict)


def _slim_summary_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "summary_detail_level": payload.get("summary_detail_level"),
        "target_date": payload.get("target_date"),
        "bucket_start": payload.get("bucket_start"),
        "bucket_end": payload.get("bucket_end"),
        "pipeline": payload.get("pipeline"),
        "stage": payload.get("stage"),
        "stock_code": payload.get("stock_code"),
        "stock_name": payload.get("stock_name"),
        "strategy": payload.get("strategy"),
        "market": payload.get("market"),
        "reason_label": payload.get("reason_label"),
        "actual_order_submitted": payload.get("actual_order_submitted"),
        "event_count": payload.get("event_count"),
        "identity_contract": payload.get("identity_contract"),
        "evidence_hash_sum": payload.get("evidence_hash_sum"),
        "first_seen": payload.get("first_seen"),
        "last_seen": payload.get("last_seen"),
        "second_counts": (
            payload.get("second_counts")
            if isinstance(payload.get("second_counts"), dict)
            else {}
        ),
        "decision_authority": payload.get("decision_authority"),
        "runtime_effect": payload.get("runtime_effect"),
    }


@_with_summary_generation_lock
def update_and_load_pipeline_event_summaries(
    *,
    raw_path: Path,
    summary_dir: Path,
    target_date: str,
    reason_labeler: ReasonLabeler,
    ignore_payload: IgnorePredicate | None = None,
    include_samples: bool = True,
    summary_stages: frozenset[str] = SUMMARY_STAGES,
    summary_profile: str = "default",
    raw_observer: Callable[[bytes, Any], None] | None = None,
    observer_state: dict[str, Any] | None = None,
    incremental_rollup: bool = False,
    allow_bootstrap: bool = False,
    observer_contract: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary_profile = _safe_str(summary_profile) or "default"
    raw_path = existing_or_gzip_path(raw_path).resolve()
    summary_dir = summary_dir.resolve()
    if not raw_path.exists():
        return [], {
            "enabled": True,
            "status": "raw_missing",
            "raw_path": str(raw_path),
            "summary_event_count": 0,
        }

    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path, manifest_path = _summary_paths(
        summary_dir, target_date, profile=summary_profile
    )
    stat = raw_path.stat()
    is_gzip_raw = raw_path.suffix == ".gz"
    raw_inode = getattr(stat, "st_ino", None)
    manifest = _read_json(manifest_path)
    summary_detail_level = (
        PRODUCER_PARITY_DETAIL_LEVEL
        if summary_profile == "producer_parity"
        else DEFAULT_SUMMARY_DETAIL_LEVEL
    )
    force_rebuild = False
    invalid_checkpoint = manifest_path.exists() and (not manifest or
        ("checkpoint_digest" in manifest and manifest["checkpoint_digest"] != checkpoint_digest(manifest)))
    if invalid_checkpoint:
        if not allow_bootstrap:
            raise ValueError("raw_summary_checkpoint_digest_invalid")
        force_rebuild = True
    actual_summary = existing_or_gzip_path(summary_path)
    summary_stamp = manifest.get("summary_stamp")
    if actual_summary.exists() and summary_stamp and summary_stamp != [
        actual_summary.stat().st_ino, actual_summary.stat().st_size,
        actual_summary.stat().st_mtime_ns, actual_summary.stat().st_ctime_ns,
    ]:
        if not allow_bootstrap:
            raise ValueError("raw_summary_generation_invalid; --allow-bootstrap permits explicit scoped repair")
        force_rebuild = True
    if raw_observer is not None and manifest and "raw_volume" not in manifest and max(stat.st_size, int(manifest.get("raw_offset") or 0)) > 64 * 1024 * 1024 and not allow_bootstrap:
        raise ValueError("volume_bootstrap_required; approved source-day streaming required")
    callback_sources = []
    for callback in (reason_labeler, ignore_payload):
        if callback is None:
            continue
        try:
            callback_sources.append(inspect.getsource(callback))
            owner_file = inspect.getsourcefile(callback)
            if owner_file:
                callback_sources.append(hashlib.sha256(Path(owner_file).read_bytes()).hexdigest())
            if getattr(callback, "__closure__", None):
                force_rebuild = True  # Unbound captured state has no append-prefix authority.
        except (OSError, TypeError):
            force_rebuild = True  # Still support normal streaming calculation.
    callback_contract = hashlib.sha256("\n".join(callback_sources).encode()).hexdigest()
    raw_offset = int(manifest.get("raw_offset") or 0)
    raw_size = max(int(stat.st_size), raw_offset) if is_gzip_raw else int(stat.st_size)
    archived_summary_path = Path(f"{summary_path}.gz")
    summary_exists = summary_path.exists() or archived_summary_path.exists()
    stale_summary = (
        force_rebuild
        or int(manifest.get("schema_version") or 0) != SUMMARY_SCHEMA_VERSION
        or str(manifest.get("raw_path") or "") != str(raw_path)
        or int(manifest.get("raw_inode") or -1) != int(raw_inode or -1)
        or set(manifest.get("summary_stages") or ()) != set(summary_stages)
        or str(manifest.get("summary_detail_level") or "") != summary_detail_level
        or (int(manifest.get("raw_size") or 0) == raw_size and (manifest.get("raw_mtime_ns") != stat.st_mtime_ns
            or manifest.get("raw_ctime_ns", stat.st_ctime_ns) != stat.st_ctime_ns))
        or (raw_observer is not None and "raw_volume" not in manifest)
        or (raw_observer is not None and manifest.get("observer_contract") != observer_contract)
        or (manifest.get("callback_contract") and manifest["callback_contract"] != callback_contract)
        or (manifest.get("parser_contract") and manifest["parser_contract"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        or raw_offset > raw_size
        or not summary_exists
        or (incremental_rollup and not is_gzip_raw and not raw_path.with_name(f".{raw_path.name}.partition.lock").is_file())
    )
    if stale_summary:
        raw_offset = 0
    if not summary_path.exists() and not archived_summary_path.exists():
        summary_path.touch(exist_ok=True)

    if observer_state is not None:
        observer_state.clear()
        observer_state.update({} if stale_summary else manifest.get("raw_volume") or {})
    groups: dict[tuple[str, ...], _SummaryAggregate] = {}
    appended_raw_lines = 0
    appended_source_events = 0
    decode_errors = 0
    last_good_offset = raw_offset
    incomplete_tail = False
    incomplete_tail_bytes = 0
    raw_opener = gzip.open if is_gzip_raw else open
    with raw_opener(raw_path, "rb") as raw_handle:
        raw_handle.seek(raw_offset)
        while True:
            line_start = raw_handle.tell()
            raw_bytes = raw_handle.readline()
            if not raw_bytes:
                break
            appended_raw_lines += 1
            if not raw_bytes.endswith(b"\n"):
                incomplete_tail = True
                incomplete_tail_bytes = len(raw_bytes)
                break
            line_end = raw_handle.tell()
            raw_line = raw_bytes.decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                if raw_observer is not None:
                    raw_observer(raw_bytes, None)
                decode_errors += 1
                last_good_offset = line_end
                continue
            if raw_observer is not None:
                raw_observer(raw_bytes, payload)
            if isinstance(payload, dict):
                event = _summary_event_from_payload(
                    payload,
                    reason_labeler=reason_labeler,
                    ignore_payload=ignore_payload,
                    line_start=line_start,
                    line_end=line_end,
                    summary_stages=summary_stages,
                )
                if event is not None:
                    key = _aggregate_key(event)
                    aggregate = groups.get(key)
                    if aggregate is None:
                        aggregate = groups[key] = _new_aggregate(
                            event,
                            include_diagnostics=(summary_profile != "producer_parity"),
                        )
                    aggregate.add(event)
                    appended_source_events += 1
            last_good_offset = line_end
            if last_good_offset <= line_start:
                break

    new_rows = [groups[key].to_row(target_date=target_date, summary_detail_level=summary_detail_level)
                for key in sorted(groups)]
    appended_summary_rows = len(new_rows)
    # Build successors off to the side; do not delete the valid generation before
    # a rebuild succeeds. An interrupted two-file publication is detected by stamp.
    publish_path = summary_path.with_name(f"{summary_path.name}.rebuild.{os.getpid()}") if stale_summary else summary_path
    if not stale_summary:
        _rehydrate_summary_for_append(summary_path)
    initial_size = publish_path.stat().st_size if publish_path.exists() else 0
    with publish_path.open("w" if stale_summary else "a", encoding="utf-8") as summary_handle:
        for row in new_rows:
            summary_handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        summary_handle.flush()
        os.fsync(summary_handle.fileno())
    if incremental_rollup:
        previous = [] if stale_summary else manifest.get("identity_rollup")
        if previous is None:
            previous = _load_summary_rows(summary_path, include_samples=False)
            # This legacy bootstrap already includes the new append.
            rows = merge_identity_rows([], previous)
        else:
            rows = merge_identity_rows(previous, new_rows)
    else:
        rows = _load_summary_rows(publish_path, include_samples=include_samples)
    backup_path = summary_path.with_name(f"{summary_path.name}.previous.{os.getpid()}")
    if stale_summary:
        if summary_path.exists():
            backup_path.unlink(missing_ok=True)
            os.link(summary_path, backup_path)
        publish_path.replace(summary_path)
    actual_summary = existing_or_gzip_path(summary_path)
    final_stat = raw_path.stat()
    final_stat_size = int(final_stat.st_size)
    final_raw_size = (
        max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
    )
    new_manifest = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "raw_path": str(raw_path),
        "raw_inode": raw_inode,
        "raw_mtime_ns": final_stat.st_mtime_ns,
        "raw_ctime_ns": final_stat.st_ctime_ns,
        "raw_offset": last_good_offset,
        "start_raw_offset": raw_offset,
        "raw_size": final_raw_size,
        "summary_path": str(summary_path),
        "manifest_path": str(manifest_path),
        "summary_profile": summary_profile,
        "summary_detail_level": summary_detail_level,
        "summary_row_count": appended_summary_rows + (0 if stale_summary else int(manifest.get("summary_row_count") or 0)),
        "incomplete_tail": incomplete_tail,
        "incomplete_tail_bytes": incomplete_tail_bytes,
        "appended_raw_lines": appended_raw_lines,
        "appended_source_events": appended_source_events,
        "appended_summary_rows": appended_summary_rows,
        "decode_errors": decode_errors,
        "rebuilt": stale_summary,
        "complete_through_raw_offset": last_good_offset,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "summary_stages": sorted(summary_stages),
        "metric_role": "ops_volume_diagnostic",
        "decision_authority": "diagnostic_aggregation",
        "runtime_effect": False,
        "raw_suppression_enabled": False,
    }
    if observer_state is not None:
        new_manifest["raw_volume"] = observer_state
    if incremental_rollup:
        new_manifest["identity_rollup"] = rows
    if not stale_summary and "producer_rollup" in manifest:
        new_manifest["producer_rollup"] = manifest["producer_rollup"]
    st = actual_summary.stat()
    new_manifest["summary_stamp"] = [st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
    new_manifest["callback_contract"] = callback_contract
    new_manifest["observer_contract"] = observer_contract
    new_manifest["parser_contract"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    new_manifest["checkpoint_digest"] = checkpoint_digest(new_manifest)
    try:
        _write_json(manifest_path, new_manifest)
    except Exception:
        if stale_summary and backup_path.exists():
            backup_path.replace(summary_path)
            if manifest:
                st = summary_path.stat()
                manifest["summary_stamp"] = [st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
                manifest["checkpoint_digest"] = checkpoint_digest(manifest)
                _write_json(manifest_path, manifest)
        if not stale_summary:
            with summary_path.open("r+b") as handle:
                handle.truncate(initial_size)
            # Rollback changes metadata; retain a matching receipt for the old
            # valid offset if publication failed before the commit.
            if manifest:
                st = summary_path.stat()
                manifest["summary_stamp"] = [st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
                manifest["checkpoint_digest"] = checkpoint_digest(manifest)
                _write_json(manifest_path, manifest)
        raise
    backup_path.unlink(missing_ok=True)
    archived_summary_path.unlink(missing_ok=True)
    return rows, {
        "enabled": True,
        "status": "ok",
        **new_manifest,
    }


def _measure_submit(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        started = time.perf_counter()
        try:
            return method(self, *args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            with self._lock:
                self._submit_durations.append(elapsed)
                self._submit_count += 1

    return wrapped


class ProducerSummaryCompactor:
    def __init__(
        self,
        *,
        summary_dir: Path,
        mode: str = "off",
        flush_sec: int = 60,
        sample_per_bucket: int = 2,
        reason_labeler: ReasonLabeler = default_reason_label,
        auto_flush: bool = False,
    ) -> None:
        self.summary_dir = summary_dir
        self.requested_mode = mode
        # No verified consumer-preserving suppression owner exists. A legacy
        # env value must not silently grant permission to discard source rows.
        self.mode = (
            "shadow"
            if mode == "suppress"
            else mode if mode in {"off", "shadow"} else "off"
        )
        self.flush_sec = max(0, int(flush_sec or 0))
        if self.flush_sec > PRODUCER_MAX_FLUSH_SEC:
            raise ValueError("producer flush interval exceeds supported 3600 seconds")
        self.sample_per_bucket = max(1, min(int(sample_per_bucket or 2), 6))
        self.reason_labeler = reason_labeler
        self._groups: dict[tuple[str, ...], _SummaryAggregate] = {}
        self._last_flush_monotonic = time.monotonic()
        self._sequence = 0
        self._lock = threading.RLock()
        # Disk publication never owns the submit/aggregation lock. One detached
        # retry batch and one active buffer are each bounded by MAX_GROUPS.
        self._publish_lock = threading.Lock()
        self._pending_batch = None
        self._lossless_by_key: Counter = Counter()
        self._submit_durations: deque[float] = deque(maxlen=2048)
        self._submit_count = 0
        self._rejected_count = 0
        self._closed = False
        self._auto_flush = bool(auto_flush)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._worker: threading.Thread | None = None
        self.flush_error_count = 0
        self.last_flush_error: str | None = None
        self.health_write_error_count = 0
        if auto_flush and self.enabled:
            self._worker = threading.Thread(
                target=self._flush_loop, name="pipeline-summary-flush", daemon=True
            )
            self._worker.start()

    def _flush_loop(self) -> None:
        failed = False
        while True:
            if failed:
                # High-water wakeups must not turn a persistent disk/lock
                # failure into a per-event retry storm.
                self._stop.wait(max(1, self.flush_sec))
            else:
                self._wake.wait(max(1, self.flush_sec))
            self._wake.clear()
            stopping = self._stop.is_set()
            try:
                self.flush()
                failed = False
            except Exception as exc:
                failed = True
                with self._lock:
                    self.flush_error_count += 1
                    self.last_flush_error = type(exc).__name__
                logging.getLogger(__name__).warning(
                    "producer summary flush failed; raw retained: %s",
                    type(exc).__name__,
                )
            if stopping:
                return

    def close(self, *, wait: bool = True) -> None:
        with self._lock:
            self._closed = True
        self._stop.set()
        self._wake.set()
        if self._worker is None:
            self.flush()
        elif wait:
            self._worker.join(timeout=5)
            if self._worker.is_alive():
                raise TimeoutError("producer summary shutdown drain exceeded 5 seconds")
            if self._pending_batch is not None or self._groups:
                self.flush()

    @property
    def enabled(self) -> bool:
        return self.mode in {"shadow", "suppress"}

    @_measure_submit
    def submit(
        self, payload: dict[str, Any], *, threshold_family: str | None = None
    ) -> dict[str, Any]:
        with self._lock:
            result = self._record(payload, threshold_family=threshold_family)
        if result.pop("_flush_requested", False):
            self.flush()
        return result

    def _record(
        self, payload: dict[str, Any], *, threshold_family: str | None
    ) -> dict[str, Any]:
        if not self.enabled or _safe_str(payload.get("event_type")) != "pipeline_event":
            return {"mode": self.mode, "summary_recorded": False, "suppress_raw": False}
        if self._closed:
            raise RuntimeError("producer summary is closed; raw must be retained")

        stage = _safe_str(payload.get("stage"))
        lossless = payload_has_lossless_authority(
            payload, threshold_family=threshold_family
        )
        if stage not in PRODUCER_SUMMARY_STAGES:
            return {
                "mode": self.mode,
                "summary_recorded": False,
                "suppress_raw": False,
                "lossless": True,
            }

        self._sequence += 1
        event = summary_event_from_payload(
            payload,
            reason_labeler=self.reason_labeler,
            line_start=self._sequence,
            line_end=self._sequence,
            summary_stages=PRODUCER_SUMMARY_STAGES,
        )
        if event is None:
            return {
                "mode": self.mode,
                "summary_recorded": False,
                "suppress_raw": False,
                "lossless": lossless,
            }

        event_date = event.emitted_at.strftime("%Y-%m-%d")
        pending_dates = (
            set()
            if self._auto_flush
            else {
                aggregate.bucket_start.strftime("%Y-%m-%d")
                for aggregate in self._groups.values()
            }
        )
        key = _aggregate_key(event)
        if len(self._groups) >= PRODUCER_MAX_GROUPS and key not in self._groups:
            self._rejected_count += 1
            raise BufferError("producer summary buffer full; raw retained")
        aggregate = self._groups.get(key)
        if aggregate is None:
            aggregate = self._groups[key] = _new_aggregate(
                event,
                sample_per_bucket=self.sample_per_bucket,
                include_diagnostics=False,
            )
        aggregate.add(event)
        suppress_raw = False
        if lossless:
            self._lossless_by_key[key] += 1
        if self._auto_flush and len(self._groups) >= max(1, PRODUCER_MAX_GROUPS // 2):
            self._wake.set()
        return {
            "mode": self.mode,
            "summary_recorded": True,
            "suppress_raw": suppress_raw,
            "lossless": lossless,
            "_flush_requested": not self._auto_flush
            and (
                self.flush_sec == 0
                or (pending_dates and pending_dates != {event_date})
                or time.monotonic() - self._last_flush_monotonic >= self.flush_sec
            ),
        }

    def flush(self, *, target_date: str | None = None) -> dict[str, Any]:
        with self._publish_lock:
            with self._lock:
                dates = {
                    group.bucket_start.strftime("%Y-%m-%d")
                    for group in self._groups.values()
                }
                work_dates = sorted(dates)
                if self._pending_batch is not None:
                    dates.add(self._pending_batch[0])
                    work_dates.insert(0, self._pending_batch[0])
                safe_date = _safe_str(target_date)
                if safe_date and dates and dates != {safe_date}:
                    raise ValueError(
                        "producer summary target date does not match pending events"
                    )
            result = {
                "enabled": self.enabled,
                "mode": self.mode,
                "status": "no_pending_rows" if self.enabled else "disabled",
                "flushed_rows": 0,
            }
            # Capture dates once, so a continuous stream cannot prevent return.
            for day in work_dates if self.enabled else []:
                with self._lock:
                    if self._pending_batch is None:
                        keys = [
                            key
                            for key, group in self._groups.items()
                            if group.bucket_start.strftime("%Y-%m-%d") == day
                        ]
                        if not keys:
                            continue
                        groups = {key: self._groups.pop(key) for key in keys}
                        lossless = sum(
                            self._lossless_by_key.pop(key, 0) for key in keys
                        )
                        self._pending_batch = (day, groups, lossless)
                result = self._flush_batch()
                with self._lock:
                    self._pending_batch = None
                    self._last_flush_monotonic = time.monotonic()
            return result

    def _flush_batch(self) -> dict[str, Any]:
        safe_date = self._pending_batch[0]
        started = time.perf_counter()
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path, manifest_path = producer_summary_paths(
            self.summary_dir, safe_date
        )
        # Cross-process serialization covers both the append and manifest.
        # Do not delete this mutex file to recover a worker.
        with manifest_path.with_suffix(".lock").open("a") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            manifest = self._publish(summary_path, manifest_path, safe_date)
        # Measure through append, close, canonical manifest publication and
        # mutex release. The separate telemetry receipt's own I/O is excluded.
        duration_ms = (time.perf_counter() - started) * 1000
        with self._lock:
            samples = tuple(self._submit_durations)
            submit_count = self._submit_count
            rejected_count = self._rejected_count
        ordered = sorted(samples)
        health = {
            "schema_version": 1,
            "timing_contract": PRODUCER_TIMING_CONTRACT,
            "target_date": safe_date,
            "writer_pid": os.getpid(),
            "manifest_sha256": producer_manifest_fingerprint(manifest),
            "last_flush_duration_ms": round(duration_ms, 3),
            "duration_scope": "summary_and_canonical_manifest_publish_excludes_health_receipt",
            "submit_sample_window": "last_2048_process_calls",
            "submit_duration_scope": "summary_submit_only_excludes_raw_writer_and_orders",
            "submit_sample_count": len(ordered),
            "submit_count": submit_count,
            "rejected_summary_count": rejected_count,
            "submit_p95_ms": (
                round(ordered[math.ceil(len(ordered) * 0.95) - 1], 3)
                if ordered
                else None
            ),
            "submit_p99_ms": (
                round(ordered[math.ceil(len(ordered) * 0.99) - 1], 3)
                if ordered
                else None
            ),
            "submit_max_ms": round(max(ordered), 3) if ordered else None,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        try:
            # A mode handover can briefly have two compactors in the same PID.
            # Serialize their receipt writes and never overwrite newer evidence.
            with manifest_path.with_suffix(".lock").open("a") as health_lock:
                fcntl.flock(health_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                current = json.loads(manifest_path.read_text(encoding="utf-8"))
                if producer_manifest_fingerprint(current) == health["manifest_sha256"]:
                    _write_json(
                        producer_health_path(self.summary_dir, safe_date, os.getpid()),
                        health,
                    )
        except Exception as exc:
            # Publication already committed. Never retry its append because
            # optional telemetry failed; exact hash mismatch reports the gap.
            self.health_write_error_count += 1
            logging.getLogger(__name__).warning(
                "producer timing receipt failed: %s", type(exc).__name__
            )
        return {
            "enabled": True,
            "mode": self.mode,
            "status": "ok",
            **manifest,
            "last_flush_duration_ms": round(duration_ms, 3),
        }

    def _publish(
        self, summary_path: Path, manifest_path: Path, safe_date: str
    ) -> dict[str, Any]:
        _rehydrate_summary_for_append(summary_path)
        flushed_rows = 0
        flushed_events = 0
        flush_first_event_at = ""
        flush_last_event_at = ""
        lines = []
        groups = self._pending_batch[1]
        for key in sorted(groups):
            row = groups[key].to_row(
                target_date=safe_date,
                summary_detail_level=PRODUCER_PARITY_DETAIL_LEVEL,
            )
            row["schema_version"] = PRODUCER_SUMMARY_SCHEMA_VERSION
            row["producer_mode"] = self.mode
            row["source"] = "pipeline_event_logger"
            lines.append(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            flushed_rows += 1
            flushed_events += int(row.get("event_count") or 0)
            first_seen = _safe_str(row.get("first_seen"))
            last_seen = _safe_str(row.get("last_seen"))
            if first_seen:
                flush_first_event_at = (
                    min(flush_first_event_at, first_seen)
                    if flush_first_event_at
                    else first_seen
                )
            if last_seen:
                flush_last_event_at = max(flush_last_event_at, last_seen)
        existing = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {}
        )
        if not isinstance(existing, dict):
            raise ValueError("invalid producer manifest")
        if existing and not summary_path.exists() and existing.get("summary_event_count"):
            raise ValueError("producer_summary_committed_body_missing; raw retained")
        if existing and summary_path.exists() and existing.get("summary_storage_size_bytes") != summary_path.stat().st_size:
            raise ValueError("producer_summary_uncommitted_or_corrupt_generation; raw retained")
        if not existing and summary_path.exists() and summary_path.stat().st_size:
            raise ValueError("producer_summary_missing_commit_receipt; raw retained")
        previous_rows = int(existing.get("summary_row_count") or 0)
        previous_events = int(existing.get("summary_event_count") or 0)
        existing_first_event_at = _safe_str(existing.get("coverage_first_event_at"))
        existing_last_event_at = _safe_str(existing.get("coverage_last_event_at"))
        coverage_first_event_at = (
            min(existing_first_event_at, flush_first_event_at)
            if existing_first_event_at and flush_first_event_at
            else existing_first_event_at or flush_first_event_at
        )
        coverage_last_event_at = max(existing_last_event_at, flush_last_event_at)
        manifest = {
            "schema_version": PRODUCER_SUMMARY_SCHEMA_VERSION,
            "summary_path": str(summary_path),
            "summary_row_count": previous_rows + flushed_rows,
            "summary_event_count": previous_events + flushed_events,
            "last_flush_rows": flushed_rows,
            "last_flush_events": flushed_events,
            "coverage_first_event_at": coverage_first_event_at or None,
            "coverage_last_event_at": coverage_last_event_at or None,
            "mode": self.mode,
            "requested_mode": self.requested_mode,
            "summary_detail_level": PRODUCER_PARITY_DETAIL_LEVEL,
            "identity_contract": IDENTITY_CONTRACT,
            "timing_contract": PRODUCER_TIMING_CONTRACT,
            "flush_interval_sec": self.flush_sec,
            "periodic_flush_enabled": self._worker is not None,
            "last_writer_pid": os.getpid(),
            "flush_error_count": self.flush_error_count,
            "health_write_error_count": self.health_write_error_count,
            "last_flush_error": self.last_flush_error,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "summary_stages": sorted(PRODUCER_SUMMARY_STAGES),
            "sample_per_bucket": self.sample_per_bucket,
            "suppressed_count": int(existing.get("suppressed_count") or 0),
            "lossless_preserved_count": int(
                existing.get("lossless_preserved_count") or 0
            )
            + self._pending_batch[2],
            "metric_role": "ops_volume_diagnostic",
            "decision_authority": "diagnostic_aggregation",
            "runtime_effect": False,
            "raw_suppression_enabled": False,
        }
        serialized = "".join(lines).encode("utf-8")
        with summary_path.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            initial_size = handle.tell()
            try:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
                manifest["last_flush_bytes"] = len(serialized)
                manifest["summary_storage_size_bytes"] = handle.tell()
                _write_json(manifest_path, manifest)
            except Exception:
                # Roll back only this locked append, keeping pending groups for
                # a bounded retry; never duplicate a partially published batch.
                handle.truncate(initial_size)
                raise
        return manifest
