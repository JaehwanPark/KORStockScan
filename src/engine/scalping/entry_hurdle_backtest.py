"""Report-only BUY funnel hurdle backtest from existing June artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "entry_hurdle_backtest"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
BUY_FUNNEL_DIR = DATA_DIR / "report" / "buy_funnel_sentinel"
MISSED_ENTRY_DIRS = [
    DATA_DIR / "report" / "monitor_snapshots",
    DATA_DIR / "report" / "missed_entry_counterfactual",
]

FORBIDDEN_USES = [
    "entry price reprice",
    "risk expansion",
    "quantity cap release",
    "broker guard bypass",
    "stale quote guard bypass",
    "intraday threshold mutation",
    "provider change",
    "bot restart",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "null", "none"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "null", "none"):
            return default
        return int(float(value))
    except Exception:
        return default


def _load_json(path: Path) -> dict[str, Any]:
    try:
        actual_path = existing_or_gzip_path(path)
        if actual_path.exists():
            with open_text_auto(actual_path) as handle:
                return json.loads(handle.read())
    except Exception:
        return {}
    return {}


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


def _buy_funnel_path(target_date: str) -> Path:
    return existing_or_gzip_path(BUY_FUNNEL_DIR / f"buy_funnel_sentinel_{target_date}.json")


def _missed_entry_path(target_date: str) -> Path:
    for base in MISSED_ENTRY_DIRS:
        path = base / f"missed_entry_counterfactual_{target_date}.json"
        actual_path = existing_or_gzip_path(path)
        if actual_path.exists():
            return actual_path
    return existing_or_gzip_path(MISSED_ENTRY_DIRS[0] / f"missed_entry_counterfactual_{target_date}.json")


def _session_summary(report: dict[str, Any]) -> dict[str, Any]:
    session = report.get("session_summary")
    if isinstance(session, dict):
        return session
    current = report.get("current")
    if isinstance(current, dict) and isinstance(current.get("session"), dict):
        return current["session"]
    if isinstance(current, dict):
        return current
    return {}


def _stage_unique(report: dict[str, Any]) -> dict[str, int]:
    session = _session_summary(report)
    values = session.get("stage_unique")
    if not isinstance(values, dict):
        return {}
    return {str(key): _safe_int(value, 0) for key, value in values.items()}


def _ratios(report: dict[str, Any]) -> dict[str, float]:
    session = _session_summary(report)
    values = session.get("ratios")
    if not isinstance(values, dict):
        return {}
    return {str(key): _safe_float(value, 0.0) for key, value in values.items()}


def _classification(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("classification")
    return value if isinstance(value, dict) else {}


def _quote_freshness_attribution(report: dict[str, Any]) -> dict[str, Any]:
    classification = _classification(report)
    root_cause = classification.get("submit_drought_root_cause")
    if not isinstance(root_cause, dict):
        return {}
    value = root_cause.get("quote_freshness_attribution")
    return value if isinstance(value, dict) else {}


def _blocker_metrics(missed_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = ((missed_report.get("metrics") or {}).get("blocker_outcome_metrics") or {})
    return metrics if isinstance(metrics, dict) else {}


def _cohort_metrics(missed_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = ((missed_report.get("metrics") or {}).get("cohort_outcome_metrics") or {})
    return metrics if isinstance(metrics, dict) else {}


def _hurdle_decision(row: dict[str, Any]) -> str:
    missed_rate = _safe_float(row.get("missed_winner_rate"), 0.0)
    avoided_rate = _safe_float(row.get("avoided_loser_rate"), 0.0)
    evaluated = _safe_int(row.get("evaluated_candidates"), 0)
    if evaluated < 3:
        return "hold_sample"
    if missed_rate >= avoided_rate + 20.0 and missed_rate >= 35.0:
        return "overblocking_candidate"
    if avoided_rate >= missed_rate + 20.0 and avoided_rate >= 35.0:
        return "protective_hurdle_candidate"
    return "balanced_or_unclear"


def _counter_to_plain(counter: Counter[str]) -> dict[str, int]:
    return {str(key): _safe_int(value, 0) for key, value in sorted(counter.items()) if _safe_int(value, 0) > 0}


def _top_overblocking(summary: dict[str, dict[str, Any]], keys: set[str]) -> dict[str, Any] | None:
    rows = []
    for key in keys:
        row = summary.get(key)
        if not isinstance(row, dict):
            continue
        if row.get("hurdle_decision") != "overblocking_candidate":
            continue
        rows.append((key, row))
    if not rows:
        return None
    rows.sort(
        key=lambda item: (
            _safe_float(item[1].get("missed_winner_rate"), 0.0),
            _safe_int(item[1].get("missed_winner_count"), 0),
            _safe_int(item[1].get("evaluated_candidates"), 0),
        ),
        reverse=True,
    )
    key, row = rows[0]
    return {"blocker": key, **row}


def _next_action_diagnostics(
    *,
    stage_totals: Counter[str],
    blocker_summary: dict[str, dict[str, Any]],
    cohort_summary: dict[str, dict[str, Any]],
    quote_totals: dict[str, Counter[str] | int],
    window_policy: str,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    refresh_attempted = _safe_int(quote_totals.get("refresh_attempted_count"), 0)
    refresh_applied = _safe_int(quote_totals.get("refresh_applied_count"), 0)
    recovered = _safe_int(quote_totals.get("latency_pass_recovered_count"), 0)
    submitted_after_refresh = _safe_int(quote_totals.get("order_bundle_submitted_after_refresh_count"), 0)
    still_blocked = _safe_int(quote_totals.get("still_latency_blocked_after_refresh_count"), 0)
    recovered_downstream = (
        quote_totals.get("latency_pass_recovered_downstream_stage_counts")
        if isinstance(quote_totals.get("latency_pass_recovered_downstream_stage_counts"), Counter)
        else Counter()
    )

    if recovered > submitted_after_refresh:
        actions.append(
            {
                "action_id": "trace_latency_refresh_recovered_downstream_blocker",
                "priority": 1,
                "decision": "instrumentation_or_guard_overlap_candidate",
                "reason": "quote refresh recovered latency pass but did not always reach broker submit",
                "evidence": {
                    "refresh_attempted_count": refresh_attempted,
                    "refresh_applied_count": refresh_applied,
                    "latency_pass_recovered_count": recovered,
                    "order_bundle_submitted_after_refresh_count": submitted_after_refresh,
                    "still_latency_blocked_after_refresh_count": still_blocked,
                    "downstream_stage_counts": _counter_to_plain(recovered_downstream),
                },
                "allowed_next_step": "trace post-refresh downstream blocker provenance before changing guards",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    liquidity = _top_overblocking(blocker_summary, {"pre_submit_liquidity_guard_block", "blocked_liquidity"})
    if liquidity:
        actions.append(
            {
                "action_id": "review_pre_submit_liquidity_relief_scope",
                "priority": 2,
                "decision": "bounded_report_only_policy_candidate",
                "reason": "liquidity blocker has missed-winner skew in existing counterfactual data",
                "evidence": liquidity,
                "allowed_next_step": (
                    "inspect pre_submit_liquidity_relief_skipped reasons and source-quality fields; "
                    "promote only through postclose/PREOPEN bounded policy if validated"
                ),
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    ai_wait = _top_overblocking(blocker_summary, {"blocked_ai_score", "first_ai_wait"})
    ai_wait = ai_wait or _top_overblocking(
        cohort_summary,
        {"entry_source_blocked_ai_score", "entry_source_wait6579", "entry_wait6579_score66_69"},
    )
    if ai_wait:
        actions.append(
            {
                "action_id": "review_ai_wait_score_recheck_scope",
                "priority": 3,
                "decision": "recheck_scope_candidate_not_threshold_relaxation",
                "reason": "AI wait/score blocker has missed-winner skew but broad BUY threshold relaxation is forbidden",
                "evidence": ai_wait,
                "allowed_next_step": "evaluate bounded recheck/cohort routing using clean-baseline missed-winner evidence",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    drift = _top_overblocking(blocker_summary, {"pre_submit_late_entry_price_drift_guard_block"})
    if drift:
        actions.append(
            {
                "action_id": "audit_late_entry_price_drift_guard_context",
                "priority": 4,
                "decision": "price_context_audit_candidate",
                "reason": "late price drift guard blocks possible winners; changing entry price is forbidden",
                "evidence": drift,
                "allowed_next_step": "audit reference-price and micro-reconfirmation provenance before any policy candidate",
                "forbidden_uses": FORBIDDEN_USES,
                "runtime_effect": False,
            }
        )

    actions.sort(key=lambda item: (_safe_int(item.get("priority"), 99), str(item.get("action_id") or "")))
    return {
        "metric_role": "next_action_diagnostic",
        "decision_authority": "entry_hurdle_backtest_report_only",
        "window_policy": window_policy,
        "sample_floor": "report_only_blocker_sample_floor_3",
        "primary_decision_metric": "missed_winner_vs_avoided_loser_tradeoff",
        "source_quality_gate": "clean_baseline_allowed_existing_buy_funnel_and_missed_entry_artifacts",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted_provenance_preserved": True,
        "forbidden_uses": FORBIDDEN_USES,
        "stage_pressure": {
            "ai_confirmed": _safe_int(stage_totals.get("ai_confirmed"), 0),
            "budget_pass": _safe_int(stage_totals.get("budget_pass"), 0),
            "latency_pass": _safe_int(stage_totals.get("latency_pass"), 0),
            "order_bundle_submitted": _safe_int(stage_totals.get("order_bundle_submitted"), 0),
            "blocked_ai_score": _safe_int(stage_totals.get("blocked_ai_score"), 0),
            "first_ai_wait": _safe_int(stage_totals.get("first_ai_wait"), 0),
            "latency_block": _safe_int(stage_totals.get("latency_block"), 0),
            "blocked_liquidity": _safe_int(stage_totals.get("blocked_liquidity"), 0),
            "pre_submit_liquidity_guard_block": _safe_int(
                stage_totals.get("pre_submit_liquidity_guard_block"), 0
            ),
            "pre_submit_late_entry_price_drift_guard_block": _safe_int(
                stage_totals.get("pre_submit_late_entry_price_drift_guard_block"), 0
            ),
        },
        "quote_freshness_totals": {
            "refresh_attempted_count": refresh_attempted,
            "refresh_applied_count": refresh_applied,
            "still_latency_blocked_after_refresh_count": still_blocked,
            "latency_pass_recovered_count": recovered,
            "order_bundle_submitted_after_refresh_count": submitted_after_refresh,
            "refresh_subreason_counts": _counter_to_plain(
                quote_totals.get("refresh_subreason_counts")
                if isinstance(quote_totals.get("refresh_subreason_counts"), Counter)
                else Counter()
            ),
            "latency_pass_recovered_downstream_stage_counts": _counter_to_plain(recovered_downstream),
        },
        "recommended_next_actions": actions,
    }


def build_report(
    target_date: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    candidate_dates = _date_range(start, end)
    source_dates, excluded_dates = filter_allowed_dates(candidate_dates, policy)
    stage_totals: Counter[str] = Counter()
    blocker_totals: dict[str, Counter] = defaultdict(Counter)
    cohort_totals: dict[str, Counter] = defaultdict(Counter)
    quote_totals: dict[str, Counter[str] | int] = {
        "refresh_subreason_counts": Counter(),
        "refresh_block_subreason_counts": Counter(),
        "latency_pass_recovered_downstream_counts": Counter(),
        "latency_pass_recovered_downstream_stage_counts": Counter(),
        "refresh_attempted_count": 0,
        "refresh_applied_count": 0,
        "still_latency_blocked_after_refresh_count": 0,
        "latency_pass_recovered_count": 0,
        "order_bundle_submitted_after_refresh_count": 0,
    }
    date_rows: list[dict[str, Any]] = []
    missing_artifacts: list[dict[str, str]] = []

    for source_date in source_dates:
        buy_path = _buy_funnel_path(source_date)
        missed_path = _missed_entry_path(source_date)
        buy_report = _load_json(buy_path)
        missed_report = _load_json(missed_path)
        if not buy_report:
            missing_artifacts.append({"date": source_date, "artifact": "buy_funnel_sentinel", "path": str(buy_path)})
        if not missed_report:
            missing_artifacts.append({"date": source_date, "artifact": "missed_entry_counterfactual", "path": str(missed_path)})

        stage_unique = _stage_unique(buy_report)
        ratios = _ratios(buy_report)
        for stage, count in stage_unique.items():
            stage_totals[stage] += count

        blocker_rows = _blocker_metrics(missed_report)
        for key, row in blocker_rows.items():
            bucket = blocker_totals[str(key)]
            bucket["evaluated_candidates"] += _safe_int(row.get("evaluated_candidates"), 0)
            bucket["missed_winner_count"] += _safe_int(row.get("missed_winner_count"), 0)
            bucket["avoided_loser_count"] += _safe_int(row.get("avoided_loser_count"), 0)
            bucket["neutral_count"] += _safe_int(row.get("neutral_count"), 0)

        cohort_rows = _cohort_metrics(missed_report)
        for key, row in cohort_rows.items():
            bucket = cohort_totals[str(key)]
            evaluated = _safe_int(row.get("evaluated_candidates"), 0)
            missed = round(_safe_float(row.get("missed_winner_rate"), 0.0) * evaluated / 100.0)
            avoided = round(_safe_float(row.get("avoided_loser_rate"), 0.0) * evaluated / 100.0)
            bucket["evaluated_candidates"] += evaluated
            bucket["missed_winner_count"] += missed
            bucket["avoided_loser_count"] += avoided

        classification = _classification(buy_report)
        quote_freshness = _quote_freshness_attribution(buy_report)
        for key in (
            "refresh_attempted_count",
            "refresh_applied_count",
            "still_latency_blocked_after_refresh_count",
            "latency_pass_recovered_count",
            "order_bundle_submitted_after_refresh_count",
        ):
            quote_totals[key] = _safe_int(quote_totals.get(key), 0) + _safe_int(quote_freshness.get(key), 0)
        for key in (
            "refresh_subreason_counts",
            "refresh_block_subreason_counts",
            "latency_pass_recovered_downstream_counts",
            "latency_pass_recovered_downstream_stage_counts",
        ):
            target_counter = quote_totals.get(key)
            source_counts = quote_freshness.get(key)
            if isinstance(target_counter, Counter) and isinstance(source_counts, dict):
                for label, count in source_counts.items():
                    target_counter[str(label)] += _safe_int(count, 0)

        date_rows.append(
            {
                "date": source_date,
                "buy_funnel_path": str(buy_path),
                "missed_entry_path": str(missed_path),
                "buy_funnel_loaded": bool(buy_report),
                "missed_entry_loaded": bool(missed_report),
                "stage_unique": stage_unique,
                "ratios": ratios,
                "classification_primary": classification.get("primary", "-"),
                "submit_drought_handoff_state": classification.get("submit_drought_handoff_state", "-"),
                "quote_freshness_attribution": quote_freshness,
            }
        )

    blocker_summary = {}
    for key, counter in blocker_totals.items():
        evaluated = _safe_int(counter.get("evaluated_candidates"), 0)
        missed = _safe_int(counter.get("missed_winner_count"), 0)
        avoided = _safe_int(counter.get("avoided_loser_count"), 0)
        row = {
            "evaluated_candidates": evaluated,
            "missed_winner_count": missed,
            "avoided_loser_count": avoided,
            "neutral_count": _safe_int(counter.get("neutral_count"), 0),
            "missed_winner_rate": round(missed * 100.0 / evaluated, 2) if evaluated else 0.0,
            "avoided_loser_rate": round(avoided * 100.0 / evaluated, 2) if evaluated else 0.0,
        }
        row["hurdle_decision"] = _hurdle_decision(row)
        blocker_summary[key] = row

    cohort_summary = {}
    for key, counter in cohort_totals.items():
        evaluated = _safe_int(counter.get("evaluated_candidates"), 0)
        missed = _safe_int(counter.get("missed_winner_count"), 0)
        avoided = _safe_int(counter.get("avoided_loser_count"), 0)
        row = {
            "evaluated_candidates": evaluated,
            "missed_winner_count": missed,
            "avoided_loser_count": avoided,
            "missed_winner_rate": round(missed * 100.0 / evaluated, 2) if evaluated else 0.0,
            "avoided_loser_rate": round(avoided * 100.0 / evaluated, 2) if evaluated else 0.0,
        }
        row["hurdle_decision"] = _hurdle_decision(row)
        cohort_summary[key] = row

    ai_unique = stage_totals.get("ai_confirmed", 0)
    budget_unique = stage_totals.get("budget_pass", 0)
    submitted_unique = stage_totals.get("order_bundle_submitted", 0)
    next_action_diagnostics = _next_action_diagnostics(
        stage_totals=stage_totals,
        blocker_summary=blocker_summary,
        cohort_summary=cohort_summary,
        quote_totals=quote_totals,
        window_policy=f"{start}_to_{end}",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metric_role": "funnel_count",
        "decision_authority": "entry_hurdle_backtest_report_only",
        "window_policy": f"{start}_to_{end}",
        "sample_floor": "report_only_blocker_sample_floor_3",
        "primary_decision_metric": "missed_winner_vs_avoided_loser_tradeoff",
        "source_quality_gate": "clean_baseline_allowed_existing_buy_funnel_and_missed_entry_artifacts",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "missing_artifacts": missing_artifacts,
        "summary": {
            "stage_unique_totals": dict(sorted(stage_totals.items())),
            "submitted_to_ai_unique_pct": round(submitted_unique * 100.0 / ai_unique, 2) if ai_unique else 0.0,
            "submitted_to_budget_unique_pct": round(submitted_unique * 100.0 / budget_unique, 2) if budget_unique else 0.0,
            "blocker_tradeoff": blocker_summary,
            "cohort_tradeoff": cohort_summary,
            "next_action_diagnostics": next_action_diagnostics,
        },
        "date_rows": date_rows,
    }


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def build_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Entry Hurdle Backtest {report['date']}",
        "",
        f"- runtime_effect: `{report['runtime_effect']}`",
        f"- source_dates: `{', '.join(report.get('source_dates') or []) or '-'}`",
        f"- submitted/ai unique: `{summary.get('submitted_to_ai_unique_pct', 0.0)}%`",
        f"- submitted/budget unique: `{summary.get('submitted_to_budget_unique_pct', 0.0)}%`",
        f"- missing_artifacts: `{len(report.get('missing_artifacts') or [])}`",
        "",
        "## Recommended Next Actions",
    ]
    diagnostics = summary.get("next_action_diagnostics") if isinstance(summary.get("next_action_diagnostics"), dict) else {}
    for item in diagnostics.get("recommended_next_actions") or []:
        lines.append(
            f"- `{item.get('action_id', '-')}`: priority={item.get('priority', '-')}, "
            f"decision={item.get('decision', '-')}, reason={item.get('reason', '-')}"
        )
    if not diagnostics.get("recommended_next_actions"):
        lines.append("- `none`: no overblocking action met the report-only trigger")
    lines.extend(
        [
            "",
            "## Blocker Tradeoff",
        ]
    )
    for blocker, row in (summary.get("blocker_tradeoff") or {}).items():
        lines.append(
            f"- `{blocker}`: evaluated={row.get('evaluated_candidates', 0)}, "
            f"missed={row.get('missed_winner_rate', 0.0)}%, "
            f"avoided={row.get('avoided_loser_rate', 0.0)}%, "
            f"decision={row.get('hurdle_decision', '-')}"
        )
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(str(report.get("date") or date.today().isoformat()))
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build report-only entry hurdle backtest.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print", dest="print_stdout", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_outputs(report)
        print(f"Wrote {json_path}")
        print(f"Wrote {md_path}")
    if args.print_stdout or not args.write:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
