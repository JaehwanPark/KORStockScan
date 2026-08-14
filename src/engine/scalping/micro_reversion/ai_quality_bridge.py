"""Past-only micro-reversion sidecar for Exact V2 AI quality replay.

This module deliberately stays outside the live AI and order paths.  It joins
immutable Exact V2 request provenance to already-persisted 0B/0D observations,
builds a compact tactical context, and keeps future outcomes in a separate
label.  The original provider payload and its hash are never modified.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import tempfile
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.utils.constants import DATA_DIR

from .contracts import CLEAN_BASELINE_DATE, normalize_symbol, normalize_venue
from .depth_join import validate_depth_row
from .onset_quality import reconstruct_shock_onset_context
from .p2_replay import (
    DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    P2ReplayPoint,
    load_source_exclusion_manifest,
)
from .path_journal import (
    MARKET_STREAM_CONTRACT_ID,
    readable_partition_path_files,
    validate_market_stream_path_provenance,
)
from .path_capture import PATH_CAPTURE_AUTHORITY

TACTICAL_EVIDENCE_SCHEMA = "tactical_micro_reversion_evidence_v1"
LIFECYCLE_PROJECTION_SCHEMA = "micro_reversion_fast_lifecycle_projection_v1"
OUTCOME_SCHEMA = "micro_reversion_ai_quality_outcome_v1"
THREE_ARM_SCHEMA = "micro_reversion_ai_quality_three_arm_manifest_v1"
REPORT_SCHEMA = "micro_reversion_ai_quality_bridge_v1"

MARKET_SCHEMAS = {
    "scalp_micro_reversion_market_stream_point_v1",
    "scalp_micro_reversion_market_stream_point_v2",
    "scalp_micro_reversion_market_stream_point_v3",
}
MARKET_CONTRACT_BY_SCHEMA = {
    "scalp_micro_reversion_market_stream_point_v1": (
        "scalp_micro_reversion_market_stream_contract_v1"
    ),
    "scalp_micro_reversion_market_stream_point_v2": (
        "scalp_micro_reversion_market_stream_contract_v2"
    ),
    "scalp_micro_reversion_market_stream_point_v3": MARKET_STREAM_CONTRACT_ID,
}
DEPTH_SCHEMA = "scalp_micro_reversion_market_depth_point_v1"
EVENT_REFERENCE_SCHEMA = "scalp_micro_reversion_path_event_reference_v2"
TRACE_SCHEMA = "ai_decision_trace_v1"
PAYLOAD_SCHEMA = "ai_decision_payload_v1"
INPUT_BUNDLE_VERSION = "scalping_multi_timeframe_context_v1"
ENTRY_CONTEXT_SCHEMA = "entry_candle_context_v1"
HOLDING_CONTEXT_SCHEMA = "holding_decision_context_v1"

METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "ai_decision_quality_tactical_microstructure_context",
    "decision_authority": "offline_paired_replay_context_only_no_runtime_change",
    "window_policy": (
        "latest_past_same_symbol_venue_session_sequence_epoch_at_or_before_"
        "exact_snapshot_watermark"
    ),
    "sample_floor": (
        "one_valid_row_starts_cumulative_observation_aggregate_promotion_floor_"
        "owned_by_research_gate"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_v2_scope_nonfuture_monotonic_fresh_bbo_and_same_basis_depth_"
        "for_economic_capacity_no_imputation"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "live_buy_tp_stop_trailing_or_threshold_change",
        "provider_or_bot_change",
        "position_sizing_owner_or_cap_replacement",
        "broker_account_order_stale_cooldown_or_hard_safety_bypass",
        "future_cross_symbol_cross_venue_cross_session_or_cross_epoch_join",
        "missing_quote_tape_or_depth_imputation",
        "depth_or_touch_as_real_fill",
        "machine_or_widget_future_performance_as_prompt_input",
        "counterfactual_and_realized_pnl_merge",
    ),
}

AUTHORITY_CONTRACT: dict[str, Any] = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "selection_authority": False,
}

OUTCOME_METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "counterfactual_outcome_label",
    "decision_authority": "offline_outcome_evaluation_only_no_runtime_change",
    "window_policy": (
        "post_snapshot_same_symbol_venue_session_sequence_epoch_mature_"
        "quantity_sweep_path"
    ),
    "sample_floor": "one_mature_row_starts_cumulative_offline_evaluation",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "mature_endpoint_continuous_sequence_fresh_bbo_same_basis_depth_"
        "full_quantity_coverage"
    ),
    "forbidden_uses": (
        "prompt_input",
        "live_runtime_apply",
        "realized_and_counterfactual_pnl_merge",
        "unverified_cost_profile_promotion",
    ),
}

REPORT_METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "ai_decision_quality_micro_reversion_bridge_report",
    "decision_authority": "offline_report_only_no_runtime_change",
    "window_policy": (
        "exact_snapshot_parent_wave_stage_deduplicated_with_separate_"
        "post_snapshot_outcomes"
    ),
    "sample_floor": "one_eligible_parent_wave_stage_row_starts_cumulative_report",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_context_and_control_response_and_mature_outcome_reported_separately"
    ),
    "forbidden_uses": (
        "direct_live_promotion",
        "provider_or_order_mutation",
        "unverified_cost_profile_as_economic_authority",
    ),
}

# These are the only deterministic, past-only ledgers currently emitted by the
# existing paired-replay request builders.  The bridge validates each ledger's
# declared schema and content hash before preserving it; arbitrary sibling
# objects are never forwarded to a provider.
REPLAY_CANDIDATE_LEDGER_SCHEMAS = frozenset(
    {
        "exact_payload_analysis_v1",
        "anticipatory_reversal_analysis_v1",
        "entry_setup_evidence_v1",
        "entry_price_exact_contract_facts_v1",
        "holding_exact_contract_facts_v1",
    }
)

REPLAY_CANDIDATE_LEDGER_FIELDS: dict[str, frozenset[str]] = {
    "exact_payload_analysis_v1": frozenset(
        {
            "schema",
            "stage",
            "completed_structure",
            "contradictions",
            "deterministic_contract_facts",
            "executable_liquidity",
            "observation_contract",
            "program_flow",
            "source_quality",
            "tape_sample",
            "trigger_state",
            "volume_confirmation",
            "analysis_sha256",
        }
    ),
    "anticipatory_reversal_analysis_v1": frozenset(
        {
            "schema",
            "stage",
            "bounded_opportunity",
            "clean_continuation_probe",
            "confidence_cap",
            "eligible_for_counterfactual_probe",
            "execution_cost",
            "execution_policy",
            "freshness",
            "hard_blockers",
            "learning_contract",
            "observation_contract",
            "precursors",
            "recovery_confirmation_probe",
            "selective_recovery_probe",
            "source_mode",
            "spread",
            "analysis_sha256",
        }
    ),
    "entry_setup_evidence_v1": frozenset(
        {
            "schema",
            "version",
            "setup_family",
            "setup_state",
            "structure_phase",
            "structure_phase_bar_end",
            "structure_phase_policy_version",
            "structure_phase_role",
            "structure_phase_sha256",
            "structure_phase_stable_on_completed_bar",
            "positive_facts",
            "contradicting_facts",
            "invalidation_facts",
            "corroborated_risk_codes",
            "recheck_reasons",
            "context_observations",
            "tail_risk_assessment",
            "execution_readiness_role",
            "execution_readiness_state",
            "symbol_specific_branching",
            "widget_dependency",
            "source_quality",
            "evidence_sha256",
            "metric_role",
            "decision_authority",
            "window_policy",
            "sample_floor",
            "primary_decision_metric",
            "source_quality_gate",
            "forbidden_uses",
            "observation_contract",
            "runtime_effect",
            "allowed_runtime_apply",
            "actual_order_submitted",
            "broker_order_forbidden",
        }
    ),
    "entry_price_exact_contract_facts_v1": frozenset(
        {
            "schema",
            "available_price_count",
            "candidate_prices",
            "control_exposure_selected",
            "control_selected_price",
            "economically_distinct_bases",
            "fresh_quote",
            "max_incremental_chase_cost_bp",
            "minimum_reward_risk_for_aggressive_basis",
            "minimum_upside_for_aggressive_basis_pct",
            "price_cost_baseline",
            "price_delta_from_cost_baseline_bp",
            "setup_invalidated",
            "skip_permitted",
            "skip_reasons",
            "source_blockers",
            "spread_bp",
            "would_fill_now",
        }
    ),
    "holding_exact_contract_facts_v1": frozenset(
        {
            "schema",
            "allowed_worsen_pct",
            "average_entry_price",
            "bbo_fresh",
            "bounded_defer_authority",
            "bounded_defer_checkpoint_horizons_sec",
            "bounded_defer_eligible",
            "candidate_exit_rule",
            "candle_status",
            "completed_bar_count",
            "completed_bars_observed",
            "executable_sell_price",
            "fresh_consistent_core",
            "hard_exit_guard_observed",
            "open_sell_qty",
            "broker_reconciliation_contract_complete",
            "order_consistent",
            "position_observed",
            "position_reconciled",
            "position_valid",
            "remaining_qty",
            "sell_order_or_exit_token_active",
            "soft_exit_candidate",
            "source_quality_status",
            "trim_available",
        }
    ),
}

OUTCOME_ONLY_FIELD_NAMES = frozenset(
    {
        "horizons",
        "first_hit",
        "mfe",
        "mae",
        "future_outcome",
        "outcome_label",
        "target_first",
        "adverse_first",
        "realized_pnl",
        "realized_profit",
        "profit_rate",
        "post_decision_mfe",
        "post_decision_mae",
        "counterfactual_net_mfe_bps",
        "counterfactual_net_mae_bps",
    }
)


@dataclass(frozen=True, slots=True)
class BridgeConfig:
    context_lookback_sec: int = 30
    active_wave_max_age_sec: int = 180
    max_market_age_ms: int = 2_500
    max_depth_age_ms: int = 1_000
    max_quote_age_ms: int = 1_000
    tape_capacity_window_sec: int = 10
    target_liquidation_sec: int = 10
    participation_grid: tuple[float, ...] = (0.02, 0.05, 0.10)
    max_entry_sweep_slippage_bps: float = 10.0
    max_exit_sweep_slippage_bps: float = 10.0
    buy_fee_bps: float = 0.0
    sell_fee_bps: float = 0.0
    statutory_sell_tax_bps: float | None = None
    uncertainty_buffer_bps: float = 3.0
    minimum_net_profit_bps: float = 5.0
    adverse_label_bps: float = -70.0
    max_outcome_endpoint_lag_ms: int = 2_500
    max_outcome_internal_gap_ms: int = 2_500
    outcome_horizons_sec: tuple[int, ...] = (1, 3, 5, 10, 20, 30, 60, 120, 180)
    cost_profile_source: str = "missing_verified_instrument_cost_profile"
    cost_profile_verified: bool = False

    def __post_init__(self) -> None:
        if self.context_lookback_sec <= 0 or self.active_wave_max_age_sec <= 0:
            raise ValueError("context windows must be positive")
        if (
            self.max_market_age_ms < 0
            or self.max_depth_age_ms < 0
            or self.max_quote_age_ms < 0
        ):
            raise ValueError("freshness limits must not be negative")
        if self.tape_capacity_window_sec <= 0 or self.target_liquidation_sec <= 0:
            raise ValueError("liquidation windows must be positive")
        if (
            not self.participation_grid
            or tuple(sorted(set(self.participation_grid)))
            != self.participation_grid
            or any(not 0 < value <= 1 for value in self.participation_grid)
        ):
            raise ValueError("participation_grid must be sorted, unique, and in (0,1]")
        for field in (
            "max_entry_sweep_slippage_bps",
            "max_exit_sweep_slippage_bps",
            "buy_fee_bps",
            "sell_fee_bps",
            "uncertainty_buffer_bps",
            "minimum_net_profit_bps",
        ):
            if getattr(self, field) < 0:
                raise ValueError(f"{field} must not be negative")
        if self.statutory_sell_tax_bps is not None and (
            self.statutory_sell_tax_bps < 0
        ):
            raise ValueError("statutory_sell_tax_bps must not be negative")
        if self.cost_profile_verified and (
            self.statutory_sell_tax_bps is None
            or not str(self.cost_profile_source or "").strip()
            or str(self.cost_profile_source).startswith(("missing_", "operator_"))
        ):
            raise ValueError(
                "verified cost profile requires complete non-operator source"
            )
        if self.adverse_label_bps >= 0:
            raise ValueError("adverse_label_bps must be negative")
        if (
            self.max_outcome_endpoint_lag_ms < 0
            or self.max_outcome_internal_gap_ms <= 0
        ):
            raise ValueError("outcome continuity limits are invalid")
        if (
            not self.outcome_horizons_sec
            or tuple(sorted(set(self.outcome_horizons_sec)))
            != self.outcome_horizons_sec
            or self.outcome_horizons_sec[0] <= 0
        ):
            raise ValueError("outcome horizons must be sorted unique positive values")


@dataclass(frozen=True, slots=True)
class ResolvedMicroScope:
    venue: str
    session_bucket: str
    status: str
    reason: str | None = None


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _producer_sha256(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _stored_semantic_sha256(value: Any) -> str:
    """Hash the sanitized stored value with the trace producer's byte rules."""

    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _positive_float(value: Any) -> float | None:
    result = _finite_float(value)
    return result if result is not None and result > 0 else None


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _parse_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def _timestamp_ms(value: Any) -> int:
    return int(_parse_timestamp(value).timestamp() * 1_000)


def _timestamp_us(value: Any) -> int:
    return int(_parse_timestamp(value).timestamp() * 1_000_000)


def _session(value: Any) -> str:
    return str(value or "").strip().upper()


def _route(value: Any) -> str:
    return str(value or "").strip().lower()


def _exact_venue(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw == "PREMARKET_KRX_LIKE":
        return raw
    return normalize_venue(raw)


def resolve_micro_scope(trace: Mapping[str, Any]) -> ResolvedMicroScope:
    """Map an Exact V2 route to one explicit persisted micro partition."""

    venue = normalize_venue(trace.get("effective_venue"))
    raw_venue = str(trace.get("effective_venue") or "").strip().upper()
    session = _session(trace.get("session_bucket"))
    market_route = _route(trace.get("market_data_route"))
    if "sor" in market_route or "integrated" in market_route:
        micro_venue = "SOR"
    elif market_route in {"krx", "krx_only", "krx_regular"}:
        micro_venue = "KRX"
    elif market_route in {"nxt", "nxt_only", "nxt_regular"}:
        micro_venue = "NXT"
    elif raw_venue == "PREMARKET_KRX_LIKE" or session == "PREMARKET_KRX_LIKE":
        return ResolvedMicroScope(
            "UNKNOWN",
            "UNKNOWN",
            "source_unavailable",
            "premarket_route_ambiguous",
        )
    else:
        micro_venue = venue
    if micro_venue == "UNKNOWN":
        return ResolvedMicroScope(
            "UNKNOWN",
            "UNKNOWN",
            "source_unavailable",
            "effective_venue_missing",
        )
    if "PREMARKET" in session:
        phase = "PREMARKET"
    elif "AFTERMARKET" in session:
        phase = "AFTERMARKET"
    elif "REGULAR" in session or "OVERLAP" in session:
        phase = "REGULAR_OVERLAP" if micro_venue == "NXT" else "REGULAR"
    else:
        return ResolvedMicroScope(
            micro_venue,
            session or "UNKNOWN",
            "source_unavailable",
            "venue_session_mapping_missing",
        )
    return ResolvedMicroScope(
        micro_venue,
        f"{micro_venue}_{phase}",
        "resolved",
    )


def _walk_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child)


def _stored_replay_exact_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    source = (
        payload.get("sanitized_replay_context")
        if payload.get("replay_context_present") is True
        else payload.get("sanitized_user_input")
    )
    if not isinstance(source, dict):
        return None
    nested = source.get("exact_payload")
    if isinstance(nested, dict) and (
        "exact_payload_analysis_v1" in source
        or str(source.get("input_schema") or "").startswith("decision_quality_")
        or TACTICAL_EVIDENCE_SCHEMA in source
    ):
        return nested
    return source


def _expected_context_schema(trace: Mapping[str, Any]) -> str | None:
    stage = str(
        trace.get("decision_stage") or trace.get("endpoint") or ""
    ).strip().lower()
    if stage in {
        "entry",
        "entry_screen",
        "analyze_target",
        "entry_price",
        "post_probe",
    }:
        return ENTRY_CONTEXT_SCHEMA
    if stage in {
        "holding",
        "holding_score",
        "holding_flow",
        "scale_in",
        "exit",
        "overnight",
    }:
        return HOLDING_CONTEXT_SCHEMA
    return None


