"""Observation-only scalping market context derived from canonical minute bars.

This module intentionally has no live prompt, order, threshold, provider-route,
or runtime-apply authority.  It produces deterministic forensics inputs for
source-quality and external-data validation.
"""

from __future__ import annotations

import math
from datetime import datetime, time as dt_time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "scalping_market_context_observation_v1"
INTERVALS = (3, 5, 15)

OBSERVATION_CONTRACT = {
    "metric_role": "ai_input_source_quality",
    "decision_authority": "forensics_only_no_runtime_change",
    "window_policy": "exact_timestamp_venue_session_completed_bar",
    "sample_floor": "one_valid_row_per_symbol_venue_session_endpoint",
    "primary_decision_metric": "required_source_field_match_status",
    "source_quality_gate": "fresh_same_basis_conflict_free",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_ai_prompt_input",
        "runtime_threshold_apply",
        "order_submit",
        "provider_route_change",
        "bot_restart",
        "broker_guard_bypass",
        "live_auto_promotion",
    ],
}


def _number(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "null"):
            return default
        result = float(str(value).replace(",", "").replace("+", ""))
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _integer(value: Any, default: int = 0) -> int:
    number = _number(value, float(default))
    return int(round(abs(number if number is not None else default)))


def _optional_integer(value: Any) -> int | None:
    number = _number(value)
    return int(round(abs(number))) if number is not None else None


def _parse_moment(
    row: dict[str, Any], *, target_date: str | None = None
) -> datetime | None:
    raw = str(row.get("source_timestamp") or row.get("timestamp") or "").strip()
    if len(raw) >= 14 and raw[:14].isdigit():
        try:
            return datetime.strptime(raw[:14], "%Y%m%d%H%M%S").replace(tzinfo=KST)
        except ValueError:
            pass
    raw_time = str(row.get("체결시간") or row.get("t") or row.get("time") or "").strip()
    date_text = str(target_date or "").strip()
    if not date_text:
        return None
    for fmt in ("%H:%M:%S", "%H:%M", "%H%M%S", "%H%M"):
        try:
            parsed_time = datetime.strptime(raw_time, fmt).time()
            parsed_date = datetime.strptime(date_text, "%Y-%m-%d").date()
            return datetime.combine(parsed_date, parsed_time, tzinfo=KST)
        except ValueError:
            continue
    return None


def _normalize_bar(
    row: dict[str, Any], *, target_date: str | None = None
) -> dict[str, Any] | None:
    moment = _parse_moment(row, target_date=target_date)
    if moment is None:
        return None
    return {
        "timestamp": moment.isoformat(),
        "minute": moment,
        "t": moment.strftime("%H:%M"),
        "o": _integer(row.get("시가", row.get("o", row.get("open")))),
        "h": _integer(row.get("고가", row.get("h", row.get("high")))),
        "l": _integer(row.get("저가", row.get("l", row.get("low")))),
        "c": _integer(
            row.get("현재가", row.get("c", row.get("close", row.get("price"))))
        ),
        "v": _integer(row.get("거래량", row.get("v", row.get("volume")))),
        "forming": bool(row.get("forming", False)),
        "partial_volume": bool(row.get("partial_volume", False)),
    }


def _session_anchor(session: str) -> dt_time:
    normalized = str(session or "").strip().lower()
    if "premarket" in normalized:
        return dt_time(8, 0)
    if "aftermarket" in normalized:
        return dt_time(16, 0)
    return dt_time(9, 0)


def _in_session(moment: datetime, session: str) -> bool:
    normalized = str(session or "").strip().lower()
    value = moment.time()
    if "premarket" in normalized:
        return dt_time(8, 0) <= value < dt_time(9, 0)
    if "aftermarket" in normalized:
        return value >= dt_time(16, 0)
    return dt_time(9, 0) <= value <= dt_time(15, 30)


def _scheduled_gap(
    previous: datetime, current: datetime, *, venue: str, session: str
) -> bool:
    return (
        str(venue or "").upper() == "KRX"
        and "regular" in str(session or "").lower()
        and previous.time() == dt_time(15, 19)
        and current.time() == dt_time(15, 30)
    )


