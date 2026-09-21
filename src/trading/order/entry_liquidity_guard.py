"""Fresh touch-depth and execution-velocity guards for new buy authority.

The guards are deliberately owner-neutral.  They evaluate one fresh Kiwoom
``ka10004`` snapshot and the latest ``ka10003`` prints but never submit,
cancel, reprice, or exit an order.  Each trading owner remains responsible for
recording its own decision and for keeping already-owned positions and target
orders unchanged.
"""

from __future__ import annotations

import math
import re
import time
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.utils import kiwoom_utils
from src.trading.market.quote_consistency import build_market_data_health, build_rest_market_data_health

ENTRY_LIQUIDITY_POLICY_ID = "entry_touch_liquidity_guard_v1"
MIN_TOUCH_QUANTITY_EACH_SIDE = 100
REQUEST_QUANTITY_MULTIPLIER = 5
MAX_SNAPSHOT_AGE_MS = 2_000
ENTRY_EXECUTION_VELOCITY_POLICY_ID = "entry_execution_velocity_guard_v1"
EXECUTABLE_MICRO_CONFIRMATION_POLICY_ID = "entry_executable_micro_confirmation_v1"
EXECUTABLE_MICRO_CONFIRMATION_MODE = (
    "supportive_non_deteriorating_bbo_positive_net_edge_v1"
)
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

EXECUTABLE_MICRO_CONFIRMATION_POLICY_CONTRACT = {
    "metric_role": "exact_date_delayed_entry_executable_micro_confirmation",
    "decision_authority": "block_selected_widget_or_episode_new_buy_only",
    "window_policy": "selected_delay_anchor_to_due_point_fresh_bbo",
    "sample_floor": (
        "exact_date_entry_timing_policy_with_supportive_0b_0d_and_positive_"
        "cost_adjusted_ev"
    ),
    "primary_decision_metric": "entry_ask_to_owner_target_modeled_net_edge_pct",
    "source_quality_gate": (
        "exact_symbol_route;fresh_anchor_and_due_ka10004;non_deteriorating_bbo;"
        "owner_target_above_due_ask_after_effective_cost"
    ),
    "forbidden_uses": [
        "standalone_signal_creation",
        "same_day_or_unselected_scope_activation",
        "price_quantity_target_exit_or_stop_mutation",
        "sell_cancel_reprice_or_existing_custody_authority",
        "main_bot_order_authority",
        "broker_guard_or_hard_safety_bypass",
        "missing_bbo_or_cost_imputation",
        "broker_receipt_exact_cost_claim",
    ],
}

KIWOOM_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "953e5dbff123f437ab4d11a78a95191a685eb51f",
    "retrieved_at_kst": "2026-09-17T11:23:49+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core/client.py",
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


def _source_policy_contract(contract, source):
    result = deepcopy(contract)
    if source == "kiwoom_ws_orderbook":
        result.update(sample_floor="one_route_qualified_0D_snapshot_per_submit_bundle",
                      source_quality_gate="exact_item_epoch_live_producer;original_receive_age_lte_2000ms;positive_uncrossed_bbo;nonnegative_touch_quantities")
    elif source == "kiwoom_ws_trade_prints":
        result.update(sample_floor="10_route_qualified_0B_trade_prints",
                      source_quality_gate="exact_item_epoch_live_producer;original_receive_and_provider_clocks;latest_print_age_lte_5000ms;local_sequence_contiguous_not_exchange_completeness;strictly_descending_accumulated_trade_quantity;positive_price_and_absolute_trade_quantity")
    return result


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
    market_data_health: dict[str, Any] = field(default_factory=dict)
    source_meta: dict[str, Any] = field(default_factory=dict)


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
            "entry_liquidity_policy_contract": _source_policy_contract(
                ENTRY_LIQUIDITY_POLICY_CONTRACT, self.snapshot.source
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
    source_meta: dict[str, Any] = field(default_factory=dict)
    response_item_raw: str = ""
    market_data_health: dict[str, Any] = field(default_factory=dict)


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
            "entry_execution_velocity_policy_contract": _source_policy_contract(
                ENTRY_EXECUTION_VELOCITY_POLICY_CONTRACT, self.snapshot.source
            ),
            "entry_execution_velocity_snapshot": asdict(self.snapshot),
        }


