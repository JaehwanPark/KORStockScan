"""Past-only offline join for canonical 0B rows and continuous 0D depth rows.

The join deliberately uses local receive time, never a future snapshot, and
never crosses symbol, venue, or session boundaries.  It has no runtime policy
or order authority.
"""

from __future__ import annotations

import gzip
import json
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .path_journal import MARKET_DEPTH_CONTRACT_ID, MARKET_DEPTH_SCHEMA

DEPTH_JOIN_SCHEMA = "scalp_micro_reversion_depth_join_v1"
DEPTH_JOIN_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_offline_depth_context",
    "decision_authority": "offline_research_join_only",
    "window_policy": "latest_past_same_symbol_venue_session_with_freshness_limit",
    "sample_floor": "five_trading_days_and_200_mature_events_gate_b_only",
    "primary_decision_metric": "past_only_depth_join_coverage_pct",
    "source_quality_gate": (
        "valid_depth_schema_and_authority_and_nonfuture_local_receive_time"
    ),
    "forbidden_uses": (
        "future_depth_join",
        "cross_symbol_venue_or_session_join",
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
                _validate_depth_row(payload)
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
    by_series: dict[tuple[str, str, str], list[tuple[int, dict[str, Any]]]] = (
        defaultdict(list)
    )
    seen_sequences: dict[tuple[str, str, str], set[tuple[int, int]]] = defaultdict(set)
    for depth in depth_rows:
        _validate_depth_row(depth)
        key = _series_key(depth)
        sequence_key = (
            int(depth.get("sequence_epoch") or 0),
            int(depth.get("series_sequence") or 0),
        )
        if sequence_key in seen_sequences[key]:
            raise ValueError("duplicate depth series sequence")
        seen_sequences[key].add(sequence_key)
        received_ms = _timestamp_ms(depth.get("local_receive_timestamp"))
        by_series[key].append((received_ms, depth))
    receive_times: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, values in by_series.items():
        values.sort(key=lambda row: (row[0], int(row[1].get("series_sequence") or 0)))
        receive_times[key] = tuple(value[0] for value in values)

    joined: list[dict[str, Any]] = []
    for market in market_rows:
        payload = dict(market)
        if payload.get("bid_depth") is not None or payload.get("ask_depth") is not None:
            raise ValueError("canonical 0B row must not contain prejoined depth")
        key = _series_key(payload)
        market_received_ms = _timestamp_ms(payload.get("local_receive_timestamp"))
        candidates = by_series.get(key, ())
        index = bisect_right(receive_times.get(key, ()), market_received_ms) - 1
        status = "missing_same_series_depth"
        age_ms: int | None = None
        selected: dict[str, Any] | None = None
        if index >= 0 and candidates:
            selected_receive_ms, candidate = candidates[index]
            age_ms = market_received_ms - selected_receive_ms
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


def _validate_depth_row(payload: object) -> None:
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
    if (
        payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
        or payload.get("trading_runtime_effect") is not False
    ):
        raise ValueError("depth authority contract is invalid")
    _series_key(payload)
    exchange_ms = _timestamp_ms(payload.get("exchange_timestamp"))
    receive_ms = _timestamp_ms(payload.get("local_receive_timestamp"))
    if receive_ms < exchange_ms:
        raise ValueError("depth receive timestamp precedes exchange timestamp")
    if int(payload.get("source_sequence") or 0) <= 0:
        raise ValueError("depth source sequence must be positive")
    if int(payload.get("sequence_epoch") or 0) <= 0:
        raise ValueError("depth sequence epoch must be positive")
    if payload.get("source_sequence") != payload.get("series_sequence"):
        raise ValueError("depth source and series sequences must match")
    for field in ("best_bid", "best_ask"):
        if float(payload.get(field) or 0) <= 0:
            raise ValueError("depth best quotes must be positive")
    if float(payload["best_ask"]) < float(payload["best_bid"]):
        raise ValueError("depth best quotes are crossed")
    for field in ("bid_depth", "ask_depth"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("depth totals must be nonnegative integers")


def _series_key(payload: dict[str, Any]) -> tuple[str, str, str]:
    key = tuple(
        str(payload.get(field) or "").strip().upper()
        for field in ("symbol", "venue", "session_bucket")
    )
    if not all(key):
        raise ValueError("depth join requires symbol, venue, and session")
    return key  # type: ignore[return-value]


def _timestamp_ms(value: object) -> int:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("depth join timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("depth join timestamp must include timezone")
    return int(parsed.timestamp() * 1_000)
