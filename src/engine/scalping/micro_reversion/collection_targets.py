"""Bounded next-session collection feedback for machine microstructure gaps.

This module turns explicit attribution gaps into an exact-date market-data
observation set.  It never creates a trading target and never reads the manual
control exclusion list: manual control is an order boundary, not a research
data boundary.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.market_day import count_krx_trading_days, is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
LEGACY_COLLECTION_TARGET_SCHEMA = "scalp_micro_reversion_collection_targets_v1"
COLLECTION_TARGET_SCHEMA = "scalp_micro_reversion_collection_targets_v2"
COLLECTION_TARGET_SCHEMAS = frozenset(
    {LEGACY_COLLECTION_TARGET_SCHEMA, COLLECTION_TARGET_SCHEMA}
)
COLLECTION_TARGET_ROOT = (
    DATA_DIR / "runtime" / "scalp_micro_reversion_collection_targets"
)
COLLECTION_TARGET_MAX_SYMBOLS_ENV = (
    "SCALP_MICRO_REVERSION_COLLECTION_TARGET_MAX_SYMBOLS"
)
DEFAULT_COLLECTION_TARGET_MAX_SYMBOLS = 4
MAX_COLLECTION_TARGET_MAX_SYMBOLS = 8
MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS = 200
REPAIRABLE_GAPS = frozenset(
    {
        "micro_date_partition_missing",
        "micro_symbol_not_observed",
        "micro_anchor_window_not_observed",
        "micro_post_anchor_not_observed",
    }
)
POLICY_SAMPLE_ACCUMULATION = "micro_policy_sample_accumulation"
COLLECTION_TARGET_METRIC_CONTRACT = {
    "metric_role": (
        "full_active_owner_collection_coverage_and_bounded_prospective_sample_budget"
    ),
    "decision_authority": "next_session_market_data_observation_only",
    "window_policy": (
        "exact_next_krx_trading_date_all_active_owner_symbols_then_bounded_prospective"
    ),
    "sample_floor": "not_an_economic_or_policy_promotion_metric",
    "primary_decision_metric": (
        "all_active_owner_symbol_coverage_before_prospective_policy_samples"
    ),
    "source_quality_gate": (
        "exact_source_and_effective_dates_valid_symbol_route_and_source_only_authority"
    ),
    "forbidden_uses": (
        "manual_control_exclusion_as_collection_filter",
        "trading_target_creation",
        "entry_exit_or_policy_decision",
        "broker_order_submission_or_cancel",
        "threshold_provider_bot_quantity_or_cap_mutation",
        "economic_imputation_for_unobserved_symbols",
    ),
}


def _next_krx_trading_date(source_date: date) -> date:
    candidate = source_date + timedelta(days=1)
    for _ in range(14):
        if is_krx_trading_day(candidate):
            return candidate
        candidate += timedelta(days=1)
    raise ValueError("next_krx_trading_date_unresolved")


def _bounded_max_symbols(value: Any = None) -> int:
    raw = os.getenv(COLLECTION_TARGET_MAX_SYMBOLS_ENV, "") if value is None else value
    try:
        parsed = int(str(raw).strip()) if str(raw).strip() else 0
    except (TypeError, ValueError):
        parsed = 0
    if parsed <= 0:
        parsed = DEFAULT_COLLECTION_TARGET_MAX_SYMBOLS
    return min(parsed, MAX_COLLECTION_TARGET_MAX_SYMBOLS)


def _normalize_symbol(value: Any) -> str:
    symbol = str(value or "").strip().upper()
    if symbol.startswith("A"):
        symbol = symbol[1:]
    return symbol if len(symbol) == 6 and symbol.isdigit() else ""


def _normalize_venue(value: Any) -> str:
    venue = str(value or "").strip().upper()
    return venue if venue in {"KRX", "NXT", "SOR"} else ""


def _registration_item(symbol: str, venue: str) -> str:
    if venue == "NXT":
        return f"{symbol}_NX"
    if venue == "SOR":
        return f"{symbol}_AL"
    return symbol


def _rotation_index(effective_date: date) -> int:
    return count_krx_trading_days(date(2026, 1, 1), effective_date)


def _priority_round_robin(
    rows: list[dict[str, Any]], *, rotation_index: int, step: int
) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    remaining_slots = max(0, step)
    priorities = sorted({int(row["_gap_priority"]) for row in rows}, reverse=True)
    for priority in priorities:
        cohort = sorted(
            (row for row in rows if int(row["_gap_priority"]) == priority),
            key=lambda row: str(row["symbol"]),
        )
        if cohort:
            cohort_slots = min(len(cohort), remaining_slots)
            rotation_step = max(1, cohort_slots)
            offset = (rotation_index * rotation_step) % len(cohort)
            selection_cycle_period = len(cohort) // math.gcd(len(cohort), rotation_step)
            for row in cohort:
                row["_selection_cycle_period"] = selection_cycle_period
            cohort = cohort[offset:] + cohort[:offset]
            remaining_slots -= cohort_slots
        ordered.extend(cohort)
    return ordered


def _is_active_gap(gap: dict[str, Any]) -> bool:
    scope_kind = str(gap.get("scope_kind") or "")
    return scope_kind in {
        "active_widget_owner",
        "active_widget_actual_execution",
        "active_episode_owner",
    }


def build_collection_targets(
    attribution_report: dict[str, Any],
    *,
    max_symbols: int | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build one exact-date source-only subscription target per selected symbol."""

    source_date = date.fromisoformat(str(attribution_report["target_date"]))
    if not is_krx_trading_day(source_date):
        raise ValueError("collection_target_source_date_not_krx_trading_day")
    effective_date = _next_krx_trading_date(source_date)
    research_budget = _bounded_max_symbols(max_symbols)
    merged: dict[str, dict[str, Any]] = {}

    def merge_scope(scope: dict[str, Any], *, collection_reason: str) -> None:
        symbol = _normalize_symbol(scope.get("symbol"))
        if not symbol:
            return
        row = merged.setdefault(
            symbol,
            {
                "symbol": symbol,
                "owners": set(),
                "scope_ids": set(),
                "scope_kinds": set(),
                "gap_classes": set(),
                "collection_reasons": set(),
                "expected_venues": set(),
                "active_owner": False,
                "actual_execution_observed": False,
            },
        )
        row["owners"].add(str(scope.get("owner") or "unknown"))
        if scope.get("scope_id"):
            row["scope_ids"].add(str(scope["scope_id"]))
        if scope.get("scope_kind"):
            row["scope_kinds"].add(str(scope["scope_kind"]))
        row["collection_reasons"].add(collection_reason)
        if collection_reason in REPAIRABLE_GAPS:
            row["gap_classes"].add(collection_reason)
        venues = {
            _normalize_venue(value) for value in scope.get("expected_venues") or ()
        }
        row["expected_venues"].update(value for value in venues if value)
        row["active_owner"] = row["active_owner"] or _is_active_gap(scope)
        row["actual_execution_observed"] = bool(
            row["actual_execution_observed"]
            or scope.get("scope_kind") == "active_widget_actual_execution"
        )

    for gap in attribution_report.get("producer_consumer_gaps") or ():
        if not isinstance(gap, dict) or gap.get("gap_class") not in REPAIRABLE_GAPS:
            continue
        merge_scope(gap, collection_reason=str(gap["gap_class"]))

    consumers = attribution_report.get("consumers") or {}
    widget_symbols = (consumers.get("widget_postclose_tuning") or {}).get("symbols")
    if isinstance(widget_symbols, dict):
        for scope_id, payload in widget_symbols.items():
            if not isinstance(payload, dict):
                continue
            scope_kinds = [str(value) for value in payload.get("scopes") or ()]
            owner_scope_ids = [
                str(value) for value in payload.get("owner_scope_ids") or ()
            ]
            owner_scope_kinds = payload.get("owner_scope_kinds") or {}
            owner_scope_venues = payload.get("owner_scope_expected_venues") or {}
            if not owner_scope_ids:
                owner_scope_ids = [str(scope_id)]
            for owner_scope_id in owner_scope_ids:
                merge_scope(
                    {
                        "owner": "widget",
                        "scope_id": owner_scope_id,
                        "scope_kind": owner_scope_kinds.get(owner_scope_id)
                        or (
                            "active_widget_owner"
                            if "active_widget_owner" in scope_kinds
                            else (
                                scope_kinds[0]
                                if scope_kinds
                                else "prospective_widget_research"
                            )
                        ),
                        "symbol": payload.get("symbol") or scope_id,
                        "expected_venues": owner_scope_venues.get(owner_scope_id)
                        or payload.get("expected_venues")
                        or ("SOR",),
                    },
                    collection_reason=POLICY_SAMPLE_ACCUMULATION,
                )
    episode_profiles = (consumers.get("episode_machine_postclose_tuning") or {}).get(
        "profiles"
    )
    if isinstance(episode_profiles, dict):
        for scope_id, payload in episode_profiles.items():
            if not isinstance(payload, dict):
                continue
            merge_scope(
                {
                    "owner": "episode",
                    "scope_id": str(scope_id),
                    "scope_kind": payload.get("scope")
                    or "prospective_episode_research",
                    "symbol": payload.get("symbol"),
                    "expected_venues": payload.get("expected_venues") or ("SOR",),
                },
                collection_reason=POLICY_SAMPLE_ACCUMULATION,
            )

    candidates: list[dict[str, Any]] = []
    effective_key = effective_date.isoformat()
    rotation_index = _rotation_index(effective_date)
    for symbol, row in merged.items():
        venues = sorted(row["expected_venues"] or {"SOR"})
        gap_classes = sorted(row["gap_classes"])
        collection_reasons = sorted(row["collection_reasons"])
        gap_priority = max(
            (
                3
                if gap in {"micro_date_partition_missing", "micro_symbol_not_observed"}
                else 2 if gap in REPAIRABLE_GAPS else 1
            )
            for gap in collection_reasons
        )
        # Exact owned execution is the highest-value source-quality repair.
        # This only changes next-session market-data observation priority.
        if row["actual_execution_observed"]:
            gap_priority += 10
        candidates.append(
            {
                "symbol": symbol,
                "owners": sorted(row["owners"]),
                "scope_ids": sorted(row["scope_ids"]),
                "scope_kinds": sorted(row["scope_kinds"]),
                "gap_classes": gap_classes,
                "collection_reasons": collection_reasons,
                "active_owner": bool(row["active_owner"]),
                "actual_execution_observed": bool(row["actual_execution_observed"]),
                "priority_class": (
                    "active_owner_collection"
                    if row["active_owner"]
                    else "prospective_owner_collection"
                ),
                "observation_allowed": True,
                "trading_target_created": False,
                "manual_control_exclusion_applied": False,
                "market_data_subscription_effect": True,
                "trading_runtime_effect": False,
                "trading_decision_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "_expected_venues": venues,
                "_gap_priority": gap_priority,
            }
        )

    active_rows = [row for row in candidates if row["active_owner"]]
    prospective_rows = [row for row in candidates if not row["active_owner"]]
    if len(active_rows) > MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS:
        raise ValueError("active_owner_collection_target_capacity_exceeded")

    # Active widget/episode owners are the collection universe, not candidates
    # competing for the research rotation budget. Intraday 0B/0D gaps cannot
    # be reconstructed after the fact, so dropping an active symbol here would
    # permanently remove its entry/stop/target microstructure evidence. The
    # bounded daily budget now applies only to prospective research symbols.
    prospective_budget = min(
        len(prospective_rows), max(0, research_budget - len(active_rows))
    )
    active_candidates = _priority_round_robin(
        active_rows,
        rotation_index=rotation_index,
        step=len(active_rows),
    )
    prospective_candidates = _priority_round_robin(
        prospective_rows,
        rotation_index=rotation_index,
        step=prospective_budget,
    )
    selected = active_candidates + prospective_candidates[:prospective_budget]
    selected_keys = {row["symbol"] for row in selected}
    overflow = [row for row in candidates if row["symbol"] not in selected_keys]
    for rows in (selected, overflow):
        for row in rows:
            venues = list(row.pop("_expected_venues"))
            selection_cycle_period = max(1, int(row.pop("_selection_cycle_period", 1)))
            # Advance the venue after the symbol-selection cohort completes a
            # cycle.  Using rotation_index directly for both dimensions phase-
            # locks multi-symbol cohorts (each symbol can otherwise receive the
            # same venue forever).  A stable symbol phase also distributes the
            # selected routes without sacrificing deterministic replay.
            venue_phase = rotation_index // selection_cycle_period + int(row["symbol"])
            venue = venues[venue_phase % len(venues)]
            row["expected_venue"] = venue
            row["registration_item"] = _registration_item(row["symbol"], venue)
            row.pop("_gap_priority", None)

    generated = generated_at or datetime.now(KST)
    return {
        "schema": COLLECTION_TARGET_SCHEMA,
        "source_report_schema": attribution_report.get("schema"),
        "source_date": source_date.isoformat(),
        "effective_date": effective_key,
        "generated_at_kst": generated.astimezone(KST).isoformat(),
        "status": "ready" if selected else "no_repairable_gap",
        "decision": (
            "active_owner_full_coverage_source_only_collection_ready"
            if selected
            else "no_source_only_collection_feedback_required"
        ),
        "metric_contract": COLLECTION_TARGET_METRIC_CONTRACT,
        "authority": {
            "decision_authority": "next_session_market_data_observation_only",
            "runtime_effect": False,
            "market_data_subscription_effect": True,
            "trading_runtime_effect": False,
            "trading_decision_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "manual_control_exclusion_applied": False,
        },
        "budget": {
            # Compatibility field: this is the effective selected-universe
            # ceiling, not the prospective research budget in schema v2.
            "max_symbols": max(len(active_rows), research_budget),
            "research_symbol_budget": research_budget,
            "selected_symbol_count": len(selected),
            "overflow_symbol_count": len(overflow),
            "rotation_key": effective_key,
            "rotation_index": rotation_index,
            "rotation_policy": "priority_cohort_deterministic_round_robin",
            "venue_rotation_policy": (
                "independent_symbol_phase_after_selection_cohort_cycle"
            ),
            "overflow_rotates_on_next_effective_date": False,
            "coverage_policy": (
                "all_active_owner_symbols_then_bounded_prospective_rotation"
            ),
            "coverage_stage": "exact_date_target_manifest_selection",
            "runtime_registration_receipt_required": True,
            "active_owner_budget_bypass": True,
            "active_owner_full_coverage": True,
            "bounded_rotation_condition": (
                "prospective_only_stable_priority_cohort_and_daily_budget"
            ),
            "active_owner_candidate_count": len(active_rows),
            "selected_active_owner_count": len(active_rows),
            "active_owner_overflow_count": 0,
            "selected_prospective_owner_count": prospective_budget,
            "prospective_overflow_count": len(prospective_rows)
            - prospective_budget,
            "prospective_reserve_applied": prospective_budget,
        },
        "selected_targets": selected,
        "overflow_targets": overflow,
    }


