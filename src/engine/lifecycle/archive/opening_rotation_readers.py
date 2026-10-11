"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from dataclasses import asdict, dataclass, field


from datetime import datetime, time


from typing import Any


from src.engine.sniper_time import (
    is_scalping_buy_time_allowed,
    is_scalping_prewarm_time_allowed,
)


POSITION_TAG = "OPENING_ROTATION_1PCT"


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
class OpeningRotationEntryProfile:
    enabled: bool = True
    observe_start: time = time(9, 0)
    entry_start: time = time(9, 3)
    entry_end: time = time(11, 40)
    min_day_change_pct: float = 1.5
    max_day_change_pct: float = 5.0
    min_pullback_pct: float = 0.25
    max_pullback_pct: float = 1.0
    max_quote_age_ms: float = 1000.0
    max_tick_age_ms: float = 1000.0
    max_spread_ticks: int = 2
    max_spread_bp: float = 50.0
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
    min_confirmation_count: int = 2
    promotion_ttl_sec: int = 60
    buy_wait_sec: int = 10
    quantity: int = 1
    budget_ratio: float = 0.10
    mechanical_signal_strength: float = 0.80


@dataclass(frozen=True)
class OpeningRotationExitProfile:
    net_take_profit_floor_pct: float = 0.30
    slippage_budget_rate: float = 0.001
    holding_ai_trigger_pct: float = -0.5
    stagnation_sec: int = 300
    stagnation_max_profit_pct: float = 0.20
    max_hold_sec: int = 600
    ratchet_shadow_enabled: bool = True
    ratchet_max_ticks: int = 1


EntryConfig = OpeningRotationEntryProfile


ExitConfig = OpeningRotationExitProfile


