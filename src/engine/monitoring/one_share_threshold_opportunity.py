from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.ai.postclose_review_config import resolve_postclose_ai_review_config

PROJECT_ROOT = Path(__file__).resolve().parents[3]
KST = timezone(timedelta(hours=9))
CLEAN_BASELINE_DATE = "2026-06-05"
CLEAN_BASELINE_TS_KST = "2026-06-05T00:00:00+09:00"
REPORT_TYPE = "one_share_threshold_opportunity"
AI_REVIEW_SCHEMA_NAME = "one_share_threshold_opportunity_ai_review_v1"
AI_REVIEWER_NAME = "one_share_threshold_opportunity_ai_review"
FORCED_REASON = "rising_missed_one_share_entry"
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "buy_score_threshold_relaxation_without_preopen_apply",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "provider_route_change",
    "bot_restart",
    "forced_one_share_success_counting",
    "real_execution_quality_approval",
]
THRESHOLD_GROUPS = {
    "ai_score_near_buy": {
        "stages": {"blocked_ai_score", "ai_confirmed_terminal_no_budget"},
        "tokens": {"blocked_ai_score", "below_buy_score_threshold"},
        "hook_family": "entry_opportunity_recheck_runtime",
        "target_subsystem": "scalping_entry_ai_score_recheck",
    },
    "latency_or_freshness": {
        "stages": {"latency_block", "entry_submit_revalidation_block"},
        "tokens": {"latency", "stale", "quote_freshness", "stale_context_or_quote"},
        "hook_family": "latency_classifier_runtime_profile",
        "target_subsystem": "entry_latency_freshness_recheck",
    },
    "strength_momentum_vpw": {
        "stages": {
            "blocked_strength_momentum",
            "strength_momentum_stability_recheck_pending",
            "scanner_fast_precheck_stability_pending",
        },
        "tokens": {
            "insufficient_history",
            "below_strength",
            "below_buy_ratio",
            "below_window_buy_value",
            "vpw",
        },
        "hook_family": "entry_strength_momentum_recheck",
        "target_subsystem": "entry_strength_momentum_history_recheck",
    },
    "overbought_or_liquidity": {
        "stages": {
            "pre_submit_liquidity_guard_block",
            "pre_submit_overbought_pullback_guard_block",
            "scalp_sim_pre_submit_overbought_guard_would_block",
        },
        "tokens": {"overbought", "liquidity", "pullback"},
        "hook_family": "pre_submit_guard_attribution",
        "target_subsystem": "entry_pre_submit_guard_split",
    },
    "cooldown_or_hard_safety": {
        "stages": {
            "entry_cooldown_active",
            "scalp_same_symbol_loss_reentry_blocked",
            "blocked_zero_qty",
            "auth_zero_qty",
            "blocked_pause",
        },
        "tokens": {
            "cooldown",
            "broker",
            "account",
            "quantity",
            "zero_qty",
            "paused",
            "loss_reentry",
        },
        "hook_family": "hard_safety_observation_only",
        "target_subsystem": "entry_hard_safety_preserve",
    },
}


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    for line in _iter_jsonl_lines(path):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _iter_jsonl_lines(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            yield line


def _record_id_from_json_line(line: str) -> str:
    match = re.search(r'"record_id"\s*:\s*"?([^",}\s]+)', line)
    return match.group(1) if match else ""


def _date_from_path(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else ""


def _date_in_range(value: str, *, since_date: str, until_date: str) -> bool:
    return bool(value and since_date <= value <= until_date)


def _jsonl_paths(
    base: Path, prefix: str, *, since_date: str, until_date: str
) -> list[Path]:
    candidates = list(base.glob(f"{prefix}_*.jsonl")) + list(
        base.glob(f"{prefix}_*.jsonl.gz")
    )
    return sorted(
        path
        for path in candidates
        if _date_in_range(
            _date_from_path(path), since_date=since_date, until_date=until_date
        )
    )


def _pipeline_paths(*, since_date: str, until_date: str) -> list[Path]:
    base = PROJECT_ROOT / "data" / "pipeline_events"
    return _jsonl_paths(
        base, "pipeline_events", since_date=since_date, until_date=until_date
    )


def _post_sell_paths(*, since_date: str, until_date: str) -> list[Path]:
    base = PROJECT_ROOT / "data" / "post_sell"
    return _jsonl_paths(
        base, "post_sell_candidates", since_date=since_date, until_date=until_date
    )


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = PROJECT_ROOT / "data" / "report" / REPORT_TYPE
    return (
        base / f"{REPORT_TYPE}_{target_date}.json",
        base / f"{REPORT_TYPE}_{target_date}.md",
    )


def _is_forced_one_share(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return row.get("stage") == "rising_missed_one_share_entry" or _boolish(
        fields.get("rising_missed_one_share_entry_forced")
    )


def _clean_baseline_allowed(row: dict[str, Any], *, clean_baseline_ts_kst: str) -> bool:
    emitted_at = str(row.get("emitted_at") or "")
    if not emitted_at:
        return True
    row_date = emitted_at[:10]
    baseline_date = clean_baseline_ts_kst[:10]
    if row_date < baseline_date:
        return False
    if row_date > baseline_date:
        return True
    return emitted_at >= clean_baseline_ts_kst


def _event_record_id(row: dict[str, Any]) -> str:
    return str(row.get("record_id") or "").strip()


def _record_feature(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return {
        "record_id": _event_record_id(row),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "entry_time": row.get("emitted_at"),
        "entry_date": str(row.get("emitted_at") or "")[:10],
        "source_stage": row.get("stage"),
        "source_signature": fields.get("source_signature"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "ai_score": _safe_float(
            fields.get("ai_score")
            or fields.get("current_ai_score")
            or fields.get("entry_opportunity_recheck_ai_score")
        ),
        "entry_price": _safe_float(
            fields.get("rising_missed_one_share_entry_price")
            or fields.get("current_price")
            or fields.get("curr_price")
            or fields.get("curr")
        ),
        "actual_order_submitted_observed": _boolish(
            fields.get("actual_order_submitted")
        ),
        "entry_split_probe_first_applied_observed": _boolish(
            fields.get("entry_split_order_probe_first_applied")
            or fields.get("entry_split_probe_first_applied")
        ),
        "entry_split_probe_bundle_id": fields.get("entry_split_probe_bundle_id"),
        "entry_split_order_variant_id": fields.get("entry_split_order_variant_id"),
        "entry_split_probe_phase": fields.get("entry_split_probe_phase"),
        "entry_split_probe_abort_reason": fields.get("entry_split_probe_abort_reason"),
        "entry_split_probe_terminal_outcome": (
            fields.get("entry_split_probe_terminal_outcome")
            or fields.get("prior_probe_residual_outcome")
        ),
    }


def _merge_probe_split_provenance(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    if _boolish(fields.get("actual_order_submitted")) or stage in {
        "order_bundle_submitted",
        "buy_order_filled",
        "buy_order_partial_filled",
    }:
        item["actual_order_submitted_observed"] = True
    if _boolish(
        fields.get("entry_split_order_probe_first_applied")
        or fields.get("entry_split_probe_first_applied")
    ):
        item["entry_split_probe_first_applied_observed"] = True
    for key, aliases in (
        (
            "entry_split_probe_bundle_id",
            ("entry_split_probe_bundle_id", "prior_probe_residual_bundle_id"),
        ),
        ("entry_split_order_variant_id", ("entry_split_order_variant_id",)),
        ("entry_split_probe_phase", ("entry_split_probe_phase",)),
        (
            "entry_split_probe_abort_reason",
            (
                "entry_split_probe_abort_reason",
                "entry_split_probe_terminal_abort_reason",
                "prior_probe_residual_abort_reason",
            ),
        ),
        (
            "entry_split_probe_terminal_outcome",
            (
                "entry_split_probe_terminal_outcome",
                "prior_probe_residual_outcome",
            ),
        ),
        (
            "entry_split_probe_terminal_abort_detail_reason",
            (
                "entry_split_probe_terminal_abort_detail_reason",
                "residual_revalidation_timeout_cause",
            ),
        ),
        (
            "entry_split_probe_terminal_failure_signature",
            (
                "entry_split_probe_terminal_failure_signature",
                "prior_probe_residual_failure_signature",
            ),
        ),
    ):
        value = next(
            (
                fields.get(alias)
                for alias in aliases
                if fields.get(alias) not in (None, "", "-")
            ),
            None,
        )
        if value not in (None, "", "-"):
            item[key] = value
    if stage == "residual_submitted":
        item["entry_split_residual_submitted_observed"] = True
    elif stage == "residual_blocked":
        item["entry_split_residual_blocked_observed"] = True


def _residual_not_submitted_source(row: dict[str, Any]) -> str:
    if (
        str(row.get("entry_split_probe_terminal_outcome") or "").strip()
        == "residual_not_submitted"
    ):
        return "explicit_terminal_outcome"
    if (
        row.get("entry_split_residual_blocked_observed") is True
        and row.get("entry_split_residual_submitted_observed") is not True
        and str(row.get("entry_split_probe_phase") or "").strip() == "aborted"
    ):
        return "legacy_aborted_phase_fallback"
    return ""


def _classify_threshold(row: dict[str, Any]) -> set[str]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    haystack = " ".join(
        str(value or "")
        for value in [
            stage,
            fields.get("reason"),
            fields.get("terminal_reason"),
            fields.get("block_reason"),
            fields.get("skip_reason"),
        ]
    ).lower()
    groups: set[str] = set()
    for group, spec in THRESHOLD_GROUPS.items():
        if stage in spec["stages"] or any(
            token in haystack for token in spec["tokens"]
        ):
            groups.add(group)
    return groups


def _build_forced_index(
    paths: Iterable[Path],
    *,
    clean_baseline_ts_kst: str = CLEAN_BASELINE_TS_KST,
) -> tuple[dict[str, dict[str, Any]], dict[str, Counter[str]], list[str]]:
    forced: dict[str, dict[str, Any]] = {}
    threshold_counts: dict[str, Counter[str]] = defaultdict(Counter)
    path_list = list(paths)
    source_paths: list[str] = [str(path) for path in path_list]
    for path in path_list:
        for line in _iter_jsonl_lines(path):
            if FORCED_REASON not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            if not _clean_baseline_allowed(
                row, clean_baseline_ts_kst=clean_baseline_ts_kst
            ):
                continue
            record_id = _event_record_id(row)
            if not record_id or not _is_forced_one_share(row):
                continue
            item = forced.setdefault(record_id, _record_feature(row))
            item["forced_event_count"] = int(item.get("forced_event_count") or 0) + 1
            if row.get("stage") == "rising_missed_one_share_entry":
                item.update(_record_feature(row))
            _merge_probe_split_provenance(item, row)
    if not forced:
        return forced, threshold_counts, source_paths
    forced_ids = set(forced)
    for path in path_list:
        for line in _iter_jsonl_lines(path):
            record_id = _record_id_from_json_line(line)
            if record_id not in forced_ids:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            if not _clean_baseline_allowed(
                row, clean_baseline_ts_kst=clean_baseline_ts_kst
            ):
                continue
            _merge_probe_split_provenance(forced[record_id], row)
            for group in _classify_threshold(row):
                threshold_counts[record_id][group] += 1
    return forced, threshold_counts, source_paths


def _source_coverage_manifest(
    *,
    pipeline_paths: list[Path],
    post_sell_paths: list[Path],
    since_date: str,
    until_date: str,
    expected_post_sell_dates: Iterable[str] | None = None,
) -> dict[str, Any]:
    pipeline_dates = sorted(
        {_date_from_path(path) for path in pipeline_paths if _date_from_path(path)}
    )
    post_sell_dates = sorted(
        {_date_from_path(path) for path in post_sell_paths if _date_from_path(path)}
    )
    observed_dates = sorted(set(pipeline_dates) | set(post_sell_dates))
    missing_pipeline_dates = [
        value for value in observed_dates if value not in set(pipeline_dates)
    ]
    expected_post_sell = sorted(
        {
            str(value)
            for value in (expected_post_sell_dates or [])
            if _date_in_range(str(value), since_date=since_date, until_date=until_date)
        }
    )
    missing_post_sell_dates = [
        value for value in expected_post_sell if value not in set(post_sell_dates)
    ]
    gap_count = len(missing_pipeline_dates) + len(missing_post_sell_dates)
    return {
        "status": "pass" if gap_count == 0 else "source_coverage_gap",
        "since_date": since_date,
        "until_date": until_date,
        "clean_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
        "observed_dates": observed_dates,
        "pipeline_event_dates": pipeline_dates,
        "post_sell_dates": post_sell_dates,
        "expected_post_sell_dates": expected_post_sell,
        "post_sell_not_expected_pipeline_dates": sorted(
            set(pipeline_dates) - set(expected_post_sell)
        ),
        "missing_pipeline_event_dates": missing_pipeline_dates,
        "missing_post_sell_dates": missing_post_sell_dates,
        "gap_count": gap_count,
        "pipeline_path_count": len(pipeline_paths),
        "pipeline_gzip_path_count": sum(
            1 for path in pipeline_paths if path.suffix == ".gz"
        ),
        "post_sell_path_count": len(post_sell_paths),
        "post_sell_gzip_path_count": sum(
            1 for path in post_sell_paths if path.suffix == ".gz"
        ),
        "fail_closed_on_gap": True,
    }


def _load_post_sell(
    paths: Iterable[Path],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    by_record: dict[str, dict[str, Any]] = {}
    source_paths: list[str] = []
    for path in paths:
        source_paths.append(str(path))
        for row in _iter_jsonl(path):
            record_id = str(
                row.get("recommendation_id") or row.get("record_id") or ""
            ).strip()
            if not record_id:
                continue
            profit = _safe_float(row.get("profit_rate"))
            by_record[record_id] = {
                "sell_time": row.get("sell_time"),
                "profit_rate": profit,
                "peak_profit": _safe_float(row.get("peak_profit")),
                "held_sec": _safe_float(row.get("held_sec")),
                "exit_rule": row.get("exit_rule"),
                "stock_code": row.get("stock_code"),
                "stock_name": row.get("stock_name"),
            }
    return by_record, source_paths


def _joined_rows(
    forced: dict[str, dict[str, Any]],
    threshold_counts: dict[str, Counter[str]],
    post_sell_by_record: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record_id, entry in forced.items():
        outcome = post_sell_by_record.get(record_id) or {}
        groups = sorted(threshold_counts.get(record_id, Counter()))
        profit = outcome.get("profit_rate")
        rows.append(
            {
                **entry,
                "record_id": record_id,
                "threshold_groups": groups,
                "threshold_group_counts": dict(
                    threshold_counts.get(record_id, Counter())
                ),
                "post_sell_joined": bool(outcome),
                "profit_rate": profit,
                "peak_profit": outcome.get("peak_profit"),
                "held_sec": outcome.get("held_sec"),
                "exit_rule": outcome.get("exit_rule"),
                "profitable": bool(profit is not None and profit > 0),
            }
        )
    return rows


def _profit_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profits = [row["profit_rate"] for row in rows if row.get("profit_rate") is not None]
    winners = [value for value in profits if value > 0]
    losses = [value for value in profits if value <= 0]
    return {
        "sample": len(rows),
        "valid_profit_sample": len(profits),
        "profitable_count": len(winners),
        "loss_or_flat_count": len(losses),
        "equal_weight_avg_profit_pct": (
            round(sum(profits) / len(profits), 6) if profits else None
        ),
        "min_profit_pct": min(profits) if profits else None,
        "max_profit_pct": max(profits) if profits else None,
    }


def _threshold_opportunities(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    joined = [row for row in rows if row.get("post_sell_joined")]
    for group, spec in THRESHOLD_GROUPS.items():
        group_rows = [
            row for row in joined if group in set(row.get("threshold_groups") or [])
        ]
        if not group_rows:
            continue
        summary = _profit_summary(group_rows)
        opportunities.append(
            {
                "candidate_id": f"one_share_threshold_{group}",
                "threshold_group": group,
                "mapped_family": spec["hook_family"],
                "target_subsystem": spec["target_subsystem"],
                "sample": summary["sample"],
                "valid_profit_sample": summary["valid_profit_sample"],
                "profitable_count": summary["profitable_count"],
                "loss_or_flat_count": summary["loss_or_flat_count"],
                "equal_weight_avg_profit_pct": summary["equal_weight_avg_profit_pct"],
                "primary_decision_metric": "equal_weight_avg_profit_pct",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
                "example_records": [
                    {
                        "record_id": row.get("record_id"),
                        "stock_code": row.get("stock_code"),
                        "stock_name": row.get("stock_name"),
                        "profit_rate": row.get("profit_rate"),
                        "threshold_groups": row.get("threshold_groups"),
                    }
                    for row in group_rows[:8]
                ],
            }
        )
    return sorted(
        opportunities,
        key=lambda item: (
            item.get("equal_weight_avg_profit_pct") is not None,
            item.get("equal_weight_avg_profit_pct") or -999,
            item.get("sample") or 0,
        ),
        reverse=True,
    )


def _build_code_orders(
    opportunities: list[dict[str, Any]], source_paths: dict[str, Any]
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for item in opportunities:
        sample = int(item.get("sample") or 0)
        valid_profit_sample = int(item.get("valid_profit_sample") or 0)
        avg = item.get("equal_weight_avg_profit_pct")
        if valid_profit_sample < 3 or avg is None or avg <= 0:
            continue
        group = str(item.get("threshold_group") or "")
        if group == "cooldown_or_hard_safety":
            continue
        priority = 1 if sample >= 10 and avg >= 0.2 else 2
        orders.append(
            {
                "order_id": f"order_{item['candidate_id']}_entry_hook_review",
                "candidate_id": item["candidate_id"],
                "title": f"one-share threshold opportunity entry hook review: {group}",
                "source_report_type": REPORT_TYPE,
                "lifecycle_stage": "entry",
                "target_subsystem": item.get("target_subsystem"),
                "route": "instrumentation_order",
                "mapped_family": item.get("mapped_family"),
                "threshold_family": item.get("mapped_family"),
                "improvement_type": "source_only_entry_hook_workorder",
                "confidence": (
                    "rolling_source_only" if sample >= 10 else "thin_source_only"
                ),
                "priority": priority,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "one_share_threshold_opportunity_audit",
                    "implemented_scope": "source-only threshold group audit and code-improvement order provenance",
                    "decision_authority": "source_only_threshold_opportunity_audit",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "requires_separate_runtime_apply_candidate": True,
                    "runtime_mutation_allowed": False,
                    "sample": sample,
                    "valid_profit_sample": valid_profit_sample,
                    "equal_weight_avg_profit_pct": avg,
                    "threshold_group": group,
                    "mapped_family": item.get("mapped_family"),
                    "primary_decision_metric": "equal_weight_avg_profit_pct",
                    "source_quality_gate": "record_id_joined_forced_one_share_event_to_post_sell_outcome",
                    "forbidden_uses": FORBIDDEN_USES,
                },
                "expected_ev_effect": (
                    "Use one-share forced-entry post-sell outcomes to improve bounded entry hook selection "
                    "without treating one-share PnL as standalone real-order approval evidence."
                ),
                "evidence": [
                    f"threshold_group={group}",
                    f"sample={sample}",
                    f"valid_profit_sample={valid_profit_sample}",
                    f"profitable_count={item.get('profitable_count')}",
                    f"loss_or_flat_count={item.get('loss_or_flat_count')}",
                    f"equal_weight_avg_profit_pct={avg}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "source_paths": [
                    path
                    for values in source_paths.values()
                    for path in (values if isinstance(values, list) else [values])
                ],
                "files_likely_touched": [
                    "src/engine/monitoring/one_share_threshold_opportunity.py",
                    "src/engine/scalping/entry_opportunity_recheck.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_entry_opportunity_recheck.py src/tests/test_build_code_improvement_workorder.py",
                    "source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return orders


def _parse_ai_review(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response in (None, ""):
        return "unavailable", {}, ["ai_review_response_missing"]
    try:
        payload = json.loads(str(raw_response))
    except json.JSONDecodeError as exc:
        return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    if not isinstance(payload, dict):
        return "parse_rejected", {}, ["ai_review_non_dict"]
    warnings: list[str] = []
    try:
        schema_version = int(payload.get("schema_version") or 0)
    except (TypeError, ValueError):
        schema_version = 0
    if schema_version != 1:
        warnings.append("ai_review_schema_version_invalid")
    if str(payload.get("reviewer") or "") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("candidate_reviews"), list):
        warnings.append("ai_review_candidate_reviews_missing")
    if not isinstance(payload.get("audit"), dict):
        warnings.append("ai_review_audit_missing")
    return ("parsed" if not warnings else "parse_rejected"), payload, warnings


def _ai_review_instructions() -> str:
    return (
        "You are one_share_threshold_opportunity_ai_review. Use English only. "
        "Return strict JSON matching one_share_threshold_opportunity_ai_review_v1. "
        "Review only source-only entry hook workorders. You cannot approve real orders, "
        "runtime threshold mutation, broker guard bypass, stale submit bypass, provider route changes, "
        "bot restarts, quantity/cap changes, or real execution quality approval. "
        "If evidence is thin or mixed, recommend keep_collecting or code_patch_required with concrete tests."
    )


def _ai_review_context(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": report.get("target_date"),
        "window": report.get("window"),
        "summary": report.get("summary"),
        "metric_contract": report.get("metric_contract"),
        "opportunities": report.get("threshold_opportunities"),
        "code_improvement_orders": report.get("code_improvement_orders"),
    }


def _call_ai_review(
    report: dict[str, Any], *, provider: str
) -> tuple[str, dict[str, Any]]:
    if provider in {"", "none", "off", "false", "0"}:
        return "", {
            "provider": provider or "none",
            "status": "disabled",
            "reason": "ai_provider_disabled",
        }
    from src.engine.ai.postclose_structured_review_provider import (
        call_postclose_structured_review,
    )

    config = resolve_postclose_ai_review_config(
        REPORT_TYPE,
        default_model="gpt-5.4-mini",
        default_reasoning_effort="medium",
        default_timeout_sec=180,
        env_prefix="KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI",
    )
    if provider:
        config = config.__class__(**{**config.__dict__, "primary_provider": provider})
    return call_postclose_structured_review(
        _ai_review_context(report),
        schema_name=AI_REVIEW_SCHEMA_NAME,
        instructions=_ai_review_instructions(),
        config=config,
        metadata={"endpoint_name": AI_REVIEWER_NAME, "report_type": REPORT_TYPE},
        ensure_ascii=True,
    )


def _apply_ai_review(report: dict[str, Any], *, provider: str) -> dict[str, Any]:
    raw, provider_status = _call_ai_review(report, provider=provider)
    status, payload, warnings = _parse_ai_review(raw)
    review_by_candidate = {
        str(item.get("candidate_id")): item
        for item in (payload.get("candidate_reviews") or [])
        if isinstance(item, dict)
    }
    for order in report.get("code_improvement_orders") or []:
        review = review_by_candidate.get(str(order.get("candidate_id")))
        if review:
            order["ai_review_status"] = status
            order["ai_recommended_disposition"] = review.get("recommended_disposition")
            order["ai_review_confidence"] = review.get("confidence")
            order["ai_review_reason"] = review.get("reason")
            order["ai_required_followup"] = review.get("required_followup") or []
        elif status == "parsed":
            order["ai_review_status"] = "unreviewed"
    report["ai_review"] = {
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "reviewer": AI_REVIEWER_NAME,
        "provider": provider,
        "status": status,
        "provider_status": provider_status,
        "warnings": warnings,
        "audit": payload.get("audit") if isinstance(payload.get("audit"), dict) else {},
        "codex_directives": (
            payload.get("codex_directives")
            if isinstance(payload.get("codex_directives"), list)
            else []
        ),
        "reviewed_candidate_count": len(review_by_candidate),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }
    report["summary"]["ai_review_status"] = status
    report["summary"]["ai_reviewed_candidate_count"] = len(review_by_candidate)
    return report


def build_report(
    target_date: str,
    *,
    since_date: str | None = None,
    pipeline_paths: list[Path] | None = None,
    post_sell_paths: list[Path] | None = None,
    generated_at: str | None = None,
    ai_provider: str = "none",
) -> dict[str, Any]:
    since_date = (
        since_date
        or os.getenv("KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_SINCE_DATE")
        or CLEAN_BASELINE_DATE
    )
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    if pipeline_paths is None:
        pipeline_paths = _pipeline_paths(since_date=since_date, until_date=target_date)
    if post_sell_paths is None:
        post_sell_paths = _post_sell_paths(
            since_date=since_date, until_date=target_date
        )
    forced, threshold_counts, pipeline_sources = _build_forced_index(pipeline_paths)
    expected_post_sell_dates = {
        str(item.get("entry_date") or "")
        for item in forced.values()
        if item.get("actual_order_submitted_observed")
    }
    coverage_manifest = _source_coverage_manifest(
        pipeline_paths=pipeline_paths,
        post_sell_paths=post_sell_paths,
        since_date=since_date,
        until_date=target_date,
        expected_post_sell_dates=expected_post_sell_dates,
    )
    post_sell_by_record, post_sell_sources = _load_post_sell(post_sell_paths)
    rows = _joined_rows(forced, threshold_counts, post_sell_by_record)
    joined = [row for row in rows if row.get("post_sell_joined")]
    opportunities = _threshold_opportunities(rows)
    source_paths = {
        "pipeline_events": pipeline_sources,
        "post_sell_candidates": post_sell_sources,
    }
    orders = (
        _build_code_orders(opportunities, source_paths)
        if coverage_manifest.get("status") == "pass"
        else []
    )
    threshold_group_counts = Counter(
        group for row in rows for group in row.get("threshold_groups") or []
    )
    submitted_rows = [row for row in rows if row.get("actual_order_submitted_observed")]
    probe_first_rows = [
        row for row in rows if row.get("entry_split_probe_first_applied_observed")
    ]
    variant_rows = [
        row
        for row in rows
        if str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    submitted_split_provenance_rows = [
        row
        for row in submitted_rows
        if str(row.get("entry_split_probe_bundle_id") or "").strip()
        or str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    probe_first_submitted_rows = [
        row
        for row in submitted_rows
        if row.get("entry_split_probe_first_applied_observed")
    ]
    probe_first_submit_with_provenance_rows = [
        row
        for row in probe_first_submitted_rows
        if str(row.get("entry_split_probe_bundle_id") or "").strip()
        or str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    probe_first_provenance_gap_count = len(probe_first_submitted_rows) - len(
        probe_first_submit_with_provenance_rows
    )
    residual_submitted_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if row.get("entry_split_residual_submitted_observed") is True
    ]
    residual_blocked_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if row.get("entry_split_residual_blocked_observed") is True
    ]
    residual_not_submitted_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if _residual_not_submitted_source(row)
    ]
    residual_not_submitted_source_counts = Counter(
        _residual_not_submitted_source(row) for row in residual_not_submitted_rows
    )
    residual_terminal_abort_reason_counts = Counter(
        str(row.get("entry_split_probe_abort_reason") or "unknown")
        for row in residual_not_submitted_rows
    )
    residual_terminal_abort_detail_reason_counts = Counter(
        str(row.get("entry_split_probe_terminal_abort_detail_reason") or "unknown")
        for row in residual_not_submitted_rows
    )
    residual_terminal_failure_signature_coverage_count = sum(
        1
        for row in residual_not_submitted_rows
        if str(row.get("entry_split_probe_terminal_failure_signature") or "").strip()
        not in {"", "-"}
    )
    resolved_probe_record_ids = {
        str(row.get("record_id") or "")
        for row in residual_submitted_rows + residual_not_submitted_rows
    }
    unresolved_probe_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if str(row.get("record_id") or "") not in resolved_probe_record_ids
    ]
    probe_to_residual_resolution_count = len(resolved_probe_record_ids)
    probe_to_residual_resolution_coverage_pct = (
        round(
            probe_to_residual_resolution_count
            / len(probe_first_submit_with_provenance_rows)
            * 100.0,
            4,
        )
        if probe_first_submit_with_provenance_rows
        else None
    )
    probe_to_residual_status = (
        "no_natural_sample"
        if not probe_first_submitted_rows
        else (
            "instrumentation_gap"
            if probe_first_provenance_gap_count > 0 or unresolved_probe_rows
            else "observed"
        )
    )
    probe_to_residual_by_entry_date: dict[str, dict[str, Any]] = {}
    probe_entry_dates = {
        str(row.get("entry_date") or "")
        for row in probe_first_submitted_rows
        if str(row.get("entry_date") or "")
    }
    probe_entry_dates.add(target_date)
    for entry_date in sorted(probe_entry_dates):
        date_submitted_rows = [
            row
            for row in probe_first_submitted_rows
            if str(row.get("entry_date") or "") == entry_date
        ]
        date_provenance_rows = [
            row
            for row in date_submitted_rows
            if str(row.get("entry_split_probe_bundle_id") or "").strip()
            or str(row.get("entry_split_order_variant_id") or "").strip()
        ]
        date_residual_submitted_rows = [
            row
            for row in date_provenance_rows
            if row.get("entry_split_residual_submitted_observed") is True
        ]
        date_residual_blocked_rows = [
            row
            for row in date_provenance_rows
            if row.get("entry_split_residual_blocked_observed") is True
        ]
        date_residual_not_submitted_rows = [
            row for row in date_provenance_rows if _residual_not_submitted_source(row)
        ]
        date_resolved_record_ids = {
            str(row.get("record_id") or "")
            for row in date_residual_submitted_rows + date_residual_not_submitted_rows
        }
        date_unresolved_count = sum(
            1
            for row in date_provenance_rows
            if str(row.get("record_id") or "") not in date_resolved_record_ids
        )
        date_provenance_gap_count = len(date_submitted_rows) - len(date_provenance_rows)
        date_status = (
            "no_natural_sample"
            if not date_submitted_rows
            else (
                "instrumentation_gap"
                if date_provenance_gap_count > 0 or date_unresolved_count > 0
                else "observed"
            )
        )
        probe_to_residual_by_entry_date[entry_date] = {
            "status": date_status,
            "probe_first_submitted_count": len(date_submitted_rows),
            "probe_first_submit_with_provenance_count": len(date_provenance_rows),
            "probe_first_submit_provenance_gap_count": (date_provenance_gap_count),
            "resolution_count": len(date_resolved_record_ids),
            "resolution_coverage_pct": (
                round(
                    len(date_resolved_record_ids) / len(date_provenance_rows) * 100.0,
                    4,
                )
                if date_provenance_rows
                else None
            ),
            "residual_submitted_record_count": len(date_residual_submitted_rows),
            "residual_blocked_record_count": len(date_residual_blocked_rows),
            "residual_not_submitted_record_count": len(
                date_residual_not_submitted_rows
            ),
            "residual_not_submitted_source_counts": dict(
                sorted(
                    Counter(
                        _residual_not_submitted_source(row)
                        for row in date_residual_not_submitted_rows
                    ).items()
                )
            ),
            "residual_terminal_abort_detail_reason_counts": dict(
                sorted(
                    Counter(
                        str(
                            row.get("entry_split_probe_terminal_abort_detail_reason")
                            or "unknown"
                        )
                        for row in date_residual_not_submitted_rows
                    ).items()
                )
            ),
            "unresolved_record_count": date_unresolved_count,
        }
    probe_split_attribution = {
        "status": (
            "no_natural_sample"
            if not rows
            else (
                "instrumentation_gap"
                if probe_first_provenance_gap_count > 0
                else "observed"
            )
        ),
        "intent_record_count": len(rows),
        "actual_submit_observed_count": len(submitted_rows),
        "probe_first_observed_count": len(probe_first_rows),
        "entry_split_variant_observed_count": len(variant_rows),
        "submitted_split_provenance_count": len(submitted_split_provenance_rows),
        "submitted_split_provenance_gap_count": (probe_first_provenance_gap_count),
        "probe_first_submitted_count": len(probe_first_submitted_rows),
        "probe_first_submit_with_provenance_count": len(
            probe_first_submit_with_provenance_rows
        ),
        "probe_to_residual_status": probe_to_residual_status,
        "probe_to_residual_resolution_count": (probe_to_residual_resolution_count),
        "probe_to_residual_resolution_coverage_pct": (
            probe_to_residual_resolution_coverage_pct
        ),
        "residual_submitted_record_count": len(residual_submitted_rows),
        "residual_blocked_record_count": len(residual_blocked_rows),
        "residual_not_submitted_record_count": len(residual_not_submitted_rows),
        "residual_not_submitted_source_counts": dict(
            sorted(residual_not_submitted_source_counts.items())
        ),
        "residual_terminal_abort_reason_counts": dict(
            sorted(residual_terminal_abort_reason_counts.items())
        ),
        "residual_terminal_abort_detail_reason_counts": dict(
            sorted(residual_terminal_abort_detail_reason_counts.items())
        ),
        "residual_terminal_failure_signature_coverage_count": (
            residual_terminal_failure_signature_coverage_count
        ),
        "probe_to_residual_unresolved_record_count": len(unresolved_probe_rows),
        "probe_to_residual_by_entry_date": probe_to_residual_by_entry_date,
        "target_date_probe_to_residual": probe_to_residual_by_entry_date[target_date],
        "legacy_or_non_split_submit_count": (
            len(submitted_rows) - len(probe_first_submitted_rows)
        ),
        "post_sell_joined_count": len(joined),
        "pending_or_unjoined_count": len(rows) - len(joined),
        "join_owner": "record_id_to_post_sell_recommendation_id",
        "execution_shape_owner": "entry_split_order_plan",
        "scale_in_owner": "scale_in_split_order_plan_avg_down_only",
        "probe_to_residual_contract": {
            "metric_role": "real_execution_quality_attribution",
            "decision_authority": "source_only_probe_residual_attribution",
            "window_policy": (
                "record_lineage_from_probe_submit_to_residual_terminal_event"
            ),
            "sample_floor": "one_probe_first_submit_with_split_provenance",
            "primary_decision_metric": ("probe_to_residual_resolution_coverage_pct"),
            "source_quality_gate": (
                "record_id_split_bundle_or_variant_and_terminal_event_or_"
                "legacy_aborted_phase_fallback"
            ),
            "forbidden_uses": FORBIDDEN_USES,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "decision_authority": "source_only_probe_split_attribution",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }
    report = {
        "schema_version": 2,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "window": {
            "since_date": since_date,
            "until_date": target_date,
            "clean_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
            "window_policy": "all_available_since_clean_baseline_or_configured_start",
            "baseline_row_filter": "pipeline rows before clean_baseline_ts_kst are excluded",
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "source_only_threshold_opportunity_audit",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "sim_probe_ev",
            "decision_authority": "source_only_threshold_opportunity_audit",
            "window_policy": "all_available_one_share_forced_events_since_configured_start",
            "sample_floor": "3_valid_profit_post_sell_rows_per_threshold_group_for_workorder",
            "primary_decision_metric": "equal_weight_avg_profit_pct",
            "source_quality_gate": "record_id_joined_forced_one_share_event_to_post_sell_outcome",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "source_paths": source_paths,
        "source_coverage_manifest": coverage_manifest,
        "probe_split_attribution": probe_split_attribution,
        "summary": {
            "forced_record_count": len(rows),
            "post_sell_joined_count": len(joined),
            "profitable_joined_count": sum(
                1 for row in joined if row.get("profitable")
            ),
            "loss_or_flat_joined_count": sum(
                1
                for row in joined
                if row.get("profit_rate") is not None and row.get("profit_rate") <= 0
            ),
            "threshold_group_counts": [
                {"threshold_group": key, "count": value}
                for key, value in threshold_group_counts.most_common()
            ],
            "threshold_opportunity_count": len(opportunities),
            "code_improvement_order_count": len(orders),
            "source_coverage_status": coverage_manifest.get("status"),
            "source_coverage_gap_count": coverage_manifest.get("gap_count"),
        },
        "profit_summary": _profit_summary(joined),
        "threshold_opportunities": opportunities,
        "joined_examples": joined[:30],
        "code_improvement_orders": orders,
    }
    return _apply_ai_review(report, provider=ai_provider)


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    probe_split = (
        report.get("probe_split_attribution")
        if isinstance(report.get("probe_split_attribution"), dict)
        else {}
    )
    lines = [
        f"# {report.get('target_date')} One Share Threshold Opportunity",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- window: {((report.get('window') or {}).get('since_date'))} -> {((report.get('window') or {}).get('until_date'))}",
        "- decision_authority: source_only_threshold_opportunity_audit",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        f"- ai_review_status: {(summary.get('ai_review_status') or '-')}",
        f"- source_coverage_status: {summary.get('source_coverage_status')}",
        f"- source_coverage_gap_count: {summary.get('source_coverage_gap_count')}",
        "",
        "## Summary",
        "",
        f"- forced_record_count: {summary.get('forced_record_count')}",
        f"- post_sell_joined_count: {summary.get('post_sell_joined_count')}",
        f"- profitable_joined_count: {summary.get('profitable_joined_count')}",
        f"- loss_or_flat_joined_count: {summary.get('loss_or_flat_joined_count')}",
        f"- threshold_opportunity_count: {summary.get('threshold_opportunity_count')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        f"- probe_split_attribution_status: {probe_split.get('status')}",
        f"- probe_intent_record_count: {probe_split.get('intent_record_count')}",
        f"- actual_submit_observed_count: {probe_split.get('actual_submit_observed_count')}",
        f"- submitted_split_provenance_gap_count: {probe_split.get('submitted_split_provenance_gap_count')}",
        f"- probe_to_residual_status: {probe_split.get('probe_to_residual_status')}",
        f"- probe_to_residual_resolution_count: {probe_split.get('probe_to_residual_resolution_count')}",
        f"- probe_to_residual_resolution_coverage_pct: {probe_split.get('probe_to_residual_resolution_coverage_pct')}",
        f"- residual_submitted_record_count: {probe_split.get('residual_submitted_record_count')}",
        f"- residual_blocked_record_count: {probe_split.get('residual_blocked_record_count')}",
        f"- residual_not_submitted_record_count: {probe_split.get('residual_not_submitted_record_count')}",
        f"- residual_not_submitted_source_counts: {json.dumps(probe_split.get('residual_not_submitted_source_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_abort_reason_counts: {json.dumps(probe_split.get('residual_terminal_abort_reason_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_abort_detail_reason_counts: {json.dumps(probe_split.get('residual_terminal_abort_detail_reason_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_failure_signature_coverage_count: {probe_split.get('residual_terminal_failure_signature_coverage_count')}",
        f"- probe_to_residual_unresolved_record_count: {probe_split.get('probe_to_residual_unresolved_record_count')}",
        f"- target_date_probe_to_residual: {json.dumps(probe_split.get('target_date_probe_to_residual') or {}, ensure_ascii=False, sort_keys=True)}",
        "",
        "## Opportunities",
        "",
    ]
    for item in report.get("threshold_opportunities") or []:
        lines.extend(
            [
                f"### {item.get('threshold_group')}",
                "",
                f"- candidate_id: {item.get('candidate_id')}",
                f"- mapped_family: {item.get('mapped_family')}",
                f"- sample: {item.get('sample')}",
                f"- valid_profit_sample: {item.get('valid_profit_sample')}",
                f"- equal_weight_avg_profit_pct: {item.get('equal_weight_avg_profit_pct')}",
                f"- profitable_count: {item.get('profitable_count')}",
                f"- loss_or_flat_count: {item.get('loss_or_flat_count')}",
                "",
            ]
        )
    lines.append("## Workorders")
    lines.append("")
    for order in report.get("code_improvement_orders") or []:
        lines.extend(
            [
                f"### {order.get('order_id')}",
                "",
                f"- mapped_family: {order.get('mapped_family')}",
                f"- runtime_effect: {str(order.get('runtime_effect')).lower()}",
                f"- allowed_runtime_apply: {str(order.get('allowed_runtime_apply')).lower()}",
                f"- ai_recommended_disposition: {order.get('ai_recommended_disposition') or '-'}",
                "- evidence:",
            ]
        )
        for item in order.get("evidence") or []:
            lines.append(f"  - {item}")
        lines.append("")
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build one-share threshold opportunity audit."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--since-date")
    parser.add_argument("--pipeline-path", action="append", type=Path)
    parser.add_argument("--post-sell-path", action="append", type=Path)
    parser.add_argument(
        "--ai-provider",
        default=os.getenv(
            "KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER", "none"
        ),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date,
        since_date=args.since_date,
        pipeline_paths=args.pipeline_path,
        post_sell_paths=args.post_sell_path,
        generated_at=args.generated_at,
        ai_provider=args.ai_provider,
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "output_json": str(output_json),
                    "output_md": str(output_md),
                    **report["summary"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
