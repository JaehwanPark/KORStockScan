"""Offline pattern-lab economics from the existing main lifecycle owner.

Display snapshots are never economic authority. No broker/API calls, policy
writes or new runtime gate live here. Missing days/rows are isolated explicitly.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, stdev

from src.engine.scalping.score_recovery_economics import (
    SCOPES,
    digest,
    economic_blockers,
    profile,
)
from src.utils.market_day import is_krx_trading_day

BASELINE = date(2026, 6, 5)
SCHEMA = "pattern_lab_real_net_v1"


def finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def trading_dates(start, end):
    start = max(date.fromisoformat(str(start)), BASELINE)
    end = date.fromisoformat(str(end))
    return [
        (start + timedelta(days=i)).isoformat()
        for i in range(max(0, (end - start).days + 1))
        if is_krx_trading_day(start + timedelta(days=i))
    ]


def verified_report(report, day):
    if not isinstance(report, dict):
        return False
    unsigned = {
        k: v
        for k, v in report.items()
        if k
        not in {"content_sha256", "report_content_sha256", "artifact_content_sha256"}
    }
    signed = {k: v for k, v in report.items() if k != "artifact_content_sha256"}
    try:
        return (
            day >= BASELINE.isoformat()
            and report.get("target_date") == day
            and report.get("schema") == "main_scalping_lifecycle_paired_daily_v2"
            and report.get("global_source_quality_gate_pass") is True
            and isinstance(report.get("rows"), list)
            and report.get("content_sha256") == digest(unsigned)
            and report.get("report_content_sha256") == digest(unsigned)
            and report.get("artifact_content_sha256") == digest(signed)
        )
    except (ValueError, TypeError, OverflowError):
        return False


def extract_rows(report, day):
    """Validate every lifecycle, excluding ALL copies of duplicate identities."""
    rows, rejected = [], Counter()
    ids = Counter(
        r.get("main_lifecycle_id")
        for r in report["rows"]
        if isinstance(r, dict) and isinstance(r.get("main_lifecycle_id"), str)
    )
    for r in report["rows"]:
        if not isinstance(r, dict):
            rejected["invalid_row"] += 1
            continue
        identity = r.get("main_lifecycle_id")
        if not isinstance(identity, str) or not identity or ids[identity] != 1:
            rejected["missing_or_duplicate_identity"] += 1
            continue
        blockers = economic_blockers(r)
        if blockers:
            rejected.update(blockers)
            continue
        notional = finite(r.get("entry_notional_krw"))
        exit_amount = finite(r.get("exit_amount_krw"))
        fees = finite(r.get("fees_taxes_krw"))
        net = finite(r.get("realized_net_pnl_krw"))
        scale_qty = finite(r.get("scale_in_fill_qty"))
        capital = finite(r.get("capital_time_krw_hours"))
        try:
            exit_at = datetime.fromisoformat(str(r.get("final_exit_at")))
            exit_time_valid = (
                exit_at.tzinfo is not None and exit_at.date().isoformat() == day
            )
        except ValueError:
            exit_time_valid = False
        if (
            r.get("trade_date") != day
            or r.get("lifecycle_population_scope") != "real_submitted"
            or r.get("right_censored") is not False
            or not exit_time_valid
            or str(r.get("fill_completion_class"))
            not in {"full_only", "partial_only", "partial_then_full"}
            or str(r.get("venue")) not in SCOPES
            or SCOPES.get(str(r.get("venue"))) != r.get("session_bucket")
            or None in (notional, exit_amount, fees, net, scale_qty)
            or notional <= 0
            or exit_amount <= 0
            or fees < 0
            or scale_qty < 0
            or not math.isclose(
                exit_amount - notional - fees, net, abs_tol=0.01, rel_tol=1e-9
            )
        ):
            rejected["unreconciled_or_nonterminal_economics"] += 1
            continue
        p = profile(r.get("score_recovery_profile"))
        if r.get("score_recovery_profile_conflict") is True or (
            r.get("score_recovery_profile") is not None and p is None
        ):
            rejected["profile_conflict"] += 1
            continue
        net = min(net, exit_amount - notional - fees)
        if finite(net / notional * 100) is None:
            rejected["nonfinite_derived_return"] += 1
            continue
        rows.append(
            {
                "identity": identity,
                "date": day,
                "venue": r["venue"],
                "session": r["session_bucket"],
                "fill_class": r["fill_completion_class"],
                "scale_class": "scale_in" if scale_qty > 0 else "initial_only",
                "profile": p,
                "profile_key": digest(p) if p else "unversioned_diagnostic_only",
                "net_krw": net,
                "notional_krw": notional,
                "net_return_pct": net / notional * 100,
                "capital_hours": (
                    capital if capital is not None and capital > 0 else None
                ),
            }
        )
    return rows, dict(rejected)


def cohort_metrics(rows, days):
    grouped = defaultdict(list)
    for r in rows:
        key = (
            r["venue"],
            r["session"],
            r["fill_class"],
            r["scale_class"],
            r["profile_key"],
        )
        grouped[key].append(r)
    result = []
    for key, group in sorted(grouped.items()):
        values = [r["net_return_pct"] for r in group]
        total = sum(r["net_krw"] for r in group)
        notional = sum(r["notional_krw"] for r in group)
        by_day = defaultdict(list)
        for r in group:
            by_day[r["date"]].append(r["net_return_pct"])
        day_values = [mean(v) for v in by_day.values()]
        # Descriptive uncertainty, not a new universal promotion hurdle.
        se = (
            max(
                stdev(values) / math.sqrt(len(values)),
                stdev(day_values) / math.sqrt(len(day_values)),
            )
            if len(day_values) >= 2
            else None
        )
        capital_complete = all(r["capital_hours"] is not None for r in group)
        capital = sum(r["capital_hours"] for r in group) if capital_complete else None
        result.append(
            {
                "cohort_id": digest(key)[:20],
                "venue": key[0],
                "session": key[1],
                "fill_class": key[2],
                "scale_class": key[3],
                "profile_key": key[4],
                "profile": group[0]["profile"],
                "completed_count": len(group),
                "outcome_day_count": len(by_day),
                "valid_source_day_count": len(days),
                "equal_weight_avg_profit_pct": mean(values),
                "notional_weighted_ev_pct": total / notional * 100,
                "net_pnl_krw": total,
                "mean_net_se_pct": se,
                "completed_per_valid_source_day": (
                    len(group) / len(days) if days else None
                ),
                "net_krw_per_valid_source_day": total / len(days) if days else None,
                "net_krw_per_capital_hour": total / capital if capital else None,
                "capital_time_status": (
                    "complete" if capital_complete else "missing_diagnostic_only"
                ),
                "diagnostic_win_rate_pct": sum(v > 0 for v in values)
                / len(values)
                * 100,
                "worst_net_return_pct": min(values),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    return result


def build_evidence(report_dir: Path, start, end):
    days = trading_dates(start, end)
    rows, sources, missing, excluded = [], {}, {}, {}
    for day in days:
        path = report_dir / f"main_scalping_lifecycle_paired_{day}.json"
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            missing[day] = "missing_or_unreadable"
            continue
        if not verified_report(report, day):
            missing[day] = "invalid_source_contract"
            continue
        selected, rejected = extract_rows(report, day)
        sources[day] = {"path": str(path), "sha256": report["artifact_content_sha256"]}
        rows.extend(selected)
        if rejected:
            excluded[day] = rejected
    # A duplicate identity across days invalidates both observations, not the
    # unrelated rows or all future dates.
    counts = Counter(r["identity"] for r in rows)
    for r in rows:
        if counts[r["identity"]] > 1:
            bucket = excluded.setdefault(r["date"], {})
            bucket["cross_date_identity_conflict"] = (
                bucket.get("cross_date_identity_conflict", 0) + 1
            )
    rows = [r for r in rows if counts[r["identity"]] == 1]
    windows = {}
    for name, window_days in (
        ("daily", days[-1:] if str(end) in days else []),
        ("rolling_10d", days[-10:]),
        ("cumulative", days),
    ):
        valid = [d for d in window_days if d in sources]
        window_rows = [r for r in rows if r["date"] in valid]
        windows[name] = {
            "expected_dates": window_days,
            "valid_source_dates": valid,
            "excluded_source_dates": [d for d in window_days if d not in sources],
            "completed_count": len(window_rows),
            "cohorts": cohort_metrics(window_rows, valid),
        }
    return {
        "schema": SCHEMA,
        "target_date": str(end),
        "basis": "actual_fill_minus_reconciled_fees_taxes_no_extra_slippage",
        "status": "available" if rows else "no_valid_economic_outcomes",
        "sources": sources,
        "excluded_source_dates": missing,
        "excluded_rows": excluded,
        "windows": windows,
        "observations": rows,
        "counterfactual_incremental_ev": None,
        "counterfactual_status": "existing_strategy_owner_evaluation_required",
        "maintenance_review_due": len(sources) >= 20
        and not any(
            c["net_pnl_krw"] > 0 and c["profile"] and c["scale_class"] == "initial_only"
            for c in windows["rolling_10d"]["cohorts"]
        ),
        "maintenance_action": "review_source_or_owner_handoff_or_retirement_not_force_buy",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def profit_followups(evidence):
    """Use winners AND losses of each cohort; never select winners only."""
    result = []
    for c in evidence["windows"]["rolling_10d"]["cohorts"]:
        if c["net_pnl_krw"] <= 0 or c["notional_weighted_ev_pct"] <= 0:
            continue
        result.append(
            {
                "title": f"net cadence cohort {c['cohort_id']}",
                "expected_effect": "Evaluate repeatable cost-adjusted profit without forcing entry",
                "risk": "Observational selection is not incremental or causal EV",
                "required_sample": "Existing strategy owner economic contract; no new lab promotion floor",
                "metric": "net_krw_per_valid_source_day and notional_weighted_ev_pct",
                "apply_stage": "report_only_observation",
                "economic_cohort": c,
                "owner_family": (
                    "score65_74_recovery_probe"
                    if c["profile"] and c["scale_class"] == "initial_only"
                    else None
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    return sorted(
        result,
        key=lambda r: (
            -r["economic_cohort"]["net_krw_per_valid_source_day"],
            r["title"],
        ),
    )
