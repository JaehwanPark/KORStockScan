"""Source-only replay for stocks that may fit the independent Samsung machines.

The caller supplies completed Kiwoom one-minute bars.  This module never calls a
broker, account, token, or order API and never grants runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
REPORT_SCHEMA = "samsung_like_machine_candidate_scan_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
MIN_COVERAGE_DAYS = 20
MIN_COMPLETED_LEGS = 10
DEFAULT_OUTPUT_DIR = DATA_DIR / "report" / "samsung_like_machine_candidate_scan"
MACHINE_WINDOWS = {
    "midday": (time(13, 15), time(13, 54)),
    "afternoon": (time(14, 0), time(14, 40)),
}
METRIC_CONTRACT = {
    "metric_role": "source_only_cross_symbol_machine_suitability_replay",
    "decision_authority": "candidate_discovery_only_no_runtime_or_order_authority",
    "window_policy": "clean_baseline_completed_1m_sor_and_nxt_sessions",
    "sample_floor": {
        "coverage_days": MIN_COVERAGE_DAYS,
        "completed_legs": MIN_COMPLETED_LEGS,
    },
    "primary_decision_metric": [
        "completed_target_legs_per_attempted_leg",
        "held_legs",
        "notional_weighted_realized_ev_pct",
    ],
    "source_quality_gate": [
        "official_ka10080_continuation_reaches_requested_start",
        "valid_unique_completed_one_minute_ohlcv",
        "sor_regular_not_split_into_krx_and_nxt_regular",
        "nxt_used_only_for_premarket_morning_leg_and_its_owned_target",
    ],
    "forbidden_uses": [
        "price_touch_as_actual_fill_evidence",
        "same_bar_fill_then_target_sequence_assumption",
        "real_order_submission_or_runtime_enablement",
        "automatic_symbol_addition",
        "threshold_provider_bot_cap_or_broker_guard_change",
        "stop_loss_or_forced_exit_creation",
    ],
}


def _timestamp(row: dict[str, Any]) -> datetime | None:
    raw = str(row.get("source_timestamp") or "")[:14]
    try:
        return datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except ValueError:
        return None


def _bars_by_day(rows: Iterable[dict[str, Any]]) -> dict[date, list[dict[str, Any]]]:
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        timestamp = _timestamp(raw)
        key = timestamp.isoformat() if timestamp else ""
        try:
            prices = [int(raw[name]) for name in ("open", "high", "low", "close")]
        except (KeyError, TypeError, ValueError):
            continue
        if (
            timestamp is None
            or not key
            or key in seen
            or min(prices) <= 0
            or prices[1] < max(prices[0], prices[2], prices[3])
            or prices[2] > min(prices[0], prices[1], prices[3])
        ):
            continue
        seen.add(key)
        grouped[timestamp.date()].append(
            {
                "timestamp": timestamp,
                "open": prices[0],
                "high": prices[1],
                "low": prices[2],
                "close": prices[3],
            }
        )
    for day in grouped:
        grouped[day].sort(key=lambda item: item["timestamp"])
    return dict(grouped)


def _leg_outcome(
    *,
    entry_price: int,
    entry_bars: list[dict[str, Any]],
    target_bars: list[dict[str, Any]],
    cost_pct: float,
) -> dict[str, Any]:
    fill_index = next(
        (index for index, bar in enumerate(entry_bars) if bar["low"] <= entry_price),
        None,
    )
    if fill_index is None:
        return {"status": "NO_FILL", "entry_price": entry_price}
    fill_bar = entry_bars[fill_index]
    target_price = move_price_by_ticks(entry_price, 2)
    # A one-minute OHLC bar cannot establish low-before-high ordering.  Target
    # evaluation therefore begins strictly after the fill bar.
    eligible_targets = [
        bar for bar in target_bars if bar["timestamp"] > fill_bar["timestamp"]
    ]
    completed = any(bar["high"] >= target_price for bar in eligible_targets)
    result = {
        "status": "COMPLETE" if completed else "HELD",
        "entry_price": entry_price,
        "target_price": target_price,
        "fill_at": fill_bar["timestamp"].isoformat(),
    }
    if completed:
        result["net_profit_pct"] = round(
            (target_price / entry_price - 1.0) * 100.0 - cost_pct, 6
        )
    return result


def _regular_episodes(
    rows: Iterable[dict[str, Any]], *, machine: str, cost_pct: float
) -> tuple[int, list[dict[str, Any]]]:
    start, end = MACHINE_WINDOWS[machine]
    grouped = _bars_by_day(rows)
    episodes: list[dict[str, Any]] = []
    for day, bars in sorted(grouped.items()):
        regular = [
            bar for bar in bars if time(9, 0) <= bar["timestamp"].time() < time(15, 30)
        ]
        signal_index = None
        signal: dict[str, Any] | None = None
        for index, candidate in enumerate(regular):
            if not start <= candidate["timestamp"].time() <= end or index < 29:
                continue
            window = regular[index - 29 : index + 1]
            if any(
                current["timestamp"] - previous["timestamp"] != timedelta(minutes=1)
                for previous, current in zip(window, window[1:])
            ):
                continue
            rolling_high = max(bar["high"] for bar in window)
            rolling_low = min(bar["low"] for bar in window)
            drawdown = (rolling_high - candidate["close"]) / rolling_high * 100.0
            near_low = (candidate["close"] - rolling_low) / rolling_low * 100.0
            if drawdown + 1e-12 >= 1.25 and near_low - 1e-12 <= 0.20:
                signal_index = index
                signal = candidate
                break
        if signal_index is None or signal is None:
            continue
        close = clamp_price_to_tick(signal["close"])
        entry_bars = regular[signal_index + 1 : signal_index + 6]
        target_bars = regular[signal_index + 1 :]
        legs = [
            _leg_outcome(
                entry_price=price,
                entry_bars=entry_bars,
                target_bars=target_bars,
                cost_pct=cost_pct,
            )
            for price in (close, move_price_by_ticks(close, -1))
        ]
        episodes.append(
            {
                "date": day.isoformat(),
                "signal_at": signal["timestamp"].isoformat(),
                "signal_close": signal["close"],
                "legs": legs,
            }
        )
    return len(grouped), episodes


def _morning_episodes(
    sor_rows: Iterable[dict[str, Any]],
    nxt_rows: Iterable[dict[str, Any]],
    *,
    cost_pct: float,
) -> tuple[int, list[dict[str, Any]]]:
    sor_by_day = _bars_by_day(sor_rows)
    nxt_by_day = _bars_by_day(nxt_rows)
    covered_days = sorted(set(sor_by_day) & set(nxt_by_day))
    episodes: list[dict[str, Any]] = []
    for day in covered_days:
        sor = sor_by_day[day]
        nxt = nxt_by_day[day]
        nxt_entry = [
            bar for bar in nxt if time(8, 0) <= bar["timestamp"].time() <= time(8, 10)
        ]
        sor_entry = [
            bar for bar in sor if time(9, 0) <= bar["timestamp"].time() <= time(9, 30)
        ]
        if not nxt_entry or not sor_entry:
            continue
        nxt_open = nxt_entry[0]["open"]
        sor_open = sor_entry[0]["open"]
        nxt_base = clamp_price_to_tick(nxt_open * 0.97)
        sor_base = clamp_price_to_tick(sor_open * 0.9925)
        nxt_prices = [move_price_by_ticks(nxt_base, 1), nxt_base]
        sor_prices = [move_price_by_ticks(sor_base, 1), sor_base]
        legs: list[dict[str, Any]] = []
        for index, nxt_price in enumerate(nxt_prices):
            nxt_result = _leg_outcome(
                entry_price=nxt_price,
                entry_bars=nxt_entry,
                target_bars=nxt,
                cost_pct=cost_pct,
            )
            if nxt_result["status"] != "NO_FILL":
                nxt_result["route"] = "NXT"
                legs.append(nxt_result)
                continue
            sor_result = _leg_outcome(
                entry_price=sor_prices[index],
                entry_bars=sor_entry,
                target_bars=sor,
                cost_pct=cost_pct,
            )
            sor_result["route"] = "SOR"
            legs.append(sor_result)
        episodes.append({"date": day.isoformat(), "legs": legs})
    return len(covered_days), episodes


def _summary(
    coverage_days: int,
    episodes: list[dict[str, Any]],
    *,
    source_quality_ready: bool,
) -> dict[str, Any]:
    legs = [leg for episode in episodes for leg in episode["legs"]]
    completed = [leg for leg in legs if leg["status"] == "COMPLETE"]
    held = [leg for leg in legs if leg["status"] == "HELD"]
    attempted_notional = sum(int(leg["entry_price"]) for leg in legs)
    realized_profit = sum(
        int(leg["entry_price"]) * float(leg["net_profit_pct"]) / 100.0
        for leg in completed
    )
    realized_ev = (
        round(realized_profit / attempted_notional * 100.0, 6)
        if attempted_notional
        else None
    )
    if not source_quality_ready:
        status = "source_quality_blocked"
    elif coverage_days < MIN_COVERAGE_DAYS:
        status = "source_coverage_insufficient"
    elif len(completed) < MIN_COMPLETED_LEGS:
        status = "collect_more_completed_targets"
    elif realized_ev is None or realized_ev <= 0:
        status = "reject_non_positive_realized_ev_proxy"
    elif held:
        status = "research_candidate_has_unresolved_hold_proxy"
    else:
        status = "implementation_candidate_source_only"
    return {
        "coverage_days": coverage_days,
        "source_quality_ready": source_quality_ready,
        "signal_episodes": len(episodes),
        "attempted_legs": len(legs),
        "completed_legs": len(completed),
        "no_fill_legs": sum(leg["status"] == "NO_FILL" for leg in legs),
        "held_legs": len(held),
        "completed_target_legs_per_attempted_leg": (
            round(len(completed) / len(legs), 6) if legs else None
        ),
        "notional_weighted_realized_ev_pct": realized_ev,
        "status": status,
    }


def build_report(
    *,
    symbols: dict[str, dict[str, Any]],
    start_date: str,
    end_date: str,
    cost_pct: float = 0.20,
) -> dict[str, Any]:
    parsed_start = date.fromisoformat(start_date)
    parsed_end = date.fromisoformat(end_date)
    if parsed_start < CLEAN_BASELINE_DATE or parsed_start > parsed_end:
        raise ValueError("invalid_or_pre_clean_baseline_date_range")
    if not math.isfinite(cost_pct) or not 0 <= cost_pct < 100:
        raise ValueError("cost_pct_must_be_finite_percentage")
    results: dict[str, Any] = {}
    ranking: list[dict[str, Any]] = []
    for code, source in symbols.items():
        sor_rows = [
            row
            for row in (source.get("sor_bars") or [])
            if isinstance(row, dict)
            and (timestamp := _timestamp(row)) is not None
            and parsed_start <= timestamp.date() <= parsed_end
        ]
        nxt_rows = [
            row
            for row in (source.get("nxt_bars") or [])
            if isinstance(row, dict)
            and (timestamp := _timestamp(row)) is not None
            and parsed_start <= timestamp.date() <= parsed_end
        ]
        source_meta = source.get("source_meta") or {}
        sor_meta = source_meta.get("SOR")
        nxt_meta = source_meta.get("NXT")
        sor_source_ready = (
            isinstance(sor_meta, dict)
            and sor_meta.get("source_quality_status") == "PASS"
        )
        nxt_source_ready = (
            isinstance(nxt_meta, dict)
            and nxt_meta.get("source_quality_status") == "PASS"
        )
        machines: dict[str, Any] = {}
        morning_coverage, morning = _morning_episodes(
            sor_rows, nxt_rows, cost_pct=cost_pct
        )
        machines["morning"] = _summary(
            morning_coverage,
            morning,
            source_quality_ready=sor_source_ready and nxt_source_ready,
        )
        for machine in MACHINE_WINDOWS:
            coverage, episodes = _regular_episodes(
                sor_rows, machine=machine, cost_pct=cost_pct
            )
            machines[machine] = _summary(
                coverage, episodes, source_quality_ready=sor_source_ready
            )
        results[code] = {
            "name": str(source.get("name") or code),
            "source_meta": source_meta,
            "machines": machines,
        }
        for machine, summary in machines.items():
            ranking.append(
                {
                    "symbol": code,
                    "name": results[code]["name"],
                    "machine": machine,
                    **summary,
                }
            )
    status_priority = {
        "implementation_candidate_source_only": 4,
        "research_candidate_has_unresolved_hold_proxy": 3,
        "collect_more_completed_targets": 2,
        "reject_non_positive_realized_ev_proxy": 1,
        "source_coverage_insufficient": 0,
        "source_quality_blocked": -1,
    }
    ranking.sort(
        key=lambda item: (
            status_priority.get(item["status"], -2),
            item["held_legs"] == 0,
            item["notional_weighted_realized_ev_pct"] or -999.0,
            item["completed_legs"],
        ),
        reverse=True,
    )
    return {
        "schema": REPORT_SCHEMA,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "start_date": start_date,
        "end_date": end_date,
        "cost_pct": cost_pct,
        "metric_contract": METRIC_CONTRACT,
        "symbols": results,
        "ranking": ranking,
        "decision": "source_only_candidate_discovery_no_symbol_runtime_promotion",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def write_report(
    report: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"samsung_like_machine_candidate_scan_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_content = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        f"# Samsung-like machine candidate scan — {report['end_date']}",
        "",
        "Source-only minute-touch replay. No symbol was added to live runtime.",
        "",
        "| Rank | Symbol | Name | Machine | Status | Days | Signals | Complete | Held | EV proxy |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(report["ranking"], 1):
        lines.append(
            f"| {index} | {row['symbol']} | {row['name']} | {row['machine']} | "
            f"{row['status']} | {row['coverage_days']} | {row['signal_episodes']} | "
            f"{row['completed_legs']} | {row['held_legs']} | "
            f"{row['notional_weighted_realized_ev_pct']} |"
        )
    _atomic_write(json_path, json_content)
    _atomic_write(md_path, "\n".join(lines) + "\n")
    return json_path, md_path


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def report_sha256(report: dict[str, Any]) -> str:
    """Return a stable digest for provenance in an external fetch wrapper."""
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