def _canonical_context_findings(
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    exact_payload: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Verify the stored context instead of trusting trace summary strings."""

    findings: list[str] = []
    expected_schema = _expected_context_schema(trace)
    if expected_schema is None:
        return ("decision_stage_context_schema_unknown",)
    capture = payload.get("canonical_context_capture")
    if not isinstance(capture, Mapping):
        findings.append("canonical_context_capture_missing")
    else:
        if capture.get("status") != "exact_completed_bars_captured":
            findings.append("canonical_context_capture_not_exact")
        if capture.get("schema") != expected_schema:
            findings.append("canonical_context_capture_schema_mismatch")
        if capture.get("input_bundle_version") != INPUT_BUNDLE_VERSION:
            findings.append("canonical_context_capture_bundle_mismatch")
        if (_nonnegative_int(capture.get("raw_bar_count")) or 0) <= 0:
            findings.append("canonical_context_capture_raw_bars_missing")
        if (_nonnegative_int(capture.get("completed_bar_count")) or 0) <= 0:
            findings.append("canonical_context_capture_completed_bars_missing")

    owner_keys = (
        ("entry_candle_context", "entry_candle_context_v1")
        if expected_schema == ENTRY_CONTEXT_SCHEMA
        else ("holding_decision_context", "holding_decision_context_v1")
    )
    owner_contexts = []
    owner_roots = [exact_payload] if isinstance(exact_payload, Mapping) else []
    nested_exact = (
        exact_payload.get("exact_payload")
        if isinstance(exact_payload, Mapping)
        else None
    )
    if isinstance(nested_exact, Mapping):
        owner_roots.append(nested_exact)
    for owner_root in owner_roots:
        if owner_root.get("schema") == expected_schema:
            owner_contexts.append(owner_root)
        for key in owner_keys:
            candidate = owner_root.get(key)
            if isinstance(candidate, Mapping) and candidate.get("schema") == expected_schema:
                owner_contexts.append(candidate)
    owner_by_hash = {_sha256(row): row for row in owner_contexts}
    contexts = list(owner_by_hash.values())
    if not contexts:
        recursive_by_hash = {
            _sha256(row): row
            for row in _walk_objects(exact_payload)
            if row.get("schema") == expected_schema
        }
        contexts = list(recursive_by_hash.values())
    if len(contexts) != 1:
        findings.append(
            "canonical_context_missing"
            if not contexts
            else "canonical_context_ambiguous"
        )
        return tuple(sorted(set(findings)))
    context = contexts[0]
    candle = (
        context.get("candle")
        if expected_schema == HOLDING_CONTEXT_SCHEMA
        else context
    )
    if not isinstance(candle, Mapping):
        findings.append("canonical_candle_context_missing")
        return tuple(sorted(set(findings)))
    if candle.get("input_bundle_version") != INPUT_BUNDLE_VERSION:
        findings.append("canonical_context_bundle_mismatch")
    bars = candle.get("bars")
    if not isinstance(bars, list) or not bars:
        findings.append("canonical_raw_bars_missing")
    else:
        forming_key = (
            "is_forming"
            if expected_schema == HOLDING_CONTEXT_SCHEMA
            else "forming"
        )
        completed_count = sum(
            isinstance(bar, Mapping)
            and forming_key in bar
            and bar.get(forming_key) is False
            for bar in bars
        )
        if completed_count <= 0:
            findings.append("canonical_completed_bars_missing")
        if isinstance(capture, Mapping) and (
            _nonnegative_int(capture.get("raw_bar_count")) != len(bars)
            or _nonnegative_int(capture.get("completed_bar_count"))
            != completed_count
        ):
            findings.append("canonical_context_capture_count_mismatch")
    trace_venue = _exact_venue(trace.get("effective_venue"))
    trace_session = _session(trace.get("session_bucket"))
    scope_context = (
        context if expected_schema == HOLDING_CONTEXT_SCHEMA else candle
    )
    if _exact_venue(scope_context.get("venue")) != trace_venue:
        findings.append("canonical_context_venue_mismatch")
    if _session(scope_context.get("session")) != trace_session:
        findings.append("canonical_context_session_mismatch")
    return tuple(sorted(set(findings)))


def exact_snapshot_watermark(
    trace: Mapping[str, Any], payload: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Return the unique exact market snapshot that precedes provider latency."""

    blockers: list[str] = []
    if trace.get("schema") != TRACE_SCHEMA:
        blockers.append("trace_schema_invalid")
    if payload.get("schema") != PAYLOAD_SCHEMA:
        blockers.append("payload_schema_invalid")
    for trace_field, payload_field in (
        ("payload_sha256", "payload_sha256"),
        ("request_envelope_sha256", "request_envelope_sha256"),
    ):
        if not trace.get(trace_field) or trace.get(trace_field) != payload.get(
            payload_field
        ):
            blockers.append(f"{trace_field}_mismatch")
    if trace.get("payload_replay_exact") is not True:
        blockers.append("trace_payload_not_exact")
    if trace.get("request_capture_status") != "captured":
        blockers.append("request_not_captured")
    if payload.get("replay_exact") is not True:
        blockers.append("payload_store_not_exact")
    sanitized_user_input = payload.get("sanitized_user_input")
    input_format = str(payload.get("input_format") or "")
    stored_semantic_hash = str(
        payload.get("sanitized_user_input_sha256") or ""
    )
    trace_semantic_hash = str(trace.get("payload_semantic_sha256") or "")
    provider_semantic_verified = False
    if stored_semantic_hash:
        if _stored_semantic_sha256(sanitized_user_input) != stored_semantic_hash:
            blockers.append("provider_payload_semantic_sha256_mismatch")
        if not trace_semantic_hash:
            blockers.append("trace_payload_semantic_sha256_missing")
        elif trace_semantic_hash != stored_semantic_hash:
            blockers.append("trace_payload_semantic_sha256_mismatch")
        else:
            provider_semantic_verified = True
    elif trace_semantic_hash:
        blockers.append("payload_semantic_sha256_missing")
    recomputed_provider_hash = None
    if input_format == "structured":
        recomputed_provider_hash = _producer_sha256(sanitized_user_input)
    elif input_format == "plain_text" and isinstance(sanitized_user_input, str):
        recomputed_provider_hash = hashlib.sha256(
            sanitized_user_input.encode("utf-8")
        ).hexdigest()
    if recomputed_provider_hash is not None and recomputed_provider_hash != str(
        payload.get("payload_sha256") or ""
    ):
        blockers.append("provider_payload_content_sha256_mismatch")
    elif recomputed_provider_hash is not None:
        provider_semantic_verified = True
    trace_replay_present = trace.get("replay_context_present") is True
    payload_replay_present = payload.get("replay_context_present") is True
    if trace_replay_present != payload_replay_present:
        blockers.append("replay_context_presence_mismatch")
    if payload_replay_present and (
        payload.get("replay_context_exact") is not True
        or trace.get("replay_context_exact") is not True
    ):
        blockers.append("replay_context_not_exact")
    if payload_replay_present:
        payload_replay_hash = str(payload.get("replay_context_sha256") or "")
        trace_replay_hash = str(trace.get("replay_context_sha256") or "")
        replay_source = payload.get("sanitized_replay_context")
        replay_input_format = str(payload.get("replay_context_input_format") or "")
        raw_replay_hash_recomputable = replay_input_format in {
            "structured",
            "plain_text",
        }
        replay_semantic_verified = False
        if (
            not payload_replay_hash
            or trace_replay_hash != payload_replay_hash
            or replay_source is None
            or (
                raw_replay_hash_recomputable
                and _stored_semantic_sha256(replay_source) != payload_replay_hash
            )
        ):
            blockers.append("replay_context_sha256_mismatch")
        else:
            replay_semantic_verified = raw_replay_hash_recomputable
        stored_replay_semantic_hash = str(
            payload.get("sanitized_replay_context_sha256") or ""
        )
        trace_replay_semantic_hash = str(
            trace.get("replay_context_semantic_sha256") or ""
        )
        if stored_replay_semantic_hash:
            if (
                replay_source is None
                or _stored_semantic_sha256(replay_source)
                != stored_replay_semantic_hash
            ):
                blockers.append("replay_context_semantic_sha256_mismatch")
            if not trace_replay_semantic_hash:
                blockers.append("trace_replay_context_semantic_sha256_missing")
            elif trace_replay_semantic_hash != stored_replay_semantic_hash:
                blockers.append("trace_replay_context_semantic_sha256_mismatch")
            else:
                replay_semantic_verified = True
        if trace_replay_semantic_hash and not stored_replay_semantic_hash:
            blockers.append("payload_replay_context_semantic_sha256_missing")
    else:
        replay_semantic_verified = False
    provider_semantic_hash_status = (
        "stored_semantic_hash_verified"
        if provider_semantic_verified
        else "stored_semantic_hash_unverifiable_legacy"
    )
    exact_replay_source_semantic_status = (
        "stored_semantic_hash_verified"
        if (
            replay_semantic_verified
            if payload_replay_present
            else provider_semantic_verified
        )
        else "stored_semantic_hash_unverifiable_legacy"
    )
    envelope = {
        "endpoint": str(payload.get("endpoint") or "generic"),
        "model": str(payload.get("model") or "-"),
        "schema_name": str(payload.get("schema_name") or "-"),
        "require_json": bool(payload.get("require_json")),
        "temperature": payload.get("temperature"),
        "max_output_tokens": payload.get("max_output_tokens"),
        "reasoning_effort": payload.get("reasoning_effort"),
        "prompt_sha256": payload.get("prompt_sha256"),
        "user_input_sha256": payload.get("payload_sha256"),
    }
    if payload_replay_present:
        envelope["replay_context_sha256"] = payload.get("replay_context_sha256")
    if _producer_sha256(envelope) != str(
        payload.get("request_envelope_sha256") or ""
    ):
        blockers.append("request_envelope_content_sha256_mismatch")
    if str(trace.get("input_preflight_mode") or "") != "exact_v2":
        blockers.append("input_preflight_not_exact_v2")
    if trace.get("input_preflight_allowed") is not True:
        blockers.append("input_preflight_not_allowed")
    if trace.get("venue_consistent") is not True:
        blockers.append("venue_not_consistent")
    if trace.get("input_blockers"):
        blockers.append("input_blockers_present")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        blockers.append("provider_none")
    trace_simulation = bool(
        str(trace.get("sim_record_id") or "").strip()
        or str(trace.get("sim_parent_record_id") or "").strip()
        or str(trace.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
    )
    payload_simulation = bool(
        str(payload.get("sim_record_id") or "").strip()
        or str(payload.get("sim_parent_record_id") or "").strip()
        or str(payload.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
    )
    if trace_simulation or payload_simulation or str(
        trace.get("position_reconciliation_mode") or ""
    ).strip() == "simulation_book":
        blockers.append("simulation_observation_not_natural_cohort")
    if trace_simulation != payload_simulation:
        blockers.append("simulation_provenance_trace_payload_mismatch")
    if str(trace.get("canonical_context_capture_status") or "") != (
        "exact_completed_bars_captured"
    ):
        blockers.append("canonical_completed_bars_not_captured")
    exact_payload = _stored_replay_exact_payload(payload)
    blockers.extend(_canonical_context_findings(trace, payload, exact_payload))
    source = (
        payload.get("sanitized_replay_context")
        if payload.get("replay_context_present") is True
        else payload.get("sanitized_user_input")
    )
    trace_symbol = normalize_symbol(trace.get("stock_code"))
    snapshots = []
    snapshot_objects = [
        row
        for row in _walk_objects(source)
        if row.get("schema") == "ai_market_snapshot_v1"
    ]
    for row in snapshot_objects:
        snapshot_symbol = normalize_symbol(row.get("stock_code"))
        if not snapshot_symbol:
            blockers.append("exact_market_snapshot_symbol_missing")
            continue
        if trace_symbol and snapshot_symbol != trace_symbol:
            blockers.append("exact_market_snapshot_cross_symbol_present")
            continue
        try:
            captured_at_ms = _timestamp_ms(row.get("captured_at"))
            captured_at_us = _timestamp_us(row.get("captured_at"))
        except (TypeError, ValueError):
            blockers.append("exact_market_snapshot_timestamp_invalid")
            continue
        snapshots.append((captured_at_ms, captured_at_us, row))
    unique = {
        (captured_ms, captured_us, _sha256(row)): row
        for captured_ms, captured_us, row in snapshots
    }
    if not unique:
        blockers.append("exact_market_snapshot_missing")
        return None, tuple(sorted(set(blockers)))
    if len(unique) != 1:
        blockers.append("exact_market_snapshot_ambiguous")
        return None, tuple(sorted(set(blockers)))
    (captured_at_ms, captured_at_us, _), snapshot = next(iter(unique.items()))
    try:
        decision_us = _timestamp_us(trace.get("decision_ts"))
    except (TypeError, ValueError):
        blockers.append("trace_decision_timestamp_invalid")
    else:
        if captured_at_us > decision_us:
            blockers.append("snapshot_after_ai_decision")
    snapshot_venue = str(snapshot.get("effective_venue") or "").strip().upper()
    snapshot_session = _session(snapshot.get("session_bucket"))
    trace_venue = str(trace.get("effective_venue") or "").strip().upper()
    trace_session = _session(trace.get("session_bucket"))
    if not snapshot_venue or snapshot_venue != trace_venue:
        blockers.append("snapshot_effective_venue_mismatch")
    if not snapshot_session or snapshot_session != trace_session:
        blockers.append("snapshot_session_bucket_mismatch")
    trace_snapshot_id = str(trace.get("snapshot_id") or "").strip()
    snapshot_id = str(snapshot.get("snapshot_id") or "").strip()
    if not trace_snapshot_id or not snapshot_id or snapshot_id != trace_snapshot_id:
        blockers.append("snapshot_id_mismatch")
    payload_venue = _exact_venue(payload.get("effective_venue"))
    payload_session = _session(payload.get("session_bucket"))
    if normalize_symbol(payload.get("symbol")) != trace_symbol:
        blockers.append("payload_trace_symbol_mismatch")
    if str(payload.get("snapshot_id") or "").strip() != trace_snapshot_id:
        blockers.append("payload_trace_snapshot_id_mismatch")
    if str(payload.get("endpoint") or "").strip() != str(
        trace.get("endpoint") or ""
    ).strip():
        blockers.append("payload_trace_endpoint_mismatch")
    requested_model = str(
        trace.get("model_requested") or trace.get("model") or ""
    ).strip()
    if requested_model and str(payload.get("model") or "").strip() != requested_model:
        blockers.append("payload_trace_requested_model_mismatch")
    if str(payload.get("prompt_sha256") or "") != str(
        trace.get("prompt_sha256") or ""
    ):
        blockers.append("payload_trace_prompt_sha256_mismatch")
    if payload_venue != _exact_venue(trace.get("effective_venue")):
        blockers.append("payload_trace_venue_mismatch")
    if payload_session != trace_session:
        blockers.append("payload_trace_session_mismatch")
    trace_route = _route(trace.get("market_data_route"))
    snapshot_route = _route(snapshot.get("market_data_route"))
    payload_route = _route(payload.get("market_data_route"))
    if not trace_route or snapshot_route != trace_route:
        blockers.append("snapshot_market_data_route_mismatch")
    if payload_route != trace_route:
        blockers.append("payload_trace_market_data_route_mismatch")
    if ("integrated" in trace_route or "sor" in trace_route) and not (
        snapshot.get("integrated_sor_route_proven") is True
        or snapshot.get("nxt_integrated_execution_view_proven") is True
    ):
        blockers.append("integrated_route_proof_missing")
    trace_broker_route = str(trace.get("broker_route") or "").strip().upper()
    snapshot_broker_route = str(snapshot.get("broker_route") or "").strip().upper()
    payload_broker_route = str(payload.get("broker_route") or "").strip().upper()
    if not trace_broker_route or snapshot_broker_route != trace_broker_route:
        blockers.append("snapshot_broker_route_mismatch")
    if payload_broker_route != trace_broker_route:
        blockers.append("payload_trace_broker_route_mismatch")
    snapshot_simulation = bool(
        str(snapshot.get("sim_record_id") or "").strip()
        or str(snapshot.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
        or snapshot.get("simulation_position_reconciled") is True
    )
    if snapshot_simulation:
        blockers.append("simulation_snapshot_not_natural_cohort")
    return {
        "snapshot_id": snapshot.get("snapshot_id") or trace.get("snapshot_id"),
        "captured_at": snapshot.get("captured_at"),
        "captured_at_ms": captured_at_ms,
        "captured_at_us": captured_at_us,
        "stock_code": trace_symbol,
        "effective_venue": snapshot_venue,
        "session_bucket": snapshot_session,
        "provider_payload_semantic_hash_status": provider_semantic_hash_status,
        "exact_replay_source_semantic_status": (
            exact_replay_source_semantic_status
        ),
    }, tuple(sorted(set(blockers)))


def _valid_market_row(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    expected_contract = MARKET_CONTRACT_BY_SCHEMA.get(str(row.get("schema") or ""))
    if expected_contract is None or row.get("metric_contract_id") != expected_contract:
        return False, "market_schema_invalid"
    if (
        row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
        or row.get("trading_runtime_effect") is not False
    ):
        return False, "market_authority_invalid"
    for field in ("trade_price", "best_bid", "best_ask"):
        value = row.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            return False, "market_numeric_contract_invalid"
    trade_qty = row.get("trade_qty")
    if trade_qty is not None and (
        isinstance(trade_qty, bool)
        or not isinstance(trade_qty, int)
        or trade_qty < 0
    ):
        return False, "market_numeric_contract_invalid"
    quote_age_ms = row.get("quote_age_ms")
    if quote_age_ms is not None and (
        isinstance(quote_age_ms, bool)
        or not isinstance(quote_age_ms, (int, float))
        or not math.isfinite(float(quote_age_ms))
        or float(quote_age_ms) < 0
    ):
        return False, "market_numeric_contract_invalid"
    try:
        _, consumer_eligible, _ = validate_market_stream_path_provenance(
            path_order_status=str(row.get("path_order_status") or ""),
            path_consumer_eligible=row.get("path_consumer_eligible"),
            exchange_timestamp_regression_ms=row.get(
                "exchange_timestamp_regression_ms"
            ),
        )
        _timestamp_us(row.get("local_receive_timestamp"))
        exchange_ms = _timestamp_us(row.get("exchange_timestamp"))
        receive_ms = _timestamp_us(row.get("local_receive_timestamp"))
    except (TypeError, ValueError):
        return False, "market_provenance_invalid"
    if not consumer_eligible:
        return False, "market_path_consumer_ineligible"
    if receive_ms < exchange_ms:
        return False, "market_receive_precedes_exchange"
    source_sequence = row.get("source_sequence")
    series_sequence = row.get("series_sequence")
    if (
        isinstance(source_sequence, bool)
        or not isinstance(source_sequence, int)
        or source_sequence <= 0
        or isinstance(series_sequence, bool)
        or not isinstance(series_sequence, int)
        or source_sequence != series_sequence
    ):
        return False, "market_sequence_invalid"
    sequence_epoch = row.get("sequence_epoch")
    if (
        isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        return False, "market_sequence_epoch_invalid"
    if row.get("realtime_type") != "0B":
        return False, "market_realtime_type_invalid"
    bid = _positive_float(row.get("best_bid"))
    ask = _positive_float(row.get("best_ask"))
    if bid is not None and ask is not None and ask < bid:
        return False, "market_bbo_crossed"
    return True, None


def _valid_depth_row(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    try:
        validate_depth_row(dict(row))
    except (TypeError, ValueError):
        return False, "depth_contract_invalid"
    return True, None


def _valid_reference(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    if row.get("schema") != EVENT_REFERENCE_SCHEMA:
        return False, "event_reference_schema_invalid"
    if (
        row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
        or row.get("trading_runtime_effect") is not False
    ):
        return False, "event_reference_authority_invalid"
    if row.get("decision_authority") != PATH_CAPTURE_AUTHORITY:
        return False, "event_reference_contract_invalid"
    for field in (
        "sequence_epoch",
        "event_detected_at_ms",
        "segment_event_detected_at_ms",
        "shock_horizon_ms",
        "event_sequence_in_wave",
    ):
        value = row.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return False, "event_reference_identity_invalid"
    if any(
        not str(row.get(field) or "").strip()
        for field in ("parent_wave_id", "path_segment_id", "shock_event_id")
    ):
        return False, "event_reference_identity_invalid"
    try:
        started_ms = _timestamp_ms(row.get("capture_started_at"))
        ended_ms = _timestamp_ms(row.get("capture_ended_at"))
    except (TypeError, ValueError):
        return False, "event_reference_capture_window_invalid"
    segment_ms = int(row.get("segment_event_detected_at_ms") or 0)
    if not started_ms <= segment_ms <= ended_ms:
        return False, "event_reference_capture_window_invalid"
    return True, None


def _scope_key(row: Mapping[str, Any]) -> tuple[str, str, str, int]:
    try:
        sequence_epoch = int(row.get("sequence_epoch") or 0)
    except (TypeError, ValueError):
        sequence_epoch = 0
    return (
        normalize_symbol(row.get("symbol")),
        normalize_venue(row.get("venue")),
        _session(row.get("session_bucket")),
        sequence_epoch,
    )


def _levels(value: Any) -> tuple[tuple[int, float, int], ...]:
    if not isinstance(value, list):
        return ()
    result: list[tuple[int, float, int]] = []
    for raw in value:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            return ()
        level = _nonnegative_int(raw[0])
        price = _positive_float(raw[1])
        quantity = _nonnegative_int(raw[2])
        if level is None or level <= 0 or price is None or quantity is None:
            return ()
        result.append((level, price, quantity))
    return tuple(result)


def _capacity_within_slippage(
    levels: Sequence[tuple[int, float, int]], *, side: str, max_slippage_bps: float
) -> int | None:
    if not levels:
        return None
    best = levels[0][1]
    capacity = 0
    for _, price, quantity in levels:
        slippage = (
            (price / best - 1.0) * 10_000.0
            if side == "ask"
            else (best / price - 1.0) * 10_000.0
        )
        if slippage > max_slippage_bps + 1e-9:
            break
        capacity += quantity
    return capacity


def _sweep_vwap(
    levels: Sequence[tuple[int, float, int]], quantity: int
) -> float | None:
    if quantity <= 0 or not levels:
        return None
    remaining = quantity
    notional = 0.0
    filled = 0
    for _, price, available in levels:
        take = min(remaining, available)
        notional += price * take
        filled += take
        remaining -= take
        if remaining <= 0:
            break
    return notional / filled if remaining <= 0 and filled > 0 else None


def _aggressor_quantities(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    buy_qty = 0
    sell_qty = 0
    unknown_qty = 0
    for row in rows:
        quantity = _nonnegative_int(row.get("trade_qty")) or 0
        side = str(row.get("aggressor_side") or "UNKNOWN").upper()
        if side == "BUY":
            buy_qty += quantity
        elif side == "SELL":
            sell_qty += quantity
        else:
            unknown_qty += quantity
    known = buy_qty + sell_qty
    return {
        "buy_qty": buy_qty,
        "sell_qty": sell_qty,
        "unknown_qty": unknown_qty,
        "known_qty": known,
        "buy_ratio": (buy_qty / known if known else None),
        "sell_ratio": (sell_qty / known if known else None),
        "sample_count": len(rows),
    }


def _series_sequence_findings(
    rows: Sequence[Mapping[str, Any]], *, prefix: str
) -> tuple[str, ...]:
    findings: list[str] = []
    previous_sequence = 0
    previous_receive_ms = 0
    for row in rows:
        sequence = int(row.get("source_sequence") or 0)
        receive_ms = _timestamp_us(row.get("local_receive_timestamp"))
        if sequence <= previous_sequence:
            findings.append(f"{prefix}_sequence_duplicate_or_regressed")
        elif previous_sequence and sequence > previous_sequence + 1:
            findings.append(f"{prefix}_sequence_gap")
        if receive_ms < previous_receive_ms:
            findings.append(f"{prefix}_local_receive_time_regressed")
        previous_sequence = sequence
        previous_receive_ms = receive_ms
    return tuple(sorted(set(findings)))


def _p2_point(row: Mapping[str, Any]) -> P2ReplayPoint:
    return P2ReplayPoint(
        exchange_timestamp_ms=_timestamp_ms(row.get("exchange_timestamp")),
        local_receive_timestamp_ms=_timestamp_ms(
            row.get("local_receive_timestamp")
        ),
        source_sequence=int(row.get("source_sequence") or 0),
        trade_price=_positive_float(row.get("trade_price")),
        trade_qty=_nonnegative_int(row.get("trade_qty")),
        best_bid=_positive_float(row.get("best_bid")),
        best_ask=_positive_float(row.get("best_ask")),
        quote_age_ms=_finite_float(row.get("quote_age_ms")),
        aggressor_side=str(row.get("aggressor_side") or "UNKNOWN").upper(),
    )


def _liquidity_projection(
    *,
    depth: Mapping[str, Any] | None,
    recent_rows: Sequence[Mapping[str, Any]],
    config: BridgeConfig,
    upstream_quantity: Mapping[str, Any],
) -> dict[str, Any]:
    upstream_qty = _nonnegative_int(upstream_quantity.get("quantity"))
    if depth is None:
        return {
            "capacity_quality_status": "depth_unavailable_not_imputed",
            "counterfactual_liquidity_qty_grid": [],
            "counterfactual_liquidity_qty_ceiling": None,
            "counterfactual_immediate_exit_qty_ceiling": None,
            "existing_position_formula_candidate_qty": upstream_qty,
            "existing_quantity_provenance": dict(upstream_quantity),
            "existing_quantity_owner": "position_sizing_dynamic_formula",
        }
    bid_levels = _levels(depth.get("bid_levels"))
    ask_levels = _levels(depth.get("ask_levels"))
    bid_capacity = _capacity_within_slippage(
        bid_levels,
        side="bid",
        max_slippage_bps=config.max_exit_sweep_slippage_bps,
    )
    ask_capacity = _capacity_within_slippage(
        ask_levels,
        side="ask",
        max_slippage_bps=config.max_entry_sweep_slippage_bps,
    )
    aggressive_buy_qty = sum(
        _nonnegative_int(row.get("trade_qty")) or 0
        for row in recent_rows
        if str(row.get("aggressor_side") or "UNKNOWN").upper() == "BUY"
    )
    grid = []
    for participation in config.participation_grid:
        roundtrip_depth_capacity = (
            None
            if bid_capacity is None or ask_capacity is None
            else math.floor(min(bid_capacity, ask_capacity) * participation)
        )
        immediate_exit_capacity = (
            None
            if bid_capacity is None
            else math.floor(bid_capacity * participation)
        )
        passive_ask_fill_support_qty = (
            None
            if aggressive_buy_qty <= 0
            else math.floor(
                aggressive_buy_qty
                / config.tape_capacity_window_sec
                * config.target_liquidation_sec
                * participation
            )
        )
        bounded_capacity = roundtrip_depth_capacity
        if bounded_capacity is not None and upstream_qty is not None:
            bounded_capacity = min(bounded_capacity, upstream_qty)
        entry_vwap = (
            None
            if bounded_capacity is None
            else _sweep_vwap(ask_levels, bounded_capacity)
        )
        exit_vwap = (
            None
            if bounded_capacity is None
            else _sweep_vwap(bid_levels, bounded_capacity)
        )
        grid.append(
            {
                "participation_rate": participation,
                "entry_ask_capacity_qty": ask_capacity,
                "depth_only_fast_exit_capacity_qty": bid_capacity,
                "immediate_roundtrip_depth_capacity_qty": (
                    roundtrip_depth_capacity
                ),
                "immediate_marketable_exit_capacity_qty": (
                    immediate_exit_capacity
                ),
                "passive_ask_fill_support_qty": passive_ask_fill_support_qty,
                "counterfactual_liquidity_bounded_qty": bounded_capacity,
                "counterfactual_entry_sweep_vwap": entry_vwap,
                "counterfactual_exit_sweep_vwap": exit_vwap,
                "counterfactual_roundtrip_execution_bps": (
                    None
                    if entry_vwap is None or exit_vwap is None
                    else round((entry_vwap / exit_vwap - 1.0) * 10_000.0, 6)
                ),
            }
        )
    conservative_index = min(1, len(grid) - 1)
    ceiling = grid[conservative_index]["counterfactual_liquidity_bounded_qty"]
    exit_ceiling = grid[conservative_index][
        "immediate_marketable_exit_capacity_qty"
    ]
    return {
        "capacity_quality_status": (
            "immediate_bid_ask_depth_capacity_observed"
            if ceiling is not None
            else "depth_capacity_unavailable"
        ),
        "target_liquidation_sec": config.target_liquidation_sec,
        "recent_tape_window_sec": config.tape_capacity_window_sec,
        "recent_aggressive_buy_qty": (
            aggressive_buy_qty if aggressive_buy_qty > 0 else None
        ),
        "aggressive_buy_role": "passive_ask_exit_support_only_not_bid_sweep_capacity",
        "counterfactual_liquidity_qty_grid": grid,
        "counterfactual_liquidity_qty_ceiling": ceiling,
        "counterfactual_immediate_exit_qty_ceiling": exit_ceiling,
        "existing_position_formula_candidate_qty": upstream_qty,
        "existing_quantity_provenance": dict(upstream_quantity),
        "existing_quantity_owner": "position_sizing_dynamic_formula",
        "future_candidate_composition_rule": (
            "min(existing_position_formula_qty,verified_fast_exit_capacity)"
        ),
    }


def _economics(
    *, liquidity: Mapping[str, Any], config: BridgeConfig
) -> dict[str, Any]:
    grid = liquidity.get("counterfactual_liquidity_qty_grid")
    grid = grid if isinstance(grid, list) else []
    conservative = grid[min(1, len(grid) - 1)] if grid else {}
    execution_bps = _finite_float(
        conservative.get("counterfactual_roundtrip_execution_bps")
    )
    cost_ready = config.statutory_sell_tax_bps is not None
    fixed_cost = (
        None
        if not cost_ready
        else config.buy_fee_bps
        + config.sell_fee_bps
        + float(config.statutory_sell_tax_bps)
        + config.uncertainty_buffer_bps
    )
    all_in = (
        None
        if fixed_cost is None or execution_bps is None
        else fixed_cost + execution_bps
    )
    return {
        "cost_profile_source": config.cost_profile_source,
        "cost_profile_verified": config.cost_profile_verified,
        "buy_fee_bps": config.buy_fee_bps if cost_ready else None,
        "sell_fee_bps": config.sell_fee_bps if cost_ready else None,
        "statutory_sell_tax_bps": config.statutory_sell_tax_bps,
        "uncertainty_buffer_bps": (
            config.uncertainty_buffer_bps if cost_ready else None
        ),
        "counterfactual_roundtrip_execution_bps": execution_bps,
        "spread_double_counted": False,
        "all_in_cost_bps": None if all_in is None else round(all_in, 6),
        "minimum_net_profit_bps": config.minimum_net_profit_bps,
        "minimum_gross_target_bps": (
            None
            if all_in is None
            else round(all_in + config.minimum_net_profit_bps, 6)
        ),
        "economic_source_quality_status": (
            "verified_cost_profile"
            if cost_ready and config.cost_profile_verified
            else (
                "research_cost_assumption_not_promotion_grade"
                if cost_ready
                else "cost_profile_unavailable_no_net_target"
            )
        ),
    }


def _nested_value(source: Any, path: Sequence[str]) -> Any:
    current = source
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _position_context(payload: Mapping[str, Any]) -> dict[str, Any]:
    source = _stored_replay_exact_payload(payload)
    roots = [source] if isinstance(source, Mapping) else []
    nested_exact = source.get("exact_payload") if isinstance(source, Mapping) else None
    if isinstance(nested_exact, Mapping):
        roots.append(nested_exact)
    contexts: list[Mapping[str, Any]] = []
    for root in roots:
        if root.get("schema") == HOLDING_CONTEXT_SCHEMA:
            contexts.append(root)
        candidate = root.get("holding_decision_context")
        if isinstance(candidate, Mapping) and candidate.get("schema") == (
            HOLDING_CONTEXT_SCHEMA
        ):
            contexts.append(candidate)
    contexts_by_hash = {_sha256(context): context for context in contexts}
    if len(contexts_by_hash) != 1:
        return {
            "status": "canonical_position_context_unavailable",
            "quantity": None,
            "free_to_sell_quantity": None,
            "average_price": None,
            "quantity_pointer": None,
            "price_pointer": None,
        }
    context = next(iter(contexts_by_hash.values()))
    execution = context.get("execution_pnl")
    execution = execution if isinstance(execution, Mapping) else {}
    lifecycle = context.get("position_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    reconciliation = context.get("order_reconciliation")
    reconciliation = reconciliation if isinstance(reconciliation, Mapping) else {}
    remaining_qty = _nonnegative_int(execution.get("remaining_qty"))
    broker_qty = _nonnegative_int(lifecycle.get("broker_qty"))
    memory_qty = _nonnegative_int(lifecycle.get("memory_qty"))
    quantity_candidates = [
        quantity
        for quantity in (broker_qty, remaining_qty, memory_qty)
        if quantity is not None
    ]
    quantity = quantity_candidates[0] if quantity_candidates else None
    quantity_conflict = bool(
        reconciliation.get("quantity_mismatch") is True
        or reconciliation.get("order_or_quantity_conflict") is True
        or len(set(quantity_candidates)) > 1
    )
    open_sell_qty = _nonnegative_int(reconciliation.get("open_sell_qty"))
    reconciliation_contract_complete = bool(
        broker_qty is not None
        and open_sell_qty is not None
        and isinstance(reconciliation.get("cancel_pending"), bool)
        and isinstance(reconciliation.get("exit_token_active"), bool)
        and isinstance(reconciliation.get("quantity_mismatch"), bool)
        and isinstance(reconciliation.get("order_or_quantity_conflict"), bool)
    )
    order_conflict = bool(
        not reconciliation_contract_complete
        or reconciliation.get("cancel_pending") is True
        or reconciliation.get("exit_token_active") is True
        or quantity_conflict
        or (quantity is not None and open_sell_qty is not None and open_sell_qty > quantity)
    )
    free_to_sell_qty = (
        None
        if quantity is None or order_conflict or open_sell_qty > quantity
        else max(0, quantity - open_sell_qty)
    )
    price = _positive_float(
        execution.get("average_entry_price")
        or lifecycle.get("average_entry_price")
    )
    return {
        "status": (
            "canonical_position_execution_conflict"
            if order_conflict and reconciliation_contract_complete
            else (
                "canonical_broker_reconciliation_incomplete"
                if not reconciliation_contract_complete
                else (
                    "canonical_position_context_captured"
                    if quantity is not None and quantity > 0
                    else "canonical_position_quantity_unavailable"
                )
            )
        ),
        "quantity": quantity if quantity is not None and quantity > 0 else None,
        "free_to_sell_quantity": (
            free_to_sell_qty
            if free_to_sell_qty is not None and free_to_sell_qty > 0
            else None
        ),
        "average_price": price,
        "open_sell_qty": open_sell_qty,
        "broker_reconciliation_contract_complete": (
            reconciliation_contract_complete
        ),
        "cancel_pending": reconciliation.get("cancel_pending") is True,
        "exit_token_active": reconciliation.get("exit_token_active") is True,
        "quantity_conflict": quantity_conflict,
        "quantity_pointer": (
            "/holding_decision_context/position_lifecycle/broker_qty"
            if broker_qty is not None
            else "/holding_decision_context/execution_pnl/remaining_qty"
        ),
        "free_to_sell_quantity_formula": "total_position_minus_open_sell_qty",
        "price_pointer": (
            "/holding_decision_context/execution_pnl/average_entry_price"
        ),
    }


def _lifecycle_projection(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    capacity_depth: Mapping[str, Any] | None,
    liquidity: Mapping[str, Any],
    economics: Mapping[str, Any],
    max_exit_sweep_slippage_bps: float,
) -> dict[str, Any]:
    position = _position_context(payload)
    position_qty = _nonnegative_int(position.get("quantity"))
    free_to_sell_qty = _nonnegative_int(position.get("free_to_sell_quantity"))
    buy_price = _positive_float(position.get("average_price"))
    entry_roundtrip_capacity = _nonnegative_int(
        liquidity.get("counterfactual_liquidity_qty_ceiling")
    )
    immediate_exit_capacity = _nonnegative_int(
        liquidity.get("counterfactual_immediate_exit_qty_ceiling")
    )
    bid_levels = _levels((capacity_depth or {}).get("bid_levels"))
    bid_slippage_capacity = _capacity_within_slippage(
        bid_levels,
        side="bid",
        max_slippage_bps=max_exit_sweep_slippage_bps,
    )
    full_position_exit_vwap = (
        None
        if free_to_sell_qty is None
        or bid_slippage_capacity is None
        or free_to_sell_qty > bid_slippage_capacity
        else _sweep_vwap(bid_levels, free_to_sell_qty)
    )
    gross_exit_bps = (
        None
        if buy_price is None or full_position_exit_vwap is None
        else (full_position_exit_vwap / buy_price - 1.0) * 10_000.0
    )
    fixed_cost = None
    if economics.get("statutory_sell_tax_bps") is not None:
        fixed_cost = sum(
            float(economics.get(field) or 0.0)
            for field in (
                "buy_fee_bps",
                "sell_fee_bps",
                "statutory_sell_tax_bps",
                "uncertainty_buffer_bps",
            )
        )
    net_exit_bps = (
        None
        if gross_exit_bps is None or fixed_cost is None
        else gross_exit_bps - fixed_cost
    )
    return {
        "schema": LIFECYCLE_PROJECTION_SCHEMA,
        "objective": (
            "maximize_after_cost_net_profit_with_fast_frequent_bounded_exposure"
        ),
        "decision_stage": trace.get("decision_stage"),
        "entry_projection": {
            "timing_owner": "deterministic_micro_reversion_state_machine_candidate",
            "ai_role": "offline_cost_liquidity_and_tail_risk_adjudication",
            "minimum_gross_target_bps": economics.get(
                "minimum_gross_target_bps"
            ),
            "counterfactual_fast_roundtrip_capacity_qty": (
                entry_roundtrip_capacity
            ),
            "counterfactual_full_position_exit_sweep_vwap": (
                full_position_exit_vwap
            ),
            "live_price_or_order_effect": False,
        },
        "holding_projection": {
            "review_cadence": "each_new_0b_or_0d_state_change_not_synchronous_llm",
            "observed_position_qty": position_qty,
            "counterfactual_free_to_sell_qty": free_to_sell_qty,
            "observed_position_average_price": buy_price,
            "position_provenance": position,
            "counterfactual_fast_exit_capacity_qty": immediate_exit_capacity,
            "counterfactual_snapshot_exit_sweep_vwap": full_position_exit_vwap,
            "counterfactual_capacity_coverage_ratio": (
                None
                if free_to_sell_qty in (None, 0) or immediate_exit_capacity is None
                else min(1.0, immediate_exit_capacity / free_to_sell_qty)
            ),
            "counterfactual_uncovered_position_qty": (
                None
                if free_to_sell_qty is None or immediate_exit_capacity is None
                else max(0, free_to_sell_qty - immediate_exit_capacity)
            ),
            "counterfactual_net_executable_pnl_bps": (
                None if net_exit_bps is None else round(net_exit_bps, 6)
            ),
            "scale_in_requires_fresh_recovery_and_verified_exit_capacity": True,
            "hard_protect_emergency_exit_priority_unchanged": True,
        },
        "exit_projection": {
            "profit_basis": (
                "full_position_bid_sweep_vwap_after_roundtrip_cost"
            ),
            "minimum_net_profit_bps": economics.get("minimum_net_profit_bps"),
            "counterfactual_net_target_reached": (
                None
                if net_exit_bps is None
                else net_exit_bps
                >= float(economics.get("minimum_net_profit_bps") or 0.0)
            ),
            "counterfactual_immediately_executable_qty": immediate_exit_capacity,
            "hard_protect_emergency_exit_priority_unchanged": True,
            "live_sell_or_cancel_effect": False,
        },
        **AUTHORITY_CONTRACT,
    }


def _upstream_quantity(payload: Mapping[str, Any]) -> dict[str, Any]:
    source = _stored_replay_exact_payload(payload)
    allowed_paths = (
        ("position_sizing_allocator", "effective_qty"),
        ("position_sizing", "effective_qty"),
        ("order_plan", "effective_qty"),
    )
    candidates = []
    for path in allowed_paths:
        quantity = _nonnegative_int(_nested_value(source, path))
        if quantity is not None and quantity > 0:
            candidates.append((quantity, "/" + "/".join(path)))
    unique = {(quantity, pointer) for quantity, pointer in candidates}
    if not unique:
        return {
            "status": "allocator_quantity_unavailable_not_imputed",
            "quantity": None,
            "pointer": None,
            "owner": "position_sizing_dynamic_formula",
        }
    quantities = {quantity for quantity, _ in unique}
    if len(quantities) != 1:
        return {
            "status": "allocator_quantity_conflict",
            "quantity": None,
            "pointer": None,
            "owner": "position_sizing_dynamic_formula",
        }
    quantity = next(iter(quantities))
    pointers = sorted(pointer for _, pointer in unique)
    return {
        "status": "allocator_quantity_captured",
        "quantity": quantity,
        "pointer": pointers[0] if len(pointers) == 1 else pointers,
        "owner": "position_sizing_dynamic_formula",
    }


def build_tactical_evidence(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
) -> dict[str, Any]:
    """Build one nonfuture sidecar without changing the exact provider payload."""

    selected_config = config or BridgeConfig()
    watermark, blockers = exact_snapshot_watermark(trace, payload)
    blocker_list = list(blockers)
    capacity_blockers: list[str] = []
    exact_payload = _stored_replay_exact_payload(payload)
    if exact_payload is None:
        blocker_list.append("stored_exact_payload_missing")
    source_exact_payload_sha256 = (
        _sha256(exact_payload) if exact_payload is not None else None
    )
    upstream_quantity = _upstream_quantity(payload)
    scope = resolve_micro_scope(trace)
    if scope.status != "resolved":
        blocker_list.append(scope.reason or "micro_scope_unresolved")
    symbol = normalize_symbol(trace.get("stock_code"))
    if not symbol:
        blocker_list.append("trace_symbol_missing")
    watermark_ms = int((watermark or {}).get("captured_at_ms") or 0)
    watermark_us = int((watermark or {}).get("captured_at_us") or 0)
    causal_lower_us = max(
        0,
        watermark_us
        - (
            selected_config.active_wave_max_age_sec
            + selected_config.context_lookback_sec
        )
        * 1_000_000,
    )

    accepted_market: list[Mapping[str, Any]] = []
    rejected_market = Counter()
    for row in market_rows:
        if (
            normalize_symbol(row.get("symbol")) != symbol
            or normalize_venue(row.get("venue")) != scope.venue
            or _session(row.get("session_bucket")) != scope.session_bucket
        ):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            # An unbounded timestamp cannot be proven past and is never part of
            # prompt-visible quality counters.
            continue
        if received_us < causal_lower_us or received_us > watermark_us:
            continue
        valid, reason = _valid_market_row(row)
        if not valid:
            rejected_market[reason or "market_invalid"] += 1
            continue
        accepted_market.append(row)
    accepted_market.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    latest_market = accepted_market[-1] if accepted_market else None
    if latest_market is None:
        blocker_list.append("past_market_row_missing")
        selected_epoch = 0
    else:
        selected_epoch = int(latest_market.get("sequence_epoch") or 0)
        market_age_ms = (
            watermark_us - _timestamp_us(latest_market.get("local_receive_timestamp"))
        ) / 1_000.0
        if market_age_ms < 0:
            blocker_list.append("future_market_row_selected")
        elif market_age_ms > selected_config.max_market_age_ms:
            blocker_list.append("market_row_stale")
        accepted_market = [
            row
            for row in accepted_market
            if int(row.get("sequence_epoch") or 0) == selected_epoch
        ]
        blocker_list.extend(
            _series_sequence_findings(accepted_market, prefix="market")
        )
        market_bid = _positive_float(latest_market.get("best_bid"))
        market_ask = _positive_float(latest_market.get("best_ask"))
        quote_age_ms = _finite_float(latest_market.get("quote_age_ms"))
        if market_bid is None or market_ask is None:
            blocker_list.append("market_bbo_missing")
        if quote_age_ms is None or quote_age_ms < 0:
            blocker_list.append("market_quote_age_missing")
        elif quote_age_ms > selected_config.max_quote_age_ms:
            blocker_list.append("market_bbo_stale")
    trade_scope = (
        str((watermark or {}).get("captured_at") or "")[:10],
        scope.venue,
        scope.session_bucket,
        selected_epoch,
    )
    if excluded_scopes and trade_scope in excluded_scopes:
        blocker_list.append("source_exclusion_scope_matched")

    accepted_depth: list[Mapping[str, Any]] = []
    rejected_depth = Counter()
    for row in depth_rows:
        if _scope_key(row) != (symbol, scope.venue, scope.session_bucket, selected_epoch):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if received_us < causal_lower_us or received_us > watermark_us:
            continue
        valid, reason = _valid_depth_row(row)
        if not valid:
            rejected_depth[reason or "depth_invalid"] += 1
            continue
        accepted_depth.append(row)
    accepted_depth.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    latest_depth = accepted_depth[-1] if accepted_depth else None
    capacity_depth = latest_depth
    depth_basis_status = "same_basis"
    depth_age_ms = None
    if latest_depth is None:
        capacity_blockers.append("same_epoch_past_depth_missing")
        depth_basis_status = "same_epoch_past_depth_missing"
    else:
        depth_age_ms = (
            watermark_us - _timestamp_us(latest_depth.get("local_receive_timestamp"))
        ) / 1_000.0
        if depth_age_ms < 0:
            capacity_blockers.append("future_depth_row_selected")
            capacity_depth = None
            depth_basis_status = "future_depth_capacity_unavailable"
        elif depth_age_ms > selected_config.max_depth_age_ms:
            capacity_blockers.append("depth_row_stale")
            capacity_depth = None
            depth_basis_status = "stale_depth_capacity_unavailable"
        depth_sequence_findings = _series_sequence_findings(
            accepted_depth, prefix="depth"
        )
        capacity_blockers.extend(depth_sequence_findings)
        if depth_sequence_findings:
            capacity_depth = None
            depth_basis_status = "depth_sequence_capacity_unavailable"
        if latest_market is not None and capacity_depth is not None:
            market_bid = _positive_float(latest_market.get("best_bid"))
            market_ask = _positive_float(latest_market.get("best_ask"))
            depth_bid = _positive_float(latest_depth.get("best_bid"))
            depth_ask = _positive_float(latest_depth.get("best_ask"))
            if market_bid != depth_bid or market_ask != depth_ask:
                capacity_depth = None
                depth_basis_status = "market_depth_bbo_conflict_capacity_unavailable"
                capacity_blockers.append(depth_basis_status)

    references: list[Mapping[str, Any]] = []
    rejected_references = Counter()
    for row in event_references:
        if _scope_key(row) != (symbol, scope.venue, scope.session_bucket, selected_epoch):
            continue
        try:
            detected_ms = int(row.get("event_detected_at_ms"))
        except (TypeError, ValueError):
            continue
        if not causal_lower_us <= detected_ms * 1_000 <= watermark_us:
            continue
        valid, reason = _valid_reference(row)
        if not valid:
            rejected_references[reason or "event_reference_invalid"] += 1
            continue
        references.append(row)
    by_wave: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in references:
        by_wave[str(row.get("parent_wave_id"))].append(row)
    wave_rows = [
        min(
            rows,
            key=lambda row: (
                int(row.get("event_detected_at_ms") or 0),
                int(row.get("event_sequence_in_wave") or 0),
                int(row.get("shock_horizon_ms") or 0),
            ),
        )
        for rows in by_wave.values()
    ]
    active_reference = (
        max(wave_rows, key=lambda row: int(row.get("event_detected_at_ms") or 0))
        if wave_rows
        else None
    )
    if active_reference is not None and (
        watermark_ms - int(active_reference.get("event_detected_at_ms") or 0)
        > selected_config.active_wave_max_age_sec * 1_000
    ):
        active_reference = None

    status = "source_unavailable" if blocker_list else "not_applicable"
    event_metrics: dict[str, Any] = {}
    tape: dict[str, Any] = {}
    orderbook: dict[str, Any] = {}
    liquidity: dict[str, Any] = _liquidity_projection(
        depth=capacity_depth,
        recent_rows=(),
        config=selected_config,
        upstream_quantity=upstream_quantity,
    )
    economics = _economics(liquidity=liquidity, config=selected_config)
    if active_reference is not None and latest_market is not None:
        try:
            onset = reconstruct_shock_onset_context(
                tuple(_p2_point(row) for row in accepted_market),
                reference=dict(active_reference),
                reference_max_lag_ms=2_000,
            )
        except (TypeError, ValueError):
            blocker_list.append("shock_onset_reconstruction_failed")
        else:
            event_ms = onset.event_local_receive_timestamp_ms
            post_rows = [
                row
                for row in accepted_market
                if (
                    _timestamp_ms(row.get("local_receive_timestamp")),
                    int(row.get("source_sequence") or 0),
                )
                >= (event_ms, onset.event_source_sequence)
                and _positive_float(row.get("trade_price")) is not None
            ]
            latest_price = _positive_float(latest_market.get("trade_price"))
            if not post_rows or latest_price is None:
                blocker_list.append("event_price_path_incomplete")
            else:
                reference_price = onset.reference_price
                shock_price = onset.shock_price
                running_low = shock_price
                confirmation_row: Mapping[str, Any] | None = None
                confirmation_low = shock_price
                recovery_invalidation_count = 0
                for row in post_rows[1:]:
                    price = float(row["trade_price"])
                    if price < running_low:
                        running_low = price
                        if confirmation_row is not None:
                            recovery_invalidation_count += 1
                            confirmation_row = None
                        confirmation_low = running_low
                        continue
                    reclaim_span = reference_price - running_low
                    if (
                        confirmation_row is None
                        and reclaim_span > 0
                        and price >= running_low + 0.5 * reclaim_span
                    ):
                        confirmation_row = row
                        confirmation_low = running_low
                post_low = min(float(row["trade_price"]) for row in post_rows)
                new_low_after_half_reclaim = bool(
                    recovery_invalidation_count > 0 and confirmation_row is None
                )
                shock_size = reference_price - post_low
                reclaim_fraction = (
                    (latest_price - post_low) / shock_size if shock_size > 0 else 0.0
                )
                early_end_ms = min(
                    watermark_ms,
                    event_ms + selected_config.tape_capacity_window_sec * 1_000,
                )
                recent_start_ms = max(
                    event_ms,
                    watermark_ms
                    - selected_config.tape_capacity_window_sec * 1_000,
                )
                early_rows = [
                    row
                    for row in accepted_market
                    if event_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= early_end_ms
                ]
                recent_rows = [
                    row
                    for row in accepted_market
                    if recent_start_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= watermark_ms
                ]
                early_tape = _aggressor_quantities(early_rows)
                recent_tape = _aggressor_quantities(recent_rows)
                nonoverlap_windows = early_end_ms < recent_start_ms
                sell_pressure_deceleration = (
                    None
                    if not nonoverlap_windows
                    or early_tape["sell_ratio"] is None
                    or recent_tape["sell_ratio"] is None
                    else round(
                        early_tape["sell_ratio"] - recent_tape["sell_ratio"],
                        6,
                    )
                )
                tape = {
                    "early": early_tape,
                    "recent": recent_tape,
                    "window_sec": selected_config.tape_capacity_window_sec,
                    "early_window_end_ms": early_end_ms,
                    "recent_window_start_ms": recent_start_ms,
                    "deceleration_windows_nonoverlap": nonoverlap_windows,
                    "sell_pressure_deceleration": sell_pressure_deceleration,
                }
                event_depth_rows = [
                    row
                    for row in accepted_depth
                    if event_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= watermark_ms
                ]
                first_depth = event_depth_rows[0] if event_depth_rows else None
                latest_bid_depth = _nonnegative_int(
                    (capacity_depth or {}).get("bid_depth")
                )
                first_bid_depth = _nonnegative_int(
                    (first_depth or {}).get("bid_depth")
                )
                same_price_depth = bool(
                    first_depth is not None
                    and capacity_depth is not None
                    and all(
                        _positive_float(row.get("best_bid"))
                        == _positive_float(first_depth.get("best_bid"))
                        for row in event_depth_rows
                    )
                    and _positive_float(first_depth.get("best_bid"))
                    == _positive_float(capacity_depth.get("best_bid"))
                )
                bid_replenishment = (
                    None
                    if not same_price_depth
                    or latest_bid_depth is None
                    or first_bid_depth is None
                    else latest_bid_depth - first_bid_depth
                )
                best_bid = _positive_float(latest_market.get("best_bid"))
                best_ask = _positive_float(latest_market.get("best_ask"))
                spread_bps = (
                    None
                    if best_bid is None or best_ask is None
                    else (best_ask / best_bid - 1.0) * 10_000.0
                )
                orderbook = {
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "best_bid_qty": _nonnegative_int(
                        (capacity_depth or {}).get("best_bid_qty")
                    ),
                    "best_ask_qty": _nonnegative_int(
                        (capacity_depth or {}).get("best_ask_qty")
                    ),
                    "bid_depth": latest_bid_depth,
                    "ask_depth": _nonnegative_int(
                        (capacity_depth or {}).get("ask_depth")
                    ),
                    "spread_bps": (
                        None if spread_bps is None else round(spread_bps, 6)
                    ),
                    "same_epoch_bid_depth_change_qty": bid_replenishment,
                    "bid_replenishment_same_price_basis": same_price_depth,
                    "bid_replenishment_price_path_status": (
                        "continuous_same_bid_price"
                        if same_price_depth
                        else "price_basis_changed_or_unavailable"
                    ),
                    "depth_age_ms": depth_age_ms,
                    "depth_join_status": (
                        "joined_fresh_past_same_epoch_same_bbo"
                        if capacity_depth is not None
                        and depth_age_ms is not None
                        and depth_age_ms <= selected_config.max_depth_age_ms
                        else depth_basis_status
                    ),
                }
                late_buy_support = (
                    recent_tape.get("known_qty", 0) > 0
                    and (recent_tape.get("buy_ratio") or 0.0) >= 0.5
                )
                sell_decelerated = (sell_pressure_deceleration or 0.0) > 0
                bid_supported = (
                    bid_replenishment is not None and bid_replenishment > 0
                )
                if new_low_after_half_reclaim:
                    status = "continuation_blocked"
                elif confirmation_row is not None and (
                    late_buy_support or sell_decelerated or bid_supported
                ):
                    status = "reversion_confirmed"
                elif reclaim_fraction > 0 or confirmation_row is not None:
                    status = "reversion_candidate"
                else:
                    status = "shock_active"
                event_metrics = {
                    "parent_wave_id": active_reference.get("parent_wave_id"),
                    "path_segment_id": active_reference.get("path_segment_id"),
                    "shock_event_id": active_reference.get("shock_event_id"),
                    "shock_horizon_ms": onset.shock_horizon_ms,
                    "event_sequence_in_wave": active_reference.get(
                        "event_sequence_in_wave"
                    ),
                    "event_detected_at_ms": event_ms,
                    "event_source_sequence": onset.event_source_sequence,
                    "reference_price": reference_price,
                    "shock_price": shock_price,
                    "post_shock_low_price": post_low,
                    "asof_trade_price": latest_price,
                    "shock_bps": onset.shock_return_bps,
                    "reclaim_from_low_bps": round(
                        (latest_price / post_low - 1.0) * 10_000.0, 6
                    ),
                    "reclaim_fraction": round(reclaim_fraction, 6),
                    "remaining_to_reference_bps": round(
                        (reference_price / latest_price - 1.0) * 10_000.0,
                        6,
                    ),
                    "half_reclaim_first_source_sequence": (
                        None
                        if confirmation_row is None
                        else confirmation_row.get("source_sequence")
                    ),
                    "half_reclaim_reference_low_price": (
                        None if confirmation_row is None else confirmation_low
                    ),
                    "new_low_after_half_reclaim": new_low_after_half_reclaim,
                    "recovery_invalidation_count": recovery_invalidation_count,
                    "latest_recovery_cycle_reconfirmed": bool(
                        recovery_invalidation_count > 0
                        and confirmation_row is not None
                    ),
                }
                liquidity = _liquidity_projection(
                    depth=capacity_depth,
                    recent_rows=recent_rows,
                    config=selected_config,
                    upstream_quantity=upstream_quantity,
                )
                economics = _economics(
                    liquidity=liquidity, config=selected_config
                )
    if blocker_list:
        status = "source_unavailable"
    latest_market_payload = latest_market or {}
    source_quality_status = "pass" if not blocker_list else "blocked"
    evidence_without_hash = {
        "schema": TACTICAL_EVIDENCE_SCHEMA,
        "evidence_version": 1,
        "decision_trace_id": trace.get("decision_trace_id"),
        "request_id": trace.get("request_id"),
        "decision_stage": trace.get("decision_stage"),
        "source_provider_payload_sha256": trace.get("payload_sha256"),
        "source_exact_payload_sha256": source_exact_payload_sha256,
        "source_request_envelope_sha256": trace.get("request_envelope_sha256"),
        "snapshot_id": (watermark or {}).get("snapshot_id"),
        "stock_code": symbol,
        "trace_effective_venue": trace.get("effective_venue"),
        "trace_session_bucket": trace.get("session_bucket"),
        "micro_venue": scope.venue,
        "micro_session_bucket": scope.session_bucket,
        "sequence_epoch": selected_epoch or None,
        "snapshot_captured_at": (watermark or {}).get("captured_at"),
        "snapshot_captured_at_ms": watermark_ms or None,
        "provider_payload_semantic_hash_status": (watermark or {}).get(
            "provider_payload_semantic_hash_status"
        ),
        "exact_replay_source_semantic_status": (watermark or {}).get(
            "exact_replay_source_semantic_status"
        ),
        "decision_watermark": {
            "local_receive_timestamp": latest_market_payload.get(
                "local_receive_timestamp"
            ),
            "source_sequence": latest_market_payload.get("source_sequence"),
            "past_only_join": True,
        },
        "depth_watermark": {
            "local_receive_timestamp": (latest_depth or {}).get(
                "local_receive_timestamp"
            ),
            "source_sequence": (latest_depth or {}).get("source_sequence"),
            "past_only_join": True,
        },
        "state": status,
        "event": event_metrics,
        "tape": tape,
        "orderbook": orderbook,
        "economics": economics,
        "liquidity_capacity": liquidity,
        "source_quality": {
            "status": source_quality_status,
            "blockers": sorted(set(blocker_list)),
            "liquidity_capacity_status": (
                "pass" if not capacity_blockers else "blocked"
            ),
            "liquidity_capacity_blockers": sorted(set(capacity_blockers)),
            "rejected_market_reason_counts": dict(rejected_market),
            "rejected_depth_reason_counts": dict(rejected_depth),
            "rejected_reference_reason_counts": dict(rejected_references),
            "parent_wave_reference_count": len(by_wave),
            "parent_wave_deduplicated": True,
            "future_outcome_fields_in_context": False,
        },
        **METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }
    lifecycle = _lifecycle_projection(
        trace=trace,
        payload=payload,
        capacity_depth=capacity_depth,
        liquidity=liquidity,
        economics=economics,
        max_exit_sweep_slippage_bps=selected_config.max_exit_sweep_slippage_bps,
    )
    context_without_hash = {
        **evidence_without_hash,
        LIFECYCLE_PROJECTION_SCHEMA: lifecycle,
    }
    return {**context_without_hash, "evidence_sha256": _sha256(context_without_hash)}


def build_future_outcome(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]] = (),
    config: BridgeConfig | None = None,
) -> dict[str, Any]:
    """Label quantity-sweep paths after the snapshot, never prompt input."""

    selected_config = config or BridgeConfig()
    start_ms = int(evidence.get("snapshot_captured_at_ms") or 0)
    symbol = normalize_symbol(evidence.get("stock_code"))
    venue = normalize_venue(evidence.get("micro_venue"))
    session = _session(evidence.get("micro_session_bucket"))
    epoch = int(evidence.get("sequence_epoch") or 0)
    stage = str(
        evidence.get("decision_stage")
        or (evidence.get(LIFECYCLE_PROJECTION_SCHEMA) or {}).get(
            "decision_stage"
        )
        or ""
    ).strip().lower()
    entry_like_stages = {
        "entry",
        "entry_screen",
        "gatekeeper",
        "post_probe",
        "scale_in",
    }
    position_like_stages = {
        "holding",
        "holding_score",
        "holding_flow",
        "exit",
    }
    grid = (evidence.get("liquidity_capacity") or {}).get(
        "counterfactual_liquidity_qty_grid"
    )
    grid = grid if isinstance(grid, list) else []
    conservative = grid[min(1, len(grid) - 1)] if grid else {}
    lifecycle = evidence.get(LIFECYCLE_PROJECTION_SCHEMA)
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    holding_projection = lifecycle.get("holding_projection")
    holding_projection = (
        holding_projection if isinstance(holding_projection, Mapping) else {}
    )
    if stage in entry_like_stages:
        evaluation_basis = "new_or_incremental_entry_ask_sweep_to_future_bid_sweep"
        quantity = _nonnegative_int(
            conservative.get("counterfactual_liquidity_bounded_qty")
        )
        baseline_vwap = _positive_float(
            conservative.get("counterfactual_entry_sweep_vwap")
        )
        position_average_price = None
    elif stage in position_like_stages:
        evaluation_basis = (
            "hold_or_exit_incremental_future_bid_sweep_vs_snapshot_bid_sweep"
        )
        quantity = _nonnegative_int(
            holding_projection.get("counterfactual_free_to_sell_qty")
        )
        baseline_vwap = _positive_float(
            holding_projection.get("counterfactual_snapshot_exit_sweep_vwap")
        )
        position_average_price = _positive_float(
            holding_projection.get("observed_position_average_price")
        )
    elif stage == "entry_price":
        evaluation_basis = (
            "entry_price_selection_evaluation_owned_by_stage_replay"
        )
        quantity = None
        baseline_vwap = None
        position_average_price = None
    elif stage == "overnight":
        evaluation_basis = "overnight_next_session_evaluation_owned_externally"
        quantity = None
        baseline_vwap = None
        position_average_price = None
    else:
        evaluation_basis = "decision_stage_not_supported"
        quantity = None
        baseline_vwap = None
        position_average_price = None
    rows: list[Mapping[str, Any]] = []
    for row in market_rows:
        valid, _ = _valid_market_row(row)
        if not valid or _scope_key(row) != (symbol, venue, session, epoch):
            continue
        received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
        if start_ms < received_ms <= (
            start_ms
            + selected_config.outcome_horizons_sec[-1] * 1_000
            + selected_config.max_outcome_endpoint_lag_ms
        ):
            rows.append(row)
    rows.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    depths: list[Mapping[str, Any]] = []
    for row in depth_rows:
        if _scope_key(row) != (symbol, venue, session, epoch):
            continue
        valid, _ = _valid_depth_row(row)
        if valid:
            depths.append(row)
    depths.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    depth_times_us = tuple(
        _timestamp_us(row.get("local_receive_timestamp")) for row in depths
    )
    fixed_cost = (
        None
        if selected_config.statutory_sell_tax_bps is None
        else selected_config.buy_fee_bps
        + selected_config.sell_fee_bps
        + selected_config.statutory_sell_tax_bps
        + selected_config.uncertainty_buffer_bps
    )
    outcome_eligibility_blockers: list[str] = []
    if stage == "entry_price":
        outcome_eligibility_blockers.append(
            "entry_price_selection_evaluation_not_implemented_in_micro_bridge"
        )
    elif stage == "overnight":
        outcome_eligibility_blockers.append(
            "overnight_next_session_evaluation_not_implemented_in_micro_bridge"
        )
    elif stage not in entry_like_stages | position_like_stages:
        outcome_eligibility_blockers.append("outcome_decision_stage_not_supported")
    if not quantity:
        outcome_eligibility_blockers.append("counterfactual_quantity_unavailable")
    if baseline_vwap is None:
        outcome_eligibility_blockers.append("snapshot_execution_basis_unavailable")
    if stage in entry_like_stages and fixed_cost is None:
        outcome_eligibility_blockers.append("roundtrip_cost_profile_unavailable")
    executable: list[tuple[int, float, float | None]] = []
    if quantity and baseline_vwap is not None and (
        stage in position_like_stages or fixed_cost is not None
    ):
        for row in rows:
            quote_age_ms = _finite_float(row.get("quote_age_ms"))
            if (
                quote_age_ms is None
                or quote_age_ms < 0
                or quote_age_ms > selected_config.max_quote_age_ms
            ):
                continue
            market_us = _timestamp_us(row.get("local_receive_timestamp"))
            depth_index = bisect_right(depth_times_us, market_us) - 1
            if depth_index < 0:
                continue
            depth = depths[depth_index]
            depth_age_ms = (market_us - depth_times_us[depth_index]) / 1_000.0
            if depth_age_ms > selected_config.max_depth_age_ms:
                continue
            if (
                _positive_float(row.get("best_bid"))
                != _positive_float(depth.get("best_bid"))
            ):
                continue
            bid_levels = _levels(depth.get("bid_levels"))
            bid_capacity = _capacity_within_slippage(
                bid_levels,
                side="bid",
                max_slippage_bps=selected_config.max_exit_sweep_slippage_bps,
            )
            if bid_capacity is None or bid_capacity < quantity:
                continue
            exit_vwap = _sweep_vwap(bid_levels, quantity)
            if exit_vwap is None:
                continue
            received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
            if stage in entry_like_stages:
                decision_quality_return = (
                    (exit_vwap / baseline_vwap - 1.0) * 10_000.0
                    - float(fixed_cost or 0.0)
                )
            else:
                # Holding/exit compares future executable proceeds with the
                # executable proceeds available at the decision snapshot.  It
                # must never fabricate a new ask-side purchase.
                decision_quality_return = (
                    exit_vwap / baseline_vwap - 1.0
                ) * 10_000.0
            cost_basis_net_return = (
                None
                if position_average_price is None or fixed_cost is None
                else (exit_vwap / position_average_price - 1.0) * 10_000.0
                - fixed_cost
            )
            executable.append(
                (received_ms, decision_quality_return, cost_basis_net_return)
            )
    horizons: list[dict[str, Any]] = []
    for horizon in selected_config.outcome_horizons_sec:
        endpoint_target_ms = start_ms + horizon * 1_000
        endpoint_candidates = [
            row for row in executable if row[0] >= endpoint_target_ms
        ]
        endpoint = endpoint_candidates[0] if endpoint_candidates else None
        endpoint_lag_ms = None if endpoint is None else endpoint[0] - endpoint_target_ms
        bounded = (
            [] if endpoint is None else [row for row in executable if row[0] <= endpoint[0]]
        )
        bounded_market = (
            []
            if endpoint is None
            else [
                row
                for row in rows
                if _timestamp_ms(row.get("local_receive_timestamp")) <= endpoint[0]
            ]
        )
        bounded_depth = (
            []
            if endpoint is None
            else [
                row
                for row in depths
                if start_ms
                < _timestamp_ms(row.get("local_receive_timestamp"))
                <= endpoint[0]
            ]
        )
        horizon_findings = tuple(
            sorted(
                set(
                    _series_sequence_findings(
                        bounded_market, prefix="outcome_market"
                    )
                )
                | set(
                    _series_sequence_findings(
                        bounded_depth, prefix="outcome_depth"
                    )
                )
            )
        )
        boundary_findings: set[str] = set()
        market_anchor_sequence = _nonnegative_int(
            (evidence.get("decision_watermark") or {}).get("source_sequence")
        )
        depth_anchor_sequence = _nonnegative_int(
            (evidence.get("depth_watermark") or {}).get("source_sequence")
        )
        if bounded_market and market_anchor_sequence is not None:
            if int(bounded_market[0].get("source_sequence") or 0) != (
                market_anchor_sequence + 1
            ):
                boundary_findings.add("outcome_market_anchor_sequence_gap")
        if bounded_depth and depth_anchor_sequence is not None:
            if int(bounded_depth[0].get("source_sequence") or 0) != (
                depth_anchor_sequence + 1
            ):
                boundary_findings.add("outcome_depth_anchor_sequence_gap")
        horizon_findings = tuple(
            sorted(set(horizon_findings) | boundary_findings)
        )
        path_times = [start_ms, *(row[0] for row in bounded)]
        max_internal_gap_ms = max(
            (
                right - left
                for left, right in zip(path_times, path_times[1:], strict=False)
            ),
            default=None,
        )
        mature = bool(
            endpoint is not None
            and endpoint_lag_ms is not None
            and endpoint_lag_ms <= selected_config.max_outcome_endpoint_lag_ms
            and max_internal_gap_ms is not None
            and max_internal_gap_ms <= selected_config.max_outcome_internal_gap_ms
            and not horizon_findings
        )
        decision_returns = [row[1] for row in bounded] if mature else []
        cost_basis_returns = (
            [row[2] for row in bounded if row[2] is not None] if mature else []
        )
        horizons.append(
            {
                "horizon_sec": horizon,
                "mature": mature,
                "endpoint_lag_ms": endpoint_lag_ms,
                "endpoint_observed_at_ms": (
                    None if endpoint is None else endpoint[0]
                ),
                "path_continuity_status": (
                    "pass"
                    if mature
                    else (
                        "sequence_gap_or_regression"
                        if horizon_findings
                        else (
                            "endpoint_missing_or_late"
                            if endpoint is None
                            or endpoint_lag_ms is None
                            or endpoint_lag_ms
                            > selected_config.max_outcome_endpoint_lag_ms
                            else "internal_gap_exceeded"
                        )
                    )
                ),
                "max_internal_gap_ms": max_internal_gap_ms,
                "source_quality_blockers": list(horizon_findings),
                "quantity_sweep_observation_count": len(bounded),
                "decision_quality_mfe_bps": (
                    None
                    if not decision_returns
                    else round(max(decision_returns), 6)
                ),
                "decision_quality_mae_bps": (
                    None
                    if not decision_returns
                    else round(min(decision_returns), 6)
                ),
                "position_cost_basis_net_mfe_bps": (
                    None
                    if not cost_basis_returns
                    else round(max(cost_basis_returns), 6)
                ),
                "position_cost_basis_net_mae_bps": (
                    None
                    if not cost_basis_returns
                    else round(min(cost_basis_returns), 6)
                ),
            }
        )
    mature_endpoints = [
        int(row["endpoint_observed_at_ms"])
        for row in horizons
        if row["mature"] is True
    ]
    first_hit_rows = (
        []
        if not mature_endpoints
        else [row for row in executable if row[0] <= max(mature_endpoints)]
    )
    target_first_ms = next(
        (
            observed_ms
            for observed_ms, value, _ in first_hit_rows
            if value >= selected_config.minimum_net_profit_bps
        ),
        None,
    )
    adverse_first_ms = next(
        (
            observed_ms
            for observed_ms, value, _ in first_hit_rows
            if value <= selected_config.adverse_label_bps
        ),
        None,
    )
    if target_first_ms is None and adverse_first_ms is None:
        first_hit = "none_or_unmatured"
    elif target_first_ms is None:
        first_hit = "adverse_first"
    elif adverse_first_ms is None:
        first_hit = "net_target_first"
    elif target_first_ms < adverse_first_ms:
        first_hit = "net_target_first"
    elif adverse_first_ms < target_first_ms:
        first_hit = "adverse_first"
    else:
        first_hit = "ambiguous_same_timestamp"
    outcome_without_hash = {
        "schema": OUTCOME_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "evidence_sha256": evidence.get("evidence_sha256"),
        "label_role": "counterfactual_outcome_only_never_prompt_input",
        "decision_stage": stage,
        "evaluation_basis": evaluation_basis,
        "execution_basis": "same_epoch_fresh_0b_0d_full_quantity_sweep",
        "counterfactual_quantity": quantity,
        "snapshot_execution_basis_vwap": baseline_vwap,
        "position_average_price": position_average_price,
        "outcome_eligibility": (
            "eligible" if not outcome_eligibility_blockers else "source_unavailable"
        ),
        "outcome_eligibility_blockers": sorted(
            set(outcome_eligibility_blockers)
        ),
        "economic_evidence_grade": (
            "reviewed_cost_profile_offline_evaluation_only"
            if selected_config.cost_profile_verified
            and fixed_cost is not None
            else "research_assumption_only"
        ),
        "source_quality_blockers": sorted(
            set(outcome_eligibility_blockers)
            | {
                blocker
                for horizon in horizons
                for blocker in horizon.get("source_quality_blockers") or []
            }
        ),
        "first_hit": first_hit,
        "target_first_delay_ms": (
            None if target_first_ms is None else target_first_ms - start_ms
        ),
        "adverse_first_delay_ms": (
            None if adverse_first_ms is None else adverse_first_ms - start_ms
        ),
        "horizons": horizons,
        **OUTCOME_METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }
    return {
        **outcome_without_hash,
        "outcome_sha256": _sha256(outcome_without_hash),
    }


def _control_decision_findings(
    trace: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if not isinstance(trace, Mapping):
        return ("control_trace_missing",)
    findings: list[str] = []
    if trace.get("provider_called") is not True:
        findings.append("control_provider_not_called")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        findings.append("control_provider_none")
    if trace.get("timeout") is not False:
        findings.append("control_timeout_or_unknown")
    if trace.get("parse_ok") is not True:
        findings.append("control_parse_not_ok")
    if str(trace.get("result_source") or "") != "live":
        findings.append("control_result_not_live")
    if str(trace.get("decision_evaluation_status") or "") != "evaluated":
        findings.append("control_decision_not_evaluated")
    if trace.get("semantic_errors"):
        findings.append("control_semantic_errors_present")
    for field in (
        "endpoint",
        "prompt_version",
        "prompt_sha256",
        "model",
        "transport",
        "response_sha256",
        "request_envelope_sha256",
    ):
        if not str(trace.get(field) or "").strip():
            findings.append(f"control_{field}_missing")
    if not str(trace.get("provider_response_id") or "").strip():
        findings.append("control_provider_response_id_missing")
    if not (
        str(trace.get("response_schema_sha256") or "").strip()
        or str(trace.get("openai_response_schema_mode") or "").strip()
    ):
        findings.append("control_response_schema_contract_missing")
    stage = str(trace.get("decision_stage") or "").lower()
    actions = {
        "entry_screen": {"BUY", "WAIT", "DROP"},
        "entry": {"BUY", "WAIT", "DROP"},
        "entry_price": {
            "USE_DEFENSIVE",
            "USE_REFERENCE",
            "IMPROVE_LIMIT",
            "SKIP",
        },
        "holding": {"HOLD", "TRIM", "EXIT"},
        "holding_score": {"HOLD", "TRIM", "EXIT"},
        "holding_flow": {"HOLD", "TRIM", "EXIT"},
        "post_probe": {"CONTINUE", "STOP"},
        "scale_in": {"ADD", "NO_ADD"},
        "exit": {"HOLD", "TRIM", "EXIT"},
        "overnight": {"HOLD_OVERNIGHT", "EXIT_BEFORE_CLOSE"},
    }
    action = str(trace.get("action") or "").upper()
    if stage not in actions or action not in actions[stage]:
        findings.append("control_stage_action_invalid")
    if stage in {"entry", "entry_screen"} and str(
        trace.get("decision_quality_contract_status") or ""
    ) != "pass":
        findings.append("control_entry_semantic_contract_not_pass")
    if stage == "entry_price" and str(
        trace.get("entry_price_v2_5_contract_status") or ""
    ) != "pass":
        findings.append("control_entry_price_semantic_contract_not_pass")
    return tuple(sorted(set(findings)))


def build_three_arm_manifest(
    *,
    evidence: Mapping[str, Any],
    control_prompt_version: str,
    control_contract: Mapping[str, Any] | None = None,
    control_trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe three replay arms plus a non-comparable captured reference."""

    exact_hash = str(evidence.get("source_exact_payload_sha256") or "")
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    base_identity = {"source_exact_payload_sha256": exact_hash}
    enriched_identity = {
        **base_identity,
        "tactical_micro_reversion_evidence_sha256": evidence_hash,
    }
    base_pair_hash = _sha256(base_identity)
    enriched_pair_hash = _sha256(enriched_identity)
    contract = dict(control_contract or {})
    locked_contract = {
        "prompt_sha256": contract.get("prompt_sha256"),
        "provider": contract.get("provider"),
        "model": contract.get("model"),
        "temperature": contract.get("temperature"),
        "reasoning_effort": contract.get("reasoning_effort"),
        "response_schema_sha256": contract.get("response_schema_sha256"),
        "semantic_validator_version": contract.get(
            "semantic_validator_version"
        ),
    }
    observation_context_eligible = bool(
        (evidence.get("source_quality") or {}).get("status") == "pass"
        and evidence.get("state") not in {"not_applicable", "source_unavailable"}
    )
    semantic_identity_verified = (
        evidence.get("exact_replay_source_semantic_status")
        == "stored_semantic_hash_verified"
    )
    context_eligible = observation_context_eligible and semantic_identity_verified
    control_findings = _control_decision_findings(control_trace)
    control_eligible = not control_findings
    economic_eligible = bool(
        context_eligible
        and (evidence.get("source_quality") or {}).get(
            "liquidity_capacity_status"
        )
        == "pass"
        and (evidence.get("economics") or {}).get("cost_profile_verified") is True
        and (evidence.get("economics") or {}).get("minimum_gross_target_bps")
        is not None
    )
    return {
        "schema": THREE_ARM_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "captured_natural_reference": {
            "prompt_version": control_prompt_version,
            **locked_contract,
            "provider_user_input_sha256": evidence.get(
                "source_provider_payload_sha256"
            ),
            "request_envelope_sha256": evidence.get(
                "source_request_envelope_sha256"
            ),
            "comparable_as_micro_only_arm": False,
            "reason": "captured_provider_input_representation_differs_from_replay_input",
        },
        "replay_arms": [
            {
                "arm": "replay_control_exact_no_micro",
                "prompt_version": control_prompt_version,
                **locked_contract,
                **base_identity,
                "analytical_context_pair_sha256": base_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": "replay_request_materialization_required",
            },
            {
                "arm": "replay_control_exact_plus_micro",
                "prompt_version": control_prompt_version,
                **locked_contract,
                **enriched_identity,
                "analytical_context_pair_sha256": enriched_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": "replay_request_materialization_required",
            },
            {
                "arm": "replay_candidate_exact_plus_micro",
                "prompt_version": None,
                "status": "candidate_prompt_contract_required",
                "provider": contract.get("provider"),
                "model": contract.get("model"),
                "temperature": contract.get("temperature"),
                "reasoning_effort": contract.get("reasoning_effort"),
                **enriched_identity,
                "analytical_context_pair_sha256": enriched_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": "candidate_prompt_contract_required",
            },
        ],
        "micro_effect_comparison": (
            "replay_control_exact_no_micro_vs_replay_control_exact_plus_micro"
        ),
        "prompt_effect_comparison": (
            "replay_control_exact_plus_micro_vs_replay_candidate_exact_plus_micro"
        ),
        "identical_exact_payload_across_replay_arms": True,
        "identical_micro_context_between_enriched_replay_arms": True,
        "actual_provider_input_hash_parity_verified": False,
        "provider_call_performed": False,
        "replay_context_eligible": context_eligible,
        "observation_context_eligible": observation_context_eligible,
        "provider_input_semantic_identity_verified": semantic_identity_verified,
        "control_decision_eligible": control_eligible,
        "control_decision_exclusion_reasons": list(control_findings),
        "paired_decision_quality_eligible": context_eligible and control_eligible,
        "net_economic_evaluation_eligible": economic_eligible,
        "promotion_evidence_eligible": False,
        **AUTHORITY_CONTRACT,
    }


def _validate_tactical_evidence_shape(evidence: Mapping[str, Any]) -> None:
    top_level = {
        "schema",
        "evidence_version",
        "decision_trace_id",
        "request_id",
        "decision_stage",
        "source_provider_payload_sha256",
        "source_exact_payload_sha256",
        "source_request_envelope_sha256",
        "snapshot_id",
        "stock_code",
        "trace_effective_venue",
        "trace_session_bucket",
        "micro_venue",
        "micro_session_bucket",
        "sequence_epoch",
        "snapshot_captured_at",
        "snapshot_captured_at_ms",
        "provider_payload_semantic_hash_status",
        "exact_replay_source_semantic_status",
        "decision_watermark",
        "depth_watermark",
        "state",
        "event",
        "tape",
        "orderbook",
        "economics",
        "liquidity_capacity",
        "source_quality",
        LIFECYCLE_PROJECTION_SCHEMA,
        "evidence_sha256",
        *METRIC_CONTRACT,
        *AUTHORITY_CONTRACT,
    }
    unknown = set(evidence) - top_level
    if unknown:
        raise ValueError(
            "micro_context_unknown_top_level_field:" + ",".join(sorted(unknown))
        )

    allowed_by_path: dict[tuple[str, ...], set[str]] = {
        ("decision_watermark",): {
            "local_receive_timestamp",
            "source_sequence",
            "past_only_join",
        },
        ("depth_watermark",): {
            "local_receive_timestamp",
            "source_sequence",
            "past_only_join",
        },
        ("event",): {
            "parent_wave_id",
            "path_segment_id",
            "shock_event_id",
            "shock_horizon_ms",
            "event_sequence_in_wave",
            "event_detected_at_ms",
            "event_source_sequence",
            "reference_price",
            "shock_price",
            "post_shock_low_price",
            "asof_trade_price",
            "shock_bps",
            "reclaim_from_low_bps",
            "reclaim_fraction",
            "remaining_to_reference_bps",
            "half_reclaim_first_source_sequence",
            "half_reclaim_reference_low_price",
            "new_low_after_half_reclaim",
            "recovery_invalidation_count",
            "latest_recovery_cycle_reconfirmed",
        },
        ("tape",): {
            "early",
            "recent",
            "window_sec",
            "early_window_end_ms",
            "recent_window_start_ms",
            "deceleration_windows_nonoverlap",
            "sell_pressure_deceleration",
        },
        ("tape", "early"): {
            "buy_qty",
            "sell_qty",
            "unknown_qty",
            "known_qty",
            "buy_ratio",
            "sell_ratio",
            "sample_count",
        },
        ("tape", "recent"): {
            "buy_qty",
            "sell_qty",
            "unknown_qty",
            "known_qty",
            "buy_ratio",
            "sell_ratio",
            "sample_count",
        },
        ("orderbook",): {
            "best_bid",
            "best_ask",
            "best_bid_qty",
            "best_ask_qty",
            "bid_depth",
            "ask_depth",
            "spread_bps",
            "same_epoch_bid_depth_change_qty",
            "bid_replenishment_same_price_basis",
            "bid_replenishment_price_path_status",
            "depth_age_ms",
            "depth_join_status",
        },
        ("economics",): {
            "cost_profile_source",
            "cost_profile_verified",
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
            "counterfactual_roundtrip_execution_bps",
            "spread_double_counted",
            "all_in_cost_bps",
            "minimum_net_profit_bps",
            "minimum_gross_target_bps",
            "economic_source_quality_status",
        },
        ("liquidity_capacity",): {
            "capacity_quality_status",
            "target_liquidation_sec",
            "recent_tape_window_sec",
            "recent_aggressive_buy_qty",
            "aggressive_buy_role",
            "counterfactual_liquidity_qty_grid",
            "counterfactual_liquidity_qty_ceiling",
            "counterfactual_immediate_exit_qty_ceiling",
            "existing_position_formula_candidate_qty",
            "existing_quantity_provenance",
            "existing_quantity_owner",
            "future_candidate_composition_rule",
        },
        ("liquidity_capacity", "existing_quantity_provenance"): {
            "status",
            "quantity",
            "pointer",
            "owner",
        },
        ("source_quality",): {
            "status",
            "blockers",
            "liquidity_capacity_status",
            "liquidity_capacity_blockers",
            "rejected_market_reason_counts",
            "rejected_depth_reason_counts",
            "rejected_reference_reason_counts",
            "parent_wave_reference_count",
            "parent_wave_deduplicated",
            "future_outcome_fields_in_context",
        },
        (LIFECYCLE_PROJECTION_SCHEMA,): {
            "schema",
            "objective",
            "decision_stage",
            "entry_projection",
            "holding_projection",
            "exit_projection",
            *AUTHORITY_CONTRACT,
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "entry_projection"): {
            "timing_owner",
            "ai_role",
            "minimum_gross_target_bps",
            "counterfactual_fast_roundtrip_capacity_qty",
            "counterfactual_full_position_exit_sweep_vwap",
            "live_price_or_order_effect",
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "holding_projection"): {
            "review_cadence",
            "observed_position_qty",
            "counterfactual_free_to_sell_qty",
            "observed_position_average_price",
            "position_provenance",
            "counterfactual_fast_exit_capacity_qty",
            "counterfactual_snapshot_exit_sweep_vwap",
            "counterfactual_capacity_coverage_ratio",
            "counterfactual_uncovered_position_qty",
            "counterfactual_net_executable_pnl_bps",
            "scale_in_requires_fresh_recovery_and_verified_exit_capacity",
            "hard_protect_emergency_exit_priority_unchanged",
        },
        (
            LIFECYCLE_PROJECTION_SCHEMA,
            "holding_projection",
            "position_provenance",
        ): {
            "status",
            "quantity",
            "free_to_sell_quantity",
            "average_price",
            "open_sell_qty",
            "cancel_pending",
            "exit_token_active",
            "quantity_conflict",
            "quantity_pointer",
            "free_to_sell_quantity_formula",
            "price_pointer",
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "exit_projection"): {
            "profit_basis",
            "minimum_net_profit_bps",
            "counterfactual_net_target_reached",
            "counterfactual_immediately_executable_qty",
            "hard_protect_emergency_exit_priority_unchanged",
            "live_sell_or_cancel_effect",
        },
    }
    for path, allowed in allowed_by_path.items():
        value: Any = evidence
        for key in path:
            value = value.get(key) if isinstance(value, Mapping) else None
        if isinstance(value, Mapping):
            unknown = set(value) - allowed
            if unknown:
                raise ValueError(
                    "micro_context_unknown_field:"
                    + "/".join(path)
                    + ":"
                    + ",".join(sorted(unknown))
                )
    grid = (evidence.get("liquidity_capacity") or {}).get(
        "counterfactual_liquidity_qty_grid"
    )
    allowed_grid_fields = {
        "participation_rate",
        "entry_ask_capacity_qty",
        "depth_only_fast_exit_capacity_qty",
        "immediate_roundtrip_depth_capacity_qty",
        "immediate_marketable_exit_capacity_qty",
        "passive_ask_fill_support_qty",
        "counterfactual_liquidity_bounded_qty",
        "counterfactual_entry_sweep_vwap",
        "counterfactual_exit_sweep_vwap",
        "counterfactual_roundtrip_execution_bps",
    }
    if isinstance(grid, list) and any(
        not isinstance(row, Mapping) or set(row) - allowed_grid_fields for row in grid
    ):
        raise ValueError("micro_context_liquidity_grid_schema_invalid")


def _validate_replay_candidate_ledgers(
    *,
    candidate_input: Mapping[str, Any],
    exact_payload: Mapping[str, Any],
    request: Mapping[str, Any],
    decision_stage: str,
) -> None:
    """Rebuild every optional ledger from the immutable exact payload."""

    ledger_keys = set(candidate_input) - {"exact_payload"}
    if not ledger_keys:
        return
    # Lazy imports keep the source-only bridge import-independent from the
    # provider replay implementation while still using its canonical builders.
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.entry_setup_evidence import build_entry_setup_evidence

    stage = str(request.get("stage") or decision_stage or "").strip().lower()
    normalized_stage = (
        "entry"
        if stage in {"entry", "entry_screen", "gatekeeper", "post_probe"}
        else (
            "holding"
            if stage in {"holding", "holding_score", "holding_flow", "exit"}
            else stage
        )
    )
    expected: dict[str, Mapping[str, Any]] = {}
    if "exact_payload_analysis_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("exact_payload_analysis_stage_invalid")
        expected["exact_payload_analysis_v1"] = (
            quality.build_exact_payload_analysis_v1(
                dict(exact_payload), stage="entry"
            )
        )
    if "anticipatory_reversal_analysis_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("anticipatory_reversal_analysis_stage_invalid")
        base = quality.build_anticipatory_reversal_analysis_v1(
            dict(exact_payload), stage="entry"
        )
        selective = quality._attach_selective_recovery_probe_contract_v1(base)
        recovery = quality.build_v2_13_recovery_confirmation_analysis_v1(
            dict(exact_payload), stage="entry"
        )
        supplied = candidate_input["anticipatory_reversal_analysis_v1"]
        if not any(
            _sha256(supplied) == _sha256(candidate)
            for candidate in (base, selective, recovery)
        ):
            raise ValueError(
                "candidate_input_ledger_rebuild_mismatch:"
                "anticipatory_reversal_analysis_v1"
            )
        expected["anticipatory_reversal_analysis_v1"] = supplied
    if "holding_exact_contract_facts_v1" in ledger_keys:
        if normalized_stage != "holding":
            raise ValueError("holding_exact_contract_facts_stage_invalid")
        expected["holding_exact_contract_facts_v1"] = (
            quality._holding_contract_facts(dict(exact_payload))
        )
    if "entry_price_exact_contract_facts_v1" in ledger_keys:
        if normalized_stage != "entry_price":
            raise ValueError("entry_price_exact_contract_facts_stage_invalid")
        control = request.get("control")
        control = control if isinstance(control, Mapping) else {}
        captured_action = str(control.get("captured_action") or "").upper()
        if not captured_action:
            raise ValueError("entry_price_control_action_missing")
        expected["entry_price_exact_contract_facts_v1"] = (
            quality.build_entry_price_explicit_fill_value_contract(
                dict(exact_payload),
                control_selected_price=control.get("captured_selected_price"),
                control_exposure_selected=captured_action != "SKIP",
            )
        )
    if "entry_setup_evidence_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("entry_setup_evidence_stage_invalid")
        exact_analysis = candidate_input.get("exact_payload_analysis_v1")
        recovery_analysis = candidate_input.get(
            "anticipatory_reversal_analysis_v1"
        )
        if not isinstance(exact_analysis, Mapping) or not isinstance(
            recovery_analysis, Mapping
        ):
            raise ValueError("entry_setup_evidence_dependencies_missing")
        expected["entry_setup_evidence_v1"] = build_entry_setup_evidence(
            exact_payload=dict(exact_payload),
            exact_analysis=dict(exact_analysis),
            recovery_analysis=dict(recovery_analysis),
        )
    for ledger_key, expected_ledger in expected.items():
        if _sha256(candidate_input.get(ledger_key)) != _sha256(expected_ledger):
            raise ValueError(
                f"candidate_input_ledger_rebuild_mismatch:{ledger_key}"
            )


def attach_micro_context_to_replay_request(
    request: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    source_trace: Mapping[str, Any] | None = None,
    source_payload: Mapping[str, Any] | None = None,
    source_market_rows: Iterable[Mapping[str, Any]] = (),
    source_depth_rows: Iterable[Mapping[str, Any]] = (),
    source_event_references: Iterable[Mapping[str, Any]] = (),
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
) -> dict[str, Any]:
    """Opt-in replay enrichment; default Exact V2 request remains unchanged."""

    def contains_outcome_only_field(value: Any) -> bool:
        return any(
            key in OUTCOME_ONLY_FIELD_NAMES
            or key.startswith("post_decision_")
            or key.startswith("realized_")
            for row in _walk_objects(value)
            for key in row
        )

    if contains_outcome_only_field(evidence):
        raise ValueError("future_outcome_field_forbidden_in_context")
    for field, expected in AUTHORITY_CONTRACT.items():
        if field == "selection_authority":
            if field in request and request.get(field) is not expected:
                raise ValueError(f"request_authority_conflict:{field}")
            continue
        if request.get(field) is not expected:
            raise ValueError(f"request_authority_conflict:{field}")
    allowed_request_authorities = {
        "offline_replay_and_attribution_only",
        "offline_replay_no_runtime_change",
        "offline_supplemental_replay_no_runtime_change",
    }
    if request.get("decision_authority") not in allowed_request_authorities:
        raise ValueError("request_decision_authority_invalid")
    if evidence.get("schema") != TACTICAL_EVIDENCE_SCHEMA:
        raise ValueError("micro_context_schema_invalid")
    _validate_tactical_evidence_shape(evidence)
    if not isinstance(source_trace, Mapping) or not isinstance(
        source_payload, Mapping
    ):
        raise ValueError("micro_context_source_rebuild_required")
    rebuilt_evidence = build_tactical_evidence(
        trace=source_trace,
        payload=source_payload,
        market_rows=source_market_rows,
        depth_rows=source_depth_rows,
        event_references=source_event_references,
        config=config,
        excluded_scopes=excluded_scopes,
    )
    if _sha256(rebuilt_evidence) != _sha256(evidence):
        raise ValueError("micro_context_source_rebuild_mismatch")
    for field, expected in AUTHORITY_CONTRACT.items():
        if evidence.get(field) is not expected:
            raise ValueError(f"micro_context_authority_invalid:{field}")
    for field, expected in METRIC_CONTRACT.items():
        if _sha256(evidence.get(field)) != _sha256(expected):
            raise ValueError(f"micro_context_metric_contract_invalid:{field}")
    stored_evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_without_hash = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if not stored_evidence_hash or _sha256(evidence_without_hash) != stored_evidence_hash:
        raise ValueError("micro_context_evidence_sha256_mismatch")
    expected_trace = str(request.get("decision_trace_id") or "")
    if expected_trace != str(evidence.get("decision_trace_id") or ""):
        raise ValueError("decision_trace_id_mismatch")
    if normalize_symbol(request.get("stock_code")) != normalize_symbol(
        evidence.get("stock_code")
    ):
        raise ValueError("request_stock_code_mismatch")
    if _exact_venue(request.get("effective_venue")) != _exact_venue(
        evidence.get("trace_effective_venue")
    ):
        raise ValueError("request_effective_venue_mismatch")
    if _session(request.get("session_bucket")) != _session(
        evidence.get("trace_session_bucket")
    ):
        raise ValueError("request_session_bucket_mismatch")
    stage_alias = {
        "entry_screen": "entry",
        "holding_score": "holding",
        "holding_flow": "holding",
    }
    request_stage = stage_alias.get(
        str(request.get("stage") or "").lower(),
        str(request.get("stage") or "").lower(),
    )
    evidence_stage = stage_alias.get(
        str(evidence.get("decision_stage") or "").lower(),
        str(evidence.get("decision_stage") or "").lower(),
    )
    if not request_stage or request_stage != evidence_stage:
        raise ValueError("request_decision_stage_mismatch")
    if str(request.get("endpoint") or "") != str(
        source_payload.get("endpoint") or source_trace.get("endpoint") or ""
    ):
        raise ValueError("request_endpoint_mismatch")
    exact_payload = request.get("exact_payload")
    if not isinstance(exact_payload, dict):
        raise ValueError("exact_payload_missing")
    if _sha256(exact_payload) != str(
        request.get("source_exact_payload_sha256")
        or evidence.get("source_exact_payload_sha256")
        or ""
    ):
        raise ValueError("exact_payload_sha256_mismatch")
    if str(request.get("payload_sha256") or "") != str(
        evidence.get("source_provider_payload_sha256") or ""
    ):
        raise ValueError("provider_payload_sha256_mismatch")
    if str(request.get("request_envelope_sha256") or "") != str(
        evidence.get("source_request_envelope_sha256") or ""
    ):
        raise ValueError("request_envelope_sha256_mismatch")
    if (evidence.get("source_quality") or {}).get("status") != "pass":
        raise ValueError("micro_context_source_quality_not_pass")
    if evidence.get("state") in {"not_applicable", "source_unavailable", None}:
        raise ValueError("micro_context_state_not_replay_eligible")
    if (
        evidence.get("exact_replay_source_semantic_status")
        != "stored_semantic_hash_verified"
    ):
        raise ValueError("exact_replay_source_semantic_identity_unverified")
    allowed_schemas = {TACTICAL_EVIDENCE_SCHEMA, LIFECYCLE_PROJECTION_SCHEMA}
    if any(
        row.get("schema") not in allowed_schemas
        for row in _walk_objects(evidence)
        if "schema" in row
    ):
        raise ValueError("micro_context_nested_schema_invalid")
    candidate_input = request.get("candidate_input")
    candidate_input = (
        deepcopy(candidate_input)
        if isinstance(candidate_input, dict)
        else {"exact_payload": deepcopy(exact_payload)}
    )
    allowed_candidate_input_keys = {
        "exact_payload",
        *REPLAY_CANDIDATE_LEDGER_SCHEMAS,
    }
    unexpected_keys = set(candidate_input) - allowed_candidate_input_keys
    if unexpected_keys:
        raise ValueError(
            "candidate_input_unknown_ledger:" + ",".join(sorted(unexpected_keys))
        )
    existing_exact = candidate_input.get("exact_payload")
    if not isinstance(existing_exact, dict) or _sha256(existing_exact) != _sha256(
        exact_payload
    ):
        raise ValueError("candidate_input_exact_payload_mismatch")
    for ledger_key in set(candidate_input) - {"exact_payload"}:
        ledger = candidate_input.get(ledger_key)
        if not isinstance(ledger, Mapping) or ledger.get("schema") != ledger_key:
            raise ValueError(f"candidate_input_ledger_schema_invalid:{ledger_key}")
        unexpected_ledger_fields = set(ledger) - REPLAY_CANDIDATE_LEDGER_FIELDS[
            ledger_key
        ]
        if unexpected_ledger_fields:
            raise ValueError(
                "candidate_input_ledger_unknown_field:"
                + ledger_key
                + ":"
                + ",".join(sorted(unexpected_ledger_fields))
            )
        if any(
            "oracle" in key.lower()
            or key.lower().startswith(("future_", "post_decision_", "realized_"))
            or key.lower() in OUTCOME_ONLY_FIELD_NAMES
            for row in _walk_objects(ledger)
            for key in row
        ):
            raise ValueError(f"candidate_input_ledger_causal_field:{ledger_key}")
        if ledger_key in {
            "exact_payload_analysis_v1",
            "anticipatory_reversal_analysis_v1",
        }:
            stored_hash = str(ledger.get("analysis_sha256") or "")
            without_hash = {
                key: value
                for key, value in ledger.items()
                if key != "analysis_sha256"
            }
            if not stored_hash or _sha256(without_hash) != stored_hash:
                raise ValueError(
                    f"candidate_input_ledger_sha256_invalid:{ledger_key}"
                )
        elif ledger_key == "entry_setup_evidence_v1":
            stored_hash = str(ledger.get("evidence_sha256") or "")
            without_hash = {
                key: value
                for key, value in ledger.items()
                if key != "evidence_sha256"
            }
            if not stored_hash or _sha256(without_hash) != stored_hash:
                raise ValueError(
                    f"candidate_input_ledger_sha256_invalid:{ledger_key}"
                )
    if any(
        contains_outcome_only_field(value)
        for key, value in candidate_input.items()
        if key != "exact_payload"
    ):
        raise ValueError("candidate_input_future_outcome_forbidden")
    stored_candidate_hash = request.get("candidate_input_sha256")
    if request.get("candidate_input") is not None and not stored_candidate_hash:
        raise ValueError("candidate_input_sha256_missing")
    if stored_candidate_hash and str(stored_candidate_hash) != _sha256(candidate_input):
        raise ValueError("candidate_input_sha256_mismatch")
    _validate_replay_candidate_ledgers(
        candidate_input=candidate_input,
        exact_payload=exact_payload,
        request=request,
        decision_stage=str(evidence.get("decision_stage") or ""),
    )
    candidate_input[TACTICAL_EVIDENCE_SCHEMA] = deepcopy(dict(evidence))
    copied_request = deepcopy(dict(request))
    return {
        **copied_request,
        "exact_payload": deepcopy(exact_payload),
        "candidate_input": candidate_input,
        "candidate_input_sha256": _sha256(candidate_input),
        "tactical_micro_reversion_evidence_sha256": evidence.get(
            "evidence_sha256"
        ),
        "micro_reversion_replay_opt_in": True,
        **AUTHORITY_CONTRACT,
    }


def _payload_indexes(
    payloads: Sequence[Mapping[str, Any]],
) -> tuple[
    dict[str, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
]:
    by_request: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_envelope: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_payload_hash: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in payloads:
        if row.get("request_id"):
            by_request[str(row.get("request_id"))].append(row)
        if row.get("request_envelope_sha256"):
            by_envelope[str(row.get("request_envelope_sha256"))].append(row)
        if row.get("payload_sha256"):
            by_payload_hash[str(row.get("payload_sha256"))].append(row)
    return by_request, by_envelope, by_payload_hash


def _consistent_payload_candidate(
    rows: Sequence[Mapping[str, Any]], *, expected_payload_sha256: str
) -> Mapping[str, Any] | None:
    matching = [
        row
        for row in rows
        if not expected_payload_sha256
        or str(row.get("payload_sha256") or "") == expected_payload_sha256
    ]
    if not matching:
        return None
    identities = {
        (
            str(row.get("payload_sha256") or ""),
            str(row.get("request_envelope_sha256") or ""),
            str(row.get("replay_context_sha256") or ""),
        )
        for row in matching
    }
    return matching[0] if len(identities) == 1 else None


def _resolve_payload_for_trace(
    trace: Mapping[str, Any],
    *,
    indexes: tuple[
        dict[str, list[Mapping[str, Any]]],
        dict[str, list[Mapping[str, Any]]],
        dict[str, list[Mapping[str, Any]]],
    ],
) -> tuple[Mapping[str, Any] | None, str]:
    by_request, by_envelope, by_payload_hash = indexes
    payload_hash = str(trace.get("payload_sha256") or "")
    request_id = str(trace.get("request_id") or "")
    if request_id:
        direct = _consistent_payload_candidate(
            by_request.get(request_id, ()), expected_payload_sha256=payload_hash
        )
        if direct is not None:
            return direct, "request_id"
    envelope_hash = str(trace.get("request_envelope_sha256") or "")
    envelope = _consistent_payload_candidate(
        by_envelope.get(envelope_hash, ()), expected_payload_sha256=payload_hash
    )
    if envelope is not None:
        return envelope, "request_envelope_sha256"
    hashed = _consistent_payload_candidate(
        by_payload_hash.get(payload_hash, ()), expected_payload_sha256=payload_hash
    )
    if hashed is not None and len(by_payload_hash.get(payload_hash, ())) == 1:
        return hashed, "unique_payload_sha256"
    return None, "missing_or_ambiguous"


def build_bridge_report(
    *,
    target_date: str,
    traces: Iterable[Mapping[str, Any]],
    payloads: Iterable[Mapping[str, Any]],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    date_value = date.fromisoformat(target_date)
    if date_value < CLEAN_BASELINE_DATE:
        raise ValueError("target date is before clean tuning baseline")
    selected_config = config or BridgeConfig()
    trace_rows = [row for row in traces if isinstance(row, Mapping)]
    payload_rows = [row for row in payloads if isinstance(row, Mapping)]
    market = [row for row in market_rows if isinstance(row, Mapping)]
    depth = [row for row in depth_rows if isinstance(row, Mapping)]
    references = [row for row in event_references if isinstance(row, Mapping)]
    payload_indexes = _payload_indexes(payload_rows)
    market_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for row in market:
        market_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    depth_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for row in depth:
        depth_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    references_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for row in references:
        references_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    def safe_receive_us(row: Mapping[str, Any]) -> int | None:
        try:
            return _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            return None

    invalid_market_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    market_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in market_by_scope.items():
        invalid_market_by_scope[key] = tuple(
            row for row in scoped_rows if safe_receive_us(row) is None
        )
        scoped_rows[:] = [row for row in scoped_rows if safe_receive_us(row) is not None]
        scoped_rows.sort(
            key=lambda row: (
                int(safe_receive_us(row) or 0),
                _nonnegative_int(row.get("source_sequence")) or 0,
            )
        )
        market_times_by_scope[key] = tuple(
            int(safe_receive_us(row) or 0)
            for row in scoped_rows
        )
    invalid_depth_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    depth_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in depth_by_scope.items():
        invalid_depth_by_scope[key] = tuple(
            row for row in scoped_rows if safe_receive_us(row) is None
        )
        scoped_rows[:] = [row for row in scoped_rows if safe_receive_us(row) is not None]
        scoped_rows.sort(
            key=lambda row: (
                int(safe_receive_us(row) or 0),
                _nonnegative_int(row.get("source_sequence")) or 0,
            )
        )
        depth_times_by_scope[key] = tuple(
            int(safe_receive_us(row) or 0)
            for row in scoped_rows
        )
    invalid_references_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    reference_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in references_by_scope.items():
        invalid_references_by_scope[key] = tuple(
            row
            for row in scoped_rows
            if _nonnegative_int(row.get("event_detected_at_ms")) is None
        )
        scoped_rows[:] = [
            row
            for row in scoped_rows
            if _nonnegative_int(row.get("event_detected_at_ms")) is not None
        ]
        scoped_rows.sort(key=lambda row: int(row.get("event_detected_at_ms") or 0))
        reference_times_by_scope[key] = tuple(
            int(row.get("event_detected_at_ms") or 0) * 1_000
            for row in scoped_rows
        )

    def bounded_rows(
        scoped_rows: Sequence[Mapping[str, Any]],
        times: Sequence[int],
        *,
        start_us: int,
        end_us: int,
    ) -> Sequence[Mapping[str, Any]]:
        left = bisect_left(times, start_us)
        right = bisect_right(times, end_us)
        return scoped_rows[left:right]

    rows = []
    exclusions = Counter()
    for trace in trace_rows:
        payload, payload_join_mode = _resolve_payload_for_trace(
            trace, indexes=payload_indexes
        )
        if payload is None:
            exclusions["payload_join_missing_or_ambiguous"] += 1
            continue
        resolved_scope = resolve_micro_scope(trace)
        scope_key = (
            normalize_symbol(trace.get("stock_code")),
            resolved_scope.venue,
            resolved_scope.session_bucket,
        )
        watermark, _ = exact_snapshot_watermark(trace, payload)
        watermark_us = int((watermark or {}).get("captured_at_us") or 0)
        context_start_us = max(
            0,
            watermark_us
            - (
                selected_config.active_wave_max_age_sec
                + selected_config.context_lookback_sec
            )
            * 1_000_000,
        )
        outcome_end_us = watermark_us + (
            selected_config.outcome_horizons_sec[-1] * 1_000
            + selected_config.max_outcome_endpoint_lag_ms
        ) * 1_000
        scoped_market = market_by_scope.get(scope_key, ())
        scoped_depth = depth_by_scope.get(scope_key, ())
        scoped_references = references_by_scope.get(scope_key, ())
        trace_market_rows = [
            *bounded_rows(
                scoped_market,
                market_times_by_scope.get(scope_key, ()),
                start_us=context_start_us,
                end_us=outcome_end_us,
            ),
            *invalid_market_by_scope.get(scope_key, ()),
        ]
        trace_depth_rows = [
            *bounded_rows(
                scoped_depth,
                depth_times_by_scope.get(scope_key, ()),
                start_us=context_start_us,
                end_us=outcome_end_us,
            ),
            *invalid_depth_by_scope.get(scope_key, ()),
        ]
        trace_references = [
            *bounded_rows(
                scoped_references,
                reference_times_by_scope.get(scope_key, ()),
                start_us=context_start_us,
                end_us=watermark_us,
            ),
            *invalid_references_by_scope.get(scope_key, ()),
        ]
        evidence = build_tactical_evidence(
            trace=trace,
            payload=payload,
            market_rows=trace_market_rows,
            depth_rows=trace_depth_rows,
            event_references=trace_references,
            config=selected_config,
            excluded_scopes=excluded_scopes,
        )
        state = str(evidence.get("state") or "source_unavailable")
        wave_id = str((evidence.get("event") or {}).get("parent_wave_id") or "")
        wave_key = (
            normalize_symbol(evidence.get("stock_code")),
            str(evidence.get("micro_venue") or ""),
            str(evidence.get("micro_session_bucket") or ""),
            str(trace.get("decision_stage") or ""),
            wave_id,
        )
        outcome = build_future_outcome(
            evidence=evidence,
            market_rows=trace_market_rows,
            depth_rows=trace_depth_rows,
            config=selected_config,
        )
        row = {
            "decision_trace_id": trace.get("decision_trace_id"),
            "decision_stage": trace.get("decision_stage"),
            "provider_actual": trace.get("provider_actual"),
            "prompt_version": trace.get("prompt_version"),
            "payload_join_mode": payload_join_mode,
            "_parent_wave_stage_key": wave_key if wave_id else None,
            "primary_parent_wave_stage_row": False,
            "primary_replay_parent_wave_stage_row": False,
            "primary_control_parent_wave_stage_row": False,
            "primary_paired_parent_wave_stage_row": False,
            "primary_economic_parent_wave_stage_row": False,
            "primary_mature_outcome_parent_wave_stage_row": False,
            "same_parent_wave_repeat": False,
            TACTICAL_EVIDENCE_SCHEMA: evidence,
            "future_outcome": outcome,
            "three_arm_manifest": build_three_arm_manifest(
                evidence=evidence,
                control_prompt_version=str(trace.get("prompt_version") or "unknown"),
                control_trace=trace,
                control_contract={
                    "prompt_sha256": trace.get("prompt_sha256"),
                    "provider": trace.get("provider_actual"),
                    "model": trace.get("model"),
                    "temperature": trace.get("request_temperature"),
                    "reasoning_effort": trace.get("request_reasoning_effort"),
                    "response_schema_sha256": trace.get(
                        "response_schema_sha256"
                    ),
                    "semantic_validator_version": trace.get(
                        "semantic_validator_version"
                    ),
                },
            ),
        }
        rows.append(row)
        if state == "source_unavailable":
            for reason in (evidence.get("source_quality") or {}).get("blockers") or []:
                exclusions[str(reason)] += 1
    grouped_wave_rows: dict[tuple[str, str, str, str, str], list[int]] = (
        defaultdict(list)
    )
    for index, row in enumerate(rows):
        wave_key = row.get("_parent_wave_stage_key")
        if isinstance(wave_key, tuple):
            grouped_wave_rows[wave_key].append(index)
    for indexes in grouped_wave_rows.values():
        observation_indexes = [
            index
            for index in indexes
            if (
                rows[index][TACTICAL_EVIDENCE_SCHEMA].get("source_quality") or {}
            ).get("status")
            == "pass"
            and rows[index][TACTICAL_EVIDENCE_SCHEMA].get("state")
            not in {"not_applicable", "source_unavailable"}
        ]
        ranked_indexes = observation_indexes or indexes
        primary_index = min(
            ranked_indexes,
            key=lambda index: int(
                rows[index][TACTICAL_EVIDENCE_SCHEMA].get(
                    "snapshot_captured_at_ms"
                )
                or 0
            ),
        )
        for index in indexes:
            rows[index]["primary_parent_wave_stage_row"] = index == primary_index
            rows[index]["same_parent_wave_repeat"] = index != primary_index
        metric_predicates = {
            "primary_replay_parent_wave_stage_row": lambda row: row[
                "three_arm_manifest"
            ].get("replay_context_eligible")
            is True,
            "primary_control_parent_wave_stage_row": lambda row: row[
                "three_arm_manifest"
            ].get("control_decision_eligible")
            is True,
            "primary_paired_parent_wave_stage_row": lambda row: row[
                "three_arm_manifest"
            ].get("paired_decision_quality_eligible")
            is True,
            "primary_economic_parent_wave_stage_row": lambda row: row[
                "three_arm_manifest"
            ].get("net_economic_evaluation_eligible")
            is True,
            "primary_mature_outcome_parent_wave_stage_row": lambda row: any(
                horizon.get("mature") is True
                for horizon in (row.get("future_outcome") or {}).get("horizons")
                or []
            ),
        }
        for flag, predicate in metric_predicates.items():
            eligible = [index for index in indexes if predicate(rows[index])]
            if not eligible:
                continue
            selected = min(
                eligible,
                key=lambda index: int(
                    rows[index][TACTICAL_EVIDENCE_SCHEMA].get(
                        "snapshot_captured_at_ms"
                    )
                    or 0
                ),
            )
            rows[selected][flag] = True
    for row in rows:
        row.pop("_parent_wave_stage_key", None)
    state_counts = Counter(
        str((row[TACTICAL_EVIDENCE_SCHEMA] or {}).get("state") or "unknown")
        for row in rows
    )
    stage_counts = Counter(str(row.get("decision_stage") or "unknown") for row in rows)
    observation_context_eligible = sum(
        (row[TACTICAL_EVIDENCE_SCHEMA].get("source_quality") or {}).get("status")
        == "pass"
        and row[TACTICAL_EVIDENCE_SCHEMA].get("state")
        not in {"not_applicable", "source_unavailable"}
        and row.get("primary_parent_wave_stage_row") is True
        for row in rows
    )
    replay_context_eligible = sum(
        row["three_arm_manifest"].get("replay_context_eligible") is True
        and row.get("primary_replay_parent_wave_stage_row") is True
        for row in rows
    )
    economic_eligible = sum(
        row["three_arm_manifest"].get("net_economic_evaluation_eligible") is True
        and row.get("primary_economic_parent_wave_stage_row") is True
        for row in rows
    )
    control_eligible = sum(
        row["three_arm_manifest"].get("control_decision_eligible") is True
        and row.get("primary_control_parent_wave_stage_row") is True
        for row in rows
    )
    paired_eligible = sum(
        row["three_arm_manifest"].get("paired_decision_quality_eligible") is True
        and row.get("primary_paired_parent_wave_stage_row") is True
        for row in rows
    )
    mature_outcome_eligible = sum(
        any(
            horizon.get("mature") is True
            for horizon in (row.get("future_outcome") or {}).get("horizons") or []
        )
        and row.get("primary_mature_outcome_parent_wave_stage_row") is True
        for row in rows
    )
    generated = generated_at or datetime.now().astimezone()
    return {
        "schema": REPORT_SCHEMA,
        "target_date": target_date,
        "generated_at": generated.isoformat(),
        "status": "pass" if replay_context_eligible else "warning",
        "decision": (
            "micro_three_arm_paired_replay_ready"
            if paired_eligible
            else (
                "micro_replay_context_ready_control_response_excluded"
                if replay_context_eligible
                else "micro_context_keep_collecting_or_source_gap"
            )
        ),
        "optimization_direction": {
            "objective": (
                "maximize_after_cost_net_profit_with_fast_frequent_bounded_exposure"
            ),
            "primary_metrics": [
                "source_quality_adjusted_ev_pct",
                "notional_weighted_ev_pct",
                "net_profit",
            ],
            "diagnostic_metrics": [
                "signals_per_hour",
                "net_target_first_rate",
                "time_to_fill_ms",
                "time_to_net_target_ms",
                "position_duration_ms",
            ],
            "constraints": [
                "severe_tail_mae",
                "p95_execution_slippage_bps",
                "p95_liquidation_time_sec",
                "hard_protect_emergency_guard_unchanged",
            ],
        },
        "summary": {
            "trace_payload_join_count": len(rows),
            "micro_observation_context_eligible_primary_episode_count": (
                observation_context_eligible
            ),
            "micro_context_eligible_primary_episode_count": (
                replay_context_eligible
            ),
            "control_decision_eligible_primary_episode_count": control_eligible,
            "paired_decision_quality_eligible_primary_episode_count": (
                paired_eligible
            ),
            "net_economic_eligible_primary_episode_count": economic_eligible,
            "mature_outcome_eligible_primary_episode_count": (
                mature_outcome_eligible
            ),
            "primary_metric_denominator": (
                "eligible_exact_trace_parent_wave_stage_rows"
            ),
            "same_parent_wave_repeat_count": sum(
                row.get("same_parent_wave_repeat") is True for row in rows
            ),
            "state_counts": dict(state_counts),
            "stage_counts": dict(stage_counts),
            "exclusion_counts": dict(exclusions),
            "noncausal_source_diagnostics": {
                "invalid_market_timestamp_row_count": sum(
                    len(scoped_rows)
                    for scoped_rows in invalid_market_by_scope.values()
                ),
                "invalid_depth_timestamp_row_count": sum(
                    len(scoped_rows)
                    for scoped_rows in invalid_depth_by_scope.values()
                ),
                "invalid_event_reference_timestamp_row_count": sum(
                    len(scoped_rows)
                    for scoped_rows in invalid_references_by_scope.values()
                ),
                "included_in_prompt_context": False,
            },
        },
        "rows": rows,
        "source_exact_payload_mutated": False,
        "future_outcomes_separate_from_prompt_context": True,
        "default_exact_v2_cohort_unchanged": True,
        "provider_call_performed": False,
        **REPORT_METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    yield payload


def _partition_paths(root: Path, target_date: str, name: str) -> list[Path]:
    partition = root / f"trade_date={target_date}"
    selected: list[Path] = []
    for directory in sorted(partition.glob("venue=*/session=*")):
        base = directory / f"{name}.jsonl"
        selected.extend(readable_partition_path_files(base))
    return selected


def _relevant_windows(
    traces: Sequence[Mapping[str, Any]],
    payloads: Sequence[Mapping[str, Any]],
    *,
    config: BridgeConfig,
) -> dict[tuple[str, str, str], tuple[tuple[int, int], ...]]:
    payload_indexes = _payload_indexes(payloads)
    raw_windows: dict[tuple[str, str, str], list[tuple[int, int]]] = defaultdict(list)
    for trace in traces:
        payload, _ = _resolve_payload_for_trace(trace, indexes=payload_indexes)
        if payload is None:
            continue
        watermark, _ = exact_snapshot_watermark(trace, payload)
        if watermark is None:
            continue
        scope = resolve_micro_scope(trace)
        if scope.status != "resolved":
            continue
        key = (
            normalize_symbol(trace.get("stock_code")),
            scope.venue,
            scope.session_bucket,
        )
        watermark_ms = int(watermark["captured_at_ms"])
        start_ms = watermark_ms - (
            config.active_wave_max_age_sec + config.context_lookback_sec
        ) * 1_000
        end_ms = (
            watermark_ms
            + config.outcome_horizons_sec[-1] * 1_000
            + config.max_outcome_endpoint_lag_ms
        )
        raw_windows[key].append((start_ms, end_ms))
    windows: dict[tuple[str, str, str], tuple[tuple[int, int], ...]] = {}
    for key, values in raw_windows.items():
        merged: list[list[int]] = []
        for start_ms, end_ms in sorted(values):
            if not merged or start_ms > merged[-1][1]:
                merged.append([start_ms, end_ms])
            else:
                merged[-1][1] = max(merged[-1][1], end_ms)
        windows[key] = tuple((start, end) for start, end in merged)
    return windows


def _filter_relevant_rows(
    rows: Iterable[Mapping[str, Any]],
    windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
    *,
    reference_rows: bool = False,
) -> list[Mapping[str, Any]]:
    selected = []
    window_index = {
        key: (tuple(window[0] for window in scope_windows), scope_windows)
        for key, scope_windows in windows.items()
    }
    for row in rows:
        key = (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        )
        indexed_windows = window_index.get(key)
        if indexed_windows is None:
            continue
        starts, scope_windows = indexed_windows
        try:
            timestamp_ms = (
                int(row.get("event_detected_at_ms") or 0)
                if reference_rows
                else _timestamp_ms(row.get("local_receive_timestamp"))
            )
        except (TypeError, ValueError):
            continue
        index = bisect_right(starts, timestamp_ms) - 1
        if index >= 0 and timestamp_ms <= scope_windows[index][1]:
            selected.append(row)
    return selected


def _excluded_scopes(payload: Mapping[str, Any]) -> set[tuple[str, str, str, int]]:
    return {
        (
            str(row.get("trade_date") or ""),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
            int(row.get("sequence_epoch") or 0),
        )
        for row in payload.get("exclusions") or []
        if isinstance(row, Mapping)
    }


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--observation-root",
        type=Path,
        default=DATA_DIR / "observations" / "scalp_micro_reversion_forward",
    )
    parser.add_argument(
        "--source-exclusion-manifest",
        type=Path,
        default=DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    )
    parser.add_argument("--statutory-sell-tax-bps", type=float)
    parser.add_argument("--buy-fee-bps", type=float, default=0.0)
    parser.add_argument("--sell-fee-bps", type=float, default=0.0)
    parser.add_argument("--uncertainty-buffer-bps", type=float, default=3.0)
    parser.add_argument(
        "--cost-profile-source",
        default="operator_supplied_research_assumption",
        help="Research provenance only; CLI values never become promotion grade.",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    target = date.fromisoformat(args.date)
    if target < CLEAN_BASELINE_DATE:
        parser.error("date is before clean tuning baseline")
    trace_path = DATA_DIR / "ai_decision_trace" / f"ai_decision_trace_{args.date}.jsonl"
    payload_path = (
        DATA_DIR / "ai_decision_payloads" / f"ai_decision_payloads_{args.date}.jsonl"
    )
    if not trace_path.exists() or not payload_path.exists():
        parser.error("exact trace or payload artifact is missing")
    exclusion_payload = load_source_exclusion_manifest(args.source_exclusion_manifest)
    config = BridgeConfig(
        statutory_sell_tax_bps=args.statutory_sell_tax_bps,
        buy_fee_bps=args.buy_fee_bps,
        sell_fee_bps=args.sell_fee_bps,
        uncertainty_buffer_bps=args.uncertainty_buffer_bps,
        cost_profile_source=args.cost_profile_source,
        # Verification must come from a reviewed versioned artifact in a
        # programmatic caller.  An operator CLI flag cannot assert it.
        cost_profile_verified=False,
    )
    traces = list(_iter_jsonl((trace_path,)))
    payloads = list(_iter_jsonl((payload_path,)))
    windows = _relevant_windows(traces, payloads, config=config)
    market_paths = _partition_paths(
        args.observation_root, args.date, "market_stream"
    )
    depth_paths = _partition_paths(
        args.observation_root, args.date, "market_depth_stream"
    )
    reference_paths = _partition_paths(
        args.observation_root, args.date, "market_stream_event_references"
    )
    market_rows = _filter_relevant_rows(_iter_jsonl(market_paths), windows)
    depth_rows = _filter_relevant_rows(_iter_jsonl(depth_paths), windows)
    reference_rows = _filter_relevant_rows(
        _iter_jsonl(reference_paths), windows, reference_rows=True
    )
    report = build_bridge_report(
        target_date=args.date,
        traces=traces,
        payloads=payloads,
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=reference_rows,
        config=config,
        excluded_scopes=_excluded_scopes(exclusion_payload),
    )
    output = (
        DATA_DIR
        / "report"
        / "micro_reversion_ai_quality_bridge"
        / f"micro_reversion_ai_quality_bridge_{args.date}.json"
    )
    if args.write:
        _atomic_write_json(output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "decision": report["decision"],
                "summary": report["summary"],
                "output": str(output) if args.write else None,
                **AUTHORITY_CONTRACT,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
