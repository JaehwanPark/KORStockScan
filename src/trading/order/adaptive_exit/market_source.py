"""Shared research snapshot calculation; no live reader or activation wiring."""

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.market.confirmation_window import (
    FEATURE_VERSION,
)

from .models import finite, positive_int

SUPPORT_CONTRACT = "past_one_second_bid_nondecay_trade_backing_refill_v1"


class MarketSourceGap(ValueError):
    def __init__(self, reason):
        super().__init__("adaptive_exit_market_source_gap:" + reason)


def _require(condition, reason):
    if not condition:
        raise MarketSourceGap(reason)


def snapshot_payload_from_window(
    *, depth, feature, scope_key, position_epoch, observed_at_ms, sequence
):
    """One exit-support calculation for canonical research and WS adapters.

    Preserve the original research hash/field contract for valid inputs. Bid
    depth is required explicitly, never synthesized from an endpoint price.
    """
    _require(
        feature.get("feature_version") == FEATURE_VERSION
        and feature.get("source_quality_status") == "eligible"
        and feature.get("eligible_for_feature_ablation") is True
        and feature.get("checkpoint_at_ms") == observed_at_ms,
        "ordered_past_window_source_gap:"
        + ",".join(feature.get("source_gap_reasons", [])),
    )
    endpoint = feature["endpoint_depth"]
    _require(
        depth.get("item") == endpoint["item"]
        and depth.get("transport_epoch", depth.get("sequence_epoch"))
        == endpoint["epoch"]
        and depth.get("route_sequence", depth.get("series_sequence"))
        == endpoint["sequence"]
        and depth.get("best_bid") == endpoint["bid"]
        and depth.get("best_ask") == endpoint["ask"],
        "endpoint_depth_binding_invalid",
    )
    raw_levels = depth.get("bid_levels")
    _require(isinstance(raw_levels, (list, tuple)) and raw_levels, "bid_depth_missing")
    levels = []
    for level in raw_levels:
        if isinstance(level, dict):
            price, qty = level.get("price"), level.get("quantity")
        else:
            _require(
                isinstance(level, (list, tuple)) and len(level) == 3,
                "bid_depth_invalid",
            )
            _, price, qty = level
        _require(
            finite(price)
            and 0 < price < endpoint["ask"]
            and positive_int(qty)
            and (not levels or price < levels[-1][0]),
            "bid_depth_invalid",
        )
        levels.append((price, qty))
    _require(levels[0][0] == endpoint["bid"], "bid_depth_endpoint_mismatch")
    if "best_bid_qty" in depth:
        _require(
            positive_int(depth["best_bid_qty"])
            and depth["best_bid_qty"] == levels[0][1],
            "bid_depth_quantity_mismatch",
        )
    left_bid = feature["anchor_depth"]["bid"]
    return {
        "observed_at_ms": observed_at_ms,
        "quote_at_ms": endpoint["at_ms"],
        "source_epoch": str(endpoint["epoch"]),
        "sequence": sequence,
        "quote_sequence": endpoint["sequence"],
        "source_hash": canonical_sha256({"depth": depth, "feature": feature}),
        "scope_key": scope_key,
        "position_epoch": position_epoch,
        "best_ask": depth["best_ask"],
        "bid_levels": levels,
        "supportive": (
            depth["best_bid"] >= left_bid
            and feature["aggressive_buy_trade_backed_ratio"] > 0
            and feature["refill_ratio"] <= 1
        ),
        "improvement_bps": (depth["best_bid"] / left_bid - 1) * 10000,
    }