def collection_target_path(
    effective_date: str, *, root: Path = COLLECTION_TARGET_ROOT
) -> Path:
    return root / f"scalp_micro_reversion_collection_targets_{effective_date}.json"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_collection_targets(
    payload: dict[str, Any], *, root: Path = COLLECTION_TARGET_ROOT
) -> Path:
    path = collection_target_path(str(payload["effective_date"]), root=root)
    _atomic_write(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return path


def load_exact_date_collection_targets(
    effective_date: str, *, root: Path = COLLECTION_TARGET_ROOT
) -> dict[str, Any]:
    """Load a fresh, source-only target set or return a fail-closed status."""

    path = collection_target_path(effective_date, root=root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"status": "missing", "path": str(path), "registration_items": []}
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid",
            "reason": type(exc).__name__,
            "path": str(path),
            "registration_items": [],
        }
    authority = payload.get("authority") if isinstance(payload, dict) else None
    try:
        source_date = date.fromisoformat(str(payload.get("source_date")))
        parsed_effective_date = date.fromisoformat(effective_date)
        source_date_valid = (
            is_krx_trading_day(source_date)
            and source_date < parsed_effective_date
            and _next_krx_trading_date(source_date) == parsed_effective_date
        )
    except (AttributeError, TypeError, ValueError):
        source_date_valid = False
    valid = bool(
        isinstance(payload, dict)
        and payload.get("schema") in COLLECTION_TARGET_SCHEMAS
        and payload.get("effective_date") == effective_date
        and source_date_valid
        and isinstance(authority, dict)
        and authority.get("decision_authority")
        == "next_session_market_data_observation_only"
        and authority.get("runtime_effect") is False
        and authority.get("trading_runtime_effect") is False
        and authority.get("market_data_subscription_effect") is True
        and authority.get("trading_decision_effect") is False
        and authority.get("actual_order_submitted") is False
        and authority.get("broker_order_forbidden") is True
        and authority.get("manual_control_exclusion_applied") is False
    )
    if not valid:
        return {
            "status": "invalid_authority_or_date_contract",
            "path": str(path),
            "registration_items": [],
        }
    budget = payload.get("budget")
    selected_targets = payload.get("selected_targets")
    overflow_targets = payload.get("overflow_targets")
    schema = payload.get("schema")
    try:
        declared_max = int((budget or {}).get("max_symbols"))
        declared_selected = int((budget or {}).get("selected_symbol_count"))
        declared_overflow = int((budget or {}).get("overflow_symbol_count"))
    except (TypeError, ValueError):
        declared_max = 0
        declared_selected = -1
        declared_overflow = -1
    legacy_budget_valid = bool(
        schema == LEGACY_COLLECTION_TARGET_SCHEMA
        and 1 <= declared_max <= MAX_COLLECTION_TARGET_MAX_SYMBOLS
        and isinstance(selected_targets, list)
        and declared_selected == len(selected_targets)
        and len(selected_targets) <= declared_max
    )
    try:
        research_budget = int((budget or {}).get("research_symbol_budget"))
        active_candidates = int((budget or {}).get("active_owner_candidate_count"))
        selected_active = int((budget or {}).get("selected_active_owner_count"))
        active_overflow = int((budget or {}).get("active_owner_overflow_count"))
        selected_prospective = int(
            (budget or {}).get("selected_prospective_owner_count")
        )
        prospective_overflow = int((budget or {}).get("prospective_overflow_count"))
    except (TypeError, ValueError):
        research_budget = 0
        active_candidates = -1
        selected_active = -1
        active_overflow = -1
        selected_prospective = -1
        prospective_overflow = -1
    v2_budget_valid = bool(
        schema == COLLECTION_TARGET_SCHEMA
        and isinstance(selected_targets, list)
        and isinstance(overflow_targets, list)
        and 1 <= research_budget <= MAX_COLLECTION_TARGET_MAX_SYMBOLS
        and 1 <= declared_max <= MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS
        and declared_selected == len(selected_targets)
        and declared_overflow == len(overflow_targets)
        and len(selected_targets) <= declared_max
        and budget.get("coverage_policy")
        == "all_active_owner_symbols_then_bounded_prospective_rotation"
        and budget.get("coverage_stage") == "exact_date_target_manifest_selection"
        and budget.get("runtime_registration_receipt_required") is True
        and budget.get("active_owner_budget_bypass") is True
        and budget.get("active_owner_full_coverage") is True
        and active_candidates == selected_active
        and active_overflow == 0
        and declared_selected == selected_active + selected_prospective
        and selected_prospective <= max(0, research_budget - selected_active)
        and prospective_overflow == len(overflow_targets)
        and declared_max == max(active_candidates, research_budget)
    )
    if not isinstance(budget, dict) or not (legacy_budget_valid or v2_budget_valid):
        return {
            "status": "invalid_budget_contract",
            "path": str(path),
            "registration_items": [],
        }
    items: list[str] = []
    seen_symbols: set[str] = set()
    selected_active_count = 0
    for row in selected_targets:
        if not isinstance(row, dict) or row.get("observation_allowed") is not True:
            return {
                "status": "invalid_target_contract",
                "path": str(path),
                "registration_items": [],
            }
        if schema == COLLECTION_TARGET_SCHEMA and not isinstance(
            row.get("active_owner"), bool
        ):
            return {
                "status": "invalid_budget_contract",
                "path": str(path),
                "registration_items": [],
            }
        symbol = _normalize_symbol(row.get("symbol"))
        venue = _normalize_venue(row.get("expected_venue"))
        item = str(row.get("registration_item") or "").strip().upper()
        if (
            not symbol
            or not venue
            or item != _registration_item(symbol, venue)
            or symbol in seen_symbols
            or row.get("trading_target_created") is not False
            or row.get("trading_runtime_effect") is not False
            or row.get("trading_decision_effect") is not False
            or row.get("market_data_subscription_effect") is not True
            or row.get("actual_order_submitted") is not False
            or row.get("broker_order_forbidden") is not True
            or row.get("manual_control_exclusion_applied") is not False
        ):
            return {
                "status": "invalid_target_contract",
                "path": str(path),
                "registration_items": [],
            }
        seen_symbols.add(symbol)
        selected_active_count += int(row.get("active_owner") is True)
        items.append(item)
    if schema == COLLECTION_TARGET_SCHEMA and selected_active_count != selected_active:
        return {
            "status": "invalid_budget_contract",
            "path": str(path),
            "registration_items": [],
        }
    if schema == COLLECTION_TARGET_SCHEMA:
        overflow_symbols: set[str] = set()
        for row in overflow_targets:
            symbol = _normalize_symbol(row.get("symbol")) if isinstance(row, dict) else ""
            if (
                not symbol
                or symbol in seen_symbols
                or symbol in overflow_symbols
                or row.get("active_owner") is not False
            ):
                return {
                    "status": "invalid_budget_contract",
                    "path": str(path),
                    "registration_items": [],
                }
            overflow_symbols.add(symbol)
    return {
        "status": "loaded",
        "path": str(path),
        "source_date": payload.get("source_date"),
        "effective_date": effective_date,
        "registration_items": items,
        "payload": payload,
    }