@dataclass(frozen=True)
class ExecutableMicroConfirmationDecision:
    allowed: bool
    reason: str
    requested_quantity: int
    reference_price: int
    maximum_entry_price: int
    target_price: int
    round_trip_cost_pct: float | None
    modeled_gross_edge_pct: float | None
    modeled_net_edge_pct: float | None
    anchor_snapshot: EntryLiquiditySnapshot | None
    current_snapshot: EntryLiquiditySnapshot | None
    policy_id: str = EXECUTABLE_MICRO_CONFIRMATION_POLICY_ID

    def event_fields(self) -> dict[str, Any]:
        return {
            "entry_executable_micro_confirmation_policy_id": self.policy_id,
            "entry_executable_micro_confirmation_allowed": self.allowed,
            "entry_executable_micro_confirmation_reason": self.reason,
            "entry_executable_micro_confirmation_requested_quantity": (
                self.requested_quantity
            ),
            "entry_executable_micro_confirmation_reference_price": (
                self.reference_price
            ),
            "entry_executable_micro_confirmation_maximum_entry_price": (
                self.maximum_entry_price
            ),
            "entry_executable_micro_confirmation_target_price": self.target_price,
            "entry_executable_micro_confirmation_round_trip_cost_pct": (
                self.round_trip_cost_pct
            ),
            "entry_executable_micro_confirmation_broker_receipt_exact": False,
            "entry_executable_micro_confirmation_modeled_gross_edge_pct": (
                self.modeled_gross_edge_pct
            ),
            "entry_executable_micro_confirmation_modeled_net_edge_pct": (
                self.modeled_net_edge_pct
            ),
            "entry_executable_micro_confirmation_anchor_snapshot": (
                asdict(self.anchor_snapshot) if self.anchor_snapshot else None
            ),
            "entry_executable_micro_confirmation_current_snapshot": (
                asdict(self.current_snapshot) if self.current_snapshot else None
            ),
            "entry_executable_micro_confirmation_policy_contract": deepcopy(
                EXECUTABLE_MICRO_CONFIRMATION_POLICY_CONTRACT
            ),
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
    source_meta: dict[str, Any] = {}
    market_health: dict[str, Any] = {}
    response_item = ""
    receipt_present = any("_kiwoom_source_meta" in tick for tick in payload[:REQUIRED_RECENT_PRINT_COUNT] if isinstance(tick, dict))
    try:
        for tick in payload[:REQUIRED_RECENT_PRINT_COUNT]:
            if not isinstance(tick, dict) or not isinstance(tick.get("raw"), dict):
                raise ValueError("ka10003_trade_row_invalid")
            raw = tick["raw"]
            if receipt_present:
                meta = tick.get("_kiwoom_source_meta")
                if not isinstance(meta, dict):
                    raise ValueError("ka10003_receive_receipt_missing_or_invalid")
                health = build_rest_market_data_health(
                    {"stk_cd": tick.get("response_item_raw")}, api_id="ka10003",
                    request_code=request_code, source_meta=meta, now_ts=observed.timestamp(),
                )
                facts = health["rest_input"]
                age = facts["response_receive_age_ms"]
                if facts["receipt_binding_proven"] is not True or age is None or age < 0:
                    raise ValueError("ka10003_receive_receipt_scope_or_clock_invalid")
                if source_meta and meta != source_meta:
                    raise ValueError("ka10003_receive_receipt_packet_conflict")
                source_meta = deepcopy(meta)
                market_health = health
                response_item = str(tick.get("response_item_raw") or "")
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
            observed_seconds - seconds[0]
        ) * 1_000 + observed.microsecond // 1_000
        receive_order_valid = True
        if source_meta:
            received = datetime.fromtimestamp(source_meta["rest_received_ts_ms"] / 1000, tz=KST)
            received_seconds = received.hour * 3600 + received.minute * 60 + received.second
            # A cached/reused response must not cure a clock conflict merely
            # because consumption waited until its future print time.
            receive_order_valid = received_seconds >= seconds[0]
        if latest_age_ms < -MAX_EVENT_CLOCK_SKEW_MS:
            raise ValueError("ka10003_latest_trade_time_in_future")
    except (TypeError, ValueError) as exc:
        return unavailable_entry_execution_velocity_snapshot(
            symbol=symbol,
            route=route,
            error=f"{exc}",
        )

    return EntryExecutionVelocitySnapshot(
        source_ok=latest_age_ms >= 0 and receive_order_valid,
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
        source_meta=source_meta,
        response_item_raw=response_item,
        market_data_health=market_health,
        error="" if latest_age_ms >= 0 and receive_order_valid else "ka10003_latest_trade_time_in_future",
    )


