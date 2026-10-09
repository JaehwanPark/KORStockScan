"""Historical collection metadata utilities for isolated archive comparison.

No Main runtime producer imports this module. Boot and WS reject its retired
feedback commands; these helpers cannot confer subscription or order authority.
Kept for reading and reproducing immutable historical metadata only.
"""

from __future__ import annotations

from src.trading.config.owner_retirement import new_entry_retired

import hashlib
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
SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA = "scalp_micro_reversion_collection_targets_v2"
COLLECTION_TARGET_SCHEMA = "scalp_micro_reversion_collection_targets_v3"
COLLECTION_TARGET_SCHEMAS = frozenset(
    {
        LEGACY_COLLECTION_TARGET_SCHEMA,
        SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA,
        COLLECTION_TARGET_SCHEMA,
    }
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
MAX_COLLECTION_TARGET_ACTIVE_ITEMS = 400
REPAIRABLE_GAPS = frozenset(
    {
        "micro_date_partition_missing",
        "micro_symbol_not_observed",
        "micro_anchor_window_not_observed",
        "micro_post_anchor_not_observed",
        "zero_base_exact_route_subscription_conflict",
    }
)
POLICY_SAMPLE_ACCUMULATION = "micro_policy_sample_accumulation"
MAX_ZERO_BASE_GAP_SOURCE_BYTES = 128 * 1024 * 1024
MAX_ZERO_BASE_GAP_EVENTS = 256


def load_zero_base_route_gap_scopes(
    source_date: str, *, root: Path = DATA_DIR / "pipeline_events",
    collection_target_root: Path = COLLECTION_TARGET_ROOT,
) -> dict[str, Any]:
    """Bind current-date premarket probe conflicts to their discovery claims.

    This is next-session observation input only.  It cannot recreate a missing
    tick or turn a failed probe into a machine decision.
    """
    path = root / f"pipeline_events_{source_date}.jsonl"
    if date.fromisoformat(source_date) < date(2026, 9, 29):
        return {"status": "not_applicable", "path": str(path), "scopes": []}
    current_targets = load_exact_date_collection_targets(
        source_date, root=collection_target_root,
    )
    if current_targets.get("status") != "loaded":
        return {"status": "unobservable",
                "reason": "current_source_only_target_"
                + str(current_targets.get("status") or "missing"),
                "path": str(path), "scopes": []}
    target_payload = current_targets.get("payload") or {}
    current_target = {
        "path": current_targets["path"],
        "semantic_sha256": hashlib.sha256(json.dumps(
            target_payload, sort_keys=True, ensure_ascii=True,
            separators=(",", ":"),
        ).encode()).hexdigest(),
    }
    owned_items = {
        row.get("symbol"): set(row.get("registration_items") or ())
        for row in target_payload.get("selected_targets") or ()
        if isinstance(row, dict)
    }
    try:
        size = path.stat().st_size
    except OSError as exc:
        return {"status": "unobservable", "reason": type(exc).__name__,
                "path": str(path), "scopes": []}
    if size > MAX_ZERO_BASE_GAP_SOURCE_BYTES:
        return {"status": "unobservable", "reason": "source_size_limit",
                "path": str(path), "scopes": []}
    claims: dict[str, tuple[str, str, datetime]] = {}
    conflicts: list[tuple[str, str, datetime, str]] = []
    digest = hashlib.sha256()
    malformed = 0
    read_bytes = 0
    try:
        with path.open("rb") as source:
            for raw in source:
                read_bytes += len(raw)
                if read_bytes > MAX_ZERO_BASE_GAP_SOURCE_BYTES:
                    return {"status": "unobservable", "reason": "source_size_limit",
                            "path": str(path), "scopes": []}
                digest.update(raw)
                try:
                    row = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    malformed += 1
                    continue
                if (not isinstance(row, dict)
                        or row.get("emitted_date") != source_date
                        or row.get("stage") not in {
                            "zero_base_probe_claim", "zero_base_probe_result"
                        }):
                    continue
                fields = row.get("fields")
                if not isinstance(fields, dict):
                    continue
                code = _normalize_symbol(row.get("stock_code"))
                route = fields.get("zero_base_route")
                source_sha = fields.get("zero_base_source_sha256")
                if (not code or route != "nxt_only"
                        or not isinstance(source_sha, str)
                        or len(source_sha) != 64
                        or any(char not in "0123456789abcdef" for char in source_sha)):
                    continue
                try:
                    emitted = datetime.fromisoformat(row["emitted_at"])
                except (KeyError, TypeError, ValueError):
                    continue
                if emitted.tzinfo is not None:
                    emitted = emitted.astimezone(KST).replace(tzinfo=None)
                if emitted.date().isoformat() != source_date:
                    continue
                if row["stage"] == "zero_base_probe_claim":
                    claims[source_sha] = (code, route, emitted)
                elif (fields.get("zero_base_probe_result") == "source_unavailable"
                      and fields.get("zero_base_probe_reason")
                      == "exact_route_subscription_conflict"
                      and fields.get("entry_mechanistic_action") in (None, "", "-")
                      and fields.get("actual_order_submitted") in (False, "False")):
                    conflicts.append((code, route, emitted, source_sha))
                    if len(conflicts) > MAX_ZERO_BASE_GAP_EVENTS:
                        return {"status": "unobservable", "reason": "event_limit",
                                "path": str(path), "scopes": []}
    except OSError as exc:
        return {"status": "unobservable", "reason": type(exc).__name__,
                "path": str(path), "scopes": []}
    scopes = []
    seen = set()
    for code, route, result_at, source_sha in conflicts:
        claim = claims.get(source_sha)
        if (claim is None or claim[:2] != (code, route)
                or not 0 <= (result_at - claim[2]).total_seconds() <= 120
                or (code, source_sha) in seen
                or not owned_items.get(code)
                or f"{code}_NX" in owned_items[code]):
            continue
        seen.add((code, source_sha))
        scopes.append({"symbol": code, "route": route,
                       "source_sha256": source_sha,
                       "result_at": result_at.isoformat()})
    return {"status": "partial" if malformed else "complete", "path": str(path),
            "source_sha256": digest.hexdigest(), "malformed_rows": malformed,
            "conflict_event_count": len(conflicts), "matched_event_count": len(scopes),
            "current_target": current_target, "scopes": scopes}
COLLECTION_TARGET_METRIC_CONTRACT = {
    "metric_role": (
        "full_active_owner_exact_route_collection_coverage_and_bounded_"
        "prospective_sample_budget"
    ),
    "decision_authority": "next_session_market_data_observation_only",
    "window_policy": (
        "exact_next_krx_trading_date_all_active_owner_symbol_routes_then_"
        "bounded_prospective"
    ),
    "sample_floor": "not_an_economic_or_policy_promotion_metric",
    "primary_decision_metric": (
        "all_active_owner_exact_route_coverage_before_prospective_policy_samples"
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
        "active_episode_owner",
        "active_main_fixed_watch",
    }


def build_collection_targets(
    attribution_report: dict[str, Any],
    *,
    max_symbols: int | None = None,
    generated_at: datetime | None = None,
    zero_base_gap_scopes: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build exact-date source-only subscriptions without collapsing owner routes."""

    source_date = date.fromisoformat(str(attribution_report["target_date"]))
    if not is_krx_trading_day(source_date):
        raise ValueError("collection_target_source_date_not_krx_trading_day")
    effective_date = _next_krx_trading_date(source_date)
    research_budget = _bounded_max_symbols(max_symbols)
    merged: dict[str, dict[str, Any]] = {}

    def merge_scope(scope: dict[str, Any], *, collection_reason: str) -> None:
        if str(scope.get("owner") or "").startswith("widget"):
            return
        symbol = _normalize_symbol(scope.get("symbol"))
        if not symbol:
            return
        from src.trading.config.owner_retirement import new_entry_retired
        if new_entry_retired(symbol, scope.get("owner")):
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
            or False
        )

    from src.engine.scalping.main_fixed_watch import SPECS
    for spec in SPECS if effective_date >= date(2026, 10, 7) else ():
        merge_scope({
            "symbol": spec.symbol, "owner": "main_scalping",
            "scope_id": f"main_fixed_watch_{spec.symbol}",
            "scope_kind": "active_main_fixed_watch", "expected_venues": ["SOR", "NXT"],
        }, collection_reason="MAIN_FIXED_WATCH_SOURCE")

    for gap in attribution_report.get("producer_consumer_gaps") or ():
        if not isinstance(gap, dict) or gap.get("gap_class") not in REPAIRABLE_GAPS:
            continue
        merge_scope(gap, collection_reason=str(gap["gap_class"]))

    consumers = attribution_report.get("consumers") or {}
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

    # The probe's exact _NX receipt was absent, so only the next session's
    # source-only collection may be augmented.  No past 0B/0D or machine
    # decision is reconstructed from this gap.
    for gap in zero_base_gap_scopes:
        if not isinstance(gap, dict) or gap.get("route") != "nxt_only":
            continue
        source_sha = gap.get("source_sha256")
        if (not isinstance(source_sha, str) or len(source_sha) != 64
                or any(char not in "0123456789abcdef" for char in source_sha)
                or str(gap.get("result_at") or "")[:10] != source_date.isoformat()):
            continue
        merge_scope(
            {"owner": "zero_base_probe_source_only", "scope_id": source_sha,
             "scope_kind": "prospective_zero_base_exact_route_gap",
             "symbol": gap.get("symbol"), "expected_venues": ("NXT",)},
            collection_reason="zero_base_exact_route_subscription_conflict",
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
        len(prospective_rows), research_budget,
        max(0, MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS - len(active_rows)),
        max(0, MAX_COLLECTION_TARGET_ACTIVE_ITEMS - sum(
            len(row["_expected_venues"]) for row in active_rows
        )),
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
            # Every active owner route is required source coverage.  Rotating
            # one route per symbol silently removed, for example, an NXT
            # premarket episode whenever the same symbol also had a SOR/KRX
            # owner.  Prospective research remains bounded to one rotated
            # route because it has no active execution lineage to repair.
            selected_venues = (
                venues if row["active_owner"] else
                ["NXT"] if "zero_base_exact_route_subscription_conflict"
                in row["gap_classes"] else
                [venues[venue_phase % len(venues)]]
            )
            row["expected_venues"] = selected_venues
            row["registration_items"] = [
                _registration_item(row["symbol"], venue) for venue in selected_venues
            ]
            if len(selected_venues) == 1:
                row["expected_venue"] = selected_venues[0]
                row["registration_item"] = row["registration_items"][0]
            row.pop("_gap_priority", None)

    selected_item_count = sum(
        len(row.get("registration_items") or ()) for row in selected
    )
    selected_active_item_count = sum(
        len(row.get("registration_items") or ())
        for row in selected
        if row.get("active_owner") is True
    )
    active_candidate_item_count = sum(
        len(row.get("expected_venues") or ()) for row in selected if row["active_owner"]
    )
    if selected_active_item_count > MAX_COLLECTION_TARGET_ACTIVE_ITEMS:
        raise ValueError("active_owner_collection_target_item_capacity_exceeded")

    generated = generated_at or datetime.now(KST)
    return {
        "schema": COLLECTION_TARGET_SCHEMA,
        "source_report_schema": attribution_report.get("schema"),
        "source_date": source_date.isoformat(),
        "effective_date": effective_key,
        "generated_at_kst": generated.astimezone(KST).isoformat(),
        "status": "ready" if selected else "no_repairable_gap",
        "decision": (
            "active_owner_exact_route_full_coverage_source_only_collection_ready"
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
            # ceiling, not the prospective research budget in schemas v2/v3.
            "max_symbols": min(MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS, len(active_rows) + research_budget),
            "prospective_budget_policy": "independent_of_active_owner_coverage",
            "research_symbol_budget": research_budget,
            "selected_symbol_count": len(selected),
            "selected_registration_item_count": selected_item_count,
            "overflow_symbol_count": len(overflow),
            "rotation_key": effective_key,
            "rotation_index": rotation_index,
            "rotation_policy": "priority_cohort_deterministic_round_robin",
            "venue_rotation_policy": (
                "independent_symbol_phase_after_selection_cohort_cycle"
            ),
            "overflow_rotates_on_next_effective_date": False,
            "coverage_policy": (
                "all_active_owner_symbol_routes_then_bounded_prospective_rotation"
            ),
            "coverage_stage": "exact_date_target_manifest_selection",
            "runtime_registration_receipt_required": True,
            "active_owner_budget_bypass": True,
            "active_owner_exact_route_full_coverage": True,
            "bounded_rotation_condition": (
                "prospective_only_stable_priority_cohort_and_daily_budget"
            ),
            "active_owner_candidate_count": len(active_rows),
            "selected_active_owner_count": len(active_rows),
            "active_owner_candidate_item_count": active_candidate_item_count,
            "selected_active_owner_item_count": selected_active_item_count,
            "active_owner_overflow_count": 0,
            "selected_prospective_owner_count": prospective_budget,
            "prospective_overflow_count": len(prospective_rows) - prospective_budget,
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
    if not isinstance(budget, dict):
        return {"status": "invalid_budget_contract", "path": str(path), "registration_items": []}
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
        schema == SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA
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
    try:
        declared_selected_items = int(
            (budget or {}).get("selected_registration_item_count")
        )
        active_candidate_items = int(
            (budget or {}).get("active_owner_candidate_item_count")
        )
        selected_active_items = int(
            (budget or {}).get("selected_active_owner_item_count")
        )
    except (TypeError, ValueError):
        declared_selected_items = -1
        active_candidate_items = -1
        selected_active_items = -1
    # Existing v3 manifests retain their original shared-budget contract.
    independent_budget = (budget or {}).get("prospective_budget_policy") == "independent_of_active_owner_coverage"
    prospective_limit = (
        min(research_budget, max(0, MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS - selected_active))
        if independent_budget else max(0, research_budget - selected_active)
    )
    expected_max = (
        min(MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS, active_candidates + research_budget)
        if independent_budget else max(active_candidates, research_budget)
    )
    v3_budget_valid = bool(
        schema == COLLECTION_TARGET_SCHEMA
        and isinstance(selected_targets, list)
        and isinstance(overflow_targets, list)
        and 1 <= research_budget <= MAX_COLLECTION_TARGET_MAX_SYMBOLS
        and 1 <= declared_max <= MAX_COLLECTION_TARGET_ACTIVE_SYMBOLS
        and declared_selected == len(selected_targets)
        and declared_overflow == len(overflow_targets)
        and len(selected_targets) <= declared_max
        and 0 <= declared_selected_items <= MAX_COLLECTION_TARGET_ACTIVE_ITEMS
        and budget.get("coverage_policy")
        == "all_active_owner_symbol_routes_then_bounded_prospective_rotation"
        and budget.get("coverage_stage") == "exact_date_target_manifest_selection"
        and budget.get("runtime_registration_receipt_required") is True
        and budget.get("active_owner_budget_bypass") is True
        and budget.get("active_owner_exact_route_full_coverage") is True
        and active_candidates == selected_active
        and active_overflow == 0
        and active_candidate_items == selected_active_items
        and 0 <= selected_active_items <= declared_selected_items
        and declared_selected == selected_active + selected_prospective
        and 0 <= selected_prospective <= prospective_limit
        and prospective_overflow == len(overflow_targets)
        and declared_max == expected_max
        and budget.get("prospective_budget_policy") in (None, "independent_of_active_owner_coverage")
    )
    if not isinstance(budget, dict) or not (
        legacy_budget_valid or v2_budget_valid or v3_budget_valid
    ):
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
        if schema in {
            SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA,
            COLLECTION_TARGET_SCHEMA,
        } and not isinstance(row.get("active_owner"), bool):
            return {
                "status": "invalid_budget_contract",
                "path": str(path),
                "registration_items": [],
            }
        symbol = _normalize_symbol(row.get("symbol"))
        if schema == COLLECTION_TARGET_SCHEMA:
            venues = [
                _normalize_venue(value) for value in row.get("expected_venues") or ()
            ]
            row_items = [
                str(value or "").strip().upper()
                for value in row.get("registration_items") or ()
            ]
        else:
            venues = [_normalize_venue(row.get("expected_venue"))]
            row_items = [str(row.get("registration_item") or "").strip().upper()]
        if (
            not symbol
            or not venues
            or any(not venue for venue in venues)
            or len(venues) != len(set(venues))
            or len(row_items) != len(venues)
            or row_items != [_registration_item(symbol, venue) for venue in venues]
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
        items.extend(row_items)
    if len(items) != len(set(items)):
        return {
            "status": "invalid_target_contract",
            "path": str(path),
            "registration_items": [],
        }
    if (
        schema
        in {
            SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA,
            COLLECTION_TARGET_SCHEMA,
        }
        and selected_active_count != selected_active
    ):
        return {
            "status": "invalid_budget_contract",
            "path": str(path),
            "registration_items": [],
        }
    if schema in {SYMBOL_ONLY_COLLECTION_TARGET_SCHEMA, COLLECTION_TARGET_SCHEMA}:
        overflow_symbols: set[str] = set()
        for row in overflow_targets:
            symbol = (
                _normalize_symbol(row.get("symbol")) if isinstance(row, dict) else ""
            )
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
    if schema == COLLECTION_TARGET_SCHEMA and len(items) != declared_selected_items:
        return {
            "status": "invalid_budget_contract",
            "path": str(path),
            "registration_items": [],
        }
    retired_items = {
        item for row in selected_targets
        if row.get("owners") and all(
            str(owner).startswith("widget") or new_entry_retired(row.get("symbol"), owner)
            for owner in row["owners"]
        )
        for item in (row.get("registration_items") or [row.get("registration_item")])
    }
    return {
        "status": "loaded",
        "path": str(path),
        "source_date": payload.get("source_date"),
        "effective_date": effective_date,
        "registration_items": [item for item in items if item not in retired_items],
        "retired_owner_items_excluded": sorted(retired_items),
        "payload": payload,
    }
