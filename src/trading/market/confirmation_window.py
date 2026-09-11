"""Pure fixed-price, past-only micro-confirmation feature calculation.

Shared by the live snapshot adapter and the postclose raw-row adapter. Local
sequences prove projection continuity, not exchange packet completeness. This
module has no network, policy publication, or broker authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from typing import Any, Mapping

FEATURE_VERSION = "machine_confirmation_fixed_price_window_v1"
WINDOW_MS = 1_000
MAX_BUFFER_ROWS = 120


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("non_numeric_source")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("non_finite_source")
    return value


def _integer(value: Any) -> int:
    number = _number(value)
    if not number.is_integer() or number <= 0:
        raise ValueError("invalid_source_identity")
    return int(number)


def _timestamp(row: Mapping[str, Any]) -> int:
    if "received_at_ms" in row:
        return _integer(row["received_at_ms"])
    stamp = datetime.fromisoformat(str(row.get("local_receive_timestamp") or ""))
    if stamp.utcoffset() is None:
        raise ValueError("naive_source_timestamp")
    return int(stamp.timestamp() * 1_000)


def _normalize(row: Mapping[str, Any], *, depth: bool) -> dict[str, Any]:
    result = {
        "at_ms": _timestamp(row),
        "item": str(row.get("item") or ""),
        "epoch": _integer(row.get("transport_epoch", row.get("sequence_epoch"))),
        "sequence": _integer(
            row.get(
                "route_sequence", row.get("series_sequence", row.get("source_sequence"))
            )
        ),
    }
    if (
        row.get("path_consumer_eligible") is False
        or row.get("path_order_status", "accept") != "accept"
    ):
        raise ValueError("source_path_ineligible")
    if depth:
        bid, ask = _number(row.get("best_bid")), _number(row.get("best_ask"))
        quantity = _number(row.get("best_ask_qty"))
        if bid <= 0 or ask < bid or quantity < 0:
            raise ValueError("invalid_depth")
        levels = row.get("ask_levels")
        normalized_levels = []
        for level in levels or ():
            price, qty = (
                (level.get("price"), level.get("quantity"))
                if isinstance(level, Mapping)
                else (level[1], level[2])
            )
            price, qty = _number(price), _number(qty)
            if price <= 0 or qty < 0:
                raise ValueError("invalid_depth_level")
            normalized_levels.append([price, qty])
        if not normalized_levels:
            normalized_levels = [[ask, quantity]]
        if normalized_levels[0] != [ask, quantity] or any(
            b[0] <= a[0] for a, b in zip(normalized_levels, normalized_levels[1:])
        ):
            raise ValueError("depth_level_contract_mismatch")
        result.update(bid=bid, ask=ask, quantity=quantity, asks=normalized_levels)
    else:
        price = _number(row.get("price", row.get("trade_price")))
        quantity = _number(row.get("volume", row.get("trade_qty")))
        if price <= 0 or quantity <= 0:
            raise ValueError("invalid_trade")
        side = row.get("aggressor_side")
        result.update(
            price=price, quantity=quantity, side=side if isinstance(side, str) else None
        )
    return result


def build_confirmation_window(
    *,
    depth_rows: Any,
    trade_rows: Any,
    item: str,
    epoch: int,
    checkpoint_at_ms: int,
    maximum_age_ms: int = 1_500,
    source_complete: bool = True,
    include_observed_rows: bool = False,
) -> dict[str, Any]:
    """Calculate a closed one-second window, including trades at its start.

    A causal left-limit quote is required. No endpoint-only estimate, all-price
    trade sum, or zero-flow replacement is used for unavailable evidence.
    """
    reasons: list[str] = []
    if not isinstance(item, str) or not item:
        reasons.append("exact_route_identity_invalid")
    if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch <= 0:
        reasons.append("exact_epoch_identity_invalid")
    start_ms = checkpoint_at_ms - WINDOW_MS
    result: dict[str, Any] = {
        "feature_version": FEATURE_VERSION,
        "window_started_at_ms": start_ms,
        "checkpoint_at_ms": checkpoint_at_ms,
        "horizon_ms": WINDOW_MS,
        "source_quality_status": "source_gap",
        "eligible_for_feature_ablation": False,
        "aggressive_buy_trade_backed_ratio": None,
        "refill_ratio": None,
        "downward_reprice_observed": None,
        "best_ask_depletion_velocity_qty_per_sec": None,
        "unexplained_or_cancel_like_depletion_ratio": None,
        "refill_half_life_ms": None,
    }
    if source_complete is not True:
        reasons.append("source_window_completeness_unproven")
    streams: list[list[dict[str, Any]]] = []
    for rows, is_depth in ((depth_rows, True), (trade_rows, False)):
        normalized: dict[int, dict[str, Any]] = {}
        if not isinstance(rows, (list, tuple)):
            reasons.append("source_window_rows_invalid")
            rows = []
        for raw in rows:
            if not isinstance(raw, Mapping):
                reasons.append("source_window_row_invalid")
                continue
            if (
                raw.get("item") != item
                or raw.get("transport_epoch", raw.get("sequence_epoch")) != epoch
            ):
                continue
            try:
                # Rows after the cutoff must not change an earlier decision.
                if _timestamp(raw) > checkpoint_at_ms:
                    continue
                row = _normalize(raw, depth=is_depth)
                prior = normalized.get(row["sequence"])
                if prior is not None and prior != row:
                    raise ValueError("conflicting_source_sequence")
                normalized[row["sequence"]] = row
            except (
                TypeError,
                ValueError,
                KeyError,
                IndexError,
                OverflowError,
                AttributeError,
            ) as exc:
                reasons.append(f"window_source_invalid:{type(exc).__name__}")
        ordered = sorted(normalized.values(), key=lambda row: row["sequence"])
        left = [r for r in ordered if r["at_ms"] <= start_ms]
        anchor = left[-1:] if left else []
        window = anchor + [r for r in ordered if r["at_ms"] > start_ms]
        if any(
            b["sequence"] != a["sequence"] + 1 or b["at_ms"] < a["at_ms"]
            for a, b in zip(window, window[1:])
        ):
            reasons.append("depth_sequence_gap" if is_depth else "market_sequence_gap")
        # A missing left trade watermark could hide dropped trades at the start.
        if not anchor:
            reasons.append(
                "depth_left_boundary_missing"
                if is_depth
                else "trade_left_boundary_missing"
            )
        streams.append(window)
    depths, trades = streams
    result["endpoint_trade"] = trades[-1] if trades else None
    if not depths or depths[0]["at_ms"] > start_ms:
        reasons.append("starting_depth_missing")
    elif start_ms - depths[0]["at_ms"] > maximum_age_ms:
        reasons.append("starting_depth_stale")
    if not depths or checkpoint_at_ms - depths[-1]["at_ms"] > maximum_age_ms:
        reasons.append("ending_depth_stale_or_missing")
    if not trades or checkpoint_at_ms - trades[-1]["at_ms"] > maximum_age_ms:
        reasons.append("trade_watermark_stale_or_missing")
    active_trades = [r for r in trades if start_ms <= r["at_ms"] <= checkpoint_at_ms]
    if any(r["side"] not in {"BUY", "SELL"} for r in active_trades):
        reasons.append("aggressor_side_unresolved")
    if depths:
        anchor, endpoint = depths[0], depths[-1]
        quantities: list[float] = []
        for row in depths:
            if row["ask"] > anchor["ask"]:
                quantities.append(0.0)
            else:
                fixed = next((q for p, q in row["asks"] if p == anchor["ask"]), None)
                if fixed is None:
                    reasons.append("fixed_ask_level_unobserved")
                    break
                quantities.append(fixed)
        result.update(
            anchor_depth=anchor,
            endpoint_depth=endpoint,
            depth_observation_count=len(depths),
            market_observation_count=len(active_trades),
            downward_reprice_observed=any(r["ask"] < anchor["ask"] for r in depths),
        )
        if quantities and len(quantities) == len(depths) and quantities[0] > 0:
            minimum = min(quantities)
            index = quantities.index(minimum)
            minimum_ms = depths[index]["at_ms"]
            depletion = quantities[0] - minimum
            buy = sum(
                r["quantity"]
                for r in active_trades
                if r["side"] == "BUY"
                and r["price"] == anchor["ask"]
                and r["at_ms"] < minimum_ms
            )
            refill = max(quantities[index:]) - minimum
            half = (
                next(
                    (
                        depths[i]["at_ms"] - minimum_ms
                        for i in range(index + 1, len(depths))
                        if quantities[i] >= minimum + depletion / 2
                    ),
                    None,
                )
                if depletion
                else None
            )
            # Observed zero depletion is neutral evidence, not a missing value.
            result.update(
                max_best_ask_depletion_qty=depletion,
                aggressive_buy_qty_before_max_depletion=buy,
                aggressive_buy_trade_backed_ratio=(
                    min(buy / depletion, 1.0) if depletion else 0.0
                ),
                refill_ratio=refill / depletion if depletion else 0.0,
                best_ask_depletion_velocity_qty_per_sec=(
                    depletion * 1_000 / (minimum_ms - start_ms)
                    if minimum_ms > start_ms
                    else 0.0
                ),
                unexplained_or_cancel_like_depletion_ratio=(
                    max(depletion - buy, 0.0) / depletion if depletion else 0.0
                ),
                refill_half_life_ms=half,
            )
        else:
            reasons.append("initial_or_fixed_depth_invalid")
    result["source_gap_reasons"] = sorted(set(reasons))
    result["eligible_for_feature_ablation"] = not reasons
    result["source_quality_status"] = "eligible" if not reasons else "source_gap"
    result["window_source_sha256"] = hashlib.sha256(
        json.dumps(
            {
                "item": item if isinstance(item, str) else None,
                "epoch": (
                    epoch
                    if isinstance(epoch, int)
                    and not isinstance(epoch, bool)
                    and epoch > 0
                    else None
                ),
                "cutoff": checkpoint_at_ms,
                "depths": depths,
                "trades": trades,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    if include_observed_rows:
        # Target-pressure live diagnostics retain the exact normalized hash
        # inputs so a later review can reproduce depletion/refill and volume.
        result["source_hash_depth_rows"] = depths
        result["source_hash_trade_rows"] = trades
    return result
