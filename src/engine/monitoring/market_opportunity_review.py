"""Pure diagnostics for the external census; no market-data or order calls.

The monitoring package owns this report projection, not the live scanner.
Valid contiguous capture windows can be diagnosed independently of incomplete
windows and economic promotion. No projection grants live authority.
"""

import hashlib
import json
from collections import Counter, defaultdict
from datetime import timedelta

from src.engine.sniper_time import scalping_same_session_entry_cutoff_blocked


def scope_exclusion(row, parse_ts):
    """Exclude only an immutable guard, never infer a historical PID's windows.

    Clock-derived strategy cohorts are not physical quote venues. In particular
    NXT overlap coverage cannot prove what the main KRX strategy should trade.
    Keep those rows in the broad census with an explicit unresolved scope.
    """
    anchor = parse_ts(row.get("first_census_at"))
    if anchor is None:
        return "invalid_opportunity_time"
    if scalping_same_session_entry_cutoff_blocked(anchor):
        return "intended_new_buy_hard_cutoff"
    if row.get("session") == "NXT_REGULAR_OVERLAP":
        return "main_overlap_route_policy_unproven"
    if str(row.get("session") or "").startswith("OUTSIDE_"):
        return "outside_supported_market_session"
    return None


def report_sha256(report):
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in report.items() if k != "artifact_sha256"},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def decision_disposition(fields):
    """An advisory snapshot is not a successful submit authorization."""
    chosen = str(fields.get("chosen_action") or "").upper()
    decision = str(
        fields.get("effective_decision") or fields.get("decision") or ""
    ).upper()
    allowed = fields.get("allowed")
    if (
        allowed is False
        or str(allowed).lower() == "false"
        or decision.startswith("REJECT")
    ):
        return "rejected"
    if chosen in {
        "NO_BUY_AI",
        "SKIP_STALE",
        "SKIP_SOURCE_QUALITY",
        "SKIP_PRE_SUBMIT_SAFETY",
    }:
        return "rejected"
    if (
        chosen == "WAIT_REQUOTE"
        or str(fields.get("entry_action_final_decision") or "").upper()
        == "OBSERVE_ONLY"
    ):
        return "observe_only"
    if fields.get("decision_authority") == "entry_advisory_prompt_context_only":
        return "advisory_only"
    # Missing/unknown booleans are not positive authority.
    if allowed is True or str(allowed).lower() == "true":
        return "allowed"
    return "unresolved"


