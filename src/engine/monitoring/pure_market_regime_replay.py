"""Regime-conditioned pure-market walk-forward backtest.

The controller does not invert every signal. It selects a weak-market
capitulation mode or a bullish-transition/strong-trend recovery mode from
completed Samsung and KOSPI one-minute bars available at that timestamp.
Historic widget states, AI output, orders, and future outcomes are forbidden
decision inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from src.engine.monitoring import pure_market_reversal_replay as base

KST = ZoneInfo("Asia/Seoul")
DEFAULT_OUTPUT_DIR = Path("data/report/pure_market_regime_replay")
REGIME_STATES = (
    "WEAK_DOWNTREND",
    "BEARISH_TRANSITION",
    "NEUTRAL_TRANSITION",
    "BULLISH_TRANSITION",
    "STRONG_UPTREND",
)
MODE_CONTRACT = {
    "weak_capitulation": {
        "strategy_mode": "capitulation_probe",
        "allowed_entry_regimes": ["WEAK_DOWNTREND", "BEARISH_TRANSITION"],
        "exit_regimes": ["BULLISH_TRANSITION", "STRONG_UPTREND"],
        "exit_regime_confirmations": 2,
        "meaning": "near-trough probe after downside extension stabilizes",
    },
    "bullish_recovery": {
        "strategy_mode": "confirmed_recovery",
        "allowed_entry_regimes": ["BULLISH_TRANSITION", "STRONG_UPTREND"],
        "exit_regimes": ["BEARISH_TRANSITION", "WEAK_DOWNTREND"],
        "exit_regime_confirmations": 2,
        "meaning": "normal recovery entry during bullish inflection or trend",
    },
}
REGIME_CONTRACT = {
    "metric_role": "causal_market_regime_router_for_offline_research",
    "decision_authority": "offline_pure_market_regime_replay_only",
    "window_policy": "completed_1m_3m_5m_15m_and_session_vwap",
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct_by_venue_and_mode",
    "source_quality_gate": (
        "completed_samsung_ka10080_and_timestamp_aligned_kospi_ka20005_for_"
        "krx_and_nxt_regular;instrument_only_explicit_for_nxt_pre_after"
    ),
    "forbidden_uses": [
        "historic_widget_entry_or_exit_state",
        "historic_ai_or_order_input",
        "future_bar_regime_assignment",
        "same_date_policy_selection",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}


@dataclass(frozen=True)
class RegimePoint:
    timestamp: datetime
    state: str
    source_quality: str
    features: dict[str, float | None]


def default_mode_policy_grids() -> dict[str, list[base.Policy]]:
    weak: list[base.Policy] = []
    for lookback in (15, 30):
        for drawdown in (1.00, 1.50):
            for target in (0.40, 0.80):
                for max_hold in (10, 20):
                    weak.append(
                        base.Policy(
                            lookback_bars=lookback,
                            drawdown_pct=drawdown,
                            stabilization_bars=1,
                            reclaim_pct=0.0,
                            max_chase_pct=0.50,
                            rebound_volume_ratio=0.0,
                            target_pct=target,
                            stop_pct=0.80,
                            trailing_arm_pct=0.40,
                            trailing_drawdown_pct=0.20,
                            max_hold_bars=max_hold,
                        )
                    )
    bullish: list[base.Policy] = []
    for lookback in (15, 30):
        for drawdown in (0.75, 1.50):
            for stabilization in (1, 2):
                for target in (3.00, 5.00):
                    for trailing_drawdown in (0.80, 1.50):
                        for max_hold in (20, 40):
                            bullish.append(
                                base.Policy(
                                    lookback_bars=lookback,
                                    drawdown_pct=drawdown,
                                    stabilization_bars=stabilization,
                                    reclaim_pct=0.10,
                                    max_chase_pct=1.20,
                                    rebound_volume_ratio=0.80,
                                    target_pct=target,
                                    stop_pct=1.20,
                                    trailing_arm_pct=1.00,
                                    trailing_drawdown_pct=trailing_drawdown,
                                    max_hold_bars=max_hold,
                                )
                            )
    return {"weak_capitulation": weak, "bullish_recovery": bullish}


def _pct(current: float, prior: float) -> float | None:
    if current <= 0 or prior <= 0:
        return None
    return (current / prior - 1.0) * 100.0


def _window_return(
    bar: base.Bar,
    by_timestamp: dict[datetime, base.Bar],
    minutes: int,
) -> float | None:
    prior = by_timestamp.get(bar.timestamp - timedelta(minutes=minutes))
    if prior is None:
        return None
    return _pct(float(bar.close), float(prior.close))


def _session_vwap(series: Sequence[base.Bar], index: int) -> float | None:
    observed = series[: index + 1]
    volume = sum(max(0, bar.volume) for bar in observed)
    if volume <= 0:
        return None
    return sum(bar.close * max(0, bar.volume) for bar in observed) / volume


def _raw_regime(features: dict[str, float | None]) -> str:
    stock3 = features.get("stock_return_3m_pct")
    stock5 = features.get("stock_return_5m_pct")
    stock15 = features.get("stock_return_15m_pct")
    index3 = features.get("kospi_return_3m_pct")
    index5 = features.get("kospi_return_5m_pct")
    index15 = features.get("kospi_return_15m_pct")
    relative3 = features.get("relative_return_3m_pct_point")
    vwap_bp = features.get("stock_vs_session_vwap_bp")

    stock_acceleration = (
        stock3 - stock15 if stock3 is not None and stock15 is not None else None
    )
    index_acceleration = (
        index3 - index15 if index3 is not None and index15 is not None else None
    )
    bullish_transition = (
        stock3 is not None
        and stock3 >= 0.15
        and stock_acceleration is not None
        and stock_acceleration >= 0.35
        and (
            (index_acceleration is not None and index_acceleration >= 0.30)
            or (relative3 is not None and relative3 >= 0.15)
        )
    )
    bearish_transition = (
        stock3 is not None
        and stock3 <= -0.15
        and stock_acceleration is not None
        and stock_acceleration <= -0.35
        and (
            (index_acceleration is not None and index_acceleration <= -0.30)
            or (relative3 is not None and relative3 <= -0.15)
        )
    )
    if bullish_transition:
        return "BULLISH_TRANSITION"
    if bearish_transition:
        return "BEARISH_TRANSITION"

    strong = (
        stock5 is not None
        and stock15 is not None
        and stock5 >= 0.35
        and stock15 >= 0.50
        and vwap_bp is not None
        and vwap_bp >= 10.0
        and (index5 is None or index5 >= 0.10)
    )
    if strong:
        return "STRONG_UPTREND"

    weak_long = (
        stock15 is not None
        and stock15 <= -0.40
        and vwap_bp is not None
        and vwap_bp <= -10.0
        and (index15 is None or index15 <= -0.30)
    )
    weak_early = (
        stock15 is None
        and stock5 is not None
        and stock5 <= -0.40
        and (index5 is None or index5 <= -0.25)
    )
    if weak_long or weak_early:
        return "WEAK_DOWNTREND"
    return "NEUTRAL_TRANSITION"


def classify_causal_regimes(
    stock_bars: Sequence[base.Bar],
    kospi_bars: Sequence[base.Bar],
) -> dict[tuple[str, str, datetime], RegimePoint]:
    """Classify each bar without using a later timestamp or outcome."""
    kospi_by_timestamp = {bar.timestamp: bar for bar in kospi_bars}
    grouped: dict[tuple[date, str, str], list[base.Bar]] = defaultdict(list)
    for bar in stock_bars:
        grouped[(bar.trade_date, bar.venue, bar.session)].append(bar)
    result: dict[tuple[str, str, datetime], RegimePoint] = {}
    for (_, venue, session), raw_series in grouped.items():
        series = sorted(raw_series, key=lambda bar: bar.timestamp)
        stock_by_timestamp = {bar.timestamp: bar for bar in series}
        aligned_index: list[base.Bar | None] = [
            kospi_by_timestamp.get(bar.timestamp) for bar in series
        ]
        prior_raw_state = "NEUTRAL_TRANSITION"
        repeated_count = 0
        for index, bar in enumerate(series):
            index_bar = aligned_index[index]
            stock_returns = {
                window: _window_return(bar, stock_by_timestamp, window)
                for window in (3, 5, 15)
            }
            index_returns: dict[int, float | None] = {}
            for window in (3, 5, 15):
                prior_index = kospi_by_timestamp.get(
                    bar.timestamp - timedelta(minutes=window)
                )
                index_returns[window] = (
                    _pct(float(index_bar.close), float(prior_index.close))
                    if index_bar is not None and prior_index is not None
                    else None
                )
            vwap = _session_vwap(series, index)
            features: dict[str, float | None] = {
                **{
                    f"stock_return_{window}m_pct": stock_returns[window]
                    for window in (3, 5, 15)
                },
                **{
                    f"kospi_return_{window}m_pct": index_returns[window]
                    for window in (3, 5, 15)
                },
                **{
                    f"relative_return_{window}m_pct_point": (
                        stock_returns[window] - index_returns[window]
                        if stock_returns[window] is not None
                        and index_returns[window] is not None
                        else None
                    )
                    for window in (3, 5, 15)
                },
                "stock_vs_session_vwap_bp": (
                    (bar.close / vwap - 1.0) * 10_000.0 if vwap else None
                ),
            }
            raw_state = _raw_regime(features)
            if raw_state == prior_raw_state:
                repeated_count += 1
            else:
                repeated_count = 1
                prior_raw_state = raw_state
            # Trend states need two completed observations. Inflection states are
            # immediate because their definition already compares short and long
            # causal windows; delaying would erase the event being measured.
            if raw_state in {"WEAK_DOWNTREND", "STRONG_UPTREND"} and repeated_count < 2:
                state = "NEUTRAL_TRANSITION"
            else:
                state = raw_state
            context_expected = session in {"KRX_REGULAR", "NXT_REGULAR"}
            source_quality = (
                "samsung_plus_kospi"
                if context_expected and index_bar is not None
                else (
                    "missing_kospi_context"
                    if context_expected
                    else "instrument_only_non_krx_session"
                )
            )
            result[(venue, session, bar.timestamp)] = RegimePoint(
                timestamp=bar.timestamp,
                state=state,
                source_quality=source_quality,
                features=features,
            )
    return result


def load_kospi_bars(
    paths: Sequence[Path],
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[base.Bar], dict[str, Any]]:
    selected: dict[datetime, base.Bar] = {}
    issues: list[str] = []
    for path in paths:
        try:
            handle = path.open("r", encoding="utf-8")
        except OSError:
            issues.append(f"index_file_unreadable:{path}")
            continue
        with handle:
            for line_number, raw_line in enumerate(handle, start=1):
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    issues.append(f"index_json_invalid:{path}:{line_number}")
                    continue
                if (
                    not isinstance(row, dict)
                    or row.get("schema") != "pure_market_index_minute_bar_v1"
                    or row.get("symbol") != "KOSPI"
                ):
                    issues.append(f"index_schema_invalid:{path}:{line_number}")
                    continue
                timestamp = base._parse_source_timestamp(row.get("source_timestamp"))
                open_, high, low, close = (
                    base._positive_int(row.get(key))
                    for key in ("open", "high", "low", "close")
                )
                volume = base._nonnegative_int(row.get("volume"))
                if timestamp is None or not base._valid_ohlcv(
                    open_=open_, high=high, low=low, close=close, volume=volume
                ):
                    issues.append(f"index_row_invalid:{path}:{line_number}")
                    continue
                if start_date is not None and timestamp.date() < start_date:
                    continue
                if end_date is not None and timestamp.date() > end_date:
                    continue
                candidate = base.Bar(
                    symbol="KOSPI",
                    venue="KRX",
                    session="KRX_REGULAR",
                    timestamp=timestamp,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    source="ka20005_backfill",
                )
                existing = selected.get(timestamp)
                if existing is not None and existing != candidate:
                    issues.append(f"index_timestamp_conflict:{timestamp.isoformat()}")
                    selected.pop(timestamp, None)
                    continue
                selected[timestamp] = candidate
    bars = sorted(selected.values(), key=lambda bar: bar.timestamp)
    return bars, {
        "status": "PASS" if bars and not issues else "PARTIAL" if bars else "FAIL",
        "bar_count": len(bars),
        "trading_date_count": len({bar.trade_date for bar in bars}),
        "issue_count": len(issues),
        "issues_sample": issues[:20],
        "source_api_id": "ka20005",
        "price_scale": "raw_index_x100",
    }


def _merge_non_overlapping(trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    last_exit_by_series: dict[tuple[str, str, str], datetime] = {}
    for trade in sorted(
        trades, key=lambda row: (row["entry_at"], row["strategy_mode"])
    ):
        key = (trade["trade_date"], trade["venue"], trade["session"])
        entry_at = datetime.fromisoformat(trade["entry_at"])
        last_exit = last_exit_by_series.get(key)
        if last_exit is not None and entry_at < last_exit:
            continue
        accepted.append(trade)
        last_exit_by_series[key] = datetime.fromisoformat(trade["exit_at"])
    return accepted


def _mode_walk_forward(
    cohort_bars: Sequence[base.Bar],
    regime_map: dict[tuple[str, str, datetime], RegimePoint],
    *,
    mode_name: str,
    policies: Sequence[base.Policy],
    training_days: int,
    min_train_trades: int,
    min_train_dates: int,
    selection_cost_pct: float,
    cost_scenarios_pct: Sequence[float],
    source_quality_passed: bool,
) -> dict[str, Any]:
    mode = MODE_CONTRACT[mode_name]
    regime_states = {
        bar.timestamp: regime_map[(bar.venue, bar.session, bar.timestamp)].state
        for bar in cohort_bars
        if (bar.venue, bar.session, bar.timestamp) in regime_map
    }
    allowed = set(mode["allowed_entry_regimes"])
    exit_regimes = set(mode["exit_regimes"])
    exit_regime_confirmations = int(mode["exit_regime_confirmations"])
    available_dates = sorted({bar.trade_date for bar in cohort_bars})
    evaluations: list[dict[str, Any]] = []
    oos_trades: list[dict[str, Any]] = []
    for date_index, evaluation_date in enumerate(available_dates):
        train_dates = available_dates[max(0, date_index - training_days) : date_index]
        if len(train_dates) < training_days:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "insufficient_prior_trading_days",
                }
            )
            continue
        train_bars = [bar for bar in cohort_bars if bar.trade_date in train_dates]
        selected: tuple[tuple[float, float, float, float], base.Policy] | None = None
        for policy in policies:
            trades = base.simulate_policy(
                train_bars,
                policy,
                cost_pct=selection_cost_pct,
                regime_by_timestamp=regime_states,
                allowed_entry_regimes=allowed,
                exit_regimes=exit_regimes,
                exit_regime_confirmations=exit_regime_confirmations,
                strategy_mode=str(mode["strategy_mode"]),
            )
            rank = base._policy_rank(
                trades,
                min_train_trades=min_train_trades,
                min_train_dates=min_train_dates,
            )
            if rank is not None and (selected is None or rank > selected[0]):
                selected = (rank, policy)
        if selected is None:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "no_policy_met_training_floor",
                    "training_dates": [item.isoformat() for item in train_dates],
                }
            )
            continue
        rank, selected_policy = selected
        evaluation_bars = [
            bar for bar in cohort_bars if bar.trade_date == evaluation_date
        ]
        trades = base.simulate_policy(
            evaluation_bars,
            selected_policy,
            cost_pct=selection_cost_pct,
            regime_by_timestamp=regime_states,
            allowed_entry_regimes=allowed,
            exit_regimes=exit_regimes,
            exit_regime_confirmations=exit_regime_confirmations,
            strategy_mode=str(mode["strategy_mode"]),
        )
        oos_trades.extend(trades)
        evaluations.append(
            {
                "evaluation_date": evaluation_date.isoformat(),
                "status": "evaluated_out_of_sample",
                "training_dates": [item.isoformat() for item in train_dates],
                "selected_policy": asdict(selected_policy),
                "selected_policy_id": selected_policy.policy_id,
                "training_rank": {
                    "source_quality_adjusted_ev_pct": round(rank[0], 6),
                    "simple_sum_profit_pct": round(rank[1], 6),
                },
                "trades": trades,
            }
        )
    summary = base._trade_summary(
        oos_trades,
        cost_scenarios_pct=cost_scenarios_pct,
        source_quality_passed=source_quality_passed,
    )
    return {
        "mode": mode_name,
        "mode_contract": mode,
        "evaluation_count": sum(
            row["status"] == "evaluated_out_of_sample" for row in evaluations
        ),
        "out_of_sample_summary": summary,
        "trades": oos_trades,
        "evaluations": evaluations,
    }


def build_regime_walk_forward_report(
    stock_bars: Sequence[base.Bar],
    kospi_bars: Sequence[base.Bar],
    *,
    stock_source_quality: dict[str, Any],
    kospi_source_quality: dict[str, Any],
    policies: Sequence[base.Policy] | None = None,
    training_days: int = 20,
    min_train_trades: int = 8,
    min_train_dates: int = 5,
    selection_cost_pct: float = 0.20,
    cost_scenarios_pct: Sequence[float] = base.DEFAULT_COST_SCENARIOS_PCT,
) -> dict[str, Any]:
    policy_grids = (
        {mode_name: list(policies) for mode_name in MODE_CONTRACT}
        if policies is not None
        else default_mode_policy_grids()
    )
    cost_scenarios_pct = tuple(
        sorted({float(value) for value in cost_scenarios_pct} | {selection_cost_pct})
    )
    stock_coverage = base.assess_date_coverage(stock_bars)
    qualified_stock = base.filter_coverage_qualified_bars(stock_bars, stock_coverage)
    regime_map = classify_causal_regimes(qualified_stock, kospi_bars)
    cohorts: dict[str, Any] = {}
    for cohort in base.COHORTS:
        cohort_bars = [bar for bar in qualified_stock if bar.venue == cohort]
        available_dates = sorted({bar.trade_date for bar in cohort_bars})
        cohort_bar_points = [
            (bar, regime_map[(bar.venue, bar.session, bar.timestamp)])
            for bar in cohort_bars
            if (bar.venue, bar.session, bar.timestamp) in regime_map
        ]
        expected_context_points = [
            point for bar, point in cohort_bar_points if bar.session == "KRX_REGULAR"
        ]
        context_passed = (
            cohort == "KRX"
            and kospi_source_quality.get("status") == "PASS"
            and expected_context_points
            and all(
                point.source_quality == "samsung_plus_kospi"
                for point in expected_context_points
            )
        )
        stock_passed = (
            stock_source_quality.get("venue_status", {}).get(cohort)
            or stock_source_quality.get("status")
        ) == "PASS"
        source_quality_passed = bool(stock_passed and context_passed)
        mode_reports = {
            mode_name: _mode_walk_forward(
                cohort_bars,
                regime_map,
                mode_name=mode_name,
                policies=policy_grids[mode_name],
                training_days=training_days,
                min_train_trades=min_train_trades,
                min_train_dates=min_train_dates,
                selection_cost_pct=selection_cost_pct,
                cost_scenarios_pct=cost_scenarios_pct,
                source_quality_passed=source_quality_passed,
            )
            for mode_name in MODE_CONTRACT
        }
        combined_trades = _merge_non_overlapping(
            [
                trade
                for mode_report in mode_reports.values()
                for trade in mode_report["trades"]
            ]
        )
        evaluated_dates = {
            date.fromisoformat(row["evaluation_date"])
            for mode_report in mode_reports.values()
            for row in mode_report["evaluations"]
            if row["status"] == "evaluated_out_of_sample"
        }
        opportunity_bars = [
            bar for bar in cohort_bars if bar.trade_date in evaluated_dates
        ]
        opportunities = base.label_reversal_opportunities(opportunity_bars)
        sample_floor_passed = base.has_research_sample_floor(available_dates)
        cohorts[cohort] = {
            "available_trading_dates": [item.isoformat() for item in available_dates],
            "bar_count": len(cohort_bars),
            "source_quality": ("PASS" if source_quality_passed else "PARTIAL_CONTEXT"),
            "sample_floor_passed": sample_floor_passed,
            "decision": (
                "research_sample_floor_passed"
                if sample_floor_passed and source_quality_passed and combined_trades
                else "insufficient_for_strategy_or_runtime_judgment"
            ),
            "regime_counts": dict(
                sorted(Counter(point.state for _, point in cohort_bar_points).items())
            ),
            "regime_source_quality_counts": dict(
                sorted(
                    Counter(
                        point.source_quality for _, point in cohort_bar_points
                    ).items()
                )
            ),
            "modes": mode_reports,
            "controller_out_of_sample_summary": base._trade_summary(
                combined_trades,
                cost_scenarios_pct=cost_scenarios_pct,
                source_quality_passed=source_quality_passed,
            ),
            "controller_trades": combined_trades,
            "opportunity_capture": base.summarize_opportunity_capture(
                opportunities, combined_trades
            ),
        }
    available_dates = sorted({bar.trade_date for bar in qualified_stock})
    return {
        "schema": "pure_market_regime_replay_v1",
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "objective": (
            "causally route weak-market capitulation and bullish-transition trend "
            "entries instead of applying one inverted or normal signal rule"
        ),
        "symbol": base.SAMSUNG_CODE,
        "data_start_date": available_dates[0].isoformat() if available_dates else None,
        "data_end_date": available_dates[-1].isoformat() if available_dates else None,
        "trading_date_count": len(available_dates),
        "training_days": training_days,
        "min_train_trades": min_train_trades,
        "min_train_dates": min_train_dates,
        "selection_cost_pct": selection_cost_pct,
        "policy_count_by_mode": {
            mode_name: len(mode_policies)
            for mode_name, mode_policies in policy_grids.items()
        },
        "mode_contract": MODE_CONTRACT,
        "regime_contract": REGIME_CONTRACT,
        "stock_source_quality": stock_source_quality,
        "kospi_source_quality": kospi_source_quality,
        "stock_coverage": stock_coverage,
        "cohorts": cohorts,
        "decision": (
            "krx_research_sample_floor_passed_nxt_context_limited"
            if cohorts["KRX"]["decision"] == "research_sample_floor_passed"
            else "insufficient_for_strategy_or_runtime_judgment"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    cost = float(report["selection_cost_pct"])
    cost_key = f"cost_{cost:.2f}pct".replace(".", "p")
    lines = [
        f"# Pure-market regime replay — {report['data_start_date']} to {report['data_end_date']}",
        "",
        "## Decision",
        "",
        f"- decision: `{report['decision']}`",
        f"- qualified trading dates: `{report['trading_date_count']}` / required `{base.MIN_QUALIFIED_TRADING_DAYS}`",
        f"- round-trip selection cost: `{cost:.2f}%`",
        "- runtime_effect: `false`",
        "",
        "## Regime-conditioned out-of-sample result",
        "",
        "| Venue | Mode | Trades | Gross EV | Net EV @ cost | Source-quality adjusted EV | Gross win rate | Source quality |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cohort in base.COHORTS:
        cohort_row = report["cohorts"][cohort]
        for mode_name in MODE_CONTRACT:
            summary = cohort_row["modes"][mode_name]["out_of_sample_summary"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        cohort,
                        mode_name,
                        str(summary["sample_count"]),
                        str(
                            summary.get("gross", {}).get("equal_weight_avg_profit_pct")
                        ),
                        str(
                            summary.get("net_by_cost", {})
                            .get(cost_key, {})
                            .get("equal_weight_avg_profit_pct")
                        ),
                        str(summary.get("source_quality_adjusted_ev_pct")),
                        str(summary.get("gross_diagnostic_win_rate_pct")),
                        cohort_row["source_quality"],
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Combined controller and opportunity capture",
            "",
            "| Venue | Trades | Gross EV | Net EV @ cost | Opportunity capture | Exit vs rebound peak | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for cohort in base.COHORTS:
        cohort_row = report["cohorts"][cohort]
        summary = cohort_row["controller_out_of_sample_summary"]
        capture = cohort_row["opportunity_capture"]
        lines.append(
            "| "
            + " | ".join(
                [
                    cohort,
                    str(summary["sample_count"]),
                    str(summary.get("gross", {}).get("equal_weight_avg_profit_pct")),
                    str(
                        summary.get("net_by_cost", {})
                        .get(cost_key, {})
                        .get("equal_weight_avg_profit_pct")
                    ),
                    str(capture.get("diagnostic_opportunity_capture_rate_pct")),
                    str(capture.get("avg_exit_price_vs_forward_rebound_peak_pct")),
                    str(cohort_row["decision"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The regime split is structurally valid only as an offline causal experiment. Negative KRX cost-adjusted EV or a source-quality/sample-floor failure blocks strategy promotion even when an individual episode is favorable.",
            "",
            "## Boundary",
            "",
            "Regimes use completed timestamp-exact 3/5/15-minute Samsung and aligned KOSPI bars plus session VWAP. Bullish and bearish transition labels compare short and long windows available at that timestamp; future bars never assign a regime. NXT premarket/aftermarket are explicitly instrument-only, while NXT regular may use timestamp-aligned KOSPI context.",
            "",
        ]
    )
    return "\n".join(lines)


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


def write_report(
    report: dict[str, Any], *, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"pure_market_regime_replay_{report['data_start_date']}_{report['data_end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--market-dir", type=Path, default=base.DEFAULT_MARKET_DIR)
    parser.add_argument("--training-days", type=int, default=20)
    parser.add_argument("--min-train-trades", type=int, default=8)
    parser.add_argument("--min-train-dates", type=int, default=5)
    parser.add_argument("--selection-cost-pct", type=float, default=0.20)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    if start_date < base.CLEAN_TUNING_BASELINE_DATE:
        raise SystemExit("start-date precedes clean tuning baseline 2026-06-05")
    stock_paths = sorted(args.market_dir.glob("samsung_1m_*.jsonl"))
    kospi_paths = sorted(args.market_dir.glob("kospi_1m_*.jsonl"))
    stock_bars, stock_quality = base.load_market_bars(
        market_paths=stock_paths,
        widget_observation_dir=None,
        start_date=start_date,
        end_date=end_date,
    )
    kospi_bars, kospi_quality = load_kospi_bars(
        kospi_paths,
        start_date=start_date,
        end_date=end_date,
    )
    if not stock_bars or not kospi_bars:
        raise SystemExit("complete Samsung and KOSPI market backfills are required")
    report = build_regime_walk_forward_report(
        stock_bars,
        kospi_bars,
        stock_source_quality=stock_quality,
        kospi_source_quality=kospi_quality,
        training_days=max(1, args.training_days),
        min_train_trades=max(1, args.min_train_trades),
        min_train_dates=max(1, args.min_train_dates),
        selection_cost_pct=max(0.0, args.selection_cost_pct),
    )
    if args.write:
        json_path, markdown_path = write_report(report, output_dir=args.output_dir)
        print(
            json.dumps(
                {
                    "status": "complete",
                    "json_path": str(json_path),
                    "markdown_path": str(markdown_path),
                    "decision": report["decision"],
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
