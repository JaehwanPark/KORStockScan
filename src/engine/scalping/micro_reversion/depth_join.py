"""Past-only offline join for canonical 0B rows and continuous 0D depth rows.

The join deliberately uses local receive time, never a future snapshot, and
never crosses symbol, venue, or session boundaries.  It has no runtime policy
or order authority.
"""

from __future__ import annotations

import gzip
import json
import math
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .contracts import normalize_symbol, normalize_venue, registration_item_identity
from .path_journal import (
    MARKET_DEPTH_CONTRACT_ID,
    MARKET_DEPTH_SCHEMA,
    MARKET_STREAM_CONTRACT_ID,
    MARKET_STREAM_SCHEMA,
    validate_market_stream_path_provenance,
)

DEPTH_JOIN_SCHEMA = "scalp_micro_reversion_depth_join_v1"
DEPTH_JOIN_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_offline_depth_context",
    "decision_authority": "offline_research_join_only",
    "window_policy": (
        "latest_past_same_symbol_venue_session_sequence_epoch_with_freshness_limit"
    ),
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "past_only_depth_join_coverage_pct",
    "source_quality_gate": (
        "valid_depth_schema_and_authority_and_nonfuture_local_receive_time"
    ),
    "forbidden_uses": (
        "future_depth_join",
        "cross_symbol_venue_session_or_sequence_epoch_join",
        "missing_depth_imputation",
        "touch_or_depth_as_real_fill",
        "broker_order_submission",
        "threshold_provider_bot_quantity_or_cap_mutation",
    ),
}


def read_depth_rows(paths: Iterable[Path | str]) -> tuple[dict[str, Any], ...]:
    """Read and validate plain or gzip depth JSONL shards."""

    rows: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        handle = (
            gzip.open(path, "rt", encoding="utf-8")
            if path.suffix == ".gz"
            else path.open("r", encoding="utf-8")
        )
        with handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                validate_depth_row(payload)
                rows.append(payload)
    return tuple(rows)


def join_latest_past_depth(
    market_rows: Iterable[dict[str, Any]],
    depth_rows: Iterable[dict[str, Any]],
    *,
    max_age_ms: int = 1_000,
) -> tuple[dict[str, Any], ...]:
    """Enrich 0B rows with the latest nonfuture fresh 0D snapshot.

    Rows without an eligible depth snapshot remain present and receive an
    explicit status.  Existing non-null depth fields are never overwritten.
    """

    if max_age_ms < 0:
        raise ValueError("max_age_ms must not be negative")
    by_series: dict[tuple[str, str, str, int], list[tuple[int, dict[str, Any]]]] = (
        defaultdict(list)
    )
    seen_sequences: dict[tuple[str, str, str, int], set[int]] = defaultdict(set)
    for depth in depth_rows:
        validate_depth_row(depth)
        key = _series_key(depth)
        sequence_key = int(depth.get("series_sequence") or 0)
        if sequence_key in seen_sequences[key]:
            raise ValueError("duplicate depth series sequence")
        seen_sequences[key].add(sequence_key)
        received_us = _timestamp_us(depth.get("local_receive_timestamp"))
        by_series[key].append((received_us, depth))
    receive_times: dict[tuple[str, str, str, int], tuple[int, ...]] = {}
    for key, values in by_series.items():
        values.sort(key=lambda row: (row[0], int(row[1].get("series_sequence") or 0)))
        sequences = [int(row[1].get("series_sequence") or 0) for row in values]
        if any(
            right != left + 1
            for left, right in zip(sequences, sequences[1:], strict=False)
        ):
            raise ValueError("depth series sequence gap or regression")
        receive_times[key] = tuple(value[0] for value in values)

    joined: list[dict[str, Any]] = []
    for market in market_rows:
        _validate_market_row(market)
        payload = dict(market)
        if payload.get("bid_depth") is not None or payload.get("ask_depth") is not None:
            raise ValueError("canonical 0B row must not contain prejoined depth")
        key = _series_key(payload)
        market_received_us = _timestamp_us(payload.get("local_receive_timestamp"))
        candidates = by_series.get(key, ())
        index = bisect_right(receive_times.get(key, ()), market_received_us) - 1
        status = "missing_same_series_depth"
        age_ms: float | None = None
        selected: dict[str, Any] | None = None
        if index >= 0 and candidates:
            selected_receive_us, candidate = candidates[index]
            age_ms = (market_received_us - selected_receive_us) / 1_000.0
            if age_ms <= max_age_ms:
                selected = candidate
                status = "joined_fresh_past_depth"
            else:
                status = "stale_past_depth"
        if selected is not None:
            if payload.get("bid_depth") is None:
                payload["bid_depth"] = selected["bid_depth"]
            if payload.get("ask_depth") is None:
                payload["ask_depth"] = selected["ask_depth"]
            payload["depth_context"] = {
                "best_bid": selected["best_bid"],
                "best_ask": selected["best_ask"],
                "best_bid_qty": selected["best_bid_qty"],
                "best_ask_qty": selected["best_ask_qty"],
                "bid_levels": selected["bid_levels"],
                "ask_levels": selected["ask_levels"],
                "route_depth_totals": selected["route_depth_totals"],
                "source_sequence": selected["source_sequence"],
                "sequence_epoch": selected["sequence_epoch"],
                "local_receive_timestamp": selected["local_receive_timestamp"],
                "exchange_timestamp": selected["exchange_timestamp"],
                "item": selected["item"],
            }
        payload.update(
            {
                "depth_join_schema": DEPTH_JOIN_SCHEMA,
                "depth_join_status": status,
                "depth_age_ms": age_ms,
                "depth_join_metric_contract": dict(DEPTH_JOIN_METRIC_CONTRACT),
            }
        )
        joined.append(payload)
    return tuple(joined)


