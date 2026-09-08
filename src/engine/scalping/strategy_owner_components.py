"""Existing Entry/holding policy components, not additional strategy owners.

Migration preserves the effective settings. Economic changes use only observed,
cost-reconciled real profiles within one venue/session and one changed parameter.
No order, provider, process, or original operator-file mutation is performed here.
"""

from __future__ import annotations

import json
import gzip
import math
import os
import re
from collections import Counter, defaultdict
from functools import lru_cache
from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.engine.scalping.score_recovery_economics import digest, economic_blockers

SCHEMA = "strategy_owner_components_v1"
EFFECTIVE_DATE = "2026-09-09"
ENV_KEY = "KORSTOCKSCAN_STRATEGY_OWNER_COMPONENTS_JSON"
CONTEXT_SCHEMA = "strategy_owner_decision_context_v2"
SOURCE_WINDOW = "rolling_20d"
# These reviewed output/retention controls cannot change an entry/exit decision.
# Keep unknown fields in the fingerprint: broad LOG/SIM prefix exemptions could
# accidentally erase a decision, cadence or shared-resource guard.
NON_DECISION_RULES = frozenset(
    {
        "MODULE_LOG_MAX_BYTES",
        "MODULE_LOG_BACKUP_COUNT",
        "LOG_RETENTION_DAYS",
        "BOT_HISTORY_BACKUP_COUNT",
        "PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED",
        "PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST",
        "WATCHING_STATE_DEBUG_LOG_ENABLED",
    }
)
WEAK = "weak_pullback_entry_block_runtime"
PROFIT = "profit_stagnation_exit_runtime"
OWNERS = {WEAK: "entry_gate_recheck", PROFIT: "holding_exit"}
STAGES = {WEAK: "entry_pre_submit", PROFIT: "holding_exit"}
PREFIX = "KORSTOCKSCAN_"
DEFAULTS = {
    WEAK: {
        "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED": "false",
        "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES": "2",
        "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_SPREAD_TICKS": "5",
    },
    PROFIT: {
        "SCALP_PROFIT_STAGNATION_EXIT_ENABLED": "false",
        "SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT": "1.0",
        "SCALP_PROFIT_STAGNATION_MIN_SEC": "180",
        "SCALP_PROFIT_STAGNATION_MAX_PROFIT_MOVE_PCT": "0.15",
        "SCALP_PROFIT_STAGNATION_MAX_PEAK_IMPROVE_PCT": "0.10",
        "SCALP_PROFIT_STAGNATION_MIN_AI_SCORE": "45",
        "SCALP_LOW_PROFIT_STAGNATION_HARD_EXIT_ENABLED": "false",
        "SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT": "0.20",
        "SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT": "1.00",
        "SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC": "1800",
        "SCALP_LOW_PROFIT_STAGNATION_ASSUMED_EXIT_SLIPPAGE_BPS": "15",
    },
}
KEYS = {
    family: frozenset(PREFIX + k for k in values) for family, values in DEFAULTS.items()
}
ALL_KEYS = frozenset().union(*KEYS.values())
# Only the existing economic conditions are adjustable. Enables, cost assumptions,
# score priors and safety are not optimized. These are maximum step sizes, not
# recommended values or a new minimum-profit requirement.
STEPS = {
    "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES": 1,
    "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_SPREAD_TICKS": 1,
    "SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT": 0.05,
    "SCALP_PROFIT_STAGNATION_MIN_SEC": 30,
    "SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT": 0.05,
    "SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT": 0.05,
    "SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC": 300,
}
SCOPES = {
    "KRX": "krx_regular",
    "NXT": "nxt",
    "PREMARKET_KRX_LIKE": "krx_like_premarket",
}
_FROZEN_RULE_CACHE = None


def valid_scope(venue, session):
    """Preserve exact runtime sessions; never pool them into a generic NXT arm."""
    if not isinstance(venue, str) or not isinstance(session, str):
        return False
    if venue == "NXT":
        return session in {
            "nxt",
            "nxt_entry_window",
            "nxt_premarket",
            "nxt_regular_overlap",
            "nxt_aftermarket",
        }
    return venue in SCOPES and SCOPES[venue] == session


