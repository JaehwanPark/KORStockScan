"""Build DeepSeek LLM payload from swing fact tables and analysis results."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from analysis.deepseek_swing_pattern_lab.config import (
    END_DATE,
    OUTPUT_DIR,
    PROMPT_DIR,
    REPORT_DIR,
)

SCHEMA_VERSION = 2
SWING_FEEDBACK_SOURCES = {
    "threshold_cycle_ev": ("threshold_cycle_ev", "threshold_cycle_ev"),
    "swing_lifecycle_decision_matrix": (
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
    ),
    "swing_lifecycle_bucket_discovery": (
        "swing_lifecycle_bucket_discovery",
        "swing_lifecycle_bucket_discovery",
    ),
    "swing_strategy_discovery_ev": (
        "swing_strategy_discovery_ev",
        "swing_strategy_discovery_ev",
    ),
}
CLEAN_TUNING_BASELINE_DATE = "2026-06-04"


def _latest_feedback_artifact_path(
    report_name: str, stem: str, target_date: str
) -> tuple[Path | None, str | None]:
    target = str(target_date).strip()[:10]
    report_dir = REPORT_DIR / report_name
    exact = report_dir / f"{stem}_{target}.json"
    if exact.exists():
        return exact, target
    latest_path: Path | None = None
    latest_date: str | None = None
    for path in sorted(report_dir.glob(f"{stem}_*.json")):
        suffix = path.name.removeprefix(f"{stem}_").removesuffix(".json")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", suffix):
            continue
        source_date = suffix
        if (
            target >= CLEAN_TUNING_BASELINE_DATE
            and source_date < CLEAN_TUNING_BASELINE_DATE
        ):
            continue
        if source_date <= target and (latest_date is None or source_date > latest_date):
            latest_path = path
            latest_date = source_date
    return latest_path, latest_date


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _load_csv(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    if path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _load_json(name: str) -> dict[str, Any]:
    path = OUTPUT_DIR / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_feedback_sources() -> dict[str, Any]:
    consumed = []
    missing = []
    target_date = str(END_DATE).strip()[:10]
    for source_id, (report_name, stem) in SWING_FEEDBACK_SOURCES.items():
        path, source_date = _latest_feedback_artifact_path(
            report_name, stem, target_date
        )
        item = {
            "source_id": source_id,
            "path": str(path) if path else "",
            "source_date": source_date,
            "target_date": target_date,
            "freshness": (
                "same_day"
                if source_date == target_date
                else "latest_available_lte_target" if source_date else "missing"
            ),
            "runtime_effect": False,
            "decision_authority": "source_quality_only",
        }
        if path and path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            summary = (
                payload.get("summary")
                if isinstance(payload.get("summary"), dict)
                else {}
            )
            consumed.append(
                {
                    **item,
                    "status": payload.get("status") or summary.get("status"),
                    "warnings": payload.get("warnings")
                    or summary.get("warnings")
                    or [],
                }
            )
        else:
            missing.append({**item, "gap_type": "source_quality_gap"})
    return {
        "consumed_feedback_sources": consumed,
        "missing_feedback_sources": missing,
        "runtime_effect": False,
        "decision_authority": "source_quality_only",
    }


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _safe_value(value: Any) -> Any:
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (pd.Timestamp,)):
        return str(value)
    return value


def build_payload_summary(
    trade_fact: pd.DataFrame,
    funnel_fact: pd.DataFrame,
    sequence_fact: pd.DataFrame,
    ofi_qi_fact: pd.DataFrame,
    analysis_result: dict[str, Any],
) -> dict[str, Any]:
    completed_case_count = 0
    if not trade_fact.empty and "completed" in trade_fact:
        completed_case_count = min(int((trade_fact["completed"] == True).sum()), 20)
    finding_case_count = min(len(analysis_result.get("stage_findings", []) or []), 10)
    ofi_qi_case_count = min(len(ofi_qi_fact), 30) if not ofi_qi_fact.empty else 0
    case_counts = {
        "selected_trades": completed_case_count,
        "findings_brief": finding_case_count,
        "ofi_qi_samples": ofi_qi_case_count,
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "payload_type": "deepseek_swing_pattern_lab_summary",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metric_contract": analysis_result.get("metric_contract", {}),
        "data_window": {
            "start": str(funnel_fact["date"].iloc[0]) if not funnel_fact.empty else "",
            "end": str(funnel_fact["date"].iloc[-1]) if not funnel_fact.empty else "",
        },
        "counts": {
            "trade_rows": len(trade_fact),
            "funnel_rows": len(funnel_fact),
            "sequence_rows": len(sequence_fact),
            "ofi_qi_rows": len(ofi_qi_fact),
        },
        "funnel_summary": _build_funnel_summary(funnel_fact),
        "trade_summary": _build_trade_summary(trade_fact),
        "ofi_qi_summary": _build_ofi_qi_summary(ofi_qi_fact),
        "findings_count": len(analysis_result.get("stage_findings", [])),
        "order_count": len(analysis_result.get("code_improvement_orders", [])),
        "case_counts": case_counts,
        "total_cases": sum(case_counts.values()),
        "feedback_sources": _load_feedback_sources(),
    }
    return summary


def _build_funnel_summary(funnel_fact: pd.DataFrame) -> dict[str, Any]:
    if funnel_fact.empty:
        return {"error": "No funnel data"}
    return {
        "total_selected": _safe_int(funnel_fact["selected_count"].sum()),
        "total_db_rows": _safe_int(funnel_fact["db_rows"].sum()),
        "total_entered": _safe_int(funnel_fact["entered_rows"].sum()),
        "total_completed": _safe_int(funnel_fact["completed_rows"].sum()),
        "total_blocked_gatekeeper": _safe_int(
            funnel_fact["blocked_gatekeeper_reject_unique"].sum()
        ),
        "total_blocked_gap": _safe_int(funnel_fact["blocked_swing_gap_unique"].sum()),
        "total_market_regime_block": _safe_int(
            funnel_fact["market_regime_block_unique"].sum()
        ),
        "total_submitted": _safe_int(funnel_fact["submitted_unique_records"].sum()),
        "total_simulated": _safe_int(
            funnel_fact["simulated_order_unique_records"].sum()
        ),
    }


def _build_trade_summary(trade_fact: pd.DataFrame) -> dict[str, Any]:
    if trade_fact.empty:
        return {"error": "No trade data"}
    completed = trade_fact[trade_fact["completed"] == True]
    valid = completed[completed["valid_profit_rate"].notna()]
    return {
        "total_trades": len(trade_fact),
        "completed": len(completed),
        "valid_profit": len(valid),
        "win_trades": int((valid["profit"] > 0).sum()) if not valid.empty else 0,
        "loss_trades": int((valid["profit"] < 0).sum()) if not valid.empty else 0,
        "total_pnl": round(float(valid["profit"].sum()), 2) if not valid.empty else 0.0,
        "avg_profit_rate": (
            round(float(valid["profit_rate"].mean()), 4) if not valid.empty else None
        ),
    }


def _build_ofi_qi_summary(ofi_qi_fact: pd.DataFrame) -> dict[str, Any]:
    if ofi_qi_fact.empty:
        return {"error": "No OFI/QI data"}
    total = len(ofi_qi_fact)
    stale = int(ofi_qi_fact["stale_missing_flag"].sum())
    reason_counts = {
        column.replace("_flag", ""): int(ofi_qi_fact[column].sum())
        for column in (
            "micro_missing_flag",
            "micro_stale_flag",
            "observer_unhealthy_flag",
            "micro_not_ready_flag",
            "state_insufficient_flag",
        )
        if column in ofi_qi_fact
    }
    stale_rows = ofi_qi_fact[ofi_qi_fact["stale_missing_flag"] == True].copy()
    reason_combination_counts = (
        stale_rows["stale_missing_reasons"]
        .fillna("unknown")
        .replace("", "unknown")
        .str.replace(",", "+")
        .value_counts()
        .to_dict()
        if "stale_missing_reasons" in stale_rows and not stale_rows.empty
        else {}
    )
    reason_combination_unique_record_counts: dict[str, int] = {}
    if (
        not stale_rows.empty
        and "stale_missing_reasons" in stale_rows
        and "record_id" in stale_rows
    ):
        tmp = stale_rows.copy()
        tmp["_reason_combination"] = (
            tmp["stale_missing_reasons"]
            .fillna("unknown")
            .replace("", "unknown")
            .str.replace(",", "+")
        )
        reason_combination_unique_record_counts = {
            str(key): int(value)
            for key, value in tmp.groupby("_reason_combination")["record_id"]
            .nunique()
            .to_dict()
            .items()
        }
    group_counts = (
        stale_rows["group"]
        .fillna("unknown")
        .replace("", "unknown")
        .value_counts()
        .to_dict()
        if "group" in stale_rows and not stale_rows.empty
        else {}
    )
    group_unique_record_counts = (
        {
            str(key): int(value)
            for key, value in stale_rows.groupby("group")["record_id"]
            .nunique()
            .to_dict()
            .items()
        }
        if "group" in stale_rows and "record_id" in stale_rows and not stale_rows.empty
        else {}
    )
    observer_overlap = {
        "observer_unhealthy_total": (
            int(stale_rows["observer_unhealthy_flag"].sum())
            if "observer_unhealthy_flag" in stale_rows and not stale_rows.empty
            else 0
        ),
        "observer_unhealthy_with_other_reason": 0,
        "observer_unhealthy_only": 0,
    }
    if not stale_rows.empty and "observer_unhealthy_flag" in stale_rows:
        other_columns = [
            column
            for column in (
                "micro_missing_flag",
                "micro_stale_flag",
                "micro_not_ready_flag",
                "state_insufficient_flag",
            )
            if column in stale_rows
        ]
        observer_rows = stale_rows[stale_rows["observer_unhealthy_flag"] == True]
        observer_overlap["observer_unhealthy_with_other_reason"] = (
            int(observer_rows[other_columns].any(axis=1).sum()) if other_columns else 0
        )
        observer_overlap["observer_unhealthy_only"] = (
            observer_overlap["observer_unhealthy_total"]
            - observer_overlap["observer_unhealthy_with_other_reason"]
        )
    advice = (
        ofi_qi_fact["swing_micro_advice"].value_counts().to_dict()
        if "swing_micro_advice" in ofi_qi_fact
        else {}
    )
    return {
        "total_samples": total,
        "stale_missing_count": stale,
        "stale_missing_ratio": round(stale / max(total, 1), 4),
        "stale_missing_reason_counts": reason_counts,
        "stale_missing_reason_ratios": {
            reason: round(count / max(total, 1), 4)
            for reason, count in reason_counts.items()
        },
        "stale_missing_unique_record_count": (
            int(stale_rows["record_id"].nunique()) if "record_id" in stale_rows else 0
        ),
        "stale_missing_reason_combination_counts": reason_combination_counts,
        "stale_missing_reason_combination_unique_record_counts": reason_combination_unique_record_counts,
        "stale_missing_group_counts": group_counts,
        "stale_missing_group_unique_record_counts": group_unique_record_counts,
        "observer_unhealthy_overlap": observer_overlap,
        "advice_distribution": advice,
    }


def build_payload_cases(
    trade_fact: pd.DataFrame,
    sequence_fact: pd.DataFrame,
    ofi_qi_fact: pd.DataFrame,
    analysis_result: dict[str, Any],
) -> dict[str, Any]:
    cases = {
        "schema_version": SCHEMA_VERSION,
        "payload_type": "deepseek_swing_pattern_lab_cases",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "feedback_sources": _load_feedback_sources(),
        "selected_trades": [],
        "findings_brief": [],
        "ofi_qi_samples": [],
    }

    if not trade_fact.empty:
        completed = trade_fact[trade_fact["completed"] == True].head(20)
        for _, row in completed.iterrows():
            cases["selected_trades"].append(
                {
                    "record_id": str(row.get("record_id", "")),
                    "stock_code": str(row.get("stock_code", "")),
                    "stock_name": str(row.get("stock_name", "")),
                    "strategy": str(row.get("strategy", "")),
                    "position_tag": str(row.get("position_tag", "")),
                    "buy_qty": _safe_int(row.get("buy_qty")),
                    "buy_price": _safe_value(row.get("buy_price")),
                    "sell_qty": _safe_int(row.get("sell_qty")),
                    "sell_price": _safe_value(row.get("sell_price")),
                    "profit_rate": _safe_value(row.get("profit_rate")),
                    "profit": _safe_value(row.get("profit")),
                    "actual_order_submitted": _safe_bool(
                        row.get("actual_order_submitted", False)
                    ),
                    "broker_order_forbidden": _safe_bool(
                        row.get("broker_order_forbidden", True)
                    ),
                    "decision_authority": str(row.get("decision_authority", "")),
                    "pyramid_count": _safe_int(row.get("pyramid_count")),
                    "avg_down_count": _safe_int(row.get("avg_down_count")),
                }
            )

    for finding in (analysis_result.get("stage_findings") or [])[:10]:
        cases["findings_brief"].append(
            {
                "finding_id": finding.get("finding_id"),
                "title": finding.get("title"),
                "stage": finding.get("lifecycle_stage"),
                "route": finding.get("route"),
                "mapped_family": finding.get("mapped_family"),
            }
        )

    if not ofi_qi_fact.empty:
        sample = ofi_qi_fact.head(30)
        for _, row in sample.iterrows():
            cases["ofi_qi_samples"].append(
                {
                    "record_id": str(row.get("record_id", "")),
                    "stock_code": str(row.get("stock_code", "")),
                    "stage": str(row.get("stage", "")),
                    "group": str(row.get("group", "")),
                    "micro_state": str(row.get("orderbook_micro_state", "")),
                    "micro_advice": str(row.get("swing_micro_advice", "")),
                    "stale_missing": bool(row.get("stale_missing_flag", False)),
                    "stale_missing_reasons": str(row.get("stale_missing_reasons", "")),
                    "reason_flags": {
                        "micro_missing": bool(row.get("micro_missing_flag", False)),
                        "micro_stale": bool(row.get("micro_stale_flag", False)),
                        "observer_unhealthy": bool(
                            row.get("observer_unhealthy_flag", False)
                        ),
                        "micro_not_ready": bool(row.get("micro_not_ready_flag", False)),
                        "state_insufficient": bool(
                            row.get("state_insufficient_flag", False)
                        ),
                    },
                    "ready": bool(row.get("orderbook_micro_ready", False)),
                    "healthy": bool(row.get("orderbook_micro_observer_healthy", False)),
                }
            )

    return cases


def generate_final_review_markdown(
    analysis_result: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    dq = analysis_result.get("data_quality", {})
    findings = analysis_result.get("stage_findings", [])
    orders = analysis_result.get("code_improvement_orders", [])

    route_counts = Counter(f.get("route", "unknown") for f in findings)
    stage_counts = Counter(f.get("lifecycle_stage", "unknown") for f in findings)

    lines = [
        "# DeepSeek Swing Pattern Lab - Final Review Report",
        "",
        "## 판정",
        "",
        f"- 분석 기간: `{analysis_result.get('analysis_start')}` ~ `{analysis_result.get('analysis_end')}`",
        f"- trade_rows: `{dq.get('trade_rows', 0)}`",
        f"- lifecycle_event_rows: `{dq.get('lifecycle_event_rows', 0)}`",
        f"- completed_valid_profit_rows: `{dq.get('completed_valid_profit_rows', 0)}`",
        f"- ofi_qi_rows: `{dq.get('ofi_qi_rows', 0)}`",
        f"- total_findings: `{len(findings)}`",
        f"- code_improvement_orders: `{len(orders)}`",
        f"- runtime_change: `{analysis_result.get('runtime_change', False)}`",
        "",
        "## 분류 요약",
        "",
        f"- implement_now: `{route_counts.get('implement_now', 0)}`",
        f"- attach_existing_family: `{route_counts.get('attach_existing_family', 0)}`",
        f"- design_family_candidate: `{route_counts.get('design_family_candidate', 0)}`",
        f"- defer_evidence: `{route_counts.get('defer_evidence', 0)}`",
        f"- reject: `{route_counts.get('reject', 0)}`",
        "",
        "## Stage별 분석",
        "",
    ]
    for stage in sorted(stage_counts):
        count = stage_counts[stage]
        lines.append(f"- `{stage}`: {count} findings")

    lines.extend(["", "## Stage Findings", ""])
    for idx, f in enumerate(findings, start=1):
        lines.extend(
            [
                f"### {idx}. `{f.get('finding_id')}`",
                "",
                f"- title: {f.get('title')}",
                f"- lifecycle_stage: `{f.get('lifecycle_stage')}`",
                f"- route: `{f.get('route')}`",
                f"- mapped_family: `{f.get('mapped_family') or '-'}`",
                f"- confidence: `{f.get('confidence')}`",
                f"- runtime_effect: `{f.get('runtime_effect')}`",
                f"- expected_ev_effect: {f.get('expected_ev_effect')}",
                "",
            ]
        )

    lines.extend(["## Code Improvement Orders", ""])
    for idx, order in enumerate(orders, start=1):
        lines.extend(
            [
                f"### {idx}. `{order.get('order_id')}`",
                "",
                f"- title: {order.get('title')}",
                f"- lifecycle_stage: `{order.get('lifecycle_stage')}`",
                f"- target_subsystem: `{order.get('target_subsystem')}`",
                f"- route: `{order.get('route')}`",
                f"- mapped_family: `{order.get('mapped_family') or '-'}`",
                f"- threshold_family: `{order.get('threshold_family') or '-'}`",
                f"- runtime_effect: `{order.get('runtime_effect')}`",
                f"- allowed_runtime_apply: `{order.get('allowed_runtime_apply')}`",
                f"- expected_ev_effect: {order.get('expected_ev_effect')}",
                f"- files_likely_touched: {', '.join(f'`{f}`' for f in (order.get('files_likely_touched') or []))}",
                "",
            ]
        )

    if not orders:
        lines.append("- none")
        lines.append("")

    lines.extend(
        [
            "## Data Quality Warnings",
            "",
        ]
    )
    for w in dq.get("warnings", []):
        lines.append(f"- {w}")
    if not dq.get("warnings"):
        lines.append("- none")
    lines.append("")

    return "\n".join(lines)


def generate_ev_backlog_markdown(
    analysis_result: dict[str, Any],
) -> str:
    findings = analysis_result.get("stage_findings", [])
    lines = [
        "# Swing EV Improvement Backlog for OPS",
        "",
        "## 개요",
        "",
        f"- total_findings: `{len(findings)}`",
        f"- runtime_change: `{analysis_result.get('runtime_change', False)}`",
        f"- purpose: report-only / proposal-only improvement backlog",
        "",
        "## Improvement Candidates",
        "",
    ]
    for idx, f in enumerate(findings, start=1):
        route = f.get("route", "defer_evidence")
        priority = (
            "HIGH"
            if route == "implement_now"
            else (
                "MEDIUM"
                if route in ("attach_existing_family", "design_family_candidate")
                else "LOW"
            )
        )
        lines.extend(
            [
                f"### {idx}. {f.get('title')}",
                "",
                f"- finding_id: `{f.get('finding_id')}`",
                f"- lifecycle_stage: `{f.get('lifecycle_stage')}`",
                f"- route: `{route}`",
                f"- priority: `{priority}`",
                f"- mapped_family: `{f.get('mapped_family') or '-'}`",
                f"- confidence: `{f.get('confidence')}`",
                f"- expected_ev_effect: {f.get('expected_ev_effect')}",
                "",
            ]
        )

    if not findings:
        lines.append("- none")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    trade_fact = _load_csv("swing_trade_fact.csv")
    funnel_fact = _load_csv("swing_lifecycle_funnel_fact.csv")
    sequence_fact = _load_csv("swing_sequence_fact.csv")
    ofi_qi_fact = _load_csv("swing_ofi_qi_fact.csv")
    analysis_result = _load_json("swing_pattern_analysis_result.json")

    summary = build_payload_summary(
        trade_fact, funnel_fact, sequence_fact, ofi_qi_fact, analysis_result
    )
    cases = build_payload_cases(trade_fact, sequence_fact, ofi_qi_fact, analysis_result)

    (OUTPUT_DIR / "deepseek_payload_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "deepseek_payload_cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    final_review_md = generate_final_review_markdown(analysis_result, summary)
    (OUTPUT_DIR / "final_review_report_for_lead_ai.md").write_text(
        final_review_md, encoding="utf-8"
    )

    ev_backlog_md = generate_ev_backlog_markdown(analysis_result)
    (OUTPUT_DIR / "swing_ev_improvement_backlog_for_ops.md").write_text(
        ev_backlog_md, encoding="utf-8"
    )

    manifest = _load_json("run_manifest.json") or {}
    manifest.update(
        {
            "deeppayload_generated_at": datetime.now()
            .astimezone()
            .isoformat(timespec="seconds"),
            "deeppayload_outputs": {
                "payload_summary": str(OUTPUT_DIR / "deepseek_payload_summary.json"),
                "payload_cases": str(OUTPUT_DIR / "deepseek_payload_cases.json"),
                "final_review_report": str(
                    OUTPUT_DIR / "final_review_report_for_lead_ai.md"
                ),
                "ev_improvement_backlog": str(
                    OUTPUT_DIR / "swing_ev_improvement_backlog_for_ops.md"
                ),
            },
        }
    )
    (OUTPUT_DIR / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"DeepSeek payload built: {summary.get('findings_count', 0)} findings summarized"
    )
    print(f"Outputs written to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
