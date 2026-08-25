"""Source-only fixed-price ask-liquidity depletion diagnostics.

The feature measures how quickly liquidity at the shock-event best ask and its
retained top-of-book price ladder disappears before the later decision
snapshot. Every comparison stays on the exact symbol, venue, session, sequence
epoch, and shock-anchor ask prices. It does not expose a runtime hook, select a
policy, or infer a broker fill.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import math
from typing import Any, Iterable, Mapping

from .contracts import normalize_symbol, normalize_venue, registration_item_identity
from .depth_join import validate_depth_row
from .path_journal import (
    MARKET_STREAM_CONTRACT_ID,
    MARKET_STREAM_SCHEMA,
    validate_market_stream_path_provenance,
)

ASK_DEPLETION_SCHEMA = "scalp_micro_reversion_ask_depletion_v2"
ASK_DEPLETION_AUTHORITY = "source_only_feature_ablation_no_runtime_authority"
DEFAULT_HORIZONS_MS = (500, 1_000, 3_000, 5_000, 10_000)
DEFAULT_TOP_DEPTH_LEVELS = (3, 5)
ASK_DEPLETION_METRIC_CONTRACT = {
    "metric_role": "microstructure_feature_observation",
    "decision_authority": ASK_DEPLETION_AUTHORITY,
    "window_policy": (
        "past_only_same_symbol_venue_session_sequence_epoch_fixed_shock_anchor_"
        "ask_prices_strict_cross_stream_ms_order_at_500_1000_3000_5000_10000ms"
    ),
    "sample_floor": (
        "five_trading_days_20_common_parents_10_symbols_before_provider_ablation"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "latest_nonfuture_anchor_and_fresh_continuous_0d_and_complete_0b_"
        "within_exact_scope_without_fixed_price_imputation"
    ),
    "forbidden_uses": (
        "standalone_buy_wait_drop_or_exit_decision",
        "broker_order_submission_or_cancel",
        "automated_sell",
        "touch_or_depth_as_real_fill",
        "cross_symbol_venue_session_or_sequence_epoch_join",
        "cross_price_quantity_comparison",
        "missing_depth_trade_or_quantity_imputation",
        "cancellation_claim_without_order_identity",
        "runtime_or_preopen_env_mutation",
        "threshold_provider_model_prompt_bot_quantity_or_cap_mutation",
        "hard_safety_or_broker_guard_bypass",
        "real_execution_quality_or_live_promotion_approval",
    ),
}

STATUS_ELIGIBLE = "eligible_source_only_feature_ablation"
STATUS_DATA_WAIT = "data_wait"
STATUS_SOURCE_GAP = "source_gap"


@dataclass(frozen=True, slots=True)
class AskDepletionContext:
    """Exact event watermark and source-completeness contract."""

    event_id: str
    anchor_role: str
    symbol: str
    venue: str
    session_bucket: str
    sequence_epoch: int
    anchor_event_local_receive_timestamp_ms: int
    event_market_source_sequence: int
    observed_through_local_receive_timestamp_ms: int
    depth_source_complete: bool
    market_source_complete: bool

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str)
            for value in (
                self.event_id,
                self.anchor_role,
                self.symbol,
                self.venue,
                self.session_bucket,
            )
        ):
            raise ValueError("ask depletion context scope must use native strings")
        symbol = normalize_symbol(self.symbol)
        venue = normalize_venue(self.venue)
        session_bucket = str(self.session_bucket or "").strip().upper()
        if (
            not isinstance(self.event_id, str)
            or not self.event_id.strip()
            or self.event_id.strip() != self.event_id
            or self.anchor_role != "shock_event"
            or not symbol
            or venue == "UNKNOWN"
            or not session_bucket
        ):
            raise ValueError("ask depletion context scope is required")
        if (
            isinstance(self.sequence_epoch, bool)
            or not isinstance(self.sequence_epoch, int)
            or self.sequence_epoch <= 0
        ):
            raise ValueError("ask depletion sequence_epoch must be positive")
        if (
            isinstance(self.anchor_event_local_receive_timestamp_ms, bool)
            or not isinstance(self.anchor_event_local_receive_timestamp_ms, int)
            or isinstance(self.event_market_source_sequence, bool)
            or not isinstance(self.event_market_source_sequence, int)
            or isinstance(self.observed_through_local_receive_timestamp_ms, bool)
            or not isinstance(self.observed_through_local_receive_timestamp_ms, int)
            or self.anchor_event_local_receive_timestamp_ms <= 0
            or self.event_market_source_sequence <= 0
            or self.observed_through_local_receive_timestamp_ms
            < self.anchor_event_local_receive_timestamp_ms
        ):
            raise ValueError("ask depletion event watermark is invalid")
        if not isinstance(self.depth_source_complete, bool) or not isinstance(
            self.market_source_complete, bool
        ):
            raise ValueError("ask depletion source completeness must be boolean")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "session_bucket", session_bucket)

    @property
    def scope(self) -> tuple[str, str, str, int]:
        return (
            self.symbol,
            self.venue,
            self.session_bucket,
            self.sequence_epoch,
        )


@dataclass(frozen=True, slots=True)
class FixedTopDepthDepletion:
    retained_level_count: int
    anchor_price_count: int
    initial_qty: int | None
    endpoint_qty: int | None
    minimum_qty: int | None
    max_depletion_qty: int | None
    max_depletion_ratio: float | None


@dataclass(frozen=True, slots=True)
class AskDepletionHorizon:
    horizon_ms: int
    mature: bool
    source_quality_status: str
    eligible_for_feature_ablation: bool
    source_gap_reasons: tuple[str, ...]
    depth_endpoint_age_ms: float | None
    depth_observation_count: int
    anchor_best_ask: float | None
    endpoint_best_ask: float | None
    initial_anchor_ask_qty: int | None
    endpoint_anchor_ask_qty: int | None
    minimum_anchor_ask_qty: int | None
    max_best_ask_depletion_qty: int | None
    max_best_ask_depletion_ratio: float | None
    best_ask_depletion_velocity_qty_per_sec: float | None
    price_level_cleared: bool | None
    first_price_level_clear_delay_ms: int | None
    downward_reprice_observed: bool | None
    aggressive_buy_qty_before_max_depletion: int | None
    aggressive_buy_trade_backed_ratio: float | None
    unexplained_or_cancel_like_depletion_qty: int | None
    unexplained_or_cancel_like_depletion_ratio: float | None
    max_refill_qty: int | None
    refill_ratio: float | None
    refill_half_life_ms: int | None
    top_depth: tuple[FixedTopDepthDepletion, ...]


@dataclass(frozen=True, slots=True)
class AskDepletionReport:
    context: AskDepletionContext
    anchor_source_sequence: int | None
    anchor_depth_age_ms: float | None
    anchor_source_quality_status: str
    source_quality_status: str
    source_gap_reasons: tuple[str, ...]
    ignored_cross_scope_depth_row_count: int
    ignored_cross_scope_market_row_count: int
    horizons: tuple[AskDepletionHorizon, ...]
    schema: str = ASK_DEPLETION_SCHEMA

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "selection_authority": False,
                "sim_effect": False,
                "runtime_effect": False,
                "trading_runtime_effect": False,
                "trading_decision_effect": False,
                "provider_effect": False,
                "threshold_effect": False,
                "quantity_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                **ASK_DEPLETION_METRIC_CONTRACT,
            }
        )
        return payload


def build_ask_depletion_report(
    *,
    context: AskDepletionContext,
    anchor_depth: Mapping[str, Any] | None,
    depth_rows: Iterable[Mapping[str, Any]],
    market_rows: Iterable[Mapping[str, Any]],
    horizons_ms: tuple[int, ...] = DEFAULT_HORIZONS_MS,
    top_depth_levels: tuple[int, ...] = DEFAULT_TOP_DEPTH_LEVELS,
    max_depth_age_ms: int = 1_000,
) -> AskDepletionReport:
    """Build one causal, source-only ask-depletion feature report.

    ``anchor_depth`` must be the latest 0D snapshot strictly before the
    shock-event millisecond. ``market_rows`` means the continuous canonical 0B
    rows, not only BUY prints, because sequence continuity is part of the
    attribution gate. Missing, stale, or cross-stream same-millisecond evidence
    is returned as an explicit source gap and never imputed.
    """

    _validate_configuration(
        horizons_ms=horizons_ms,
        top_depth_levels=top_depth_levels,
        max_depth_age_ms=max_depth_age_ms,
    )
    depth_payloads = tuple(dict(row) for row in depth_rows)
    market_payloads = tuple(dict(row) for row in market_rows)
    scoped_depth: list[dict[str, Any]] = []
    scoped_market: list[dict[str, Any]] = []
    ignored_depth_count = 0
    ignored_market_count = 0
    for row in depth_payloads:
        if _scope(row) != context.scope:
            ignored_depth_count += 1
            continue
        validate_depth_row(row)
        scoped_depth.append(row)
    for row in market_payloads:
        if _scope(row) != context.scope:
            ignored_market_count += 1
            continue
        _validate_market_row(row)
        scoped_market.append(row)
    same_scope_depth = tuple(scoped_depth)
    same_scope_market = tuple(scoped_market)

    if anchor_depth is None:
        return _missing_anchor_report(
            context=context,
            horizons_ms=horizons_ms,
            reason="anchor_depth_missing",
            ignored_depth_count=ignored_depth_count,
            ignored_market_count=ignored_market_count,
        )
    anchor = dict(anchor_depth)
    validate_depth_row(anchor)
    if _scope(anchor) != context.scope:
        raise ValueError("ask depletion anchor scope conflicts with event context")

    anchor_event_us = context.anchor_event_local_receive_timestamp_ms * 1_000
    observed_through_us = context.observed_through_local_receive_timestamp_ms * 1_000
    anchor_us = _timestamp_us(anchor.get("local_receive_timestamp"))
    anchor_sequence = int(anchor["source_sequence"])
    anchor_age_ms = (anchor_event_us - anchor_us) / 1_000.0
    anchor_reasons: list[str] = []
    if anchor_us >= anchor_event_us:
        anchor_reasons.append("anchor_depth_not_strictly_before_shock")
    elif anchor_age_ms > max_depth_age_ms:
        anchor_reasons.append("anchor_depth_is_stale")
    if not context.depth_source_complete:
        anchor_reasons.append("depth_source_incomplete")
    later_nonfuture = tuple(
        row
        for row in same_scope_depth
        if _depth_sort_key(row) > _depth_sort_key(anchor)
        and _timestamp_us(row.get("local_receive_timestamp")) < anchor_event_us
    )
    if later_nonfuture:
        anchor_reasons.append("anchor_is_not_latest_nonfuture_depth")

    same_scope_depth = _deduplicate_explicit_anchor(
        anchor=anchor,
        rows=same_scope_depth,
    )
    _validate_unique_sequences((anchor, *same_scope_depth), source_name="depth")
    _validate_unique_sequences(same_scope_market, source_name="market")
    sorted_depth = tuple(sorted(same_scope_depth, key=_depth_sort_key))
    sorted_market = tuple(sorted(same_scope_market, key=_market_sort_key))

    if anchor_reasons:
        horizons = tuple(
            _empty_horizon(
                horizon_ms=horizon_ms,
                mature=observed_through_us >= anchor_event_us + horizon_ms * 1_000,
                reasons=tuple(anchor_reasons),
                anchor_best_ask=float(anchor["best_ask"]),
            )
            for horizon_ms in horizons_ms
        )
        return AskDepletionReport(
            context=context,
            anchor_source_sequence=anchor_sequence,
            anchor_depth_age_ms=round(anchor_age_ms, 6),
            anchor_source_quality_status=STATUS_SOURCE_GAP,
            source_quality_status=STATUS_SOURCE_GAP,
            source_gap_reasons=tuple(sorted(set(anchor_reasons))),
            ignored_cross_scope_depth_row_count=ignored_depth_count,
            ignored_cross_scope_market_row_count=ignored_market_count,
            horizons=horizons,
        )

    horizons = tuple(
        _build_horizon(
            context=context,
            anchor=anchor,
            depth_rows=sorted_depth,
            market_rows=sorted_market,
            anchor_event_us=anchor_event_us,
            observed_through_us=observed_through_us,
            horizon_ms=horizon_ms,
            top_depth_levels=top_depth_levels,
            max_depth_age_ms=max_depth_age_ms,
        )
        for horizon_ms in horizons_ms
    )
    statuses = {row.source_quality_status for row in horizons}
    if statuses == {STATUS_ELIGIBLE}:
        report_status = STATUS_ELIGIBLE
    elif STATUS_ELIGIBLE in statuses:
        report_status = "partial"
    elif statuses == {STATUS_DATA_WAIT}:
        report_status = STATUS_DATA_WAIT
    else:
        report_status = STATUS_SOURCE_GAP
    report_reasons = tuple(
        sorted({reason for row in horizons for reason in row.source_gap_reasons})
    )
    return AskDepletionReport(
        context=context,
        anchor_source_sequence=anchor_sequence,
        anchor_depth_age_ms=round(anchor_age_ms, 6),
        anchor_source_quality_status=STATUS_ELIGIBLE,
        source_quality_status=report_status,
        source_gap_reasons=report_reasons,
        ignored_cross_scope_depth_row_count=ignored_depth_count,
        ignored_cross_scope_market_row_count=ignored_market_count,
        horizons=horizons,
    )


def _build_horizon(
    *,
    context: AskDepletionContext,
    anchor: dict[str, Any],
    depth_rows: tuple[dict[str, Any], ...],
    market_rows: tuple[dict[str, Any], ...],
    anchor_event_us: int,
    observed_through_us: int,
    horizon_ms: int,
    top_depth_levels: tuple[int, ...],
    max_depth_age_ms: int,
) -> AskDepletionHorizon:
    horizon_end_us = anchor_event_us + horizon_ms * 1_000
    anchor_best_ask = float(anchor["best_ask"])
    if observed_through_us < horizon_end_us:
        return _empty_horizon(
            horizon_ms=horizon_ms,
            mature=False,
            reasons=("horizon_not_observed_through",),
            anchor_best_ask=anchor_best_ask,
            status=STATUS_DATA_WAIT,
        )

    anchor_key = _depth_sort_key(anchor)
    same_millisecond_depth = tuple(
        row
        for row in depth_rows
        if _depth_sort_key(row) > anchor_key
        and _timestamp_us(row.get("local_receive_timestamp")) == anchor_event_us
    )
    samples = (anchor,) + tuple(
        row
        for row in depth_rows
        if _depth_sort_key(row) > anchor_key
        and anchor_event_us
        < _timestamp_us(row.get("local_receive_timestamp"))
        <= horizon_end_us
    )
    endpoint = samples[-1]
    endpoint_us = _timestamp_us(endpoint.get("local_receive_timestamp"))
    endpoint_age_ms = (horizon_end_us - endpoint_us) / 1_000.0
    reasons: list[str] = []
    if same_millisecond_depth:
        reasons.append("depth_order_ambiguous_at_shock_millisecond")
    if int(anchor["best_ask_qty"]) <= 0:
        reasons.append("anchor_best_ask_quantity_not_positive")
    if endpoint_age_ms > max_depth_age_ms:
        reasons.append("depth_endpoint_stale")
    if not context.depth_source_complete:
        reasons.append("depth_source_incomplete")
    if not context.market_source_complete:
        reasons.append("market_source_incomplete")
    if _has_sequence_gap(
        rows=samples,
        start_sequence=int(anchor["source_sequence"]),
    ):
        reasons.append("depth_sequence_gap")

    market_window = tuple(
        row
        for row in market_rows
        if int(row["source_sequence"]) >= context.event_market_source_sequence
        and _timestamp_us(row.get("local_receive_timestamp")) >= anchor_event_us
        and _timestamp_us(row.get("local_receive_timestamp")) <= horizon_end_us
    )
    if any(
        row.get("trade_price") is None or row.get("trade_qty") is None
        for row in market_window
    ):
        reasons.append("market_trade_fields_missing")
    post_market = tuple(
        row
        for row in market_window
        if int(row["source_sequence"]) > context.event_market_source_sequence
    )
    if _has_market_sequence_gap(
        rows=post_market,
        start_sequence=context.event_market_source_sequence,
    ):
        reasons.append("market_sequence_gap")

    fixed_best_quantities: list[int] = []
    for row in samples:
        quantity = _quantity_at_fixed_ask_price(row, anchor_best_ask)
        if quantity is None:
            reasons.append("anchor_ask_price_not_retained")
            fixed_best_quantities = []
            break
        fixed_best_quantities.append(quantity)

    anchor_ask_levels = tuple(
        (float(raw[1]), int(raw[2])) for raw in anchor["ask_levels"]
    )
    top_depth_metrics: list[FixedTopDepthDepletion] = []
    for level_count in top_depth_levels:
        if len(anchor_ask_levels) < level_count:
            reasons.append(f"anchor_top{level_count}_depth_not_retained")
            top_depth_metrics.append(
                FixedTopDepthDepletion(
                    retained_level_count=level_count,
                    anchor_price_count=len(anchor_ask_levels),
                    initial_qty=None,
                    endpoint_qty=None,
                    minimum_qty=None,
                    max_depletion_qty=None,
                    max_depletion_ratio=None,
                )
            )
            continue
        anchor_prices = tuple(price for price, _ in anchor_ask_levels[:level_count])
        quantities: list[int] = []
        for row in samples:
            fixed_quantity = _quantity_at_fixed_ask_prices(row, anchor_prices)
            if fixed_quantity is None:
                reasons.append(f"anchor_top{level_count}_prices_not_retained")
                quantities = []
                break
            quantities.append(fixed_quantity)
        if not quantities:
            top_depth_metrics.append(
                FixedTopDepthDepletion(
                    retained_level_count=level_count,
                    anchor_price_count=level_count,
                    initial_qty=None,
                    endpoint_qty=None,
                    minimum_qty=None,
                    max_depletion_qty=None,
                    max_depletion_ratio=None,
                )
            )
        else:
            initial = quantities[0]
            minimum = min(quantities)
            depletion = initial - minimum
            top_depth_metrics.append(
                FixedTopDepthDepletion(
                    retained_level_count=level_count,
                    anchor_price_count=level_count,
                    initial_qty=initial,
                    endpoint_qty=quantities[-1],
                    minimum_qty=minimum,
                    max_depletion_qty=depletion,
                    max_depletion_ratio=_safe_ratio(depletion, initial),
                )
            )

    price_clear_rows = tuple(
        row for row in samples[1:] if float(row["best_ask"]) > anchor_best_ask
    )
    price_level_cleared = bool(price_clear_rows)
    first_clear_delay_ms = (
        None
        if not price_clear_rows
        else max(
            0,
            int(
                round(
                    (
                        _timestamp_us(
                            price_clear_rows[0].get("local_receive_timestamp")
                        )
                        - anchor_event_us
                    )
                    / 1_000.0
                )
            ),
        )
    )
    downward_reprice_observed = any(
        float(row["best_ask"]) < anchor_best_ask for row in samples[1:]
    )

    if fixed_best_quantities:
        minimum_index = fixed_best_quantities.index(min(fixed_best_quantities))
        minimum_us = _timestamp_us(
            samples[minimum_index].get("local_receive_timestamp")
        )
        if any(
            _timestamp_us(row.get("local_receive_timestamp")) == minimum_us
            and row.get("trade_qty") is not None
            and int(row["trade_qty"]) > 0
            and _same_price(row.get("trade_price"), anchor_best_ask)
            for row in post_market
        ):
            reasons.append("trade_depth_order_ambiguous_same_millisecond")
        if any(
            _timestamp_us(row.get("local_receive_timestamp")) < minimum_us
            and row.get("trade_qty") is not None
            and int(row["trade_qty"]) > 0
            and _same_price(row.get("trade_price"), anchor_best_ask)
            and row.get("aggressor_side") not in {"BUY", "SELL"}
            for row in post_market
        ):
            reasons.append("anchor_ask_trade_aggressor_unknown")

    metrics = _best_ask_metrics(
        quantities=fixed_best_quantities,
        samples=samples,
        anchor_best_ask=anchor_best_ask,
        market_rows=post_market,
        anchor_event_us=anchor_event_us,
        classification_source_clean=not reasons,
    )
    unique_reasons = tuple(sorted(set(reasons)))
    status = STATUS_ELIGIBLE if not unique_reasons else STATUS_SOURCE_GAP
    return AskDepletionHorizon(
        horizon_ms=horizon_ms,
        mature=True,
        source_quality_status=status,
        eligible_for_feature_ablation=status == STATUS_ELIGIBLE,
        source_gap_reasons=unique_reasons,
        depth_endpoint_age_ms=round(endpoint_age_ms, 6),
        depth_observation_count=len(samples),
        anchor_best_ask=anchor_best_ask,
        endpoint_best_ask=float(endpoint["best_ask"]),
        initial_anchor_ask_qty=metrics["initial_qty"],
        endpoint_anchor_ask_qty=metrics["endpoint_qty"],
        minimum_anchor_ask_qty=metrics["minimum_qty"],
        max_best_ask_depletion_qty=metrics["depletion_qty"],
        max_best_ask_depletion_ratio=metrics["depletion_ratio"],
        best_ask_depletion_velocity_qty_per_sec=metrics["velocity"],
        price_level_cleared=price_level_cleared,
        first_price_level_clear_delay_ms=first_clear_delay_ms,
        downward_reprice_observed=downward_reprice_observed,
        aggressive_buy_qty_before_max_depletion=metrics["aggressive_buy_qty"],
        aggressive_buy_trade_backed_ratio=metrics["trade_backed_ratio"],
        unexplained_or_cancel_like_depletion_qty=metrics["unexplained_qty"],
        unexplained_or_cancel_like_depletion_ratio=metrics["unexplained_ratio"],
        max_refill_qty=metrics["refill_qty"],
        refill_ratio=metrics["refill_ratio"],
        refill_half_life_ms=metrics["refill_half_life_ms"],
        top_depth=tuple(top_depth_metrics),
    )


def _best_ask_metrics(
    *,
    quantities: list[int],
    samples: tuple[dict[str, Any], ...],
    anchor_best_ask: float,
    market_rows: tuple[dict[str, Any], ...],
    anchor_event_us: int,
    classification_source_clean: bool,
) -> dict[str, int | float | None]:
    empty = {
        "initial_qty": None,
        "endpoint_qty": None,
        "minimum_qty": None,
        "depletion_qty": None,
        "depletion_ratio": None,
        "velocity": None,
        "aggressive_buy_qty": None,
        "trade_backed_ratio": None,
        "unexplained_qty": None,
        "unexplained_ratio": None,
        "refill_qty": None,
        "refill_ratio": None,
        "refill_half_life_ms": None,
    }
    if not quantities:
        return empty
    initial = quantities[0]
    minimum = min(quantities)
    minimum_index = quantities.index(minimum)
    minimum_us = _timestamp_us(samples[minimum_index].get("local_receive_timestamp"))
    depletion = initial - minimum
    delay_sec = max(0.0, (minimum_us - anchor_event_us) / 1_000_000.0)
    velocity = (
        0.0 if depletion == 0 else (None if delay_sec <= 0 else depletion / delay_sec)
    )
    later_quantities = quantities[minimum_index:]
    refill_qty = max(later_quantities) - minimum
    refill_ratio = _safe_ratio(refill_qty, depletion)
    refill_half_life_ms: int | None = None
    if depletion > 0:
        half_refill_quantity = minimum + depletion * 0.5
        for index in range(minimum_index + 1, len(quantities)):
            if quantities[index] >= half_refill_quantity:
                refill_half_life_ms = max(
                    0,
                    int(
                        round(
                            (
                                _timestamp_us(
                                    samples[index].get("local_receive_timestamp")
                                )
                                - minimum_us
                            )
                            / 1_000.0
                        )
                    ),
                )
                break

    aggressive_buy_qty: int | None = None
    trade_backed_ratio: float | None = None
    unexplained_qty: int | None = None
    unexplained_ratio: float | None = None
    if classification_source_clean:
        aggressive_buy_qty = sum(
            int(row["trade_qty"])
            for row in market_rows
            if _timestamp_us(row.get("local_receive_timestamp")) < minimum_us
            and row.get("aggressor_side") == "BUY"
            and row.get("trade_qty") is not None
            and int(row["trade_qty"]) > 0
            and _same_price(row.get("trade_price"), anchor_best_ask)
        )
        if depletion > 0:
            explained_qty = min(depletion, aggressive_buy_qty)
            unexplained_qty = depletion - explained_qty
            trade_backed_ratio = _safe_ratio(explained_qty, depletion)
            unexplained_ratio = _safe_ratio(unexplained_qty, depletion)

    return {
        "initial_qty": initial,
        "endpoint_qty": quantities[-1],
        "minimum_qty": minimum,
        "depletion_qty": depletion,
        "depletion_ratio": _safe_ratio(depletion, initial),
        "velocity": _rounded(velocity),
        "aggressive_buy_qty": aggressive_buy_qty,
        "trade_backed_ratio": trade_backed_ratio,
        "unexplained_qty": unexplained_qty,
        "unexplained_ratio": unexplained_ratio,
        "refill_qty": refill_qty,
        "refill_ratio": refill_ratio,
        "refill_half_life_ms": refill_half_life_ms,
    }


def _quantity_at_fixed_ask_price(
    payload: Mapping[str, Any], fixed_price: float
) -> int | None:
    current_best_ask = float(payload["best_ask"])
    if current_best_ask > fixed_price and not _same_price(
        current_best_ask, fixed_price
    ):
        return 0
    for raw in payload["ask_levels"]:
        if _same_price(raw[1], fixed_price):
            return int(raw[2])
    return None


def _quantity_at_fixed_ask_prices(
    payload: Mapping[str, Any], fixed_prices: tuple[float, ...]
) -> int | None:
    quantities: list[int] = []
    for price in fixed_prices:
        quantity = _quantity_at_fixed_ask_price(payload, price)
        if quantity is None:
            return None
        quantities.append(quantity)
    return sum(quantities)


def _missing_anchor_report(
    *,
    context: AskDepletionContext,
    horizons_ms: tuple[int, ...],
    reason: str,
    ignored_depth_count: int,
    ignored_market_count: int,
) -> AskDepletionReport:
    horizons = tuple(
        _empty_horizon(
            horizon_ms=horizon_ms,
            mature=(
                context.observed_through_local_receive_timestamp_ms
                >= context.anchor_event_local_receive_timestamp_ms + horizon_ms
            ),
            reasons=(reason,),
        )
        for horizon_ms in horizons_ms
    )
    return AskDepletionReport(
        context=context,
        anchor_source_sequence=None,
        anchor_depth_age_ms=None,
        anchor_source_quality_status=STATUS_SOURCE_GAP,
        source_quality_status=STATUS_SOURCE_GAP,
        source_gap_reasons=(reason,),
        ignored_cross_scope_depth_row_count=ignored_depth_count,
        ignored_cross_scope_market_row_count=ignored_market_count,
        horizons=horizons,
    )


def _empty_horizon(
    *,
    horizon_ms: int,
    mature: bool,
    reasons: tuple[str, ...],
    anchor_best_ask: float | None = None,
    status: str = STATUS_SOURCE_GAP,
) -> AskDepletionHorizon:
    return AskDepletionHorizon(
        horizon_ms=horizon_ms,
        mature=mature,
        source_quality_status=status,
        eligible_for_feature_ablation=False,
        source_gap_reasons=tuple(sorted(set(reasons))),
        depth_endpoint_age_ms=None,
        depth_observation_count=0,
        anchor_best_ask=anchor_best_ask,
        endpoint_best_ask=None,
        initial_anchor_ask_qty=None,
        endpoint_anchor_ask_qty=None,
        minimum_anchor_ask_qty=None,
        max_best_ask_depletion_qty=None,
        max_best_ask_depletion_ratio=None,
        best_ask_depletion_velocity_qty_per_sec=None,
        price_level_cleared=None,
        first_price_level_clear_delay_ms=None,
        downward_reprice_observed=None,
        aggressive_buy_qty_before_max_depletion=None,
        aggressive_buy_trade_backed_ratio=None,
        unexplained_or_cancel_like_depletion_qty=None,
        unexplained_or_cancel_like_depletion_ratio=None,
        max_refill_qty=None,
        refill_ratio=None,
        refill_half_life_ms=None,
        top_depth=(),
    )


def _deduplicate_explicit_anchor(
    *, anchor: dict[str, Any], rows: tuple[dict[str, Any], ...]
) -> tuple[dict[str, Any], ...]:
    retained: list[dict[str, Any]] = []
    anchor_key = _depth_sort_key(anchor)
    anchor_seen = False
    for row in rows:
        if _depth_sort_key(row) != anchor_key:
            retained.append(row)
            continue
        if row != anchor:
            raise ValueError("depth row conflicts with the explicit anchor")
        if anchor_seen:
            raise ValueError("duplicate depth source sequence")
        anchor_seen = True
    return tuple(retained)


def _validate_unique_sequences(
    rows: tuple[dict[str, Any], ...], *, source_name: str
) -> None:
    seen: set[int] = set()
    for row in rows:
        sequence = int(row["source_sequence"])
        if sequence in seen:
            raise ValueError(f"duplicate {source_name} source sequence")
        seen.add(sequence)


def _has_sequence_gap(*, rows: tuple[dict[str, Any], ...], start_sequence: int) -> bool:
    expected = start_sequence
    for row in rows[1:]:
        sequence = int(row["source_sequence"])
        if sequence != expected + 1:
            return True
        expected = sequence
    return False


def _has_market_sequence_gap(
    *, rows: tuple[dict[str, Any], ...], start_sequence: int
) -> bool:
    expected = start_sequence
    for row in rows:
        sequence = int(row["source_sequence"])
        if sequence != expected + 1:
            return True
        expected = sequence
    return False


def _validate_market_row(payload: Mapping[str, Any]) -> None:
    if (
        payload.get("schema") != MARKET_STREAM_SCHEMA
        or payload.get("metric_contract_id") != MARKET_STREAM_CONTRACT_ID
        or payload.get("realtime_type") != "0B"
    ):
        raise ValueError("unexpected ask depletion market schema or contract")
    registration_item = payload.get("item")
    if registration_item is not None:
        item_symbol, item_venue = registration_item_identity(registration_item)
        if (
            not item_symbol
            or item_symbol != normalize_symbol(payload.get("symbol"))
            or item_venue != normalize_venue(payload.get("venue"))
        ):
            raise ValueError("ask depletion market item conflicts with row scope")
    if (
        payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("trading_runtime_effect") is not False
    ):
        raise ValueError("ask depletion market authority contract is invalid")
    source_sequence = payload.get("source_sequence")
    series_sequence = payload.get("series_sequence")
    if (
        isinstance(source_sequence, bool)
        or not isinstance(source_sequence, int)
        or source_sequence <= 0
        or isinstance(series_sequence, bool)
        or not isinstance(series_sequence, int)
        or series_sequence != source_sequence
    ):
        raise ValueError("ask depletion market sequence is invalid")
    _scope(payload)
    exchange_us = _timestamp_us(payload.get("exchange_timestamp"))
    receive_us = _timestamp_us(payload.get("local_receive_timestamp"))
    if receive_us < exchange_us:
        raise ValueError("ask depletion market receive time precedes exchange time")
    _, eligible, _ = validate_market_stream_path_provenance(
        path_order_status=payload.get("path_order_status"),
        path_consumer_eligible=payload.get("path_consumer_eligible"),
        exchange_timestamp_regression_ms=payload.get(
            "exchange_timestamp_regression_ms"
        ),
    )
    if not eligible:
        raise ValueError("ask depletion market row is not path eligible")
    trade_price = payload.get("trade_price")
    trade_qty = payload.get("trade_qty")
    if trade_price is not None and (
        isinstance(trade_price, bool)
        or not isinstance(trade_price, (int, float))
        or not math.isfinite(float(trade_price))
        or float(trade_price) <= 0
    ):
        raise ValueError("ask depletion trade price is invalid")
    if trade_qty is not None and (
        isinstance(trade_qty, bool) or not isinstance(trade_qty, int) or trade_qty < 0
    ):
        raise ValueError("ask depletion trade quantity is invalid")
    if payload.get("aggressor_side") not in {None, "BUY", "SELL", "UNKNOWN"}:
        raise ValueError("ask depletion aggressor side is invalid")


def _validate_configuration(
    *,
    horizons_ms: tuple[int, ...],
    top_depth_levels: tuple[int, ...],
    max_depth_age_ms: int,
) -> None:
    if any(
        isinstance(value, bool) or not isinstance(value, int) for value in horizons_ms
    ):
        raise ValueError("ask depletion horizons must be positive, sorted, and unique")
    if not horizons_ms or tuple(sorted(set(horizons_ms))) != horizons_ms:
        raise ValueError("ask depletion horizons must be positive, sorted, and unique")
    if any(value <= 0 for value in horizons_ms):
        raise ValueError("ask depletion horizons must be positive, sorted, and unique")
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in top_depth_levels
    ):
        raise ValueError("top depth levels must be positive, sorted, and unique")
    if not top_depth_levels or tuple(sorted(set(top_depth_levels))) != top_depth_levels:
        raise ValueError("top depth levels must be positive, sorted, and unique")
    if any(value <= 0 for value in top_depth_levels):
        raise ValueError("top depth levels must be positive, sorted, and unique")
    if (
        isinstance(max_depth_age_ms, bool)
        or not isinstance(max_depth_age_ms, int)
        or max_depth_age_ms <= 0
    ):
        raise ValueError("max_depth_age_ms must be positive")


def _scope(payload: Mapping[str, Any]) -> tuple[str, str, str, int]:
    symbol = normalize_symbol(payload.get("symbol"))
    venue = normalize_venue(payload.get("venue"))
    session_bucket = str(payload.get("session_bucket") or "").strip().upper()
    sequence_epoch = payload.get("sequence_epoch")
    if (
        not symbol
        or venue == "UNKNOWN"
        or not session_bucket
        or isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        raise ValueError("ask depletion row scope is invalid")
    return symbol, venue, session_bucket, sequence_epoch


def _depth_sort_key(payload: Mapping[str, Any]) -> tuple[int, int]:
    return (
        _timestamp_us(payload.get("local_receive_timestamp")),
        int(payload["source_sequence"]),
    )


def _market_sort_key(payload: Mapping[str, Any]) -> tuple[int, int]:
    return (
        _timestamp_us(payload.get("local_receive_timestamp")),
        int(payload["source_sequence"]),
    )


def _timestamp_us(value: object) -> int:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("ask depletion timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("ask depletion timestamp must include timezone")
    return int(parsed.timestamp() * 1_000_000)


def _same_price(left: object, right: object) -> bool:
    if left is None or right is None:
        return False
    try:
        left_value = float(left)
        right_value = float(right)
    except (TypeError, ValueError):
        return False
    return math.isfinite(left_value) and math.isclose(
        left_value,
        right_value,
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 8)


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, 8)


__all__ = (
    "ASK_DEPLETION_AUTHORITY",
    "ASK_DEPLETION_METRIC_CONTRACT",
    "ASK_DEPLETION_SCHEMA",
    "AskDepletionContext",
    "AskDepletionHorizon",
    "AskDepletionReport",
    "DEFAULT_HORIZONS_MS",
    "DEFAULT_TOP_DEPTH_LEVELS",
    "FixedTopDepthDepletion",
    "build_ask_depletion_report",
)
