"""Bounded source-only path journal for smoothing alternatives.

This module owns observation state only.  It never changes a holding action,
submits an order, or grants runtime-apply authority.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from copy import deepcopy
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "smoothing_source_only_path_journal_v1"
HORIZONS_SEC = (10, 20, 40, 60, 90)
MAX_OBSERVATION_LAG_SEC = 2.0
MAX_ACTIVE_ARMS = 8
STATE_KEY = "smoothing_source_only_path_journals"
PATH_QUALITY_CONTRACT_VERSION = "fresh_observation_gap_v2"
NOT_AVAILABLE_PRICE = "not_available"
NOT_AVAILABLE_PROFIT_RATE = "not_available"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _present(value: Any) -> bool:
    return str(value or "").strip() not in {"", "-", "None", "null"}


def _price_quality_usable(value: Any) -> bool:
    return str(value or "").strip().lower() in {"ok", "warning", "single_source"}


def _price_observation_fields(
    *,
    effective_price: int,
    effective_profit_rate: float,
    effective_price_source: str,
    effective_price_quality: str,
    missing_reason: str,
    prefix: str = "",
) -> dict[str, Any]:
    """Represent missing executable prices without fabricating zero-return EV."""

    observed = effective_price > 0
    name = f"{prefix}_" if prefix else ""
    return {
        f"{name}effective_price": (
            int(effective_price) if observed else NOT_AVAILABLE_PRICE
        ),
        f"{name}effective_profit_rate": (
            round(float(effective_profit_rate), 6)
            if observed
            else NOT_AVAILABLE_PROFIT_RATE
        ),
        f"{name}effective_price_source": (
            str(effective_price_source or "unknown")
            if observed
            else f"not_available:{missing_reason}"
        ),
        f"{name}effective_price_quality": (
            str(effective_price_quality or "unknown") if observed else "missing"
        ),
        f"{name}effective_price_observation_state": (
            "observed" if observed else f"not_available:{missing_reason}"
        ),
    }


def _contract_fields() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "metric_role": "sim_probe_ev",
        "decision_authority": "source_only_counterfactual_no_runtime_change",
        "window_policy": "same_exact_position_trace_snapshot_10_20_40_60_90s",
        "sample_floor": "soft_stop_10_ofi_20_exact_paths",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "exact_position_trace_snapshot_and_fresh_effective_price",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "live_action_change|stop_or_trailing_delay|hard_or_emergency_bypass|"
            "threshold_apply|provider_route_change|quantity_or_cap_change|bot_restart"
        ),
    }


def _event(stage: str, arm: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {
        "stage": stage,
        "fields": {
            **_contract_fields(),
            "journal_arm_id": arm["arm_id"],
            "journal_family": arm["family"],
            "journal_position_key": arm["position_key"],
            "journal_trace_id": arm["trace_id"],
            "journal_snapshot_id": arm["snapshot_id"],
            "exact_lineage_status": arm["exact_lineage_status"],
            "journal_alternative_action": arm["alternative_action"],
            "journal_control_action": arm["control_action"],
            "journal_started_at_epoch": arm["started_at"],
            "path_quality_contract_version": arm.get(
                "path_quality_contract_version", "legacy_any_invalid_sample_v1"
            ),
            **fields,
        },
    }


def arm_source_only_path(
    state: dict[str, Any] | None,
    *,
    family: str,
    position_key: str,
    trace_id: str | None,
    snapshot_id: str | None,
    alternative_action: str,
    control_action: str,
    now_ts: float,
    effective_price: int,
    effective_profit_rate: float,
    reference_buy_price: int,
    effective_price_source: str = "unknown",
    effective_price_quality: str = "unknown",
    runtime_family_enabled: bool,
    alternative_executed: bool,
    source_reason: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Arm one exact alternative path, deduplicated by its source snapshot."""

    normalized = deepcopy(state) if isinstance(state, dict) else {}
    arms = normalized.get("arms") if isinstance(normalized.get("arms"), dict) else {}
    arms = dict(arms)
    position = str(position_key or "").strip()
    if not _present(position) or effective_price <= 0 or reference_buy_price <= 0:
        return {"schema_version": SCHEMA_VERSION, "arms": arms}, None

    alternative = str(alternative_action).upper()
    for active_arm in arms.values():
        if (
            active_arm.get("family") == str(family)
            and active_arm.get("position_key") == position
            and active_arm.get("alternative_action") == alternative
        ):
            return {"schema_version": SCHEMA_VERSION, "arms": arms}, None

    source_trace_present = _present(trace_id)
    source_snapshot_present = _present(snapshot_id)
    exact_lineage_status = (
        "source_exact"
        if source_trace_present and source_snapshot_present
        else "journal_native_only"
    )
    trace = str(trace_id or "").strip()
    if not source_trace_present:
        trace = f"journal-trace:{family}:{position}:{alternative}"
    snapshot = str(snapshot_id or "").strip()
    if not source_snapshot_present:
        snapshot = (
            f"journal-snapshot:{family}:{position}:{alternative}:"
            f"{int(float(now_ts) * 1000)}:{int(effective_price)}"
        )
    dedupe_key = "|".join(
        (
            str(family),
            position,
            trace,
            snapshot,
            alternative,
        )
    )
    for arm in arms.values():
        if arm.get("dedupe_key") == dedupe_key:
            return {"schema_version": SCHEMA_VERSION, "arms": arms}, None

    arm_id = f"sj-{uuid4().hex}"
    anchor_price_usable = _price_quality_usable(effective_price_quality)
    arm = {
        "arm_id": arm_id,
        "dedupe_key": dedupe_key,
        "family": str(family),
        "position_key": position,
        "trace_id": trace,
        "snapshot_id": snapshot,
        "exact_lineage_status": exact_lineage_status,
        "alternative_action": alternative,
        "control_action": str(control_action).upper(),
        "started_at": float(now_ts),
        "anchor_effective_price": int(effective_price),
        "anchor_effective_profit_rate": float(effective_profit_rate),
        "reference_buy_price": int(reference_buy_price or 0),
        "anchor_effective_price_source": str(effective_price_source or "unknown"),
        "anchor_effective_price_quality": str(effective_price_quality or "unknown"),
        "runtime_family_enabled": bool(runtime_family_enabled),
        "alternative_executed": bool(alternative_executed),
        "source_reason": str(source_reason or "-")[:240],
        "emitted_horizons": [],
        "path_mfe_profit_rate": (
            float(effective_profit_rate) if anchor_price_usable else None
        ),
        "path_mae_profit_rate": (
            float(effective_profit_rate) if anchor_price_usable else None
        ),
        "path_price_quality_valid_sample_count": int(anchor_price_usable),
        "path_price_quality_invalid_sample_count": int(not anchor_price_usable),
        "path_quality_contract_version": PATH_QUALITY_CONTRACT_VERSION,
        "path_last_valid_observed_at_epoch": (
            float(now_ts) if anchor_price_usable else None
        ),
        "path_max_valid_observation_gap_sec": (0.0 if anchor_price_usable else None),
        "path_max_allowed_observation_gap_sec": MAX_OBSERVATION_LAG_SEC,
    }
    arms[arm_id] = arm
    if len(arms) > MAX_ACTIVE_ARMS:
        oldest = sorted(
            arms.values(), key=lambda item: float(item.get("started_at") or 0.0)
        )[: len(arms) - MAX_ACTIVE_ARMS]
        for item in oldest:
            arms.pop(str(item.get("arm_id") or ""), None)
    return {"schema_version": SCHEMA_VERSION, "arms": arms}, _event(
        "smoothing_source_only_path_armed",
        arm,
        anchor_effective_price=int(effective_price),
        anchor_effective_profit_rate=round(float(effective_profit_rate), 6),
        reference_buy_price=int(reference_buy_price or 0),
        anchor_effective_price_source=arm["anchor_effective_price_source"],
        anchor_effective_price_quality=arm["anchor_effective_price_quality"],
        runtime_family_enabled=bool(runtime_family_enabled),
        alternative_executed=bool(alternative_executed),
        source_reason=arm["source_reason"],
        horizon_seconds=list(HORIZONS_SEC),
    )