def stock_scope(stock):
    """Use explicit target provenance, without clock or cross-session inference."""
    source = stock if isinstance(stock, dict) else {}
    if not any(source.get(key) for key in ("venue", "effective_venue")):
        source = source.get("_scanner_fast_precheck_fields") or {}
    if not isinstance(source, dict):
        return None, None
    venues = {
        str(source[key]).strip().upper()
        for key in ("venue", "effective_venue")
        if source.get(key)
    }
    venue = next(iter(venues)) if len(venues) == 1 else None
    session = source.get("market_session_bucket")
    return (venue, session) if valid_scope(venue, session) else (None, None)


def profile(family, values):
    if (
        family not in DEFAULTS
        or not isinstance(values, dict)
        or set(values) != set(DEFAULTS[family])
    ):
        return None
    result = {}
    for key, value in values.items():
        if key.endswith("_ENABLED"):
            raw = str(value).lower()
            if raw not in {"true", "false", "1", "0"}:
                return None
            result[key] = raw in {"true", "1"}
        else:
            if isinstance(value, bool):
                return None
            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError):
                return None
            if not math.isfinite(number) or number <= 0:
                return None
            if key.endswith(("_SEC", "_TICKS", "_POSITIVES")) and (
                number != int(number) or number < 1
            ):
                return None
            result[key] = number
    if (
        family == PROFIT
        and result["SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT"]
        > result["SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT"]
    ):
        return None
    return result


def runtime_profiles(rules):
    return {
        family: profile(
            family, {key: getattr(rules, key, value) for key, value in defaults.items()}
        )
        for family, defaults in DEFAULTS.items()
    }


def context_fingerprint(rules):
    # Other rule changes must not inherit a component's economic comparison.
    values = vars(rules) if hasattr(rules, "__dict__") else {}
    excluded = {
        k for defaults in DEFAULTS.values() for k in defaults
    } | NON_DECISION_RULES
    try:
        return digest(
            {
                "schema": CONTEXT_SCHEMA,
                "rules": {
                    k: v
                    for k, v in values.items()
                    if k.isupper()
                    and k not in excluded
                    and isinstance(
                        v, (str, int, float, bool, list, tuple, dict, type(None))
                    )
                },
            }
        )
    except (TypeError, ValueError, OverflowError):
        # An instrumentation gap must not become an accidental order veto.
        return None


@lru_cache(maxsize=8)
def _parse_bundle(raw):
    return json.loads(raw)


def _runtime_baseline(rules):
    global _FROZEN_RULE_CACHE
    frozen = getattr(
        getattr(type(rules), "__dataclass_params__", None), "frozen", False
    )
    if frozen and _FROZEN_RULE_CACHE and _FROZEN_RULE_CACHE[0] is rules:
        return _FROZEN_RULE_CACHE[1:]
    profiles, context = runtime_profiles(rules), context_fingerprint(rules)
    if frozen:
        _FROZEN_RULE_CACHE = (rules, profiles, context)
    return profiles, context


def valid_canary(policy, today):
    """The loader and live helper share the same finite first-use contract."""
    try:
        start = date.fromisoformat(policy["canary_start_date"])
        end = date.fromisoformat(policy["canary_until_date"])
        return (
            policy.get("mode") == "first_use_bounded_canary"
            and policy["canary_start_date"] <= today <= policy["canary_until_date"]
            and (end - start).days == 6
            and policy.get("canary_max_calendar_days") == 7
            and policy.get("real_promotion_required") is True
            and policy.get("runtime_safety_and_quantity_unchanged") is True
            and type(policy.get("real_full_fill_sample_count")) is int
            and policy["real_full_fill_sample_count"] >= 20
            and policy.get("sample_floor") == 10
            and re.fullmatch(r"[a-f0-9]{64}", str(policy.get("trial_id", "")))
            is not None
            and len(set(policy["source_dates"])) >= 2
            and all(
                "2026-06-05" <= d < policy["canary_start_date"]
                for d in policy["source_dates"]
            )
            and all(
                isinstance(policy.get(k), dict)
                and len(policy[k]) >= 2
                and all(
                    d in policy["source_dates"]
                    and re.fullmatch(r"[a-f0-9]{64}", str(h))
                    for d, h in policy[k].items()
                )
                for k in ("replay_sources", "real_sources")
            )
        )
    except (ValueError, TypeError, KeyError, OverflowError):
        return False


