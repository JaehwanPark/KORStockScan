"""Event-time, source-bound strength selection for scalping take profit.

This module chooses a trailing width. It never selects an order, price, stop,
or provider. Its input is the already subscribed, bounded 0B/0D WS history.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping


VERSION = "mechanical_strength_v2"
TRADE_WINDOW_MS = 1_000
HISTORY_LIMIT = 120

CONFIG_DEFAULTS = {
    "trade_window_ms": 1000,
    "strong_queue_min": 0.0,
    "strong_ofi_min": 0.0,
    "strong_signed_qty_min": 0,
    "weak_queue_negative_min": 0.0,
    "weak_ofi_negative_min": 0.0,
    "weak_signed_qty_negative_min": 0,
    "adverse_updates_required": 2,
}


def normalize_config(raw: Mapping[str, Any]) -> dict[str, int | float]:
    """Validate the eight bounded policy knobs without coercing strings or bools."""

    if not isinstance(raw, Mapping) or set(raw) != set(CONFIG_DEFAULTS):
        raise ValueError("classifier_config_keys_invalid")
    result: dict[str, int | float] = {}
    for key, default in CONFIG_DEFAULTS.items():
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"classifier_config_{key}_type_invalid")
        if isinstance(default, int):
            if not float(value).is_integer():
                raise ValueError(f"classifier_config_{key}_integer_required")
            value = int(value)
        else:
            value = float(value)
        result[key] = value
    if result["trade_window_ms"] not in (500, 1000):
        raise ValueError("classifier_trade_window_out_of_range")
    if result["adverse_updates_required"] not in (2, 3):
        raise ValueError("classifier_adverse_updates_out_of_range")
    if any(result[key] not in (0.0, 0.1) for key in (
        "strong_queue_min", "strong_ofi_min", "weak_queue_negative_min", "weak_ofi_negative_min"
    )) or any(result[key] not in (0, 10) for key in (
        "strong_signed_qty_min", "weak_signed_qty_negative_min"
    )):
        raise ValueError("classifier_threshold_out_of_range")
    return result


@dataclass(frozen=True)
class StrengthDecision:
    state: str
    reason: str
    ofi_proxy: float | None
    queue_imbalance: float | None
    signed_trade_qty: int | None
    quote_sequence: int | None
    quote_received_at_ms: int | None
    trade_received_at_ms: int | None
    source_item: str | None
    transport_epoch: int | None
    new_observations: tuple[dict[str, Any], ...] = ()

    @property
    def strong(self) -> bool:
        return self.state == "STRONG"


def _nonnegative_int(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        return None
    return int(number)


def _positive_int(raw: Any) -> int | None:
    number = _nonnegative_int(raw)
    return number if number and number > 0 else None


def _touch(row: Mapping[str, Any]) -> tuple[int, int, int, int] | None:
    bids = row.get("bid_levels")
    asks = row.get("ask_levels")
    if not isinstance(bids, list) or not isinstance(asks, list) or not bids or not asks:
        return None
    bid = bids[0]
    ask = asks[0]
    if not isinstance(bid, Mapping) or not isinstance(ask, Mapping):
        return None
    bp, bq = _positive_int(bid.get("price")), _nonnegative_int(bid.get("quantity"))
    ap, aq = _positive_int(ask.get("price")), _nonnegative_int(ask.get("quantity"))
    if bp is None or bq is None or ap is None or aq is None or bp > ap or bq + aq <= 0:
        return None
    return bp, bq, ap, aq


def _ofi(previous: tuple[int, int, int, int], current: tuple[int, int, int, int]) -> float:
    bp0, bq0, ap0, aq0 = previous
    bp1, bq1, ap1, aq1 = current
    bid = bq1 if bp1 > bp0 else bq1 - bq0 if bp1 == bp0 else -bq0
    ask = aq1 if ap1 < ap0 else aq1 - aq0 if ap1 == ap0 else -aq0
    return (bid - ask) / max(1, bq0 + aq0)


def _rows_by_item(source: Any, item: str, epoch: int, route_key: str) -> list[dict[str, Any]]:
    rows = []
    if not isinstance(source, Mapping):
        return rows
    for key, bucket in source.items():
        if str(key) != route_key:
            continue
        if not isinstance(bucket, (list, tuple)):
            continue
        for row in bucket[:HISTORY_LIMIT]:
            if not isinstance(row, dict):
                continue
            if str(row.get("item") or "").upper() != item:
                continue
            if _nonnegative_int(row.get("transport_epoch")) != epoch:
                continue
            at = _positive_int(row.get("received_at_ms"))
            seq = _positive_int(row.get("route_sequence"))
            if at is None or seq is None:
                continue
            rows.append(row)
    return sorted(rows, key=lambda row: int(row["route_sequence"]))


def _signed_tape(
    trades: list[dict[str, Any]], *, at_ms: int, min_sequence_exclusive: int,
    window_ms: int = TRADE_WINDOW_MS,
) -> tuple[int | None, int | None, list[dict[str, Any]], str | None]:
    net = 0
    latest = None
    receipts = []
    if (len(trades) >= HISTORY_LIMIT
            and _positive_int(trades[0].get("received_at_ms")) is not None
            and int(trades[0]["received_at_ms"]) > at_ms - window_ms):
        return None, None, [], "trade_window_capacity_gap"
    previous_sequence = None
    previous_at = None
    for row in trades:
        received = _positive_int(row.get("received_at_ms"))
        sequence = _positive_int(row.get("route_sequence"))
        if sequence is None or sequence <= min_sequence_exclusive:
            continue
        if received is None or not at_ms - window_ms <= received <= at_ms:
            continue
        if (previous_sequence is not None
                and (sequence != previous_sequence + 1 or received < previous_at)):
            return None, None, [], "trade_sequence_or_time_gap"
        previous_sequence, previous_at = sequence, received
        if row.get("aggressor_source") != "kiwoom_0b_signed_trade_volume":
            return None, None, [], "trade_direction_unverified"
        if row.get("aggressor_quality") not in {
            "signed_trade_volume_positive", "signed_trade_volume_negative"
        }:
            return None, None, [], "trade_direction_unverified"
        qty = _positive_int(row.get("volume"))
        side = str(row.get("aggressor_side") or "")
        if qty is None or side not in {"BUY", "SELL"}:
            return None, None, [], "trade_quantity_or_side_invalid"
        receipts.append({"sequence": sequence, "received_at_ms": received,
                         "side": side, "qty": qty,
                         "source": row["aggressor_source"],
                         "quality": row["aggressor_quality"]})
        net += qty if side == "BUY" else -qty
        latest = received
    return (net if receipts else None), latest, receipts, None


def _trade_peak_since(
    trades: list[dict[str, Any]], *, after_sequence: int, at_ms: int,
) -> tuple[int | None, int, list[dict[str, int]], str | None]:
    """Advance a separate 0B price cursor without filling missing messages."""

    peak = 0
    cursor = after_sequence
    previous_at = None
    receipts = []
    for row in trades:
        sequence = _positive_int(row.get("route_sequence"))
        received = _positive_int(row.get("received_at_ms"))
        if sequence is None or received is None or sequence <= cursor or received > at_ms:
            continue
        price = _positive_int(row.get("price"))
        if (sequence != cursor + 1 or price is None
                or (previous_at is not None and received < previous_at)):
            return None, cursor, [], "trade_peak_sequence_price_or_time_gap"
        peak = max(peak, price)
        receipts.append({"sequence": sequence, "received_at_ms": received,
                         "price": price})
        cursor, previous_at = sequence, received
    return peak, cursor, receipts, None


def classify_ws_history(
    ws_data: Mapping[str, Any], previous_state: Mapping[str, Any] | None,
    *, now_ms: int, max_quote_age_ms: int, market: str | None = None,
    config: Mapping[str, Any] | None = None,
) -> tuple[StrengthDecision, dict[str, Any]]:
    """Advance once per unseen 0D event; never fill a missing event or trade.

    The returned state is position-local. A new item/transport epoch resets it.
    A route/market change or sequence gap resets strength; first observation is
    a baseline only.
    """

    params = normalize_config(config if config is not None else CONFIG_DEFAULTS)
    type_items = ws_data.get("last_realtime_type_item") or {}
    item = str(type_items.get("0D") or "").strip().upper() if isinstance(type_items, Mapping) else ""
    epoch = _nonnegative_int(ws_data.get("market_data_transport_epoch"))
    type_routes = ws_data.get("last_realtime_type_market_route") or {}
    type_suffixes = ws_data.get("last_realtime_type_market_suffix") or {}
    route = str(type_routes.get("0D") or "").strip() if isinstance(type_routes, Mapping) else ""
    trade_route = str(type_routes.get("0B") or "").strip() if isinstance(type_routes, Mapping) else ""
    suffix = str(type_suffixes.get("0D") or "KRX").strip() if isinstance(type_suffixes, Mapping) else ""
    trade_suffix = str(type_suffixes.get("0B") or "KRX").strip() if isinstance(type_suffixes, Mapping) else ""
    if (not item or epoch is None or not route or route != trade_route
            or suffix != trade_suffix
            or str(type_items.get("0B") or "").strip().upper() != item):
        return StrengthDecision("UNKNOWN", "source_identity_missing", None, None, None,
                                None, None, None, item or None, epoch), {}
    route_key = f"{suffix}|{route}"
    old = dict(previous_state or {})
    reset = (old.get("item") != item or old.get("epoch") != epoch
             or old.get("route_key") != route_key
             or old.get("market") != market
             or old.get("config") != params)
    if reset:
        old = {"item": item, "epoch": epoch, "route_key": route_key,
               "market": market, "strong": False,
               "config": params, "last_depth_seq": None, "last_touch": None,
               "adverse_count": 0}
    depths = _rows_by_item(ws_data.get("recent_depth_ticks_by_route"), item, epoch, route_key)
    trades = _rows_by_item(ws_data.get("recent_trade_ticks_by_route"), item, epoch, route_key)
    if reset:
        # The buffer may predate this position or this process. Take a baseline
        # and wait for fresh events instead of promoting from pre-entry history.
        if depths:
            latest = depths[-1]
            old["last_depth_seq"] = _positive_int(latest.get("route_sequence"))
            old["last_depth_at_ms"] = _positive_int(latest.get("received_at_ms"))
            old["last_touch"] = _touch(latest)
        old["first_trade_seq"] = max(
            (_positive_int(row.get("route_sequence")) or 0 for row in trades),
            default=0,
        )
        old["last_peak_trade_seq"] = old["first_trade_seq"]
        return StrengthDecision(
            "UNKNOWN", "position_or_transport_baseline", None, None, None,
            old.get("last_depth_seq"), old.get("last_depth_at_ms"), None,
            item, epoch,
        ), old
    last_seq = _positive_int(old.get("last_depth_seq"))
    last_touch = old.get("last_touch")
    if not isinstance(last_touch, tuple) or len(last_touch) != 4:
        last_touch = None
    strength = bool(old.get("strong"))
    adverse = int(old.get("adverse_count") or 0)
    observations = []
    reason = "no_new_quote"
    ofi = old.get("last_ofi_proxy")
    imbalance = old.get("last_queue_imbalance")
    net = None
    trade_at = None
    trade_receipts: list[dict[str, Any]] = []
    trade_gap = None
    quote_at = _positive_int(old.get("last_depth_at_ms"))
    peak_trade_cursor = int(old.get("last_peak_trade_seq") or 0)
    for row in depths:
        seq = _positive_int(row.get("route_sequence"))
        at = _positive_int(row.get("received_at_ms"))
        if seq is None or at is None or (last_seq is not None and seq <= last_seq):
            continue
        touch = _touch(row)
        ofi, imbalance, net, trade_at = None, None, None, None
        trade_receipts, trade_gap = [], None
        if last_seq is not None and seq != last_seq + 1:
            strength, adverse, last_touch = False, 0, None
            reason = "depth_sequence_gap"
        if quote_at is not None and at < quote_at:
            strength, adverse, last_touch = False, 0, None
            reason = "depth_time_reversal"
        if quote_at is not None and at - quote_at > max_quote_age_ms:
            strength, adverse, last_touch = False, 0, None
            reason = "depth_continuity_expired"
        prior_touch = last_touch
        prior_quote_at = quote_at
        trade_peak, peak_trade_cursor, peak_receipts, peak_gap = _trade_peak_since(
            trades, after_sequence=peak_trade_cursor, at_ms=at,
        )
        if touch is None:
            strength, adverse, last_touch = False, 0, None
            reason = "depth_touch_invalid"
        else:
            imbalance = (touch[1] - touch[3]) / (touch[1] + touch[3])
            _, _, trade_receipts, trade_gap = _signed_tape(
                trades, at_ms=at,
                min_sequence_exclusive=int(old.get("first_trade_seq") or 0),
                window_ms=TRADE_WINDOW_MS,
            )
            selected_receipts = [receipt for receipt in trade_receipts
                                 if receipt["received_at_ms"] >= at - params["trade_window_ms"]]
            net = (sum(receipt["qty"] * (1 if receipt["side"] == "BUY" else -1)
                       for receipt in selected_receipts)
                   if selected_receipts else None)
            trade_at = (selected_receipts[-1]["received_at_ms"]
                        if selected_receipts else None)
            if net is None:
                strength, adverse = False, 0
            if last_touch is None:
                reason = "first_depth_baseline"
            else:
                ofi = _ofi(last_touch, touch)
                book_positive = (ofi > params["strong_ofi_min"]
                                 and imbalance > params["strong_queue_min"])
                book_negative = (ofi < -params["weak_ofi_negative_min"]
                                 and imbalance < -params["weak_queue_negative_min"])
                if (book_positive and net is not None
                        and net > params["strong_signed_qty_min"]):
                    strength, adverse, reason = True, 0, "book_and_trade_support"
                elif (strength and book_negative and net is not None
                      and net < -params["weak_signed_qty_negative_min"]):
                    adverse += 1
                    reason = "adverse_evidence_pending"
                    if adverse >= params["adverse_updates_required"]:
                        strength, adverse, reason = False, 0, "sustained_adverse_evidence"
                elif strength:
                    adverse = 0
                    reason = "strong_retained"
                else:
                    adverse = 0
                    reason = ("valid_weak_evidence" if net is not None
                              else trade_gap or "trade_source_missing")
            last_touch = touch
        last_seq, quote_at = seq, at
        observations.append({"at_ms": at, "sequence": seq,
                             "state": ("STRONG" if strength else "WEAK")
                             if touch is not None and net is not None else "UNKNOWN",
                             "reason": reason, "ofi_proxy": ofi, "queue_imbalance": imbalance,
                             "signed_trade_qty": net, "trade_received_at_ms": trade_at,
                             "trade_receipts": trade_receipts,
                             "trade_window_ms": params["trade_window_ms"],
                             "trade_gap": trade_gap,
                             "trade_peak_price_since_prior_depth": trade_peak,
                             "trade_peak_receipts": peak_receipts,
                             "trade_peak_gap": peak_gap,
                             "previous_quote_at_ms": prior_quote_at,
                             "touch": touch, "previous_touch": prior_touch,
                             "best_bid": touch[0] if touch else None})
    old.update({"item": item, "epoch": epoch, "strong": strength,
                "last_depth_seq": last_seq, "last_depth_at_ms": quote_at,
                "last_touch": last_touch, "adverse_count": adverse,
                "last_peak_trade_seq": peak_trade_cursor,
                "last_ofi_proxy": ofi, "last_queue_imbalance": imbalance})
    if quote_at is not None:
        net, trade_at, _, trade_gap = _signed_tape(
            trades, at_ms=now_ms,
            min_sequence_exclusive=int(old.get("first_trade_seq") or 0),
            window_ms=int(params["trade_window_ms"]),
        )
    if quote_at is None or now_ms < quote_at or now_ms - quote_at > max_quote_age_ms:
        state, reason = "UNKNOWN", "depth_expired_or_missing"
    elif trade_at is None or now_ms < trade_at or now_ms - trade_at > params["trade_window_ms"]:
        state, reason = "UNKNOWN", trade_gap or "trade_expired_or_missing"
    elif last_touch is None:
        state, reason = "UNKNOWN", "depth_touch_invalid"
    else:
        state = "STRONG" if strength else "WEAK"
    if state == "UNKNOWN":
        old["strong"] = False
        old["adverse_count"] = 0
    return StrengthDecision(state, reason, ofi, imbalance, net, last_seq, quote_at,
                            trade_at, item, epoch, tuple(observations)), old
