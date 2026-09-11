"""Past-only exit pressure; no AI, broker, subscription or policy publication.

Relational starting heuristics, not calibrated probabilities or economic proof.
Reuse the entry/report feature kernel without changing its decision contract.
"""

import math

from src.trading.market.confirmation_window import _normalize, build_confirmation_window
from src.trading.market.micro_confirmation import (
    _live_route_item,
    load_live_dynamic_confirmation_source,
)
from src.trading.market.profit_stagnation_quote import executable_quote
from src.trading.order.tick_utils import move_price_by_ticks

CONTRACT = "machine_target_pressure_v1"


def evaluate_pressure(*, symbol, route, quantity, target_price, now):
    snapshot, reason = load_live_dynamic_confirmation_source()
    if snapshot is None:
        raise ValueError(reason)
    return pressure_from_snapshot(
        snapshot=snapshot,
        symbol=symbol,
        route=route,
        quantity=quantity,
        target_price=target_price,
        now=now,
    )


def pressure_from_snapshot(*, snapshot, symbol, route, quantity, target_price, now):
    """One already-observed second ending now; never wait a second at touch.

    Local sequence continuity is not proof of complete exchange traffic. The
    caller must retain the original target on invalid or unavailable evidence.
    """
    if now.utcoffset() is None or type(target_price) is not int or target_price <= 0:
        raise ValueError("pressure_time_or_target_invalid")
    item = _live_route_item(symbol, route)
    sources = snapshot["stocks"][symbol]["machine_confirmation_routes"]
    matches = [
        s
        for s in sources.values()
        if all(
            s.get("realtime_types", {}).get(t, {}).get("item") == item
            for t in ("0B", "0D")
        )
    ]
    if not item or len(matches) != 1:
        raise ValueError("pressure_exact_route_missing_or_duplicate")
    source = matches[0]
    receipts = source["realtime_types"]
    epoch = receipts["0D"]["transport_epoch"]
    if (
        type(epoch) is not int
        or epoch <= 0
        or type(receipts["0B"]["transport_epoch"]) is not int
        or receipts["0B"]["transport_epoch"] != epoch
    ):
        raise ValueError("pressure_epoch_mismatch")
    cutoff = int(now.timestamp() * 1000)
    feature = build_confirmation_window(
        depth_rows=source.get("recent_depth"),
        trade_rows=source.get("recent_trades"),
        item=item,
        epoch=epoch,
        checkpoint_at_ms=cutoff,
        source_complete=source.get("source_complete", True),
    )
    if not feature["eligible_for_feature_ablation"]:
        raise ValueError(
            "pressure_source_gap:" + ",".join(feature["source_gap_reasons"])
        )
    for kind, endpoint in (("0B", "endpoint_trade"), ("0D", "endpoint_depth")):
        receipt, row = receipts[kind], feature[endpoint]
        # A newer receipt than the frozen window is not usable for live action.
        stamp = receipt.get("observed_epoch")
        if (
            type(stamp) not in {int, float}
            or not math.isfinite(stamp)
            or type(receipt.get("route_sequence")) is not int
            or receipt["route_sequence"] != row["sequence"]
            or abs(stamp * 1000 - row["at_ms"]) > 1
        ):
            raise ValueError("pressure_endpoint_mismatch")
    quote = executable_quote(
        symbol=symbol,
        route=route,
        quantity=quantity,
        now=now,
        snapshot=snapshot,
    )
    # The shared kernel checked conflict/gap/side semantics. Deduplicate by
    # local sequence here too: duplicate projection rows are not extra volume.
    trades = {}
    for raw in source["recent_trades"]:
        if raw.get("item") != item or raw.get("transport_epoch") != epoch:
            continue
        if not cutoff - 1000 <= raw["received_at_ms"] <= cutoff:
            continue
        row = _normalize(raw, depth=False)
        trades[row["sequence"]] = row
    early = sum(
        r["quantity"]
        for r in trades.values()
        if r["side"] == "BUY" and r["at_ms"] < cutoff - 500
    )
    late = sum(
        r["quantity"]
        for r in trades.values()
        if r["side"] == "BUY" and r["at_ms"] >= cutoff - 500
    )
    sold = sum(r["quantity"] for r in trades.values() if r["side"] == "SELL")
    active = sorted(trades.values(), key=lambda row: (row["at_ms"], row["sequence"]))
    endpoint, anchor = feature["endpoint_depth"], feature["anchor_depth"]
    next_price = move_price_by_ticks(target_price, 1)
    if endpoint["asks"][-1][0] < next_price:
        raise ValueError("pressure_next_target_depth_unobserved")
    wall = sum(q for p, q in endpoint["asks"] if p <= next_price)
    checks = {
        "target_reached": quote["executable_bid"] >= target_price,
        "buy_flow_dominant": early + late > sold,
        "buy_speed_sustained": late > 0 and late >= early,
        "depletion_positive": feature["best_ask_depletion_velocity_qty_per_sec"] > 0,
        "depletion_trade_backed": feature["aggressive_buy_trade_backed_ratio"]
        > feature["unexplained_or_cancel_like_depletion_ratio"],
        "refill_weak": feature["refill_ratio"] < 0.5,
        "bid_support": endpoint["bid"] >= anchor["bid"],
        "no_downward_ask_reprice": feature["downward_reprice_observed"] is False,
        # One-second consumption proxy using the most recent half-second.
        # This is not our queue position or a guarantee of a subsequent fill.
        "next_wall_consumable": wall + quantity <= late * 2,
    }
    first_half_started_at_ms = cutoff - 1000
    recent_half_started_at_ms = cutoff - 500
    target_touch_trade_qty = sum(
        r["quantity"]
        for r in active
        if r["side"] == "BUY" and r["price"] >= target_price
    )
    return {
        "contract": CONTRACT,
        "decision": "RAISE_ONE_TICK" if all(checks.values()) else "KEEP_TARGET",
        "checks": checks,
        "reasons": [k for k, ok in checks.items() if not ok],
        "quote": quote,
        "next_price": next_price,
        "checkpoint_at_ms": cutoff,
        "source_sequence_authority": source.get("sequence_authority", "unspecified"),
        "source_scope": "exact_route_local_projection_not_exchange_completeness",
        "source_complete_claim": source.get("source_complete"),
        "source_quality_status": "eligible_local_projection",
        "feature": feature,
        "target_reach_basis": "executable_bid_gte_target_price",
        "trade_target_touch_observed": target_touch_trade_qty > 0,
        "target_touch_buy_qty_observed": target_touch_trade_qty,
        "trade_watermark_age_ms": cutoff - feature["endpoint_trade"]["at_ms"],
        "depth_watermark_age_ms": cutoff - feature["endpoint_depth"]["at_ms"],
        "first_half_started_at_ms": first_half_started_at_ms,
        "recent_half_started_at_ms": recent_half_started_at_ms,
        "window_ended_at_ms": cutoff,
        "buy_qty_first_half_observed": early,
        "buy_qty_recent_half_observed": late,
        "observed_window_trade_rows": active,
        "buy_speed_early_qty_per_sec": early * 2,
        "buy_speed_recent_qty_per_sec": late * 2,
        "sell_qty": sold,
        "next_target_visible_ask_qty": wall,
    }
