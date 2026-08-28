"""Fresh touch-depth and execution-velocity guards for new buy authority.

The guards are deliberately owner-neutral.  They evaluate one fresh Kiwoom
``ka10004`` snapshot and the latest ``ka10003`` prints but never submit,
cancel, reprice, or exit an order.  Each trading owner remains responsible for
recording its own decision and for keeping already-owned positions and target
orders unchanged.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.utils import kiwoom_utils

ENTRY_LIQUIDITY_POLICY_ID = "entry_touch_liquidity_guard_v1"
MIN_TOUCH_QUANTITY_EACH_SIDE = 100
REQUEST_QUANTITY_MULTIPLIER = 5
MAX_SNAPSHOT_AGE_MS = 2_000
ENTRY_EXECUTION_VELOCITY_POLICY_ID = "entry_execution_velocity_guard_v1"
REQUIRED_RECENT_PRINT_COUNT = 10
MAX_RECENT_PRINT_SPAN_MS = 20_000
MAX_LATEST_PRINT_AGE_MS = 5_000
MAX_EVENT_CLOCK_SKEW_MS = 2_000
MIN_RECENT_PRINT_VOLUME = 20
RECENT_VOLUME_QUANTITY_MULTIPLIER = 2
KST = ZoneInfo("Asia/Seoul")

ENTRY_LIQUIDITY_POLICY_CONTRACT = {
    "metric_role": "new_buy_pre_submit_liquidity_guard",
    "decision_authority": "block_new_widget_or_episode_buy_only",
    "window_policy": "point_in_time_fresh_snapshot_only",
    "sample_floor": "one_route_qualified_ka10004_snapshot_per_submit_bundle",
    "primary_decision_metric": "minimum_best_bid_and_ask_touch_quantity_shares",
    "source_quality_gate": (
        "exact_symbol_and_route;response_receive_age_lte_2000ms;"
        "positive_uncrossed_bbo;nonnegative_touch_quantities"
    ),
    "forbidden_uses": [
        "sell_cancel_reprice_or_exit_authority",
        "existing_position_or_target_order_mutation",
        "owner_custody_reconciliation",
        "postclose_automatic_threshold_or_quantity_tuning",
        "main_bot_order_authority",
    ],
}

ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT = {
    "metric_role": "new_buy_pre_submit_execution_velocity_guard",
    "decision_authority": "block_new_widget_or_episode_buy_only",
    "window_policy": "point_in_time_latest_10_trade_prints",
    "sample_floor": "10_route_qualified_ka10003_trade_prints",
    "primary_decision_metric": "latest_10_trade_print_span_milliseconds",
    "source_quality_gate": (
        "exact_symbol_and_route;ka10003_cache_ttl_lte_1000ms;"
        "valid_monotonic_HHmmss;latest_print_age_lte_5000ms;"
        "strictly_descending_accumulated_trade_quantity;"
        "positive_price_and_absolute_trade_quantity"
    ),
    "forbidden_uses": [
        "sell_cancel_reprice_or_exit_authority",
        "existing_position_or_target_order_mutation",
        "owner_custody_reconciliation",
        "aggressor_side_or_direction_inference",
        "postclose_automatic_threshold_or_quantity_tuning",
        "main_bot_order_authority",
    ],
}

KIWOOM_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "9180debf7aea0074715dd8f7a15af432afbfc403",
    "retrieved_at_kst": "2026-08-28T14:31:24+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["ka10004"],
    "verified_contract": {
        "method": "POST",
        "path": "/api/dostk/mrkcond",
        "request_field": "stk_cd",
        "best_ask_fields": ["sel_fpr_bid", "sel_fpr_req"],
        "best_bid_fields": ["buy_fpr_bid", "buy_fpr_req"],
        "total_depth_fields": ["tot_sel_req", "tot_buy_req"],
        "quantity_unit": "shares",
    },
}

KIWOOM_EXECUTION_VELOCITY_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "9180debf7aea0074715dd8f7a15af432afbfc403",
    "retrieved_at_kst": "2026-08-28T15:14:00+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["ka10003"],
    "verified_contract": {
        "method": "POST",
        "path": "/api/dostk/stkinfo",
        "request_field": "stk_cd",
        "response_list": "cntr_infr",
        "trade_time_field": "tm",
        "trade_price_field": "cur_prc",
        "trade_quantity_field": "cntr_trde_qty",
        "venue_field": "stex_tp",
        "time_format": "HHmmss",
        "quantity_unit": "shares",
    },
}


def _nonnegative_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean_is_not_quantity")
    normalized = int(value)
    if normalized < 0:
        raise ValueError("negative_quantity")
    return normalized


def _positive_int(value: object) -> int:
    normalized = _nonnegative_int(value)
    if normalized <= 0:
        raise ValueError("nonpositive_value")
    return normalized


def entry_liquidity_request_code(symbol: str, route: str) -> str:
    """Return an explicit venue-qualified Kiwoom orderbook instrument code.

    Regular-session KRX widget observations are broker-routed through SOR, so
    both ``KRX`` and ``SOR`` intentionally use the integrated ``_AL`` book.
    NXT PRE/AFTER observations use the NXT-only ``_NX`` book.
    """

    code = kiwoom_utils.normalize_stock_code(symbol)
    if len(code) != 6 or not code.isdigit():
        raise ValueError("entry_liquidity_symbol_invalid")
    normalized_route = str(route or "").strip().upper()
    if normalized_route in {"KRX", "SOR"}:
        return f"{code}_AL"
    if normalized_route == "NXT":
        return f"{code}_NX"
    raise ValueError("entry_liquidity_route_invalid")


@dataclass(frozen=True)
class EntryLiquiditySnapshot:
    source_ok: bool
    symbol: str
    route: str
    request_code: str
    source: str = "ka10004_rest_orderbook"
    best_bid: int = 0
    best_ask: int = 0
    best_bid_qty: int = 0
    best_ask_qty: int = 0
    bid_total_qty: int = 0
    ask_total_qty: int = 0
    age_ms: int = 0
    received_ts_ms: int = 0
    error: str = ""


@dataclass(frozen=True)
class EntryLiquidityDecision:
    allowed: bool
    reason: str
    requested_quantity: int
    required_each_side_quantity: int
    snapshot: EntryLiquiditySnapshot
    policy_id: str = ENTRY_LIQUIDITY_POLICY_ID

    def event_fields(self) -> dict[str, Any]:
        return {
            "entry_liquidity_policy_id": self.policy_id,
            "entry_liquidity_allowed": self.allowed,
            "entry_liquidity_reason": self.reason,
            "entry_liquidity_requested_quantity": self.requested_quantity,
            "entry_liquidity_required_each_side_quantity": (
                self.required_each_side_quantity
            ),
            "entry_liquidity_policy_contract": deepcopy(
                ENTRY_LIQUIDITY_POLICY_CONTRACT
            ),
            "entry_liquidity_snapshot": asdict(self.snapshot),
        }


@dataclass(frozen=True)
class EntryExecutionVelocitySnapshot:
    source_ok: bool
    symbol: str
    route: str
    request_code: str
    source: str = "ka10003_rest_trade_prints"
    print_count: int = 0
    recent_print_span_ms: int = 0
    latest_print_age_ms: int = 0
    recent_volume: int = 0
    observed_at_kst: str = ""
    print_times: tuple[str, ...] = ()
    venues: tuple[str, ...] = ()
    error: str = ""


@dataclass(frozen=True)
class EntryExecutionVelocityDecision:
    allowed: bool
    reason: str
    requested_quantity: int
    required_recent_volume: int
    snapshot: EntryExecutionVelocitySnapshot
    policy_id: str = ENTRY_EXECUTION_VELOCITY_POLICY_ID

    def event_fields(self) -> dict[str, Any]:
        return {
            "entry_execution_velocity_policy_id": self.policy_id,
            "entry_execution_velocity_allowed": self.allowed,
            "entry_execution_velocity_reason": self.reason,
            "entry_execution_velocity_requested_quantity": self.requested_quantity,
            "entry_execution_velocity_required_recent_volume": (
                self.required_recent_volume
            ),
            "entry_execution_velocity_policy_contract": deepcopy(
                ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT
            ),
            "entry_execution_velocity_snapshot": asdict(self.snapshot),
        }


def unavailable_entry_liquidity_snapshot(
    *, symbol: str, route: str, error: str
) -> EntryLiquiditySnapshot:
    try:
        request_code = entry_liquidity_request_code(symbol, route)
    except ValueError:
        request_code = ""
    return EntryLiquiditySnapshot(
        source_ok=False,
        symbol=kiwoom_utils.normalize_stock_code(symbol),
        route=str(route or "").strip().upper(),
        request_code=request_code,
        error=str(error or "entry_liquidity_source_unavailable")[:160],
    )


def unavailable_entry_execution_velocity_snapshot(
    *, symbol: str, route: str, error: str
) -> EntryExecutionVelocitySnapshot:
    try:
        request_code = entry_liquidity_request_code(symbol, route)
    except ValueError:
        request_code = ""
    return EntryExecutionVelocitySnapshot(
        source_ok=False,
        symbol=kiwoom_utils.normalize_stock_code(symbol),
        route=str(route or "").strip().upper(),
        request_code=request_code,
        error=str(error or "entry_execution_velocity_source_unavailable")[:160],
    )


def _strict_signed_int(value: object) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError("signed_integer_missing_or_boolean")
    normalized = str(value).replace(",", "").strip()
    if re.fullmatch(r"[+-]?[0-9]+", normalized) is None:
        raise ValueError("signed_integer_invalid")
    return int(normalized)


def _hhmmss_seconds(value: object) -> int:
    text = str(value or "").strip()
    if re.fullmatch(r"[0-9]{6}", text) is None:
        raise ValueError("trade_time_invalid")
    hours, minutes, seconds = int(text[:2]), int(text[2:4]), int(text[4:6])
    if hours > 23 or minutes > 59 or seconds > 59:
        raise ValueError("trade_time_out_of_range")
    return hours * 3600 + minutes * 60 + seconds


def parse_ka10003_entry_execution_velocity_snapshot(
    payload: object,
    *,
    symbol: str,
    route: str,
    observed_at: datetime | None = None,
) -> EntryExecutionVelocitySnapshot:
    """Validate recent ``ka10003`` prints without inferring trade direction."""

    observed = observed_at or datetime.now(tz=KST)
    if observed.tzinfo is None:
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol,
            route=route,
            error="entry_execution_velocity_observed_at_timezone_required",
        )
    observed = observed.astimezone(KST)
    try:
        expected_code = kiwoom_utils.normalize_stock_code(symbol)
        request_code = entry_liquidity_request_code(symbol, route)
    except ValueError as exc:
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol, route=route, error=str(exc)
        )
    normalized_route = str(route or "").strip().upper()
    if not isinstance(payload, list):
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol, route=route, error="ka10003_payload_invalid"
        )
    if not payload:
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol, route=route, error="ka10003_trade_rows_unavailable"
        )

    times: list[str] = []
    seconds: list[int] = []
    volumes: list[int] = []
    accumulated_volumes: list[int] = []
    venues: list[str] = []
    try:
        for tick in payload[:REQUIRED_RECENT_PRINT_COUNT]:
            if not isinstance(tick, dict) or not isinstance(tick.get("raw"), dict):
                raise ValueError("ka10003_trade_row_invalid")
            raw = tick["raw"]
            raw_time = str(raw.get("tm") or "").strip()
            if str(tick.get("time") or "").strip() != raw_time:
                raise ValueError("ka10003_trade_time_normalization_conflict")
            trade_seconds = _hhmmss_seconds(raw_time)
            price = abs(_strict_signed_int(raw.get("cur_prc")))
            volume = abs(_strict_signed_int(raw.get("cntr_trde_qty")))
            accumulated_volume = _strict_signed_int(raw.get("acc_trde_qty"))
            venue = str(raw.get("stex_tp") or "").strip().upper()
            if price <= 0 or volume <= 0 or accumulated_volume <= 0:
                raise ValueError("ka10003_nonpositive_trade_value")
            if normalized_route == "NXT":
                if venue != "NXT":
                    raise ValueError("ka10003_nxt_route_conflict")
            elif venue not in {"KRX", "NXT", "SOR", "통합"}:
                raise ValueError("ka10003_integrated_route_conflict")
            times.append(raw_time)
            seconds.append(trade_seconds)
            volumes.append(volume)
            accumulated_volumes.append(accumulated_volume)
            venues.append(venue)
        if any(left < right for left, right in zip(seconds, seconds[1:])):
            raise ValueError("ka10003_trade_time_not_latest_first")
        if any(
            left <= right
            for left, right in zip(accumulated_volumes, accumulated_volumes[1:])
        ):
            raise ValueError("ka10003_accumulated_volume_not_latest_first")
        observed_seconds = observed.hour * 3600 + observed.minute * 60 + observed.second
        latest_age_ms = (
            (observed_seconds - seconds[0]) * 1_000
            + observed.microsecond // 1_000
        )
        if latest_age_ms < -MAX_EVENT_CLOCK_SKEW_MS:
            raise ValueError("ka10003_latest_trade_time_in_future")
        latest_age_ms = max(0, latest_age_ms)
    except (TypeError, ValueError) as exc:
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol,
            route=route,
            error=f"{exc}",
        )

    return EntryExecutionVelocitySnapshot(
        source_ok=True,
        symbol=expected_code,
        route=normalized_route,
        request_code=request_code,
        print_count=len(times),
        recent_print_span_ms=(seconds[0] - seconds[-1]) * 1_000,
        latest_print_age_ms=latest_age_ms,
        recent_volume=sum(volumes),
        observed_at_kst=observed.isoformat(),
        print_times=tuple(times),
        venues=tuple(venues),
    )


def parse_ka10004_entry_liquidity_snapshot(
    payload: object, *, symbol: str, route: str
) -> EntryLiquiditySnapshot:
    """Validate normalized ``get_stock_orderbook_ka10004`` output."""

    try:
        expected_code = kiwoom_utils.normalize_stock_code(symbol)
        expected_request_code = entry_liquidity_request_code(symbol, route)
    except ValueError as exc:
        return unavailable_entry_liquidity_snapshot(
            symbol=symbol, route=route, error=str(exc)
        )
    if not isinstance(payload, dict):
        return unavailable_entry_liquidity_snapshot(
            symbol=symbol, route=route, error="ka10004_payload_invalid"
        )
    try:
        best_bid = _positive_int(payload.get("best_bid"))
        best_ask = _positive_int(payload.get("best_ask"))
        best_bid_qty = _nonnegative_int(payload.get("best_bid_qty"))
        best_ask_qty = _nonnegative_int(payload.get("best_ask_qty"))
        bid_total_qty = _nonnegative_int(payload.get("bid_tot", 0))
        ask_total_qty = _nonnegative_int(payload.get("ask_tot", 0))
        age_ms = _nonnegative_int(payload.get("rest_age_ms"))
        received_ts_ms = _positive_int(payload.get("rest_received_ts_ms"))
    except (TypeError, ValueError) as exc:
        return unavailable_entry_liquidity_snapshot(
            symbol=symbol,
            route=route,
            error=f"ka10004_numeric_contract_invalid:{type(exc).__name__}",
        )
    source = str(payload.get("source") or "").strip()
    stock_code = kiwoom_utils.normalize_stock_code(str(payload.get("stock_code") or ""))
    request_code = str(payload.get("request_code") or "").strip().upper()
    time_basis = str(payload.get("rest_freshness_basis") or "").strip()
    contract_error = ""
    if source != "ka10004_rest_orderbook":
        contract_error = "ka10004_source_contract_invalid"
    elif stock_code != expected_code:
        contract_error = "ka10004_symbol_contract_invalid"
    elif request_code != expected_request_code:
        contract_error = "ka10004_route_contract_invalid"
    elif time_basis != "response_received_epoch_ms":
        contract_error = "ka10004_freshness_contract_invalid"
    elif best_ask < best_bid:
        contract_error = "ka10004_crossed_book_invalid"
    return EntryLiquiditySnapshot(
        source_ok=not contract_error,
        symbol=expected_code,
        route=str(route or "").strip().upper(),
        request_code=expected_request_code,
        source=source or "ka10004_rest_orderbook",
        best_bid=best_bid,
        best_ask=best_ask,
        best_bid_qty=best_bid_qty,
        best_ask_qty=best_ask_qty,
        bid_total_qty=bid_total_qty,
        ask_total_qty=ask_total_qty,
        age_ms=age_ms,
        received_ts_ms=received_ts_ms,
        error=contract_error,
    )


def evaluate_entry_liquidity(
    snapshot: EntryLiquiditySnapshot, *, requested_quantity: int
) -> EntryLiquidityDecision:
    requested = _positive_int(requested_quantity)
    required = max(
        MIN_TOUCH_QUANTITY_EACH_SIDE,
        requested * REQUEST_QUANTITY_MULTIPLIER,
    )
    if not snapshot.source_ok:
        reason = snapshot.error or "entry_liquidity_source_unavailable"
        allowed = False
    elif snapshot.age_ms > MAX_SNAPSHOT_AGE_MS:
        reason = "entry_liquidity_snapshot_stale"
        allowed = False
    elif snapshot.best_bid_qty < required or snapshot.best_ask_qty < required:
        reason = "entry_liquidity_touch_depth_insufficient"
        allowed = False
    else:
        reason = "entry_liquidity_touch_depth_sufficient"
        allowed = True
    return EntryLiquidityDecision(
        allowed=allowed,
        reason=reason,
        requested_quantity=requested,
        required_each_side_quantity=required,
        snapshot=snapshot,
    )


def evaluate_entry_execution_velocity(
    snapshot: EntryExecutionVelocitySnapshot, *, requested_quantity: int
) -> EntryExecutionVelocityDecision:
    requested = _positive_int(requested_quantity)
    required_recent_volume = max(
        MIN_RECENT_PRINT_VOLUME,
        requested * RECENT_VOLUME_QUANTITY_MULTIPLIER,
    )
    if not snapshot.source_ok:
        reason = snapshot.error or "entry_execution_velocity_source_unavailable"
        allowed = False
    elif snapshot.print_count < REQUIRED_RECENT_PRINT_COUNT:
        reason = "entry_execution_velocity_print_count_insufficient"
        allowed = False
    elif snapshot.latest_print_age_ms > MAX_LATEST_PRINT_AGE_MS:
        reason = "entry_execution_velocity_latest_print_stale"
        allowed = False
    elif snapshot.recent_print_span_ms > MAX_RECENT_PRINT_SPAN_MS:
        reason = "entry_execution_velocity_too_slow"
        allowed = False
    elif snapshot.recent_volume < required_recent_volume:
        reason = "entry_execution_velocity_volume_insufficient"
        allowed = False
    else:
        reason = "entry_execution_velocity_sufficient"
        allowed = True
    return EntryExecutionVelocityDecision(
        allowed=allowed,
        reason=reason,
        requested_quantity=requested,
        required_recent_volume=required_recent_volume,
        snapshot=snapshot,
    )
