"""Causal entry veto, not a BUY signal or a profitability estimate."""

import math

from src.trading.market.confirmation_window import (
    _normalize,
    _timestamp,
    build_confirmation_window,
)
from src.trading.market.micro_confirmation import _live_route_item

from src.trading.market.quote_consistency import build_market_data_health

CONTRACT = "machine_entry_adverse_flow_v1"
CHECKPOINTS_MS = (0, 1000, 3000, 5000)
MAX_LATE_MS = 1500
DEADLINE_MS = 6500
MAXIMUM_SOURCE_AGE_MS = 1500



def evaluate_machine_entry_payload(*, snapshot, payload, cutoff_ms):
    """Bind the market-data item to the exact AI snapshot, not a scope alias."""
    payload = payload if isinstance(payload, dict) else {}
    exact = payload.get("ai_market_snapshot_v1")
    exact = exact if isinstance(exact, dict) else {}
    market_route = str(exact.get("market_data_route") or "").lower()
    route = {"krx_only": "KRX", "nxt_only": "NXT", "krx_nxt_integrated": "SOR"}.get(market_route)
    symbol = str(payload.get("stock_code") or "")
    identity_valid = bool(
        route and exact.get("snapshot_id") and symbol
        and symbol == exact.get("stock_code")
        and all(str(payload.get(k) or "").upper() == str(exact.get(k) or "").upper() and payload.get(k) for k in ("effective_venue", "session_bucket"))
    )
    if not identity_valid:
        return {"contract": CONTRACT, "action": "SOURCE_UNAVAILABLE", "cutoff_ms": cutoff_ms, "source_quality_status": "source_gap", "reason": "machine_payload_market_route_missing_or_conflicting"}
    result = evaluate_snapshot(snapshot=snapshot, symbol=symbol, route=route, cutoff_ms=cutoff_ms, market_session=payload["session_bucket"])
    result["machine_market_route_binding"] = {"snapshot_id": exact["snapshot_id"], "market_data_route": market_route, "confirmation_route": route, "effective_venue": payload["effective_venue"], "session_bucket": payload["session_bucket"]}
    return result