def parse_ka10004_entry_liquidity_snapshot(
    payload: object, *, symbol: str, route: str, now_ts: float | None = None
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
    except (TypeError, ValueError, OverflowError) as exc:
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
    health = build_market_data_health(
        payload,
        now_ts=time.time() if now_ts is None else now_ts,
        quote_max_age_ms=MAX_SNAPSHOT_AGE_MS,
    )
    rest = health.get("rest_quote") or {}
    measured_age = rest.get("quote_receive_age_ms")
    if not contract_error and rest.get("quote_state") in {
        "future",
        "missing",
        "unproven",
        "invalid",
    }:
        contract_error = "ka10004_receive_clock_or_quote_contract_invalid"
    if measured_age is not None and measured_age >= 0:
        age_ms = max(age_ms, math.ceil(measured_age))
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
        market_data_health=health,
    )


def _refresh_liquidity_snapshot(
    snapshot: EntryLiquiditySnapshot, *, now_ts: float | None = None
) -> EntryLiquiditySnapshot:
    """Recompute quote facts at the decision, never tape inactivity/authority."""
    if snapshot.source == "kiwoom_ws_orderbook":
        from src.trading.market.entry_ws_snapshot import validate_receipt
        try:
            age = validate_receipt(snapshot.source_meta, symbol=snapshot.symbol, route=snapshot.route,
                                   now_ts=time.time() if now_ts is None else now_ts)
            if (snapshot.source_meta.get("realtime_type") != "0D"
                    or any(type(v) is not int or v < 0 for v in (snapshot.age_ms, snapshot.received_ts_ms, snapshot.best_bid, snapshot.best_ask, snapshot.best_bid_qty, snapshot.best_ask_qty))
                    or snapshot.best_bid <= 0 or snapshot.best_ask < snapshot.best_bid):
                raise ValueError("ws_quote_contract_invalid")
            return replace(snapshot, age_ms=max(snapshot.age_ms, age))
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
            return replace(snapshot, source_ok=False, error=snapshot.error or "ws_quote_receipt_invalid")
    health = build_market_data_health(
        {
            "source": snapshot.source,
            "stock_code": snapshot.symbol,
            "request_code": snapshot.request_code,
            "rest_freshness_basis": "response_received_epoch_ms",
            "rest_received_ts_ms": snapshot.received_ts_ms,
            "best_bid": snapshot.best_bid,
            "best_ask": snapshot.best_ask,
        },
        now_ts=time.time() if now_ts is None else now_ts,
        quote_max_age_ms=MAX_SNAPSHOT_AGE_MS,
    )
    rest = health.get("rest_quote") or {}
    age = rest.get("quote_receive_age_ms")
    try:
        scope_valid = snapshot.request_code == entry_liquidity_request_code(
            snapshot.symbol, snapshot.route
        )
    except ValueError:
        scope_valid = False
    invalid = (
        rest.get("quote_state") not in {"fresh", "stale"}
        or type(snapshot.age_ms) is not int
        or snapshot.age_ms < 0
        or any(
            type(value) is not int or value < 0
            for value in (
                snapshot.best_bid,
                snapshot.best_ask,
                snapshot.best_bid_qty,
                snapshot.best_ask_qty,
                snapshot.received_ts_ms,
            )
        )
        or not scope_valid
    )
    recorded_age = (
        snapshot.age_ms if type(snapshot.age_ms) is int and snapshot.age_ms >= 0 else 0
    )
    return replace(
        snapshot,
        source_ok=snapshot.source_ok is True and not invalid,
        age_ms=(
            max(recorded_age, math.ceil(age))
            if age is not None and age >= 0
            else recorded_age
        ),
        error=snapshot.error
        or ("ka10004_receive_clock_or_quote_contract_invalid" if invalid else ""),
        market_data_health=health,
    )