def runtime_state(
    rules,
    *,
    venue,
    session,
    score_profile=None,
    simulated=False,
    environment=None,
    today=None,
):
    profiles, context = _runtime_baseline(rules)
    result = {
        "profiles": profiles,
        "context_sha256": context,
        "status": "baseline",
        "applied_families": [],
        "managed_families": [],
    }
    if simulated:
        return result
    environment = os.environ if environment is None else environment
    raw = environment.get(ENV_KEY)
    if not raw:
        return result
    today = today or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    try:
        bundle = _parse_bundle(raw)
        if (
            bundle.get("schema") != SCHEMA
            or bundle.get("target_date") != today
            or today < EFFECTIVE_DATE
        ):
            raise ValueError("stale_component_bundle")
        for component in bundle["components"]:
            family = component["family"]
            if family not in OWNERS or component.get("owner") != OWNERS[family]:
                raise ValueError("component_owner_invalid")
            if profile(family, component["baseline"]) != profiles[family]:
                continue  # An explicit effective operator change wins.
            result["managed_families"].append(family)
            for policy in component["policies"]:
                if policy.get("mode") not in (None, "first_use_bounded_canary"):
                    raise ValueError("unknown_component_policy_mode")
                if policy.get(
                    "mode"
                ) == "first_use_bounded_canary" and not valid_canary(policy, today):
                    continue
                if (
                    policy["venue"] == venue
                    and policy["session"] == session
                    and valid_scope(venue, session)
                    and policy.get("context_sha256") == context
                    and policy.get("score_profile") == score_profile
                    and all(
                        result["profiles"].get(k) == v
                        for k, v in policy["other_profiles"].items()
                    )
                    and bounded_change(family, policy["baseline"], policy["profile"])
                ):
                    result["profiles"] = {
                        **result["profiles"],
                        family: policy["profile"],
                    }
                    result["status"] = (
                        "first_use_bounded_canary"
                        if policy.get("mode") == "first_use_bounded_canary"
                        else "verified_scoped_policy"
                    )
                    result["applied_families"].append(family)
    except (TypeError, ValueError, KeyError, AttributeError):
        return {
            "profiles": profiles,
            "context_sha256": context,
            "status": "invalid_policy_baseline_retained",
            "applied_families": [],
            "managed_families": [],
        }
    return result


def bounded_change(family, before, after):
    before, after = profile(family, before), profile(family, after)
    if before is None or after is None:
        return False
    changed = [key for key in before if before[key] != after[key]]
    return (
        len(changed) == 1
        and changed[0] in STEPS
        and 0 < abs(after[changed[0]] - before[changed[0]]) <= STEPS[changed[0]] + 1e-9
    )


