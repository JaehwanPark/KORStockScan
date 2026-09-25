"""Exploratory trailing-exit scenarios over legacy completed trade displays.

This is an assumption-based sensitivity study. Missing paths contribute a
neutral zero *scenario change*, never a zero realized PnL or a live candidate.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.market import session_contract
from src.engine.scalping.trailing_start_replay import _epoch, _number
from src.engine.scalping.trailing_threshold_policy import (
    START_MARKETS, THRESHOLD_KEYS, default_values, market_type_at,
)
from src.engine.trade_profit import get_trade_cost_rate

SCHEMA = "scalp_trailing_legacy_neutral_scenario_v1"
GRID = {
    THRESHOLD_KEYS[0]: (0.4, 0.6, 0.8),
    THRESHOLD_KEYS[1]: (65, 75, 85),
    THRESHOLD_KEYS[2]: (0.3, 0.4, 0.5),
    THRESHOLD_KEYS[3]: (0.6, 0.8, 1.0),
}
SLIPPAGE_BPS = (0, 30, 100)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _peak_mfe(trade: dict) -> float | None:
    signal = trade.get("exit_signal") or {}
    fields = signal.get("fields") or {}
    for raw in (fields.get("mfe_pct"), trade.get("mfe_pct")):
        value = _number(raw)
        if value is not None and -100 < value < 1000:
            return value
    return None


def _prepare(trade: dict, *, clean_start: str, cost_rate: float) -> dict:
    trade_id = str(trade.get("id") or "")
    base = {"id": trade_id, "source_grade": "excluded", "reason": None}
    entry_date = str(trade.get("rec_date") or "")[:10]
    completion_date = str(
        trade.get("completion_observed_date") or trade.get("exact_sell_fill_time")
        or trade.get("sell_time") or ""
    )[:10]
    if (str(trade.get("status") or "").upper() != "COMPLETED"
            or str(trade.get("strategy") or "").upper() not in {"SCALP", "SCALPING"}
            or entry_date < clean_start or completion_date < clean_start):
        return {**base, "reason": "outside_completed_clean_main_scope"}
    if completion_date < entry_date:
        return {**base, "reason": "completion_before_entry_day"}
    buy = _number(trade.get("buy_price"))
    sell = _number(trade.get("sell_price"))
    qty = _number(trade.get("buy_qty"))
    profit = _number(trade.get("profit_rate"))
    if (buy is None or buy <= 0 or sell is None or sell <= 0
            or qty is None or qty <= 0 or profit is None):
        return {**base, "reason": "missing_price_quantity_or_valid_profit"}
    sell_at = _epoch(trade.get("exact_sell_fill_time") or trade.get("sell_time"))
    market = market_type_at(sell_at) if sell_at is not None else None
    if market not in START_MARKETS:
        return {**base, "reason": "sell_market_clock_unidentified"}
    buy_at = _epoch(trade.get("buy_time"))
    if buy_at is not None and buy_at > sell_at:
        return {**base, "reason": "sell_before_buy_clock"}
    signal = trade.get("exit_signal") or {}
    mfe = _peak_mfe(trade)
    modeled_sell_net_pct = 100 * (sell * (1 - cost_rate) / buy - 1)
    mfe_conflicts_with_sell = mfe is not None and mfe + 0.1 < modeled_sell_net_pct
    grade = (
        "neutral_inconsistent_mfe" if mfe_conflicts_with_sell
        else
        "reported_mfe_assumed_peak_to_sell_path" if mfe is not None
        else "inferred_trailing_rule_assumed_peak_to_sell_path"
        if signal.get("exit_rule") == "scalp_trailing_take_profit"
        else "neutral_unknown_peak"
    )
    recorded_cost = bool(
        trade.get("realized_pnl_krw_source") == "broker_fill_prices_fee_aware"
        and _number(trade.get("realized_pnl_krw")) is not None
        and _number(trade.get("main_lifecycle_fees_taxes_krw")) is not None
        and trade.get("exact_sell_fill_time")
    )
    return {
        **base, "source_grade": grade, "market": market, "buy": buy,
        "sell": sell, "qty": qty, "profit_rate": profit,
        "completion_day": completion_date,
        "notional": buy * qty, "mfe_pct": None if mfe_conflicts_with_sell else mfe,
        "cost_rate": cost_rate,
        "exit_rule_provenance": "inferred" if signal.get("inferred") else "observed",
        "cost_evidence": (
            "recorded_fill_cost" if recorded_cost
            else "reported_net_profit_rate_cost_unverified"
        ),
        "buy_clock_status": "observed" if buy_at is not None else "missing",
        "current_exit_clock_allowed": session_contract.resolve_market_session(
            datetime.fromtimestamp(sell_at, ZoneInfo("Asia/Seoul"))
        ).exit_allowed_by_clock,
    }


def _scenario_sell_price(
    row: dict, vector: dict[str, float | int], incumbent: dict[str, float | int],
    *, strong: bool,
) -> float | None:
    if row["source_grade"].startswith("neutral_"):
        return None
    active_key = THRESHOLD_KEYS[3] if strong else THRESHOLD_KEYS[2]
    mfe = row["mfe_pct"]
    if mfe is not None:
        peak = row["buy"] * (1 + mfe / 100) / (1 - row["cost_rate"])
    else:
        # Conditional historical hypothesis: the inferred old trailing rule
        # first crossed its incumbent width at the recorded SELL price.
        peak = row["sell"] / (1 - incumbent[active_key] / 100)
    peak = max(peak, row["sell"])
    peak_net_pct = 100 * (peak * (1 - row["cost_rate"]) / row["buy"] - 1)
    if peak_net_pct + 1e-9 < vector[THRESHOLD_KEYS[0]]:
        return None
    crossing = peak * (1 - vector[active_key] / 100)
    if crossing + 1e-9 < row["sell"]:
        return None  # Later-than-observed path is unknown; neutral scenario.
    return crossing


def _score_rows(
    rows: list[dict], vector: dict[str, float | int], incumbent: dict[str, float | int],
) -> dict:
    capital = sum(row["notional"] for row in rows)
    scenario = {}
    for branch in ("weak", "strong"):
        strong = branch == "strong"
        by_slippage = {}
        for slippage_bps in SLIPPAGE_BPS:
            delta_notional = 0.0
            modeled_ids = []
            neutral_ids = []
            for row in rows:
                candidate_price = _scenario_sell_price(
                    row, vector, incumbent, strong=strong,
                )
                baseline_price = _scenario_sell_price(
                    row, incumbent, incumbent, strong=strong,
                )
                if candidate_price is None:
                    neutral_ids.append(row["id"])
                    continue
                if baseline_price is None:
                    baseline_price = row["sell"]
                if abs(candidate_price - baseline_price) <= 1e-9:
                    modeled_ids.append(row["id"])
                    continue
                # Reported net return anchors the result; the configured cost
                # and slippage are scenario assumptions on the marginal SELL.
                candidate_after_cost = candidate_price * (
                    1 - row["cost_rate"] - slippage_bps / 10_000
                )
                baseline_after_cost = baseline_price * (1 - row["cost_rate"])
                delta_notional += row["qty"] * (
                    candidate_after_cost - baseline_after_cost
                )
                modeled_ids.append(row["id"])
            by_slippage[str(slippage_bps)] = {
                "neutral_scenario_delta_pct": (
                    round(100 * delta_notional / capital, 6) if capital else None
                ),
                "modeled_ids": sorted(modeled_ids),
                "neutral_unknown_effect_ids": sorted(neutral_ids),
            }
        scenario[branch] = by_slippage
    return scenario


def summarize_legacy_neutral_scenarios(
    trades: list[dict], *, clean_start: str, source_gap_dates: list[dict],
) -> dict:
    """Maximize identifiable legacy coverage without creating live evidence."""

    cost_rate = get_trade_cost_rate()
    incumbent = default_values()
    prepared = [_prepare(row, clean_start=clean_start, cost_rate=cost_rate)
                for row in trades]
    counts = Counter(row["id"] for row in prepared)
    for row in prepared:
        if counts[row["id"]] > 1:
            row.update(source_grade="excluded", reason="duplicate_completed_position_id")
    usable = [row for row in prepared
              if row.get("market") in START_MARKETS and not row.get("reason")]
    result = {
        "schema": SCHEMA, "metric_role": "source_quality_gate",
        "decision_authority": "historical_scenario_diagnostic_only",
        "window_policy": "clean_baseline_completed_display_through_target_date",
        "sample_floor": "all_identifiable_legacy_completed_rows_with_valid_profit",
        "primary_decision_metric": "neutral_scenario_delta_pct_not_realized_ev",
        "source_quality_gate": "assumption_and_neutral_coverage_disclosed",
        "forbidden_uses": "threshold_apply|runtime_selection|actual_fill_or_cost_claim|primary_ev",
        "source_gap_dates": source_gap_dates,
        "input_projection_sha256": _digest(sorted(((
            str(row.get("id")), str(row.get("rec_date")),
            str(row.get("completion_observed_date")), str(row.get("buy_price")),
            str(row.get("buy_qty")), str(row.get("sell_price")),
            str(row.get("sell_time")), str(row.get("exact_sell_fill_time")),
            str(row.get("profit_rate")),
            str((row.get("exit_signal") or {}).get("exit_rule")),
            str(_peak_mfe(row)),
        ) for row in trades), key=lambda item: str(item[0]))),
        "reported_completed_ids": sorted(row["id"] for row in prepared),
        "duplicate_completed_ids": sorted(
            trade_id for trade_id, count in counts.items() if count > 1
        ),
        "excluded_by_id": {row["id"]: row["reason"] for row in prepared if row["reason"]},
        "source_grade_counts": dict(Counter(row["source_grade"] for row in usable)),
        "cost_evidence_counts": dict(Counter(row["cost_evidence"] for row in usable)),
        "buy_clock_status_counts": dict(Counter(row["buy_clock_status"] for row in usable)),
        "cost_model_rate": cost_rate, "slippage_sensitivity_bps": list(SLIPPAGE_BPS),
        "score_path_status": "unidentified_neutral_no_threshold_score_effect",
        "assumed_path": "entry_to_peak_to_recorded_sell_no_clock_or_depth_reconstruction",
        "incumbent_projection": incumbent, "grid": {key: list(values) for key, values in GRID.items()},
        "grid_sha256": _digest(GRID), "markets": {},
        "research_candidate": None, "runtime_selected": None,
    }
    for market in START_MARKETS:
        market_rows = [row for row in usable if row["market"] == market]
        market_days = sorted({row["completion_day"] for row in market_rows})
        holdout_days = set(
            market_days[-max(2, math.ceil(len(market_days) * .2)):]
        ) if len(market_days) >= 3 else set()
        train_rows = [row for row in market_rows
                      if row["completion_day"] not in holdout_days]
        holdout_rows = [row for row in market_rows
                        if row["completion_day"] in holdout_days]
        def score(vector: dict[str, float | int]) -> dict:
            return {
                **_score_rows(market_rows, vector, incumbent),
                "train": _score_rows(train_rows, vector, incumbent),
                "holdout": _score_rows(holdout_rows, vector, incumbent),
            }
        single = {}
        for axis in THRESHOLD_KEYS:
            candidates = {}
            for value in GRID[axis]:
                vector = {**incumbent, axis: value}
                if vector[THRESHOLD_KEYS[3]] < vector[THRESHOLD_KEYS[2]]:
                    continue
                candidates[str(value)] = score(vector)
            single[axis] = candidates
        combinations = {}
        for values in itertools.product(*(GRID[axis] for axis in THRESHOLD_KEYS)):
            vector = dict(zip(THRESHOLD_KEYS, values))
            if vector[THRESHOLD_KEYS[3]] < vector[THRESHOLD_KEYS[2]]:
                continue
            label = "|".join(map(str, values))
            combinations[label] = score(vector)
        result["markets"][market] = {
            "n": len(market_rows), "ids": sorted(row["id"] for row in market_rows),
            "holdout_date_basis": "observed_completion_or_sell_time_date",
            "holdout_days": sorted(holdout_days),
            "train_n": len(train_rows), "holdout_n": len(holdout_rows),
            "current_exit_clock_blocked_ids": sorted(
                row["id"] for row in market_rows
                if not row["current_exit_clock_allowed"]
            ),
            "source_grade_counts": dict(Counter(row["source_grade"] for row in market_rows)),
            "single_axis": single, "combinations": combinations,
            "combination_count": len(combinations),
        }
    return result