def evaluate_entry_liquidity(
    snapshot: EntryLiquiditySnapshot,
    *,
    requested_quantity: int,
    now_ts: float | None = None,
) -> EntryLiquidityDecision:
    snapshot = _refresh_liquidity_snapshot(snapshot, now_ts=now_ts)
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


def _coerce_liquidity_snapshot(
    value: EntryLiquiditySnapshot | Mapping[str, Any] | None,
) -> EntryLiquiditySnapshot | None:
    if isinstance(value, EntryLiquiditySnapshot):
        raw: Mapping[str, Any] = asdict(value)
    elif isinstance(value, Mapping):
        raw = value
    else:
        return None

    def contract_int(field: str, default: object | None = None) -> int:
        candidate = raw.get(field, default)
        if isinstance(candidate, bool):
            raise ValueError(f"boolean_is_not_{field}")
        return int(candidate)

    try:
        return EntryLiquiditySnapshot(
            source_ok=raw.get("source_ok") is True,
            symbol=str(raw.get("symbol") or ""),
            route=str(raw.get("route") or "").upper(),
            request_code=str(raw.get("request_code") or ""),
            source=str(raw.get("source") or "ka10004_rest_orderbook"),
            best_bid=contract_int("best_bid"),
            best_ask=contract_int("best_ask"),
            best_bid_qty=contract_int("best_bid_qty"),
            best_ask_qty=contract_int("best_ask_qty"),
            bid_total_qty=contract_int("bid_total_qty", 0),
            ask_total_qty=contract_int("ask_total_qty", 0),
            age_ms=contract_int("age_ms", 0),
            received_ts_ms=contract_int("received_ts_ms"),
            error=str(raw.get("error") or ""),
            market_data_health=deepcopy(raw.get("market_data_health", {})),
            source_meta=deepcopy(raw.get("source_meta", {})),
        )
    except (TypeError, ValueError, OverflowError):
        return None


