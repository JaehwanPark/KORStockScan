"""Explicit inputs for adaptive exits. These objects never grant order authority."""

from __future__ import annotations

from dataclasses import dataclass
import math


def finite(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def positive_int(value: object) -> bool:
    return type(value) is int and value > 0


@dataclass(frozen=True)
class TrailPolicy:
    fast_sec: float
    min_progress: float
    gap_ticks: int
    transition_buffer_ticks: int
    minimum_net_cushion_pct: float


@dataclass(frozen=True)
class ExitPolicy:
    policy_hash: str
    scope_key: str
    mode: str
    soft_sec: float
    extension_sec: float
    minimum_progress: float
    minimum_improvement_bps: float
    # Explicit None means there is NO maximum holding-time guarantee.
    hard_wall_sec: float | None
    loss_budget_pct: float
    max_quote_age_ms: int
    max_observation_gap_ms: int
    trail: TrailPolicy | None

    def __post_init__(self) -> None:
        if not all(
            isinstance(v, str) and v for v in (self.policy_hash, self.scope_key)
        ) or self.mode not in ("time_progress_exit", "fast_partial_trailing"):
            raise ValueError("invalid_policy_identity_or_mode")
        positive = (self.soft_sec, self.extension_sec, self.loss_budget_pct)
        if not all(finite(v) and v > 0 for v in positive):
            raise ValueError("invalid_policy_time_or_loss_bound")
        if not finite(self.minimum_progress) or not 0 <= self.minimum_progress <= 1:
            raise ValueError("invalid_progress_bound")
        if not finite(self.minimum_improvement_bps) or self.minimum_improvement_bps < 0:
            raise ValueError("invalid_improvement_bound")
        if self.hard_wall_sec is not None and (
            not finite(self.hard_wall_sec) or self.hard_wall_sec < self.soft_sec
        ):
            raise ValueError("invalid_hard_wall_bound")
        if not all(
            positive_int(v)
            for v in (self.max_quote_age_ms, self.max_observation_gap_ms)
        ):
            raise ValueError("invalid_source_bounds")
        if self.mode == "time_progress_exit" and self.trail is not None:
            raise ValueError("combined_mode_not_supported")
        if self.mode == "fast_partial_trailing":
            t = self.trail
            if not isinstance(t, TrailPolicy) or not (
                finite(t.fast_sec)
                and 0 < t.fast_sec <= self.soft_sec
                and finite(t.min_progress)
                and 0 < t.min_progress < 1
                and positive_int(t.gap_ticks)
                and positive_int(t.transition_buffer_ticks)
                and finite(t.minimum_net_cushion_pct)
                and t.minimum_net_cushion_pct > 0
            ):
                raise ValueError("invalid_trail_bounds")


@dataclass(frozen=True)
class Position:
    owner_id: str
    scope_key: str
    episode_id: str
    lot_id: str
    position_epoch: str
    first_fill_at_ms: int
    open_qty: int
    entry_price: float
    original_target: float
    round_trip_cost_pct: float
    cost_contract_hash: str
    tick_size: float


@dataclass(frozen=True)
class Snapshot:
    observed_at_ms: int
    quote_at_ms: int
    source_epoch: str
    sequence: int
    source_hash: str
    scope_key: str
    position_epoch: str
    best_ask: float
    # Best bid first, prices strictly descending. A VWAP is not a limit price.
    bid_levels: tuple[tuple[float, int], ...]
    supportive: bool | None
    improvement_bps: float | None


@dataclass(frozen=True)
class Clock:
    now_ms: int
    verified_halt_ms: int


@dataclass(frozen=True)
class DecisionState:
    policy_hash: str
    position_epoch: str
    first_fill_at_ms: int
    open_qty: int
    extensions: int = 0
    extension_until_active_ms: int | None = None
    extension_granted_at_active_ms: int | None = None
    last_observed_at_ms: int | None = None
    source_epoch: str | None = None
    sequence: int | None = None
    trail_active: bool = False
    high_water: float | None = None
    stop_price: float | None = None


@dataclass(frozen=True)
class ExitDecision:
    action: str
    reason: str
    policy_hash: str
    source_hash: str
    lot_id: str
    quantity: int
    executable_bid: float | None = None
    worst_bid: float | None = None
    progress: float | None = None
    net_return_pct: float | None = None
    next_active_deadline_ms: int | None = None
    high_water: float | None = None
    stop_price: float | None = None
