"""Cost-aware source-only policy for risky rising-missed micro episodes.

The policy classifies opportunities and emits a hypothetical passive order plan.
It deliberately has no broker adapter, runtime switch, order owner, or sell owner.
Real-order promotion must go through the normal clean-baseline rolling evidence and
PREOPEN approval chain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.trading.order.tick_utils import (
    get_tick_size,
    move_price_by_ticks,
    move_price_down_by_bps,
    move_price_up_by_bps,
)

SCHEMA = "risky_micro_episode_source_candidate_v2"
POLICY_VERSION = "rising_missed_passive_micro_episode_source_only_v2"
PRIMARY_ENTRY_PROFILE = "bid_plus_one_ttl_3s"
TICK_CONTEXT_GAP_REASONS = frozenset(
    {
        "none",
        "direct_and_tp1_tick_context_missing",
        "tp1_signed_tick_sample_floor_not_met",
        "tp1_tick_source_untrusted_or_missing",
        "tp1_tick_context_age_missing",
        "tp1_tick_context_stale",
        "tp1_submit_context_freshness_unconfirmed",
        "tick_acceleration_and_window_span_missing",
        "tick_acceleration_missing",
        "tick_window_span_missing",
        "unclassified_tick_context_gap",
    }
)


@dataclass(frozen=True, slots=True)
class RiskyMicroEpisodeConfig:
    """Frozen research defaults; these values cannot affect live orders."""

    min_recheck_tick_acceleration: float = 0.70
    min_confirmed_tick_acceleration: float = 1.00
    max_tick_window_span_sec: float = 60.0
    max_quote_age_ms: float = 1_000.0
    max_passive_spread_bps: float = 80.0
    marketable_spread_bps: float = 15.0
    conservative_total_cost_bps: int = 23
    desired_net_profit_bps: int = 10
    adverse_limit_bps: int = 33
    passive_ttl_sec: int = 3
    max_hold_sec: int = 20
    proposed_per_symbol_daily_episode_cap: int = 1
    proposed_global_daily_episode_cap: int = 5

    def __post_init__(self) -> None:
        if (
            not 0
            < self.min_recheck_tick_acceleration
            < self.min_confirmed_tick_acceleration
        ):
            raise ValueError("invalid_tick_acceleration_bounds")
        if self.max_quote_age_ms <= 0:
            raise ValueError("max_quote_age_ms_must_be_positive")
        if self.max_tick_window_span_sec <= 0:
            raise ValueError("max_tick_window_span_sec_must_be_positive")
        if not 0 < self.marketable_spread_bps <= self.max_passive_spread_bps:
            raise ValueError("invalid_spread_bounds")
        if (
            min(
                self.conservative_total_cost_bps,
                self.desired_net_profit_bps,
                self.adverse_limit_bps,
                self.passive_ttl_sec,
                self.max_hold_sec,
                self.proposed_per_symbol_daily_episode_cap,
                self.proposed_global_daily_episode_cap,
            )
            <= 0
        ):
            raise ValueError("positive_episode_limits_required")


def _base_payload(
    config: RiskyMicroEpisodeConfig, *, source_stage: str
) -> dict[str, Any]:
    return {
        "risky_micro_episode_schema": SCHEMA,
        "risky_micro_episode_policy_version": POLICY_VERSION,
        "risky_micro_episode_source_stage": str(source_stage or "unknown"),
        "risky_micro_episode_metric_role": "source_candidate_classification",
        "risky_micro_episode_decision_authority": (
            "source_only_passive_episode_research_no_order_authority"
        ),
        "risky_micro_episode_window_policy": "same_candidate_fresh_bbo_source_projection",
        "risky_micro_episode_sample_floor": "not_applicable_source_candidate_projection",
        "risky_micro_episode_primary_decision_metric": "candidate_status_counts",
        "risky_micro_episode_source_quality_gate": (
            "rising_missed_lineage_fresh_executable_bbo_tick_context_and_non_adverse_micro"
        ),
        "risky_micro_episode_forbidden_uses": (
            "broker_order_submission|broker_order_cancel|automated_sell|"
            "normal_entry_guard_bypass|stale_quote_bypass|hard_safety_bypass|"
            "scale_in|residual_multi_leg|provider_or_bot_change|quantity_or_cap_change|"
            "live_promotion_from_daily_only_or_win_rate"
        ),
        "risky_micro_episode_runtime_effect": False,
        "risky_micro_episode_allowed_runtime_apply": False,
        "risky_micro_episode_actual_order_submitted": False,
        "risky_micro_episode_broker_order_forbidden": True,
        "risky_micro_episode_hard_safety_preserved": True,
        "risky_micro_episode_scale_in_allowed": False,
        "risky_micro_episode_residual_multi_leg_allowed": False,
        "risky_micro_episode_quantity_owner": (
            "position_sizing_dynamic_formula_then_existing_probe_first"
        ),
        "risky_micro_episode_quantity_is_tuning_axis": False,
        "risky_micro_episode_independent_episode_or_widget_owner": False,
        "risky_micro_episode_outcome_join_required": True,
        "risky_micro_episode_outcome_join_status": (
            "pending_executable_fill_and_3_10_20_30_second_path_consumer"
        ),
        "risky_micro_episode_entry_profile": PRIMARY_ENTRY_PROFILE,
        "risky_micro_episode_config": asdict(config),
    }


def evaluate_risky_micro_episode(
    *,
    rising_missed_lineage: bool,
    source_stage: str,
    source_block_reason: str,
    best_bid: int,
    best_ask: int,
    quote_age_ms: float | None,
    tick_acceleration_ratio: float | None,
    tick_window_span_sec: float | None,
    tick_context_gap_reason: str | None = None,
    positive_micro_support: bool,
    adverse_micro_detected: bool,
    large_sell_detected: bool,
    config: RiskyMicroEpisodeConfig | None = None,
) -> dict[str, Any]:
    """Classify a possible micro episode without creating order authority."""

    policy = config or RiskyMicroEpisodeConfig()
    payload = _base_payload(policy, source_stage=source_stage)
    bid = int(best_bid or 0)
    ask = int(best_ask or 0)
    bbo_valid = bid > 0 and ask >= bid
    quote_fresh = (
        quote_age_ms is not None and 0 <= float(quote_age_ms) <= policy.max_quote_age_ms
    )
    spread_bps = ((ask - bid) / bid) * 10_000.0 if bbo_valid else None
    spread_ticks = (
        max(0, int(round((ask - bid) / max(1, get_tick_size(bid)))))
        if bbo_valid
        else None
    )
    gross_target_bps = (
        policy.conservative_total_cost_bps + policy.desired_net_profit_bps
    )
    passive_entry_price = 0
    target_price = 0
    adverse_price = 0
    if bbo_valid:
        bid_plus_one = move_price_by_ticks(bid, 1)
        passive_entry_price = bid_plus_one if bid_plus_one < ask else bid
        target_price = move_price_up_by_bps(passive_entry_price, gross_target_bps)
        adverse_price = move_price_down_by_bps(
            passive_entry_price,
            policy.adverse_limit_bps,
        )

    status = "not_applicable"
    reason = "not_rising_missed_lineage"
    if rising_missed_lineage:
        if not bbo_valid:
            status = "source_quality_blocked"
            reason = "executable_bbo_missing_or_invalid"
        elif not quote_fresh:
            status = "source_quality_blocked"
            reason = "executable_quote_stale_or_age_missing"
        elif tick_acceleration_ratio is None or tick_window_span_sec is None:
            status = "source_quality_blocked"
            reason = "tick_context_missing"
        elif not 0 < float(tick_window_span_sec) < policy.max_tick_window_span_sec:
            status = "excluded_excessive_risk"
            reason = "tick_window_span_not_micro"
        elif large_sell_detected or adverse_micro_detected:
            status = "excluded_excessive_risk"
            reason = "adverse_micro_or_large_sell_detected"
        elif float(tick_acceleration_ratio) < policy.min_recheck_tick_acceleration:
            status = "excluded_excessive_risk"
            reason = "tick_acceleration_below_recheck_floor"
        elif spread_bps is not None and spread_bps > policy.max_passive_spread_bps:
            status = "excluded_uneconomic_spread"
            reason = "spread_exceeds_passive_economic_ceiling"
        elif not positive_micro_support:
            status = "recheck_required"
            reason = "positive_micro_support_not_confirmed"
        elif float(tick_acceleration_ratio) < policy.min_confirmed_tick_acceleration:
            status = "recheck_required"
            reason = "tick_acceleration_confirmation_pending"
        else:
            status = "source_only_candidate"
            reason = "fresh_passive_cost_aware_episode_candidate"

    if not bbo_valid:
        instrumentation_gap = "executable_bbo_missing"
    elif quote_age_ms is None:
        instrumentation_gap = "quote_age_missing"
    elif not quote_fresh:
        instrumentation_gap = "stale_quote"
    elif tick_acceleration_ratio is None or tick_window_span_sec is None:
        instrumentation_gap = "tick_context_missing"
    else:
        instrumentation_gap = "none"

    normalized_tick_gap_reason = str(tick_context_gap_reason or "").strip()
    if tick_acceleration_ratio is not None and tick_window_span_sec is not None:
        normalized_tick_gap_reason = "none"
    elif not normalized_tick_gap_reason:
        if tick_acceleration_ratio is None and tick_window_span_sec is None:
            normalized_tick_gap_reason = "tick_acceleration_and_window_span_missing"
        elif tick_acceleration_ratio is None:
            normalized_tick_gap_reason = "tick_acceleration_missing"
        else:
            normalized_tick_gap_reason = "tick_window_span_missing"
    if normalized_tick_gap_reason not in TICK_CONTEXT_GAP_REASONS:
        normalized_tick_gap_reason = "unclassified_tick_context_gap"

    return {
        **payload,
        "risky_micro_episode_status": status,
        "risky_micro_episode_reason": reason,
        "risky_micro_episode_source_block_reason": str(source_block_reason or "-"),
        "risky_micro_episode_rising_missed_lineage": bool(rising_missed_lineage),
        "risky_micro_episode_best_bid": bid,
        "risky_micro_episode_best_ask": ask,
        "risky_micro_episode_bbo_valid": bbo_valid,
        "risky_micro_episode_quote_age_ms": (
            round(float(quote_age_ms), 3) if quote_age_ms is not None else "-"
        ),
        "risky_micro_episode_quote_fresh": quote_fresh,
        "risky_micro_episode_quote_freshness_state": (
            "missing" if quote_age_ms is None else "fresh" if quote_fresh else "stale"
        ),
        "risky_micro_episode_bbo_state": "valid" if bbo_valid else "missing_or_invalid",
        "risky_micro_episode_tick_context_state": (
            "present"
            if tick_acceleration_ratio is not None and tick_window_span_sec is not None
            else "missing"
        ),
        "risky_micro_episode_tick_context_gap_reason": (normalized_tick_gap_reason),
        "risky_micro_episode_instrumentation_gap": instrumentation_gap,
        "risky_micro_episode_spread_bps": (
            round(spread_bps, 3) if spread_bps is not None else "-"
        ),
        "risky_micro_episode_spread_ticks": (
            spread_ticks if spread_ticks is not None else "-"
        ),
        "risky_micro_episode_tick_acceleration_ratio": (
            round(float(tick_acceleration_ratio), 6)
            if tick_acceleration_ratio is not None
            else "-"
        ),
        "risky_micro_episode_tick_window_span_sec": (
            round(float(tick_window_span_sec), 6)
            if tick_window_span_sec is not None
            else "-"
        ),
        "risky_micro_episode_positive_micro_support": bool(positive_micro_support),
        "risky_micro_episode_adverse_micro_detected": bool(adverse_micro_detected),
        "risky_micro_episode_large_sell_detected": bool(large_sell_detected),
        "risky_micro_episode_entry_style": "passive_limit_no_chase",
        "risky_micro_episode_entry_profile": PRIMARY_ENTRY_PROFILE,
        "risky_micro_episode_hypothetical_entry_price": passive_entry_price,
        "risky_micro_episode_hypothetical_target_price": target_price,
        "risky_micro_episode_hypothetical_adverse_price": adverse_price,
        "risky_micro_episode_conservative_total_cost_bps": (
            policy.conservative_total_cost_bps
        ),
        "risky_micro_episode_desired_net_profit_bps": policy.desired_net_profit_bps,
        "risky_micro_episode_gross_target_bps": gross_target_bps,
        "risky_micro_episode_adverse_limit_bps": policy.adverse_limit_bps,
        "risky_micro_episode_passive_ttl_sec": policy.passive_ttl_sec,
        "risky_micro_episode_max_hold_sec": policy.max_hold_sec,
        "risky_micro_episode_proposed_per_symbol_daily_cap": (
            policy.proposed_per_symbol_daily_episode_cap
        ),
        "risky_micro_episode_proposed_global_daily_cap": (
            policy.proposed_global_daily_episode_cap
        ),
        "risky_micro_episode_marketability": (
            "narrow_spread_but_source_only"
            if spread_bps is not None and spread_bps <= policy.marketable_spread_bps
            else "passive_only"
        ),
    }