def observe_source_only_paths(
    state: dict[str, Any] | None,
    *,
    position_key: str,
    now_ts: float,
    effective_price: int,
    effective_profit_rate: float,
    effective_price_source: str = "unknown",
    effective_price_quality: str = "unknown",
    hard_breach: bool,
    emergency_breach: bool,
    observation_phase: str = "holding",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Advance active arms and emit each exact horizon at most once."""

    normalized = deepcopy(state) if isinstance(state, dict) else {}
    source_arms = (
        normalized.get("arms") if isinstance(normalized.get("arms"), dict) else {}
    )
    remaining: dict[str, Any] = {}
    events: list[dict[str, Any]] = []
    for arm_id, raw_arm in source_arms.items():
        arm = dict(raw_arm) if isinstance(raw_arm, dict) else {}
        if arm.get("position_key") != position_key:
            events.append(
                _event(
                    "smoothing_source_only_path_closed",
                    arm,
                    close_reason="position_lineage_changed",
                    observation_phase=str(observation_phase or "unknown"),
                    **_price_observation_fields(
                        effective_price=0,
                        effective_profit_rate=0.0,
                        effective_price_source="not_applicable",
                        effective_price_quality="not_applicable",
                        missing_reason="position_lineage_changed",
                        prefix="terminal",
                    ),
                    path_mfe_profit_rate=arm.get("path_mfe_profit_rate"),
                    path_mae_profit_rate=arm.get("path_mae_profit_rate"),
                    path_price_quality_valid_sample_count=int(
                        arm.get("path_price_quality_valid_sample_count") or 0
                    ),
                    path_price_quality_invalid_sample_count=int(
                        arm.get("path_price_quality_invalid_sample_count") or 0
                    ),
                    path_max_valid_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_valid_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC + 1.0,
                        ),
                        3,
                    ),
                    path_max_allowed_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_allowed_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC,
                        ),
                        3,
                    ),
                    hard_breach=False,
                    emergency_breach=False,
                )
            )
            continue
        elapsed = max(0.0, float(now_ts) - _safe_float(arm.get("started_at")))
        if effective_price > 0:
            if _price_quality_usable(effective_price_quality):
                previous_valid_at = _safe_float(
                    arm.get("path_last_valid_observed_at_epoch"),
                    _safe_float(arm.get("started_at")),
                )
                valid_observation_gap_sec = max(0.0, float(now_ts) - previous_valid_at)
                arm["path_max_valid_observation_gap_sec"] = max(
                    valid_observation_gap_sec,
                    _safe_float(arm.get("path_max_valid_observation_gap_sec")),
                )
                arm["path_last_valid_observed_at_epoch"] = float(now_ts)
                arm["path_mfe_profit_rate"] = max(
                    float(effective_profit_rate),
                    _safe_float(arm.get("path_mfe_profit_rate"), effective_profit_rate),
                )
                arm["path_mae_profit_rate"] = min(
                    float(effective_profit_rate),
                    _safe_float(arm.get("path_mae_profit_rate"), effective_profit_rate),
                )
                arm["path_price_quality_valid_sample_count"] = (
                    int(arm.get("path_price_quality_valid_sample_count") or 0) + 1
                )
            else:
                arm["path_price_quality_invalid_sample_count"] = (
                    int(arm.get("path_price_quality_invalid_sample_count") or 0) + 1
                )
        emitted = {int(value) for value in arm.get("emitted_horizons") or []}
        valid_price_sample_count = int(
            arm.get("path_price_quality_valid_sample_count") or 0
        )
        invalid_price_sample_count = int(
            arm.get("path_price_quality_invalid_sample_count") or 0
        )
        for horizon in HORIZONS_SEC:
            if horizon in emitted or elapsed < horizon:
                continue
            lag = elapsed - horizon
            status = (
                "observed"
                if effective_price > 0 and lag <= MAX_OBSERVATION_LAG_SEC
                else "expired_observation_gap"
            )
            events.append(
                _event(
                    "smoothing_source_only_path_horizon",
                    arm,
                    horizon_sec=horizon,
                    observation_elapsed_sec=round(elapsed, 3),
                    observation_lag_sec=round(lag, 3),
                    horizon_status=status,
                    observation_phase=str(observation_phase or "unknown"),
                    **_price_observation_fields(
                        effective_price=effective_price,
                        effective_profit_rate=effective_profit_rate,
                        effective_price_source=effective_price_source,
                        effective_price_quality=effective_price_quality,
                        missing_reason=status,
                    ),
                    path_mfe_profit_rate=(
                        round(_safe_float(arm.get("path_mfe_profit_rate")), 6)
                        if valid_price_sample_count
                        else None
                    ),
                    path_mae_profit_rate=(
                        round(_safe_float(arm.get("path_mae_profit_rate")), 6)
                        if valid_price_sample_count
                        else None
                    ),
                    path_price_quality_valid_sample_count=valid_price_sample_count,
                    path_price_quality_invalid_sample_count=(
                        invalid_price_sample_count
                    ),
                    path_max_valid_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_valid_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC + 1.0,
                        ),
                        3,
                    ),
                    path_max_allowed_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_allowed_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC,
                        ),
                        3,
                    ),
                    hard_breach=bool(hard_breach),
                    emergency_breach=bool(emergency_breach),
                )
            )
            emitted.add(horizon)
        arm["emitted_horizons"] = sorted(emitted)
        close_reason = ""
        if emergency_breach:
            close_reason = "emergency_breach"
        elif hard_breach:
            close_reason = "hard_breach"
        elif all(horizon in emitted for horizon in HORIZONS_SEC):
            close_reason = "horizons_complete"
        if close_reason:
            events.append(
                _event(
                    "smoothing_source_only_path_closed",
                    arm,
                    close_reason=close_reason,
                    observation_phase=str(observation_phase or "unknown"),
                    **_price_observation_fields(
                        effective_price=effective_price,
                        effective_profit_rate=effective_profit_rate,
                        effective_price_source=effective_price_source,
                        effective_price_quality=effective_price_quality,
                        missing_reason=close_reason,
                        prefix="terminal",
                    ),
                    path_mfe_profit_rate=(
                        round(_safe_float(arm.get("path_mfe_profit_rate")), 6)
                        if valid_price_sample_count
                        else None
                    ),
                    path_mae_profit_rate=(
                        round(_safe_float(arm.get("path_mae_profit_rate")), 6)
                        if valid_price_sample_count
                        else None
                    ),
                    path_price_quality_valid_sample_count=valid_price_sample_count,
                    path_price_quality_invalid_sample_count=(
                        invalid_price_sample_count
                    ),
                    path_max_valid_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_valid_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC + 1.0,
                        ),
                        3,
                    ),
                    path_max_allowed_observation_gap_sec=round(
                        _safe_float(
                            arm.get("path_max_allowed_observation_gap_sec"),
                            MAX_OBSERVATION_LAG_SEC,
                        ),
                        3,
                    ),
                    hard_breach=bool(hard_breach),
                    emergency_breach=bool(emergency_breach),
                )
            )
        else:
            remaining[str(arm_id)] = arm
    return {"schema_version": SCHEMA_VERSION, "arms": remaining}, events


class SmoothingSourceOnlyPathObserver:
    """Run the injected source-only journal observer on an independent cadence."""

    def __init__(
        self,
        *,
        observer: Callable[..., Any],
        interval_sec: float = 0.25,
        error_handler: Callable[[str], None] | None = None,
    ) -> None:
        self._observer = observer
        self._interval_sec = max(0.05, float(interval_sec))
        self._error_handler = error_handler
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> bool:
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="smoothing-source-only-path-observer",
        )
        self._thread.start()
        return True

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, float(timeout)))

    def run_once(self, *, now_ts: float | None = None) -> Any:
        observed_at = float(time.time() if now_ts is None else now_ts)
        try:
            return self._observer(now_ts=observed_at)
        except Exception as exc:
            if self._error_handler is not None:
                self._error_handler(str(exc))
            return None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            started = time.monotonic()
            self.run_once()
            elapsed = max(0.0, time.monotonic() - started)
            self._stop_event.wait(max(0.0, self._interval_sec - elapsed))