def scoped_diagnostics(
    rows,
    snapshots,
    *,
    parse_ts,
    summarize,
    master_valid,
    trigger_valid,
    validity_sec=300,
    max_gap_sec=360,
    capture_floor=3,
    sample_floor=20,
):
    """Isolate missing master rows and broken capture intervals, never backfill.

    An interval needs actual, hashed primary-panel captures. The last capture
    must close the opportunity validity window; future scheduled captures and
    another venue's watermark cannot close it. Daily limitations remain visible.
    """
    grouped = defaultdict(list)
    captures = defaultdict(set)
    for row in rows:
        grouped[(row["venue"], row["session"])].append(row)
    for snapshot in snapshots:
        if snapshot.get("panel") != "liquid_common":
            continue
        key = (snapshot.get("venue"), snapshot.get("session"))
        if not all(key) or str(key[1]).startswith("OUTSIDE_"):
            continue
        captures.setdefault(key, set())
        if snapshot.get("source_quality_status") == "ok" and (
            snapshot.get("source") or {}
        ).get("normalized_source_payload_sha256"):
            ts = parse_ts(snapshot.get("captured_at"))
            if ts is not None:
                captures[key].add(ts)
    result = {}
    for key in sorted(grouped.keys() | captures.keys()):
        islands = []
        for ts in sorted(captures[key]):
            if not islands or (ts - islands[-1][-1]).total_seconds() > max_gap_sec:
                islands.append([])
            islands[-1].append(ts)
        intervals = [
            (part[0], part[-1]) for part in islands if len(part) >= capture_floor
        ]
        eligible = []
        excluded = Counter()
        for row in grouped[key]:
            anchor = parse_ts(row.get("first_census_at"))
            if not master_valid or not trigger_valid:
                excluded["global_source_contract_missing"] += 1
            elif (
                row.get("symbol_master_status") != "verified"
                or row.get("instrument_type") != "EQUITY"
                or row.get("listing_market") not in {"KOSPI", "KOSDAQ"}
            ):
                excluded["master_unverified_or_not_common_equity"] += 1
            elif scope_exclusion(row, parse_ts):
                excluded[scope_exclusion(row, parse_ts)] += 1
            elif anchor not in captures[key] or not any(
                start <= anchor and anchor + timedelta(seconds=validity_sec) <= end
                for start, end in intervals
            ):
                excluded["capture_gap_or_pending_validity_window"] += 1
            else:
                eligible.append(row)
        summary = summarize(eligible)
        count = len(eligible)
        ready = master_valid and trigger_valid and count >= sample_floor
        timely = [r for r in eligible if r.get("scanner_detection_sla_met") is True]
        handoff_gaps = sum(
            not all(
                (r.get("stage_reached") or {}).get(s)
                for s in ("runtime_watch_attached", "fast_precheck", "heavy_eval")
            )
            for r in timely
        )
        reasons = dict(
            sorted(
                Counter(
                    r.get("terminal_coverage_reason", "unknown") for r in eligible
                ).items()
            )
        )
        result["|".join(key)] = {
            "status": (
                "diagnostic_ready" if ready else "insufficient_evidence_scanner_recall"
            ),
            "whole_market_coverage_claim_allowed": False,
            "scope": "verified_common_equity_contiguous_primary_capture_windows_only",
            "source_fetch_pool_visibility": (
                "partial_exact_adapter_pool_receipts_not_raw_api_universe"
                if any(
                    r.get("source_fetch_observed_exact")
                    or r.get("candidate_pool_observed_exact")
                    for r in eligible
                )
                else "promotion_prune_proxy_not_full_fetch_pool_census"
            ),
            "exact_fetch_episode_count": sum(
                r.get("source_fetch_observed_exact") is True for r in eligible
            ),
            "exact_pool_episode_count": sum(
                r.get("candidate_pool_observed_exact") is True for r in eligible
            ),
            "scope_contract": "hard_cutoff_excluded_exact_runtime_windows_not_assumed",
            "runtime_buy_window_receipt_verified": False,
            "raw_episode_count": len(grouped[key]),
            "eligible_episode_count": count,
            "excluded_episode_count": sum(excluded.values()),
            "exclusion_counts": dict(excluded),
            "conservation_delta": len(grouped[key]) - count - sum(excluded.values()),
            "eligible_episode_ids": [r["opportunity_episode_id"] for r in eligible],
            "valid_capture_intervals": [
                {"start": a.isoformat(), "end": b.isoformat()} for a, b in intervals
            ],
            "discovery": summary,
            "post_promotion": {
                "denominator_timely_promotions": len(timely),
                "attach_fast_heavy_handoff_gap_count": handoff_gaps,
            },
            "terminal_reason_counts": reasons,
            "economic_status": (
                "source_only_evidence_ready"
                if summary["ex_post_executable_opportunity"][
                    "economic_evidence_floor_met"
                ]
                else "insufficient_economic_evidence"
            ),
            "economic_floor_is_discovery_gate": False,
            "next_action": (
                "repair_capture_or_master_then_review_scoped_funnel"
                if not ready
                else "review_first_missing_owner_and_intended_exclusions_without_relaxing_guards"
            ),
        }
    return {
        "schema_version": "market_opportunity_scoped_review_v2",
        "metric_role": "funnel_count",
        "decision_authority": "source_only_scanner_coverage_audit",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "primary_decision_metric": "promotion_recall_pct",
        "window_policy": "venue_session_contiguous_primary_capture_intervals",
        "sample_floor": {
            "captures_per_interval": capture_floor,
            "episodes_per_scope": sample_floor,
        },
        "source_quality_gate": "official_master_exact_hashed_capture_and_installed_trigger",
        "forbidden_uses": [
            "whole_market_recall_extrapolation",
            "live_runtime_apply",
            "guard_relaxation",
        ],
        "by_venue_session": result,
    }


def diagnostic_followups(scoped, target_date):
    """Native, stable source-only requests for the existing workorder consumer."""
    return [
        {
            "recommendation_id": "market_census_" + scope.replace("|", "_").lower(),
            "target_date": target_date,
            "scope": scope,
            "decision": "objective_followup_required",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "owner": "scanner_recall_instrumentation",
            "intended_consumer": "code_improvement_workorder",
            "implementation_scope": "source_only_parser_report_instrumentation",
            "acceptance": "exact first blocker and isolated capture-window conservation; no live changes",
            "files_likely_touched": [
                "src/engine/monitoring/market_opportunity_census.py",
                "src/engine/monitoring/market_opportunity_review.py",
                "src/scanners/scanner_source_census.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_market_opportunity_review.py src/tests/test_scanner_source_census.py",
                "hard-cutoff exclusions, exact premarket route, first missing stage and source receipt conservation remain non-live",
            ],
            "required_downstream": ["code_improvement_workorder"],
            "reason": summary["next_action"],
            "evidence": {
                k: summary[k]
                for k in (
                    "status",
                    "raw_episode_count",
                    "eligible_episode_count",
                    "exclusion_counts",
                    "terminal_reason_counts",
                )
            },
        }
        for scope, summary in scoped["by_venue_session"].items()
        if summary["excluded_episode_count"]
        or summary["terminal_reason_counts"].keys() - {"submitted"}
    ]