def is_entry_time_allowed(now_dt: datetime, config: EntryConfig) -> bool:
    return bool(
        time(9, 0) <= now_dt.time() <= config.entry_end
        and now_dt.time() >= config.entry_start
        and is_scalping_buy_time_allowed(now_dt)
    )


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
    packet: dict[str, Any],
    config: EntryConfig,
    *,
    source_quality_ready: bool = True,
) -> tuple[dict[str, Any], tuple[tuple[bool, str], ...]]:
    """Expose downstream gate readiness before the pullback state is complete."""

    spread_bp = _number(packet.get("spread_bp"), 999.0)
    spread_ticks = _number(packet.get("spread_ticks"), 999.0)
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
    hard_checks = (
        (
            0.0 <= spread_bp <= config.max_spread_bp
            and 0.0 <= spread_ticks <= config.max_spread_ticks,
            "spread_too_wide",
        ),
        (buy_pressure >= config.min_buy_pressure_pct, "buy_pressure_below_min"),
        (trusted_ticks >= config.min_trusted_ticks, "trusted_tick_sample_below_min"),
        (wall_risk <= config.max_wall_risk_score, "wall_replenishment_risk"),
        (vi_risk <= config.max_vi_risk_score, "vi_proximity_risk"),
    )
    confirmations = (
        (tick_acceleration >= config.min_tick_acceleration, "tick_acceleration"),
        (tick_price_change >= config.min_tick_price_change_pct, "tick_price_change"),
        (volume_ratio >= config.min_volume_ratio_pct, "volume_reacceleration"),
        (
            bid_replenishment >= config.min_bid_replenishment_score,
            "bid_replenishment",
        ),
        (
            vwap_available
            and config.min_vwap_distance_bp
            <= vwap_distance
            <= config.max_vwap_distance_bp,
            "micro_vwap_distance",
        ),
    )
    confirmation_count = sum(1 for passed, _name in confirmations if passed)
    checks = hard_checks + (
        (
            confirmation_count >= config.min_confirmation_count,
            "confirmation_count_below_min",
        ),
    )
    failed_reasons = [reason for passed, reason in checks if not passed]
    preview_blockers = (
        failed_reasons if source_quality_ready else ["trusted_tick_context_unavailable"]
    )
    metrics = {
        "spread_bp": spread_bp,
        "spread_ticks": spread_ticks,
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
        "opening_rotation_confirmation_count": confirmation_count,
        "opening_rotation_confirmation_required": config.min_confirmation_count,
        "opening_rotation_confirmations": ",".join(
            name for passed, name in confirmations if passed
        )
        or "-",
        "opening_rotation_ask_sweep_diagnostic": ask_sweep,
        "opening_rotation_post_sweep_hold_diagnostic": post_sweep_hold,
        "opening_rotation_downstream_preview_evaluated": source_quality_ready,
        "opening_rotation_downstream_preview_source_quality": (
            "ready" if source_quality_ready else "trusted_tick_context_unavailable"
        ),
        "opening_rotation_downstream_preview_passed": (
            source_quality_ready and not failed_reasons
        ),
        "opening_rotation_downstream_preview_pass_count": (
            len(checks) - len(failed_reasons) if source_quality_ready else 0
        ),
        "opening_rotation_downstream_preview_total_count": len(checks),
        "opening_rotation_downstream_preview_first_blocker": (
            preview_blockers[0] if preview_blockers else "all_downstream_gates_ready"
        ),
        "opening_rotation_downstream_preview_blockers": (
            ",".join(preview_blockers) if preview_blockers else "-"
        ),
        "opening_rotation_downstream_preview_decision_authority": (
            "observation_only_no_pattern_or_submit_bypass"
        ),
        "opening_rotation_downstream_preview_metric_role": "diagnostic",
        "opening_rotation_downstream_preview_window_policy": (
            "same_symbol_same_day_opening_rotation_state"
        ),
        "opening_rotation_downstream_preview_sample_floor": (
            "one_fresh_quote_observation_trusted_tape_required_for_evaluated_true"
        ),
        "opening_rotation_downstream_preview_primary_decision_metric": (
            "first_blocker_after_source_quality"
        ),
        "opening_rotation_downstream_preview_source_quality_gate": (
            "fresh_quote_and_trusted_ws_aggressor_context"
        ),
        "opening_rotation_downstream_preview_forbidden_uses": (
            "standalone_buy,pattern_bypass,submit_safety_bypass,broker_guard_bypass,"
            "threshold_mutation,quantity_or_cap_change,provider_route_change"
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
    promotion_id: str = "",
    config: EntryConfig | None = None,
) -> dict[str, Any]:
    """Return a deterministic WATCH/BUY decision and the next state."""

    # A pullback belongs to the current scanner promotion, not to the symbol's
    # day-wide high.  Reusing ``intraday_high_price`` would let a later episode
    # inherit a peak formed before its promotion even though its state dict was
    # reset.  Keep the argument for compatibility with existing callers and
    # archived replay rows, but deliberately exclude it from live authority.
    del intraday_high_price
    config = config or EntryConfig()
    packet = feature_packet if isinstance(feature_packet, dict) else {}
    state = dict(previous_state or {})
    normalized_promotion_id = str(promotion_id or "").strip()
    state_promotion_id = str(state.get("promotion_id") or "").strip()
    promotion_started_epoch = _number(state.get("promotion_started_epoch"), 0.0)
    now_epoch = now_dt.timestamp()
    if not normalized_promotion_id:
        return _blocked("promotion_id_missing", {})
    if state_promotion_id != normalized_promotion_id or promotion_started_epoch <= 0:
        promotion_started_epoch = now_epoch
        state = {
            "promotion_id": normalized_promotion_id,
            "promotion_started_epoch": promotion_started_epoch,
        }
    promotion_age_sec = max(0.0, now_epoch - promotion_started_epoch)
    curr_price = int(_number(packet.get("curr_price"), 0.0))
    prior_peak = int(_number(state.get("peak_price"), 0.0))
    peak_price = max(curr_price, prior_peak)
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
        "promotion_id": normalized_promotion_id,
        "promotion_age_sec": round(promotion_age_sec, 3),
        "promotion_ttl_sec": config.promotion_ttl_sec,
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
    if promotion_age_sec > config.promotion_ttl_sec:
        state.update(
            {
                "phase": "DROP",
                "terminal_reason": "promotion_ttl_expired",
                "last_observed_at": now_dt.isoformat(),
                "last_observed_epoch": now_epoch,
            }
        )
        return _blocked("promotion_ttl_expired", state, **common)
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
    if not source_tokens:
        return _blocked("scanner_source_missing", state, **common)
    if not (config.min_day_change_pct <= day_change_pct <= config.max_day_change_pct):
        return _blocked("day_change_out_of_range", state, **common)
    if curr_price <= 0:
        return _blocked("invalid_current_price", state, **common)

    quote_stale = _boolean(packet.get("quote_stale"))
    quote_age_ms = _number(packet.get("quote_age_ms"), -1.0)
    quote_stale_threshold_ms = min(
        config.max_quote_age_ms,
        _number(packet.get("quote_stale_threshold_ms"), config.max_quote_age_ms),
    )
    tick_stale = _boolean(packet.get("tick_context_stale"))
    tick_age_ms = _number(packet.get("tick_latest_age_ms"), -1.0)
    pressure_usable = _boolean(packet.get("tick_aggressor_pressure_usable"))
    tick_quality = str(packet.get("tick_context_quality") or "").strip().lower()
    if quote_age_ms < 0:
        return _blocked("quote_freshness_unavailable", state, **common)
    if (
        quote_stale
        or quote_age_ms > quote_stale_threshold_ms
        or tick_stale
        or tick_age_ms < 0
        or tick_age_ms > config.max_tick_age_ms
    ):
        return _blocked("stale_market_context", state, **common)
    trusted_tick_context_ready = bool(
        tick_quality == "fresh_computed" and pressure_usable
    )
    micro_metrics, checks = _entry_micro_gate_preview(
        packet,
        config,
        source_quality_ready=trusted_tick_context_ready,
    )
    common.update(
        {
            "quote_age_ms": quote_age_ms,
            "quote_stale_threshold_ms": quote_stale_threshold_ms,
            "quote_stale": quote_stale,
            "tick_context_stale": tick_stale,
            "tick_context_quality": tick_quality,
            "tick_latest_age_ms": tick_age_ms,
            "tick_aggressor_pressure_usable": pressure_usable,
            "trusted_tick_prices": list(packet.get("trusted_tick_prices") or [])[:10],
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
            "last_observed_epoch": now_epoch,
            "promotion_id": normalized_promotion_id,
            "promotion_started_epoch": promotion_started_epoch,
        }
    )
    if not trusted_tick_context_ready:
        return _blocked("trusted_tick_context_unavailable", state, **common)
    if not is_entry_time_allowed(now_dt, config):
        state["phase"] = "COLLECTING"
        return _blocked("collecting_before_entry_window", state, **common)
    if not pullback_seen:
        return _blocked("pullback_not_observed", state, **common)
    if not (config.min_pullback_pct <= pullback_pct <= config.max_pullback_pct):
        return _blocked("pullback_out_of_range", state, **common)
    trusted_prices = [
        int(_number(value, 0.0))
        for value in (packet.get("trusted_tick_prices") or [])
        if int(_number(value, 0.0)) > 0
    ]
    if len(trusted_prices) < 2:
        return _blocked("trusted_tick_prices_below_min", state, **common)
    latest_trusted = trusted_prices[0]
    previous_trusted = trusted_prices[1]
    oldest_trusted = trusted_prices[-1]
    if latest_trusted < previous_trusted or latest_trusted <= oldest_trusted:
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
        "trusted_tick_latest_price": latest_trusted,
        "trusted_tick_previous_price": previous_trusted,
        "trusted_tick_oldest_price": oldest_trusted,
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
        "net_take_profit_floor_pct": config.net_take_profit_floor_pct,
        "holding_ai_trigger_pct": config.holding_ai_trigger_pct,
        "stagnation_sec": config.stagnation_sec,
        "max_hold_sec": config.max_hold_sec,
        "ai_score_hard_gate": False,
        "ai_score_decision_authority": "feature_only_not_evaluated",
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
    if profit_rate <= config.holding_ai_trigger_pct:
        return {
            **common,
            "should_exit": False,
            "holding_ai_handoff_required": True,
            "sell_reason_type": "",
            "exit_rule": "",
            "reason": "holding_ai_drawdown_trigger",
        }
    return {
        **common,
        "should_exit": False,
        "sell_reason_type": "",
        "exit_rule": "",
        "reason": "hold",
        "holding_ai_handoff_required": False,
    }
