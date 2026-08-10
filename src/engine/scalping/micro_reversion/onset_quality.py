"""Source-only shock-onset timing diagnostics from canonical P2 paths.

This module belongs to the micro-reversion research package because it labels
the detector onset and its future path.  It has no collector, discovery,
ranking, simulation, runtime, broker, or order dependency.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import math
from typing import Any, Iterable

from .p2_replay import P2ReplayPoint

ONSET_QUALITY_SCHEMA = "scalp_micro_reversion_onset_quality_v1"
ONSET_QUALITY_AUTHORITY = "shock_onset_timing_diagnostic_only"
ONSET_QUALITY_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_pattern_timing_diagnostic",
    "decision_authority": ONSET_QUALITY_AUTHORITY,
    "window_policy": (
        "post_decision_local_receive_5s_15s_30s_60s_180s_without_imputation"
    ),
    "sample_floor": "gate_b_collector_health_then_frozen_confirmation_economics",
    "primary_decision_metric": "additional_mae_bps_and_post_low_delay_ms",
    "source_quality_gate": (
        "v2_event_reference_and_monotonic_canonical_path_and_exact_"
        "decision_watermark"
    ),
    "forbidden_uses": (
        "real_data_policy_ranking_before_gate_b",
        "shock_onset_as_entry_or_bottom_confirmation",
        "missing_trade_or_trigger_basis_imputation",
        "sim_or_live_policy_selection",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}


class ShockTriggerBasis(StrEnum):
    ROBUST_RETURN = "ROBUST_RETURN"
    ROBUST_ACCELERATION = "ROBUST_ACCELERATION"
    ROBUST_RETURN_AND_ACCELERATION = "ROBUST_RETURN_AND_ACCELERATION"
    WARMUP_ABSOLUTE = "WARMUP_ABSOLUTE"
    UNKNOWN_RECONSTRUCTED = "UNKNOWN_RECONSTRUCTED"


@dataclass(frozen=True, slots=True)
class ShockOnsetContext:
    shock_event_id: str
    symbol: str
    venue: str
    session_bucket: str
    sequence_epoch: int
    shock_horizon_ms: int
    event_exchange_timestamp_ms: int
    event_local_receive_timestamp_ms: int
    event_source_sequence: int
    reference_price: float
    shock_price: float
    shock_return_bps: float
    trigger_trade_qty: int | None
    trigger_aggressor_side: str | None
    trigger_basis: ShockTriggerBasis
    return_robust_z: float | None = None
    acceleration_robust_z: float | None = None

    def __post_init__(self) -> None:
        if not self.shock_event_id:
            raise ValueError("shock_event_id is required")
        if not self.symbol or not self.venue or not self.session_bucket:
            raise ValueError("symbol, venue, and session_bucket are required")
        if self.sequence_epoch <= 0:
            raise ValueError("sequence_epoch must be positive")
        if self.shock_horizon_ms <= 0:
            raise ValueError("shock_horizon_ms must be positive")
        if (
            self.event_exchange_timestamp_ms <= 0
            or self.event_local_receive_timestamp_ms < self.event_exchange_timestamp_ms
            or self.event_source_sequence <= 0
        ):
            raise ValueError("shock event watermark is invalid")
        if (
            not math.isfinite(self.reference_price)
            or not math.isfinite(self.shock_price)
            or self.reference_price <= 0
            or self.shock_price <= 0
        ):
            raise ValueError("shock reference and event prices must be positive")
        if not math.isfinite(self.shock_return_bps) or self.shock_return_bps > 0:
            raise ValueError("shock_return_bps must not be positive")
        if self.trigger_trade_qty is not None and (
            isinstance(self.trigger_trade_qty, bool)
            or not isinstance(self.trigger_trade_qty, int)
            or self.trigger_trade_qty < 0
        ):
            raise ValueError("trigger_trade_qty must be a nonnegative integer")
        if self.trigger_aggressor_side not in {
            None,
            "BUY",
            "SELL",
            "UNKNOWN",
        }:
            raise ValueError("trigger_aggressor_side is invalid")
        for field_name in ("return_robust_z", "acceleration_robust_z"):
            value = getattr(self, field_name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite when present")
        object.__setattr__(self, "trigger_basis", ShockTriggerBasis(self.trigger_basis))

    @property
    def trigger_trade_notional(self) -> float | None:
        if self.trigger_trade_qty is None:
            return None
        return self.shock_price * self.trigger_trade_qty


@dataclass(frozen=True, slots=True)
class OnsetHorizonQuality:
    horizon_ms: int
    mature: bool
    post_trade_count: int
    additional_mae_bps: float | None
    post_low_delay_ms: int | None
    terminal_trade_return_bps: float | None
    max_reclaim_from_post_low_bps: float | None


@dataclass(frozen=True, slots=True)
class ShockOnsetQualityReport:
    context: ShockOnsetContext
    horizons: tuple[OnsetHorizonQuality, ...]
    schema: str = ONSET_QUALITY_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context"]["trigger_basis"] = self.context.trigger_basis.value
        payload["context"][
            "trigger_trade_notional"
        ] = self.context.trigger_trade_notional
        payload.update(
            {
                "selection_authority": False,
                "sim_effect": False,
                "runtime_effect": False,
                "trading_decision_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                **ONSET_QUALITY_METRIC_CONTRACT,
            }
        )
        return payload


def reconstruct_shock_onset_context(
    points: Iterable[P2ReplayPoint],
    *,
    reference: dict[str, Any],
    reference_max_lag_ms: int = 2_000,
) -> ShockOnsetContext:
    """Reconstruct auditable onset prices without claiming robust trigger basis."""

    if reference.get("schema") != "scalp_micro_reversion_path_event_reference_v2":
        raise ValueError("onset reconstruction requires a v2 event reference")
    if (
        reference.get("actual_order_submitted") is not False
        or reference.get("broker_order_forbidden") is not True
        or reference.get("trading_runtime_effect") is not False
    ):
        raise ValueError("event reference authority contract is invalid")
    if reference_max_lag_ms < 0:
        raise ValueError("reference_max_lag_ms must not be negative")

    path = tuple(points)
    _validate_path(path)
    detected_local_ms = int(reference.get("event_detected_at_ms") or 0)
    horizon_ms = int(reference.get("shock_horizon_ms") or 0)
    if detected_local_ms <= 0 or horizon_ms <= 0:
        raise ValueError("event reference detector watermark is invalid")

    detector_clock_by_sequence: dict[int, int] = {}
    previous_detector_clock_ms = 0
    for point in path:
        detector_clock_ms = max(
            point.local_receive_timestamp_ms,
            previous_detector_clock_ms + 1,
        )
        detector_clock_by_sequence[point.source_sequence] = detector_clock_ms
        previous_detector_clock_ms = detector_clock_ms
    trigger_candidates = tuple(
        point
        for point in path
        if point.trade_price is not None
        and detector_clock_by_sequence[point.source_sequence] == detected_local_ms
    )
    if not trigger_candidates:
        raise ValueError("canonical path does not contain the shock trigger trade")
    if len(trigger_candidates) != 1:
        raise ValueError("shock trigger trade reconstruction is ambiguous")
    trigger = trigger_candidates[0]

    reference_target_ms = detected_local_ms - horizon_ms
    reference_candidates = tuple(
        point
        for point in path
        if point.trade_price is not None
        and point.source_sequence < trigger.source_sequence
        and detector_clock_by_sequence[point.source_sequence] <= reference_target_ms
    )
    if not reference_candidates:
        raise ValueError("canonical path does not contain the shock reference trade")
    reference_point = max(
        reference_candidates,
        key=lambda point: (
            detector_clock_by_sequence[point.source_sequence],
            point.source_sequence,
        ),
    )
    if (
        reference_target_ms
        - detector_clock_by_sequence[reference_point.source_sequence]
        > reference_max_lag_ms
    ):
        raise ValueError("shock reference trade exceeds the maximum lag")

    assert trigger.trade_price is not None
    assert reference_point.trade_price is not None
    shock_return_bps = (
        trigger.trade_price / reference_point.trade_price - 1.0
    ) * 10_000.0
    return ShockOnsetContext(
        shock_event_id=str(reference.get("shock_event_id") or "").strip(),
        symbol=str(reference.get("symbol") or "").strip(),
        venue=str(reference.get("venue") or "").strip(),
        session_bucket=str(reference.get("session_bucket") or "").strip(),
        sequence_epoch=int(reference.get("sequence_epoch") or 0),
        shock_horizon_ms=horizon_ms,
        event_exchange_timestamp_ms=trigger.exchange_timestamp_ms,
        event_local_receive_timestamp_ms=trigger.local_receive_timestamp_ms,
        event_source_sequence=trigger.source_sequence,
        reference_price=reference_point.trade_price,
        shock_price=trigger.trade_price,
        shock_return_bps=round(shock_return_bps, 6),
        trigger_trade_qty=trigger.trade_qty,
        trigger_aggressor_side=trigger.aggressor_side,
        trigger_basis=ShockTriggerBasis.UNKNOWN_RECONSTRUCTED,
    )


def analyze_shock_onset(
    points: Iterable[P2ReplayPoint],
    *,
    context: ShockOnsetContext,
    horizons_ms: tuple[int, ...] = (5_000, 15_000, 30_000, 60_000, 180_000),
) -> ShockOnsetQualityReport:
    """Measure continuation and reclaim after onset without choosing a policy."""

    if not horizons_ms or tuple(sorted(set(horizons_ms))) != horizons_ms:
        raise ValueError("horizons_ms must be positive, sorted, and unique")
    if any(horizon <= 0 for horizon in horizons_ms):
        raise ValueError("horizons_ms must be positive, sorted, and unique")
    path = tuple(points)
    _validate_path(path)
    post = tuple(
        point
        for point in path
        if (
            point.local_receive_timestamp_ms,
            point.source_sequence,
        )
        > (
            context.event_local_receive_timestamp_ms,
            context.event_source_sequence,
        )
    )
    horizons = tuple(
        _analyze_horizon(post, context=context, horizon_ms=horizon_ms)
        for horizon_ms in horizons_ms
    )
    return ShockOnsetQualityReport(context=context, horizons=horizons)


def _analyze_horizon(
    post: tuple[P2ReplayPoint, ...],
    *,
    context: ShockOnsetContext,
    horizon_ms: int,
) -> OnsetHorizonQuality:
    deadline_ms = context.event_local_receive_timestamp_ms + horizon_ms
    mature = any(point.local_receive_timestamp_ms >= deadline_ms for point in post)
    trades = tuple(
        point
        for point in post
        if point.local_receive_timestamp_ms <= deadline_ms
        and point.trade_price is not None
    )
    if not trades:
        return OnsetHorizonQuality(
            horizon_ms=horizon_ms,
            mature=mature,
            post_trade_count=0,
            additional_mae_bps=None,
            post_low_delay_ms=None,
            terminal_trade_return_bps=None,
            max_reclaim_from_post_low_bps=None,
        )

    low_price = context.shock_price
    low_at_ms = context.event_local_receive_timestamp_ms
    low_index = -1
    for index, point in enumerate(trades):
        assert point.trade_price is not None
        point_low = point.low or point.trade_price
        if point_low < low_price:
            low_price = point_low
            low_at_ms = point.local_receive_timestamp_ms
            low_index = index
    reclaim_prices = [low_price]
    reclaim_prices.extend(
        point.trade_price
        for point in trades[low_index + 1 :]
        if point.trade_price is not None
    )
    terminal_price = trades[-1].trade_price
    assert terminal_price is not None
    return OnsetHorizonQuality(
        horizon_ms=horizon_ms,
        mature=mature,
        post_trade_count=len(trades),
        additional_mae_bps=round((low_price / context.shock_price - 1.0) * 10_000.0, 6),
        post_low_delay_ms=low_at_ms - context.event_local_receive_timestamp_ms,
        terminal_trade_return_bps=round(
            (terminal_price / context.shock_price - 1.0) * 10_000.0, 6
        ),
        max_reclaim_from_post_low_bps=round(
            (max(reclaim_prices) / low_price - 1.0) * 10_000.0, 6
        ),
    )


def _validate_path(path: tuple[P2ReplayPoint, ...]) -> None:
    previous: P2ReplayPoint | None = None
    for point in path:
        if previous is not None and (
            point.exchange_timestamp_ms < previous.exchange_timestamp_ms
            or point.local_receive_timestamp_ms < previous.local_receive_timestamp_ms
            or point.source_sequence <= previous.source_sequence
        ):
            raise ValueError(
                "path must increase by exchange/local timestamp and source sequence"
            )
        previous = point
