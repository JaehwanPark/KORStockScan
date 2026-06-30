"""Holding/exit observation report for Plan Rebase tuning decisions."""

from __future__ import annotations

import gzip
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitor_snapshot_runtime import guard_stdin_heavy_build
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import existing_or_gzip_path


SCHEMA_VERSION = 1
POST_FALLBACK_CUTOFF = datetime(2026, 4, 21, 9, 45)
TARGET_EXIT_RULES = (
    "scalp_trailing_take_profit",
    "scalp_soft_stop_pct",
    "scalp_preset_hard_stop_pct",
    "scalp_hard_stop_pct",
    "EOD/NXT",
)


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int = 0) -> int:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _ratio(numerator: int, denominator: int) -> float:
    return round((float(numerator) / float(denominator)) * 100.0, 1) if denominator > 0 else 0.0


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    return round(sum(clean) / len(clean), 3) if clean else 0.0


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "None"):
        return None
    raw = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def _date_range(month_start: str, target_date: str) -> list[str]:
    start = datetime.strptime(month_start, "%Y-%m-%d").date()
    end = datetime.strptime(target_date, "%Y-%m-%d").date()
    if end < start:
        return []
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def _read_json(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict]:
    path = existing_or_gzip_path(path)
    if not path.exists():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    rows: list[dict] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _monitor_snapshot_path(snapshot_kind: str, target_date: str) -> Path | None:
    snapshot_dir = DATA_DIR / "report" / "monitor_snapshots"
    safe_kind = str(snapshot_kind or "").strip().lower().replace("-", "_")
    for suffix in (".json", ".json.gz"):
        candidate = snapshot_dir / f"{safe_kind}_{target_date}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _load_saved_snapshot(snapshot_kind: str, target_date: str) -> dict | None:
    path = _monitor_snapshot_path(snapshot_kind, target_date)
    if path is None:
        return None
    try:
        return _read_json(path)
    except Exception:
        return None


def _load_saved_snapshots(snapshot_kind: str, dates: list[str]) -> tuple[list[dict], list[str]]:
    snapshots: list[dict] = []
    paths: list[str] = []
    for target_date in dates:
        path = _monitor_snapshot_path(snapshot_kind, target_date)
        if path is None:
            continue
        try:
            snapshots.append(_read_json(path))
            paths.append(str(path))
        except Exception:
            continue
    return snapshots, paths