def evidence_book(report, target_date):
    book = {"schema": SCHEMA, "rows": {}, "sources": {}, "excluded": {}}
    if not isinstance(report, dict) or not report:
        book["excluded"] = {"paired_source_missing": 1}
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
            and report.get("global_source_quality_gate_pass") is True
            and report.get("content_sha256")
            == report.get("report_content_sha256")
            == digest(unsigned)
            and report.get("artifact_content_sha256") == digest(signed)
            and isinstance(report.get("rows"), list)
        )
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        book["excluded"] = {"paired_source_invalid": 1}
        return book
    book["sources"][target_date] = report["artifact_content_sha256"]
    excluded, seen = Counter(), set()
    for row in report["rows"]:
        if not isinstance(row, dict):
            excluded["invalid_row"] += 1
            continue
        identity = row.get("main_lifecycle_id")
        if not isinstance(identity, str) or not identity or identity in seen:
            book["rows"].pop(identity if isinstance(identity, str) else "", None)
            excluded["duplicate_or_missing_identity"] += 1
            continue
        seen.add(identity)
        profiles = row.get("strategy_owner_profiles")
        if (
            not isinstance(profiles, dict)
            or set(profiles) != set(OWNERS)
            or row.get("strategy_owner_profile_conflict") is not False
        ):
            excluded["component_profile_missing_or_conflicting"] += 1
            continue
        profiles = {
            family: profile(family, values) for family, values in profiles.items()
        }
        values = [
            row.get(k)
            for k in (
                "entry_notional_krw",
                "exit_amount_krw",
                "fees_taxes_krw",
                "realized_net_pnl_krw",
                "capital_time_krw_hours",
            )
        ]
        if (
            any(p is None for p in profiles.values())
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or economic_blockers(row)
            or row.get("trade_date") != target_date
            or row.get("lifecycle_population_scope") != "real_submitted"
            or row.get("right_censored") is not False
            or not row.get("final_exit_at")
            or row.get("scale_in_fill_qty") != 0
            or row.get("score_recovery_profile_conflict") is not False
            or row.get("fill_completion_class") != "full_only"
            or not valid_scope(row.get("venue"), row.get("session_bucket"))
            or row.get("venue") not in SCOPES
        ):
            excluded["nonterminal_partial_or_invalid_economics"] += 1
            continue
        context = row.get("strategy_owner_context_sha256")
        if not isinstance(context, str) or not re.fullmatch(r"[a-f0-9]{64}", context):
            excluded["runtime_context_missing"] += 1
            continue
        notional, amount, fees, net, capital = values
        if (
            notional <= 0
            or amount <= 0
            or fees < 0
            or capital <= 0
            or not math.isclose(
                amount - notional - fees, net, abs_tol=0.01, rel_tol=1e-9
            )
        ):
            excluded["cost_reconciliation_failed"] += 1
            continue
        book["rows"][identity] = {
            "date": target_date,
            "profiles": profiles,
            "venue": row["venue"],
            "session": row["session_bucket"],
            "score_profile": row.get("score_recovery_profile"),
            "context_sha256": context,
            "net": min(net, amount - notional - fees),
            "notional": notional,
            "capital": capital,
        }
    book["excluded"] = dict(excluded)
    return book


def merge_books(books):
    result = {
        "schema": SCHEMA,
        "rows": {},
        "sources": {},
        "excluded": {},
        "replays": {},
        "replay_sources": {},
    }
    conflicts, excluded = set(), Counter()
    for book in books:
        if not isinstance(book, dict) or book.get("schema") != SCHEMA:
            excluded["book_contract_invalid"] += 1
            continue
        excluded.update(book.get("excluded", {}))
        for day, sha in book.get("replay_sources", {}).items():
            if day in result["replay_sources"] and result["replay_sources"][day] != sha:
                conflicts.add(day)
            result["replay_sources"][day] = sha
        for identity, row in book.get("replays", {}).items():
            old = result["replays"].get(identity)
            if old is not None and old != row:
                conflicts.update((old["date"], row["date"]))
            result["replays"][identity] = row
        for day, sha in book.get("sources", {}).items():
            if day in result["sources"] and result["sources"][day] != sha:
                conflicts.add(day)
            result["sources"][day] = sha
        for identity, row in book.get("rows", {}).items():
            old = result["rows"].get(identity)
            if old and old != row:
                conflicts.update((old["date"], row["date"]))
            result["rows"][identity] = row
    result["rows"] = {
        k: v for k, v in result["rows"].items() if v["date"] not in conflicts
    }
    result["replays"] = {
        k: v for k, v in result["replays"].items() if v["date"] not in conflicts
    }
    excluded["conflicting_source_dates"] += len(conflicts)
    result["excluded"] = dict(excluded)
    return result


