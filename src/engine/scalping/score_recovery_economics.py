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
        partial_risk_veto = partial_net is None or partial_net < 0
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
    decision = evaluate(metrics, sample_floor)
    if not decision["ready"]:
        raise ValueError("score_recovery_economics_not_ready")
    return (
        VERSION_PREFIX
        + decision["profile_hash"]
        + ":"
        + ",".join(decision["eligible_scopes"])
    )


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
