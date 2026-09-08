"""Real, cost-reconciled score-recovery evidence shared by postclose/PREOPEN.

This is an economic eligibility check, not order authority. Existing entry,
source-quality, stage, operator veto and PREOPEN guards remain authoritative.
Actual execution prices already contain slippage; never deduct it twice.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import date

from src.engine.scalping.score_recovery_observation import finite

SCHEMA = "score_recovery_real_net_v1"
VERSION_PREFIX = "score_recovery_real_net_v1:"
PROFILE_KEYS = (
    "min_score",
    "max_score",
    "min_buy_pressure",
    "min_tick_accel",
    "min_micro_vwap_bp",
)
SCOPES = {
    "KRX": "krx_regular",
    "NXT": "nxt",
    "PREMARKET_KRX_LIKE": "krx_like_premarket",
}
POLICY_SEARCH_SCHEMA = "score_recovery_real_profile_search_v2"
# Existing bounded axes only. Scores, sizing and the effective rebound floor
# are not searched. An unseen profile never receives execution evidence.
PROFILE_SEARCH_BOUNDS = {
    "min_buy_pressure": (55.0, 75.0, 5.0),
    "min_tick_accel": (0.8, 1.5, 0.1),
    "min_micro_vwap_bp": (10.0, 20.0, 5.0),
}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("ascii")
    ).hexdigest()


def profile(values):
    if not isinstance(values, dict):
        return None
    result = {key: finite(values.get(key)) for key in PROFILE_KEYS}
    if any(value is None for value in result.values()):
        return None
    if not 60 <= result["min_score"] <= result["max_score"] <= 74:
        return None
    return result


def economic_blockers(row):
    """Do not import AI replay depth/all-stage requirements into realized PnL.

    Receipt identity, venue, final exit, cost/symbol verification, reconciliation,
    censoring and historical-recovery restrictions are NOT waived.
    """
    blockers = row.get("promotion_blockers")
    if (
        not isinstance(blockers, list)
        or any(not isinstance(v, str) for v in blockers)
        or row.get("promotion_evidence_eligible") is not (not blockers)
    ):
        return ["paired_row_contract_invalid"]
    diagnostic_only = {
        "bbo_coverage_below_95pct",
        "depth_coverage_below_90pct",
        "session_exposure_requires_interval_or_two_samples",
        "scale_in_decision_missing",
        "realized_economics_fields_missing:slippage_krw",
        "slippage_krw_exit_qty_coverage_incomplete",
        "slippage_basis_exit_qty_coverage_incomplete",
        "slippage_basis_source_exit_qty_coverage_incomplete",
    }
    return [
        b
        for b in blockers
        if b not in diagnostic_only
        and not (
            b.startswith("missing_required_stages:")
            and set(b.split(":", 1)[1].split(",")) <= {"holding", "scale_in"}
        )
    ]


def evidence_book(report, target_date):
    """Extract all eligible applied lifecycles, never a headline/top-N sample."""
    book = {
        "schema": SCHEMA,
        "observations": {},
        "partial_observations": {},
        "excluded": {},
        "source_dates": {},
    }
    if not report:
        book["excluded"] = {"paired_source_not_yet_available": 1}
        return book
    if not isinstance(report, dict):
        book["excluded"] = {"paired_source_contract_invalid": 1}
        return book
    unsigned = {
        k: v
        for k, v in report.items()
        if k
        not in {"content_sha256", "report_content_sha256", "artifact_content_sha256"}
    }
    signed = {k: v for k, v in report.items() if k != "artifact_content_sha256"}
    try:
        valid = (
            report.get("schema") == "main_scalping_lifecycle_paired_daily_v2"
            and report.get("target_date") == target_date
            and "2026-06-05" <= target_date
            and report.get("content_sha256") == digest(unsigned)
            and report.get("report_content_sha256") == digest(unsigned)
            and report.get("artifact_content_sha256") == digest(signed)
            and report.get("global_source_quality_gate_pass") is True
            and isinstance(report.get("rows"), list)
        )
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        book["excluded"] = {"paired_source_contract_invalid": 1}
        return book
    book["source_dates"][target_date] = report["artifact_content_sha256"]
    excluded = Counter()
    seen = set()
    for row in report["rows"]:
        if not isinstance(row, dict) or (
            row.get("score_recovery_profile") is None
            and row.get("score_recovery_profile_conflict") is not True
        ):
            continue
        identity = row.get("main_lifecycle_id")
        if not isinstance(identity, str) or not identity or identity in seen:
            # Duplicated identity is never silently downweighted or double counted.
            book["observations"].pop(str(identity), None)
            book["partial_observations"].pop(str(identity), None)
            excluded["duplicate_or_missing_identity"] += 1
            continue
        seen.add(identity)
        p = profile(row.get("score_recovery_profile"))
        notional = finite(row.get("entry_notional_krw"))
        exit_amount = finite(row.get("exit_amount_krw"))
        fees = finite(row.get("fees_taxes_krw"))
        net = finite(row.get("realized_net_pnl_krw"))
        capital_hours = finite(row.get("capital_time_krw_hours"))
        if (
            p is None
            or row.get("score_recovery_profile_conflict") is not False
            or row.get("trade_date") != target_date
            or economic_blockers(row)
            or row.get("lifecycle_population_scope") != "real_submitted"
            or row.get("right_censored") is not False
            or not row.get("final_exit_at")
            or row.get("scale_in_fill_qty") != 0
            or row.get("fill_completion_class")
            not in {"full_only", "partial_then_full", "partial_only"}
            or SCOPES.get(row.get("venue")) != row.get("session_bucket")
            or None in (notional, exit_amount, fees, net, capital_hours)
            or notional <= 0
            or exit_amount <= 0
            or fees < 0
            or capital_hours <= 0
            or not math.isclose(
                exit_amount - notional - fees, net, abs_tol=0.01, rel_tol=1e-9
            )
        ):
            excluded["nonterminal_mixed_or_unreconciled"] += 1
            continue
        destination = (
            "observations"
            if row["fill_completion_class"] == "full_only"
            else "partial_observations"
        )
        # Rounding tolerance must never turn zero/loss into a positive edge.
        net = min(net, exit_amount - notional - fees)
        book[destination][identity] = {
            "date": target_date,
            "profile": p,
            "venue": row["venue"],
            "session": row["session_bucket"],
            "net_krw": net,
            "notional_krw": notional,
            "capital_hours": capital_hours,
            "net_return_pct": net / notional * 100,
            "fill_class": row["fill_completion_class"],
        }
    book["excluded"] = dict(excluded)
    return book


def merge_books(books):
    result = {
        "schema": SCHEMA,
        "observations": {},
        "partial_observations": {},
        "excluded": {},
        "source_dates": {},
    }
    conflicts = set()
    excluded = Counter()
    for book in books:
        if (
            not isinstance(book, dict)
            or book.get("schema") != SCHEMA
            or any(
                not isinstance(book.get(key, {}), dict)
                for key in (
                    "excluded",
                    "source_dates",
                    "observations",
                    "partial_observations",
                )
            )
            or any(
                not isinstance(row, dict) or not isinstance(row.get("date"), str)
                for key in ("observations", "partial_observations")
                for row in book.get(key, {}).values()
            )
        ):
            excluded["book_contract_invalid"] += 1
            continue
        excluded.update(book.get("excluded") or {})
        for day, sha in (book.get("source_dates") or {}).items():
            if day in result["source_dates"] and result["source_dates"][day] != sha:
                conflicts.add(day)
            result["source_dates"][day] = sha
        for field in ("observations", "partial_observations"):
            for identity, row in (book.get(field) or {}).items():
                previous = result["observations"].get(identity) or result[
                    "partial_observations"
                ].get(identity)
                if previous is not None and previous != row:
                    conflicts.update((previous["date"], row["date"]))
                result[field][identity] = row
    for field in ("observations", "partial_observations"):
        result[field] = {
            key: row
            for key, row in result[field].items()
            if row["date"] not in conflicts
        }
    excluded["conflicting_source_dates"] += len(conflicts)
    result["excluded"] = dict(excluded)
    return result


def _evaluate(metrics, sample_floor=20):
    """Positive net edge with a dispersion margin, not a fixed profit target.

    Two-standard-error margin is a robustness screen, not a profit guarantee or
    a claimed confidence interval for correlated trading observations.
    """
    result = {
        "schema": SCHEMA,
        "ready": False,
        "state": "hold_sample",
        "reason": "real_applied_evidence_missing",
        "sample_count": 0,
        "eligible_scopes": [],
        "cohorts": [],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "primary_metric": "actual_fill_net_return_after_fees_taxes",
        "slippage_accounting": "embedded_in_actual_fill_prices_not_deducted_twice",
        "removed_gates": [
            "absolute_net_2pct",
            "close_10m_1pct",
            "mfe_10m_2pct",
            "submit_drought",
        ],
        "success_probability": None,
    }
    p = profile(metrics.get("score_recovery_current_profile"))
    book = metrics.get("score_recovery_real_economics")
    if p is None or not isinstance(book, dict) or book.get("schema") != SCHEMA:
        return result
    risk = str(metrics.get("risk_regime_gate_state") or "").lower()
    if (
        metrics.get("source_quality_blocked") is True
        or risk == "confirmed_panic"
        or any(
            marker in risk for marker in ("source_quality_blocked", "invalid", "fail")
        )
    ):
        result.update(state="source_quality_blocked", reason="risk_or_source_guard")
        return result
    result["profile"] = p
    result["profile_hash"] = digest(p)
    floor = max(20, int(sample_floor))
    observations = book.get("observations")
    if not isinstance(observations, dict):
        return result
    sources = book.get("source_dates")
    if not isinstance(sources, dict):
        return result
    try:
        for day, sha in sources.items():
            if (
                date.fromisoformat(day).isoformat() != day
                or day < "2026-06-05"
                or not isinstance(sha, str)
                or len(sha) != 64
            ):
                return result
        for row in observations.values():
            if not isinstance(row, dict) or row.get("date") not in sources:
                return result
            notional = finite(row.get("notional_krw"))
            net = finite(row.get("net_krw"))
            rate = finite(row.get("net_return_pct"))
            hours = finite(row.get("capital_hours"))
            if (
                None in (notional, net, rate, hours)
                or notional <= 0
                or hours <= 0
                or not math.isclose(net / notional * 100, rate, abs_tol=1e-8)
            ):
                return result
    except (ValueError, TypeError):
        return result
    partial = book.get("partial_observations", {})
    if not isinstance(partial, dict):
        return result
    if set(partial) & set(observations):
        return result
    if any(
        not isinstance(r, dict)
        or r.get("date") not in sources
        or r.get("fill_class") not in {"partial_only", "partial_then_full"}
        or finite(r.get("net_krw")) is None
        for r in partial.values()
    ):
        return result
    if any(r.get("fill_class") != "full_only" for r in observations.values()):
        return result
    result["natural_acceptance"] = {
        "valid_source_day_count": len(sources),
        "bounded_review_after_valid_days": 20,
        "maintenance_review_due": len(sources) >= 20,
        "next_action": "keep_collecting",
        "excluded_source_reasons": book.get("excluded", {}),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "profit_improvement_proven": False,
    }
    for venue, session in SCOPES.items():
        rows = [
            r
            for r in observations.values()
            if isinstance(r, dict)
            and r.get("profile") == p
            and r.get("venue") == venue
            and r.get("session") == session
        ]
        if not rows:
            continue
        if any(
            finite(r.get(key)) is None
            for r in rows
            for key in ("net_return_pct", "net_krw", "notional_krw", "capital_hours")
        ):
            continue
        n = len(rows)
        days = len({r["date"] for r in rows})
        values = [r["net_return_pct"] for r in rows]
        mean = math.fsum(values) / n
        se = (
            math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (n - 1) / n)
            if n > 1
            else math.inf
        )
        net = math.fsum(r["net_krw"] for r in rows)
        hours = math.fsum(r["capital_hours"] for r in rows)
        partial_rows = [
            r
            for r in partial.values()
            if isinstance(r, dict)
            and r.get("profile") == p
            and r.get("venue") == venue
            and r.get("session") == session
        ]
        partial_invalid = any(finite(r.get("net_krw")) is None for r in partial_rows)
        partial_net = (
            math.fsum(r["net_krw"] for r in partial_rows)
            if not partial_invalid
            else None
        )
        # A tiny isolated partial loss is not a whole-scope stop. Preserve
        # separate fill cohorts and compare losses with the conservative full
        # edge reserve; repeated negative partial-day evidence is a veto too.
        partial_by_day = {}
        for r in partial_rows:
            partial_by_day.setdefault(r["date"], []).append(r["net_krw"])
        partial_days = [math.fsum(v) for v in partial_by_day.values()]
        partial_mean = (
            math.fsum(partial_days) / len(partial_days) if partial_days else 0
        )
        partial_se = (
            math.sqrt(
                sum((v - partial_mean) ** 2 for v in partial_days)
                / (len(partial_days) - 1)
                / len(partial_days)
            )
            if len(partial_days) > 1
            else None
        )
        repeated_partial_loss = (
            partial_se is not None and partial_mean + 2 * partial_se < 0
        )
        full_edge_reserve = (
            max(0.0, mean - 2 * se) / 100 * math.fsum(r["notional_krw"] for r in rows)
        )
        full_edge_reserve = max(0.0, min(net, full_edge_reserve))
        partial_risk_veto = (
            partial_net is None
            or (partial_net < 0 and -partial_net >= full_edge_reserve)
            or repeated_partial_loss
        )
        ready = (
            n >= floor
            and days >= 2
            and mean - 2 * se > 0
            and net > 0
            and hours > 0
            and not partial_risk_veto
        )
        result["cohorts"].append(
            {
                "venue": venue,
                "session": session,
                "sample_count": n,
                "trade_days": days,
                "mean_net_pct": mean,
                "dispersion_margin_net_pct": mean - 2 * se if n > 1 else None,
                "net_krw": net,
                "trades_per_observed_day": n / days,
                "completed_per_valid_source_day": n / len(sources),
                "net_per_valid_source_day_krw": net / len(sources),
                "net_per_capital_hour": net / hours if hours > 0 else None,
                "partial_sample_count_diagnostic": len(partial_rows),
                "partial_net_krw_diagnostic": partial_net,
                "partial_loss_veto": partial_risk_veto,
                "partial_risk_contract": "separate_partial_loss_vs_full_edge_reserve_v2",
                "partial_loss_repeated_across_days": repeated_partial_loss,
                "full_edge_reserve_krw": full_edge_reserve,
                "ready": ready,
            }
        )
        result["sample_count"] = max(result["sample_count"], n)
        if ready:
            result["eligible_scopes"].append(venue)
    result["ready"] = bool(result["eligible_scopes"])
    if result["ready"]:
        result.update(state="adjust_up", reason="positive_repeated_real_net_edge")
    elif result["sample_count"] >= floor:
        result.update(state="hold", reason="repeatability_or_net_edge_not_demonstrated")
    result["natural_acceptance"]["next_action"] = (
        "verify_preopen_then_pid_and_real_net"
        if result["ready"]
        else (
            "review_source_or_integrate_or_retire"
            if len(sources) >= 20
            else "keep_collecting"
        )
    )
    return result


def evaluate(metrics, sample_floor=20):
    try:
        return _evaluate(metrics, sample_floor)
    except (ValueError, TypeError, OverflowError, KeyError, AttributeError):
        return {
            "schema": SCHEMA,
            "ready": False,
            "sample_count": 0,
            "state": "source_quality_blocked",
            "reason": "malformed_real_economic_contract",
            "eligible_scopes": [],
            "cohorts": [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }


def approval_version(metrics, sample_floor=20):
    decision = evaluate_policy(metrics, sample_floor)
    if not decision["ready"]:
        raise ValueError("score_recovery_economics_not_ready")
    return (
        VERSION_PREFIX
        + decision["profile_hash"]
        + ":"
        + ",".join(decision["eligible_scopes"])
    )


def _bounded_profile_change(current, proposed):
    changed = [k for k in PROFILE_KEYS if proposed[k] != current[k]]
    if len(changed) != 1 or changed[0] not in PROFILE_SEARCH_BOUNDS:
        return False
    key = changed[0]
    low, high, step = PROFILE_SEARCH_BOUNDS[key]
    return (
        low <= proposed[key] <= high
        and abs(proposed[key] - current[key]) <= step + 1e-9
        and proposed["min_micro_vwap_bp"] >= 10
    )


def _profile_period_stats(book, p, venue, days):
    rows = [
        r
        for r in book["observations"].values()
        if r["profile"] == p
        and r["venue"] == venue
        and r.get("session") == SCOPES[venue]
        and r["date"] in days
    ]
    partial_rows = [
        r
        for r in book["partial_observations"].values()
        if r.get("profile") == p
        and r.get("venue") == venue
        and r.get("session") == SCOPES[venue]
        and r.get("date") in days
    ]
    partial_net = math.fsum(r["net_krw"] for r in partial_rows)
    full_net = math.fsum(r["net_krw"] for r in rows)
    hours = [finite(r.get("capital_hours")) for r in [*rows, *partial_rows]]
    capital = (
        math.fsum(hours)
        if hours and all(h is not None and h > 0 for h in hours)
        else None
    )
    return {
        "count": len(rows),
        "net_per_source_day": (full_net + partial_net) / len(days),
        "full_net_per_source_day": full_net / len(days),
        "partial_net_per_source_day": partial_net / len(days),
        "net_ev_scope": "full_only_not_pooled_with_partial",
        "completed_per_source_day": len(rows) / len(days),
        "capital_time_krw_hours": capital,
        "net_per_capital_time": (
            (full_net + partial_net) / capital if capital else None
        ),
        "net_ev_pct": (
            (
                math.fsum(r["net_krw"] for r in rows)
                / math.fsum(r["notional_krw"] for r in rows)
                * 100
            )
            if rows
            else None
        ),
    }


def _cadence_economics_improved(before, after, *, strict=True):
    """Small profitable fills may trade more often; extra capital is not alpha.

    Full-only positive net EV remains required. Total net includes separately
    reconciled partial fills, including their capital-time denominator.
    Existing dispersion, sample, partial-loss and holdout guards stay intact.
    """
    if not before["count"] or not after["count"]:
        return False
    old_eff = before["net_per_capital_time"]
    new_eff = after["net_per_capital_time"]
    if old_eff is None or new_eff is None or after["net_ev_pct"] <= 0:
        return False
    old_net = max(0, before["net_per_source_day"])
    new_net = after["net_per_source_day"]
    return (
        (new_net > old_net if strict else new_net >= old_net)
        and new_eff >= max(0, old_eff)
        and (not strict or not math.isclose(new_eff, max(0, old_eff), rel_tol=1e-9))
    )


def _evaluate_policy(metrics, sample_floor=20):
    """Bounded reselection of actually traded profiles, not invented BUY fills.

    Fit ranks on the early half of source dates; only the one frozen winner is
    checked on the later half. Both halves retain losses and zero-trade days.
    Observational version comparison is NOT a causal treatment-effect claim.
    The existing PREOPEN/AI/lock/safety owners remain in charge of application.
    """
    baseline = evaluate(metrics, sample_floor)
    search = {
        "schema": POLICY_SEARCH_SCHEMA,
        "status": "no_supported_alternative_profile",
        "comparison_basis": "observed_real_profiles_not_causal_counterfactual",
        "selection_objective": "positive_full_net_ev_and_net_per_source_day_with_non_degrading_capital_efficiency",
        "candidate_count": 0,
        "selected_profile": None,
        "candidate_ledger": [],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    baseline["policy_search"] = search
    current = profile(metrics.get("score_recovery_current_profile"))
    book = metrics.get("score_recovery_real_economics")
    if (
        current is None
        or not isinstance(book, dict)
        or "natural_acceptance" not in baseline
    ):
        search["status"] = "source_contract_not_ready"
        return baseline
    days = sorted(book["source_dates"])
    if len(days) < 2:
        search["status"] = "source_window_not_mature"
        return baseline
    train, holdout = days[: len(days) // 2], days[len(days) // 2 :]
    search.update(
        source_dates=days,
        train_dates=train,
        holdout_dates=holdout,
        source_book_sha256=digest(book),
        current_profile=current,
    )
    profiles = {}
    for row in book["observations"].values():
        p = profile(row.get("profile"))
        if p is not None and _bounded_profile_change(current, p):
            profiles[digest(p)] = p
    ranked = []
    for key, p in sorted(profiles.items()):
        candidate = evaluate(
            {**metrics, "score_recovery_current_profile": p}, sample_floor
        )
        entry = {
            "candidate_id": "score-profile-" + key[:20],
            "profile": p,
            "sample_count": candidate["sample_count"],
            "status": "hold_economic_evidence",
            "training_comparisons": [],
            "comparisons": [],
        }
        search["candidate_ledger"].append(entry)
        # Do not select a runner-up using knowledge of holdout outcomes.
        for venue in SCOPES:
            before = _profile_period_stats(book, current, venue, train)
            after = _profile_period_stats(book, p, venue, train)
            entry["training_comparisons"].append(
                {"venue": venue, "baseline": before, "candidate": after}
            )
            if not before["count"] or not after["count"]:
                continue
            if (
                before["net_per_capital_time"] is None
                or after["net_per_capital_time"] is None
            ):
                entry["status"] = "comparison_capital_time_missing"
                continue
            delta = after["net_per_source_day"] - before["net_per_source_day"]
            if _cadence_economics_improved(before, after):
                ranked.append((delta, key, venue, p, candidate, entry))
                entry["status"] = "train_candidate"
    search["candidate_count"] = len(profiles)
    if not ranked:
        search["status"] = (
            "comparison_source_incomplete"
            if any(
                e["status"] == "comparison_capital_time_missing"
                for e in search["candidate_ledger"]
            )
            else "no_training_improvement" if profiles else search["status"]
        )
        return baseline
    _, key, venue, p, candidate, entry = sorted(
        ranked, key=lambda v: (-v[0], v[1], v[2])
    )[0]
    before = _profile_period_stats(book, current, venue, holdout)
    after = _profile_period_stats(book, p, venue, holdout)
    comparison = {
        "venue": venue,
        "baseline": before,
        "candidate": after,
        "observed_incremental_net_per_source_day": after["net_per_source_day"]
        - before["net_per_source_day"],
    }
    entry["comparisons"].append(comparison)
    passed = (
        candidate["ready"]
        and venue in candidate["eligible_scopes"]
        and _cadence_economics_improved(before, after)
    )
    # One env profile is shared by the scoped runtime consumer. A KRX-only
    # improvement must not silently drop an already eligible NXT scope.
    required_scopes = sorted(set(baseline["eligible_scopes"]) | {venue})
    for other in sorted(set(required_scopes) - {venue}):
        old = _profile_period_stats(book, current, other, holdout)
        new = _profile_period_stats(book, p, other, holdout)
        passed = passed and (
            other in candidate["eligible_scopes"]
            and _cadence_economics_improved(old, new, strict=False)
        )
        entry["comparisons"].append({"venue": other, "baseline": old, "candidate": new})
    entry["status"] = "selected_observed_profile" if passed else "holdout_not_improved"
    search["status"] = entry["status"]
    if not passed:
        return baseline
    search.update(
        selected_profile=p,
        selected_candidate_id=entry["candidate_id"],
        eligible_scopes=required_scopes,
    )
    candidate.update(
        policy_search=search,
        eligible_scopes=required_scopes,
        reason="bounded_observed_profile_improved_on_holdout",
    )
    return candidate


def evaluate_policy(metrics, sample_floor=20):
    try:
        return _evaluate_policy(metrics, sample_floor)
    except (ValueError, TypeError, OverflowError, KeyError, AttributeError):
        result = evaluate({}, sample_floor)
        result.update(
            state="source_quality_blocked", reason="malformed_profile_search_contract"
        )
        result["policy_search"] = {
            "schema": POLICY_SEARCH_SCHEMA,
            "status": "source_contract_not_ready",
            "candidate_count": 0,
            "selected_profile": None,
            "candidate_ledger": [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        return result


def policy_search_digest(metrics, sample_floor=20):
    return digest(evaluate_policy(metrics, sample_floor)["policy_search"])


def runtime_profile(rule):
    values = {
        key: rule("AI_SCORE65_74_RECOVERY_PROBE_" + key.upper(), default)
        for key, default in zip(PROFILE_KEYS, (60, 74, 65.0, 1.2, 0.0))
    }
    floor = finite(
        rule("AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP", 10.0)
    )
    micro = finite(values["min_micro_vwap_bp"])
    values["min_micro_vwap_bp"] = (
        max(micro, floor) if micro is not None and floor is not None else None
    )
    return profile(values)


def runtime_scope_allowed(version, values, scope):
    # Existing operator override versions retain their separately owned contract.
    if not str(version).startswith("score_recovery_real_net"):
        return True
    p = profile(values)
    parts = str(version).split(":")
    return bool(
        len(parts) == 3
        and parts[0] + ":" == VERSION_PREFIX
        and p is not None
        and parts[1] == digest(p)
        and parts[2]
        and all(v in SCOPES for v in parts[2].split(","))
        and scope.get("effective_venue") in parts[2].split(",")
        and SCOPES.get(scope.get("effective_venue"))
        == scope.get("market_session_bucket")
    )