def verify_research(book, report_dir, target_date):
    """Rebuild the compact book from exact signed producer generations."""
    if not book:
        return None
    if (
        not isinstance(book, dict)
        or book.get("schema") != SCHEMA
        or not isinstance(book.get("sources"), dict)
        or not isinstance(book.get("replay_sources", {}), dict)
        or not set(book.get("replay_sources", {})).issubset(book["sources"])
    ):
        raise ValueError("owner_component_research_invalid")
    books = []
    for day in book["sources"]:
        if (
            not isinstance(day, str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day)
            or not "2026-06-05" <= day < target_date
        ):
            raise ValueError("owner_component_source_date_invalid")
        date.fromisoformat(day)
        path = (
            report_dir
            / "main_scalping_lifecycle_paired"
            / f"main_scalping_lifecycle_paired_{day}.json"
        )
        if path.exists():
            payload = json.loads(path.read_text())
        else:
            with gzip.open(str(path) + ".gz", "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
        rebuilt = evidence_book(payload, day)
        if rebuilt["sources"].get(day) != book["sources"][day]:
            raise ValueError("owner_component_source_generation_changed")
        if day in book.get("replay_sources", {}):
            from src.engine.scalping.strategy_owner_replay import attach_replays

            attach_replays(rebuilt, report_dir, day)
            if (
                rebuilt.get("replay_sources", {}).get(day)
                != book["replay_sources"][day]
            ):
                raise ValueError("owner_component_replay_generation_changed")
        books.append(rebuilt)
    rebuilt = merge_books(books)
    if rebuilt["rows"] != book.get("rows"):
        raise ValueError("owner_component_research_row_mismatch")
    if rebuilt.get("replays", {}) != book.get("replays", {}):
        raise ValueError("owner_component_replay_row_mismatch")
    if rebuilt.get("replay_sources", {}) != book.get("replay_sources", {}):
        raise ValueError("owner_component_replay_source_mismatch")
    return rebuilt


def evaluate(book, family, baseline, target_date, sample_floor=20):
    """Observed profiles only; frequency/capital efficiency, not per-trade uplift.

    Matching venue/session, other component and score profile are mandatory. Train
    and holdout split each policy's chronological exposure dates independently.
    Different PREOPEN versions need not trade concurrently on identical dates.
    This is bounded observational comparison, not proof of a causal profit gain.
    """
    result = {
        "state": "hold_sample",
        "policies": [],
        "baseline": baseline,
        "owner": OWNERS[family],
        "economic_acceptance": "real_post_apply_separate",
        "unseen_profile_live_authority": False,
        "first_use_authority": "exact_replay_real_full_fill_bounded_preopen_contract",
        "maintenance_requires_positive_ev": False,
        "evaluated_candidate_count": 0,
        "evaluated_profiles": [],
        "qualified_candidate_count": 0,
        "comparison_window_policy": "per_profile_chronological_halves",
    }
    if (
        profile(family, baseline) is None
        or not isinstance(book, dict)
        or book.get("schema") != SCHEMA
    ):
        result["state"] = "source_quality_blocked"
        return result
    groups = defaultdict(list)
    for identity, row in book.get("rows", {}).items():
        if (
            row.get("date") not in book.get("sources", {})
            or not "2026-06-05" <= row["date"] < target_date
        ):
            continue
        others = {k: v for k, v in row["profiles"].items() if k != family}
        groups[
            (
                row["venue"],
                row["session"],
                digest([others, row.get("score_profile"), row["context_sha256"]]),
            )
        ].append((identity, row))
    for (venue, session, cohort), items in groups.items():
        days = sorted({r["date"] for _, r in items})
        if len(days) < 2:
            continue
        profiles = {
            digest(r["profiles"][family]): r["profiles"][family] for _, r in items
        }
        for proposed in profiles.values():
            if not bounded_change(family, baseline, proposed):
                continue
            arms = [
                [r for _, r in items if r["profiles"][family] == p]
                for p in (baseline, proposed)
            ]
            if any(len(arm) < sample_floor for arm in arms):
                continue
            arm_days = [sorted({r["date"] for r in arm}) for arm in arms]
            if any(len(dates) < 2 for dates in arm_days):
                continue
            splits = [dates[len(dates) // 2] for dates in arm_days]
            metrics = []
            ready = True
            for holdout in (False, True):
                subsets = [
                    [r for r in arm if (r["date"] >= split) == holdout]
                    for arm, split in zip(arms, splits)
                ]
                if any(len(rows) < max(1, sample_floor // 2) for rows in subsets):
                    ready = False
                    break
                summaries = [
                    {
                        "net": sum(r["net"] for r in rows),
                        "capital": sum(r["capital"] for r in rows),
                        "notional": sum(r["notional"] for r in rows),
                        "days": len({r["date"] for r in rows}),
                        "dates": sorted({r["date"] for r in rows}),
                        "sample_count": len(rows),
                    }
                    for rows in subsets
                ]
                before, after = summaries
                if (
                    after["net"] <= 0
                    or after["net"] / after["days"] <= before["net"] / before["days"]
                    or after["net"] / after["capital"]
                    <= before["net"] / before["capital"]
                ):
                    ready = False
                metrics.append(summaries)
            if ready:
                result["policies"].append(
                    {
                        "venue": venue,
                        "session": session,
                        "cohort_sha256": cohort,
                        "context_sha256": items[0][1]["context_sha256"],
                        "score_profile": items[0][1].get("score_profile"),
                        "other_profiles": {
                            k: v
                            for k, v in items[0][1]["profiles"].items()
                            if k != family
                        },
                        "profile": proposed,
                        "baseline": baseline,
                        "metrics": metrics,
                        "source_dates": days,
                        "evidence_sha256": digest(items),
                        "sample_floor": sample_floor,
                        "comparison_window_policy": result["comparison_window_policy"],
                    }
                )
            if len(metrics) == 2:
                result["evaluated_candidate_count"] += 1
                result["evaluated_profiles"].append(
                    {
                        "venue": venue,
                        "session": session,
                        "context_sha256": items[0][1]["context_sha256"],
                        "score_profile": items[0][1].get("score_profile"),
                        "other_profiles": {
                            k: v
                            for k, v in items[0][1]["profiles"].items()
                            if k != family
                        },
                        "profile": proposed,
                        "qualified": ready,
                    }
                )
    # Retain disjoint runtime contexts. For overlapping candidates choose by
    # training economics only, then a stable identity tie-break (not input order).
    result["qualified_candidate_count"] = len(result["policies"])
    by_scope = defaultdict(list)
    for policy in result["policies"]:
        by_scope[
            (
                policy["venue"],
                policy["session"],
                policy["context_sha256"],
                digest(policy.get("score_profile")),
                digest(policy["other_profiles"]),
            )
        ].append(policy)

    def rank(policy):
        before, after = policy["metrics"][0]
        return (
            -(after["net"] / after["days"] - before["net"] / before["days"]),
            -(after["net"] / after["capital"] - before["net"] / before["capital"]),
            digest(policy["profile"]),
            policy["cohort_sha256"],
        )

    result["policies"] = [
        sorted(rows, key=rank)[0] for _, rows in sorted(by_scope.items())
    ]
    result["superseded_qualified_candidate_count"] = result[
        "qualified_candidate_count"
    ] - len(result["policies"])
    eligible_rows = [row for items in groups.values() for _, row in items]
    alternative_profiles = {
        digest(row["profiles"][family])
        for row in eligible_rows
        if bounded_change(family, baseline, row["profiles"][family])
    }
    result["observed_alternative_profile_count"] = len(alternative_profiles)
    result["valid_source_day_count"] = len(book.get("sources", {}))
    # A rolling book cannot reach an unbounded cumulative-date floor. Surface a
    # missing alternative immediately, rather than promise that more identical
    # baseline trades will magically create first-use authority.
    result["first_use_research_required"] = bool(
        eligible_rows and not alternative_profiles
    )
    result["maintenance_review_due"] = False
    result["state"] = (
        "verified_observed_profile"
        if result["policies"]
        else (
            "baseline_only_no_observed_challenger"
            if eligible_rows and not alternative_profiles
            else (
                "hold_no_edge" if result["evaluated_candidate_count"] else "hold_sample"
            )
        )
    )
    return result
