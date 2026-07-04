"""Backtest scalping entry AI score/action gates from existing report artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "entry_ai_gate_backtest"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
SCALP_ENTRY_ADM_DIR = DATA_DIR / "report" / "scalp_entry_action_decision_matrix"
MISSED_ENTRY_DIRS = [
    DATA_DIR / "report" / "monitor_snapshots",
    DATA_DIR / "report" / "missed_entry_counterfactual",
]
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"

REALIZED_SAMPLE_FLOOR = 30
COUNTERFACTUAL_SAMPLE_FLOOR = 100
THRESHOLD_RANGE = range(55, 86)
SUPPORTED_WAIT_MIN_SCORE = 60
SUPPORTED_WAIT_MAX_SCORE = 74
SUPPORTED_WAIT_ACTIONS = {"WAIT", "DROP", "NO_BUY_AI", ""}
HARD_BLOCK_TOKENS = {
    "broker",
    "cooldown",
    "account",
    "deposit",
    "quantity",
    "zero_qty",
    "manual_control",
    "already_holding",
    "open_pending",
    "loss_reentry",
    "hard_stop",
    "protect_stop",
    "emergency",
}
FORBIDDEN_USES = [
    "score_only_buy",
    "intraday_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "quantity_or_cap_change",
    "entry_price_reprice",
]


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "null", "none", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "stale"}


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates: list[str] = []
    current = start
    while current <= end:
        if is_krx_trading_day(current):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _load_json(path: Path) -> dict[str, Any]:
    actual = existing_or_gzip_path(path)
    if not actual.exists():
        return {}
    try:
        with open_text_auto(actual) as handle:
            return json.loads(handle.read())
    except Exception:
        return {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    actual = existing_or_gzip_path(path)
    if not actual.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with open_text_auto(actual) as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except Exception:
        return []
    return rows


def _missed_entry_path(target_date: str) -> Path:
    for base in MISSED_ENTRY_DIRS:
        path = existing_or_gzip_path(base / f"missed_entry_counterfactual_{target_date}.json")
        if path.exists():
            return path
    return existing_or_gzip_path(MISSED_ENTRY_DIRS[0] / f"missed_entry_counterfactual_{target_date}.json")


def _real_post_sell_outcomes(source_date: str) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for name in ("post_sell_evaluations", "post_sell_candidates"):
        path = POST_SELL_DIR / f"{name}_{source_date}.jsonl"
        for row in _load_jsonl(path):
            if str(row.get("strategy") or "").upper() not in {"", "SCALPING"}:
                continue
            rec_id = str(row.get("recommendation_id") or "").strip()
            profit = _safe_float(row.get("profit_rate"), None)
            if not rec_id or profit is None:
                continue
            prior = outcomes.get(rec_id)
            if prior and prior.get("_outcome_source") == "post_sell_evaluations":
                continue
            item = dict(row)
            item["_outcome_source"] = name
            item["_profit_rate"] = profit
            outcomes[rec_id] = item
    return outcomes


def _source_quality_blocked(row: dict[str, Any]) -> bool:
    text_parts = [
        row.get("source_quality_gate"),
        row.get("source_quality_block_reason"),
        row.get("entry_score_excluded_reason"),
        row.get("ai_input_source_quality_reason"),
    ]
    text = " ".join(str(part or "").lower() for part in text_parts)
    return bool("source_quality_blocked" in text or "hard_block" in text)


def _hard_blocked(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or row.get("terminal_stage") or row.get("source_stage") or "").lower()
    reason = " ".join(
        str(row.get(key) or "").lower()
        for key in (
            "blocked_reason",
            "no_submit_reason",
            "source_quality_block_reason",
            "entry_submit_revalidation_block",
        )
    )
    return any(token in stage or token in reason for token in HARD_BLOCK_TOKENS)


def _stale(row: dict[str, Any]) -> bool:
    if any(_safe_bool(row.get(key)) for key in ("quote_stale", "tick_context_stale", "context_stale")):
        return True
    submit_block = str(row.get("entry_submit_revalidation_block") or "").strip().lower()
    if submit_block and submit_block not in {"0", "false", "no", "n", "off", "-"}:
        return True
    stale_bucket = str(row.get("stale_bucket") or "").lower()
    return stale_bucket in {"stale", "quote_stale", "stale_quote"}


def _micro_support(row: dict[str, Any]) -> bool:
    buy_pressure = _safe_float(row.get("buy_pressure_10t"), None)
    net_delta = _safe_float(row.get("net_aggressive_delta_10t"), None)
    tick_accel = _safe_float(row.get("tick_acceleration_ratio") or row.get("tick_accel"), None)
    micro_vwap = _safe_float(row.get("curr_vs_micro_vwap_bp") or row.get("micro_vwap_bp"), None)
    large_sell = _safe_bool(row.get("large_sell_print_detected"))
    support = (
        (buy_pressure is not None and buy_pressure >= 68.0)
        or (net_delta is not None and net_delta > 0.0)
        or (tick_accel is not None and tick_accel >= 1.10)
        or (micro_vwap is not None and micro_vwap > 0.0)
    )
    return bool(support and not large_sell)


def _score(row: dict[str, Any]) -> float | None:
    for key in ("ai_score", "score_source_value", "current_ai_score"):
        value = _safe_float(row.get(key), None)
        if value is not None:
            return value
    return None


def _realized_rows(source_dates: list[str], missing: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_date in source_dates:
        path = existing_or_gzip_path(SCALP_ENTRY_ADM_DIR / f"scalp_entry_action_decision_matrix_{source_date}.json")
        report = _load_json(path)
        if not report:
            missing.append({"date": source_date, "artifact": "scalp_entry_action_decision_matrix", "path": str(path)})
            continue
        real_outcomes = _real_post_sell_outcomes(source_date)
        real_joined_by_record: dict[str, tuple[int, dict[str, Any]]] = {}
        for raw in report.get("rows") or []:
            if not isinstance(raw, dict):
                continue
            score = _score(raw)
            if score is None:
                continue
            record_id = str(raw.get("record_id") or "").strip()
            outcome = real_outcomes.get(record_id)
            profit = _safe_float((outcome or {}).get("_profit_rate"), None)
            outcome_source = (outcome or {}).get("_outcome_source")
            if profit is None and _safe_bool(raw.get("actual_order_submitted") or raw.get("broker_order_submitted")):
                profit = _safe_float(raw.get("profit_rate"), None)
                outcome_source = "scalp_entry_action_decision_matrix"
            if profit is None:
                continue
            row = dict(raw)
            if outcome:
                row.update(
                    {
                        "actual_order_submitted": True,
                        "broker_order_forbidden": False,
                        "post_sell_id": outcome.get("post_sell_id"),
                        "sell_time": outcome.get("sell_time"),
                        "exit_rule": outcome.get("exit_rule"),
                    }
                )
            row["_date"] = source_date
            row["_score"] = score
            row["_realized_profit_pct"] = profit
            row["_realized_outcome_source"] = outcome_source or "unknown"
            if outcome and record_id:
                stage_text = f"{row.get('stage') or ''} {row.get('source_stage') or ''}".lower()
                if "ai_confirmed" in stage_text:
                    priority = 0
                elif "blocked_ai_score" in stage_text:
                    priority = 1
                elif str(row.get("ai_action") or "").strip():
                    priority = 2
                else:
                    priority = 3
                prior = real_joined_by_record.get(record_id)
                if prior is None or priority < prior[0]:
                    real_joined_by_record[record_id] = (priority, row)
            else:
                rows.append(row)
        rows.extend(item[1] for item in real_joined_by_record.values())
    return rows


def _counterfactual_rows(source_dates: list[str], missing: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_date in source_dates:
        path = _missed_entry_path(source_date)
        report = _load_json(path)
        if not report:
            missing.append({"date": source_date, "artifact": "missed_entry_counterfactual", "path": str(path)})
            continue
        for raw in report.get("full_rows") or []:
            if not isinstance(raw, dict):
                continue
            close_10m = _safe_float(raw.get("close_10m_pct"), None)
            score = _score(raw)
            if close_10m is None or score is None:
                continue
            row = dict(raw)
            row["_date"] = source_date
            row["_score"] = score
            row["_close_10m_pct"] = close_10m
            row["_mfe_10m_pct"] = _safe_float(raw.get("mfe_10m_pct"), 0.0) or 0.0
            row["_mae_10m_pct"] = _safe_float(raw.get("mae_10m_pct"), 0.0) or 0.0
            rows.append(row)
    return rows


def _notional(row: dict[str, Any]) -> float:
    value = _safe_float(row.get("counterfactual_notional_krw") or row.get("notional_krw"), None)
    return value if value and value > 0 else 1.0


def _metrics(rows: list[dict[str, Any]], value_key: str) -> dict[str, Any]:
    values = [_safe_float(row.get(value_key), None) for row in rows]
    values = [value for value in values if value is not None]
    if not values:
        return {
            "sample": 0,
            "diagnostic_win_rate": 0.0,
            "equal_weight_avg_profit_pct": 0.0,
            "notional_weighted_ev_pct": 0.0,
            "source_quality_adjusted_ev_pct": 0.0,
            "simple_sum_profit_pct": 0.0,
        }
    notionals = [_notional(row) for row in rows if _safe_float(row.get(value_key), None) is not None]
    weighted = sum(value * notional for value, notional in zip(values, notionals)) / max(sum(notionals), 1.0)
    source_quality_pass = sum(1 for row in rows if not _source_quality_blocked(row))
    quality_ratio = source_quality_pass / len(rows) if rows else 0.0
    avg = sum(values) / len(values)
    return {
        "sample": len(values),
        "diagnostic_win_rate": round(sum(1 for value in values if value > 0) * 100.0 / len(values), 2),
        "equal_weight_avg_profit_pct": round(avg, 6),
        "notional_weighted_ev_pct": round(weighted, 6),
        "source_quality_adjusted_ev_pct": round(avg * quality_ratio, 6),
        "simple_sum_profit_pct": round(sum(values), 6),
    }


def _matches_policy(row: dict[str, Any], policy: str, threshold: int) -> bool:
    score = _safe_float(row.get("_score"), -1.0) or -1.0
    ai_action = str(row.get("ai_action") or row.get("action") or "").strip().upper()
    chosen_action = str(row.get("chosen_action") or "").strip().upper()
    if policy == "strict_buy":
        return (
            ai_action == "BUY"
            and score >= threshold
            and not _stale(row)
            and not _hard_blocked(row)
            and not _source_quality_blocked(row)
        )
    if policy == "diagnostic_score_only":
        return score >= threshold
    if policy == "supported_wait_recovery":
        action_key = ai_action or chosen_action
        return (
            SUPPORTED_WAIT_MIN_SCORE <= score <= SUPPORTED_WAIT_MAX_SCORE
            and score >= threshold
            and action_key in SUPPORTED_WAIT_ACTIONS
            and not _stale(row)
            and not _hard_blocked(row)
            and not _source_quality_blocked(row)
            and _micro_support(row)
        )
    return False


def _policy_result(
    *,
    policy: str,
    threshold: int,
    realized_rows: list[dict[str, Any]],
    counterfactual_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    realized = [row for row in realized_rows if _matches_policy(row, policy, threshold)]
    counterfactual = [row for row in counterfactual_rows if _matches_policy(row, policy, threshold)]
    realized_metrics = _metrics(realized, "_realized_profit_pct")
    opportunity_metrics = _metrics(counterfactual, "_close_10m_pct")
    mae_values = [_safe_float(row.get("_mae_10m_pct"), None) for row in counterfactual]
    mae_values = [value for value in mae_values if value is not None]
    mfe_values = [_safe_float(row.get("_mfe_10m_pct"), None) for row in counterfactual]
    mfe_values = [value for value in mfe_values if value is not None]
    sample_floor_passed = (
        realized_metrics["sample"] >= REALIZED_SAMPLE_FLOOR
        and opportunity_metrics["sample"] >= COUNTERFACTUAL_SAMPLE_FLOOR
    )
    allowed = bool(policy != "diagnostic_score_only" and sample_floor_passed)
    return {
        "policy": policy,
        "threshold": threshold,
        "realized": realized_metrics,
        "counterfactual": {
            **opportunity_metrics,
            "missed_upside_close_10m_pct": opportunity_metrics["equal_weight_avg_profit_pct"],
            "mfe_10m_pct": round(sum(mfe_values) / len(mfe_values), 6) if mfe_values else 0.0,
            "mae_10m_pct": round(sum(mae_values) / len(mae_values), 6) if mae_values else 0.0,
        },
        "sample_floor_passed": sample_floor_passed,
        "calibration_state": "candidate_ready" if allowed else "hold_sample",
        "allowed_runtime_apply": allowed,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _policy_rank_key(item: dict[str, Any]) -> tuple[Any, ...]:
    realized = item.get("realized") or {}
    counterfactual = item.get("counterfactual") or {}
    passed = bool(item.get("sample_floor_passed"))
    ev = float(realized.get("source_quality_adjusted_ev_pct") or 0.0)
    missed = float(counterfactual.get("missed_upside_close_10m_pct") or 0.0)
    realized_sample = int(realized.get("sample") or 0)
    counterfactual_sample = int(counterfactual.get("sample") or 0)
    threshold = int(item.get("threshold") or 0)
    if passed:
        return (1, ev, missed, realized_sample, counterfactual_sample, -threshold)
    return (0, realized_sample, counterfactual_sample, ev, missed, -threshold)


def _best_candidate(results: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=_policy_rank_key,
        reverse=True,
    )
    return ranked[0] if ranked else {}


def _best_allowed_candidate(results: list[dict[str, Any]]) -> dict[str, Any]:
    return _best_candidate([item for item in results if item.get("allowed_runtime_apply")])


def _best_by_realized_ev(results: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=lambda item: (
            float((item.get("realized") or {}).get("source_quality_adjusted_ev_pct") or 0.0),
            int((item.get("realized") or {}).get("sample") or 0),
            int((item.get("counterfactual") or {}).get("sample") or 0),
            -int(item.get("threshold") or 0),
        ),
        reverse=True,
    )
    return ranked[0] if ranked else {}


def build_report(target_date: str, *, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    source_dates, excluded_dates = filter_allowed_dates(_date_range(start, end), policy)
    missing_artifacts: list[dict[str, str]] = []
    realized = _realized_rows(source_dates, missing_artifacts)
    counterfactual = _counterfactual_rows(source_dates, missing_artifacts)
    results = [
        _policy_result(policy=policy_name, threshold=threshold, realized_rows=realized, counterfactual_rows=counterfactual)
        for policy_name in ("strict_buy", "supported_wait_recovery", "diagnostic_score_only")
        for threshold in THRESHOLD_RANGE
    ]
    best = _best_candidate([item for item in results if item["policy"] != "diagnostic_score_only"])
    best_allowed = _best_allowed_candidate([item for item in results if item["policy"] != "diagnostic_score_only"])
    diagnostic_results = [item for item in results if item["policy"] == "diagnostic_score_only"]
    best_diagnostic = _best_candidate(diagnostic_results)
    best_positive_diagnostic = _best_by_realized_ev(
        [
            item
            for item in diagnostic_results
            if float((item.get("realized") or {}).get("source_quality_adjusted_ev_pct") or 0.0) > 0.0
        ]
    )
    score_band_counts: Counter[str] = Counter()
    for row in counterfactual:
        score = _safe_float(row.get("_score"), -1.0) or -1.0
        if score < 50:
            score_band_counts["score_lt50"] += 1
        elif score < 60:
            score_band_counts["score50_59"] += 1
        elif score < 65:
            score_band_counts["score60_64"] += 1
        elif score < 70:
            score_band_counts["score65_69"] += 1
        elif score < 75:
            score_band_counts["score70_74"] += 1
        else:
            score_band_counts["score75_plus"] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "source_paths": {
            "scalp_entry_action_decision_matrix": str(SCALP_ENTRY_ADM_DIR),
            "missed_entry_counterfactual": [str(path) for path in MISSED_ENTRY_DIRS],
            "pipeline_events": str(PIPELINE_EVENTS_DIR),
            "post_sell": str(POST_SELL_DIR),
        },
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "entry_ai_gate_backtest_postclose_candidate",
            "window_policy": f"{start}_to_{end}",
            "sample_floor": {
                "realized_joined_rows": REALIZED_SAMPLE_FLOOR,
                "counterfactual_rows": COUNTERFACTUAL_SAMPLE_FLOOR,
            },
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "clean_baseline_allowed_rows_without_hard_source_quality_block",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": bool(best_allowed.get("allowed_runtime_apply", False)),
        "calibration_state": "candidate_ready" if best_allowed else "hold_sample",
        "summary": {
            "realized_joined_rows": len(realized),
            "counterfactual_rows": len(counterfactual),
            "score_band_counterfactual_counts": dict(score_band_counts),
            "best_policy": best.get("policy"),
            "best_threshold": best.get("threshold"),
            "best_realized_source_quality_adjusted_ev_pct": (best.get("realized") or {}).get(
                "source_quality_adjusted_ev_pct"
            ),
            "best_counterfactual_close_10m_pct": (best.get("counterfactual") or {}).get(
                "missed_upside_close_10m_pct"
            ),
            "sample_floor_passed": bool(best.get("sample_floor_passed", False)),
            "best_apply_policy": best_allowed.get("policy"),
            "best_apply_threshold": best_allowed.get("threshold"),
            "best_apply_realized_source_quality_adjusted_ev_pct": (best_allowed.get("realized") or {}).get(
                "source_quality_adjusted_ev_pct"
            ),
            "best_apply_counterfactual_close_10m_pct": (best_allowed.get("counterfactual") or {}).get(
                "missed_upside_close_10m_pct"
            ),
            "best_diagnostic_score_only_threshold": best_diagnostic.get("threshold"),
            "best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct": (
                best_diagnostic.get("realized") or {}
            ).get("source_quality_adjusted_ev_pct"),
            "best_diagnostic_score_only_counterfactual_close_10m_pct": (
                best_diagnostic.get("counterfactual") or {}
            ).get("missed_upside_close_10m_pct"),
            "best_diagnostic_score_only_realized_sample": (best_diagnostic.get("realized") or {}).get("sample"),
            "best_diagnostic_score_only_counterfactual_sample": (
                best_diagnostic.get("counterfactual") or {}
            ).get("sample"),
            "best_positive_realized_diagnostic_threshold": best_positive_diagnostic.get("threshold"),
            "best_positive_realized_diagnostic_ev_pct": (best_positive_diagnostic.get("realized") or {}).get(
                "source_quality_adjusted_ev_pct"
            ),
            "best_positive_realized_diagnostic_sample_floor_passed": bool(
                best_positive_diagnostic.get("sample_floor_passed", False)
            ),
            "best_positive_realized_diagnostic_realized_sample": (best_positive_diagnostic.get("realized") or {}).get(
                "sample"
            ),
            "best_positive_realized_diagnostic_counterfactual_sample": (
                best_positive_diagnostic.get("counterfactual") or {}
            ).get("sample"),
        },
        "best_candidate": best,
        "best_apply_candidate": best_allowed,
        "best_diagnostic_score_only_candidate": best_diagnostic,
        "best_positive_realized_diagnostic_candidate": best_positive_diagnostic,
        "policy_results": results,
        "missing_artifacts": missing_artifacts,
        "forbidden_uses": FORBIDDEN_USES,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    best = report.get("best_candidate") if isinstance(report.get("best_candidate"), dict) else {}
    lines = [
        f"# Entry AI Gate Backtest - {report.get('target_date')}",
        "",
        f"- calibration_state: `{report.get('calibration_state')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- realized_joined_rows: `{summary.get('realized_joined_rows')}`",
        f"- counterfactual_rows: `{summary.get('counterfactual_rows')}`",
        f"- best_policy: `{summary.get('best_policy')}`",
        f"- best_threshold: `{summary.get('best_threshold')}`",
        f"- best_realized_source_quality_adjusted_ev_pct: `{summary.get('best_realized_source_quality_adjusted_ev_pct')}`",
        f"- best_counterfactual_close_10m_pct: `{summary.get('best_counterfactual_close_10m_pct')}`",
        f"- best_apply_policy: `{summary.get('best_apply_policy')}`",
        f"- best_apply_threshold: `{summary.get('best_apply_threshold')}`",
        f"- best_diagnostic_score_only_threshold: `{summary.get('best_diagnostic_score_only_threshold')}`",
        f"- best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct: "
        f"`{summary.get('best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct')}`",
        f"- best_diagnostic_score_only_counterfactual_close_10m_pct: "
        f"`{summary.get('best_diagnostic_score_only_counterfactual_close_10m_pct')}`",
        f"- best_positive_realized_diagnostic_threshold: "
        f"`{summary.get('best_positive_realized_diagnostic_threshold')}`",
        f"- best_positive_realized_diagnostic_ev_pct: "
        f"`{summary.get('best_positive_realized_diagnostic_ev_pct')}`",
        f"- best_positive_realized_diagnostic_sample_floor_passed: "
        f"`{summary.get('best_positive_realized_diagnostic_sample_floor_passed')}`",
        "",
        "## Best Candidate",
        "",
        "```json",
        json.dumps(best, ensure_ascii=False, indent=2, default=str),
        "```",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("target_date") or "unknown"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_report(report)
        print(json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
