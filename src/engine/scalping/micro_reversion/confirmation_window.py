"""Offline 120/180-second micro-reversion confirmation labels.

The frozen forward-collector onset diagnostic is deliberately not modified by
this module.  These labels consume the already captured path after a shock and
remain outcome-only inputs for postclose micro-reversion tuning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from .onset_quality import ShockOnsetContext
from .p2_replay import P2ReplayPoint

DEFAULT_CONFIRMATION_HORIZONS_MS = (120_000, 180_000)


class ConfirmationDirectionState(StrEnum):
    DATA_WAIT = "DATA_WAIT"
    SOURCE_GAP = "SOURCE_GAP"
    REVERSION_CONFIRMED = "REVERSION_CONFIRMED"
    CONTINUATION_CONFIRMED = "CONTINUATION_CONFIRMED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True, slots=True)
class ConfirmationHorizon:
    horizon_ms: int
    confirmation_fraction: float
    mature: bool
    post_trade_count: int
    additional_mae_bps: float | None
    post_low_delay_ms: int | None
    terminal_trade_return_bps: float | None
    max_reclaim_from_post_low_bps: float | None
    half_reclaim_confirmed: bool
    confirmation_count: int
    recovery_invalidation_count: int
    active_confirmation_delay_ms: int | None
    active_confirmation_trade_price: float | None
    active_confirmation_best_ask: float | None
    active_confirmation_quote_age_ms: float | None
    confirmation_followthrough_ms: int | None
    confirmation_followthrough_trade_count: int
    confirmation_fresh_bbo_count: int
    confirmation_to_terminal_trade_return_bps: float | None
    confirmation_to_terminal_trade_mfe_bps: float | None
    confirmation_to_terminal_trade_mae_bps: float | None
    confirmation_to_terminal_bbo_proxy_gross_return_bps: float | None
    confirmation_to_terminal_bbo_proxy_mfe_bps: float | None
    confirmation_to_terminal_bbo_proxy_mae_bps: float | None
    terminal_trade_lag_ms: int | None
    direction_state: ConfirmationDirectionState


def analyze_confirmation_window(
    points: Iterable[P2ReplayPoint],
    *,
    context: ShockOnsetContext,
    horizons_ms: tuple[int, ...] = DEFAULT_CONFIRMATION_HORIZONS_MS,
    confirmation_fraction: float = 0.5,
    max_terminal_trade_lag_ms: int = 2_500,
    max_quote_age_ms: int = 1_000,
) -> tuple[ConfirmationHorizon, ...]:
    """Classify each completed horizon without imputing an endpoint trade."""

    if (
        not horizons_ms
        or tuple(sorted(set(horizons_ms))) != horizons_ms
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in horizons_ms
        )
    ):
        raise ValueError("horizons_ms must be positive, sorted, and unique")
    if (
        isinstance(max_terminal_trade_lag_ms, bool)
        or not isinstance(max_terminal_trade_lag_ms, int)
        or max_terminal_trade_lag_ms < 0
    ):
        raise ValueError("max_terminal_trade_lag_ms must not be negative")
    if (
        isinstance(confirmation_fraction, bool)
        or not isinstance(confirmation_fraction, (int, float))
        or not math.isfinite(float(confirmation_fraction))
        or not 0 < confirmation_fraction <= 1
    ):
        raise ValueError("confirmation_fraction must be in (0, 1]")
    if (
        isinstance(max_quote_age_ms, bool)
        or not isinstance(max_quote_age_ms, int)
        or max_quote_age_ms < 0
    ):
        raise ValueError("max_quote_age_ms must not be negative")
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
    return tuple(
        _analyze_horizon(
            post,
            context=context,
            horizon_ms=horizon_ms,
            confirmation_fraction=confirmation_fraction,
            max_terminal_trade_lag_ms=max_terminal_trade_lag_ms,
            max_quote_age_ms=max_quote_age_ms,
        )
        for horizon_ms in horizons_ms
    )


def _analyze_horizon(
    post: tuple[P2ReplayPoint, ...],
    *,
    context: ShockOnsetContext,
    horizon_ms: int,
    confirmation_fraction: float,
    max_terminal_trade_lag_ms: int,
    max_quote_age_ms: int,
) -> ConfirmationHorizon:
    deadline_ms = context.event_local_receive_timestamp_ms + horizon_ms
    mature = any(point.local_receive_timestamp_ms >= deadline_ms for point in post)
    trades = tuple(
        point
        for point in post
        if point.local_receive_timestamp_ms <= deadline_ms
        and point.trade_price is not None
    )
    if not trades:
        return ConfirmationHorizon(
            horizon_ms=horizon_ms,
            confirmation_fraction=confirmation_fraction,
            mature=mature,
            post_trade_count=0,
            additional_mae_bps=None,
            post_low_delay_ms=None,
            terminal_trade_return_bps=None,
            max_reclaim_from_post_low_bps=None,
            half_reclaim_confirmed=False,
            confirmation_count=0,
            recovery_invalidation_count=0,
            active_confirmation_delay_ms=None,
            active_confirmation_trade_price=None,
            active_confirmation_best_ask=None,
            active_confirmation_quote_age_ms=None,
            confirmation_followthrough_ms=None,
            confirmation_followthrough_trade_count=0,
            confirmation_fresh_bbo_count=0,
            confirmation_to_terminal_trade_return_bps=None,
            confirmation_to_terminal_trade_mfe_bps=None,
            confirmation_to_terminal_trade_mae_bps=None,
            confirmation_to_terminal_bbo_proxy_gross_return_bps=None,
            confirmation_to_terminal_bbo_proxy_mfe_bps=None,
            confirmation_to_terminal_bbo_proxy_mae_bps=None,
            terminal_trade_lag_ms=None,
            direction_state=(
                ConfirmationDirectionState.SOURCE_GAP
                if mature
                else ConfirmationDirectionState.DATA_WAIT
            ),
        )

    low_price = context.shock_price
    low_at_ms = context.event_local_receive_timestamp_ms
    low_index = -1
    half_reclaim_confirmed = False
    confirmation_count = 0
    active_confirmation_index: int | None = None
    recovery_invalidation_count = 0
    for index, point in enumerate(trades):
        assert point.trade_price is not None
        point_low = point.low or point.trade_price
        if point_low < low_price:
            low_price = point_low
            low_at_ms = point.local_receive_timestamp_ms
            low_index = index
            if half_reclaim_confirmed:
                recovery_invalidation_count += 1
                half_reclaim_confirmed = False
                active_confirmation_index = None
        reclaim_span = context.reference_price - low_price
        reclaim_threshold = low_price + confirmation_fraction * reclaim_span
        if half_reclaim_confirmed and point.trade_price < reclaim_threshold:
            recovery_invalidation_count += 1
            half_reclaim_confirmed = False
            active_confirmation_index = None
        if (
            not half_reclaim_confirmed
            and reclaim_span > 0
            and point.trade_price >= reclaim_threshold
        ):
            half_reclaim_confirmed = True
            confirmation_count += 1
            active_confirmation_index = index
    reclaim_prices = [low_price]
    reclaim_prices.extend(
        point.trade_price
        for point in trades[low_index + 1 :]
        if point.trade_price is not None
    )
    terminal_price = trades[-1].trade_price
    assert terminal_price is not None
    confirmation_point = (
        None if active_confirmation_index is None else trades[active_confirmation_index]
    )
    confirmation_price = (
        None if confirmation_point is None else confirmation_point.trade_price
    )
    confirmation_path = (
        () if active_confirmation_index is None else trades[active_confirmation_index:]
    )
    confirmation_prices = tuple(
        point.trade_price
        for point in confirmation_path
        if point.trade_price is not None
    )
    confirmation_bbo_path = tuple(
        point
        for point in confirmation_path
        if _fresh_bbo(point, max_quote_age_ms=max_quote_age_ms)
    )
    confirmation_ask = (
        None
        if confirmation_point is None
        or not _fresh_bbo(confirmation_point, max_quote_age_ms=max_quote_age_ms)
        else confirmation_point.best_ask
    )
    bbo_proxy_returns = (
        ()
        if confirmation_ask is None
        else tuple(
            (float(point.best_bid) / float(confirmation_ask) - 1.0) * 10_000.0
            for point in confirmation_bbo_path
            if point.best_bid is not None
        )
    )
    terminal_bbo_proxy_return = (
        None
        if confirmation_ask is None
        or not _fresh_bbo(trades[-1], max_quote_age_ms=max_quote_age_ms)
        or trades[-1].best_bid is None
        else (float(trades[-1].best_bid) / float(confirmation_ask) - 1.0) * 10_000.0
    )
    terminal_trade_lag_ms = deadline_ms - trades[-1].local_receive_timestamp_ms
    if not mature:
        direction_state = ConfirmationDirectionState.DATA_WAIT
    elif terminal_trade_lag_ms > max_terminal_trade_lag_ms:
        direction_state = ConfirmationDirectionState.SOURCE_GAP
    elif half_reclaim_confirmed:
        direction_state = ConfirmationDirectionState.REVERSION_CONFIRMED
    elif low_price < context.shock_price and terminal_price <= context.shock_price:
        direction_state = ConfirmationDirectionState.CONTINUATION_CONFIRMED
    else:
        direction_state = ConfirmationDirectionState.INCONCLUSIVE
    return ConfirmationHorizon(
        horizon_ms=horizon_ms,
        confirmation_fraction=confirmation_fraction,
        mature=mature,
        post_trade_count=len(trades),
        additional_mae_bps=round(
            (low_price / context.shock_price - 1.0) * 10_000.0,
            6,
        ),
        post_low_delay_ms=low_at_ms - context.event_local_receive_timestamp_ms,
        terminal_trade_return_bps=round(
            (terminal_price / context.shock_price - 1.0) * 10_000.0,
            6,
        ),
        max_reclaim_from_post_low_bps=round(
            (max(reclaim_prices) / low_price - 1.0) * 10_000.0,
            6,
        ),
        half_reclaim_confirmed=half_reclaim_confirmed,
        confirmation_count=confirmation_count,
        recovery_invalidation_count=recovery_invalidation_count,
        active_confirmation_delay_ms=(
            None
            if confirmation_point is None
            else confirmation_point.local_receive_timestamp_ms
            - context.event_local_receive_timestamp_ms
        ),
        active_confirmation_trade_price=confirmation_price,
        active_confirmation_best_ask=confirmation_ask,
        active_confirmation_quote_age_ms=(
            None if confirmation_point is None else confirmation_point.quote_age_ms
        ),
        confirmation_followthrough_ms=(
            None
            if confirmation_point is None
            else trades[-1].local_receive_timestamp_ms
            - confirmation_point.local_receive_timestamp_ms
        ),
        confirmation_followthrough_trade_count=len(confirmation_path),
        confirmation_fresh_bbo_count=len(confirmation_bbo_path),
        confirmation_to_terminal_trade_return_bps=(
            None
            if confirmation_price is None
            else round((terminal_price / confirmation_price - 1.0) * 10_000.0, 6)
        ),
        confirmation_to_terminal_trade_mfe_bps=(
            None
            if confirmation_price is None or not confirmation_prices
            else round(
                (max(confirmation_prices) / confirmation_price - 1.0) * 10_000.0,
                6,
            )
        ),
        confirmation_to_terminal_trade_mae_bps=(
            None
            if confirmation_price is None or not confirmation_prices
            else round(
                (min(confirmation_prices) / confirmation_price - 1.0) * 10_000.0,
                6,
            )
        ),
        confirmation_to_terminal_bbo_proxy_gross_return_bps=(
            None
            if terminal_bbo_proxy_return is None
            else round(terminal_bbo_proxy_return, 6)
        ),
        confirmation_to_terminal_bbo_proxy_mfe_bps=(
            None if not bbo_proxy_returns else round(max(bbo_proxy_returns), 6)
        ),
        confirmation_to_terminal_bbo_proxy_mae_bps=(
            None if not bbo_proxy_returns else round(min(bbo_proxy_returns), 6)
        ),
        terminal_trade_lag_ms=terminal_trade_lag_ms,
        direction_state=direction_state,
    )


def _fresh_bbo(point: P2ReplayPoint, *, max_quote_age_ms: int) -> bool:
    return bool(
        point.best_bid is not None
        and point.best_ask is not None
        and point.best_bid > 0
        and point.best_ask >= point.best_bid
        and point.quote_age_ms is not None
        and 0 <= point.quote_age_ms <= max_quote_age_ms
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
