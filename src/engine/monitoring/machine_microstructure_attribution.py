"""Join source-only micro-reversion observations to widget/episode machines.

The report is deliberately diagnostic.  It discovers the current machine
universe from target-date postclose artifacts, so a newly added symbol is
represented even when the micro producer did not observe it.  Missing micro
data is never imputed and never blocks the existing owner tuning path.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import gzip
import hashlib
import json
import math
import os
import statistics
import tempfile
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping.micro_reversion.p2_replay import (
    DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    load_source_exclusion_manifest,
)
from src.engine.scalping.micro_reversion.ask_depletion import (
    AskDepletionContext,
    build_ask_depletion_report,
)
from src.engine.scalping.micro_reversion.path_journal import (
    MARKET_STREAM_CONTRACT_ID,
    MarketDepthPoint,
    MarketStreamPoint,
    readable_partition_path_files,
)
from src.engine.scalping.micro_reversion.path_capture import PathEventReference
from src.engine.scalping.micro_reversion.depth_join import (
    validate_depth_row as validate_canonical_depth_row,
)
from src.engine.scalping.micro_reversion.collection_targets import (
    COLLECTION_TARGET_SCHEMA,
    build_collection_targets,
    write_collection_targets,
)
from src.engine.monitoring.machine_lifecycle_turnover_policy_research import (
    build_rolling_paired_policy_research,
)
from src.engine.monitoring.machine_market_weakness_response import (
    build_machine_market_weakness_response,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    modeled_execution_economics,
)
from src.engine.risk.market_weakness_entry_guard import (
    market_weakness_blocked_entry_contract_errors,
)
from src.trading.low_price_two_leg.profiles import PROFILES
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_json_object_strict
from src.utils.market_day import is_krx_trading_day

KST_SUFFIX = "+09:00"
KST = ZoneInfo("Asia/Seoul")
REPORT_TYPE = "machine_microstructure_attribution"
REPORT_SCHEMA = "machine_microstructure_attribution_v1"
OBJECTIVE_FOLLOWUP_SCHEMA = "machine_fast_lifecycle_objective_followup_v1"
FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID = "machine_lifecycle_turnover_policy_research_v1"
OBJECTIVE_CANDIDATE_BINDING_SCHEMA = (
    "machine_fast_lifecycle_objective_candidate_binding_v1"
)
OBJECTIVE_HANDOFF_BINDING_SCHEMA = "machine_fast_lifecycle_objective_handoff_binding_v1"
OBJECTIVE_HANDOFF_RESOLVABLE_GAP_CODES = (
    "rolling_paired_policy_candidate_producer_not_implemented",
    "episode_single_attempt_no_same_day_reentry_tuning_axis",
    "speed_and_capital_occupancy_not_policy_selection_axes",
)
OUTPUT_DIR = DATA_DIR / "report" / REPORT_TYPE
OBSERVATION_ROOT = DATA_DIR / "observations" / "scalp_micro_reversion_forward"
DEFAULT_CANARY_SNAPSHOT_PATH = (
    DATA_DIR / "runtime" / "scalp_micro_reversion_forward_collector" / "latest.json"
)
DEFAULT_WIDGET_AUTO_TRADE_STATE_PATH = (
    DATA_DIR / "runtime" / "widget_signal_auto_trade_state.json"
)
WIDGET_AUTO_TRADE_EVENT_SCHEMA = "widget_signal_auto_trade_event_v1"
WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY = "operator_directed_widget_auto_trade_v1"
WIDGET_BROKER_EXECUTION_VENUES = {"KRX", "NXT", "SOR"}
WIDGET_MANUAL_PARTIAL_EXIT_ROLE = "MANUAL_OPERATOR_PARTIAL_EXIT"
WIDGET_MANUAL_PARTIAL_EXIT_AUTHORITY = "explicit_user_manual_partial_exit"
WIDGET_SESSION_VENUES = {
    "NXT_PREMARKET": "NXT",
    "KRX_REGULAR": "KRX",
    "NXT_AFTERMARKET": "NXT",
}
CANARY_DAILY_SNAPSHOT_DIR = (
    DATA_DIR / "source_quality" / "scalp_micro_reversion_canary_daily"
)
PRE_WINDOW_SEC = 30
POST_WINDOW_SEC = 180
MARKET_WEAKNESS_COUNTERFACTUAL_POST_WINDOW_SEC = 30 * 60
DEPTH_CONTEXT_MAX_AGE_SEC = 5
TIMEOUT_RESEARCH_HORIZONS_SEC = (60, 120, 180)
TIMEOUT_RESEARCH_MAX_QUOTE_AGE_SEC = 5
CANARY_COMPLETE_AFTER_KST = time(20, 0)
GROSS_PROFIT_TOUCH_BPS = (1, 3, 5, 10, 20, 30, 50)
CLEAN_BASELINE_DATE = date(2026, 6, 5)
POSTCLOSE_COMPLETE_TIME = time(20, 0)
ENTRY_CONFIRMATION_HORIZONS_SEC = (1, 3, 5)
ENTRY_CONFIRMATION_MAX_QUOTE_AGE_SEC = 1
MARKET_WEAKNESS_COUNTERFACTUAL_HORIZONS_SEC = (60, 180, 300, 600, 1200, 1800)
MARKET_WEAKNESS_COUNTERFACTUAL_MAX_QUOTE_AGE_SEC = 5
MANUAL_EXIT_FILL_SOURCE = "broker_verified_manual_sell_receipt"
MANUAL_EXIT_PRICE_SOURCE = "broker_manual_sell_receipt"

METRIC_CONTRACT = {
    "metric_role": "machine_lifecycle_microstructure_diagnostic_context",
    "decision_authority": "postclose_diagnostic_only",
    "window_policy": (
        "target_date_signal_entry_submit_fill_target_submit_and_reconciled_exit_anchor_"
        "minus_30s_through_plus_180s_except_market_weakness_entry_counterfactual_"
        "through_plus_1800s"
    ),
    "sample_floor": {
        "per_anchor_eligible_0b_rows": 1,
        "live_or_policy_promotion": "not_permitted",
    },
    "primary_decision_metric": "source_quality_and_lifecycle_anchor_path_coverage",
    "source_quality_gate": [
        "exact_target_date_owner_inventory",
        "exact_target_date_micro_partition",
        "target_date_on_or_after_clean_tuning_baseline",
        "path_consumer_eligible_true_when_present",
        "source_only_authority_flags",
        "physical_partition_venue_session_matches_row_contract",
        "exact_date_complete_fresh_canary_when_requested",
        "valid_symbol_timestamp_and_trade_price",
    ],
    "forbidden_uses": [
        "zero_or_flat_imputation_for_missing_micro_data",
        "replacement_of_owner_policy_ev",
        "real_execution_quality_claim",
        "threshold_or_policy_selection",
        "gross_no_slippage_diagnostic_as_live_or_policy_authority",
        "broker_order_submission",
        "provider_or_bot_or_cap_mutation",
    ],
}
MICRO_ENTRY_CONFIRMATION_CONTRACT = {
    "metric_role": "widget_episode_entry_microstructure_source_only_comparison",
    "decision_authority": (
        "postclose_source_only_input_to_exact_date_entry_timing_tuning"
    ),
    "window_policy": (
        "exact_owner_symbol_venue_session_entry_anchor_then_1s_3s_5s_bbo_and_"
        "fixed_anchor_ask_depletion"
    ),
    "sample_floor": {
        "observed_trading_days_per_owner_symbol_session_state": 5,
        "unique_decision_lifecycles": 20,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "canonical_contiguous_0b_0d_exact_scope_latest_nonfuture_depth_and_"
        "executable_bbo_without_missing_value_imputation_with_manual_exit_"
        "provenance_preserved"
    ),
    "forbidden_uses": [
        "standalone_buy_wait_drop_or_exit_decision",
        "cross_owner_or_cross_entry_state_pooling",
        "broker_order_submission_cancel_or_automated_sell",
        "same_day_or_preopen_runtime_policy_mutation",
        "entry_timing_apply_without_cumulative_floor_and_exact_date_policy",
        "quantity_target_cooldown_daily_cap_or_stop_mutation",
        "provider_bot_broker_guard_or_hard_safety_change",
        "missing_micro_data_as_zero_or_neutral_confirmation",
        "source_only_opportunity_as_realized_broker_profit",
        "manual_operator_exit_as_machine_target_fill_success",
    ],
}
FAST_LIFECYCLE_OBJECTIVE_CONTRACT = {
    "objective": (
        "maximize_cost_aware_cumulative_net_profit_with_fast_entry_holding_exit_"
        "turnover_and_frequent_small_profit_completion"
    ),
    "metric_role": "diagnostic_execution_velocity_and_turnover_context",
    "decision_authority": "postclose_diagnostic_only",
    "window_policy": (
        "per_lifecycle_signal_submit_fill_target_submit_exit_anchor_plus_owner_span"
    ),
    "sample_floor": {
        "daily_diagnostic": 1,
        "policy_or_runtime_change": "uses_policy_change_readiness_not_daily_count",
    },
    "primary_decision_metric": (
        "cost_aware_net_profit_and_source_quality_adjusted_ev_for_policy_authority"
    ),
    "gross_no_slippage_diagnostic": {
        "touch_bps": list(GROSS_PROFIT_TOUCH_BPS),
        "authority": "diagnostic_only",
        "slippage_cost_assumption": "excluded",
        "fees_and_taxes": "not_deducted",
    },
    "source_quality_gate": [
        "owner_lifecycle_timestamp_present_and_timezone_aware",
        "timestamp_order_nonnegative",
        "micro_anchor_source_contract_valid",
        "missing_latency_is_unknown_not_zero",
        "manual_operator_exit_loss_kept_in_cost_aware_realized_outcome",
    ],
    "forbidden_uses": [
        "target_cooldown_cap_entry_validity_quantity_or_force_exit_mutation",
        "held_or_right_censored_as_realized_profit",
        "gross_no_slippage_result_as_live_promotion_evidence",
        "manual_operator_exit_as_autonomous_target_completion",
        "same_day_or_intraday_runtime_mutation",
        "broker_provider_bot_or_hard_safety_change",
    ],
}
POLICY_CHANGE_READINESS_CONTRACT = {
    "current_state": "diagnostic_collection_only",
    "policy_change_allowed": False,
    "daily_report_can_change_policy": False,
    "required_evidence": {
        "minimum_observed_trading_days_per_owner_symbol_session": 5,
        "minimum_policy_eligible_unique_decision_lifecycles_per_owner_symbol_session": 20,
        "minimum_bbo_complete_rate_pct": 95.0,
        "minimum_depth_window_coverage_pct": 90.0,
        "invalid_contract_row_count": 0,
        "comparison": (
            "paired_same_anchor_current_policy_vs_one_micro_conditioned_axis"
        ),
        "primary_metric": "source_quality_adjusted_ev_pct",
        "cost_policy": "fees_taxes_and_slippage_included",
        "rolling_windows_trading_days": [5, 10, 20],
        "required_absolute_ev_uplift": "greater_than_zero_in_all_windows",
        "minimum_relative_primary_ev_uplift_pct": 1.0,
        "required_net_profit": "positive_in_primary_20d_window",
        "downside_guard": "paired_p10_not_worse_and_held_unresolved_not_increased",
    },
    "promotion_boundary": {
        "candidate_timing": "next_session_preopen_exact_date_only",
        "mutation_limit": "one_existing_owner_stage_axis",
        "required_guards": [
            "source_quality_pass",
            "same_stage_owner_conflict_free",
            "before_after_runtime_provenance",
            "rollback_guard",
            "post_apply_attribution",
        ],
        "first_runtime_linkage": (
            "requires_new_runtime_family_mapping_and_explicit_operator_approval"
        ),
        "after_first_approval": (
            "bounded_candidates_may_follow_the_existing_postclose_to_preopen_chain"
        ),
    },
}
PROMOTION_CANDIDATE_INTAKE_CONTRACT = {
    "schema": "machine_microstructure_policy_promotion_candidate_v1",
    "producer_boundary": (
        "rolling_paired_policy_research_after_all_policy_change_readiness_gates"
    ),
    "consumer": ("src.engine.automation.machine_microstructure_policy_approval"),
    "initial_state": "DESIGN_REQUIRED_or_REVIEW_READY",
    "required_runtime_design": [
        "one_registered_bounded_runtime_family",
        "one_same_stage_axis",
        "bounded_before_after_values",
        "rollback_guard",
        "preopen_consumer",
        "post_apply_attribution",
    ],
    "first_operator_approval_required": True,
    "daily_report_runtime_effect": False,
}
OBJECTIVE_FOLLOWUP_METRIC_CONTRACT = {
    "metric_role": "machine_lifecycle_objective_completion_followup",
    "decision_authority": "postclose_followup_tracking_only",
    "window_policy": "daily_until_implementation_evidence_or_candidate_handoff",
    "sample_floor": POLICY_CHANGE_READINESS_CONTRACT["required_evidence"],
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": [
        "exact_target_date_machine_attribution",
        "clean_baseline_only",
        "paired_cost_aware_rolling_evidence_before_candidate_handoff",
    ],
    "forbidden_uses": [
        "promotion_candidate_substitution",
        "operator_approval_substitution",
        "preopen_handoff_or_runtime_family_enrollment",
        "runtime_env_or_threshold_or_order_mutation",
        "provider_bot_cap_or_hard_safety_change",
    ],
}
OWNER_DIAGNOSTIC_HANDOFF_CONTRACT = {
    "mode": "next_trading_day_owner_report_diagnostic_ingestion",
    "selection_effect": False,
    "missing_or_invalid_effect": "base_owner_policy_unchanged",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "broker_order_forbidden": True,
}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_target_json(
    path: Path,
    target_date: str,
    *,
    date_fields: tuple[str, ...] = ("target_date",),
    expected_schemas: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    payload = _read_json(path)
    if payload is None or not any(
        payload.get(field) == target_date for field in date_fields
    ):
        return None
    if expected_schemas and payload.get("schema") not in expected_schemas:
        return None
    return payload


def _market_weakness_blocked_entry_inventory(
    target_date: str, report_root: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_dir = report_root / "machine_market_weakness_blocked_entries" / target_date
    anchors: list[dict[str, Any]] = []
    errors: list[str] = []
    invalid_artifact_count = 0
    seen_ids: set[str] = set()
    paths = sorted(
        {
            (
                path.with_name(path.name[: -len(".gz")])
                if path.name.endswith(".json.gz")
                else path
            )
            for pattern in (
                "machine-weakness-block-*.json",
                "machine-weakness-block-*.json.gz",
            )
            for path in source_dir.glob(pattern)
        }
    )
    comparison_cost = (
        comparison_cost_contract(target_date)
        if date.fromisoformat(target_date) >= CLEAN_BASELINE_DATE
        else None
    )
    for path in paths:
        try:
            payload = read_json_object_strict(path)
        except (FileNotFoundError, OSError, TypeError, ValueError):
            payload = None
        observation_id = str((payload or {}).get("observation_id") or "").strip()
        observed_at = _owner_ts_on_target_date(
            (payload or {}).get("observed_at"), target_date
        )
        owner = str((payload or {}).get("owner") or "").strip()
        symbol = str((payload or {}).get("symbol") or "").strip()
        scope_id = str((payload or {}).get("scope_id") or "").strip()
        session = str((payload or {}).get("session") or "").strip().upper()
        venues = (payload or {}).get("expected_venues")
        quantity = (payload or {}).get("required_quantity")
        contract_errors = market_weakness_blocked_entry_contract_errors(
            payload,
            target_date=target_date,
        )
        if observation_id in seen_ids:
            contract_errors.append("blocked_entry_observation_id_duplicate")
        if contract_errors:
            invalid_artifact_count += 1
            errors.extend(f"{reason}:{path.name}" for reason in contract_errors)
            continue
        seen_ids.add(observation_id)
        anchors.append(
            {
                "anchor_id": f"market_weakness_blocked:{observation_id}",
                "lifecycle_id": f"market_weakness_blocked:{observation_id}",
                "owner": owner,
                "scope_id": scope_id,
                "symbol": symbol,
                "session": session,
                "expected_venues": sorted(
                    {str(value).strip().upper() for value in venues}
                ),
                "expected_session_buckets": [session],
                "anchor_at": observed_at.isoformat(),
                "anchor_price": _finite_float(payload.get("reference_price")),
                "owner_target_price": _finite_float(payload.get("target_price")),
                "owner_requested_quantity": int(quantity),
                "owner_round_trip_cost_pct": (
                    comparison_cost.get("round_trip_cost_pct")
                    if comparison_cost is not None
                    else None
                ),
                "owner_round_trip_cost_provenance": (
                    "effective_dated_widget_episode_comparison_cost_contract"
                ),
                "lifecycle_stage": "entry",
                "anchor_role": "actual_market_weakness_blocked_entry_signal",
                "entry_state": "MARKET_WEAKNESS_BLOCKED",
                "entry_timing_decision_anchor_valid": True,
                "source_entry_event_id": observation_id,
                "source_signal_id": payload.get("source_signal_id"),
                "guard_observation_id": payload.get("guard_observation_id"),
                "owner_outcome": {
                    "realized": False,
                    "actual_order_submitted": False,
                    "counterfactual_only": True,
                    "quantity": int(quantity),
                },
                "owner_lifecycle_contract_valid": True,
                "owner_policy_tuning_eligible": True,
                "owner_timing_custody_observation_eligible": True,
                "actual_order_submitted": False,
            }
        )
    return anchors, {
        "path": str(source_dir),
        "status": (
            "loaded" if anchors else ("contract_invalid" if errors else "not_observed")
        ),
        "artifact_count": len(paths),
        "eligible_count": len(anchors),
        "excluded_count": invalid_artifact_count,
        "contract_error_count": len(errors),
        "partition_reconciled": (len(paths) == len(anchors) + invalid_artifact_count),
        "contract_errors": errors,
        "optional_when_absent": True,
    }


def _previous_krx_trading_date(value: date) -> date:
    candidate = value - timedelta(days=1)
    for _ in range(14):
        if is_krx_trading_day(candidate):
            return candidate
        candidate -= timedelta(days=1)
    raise ValueError("previous_krx_trading_date_unresolved")


def resolve_completed_machine_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) >= POSTCLOSE_COMPLETE_TIME
    ):
        return current.date()
    return _previous_krx_trading_date(current.date())


def daily_canary_snapshot_path(
    target_date: date, *, root: Path = CANARY_DAILY_SNAPSHOT_DIR
) -> Path:
    return (
        root / f"scalp_micro_reversion_canary_snapshot_{target_date.isoformat()}.json"
    )


def _canary_snapshot_date(payload: dict[str, Any] | None) -> date | None:
    generated_at = _parse_owner_ts((payload or {}).get("generated_at"))
    return generated_at.astimezone(KST).date() if generated_at is not None else None


def resolve_target_canary_snapshot(
    *,
    target_date: date,
    latest_path: Path | None,
    daily_root: Path = CANARY_DAILY_SNAPSHOT_DIR,
) -> Path | None:
    if latest_path is None:
        return None
    daily_path = daily_canary_snapshot_path(target_date, root=daily_root)
    if _canary_snapshot_date(_read_json(latest_path)) == target_date:
        return latest_path
    if daily_path.exists():
        return daily_path
    return latest_path


def archive_exact_date_canary_snapshot(
    *,
    target_date: date,
    source_path: Path,
    daily_root: Path = CANARY_DAILY_SNAPSHOT_DIR,
    now: datetime | None = None,
) -> Path | None:
    payload = _read_json(source_path)
    if _canary_snapshot_date(payload) != target_date:
        return None
    archived_at = (now or datetime.now(KST)).astimezone(KST)
    generated_at = _parse_owner_ts((payload or {}).get("generated_at"))
    guard = (payload or {}).get("canary_guard") or {}
    collector = (payload or {}).get("collector_snapshot") or {}
    status = guard.get("status") if isinstance(guard, dict) else None
    valid_until_epoch = _finite_float((payload or {}).get("valid_until_epoch"))
    target_day_complete = bool(
        generated_at is not None
        and generated_at.astimezone(KST).time().replace(tzinfo=None)
        >= CANARY_COMPLETE_AFTER_KST
    )
    generation_causal = bool(generated_at is not None and generated_at <= archived_at)
    freshness_valid = bool(
        (
            status == "stopped_clean"
            and isinstance(collector, dict)
            and collector.get("collector_lifecycle") == "closed"
            and collector.get("reference_reconciliation_completed") is True
        )
        or (
            status == "healthy_observer_canary"
            and valid_until_epoch is not None
            and valid_until_epoch >= archived_at.timestamp()
        )
    )
    diagnostic_stop = bool(
        isinstance(guard, dict)
        and guard.get("status") == "stop_required"
        and guard.get("stop_required") is True
    )
    diagnostic_source_exclusion = bool(
        isinstance(guard, dict) and guard.get("raw_row_exclusion_required") is True
    )
    diagnostic_only = diagnostic_stop or diagnostic_source_exclusion
    if not generation_causal or not (
        (target_day_complete and freshness_valid) or diagnostic_only
    ):
        return None
    payload = {
        **payload,
        "archive_validation": {
            "schema": "scalp_micro_reversion_canary_archive_validation_v1",
            "target_date": target_date.isoformat(),
            "archived_at_kst": archived_at.isoformat(),
            "target_day_complete": target_day_complete,
            "source_fresh_at_archive": freshness_valid,
            "source_generated_not_after_archive": True,
            "source_valid_until_epoch": valid_until_epoch,
            "diagnostic_only": diagnostic_only,
            "promotion_evidence_eligible": bool(
                target_day_complete and freshness_valid and not diagnostic_only
            ),
        },
    }
    destination = daily_canary_snapshot_path(target_date, root=daily_root)
    _atomic_write(
        destination,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return destination


def load_prior_owner_diagnostic(
    *,
    target_date: date,
    owner: str,
    report_dir: Path = OUTPUT_DIR,
    source_date: date | None = None,
) -> dict[str, Any]:
    """Load one exact source-date diagnostic without policy authority."""

    consumer_key = {
        "widget": "widget_postclose_tuning",
        "episode": "episode_machine_postclose_tuning",
    }.get(owner)
    if consumer_key is None:
        raise ValueError("unsupported_machine_microstructure_owner")
    resolved_source_date = source_date or _previous_krx_trading_date(target_date)
    path = report_dir / f"{REPORT_TYPE}_{resolved_source_date.isoformat()}.json"
    payload = _read_json(path)
    base = {
        "contract": OWNER_DIAGNOSTIC_HANDOFF_CONTRACT,
        "requested_for_target_date": target_date.isoformat(),
        "source_date": resolved_source_date.isoformat(),
        "source_path": str(path),
        "owner": owner,
        "selection_effect": False,
        "base_policy_unchanged": True,
    }
    if payload is None:
        return {**base, "status": "missing", "owner_payload": None}
    authority = payload.get("authority") or {}
    consumers = payload.get("consumers") or {}
    owner_payload = consumers.get(consumer_key) if isinstance(consumers, dict) else None
    valid = bool(
        payload.get("schema") == REPORT_SCHEMA
        and payload.get("target_date") == resolved_source_date.isoformat()
        and isinstance(authority, dict)
        and authority.get("runtime_effect") is False
        and authority.get("allowed_runtime_apply") is False
        and authority.get("actual_order_submitted") is False
        and authority.get("broker_order_forbidden") is True
        and isinstance(owner_payload, dict)
    )
    if not valid:
        return {**base, "status": "invalid", "owner_payload": None}
    return {
        **base,
        "status": "loaded",
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_status": payload.get("status"),
        "fast_lifecycle_objective_alignment": payload.get(
            "fast_lifecycle_objective_alignment"
        ),
        "owner_payload": owner_payload,
    }


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        try:
            parsed = datetime.fromisoformat(f"{text}{KST_SUFFIX}")
        except ValueError:
            return None
    return parsed


def _parse_owner_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _owner_ts_on_target_date(value: Any, target_date: str) -> datetime | None:
    parsed = _parse_owner_ts(value)
    if parsed is None or parsed.astimezone(KST).date().isoformat() != target_date:
        return None
    return parsed


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _episode_exit_outcome_provenance(
    leg: Mapping[str, Any], *, realized: bool
) -> dict[str, Any]:
    exit_fill_source = str(leg.get("exit_fill_source") or "")
    profit_price_source = str(leg.get("profit_price_source") or "")
    explicit_class = str(leg.get("exit_execution_class") or "")
    if not realized:
        exit_execution_class = "not_realized"
    elif (
        explicit_class == "manual_operator_exit"
        or exit_fill_source == MANUAL_EXIT_FILL_SOURCE
        or profit_price_source == MANUAL_EXIT_PRICE_SOURCE
    ):
        exit_execution_class = "manual_operator_exit"
    elif explicit_class in {"machine_target_fill", "configured_target_price_proxy"}:
        exit_execution_class = explicit_class
    elif profit_price_source == "broker_target_fill_price":
        exit_execution_class = "machine_target_fill"
    elif profit_price_source == "configured_target_price_proxy":
        exit_execution_class = "configured_target_price_proxy"
    else:
        exit_execution_class = "realized_exit_source_unknown"
    net_return = _finite_float(leg.get("net_profit_pct"))
    if net_return is None:
        net_return = _finite_float(leg.get("equal_weight_profit_pct"))
    return {
        "exit_execution_class": exit_execution_class,
        "exit_fill_source": exit_fill_source or None,
        "profit_price_source": profit_price_source or None,
        "manual_exit_realized": bool(
            realized and exit_execution_class == "manual_operator_exit"
        ),
        "autonomous_target_filled": bool(
            realized and exit_execution_class == "machine_target_fill"
        ),
        "realized_loss": bool(realized and net_return is not None and net_return < 0.0),
        "holding_duration_provenance": (
            str(leg.get("lifecycle_timestamp_provenance") or "") or None
        ),
    }


def _episode_exit_anchor_role(
    *, realized: bool, exit_execution_class: str, reconciled: bool = False
) -> str:
    if exit_execution_class == "manual_operator_exit":
        return (
            "episode_manual_exit_reconciled"
            if reconciled
            else "episode_manual_exit_confirmed"
        )
    if realized:
        return (
            "episode_target_fill_reconciled"
            if reconciled
            else "episode_target_fill_confirmed"
        )
    return (
        "episode_target_partial_fill_reconciled"
        if reconciled
        else "episode_target_partial_fill_confirmed"
    )


def _source(
    path: Path,
    payload: dict[str, Any] | None,
    *,
    target_date: str,
    expected_schemas: tuple[str, ...],
    date_fields: tuple[str, ...] = ("target_date",),
) -> dict[str, Any]:
    raw = _read_json(path)
    if payload is not None:
        status = "loaded"
    elif raw is None:
        status = "missing_or_invalid_json"
    elif raw.get("schema") not in expected_schemas:
        status = "schema_mismatch"
    elif not any(raw.get(field) == target_date for field in date_fields):
        status = "target_date_mismatch"
    else:
        status = "contract_invalid"
    return {
        "path": str(path),
        "status": status,
        "schema": (raw or {}).get("schema"),
        "expected_schemas": list(expected_schemas),
    }


def _widget_entry_signal_contract(
    value: Any, *, symbol: str, target_date: str
) -> tuple[str, datetime] | None:
    if not isinstance(value, str):
        return None
    parts = value.strip().split(":", 4)
    if (
        len(parts) != 5
        or parts[0] != symbol
        or parts[1] != target_date
        or parts[2] != "ENTRY"
    ):
        return None
    session = parts[3]
    observed_at = _owner_ts_on_target_date(parts[4], target_date)
    if session not in WIDGET_SESSION_VENUES or observed_at is None:
        return None
    return session, observed_at


def _widget_numeric(value: Any) -> float | None:
    return None if isinstance(value, bool) else _finite_float(value)


def _widget_state_order_index(
    *, target_date: str, state_path: Path
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    try:
        state_bytes = state_path.read_bytes()
        decoded = json.loads(state_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        state_bytes = None
        decoded = None
    payload = decoded if isinstance(decoded, dict) else None
    source = {
        "path": str(state_path),
        "status": "missing",
        "target_date": target_date,
        "sha256": None,
        "order_count": 0,
        "contract_errors": [],
    }
    if payload is None:
        return {}, source
    if (
        payload.get("schema_version") != 1
        or payload.get("execution_authority") != WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY
    ):
        source["status"] = "contract_invalid"
        source["contract_errors"] = ["state_envelope_invalid"]
        return {}, source
    raw_history = payload.get("history")
    if raw_history is not None and not isinstance(raw_history, list):
        source["status"] = "contract_invalid"
        source["contract_errors"] = ["state_history_invalid"]
        return {}, source
    symbol_rows: Any = None
    history_matches = [
        row
        for row in raw_history or []
        if isinstance(row, dict) and row.get("trade_date") == target_date
    ]
    if payload.get("active_date") == target_date:
        if history_matches:
            source["status"] = "contract_invalid"
            source["contract_errors"] = ["duplicate_target_date_state_sources"]
            return {}, source
        symbol_rows = payload.get("symbols")
    else:
        if len(history_matches) == 1:
            symbol_rows = history_matches[0].get("symbols")
        elif len(history_matches) > 1:
            source["status"] = "contract_invalid"
            source["contract_errors"] = ["duplicate_target_date_history"]
            return {}, source
    if not isinstance(symbol_rows, dict):
        source["status"] = "target_date_not_present"
        return {}, source
    index: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[str] = []
    for symbol, symbol_payload in symbol_rows.items():
        if not isinstance(symbol_payload, dict):
            errors.append(f"symbol_payload_invalid:{symbol}")
            continue
        raw_orders = symbol_payload.get("orders")
        if raw_orders is not None and not isinstance(raw_orders, list):
            errors.append(f"symbol_orders_invalid:{symbol}")
            continue
        for order in raw_orders or []:
            if not isinstance(order, dict) or order.get("broker_accepted") is not True:
                continue
            order_no = str(order.get("order_no") or "").strip()
            requested_qty = _widget_numeric(order.get("requested_qty"))
            filled_qty = _widget_numeric(order.get("filled_qty"))
            broker_execution_venue = (
                str(order.get("broker_execution_venue") or "").strip().upper()
            )
            if (
                not str(symbol).isdigit()
                or len(str(symbol)) != 6
                or not order_no
                or order.get("order_date") != target_date
                or requested_qty is None
                or not requested_qty.is_integer()
                or requested_qty <= 0
                or filled_qty is None
                or not filled_qty.is_integer()
                or filled_qty < 0
                or filled_qty > requested_qty
                or (
                    broker_execution_venue
                    and broker_execution_venue not in WIDGET_BROKER_EXECUTION_VENUES
                )
            ):
                errors.append(f"accepted_order_contract_invalid:{symbol}:{order_no}")
                continue
            key = (str(symbol), order_no)
            if key in index:
                errors.append(f"duplicate_accepted_order:{symbol}:{order_no}")
                continue
            index[key] = {
                **order,
                "symbol": str(symbol),
                "_state_entry_signal_id": str(
                    symbol_payload.get("entry_signal_id")
                    or symbol_payload.get("last_completed_entry_signal_id")
                    or ""
                ).strip(),
            }
    source.update(
        {
            "status": "contract_invalid" if errors else "loaded",
            "sha256": hashlib.sha256(state_bytes).hexdigest() if state_bytes else None,
            "order_count": len(index),
            "contract_errors": errors,
        }
    )
    return index, source


def _widget_advisory_event_index(*, target_date: str, report_root: Path) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[tuple[str, str, int], dict[str, Any]],
    dict[str, Any],
]:
    observation_dir = report_root / "widget_symbol_advisory_observation"
    paths = sorted(
        observation_dir.glob(
            f"widget_symbol_advisory_*_{target_date.replace('-', '')}.jsonl"
        )
    )
    entries: dict[str, dict[str, Any]] = {}
    exits: dict[str, dict[str, Any]] = {}
    episodes: dict[tuple[str, str, int], dict[str, Any]] = {}
    errors: list[str] = []
    row_count = 0
    source_hash = hashlib.sha256()
    for path in paths:
        try:
            raw_bytes = path.read_bytes()
            raw_lines = raw_bytes.decode("utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            errors.append(f"advisory_unreadable:{path}")
            continue
        source_hash.update(path.name.encode("utf-8"))
        source_hash.update(b"\0")
        source_hash.update(raw_bytes)
        for line_number, line in enumerate(raw_lines, start=1):
            if not line.strip():
                continue
            row_count += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"advisory_json_invalid:{path.name}:{line_number}")
                continue
            if not isinstance(payload, dict):
                errors.append(f"advisory_row_invalid:{path.name}:{line_number}")
                continue
            entry_event = payload.get("entry_event")
            exit_event = payload.get("exit_event")
            if entry_event is None and exit_event is None:
                continue
            observed_at = _owner_ts_on_target_date(
                payload.get("observed_at_kst"), target_date
            )
            symbol = str(payload.get("symbol") or "")
            advisory = payload.get("advisory")
            episode = payload.get("episode")
            session = (
                str(advisory.get("session") or "") if isinstance(advisory, dict) else ""
            )
            sequence = (
                int(episode.get("sequence"))
                if isinstance(episode, dict)
                and not isinstance(episode.get("sequence"), bool)
                and isinstance(episode.get("sequence"), int)
                else None
            )
            base_valid = bool(
                observed_at is not None
                and len(symbol) == 6
                and symbol.isdigit()
                and session in WIDGET_SESSION_VENUES
                and payload.get("actual_order_submitted") is False
                and payload.get("broker_order_forbidden") is True
                and isinstance(episode, dict)
                and sequence is not None
                and sequence > 0
                and episode.get("actual_order_submitted") is False
                and episode.get("broker_order_forbidden") is True
                and episode.get("runtime_effect") is False
            )
            if not base_valid:
                errors.append(
                    f"advisory_event_envelope_invalid:{path.name}:{line_number}"
                )
                continue
            episode_key = (symbol, session, sequence)
            episode_fact = episodes.setdefault(
                episode_key,
                {
                    "symbol": symbol,
                    "sequence": sequence,
                    "session": session,
                    "entry_event": None,
                    "exit_event": None,
                },
            )
            if episode_fact["session"] != session:
                errors.append(f"advisory_episode_session_conflict:{symbol}:{sequence}")
                continue
            for event_name, raw_event, index in (
                ("entry_event", entry_event, entries),
                ("exit_event", exit_event, exits),
            ):
                if raw_event is None:
                    continue
                event_at = _owner_ts_on_target_date(
                    (
                        raw_event.get("observed_at")
                        if isinstance(raw_event, dict)
                        else None
                    ),
                    target_date,
                )
                event_id = (
                    str(raw_event.get("event_id") or "").strip()
                    if isinstance(raw_event, dict)
                    else ""
                )
                expected_type = "ENTRY" if event_name == "entry_event" else "EXIT"
                event_id_parts = event_id.split(":")
                event_timestamp = event_id_parts[4] if len(event_id_parts) == 5 else ""
                event_timestamp_valid = bool(
                    event_timestamp.isdigit()
                    and (
                        len(event_timestamp) == 6
                        or (
                            len(event_timestamp) == 14
                            and event_timestamp.startswith(target_date.replace("-", ""))
                        )
                    )
                )
                event_id_valid = bool(
                    len(event_id_parts) == 5
                    and event_id_parts[0] == symbol
                    and event_id_parts[1] == target_date
                    and event_id_parts[2] == expected_type
                    and event_id_parts[3].isdigit()
                    and int(event_id_parts[3]) == sequence
                    and event_timestamp_valid
                )
                raw_episode_sequence = (
                    raw_event.get("episode_sequence")
                    if isinstance(raw_event, dict)
                    else None
                )
                event_valid = bool(
                    isinstance(raw_event, dict)
                    and event_id_valid
                    and (
                        raw_episode_sequence is None or raw_episode_sequence == sequence
                    )
                    and event_at is not None
                    and raw_event.get("event_type") == expected_type
                    and raw_event.get("source_quality_status") == "PASS"
                    and raw_event.get("actual_order_submitted") is False
                    and raw_event.get("broker_order_forbidden") is True
                    and raw_event.get("runtime_effect") is False
                    and (
                        expected_type != "ENTRY"
                        or (
                            raw_event.get("state") in ("ENTRY_CAUTION", "ENTRY_READY")
                            and all(
                                (_widget_numeric(raw_event.get(field)) or 0) > 0
                                for field in (
                                    "entry_price_high",
                                    "target_price",
                                    "structural_support",
                                )
                            )
                        )
                    )
                    and (
                        expected_type != "EXIT"
                        or (
                            str(raw_event.get("reason") or "").strip()
                            and (
                                _widget_numeric(raw_event.get("reference_exit_price"))
                                or 0
                            )
                            > 0
                        )
                    )
                )
                if not event_valid:
                    errors.append(
                        f"advisory_{event_name}_invalid:{path.name}:{line_number}"
                    )
                    continue
                normalized = {
                    **raw_event,
                    "symbol": symbol,
                    "session": session,
                    "episode_sequence": sequence,
                    "event_at": event_at,
                    "source_path": str(path),
                    "source_line_number": line_number,
                }
                prior = index.get(event_id)
                if prior is not None and any(
                    prior.get(key) != normalized.get(key)
                    for key in (
                        "symbol",
                        "session",
                        "episode_sequence",
                        "event_at",
                        "state",
                        "reason",
                        "reference_exit_price",
                    )
                ):
                    errors.append(f"advisory_event_identity_conflict:{event_id}")
                    continue
                episode_prior = episode_fact.get(event_name)
                if (
                    isinstance(episode_prior, dict)
                    and episode_prior.get("event_id") != event_id
                ):
                    errors.append(
                        "advisory_episode_event_conflict:"
                        f"{symbol}:{session}:{sequence}:{event_name}"
                    )
                    continue
                index[event_id] = normalized
                episode_fact[event_name] = normalized
    for (symbol, session, sequence), episode_fact in episodes.items():
        entry = episode_fact.get("entry_event")
        exit_event = episode_fact.get("exit_event")
        if (
            isinstance(entry, dict)
            and isinstance(exit_event, dict)
            and exit_event.get("event_at") < entry.get("event_at")
        ):
            errors.append(
                f"advisory_episode_event_time_regression:{symbol}:{session}:{sequence}"
            )
    source = {
        "paths": [str(path) for path in paths],
        "status": (
            "contract_invalid" if errors else "loaded" if paths else "not_observed"
        ),
        "optional_when_absent": True,
        "target_date": target_date,
        "sha256": source_hash.hexdigest() if paths else None,
        "row_count": row_count,
        "entry_event_count": len(entries),
        "exit_event_count": len(exits),
        "episode_count": len(episodes),
        "contract_errors": sorted(set(errors)),
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return entries, exits, episodes, source


def _widget_actual_execution_inventory(
    *,
    target_date: str,
    report_root: Path,
    state_path: Path,
    symbols: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    comparison_cost = (
        comparison_cost_contract(target_date)
        if date.fromisoformat(target_date) >= CLEAN_BASELINE_DATE
        else None
    )
    round_trip_cost_pct = (
        float(comparison_cost["round_trip_cost_pct"])
        if comparison_cost is not None
        else None
    )
    event_path = (
        report_root
        / "widget_signal_auto_trade_events"
        / f"widget_signal_auto_trade_events_{target_date.replace('-', '')}.jsonl"
    )
    state_orders, state_source = _widget_state_order_index(
        target_date=target_date, state_path=state_path
    )
    advisory_entries, advisory_exits, advisory_episodes, advisory_source = (
        _widget_advisory_event_index(
            target_date=target_date,
            report_root=report_root,
        )
    )
    source: dict[str, Any] = {
        "path": str(event_path),
        "status": "not_observed",
        "target_date": target_date,
        "optional_when_absent": True,
        "event_schema": WIDGET_AUTO_TRADE_EVENT_SCHEMA,
        "sha256": None,
        "row_count": 0,
        "actual_event_count": 0,
        "actual_lifecycle_count": 0,
        "contract_errors": [],
        "state_source": state_source,
        "advisory_source": advisory_source,
        "blocked_daily_entry_limit_opportunities": [],
        "timestamp_provenance": (
            "execution_loop_submit_record_and_broker_reconciliation_confirmation_time"
        ),
        "comparison_cost_contract": comparison_cost,
    }
    if not event_path.exists():
        if state_source.get("status") == "contract_invalid":
            source.update(
                {
                    "status": "state_contract_invalid",
                    "optional_when_absent": False,
                    "contract_errors": list(state_source.get("contract_errors") or []),
                }
            )
        elif int(state_source.get("order_count") or 0) > 0:
            source.update(
                {
                    "status": "event_journal_missing_with_accepted_state_orders",
                    "optional_when_absent": False,
                    "contract_errors": [
                        "accepted_state_orders_without_exact_date_event_journal"
                    ],
                }
            )
        return [], source
    try:
        event_bytes = event_path.read_bytes()
        raw_lines = event_bytes.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        source["status"] = "unreadable"
        source["optional_when_absent"] = False
        return [], source
    source["sha256"] = hashlib.sha256(event_bytes).hexdigest()
    source["row_count"] = len([line for line in raw_lines if line.strip()])
    submit_rows: dict[tuple[str, str], dict[str, Any]] = {}
    reconcile_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    contract_errors: list[str] = list(state_source.get("contract_errors") or [])
    actual_event_count = 0
    blocked_daily_entry_limit_opportunities: list[dict[str, Any]] = []
    relevant_types = (
        "order_submitted",
        "order_execution_reconciled",
        "take_profit_episode_completed",
    )
    for line_number, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            contract_errors.append(f"event_json_invalid:{line_number}")
            continue
        if not isinstance(event, dict):
            contract_errors.append(f"event_row_invalid:{line_number}")
            continue
        if event.get("event_type") == "entry_blocked_daily_entry_limit":
            observed_at = _owner_ts_on_target_date(
                event.get("observed_at"), target_date
            )
            symbol = str(event.get("symbol") or "")
            signal_id = str(event.get("signal_id") or "").strip()
            advisory_entry = advisory_entries.get(signal_id)
            episode_fact = (
                advisory_episodes.get(
                    (
                        symbol,
                        str(advisory_entry["session"]),
                        int(advisory_entry["episode_sequence"]),
                    )
                )
                if advisory_entry is not None
                else None
            )
            blocked_valid = bool(
                event.get("schema") in (None, WIDGET_AUTO_TRADE_EVENT_SCHEMA)
                and event.get("trade_date") == target_date
                and observed_at is not None
                and len(symbol) == 6
                and symbol.isdigit()
                and signal_id
                and event.get("execution_authority")
                == WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY
                and event.get("decision_authority")
                == WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY
                and event.get("runtime_effect") is True
                and event.get("actual_order_submitted") is False
                and event.get("broker_order_forbidden") is False
                and advisory_entry is not None
                and advisory_entry.get("symbol") == symbol
            )
            if not blocked_valid:
                contract_errors.append(
                    f"blocked_daily_entry_limit_contract_invalid:{line_number}"
                )
                continue
            advisory_exit = (
                episode_fact.get("exit_event")
                if isinstance(episode_fact, dict)
                else None
            )
            blocked_daily_entry_limit_opportunities.append(
                {
                    "symbol": symbol,
                    "signal_id": signal_id,
                    "observed_at": observed_at.isoformat(),
                    "session": advisory_entry["session"],
                    "entry_state": advisory_entry.get("state"),
                    "entry_price": _widget_numeric(
                        advisory_entry.get("entry_price_high")
                    ),
                    "target_price": _widget_numeric(advisory_entry.get("target_price")),
                    "structural_support": _widget_numeric(
                        advisory_entry.get("structural_support")
                    ),
                    "episode_sequence": advisory_entry["episode_sequence"],
                    "source_only_exit_event_id": (
                        advisory_exit.get("event_id")
                        if isinstance(advisory_exit, dict)
                        else None
                    ),
                    "source_only_exit_reason": (
                        advisory_exit.get("reason")
                        if isinstance(advisory_exit, dict)
                        else None
                    ),
                    "source_only_exit_price": (
                        _widget_numeric(advisory_exit.get("reference_exit_price"))
                        if isinstance(advisory_exit, dict)
                        else None
                    ),
                    "source_only_exit_at": (
                        advisory_exit["event_at"].isoformat()
                        if isinstance(advisory_exit, dict)
                        else None
                    ),
                    "actual_order_submitted": False,
                    "broker_fill_observed": False,
                    "counterfactual_only": True,
                }
            )
            continue
        if event.get("event_type") not in relevant_types:
            continue
        actual_event_count += 1
        observed_at = _owner_ts_on_target_date(event.get("observed_at"), target_date)
        symbol = str(event.get("symbol") or "")
        schema = event.get("schema")
        base_valid = bool(
            schema in (None, WIDGET_AUTO_TRADE_EVENT_SCHEMA)
            and event.get("trade_date") == target_date
            and observed_at is not None
            and len(symbol) == 6
            and symbol.isdigit()
            and event.get("execution_authority")
            == WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY
            and event.get("decision_authority") == WIDGET_AUTO_TRADE_EXECUTION_AUTHORITY
            and event.get("runtime_effect") is True
            and event.get("actual_order_submitted") is True
            and event.get("broker_order_forbidden") is False
        )
        if not base_valid:
            contract_errors.append(f"event_envelope_invalid:{line_number}")
            continue
        if event["event_type"] == "take_profit_episode_completed":
            continue
        order_no = str(event.get("order_no") or "").strip()
        role = str(event.get("order_role") or "").strip()
        side = str(event.get("side") or "").strip().upper()
        if (
            not order_no
            or role
            not in {
                "ENTRY_BUY",
                "SCALE_IN_BUY",
                "TAKE_PROFIT_SELL",
                "FINAL_EXIT_SELL",
                WIDGET_MANUAL_PARTIAL_EXIT_ROLE,
            }
            or side != ("BUY" if role in {"ENTRY_BUY", "SCALE_IN_BUY"} else "SELL")
        ):
            contract_errors.append(f"event_order_identity_invalid:{line_number}")
            continue
        key = (symbol, order_no)
        normalized_event = {**event, "_observed_at": observed_at}
        if event["event_type"] == "order_submitted":
            requested_qty = _widget_numeric(event.get("requested_qty"))
            if (
                requested_qty is None
                or not requested_qty.is_integer()
                or requested_qty <= 0
                or key in submit_rows
            ):
                contract_errors.append(f"submit_contract_invalid:{line_number}")
                continue
            submit_rows[key] = normalized_event
        else:
            requested_qty = _widget_numeric(event.get("requested_qty"))
            filled_qty = _widget_numeric(event.get("filled_qty"))
            remaining_qty = _widget_numeric(event.get("remaining_qty"))
            broker_execution_venue = (
                str(event.get("broker_execution_venue") or "").strip().upper()
            )
            if (
                requested_qty is None
                or not requested_qty.is_integer()
                or requested_qty <= 0
                or filled_qty is None
                or not filled_qty.is_integer()
                or filled_qty < 0
                or filled_qty > requested_qty
                or remaining_qty is None
                or not remaining_qty.is_integer()
                or remaining_qty < 0
                or remaining_qty > requested_qty
                or filled_qty + remaining_qty > requested_qty
                or (
                    broker_execution_venue
                    and broker_execution_venue not in WIDGET_BROKER_EXECUTION_VENUES
                )
            ):
                contract_errors.append(f"reconcile_contract_invalid:{line_number}")
                continue
            reconcile_rows[key].append(normalized_event)
    for symbol, order_no in sorted(set(reconcile_rows) - set(submit_rows)):
        contract_errors.append(f"reconcile_without_submit:{symbol}:{order_no}")
    for symbol, order_no in sorted(set(state_orders) - set(submit_rows)):
        contract_errors.append(
            f"accepted_state_order_without_submit:{symbol}:{order_no}"
        )
    for symbol, order_no in sorted(set(submit_rows) - set(state_orders)):
        contract_errors.append(
            f"accepted_submit_without_exact_date_state:{symbol}:{order_no}"
        )
    for key, rows in reconcile_rows.items():
        submit = submit_rows.get(key)
        if submit is None:
            continue
        submit_requested = int(_widget_numeric(submit.get("requested_qty")) or 0)
        prior_filled = -1
        prior_remaining = submit_requested
        prior_execution_venue = ""
        for row in sorted(rows, key=lambda value: value["_observed_at"]):
            filled = int(_widget_numeric(row.get("filled_qty")) or 0)
            remaining = int(_widget_numeric(row.get("remaining_qty")) or 0)
            row_requested = int(_widget_numeric(row.get("requested_qty")) or 0)
            execution_venue = (
                str(row.get("broker_execution_venue") or "").strip().upper()
            )
            if (
                row_requested != submit_requested
                or row.get("order_role") != submit.get("order_role")
                or row.get("side") != submit.get("side")
                or filled < prior_filled
                or remaining > prior_remaining
                or (
                    execution_venue
                    and prior_execution_venue
                    and execution_venue != prior_execution_venue
                )
            ):
                contract_errors.append(
                    f"reconciliation_sequence_invalid:{key[0]}:{key[1]}"
                )
                break
            prior_filled = filled
            prior_remaining = remaining
            prior_execution_venue = execution_venue or prior_execution_venue
    for key in sorted(set(state_orders) & set(submit_rows)):
        state_order = state_orders[key]
        submit = submit_rows[key]
        state_requested = int(_widget_numeric(state_order.get("requested_qty")) or 0)
        submit_requested = int(_widget_numeric(submit.get("requested_qty")) or 0)
        if (
            state_requested != submit_requested
            or state_order.get("order_role") != submit.get("order_role")
            or state_order.get("side") != submit.get("side")
            or (
                state_order.get("signal_id")
                and state_order.get("signal_id") != submit.get("signal_id")
            )
            or (
                state_order.get("market_venue")
                and state_order.get("market_venue") != submit.get("market_venue")
            )
        ):
            contract_errors.append(f"state_event_order_mismatch:{key[0]}:{key[1]}")
            continue
        if submit.get("order_role") == WIDGET_MANUAL_PARTIAL_EXIT_ROLE:
            receipt = state_order.get("manual_exit_receipt")
            if (
                state_order.get("operator_authority")
                != WIDGET_MANUAL_PARTIAL_EXIT_AUTHORITY
                or state_order.get("exit_execution_class") != "manual_operator_exit"
                or state_order.get("manual_exit_realized") is not True
                or not isinstance(receipt, dict)
                or str(receipt.get("order_no") or "").strip() != key[1]
                or str(receipt.get("symbol") or "").strip() != key[0]
                or str(receipt.get("owner_id") or "").strip() != "widget_auto_trade"
                or str(receipt.get("order_date") or "").strip() != target_date
                or str(receipt.get("source_api") or "").strip() != "kt00007"
                or receipt.get("allocation_authority")
                != WIDGET_MANUAL_PARTIAL_EXIT_AUTHORITY
                or int(_widget_numeric(receipt.get("filled_qty")) or 0)
                != int(_widget_numeric(state_order.get("filled_qty")) or 0)
                or _widget_numeric(receipt.get("fill_price"))
                != _widget_numeric(state_order.get("fill_price"))
                or int(
                    _widget_numeric(
                        state_order.get("manual_partial_exit_requested_qty")
                    )
                    or 0
                )
                != int(_widget_numeric(state_order.get("requested_qty")) or 0)
            ):
                contract_errors.append(
                    f"manual_partial_exit_state_contract_invalid:{key[0]}:{key[1]}"
                )
                continue
        state_execution_venue = (
            str(state_order.get("broker_execution_venue") or "").strip().upper()
        )
        event_execution_venues = {
            str(row.get("broker_execution_venue") or "").strip().upper()
            for row in reconcile_rows.get(key) or []
            if str(row.get("broker_execution_venue") or "").strip()
        }
        if len(event_execution_venues) > 1 or (
            state_execution_venue
            and event_execution_venues
            and event_execution_venues != {state_execution_venue}
        ):
            contract_errors.append(
                f"state_event_execution_venue_mismatch:{key[0]}:{key[1]}"
            )
    source["actual_event_count"] = actual_event_count
    if contract_errors:
        source.update(
            {
                "status": "contract_invalid",
                "optional_when_absent": False,
                "contract_errors": sorted(set(contract_errors)),
            }
        )
        return [], source

    lifecycle_orders: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    instrumentation_gaps: list[str] = []
    for key, submit in submit_rows.items():
        state_order = state_orders.get(key) or {}
        rows = sorted(
            reconcile_rows.get(key) or [], key=lambda row: row["_observed_at"]
        )
        execution_venues = {
            str(value).strip().upper()
            for value in (
                state_order.get("broker_execution_venue"),
                *(row.get("broker_execution_venue") for row in rows),
            )
            if str(value or "").strip()
        }
        broker_execution_venue = (
            next(iter(execution_venues)) if len(execution_venues) == 1 else None
        )
        positive_rows = [
            row for row in rows if (_widget_numeric(row.get("filled_qty")) or 0.0) > 0
        ]
        requested_qty = int(_widget_numeric(submit.get("requested_qty")) or 0)
        event_filled_qty = max(
            (int(_widget_numeric(row.get("filled_qty")) or 0) for row in rows),
            default=0,
        )
        state_filled_qty = int(_widget_numeric(state_order.get("filled_qty")) or 0)
        filled_qty = max(event_filled_qty, state_filled_qty)
        fill_price = next(
            (
                value
                for row in reversed(positive_rows)
                if (value := _widget_numeric(row.get("fill_price"))) is not None
                and value > 0
                and int(_widget_numeric(row.get("filled_qty")) or 0) == filled_qty
            ),
            None,
        )
        if fill_price is None and state_filled_qty == filled_qty:
            fill_price = _widget_numeric(state_order.get("fill_price"))
        first_fill_price = (
            _widget_numeric(positive_rows[0].get("fill_price"))
            if positive_rows
            else None
        )
        first_fill_at = positive_rows[0]["_observed_at"] if positive_rows else None
        latest_fill_at = next(
            (
                row["_observed_at"]
                for row in reversed(positive_rows)
                if int(_widget_numeric(row.get("filled_qty")) or 0) == filled_qty
            ),
            None,
        )
        full_fill_at = next(
            (
                row["_observed_at"]
                for row in positive_rows
                if int(_widget_numeric(row.get("filled_qty")) or 0) == requested_qty
                and int(_widget_numeric(row.get("remaining_qty")) or 0) == 0
            ),
            None,
        )
        if first_fill_at is None and filled_qty > 0:
            first_fill_at = _owner_ts_on_target_date(
                state_order.get("last_reconciled_at"), target_date
            )
        state_reconciled_at = _owner_ts_on_target_date(
            state_order.get("last_reconciled_at"), target_date
        )
        if state_filled_qty == filled_qty and state_reconciled_at is not None:
            latest_fill_at = max(
                (value for value in (latest_fill_at, state_reconciled_at) if value),
                default=None,
            )
        if (
            full_fill_at is None
            and filled_qty == requested_qty
            and state_order.get("status") == "FILLED"
        ):
            full_fill_at = _owner_ts_on_target_date(
                state_order.get("last_reconciled_at"), target_date
            )
        fill_at = full_fill_at or latest_fill_at or first_fill_at
        parent_signal_id = str(
            submit.get("parent_entry_signal_id")
            or state_order.get("parent_entry_signal_id")
            or ""
        ).strip()
        signal_id = str(submit.get("signal_id") or state_order.get("signal_id") or "")
        role = str(submit.get("order_role") or "")
        if role == "ENTRY_BUY":
            lifecycle_signal_id = signal_id
        elif role == "SCALE_IN_BUY":
            lifecycle_signal_id = parent_signal_id or str(
                state_order.get("_state_entry_signal_id") or ""
            )
        elif role == "TAKE_PROFIT_SELL":
            lifecycle_signal_id = (
                parent_signal_id
                or (signal_id.rsplit(":TP:", 1)[0] if ":TP:" in signal_id else "")
                or str(state_order.get("_state_entry_signal_id") or "")
            )
        else:
            lifecycle_signal_id = parent_signal_id or str(
                state_order.get("_state_entry_signal_id") or ""
            )
        venue = str(
            submit.get("market_venue") or state_order.get("market_venue") or ""
        ).upper()
        if (
            not lifecycle_signal_id
            or venue not in {"KRX", "NXT"}
            or filled_qty > requested_qty
            or (
                filled_qty > 0
                and (fill_price is None or fill_price <= 0 or fill_at is None)
            )
        ):
            instrumentation_gaps.append(f"order_lifecycle_incomplete:{key[0]}:{key[1]}")
            continue
        fact = {
            **state_order,
            **submit,
            "filled_qty": filled_qty,
            "fill_price": fill_price,
            "first_fill_price": first_fill_price,
            "fill_at": fill_at,
            "first_fill_at": first_fill_at,
            "full_fill_at": full_fill_at,
            "lifecycle_signal_id": lifecycle_signal_id,
            "market_venue": venue,
            "broker_execution_venue": broker_execution_venue,
        }
        lifecycle_orders[(key[0], lifecycle_signal_id)].append(fact)

    anchors: list[dict[str, Any]] = []
    for (symbol, signal_id), orders in sorted(lifecycle_orders.items()):
        signal_contract = _widget_entry_signal_contract(
            signal_id, symbol=symbol, target_date=target_date
        )
        advisory_entry = advisory_entries.get(signal_id)
        if (
            signal_contract is None
            and advisory_entry is not None
            and advisory_entry.get("symbol") == symbol
        ):
            signal_contract = (
                str(advisory_entry["session"]),
                advisory_entry["event_at"],
            )
        initial_orders = [
            order for order in orders if order.get("order_role") == "ENTRY_BUY"
        ]
        if signal_contract is None or len(initial_orders) != 1:
            instrumentation_gaps.append(
                f"entry_signal_contract_invalid:{symbol}:{signal_id}"
            )
            continue
        session, signal_at = signal_contract
        buy_submit_orders = [
            order
            for order in orders
            if order.get("order_role") in {"ENTRY_BUY", "SCALE_IN_BUY"}
        ]
        buy_fill_orders = [
            order
            for order in buy_submit_orders
            if order.get("order_role") in {"ENTRY_BUY", "SCALE_IN_BUY"}
            and int(order.get("filled_qty") or 0) > 0
        ]
        sell_orders = [
            order
            for order in orders
            if order.get("order_role")
            in {
                "TAKE_PROFIT_SELL",
                "FINAL_EXIT_SELL",
                WIDGET_MANUAL_PARTIAL_EXIT_ROLE,
            }
            and int(order.get("filled_qty") or 0) > 0
        ]
        sell_submit_orders = [
            order
            for order in orders
            if order.get("order_role")
            in {
                "TAKE_PROFIT_SELL",
                "FINAL_EXIT_SELL",
                WIDGET_MANUAL_PARTIAL_EXIT_ROLE,
            }
        ]
        manual_sell_orders = [
            order
            for order in sell_orders
            if order.get("order_role") == WIDGET_MANUAL_PARTIAL_EXIT_ROLE
        ]
        venue = str(initial_orders[0].get("market_venue") or "")
        scope_id = f"actual:{symbol}:{session}"
        row = symbols.setdefault(
            symbol,
            {
                "symbol": symbol,
                "name": initial_orders[0].get("name"),
                "scopes": [],
                "owner_scope_ids": [],
                "owner_scope_kinds": {},
                "owner_scope_expected_venues": {},
                "owner_anchor_contract_gaps": [],
                "expected_venues": [],
                "owner_inventory_source": "exact_date_widget_execution_event_journal",
            },
        )
        for key, default in (
            ("scopes", []),
            ("owner_scope_ids", []),
            ("owner_scope_kinds", {}),
            ("owner_scope_expected_venues", {}),
            ("owner_anchor_contract_gaps", []),
            ("expected_venues", []),
        ):
            row.setdefault(key, default.copy())
        if "active_widget_actual_execution" not in row["scopes"]:
            row["scopes"].append("active_widget_actual_execution")
        if scope_id not in row["owner_scope_ids"]:
            row["owner_scope_ids"].append(scope_id)
        row["owner_scope_kinds"][scope_id] = "active_widget_actual_execution"
        row["owner_scope_expected_venues"][scope_id] = [venue]
        if venue not in row["expected_venues"]:
            row["expected_venues"].append(venue)
        buy_qty = sum(int(order["filled_qty"]) for order in buy_fill_orders)
        sell_qty = sum(int(order["filled_qty"]) for order in sell_orders)
        buy_notional = sum(
            int(order["filled_qty"]) * float(order["fill_price"])
            for order in buy_fill_orders
        )
        sell_notional = sum(
            int(order["filled_qty"]) * float(order["fill_price"])
            for order in sell_orders
        )
        first_fill_at = min(
            (order["first_fill_at"] for order in buy_fill_orders), default=None
        )
        exit_at = max((order["fill_at"] for order in sell_orders), default=None)
        first_entry_submit_at = min(
            order["_observed_at"] for order in buy_submit_orders
        )
        first_exit_submit_at = min(
            (order["_observed_at"] for order in sell_submit_orders), default=None
        )
        order_venues = {str(order.get("market_venue") or "") for order in orders}
        initial_submit_price = _widget_numeric(initial_orders[0].get("limit_price"))
        initial_fill_price = _widget_numeric(initial_orders[0].get("fill_price"))
        anchor_entry_price = initial_fill_price or initial_submit_price
        buy_submit_prices = {
            str(order["order_no"]): _widget_numeric(order.get("fill_price"))
            or _widget_numeric(order.get("limit_price"))
            for order in buy_submit_orders
        }
        sell_submit_prices = {
            str(order["order_no"]): _widget_numeric(order.get("limit_price"))
            or _widget_numeric(order.get("fill_price"))
            for order in sell_submit_orders
        }
        entry_execution_venues = sorted(
            {
                str(order.get("broker_execution_venue") or "")
                for order in buy_fill_orders
                if order.get("broker_execution_venue")
            }
        )
        exit_execution_venues = sorted(
            {
                str(order.get("broker_execution_venue") or "")
                for order in sell_orders
                if order.get("broker_execution_venue")
            }
        )
        all_execution_venues = set(entry_execution_venues) | set(exit_execution_venues)
        execution_venue_alignment_state = (
            "unknown"
            if not all_execution_venues
            else "aligned" if all_execution_venues == {venue} else "cross_venue"
        )
        timestamp_order_valid = bool(
            signal_at <= first_entry_submit_at
            and all(
                order["_observed_at"] <= order["first_fill_at"]
                for order in buy_fill_orders
            )
            and all(order["_observed_at"] <= order["fill_at"] for order in sell_orders)
            and (first_fill_at is None or first_entry_submit_at <= first_fill_at)
            and (
                first_exit_submit_at is None
                or (first_fill_at is not None and first_exit_submit_at >= first_fill_at)
            )
            and (
                exit_at is None
                or (first_fill_at is not None and exit_at >= first_fill_at)
            )
        )
        buy_market_venues = {
            str(order.get("market_venue") or "") for order in buy_submit_orders
        }
        if (
            sell_qty > buy_qty
            or not timestamp_order_valid
            or buy_market_venues != {venue}
            or not order_venues.issubset({"KRX", "NXT"})
            or WIDGET_SESSION_VENUES.get(session) != venue
            or anchor_entry_price is None
            or anchor_entry_price <= 0
            or any(price is None or price <= 0 for price in buy_submit_prices.values())
            or any(price is None or price <= 0 for price in sell_submit_prices.values())
        ):
            row["owner_anchor_contract_gaps"].append(
                {"scope_id": scope_id, "reason": "actual_widget_fill_order_invalid"}
            )
            continue
        manual_sell_qty = sum(int(order["filled_qty"]) for order in manual_sell_orders)
        partial_manual_realization = bool(
            0 < manual_sell_qty <= sell_qty < buy_qty and exit_at is not None
        )
        realized = bool(
            (sell_qty == buy_qty and buy_qty > 0 and exit_at is not None)
            or partial_manual_realization
        )
        realized_qty = sell_qty if partial_manual_realization else buy_qty
        average_entry_price = buy_notional / buy_qty if buy_qty > 0 else None
        realized_entry_notional = (
            average_entry_price * realized_qty
            if realized and average_entry_price is not None
            else buy_notional
        )
        gross_return_pct = (
            (sell_notional / realized_entry_notional - 1.0) * 100.0
            if realized and realized_entry_notional > 0
            else None
        )
        execution_economics = (
            modeled_execution_economics(
                buy_notional_krw=realized_entry_notional,
                sell_notional_krw=sell_notional,
                trade_date=target_date,
            )
            if realized and comparison_cost is not None
            else None
        )
        target_prices = [
            value
            for order in sell_submit_orders
            if order.get("order_role") == "TAKE_PROFIT_SELL"
            and (value := _widget_numeric(order.get("limit_price"))) is not None
            and value > 0
        ]
        final_exit_events = [
            event
            for order in sell_orders
            if order.get("order_role") == "FINAL_EXIT_SELL"
            and (event := advisory_exits.get(str(order.get("signal_id") or "")))
            is not None
            and event.get("symbol") == symbol
        ]
        resolved_final_exit_reasons = {
            str(event.get("reason") or "")
            for event in final_exit_events
            if isinstance(event, dict) and event.get("reason")
        }
        source_final_exit_reason = (
            next(iter(resolved_final_exit_reasons))
            if len(resolved_final_exit_reasons) == 1
            else None
        )
        if not realized:
            exit_execution_class = "not_realized"
        elif manual_sell_qty == sell_qty:
            exit_execution_class = "manual_operator_exit"
        elif manual_sell_qty > 0:
            exit_execution_class = "mixed_manual_and_machine_exit"
        elif all(
            order.get("order_role") == "TAKE_PROFIT_SELL" for order in sell_orders
        ):
            exit_execution_class = "machine_target_fill"
        elif all(order.get("order_role") == "FINAL_EXIT_SELL" for order in sell_orders):
            exit_execution_class = "machine_final_exit"
        else:
            exit_execution_class = "realized_exit_source_unknown"
        owner_outcome = {
            "exit_at": exit_at.isoformat() if exit_at else None,
            "exit_price": sell_notional / sell_qty if sell_qty else None,
            "exit_reason": (
                "manual_operator_partial_exit"
                if partial_manual_realization
                else (
                    "take_profit_fill"
                    if realized and exit_execution_class == "machine_target_fill"
                    else (
                        source_final_exit_reason
                        if realized and source_final_exit_reason
                        else "final_exit_fill" if realized else "right_censored"
                    )
                )
            ),
            "source_final_exit_event_ids": [
                event["event_id"]
                for event in final_exit_events
                if isinstance(event, dict)
            ],
            "holding_duration_ms": (
                round((exit_at - first_fill_at).total_seconds() * 1000.0)
                if realized and exit_at is not None and first_fill_at is not None
                else None
            ),
            "signal_to_entry_submit_record_ms": round(
                (first_entry_submit_at - signal_at).total_seconds() * 1000.0
            ),
            "entry_submit_record_to_first_fill_confirmation_ms": (
                round((first_fill_at - first_entry_submit_at).total_seconds() * 1000.0)
                if first_fill_at is not None
                else None
            ),
            "first_fill_confirmation_to_first_exit_submit_record_ms": (
                round((first_exit_submit_at - first_fill_at).total_seconds() * 1000.0)
                if first_exit_submit_at is not None and first_fill_at is not None
                else None
            ),
            "first_exit_submit_record_to_final_exit_fill_confirmation_ms": (
                round((exit_at - first_exit_submit_at).total_seconds() * 1000.0)
                if exit_at is not None and first_exit_submit_at is not None
                else None
            ),
            "gross_no_slippage_return_pct": (
                round(gross_return_pct, 8) if gross_return_pct is not None else None
            ),
            "cost_aware_net_return_pct": (
                execution_economics["modeled_net_return_pct"]
                if execution_economics is not None
                else None
            ),
            "modeled_total_cost_krw": (
                execution_economics["modeled_total_cost_krw"]
                if execution_economics is not None
                else None
            ),
            "modeled_net_profit_krw": (
                execution_economics["modeled_net_profit_krw"]
                if execution_economics is not None
                else None
            ),
            "modeled_costs_broker_receipt_exact": False,
            "cost_contract_sha256": (
                comparison_cost["contract_sha256"]
                if comparison_cost is not None
                else None
            ),
            "entry_notional_krw": round(realized_entry_notional, 3),
            "quantity": realized_qty,
            "purchased_quantity": buy_qty,
            "manual_exit_filled_quantity": manual_sell_qty,
            "right_censored_residual_quantity": max(0, buy_qty - sell_qty),
            "realization_scope": (
                "partial_manual_exit_cashflow"
                if partial_manual_realization
                else "full_widget_episode" if realized else "right_censored"
            ),
            "buy_leg_count": len(buy_submit_orders),
            "scale_in_buy_leg_count": sum(
                order.get("order_role") == "SCALE_IN_BUY" for order in buy_submit_orders
            ),
            "quantity_basis": "actual_widget_filled_quantity",
            "entry_fill_status": "filled" if buy_qty > 0 else "unfilled",
            "entry_execution_venues": entry_execution_venues,
            "exit_execution_venues": exit_execution_venues,
            "execution_venue_alignment_state": execution_venue_alignment_state,
            "realized": realized,
            "leg_id": (
                "widget_partial_manual_exit_cashflow"
                if partial_manual_realization
                else "widget_episode"
            ),
            "exit_execution_class": exit_execution_class,
            "manual_exit_realized": bool(realized and manual_sell_qty > 0),
            "autonomous_target_filled": bool(
                realized and exit_execution_class == "machine_target_fill"
            ),
            "realized_loss": bool(
                realized
                and execution_economics is not None
                and execution_economics["modeled_net_profit_krw"] < 0
            ),
            "timestamp_provenance": (
                "execution_loop_submit_record_and_broker_reconciliation_confirmation_time"
            ),
        }
        policy_tuning_eligible = bool(
            buy_qty > 0
            and buy_notional > 0
            and len(buy_submit_orders) == 1
            and initial_orders[0].get("full_fill_at") is not None
            and round_trip_cost_pct is not None
            and round_trip_cost_pct >= 0
            and advisory_source.get("status") != "contract_invalid"
            and execution_venue_alignment_state != "cross_venue"
        )
        owner_cost_contract = {
            "owner_round_trip_cost_pct": round_trip_cost_pct,
            "owner_round_trip_cost_provenance": (
                "widget_comparison_cost.effective_dated_contract"
            ),
            "owner_round_trip_cost_contract_sha256": (
                comparison_cost["contract_sha256"]
                if comparison_cost is not None
                else None
            ),
        }
        lifecycle_id = f"widget_actual:{symbol}:{signal_id}"
        anchors.append(
            {
                "anchor_id": f"{lifecycle_id}:signal",
                "lifecycle_id": lifecycle_id,
                "owner": "widget",
                "scope_id": scope_id,
                "symbol": symbol,
                "session": session,
                "expected_venues": [venue],
                "expected_session_buckets": [session],
                "anchor_at": signal_at.isoformat(),
                "anchor_price": anchor_entry_price,
                "anchor_price_provenance": (
                    "actual_initial_entry_fill_price"
                    if initial_fill_price is not None
                    else "accepted_entry_limit_price_unfilled"
                ),
                "owner_requested_quantity": int(
                    _widget_numeric(initial_orders[0].get("requested_qty")) or 0
                ),
                "owner_target_price": target_prices[-1] if target_prices else None,
                "lifecycle_stage": "entry",
                "anchor_role": "actual_widget_entry_signal",
                "entry_state": (
                    advisory_entry.get("state") if advisory_entry else None
                ),
                "structural_support": (
                    _widget_numeric(advisory_entry.get("structural_support"))
                    if advisory_entry
                    else None
                ),
                "source_entry_event_id": (
                    advisory_entry.get("event_id") if advisory_entry else None
                ),
                **owner_cost_contract,
                "owner_outcome": owner_outcome,
                "owner_lifecycle_contract_valid": True,
                "owner_policy_tuning_eligible": policy_tuning_eligible,
                "actual_order_submitted": True,
            }
        )
        for order in buy_submit_orders:
            submit_anchor_price = buy_submit_prices[str(order["order_no"])]
            assert submit_anchor_price is not None
            anchors.append(
                {
                    "anchor_id": f"{lifecycle_id}:buy_submit:{order['order_no']}",
                    "lifecycle_id": lifecycle_id,
                    "owner": "widget",
                    "scope_id": scope_id,
                    "symbol": symbol,
                    "session": session,
                    "expected_venues": [venue],
                    "expected_session_buckets": [session],
                    "anchor_at": order["_observed_at"].isoformat(),
                    "anchor_price": submit_anchor_price,
                    "anchor_price_provenance": (
                        "eventual_actual_fill_price"
                        if order.get("fill_price") is not None
                        else "accepted_entry_limit_price_unfilled"
                    ),
                    "owner_requested_quantity": int(
                        _widget_numeric(order.get("requested_qty")) or 0
                    ),
                    "owner_target_price": target_prices[-1] if target_prices else None,
                    "lifecycle_stage": "entry_submit",
                    "anchor_role": (
                        "actual_widget_scale_in_signal"
                        if order.get("order_role") == "SCALE_IN_BUY"
                        else "actual_widget_entry_submit_accept_recorded"
                    ),
                    "execution_order_role": order.get("order_role"),
                    "actual_realized_response_eligible": (
                        order.get("order_role") != "SCALE_IN_BUY"
                    ),
                    "execution_order_no": order.get("order_no"),
                    "eventual_broker_execution_venue": order.get(
                        "broker_execution_venue"
                    ),
                    **owner_cost_contract,
                    "owner_outcome": owner_outcome,
                    "owner_lifecycle_contract_valid": True,
                    "owner_policy_tuning_eligible": policy_tuning_eligible,
                    "actual_order_submitted": True,
                }
            )
        for order in buy_fill_orders:
            full_fill = order.get("full_fill_at") is not None
            if (
                full_fill
                and order.get("first_fill_price") is not None
                and order["first_fill_at"] < order["full_fill_at"]
            ):
                anchors.append(
                    {
                        "anchor_id": (
                            f"{lifecycle_id}:buy_partial_fill:{order['order_no']}"
                        ),
                        "lifecycle_id": lifecycle_id,
                        "owner": "widget",
                        "scope_id": scope_id,
                        "symbol": symbol,
                        "session": session,
                        "expected_venues": [
                            str(order.get("broker_execution_venue") or venue)
                        ],
                        "expected_session_buckets": [session],
                        "anchor_at": order["first_fill_at"].isoformat(),
                        "anchor_price": float(order["first_fill_price"]),
                        "anchor_price_provenance": ("first_reconciliation_fill_price"),
                        "owner_target_price": (
                            target_prices[-1] if target_prices else None
                        ),
                        "lifecycle_stage": "entry_partial_fill",
                        "anchor_role": "actual_widget_entry_partial_fill_reconciled",
                        "execution_order_role": order.get("order_role"),
                        "execution_order_no": order.get("order_no"),
                        "broker_execution_venue": order.get("broker_execution_venue"),
                        **owner_cost_contract,
                        "owner_outcome": owner_outcome,
                        "owner_lifecycle_contract_valid": True,
                        "owner_policy_tuning_eligible": policy_tuning_eligible,
                        "actual_order_submitted": True,
                    }
                )
            anchors.append(
                {
                    "anchor_id": f"{lifecycle_id}:buy_fill:{order['order_no']}",
                    "lifecycle_id": lifecycle_id,
                    "owner": "widget",
                    "scope_id": scope_id,
                    "symbol": symbol,
                    "session": session,
                    "expected_venues": [
                        str(order.get("broker_execution_venue") or venue)
                    ],
                    "expected_session_buckets": [session],
                    "anchor_at": order["fill_at"].isoformat(),
                    "anchor_price": float(order["fill_price"]),
                    "anchor_price_provenance": "latest_cumulative_fill_price",
                    "owner_target_price": target_prices[-1] if target_prices else None,
                    "lifecycle_stage": "entry" if full_fill else "entry_partial_fill",
                    "anchor_role": (
                        "actual_widget_entry_fill_reconciled"
                        if full_fill
                        else "actual_widget_entry_partial_fill_reconciled"
                    ),
                    "execution_order_role": order.get("order_role"),
                    "execution_order_no": order.get("order_no"),
                    "broker_execution_venue": order.get("broker_execution_venue"),
                    **owner_cost_contract,
                    "owner_outcome": owner_outcome,
                    "owner_lifecycle_contract_valid": True,
                    "owner_policy_tuning_eligible": policy_tuning_eligible,
                    "actual_order_submitted": True,
                }
            )
        for order in sell_submit_orders:
            submit_price = sell_submit_prices[str(order["order_no"])]
            assert submit_price is not None
            anchors.append(
                {
                    "anchor_id": f"{lifecycle_id}:sell_submit:{order['order_no']}",
                    "lifecycle_id": lifecycle_id,
                    "owner": "widget",
                    "scope_id": scope_id,
                    "symbol": symbol,
                    "session": session,
                    "expected_venues": [venue],
                    "expected_session_buckets": [session],
                    "anchor_at": order["_observed_at"].isoformat(),
                    "anchor_price": submit_price,
                    "anchor_price_provenance": (
                        "accepted_limit_price_or_eventual_actual_fill_price"
                    ),
                    "owner_target_price": None,
                    "lifecycle_stage": "exit_submit",
                    "anchor_role": "actual_widget_exit_submit_accept_recorded",
                    "execution_order_role": order.get("order_role"),
                    "execution_order_no": order.get("order_no"),
                    "eventual_broker_execution_venue": order.get(
                        "broker_execution_venue"
                    ),
                    **owner_cost_contract,
                    "owner_outcome": owner_outcome,
                    "owner_lifecycle_contract_valid": True,
                    "owner_policy_tuning_eligible": policy_tuning_eligible,
                    "actual_order_submitted": True,
                }
            )
        if realized:
            for order in sell_orders:
                partial_fill_at = order.get("first_fill_at")
                partial_fill_price = order.get("first_fill_price")
                full_fill_at = order.get("full_fill_at")
                if (
                    partial_fill_at is None
                    or partial_fill_price is None
                    or (full_fill_at is not None and partial_fill_at >= full_fill_at)
                ):
                    continue
                anchors.append(
                    {
                        "anchor_id": (
                            f"{lifecycle_id}:sell_partial_fill:{order['order_no']}"
                        ),
                        "lifecycle_id": lifecycle_id,
                        "owner": "widget",
                        "scope_id": scope_id,
                        "symbol": symbol,
                        "session": session,
                        "expected_venues": [
                            str(order.get("broker_execution_venue") or venue)
                        ],
                        "expected_session_buckets": [session],
                        "anchor_at": partial_fill_at.isoformat(),
                        "anchor_price": float(order["first_fill_price"]),
                        "anchor_price_provenance": ("first_reconciliation_fill_price"),
                        "owner_target_price": None,
                        "lifecycle_stage": "exit_partial_fill",
                        "anchor_role": ("actual_widget_exit_partial_fill_reconciled"),
                        "execution_order_role": order.get("order_role"),
                        "execution_order_no": order.get("order_no"),
                        "broker_execution_venue": order.get("broker_execution_venue"),
                        **owner_cost_contract,
                        "owner_outcome": owner_outcome,
                        "owner_lifecycle_contract_valid": True,
                        "owner_policy_tuning_eligible": policy_tuning_eligible,
                        "actual_order_submitted": True,
                    }
                )
        if sell_qty > 0 and exit_at is not None:
            manual_exit_only = bool(manual_sell_qty == sell_qty and manual_sell_qty > 0)
            anchors.append(
                {
                    "anchor_id": f"{lifecycle_id}:exit",
                    "lifecycle_id": lifecycle_id,
                    "owner": "widget",
                    "scope_id": scope_id,
                    "symbol": symbol,
                    "session": session,
                    "expected_venues": (
                        exit_execution_venues if exit_execution_venues else [venue]
                    ),
                    "expected_session_buckets": [session],
                    "anchor_at": exit_at.isoformat(),
                    "anchor_price": sell_notional / sell_qty,
                    "owner_target_price": None,
                    "lifecycle_stage": "exit" if realized else "exit_partial_fill",
                    "anchor_role": (
                        "actual_widget_manual_partial_exit_reconciled"
                        if manual_exit_only and buy_qty > sell_qty
                        else (
                            "actual_widget_manual_exit_reconciled"
                            if manual_exit_only
                            else (
                                "actual_widget_exit_fill_reconciled"
                                if realized
                                else "actual_widget_exit_partial_fill_reconciled"
                            )
                        )
                    ),
                    "broker_execution_venues": exit_execution_venues,
                    **owner_cost_contract,
                    "owner_outcome": owner_outcome,
                    "owner_lifecycle_contract_valid": True,
                    "owner_policy_tuning_eligible": policy_tuning_eligible,
                    "actual_order_submitted": True,
                }
            )
    for opportunity in blocked_daily_entry_limit_opportunities:
        symbol = str(opportunity["symbol"])
        session = str(opportunity["session"])
        venue = WIDGET_SESSION_VENUES[session]
        signal_id = str(opportunity["signal_id"])
        scope_id = f"actual_blocked:{symbol}:{session}"
        row = symbols.setdefault(
            symbol,
            {
                "symbol": symbol,
                "name": None,
                "scopes": [],
                "owner_scope_ids": [],
                "owner_scope_kinds": {},
                "owner_scope_expected_venues": {},
                "owner_anchor_contract_gaps": [],
                "expected_venues": [],
                "owner_inventory_source": ("exact_date_widget_execution_event_journal"),
            },
        )
        for key, default in (
            ("scopes", []),
            ("owner_scope_ids", []),
            ("owner_scope_kinds", {}),
            ("owner_scope_expected_venues", {}),
            ("owner_anchor_contract_gaps", []),
            ("expected_venues", []),
        ):
            row.setdefault(key, default.copy())
        if "active_widget_actual_execution" not in row["scopes"]:
            row["scopes"].append("active_widget_actual_execution")
        if scope_id not in row["owner_scope_ids"]:
            row["owner_scope_ids"].append(scope_id)
        row["owner_scope_kinds"][scope_id] = "active_widget_actual_execution"
        row["owner_scope_expected_venues"][scope_id] = [venue]
        if venue not in row["expected_venues"]:
            row["expected_venues"].append(venue)
        source_only_outcome = {
            "exit_at": opportunity.get("source_only_exit_at"),
            "exit_price": opportunity.get("source_only_exit_price"),
            "exit_reason": opportunity.get("source_only_exit_reason"),
            "realized": False,
            "actual_order_submitted": False,
            "broker_fill_observed": False,
            "counterfactual_only": True,
        }
        lifecycle_id = f"widget_daily_cap_blocked:{symbol}:{signal_id}"
        anchors.append(
            {
                "anchor_id": f"{lifecycle_id}:signal",
                "lifecycle_id": lifecycle_id,
                "owner": "widget",
                "scope_id": scope_id,
                "symbol": symbol,
                "session": session,
                "expected_venues": [venue],
                "expected_session_buckets": [session],
                "anchor_at": opportunity["observed_at"],
                "anchor_price": opportunity.get("entry_price"),
                "anchor_price_provenance": (
                    "source_qualified_advisory_entry_price_no_broker_order"
                ),
                "owner_target_price": opportunity.get("target_price"),
                "lifecycle_stage": "entry",
                "anchor_role": ("actual_widget_daily_cap_blocked_entry_signal"),
                "entry_state": opportunity.get("entry_state"),
                "structural_support": opportunity.get("structural_support"),
                "source_entry_event_id": signal_id,
                "owner_round_trip_cost_pct": round_trip_cost_pct,
                "owner_round_trip_cost_provenance": (
                    "widget_comparison_cost.effective_dated_contract"
                ),
                "owner_round_trip_cost_contract_sha256": (
                    comparison_cost["contract_sha256"]
                    if comparison_cost is not None
                    else None
                ),
                "owner_outcome": source_only_outcome,
                "owner_lifecycle_contract_valid": True,
                "owner_policy_tuning_eligible": False,
                "actual_order_submitted": False,
                "daily_entry_limit_blocked": True,
            }
        )
    for gap in instrumentation_gaps:
        parts = gap.split(":", 2)
        if len(parts) >= 2 and parts[1] in symbols:
            symbols[parts[1]].setdefault("owner_anchor_contract_gaps", []).append(
                {"scope_id": f"actual:{parts[1]}:unknown", "reason": gap}
            )
    advisory_contract_gaps = (
        [f"advisory:{value}" for value in advisory_source.get("contract_errors") or []]
        if advisory_source.get("status") == "contract_invalid"
        else []
    )
    source.update(
        {
            "status": (
                "loaded_with_instrumentation_gaps"
                if instrumentation_gaps or advisory_contract_gaps
                else "loaded"
            ),
            "optional_when_absent": False,
            "grouped_lifecycle_count": len(lifecycle_orders),
            "actual_lifecycle_count": len(
                {
                    str(anchor.get("lifecycle_id"))
                    for anchor in anchors
                    if anchor.get("lifecycle_id")
                    and anchor.get("actual_order_submitted") is True
                }
            ),
            "source_only_blocked_entry_anchor_count": sum(
                anchor.get("daily_entry_limit_blocked") is True for anchor in anchors
            ),
            "anchor_count": len(anchors),
            "contract_errors": instrumentation_gaps + advisory_contract_gaps,
            "blocked_daily_entry_limit_opportunities": (
                blocked_daily_entry_limit_opportunities
            ),
        }
    )
    return anchors, source


def _widget_inventory(
    target_date: str,
    report_root: Path,
    *,
    widget_state_path: Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    calibration_path = (
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json"
    )
    research_path = (
        report_root
        / "widget_symbol_signal_policy_research"
        / f"widget_symbol_signal_policy_research_{target_date}.json"
    )
    expansion_path = (
        report_root
        / "widget_collector_expansion_recommendation"
        / f"widget_collector_expansion_recommendation_{target_date}.json"
    )
    calibration_schemas = ("widget_auto_trade_policy_calibration_report_v1",)
    research_schemas = (
        "widget_symbol_signal_policy_research_v2",
        "widget_symbol_signal_policy_research_v3",
    )
    expansion_schemas = ("widget_collector_expansion_recommendation_v1",)
    calibration = _read_target_json(
        calibration_path, target_date, expected_schemas=calibration_schemas
    )
    research = _read_target_json(
        research_path,
        target_date,
        date_fields=("target_date", "end_date"),
        expected_schemas=research_schemas,
    )
    expansion = _read_target_json(
        expansion_path, target_date, expected_schemas=expansion_schemas
    )
    declared_widget_round_trip_cost_pct = _finite_float(
        (calibration or {}).get("round_trip_cost_pct")
    )
    widget_cost_contract = (
        comparison_cost_contract(target_date)
        if date.fromisoformat(target_date) >= CLEAN_BASELINE_DATE
        else None
    )
    widget_round_trip_cost_pct = (
        float(widget_cost_contract["round_trip_cost_pct"])
        if widget_cost_contract is not None
        else None
    )
    declared_widget_cost_contract = (
        calibration.get("comparison_cost_contract")
        if isinstance(calibration, dict)
        else None
    )
    widget_cost_contract_matches = bool(
        widget_cost_contract is None
        or declared_widget_round_trip_cost_pct is None
        or math.isclose(
            declared_widget_round_trip_cost_pct,
            float(widget_round_trip_cost_pct),
            abs_tol=1e-12,
        )
    )
    widget_cost_contract_ready = bool(
        widget_cost_contract is not None
        and isinstance(declared_widget_cost_contract, dict)
        and declared_widget_cost_contract.get("contract_sha256")
        == widget_cost_contract.get("contract_sha256")
        and declared_widget_round_trip_cost_pct is not None
        and widget_cost_contract_matches
    )
    declared_research_cost_contract = (
        research.get("comparison_cost_contract") if isinstance(research, dict) else None
    )
    research_cost_contract_ready = bool(
        widget_cost_contract is not None
        and isinstance(declared_research_cost_contract, dict)
        and declared_research_cost_contract.get("contract_sha256")
        == widget_cost_contract.get("contract_sha256")
    )
    symbols: dict[str, dict[str, Any]] = {}
    anchors: list[dict[str, Any]] = []

    report_symbols = (calibration or {}).get("symbols") or {}
    if isinstance(report_symbols, dict):
        for symbol, payload in report_symbols.items():
            if not isinstance(payload, dict):
                continue
            row = symbols.setdefault(
                str(symbol),
                {
                    "symbol": str(symbol),
                    "name": payload.get("name"),
                    "scopes": [],
                    "owner_scope_ids": [],
                    "owner_scope_kinds": {},
                    "owner_scope_expected_venues": {},
                    "owner_anchor_contract_gaps": [],
                    "expected_venues": [],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            row.setdefault("owner_scope_ids", [])
            row.setdefault("owner_scope_kinds", {})
            row.setdefault("owner_scope_expected_venues", {})
            row.setdefault("owner_anchor_contract_gaps", [])
            if "active_widget_owner" not in row["scopes"]:
                row["scopes"].append("active_widget_owner")
            sessions = payload.get("sessions") or {}
            if not isinstance(sessions, dict):
                continue
            for session, session_payload in sessions.items():
                if not isinstance(session_payload, dict):
                    continue
                venue = str(session).split("_", 1)[0].upper()
                scope_id = f"{symbol}:{session}"
                if scope_id not in row["owner_scope_ids"]:
                    row["owner_scope_ids"].append(scope_id)
                row["owner_scope_kinds"][scope_id] = "active_widget_owner"
                row["owner_scope_expected_venues"][scope_id] = [venue]
                if (
                    venue in {"KRX", "NXT", "SOR"}
                    and venue not in row["expected_venues"]
                ):
                    row["expected_venues"].append(venue)
                trades = session_payload.get("selected_trades") or []
                if not isinstance(trades, list):
                    continue
                selected_policy = session_payload.get("selected_policy") or {}
                target_bps = (
                    _finite_float(selected_policy.get("target_bps"))
                    if isinstance(selected_policy, dict)
                    else None
                )
                for index, trade in enumerate(trades, start=1):
                    if (
                        not isinstance(trade, dict)
                        or trade.get("trade_date") != target_date
                    ):
                        continue
                    raw_entry_at = _parse_owner_ts(trade.get("entry_at"))
                    entry_at = _owner_ts_on_target_date(
                        trade.get("entry_at"), target_date
                    )
                    if entry_at is None:
                        row["owner_anchor_contract_gaps"].append(
                            {
                                "scope_id": scope_id,
                                "reason": (
                                    "entry_at_outside_target_date"
                                    if raw_entry_at is not None
                                    else "entry_at_missing_or_invalid"
                                ),
                            }
                        )
                        continue
                    entry_price = _finite_float(
                        trade.get("average_price") or trade.get("entry_price")
                    )
                    if entry_price is None or entry_price <= 0:
                        row["owner_anchor_contract_gaps"].append(
                            {
                                "scope_id": scope_id,
                                "reason": "entry_price_missing_or_invalid",
                            }
                        )
                        continue
                    exit_reason = str(trade.get("exit_reason") or "").strip() or None
                    raw_exit_at = _parse_owner_ts(trade.get("exit_at"))
                    exit_at = _owner_ts_on_target_date(
                        trade.get("exit_at"), target_date
                    )
                    exit_price = _finite_float(trade.get("exit_price"))
                    resolved_exit_requested = exit_reason not in {
                        None,
                        "right_censored",
                    }
                    resolved_exit_valid = bool(
                        resolved_exit_requested
                        and exit_at is not None
                        and exit_at >= entry_at
                        and exit_price is not None
                        and exit_price > 0
                    )
                    if resolved_exit_requested and not resolved_exit_valid:
                        reason = "resolved_exit_timestamp_or_price_invalid"
                        if raw_exit_at is not None and exit_at is None:
                            reason = "resolved_exit_outside_target_date"
                        elif exit_at is not None and exit_at < entry_at:
                            reason = "resolved_exit_before_entry"
                        row["owner_anchor_contract_gaps"].append(
                            {
                                "scope_id": scope_id,
                                "reason": reason,
                            }
                        )
                    holding_duration_ms = (
                        round((exit_at - entry_at).total_seconds() * 1000.0)
                        if resolved_exit_valid
                        else None
                    )
                    owner_target_price = (
                        entry_price * (1.0 + target_bps / 10000.0)
                        if entry_price is not None
                        and entry_price > 0
                        and target_bps is not None
                        and target_bps > 0
                        else (
                            exit_price
                            if exit_reason == "fixed_average_take_profit"
                            else None
                        )
                    )
                    lifecycle_id = (
                        f"widget:{symbol}:{session}:{index}:{entry_at.isoformat()}"
                    )
                    anchors.append(
                        {
                            "anchor_id": f"{lifecycle_id}:entry",
                            "lifecycle_id": lifecycle_id,
                            "owner": "widget",
                            "scope_id": f"{symbol}:{session}",
                            "symbol": str(symbol),
                            "session": str(session),
                            "expected_venues": [str(session).split("_", 1)[0]],
                            "expected_session_buckets": [str(session)],
                            "anchor_at": entry_at.isoformat(),
                            "anchor_price": entry_price,
                            "owner_target_price": owner_target_price,
                            "lifecycle_stage": "entry",
                            "anchor_role": "counterfactual_calibration_entry",
                            "owner_round_trip_cost_pct": widget_round_trip_cost_pct,
                            "owner_round_trip_cost_provenance": (
                                "widget_auto_trade_policy_calibration.round_trip_cost_pct"
                            ),
                            "owner_outcome": {
                                "exit_at": exit_at.isoformat() if exit_at else None,
                                "exit_price": exit_price,
                                "exit_reason": exit_reason,
                                "holding_duration_ms": holding_duration_ms,
                                "gross_no_slippage_return_pct": _finite_float(
                                    trade.get("gross_return_pct")
                                ),
                                "cost_aware_net_return_pct": _finite_float(
                                    trade.get("net_return_pct")
                                ),
                                "entry_notional_krw": entry_price,
                                "quantity_basis": "one_share_normalized",
                                "realized": resolved_exit_valid,
                            },
                            "owner_lifecycle_contract_valid": (
                                not resolved_exit_requested or resolved_exit_valid
                            ),
                            "owner_policy_tuning_eligible": (
                                widget_cost_contract_ready
                            ),
                            "actual_order_submitted": False,
                        }
                    )
                    if resolved_exit_valid:
                        anchors.append(
                            {
                                "anchor_id": f"{lifecycle_id}:exit",
                                "lifecycle_id": lifecycle_id,
                                "owner": "widget",
                                "scope_id": f"{symbol}:{session}",
                                "symbol": str(symbol),
                                "session": str(session),
                                "expected_venues": [str(session).split("_", 1)[0]],
                                "expected_session_buckets": [str(session)],
                                "anchor_at": exit_at.isoformat(),
                                "anchor_price": exit_price,
                                "owner_target_price": None,
                                "lifecycle_stage": "exit",
                                "anchor_role": "counterfactual_calibration_exit",
                                "owner_round_trip_cost_pct": (
                                    widget_round_trip_cost_pct
                                ),
                                "owner_round_trip_cost_provenance": (
                                    "widget_auto_trade_policy_calibration.round_trip_cost_pct"
                                ),
                                "owner_outcome": {
                                    "entry_at": entry_at.isoformat(),
                                    "holding_duration_ms": holding_duration_ms,
                                    "exit_reason": exit_reason,
                                    "gross_no_slippage_return_pct": _finite_float(
                                        trade.get("gross_return_pct")
                                    ),
                                    "cost_aware_net_return_pct": _finite_float(
                                        trade.get("net_return_pct")
                                    ),
                                    "entry_notional_krw": entry_price,
                                    "quantity_basis": "one_share_normalized",
                                    "realized": True,
                                },
                                "owner_lifecycle_contract_valid": True,
                                "owner_policy_tuning_eligible": (
                                    widget_cost_contract_ready
                                ),
                                "actual_order_submitted": False,
                            }
                        )

    research_symbols = (research or {}).get("symbols") or {}
    if isinstance(research_symbols, dict):
        for symbol, payload in research_symbols.items():
            symbol = str(symbol)
            row = symbols.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": (
                        (payload or {}).get("name")
                        if isinstance(payload, dict)
                        else None
                    ),
                    "scopes": [],
                    "owner_scope_ids": [],
                    "owner_scope_kinds": {},
                    "owner_scope_expected_venues": {},
                    "owner_anchor_contract_gaps": [],
                    "expected_venues": ["KRX"],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            row.setdefault("owner_scope_ids", [])
            row.setdefault("owner_scope_kinds", {})
            row.setdefault("owner_scope_expected_venues", {})
            row.setdefault("owner_anchor_contract_gaps", [])
            if "prospective_widget_research" not in row["scopes"]:
                row["scopes"].append("prospective_widget_research")
            scope_id = f"research:{symbol}:KRX_REGULAR"
            if scope_id not in row["owner_scope_ids"]:
                row["owner_scope_ids"].append(scope_id)
            row["owner_scope_kinds"][scope_id] = "prospective_widget_research"
            row["owner_scope_expected_venues"][scope_id] = ["KRX"]
            if "KRX" not in row["expected_venues"]:
                row["expected_venues"].append("KRX")
            holdout = (
                (payload or {}).get("holdout") if isinstance(payload, dict) else {}
            )
            episodes = (
                (holdout or {}).get("episodes") if isinstance(holdout, dict) else []
            )
            if not isinstance(episodes, list):
                row["owner_anchor_contract_gaps"].append(
                    {"scope_id": scope_id, "reason": "holdout_episodes_invalid"}
                )
                continue
            for index, episode in enumerate(episodes, start=1):
                if (
                    not isinstance(episode, dict)
                    or episode.get("trade_date") != target_date
                ):
                    continue
                raw_entry_at = _parse_owner_ts(episode.get("entry_at"))
                entry_at = _owner_ts_on_target_date(
                    episode.get("entry_at"), target_date
                )
                entry_price = _finite_float(episode.get("entry_price"))
                if entry_at is None or entry_price is None or entry_price <= 0:
                    reason = "research_entry_timestamp_or_price_invalid"
                    if raw_entry_at is not None and entry_at is None:
                        reason = "research_entry_outside_target_date"
                    row["owner_anchor_contract_gaps"].append(
                        {
                            "scope_id": scope_id,
                            "reason": reason,
                        }
                    )
                    continue
                exit_reason = str(episode.get("exit_reason") or "").strip() or None
                raw_exit_at = _parse_owner_ts(episode.get("exit_at"))
                exit_at = _owner_ts_on_target_date(episode.get("exit_at"), target_date)
                exit_price = _finite_float(episode.get("exit_price"))
                resolved_exit_requested = exit_reason not in {
                    None,
                    "right_censored",
                }
                resolved_exit_valid = bool(
                    resolved_exit_requested
                    and exit_at is not None
                    and exit_at >= entry_at
                    and exit_price is not None
                    and exit_price > 0
                )
                if resolved_exit_requested and not resolved_exit_valid:
                    reason = "research_exit_timestamp_or_price_invalid"
                    if raw_exit_at is not None and exit_at is None:
                        reason = "research_exit_outside_target_date"
                    elif exit_at is not None and exit_at < entry_at:
                        reason = "research_exit_before_entry"
                    row["owner_anchor_contract_gaps"].append(
                        {
                            "scope_id": scope_id,
                            "reason": reason,
                        }
                    )
                holding_duration_ms = (
                    round((exit_at - entry_at).total_seconds() * 1000.0)
                    if resolved_exit_valid
                    else None
                )
                lifecycle_id = (
                    f"widget_research:{symbol}:{index}:{entry_at.isoformat()}"
                )
                owner_outcome = {
                    "exit_at": exit_at.isoformat() if exit_at else None,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "holding_duration_ms": holding_duration_ms,
                    "gross_no_slippage_return_pct": (
                        round((exit_price / entry_price - 1.0) * 100.0, 6)
                        if resolved_exit_valid
                        else None
                    ),
                    "cost_aware_net_return_pct": _finite_float(
                        episode.get("net_return_pct")
                    ),
                    "entry_notional_krw": entry_price,
                    "quantity_basis": "one_share_normalized",
                    "realized": resolved_exit_valid,
                }
                common_anchor = {
                    "lifecycle_id": lifecycle_id,
                    "owner": "widget",
                    "scope_id": scope_id,
                    "symbol": symbol,
                    "session": "KRX_REGULAR",
                    "expected_venues": ["KRX"],
                    "expected_session_buckets": ["KRX_REGULAR"],
                    "actual_order_submitted": False,
                    "owner_lifecycle_contract_valid": (
                        not resolved_exit_requested or resolved_exit_valid
                    ),
                    "owner_policy_tuning_eligible": research_cost_contract_ready,
                    "owner_round_trip_cost_pct": widget_round_trip_cost_pct,
                    "owner_round_trip_cost_provenance": (
                        "widget_auto_trade_policy_calibration.round_trip_cost_pct"
                    ),
                }
                anchors.append(
                    {
                        **common_anchor,
                        "anchor_id": f"{lifecycle_id}:entry",
                        "anchor_at": entry_at.isoformat(),
                        "anchor_price": entry_price,
                        "owner_target_price": _finite_float(
                            episode.get("target_price")
                        ),
                        "lifecycle_stage": "entry",
                        "anchor_role": "prospective_widget_research_entry",
                        "owner_outcome": owner_outcome,
                    }
                )
                if resolved_exit_valid:
                    anchors.append(
                        {
                            **common_anchor,
                            "anchor_id": f"{lifecycle_id}:exit",
                            "anchor_at": exit_at.isoformat(),
                            "anchor_price": exit_price,
                            "owner_target_price": None,
                            "lifecycle_stage": "exit",
                            "anchor_role": "prospective_widget_research_exit",
                            "owner_outcome": owner_outcome,
                        }
                    )

    recommendations = (expansion or {}).get("recommendations") or []
    if isinstance(recommendations, list):
        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                continue
            symbol = str(
                recommendation.get("stock_code") or recommendation.get("symbol") or ""
            )
            if not symbol:
                continue
            row = symbols.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": recommendation.get("stock_name"),
                    "scopes": [],
                    "owner_scope_ids": [],
                    "owner_scope_kinds": {},
                    "owner_scope_expected_venues": {},
                    "owner_anchor_contract_gaps": [],
                    "expected_venues": ["SOR"],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            row.setdefault("owner_scope_ids", [])
            row.setdefault("owner_scope_kinds", {})
            row.setdefault("owner_scope_expected_venues", {})
            row.setdefault("owner_anchor_contract_gaps", [])
            if "prospective_widget_collector_expansion" not in row["scopes"]:
                row["scopes"].append("prospective_widget_collector_expansion")
            scope_id = f"expansion:{symbol}:SOR_REGULAR"
            if scope_id not in row["owner_scope_ids"]:
                row["owner_scope_ids"].append(scope_id)
            row["owner_scope_kinds"][
                scope_id
            ] = "prospective_widget_collector_expansion"
            row["owner_scope_expected_venues"][scope_id] = ["SOR"]

    actual_anchors, actual_source = _widget_actual_execution_inventory(
        target_date=target_date,
        report_root=report_root,
        state_path=widget_state_path,
        symbols=symbols,
    )
    anchors.extend(actual_anchors)

    for row in symbols.values():
        if not row.get("expected_venues"):
            row["expected_venues"] = ["SOR"]
        else:
            row["expected_venues"] = sorted(set(row["expected_venues"]))

    return (
        symbols,
        anchors,
        {
            "comparison_cost": {
                "status": (
                    "pre_clean_baseline_archive_only"
                    if widget_cost_contract is None
                    else (
                        "not_observed"
                        if calibration is None
                        else (
                            "calibration_declared_cost_missing"
                            if declared_widget_round_trip_cost_pct is None
                            else (
                                "calibration_declared_cost_contract_missing_or_invalid"
                                if not isinstance(declared_widget_cost_contract, dict)
                                else (
                                    "loaded"
                                    if widget_cost_contract_ready
                                    else "calibration_declared_cost_mismatch"
                                )
                            )
                        )
                    )
                ),
                "optional_when_absent": calibration is None,
                "declared_round_trip_cost_pct": (declared_widget_round_trip_cost_pct),
                "resolved_contract": widget_cost_contract,
            },
            "symbol_research_comparison_cost": {
                "status": (
                    "pre_clean_baseline_archive_only"
                    if widget_cost_contract is None
                    else (
                        "not_observed"
                        if research is None
                        else (
                            "loaded"
                            if research_cost_contract_ready
                            else "research_declared_cost_contract_missing_or_invalid"
                        )
                    )
                ),
                "optional_when_absent": research is None,
                "resolved_contract": widget_cost_contract,
            },
            "calibration": _source(
                calibration_path,
                calibration,
                target_date=target_date,
                expected_schemas=calibration_schemas,
            ),
            "symbol_research": _source(
                research_path,
                research,
                target_date=target_date,
                expected_schemas=research_schemas,
                date_fields=("target_date", "end_date"),
            ),
            "collector_expansion_recommendation": _source(
                expansion_path,
                expansion,
                target_date=target_date,
                expected_schemas=expansion_schemas,
            ),
            "actual_execution_events": actual_source,
        },
    )


def _signal_anchor(row: dict[str, Any]) -> tuple[datetime | None, float | None]:
    features = row.get("signal_features") or {}
    signal = features.get("signal_bar") or {}
    if isinstance(signal, dict):
        # Compatibility for early synthetic/research fixtures.
        timestamp = _parse_owner_ts(
            features.get("signal_decision_at")
            or signal.get("decision_at")
            or signal.get("timestamp")
            or signal.get("at")
        )
        price = _finite_float(signal.get("close_price") or signal.get("close"))
    else:
        # Keep the completed-bar timestamp for legacy owner diagnostics. New
        # entry-timing anchors are emitted separately from signal_decision_at;
        # this fallback is never policy-eligible by itself.
        timestamp = _parse_owner_ts(features.get("signal_decision_at") or signal)
        price = _finite_float(features.get("signal_close"))
    return timestamp, price


def _has_positive_fill(legs: Any) -> bool:
    if not isinstance(legs, list):
        return False
    for leg in legs:
        if not isinstance(leg, dict):
            continue
        try:
            if int(leg.get("buy_filled_qty") or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _episode_inventory(
    target_date: str, report_root: Path
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    tuning_path = (
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json"
    )
    expansion_path = (
        report_root
        / "low_price_two_leg_expanded_candidate_research"
        / f"low_price_two_leg_expanded_candidate_research_{target_date}.json"
    )
    samsung_path = (
        report_root
        / "samsung_machine_entry_tuning"
        / f"samsung_machine_entry_tuning_{target_date}.json"
    )
    tuning_schemas = (
        "low_price_two_leg_tuning_report_v3",
        "low_price_two_leg_tuning_report_v4",
        "low_price_two_leg_tuning_report_v5",
        "low_price_two_leg_tuning_report_v6",
    )
    expansion_schemas = ("low_price_two_leg_expanded_candidate_research_v5",)
    samsung_schemas = tuple(
        f"samsung_machine_entry_tuning_report_v{version}" for version in range(2, 8)
    )
    tuning = _read_target_json(
        tuning_path, target_date, expected_schemas=tuning_schemas
    )
    expansion = _read_target_json(
        expansion_path, target_date, expected_schemas=expansion_schemas
    )
    samsung = _read_target_json(
        samsung_path, target_date, expected_schemas=samsung_schemas
    )
    episode_round_trip_cost_pct = _finite_float((tuning or {}).get("cost_pct"))
    episode_round_trip_cost_provenance = "low_price_two_leg_tuning.cost_pct"
    prospective_episode_round_trip_cost_pct = _finite_float(
        (expansion or {}).get("cost_pct")
    )
    prospective_episode_round_trip_cost_provenance = (
        "low_price_two_leg_expanded_candidate_research.cost_pct"
    )
    profiles: dict[str, dict[str, Any]] = {}
    anchors: list[dict[str, Any]] = []

    for profile_id, spec in PROFILES.items():
        profiles[profile_id] = {
            "profile_id": profile_id,
            "symbol": spec.symbol,
            "session": spec.session,
            "scope": "active_episode_owner",
            "expected_venues": ["SOR"],
            "owner_inventory_source": "runtime_registry_fallback",
        }

    daily_profiles = ((tuning or {}).get("daily") or {}).get("profiles") or {}
    if isinstance(daily_profiles, dict):
        for profile_id, payload in daily_profiles.items():
            if not isinstance(payload, dict):
                continue
            profile_id = str(profile_id)
            row = profiles.setdefault(profile_id, {})
            registered_profile = PROFILES.get(profile_id)
            owner_identity_valid = bool(
                registered_profile is not None
                and payload.get("symbol") == registered_profile.symbol
                and payload.get("session") == registered_profile.session
            )
            row.update(
                {
                    "profile_id": profile_id,
                    "symbol": str(
                        registered_profile.symbol
                        if registered_profile is not None
                        else ""
                    ),
                    "session": (
                        registered_profile.session
                        if registered_profile is not None
                        else None
                    ),
                    "scope": (
                        "active_episode_owner"
                        if registered_profile is not None
                        else "invalid_episode_owner_identity"
                    ),
                    "expected_venues": (
                        ["SOR"] if registered_profile is not None else []
                    ),
                    "owner_inventory_source": "target_date_postclose_report",
                    "owner_source_quality": payload.get("source_quality"),
                    "attempted": payload.get("attempted") is True,
                    "owner_anchor_contract_status": "not_applicable_no_attempt",
                    "lifecycle_instrumentation_gaps": [],
                }
            )
            if not owner_identity_valid:
                row["owner_policy_tuning_eligible"] = False
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "owner_profile_identity_contract_invalid"
                )
                continue
            if payload.get("target_date") != target_date:
                row["owner_policy_tuning_eligible"] = False
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "owner_nested_target_date_contract_invalid"
                )
                continue
            anchor_at, anchor_price = _signal_anchor(payload)
            signal_features = payload.get("signal_features") or {}
            decision_at = (
                _parse_owner_ts(signal_features.get("signal_decision_at"))
                if isinstance(signal_features, dict)
                else None
            )
            if (
                anchor_at is not None
                and anchor_at.astimezone(KST).date().isoformat() != target_date
            ):
                row["lifecycle_instrumentation_gaps"].append(
                    "signal_bar_outside_target_date"
                )
                anchor_at = None
            owner_row_eligible = bool(
                payload.get("attempted") is True
                and payload.get("eligible_for_tuning") is True
                and payload.get("source_quality") == "pass"
            )
            source_quality_reasons = {
                str(reason) for reason in payload.get("source_quality_reasons") or []
            }
            held_inventory_only_gap = bool(
                payload.get("source_quality") == "gap"
                and source_quality_reasons == {"held_or_unresolved_inventory"}
            )
            owner_diagnostic_eligible = bool(
                payload.get("attempted") is True
                and (owner_row_eligible or held_inventory_only_gap)
            )
            row["owner_policy_tuning_eligible"] = owner_row_eligible
            if (
                owner_diagnostic_eligible
                and anchor_at is not None
                and anchor_price is not None
            ):
                row["owner_anchor_contract_status"] = "valid"
                lifecycle_id = f"episode:{profile_id}:{anchor_at.isoformat()}"
                lifecycle_invalid = False
                legs = payload.get("legs") or []
                owner_target_prices = [
                    value
                    for leg in legs
                    if isinstance(leg, dict)
                    and (value := _finite_float(leg.get("target_price"))) is not None
                    and value > 0
                ]
                anchors.append(
                    {
                        "anchor_id": f"{lifecycle_id}:signal",
                        "lifecycle_id": lifecycle_id,
                        "owner": "episode",
                        "scope_id": profile_id,
                        "symbol": row["symbol"],
                        "session": row["session"],
                        "expected_venues": ["SOR"],
                        "expected_session_buckets": ["SOR_REGULAR"],
                        "anchor_at": anchor_at.isoformat(),
                        "anchor_price": anchor_price,
                        "owner_target_price": (
                            min(owner_target_prices) if owner_target_prices else None
                        ),
                        "lifecycle_stage": "entry",
                        "anchor_role": "episode_signal_bar",
                        "entry_timing_decision_anchor_valid": False,
                        "owner_round_trip_cost_pct": episode_round_trip_cost_pct,
                        "owner_round_trip_cost_provenance": (
                            episode_round_trip_cost_provenance
                        ),
                        "owner_lifecycle_contract_valid": True,
                        "owner_policy_tuning_eligible": owner_row_eligible,
                        "owner_source_quality": payload.get("source_quality"),
                        "actual_order_submitted": _has_positive_fill(
                            payload.get("legs")
                        ),
                    }
                )
                for leg_index, leg in enumerate(legs, start=1):
                    if not isinstance(leg, dict):
                        continue
                    leg_id = str(leg.get("leg_id") or leg_index)
                    buy_filled_qty_value = _finite_float(leg.get("buy_filled_qty"))
                    buy_filled_qty = (
                        int(buy_filled_qty_value)
                        if buy_filled_qty_value is not None
                        and buy_filled_qty_value >= 0
                        and buy_filled_qty_value.is_integer()
                        else 0
                    )
                    raw_buy_filled_at = _parse_owner_ts(leg.get("buy_filled_at"))
                    buy_filled_at = _owner_ts_on_target_date(
                        leg.get("buy_filled_at"), target_date
                    )
                    fill_price = _finite_float(leg.get("fill_price"))
                    target_filled_qty_value = _finite_float(
                        leg.get("target_filled_qty")
                    )
                    target_filled_qty = (
                        int(target_filled_qty_value)
                        if target_filled_qty_value is not None
                        and target_filled_qty_value >= 0
                        and target_filled_qty_value.is_integer()
                        else 0
                    )
                    raw_target_filled_at = _parse_owner_ts(leg.get("target_filled_at"))
                    target_filled_at = _owner_ts_on_target_date(
                        leg.get("target_filled_at"), target_date
                    )
                    target_fill_price = _finite_float(leg.get("target_fill_price"))
                    target_price = _finite_float(leg.get("target_price"))
                    valid_buy_fill = bool(
                        buy_filled_qty > 0
                        and buy_filled_at is not None
                        and buy_filled_at >= anchor_at
                        and fill_price is not None
                        and fill_price > 0
                    )
                    if buy_filled_qty > 0 and not valid_buy_fill:
                        lifecycle_invalid = True
                        reason = f"{leg_id}:buy_fill_timestamp_or_price_missing"
                        if raw_buy_filled_at is not None and buy_filled_at is None:
                            reason = f"{leg_id}:buy_fill_outside_target_date"
                        elif buy_filled_at is not None and buy_filled_at < anchor_at:
                            reason = f"{leg_id}:buy_fill_before_signal"
                        row["lifecycle_instrumentation_gaps"].append(reason)
                    valid_target_fill = bool(
                        target_filled_qty > 0
                        and valid_buy_fill
                        and target_filled_at is not None
                        and target_filled_at >= buy_filled_at
                        and target_fill_price is not None
                        and target_fill_price > 0
                        and target_filled_qty <= buy_filled_qty
                    )
                    if target_filled_qty > 0 and not valid_target_fill:
                        lifecycle_invalid = True
                        reason = f"{leg_id}:target_fill_timestamp_or_price_missing"
                        if (
                            raw_target_filled_at is not None
                            and target_filled_at is None
                        ):
                            reason = f"{leg_id}:target_fill_outside_target_date"
                        elif (
                            target_filled_at is not None
                            and buy_filled_at is not None
                            and target_filled_at < buy_filled_at
                        ):
                            reason = f"{leg_id}:target_fill_before_buy_fill"
                        elif target_filled_qty > buy_filled_qty:
                            reason = f"{leg_id}:target_fill_qty_exceeds_buy_fill_qty"
                        elif not valid_buy_fill:
                            reason = f"{leg_id}:target_fill_without_valid_buy_fill"
                        row["lifecycle_instrumentation_gaps"].append(reason)
                    holding_duration_ms = (
                        round(
                            (target_filled_at - buy_filled_at).total_seconds() * 1000.0
                        )
                        if valid_target_fill
                        else None
                    )
                    realized = bool(
                        valid_target_fill
                        and leg.get("completed") is True
                        and target_filled_qty == buy_filled_qty
                    )
                    exit_provenance = _episode_exit_outcome_provenance(
                        leg, realized=realized
                    )
                    if valid_buy_fill:
                        leg_gross_return_pct = _finite_float(
                            leg.get("gross_no_slippage_return_pct")
                        )
                        leg_net_return_pct = _finite_float(leg.get("net_profit_pct"))
                        leg_round_trip_cost_pct = (
                            leg_gross_return_pct - leg_net_return_pct
                            if leg_gross_return_pct is not None
                            and leg_net_return_pct is not None
                            and leg_gross_return_pct >= leg_net_return_pct
                            else episode_round_trip_cost_pct
                        )
                        signal_leg_outcome = {
                            "leg_id": leg_id,
                            "holding_duration_ms": holding_duration_ms,
                            "gross_no_slippage_return_pct": leg_gross_return_pct,
                            "cost_aware_net_return_pct": leg_net_return_pct,
                            "entry_notional_krw": (fill_price * buy_filled_qty),
                            "quantity": buy_filled_qty,
                            "quantity_basis": "broker_confirmed_fill",
                            "exit_price": target_fill_price,
                            "exit_at": (
                                target_filled_at.isoformat()
                                if target_filled_at is not None
                                else None
                            ),
                            "realized": realized,
                            **exit_provenance,
                        }
                        if decision_at is not None:
                            anchors.append(
                                {
                                    "anchor_id": (
                                        f"{lifecycle_id}:{leg_id}:signal_decision"
                                    ),
                                    "lifecycle_id": lifecycle_id,
                                    "owner": "episode",
                                    "scope_id": profile_id,
                                    "symbol": row["symbol"],
                                    "session": row["session"],
                                    "expected_venues": ["SOR"],
                                    "expected_session_buckets": ["SOR_REGULAR"],
                                    "anchor_at": decision_at.isoformat(),
                                    "anchor_price": fill_price,
                                    "anchor_price_provenance": (
                                        "broker_confirmed_baseline_fill_price"
                                    ),
                                    "owner_entry_limit_price": _finite_float(
                                        leg.get("entry_price")
                                    ),
                                    "owner_target_price": target_price,
                                    "lifecycle_stage": "entry",
                                    "anchor_role": "episode_signal_decision_leg",
                                    "entry_timing_decision_anchor_valid": True,
                                    "owner_round_trip_cost_pct": (
                                        episode_round_trip_cost_pct
                                    ),
                                    "owner_round_trip_cost_provenance": (
                                        episode_round_trip_cost_provenance
                                    ),
                                    "owner_outcome": signal_leg_outcome,
                                    "owner_lifecycle_contract_valid": True,
                                    "owner_policy_tuning_eligible": owner_row_eligible,
                                    "owner_timing_custody_observation_eligible": (
                                        held_inventory_only_gap
                                    ),
                                    "owner_source_quality": payload.get(
                                        "source_quality"
                                    ),
                                    "actual_order_submitted": True,
                                }
                            )
                        anchors.append(
                            {
                                "anchor_id": f"{lifecycle_id}:{leg_id}:buy_fill",
                                "lifecycle_id": lifecycle_id,
                                "owner": "episode",
                                "scope_id": profile_id,
                                "symbol": row["symbol"],
                                "session": row["session"],
                                "expected_venues": ["SOR"],
                                "expected_session_buckets": ["SOR_REGULAR"],
                                "anchor_at": buy_filled_at.isoformat(),
                                "anchor_price": fill_price,
                                "owner_target_price": target_price,
                                "lifecycle_stage": "entry",
                                "anchor_role": "episode_buy_fill_confirmed",
                                "owner_round_trip_cost_pct": leg_round_trip_cost_pct,
                                "owner_round_trip_cost_provenance": (
                                    episode_round_trip_cost_provenance
                                ),
                                "owner_outcome": signal_leg_outcome,
                                "owner_lifecycle_contract_valid": True,
                                "owner_policy_tuning_eligible": owner_row_eligible,
                                "owner_source_quality": payload.get("source_quality"),
                                "actual_order_submitted": True,
                            }
                        )
                    if valid_target_fill:
                        target_anchor_role = _episode_exit_anchor_role(
                            realized=realized,
                            exit_execution_class=str(
                                exit_provenance["exit_execution_class"]
                            ),
                        )
                        anchors.append(
                            {
                                "anchor_id": f"{lifecycle_id}:{leg_id}:target_fill",
                                "lifecycle_id": lifecycle_id,
                                "owner": "episode",
                                "scope_id": profile_id,
                                "symbol": row["symbol"],
                                "session": row["session"],
                                "expected_venues": ["SOR"],
                                "expected_session_buckets": ["SOR_REGULAR"],
                                "anchor_at": target_filled_at.isoformat(),
                                "anchor_price": target_fill_price,
                                "owner_target_price": None,
                                "lifecycle_stage": (
                                    "exit" if realized else "exit_partial_fill"
                                ),
                                "anchor_role": target_anchor_role,
                                "owner_round_trip_cost_pct": (
                                    episode_round_trip_cost_pct
                                ),
                                "owner_round_trip_cost_provenance": (
                                    episode_round_trip_cost_provenance
                                ),
                                "owner_outcome": {
                                    "leg_id": leg_id,
                                    "buy_filled_at": (
                                        buy_filled_at.isoformat()
                                        if buy_filled_at is not None
                                        else None
                                    ),
                                    "holding_duration_ms": holding_duration_ms,
                                    "gross_no_slippage_return_pct": _finite_float(
                                        leg.get("gross_no_slippage_return_pct")
                                    ),
                                    "cost_aware_net_return_pct": _finite_float(
                                        leg.get("net_profit_pct")
                                    ),
                                    "entry_notional_krw": (fill_price * buy_filled_qty),
                                    "quantity": buy_filled_qty,
                                    "quantity_basis": "broker_confirmed_fill",
                                    "realized": realized,
                                    **exit_provenance,
                                },
                                "owner_lifecycle_contract_valid": True,
                                "owner_policy_tuning_eligible": owner_row_eligible,
                                "owner_source_quality": payload.get("source_quality"),
                                "actual_order_submitted": True,
                            }
                        )
                if lifecycle_invalid:
                    row["owner_anchor_contract_status"] = "invalid"
                    row["owner_policy_tuning_eligible"] = False
                    for anchor in anchors:
                        if anchor.get("lifecycle_id") == lifecycle_id:
                            anchor["owner_lifecycle_contract_valid"] = False
                            anchor["owner_policy_tuning_eligible"] = False
            elif owner_diagnostic_eligible:
                row["owner_anchor_contract_status"] = "invalid"
                row["owner_policy_tuning_eligible"] = False
                row["lifecycle_instrumentation_gaps"].append(
                    "signal_bar_or_signal_close_missing_or_invalid"
                )
            elif payload.get("attempted") is True:
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "owner_source_quality_not_diagnostic_eligible"
                )

    samsung_machine_contracts = {
        "morning": {"scope_id": "morning", "strategy": "morning"},
        "morning_reentry": {
            "scope_id": "morning_sor_reentry",
            "strategy": "morning_sor_reentry",
        },
        "midday": {"scope_id": "midday", "strategy": "midday"},
        "afternoon": {"scope_id": "afternoon", "strategy": "afternoon"},
    }
    samsung_machines = ((samsung or {}).get("daily") or {}).get("machines") or {}
    if isinstance(samsung_machines, dict):
        for machine, contract in samsung_machine_contracts.items():
            payload = samsung_machines.get(machine)
            if not isinstance(payload, dict):
                continue
            scope_id = str(contract["scope_id"])
            profile_id = f"samsung:{scope_id}"
            features = payload.get("signal_features") or {}
            routes = {
                str(leg.get("route") or "")
                for leg in payload.get("legs") or []
                if isinstance(leg, dict) and str(leg.get("route") or "")
            }
            if machine == "morning" and not routes and isinstance(features, dict):
                routes = {
                    str(route)
                    for route in features.get("routes") or []
                    if str(route) in {"NXT", "SOR"}
                }
            route = next(iter(routes)) if len(routes) == 1 else ""
            session = "NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR"
            expected_venue = "NXT" if route == "NXT" else "SOR"
            expected_bucket = "NXT_PREMARKET" if route == "NXT" else "SOR_REGULAR"
            source_quality_reasons = {
                str(reason) for reason in payload.get("source_quality_reasons") or []
            }
            held_inventory_only_gap = bool(
                payload.get("source_quality") == "gap"
                and source_quality_reasons == {"held_or_unresolved_inventory"}
            )
            owner_row_eligible = bool(
                payload.get("attempted") is True
                and payload.get("eligible_for_cumulative_tuning") is True
                and payload.get("source_quality") == "pass"
            )
            owner_diagnostic_eligible = bool(
                payload.get("attempted") is True
                and (owner_row_eligible or held_inventory_only_gap)
            )
            row = profiles.setdefault(profile_id, {})
            row.update(
                {
                    "profile_id": profile_id,
                    "symbol": "005930",
                    "session": session,
                    "scope": "active_samsung_episode_owner",
                    "expected_venues": [expected_venue],
                    "owner_inventory_source": "samsung_target_date_postclose_report",
                    "owner_source_quality": payload.get("source_quality"),
                    "attempted": payload.get("attempted") is True,
                    "owner_policy_tuning_eligible": owner_row_eligible,
                    "owner_anchor_contract_status": "not_applicable_no_attempt",
                    "lifecycle_instrumentation_gaps": [],
                }
            )
            identity_valid = bool(
                (samsung or {}).get("symbol") == "005930"
                and payload.get("machine") == machine
                and payload.get("target_date") == target_date
                and isinstance(features, dict)
                and features.get("strategy") == contract["strategy"]
                and route in {"NXT", "SOR"}
            )
            decision_at = (
                _owner_ts_on_target_date(
                    features.get("signal_decision_at"), target_date
                )
                if isinstance(features, dict)
                else None
            )
            if not identity_valid:
                row["owner_policy_tuning_eligible"] = False
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "samsung_owner_identity_or_route_contract_invalid"
                )
                continue
            if not owner_diagnostic_eligible:
                if payload.get("attempted") is True:
                    row["owner_anchor_contract_status"] = "invalid"
                    row["lifecycle_instrumentation_gaps"].append(
                        "samsung_owner_source_quality_not_diagnostic_eligible"
                    )
                continue
            if decision_at is None:
                row["owner_policy_tuning_eligible"] = False
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "signal_decision_timestamp_missing_or_invalid"
                )
                continue
            lifecycle_id = f"episode:{scope_id}:{decision_at.isoformat()}"
            lifecycle_invalid = False
            emitted_decision_anchor = False
            for leg_index, leg in enumerate(payload.get("legs") or [], start=1):
                if not isinstance(leg, dict):
                    lifecycle_invalid = True
                    row["lifecycle_instrumentation_gaps"].append(
                        f"leg_{leg_index}:payload_invalid"
                    )
                    continue
                leg_id = str(leg.get("leg_id") or leg_index)
                buy_filled_qty_value = _finite_float(leg.get("buy_filled_qty"))
                buy_filled_qty = (
                    int(buy_filled_qty_value)
                    if buy_filled_qty_value is not None
                    and buy_filled_qty_value > 0
                    and buy_filled_qty_value.is_integer()
                    else 0
                )
                buy_filled_at = _owner_ts_on_target_date(
                    leg.get("buy_filled_at"), target_date
                )
                fill_price = _finite_float(leg.get("fill_price"))
                target_filled_qty_value = _finite_float(leg.get("target_filled_qty"))
                target_filled_qty = (
                    int(target_filled_qty_value)
                    if target_filled_qty_value is not None
                    and target_filled_qty_value >= 0
                    and target_filled_qty_value.is_integer()
                    else 0
                )
                target_filled_at = _owner_ts_on_target_date(
                    leg.get("target_filled_at"), target_date
                )
                target_fill_price = _finite_float(leg.get("target_fill_price"))
                target_price = _finite_float(leg.get("target_price"))
                valid_buy_fill = bool(
                    buy_filled_qty > 0
                    and buy_filled_at is not None
                    and buy_filled_at >= decision_at
                    and fill_price is not None
                    and fill_price > 0
                    and str(leg.get("route") or "") == route
                )
                if buy_filled_qty > 0 and not valid_buy_fill:
                    lifecycle_invalid = True
                    row["lifecycle_instrumentation_gaps"].append(
                        f"{leg_id}:buy_fill_contract_invalid"
                    )
                    continue
                if not valid_buy_fill:
                    continue
                realized = bool(
                    leg.get("completed") is True
                    and target_filled_qty == buy_filled_qty
                    and target_filled_at is not None
                    and target_filled_at >= buy_filled_at
                    and target_fill_price is not None
                    and target_fill_price > 0
                )
                exit_provenance = _episode_exit_outcome_provenance(
                    leg, realized=realized
                )
                if leg.get("completed") is True and not realized:
                    lifecycle_invalid = True
                    row["lifecycle_instrumentation_gaps"].append(
                        f"{leg_id}:target_fill_contract_invalid"
                    )
                gross_return = (
                    (target_fill_price / fill_price - 1.0) * 100.0 if realized else None
                )
                net_return = _finite_float(leg.get("equal_weight_profit_pct"))
                owner_outcome = {
                    "leg_id": leg_id,
                    "holding_duration_ms": (
                        round(
                            (target_filled_at - buy_filled_at).total_seconds() * 1000.0
                        )
                        if realized
                        else None
                    ),
                    "gross_no_slippage_return_pct": gross_return,
                    "cost_aware_net_return_pct": net_return,
                    "entry_notional_krw": fill_price * buy_filled_qty,
                    "quantity": buy_filled_qty,
                    "quantity_basis": "broker_confirmed_fill",
                    "exit_price": target_fill_price if realized else None,
                    "exit_at": target_filled_at.isoformat() if realized else None,
                    "realized": realized,
                    **exit_provenance,
                }
                anchors.append(
                    {
                        "anchor_id": f"{lifecycle_id}:{leg_id}:signal_decision",
                        "lifecycle_id": lifecycle_id,
                        "owner": "episode",
                        "scope_id": scope_id,
                        "symbol": "005930",
                        "session": session,
                        "expected_venues": [expected_venue],
                        "expected_session_buckets": [expected_bucket],
                        "anchor_at": decision_at.isoformat(),
                        "anchor_price": fill_price,
                        "anchor_price_provenance": (
                            "broker_confirmed_baseline_fill_price"
                        ),
                        "owner_entry_limit_price": _finite_float(
                            leg.get("entry_price")
                        ),
                        "owner_target_price": target_price,
                        "lifecycle_stage": "entry",
                        "anchor_role": "episode_signal_decision_leg",
                        "entry_timing_decision_anchor_valid": True,
                        "owner_round_trip_cost_pct": _finite_float(
                            (samsung or {}).get("cost_pct")
                        ),
                        "owner_round_trip_cost_provenance": (
                            "samsung_machine_entry_tuning.cost_pct"
                        ),
                        "owner_outcome": owner_outcome,
                        "owner_lifecycle_contract_valid": True,
                        "owner_policy_tuning_eligible": owner_row_eligible,
                        "owner_timing_custody_observation_eligible": (
                            held_inventory_only_gap
                        ),
                        "owner_source_quality": payload.get("source_quality"),
                        "actual_order_submitted": True,
                    }
                )
                emitted_decision_anchor = True
            if lifecycle_invalid:
                row["owner_anchor_contract_status"] = "invalid"
                row["owner_policy_tuning_eligible"] = False
                for anchor in anchors:
                    if anchor.get("lifecycle_id") == lifecycle_id:
                        anchor["owner_lifecycle_contract_valid"] = False
                        anchor["owner_policy_tuning_eligible"] = False
            elif emitted_decision_anchor:
                row["owner_anchor_contract_status"] = "valid"
            else:
                row["owner_policy_tuning_eligible"] = False
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "broker_confirmed_buy_fill_missing"
                )

    prior_reconciliations = (tuning or {}).get("prior_state_reconciliations") or {}
    if isinstance(prior_reconciliations, dict):
        for profile_id, reconciliation in prior_reconciliations.items():
            if not isinstance(reconciliation, dict):
                continue
            payload = reconciliation.get("row") or {}
            if not isinstance(payload, dict) or payload.get("attempted") is not True:
                continue
            profile_id = str(profile_id)
            source_date = str(
                reconciliation.get("source_date") or payload.get("target_date") or ""
            )
            row = profiles.setdefault(profile_id, {})
            registered_profile = PROFILES.get(profile_id)
            owner_identity_valid = bool(
                registered_profile is not None
                and payload.get("symbol") == registered_profile.symbol
                and payload.get("session") == registered_profile.session
            )
            reconciliation_policy_eligible = bool(
                payload.get("eligible_for_tuning") is True
                and payload.get("source_quality") == "pass"
            )
            reconciliation_reasons = {
                str(reason) for reason in payload.get("source_quality_reasons") or []
            }
            reconciliation_held_only_gap = bool(
                payload.get("source_quality") == "gap"
                and reconciliation_reasons == {"held_or_unresolved_inventory"}
            )
            row.update(
                {
                    "profile_id": profile_id,
                    "symbol": str(
                        registered_profile.symbol
                        if registered_profile is not None
                        else ""
                    ),
                    "session": (
                        registered_profile.session
                        if registered_profile is not None
                        else None
                    ),
                    "scope": (
                        "active_episode_owner"
                        if registered_profile is not None
                        else "invalid_episode_owner_identity"
                    ),
                    "expected_venues": (
                        ["SOR"] if registered_profile is not None else []
                    ),
                    "owner_inventory_source": "target_date_prior_state_reconciliation",
                    "owner_source_quality": payload.get("source_quality"),
                    "attempted": True,
                    "owner_policy_tuning_eligible": False,
                    "owner_anchor_contract_status": "not_applicable_no_current_exit",
                }
            )
            gaps = row.setdefault("lifecycle_instrumentation_gaps", [])
            if not owner_identity_valid:
                row["owner_anchor_contract_status"] = "invalid"
                gaps.append("owner_profile_identity_contract_invalid")
                continue
            try:
                source_day = date.fromisoformat(source_date)
            except ValueError:
                source_day = None
            if not (
                source_day is not None
                and payload.get("target_date") == source_date
                and source_day >= CLEAN_BASELINE_DATE
                and source_day < date.fromisoformat(target_date)
                and is_krx_trading_day(source_day)
            ):
                row["owner_anchor_contract_status"] = "invalid"
                gaps.append("prior_reconciliation_source_date_contract_invalid")
                continue
            signal_at, _ = _signal_anchor(payload)
            if (
                signal_at is None
                or signal_at.astimezone(KST).date().isoformat() != source_date
            ):
                row["owner_anchor_contract_status"] = "invalid"
                gaps.append("prior_reconciliation_signal_contract_invalid")
                continue
            if not (reconciliation_policy_eligible or reconciliation_held_only_gap):
                row["owner_anchor_contract_status"] = "invalid"
                gaps.append(
                    "prior_reconciliation_source_quality_not_diagnostic_eligible"
                )
                continue
            row["owner_policy_tuning_eligible"] = reconciliation_policy_eligible
            lifecycle_id = f"episode:{profile_id}:{signal_at.isoformat()}"
            emitted_exit = False
            invalid_exit = False
            for leg_index, leg in enumerate(payload.get("legs") or [], start=1):
                if not isinstance(leg, dict):
                    continue
                target_filled_at = _owner_ts_on_target_date(
                    leg.get("target_filled_at"), target_date
                )
                if target_filled_at is None:
                    continue
                leg_id = str(leg.get("leg_id") or leg_index)
                buy_filled_at = _parse_owner_ts(leg.get("buy_filled_at"))
                buy_filled_qty_value = _finite_float(leg.get("buy_filled_qty"))
                target_filled_qty_value = _finite_float(leg.get("target_filled_qty"))
                target_fill_price = _finite_float(leg.get("target_fill_price"))
                valid_exit = bool(
                    buy_filled_at is not None
                    and buy_filled_at >= signal_at
                    and target_filled_at >= buy_filled_at
                    and buy_filled_qty_value is not None
                    and buy_filled_qty_value > 0
                    and buy_filled_qty_value.is_integer()
                    and target_filled_qty_value is not None
                    and target_filled_qty_value > 0
                    and target_filled_qty_value.is_integer()
                    and target_filled_qty_value <= buy_filled_qty_value
                    and target_fill_price is not None
                    and target_fill_price > 0
                )
                if not valid_exit:
                    invalid_exit = True
                    gaps.append(f"{leg_id}:reconciled_target_fill_contract_invalid")
                    continue
                realized = bool(
                    leg.get("completed") is True
                    and target_filled_qty_value == buy_filled_qty_value
                )
                exit_provenance = _episode_exit_outcome_provenance(
                    leg, realized=realized
                )
                target_anchor_role = _episode_exit_anchor_role(
                    realized=realized,
                    exit_execution_class=str(exit_provenance["exit_execution_class"]),
                    reconciled=True,
                )
                anchors.append(
                    {
                        "anchor_id": f"{lifecycle_id}:{leg_id}:reconciled_target_fill",
                        "lifecycle_id": lifecycle_id,
                        "owner": "episode",
                        "scope_id": profile_id,
                        "symbol": row["symbol"],
                        "session": row["session"],
                        "expected_venues": ["SOR"],
                        "expected_session_buckets": ["SOR_REGULAR"],
                        "anchor_at": target_filled_at.isoformat(),
                        "anchor_price": target_fill_price,
                        "owner_target_price": None,
                        "lifecycle_stage": (
                            "exit" if realized else "exit_partial_fill"
                        ),
                        "anchor_role": target_anchor_role,
                        "owner_round_trip_cost_pct": episode_round_trip_cost_pct,
                        "owner_round_trip_cost_provenance": (
                            episode_round_trip_cost_provenance
                        ),
                        "owner_original_source_date": source_date,
                        "owner_outcome": {
                            "leg_id": leg_id,
                            "buy_filled_at": buy_filled_at.isoformat(),
                            "holding_duration_ms": round(
                                (target_filled_at - buy_filled_at).total_seconds()
                                * 1000.0
                            ),
                            "gross_no_slippage_return_pct": _finite_float(
                                leg.get("gross_no_slippage_return_pct")
                            ),
                            "cost_aware_net_return_pct": _finite_float(
                                leg.get("net_profit_pct")
                            ),
                            "entry_notional_krw": (
                                (_finite_float(leg.get("fill_price")) or 0.0)
                                * int(buy_filled_qty_value)
                            ),
                            "quantity": int(buy_filled_qty_value),
                            "quantity_basis": "broker_confirmed_fill",
                            "realized": realized,
                            **exit_provenance,
                        },
                        "owner_lifecycle_contract_valid": True,
                        "owner_policy_tuning_eligible": row[
                            "owner_policy_tuning_eligible"
                        ],
                        "owner_source_quality": payload.get("source_quality"),
                        "actual_order_submitted": True,
                    }
                )
                emitted_exit = True
            if invalid_exit:
                row["owner_anchor_contract_status"] = "invalid"
                row["owner_policy_tuning_eligible"] = False
                for anchor in anchors:
                    if anchor.get("lifecycle_id") == lifecycle_id:
                        anchor["owner_lifecycle_contract_valid"] = False
                        anchor["owner_policy_tuning_eligible"] = False
            elif emitted_exit:
                row["owner_anchor_contract_status"] = "valid"

    expanded_profiles = (expansion or {}).get("profiles") or {}
    if isinstance(expanded_profiles, dict):
        for profile_id, payload in expanded_profiles.items():
            if not isinstance(payload, dict):
                continue
            profile_id = str(payload.get("profile_id") or profile_id)
            if profile_id in profiles:
                continue
            row = {
                "profile_id": profile_id,
                "symbol": str(payload.get("symbol") or ""),
                "name": payload.get("name"),
                "session": payload.get("session"),
                "scope": "prospective_episode_research",
                "expected_venues": ["SOR"],
                "discovery_lane": payload.get("discovery_lane"),
                "owner_inventory_source": "target_date_postclose_report",
                "owner_anchor_contract_status": "not_applicable_no_target_date_episode",
                "lifecycle_instrumentation_gaps": [],
            }
            profiles[profile_id] = row
            selected = payload.get("selected") or {}
            full = selected.get("full") or {} if isinstance(selected, dict) else {}
            episodes = full.get("episodes") if isinstance(full, dict) else []
            if episodes is None:
                episodes = []
            if not isinstance(episodes, list):
                row["owner_anchor_contract_status"] = "invalid"
                row["lifecycle_instrumentation_gaps"].append(
                    "selected_full_episodes_invalid"
                )
                continue
            target_episodes = [
                episode
                for episode in episodes
                if isinstance(episode, dict) and episode.get("date") == target_date
            ]
            valid_target_episode_count = 0
            invalid_target_episode_count = 0
            for episode_index, episode in enumerate(target_episodes, start=1):
                raw_signal_at = _parse_owner_ts(episode.get("signal_at"))
                signal_at = _owner_ts_on_target_date(
                    episode.get("signal_at"), target_date
                )
                signal_close = _finite_float(episode.get("signal_close"))
                if signal_at is None or signal_close is None or signal_close <= 0:
                    invalid_target_episode_count += 1
                    reason = (
                        f"episode_{episode_index}:signal_timestamp_or_price_invalid"
                    )
                    if raw_signal_at is not None and signal_at is None:
                        reason = f"episode_{episode_index}:signal_outside_target_date"
                    row["lifecycle_instrumentation_gaps"].append(reason)
                    continue
                valid_target_episode_count += 1
                lifecycle_invalid = False
                lifecycle_id = (
                    f"episode_research:{profile_id}:{episode_index}:"
                    f"{signal_at.isoformat()}"
                )
                legs = episode.get("legs") or []
                owner_target_prices = [
                    value
                    for leg in legs
                    if isinstance(leg, dict)
                    and (value := _finite_float(leg.get("target_price"))) is not None
                    and value > 0
                ]
                common_anchor = {
                    "lifecycle_id": lifecycle_id,
                    "owner": "episode",
                    "scope_id": profile_id,
                    "symbol": row["symbol"],
                    "session": row["session"],
                    "expected_venues": ["SOR"],
                    "expected_session_buckets": ["SOR_REGULAR"],
                    "actual_order_submitted": False,
                    "owner_lifecycle_contract_valid": True,
                    "owner_round_trip_cost_pct": (
                        prospective_episode_round_trip_cost_pct
                    ),
                    "owner_round_trip_cost_provenance": (
                        prospective_episode_round_trip_cost_provenance
                    ),
                }
                anchors.append(
                    {
                        **common_anchor,
                        "anchor_id": f"{lifecycle_id}:signal",
                        "anchor_at": signal_at.isoformat(),
                        "anchor_price": signal_close,
                        "owner_target_price": (
                            min(owner_target_prices) if owner_target_prices else None
                        ),
                        "lifecycle_stage": "entry",
                        "anchor_role": "prospective_episode_research_signal",
                    }
                )
                if not isinstance(legs, list):
                    invalid_target_episode_count += 1
                    row["lifecycle_instrumentation_gaps"].append(
                        f"episode_{episode_index}:legs_invalid"
                    )
                    for anchor in anchors:
                        if anchor.get("lifecycle_id") == lifecycle_id:
                            anchor["owner_lifecycle_contract_valid"] = False
                    continue
                for leg_index, leg in enumerate(legs, start=1):
                    if not isinstance(leg, dict):
                        lifecycle_invalid = True
                        row["lifecycle_instrumentation_gaps"].append(
                            f"episode_{episode_index}:leg_{leg_index}_invalid"
                        )
                        continue
                    entry_price = _finite_float(leg.get("entry_price"))
                    raw_fill_at = _parse_owner_ts(leg.get("fill_at"))
                    fill_at = _owner_ts_on_target_date(leg.get("fill_at"), target_date)
                    raw_target_at = _parse_owner_ts(leg.get("target_at"))
                    target_at = _owner_ts_on_target_date(
                        leg.get("target_at"), target_date
                    )
                    target_price = _finite_float(leg.get("target_price"))
                    status = str(leg.get("status") or "")
                    if fill_at is None:
                        if status not in {"NO_FILL", ""}:
                            lifecycle_invalid = True
                            reason = f"episode_{episode_index}:leg_{leg_index}_fill_timestamp_missing"
                            if raw_fill_at is not None:
                                reason = f"episode_{episode_index}:leg_{leg_index}_fill_outside_target_date"
                            row["lifecycle_instrumentation_gaps"].append(reason)
                        continue
                    if fill_at < signal_at:
                        lifecycle_invalid = True
                        row["lifecycle_instrumentation_gaps"].append(
                            f"episode_{episode_index}:leg_{leg_index}_fill_before_signal"
                        )
                        continue
                    if entry_price is None or entry_price <= 0:
                        lifecycle_invalid = True
                        row["lifecycle_instrumentation_gaps"].append(
                            f"episode_{episode_index}:leg_{leg_index}_entry_price_invalid"
                        )
                        continue
                    holding_duration_ms = (
                        round((target_at - fill_at).total_seconds() * 1000.0)
                        if target_at is not None and target_at >= fill_at
                        else None
                    )
                    completed = status == "COMPLETE"
                    target_valid = bool(
                        completed
                        and target_at is not None
                        and target_at >= fill_at
                        and target_price is not None
                        and target_price > 0
                    )
                    if completed and not target_valid:
                        lifecycle_invalid = True
                        reason = f"episode_{episode_index}:leg_{leg_index}_target_timestamp_or_price_invalid"
                        if raw_target_at is not None and target_at is None:
                            reason = f"episode_{episode_index}:leg_{leg_index}_target_outside_target_date"
                        elif target_at is not None and target_at < fill_at:
                            reason = f"episode_{episode_index}:leg_{leg_index}_target_before_fill"
                        row["lifecycle_instrumentation_gaps"].append(reason)
                    gross_return = (
                        round((target_price / entry_price - 1.0) * 100.0, 6)
                        if target_valid
                        else None
                    )
                    owner_outcome = {
                        "leg_id": str(leg_index),
                        "holding_duration_ms": holding_duration_ms,
                        "gross_no_slippage_return_pct": gross_return,
                        "cost_aware_net_return_pct": _finite_float(
                            leg.get("net_profit_pct")
                        ),
                        "entry_notional_krw": entry_price,
                        "quantity_basis": "one_share_normalized_source_only",
                        "realized": target_valid,
                    }
                    anchors.append(
                        {
                            **common_anchor,
                            "anchor_id": f"{lifecycle_id}:leg_{leg_index}:fill",
                            "anchor_at": fill_at.isoformat(),
                            "anchor_price": entry_price,
                            "owner_target_price": target_price,
                            "lifecycle_stage": "entry",
                            "anchor_role": "prospective_episode_research_buy_fill",
                            "owner_outcome": owner_outcome,
                        }
                    )
                    if target_valid:
                        anchors.append(
                            {
                                **common_anchor,
                                "anchor_id": (f"{lifecycle_id}:leg_{leg_index}:target"),
                                "anchor_at": target_at.isoformat(),
                                "anchor_price": target_price,
                                "owner_target_price": None,
                                "lifecycle_stage": "exit",
                                "anchor_role": (
                                    "prospective_episode_research_target_fill"
                                ),
                                "owner_outcome": owner_outcome,
                            }
                        )
                if lifecycle_invalid:
                    invalid_target_episode_count += 1
                    for anchor in anchors:
                        if anchor.get("lifecycle_id") == lifecycle_id:
                            anchor["owner_lifecycle_contract_valid"] = False
            if target_episodes:
                row["owner_anchor_contract_status"] = (
                    "valid"
                    if valid_target_episode_count and not invalid_target_episode_count
                    else "invalid"
                )

    candidate_symbols = (expansion or {}).get("candidate_symbols") or {}
    if isinstance(candidate_symbols, dict):
        known = {str(row.get("symbol")) for row in profiles.values()}
        for symbol, name in candidate_symbols.items():
            symbol = str(symbol)
            if symbol in known:
                continue
            profile_id = f"prospective_symbol:{symbol}"
            profiles[profile_id] = {
                "profile_id": profile_id,
                "symbol": symbol,
                "name": name,
                "session": None,
                "scope": "prospective_episode_symbol",
                "expected_venues": ["SOR"],
                "owner_inventory_source": "target_date_postclose_report",
            }

    return (
        profiles,
        anchors,
        {
            "tuning": _source(
                tuning_path,
                tuning,
                target_date=target_date,
                expected_schemas=tuning_schemas,
            ),
            "expanded_candidate_research": _source(
                expansion_path,
                expansion,
                target_date=target_date,
                expected_schemas=expansion_schemas,
            ),
            "samsung_machine_entry_tuning": _source(
                samsung_path,
                samsung,
                target_date=target_date,
                expected_schemas=samsung_schemas,
            ),
        },
    )


def _partition_stream_files(
    partition: Path, logical_name: str
) -> tuple[list[tuple[Path, str, str]], list[str]]:
    paths: list[tuple[Path, str, str]] = []
    errors: list[str] = []
    for session_dir in sorted(partition.glob("venue=*/session=*")):
        venue = session_dir.parent.name.partition("=")[2]
        session = session_dir.name.partition("=")[2]
        if not venue or not session:
            errors.append(f"{session_dir}:invalid_partition_scope")
            continue
        base = session_dir / logical_name
        try:
            discovered = readable_partition_path_files(base)
        except ValueError as exc:
            errors.append(f"{base}:{exc}")
            continue
        paths.extend((path, venue, session) for path in discovered)
    return paths, errors


def _iter_relevant_rows(
    paths: Iterable[tuple[Path, str, str]],
    symbols: set[str],
    *,
    diagnostics: dict[str, int] | None = None,
) -> Iterable[dict[str, Any]]:
    for path, partition_venue, partition_session in paths:
        try:
            opener = gzip.open if path.suffix == ".gz" else Path.open
            with opener(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    key_at = line.find('"symbol"')
                    colon_at = line.find(":", key_at + 8) if key_at >= 0 else -1
                    quote_at = line.find('"', colon_at + 1) if colon_at >= 0 else -1
                    quote_end = line.find('"', quote_at + 1) if quote_at >= 0 else -1
                    if quote_end < 0 or line[quote_at + 1 : quote_end] not in symbols:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        if diagnostics is not None:
                            diagnostics["malformed_relevant_json_line_count"] = (
                                diagnostics.get("malformed_relevant_json_line_count", 0)
                                + 1
                            )
                        continue
                    if (
                        isinstance(payload, dict)
                        and str(payload.get("symbol")) in symbols
                    ):
                        row = dict(payload)
                        row["_partition_venue"] = partition_venue
                        row["_partition_session_bucket"] = partition_session
                        yield row
        except OSError:
            if diagnostics is not None:
                diagnostics["source_file_read_error_count"] = (
                    diagnostics.get("source_file_read_error_count", 0) + 1
                )
            continue


def _scope_contract_key(payload: dict[str, Any]) -> str:
    return (
        f"{str(payload.get('venue') or 'unknown')}|"
        f"{str(payload.get('session_bucket') or 'unknown')}"
    )


def _physical_scope_contract_key(payload: dict[str, Any]) -> str:
    return (
        f"{str(payload.get('_partition_venue') or 'unknown')}|"
        f"{str(payload.get('_partition_session_bucket') or 'unknown')}"
    )


def _physical_scope_matches_row(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("venue") == payload.get("_partition_venue")
        and payload.get("session_bucket") == payload.get("_partition_session_bucket")
    )


def _depth_item_matches_scope(payload: dict[str, Any]) -> bool:
    symbol = str(payload.get("symbol") or "").strip()
    venue = str(payload.get("venue") or "").strip().upper()
    expected_item = (
        symbol
        if venue == "KRX"
        else (
            f"{symbol}_NX"
            if venue == "NXT"
            else f"{symbol}_AL" if venue == "SOR" else ""
        )
    )
    return bool(symbol and expected_item and payload.get("item") == expected_item)


def _validate_stream_row(
    payload: dict[str, Any],
) -> tuple[bool, bool, datetime | None, float | None, float | None, float | None]:
    schema = payload.get("schema")
    timestamp = _parse_owner_ts(
        payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
    )
    price = _finite_float(payload.get("trade_price"))
    best_bid = _finite_float(payload.get("best_bid"))
    best_ask = _finite_float(payload.get("best_ask"))
    authority_valid = bool(
        payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("trading_runtime_effect") is False
    )
    path_consumer_eligible = payload.get("path_consumer_eligible") is not False
    basic_valid = bool(
        schema
        in {
            "scalp_micro_reversion_market_stream_point_v1",
            "scalp_micro_reversion_market_stream_point_v2",
            "scalp_micro_reversion_market_stream_point_v3",
        }
        and authority_valid
        and timestamp is not None
        and price is not None
        and price > 0
        and (best_bid is None or best_bid > 0)
        and (best_ask is None or best_ask > 0)
        and not (best_bid is not None and best_ask is not None and best_ask < best_bid)
    )
    if basic_valid and schema == "scalp_micro_reversion_market_stream_point_v3":
        try:
            if payload.get("metric_contract_id") != MARKET_STREAM_CONTRACT_ID:
                raise ValueError("unexpected canonical stream metric contract")
            MarketStreamPoint(
                symbol=str(payload.get("symbol") or ""),
                exchange_timestamp=payload.get("exchange_timestamp"),
                local_receive_timestamp=payload.get("local_receive_timestamp"),
                source_sequence=payload.get("source_sequence"),
                sequence_epoch=payload.get("sequence_epoch"),
                series_sequence=payload.get("series_sequence"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                realtime_type=payload.get("realtime_type"),
                trade_price=price,
                trade_qty=payload.get("trade_qty"),
                best_bid=best_bid,
                best_ask=best_ask,
                bid_depth=payload.get("bid_depth"),
                ask_depth=payload.get("ask_depth"),
                quote_age_ms=payload.get("quote_age_ms"),
                aggressor_side=payload.get("aggressor_side") or "UNKNOWN",
                path_order_status=payload.get("path_order_status"),
                path_consumer_eligible=payload.get("path_consumer_eligible"),
                exchange_timestamp_regression_ms=payload.get(
                    "exchange_timestamp_regression_ms"
                ),
                schema=payload.get("schema"),
            )
        except (TypeError, ValueError):
            basic_valid = False
            path_consumer_eligible = False
    # V1/V2 are archive compatibility rows. They predate the V3 ordering
    # provenance fields, so only the shared strict timestamp/price/authority
    # contract applies and they can never claim V3 path-order validation.
    return (
        basic_valid,
        path_consumer_eligible,
        timestamp,
        price,
        best_bid,
        best_ask,
    )


def _validate_depth_row(
    payload: dict[str, Any],
) -> tuple[
    bool, datetime | None, float | None, float | None, float | None, float | None
]:
    timestamp = _parse_owner_ts(
        payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
    )
    bid_depth = _finite_float(payload.get("bid_depth"))
    ask_depth = _finite_float(payload.get("ask_depth"))
    best_bid = _finite_float(payload.get("best_bid"))
    best_ask = _finite_float(payload.get("best_ask"))
    valid = bool(
        payload.get("schema") == "scalp_micro_reversion_market_depth_point_v1"
        and payload.get("trading_runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and timestamp is not None
        and _depth_item_matches_scope(payload)
    )
    if valid:
        try:
            validate_canonical_depth_row(payload)
            MarketDepthPoint(
                symbol=str(payload.get("symbol") or ""),
                exchange_timestamp=payload.get("exchange_timestamp"),
                local_receive_timestamp=payload.get("local_receive_timestamp"),
                source_sequence=payload.get("source_sequence"),
                sequence_epoch=payload.get("sequence_epoch"),
                series_sequence=payload.get("series_sequence"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                item=payload.get("item"),
                orderbook_time_raw=payload.get("orderbook_time_raw"),
                best_bid=best_bid,
                best_ask=best_ask,
                best_bid_qty=payload.get("best_bid_qty"),
                best_ask_qty=payload.get("best_ask_qty"),
                bid_depth=payload.get("bid_depth"),
                ask_depth=payload.get("ask_depth"),
                bid_levels=payload.get("bid_levels"),
                ask_levels=payload.get("ask_levels"),
                route_depth_totals=payload.get("route_depth_totals"),
                realtime_type=payload.get("realtime_type"),
                schema=payload.get("schema"),
            )
        except (TypeError, ValueError):
            valid = False
    return valid, timestamp, bid_depth, ask_depth, best_bid, best_ask


def _validate_reference_row(
    payload: dict[str, Any], target_date: str
) -> tuple[bool, datetime | None]:
    valid = bool(
        payload.get("schema") == "scalp_micro_reversion_path_event_reference_v2"
        and payload.get("trading_runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and not isinstance(payload.get("event_detected_at_ms"), bool)
    )
    if valid:
        try:
            reference = PathEventReference(
                parent_wave_id=payload.get("parent_wave_id"),
                path_segment_id=payload.get("path_segment_id"),
                shock_event_id=payload.get("shock_event_id"),
                shock_horizon_ms=payload.get("shock_horizon_ms"),
                event_sequence_in_wave=payload.get("event_sequence_in_wave"),
                event_detected_at_ms=payload.get("event_detected_at_ms"),
                symbol=payload.get("symbol"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                sequence_epoch=payload.get("sequence_epoch"),
                capture_started_at=payload.get("capture_started_at"),
                segment_event_detected_at_ms=payload.get(
                    "segment_event_detected_at_ms"
                ),
                capture_ended_at=payload.get("capture_ended_at"),
                schema=payload.get("schema"),
            )
            timestamp = datetime.fromtimestamp(
                reference.event_detected_at_ms / 1000.0, tz=timezone.utc
            )
        except (OSError, OverflowError, TypeError, ValueError):
            return False, None
        valid = timestamp.astimezone(KST).date().isoformat() == target_date
        return valid, timestamp
    return False, None


def _micro_context(
    target_date: str,
    observation_root: Path,
    symbols: set[str],
    anchors: list[dict[str, Any]],
    source_exclusion_manifest_path: Path,
    canary_snapshot_path: Path | None,
    canary_evaluated_at: datetime,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    partition = observation_root / f"trade_date={target_date}"
    stream_paths, stream_path_errors = _partition_stream_files(
        partition, "market_stream.jsonl"
    )
    depth_paths, depth_path_errors = _partition_stream_files(
        partition, "market_depth_stream.jsonl"
    )
    ref_paths, ref_path_errors = _partition_stream_files(
        partition, "market_stream_event_references.jsonl"
    )
    read_diagnostics: dict[str, int] = {
        "malformed_relevant_json_line_count": 0,
        "source_file_read_error_count": 0,
        "partition_scope_mismatch_row_count": 0,
    }
    try:
        exclusion_manifest = load_source_exclusion_manifest(
            source_exclusion_manifest_path
        )
        excluded_scopes = {
            (
                str(entry["trade_date"]),
                str(entry["venue"]),
                str(entry["session_bucket"]),
                int(entry["sequence_epoch"]),
            )
            for entry in exclusion_manifest.get("exclusions") or []
        }
        exclusion_manifest_status = "loaded"
    except (KeyError, TypeError, ValueError):
        excluded_scopes = set()
        exclusion_manifest_status = "missing_or_invalid"

    canary_status = "not_requested"
    canary_source: dict[str, Any] = {
        "path": str(canary_snapshot_path) if canary_snapshot_path else None,
        "status": canary_status,
    }
    if canary_snapshot_path is not None:
        canary_payload = _read_json(canary_snapshot_path)
        raw_guard = (canary_payload or {}).get("canary_guard")
        raw_collector = (canary_payload or {}).get("collector_snapshot")
        raw_archive_validation = (canary_payload or {}).get("archive_validation")
        guard = raw_guard if isinstance(raw_guard, dict) else {}
        collector = raw_collector if isinstance(raw_collector, dict) else {}
        archive_validation = (
            raw_archive_validation if isinstance(raw_archive_validation, dict) else {}
        )
        generated_at = _parse_owner_ts((canary_payload or {}).get("generated_at"))
        canary_target_date_matches = bool(
            generated_at is not None
            and generated_at.astimezone(KST).date().isoformat() == target_date
        )
        canary_target_day_complete = bool(
            canary_target_date_matches
            and generated_at is not None
            and generated_at.astimezone(KST).time().replace(tzinfo=None)
            >= CANARY_COMPLETE_AFTER_KST
        )
        valid_until_epoch = _finite_float(
            (canary_payload or {}).get("valid_until_epoch")
        )
        archived_at = _parse_owner_ts(
            archive_validation.get("archived_at_kst")
            if isinstance(archive_validation, dict)
            else None
        )
        archived_freshness_valid = bool(
            isinstance(archive_validation, dict)
            and archive_validation.get("schema")
            == "scalp_micro_reversion_canary_archive_validation_v1"
            and archive_validation.get("target_date") == target_date
            and archive_validation.get("target_day_complete") is True
            and archive_validation.get("source_fresh_at_archive") is True
            and archive_validation.get("source_generated_not_after_archive") is True
            and archived_at is not None
            and generated_at is not None
            and generated_at <= archived_at
        )
        generation_causal = bool(
            archived_freshness_valid
            or (generated_at is not None and generated_at <= canary_evaluated_at)
        )
        stopped_clean_closed = bool(
            guard.get("status") == "stopped_clean"
            and isinstance(collector, dict)
            and collector.get("collector_lifecycle") == "closed"
            and collector.get("reference_reconciliation_completed") is True
        )
        live_freshness_valid = bool(
            stopped_clean_closed
            or (
                guard.get("status") == "healthy_observer_canary"
                and valid_until_epoch is not None
                and valid_until_epoch >= canary_evaluated_at.timestamp()
            )
        )
        canary_freshness_valid = archived_freshness_valid or live_freshness_valid
        canary_contract_valid = bool(
            (canary_payload or {}).get("schema")
            == "scalp_micro_reversion_canary_monitor_v1"
            and canary_target_date_matches
            and generation_causal
            and isinstance(guard, dict)
            and guard.get("status") in {"healthy_observer_canary", "stopped_clean"}
            and (
                (
                    guard.get("status") == "healthy_observer_canary"
                    and collector.get("collector_lifecycle") == "running"
                )
                or stopped_clean_closed
            )
            and guard.get("stop_required") is False
            and guard.get("raw_row_exclusion_required") is False
            and isinstance(collector, dict)
            and collector.get("selection_authority") is False
            and collector.get("trading_runtime_effect") is False
            and collector.get("actual_order_submitted") is False
            and collector.get("broker_order_forbidden") is True
        )
        canary_valid = bool(
            canary_contract_valid
            and canary_target_day_complete
            and canary_freshness_valid
        )
        canary_status = (
            "loaded_pass"
            if canary_valid
            else (
                "target_date_evidence_unavailable"
                if canary_payload is None or not canary_target_date_matches
                else (
                    "target_date_evidence_incomplete"
                    if not canary_target_day_complete
                    else (
                        "missing_or_invalid"
                        if not canary_contract_valid
                        else (
                            "target_date_evidence_stale"
                            if not canary_freshness_valid
                            else "missing_or_invalid"
                        )
                    )
                )
            )
        )
        canary_source = {
            "path": str(canary_snapshot_path),
            "status": canary_status,
            "generated_at": (
                generated_at.isoformat() if generated_at is not None else None
            ),
            "target_day_complete": canary_target_day_complete,
            "complete_after_kst": CANARY_COMPLETE_AFTER_KST.isoformat(),
            "fresh_at_evaluation_or_archive": canary_freshness_valid,
            "generated_not_after_evaluation_or_archive": generation_causal,
            "valid_until_epoch": valid_until_epoch,
            "archive_validation": (
                archive_validation if isinstance(archive_validation, dict) else None
            ),
            "stopped_clean_closed": stopped_clean_closed,
            "guard_status": guard.get("status") if isinstance(guard, dict) else None,
            "stop_required": (
                guard.get("stop_required") if isinstance(guard, dict) else None
            ),
            "raw_row_exclusion_required": (
                guard.get("raw_row_exclusion_required")
                if isinstance(guard, dict)
                else None
            ),
            "sequence_epoch": (
                collector.get("sequence_epoch") if isinstance(collector, dict) else None
            ),
            "source_sha256": (
                hashlib.sha256(canary_snapshot_path.read_bytes()).hexdigest()
                if canary_payload is not None
                else None
            ),
        }

    def is_excluded(payload: dict[str, Any]) -> bool:
        try:
            scope = (
                target_date,
                str(payload.get("venue") or ""),
                str(payload.get("session_bucket") or ""),
                int(payload.get("sequence_epoch") or 0),
            )
        except (TypeError, ValueError):
            return False
        return scope in excluded_scopes

    inventory: dict[str, dict[str, Any]] = {
        symbol: {
            "observed_row_count": 0,
            "eligible_row_count": 0,
            "ineligible_row_count": 0,
            "source_excluded_row_count": 0,
            "invalid_contract_row_count": 0,
            "invalid_contract_scope_counts": defaultdict(int),
            "depth_row_count": 0,
            "venues": set(),
            "sessions": set(),
        }
        for symbol in symbols
    }
    windows: dict[str, dict[str, Any]] = {
        anchor["anchor_id"]: {
            "rows": [],
            "raw_market_rows": [],
            "depth_rows": 0,
            "depth_points": [],
            "raw_depth_rows": [],
            "shock_reference_count": 0,
        }
        for anchor in anchors
    }
    anchors_by_symbol: dict[str, list[tuple[dict[str, Any], datetime]]] = defaultdict(
        list
    )
    for anchor in anchors:
        anchor_at = _parse_ts(anchor["anchor_at"])
        if anchor_at is not None:
            anchors_by_symbol[anchor["symbol"]].append((anchor, anchor_at))

    def post_window_sec(anchor: Mapping[str, Any]) -> int:
        return (
            MARKET_WEAKNESS_COUNTERFACTUAL_POST_WINDOW_SEC
            if anchor.get("anchor_role") in _ENTRY_CONFIRMATION_ANCHOR_ROLES
            else POST_WINDOW_SEC
        )

    for payload in _iter_relevant_rows(
        stream_paths, symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        item = inventory[symbol]
        item["observed_row_count"] += 1
        if not _physical_scope_matches_row(payload):
            item["venues"].add(str(payload.get("_partition_venue") or "unknown"))
            item["sessions"].add(
                str(payload.get("_partition_session_bucket") or "unknown")
            )
            item["invalid_contract_row_count"] += 1
            item["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            item["ineligible_row_count"] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        item["venues"].add(str(payload.get("venue") or "unknown"))
        item["sessions"].add(str(payload.get("session_bucket") or "unknown"))
        if is_excluded(payload):
            item["source_excluded_row_count"] += 1
            item["ineligible_row_count"] += 1
            continue
        (
            contract_valid,
            path_consumer_eligible,
            timestamp,
            price,
            best_bid,
            best_ask,
        ) = _validate_stream_row(payload)
        if (
            contract_valid
            and timestamp is not None
            and timestamp.astimezone(KST).date().isoformat() != target_date
        ):
            contract_valid = False
            path_consumer_eligible = False
        eligible = contract_valid and path_consumer_eligible
        if not contract_valid:
            item["invalid_contract_row_count"] += 1
            item["invalid_contract_scope_counts"][_scope_contract_key(payload)] += 1
        item["eligible_row_count" if eligible else "ineligible_row_count"] += 1
        if not eligible:
            continue
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                windows[anchor["anchor_id"]]["rows"].append(
                    {
                        "timestamp": timestamp,
                        "price": price,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "venue": payload.get("venue"),
                        "session": payload.get("session_bucket"),
                        "sequence_epoch": payload.get("sequence_epoch"),
                    }
                )
                windows[anchor["anchor_id"]]["raw_market_rows"].append(dict(payload))

    for payload in _iter_relevant_rows(
        depth_paths, symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        if not _physical_scope_matches_row(payload):
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        (
            valid_depth,
            timestamp,
            bid_depth,
            ask_depth,
            depth_best_bid,
            depth_best_ask,
        ) = _validate_depth_row(payload)
        if (
            valid_depth
            and timestamp is not None
            and timestamp.astimezone(KST).date().isoformat() != target_date
        ):
            valid_depth = False
        if not valid_depth:
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _scope_contract_key(payload)
            ] += 1
            continue
        inventory[symbol]["depth_row_count"] += 1
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                windows[anchor["anchor_id"]]["depth_rows"] += 1
                windows[anchor["anchor_id"]]["depth_points"].append(
                    {
                        "sequence_epoch": int(payload["sequence_epoch"]),
                        "timestamp": timestamp,
                        "best_bid": depth_best_bid,
                        "best_bid_qty": int(payload["best_bid_qty"]),
                        "best_ask": depth_best_ask,
                        "best_ask_qty": int(payload["best_ask_qty"]),
                        "bid_depth": bid_depth,
                        "ask_depth": ask_depth,
                    }
                )
                windows[anchor["anchor_id"]]["raw_depth_rows"].append(dict(payload))

    for payload in _iter_relevant_rows(
        ref_paths, symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        if not _physical_scope_matches_row(payload):
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        valid_reference, timestamp = _validate_reference_row(payload, target_date)
        if not valid_reference or timestamp is None:
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _scope_contract_key(payload)
            ] += 1
            continue
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                windows[anchor["anchor_id"]]["shock_reference_count"] += 1

    for item in inventory.values():
        item["venues"] = sorted(item["venues"])
        item["sessions"] = sorted(item["sessions"])
        item["invalid_contract_scope_counts"] = dict(
            sorted(item["invalid_contract_scope_counts"].items())
        )

    shard_discovery_error_count = (
        len(stream_path_errors) + len(depth_path_errors) + len(ref_path_errors)
    )
    source_contract_ready = bool(
        exclusion_manifest_status == "loaded"
        and canary_status in {"not_requested", "loaded_pass"}
        and shard_discovery_error_count == 0
        and read_diagnostics["malformed_relevant_json_line_count"] == 0
        and read_diagnostics["source_file_read_error_count"] == 0
    )
    return (
        {
            "partition": str(partition),
            "partition_status": "loaded" if stream_paths else "missing",
            "market_stream_file_count": len(stream_paths),
            "market_depth_file_count": len(depth_paths),
            "event_reference_file_count": len(ref_paths),
            "stream_shard_discovery_errors": stream_path_errors,
            "depth_shard_discovery_errors": depth_path_errors,
            "event_reference_shard_discovery_errors": ref_path_errors,
            "shard_discovery_error_count": shard_discovery_error_count,
            **read_diagnostics,
            "source_exclusion_manifest_path": str(source_exclusion_manifest_path),
            "source_exclusion_manifest_status": exclusion_manifest_status,
            "source_exclusion_scope_count": len(excluded_scopes),
            "canary_source_quality": canary_source,
            "source_contract_ready": source_contract_ready,
        },
        inventory,
        windows,
    )


def _invalid_contract_count_for_scope(
    inventory: dict[str, Any],
    *,
    expected_venues: Iterable[str],
    expected_sessions: Iterable[str],
) -> int:
    counts = inventory.get("invalid_contract_scope_counts") or {}
    venues = set(expected_venues)
    sessions = set(expected_sessions)
    total = 0
    for key, raw_count in counts.items():
        venue, _, session = str(key).partition("|")
        if (
            venue == "unknown"
            or session == "unknown"
            or (venue in venues and session in sessions)
        ):
            total += int(raw_count or 0)
    return total


_ENTRY_CONFIRMATION_ANCHOR_ROLES = frozenset(
    {
        "actual_widget_entry_signal",
        "actual_widget_scale_in_signal",
        "actual_widget_daily_cap_blocked_entry_signal",
        "actual_market_weakness_blocked_entry_signal",
        "counterfactual_calibration_entry",
        "prospective_widget_research_entry",
        "episode_signal_decision_leg",
        "episode_signal_bar",
        "prospective_episode_research_signal",
    }
)


def _entry_ask_depletion_feature(
    anchor: dict[str, Any],
    window: dict[str, Any],
    *,
    source_complete: bool,
) -> dict[str, Any] | None:
    if anchor.get("anchor_role") not in _ENTRY_CONFIRMATION_ANCHOR_ROLES:
        return None
    anchor_at = _parse_ts(anchor.get("anchor_at"))
    if anchor_at is None:
        return {
            "source_quality_status": "source_gap",
            "source_gap_reasons": ["decision_anchor_timestamp_invalid"],
        }
    raw_market_rows = [
        dict(row)
        for row in window.get("raw_market_rows") or []
        if isinstance(row, dict)
    ]
    raw_depth_rows = [
        dict(row) for row in window.get("raw_depth_rows") or [] if isinstance(row, dict)
    ]
    event_candidates: list[tuple[datetime, dict[str, Any]]] = []
    for row in raw_market_rows:
        timestamp = _parse_owner_ts(row.get("local_receive_timestamp"))
        if (
            timestamp is not None
            and timestamp >= anchor_at
            and timestamp <= anchor_at + timedelta(seconds=1)
            and row.get("schema") == "scalp_micro_reversion_market_stream_point_v3"
        ):
            event_candidates.append((timestamp, row))
    if not event_candidates:
        return {
            "source_quality_status": "source_gap",
            "source_gap_reasons": ["canonical_0b_market_anchor_within_1s_missing"],
        }
    event_at, event_market = min(event_candidates, key=lambda item: item[0])
    try:
        sequence_epoch = int(event_market["sequence_epoch"])
        market_sequence = int(event_market["source_sequence"])
    except (KeyError, TypeError, ValueError):
        return {
            "source_quality_status": "source_gap",
            "source_gap_reasons": ["canonical_0b_market_anchor_sequence_invalid"],
        }
    scope = (
        str(event_market.get("symbol") or ""),
        str(event_market.get("venue") or ""),
        str(event_market.get("session_bucket") or ""),
        sequence_epoch,
    )
    scoped_depth: list[tuple[datetime, dict[str, Any]]] = []
    for row in raw_depth_rows:
        timestamp = _parse_owner_ts(row.get("local_receive_timestamp"))
        try:
            row_epoch = int(row.get("sequence_epoch"))
        except (TypeError, ValueError):
            continue
        if (
            timestamp is not None
            and (
                str(row.get("symbol") or ""),
                str(row.get("venue") or ""),
                str(row.get("session_bucket") or ""),
                row_epoch,
            )
            == scope
        ):
            scoped_depth.append((timestamp, row))
    anchor_depth_candidates = [item for item in scoped_depth if item[0] < event_at]
    anchor_depth = (
        max(anchor_depth_candidates, key=lambda item: item[0])[1]
        if anchor_depth_candidates
        else None
    )
    scoped_market_times = [
        timestamp
        for row in raw_market_rows
        if (
            (timestamp := _parse_owner_ts(row.get("local_receive_timestamp")))
            is not None
            and str(row.get("symbol") or "") == scope[0]
            and str(row.get("venue") or "") == scope[1]
            and str(row.get("session_bucket") or "") == scope[2]
            and row.get("sequence_epoch") == sequence_epoch
        )
    ]
    observed_through = max(
        [event_at, *scoped_market_times, *(item[0] for item in scoped_depth)]
    )
    context = AskDepletionContext(
        event_id=f"entry_confirmation:{anchor['anchor_id']}:{market_sequence}",
        anchor_role="shock_event",
        symbol=scope[0],
        venue=scope[1],
        session_bucket=scope[2],
        sequence_epoch=sequence_epoch,
        anchor_event_local_receive_timestamp_ms=int(event_at.timestamp() * 1000),
        event_market_source_sequence=market_sequence,
        observed_through_local_receive_timestamp_ms=int(
            observed_through.timestamp() * 1000
        ),
        depth_source_complete=source_complete,
        market_source_complete=source_complete,
    )
    try:
        report = build_ask_depletion_report(
            context=context,
            anchor_depth=anchor_depth,
            depth_rows=[row for _, row in scoped_depth],
            market_rows=raw_market_rows,
            horizons_ms=(1_000, 3_000, 5_000),
            top_depth_levels=(3, 5),
            max_depth_age_ms=1_000,
        ).as_dict()
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "source_quality_status": "source_gap",
            "source_gap_reasons": [
                f"ask_depletion_contract_error:{type(exc).__name__}:{exc}"
            ],
        }
    report["decision_anchor_binding"] = {
        "decision_anchor_id": anchor["anchor_id"],
        "decision_anchor_at": anchor_at.isoformat(),
        "market_anchor_at": event_at.isoformat(),
        "market_anchor_offset_ms": round(
            (event_at - anchor_at).total_seconds() * 1000.0
        ),
        "binding_policy": "first_canonical_0b_at_or_after_decision_within_1s",
    }
    return report


def _anchor_result(
    anchor: dict[str, Any],
    symbol_inventory: dict[str, Any],
    window: dict[str, Any],
    *,
    partition_loaded: bool,
    source_contract_gap: str | None,
    clean_baseline_allowed: bool,
) -> dict[str, Any]:
    rows = sorted(window["rows"], key=lambda row: row["timestamp"])
    depth_points_by_epoch: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for point in window.get("depth_points") or []:
        if not isinstance(point, dict):
            continue
        depth_points_by_epoch[int(point["sequence_epoch"])].append(point)
    for points in depth_points_by_epoch.values():
        points.sort(key=lambda point: point["timestamp"])
    anchor_at = _parse_ts(anchor["anchor_at"])
    post = [
        row for row in rows if anchor_at is not None and row["timestamp"] >= anchor_at
    ]
    if not clean_baseline_allowed:
        status = "pre_clean_baseline_archive_only"
    elif not partition_loaded:
        status = "micro_date_partition_missing"
    elif source_contract_gap is not None:
        status = source_contract_gap
    elif anchor.get("owner_lifecycle_contract_valid") is False:
        status = "owner_anchor_contract_invalid"
    elif _invalid_contract_count_for_scope(
        symbol_inventory,
        expected_venues=anchor.get("expected_venues") or (),
        expected_sessions=anchor.get("expected_session_buckets") or (),
    ):
        status = "micro_scope_source_contract_invalid"
    elif symbol_inventory["observed_row_count"] == 0:
        status = "micro_symbol_not_observed"
    elif not rows:
        status = "micro_anchor_window_not_observed"
    elif not post:
        status = "micro_post_anchor_not_observed"
    else:
        status = "matched"
    reference = _finite_float(anchor.get("anchor_price"))
    if (reference is None or reference <= 0) and post:
        reference = post[0]["price"]
    bbo_complete_count = sum(
        row["best_bid"] is not None and row["best_ask"] is not None for row in rows
    )

    def depth_context_present(row: dict[str, Any]) -> bool:
        try:
            sequence_epoch = int(row.get("sequence_epoch"))
        except (TypeError, ValueError):
            return False
        depth_points = depth_points_by_epoch.get(sequence_epoch) or []
        if not depth_points:
            return False
        timestamp = row["timestamp"]
        depth_timestamps = [point["timestamp"] for point in depth_points]
        index = bisect_right(depth_timestamps, timestamp) - 1
        if index < 0:
            return False
        age_sec = (timestamp - depth_timestamps[index]).total_seconds()
        return 0.0 <= age_sec <= DEPTH_CONTEXT_MAX_AGE_SEC

    def fillable_depth_context(row: dict[str, Any]) -> dict[str, Any] | None:
        try:
            sequence_epoch = int(row.get("sequence_epoch"))
        except (TypeError, ValueError):
            return None
        depth_points = depth_points_by_epoch.get(sequence_epoch) or []
        if not depth_points:
            return None
        timestamps = [point["timestamp"] for point in depth_points]
        index = bisect_right(timestamps, row["timestamp"]) - 1
        if index < 0:
            return None
        point = depth_points[index]
        age_sec = (row["timestamp"] - point["timestamp"]).total_seconds()
        if not 0.0 <= age_sec <= DEPTH_CONTEXT_MAX_AGE_SEC:
            return None
        if point.get("best_bid") != row.get("best_bid"):
            return None
        return point

    outcome = anchor.get("owner_outcome")
    required_exit_quantity = (
        _finite_float(outcome.get("quantity")) if isinstance(outcome, dict) else None
    )
    if required_exit_quantity is None:
        required_exit_quantity = _finite_float(anchor.get("owner_requested_quantity"))
    if (
        required_exit_quantity is None
        and isinstance(outcome, dict)
        and str(outcome.get("quantity_basis") or "").startswith("one_share_normalized")
    ):
        required_exit_quantity = 1.0

    depth_context_count = sum(depth_context_present(row) for row in rows)
    metrics: dict[str, Any] = {
        "eligible_window_row_count": len(rows),
        "post_anchor_row_count": len(post),
        "depth_window_row_count": window["depth_rows"],
        "shock_reference_count": window["shock_reference_count"],
        "bbo_complete_row_count": bbo_complete_count,
        "bbo_complete_rate_pct": (
            round(bbo_complete_count / len(rows) * 100.0, 6) if rows else None
        ),
        "depth_context_max_age_sec": DEPTH_CONTEXT_MAX_AGE_SEC,
        "depth_context_covered_row_count": depth_context_count,
        "depth_window_coverage_pct": (
            round(depth_context_count / len(rows) * 100.0, 6) if rows else None
        ),
        "reference_price": reference,
        "mfe_bps": None,
        "mae_bps": None,
        "terminal_return_bps": None,
        "time_to_low_ms": None,
        "time_to_high_ms": None,
        "time_to_first_positive_trade_ms": None,
        "owner_target_touched": None,
        "time_to_owner_target_ms": None,
        "fillable_owner_target_touch": {
            "touched": None,
            "time_ms": None,
            "gross_return_bps": None,
            "required_exit_quantity": required_exit_quantity,
            "available_best_bid_quantity": None,
            "depth_backed": None,
        },
        "fillable_bid_exit_horizons": {
            str(horizon): {
                "observed": None,
                "bid_price": None,
                "gross_return_bps": None,
                "observation_offset_ms": None,
                "quote_age_from_horizon_ms": None,
                "required_exit_quantity": required_exit_quantity,
                "available_best_bid_quantity": None,
                "depth_backed": None,
            }
            for horizon in TIMEOUT_RESEARCH_HORIZONS_SEC
        },
        "entry_confirmation_bbo_horizons": {
            str(horizon): {
                "observed": None,
                "best_bid": None,
                "best_ask": None,
                "bid_return_bps": None,
                "ask_return_bps": None,
                "spread_bps": None,
                "observation_offset_ms": None,
                "quote_age_from_horizon_ms": None,
            }
            for horizon in ENTRY_CONFIRMATION_HORIZONS_SEC
        },
        "market_weakness_counterfactual": None,
        "gross_no_slippage_profit_touch": {
            str(threshold): {"touched": None, "time_ms": None}
            for threshold in GROSS_PROFIT_TOUCH_BPS
        },
    }
    if post and reference is not None and reference > 0:
        high = max(post, key=lambda row: row["price"])
        low = min(post, key=lambda row: row["price"])
        first_positive = next((row for row in post if row["price"] > reference), None)
        owner_target = _finite_float(anchor.get("owner_target_price"))
        owner_target_hit = (
            next(
                (row for row in post if row["price"] >= owner_target),
                None,
            )
            if anchor.get("lifecycle_stage") == "entry"
            and owner_target is not None
            and owner_target > reference
            else None
        )
        fillable_owner_target_hit = (
            next(
                (
                    row
                    for row in post
                    if row.get("best_bid") is not None
                    and row["best_bid"] >= owner_target
                    and required_exit_quantity is not None
                    and (
                        (depth_point := fillable_depth_context(row)) is not None
                        and int(depth_point["best_bid_qty"]) >= required_exit_quantity
                    )
                ),
                None,
            )
            if anchor.get("lifecycle_stage") == "entry"
            and owner_target is not None
            and owner_target > reference
            else None
        )
        fillable_bid_exit_horizons: dict[str, dict[str, Any]] = {}
        for horizon_sec in TIMEOUT_RESEARCH_HORIZONS_SEC:
            deadline = (
                anchor_at + timedelta(seconds=horizon_sec)
                if anchor_at is not None
                else None
            )
            eligible_bid_rows = (
                [
                    row
                    for row in post
                    if deadline is not None
                    and row["timestamp"] <= deadline
                    and row.get("best_bid") is not None
                ]
                if anchor.get("lifecycle_stage") == "entry"
                else []
            )
            horizon_row = eligible_bid_rows[-1] if eligible_bid_rows else None
            quote_age_ms = (
                round((deadline - horizon_row["timestamp"]).total_seconds() * 1000.0)
                if deadline is not None and horizon_row is not None
                else None
            )
            observed = bool(
                horizon_row is not None
                and quote_age_ms is not None
                and 0 <= quote_age_ms <= TIMEOUT_RESEARCH_MAX_QUOTE_AGE_SEC * 1000
            )
            horizon_depth = (
                fillable_depth_context(horizon_row)
                if observed and horizon_row is not None
                else None
            )
            depth_backed = bool(
                horizon_depth is not None
                and required_exit_quantity is not None
                and int(horizon_depth["best_bid_qty"]) >= required_exit_quantity
            )
            observed = bool(observed and depth_backed)
            fillable_bid_exit_horizons[str(horizon_sec)] = {
                "observed": observed,
                "bid_price": (
                    round(float(horizon_row["best_bid"]), 6) if observed else None
                ),
                "gross_return_bps": (
                    round(
                        (float(horizon_row["best_bid"]) / reference - 1.0) * 10000.0,
                        6,
                    )
                    if observed
                    else None
                ),
                "observation_offset_ms": (
                    round(
                        (horizon_row["timestamp"] - anchor_at).total_seconds() * 1000.0
                    )
                    if observed and anchor_at is not None
                    else None
                ),
                "quote_age_from_horizon_ms": quote_age_ms if observed else None,
                "required_exit_quantity": required_exit_quantity,
                "available_best_bid_quantity": (
                    int(horizon_depth["best_bid_qty"])
                    if observed and horizon_depth is not None
                    else None
                ),
                "depth_backed": depth_backed,
            }
        entry_confirmation_bbo_horizons: dict[str, dict[str, Any]] = {}
        for horizon_sec in ENTRY_CONFIRMATION_HORIZONS_SEC:
            deadline = (
                anchor_at + timedelta(seconds=horizon_sec)
                if anchor_at is not None
                else None
            )
            eligible_rows = [
                row
                for row in post
                if deadline is not None
                and row["timestamp"] <= deadline
                and row.get("best_bid") is not None
                and row.get("best_ask") is not None
            ]
            horizon_row = eligible_rows[-1] if eligible_rows else None
            quote_age_ms = (
                round((deadline - horizon_row["timestamp"]).total_seconds() * 1000.0)
                if deadline is not None and horizon_row is not None
                else None
            )
            observed = bool(
                anchor.get("anchor_role") in _ENTRY_CONFIRMATION_ANCHOR_ROLES
                and horizon_row is not None
                and quote_age_ms is not None
                and 0 <= quote_age_ms <= ENTRY_CONFIRMATION_MAX_QUOTE_AGE_SEC * 1000
            )
            best_bid = float(horizon_row["best_bid"]) if observed else None
            best_ask = float(horizon_row["best_ask"]) if observed else None
            horizon_depth = (
                fillable_depth_context(horizon_row)
                if observed and horizon_row is not None
                else None
            )
            ask_depth_backed = bool(
                horizon_depth is not None
                and best_ask is not None
                and horizon_depth.get("best_ask") == best_ask
                and required_exit_quantity is not None
                and int(horizon_depth.get("best_ask_qty") or 0)
                >= required_exit_quantity
            )
            entry_confirmation_bbo_horizons[str(horizon_sec)] = {
                "observed": (
                    observed
                    if anchor.get("anchor_role") in _ENTRY_CONFIRMATION_ANCHOR_ROLES
                    else None
                ),
                "best_bid": round(best_bid, 6) if best_bid is not None else None,
                "best_ask": round(best_ask, 6) if best_ask is not None else None,
                "bid_return_bps": (
                    round((best_bid / reference - 1.0) * 10_000.0, 6)
                    if best_bid is not None
                    else None
                ),
                "ask_return_bps": (
                    round((best_ask / reference - 1.0) * 10_000.0, 6)
                    if best_ask is not None
                    else None
                ),
                "spread_bps": (
                    round((best_ask - best_bid) / best_bid * 10_000.0, 6)
                    if best_bid is not None and best_ask is not None and best_bid > 0
                    else None
                ),
                "observation_offset_ms": (
                    round(
                        (horizon_row["timestamp"] - anchor_at).total_seconds() * 1000.0
                    )
                    if observed and anchor_at is not None
                    else None
                ),
                "quote_age_from_horizon_ms": quote_age_ms if observed else None,
                "required_entry_quantity": required_exit_quantity,
                "available_best_ask_quantity": (
                    int(horizon_depth["best_ask_qty"])
                    if horizon_depth is not None
                    and horizon_depth.get("best_ask_qty") is not None
                    else None
                ),
                "depth_backed": ask_depth_backed if observed else None,
            }
        profit_touches: dict[str, dict[str, Any]] = {}
        for threshold in GROSS_PROFIT_TOUCH_BPS:
            hit = (
                next(
                    (
                        row
                        for row in post
                        if (row["price"] / reference - 1.0) * 10000.0 >= threshold
                    ),
                    None,
                )
                if anchor.get("lifecycle_stage") == "entry"
                else None
            )
            profit_touches[str(threshold)] = {
                "touched": (
                    hit is not None
                    if anchor.get("lifecycle_stage") == "entry"
                    else None
                ),
                "time_ms": (
                    round((hit["timestamp"] - anchor_at).total_seconds() * 1000.0)
                    if hit is not None and anchor_at is not None
                    else None
                ),
            }
        metrics.update(
            {
                "mfe_bps": round((high["price"] / reference - 1.0) * 10000.0, 4),
                "mae_bps": round((low["price"] / reference - 1.0) * 10000.0, 4),
                "terminal_return_bps": round(
                    (post[-1]["price"] / reference - 1.0) * 10000.0, 4
                ),
                "time_to_low_ms": (
                    round((low["timestamp"] - anchor_at).total_seconds() * 1000.0)
                    if anchor_at is not None
                    else None
                ),
                "time_to_high_ms": (
                    round((high["timestamp"] - anchor_at).total_seconds() * 1000.0)
                    if anchor_at is not None
                    else None
                ),
                "time_to_first_positive_trade_ms": (
                    round(
                        (first_positive["timestamp"] - anchor_at).total_seconds()
                        * 1000.0
                    )
                    if first_positive is not None and anchor_at is not None
                    else None
                ),
                "owner_target_touched": (
                    owner_target_hit is not None
                    if anchor.get("lifecycle_stage") == "entry"
                    and owner_target is not None
                    and owner_target > reference
                    else None
                ),
                "time_to_owner_target_ms": (
                    round(
                        (owner_target_hit["timestamp"] - anchor_at).total_seconds()
                        * 1000.0
                    )
                    if owner_target_hit is not None and anchor_at is not None
                    else None
                ),
                "fillable_owner_target_touch": {
                    "touched": (
                        fillable_owner_target_hit is not None
                        if anchor.get("lifecycle_stage") == "entry"
                        and owner_target is not None
                        and owner_target > reference
                        else None
                    ),
                    "time_ms": (
                        round(
                            (
                                fillable_owner_target_hit["timestamp"] - anchor_at
                            ).total_seconds()
                            * 1000.0
                        )
                        if fillable_owner_target_hit is not None
                        and anchor_at is not None
                        else None
                    ),
                    "gross_return_bps": (
                        round((owner_target / reference - 1.0) * 10000.0, 6)
                        if fillable_owner_target_hit is not None
                        and owner_target is not None
                        else None
                    ),
                    "required_exit_quantity": required_exit_quantity,
                    "available_best_bid_quantity": (
                        int(
                            fillable_depth_context(fillable_owner_target_hit)[
                                "best_bid_qty"
                            ]
                        )
                        if fillable_owner_target_hit is not None
                        and fillable_depth_context(fillable_owner_target_hit)
                        is not None
                        else None
                    ),
                    "depth_backed": fillable_owner_target_hit is not None,
                },
                "fillable_bid_exit_horizons": fillable_bid_exit_horizons,
                "entry_confirmation_bbo_horizons": (entry_confirmation_bbo_horizons),
                "gross_no_slippage_profit_touch": profit_touches,
            }
        )
    if anchor.get("anchor_role") in _ENTRY_CONFIRMATION_ANCHOR_ROLES:
        counterfactual_gaps: list[str] = []
        counterfactual_quantity = _finite_float(anchor.get("owner_requested_quantity"))
        if counterfactual_quantity is None and isinstance(outcome, dict):
            counterfactual_quantity = _finite_float(outcome.get("purchased_quantity"))
        if counterfactual_quantity is None:
            counterfactual_quantity = required_exit_quantity
        quantity = (
            int(counterfactual_quantity)
            if counterfactual_quantity is not None
            and counterfactual_quantity > 0
            and float(counterfactual_quantity).is_integer()
            else 0
        )
        cost_pct = _finite_float(anchor.get("owner_round_trip_cost_pct"))
        if status != "matched":
            counterfactual_gaps.append(status)
        if quantity <= 0:
            counterfactual_gaps.append("required_quantity_missing_or_invalid")
        if cost_pct is None or cost_pct < 0:
            counterfactual_gaps.append("round_trip_cost_contract_missing_or_invalid")
        entry_deadline = (
            anchor_at
            + timedelta(seconds=MARKET_WEAKNESS_COUNTERFACTUAL_MAX_QUOTE_AGE_SEC)
            if anchor_at is not None
            else None
        )
        executable_entry_row = None
        executable_entry_depth = None
        if not counterfactual_gaps and entry_deadline is not None:
            for candidate in post:
                if candidate["timestamp"] > entry_deadline:
                    break
                if candidate.get("best_ask") is None:
                    continue
                depth = fillable_depth_context(candidate)
                if (
                    depth is not None
                    and depth.get("best_ask") == candidate.get("best_ask")
                    and int(depth.get("best_ask_qty") or 0) >= quantity
                ):
                    executable_entry_row = candidate
                    executable_entry_depth = depth
                    break
        if executable_entry_row is None:
            counterfactual_gaps.append("executable_depth_backed_entry_ask_missing")
        entry_price = (
            float(executable_entry_row["best_ask"])
            if executable_entry_row is not None
            else None
        )
        executable_bid_path: list[tuple[dict[str, Any], dict[str, Any]]] = []
        if executable_entry_row is not None and entry_price is not None:
            maximum_at = anchor_at + timedelta(
                seconds=MARKET_WEAKNESS_COUNTERFACTUAL_POST_WINDOW_SEC
            )
            for candidate in post:
                if candidate["timestamp"] < executable_entry_row["timestamp"]:
                    continue
                if candidate["timestamp"] > maximum_at:
                    break
                if candidate.get("best_bid") is None:
                    continue
                depth = fillable_depth_context(candidate)
                if (
                    depth is not None
                    and depth.get("best_bid") == candidate.get("best_bid")
                    and int(depth.get("best_bid_qty") or 0) >= quantity
                ):
                    executable_bid_path.append((candidate, depth))
        if not executable_bid_path:
            counterfactual_gaps.append("executable_depth_backed_exit_bid_path_missing")

        horizons: dict[str, dict[str, Any]] = {}
        for horizon_sec in MARKET_WEAKNESS_COUNTERFACTUAL_HORIZONS_SEC:
            deadline = (
                anchor_at + timedelta(seconds=horizon_sec)
                if anchor_at is not None
                else None
            )
            candidates = [
                item
                for item in executable_bid_path
                if deadline is not None and item[0]["timestamp"] <= deadline
            ]
            selected = candidates[-1] if candidates else None
            quote_age_ms = (
                round((deadline - selected[0]["timestamp"]).total_seconds() * 1000.0)
                if deadline is not None and selected is not None
                else None
            )
            observed = bool(
                selected is not None
                and quote_age_ms is not None
                and 0
                <= quote_age_ms
                <= MARKET_WEAKNESS_COUNTERFACTUAL_MAX_QUOTE_AGE_SEC * 1000
                and entry_price is not None
                and cost_pct is not None
            )
            bid_price = float(selected[0]["best_bid"]) if observed else None
            gross_return_pct = (
                (bid_price / entry_price - 1.0) * 100.0
                if bid_price is not None and entry_price is not None
                else None
            )
            horizons[str(horizon_sec // 60)] = {
                "horizon_sec": horizon_sec,
                "observed": observed,
                "bid_price": round(bid_price, 6) if bid_price is not None else None,
                "gross_return_pct": (
                    round(gross_return_pct, 8) if gross_return_pct is not None else None
                ),
                "cost_aware_net_return_pct": (
                    round(gross_return_pct - cost_pct, 8)
                    if gross_return_pct is not None and cost_pct is not None
                    else None
                ),
                "quote_age_from_horizon_ms": quote_age_ms,
                "available_best_bid_quantity": (
                    int(selected[1]["best_bid_qty"]) if observed else None
                ),
                "required_quantity": quantity or None,
                "depth_backed": observed,
            }
        counterfactual_gaps.extend(
            f"executable_bbo_horizon_{minute}m_missing"
            for minute, row in horizons.items()
            if row.get("observed") is not True
        )

        target_price = _finite_float(anchor.get("owner_target_price"))
        adverse_price = None
        if (
            entry_price is not None
            and target_price is not None
            and target_price > entry_price
        ):
            adverse_price = entry_price - (target_price - entry_price)
        else:
            counterfactual_gaps.append("owner_target_not_above_executable_entry")
        target_hit = next(
            (
                item
                for item in executable_bid_path
                if target_price is not None
                and target_price > 0
                and float(item[0]["best_bid"]) >= target_price
            ),
            None,
        )
        adverse_hit = next(
            (
                item
                for item in executable_bid_path
                if adverse_price is not None
                and float(item[0]["best_bid"]) <= adverse_price
            ),
            None,
        )
        if target_hit is not None and adverse_hit is not None:
            if target_hit[0]["timestamp"] < adverse_hit[0]["timestamp"]:
                first_hit = "target_first"
            elif adverse_hit[0]["timestamp"] < target_hit[0]["timestamp"]:
                first_hit = "adverse_first"
            else:
                first_hit = "same_timestamp_ambiguous"
        elif target_hit is not None:
            first_hit = "target_first"
        elif adverse_hit is not None:
            first_hit = "adverse_first"
        else:
            first_hit = "unresolved"
        bid_returns_pct = (
            [
                (float(item[0]["best_bid"]) / entry_price - 1.0) * 100.0
                for item in executable_bid_path
            ]
            if entry_price is not None
            else []
        )
        metrics["market_weakness_counterfactual"] = {
            "schema": "machine_market_weakness_executable_bbo_counterfactual_v1",
            "source_quality_status": (
                "eligible" if not counterfactual_gaps else "blocked"
            ),
            "source_gap_reasons": sorted(set(counterfactual_gaps)),
            "entry": {
                "observed": executable_entry_row is not None,
                "ask_price": round(entry_price, 6) if entry_price is not None else None,
                "entry_at": (
                    executable_entry_row["timestamp"].isoformat()
                    if executable_entry_row is not None
                    else None
                ),
                "available_best_ask_quantity": (
                    int(executable_entry_depth["best_ask_qty"])
                    if executable_entry_depth is not None
                    else None
                ),
                "required_quantity": quantity or None,
                "depth_backed": executable_entry_row is not None,
            },
            "horizons_minutes": horizons,
            "mfe_executable_bid_pct": (
                round(max(bid_returns_pct), 8) if bid_returns_pct else None
            ),
            "mae_executable_bid_pct": (
                round(min(bid_returns_pct), 8) if bid_returns_pct else None
            ),
            "target_adverse_first_hit": {
                "state": first_hit,
                "target_price": target_price,
                "adverse_price": (
                    round(adverse_price, 6) if adverse_price is not None else None
                ),
                "target_at": (
                    target_hit[0]["timestamp"].isoformat()
                    if target_hit is not None
                    else None
                ),
                "adverse_at": (
                    adverse_hit[0]["timestamp"].isoformat()
                    if adverse_hit is not None
                    else None
                ),
                "adverse_threshold_role": (
                    "diagnostic_symmetric_distance_to_owner_target_not_stop"
                ),
            },
            "round_trip_cost_pct": cost_pct,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
        }

    metrics["entry_ask_depletion"] = _entry_ask_depletion_feature(
        anchor,
        window,
        source_complete=status == "matched",
    )
    result = dict(anchor)
    result.update(
        {
            "micro_context_status": status,
            "micro_tuning_input_allowed": bool(
                status == "matched"
                and anchor.get("owner_policy_tuning_eligible") is not False
            ),
            "base_owner_tuning_effect": False,
            "metrics": metrics,
        }
    )
    return result


def _entry_confirmation_label(result: dict[str, Any]) -> dict[str, Any] | None:
    if result.get("anchor_role") not in _ENTRY_CONFIRMATION_ANCHOR_ROLES:
        return None
    metrics = result.get("metrics") or {}
    bbo_horizons = metrics.get("entry_confirmation_bbo_horizons") or {}
    ask_report = metrics.get("entry_ask_depletion")
    missing_bbo = [
        horizon
        for horizon in ENTRY_CONFIRMATION_HORIZONS_SEC
        if (bbo_horizons.get(str(horizon)) or {}).get("observed") is not True
    ]
    ask_horizons = {
        int(row.get("horizon_ms") or 0): row
        for row in (ask_report or {}).get("horizons") or []
        if isinstance(row, dict)
    }
    missing_ask = [
        horizon
        for horizon in ENTRY_CONFIRMATION_HORIZONS_SEC
        if (ask_horizons.get(horizon * 1000) or {}).get("eligible_for_feature_ablation")
        is not True
    ]
    source_gaps: list[str] = []
    if result.get("entry_timing_decision_anchor_valid") is False:
        source_gaps.append("actual_signal_decision_timestamp_missing")
    if result.get("micro_context_status") != "matched":
        source_gaps.append(str(result.get("micro_context_status") or "unknown"))
    source_gaps.extend(f"bbo_{horizon}s_missing" for horizon in missing_bbo)
    source_gaps.extend(
        f"ask_depletion_{horizon}s_ineligible" for horizon in missing_ask
    )
    if isinstance(ask_report, dict):
        source_gaps.extend(
            str(value) for value in ask_report.get("source_gap_reasons") or []
        )
    if source_gaps:
        label = "source_quality_blocked"
    else:
        eligible_ask = [
            ask_horizons[horizon * 1000] for horizon in ENTRY_CONFIRMATION_HORIZONS_SEC
        ]
        bid_returns = [
            float(bbo_horizons[str(horizon)]["bid_return_bps"])
            for horizon in ENTRY_CONFIRMATION_HORIZONS_SEC
        ]
        refill_ratios = [
            float(value)
            for row in eligible_ask
            if (value := _finite_float(row.get("refill_ratio"))) is not None
        ]
        trade_backed_ratios = [
            float(value)
            for row in eligible_ask
            if (value := _finite_float(row.get("aggressive_buy_trade_backed_ratio")))
            is not None
        ]
        adverse = bool(
            min(bid_returns) <= -10.0
            or (refill_ratios and max(refill_ratios) >= 1.0)
            or any(row.get("downward_reprice_observed") is True for row in eligible_ask)
        )
        supportive = bool(
            not adverse
            and bid_returns[-1] >= 0.0
            and bool(trade_backed_ratios)
            and bool(refill_ratios)
            and max(trade_backed_ratios) >= 0.5
            and max(refill_ratios) < 0.5
        )
        label = (
            "adverse_veto_candidate"
            if adverse
            else (
                "supportive_confirmation_candidate"
                if supportive
                else "recheck_required"
            )
        )
    return {
        "anchor_id": result.get("anchor_id"),
        "lifecycle_id": result.get("lifecycle_id"),
        "owner": result.get("owner"),
        "scope_id": result.get("scope_id"),
        "entry_timing_scope_id": (
            f"{result.get('symbol')}:{result.get('session')}"
            if result.get("owner") == "widget"
            else result.get("scope_id")
        ),
        "symbol": result.get("symbol"),
        "session": result.get("session"),
        "anchor_at": result.get("anchor_at"),
        "entry_state": str(result.get("entry_state") or "UNSPECIFIED"),
        "source_entry_event_id": result.get("source_entry_event_id"),
        "anchor_role": result.get("anchor_role"),
        "classification": label,
        "source_gap_reasons": sorted(set(source_gaps)),
        "actual_order_submitted": result.get("actual_order_submitted") is True,
        "actual_realized_response_eligible": (
            result.get("actual_realized_response_eligible") is not False
        ),
        "owner_outcome": result.get("owner_outcome"),
        "owner_entry_limit_price": result.get("owner_entry_limit_price"),
        "owner_target_price": result.get("owner_target_price"),
        "owner_round_trip_cost_pct": result.get("owner_round_trip_cost_pct"),
        "owner_policy_tuning_eligible": (
            result.get("owner_policy_tuning_eligible") is True
        ),
        "owner_timing_custody_observation_eligible": (
            result.get("owner_timing_custody_observation_eligible") is True
        ),
        "anchor_price": (result.get("metrics") or {}).get("reference_price"),
        "entry_confirmation_bbo_horizons": bbo_horizons,
        "entry_ask_depletion": ask_report,
        "market_weakness_counterfactual": metrics.get("market_weakness_counterfactual"),
        "runtime_effect": False,
        "broker_order_forbidden": True,
    }


def _micro_entry_confirmation_summary(
    results: list[dict[str, Any]],
    *,
    widget_sources: dict[str, Any],
    target_date: str,
) -> dict[str, Any]:
    rows = [
        row
        for result in results
        if (row := _entry_confirmation_label(result)) is not None
    ]
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for row in rows:
        grouped[
            (
                str(row["owner"]),
                str(row.get("scope_id") or ""),
                str(row["symbol"]),
                str(row["session"]),
                str(row["entry_state"]),
            )
        ].append(row)
    cohorts: list[dict[str, Any]] = []
    for (
        owner,
        scope_id,
        symbol,
        session,
        entry_state,
    ), cohort_rows in sorted(grouped.items()):
        eligible_rows = [
            row
            for row in cohort_rows
            if row["classification"] != "source_quality_blocked"
        ]
        realized_net_returns = [
            float(outcome["cost_aware_net_return_pct"])
            for row in eligible_rows
            if isinstance((outcome := row.get("owner_outcome")), dict)
            and outcome.get("realized") is True
            and _finite_float(outcome.get("cost_aware_net_return_pct")) is not None
        ]
        cohorts.append(
            {
                "owner": owner,
                "scope_id": scope_id,
                "symbol": symbol,
                "session": session,
                "entry_state": entry_state,
                "sample_count": len(cohort_rows),
                "source_quality_eligible_count": len(eligible_rows),
                "classification_counts": {
                    label: sum(row["classification"] == label for row in cohort_rows)
                    for label in (
                        "supportive_confirmation_candidate",
                        "adverse_veto_candidate",
                        "recheck_required",
                        "source_quality_blocked",
                    )
                },
                "source_quality_adjusted_ev_pct": (
                    round(statistics.fmean(realized_net_returns), 8)
                    if realized_net_returns
                    else None
                ),
                "actual_realized_sample_count": len(realized_net_returns),
                "policy_candidate_ready": False,
            }
        )

    actual_entry_rows = [
        row
        for row in rows
        if row["anchor_role"] == "actual_widget_entry_signal"
        and row["actual_order_submitted"] is True
    ]
    blocked_entry_rows = [
        row
        for row in rows
        if row["anchor_role"] == "actual_widget_daily_cap_blocked_entry_signal"
    ]
    actual_source = widget_sources.get("actual_execution_events") or {}
    blocked_opportunities = (
        actual_source.get("blocked_daily_entry_limit_opportunities") or []
    )
    cap_reallocation: list[dict[str, Any]] = []
    cost_contract = (
        comparison_cost_contract(target_date)
        if date.fromisoformat(target_date) >= CLEAN_BASELINE_DATE
        else None
    )
    for opportunity in blocked_opportunities:
        if not isinstance(opportunity, dict):
            continue
        opportunity_at = _parse_owner_ts(opportunity.get("observed_at"))
        prior_candidates = sorted(
            [
                row
                for row in actual_entry_rows
                if row["symbol"] == opportunity.get("symbol")
                and row["session"] == opportunity.get("session")
                and opportunity_at is not None
                and (prior_at := _parse_owner_ts(row.get("anchor_at"))) is not None
                and prior_at < opportunity_at
            ],
            key=lambda row: str(row.get("anchor_at") or ""),
        )
        blocked_confirmation = next(
            (
                row
                for row in blocked_entry_rows
                if row.get("source_entry_event_id") == opportunity.get("signal_id")
            ),
            None,
        )
        prior = prior_candidates[-1] if prior_candidates else None
        prior_outcome = prior.get("owner_outcome") if isinstance(prior, dict) else None
        prior_outcome_ready = bool(
            isinstance(prior_outcome, dict)
            and prior_outcome.get("realized") is True
            and _finite_float(prior_outcome.get("cost_aware_net_return_pct"))
            is not None
            and prior_outcome.get("cost_contract_sha256")
            == (cost_contract or {}).get("contract_sha256")
        )
        entry_price = _finite_float(opportunity.get("entry_price"))
        exit_price = _finite_float(opportunity.get("source_only_exit_price"))
        gross_return = (
            (exit_price / entry_price - 1.0) * 100.0
            if entry_price is not None
            and entry_price > 0
            and exit_price is not None
            and exit_price > 0
            else None
        )
        source_quality_ready = bool(
            prior is not None
            and prior["classification"] != "source_quality_blocked"
            and prior_outcome_ready
            and blocked_confirmation is not None
            and blocked_confirmation["classification"] != "source_quality_blocked"
            and opportunity.get("source_only_exit_reason")
            and gross_return is not None
        )
        cap_reallocation.append(
            {
                **opportunity,
                "prior_actual_anchor_id": prior.get("anchor_id") if prior else None,
                "prior_actual_confirmation_classification": (
                    prior.get("classification") if prior else None
                ),
                "prior_actual_realized": (
                    prior_outcome.get("realized")
                    if isinstance(prior_outcome, dict)
                    else None
                ),
                "prior_actual_cost_aware_net_return_pct": (
                    prior_outcome.get("cost_aware_net_return_pct")
                    if isinstance(prior_outcome, dict)
                    else None
                ),
                "blocked_opportunity_anchor_id": (
                    blocked_confirmation.get("anchor_id")
                    if blocked_confirmation
                    else None
                ),
                "blocked_opportunity_confirmation_classification": (
                    blocked_confirmation.get("classification")
                    if blocked_confirmation
                    else None
                ),
                "comparison_status": (
                    "source_only_reallocation_evidence_ready"
                    if source_quality_ready
                    else "source_quality_blocked"
                ),
                "source_only_mark_gross_return_pct": (
                    round(gross_return, 8) if gross_return is not None else None
                ),
                "source_only_mark_cost_aware_return_pct": (
                    round(
                        gross_return - float(cost_contract["round_trip_cost_pct"]),
                        8,
                    )
                    if gross_return is not None and cost_contract is not None
                    else None
                ),
                "cost_contract_sha256": (
                    cost_contract["contract_sha256"]
                    if cost_contract is not None
                    else None
                ),
                "actual_order_submitted": False,
                "broker_fill_observed": False,
                "counterfactual_only": True,
                "daily_cap_mutation_allowed": False,
            }
        )
    return {
        "schema": "machine_micro_entry_confirmation_v1",
        "status": (
            "source_only_evidence_accumulating" if rows else "no_entry_anchor_observed"
        ),
        "decision": "no_runtime_or_policy_change",
        "metric_contract": MICRO_ENTRY_CONFIRMATION_CONTRACT,
        "authority": {
            "runtime_effect": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "policy_candidate_ready": False,
        },
        "summary": {
            "entry_anchor_count": len(rows),
            "source_quality_eligible_count": sum(
                row["classification"] != "source_quality_blocked" for row in rows
            ),
            "source_quality_blocked_count": sum(
                row["classification"] == "source_quality_blocked" for row in rows
            ),
            "owner_state_cohort_count": len(cohorts),
            "daily_cap_reallocation_observation_count": len(cap_reallocation),
        },
        "owner_state_cohorts": cohorts,
        "entry_anchors": rows,
        "daily_cap_reallocation_observations": cap_reallocation,
    }


def _scope_micro_gap_class(
    *,
    clean_baseline_allowed: bool,
    micro_source: dict[str, Any],
    inventory: dict[str, Any],
    scope_results: list[dict[str, Any]],
    owner_anchor_contract_invalid: bool = False,
    expected_venues: Iterable[str] = (),
    expected_sessions: Iterable[str] = (),
) -> str | None:
    if not clean_baseline_allowed:
        return "pre_clean_baseline_archive_only"
    if micro_source["partition_status"] != "loaded":
        return "micro_date_partition_missing"
    if micro_source["source_exclusion_manifest_status"] != "loaded":
        return "micro_source_exclusion_manifest_missing_or_invalid"
    if (micro_source.get("canary_source_quality") or {}).get("status") == (
        "missing_or_invalid"
    ):
        return "micro_canary_source_quality_missing_or_invalid"
    if (micro_source.get("canary_source_quality") or {}).get("status") == (
        "target_date_evidence_unavailable"
    ):
        return "micro_canary_target_date_evidence_unavailable"
    if (micro_source.get("canary_source_quality") or {}).get("status") == (
        "target_date_evidence_incomplete"
    ):
        return "micro_canary_target_date_evidence_incomplete"
    if (micro_source.get("canary_source_quality") or {}).get("status") == (
        "target_date_evidence_stale"
    ):
        return "micro_canary_target_date_evidence_stale"
    if micro_source.get("source_contract_ready") is not True:
        return "micro_stream_source_contract_invalid"
    if owner_anchor_contract_invalid:
        return "owner_anchor_contract_invalid"
    if _invalid_contract_count_for_scope(
        inventory,
        expected_venues=expected_venues,
        expected_sessions=expected_sessions,
    ):
        return "micro_scope_source_contract_invalid"
    if inventory["observed_row_count"] == 0:
        return "micro_symbol_not_observed"
    observed_venues = set(inventory.get("venues") or ())
    observed_sessions = set(inventory.get("sessions") or ())
    if set(expected_venues) - observed_venues:
        return "micro_expected_venue_not_observed"
    if set(expected_sessions) - observed_sessions:
        return "micro_expected_session_not_observed"
    status_priority = (
        "owner_anchor_contract_invalid",
        "micro_scope_source_contract_invalid",
        "micro_post_anchor_not_observed",
        "micro_anchor_window_not_observed",
        "micro_symbol_not_observed",
    )
    observed_statuses = {
        str(item.get("micro_context_status"))
        for item in scope_results
        if item.get("micro_context_status") != "matched"
    }
    return next(
        (status for status in status_priority if status in observed_statuses),
        next(iter(sorted(observed_statuses)), None),
    )


def _lifecycle_objective_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    decision_roles = {
        "counterfactual_calibration_entry",
        "actual_widget_entry_signal",
        "episode_signal_bar",
        "prospective_widget_research_entry",
        "prospective_episode_research_signal",
    }
    context_matched_results = [
        row for row in results if row.get("micro_context_status") == "matched"
    ]
    context_matched_decision_lifecycle_ids = {
        str(row.get("lifecycle_id"))
        for row in context_matched_results
        if row.get("anchor_role") in decision_roles and row.get("lifecycle_id")
    }
    policy_eligible_matched_results = [
        row
        for row in context_matched_results
        if row.get("micro_tuning_input_allowed") is True
    ]
    policy_eligible_matched_decision_lifecycle_ids = {
        str(row.get("lifecycle_id"))
        for row in policy_eligible_matched_results
        if row.get("anchor_role") in decision_roles and row.get("lifecycle_id")
    }
    matched_entry_fill_count = sum(
        row.get("anchor_role")
        in {"episode_buy_fill_confirmed", "actual_widget_entry_fill_reconciled"}
        for row in context_matched_results
    )
    matched_partial_entry_fill_count = sum(
        row.get("lifecycle_stage") == "entry_partial_fill"
        for row in context_matched_results
    )
    matched_entry_submit_count = sum(
        row.get("anchor_role") == "actual_widget_entry_submit_accept_recorded"
        for row in context_matched_results
    )
    matched_exit_submit_count = sum(
        row.get("anchor_role") == "actual_widget_exit_submit_accept_recorded"
        for row in context_matched_results
    )
    matched_exit_count = sum(
        row.get("lifecycle_stage") == "exit" for row in context_matched_results
    )
    matched_manual_exit_count = sum(
        row.get("anchor_role")
        in {
            "episode_manual_exit_confirmed",
            "episode_manual_exit_reconciled",
            "actual_widget_manual_partial_exit_reconciled",
            "actual_widget_manual_exit_reconciled",
        }
        for row in context_matched_results
    )
    matched_partial_exit_fill_count = sum(
        row.get("lifecycle_stage") == "exit_partial_fill"
        for row in context_matched_results
    )
    outcome_units: dict[tuple[str, str], dict[str, Any]] = {}
    owner_outcome_keys: set[tuple[str, str]] = set()
    for row in results:
        if row.get("owner_lifecycle_contract_valid") is False:
            continue
        outcome = row.get("owner_outcome")
        if not isinstance(outcome, dict):
            continue
        lifecycle_id = str(row.get("lifecycle_id") or row.get("anchor_id") or "")
        leg_id = str(outcome.get("leg_id") or "owner_episode")
        if not lifecycle_id:
            continue
        owner_outcome_keys.add((lifecycle_id, leg_id))
        if lifecycle_id not in context_matched_decision_lifecycle_ids:
            continue
        existing = outcome_units.get((lifecycle_id, leg_id))
        if existing is None or (
            existing["outcome"].get("holding_duration_ms") is None
            and outcome.get("holding_duration_ms") is not None
        ):
            outcome_units[(lifecycle_id, leg_id)] = {
                "outcome": outcome,
                "cohort": (
                    "actual_widget_execution"
                    if row.get("actual_order_submitted") is True
                    and row.get("owner") == "widget"
                    else (
                        "actual_episode_execution"
                        if row.get("actual_order_submitted") is True
                        else "source_only_counterfactual"
                    )
                ),
            }
    realized_units = [
        unit
        for unit in outcome_units.values()
        if unit["outcome"].get("realized") is True
    ]
    manual_exit_units = [
        unit
        for unit in realized_units
        if unit["outcome"].get("exit_execution_class") == "manual_operator_exit"
    ]
    manual_exit_loss_units = [
        unit
        for unit in manual_exit_units
        if unit["outcome"].get("realized_loss") is True
    ]
    machine_target_units = [
        unit
        for unit in realized_units
        if unit["outcome"].get("exit_execution_class") == "machine_target_fill"
    ]
    episode_machine_target_units = [
        unit
        for unit in machine_target_units
        if unit["cohort"] == "actual_episode_execution"
    ]
    episode_manual_exit_units = [
        unit
        for unit in manual_exit_units
        if unit["cohort"] == "actual_episode_execution"
    ]
    episode_manual_exit_loss_units = [
        unit
        for unit in manual_exit_loss_units
        if unit["cohort"] == "actual_episode_execution"
    ]
    widget_manual_exit_units = [
        unit
        for unit in manual_exit_units
        if unit["cohort"] == "actual_widget_execution"
    ]
    widget_manual_exit_loss_units = [
        unit
        for unit in manual_exit_loss_units
        if unit["cohort"] == "actual_widget_execution"
    ]
    realized_holding_durations_ms = [
        value
        for unit in realized_units
        if (value := _finite_float(unit["outcome"].get("holding_duration_ms")))
        is not None
        and value >= 0
    ]
    gross_values = [
        value
        for unit in realized_units
        if (value := _finite_float(unit["outcome"].get("gross_no_slippage_return_pct")))
        is not None
    ]
    cost_aware_values = [
        value
        for unit in realized_units
        if (value := _finite_float(unit["outcome"].get("cost_aware_net_return_pct")))
        is not None
    ]
    fast_completed_count = sum(
        value <= 180_000 for value in realized_holding_durations_ms
    )

    cohort_diagnostics: dict[str, dict[str, Any]] = {}
    for cohort in (
        "actual_widget_execution",
        "actual_episode_execution",
        "source_only_counterfactual",
    ):
        cohort_units = [unit for unit in realized_units if unit["cohort"] == cohort]
        cohort_manual_units = [
            unit
            for unit in cohort_units
            if unit["outcome"].get("exit_execution_class") == "manual_operator_exit"
        ]
        cohort_gross = [
            value
            for unit in cohort_units
            if (
                value := _finite_float(
                    unit["outcome"].get("gross_no_slippage_return_pct")
                )
            )
            is not None
        ]
        cohort_holding = [
            value
            for unit in cohort_units
            if (value := _finite_float(unit["outcome"].get("holding_duration_ms")))
            is not None
            and value >= 0
        ]
        cohort_fast = sum(value <= 180_000 for value in cohort_holding)
        cohort_cost_aware = [
            value
            for unit in cohort_units
            if (
                value := _finite_float(unit["outcome"].get("cost_aware_net_return_pct"))
            )
            is not None
        ]
        cohort_diagnostics[cohort] = {
            "realized_sample_count": len(cohort_units),
            "machine_target_fill_sample_count": sum(
                unit["outcome"].get("exit_execution_class") == "machine_target_fill"
                for unit in cohort_units
            ),
            "manual_operator_exit_sample_count": len(cohort_manual_units),
            "manual_operator_exit_loss_sample_count": sum(
                unit["outcome"].get("realized_loss") is True
                for unit in cohort_manual_units
            ),
            "gross_no_slippage_avg_return_pct": (
                round(statistics.fmean(cohort_gross), 6) if cohort_gross else None
            ),
            "cost_aware_equal_weight_avg_profit_pct": (
                round(statistics.fmean(cohort_cost_aware), 6)
                if cohort_cost_aware
                else None
            ),
            "median_holding_duration_ms": (
                round(statistics.median(cohort_holding), 3) if cohort_holding else None
            ),
            "completed_within_180s_count": cohort_fast,
            "completed_within_180s_ratio": (
                round(cohort_fast / len(cohort_holding), 6) if cohort_holding else None
            ),
        }
    populated_cohorts = sum(
        row["realized_sample_count"] > 0 for row in cohort_diagnostics.values()
    )
    implementation_boundary = {
        "post_fill_limit_take_profit_present": True,
        "next_trading_day_owner_report_micro_ingestion": True,
        "owner_report_ingestion_selection_effect": False,
        "rolling_paired_policy_candidate_producer_present": False,
        "episode_same_day_reentry_or_timeout_tuning_axis_present": False,
        "speed_or_turnover_metric_changes_policy_selection": False,
    }
    remaining_gaps: list[str] = []
    if not implementation_boundary["rolling_paired_policy_candidate_producer_present"]:
        remaining_gaps.append(
            "rolling_paired_policy_candidate_producer_not_implemented"
        )
    if not implementation_boundary[
        "episode_same_day_reentry_or_timeout_tuning_axis_present"
    ]:
        remaining_gaps.append("episode_single_attempt_no_same_day_reentry_tuning_axis")
    if not implementation_boundary["speed_or_turnover_metric_changes_policy_selection"]:
        remaining_gaps.append("speed_and_capital_occupancy_not_policy_selection_axes")
    return {
        "decision": "partial_alignment_source_only_lifecycle_observation",
        "contract": FAST_LIFECYCLE_OBJECTIVE_CONTRACT,
        "identified": bool(context_matched_decision_lifecycle_ids),
        "applied_to_sim": False,
        "reflected_in_real_runtime_policy": False,
        "lifecycle_coverage": {
            "matched_decision_lifecycle_count": len(
                policy_eligible_matched_decision_lifecycle_ids
            ),
            "context_matched_decision_lifecycle_count": len(
                context_matched_decision_lifecycle_ids
            ),
            "policy_eligible_matched_decision_lifecycle_count": len(
                policy_eligible_matched_decision_lifecycle_ids
            ),
            "matched_entry_fill_anchor_count": matched_entry_fill_count,
            "matched_partial_entry_fill_anchor_count": (
                matched_partial_entry_fill_count
            ),
            "matched_entry_submit_anchor_count": matched_entry_submit_count,
            "matched_exit_submit_anchor_count": matched_exit_submit_count,
            "matched_exit_anchor_count": matched_exit_count,
            "matched_manual_exit_anchor_count": matched_manual_exit_count,
            "matched_partial_exit_fill_anchor_count": (matched_partial_exit_fill_count),
            "owner_outcome_unit_count": len(outcome_units),
            "owner_outcome_not_micro_attributed_count": len(owner_outcome_keys)
            - len(outcome_units),
            "realized_owner_outcome_count": len(realized_units),
            "episode_machine_target_fill_owner_outcome_count": len(
                episode_machine_target_units
            ),
            "episode_manual_operator_exit_owner_outcome_count": len(
                episode_manual_exit_units
            ),
            "episode_manual_operator_exit_loss_owner_outcome_count": len(
                episode_manual_exit_loss_units
            ),
            "widget_manual_operator_exit_owner_outcome_count": len(
                widget_manual_exit_units
            ),
            "widget_manual_operator_exit_loss_owner_outcome_count": len(
                widget_manual_exit_loss_units
            ),
            "all_owner_machine_target_fill_outcome_count": len(machine_target_units),
            "all_owner_manual_operator_exit_outcome_count": len(manual_exit_units),
            "all_owner_manual_operator_exit_loss_outcome_count": len(
                manual_exit_loss_units
            ),
            "unrealized_owner_outcome_count": len(outcome_units) - len(realized_units),
            "timed_owner_outcome_count": len(realized_holding_durations_ms),
            "timing_missing_owner_outcome_count": len(realized_units)
            - len(realized_holding_durations_ms),
        },
        "gross_no_slippage_diagnostic": {
            "authority": "diagnostic_only",
            "cohort_mixing_forbidden": True,
            "cohorts": cohort_diagnostics,
            "sample_count": len(gross_values),
            "avg_return_pct": (
                round(statistics.fmean(gross_values), 6)
                if gross_values and populated_cohorts <= 1
                else None
            ),
            "median_holding_duration_ms": (
                round(statistics.median(realized_holding_durations_ms), 3)
                if realized_holding_durations_ms and populated_cohorts <= 1
                else None
            ),
            "completed_within_180s_count": fast_completed_count,
            "completed_within_180s_ratio": (
                round(fast_completed_count / len(realized_holding_durations_ms), 6)
                if realized_holding_durations_ms and populated_cohorts <= 1
                else None
            ),
        },
        "cost_aware_owner_outcome_diagnostic": {
            "cohort_mixing_forbidden": True,
            "cohorts": {
                cohort: {
                    "sample_count": row["realized_sample_count"],
                    "equal_weight_avg_profit_pct": row[
                        "cost_aware_equal_weight_avg_profit_pct"
                    ],
                }
                for cohort, row in cohort_diagnostics.items()
            },
            "sample_count": len(cost_aware_values),
            "equal_weight_avg_profit_pct": (
                round(statistics.fmean(cost_aware_values), 6)
                if cost_aware_values and populated_cohorts <= 1
                else None
            ),
            "policy_authority": False,
            "reason": "daily_unpaired_owner_outcome_context_only",
        },
        "implementation_boundary": implementation_boundary,
        "remaining_gaps": remaining_gaps,
    }


def _canonical_payload_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _candidate_payload_sha256(candidate: Mapping[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_sha256", None)
    return _canonical_payload_sha256(payload)


def _bound_objective_candidate_handoff(
    candidate: Mapping[str, Any], *, expected_handoff_gap_codes: Sequence[str]
) -> dict[str, Any] | None:
    binding = candidate.get("objective_followup_binding")
    if not isinstance(binding, Mapping):
        return None
    resolved_gap_codes = binding.get("resolved_gap_codes")
    if (
        binding.get("schema") != OBJECTIVE_CANDIDATE_BINDING_SCHEMA
        or binding.get("followup_id") != FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID
        or not isinstance(resolved_gap_codes, list)
        or any(
            not isinstance(value, str) or not value.strip()
            for value in resolved_gap_codes
        )
        or len(set(resolved_gap_codes)) != len(resolved_gap_codes)
        or sorted(resolved_gap_codes) != sorted(expected_handoff_gap_codes)
    ):
        return None
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    if not candidate_id:
        return None
    digest = _candidate_payload_sha256(candidate)
    declared_digest = str(candidate.get("candidate_sha256") or "").strip()
    if declared_digest and declared_digest != digest:
        return None
    return {
        "schema": OBJECTIVE_HANDOFF_BINDING_SCHEMA,
        "followup_id": FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
        "candidate_id": candidate_id,
        "candidate_sha256": digest,
        "required_gap_codes": list(expected_handoff_gap_codes),
        "resolved_gap_codes": list(resolved_gap_codes),
    }


def _fast_lifecycle_objective_followup(
    *,
    target_date: str,
    objective_alignment: dict[str, Any],
    promotion_candidates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    boundary = objective_alignment.get("implementation_boundary") or {}
    reflected_in_runtime = (
        objective_alignment.get("reflected_in_real_runtime_policy") is True
    )
    turnover_selection_present = (
        boundary.get("speed_or_turnover_metric_changes_policy_selection") is True
    )
    paired_producer_present = (
        boundary.get("rolling_paired_policy_candidate_producer_present") is True
    )
    sample_floor_assessment = objective_alignment.get("sample_floor_assessment") or {}
    sample_floor_state = str(sample_floor_assessment.get("state") or "")
    required_gap_codes = list(
        dict.fromkeys(objective_alignment.get("remaining_gaps") or [])
    )
    expected_handoff_gap_codes = [
        gap_code
        for gap_code in required_gap_codes
        if gap_code in OBJECTIVE_HANDOFF_RESOLVABLE_GAP_CODES
    ]
    non_handoff_gap_codes = [
        gap_code
        for gap_code in required_gap_codes
        if gap_code not in OBJECTIVE_HANDOFF_RESOLVABLE_GAP_CODES
    ]
    matching_handoffs = [
        handoff
        for candidate in promotion_candidates
        if (
            handoff := _bound_objective_candidate_handoff(
                candidate,
                expected_handoff_gap_codes=expected_handoff_gap_codes,
            )
        )
        is not None
    ]
    candidate_handoff_binding: dict[str, Any] | None = None
    remaining_gap_codes = list(required_gap_codes)
    completion_ready = (
        reflected_in_runtime and turnover_selection_present and not required_gap_codes
    )
    if completion_ready:
        state = "COMPLETE"
        followup_required = False
        attention_class = "none"
        current_capability = "bounded_runtime_policy_with_post_apply_attribution"
        next_action = "continue_post_apply_attribution_and_rollback_monitoring"
    elif len(matching_handoffs) == 1 and not non_handoff_gap_codes:
        state = "CANDIDATE_QUEUE_HANDOFF"
        followup_required = False
        attention_class = "candidate_queue"
        current_capability = "rolling_paired_candidate_ready"
        next_action = "track_candidate_in_separate_approval_queue"
        remaining_gap_codes = []
        candidate_handoff_binding = matching_handoffs[0]
    elif not paired_producer_present:
        state = "IMPLEMENTATION_REQUIRED"
        followup_required = True
        attention_class = "code_improvement_workorder"
        current_capability = "diagnostic_observation_only"
        next_action = "implement_source_only_rolling_paired_policy_research"
    elif "current_attribution_source_contract_invalid" in required_gap_codes:
        state = "EVIDENCE_ACCUMULATING"
        followup_required = True
        attention_class = "source_quality"
        current_capability = "rolling_paired_research_source_quality_blocked"
        recovery = objective_alignment.get("current_source_contract_recovery") or {}
        next_action = (
            "quarantine_current_source_date_and_continue_next_exact_date_collection"
            if isinstance(recovery, dict)
            and recovery.get("rerun_same_source_date_allowed") is False
            else "repair_current_attribution_source_contract_and_rerun"
        )
    elif sample_floor_state == "source_quality_or_eligibility_gap":
        state = "EVIDENCE_ACCUMULATING"
        followup_required = True
        attention_class = "source_quality"
        current_capability = "rolling_paired_research_scope_source_blocked"
        next_action = "repair_exact_scope_source_or_eligibility_contract_and_rerun"
    elif sample_floor_state == "source_report_contract_gap":
        state = "EVIDENCE_ACCUMULATING"
        followup_required = True
        attention_class = "source_quality"
        current_capability = "rolling_paired_research_report_contract_blocked"
        next_action = "repair_excluded_source_report_contracts_and_rerun"
    elif sample_floor_state == "terminal_or_right_censored_gap":
        state = "EVIDENCE_ACCUMULATING"
        followup_required = True
        attention_class = "terminal_reconciliation"
        current_capability = "rolling_paired_research_terminal_outcome_blocked"
        next_action = "reconcile_exact_owner_terminal_outcomes_before_waiting"
    elif sample_floor_state == "window_floor_unattainable_at_observed_yield":
        state = "IMPLEMENTATION_REQUIRED"
        followup_required = True
        attention_class = "sample_floor_contract"
        current_capability = "rolling_paired_research_window_floor_unattainable"
        next_action = "repair_exact_scope_collection_yield_or_review_window_contract"
    else:
        state = "EVIDENCE_ACCUMULATING"
        followup_required = True
        attention_class = "evidence_collection"
        current_capability = "rolling_paired_research_without_ready_candidate"
        next_action = "continue_exact_date_collection_and_rolling_readiness_review"
        if not remaining_gap_codes:
            remaining_gap_codes.append("objective_bound_candidate_missing_or_ambiguous")
    row = {
        "schema": OBJECTIVE_FOLLOWUP_SCHEMA,
        "followup_id": FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
        "source_date": target_date,
        "state": state,
        "followup_required": followup_required,
        "attention_class": attention_class,
        "operator_decision_required": False,
        "current_capability": current_capability,
        "remaining_gap_codes": remaining_gap_codes,
        "next_action": next_action,
        "metric_contract": OBJECTIVE_FOLLOWUP_METRIC_CONTRACT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if candidate_handoff_binding is not None:
        row["candidate_handoff_binding"] = candidate_handoff_binding
    source_contract_recovery = objective_alignment.get(
        "current_source_contract_recovery"
    )
    if isinstance(source_contract_recovery, dict) and source_contract_recovery:
        row["source_contract_recovery"] = dict(source_contract_recovery)
    return row


def _rolling_source_contract_recovery(gap: str | None) -> dict[str, Any]:
    if gap is None:
        return {
            "disposition": "not_required",
            "rerun_same_source_date_allowed": False,
            "excluded_from_rolling_policy_evidence": False,
            "next_action": "continue_rolling_readiness_review",
        }
    if gap == "micro_canary_target_date_evidence_incomplete":
        return {
            "disposition": "immutable_source_date_quarantine",
            "rerun_same_source_date_allowed": False,
            "excluded_from_rolling_policy_evidence": True,
            "next_action": (
                "quarantine_current_source_date_and_continue_next_exact_date_collection"
            ),
            "reason": "irreversible_intraday_observation_loss_cannot_be_reconstructed",
        }
    return {
        "disposition": "repairable_source_contract_gap",
        "rerun_same_source_date_allowed": True,
        "excluded_from_rolling_policy_evidence": True,
        "next_action": "repair_current_attribution_source_contract_and_rerun",
        "reason": gap,
    }


def build_report(
    target_date: str,
    *,
    report_root: Path = DATA_DIR / "report",
    observation_root: Path = OBSERVATION_ROOT,
    source_exclusion_manifest_path: Path = DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    canary_snapshot_path: Path | None = DEFAULT_CANARY_SNAPSHOT_PATH,
    canary_snapshot_dir: Path = CANARY_DAILY_SNAPSHOT_DIR,
    widget_state_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    generated = now or datetime.now(KST)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=KST)
    generated = generated.astimezone(KST)
    canary_snapshot_path = resolve_target_canary_snapshot(
        target_date=target_day,
        latest_path=canary_snapshot_path,
        daily_root=canary_snapshot_dir,
    )
    clean_baseline_allowed = target_day >= CLEAN_BASELINE_DATE
    resolved_widget_state_path = widget_state_path or (
        DEFAULT_WIDGET_AUTO_TRADE_STATE_PATH
        if report_root == DATA_DIR / "report"
        else report_root.parent / "runtime" / "widget_signal_auto_trade_state.json"
    )
    widget_symbols, widget_anchors, widget_sources = _widget_inventory(
        target_date, report_root, widget_state_path=resolved_widget_state_path
    )
    episode_profiles, episode_anchors, episode_sources = _episode_inventory(
        target_date, report_root
    )
    weakness_blocked_anchors, weakness_blocked_source = (
        _market_weakness_blocked_entry_inventory(target_date, report_root)
    )
    anchors = widget_anchors + episode_anchors + weakness_blocked_anchors
    symbols = set(widget_symbols)
    symbols.update(
        str(row.get("symbol")) for row in episode_profiles.values() if row.get("symbol")
    )
    symbols.update(str(row["symbol"]) for row in weakness_blocked_anchors)
    micro_source, micro_inventory, windows = _micro_context(
        target_date,
        observation_root,
        symbols,
        anchors,
        source_exclusion_manifest_path,
        canary_snapshot_path,
        generated,
    )
    source_contract_gap = (
        "micro_source_exclusion_manifest_missing_or_invalid"
        if micro_source["source_exclusion_manifest_status"] != "loaded"
        else (
            "micro_canary_source_quality_missing_or_invalid"
            if (micro_source.get("canary_source_quality") or {}).get("status")
            == "missing_or_invalid"
            else (
                "micro_canary_target_date_evidence_unavailable"
                if (micro_source.get("canary_source_quality") or {}).get("status")
                == "target_date_evidence_unavailable"
                else (
                    "micro_canary_target_date_evidence_incomplete"
                    if (micro_source.get("canary_source_quality") or {}).get("status")
                    == "target_date_evidence_incomplete"
                    else (
                        "micro_canary_target_date_evidence_stale"
                        if (micro_source.get("canary_source_quality") or {}).get(
                            "status"
                        )
                        == "target_date_evidence_stale"
                        else (
                            "micro_stream_source_contract_invalid"
                            if micro_source.get("source_contract_ready") is not True
                            else None
                        )
                    )
                )
            )
        )
    )
    results = [
        _anchor_result(
            anchor,
            micro_inventory[anchor["symbol"]],
            windows[anchor["anchor_id"]],
            partition_loaded=micro_source["partition_status"] == "loaded",
            source_contract_gap=source_contract_gap,
            clean_baseline_allowed=clean_baseline_allowed,
        )
        for anchor in anchors
    ]
    micro_entry_confirmation = _micro_entry_confirmation_summary(
        results,
        widget_sources=widget_sources,
        target_date=target_date,
    )
    market_weakness_response = build_machine_market_weakness_response(
        micro_entry_confirmation,
        target_date=target_date,
        observation_root=report_root / "market_weakness_observations",
        symbol_master_dir=report_root / "micro_reversion_economic_reference",
        history_report_dir=report_root / REPORT_TYPE,
    )
    results_by_scope: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        results_by_scope[(result["owner"], result["scope_id"])].append(result)

    gaps: list[dict[str, Any]] = []

    def append_gap(
        *,
        owner: str,
        scope_id: str,
        row: dict[str, Any],
        symbol: str,
        gap_class: str,
        expected_venues: list[str] | None = None,
        scope_kind: str | None = None,
    ) -> None:
        scope_kinds = row.get("scopes") or [row.get("scope")]
        normalized_scope_kinds = [str(value) for value in scope_kinds if value]
        resolved_scope_kind = scope_kind or (
            "active_widget_owner"
            if owner == "widget" and "active_widget_owner" in normalized_scope_kinds
            else (
                "active_episode_owner"
                if owner == "episode"
                and "active_episode_owner" in normalized_scope_kinds
                else (
                    normalized_scope_kinds[0]
                    if normalized_scope_kinds
                    else "unknown_owner_scope"
                )
            )
        )
        gaps.append(
            {
                "owner": owner,
                "scope_id": scope_id,
                "scope_kind": resolved_scope_kind,
                "symbol": symbol,
                "expected_venues": list(
                    expected_venues or row.get("expected_venues") or ["SOR"]
                ),
                "gap_class": gap_class,
                "effect": "micro_context_unavailable_base_owner_tuning_unchanged",
            }
        )

    for owner, rows in (("widget", widget_symbols), ("episode", episode_profiles)):
        for scope_id, row in rows.items():
            symbol = str(
                row.get("symbol")
                or (
                    ""
                    if owner == "episode"
                    and row.get("scope") == "invalid_episode_owner_identity"
                    else scope_id
                )
            )
            inventory = micro_inventory.get(symbol) or {
                "observed_row_count": 0,
                "eligible_row_count": 0,
                "ineligible_row_count": 0,
                "source_excluded_row_count": 0,
                "invalid_contract_row_count": 0,
                "invalid_contract_scope_counts": {},
                "depth_row_count": 0,
                "venues": [],
                "sessions": [],
            }
            if owner == "widget":
                widget_scope_ids = list(row.get("owner_scope_ids") or [])
                session_contexts: dict[str, dict[str, Any]] = {}
                for widget_scope_id in widget_scope_ids:
                    exact_results = results_by_scope.get(
                        ("widget", str(widget_scope_id)), []
                    )
                    session_name = widget_scope_id.rsplit(":", 1)[-1]
                    exact_venues = sorted(
                        {
                            str(venue)
                            for result in exact_results
                            for venue in result.get("expected_venues") or []
                        }
                    )
                    if not exact_venues:
                        inferred_venue = session_name.split("_", 1)[0].upper()
                        exact_venues = list(
                            (row.get("owner_scope_expected_venues") or {}).get(
                                widget_scope_id
                            )
                            or ()
                        ) or (
                            [inferred_venue]
                            if inferred_venue in {"KRX", "NXT", "SOR"}
                            else list(row.get("expected_venues") or ["SOR"])
                        )
                    exact_sessions = sorted(
                        {
                            str(session)
                            for result in exact_results
                            for session in result.get("expected_session_buckets") or []
                        }
                    ) or [session_name]
                    owner_contract_invalid = any(
                        gap.get("scope_id") == widget_scope_id
                        for gap in row.get("owner_anchor_contract_gaps") or []
                        if isinstance(gap, dict)
                    )
                    exact_gap = _scope_micro_gap_class(
                        clean_baseline_allowed=clean_baseline_allowed,
                        micro_source=micro_source,
                        inventory=inventory,
                        scope_results=exact_results,
                        owner_anchor_contract_invalid=owner_contract_invalid,
                        expected_venues=exact_venues,
                        expected_sessions=exact_sessions,
                    )
                    session_contexts[widget_scope_id] = {
                        "micro_context_status": exact_gap
                        or (
                            "matched" if exact_results else "observed_no_owner_episode"
                        ),
                        "micro_tuning_input_allowed": bool(exact_results)
                        and all(
                            item["micro_tuning_input_allowed"] is True
                            for item in exact_results
                        ),
                        "anchor_results": exact_results,
                        "expected_venues": exact_venues,
                        "base_owner_tuning_effect": False,
                    }
                    if exact_gap:
                        append_gap(
                            owner=owner,
                            scope_id=widget_scope_id,
                            row=row,
                            symbol=symbol,
                            gap_class=exact_gap,
                            expected_venues=exact_venues,
                            scope_kind=(row.get("owner_scope_kinds") or {}).get(
                                widget_scope_id
                            ),
                        )
                row["session_contexts"] = session_contexts
                scope_results = [
                    result
                    for result in results
                    if result["owner"] == "widget" and result["symbol"] == symbol
                ]
                session_gaps = [
                    context["micro_context_status"]
                    for context in session_contexts.values()
                    if context["micro_context_status"]
                    not in {"matched", "observed_no_owner_episode"}
                ]
                gap_class = session_gaps[0] if session_gaps else None
                row["micro_tuning_input_allowed"] = bool(scope_results) and all(
                    context["micro_tuning_input_allowed"]
                    for context in session_contexts.values()
                    if context["anchor_results"]
                )
            else:
                scope_results = results_by_scope.get((owner, str(scope_id)), [])
                owner_contract_invalid = (
                    row.get("owner_anchor_contract_status") == "invalid"
                )
                gap_class = _scope_micro_gap_class(
                    clean_baseline_allowed=clean_baseline_allowed,
                    micro_source=micro_source,
                    inventory=inventory,
                    scope_results=scope_results,
                    owner_anchor_contract_invalid=owner_contract_invalid,
                    expected_venues=row.get("expected_venues") or ["SOR"],
                    expected_sessions=["SOR_REGULAR"],
                )
                row["micro_tuning_input_allowed"] = bool(scope_results) and all(
                    item["micro_tuning_input_allowed"] is True for item in scope_results
                )
                if gap_class:
                    append_gap(
                        owner=owner,
                        scope_id=str(scope_id),
                        row=row,
                        symbol=symbol,
                        gap_class=gap_class,
                    )
            row["micro_source_inventory"] = inventory
            row["micro_context_status"] = gap_class or (
                "matched" if scope_results else "observed_no_owner_episode"
            )
            row["base_owner_tuning_effect"] = False
            row["anchor_results"] = scope_results

    source_gaps = [
        {
            "owner": "widget",
            "source": key,
            "gap_class": f"owner_source_{value['status']}",
        }
        for key, value in widget_sources.items()
        if value["status"] != "loaded"
        and not (
            value.get("optional_when_absent") is True
            and value["status"] == "not_observed"
        )
    ] + [
        {
            "owner": "episode",
            "source": key,
            "gap_class": f"owner_source_{value['status']}",
        }
        for key, value in episode_sources.items()
        if value["status"] != "loaded"
    ]
    gaps.extend(source_gaps)
    matched = sum(item["micro_context_status"] == "matched" for item in results)
    objective_alignment = _lifecycle_objective_summary(results)
    rolling_policy_source_contract = {
        "ready": bool(clean_baseline_allowed and source_contract_gap is None),
        "gap": source_contract_gap,
        "recovery": _rolling_source_contract_recovery(source_contract_gap),
        "required": (
            "clean_baseline_and_exact_date_partition_manifest_canary_stream_contract"
        ),
    }
    research_input_report = {
        "schema": REPORT_SCHEMA,
        "target_date": target_date,
        "clean_baseline_allowed": clean_baseline_allowed,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "rolling_policy_source_contract": rolling_policy_source_contract,
        "consumers": {
            "widget_postclose_tuning": {"symbols": widget_symbols},
            "episode_machine_postclose_tuning": {"profiles": episode_profiles},
        },
    }
    rolling_paired_policy_research = build_rolling_paired_policy_research(
        target_date=target_date,
        current_report=research_input_report,
        report_dir=report_root / REPORT_TYPE,
    )
    research_boundary = (
        rolling_paired_policy_research.get("implementation_boundary") or {}
    )
    objective_alignment["implementation_boundary"].update(research_boundary)
    objective_alignment["remaining_gaps"] = list(
        rolling_paired_policy_research.get("remaining_gap_codes") or []
    )
    objective_alignment["current_source_contract_recovery"] = dict(
        (rolling_paired_policy_research.get("current_source_contract") or {}).get(
            "recovery"
        )
        or rolling_policy_source_contract["recovery"]
    )
    objective_alignment["sample_floor_assessment"] = dict(
        rolling_paired_policy_research.get("sample_floor_assessment") or {}
    )
    research_status = str(rolling_paired_policy_research.get("status") or "")
    objective_alignment["decision"] = (
        "source_only_rolling_paired_candidate_ready"
        if rolling_paired_policy_research.get("policy_promotion_candidates")
        else (
            "source_only_rolling_paired_research_source_quality_blocked"
            if research_status == "source_quality_blocked"
            else "source_only_rolling_paired_research_evidence_accumulating"
        )
    )
    policy_promotion_candidates = list(
        rolling_paired_policy_research.get("policy_promotion_candidates") or []
    )
    objective_followups = [
        _fast_lifecycle_objective_followup(
            target_date=target_date,
            objective_alignment=objective_alignment,
            promotion_candidates=policy_promotion_candidates,
        )
    ]
    anchor_count_by_stage = {
        stage: sum(item.get("lifecycle_stage") == stage for item in results)
        for stage in (
            "entry",
            "entry_submit",
            "entry_partial_fill",
            "exit_submit",
            "exit_partial_fill",
            "exit",
        )
    }
    matched_anchor_count_by_stage = {
        stage: sum(
            item.get("lifecycle_stage") == stage
            and item.get("micro_context_status") == "matched"
            for item in results
        )
        for stage in (
            "entry",
            "entry_submit",
            "entry_partial_fill",
            "exit_submit",
            "exit_partial_fill",
            "exit",
        )
    }
    decision = (
        "diagnostic_attribution_ready"
        if not gaps
        else "partial_owner_or_micro_source_gap_base_tuning_unchanged"
    )
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at_kst": generated.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "clean_baseline_allowed": clean_baseline_allowed,
        "status": "pass" if not gaps else "warning",
        "decision": decision,
        "metric_contract": METRIC_CONTRACT,
        "rolling_policy_source_contract": rolling_policy_source_contract,
        "fast_lifecycle_objective_alignment": objective_alignment,
        "rolling_paired_policy_research": rolling_paired_policy_research,
        "micro_entry_confirmation": micro_entry_confirmation,
        "market_weakness_entry_response": market_weakness_response,
        "objective_followups": objective_followups,
        "policy_change_readiness": POLICY_CHANGE_READINESS_CONTRACT,
        "promotion_candidate_intake_contract": PROMOTION_CANDIDATE_INTAKE_CONTRACT,
        "policy_promotion_candidates": policy_promotion_candidates,
        "authority": {
            "decision_authority": "postclose_diagnostic_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "base_owner_tuning_continues_when_micro_missing": True,
        },
        "sources": {
            "widget": widget_sources,
            "episode": episode_sources,
            "micro_reversion": micro_source,
            "market_weakness_response": market_weakness_response["sources"],
            "market_weakness_blocked_entries": weakness_blocked_source,
        },
        "summary": {
            "dynamic_symbol_count": len(symbols),
            "widget_symbol_count": len(widget_symbols),
            "episode_profile_count": len(episode_profiles),
            "anchor_count": len(results),
            "matched_anchor_count": matched,
            "unmatched_anchor_count": len(results) - matched,
            "anchor_count_by_stage": anchor_count_by_stage,
            "matched_anchor_count_by_stage": matched_anchor_count_by_stage,
            "matched_decision_lifecycle_count": objective_alignment[
                "lifecycle_coverage"
            ]["matched_decision_lifecycle_count"],
            "producer_consumer_gap_count": len(gaps),
            "objective_followup_required_count": sum(
                row["followup_required"] is True for row in objective_followups
            ),
            "rolling_paired_policy_cohort_count": rolling_paired_policy_research[
                "summary"
            ]["cohort_count"],
            "policy_promotion_candidate_count": len(policy_promotion_candidates),
            "micro_entry_confirmation_eligible_count": (
                micro_entry_confirmation["summary"]["source_quality_eligible_count"]
            ),
            "micro_entry_confirmation_blocked_count": (
                micro_entry_confirmation["summary"]["source_quality_blocked_count"]
            ),
            "daily_cap_reallocation_observation_count": (
                micro_entry_confirmation["summary"][
                    "daily_cap_reallocation_observation_count"
                ]
            ),
            "confirmed_market_weakness_entry_count": (
                market_weakness_response["summary"]["confirmed_weakness_entry_count"]
            ),
            "market_weakness_actual_realized_comparison_count": (
                market_weakness_response["summary"]["actual_realized_comparison_count"]
            ),
        },
        "consumers": {
            "widget_postclose_tuning": {
                "mode": "next_trading_day_supplemental_diagnostic_handoff",
                "next_trading_day_owner_report_ingestion": True,
                "selection_effect": False,
                "base_policy_unchanged_on_missing": True,
                "symbols": widget_symbols,
            },
            "episode_machine_postclose_tuning": {
                "mode": "next_trading_day_supplemental_diagnostic_handoff",
                "next_trading_day_owner_report_ingestion": True,
                "selection_effect": False,
                "base_policy_unchanged_on_missing": True,
                "profiles": episode_profiles,
            },
        },
        "producer_consumer_gaps": gaps,
    }
    if is_krx_trading_day(target_day):
        collection_targets = build_collection_targets(
            report,
            generated_at=generated,
        )
        selected_collection_targets = collection_targets["selected_targets"]
        report["collection_feedback"] = {
            "schema": collection_targets["schema"],
            "effective_date": collection_targets["effective_date"],
            "status": collection_targets["status"],
            "coverage_policy": collection_targets["budget"]["coverage_policy"],
            "coverage_stage": collection_targets["budget"]["coverage_stage"],
            "runtime_registration_receipt_required": collection_targets["budget"][
                "runtime_registration_receipt_required"
            ],
            "active_owner_full_coverage": collection_targets["budget"][
                "active_owner_full_coverage"
            ],
            "active_owner_candidate_count": collection_targets["budget"][
                "active_owner_candidate_count"
            ],
            "selected_active_owner_count": collection_targets["budget"][
                "selected_active_owner_count"
            ],
            "active_owner_overflow_count": collection_targets["budget"][
                "active_owner_overflow_count"
            ],
            "selected_symbol_count": collection_targets["budget"][
                "selected_symbol_count"
            ],
            "repair_gap_selected_symbol_count": sum(
                bool(row.get("gap_classes")) for row in selected_collection_targets
            ),
            "policy_sample_selected_symbol_count": sum(
                "micro_policy_sample_accumulation"
                in (row.get("collection_reasons") or ())
                for row in selected_collection_targets
            ),
            "overflow_symbol_count": collection_targets["budget"][
                "overflow_symbol_count"
            ],
            "manual_control_exclusion_applied": False,
            "market_data_subscription_effect": True,
            "trading_runtime_effect": False,
        }
    else:
        report["collection_feedback"] = {
            "schema": COLLECTION_TARGET_SCHEMA,
            "effective_date": None,
            "status": "source_date_not_krx_trading_day_write_skipped",
            "coverage_policy": (
                "all_active_owner_symbols_then_bounded_prospective_rotation"
            ),
            "coverage_stage": "exact_date_target_manifest_selection",
            "runtime_registration_receipt_required": True,
            "active_owner_full_coverage": False,
            "active_owner_candidate_count": 0,
            "selected_active_owner_count": 0,
            "active_owner_overflow_count": 0,
            "selected_symbol_count": 0,
            "repair_gap_selected_symbol_count": 0,
            "policy_sample_selected_symbol_count": 0,
            "overflow_symbol_count": 0,
            "manual_control_exclusion_applied": False,
            "market_data_subscription_effect": False,
            "trading_runtime_effect": False,
        }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Machine Microstructure Attribution",
        "",
        f"- Target date: `{report['target_date']}`",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        "- Authority: diagnostic only; existing widget/episode policy is unchanged.",
        (
            "- Collection feedback: next-session source-only targets "
            f"`{report.get('collection_feedback', {}).get('selected_symbol_count', 0)}`; "
            "all active widget/episode owner symbols precede bounded prospective "
            "policy-sample rotation; "
            "manual-control exclusions are not applied."
        ),
        "",
        "## Coverage",
        "",
        "| Dynamic symbols | Widget symbols | Episode profiles | Anchors | Matched | Gaps |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {summary['dynamic_symbol_count']} | {summary['widget_symbol_count']} | "
            f"{summary['episode_profile_count']} | {summary['anchor_count']} | "
            f"{summary['matched_anchor_count']} | {summary['producer_consumer_gap_count']} |"
        ),
        "",
    ]
    objective = report.get("fast_lifecycle_objective_alignment")
    if isinstance(objective, dict):
        lifecycle = objective.get("lifecycle_coverage") or {}
        gross = objective.get("gross_no_slippage_diagnostic") or {}
        cost_aware = objective.get("cost_aware_owner_outcome_diagnostic") or {}
        followups = report.get("objective_followups") or []
        followup = followups[0] if followups and isinstance(followups[0], dict) else {}
        lines.extend(
            [
                "## Fast Lifecycle Objective",
                "",
                f"- Decision: `{objective.get('decision')}`",
                (
                    "- Matched unique decision lifecycles: "
                    f"`{lifecycle.get('matched_decision_lifecycle_count', 0)}`; "
                    f"entry-submit anchors: `{lifecycle.get('matched_entry_submit_anchor_count', 0)}`; "
                    f"entry-fill anchors: `{lifecycle.get('matched_entry_fill_anchor_count', 0)}`; "
                    f"exit-submit anchors: `{lifecycle.get('matched_exit_submit_anchor_count', 0)}`; "
                    f"exit anchors: `{lifecycle.get('matched_exit_anchor_count', 0)}`."
                ),
                (
                    "- Timed outcomes: "
                    f"`{lifecycle.get('timed_owner_outcome_count', 0)}`; "
                    f"completed within 180s: `{gross.get('completed_within_180s_ratio')}`."
                ),
                (
                    "- Gross/no-slippage average (diagnostic only): "
                    f"`{gross.get('avg_return_pct')}`; cost-aware owner average "
                    f"(daily diagnostic only): `{cost_aware.get('equal_weight_avg_profit_pct')}`."
                ),
                (
                    "- Completion follow-up: "
                    f"`{followup.get('state') or 'missing'}`; "
                    f"next=`{followup.get('next_action') or '-'}`; "
                    "tracked by the 21:15 approval/reminder ledger."
                ),
                "- Speed, target, cooldown, cap, quantity, re-entry, and forced-exit policy remain unchanged.",
                "",
            ]
        )
    research = report.get("rolling_paired_policy_research")
    if isinstance(research, dict):
        research_summary = research.get("summary") or {}
        lines.extend(
            [
                "## Rolling Paired Turnover Policy Research",
                "",
                f"- Status: `{research.get('status')}`; decision: `{research.get('decision')}`.",
                (
                    "- Cohorts: "
                    f"`{research_summary.get('cohort_count', 0)}`; ready candidates: "
                    f"`{research_summary.get('policy_promotion_candidate_count', 0)}`."
                ),
                (
                    "- Axis: source-only target timeout `60/120/180s`; ranking requires "
                    "positive cost-aware rolling EV/net profit, p10 and HELD guards, then "
                    "capital-efficiency improvement."
                ),
                (
                    "- Remaining evidence gaps: `"
                    + ",".join(research.get("remaining_gap_codes") or [])
                    + "`."
                ),
                "- Runtime family registration, PREOPEN apply, orders, and current owner policy remain unchanged.",
                "",
            ]
        )
    entry_confirmation = report.get("micro_entry_confirmation")
    if isinstance(entry_confirmation, dict):
        entry_summary = entry_confirmation.get("summary") or {}
        lines.extend(
            [
                "## Micro Entry Confirmation",
                "",
                (
                    "- Entry anchors: "
                    f"`{entry_summary.get('entry_anchor_count', 0)}`; source-quality "
                    f"eligible: `{entry_summary.get('source_quality_eligible_count', 0)}`; "
                    f"blocked: `{entry_summary.get('source_quality_blocked_count', 0)}`."
                ),
                (
                    "- Owner/state cohorts: "
                    f"`{entry_summary.get('owner_state_cohort_count', 0)}`; daily-cap "
                    "reallocation observations: "
                    f"`{entry_summary.get('daily_cap_reallocation_observation_count', 0)}`."
                ),
                (
                    "- The 1/3/5-second BBO and fixed-anchor ask-depletion axis is "
                    "source-only. Missing 0B/0D is an explicit source-quality block, "
                    "and widget/episode owners and entry states are not pooled."
                ),
                "- No BUY, exit, quantity, target, cooldown, or daily-cap mutation is authorized.",
                "",
            ]
        )
    weakness_response = report.get("market_weakness_entry_response")
    if isinstance(weakness_response, dict):
        weakness_summary = weakness_response.get("summary") or {}
        weakness_cumulative = weakness_response.get("clean_baseline_cumulative") or {}
        lines.extend(
            [
                "## Market-Scoped Weakness Entry Response",
                "",
                (
                    "- Confirmed-weakness entry anchors: "
                    f"`{weakness_summary.get('confirmed_weakness_entry_count', 0)}`; "
                    "actual realized comparisons: "
                    f"`{weakness_summary.get('actual_realized_comparison_count', 0)}`; "
                    "source blocked: "
                    f"`{weakness_summary.get('source_quality_blocked_count', 0)}`."
                ),
                (
                    "- Actual realized skip-vs-control incremental average: "
                    f"`{weakness_summary.get('actual_realized_source_quality_adjusted_incremental_vs_control_pct')}`."
                ),
                (
                    "- Clean-baseline cumulative: dates "
                    f"`{weakness_cumulative.get('affected_actual_realized_trading_date_count', 0)}`; "
                    "comparisons "
                    f"`{weakness_cumulative.get('affected_actual_realized_comparison_count', 0)}`; "
                    "average/p10 "
                    f"`{weakness_cumulative.get('incremental_vs_control_avg_pct')}` / "
                    f"`{weakness_cumulative.get('incremental_vs_control_p10_pct')}`; "
                    "source-only review ready "
                    f"`{weakness_cumulative.get('source_only_review_ready', False)}`."
                ),
                (
                    "- KOSPI/KOSDAQ listing market and two-observation activation / "
                    "three-observation release are reconstructed from past-only "
                    "schema-v2 observations."
                ),
                "- Response arms are source-only; no entry block, cancel, target, holding, exit, price, or quantity authority exists.",
                "",
            ]
        )
    lines.extend(["## Producer/Consumer Gaps", ""])
    gaps = report["producer_consumer_gaps"]
    if not gaps:
        lines.append("- None")
    else:
        lines.extend(
            [
                "| Owner | Scope | Symbol | Gap | Effect |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for gap in gaps:
            lines.append(
                f"| {gap.get('owner')} | {gap.get('scope_id') or gap.get('source')} | "
                f"{gap.get('symbol') or '-'} | {gap.get('gap_class')} | "
                f"{gap.get('effect') or 'micro context unavailable'} |"
            )
    lines.extend(
        [
            "",
            "Missing micro data is not imputed as zero return and does not stop the existing owner tuning path.",
            "",
            "## Policy Change Boundary",
            "",
            (
                "This daily report cannot change policy. Policy review opens only after "
                "5 observed trading days, 20 matched unique owner/symbol/session decision lifecycles, "
                "BBO coverage >=95%, depth coverage >=90%, and a cost-adjusted paired "
                "5/10/20-day EV improvement with no downside deterioration."
            ),
            (
                "The first runtime linkage still requires a new bounded family mapping "
                "and explicit operator approval; any approved candidate applies PREOPEN only."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    target_date = report["target_date"]
    json_path = output_dir / f"{REPORT_TYPE}_{target_date}.json"
    markdown_path = output_dir / f"{REPORT_TYPE}_{target_date}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--report-root", type=Path, default=DATA_DIR / "report")
    parser.add_argument("--observation-root", type=Path, default=OBSERVATION_ROOT)
    parser.add_argument(
        "--source-exclusion-manifest",
        type=Path,
        default=DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    )
    parser.add_argument(
        "--canary-snapshot",
        type=Path,
        default=DEFAULT_CANARY_SNAPSHOT_PATH,
    )
    parser.add_argument(
        "--canary-snapshot-dir",
        type=Path,
        default=CANARY_DAILY_SNAPSHOT_DIR,
    )
    parser.add_argument(
        "--widget-state",
        type=Path,
        default=None,
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--collection-target-root",
        type=Path,
        default=None,
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else resolve_completed_machine_target_date()
    )
    canary_snapshot = resolve_target_canary_snapshot(
        target_date=target_date,
        latest_path=args.canary_snapshot,
        daily_root=args.canary_snapshot_dir,
    )
    if args.write and args.canary_snapshot is not None:
        archived_canary = archive_exact_date_canary_snapshot(
            target_date=target_date,
            source_path=args.canary_snapshot,
            daily_root=args.canary_snapshot_dir,
        )
        if archived_canary is not None:
            canary_snapshot = archived_canary
    report = build_report(
        target_date.isoformat(),
        report_root=args.report_root,
        observation_root=args.observation_root,
        source_exclusion_manifest_path=args.source_exclusion_manifest,
        canary_snapshot_path=canary_snapshot,
        canary_snapshot_dir=args.canary_snapshot_dir,
        widget_state_path=args.widget_state,
    )
    if args.write:
        write_report(report, args.output_dir)
        if is_krx_trading_day(target_date):
            collection_payload = build_collection_targets(report)
            if args.collection_target_root is None:
                write_collection_targets(collection_payload)
            else:
                write_collection_targets(
                    collection_payload,
                    root=args.collection_target_root,
                )
    if args.print_summary or not args.write:
        print(
            json.dumps(
                {"status": report["status"], **report["summary"]}, ensure_ascii=False
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
