"""Deterministic live policy for early-session 1% rotation trades.

The policy deliberately has no AI score input.  It only evaluates scanner
provenance, fresh market microstructure, a bounded pullback, and reacceleration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

POSITION_TAG = "OPENING_ROTATION_1PCT"
WATCH_POSITION_TAG = "SCANNER"
STATE_KEY = "opening_rotation_1pct_state"
WINDOW_VERSION = "opening_rotation_0910_1500_v1"
ENTRY_TIME_BUCKET_MINUTES = 30

PRIMARY_SOURCES = frozenset(
    {
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
    }
)
EXCLUDED_ENTRY_OWNER_SOURCES = frozenset({"LOW_REBOUND_RISING_MISSED"})


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_source_signature(value: Any) -> frozenset[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        values = value
    else:
        values = str(value or "").replace("|", ",").split(",")
    return frozenset(str(item).strip().upper() for item in values if str(item).strip())


@dataclass(frozen=True)
class EntryConfig:
    enabled: bool = True
    observe_start: time = time(9, 1)
    entry_start: time = time(9, 10)
    entry_end: time = time(15, 0)
    min_day_change_pct: float = 1.5
    max_day_change_pct: float = 8.0
    min_pullback_pct: float = 0.25
    max_pullback_pct: float = 1.0
    max_spread_bp: float = 15.0
    min_buy_pressure_pct: float = 58.0
    min_trusted_ticks: int = 5
    min_tick_acceleration: float = 1.15
    min_tick_price_change_pct: float = 0.03
    min_volume_ratio_pct: float = 80.0
    min_vwap_distance_bp: float = -5.0
    max_vwap_distance_bp: float = 60.0
    min_ask_sweep_score: float = 65.0
    min_post_sweep_hold_score: float = 60.0
    min_bid_replenishment_score: float = 55.0
    max_wall_risk_score: float = 69.0
    max_vi_risk_score: float = 69.0
    budget_ratio: float = 0.10
    mechanical_signal_strength: float = 0.80


@dataclass(frozen=True)
class ExitConfig:
    take_profit_pct: float = 1.0
    stop_loss_pct: float = -0.5
    stagnation_sec: int = 300
    stagnation_max_profit_pct: float = 0.20
    max_hold_sec: int = 600


def entry_window_version(config: EntryConfig | None = None) -> str:
    """Return a stable cohort version for the effective entry window."""

    config = config or EntryConfig()
    if config.entry_start == time(9, 10) and config.entry_end == time(15, 0):
        return WINDOW_VERSION
    return (
        "opening_rotation_"
        f"{config.entry_start.strftime('%H%M')}_"
        f"{config.entry_end.strftime('%H%M')}_custom"
    )


def entry_time_bucket(
    value: datetime | time,
    config: EntryConfig | None = None,
) -> str:
    """Map an in-window entry to its clock-aligned 30-minute cohort.

    The inclusive end boundary belongs to the final bucket so a fill stamped
    exactly at 15:00 is not reported as an out-of-window trade.
    """

    config = config or EntryConfig()
    value_time = value.time() if isinstance(value, datetime) else value
    if value_time < config.entry_start or value_time > config.entry_end:
        return "outside_entry_window"

    minute_of_day = (value_time.hour * 60) + value_time.minute
    end_minute = (config.entry_end.hour * 60) + config.entry_end.minute
    if value_time == config.entry_end:
        minute_of_day = max(0, end_minute - 1)
    bucket_start = (
        minute_of_day // ENTRY_TIME_BUCKET_MINUTES
    ) * ENTRY_TIME_BUCKET_MINUTES
    bucket_end = bucket_start + ENTRY_TIME_BUCKET_MINUTES
    return (
        f"{bucket_start // 60:02d}:{bucket_start % 60:02d}-"
        f"{bucket_end // 60:02d}:{bucket_end % 60:02d}"
    )


def entry_time_bucket_labels(config: EntryConfig | None = None) -> tuple[str, ...]:
    """Return every clock-aligned cohort intersecting the entry window."""

    config = config or EntryConfig()
    start_minute = (config.entry_start.hour * 60) + config.entry_start.minute
    end_minute = (config.entry_end.hour * 60) + config.entry_end.minute
    bucket_start = (
        start_minute // ENTRY_TIME_BUCKET_MINUTES
    ) * ENTRY_TIME_BUCKET_MINUTES
    labels: list[str] = []
    while bucket_start < end_minute:
        bucket_end = bucket_start + ENTRY_TIME_BUCKET_MINUTES
        labels.append(
            f"{bucket_start // 60:02d}:{bucket_start % 60:02d}-"
            f"{bucket_end // 60:02d}:{bucket_end % 60:02d}"
        )
        bucket_start = bucket_end
    return tuple(labels)


def is_strategy_position(position_tag: Any) -> bool:
    return str(position_tag or "").strip().upper() == POSITION_TAG


def is_watch_source_scope(
    *,
    position_tag: Any,
    source_signature: Any,
    now_dt: datetime,
    config: EntryConfig,
) -> bool:
    """Return the source/time scope before a live day-change value is available.

    Scanner upstream skips can happen before a usable WS snapshot reaches the
    strategy.  Keeping this predicate separate lets those gaps be attributed
    without pretending that a source-scoped row passed the full entry screen.
    """

    if not config.enabled:
        return False
    normalized_tag = str(position_tag or "").strip().upper()
    if normalized_tag not in {WATCH_POSITION_TAG, POSITION_TAG}:
        return False
    if now_dt.time() < config.observe_start or now_dt.time() > config.entry_end:
        return False
    if normalized_tag == POSITION_TAG:
        return True
    source_tokens = parse_source_signature(source_signature)
    if source_tokens & EXCLUDED_ENTRY_OWNER_SOURCES:
        return False
    return bool(source_tokens & PRIMARY_SOURCES)


def is_watch_candidate(
    *,
    position_tag: Any,
    source_signature: Any,
    day_change_pct: float,
    now_dt: datetime,
    config: EntryConfig,
) -> bool:
    if not is_watch_source_scope(
        position_tag=position_tag,
        source_signature=source_signature,
        now_dt=now_dt,
        config=config,
    ):
        return False
    if not (
        config.min_day_change_pct <= float(day_change_pct) <= config.max_day_change_pct
    ):
        return False
    return True


def _blocked(reason: str, state: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {
        "in_scope": True,
        "qualified": False,
        "reason": reason,
        "state": state,
        "position_tag": POSITION_TAG,
        "ai_score_hard_gate": False,
        "ai_score_decision_authority": "feature_only_not_evaluated",
        **fields,
    }


def _entry_micro_gate_preview(
    packet: dict[str, Any], config: EntryConfig
) -> tuple[dict[str, Any], tuple[tuple[bool, str], ...]]:
    """Expose downstream gate readiness before the pullback state is complete."""

    spread_bp = _number(packet.get("spread_bp"), 999.0)
    buy_pressure = _number(packet.get("buy_pressure_10t"), 0.0)
    trusted_ticks = int(_number(packet.get("tick_aggressor_trusted_count"), 0.0))
    tick_acceleration = _number(packet.get("tick_acceleration_ratio"), 0.0)
    tick_price_change = _number(packet.get("price_change_10t_pct"), 0.0)
    volume_ratio = _number(packet.get("volume_ratio_pct"), 0.0)
    vwap_available = _boolean(packet.get("micro_vwap_available"))
    vwap_distance = _number(packet.get("curr_vs_micro_vwap_bp"), -999.0)
    ask_sweep = _number(packet.get("microstructure_reaction_ask_sweep_score"), 0.0)
    post_sweep_hold = _number(
        packet.get("microstructure_reaction_post_sweep_hold_score"), 0.0
    )
    bid_replenishment = _number(
        packet.get("microstructure_reaction_bid_replenishment_score"), 0.0
    )
    wall_risk = _number(
        packet.get("microstructure_reaction_wall_replenishment_risk_score"), 100.0
    )
    vi_risk = _number(packet.get("microstructure_reaction_vi_proximity_risk"), 100.0)
    checks = (
        (0.0 < spread_bp <= config.max_spread_bp, "spread_too_wide"),
        (buy_pressure >= config.min_buy_pressure_pct, "buy_pressure_below_min"),
        (trusted_ticks >= config.min_trusted_ticks, "trusted_tick_sample_below_min"),
        (
            tick_acceleration >= config.min_tick_acceleration,
            "tick_acceleration_below_min",
        ),
        (
            tick_price_change >= config.min_tick_price_change_pct,
            "tick_price_change_below_min",
        ),
        (
            volume_ratio >= config.min_volume_ratio_pct,
            "volume_reacceleration_below_min",
        ),
        (vwap_available, "micro_vwap_unavailable"),
        (
            config.min_vwap_distance_bp <= vwap_distance <= config.max_vwap_distance_bp,
            "micro_vwap_distance_out_of_range",
        ),
        (ask_sweep >= config.min_ask_sweep_score, "ask_sweep_below_min"),
        (
            post_sweep_hold >= config.min_post_sweep_hold_score,
            "post_sweep_hold_below_min",
        ),
        (
            bid_replenishment >= config.min_bid_replenishment_score,
            "bid_replenishment_below_min",
        ),
        (wall_risk <= config.max_wall_risk_score, "wall_replenishment_risk"),
        (vi_risk <= config.max_vi_risk_score, "vi_proximity_risk"),
    )
    failed_reasons = [reason for passed, reason in checks if not passed]
    metrics = {
        "spread_bp": spread_bp,
        "buy_pressure_10t": buy_pressure,
        "tick_aggressor_trusted_count": trusted_ticks,
        "tick_acceleration_ratio": tick_acceleration,
        "price_change_10t_pct": tick_price_change,
        "volume_ratio_pct": volume_ratio,
        "micro_vwap_available": vwap_available,
        "curr_vs_micro_vwap_bp": vwap_distance,
        "microstructure_reaction_ask_sweep_score": ask_sweep,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment,
        "microstructure_reaction_wall_replenishment_risk_score": wall_risk,
        "microstructure_reaction_vi_proximity_risk": vi_risk,
        "opening_rotation_downstream_preview_evaluated": True,
        "opening_rotation_downstream_preview_passed": not failed_reasons,
        "opening_rotation_downstream_preview_pass_count": (
            len(checks) - len(failed_reasons)
        ),
        "opening_rotation_downstream_preview_total_count": len(checks),
        "opening_rotation_downstream_preview_first_blocker": (
            failed_reasons[0] if failed_reasons else "all_downstream_gates_ready"
        ),
        "opening_rotation_downstream_preview_blockers": (
            ",".join(failed_reasons) if failed_reasons else "-"
        ),
        "opening_rotation_downstream_preview_decision_authority": (
            "observation_only_no_pattern_or_submit_bypass"
        ),
    }
    return metrics, checks


def evaluate_entry(
    *,
    previous_state: dict[str, Any] | None,
    feature_packet: dict[str, Any] | None,
    source_signature: Any,
    day_change_pct: float,
    intraday_high_price: Any,
    now_dt: datetime,
    config: EntryConfig | None = None,
) -> dict[str, Any]:
    """Return a deterministic WATCH/BUY decision and the next state."""

    config = config or EntryConfig()
    packet = feature_packet if isinstance(feature_packet, dict) else {}
    state = dict(previous_state or {})
    curr_price = int(_number(packet.get("curr_price"), 0.0))
    prior_peak = int(_number(state.get("peak_price"), 0.0))
    external_high = int(_number(intraday_high_price, 0.0))
    peak_price = max(curr_price, prior_peak, external_high)
    previous_price = int(_number(state.get("last_price"), curr_price))
    pullback_pct = (
        ((peak_price - curr_price) / peak_price) * 100.0 if peak_price > 0 else 0.0
    )
    common = {
        "curr_price": curr_price,
        "peak_price": peak_price,
        "previous_price": previous_price,
        "pullback_pct": round(pullback_pct, 4),
        "source_signature": ",".join(sorted(parse_source_signature(source_signature))),
        "day_change_pct": round(float(day_change_pct), 4),
        **{
            key: value
            for key, value in packet.items()
            if str(key).startswith("market_data_")
            or str(key).startswith("opening_rotation_freshness_")
            or key
            in {
                "tick_latest_age_ms",
                "tick_accel_source",
                "tick_aggressor_source_counts",
                "tick_aggressor_quality_counts",
            }
        },
    }
    if not config.enabled:
        return {
            "in_scope": False,
            "qualified": False,
            "reason": "disabled",
            "state": state,
        }
    if now_dt.time() < config.observe_start:
        return {
            "in_scope": False,
            "qualified": False,
            "reason": "before_observation_window",
            "state": state,
        }
    if now_dt.time() > config.entry_end:
        return _blocked("entry_window_closed", state, **common)
    source_tokens = parse_source_signature(source_signature)
    if source_tokens & EXCLUDED_ENTRY_OWNER_SOURCES:
        return _blocked("entry_owner_rising_missed_scout", state, **common)
    if not (source_tokens & PRIMARY_SOURCES):
        return _blocked("primary_rising_source_missing", state, **common)
    if not (config.min_day_change_pct <= day_change_pct <= config.max_day_change_pct):
        return _blocked("day_change_out_of_range", state, **common)
    if curr_price <= 0:
        return _blocked("invalid_current_price", state, **common)

    quote_stale = _boolean(packet.get("quote_stale"))
    quote_age_ms = _number(packet.get("quote_age_ms"), -1.0)
    quote_stale_threshold_ms = _number(packet.get("quote_stale_threshold_ms"), 3000.0)
    tick_stale = _boolean(packet.get("tick_context_stale"))
    pressure_usable = _boolean(packet.get("tick_aggressor_pressure_usable"))
    tick_quality = str(packet.get("tick_context_quality") or "").strip().lower()
    if quote_age_ms < 0:
        return _blocked("quote_freshness_unavailable", state, **common)
    if quote_stale or quote_age_ms > quote_stale_threshold_ms or tick_stale:
        return _blocked("stale_market_context", state, **common)
    if tick_quality != "fresh_computed" or not pressure_usable:
        return _blocked("trusted_tick_context_unavailable", state, **common)

    micro_metrics, checks = _entry_micro_gate_preview(packet, config)
    common.update(
        {
            "quote_age_ms": quote_age_ms,
            "quote_stale_threshold_ms": quote_stale_threshold_ms,
            "quote_stale": quote_stale,
            "tick_context_stale": tick_stale,
            "tick_context_quality": tick_quality,
            "tick_aggressor_pressure_usable": pressure_usable,
            **micro_metrics,
        }
    )

    pullback_seen = bool(state.get("pullback_seen")) or (
        config.min_pullback_pct <= pullback_pct <= config.max_pullback_pct
    )
    state.update(
        {
            "phase": "PULLBACK_OBSERVED" if pullback_seen else "WAIT_PULLBACK",
            "peak_price": peak_price,
            "last_price": curr_price,
            "pullback_pct": round(pullback_pct, 4),
            "pullback_seen": pullback_seen,
            "last_observed_at": now_dt.isoformat(),
        }
    )
    if now_dt.time() < config.entry_start:
        state["phase"] = "COLLECTING"
        return _blocked("collecting_before_entry_window", state, **common)
    if not pullback_seen:
        return _blocked("pullback_not_observed", state, **common)
    if not (config.min_pullback_pct <= pullback_pct <= config.max_pullback_pct):
        return _blocked("pullback_out_of_range", state, **common)
    if curr_price <= previous_price:
        return _blocked("reacceleration_not_observed", state, **common)

    for passed, reason in checks:
        if not passed:
            return _blocked(reason, state, **common)

    state.update(
        {
            "phase": "QUALIFIED",
            "qualified_at": now_dt.isoformat(),
            "qualified_price": curr_price,
        }
    )
    return {
        "in_scope": True,
        "qualified": True,
        "reason": "pullback_reacceleration_confirmed",
        "state": state,
        "position_tag": POSITION_TAG,
        "budget_ratio": config.budget_ratio,
        "mechanical_signal_strength": config.mechanical_signal_strength,
        "ai_score_hard_gate": False,
        "ai_score_decision_authority": "feature_only_not_evaluated",
        **common,
    }


def evaluate_exit(
    *,
    profit_rate: float,
    held_sec: int,
    config: ExitConfig | None = None,
) -> dict[str, Any]:
    """Evaluate cost-aware exit thresholds without AI inputs."""

    config = config or ExitConfig()
    profit_rate = float(profit_rate)
    held_sec = max(0, int(held_sec))
    common = {
        "profit_rate": round(profit_rate, 6),
        "held_sec": held_sec,
        "take_profit_pct": config.take_profit_pct,
        "stop_loss_pct": config.stop_loss_pct,
        "stagnation_sec": config.stagnation_sec,
        "max_hold_sec": config.max_hold_sec,
        "ai_score_hard_gate": False,
        "ai_score_decision_authority": "feature_only_not_evaluated",
    }
    if profit_rate >= config.take_profit_pct:
        return {
            **common,
            "should_exit": True,
            "sell_reason_type": "PROFIT",
            "exit_rule": "opening_rotation_1pct_take_profit",
            "reason": "net_take_profit_reached",
        }
    if profit_rate <= config.stop_loss_pct:
        return {
            **common,
            "should_exit": True,
            "sell_reason_type": "LOSS",
            "exit_rule": "opening_rotation_tight_stop",
            "reason": "tight_stop_reached",
        }
    if held_sec >= config.max_hold_sec:
        return {
            **common,
            "should_exit": True,
            "sell_reason_type": "TIMEOUT",
            "exit_rule": "opening_rotation_max_hold_exit",
            "reason": "maximum_hold_time_reached",
        }
    if (
        held_sec >= config.stagnation_sec
        and profit_rate <= config.stagnation_max_profit_pct
    ):
        return {
            **common,
            "should_exit": True,
            "sell_reason_type": "TIMEOUT",
            "exit_rule": "opening_rotation_stagnation_exit",
            "reason": "rotation_stagnation_timeout",
        }
    return {
        **common,
        "should_exit": False,
        "sell_reason_type": "",
        "exit_rule": "",
        "reason": "hold",
    }
