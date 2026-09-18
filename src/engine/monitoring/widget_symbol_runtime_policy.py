"""Promote verified symbol-specific widget research to next-day runtime policy.

The bridge is intentionally separate from the low-price two-leg owner.  It
only accepts a complete clean-baseline research report, emits an exact-date
policy, and never starts a process or calls an account/order API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring.widget_symbol_signal_policy_research import (
    AUTHORITY as RESEARCH_AUTHORITY,
    CLEAN_BASELINE_DATE,
    METRIC_CONTRACT as RESEARCH_METRIC_CONTRACT,
    OWNER,
    REPORT_SCHEMA,
    SYMBOLS,
    resolve_completed_research_end_date,
)
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_execution_quality import EXECUTION_OWNER
from src.trading.order.episode_quantity import EPISODE_LEG_QUANTITY
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

POLICY_SCHEMA = "widget_symbol_runtime_policy_v1"
POLICY_AUTHORITY = "postclose_widget_symbol_runtime_policy_v1"
DEFAULT_RESEARCH_DIR = DATA_DIR / "report" / "widget_symbol_signal_policy_research"
DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "widget_symbol_runtime_policy"
DEFAULT_APPLY_REPORT_DIR = DATA_DIR / "report" / "widget_symbol_runtime_policy_apply"
POLICY_PREFIX = "widget_symbol_runtime_policy"
SUPPORTED_RESEARCH_SCHEMAS = {
    "widget_symbol_signal_policy_research_v2",
    "widget_symbol_signal_policy_research_v3",
    REPORT_SCHEMA,
}

OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-13T10:18:06+09:00",
    "inspected_paths": [
        "kiwoom_docs/종목정보.md",
        "kiwoom_docs/시세.md",
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contracts": [
        "POST /api/dostk/stkinfo; api-id=ka10001",
        "POST /api/dostk/mrkcond; api-id=ka10004",
        "POST /api/dostk/chart; api-id=ka10064",
        "POST /api/dostk/chart; api-id=ka10080",
        "POST /api/dostk/chart; api-id=ka20005",
        "POST /api/dostk/mrkcond; api-id=ka90008",
    ],
}

METRIC_CONTRACT = {
    "metric_role": "bounded_widget_symbol_runtime_policy_apply",
    "decision_authority": POLICY_AUTHORITY,
    "window_policy": "exact_next_krx_trading_date_only",
    "sample_floor": RESEARCH_METRIC_CONTRACT["sample_floor"],
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "complete_clean_baseline_research_report",
        "holdout_pass_widget_signal_policy_candidate",
        "positive_calibration_halves_and_holdout_ev",
        "exact_date_policy_loader_round_trip",
    ],
    "forbidden_uses": [
        "cross_symbol_policy_transfer",
        "same_day_runtime_apply",
        "stale_policy_auto_extension",
        "low_price_two_leg_owner_mutation",
        "account_or_order_api",
        "token_issue_or_refresh",
        "process_control",
        "broker_guard_bypass",
    ],
}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def next_krx_trading_date(value: date) -> date:
    candidate = value + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _positive_metric(payload: dict[str, Any], key: str) -> bool:
    try:
        return float(payload.get(key)) > 0.0
    except (TypeError, ValueError):
        return False


def _high_entry_cap_evidence_valid(result: dict[str, Any], max_entries: int) -> bool:
    if max_entries < 4:
        return True
    comparisons = result.get("entry_cap_comparison")
    if not isinstance(comparisons, dict):
        return False
    for window in (
        "calibration",
        "calibration_first_half",
        "calibration_second_half",
        "holdout",
    ):
        comparison = comparisons.get(window)
        if not isinstance(comparison, dict):
            return False
        for cap in range(4, max_entries + 1):
            evidence = comparison.get(str(cap))
            incremental = (
                evidence.get("incremental") if isinstance(evidence, dict) else None
            )
            if (
                not isinstance(evidence, dict)
                or evidence.get("incremental_ev_positive") is not True
                or not isinstance(incremental, dict)
                or int(incremental.get("episode_count") or 0) < 1
                or not _positive_metric(incremental, "notional_weighted_ev_pct")
            ):
                return False
    return True


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _research_universe(
    research: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    raw_universe = research.get("symbol_universe")
    raw_origins = research.get("symbol_origins")
    if raw_universe is None and raw_origins is None:
        if set(research.get("symbols") or {}) != set(SYMBOLS):
            raise ValueError("widget_symbol_research_universe_missing")
        return (
            dict(SYMBOLS),
            {symbol: "established_widget_symbol" for symbol in SYMBOLS},
        )
    if not isinstance(raw_universe, dict) or not isinstance(raw_origins, dict):
        raise ValueError("widget_symbol_research_universe_invalid")
    universe = {str(symbol): str(name).strip() for symbol, name in raw_universe.items()}
    origins = {
        str(symbol): str(origin).strip() for symbol, origin in raw_origins.items()
    }
    if (
        not universe
        or set(universe) != set(origins)
        or set(research.get("symbols") or {}) != set(universe)
        or any(
            len(symbol) != 6 or not symbol.isdigit() or not name
            for symbol, name in universe.items()
        )
        or any(
            origin
            not in {
                "established_widget_symbol",
                "operator_enrolled_research_watch",
                "completed_daily_recommendation_auto_discovery",
                "causal_scanner_research_admission",
            }
            for origin in origins.values()
        )
        or any(universe.get(symbol) != name for symbol, name in SYMBOLS.items())
        or any(origins.get(symbol) != "established_widget_symbol" for symbol in SYMBOLS)
    ):
        raise ValueError("widget_symbol_research_universe_invalid")
    return universe, origins


def _normalized_selected_parameters(selected: object) -> dict[str, Any] | None:
    if not isinstance(selected, dict):
        return None
    required = {
        "segment",
        "lookback_bars",
        "drawdown_pct",
        "near_low_pct",
        "reclaim_ticks",
        "target_bps",
        "max_completed_entries_per_day",
        "setup_valid_bars",
        "reentry_cooldown_bars",
        "force_flat_time",
    }
    optional = {
        "anchor_mode",
        "minimum_history_bars",
        "max_reclaim_chase_ticks",
    }
    if not required.issubset(selected) or set(selected) - required - optional:
        return None
    try:
        lookback = int(selected["lookback_bars"])
        drawdown = float(selected["drawdown_pct"])
        near_low = float(selected["near_low_pct"])
        reclaim_ticks = int(selected["reclaim_ticks"])
        target_bps = int(selected["target_bps"])
        max_entries = int(selected["max_completed_entries_per_day"])
        setup_valid = int(selected["setup_valid_bars"])
        cooldown = int(selected["reentry_cooldown_bars"])
        minimum_history = int(selected.get("minimum_history_bars", lookback))
        max_reclaim_chase_ticks = int(selected.get("max_reclaim_chase_ticks", 2))
    except (TypeError, ValueError):
        return None
    segment = str(selected["segment"])
    anchor_mode = str(selected.get("anchor_mode", "rolling"))
    segment_windows = {
        "morning": ("09:03:00", "10:30:00"),
        "midday": ("10:30:00", "13:30:00"),
        "afternoon": ("13:30:00", "15:00:00"),
    }
    if (
        segment not in segment_windows
        or lookback not in {15, 30, 45}
        or anchor_mode not in {"rolling", "session"}
        or not 2 <= minimum_history <= lookback
        or max_reclaim_chase_ticks not in {2, 6}
        or (max_reclaim_chase_ticks != 2 and segment != "morning")
        or not 0.5 <= drawdown <= 2.0
        or not 0.2 <= near_low <= 0.75
        or reclaim_ticks not in {1, 2}
        or not 30 <= target_bps <= 100
        or not 1 <= max_entries <= 5
        or setup_valid != 5
        or cooldown != 10
        or str(selected["force_flat_time"]) != "15:19:00"
    ):
        return None
    start_time, end_time = segment_windows[segment]
    signal_policy = {
        "segment": segment,
        "segment_start_time": start_time,
        "segment_end_time": end_time,
        "lookback_bars": lookback,
        "drawdown_pct": drawdown,
        "near_low_pct": near_low,
        "reclaim_ticks": reclaim_ticks,
        "target_bps": target_bps,
        "setup_valid_bars": setup_valid,
        "reentry_cooldown_bars": cooldown,
        "force_flat_time": "15:19:00",
    }
    if "anchor_mode" in selected:
        signal_policy["anchor_mode"] = anchor_mode
    if "minimum_history_bars" in selected:
        signal_policy["minimum_history_bars"] = minimum_history
    if "max_reclaim_chase_ticks" in selected:
        signal_policy["max_reclaim_chase_ticks"] = max_reclaim_chase_ticks
    return {
        "signal_policy": signal_policy,
        "execution_policy": {
            "session": "KRX_REGULAR",
            "market_venue": "KRX",
            "allowed_entry_sessions": ["KRX_REGULAR"],
            "allowed_entry_venues": ["KRX"],
            "allowed_entry_states": ["ENTRY_CAUTION", "ENTRY_READY"],
            "leg_quantity_each": EPISODE_LEG_QUANTITY,
            "add_trigger_bps_from_initial_fill": [],
            "take_profit_bps_from_equal_share_average": target_bps,
            "max_completed_entries_per_day": max_entries,
            "reentry_cooldown_minutes": cooldown,
            "new_entry_cutoff_time": end_time,
            "force_flat_at_session_end": True,
            "force_exit_time": "15:19:00",
            "overnight_forbidden": True,
            "source_final_exit_action": "sell_own_filled_quantity",
        },
    }


def _validated_selected_policy(result: object) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    if "component_selection" in result:
        from src.engine.monitoring.widget_signal_quality import select_policy_component

        try:
            comparison = result["component_comparison"]
            selection = select_policy_component(comparison)
            chosen = comparison["arms"][selection["selected_arm"]]
            expected = {
                key: value
                for key, value in chosen["parameters"].items()
                if key not in {"segment_start_time", "segment_end_time"}
            }
            if (
                selection != result["component_selection"]
                or expected != result.get("selected_policy")
                or any(
                    result.get(window) != chosen.get(window)
                    for window in (
                        "calibration",
                        "calibration_first_half",
                        "calibration_second_half",
                        "holdout",
                    )
                )
            ):
                return None
        except (KeyError, ValueError, TypeError, AttributeError):
            return None
    calibration = result.get("calibration")
    first = result.get("calibration_first_half")
    second = result.get("calibration_second_half")
    holdout = result.get("holdout")
    if not all(
        isinstance(value, dict) for value in (calibration, first, second, holdout)
    ):
        return None
    selected = result.get("selected_policy")
    try:
        max_entries = int(
            selected.get("max_completed_entries_per_day")
            if isinstance(selected, dict)
            else 0
        )
    except (TypeError, ValueError):
        max_entries = 0
    if (
        result.get("decision") != "holdout_pass_widget_signal_policy_candidate"
        or result.get("runtime_effect") is not False
        or result.get("allowed_runtime_apply") is not False
        or not _positive_metric(calibration, "notional_weighted_ev_pct")
        or not _positive_metric(first, "notional_weighted_ev_pct")
        or not _positive_metric(second, "notional_weighted_ev_pct")
        or not _positive_metric(holdout, "notional_weighted_ev_pct")
        or int(holdout.get("episode_count") or 0) < 4
        or not _high_entry_cap_evidence_valid(result, max_entries)
    ):
        return None
    return _normalized_selected_parameters(selected)


def _validated_observation_policy(result: object) -> dict[str, Any] | None:
    """Return a source-only policy for prospective exact-data collection."""

    if not isinstance(result, dict) or result.get("runtime_effect") is not False:
        return None
    selected = result.get("selected_policy")
    if not isinstance(selected, dict):
        diagnostic = result.get("best_diagnostic_candidate")
        selected = (
            diagnostic.get("parameters") if isinstance(diagnostic, dict) else None
        )
    normalized = _normalized_selected_parameters(selected)
    if normalized is None:
        return None
    return {
        "signal_policy": normalized["signal_policy"],
        "observation_authority": "prospective_exact_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _observation_effective_at(
    research: dict[str, Any], effective_date: date, hour: int, minute: int
) -> str:
    boundary = datetime.combine(
        effective_date, datetime.min.time(), tzinfo=KST
    ).replace(hour=hour, minute=minute)
    try:
        registered = datetime.fromisoformat(str(research.get("generated_at_kst") or ""))
        if registered.tzinfo is not None:
            boundary = max(boundary, registered.astimezone(KST))
    except ValueError:
        pass  # Legacy evidence keeps unknown registration explicit, never refreshed.
    return boundary.isoformat()


CLOSED_LOOP_POLICY_SCHEMA = "widget_symbol_runtime_policy_v2"


def build_policy(
    research: dict[str, Any],
    *,
    evidence_report_path: Path | None = None,
    legacy_observation_enrollment: bool = False,
    reader_validation: bool = False,
    incumbent_policy_dir: Path | None = None,
) -> dict[str, Any]:
    if (
        research.get("schema") not in SUPPORTED_RESEARCH_SCHEMAS
        or research.get("status") != "complete"
        or research.get("start_date") != CLEAN_BASELINE_DATE.isoformat()
        or research.get("runtime_effect") is not False
        or research.get("allowed_runtime_apply") is not False
        or research.get("actual_order_submitted") is not False
        or research.get("broker_order_forbidden") is not True
        or (research.get("owner_contract") or {}).get("owner") != OWNER
        or (research.get("owner_contract") or {}).get("authority") != RESEARCH_AUTHORITY
        or research.get("metric_contract") != RESEARCH_METRIC_CONTRACT
    ):
        raise ValueError("widget_symbol_research_contract_invalid")
    universe, origins = _research_universe(research)
    source_meta = research.get("source_meta")
    if not isinstance(source_meta, dict):
        raise ValueError("widget_symbol_research_krx_source_provenance_invalid")
    quarantine = research.get("source_quarantine", {})
    if (
        not isinstance(quarantine, dict)
        or not set(quarantine).issubset(universe)
        or type(research.get("quarantined_source_symbol_count", 0)) is not int
        or research.get("quarantined_source_symbol_count", 0) != len(quarantine)
        or len(quarantine) == len(universe)
    ):
        raise ValueError("widget_symbol_research_source_quarantine_invalid")
    for symbol, reason in quarantine.items():
        result = (research.get("symbols") or {}).get(symbol) or {}
        meta = (source_meta or {}).get(symbol) or {}
        if not isinstance(result, dict) or not isinstance(meta, dict):
            raise ValueError("widget_symbol_research_source_quarantine_invalid")
        if (
            reason not in {
                f"{symbol}_daily_source_coverage_fail", f"{symbol}_snapshot_coverage_incomplete",
                f"{symbol}_source_quality_not_pass", f"{symbol}_source_quality_fail",
            }
            or result.get("decision") != "source_quality_quarantined_no_evaluation"
            or result.get("source_quality_reason") != reason
            or result.get("runtime_effect") is not False
            or result.get("allowed_runtime_apply") is not False
            or meta.get("source_quality_status") != "FAIL"
            or meta.get("source_quality_reason") != reason
            or symbol in research.get("passed_symbols", [])
        ):
            raise ValueError("widget_symbol_research_source_quarantine_invalid")
    if not isinstance(source_meta, dict) or any(
        not isinstance(source_meta.get(symbol), dict)
        or source_meta[symbol].get("symbol") != symbol
        or source_meta[symbol].get("request_code") != symbol
        or source_meta[symbol].get("market") != "KRX_regular"
        or source_meta[symbol].get("source_quality_status") != "PASS"
        or source_meta[symbol].get("source_role") == "synthetic_frozen_benchmark_only"
        for symbol in universe if symbol not in quarantine
    ):
        raise ValueError("widget_symbol_research_krx_source_provenance_invalid")
    source_date = date.fromisoformat(str(research.get("end_date") or ""))
    effective_date = next_krx_trading_date(source_date)
    evidence_path = evidence_report_path or (
        DEFAULT_RESEARCH_DIR
        / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
    )
    symbols: dict[str, Any] = {}
    observation_symbols: dict[str, Any] = {}
    quality_by_symbol = research.get("execution_quality_by_symbol")
    require_execution_quality = (
        source_date >= date(2026, 9, 9) or quality_by_symbol is not None
    )
    quality_blocks: dict[str, str] = {}
    from src.engine.monitoring import research_closed_loop as loop

    closed_loop = research.get("closed_loop_contract") == loop.SCHEMA
    joint_gate = (
        loop.report_joint_gate(research, source_date=source_date)
        if closed_loop
        else None
    )
    if closed_loop and joint_gate != research.get("joint_allocation_gate"):
        raise ValueError("widget_joint_allocation_reconstruction_mismatch")
    from src.engine.monitoring.research_version_outcomes import (
        outcome_feedback,
        mature_widget_retired_revisions,
    )

    feedback = outcome_feedback(source_date) if closed_loop else {}
    if (
        closed_loop
        and research.get("policy_version_feedback") is not None
        and research["policy_version_feedback"] != feedback
    ):
        raise ValueError("widget_native_version_feedback_reconstruction_mismatch")
    retired_revisions = mature_widget_retired_revisions(feedback)
    incumbent_by_symbol = (
        WidgetSymbolRuntimePolicyLoader(
            incumbent_policy_dir or DEFAULT_POLICY_DIR
        ).resolve_all(observed_date=source_date)
        if source_date >= date(2026, 9, 17)
        else {}
    )
    for symbol, name in universe.items():
        result = (research.get("symbols") or {}).get(symbol)
        if symbol in quarantine:
            quality_blocks[symbol] = "source_quality_quarantined_no_evaluation"
            continue
        if research.get("schema") in {
            "widget_symbol_signal_policy_research_v3",
            REPORT_SCHEMA,
        } and isinstance(result, dict):
            selected_contract = result.get("selected_policy")
            if not isinstance(selected_contract, dict):
                diagnostic = result.get("best_diagnostic_candidate")
                selected_contract = (
                    diagnostic.get("parameters")
                    if isinstance(diagnostic, dict)
                    else None
                )
            if isinstance(selected_contract, dict) and not {
                "anchor_mode",
                "minimum_history_bars",
                "max_reclaim_chase_ticks",
            }.issubset(selected_contract):
                raise ValueError("widget_symbol_research_v3_parameters_missing")
        observation = (
            _validated_observation_policy(result)
            if not legacy_observation_enrollment
            or origins[symbol] == "established_widget_symbol"
            else None
        )
        if observation is not None:
            observation_symbols[symbol] = {
                "name": name,
                **observation,
                "seed_id": _payload_sha256(
                    {
                        "symbol": symbol,
                        "source": _payload_sha256(research),
                        "parameters": observation["signal_policy"],
                        "effective_date": effective_date.isoformat(),
                    }
                ),
                "parameters_sha256": _payload_sha256(observation["signal_policy"]),
                "source_report_sha256": _payload_sha256(research),
                "registered_at_kst": research.get("generated_at_kst"),
                "effective_at_kst": _observation_effective_at(
                    research, effective_date, 9, 3
                ),
                "aftermarket_effective_at_kst": _observation_effective_at(
                    research, effective_date, 16, 3
                ),
                "session_authority": {
                    "KRX_REGULAR": "prospective_observation_only",
                    "KRX_NXT_AFTERMARKET": "prospective_reference_seed_no_transferred_economics",
                },
            }
        revision = (
            result.get("candidate_revision") if isinstance(result, dict) else None
        )
        if closed_loop and revision is not None:
            loop.validate_revision(revision, symbol=symbol, owner="widget")
            frozen = (
                revision
                if reader_validation and loop.registered_revision(revision)
                else loop.load_candidate(symbol)
            )
            if frozen != revision or revision["parameters"] != result.get(
                "selected_policy"
            ):
                raise ValueError("widget_frozen_candidate_reconstruction_mismatch")
            if symbol in observation_symbols:
                observation_symbols[symbol].update(
                    seed_id=revision["revision_sha256"],
                    registered_at_kst=revision["frozen_at"],
                    effective_at_kst=revision["calibration_dates"][0]
                    + "T09:03:00+09:00",
                    candidate_revision_sha256=revision["revision_sha256"],
                )
        if (
            legacy_observation_enrollment
            and symbol in observation_symbols
            and not closed_loop
        ):
            observation_symbols[symbol] = {"name": name, **observation}
        if revision is not None and revision["revision_sha256"] in retired_revisions:
            quality_blocks[symbol] = "mature_nonperforming_revision_entry_retired"
            continue
        selected = _validated_selected_policy(result)
        if selected is None:
            continue
        if legacy_observation_enrollment and observation is None:
            observation = _validated_observation_policy(result)
            if observation is not None:
                observation_symbols[symbol] = {"name": name, **observation}
        if (
            source_date >= date(2026, 9, 9)
            and isinstance(result.get("component_comparison"), dict)
            and result["component_comparison"].get("arms")
            and "component_selection" not in result
        ):
            quality_blocks[symbol] = "component_selection_contract_missing"
            continue
        if source_date >= date(2026, 9, 17):
            from src.engine.monitoring.policy_research_economics import (
                signal_execution_feasibility,
            )
            from src.engine.monitoring.widget_symbol_runtime_contract import (
                DEFAULT_OBSERVATION_DIR,
            )

            # Exact unchanged incumbent is carry, not a new proxy promotion.
            incumbent = incumbent_by_symbol.get(symbol)
            unchanged = isinstance(incumbent, dict) and all(
                incumbent.get(key) == selected.get(key)
                for key in ("signal_policy", "execution_policy")
            )
            if not unchanged:
                if source_date >= date(2026, 9, 17) and not closed_loop:
                    quality_blocks[symbol] = "closed_loop_evidence_contract_missing"
                    continue
                if closed_loop and (joint_gate or {}).get("status") != "pass":
                    quality_blocks[symbol] = "joint_allocation_blocked"
                    continue
                if closed_loop and revision is not None:
                    prospective = result.get("prospective_window") or {}
                    qualified = (
                        (source_meta.get(symbol) or {}).get("daily_source_coverage")
                        or {}
                    ).get("qualified_dates", [])
                    if (
                        loop.prospective_window(
                            revision, source_date=source_date, qualified_dates=qualified
                        )
                        != prospective
                        or prospective.get("status") != "ready"
                    ):
                        quality_blocks[symbol] = "prospective_calendar_not_validated"
                        continue
                feasibility = (
                    {
                        "status": "pass"
                        if loop.verified_execution_receipt(
                            result.get("execution_feasibility") or {}
                        )
                        else "source_gap"
                    }
                    if reader_validation and closed_loop
                    else signal_execution_feasibility(
                        result,
                        symbol=symbol,
                        source_date=source_date,
                        signal_policy=selected["signal_policy"],
                        observation_dir=DEFAULT_OBSERVATION_DIR,
                    )
                )
                if feasibility["status"] != "pass":
                    quality_blocks[symbol] = (
                        "selected_proxy_execution_feasibility_missing"
                    )
                    continue
        if require_execution_quality:
            quality = (
                quality_by_symbol.get(symbol)
                if isinstance(quality_by_symbol, dict)
                else None
            )
            if (
                not isinstance(quality, dict)
                or quality.get("schema") != "widget_execution_incidents_v1"
                or quality.get("symbol") != symbol
                or quality.get("owner") != EXECUTION_OWNER
                or quality.get("session") != "KRX_REGULAR"
                or quality.get("source_target_date") != source_date.isoformat()
                or quality.get("runtime_apply_allowed") is not True
                or quality.get("source_gap_count") != 0
                or quality.get("unresolved_incident_count") != 0
                or quality.get("same_day_failure_event_count") != 0
                or not isinstance(quality.get("incidents"), list)
                or quality.get("incident_count") != len(quality.get("incidents", []))
                or any(
                    not isinstance(item, dict)
                    or item.get("status")
                    not in {
                        "resolved_exact_full_fill",
                        "resolved_exact_zero_fill_cancel",
                        "resolved_exact_manual_custody_flat",
                        "closed_definitive_rejection_no_order",
                    }
                    for item in quality.get("incidents", [])
                )
            ):
                quality_blocks[symbol] = "execution_incident_unresolved_or_source_gap"
                continue
        symbols[symbol] = {
            "name": name,
            **selected,
            "evidence": {
                "calibration": result["calibration"],
                "calibration_first_half": result["calibration_first_half"],
                "calibration_second_half": result["calibration_second_half"],
                "holdout": {
                    key: value
                    for key, value in result["holdout"].items()
                    if key != "episodes"
                },
                "entry_cap_comparison": result.get("entry_cap_comparison"),
            },
        }
    if closed_loop:
        for symbol, incumbent in incumbent_by_symbol.items():
            if incumbent.get("candidate_revision_sha256") in retired_revisions:
                quality_blocks[symbol] = "mature_nonperforming_revision_entry_retired"
                continue
            if symbol in symbols or symbol not in universe:
                continue
            quality = (quality_by_symbol or {}).get(symbol) or {}
            if (
                quality.get("schema") != "widget_execution_incidents_v1"
                or quality.get("symbol") != symbol
                or quality.get("owner") != EXECUTION_OWNER
                or quality.get("session") != "KRX_REGULAR"
                or quality.get("source_target_date") != str(source_date)
                or quality.get("runtime_apply_allowed") is not True
                or any(
                    quality.get(key) != 0
                    for key in (
                        "source_gap_count",
                        "unresolved_incident_count",
                        "same_day_failure_event_count",
                    )
                )
            ):
                continue
            try:
                parent = loop.read_object(
                    Path(incumbent["policy_path"]), limit=32 * 1024 * 1024
                )
                original = parent["symbols"][symbol]
                symbols[symbol] = {
                    **original,
                    "selection_status": "verified_incumbent_carry",
                    "parent_policy_content_sha256": incumbent["policy_content_sha256"],
                    "candidate_revision_sha256": incumbent.get(
                        "candidate_revision_sha256"
                    ),
                }
            except (OSError, ValueError, KeyError, TypeError):
                quality_blocks[symbol] = "verified_incumbent_parent_missing"
    return {
        "schema": CLOSED_LOOP_POLICY_SCHEMA if closed_loop else POLICY_SCHEMA,
        **(
            {
                "closed_loop_contract": loop.SCHEMA,
                "joint_allocation_gate": joint_gate,
                "version_feedback_sha256": loop.digest(feedback),
                "retired_candidate_revision_sha256": sorted(retired_revisions),
            }
            if closed_loop
            else {}
        ),
        **({} if legacy_observation_enrollment else {"observation_catalog_version": 2}),
        "status": (
            "verified"
            if symbols
            else "observation_only"
            if observation_symbols
            else "no_ready_policy"
        ),
        "policy_version": (
            f"widget_symbol_runtime_policy_{effective_date.isoformat()}_"
            f"from_{source_date.isoformat()}"
        ),
        "source_target_date": source_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "evidence_report_path": str(evidence_path.resolve()),
        "evidence_report_sha256": _payload_sha256(research),
        "source_quality_status": "PASS",
        "official_reference": OFFICIAL_REFERENCE,
        "authority": POLICY_AUTHORITY,
        "owner": OWNER,
        **(
            {"symbol_universe": universe, "symbol_origins": origins}
            if research.get("symbol_universe") is not None
            else {}
        ),
        "symbols": symbols,
        **(
            {"execution_quality_blocks": quality_blocks}
            if require_execution_quality or quality_blocks
            else {}
        ),
        "observation_symbols": observation_symbols,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": bool(symbols),
        "observation_runtime_effect": bool(observation_symbols),
        "actual_order_submitted": False,
        "broker_order_forbidden": not bool(symbols),
    }


OBSERVATION_CATALOG_SCHEMA = "widget_symbol_observation_catalog_v1"
OBSERVATION_CATALOG_PREFIX = "widget_symbol_observation_catalog"
OBSERVATION_CATALOG_AUTHORITY = "prospective_exact_observation_only"


def build_observation_catalog(
    research: dict[str, Any],
    *,
    evidence_report_path: Path | None = None,
    reader_validation: bool = False,
    incumbent_policy_dir: Path | None = None,
) -> dict[str, Any]:
    expanded = build_policy(
        research,
        evidence_report_path=evidence_report_path,
        reader_validation=reader_validation,
        incumbent_policy_dir=incumbent_policy_dir,
    )
    execution = build_policy(
        research,
        evidence_report_path=evidence_report_path,
        legacy_observation_enrollment=True,
        reader_validation=reader_validation,
        incumbent_policy_dir=incumbent_policy_dir,
    )
    return {
        **expanded,
        "schema": OBSERVATION_CATALOG_SCHEMA,
        "authority": OBSERVATION_CATALOG_AUTHORITY,
        "status": (
            "observation_only" if expanded["observation_symbols"] else "no_ready_policy"
        ),
        "symbols": {},
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "execution_catalog_sha256": _payload_sha256(execution),
    }


class WidgetSymbolRuntimePolicyLoader:
    """Load only a verified policy whose effective date is exactly today."""

    def __init__(
        self,
        policy_dir: Path = DEFAULT_POLICY_DIR,
        *,
        research_dir: Path = DEFAULT_RESEARCH_DIR,
    ) -> None:
        self.policy_dir = policy_dir
        self.research_dir = research_dir

    def resolve_all(self, *, observed_date: date) -> dict[str, dict[str, Any]]:
        path = self.policy_dir / f"{POLICY_PREFIX}_{observed_date.isoformat()}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if (
            not isinstance(payload, dict)
            or payload.get("schema") not in {POLICY_SCHEMA, CLOSED_LOOP_POLICY_SCHEMA}
            or payload.get("status") != "verified"
            or payload.get("effective_date") != observed_date.isoformat()
            or payload.get("authority") != POLICY_AUTHORITY
            or payload.get("owner") != OWNER
            or payload.get("metric_contract") != METRIC_CONTRACT
            or payload.get("runtime_effect") is not True
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not False
            or payload.get("source_quality_status") != "PASS"
        ):
            return {}
        try:
            source_date = date.fromisoformat(
                str(payload.get("source_target_date") or "")
            )
        except ValueError:
            return {}
        if (
            source_date >= observed_date
            or next_krx_trading_date(source_date) != observed_date
        ):
            return {}
        evidence_path = Path(str(payload.get("evidence_report_path") or ""))
        if not evidence_path.is_absolute():
            evidence_path = self.research_dir / evidence_path.name
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(evidence, dict) or _payload_sha256(evidence) != str(
            payload.get("evidence_report_sha256") or ""
        ):
            return {}
        try:
            if payload.get("schema") == CLOSED_LOOP_POLICY_SCHEMA:
                from src.engine.monitoring.research_closed_loop import (
                    verify_publication,
                )

                verify_publication(
                    self.policy_dir,
                    effective_date=observed_date,
                    name=path.name,
                    value=payload,
                )
            reconstructed = build_policy(
                evidence,
                reader_validation=payload.get("schema") == CLOSED_LOOP_POLICY_SCHEMA,
                incumbent_policy_dir=self.policy_dir,
                evidence_report_path=evidence_path,
                legacy_observation_enrollment=payload.get("observation_catalog_version")
                is None,
            )
            universe, _origins = _research_universe(evidence)
        except (TypeError, ValueError):
            return {}
        if reconstructed != payload:
            return {}
        symbols = payload.get("symbols")
        if not isinstance(symbols, dict):
            return {}
        resolved: dict[str, dict[str, Any]] = {}
        for symbol, value in symbols.items():
            if symbol not in universe or not isinstance(value, dict):
                continue
            raw_signal_policy = value.get("signal_policy")
            raw_signal_policy = (
                raw_signal_policy if isinstance(raw_signal_policy, dict) else {}
            )
            signal_keys = {
                "segment",
                "lookback_bars",
                "drawdown_pct",
                "near_low_pct",
                "reclaim_ticks",
                "target_bps",
                "setup_valid_bars",
                "reentry_cooldown_bars",
                "force_flat_time",
                "anchor_mode",
                "minimum_history_bars",
                "max_reclaim_chase_ticks",
            }
            selected = {
                "selected_policy": {
                    **{
                        key: raw_signal_policy[key]
                        for key in signal_keys
                        if key in raw_signal_policy
                    },
                    "max_completed_entries_per_day": (
                        value.get("execution_policy") or {}
                    ).get("max_completed_entries_per_day"),
                },
                "calibration": (value.get("evidence") or {}).get("calibration"),
                "calibration_first_half": (value.get("evidence") or {}).get(
                    "calibration_first_half"
                ),
                "calibration_second_half": (value.get("evidence") or {}).get(
                    "calibration_second_half"
                ),
                "holdout": (value.get("evidence") or {}).get("holdout"),
                "entry_cap_comparison": (value.get("evidence") or {}).get(
                    "entry_cap_comparison"
                ),
                "decision": "holdout_pass_widget_signal_policy_candidate",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
            normalized = _validated_selected_policy(selected)
            if normalized is None or normalized["signal_policy"] != value.get(
                "signal_policy"
            ):
                continue
            execution = normalized["execution_policy"]
            if execution != value.get("execution_policy"):
                continue
            resolved[symbol] = {
                "symbol": symbol,
                "name": universe[symbol],
                "policy_id": str(payload["policy_version"]),
                "policy_content_sha256": _payload_sha256(payload),
                "closed_loop_contract": payload.get("closed_loop_contract"),
                "joint_gate_sha256": _payload_sha256(
                    payload.get("joint_allocation_gate")
                ),
                "candidate_revision_sha256": value.get("candidate_revision_sha256")
                if value.get("selection_status") == "verified_incumbent_carry"
                else (
                    ((evidence.get("symbols") or {}).get(symbol) or {})
                    .get("candidate_revision", {})
                    .get("revision_sha256")
                ),
                "source_target_date": source_date.isoformat(),
                "effective_date": observed_date.isoformat(),
                "policy_path": str(path.resolve()),
                "signal_policy": normalized["signal_policy"],
                "execution_policy": normalized["execution_policy"],
                "authority": POLICY_AUTHORITY,
                "official_reference": OFFICIAL_REFERENCE,
                "evidence_window": (
                    f"{CLEAN_BASELINE_DATE.isoformat()}_{source_date.isoformat()}"
                ),
                "evidence_artifact": str(
                    DEFAULT_RESEARCH_DIR
                    / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
                ),
            }
        return resolved

    def resolve_observation_all(
        self, *, observed_date: date
    ) -> dict[str, dict[str, Any]]:
        """Load exact-date source-only policies without granting order authority."""

        path = (
            self.policy_dir
            / f"{OBSERVATION_CATALOG_PREFIX}_{observed_date.isoformat()}.json"
        )
        is_catalog = path.exists()
        if not is_catalog:
            path = self.policy_dir / f"{POLICY_PREFIX}_{observed_date.isoformat()}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if (
            not isinstance(payload, dict)
            or payload.get("schema")
            != (OBSERVATION_CATALOG_SCHEMA if is_catalog else POLICY_SCHEMA)
            or payload.get("status") not in {"verified", "observation_only"}
            or payload.get("effective_date") != observed_date.isoformat()
            or payload.get("authority")
            != (OBSERVATION_CATALOG_AUTHORITY if is_catalog else POLICY_AUTHORITY)
            or payload.get("owner") != OWNER
            or payload.get("metric_contract") != METRIC_CONTRACT
            or payload.get("observation_runtime_effect") is not True
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden")
            is not (not bool(payload.get("symbols")))
            or payload.get("source_quality_status") != "PASS"
        ):
            return {}
        if payload.get("closed_loop_contract") is not None:
            try:
                from src.engine.monitoring.research_closed_loop import (
                    verify_publication,
                )

                verify_publication(
                    self.policy_dir,
                    effective_date=observed_date,
                    name=path.name,
                    value=payload,
                )
            except (OSError, ValueError, TypeError):
                return {}
        evidence_path = Path(str(payload.get("evidence_report_path") or ""))
        if not evidence_path.is_absolute():
            evidence_path = self.research_dir / evidence_path.name
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            source_date = date.fromisoformat(
                str(payload.get("source_target_date") or "")
            )
        except (OSError, ValueError):
            return {}
        if (
            source_date >= observed_date
            or next_krx_trading_date(source_date) != observed_date
            or _payload_sha256(evidence)
            != str(payload.get("evidence_report_sha256") or "")
        ):
            return {}
        try:
            reconstructed = (
                build_observation_catalog(
                    evidence,
                    evidence_report_path=evidence_path,
                    reader_validation=bool(payload.get("closed_loop_contract")),
                    incumbent_policy_dir=self.policy_dir,
                )
                if is_catalog
                else build_policy(
                    evidence,
                    evidence_report_path=evidence_path,
                    legacy_observation_enrollment=payload.get(
                        "observation_catalog_version"
                    )
                    is None,
                )
            )
            universe, _origins = _research_universe(evidence)
        except (TypeError, ValueError):
            return {}
        if reconstructed != payload or (
            is_catalog
            and (
                payload.get("runtime_effect") is not False
                or payload.get("allowed_runtime_apply") is not False
                or payload.get("symbols") != {}
            )
        ):
            return {}
        resolved: dict[str, dict[str, Any]] = {}
        observation_symbols = payload.get("observation_symbols")
        if not isinstance(observation_symbols, dict):
            return {}
        for symbol, value in observation_symbols.items():
            if symbol not in universe or not isinstance(value, dict):
                continue
            result = (evidence.get("symbols") or {}).get(symbol)
            normalized = _validated_observation_policy(result)
            if normalized is None or normalized["signal_policy"] != value.get(
                "signal_policy"
            ):
                continue
            resolved[symbol] = {
                "symbol": symbol,
                "name": universe[symbol],
                "policy_id": str(payload["policy_version"]),
                "policy_content_sha256": _payload_sha256(payload),
                "closed_loop_contract": payload.get("closed_loop_contract"),
                "joint_gate_sha256": _payload_sha256(
                    payload.get("joint_allocation_gate")
                ),
                "candidate_revision_sha256": value.get("candidate_revision_sha256")
                if value.get("selection_status") == "verified_incumbent_carry"
                else (
                    ((evidence.get("symbols") or {}).get(symbol) or {})
                    .get("candidate_revision", {})
                    .get("revision_sha256")
                ),
                "source_target_date": source_date.isoformat(),
                "effective_date": observed_date.isoformat(),
                "policy_path": str(path.resolve()),
                **{
                    key: value.get(key)
                    for key in (
                        "seed_id",
                        "parameters_sha256",
                        "source_report_sha256",
                        "registered_at_kst",
                        "effective_at_kst",
                        "aftermarket_effective_at_kst",
                        "session_authority",
                    )
                },
                "signal_policy": normalized["signal_policy"],
                "integrated_aftermarket_observation_policy": {
                    **normalized["signal_policy"],
                    "segment": "integrated_aftermarket_prospective",
                    "segment_start_time": "16:03:00",
                    "segment_end_time": "19:20:00",
                    "force_flat_time": "19:44:00",
                },
                "integrated_aftermarket_observation_authority": (
                    "prospective_frozen_seed_requires_session_specific_outcomes"
                ),
                "authority": "prospective_exact_observation_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        return resolved


def write_outputs(
    research: dict[str, Any],
    *,
    policy_dir: Path = DEFAULT_POLICY_DIR,
    apply_report_dir: Path = DEFAULT_APPLY_REPORT_DIR,
    evidence_report_path: Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    policy = build_policy(
        research,
        evidence_report_path=evidence_report_path,
        legacy_observation_enrollment=True,
        incumbent_policy_dir=policy_dir,
    )
    catalog = build_observation_catalog(
        research,
        evidence_report_path=evidence_report_path,
        incumbent_policy_dir=policy_dir,
    )
    effective_date = date.fromisoformat(policy["effective_date"])
    policy_path = policy_dir / f"{POLICY_PREFIX}_{effective_date.isoformat()}.json"
    catalog_path = (
        policy_dir / f"{OBSERVATION_CATALOG_PREFIX}_{effective_date.isoformat()}.json"
    )
    if policy.get("schema") == CLOSED_LOOP_POLICY_SCHEMA:
        from src.engine.monitoring.research_closed_loop import (
            publication_transaction,
            future_publication_parent,
        )

        publication_transaction(
            policy_dir,
            effective_date=effective_date,
            files={policy_path.name: policy, catalog_path.name: catalog},
            expected_generation=future_publication_parent(policy_dir, effective_date),
        )
    else:
        _atomic_write(catalog_path, catalog)
        _atomic_write(policy_path, policy)
    loaded = WidgetSymbolRuntimePolicyLoader(policy_dir).resolve_all(
        observed_date=effective_date
    )
    observed = WidgetSymbolRuntimePolicyLoader(policy_dir).resolve_observation_all(
        observed_date=effective_date
    )
    expected = set(policy["symbols"]) if policy["status"] == "verified" else set()
    verification = {
        "status": (
            "pass"
            if set(loaded) == expected
            and set(observed) == set(catalog["observation_symbols"])
            else "fail"
        ),
        "expected_symbols": sorted(expected),
        "loaded_symbols": sorted(loaded),
        "expected_observation_symbols": sorted(catalog["observation_symbols"]),
        "loaded_observation_symbols": sorted(observed),
        "policy_path": str(policy_path),
    }
    apply_report = {
        "schema": "widget_symbol_runtime_policy_apply_report_v1",
        "status": "complete" if verification["status"] == "pass" else "failed",
        "source_target_date": policy["source_target_date"],
        "effective_date": policy["effective_date"],
        "selected_symbols": sorted(expected),
        "withheld_symbols": sorted(set(_research_universe(research)[0]) - expected),
        "policy_status": policy["status"],
        "observation_catalog_path": str(catalog_path),
        "observation_catalog_sha256": _payload_sha256(catalog),
        "observation_catalog_runtime_effect": False,
        "policy_verification": verification,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }
    report_path = apply_report_dir / (
        f"widget_symbol_runtime_policy_apply_{policy['source_target_date']}.json"
    )
    _atomic_write(report_path, apply_report)
    if verification["status"] != "pass":
        raise RuntimeError("widget_symbol_runtime_policy_round_trip_failed")
    return policy_path, report_path, apply_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument(
        "--apply-report-dir", type=Path, default=DEFAULT_APPLY_REPORT_DIR
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-active", action="store_true")
    parser.add_argument("--check-observation-scope", action="store_true")
    args = parser.parse_args(argv)
    if args.check_active or args.check_observation_scope:
        target = (
            date.fromisoformat(args.target_date)
            if args.target_date
            else datetime.now(KST).date()
        )
        active = WidgetSymbolRuntimePolicyLoader(
            args.policy_dir
        ).resolve_observation_all(observed_date=target)
        print(
            json.dumps(
                {
                    "effective_date": target.isoformat(),
                    "active_symbols": sorted(active),
                },
                ensure_ascii=False,
            )
        )
        if args.check_observation_scope:
            from src.engine.monitoring.widget_symbol_signal_policy_research import (
                load_symbol_universe,
            )

            try:
                universe, _origins = load_symbol_universe(observed_date=target)
            except (OSError, ValueError):
                return 3
            print(
                json.dumps(
                    {
                        "raw_observation_symbols": sorted(universe),
                        "order_authority": False,
                    },
                    sort_keys=True,
                )
            )
            return 0 if universe else 3
        return 0 if active else 3
    source_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else resolve_completed_research_end_date()
    )
    research_path = (
        args.research_dir
        / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
    )
    research = json.loads(research_path.read_text(encoding="utf-8"))
    policy = build_policy(research, evidence_report_path=research_path)
    result: dict[str, Any] = {
        "source_target_date": policy["source_target_date"],
        "effective_date": policy["effective_date"],
        "selected_symbols": sorted(policy["symbols"]),
        "policy_status": policy["status"],
        "runtime_effect": False,
    }
    if args.write:
        policy_path, report_path, apply_report = write_outputs(
            research,
            policy_dir=args.policy_dir,
            apply_report_dir=args.apply_report_dir,
            evidence_report_path=research_path,
        )
        result.update(
            {
                "policy_path": str(policy_path),
                "report_path": str(report_path),
                "verification": apply_report["policy_verification"],
            }
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
