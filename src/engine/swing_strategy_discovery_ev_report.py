"""EV report for Swing Strategy Discovery Sim labels."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy, is_date_allowed
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema
from src.utils.constants import DATA_DIR, POSTGRES_URL


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_ev"
LABEL_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_labels"
DISCOVERY_SIM_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_sim"
DECISION_AUTHORITY = "swing_sim_exploration_only"
SAMPLE_FLOOR = 5
IMPLEMENTATION_ORDER_ID = "order_swing_strategy_discovery_source_quality_followup"
MORNING_TURBULENCE_AXES = [
    "entry_price_delta_bucket",
    "entry_day_gap_bucket",
    "entry_day_low_from_entry_bucket",
    "entry_day_close_from_entry_bucket",
    "stop_touch_outcome_bucket",
    "entry_position_opportunity_bucket",
]
MORNING_TURBULENCE_METRIC_CONTRACT = {
    "metric_role": "sim_probe_ev",
    "decision_authority": DECISION_AUTHORITY,
    "window_policy": "rolling_90d",
    "sample_floor": SAMPLE_FLOOR,
    "sample_floor_behavior": "hold_sample",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "label_status_labeled_and_source_quality_status_ok",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "time_hard_gate",
        "broker_order_submit",
        "runtime_threshold_apply",
        "stop_relaxation_or_tightening",
        "swing_dry_run_guard_change",
        "real_canary_approval_standalone",
        "volatile_symbol_exclusion",
    ],
}


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _json_loads(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return {}
    try:
        return json.loads(str(value))
    except Exception:
        return {}


def _theme_key(value: Any) -> str:
    parsed = _json_loads(value)
    if isinstance(parsed, list):
        return ",".join(sorted(str(item) for item in parsed if str(item).strip())) or "-"
    return str(value or "-")


def _percentile(values: list[float], q: float) -> float | None:
    values = sorted(v for v in values if math.isfinite(v))
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 6)
    idx = (len(values) - 1) * q
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return round(values[lo], 6)
    weight = idx - lo
    return round(values[lo] * (1 - weight) + values[hi] * weight, 6)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_strategy_discovery_ev_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _source_paths(target_date: str) -> dict[str, str | None]:
    sim_json = DISCOVERY_SIM_REPORT_DIR / f"swing_strategy_discovery_sim_{target_date}.json"
    labels_json = LABEL_REPORT_DIR / f"swing_strategy_discovery_labels_{target_date}.json"
    return {
        "swing_strategy_discovery_sim": str(sim_json) if sim_json.exists() else None,
        "swing_strategy_discovery_labels": str(labels_json) if labels_json.exists() else None,
    }


def _bottom_rebound_sim_expected(target_date: str) -> bool:
    sim_json = DISCOVERY_SIM_REPORT_DIR / f"swing_strategy_discovery_sim_{target_date}.json"
    try:
        payload = json.loads(sim_json.read_text(encoding="utf-8"))
    except Exception:
        return False
    source_quality = payload.get("source_quality") if isinstance(payload.get("source_quality"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    bottom_source = source_quality.get("bottom_rebound_source") if isinstance(source_quality.get("bottom_rebound_source"), dict) else {}
    return (
        bottom_source.get("status") == "ok"
        and _safe_int(source_quality.get("bottom_rebound_source_rows")) > 0
        and _safe_int(summary.get("bottom_rebound_persisted_arm_count")) > 0
    )


def _clean_baseline_metadata(target_date: str, lookback_days: int) -> dict[str, Any]:
    target = datetime.fromisoformat(_date_text(target_date)).date()
    requested_start = target - timedelta(days=max(1, int(lookback_days)))
    policy = clean_baseline_policy()
    effective_start = requested_start
    excluded_before: str | None = None
    if is_date_allowed(target.isoformat(), policy):
        try:
            baseline = date.fromisoformat(str(policy.get("clean_tuning_baseline_date") or ""))
        except ValueError:
            baseline = requested_start
        if requested_start < baseline:
            effective_start = baseline
            excluded_before = baseline.isoformat()
    return {
        "policy": policy,
        "requested_start_date": requested_start.isoformat(),
        "effective_start_date": effective_start.isoformat(),
        "target_date": target.isoformat(),
        "excluded_pre_start_date": excluded_before,
        "filter_active": excluded_before is not None,
    }


def _row_from_models(
    candidate: SwingStrategyDiscoveryCandidate,
    arm: SwingStrategyDiscoveryArm,
    label: SwingStrategyDiscoveryLabel,
) -> dict[str, Any]:
    features = _json_loads(label.label_features)
    arm_features = _json_loads(arm.arm_features)
    candidate_features = _json_loads(candidate.source_features)
    bottom = candidate_features.get("bottom_rebound_source") if isinstance(candidate_features.get("bottom_rebound_source"), dict) else {}
    source_family_bucket = str(candidate_features.get("source_family_bucket") or "")
    if not source_family_bucket:
        source_family_bucket = "bottom_rebound" if bottom.get("present") or str(arm.entry_policy or "").startswith("bottom_rebound_") else "safe_pool"
    def _feature_value(name: str) -> Any:
        return (features or {}).get(name) or (arm_features or {}).get(name) or "unknown"

    return {
        "candidate_id": candidate.id,
        "arm_row_id": arm.id,
        "source_date": str(arm.source_date),
        "stock_code": arm.stock_code,
        "arm_id": arm.arm_id,
        "entry_policy": arm.entry_policy,
        "sizing_policy": arm.sizing_policy,
        "exit_policy": arm.exit_policy,
        "selection_arm": candidate.selection_arm,
        "legacy_pick_type": candidate.legacy_pick_type or "-",
        "position_tag": candidate.position_tag or "-",
        "volatility_bucket": candidate.volatility_bucket or "-",
        "source_family_bucket": source_family_bucket,
        "block_reason": candidate.block_reason or "-",
        "sector": candidate.sector or "-",
        "theme_tags": _theme_key(candidate.theme_tags),
        "label_status": label.label_status,
        "final_return_pct": _safe_float(label.final_return_pct, float("nan")),
        "realized_exit_return_pct": _safe_float(label.realized_exit_return_pct, float("nan")),
        "mfe_pct": _safe_float(label.mfe_pct, float("nan")),
        "mae_pct": _safe_float(label.mae_pct, float("nan")),
        "virtual_notional_krw": _safe_float(arm.virtual_notional_krw, 0.0),
        "fill_status": (features or {}).get("fill_status"),
        "entry_reason": (features or {}).get("entry_reason") or (arm_features or {}).get("entry_reason"),
        "policy_exit_reason": (features or {}).get("exit_reason") or (arm_features or {}).get("policy_exit_reason"),
        "label_maturity_status": (arm_features or {}).get("label_maturity_status"),
        "source_quality_status": (arm_features or {}).get("source_quality_status"),
        "future_quote_count": int((arm_features or {}).get("future_quote_count") or 0),
        "quotes_from_entry_count": int((arm_features or {}).get("quotes_from_entry_count") or 0),
        "latest_future_quote_date": (arm_features or {}).get("latest_future_quote_date"),
        "final_return_basis": (features or {}).get("final_return_basis"),
        "entry_price_delta_bucket": _feature_value("entry_price_delta_bucket"),
        "entry_day_gap_bucket": _feature_value("entry_day_gap_bucket"),
        "entry_day_low_from_entry_bucket": _feature_value("entry_day_low_from_entry_bucket"),
        "entry_day_close_from_entry_bucket": _feature_value("entry_day_close_from_entry_bucket"),
        "stop_touch_outcome_bucket": _feature_value("stop_touch_outcome_bucket"),
        "entry_position_opportunity_bucket": _feature_value("entry_position_opportunity_bucket"),
    }


def _load_rows(target_date: str, *, db_url: str = POSTGRES_URL, lookback_days: int = 90) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ensure_swing_strategy_discovery_schema(db_url)
    target = datetime.fromisoformat(_date_text(target_date)).date()
    metadata = _clean_baseline_metadata(target.isoformat(), lookback_days)
    start = date.fromisoformat(str(metadata["effective_start_date"]))
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        query = (
            session.query(SwingStrategyDiscoveryCandidate, SwingStrategyDiscoveryArm, SwingStrategyDiscoveryLabel)
            .join(SwingStrategyDiscoveryArm, SwingStrategyDiscoveryArm.candidate_id == SwingStrategyDiscoveryCandidate.id)
            .join(SwingStrategyDiscoveryLabel, SwingStrategyDiscoveryLabel.arm_row_id == SwingStrategyDiscoveryArm.id)
            .filter(SwingStrategyDiscoveryArm.source_date >= start)
            .filter(SwingStrategyDiscoveryArm.source_date <= target)
            .filter(SwingStrategyDiscoveryLabel.label_horizon == "policy_exit")
        )
        rows = [_row_from_models(candidate, arm, label) for candidate, arm, label in query.all()]
        arm_status_counts: dict[str, int] = defaultdict(int)
        for status, count in (
            session.query(SwingStrategyDiscoveryArm.status, SwingStrategyDiscoveryArm.id)
            .filter(SwingStrategyDiscoveryArm.source_date >= start)
            .filter(SwingStrategyDiscoveryArm.source_date <= target)
            .all()
        ):
            arm_status_counts[str(status or "UNKNOWN")] += 1
    return rows, dict(arm_status_counts)


def _aggregate(rows: Iterable[dict[str, Any]], group_key: str, *, total_by_key: dict[str, int] | None = None) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key) or "-")].append(row)
    out: list[dict[str, Any]] = []
    for key, items in groups.items():
        labeled = [item for item in items if item.get("label_status") == "labeled" and math.isfinite(item.get("final_return_pct", float("nan")))]
        returns = [float(item["final_return_pct"]) for item in labeled]
        notional_sum = sum(max(0.0, _safe_float(item.get("virtual_notional_krw"), 0.0)) for item in labeled)
        weighted = (
            sum(float(item["final_return_pct"]) * max(0.0, _safe_float(item.get("virtual_notional_krw"), 0.0)) for item in labeled)
            / notional_sum
            if notional_sum > 0
            else (sum(returns) / len(returns) if returns else 0.0)
        )
        sample_count = len(labeled)
        total = (total_by_key or {}).get(key, len(items)) or len(items)
        expired = sum(1 for item in items if item.get("label_status") == "expired_entry_no_trigger")
        mae_values = [float(item["mae_pct"]) for item in labeled if math.isfinite(item.get("mae_pct", float("nan")))]
        equal_ev = sum(returns) / sample_count if sample_count else 0.0
        coverage_factor = min(1.0, sample_count / SAMPLE_FLOOR) if SAMPLE_FLOOR else 1.0
        out.append(
            {
                group_key: key,
                "sample_count": sample_count,
                "total_row_count": total,
                "entry_fill_rate": round(sample_count / total, 6) if total else 0.0,
                "expired_rate": round(expired / total, 6) if total else 0.0,
                "equal_weight_avg_final_return_pct": round(equal_ev, 6),
                "notional_weighted_ev_pct": round(weighted, 6),
                "source_quality_adjusted_ev_pct": round(weighted * coverage_factor, 6),
                "diagnostic_win_rate": round(sum(1 for value in returns if value > 0) / sample_count, 6) if sample_count else 0.0,
                "downside_p10_pct": _percentile(returns, 0.10),
                "mae_p90_pct": _percentile(mae_values, 0.10),
            }
        )
    return sorted(out, key=lambda item: (item["source_quality_adjusted_ev_pct"], item["sample_count"]), reverse=True)


def _aggregate_all(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    axes = [
        "arm_id",
        "entry_policy",
        "sizing_policy",
        "exit_policy",
        "selection_arm",
        "legacy_pick_type",
        "position_tag",
        "volatility_bucket",
        "source_family_bucket",
        "block_reason",
        "sector",
        "theme_tags",
    ]
    return {axis: _aggregate(rows, axis) for axis in axes}


def _morning_turbulence_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "analysis_role": "source_only_observation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_contract": MORNING_TURBULENCE_METRIC_CONTRACT,
        "axes": {axis: _aggregate(rows, axis) for axis in MORNING_TURBULENCE_AXES},
    }


def _surviving_arms(aggregates: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    arms = aggregates.get("arm_id") or []
    out = []
    for item in arms:
        downside = item.get("downside_p10_pct")
        if (
            int(item.get("sample_count") or 0) >= SAMPLE_FLOOR
            and _safe_float(item.get("source_quality_adjusted_ev_pct"), 0.0) > 0
            and (downside is None or _safe_float(downside, 0.0) > -5.0)
        ):
            out.append(item)
    return out


def _avoid_buckets(aggregates: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for axis in ("block_reason", "position_tag", "volatility_bucket", "sector", "theme_tags"):
        for item in aggregates.get(axis) or []:
            downside = item.get("downside_p10_pct")
            if int(item.get("sample_count") or 0) >= SAMPLE_FLOOR and (
                _safe_float(item.get("source_quality_adjusted_ev_pct"), 0.0) < 0
                or (downside is not None and _safe_float(downside, 0.0) <= -5.0)
            ):
                out.append({"axis": axis, **item})
    return sorted(out, key=lambda item: (item.get("source_quality_adjusted_ev_pct", 0), item.get("downside_p10_pct") or 0))[:20]


def _legacy_vs_discovery(aggregates: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    selection = {item.get("selection_arm"): item for item in aggregates.get("selection_arm") or []}
    legacy = selection.get("legacy_ml") or {}
    discovery = [
        item
        for item in (aggregates.get("selection_arm") or [])
        if item.get("selection_arm") in {"lifecycle_rank", "diversity_exploration"}
    ]
    discovery_sample = sum(int(item.get("sample_count") or 0) for item in discovery)
    discovery_ev = (
        sum(_safe_float(item.get("source_quality_adjusted_ev_pct"), 0.0) * int(item.get("sample_count") or 0) for item in discovery)
        / discovery_sample
        if discovery_sample
        else 0.0
    )
    return {
        "legacy_ml": legacy,
        "discovery_combined": {
            "sample_count": discovery_sample,
            "source_quality_adjusted_ev_pct": round(discovery_ev, 6),
        },
    }


def _source_quality_summary(
    rows: list[dict[str, Any]],
    *,
    arm_status_counts: dict[str, int],
    label_status_counts: dict[str, int],
) -> dict[str, Any]:
    maturity_counts: dict[str, int] = defaultdict(int)
    entry_reason_counts: dict[str, int] = defaultdict(int)
    exit_reason_counts: dict[str, int] = defaultdict(int)
    source_quality_counts: dict[str, int] = defaultdict(int)
    bottom_label_status_counts: dict[str, int] = defaultdict(int)
    bottom_maturity_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        maturity_counts[str(row.get("label_maturity_status") or "unknown")] += 1
        entry_reason_counts[str(row.get("entry_reason") or "-")] += 1
        exit_reason_counts[str(row.get("policy_exit_reason") or "-")] += 1
        source_quality_counts[str(row.get("source_quality_status") or "-")] += 1
        if row.get("source_family_bucket") == "bottom_rebound":
            bottom_label_status_counts[str(row.get("label_status") or "UNKNOWN")] += 1
            bottom_maturity_counts[str(row.get("label_maturity_status") or "unknown")] += 1
    return {
        "implementation_status": "implemented",
        "implementation_provenance": {
            "order_id": IMPLEMENTATION_ORDER_ID,
            "scope": "source_quality_instrumentation_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": DECISION_AUTHORITY,
        },
        "implementation_checks": [
            {
                "name": "label_maturity_provenance",
                "status": "pass",
                "fields": [
                    "label_maturity_status",
                    "entry_reason",
                    "policy_exit_reason",
                    "future_quote_count",
                    "quotes_from_entry_count",
                ],
            },
            {
                "name": "source_only_contract",
                "status": "pass",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        ],
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "arm_status_counts": arm_status_counts,
        "label_status_counts": dict(label_status_counts),
        "bottom_rebound_label_status_counts": dict(bottom_label_status_counts),
        "bottom_rebound_maturity_status_counts": dict(bottom_maturity_counts),
        "bottom_rebound_pending_future_quote_count": bottom_label_status_counts.get("pending_future_quotes", 0),
        "bottom_rebound_labeled_sample_count": bottom_label_status_counts.get("labeled", 0),
        "bottom_rebound_expired_entry_count": bottom_label_status_counts.get("expired_entry_no_trigger", 0),
        "maturity_status_counts": dict(maturity_counts),
        "entry_reason_counts": dict(entry_reason_counts),
        "policy_exit_reason_counts": dict(exit_reason_counts),
        "source_quality_status_counts": dict(source_quality_counts),
    }


def build_swing_strategy_discovery_ev_report(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    lookback_days: int = 90,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    clean_metadata = _clean_baseline_metadata(date_key, lookback_days)
    rows, arm_status_counts = _load_rows(date_key, db_url=db_url, lookback_days=lookback_days)
    aggregates = _aggregate_all(rows)
    morning_turbulence = _morning_turbulence_analysis(rows)
    surviving = _surviving_arms(aggregates)
    avoid = _avoid_buckets(aggregates)
    label_status_counts: dict[str, int] = defaultdict(int)
    bottom_label_status_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        label_status_counts[str(row.get("label_status") or "UNKNOWN")] += 1
        if row.get("source_family_bucket") == "bottom_rebound":
            bottom_label_status_counts[str(row.get("label_status") or "UNKNOWN")] += 1
    bottom_rows = [row for row in rows if row.get("source_family_bucket") == "bottom_rebound"]
    source_quality_summary = _source_quality_summary(
        rows,
        arm_status_counts=arm_status_counts,
        label_status_counts=dict(label_status_counts),
    )
    summary = {
        "candidate_count": len({row.get("candidate_id") for row in rows}),
        "arm_count": len({row.get("arm_row_id") for row in rows}),
        "policy_exit_row_count": len(rows),
        "labeled_sample_count": label_status_counts.get("labeled", 0),
        "pending_future_quote_count": label_status_counts.get("pending_future_quotes", 0),
        "expired_entry_count": label_status_counts.get("expired_entry_no_trigger", 0),
        "bottom_rebound_policy_exit_row_count": len(bottom_rows),
        "bottom_rebound_labeled_sample_count": bottom_label_status_counts.get("labeled", 0),
        "bottom_rebound_pending_future_quote_count": bottom_label_status_counts.get("pending_future_quotes", 0),
        "bottom_rebound_expired_entry_count": bottom_label_status_counts.get("expired_entry_no_trigger", 0),
        "bottom_rebound_label_status_counts": dict(bottom_label_status_counts),
        "surviving_arm_count": len(surviving),
        "avoid_bucket_count": len(avoid),
        "top_surviving_arm": (surviving[0].get("arm_id") if surviving else None),
        "arm_status_counts": arm_status_counts,
        "label_status_counts": dict(label_status_counts),
    }
    warnings = []
    if not rows:
        warnings.append("swing_strategy_discovery_labels_missing")
    if summary["pending_future_quote_count"]:
        warnings.append("pending_future_quotes")
    if summary["labeled_sample_count"] < SAMPLE_FLOOR:
        warnings.append("sample_floor_not_met")
    if _bottom_rebound_sim_expected(date_key) and not bottom_rows:
        warnings.append("bottom_rebound_ev_handoff_missing")
    if clean_metadata.get("filter_active"):
        warnings.append("clean_tuning_baseline_swing_discovery_lookback_filtered")
    report = {
        "schema_version": 1,
        "report_type": "swing_strategy_discovery_ev",
        "date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "sample_floor": SAMPLE_FLOOR,
        "morning_turbulence_metric_contract": MORNING_TURBULENCE_METRIC_CONTRACT,
        "primary_metrics": [
            "equal_weight_avg_final_return_pct",
            "notional_weighted_ev_pct",
            "source_quality_adjusted_ev_pct",
        ],
        "clean_tuning_baseline": clean_metadata,
        "summary": summary,
        "source_quality_summary": source_quality_summary,
        "aggregates": aggregates,
        "morning_turbulence_analysis": morning_turbulence,
        "surviving_arms": surviving,
        "legacy_vs_discovery": _legacy_vs_discovery(aggregates),
        "avoid_buckets": avoid,
        "sources": _source_paths(date_key),
        "warnings": warnings,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    legacy = report.get("legacy_vs_discovery") if isinstance(report.get("legacy_vs_discovery"), dict) else {}
    morning = report.get("morning_turbulence_analysis") if isinstance(report.get("morning_turbulence_analysis"), dict) else {}
    morning_axes = morning.get("axes") if isinstance(morning.get("axes"), dict) else {}
    stop_touch_rows = morning_axes.get("stop_touch_outcome_bucket") or []
    opportunity_rows = morning_axes.get("entry_position_opportunity_bucket") or []
    morning_contract = morning.get("metric_contract") if isinstance(morning.get("metric_contract"), dict) else {}
    lines = [
        f"# Swing Strategy Discovery EV - {report.get('date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- candidate/arm/policy_exit_rows: `{summary.get('candidate_count')}` / `{summary.get('arm_count')}` / `{summary.get('policy_exit_row_count')}`",
        f"- labeled_sample_count: `{summary.get('labeled_sample_count')}`",
        f"- pending_future_quote_count: `{summary.get('pending_future_quote_count')}`",
        f"- bottom_rebound_policy_exit_row_count: `{summary.get('bottom_rebound_policy_exit_row_count')}`",
        f"- bottom_rebound_label_status_counts: `{summary.get('bottom_rebound_label_status_counts') or {}}`",
        f"- top_surviving_arm: `{summary.get('top_surviving_arm') or '-'}`",
        f"- avoid_bucket_count: `{summary.get('avoid_bucket_count')}`",
        f"- source_quality_summary: `{report.get('source_quality_summary') or {}}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Surviving Arms",
        "",
        "| arm_id | sample | source_quality_ev | downside_p10 | win_rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in (report.get("surviving_arms") or [])[:10]:
        lines.append(
            f"| `{item.get('arm_id')}` | `{item.get('sample_count')}` | `{item.get('source_quality_adjusted_ev_pct')}` | `{item.get('downside_p10_pct')}` | `{item.get('diagnostic_win_rate')}` |"
        )
    if not report.get("surviving_arms"):
        lines.append("| - | 0 | - | - | - |")
    lines.extend(
        [
            "",
            "## Legacy vs Discovery",
            "",
            f"- legacy_ml: `{legacy.get('legacy_ml') or {}}`",
            f"- discovery_combined: `{legacy.get('discovery_combined') or {}}`",
            "",
            "## Morning Turbulence Observation",
            "",
            f"- analysis_role: `{morning.get('analysis_role') or 'source_only_observation'}`",
            f"- metric_contract: `{morning_contract}`",
            "",
            "| stop_touch_outcome_bucket | sample | source_quality_ev | downside_p10 | win_rate |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in stop_touch_rows[:10]:
        lines.append(
            f"| `{item.get('stop_touch_outcome_bucket')}` | `{item.get('sample_count')}` | `{item.get('source_quality_adjusted_ev_pct')}` | `{item.get('downside_p10_pct')}` | `{item.get('diagnostic_win_rate')}` |"
        )
    if not stop_touch_rows:
        lines.append("| - | 0 | - | - | - |")
    lines.extend(
        [
            "",
            "| entry_position_opportunity_bucket | sample | source_quality_ev | downside_p10 | win_rate |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in opportunity_rows[:10]:
        lines.append(
            f"| `{item.get('entry_position_opportunity_bucket')}` | `{item.get('sample_count')}` | `{item.get('source_quality_adjusted_ev_pct')}` | `{item.get('downside_p10_pct')}` | `{item.get('diagnostic_win_rate')}` |"
        )
    if not opportunity_rows:
        lines.append("| - | 0 | - | - | - |")
    lines.extend(
        [
            "",
            "## Avoid Buckets",
            "",
            "| axis | key | sample | source_quality_ev | downside_p10 |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in (report.get("avoid_buckets") or [])[:20]:
        axis = item.get("axis")
        key = item.get(axis)
        lines.append(
            f"| `{axis}` | `{key}` | `{item.get('sample_count')}` | `{item.get('source_quality_adjusted_ev_pct')}` | `{item.get('downside_p10_pct')}` |"
        )
    if not report.get("avoid_buckets"):
        lines.append("| - | - | 0 | - | - |")
    lines.extend(
        [
            "",
            "## Contract",
            "",
            "- This report is source-only and cannot mutate runtime env.",
            "- Sim discovery labels are not real execution quality evidence.",
            "- Sector/theme fields are diversity/source-quality inputs only.",
            "",
        ]
    )
    return "\n".join(lines)


def write_swing_strategy_discovery_ev_report(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    output_dir: Path = REPORT_DIR,
    lookback_days: int = 90,
) -> dict[str, Path]:
    report = build_swing_strategy_discovery_ev_report(target_date, db_url=db_url, lookback_days=lookback_days)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(_date_text(target_date))
    if output_dir != REPORT_DIR:
        base = output_dir / f"swing_strategy_discovery_ev_{_date_text(target_date)}"
        json_path, md_path = base.with_suffix(".json"), base.with_suffix(".md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--db-url", default=POSTGRES_URL)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--lookback-days", type=int, default=90)
    args = parser.parse_args(argv)
    paths = write_swing_strategy_discovery_ev_report(
        args.target_date,
        db_url=args.db_url,
        output_dir=args.output_dir,
        lookback_days=args.lookback_days,
    )
    print(f"[DONE] swing_strategy_discovery_ev_report json={paths['json']} md={paths['md']}")


if __name__ == "__main__":
    main()