def evaluate_executable_micro_confirmation(
    *,
    anchor_snapshot: EntryLiquiditySnapshot | Mapping[str, Any] | None,
    current_snapshot: EntryLiquiditySnapshot | Mapping[str, Any] | None,
    requested_quantity: int,
    reference_price: int,
    maximum_entry_price: int,
    target_price: int,
    policy: Mapping[str, Any] | None,
    now_ts: float | None = None,
) -> ExecutableMicroConfirmationDecision:
    """Confirm one selected delayed entry without creating a new signal.

    The exact-date timing policy is selected from supportive 0B/0D and
    cost-adjusted completed outcomes.  At the due point this guard requires a
    fresh executable book that has not deteriorated from the signal anchor and
    still leaves positive owner-target edge after the policy-pinned comparison
    cost.  Missing source or policy evidence always blocks the selected entry.
    """

    try:
        requested = _positive_int(requested_quantity)
    except (TypeError, ValueError):
        requested = 0
    try:
        reference = _positive_int(reference_price)
    except (TypeError, ValueError):
        reference = 0
    try:
        maximum_entry = _positive_int(maximum_entry_price)
    except (TypeError, ValueError):
        maximum_entry = 0
    try:
        target = _positive_int(target_price)
    except (TypeError, ValueError):
        target = 0
    anchor = _coerce_liquidity_snapshot(anchor_snapshot)
    current = _coerce_liquidity_snapshot(current_snapshot)
    if current is not None:
        current = _refresh_liquidity_snapshot(current, now_ts=now_ts)
    cost_pct: float | None = None
    if isinstance(policy, Mapping):
        raw_cost = policy.get("round_trip_cost_pct")
        try:
            parsed_cost = float(raw_cost)
        except (TypeError, ValueError):
            parsed_cost = math.nan
        if (
            not isinstance(raw_cost, bool)
            and math.isfinite(parsed_cost)
            and parsed_cost >= 0
        ):
            cost_pct = parsed_cost

    gross_edge_pct: float | None = None
    net_edge_pct: float | None = None
    reason = "entry_executable_micro_confirmation_passed"
    if (
        not isinstance(policy, Mapping)
        or policy.get("mode") != EXECUTABLE_MICRO_CONFIRMATION_MODE
        or policy.get("supportive_confirmation_only") is not True
        or policy.get("require_bid_non_deterioration") is not True
        or policy.get("require_ask_non_deterioration") is not True
        or policy.get("require_positive_net_edge_after_costs") is not True
        or policy.get("broker_receipt_exact") is not False
        or cost_pct is None
    ):
        reason = "entry_executable_micro_confirmation_policy_invalid"
    elif requested <= 0 or reference <= 0:
        reason = "entry_executable_micro_confirmation_input_invalid"
    elif anchor is None:
        reason = "entry_executable_micro_confirmation_anchor_missing"
    elif current is None:
        reason = "entry_executable_micro_confirmation_current_missing"
    elif not anchor.source_ok:
        reason = anchor.error or "entry_executable_micro_confirmation_anchor_invalid"
    elif not current.source_ok:
        reason = current.error or "entry_executable_micro_confirmation_current_invalid"
    elif (
        anchor.best_bid <= 0
        or anchor.best_ask <= 0
        or anchor.best_ask < anchor.best_bid
        or anchor.best_bid_qty < 0
        or anchor.best_ask_qty < 0
        or anchor.age_ms < 0
        or anchor.received_ts_ms <= 0
    ):
        reason = "entry_executable_micro_confirmation_anchor_contract_invalid"
    elif (
        current.best_bid <= 0
        or current.best_ask <= 0
        or current.best_ask < current.best_bid
        or current.best_bid_qty < 0
        or current.best_ask_qty < 0
        or current.age_ms < 0
        or current.received_ts_ms <= 0
    ):
        reason = "entry_executable_micro_confirmation_current_contract_invalid"
    elif anchor.age_ms > MAX_SNAPSHOT_AGE_MS:
        reason = "entry_executable_micro_confirmation_anchor_stale"
    elif current.age_ms > MAX_SNAPSHOT_AGE_MS:
        reason = "entry_executable_micro_confirmation_current_stale"
    elif (
        anchor.symbol != current.symbol
        or anchor.route != current.route
        or anchor.request_code != current.request_code
    ):
        reason = "entry_executable_micro_confirmation_scope_mismatch"
    elif current.received_ts_ms < anchor.received_ts_ms:
        reason = "entry_executable_micro_confirmation_time_regression"
    elif current.best_bid < anchor.best_bid:
        reason = "entry_executable_micro_confirmation_bid_deteriorated"
    elif current.best_ask > anchor.best_ask:
        reason = "entry_executable_micro_confirmation_ask_deteriorated"
    elif current.best_ask_qty < requested:
        reason = "entry_executable_micro_confirmation_ask_depth_insufficient"
    elif maximum_entry <= 0 or current.best_ask > maximum_entry:
        reason = "entry_executable_micro_confirmation_not_executable_at_owner_limit"
    elif target <= current.best_ask:
        reason = "entry_executable_micro_confirmation_target_not_above_ask"
    else:
        gross_edge_pct = (target / current.best_ask - 1.0) * 100.0
        net_edge_pct = gross_edge_pct - cost_pct
        if net_edge_pct <= 0:
            reason = "entry_executable_micro_confirmation_nonpositive_net_edge"

    return ExecutableMicroConfirmationDecision(
        allowed=reason == "entry_executable_micro_confirmation_passed",
        reason=reason,
        requested_quantity=requested,
        reference_price=reference,
        maximum_entry_price=maximum_entry,
        target_price=target,
        round_trip_cost_pct=cost_pct,
        modeled_gross_edge_pct=(
            round(gross_edge_pct, 8) if gross_edge_pct is not None else None
        ),
        modeled_net_edge_pct=(
            round(net_edge_pct, 8) if net_edge_pct is not None else None
        ),
        anchor_snapshot=anchor,
        current_snapshot=current,
    )