def validate_depth_row(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("depth JSONL row must be an object")
    if (
        payload.get("schema") != MARKET_DEPTH_SCHEMA
        or payload.get("metric_contract_id") != MARKET_DEPTH_CONTRACT_ID
    ):
        raise ValueError("unexpected depth schema or contract")
    if (
        payload.get("realtime_type") != "0D"
        or not str(payload.get("item") or "").strip()
    ):
        raise ValueError("depth realtime type or item is invalid")
    item_symbol, item_venue = registration_item_identity(payload.get("item"))
    if (
        not item_symbol
        or item_symbol != normalize_symbol(payload.get("symbol"))
        or item_venue != normalize_venue(payload.get("venue"))
    ):
        raise ValueError("depth item symbol or venue conflicts with row scope")
    if (
        payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("trading_runtime_effect") is not False
    ):
        raise ValueError("depth authority contract is invalid")
    sequence_epoch = payload.get("sequence_epoch")
    if (
        isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        raise ValueError("depth sequence epoch must be positive")
    _series_key(payload)
    exchange_us = _timestamp_us(payload.get("exchange_timestamp"))
    receive_us = _timestamp_us(payload.get("local_receive_timestamp"))
    if receive_us < exchange_us:
        raise ValueError("depth receive timestamp precedes exchange timestamp")
    source_sequence = payload.get("source_sequence")
    series_sequence = payload.get("series_sequence")
    if (
        isinstance(source_sequence, bool)
        or not isinstance(source_sequence, int)
        or source_sequence <= 0
    ):
        raise ValueError("depth source sequence must be positive")
    if (
        isinstance(series_sequence, bool)
        or not isinstance(series_sequence, int)
        or source_sequence != series_sequence
    ):
        raise ValueError("depth source and series sequences must match")
    for field in ("best_bid", "best_ask"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            raise ValueError("depth best quotes must be positive")
    if float(payload["best_ask"]) < float(payload["best_bid"]):
        raise ValueError("depth best quotes are crossed")
    for field in ("bid_depth", "ask_depth"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("depth totals must be nonnegative integers")
    for side in ("bid", "ask"):
        best_quantity = payload.get(f"best_{side}_qty")
        if (
            isinstance(best_quantity, bool)
            or not isinstance(best_quantity, int)
            or best_quantity < 0
        ):
            raise ValueError(f"depth best {side} quantity is invalid")
        raw_levels = payload.get(f"{side}_levels")
        if not isinstance(raw_levels, (list, tuple)) or not raw_levels:
            raise ValueError(f"depth {side} levels must not be empty")
        levels: list[tuple[int, float, int]] = []
        for raw in raw_levels:
            if not isinstance(raw, (list, tuple)) or len(raw) != 3:
                raise ValueError(f"depth {side} level shape is invalid")
            level, price, quantity = raw
            if (
                isinstance(level, bool)
                or not isinstance(level, int)
                or level <= 0
                or isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 0
                or isinstance(price, bool)
                or not isinstance(price, (int, float))
                or not math.isfinite(float(price))
                or float(price) <= 0
            ):
                raise ValueError(f"depth {side} level value is invalid")
            levels.append((level, float(price), quantity))
        if tuple(row[0] for row in levels) != tuple(range(1, len(levels) + 1)):
            raise ValueError(f"depth {side} levels must be contiguous")
        if side == "ask" and any(
            left[1] >= right[1] for left, right in zip(levels, levels[1:], strict=False)
        ):
            raise ValueError("depth ask prices must increase")
        if side == "bid" and any(
            left[1] <= right[1] for left, right in zip(levels, levels[1:], strict=False)
        ):
            raise ValueError("depth bid prices must decrease")
        if levels[0][1] != float(payload[f"best_{side}"]):
            raise ValueError(f"depth best {side} conflicts with level one")
        if levels[0][2] != best_quantity:
            raise ValueError(f"depth best {side} quantity conflicts with level one")
        if int(payload[f"{side}_depth"]) < sum(row[2] for row in levels):
            raise ValueError(f"depth {side} total does not cover retained levels")
    route_totals = payload.get("route_depth_totals")
    if not isinstance(route_totals, dict):
        raise ValueError("depth route totals are missing")
    combined = route_totals.get("combined")
    if not isinstance(combined, dict) or (
        combined.get("bid") != payload.get("bid_depth")
        or combined.get("ask") != payload.get("ask_depth")
    ):
        raise ValueError("depth combined route totals conflict")
    for totals in route_totals.values():
        if not isinstance(totals, dict):
            raise ValueError("depth route totals must be objects")
        for quantity in totals.values():
            if quantity is not None and (
                isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 0
            ):
                raise ValueError("depth route total is invalid")
    components = [
        totals
        for route, totals in route_totals.items()
        if route != "combined" and isinstance(totals, dict)
    ]
    for side in ("bid", "ask"):
        component_values = [totals.get(side) for totals in components]
        if component_values and all(value is not None for value in component_values):
            if sum(component_values) != combined.get(side):
                raise ValueError("depth component route totals do not reconcile")


def _validate_market_row(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("market row must be an object")
    if (
        payload.get("schema") != MARKET_STREAM_SCHEMA
        or payload.get("metric_contract_id") != MARKET_STREAM_CONTRACT_ID
        or payload.get("realtime_type") != "0B"
    ):
        raise ValueError("unexpected market schema or contract")
    item_symbol, item_venue = registration_item_identity(payload.get("item"))
    if (
        not item_symbol
        or item_symbol != normalize_symbol(payload.get("symbol"))
        or item_venue != normalize_venue(payload.get("venue"))
    ):
        raise ValueError("market item symbol or venue conflicts with row scope")
    if (
        payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("trading_runtime_effect") is not False
    ):
        raise ValueError("market authority contract is invalid")
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
        raise ValueError(
            "market source and series sequences must be positive and equal"
        )
    _series_key(payload)
    exchange_us = _timestamp_us(payload.get("exchange_timestamp"))
    receive_us = _timestamp_us(payload.get("local_receive_timestamp"))
    if receive_us < exchange_us:
        raise ValueError("market receive timestamp precedes exchange timestamp")
    _, consumer_eligible, _ = validate_market_stream_path_provenance(
        path_order_status=payload.get("path_order_status"),
        path_consumer_eligible=payload.get("path_consumer_eligible"),
        exchange_timestamp_regression_ms=payload.get(
            "exchange_timestamp_regression_ms"
        ),
    )
    if not consumer_eligible:
        raise ValueError("market path is not consumer eligible")


def _series_key(payload: dict[str, Any]) -> tuple[str, str, str, int]:
    symbol = str(payload.get("symbol") or "").strip().upper()
    venue = str(payload.get("venue") or "").strip().upper()
    session_bucket = str(payload.get("session_bucket") or "").strip().upper()
    sequence_epoch = payload.get("sequence_epoch")
    if (
        isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        raise ValueError("depth join sequence_epoch is invalid")
    if not all((symbol, venue, session_bucket)) or sequence_epoch <= 0:
        raise ValueError(
            "depth join requires symbol, venue, session, and sequence_epoch"
        )
    return symbol, venue, session_bucket, sequence_epoch


def _timestamp_us(value: object) -> int:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("depth join timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("depth join timestamp must include timezone")
    return int(parsed.timestamp() * 1_000_000)