def _trade_rows_from_snapshots(snapshots: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for snapshot in snapshots:
        for row in ((snapshot.get("sections") or {}).get("recent_trades") or []):
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _is_valid_completed_trade(row: dict) -> bool:
    if str(row.get("status") or "").upper() != "COMPLETED":
        return False
    return _safe_float(row.get("profit_rate"), None) is not None


def _entry_mode(row: dict) -> str:
    return str(row.get("entry_mode") or "").strip().lower()


def _trade_id(row: dict) -> str:
    return str(row.get("id") or row.get("recommendation_id") or "").strip()


def _is_post_fallback(row: dict) -> bool:
    buy_dt = _parse_dt(row.get("buy_time"))
    return bool(buy_dt and buy_dt >= POST_FALLBACK_CUTOFF)


def _exit_rule_from_trade(row: dict) -> str:
    exit_signal = row.get("exit_signal")
    if isinstance(exit_signal, dict):
        for key in ("exit_rule", "rule", "reason"):
            value = str(exit_signal.get(key) or "").strip()
            if value:
                return value
    for event in row.get("timeline") or []:
        if not isinstance(event, dict) or event.get("stage") != "exit_signal":
            continue
        fields = event.get("fields") or {}
        for key in ("exit_rule", "rule", "reason", "exit_reason"):
            value = str(fields.get(key) or "").strip()
            if value:
                return value
    return "-"


def _exit_group(exit_rule: str) -> str:
    normalized = str(exit_rule or "-").strip()
    lowered = normalized.lower()
    if any(token in lowered for token in ("eod", "nxt", "overnight", "preclose")):
        return "EOD/NXT"
    return normalized or "-"


def _fill_quality(row: dict) -> str:
    qualities: list[str] = []
    for event in row.get("timeline") or []:
        if not isinstance(event, dict):
            continue
        fields = event.get("fields") or {}
        value = str(fields.get("fill_quality") or "").strip().upper()
        if value:
            qualities.append(value)
    if any("PARTIAL" in quality for quality in qualities):
        return "partial_fill"
    if any("FULL" in quality for quality in qualities):
        return "full_fill"
    return "unknown_fill"


def _is_pyramid_activated(row: dict) -> bool:
    base_qty = _safe_int(row.get("buy_qty"), 0)
    for event in row.get("timeline") or []:
        if not isinstance(event, dict):
            continue
        if str(event.get("stage") or "") == "scale_in_executed":
            return True
        fields = event.get("fields") or {}
        if _safe_int(fields.get("add_count"), 0) > 0:
            return True
        if base_qty > 0 and _safe_int(fields.get("new_buy_qty"), 0) > base_qty:
            return True
    return False


def _summarize_completed_trades(rows: list[dict]) -> dict:
    valid_rows = [row for row in rows if _is_valid_completed_trade(row)]
    profits = [float(_safe_float(row.get("profit_rate"), 0.0) or 0.0) for row in valid_rows]
    exit_rules = Counter(_exit_group(_exit_rule_from_trade(row)) for row in valid_rows)
    return {
        "trade_count": len(valid_rows),
        "win_trades": sum(1 for value in profits if value > 0),
        "loss_trades": sum(1 for value in profits if value <= 0),
        "avg_profit_rate": _avg(profits),
        "realized_pnl_krw": int(sum(_safe_int(row.get("realized_pnl_krw"), 0) for row in valid_rows)),
        "exit_rules": [{"label": key, "count": value} for key, value in exit_rules.most_common()],
    }


def _build_cohorts(valid_trades: list[dict]) -> dict:
    return {
        "normal_only": _summarize_completed_trades([row for row in valid_trades if _entry_mode(row) == "normal"]),
        "post_fallback_deprecation": _summarize_completed_trades([row for row in valid_trades if _is_post_fallback(row)]),
        "post_fallback_normal_only": _summarize_completed_trades(
            [row for row in valid_trades if _is_post_fallback(row) and _entry_mode(row) == "normal"]
        ),
        "full_fill": _summarize_completed_trades([row for row in valid_trades if _fill_quality(row) == "full_fill"]),
        "partial_fill": _summarize_completed_trades([row for row in valid_trades if _fill_quality(row) == "partial_fill"]),
        "initial-only": _summarize_completed_trades([row for row in valid_trades if not _is_pyramid_activated(row)]),
        "pyramid-activated": _summarize_completed_trades([row for row in valid_trades if _is_pyramid_activated(row)]),
    }


def _post_sell_candidate_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_candidates_{target_date}.jsonl"


def _post_sell_evaluation_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl"


def _load_post_sell_rows(dates: list[str]) -> tuple[list[dict], list[str]]:
    candidates_by_id: dict[str, dict] = {}
    evaluations: list[dict] = []
    paths: list[str] = []
    for target_date in dates:
        candidate_path = _post_sell_candidate_path(target_date)
        evaluation_path = _post_sell_evaluation_path(target_date)
        candidate_actual_path = existing_or_gzip_path(candidate_path)
        evaluation_actual_path = existing_or_gzip_path(evaluation_path)
        if candidate_actual_path.exists():
            paths.append(str(candidate_actual_path))
        if evaluation_actual_path.exists():
            paths.append(str(evaluation_actual_path))
        for candidate in _read_jsonl(candidate_path):
            post_sell_id = str(candidate.get("post_sell_id") or "")
            if post_sell_id:
                candidates_by_id[post_sell_id] = candidate
        evaluations.extend(_read_jsonl(evaluation_path))

    rows: list[dict] = []
    for evaluation in evaluations:
        post_sell_id = str(evaluation.get("post_sell_id") or "")
        candidate = candidates_by_id.get(post_sell_id, {})
        rows.append(_enrich_post_sell_row(candidate=candidate, evaluation=evaluation))
    return rows, paths


def _metric_window(row: dict, window: str) -> dict:
    metrics = row.get(window) or {}
    return metrics if isinstance(metrics, dict) else {}


def _metric_float(row: dict, window: str, key: str) -> float:
    return float(_safe_float(_metric_window(row, window).get(key), 0.0) or 0.0)


def _recovery_to_buy_threshold_pct(row: dict) -> float:
    buy_price = float(_safe_float(row.get("buy_price"), 0.0) or 0.0)
    sell_price = float(_safe_float(row.get("sell_price"), 0.0) or 0.0)
    if buy_price <= 0 or sell_price <= 0:
        return 0.0
    return round(((buy_price / sell_price) - 1.0) * 100.0, 3)


def _rebound_above_sell(row: dict, window: str) -> bool:
    metrics = _metric_window(row, window)
    if "rebound_above_sell" in metrics:
        return bool(metrics.get("rebound_above_sell"))
    return _metric_float(row, window, "mfe_pct") > 0.0


def _rebound_above_buy(row: dict, window: str) -> bool:
    metrics = _metric_window(row, window)
    if "rebound_above_buy" in metrics:
        return bool(metrics.get("rebound_above_buy"))
    return _metric_float(row, window, "mfe_pct") >= _recovery_to_buy_threshold_pct(row)


def _enrich_post_sell_row(*, candidate: dict, evaluation: dict) -> dict:
    merged = {**(candidate or {}), **(evaluation or {})}
    metrics_10m = _metric_window(merged, "metrics_10m")
    metrics_1m = _metric_window(merged, "metrics_1m")
    metrics_3m = _metric_window(merged, "metrics_3m")
    metrics_5m = _metric_window(merged, "metrics_5m")
    metrics_20m = _metric_window(merged, "metrics_20m")
    profit_rate = float(_safe_float(merged.get("profit_rate"), 0.0) or 0.0)
    sell_price = float(_safe_float(merged.get("sell_price"), 0.0) or 0.0)
    buy_qty = _safe_int(merged.get("buy_qty"), 0)
    extra_upside_pct = max(0.0, float(_safe_float(metrics_10m.get("mfe_pct"), 0.0) or 0.0))
    potential_peak_profit_rate = round(profit_rate + extra_upside_pct, 3)
    capture_efficiency_pct = (
        round(max(0.0, min(100.0, (profit_rate / potential_peak_profit_rate) * 100.0)), 1)
        if potential_peak_profit_rate > 0
        else 0.0
    )
    return {
        **merged,
        "post_sell_id": str(merged.get("post_sell_id") or ""),
        "recommendation_id": _safe_int(merged.get("recommendation_id"), 0),
        "signal_date": str(merged.get("signal_date") or ""),
        "stock_code": str(merged.get("stock_code") or ""),
        "stock_name": str(merged.get("stock_name") or ""),
        "strategy": str(merged.get("strategy") or ""),
        "position_tag": str(merged.get("position_tag") or ""),
        "exit_rule": str(merged.get("exit_rule") or "-"),
        "outcome": str(merged.get("outcome") or "NEUTRAL").upper(),
        "profit_rate": round(profit_rate, 3),
        "buy_price": _safe_int(merged.get("buy_price"), 0),
        "sell_price": _safe_int(merged.get("sell_price"), 0),
        "buy_qty": buy_qty,
        "peak_profit": round(float(_safe_float(merged.get("peak_profit"), 0.0) or 0.0), 3),
        "held_sec": _safe_int(merged.get("held_sec"), 0),
        "extra_upside_10m_pct": round(extra_upside_pct, 3),
        "extra_upside_10m_krw_est": int(round(sell_price * buy_qty * (extra_upside_pct / 100.0)))
        if sell_price > 0 and buy_qty > 0
        else 0,
        "potential_peak_profit_rate_10m": float(potential_peak_profit_rate),
        "capture_efficiency_pct": float(capture_efficiency_pct),
        "recovery_to_buy_threshold_pct": _recovery_to_buy_threshold_pct(merged),
        "rebound_above_sell_1m": _rebound_above_sell(merged, "metrics_1m"),
        "rebound_above_sell_3m": _rebound_above_sell(merged, "metrics_3m"),
        "rebound_above_sell_5m": _rebound_above_sell(merged, "metrics_5m"),
        "rebound_above_sell_10m": _rebound_above_sell(merged, "metrics_10m"),
        "rebound_above_sell_20m": _rebound_above_sell(merged, "metrics_20m"),
        "rebound_above_buy_1m": _rebound_above_buy(merged, "metrics_1m"),
        "rebound_above_buy_3m": _rebound_above_buy(merged, "metrics_3m"),
        "rebound_above_buy_5m": _rebound_above_buy(merged, "metrics_5m"),
        "rebound_above_buy_10m": _rebound_above_buy(merged, "metrics_10m"),
        "rebound_above_buy_20m": _rebound_above_buy(merged, "metrics_20m"),
        "mfe_1m_pct": round(float(_safe_float(metrics_1m.get("mfe_pct"), 0.0) or 0.0), 3),
        "mfe_3m_pct": round(float(_safe_float(metrics_3m.get("mfe_pct"), 0.0) or 0.0), 3),
        "mfe_5m_pct": round(float(_safe_float(metrics_5m.get("mfe_pct"), 0.0) or 0.0), 3),
        "mfe_10m_pct": round(float(_safe_float(metrics_10m.get("mfe_pct"), 0.0) or 0.0), 3),
        "mfe_20m_pct": round(float(_safe_float(metrics_20m.get("mfe_pct"), 0.0) or 0.0), 3),
        "close_ret_1m_pct": round(float(_safe_float(metrics_1m.get("close_ret_pct"), 0.0) or 0.0), 3),
        "close_ret_3m_pct": round(float(_safe_float(metrics_3m.get("close_ret_pct"), 0.0) or 0.0), 3),
        "close_ret_5m_pct": round(float(_safe_float(metrics_5m.get("close_ret_pct"), 0.0) or 0.0), 3),
        "close_ret_10m_pct": round(float(_safe_float(metrics_10m.get("close_ret_pct"), 0.0) or 0.0), 3),
        "close_ret_20m_pct": round(float(_safe_float(metrics_20m.get("close_ret_pct"), 0.0) or 0.0), 3),
        "hit_up_05_1m": bool(metrics_1m.get("hit_up_05", False)),
        "hit_up_05_3m": bool(metrics_3m.get("hit_up_05", False)),
        "hit_up_05_5m": bool(metrics_5m.get("hit_up_05", False)),
        "hit_up_05_10m": bool(metrics_10m.get("hit_up_05", False)),
        "hit_up_05_20m": bool(metrics_20m.get("hit_up_05", False)),
        "hit_up_10_1m": bool(metrics_1m.get("hit_up_10", False)),
        "hit_up_10_3m": bool(metrics_3m.get("hit_up_10", False)),
        "hit_up_10_5m": bool(metrics_5m.get("hit_up_10", False)),
        "hit_up_10_10m": bool(metrics_10m.get("hit_up_10", False)),
        "hit_up_10_20m": bool(metrics_20m.get("hit_up_10", False)),
        "same_symbol_soft_stop_cooldown_would_block": bool(
            merged.get("same_symbol_soft_stop_cooldown_would_block", False)
        ),
    }


def _summarize_exit_rule_quality(post_sell_rows: list[dict], valid_trades: list[dict]) -> list[dict]:
    post_sell_by_rule: dict[str, list[dict]] = defaultdict(list)
    for row in post_sell_rows:
        post_sell_by_rule[_exit_group(str(row.get("exit_rule") or "-"))].append(row)

    trades_by_rule: dict[str, list[dict]] = defaultdict(list)
    for row in valid_trades:
        trades_by_rule[_exit_group(_exit_rule_from_trade(row))].append(row)

    rows: list[dict] = []
    for exit_rule in TARGET_EXIT_RULES:
        quality_rows = post_sell_by_rule.get(exit_rule, [])
        completed_rows = trades_by_rule.get(exit_rule, [])
        outcomes = Counter(str(row.get("outcome") or "NEUTRAL").upper() for row in quality_rows)
        evaluated = len(quality_rows)
        completed_profits = [
            float(_safe_float(row.get("profit_rate"), 0.0) or 0.0)
            for row in completed_rows
            if _is_valid_completed_trade(row)
        ]
        capture_values = [
            float(_safe_float(row.get("capture_efficiency_pct"), 0.0) or 0.0)
            for row in quality_rows
            if float(_safe_float(row.get("potential_peak_profit_rate_10m"), 0.0) or 0.0) > 0
        ]
        rows.append(
            {
                "exit_rule": exit_rule,
                "evaluated_post_sell": evaluated,
                "outcome_counts": {
                    "MISSED_UPSIDE": int(outcomes.get("MISSED_UPSIDE", 0)),
                    "GOOD_EXIT": int(outcomes.get("GOOD_EXIT", 0)),
                    "NEUTRAL": int(outcomes.get("NEUTRAL", 0)),
                },
                "missed_upside_rate": _ratio(outcomes.get("MISSED_UPSIDE", 0), evaluated),
                "good_exit_rate": _ratio(outcomes.get("GOOD_EXIT", 0), evaluated),
                "capture_efficiency_avg_pct": _avg(capture_values),
                "avg_extra_upside_10m_pct": _avg(
                    [float(_safe_float(row.get("extra_upside_10m_pct"), 0.0) or 0.0) for row in quality_rows]
                ),
                "completed_valid_trades": len(completed_profits),
                "completed_valid_avg_profit_rate": _avg(completed_profits),
                "completed_valid_realized_pnl_krw": int(
                    sum(_safe_int(row.get("realized_pnl_krw"), 0) for row in completed_rows)
                ),
            }
        )
    return rows


def _build_trade_lookup(valid_trades: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for row in valid_trades:
        trade_id = _trade_id(row)
        if trade_id:
            lookup[trade_id] = row
    return lookup


def _build_trailing_continuation(
    *,
    post_sell_rows: list[dict],
    valid_trades: list[dict],
    fallback_regression_count: int,
) -> dict:
    trade_lookup = _build_trade_lookup(valid_trades)
    trailing_rows = [row for row in post_sell_rows if _exit_group(str(row.get("exit_rule") or "-")) == "scalp_trailing_take_profit"]
    qualifying_rows: list[dict] = []
    for row in trailing_rows:
        trade = trade_lookup.get(str(row.get("recommendation_id") or ""))
        if not trade:
            continue
        if (
            _entry_mode(trade) == "normal"
            and _is_post_fallback(trade)
            and _fill_quality(trade) == "full_fill"
            and not _is_pyramid_activated(trade)
            and float(_safe_float(row.get("profit_rate"), 0.0) or 0.0) > 0
        ):
            qualifying_rows.append(row)

    outcomes = Counter(str(row.get("outcome") or "NEUTRAL").upper() for row in trailing_rows)
    evaluated = len(trailing_rows)
    missed_rate = _ratio(outcomes.get("MISSED_UPSIDE", 0), evaluated)
    good_rate = _ratio(outcomes.get("GOOD_EXIT", 0), evaluated)
    eligible = (
        evaluated >= 5
        and missed_rate >= 60.0
        and good_rate <= 30.0
        and fallback_regression_count == 0
        and len(qualifying_rows) > 0
    )
    return {
        "candidate_id": "trailing_continuation_micro_canary",
        "priority": 2,
        "priority_basis": "upside capture 개선 후보이나 soft_stop realized loss 축보다 손익 훼손 우선순위가 낮다.",
        "evaluated_trailing": evaluated,
        "qualifying_cohort_count": len(qualifying_rows),
        "outcome_counts": {
            "MISSED_UPSIDE": int(outcomes.get("MISSED_UPSIDE", 0)),
            "GOOD_EXIT": int(outcomes.get("GOOD_EXIT", 0)),
            "NEUTRAL": int(outcomes.get("NEUTRAL", 0)),
        },
        "missed_upside_rate": missed_rate,
        "good_exit_rate": good_rate,
        "fallback_regression_count": int(fallback_regression_count),
        "eligible_for_live_review": eligible,
        "single_control_point": "SCALP_TRAILING_LIMIT_WEAK qualifying cohort +0.2%p only",
        "scope": "normal_only + post_fallback_deprecation + full_fill + initial-only + scalp_trailing_take_profit + profit_rate>0",
        "excluded_scopes": ["partial_fill", "pyramid-activated", "soft_stop", "EOD/NXT", "fallback"],
        "rollback_guards": [
            "Plan Rebase §6 common guards",
            "trailing canary cohort avg_profit_rate <= 0",
            "soft_stop transition rate baseline +5.0%p",
            "GOOD_EXIT rate additional deterioration +15.0%p",
        ],
    }


def _build_rebound_windows(rows: list[dict]) -> list[dict]:
    windows: list[dict] = []
    for label in ("1m", "3m", "5m", "10m", "20m"):
        window_total = sum(1 for row in rows if f"mfe_{label}_pct" in row)
        if window_total <= 0:
            continue
        mfe_values = [float(_safe_float(row.get(f"mfe_{label}_pct"), 0.0) or 0.0) for row in rows]
        close_values = [float(_safe_float(row.get(f"close_ret_{label}_pct"), 0.0) or 0.0) for row in rows]
        above_sell = sum(1 for row in rows if bool(row.get(f"rebound_above_sell_{label}")))
        above_buy = sum(1 for row in rows if bool(row.get(f"rebound_above_buy_{label}")))
        hit_up_05 = sum(1 for row in rows if bool(row.get(f"hit_up_05_{label}")))
        hit_up_10 = sum(1 for row in rows if bool(row.get(f"hit_up_10_{label}")))
        windows.append(
            {
                "window": label,
                "total": int(window_total),
                "rebound_above_sell_count": int(above_sell),
                "rebound_above_sell_rate": _ratio(above_sell, window_total),
                "rebound_above_buy_count": int(above_buy),
                "rebound_above_buy_rate": _ratio(above_buy, window_total),
                "hit_up_05_count": int(hit_up_05),
                "hit_up_05_rate": _ratio(hit_up_05, window_total),
                "hit_up_10_count": int(hit_up_10),
                "hit_up_10_rate": _ratio(hit_up_10, window_total),
                "mfe_ge_0_5_count": sum(1 for value in mfe_values if value >= 0.5),
                "mfe_ge_0_5_rate": _ratio(sum(1 for value in mfe_values if value >= 0.5), window_total),
                "mfe_ge_1_0_count": sum(1 for value in mfe_values if value >= 1.0),
                "mfe_ge_1_0_rate": _ratio(sum(1 for value in mfe_values if value >= 1.0), window_total),
                "avg_mfe_pct": _avg(mfe_values),
                "avg_close_ret_pct": _avg(close_values),
            }
        )
    return windows


def _build_hard_stop_auxiliary(post_sell_rows: list[dict], valid_trades: list[dict]) -> dict:
    hard_rules = {"scalp_preset_hard_stop_pct", "scalp_hard_stop_pct"}
    rows = [row for row in post_sell_rows if _exit_group(str(row.get("exit_rule") or "-")) in hard_rules]
    completed_rows = [
        row
        for row in valid_trades
        if _exit_group(_exit_rule_from_trade(row)) in hard_rules and _is_valid_completed_trade(row)
    ]
    outcomes = Counter(str(row.get("outcome") or "NEUTRAL").upper() for row in rows)
    by_rule = Counter(_exit_group(str(row.get("exit_rule") or "-")) for row in rows)
    completed_profits = [float(_safe_float(row.get("profit_rate"), 0.0) or 0.0) for row in completed_rows]
    return {
        "candidate_id": "hard_stop_whipsaw_aux",
        "priority": "parking_auxiliary",
        "basis": "하드스탑은 극단 손실 방어선이므로 표본이 작거나 반등이 보여도 soft_stop보다 먼저 완화하지 않는다.",
        "evaluated_post_sell": len(rows),
        "exit_rule_counts": [{"label": key, "count": value} for key, value in by_rule.most_common()],
        "outcome_counts": {
            "MISSED_UPSIDE": int(outcomes.get("MISSED_UPSIDE", 0)),
            "GOOD_EXIT": int(outcomes.get("GOOD_EXIT", 0)),
            "NEUTRAL": int(outcomes.get("NEUTRAL", 0)),
        },
        "rebound_windows": _build_rebound_windows(rows),
        "completed_valid_trades": len(completed_rows),
        "completed_valid_avg_profit_rate": _avg(completed_profits),
        "completed_valid_realized_pnl_krw": int(
            sum(_safe_int(row.get("realized_pnl_krw"), 0) for row in completed_rows)
        ),
        "live_priority": "soft_stop 이후 보조 관찰. hard stop 완화 canary는 severe-loss guard 훼손 리스크 때문에 금지.",
    }


def _build_soft_stop_rebound(
    post_sell_rows: list[dict],
    same_symbol_reentry: dict,
    valid_trades: list[dict],
) -> dict:
    rows = [row for row in post_sell_rows if _exit_group(str(row.get("exit_rule") or "-")) == "scalp_soft_stop_pct"]
    total = len(rows)
    rebound_sell_rate = _ratio(sum(1 for row in rows if bool(row.get("rebound_above_sell_10m"))), total)
    rebound_buy_rate = _ratio(sum(1 for row in rows if bool(row.get("rebound_above_buy_10m"))), total)
    cooldown_rate = _ratio(
        sum(1 for row in rows if bool(row.get("same_symbol_soft_stop_cooldown_would_block"))),
        total,
    )
    soft_reentry_losses = int(same_symbol_reentry.get("after_soft_stop_next_loss_count", 0) or 0)
    whipsaw_windows = _build_rebound_windows(rows)
    whipsaw_10m = next((row for row in whipsaw_windows if row["window"] == "10m"), {})
    whipsaw_signal = bool(
        whipsaw_10m
        and (
            float(whipsaw_10m.get("rebound_above_sell_rate", 0.0)) >= 50.0
            or float(whipsaw_10m.get("mfe_ge_0_5_rate", 0.0)) >= 30.0
        )
    )
    if rebound_buy_rate >= 50.0:
        recommendation = "cooldown live 금지, threshold/AI 재판정 후보"
    elif whipsaw_signal:
        recommendation = "soft_stop whipsaw confirmation canary 후보"
    elif rebound_sell_rate >= 50.0 and rebound_buy_rate < 50.0 and soft_reentry_losses > 0:
        recommendation = "same-symbol cooldown canary 후보"
    else:
        recommendation = "관찰 지속"
    return {
        "candidate_id": "soft_stop_rebound_split",
        "priority": 1,
        "priority_basis": "soft_stop completed_valid 손익 훼손이 가장 크므로 보유/청산 pain point 1순위다. 단, live 조작점은 rebound/reentry 조건으로 분리한다.",
        "total_soft_stop": total,
        "rebound_above_sell_10m_rate": rebound_sell_rate,
        "rebound_above_buy_10m_rate": rebound_buy_rate,
        "cooldown_would_block_rate": cooldown_rate,
        "same_symbol_reentry_loss_count": soft_reentry_losses,
        "whipsaw_signal": whipsaw_signal,
        "whipsaw_windows": whipsaw_windows,
        "hard_stop_auxiliary": _build_hard_stop_auxiliary(post_sell_rows, valid_trades),
        "recommendation": recommendation,
        "cooldown_live_allowed": bool(
            rebound_sell_rate >= 50.0 and rebound_buy_rate < 50.0 and soft_reentry_losses > 0
        ),
    }


def _build_same_symbol_reentry(valid_trades: list[dict]) -> dict:
    by_code: dict[str, list[dict]] = defaultdict(list)
    for row in valid_trades:
        code = str(row.get("code") or "").strip()
        if code:
            by_code[code].append(row)

    reentries: list[dict] = []
    for code, rows in by_code.items():
        ordered = sorted(rows, key=lambda item: _parse_dt(item.get("buy_time")) or datetime.min)
        for prev, next_trade in zip(ordered, ordered[1:]):
            prev_sell_dt = _parse_dt(prev.get("sell_time"))
            next_buy_dt = _parse_dt(next_trade.get("buy_time"))
            if not prev_sell_dt or not next_buy_dt or next_buy_dt < prev_sell_dt:
                continue
            gap_min = (next_buy_dt - prev_sell_dt).total_seconds() / 60.0
            if gap_min > 60.0:
                continue
            prev_rule = _exit_group(_exit_rule_from_trade(prev))
            next_profit = float(_safe_float(next_trade.get("profit_rate"), 0.0) or 0.0)
            reentries.append(
                {
                    "code": code,
                    "name": str(prev.get("name") or next_trade.get("name") or ""),
                    "prev_id": _trade_id(prev),
                    "next_id": _trade_id(next_trade),
                    "gap_min": round(gap_min, 1),
                    "prev_exit_rule": prev_rule,
                    "prev_profit_rate": round(float(_safe_float(prev.get("profit_rate"), 0.0) or 0.0), 3),
                    "next_profit_rate": round(next_profit, 3),
                    "higher_reentry": (
                        float(_safe_float(next_trade.get("buy_price"), 0.0) or 0.0)
                        > float(_safe_float(prev.get("sell_price"), 0.0) or 0.0)
                    ),
                    "post_fallback_reentry": _is_post_fallback(next_trade),
                    "next_loss": next_profit <= 0,
                }
            )
    by_prev_rule = Counter(row["prev_exit_rule"] for row in reentries)
    return {
        "window_min": 60,
        "total_reentries": len(reentries),
        "higher_reentry_count": sum(1 for row in reentries if row["higher_reentry"]),
        "post_fallback_reentry_count": sum(1 for row in reentries if row["post_fallback_reentry"]),
        "after_trailing_count": int(by_prev_rule.get("scalp_trailing_take_profit", 0)),
        "after_soft_stop_count": int(by_prev_rule.get("scalp_soft_stop_pct", 0)),
        "after_soft_stop_next_loss_count": sum(
            1 for row in reentries if row["prev_exit_rule"] == "scalp_soft_stop_pct" and row["next_loss"]
        ),
        "prev_exit_rule_counts": [{"label": key, "count": value} for key, value in by_prev_rule.most_common()],
        "examples": sorted(
            reentries,
            key=lambda row: (row["post_fallback_reentry"], -row["gap_min"]),
            reverse=True,
        )[:10],
    }


def _pipeline_event_paths(dates: list[str]) -> list[Path]:
    paths: list[Path] = []
    base = DATA_DIR / "pipeline_events"
    for target_date in dates:
        for suffix in (".jsonl", ".jsonl.gz"):
            path = base / f"pipeline_events_{target_date}{suffix}"
            if path.exists():
                paths.append(path)
    return paths


def _summarize_target_pipeline_events(target_date: str) -> tuple[dict, list[str], int]:
    paths = _pipeline_event_paths([target_date])
    counts = Counter()
    fallback_regression = 0
    row_count = 0
    for path in paths:
        for payload in _read_jsonl(path):
            row_count += 1
            stage = str(payload.get("stage") or "").strip()
            if stage:
                counts[stage] += 1
            fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
            if stage == "position_rebased_after_fill":
                fill_quality = str(fields.get("fill_quality") or "").upper()
                if "PARTIAL" in fill_quality:
                    counts["partial_fill_events"] += 1
                else:
                    counts["full_fill_events"] += 1
            joined = " ".join(str(value) for value in [stage, *(fields or {}).values()])
            if "fallback_scout" in joined or "fallback_main" in joined or "fallback_single" in joined:
                fallback_regression += 1
    return (
        {
            "order_bundle_submitted_events": int(counts.get("order_bundle_submitted", 0)),
            "full_fill_events": int(counts.get("full_fill_events", 0)),
            "partial_fill_events": int(counts.get("partial_fill_events", 0)),
            "fallback_regression_count": int(fallback_regression),
        },
        [str(path) for path in paths],
        row_count,
    )


def _build_opportunity_cost(dates: list[str]) -> tuple[dict, list[str]]:
    snapshots, paths = _load_saved_snapshots("missed_entry_counterfactual", dates)
    outcome_counts = Counter()
    terminal_counts = Counter()
    total_estimated_pnl = 0
    evaluated = 0
    for snapshot in snapshots:
        summary = snapshot.get("summary") or {}
        metrics = snapshot.get("metrics") or {}
        outcome_counts.update(summary.get("outcome_counts") or {})
        evaluated += _safe_int(metrics.get("evaluated_candidates", summary.get("evaluated_candidates")), 0)
        total_estimated_pnl += _safe_int(metrics.get("estimated_counterfactual_pnl_10m_krw_sum"), 0)
        for row in snapshot.get("rows") or []:
            terminal_counts[str(row.get("terminal_stage") or "-")] += 1
    return (
        {
            "evaluated_candidates": int(evaluated),
            "outcome_counts": {
                "MISSED_WINNER": int(outcome_counts.get("MISSED_WINNER", 0)),
                "AVOIDED_LOSER": int(outcome_counts.get("AVOIDED_LOSER", 0)),
                "NEUTRAL": int(outcome_counts.get("NEUTRAL", 0)),
            },
            "terminal_stage_top": [
                {"label": key, "count": value} for key, value in terminal_counts.most_common(10)
            ],
            "estimated_counterfactual_pnl_10m_krw_sum": int(total_estimated_pnl),
            "interpretation": "기회비용 방향성 참고용이며 COMPLETED 실현손익과 합산하지 않는다.",
        },
        paths,
    )


def _build_readiness(
    *,
    target_date: str,
    target_valid_trades: list[dict],
    performance_snapshot: dict | None,
    target_pipeline_summary: dict,
) -> dict:
    metrics = (performance_snapshot or {}).get("metrics") or {}
    submitted = _safe_int(metrics.get("order_bundle_submitted_events"), 0)
    full_fill = _safe_int(metrics.get("full_fill_events"), 0)
    partial_fill = _safe_int(metrics.get("partial_fill_events"), 0)
    if submitted <= 0:
        submitted = _safe_int(target_pipeline_summary.get("order_bundle_submitted_events"), 0)
    if full_fill + partial_fill <= 0:
        full_fill = _safe_int(target_pipeline_summary.get("full_fill_events"), 0)
        partial_fill = _safe_int(target_pipeline_summary.get("partial_fill_events"), 0)
    completed_valid = len(target_valid_trades)
    observation_ready = submitted >= 20 or (full_fill + partial_fill) >= 5
    directional_only = completed_valid < 10 or (completed_valid < 50 and submitted < 20)
    return {
        "target_date": target_date,
        "submitted_orders": int(submitted),
        "full_fill_events": int(full_fill),
        "partial_fill_events": int(partial_fill),
        "completed_valid_trades": int(completed_valid),
        "observation_ready": bool(observation_ready),
        "hard_pass_fail_allowed": not directional_only,
        "directional_only": bool(directional_only),
        "reason": (
            "submitted>=20 또는 full+partial>=5 조건 충족"
            if observation_ready
            else "submitted/full/partial 표본 부족"
        ),
    }


def _build_load_distribution_evidence(
    *,
    target_date: str,
    snapshot_paths: dict[str, list[str]],
    post_sell_paths: list[str],
    pipeline_paths: list[str],
    post_sell_rows: int,
    pipeline_rows: int,
) -> dict:
    manifest_dir = DATA_DIR / "report" / "monitor_snapshots" / "manifests"
    manifest_paths = [
        str(path)
        for path in (
            manifest_dir / f"monitor_snapshot_manifest_{target_date}_intraday_light.json",
            manifest_dir / f"monitor_snapshot_manifest_{target_date}_full.json",
        )
        if path.exists()
    ]
    return {
        "policy": "saved snapshot 우선 -> safe wrapper async dispatch -> completion artifact/Telegram",
        "direct_foreground_build_allowed": False,
        "intraday_refresh_command": f"deploy/run_monitor_snapshot_incremental_cron.sh {target_date}",
        "full_refresh_command": f"deploy/run_monitor_snapshot_cron.sh {target_date}",
        "full_snapshot_window": "12:00~12:20 KST 1회",
        "snapshot_paths": snapshot_paths,
        "manifest_paths": manifest_paths,
        "post_sell_files_read": post_sell_paths,
        "post_sell_rows_read": int(post_sell_rows),
        "pipeline_event_files_read": pipeline_paths,
        "pipeline_event_rows_read": int(pipeline_rows),
        "server_comparison_excluded": True,
    }


def build_holding_exit_observation_report(
    *,
    target_date: str,
    month_start: str | None = None,
) -> dict:
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    safe_month_start = str(month_start or f"{safe_date[:7]}-01").strip()
    guarded = guard_stdin_heavy_build(
        snapshot_kind="holding_exit_observation",
        target_date=safe_date,
        fallback_snapshot=_load_saved_snapshot("holding_exit_observation", safe_date),
        request_details={"month_start": safe_month_start},
    )
    if guarded is not None:
        return guarded

    dates = _date_range(safe_month_start, safe_date)
    trade_snapshots, trade_snapshot_paths = _load_saved_snapshots("trade_review", dates)
    performance_snapshot = _load_saved_snapshot("performance_tuning", safe_date)
    performance_paths = []
    perf_path = _monitor_snapshot_path("performance_tuning", safe_date)
    if perf_path is not None:
        performance_paths.append(str(perf_path))

    valid_trades = [row for row in _trade_rows_from_snapshots(trade_snapshots) if _is_valid_completed_trade(row)]
    target_valid_trades = [
        row
        for row in valid_trades
        if str(row.get("rec_date") or "") == safe_date or str(row.get("buy_time") or "").startswith(safe_date)
    ]
    post_sell_rows, post_sell_paths = _load_post_sell_rows(dates)
    target_pipeline_summary, pipeline_paths, pipeline_rows = _summarize_target_pipeline_events(safe_date)
    opportunity_cost, missed_entry_paths = _build_opportunity_cost(dates)
    fallback_regression_count = _safe_int(target_pipeline_summary.get("fallback_regression_count"), 0)

    same_symbol_reentry = _build_same_symbol_reentry(valid_trades)
    report = {
        "date": safe_date,
        "month_start": safe_month_start,
        "readiness": _build_readiness(
            target_date=safe_date,
            target_valid_trades=target_valid_trades,
            performance_snapshot=performance_snapshot,
            target_pipeline_summary=target_pipeline_summary,
        ),
        "cohorts": _build_cohorts(valid_trades),
        "exit_rule_quality": _summarize_exit_rule_quality(post_sell_rows, valid_trades),
        "trailing_continuation": _build_trailing_continuation(
            post_sell_rows=post_sell_rows,
            valid_trades=valid_trades,
            fallback_regression_count=fallback_regression_count,
        ),
        "soft_stop_rebound": _build_soft_stop_rebound(
            post_sell_rows,
            same_symbol_reentry,
            valid_trades,
        ),
        "same_symbol_reentry": same_symbol_reentry,
        "opportunity_cost": opportunity_cost,
        "load_distribution_evidence": _build_load_distribution_evidence(
            target_date=safe_date,
            snapshot_paths={
                "trade_review": trade_snapshot_paths,
                "performance_tuning": performance_paths,
                "missed_entry_counterfactual": missed_entry_paths,
            },
            post_sell_paths=post_sell_paths,
            pipeline_paths=pipeline_paths,
            post_sell_rows=len(post_sell_rows),
            pipeline_rows=pipeline_rows,
        ),
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "basis": "main-only, normal_only, post_fallback_deprecation",
            "profit_basis": "COMPLETED + valid profit_rate only",
            "post_fallback_cutoff": POST_FALLBACK_CUTOFF.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }
    return report