def evaluate_snapshot(
    *,
    snapshot,
    symbol,
    route,
    cutoff_ms,
    require_latest=False,
    market_session="",
):
    """Use the existing window validator without changing its feature contract.

    Fixed ask depletion/refill are diagnostics here, not extra entry gates.
    Local projection sequence continuity does not prove exchange completeness.
    """
    result = dict(contract=CONTRACT, action="SOURCE_UNAVAILABLE", cutoff_ms=cutoff_ms)
    try:
        if type(cutoff_ms) is not int or cutoff_ms <= 0:
            raise ValueError("invalid_cutoff")
        contract = snapshot["machine_confirmation_input_contract"]
        if (
            snapshot["schema_version"] != "kiwoom_ws_dashboard_snapshot_v1"
            or snapshot["decision_authority"] != "source_quality_only"
            or snapshot["runtime_effect"] is not False
            or contract.get("schema") != "machine_entry_confirmation_ws_snapshot_v1"
            or contract.get("decision_authority")
            != "market_data_input_only_no_order_authority"
            or any(
                contract.get(k) is not True
                for k in (
                    "exact_route_required",
                    "causal_past_only",
                    "broker_order_forbidden",
                )
            )
            or any(
                contract.get(k) is not False
                for k in ("runtime_effect", "actual_order_submitted")
            )
        ):
            raise ValueError("invalid_snapshot_authority")
        item = _live_route_item(symbol, route)
        stock = snapshot["stocks"][symbol]
        result["market_data_health"] = build_market_data_health(
            stock, now_ts=cutoff_ms / 1000.0, quote_max_age_ms=MAXIMUM_SOURCE_AGE_MS,
        )
        routes = stock["machine_confirmation_routes"]
        matches = [
            r
            for r in routes.values()
            if all(
                r.get("realtime_types", {}).get(t, {}).get("item") == item
                for t in ("0B", "0D")
            )
        ]
        if not item or len(matches) != 1:
            raise ValueError("exact_route_missing_or_duplicate")
        source = matches[0]
        realtime_types = source.get("realtime_types") or {}
        venues = {
            str((realtime_types.get(kind) or {}).get("effective_venue") or "")
            .strip()
            .upper()
            for kind in ("0B", "0D")
        } - {""}
        market_routes = {
            str((realtime_types.get(kind) or {}).get("market_route") or "")
            .strip()
            .lower()
            for kind in ("0B", "0D")
        } - {""}
        effective_venue = (
            next(iter(venues))
            if len(venues) == 1
            else (
                "KRX_NXT_INTEGRATED"
                if not venues and market_routes == {"krx_nxt_integrated"}
                else "UNKNOWN"
            )
        )
        epoch = source["realtime_types"]["0D"]["transport_epoch"]
        trade_epoch = source["realtime_types"]["0B"]["transport_epoch"]
        if (
            type(epoch) is not int
            or epoch <= 0
            or type(trade_epoch) is not int
            or trade_epoch != epoch
        ):
            raise ValueError("epoch_mismatch")
        feature = build_confirmation_window(
            depth_rows=source.get("recent_depth"),
            trade_rows=source.get("recent_trades"),
            item=item,
            epoch=epoch,
            checkpoint_at_ms=cutoff_ms,
            source_complete=source.get("source_complete", True),
            maximum_age_ms=MAXIMUM_SOURCE_AGE_MS,
        )
        # No new ask-wall economic gate on this bid/trade-only hypothesis.
        gaps = set(feature["source_gap_reasons"]) - {
            "fixed_ask_level_unobserved",
            "initial_or_fixed_depth_invalid",
        }
        if gaps:
            raise ValueError(",".join(sorted(gaps)))
        if require_latest:
            for kind, endpoint in (("0B", "endpoint_trade"), ("0D", "endpoint_depth")):
                receipt, row = source["realtime_types"][kind], feature[endpoint]
                stamp = receipt.get("observed_epoch")
                if (
                    type(stamp) not in (int, float)
                    or not math.isfinite(stamp)
                    or type(receipt.get("route_sequence")) is not int
                    or receipt["route_sequence"] != row["sequence"]
                    or abs(stamp * 1000 - row["at_ms"]) > 1
                ):
                    raise ValueError("latest_endpoint_receipt_mismatch")
        start = cutoff_ms - 1000
        streams = []
        for name, depth in (("recent_depth", True), ("recent_trades", False)):
            rows = {}
            for raw in source[name]:
                if (
                    raw.get("item") != item
                    or raw.get("transport_epoch", raw.get("sequence_epoch")) != epoch
                ):
                    continue
                # Do not normalize post-cutoff rows into an earlier decision.
                if _timestamp(raw) > cutoff_ms:
                    continue
                row = _normalize(raw, depth=depth)
                if row["at_ms"] > start:
                    rows[row["sequence"]] = row
            streams.append(list(rows.values()))
        depths, trades = streams
        bid_start = feature["anchor_depth"]["bid"]
        bid_end = feature["endpoint_depth"]["bid"]
        bid_min = min([bid_start, *[r["bid"] for r in depths]])
        quantities = {side: [0, 0] for side in ("BUY", "SELL")}
        for row in trades:
            quantities[row["side"]][int(row["at_ms"] > cutoff_ms - 500)] += row[
                "quantity"
            ]
        buy, sell = quantities["BUY"], quantities["SELL"]
        checks = dict(
            bid_declining=bid_end < bid_start,
            sell_dominant_both_halves=sell[0] > buy[0] and sell[1] > buy[1],
            sell_speed_not_easing=sell[1] >= sell[0],
            no_bid_recovery=bid_end == bid_min,
        )
        result.update(
            action="DEFER_ADVERSE_FLOW" if all(checks.values()) else "CONTINUE",
            checks=checks,
            buy_qty_halves=buy,
            sell_qty_halves=sell,
            sell_rate_qty_per_sec=[v * 2 for v in sell],
            bid_start=bid_start,
            bid_end=bid_end,
            bid_min=bid_min,
            item=item,
            epoch=epoch,
            source_sha256=feature["window_source_sha256"],
            feature=feature,
            source_quality_status="eligible",
            effective_venue=effective_venue,
            market_session=str(market_session or "UNKNOWN"),
            route_identity_source=(
                "exact_realtime_type_effective_venue"
                if len(venues) == 1
                else (
                    "exact_integrated_market_route"
                    if effective_venue == "KRX_NXT_INTEGRATED"
                    else "unresolved"
                )
            ),
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        IndexError,
        OverflowError,
    ) as exc:
        result.update(reason=str(exc), source_quality_status="source_gap")
    return result