def normalize_completed_bars(
    rows: list[dict[str, Any]],
    *,
    target_date: str | None,
    venue: str,
    session: str,
    as_of: datetime | None = None,
    sparse_observed_minutes_are_no_trade: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_minute: dict[datetime, dict[str, Any]] = {}
    duplicate_count = 0
    duplicate_conflict_count = 0
    invalid_count = 0
    market_route_conflict_count = 0
    excluded_other_date_count = 0
    excluded_other_session_count = 0
    forming_rows: list[dict[str, Any]] = []
    max_consecutive_missing_minutes = 0
    expected_venue = str(venue or "").strip().upper()
    try:
        expected_date = (
            datetime.strptime(str(target_date), "%Y-%m-%d").date()
            if target_date
            else None
        )
    except ValueError:
        expected_date = None
    for raw in rows or []:
        if not isinstance(raw, dict):
            invalid_count += 1
            continue
        normalized = _normalize_bar(raw, target_date=target_date)
        if normalized is None:
            invalid_count += 1
            continue
        if (
            min(normalized[key] for key in ("o", "h", "l", "c")) <= 0
            or normalized["h"] < max(normalized["o"], normalized["c"])
            or normalized["l"] > min(normalized["o"], normalized["c"])
        ):
            invalid_count += 1
            continue
        if expected_date is not None and normalized["minute"].date() != expected_date:
            excluded_other_date_count += 1
            continue
        if not _in_session(normalized["minute"], session):
            excluded_other_session_count += 1
            continue
        observed_venue = (
            str(
                raw.get("effective_venue")
                or raw.get("venue")
                or raw.get("market")
                or ""
            )
            .strip()
            .upper()
        )
        if (
            observed_venue
            and expected_venue
            and observed_venue not in {expected_venue, "UNKNOWN"}
        ):
            market_route_conflict_count += 1
        if (
            as_of is not None
            and normalized["minute"].date() == as_of.date()
            and normalized["minute"] + timedelta(minutes=1) > as_of
        ):
            normalized["forming"] = True
        minute = normalized["minute"]
        if normalized["forming"] or normalized["partial_volume"]:
            forming_rows.append(normalized)
            continue
        existing = by_minute.get(minute)
        if existing is not None:
            duplicate_count += 1
            if any(
                existing[key] != normalized[key] for key in ("o", "h", "l", "c", "v")
            ):
                duplicate_conflict_count += 1
        by_minute[minute] = normalized

    completed = [by_minute[key] for key in sorted(by_minute)]
    missing_minutes: list[str] = []
    scheduled_gap_count = 0
    for previous, current in zip(completed, completed[1:]):
        delta = int((current["minute"] - previous["minute"]).total_seconds() // 60)
        if delta <= 1:
            continue
        if _scheduled_gap(
            previous["minute"],
            current["minute"],
            venue=venue,
            session=session,
        ):
            scheduled_gap_count += 1
            continue
        max_consecutive_missing_minutes = max(
            max_consecutive_missing_minutes, delta - 1
        )
        for offset in range(1, delta):
            missing_minutes.append(
                (previous["minute"] + timedelta(minutes=offset)).strftime("%H:%M")
            )

    bounded_no_trade_gap = bool(
        sparse_observed_minutes_are_no_trade and max_consecutive_missing_minutes <= 3
    )
    blockers = []
    if not completed:
        blockers.append("no_completed_bars")
    if duplicate_conflict_count:
        blockers.append("duplicate_price_or_volume_conflict")
    if missing_minutes and not bounded_no_trade_gap:
        blockers.append("missing_completed_minutes")
    if invalid_count:
        blockers.append("invalid_minute_rows")
    if market_route_conflict_count:
        blockers.append("market_route_conflict")
    quality = {
        "status": "source_quality_blocked" if blockers else "pass",
        "blockers": blockers,
        "completed_bar_count": len(completed),
        "forming_bar_count": len(forming_rows),
        "duplicate_count": duplicate_count,
        "duplicate_conflict_count": duplicate_conflict_count,
        "invalid_row_count": invalid_count,
        "market_route_conflict_count": market_route_conflict_count,
        "excluded_other_date_count": excluded_other_date_count,
        "excluded_other_session_count": excluded_other_session_count,
        "missing_minute_count": len(missing_minutes),
        "missing_minutes": missing_minutes[:60],
        "observed_no_trade_minute_count": (
            len(missing_minutes) if bounded_no_trade_gap else 0
        ),
        "observed_no_trade_minutes": (
            missing_minutes[:60] if bounded_no_trade_gap else []
        ),
        "missing_source_minute_count": (
            0 if bounded_no_trade_gap else len(missing_minutes)
        ),
        "max_consecutive_missing_minute_count": max_consecutive_missing_minutes,
        "no_trade_gap_acceptance_max_consecutive_minutes": 3,
        "minute_gap_interpretation": (
            (
                "ka10080_no_trade_interval_no_synthetic_fill"
                if bounded_no_trade_gap
                else "ka10080_extended_gap_source_quality_blocked"
            )
            if sparse_observed_minutes_are_no_trade
            else "strict_missing_source_interval"
        ),
        "scheduled_call_auction_gap_count": scheduled_gap_count,
    }
    return completed, forming_rows, quality


def _public_bar(bar: dict[str, Any]) -> dict[str, Any]:
    return {key: bar.get(key) for key in ("timestamp", "t", "o", "h", "l", "c", "v")}


def resample_completed_bars(
    bars: list[dict[str, Any]],
    *,
    interval_min: int,
    session: str,
    as_of: datetime | None = None,
    sparse_observed_minutes_are_no_trade: bool = False,
) -> list[dict[str, Any]]:
    interval = max(1, int(interval_min))
    anchor = _session_anchor(session)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for bar in bars:
        moment = bar.get("minute")
        if not isinstance(moment, datetime):
            continue
        anchor_dt = datetime.combine(moment.date(), anchor, tzinfo=KST)
        offset = int((moment - anchor_dt).total_seconds() // 60)
        if offset < 0:
            continue
        grouped.setdefault((moment.date().isoformat(), offset // interval), []).append(
            bar
        )

    output: list[dict[str, Any]] = []
    for (_date_key, bucket), rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda item: item["minute"])
        anchor_dt = datetime.combine(rows[0]["minute"].date(), anchor, tzinfo=KST)
        bucket_start = anchor_dt + timedelta(minutes=bucket * interval)
        expected = [
            bucket_start + timedelta(minutes=index) for index in range(interval)
        ]
        observed = {row["minute"] for row in rows}
        wall_clock_complete = bool(
            as_of is not None and bucket_start + timedelta(minutes=interval) <= as_of
        )
        complete = all(item in observed for item in expected) or (
            sparse_observed_minutes_are_no_trade and wall_clock_complete and bool(rows)
        )
        omitted_minutes = [
            item.strftime("%H:%M") for item in expected if item not in observed
        ]
        output.append(
            {
                "interval_min": interval,
                "start": bucket_start.isoformat(),
                "end": (bucket_start + timedelta(minutes=interval)).isoformat(),
                "o": rows[0]["o"],
                "h": max(row["h"] for row in rows),
                "l": min(row["l"] for row in rows),
                "c": rows[-1]["c"],
                "v": sum(row["v"] for row in rows),
                "source_bar_count": len(rows),
                "expected_bar_count": interval,
                "source_quality": "pass" if complete else "source_quality_blocked",
                "missing_minutes": (
                    [] if sparse_observed_minutes_are_no_trade else omitted_minutes
                ),
                "observed_no_trade_minutes": (
                    omitted_minutes if sparse_observed_minutes_are_no_trade else []
                ),
                "minute_gap_interpretation": (
                    "no_trade_interval_no_synthetic_fill"
                    if sparse_observed_minutes_are_no_trade
                    else "strict_expected_minute"
                ),
            }
        )
    return output


def _opening_range(
    bars: list[dict[str, Any]],
    *,
    minutes: int,
    session: str,
    as_of: datetime | None = None,
    sparse_observed_minutes_are_no_trade: bool = False,
) -> dict[str, Any]:
    if not bars:
        return {"status": "source_quality_blocked", "reason": "no_completed_bars"}
    anchor = datetime.combine(
        bars[0]["minute"].date(), _session_anchor(session), tzinfo=KST
    )
    expected = [anchor + timedelta(minutes=index) for index in range(minutes)]
    by_minute = {bar["minute"]: bar for bar in bars}
    missing = [item for item in expected if item not in by_minute]
    selected = [by_minute[item] for item in expected if item in by_minute]
    window_complete = bool(
        as_of is not None and anchor + timedelta(minutes=minutes) <= as_of
    )
    if missing and not (
        sparse_observed_minutes_are_no_trade and window_complete and selected
    ):
        return {
            "status": "source_quality_blocked",
            "reason": "opening_range_missing_minutes",
            "missing_minutes": [item.strftime("%H:%M") for item in missing],
        }
    return {
        "status": "pass",
        "minutes": minutes,
        "high": max(row["h"] for row in selected),
        "low": min(row["l"] for row in selected),
        "open": selected[0]["o"],
        "close": selected[-1]["c"],
        "source_bar_count": len(selected),
        "observed_no_trade_minutes": (
            [item.strftime("%H:%M") for item in missing]
            if sparse_observed_minutes_are_no_trade
            else []
        ),
        "range_pct": (
            round(
                (
                    max(row["h"] for row in selected)
                    / min(row["l"] for row in selected)
                    - 1
                )
                * 100,
                6,
            )
            if min(row["l"] for row in selected) > 0
            else None
        ),
    }


def _session_bar_vwap(
    bars: list[dict[str, Any]],
    *,
    session: str,
    sparse_observed_minutes_are_no_trade: bool = False,
) -> dict[str, Any]:
    if not bars:
        return {
            "status": "source_quality_blocked",
            "reason": "no_completed_bars",
            "value": None,
        }
    expected_start = datetime.combine(
        bars[0]["minute"].date(), _session_anchor(session), tzinfo=KST
    )
    if bars[0]["minute"] != expected_start and not sparse_observed_minutes_are_no_trade:
        return {
            "status": "source_quality_blocked",
            "reason": "session_start_bar_missing",
            "value": None,
        }
    usable = [
        row for row in bars if row["v"] > 0 and min(row["h"], row["l"], row["c"]) > 0
    ]
    total_volume = sum(row["v"] for row in usable)
    if total_volume <= 0:
        return {
            "status": "source_quality_blocked",
            "reason": "positive_completed_volume_missing",
            "value": None,
        }
    numerator = sum(
        ((row["h"] + row["l"] + row["c"]) / 3.0) * row["v"] for row in usable
    )
    return {
        "status": "pass",
        "value": round(numerator / total_volume, 6),
        "formula": "sum(((high+low+close)/3)*volume)/sum(volume)",
        "completed_volume": total_volume,
        "source_bar_count": len(usable),
        "forming_bar_excluded": True,
        "zero_trade_minutes_synthetic_fill": False,
    }


def _return_windows(bars: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for minutes in (5, 15):
        selected = bars[-minutes:]
        if len(selected) < minutes or selected[0]["o"] <= 0:
            output[f"return_{minutes}m_pct"] = None
            output[f"direction_{minutes}m"] = "source_quality_blocked"
            continue
        value = round((selected[-1]["c"] / selected[0]["o"] - 1) * 100, 6)
        output[f"return_{minutes}m_pct"] = value
        output[f"direction_{minutes}m"] = (
            "up" if value > 0 else "down" if value < 0 else "flat"
        )
    return output


def _context_from_optional_rows(
    context: dict[str, Any],
    *,
    target_date: str,
    venue: str,
    session: str,
    as_of: datetime,
) -> dict[str, Any]:
    output = {key: value for key, value in context.items() if key != "minute_rows"}
    rows = context.get("minute_rows")
    if not isinstance(rows, list):
        return output
    completed, _forming, quality = normalize_completed_bars(
        rows,
        target_date=target_date,
        venue=venue,
        session=session,
        as_of=as_of,
    )
    output.update(_return_windows(completed))
    output["source_quality"] = quality
    return output


def derive_scalping_market_features(
    rows: list[dict[str, Any]],
    *,
    symbol: str,
    venue: str,
    session: str,
    target_date: str,
    captured_at: str | None = None,
    previous_day: dict[str, Any] | None = None,
    market_context: dict[str, Any] | None = None,
    sector_context: dict[str, Any] | None = None,
    minute_bar_source_api_id: str | None = None,
) -> dict[str, Any]:
    """Derive source-neutral features for observation or stage input wrappers."""
    capture_moment = None
    if captured_at:
        try:
            capture_moment = datetime.fromisoformat(captured_at)
            if capture_moment.tzinfo is None:
                capture_moment = capture_moment.replace(tzinfo=KST)
        except ValueError:
            capture_moment = None
    if capture_moment is None:
        capture_moment = datetime.now(KST)
    sparse_observed_minutes_are_no_trade = (
        str(minute_bar_source_api_id or "").strip().lower() == "ka10080"
    )
    completed, forming, quality = normalize_completed_bars(
        rows,
        target_date=target_date,
        venue=venue,
        session=session,
        as_of=capture_moment,
        sparse_observed_minutes_are_no_trade=sparse_observed_minutes_are_no_trade,
    )
    accepted_sparse_observed_minutes = (
        quality.get("minute_gap_interpretation")
        == "ka10080_no_trade_interval_no_synthetic_fill"
    )
    call_auction = [
        row
        for row in completed
        if str(venue or "").upper() == "KRX"
        and "regular" in str(session or "").lower()
        and row["minute"].time() == dt_time(15, 30)
    ]
    continuous_completed = [row for row in completed if row not in call_auction]
    derived_allowed = quality["status"] == "pass"
    resampled = {
        f"{interval}m": (
            resample_completed_bars(
                continuous_completed,
                interval_min=interval,
                session=session,
                as_of=capture_moment,
                sparse_observed_minutes_are_no_trade=(accepted_sparse_observed_minutes),
            )
            if derived_allowed
            else []
        )
        for interval in INTERVALS
    }
    multi = {
        key: [row for row in rows_for_interval if row["source_quality"] == "pass"]
        for key, rows_for_interval in resampled.items()
    }
    incomplete_multi = {
        key: [row for row in rows_for_interval if row["source_quality"] != "pass"]
        for key, rows_for_interval in resampled.items()
    }
    previous = dict(previous_day or {})
    stock_windows = _return_windows(continuous_completed) if derived_allowed else {}
    market = _context_from_optional_rows(
        dict(market_context or {}),
        target_date=target_date,
        venue=venue,
        session=session,
        as_of=capture_moment,
    )
    sector = _context_from_optional_rows(
        dict(sector_context or {}),
        target_date=target_date,
        venue=venue,
        session=session,
        as_of=capture_moment,
    )
    relative: dict[str, Any] = {}
    for minutes in (5, 15):
        stock_return = _number(stock_windows.get(f"return_{minutes}m_pct"))
        sector_return = _number(
            sector.get(f"sector_return_{minutes}m_pct"),
            _number(sector.get(f"return_{minutes}m_pct")),
        )
        relative[f"sector_relative_return_{minutes}m_pct"] = (
            round(stock_return - sector_return, 6)
            if stock_return is not None and sector_return is not None
            else None
        )
    return {
        "symbol": str(symbol),
        "venue": str(venue),
        "session": str(session),
        "target_date": str(target_date),
        "captured_at": captured_at or capture_moment.isoformat(),
        "bars_1m_completed": [_public_bar(row) for row in continuous_completed],
        "closing_call_auction_bars": [_public_bar(row) for row in call_auction],
        "forming_bars": [_public_bar(row) for row in forming],
        "multi_timeframe_bars": multi,
        "incomplete_multi_timeframe_bars": incomplete_multi,
        "session_bar_vwap": (
            _session_bar_vwap(
                continuous_completed,
                session=session,
                sparse_observed_minutes_are_no_trade=(accepted_sparse_observed_minutes),
            )
            if derived_allowed
            else {
                "status": "source_quality_blocked",
                "reason": "minute_source_quality_blocked",
                "value": None,
            }
        ),
        "opening_range_5m": (
            _opening_range(
                continuous_completed,
                minutes=5,
                session=session,
                as_of=capture_moment,
                sparse_observed_minutes_are_no_trade=(accepted_sparse_observed_minutes),
            )
            if derived_allowed
            else {
                "status": "source_quality_blocked",
                "reason": "minute_source_quality_blocked",
            }
        ),
        "opening_range_15m": (
            _opening_range(
                continuous_completed,
                minutes=15,
                session=session,
                as_of=capture_moment,
                sparse_observed_minutes_are_no_trade=(accepted_sparse_observed_minutes),
            )
            if derived_allowed
            else {
                "status": "source_quality_blocked",
                "reason": "minute_source_quality_blocked",
            }
        ),
        "previous_day_levels": {
            "date": previous.get("date"),
            "high": _optional_integer(previous.get("high")),
            "low": _optional_integer(previous.get("low")),
            "close": _optional_integer(previous.get("close")),
            "source": previous.get("source"),
            "request_code": previous.get("request_code"),
            "venue_basis": previous.get("venue_basis"),
            "source_quality": previous.get("source_quality", "missing"),
            "reason": previous.get("reason"),
        },
        "market_context": market,
        "sector_context": {
            **sector,
            **{
                f"stock_{key}": value
                for key, value in stock_windows.items()
                if key.startswith("return_")
            },
            **relative,
        },
        "source_quality": quality,
    }


def build_market_context_observation(
    rows: list[dict[str, Any]],
    *,
    symbol: str,
    venue: str,
    session: str,
    target_date: str,
    captured_at: str | None = None,
    previous_day: dict[str, Any] | None = None,
    market_context: dict[str, Any] | None = None,
    sector_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap shared deterministic features in the forensics-only contract."""

    return {
        "schema": SCHEMA,
        **derive_scalping_market_features(
            rows,
            symbol=symbol,
            venue=venue,
            session=session,
            target_date=target_date,
            captured_at=captured_at,
            previous_day=previous_day,
            market_context=market_context,
            sector_context=sector_context,
        ),
        **OBSERVATION_CONTRACT,
    }