def evaluate_entry_execution_velocity(
    snapshot: EntryExecutionVelocitySnapshot, *, requested_quantity: int,
    now_ts: float | None = None,
) -> EntryExecutionVelocityDecision:
    # Revalidate the original successful response, not the carried health age.
    # Legacy declared print fixtures retain their existing receive-window adapter.
    if snapshot.source == "kiwoom_ws_trade_prints":
        from src.trading.market.entry_ws_snapshot import validate_receipt
        try:
            consumed = time.time() if now_ts is None else now_ts
            age = validate_receipt(snapshot.source_meta, symbol=snapshot.symbol, route=snapshot.route, now_ts=consumed)
            event_age = math.ceil((consumed - snapshot.source_meta["provider_latest_epoch"]) * 1000)
            if (snapshot.source_meta.get("realtime_type") != "0B" or event_age < 0 or age > MAX_LATEST_PRINT_AGE_MS
                    or any(type(v) is not int or v < 0 for v in (snapshot.print_count, snapshot.recent_volume, snapshot.latest_print_age_ms, snapshot.recent_print_span_ms))):
                raise ValueError("ws_trade_clock_invalid")
            snapshot = replace(snapshot, latest_print_age_ms=max(snapshot.latest_print_age_ms, event_age))
        except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
            snapshot = replace(snapshot, source_ok=False, error=snapshot.error or "ws_trade_receipt_invalid")
    elif snapshot.source_meta:
        consumed = time.time() if now_ts is None else now_ts
        health = build_rest_market_data_health(
            {"stk_cd": snapshot.response_item_raw}, api_id="ka10003",
            request_code=snapshot.request_code, source_meta=snapshot.source_meta, now_ts=consumed,
        )
        facts = health["rest_input"]
        age = facts["response_receive_age_ms"]
        try:
            evaluated = datetime.fromisoformat(snapshot.observed_at_kst)
            if evaluated.tzinfo is None:
                raise ValueError("velocity_consume_timezone_missing")
            lag_ms = (consumed - evaluated.timestamp()) * 1000
            if not math.isfinite(lag_ms) or lag_ms < 0:
                raise ValueError("velocity_consume_clock_invalid")
            valid = facts["receipt_binding_proven"] is True and age is not None and 0 <= age <= MAX_LATEST_PRINT_AGE_MS
            snapshot = replace(snapshot, source_ok=snapshot.source_ok and valid,
                               latest_print_age_ms=snapshot.latest_print_age_ms + math.ceil(lag_ms),
                               market_data_health=health,
                               error=snapshot.error if valid else "ka10003_receive_receipt_scope_or_clock_invalid")
        except (ValueError, TypeError, OverflowError):
            snapshot = replace(snapshot, source_ok=False, market_data_health=health,
                               error="ka10003_consume_clock_invalid")
    requested = _positive_int(requested_quantity)
    required_recent_volume = max(
        MIN_RECENT_PRINT_VOLUME,
        requested * RECENT_VOLUME_QUANTITY_MULTIPLIER,
    )
    if not snapshot.source_ok:
        reason = snapshot.error or "entry_execution_velocity_source_unavailable"
        allowed = False
    elif snapshot.latest_print_age_ms < 0:
        reason = "ka10003_latest_trade_time_in_future"
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
