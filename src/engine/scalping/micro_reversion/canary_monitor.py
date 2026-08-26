"""Fail-closed runtime health monitor for the forward-collector canary.

The monitor consumes only the collector's read-only runtime snapshot.  It may
request that the observer itself stop, but it has no strategy, simulation, or
broker authority.  Snapshot persistence runs outside the market-data lock.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import statistics
import tempfile
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .forward_collector import (
    ForwardCollectorConfig,
    ForwardObservationCollector,
    PRODUCER_CALLBACK_LATENCY_SCOPE,
)
from .observation_adapter import ObserverFeatureFlags

KST = ZoneInfo("Asia/Seoul")
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CANARY_GUARD_SCHEMA = "scalp_micro_reversion_canary_guard_v1"
CANARY_MONITOR_SCHEMA = "scalp_micro_reversion_canary_monitor_v1"
CANARY_BASELINE_SCHEMA = "scalp_micro_reversion_callback_baseline_v1"
DEFAULT_GUARD_PATH = REPOSITORY_ROOT / Path(
    "configs/scalp_micro_reversion_canary_guard.toml"
)
DEFAULT_SNAPSHOT_PATH = REPOSITORY_ROOT / Path(
    "data/runtime/scalp_micro_reversion_forward_collector/latest.json"
)
CANARY_MONITOR_METRIC_CONTRACT = {
    "metric_role": "source_quality_gate_and_observer_canary_safety_veto",
    "decision_authority": "observer_canary_stop_only_no_trading_authority",
    "window_policy": "current_process_cumulative_with_periodic_snapshot",
    "sample_floor": "latency_guard_after_frozen_minimum_callback_samples",
    "primary_decision_metric": "stop_required",
    "source_quality_gate": (
        "fresh_collector_snapshot_and_valid_frozen_guard_config;_bounded_ingress_"
        "queue_loss_is_source_quality_exclusion_and_provider_replay_hold;_"
        "successful_write_below_preventive_low_disk_watermark_is_operational_"
        "warning_only;_worker_writer_actual_capture_loss_storage_self_disable_"
        "or_authority_failure_is_immediate_stop"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "buy_wait_drop_or_entry_exit_decision",
        "simulated_or_real_position_creation",
        "threshold_provider_bot_quantity_or_cap_mutation",
        "p2_policy_selection_or_economic_edge_claim",
    ),
}


@dataclass(frozen=True, slots=True)
class CanaryGuard:
    baseline_id: str
    minimum_callback_samples: int
    producer_callback_latency_p95_max_ms: float
    producer_callback_latency_p99_max_ms: float
    latency_breach_confirmation_snapshots: int
    latency_breach_immediate_multiplier: float
    snapshot_stale_after_sec: float
    config_sha256: str


_ROW_EXCLUSION_COUNTERS = (
    "observation_queue_full_count",
    "observation_dropped_envelope_count",
)

_ZERO_STOP_COUNTERS = (
    "adapter_isolated_error_count",
    "worker_error_count",
    "path_point_dropped_count",
    "event_reference_error_count",
    "orphan_reference_count",
    "unreferenced_segment_count",
    "reference_reconciliation_error_count",
    "duplicate_event_reference_count",
    "duplicate_event_id_count",
    "duplicate_path_reference_pair_count",
    "path_duplicate_sequence_count",
    "path_out_of_order_sequence_count",
    "path_local_receive_timestamp_regression_count",
    "unexplained_sequence_gap_count",
    "writer_queue_full_count",
    "writer_dropped_envelope_count",
    "writer_error_count",
    "writer_restart_count",
    "writer_capture_degraded_count",
    "writer_storage_self_disabled_count",
    "writer_manifest_error_count",
    "writer_projection_breach_count",
    "canonical_stream_duplicate_count",
    "collector_close_failure_count",
    "collector_worker_alive_after_close_count",
    "writer_alive_after_close_count",
    "event_symbol_mismatch_count",
)

_FORBIDDEN_TRUE_FIELDS = (
    "p2_real_data_discovery_run",
    "research_policy_selected",
    "selection_authority",
    "sim_position_effect",
    "trading_runtime_effect",
    "trading_decision_effect",
    "threshold_effect",
    "broker_effect",
    "actual_order_submitted",
)

_DEPTH_ROW_EXCLUSION_COUNTERS = (
    "depth_queue_full_count",
    "depth_dropped_envelope_count",
)

_DEPTH_ZERO_STOP_COUNTERS = (
    "depth_worker_error_count",
    "depth_writer_queue_full_count",
    "depth_writer_dropped_envelope_count",
    "depth_writer_error_count",
    "depth_writer_storage_self_disabled_count",
    "depth_writer_manifest_error_count",
    "depth_writer_projection_breach_count",
)


def load_canary_guard(path: Path | str = DEFAULT_GUARD_PATH) -> CanaryGuard:
    guard_path = Path(path)
    raw = guard_path.read_bytes()
    payload = tomllib.loads(raw.decode("utf-8"))
    if payload.get("schema") != CANARY_GUARD_SCHEMA:
        raise ValueError("unexpected canary guard schema")
    limits = payload.get("limits")
    if not isinstance(limits, dict):
        raise ValueError("canary guard limits are missing")
    baseline_id = str(payload.get("baseline_id") or "").strip()
    minimum_samples = _positive_int(limits.get("minimum_callback_samples"))
    p95_max = _positive_float(limits.get("producer_callback_latency_p95_max_ms"))
    p99_max = _positive_float(limits.get("producer_callback_latency_p99_max_ms"))
    latency_confirmation_snapshots = _positive_int(
        payload.get("latency_breach_confirmation_snapshots")
    )
    latency_immediate_multiplier = _positive_float(
        payload.get("latency_breach_immediate_multiplier")
    )
    stale_after = _positive_float(limits.get("snapshot_stale_after_sec"))
    if not baseline_id or minimum_samples is None:
        raise ValueError("canary guard baseline/sample floor is invalid")
    if p95_max is None or p99_max is None or p95_max > p99_max:
        raise ValueError("canary latency limits are invalid")
    if latency_confirmation_snapshots is None:
        raise ValueError("canary latency confirmation floor is invalid")
    if latency_immediate_multiplier is None or latency_immediate_multiplier <= 1.0:
        raise ValueError("canary immediate latency multiplier is invalid")
    if stale_after is None:
        raise ValueError("canary snapshot freshness limit is invalid")
    return CanaryGuard(
        baseline_id=baseline_id,
        minimum_callback_samples=minimum_samples,
        producer_callback_latency_p95_max_ms=p95_max,
        producer_callback_latency_p99_max_ms=p99_max,
        latency_breach_confirmation_snapshots=latency_confirmation_snapshots,
        latency_breach_immediate_multiplier=latency_immediate_multiplier,
        snapshot_stale_after_sec=stale_after,
        config_sha256=hashlib.sha256(raw).hexdigest(),
    )


def evaluate_canary_snapshot(
    collector_snapshot: dict[str, Any],
    guard: CanaryGuard,
) -> dict[str, Any]:
    snapshot = dict(collector_snapshot or {})
    reasons: list[str] = []
    operational_capacity_warnings: list[str] = []
    lifecycle = str(snapshot.get("collector_lifecycle") or "unknown").lower()
    running = lifecycle == "running"

    isolated_error = str(snapshot.get("isolated_error_type") or "").strip()
    if isolated_error:
        reasons.append(f"isolated_error_type:{isolated_error}")
    for field in _ZERO_STOP_COUNTERS:
        value = _nonnegative_float(snapshot.get(field))
        if value is None:
            reasons.append(f"missing_or_invalid_metric:{field}")
        elif value > 0:
            reasons.append(f"nonzero_stop_metric:{field}={_compact_number(value)}")
    if snapshot.get("depth_capture_requested") is True:
        if running and snapshot.get("depth_capture_active") is not True:
            reasons.append("depth_capture_requested_but_not_active")
        for field in _DEPTH_ZERO_STOP_COUNTERS:
            value = _nonnegative_float(snapshot.get(field))
            if value is None:
                reasons.append(f"missing_or_invalid_metric:{field}")
            elif value > 0:
                reasons.append(f"nonzero_stop_metric:{field}={_compact_number(value)}")
        if running:
            depth_writer_count = _nonnegative_int(snapshot.get("depth_writer_count"))
            depth_writer_alive_count = _nonnegative_int(
                snapshot.get("depth_writer_alive_count")
            )
            if depth_writer_count is None or depth_writer_alive_count is None:
                reasons.append("missing_or_invalid_depth_writer_liveness_metric")
            elif depth_writer_alive_count != depth_writer_count:
                reasons.append(
                    "depth_writer_liveness_mismatch:"
                    f"alive={depth_writer_alive_count},expected={depth_writer_count}"
                )
    for field in _FORBIDDEN_TRUE_FIELDS:
        if snapshot.get(field) is not False:
            reasons.append(f"forbidden_authority_field:{field}")
    if snapshot.get("broker_order_forbidden") is not True:
        reasons.append("forbidden_authority_field:broker_order_forbidden")

    for field, label in (
        ("writer_low_disk_watermark_breach_count", "writer"),
        ("depth_writer_low_disk_watermark_breach_count", "depth_writer"),
    ):
        low_disk_breach_count = _nonnegative_int(snapshot.get(field, 0))
        if low_disk_breach_count is None:
            reasons.append(f"missing_or_invalid_metric:{field}")
        elif low_disk_breach_count > 0:
            operational_capacity_warnings.append(
                f"{label}_low_disk_watermark_capacity_warning:"
                f"writers={low_disk_breach_count}"
            )

    if running:
        for field in (
            "observer_runtime_loaded",
            "producer_observation_connected",
            "observer_runtime_effect",
            "observation_capture_active",
        ):
            if snapshot.get(field) is not True:
                reasons.append(f"inactive_required_field:{field}")
        writer_count = _nonnegative_int(snapshot.get("writer_count"))
        writer_alive_count = _nonnegative_int(snapshot.get("writer_alive_count"))
        if writer_count is None or writer_alive_count is None:
            reasons.append("missing_or_invalid_writer_liveness_metric")
        elif writer_alive_count != writer_count:
            reasons.append(
                "writer_liveness_mismatch:"
                f"alive={writer_alive_count},expected={writer_count}"
            )
    elif lifecycle in {"closing", "close_failed", "closed"}:
        if (
            lifecycle == "closed"
            and snapshot.get("reference_reconciliation_completed") is not True
        ):
            reasons.append("reconciliation_not_completed_after_close")
    else:
        reasons.append(f"unexpected_collector_lifecycle:{lifecycle}")

    callback_count = _nonnegative_int(snapshot.get("producer_0b_callback_count"))
    callback_latency_scope = str(
        snapshot.get("producer_callback_latency_scope") or ""
    ).strip()
    p95_ms = _nonnegative_float(snapshot.get("producer_callback_latency_p95_ms"))
    p99_ms = _nonnegative_float(snapshot.get("producer_callback_latency_p99_ms"))
    latency_guard_armed = bool(
        callback_count is not None and callback_count >= guard.minimum_callback_samples
    )
    if callback_latency_scope != PRODUCER_CALLBACK_LATENCY_SCOPE:
        reasons.append("producer_callback_latency_scope_invalid")
    if callback_count is None or p95_ms is None or p99_ms is None:
        reasons.append("missing_or_invalid_callback_latency_metric")
    elif latency_guard_armed:
        if p95_ms > guard.producer_callback_latency_p95_max_ms:
            reasons.append(
                "producer_callback_latency_p95_exceeded:"
                f"{p95_ms:.6f}>{guard.producer_callback_latency_p95_max_ms:.6f}"
            )
        if p99_ms > guard.producer_callback_latency_p99_max_ms:
            reasons.append(
                "producer_callback_latency_p99_exceeded:"
                f"{p99_ms:.6f}>{guard.producer_callback_latency_p99_max_ms:.6f}"
            )

    source_quality_row_exclusions = []
    for field in _ROW_EXCLUSION_COUNTERS:
        value = _nonnegative_int(snapshot.get(field))
        if value is None:
            reasons.append(f"missing_or_invalid_metric:{field}")
        elif value > 0:
            source_quality_row_exclusions.append(
                f"raw_row_exclusion_required:{field}={value}"
            )
    if snapshot.get("depth_capture_requested") is True:
        for field in _DEPTH_ROW_EXCLUSION_COUNTERS:
            value = _nonnegative_int(snapshot.get(field))
            if value is None:
                reasons.append(f"missing_or_invalid_metric:{field}")
            elif value > 0:
                source_quality_row_exclusions.append(
                    f"raw_row_exclusion_required:{field}={value}"
                )
    timestamp_regression_exceeded_count = _nonnegative_int(
        snapshot.get("path_exchange_timestamp_regression_exceeded_count")
    )
    if timestamp_regression_exceeded_count is None:
        reasons.append(
            "missing_or_invalid_metric:"
            "path_exchange_timestamp_regression_exceeded_count"
        )
    elif timestamp_regression_exceeded_count > 0:
        source_quality_row_exclusions.append(
            "raw_row_exclusion_required:"
            "path_exchange_timestamp_regression_exceeded_count="
            f"{timestamp_regression_exceeded_count}"
        )

    auto_stop_reason = str(snapshot.get("canary_auto_stop_reason") or "").strip()
    if auto_stop_reason:
        reasons.append(f"prior_auto_stop:{auto_stop_reason}")
    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        status = "stop_required"
    elif lifecycle == "closed":
        status = "stopped_clean"
    elif source_quality_row_exclusions and running:
        status = "healthy_observer_canary_with_source_row_exclusions"
    elif not latency_guard_armed:
        status = "warming_up"
    elif running:
        status = "healthy_observer_canary"
    else:
        status = "stopped_clean"
    return {
        "status": status,
        "stop_required": bool(unique_reasons),
        "stop_reasons": unique_reasons,
        "source_quality_row_exclusions": tuple(source_quality_row_exclusions),
        "operational_capacity_warnings": tuple(operational_capacity_warnings),
        "raw_row_exclusion_required": bool(source_quality_row_exclusions),
        "latency_guard_armed": latency_guard_armed,
        "callback_sample_count": callback_count,
        "observed_latency_p95_ms": p95_ms,
        "observed_latency_p99_ms": p99_ms,
        "latency_p95_max_ms": guard.producer_callback_latency_p95_max_ms,
        "latency_p99_max_ms": guard.producer_callback_latency_p99_max_ms,
        "latency_breach_confirmation_snapshots": (
            guard.latency_breach_confirmation_snapshots
        ),
        "latency_breach_immediate_multiplier": (
            guard.latency_breach_immediate_multiplier
        ),
        "minimum_callback_samples": guard.minimum_callback_samples,
        "snapshot_stale_after_sec": guard.snapshot_stale_after_sec,
    }


def write_canary_runtime_snapshot(
    collector_snapshot: dict[str, Any],
    *,
    guard_path: Path | str = DEFAULT_GUARD_PATH,
    output_path: Path | str = DEFAULT_SNAPSHOT_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    generated_at = now or datetime.now(KST)
    guard = load_canary_guard(guard_path)
    evaluation = evaluate_canary_snapshot(collector_snapshot, guard)
    payload = {
        "schema": CANARY_MONITOR_SCHEMA,
        "generated_at": generated_at.isoformat(timespec="milliseconds"),
        "generated_at_epoch": generated_at.timestamp(),
        "valid_until_epoch": (
            generated_at.timestamp() + guard.snapshot_stale_after_sec
        ),
        "baseline_id": guard.baseline_id,
        "guard_config_sha256": guard.config_sha256,
        **CANARY_MONITOR_METRIC_CONTRACT,
        "canary_guard": evaluation,
        "collector_snapshot": collector_snapshot,
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    normalized_payload = json.loads(encoded)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{time.time_ns()}.tmp"
    )
    try:
        temporary.write_text(
            encoded,
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
    return normalized_payload


def run_callback_latency_preflight(
    *,
    iterations: int = 5_000,
    warmup: int = 500,
    repeats: int = 5,
) -> dict[str, Any]:
    if iterations < 1_000 or warmup < 0 or repeats < 3:
        raise ValueError("preflight requires iterations>=1000, warmup>=0, repeats>=3")
    off_runs: list[dict[str, float]] = []
    on_runs: list[dict[str, float]] = []
    for repeat_index in range(repeats):
        payload = _benchmark_snapshot(repeat_index)
        off_samples = _measure_callback(
            lambda: _observer_branch(None, "000001", payload),
            iterations=iterations,
            warmup=warmup,
        )
        off_runs.append(_latency_summary(off_samples))
        with tempfile.TemporaryDirectory(
            prefix="scalp-micro-reversion-canary-preflight-"
        ) as directory:
            collector = ForwardObservationCollector(
                flags=ObserverFeatureFlags(
                    observer_enabled=True,
                    path_capture_enabled=True,
                    discovery_enabled=False,
                ),
                config=ForwardCollectorConfig(
                    output_root=Path(directory),
                    observation_queue_size=iterations + warmup + 1_000,
                    path_queue_size=10_000,
                    path_batch_size=256,
                    writer_flush_interval_sec=0.25,
                    worker_poll_interval_sec=0.01,
                ),
            )
            collector.start()
            try:
                on_samples = _measure_callback(
                    lambda: _observer_branch(collector, "000001", payload),
                    iterations=iterations,
                    warmup=warmup,
                )
            finally:
                collector.close(timeout_sec=30.0)
            runtime = collector.runtime_snapshot()
            on_summary = _latency_summary(on_samples)
            on_summary["collector_internal_p95_ms"] = (
                runtime.producer_callback_latency_p95_ms
            )
            on_summary["collector_internal_p99_ms"] = (
                runtime.producer_callback_latency_p99_ms
            )
            on_summary["queue_drop_count"] = float(
                runtime.observation_dropped_envelope_count
            )
            on_summary["worker_error_count"] = float(runtime.worker_error_count)
            on_runs.append(on_summary)

    internal_p95_max = max(row["collector_internal_p95_ms"] for row in on_runs)
    internal_p99_max = max(row["collector_internal_p99_ms"] for row in on_runs)
    p95_limit = max(1.0, _ceil_millis(internal_p95_max * 5.0))
    p99_limit = max(2.0, _ceil_millis(internal_p99_max * 5.0))
    generated_at = datetime.now(KST)
    return {
        "schema": CANARY_BASELINE_SCHEMA,
        "baseline_id": (
            f"main_server_synthetic_0b_{generated_at.strftime('%Y%m%dT%H%M%S%z')}"
        ),
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "host": {
            "hostname": platform.node(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "workload": {
            "input": "same_valid_stable_price_kiwoom_0b_snapshot",
            "observer_off_then_on": True,
            "path_capture_enabled_on": True,
            "discovery_enabled_on": False,
            "iterations_per_repeat": iterations,
            "warmup_per_repeat": warmup,
            "repeat_count": repeats,
        },
        "observer_off_runs": off_runs,
        "observer_on_runs": on_runs,
        "summary": {
            "observer_off_p95_ms_max": max(row["p95_ms"] for row in off_runs),
            "observer_off_p99_ms_max": max(row["p99_ms"] for row in off_runs),
            "observer_on_external_p95_ms_max": max(row["p95_ms"] for row in on_runs),
            "observer_on_external_p99_ms_max": max(row["p99_ms"] for row in on_runs),
            "observer_on_internal_p95_ms_max": internal_p95_max,
            "observer_on_internal_p99_ms_max": internal_p99_max,
            "queue_drop_count": int(sum(row["queue_drop_count"] for row in on_runs)),
            "worker_error_count": int(
                sum(row["worker_error_count"] for row in on_runs)
            ),
        },
        "frozen_limits": {
            "derivation": (
                "max(absolute_floor, five_times_max_observed_internal_percentile)"
            ),
            "minimum_callback_samples": 1_000,
            "producer_callback_latency_p95_max_ms": p95_limit,
            "producer_callback_latency_p99_max_ms": p99_limit,
            "snapshot_stale_after_sec": 30.0,
        },
        **CANARY_MONITOR_METRIC_CONTRACT,
    }


def _observer_branch(
    collector: ForwardObservationCollector | None,
    symbol: str,
    payload: dict[str, Any],
) -> None:
    if collector is not None:
        collector.observe_kiwoom_0b(symbol, payload, realtime_type="0B")


def _measure_callback(
    callback: Callable[[], None],
    *,
    iterations: int,
    warmup: int,
) -> tuple[float, ...]:
    for _ in range(warmup):
        callback()
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        callback()
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return tuple(samples)


def _latency_summary(samples: tuple[float, ...]) -> dict[str, float]:
    ordered = tuple(sorted(samples))
    return {
        "p50_ms": _percentile(ordered, 50),
        "p95_ms": _percentile(ordered, 95),
        "p99_ms": _percentile(ordered, 99),
        "max_ms": max(ordered, default=0.0),
        "mean_ms": statistics.fmean(ordered) if ordered else 0.0,
    }


def _percentile(ordered: tuple[float, ...], percentile: int) -> float:
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * percentile / 100.0
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return round(ordered[low], 6)
    weight = rank - low
    return round(ordered[low] * (1 - weight) + ordered[high] * weight, 6)


def _benchmark_snapshot(repeat_index: int) -> dict[str, Any]:
    received = datetime.now(KST).replace(microsecond=repeat_index * 1_000)
    return {
        "last_realtime_type_item": {"0B": "000001"},
        "last_realtime_type_effective_venue": {"0B": "KRX"},
        "last_trade_tick": {
            "exchange_time_raw": received.strftime("%H%M%S%f")[:9],
            "exchange_code_9081": "1",
            "received_at_ms": int(received.timestamp() * 1_000),
            "price": 10_000,
            "volume": 10,
            "best_bid": 9_990,
            "best_ask": 10_010,
            "quote_age_ms": 10.0,
            "aggressor_side": "SELL",
        },
    }


def _positive_int(value: Any) -> int | None:
    parsed = _nonnegative_int(value)
    return parsed if parsed is not None and parsed > 0 else None


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _positive_float(value: Any) -> float | None:
    parsed = _nonnegative_float(value)
    return parsed if parsed is not None and parsed > 0 else None


def _nonnegative_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _compact_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.6f}"


def _ceil_millis(value: float) -> float:
    return math.ceil(value * 1_000.0) / 1_000.0


def main() -> int:
    print(json.dumps(run_callback_latency_preflight(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
