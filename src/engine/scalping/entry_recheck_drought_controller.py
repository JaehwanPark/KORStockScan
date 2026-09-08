"""Build the lightweight daily drought controller for entry recheck runtime."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy
from src.engine.automation.source_quality_hard_gate import (
    apply_source_quality_preflight_block,
    load_source_quality_preflight,
)
from src.engine.scalping.entry_ai_gate_backtest import (
    DROUGHT_REPORT_DIR,
    DROUGHT_REPORT_TYPE,
    DROUGHT_RUNTIME_UPDATE_MODE,
    ENTRY_OPPORTUNITY_RECHECK_FAMILY,
    EXACT_ARMED_SAMPLE_FLOOR,
    EXACT_COMPLETED_SAMPLE_FLOOR,
    FORBIDDEN_USES,
    _atomic_write_report_pair,
    _drought_conditional_policy,
    _entry_recheck_drought_candidate,
    _exclusive_report_lock,
    _drought_day_summary,
    _recent_trading_dates,
    BUY_FUNNEL_SENTINEL_DIR,
)

SCHEMA_VERSION = 1


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = DROUGHT_REPORT_DIR / f"{DROUGHT_REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _runtime_update_contract(
    *,
    target_date: str,
    clean_baseline_date: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        item
        for item in report.get("calibration_candidates") or []
        if isinstance(item, dict)
    ]
    allowed = [item for item in candidates if item.get("allowed_runtime_apply") is True]
    quality_window = (
        candidates[0].get("cumulative_quality_window")
        if candidates
        else {
            "window_policy": "rolling_3_trading_days",
            "start_date": target_date,
            "end_date": target_date,
            "clean_tuning_baseline_date": clean_baseline_date,
            "source_date_count": 0,
            "source_dates": [],
        }
    )
    return {
        "schema_version": 1,
        "update_mode": DROUGHT_RUNTIME_UPDATE_MODE,
        "owner_family": ENTRY_OPPORTUNITY_RECHECK_FAMILY,
        "max_runtime_apply_count": 1,
        "runtime_apply_candidate_count": len(candidates),
        "allowed_runtime_apply_count": len(allowed),
        "quality_update_id": (
            str(allowed[0].get("quality_update_id") or "") if allowed else ""
        ),
        "cumulative_quality_window": quality_window,
        "primary_decision_metric": "addressable_submit_drought_then_cost_adjusted_ev",
        "source_quality_gate": report.get("source_quality_gate") or "pass",
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    baseline_policy = clean_baseline_policy()
    clean_baseline_date = str(
        baseline_policy.get("clean_tuning_baseline_date") or "2026-06-05"
    )
    drought_policy = _drought_conditional_policy(
        target_date=target_date,
        clean_baseline_date=clean_baseline_date,
    )
    candidates = _entry_recheck_drought_candidate(
        target_date=target_date,
        clean_baseline_date=clean_baseline_date,
        drought_policy=drought_policy,
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_type": DROUGHT_REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "clean_baseline_policy": baseline_policy,
        "metric_contract": {
            "metric_role": "bounded_tunable",
            "decision_authority": "buy_funnel_drought_conditional_preopen_policy",
            "window_policy": "rolling_3_trading_days_plus_rolling20_causal_episode",
            "sample_floor": {
                "activation": "latest_critical_and_2_of_3_critical_with_denominators",
                "conversion_stop_exact_armed": EXACT_ARMED_SAMPLE_FLOOR,
                "economic_stop_exact_completed": EXACT_COMPLETED_SAMPLE_FLOOR,
            },
            "primary_decision_metric": (
                "addressable_submit_drought_then_cost_adjusted_ev"
            ),
            "source_quality_gate": "daily_preflight_and_exact_attempt_contract",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_gate": "pass",
        "diagnostic_apply_ready": False,
        "runtime_candidate_ready": any(
            item.get("allowed_runtime_apply") is True for item in candidates
        ),
        "allowed_runtime_apply": any(
            item.get("allowed_runtime_apply") is True for item in candidates
        ),
        "calibration_state": (
            str(candidates[0].get("calibration_state") or "freeze")
            if candidates
            else "freeze"
        ),
        "calibration_candidates": candidates,
        "drought_conditional_policy": drought_policy,
        "summary": {
            "bounded_calibration_candidate_count": len(candidates),
            "drought_activation_triggered": drought_policy.get("activation_triggered"),
            "drought_stop_triggered": drought_policy.get("stop_triggered"),
            "drought_desired_enabled": (
                (candidates[0].get("recommended_values") or {}).get("enabled")
                if candidates
                else None
            ),
            "intraday_escalation_allowed": drought_policy.get(
                "intraday_escalation_allowed"
            ),
            "intraday_escalation_scopes": drought_policy.get(
                "intraday_escalation_scopes"
            )
            or [],
            "runtime_acceptance_state": (
                drought_policy.get("exact_post_apply_attribution") or {}
            ).get("runtime_acceptance_state"),
            "top_evaluation_reason": (
                drought_policy.get("exact_post_apply_attribution") or {}
            ).get("top_evaluation_reason"),
        },
        "forbidden_uses": FORBIDDEN_USES,
    }
    report = apply_source_quality_preflight_block(
        report, load_source_quality_preflight(target_date)
    )
    final_candidates = [
        item
        for item in report.get("calibration_candidates") or []
        if isinstance(item, dict)
    ]
    ready = any(item.get("allowed_runtime_apply") is True for item in final_candidates)
    report["runtime_candidate_ready"] = ready
    report["allowed_runtime_apply"] = ready
    report["calibration_candidates"] = final_candidates
    report["runtime_update_contract"] = _runtime_update_contract(
        target_date=target_date,
        clean_baseline_date=clean_baseline_date,
        report=report,
    )
    from src.engine.automation.drought_handoff import (
        EFFECTIVE_DATE,
        controller_source_error,
    )

    if target_date >= EFFECTIVE_DATE:
        from src.engine.scalping.entry_recheck_review import (
            build_review,
            review_orders,
            REVIEW_DATES,
        )

        history_by_date = {row["source_date"]: row for row in drought_policy["history"]}
        review_days = []
        for day in _recent_trading_dates(
            target_date, start_date=clean_baseline_date, count=REVIEW_DATES
        ):
            review_days.append(
                history_by_date.get(day)
                or _drought_day_summary(
                    BUY_FUNNEL_SENTINEL_DIR / f"buy_funnel_sentinel_{day}.json"
                )
            )
        report["source_binding_version"] = 1
        report["maintenance_review"] = build_review(
            drought_policy, review_days, target_date
        )
        report["code_improvement_orders"] = review_orders(report["maintenance_review"])
        # Do not publish a policy calculated from an overwritten input generation.
        source_error = controller_source_error(
            report, BUY_FUNNEL_SENTINEL_DIR.parent, target_date, validate_review=True
        )
        if source_error:
            raise RuntimeError(source_error)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    policy = (
        report.get("drought_conditional_policy")
        if isinstance(report.get("drought_conditional_policy"), dict)
        else {}
    )
    exact = (
        policy.get("exact_post_apply_attribution")
        if isinstance(policy.get("exact_post_apply_attribution"), dict)
        else {}
    )
    lines = [
        f"# Entry Recheck Drought Controller - {report.get('target_date')}",
        "",
        "## Decision",
        "",
        f"- runtime_candidate_ready: `{report.get('runtime_candidate_ready')}`",
        f"- calibration_state: `{report.get('calibration_state')}`",
        f"- desired_enabled: `{summary.get('drought_desired_enabled')}`",
        f"- allowed_scopes: `{policy.get('allowed_scopes') or []}`",
        f"- intraday_escalation_scopes: "
        f"`{summary.get('intraday_escalation_scopes') or []}`",
        "",
        "## Evidence",
        "",
        f"- drought_history_dates: "
        f"`{[item.get('source_date') for item in policy.get('history') or []]}`",
        f"- activation/stop: `{policy.get('activation_triggered')}/"
        f"{policy.get('stop_triggered')}`",
        f"- stop_reasons: `{policy.get('stop_reasons') or []}`",
        f"- runtime_acceptance_state: `{exact.get('runtime_acceptance_state')}`",
        f"- evaluated/armed/submitted/filled/completed/paired: "
        f"`{exact.get('exact_evaluated_count')}/{exact.get('exact_armed_count')}/"
        f"{exact.get('exact_direct_submitted_count')}/{exact.get('exact_filled_count')}/"
        f"{exact.get('exact_completed_count')}/{exact.get('exact_paired_economic_sample')}`",
        f"- top_evaluation_reason: `{exact.get('top_evaluation_reason')}`",
        f"- evaluation_reason_counts_by_scope: "
        f"`{json.dumps(exact.get('evaluation_reason_counts_by_scope') or {}, ensure_ascii=False, sort_keys=True)}`",
        f"- aggregate_diagnostic_after_cost_ev_pct/net_pnl_krw: "
        f"`{exact.get('equal_weight_avg_profit_pct')}/"
        f"{exact.get('realized_net_pnl_krw')}`",
        "",
        "## Scope decisions and fill-quality cohorts",
        "",
        "| Scope | Enabled | Escalation | Stop reasons | Evidence start |",
        "|---|---|---|---|---|",
    ]
    for scope, decision in sorted((policy.get("scope_decisions") or {}).items()):
        state = decision.get("controller_state") or {}
        lines.append(
            f"| {scope.replace('|', '/')} | {decision.get('desired_enabled')} | "
            f"{decision.get('intraday_escalation_allowed')} | "
            f"{', '.join(decision.get('stop_reasons') or []) or '-'} | "
            f"{state.get('evidence_start_date')} |"
        )
    lines += [
        "",
        "| Scope | Cohort | Paired | Cost-adjusted EV (%) | Net PnL (KRW) | Decision eligible |",
        "|---|---|---|---|---|---|",
    ]
    for scope, cohorts in sorted(
        (exact.get("paired_economics_by_scope_and_cohort") or {}).items()
    ):
        for cohort, metrics in sorted(cohorts.items()):
            lines.append(
                f"| {scope.replace('|', '/')} | {cohort} | {metrics.get('paired_sample')} | "
                f"{metrics.get('equal_weight_avg_profit_pct')} | {metrics.get('realized_net_pnl_krw')} | "
                f"{metrics.get('decision_eligible')} |"
            )
    lines += [
        "",
        "- Stops and widening use same-scope, same-fill-quality evidence; mixed scale-in is diagnostic only.",
        "",
        "## Next action",
        "",
        "- PREOPEN consumes only this controller report; the cumulative score sweep is diagnostic-only.",
        "- Investigate source/consumption gaps and design source-only repairs immediately; positive economics is not a prerequisite for investigation.",
        "- Live widening still requires the existing exact paired economics and separate policy authority. The finite maintenance review may recommend repair, merge, or retirement, never automatic runtime mutation.",
        f"- maintenance acceptance owner: `{(report.get('maintenance_review') or {}).get('acceptance_owner')}`",
        f"- conditional next PREOPEN date (all existing guards required): `{(report.get('maintenance_review') or {}).get('conditional_next_preopen_date')}`",
        f"- source transition dates: `{[r.get('source_date') for r in (report.get('maintenance_review') or {}).get('history_transition', [])]}`",
        "- Never relax stale quote, DANGER, broker/account/order/quantity/cooldown, or probe-first guards.",
        "",
        "| Scope | Valid drought dates / review bound | First depleted stage | Maintenance due | Review options |",
        "|---|---|---|---|---|",
    ]
    for row in (report.get("maintenance_review") or {}).get("scopes", []):
        lines.append(
            f"| {row['scope'].replace('|', '/')} | {row['review_date_count']}/{row['review_date_floor']} | {row['first_depleted_stage']} | {row['bounded_maintenance_due']} | {', '.join(row['review_options'])} |"
        )
    return "\n".join(lines)


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    return _atomic_write_report_pair(
        report,
        report_dir=DROUGHT_REPORT_DIR,
        report_type=DROUGHT_REPORT_TYPE,
        markdown=render_markdown(report),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        with _exclusive_report_lock(
            DROUGHT_REPORT_DIR, DROUGHT_REPORT_TYPE, args.target_date
        ):
            report = build_report(args.target_date)
            if args.write:
                json_path, md_path = write_report(report)
                print(
                    json.dumps(
                        {"json": str(json_path), "md": str(md_path)},
                        ensure_ascii=False,
                    )
                )
            else:
                print(
                    json.dumps(
                        report,
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                        default=str,
                    )
                )
    except RuntimeError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
