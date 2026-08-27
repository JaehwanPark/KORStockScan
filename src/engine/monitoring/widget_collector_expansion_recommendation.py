"""Recommend, but never create, additional widget collector symbols.

The deterministic report combines every available clean-baseline exact
Entry-AI payload/replay date.  It is an operator recommendation and has no
authority to create collectors, start services, call Kiwoom, or alter trading
behavior.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any, Callable
from urllib import parse, request

from src.engine.monitoring import widget_mechanical_entry_replay as mechanical_replay
from src.engine.monitoring.samsung_widget_contract import (
    KST,
    NXT_AFTERMARKET_END,
    previous_krx_trading_date,
)
from src.engine.scalping.ai_decision_trace import replay_source_input
from src.engine.monitoring.widget_symbol_signal_policy_research import (
    SYMBOLS as RESEARCH_WIDGET_SYMBOLS,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    cost_aware_return_pct,
)
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT
from src.utils.jsonl_io import iter_jsonl_objects_strict, read_json_object_strict
from src.utils.market_day import is_krx_trading_day

AUTHORITY = "widget_collector_expansion_recommendation_only"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
ACTIVE_WIDGET_CODES = frozenset({"005930", "034020", "042660"})
IMPLEMENTED_WIDGET_CODES = ACTIVE_WIDGET_CODES | frozenset(RESEARCH_WIDGET_SYMBOLS)
DEFAULT_REPLAY_DIR = Path("data/report/widget_mechanical_entry_replay")
DEFAULT_PAYLOAD_DIR = Path("data/ai_decision_payloads")
DEFAULT_SENTINEL_DIR = Path("data/runtime/sentinel_event_cache")
DEFAULT_OUTPUT_DIR = Path("data/report/widget_collector_expansion_recommendation")
DEFAULT_RESEARCH_WATCH_CONFIG_PATH = Path(
    "data/config/widget_research_watch_symbols.json"
)
DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "widget_collector_expansion_telegram_state.json"
)
# Retain a ranked review set larger than the bounded shared collector so
# capacity overflow remains visible instead of silently disappearing.  The
# collector admits only its separately declared active-symbol cap.
MAX_RECOMMENDATIONS = 20
MAX_ACTIVE_RESEARCH_WATCH_SYMBOLS = 15
SHARED_COLLECTOR_REQUESTS_PER_MINUTE = 15
SHARED_COLLECTOR_MEMORY_CAP_MB = 256
IMPLEMENTATION_REVIEW_MIN_SAMPLES = 5
IMPLEMENTATION_REVIEW_MIN_TRADING_DATES = 3
IMPLEMENTATION_REVIEW_MAX_MEDIAN_SPREAD_BP = 25.0
IMPLEMENTATION_REVIEW_MAX_MEDIAN_RANGE_PCT = 12.0

METRIC_CONTRACT = {
    "metric_role": "collector_expansion_recommendation",
    "decision_authority": AUTHORITY,
    "window_policy": "all_available_clean_baseline_exact_replay_dates",
    "sample_floor": (
        "research_watch=two_joined_rows_and_one_decisive_outcome;"
        "implementation_review=five_rows_three_trading_dates_"
        "median_spread_at_most_25bp_range_at_most_12pct"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "source_qualified_exact_replay_outcome_plus_fresh_entry_context_"
        "liquidity_and_quote_features;portable_setup_is_diagnostic"
    ),
    "forbidden_uses": [
        "automatic_collector_creation",
        "automatic_service_start_or_restart",
        "manual_control_exclusion_as_collection_or_evaluation_filter",
        "real_order_submission",
        "account_or_quantity_decision",
        "trading_runtime_threshold",
        "provider_or_token_route_change",
        "broker_or_hard_safety_bypass",
    ],
}

Sender = Callable[[str, str, str], None]
ConfigLoader = Callable[[], tuple[str, str]]


def _dated_paths(directory: Path, prefix: str, *, through_date: date) -> list[Path]:
    selected: list[tuple[date, Path]] = []
    for path in directory.glob(f"{prefix}_*.json*"):
        raw_date = path.name.removeprefix(f"{prefix}_").split(".", 1)[0]
        try:
            artifact_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if CLEAN_BASELINE_DATE <= artifact_date <= through_date:
            selected.append((artifact_date, path))
    return [path for _, path in sorted(selected)]


def _load_names(paths: list[Path]) -> dict[str, str]:
    names: dict[str, str] = {}
    for replay_path in paths:
        target_date = replay_path.stem.rsplit("_", 1)[-1]
        sentinel_paths = (
            DEFAULT_SENTINEL_DIR / f"buy_funnel_sentinel_events_{target_date}.jsonl",
            DEFAULT_SENTINEL_DIR / f"buy_funnel_sentinel_events_{target_date}.jsonl.gz",
        )
        for sentinel_path in sentinel_paths:
            try:
                handle = (
                    gzip.open(sentinel_path, "rt", encoding="utf-8")
                    if sentinel_path.suffix == ".gz"
                    else sentinel_path.open("r", encoding="utf-8")
                )
            except OSError:
                continue
            try:
                with handle:
                    for line in handle:
                        try:
                            row = json.loads(line)
                        except ValueError:
                            continue
                        code = str(row.get("stock_code") or "").strip()
                        name = str(row.get("stock_name") or "").strip()
                        if code and name:
                            names[code] = name
            except (OSError, EOFError):
                # Stock names are display-only enrichment. A damaged archive
                # must not invalidate otherwise qualified market evidence.
                continue
    return names


def _payload_feature(value: object, key: str) -> float | None:
    payload = value if isinstance(value, dict) else {}
    exact = payload.get("exact_payload")
    exact = exact if isinstance(exact, dict) else {}
    features = exact.get("features")
    features = features if isinstance(features, dict) else {}
    try:
        return float(features[key])
    except (KeyError, TypeError, ValueError):
        return None


def _source_qualified_exact_payload(row: object) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    if (
        row.get("schema") != "ai_decision_payload_v1"
        or row.get("endpoint") != "analyze_target"
        or row.get("replay_exact") is not True
        or row.get("runtime_effect") is not False
        or row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
    ):
        return None
    sanitized = replay_source_input(row)
    exact = sanitized.get("exact_payload") if isinstance(sanitized, dict) else None
    if not isinstance(exact, dict):
        return None
    context = exact.get("entry_candle_context")
    context_quality = (
        context.get("source_quality") if isinstance(context, dict) else None
    )
    quote = exact.get("quote")
    if (
        not isinstance(context_quality, dict)
        or context_quality.get("status") != "fresh_consistent"
        or not isinstance(quote, dict)
        or quote.get("quote_stale") not in {True, False}
    ):
        return None
    return exact


def _load_feature_history(
    payload_dir: Path,
    *,
    through_date: date,
    eligible_codes: frozenset[str] | None = None,
) -> tuple[dict[str, list[dict[str, float | bool]]], list[str]]:
    history: dict[str, list[dict[str, float | bool]]] = defaultdict(list)
    paths = _dated_paths(
        payload_dir,
        "ai_decision_payloads",
        through_date=through_date,
    )
    logical_paths = {
        path.with_name(path.name[: -len(".gz")]) if path.suffix == ".gz" else path
        for path in paths
    }
    paths = sorted(logical_paths)
    if eligible_codes is not None and not eligible_codes:
        return history, [str(path) for path in paths]
    for path in paths:
        try:
            rows = iter_jsonl_objects_strict(path)
            for row in rows:
                if (
                    str(row.get("effective_venue") or "").upper() != "KRX"
                    or str(row.get("session_bucket") or "").lower() != "krx_regular"
                ):
                    continue
                exact = _source_qualified_exact_payload(row)
                if exact is None:
                    continue
                code = str(row.get("symbol") or "").strip()
                if eligible_codes is not None and code not in eligible_codes:
                    continue
                sanitized = replay_source_input(row)
                liquidity = _payload_feature(sanitized, "entry_liquidity_score")
                intraday_range = _payload_feature(sanitized, "intraday_range_pct")
                spread_bp = _payload_feature(sanitized, "spread_bp")
                quote = exact.get("quote") if isinstance(exact, dict) else None
                quote_stale = (
                    quote.get("quote_stale") if isinstance(quote, dict) else None
                )
                if (
                    not code
                    or liquidity is None
                    or intraday_range is None
                    or spread_bp is None
                    or quote_stale not in {True, False}
                ):
                    continue
                history[code].append(
                    {
                        "entry_liquidity_score": liquidity,
                        "intraday_range_pct": abs(intraday_range),
                        "spread_bp": spread_bp,
                        "quote_fresh": quote_stale is False,
                    }
                )
        except FileNotFoundError:
            continue
    return history, [str(path) for path in paths]


def _load_replay_history(
    replay_dir: Path,
    *,
    through_date: date,
    current_replay_report: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[Path]]:
    aggregates: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "sample_count": 0,
            "source_qualified_joined_count": 0,
            "target_first_count": 0,
            "adverse_first_count": 0,
            "end_returns": [],
            "cost_adjusted_end_returns": [],
            "mechanical_signal_count": 0,
            "pre_spread_candidate_count": 0,
            "trading_dates": set(),
        }
    )
    paths = _dated_paths(
        replay_dir,
        "widget_mechanical_entry_replay",
        through_date=through_date,
    )
    paths = [path for path in paths if path.suffix == ".json"]
    current_target_date = (
        str(current_replay_report.get("target_date") or "")
        if isinstance(current_replay_report, dict)
        else ""
    )
    reports: list[tuple[Path | None, object]] = []
    for path in paths:
        if current_target_date and path.stem.endswith(f"_{current_target_date}"):
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        reports.append((path, report))
    if current_replay_report is not None:
        reports.append((None, current_replay_report))
    accepted_paths: list[Path] = []
    for path, report in reports:
        if (
            not isinstance(report, dict)
            or report.get("schema") != "widget_mechanical_entry_replay_v1"
            or report.get("runtime_effect") is not False
            or report.get("allowed_runtime_apply") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
        ):
            continue
        try:
            report_date = date.fromisoformat(str(report.get("target_date") or ""))
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date <= through_date:
            continue
        if path is not None and not path.stem.endswith(f"_{report_date}"):
            continue
        if path is not None:
            accepted_paths.append(path)
        for row in report.get("rows", []):
            if not isinstance(row, dict):
                continue
            if (
                str(row.get("effective_venue") or "").upper() != "KRX"
                or str(row.get("session_bucket") or "").lower() != "krx_regular"
            ):
                continue
            code = str(row.get("stock_code") or "").strip()
            if not (len(code) == 6 and code.isdigit()):
                continue
            if (
                row.get("runtime_effect") is not False
                or row.get("actual_order_submitted") is not False
                or row.get("broker_order_forbidden") is not True
            ):
                continue
            item = aggregates[code]
            if str(row.get("mechanical_source_issue") or "").strip():
                continue
            item["source_qualified_joined_count"] += 1
            first_hit = str(row.get("entry_path_first_hit") or "")
            if first_hit not in {
                "target_first",
                "adverse_first",
                "same_bar_ambiguous",
                "neither_hit",
            }:
                continue
            try:
                end_return = float(row.get("end_return_pct"))
            except (TypeError, ValueError):
                continue
            item["sample_count"] += 1
            item["trading_dates"].add(report_date.isoformat())
            if first_hit == "target_first":
                item["target_first_count"] += 1
            elif first_hit == "adverse_first":
                item["adverse_first_count"] += 1
            item["end_returns"].append(end_return)
            item["cost_adjusted_end_returns"].append(
                cost_aware_return_pct(end_return, trade_date=report_date)
            )
            item["mechanical_signal_count"] += row.get("mechanical_signal") is True
            item["pre_spread_candidate_count"] += (
                row.get("mechanical_candidate_before_spread_gate") is True
            )
    return aggregates, accepted_paths


def _score_candidate(
    *,
    target_share_pct: float,
    equal_weight_ev_pct: float,
    liquidity_score: float,
    intraday_range_pct: float,
    sample_count: int,
    portability_ratio: float,
) -> float:
    ev_component = max(0.0, min(1.0, (equal_weight_ev_pct + 1.0) / 2.0))
    volatility_component = max(0.0, min(1.0, (intraday_range_pct - 1.0) / 7.0))
    return round(
        target_share_pct * 0.10
        + ev_component * 45.0
        + max(0.0, min(100.0, liquidity_score)) * 0.20
        + min(1.0, sample_count / 10.0) * 10.0
        + volatility_component * 10.0
        + max(0.0, min(1.0, portability_ratio)) * 5.0,
        4,
    )


def _load_active_research_watch_inventory(
    *, target_date: date, config_path: Path = DEFAULT_RESEARCH_WATCH_CONFIG_PATH
) -> tuple[frozenset[str], list[str]]:
    """Load the exact operator-enrolled catalog without granting apply authority."""

    try:
        from src.engine.monitoring.widget_research_watch_collector import load_config

        config = load_config(observed_date=target_date, config_path=config_path)
    except (OSError, ValueError) as exc:
        return frozenset(), [type(exc).__name__ + ":" + str(exc)]
    return (
        frozenset(str(row["stock_code"]) for row in config["symbols"]),
        [],
    )


def _collection_capacity_context(
    *, candidates: list[dict[str, Any]], active_codes: frozenset[str]
) -> dict[str, Any]:
    candidate_codes = {
        str(row.get("stock_code") or "")
        for row in candidates
        if row.get("recommendation_tier") == "research_watch"
    }
    union_codes = set(active_codes) | candidate_codes
    return {
        "active_research_watch_count": len(active_codes),
        "candidate_research_watch_count": len(candidate_codes),
        "active_candidate_union_count": len(union_codes),
        "research_watch_overflow_candidate_count": max(
            0, len(union_codes) - MAX_ACTIVE_RESEARCH_WATCH_SYMBOLS
        ),
    }


def build_recommendation_report(
    *,
    target_date: date,
    replay_dir: Path = DEFAULT_REPLAY_DIR,
    payload_dir: Path = DEFAULT_PAYLOAD_DIR,
    manual_excluded_codes: frozenset[str] | None = None,
    current_replay_report: dict[str, Any] | None = None,
    active_research_watch_codes: frozenset[str] = frozenset(),
    active_inventory_issues: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build research recommendations without applying final-order exclusions.

    ``manual_excluded_codes`` remains an ignored compatibility keyword for older
    callers.  Manual-control exclusion is enforced only at the final trading
    action boundary and must not censor collection, replay, or evaluation.
    """

    replay, replay_paths = _load_replay_history(
        replay_dir,
        through_date=target_date,
        current_replay_report=current_replay_report,
    )
    exclusion_counts: dict[str, int] = defaultdict(int)
    outcome_candidates: dict[str, dict[str, Any]] = {}
    for code, item in replay.items():
        if code in IMPLEMENTED_WIDGET_CODES:
            exclusion_counts["already_active_widget"] += 1
            continue
        samples = int(item["sample_count"])
        target_first = int(item["target_first_count"])
        adverse_first = int(item["adverse_first_count"])
        decisive = target_first + adverse_first
        end_returns = item.get("cost_adjusted_end_returns")
        if end_returns is None:
            # Compatibility for callers that supply the former aggregate shape.
            # Production history loading always prices each row by its own date.
            end_returns = [
                cost_aware_return_pct(value, trade_date=target_date)
                for value in item.get("end_returns", [])
            ]
        equal_weight_ev = sum(end_returns) / len(end_returns) if end_returns else 0.0
        if samples < 2 or decisive < 1:
            exclusion_counts["sample_floor_not_met"] += 1
            continue
        if equal_weight_ev <= 0:
            exclusion_counts["outcome_quality_not_positive"] += 1
            continue
        outcome_candidates[code] = {
            **item,
            "sample_count": samples,
            "target_first_count": target_first,
            "adverse_first_count": adverse_first,
            "decisive_sample_count": decisive,
            "equal_weight_avg_profit_pct": equal_weight_ev,
            "trading_dates": item["trading_dates"],
        }
    features, feature_paths = _load_feature_history(
        payload_dir,
        through_date=target_date,
        eligible_codes=frozenset(outcome_candidates),
    )
    names = _load_names(replay_paths)
    candidates: list[dict[str, Any]] = []
    for code, item in outcome_candidates.items():
        samples = int(item["sample_count"])
        target_first = int(item["target_first_count"])
        adverse_first = int(item["adverse_first_count"])
        decisive = int(item["decisive_sample_count"])
        equal_weight_ev = float(item["equal_weight_avg_profit_pct"])
        trading_dates = sorted(str(value) for value in item["trading_dates"])
        feature_rows = features.get(code, [])
        if not feature_rows:
            exclusion_counts["liquidity_feature_missing"] += 1
            continue
        liquidity = median(float(row["entry_liquidity_score"]) for row in feature_rows)
        intraday_range = median(
            float(row["intraday_range_pct"]) for row in feature_rows
        )
        spread_bp = median(float(row["spread_bp"]) for row in feature_rows)
        fresh_quote_rate = sum(bool(row["quote_fresh"]) for row in feature_rows) / len(
            feature_rows
        )
        if liquidity < 60 or intraday_range < 1.0 or fresh_quote_rate < 0.80:
            exclusion_counts["tradability_floor_not_met"] += 1
            continue
        portability_count = int(item["mechanical_signal_count"]) + int(
            item["pre_spread_candidate_count"]
        )
        source_qualified_joined_count = int(item["source_qualified_joined_count"])
        portability_ratio = portability_count / max(1, source_qualified_joined_count)
        target_share = target_first / decisive * 100
        implementation_review_blockers: list[str] = []
        if samples < IMPLEMENTATION_REVIEW_MIN_SAMPLES:
            implementation_review_blockers.append("sample_floor_not_met")
        if len(trading_dates) < IMPLEMENTATION_REVIEW_MIN_TRADING_DATES:
            implementation_review_blockers.append("trading_date_floor_not_met")
        if spread_bp > IMPLEMENTATION_REVIEW_MAX_MEDIAN_SPREAD_BP:
            implementation_review_blockers.append("median_spread_too_wide")
        if intraday_range > IMPLEMENTATION_REVIEW_MAX_MEDIAN_RANGE_PCT:
            implementation_review_blockers.append("extreme_volatility")
        recommendation_tier = (
            "implementation_review"
            if not implementation_review_blockers
            else "research_watch"
        )
        candidates.append(
            {
                "stock_code": code,
                "stock_name": names.get(code) or code,
                "recommendation_score": _score_candidate(
                    target_share_pct=target_share,
                    equal_weight_ev_pct=equal_weight_ev,
                    liquidity_score=liquidity,
                    intraday_range_pct=intraday_range,
                    sample_count=samples,
                    portability_ratio=portability_ratio,
                ),
                "sample_count": samples,
                "observed_trading_date_count": len(trading_dates),
                "observed_trading_dates": trading_dates,
                "decisive_sample_count": decisive,
                "target_first_count": target_first,
                "adverse_first_count": adverse_first,
                "diagnostic_target_share_among_decisive_pct": round(target_share, 4),
                "equal_weight_avg_profit_pct": round(equal_weight_ev, 6),
                "source_quality_adjusted_ev_pct": round(equal_weight_ev, 6),
                "round_trip_cost_pct": comparison_cost_contract(target_date)[
                    "round_trip_cost_pct"
                ],
                "comparison_cost_policy": "effective_dated_per_replay_trade_date",
                "source_quality_adjustment_policy": (
                    "exclude_ineligible_rows_then_equal_weight"
                ),
                "median_entry_liquidity_score": round(liquidity, 4),
                "median_intraday_range_pct": round(intraday_range, 4),
                "extreme_volatility_warning": intraday_range > 12.0,
                "median_spread_bp": round(spread_bp, 4),
                "fresh_quote_rate_pct": round(fresh_quote_rate * 100, 4),
                "portable_signal_or_candidate_count": portability_count,
                "source_qualified_joined_count": source_qualified_joined_count,
                "portability_ratio_pct": round(portability_ratio * 100, 4),
                "evidence_status": (
                    "early_sample" if samples < 10 else "accumulating_sample"
                ),
                "recommendation_tier": recommendation_tier,
                "implementation_review_ready": not implementation_review_blockers,
                "implementation_review_blockers": implementation_review_blockers,
                "suggested_session": "KRX_REGULAR",
                "estimated_added_requests_per_minute": None,
                "estimated_added_memory_mb": None,
                "resource_profile": "shared_budget_paced_research_watch_collector",
                "resource_estimate_policy": (
                    "no_fixed_per_symbol_increment;shared_service_total_cap_only"
                ),
                "estimated_shared_total_requests_per_minute": (
                    SHARED_COLLECTOR_REQUESTS_PER_MINUTE
                ),
                "estimated_shared_service_memory_cap_mb": (
                    SHARED_COLLECTOR_MEMORY_CAP_MB
                ),
                "research_collection_status": (
                    "active_shared_collector"
                    if code in active_research_watch_codes
                    else (
                        "active_inventory_unverified"
                        if active_inventory_issues
                        else "not_enrolled"
                    )
                ),
                "already_enrolled_research_watch": (
                    code in active_research_watch_codes
                ),
                "collector_created": False,
                "service_started": False,
            }
        )
    candidates.sort(
        key=lambda row: (
            row["implementation_review_ready"] is True,
            float(row["recommendation_score"]),
            int(row["sample_count"]),
            str(row["stock_code"]),
        ),
        reverse=True,
    )
    recommendations = candidates[:MAX_RECOMMENDATIONS]
    capacity_context = _collection_capacity_context(
        candidates=candidates,
        active_codes=active_research_watch_codes,
    )
    implementation_review_candidate_count = sum(
        row["implementation_review_ready"] is True for row in candidates
    )
    recommended_active_research_watch_count = sum(
        row["research_collection_status"] == "active_shared_collector"
        for row in recommendations
    )
    recommended_not_enrolled_count = sum(
        row["research_collection_status"] == "not_enrolled" for row in recommendations
    )
    return {
        "schema": "widget_collector_expansion_recommendation_v1",
        "status": (
            "recommendations_ready" if recommendations else "no_qualified_candidate"
        ),
        "target_date": target_date.isoformat(),
        "comparison_cost_contract": comparison_cost_contract(target_date),
        "generated_at": datetime.now(KST).isoformat(),
        "authority": AUTHORITY,
        "recommendations": recommendations,
        "qualified_candidate_count": len(candidates),
        "reported_candidate_count": len(recommendations),
        "qualified_beyond_report_limit_count": max(
            0, len(candidates) - MAX_RECOMMENDATIONS
        ),
        "research_watch_collection_capacity": MAX_ACTIVE_RESEARCH_WATCH_SYMBOLS,
        "research_watch_report_limit": MAX_RECOMMENDATIONS,
        **capacity_context,
        "research_watch_capacity_status": (
            "verified_active_candidate_union"
            if not active_inventory_issues
            else "active_inventory_unverified"
        ),
        "research_watch_overflow_action": (
            "operator_review_ranked_replacement_or_defer_no_silent_enrollment"
        ),
        "implementation_review_candidate_count": (
            implementation_review_candidate_count
        ),
        "recommended_active_research_watch_count": (
            recommended_active_research_watch_count
        ),
        "recommended_not_enrolled_count": recommended_not_enrolled_count,
        "research_watch_candidate_count": (
            len(candidates) - implementation_review_candidate_count
        ),
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "source": {
            "market_session_scope": "KRX_REGULAR_ONLY",
            "replay_paths": [str(path) for path in replay_paths],
            "current_replay_in_memory_target_date": (
                str(current_replay_report.get("target_date") or "")
                if isinstance(current_replay_report, dict)
                else None
            ),
            "feature_paths": feature_paths,
            "active_widget_codes": sorted(IMPLEMENTED_WIDGET_CODES),
            "manual_control_exclusion_applied": False,
            "active_research_watch_inventory_issues": list(active_inventory_issues),
        },
        "metric_contract": METRIC_CONTRACT,
        "implementation_review_contract": {
            "minimum_sample_count": IMPLEMENTATION_REVIEW_MIN_SAMPLES,
            "minimum_trading_date_count": (IMPLEMENTATION_REVIEW_MIN_TRADING_DATES),
            "maximum_median_spread_bp": (IMPLEMENTATION_REVIEW_MAX_MEDIAN_SPREAD_BP),
            "maximum_median_intraday_range_pct": (
                IMPLEMENTATION_REVIEW_MAX_MEDIAN_RANGE_PCT
            ),
            "decision_authority": AUTHORITY,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "recommendation_only": True,
        "collector_created": False,
        "service_started": False,
        "widget_runtime_effect": False,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "manual_control_exclusion_applied": False,
    }


def build_telegram_message(report: dict[str, Any]) -> str:
    lines = [
        "📋 [위젯 수집서비스 확대 후보]",
        f"기준일: {report.get('target_date')}",
        "권한: 추천 자체는 자동 생성/기동 권한 없음",
    ]
    recommendations = report.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        lines.append("오늘 기준을 통과한 신규 후보가 없습니다.")
        return "\n".join(lines)
    lines.append(
        "구현검토 "
        f"{report.get('implementation_review_candidate_count', 0)}개 · "
        "연구관찰 "
        f"{report.get('research_watch_candidate_count', 0)}개"
    )
    lines.append(
        "추천기록 상한 "
        f"{report.get('research_watch_report_limit', MAX_RECOMMENDATIONS)}개 · "
        "동시수집 상한 "
        f"{report.get('research_watch_collection_capacity', MAX_ACTIVE_RESEARCH_WATCH_SYMBOLS)}개 · "
        "교체/대기 검토 "
        f"{report.get('research_watch_overflow_candidate_count', 0)}개"
    )
    if report.get("research_watch_capacity_status") != (
        "verified_active_candidate_union"
    ):
        lines.append(
            "주의: 기존 활성 관찰목록 검증 실패로 초과 수 재확인이 필요합니다."
        )
    for index, row in enumerate(recommendations, start=1):
        lines.extend(
            [
                (
                    f"{index}. {row.get('stock_name')}({row.get('stock_code')}) "
                    f"점수 {row.get('recommendation_score')}"
                ),
                (
                    "   등급 "
                    f"{row.get('recommendation_tier')}, "
                    f"관측 {row.get('observed_trading_date_count')}일/"
                    f"{row.get('sample_count')}건"
                ),
                (
                    "   target/adverse "
                    f"{row.get('target_first_count')}/{row.get('adverse_first_count')}, "
                    f"EV {row.get('source_quality_adjusted_ev_pct')}%, "
                    f"유동성 {row.get('median_entry_liquidity_score')}, "
                    f"장중범위 {row.get('median_intraday_range_pct')}%, "
                    f"스프레드 {row.get('median_spread_bp')}bp"
                ),
                (
                    "   공유수집 총예산 ≤"
                    f"{row.get('estimated_shared_total_requests_per_minute', 15)} "
                    "req/min, 서비스 메모리 상한 "
                    f"{row.get('estimated_shared_service_memory_cap_mb', 256)}MB"
                ),
                (
                    "   수집상태: "
                    + {
                        "active_shared_collector": "기존 공동수집기 등록·축적 중",
                        "not_enrolled": "미등록·사용자 지시 필요",
                        "active_inventory_unverified": "활성 목록 검증 필요",
                    }.get(
                        str(row.get("research_collection_status") or ""),
                        "확인 필요",
                    )
                ),
            ]
        )
    if int(report.get("implementation_review_candidate_count") or 0) == 0:
        lines.append(
            "즉시 구현검토 후보는 없으며 연구관찰 후보는 표본을 더 축적합니다."
        )
    not_enrolled_count = int(report.get("recommended_not_enrolled_count") or 0)
    active_count = int(report.get("recommended_active_research_watch_count") or 0)
    if not_enrolled_count:
        lines.append(
            f"미등록 후보 {not_enrolled_count}개는 사용자 지시 전에 "
            "collector/service를 변경하거나 시작하지 않습니다."
        )
    elif active_count == len(recommendations):
        lines.append(
            "표시된 후보는 기존 공동수집기에 모두 등록되어 "
            "표본을 축적 중입니다. 이 추천 작업 자체는 서비스를 변경하지 않습니다."
        )
    else:
        lines.append("활성 관찰목록 검증 후 등록 여부를 재확인해야 합니다.")
    return "\n".join(lines)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _source_artifact_issues(
    *,
    target_date: date,
    payload_path: Path,
    label_path: Path,
) -> list[str]:
    issues: list[str] = []
    try:
        for _ in iter_jsonl_objects_strict(payload_path):
            pass
    except FileNotFoundError:
        issues.append("exact_payload_artifact_missing")
    except (OSError, ValueError):
        issues.append("exact_payload_artifact_invalid")
    try:
        label_report = read_json_object_strict(label_path)
    except (FileNotFoundError, OSError, ValueError):
        label_report = None
    if not isinstance(label_report, dict):
        issues.append("outcome_label_artifact_missing_or_invalid")
        return issues
    try:
        label_generated_at = datetime.fromisoformat(
            str(label_report.get("generated_at") or "")
        )
        if label_generated_at.tzinfo is None:
            raise ValueError
        label_generated_at = label_generated_at.astimezone(KST)
    except (TypeError, ValueError):
        label_generated_at = None
    earliest_complete_time = datetime.combine(
        target_date,
        NXT_AFTERMARKET_END,
        tzinfo=KST,
    )
    if (
        label_report.get("schema") != "ai_decision_outcome_labels_v1"
        or label_report.get("target_date") != target_date.isoformat()
        or label_report.get("status")
        not in {"mature_label_rows_available", "partial_horizons_keep_maturing"}
        or not isinstance(label_report.get("labels"), list)
        or label_generated_at is None
        or label_generated_at < earliest_complete_time
        or label_report.get("runtime_effect") is not False
        or label_report.get("allowed_runtime_apply") is not False
        or label_report.get("actual_order_submitted") is not False
        or label_report.get("broker_order_forbidden") is not True
    ):
        issues.append("outcome_label_contract_mismatch")
    return issues


def _wait_for_source_artifacts(
    *,
    target_date: date,
    payload_path: Path,
    label_path: Path,
    wait_sec: float,
    poll_sec: float,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[str]:
    """Wait boundedly for the postclose label producer to finish atomically."""

    wait_sec = max(0.0, float(wait_sec))
    poll_sec = max(0.1, float(poll_sec))
    deadline = monotonic() + wait_sec
    while True:
        issues = _source_artifact_issues(
            target_date=target_date,
            payload_path=payload_path,
            label_path=label_path,
        )
        if not issues or monotonic() >= deadline:
            return issues
        sleeper(min(poll_sec, max(0.0, deadline - monotonic())))


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


class WidgetExpansionRecommendationNotifier:
    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        enabled: bool | None = None,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.enabled = (
            str(os.getenv("KORSTOCKSCAN_WIDGET_EXPANSION_TELEGRAM_ENABLED", "true"))
            .strip()
            .lower()
            not in {"0", "false", "no", "off"}
            if enabled is None
            else bool(enabled)
        )

    def notify(self, report: dict[str, Any]) -> str:
        if not self.enabled:
            return "disabled"
        if (
            report.get("schema") != "widget_collector_expansion_recommendation_v1"
            or report.get("status")
            not in {"recommendations_ready", "no_qualified_candidate"}
            or report.get("metric_contract") != METRIC_CONTRACT
            or report.get("authority") != AUTHORITY
            or report.get("recommendation_only") is not True
            or report.get("widget_runtime_effect") is not False
            or report.get("trading_runtime_effect") is not False
            or report.get("runtime_effect") is not False
            or report.get("allowed_runtime_apply") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
            or report.get("collector_created") is not False
            or report.get("service_started") is not False
        ):
            return "invalid_report"
        target_date = str(report.get("target_date") or "")
        try:
            date.fromisoformat(target_date)
        except ValueError:
            return "invalid_report"
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if (
            isinstance(state, dict)
            and state.get("last_sent_target_date") == target_date
        ):
            return "duplicate"
        token, admin_id = self.config_loader()
        if not token or not admin_id:
            return "missing_config"
        try:
            self.sender(token, admin_id, build_telegram_message(report))
        except Exception:
            return "send_failed"
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_file.with_name(
                f".{self.state_file.name}.{os.getpid()}.tmp"
            )
            temporary.write_text(
                json.dumps(
                    {
                        "last_sent_target_date": target_date,
                        "authority": AUTHORITY,
                        "telegram_audience": "ADMIN_ONLY",
                        "runtime_effect": False,
                        "collector_created": False,
                        "service_started": False,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            os.replace(temporary, self.state_file)
        except OSError:
            return "sent_state_persist_failed"
        return "sent"


def _resolve_default_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) >= NXT_AFTERMARKET_END
    ):
        return current.date()
    return previous_krx_trading_date(current.date())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--payload-dir", type=Path, default=DEFAULT_PAYLOAD_DIR)
    parser.add_argument(
        "--label-dir", type=Path, default=mechanical_replay.DEFAULT_LABEL_DIR
    )
    parser.add_argument("--replay-dir", type=Path, default=DEFAULT_REPLAY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--source-wait-sec", type=float, default=0.0)
    parser.add_argument("--source-poll-sec", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else _resolve_default_target_date()
    )
    if not is_krx_trading_day(target_date):
        raise ValueError(
            f"widget_expansion_recommendation_requires_krx_trading_date:{target_date}"
        )
    payload_path = args.payload_dir / f"ai_decision_payloads_{target_date}.jsonl"
    label_path = args.label_dir / f"ai_decision_outcome_labels_{target_date}.json"
    source_issues = _wait_for_source_artifacts(
        target_date=target_date,
        payload_path=payload_path,
        label_path=label_path,
        wait_sec=args.source_wait_sec,
        poll_sec=args.source_poll_sec,
    )
    if source_issues:
        raise RuntimeError(
            "widget_expansion_source_not_ready:" + ",".join(source_issues)
        )
    replay_report = mechanical_replay.build_report_for_date(
        target_date,
        payload_dir=args.payload_dir,
        label_dir=args.label_dir,
    )
    if args.write:
        mechanical_replay.write_report(replay_report, output_dir=args.replay_dir)
    active_codes, active_inventory_issues = _load_active_research_watch_inventory(
        target_date=target_date
    )
    report = build_recommendation_report(
        target_date=target_date,
        replay_dir=args.replay_dir,
        payload_dir=args.payload_dir,
        current_replay_report=None if args.write else replay_report,
        active_research_watch_codes=active_codes,
        active_inventory_issues=tuple(active_inventory_issues),
    )
    report["telegram_status"] = "not_requested"
    output_path = args.output_dir / (
        f"widget_collector_expansion_recommendation_{target_date}.json"
    )
    if args.write:
        _atomic_write(output_path, report)
    if args.notify:
        report["telegram_status"] = WidgetExpansionRecommendationNotifier().notify(
            report
        )
        if args.write:
            _atomic_write(output_path, report)
        if report["telegram_status"] not in {
            "sent",
            "duplicate",
            "sent_state_persist_failed",
        }:
            raise RuntimeError(
                f"widget_expansion_telegram_not_delivered:{report['telegram_status']}"
            )
    if not args.write:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
