"""Offline decision-quality control, outcome maturity, and paired replay.

This module consumes redacted exact payloads and future market observations.
It never sends an order and never mutates runtime prompts, models, providers,
thresholds, prices, quantities, broker guards, safety guards, or bot state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION,
    DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION,
    DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION,
    DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION,
    DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
    DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
    DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
    DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
    DECISION_QUALITY_V2_PROMPT_VERSION,
    DECISION_QUALITY_V2_RESPONSE_SCHEMA,
    DECISION_QUALITY_V2_REASON_CODES,
    decision_quality_holding_v2_3_system_prompt,
    decision_quality_v2_detailed_system_prompt,
    decision_quality_v2_8_detailed_system_prompt,
    decision_quality_v2_9_anticipatory_system_prompt,
    decision_quality_v2_9_1_anticipatory_system_prompt,
    decision_quality_v2_10_bounded_opportunity_system_prompt,
    decision_quality_v2_11_clean_continuation_system_prompt,
    decision_quality_v2_12_selective_recovery_system_prompt,
    decision_quality_v2_13_recovery_confirmation_system_prompt,
    decision_quality_v2_14_setup_risk_adjudicator_system_prompt,
    decision_quality_v2_15_bounded_recovery_system_prompt,
    decision_quality_v2_16_sequential_recovery_system_prompt,
    decision_quality_v2_system_prompt,
)
from src.engine.scalping.ai_decision_trace import replay_source_input
from src.engine.scalping.entry_candidate_lifecycle_state import (
    component_is_complete as candidate_lifecycle_component_is_complete,
    event_path as candidate_lifecycle_event_path,
    load_candidate_state_index,
    materialize_candidate_states,
    report_path as candidate_lifecycle_report_path,
)
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_DECISION_COMPOSER_VERSION,
    ENTRY_DECISION_COMPOSER_V2_15_VERSION,
    ENTRY_DECISION_COMPOSER_V2_16_VERSION,
    ENTRY_RISK_ADJUDICATION_SCHEMA,
    ENTRY_RISK_ADJUDICATION_REPAIR_VERSION,
    ENTRY_SETUP_EVIDENCE_SCHEMA,
    ENTRY_SETUP_EVIDENCE_VERSION,
    STRUCTURE_PHASE_POLICY_VERSION,
    TAIL_RISK_OBSERVATION_CONTRACT,
    build_entry_setup_evidence,
    compose_entry_decision,
    entry_risk_adjudication_openai_schema,
    repair_invalid_entry_risk_adjudication,
    validate_entry_risk_adjudication,
)
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

KST = ZoneInfo("Asia/Seoul")
CONTROL_SCHEMA = "ai_decision_quality_control_v1"
LABEL_REPORT_SCHEMA = "ai_decision_outcome_labels_v1"
BASELINE_SCHEMA = "ai_decision_quality_baseline_v1"
PAIRED_SCHEMA = "ai_prompt_paired_replay_v1"
DAILY_MATERIALIZATION_SCHEMA = "ai_decision_quality_daily_materialization_v1"
DETAILED_PAIRED_SCHEMA = "ai_prompt_detailed_paired_replay_v1"
EXACT_PAYLOAD_ANALYSIS_SCHEMA = "exact_payload_analysis_v1"
ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA = "anticipatory_reversal_analysis_v1"
SCORE_CORRELATION_SCHEMA = "ai_score_outcome_correlation_v1"
RECOVERY_TRIGGER_SCHEMA = "ai_prompt_recovery_trigger_labels_v1"
REVERSAL_SEQUENCE_SCHEMA = "ai_entry_reversal_sequence_replay_v1"
REVERSAL_SEQUENCE_CONTEXT_SCHEMA = "entry_reversal_sequence_context_v1"
PAIRED_OUTCOME_RECOVERY_SCHEMA = "same_trace_paired_outcome_recovery_v1"
INPUT_BUNDLE_VERSION = "scalping_multi_timeframe_context_v1"
ENTRY_CONTEXT_SCHEMA = "entry_candle_context_v1"
HOLDING_CONTEXT_SCHEMA = "holding_decision_context_v1"
HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)
HORIZON_END_MAX_LAG_SEC = 90
PROFIT_OPPORTUNITY_THRESHOLD_PCT = 1.0
ENTRY_PATH_TARGET_PCT = 0.30
ENTRY_PATH_ADVERSE_PCT = -0.70
ENTRY_PATH_PRIMARY_HORIZON = "10m"
ENTRY_PATH_LABEL_VERSION = "tight_stop_entry_path_v1"
PROBE_RISK_CONTRACT_VERSION = "bounded_probe_recovery_risk_v1"
OFFLINE_PROBE_SHARE_COUNT = 1
OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT = 2.0
OFFLINE_PROBE_SEVERE_TAIL_ADVERSE_PCT = -2.0
RISING_MISSED_POST_BLOCK_MIN_FRESH_SAMPLES = 2
RISING_MISSED_POST_BLOCK_LABEL_VERSION = "rising_missed_post_block_exact_trace_v1"
PIPELINE_FORWARD_DAYS = 7
PRIMARY_HORIZON_BY_STAGE = {
    "entry": "10m",
    "entry_price": "10m",
    "post_probe": "10m",
    "scale_in": "20m",
    "holding": "30m",
    "exit": "30m",
    "overnight": "60m",
}

TRACE_DIR = DATA_DIR / "ai_decision_trace"
PAYLOAD_DIR = DATA_DIR / "ai_decision_payloads"
OUTCOME_DIR = DATA_DIR / "ai_decision_outcomes"
PIPELINE_DIR = DATA_DIR / "pipeline_events"
RUNTIME_DIR = DATA_DIR / "runtime"
LABEL_REPORT_DIR = DATA_DIR / "report" / "ai_decision_outcome_labels"
BASELINE_REPORT_DIR = DATA_DIR / "report" / "ai_decision_quality_baseline"
PAIRED_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_paired_replay"
DETAILED_PAIRED_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_detailed_paired_replay"
SCORE_CORRELATION_REPORT_DIR = DATA_DIR / "report" / "ai_score_outcome_correlation"
RECOVERY_TRIGGER_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_recovery_trigger"
REVERSAL_SEQUENCE_REPORT_DIR = DATA_DIR / "report" / "ai_entry_reversal_sequence_replay"
PYRAMID_FEEDBACK_REPORT_DIR = DATA_DIR / "report" / "scalping_pyramid_intraday_feedback"
SCALE_IN_COUNTERFACTUAL_REPORT_DIR = (
    DATA_DIR / "report" / "scale_in_incremental_counterfactual"
)
ENTRY_SPLIT_ORDER_PLAN_REPORT_DIR = DATA_DIR / "report" / "entry_split_order_plan"
PAIRED_REPLAY_MIN_ROWS = 30
PAIRED_REPLAY_MIN_SYMBOLS = 10
PAIRED_LEARNING_MIN_ROWS = 1
PAIRED_LEARNING_MIN_SYMBOLS = 1
PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS = 10
PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS = 3
PAIRED_CANDIDATE_MAX_LOSS_BREACH_RATE_PCT = 20.0
PAIRED_CANDIDATE_MAX_SEVERE_TAIL_RATE_PCT = 20.0
PAIRED_CANDIDATE_CATASTROPHIC_LOSS_PCT = -5.0
ENTRY_RECHECK_MAX_WAIT_SEC = 300
CANDIDATE_EXECUTION_SELECTION_POLICY = (
    "deterministic_outcome_blind_setup_state_symbol_round_robin_v3"
)
ANTICIPATORY_LEARNING_MIN_ROWS = 1
ANTICIPATORY_LEARNING_MIN_SYMBOLS = 1
CANDIDATE_SCHEMA_MAX_ATTEMPTS = 4
HOLDING_SEMANTIC_VALIDATOR_VERSION = "holding_exact_semantic_gate_v1"
HOLDING_FLOW_BOUNDED_DEFER_SEMANTIC_VALIDATOR_VERSION = (
    "holding_flow_bounded_defer_semantic_v1"
)
ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION = "entry_price_cost_aware_downside_semantic_v5"
ENTRY_PRICE_MAX_INCREMENTAL_CHASE_COST_BP = 25.0
ENTRY_PRICE_MIN_REWARD_RISK_FOR_AGGRESSIVE_BASIS = 1.0
ANTICIPATORY_SEMANTIC_VALIDATOR_VERSION = "anticipatory_reversal_offline_semantic_v1"
BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION = (
    "bounded_opportunity_offline_semantic_v1"
)
BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION = "bounded_opportunity_fail_safe_repair_v2"
ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION = "entry_setup_risk_offline_semantic_v7"
ANTICIPATORY_SEMANTIC_REPAIR_VERSION = (
    "anticipatory_reversal_contract_closure_repair_v1"
)
RECOVERY_TRIGGER_MIN_ROWS = 15
RECOVERY_TRIGGER_MIN_SYMBOLS = 10
RECOVERY_TRIGGER_WINDOW_MIN = 5
RECOVERY_OUTCOME_HORIZONS_MIN = (1, 3, 5, 10)
REVERSAL_SEQUENCE_HORIZONS_MIN = (5, 10, 20, 30, 60)
REVERSAL_SEQUENCE_MAX_PREVIOUS_SEC = 300
REVERSAL_SEQUENCE_EPISODE_GAP_SEC = 300
REVERSAL_SEQUENCE_REFERENCE_NEAR_BP = 150.0
REVERSAL_SEQUENCE_MA_NEAR_BP = 100.0
REVERSAL_SEQUENCE_MAX_PRICE_DECLINE_PCT = -0.35

OFFLINE_CONTRACT = {
    "metric_role": "ai_decision_quality_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "exact_snapshot_stage_venue_session_mature_forward_window",
    "sample_floor": "eligible_exact_rows_with_mature_outcomes",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_prompt_promotion_without_separate_review",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}

DECISION_QUALITY_OBJECTIVE = {
    "objective": (
        "maximize_cumulative_net_profit_by_exploring_more_positive_edge_"
        "opportunities_with_tolerable_risk_and_downstream_protection"
    ),
    "not_objective": "maximize_drop_wait_or_eliminate_all_risk",
    "exploration_unit": "one_share_probe_intent_before_existing_submit_guards",
    "downstream_protection": [
        "fresh_quote_and_stale_conflict_guard",
        "broker_account_order_quantity_cooldown_guards",
        "post_probe_direction_and_price_resolver",
        "holding_exit_and_hard_safety_guards",
    ],
    "success_metrics": [
        "missed_upside_reduction",
        "positive_cost_adjusted_probe_ev_pct",
        "bounded_probe_loss_and_severe_tail_not_increased",
        "drawdown_recovery_capture_not_decreased",
        "positive_source_quality_adjusted_exposure_ev_pct",
        "notional_fill_joined_net_profit_improvement",
    ],
    "artifact_generation_is_performance": False,
}

RECOVERY_TRIGGER_CONTRACT = {
    "metric_role": "ai_decision_quality_recovery_observation",
    "decision_authority": "offline_counterfactual_recovery_attribution_only",
    "window_policy": (
        "exact_snapshot_same_venue_session_completed_bar_recovery_then_forward"
    ),
    "sample_floor": {
        "decision_rows": RECOVERY_TRIGGER_MIN_ROWS,
        "unique_symbols": RECOVERY_TRIGGER_MIN_SYMBOLS,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": ("exact_payload_fresh_same_route_completed_recovery_window"),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_prompt_promotion",
        "synthetic_order_or_fill_claim",
        "counterfactual_realized_pnl_merge",
        "provider_model_threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "bot_restart",
    ],
}

REVERSAL_SEQUENCE_CONTRACT = {
    "metric_role": "ai_entry_reversal_sequence_quality_observation",
    "decision_authority": "offline_sequence_replay_only_no_runtime_change",
    "window_policy": (
        "previous_and_current_exact_snapshot_same_symbol_venue_session_then_"
        "mature_5_10_20_30_60m_outcome"
    ),
    "sample_floor": (
        "one_first_signal_episode_starts_observation_three_symbols_required_for_"
        "prompt_candidate_review"
    ),
    "primary_decision_metric": (
        "20m_first_signal_episode_source_quality_adjusted_ev_pct"
    ),
    "source_quality_gate": (
        "exact_payload_hash_match_fresh_same_route_mature_horizon_no_future_feature"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "future_outcome_as_entry_feature",
        "standalone_live_buy_wait_or_drop_authority",
        "prompt_or_model_runtime_promotion",
        "provider_threshold_price_quantity_or_cap_change",
        "wide_spread_or_stale_quote_safety_bypass",
        "broker_or_hard_safety_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}

STAGE_ALIASES = {
    "analyze_target": "entry",
    "gatekeeper": "entry",
    "entry": "entry",
    "entry_price": "entry_price",
    "post_probe": "post_probe",
    "scale_in": "scale_in",
    "holding_score": "holding",
    "holding_flow": "holding",
    "holding": "holding",
    "exit": "exit",
    "overnight": "overnight",
}
ENDPOINT_ALIASES = {
    # Historical fail-closed holding rows were recorded with the prompt type
    # before the provider transport could attach the logical endpoint.
    "scalping_holding_score": "holding_score",
}

REASON_EVIDENCE_KEYS = (
    "trend",
    "liquidity",
    "tape",
    "risk",
    "uncertainty",
    "setup",
    "positive_edge",
    "adverse_risk",
    "trigger",
)
STAGE_ACTIONS = {
    "entry": {"BUY", "WAIT", "DROP"},
    "entry_price": {"USE_DEFENSIVE", "USE_REFERENCE", "IMPROVE_LIMIT", "SKIP"},
    "post_probe": {"CONTINUE", "STOP"},
    "scale_in": {"ADD", "NO_ADD"},
    "holding": {"HOLD", "TRIM", "EXIT"},
    "exit": {"HOLD", "TRIM", "EXIT"},
    "overnight": {"HOLD_OVERNIGHT", "EXIT_BEFORE_CLOSE"},
}
EXPOSURE_ACTIONS = {
    "BUY",
    "ADD",
    "CONTINUE",
    "HOLD",
    "HOLD_OVERNIGHT",
    "USE_DEFENSIVE",
    "USE_REFERENCE",
    "IMPROVE_LIMIT",
}
NO_EXPOSURE_ACTIONS = {
    "DROP",
    "WAIT",
    "NO_ADD",
    "STOP",
    "EXIT",
    "SELL",
    "SELL_TODAY",
    "EXIT_BEFORE_CLOSE",
    "SKIP",
}
REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
EVIDENCE_VALUES = {
    "trend": {"supportive", "mixed", "adverse", "insufficient"},
    "liquidity": {"supportive", "mixed", "adverse", "insufficient"},
    "tape": {"supportive", "mixed", "adverse", "insufficient"},
    "risk": {"low", "medium", "high", "insufficient"},
    "uncertainty": {"low", "medium", "high"},
    "setup": {
        "continuation",
        "pullback_recovery",
        "reversal",
        "no_setup",
        "not_applicable",
        "insufficient",
    },
    "positive_edge": {"strong", "moderate", "weak", "none", "insufficient"},
    "adverse_risk": {"low", "moderate", "high", "blocking", "insufficient"},
    "trigger": {
        "confirmed",
        "recovery_required",
        "failed",
        "not_applicable",
        "insufficient",
    },
}
MUTUALLY_EXCLUSIVE_REASON_CODE_GROUPS = (
    {"edge_positive", "edge_absent", "no_positive_edge"},
    {"risk_reward_favorable", "risk_reward_unfavorable"},
    {"trend_supportive", "trend_adverse"},
    {"liquidity_supportive", "liquidity_adverse"},
    {"tape_supportive", "tape_adverse"},
    {
        "recovery_trigger_confirmed",
        "recovery_trigger_required",
        "recovery_trigger_failed",
    },
)


def resolve_candidate_reason_code_conflicts(
    response: dict[str, Any],
) -> tuple[list[str], bool]:
    """Resolve duplicate semantic labels without changing the model action.

    The model occasionally emits two labels from the same mutually-exclusive
    family even though its structured evidence is internally consistent.  This
    helper keeps the label aligned with that evidence.  A conflict without one
    evidence-supported label remains unresolved so the caller can fail closed.
    It must not be used to repair BUY results.
    """

    codes = response.get("reason_codes")
    if not isinstance(codes, list):
        return [], False
    normalized = [str(code) for code in codes]
    if str(response.get("action") or "").strip().upper() == "BUY":
        return normalized, False
    evidence = response.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    edge_state = str(response.get("edge_state") or "").strip().upper()
    positive_edge = str(evidence.get("positive_edge") or "").strip().lower()
    trigger = str(evidence.get("trigger") or "").strip().lower()
    directional_preference = {
        "supportive": "supportive",
        "adverse": "adverse",
        # A mixed or insufficient evidence axis supports neither directional
        # label.  Non-BUY normalization may remove both labels while retaining
        # the model's original list in decision-quality provenance.
        "mixed": "remove_all",
        "insufficient": "remove_all",
    }

    def _directional_reason_preference(axis: str) -> str | None:
        direction = directional_preference.get(
            str(evidence.get(axis) or "").strip().lower()
        )
        if direction == "remove_all":
            return direction
        if direction in {"supportive", "adverse"}:
            return f"{axis}_{direction}"
        return None

    edge_preferred = None
    if edge_state == "EDGE" and positive_edge in {"moderate", "strong"}:
        edge_preferred = "edge_positive"
    elif edge_state == "NO_EDGE" and positive_edge == "none":
        edge_preferred = "no_positive_edge"
    elif edge_state == "NO_EDGE" and positive_edge == "weak":
        edge_preferred = "edge_absent"
    preferred_by_group = {
        frozenset({"edge_positive", "edge_absent", "no_positive_edge"}): edge_preferred,
        frozenset({"risk_reward_favorable", "risk_reward_unfavorable"}): None,
        frozenset({"trend_supportive", "trend_adverse"}): (
            _directional_reason_preference("trend")
        ),
        frozenset({"liquidity_supportive", "liquidity_adverse"}): (
            _directional_reason_preference("liquidity")
        ),
        frozenset({"tape_supportive", "tape_adverse"}): (
            _directional_reason_preference("tape")
        ),
        frozenset(
            {
                "recovery_trigger_confirmed",
                "recovery_trigger_required",
                "recovery_trigger_failed",
            }
        ): {
            "confirmed": "recovery_trigger_confirmed",
            "recovery_required": "recovery_trigger_required",
            "failed": "recovery_trigger_failed",
        }.get(
            trigger
        ),
    }
    try:
        upside = float(response.get("expected_upside_pct"))
        downside = float(response.get("expected_downside_pct"))
    except (TypeError, ValueError):
        upside = None
        downside = None
    if upside is not None and downside is not None and downside < 0:
        preferred_by_group[
            frozenset({"risk_reward_favorable", "risk_reward_unfavorable"})
        ] = (
            "risk_reward_favorable"
            if upside / abs(downside) >= 1.25
            else "risk_reward_unfavorable"
        )

    resolved = list(normalized)
    changed = False
    for group in MUTUALLY_EXCLUSIVE_REASON_CODE_GROUPS:
        indexes = [index for index, code in enumerate(resolved) if code in group]
        if len(indexes) <= 1:
            continue
        preferred = preferred_by_group.get(frozenset(group))
        candidates = {resolved[index] for index in indexes}
        if preferred is None:
            continue
        if preferred == "remove_all":
            resolved = [code for code in resolved if code not in group]
            changed = True
            continue
        if preferred not in candidates:
            continue
        keep = preferred
        kept = False
        next_codes: list[str] = []
        for code in resolved:
            if code not in group:
                next_codes.append(code)
            elif code == keep and not kept:
                next_codes.append(code)
                kept = True
        resolved = next_codes
        changed = True
    return resolved, changed


def _cohort_artifact_suffix(
    *,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> str:
    parts: list[str] = []
    for label, value in (
        ("venue", effective_venue),
        ("session", session_bucket),
    ):
        normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
        normalized = normalized.strip("_")
        if normalized:
            parts.extend((label, normalized))
    return f"_{'_'.join(parts)}" if parts else ""


def control_path(
    target_date: str,
    *,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> Path:
    suffix = _cohort_artifact_suffix(
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    return RUNTIME_DIR / f"ai_decision_quality_control_{target_date}{suffix}.json"


def label_report_path(target_date: str) -> Path:
    return LABEL_REPORT_DIR / f"ai_decision_outcome_labels_{target_date}.json"


def baseline_path(target_date: str) -> Path:
    return BASELINE_REPORT_DIR / f"ai_decision_quality_baseline_{target_date}.json"


def paired_path(
    target_date: str,
    *,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> Path:
    suffix = _cohort_artifact_suffix(
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    return PAIRED_REPORT_DIR / f"ai_prompt_paired_replay_{target_date}{suffix}.json"


def stage_paired_path(
    target_date: str,
    stage: str,
    *,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> Path:
    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in {"entry", "holding"}:
        raise ValueError(f"unsupported_paired_stage:{normalized_stage or 'missing'}")
    suffix = _cohort_artifact_suffix(
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    return PAIRED_REPORT_DIR / (
        f"ai_prompt_paired_replay_{target_date}_{normalized_stage}{suffix}.json"
    )


def detailed_paired_path(
    target_date: str,
    *,
    candidate_prompt_version: str = DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    candidate_model: str | None = None,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> Path:
    suffix = (
        ""
        if candidate_prompt_version == DECISION_QUALITY_DETAILED_PROMPT_VERSION
        else f"_{candidate_prompt_version}"
    )
    if candidate_model:
        model_slug = re.sub(r"[^a-z0-9._-]+", "_", candidate_model.strip().lower())
        suffix += f"_model_{model_slug}"
    suffix += _cohort_artifact_suffix(
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    return (
        DETAILED_PAIRED_REPORT_DIR
        / f"ai_prompt_detailed_paired_replay_{target_date}{suffix}.json"
    )


def score_correlation_path(target_date: str) -> Path:
    return (
        SCORE_CORRELATION_REPORT_DIR
        / f"ai_score_outcome_correlation_{target_date}.json"
    )


def recovery_trigger_path(target_date: str) -> Path:
    return (
        RECOVERY_TRIGGER_REPORT_DIR / f"ai_prompt_recovery_trigger_{target_date}.json"
    )


def reversal_sequence_path(target_date: str) -> Path:
    return (
        REVERSAL_SEQUENCE_REPORT_DIR
        / f"ai_entry_reversal_sequence_replay_{target_date}.json"
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        value if isinstance(value, bytes) else _canonical_bytes(value)
    ).hexdigest()


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
        Path(tmp_name).replace(path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def _offline_openai_api_keys() -> list[str]:
    """Load configured OpenAI keys without exposing names or values."""

    target_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    return [
        str(value)
        for name, value in sorted(payload.items())
        if str(name).startswith("OPENAI_API_KEY") and value not in (None, "", "-")
    ]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def load_promotion_for_target_date(
    target_date: str,
) -> tuple[dict[str, Any], Path, str]:
    """Resolve the latest promotion marker at or before target_date.

    The caller validates committed/rollback authority. A malformed latest marker
    is intentionally returned as empty and therefore fails closed instead of
    silently falling back to an older promotion.
    """

    exact_path = (
        RUNTIME_DIR / f"ai_multi_timeframe_context_promotion_{target_date}.json"
    )
    candidates: list[tuple[str, Path]] = []
    for path in RUNTIME_DIR.glob("ai_multi_timeframe_context_promotion_*.json"):
        source_date = path.stem.removeprefix("ai_multi_timeframe_context_promotion_")
        try:
            datetime.strptime(source_date, "%Y-%m-%d")
        except ValueError:
            continue
        if source_date <= target_date:
            candidates.append((source_date, path))
    if not candidates:
        return {}, exact_path, ""
    source_date, path = max(candidates, key=lambda item: item[0])
    return _load_json(path), path, source_date


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(_iter_jsonl(path))


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    resolved_path = existing_or_gzip_path(path)
    if not resolved_path.exists():
        return
    with open_text_auto(resolved_path) as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                yield value


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _number(value: Any) -> float | None:
    try:
        parsed = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _probe_path_risk(
    *,
    request: dict[str, Any],
    outcome_mfe_pct: float | None,
    outcome_mae_pct: float | None,
    pre_profit_mae_pct: float | None,
    entry_path_first_hit: str,
    profit_opportunity_sequence: str,
    conservative_execution_cost_pct: float | None,
) -> dict[str, Any]:
    """Separate quote spread from the completed-trade counterfactual path.

    The exact decision reference can be the executable ask while future bars are
    completed trade OHLC.  In a wide market, comparing those values directly can
    label the bid/last-side spread as directional adverse movement.  Keep the raw
    label for audit compatibility, but expose the spread-confounded diagnostic and
    a bounded one-share counterfactual risk contract for offline quality review.
    """

    reference_price = _number(request.get("reference_price"))
    best_bid = _number(request.get("best_bid"))
    best_ask = _number(request.get("best_ask"))
    initial_spread_cost_pct = None
    if (
        best_bid is not None
        and best_ask is not None
        and best_ask > 0
        and 0 < best_bid <= best_ask
    ):
        initial_spread_cost_pct = (best_ask - best_bid) / best_ask * 100.0
    spread_confounded = bool(
        entry_path_first_hit == "adverse_first"
        and initial_spread_cost_pct is not None
        and initial_spread_cost_pct >= abs(ENTRY_PATH_ADVERSE_PCT)
    )

    def directional(value: float | None) -> float | None:
        if value is None:
            return None
        if initial_spread_cost_pct is None:
            return value
        return min(0.0, value + initial_spread_cost_pct)

    execution_cost = conservative_execution_cost_pct or 0.0
    cost_adjusted_mfe = (
        outcome_mfe_pct - execution_cost if outcome_mfe_pct is not None else None
    )
    cost_adjusted_mae = (
        outcome_mae_pct - execution_cost if outcome_mae_pct is not None else None
    )
    worst_loss_pct = (
        min(0.0, cost_adjusted_mae) if cost_adjusted_mae is not None else None
    )
    worst_loss_krw = (
        reference_price * abs(worst_loss_pct) / 100.0
        if (
            reference_price is not None
            and reference_price > 0
            and worst_loss_pct is not None
        )
        else None
    )
    return {
        "probe_risk_contract_version": PROBE_RISK_CONTRACT_VERSION,
        "reference_price_type": request.get("reference_price_type"),
        "reference_price": reference_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "initial_spread_cost_pct": initial_spread_cost_pct,
        "entry_path_adverse_first_spread_confounded": spread_confounded,
        "directional_mae_estimate_ex_initial_spread_pct": directional(outcome_mae_pct),
        "directional_pre_profit_mae_estimate_ex_initial_spread_pct": directional(
            pre_profit_mae_pct
        ),
        "probe_cost_adjusted_mfe_pct": cost_adjusted_mfe,
        "probe_cost_adjusted_mae_pct": cost_adjusted_mae,
        "probe_worst_loss_pct": worst_loss_pct,
        "probe_worst_loss_krw_per_share": worst_loss_krw,
        "probe_loss_within_bounded_cap": (
            worst_loss_pct is not None
            and worst_loss_pct >= -OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT
        ),
        "probe_severe_tail_adverse": (
            worst_loss_pct is not None
            and worst_loss_pct < OFFLINE_PROBE_SEVERE_TAIL_ADVERSE_PCT
        ),
        "probe_path_risk_evaluable": worst_loss_pct is not None,
        "drawdown_recovery_observed": (
            profit_opportunity_sequence == "drawdown_then_profit_recovery"
        ),
        "path_basis": ("counterfactual_completed_1m_trade_path_with_conservative_cost"),
    }


def _bounded_probe_risk_budget(
    exposure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate tolerable one-share path risk without demanding zero tail events."""

    losses = [
        _number(row.get("candidate_probe_worst_loss_pct")) for row in exposure_rows
    ]
    evaluable_losses = [value for value in losses if value is not None]
    breach_count = sum(
        value < -OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT for value in evaluable_losses
    )
    severe_tail_count = sum(
        row.get("candidate_probe_severe_tail_exposure") is True for row in exposure_rows
    )
    catastrophic_count = sum(
        value < PAIRED_CANDIDATE_CATASTROPHIC_LOSS_PCT for value in evaluable_losses
    )
    exposure_count = len(exposure_rows)
    breach_rate_pct = breach_count / exposure_count * 100.0 if exposure_count else None
    severe_tail_rate_pct = (
        severe_tail_count / exposure_count * 100.0 if exposure_count else None
    )
    pass_budget = bool(
        exposure_count
        and len(evaluable_losses) == exposure_count
        and catastrophic_count == 0
        and breach_rate_pct is not None
        and breach_rate_pct <= PAIRED_CANDIDATE_MAX_LOSS_BREACH_RATE_PCT
        and severe_tail_rate_pct is not None
        and severe_tail_rate_pct <= PAIRED_CANDIDATE_MAX_SEVERE_TAIL_RATE_PCT
    )
    return {
        "evaluable_count": len(evaluable_losses),
        "missing_count": exposure_count - len(evaluable_losses),
        "loss_budget_breach_count": breach_count,
        "loss_budget_breach_rate_pct": breach_rate_pct,
        "maximum_loss_budget_breach_rate_pct": (
            PAIRED_CANDIDATE_MAX_LOSS_BREACH_RATE_PCT
        ),
        "severe_tail_count": severe_tail_count,
        "severe_tail_rate_pct": severe_tail_rate_pct,
        "maximum_severe_tail_rate_pct": PAIRED_CANDIDATE_MAX_SEVERE_TAIL_RATE_PCT,
        "catastrophic_loss_threshold_pct": (PAIRED_CANDIDATE_CATASTROPHIC_LOSS_PCT),
        "catastrophic_loss_count": catastrophic_count,
        "pass": pass_budget,
        "risk_interpretation": (
            "completed_bar_mae_is_unprotected_path_stress; any runtime canary "
            "must retain one-share probe-first and existing downstream guards"
        ),
    }


def _opportunity_capture_tradeoff(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure added opportunity against forgone positive exposure by value.

    The candidate is allowed to take more bounded one-share risk.  Promotion is
    therefore based on the cost-adjusted incremental exposure value and the net
    missed-upside tradeoff, rather than demanding that it introduce zero new
    misses compared with the control.
    """

    incremental_rows = [
        row
        for row in rows
        if row.get("candidate_exposure_selected") is True
        and row.get("control_exposure_selected") is not True
    ]
    forgone_rows = [
        row
        for row in rows
        if row.get("control_exposure_selected") is True
        and row.get("candidate_exposure_selected") is not True
    ]
    incremental_values = [
        value
        for row in incremental_rows
        if (value := _number(row.get("candidate_primary_decision_value_pct")))
        is not None
    ]
    forgone_values = [
        value
        for row in forgone_rows
        if (value := _number(row.get("control_primary_decision_value_pct"))) is not None
    ]
    missed_upside_reduction_count = sum(
        row.get("control_missed_upside") is True
        and row.get("candidate_missed_upside") is not True
        for row in rows
    )
    new_missed_upside_count = sum(
        row.get("control_missed_upside") is not True
        and row.get("candidate_missed_upside") is True
        for row in rows
    )
    recovered_missed_upside_values = [
        value
        for row in rows
        if row.get("control_missed_upside") is True
        and row.get("candidate_missed_upside") is not True
        and (value := _number(row.get("candidate_primary_decision_value_pct")))
        is not None
        and value > 0
    ]
    introduced_missed_upside_values = [
        value
        for row in rows
        if row.get("control_missed_upside") is not True
        and row.get("candidate_missed_upside") is True
        and (value := _number(row.get("control_primary_decision_value_pct")))
        is not None
        and value > 0
    ]
    incremental_ev = fmean(incremental_values) if incremental_values else None
    forgone_ev = fmean(forgone_values) if forgone_values else None
    net_missed_upside_count = missed_upside_reduction_count - new_missed_upside_count
    recovered_missed_upside_value_pct = sum(recovered_missed_upside_values)
    introduced_missed_upside_value_pct = sum(introduced_missed_upside_values)
    net_missed_upside_value_pct = (
        recovered_missed_upside_value_pct - introduced_missed_upside_value_pct
    )
    return {
        "incremental_candidate_exposure_count": len(incremental_rows),
        "incremental_candidate_exposure_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in incremental_rows
                if row.get("stock_code")
            }
        ),
        "incremental_candidate_exposure_cost_adjusted_ev_pct": incremental_ev,
        "forgone_control_exposure_count": len(forgone_rows),
        "forgone_control_exposure_ev_pct": forgone_ev,
        "missed_upside_reduction_count": missed_upside_reduction_count,
        "new_missed_upside_count": new_missed_upside_count,
        "net_missed_upside_reduction_count": net_missed_upside_count,
        "recovered_missed_upside_value_pct": recovered_missed_upside_value_pct,
        "introduced_missed_upside_value_pct": introduced_missed_upside_value_pct,
        "net_missed_upside_value_pct": net_missed_upside_value_pct,
        "opportunity_capture_expanded": bool(
            net_missed_upside_value_pct > 0
            or (incremental_rows and incremental_ev is not None and incremental_ev > 0)
        ),
        "missed_upside_tradeoff_not_worse": net_missed_upside_value_pct >= 0,
        "decision_rule": (
            "positive_cost_adjusted_incremental_exposure_or_positive_net_"
            "missed_upside_value; count_is_diagnostic_only"
        ),
    }


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_stock_code(value: Any) -> str:
    raw = str(value or "").strip().upper()
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            raw = raw[:-3]
    if raw.startswith("A"):
        raw = raw[1:]
    digits = "".join(char for char in raw if char.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _extract_holding_context_from_exact_payload(value: Any) -> dict[str, Any]:
    """Extract only the canonical holding JSON embedded in an exact text prompt."""

    if isinstance(value, dict):
        holding = value.get("holding_decision_context")
        return dict(holding) if isinstance(holding, dict) else {}
    if not isinstance(value, str):
        return {}
    marker = "[HOLDING_DECISION_CONTEXT]"
    marker_index = value.find(marker)
    if marker_index < 0:
        return {}
    decoder = json.JSONDecoder()
    marked_json = value[marker_index + len(marker) :].lstrip()
    try:
        parsed, _end = decoder.raw_decode(marked_json)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _payload_contract(payload: dict[str, Any]) -> dict[str, Any]:
    schemas: set[str] = set()
    bundles: set[str] = set()
    canonical_contexts: list[dict[str, Any]] = []
    sanitized_input = replay_source_input(payload)
    roots = [sanitized_input]
    marked_holding = (
        _extract_holding_context_from_exact_payload(sanitized_input)
        if isinstance(sanitized_input, str)
        else {}
    )
    if marked_holding:
        roots.append(marked_holding)
    for root in roots:
        for item in _walk(root):
            if not isinstance(item, dict):
                continue
            schema = str(item.get("schema") or "")
            if schema not in {ENTRY_CONTEXT_SCHEMA, HOLDING_CONTEXT_SCHEMA}:
                continue
            schemas.add(schema)
            candle = item.get("candle") if schema == HOLDING_CONTEXT_SCHEMA else item
            candle = candle if isinstance(candle, dict) else {}
            bars = candle.get("bars") if isinstance(candle.get("bars"), list) else None
            candle_bundle = str(candle.get("input_bundle_version") or "")
            if candle_bundle:
                bundles.add(candle_bundle)
            forming_key = (
                "is_forming" if schema == HOLDING_CONTEXT_SCHEMA else "forming"
            )
            source_quality = (
                item.get("source_quality")
                if schema == HOLDING_CONTEXT_SCHEMA
                and isinstance(item.get("source_quality"), dict)
                else (
                    candle.get("source_quality")
                    if isinstance(candle.get("source_quality"), dict)
                    else {}
                )
            )
            decision_window = (
                source_quality.get("decision_window")
                if isinstance(source_quality.get("decision_window"), dict)
                else {}
            )
            route_equivalence_proof = (
                source_quality.get("route_equivalence_proof")
                if isinstance(source_quality.get("route_equivalence_proof"), dict)
                else {}
            )
            canonical_contexts.append(
                {
                    "schema": schema,
                    "venue": str(item.get("venue") or "") or None,
                    "session": str(item.get("session") or "") or None,
                    "input_bundle_version": str(
                        candle.get("input_bundle_version") or ""
                    )
                    or None,
                    "raw_bar_count": len(bars) if bars is not None else None,
                    "completed_bar_count": sum(
                        1
                        for bar in (bars or [])
                        if isinstance(bar, dict)
                        and not bool(bar.get(forming_key, False))
                    ),
                    "forming_bar_present": any(
                        isinstance(bar, dict) and bool(bar.get(forming_key, False))
                        for bar in (bars or [])
                    ),
                    "decision_window_status": (
                        str(decision_window.get("status") or "") or None
                    ),
                    "decision_window_provider_call_allowed": decision_window.get(
                        "provider_call_allowed"
                    ),
                    "decision_window_missing_bar_count": decision_window.get(
                        "missing_bar_count"
                    ),
                    "decision_window_max_consecutive_missing_bar_count": (
                        decision_window.get("max_consecutive_missing_bar_count")
                    ),
                    "decision_window_sparse_observed_minutes": decision_window.get(
                        "sparse_observed_minutes"
                    ),
                    "decision_window_minute_bar_policy": decision_window.get(
                        "minute_bar_policy"
                    ),
                    "source_quality_status": (
                        str(source_quality.get("status") or "") or None
                    ),
                    "route_equivalence_proven": route_equivalence_proof.get("proven"),
                }
            )
        for item in _walk(root):
            if not isinstance(item, dict):
                continue
            bundle = str(item.get("input_bundle_version") or "")
            if bundle:
                bundles.add(bundle)
    return {
        "context_schemas": sorted(schemas),
        "input_bundle_versions": sorted(bundles),
        "canonical_contexts": canonical_contexts,
    }


def _payload_indexes(
    payloads: list[dict[str, Any]],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    counts = Counter(
        str(row.get("payload_sha256")) for row in payloads if row.get("payload_sha256")
    )
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in payloads:
        endpoint = str(row.get("endpoint") or "")
        payload_sha256 = str(row.get("payload_sha256") or "")
        request_envelope_sha256 = str(row.get("request_envelope_sha256") or "")
        if payload_sha256:
            by_key[(payload_sha256, endpoint)] = row
        if request_envelope_sha256:
            by_key[(f"request:{request_envelope_sha256}", endpoint)] = row
    by_unique_hash = {
        str(row.get("payload_sha256")): row
        for row in payloads
        if row.get("payload_sha256") and counts[str(row.get("payload_sha256"))] == 1
    }
    return by_key, by_unique_hash


def _payload_for_trace(
    trace: dict[str, Any],
    *,
    payload_by_key: dict[tuple[str, str], dict[str, Any]],
    payload_by_unique_hash: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Resolve the exact payload row, preferring the full request envelope.

    A provider-input hash can legitimately repeat while prompt settings or the
    separately retained exact replay context differ.  The request envelope
    binds all of those inputs, so it is authoritative whenever both ledgers
    contain it.  The payload-hash paths retain backward compatibility with
    traces captured before request-envelope storage.
    """

    endpoint = _trace_endpoint(trace)
    request_envelope_sha256 = str(trace.get("request_envelope_sha256") or "")
    payload_sha256 = str(trace.get("payload_sha256") or "")
    if request_envelope_sha256:
        payload = payload_by_key.get((f"request:{request_envelope_sha256}", endpoint))
        if payload is not None:
            if not payload_sha256 or str(payload.get("payload_sha256") or "") == (
                payload_sha256
            ):
                return payload
            return {}
    return payload_by_key.get(
        (payload_sha256, endpoint),
        payload_by_unique_hash.get(payload_sha256, {}),
    )


def _replay_exact_payload(value: Any) -> Any:
    """Return the raw exact payload from either legacy or live V2.7 storage."""

    if not isinstance(value, dict):
        return value
    nested = value.get("exact_payload")
    if isinstance(nested, dict) and (
        "exact_payload_analysis_v1" in value
        or str(value.get("input_schema") or "").startswith("decision_quality_")
    ):
        return nested
    return value


_SUPPLEMENTAL_CACHE_REDACTION_PATHS = frozenset(
    {
        ("exact_payload", "runtime_context", "entry_adm", "cache_token"),
        (
            "exact_payload",
            "runtime_context",
            "entry_adm",
            "entry_adm_bucket_token",
        ),
        (
            "exact_payload",
            "runtime_context",
            "entry_adm",
            "entry_adm_cache_token",
        ),
        (
            "exact_payload",
            "runtime_context",
            "holding_exit_matrix",
            "cache_token",
        ),
        ("exact_payload", "runtime_context", "lifecycle_ai", "cache_token"),
    }
)


def _redacted_value_paths(
    value: Any, path: tuple[str, ...] = ()
) -> set[tuple[str, ...]]:
    if isinstance(value, dict):
        return {
            redacted_path
            for key, child in value.items()
            for redacted_path in _redacted_value_paths(child, (*path, str(key)))
        }
    if isinstance(value, list):
        return {
            redacted_path
            for child in value
            for redacted_path in _redacted_value_paths(child, path)
        }
    return {path} if value == "[REDACTED]" else set()


def _approved_cache_redaction_supplemental(payload: dict[str, Any]) -> bool:
    """Allow decision-semantic replay without claiming byte-exact provenance."""

    if payload.get("redacted") is not True or payload.get("replay_exact") is not False:
        return False
    redacted_paths = _redacted_value_paths(replay_source_input(payload))
    return bool(redacted_paths) and redacted_paths.issubset(
        _SUPPLEMENTAL_CACHE_REDACTION_PATHS
    )


def _stage(value: Any, endpoint: Any = None) -> str:
    for candidate in (value, endpoint):
        normalized = str(candidate or "").strip().lower()
        if normalized in STAGE_ALIASES:
            return STAGE_ALIASES[normalized]
        for key, result in STAGE_ALIASES.items():
            if key in normalized:
                return result
    return "unknown"


def _trace_endpoint(trace: dict[str, Any]) -> str:
    value = str(trace.get("endpoint") or trace.get("decision_stage") or "").strip()
    return ENDPOINT_ALIASES.get(value.lower(), value)


def _exact_trace_payload_findings(
    *,
    trace: dict[str, Any],
    payload: dict[str, Any],
    promoted_at: datetime | None,
) -> list[str]:
    findings: list[str] = []
    decision_ts = _parse_ts(trace.get("decision_ts"))
    if promoted_at is None:
        findings.append("promotion_timestamp_missing")
    elif decision_ts is None or decision_ts < promoted_at:
        findings.append("pre_promotion")
    if trace.get("payload_replay_exact") is not True:
        findings.append("not_exact")
    if trace.get("request_capture_status") != "captured":
        findings.append("request_not_captured")
    if not trace.get("payload_sha256"):
        findings.append("payload_hash_missing")
    if not payload or payload.get("replay_exact") is not True:
        findings.append("payload_store_not_exact")
    if payload.get("replay_context_present") is True and (
        payload.get("replay_context_exact") is not True
        or replay_source_input(payload) is None
    ):
        findings.append("replay_context_not_exact")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        findings.append("provider_none")
    if trace.get("input_preflight_allowed") is not True:
        findings.append("source_quality_not_allowed")
    if trace.get("venue_consistent") is not True:
        findings.append("venue_not_consistent")
    if str(trace.get("input_preflight_mode") or "") != "exact_v2":
        findings.append("input_preflight_not_exact_v2")
    if trace.get("input_blockers"):
        findings.append("source_quality_blockers_present")
    if (
        str(trace.get("sim_record_id") or "").strip()
        or str(trace.get("position_reconciliation_mode") or "") == "simulation_book"
    ):
        findings.append("simulation_observation_not_natural_cohort")
    trace_venue = _venue(trace.get("effective_venue"))
    trace_session = _session(trace.get("session_bucket"))
    contract = _payload_contract(payload)
    context_venues = {
        _venue(context.get("venue"))
        for context in contract["canonical_contexts"]
        if context.get("venue")
    }
    context_sessions = {
        _session(context.get("session"))
        for context in contract["canonical_contexts"]
        if context.get("session")
    }
    payload_venue = _venue(payload.get("effective_venue")) or (
        next(iter(context_venues)) if len(context_venues) == 1 else ""
    )
    payload_session = _session(payload.get("session_bucket")) or (
        next(iter(context_sessions)) if len(context_sessions) == 1 else ""
    )
    if payload and payload_venue != trace_venue:
        findings.append("payload_trace_venue_mismatch")
    if payload and payload_session != trace_session:
        findings.append("payload_trace_session_mismatch")
    expected_schema = (
        ENTRY_CONTEXT_SCHEMA
        if _stage(trace.get("decision_stage"), trace.get("endpoint"))
        in {"entry", "entry_price"}
        else HOLDING_CONTEXT_SCHEMA
    )
    if expected_schema not in contract["context_schemas"]:
        findings.append("context_schema_missing")
    expected_contexts = [
        context
        for context in contract["canonical_contexts"]
        if context["schema"] == expected_schema
    ]
    matching_contexts = [
        context
        for context in expected_contexts
        if _venue(context.get("venue")) == trace_venue
        and _session(context.get("session")) == trace_session
    ]
    if expected_contexts and not matching_contexts:
        findings.append("canonical_context_venue_session_mismatch")
    cohort_contexts = matching_contexts or expected_contexts
    if not cohort_contexts or not any(
        context["input_bundle_version"] == INPUT_BUNDLE_VERSION
        for context in cohort_contexts
    ):
        findings.append("input_bundle_missing")
    contexts_with_raw_bars = [
        context for context in cohort_contexts if context["raw_bar_count"] is not None
    ]
    if not contexts_with_raw_bars:
        findings.append("canonical_bars_missing")
    elif not any(
        context["completed_bar_count"] > 0 for context in contexts_with_raw_bars
    ):
        findings.append("canonical_completed_bars_missing")
    contexts_with_decision_quality = [
        context
        for context in cohort_contexts
        if context.get("decision_window_status") is not None
    ]

    def decision_window_eligible(context: dict[str, Any]) -> bool:
        status = context.get("decision_window_status")
        provider_allowed = context.get("decision_window_provider_call_allowed") is True
        if not provider_allowed:
            return False
        if (
            status == "fresh_consistent"
            and (_number(context.get("decision_window_missing_bar_count")) or 0) == 0
        ):
            return True
        # ka10080 omits minutes with no trades.  Those observed-row gaps are
        # exact input, not reconstructed missing data.  Preserve the sparse
        # quality dimension while allowing the natural call into the baseline;
        # individual unavailable lookback features remain null in the payload.
        return bool(
            status == "sparse_observed_minutes"
            and context.get("decision_window_sparse_observed_minutes") is True
            and context.get("decision_window_minute_bar_policy")
            == "ka10080_observed_rows_no_synthetic_fill"
            and context.get("source_quality_status") == "fresh_consistent"
            and str(context.get("venue") or "").upper() == "NXT"
            and str(context.get("session") or "").lower() == "nxt_aftermarket"
        )

    if contexts_with_decision_quality and not any(
        decision_window_eligible(context) for context in contexts_with_decision_quality
    ):
        findings.append("canonical_decision_window_source_quality_blocked")
    capture_status = str(trace.get("canonical_context_capture_status") or "")
    if capture_status and capture_status != "exact_completed_bars_captured":
        findings.append(f"canonical_context_capture_{capture_status}")
    return findings


def build_control_manifest(
    *,
    target_date: str,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    control_prompt_versions: dict[str, str] | None = None,
    control_signatures: dict[str, dict[str, Any]] | None = None,
    promotion_artifact_path: Path | None = None,
    promotion_source_date: str | None = None,
) -> dict[str, Any]:
    """Freeze actual current prompts/routes on post-promotion exact requests."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    supplemental_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exact_prompt_rows: list[dict[str, Any]] = []
    excluded = Counter()
    selected_prompt_versions = {
        str(endpoint).strip(): str(version).strip()
        for endpoint, version in (control_prompt_versions or {}).items()
        if str(endpoint).strip() and str(version).strip()
    }
    selected_signatures = {
        str(endpoint).strip(): dict(signature)
        for endpoint, signature in (control_signatures or {}).items()
        if str(endpoint).strip() and isinstance(signature, dict)
    }
    for trace in traces:
        endpoint = _trace_endpoint(trace)
        payload = _payload_for_trace(
            trace,
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        exact_findings = _exact_trace_payload_findings(
            trace=trace,
            payload=payload,
            promoted_at=promoted_at,
        )
        if exact_findings:
            if set(exact_findings) == {"not_exact", "payload_store_not_exact"} and (
                _approved_cache_redaction_supplemental(payload)
                and all(
                    str(trace.get(key) or "").strip()
                    for key in ("prompt_version", "prompt_sha256", "model")
                )
            ):
                supplemental_grouped[endpoint].append(trace)
            excluded.update(exact_findings)
            continue
        if not all(
            str(trace.get(key) or "").strip()
            for key in ("prompt_version", "prompt_sha256", "model")
        ):
            excluded["control_signature_incomplete"] += 1
            continue
        exact_prompt_rows.append(trace)
        selected_prompt_version = selected_prompt_versions.get(endpoint)
        if (
            selected_prompt_version
            and str(trace.get("prompt_version") or "") != selected_prompt_version
        ):
            excluded["control_prompt_version_not_selected"] += 1
            continue
        selected_signature = selected_signatures.get(endpoint)
        observed_signature = {
            field: trace.get(field)
            for field in (
                "prompt_version",
                "prompt_sha256",
                "provider_actual",
                "model",
                "request_temperature",
                "request_reasoning_effort",
            )
        }
        observed_signature["response_schema"] = (
            trace.get("schema_name")
            or trace.get("response_schema")
            or "captured_runtime_contract"
        )
        if selected_signature and any(
            observed_signature.get(field) != expected
            for field, expected in selected_signature.items()
        ):
            excluded["control_signature_not_selected"] += 1
            continue
        grouped[
            str(trace.get("endpoint") or trace.get("decision_stage") or "unknown")
        ].append(trace)
    controls: list[dict[str, Any]] = []
    supplemental_controls: list[dict[str, Any]] = []
    conflicts: list[str] = []
    supplemental_conflicts: list[str] = []

    def freeze_signatures(
        source: dict[str, list[dict[str, Any]]],
        *,
        conflict_prefix: str,
        conflict_sink: list[str],
    ) -> list[dict[str, Any]]:
        frozen: list[dict[str, Any]] = []
        for endpoint, rows in sorted(source.items()):
            selected_prompt_version = selected_prompt_versions.get(endpoint)
            if selected_prompt_version:
                rows = [
                    row
                    for row in rows
                    if str(row.get("prompt_version") or "") == selected_prompt_version
                ]
            if not rows:
                continue
            signatures: dict[str, dict[str, Any]] = {}
            for row in rows:
                signature = {
                    "decision_stage": _stage(
                        row.get("decision_stage"), row.get("endpoint")
                    ),
                    "endpoint": endpoint,
                    "prompt_version": row.get("prompt_version"),
                    "prompt_sha256": row.get("prompt_sha256"),
                    "provider_actual": row.get("provider_actual"),
                    "model": row.get("model"),
                    "request_temperature": row.get("request_temperature"),
                    "request_reasoning_effort": row.get("request_reasoning_effort"),
                    "response_schema": row.get("schema_name")
                    or row.get("response_schema")
                    or "captured_runtime_contract",
                }
                signatures[_sha256(signature)] = signature
            if len(signatures) != 1:
                conflict_sink.append(f"{conflict_prefix}:{endpoint}")
                continue
            control = next(iter(signatures.values()))
            control["sample_count"] = len(rows)
            frozen.append(control)
        return frozen

    controls = freeze_signatures(
        grouped,
        conflict_prefix="control_signature_conflict",
        conflict_sink=conflicts,
    )
    supplemental_controls = freeze_signatures(
        supplemental_grouped,
        conflict_prefix="supplemental_control_signature_conflict",
        conflict_sink=supplemental_conflicts,
    )
    required_stages = {"entry", "entry_price", "holding", "overnight"}
    observed_stages = {row["decision_stage"] for row in controls}
    missing_stages = sorted(required_stages - observed_stages)
    promotion_ready = (
        promotion.get("decision") == "promoted_all_market_sessions_full"
        and promotion.get("runtime_activation") is True
        and promotion.get("transaction_status") == "committed"
    )
    status = (
        "control_manifest_frozen_collect_exact_samples"
        if promotion_ready and controls and not conflicts
        else (
            "promotion_failed_no_control_reset"
            if not promotion_ready
            else "control_manifest_gap_fix_required"
        )
    )
    resolved_promotion_path = promotion_artifact_path or (
        RUNTIME_DIR / f"ai_multi_timeframe_context_promotion_{target_date}.json"
    )
    resolved_promotion_date = promotion_source_date or target_date
    prompt_cohort_counts = Counter(
        (
            _trace_endpoint(row),
            str(row.get("prompt_version") or ""),
            str(row.get("prompt_sha256") or ""),
            _venue(row.get("effective_venue")) or "UNKNOWN",
            _session(row.get("session_bucket")) or "UNKNOWN",
        )
        for row in exact_prompt_rows
    )
    prompt_sha_sets: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (
        endpoint,
        prompt_version,
        prompt_sha,
        _venue_name,
        _session_name,
    ) in prompt_cohort_counts:
        prompt_sha_sets[(endpoint, prompt_version)].add(prompt_sha)
    prompt_version_sha_drift = [
        {
            "endpoint": endpoint,
            "prompt_version": prompt_version,
            "prompt_sha256_values": sorted(prompt_shas),
            "required_action": "isolate_by_exact_signature_and_venue_session",
        }
        for (endpoint, prompt_version), prompt_shas in sorted(prompt_sha_sets.items())
        if len(prompt_shas) > 1
    ]
    prompt_signature_cohorts = [
        {
            "endpoint": endpoint,
            "prompt_version": prompt_version,
            "prompt_sha256": prompt_sha,
            "effective_venue": venue,
            "session_bucket": session,
            "sample_count": count,
        }
        for (
            endpoint,
            prompt_version,
            prompt_sha,
            venue,
            session,
        ), count in sorted(prompt_cohort_counts.items())
    ]
    manifest = {
        "schema": CONTROL_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "input_preflight_mode": "exact_v2",
        "entry_context_schema": ENTRY_CONTEXT_SCHEMA,
        "holding_context_schema": HOLDING_CONTEXT_SCHEMA,
        "input_bundle_version": INPUT_BUNDLE_VERSION,
        "promotion_artifact": str(resolved_promotion_path),
        "promotion_source_date": resolved_promotion_date,
        "promotion_rollover": resolved_promotion_date != target_date,
        "promotion_sha256": _sha256(promotion) if promotion else None,
        "selected_control_prompt_versions": selected_prompt_versions,
        "selected_control_signatures": selected_signatures,
        "controls": controls,
        "supplemental_semantic_controls": supplemental_controls,
        "supplemental_semantic_control_authority": (
            "offline_replay_only_non_exact_approved_cache_token_redaction"
        ),
        "supplemental_conflicts": supplemental_conflicts,
        "missing_natural_stages": missing_stages,
        "conflicts": conflicts,
        "excluded_counts": dict(excluded),
        "prompt_model_provider_change_count": len(conflicts),
        "prompt_signature_cohorts": prompt_signature_cohorts,
        "prompt_version_sha_drift": prompt_version_sha_drift,
        "prompt_version_sha_drift_count": len(prompt_version_sha_drift),
        "prompt_signature_selection_status": (
            "selected_exact_signature_with_historical_drift"
            if prompt_version_sha_drift and selected_signatures
            else (
                "cohort_isolation_required"
                if prompt_version_sha_drift
                else "single_sha_per_prompt_version"
            )
        ),
        **OFFLINE_CONTRACT,
    }
    manifest["control_manifest_sha256"] = _sha256(manifest)
    return manifest


def _latest_exact_control_prompt_versions(
    *,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
) -> dict[str, str]:
    """Select the latest exact natural prompt version for each endpoint."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    selected: dict[str, tuple[datetime, int, str]] = {}
    for index, trace in enumerate(traces):
        endpoint = _trace_endpoint(trace)
        prompt_version = str(trace.get("prompt_version") or "").strip()
        payload = _payload_for_trace(
            trace,
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        if (
            not endpoint
            or not prompt_version
            or _exact_trace_payload_findings(
                trace=trace,
                payload=payload,
                promoted_at=promoted_at,
            )
        ):
            continue
        observed_at = _parse_ts(
            trace.get("decision_ts")
            or trace.get("captured_at")
            or trace.get("timestamp")
        ) or datetime.min.replace(tzinfo=KST)
        candidate = (observed_at, index, prompt_version)
        if endpoint not in selected or candidate[:2] > selected[endpoint][:2]:
            selected[endpoint] = candidate
    return {endpoint: value[2] for endpoint, value in sorted(selected.items())}


def _latest_exact_control_signatures(
    *,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Select the latest complete exact runtime signature for each endpoint."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    selected: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
    for index, trace in enumerate(traces):
        endpoint = _trace_endpoint(trace)
        payload = _payload_for_trace(
            trace,
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        signature = {
            "prompt_version": trace.get("prompt_version"),
            "prompt_sha256": trace.get("prompt_sha256"),
            "provider_actual": trace.get("provider_actual"),
            "model": trace.get("model"),
            "request_temperature": trace.get("request_temperature"),
            "request_reasoning_effort": trace.get("request_reasoning_effort"),
            "response_schema": trace.get("schema_name")
            or trace.get("response_schema")
            or "captured_runtime_contract",
        }
        if (
            not endpoint
            or not all(
                str(signature.get(field) or "").strip()
                for field in ("prompt_version", "prompt_sha256", "model")
            )
            or _exact_trace_payload_findings(
                trace=trace,
                payload=payload,
                promoted_at=promoted_at,
            )
        ):
            continue
        observed_at = _parse_ts(
            trace.get("decision_ts")
            or trace.get("captured_at")
            or trace.get("timestamp")
        ) or datetime.min.replace(tzinfo=KST)
        candidate = (observed_at, index, signature)
        if endpoint not in selected or candidate[:2] > selected[endpoint][:2]:
            selected[endpoint] = candidate
    return {endpoint: value[2] for endpoint, value in sorted(selected.items())}


def annotate_primary_cohort_eligibility(
    *,
    labels: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    promotion: dict[str, Any],
) -> list[dict[str, Any]]:
    """Join exact trace/payload evidence before labels enter the primary cohort."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    traces_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        trace_id = str(trace.get("decision_trace_id") or "")
        if trace_id:
            traces_by_id[trace_id].append(trace)
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    annotated: list[dict[str, Any]] = []
    for label in labels:
        trace_id = str(label.get("decision_trace_id") or "")
        trace_rows = traces_by_id.get(trace_id, [])
        findings: list[str] = []
        if len(trace_rows) != 1:
            findings.append(
                "decision_trace_missing"
                if not trace_rows
                else "decision_trace_ambiguous"
            )
            trace: dict[str, Any] = {}
            payload: dict[str, Any] = {}
        else:
            trace = trace_rows[0]
            payload = _payload_for_trace(
                trace,
                payload_by_key=payload_by_key,
                payload_by_unique_hash=payload_by_unique_hash,
            )
            findings.extend(
                _exact_trace_payload_findings(
                    trace=trace,
                    payload=payload,
                    promoted_at=promoted_at,
                )
            )
            if _venue(label.get("effective_venue")) != _venue(
                trace.get("effective_venue")
            ):
                findings.append("label_trace_venue_mismatch")
            if _session(label.get("session_bucket")) != _session(
                trace.get("session_bucket")
            ):
                findings.append("label_trace_session_mismatch")
        annotated.append(
            {
                **label,
                "primary_cohort_eligible": not findings,
                "primary_cohort_exclusion_reasons": sorted(set(findings)),
                "primary_payload_sha256": trace.get("payload_sha256"),
                "primary_context_contract": _payload_contract(payload),
            }
        )
    return annotated


def load_pipeline_price_and_lifecycle_rows(
    rows: Iterable[dict[str, Any]],
    *,
    stock_codes: set[str] | None = None,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    price_buckets: dict[tuple[str, str, str, datetime], dict[str, Any]] = {}
    post_block_meta_by_evaluation: dict[str, dict[str, Any]] = {}
    lifecycle: list[dict[str, Any]] = []
    lifecycle_seen: set[tuple[Any, ...]] = set()
    for row in rows:
        fields = row.get("fields")
        fields = fields if isinstance(fields, dict) else {}
        timestamp = _parse_ts(row.get("emitted_at") or fields.get("event_ts"))
        code = _normalize_stock_code(row.get("stock_code") or fields.get("stock_code"))
        stage = str(row.get("stage") or "")
        if stock_codes is not None and code not in stock_codes:
            continue
        if (
            timestamp is not None
            and window_start is not None
            and timestamp < window_start
        ):
            continue
        if timestamp is not None and window_end is not None and timestamp > window_end:
            continue
        post_block_evaluation_id = str(
            fields.get("rising_missed_tp1_evaluation_id") or ""
        ).strip()
        if post_block_evaluation_id:
            post_block_meta = post_block_meta_by_evaluation.setdefault(
                post_block_evaluation_id,
                {
                    "stock_code": code,
                    "decision_trace_id": None,
                    "registered_at": None,
                    "reference_price": None,
                    "effective_venue": None,
                    "session_bucket": None,
                    "gross_target_pct": None,
                    "adverse_pct": None,
                    "horizon_sec": None,
                    "source_block_stage": None,
                    "source_block_reason": None,
                },
            )
            linked_trace_id = str(
                fields.get("rising_missed_tp1_ai_decision_trace_id") or ""
            ).strip()
            if linked_trace_id in {"", "-"} and stage == "ai_confirmed":
                linked_trace_id = str(fields.get("ai_decision_trace_id") or "").strip()
            if linked_trace_id not in {"", "-"}:
                post_block_meta["decision_trace_id"] = linked_trace_id
            gross_target_pct = _number(fields.get("rising_missed_tp1_gross_target_pct"))
            adverse_pct = _number(fields.get("rising_missed_tp1_adverse_stop_pct"))
            horizon_sec = _number(fields.get("rising_missed_tp1_horizon_sec"))
            if gross_target_pct is not None and gross_target_pct > 0:
                post_block_meta["gross_target_pct"] = gross_target_pct
            if adverse_pct is not None and adverse_pct < 0:
                post_block_meta["adverse_pct"] = adverse_pct
            if horizon_sec is not None and horizon_sec > 0:
                post_block_meta["horizon_sec"] = horizon_sec
            source_block_stage = str(
                fields.get("rising_missed_nxt_post_block_source_block_stage") or ""
            ).strip()
            source_block_reason = str(
                fields.get("rising_missed_nxt_post_block_source_block_reason")
                or fields.get("block_reason")
                or fields.get("rising_missed_tp1_candidate_reason")
                or ""
            ).strip()
            if source_block_stage:
                post_block_meta["source_block_stage"] = source_block_stage
            if source_block_reason:
                post_block_meta["source_block_reason"] = source_block_reason
            if stage in {
                "rising_missed_nxt_post_block_sampler_registered",
                "rising_missed_nxt_post_block_sampler_restored",
            }:
                post_block_meta["registered_at"] = (
                    timestamp.isoformat() if timestamp else None
                )
                post_block_meta["reference_price"] = _number(
                    fields.get("rising_missed_nxt_post_block_sampler_entry_price")
                )
                post_block_meta["effective_venue"] = str(
                    fields.get("rising_missed_effective_venue")
                    or fields.get("effective_venue")
                    or ""
                ).upper()
                post_block_meta["session_bucket"] = str(
                    fields.get("rising_missed_market_session_bucket")
                    or fields.get("session_bucket")
                    or ""
                ).upper()
        price = _pipeline_event_observed_price(fields)
        venue = str(
            fields.get("effective_venue")
            or fields.get("ai_market_snapshot_effective_venue")
            or fields.get("holding_context_venue")
            or fields.get("market_venue")
            or fields.get("rising_missed_effective_venue")
            or ""
        ).upper()
        session = str(
            fields.get("session_bucket")
            or fields.get("ai_market_snapshot_session_bucket")
            or fields.get("holding_context_session")
            or fields.get("market_session_bucket")
            or fields.get("rising_missed_market_session_bucket")
            or ""
        ).upper()
        if timestamp and code and price and venue and session:
            explicit_source_quality = str(
                fields.get("source_quality_status")
                or fields.get("source_quality")
                or "not_recorded"
            )
            source_quality = _pipeline_event_price_source_quality(
                fields,
                explicit_source_quality=explicit_source_quality,
            )
            candidate_price = {
                "timestamp": timestamp.isoformat(),
                "stock_code": code,
                "price": price,
                "effective_venue": venue,
                "session_bucket": session,
                "source_quality": source_quality,
            }
            if (
                stage == "rising_missed_nxt_post_block_price_sample"
                and post_block_evaluation_id
            ):
                candidate_price["_post_block_evaluation_ids"] = [
                    post_block_evaluation_id
                ]
            # Rows without an explicit usable source-quality contract are
            # rejected later by ``_same_route``. Do not retain millions of
            # unusable event observations in memory merely to discard them
            # during maturity calculation.
            if _price_source_usable(candidate_price):
                second = timestamp.replace(microsecond=0)
                key = (code, venue, session, second)
                bucket = price_buckets.get(key)
                if bucket is None:
                    price_buckets[key] = {
                        **candidate_price,
                        "timestamp": second.isoformat(),
                        "high": price,
                        "low": price,
                        "close": price,
                    }
                else:
                    bucket["price"] = price
                    bucket["high"] = max(float(bucket["high"]), price)
                    bucket["low"] = min(float(bucket["low"]), price)
                    bucket["close"] = price
                    for evaluation_id in candidate_price.get(
                        "_post_block_evaluation_ids", []
                    ):
                        evaluation_ids = bucket.setdefault(
                            "_post_block_evaluation_ids", []
                        )
                        if evaluation_id not in evaluation_ids:
                            evaluation_ids.append(evaluation_id)
        lifecycle_identifiers = {
            "decision_trace_id": fields.get("ai_decision_trace_id"),
            "entry_price_decision_trace_id": fields.get(
                "entry_price_ai_decision_trace_id"
            ),
            "record_id": row.get("record_id") or fields.get("record_id"),
            "recommendation_id": fields.get("recommendation_id"),
            "probe_bundle_id": fields.get("probe_bundle_id"),
            "position_cycle_id": fields.get("position_cycle_id"),
            "broker_order_no": fields.get("broker_order_no") or fields.get("order_no"),
        }
        stage_lower = stage.lower()
        actual_order_submitted = _bool(fields.get("actual_order_submitted"))
        filled = "fill" in stage_lower or _bool(fields.get("filled"))
        realized_stage = any(
            token in stage_lower
            for token in (
                "sell_fill",
                "sell_filled",
                "exit_fill",
                "trade_completed",
                "position_completed",
            )
        )
        realized_profit_pct = (
            _number(
                fields.get("realized_profit_pct")
                if fields.get("realized_profit_pct") is not None
                else fields.get("profit_rate")
            )
            if realized_stage
            else None
        )
        correlation_identifier_present = any(
            lifecycle_identifiers.get(key) not in (None, "", "-")
            for key in (
                "decision_trace_id",
                "entry_price_decision_trace_id",
                "broker_order_no",
            )
        )
        if (
            correlation_identifier_present
            or actual_order_submitted
            or filled
            or realized_profit_pct is not None
        ):
            lifecycle_key = (
                timestamp.isoformat() if timestamp else None,
                stage,
                code,
                *(lifecycle_identifiers.get(key) for key in lifecycle_identifiers),
                actual_order_submitted,
                filled,
                realized_profit_pct,
            )
            if lifecycle_key in lifecycle_seen:
                continue
            lifecycle_seen.add(lifecycle_key)
            lifecycle.append(
                {
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "stage": stage,
                    "stock_code": code,
                    **lifecycle_identifiers,
                    "actual_order_submitted": actual_order_submitted,
                    "filled": filled,
                    "realized_profit_pct": realized_profit_pct,
                }
            )
    for price_row in price_buckets.values():
        evaluation_ids = price_row.pop("_post_block_evaluation_ids", [])
        provenances: list[dict[str, Any]] = []
        for evaluation_id_value in evaluation_ids:
            evaluation_id = str(evaluation_id_value or "").strip()
            post_block_meta = post_block_meta_by_evaluation.get(evaluation_id) or {}
            if not (
                evaluation_id
                and post_block_meta.get("decision_trace_id")
                and post_block_meta.get("registered_at")
                and _number(post_block_meta.get("reference_price"))
                and _number(post_block_meta.get("gross_target_pct"))
                and _number(post_block_meta.get("adverse_pct"))
                and _number(post_block_meta.get("horizon_sec"))
                and _normalize_stock_code(post_block_meta.get("stock_code"))
                == _normalize_stock_code(price_row.get("stock_code"))
                and _venue(post_block_meta.get("effective_venue"))
                == _venue(price_row.get("effective_venue"))
                and _session(post_block_meta.get("session_bucket"))
                == _session(price_row.get("session_bucket"))
            ):
                continue
            provenances.append(
                {
                    "label_version": RISING_MISSED_POST_BLOCK_LABEL_VERSION,
                    "evaluation_id": evaluation_id,
                    "stock_code": post_block_meta.get("stock_code"),
                    "decision_trace_id": post_block_meta.get("decision_trace_id"),
                    "registered_at": post_block_meta.get("registered_at"),
                    "reference_price": post_block_meta.get("reference_price"),
                    "effective_venue": post_block_meta.get("effective_venue"),
                    "session_bucket": post_block_meta.get("session_bucket"),
                    "gross_target_pct": post_block_meta.get("gross_target_pct"),
                    "adverse_pct": post_block_meta.get("adverse_pct"),
                    "horizon_sec": post_block_meta.get("horizon_sec"),
                    "source_block_stage": post_block_meta.get("source_block_stage"),
                    "source_block_reason": post_block_meta.get("source_block_reason"),
                    "source_quality_status": "pass_exact_trace_evaluation_join",
                    "counterfactual_only": True,
                }
            )
        if provenances:
            price_row["post_block_outcome_provenances"] = provenances
    prices = sorted(
        price_buckets.values(),
        key=lambda row: (
            row["timestamp"],
            row["stock_code"],
            row["effective_venue"],
            row["session_bucket"],
        ),
    )
    return prices, lifecycle


def _linked_rising_missed_post_block_outcome(
    *,
    label: dict[str, Any],
    price_rows: list[dict[str, Any]],
    as_of: datetime,
) -> dict[str, Any] | None:
    """Return the bounded TP1 outcome owned by this exact decision trace.

    The same symbol may receive multiple AI decisions a few minutes apart.  A
    symbol/time-window join would leak the first sampler outcome into the later
    decision.  Require the runtime evaluation-to-trace link recorded by the
    blocker producer and keep this result counterfactual/offline-only.
    """

    if _stage(label.get("decision_stage")) != "entry":
        return None
    trace_id = str(label.get("decision_trace_id") or "").strip()
    decision_ts = _parse_ts(label.get("decision_ts"))
    if not trace_id or decision_ts is None:
        return None
    linked: list[dict[str, Any]] = []
    for row in price_rows:
        provenances = row.get("post_block_outcome_provenances")
        provenances = provenances if isinstance(provenances, list) else []
        for provenance in provenances:
            provenance = provenance if isinstance(provenance, dict) else {}
            if str(provenance.get("decision_trace_id") or "") != trace_id:
                continue
            registered_at = _parse_ts(provenance.get("registered_at"))
            reference = _number(provenance.get("reference_price"))
            timestamp = row.get("_timestamp")
            if (
                registered_at is None
                or registered_at < decision_ts
                or reference is None
                or reference <= 0
                or not isinstance(timestamp, datetime)
                or timestamp < registered_at
                or not _same_route(label, row)
            ):
                continue
            linked.append({**row, "post_block_outcome_provenance": provenance})
    if not linked:
        return None
    linked.sort(key=lambda row: row["_timestamp"])
    first_provenance = linked[0]["post_block_outcome_provenance"]
    evaluation_id = str(first_provenance.get("evaluation_id") or "")
    linked = [
        row
        for row in linked
        if str(
            (row.get("post_block_outcome_provenance") or {}).get("evaluation_id") or ""
        )
        == evaluation_id
    ]
    registered_at = _parse_ts(first_provenance.get("registered_at"))
    reference = _number(first_provenance.get("reference_price"))
    gross_target_pct = _number(first_provenance.get("gross_target_pct"))
    adverse_pct = _number(first_provenance.get("adverse_pct"))
    horizon_sec = _number(first_provenance.get("horizon_sec"))
    if (
        registered_at is None
        or reference is None
        or reference <= 0
        or gross_target_pct is None
        or gross_target_pct <= 0
        or adverse_pct is None
        or adverse_pct >= 0
        or horizon_sec is None
        or horizon_sec <= 0
    ):
        return None
    horizon_end = registered_at + timedelta(seconds=horizon_sec)
    linked = [row for row in linked if row["_timestamp"] <= horizon_end]
    if not linked:
        return None
    target_price = reference * (1.0 + gross_target_pct / 100.0)
    adverse_price = reference * (1.0 + adverse_pct / 100.0)
    target_hit_at = next(
        (
            row["_timestamp"].isoformat()
            for row in linked
            if row["_high"] >= target_price
        ),
        None,
    )
    adverse_hit_at = next(
        (
            row["_timestamp"].isoformat()
            for row in linked
            if row["_low"] <= adverse_price
        ),
        None,
    )
    if target_hit_at and adverse_hit_at and target_hit_at == adverse_hit_at:
        outcome_label = "same_sample_ambiguous"
    elif target_hit_at and (not adverse_hit_at or target_hit_at < adverse_hit_at):
        outcome_label = "gross_target_first"
    elif adverse_hit_at:
        outcome_label = "adverse_stop_first"
    elif as_of >= horizon_end:
        outcome_label = "neither_hit"
    else:
        outcome_label = "pending_horizon"
    max_move_pct = max(((row["_high"] / reference) - 1.0) * 100.0 for row in linked)
    min_move_pct = min(((row["_low"] / reference) - 1.0) * 100.0 for row in linked)
    sample_floor_pass = len(linked) >= RISING_MISSED_POST_BLOCK_MIN_FRESH_SAMPLES
    return {
        "label_version": RISING_MISSED_POST_BLOCK_LABEL_VERSION,
        "link_status": "exact_trace_evaluation_joined",
        "evaluation_id": evaluation_id,
        "decision_trace_id": trace_id,
        "registered_at": registered_at.isoformat(),
        "reference_price": reference,
        "gross_target_pct": gross_target_pct,
        "adverse_pct": adverse_pct,
        "horizon_sec": horizon_sec,
        "source_block_stage": first_provenance.get("source_block_stage"),
        "source_block_reason": first_provenance.get("source_block_reason"),
        "gross_first_hit_label": outcome_label,
        "target_hit_at": target_hit_at,
        "adverse_hit_at": adverse_hit_at,
        "max_move_pct": round(max_move_pct, 10),
        "min_move_pct": round(min_move_pct, 10),
        "fresh_sample_count": len(linked),
        "metric_role": "ai_decision_quality_outcome_attribution",
        "decision_authority": "offline_replay_and_attribution_only",
        "window_policy": (
            "exact_trace_evaluation_same_venue_session_bounded_post_block_window"
        ),
        "sample_floor": "2_fresh_route_consistent_post_block_price_samples",
        "sample_floor_pass": sample_floor_pass,
        "primary_decision_metric": "gross_target_first_before_adverse_stop",
        "source_quality_gate": (
            "exact_trace_evaluation_join_and_fresh_same_route_price_samples"
        ),
        "source_quality_status": (
            "pass" if sample_floor_pass else "sample_floor_keep_collecting"
        ),
        "counterfactual_only": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": list(OFFLINE_CONTRACT["forbidden_uses"]),
    }


def _request_code_for_venue(stock_code: Any, effective_venue: Any) -> str | None:
    code = _normalize_stock_code(stock_code)
    venue = _venue(effective_venue)
    if venue == "NXT":
        return f"{code}_NX"
    if venue == "SOR":
        return f"{code}_AL"
    if venue == "KRX":
        return code
    return None


def _venue_session_consistent(effective_venue: Any, session_bucket: Any) -> bool:
    venue = _venue(effective_venue)
    session = _session(session_bucket)
    allowed_sessions = {
        "KRX": {"KRX_REGULAR"},
        "SOR": {"KRX_REGULAR"},
        "NXT": {
            "NXT_PREMARKET",
            "PREMARKET_KRX_LIKE",
            "NXT_REGULAR_OVERLAP",
            "NXT_AFTERMARKET",
        },
    }
    return session in allowed_sessions.get(venue, set())


def _timestamp_in_session(timestamp: datetime, session_bucket: Any) -> bool:
    minute = timestamp.hour * 60 + timestamp.minute
    session = _session(session_bucket)
    if session in {"PREMARKET_KRX_LIKE", "NXT_PREMARKET"}:
        return 8 * 60 <= minute < 9 * 60
    if session == "KRX_REGULAR":
        return 9 * 60 <= minute <= 15 * 60 + 30
    if session == "NXT_REGULAR_OVERLAP":
        return 9 * 60 <= minute <= 15 * 60 + 30
    if session == "NXT_AFTERMARKET":
        return 15 * 60 + 30 < minute <= 20 * 60
    return False


def load_kiwoom_completed_minute_price_rows(
    *,
    target_date: str,
    labels: Iterable[dict[str, Any]],
    as_of: datetime,
    fetcher: Callable[[str, str], tuple[list[dict[str, Any]], dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load completed ka10080 bars for exact label routes.

    ``fetcher`` receives ``(stock_code, request_code)`` so the CLI can use a
    cached read-only token while tests remain network-independent.  Chart bars
    are an offline outcome source only; they never provide runtime quote
    freshness or order authority.
    """

    routes = sorted(
        {
            (
                _normalize_stock_code(row.get("stock_code")),
                _venue(row.get("effective_venue")),
                _session(row.get("session_bucket")),
            )
            for row in labels
            if _normalize_stock_code(row.get("stock_code"))
            and _venue(row.get("effective_venue"))
            and _session(row.get("session_bucket"))
        }
    )
    target_compact = target_date.replace("-", "")
    current_minute = as_of.replace(second=0, microsecond=0)
    prices: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    fetch_cache: dict[tuple[str, str], tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    for code, venue, session in routes:
        request_code = _request_code_for_venue(code, venue)
        if request_code is None or not _venue_session_consistent(venue, session):
            provenance.append(
                {
                    "stock_code": code,
                    "effective_venue": venue,
                    "session_bucket": session,
                    "request_code": request_code,
                    "api_id": "ka10080",
                    "received_count": None,
                    "target_completed_bar_count": 0,
                    "coverage_start": None,
                    "coverage_end": None,
                    "continuation_observed": False,
                    "continuation_page_limit_reached": False,
                    "fetch_error": (
                        "unsupported_effective_venue"
                        if request_code is None
                        else "venue_session_conflict"
                    ),
                    "source_quality_status": "source_quality_blocked",
                }
            )
            continue
        fetch_key = (code, request_code)
        if fetch_key not in fetch_cache:
            try:
                fetch_cache[fetch_key] = fetcher(code, request_code)
            except Exception as exc:
                fetch_cache[fetch_key] = (
                    [],
                    {
                        "fetch_error": type(exc).__name__,
                    },
                )
        candles, source_meta = fetch_cache[fetch_key]
        source_meta = source_meta if isinstance(source_meta, dict) else {}
        route_prices: list[dict[str, Any]] = []
        for candle in candles or []:
            source_timestamp = str(candle.get("source_timestamp") or "").strip()
            if (
                len(source_timestamp) < 14
                or not source_timestamp[:14].isdigit()
                or not source_timestamp.startswith(target_compact)
            ):
                continue
            timestamp = _parse_ts(
                datetime.strptime(source_timestamp[:14], "%Y%m%d%H%M%S")
                .replace(tzinfo=KST)
                .isoformat()
            )
            price = _number(candle.get("현재가"))
            open_price = _number(candle.get("시가"))
            high = _number(candle.get("고가"))
            low = _number(candle.get("저가"))
            if (
                timestamp is None
                or price is None
                or price <= 0
                or timestamp.replace(second=0, microsecond=0) >= current_minute
                or not _timestamp_in_session(timestamp, session)
            ):
                continue
            route_prices.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "stock_code": code,
                    "price": price,
                    "open": (
                        open_price
                        if open_price is not None and open_price > 0
                        else None
                    ),
                    "high": high if high is not None and high > 0 else price,
                    "low": low if low is not None and low > 0 else price,
                    "close": price,
                    "effective_venue": venue,
                    "session_bucket": session,
                    "source_quality": "pass_completed_ka10080_bar",
                    "source_api_id": "ka10080",
                    "source_request_code": request_code,
                    "source_time_basis": "ka10080_cntr_tm_bar_timestamp",
                    "completed_bar_only": True,
                }
            )
        prices.extend(route_prices)
        timestamps = [row["timestamp"] for row in route_prices]
        provenance.append(
            {
                "stock_code": code,
                "effective_venue": venue,
                "session_bucket": session,
                "request_code": request_code,
                "api_id": source_meta.get("api_id") or "ka10080",
                "received_count": source_meta.get("received_count"),
                "target_completed_bar_count": len(route_prices),
                "coverage_start": min(timestamps) if timestamps else None,
                "coverage_end": max(timestamps) if timestamps else None,
                "continuation_observed": bool(source_meta.get("cont_yn_seen")),
                "continuation_page_limit_reached": bool(
                    source_meta.get("continuous_page_limit_reached")
                ),
                "fetch_error": source_meta.get("fetch_error"),
                "source_quality_status": (
                    "pass_target_window_available"
                    if route_prices
                    else "source_quality_blocked"
                ),
            }
        )
    return prices, provenance


def merge_preferred_outcome_price_rows(
    primary_rows: Iterable[dict[str, Any]],
    fallback_rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Merge outcome prices while keeping one route/minute source owner.

    Completed Kiwoom OHLC bars own their covered route/minute. Pipeline rows
    remain available only outside that coverage so lifecycle correlation can
    be retained without duplicating or contaminating MFE/MAE observations.
    """

    primary = list(primary_rows)
    covered_minutes: set[tuple[str, str, str, datetime]] = set()
    for row in primary:
        timestamp = _parse_ts(row.get("timestamp"))
        code = _normalize_stock_code(row.get("stock_code"))
        venue = _venue(row.get("effective_venue"))
        session = _session(row.get("session_bucket"))
        if timestamp and code and venue and session:
            covered_minutes.add(
                (code, venue, session, timestamp.replace(second=0, microsecond=0))
            )
    retained_fallback: list[dict[str, Any]] = []
    suppressed_count = 0
    for row in fallback_rows:
        timestamp = _parse_ts(row.get("timestamp"))
        key = (
            _normalize_stock_code(row.get("stock_code")),
            _venue(row.get("effective_venue")),
            _session(row.get("session_bucket")),
            timestamp.replace(second=0, microsecond=0) if timestamp else None,
        )
        if timestamp and key in covered_minutes:
            suppressed_count += 1
            provenances = row.get("post_block_outcome_provenances")
            if isinstance(provenances, list) and provenances:
                # Completed 1m OHLC remains the general MFE/MAE owner, but it
                # cannot replace second-level exact-evaluation observations
                # used to order the bounded TP1/adverse first hit.
                retained_fallback.append(
                    {
                        **row,
                        "post_block_attribution_only": True,
                    }
                )
            continue
        retained_fallback.append(row)
    return primary + retained_fallback, suppressed_count


def _venue(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"PREMARKET", "PREMARKET_KRX_LIKE"}:
        return "PREMARKET_KRX_LIKE"
    if "NXT" in text:
        return "NXT"
    if "KRX" in text:
        return "KRX"
    return text


def _session(value: Any) -> str:
    text = str(value or "").strip().upper()
    aliases = {
        "REGULAR": "KRX_REGULAR",
        "AFTERMARKET": "NXT_AFTERMARKET",
        "PREMARKET": "PREMARKET_KRX_LIKE",
        "KRX_LIKE_PREMARKET": "PREMARKET_KRX_LIKE",
        "NXT_OPEN_OBSERVE": "NXT_AFTERMARKET",
    }
    return aliases.get(text, text)


def _filter_rows_for_cohort(
    rows: Iterable[dict[str, Any]],
    *,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> list[dict[str, Any]]:
    """Keep an exact venue/session cohort without cross-route substitution."""

    venue = _venue(effective_venue) if effective_venue else ""
    session = _session(session_bucket) if session_bucket else ""
    return [
        row
        for row in rows
        if (not venue or _venue(row.get("effective_venue")) == venue)
        and (not session or _session(row.get("session_bucket")) == session)
    ]


def _pipeline_event_price_source_quality(
    fields: dict[str, Any],
    *,
    explicit_source_quality: str,
) -> str:
    """Qualify an observed pipeline price from explicit freshness provenance.

    Most live pipeline producers declare their source-quality *contract* and
    freshness facts separately instead of emitting ``source_quality_status``.
    Treating those rows as ``not_recorded`` made the pipeline outcome source
    permanently empty.  This adapter accepts only affirmative, symbol-local
    freshness evidence and keeps stale/conflicted observations fail-closed.
    """

    if _holding_pipeline_price_contract_fresh(fields):
        return "event_observed_holding_exact"
    candidate = {"source_quality": explicit_source_quality}
    if _price_source_usable(candidate):
        return explicit_source_quality
    if not str(fields.get("source_quality_gate") or "").strip():
        return explicit_source_quality
    venue_resolution = str(fields.get("venue_resolution") or "").strip().lower()
    if any(token in venue_resolution for token in ("conflict", "missing")):
        return "source_quality_blocked"
    if _bool(fields.get("scanner_promotion_price_conflict")) or _bool(
        fields.get("quote_stale")
    ):
        return "source_quality_blocked"

    refresh_reason = (
        str(fields.get("pre_ai_ws_snapshot_refresh_reason") or "").strip().lower()
    )
    rising_refresh_reason = (
        str(fields.get("rising_missed_watch_delta_refresh_reason") or "")
        .strip()
        .lower()
    )
    affirmative_freshness = any(
        (
            _bool(fields.get("scanner_promotion_price_ws_fresh")),
            _bool(fields.get("scanner_promotion_reanchor_source_fresh")),
            _bool(fields.get("rising_missed_nxt_post_block_fresh_sample")),
            (
                _bool(fields.get("rising_missed_watch_delta_refresh_applied"))
                and rising_refresh_reason == "same_symbol_current_price_observed"
            ),
            refresh_reason in {"input_snapshot_fresh", "latest_ws_snapshot_fresh"},
        )
    )
    return "event_observed" if affirmative_freshness else explicit_source_quality


def _holding_pipeline_price_contract_fresh(fields: dict[str, Any]) -> bool:
    """Accept only evaluated holding rows with a complete fresh broker/BBO contract."""

    if str(fields.get("ai_prompt_type") or "").strip() != "scalping_holding_score":
        return False
    if (
        str(fields.get("holding_context_schema") or "").strip()
        != HOLDING_CONTEXT_SCHEMA
    ):
        return False
    if str(fields.get("ai_result_source") or "").strip().lower() != "live":
        return False
    if (
        str(fields.get("ai_decision_evaluation_status") or "").strip().lower()
        != "evaluated"
    ):
        return False
    if _bool(fields.get("holding_score_preflight_blocked")):
        return False
    if str(
        fields.get("holding_score_preflight_source_quality") or ""
    ).strip().lower() not in {"fresh", "fresh_consistent", "partial"}:
        return False
    if str(
        fields.get("holding_context_source_quality_status") or ""
    ).strip().lower() not in {"fresh", "fresh_consistent", "partial"}:
        return False
    if fields.get("holding_context_blockers") not in ([], (), "", "[]"):
        return False
    candle_route_conflicts = _number(
        fields.get("holding_context_candle_route_conflict_count")
    )
    if candle_route_conflicts is None or candle_route_conflicts != 0:
        return False
    if not all(
        _bool(fields.get(key))
        for key in (
            "holding_context_bbo_fresh",
            "holding_context_position_valid",
            "holding_context_order_consistent",
        )
    ):
        return False
    if "quote_stale" not in fields or "tick_context_stale" not in fields:
        return False
    if _bool(fields.get("quote_stale")) or _bool(fields.get("tick_context_stale")):
        return False
    quote_age_ms = _number(
        fields.get("holding_context_quote_age_ms")
        if fields.get("holding_context_quote_age_ms") is not None
        else fields.get("quote_age_ms")
    )
    best_bid = _number(fields.get("holding_context_best_bid"))
    return bool(
        quote_age_ms is not None
        and 0 <= quote_age_ms <= 3_000
        and best_bid is not None
        and best_bid > 0
    )


def _pipeline_event_observed_price(fields: dict[str, Any]) -> float | None:
    """Select the price owned by the same freshness fact used for qualification."""

    selected_keys: tuple[str, ...]
    refresh_reason = (
        str(fields.get("pre_ai_ws_snapshot_refresh_reason") or "").strip().lower()
    )
    rising_refresh_reason = (
        str(fields.get("rising_missed_watch_delta_refresh_reason") or "")
        .strip()
        .lower()
    )
    if _holding_pipeline_price_contract_fresh(fields):
        selected_keys = ("holding_context_best_bid",)
    elif _bool(fields.get("scanner_promotion_price_ws_fresh")) and not _bool(
        fields.get("scanner_promotion_price_conflict")
    ):
        selected_keys = (
            "scanner_promotion_price_effective_curr",
            "scanner_promotion_price_ws_curr",
        )
    elif _bool(fields.get("rising_missed_nxt_post_block_fresh_sample")):
        selected_keys = ("current_price_observed",)
    elif (
        _bool(fields.get("rising_missed_watch_delta_refresh_applied"))
        and rising_refresh_reason == "same_symbol_current_price_observed"
    ):
        selected_keys = ("current_price_observed",)
    elif refresh_reason in {"input_snapshot_fresh", "latest_ws_snapshot_fresh"}:
        selected_keys = ("current_price", "curr", "current_price_observed")
    else:
        selected_keys = (
            "current_price",
            "curr",
            "price",
            "observed_price",
            "current_price_observed",
            "trade_price",
            "fill_price",
        )
    return next(
        (
            parsed
            for key in selected_keys
            if (parsed := _number(fields.get(key))) is not None and parsed > 0
        ),
        None,
    )


def _price_source_usable(price: dict[str, Any]) -> bool:
    quality = str(price.get("source_quality") or "").strip().lower()
    if not quality or any(
        token in quality
        for token in (
            "conflict",
            "duplicate",
            "invalid",
            "stale",
            "missing",
            "unavailable",
            "not_recorded",
            "unknown",
        )
    ):
        return False
    return any(
        token in quality
        for token in ("pass", "fresh", "usable", "valid", "event_observed")
    )


def _same_route(label: dict[str, Any], price: dict[str, Any]) -> bool:

    venue = _venue(label.get("effective_venue"))
    observed_venue = _venue(price.get("effective_venue"))
    if venue and (not observed_venue or venue != observed_venue):
        return False
    session = _session(label.get("session_bucket"))
    observed_session = _session(price.get("session_bucket"))
    if session and (not observed_session or session != observed_session):
        return False
    return _price_source_usable(price)


def _correlation(
    label: dict[str, Any], lifecycle_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    label_code = _normalize_stock_code(label.get("stock_code"))
    decision_ts = _parse_ts(label.get("decision_ts"))
    label_stage = _stage(label.get("decision_stage"))
    label_trace_id = str(label.get("decision_trace_id") or "").strip()
    identifiers = {
        str(label.get(key))
        for key in (
            "decision_trace_id",
            "record_id",
            "recommendation_id",
            "probe_bundle_id",
            "position_cycle_id",
            "broker_order_no",
        )
        if label.get(key) not in (None, "", "-")
    }
    matched = []
    for row in lifecycle_rows:
        row_code = _normalize_stock_code(row.get("stock_code"))
        row_ts = _parse_ts(row.get("timestamp"))
        if not label_code or not row_code or row_code != label_code:
            continue
        if decision_ts is None or row_ts is None or row_ts < decision_ts:
            continue
        row_trace_id = str(
            (
                row.get("entry_price_decision_trace_id")
                if label_stage == "entry_price"
                else row.get("decision_trace_id")
            )
            or ""
        ).strip()
        if label_trace_id and row_trace_id and label_trace_id != row_trace_id:
            continue
        values = {
            str(row.get(key))
            for key in (
                "record_id",
                "recommendation_id",
                "probe_bundle_id",
                "position_cycle_id",
                "broker_order_no",
            )
            if row.get(key) not in (None, "", "-")
        }
        if row_trace_id:
            values.add(row_trace_id)
        if identifiers and identifiers.intersection(values):
            matched.append(row)
    matched.sort(
        key=lambda row: (
            _parse_ts(row.get("timestamp")) or datetime.min.replace(tzinfo=KST)
        )
    )
    realized = [
        row["realized_profit_pct"]
        for row in matched
        if row.get("realized_profit_pct") is not None
    ]
    matched_event_count = len(matched)
    matched_stage_counts = Counter(
        str(row.get("stage") or "unknown").strip().lower() for row in matched
    )
    position_cycle_ids = sorted(
        {
            str(row.get("position_cycle_id"))
            for row in matched
            if row.get("position_cycle_id") not in (None, "", "-")
        }
    )
    probe_bundle_ids = sorted(
        {
            str(row.get("probe_bundle_id"))
            for row in matched
            if row.get("probe_bundle_id") not in (None, "", "-")
        }
    )
    broker_order_nos = sorted(
        {
            str(row.get("broker_order_no"))
            for row in matched
            if row.get("broker_order_no") not in (None, "", "-")
        }
    )

    def stage_seen(*tokens: str) -> bool:
        return any(
            any(token in stage for token in tokens) for stage in matched_stage_counts
        )

    initial_probe_seen = any(
        "probe" in stage and "post_probe" not in stage and "post-probe" not in stage
        for stage in matched_stage_counts
    )

    return {
        "status": "exact_matched" if matched else "open_unresolved",
        "matched_event_count": matched_event_count,
        "matched_stage_counts": dict(matched_stage_counts),
        "position_cycle_ids": position_cycle_ids,
        "probe_bundle_ids": probe_bundle_ids,
        "broker_order_nos": broker_order_nos,
        "lifecycle_stage_presence": {
            "probe": initial_probe_seen,
            "post_probe": stage_seen("post_probe", "post-probe"),
            "residual_multi_leg": stage_seen("residual", "multi_leg", "multi-leg"),
            "scale_in": stage_seen("scale_in", "scale-in", "avg_down", "pyramid"),
            "exit": stage_seen("sell", "exit", "trade_completed", "position_completed"),
        },
        "actual_order_submitted": (
            any(row.get("actual_order_submitted") for row in matched)
            if matched
            else None
        ),
        "fill_observed": (
            any(row.get("filled") for row in matched) if matched else None
        ),
        "realized_profit_pct": realized[-1] if realized else None,
        "realized_event_count": len(realized),
        "realized_separate_from_counterfactual": True,
    }


def mature_outcome_labels(
    *,
    pending_labels: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
    as_of: datetime,
) -> list[dict[str, Any]]:
    prices_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in price_rows:
        timestamp = _parse_ts(row.get("timestamp"))
        price = _number(row.get("price"))
        high = _number(row.get("high"))
        low = _number(row.get("low"))
        close = _number(row.get("close"))
        code = _normalize_stock_code(row.get("stock_code"))
        if timestamp and price and price > 0 and code:
            prices_by_code[code].append(
                {
                    **row,
                    "_timestamp": timestamp,
                    "_price": price,
                    "_high": high if high is not None and high > 0 else price,
                    "_low": low if low is not None and low > 0 else price,
                    "_close": close if close is not None and close > 0 else price,
                }
            )
    for rows in prices_by_code.values():
        rows.sort(key=lambda row: row["_timestamp"])
    matured: list[dict[str, Any]] = []
    for pending in pending_labels:
        decision_ts = _parse_ts(pending.get("decision_ts"))
        reference = _number(pending.get("reference_price"))
        code = _normalize_stock_code(pending.get("stock_code"))
        stage = _stage(pending.get("decision_stage"))
        invalid = list(pending.get("invalid_reasons") or [])
        horizon_metrics: dict[str, dict[str, Any]] = {}
        matured_horizons: list[int] = []
        pending_horizons: list[int] = []
        if not decision_ts:
            invalid.append("decision_ts_invalid")
        if reference is None or reference <= 0:
            invalid.append("reference_price_missing")
        if not str(pending.get("effective_venue") or "").strip():
            invalid.append("effective_venue_missing")
        if not str(pending.get("session_bucket") or "").strip():
            invalid.append("session_bucket_missing")
        next_session_start: datetime | None = None
        next_session_date = ""
        next_session_venue = ""
        next_session_bucket = ""
        if stage == "overnight" and decision_ts:
            next_session_candidates = [
                row
                for row in prices_by_code.get(code, [])
                if row["_timestamp"].date() > decision_ts.date()
                and row.get("post_block_attribution_only") is not True
                and _venue(row.get("effective_venue"))
                and _session(row.get("session_bucket"))
                and _price_source_usable(row)
            ]
            if next_session_candidates:
                first = next_session_candidates[0]
                next_session_start = first["_timestamp"]
                next_session_date = first["_timestamp"].date().isoformat()
                next_session_venue = _venue(first.get("effective_venue"))
                next_session_bucket = _session(first.get("session_bucket"))
        for horizon in HORIZONS_MIN:
            window_start = next_session_start if stage == "overnight" else decision_ts
            horizon_end = (
                window_start + timedelta(minutes=horizon) if window_start else None
            )
            if not horizon_end or as_of < horizon_end:
                pending_horizons.append(horizon)
                continue
            if stage == "overnight":
                window = [
                    row
                    for row in prices_by_code.get(code, [])
                    if window_start <= row["_timestamp"] <= horizon_end
                    and row.get("post_block_attribution_only") is not True
                    and row["_timestamp"].date().isoformat() == next_session_date
                    and _venue(row.get("effective_venue")) == next_session_venue
                    and _session(row.get("session_bucket")) == next_session_bucket
                    and _price_source_usable(row)
                ]
            else:
                window = [
                    row
                    for row in prices_by_code.get(code, [])
                    if decision_ts < row["_timestamp"] <= horizon_end
                    and row.get("post_block_attribution_only") is not True
                    and _same_route(pending, row)
                ]
            if not window or reference is None or reference <= 0:
                pending_horizons.append(horizon)
                continue
            if (
                horizon_end - window[-1]["_timestamp"]
            ).total_seconds() > HORIZON_END_MAX_LAG_SEC:
                pending_horizons.append(horizon)
                continue
            high_returns = [
                round(((row["_high"] / reference) - 1.0) * 100.0, 10) for row in window
            ]
            low_returns = [
                round(((row["_low"] / reference) - 1.0) * 100.0, 10) for row in window
            ]
            end_return = round(((window[-1]["_close"] / reference) - 1.0) * 100.0, 10)
            target_price = _number(pending.get("target_price"))
            adverse_price = _number(pending.get("adverse_price"))
            target_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if target_price is not None and row["_high"] >= target_price
                ),
                None,
            )
            adverse_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if adverse_price is not None and row["_low"] <= adverse_price
                ),
                None,
            )
            first_hit = (
                "ambiguous_same_bar"
                if target_hit and adverse_hit and target_hit == adverse_hit
                else (
                    "target"
                    if target_hit and (not adverse_hit or target_hit < adverse_hit)
                    else ("adverse" if adverse_hit else "neither")
                )
            )
            entry_path_metrics: dict[str, Any] = {}
            if stage == "entry":
                entry_path_target_price = reference * (
                    1.0 + (ENTRY_PATH_TARGET_PCT / 100.0)
                )
                entry_path_adverse_price = reference * (
                    1.0 + (ENTRY_PATH_ADVERSE_PCT / 100.0)
                )
                entry_path_target_hit = next(
                    (
                        row["_timestamp"].isoformat()
                        for row in window
                        if row["_high"] >= entry_path_target_price
                    ),
                    None,
                )
                entry_path_adverse_hit = next(
                    (
                        row["_timestamp"].isoformat()
                        for row in window
                        if row["_low"] <= entry_path_adverse_price
                    ),
                    None,
                )
                entry_path_first_hit = (
                    "same_bar_ambiguous"
                    if entry_path_target_hit
                    and entry_path_adverse_hit
                    and entry_path_target_hit == entry_path_adverse_hit
                    else (
                        "target_first"
                        if entry_path_target_hit
                        and (
                            not entry_path_adverse_hit
                            or entry_path_target_hit < entry_path_adverse_hit
                        )
                        else (
                            "adverse_first" if entry_path_adverse_hit else "neither_hit"
                        )
                    )
                )
                entry_path_metrics = {
                    "entry_path_label_version": ENTRY_PATH_LABEL_VERSION,
                    "entry_path_target_pct": ENTRY_PATH_TARGET_PCT,
                    "entry_path_adverse_pct": ENTRY_PATH_ADVERSE_PCT,
                    "entry_path_target_hit_at": entry_path_target_hit,
                    "entry_path_adverse_hit_at": entry_path_adverse_hit,
                    "entry_path_first_hit": entry_path_first_hit,
                }
            profit_opportunity_price = reference * (
                1.0 + (PROFIT_OPPORTUNITY_THRESHOLD_PCT / 100.0)
            )
            profit_opportunity_index = next(
                (
                    index
                    for index, row in enumerate(window)
                    if row["_high"] >= profit_opportunity_price
                ),
                None,
            )
            below_reference_index = next(
                (index for index, row in enumerate(window) if row["_low"] < reference),
                None,
            )
            if profit_opportunity_index is None:
                profit_opportunity_sequence = (
                    "below_reference_without_profit"
                    if below_reference_index is not None
                    else "neither"
                )
            elif below_reference_index is None:
                profit_opportunity_sequence = "profit_without_prior_drawdown"
            elif below_reference_index < profit_opportunity_index:
                profit_opportunity_sequence = "drawdown_then_profit_recovery"
            elif profit_opportunity_index < below_reference_index:
                profit_opportunity_sequence = "profit_before_drawdown"
            else:
                profit_opportunity_sequence = "ambiguous_same_bar"
            profit_opportunity_row = (
                window[profit_opportunity_index]
                if profit_opportunity_index is not None
                else None
            )
            below_reference_row = (
                window[below_reference_index]
                if below_reference_index is not None
                else None
            )
            pre_profit_rows = (
                window[: profit_opportunity_index + 1]
                if profit_opportunity_index is not None
                else []
            )
            horizon_metrics[f"{horizon}m"] = {
                "sample_count": len(window),
                "mfe_pct": max(high_returns),
                "mae_pct": min(low_returns),
                "end_return_pct": end_return,
                "target_hit_at": target_hit,
                "adverse_hit_at": adverse_hit,
                "first_hit": first_hit,
                **entry_path_metrics,
                "profit_opportunity_threshold_pct": (PROFIT_OPPORTUNITY_THRESHOLD_PCT),
                "profit_opportunity_observed": (profit_opportunity_index is not None),
                "profit_opportunity_hit_at": (
                    profit_opportunity_row["_timestamp"].isoformat()
                    if profit_opportunity_row is not None
                    else None
                ),
                "below_reference_excursion_at": (
                    below_reference_row["_timestamp"].isoformat()
                    if below_reference_row is not None
                    else None
                ),
                "profit_opportunity_sequence": profit_opportunity_sequence,
                "pre_profit_mae_pct": (
                    min(
                        round(((row["_low"] / reference) - 1.0) * 100.0, 10)
                        for row in pre_profit_rows
                    )
                    if pre_profit_rows
                    else None
                ),
                "counterfactual_only": True,
                "window_basis": (
                    "next_session_from_first_observation"
                    if stage == "overnight"
                    else "post_decision_same_route"
                ),
                "window_start": window_start.isoformat(),
                "observed_venue": (
                    next_session_venue
                    if stage == "overnight"
                    else _venue(pending.get("effective_venue"))
                ),
                "observed_session_bucket": (
                    next_session_bucket
                    if stage == "overnight"
                    else _session(pending.get("session_bucket"))
                ),
                "first_price": window[0]["_price"],
                "gap_from_reference_pct": (
                    round(((window[0]["_price"] / reference) - 1.0) * 100.0, 10)
                    if stage == "overnight"
                    else None
                ),
            }
            matured_horizons.append(horizon)
        correlation = _correlation(pending, lifecycle_rows)
        linked_post_block_outcome = _linked_rising_missed_post_block_outcome(
            label=pending,
            price_rows=prices_by_code.get(code, []),
            as_of=as_of,
        )
        longest = (
            horizon_metrics[f"{max(matured_horizons)}m"] if matured_horizons else {}
        )
        stage_outcome: dict[str, Any] = {}
        if stage == "entry":
            primary_entry_path = horizon_metrics.get(ENTRY_PATH_PRIMARY_HORIZON) or {}
            stage_outcome = {
                "entry_path_primary_horizon": ENTRY_PATH_PRIMARY_HORIZON,
                "entry_path_label_version": ENTRY_PATH_LABEL_VERSION,
                "entry_path_first_hit": primary_entry_path.get("entry_path_first_hit"),
                "entry_path_target_pct": ENTRY_PATH_TARGET_PCT,
                "entry_path_adverse_pct": ENTRY_PATH_ADVERSE_PCT,
                "entry_path_target_hit_at": primary_entry_path.get(
                    "entry_path_target_hit_at"
                ),
                "entry_path_adverse_hit_at": primary_entry_path.get(
                    "entry_path_adverse_hit_at"
                ),
                "entry_path_label_status": (
                    "mature" if primary_entry_path else "pending_primary_horizon"
                ),
                "counterfactual_only": True,
            }
            if linked_post_block_outcome is not None:
                stage_outcome["rising_missed_post_block_outcome"] = (
                    linked_post_block_outcome
                )
        elif stage == "post_probe":
            stage_outcome = {
                "residual_submitted": correlation["actual_order_submitted"],
                "fill_observed": correlation["fill_observed"],
                "incremental_mfe_pct": longest.get("mfe_pct"),
                "incremental_mae_pct": longest.get("mae_pct"),
            }
        elif stage == "scale_in":
            stage_outcome = {
                "incremental_return_pct": longest.get("end_return_pct"),
                "incremental_ev_pct": None,
                "incremental_ev_status": (
                    "not_available_without_add_no_add_notional_join"
                ),
                "additional_downside_pct": longest.get("mae_pct"),
            }
        elif stage == "holding":
            stage_outcome = {
                "secured_upside_pct": longest.get("mfe_pct"),
                "enlarged_loss_pct": longest.get("mae_pct"),
            }
        elif stage == "exit":
            stage_outcome = {
                "realized_profit_pct": correlation["realized_profit_pct"],
                "post_sell_mfe_pct": longest.get("mfe_pct"),
                "post_sell_mae_pct": longest.get("mae_pct"),
                "peak_giveback_pct": (
                    longest.get("mfe_pct", 0) - longest.get("end_return_pct", 0)
                    if longest
                    else None
                ),
            }
        elif stage == "overnight":
            shortest = (
                horizon_metrics[f"{min(matured_horizons)}m"] if matured_horizons else {}
            )
            stage_outcome = {
                "next_session_date": next_session_date or None,
                "next_session_venue": next_session_venue or None,
                "next_session_bucket": next_session_bucket or None,
                "next_session_gap_pct": shortest.get("gap_from_reference_pct"),
                "next_session_return_pct": longest.get("end_return_pct"),
                "next_session_mfe_pct": longest.get("mfe_pct"),
                "next_session_mae_pct": longest.get("mae_pct"),
            }
        status = (
            "mature"
            if len(matured_horizons) == len(HORIZONS_MIN)
            else ("partial" if matured_horizons else "pending")
        )
        source_quality = (
            "pass"
            if matured_horizons and not invalid
            else ("partial" if matured_horizons else "source_quality_blocked")
        )
        matured.append(
            {
                **pending,
                "label_status": status,
                "matured_at": as_of.isoformat() if matured_horizons else None,
                "matured_horizons_min": matured_horizons,
                "pending_horizons_min": pending_horizons,
                "horizon_metrics": horizon_metrics,
                "stage_outcome": stage_outcome,
                "correlation": correlation,
                "source_quality_status": source_quality,
                "invalid_reasons": sorted(set(invalid)),
                **OFFLINE_CONTRACT,
            }
        )
    return matured


def _primary_metric(label: dict[str, Any]) -> dict[str, Any] | None:
    metrics = label.get("horizon_metrics")
    if not isinstance(metrics, dict):
        return None
    horizon = PRIMARY_HORIZON_BY_STAGE.get(_stage(label.get("decision_stage")))
    metric = metrics.get(horizon) if horizon else None
    return metric if isinstance(metric, dict) else None


def _paired_outcome_recovery_signature(metric: Any) -> dict[str, Any] | None:
    """Normalize only the outcome fields preserved by paired-report recovery."""

    if not isinstance(metric, dict):
        return None
    numeric_fields = (
        "end_return_pct",
        "mfe_pct",
        "mae_pct",
        "entry_path_target_pct",
        "entry_path_adverse_pct",
        "profit_opportunity_threshold_pct",
        "pre_profit_mae_pct",
    )
    text_fields = (
        "first_hit",
        "entry_path_first_hit",
        "profit_opportunity_hit_at",
        "below_reference_excursion_at",
        "profit_opportunity_sequence",
    )
    return {
        **{field: _number(metric.get(field)) for field in numeric_fields},
        **{field: str(metric.get(field) or "") for field in text_fields},
        "profit_opportunity_observed": (
            metric.get("profit_opportunity_observed") is True
        ),
    }


def _taxonomy(label: dict[str, Any]) -> list[str]:
    action = str(label.get("action") or "").upper()
    preferred = _primary_metric(label) or {}
    mfe = _number(preferred.get("mfe_pct")) or 0.0
    mae = _number(preferred.get("mae_pct")) or 0.0
    end_return = _number(preferred.get("end_return_pct")) or 0.0
    first_hit = str(preferred.get("first_hit") or "")
    entry_path_first_hit = str(preferred.get("entry_path_first_hit") or "")
    stage = _stage(label.get("decision_stage"))
    stage_outcome = label.get("stage_outcome")
    stage_outcome = stage_outcome if isinstance(stage_outcome, dict) else {}
    post_block_outcome = stage_outcome.get("rising_missed_post_block_outcome")
    post_block_outcome = (
        post_block_outcome if isinstance(post_block_outcome, dict) else {}
    )
    errors: list[str] = []
    if action == "DROP" and mfe >= 1.0:
        errors.append("false_drop")
    if action == "WAIT" and mfe >= 1.0:
        errors.append("false_wait")
    if (
        action == "DROP"
        and post_block_outcome.get("gross_first_hit_label") == "gross_target_first"
        and post_block_outcome.get("source_quality_status") == "pass"
    ):
        errors.append("false_drop_post_block_gross_target_first")
    if action == "BUY" and (first_hit == "adverse" or mae <= -1.0):
        errors.append("false_buy")
    if stage == "entry" and action == "BUY" and entry_path_first_hit == "adverse_first":
        errors.append("false_buy_tight_stop_adverse_first")
    if (
        stage == "entry"
        and action in {"WAIT", "DROP"}
        and entry_path_first_hit == "target_first"
    ):
        errors.append("missed_entry_tight_stop_target_first")
    if stage == "scale_in" and action in {"ADD", "BUY", "SUPPORT"} and end_return < 0:
        errors.append("bad_scale_support")
    if stage in {"holding", "exit"} and action == "HOLD" and end_return <= -1.0:
        errors.append("bad_exit_defer")
    if stage == "exit" and action in {"EXIT", "SELL", "TRIM"} and mfe >= 1.0:
        errors.append("early_exit_support")
    confidence = _number(label.get("confidence")) or 0.0
    if confidence >= 80 and label.get("source_quality_status") != "pass":
        errors.append("unsupported_confidence")
    return errors


def _decision_value(action: Any, outcome: float | None) -> float | None:
    normalized = str(action or "").strip().upper()
    if outcome is None:
        return None
    if normalized in EXPOSURE_ACTIONS:
        return outcome
    if normalized in NO_EXPOSURE_ACTIONS:
        return 0.0
    return None


def _decision_exposure_selected(
    *,
    stage: str,
    action: Any,
    response: dict[str, Any],
) -> bool:
    """Map only an immediate action to offline exposure semantics.

    ``entry_probe_intent`` is an arm for the live recheck owner, not an order.
    Treating an armed WAIT as exposure incorrectly charges its entire future path
    to Entry AI even when freshness, strong-micro, latency, cap, or submit guards
    would stop it before the one-share probe.
    """

    _ = (stage, response)
    return str(action or "").strip().upper() in EXPOSURE_ACTIONS


def _decision_probe_armed(
    *,
    stage: str,
    action: Any,
    response: dict[str, Any],
) -> bool:
    """Identify an Entry probe candidate before downstream submit guards."""

    if str(stage or "").strip().lower() != "entry":
        return False
    if str(action or "").strip().upper() in EXPOSURE_ACTIONS:
        return True
    return bool(
        response.get("entry_probe_intent") is True
        and response.get("entry_probe_intent_status")
        in {None, "", "eligible_wait_probe", "eligible_offline_probe"}
    )


def build_quality_baseline(
    *, target_date: str, labels: list[dict[str, Any]]
) -> dict[str, Any]:
    source_eligible = [
        row
        for row in labels
        if row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    ]
    primary_ineligible_count = sum(
        row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is not True
        for row in labels
    )
    eligible = [row for row in source_eligible if _primary_metric(row) is not None]
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    enriched = []
    taxonomy_counts = Counter()
    for row in eligible:
        errors = _taxonomy(row)
        taxonomy_counts.update(errors)
        preferred = _primary_metric(row) or {}
        outcome = _number(preferred.get("end_return_pct"))
        decision_value = _decision_value(row.get("action"), outcome)
        enriched_row = {
            "decision_trace_id": row.get("decision_trace_id"),
            "decision_stage": _stage(row.get("decision_stage")),
            "effective_venue": row.get("effective_venue"),
            "session_bucket": row.get("session_bucket"),
            "action": row.get("action"),
            "outcome_return_pct": outcome,
            "entry_path_first_hit": preferred.get("entry_path_first_hit"),
            "entry_path_target_pct": preferred.get("entry_path_target_pct"),
            "entry_path_adverse_pct": preferred.get("entry_path_adverse_pct"),
            "rising_missed_post_block_outcome": (row.get("stage_outcome") or {}).get(
                "rising_missed_post_block_outcome"
            ),
            "decision_value_pct": decision_value,
            "errors": errors,
        }
        enriched.append(enriched_row)
        buckets[
            (
                enriched_row["decision_stage"],
                str(enriched_row["effective_venue"] or "UNKNOWN"),
                str(enriched_row["session_bucket"] or "UNKNOWN"),
            )
        ].append(enriched_row)
    bucket_rows = []
    for (stage, venue, session), rows in sorted(buckets.items()):
        decision_values = [
            row["decision_value_pct"]
            for row in rows
            if row["decision_value_pct"] is not None
        ]
        bucket_rows.append(
            {
                "decision_stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "sample_count": len(rows),
                "source_quality_adjusted_ev_pct": (
                    fmean(decision_values) if decision_values else None
                ),
                "diagnostic_win_rate": (
                    sum(value > 0 for value in decision_values)
                    / len(decision_values)
                    * 100.0
                    if decision_values
                    else None
                ),
                "error_counts": dict(
                    Counter(error for row in rows for error in row["errors"])
                ),
            }
        )
    decision_values = [
        row["decision_value_pct"]
        for row in enriched
        if row["decision_value_pct"] is not None
    ]
    status = (
        "control_error_baseline_ready" if eligible else "partial_horizons_keep_maturing"
    )
    return {
        "schema": BASELINE_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "eligible_sample_count": len(eligible),
        "source_eligible_sample_count": len(source_eligible),
        "primary_horizon_pending_count": len(source_eligible) - len(eligible),
        "primary_cohort_ineligible_count": primary_ineligible_count,
        "source_quality_adjusted_ev_pct": (
            fmean(decision_values) if decision_values else None
        ),
        "diagnostic_win_rate": (
            sum(value > 0 for value in decision_values) / len(decision_values) * 100.0
            if decision_values
            else None
        ),
        "taxonomy_counts": dict(taxonomy_counts),
        "buckets": bucket_rows,
        "rows": enriched,
        **OFFLINE_CONTRACT,
    }


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for position in range(index, end):
            ranks[order[position]] = average_rank
        index = end
    return ranks


def _pearson(values_x: list[float], values_y: list[float]) -> float | None:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return None
    mean_x = fmean(values_x)
    mean_y = fmean(values_y)
    variance_x = sum((value - mean_x) ** 2 for value in values_x)
    variance_y = sum((value - mean_y) ** 2 for value in values_y)
    if variance_x <= 0 or variance_y <= 0:
        return None
    covariance = sum(
        (value_x - mean_x) * (value_y - mean_y)
        for value_x, value_y in zip(values_x, values_y)
    )
    return covariance / math.sqrt(variance_x * variance_y)


def _correlation_pair(
    values_x: list[float], values_y: list[float]
) -> dict[str, float | None]:
    return {
        "spearman": _pearson(_average_ranks(values_x), _average_ranks(values_y)),
        "pearson": _pearson(values_x, values_y),
    }


def build_score_outcome_correlation_report(
    *,
    target_date: str,
    labels: Iterable[dict[str, Any]],
    price_source_provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure exact-v2 AI score association with forward MFE and MAE."""

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    eligible_label_count = 0
    for row in labels:
        if (
            row.get("primary_cohort_eligible") is not True
            or row.get("source_quality_status") != "pass"
        ):
            continue
        score = _number(row.get("score"))
        metrics = row.get("horizon_metrics")
        if score is None or not isinstance(metrics, dict):
            continue
        eligible_label_count += 1
        for horizon in HORIZONS_MIN:
            metric = metrics.get(f"{horizon}m")
            if not isinstance(metric, dict):
                continue
            mfe = _number(metric.get("mfe_pct"))
            mae = _number(metric.get("mae_pct"))
            if mfe is None or mae is None:
                continue
            grouped[
                (
                    _stage(row.get("decision_stage")),
                    _venue(row.get("effective_venue")),
                    _session(row.get("session_bucket")),
                    f"{horizon}m",
                )
            ].append(
                {
                    "stock_code": _normalize_stock_code(row.get("stock_code")),
                    "score": score,
                    "mfe_pct": mfe,
                    "mae_pct": mae,
                }
            )
    buckets: list[dict[str, Any]] = []
    ready_bucket_count = 0
    grouped_items = sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2],
            int(item[0][3].removesuffix("m")),
        ),
    )
    for (stage, venue, session, horizon), rows in grouped_items:
        scores = [row["score"] for row in rows]
        mfe_values = [row["mfe_pct"] for row in rows]
        mae_values = [row["mae_pct"] for row in rows]
        adverse_magnitudes = [abs(min(0.0, value)) for value in mae_values]
        symbol_count = len({row["stock_code"] for row in rows})
        sample_floor_pass = len(rows) >= 30 and symbol_count >= 10
        if sample_floor_pass:
            ready_bucket_count += 1
        buckets.append(
            {
                "decision_stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "horizon": horizon,
                "sample_count": len(rows),
                "symbol_count": symbol_count,
                "distinct_score_count": len(set(scores)),
                "sample_floor_pass": sample_floor_pass,
                "inference_status": (
                    "exploratory_repeated_symbol_calls"
                    if sample_floor_pass
                    else "sample_floor_keep_collecting"
                ),
                "score_vs_mfe_pct": _correlation_pair(scores, mfe_values),
                "score_vs_mae_pct": _correlation_pair(scores, mae_values),
                "score_vs_adverse_magnitude_pct": _correlation_pair(
                    scores, adverse_magnitudes
                ),
                "interpretation_contract": {
                    "mfe_preferred_direction": "positive",
                    "mae_pct_preferred_direction": "positive_toward_zero",
                    "adverse_magnitude_preferred_direction": "negative",
                    "primary_coefficient": "spearman",
                    "pearson_role": "diagnostic_only",
                },
            }
        )
    return {
        "schema": SCORE_CORRELATION_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "exploratory_score_outcome_correlation_available"
            if ready_bucket_count
            else "sample_floor_keep_collecting"
        ),
        "eligible_label_count": eligible_label_count,
        "bucket_count": len(buckets),
        "sample_floor_ready_bucket_count": ready_bucket_count,
        "sample_floor": {
            "decision_rows": 30,
            "unique_symbols": 10,
            "significance_authority": False,
            "reason": "same_symbol_repeated_calls_are_not_independent",
        },
        "price_source_provenance": list(price_source_provenance or []),
        "buckets": buckets,
        **OFFLINE_CONTRACT,
    }


def _window_value(values: Any, horizon: int) -> float | None:
    if not isinstance(values, dict):
        return None
    return _number(values.get(str(horizon), values.get(horizon)))


def _entry_contract_facts(exact_payload: Any) -> dict[str, bool]:
    exact_payload_supplied = isinstance(exact_payload, dict)
    payload = exact_payload if isinstance(exact_payload, dict) else {}
    context = payload.get("entry_candle_context")
    context = context if isinstance(context, dict) else {}
    structure = context.get("structure")
    structure = structure if isinstance(structure, dict) else {}
    returns = structure.get("returns_pct")
    slopes = structure.get("slopes_pct_per_bar")
    structural_horizons = (5, 10, 20, 60)
    positive_return_count = sum(
        (_window_value(returns, horizon) or 0) > 0 for horizon in structural_horizons
    )
    positive_slope_count = sum(
        (_window_value(slopes, horizon) or 0) > 0 for horizon in structural_horizons
    )
    long_horizon_structural_edge_floor = bool(
        positive_return_count >= 3 and positive_slope_count >= 2
    )
    completed_bar_count = int(_number(context.get("completed_bar_count")) or 0)
    if completed_bar_count <= 0:
        completed_bar_count = sum(
            isinstance(row, dict) and not bool(row.get("forming", False))
            for row in context.get("bars") or []
        )
    early_horizons = (1, 3, 5, 10)
    available_early_returns = [
        value
        for horizon in early_horizons
        if (value := _window_value(returns, horizon)) is not None
    ]
    available_early_slopes = [
        value
        for horizon in early_horizons
        if (value := _window_value(slopes, horizon)) is not None
    ]
    regime = str(structure.get("regime") or "").lower()
    alignment = str(structure.get("alignment") or "").lower()
    peak_drawdown = _number(structure.get("peak_drawdown_pct"))
    high_direction = str(structure.get("high_direction") or "").lower()
    low_direction = str(structure.get("low_direction") or "").lower()
    volume_ratio = _number(structure.get("volume_ratio"))
    volume_alignment = str(structure.get("volume_direction_alignment") or "").lower()
    early_session_structural_edge_floor = bool(
        completed_bar_count >= 10
        and len(available_early_returns) >= 3
        and sum(value > 0 for value in available_early_returns) >= 3
        and not any(value <= -0.5 for value in available_early_returns)
        and len(available_early_slopes) >= 3
        and sum(value > 0 for value in available_early_slopes) >= 3
        and regime in {"breakout", "trend", "continuation"}
        and alignment == "positive"
        and high_direction in {"up", "up_or_flat"}
        and low_direction in {"up", "up_or_flat"}
        and peak_drawdown is not None
        and peak_drawdown > -1.5
        and volume_ratio is not None
        and volume_ratio >= 1.0
        and volume_alignment != "price_volume_divergence"
    )
    structural_edge_floor = bool(
        long_horizon_structural_edge_floor or early_session_structural_edge_floor
    )
    features = payload.get("features")
    features = features if isinstance(features, dict) else {}
    current = payload.get("current")
    current = current if isinstance(current, dict) else {}
    daily_runup = _number(current.get("fluctuation_pct"))
    micro_vwap_bp = _number(features.get("curr_vs_micro_vwap_bp"))
    ma5_bp = _number(features.get("curr_vs_ma5_bp"))
    tape_status = str(features.get("entry_order_flow_status") or "").lower()
    tape_source = str(features.get("order_flow_pressure_source") or "").lower()
    momentum_status = str(features.get("entry_momentum_status") or "").lower()
    tick_acceleration = _number(features.get("tick_acceleration_ratio"))
    buy_pressure = _number(features.get("buy_pressure_10t"))
    net_aggressive_delta = _number(features.get("net_aggressive_delta_10t"))
    trusted_tick_count = _number(features.get("tick_aggressor_trusted_count"))
    trusted_tape_usable = features.get("tick_aggressor_pressure_usable") is True
    quote_fresh = features.get("quote_fresh_for_entry") is True
    tick_fresh = features.get("tick_context_stale") is False
    large_sell_print_absent = features.get("large_sell_print_detected") is False
    tick_context_quality = str(features.get("tick_context_quality") or "").lower()
    tick_accel_source = str(features.get("tick_accel_source") or "").lower()
    thin_tape_sample = bool(
        (exact_payload_supplied and trusted_tick_count is None)
        or (trusted_tick_count is not None and trusted_tick_count < 10)
        or "insufficient_ticks" in tick_context_quality
        or tick_accel_source == "insufficient_ticks"
    )
    blocking_overextension = bool(
        structural_edge_floor
        and daily_runup is not None
        and daily_runup >= 15
        and micro_vwap_bp is not None
        and micro_vwap_bp >= 80
        and ma5_bp is not None
        and ma5_bp >= 80
        and tape_status != "supportive"
    )
    latest_recovery = (_window_value(returns, 1) or 0) > 0 or (
        _window_value(returns, 3) or 0
    ) > 0
    trusted_supportive_trigger = bool(
        structural_edge_floor
        and not blocking_overextension
        and latest_recovery
        and tape_status == "supportive"
        and tape_source == "trusted_aggressor"
        and momentum_status == "accelerating"
        and buy_pressure is not None
        and buy_pressure >= 60
        and net_aggressive_delta is not None
        and net_aggressive_delta > 0
        and trusted_tape_usable
        and trusted_tick_count is not None
        and trusted_tick_count >= 10
        and not thin_tape_sample
        and quote_fresh
        and tick_fresh
        and large_sell_print_absent
    )
    orderly_pullback_recovery = bool(
        structural_edge_floor
        and not blocking_overextension
        and micro_vwap_bp is not None
        and micro_vwap_bp < 0
        and ma5_bp is not None
        and ma5_bp < 0
        and tape_status in {"adverse", "mixed", "neutral", "unknown"}
        and latest_recovery
        and regime not in {"failed_breakout", "breakdown"}
        and alignment != "adverse"
    )
    return_3m = _window_value(returns, 3)
    return_5m = _window_value(returns, 5)
    return_10m = _window_value(returns, 10)
    return_20m = _window_value(returns, 20)
    bounded_reversal_probe_candidate = bool(
        not structural_edge_floor
        and not blocking_overextension
        and return_3m is not None
        and return_3m > 0
        and return_5m is not None
        and return_5m > 0
        and return_10m is not None
        and return_10m > 0
        and return_20m is not None
        and return_20m < 0
        and momentum_status == "accelerating"
        and tick_acceleration is not None
        and tick_acceleration >= 1.5
        and quote_fresh
        and tick_fresh
    )
    adverse_distribution_no_edge = bool(
        not structural_edge_floor
        and return_5m is not None
        and return_5m <= -0.5
        and return_10m is not None
        and return_10m <= -1.0
        and peak_drawdown is not None
        and peak_drawdown <= -2.0
        and high_direction == "down"
        and (
            (volume_ratio is not None and volume_ratio <= 0.5)
            or volume_alignment == "price_volume_divergence"
        )
    )
    spread_bp = _number(features.get("spread_bp"))
    top1_bid_notional = _number(features.get("top1_bid_notional"))
    top1_ask_notional = _number(features.get("top1_ask_notional"))
    ask_wall_wide_spread = bool(
        spread_bp is not None
        and spread_bp >= 50
        and top1_bid_notional is not None
        and top1_bid_notional > 0
        and top1_ask_notional is not None
        and top1_ask_notional / top1_bid_notional >= 5
    )
    early_short_structure = bool(
        3 <= completed_bar_count < 10
        and (_window_value(returns, 1) or 0) > 0
        and (_window_value(slopes, 1) or 0) > 0
        and (_window_value(slopes, 3) or 0) > 0
        and high_direction in {"up", "up_or_flat"}
        and low_direction in {"up", "up_or_flat"}
        and peak_drawdown is not None
        and peak_drawdown > -0.75
        and volume_ratio is not None
        and volume_ratio >= 1.2
        and volume_alignment != "price_volume_divergence"
    )
    early_session_probe_candidate = bool(
        (early_session_structural_edge_floor or early_short_structure)
        and not blocking_overextension
        and not ask_wall_wide_spread
        and daily_runup is not None
        and 0 <= daily_runup < 15.0
        and spread_bp is not None
        and 0 <= spread_bp <= 50.0
        and tape_status in {"supportive", "neutral", "mixed"}
        and buy_pressure is not None
        and buy_pressure >= 55.0
        and net_aggressive_delta is not None
        and net_aggressive_delta > 0
        and trusted_tape_usable
        and trusted_tick_count is not None
        and trusted_tick_count >= 10
        and not thin_tape_sample
        and quote_fresh
        and tick_fresh
        and large_sell_print_absent
    )
    return {
        "structural_edge_floor": structural_edge_floor,
        "long_horizon_structural_edge_floor": long_horizon_structural_edge_floor,
        "early_session_structural_edge_floor": early_session_structural_edge_floor,
        "early_session_probe_candidate": early_session_probe_candidate,
        "early_short_structure_floor": early_short_structure,
        "blocking_overextension": blocking_overextension,
        "orderly_pullback_recovery": orderly_pullback_recovery,
        "bounded_reversal_probe_candidate": bounded_reversal_probe_candidate,
        "trusted_supportive_trigger": trusted_supportive_trigger,
        "thin_tape_sample": thin_tape_sample,
        "adverse_distribution_no_edge": adverse_distribution_no_edge,
        "ask_wall_wide_spread": ask_wall_wide_spread,
    }


def build_exact_payload_analysis_v1(
    exact_payload: Any,
    *,
    stage: str,
    live_entry: bool = False,
) -> dict[str, Any]:
    """Build a deterministic, non-authoritative evidence ledger."""

    if live_entry and str(stage or "").strip().lower() != "entry":
        raise ValueError("live exact-payload analysis supports entry stage only")
    payload = exact_payload if isinstance(exact_payload, dict) else {}
    current = payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = payload.get("features")
    features = features if isinstance(features, dict) else {}
    candle = payload.get("entry_candle_context")
    candle = candle if isinstance(candle, dict) else {}
    structure = candle.get("structure")
    structure = structure if isinstance(structure, dict) else {}
    returns = structure.get("returns_pct")
    returns = returns if isinstance(returns, dict) else {}
    slopes = structure.get("slopes_pct_per_bar")
    slopes = slopes if isinstance(slopes, dict) else {}
    horizons = (1, 3, 5, 10, 20, 60)
    normalized_returns = {
        f"{horizon}m": _window_value(returns, horizon) for horizon in horizons
    }
    normalized_slopes = {
        f"{horizon}m": _window_value(slopes, horizon) for horizon in horizons
    }
    facts = _entry_contract_facts(payload) if str(stage).lower() == "entry" else {}
    completed_bar_count = _number(candle.get("completed_bar_count"))
    if completed_bar_count is None:
        completed_bar_count = float(
            sum(
                isinstance(row, dict) and not bool(row.get("forming", False))
                for row in candle.get("bars") or []
            )
        )
    forming_bar_count = sum(
        isinstance(row, dict) and bool(row.get("forming", False))
        for row in candle.get("bars") or []
    )
    current_price = _number(current.get("price"))
    trusted_tick_count = _number(features.get("tick_aggressor_trusted_count"))
    net_aggressive_delta = _number(features.get("net_aggressive_delta_10t"))
    tape_notional = (
        abs(net_aggressive_delta) * current_price
        if net_aggressive_delta is not None
        and current_price is not None
        and current_price > 0
        else None
    )
    tape_status = str(features.get("entry_order_flow_status") or "unknown").lower()
    tape_sample_sufficient = bool(
        trusted_tick_count is not None
        and trusted_tick_count >= 10
        and "insufficient_ticks"
        not in str(features.get("tick_context_quality") or "").lower()
        and str(features.get("tick_accel_source") or "").lower() != "insufficient_ticks"
    )
    spread_bp = _number(features.get("spread_bp"))
    top1_bid_notional = _number(features.get("top1_bid_notional"))
    top1_ask_notional = _number(features.get("top1_ask_notional"))
    top1_ask_to_bid_ratio = (
        top1_ask_notional / top1_bid_notional
        if top1_ask_notional is not None
        and top1_bid_notional is not None
        and top1_bid_notional > 0
        else None
    )
    top3_bid_notional = _number(features.get("top3_bid_notional"))
    top3_ask_notional = _number(features.get("top3_ask_notional"))
    top3_ask_to_bid_ratio = (
        top3_ask_notional / top3_bid_notional
        if top3_ask_notional is not None
        and top3_bid_notional is not None
        and top3_bid_notional > 0
        else None
    )
    would_fill_now = features.get("would_fill_now")
    if facts.get("ask_wall_wide_spread"):
        directional_depth_state = "blocking"
    elif top3_ask_to_bid_ratio is not None and top3_ask_to_bid_ratio >= 2.0:
        directional_depth_state = "adverse"
    elif (
        top3_ask_to_bid_ratio is not None
        and top3_ask_to_bid_ratio <= 1.0
        and (top1_ask_to_bid_ratio is None or top1_ask_to_bid_ratio <= 1.5)
    ):
        directional_depth_state = "supportive"
    elif (
        would_fill_now is True
        and top1_ask_to_bid_ratio is not None
        and top1_ask_to_bid_ratio <= 1.5
    ):
        directional_depth_state = "supportive"
    else:
        directional_depth_state = "mixed"
    if spread_bp is None:
        execution_cost_state = "insufficient"
    elif spread_bp <= 15:
        execution_cost_state = "low"
    elif spread_bp <= 50:
        execution_cost_state = "observable"
    elif spread_bp <= 150 and features.get("quote_fresh_for_entry") is True:
        execution_cost_state = "wide_but_observable"
    else:
        execution_cost_state = "extreme_or_unusable"
    if facts.get("ask_wall_wide_spread"):
        liquidity_state = "blocking"
    elif spread_bp is None:
        liquidity_state = "insufficient"
    elif execution_cost_state == "extreme_or_unusable":
        liquidity_state = "adverse"
    else:
        liquidity_state = directional_depth_state
    volume_ratio = _number(structure.get("volume_ratio"))
    volume_alignment = str(
        structure.get("volume_direction_alignment") or "unknown"
    ).lower()
    if volume_alignment == "price_volume_divergence" or (
        volume_ratio is not None and volume_ratio <= 0.5
    ):
        volume_state = "confirmation_absent"
    elif volume_ratio is not None and volume_ratio >= 1.0:
        volume_state = "confirmed"
    elif volume_ratio is None:
        volume_state = "insufficient"
    else:
        volume_state = "mixed"
    return_1m = normalized_returns["1m"]
    return_3m = normalized_returns["3m"]
    regime = str(structure.get("regime") or "").lower()
    peak_drawdown = _number(structure.get("peak_drawdown_pct"))
    return_5m = normalized_returns["5m"]
    return_10m = normalized_returns["10m"]
    positive_recovery_windows = sum(
        value is not None and value > 0 for value in (return_3m, return_5m, return_10m)
    )
    short_recovery = bool((return_1m or 0) > 0 or (return_3m or 0) > 0)
    deep_session_drawdown = bool(peak_drawdown is not None and peak_drawdown <= -2.0)
    if facts.get("adverse_distribution_no_edge") or regime == (
        "lower_high_distribution"
    ):
        structure_phase = "distribution"
        structural_edge = "absent"
    elif regime in {"failed_breakout", "breakdown"}:
        structure_phase = "failed_breakout"
        structural_edge = "moderate" if facts.get("structural_edge_floor") else "absent"
    elif regime == "downtrend_bounce":
        structure_phase = "rebound_attempt"
        structural_edge = "moderate" if facts.get("structural_edge_floor") else "weak"
    elif (
        deep_session_drawdown
        and facts.get("structural_edge_floor")
        and (positive_recovery_windows >= 2)
    ):
        structure_phase = "recovery_continuation"
        structural_edge = "moderate"
    elif deep_session_drawdown and short_recovery:
        structure_phase = "rebound_attempt"
        structural_edge = "weak"
    elif facts.get("early_short_structure_floor") and completed_bar_count < 10:
        structure_phase = "early_continuation_probe"
        structural_edge = "moderate"
    elif facts.get("structural_edge_floor") and (short_recovery):
        structure_phase = "continuation"
        structural_edge = "moderate"
    elif facts.get("structural_edge_floor"):
        structure_phase = "pullback"
        structural_edge = "moderate"
    elif (
        (normalized_returns["5m"] or 0) < 0
        and (normalized_returns["10m"] or 0) < 0
        and ((return_1m or 0) > 0 or (return_3m or 0) > 0)
    ):
        structure_phase = "rebound_attempt"
        structural_edge = "weak"
    else:
        structure_phase = "range_or_no_setup"
        structural_edge = "weak"
    contradictions: list[str] = []
    if tape_status == "supportive" and not tape_sample_sufficient:
        contradictions.append("supportive_tape_ratio_from_thin_sample")
    if tape_status == "supportive" and facts.get("adverse_distribution_no_edge"):
        contradictions.append("supportive_micro_tape_vs_adverse_distribution")
    if facts.get("structural_edge_floor") and liquidity_state == "blocking":
        contradictions.append("structural_edge_vs_blocking_liquidity")
    return_signs = {
        "positive" if value > 0 else "negative" if value < 0 else "flat"
        for value in normalized_returns.values()
        if value is not None
    }
    if "positive" in return_signs and "negative" in return_signs:
        contradictions.append("multi_horizon_direction_conflict")
    snapshot = payload.get("ai_market_snapshot_v1")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    sources = snapshot.get("sources")
    sources = sources if isinstance(sources, dict) else {}
    program = sources.get("program")
    program = program if isinstance(program, dict) else {}
    program_value = program.get("value")
    program_value = program_value if isinstance(program_value, dict) else {}
    program_net_qty = _number(program_value.get("net_qty"))
    if (
        tape_status == "supportive"
        and program_net_qty is not None
        and program_net_qty < 0
    ):
        contradictions.append("supportive_micro_tape_vs_program_net_sell")
    if facts.get("adverse_distribution_no_edge"):
        trigger_state = "failed"
    elif facts.get("trusted_supportive_trigger"):
        trigger_state = "confirmed"
    elif facts.get("orderly_pullback_recovery"):
        trigger_state = "recovery_required"
    elif facts.get("early_session_probe_candidate"):
        trigger_state = "recovery_required"
    elif not tape_sample_sufficient:
        trigger_state = "insufficient_tape_confirmation"
    else:
        trigger_state = "unconfirmed"
    source_quality = candle.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, dict) else {}
    analysis = {
        "schema": EXACT_PAYLOAD_ANALYSIS_SCHEMA,
        "stage": str(stage or "unknown"),
        "source_quality": {
            "status": source_quality.get("status"),
            "completed_bar_count": int(completed_bar_count),
            "forming_bar_count": forming_bar_count,
            "forming_bar_excluded": structure.get("forming_bar_excluded"),
            "risk_flags": list(candle.get("risk_flags") or []),
        },
        "completed_structure": {
            "phase": structure_phase,
            "phase_policy_version": STRUCTURE_PHASE_POLICY_VERSION,
            "phase_stable_on_completed_bar": True,
            "phase_input_policy": (
                "completed_candle_structure_only_intrabar_tape_quote_excluded"
            ),
            "structural_edge": structural_edge,
            "returns_pct": normalized_returns,
            "slopes_pct_per_bar": normalized_slopes,
            "peak_drawdown_pct": peak_drawdown,
            "rolling_20m_peak_drawdown_pct": _number(
                structure.get("rolling_20m_peak_drawdown_pct")
            ),
            "rolling_20m_low_rebound_pct": _number(
                structure.get("rolling_20m_low_rebound_pct")
            ),
            "bars_since_session_high": structure.get("bars_since_session_high"),
            "bars_since_session_low": structure.get("bars_since_session_low"),
            "bars_since_20m_high": structure.get("bars_since_20m_high"),
            "bars_since_20m_low": structure.get("bars_since_20m_low"),
            "high_direction": structure.get("high_direction"),
            "low_direction": structure.get("low_direction"),
            "regime": structure.get("regime"),
            "alignment": structure.get("alignment"),
            "structural_edge_policy_version": ("session_available_horizons_v2"),
            "structural_edge_floor": facts.get("structural_edge_floor"),
            "long_horizon_structural_edge_floor": facts.get(
                "long_horizon_structural_edge_floor"
            ),
            "early_session_structural_edge_floor": facts.get(
                "early_session_structural_edge_floor"
            ),
            "early_short_structure_floor": facts.get("early_short_structure_floor"),
            "adverse_distribution_no_edge": facts.get("adverse_distribution_no_edge"),
            "early_session_probe_candidate": facts.get("early_session_probe_candidate"),
        },
        "volume_confirmation": {
            "state": volume_state,
            "volume_ratio": volume_ratio,
            "alignment": volume_alignment,
        },
        "tape_sample": {
            "state": "sufficient" if tape_sample_sufficient else "too_thin",
            "raw_status": tape_status,
            "trusted_tick_count": trusted_tick_count,
            "buy_pressure_pct": _number(features.get("buy_pressure_10t")),
            "net_aggressive_delta_shares": net_aggressive_delta,
            "net_aggressive_notional_krw": tape_notional,
            "tick_context_quality": features.get("tick_context_quality"),
            "tick_accel_source": features.get("tick_accel_source"),
        },
        "executable_liquidity": {
            "state": liquidity_state,
            "directional_depth_state": directional_depth_state,
            "execution_cost_state": execution_cost_state,
            "spread_bp": spread_bp,
            "top1_bid_notional": top1_bid_notional,
            "top1_ask_notional": top1_ask_notional,
            "top1_ask_to_bid_ratio": top1_ask_to_bid_ratio,
            "top3_bid_notional": top3_bid_notional,
            "top3_ask_notional": top3_ask_notional,
            "top3_ask_to_bid_ratio": top3_ask_to_bid_ratio,
            "fillability_score": _number(features.get("fillability_score")),
            "would_fill_now": would_fill_now,
        },
        "program_flow": {
            "net_qty": program_net_qty,
            "source": program.get("source"),
        },
        "trigger_state": trigger_state,
        "contradictions": contradictions,
        "deterministic_contract_facts": facts,
        "observation_contract": {
            "metric_role": "ai_input_feature_analysis",
            "decision_authority": (
                "operator_directed_live_entry_prompt_input"
                if live_entry
                else "offline_replay_evidence_organization_only"
            ),
            "window_policy": "same_exact_payload_completed_bar_snapshot",
            "sample_floor": "one_exact_payload_with_completed_bar",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "exact_payload_fresh_same_route",
            "runtime_effect": live_entry,
            "allowed_runtime_apply": live_entry,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": (
                (
                    "direct_order_submission|provider_change|"
                    "threshold_price_quantity_change|broker_guard_bypass|"
                    "safety_guard_bypass"
                )
                if live_entry
                else (
                    "standalone_live_action|runtime_prompt_promotion|"
                    "provider_change|threshold_price_quantity_change|"
                    "broker_guard_bypass|bot_restart"
                )
            ),
        },
    }
    analysis["analysis_sha256"] = _sha256(analysis)
    return analysis


def build_anticipatory_reversal_analysis_v1(
    exact_payload: Any,
    *,
    stage: str,
) -> dict[str, Any]:
    """Build an offline-only early-reversal and execution-risk ledger."""

    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage != "entry":
        raise ValueError("anticipatory reversal analysis supports entry only")
    payload = exact_payload if isinstance(exact_payload, dict) else {}
    current = payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = payload.get("features")
    features = features if isinstance(features, dict) else {}
    candle = payload.get("entry_candle_context")
    candle = candle if isinstance(candle, dict) else {}
    structure = candle.get("structure")
    structure = structure if isinstance(structure, dict) else {}
    source_quality = candle.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, dict) else {}
    decision_window = source_quality.get("decision_window")
    decision_window = decision_window if isinstance(decision_window, dict) else {}
    facts = _entry_contract_facts(payload)

    returns = structure.get("returns_pct")
    returns = returns if isinstance(returns, dict) else {}
    return_1m = _window_value(returns, 1)
    return_3m = _window_value(returns, 3)
    return_5m = _window_value(returns, 5)
    return_10m = _window_value(returns, 10)
    peak_drawdown = _number(structure.get("peak_drawdown_pct"))

    completed_bar_count = int(
        _number(
            decision_window.get("completed_bar_count")
            if decision_window.get("completed_bar_count") is not None
            else candle.get("completed_bar_count")
        )
        or 0
    )
    candle_fresh = bool(
        str(source_quality.get("status") or "") == "fresh_consistent"
        and str(decision_window.get("status") or "") == "fresh_consistent"
        and decision_window.get("provider_call_allowed") is not False
        and completed_bar_count >= 1
    )
    quote_age_ms = _number(features.get("quote_age_ms"))
    tick_age_ms = _number(features.get("tick_latest_age_ms"))
    quote_fresh = bool(
        features.get("quote_fresh_for_entry") is True
        and features.get("quote_stale") is not True
        and quote_age_ms is not None
        and quote_age_ms <= 5_000
    )
    tick_fresh = bool(
        features.get("tick_context_stale") is False
        and tick_age_ms is not None
        and tick_age_ms <= 5_000
    )
    if candle_fresh and quote_fresh and tick_fresh:
        source_mode = "fresh_dual"
    elif candle_fresh and quote_fresh:
        source_mode = "degraded_but_bounded"
    else:
        source_mode = "unusable"

    spread_bp = _number(features.get("spread_bp"))
    quote_depth_present = features.get("quote_depth_present") is True
    if spread_bp is None or spread_bp < 0:
        spread_regime = "unavailable"
    elif spread_bp <= 50:
        spread_regime = "normal"
    elif spread_bp <= 150 and quote_fresh and quote_depth_present:
        spread_regime = "wide_but_observable"
    else:
        spread_regime = "extreme_or_unusable"

    half_spread_cost_pct = spread_bp / 200.0 if spread_bp is not None else None
    quote_latency_cost_pct = (
        min(0.20, max(0.0, quote_age_ms - 1_000) / 1_000 * 0.02)
        if quote_age_ms is not None
        else 0.20
    )
    tick_latency_cost_pct = (
        min(0.15, max(0.0, tick_age_ms - 2_000) / 1_000 * 0.01)
        if tick_age_ms is not None
        else 0.15
    )
    latency_risk_cost_pct = round(quote_latency_cost_pct + tick_latency_cost_pct, 6)
    conservative_execution_cost_pct = (
        round(half_spread_cost_pct + latency_risk_cost_pct, 6)
        if half_spread_cost_pct is not None
        else None
    )

    buy_pressure = _number(features.get("buy_pressure_10t"))
    net_delta = _number(features.get("net_aggressive_delta_10t"))
    absorption_count = int(_number(features.get("same_price_buy_absorption")) or 0)
    large_sell_absent = features.get("large_sell_print_detected") is False
    micro_absorption = bool(
        absorption_count >= 1
        or (
            buy_pressure is not None
            and buy_pressure >= 55
            and net_delta is not None
            and net_delta > 0
            and large_sell_absent
        )
    )
    prior_minute_pace = [
        value
        for value in (
            return_3m / 3.0 if return_3m is not None else None,
            return_5m / 5.0 if return_5m is not None else None,
        )
        if value is not None
    ]
    sell_momentum_decelerating = bool(
        return_1m is not None
        and prior_minute_pace
        and any(return_1m > pace + 0.05 for pace in prior_minute_pace)
        and any(pace < 0 for pace in prior_minute_pace)
    )
    lower_wick_ratio = _number(structure.get("latest_lower_wick_ratio"))
    low_rebound_pct = _number(structure.get("low_rebound_pct"))
    price_rejection = bool(
        (lower_wick_ratio is not None and lower_wick_ratio >= 0.35)
        or (
            str(structure.get("low_direction") or "").lower() == "up_or_flat"
            and low_rebound_pct is not None
            and low_rebound_pct >= 0.5
        )
    )
    micro_vwap_bp = _number(features.get("curr_vs_micro_vwap_bp"))
    ma5_bp = _number(features.get("curr_vs_ma5_bp"))
    price_change_10t_pct = _number(features.get("price_change_10t_pct"))
    near_reference_reclaim = bool(
        (
            micro_vwap_bp is not None
            and micro_vwap_bp >= -50
            or ma5_bp is not None
            and ma5_bp >= -50
        )
        and price_change_10t_pct is not None
        and price_change_10t_pct > 0
    )
    tick_acceleration = _number(features.get("tick_acceleration_ratio"))
    trusted_tick_count = _number(features.get("tick_aggressor_trusted_count"))
    trusted_tape_acceleration = bool(
        tick_fresh
        and trusted_tick_count is not None
        and trusted_tick_count >= 10
        and (
            (
                str(features.get("entry_order_flow_status") or "").lower()
                == "supportive"
                and net_delta is not None
                and net_delta > 0
            )
            or (tick_acceleration is not None and tick_acceleration >= 1.0)
        )
    )
    precursor_flags = {
        "micro_absorption": micro_absorption,
        "sell_momentum_decelerating": sell_momentum_decelerating,
        "price_rejection": price_rejection,
        "near_reference_reclaim": near_reference_reclaim,
        "trusted_tape_acceleration": trusted_tape_acceleration,
    }
    precursor_count = sum(precursor_flags.values())
    non_tape_precursor_count = sum(
        value
        for key, value in precursor_flags.items()
        if key != "trusted_tape_acceleration"
    )
    prior_adverse_structure = bool(
        (return_5m is not None and return_5m < 0)
        or (return_10m is not None and return_10m < 0)
        or (peak_drawdown is not None and peak_drawdown <= -1.0)
    )
    failed_structure = str(structure.get("regime") or "").lower() in {
        "failed_breakout",
        "breakdown",
    }
    hard_blockers = [
        reason
        for reason, blocked in (
            ("source_unusable", source_mode == "unusable"),
            (
                "spread_extreme_or_unusable",
                spread_regime in {"unavailable", "extreme_or_unusable"},
            ),
            ("blocking_overextension", facts["blocking_overextension"]),
            ("failed_structure", failed_structure),
            (
                "large_sell_print_present",
                features.get("large_sell_print_detected") is True,
            ),
        )
        if blocked
    ]
    required_precursor_count = 3 if source_mode == "fresh_dual" else 4
    eligible = bool(
        prior_adverse_structure
        and precursor_count >= required_precursor_count
        and non_tape_precursor_count >= 3
        and micro_absorption
        and not hard_blockers
        and conservative_execution_cost_pct is not None
    )
    bounded_edge_facts = {
        "anticipatory_reversal": eligible,
        "structural_edge_floor": bool(facts["structural_edge_floor"]),
        "early_session_probe_candidate": bool(facts["early_session_probe_candidate"]),
        "orderly_pullback_recovery": bool(facts["orderly_pullback_recovery"]),
        "trusted_supportive_trigger": bool(facts["trusted_supportive_trigger"]),
    }
    bounded_opportunity_eligible = bool(
        any(bounded_edge_facts.values())
        and not hard_blockers
        and source_mode in {"fresh_dual", "degraded_but_bounded"}
        and spread_regime in {"normal", "wide_but_observable"}
        and conservative_execution_cost_pct is not None
    )
    clean_continuation_eligible = bool(
        source_mode == "fresh_dual"
        and spread_regime == "normal"
        and not hard_blockers
        and facts["structural_edge_floor"]
        and return_3m is not None
        and return_3m > 0
        and return_5m is not None
        and return_5m > 0
        and return_10m is not None
        and return_10m > 0
        and peak_drawdown is not None
        and peak_drawdown > -0.5
        and near_reference_reclaim
        and precursor_count >= 2
        and conservative_execution_cost_pct is not None
        and conservative_execution_cost_pct <= 0.25
    )
    analysis = {
        "schema": ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA,
        "stage": normalized_stage,
        "source_mode": source_mode,
        "freshness": {
            "candle_fresh": candle_fresh,
            "completed_bar_count": completed_bar_count,
            "quote_fresh": quote_fresh,
            "quote_age_ms": quote_age_ms,
            "tick_fresh": tick_fresh,
            "tick_age_ms": tick_age_ms,
            "degraded_source_policy": (
                "fresh_completed_candles_and_quote_plus_non_tape_precursors"
            ),
        },
        "spread": {
            "regime": spread_regime,
            "spread_bp": spread_bp,
            "quote_depth_present": quote_depth_present,
            "wide_spread_erases_alpha_edge": False,
            "extreme_or_stale_spread_blocks_probe": True,
        },
        "execution_cost": {
            "half_spread_cost_pct": (
                round(half_spread_cost_pct, 6)
                if half_spread_cost_pct is not None
                else None
            ),
            "latency_risk_cost_pct": latency_risk_cost_pct,
            "conservative_execution_cost_pct": conservative_execution_cost_pct,
            "cost_basis": "half_spread_plus_bounded_source_age_penalty",
            "fill_assumption": "counterfactual_only_no_fill_claim",
        },
        "precursors": {
            **precursor_flags,
            "independent_precursor_count": precursor_count,
            "non_tape_precursor_count": non_tape_precursor_count,
            "required_precursor_count": required_precursor_count,
            "prior_adverse_structure": prior_adverse_structure,
            "return_1m_pct": return_1m,
            "return_3m_pct": return_3m,
            "return_5m_pct": return_5m,
            "return_10m_pct": return_10m,
            "peak_drawdown_pct": peak_drawdown,
        },
        "hard_blockers": hard_blockers,
        "eligible_for_counterfactual_probe": eligible,
        "execution_policy": (
            "passive_probe_required" if eligible else "no_counterfactual_exposure"
        ),
        "bounded_opportunity": {
            "eligible_for_one_share_probe": bounded_opportunity_eligible,
            "qualifying_edge_facts": bounded_edge_facts,
            "execution_policy": (
                "passive_probe_required"
                if bounded_opportunity_eligible
                else "no_counterfactual_exposure"
            ),
            "accepted_adverse_risk": ["low", "moderate", "high"],
            "blocking_risk_allowed": False,
            "after_cost_reward_risk_floor": 1.0,
            "downstream_submit_guards_required": True,
            "runtime_effect": False,
        },
        "clean_continuation_probe": {
            "eligible": clean_continuation_eligible,
            "execution_policy": (
                "passive_probe_required"
                if clean_continuation_eligible
                else "no_counterfactual_exposure"
            ),
            "required_source_mode": "fresh_dual",
            "required_spread_regime": "normal",
            "hard_blockers_allowed": False,
            "required_completed_return_windows_min": [3, 5, 10],
            "minimum_independent_precursors": 2,
            "minimum_peak_drawdown_pct_exclusive": -0.5,
            "maximum_execution_cost_pct": 0.25,
            "after_cost_reward_risk_floor": 0.75,
            "downstream_submit_guards_required": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "confidence_cap": 60 if source_mode == "degraded_but_bounded" else 75,
        "learning_contract": {
            "update_floor_rows": ANTICIPATORY_LEARNING_MIN_ROWS,
            "update_floor_unique_symbols": ANTICIPATORY_LEARNING_MIN_SYMBOLS,
            "update_policy": "append_daily_then_recompute_cumulative",
            "single_sample_role": "start_or_update_observation_only",
            "promotion_authority": False,
        },
        "observation_contract": {
            "metric_role": "ai_anticipatory_reversal_quality_observation",
            "decision_authority": "offline_counterfactual_passive_probe_only",
            "window_policy": "same_exact_payload_completed_bar_snapshot",
            "sample_floor": "one_eligible_exact_row_starts_cumulative_learning",
            "primary_decision_metric": ("candidate_execution_cost_adjusted_ev_pct"),
            "source_quality_gate": (
                "fresh_completed_candle_and_fresh_quote_with_bounded_degradation"
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": [
                "single_sample_live_promotion",
                "real_order_or_fill_claim",
                "stale_or_extreme_spread_guard_bypass",
                "provider_model_threshold_price_quantity_or_cap_change",
                "bot_restart",
            ],
        },
    }
    analysis["analysis_sha256"] = _sha256(analysis)
    return analysis


def _attach_selective_recovery_probe_contract_v1(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """Attach the V2.12-only recovery contract without mutating older inputs."""

    enriched = dict(analysis)
    bounded = analysis.get("bounded_opportunity")
    bounded = bounded if isinstance(bounded, dict) else {}
    edge_facts = bounded.get("qualifying_edge_facts")
    edge_facts = edge_facts if isinstance(edge_facts, dict) else {}
    precursors = analysis.get("precursors")
    precursors = precursors if isinstance(precursors, dict) else {}
    spread = analysis.get("spread")
    spread = spread if isinstance(spread, dict) else {}
    execution_cost = analysis.get("execution_cost")
    execution_cost = execution_cost if isinstance(execution_cost, dict) else {}
    conservative_cost_pct = _number(
        execution_cost.get("conservative_execution_cost_pct")
    )
    peak_drawdown_pct = _number(precursors.get("peak_drawdown_pct"))
    non_tape_precursor_count = int(
        _number(precursors.get("non_tape_precursor_count")) or 0
    )
    eligible = bool(
        analysis.get("source_mode") == "fresh_dual"
        and spread.get("regime") == "normal"
        and not analysis.get("hard_blockers")
        and bounded.get("eligible_for_one_share_probe") is True
        and edge_facts.get("structural_edge_floor") is True
        and edge_facts.get("anticipatory_reversal") is True
        and conservative_cost_pct is not None
        and conservative_cost_pct <= 0.25
        and peak_drawdown_pct is not None
        and peak_drawdown_pct > -2.0
        and precursors.get("near_reference_reclaim") is True
        and non_tape_precursor_count >= 3
    )
    enriched["selective_recovery_probe"] = {
        "eligible": eligible,
        "execution_policy": (
            "passive_probe_required" if eligible else "no_counterfactual_exposure"
        ),
        "required_source_mode": "fresh_dual",
        "required_spread_regime": "normal",
        "hard_blockers_allowed": False,
        "structural_edge_required": True,
        "bounded_anticipatory_reversal_required": True,
        "maximum_execution_cost_pct": 0.25,
        "minimum_peak_drawdown_pct_exclusive": -2.0,
        "near_reference_reclaim_required": True,
        "minimum_non_tape_precursors": 3,
        "after_cost_reward_risk_floor": 1.0,
        "downstream_submit_guards_required": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    enriched.pop("analysis_sha256", None)
    enriched["analysis_sha256"] = _sha256(enriched)
    return enriched


def _attach_recovery_confirmation_probe_contract_v1(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """Attach the V2.13-only pre-outcome recovery confirmation contract."""

    enriched = dict(analysis)
    selective = analysis.get("selective_recovery_probe")
    selective = selective if isinstance(selective, dict) else {}
    precursors = analysis.get("precursors")
    precursors = precursors if isinstance(precursors, dict) else {}
    bounded = analysis.get("bounded_opportunity")
    bounded = bounded if isinstance(bounded, dict) else {}
    edge_facts = bounded.get("qualifying_edge_facts")
    edge_facts = edge_facts if isinstance(edge_facts, dict) else {}
    eligible = bool(
        selective.get("eligible") is True
        and precursors.get("sell_momentum_decelerating") is True
        and edge_facts.get("trusted_supportive_trigger") is True
    )
    enriched["recovery_confirmation_probe"] = {
        "eligible": eligible,
        "execution_policy": (
            "passive_probe_required" if eligible else "no_counterfactual_exposure"
        ),
        "selective_recovery_contract_required": True,
        "sell_momentum_decelerating_required": True,
        "trusted_supportive_trigger_required": True,
        "price_rejection_only_insufficient": True,
        "after_cost_reward_risk_floor": 0.75,
        "strictly_negative_downside_required": True,
        "downstream_submit_guards_required": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    enriched.pop("analysis_sha256", None)
    enriched["analysis_sha256"] = _sha256(enriched)
    return enriched


def build_v2_13_recovery_confirmation_analysis_v1(
    exact_payload: Any,
    *,
    stage: str = "entry",
) -> dict[str, Any]:
    """Build the shared offline/live V2.13 pre-outcome analysis contract."""

    analysis = build_anticipatory_reversal_analysis_v1(
        exact_payload,
        stage=stage,
    )
    analysis = _attach_selective_recovery_probe_contract_v1(analysis)
    return _attach_recovery_confirmation_probe_contract_v1(analysis)


def validate_v2_13_recovery_confirmation_response(
    *,
    exact_payload: Any,
    analysis: dict[str, Any],
    response: dict[str, Any],
) -> list[str]:
    """Validate one V2.13 response without granting order authority."""

    request = {
        "stage": "entry",
        "exact_payload": exact_payload,
        "anticipatory_reversal_analysis": analysis,
        "candidate": {
            "prompt_version": (
                f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
            ),
            "semantic_validator_version": (
                BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
            ),
            "semantic_repair_version": BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION,
        },
    }
    return validate_replay_candidate_response(request, response)


def repair_v2_13_recovery_confirmation_response(
    *,
    exact_payload: Any,
    analysis: dict[str, Any],
    response: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Apply the deterministic V2.13 adapter and return remaining errors."""

    request = {
        "stage": "entry",
        "exact_payload": exact_payload,
        "anticipatory_reversal_analysis": analysis,
        "candidate": {
            "prompt_version": (
                f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
            ),
            "semantic_validator_version": (
                BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
            ),
            "semantic_repair_version": BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION,
        },
    }
    repaired, repairs = repair_bounded_opportunity_candidate_response(
        request,
        response,
    )
    return (
        repaired,
        repairs,
        validate_replay_candidate_response(request, repaired),
    )


def _holding_contract_facts(exact_payload: Any) -> dict[str, Any]:
    exact_text = exact_payload if isinstance(exact_payload, str) else ""
    marked_holding = (
        _extract_holding_context_from_exact_payload(exact_payload)
        if isinstance(exact_payload, str)
        else {}
    )
    if marked_holding:
        exact_payload = {"holding_decision_context": marked_holding}
    holding = (
        exact_payload.get("holding_decision_context")
        if isinstance(exact_payload, dict)
        else {}
    )
    holding = holding if isinstance(holding, dict) else {}
    position = (
        exact_payload.get("position_context") if isinstance(exact_payload, dict) else {}
    )
    position = position if isinstance(position, dict) else {}
    execution = holding.get("execution_pnl")
    execution = execution if isinstance(execution, dict) else {}
    lifecycle = holding.get("position_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
    source_quality = holding.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, dict) else {}
    candle = holding.get("candle")
    candle = candle if isinstance(candle, dict) else {}
    bars = candle.get("bars")
    bars = bars if isinstance(bars, list) else []
    order_reconciliation = holding.get("order_reconciliation")
    order_reconciliation = (
        order_reconciliation if isinstance(order_reconciliation, dict) else {}
    )

    def marked_scalar(name: str) -> str:
        if not exact_text:
            return ""
        match = re.search(
            rf"(?m)^\s*-\s*{re.escape(name)}\s*:\s*([^\r\n]+)$",
            exact_text,
        )
        return str(match.group(1)).strip() if match else ""

    candidate_exit_rule = marked_scalar("candidate_exit_rule").lower()
    allowed_worsen_pct = _number(marked_scalar("allowed_worsen_pct"))
    remaining_qty = _number(
        execution.get("remaining_qty")
        if execution.get("remaining_qty") is not None
        else (
            lifecycle.get("memory_qty")
            if lifecycle.get("memory_qty") is not None
            else position.get("buy_qty")
        )
    )
    average_entry_price = _number(
        execution.get("average_entry_price")
        if execution.get("average_entry_price") is not None
        else (
            lifecycle.get("average_entry_price")
            if lifecycle.get("average_entry_price") is not None
            else position.get("buy_price")
        )
    )
    executable_sell_price = _number(execution.get("executable_sell_price"))
    position_observed = (
        remaining_qty is not None
        and remaining_qty > 0
        and average_entry_price is not None
        and average_entry_price > 0
        and executable_sell_price is not None
        and executable_sell_price > 0
        and source_quality.get("position_valid") is True
        and source_quality.get("order_consistent") is True
    )
    completed_bar_count = int(_number(candle.get("completed_bar_count")) or 0)
    completed_bars_observed = completed_bar_count > 0 and any(
        isinstance(bar, dict) and not bool(bar.get("is_forming", False)) for bar in bars
    )
    fresh_consistent_core = (
        position_observed
        and completed_bars_observed
        and str(source_quality.get("status") or "") == "fresh_consistent"
        and str(source_quality.get("candle_status") or "") == "fresh_consistent"
        and source_quality.get("bbo_fresh") is True
    )
    hard_exit_guard_observed = any(
        token in candidate_exit_rule
        for token in ("hard", "protect", "emergency", "mandatory")
    )
    soft_exit_candidate = "soft" in candidate_exit_rule
    open_sell_qty = _number(order_reconciliation.get("open_sell_qty"))
    sell_order_or_exit_token_active = bool(
        (open_sell_qty is not None and open_sell_qty > 0)
        or order_reconciliation.get("cancel_pending") is True
        or order_reconciliation.get("exit_token_active") is True
        or order_reconciliation.get("order_or_quantity_conflict") is True
    )
    bounded_defer_eligible = bool(
        fresh_consistent_core
        and soft_exit_candidate
        and not hard_exit_guard_observed
        and not sell_order_or_exit_token_active
        and allowed_worsen_pct is not None
        and allowed_worsen_pct > 0
    )
    return {
        "schema": "holding_exact_contract_facts_v1",
        "position_observed": position_observed,
        "remaining_qty": remaining_qty,
        "average_entry_price": average_entry_price,
        "executable_sell_price": executable_sell_price,
        "position_valid": source_quality.get("position_valid"),
        "order_consistent": source_quality.get("order_consistent"),
        "position_reconciled": source_quality.get("position_reconciled"),
        "completed_bar_count": completed_bar_count,
        "completed_bars_observed": completed_bars_observed,
        "source_quality_status": source_quality.get("status"),
        "candle_status": source_quality.get("candle_status"),
        "bbo_fresh": source_quality.get("bbo_fresh"),
        "fresh_consistent_core": fresh_consistent_core,
        "trim_available": remaining_qty is not None and remaining_qty >= 2,
        "candidate_exit_rule": candidate_exit_rule or None,
        "allowed_worsen_pct": allowed_worsen_pct,
        "hard_exit_guard_observed": hard_exit_guard_observed,
        "soft_exit_candidate": soft_exit_candidate,
        "open_sell_qty": open_sell_qty,
        "sell_order_or_exit_token_active": sell_order_or_exit_token_active,
        "bounded_defer_eligible": bounded_defer_eligible,
        "bounded_defer_checkpoint_horizons_sec": [30, 60, 90],
        "bounded_defer_authority": "offline_observation_only_no_exit_delay",
    }


def validate_candidate_response(
    response: dict[str, Any],
    *,
    stage: str,
    exact_payload: Any = None,
    enforce_live_probe_contract: bool = False,
) -> list[str]:
    errors: list[str] = []
    normalized_stage = str(stage or "").strip().lower()
    if response.get("edge_state") not in {
        "EDGE",
        "NO_EDGE",
        "INSUFFICIENT_DATA",
    }:
        errors.append("edge_state_invalid")
    action = str(response.get("action") or "").strip().upper()
    if not action:
        errors.append("action_missing")
    elif action not in STAGE_ACTIONS.get(normalized_stage, set()):
        errors.append("action_invalid_for_stage")
    expected_values: dict[str, float | None] = {}
    for field in ("expected_upside_pct", "expected_downside_pct"):
        if field not in response:
            errors.append(f"{field}_missing")
            expected_values[field] = None
        elif response.get(field) is None:
            expected_values[field] = None
        else:
            expected_values[field] = _number(response.get(field))
            if expected_values[field] is None:
                errors.append(f"{field}_invalid")
    edge_state = str(response.get("edge_state") or "")
    if edge_state in {"EDGE", "NO_EDGE"} and any(
        expected_values.get(field) is None
        for field in ("expected_upside_pct", "expected_downside_pct")
    ):
        errors.append("expected_edge_values_required")
    if edge_state == "INSUFFICIENT_DATA" and any(
        response.get(field) is not None
        for field in ("expected_upside_pct", "expected_downside_pct")
    ):
        errors.append("insufficient_data_expected_values_must_be_null")
    upside = expected_values.get("expected_upside_pct")
    downside = expected_values.get("expected_downside_pct")
    if upside is not None and upside < 0:
        errors.append("expected_upside_pct_negative")
    if downside is not None and downside > 0:
        errors.append("expected_downside_pct_positive")
    confidence = _number(response.get("confidence"))
    if confidence is None or not 0 <= confidence <= 100:
        errors.append("confidence_invalid")
    codes = response.get("reason_codes")
    reason_code_set = set(map(str, codes)) if isinstance(codes, list) else set()
    if (
        not isinstance(codes, list)
        or not codes
        or len(codes) != len(set(map(str, codes)))
        or any(
            not REASON_CODE_PATTERN.fullmatch(str(code))
            or str(code) not in DECISION_QUALITY_V2_REASON_CODES
            for code in codes
        )
    ):
        errors.append("reason_codes_invalid")
    elif any(
        len(set(map(str, codes)) & group) > 1
        for group in MUTUALLY_EXCLUSIVE_REASON_CODE_GROUPS
    ):
        errors.append("reason_codes_conflict")
    evidence = response.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence_missing")
    else:
        for key in REASON_EVIDENCE_KEYS:
            value = str(evidence.get(key) or "").strip().lower()
            if not value:
                errors.append(f"evidence_{key}_missing")
            elif value not in EVIDENCE_VALUES[key]:
                errors.append(f"evidence_{key}_invalid")
        if normalized_stage == "entry":
            positive_edge = str(evidence.get("positive_edge") or "").lower()
            adverse_risk = str(evidence.get("adverse_risk") or "").lower()
            trigger = str(evidence.get("trigger") or "").lower()
            setup = str(evidence.get("setup") or "").lower()
            trigger_reason_requirements = {
                "recovery_trigger_confirmed": "confirmed",
                "recovery_trigger_required": "recovery_required",
                "recovery_trigger_failed": "failed",
            }
            if any(
                reason_code in reason_code_set and trigger != required_trigger
                for reason_code, required_trigger in trigger_reason_requirements.items()
            ) or (
                "structural_edge_without_trigger" in reason_code_set
                and trigger == "confirmed"
            ):
                errors.append("entry_trigger_reason_evidence_conflict")
            if edge_state == "INSUFFICIENT_DATA":
                if action != "WAIT":
                    errors.append("entry_insufficient_requires_wait")
                if (
                    positive_edge != "insufficient"
                    or adverse_risk != "insufficient"
                    or trigger != "insufficient"
                    or setup != "insufficient"
                ):
                    errors.append("entry_insufficient_evidence_invalid")
            elif edge_state == "NO_EDGE":
                if action != "DROP":
                    errors.append("entry_no_edge_requires_drop")
                if positive_edge not in {"none", "weak"}:
                    errors.append("entry_no_edge_strength_invalid")
                if setup not in {"no_setup", "not_applicable"}:
                    errors.append("entry_no_edge_setup_invalid")
            elif edge_state == "EDGE":
                if positive_edge not in {"moderate", "strong"}:
                    errors.append("entry_edge_strength_invalid")
                if action == "BUY":
                    if trigger != "confirmed":
                        errors.append("entry_buy_requires_confirmed_trigger")
                    if adverse_risk not in {"low", "moderate"}:
                        errors.append("entry_buy_adverse_risk_too_high")
                    if (
                        upside is not None
                        and downside is not None
                        and (downside >= 0 or upside / abs(downside) < 1.25)
                    ):
                        errors.append("entry_buy_reward_risk_below_floor")
                elif action == "WAIT":
                    if trigger != "recovery_required":
                        errors.append("entry_wait_requires_recovery_trigger")
                    if adverse_risk == "insufficient":
                        errors.append("entry_wait_adverse_risk_invalid")
                elif action == "DROP":
                    reward_risk_unfavorable = (
                        upside is not None
                        and downside is not None
                        and downside < 0
                        and upside / abs(downside) < 1.25
                    )
                    if not (
                        trigger == "failed"
                        or adverse_risk == "blocking"
                        or reward_risk_unfavorable
                    ):
                        errors.append(
                            "entry_edge_drop_requires_failed_blocking_or_unfavorable"
                        )
            contract_facts = _entry_contract_facts(exact_payload)
            if contract_facts["structural_edge_floor"]:
                if edge_state != "EDGE" or positive_edge not in {
                    "moderate",
                    "strong",
                }:
                    errors.append("entry_structural_edge_floor_misclassified")
            if contract_facts["blocking_overextension"]:
                if adverse_risk != "blocking" or action != "DROP":
                    errors.append("entry_blocking_overextension_misclassified")
            if contract_facts["orderly_pullback_recovery"]:
                if (
                    setup != "pullback_recovery"
                    or trigger != "recovery_required"
                    or action != "WAIT"
                    or adverse_risk in {"blocking", "insufficient"}
                ):
                    errors.append("entry_orderly_pullback_recovery_misclassified")
            if contract_facts["bounded_reversal_probe_candidate"]:
                if (
                    edge_state != "EDGE"
                    or positive_edge not in {"moderate", "strong"}
                    or setup != "reversal"
                    or trigger != "recovery_required"
                    or action != "WAIT"
                    or adverse_risk not in {"low", "moderate", "high"}
                ):
                    errors.append("entry_bounded_reversal_probe_misclassified")
            if (
                enforce_live_probe_contract
                and contract_facts["early_session_probe_candidate"]
            ):
                if (
                    edge_state != "EDGE"
                    or positive_edge not in {"moderate", "strong"}
                    or setup != "continuation"
                    or trigger != "recovery_required"
                    or action != "WAIT"
                    or adverse_risk not in {"low", "moderate", "high"}
                ):
                    errors.append("entry_early_session_probe_misclassified")
            if contract_facts["trusted_supportive_trigger"]:
                # WAIT remains a non-exposure candidate signal.  Trusted tape
                # may justify a recovery-required probe candidate while the
                # existing liquidity, freshness, broker, and submit guards
                # retain final order authority.
                trusted_trigger_action_consistent = bool(
                    (action == "WAIT" and trigger == "recovery_required")
                    or (action != "WAIT" and trigger == "confirmed")
                )
                if (
                    edge_state != "EDGE"
                    or positive_edge not in {"moderate", "strong"}
                    or str(evidence.get("tape") or "").lower() != "supportive"
                    or not trusted_trigger_action_consistent
                ):
                    errors.append("entry_trusted_supportive_trigger_misclassified")
            if edge_state != "INSUFFICIENT_DATA" and contract_facts["thin_tape_sample"]:
                if (
                    str(evidence.get("tape") or "").lower() == "supportive"
                    or trigger == "confirmed"
                ):
                    errors.append("entry_thin_tape_sample_overstated")
            if (
                edge_state != "INSUFFICIENT_DATA"
                and contract_facts["adverse_distribution_no_edge"]
            ):
                if (
                    edge_state != "NO_EDGE"
                    or action != "DROP"
                    or str(evidence.get("trend") or "").lower() != "adverse"
                    or setup != "no_setup"
                    or trigger not in {"failed", "not_applicable"}
                    or not {
                        "distribution_adverse",
                        "volume_confirmation_missing",
                    }.issubset(reason_code_set)
                ):
                    errors.append("entry_adverse_distribution_misclassified")
            if (
                edge_state != "INSUFFICIENT_DATA"
                and contract_facts["ask_wall_wide_spread"]
            ):
                if (
                    str(evidence.get("liquidity") or "").lower() != "adverse"
                    or adverse_risk not in {"high", "blocking"}
                    or action == "BUY"
                    or not {
                        "ask_wall_adverse",
                        "liquidity_adverse",
                    }.intersection(reason_code_set)
                ):
                    errors.append("entry_ask_wall_wide_spread_misclassified")
        elif normalized_stage == "holding":
            holding_facts = _holding_contract_facts(exact_payload)
            if (
                holding_facts["position_observed"]
                and "broker_state_missing" in reason_code_set
            ):
                errors.append("holding_broker_state_missing_misclassified")
            if (
                holding_facts["completed_bars_observed"]
                and "completed_bars_missing" in reason_code_set
            ):
                errors.append("holding_completed_bars_missing_misclassified")
            if (
                holding_facts["fresh_consistent_core"]
                and edge_state == "INSUFFICIENT_DATA"
            ):
                errors.append("holding_sufficient_core_misclassified")
            if holding_facts["fresh_consistent_core"] and {
                "source_stale",
                "source_conflict",
                "venue_session_mismatch",
            }.intersection(reason_code_set):
                errors.append("holding_source_quality_misclassified")
            if action == "TRIM" and not holding_facts["trim_available"]:
                errors.append("holding_trim_requires_multiple_shares")
    if normalized_stage not in STAGE_ACTIONS:
        errors.append("stage_unsupported")
    return errors


def _entry_price_contract_facts(exact_payload: Any) -> dict[str, Any]:
    """Derive a small price-selection ledger without changing the exact payload."""

    payload = exact_payload if isinstance(exact_payload, dict) else {}
    if isinstance(payload.get("exact_payload"), dict):
        payload = payload["exact_payload"]
    price_context = payload.get("price_context")
    price_context = price_context if isinstance(price_context, dict) else {}
    entry_context = payload.get("entry_context_features")
    entry_context = entry_context if isinstance(entry_context, dict) else {}
    snapshot = payload.get("ai_market_snapshot_v1")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    preflight = snapshot.get("ai_input_preflight_v1")
    preflight = preflight if isinstance(preflight, dict) else {}
    candle = payload.get("entry_candle_context")
    candle = candle if isinstance(candle, dict) else {}
    guard = price_context.get("entry_price_guard")
    guard = guard if isinstance(guard, dict) else {}

    def positive_integer(value: Any) -> int | None:
        number = _number(value)
        if number is None or number <= 0 or not float(number).is_integer():
            return None
        return int(number)

    candidate_prices = {
        "DEFENSIVE": positive_integer(price_context.get("defensive_order_price")),
        "REFERENCE": positive_integer(price_context.get("reference_target_price")),
        "RESOLVED": positive_integer(price_context.get("resolved_order_price")),
        "BEST_BID": positive_integer(price_context.get("best_bid")),
        "BEST_ASK": positive_integer(price_context.get("best_ask")),
    }
    source_blockers: list[str] = []
    if not preflight:
        source_blockers.append("preflight_missing")
    elif preflight.get("allowed") is not True:
        source_blockers.append("preflight_not_allowed")
    source_blockers.extend(str(value) for value in preflight.get("blockers") or [])
    if not entry_context:
        source_blockers.append("entry_context_missing")
    if entry_context.get("quote_stale") is True:
        source_blockers.append("quote_stale")
    if entry_context.get("quote_fresh_for_entry") is not True:
        source_blockers.append("quote_not_fresh")
    if preflight.get("venue_consistent") is False:
        source_blockers.append("venue_session_mismatch")

    explicit_block = any(
        value is True
        for value in (
            guard.get("blocked"),
            guard.get("price_selection_blocked"),
            guard.get("setup_invalidated"),
        )
    ) or bool(str(guard.get("block_reason") or "").strip())
    raw_risk_flags = candle.get("risk_flags") or []
    if isinstance(raw_risk_flags, str):
        raw_risk_flags = [raw_risk_flags]
    risk_flags = {str(value).strip().lower() for value in raw_risk_flags}
    setup_invalidated = explicit_block or bool(
        risk_flags.intersection(
            {"setup_invalidated", "failed_breakout", "entry_setup_invalidated"}
        )
    )
    available_price_count = sum(
        value is not None for value in candidate_prices.values()
    )
    skip_reasons = list(dict.fromkeys(source_blockers))
    if setup_invalidated:
        skip_reasons.append("explicit_setup_or_price_guard_block")
    if available_price_count == 0:
        skip_reasons.append("candidate_prices_missing")
    return {
        "schema": "entry_price_exact_contract_facts_v1",
        "candidate_prices": candidate_prices,
        "available_price_count": available_price_count,
        "fresh_quote": not source_blockers,
        "source_blockers": list(dict.fromkeys(source_blockers)),
        "setup_invalidated": setup_invalidated,
        "would_fill_now": entry_context.get("would_fill_now"),
        "spread_bp": _number(entry_context.get("spread_bp")),
        "skip_permitted": bool(skip_reasons),
        "skip_reasons": list(dict.fromkeys(skip_reasons)),
    }


def _entry_price_response_errors(
    response: dict[str, Any],
    *,
    exact_payload: Any,
    contract_facts: dict[str, Any] | None = None,
    require_fill_adjusted_distinct_limit: bool = False,
) -> list[str]:
    facts = _entry_price_contract_facts(exact_payload)
    if isinstance(contract_facts, dict):
        control_price = _number(contract_facts.get("control_selected_price"))
        price_cost_baseline = _number(contract_facts.get("price_cost_baseline"))
        if control_price is not None and control_price > 0:
            facts["control_selected_price"] = control_price
        if price_cost_baseline is not None and price_cost_baseline > 0:
            facts["price_cost_baseline"] = price_cost_baseline
            facts["price_delta_from_cost_baseline_bp"] = {
                candidate_basis: (
                    ((candidate_price - price_cost_baseline) / price_cost_baseline)
                    * 10000.0
                    if candidate_price is not None
                    else None
                )
                for candidate_basis, candidate_price in facts[
                    "candidate_prices"
                ].items()
            }
    action = str(response.get("action") or "").strip().upper()
    basis = str(response.get("price_basis") or "").strip().upper()
    selected_price = _number(response.get("selected_price"))
    errors: list[str] = []
    if action == "SKIP":
        if selected_price is not None or basis != "NONE":
            errors.append("entry_price_skip_requires_null_none")
        if not facts["skip_permitted"]:
            errors.append("entry_price_skip_without_explicit_blocker")
        return errors

    if facts["skip_permitted"]:
        errors.append("entry_price_explicit_blocker_requires_skip")
    action_bases = {
        "USE_DEFENSIVE": (
            {"DEFENSIVE"}
            if facts["candidate_prices"].get("DEFENSIVE") is not None
            else {"BEST_BID"}
        ),
        "USE_REFERENCE": {"REFERENCE"},
        "IMPROVE_LIMIT": {"RESOLVED", "BEST_ASK"},
    }
    allowed_bases = action_bases.get(action, set())
    if basis not in allowed_bases:
        errors.append("entry_price_action_basis_mismatch")
    expected_price = facts["candidate_prices"].get(basis)
    if (
        selected_price is None
        or selected_price <= 0
        or not float(selected_price).is_integer()
    ):
        errors.append("entry_price_selected_price_invalid")
    elif expected_price is None or int(selected_price) != expected_price:
        errors.append("entry_price_selected_price_not_exact_basis_value")
    if require_fill_adjusted_distinct_limit and selected_price is not None:
        control_price = _number(facts.get("control_selected_price"))
        if (
            action in {"USE_REFERENCE", "IMPROVE_LIMIT"}
            and control_price is not None
            and int(selected_price) == int(control_price)
        ):
            errors.append("entry_price_nondefensive_price_not_distinct")
        selected_delta_bp = _number(
            (facts.get("price_delta_from_cost_baseline_bp") or {}).get(basis)
        )
        if selected_delta_bp is not None and selected_delta_bp > 0:
            edge_state = str(response.get("edge_state") or "").strip().upper()
            evidence = response.get("evidence")
            evidence = evidence if isinstance(evidence, dict) else {}
            expected_upside_pct = _number(response.get("expected_upside_pct"))
            expected_downside_pct = _number(response.get("expected_downside_pct"))
            supportive_immediacy = any(
                str(evidence.get(key) or "").strip().lower() == "supportive"
                for key in ("trend", "tape")
            )
            if not (
                edge_state == "EDGE"
                and str(evidence.get("positive_edge") or "").lower()
                in {"moderate", "strong"}
                and str(evidence.get("adverse_risk") or "").lower()
                in {"low", "moderate"}
                and str(evidence.get("trigger") or "").lower() == "confirmed"
                and supportive_immediacy
            ):
                errors.append("entry_price_aggressive_limit_without_confirmed_edge")
            required_upside_pct = (selected_delta_bp / 100.0) + 0.20
            if expected_upside_pct is None or expected_upside_pct < required_upside_pct:
                errors.append("entry_price_aggressive_limit_insufficient_edge_buffer")
            max_chase_cost_bp = _number(
                (contract_facts or {}).get("max_incremental_chase_cost_bp")
            )
            if max_chase_cost_bp is None:
                max_chase_cost_bp = ENTRY_PRICE_MAX_INCREMENTAL_CHASE_COST_BP
            if selected_delta_bp > max_chase_cost_bp:
                errors.append("entry_price_aggressive_limit_exceeds_chase_cost_bound")
            if expected_downside_pct is None or expected_downside_pct >= 0:
                errors.append("entry_price_aggressive_limit_requires_negative_downside")
            else:
                incremental_cost_pct = selected_delta_bp / 100.0
                if abs(expected_downside_pct) < incremental_cost_pct:
                    errors.append(
                        "entry_price_aggressive_limit_downside_below_chase_cost"
                    )
                minimum_reward_risk = _number(
                    (contract_facts or {}).get(
                        "minimum_reward_risk_for_aggressive_basis"
                    )
                )
                if minimum_reward_risk is None:
                    minimum_reward_risk = (
                        ENTRY_PRICE_MIN_REWARD_RISK_FOR_AGGRESSIVE_BASIS
                    )
                if (
                    expected_upside_pct is None
                    or expected_upside_pct / abs(expected_downside_pct)
                    < minimum_reward_risk
                ):
                    errors.append(
                        "entry_price_aggressive_limit_reward_risk_below_floor"
                    )
    return errors


def validate_replay_candidate_response(
    request: dict[str, Any],
    response: dict[str, Any],
) -> list[str]:
    """Validate a replay response with an explicitly scoped offline contract."""

    stage = str(request.get("stage") or "")
    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    semantic_validator_version = str(candidate.get("semantic_validator_version") or "")
    if semantic_validator_version == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION:
        if stage != "entry":
            return ["entry_setup_risk_stage_unsupported"]
        adjudication = response.get("entry_risk_adjudication")
        adjudication = adjudication if isinstance(adjudication, dict) else response
        return validate_entry_risk_adjudication(
            adjudication,
            setup_evidence=request.get("entry_setup_evidence"),
        )
    errors = validate_candidate_response(
        response,
        stage=stage,
        exact_payload=request.get("exact_payload"),
    )
    if (
        semantic_validator_version
        == HOLDING_FLOW_BOUNDED_DEFER_SEMANTIC_VALIDATOR_VERSION
    ):
        if stage != "holding":
            return [*errors, "holding_flow_semantic_stage_unsupported"]
        facts = _holding_contract_facts(request.get("exact_payload"))
        action = str(response.get("action") or "").strip().upper()
        evidence = response.get("evidence")
        evidence = evidence if isinstance(evidence, dict) else {}
        if facts["hard_exit_guard_observed"] and action != "EXIT":
            errors.append("holding_flow_hard_guard_requires_exit")
        if action in {"HOLD", "TRIM"} and not facts["bounded_defer_eligible"]:
            errors.append("holding_flow_defer_not_eligible")
        if action == "HOLD" and str(evidence.get("trigger") or "").lower() != (
            "recovery_required"
        ):
            errors.append("holding_flow_hold_requires_recovery_trigger")
        return list(dict.fromkeys(errors))
    if semantic_validator_version == ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION:
        if stage != "entry_price":
            return [*errors, "entry_price_semantic_stage_unsupported"]
        return [
            *errors,
            *_entry_price_response_errors(
                response,
                exact_payload=request.get("exact_payload"),
                contract_facts=(
                    (request.get("candidate_input") or {}).get(
                        "entry_price_exact_contract_facts_v1"
                    )
                ),
                require_fill_adjusted_distinct_limit=True,
            ),
        ]
    if semantic_validator_version not in {
        ANTICIPATORY_SEMANTIC_VALIDATOR_VERSION,
        BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION,
    }:
        return errors
    bounded_opportunity_contract = (
        semantic_validator_version == BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
    )
    candidate_prompt_version = str(candidate.get("prompt_version") or "")
    clean_continuation_contract = candidate_prompt_version in {
        f"{DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION}_entry",
        f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry",
        f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry",
    }
    selective_recovery_contract = candidate_prompt_version in {
        f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry",
        f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry",
    }
    recovery_confirmation_contract = bool(
        candidate_prompt_version
        == f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
    )
    if stage != "entry":
        return [*errors, "anticipatory_stage_unsupported"]
    analysis = request.get("anticipatory_reversal_analysis")
    analysis = analysis if isinstance(analysis, dict) else {}
    if analysis.get("schema") != ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA:
        return [*errors, "anticipatory_analysis_missing"]

    evidence = response.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    action = str(response.get("action") or "").strip().upper()
    edge_state = str(response.get("edge_state") or "").strip().upper()
    setup = str(evidence.get("setup") or "").strip().lower()
    tape = str(evidence.get("tape") or "").strip().lower()
    liquidity = str(evidence.get("liquidity") or "").strip().lower()
    adverse_risk = str(evidence.get("adverse_risk") or "").strip().lower()
    trigger = str(evidence.get("trigger") or "").strip().lower()
    source_mode = str(analysis.get("source_mode") or "")
    spread = analysis.get("spread")
    spread = spread if isinstance(spread, dict) else {}
    precursors = analysis.get("precursors")
    precursors = precursors if isinstance(precursors, dict) else {}
    execution_cost = analysis.get("execution_cost")
    execution_cost = execution_cost if isinstance(execution_cost, dict) else {}

    semantic_errors: list[str] = []
    source_unusable_fail_closed = bool(
        source_mode == "unusable"
        and edge_state == "INSUFFICIENT_DATA"
        and action == "WAIT"
    )
    if source_mode == "unusable":
        if not source_unusable_fail_closed:
            semantic_errors.append("anticipatory_unusable_source_requires_wait")
        else:
            # The supplemental source contract intentionally owns the fail-closed
            # state here.  Exact structural facts can remain observable while a
            # required candle/quote/tape source is unusable; they must not force
            # EDGE and contradict the required INSUFFICIENT_DATA/WAIT response.
            source_unusable_superseded_errors = {
                "entry_structural_edge_floor_misclassified",
                "entry_blocking_overextension_misclassified",
                "entry_orderly_pullback_recovery_misclassified",
                "entry_bounded_reversal_probe_misclassified",
                "entry_early_session_probe_misclassified",
                "entry_trusted_supportive_trigger_misclassified",
            }
            errors = [
                error
                for error in errors
                if error not in source_unusable_superseded_errors
            ]
    confidence = _number(response.get("confidence"))
    confidence_cap = _number(analysis.get("confidence_cap"))
    if (
        source_mode == "degraded_but_bounded"
        and confidence is not None
        and confidence_cap is not None
        and confidence > confidence_cap
    ):
        semantic_errors.append("anticipatory_degraded_confidence_above_cap")
    if (
        source_mode != "unusable"
        and spread.get("regime") == "wide_but_observable"
        and liquidity != "adverse"
    ):
        semantic_errors.append("anticipatory_wide_spread_liquidity_not_adverse")

    if bounded_opportunity_contract:
        bounded = analysis.get("bounded_opportunity")
        bounded = bounded if isinstance(bounded, dict) else {}
        clean_continuation = analysis.get("clean_continuation_probe")
        clean_continuation = (
            clean_continuation if isinstance(clean_continuation, dict) else {}
        )
        selective_recovery = analysis.get("selective_recovery_probe")
        selective_recovery = (
            selective_recovery if isinstance(selective_recovery, dict) else {}
        )
        recovery_confirmation = analysis.get("recovery_confirmation_probe")
        recovery_confirmation = (
            recovery_confirmation if isinstance(recovery_confirmation, dict) else {}
        )
        if not bounded:
            return [*errors, *semantic_errors, "bounded_opportunity_contract_missing"]
        if clean_continuation_contract and not clean_continuation:
            return [
                *errors,
                *semantic_errors,
                "clean_continuation_probe_contract_missing",
            ]
        if selective_recovery_contract and not selective_recovery:
            return [
                *errors,
                *semantic_errors,
                "selective_recovery_probe_contract_missing",
            ]
        if recovery_confirmation_contract and not recovery_confirmation:
            return [
                *errors,
                *semantic_errors,
                "recovery_confirmation_probe_contract_missing",
            ]
        cost_pct = _number(execution_cost.get("conservative_execution_cost_pct"))
        upside = _number(response.get("expected_upside_pct"))
        downside = _number(response.get("expected_downside_pct"))
        after_cost_ratio = (
            max(0.0, upside - cost_pct) / abs(downside - cost_pct)
            if cost_pct is not None
            and upside is not None
            and downside is not None
            and downside < 0
            else None
        )
        clean_continuation_eligible = bool(
            clean_continuation_contract and clean_continuation.get("eligible") is True
        )
        selective_recovery_eligible = bool(
            selective_recovery_contract and selective_recovery.get("eligible") is True
        )
        recovery_confirmation_eligible = bool(
            recovery_confirmation_contract
            and recovery_confirmation.get("eligible") is True
        )
        contracted_buy_eligible = bool(
            clean_continuation_eligible
            or (
                recovery_confirmation_eligible
                if recovery_confirmation_contract
                else selective_recovery_eligible
            )
        )
        after_cost_floor = (
            0.75
            if clean_continuation_eligible or recovery_confirmation_eligible
            else 1.0
        )
        if action == "BUY":
            adverse_risk = str(evidence.get("adverse_risk") or "").strip().lower()
            trigger = str(evidence.get("trigger") or "").strip().lower()
            if bounded.get("eligible_for_one_share_probe") is not True:
                semantic_errors.append("bounded_opportunity_buy_not_eligible")
            if recovery_confirmation_contract and not contracted_buy_eligible:
                semantic_errors.append("recovery_confirmation_buy_not_eligible")
            elif selective_recovery_contract and not contracted_buy_eligible:
                semantic_errors.append("selective_recovery_buy_not_eligible")
            if bounded.get("execution_policy") != "passive_probe_required":
                semantic_errors.append("bounded_opportunity_passive_probe_required")
            if setup not in {"continuation", "pullback_recovery", "reversal"}:
                semantic_errors.append("bounded_opportunity_setup_invalid")
            if adverse_risk not in {"low", "moderate", "high"}:
                semantic_errors.append("bounded_opportunity_risk_not_bounded")
            if trigger != "confirmed":
                semantic_errors.append("bounded_opportunity_trigger_not_confirmed")
            if adverse_risk == "high" and confidence is not None and confidence > 65:
                semantic_errors.append("bounded_opportunity_high_risk_confidence_cap")
            if cost_pct is None or upside is None or downside is None or downside >= 0:
                semantic_errors.append(
                    "bounded_opportunity_after_cost_reward_risk_unavailable"
                )
            else:
                adjusted_upside = max(0.0, upside - cost_pct)
                adjusted_downside = downside - cost_pct
                if adjusted_upside / abs(adjusted_downside) < after_cost_floor:
                    semantic_errors.append(
                        "bounded_opportunity_after_cost_reward_risk_below_floor"
                    )
            if not semantic_errors:
                relaxable = {
                    "entry_buy_adverse_risk_too_high",
                    "entry_buy_reward_risk_below_floor",
                    "entry_orderly_pullback_recovery_misclassified",
                    "entry_bounded_reversal_probe_misclassified",
                    "entry_thin_tape_sample_overstated",
                    "entry_adverse_distribution_misclassified",
                }
                if spread.get("regime") == "wide_but_observable":
                    relaxable.add("entry_ask_wall_wide_spread_misclassified")
                errors = [error for error in errors if error not in relaxable]
        elif (
            action == "WAIT"
            and bounded.get("eligible_for_one_share_probe") is True
            and edge_state == "EDGE"
            and setup in {"continuation", "pullback_recovery", "reversal"}
            and str(evidence.get("positive_edge") or "") in {"moderate", "strong"}
            and str(evidence.get("adverse_risk") or "") in {"low", "moderate", "high"}
            and str(evidence.get("trigger") or "") in {"recovery_required", "confirmed"}
            and (
                str(evidence.get("trigger") or "") == "recovery_required"
                or after_cost_ratio is None
                or after_cost_ratio < 1.0
            )
        ):
            # A candidate that lost after-cost BUY eligibility may retain the
            # deterministic bounded edge as WAIT.  This is no-exposure offline
            # attribution, not a relaxation of submit or broker guards.
            errors = [
                error
                for error in errors
                if error
                not in {
                    "entry_adverse_distribution_misclassified",
                    "entry_ask_wall_wide_spread_misclassified",
                    "entry_wait_requires_recovery_trigger",
                    "entry_trusted_supportive_trigger_misclassified",
                }
            ]
        elif (
            action == "DROP"
            and bounded.get("eligible_for_one_share_probe") is True
            and edge_state == "EDGE"
            and setup in {"continuation", "pullback_recovery", "reversal"}
            and adverse_risk == "high"
            and liquidity == "adverse"
            and trigger == "confirmed"
            and after_cost_ratio is not None
        ):
            # High risk is tolerated by the offline one-share experiment but it
            # does not compel exposure. Preserve the model's truthful DROP and
            # charge it to no-exposure/missed-opportunity attribution instead of
            # treating conservative abstention as a malformed response.
            errors = [
                error
                for error in errors
                if error
                not in {
                    "entry_edge_drop_requires_failed_blocking_or_unfavorable",
                    "entry_thin_tape_sample_overstated",
                    "entry_adverse_distribution_misclassified",
                    "entry_orderly_pullback_recovery_misclassified",
                    "entry_bounded_reversal_probe_misclassified",
                    "entry_ask_wall_wide_spread_misclassified",
                }
            ]
        hard_blockers = [
            str(value) for value in analysis.get("hard_blockers") or [] if value
        ]
        if hard_blockers and action == "DROP" and adverse_risk == "blocking":
            # A deterministic hard blocker owns the final no-exposure action.
            # Exact-candle facts may still describe an early reversal or orderly
            # pullback, but they must not force WAIT after the blocker has been
            # preserved as DROP.  Base EDGE/DROP validation still requires a
            # failed trigger, blocking risk, or unfavorable reward/risk.
            errors = [
                error
                for error in errors
                if error
                not in {
                    "entry_adverse_distribution_misclassified",
                    "entry_orderly_pullback_recovery_misclassified",
                    "entry_bounded_reversal_probe_misclassified",
                }
            ]
        return list(dict.fromkeys([*errors, *semantic_errors]))

    reversal_buy = action == "BUY" and setup == "reversal"
    if action == "BUY" and setup != "reversal":
        return [*errors, *semantic_errors]
    if reversal_buy:
        eligible = analysis.get("eligible_for_counterfactual_probe") is True
        if not eligible:
            semantic_errors.append("anticipatory_buy_without_eligible_precursors")
        if analysis.get("execution_policy") != "passive_probe_required":
            semantic_errors.append("anticipatory_buy_requires_passive_probe")
        if int(_number(precursors.get("non_tape_precursor_count")) or 0) < 3:
            semantic_errors.append("anticipatory_buy_non_tape_precursors_insufficient")
        if tape == "supportive" and source_mode == "degraded_but_bounded":
            semantic_errors.append("anticipatory_degraded_tape_overstated")
        cost_pct = _number(execution_cost.get("conservative_execution_cost_pct"))
        upside = _number(response.get("expected_upside_pct"))
        downside = _number(response.get("expected_downside_pct"))
        if cost_pct is None or upside is None or downside is None or downside >= 0:
            semantic_errors.append("anticipatory_after_cost_reward_risk_unavailable")
        else:
            adjusted_upside = max(0.0, upside - cost_pct)
            adjusted_downside = downside - cost_pct
            if adjusted_upside / abs(adjusted_downside) < 1.25:
                semantic_errors.append(
                    "anticipatory_after_cost_reward_risk_below_floor"
                )

        relaxable = {
            "entry_thin_tape_sample_overstated",
            "entry_adverse_distribution_misclassified",
        }
        if spread.get("regime") == "wide_but_observable":
            relaxable.add("entry_ask_wall_wide_spread_misclassified")
        if eligible and not semantic_errors:
            errors = [error for error in errors if error not in relaxable]
    return list(dict.fromkeys([*errors, *semantic_errors]))


def repair_anticipatory_candidate_response(
    request: dict[str, Any],
    response: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Close deterministic V2.9.1 semantic conflicts without weakening risk.

    The adapter is offline-only and runs only after all provider correction
    attempts failed.  It preserves exact numeric estimates and applies the same
    deterministic contract facts already used by the validator.  When evidence
    conflicts with BUY, it can only move toward WAIT/DROP, never toward BUY.
    """

    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    if (
        candidate.get("semantic_repair_version") != ANTICIPATORY_SEMANTIC_REPAIR_VERSION
        or str(request.get("stage") or "") != "entry"
    ):
        return dict(response), []
    repaired = json.loads(json.dumps(response))
    evidence = repaired.get("evidence")
    if not isinstance(evidence, dict):
        return repaired, []
    facts = _entry_contract_facts(request.get("exact_payload"))
    repairs: list[str] = []

    def set_value(container: dict[str, Any], key: str, value: Any, reason: str) -> None:
        if container.get(key) != value:
            container[key] = value
            repairs.append(reason)

    if facts["structural_edge_floor"]:
        set_value(repaired, "edge_state", "EDGE", "structural_edge_floor")
        if str(evidence.get("positive_edge") or "") not in {"moderate", "strong"}:
            set_value(evidence, "positive_edge", "moderate", "structural_edge_strength")

    if facts["adverse_distribution_no_edge"] and not facts["structural_edge_floor"]:
        set_value(repaired, "edge_state", "NO_EDGE", "adverse_distribution_edge")
        set_value(repaired, "action", "DROP", "adverse_distribution_action")
        set_value(evidence, "trend", "adverse", "adverse_distribution_trend")
        set_value(evidence, "setup", "no_setup", "adverse_distribution_setup")
        set_value(evidence, "positive_edge", "none", "adverse_distribution_strength")
        set_value(evidence, "trigger", "failed", "adverse_distribution_trigger")

    if facts["orderly_pullback_recovery"]:
        set_value(repaired, "edge_state", "EDGE", "orderly_pullback_edge")
        set_value(repaired, "action", "WAIT", "orderly_pullback_action")
        set_value(evidence, "setup", "pullback_recovery", "orderly_pullback_setup")
        set_value(
            evidence,
            "positive_edge",
            (
                evidence.get("positive_edge")
                if evidence.get("positive_edge") in {"moderate", "strong"}
                else "moderate"
            ),
            "orderly_pullback_strength",
        )
        set_value(
            evidence,
            "trigger",
            "recovery_required",
            "orderly_pullback_trigger",
        )
        if evidence.get("adverse_risk") in {"blocking", "insufficient"}:
            set_value(
                evidence,
                "adverse_risk",
                "high" if facts["ask_wall_wide_spread"] else "moderate",
                "orderly_pullback_nonblocking_risk",
            )

    if facts["trusted_supportive_trigger"]:
        set_value(repaired, "edge_state", "EDGE", "trusted_trigger_edge")
        if str(evidence.get("positive_edge") or "") not in {"moderate", "strong"}:
            set_value(evidence, "positive_edge", "moderate", "trusted_trigger_strength")
        set_value(evidence, "tape", "supportive", "trusted_trigger_tape")
        set_value(evidence, "trigger", "confirmed", "trusted_trigger_state")
        if repaired.get("action") == "WAIT":
            set_value(repaired, "action", "DROP", "trusted_trigger_no_wait")

    if facts["blocking_overextension"]:
        set_value(repaired, "action", "DROP", "blocking_overextension_action")
        set_value(
            evidence,
            "adverse_risk",
            "blocking",
            "blocking_overextension_risk",
        )

    if facts["ask_wall_wide_spread"]:
        set_value(evidence, "liquidity", "adverse", "ask_wall_liquidity")
        if facts["orderly_pullback_recovery"]:
            set_value(evidence, "adverse_risk", "high", "ask_wall_high_risk")
        else:
            set_value(evidence, "adverse_risk", "blocking", "ask_wall_blocking_risk")
            if repaired.get("action") == "BUY":
                set_value(repaired, "action", "DROP", "ask_wall_blocks_buy")

    if repaired.get("action") == "BUY" and evidence.get("adverse_risk") not in {
        "low",
        "moderate",
    }:
        set_value(repaired, "action", "DROP", "unsafe_buy_demoted")
    if repaired.get("action") == "WAIT" and evidence.get("adverse_risk") in {
        "blocking",
        "insufficient",
    }:
        set_value(evidence, "adverse_risk", "high", "wait_nonblocking_risk")

    edge_state = str(repaired.get("edge_state") or "")
    if edge_state == "NO_EDGE":
        if evidence.get("positive_edge") not in {"none", "weak"}:
            set_value(evidence, "positive_edge", "none", "no_edge_strength")
        if evidence.get("setup") not in {"no_setup", "not_applicable"}:
            set_value(evidence, "setup", "no_setup", "no_edge_setup")
        set_value(repaired, "action", "DROP", "no_edge_action")
    elif edge_state == "EDGE" and evidence.get("positive_edge") not in {
        "moderate",
        "strong",
    }:
        set_value(evidence, "positive_edge", "moderate", "edge_strength")

    action = str(repaired.get("action") or "")
    trigger = str(evidence.get("trigger") or "")
    if action == "DROP" and trigger not in {"failed", "confirmed"}:
        set_value(
            evidence,
            "trigger",
            "confirmed" if facts["trusted_supportive_trigger"] else "failed",
            "drop_trigger_alignment",
        )
        trigger = str(evidence.get("trigger") or "")

    reason_codes = [
        str(value)
        for value in repaired.get("reason_codes") or []
        if str(value) in DECISION_QUALITY_V2_REASON_CODES
    ]
    trigger_codes = {
        "recovery_trigger_confirmed",
        "recovery_trigger_required",
        "recovery_trigger_failed",
    }
    edge_codes = {"edge_positive", "edge_absent", "no_positive_edge"}
    reward_codes = {"risk_reward_favorable", "risk_reward_unfavorable"}
    reason_codes = [
        code
        for code in reason_codes
        if code not in trigger_codes | edge_codes | reward_codes
    ]
    trigger_code = {
        "confirmed": "recovery_trigger_confirmed",
        "recovery_required": "recovery_trigger_required",
        "failed": "recovery_trigger_failed",
    }.get(trigger)
    if trigger_code:
        reason_codes.append(trigger_code)
    reason_codes.append("edge_positive" if edge_state == "EDGE" else "edge_absent")
    upside = _number(repaired.get("expected_upside_pct"))
    downside = _number(repaired.get("expected_downside_pct"))
    favorable = bool(
        upside is not None
        and downside is not None
        and downside < 0
        and upside / abs(downside) >= 1.25
    )
    reason_codes.append(
        "risk_reward_favorable" if favorable else "risk_reward_unfavorable"
    )
    mandatory_reason_codes = [
        trigger_code,
        "edge_positive" if edge_state == "EDGE" else "edge_absent",
        "risk_reward_favorable" if favorable else "risk_reward_unfavorable",
    ]
    if facts["ask_wall_wide_spread"]:
        reason_codes.extend(("ask_wall_adverse", "liquidity_adverse"))
        mandatory_reason_codes.extend(("ask_wall_adverse", "liquidity_adverse"))
    if facts["adverse_distribution_no_edge"]:
        reason_codes.extend(("distribution_adverse", "volume_confirmation_missing"))
        mandatory_reason_codes.extend(
            ("distribution_adverse", "volume_confirmation_missing")
        )
    unique_codes = list(dict.fromkeys(reason_codes))
    mandatory_codes = [
        code
        for code in dict.fromkeys(mandatory_reason_codes)
        if code is not None and code in unique_codes
    ]
    optional_codes = [code for code in unique_codes if code not in mandatory_codes]
    normalized_codes = [
        *mandatory_codes,
        *optional_codes[: max(0, 8 - len(mandatory_codes))],
    ]
    if repaired.get("reason_codes") != normalized_codes:
        repaired["reason_codes"] = normalized_codes
        repairs.append("reason_code_evidence_alignment")
    return repaired, list(dict.fromkeys(repairs))


def repair_bounded_opportunity_candidate_response(
    request: dict[str, Any],
    response: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Close representational semantic conflicts without creating BUY exposure.

    This adapter is shared by offline replay and the selected live entry prompt.
    It may preserve an EDGE as WAIT or demote an invalid BUY to WAIT/DROP.  It
    never promotes a non-BUY response to BUY.  Sign-only normalization preserves
    the magnitude of a model downside estimate while closing the documented
    negative-downside convention.
    """

    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    if (
        candidate.get("semantic_validator_version")
        != BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
        or candidate.get("semantic_repair_version")
        != BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION
        or str(request.get("stage") or "") != "entry"
    ):
        return dict(response), []
    analysis = request.get("anticipatory_reversal_analysis")
    analysis = analysis if isinstance(analysis, dict) else {}
    source_mode = str(analysis.get("source_mode") or "")
    repaired = json.loads(json.dumps(response))
    repairs: list[str] = []

    def set_value(container: dict[str, Any], key: str, value: Any, reason: str) -> None:
        if container.get(key) != value:
            container[key] = value
            repairs.append(reason)

    if source_mode == "degraded_but_bounded":
        cap = int(_number(analysis.get("confidence_cap")) or 60)
        confidence = _number(repaired.get("confidence"))
        if confidence is not None and confidence > cap:
            repaired["confidence"] = cap
            repairs.append("degraded_source_confidence_clamped")
    if source_mode == "unusable":
        safe_response = {
            "edge_state": "INSUFFICIENT_DATA",
            "action": "WAIT",
            "expected_upside_pct": None,
            "expected_downside_pct": None,
            "confidence": 0,
            "reason_codes": ["insufficient_core_data"],
            "evidence": {
                "trend": "insufficient",
                "liquidity": "insufficient",
                "tape": "insufficient",
                "risk": "insufficient",
                "uncertainty": "high",
                "setup": "insufficient",
                "positive_edge": "insufficient",
                "adverse_risk": "insufficient",
                "trigger": "insufficient",
            },
        }
        if repaired != safe_response:
            repaired = safe_response
            repairs.append("unusable_source_fail_closed_wait")
        return repaired, repairs

    evidence = repaired.get("evidence")
    if not isinstance(evidence, dict):
        return repaired, repairs

    raw_action = str(repaired.get("action") or "").strip().upper()
    if raw_action not in STAGE_ACTIONS["entry"]:
        # The model occasionally returns a prose-decorated non-BUY action even
        # though the prompt asks for an enum.  Preserve its no-exposure intent;
        # never infer BUY from a non-canonical token.
        canonical_action = None
        drop_markers = (
            raw_action.startswith("DROP"),
            "NO_EDGE_DROP" in raw_action,
            "ENTRY_DECISION: DROP" in raw_action,
            "DECISION_NO_EDGE_DROP" in raw_action,
            raw_action == "STAGE_NO_ENTRY",
        )
        wait_markers = (
            "WAIT" in raw_action,
            "RECOVERY_REQUIRED" in raw_action,
            "OBSERVATION" in raw_action,
            "EVALUATE" in raw_action,
            "PASSIVE_PROBE" in raw_action,
        )
        if any(drop_markers):
            canonical_action = "DROP"
        elif any(wait_markers):
            canonical_action = "WAIT"
        elif "DROP" in raw_action or "NO_ENTRY" in raw_action:
            canonical_action = "DROP"
        if canonical_action is not None:
            set_value(
                repaired,
                "action",
                canonical_action,
                "non_buy_action_enum_normalized",
            )

    action = str(repaired.get("action") or "").strip().upper()
    if action in {"WAIT", "DROP"}:
        downside = _number(repaired.get("expected_downside_pct"))
        if downside is not None and downside > 0:
            set_value(
                repaired,
                "expected_downside_pct",
                -downside,
                "non_buy_downside_sign_normalized",
            )

    evidence_aliases = {
        "risk": {"blocking": "high", "moderate": "medium"},
        "tape": {"neutral": "mixed"},
        "adverse_risk": {"medium": "moderate"},
    }
    for field, aliases in evidence_aliases.items():
        value = str(evidence.get(field) or "").strip().lower()
        normalized = aliases.get(value)
        if normalized is not None:
            set_value(
                evidence,
                field,
                normalized,
                f"{field}_enum_normalized",
            )
    facts = _entry_contract_facts(request.get("exact_payload"))
    bounded = analysis.get("bounded_opportunity")
    bounded = bounded if isinstance(bounded, dict) else {}
    clean_continuation = analysis.get("clean_continuation_probe")
    clean_continuation = (
        clean_continuation if isinstance(clean_continuation, dict) else {}
    )
    execution_cost = analysis.get("execution_cost")
    execution_cost = execution_cost if isinstance(execution_cost, dict) else {}
    cost_pct = _number(execution_cost.get("conservative_execution_cost_pct"))
    upside = _number(repaired.get("expected_upside_pct"))
    downside = _number(repaired.get("expected_downside_pct"))
    after_cost_ratio = (
        max(0.0, upside - cost_pct) / abs(downside - cost_pct)
        if cost_pct is not None
        and upside is not None
        and downside is not None
        and downside < 0
        else None
    )
    selective_recovery = analysis.get("selective_recovery_probe")
    selective_recovery = (
        selective_recovery if isinstance(selective_recovery, dict) else {}
    )
    recovery_confirmation = analysis.get("recovery_confirmation_probe")
    recovery_confirmation = (
        recovery_confirmation if isinstance(recovery_confirmation, dict) else {}
    )
    candidate_prompt_version = str(candidate.get("prompt_version") or "")
    v12_contract = bool(
        candidate_prompt_version
        == f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry"
    )
    v13_contract = bool(
        candidate_prompt_version
        == f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
    )
    clean_continuation_contract = bool(
        candidate_prompt_version
        in {
            f"{DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION}_entry",
            f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry",
            f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry",
        }
        and clean_continuation.get("eligible") is True
    )
    selective_recovery_contract = bool(
        (v12_contract or v13_contract) and selective_recovery.get("eligible") is True
    )
    recovery_confirmation_contract = bool(
        v13_contract and recovery_confirmation.get("eligible") is True
    )
    contracted_buy_eligible = bool(
        clean_continuation_contract
        or (
            recovery_confirmation_contract
            if v13_contract
            else selective_recovery_contract
        )
    )
    after_cost_floor = (
        0.75 if clean_continuation_contract or recovery_confirmation_contract else 1.0
    )

    if facts["structural_edge_floor"]:
        set_value(repaired, "edge_state", "EDGE", "structural_edge_floor")
        if evidence.get("positive_edge") not in {"moderate", "strong"}:
            set_value(evidence, "positive_edge", "moderate", "structural_edge_strength")

    if (
        facts["adverse_distribution_no_edge"]
        and not facts["structural_edge_floor"]
        and str(repaired.get("edge_state") or "").strip().upper() == "NO_EDGE"
        and str(repaired.get("action") or "").strip().upper() == "DROP"
    ):
        set_value(evidence, "trend", "adverse", "adverse_distribution_trend")
        set_value(evidence, "setup", "no_setup", "adverse_distribution_setup")
        set_value(
            evidence,
            "positive_edge",
            "none",
            "adverse_distribution_strength",
        )
        set_value(evidence, "trigger", "failed", "adverse_distribution_trigger")

    if facts["bounded_reversal_probe_candidate"]:
        set_value(repaired, "edge_state", "EDGE", "bounded_reversal_edge")
        set_value(repaired, "action", "WAIT", "bounded_reversal_wait")
        set_value(evidence, "setup", "reversal", "bounded_reversal_setup")
        if evidence.get("positive_edge") not in {"moderate", "strong"}:
            set_value(
                evidence, "positive_edge", "moderate", "bounded_reversal_strength"
            )
        if evidence.get("adverse_risk") not in {"low", "moderate", "high"}:
            set_value(evidence, "adverse_risk", "high", "bounded_reversal_risk")
        set_value(
            evidence,
            "trigger",
            "recovery_required",
            "bounded_reversal_trigger",
        )
    elif facts["orderly_pullback_recovery"]:
        set_value(repaired, "edge_state", "EDGE", "orderly_pullback_edge")
        set_value(repaired, "action", "WAIT", "orderly_pullback_wait")
        set_value(evidence, "setup", "pullback_recovery", "orderly_pullback_setup")
        if evidence.get("positive_edge") not in {"moderate", "strong"}:
            set_value(
                evidence, "positive_edge", "moderate", "orderly_pullback_strength"
            )
        if evidence.get("adverse_risk") not in {"low", "moderate", "high"}:
            set_value(evidence, "adverse_risk", "high", "orderly_pullback_risk")
        set_value(
            evidence,
            "trigger",
            "recovery_required",
            "orderly_pullback_trigger",
        )

    if facts["trusted_supportive_trigger"]:
        set_value(repaired, "edge_state", "EDGE", "trusted_trigger_edge")
        if evidence.get("positive_edge") not in {"moderate", "strong"}:
            set_value(evidence, "positive_edge", "moderate", "trusted_trigger_strength")
        set_value(evidence, "tape", "supportive", "trusted_trigger_tape")
        set_value(evidence, "trigger", "confirmed", "trusted_trigger_state")
        if repaired.get("action") == "WAIT":
            set_value(repaired, "action", "DROP", "trusted_trigger_wait_removed")

    if facts["blocking_overextension"]:
        set_value(repaired, "action", "DROP", "blocking_overextension_action")
        set_value(evidence, "adverse_risk", "blocking", "blocking_overextension_risk")
    spread = analysis.get("spread")
    spread = spread if isinstance(spread, dict) else {}
    if spread.get("regime") == "wide_but_observable":
        set_value(
            evidence,
            "liquidity",
            "adverse",
            "wide_spread_liquidity_aligned",
        )
    bounded_wide_spread = bool(
        facts["ask_wall_wide_spread"]
        and spread.get("regime") == "wide_but_observable"
        and bounded.get("eligible_for_one_share_probe") is True
    )
    if facts["ask_wall_wide_spread"]:
        set_value(evidence, "liquidity", "adverse", "ask_wall_liquidity")
        if facts["orderly_pullback_recovery"] or (
            bounded_wide_spread and repaired.get("action") in {"BUY", "WAIT"}
        ):
            set_value(evidence, "adverse_risk", "high", "ask_wall_bounded_high_risk")
        else:
            set_value(evidence, "adverse_risk", "blocking", "ask_wall_blocking_risk")
            if repaired.get("action") == "BUY":
                set_value(repaired, "action", "DROP", "ask_wall_buy_removed")

    hard_blockers = [str(value) for value in analysis.get("hard_blockers") or []]
    if hard_blockers:
        if repaired.get("action") in {"BUY", "WAIT"}:
            set_value(repaired, "action", "DROP", "deterministic_hard_blocker_drop")
        set_value(
            evidence,
            "adverse_risk",
            "blocking",
            "deterministic_hard_blocker_risk",
        )
        set_value(
            evidence,
            "risk",
            "high",
            "deterministic_hard_blocker_risk_level",
        )
        if not facts["trusted_supportive_trigger"]:
            set_value(
                evidence,
                "trigger",
                "failed",
                "deterministic_hard_blocker_trigger",
            )

    if repaired.get("action") == "BUY":
        adverse_risk = str(evidence.get("adverse_risk") or "")
        bounded_buy_valid = bool(
            bounded.get("eligible_for_one_share_probe") is True
            and (not (v12_contract or v13_contract) or contracted_buy_eligible)
            and bounded.get("execution_policy") == "passive_probe_required"
            and adverse_risk in {"low", "moderate", "high"}
            and str(evidence.get("trigger") or "") == "confirmed"
            and after_cost_ratio is not None
            and after_cost_ratio >= after_cost_floor
        )
        if not bounded_buy_valid:
            if adverse_risk == "blocking":
                set_value(repaired, "action", "DROP", "invalid_probe_buy_dropped")
            else:
                set_value(repaired, "action", "WAIT", "invalid_probe_buy_waited")
                if not facts["trusted_supportive_trigger"]:
                    set_value(
                        evidence,
                        "trigger",
                        "recovery_required",
                        "invalid_probe_recovery_required",
                    )
                if adverse_risk not in {"low", "moderate", "high"}:
                    set_value(evidence, "adverse_risk", "high", "invalid_probe_risk")

    edge_state = str(repaired.get("edge_state") or "")
    action = str(repaired.get("action") or "")
    trigger = str(evidence.get("trigger") or "")
    if edge_state == "NO_EDGE":
        set_value(repaired, "action", "DROP", "no_edge_action")
        if evidence.get("positive_edge") not in {"none", "weak"}:
            set_value(evidence, "positive_edge", "none", "no_edge_strength")
        if evidence.get("setup") not in {"no_setup", "not_applicable"}:
            set_value(evidence, "setup", "no_setup", "no_edge_setup")
    elif edge_state == "EDGE" and evidence.get("positive_edge") not in {
        "moderate",
        "strong",
    }:
        set_value(evidence, "positive_edge", "moderate", "edge_strength")
    if (
        action == "WAIT"
        and trigger != "recovery_required"
        and not (
            facts["trusted_supportive_trigger"]
            and trigger == "confirmed"
            and (after_cost_ratio is None or after_cost_ratio < 1.0)
        )
    ):
        set_value(evidence, "trigger", "recovery_required", "wait_trigger_alignment")
    if action == "WAIT" and evidence.get("adverse_risk") in {
        "blocking",
        "insufficient",
    }:
        set_value(evidence, "adverse_risk", "high", "wait_nonblocking_risk")
    if (
        action == "DROP"
        and evidence.get("adverse_risk") == "blocking"
        and evidence.get("trigger") == "recovery_required"
    ):
        set_value(evidence, "trigger", "failed", "blocking_drop_trigger_alignment")

    edge_state = str(repaired.get("edge_state") or "")
    trigger = str(evidence.get("trigger") or "")
    reason_codes = [
        str(value)
        for value in repaired.get("reason_codes") or []
        if str(value) in DECISION_QUALITY_V2_REASON_CODES
    ]
    mutually_owned = {
        "recovery_trigger_confirmed",
        "recovery_trigger_required",
        "recovery_trigger_failed",
        "structural_edge_without_trigger",
        "edge_positive",
        "edge_absent",
        "no_positive_edge",
        "risk_reward_favorable",
        "risk_reward_unfavorable",
    }
    reason_codes = [code for code in reason_codes if code not in mutually_owned]
    trigger_code = {
        "confirmed": "recovery_trigger_confirmed",
        "recovery_required": "recovery_trigger_required",
        "failed": "recovery_trigger_failed",
    }.get(trigger)
    favorable = after_cost_ratio is not None and after_cost_ratio >= 1.0
    mandatory_codes = [
        trigger_code,
        "edge_positive" if edge_state == "EDGE" else "edge_absent",
        "risk_reward_favorable" if favorable else "risk_reward_unfavorable",
    ]
    if facts["ask_wall_wide_spread"]:
        mandatory_codes.extend(("ask_wall_adverse", "liquidity_adverse"))
    if facts["adverse_distribution_no_edge"]:
        mandatory_codes.extend(("distribution_adverse", "volume_confirmation_missing"))
    mandatory_codes = [
        code for code in dict.fromkeys(mandatory_codes) if code is not None
    ]
    optional_codes = [
        code for code in dict.fromkeys(reason_codes) if code not in mandatory_codes
    ]
    normalized_codes = [
        *mandatory_codes,
        *optional_codes[: max(0, 8 - len(mandatory_codes))],
    ]
    if repaired.get("reason_codes") != normalized_codes:
        repaired["reason_codes"] = normalized_codes
        repairs.append("reason_code_evidence_alignment")
    resolved_codes, conflicts_resolved = resolve_candidate_reason_code_conflicts(
        repaired
    )
    if conflicts_resolved:
        repaired["reason_codes"] = resolved_codes
        repairs.append("reason_code_conflicts_resolved")
    return repaired, list(dict.fromkeys(repairs))


def _prompt_v2_openai_schema(stage: str) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip().lower()
    actions = sorted(STAGE_ACTIONS.get(normalized_stage, set()))
    if not actions:
        raise ValueError(f"unsupported decision-quality stage: {stage}")
    evidence_properties = {
        key: {"type": "string", "enum": sorted(values)}
        for key, values in EVIDENCE_VALUES.items()
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "edge_state",
            "action",
            "expected_upside_pct",
            "expected_downside_pct",
            "confidence",
            "reason_codes",
            "evidence",
        ],
        "properties": {
            "edge_state": {
                "type": "string",
                "enum": ["EDGE", "NO_EDGE", "INSUFFICIENT_DATA"],
            },
            "action": {"type": "string", "enum": actions},
            "expected_upside_pct": {
                "type": ["number", "null"],
                "minimum": 0,
            },
            "expected_downside_pct": {
                "type": ["number", "null"],
                "maximum": 0,
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "reason_codes": {
                "type": "array",
                "minItems": 1,
                "maxItems": 8,
                "items": {
                    "type": "string",
                    "enum": list(DECISION_QUALITY_V2_REASON_CODES),
                },
            },
            "evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REASON_EVIDENCE_KEYS),
                "properties": evidence_properties,
            },
        },
    }


def _candidate_openai_schema(
    *, stage: str, candidate: dict[str, Any], setup_evidence: Any = None
) -> dict[str, Any]:
    if (
        str(candidate.get("semantic_validator_version") or "")
        == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
    ):
        if str(stage or "").strip().lower() != "entry":
            raise ValueError("entry setup-risk schema supports entry only")
        return entry_risk_adjudication_openai_schema(setup_evidence)
    return _prompt_v2_openai_schema(stage)


def _candidate_contract_sha256(candidate: dict[str, Any]) -> str:
    contract = {
        "prompt_version": candidate.get("prompt_version"),
        "system_prompt_sha256": candidate.get("system_prompt_sha256"),
        "response_schema_sha256": candidate.get("response_schema_sha256"),
    }
    if candidate.get("response_schema_instance_policy") is not None:
        contract["response_schema_instance_policy"] = candidate.get(
            "response_schema_instance_policy"
        )
    if candidate.get("analysis_schema") is not None:
        contract["analysis_schema"] = candidate.get("analysis_schema")
        contract["analysis_schema_sha256"] = candidate.get("analysis_schema_sha256")
    if candidate.get("supplemental_analysis_schema") is not None:
        contract["supplemental_analysis_schema"] = candidate.get(
            "supplemental_analysis_schema"
        )
        contract["supplemental_analysis_schema_sha256"] = candidate.get(
            "supplemental_analysis_schema_sha256"
        )
    if candidate.get("entry_setup_evidence_schema") is not None:
        contract["entry_setup_evidence_schema"] = candidate.get(
            "entry_setup_evidence_schema"
        )
        contract["entry_setup_evidence_schema_sha256"] = candidate.get(
            "entry_setup_evidence_schema_sha256"
        )
        contract["entry_setup_evidence_version"] = candidate.get(
            "entry_setup_evidence_version"
        )
        contract["entry_decision_composer_version"] = candidate.get(
            "entry_decision_composer_version"
        )
        contract["entry_structure_phase_policy_version"] = candidate.get(
            "entry_structure_phase_policy_version"
        )
        contract["tail_risk_observation_contract_sha256"] = candidate.get(
            "tail_risk_observation_contract_sha256"
        )
    if candidate.get("semantic_validator_version") is not None:
        contract["semantic_validator_version"] = candidate.get(
            "semantic_validator_version"
        )
    if candidate.get("semantic_repair_version") is not None:
        contract["semantic_repair_version"] = candidate.get("semantic_repair_version")
    if candidate.get("exposure_semantics") is not None:
        contract["exposure_semantics"] = candidate.get("exposure_semantics")
    if candidate.get("learning_sample_floor") is not None:
        contract["learning_sample_floor"] = candidate.get("learning_sample_floor")
    if candidate.get("model_comparison") is not None:
        contract["model_comparison"] = candidate.get("model_comparison")
    return _sha256(contract)


def _openai_output_text(response: Any) -> str:
    direct = getattr(response, "output_text", None)
    if direct not in (None, ""):
        return str(direct)
    if isinstance(response, dict):
        direct = response.get("output_text")
        if direct not in (None, ""):
            return str(direct)
    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")
    parts: list[str] = []
    for item in output or []:
        content = getattr(item, "content", None)
        if content is None and isinstance(item, dict):
            content = item.get("content")
        for block in content or []:
            text_value = getattr(block, "text", None)
            if text_value is None and isinstance(block, dict):
                text_value = block.get("text")
            if text_value not in (None, ""):
                parts.append(str(text_value))
    return "\n".join(parts)


def _usage_value(value: Any, field: str) -> int | None:
    usage = getattr(value, "usage", None)
    if usage is None and isinstance(value, dict):
        usage = value.get("usage")
    raw = getattr(usage, field, None)
    if raw is None and isinstance(usage, dict):
        raw = usage.get(field)
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def execute_openai_prompt_v2_candidate(
    request: dict[str, Any],
    *,
    api_keys: list[str] | None = None,
    timeout_sec: float = 45.0,
) -> dict[str, Any]:
    """Run one exact-payload Prompt V2 candidate with no runtime authority."""

    if any(
        (
            request.get("runtime_effect") is not False,
            request.get("allowed_runtime_apply") is not False,
            request.get("actual_order_submitted") is not False,
            request.get("broker_order_forbidden") is not True,
        )
    ):
        raise ValueError("offline_authority_contract_invalid")
    control = request.get("control") or {}
    candidate = request.get("candidate") or {}
    provider = str(candidate.get("provider") or "").strip().lower()
    model = str(candidate.get("model") or "").strip()
    reasoning_effort = str(candidate.get("reasoning_effort") or "").strip().lower()
    control_provider = str(control.get("provider") or "").strip().lower()
    control_model = str(control.get("model") or "").strip()
    model_comparison = candidate.get("model_comparison")
    model_comparison = model_comparison if isinstance(model_comparison, dict) else {}
    model_comparison_allowed = bool(
        model_comparison.get("enabled") is True
        and model_comparison.get("decision_authority")
        == "offline_model_comparison_only"
        and model_comparison.get("baseline_model") == control_model
        and model_comparison.get("candidate_model") == model
        and str(model_comparison.get("baseline_reasoning_effort") or "")
        == str(control.get("reasoning_effort") or "")
        and str(model_comparison.get("candidate_reasoning_effort") or "")
        == reasoning_effort
        and model != control_model
    )
    if (
        provider != "openai"
        or provider != control_provider
        or (model != control_model and not model_comparison_allowed)
    ):
        raise ValueError("provider_or_model_control_mismatch")
    keys = list(api_keys or _offline_openai_api_keys())
    if not keys:
        raise RuntimeError("openai_api_key_unavailable")
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError("openai_sdk_unavailable") from exc

    pair_id = str(request.get("paired_replay_id") or "")
    key_index = int(hashlib.sha256(pair_id.encode("utf-8")).hexdigest(), 16) % len(keys)
    exact_payload = request.get("candidate_input", request.get("exact_payload"))
    user_input = (
        exact_payload
        if isinstance(exact_payload, str)
        else _canonical_bytes(exact_payload).decode("utf-8")
    )
    if not user_input:
        raise ValueError("exact_payload_missing")
    stage = str(request.get("stage") or "")
    instructions = str(candidate.get("system_prompt") or "")
    correction_errors = [
        str(value)
        for value in request.get("candidate_schema_correction_errors") or []
        if value
    ]
    if correction_errors:
        correction_rules = []
        setup_risk_candidate = bool(
            candidate.get("semantic_validator_version")
            == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
        )
        bounded_opportunity_candidate = bool(
            candidate.get("semantic_validator_version")
            == BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
        )
        clean_continuation_candidate = bool(
            str(candidate.get("prompt_version") or "")
            in {
                f"{DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION}_entry",
                f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry",
                f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry",
            }
        )
        candidate_prompt_version = str(candidate.get("prompt_version") or "")
        selective_recovery_candidate = candidate_prompt_version in {
            f"{DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION}_entry",
            f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry",
        }
        recovery_confirmation_candidate = bool(
            candidate_prompt_version
            == f"{DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION}_entry"
        )
        if "expected_edge_values_required" in correction_errors:
            correction_rules.append(
                "EDGE or NO_EDGE requires numeric expected_upside_pct and "
                "expected_downside_pct; do not return null. For BUY, downside "
                "must be strictly negative"
            )
        if "expected_upside_pct_negative" in correction_errors:
            correction_rules.append("expected_upside_pct must be zero or positive")
        if "expected_downside_pct_positive" in correction_errors:
            correction_rules.append("expected_downside_pct must be zero or negative")
        if "insufficient_data_expected_values_must_be_null" in correction_errors:
            correction_rules.append(
                "INSUFFICIENT_DATA requires null upside and downside"
            )
        if any(error.startswith("entry_") for error in correction_errors) and not (
            setup_risk_candidate
        ):
            if bounded_opportunity_candidate:
                correction_rules.append(
                    (
                        "For V2.13, EDGE/BUY is allowed only when either "
                        "clean_continuation_probe.eligible=true or "
                        "recovery_confirmation_probe.eligible=true, with truthful "
                        "after-cost reward/risk >=0.75. V2.12 selective recovery "
                        "alone is insufficient. Downstream guards remain mandatory"
                        if recovery_confirmation_candidate
                        else (
                            "For V2.12, EDGE/BUY is allowed only when either "
                            "clean_continuation_probe.eligible=true with truthful "
                            "after-cost reward/risk >=0.75 or "
                            "selective_recovery_probe.eligible=true with truthful "
                            "after-cost reward/risk >=1.00. Generic bounded opportunity "
                            "is insufficient. Downstream guards remain mandatory"
                            if selective_recovery_candidate
                            else (
                                "For the V2.11 clean_continuation_probe eligible "
                                "cohort, EDGE/BUY requires trigger=confirmed, "
                                "non-blocking low/moderate/high adverse risk, and "
                                "truthful after-cost reward/risk >=0.75. For other "
                                "rows keep the V2.10 >=1.00 floor. Downstream guards "
                                "remain mandatory"
                                if clean_continuation_candidate
                                else "For the V2.10 offline one-share probe only, "
                                "EDGE/BUY requires the deterministic "
                                "bounded_opportunity contract to be eligible, "
                                "trigger=confirmed, adverse_risk low/moderate/high "
                                "but never blocking, and after-cost reward/risk "
                                ">=1.00. Preserve high risk and adverse wide-spread "
                                "liquidity; downstream guards remain mandatory"
                            )
                        )
                    )
                )
            else:
                correction_rules.append(
                    "For entry: NO_EDGE requires DROP; INSUFFICIENT_DATA requires "
                    "WAIT with all four edge/risk evidence fields set to "
                    "insufficient; EDGE BUY requires a confirmed trigger, "
                    "low/moderate adverse risk, and reward/risk >= 1.25; EDGE WAIT "
                    "requires recovery_required and non-blocking risk; EDGE DROP "
                    "requires failed trigger, blocking risk, or reward/risk below "
                    "1.25"
                )
        if "entry_no_edge_requires_drop" in correction_errors:
            correction_rules.append(
                "Set action=DROP for NO_EDGE, with positive_edge none/weak and "
                "setup no_setup/not_applicable; do not retain WAIT"
            )
        if "entry_no_edge_strength_invalid" in correction_errors:
            correction_rules.append(
                "NO_EDGE requires positive_edge=none or weak. If the deterministic "
                "structural edge floor is true, use EDGE instead of weakening it"
            )
        if "entry_edge_strength_invalid" in correction_errors:
            correction_rules.append(
                "EDGE requires positive_edge=moderate or strong; otherwise use "
                "NO_EDGE/DROP only when the structural edge floor is not met"
            )
        if "entry_wait_adverse_risk_invalid" in correction_errors:
            correction_rules.append(
                "WAIT cannot carry insufficient adverse risk. Blocking current-entry "
                "risk may remain EDGE/WAIT only with trigger=recovery_required; it "
                "is observation-only and must not imply probe or submit authority. "
                "Use DROP when the setup failed or structure was invalidated"
            )
        if "entry_buy_adverse_risk_too_high" in correction_errors:
            correction_rules.append(
                (
                    "V2.10 offline bounded-opportunity BUY may retain high adverse "
                    "risk with confidence <=65 when the one-share probe contract "
                    "is eligible; blocking risk still requires DROP"
                    if bounded_opportunity_candidate
                    else "BUY cannot carry high or blocking adverse risk. Preserve "
                    "the observed risk: use DROP with blocking risk or unfavorable "
                    "numeric reward/risk, or WAIT only when the trigger is "
                    "recovery_required and risk is non-blocking"
                )
            )
        if "entry_buy_reward_risk_below_floor" in correction_errors:
            correction_rules.append(
                (
                    "For V2.10 offline bounded-opportunity BUY, subtract the "
                    "conservative execution cost and require adjusted reward/risk "
                    + (
                        ">=0.75 when clean_continuation_probe.eligible=true or "
                        "recovery_confirmation_probe.eligible=true; otherwise "
                        "BUY is not permitted"
                        if recovery_confirmation_candidate
                        else (
                            ">=0.75 only when clean_continuation_probe.eligible=true; "
                            "otherwise require >=1.00"
                            if clean_continuation_candidate
                            else ">=1.00; the inherited 1.25 full-entry floor does "
                            "not apply"
                        )
                    )
                    if bounded_opportunity_candidate
                    else "Do not retain BUY when expected_upside_pct divided by the "
                    "absolute strictly negative expected_downside_pct is below "
                    "1.25. Use DROP with risk_reward_unfavorable, or return a "
                    "supported non-BUY state"
                )
            )
        if (
            "entry_edge_drop_requires_failed_blocking_or_unfavorable"
            in correction_errors
        ):
            correction_rules.append(
                (
                    "For V2.13, EDGE/DROP still requires trigger=failed, "
                    "adverse_risk=blocking, or genuinely unfavorable numeric "
                    "reward/risk. BUY additionally requires clean_continuation_probe "
                    "or recovery_confirmation_probe eligibility and the 0.75 "
                    "after-cost floor. Otherwise preserve non-blocking structural "
                    "edge as WAIT with trigger=recovery_required"
                    if recovery_confirmation_candidate
                    else (
                        "For V2.12, EDGE/DROP still requires trigger=failed, "
                        "adverse_risk=blocking, or genuinely unfavorable numeric "
                        "reward/risk. BUY additionally requires "
                        "clean_continuation_probe or selective_recovery_probe "
                        "eligibility and its after-cost floor. Otherwise preserve "
                        "non-blocking structural edge as WAIT with "
                        "trigger=recovery_required"
                        if selective_recovery_candidate
                        else "EDGE/DROP requires trigger=failed, "
                        "adverse_risk=blocking, or numeric reward/risk below 1.25. "
                        "If none applies, use BUY for a confirmed "
                        "low/moderate-risk trigger or WAIT for a recovery_required "
                        "non-blocking trigger"
                    )
                )
            )
        if "entry_no_edge_setup_invalid" in correction_errors:
            correction_rules.append(
                "NO_EDGE requires setup=no_setup or not_applicable; do not use "
                "continuation, pullback_recovery, or reversal"
            )
        if "entry_structural_edge_floor_misclassified" in correction_errors:
            correction_rules.append(
                "The exact completed-bar returns/slopes meet the mandatory "
                "structural edge floor; return EDGE with moderate/strong "
                "positive_edge while assessing adverse risk separately"
            )
        if "entry_blocking_overextension_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload meets the blocking overextension contract; "
                "preserve EDGE but return DROP with blocking adverse risk"
            )
        if "entry_orderly_pullback_recovery_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload meets the orderly pullback-recovery contract; "
                "return EDGE/WAIT with pullback_recovery, recovery_required, and "
                "non-blocking adverse risk"
            )
        if "entry_bounded_reversal_probe_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload has a bounded early reversal: positive completed "
                "3m/5m/10m returns after a negative 20m return, accelerating "
                "momentum, tick acceleration >=1.5, and fresh quote/tick inputs. "
                "Return EDGE/WAIT with reversal, recovery_required, moderate/strong "
                "positive edge, and low/moderate/high adverse risk. Do not return "
                "BUY; downstream submit guards retain all execution authority"
            )
        if "entry_trusted_supportive_trigger_misclassified" in correction_errors:
            correction_rules.append(
                (
                    "The exact payload has trusted supportive aggressor tape plus "
                    "completed recovery and structural edge. Preserve EDGE with "
                    "moderate/strong positive_edge and tape=supportive. For V2.13, "
                    "recovery_confirmation_probe eligibility certifies this trusted "
                    "trigger plus sell-momentum deceleration. BUY still requires its "
                    "truthful 0.75 after-cost floor and non-blocking risk. Do not "
                    "invent blocking risk from ordinary ask-heavy depth when the "
                    "deterministic contract has no hard blocker"
                    if recovery_confirmation_candidate
                    else (
                        "The exact payload has trusted supportive aggressor tape plus "
                        "completed recovery and structural edge. Preserve EDGE with "
                        "moderate/strong positive_edge and tape=supportive. For V2.12, "
                        "BUY still requires clean_continuation_probe or "
                        "selective_recovery_probe eligibility and its after-cost "
                        "floor. Otherwise use WAIT with trigger=recovery_required "
                        "when risk is non-blocking; use DROP only for failed, "
                        "blocking, or genuinely unfavorable evidence. Keep adverse "
                        "depth in liquidity/risk"
                        if selective_recovery_candidate
                        else "The exact payload has trusted supportive aggressor "
                        "tape plus a completed 1m/3m recovery and structural edge. "
                        "Return EDGE with moderate/strong positive_edge, "
                        "tape=supportive, and trigger=confirmed. WAIT is prohibited "
                        "for this contract. Keep ask-heavy depth or a wide spread in "
                        "liquidity/adverse_risk. Return BUY when adverse_risk is "
                        "low/moderate and numeric reward/risk is at least 1.25; "
                        "otherwise return DROP with blocking risk or numeric "
                        "unfavorable reward/risk"
                    )
                )
            )
        if "entry_thin_tape_sample_overstated" in correction_errors:
            correction_rules.append(
                "The tape sample is too thin for supportive or confirmed evidence. "
                "For otherwise sufficient core data use tape=mixed; do not confirm "
                "the trigger, and include tape_sample_insufficient"
            )
        if "entry_adverse_distribution_misclassified" in correction_errors:
            correction_rules.append(
                "The completed-bar distribution meets the adverse no-edge "
                "contract. Return NO_EDGE/DROP with trend=adverse, setup=no_setup, "
                "trigger=failed or not_applicable, and include "
                "distribution_adverse and volume_confirmation_missing"
            )
        if "entry_ask_wall_wide_spread_misclassified" in correction_errors:
            correction_rules.append(
                "The spread and top1 ask wall meet the adverse liquidity contract. "
                "Use liquidity=adverse, adverse_risk=high or blocking, never BUY, "
                "and include ask_wall_adverse"
            )
        if "entry_trigger_reason_evidence_conflict" in correction_errors:
            correction_rules.append(
                "Make recovery reason codes exactly match evidence.trigger: "
                "confirmed uses only recovery_trigger_confirmed, "
                "recovery_required uses only recovery_trigger_required, and failed "
                "uses only recovery_trigger_failed"
            )
        if any(error.startswith("anticipatory_") for error in correction_errors):
            correction_rules.append(
                (
                    "Follow anticipatory_reversal_analysis_v1 source, spread, and "
                    "confidence facts. Under V2.10 use its bounded_opportunity "
                    "eligibility and adjusted reward/risk >=1.00; do not fall back "
                    "to the V2.9 reversal-only 1.25 floor"
                    if bounded_opportunity_candidate
                    else "For setup=reversal follow "
                    "anticipatory_reversal_analysis_v1. BUY only when "
                    "eligible_for_counterfactual_probe=true, use passive-probe "
                    "semantics, keep wide-but-observable liquidity adverse, honor "
                    "the degraded confidence cap, and require reward/risk >=1.25 "
                    "after conservative execution cost"
                )
            )
        if any(error.startswith("bounded_opportunity_") for error in correction_errors):
            correction_rules.append(
                "For V2.10, BUY is an offline one-share passive-probe label only. "
                "It requires bounded_opportunity.eligible_for_one_share_probe=true, "
                "normal or wide_but_observable spread, setup continuation, "
                "pullback_recovery, or reversal, confirmed bounded-opportunity "
                "trigger, non-blocking risk, and adjusted reward/risk >=1.00. "
                "Keep wide spread adverse and do not weaken high risk"
            )
        if any(
            error.startswith("clean_continuation_probe_") for error in correction_errors
        ):
            correction_rules.append(
                "For V2.11, clean_continuation_probe.eligible=true is the narrow "
                "deterministic no-blocker cohort selected for one-share "
                "exploration. Return EDGE/BUY with trigger=confirmed and "
                "non-blocking low/moderate/high risk only when your truthful "
                "after-cost magnitude ratio is >=0.75. Do not alter exact facts "
                "or claim that downstream submit guards have passed"
            )
        if any(error.startswith("selective_recovery_") for error in correction_errors):
            correction_rules.append(
                "For V2.12, BUY requires clean_continuation_probe.eligible=true or "
                "selective_recovery_probe.eligible=true. Selective recovery also "
                "requires truthful after-cost reward/risk >=1.00. Otherwise keep "
                "valid structural edge as WAIT/recovery_required unless evidence "
                "is failed, blocking, or unfavorable"
            )
        if any(
            error.startswith("recovery_confirmation_") for error in correction_errors
        ):
            correction_rules.append(
                "For V2.13, BUY requires clean_continuation_probe.eligible=true or "
                "recovery_confirmation_probe.eligible=true with truthful after-cost "
                "reward/risk >=0.75 and a strictly negative downside estimate. "
                "V2.12 selective recovery alone is insufficient. Confirmed recovery "
                "has trusted supportive tape plus sell-momentum deceleration; do not "
                "invent blocking risk without a deterministic hard blocker"
            )
        if any(error.startswith("holding_") for error in correction_errors):
            correction_rules.append(
                "For holding: read position_context and holding_decision_context "
                "by their exact paths. A positive observed quantity, average entry "
                "price, executable sell price, position_valid=true, and "
                "order_consistent=true are sufficient position evidence even when "
                "position_reconciled=false. Positive completed_bar_count plus a "
                "non-forming bar proves completed bars. fresh_consistent source, "
                "candle, and BBO prohibit stale/conflict/venue-mismatch reasons "
                "unless an explicit current conflict exists. TRIM requires at "
                "least two remaining shares. For one share, use HOLD when the "
                "continuation/recovery edge remains intact; use EXIT when NO_EDGE "
                "or invalidated structure aligns with high/blocking executable "
                "risk. Do not return INSUFFICIENT_DATA merely because TRIM is "
                "unavailable"
            )
        if any(error.startswith("holding_flow_") for error in correction_errors):
            correction_rules.append(
                "For holding-flow bounded defer: hard/protect/emergency or active "
                "sell-order guards require EXIT. HOLD or TRIM is permitted only "
                "when holding_exact_contract_facts_v1.bounded_defer_eligible=true. "
                "HOLD requires trigger=recovery_required and represents only an "
                "offline 30/60/90-second comparison inside allowed_worsen_pct; it "
                "does not delay a live exit or bypass any broker or safety guard"
            )
        if "reason_codes_conflict" in correction_errors:
            correction_rules.append(
                "Use at most one of edge_positive/edge_absent/no_positive_edge, at "
                "most one of risk_reward_favorable/risk_reward_unfavorable, and at "
                "most one recovery trigger code"
            )
        if setup_risk_candidate:
            correction_rules.append(
                "Return only the setup-risk adjudication schema. Copy fact IDs "
                "verbatim from entry_setup_evidence_v1, use PASS only with "
                "NO_BLOCKING_RISK, and do not add action, score, price, quantity, "
                "or invented evidence. READY permits PASS/CAUTION/VETO; "
                "WAIT_CONFIRMATION requires CAUTION/VETO with a contradicting "
                "fact; INVALID requires VETO with an invalidation fact; only "
                "INSUFFICIENT setup/source permits INSUFFICIENT with "
                "SOURCE_QUALITY_GAP. For READY, LIQUIDITY_FRAGILE, ADVERSE_TAPE, "
                "REWARD_RISK_WEAK, and "
                "CONFIRMATION_MISSING are bounded CAUTION risks, not structural "
                "blocking risks"
            )
            if candidate_prompt_version == (
                f"{DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION}_entry"
            ):
                correction_rules.append(
                    "For V2.15, never cite a contradiction or invalidation as a "
                    "supporting fact. A no_supported_setup-only distribution may "
                    "remain VETO while the deterministic composer retains only its "
                    "fresh bounded-recovery recheck path. WAIT_CONFIRMATION with "
                    "both liquidity_supportive and tape_supportive should cite both "
                    "positive facts and use CAUTION when no hard blocker exists"
                )
            if candidate_prompt_version == (
                f"{DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION}_entry"
            ):
                correction_rules.append(
                    "For V2.16, never cite a contradiction or invalidation as a "
                    "supporting fact. Retained recovery evidence creates only a "
                    "WAIT/recovery_required observation seed. Do not claim that a "
                    "later completed-bar, price, spread, cost, or sell-momentum "
                    "confirmation already exists in the current snapshot"
                )
            if (
                "entry_risk_invalid_setup_invalidation_fact_required"
                in correction_errors
            ):
                correction_rules.append(
                    "The ledger setup_state is INVALID. Set risk_verdict=VETO and "
                    "copy at least one exact string from "
                    "entry_setup_evidence_v1.invalidation_facts into "
                    "contradicting_fact_ids. A contradicting_facts-only citation "
                    "does not satisfy this requirement"
                )
            if "entry_risk_supporting_fact_ids_invented" in correction_errors:
                correction_rules.append(
                    "supporting_fact_ids may contain only exact IDs listed under "
                    "positive_facts. Never copy trigger_confirmation_missing, "
                    "liquidity_adverse, tape_adverse, or any other contradiction "
                    "into supporting_fact_ids; use an empty supporting array when "
                    "no positive fact is needed. Keep adverse IDs only in "
                    "contradicting_fact_ids"
                )
        instructions += (
            "\nCorrection retry: the prior response violated these contract fields: "
            + ",".join(correction_errors)
            + ". "
            + "; ".join(correction_rules)
            + ". Return one corrected JSON object only."
        )
    started = time.perf_counter()
    client = OpenAI(api_key=keys[key_index], max_retries=0)
    response_schema_name = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        str(candidate.get("prompt_version") or DECISION_QUALITY_V2_PROMPT_VERSION),
    )[:64]
    response_schema = _candidate_openai_schema(
        stage=stage,
        candidate=candidate,
        setup_evidence=request.get("entry_setup_evidence"),
    )
    response_schema_instance_sha256 = _sha256(response_schema)
    expected_schema_instance_sha256 = str(
        candidate.get("response_schema_instance_sha256") or ""
    )
    if (
        expected_schema_instance_sha256
        and expected_schema_instance_sha256 != response_schema_instance_sha256
    ):
        raise ValueError("candidate_response_schema_instance_hash_mismatch")
    response_kwargs: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": user_input,
        "text": {
            "format": {
                "type": "json_schema",
                "name": response_schema_name,
                "strict": True,
                "schema": response_schema,
            },
            "verbosity": "low",
        },
        "store": False,
        "metadata": {
            "paired_replay_id": pair_id,
            "decision_stage": stage,
            "candidate_prompt_version": str(
                candidate.get("prompt_version") or DECISION_QUALITY_V2_PROMPT_VERSION
            ),
            "candidate_contract_sha256": str(
                candidate.get("contract_sha256")
                or _candidate_contract_sha256(candidate)
            ),
            "candidate_input_sha256": str(request.get("candidate_input_sha256") or ""),
            "runtime_effect": "false",
        },
        "timeout": max(1.0, float(timeout_sec)),
    }
    if reasoning_effort:
        response_kwargs["reasoning"] = {"effort": reasoning_effort}
    response = client.responses.create(**response_kwargs)
    raw_text = _openai_output_text(response)
    parse_error = ""
    try:
        payload = json.loads(raw_text)
    except Exception:
        payload = {}
        parse_error = "candidate_response_json_invalid"
    if not isinstance(payload, dict):
        payload = {}
        parse_error = "candidate_response_not_object"
    response_id = getattr(response, "id", None)
    if response_id is None and isinstance(response, dict):
        response_id = response.get("id")
    return {
        "candidate_response": payload,
        "provider_provenance": {
            "provider": "openai",
            "model": model,
            "reasoning_effort": reasoning_effort or None,
            "transport": "openai_responses_http_offline",
            "response_id": str(response_id or "") or None,
            "response_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "input_tokens": _usage_value(response, "input_tokens"),
            "output_tokens": _usage_value(response, "output_tokens"),
            "total_tokens": _usage_value(response, "total_tokens"),
            "provider_none": False,
            "store": False,
            "failback_chain": [],
            "parse_error": parse_error or None,
            "response_schema_instance_sha256": response_schema_instance_sha256,
        },
    }


def _candidate_envelope(
    value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(value.get("candidate_response"), dict):
        return (
            dict(value["candidate_response"]),
            dict(value.get("provider_provenance") or {}),
        )
    return dict(value), {}


def _successful_candidate_result_model(result: dict[str, Any]) -> str:
    attempts = result.get("candidate_attempts") or []
    for attempt in reversed(attempts):
        if not isinstance(attempt, dict):
            continue
        provenance = attempt.get("provider_provenance")
        if isinstance(provenance, dict) and provenance.get("model"):
            return str(provenance["model"])
    return ""


def validate_model_comparison_baseline(
    requests: list[dict[str, Any]],
    baseline_report: dict[str, Any],
) -> list[str]:
    if not requests:
        return ["model_comparison_requests_missing"]
    first_comparison = (requests[0].get("candidate") or {}).get("model_comparison")
    first_comparison = first_comparison if isinstance(first_comparison, dict) else {}
    baseline_model = str(first_comparison.get("baseline_model") or "")
    if not baseline_model:
        return ["model_comparison_baseline_model_missing"]
    expected_baseline_effort = str(
        first_comparison.get("baseline_reasoning_effort") or ""
    )
    baseline_request_models = {
        str((row.get("candidate") or {}).get("model") or "")
        for row in baseline_report.get("requests") or []
        if isinstance(row, dict)
    }
    baseline_request_efforts = {
        str((row.get("candidate") or {}).get("reasoning_effort") or "")
        for row in baseline_report.get("requests") or []
        if isinstance(row, dict)
    }
    baseline_results = {
        str(row.get("decision_trace_id") or ""): row
        for row in baseline_report.get("results") or []
        if isinstance(row, dict) and row.get("status") == "pass"
    }
    errors: list[str] = []
    if not baseline_report:
        errors.append("model_comparison_baseline_report_missing")
    if baseline_request_models != {baseline_model}:
        errors.append("model_comparison_baseline_report_model_mismatch")
    if baseline_request_efforts != {expected_baseline_effort}:
        errors.append("model_comparison_baseline_report_reasoning_effort_mismatch")
    for request in requests:
        trace_id = str(request.get("decision_trace_id") or "")
        result = baseline_results.get(trace_id)
        if not result:
            errors.append(f"baseline_pass_result_missing:{trace_id}")
            continue
        if _successful_candidate_result_model(result) != baseline_model:
            errors.append(f"baseline_provider_model_mismatch:{trace_id}")
        expected_values = {
            "payload_sha256": request.get("payload_sha256"),
            "candidate_prompt_sha256": (request.get("candidate") or {}).get(
                "system_prompt_sha256"
            ),
            "candidate_input_sha256": request.get("candidate_input_sha256"),
            "exact_payload_analysis_sha256": request.get(
                "exact_payload_analysis_sha256"
            ),
            "anticipatory_reversal_analysis_sha256": request.get(
                "anticipatory_reversal_analysis_sha256"
            ),
        }
        for key, expected in expected_values.items():
            if result.get(key) != expected:
                errors.append(f"baseline_{key}_mismatch:{trace_id}")
    return list(dict.fromkeys(errors))


def prepare_paired_replay_requests(
    *,
    control_manifest: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if (
        control_manifest.get("status")
        != "control_manifest_frozen_collect_exact_samples"
    ):
        return []
    controls = {
        str(row.get("endpoint") or ""): row
        for row in control_manifest.get("controls") or []
        if isinstance(row, dict) and row.get("endpoint")
    }
    label_by_trace = {
        str(row.get("decision_trace_id")): row
        for row in labels
        if row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
        and _primary_metric(row) is not None
    }
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    requests = []
    for trace in traces:
        trace_id = str(trace.get("decision_trace_id") or "")
        label = label_by_trace.get(trace_id)
        endpoint = _trace_endpoint(trace)
        payload = _payload_for_trace(
            trace,
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        if (
            not label
            or not payload
            or not trace.get("payload_replay_exact")
            or payload.get("replay_exact") is not True
            or label.get("primary_cohort_eligible") is not True
        ):
            continue
        stage = _stage(trace.get("decision_stage"), trace.get("endpoint"))
        if stage == "unknown":
            continue
        control = controls.get(endpoint)
        if not control:
            continue
        signature_fields = (
            ("prompt_version", "prompt_version"),
            ("prompt_sha256", "prompt_sha256"),
            ("provider_actual", "provider_actual"),
            ("model", "model"),
            ("request_temperature", "request_temperature"),
            ("request_reasoning_effort", "request_reasoning_effort"),
        )
        if any(
            trace.get(trace_key) != control.get(control_key)
            for trace_key, control_key in signature_fields
        ):
            continue
        candidate_prompt = (
            decision_quality_holding_v2_3_system_prompt()
            if stage == "holding"
            else decision_quality_v2_system_prompt(stage)
        )
        replay_payload = _replay_exact_payload(replay_source_input(payload))
        if not isinstance(replay_payload, dict):
            continue
        candidate = {
            "prompt_version": (
                DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION
                if stage == "holding"
                else f"{DECISION_QUALITY_V2_PROMPT_VERSION}_{stage}"
            ),
            "system_prompt": candidate_prompt,
            "system_prompt_sha256": _sha256(candidate_prompt),
            "response_schema": DECISION_QUALITY_V2_RESPONSE_SCHEMA,
            "response_schema_sha256": _sha256(DECISION_QUALITY_V2_RESPONSE_SCHEMA),
            "provider": trace.get("provider_actual"),
            "model": trace.get("model"),
            "temperature": trace.get("request_temperature"),
            "reasoning_effort": trace.get("request_reasoning_effort"),
        }
        if stage == "holding":
            candidate["semantic_validator_version"] = HOLDING_SEMANTIC_VALIDATOR_VERSION
        candidate["contract_sha256"] = _candidate_contract_sha256(candidate)
        request = {
            "paired_replay_id": f"pair-{_sha256((trace_id, trace.get('payload_sha256')))[:24]}",
            "decision_trace_id": trace_id,
            "decision_ts": trace.get("decision_ts") or label.get("decision_ts"),
            "stage": stage,
            "stock_code": label.get("stock_code"),
            "effective_venue": trace.get("effective_venue"),
            "session_bucket": trace.get("session_bucket"),
            "reference_price_type": trace.get("reference_price_type"),
            "reference_price": trace.get("reference_price"),
            "best_bid": trace.get("best_bid"),
            "best_ask": trace.get("best_ask"),
            "payload_sha256": trace.get("payload_sha256"),
            "request_envelope_sha256": trace.get("request_envelope_sha256"),
            "endpoint": endpoint,
            "exact_payload": replay_payload,
            "control": {
                "prompt_version": control.get("prompt_version"),
                "prompt_sha256": control.get("prompt_sha256"),
                "provider": control.get("provider_actual"),
                "model": control.get("model"),
                "temperature": control.get("request_temperature"),
                "reasoning_effort": control.get("request_reasoning_effort"),
                "captured_action": trace.get("action"),
                "captured_score": trace.get("score"),
                "captured_reason": trace.get("reason"),
                "captured_edge_state": trace.get("decision_quality_model_edge_state"),
                "captured_evidence": trace.get("decision_quality_model_evidence"),
                "captured_entry_probe_intent": trace.get("entry_probe_intent"),
                "captured_entry_probe_intent_status": trace.get(
                    "entry_probe_intent_status"
                ),
                "captured_entry_probe_intent_eligibility_path": trace.get(
                    "entry_probe_intent_eligibility_path"
                ),
                "captured_entry_probe_intent_after_cost_reward_risk": trace.get(
                    "entry_probe_intent_after_cost_reward_risk"
                ),
            },
            "candidate": candidate,
            "outcome_join_key": label.get("label_id"),
            **OFFLINE_CONTRACT,
        }
        if stage == "holding":
            candidate_input = {
                "exact_payload": replay_payload,
                "holding_exact_contract_facts_v1": _holding_contract_facts(
                    replay_payload
                ),
            }
            request["candidate_input"] = candidate_input
            request["candidate_input_sha256"] = _sha256(candidate_input)
        requests.append(request)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        grouped[
            (
                str(request.get("stage") or "unknown"),
                str(request.get("effective_venue") or "UNKNOWN"),
                str(request.get("session_bucket") or "UNKNOWN"),
            )
        ].append(request)
    for rows in grouped.values():
        symbol_count = len(
            {
                _normalize_stock_code(row.get("stock_code"))
                for row in rows
                if _normalize_stock_code(row.get("stock_code"))
            }
        )
        promotion_evidence_pass = (
            len(rows) >= PAIRED_REPLAY_MIN_ROWS
            and symbol_count >= PAIRED_REPLAY_MIN_SYMBOLS
        )
        learning_update_pass = (
            len(rows) >= PAIRED_LEARNING_MIN_ROWS
            and symbol_count >= PAIRED_LEARNING_MIN_SYMBOLS
        )
        for row in rows:
            row["sample_floor"] = {
                "decision_rows": len(rows),
                "unique_symbols": symbol_count,
                "required_decision_rows": PAIRED_LEARNING_MIN_ROWS,
                "required_unique_symbols": PAIRED_LEARNING_MIN_SYMBOLS,
                "pass": learning_update_pass,
                "floor_role": "cumulative_learning_update_only",
                "promotion_authority": False,
                "promotion_evidence_floor": {
                    "decision_rows": len(rows),
                    "unique_symbols": symbol_count,
                    "required_decision_rows": PAIRED_REPLAY_MIN_ROWS,
                    "required_unique_symbols": PAIRED_REPLAY_MIN_SYMBOLS,
                    "pass": promotion_evidence_pass,
                },
            }
    return requests


def recover_same_trace_outcome_labels_from_paired_reports(
    *,
    target_date: str,
    labels: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    report_paths: list[Path],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Recover primary-horizon outcomes without reconstructing exact inputs.

    This is an explicit offline replay compatibility path for a historical day
    whose route-qualified completed-bar label materialization is no longer
    reproducible from the retained raw window.  Only the outcome summary from a
    prior same-trace paired report is reused.  The current immutable exact trace
    and payload stores still own candidate input preparation.
    """

    trace_by_id = {
        str(row.get("decision_trace_id") or ""): row
        for row in traces
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    current_by_trace: dict[str, dict[str, Any]] = {}
    label_order: list[str] = []
    anonymous_labels: list[dict[str, Any]] = []
    for row in labels:
        trace_id = str(row.get("decision_trace_id") or "")
        if not trace_id:
            anonymous_labels.append(row)
            continue
        if trace_id not in current_by_trace:
            label_order.append(trace_id)
        current_by_trace[trace_id] = row

    excluded = Counter()
    source_metadata: list[dict[str, Any]] = []
    candidates_by_trace: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for raw_path in report_paths:
        path = Path(raw_path).resolve()
        try:
            raw_bytes = path.read_bytes()
            report = json.loads(raw_bytes)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            excluded["source_report_unreadable"] += 1
            source_metadata.append(
                {
                    "path": str(path),
                    "status": "rejected_source_report_unreadable",
                }
            )
            continue
        if not isinstance(report, dict):
            excluded["source_report_not_object"] += 1
            source_metadata.append(
                {
                    "path": str(path),
                    "status": "rejected_source_report_not_object",
                }
            )
            continue
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        source_meta = {
            "path": str(path),
            "sha256": source_hash,
            "target_date": report.get("target_date"),
            "outcome_price_source": report.get("outcome_price_source"),
            "paired_comparable_count": report.get("paired_comparable_count"),
        }
        comparisons = report.get("paired_comparisons")
        comparisons = comparisons if isinstance(comparisons, list) else []
        authority_valid = (
            target_date >= "2026-06-05"
            and report.get("schema") in {PAIRED_SCHEMA, DETAILED_PAIRED_SCHEMA}
            and report.get("target_date") == target_date
            and report.get("runtime_effect") is False
            and report.get("allowed_runtime_apply") is False
            and report.get("actual_order_submitted") is False
            and report.get("broker_order_forbidden") is True
            and report.get("source_quality_gate")
            == OFFLINE_CONTRACT["source_quality_gate"]
            and report.get("paired_comparable_count") == len(comparisons)
            and len(comparisons) > 0
            and "kiwoom_completed_1m" in str(report.get("outcome_price_source") or "")
        )
        if not authority_valid:
            excluded["source_report_contract_invalid"] += 1
            source_meta["status"] = "rejected_source_report_contract_invalid"
            source_metadata.append(source_meta)
            continue

        requests_by_trace = {
            str(row.get("decision_trace_id") or ""): row
            for row in report.get("requests") or []
            if isinstance(row, dict) and row.get("decision_trace_id")
        }
        route_provenance = [
            row
            for row in report.get("price_source_provenance") or []
            if isinstance(row, dict)
            and str(row.get("source_quality_status") or "").startswith("pass")
            and not row.get("fetch_error")
        ]
        accepted_from_source = 0
        for comparison in comparisons:
            if not isinstance(comparison, dict):
                excluded["comparison_not_object"] += 1
                continue
            trace_id = str(comparison.get("decision_trace_id") or "")
            source_request = requests_by_trace.get(trace_id)
            trace = trace_by_id.get(trace_id)
            if not source_request or not trace:
                excluded["same_trace_not_available"] += 1
                continue
            stage = _stage(comparison.get("stage"), trace.get("decision_stage"))
            horizon = PRIMARY_HORIZON_BY_STAGE.get(stage)
            payload_hash = str(trace.get("payload_sha256") or "")
            payload = _payload_for_trace(
                trace,
                payload_by_key=payload_by_key,
                payload_by_unique_hash=payload_by_unique_hash,
            )
            current_exact_payload_sha256 = (
                _sha256(_replay_exact_payload(replay_source_input(payload)))
                if isinstance(payload, dict)
                else ""
            )
            if (
                not horizon
                or trace.get("payload_replay_exact") is not True
                or not payload
                or payload.get("replay_exact") is not True
                or str(source_request.get("payload_sha256") or "") != payload_hash
                or str(source_request.get("source_exact_payload_sha256") or "")
                != current_exact_payload_sha256
                or source_request.get("candidate_exact_payload_sha256")
                not in (None, "", current_exact_payload_sha256)
            ):
                excluded["exact_trace_payload_contract_mismatch"] += 1
                continue
            stock_code = _normalize_stock_code(
                comparison.get("stock_code") or source_request.get("stock_code")
            )
            venue = _venue(comparison.get("effective_venue"))
            session = _session(comparison.get("session_bucket"))
            if (
                not stock_code
                or venue != _venue(source_request.get("effective_venue"))
                or venue != _venue(trace.get("effective_venue"))
                or session != _session(source_request.get("session_bucket"))
                or session != _session(trace.get("session_bucket"))
            ):
                excluded["same_route_contract_mismatch"] += 1
                continue
            route_pass = any(
                _normalize_stock_code(row.get("stock_code")) == stock_code
                and _venue(row.get("effective_venue")) == venue
                and _session(row.get("session_bucket")) == session
                for row in route_provenance
            )
            if not route_pass:
                excluded["route_price_provenance_missing"] += 1
                continue
            outcome = _number(comparison.get("outcome_return_pct"))
            mfe = _number(comparison.get("outcome_mfe_pct"))
            mae = _number(comparison.get("outcome_mae_pct"))
            if outcome is None or mfe is None or mae is None:
                excluded["primary_outcome_metric_missing"] += 1
                continue
            metric = {
                "end_return_pct": outcome,
                "mfe_pct": mfe,
                "mae_pct": mae,
                "first_hit": comparison.get("first_hit"),
                "entry_path_first_hit": comparison.get("entry_path_first_hit"),
                "entry_path_target_pct": comparison.get("entry_path_target_pct"),
                "entry_path_adverse_pct": comparison.get("entry_path_adverse_pct"),
                "profit_opportunity_threshold_pct": comparison.get(
                    "profit_opportunity_threshold_pct"
                ),
                "profit_opportunity_observed": comparison.get(
                    "profit_opportunity_observed"
                ),
                "profit_opportunity_hit_at": comparison.get(
                    "profit_opportunity_hit_at"
                ),
                "below_reference_excursion_at": comparison.get(
                    "below_reference_excursion_at"
                ),
                "profit_opportunity_sequence": comparison.get(
                    "profit_opportunity_sequence"
                ),
                "pre_profit_mae_pct": comparison.get("pre_profit_mae_pct"),
            }
            candidates_by_trace[trace_id].append(
                {
                    "schema": "ai_decision_outcome_label_v1",
                    "label_id": source_request.get("outcome_join_key")
                    or f"{trace_id}:recovered-primary",
                    "decision_trace_id": trace_id,
                    "decision_stage": stage,
                    "decision_ts": trace.get("decision_ts"),
                    "stock_code": stock_code,
                    "effective_venue": trace.get("effective_venue"),
                    "session_bucket": trace.get("session_bucket"),
                    "action": comparison.get("control_action"),
                    "label_status": "partial",
                    "matured_horizons_min": [int(horizon.removesuffix("m"))],
                    "pending_horizons_min": [
                        value
                        for value in HORIZONS_MIN
                        if value != int(horizon.removesuffix("m"))
                    ],
                    "horizon_metrics": {horizon: metric},
                    "source_quality_status": "pass",
                    "invalid_reasons": [],
                    "primary_cohort_eligible": True,
                    "outcome_recovery": {
                        "schema": PAIRED_OUTCOME_RECOVERY_SCHEMA,
                        "source_report_path": str(path),
                        "source_report_sha256": source_hash,
                        "source_outcome_price_source": report.get(
                            "outcome_price_source"
                        ),
                        "same_trace_payload_hash_confirmed": True,
                        "same_venue_session_confirmed": True,
                        "outcome_only_reuse": True,
                        "exact_payload_reconstructed": False,
                    },
                    **OFFLINE_CONTRACT,
                }
            )
            accepted_from_source += 1
        source_meta["status"] = "accepted_outcome_evidence_source"
        source_meta["accepted_comparison_count"] = accepted_from_source
        source_metadata.append(source_meta)

    recovered_count = 0
    replaced_current_count = 0
    current_metric_conflict_count = 0
    for trace_id, recovered_rows in candidates_by_trace.items():
        current = current_by_trace.get(trace_id)
        metric_hashes = {
            _sha256(signature)
            for row in recovered_rows
            if (signature := _paired_outcome_recovery_signature(_primary_metric(row)))
        }
        if len(metric_hashes) != 1:
            excluded["conflicting_recovered_outcome"] += 1
            continue
        recovered = recovered_rows[0]
        if isinstance(current, dict) and _primary_metric(current) is not None:
            replaced_current_count += 1
            current_signature = _paired_outcome_recovery_signature(
                _primary_metric(current)
            )
            if not current_signature or _sha256(current_signature) not in metric_hashes:
                current_metric_conflict_count += 1
        if trace_id not in current_by_trace:
            label_order.append(trace_id)
        current_by_trace[trace_id] = recovered
        recovered_count += 1

    merged = anonymous_labels + [
        current_by_trace[trace_id]
        for trace_id in label_order
        if trace_id in current_by_trace
    ]
    metadata = {
        "schema": PAIRED_OUTCOME_RECOVERY_SCHEMA,
        "status": (
            "recovered_same_trace_primary_outcomes"
            if recovered_count
            else "no_primary_outcome_recovered"
        ),
        "target_date": target_date,
        "requested_source_report_count": len(report_paths),
        "accepted_source_report_count": sum(
            row.get("status") == "accepted_outcome_evidence_source"
            for row in source_metadata
        ),
        "recovered_label_count": recovered_count,
        "replaced_current_label_count": replaced_current_count,
        "current_primary_metric_conflict_count": current_metric_conflict_count,
        "excluded_counts": dict(excluded),
        "sources": source_metadata,
        "outcome_only_reuse": True,
        "exact_payload_reconstructed": False,
        **OFFLINE_CONTRACT,
    }
    return merged, metadata


def prepare_detailed_paired_replay_requests(
    requests: list[dict[str, Any]],
    *,
    candidate_prompt_version: str = DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    candidate_model_override: str | None = None,
) -> list[dict[str, Any]]:
    """Attach a deterministic analysis ledger to the same exact payload."""

    supported_prompt_versions = {
        DECISION_QUALITY_DETAILED_PROMPT_VERSION,
        DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION,
        DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION,
        DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION,
        DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
        DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
        DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
        DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
        DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
    }
    if candidate_prompt_version not in supported_prompt_versions:
        raise ValueError("unsupported_detailed_candidate_prompt_version")
    if candidate_model_override and not re.fullmatch(
        r"[a-z0-9][a-z0-9._-]{0,127}",
        candidate_model_override,
    ):
        raise ValueError("invalid_offline_candidate_model_override")
    detailed_requests: list[dict[str, Any]] = []
    for request in requests:
        exact_payload = _replay_exact_payload(request.get("exact_payload"))
        if not isinstance(exact_payload, dict):
            continue
        stage = str(request.get("stage") or "")
        if stage != "entry":
            sample_floor = request.get("sample_floor")
            sample_floor = sample_floor if isinstance(sample_floor, dict) else {}
            detailed_requests.append(
                {
                    **request,
                    "detailed_analysis_exclusion_reason": (
                        "detailed_analysis_stage_not_implemented"
                    ),
                    "sample_floor": {
                        **sample_floor,
                        "pass": False,
                        "detailed_analysis_stage_supported": False,
                    },
                }
            )
            continue
        analysis = build_exact_payload_analysis_v1(exact_payload, stage=stage)
        candidate_input = {
            "exact_payload": exact_payload,
            EXACT_PAYLOAD_ANALYSIS_SCHEMA: analysis,
        }
        anticipatory_analysis: dict[str, Any] | None = None
        if candidate_prompt_version in {
            DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION,
            DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION,
            DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
            DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
            DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
            DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
            DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
        }:
            if candidate_prompt_version in {
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
            }:
                anticipatory_analysis = build_v2_13_recovery_confirmation_analysis_v1(
                    exact_payload,
                    stage=stage,
                )
            else:
                anticipatory_analysis = build_anticipatory_reversal_analysis_v1(
                    exact_payload,
                    stage=stage,
                )
            if (
                candidate_prompt_version
                == DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION
            ):
                anticipatory_analysis = _attach_selective_recovery_probe_contract_v1(
                    anticipatory_analysis
                )
            candidate_input[ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA] = (
                anticipatory_analysis
            )
            if (
                candidate_prompt_version
                == DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_16_sequential_recovery_system_prompt(stage)
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_15_bounded_recovery_system_prompt(stage)
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_14_setup_risk_adjudicator_system_prompt(
                    stage
                )
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_13_recovery_confirmation_system_prompt(
                    stage
                )
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_12_selective_recovery_system_prompt(stage)
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_11_clean_continuation_system_prompt(stage)
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_10_bounded_opportunity_system_prompt(stage)
            elif (
                candidate_prompt_version
                == DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION
            ):
                prompt = decision_quality_v2_9_1_anticipatory_system_prompt(stage)
            else:
                prompt = decision_quality_v2_9_anticipatory_system_prompt(stage)
        elif candidate_prompt_version == DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION:
            prompt = decision_quality_v2_8_detailed_system_prompt(stage)
        else:
            prompt = decision_quality_v2_detailed_system_prompt(stage)
        original_candidate = request.get("candidate")
        original_candidate = (
            original_candidate if isinstance(original_candidate, dict) else {}
        )
        candidate = {
            **original_candidate,
            "prompt_version": f"{candidate_prompt_version}_{stage}",
            "system_prompt": prompt,
            "system_prompt_sha256": _sha256(prompt),
            "analysis_schema": EXACT_PAYLOAD_ANALYSIS_SCHEMA,
            "analysis_schema_sha256": _sha256(EXACT_PAYLOAD_ANALYSIS_SCHEMA),
        }
        entry_setup_evidence: dict[str, Any] | None = None
        if candidate_prompt_version in {
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
            DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
            DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
        }:
            entry_setup_evidence = build_entry_setup_evidence(
                exact_payload=exact_payload,
                exact_analysis=analysis,
                recovery_analysis=anticipatory_analysis,
            )
            candidate_input[ENTRY_SETUP_EVIDENCE_SCHEMA] = entry_setup_evidence
            constrained_response_schema = entry_risk_adjudication_openai_schema(
                entry_setup_evidence
            )
            response_schema_template = entry_risk_adjudication_openai_schema()
            candidate.update(
                {
                    "response_schema": response_schema_template,
                    "response_schema_sha256": _sha256(response_schema_template),
                    "response_schema_instance_policy": "exact_fact_role_enum_v1",
                    "response_schema_instance_sha256": _sha256(
                        constrained_response_schema
                    ),
                    "semantic_validator_version": (
                        ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
                    ),
                    "entry_setup_evidence_schema": ENTRY_SETUP_EVIDENCE_SCHEMA,
                    "entry_setup_evidence_schema_sha256": _sha256(
                        ENTRY_SETUP_EVIDENCE_SCHEMA
                    ),
                    "entry_setup_evidence_version": ENTRY_SETUP_EVIDENCE_VERSION,
                    "entry_decision_composer_version": (
                        ENTRY_DECISION_COMPOSER_V2_16_VERSION
                        if candidate_prompt_version
                        == DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION
                        else (
                            ENTRY_DECISION_COMPOSER_V2_15_VERSION
                            if candidate_prompt_version
                            == DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
                            else ENTRY_DECISION_COMPOSER_VERSION
                        )
                    ),
                    "entry_structure_phase_policy_version": (
                        STRUCTURE_PHASE_POLICY_VERSION
                    ),
                    "tail_risk_observation_contract_sha256": _sha256(
                        TAIL_RISK_OBSERVATION_CONTRACT
                    ),
                    "exposure_semantics": ("offline_counterfactual_passive_probe_only"),
                }
            )
        if candidate_model_override:
            baseline_model = str(original_candidate.get("model") or "").strip()
            if not baseline_model:
                raise ValueError("offline_model_comparison_baseline_model_missing")
            if candidate_model_override == baseline_model:
                raise ValueError("offline_candidate_model_matches_baseline")
            baseline_reasoning_effort = str(
                original_candidate.get("reasoning_effort") or ""
            ).strip()
            candidate_reasoning_effort = baseline_reasoning_effort
            reasoning_compatibility_mapping = "exact"
            if (
                candidate_model_override == "gpt-5-nano"
                and baseline_reasoning_effort in {"", "none"}
            ):
                candidate_reasoning_effort = "minimal"
                reasoning_compatibility_mapping = "none_to_minimal"
            candidate["model"] = candidate_model_override
            candidate["reasoning_effort"] = candidate_reasoning_effort
            candidate["model_comparison"] = {
                "enabled": True,
                "baseline_model": baseline_model,
                "candidate_model": candidate_model_override,
                "baseline_reasoning_effort": baseline_reasoning_effort or None,
                "candidate_reasoning_effort": candidate_reasoning_effort or None,
                "reasoning_compatibility_mapping": (reasoning_compatibility_mapping),
                "decision_authority": "offline_model_comparison_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        if anticipatory_analysis is not None:
            candidate.update(
                {
                    "supplemental_analysis_schema": (
                        ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA
                    ),
                    "supplemental_analysis_schema_sha256": _sha256(
                        ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA
                    ),
                    "semantic_validator_version": (
                        ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
                        if candidate_prompt_version
                        in {
                            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                            DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                            DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
                        }
                        else (
                            BOUNDED_OPPORTUNITY_SEMANTIC_VALIDATOR_VERSION
                            if candidate_prompt_version
                            in {
                                DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
                                DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
                                DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
                                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
                            }
                            else ANTICIPATORY_SEMANTIC_VALIDATOR_VERSION
                        )
                    ),
                    "exposure_semantics": ("offline_counterfactual_passive_probe_only"),
                    "learning_sample_floor": {
                        "decision_rows": ANTICIPATORY_LEARNING_MIN_ROWS,
                        "unique_symbols": ANTICIPATORY_LEARNING_MIN_SYMBOLS,
                        "role": "start_or_update_cumulative_observation",
                        "promotion_authority": False,
                    },
                }
            )
            if (
                candidate_prompt_version
                == DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION
            ):
                candidate["semantic_repair_version"] = (
                    ANTICIPATORY_SEMANTIC_REPAIR_VERSION
                )
            elif candidate_prompt_version in {
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
            }:
                candidate["semantic_repair_version"] = (
                    ENTRY_RISK_ADJUDICATION_REPAIR_VERSION
                )
            elif candidate_prompt_version in {
                DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
                DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
                DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
            }:
                candidate["semantic_repair_version"] = (
                    BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION
                )
        candidate["contract_sha256"] = _candidate_contract_sha256(candidate)
        sample_floor = request.get("sample_floor")
        sample_floor = sample_floor if isinstance(sample_floor, dict) else {}
        if anticipatory_analysis is not None:
            promotion_evidence_floor = sample_floor.get("promotion_evidence_floor")
            promotion_evidence_floor = (
                dict(promotion_evidence_floor)
                if isinstance(promotion_evidence_floor, dict)
                else dict(sample_floor)
            )
            sample_floor = {
                **sample_floor,
                "promotion_evidence_floor": promotion_evidence_floor,
                "required_decision_rows": ANTICIPATORY_LEARNING_MIN_ROWS,
                "required_unique_symbols": ANTICIPATORY_LEARNING_MIN_SYMBOLS,
                "pass": True,
                "floor_role": "cumulative_learning_update_only",
                "promotion_authority": False,
            }
            if candidate_prompt_version in {
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
            }:
                sample_floor["promotion_evidence_floor"] = {
                    "candidate_exposure_decision_rows": (
                        PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
                    ),
                    "candidate_exposure_unique_symbols": (
                        PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
                    ),
                    "pass": None,
                    "evaluation_stage": "post_candidate_exposure_outcome_join",
                    "promotion_authority": False,
                }
        detailed_requests.append(
            {
                **request,
                "paired_replay_id": (
                    str(request.get("paired_replay_id") or "").replace(
                        "pair-", "detailed-pair-", 1
                    )
                    + (
                        f"-model-{_sha256(candidate_model_override)[:8]}"
                        if candidate_model_override
                        else ""
                    )
                ),
                "exact_payload_analysis": analysis,
                "exact_payload_analysis_sha256": analysis["analysis_sha256"],
                "anticipatory_reversal_analysis": anticipatory_analysis,
                "anticipatory_reversal_analysis_sha256": (
                    anticipatory_analysis.get("analysis_sha256")
                    if anticipatory_analysis is not None
                    else None
                ),
                "entry_setup_evidence": entry_setup_evidence,
                "entry_setup_evidence_sha256": (
                    entry_setup_evidence.get("evidence_sha256")
                    if entry_setup_evidence is not None
                    else None
                ),
                "source_exact_payload_sha256": _sha256(exact_payload),
                "candidate_exact_payload_sha256": _sha256(
                    candidate_input["exact_payload"]
                ),
                "candidate_input": candidate_input,
                "candidate_input_sha256": _sha256(candidate_input),
                "candidate": candidate,
                "detailed_analysis_stage_supported": True,
                "sample_floor": sample_floor,
            }
        )
    return detailed_requests


def run_paired_replay(
    requests: list[dict[str, Any]],
    *,
    control_runner: Callable[[dict[str, Any]], dict[str, Any]],
    candidate_runner: Callable[[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Execute both prompts on the same payload through injected offline runners."""

    results = []
    for request in requests:
        control_response = control_runner(request)
        candidate_attempts: list[dict[str, Any]] = []
        candidate_response: dict[str, Any] = {}
        candidate_errors: list[str] = []
        provider_failed = False
        semantic_repairs: list[str] = []
        risk_adjudication_response: dict[str, Any] | None = None
        for attempt_number in range(1, CANDIDATE_SCHEMA_MAX_ATTEMPTS + 1):
            attempt_request = dict(request)
            if candidate_errors:
                attempt_request["candidate_schema_correction_errors"] = list(
                    candidate_errors
                )
            try:
                envelope = candidate_runner(attempt_request)
                candidate_response, provider_provenance = _candidate_envelope(envelope)
                candidate_errors = validate_replay_candidate_response(
                    request,
                    candidate_response,
                )
                candidate_attempts.append(
                    {
                        "attempt_number": attempt_number,
                        "status": (
                            "pass" if not candidate_errors else "schema_rejected"
                        ),
                        "schema_errors": list(candidate_errors),
                        "provider_provenance": provider_provenance,
                    }
                )
            except Exception as exc:
                provider_failed = True
                candidate_errors = ["candidate_provider_call_failed"]
                candidate_attempts.append(
                    {
                        "attempt_number": attempt_number,
                        "status": "provider_failed",
                        "schema_errors": list(candidate_errors),
                        "provider_provenance": {
                            "provider": str(
                                (request.get("candidate") or {}).get("provider")
                                or "none"
                            ),
                            "model": (request.get("candidate") or {}).get("model"),
                            "provider_none": (
                                str(
                                    (request.get("candidate") or {}).get("provider")
                                    or "none"
                                ).lower()
                                == "none"
                            ),
                            "error_type": type(exc).__name__,
                            "error_code": "candidate_provider_call_failed",
                        },
                    }
                )
                break
            if not candidate_errors:
                break
        semantic_validator_version = str(
            (request.get("candidate") or {}).get("semantic_validator_version") or ""
        )
        if (
            candidate_errors
            and not provider_failed
            and semantic_validator_version
            == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
        ):
            repaired_response, semantic_repairs = (
                repair_invalid_entry_risk_adjudication(
                    candidate_response,
                    setup_evidence=request.get("entry_setup_evidence"),
                )
            )
            if semantic_repairs:
                repaired_errors = validate_replay_candidate_response(
                    request,
                    repaired_response,
                )
                candidate_attempts.append(
                    {
                        "attempt_number": len(candidate_attempts) + 1,
                        "status": (
                            "pass" if not repaired_errors else "schema_rejected"
                        ),
                        "schema_errors": list(repaired_errors),
                        "provider_provenance": {
                            "provider": "deterministic_offline_adapter",
                            "provider_none": False,
                            "runtime_effect": False,
                            "semantic_repair_version": (
                                ENTRY_RISK_ADJUDICATION_REPAIR_VERSION
                            ),
                            "repairs": list(semantic_repairs),
                        },
                    }
                )
                candidate_response = repaired_response
                candidate_errors = repaired_errors
        if (
            candidate_errors
            and not provider_failed
            and semantic_validator_version
            != ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
        ):
            repaired_response, semantic_repairs = (
                repair_bounded_opportunity_candidate_response(
                    request, candidate_response
                )
            )
            semantic_repair_version = (
                BOUNDED_OPPORTUNITY_SEMANTIC_REPAIR_VERSION
                if semantic_repairs
                else ANTICIPATORY_SEMANTIC_REPAIR_VERSION
            )
            if not semantic_repairs:
                repaired_response, semantic_repairs = (
                    repair_anticipatory_candidate_response(request, candidate_response)
                )
            if semantic_repairs:
                repaired_errors = validate_replay_candidate_response(
                    request,
                    repaired_response,
                )
                candidate_attempts.append(
                    {
                        "attempt_number": len(candidate_attempts) + 1,
                        "status": (
                            "pass" if not repaired_errors else "schema_rejected"
                        ),
                        "schema_errors": list(repaired_errors),
                        "provider_provenance": {
                            "provider": "deterministic_offline_adapter",
                            "provider_none": False,
                            "runtime_effect": False,
                            "semantic_repair_version": semantic_repair_version,
                            "repairs": list(semantic_repairs),
                        },
                    }
                )
                candidate_response = repaired_response
                candidate_errors = repaired_errors
        if (
            not candidate_errors
            and not provider_failed
            and semantic_validator_version
            == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
        ):
            risk_adjudication_response = dict(candidate_response)
            candidate_response = {
                **compose_entry_decision(
                    setup_evidence=request.get("entry_setup_evidence"),
                    risk_adjudication=risk_adjudication_response,
                    bounded_recovery_policy=(
                        str(
                            (request.get("candidate") or {}).get("prompt_version") or ""
                        )
                        == f"{DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION}_entry"
                    ),
                    sequential_recovery_policy=(
                        str(
                            (request.get("candidate") or {}).get("prompt_version") or ""
                        )
                        == f"{DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION}_entry"
                    ),
                ),
                "entry_risk_adjudication": risk_adjudication_response,
            }
        results.append(
            {
                "paired_replay_id": request["paired_replay_id"],
                "decision_trace_id": request["decision_trace_id"],
                "stage": request["stage"],
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "payload_sha256": request["payload_sha256"],
                "candidate_prompt_sha256": (request.get("candidate") or {}).get(
                    "system_prompt_sha256"
                ),
                "candidate_response_schema_sha256": (
                    request.get("candidate") or {}
                ).get("response_schema_sha256"),
                "candidate_response_schema_instance_sha256": (
                    request.get("candidate") or {}
                ).get("response_schema_instance_sha256"),
                "candidate_contract_sha256": _candidate_contract_sha256(
                    request.get("candidate") or {}
                ),
                "exact_payload_analysis_schema": (
                    (request.get("candidate") or {}).get("analysis_schema")
                ),
                "exact_payload_analysis_sha256": request.get(
                    "exact_payload_analysis_sha256"
                ),
                "anticipatory_reversal_analysis_sha256": request.get(
                    "anticipatory_reversal_analysis_sha256"
                ),
                "entry_setup_evidence_sha256": request.get(
                    "entry_setup_evidence_sha256"
                ),
                "entry_setup_evidence_confirmed": (
                    not request.get("entry_setup_evidence_sha256")
                    or request.get("entry_setup_evidence_sha256")
                    == _sha256(
                        {
                            key: value
                            for key, value in (
                                request.get("entry_setup_evidence") or {}
                            ).items()
                            if key != "evidence_sha256"
                        }
                    )
                ),
                "candidate_input_sha256": request.get("candidate_input_sha256"),
                "deterministic_analysis_confirmed": (
                    not request.get("exact_payload_analysis_sha256")
                    or request.get("exact_payload_analysis_sha256")
                    == _sha256(
                        {
                            key: value
                            for key, value in (
                                request.get("exact_payload_analysis") or {}
                            ).items()
                            if key != "analysis_sha256"
                        }
                    )
                ),
                "supplemental_analysis_confirmed": (
                    not request.get("anticipatory_reversal_analysis_sha256")
                    or request.get("anticipatory_reversal_analysis_sha256")
                    == _sha256(
                        {
                            key: value
                            for key, value in (
                                request.get("anticipatory_reversal_analysis") or {}
                            ).items()
                            if key != "analysis_sha256"
                        }
                    )
                ),
                "same_payload_confirmed": (
                    not request.get("candidate_exact_payload_sha256")
                    or request.get("candidate_exact_payload_sha256")
                    == request.get("source_exact_payload_sha256")
                ),
                "control_response": control_response,
                "candidate_response": candidate_response,
                "candidate_risk_adjudication_response": risk_adjudication_response,
                "candidate_schema_errors": candidate_errors,
                "candidate_semantic_repairs": semantic_repairs,
                "candidate_attempts": candidate_attempts,
                "status": (
                    "provider_failed"
                    if provider_failed
                    else ("pass" if not candidate_errors else "schema_rejected")
                ),
                **OFFLINE_CONTRACT,
            }
        )
    return results


def run_paired_replay_parallel(
    requests: list[dict[str, Any]],
    *,
    control_runner: Callable[[dict[str, Any]], dict[str, Any]],
    candidate_runner: Callable[[dict[str, Any]], dict[str, Any]],
    max_workers: int = 4,
) -> list[dict[str, Any]]:
    if not requests:
        return []
    indexed: dict[str, int] = {
        str(request.get("paired_replay_id") or ""): index
        for index, request in enumerate(requests)
    }
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 8))) as executor:
        futures = {
            executor.submit(
                run_paired_replay,
                [request],
                control_runner=control_runner,
                candidate_runner=candidate_runner,
            ): request
            for request in requests
        }
        for future in as_completed(futures):
            results.extend(future.result())
    results.sort(
        key=lambda row: indexed.get(
            str(row.get("paired_replay_id") or ""), len(indexed)
        )
    )
    return results


def _semantic_repair_provenance_matches(
    result: dict[str, Any], request: dict[str, Any]
) -> bool:
    """Require cached deterministic repairs to match the current contract."""

    repairs = [str(value) for value in result.get("candidate_semantic_repairs") or []]
    if not repairs:
        return True
    expected_version = str(
        ((request.get("candidate") or {}).get("semantic_repair_version")) or ""
    )
    if not expected_version:
        return False
    adapter_attempts = [
        attempt
        for attempt in result.get("candidate_attempts") or []
        if isinstance(attempt, dict)
        and (attempt.get("provider_provenance") or {}).get("provider")
        == "deterministic_offline_adapter"
    ]
    if len(adapter_attempts) != 1:
        return False
    provenance = adapter_attempts[0].get("provider_provenance") or {}
    recorded_repairs = [str(value) for value in provenance.get("repairs") or []]
    return bool(
        provenance.get("semantic_repair_version") == expected_version
        and recorded_repairs == repairs
    )


def _entry_setup_state_from_request(request: dict[str, Any]) -> str:
    evidence = request.get("entry_setup_evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    return str(evidence.get("setup_state") or "NOT_PREPARED").strip().upper()


def _entry_opportunity_funnel_attribution(
    *,
    labels: list[dict[str, Any]],
    prepared_requests: list[dict[str, Any]],
    comparable_rows: list[dict[str, Any]],
    results: list[dict[str, Any]],
    candidate_execution_requested: bool,
) -> dict[str, Any]:
    """Measure Entry opportunity recall before the candidate execution budget.

    Labels are decision events, not independent trade episodes.  The report keeps
    venue/session cohorts separate and treats candidate replay coverage as a
    sampling layer so an unevaluated READY row cannot be mislabeled as an AI
    rejection.
    """

    prepared_by_trace: dict[str, dict[str, Any]] = {}
    prepared_states_by_trace: dict[str, set[str]] = defaultdict(set)
    for request in prepared_requests:
        if _stage(request.get("stage")) != "entry":
            continue
        trace_id = str(request.get("decision_trace_id") or "").strip()
        if trace_id:
            prepared_states_by_trace[trace_id].add(
                _entry_setup_state_from_request(request)
            )
            if trace_id not in prepared_by_trace:
                prepared_by_trace[trace_id] = request
    conflicting_prepared_trace_ids = {
        trace_id
        for trace_id, states in prepared_states_by_trace.items()
        if len(states) > 1
    }
    comparison_by_trace = {
        str(row.get("decision_trace_id") or "").strip(): row
        for row in comparable_rows
        if _stage(row.get("stage")) == "entry" and row.get("decision_trace_id")
    }
    result_by_trace = {
        str(row.get("decision_trace_id") or "").strip(): row
        for row in results
        if _stage(row.get("stage")) == "entry" and row.get("decision_trace_id")
    }

    eligible_labels: list[dict[str, Any]] = []
    for label in labels:
        if (
            _stage(label.get("decision_stage")) != "entry"
            or label.get("source_quality_status") != "pass"
            or label.get("primary_cohort_eligible") is not True
        ):
            continue
        metric = _primary_metric(label) or {}
        if not metric.get("entry_path_first_hit"):
            continue
        eligible_labels.append(label)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for label in eligible_labels:
        grouped[
            (
                _venue(label.get("effective_venue")) or "UNKNOWN",
                _session(label.get("session_bucket")) or "UNKNOWN",
            )
        ].append(label)

    cohorts: list[dict[str, Any]] = []
    for (venue, session), cohort_labels in sorted(grouped.items()):
        control_action_path: dict[str, Counter[str]] = defaultdict(Counter)
        candidate_action_path: dict[str, Counter[str]] = defaultdict(Counter)
        path_counts: Counter[str] = Counter()
        setup_state_counts: Counter[str] = Counter()
        first_blocker_counts: Counter[str] = Counter()
        target_first_blocker_counts: Counter[str] = Counter()
        control_action_counts: Counter[str] = Counter()
        candidate_action_counts: Counter[str] = Counter()
        candidate_execution_status_counts: Counter[str] = Counter()
        prepared_count = 0
        attempted_count = 0
        evaluated_count = 0
        target_first_count = 0
        profit_opportunity_count = 0
        control_target_first_capture_count = 0
        control_target_first_probe_arm_count = 0
        control_adverse_first_exposure_count = 0
        candidate_evaluated_target_first_count = 0
        candidate_target_first_capture_count = 0
        candidate_adverse_first_exposure_count = 0

        for label in cohort_labels:
            trace_id = str(label.get("decision_trace_id") or "").strip()
            metric = _primary_metric(label) or {}
            path = str(metric.get("entry_path_first_hit") or "unknown")
            path_counts[path] += 1
            target_first = path == "target_first"
            if target_first:
                target_first_count += 1
            if metric.get("profit_opportunity_observed") is True:
                profit_opportunity_count += 1

            control_action = str(label.get("action") or "UNKNOWN").strip().upper()
            control_exposed = control_action in EXPOSURE_ACTIONS
            control_probe_armed = bool(
                control_exposed or label.get("entry_probe_intent") is True
            )
            control_action_counts[control_action] += 1
            control_action_path[control_action][path] += 1
            if target_first and control_exposed:
                control_target_first_capture_count += 1
            if target_first and control_probe_armed:
                control_target_first_probe_arm_count += 1
            if path == "adverse_first" and control_exposed:
                control_adverse_first_exposure_count += 1

            prepared = prepared_by_trace.get(trace_id)
            comparison = comparison_by_trace.get(trace_id)
            result = result_by_trace.get(trace_id)
            if result is not None:
                attempted_count += 1
                candidate_execution_status_counts[
                    str(result.get("status") or "unknown")
                ] += 1
            candidate_action = "UNKNOWN"
            candidate_exposed = False
            if comparison is not None:
                evaluated_count += 1
                candidate_action = (
                    str(comparison.get("candidate_action") or "UNKNOWN").strip().upper()
                )
                candidate_action_counts[candidate_action] += 1
                candidate_action_path[candidate_action][path] += 1
                candidate_exposed = bool(
                    comparison.get("candidate_exposure_selected") is True
                )
                if target_first:
                    candidate_evaluated_target_first_count += 1
                    if candidate_exposed:
                        candidate_target_first_capture_count += 1
                if path == "adverse_first" and candidate_exposed:
                    candidate_adverse_first_exposure_count += 1
            if trace_id in conflicting_prepared_trace_ids:
                prepared_count += 1
                setup_state_counts["CONFLICT"] += 1
                blocker = "prepared_setup_state_conflict"
            elif prepared is None:
                blocker = "paired_request_not_prepared"
            else:
                prepared_count += 1
                setup_state = _entry_setup_state_from_request(prepared)
                setup_state_counts[setup_state] += 1
                if setup_state == "INVALID":
                    blocker = "deterministic_setup_invalid"
                elif setup_state == "WAIT_CONFIRMATION":
                    blocker = "deterministic_setup_wait_confirmation"
                elif result is None and candidate_execution_requested:
                    blocker = "candidate_execution_budget_deferred"
                elif result is None:
                    blocker = "candidate_execution_not_requested"
                elif result.get("status") == "provider_failed":
                    blocker = "candidate_provider_failed"
                elif result.get("status") == "schema_rejected":
                    blocker = "candidate_schema_rejected"
                elif comparison is None:
                    blocker = "candidate_comparison_ineligible"
                elif candidate_exposed:
                    blocker = "candidate_exposure_selected"
                elif comparison.get("entry_ai_veto_corroborated") is True:
                    blocker = "ai_risk_veto_corroborated"
                elif comparison.get("candidate_probe_armed") is True:
                    blocker = "bounded_probe_arm_pending_recheck"
                elif candidate_action == "WAIT":
                    blocker = "composer_wait_without_probe_arm"
                else:
                    blocker = "composer_drop_or_no_exposure"
            first_blocker_counts[blocker] += 1
            if target_first:
                target_first_blocker_counts[blocker] += 1

        eligible_count = len(cohort_labels)
        cohorts.append(
            {
                "effective_venue": venue,
                "session_bucket": session,
                "eligible_decision_event_count": eligible_count,
                "eligible_unique_symbol_count": len(
                    {
                        _normalize_stock_code(row.get("stock_code"))
                        for row in cohort_labels
                        if _normalize_stock_code(row.get("stock_code"))
                    }
                ),
                "decision_event_semantics": (
                    "repeated_same_symbol_decisions_are_not_independent_trade_episodes"
                ),
                "entry_path_first_hit_counts": dict(path_counts),
                "profit_opportunity_1pct_count": profit_opportunity_count,
                "control_action_counts": dict(control_action_counts),
                "control_action_by_entry_path": {
                    action: dict(counts)
                    for action, counts in sorted(control_action_path.items())
                },
                "control_target_first_capture_count": (
                    control_target_first_capture_count
                ),
                "control_target_first_capture_rate_pct": (
                    control_target_first_capture_count / target_first_count * 100.0
                    if target_first_count
                    else None
                ),
                "control_target_first_probe_arm_count": (
                    control_target_first_probe_arm_count
                ),
                "control_adverse_first_exposure_count": (
                    control_adverse_first_exposure_count
                ),
                "prepared_setup_decision_count": prepared_count,
                "prepared_setup_coverage_pct": (
                    prepared_count / eligible_count * 100.0 if eligible_count else None
                ),
                "prepared_setup_state_counts": dict(setup_state_counts),
                "prepared_setup_state_conflict_count": sum(
                    str(row.get("decision_trace_id") or "").strip()
                    in conflicting_prepared_trace_ids
                    for row in cohort_labels
                ),
                "candidate_execution_attempted_decision_count": attempted_count,
                "candidate_execution_attempt_coverage_pct": (
                    attempted_count / prepared_count * 100.0 if prepared_count else None
                ),
                "candidate_execution_status_counts": dict(
                    candidate_execution_status_counts
                ),
                "candidate_evaluated_decision_count": evaluated_count,
                "candidate_evaluated_semantics": (
                    "same_payload_contract_valid_outcome_comparable_only"
                ),
                "candidate_evaluation_coverage_pct": (
                    evaluated_count / prepared_count * 100.0 if prepared_count else None
                ),
                "candidate_action_counts": dict(candidate_action_counts),
                "candidate_action_by_entry_path": {
                    action: dict(counts)
                    for action, counts in sorted(candidate_action_path.items())
                },
                "candidate_evaluated_target_first_count": (
                    candidate_evaluated_target_first_count
                ),
                "candidate_target_first_capture_count": (
                    candidate_target_first_capture_count
                ),
                "candidate_target_first_capture_rate_pct": (
                    candidate_target_first_capture_count
                    / candidate_evaluated_target_first_count
                    * 100.0
                    if candidate_evaluated_target_first_count
                    else None
                ),
                "candidate_adverse_first_exposure_count": (
                    candidate_adverse_first_exposure_count
                ),
                "first_blocker_counts": dict(first_blocker_counts),
                "target_first_first_blocker_counts": dict(target_first_blocker_counts),
            }
        )

    return {
        "schema": "entry_opportunity_funnel_attribution_v1",
        "metric_role": "funnel_count",
        "decision_authority": "offline_full_census_attribution_only",
        "window_policy": "full_mature_exact_entry_cohort_by_venue_session",
        "sample_floor": "one_eligible_decision_event_starts_observation",
        "primary_decision_metric": "target_first_capture_rate_pct",
        "source_quality_gate": "exact_v2_fresh_same_route_mature_10m_window",
        "cohort_count": len(cohorts),
        "cohorts": cohorts,
        "candidate_execution_requested": candidate_execution_requested,
        "cross_cohort_aggregation_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "treat_repeated_decision_events_as_independent_trades",
            "treat_unevaluated_candidate_rows_as_ai_rejections",
            "cross_venue_or_cross_session_performance_aggregation",
            "standalone_live_prompt_promotion",
            "real_order_or_realized_pnl_claim",
            "provider_model_threshold_price_quantity_or_cap_change",
            "broker_or_safety_guard_bypass",
            "bot_restart",
        ],
    }


def _prepared_entry_transition_observations(
    *,
    prepared_requests: list[dict[str, Any]],
    comparable_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    comparison_by_trace = {
        str(row.get("decision_trace_id") or "").strip(): row
        for row in comparable_rows
        if row.get("decision_trace_id")
    }
    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    prepared_state_sets: dict[str, set[str]] = defaultdict(set)
    for request in prepared_requests:
        if _stage(request.get("stage")) != "entry":
            continue
        trace_id = str(request.get("decision_trace_id") or "").strip()
        dedupe_key = trace_id or str(request.get("paired_replay_id") or "").strip()
        if dedupe_key:
            prepared_state_sets[dedupe_key].add(
                _entry_setup_state_from_request(request)
            )
    for request in prepared_requests:
        if _stage(request.get("stage")) != "entry":
            continue
        trace_id = str(request.get("decision_trace_id") or "").strip()
        dedupe_key = trace_id or str(request.get("paired_replay_id") or "").strip()
        if not dedupe_key or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        comparison = comparison_by_trace.get(trace_id)
        states = prepared_state_sets.get(dedupe_key) or set()
        setup_evidence = request.get("entry_setup_evidence")
        setup_evidence = setup_evidence if isinstance(setup_evidence, dict) else {}
        source_quality = setup_evidence.get("source_quality")
        source_quality = source_quality if isinstance(source_quality, dict) else {}
        recovery_analysis = request.get("anticipatory_reversal_analysis")
        recovery_analysis = (
            recovery_analysis if isinstance(recovery_analysis, dict) else {}
        )
        spread = recovery_analysis.get("spread")
        spread = spread if isinstance(spread, dict) else {}
        execution_cost = recovery_analysis.get("execution_cost")
        execution_cost = execution_cost if isinstance(execution_cost, dict) else {}
        precursors = recovery_analysis.get("precursors")
        precursors = precursors if isinstance(precursors, dict) else {}
        observations.append(
            {
                "decision_trace_id": trace_id,
                "decision_ts": request.get("decision_ts"),
                "stock_code": request.get("stock_code"),
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "entry_setup_state": (
                    next(iter(states)) if len(states) == 1 else "CONFLICT"
                ),
                "prepared_setup_state_conflict": len(states) > 1,
                "reference_price": request.get("reference_price"),
                "best_bid": request.get("best_bid"),
                "best_ask": request.get("best_ask"),
                "structure_phase_bar_end": setup_evidence.get(
                    "structure_phase_bar_end"
                ),
                "source_quality_status": source_quality.get("status"),
                "spread_bp": spread.get("spread_bp"),
                "conservative_execution_cost_pct": execution_cost.get(
                    "conservative_execution_cost_pct"
                ),
                "sell_momentum_decelerating": precursors.get(
                    "sell_momentum_decelerating"
                ),
                "hard_blockers": list(recovery_analysis.get("hard_blockers") or []),
                "candidate_evaluated": comparison is not None,
                "comparison_row": comparison,
                "candidate_action": (
                    comparison.get("candidate_action") if comparison else None
                ),
                "candidate_exposure_selected": bool(
                    comparison and comparison.get("candidate_exposure_selected") is True
                ),
                "candidate_primary_decision_value_pct": (
                    comparison.get("candidate_primary_decision_value_pct")
                    if comparison
                    else None
                ),
                "entry_path_first_hit": (
                    comparison.get("entry_path_first_hit") if comparison else None
                ),
            }
        )
    for row in comparable_rows:
        trace_id = str(row.get("decision_trace_id") or "").strip()
        dedupe_key = trace_id or str(row.get("paired_replay_id") or "").strip()
        if dedupe_key and dedupe_key not in seen:
            seen.add(dedupe_key)
            observations.append(dict(row, candidate_evaluated=True))
    return observations


def _attach_sequential_recovery_transitions(
    *,
    seed_rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Arm an offline probe only after a later exact recovery confirmation."""

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        grouped[
            (
                _normalize_stock_code(observation.get("stock_code")),
                _venue(observation.get("effective_venue")),
                _session(observation.get("session_bucket")),
            )
        ].append(observation)
    for route_rows in grouped.values():
        route_rows.sort(
            key=lambda row: _parse_ts(row.get("decision_ts"))
            or datetime.max.replace(tzinfo=KST)
        )

    comparison_by_trace = {
        str(row.get("decision_trace_id") or "").strip(): row.get("comparison_row")
        for row in observations
        if row.get("candidate_evaluated") is True
        and isinstance(row.get("comparison_row"), dict)
        and row.get("decision_trace_id")
    }
    used_followup_trace_ids: set[str] = set()
    arm_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    for seed in sorted(
        seed_rows,
        key=lambda row: _parse_ts(row.get("decision_ts"))
        or datetime.max.replace(tzinfo=KST),
    ):
        route_key = (
            _normalize_stock_code(seed.get("stock_code")),
            _venue(seed.get("effective_venue")),
            _session(seed.get("session_bucket")),
        )
        decision_ts = _parse_ts(seed.get("decision_ts"))
        initial_bar_end = _parse_ts(seed.get("entry_structure_phase_bar_end"))
        initial_price = _number(seed.get("best_ask")) or _number(
            seed.get("reference_price")
        )
        initial_spread = _number(seed.get("conservative_spread_bp"))
        initial_cost = _number(seed.get("conservative_execution_cost_pct"))
        current_trace_id = str(seed.get("decision_trace_id") or "").strip()
        followups: list[tuple[float, dict[str, Any], list[str]]] = []
        if decision_ts is not None:
            for candidate in grouped.get(route_key, []):
                candidate_trace_id = str(
                    candidate.get("decision_trace_id") or ""
                ).strip()
                if not candidate_trace_id or candidate_trace_id == current_trace_id:
                    continue
                candidate_ts = _parse_ts(candidate.get("decision_ts"))
                if candidate_ts is None:
                    continue
                delay_sec = (candidate_ts - decision_ts).total_seconds()
                if not 0 < delay_sec <= ENTRY_RECHECK_MAX_WAIT_SEC:
                    continue
                failures: list[str] = []
                candidate_bar_end = _parse_ts(candidate.get("structure_phase_bar_end"))
                candidate_price = _number(candidate.get("best_ask")) or _number(
                    candidate.get("reference_price")
                )
                candidate_spread = _number(candidate.get("spread_bp"))
                candidate_cost = _number(
                    candidate.get("conservative_execution_cost_pct")
                )
                if (
                    initial_bar_end is None
                    or candidate_bar_end is None
                    or candidate_bar_end <= initial_bar_end
                ):
                    failures.append("completed_bar_not_advanced")
                if (
                    initial_price is None
                    or candidate_price is None
                    or candidate_price < initial_price
                ):
                    failures.append("effective_price_not_recovered")
                if (
                    initial_spread is None
                    or candidate_spread is None
                    or candidate_spread > initial_spread
                ):
                    failures.append("spread_worsened_or_missing")
                if (
                    initial_cost is None
                    or candidate_cost is None
                    or candidate_cost > initial_cost
                ):
                    failures.append("execution_cost_worsened_or_missing")
                if candidate.get("sell_momentum_decelerating") is not True:
                    failures.append("sell_momentum_not_decelerating")
                if candidate.get("hard_blockers"):
                    failures.append("hard_blocker_present")
                if str(candidate.get("source_quality_status") or "").lower() not in {
                    "fresh",
                    "fresh_consistent",
                    "pass",
                }:
                    failures.append("source_quality_not_fresh")
                followups.append((delay_sec, candidate, failures))

        selected = next(
            (
                item
                for item in followups
                if not item[2]
                and str(item[1].get("decision_trace_id") or "").strip()
                not in used_followup_trace_ids
            ),
            None,
        )
        diagnostic = selected or (followups[0] if followups else None)
        if decision_ts is None:
            status = "decision_time_missing"
        elif selected is not None:
            status = "sequential_confirmation_observed"
        elif followups:
            status = "followup_observed_not_confirmed"
        else:
            status = "no_followup_within_window"
        selected_trace_id = (
            str(selected[1].get("decision_trace_id") or "").strip()
            if selected is not None
            else ""
        )
        if selected_trace_id:
            used_followup_trace_ids.add(selected_trace_id)
            selected_comparison = comparison_by_trace.get(selected_trace_id)
            if selected_comparison is not None:
                arm_rows.append(selected_comparison)
        seed["entry_sequential_recovery_transition_status"] = status
        seed["entry_sequential_recovery_followup_count"] = len(followups)
        seed["entry_sequential_recovery_followup_trace_id"] = (
            diagnostic[1].get("decision_trace_id") if diagnostic is not None else None
        )
        seed["entry_sequential_recovery_followup_delay_sec"] = (
            diagnostic[0] if diagnostic is not None else None
        )
        seed["entry_sequential_recovery_confirmation_failures"] = (
            list(diagnostic[2]) if diagnostic is not None else []
        )
        seed["entry_sequential_recovery_probe_armed"] = selected is not None
        seed["entry_sequential_recovery_outcome_joined"] = bool(
            selected_trace_id and selected_trace_id in comparison_by_trace
        )
        transition_rows.append(seed)

    arm_values = [
        outcome - cost
        for row in arm_rows
        if (outcome := _number(row.get("outcome_return_pct"))) is not None
        and (cost := _number(row.get("conservative_execution_cost_pct"))) is not None
    ]
    severe_tail_count = sum(
        row.get("probe_severe_tail_adverse") is True for row in arm_rows
    )
    catastrophic_count = sum(
        (loss := _number(row.get("probe_worst_loss_pct"))) is not None
        and loss < PAIRED_CANDIDATE_CATASTROPHIC_LOSS_PCT
        for row in arm_rows
    )
    arm_count = sum(
        row.get("entry_sequential_recovery_probe_armed") is True
        for row in transition_rows
    )
    unique_symbols = len(
        {
            _normalize_stock_code(row.get("stock_code"))
            for row in transition_rows
            if row.get("entry_sequential_recovery_probe_armed") is True
        }
    )
    floor_pass = bool(
        arm_count >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
        and unique_symbols >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
    )
    return {
        "schema": "entry_sequential_recovery_replay_v1",
        "contract_version": "entry_next_exact_sequential_recovery_v1",
        "metric_role": "ai_entry_sequential_recovery_quality_observation",
        "decision_authority": "offline_counterfactual_passive_probe_only",
        "window_policy": (
            "same_symbol_venue_session_natural_exact_snapshot_within_300s"
        ),
        "sample_floor": {
            "required_arm_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "required_unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            "observed_arm_rows": arm_count,
            "observed_unique_symbols": unique_symbols,
            "pass": floor_pass,
        },
        "primary_decision_metric": "probe_cost_adjusted_ev_pct",
        "source_quality_gate": (
            "exact_v2_same_route_completed_bar_advanced_fresh_conflict_free"
        ),
        "seed_count": len(transition_rows),
        "followup_observed_count": sum(
            int(row.get("entry_sequential_recovery_followup_count") or 0) > 0
            for row in transition_rows
        ),
        "confirmed_arm_count": arm_count,
        "outcome_joined_arm_count": len(arm_rows),
        "probe_cost_adjusted_ev_pct": fmean(arm_values) if arm_values else None,
        "target_first_count": sum(
            row.get("entry_path_first_hit") == "target_first" for row in arm_rows
        ),
        "adverse_first_count": sum(
            row.get("entry_path_first_hit") == "adverse_first" for row in arm_rows
        ),
        "severe_tail_count": severe_tail_count,
        "catastrophic_loss_count": catastrophic_count,
        "status_counts": dict(
            Counter(
                str(row.get("entry_sequential_recovery_transition_status") or "unknown")
                for row in transition_rows
            )
        ),
        "confirmation_failure_counts": dict(
            Counter(
                failure
                for row in transition_rows
                for failure in row.get(
                    "entry_sequential_recovery_confirmation_failures"
                )
                or []
            )
        ),
        "development_quality_gate_pass": (
            bool(
                floor_pass
                and len(arm_values) == arm_count
                and fmean(arm_values) > 0
                and catastrophic_count == 0
                and severe_tail_count / arm_count * 100.0
                <= PAIRED_CANDIDATE_MAX_SEVERE_TAIL_RATE_PCT
            )
            if arm_count
            else False
        ),
        "prospective_validation_required": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "same_sample_live_promotion",
            "treat_initial_wait_as_probe",
            "treat_arm_as_submitted_order",
            "provider_model_threshold_price_quantity_or_cap_change",
            "broker_or_safety_guard_bypass",
            "bot_restart",
        ],
    }


def _attach_wait_transition_continuity(
    *,
    waiting_rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    field_prefix: str,
    contract_version: str,
    observation_source: str,
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[
            (
                _normalize_stock_code(row.get("stock_code")),
                _venue(row.get("effective_venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    for route_rows in grouped.values():
        route_rows.sort(
            key=lambda row: _parse_ts(row.get("decision_ts"))
            or datetime.max.replace(tzinfo=KST)
        )

    transition_rows: list[dict[str, Any]] = []
    for row in waiting_rows:
        route_key = (
            _normalize_stock_code(row.get("stock_code")),
            _venue(row.get("effective_venue")),
            _session(row.get("session_bucket")),
        )
        decision_ts = _parse_ts(row.get("decision_ts"))
        current_trace_id = str(row.get("decision_trace_id") or "").strip()
        followups: list[tuple[float, dict[str, Any]]] = []
        if decision_ts is not None:
            for candidate in grouped.get(route_key, []):
                if (
                    str(candidate.get("decision_trace_id") or "").strip()
                    == current_trace_id
                ):
                    continue
                candidate_ts = _parse_ts(candidate.get("decision_ts"))
                if candidate_ts is None:
                    continue
                delay_sec = (candidate_ts - decision_ts).total_seconds()
                if 0 < delay_sec <= ENTRY_RECHECK_MAX_WAIT_SEC:
                    followups.append((delay_sec, candidate))
        ready_followup = next(
            (
                (delay_sec, candidate)
                for delay_sec, candidate in followups
                if candidate.get("entry_setup_state") == "READY"
            ),
            None,
        )
        confirmed = next(
            (
                (delay_sec, candidate)
                for delay_sec, candidate in followups
                if candidate.get("entry_setup_state") == "READY"
                and candidate.get("candidate_evaluated") is True
                and candidate.get("candidate_exposure_selected") is True
            ),
            None,
        )
        selected = confirmed or ready_followup or (followups[0] if followups else None)
        if decision_ts is None:
            status = "decision_time_missing"
        elif confirmed is not None:
            status = "ready_exposure_confirmed_after_wait"
        elif (
            ready_followup is not None
            and ready_followup[1].get("candidate_evaluated") is not True
        ):
            status = "ready_followup_candidate_budget_deferred"
        elif ready_followup is not None:
            status = "ready_followup_evaluated_not_exposed"
        elif followups:
            status = "followup_observed_not_ready"
        else:
            status = "no_followup_within_window"
        row[f"{field_prefix}_transition_status"] = status
        row[f"{field_prefix}_followup_count"] = len(followups)
        row[f"{field_prefix}_ready_followup_delay_sec"] = (
            ready_followup[0] if ready_followup is not None else None
        )
        row[f"{field_prefix}_followup_trace_id"] = (
            selected[1].get("decision_trace_id") if selected is not None else None
        )
        row[f"{field_prefix}_followup_setup_state"] = (
            selected[1].get("entry_setup_state") if selected is not None else None
        )
        row[f"{field_prefix}_followup_candidate_evaluated"] = bool(
            selected is not None and selected[1].get("candidate_evaluated") is True
        )
        row[f"{field_prefix}_followup_exposure_selected"] = bool(
            selected is not None
            and selected[1].get("candidate_exposure_selected") is True
        )
        row[f"{field_prefix}_confirmed_primary_decision_value_pct"] = (
            confirmed[1].get("candidate_primary_decision_value_pct")
            if confirmed is not None
            else None
        )
        transition_rows.append(row)

    confirmed_values = [
        value
        for row in transition_rows
        if (
            value := _number(
                row.get(f"{field_prefix}_confirmed_primary_decision_value_pct")
            )
        )
        is not None
    ]
    ready_followup_observed_count = sum(
        row.get(f"{field_prefix}_followup_setup_state") == "READY"
        for row in transition_rows
    )
    status_by_initial_risk_verdict: dict[str, Counter[str]] = defaultdict(Counter)
    for row in transition_rows:
        status_by_initial_risk_verdict[
            str(row.get("entry_ai_risk_verdict") or "NOT_RECORDED")
        ][str(row.get(f"{field_prefix}_transition_status") or "unknown")] += 1
    return {
        "contract_version": contract_version,
        "maximum_wait_sec": ENTRY_RECHECK_MAX_WAIT_SEC,
        "waiting_decision_count": len(transition_rows),
        "followup_observed_count": sum(
            int(row.get(f"{field_prefix}_followup_count") or 0) > 0
            for row in transition_rows
        ),
        "ready_followup_observed_count": ready_followup_observed_count,
        "ready_followup_observed_rate_pct": (
            ready_followup_observed_count / len(transition_rows) * 100.0
            if transition_rows
            else None
        ),
        "ready_followup_candidate_budget_deferred_count": sum(
            row.get(f"{field_prefix}_transition_status")
            == "ready_followup_candidate_budget_deferred"
            for row in transition_rows
        ),
        "ready_exposure_confirmed_count": sum(
            row.get(f"{field_prefix}_transition_status")
            == "ready_exposure_confirmed_after_wait"
            for row in transition_rows
        ),
        "confirmed_exposure_source_quality_adjusted_ev_pct": (
            fmean(confirmed_values) if confirmed_values else None
        ),
        "status_counts": dict(
            Counter(
                str(row.get(f"{field_prefix}_transition_status") or "unknown")
                for row in transition_rows
            )
        ),
        "initial_setup_state_counts": dict(
            Counter(
                str(row.get("entry_setup_state") or "NOT_RECORDED")
                for row in transition_rows
            )
        ),
        "initial_risk_verdict_counts": dict(
            Counter(
                str(row.get("entry_ai_risk_verdict") or "NOT_RECORDED")
                for row in transition_rows
            )
        ),
        "transition_status_by_initial_risk_verdict": {
            verdict: dict(counts)
            for verdict, counts in sorted(status_by_initial_risk_verdict.items())
        },
        "observation_source": observation_source,
        "decision_authority": "offline_sequential_continuity_attribution_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _entry_recheck_reason_breakdown(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Split offline recheck stress evidence by deterministic owner reason."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for reason in row.get("entry_recheck_reasons") or []:
            grouped[str(reason)].append(row)
    breakdown: dict[str, dict[str, Any]] = {}
    for reason, reason_rows in sorted(grouped.items()):
        stress_values = []
        for row in reason_rows:
            outcome = _number(row.get("outcome_return_pct"))
            cost = _number(row.get("conservative_execution_cost_pct"))
            if outcome is not None and cost is not None:
                stress_values.append(outcome - cost)
        breakdown[reason] = {
            "decision_count": len(reason_rows),
            "unique_symbol_count": len(
                {
                    str(row.get("stock_code") or "")
                    for row in reason_rows
                    if row.get("stock_code")
                }
            ),
            "immediate_exposure_stress_source_quality_adjusted_ev_pct": (
                fmean(stress_values) if stress_values else None
            ),
            "target_first_count": sum(
                str(row.get("entry_path_first_hit") or "") == "target_first"
                for row in reason_rows
            ),
            "adverse_first_count": sum(
                str(row.get("entry_path_first_hit") or "") == "adverse_first"
                for row in reason_rows
            ),
            "severe_tail_stress_count": sum(
                row.get("probe_severe_tail_adverse") is True for row in reason_rows
            ),
            "candidate_exposure_count": sum(
                row.get("candidate_exposure_selected") is True for row in reason_rows
            ),
        }
    return breakdown


def _attach_entry_recheck_transitions(
    rows: list[dict[str, Any]],
    *,
    prepared_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Link WAIT_CONFIRMATION to a later exact READY exposure on the same route."""

    if prepared_requests is not None:
        observations = _prepared_entry_transition_observations(
            prepared_requests=prepared_requests,
            comparable_rows=rows,
        )
        waiting_rows = [row for row in rows if row.get("entry_recheck_intent") is True]
        summary = _attach_wait_transition_continuity(
            waiting_rows=waiting_rows,
            observations=observations,
            field_prefix="entry_recheck",
            contract_version="entry_next_exact_recheck_transition_v2",
            observation_source="full_prepared_exact_request_census",
        )
        return {
            "contract_version": summary["contract_version"],
            "maximum_recheck_wait_sec": summary["maximum_wait_sec"],
            "recheck_decision_count": summary["waiting_decision_count"],
            "followup_observed_count": summary["followup_observed_count"],
            "ready_followup_observed_count": summary["ready_followup_observed_count"],
            "ready_followup_observed_rate_pct": summary[
                "ready_followup_observed_rate_pct"
            ],
            "ready_followup_candidate_budget_deferred_count": summary[
                "ready_followup_candidate_budget_deferred_count"
            ],
            "ready_exposure_confirmed_count": summary["ready_exposure_confirmed_count"],
            "confirmed_exposure_cost_adjusted_ev_pct": summary[
                "confirmed_exposure_source_quality_adjusted_ev_pct"
            ],
            "confirmed_exposure_source_quality_adjusted_ev_pct": summary[
                "confirmed_exposure_source_quality_adjusted_ev_pct"
            ],
            "status_counts": summary["status_counts"],
            "observation_source": summary["observation_source"],
            "decision_authority": summary["decision_authority"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                _normalize_stock_code(row.get("stock_code")),
                _venue(row.get("effective_venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    transition_rows: list[dict[str, Any]] = []
    for route_rows in grouped.values():
        route_rows.sort(
            key=lambda row: _parse_ts(row.get("decision_ts"))
            or datetime.max.replace(tzinfo=KST)
        )
        for index, row in enumerate(route_rows):
            if row.get("entry_recheck_intent") is not True:
                continue
            decision_ts = _parse_ts(row.get("decision_ts"))
            followups: list[tuple[float, dict[str, Any]]] = []
            if decision_ts is not None:
                for candidate in route_rows[index + 1 :]:
                    candidate_ts = _parse_ts(candidate.get("decision_ts"))
                    if candidate_ts is None:
                        continue
                    delay_sec = (candidate_ts - decision_ts).total_seconds()
                    if delay_sec <= 0:
                        continue
                    if delay_sec > ENTRY_RECHECK_MAX_WAIT_SEC:
                        break
                    followups.append((delay_sec, candidate))
            confirmed = next(
                (
                    (delay_sec, candidate)
                    for delay_sec, candidate in followups
                    if candidate.get("entry_setup_state") == "READY"
                    and candidate.get("candidate_exposure_selected") is True
                ),
                None,
            )
            first_followup = followups[0] if followups else None
            selected = confirmed or first_followup
            if decision_ts is None:
                status = "decision_time_missing"
            elif confirmed is not None:
                status = "ready_exposure_confirmed_after_recheck"
            elif followups:
                status = "followup_observed_not_confirmed"
            else:
                status = "no_followup_within_window"
            row["entry_recheck_transition_status"] = status
            row["entry_recheck_followup_count"] = len(followups)
            row["entry_recheck_confirmation_delay_sec"] = (
                confirmed[0] if confirmed is not None else None
            )
            row["entry_recheck_followup_trace_id"] = (
                selected[1].get("decision_trace_id") if selected is not None else None
            )
            row["entry_recheck_followup_setup_state"] = (
                selected[1].get("entry_setup_state") if selected is not None else None
            )
            row["entry_recheck_followup_exposure_selected"] = bool(
                selected is not None
                and selected[1].get("candidate_exposure_selected") is True
            )
            row["entry_recheck_confirmed_primary_decision_value_pct"] = (
                confirmed[1].get("candidate_primary_decision_value_pct")
                if confirmed is not None
                else None
            )
            row["entry_recheck_confirmed_entry_path_first_hit"] = (
                confirmed[1].get("entry_path_first_hit")
                if confirmed is not None
                else None
            )
            transition_rows.append(row)

    confirmed_values = [
        value
        for row in transition_rows
        if (
            value := _number(
                row.get("entry_recheck_confirmed_primary_decision_value_pct")
            )
        )
        is not None
    ]
    return {
        "contract_version": "entry_next_exact_recheck_transition_v1",
        "maximum_recheck_wait_sec": ENTRY_RECHECK_MAX_WAIT_SEC,
        "recheck_decision_count": len(transition_rows),
        "followup_observed_count": sum(
            int(row.get("entry_recheck_followup_count") or 0) > 0
            for row in transition_rows
        ),
        "ready_exposure_confirmed_count": sum(
            row.get("entry_recheck_transition_status")
            == "ready_exposure_confirmed_after_recheck"
            for row in transition_rows
        ),
        "confirmed_exposure_cost_adjusted_ev_pct": (
            fmean(confirmed_values) if confirmed_values else None
        ),
        "status_counts": dict(
            Counter(
                str(row.get("entry_recheck_transition_status") or "unknown")
                for row in transition_rows
            )
        ),
        "decision_authority": "offline_sequential_recheck_attribution_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _entry_probe_path_proxy_value(row: dict[str, Any]) -> float | None:
    """Return a bounded one-share path proxy, never a realized exit PnL."""

    path = str(row.get("entry_path_first_hit") or "")
    cost = _number(row.get("conservative_execution_cost_pct"))
    if cost is None:
        return None
    if path == "target_first":
        gross = _number(row.get("entry_path_target_pct"))
    elif path == "adverse_first":
        gross = _number(row.get("entry_path_adverse_pct"))
    elif path == "neither_hit":
        gross = _number(row.get("outcome_return_pct"))
    else:
        return None
    return gross - cost if gross is not None else None


def _entry_lifecycle_source_inventory(target_date: str) -> list[dict[str, Any]]:
    """Inventory adjacent reports without treating them as candidate ownership.

    These reports can prove that the natural lifecycle or a generic policy was
    observed.  They cannot, by themselves, prove how this report's V2.14
    counterfactual candidate would have submitted, filled, scaled, or exited.
    """

    paths = (
        (
            "entry_candidate_lifecycle_state",
            candidate_lifecycle_report_path(target_date),
        ),
        (
            "scalping_pyramid_intraday_feedback",
            PYRAMID_FEEDBACK_REPORT_DIR
            / f"scalping_pyramid_intraday_feedback_{target_date}.json",
        ),
        (
            "scale_in_incremental_counterfactual",
            SCALE_IN_COUNTERFACTUAL_REPORT_DIR
            / f"scale_in_incremental_counterfactual_{target_date}.json",
        ),
        (
            "entry_split_order_plan",
            ENTRY_SPLIT_ORDER_PLAN_REPORT_DIR
            / f"entry_split_order_plan_{target_date}.json",
        ),
    )
    inventory: list[dict[str, Any]] = []
    for owner, path in paths:
        payload = _load_json(path)
        if not payload:
            inventory.append(
                {
                    "owner": owner,
                    "path": str(path),
                    "status": "missing_or_unreadable",
                    "candidate_exact_state_authority": False,
                }
            )
            continue
        row: dict[str, Any] = {
            "owner": owner,
            "path": str(path),
            "status": "available",
            "canonical_json_sha256": _sha256(payload),
            "schema_version": payload.get("schema_version"),
            "runtime_effect": payload.get("runtime_effect"),
            "candidate_exact_state_authority": False,
        }
        summary = payload.get("summary")
        summary = summary if isinstance(summary, dict) else {}
        if owner == "entry_candidate_lifecycle_state":
            row["candidate_exact_state_authority"] = bool(
                payload.get("schema") == "entry_candidate_lifecycle_state_report_v1"
                and payload.get("runtime_effect") is False
                and payload.get("allowed_runtime_apply") is False
                and payload.get("actual_order_submitted") is False
                and payload.get("broker_order_forbidden") is True
            )
            row["evidence"] = {
                "source_event_path": payload.get("source_event_path"),
                "source_event_count": int(
                    _number(payload.get("source_event_count")) or 0
                ),
                "candidate_state_count": int(
                    _number(payload.get("candidate_state_count")) or 0
                ),
                "source_quality_pass_count": int(
                    _number(payload.get("source_quality_pass_count")) or 0
                ),
                "full_lifecycle_evaluable_candidate_count": int(
                    _number(payload.get("full_lifecycle_evaluable_candidate_count"))
                    or 0
                ),
            }
            row["non_authority_reason"] = (
                None
                if row["candidate_exact_state_authority"]
                else "candidate_state_report_schema_mismatch"
            )
        elif owner == "scalping_pyramid_intraday_feedback":
            natural = summary.get("whole_day_real_entry_lifecycle")
            natural = natural if isinstance(natural, dict) else {}
            scale_in = summary.get("real_scale_in_performance")
            scale_in = scale_in if isinstance(scale_in, dict) else {}
            row["evidence"] = {
                "one_share_event_count": int(
                    _number(summary.get("one_share_event_count")) or 0
                ),
                "probe_residual_real_outcome_closed_count": int(
                    _number(summary.get("probe_residual_real_outcome_closed_count"))
                    or 0
                ),
                "natural_filled_cycle_count": int(
                    _number(natural.get("filled_cycle_count")) or 0
                ),
                "natural_closed_cycle_count": int(
                    _number(natural.get("closed_cycle_count")) or 0
                ),
                "real_scale_in_execution_count": int(
                    _number(scale_in.get("execution_count")) or 0
                ),
            }
            row["non_authority_reason"] = (
                "natural_real_lifecycle_not_same_candidate_counterfactual_state"
            )
        elif owner == "scale_in_incremental_counterfactual":
            row["evidence"] = {
                "status": payload.get("status"),
                "candidate_activity_count": int(
                    _number(summary.get("candidate_activity_count")) or 0
                ),
                "eligible_candidate_count": int(
                    _number(summary.get("eligible_candidate_count")) or 0
                ),
                "counterfactual_event_count": int(
                    _number(summary.get("counterfactual_event_count")) or 0
                ),
                "no_sample_reason": summary.get("no_sample_reason"),
            }
            row["non_authority_reason"] = (
                "scale_in_only_report_not_same_entry_candidate_full_lifecycle"
            )
        else:
            candidate_grid = payload.get("candidate_grid")
            row["evidence"] = {
                "candidate_policy_count": (
                    len(candidate_grid) if isinstance(candidate_grid, list) else 0
                ),
                "recommended_policy_present": isinstance(
                    payload.get("recommended_policy"), dict
                ),
                "actual_order_submitted": payload.get("actual_order_submitted"),
            }
            row["non_authority_reason"] = (
                "generic_policy_calibration_not_candidate_specific_invocation_fill"
            )
        inventory.append(row)
    return inventory


def _attach_entry_candidate_lifecycle_states(
    rows: list[dict[str, Any]], *, target_date: str
) -> dict[str, Any]:
    """Join only exact trace/pair/venue/session candidate-owned state."""

    state_index = load_candidate_state_index(
        target_date,
        materialize=True,
        write=False,
    )
    attached = 0
    conflicts = 0
    for row in rows:
        if not (
            row.get("candidate_exposure_selected") is True
            or row.get("candidate_probe_armed") is True
        ):
            continue
        key = (
            str(row.get("decision_trace_id") or "").strip(),
            str(row.get("paired_replay_id") or "").strip(),
            _venue(row.get("effective_venue")),
            _session(row.get("session_bucket")).lower(),
        )
        state = state_index.get(key)
        if not isinstance(state, dict):
            continue
        existing = row.get("candidate_counterfactual_lifecycle_state")
        if isinstance(existing, dict) and existing and existing != state:
            conflicts += 1
            row["candidate_lifecycle_state_join_conflict"] = True
            continue
        row["candidate_counterfactual_lifecycle_state"] = dict(state)
        row["candidate_lifecycle_state_join_basis"] = state.get("lifecycle_basis")
        attached += 1
    return {
        "candidate_state_index_count": len(state_index),
        "candidate_state_attached_count": attached,
        "candidate_state_join_conflict_count": conflicts,
        "candidate_state_event_path": str(candidate_lifecycle_event_path(target_date)),
        "candidate_state_report_path": str(
            candidate_lifecycle_report_path(target_date)
        ),
    }


def _entry_candidate_lifecycle_source_audit(
    rows: list[dict[str, Any]],
    *,
    source_inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    """Declare whether candidate-owned full-lifecycle state is replayable."""

    candidate_rows = [
        row
        for row in rows
        if row.get("candidate_exposure_selected") is True
        or row.get("candidate_probe_armed") is True
    ]
    state_rows = [
        row
        for row in candidate_rows
        if isinstance(row.get("candidate_counterfactual_lifecycle_state"), dict)
        and bool(row.get("candidate_counterfactual_lifecycle_state"))
    ]
    required_components = (
        "probe",
        "post_probe",
        "residual_multi_leg",
        "scale_in",
        "holding_exit",
        "economics",
    )
    component_available_counts = {
        component: sum(
            candidate_lifecycle_component_is_complete(
                component,
                (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
                    component
                ),
            )
            for row in state_rows
        )
        for component in required_components
    }
    complete_rows = [
        row
        for row in state_rows
        if all(
            candidate_lifecycle_component_is_complete(
                component,
                (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
                    component
                ),
            )
            for component in required_components
        )
        and (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
            "source_quality_status"
        )
        == "pass"
        and (row.get("candidate_counterfactual_lifecycle_state") or {}).get("schema")
        == "entry_candidate_lifecycle_state_v1"
        and (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
            "decision_trace_id"
        )
        == row.get("decision_trace_id")
        and (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
            "paired_replay_id"
        )
        == row.get("paired_replay_id")
        and (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
            "effective_venue"
        )
        == _venue(row.get("effective_venue"))
        and str(
            (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
                "session_bucket"
            )
            or ""
        ).lower()
        == _session(row.get("session_bucket")).lower()
    ]
    if not candidate_rows:
        status = "keep_path_proxy_only"
    elif complete_rows:
        status = "exact_candidate_owned_state_source_available_not_yet_evaluated"
    else:
        status = "source_state_missing_instrumentation_gap"
    return {
        "schema": "entry_candidate_lifecycle_source_audit_v1",
        "metric_role": "instrumentation_gap",
        "decision_authority": "offline_source_adequacy_only",
        "window_policy": "same_exact_candidate_probe_through_terminal_exit",
        "sample_floor": "one_candidate_probe_arm_starts_source_adequacy_audit",
        "primary_decision_metric": "full_lifecycle_evaluable_candidate_count",
        "source_quality_gate": (
            "exact_candidate_owned_same_route_stage_state_with_time_price_quantity_cost"
        ),
        "required_state_schema": "entry_candidate_lifecycle_state_v1",
        "required_components": list(required_components),
        "candidate_probe_or_exposure_count": len(candidate_rows),
        "candidate_state_row_count": len(state_rows),
        "candidate_state_schema_pass_count": sum(
            (row.get("candidate_counterfactual_lifecycle_state") or {}).get("schema")
            == "entry_candidate_lifecycle_state_v1"
            for row in state_rows
        ),
        "candidate_state_source_quality_pass_count": sum(
            (row.get("candidate_counterfactual_lifecycle_state") or {}).get(
                "source_quality_status"
            )
            == "pass"
            for row in state_rows
        ),
        "component_available_counts": component_available_counts,
        "full_lifecycle_evaluable_candidate_count": len(complete_rows),
        "status": status,
        "source_inventory": source_inventory,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "attribute_natural_control_order_fill_or_exit_to_candidate",
            "treat_generic_entry_split_policy_as_candidate_invocation",
            "treat_bar_path_proxy_as_realized_pnl",
            "assume_missing_residual_scale_in_holding_or_exit_state",
            "runtime_provider_model_threshold_price_quantity_cap_or_bot_change",
        ],
    }


def _entry_lifecycle_replay_attribution(
    rows: list[dict[str, Any]],
    *,
    target_date: str,
    probe_arm_transition_summary: dict[str, Any],
) -> dict[str, Any]:
    """Separate path-proxy evidence from observed real lifecycle evidence.

    A candidate replay has no historical broker fill of its own.  The report can
    therefore evaluate the completed-bar one-share path and join the natural
    control lifecycle, but it must not invent residual, scale-in, trailing, or
    realized PnL for a counterfactual candidate.
    """

    candidate_state_join = _attach_entry_candidate_lifecycle_states(
        rows,
        target_date=target_date,
    )
    entry_rows = [row for row in rows if _stage(row.get("stage")) == "entry"]
    control_exposure_rows = [
        row for row in entry_rows if row.get("control_exposure_selected") is True
    ]
    candidate_exposure_rows = [
        row for row in entry_rows if row.get("candidate_exposure_selected") is True
    ]
    candidate_probe_arm_rows = [
        row for row in entry_rows if row.get("candidate_probe_armed") is True
    ]

    def proxy_values(source_rows: list[dict[str, Any]]) -> list[float]:
        return [
            value
            for row in source_rows
            if (value := _entry_probe_path_proxy_value(row)) is not None
        ]

    control_proxy_values = proxy_values(control_exposure_rows)
    candidate_proxy_values = proxy_values(candidate_exposure_rows)
    probe_arm_proxy_values = proxy_values(candidate_probe_arm_rows)
    correlation_rows = [
        (row, row.get("lifecycle_correlation"))
        for row in entry_rows
        if isinstance(row.get("lifecycle_correlation"), dict)
    ]
    exact_correlations = [
        (entry_row, correlation)
        for entry_row, correlation in correlation_rows
        if correlation.get("status") == "exact_matched"
    ]
    deduped_lifecycle: dict[tuple[Any, ...], dict[str, Any]] = {}
    for entry_row, correlation in exact_correlations:
        key: tuple[Any, ...] = (
            tuple(correlation.get("position_cycle_ids") or []),
            tuple(correlation.get("probe_bundle_ids") or []),
            tuple(correlation.get("broker_order_nos") or []),
        )
        if not any(key):
            key = (str(entry_row.get("decision_trace_id") or ""),)
        deduped_lifecycle.setdefault(key, correlation)
    realized_values = [
        value
        for row in deduped_lifecycle.values()
        if (value := _number(row.get("realized_profit_pct"))) is not None
    ]
    observed_stage_presence_counts = Counter(
        stage
        for row in deduped_lifecycle.values()
        for stage, present in (row.get("lifecycle_stage_presence") or {}).items()
        if present is True
    )
    candidate_source_audit = _entry_candidate_lifecycle_source_audit(
        entry_rows,
        source_inventory=_entry_lifecycle_source_inventory(target_date),
    )
    return {
        "schema": "entry_lifecycle_replay_attribution_v1",
        "metric_role": "sim_probe_ev",
        "decision_authority": "offline_path_and_observed_lifecycle_attribution_only",
        "window_policy": (
            "same_exact_entry_snapshot_completed_1m_path_plus_natural_trace_lifecycle"
        ),
        "sample_floor": {
            "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
        },
        "primary_decision_metric": (
            "candidate_probe_path_proxy_source_quality_adjusted_ev_pct"
        ),
        "source_quality_gate": "exact_v2_same_route_completed_bar_and_trace_join",
        "path_proxy_contract": {
            "target_first_value_pct": "entry_path_target_pct_minus_cost",
            "adverse_first_value_pct": "entry_path_adverse_pct_minus_cost",
            "neither_hit_value_pct": "primary_horizon_end_return_minus_cost",
            "same_bar_ambiguous": "excluded",
            "realized_pnl_equivalent": False,
        },
        "control_exposure_count": len(control_exposure_rows),
        "control_probe_path_proxy_evaluable_count": len(control_proxy_values),
        "control_probe_path_proxy_source_quality_adjusted_ev_pct": (
            fmean(control_proxy_values) if control_proxy_values else None
        ),
        "candidate_immediate_exposure_count": len(candidate_exposure_rows),
        "candidate_probe_path_proxy_evaluable_count": len(candidate_proxy_values),
        "candidate_probe_path_proxy_source_quality_adjusted_ev_pct": (
            fmean(candidate_proxy_values) if candidate_proxy_values else None
        ),
        "candidate_probe_arm_count": len(candidate_probe_arm_rows),
        "candidate_probe_arm_path_proxy_evaluable_count": len(probe_arm_proxy_values),
        "candidate_probe_arm_path_proxy_stress_source_quality_adjusted_ev_pct": (
            fmean(probe_arm_proxy_values) if probe_arm_proxy_values else None
        ),
        "probe_arm_transition_summary": probe_arm_transition_summary,
        "observed_natural_lifecycle": {
            "exact_trace_join_count": len(exact_correlations),
            "deduped_lifecycle_count": len(deduped_lifecycle),
            "decision_event_join_semantics": (
                "repeated_decision_trace_joins_are_deduped_by_position_probe_order_ids"
            ),
            "actual_order_submitted_count": sum(
                row.get("actual_order_submitted") is True
                for row in deduped_lifecycle.values()
            ),
            "fill_observed_count": sum(
                row.get("fill_observed") is True for row in deduped_lifecycle.values()
            ),
            "realized_profit_observed_count": len(realized_values),
            "realized_profit_equal_weight_avg_profit_pct": (
                fmean(realized_values) if realized_values else None
            ),
            "lifecycle_stage_presence_counts": dict(observed_stage_presence_counts),
            "candidate_counterfactual_attribution_allowed": False,
        },
        "candidate_full_lifecycle_source_audit": candidate_source_audit,
        "candidate_lifecycle_state_join": candidate_state_join,
        "replay_component_status": {
            "one_share_probe_first": "completed_bar_path_proxy_available",
            "post_probe_recheck": (
                "next_exact_transition_attribution_available"
                if probe_arm_transition_summary.get("waiting_decision_count")
                else "no_waiting_probe_arm_sample"
            ),
            "residual_multi_leg": "not_counterfactually_replayed",
            "scale_in": "not_counterfactually_replayed",
            "holding_exit": "natural_trace_observation_only_not_candidate_replay",
        },
        "full_lifecycle_counterfactual_status": candidate_source_audit["status"],
        "full_lifecycle_counterfactual_ev_pct": None,
        "bounded_one_share_replay_status": (
            "path_proxy_available"
            if candidate_proxy_values or probe_arm_proxy_values
            else "no_evaluable_candidate_probe_path"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "treat_path_proxy_as_realized_pnl",
            "attribute_natural_control_fill_or_exit_to_candidate",
            "assume_residual_multi_leg_or_scale_in_execution",
            "standalone_live_prompt_promotion",
            "provider_model_threshold_price_quantity_or_cap_change",
            "broker_or_safety_guard_bypass",
            "bot_restart",
        ],
    }


def _anticipatory_cumulative_learning_summary(
    *,
    target_date: str,
    current_rows: list[dict[str, Any]],
    candidate_prompt_version: str,
    candidate_contract_sha256: str | None,
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> dict[str, Any]:
    """Recompute one venue/session offline ledger from versioned reports."""

    rows_by_trace: dict[str, dict[str, Any]] = {}
    cohort_isolated = bool(effective_venue and session_bucket)
    pattern = f"ai_prompt_detailed_paired_replay_*_{candidate_prompt_version}*.json"
    historical_paths = (
        sorted(DETAILED_PAIRED_REPORT_DIR.glob(pattern)) if cohort_isolated else []
    )
    accepted_historical_report_count = 0
    for path in historical_paths:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        source_date = match.group(1) if match else ""
        if not source_date or source_date < "2026-06-05" or source_date >= target_date:
            continue
        report = _load_json(path)
        if (
            report.get("target_date") != source_date
            or report.get("runtime_effect") is not False
            or report.get("allowed_runtime_apply") is not False
            or report.get("broker_order_forbidden") is not True
            or not isinstance(report.get("candidate_execution_selection"), dict)
            or report["candidate_execution_selection"].get("outcome_blind") is not True
            or report["candidate_execution_selection"].get("contract_pass") is not True
            or report.get("promotion_report_integrity_pass") is not True
        ):
            continue
        if (
            candidate_contract_sha256
            and report.get("candidate_contract_sha256") != candidate_contract_sha256
        ):
            continue
        accepted_historical_report_count += 1
        for row in report.get("paired_comparisons") or []:
            if not isinstance(row, dict):
                continue
            if (
                _venue(row.get("effective_venue")) != effective_venue
                or _session(row.get("session_bucket")) != session_bucket
            ):
                continue
            trace_id = str(row.get("decision_trace_id") or "")
            if trace_id:
                rows_by_trace[trace_id] = dict(row)
    for row in current_rows:
        if cohort_isolated and (
            _venue(row.get("effective_venue")) != effective_venue
            or _session(row.get("session_bucket")) != session_bucket
        ):
            continue
        trace_id = str(row.get("decision_trace_id") or "")
        if trace_id:
            rows_by_trace[trace_id] = dict(row)
    cumulative_rows = list(rows_by_trace.values())
    exposure_rows = [
        row for row in cumulative_rows if row.get("candidate_exposure_selected") is True
    ]
    probe_arm_rows = [
        row for row in cumulative_rows if row.get("candidate_probe_armed") is True
    ]
    recheck_rows = [
        row for row in cumulative_rows if row.get("entry_recheck_intent") is True
    ]
    exposure_symbols = {
        str(row.get("stock_code") or "")
        for row in exposure_rows
        if row.get("stock_code")
    }
    probe_arm_symbols = {
        str(row.get("stock_code") or "")
        for row in probe_arm_rows
        if row.get("stock_code")
    }
    control_values = [
        _number(row.get("control_decision_value_pct")) for row in cumulative_rows
    ]
    control_values = [value for value in control_values if value is not None]
    candidate_values = [
        _number(row.get("candidate_decision_value_pct")) for row in cumulative_rows
    ]
    candidate_values = [value for value in candidate_values if value is not None]
    source_quality_delta_values = [
        candidate - control
        for control, candidate in zip(
            (_number(row.get("control_decision_value_pct")) for row in cumulative_rows),
            (
                _number(row.get("candidate_decision_value_pct"))
                for row in cumulative_rows
            ),
        )
        if control is not None and candidate is not None
    ]
    control_primary_values = [
        _number(row.get("control_primary_decision_value_pct"))
        for row in cumulative_rows
    ]
    control_primary_values = [
        value for value in control_primary_values if value is not None
    ]
    candidate_primary_values = [
        _number(row.get("candidate_primary_decision_value_pct"))
        for row in cumulative_rows
    ]
    candidate_primary_values = [
        value for value in candidate_primary_values if value is not None
    ]
    primary_delta_values = [_number(row.get("delta_pct")) for row in cumulative_rows]
    primary_delta_values = [
        value for value in primary_delta_values if value is not None
    ]
    exposure_adjusted_values = [
        _number(row.get("candidate_primary_decision_value_pct"))
        for row in exposure_rows
    ]
    exposure_adjusted_values = [
        value for value in exposure_adjusted_values if value is not None
    ]
    adverse_exposure_count = sum(
        str(row.get("first_hit") or "") == "adverse"
        or str(row.get("entry_path_first_hit") or "") == "adverse_first"
        for row in exposure_rows
    )
    probe_worst_losses = [
        _number(row.get("candidate_probe_worst_loss_pct")) for row in exposure_rows
    ]
    cumulative_probe_risk_budget = _bounded_probe_risk_budget(exposure_rows)
    cumulative_probe_arm_risk_budget = _bounded_probe_risk_budget(
        [
            {
                **row,
                "candidate_probe_worst_loss_pct": row.get(
                    "candidate_probe_arm_worst_loss_pct"
                ),
                "candidate_probe_severe_tail_exposure": row.get(
                    "candidate_probe_arm_severe_tail_exposure"
                ),
            }
            for row in probe_arm_rows
        ]
    )
    cumulative_exposure_cost_contract_complete = bool(exposure_rows) and all(
        row.get("candidate_execution_cost_contract_applied") is True
        and _number(row.get("candidate_execution_cost_pct")) is not None
        for row in exposure_rows
    )
    opportunity_capture = _opportunity_capture_tradeoff(cumulative_rows)
    cumulative_control_recovery_capture_count = sum(
        row.get("control_drawdown_recovery_captured") is True for row in cumulative_rows
    )
    cumulative_candidate_recovery_capture_count = sum(
        row.get("candidate_drawdown_recovery_captured") is True
        for row in cumulative_rows
    )
    promotion_floor_pass = bool(
        len(exposure_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
        and len(exposure_symbols) >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
    )
    cumulative_candidate_primary_ev = (
        fmean(candidate_primary_values) if candidate_primary_values else None
    )
    cumulative_primary_delta = (
        fmean(primary_delta_values) if primary_delta_values else None
    )
    cumulative_exposure_ev = (
        fmean(exposure_adjusted_values) if exposure_adjusted_values else None
    )
    promotion_quality_checks = {
        "cohort_isolated": cohort_isolated,
        "candidate_exposure_sample_floor_pass": promotion_floor_pass,
        "candidate_primary_decision_ev_positive": (
            cumulative_candidate_primary_ev is not None
            and cumulative_candidate_primary_ev > 0
        ),
        "candidate_primary_decision_ev_improved": (
            cumulative_primary_delta is not None and cumulative_primary_delta > 0
        ),
        "candidate_exposure_probe_cost_adjusted_ev_positive": (
            cumulative_exposure_cost_contract_complete
            and cumulative_exposure_ev is not None
            and cumulative_exposure_ev > 0
        ),
        "candidate_probe_bounded_risk_budget_pass": (
            cumulative_probe_risk_budget["pass"]
        ),
        "opportunity_capture_expanded": opportunity_capture[
            "opportunity_capture_expanded"
        ],
        "missed_upside_tradeoff_not_worse": opportunity_capture[
            "missed_upside_tradeoff_not_worse"
        ],
        "drawdown_recovery_capture_not_decreased": (
            cumulative_candidate_recovery_capture_count
            >= cumulative_control_recovery_capture_count
        ),
    }
    recheck_stress_values = []
    for row in recheck_rows:
        outcome = _number(row.get("outcome_return_pct"))
        cost = _number(row.get("conservative_execution_cost_pct"))
        if outcome is not None and cost is not None:
            recheck_stress_values.append(outcome - cost)
    return {
        "schema": "anticipatory_reversal_cumulative_learning_v2",
        "status": (
            "cumulative_learning_updated"
            if cumulative_rows
            else "cumulative_learning_no_sample"
        ),
        "candidate_prompt_version": candidate_prompt_version,
        "candidate_contract_sha256": candidate_contract_sha256,
        "cohort_scope": {
            "effective_venue": effective_venue,
            "session_bucket": session_bucket,
            "isolated": cohort_isolated,
            "discovered_historical_report_count": len(historical_paths),
            "accepted_historical_report_count": accepted_historical_report_count,
            "cross_cohort_aggregation_forbidden": True,
        },
        "clean_tuning_baseline_date": "2026-06-05",
        "as_of_date": target_date,
        "decision_count": len(cumulative_rows),
        "unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in cumulative_rows
                if row.get("stock_code")
            }
        ),
        "candidate_exposure_decision_count": len(exposure_rows),
        "candidate_exposure_unique_symbol_count": len(exposure_symbols),
        "candidate_probe_arm_decision_count": len(probe_arm_rows),
        "candidate_probe_arm_unique_symbol_count": len(probe_arm_symbols),
        "exploration_evidence_floor": {
            "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            "pass": bool(
                len(probe_arm_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
                and len(probe_arm_symbols) >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
            ),
            "authority": "bounded_one_share_exploration_candidate_only",
            "performance_promotion_authority": False,
        },
        "primary_decision_metric": "candidate_primary_decision_ev_pct",
        "control_source_quality_adjusted_ev_pct": (
            fmean(control_values) if control_values else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            fmean(candidate_values) if candidate_values else None
        ),
        "source_quality_adjusted_ev_delta_pct": (
            fmean(source_quality_delta_values) if source_quality_delta_values else None
        ),
        "control_primary_decision_ev_pct": (
            fmean(control_primary_values) if control_primary_values else None
        ),
        "candidate_primary_decision_ev_pct": cumulative_candidate_primary_ev,
        "candidate_primary_decision_ev_delta_pct": cumulative_primary_delta,
        "candidate_exposure_probe_cost_adjusted_ev_pct": cumulative_exposure_ev,
        "opportunity_capture_tradeoff": opportunity_capture,
        "candidate_execution_cost_adjusted_ev_pct": (
            fmean(candidate_primary_values) if candidate_primary_values else None
        ),
        "adverse_first_candidate_exposure_count": adverse_exposure_count,
        "candidate_probe_loss_budget_breach_count": sum(
            value is not None and value < -OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT
            for value in probe_worst_losses
        ),
        "candidate_probe_severe_tail_exposure_count": sum(
            row.get("candidate_probe_severe_tail_exposure") is True
            for row in exposure_rows
        ),
        "candidate_probe_risk_budget": cumulative_probe_risk_budget,
        "candidate_probe_arm_risk_budget": {
            **cumulative_probe_arm_risk_budget,
            "metric_role": "counterfactual_exploration_risk_diagnostic",
            "decision_authority": "diagnostic_only_not_performance_promotion_veto",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "candidate_recheck_intent_count": len(recheck_rows),
        "candidate_recheck_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in recheck_rows
                if row.get("stock_code")
            }
        ),
        "candidate_recheck_reason_counts": dict(
            Counter(
                reason
                for row in recheck_rows
                for reason in row.get("entry_recheck_reasons") or []
            )
        ),
        "candidate_recheck_reason_breakdown": _entry_recheck_reason_breakdown(
            recheck_rows
        ),
        "recheck_immediate_exposure_stress_source_quality_adjusted_ev_pct": (
            fmean(recheck_stress_values) if recheck_stress_values else None
        ),
        "recheck_target_first_count": sum(
            str(row.get("entry_path_first_hit") or "") == "target_first"
            for row in recheck_rows
        ),
        "recheck_adverse_first_count": sum(
            str(row.get("entry_path_first_hit") or "") == "adverse_first"
            for row in recheck_rows
        ),
        "recheck_severe_tail_stress_count": sum(
            row.get("probe_severe_tail_adverse") is True for row in recheck_rows
        ),
        "tail_risk_probe_prevented_count": sum(
            "TAIL_LIQUIDITY_RECHECK" in (row.get("entry_recheck_reasons") or [])
            and row.get("candidate_exposure_selected") is not True
            for row in recheck_rows
        ),
        "candidate_error_taxonomy_counts": dict(
            Counter(
                error
                for row in cumulative_rows
                for error in row.get("candidate_error_taxonomy") or []
            )
        ),
        "learning_update_floor": {
            "decision_rows": ANTICIPATORY_LEARNING_MIN_ROWS,
            "unique_symbols": ANTICIPATORY_LEARNING_MIN_SYMBOLS,
            "pass": bool(cumulative_rows),
            "role": "start_or_update_observation_only",
        },
        "promotion_evidence_floor": {
            "candidate_exposure_decision_rows": (PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS),
            "candidate_exposure_unique_symbols": (
                PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
            ),
            "pass": promotion_floor_pass,
            "promotion_authority": False,
        },
        "promotion_quality_checks": promotion_quality_checks,
        "promotion_quality_gate_pass": all(promotion_quality_checks.values()),
        "update_policy": (
            "append_daily_exact_rows_dedupe_trace_then_recompute_cumulative"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "single_sample_live_promotion",
            "realized_pnl_claim",
            "runtime_threshold_or_prompt_mutation",
        ],
    }


def build_paired_replay_report(
    *,
    target_date: str,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]] | None = None,
    labels: list[dict[str, Any]] | None = None,
    execution_selection: dict[str, Any] | None = None,
    prepared_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    results = list(results or [])
    candidate_execution_requested = bool(results or execution_selection is not None)
    prepared_census_provided = prepared_requests is not None
    all_prepared_requests = list(prepared_requests or requests)
    if execution_selection is None:
        execution_selection = {
            "policy": "complete_evaluated_request_census",
            "outcome_blind": True,
            "eligible_pending_count": len(requests),
            "selected_new_count": len(requests),
            "deferred_new_count": 0,
            "selected_unique_symbol_count": len(
                {
                    _normalize_stock_code(row.get("stock_code"))
                    for row in requests
                    if _normalize_stock_code(row.get("stock_code"))
                }
            ),
            "contract_pass": True,
        }
    else:
        execution_selection = dict(execution_selection)
    execution_selection_contract_pass = bool(
        execution_selection.get("outcome_blind") is True
        and execution_selection.get("contract_pass") is True
    )
    label_by_trace = {
        str(row.get("decision_trace_id")): row
        for row in labels or []
        if row.get("source_quality_status") == "pass"
    }
    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in requests
        if isinstance(row, dict)
    }
    request_by_pair = {
        str(row.get("paired_replay_id") or ""): row
        for row in requests
        if isinstance(row, dict) and row.get("paired_replay_id")
    }
    comparable_rows: list[dict[str, Any]] = []
    candidate_contract_integrity_rejected_count = 0
    for result in results:
        if (
            result.get("status") != "pass"
            or result.get("same_payload_confirmed") is not True
            or (
                result.get("entry_setup_evidence_sha256")
                and result.get("entry_setup_evidence_confirmed") is not True
            )
        ):
            continue
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_pair.get(
            str(result.get("paired_replay_id") or ""),
            request_by_trace.get(trace_id) or {},
        )
        candidate_contract = request.get("candidate")
        candidate_contract = (
            candidate_contract if isinstance(candidate_contract, dict) else {}
        )
        declared_candidate_contract_sha256 = str(
            candidate_contract.get("contract_sha256") or ""
        )
        computed_candidate_contract_sha256 = (
            _candidate_contract_sha256(candidate_contract)
            if declared_candidate_contract_sha256
            else ""
        )
        if declared_candidate_contract_sha256 and (
            declared_candidate_contract_sha256 != computed_candidate_contract_sha256
            or result.get("candidate_contract_sha256")
            != computed_candidate_contract_sha256
        ):
            candidate_contract_integrity_rejected_count += 1
            continue
        if candidate_contract.get(
            "semantic_validator_version"
        ) == ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION and (
            not request.get("entry_setup_evidence_sha256")
            or result.get("entry_setup_evidence_sha256")
            != request.get("entry_setup_evidence_sha256")
            or result.get("entry_setup_evidence_confirmed") is not True
            or (
                candidate_contract.get("response_schema_instance_sha256")
                and result.get("candidate_response_schema_instance_sha256")
                != candidate_contract.get("response_schema_instance_sha256")
            )
        ):
            candidate_contract_integrity_rejected_count += 1
            continue
        label = label_by_trace.get(str(result.get("decision_trace_id") or ""))
        preferred = _primary_metric(label) if isinstance(label, dict) else None
        preferred = preferred or {}
        outcome = _number(preferred.get("end_return_pct"))
        if outcome is None:
            continue
        control_response = result.get("control_response") or {}
        control_response = (
            control_response if isinstance(control_response, dict) else {}
        )
        candidate_response = result.get("candidate_response") or {}
        candidate_response = (
            candidate_response if isinstance(candidate_response, dict) else {}
        )
        control_action = str(control_response.get("action") or "").upper()
        candidate_action = str(candidate_response.get("action") or "").upper()
        comparison_stage = _stage(
            result.get("stage"),
            label.get("decision_stage") if isinstance(label, dict) else None,
        )

        control_value = _decision_value(control_action, outcome)
        candidate_value = _decision_value(candidate_action, outcome)
        if control_value is None or candidate_value is None:
            continue
        anticipatory_analysis = request.get("anticipatory_reversal_analysis")
        anticipatory_analysis = (
            anticipatory_analysis if isinstance(anticipatory_analysis, dict) else {}
        )
        execution_cost = anticipatory_analysis.get("execution_cost")
        execution_cost = execution_cost if isinstance(execution_cost, dict) else {}
        spread = anticipatory_analysis.get("spread")
        spread = spread if isinstance(spread, dict) else {}
        clean_continuation = anticipatory_analysis.get("clean_continuation_probe")
        clean_continuation = (
            clean_continuation if isinstance(clean_continuation, dict) else {}
        )
        selective_recovery = anticipatory_analysis.get("selective_recovery_probe")
        selective_recovery = (
            selective_recovery if isinstance(selective_recovery, dict) else {}
        )
        recovery_confirmation = anticipatory_analysis.get("recovery_confirmation_probe")
        recovery_confirmation = (
            recovery_confirmation if isinstance(recovery_confirmation, dict) else {}
        )
        execution_cost_contract_applied = bool(
            candidate_contract.get("exposure_semantics")
            == "offline_counterfactual_passive_probe_only"
        )
        control_exposure_selected = _decision_exposure_selected(
            stage=comparison_stage,
            action=control_action,
            response=control_response,
        )
        candidate_exposure_selected = _decision_exposure_selected(
            stage=comparison_stage,
            action=candidate_action,
            response=candidate_response,
        )
        control_probe_armed = _decision_probe_armed(
            stage=comparison_stage,
            action=control_action,
            response=control_response,
        )
        candidate_probe_armed = _decision_probe_armed(
            stage=comparison_stage,
            action=candidate_action,
            response=candidate_response,
        )
        control_execution_cost_pct = (
            _number(execution_cost.get("conservative_execution_cost_pct"))
            if execution_cost_contract_applied and control_exposure_selected
            else 0.0 if execution_cost_contract_applied else None
        )
        candidate_execution_cost_pct = (
            _number(execution_cost.get("conservative_execution_cost_pct"))
            if execution_cost_contract_applied and candidate_exposure_selected
            else 0.0 if execution_cost_contract_applied else None
        )
        control_primary_value = (
            (outcome if control_exposure_selected else 0.0)
            - (control_execution_cost_pct or 0.0)
            if execution_cost_contract_applied
            else control_value
        )
        candidate_execution_cost_adjusted_value = (
            (outcome if candidate_exposure_selected else 0.0)
            - (candidate_execution_cost_pct or 0.0)
            if execution_cost_contract_applied
            else candidate_value
        )
        primary_candidate_value = (
            candidate_execution_cost_adjusted_value
            if execution_cost_contract_applied
            else candidate_value
        )
        mfe = _number(preferred.get("mfe_pct"))
        mae = _number(preferred.get("mae_pct"))
        first_hit = str(preferred.get("first_hit") or "")
        entry_path_first_hit = str(preferred.get("entry_path_first_hit") or "")
        profit_opportunity_observed = preferred.get("profit_opportunity_observed")
        if profit_opportunity_observed is None:
            profit_opportunity_observed = bool(
                mfe is not None and mfe >= PROFIT_OPPORTUNITY_THRESHOLD_PCT
            )
        else:
            profit_opportunity_observed = bool(profit_opportunity_observed)
        profit_opportunity_sequence = str(
            preferred.get("profit_opportunity_sequence") or "not_recorded_legacy"
        )
        pre_profit_mae = _number(preferred.get("pre_profit_mae_pct"))
        conservative_execution_cost_pct = _number(
            execution_cost.get("conservative_execution_cost_pct")
        )
        probe_path_risk = _probe_path_risk(
            request=request,
            outcome_mfe_pct=mfe,
            outcome_mae_pct=mae,
            pre_profit_mae_pct=pre_profit_mae,
            entry_path_first_hit=entry_path_first_hit,
            profit_opportunity_sequence=profit_opportunity_sequence,
            conservative_execution_cost_pct=conservative_execution_cost_pct,
        )
        candidate_errors: list[str] = []
        stage_outcome = label.get("stage_outcome")
        stage_outcome = stage_outcome if isinstance(stage_outcome, dict) else {}
        post_block_outcome = stage_outcome.get("rising_missed_post_block_outcome")
        post_block_outcome = (
            post_block_outcome if isinstance(post_block_outcome, dict) else {}
        )
        if candidate_action == "DROP" and profit_opportunity_observed:
            candidate_errors.append("false_drop")
            if profit_opportunity_sequence == "drawdown_then_profit_recovery":
                candidate_errors.append("false_drop_drawdown_recovery")
            elif profit_opportunity_sequence in {
                "profit_without_prior_drawdown",
                "profit_before_drawdown",
            }:
                candidate_errors.append("false_drop_direct_profit")
            elif profit_opportunity_sequence == "ambiguous_same_bar":
                candidate_errors.append("false_drop_same_bar_sequence_ambiguous")
        if (
            candidate_action == "DROP"
            and post_block_outcome.get("gross_first_hit_label") == "gross_target_first"
            and post_block_outcome.get("source_quality_status") == "pass"
        ):
            candidate_errors.append("false_drop_post_block_gross_target_first")
        if (
            not candidate_exposure_selected
            and candidate_action == "WAIT"
            and mfe is not None
            and mfe >= 1.0
        ):
            candidate_errors.append("false_wait")
        if candidate_exposure_selected and (
            first_hit == "adverse" or (mae is not None and mae <= -1.0)
        ):
            candidate_errors.append("false_buy")
        if (
            comparison_stage == "entry"
            and candidate_exposure_selected
            and entry_path_first_hit == "adverse_first"
        ):
            candidate_errors.append("false_buy_tight_stop_adverse_first")
        if (
            comparison_stage == "entry"
            and not candidate_exposure_selected
            and entry_path_first_hit == "target_first"
        ):
            candidate_errors.append("missed_entry_tight_stop_target_first")
        comparable_rows.append(
            {
                "decision_trace_id": trace_id,
                "paired_replay_id": result.get("paired_replay_id"),
                "decision_ts": request.get("decision_ts") or label.get("decision_ts"),
                "stock_code": request.get("stock_code"),
                "stage": comparison_stage,
                "effective_venue": result.get("effective_venue"),
                "session_bucket": result.get("session_bucket"),
                "control_action": control_action,
                "candidate_action": candidate_action,
                "outcome_return_pct": outcome,
                "control_decision_value_pct": control_value,
                "control_primary_decision_value_pct": control_primary_value,
                "candidate_decision_value_pct": candidate_value,
                "control_exposure_selected": control_exposure_selected,
                "candidate_exposure_selected": candidate_exposure_selected,
                "control_probe_armed": control_probe_armed,
                "candidate_probe_armed": candidate_probe_armed,
                "control_entry_probe_intent": (
                    control_response.get("entry_probe_intent") is True
                ),
                "candidate_execution_cost_contract_applied": (
                    execution_cost_contract_applied
                ),
                "control_execution_cost_pct": control_execution_cost_pct,
                "candidate_execution_cost_pct": candidate_execution_cost_pct,
                "conservative_execution_cost_pct": conservative_execution_cost_pct,
                "conservative_spread_bp": _number(spread.get("spread_bp")),
                "reference_price": _number(request.get("reference_price")),
                "best_bid": _number(request.get("best_bid")),
                "best_ask": _number(request.get("best_ask")),
                "candidate_execution_cost_adjusted_decision_value_pct": (
                    candidate_execution_cost_adjusted_value
                ),
                "candidate_primary_decision_value_pct": primary_candidate_value,
                "delta_pct": primary_candidate_value - control_primary_value,
                "control_missed_upside": (
                    not control_exposure_selected and outcome > 0
                ),
                "candidate_missed_upside": (
                    not candidate_exposure_selected and outcome > 0
                ),
                "outcome_mfe_pct": mfe,
                "outcome_mae_pct": mae,
                "first_hit": first_hit,
                "entry_path_first_hit": entry_path_first_hit or None,
                "entry_path_target_pct": preferred.get("entry_path_target_pct"),
                "entry_path_adverse_pct": preferred.get("entry_path_adverse_pct"),
                "profit_opportunity_threshold_pct": (
                    _number(preferred.get("profit_opportunity_threshold_pct"))
                    or PROFIT_OPPORTUNITY_THRESHOLD_PCT
                ),
                "profit_opportunity_observed": profit_opportunity_observed,
                "profit_opportunity_hit_at": preferred.get("profit_opportunity_hit_at"),
                "below_reference_excursion_at": preferred.get(
                    "below_reference_excursion_at"
                ),
                "profit_opportunity_sequence": profit_opportunity_sequence,
                "pre_profit_mae_pct": pre_profit_mae,
                **probe_path_risk,
                "control_probe_worst_loss_pct": (
                    probe_path_risk["probe_worst_loss_pct"]
                    if control_exposure_selected
                    else 0.0
                ),
                "candidate_probe_worst_loss_pct": (
                    probe_path_risk["probe_worst_loss_pct"]
                    if candidate_exposure_selected
                    else 0.0
                ),
                "candidate_probe_arm_worst_loss_pct": (
                    probe_path_risk["probe_worst_loss_pct"]
                    if candidate_probe_armed
                    else 0.0
                ),
                "control_probe_severe_tail_exposure": bool(
                    control_exposure_selected
                    and probe_path_risk["probe_severe_tail_adverse"]
                ),
                "candidate_probe_severe_tail_exposure": bool(
                    candidate_exposure_selected
                    and probe_path_risk["probe_severe_tail_adverse"]
                ),
                "candidate_probe_arm_severe_tail_exposure": bool(
                    candidate_probe_armed
                    and probe_path_risk["probe_severe_tail_adverse"]
                ),
                "control_drawdown_recovery_captured": bool(
                    control_exposure_selected
                    and probe_path_risk["drawdown_recovery_observed"]
                ),
                "candidate_drawdown_recovery_captured": bool(
                    candidate_exposure_selected
                    and probe_path_risk["drawdown_recovery_observed"]
                ),
                "rising_missed_post_block_outcome": post_block_outcome or None,
                "candidate_error_taxonomy": candidate_errors,
                "clean_continuation_probe_eligible": (
                    clean_continuation.get("eligible") is True
                ),
                "selective_recovery_probe_eligible": (
                    selective_recovery.get("eligible") is True
                ),
                "recovery_confirmation_probe_eligible": (
                    recovery_confirmation.get("eligible") is True
                ),
                "entry_setup_family": candidate_response.get("entry_setup_family"),
                "entry_setup_state": candidate_response.get("entry_setup_state"),
                "entry_ai_risk_verdict": candidate_response.get(
                    "entry_ai_risk_verdict"
                ),
                "entry_ai_risk_codes": list(
                    candidate_response.get("entry_ai_risk_codes") or []
                ),
                "entry_ai_veto_supported_codes": list(
                    candidate_response.get("entry_ai_veto_supported_codes") or []
                ),
                "entry_ai_bounded_risk_codes": list(
                    candidate_response.get("entry_ai_bounded_risk_codes") or []
                ),
                "entry_ai_veto_corroborated": candidate_response.get(
                    "entry_ai_veto_corroborated"
                ),
                "entry_recheck_intent": candidate_response.get("entry_recheck_intent"),
                "entry_recheck_reasons": list(
                    candidate_response.get("entry_recheck_reasons") or []
                ),
                "entry_bounded_recovery_policy_version": candidate_response.get(
                    "entry_bounded_recovery_policy_version"
                ),
                "entry_bounded_recovery_eligible": candidate_response.get(
                    "entry_bounded_recovery_eligible"
                ),
                "entry_bounded_recovery_path": candidate_response.get(
                    "entry_bounded_recovery_path"
                ),
                "entry_sequential_recovery_policy_version": candidate_response.get(
                    "entry_sequential_recovery_policy_version"
                ),
                "entry_sequential_recovery_seed_eligible": candidate_response.get(
                    "entry_sequential_recovery_seed_eligible"
                ),
                "entry_structure_phase_bar_end": candidate_response.get(
                    "entry_structure_phase_bar_end"
                ),
                "entry_tail_risk_state": candidate_response.get(
                    "entry_tail_risk_state"
                ),
                "entry_composed_action": candidate_response.get(
                    "entry_composed_action"
                ),
                "entry_composed_reason": candidate_response.get(
                    "entry_composed_reason"
                ),
                "lifecycle_correlation": (
                    dict(label.get("correlation") or {})
                    if isinstance(label.get("correlation"), dict)
                    else {}
                ),
                "candidate_counterfactual_lifecycle_state": (
                    dict(result.get("candidate_counterfactual_lifecycle_state") or {})
                    if isinstance(
                        result.get("candidate_counterfactual_lifecycle_state"), dict
                    )
                    else {}
                ),
            }
        )
    entry_recheck_transition_summary = _attach_entry_recheck_transitions(
        comparable_rows,
        prepared_requests=(all_prepared_requests if prepared_census_provided else None),
    )
    transition_observations = _prepared_entry_transition_observations(
        prepared_requests=all_prepared_requests,
        comparable_rows=comparable_rows,
    )
    sequential_recovery_summary = _attach_sequential_recovery_transitions(
        seed_rows=[
            row
            for row in comparable_rows
            if row.get("entry_sequential_recovery_seed_eligible") is True
        ],
        observations=transition_observations,
    )
    waiting_probe_arm_rows = [
        row
        for row in comparable_rows
        if row.get("candidate_probe_armed") is True
        and row.get("candidate_exposure_selected") is not True
    ]
    entry_probe_arm_transition_summary = _attach_wait_transition_continuity(
        waiting_rows=waiting_probe_arm_rows,
        observations=transition_observations,
        field_prefix="entry_probe_arm_continuity",
        contract_version="entry_probe_arm_next_exact_transition_v1",
        observation_source=(
            "full_prepared_exact_request_census"
            if prepared_census_provided
            else "evaluated_request_set_only"
        ),
    )
    entry_opportunity_funnel = _entry_opportunity_funnel_attribution(
        labels=list(labels or []),
        prepared_requests=all_prepared_requests,
        comparable_rows=comparable_rows,
        results=results,
        candidate_execution_requested=candidate_execution_requested,
    )
    rejected = sum(row.get("status") != "pass" for row in results)
    schema_rejected = sum(row.get("status") == "schema_rejected" for row in results)
    provider_failed = sum(row.get("status") == "provider_failed" for row in results)
    completed_pair_ids = {
        str(row.get("paired_replay_id") or "")
        for row in results
        if row.get("paired_replay_id")
    }
    missing_result_count = sum(
        str(row.get("paired_replay_id") or "") not in completed_pair_ids
        for row in requests
    )
    buckets: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in comparable_rows:
        grouped[
            (
                _stage(row.get("stage")) or "unknown",
                _venue(row.get("effective_venue")) or "UNKNOWN",
                _session(row.get("session_bucket")) or "UNKNOWN",
            )
        ].append(row)
    for (stage, venue, session), rows in sorted(grouped.items()):
        bucket_control_ev = fmean(row["control_decision_value_pct"] for row in rows)
        bucket_control_primary_ev = fmean(
            row["control_primary_decision_value_pct"] for row in rows
        )
        bucket_candidate_ev = fmean(row["candidate_decision_value_pct"] for row in rows)
        bucket_candidate_primary_ev = fmean(
            row["candidate_primary_decision_value_pct"] for row in rows
        )
        bucket_execution_cost_adjusted_ev = (
            fmean(
                row["candidate_execution_cost_adjusted_decision_value_pct"]
                for row in rows
            )
            if any(row["candidate_execution_cost_contract_applied"] for row in rows)
            else None
        )
        bucket_ev_delta = fmean(row["delta_pct"] for row in rows)
        bucket_source_quality_ev_delta = bucket_candidate_ev - bucket_control_ev
        bucket_missed_upside_reduction = sum(
            row["control_missed_upside"] and not row["candidate_missed_upside"]
            for row in rows
        )
        bucket_new_missed_upside = sum(
            not row["control_missed_upside"] and row["candidate_missed_upside"]
            for row in rows
        )
        bucket_opportunity_capture = _opportunity_capture_tradeoff(rows)
        bucket_control_adverse_exposure = sum(
            row["first_hit"] == "adverse" and row["control_exposure_selected"]
            for row in rows
        )
        bucket_candidate_adverse_exposure = sum(
            row["first_hit"] == "adverse" and row["candidate_exposure_selected"]
            for row in rows
        )
        bucket_control_tight_stop_adverse_exposure = sum(
            row["stage"] == "entry"
            and row["entry_path_first_hit"] == "adverse_first"
            and row["control_exposure_selected"]
            for row in rows
        )
        bucket_candidate_tight_stop_adverse_exposure = sum(
            row["stage"] == "entry"
            and row["entry_path_first_hit"] == "adverse_first"
            and row["candidate_exposure_selected"]
            for row in rows
        )
        bucket_exposure_rows = [
            row for row in rows if row["candidate_exposure_selected"]
        ]
        bucket_probe_arm_rows = [
            row for row in rows if row.get("candidate_probe_armed") is True
        ]
        bucket_probe_cost_contract_complete = bool(bucket_exposure_rows) and all(
            row["candidate_execution_cost_contract_applied"]
            and row["candidate_execution_cost_pct"] is not None
            for row in bucket_exposure_rows
        )
        bucket_probe_cost_adjusted_ev = (
            fmean(
                row["candidate_primary_decision_value_pct"]
                for row in bucket_exposure_rows
            )
            if bucket_probe_cost_contract_complete
            else None
        )
        bucket_probe_risk_budget = _bounded_probe_risk_budget(bucket_exposure_rows)
        bucket_control_severe_tail = sum(
            row["control_probe_severe_tail_exposure"] for row in rows
        )
        bucket_candidate_severe_tail = sum(
            row["candidate_probe_severe_tail_exposure"] for row in rows
        )
        bucket_control_recovery_capture = sum(
            row["control_drawdown_recovery_captured"] for row in rows
        )
        bucket_candidate_recovery_capture = sum(
            row["candidate_drawdown_recovery_captured"] for row in rows
        )
        bucket_exposure_symbols = {
            str(row.get("stock_code") or "")
            for row in bucket_exposure_rows
            if row.get("stock_code")
        }
        bucket_probe_arm_symbols = {
            str(row.get("stock_code") or "")
            for row in bucket_probe_arm_rows
            if row.get("stock_code")
        }
        bucket_exposure_floor_pass = (
            len(bucket_exposure_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
            and len(bucket_exposure_symbols) >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
        )
        bucket_action_counter = Counter(row["candidate_action"] for row in rows)
        bucket_dominant_action_ratio = max(bucket_action_counter.values()) / len(rows)
        bucket_quality_checks = {
            "source_quality_adjusted_ev_improved": (bucket_source_quality_ev_delta > 0),
            "primary_decision_ev_improved": bucket_ev_delta > 0,
            "candidate_ev_positive": bucket_candidate_primary_ev > 0,
            "opportunity_capture_expanded": bucket_opportunity_capture[
                "opportunity_capture_expanded"
            ],
            "missed_upside_tradeoff_not_worse": bucket_opportunity_capture[
                "missed_upside_tradeoff_not_worse"
            ],
            "drawdown_recovery_capture_not_decreased": (
                bucket_candidate_recovery_capture >= bucket_control_recovery_capture
            ),
            "candidate_exposure_sample_floor_pass": bucket_exposure_floor_pass,
        }
        if stage == "entry":
            bucket_quality_checks.update(
                {
                    "candidate_probe_cost_adjusted_ev_positive": (
                        bucket_probe_cost_adjusted_ev is not None
                        and bucket_probe_cost_adjusted_ev > 0
                    ),
                    "candidate_probe_bounded_risk_budget_pass": (
                        bucket_probe_risk_budget["pass"]
                    ),
                }
            )
        bucket_diagnostic_checks = {
            "adverse_first_exposure_not_increased": (
                bucket_candidate_adverse_exposure <= bucket_control_adverse_exposure
            ),
            "tight_stop_adverse_first_exposure_not_increased": (
                bucket_candidate_tight_stop_adverse_exposure
                <= bucket_control_tight_stop_adverse_exposure
            ),
            "severe_tail_adverse_not_increased": (
                bucket_candidate_severe_tail <= bucket_control_severe_tail
            ),
            "candidate_action_not_collapsed": bucket_dominant_action_ratio <= 0.90,
        }
        buckets.append(
            {
                "stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "sample_count": len(rows),
                "control_source_quality_adjusted_ev_pct": bucket_control_ev,
                "control_primary_decision_ev_pct": bucket_control_primary_ev,
                "candidate_source_quality_adjusted_ev_pct": bucket_candidate_ev,
                "candidate_execution_cost_adjusted_ev_pct": (
                    bucket_execution_cost_adjusted_ev
                ),
                "candidate_primary_decision_ev_pct": bucket_candidate_primary_ev,
                "source_quality_adjusted_ev_delta_pct": (
                    bucket_source_quality_ev_delta
                ),
                "candidate_primary_decision_ev_delta_pct": bucket_ev_delta,
                "missed_upside_reduction_count": bucket_missed_upside_reduction,
                "new_missed_upside_count": bucket_new_missed_upside,
                "opportunity_capture_tradeoff": bucket_opportunity_capture,
                "control_adverse_first_exposure_count": (
                    bucket_control_adverse_exposure
                ),
                "adverse_first_candidate_exposure_count": (
                    bucket_candidate_adverse_exposure
                ),
                "control_tight_stop_adverse_first_exposure_count": (
                    bucket_control_tight_stop_adverse_exposure
                ),
                "candidate_tight_stop_adverse_first_exposure_count": (
                    bucket_candidate_tight_stop_adverse_exposure
                ),
                "candidate_probe_cost_adjusted_ev_pct": (bucket_probe_cost_adjusted_ev),
                "candidate_probe_loss_budget_breach_count": sum(
                    row["candidate_probe_worst_loss_pct"] is not None
                    and row["candidate_probe_worst_loss_pct"]
                    < -OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT
                    for row in bucket_exposure_rows
                ),
                "candidate_probe_risk_budget": bucket_probe_risk_budget,
                "candidate_probe_risk_missing_count": sum(
                    row["candidate_probe_worst_loss_pct"] is None
                    for row in bucket_exposure_rows
                ),
                "control_probe_severe_tail_exposure_count": (
                    bucket_control_severe_tail
                ),
                "candidate_probe_severe_tail_exposure_count": (
                    bucket_candidate_severe_tail
                ),
                "control_drawdown_recovery_capture_count": (
                    bucket_control_recovery_capture
                ),
                "candidate_drawdown_recovery_capture_count": (
                    bucket_candidate_recovery_capture
                ),
                "spread_confounded_adverse_first_count": sum(
                    row["entry_path_adverse_first_spread_confounded"] for row in rows
                ),
                "candidate_exposure_decision_count": len(bucket_exposure_rows),
                "candidate_exposure_unique_symbol_count": len(bucket_exposure_symbols),
                "candidate_exposure_sample_floor_pass": (bucket_exposure_floor_pass),
                "candidate_probe_arm_decision_count": len(bucket_probe_arm_rows),
                "candidate_probe_arm_unique_symbol_count": len(
                    bucket_probe_arm_symbols
                ),
                "candidate_dominant_action_ratio": (bucket_dominant_action_ratio),
                "candidate_quality_checks": bucket_quality_checks,
                "diagnostic_checks_not_quality_veto": bucket_diagnostic_checks,
                "candidate_quality_gate_pass": all(bucket_quality_checks.values()),
                "candidate_error_taxonomy_counts": dict(
                    Counter(
                        error
                        for row in rows
                        for error in row["candidate_error_taxonomy"]
                    )
                ),
            }
        )
    control_ev = (
        fmean(row["control_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    control_primary_ev = (
        fmean(row["control_primary_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    candidate_ev = (
        fmean(row["candidate_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    execution_cost_contract_applied = any(
        row["candidate_execution_cost_contract_applied"] for row in comparable_rows
    )
    candidate_execution_cost_adjusted_ev = (
        fmean(
            row["candidate_execution_cost_adjusted_decision_value_pct"]
            for row in comparable_rows
        )
        if comparable_rows and execution_cost_contract_applied
        else None
    )
    candidate_primary_ev = (
        fmean(row["candidate_primary_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    source_quality_ev_delta = (
        candidate_ev - control_ev
        if candidate_ev is not None and control_ev is not None
        else None
    )
    ev_delta = (
        fmean(row["delta_pct"] for row in comparable_rows) if comparable_rows else None
    )
    missed_upside_reduction_count = sum(
        row["control_missed_upside"] and not row["candidate_missed_upside"]
        for row in comparable_rows
    )
    new_missed_upside_count = sum(
        not row["control_missed_upside"] and row["candidate_missed_upside"]
        for row in comparable_rows
    )
    opportunity_capture = _opportunity_capture_tradeoff(comparable_rows)
    control_adverse_first_exposure_count = sum(
        row["first_hit"] == "adverse" and row["control_exposure_selected"]
        for row in comparable_rows
    )
    candidate_adverse_first_exposure_count = sum(
        row["first_hit"] == "adverse" and row["candidate_exposure_selected"]
        for row in comparable_rows
    )
    control_tight_stop_adverse_first_exposure_count = sum(
        row["stage"] == "entry"
        and row["entry_path_first_hit"] == "adverse_first"
        and row["control_exposure_selected"]
        for row in comparable_rows
    )
    candidate_tight_stop_adverse_first_exposure_count = sum(
        row["stage"] == "entry"
        and row["entry_path_first_hit"] == "adverse_first"
        and row["candidate_exposure_selected"]
        for row in comparable_rows
    )
    candidate_exposure_rows = [
        row for row in comparable_rows if row["candidate_exposure_selected"]
    ]
    candidate_probe_arm_rows = [
        row for row in comparable_rows if row.get("candidate_probe_armed") is True
    ]
    candidate_probe_cost_contract_complete = bool(candidate_exposure_rows) and all(
        row["candidate_execution_cost_contract_applied"]
        and row["candidate_execution_cost_pct"] is not None
        for row in candidate_exposure_rows
    )
    candidate_probe_cost_adjusted_ev = (
        fmean(
            row["candidate_primary_decision_value_pct"]
            for row in candidate_exposure_rows
        )
        if candidate_probe_cost_contract_complete
        else None
    )
    candidate_probe_risk_budget = _bounded_probe_risk_budget(candidate_exposure_rows)
    candidate_probe_arm_risk_budget = _bounded_probe_risk_budget(
        [
            {
                **row,
                "candidate_probe_worst_loss_pct": row.get(
                    "candidate_probe_arm_worst_loss_pct"
                ),
                "candidate_probe_severe_tail_exposure": row.get(
                    "candidate_probe_arm_severe_tail_exposure"
                ),
            }
            for row in candidate_probe_arm_rows
        ]
    )
    entry_lifecycle_replay = _entry_lifecycle_replay_attribution(
        comparable_rows,
        target_date=target_date,
        probe_arm_transition_summary=entry_probe_arm_transition_summary,
    )
    control_probe_severe_tail_count = sum(
        row["control_probe_severe_tail_exposure"] for row in comparable_rows
    )
    candidate_probe_severe_tail_count = sum(
        row["candidate_probe_severe_tail_exposure"] for row in comparable_rows
    )
    control_recovery_capture_count = sum(
        row["control_drawdown_recovery_captured"] for row in comparable_rows
    )
    candidate_recovery_capture_count = sum(
        row["candidate_drawdown_recovery_captured"] for row in comparable_rows
    )
    candidate_exposure_symbol_count = len(
        {
            str(row.get("stock_code") or "")
            for row in candidate_exposure_rows
            if row.get("stock_code")
        }
    )
    candidate_probe_arm_symbol_count = len(
        {
            str(row.get("stock_code") or "")
            for row in candidate_probe_arm_rows
            if row.get("stock_code")
        }
    )
    candidate_probe_arm_floor_pass = bool(
        len(candidate_probe_arm_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
        and candidate_probe_arm_symbol_count >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
    )
    candidate_exposure_count_floor_pass = (
        len(candidate_exposure_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
        and candidate_exposure_symbol_count >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
    )
    cohort_keys = {
        (
            _stage(row.get("stage")) or "unknown",
            _venue(row.get("effective_venue")) or "UNKNOWN",
            _session(row.get("session_bucket")) or "UNKNOWN",
        )
        for row in comparable_rows
    }
    promotion_cohort_isolated = len(cohort_keys) == 1
    selected_cohort_venue = (
        next(iter(cohort_keys))[1] if promotion_cohort_isolated else "UNKNOWN"
    )
    candidate_contract_hashes = {
        str((request.get("candidate") or {}).get("contract_sha256") or "")
        for request in requests
        if isinstance(request.get("candidate"), dict)
        and (request.get("candidate") or {}).get("contract_sha256")
    }
    cumulative_candidate_contract_sha256 = (
        next(iter(candidate_contract_hashes))
        if len(candidate_contract_hashes) == 1
        else None
    )
    promotion_contract_isolated = bool(
        cumulative_candidate_contract_sha256
        or (not candidate_contract_hashes and not execution_cost_contract_applied)
    )
    selected_cohort_quality_pass = bool(
        promotion_cohort_isolated
        and promotion_contract_isolated
        and len(buckets) == 1
        and buckets[0]["candidate_quality_gate_pass"]
    )
    candidate_exposure_sample_floor_pass = bool(
        candidate_exposure_count_floor_pass
        and promotion_cohort_isolated
        and promotion_contract_isolated
        and len(buckets) == 1
        and buckets[0]["candidate_exposure_sample_floor_pass"]
    )
    valid_results = [row for row in results if row.get("status") == "pass"]
    candidate_action_counter = Counter(
        str((row.get("candidate_response") or {}).get("action") or "UNKNOWN")
        for row in valid_results
    )
    dominant_candidate_action_ratio = (
        max(candidate_action_counter.values()) / len(valid_results)
        if valid_results
        else None
    )
    candidate_drop_rows = [
        row for row in comparable_rows if row["candidate_action"] == "DROP"
    ]
    candidate_drop_profit_rows = [
        row for row in candidate_drop_rows if row["profit_opportunity_observed"]
    ]
    candidate_drop_trajectory = {
        "result_drop_count": candidate_action_counter.get("DROP", 0),
        "comparable_drop_count": len(candidate_drop_rows),
        "outcome_unavailable_drop_count": (
            candidate_action_counter.get("DROP", 0) - len(candidate_drop_rows)
        ),
        "profit_opportunity_threshold_pct": PROFIT_OPPORTUNITY_THRESHOLD_PCT,
        "profit_opportunity_count": len(candidate_drop_profit_rows),
        "drawdown_then_profit_recovery_count": sum(
            row["profit_opportunity_sequence"] == "drawdown_then_profit_recovery"
            for row in candidate_drop_profit_rows
        ),
        "direct_profit_count": sum(
            row["profit_opportunity_sequence"]
            in {"profit_without_prior_drawdown", "profit_before_drawdown"}
            for row in candidate_drop_profit_rows
        ),
        "same_bar_sequence_ambiguous_count": sum(
            row["profit_opportunity_sequence"] == "ambiguous_same_bar"
            for row in candidate_drop_profit_rows
        ),
        "positive_excursion_below_profit_count": sum(
            (row["outcome_mfe_pct"] or 0.0) > 0.0
            and not row["profit_opportunity_observed"]
            for row in candidate_drop_rows
        ),
        "no_positive_excursion_count": sum(
            (row["outcome_mfe_pct"] or 0.0) <= 0.0 for row in candidate_drop_rows
        ),
        "profit_sequence_counts": dict(
            Counter(row["profit_opportunity_sequence"] for row in candidate_drop_rows)
        ),
        "pre_profit_mae_buckets": {
            "nonnegative": sum(
                row["pre_profit_mae_pct"] is not None
                and row["pre_profit_mae_pct"] >= 0.0
                for row in candidate_drop_profit_rows
            ),
            "minus_0_to_0_5": sum(
                row["pre_profit_mae_pct"] is not None
                and -0.5 <= row["pre_profit_mae_pct"] < 0.0
                for row in candidate_drop_profit_rows
            ),
            "minus_0_5_to_1": sum(
                row["pre_profit_mae_pct"] is not None
                and -1.0 <= row["pre_profit_mae_pct"] < -0.5
                for row in candidate_drop_profit_rows
            ),
            "minus_1_to_2": sum(
                row["pre_profit_mae_pct"] is not None
                and -2.0 <= row["pre_profit_mae_pct"] < -1.0
                for row in candidate_drop_profit_rows
            ),
            "below_minus_2": sum(
                row["pre_profit_mae_pct"] is not None
                and row["pre_profit_mae_pct"] < -2.0
                for row in candidate_drop_profit_rows
            ),
            "not_recorded": sum(
                row["pre_profit_mae_pct"] is None for row in candidate_drop_profit_rows
            ),
        },
        "interpretation": (
            "DROP is not equivalent to a monotonic decline. Profit opportunity "
            "and drawdown-before-profit are evaluated separately."
        ),
    }
    clean_continuation_rows = [
        row for row in comparable_rows if row["clean_continuation_probe_eligible"]
    ]
    clean_continuation_exposure_rows = [
        row for row in clean_continuation_rows if row["candidate_exposure_selected"]
    ]
    clean_continuation_probe_summary = {
        "schema": "clean_continuation_probe_attribution_v1",
        "eligible_decision_count": len(clean_continuation_rows),
        "eligible_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in clean_continuation_rows
                if row.get("stock_code")
            }
        ),
        "candidate_exposure_decision_count": len(clean_continuation_exposure_rows),
        "candidate_not_exposed_decision_count": (
            len(clean_continuation_rows) - len(clean_continuation_exposure_rows)
        ),
        "candidate_exposure_coverage_pct": (
            len(clean_continuation_exposure_rows) / len(clean_continuation_rows) * 100.0
            if clean_continuation_rows
            else None
        ),
        "candidate_exposure_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in clean_continuation_exposure_rows
                if row.get("stock_code")
            }
        ),
        "eligible_cohort_after_cost_ev_pct": (
            fmean(
                row["outcome_return_pct"]
                - (row["conservative_execution_cost_pct"] or 0.0)
                for row in clean_continuation_rows
            )
            if clean_continuation_rows
            else None
        ),
        "candidate_selected_after_cost_ev_pct": (
            fmean(
                row["candidate_primary_decision_value_pct"]
                for row in clean_continuation_exposure_rows
            )
            if clean_continuation_exposure_rows
            else None
        ),
        "profit_opportunity_count": sum(
            row["profit_opportunity_observed"] for row in clean_continuation_rows
        ),
        "adverse_first_exposure_count": sum(
            row["first_hit"] == "adverse"
            or row["entry_path_first_hit"] == "adverse_first"
            for row in clean_continuation_exposure_rows
        ),
        "metric_role": "ai_decision_quality_opportunity_cohort_attribution",
        "decision_authority": "offline_replay_and_attribution_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    selective_recovery_rows = [
        row for row in comparable_rows if row["selective_recovery_probe_eligible"]
    ]
    selective_recovery_exposure_rows = [
        row for row in selective_recovery_rows if row["candidate_exposure_selected"]
    ]
    selective_recovery_probe_summary = {
        "schema": "selective_recovery_probe_attribution_v1",
        "eligible_decision_count": len(selective_recovery_rows),
        "eligible_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in selective_recovery_rows
                if row.get("stock_code")
            }
        ),
        "candidate_exposure_decision_count": len(selective_recovery_exposure_rows),
        "candidate_not_exposed_decision_count": (
            len(selective_recovery_rows) - len(selective_recovery_exposure_rows)
        ),
        "candidate_exposure_coverage_pct": (
            len(selective_recovery_exposure_rows) / len(selective_recovery_rows) * 100.0
            if selective_recovery_rows
            else None
        ),
        "eligible_cohort_after_cost_ev_pct": (
            fmean(
                row["outcome_return_pct"]
                - (row["conservative_execution_cost_pct"] or 0.0)
                for row in selective_recovery_rows
            )
            if selective_recovery_rows
            else None
        ),
        "candidate_selected_after_cost_ev_pct": (
            fmean(
                row["candidate_primary_decision_value_pct"]
                for row in selective_recovery_exposure_rows
            )
            if selective_recovery_exposure_rows
            else None
        ),
        "profit_opportunity_count": sum(
            row["profit_opportunity_observed"] for row in selective_recovery_rows
        ),
        "severe_tail_exposure_count": sum(
            row["candidate_probe_severe_tail_exposure"]
            for row in selective_recovery_exposure_rows
        ),
        "drawdown_recovery_exposure_count": sum(
            row["candidate_drawdown_recovery_captured"]
            for row in selective_recovery_exposure_rows
        ),
        "metric_role": "ai_decision_quality_opportunity_cohort_attribution",
        "decision_authority": "offline_replay_and_attribution_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    recovery_confirmation_rows = [
        row for row in comparable_rows if row["recovery_confirmation_probe_eligible"]
    ]
    recovery_confirmation_exposure_rows = [
        row for row in recovery_confirmation_rows if row["candidate_exposure_selected"]
    ]
    recovery_confirmation_probe_summary = {
        "schema": "recovery_confirmation_probe_attribution_v1",
        "eligible_decision_count": len(recovery_confirmation_rows),
        "eligible_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in recovery_confirmation_rows
                if row.get("stock_code")
            }
        ),
        "candidate_exposure_decision_count": len(recovery_confirmation_exposure_rows),
        "candidate_not_exposed_decision_count": (
            len(recovery_confirmation_rows) - len(recovery_confirmation_exposure_rows)
        ),
        "candidate_exposure_coverage_pct": (
            len(recovery_confirmation_exposure_rows)
            / len(recovery_confirmation_rows)
            * 100.0
            if recovery_confirmation_rows
            else None
        ),
        "eligible_cohort_after_cost_ev_pct": (
            fmean(
                row["outcome_return_pct"]
                - (row["conservative_execution_cost_pct"] or 0.0)
                for row in recovery_confirmation_rows
            )
            if recovery_confirmation_rows
            else None
        ),
        "candidate_selected_after_cost_ev_pct": (
            fmean(
                row["candidate_primary_decision_value_pct"]
                for row in recovery_confirmation_exposure_rows
            )
            if recovery_confirmation_exposure_rows
            else None
        ),
        "profit_opportunity_count": sum(
            row["profit_opportunity_observed"] for row in recovery_confirmation_rows
        ),
        "severe_tail_exposure_count": sum(
            row["candidate_probe_severe_tail_exposure"]
            for row in recovery_confirmation_exposure_rows
        ),
        "drawdown_recovery_exposure_count": sum(
            row["candidate_drawdown_recovery_captured"]
            for row in recovery_confirmation_exposure_rows
        ),
        "metric_role": "ai_decision_quality_opportunity_cohort_attribution",
        "decision_authority": "offline_replay_and_attribution_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    ready_opportunity_rows = [
        row for row in comparable_rows if row.get("entry_setup_state") == "READY"
    ]
    ready_opportunity_symbols = {
        str(row.get("stock_code") or "")
        for row in ready_opportunity_rows
        if row.get("stock_code")
    }
    recheck_opportunity_rows = [
        row for row in comparable_rows if row.get("entry_recheck_intent") is True
    ]
    recheck_opportunity_symbols = {
        str(row.get("stock_code") or "")
        for row in recheck_opportunity_rows
        if row.get("stock_code")
    }
    exposure_floor_feasibility_status = (
        "promotion_floor_pass"
        if candidate_exposure_sample_floor_pass
        else (
            "bounded_exploration_arm_floor_pass"
            if candidate_probe_arm_floor_pass
            else (
                "ready_exposure_drought_review_required"
                if len(ready_opportunity_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
                and len(ready_opportunity_symbols)
                >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
                else (
                    "sequential_recheck_sample_route_available"
                    if len(recheck_opportunity_rows)
                    >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
                    and len(recheck_opportunity_symbols)
                    >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
                    else "natural_sample_keep_collecting"
                )
            )
        )
    )
    quality_stages = {str(row.get("stage") or "unknown") for row in comparable_rows}
    quality_checks = {
        "all_pairs_comparable": bool(requests)
        and len(comparable_rows) == len(requests),
        "candidate_execution_selection_contract_pass": (
            execution_selection_contract_pass
        ),
        "source_quality_adjusted_ev_improved": (
            source_quality_ev_delta is not None and source_quality_ev_delta > 0
        ),
        "primary_decision_ev_improved": ev_delta is not None and ev_delta > 0,
        "candidate_ev_positive": (
            candidate_primary_ev is not None and candidate_primary_ev > 0
        ),
        "opportunity_capture_expanded": opportunity_capture[
            "opportunity_capture_expanded"
        ],
        "missed_upside_tradeoff_not_worse": opportunity_capture[
            "missed_upside_tradeoff_not_worse"
        ],
        "drawdown_recovery_capture_not_decreased": (
            candidate_recovery_capture_count >= control_recovery_capture_count
        ),
        "candidate_exposure_sample_floor_pass": (candidate_exposure_sample_floor_pass),
        "promotion_cohort_isolated": promotion_cohort_isolated,
        "promotion_candidate_contract_isolated": promotion_contract_isolated,
        "selected_cohort_quality_pass": selected_cohort_quality_pass,
    }
    if quality_stages == {"entry"}:
        quality_checks.update(
            {
                "candidate_probe_cost_adjusted_ev_positive": (
                    candidate_probe_cost_adjusted_ev is not None
                    and candidate_probe_cost_adjusted_ev > 0
                ),
                "candidate_probe_bounded_risk_budget_pass": (
                    candidate_probe_risk_budget["pass"]
                ),
            }
        )
    diagnostic_checks = {
        "adverse_first_exposure_not_increased": (
            candidate_adverse_first_exposure_count
            <= control_adverse_first_exposure_count
        ),
        "tight_stop_adverse_first_exposure_not_increased": (
            candidate_tight_stop_adverse_first_exposure_count
            <= control_tight_stop_adverse_first_exposure_count
        ),
        "severe_tail_adverse_not_increased": (
            candidate_probe_severe_tail_count <= control_probe_severe_tail_count
        ),
        "candidate_action_not_collapsed": (
            dominant_candidate_action_ratio is not None
            and dominant_candidate_action_ratio <= 0.90
        ),
    }
    quality_gate_pass = all(quality_checks.values())
    if candidate_contract_integrity_rejected_count:
        status = "candidate_contract_integrity_rejected_no_runtime_apply"
    elif rejected or (results and missing_result_count):
        status = "candidate_rejected_no_runtime_apply"
    elif not requests:
        status = "sample_floor_keep_collecting"
    elif not results:
        status = "paired_replay_requests_ready_candidate_not_executed"
    elif not promotion_cohort_isolated:
        status = "paired_replay_complete_cohort_split_required"
    elif not promotion_contract_isolated:
        status = "paired_replay_complete_candidate_contract_split_required"
    elif not candidate_exposure_sample_floor_pass:
        status = (
            "paired_replay_complete_exposure_drought_review_required"
            if exposure_floor_feasibility_status
            == "ready_exposure_drought_review_required"
            else "paired_replay_complete_hold_sample_offline_only"
        )
    elif quality_gate_pass:
        status = "paired_replay_complete_candidate_quality_pass_offline_only"
    else:
        status = "paired_replay_complete_candidate_quality_rejected"
    report_requests = [
        {
            key: value
            for key, value in request.items()
            if key not in {"exact_payload", "candidate_input"}
        }
        for request in requests
    ]
    provider_attempts = [
        attempt
        for result in results
        for attempt in result.get("candidate_attempts") or []
        if isinstance(attempt, dict)
    ]
    candidate_prompt_versions = {
        str((request.get("candidate") or {}).get("prompt_version") or "").removesuffix(
            f"_{request.get('stage')}"
        )
        for request in requests
        if isinstance(request.get("candidate"), dict)
    }
    cumulative_candidate_prompt_version = (
        next(iter(candidate_prompt_versions))
        if len(candidate_prompt_versions) == 1
        else DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION
    )
    if (
        cumulative_candidate_prompt_version
        == DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION
        and results
        and not rejected
        and not missing_result_count
        and not candidate_contract_integrity_rejected_count
        and promotion_cohort_isolated
        and promotion_contract_isolated
        and status
        in {
            "paired_replay_complete_exposure_drought_review_required",
            "paired_replay_complete_hold_sample_offline_only",
            "paired_replay_complete_candidate_quality_pass_offline_only",
            "paired_replay_complete_candidate_quality_rejected",
        }
    ):
        sequential_arm_count = int(
            sequential_recovery_summary.get("confirmed_arm_count") or 0
        )
        sequential_floor_pass = bool(
            (sequential_recovery_summary.get("sample_floor") or {}).get("pass") is True
        )
        if not sequential_arm_count:
            status = (
                "paired_replay_complete_sequential_confirmation_sample_keep_collecting"
            )
        elif not sequential_floor_pass:
            status = "paired_replay_complete_sequential_hold_sample_offline_only"
        elif sequential_recovery_summary.get("development_quality_gate_pass") is True:
            status = (
                "paired_replay_complete_sequential_quality_pass_prospective_required"
            )
        else:
            status = "paired_replay_complete_sequential_prompt_redesign_required"
    entry_recheck_rows = [
        row for row in comparable_rows if row.get("entry_recheck_intent") is True
    ]
    entry_recheck_stress_values = []
    for row in entry_recheck_rows:
        outcome = _number(row.get("outcome_return_pct"))
        cost = _number(row.get("conservative_execution_cost_pct"))
        if outcome is not None and cost is not None:
            entry_recheck_stress_values.append(outcome - cost)
    cumulative_venues = {
        _venue(row.get("effective_venue"))
        for row in comparable_rows
        if _venue(row.get("effective_venue"))
    }
    cumulative_sessions = {
        _session(row.get("session_bucket"))
        for row in comparable_rows
        if _session(row.get("session_bucket"))
    }
    cumulative_venue = (
        next(iter(cumulative_venues)) if len(cumulative_venues) == 1 else None
    )
    cumulative_session = (
        next(iter(cumulative_sessions)) if len(cumulative_sessions) == 1 else None
    )
    if (
        execution_cost_contract_applied
        and cumulative_venue
        and cumulative_session
        and cumulative_candidate_contract_sha256
    ):
        cumulative_learning = _anticipatory_cumulative_learning_summary(
            target_date=target_date,
            current_rows=comparable_rows,
            candidate_prompt_version=cumulative_candidate_prompt_version,
            candidate_contract_sha256=cumulative_candidate_contract_sha256,
            effective_venue=cumulative_venue,
            session_bucket=cumulative_session,
        )
    elif execution_cost_contract_applied:
        cumulative_learning = {
            "schema": "anticipatory_reversal_cumulative_learning_v2",
            "status": (
                "candidate_contract_isolation_required"
                if cumulative_venue and cumulative_session
                else "cohort_isolation_required"
            ),
            "candidate_prompt_version": cumulative_candidate_prompt_version,
            "candidate_contract_sha256": cumulative_candidate_contract_sha256,
            "cohort_scope": {
                "effective_venue": cumulative_venue,
                "session_bucket": cumulative_session,
                "isolated": False,
                "candidate_contract_sha256": (cumulative_candidate_contract_sha256),
                "cross_cohort_aggregation_forbidden": True,
            },
            "promotion_quality_gate_pass": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    else:
        cumulative_learning = None
    cumulative_promotion_quality_gate_pass = bool(
        isinstance(cumulative_learning, dict)
        and cumulative_learning.get("promotion_quality_gate_pass") is True
    )
    promotion_report_integrity_pass = bool(
        requests
        and results
        and execution_selection_contract_pass
        and candidate_contract_integrity_rejected_count == 0
        and rejected == 0
        and missing_result_count == 0
        and len(comparable_rows) == len(requests)
    )
    promotion_quality_gate_pass = bool(
        promotion_report_integrity_pass
        and (quality_gate_pass or cumulative_promotion_quality_gate_pass)
    )
    if (
        status
        in {
            "paired_replay_complete_exposure_drought_review_required",
            "paired_replay_complete_hold_sample_offline_only",
        }
        and promotion_report_integrity_pass
        and cumulative_promotion_quality_gate_pass
    ):
        status = "paired_replay_complete_cumulative_quality_pass_offline_only"

    def _single_candidate_contract_value(field: str) -> Any:
        values = {
            candidate.get(field)
            for request in requests
            if isinstance(request, dict)
            and isinstance((candidate := request.get("candidate")), dict)
            and candidate.get(field) not in (None, "")
        }
        return next(iter(values)) if len(values) == 1 else None

    return {
        "schema": PAIRED_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "candidate_contract_sha256": cumulative_candidate_contract_sha256,
        "entry_setup_evidence_version": _single_candidate_contract_value(
            "entry_setup_evidence_version"
        ),
        "entry_decision_composer_version": _single_candidate_contract_value(
            "entry_decision_composer_version"
        ),
        "entry_structure_phase_policy_version": _single_candidate_contract_value(
            "entry_structure_phase_policy_version"
        ),
        "request_count": len(requests),
        "result_count": len(results),
        "candidate_execution_performed": bool(results),
        "candidate_execution_selection": execution_selection,
        "schema_rejected_count": schema_rejected,
        "provider_failed_count": provider_failed,
        "missing_result_count": missing_result_count,
        "paired_comparable_count": len(comparable_rows),
        "candidate_contract_integrity_rejected_count": (
            candidate_contract_integrity_rejected_count
        ),
        "control_source_quality_adjusted_ev_pct": control_ev,
        "control_primary_decision_ev_pct": control_primary_ev,
        "candidate_source_quality_adjusted_ev_pct": candidate_ev,
        "candidate_execution_cost_adjusted_ev_pct": (
            candidate_execution_cost_adjusted_ev
        ),
        "candidate_primary_decision_ev_pct": candidate_primary_ev,
        "candidate_primary_decision_metric": (
            "probe_intent_and_execution_cost_adjusted_ev_pct"
            if execution_cost_contract_applied
            else "source_quality_adjusted_ev_pct"
        ),
        "control_entry_probe_intent_count": sum(
            row["control_entry_probe_intent"] for row in comparable_rows
        ),
        "candidate_execution_cost_observed_count": sum(
            row["candidate_execution_cost_pct"] is not None
            and row["candidate_exposure_selected"]
            for row in comparable_rows
        ),
        "control_execution_cost_observed_count": sum(
            row["control_execution_cost_pct"] is not None
            and row["control_exposure_selected"]
            for row in comparable_rows
        ),
        "candidate_execution_cost_total_pct": (
            sum(row["candidate_execution_cost_pct"] or 0.0 for row in comparable_rows)
            if execution_cost_contract_applied
            else None
        ),
        "source_quality_adjusted_ev_delta_pct": source_quality_ev_delta,
        "candidate_primary_decision_ev_delta_pct": ev_delta,
        "missed_upside_reduction_count": missed_upside_reduction_count,
        "new_missed_upside_count": new_missed_upside_count,
        "opportunity_capture_tradeoff": opportunity_capture,
        "control_adverse_first_exposure_count": (control_adverse_first_exposure_count),
        "adverse_first_candidate_exposure_count": (
            candidate_adverse_first_exposure_count
        ),
        "control_tight_stop_adverse_first_exposure_count": (
            control_tight_stop_adverse_first_exposure_count
        ),
        "candidate_tight_stop_adverse_first_exposure_count": (
            candidate_tight_stop_adverse_first_exposure_count
        ),
        "probe_risk_contract": {
            "version": PROBE_RISK_CONTRACT_VERSION,
            "probe_share_count": OFFLINE_PROBE_SHARE_COUNT,
            "maximum_bounded_loss_pct": OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT,
            "severe_tail_adverse_pct": OFFLINE_PROBE_SEVERE_TAIL_ADVERSE_PCT,
            "path_basis": (
                "counterfactual_completed_1m_trade_path_with_conservative_cost"
            ),
            "adverse_first_role": "diagnostic_not_absolute_quality_veto",
            "maximum_loss_budget_breach_rate_pct": (
                PAIRED_CANDIDATE_MAX_LOSS_BREACH_RATE_PCT
            ),
            "maximum_severe_tail_rate_pct": (PAIRED_CANDIDATE_MAX_SEVERE_TAIL_RATE_PCT),
            "catastrophic_loss_threshold_pct": (PAIRED_CANDIDATE_CATASTROPHIC_LOSS_PCT),
            "runtime_guard_requirement": (
                "one_share_probe_first_plus_existing_submit_post_probe_and_exit_guards"
            ),
            "decision_authority": "offline_replay_and_attribution_only",
            "runtime_effect": False,
            "actual_order_submitted": False,
        },
        "candidate_probe_cost_adjusted_ev_pct": candidate_probe_cost_adjusted_ev,
        "candidate_probe_risk_budget": candidate_probe_risk_budget,
        "candidate_probe_loss_budget_breach_count": sum(
            row["candidate_probe_worst_loss_pct"] is not None
            and row["candidate_probe_worst_loss_pct"]
            < -OFFLINE_PROBE_MAX_BOUNDED_LOSS_PCT
            for row in candidate_exposure_rows
        ),
        "candidate_probe_risk_missing_count": sum(
            row["candidate_probe_worst_loss_pct"] is None
            for row in candidate_exposure_rows
        ),
        "control_probe_severe_tail_exposure_count": control_probe_severe_tail_count,
        "candidate_probe_severe_tail_exposure_count": (
            candidate_probe_severe_tail_count
        ),
        "control_drawdown_recovery_capture_count": control_recovery_capture_count,
        "candidate_drawdown_recovery_capture_count": (candidate_recovery_capture_count),
        "spread_confounded_adverse_first_count": sum(
            row["entry_path_adverse_first_spread_confounded"] for row in comparable_rows
        ),
        "entry_path_label_contract": {
            "version": ENTRY_PATH_LABEL_VERSION,
            "primary_horizon": ENTRY_PATH_PRIMARY_HORIZON,
            "target_pct": ENTRY_PATH_TARGET_PCT,
            "adverse_pct": ENTRY_PATH_ADVERSE_PCT,
            "labels": [
                "target_first",
                "adverse_first",
                "same_bar_ambiguous",
                "neither_hit",
            ],
            "decision_authority": "offline_replay_and_attribution_only",
        },
        "candidate_exposure_decision_count": len(candidate_exposure_rows),
        "candidate_exposure_unique_symbol_count": candidate_exposure_symbol_count,
        "candidate_exposure_sample_floor": {
            "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            "pass": candidate_exposure_sample_floor_pass,
            "policy": (
                "fixed_promotion_floor_not_auto_lowered; one_sample_starts_learning"
            ),
        },
        "candidate_probe_arm_decision_count": len(candidate_probe_arm_rows),
        "candidate_probe_arm_unique_symbol_count": candidate_probe_arm_symbol_count,
        "candidate_probe_arm_sample_floor": {
            "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            "pass": candidate_probe_arm_floor_pass,
            "authority": "bounded_one_share_exploration_candidate_only",
            "performance_promotion_authority": False,
            "interpretation": (
                "A WAIT probe intent arms the downstream recheck owner but is not "
                "counted as an order or immediate performance exposure."
            ),
        },
        "candidate_probe_arm_risk_budget": {
            **candidate_probe_arm_risk_budget,
            "metric_role": "counterfactual_exploration_risk_diagnostic",
            "decision_authority": "diagnostic_only_not_performance_promotion_veto",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "candidate_exposure_floor_feasibility": {
            "status": exposure_floor_feasibility_status,
            "ready_decision_count": len(ready_opportunity_rows),
            "ready_unique_symbol_count": len(ready_opportunity_symbols),
            "recheck_decision_count": len(recheck_opportunity_rows),
            "recheck_unique_symbol_count": len(recheck_opportunity_symbols),
            "next_action": (
                (
                    "allow_krx_one_share_exploration_with_residual_and_scale_in_forbidden"
                    if selected_cohort_venue == "KRX"
                    else "keep_nxt_control_and_collect_separate_cohort_evidence"
                )
                if exposure_floor_feasibility_status
                == "bounded_exploration_arm_floor_pass"
                else (
                    "review_ready_to_exposure_composer_drought"
                    if exposure_floor_feasibility_status
                    == "ready_exposure_drought_review_required"
                    else (
                        "attribute_next_exact_recheck_transition_before_relaxation"
                        if exposure_floor_feasibility_status
                        == "sequential_recheck_sample_route_available"
                        else "collect_natural_same_cohort_exact_samples"
                    )
                )
            ),
        },
        "promotion_cohort_scope": {
            "stages": sorted({str(key[0]) for key in cohort_keys}),
            "effective_venues": sorted({str(key[1]) for key in cohort_keys}),
            "session_buckets": sorted({str(key[2]) for key in cohort_keys}),
            "isolated": promotion_cohort_isolated,
            "candidate_contract_sha256": cumulative_candidate_contract_sha256,
            "candidate_contract_isolated": promotion_contract_isolated,
            "cross_cohort_promotion_forbidden": True,
        },
        "candidate_error_taxonomy_counts": dict(
            Counter(
                error
                for row in comparable_rows
                for error in row["candidate_error_taxonomy"]
            )
        ),
        "candidate_dominant_action_ratio": dominant_candidate_action_ratio,
        "candidate_quality_gate_pass": quality_gate_pass,
        "promotion_report_integrity_pass": promotion_report_integrity_pass,
        "promotion_quality_gate_pass": promotion_quality_gate_pass,
        "promotion_quality_gate_basis": (
            "current_same_cohort_report"
            if promotion_report_integrity_pass and quality_gate_pass
            else (
                "cumulative_same_contract_venue_session"
                if promotion_report_integrity_pass
                and cumulative_promotion_quality_gate_pass
                else "not_passed"
            )
        ),
        "candidate_quality_checks": quality_checks,
        "diagnostic_checks_not_quality_veto": diagnostic_checks,
        "control_action_counts": dict(
            Counter(
                str((row.get("control_response") or {}).get("action") or "UNKNOWN")
                for row in valid_results
            )
        ),
        "candidate_action_counts": dict(candidate_action_counter),
        "candidate_drop_outcome_trajectory": candidate_drop_trajectory,
        "clean_continuation_probe_summary": clean_continuation_probe_summary,
        "selective_recovery_probe_summary": selective_recovery_probe_summary,
        "recovery_confirmation_probe_summary": (recovery_confirmation_probe_summary),
        "entry_sequential_recovery": sequential_recovery_summary,
        "entry_opportunity_funnel": entry_opportunity_funnel,
        "entry_lifecycle_replay": entry_lifecycle_replay,
        "entry_setup_adjudicator_summary": {
            "schema": "entry_setup_adjudicator_attribution_v1",
            "metric_role": "ai_entry_setup_adjudicator_attribution",
            "decision_authority": "offline_replay_and_attribution_only",
            "window_policy": "same_exact_payload_stage_venue_session_mature_window",
            "sample_floor": {
                "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
                "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            },
            "primary_decision_metric": "candidate_probe_cost_adjusted_ev_pct",
            "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
            "forbidden_uses": [
                "standalone_live_prompt_promotion",
                "real_order_or_fill_claim",
                "provider_model_threshold_price_quantity_or_cap_change",
                "broker_or_safety_guard_bypass",
                "bot_restart",
            ],
            "setup_family_counts": dict(
                Counter(
                    str(row.get("entry_setup_family") or "NOT_APPLICABLE")
                    for row in comparable_rows
                )
            ),
            "setup_state_counts": dict(
                Counter(
                    str(row.get("entry_setup_state") or "NOT_APPLICABLE")
                    for row in comparable_rows
                )
            ),
            "risk_verdict_counts": dict(
                Counter(
                    str(row.get("entry_ai_risk_verdict") or "NOT_APPLICABLE")
                    for row in comparable_rows
                )
            ),
            "corroborated_veto_count": sum(
                row.get("entry_ai_veto_corroborated") is True for row in comparable_rows
            ),
            "bounded_risk_observation_count": sum(
                bool(row.get("entry_ai_bounded_risk_codes")) for row in comparable_rows
            ),
            "bounded_risk_code_counts": dict(
                Counter(
                    code
                    for row in comparable_rows
                    for code in row.get("entry_ai_bounded_risk_codes") or []
                )
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "entry_recheck_attribution": {
            "schema": "entry_recheck_attribution_v2",
            "metric_role": "ai_entry_recheck_counterfactual_attribution",
            "decision_authority": "offline_replay_and_attribution_only",
            "window_policy": "same_exact_payload_stage_venue_session_mature_window",
            "sample_floor": {
                "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
                "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            },
            "primary_decision_metric": (
                "recheck_immediate_exposure_stress_source_quality_adjusted_ev_pct"
            ),
            "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
            "forbidden_uses": [
                "treat_recheck_as_immediate_entry",
                "standalone_live_prompt_promotion",
                "real_order_or_fill_claim",
                "provider_model_threshold_price_quantity_or_cap_change",
                "broker_or_safety_guard_bypass",
                "bot_restart",
            ],
            "candidate_recheck_intent_count": len(entry_recheck_rows),
            "candidate_recheck_unique_symbol_count": len(
                {
                    str(row.get("stock_code") or "")
                    for row in entry_recheck_rows
                    if row.get("stock_code")
                }
            ),
            "candidate_recheck_reason_counts": dict(
                Counter(
                    reason
                    for row in entry_recheck_rows
                    for reason in row.get("entry_recheck_reasons") or []
                )
            ),
            "candidate_recheck_reason_breakdown": (
                _entry_recheck_reason_breakdown(entry_recheck_rows)
            ),
            "next_exact_transition_summary": entry_recheck_transition_summary,
            "recheck_immediate_exposure_stress_source_quality_adjusted_ev_pct": (
                fmean(entry_recheck_stress_values)
                if entry_recheck_stress_values
                else None
            ),
            "target_first_count": sum(
                str(row.get("entry_path_first_hit") or "") == "target_first"
                for row in entry_recheck_rows
            ),
            "adverse_first_count": sum(
                str(row.get("entry_path_first_hit") or "") == "adverse_first"
                for row in entry_recheck_rows
            ),
            "severe_tail_stress_count": sum(
                row.get("probe_severe_tail_adverse") is True
                for row in entry_recheck_rows
            ),
            "tail_risk_probe_prevented_count": sum(
                "TAIL_LIQUIDITY_RECHECK" in (row.get("entry_recheck_reasons") or [])
                and row.get("candidate_exposure_selected") is not True
                for row in entry_recheck_rows
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "entry_probe_arm_continuity": {
            "schema": "entry_probe_arm_continuity_v1",
            "metric_role": "funnel_count",
            "decision_authority": "offline_sequential_continuity_attribution_only",
            "window_policy": (
                "same_symbol_venue_session_full_prepared_exact_request_census_300s"
            ),
            "sample_floor": "one_waiting_probe_arm_starts_observation",
            "primary_decision_metric": "ready_followup_observed_rate_pct",
            "source_quality_gate": "exact_v2_same_route_prepared_request_census",
            **entry_probe_arm_transition_summary,
            "forbidden_uses": [
                "treat_waiting_probe_arm_as_submitted_order",
                "treat_candidate_budget_defer_as_ai_rejection",
                "standalone_live_prompt_promotion",
                "provider_model_threshold_price_quantity_or_cap_change",
                "broker_or_safety_guard_bypass",
                "bot_restart",
            ],
        },
        "candidate_edge_state_counts": dict(
            Counter(
                str(
                    (row.get("candidate_response") or {}).get("edge_state") or "UNKNOWN"
                )
                for row in valid_results
            )
        ),
        "candidate_provider_attempt_count": len(provider_attempts),
        "candidate_provider_none_count": sum(
            (attempt.get("provider_provenance") or {}).get("provider_none") is True
            for attempt in provider_attempts
        ),
        "cumulative_learning": cumulative_learning,
        "net_profit_status": "not_available_without_notional_and_fill_join",
        "buckets": buckets,
        "paired_comparisons": comparable_rows,
        "requests": report_requests,
        "results": results,
        **OFFLINE_CONTRACT,
    }


def _attach_paired_preparation_metadata(
    report: dict[str, Any],
    *,
    prepared_requests: list[dict[str, Any]],
    accepted_requests: list[dict[str, Any]],
    outcome_price_source: str,
    outcome_price_source_requested: str,
    price_source_provenance: list[dict[str, Any]],
    outcome_as_of: str | None = None,
) -> dict[str, Any]:
    """Attach the shared request-floor and outcome-source preparation contract."""

    floor_groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for request in prepared_requests:
        key = (
            str(request.get("stage") or "unknown"),
            str(request.get("effective_venue") or "UNKNOWN"),
            str(request.get("session_bucket") or "UNKNOWN"),
        )
        floor_groups[key] = dict(request.get("sample_floor") or {})
    report["prepared_request_count"] = len(prepared_requests)
    report["sample_floor_excluded_request_count"] = len(prepared_requests) - len(
        accepted_requests
    )
    report["sample_floor_buckets"] = [
        {
            "stage": key[0],
            "effective_venue": key[1],
            "session_bucket": key[2],
            **value,
        }
        for key, value in sorted(floor_groups.items())
    ]
    report["outcome_price_source"] = outcome_price_source
    report["outcome_price_source_requested"] = outcome_price_source_requested
    report["price_source_provenance"] = price_source_provenance
    report["outcome_as_of"] = outcome_as_of
    return report


def build_daily_materialization_reports(
    *,
    target_date: str,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    label_report: dict[str, Any],
    outcome_price_source: str,
    outcome_price_source_requested: str,
    price_source_provenance: list[dict[str, Any]],
    promotion_artifact_path: Path | None = None,
    promotion_source_date: str | None = None,
) -> dict[str, Any]:
    """Build the daily Exact V2 quality chain without candidate API execution."""

    control_prompt_versions = _latest_exact_control_prompt_versions(
        promotion=promotion,
        traces=traces,
        payloads=payloads,
    )
    control_signatures = _latest_exact_control_signatures(
        promotion=promotion,
        traces=traces,
        payloads=payloads,
    )
    control = build_control_manifest(
        target_date=target_date,
        promotion=promotion,
        traces=traces,
        payloads=payloads,
        control_prompt_versions=control_prompt_versions,
        control_signatures=control_signatures,
        promotion_artifact_path=promotion_artifact_path,
        promotion_source_date=promotion_source_date,
    )
    baseline = build_quality_baseline(target_date=target_date, labels=labels)
    baseline["outcome_price_source"] = outcome_price_source
    baseline["outcome_price_source_requested"] = outcome_price_source_requested
    baseline["price_source_provenance"] = price_source_provenance

    prepared_requests = prepare_paired_replay_requests(
        control_manifest=control,
        traces=traces,
        payloads=payloads,
        labels=labels,
    )
    accepted_requests = [
        request
        for request in prepared_requests
        if (request.get("sample_floor") or {}).get("pass") is True
    ]
    paired = build_paired_replay_report(
        target_date=target_date,
        requests=accepted_requests,
        results=[],
        labels=labels,
        prepared_requests=prepared_requests,
    )
    _attach_paired_preparation_metadata(
        paired,
        prepared_requests=prepared_requests,
        accepted_requests=accepted_requests,
        outcome_price_source=outcome_price_source,
        outcome_price_source_requested=outcome_price_source_requested,
        price_source_provenance=price_source_provenance,
        outcome_as_of=(str(label_report.get("outcome_as_of") or "") or None),
    )
    paired["candidate_execution_performed"] = False
    paired["candidate_execution_authority"] = "explicit_offline_execute_candidate_only"
    paired["decision_quality_objective"] = dict(DECISION_QUALITY_OBJECTIVE)
    candidate_lifecycle_state = materialize_candidate_states(
        target_date,
        write=False,
    )

    reports = {
        "control": control,
        "mature": label_report,
        "baseline": baseline,
        "paired": paired,
        "candidate_lifecycle_state": candidate_lifecycle_state,
    }
    validation_errors = validate_daily_materialization_reports(
        target_date=target_date,
        reports=reports,
    )
    if validation_errors:
        raise RuntimeError(
            "daily_exact_quality_chain_contract_invalid:" + ",".join(validation_errors)
        )
    return {
        "schema": DAILY_MATERIALIZATION_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": "daily_exact_quality_chain_prepared",
        "write_order": [
            "control",
            "mature",
            "baseline",
            "paired",
            "candidate_lifecycle_state",
        ],
        "candidate_execution_performed": False,
        "decision_quality_objective": dict(DECISION_QUALITY_OBJECTIVE),
        "reports": reports,
        "contract_validation": "pass",
        "summary": {
            "control_status": control.get("status"),
            "label_status": label_report.get("status"),
            "label_counts": label_report.get("summary"),
            "baseline_status": baseline.get("status"),
            "baseline_eligible_sample_count": baseline.get("eligible_sample_count"),
            "paired_status": paired.get("status"),
            "paired_prepared_request_count": paired.get("prepared_request_count"),
            "paired_accepted_request_count": paired.get("request_count"),
            "candidate_lifecycle_state_count": candidate_lifecycle_state.get(
                "candidate_state_count"
            ),
            "candidate_lifecycle_source_quality_pass_count": (
                candidate_lifecycle_state.get("source_quality_pass_count")
            ),
        },
        **OFFLINE_CONTRACT,
    }


def validate_daily_materialization_reports(
    *,
    target_date: str,
    reports: dict[str, dict[str, Any]],
) -> list[str]:
    """Validate daily artifact identity and report-only authority isolation."""

    expected_schemas = {
        "control": CONTROL_SCHEMA,
        "mature": LABEL_REPORT_SCHEMA,
        "baseline": BASELINE_SCHEMA,
        "paired": PAIRED_SCHEMA,
        "candidate_lifecycle_state": "entry_candidate_lifecycle_state_report_v1",
    }
    errors: list[str] = []
    for name, expected_schema in expected_schemas.items():
        report = reports.get(name)
        if not isinstance(report, dict):
            errors.append(f"{name}_missing")
            continue
        if report.get("schema") != expected_schema:
            errors.append(f"{name}_schema_invalid")
        if report.get("target_date") != target_date:
            errors.append(f"{name}_target_date_mismatch")
        for field, expected in (
            ("runtime_effect", False),
            ("allowed_runtime_apply", False),
            ("actual_order_submitted", False),
            ("broker_order_forbidden", True),
        ):
            if report.get(field) is not expected:
                errors.append(f"{name}_{field}_invalid")
    paired = reports.get("paired") or {}
    if paired.get("candidate_execution_performed") is not False:
        errors.append("paired_candidate_execution_performed")
    if paired.get("results"):
        errors.append("paired_candidate_results_not_empty")
    return errors


def build_detailed_three_way_comparison(
    *,
    one_pass_report: dict[str, Any],
    detailed_report: dict[str, Any],
) -> dict[str, Any]:
    """Compare control, one-pass V2, and detailed two-pass on common rows."""

    one_pass_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in one_pass_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    detailed_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in detailed_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    trace_ids = sorted(set(one_pass_by_trace) & set(detailed_by_trace))
    rows: list[dict[str, Any]] = []
    for trace_id in trace_ids:
        one_pass = one_pass_by_trace[trace_id]
        detailed = detailed_by_trace[trace_id]
        outcome = _number(detailed.get("outcome_return_pct"))
        control_value = _number(detailed.get("control_decision_value_pct"))
        one_pass_value = _number(one_pass.get("candidate_decision_value_pct"))
        detailed_value = _number(detailed.get("candidate_decision_value_pct"))
        if None in {outcome, control_value, one_pass_value, detailed_value}:
            continue
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": detailed.get("stock_code"),
                "effective_venue": detailed.get("effective_venue"),
                "session_bucket": detailed.get("session_bucket"),
                "outcome_return_pct": outcome,
                "control_action": detailed.get("control_action"),
                "one_pass_action": one_pass.get("candidate_action"),
                "detailed_action": detailed.get("candidate_action"),
                "control_decision_value_pct": control_value,
                "one_pass_decision_value_pct": one_pass_value,
                "detailed_decision_value_pct": detailed_value,
                "detailed_vs_one_pass_delta_pct": detailed_value - one_pass_value,
                "one_pass_error_taxonomy": list(
                    one_pass.get("candidate_error_taxonomy") or []
                ),
                "detailed_error_taxonomy": list(
                    detailed.get("candidate_error_taxonomy") or []
                ),
            }
        )
    comparable_trace_ids = [row["decision_trace_id"] for row in rows]

    def mean_field(field: str) -> float | None:
        return fmean(row[field] for row in rows) if rows else None

    transition_counts = Counter(
        f"{row['one_pass_action']}->{row['detailed_action']}" for row in rows
    )
    one_pass_errors = Counter(
        error for row in rows for error in row["one_pass_error_taxonomy"]
    )
    detailed_errors = Counter(
        error for row in rows for error in row["detailed_error_taxonomy"]
    )
    return {
        "schema": "ai_prompt_three_way_comparison_v1",
        "one_pass_prompt_version": (
            ((one_pass_report.get("requests") or [{}])[0].get("candidate") or {}).get(
                "prompt_version"
            )
            if one_pass_report.get("requests")
            else None
        ),
        "detailed_prompt_version": (
            ((detailed_report.get("requests") or [{}])[0].get("candidate") or {}).get(
                "prompt_version"
            )
            if detailed_report.get("requests")
            else None
        ),
        "common_comparable_count": len(rows),
        "common_cohort_sha256": _sha256(comparable_trace_ids),
        "control_source_quality_adjusted_ev_pct": mean_field(
            "control_decision_value_pct"
        ),
        "one_pass_source_quality_adjusted_ev_pct": mean_field(
            "one_pass_decision_value_pct"
        ),
        "detailed_source_quality_adjusted_ev_pct": mean_field(
            "detailed_decision_value_pct"
        ),
        "detailed_vs_one_pass_ev_delta_pct": mean_field(
            "detailed_vs_one_pass_delta_pct"
        ),
        "action_transition_counts": dict(transition_counts),
        "one_pass_error_taxonomy_counts": dict(one_pass_errors),
        "detailed_error_taxonomy_counts": dict(detailed_errors),
        "rows": rows,
        **OFFLINE_CONTRACT,
    }


def _model_replay_attempt_stats(report: dict[str, Any]) -> dict[str, Any]:
    attempts = [
        attempt
        for result in report.get("results") or []
        if isinstance(result, dict)
        for attempt in result.get("candidate_attempts") or []
        if isinstance(attempt, dict)
    ]
    provenance_rows = [
        row
        for attempt in attempts
        if isinstance((row := attempt.get("provider_provenance")), dict)
    ]
    openai_provenance_rows = [
        row
        for row in provenance_rows
        if str(row.get("provider") or "").lower() == "openai" and row.get("model")
    ]
    latencies = sorted(
        value
        for row in provenance_rows
        if (value := _number(row.get("latency_ms"))) is not None
    )

    def percentile(fraction: float) -> float | None:
        if not latencies:
            return None
        index = max(
            0, min(len(latencies) - 1, math.ceil(len(latencies) * fraction) - 1)
        )
        return latencies[index]

    return {
        "provider_attempt_count": len(attempts),
        "openai_api_attempt_count": len(openai_provenance_rows),
        "deterministic_adapter_attempt_count": sum(
            str(row.get("provider") or "") == "deterministic_offline_adapter"
            for row in provenance_rows
        ),
        "provider_models": sorted(
            {str(row.get("model") or "") for row in provenance_rows if row.get("model")}
        ),
        "provider_reasoning_efforts": sorted(
            {
                str(row.get("reasoning_effort") or "")
                for row in provenance_rows
                if row.get("reasoning_effort")
            }
        ),
        "configured_reasoning_efforts": sorted(
            {
                str((request.get("candidate") or {}).get("reasoning_effort") or "")
                for request in report.get("requests") or []
                if isinstance(request, dict)
                and (request.get("candidate") or {}).get("reasoning_effort")
            }
        ),
        "provider_none_count": sum(
            row.get("provider_none") is True for row in provenance_rows
        ),
        "latency_ms_mean": fmean(latencies) if latencies else None,
        "latency_ms_p50": percentile(0.50),
        "latency_ms_p95": percentile(0.95),
        "input_tokens_total": sum(
            int(value)
            for row in provenance_rows
            if (value := _number(row.get("input_tokens"))) is not None
        ),
        "output_tokens_total": sum(
            int(value)
            for row in provenance_rows
            if (value := _number(row.get("output_tokens"))) is not None
        ),
        "total_tokens": sum(
            int(value)
            for row in provenance_rows
            if (value := _number(row.get("total_tokens"))) is not None
        ),
    }


def build_model_replay_comparison(
    *,
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
    baseline_model: str,
    candidate_model: str,
) -> dict[str, Any]:
    """Compare two model runs over the same exact-payload replay cohort."""

    baseline_results = {
        str(row.get("decision_trace_id") or ""): row
        for row in baseline_report.get("results") or []
        if isinstance(row, dict) and row.get("status") == "pass"
    }
    candidate_results = {
        str(row.get("decision_trace_id") or ""): row
        for row in candidate_report.get("results") or []
        if isinstance(row, dict) and row.get("status") == "pass"
    }
    common_trace_ids = sorted(set(baseline_results) & set(candidate_results))
    baseline_all_results = {
        str(row.get("decision_trace_id") or ""): row
        for row in baseline_report.get("results") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    candidate_all_results = {
        str(row.get("decision_trace_id") or ""): row
        for row in candidate_report.get("results") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    baseline_pairs = {
        str(row.get("decision_trace_id") or ""): row
        for row in baseline_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    candidate_pairs = {
        str(row.get("decision_trace_id") or ""): row
        for row in candidate_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    common_comparable_trace_ids = [
        trace_id
        for trace_id in common_trace_ids
        if trace_id in baseline_pairs and trace_id in candidate_pairs
    ]
    transition_counts: Counter[str] = Counter()
    exact_response_match_count = 0
    payload_hash_mismatch_count = 0
    prompt_hash_mismatch_count = 0
    candidate_input_hash_mismatch_count = 0
    for trace_id in common_trace_ids:
        baseline = baseline_results[trace_id]
        candidate = candidate_results[trace_id]
        baseline_response = baseline.get("candidate_response") or {}
        candidate_response = candidate.get("candidate_response") or {}
        baseline_action = str(baseline_response.get("action") or "UNKNOWN")
        candidate_action = str(candidate_response.get("action") or "UNKNOWN")
        transition_counts[f"{baseline_action}->{candidate_action}"] += 1
        exact_response_match_count += _sha256(baseline_response) == _sha256(
            candidate_response
        )
        payload_hash_mismatch_count += baseline.get("payload_sha256") != candidate.get(
            "payload_sha256"
        )
        prompt_hash_mismatch_count += baseline.get(
            "candidate_prompt_sha256"
        ) != candidate.get("candidate_prompt_sha256")
        candidate_input_hash_mismatch_count += baseline.get(
            "candidate_input_sha256"
        ) != candidate.get("candidate_input_sha256")

    def common_mean(
        rows: dict[str, dict[str, Any]],
        key: str,
    ) -> float | None:
        values = [
            value
            for trace_id in common_comparable_trace_ids
            if (value := _number(rows[trace_id].get(key))) is not None
        ]
        return fmean(values) if values else None

    baseline_common_raw_ev = common_mean(
        baseline_pairs,
        "candidate_decision_value_pct",
    )
    candidate_common_raw_ev = common_mean(
        candidate_pairs,
        "candidate_decision_value_pct",
    )
    baseline_common_primary_ev = common_mean(
        baseline_pairs,
        "candidate_primary_decision_value_pct",
    )
    candidate_common_primary_ev = common_mean(
        candidate_pairs,
        "candidate_primary_decision_value_pct",
    )
    full_eligible_trace_ids = sorted(set(baseline_pairs) & set(candidate_all_results))

    def full_eligible_means(
        key: str,
    ) -> tuple[float | None, float | None, int]:
        baseline_values: list[float] = []
        candidate_values: list[float] = []
        missing_metric_count = 0
        for trace_id in full_eligible_trace_ids:
            baseline_value = _number(baseline_pairs[trace_id].get(key))
            candidate_result = candidate_all_results[trace_id]
            candidate_pair = candidate_pairs.get(trace_id)
            if baseline_value is None:
                missing_metric_count += 1
                continue
            if candidate_result.get("status") == "pass":
                candidate_value = (
                    _number(candidate_pair.get(key))
                    if isinstance(candidate_pair, dict)
                    else None
                )
                if candidate_value is None:
                    missing_metric_count += 1
                    continue
            else:
                # Provider/schema failures close without exposure in this offline
                # comparison. Retain them in the eligible denominator rather than
                # comparing only the candidate model's successful subset.
                candidate_value = 0.0
            baseline_values.append(baseline_value)
            candidate_values.append(candidate_value)
        return (
            fmean(baseline_values) if baseline_values else None,
            fmean(candidate_values) if candidate_values else None,
            missing_metric_count,
        )

    (
        baseline_full_eligible_raw_ev,
        candidate_fail_closed_full_eligible_raw_ev,
        full_eligible_raw_metric_missing_count,
    ) = full_eligible_means("candidate_decision_value_pct")
    (
        baseline_full_eligible_primary_ev,
        candidate_fail_closed_full_eligible_primary_ev,
        full_eligible_primary_metric_missing_count,
    ) = full_eligible_means("candidate_primary_decision_value_pct")

    def delta(
        candidate_value: float | None, baseline_value: float | None
    ) -> float | None:
        if candidate_value is None or baseline_value is None:
            return None
        return candidate_value - baseline_value

    baseline_common_errors = Counter(
        error
        for trace_id in common_comparable_trace_ids
        for error in baseline_pairs[trace_id].get("candidate_error_taxonomy") or []
    )
    candidate_common_errors = Counter(
        error
        for trace_id in common_comparable_trace_ids
        for error in candidate_pairs[trace_id].get("candidate_error_taxonomy") or []
    )

    return {
        "schema": "ai_prompt_model_replay_comparison_v1",
        "baseline_model": baseline_model,
        "candidate_model": candidate_model,
        "baseline_report_status": baseline_report.get("status"),
        "candidate_report_status": candidate_report.get("status"),
        "baseline_result_count": baseline_report.get("result_count"),
        "candidate_result_count": candidate_report.get("result_count"),
        "common_pass_count": len(common_trace_ids),
        "common_comparable_count": len(common_comparable_trace_ids),
        "candidate_nonpass_count": (
            int(candidate_report.get("result_count") or 0) - len(common_trace_ids)
        ),
        "baseline_pass_rate_pct": (
            len(baseline_results) / len(baseline_all_results) * 100.0
            if baseline_all_results
            else None
        ),
        "candidate_pass_rate_pct": (
            len(candidate_results) / len(candidate_all_results) * 100.0
            if candidate_all_results
            else None
        ),
        "common_cohort_sha256": _sha256(common_trace_ids),
        "common_comparable_cohort_sha256": _sha256(common_comparable_trace_ids),
        "full_eligible_cohort_count": len(full_eligible_trace_ids),
        "full_eligible_cohort_sha256": _sha256(full_eligible_trace_ids),
        "candidate_fail_closed_nonpass_value_policy": "zero_no_exposure",
        "full_eligible_raw_metric_missing_count": (
            full_eligible_raw_metric_missing_count
        ),
        "full_eligible_primary_metric_missing_count": (
            full_eligible_primary_metric_missing_count
        ),
        "payload_hash_mismatch_count": payload_hash_mismatch_count,
        "prompt_hash_mismatch_count": prompt_hash_mismatch_count,
        "candidate_input_hash_mismatch_count": candidate_input_hash_mismatch_count,
        "action_agreement_count": sum(
            count
            for transition, count in transition_counts.items()
            if len(set(transition.split("->"))) == 1
        ),
        "action_agreement_rate_pct": (
            sum(
                count
                for transition, count in transition_counts.items()
                if len(set(transition.split("->"))) == 1
            )
            / len(common_trace_ids)
            * 100.0
            if common_trace_ids
            else None
        ),
        "exact_response_match_count": exact_response_match_count,
        "action_transition_counts": dict(transition_counts),
        "baseline_common_action_counts": dict(
            Counter(
                str(
                    (baseline_results[trace_id].get("candidate_response") or {}).get(
                        "action"
                    )
                    or "UNKNOWN"
                )
                for trace_id in common_trace_ids
            )
        ),
        "candidate_common_action_counts": dict(
            Counter(
                str(
                    (candidate_results[trace_id].get("candidate_response") or {}).get(
                        "action"
                    )
                    or "UNKNOWN"
                )
                for trace_id in common_trace_ids
            )
        ),
        "baseline_full_action_counts": baseline_report.get("candidate_action_counts")
        or {},
        "candidate_full_pass_action_counts": candidate_report.get(
            "candidate_action_counts"
        )
        or {},
        "baseline_common_candidate_source_quality_adjusted_ev_pct": (
            baseline_common_raw_ev
        ),
        "candidate_common_source_quality_adjusted_ev_pct": candidate_common_raw_ev,
        "candidate_vs_baseline_common_source_quality_adjusted_ev_delta_pct": delta(
            candidate_common_raw_ev,
            baseline_common_raw_ev,
        ),
        "baseline_common_candidate_primary_decision_ev_pct": (
            baseline_common_primary_ev
        ),
        "candidate_common_primary_decision_ev_pct": candidate_common_primary_ev,
        "candidate_vs_baseline_common_primary_decision_ev_delta_pct": delta(
            candidate_common_primary_ev,
            baseline_common_primary_ev,
        ),
        "baseline_full_candidate_source_quality_adjusted_ev_pct": baseline_report.get(
            "candidate_source_quality_adjusted_ev_pct"
        ),
        "candidate_full_pass_source_quality_adjusted_ev_pct": candidate_report.get(
            "candidate_source_quality_adjusted_ev_pct"
        ),
        "baseline_full_candidate_primary_decision_ev_pct": baseline_report.get(
            "candidate_primary_decision_ev_pct"
        ),
        "candidate_full_pass_primary_decision_ev_pct": candidate_report.get(
            "candidate_primary_decision_ev_pct"
        ),
        "baseline_full_eligible_source_quality_adjusted_ev_pct": (
            baseline_full_eligible_raw_ev
        ),
        "candidate_fail_closed_full_eligible_source_quality_adjusted_ev_pct": (
            candidate_fail_closed_full_eligible_raw_ev
        ),
        "candidate_vs_baseline_fail_closed_full_eligible_source_quality_adjusted_ev_delta_pct": delta(
            candidate_fail_closed_full_eligible_raw_ev,
            baseline_full_eligible_raw_ev,
        ),
        "baseline_full_eligible_primary_decision_ev_pct": (
            baseline_full_eligible_primary_ev
        ),
        "candidate_fail_closed_full_eligible_primary_decision_ev_pct": (
            candidate_fail_closed_full_eligible_primary_ev
        ),
        "candidate_vs_baseline_fail_closed_full_eligible_primary_decision_ev_delta_pct": delta(
            candidate_fail_closed_full_eligible_primary_ev,
            baseline_full_eligible_primary_ev,
        ),
        "baseline_common_error_taxonomy_counts": dict(baseline_common_errors),
        "candidate_common_error_taxonomy_counts": dict(candidate_common_errors),
        "baseline_full_error_taxonomy_counts": baseline_report.get(
            "candidate_error_taxonomy_counts"
        )
        or {},
        "candidate_full_pass_error_taxonomy_counts": candidate_report.get(
            "candidate_error_taxonomy_counts"
        )
        or {},
        "baseline_quality_gate_pass": baseline_report.get(
            "candidate_quality_gate_pass"
        ),
        "candidate_quality_gate_pass": candidate_report.get(
            "candidate_quality_gate_pass"
        ),
        "baseline_attempt_stats": _model_replay_attempt_stats(baseline_report),
        "candidate_attempt_stats": _model_replay_attempt_stats(candidate_report),
        "decision_authority": "offline_model_comparison_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _snapshot_recovery_levels(
    exact_payload: dict[str, Any],
) -> dict[str, float | None]:
    current = exact_payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = exact_payload.get("features")
    features = features if isinstance(features, dict) else {}
    context = exact_payload.get("entry_candle_context")
    context = context if isinstance(context, dict) else {}
    reference_price = _number(current.get("price"))

    def level_from_bp(value: Any) -> float | None:
        basis_points = _number(value)
        if reference_price is None or reference_price <= 0 or basis_points is None:
            return None
        denominator = 1.0 + (basis_points / 10000.0)
        return reference_price / denominator if denominator > 0 else None

    completed_bars = [
        row
        for row in context.get("bars") or []
        if isinstance(row, dict) and not bool(row.get("forming", False))
    ]
    last_completed_close = (
        _number(completed_bars[-1].get("c")) if completed_bars else None
    )
    recent_lows = [
        value
        for value in (_number(row.get("l")) for row in completed_bars[-3:])
        if value is not None and value > 0
    ]
    micro_vwap = level_from_bp(features.get("curr_vs_micro_vwap_bp"))
    ma5 = level_from_bp(features.get("curr_vs_ma5_bp"))
    reclaim_candidates = [
        value
        for value in (micro_vwap, ma5, last_completed_close)
        if value is not None and value > 0
    ]
    return {
        "reference_price": reference_price,
        "micro_vwap_level": micro_vwap,
        "ma5_level": ma5,
        "last_completed_close": last_completed_close,
        "recent_completed_low": min(recent_lows) if recent_lows else None,
        "reclaim_level": max(reclaim_candidates) if reclaim_candidates else None,
    }


def _indexed_completed_price_rows(
    price_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    rows_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in price_rows:
        timestamp = _parse_ts(row.get("timestamp"))
        code = _normalize_stock_code(row.get("stock_code"))
        open_price = _number(row.get("open"))
        close = _number(row.get("close"))
        high = _number(row.get("high"))
        low = _number(row.get("low"))
        if (
            timestamp is None
            or not code
            or close is None
            or close <= 0
            or not _price_source_usable(row)
        ):
            continue
        rows_by_code[code].append(
            {
                **row,
                "_timestamp": timestamp,
                "_open": (
                    open_price if open_price is not None and open_price > 0 else None
                ),
                "_close": close,
                "_high": high if high is not None and high > 0 else close,
                "_low": low if low is not None and low > 0 else close,
            }
        )
    for rows in rows_by_code.values():
        rows.sort(key=lambda item: item["_timestamp"])
    return rows_by_code


def _forward_metrics_after_recovery(
    *,
    route_rows: list[dict[str, Any]],
    entry_row: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    entry_at = entry_row["_timestamp"]
    entry_price = entry_row["_open"]
    metrics: dict[str, dict[str, Any]] = {}
    for horizon in RECOVERY_OUTCOME_HORIZONS_MIN:
        horizon_end = entry_at + timedelta(minutes=horizon)
        expected_last_bar_at = horizon_end - timedelta(minutes=1)
        window = [
            row for row in route_rows if entry_at <= row["_timestamp"] < horizon_end
        ]
        if (
            not window
            or (expected_last_bar_at - window[-1]["_timestamp"]).total_seconds()
            > HORIZON_END_MAX_LAG_SEC
        ):
            continue
        metrics[f"{horizon}m"] = {
            "sample_count": len(window),
            "mfe_pct": max(
                round(((row["_high"] / entry_price) - 1.0) * 100.0, 10)
                for row in window
            ),
            "mae_pct": min(
                round(((row["_low"] / entry_price) - 1.0) * 100.0, 10) for row in window
            ),
            "end_return_pct": round(
                ((window[-1]["_close"] / entry_price) - 1.0) * 100.0,
                10,
            ),
            "counterfactual_only": True,
            "window_basis": "next_bar_open_after_recovery_same_route",
            "window_end": horizon_end.isoformat(),
        }
    return metrics


def build_recovery_trigger_report(
    *,
    target_date: str,
    paired_report: dict[str, Any],
    labels: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    price_source_provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Value EDGE+WAIT as retained observation, never as an immediate fill."""

    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    }
    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in paired_report.get("requests") or []
        if isinstance(row, dict)
    }
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    rows_by_code = _indexed_completed_price_rows(price_rows)
    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for result in paired_report.get("results") or []:
        if not isinstance(result, dict) or result.get("status") != "pass":
            continue
        candidate = result.get("candidate_response")
        candidate = candidate if isinstance(candidate, dict) else {}
        evidence = candidate.get("evidence")
        evidence = evidence if isinstance(evidence, dict) else {}
        if not (
            candidate.get("edge_state") == "EDGE"
            and candidate.get("action") == "WAIT"
            and evidence.get("trigger") == "recovery_required"
        ):
            continue
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_trace.get(trace_id) or {}
        label = label_by_trace.get(trace_id)
        payload_reference = {
            **request,
            "payload_sha256": (
                result.get("payload_sha256") or request.get("payload_sha256")
            ),
            "endpoint": request.get("endpoint") or "analyze_target",
        }
        payload_row = _payload_for_trace(
            payload_reference,
            payload_by_key=payload_by_key,
            payload_by_unique_hash=payload_by_unique_hash,
        )
        payload_hash = str(payload_reference.get("payload_sha256") or "")
        exact_payload = (
            _replay_exact_payload(replay_source_input(payload_row))
            if isinstance(payload_row, dict)
            else None
        )
        if not isinstance(label, dict) or not isinstance(exact_payload, dict):
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": (
                        "mature_exact_label_missing"
                        if not isinstance(label, dict)
                        else "exact_payload_missing"
                    ),
                }
            )
            continue
        code = _normalize_stock_code(
            label.get("stock_code") or request.get("stock_code")
        )
        decision_ts = _parse_ts(label.get("decision_ts"))
        levels = _snapshot_recovery_levels(exact_payload)
        if (
            not code
            or decision_ts is None
            or levels["reclaim_level"] is None
            or levels["recent_completed_low"] is None
        ):
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": "recovery_level_contract_missing",
                }
            )
            continue
        recovery_window_end = decision_ts + timedelta(
            minutes=RECOVERY_TRIGGER_WINDOW_MIN
        )
        route_rows = [
            row
            for row in rows_by_code.get(code, [])
            if decision_ts < row["_timestamp"] and _same_route(label, row)
        ]
        recovery_window = [
            row for row in route_rows if row["_timestamp"] <= recovery_window_end
        ]
        window_complete = (
            bool(recovery_window)
            and (
                recovery_window_end - recovery_window[-1]["_timestamp"]
            ).total_seconds()
            <= HORIZON_END_MAX_LAG_SEC
        )
        previous_close = (
            levels["last_completed_close"]
            or levels["reference_price"]
            or levels["reclaim_level"]
        )
        trigger_row = None
        adverse_row = None
        for row in recovery_window:
            if (
                trigger_row is None
                and row["_close"] >= levels["reclaim_level"]
                and row["_close"] > previous_close
            ):
                trigger_row = row
            if adverse_row is None and row["_low"] < levels["recent_completed_low"]:
                adverse_row = row
            previous_close = row["_close"]
        trigger_at = trigger_row["_timestamp"] if trigger_row else None
        adverse_at = adverse_row["_timestamp"] if adverse_row else None
        if trigger_at and adverse_at and trigger_at == adverse_at:
            first_event = "ambiguous_same_bar"
        elif trigger_at and (adverse_at is None or trigger_at < adverse_at):
            first_event = "recovery"
        elif adverse_at:
            first_event = "adverse"
        else:
            first_event = "none"
        recovery_eligible = first_event == "recovery"
        recovery_entry_row = None
        if recovery_eligible:
            next_route_row = next(
                (
                    row
                    for row in route_rows
                    if trigger_at and row["_timestamp"] > trigger_at
                ),
                None,
            )
            if (
                next_route_row is not None
                and next_route_row.get("_open") is not None
                and (next_route_row["_timestamp"] - trigger_at).total_seconds()
                <= HORIZON_END_MAX_LAG_SEC
            ):
                recovery_entry_row = next_route_row
        forward_metrics = (
            _forward_metrics_after_recovery(
                route_rows=route_rows,
                entry_row=recovery_entry_row,
            )
            if recovery_entry_row is not None
            else {}
        )
        primary_recovery_metric = forward_metrics.get("10m")
        decision_value = (
            _number(primary_recovery_metric.get("end_return_pct"))
            if isinstance(primary_recovery_metric, dict)
            else (0.0 if window_complete and not recovery_eligible else None)
        )
        control_action = str(
            (result.get("control_response") or {}).get("action") or ""
        ).upper()
        primary_control_metric = _primary_metric(label) or {}
        control_value = _decision_value(
            control_action,
            _number(primary_control_metric.get("end_return_pct")),
        )
        rows.append(
            {
                "decision_trace_id": trace_id,
                "paired_replay_id": result.get("paired_replay_id"),
                "payload_sha256": payload_hash,
                "stock_code": code,
                "effective_venue": label.get("effective_venue"),
                "session_bucket": label.get("session_bucket"),
                "decision_ts": decision_ts.isoformat(),
                "control_action": control_action,
                "candidate_action": "WAIT",
                "candidate_edge_state": "EDGE",
                "candidate_setup": evidence.get("setup"),
                "candidate_adverse_risk": evidence.get("adverse_risk"),
                "recovery_levels": {
                    key: (
                        round(value, 10) if isinstance(value, (int, float)) else value
                    )
                    for key, value in levels.items()
                },
                "recovery_window_min": RECOVERY_TRIGGER_WINDOW_MIN,
                "recovery_window_complete": window_complete,
                "recovery_trigger_at": (trigger_at.isoformat() if trigger_at else None),
                "adverse_breach_at": (adverse_at.isoformat() if adverse_at else None),
                "first_event": first_event,
                "recovery_entry_price": (
                    recovery_entry_row["_open"] if recovery_entry_row else None
                ),
                "recovery_entry_at": (
                    recovery_entry_row["_timestamp"].isoformat()
                    if recovery_entry_row
                    else None
                ),
                "recovery_trigger_close": (
                    trigger_row["_close"] if recovery_eligible and trigger_row else None
                ),
                "recovery_entry_move_from_snapshot_pct": (
                    round(
                        (
                            (recovery_entry_row["_open"] / levels["reference_price"])
                            - 1.0
                        )
                        * 100.0,
                        10,
                    )
                    if recovery_entry_row and levels["reference_price"]
                    else None
                ),
                "forward_metrics": forward_metrics,
                "control_decision_value_pct": control_value,
                "candidate_conditional_decision_value_pct": decision_value,
                "conditional_delta_pct": (
                    decision_value - control_value
                    if decision_value is not None and control_value is not None
                    else None
                ),
                "counterfactual_only": True,
            }
        )
    symbol_count = len(
        {str(row.get("stock_code") or "") for row in rows if row.get("stock_code")}
    )
    sample_floor_pass = (
        len(rows) >= RECOVERY_TRIGGER_MIN_ROWS
        and symbol_count >= RECOVERY_TRIGGER_MIN_SYMBOLS
    )
    comparable = [
        row
        for row in rows
        if row.get("control_decision_value_pct") is not None
        and row.get("candidate_conditional_decision_value_pct") is not None
    ]
    control_ev = (
        fmean(row["control_decision_value_pct"] for row in comparable)
        if comparable
        else None
    )
    candidate_ev = (
        fmean(row["candidate_conditional_decision_value_pct"] for row in comparable)
        if comparable
        else None
    )
    ev_delta = (
        candidate_ev - control_ev
        if candidate_ev is not None and control_ev is not None
        else None
    )
    missed_upside_reduction_count = sum(
        row["control_action"] in NO_EXPOSURE_ACTIONS
        and row["candidate_conditional_decision_value_pct"] > 0
        for row in comparable
    )
    control_negative_exposure_count = sum(
        row["control_decision_value_pct"] < 0 for row in comparable
    )
    candidate_negative_exposure_count = sum(
        row["candidate_conditional_decision_value_pct"] < 0 for row in comparable
    )
    quality_checks = {
        "sample_floor_pass": sample_floor_pass,
        "all_rows_comparable": bool(rows) and len(comparable) == len(rows),
        "source_quality_adjusted_ev_improved": ev_delta is not None and ev_delta > 0,
        "candidate_ev_positive": candidate_ev is not None and candidate_ev > 0,
        "missed_upside_reduced": missed_upside_reduction_count > 0,
        "negative_exposure_not_increased": (
            candidate_negative_exposure_count <= control_negative_exposure_count
        ),
    }
    quality_gate_pass = all(quality_checks.values())
    status = (
        "sample_floor_keep_collecting"
        if not sample_floor_pass
        else (
            "recovery_counterfactual_quality_pass_offline_only"
            if quality_gate_pass
            else "recovery_counterfactual_quality_rejected"
        )
    )
    return {
        "schema": RECOVERY_TRIGGER_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "eligible_row_count": len(rows),
        "eligible_symbol_count": symbol_count,
        "excluded_row_count": len(exclusions),
        "comparable_row_count": len(comparable),
        "sample_floor_pass": sample_floor_pass,
        "recovery_trigger_count": sum(
            row.get("first_event") == "recovery" for row in rows
        ),
        "adverse_first_count": sum(row.get("first_event") == "adverse" for row in rows),
        "ambiguous_same_bar_count": sum(
            row.get("first_event") == "ambiguous_same_bar" for row in rows
        ),
        "no_event_count": sum(row.get("first_event") == "none" for row in rows),
        "control_drop_recovery_count": sum(
            row.get("control_action") == "DROP" and row.get("first_event") == "recovery"
            for row in rows
        ),
        "control_source_quality_adjusted_ev_pct": control_ev,
        "candidate_source_quality_adjusted_ev_pct": candidate_ev,
        "source_quality_adjusted_ev_delta_pct": ev_delta,
        "missed_upside_reduction_count": missed_upside_reduction_count,
        "control_negative_exposure_count": control_negative_exposure_count,
        "candidate_negative_exposure_count": candidate_negative_exposure_count,
        "quality_gate_pass": quality_gate_pass,
        "quality_checks": quality_checks,
        "price_source_provenance": list(price_source_provenance or []),
        "rows": rows,
        "exclusions": exclusions,
        **RECOVERY_TRIGGER_CONTRACT,
    }


def _distance_bp(price: float | None, reference: Any) -> float | None:
    reference_value = _number(reference)
    if price is None or price <= 0 or reference_value is None or reference_value <= 0:
        return None
    return ((price / reference_value) - 1.0) * 10000.0


def _entry_multi_timeframe_context(exact_payload: dict[str, Any]) -> dict[str, Any]:
    candle_context = exact_payload.get("entry_candle_context")
    candle_context = candle_context if isinstance(candle_context, dict) else {}
    context = candle_context.get("multi_timeframe_context")
    return context if isinstance(context, dict) else {}


def _reversal_sequence_context_sha256(context: dict[str, Any]) -> str:
    non_feature_fields = {
        "candidate_action",
        "control_action",
        "conservative_execution_cost_pct",
        "episode_id",
        "outcome_join_key",
        "outcomes",
        "counterfactual_only",
        "sequence_context_sha256",
    }
    return _sha256(
        {
            key: value
            for key, value in context.items()
            if key not in non_feature_fields and not key.startswith("_")
        }
    )


def _entry_reversal_snapshot_context(
    *,
    request: dict[str, Any],
    payload_row: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    exact_payload = _replay_exact_payload(replay_source_input(payload_row))
    if not isinstance(exact_payload, dict):
        return None, "exact_payload_missing"
    request_payload_sha256 = str(request.get("payload_sha256") or "")
    stored_payload_sha256 = str(payload_row.get("payload_sha256") or "")
    source_exact_sha256 = str(request.get("source_exact_payload_sha256") or "")
    candidate_exact_sha256 = str(request.get("candidate_exact_payload_sha256") or "")
    if (
        payload_row.get("replay_exact") is not True
        or not request_payload_sha256
        or stored_payload_sha256 != request_payload_sha256
        or not source_exact_sha256
        or source_exact_sha256 != candidate_exact_sha256
        or request.get("stage") != "entry"
    ):
        return None, "exact_payload_contract_mismatch"
    request_code = _normalize_stock_code(request.get("stock_code"))
    request_venue = _venue(request.get("effective_venue"))
    request_session = _session(request.get("session_bucket"))
    payload_code = _normalize_stock_code(
        payload_row.get("symbol") or payload_row.get("stock_code")
    )
    payload_venue = _venue(payload_row.get("effective_venue"))
    payload_session = _session(payload_row.get("session_bucket"))
    if (
        not request_code
        or request_code != payload_code
        or not request_venue
        or request_venue != payload_venue
        or not request_session
        or request_session != payload_session
        or not _venue_session_consistent(request_venue, request_session)
    ):
        return None, "payload_venue_session_contract_mismatch"
    candle_context = exact_payload.get("entry_candle_context")
    candle_context = candle_context if isinstance(candle_context, dict) else {}
    completed_bars = [
        row
        for row in candle_context.get("bars") or []
        if isinstance(row, dict) and row.get("forming") is not True
    ]
    if (
        candle_context.get("schema") != ENTRY_CONTEXT_SCHEMA
        or candle_context.get("input_bundle_version") != INPUT_BUNDLE_VERSION
        or _venue(candle_context.get("venue")) != request_venue
        or _session(candle_context.get("session")) != request_session
        or not completed_bars
        or (_number(candle_context.get("completed_bar_count")) or 0)
        < len(completed_bars)
    ):
        return None, "canonical_completed_bar_contract_mismatch"
    captured_at = _parse_ts(payload_row.get("captured_at"))
    if captured_at is None:
        return None, "captured_at_missing"
    current = exact_payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = exact_payload.get("features")
    features = features if isinstance(features, dict) else {}
    analysis = request.get("exact_payload_analysis")
    analysis = analysis if isinstance(analysis, dict) else {}
    source_quality = analysis.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, dict) else {}
    structure = analysis.get("completed_structure")
    structure = structure if isinstance(structure, dict) else {}
    returns = structure.get("returns_pct")
    returns = returns if isinstance(returns, dict) else {}
    multi_timeframe = _entry_multi_timeframe_context(exact_payload)
    previous_day = multi_timeframe.get("previous_day_levels")
    previous_day = previous_day if isinstance(previous_day, dict) else {}
    session_vwap = multi_timeframe.get("session_bar_vwap")
    session_vwap = session_vwap if isinstance(session_vwap, dict) else {}

    price = _number(current.get("price"))
    net_aggressive_delta = _number(features.get("net_aggressive_delta_10t"))
    buy_pressure = _number(features.get("buy_pressure_10t"))
    absorption_count = _number(features.get("same_price_buy_absorption"))
    price_change_10t_pct = _number(features.get("price_change_10t_pct"))
    ma5_distance_bp = _number(features.get("curr_vs_ma5_bp"))
    micro_vwap_distance_bp = _number(features.get("curr_vs_micro_vwap_bp"))
    if None in {
        price,
        net_aggressive_delta,
        buy_pressure,
        absorption_count,
        price_change_10t_pct,
    }:
        return None, "required_reversal_feature_missing"

    reference_distances_bp = {
        "micro_vwap": micro_vwap_distance_bp,
        "ma5": ma5_distance_bp,
        "session_vwap": _distance_bp(price, session_vwap.get("value")),
        "previous_low": _distance_bp(price, previous_day.get("low")),
        "previous_close": _distance_bp(price, previous_day.get("close")),
        "previous_high": _distance_bp(price, previous_day.get("high")),
    }
    valid_reference_distances = {
        key: value for key, value in reference_distances_bp.items() if value is not None
    }
    nearest_reference = (
        min(
            valid_reference_distances,
            key=lambda key: abs(valid_reference_distances[key]),
        )
        if valid_reference_distances
        else None
    )
    nearest_reference_distance_bp = (
        valid_reference_distances[nearest_reference]
        if nearest_reference is not None
        else None
    )
    return_1m = _number(returns.get("1m"))
    return_3m = _number(returns.get("3m"))
    return_5m = _number(returns.get("5m"))
    return_10m = _number(returns.get("10m"))
    return_20m = _number(returns.get("20m"))
    fluctuation_pct = _number(current.get("fluctuation_pct"))
    distance_from_day_high_pct = _number(features.get("distance_from_day_high_pct"))

    reference_near = bool(
        nearest_reference_distance_bp is not None
        and abs(nearest_reference_distance_bp) <= REVERSAL_SEQUENCE_REFERENCE_NEAR_BP
    )
    moving_average_near = bool(
        (
            ma5_distance_bp is not None
            and abs(ma5_distance_bp) <= REVERSAL_SEQUENCE_MA_NEAR_BP
        )
        or (
            micro_vwap_distance_bp is not None
            and abs(micro_vwap_distance_bp) <= REVERSAL_SEQUENCE_MA_NEAR_BP
        )
    )
    support_flush = bool(
        fluctuation_pct is not None
        and fluctuation_pct < 0
        and (reference_near or moving_average_near)
    )
    trend_pullback = bool(
        return_20m is not None
        and return_20m > 0
        and (
            (return_1m is not None and return_1m <= 0)
            or (return_3m is not None and return_3m <= 0)
        )
        and (reference_near or moving_average_near)
    )
    continuation_shakeout = bool(
        all(
            value is not None and value > 0
            for value in (return_5m, return_10m, return_20m)
        )
        and distance_from_day_high_pct is not None
        and distance_from_day_high_pct >= -1.5
    )
    adverse_tape = bool(net_aggressive_delta < 0 and buy_pressure < 50)
    price_resilience = bool(
        absorption_count >= 1
        and price_change_10t_pct >= REVERSAL_SEQUENCE_MAX_PRICE_DECLINE_PCT
    )
    source_fresh = bool(
        source_quality.get("status") == "fresh_consistent"
        and (_number(source_quality.get("completed_bar_count")) or 0) > 0
        and features.get("quote_fresh_for_entry") is True
        and features.get("tick_context_stale") is not True
        and features.get("minute_candle_window_fresh") is True
        and request.get("candidate_exact_payload_sha256")
        == request.get("source_exact_payload_sha256")
    )
    archetypes = {
        "support_flush": support_flush,
        "trend_pullback": trend_pullback,
        "continuation_shakeout": continuation_shakeout,
    }
    reversal_armed = bool(
        source_fresh and adverse_tape and price_resilience and any(archetypes.values())
    )
    spread_bp = _number(features.get("spread_bp"))
    context = {
        "schema": REVERSAL_SEQUENCE_CONTEXT_SCHEMA,
        "decision_trace_id": request.get("decision_trace_id"),
        "captured_at": captured_at.isoformat(),
        "stock_code": request_code,
        "effective_venue": request_venue,
        "session_bucket": request_session,
        "payload_sha256": request_payload_sha256,
        "candidate_input_sha256": request.get("candidate_input_sha256"),
        "source_quality": {
            "status": source_quality.get("status"),
            "completed_bar_count": source_quality.get("completed_bar_count"),
            "exact_payload_hash_match": (
                bool(source_exact_sha256)
                and source_exact_sha256 == candidate_exact_sha256
            ),
            "payload_venue_session_match": True,
            "canonical_raw_completed_bar_count": len(completed_bars),
            "future_outcome_feature_count": 0,
        },
        "current": {
            "price": price,
            "fluctuation_pct": fluctuation_pct,
            "execution_strength": _number(current.get("execution_strength")),
        },
        "tape_price_response": {
            "net_aggressive_delta_10t": net_aggressive_delta,
            "buy_pressure_10t": buy_pressure,
            "same_price_buy_absorption": absorption_count,
            "price_change_10t_pct": price_change_10t_pct,
            "large_sell_print_detected": bool(
                features.get("large_sell_print_detected")
            ),
            "adverse_tape": adverse_tape,
            "price_resilience": price_resilience,
        },
        "liquidity": {
            "spread_bp": spread_bp,
            "wide_spread_observed": bool(spread_bp is not None and spread_bp >= 60.0),
            "orderbook_total_ratio": _number(features.get("orderbook_total_ratio")),
            "fillability_score": _number(features.get("fillability_score")),
            "quote_fresh_for_entry": features.get("quote_fresh_for_entry") is True,
        },
        "completed_structure": {
            "phase": structure.get("phase"),
            "structural_edge": structure.get("structural_edge"),
            "return_1m_pct": return_1m,
            "return_3m_pct": return_3m,
            "return_5m_pct": return_5m,
            "return_10m_pct": return_10m,
            "return_20m_pct": return_20m,
            "distance_from_day_high_pct": distance_from_day_high_pct,
        },
        "reference_context": {
            "distances_bp": reference_distances_bp,
            "nearest_reference": nearest_reference,
            "nearest_reference_distance_bp": nearest_reference_distance_bp,
            "reference_near": reference_near,
            "moving_average_near": moving_average_near,
        },
        "archetypes": archetypes,
        "reversal_armed": reversal_armed,
        "reversal_state": "ARMED" if reversal_armed else "NOT_ARMED",
        "state_reason_codes": [
            reason
            for reason, present in (
                ("fresh_exact_source", source_fresh),
                ("adverse_tape", adverse_tape),
                ("price_resilient_to_sell_pressure", price_resilience),
                ("meaningful_reference_near", reference_near or moving_average_near),
                ("support_flush", support_flush),
                ("trend_pullback", trend_pullback),
                ("continuation_shakeout", continuation_shakeout),
                (
                    "wide_spread_observation_not_confirmation",
                    spread_bp is not None and spread_bp >= 60.0,
                ),
            )
            if present
        ],
        "transition": {
            "previous_snapshot_available": False,
            "previous_decision_trace_id": None,
            "elapsed_sec": None,
            "confirmation_score": 0,
            "confirmation_components": {},
        },
        **REVERSAL_SEQUENCE_CONTRACT,
    }
    context["sequence_context_sha256"] = _reversal_sequence_context_sha256(context)
    return context, None


def _attach_reversal_transition(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    context = dict(current)
    context["transition"] = dict(current.get("transition") or {})
    if previous is None:
        context["sequence_context_sha256"] = _reversal_sequence_context_sha256(context)
        return context
    current_at = _parse_ts(current.get("captured_at"))
    previous_at = _parse_ts(previous.get("captured_at"))
    if current_at is None or previous_at is None:
        return context
    elapsed_sec = (current_at - previous_at).total_seconds()
    if elapsed_sec <= 0 or elapsed_sec > REVERSAL_SEQUENCE_MAX_PREVIOUS_SEC:
        return context

    current_price = _number((current.get("current") or {}).get("price"))
    previous_price = _number((previous.get("current") or {}).get("price"))
    price_delta_pct = (
        ((current_price / previous_price) - 1.0) * 100.0
        if current_price is not None
        and previous_price is not None
        and previous_price > 0
        else None
    )
    current_tape = current.get("tape_price_response") or {}
    previous_tape = previous.get("tape_price_response") or {}
    current_net = _number(current_tape.get("net_aggressive_delta_10t"))
    previous_net = _number(previous_tape.get("net_aggressive_delta_10t"))
    current_pressure = _number(current_tape.get("buy_pressure_10t"))
    previous_pressure = _number(previous_tape.get("buy_pressure_10t"))
    current_absorption = _number(current_tape.get("same_price_buy_absorption"))
    previous_absorption = _number(previous_tape.get("same_price_buy_absorption"))
    current_reference = _number(
        (current.get("reference_context") or {}).get("nearest_reference_distance_bp")
    )
    previous_reference = _number(
        (previous.get("reference_context") or {}).get("nearest_reference_distance_bp")
    )
    price_floor_held = bool(
        price_delta_pct is not None
        and price_delta_pct >= REVERSAL_SEQUENCE_MAX_PRICE_DECLINE_PCT
    )
    reference_not_worse = bool(
        current_reference is not None
        and previous_reference is not None
        and abs(current_reference) <= abs(previous_reference) + 25.0
    )
    sell_pressure_not_worsening = bool(
        (
            current_net is not None
            and previous_net is not None
            and current_net >= previous_net
        )
        or (
            current_pressure is not None
            and previous_pressure is not None
            and current_pressure >= previous_pressure
        )
        or (price_delta_pct is not None and price_delta_pct >= 0)
    )
    absorption_persistent = bool(
        current_absorption is not None
        and previous_absorption is not None
        and current_absorption >= 1
        and previous_absorption >= 1
    )
    large_sell_cleared = bool(
        previous_tape.get("large_sell_print_detected") is True
        and current_tape.get("large_sell_print_detected") is False
    )
    sell_shock_absorbed = bool(
        current.get("reversal_armed") is True
        and previous_net is not None
        and previous_net >= 0
        and current_net is not None
        and current_net < 0
        and price_floor_held
        and absorption_persistent
    )
    resilience_persistent = bool(
        previous.get("reversal_armed") is True
        and current.get("reversal_armed") is True
        and price_floor_held
        and reference_not_worse
    )
    confirmation_components = {
        "price_floor_held": price_floor_held,
        "reference_not_worse": reference_not_worse,
        "sell_pressure_not_worsening": sell_pressure_not_worsening,
        "absorption_persistent": absorption_persistent,
        "large_sell_cleared": large_sell_cleared,
        "sell_shock_absorbed": sell_shock_absorbed,
        "resilience_persistent": resilience_persistent,
    }
    confirmation_score = sum(
        confirmation_components[key]
        for key in (
            "price_floor_held",
            "reference_not_worse",
            "sell_pressure_not_worsening",
            "absorption_persistent",
            "large_sell_cleared",
        )
    )
    confirmed = bool(
        current.get("reversal_armed") is True
        and (sell_shock_absorbed or resilience_persistent)
        and confirmation_score >= 3
    )
    invalidated = bool(
        previous.get("reversal_armed") is True
        and current.get("reversal_armed") is not True
        and price_delta_pct is not None
        and price_delta_pct < REVERSAL_SEQUENCE_MAX_PRICE_DECLINE_PCT
        and current_tape.get("adverse_tape") is True
    )
    state = (
        "CONFIRMED"
        if confirmed
        else (
            "INVALIDATED"
            if invalidated
            else ("ARMED" if current.get("reversal_armed") is True else "NOT_ARMED")
        )
    )
    context["reversal_state"] = state
    context["state_reason_codes"] = list(current.get("state_reason_codes") or []) + [
        reason
        for reason, present in (
            ("sell_shock_absorbed", sell_shock_absorbed),
            ("price_resilience_persistent", resilience_persistent),
            ("reversal_transition_confirmed", confirmed),
            ("reversal_transition_invalidated", invalidated),
        )
        if present
    ]
    context["transition"] = {
        "previous_snapshot_available": True,
        "previous_decision_trace_id": previous.get("decision_trace_id"),
        "elapsed_sec": elapsed_sec,
        "price_delta_pct": price_delta_pct,
        "net_aggressive_delta_change": (
            current_net - previous_net
            if current_net is not None and previous_net is not None
            else None
        ),
        "buy_pressure_change": (
            current_pressure - previous_pressure
            if current_pressure is not None and previous_pressure is not None
            else None
        ),
        "nearest_reference_abs_distance_change_bp": (
            abs(current_reference) - abs(previous_reference)
            if current_reference is not None and previous_reference is not None
            else None
        ),
        "confirmation_score": confirmation_score,
        "confirmation_components": confirmation_components,
    }
    context["sequence_context_sha256"] = _reversal_sequence_context_sha256(context)
    return context


def _sequence_horizon_summary(
    rows: list[dict[str, Any]],
    horizon: int,
) -> dict[str, Any]:
    horizon_key = f"{horizon}m"
    mature_rows = [
        row
        for row in rows
        if isinstance((row.get("outcomes") or {}).get(horizon_key), dict)
    ]
    metrics = [(row.get("outcomes") or {})[horizon_key] for row in mature_rows]

    def mean_metric(key: str) -> float | None:
        values = [
            value
            for metric in metrics
            if (value := _number(metric.get(key))) is not None
        ]
        return fmean(values) if values else None

    adjusted_values = [
        end_return - cost
        for row, metric in zip(mature_rows, metrics)
        if (end_return := _number(metric.get("end_return_pct"))) is not None
        and (cost := _number(row.get("conservative_execution_cost_pct"))) is not None
    ]
    recovery_count = sum(
        metric.get("profit_opportunity_sequence") == "drawdown_then_profit_recovery"
        for metric in metrics
    )
    return {
        "horizon_min": horizon,
        "sample_count": len(mature_rows),
        "unique_symbol_count": len(
            {
                _normalize_stock_code(row.get("stock_code"))
                for row in mature_rows
                if _normalize_stock_code(row.get("stock_code"))
            }
        ),
        "drawdown_recovery_count": recovery_count,
        "drawdown_recovery_rate_pct": (
            recovery_count / len(mature_rows) * 100.0 if mature_rows else None
        ),
        "profit_opportunity_count": sum(
            metric.get("profit_opportunity_observed") is True for metric in metrics
        ),
        "profit_opportunity_rate_pct": (
            sum(metric.get("profit_opportunity_observed") is True for metric in metrics)
            / len(mature_rows)
            * 100.0
            if mature_rows
            else None
        ),
        "equal_weight_avg_profit_pct": mean_metric("end_return_pct"),
        "source_quality_adjusted_ev_pct": (
            fmean(adjusted_values) if adjusted_values else None
        ),
        "avg_mfe_pct": mean_metric("mfe_pct"),
        "avg_mae_pct": mean_metric("mae_pct"),
        "worst_mae_pct": (
            min(
                value
                for metric in metrics
                if (value := _number(metric.get("mae_pct"))) is not None
            )
            if any(_number(metric.get("mae_pct")) is not None for metric in metrics)
            else None
        ),
        "counterfactual_only": True,
    }


def _first_signal_episode_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_rows: dict[str, dict[str, Any]] = {}
    for row in sorted(
        rows,
        key=lambda value: (
            str(value.get("episode_id") or ""),
            str(value.get("captured_at") or ""),
        ),
    ):
        episode_id = str(row.get("episode_id") or "")
        if episode_id and episode_id not in first_rows:
            first_rows[episode_id] = row
    return list(first_rows.values())


def _scale_in_horizon_counterfactual(
    *,
    first_signal: dict[str, Any],
    second_confirmation: dict[str, Any],
    horizon: int,
) -> dict[str, Any] | None:
    metric = (second_confirmation.get("outcomes") or {}).get(f"{horizon}m")
    if not isinstance(metric, dict):
        return None
    first_price = _number((first_signal.get("current") or {}).get("price"))
    second_price = _number((second_confirmation.get("current") or {}).get("price"))
    end_return = _number(metric.get("end_return_pct"))
    mfe = _number(metric.get("mfe_pct"))
    mae = _number(metric.get("mae_pct"))
    first_cost = _number(first_signal.get("conservative_execution_cost_pct"))
    second_cost = _number(second_confirmation.get("conservative_execution_cost_pct"))
    if (
        first_price is None
        or first_price <= 0
        or second_price is None
        or second_price <= 0
        or end_return is None
        or mfe is None
        or mae is None
        or first_cost is None
        or second_cost is None
    ):
        return None
    average_cost = (first_price + second_price) / 2.0
    end_price = second_price * (1.0 + (end_return / 100.0))
    high_price = second_price * (1.0 + (mfe / 100.0))
    low_price = second_price * (1.0 + (mae / 100.0))
    combined_cost_pct = ((first_price * first_cost) + (second_price * second_cost)) / (
        first_price + second_price
    )
    probe_only_end_return = ((end_price / first_price) - 1.0) * 100.0
    combined_end_return = ((end_price / average_cost) - 1.0) * 100.0
    combined_mfe = ((high_price / average_cost) - 1.0) * 100.0
    combined_mae = ((low_price / average_cost) - 1.0) * 100.0
    probe_only_net_ev = probe_only_end_return - first_cost
    combined_net_ev = combined_end_return - combined_cost_pct
    second_leg_net_ev = end_return - second_cost
    return {
        "horizon_min": horizon,
        "average_cost": average_cost,
        "probe_only_end_return_pct": probe_only_end_return,
        "probe_only_net_ev_pct": probe_only_net_ev,
        "second_leg_end_return_pct": end_return,
        "second_leg_incremental_net_ev_pct": second_leg_net_ev,
        "combined_end_return_pct": combined_end_return,
        "combined_net_ev_pct": combined_net_ev,
        "combined_mfe_pct": combined_mfe,
        "combined_mae_pct": combined_mae,
        "combined_cost_pct": combined_cost_pct,
        "scale_in_vs_probe_only_net_ev_delta_pct": (
            combined_net_ev - probe_only_net_ev
        ),
        "combined_positive_excursion_after_cost": (combined_mfe > combined_cost_pct),
        "combined_end_profitable_after_cost": combined_net_ev > 0,
        "second_leg_incremental_ev_positive": second_leg_net_ev > 0,
        "counterfactual_only": True,
    }


def _build_scale_in_counterfactual(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("episode_id"):
            grouped[str(row["episode_id"])].append(row)
    pair_rows: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    for episode_id, episode_rows in grouped.items():
        ordered = sorted(
            episode_rows, key=lambda row: str(row.get("captured_at") or "")
        )
        armed_rows = [
            row
            for row in ordered
            if row.get("reversal_armed") is True
            and row.get("candidate_action") == "DROP"
        ]
        if not armed_rows:
            exclusion_counts["first_reversal_signal_missing"] += 1
            continue
        first_signal = armed_rows[0]
        first_at = _parse_ts(first_signal.get("captured_at"))
        first_price = _number((first_signal.get("current") or {}).get("price"))
        if first_at is None or first_price is None or first_price <= 0:
            exclusion_counts["first_signal_time_or_price_missing"] += 1
            continue
        second_confirmation = None
        invalidated_before_second = False
        for row in ordered:
            row_at = _parse_ts(row.get("captured_at"))
            if row_at is None or row_at <= first_at:
                continue
            if row.get("reversal_state") == "INVALIDATED":
                invalidated_before_second = True
                break
            row_price = _number((row.get("current") or {}).get("price"))
            if (
                row.get("reversal_state") == "CONFIRMED"
                and row.get("candidate_action") == "DROP"
                and row_price is not None
                and row_price < first_price
            ):
                second_confirmation = row
                break
        if second_confirmation is None:
            exclusion_counts[
                (
                    "invalidated_before_lower_confirmation"
                    if invalidated_before_second
                    else "lower_second_confirmation_missing"
                )
            ] += 1
            continue
        second_at = _parse_ts(second_confirmation.get("captured_at"))
        second_price = _number((second_confirmation.get("current") or {}).get("price"))
        horizon_metrics = {
            f"{horizon}m": metric
            for horizon in REVERSAL_SEQUENCE_HORIZONS_MIN
            if (
                metric := _scale_in_horizon_counterfactual(
                    first_signal=first_signal,
                    second_confirmation=second_confirmation,
                    horizon=horizon,
                )
            )
            is not None
        }
        pair_rows.append(
            {
                "episode_id": episode_id,
                "stock_code": first_signal.get("stock_code"),
                "effective_venue": first_signal.get("effective_venue"),
                "session_bucket": first_signal.get("session_bucket"),
                "first_decision_trace_id": first_signal.get("decision_trace_id"),
                "first_signal_at": first_at.isoformat(),
                "first_signal_state": first_signal.get("reversal_state"),
                "first_price": first_price,
                "second_decision_trace_id": second_confirmation.get(
                    "decision_trace_id"
                ),
                "second_confirmation_at": (
                    second_at.isoformat() if second_at is not None else None
                ),
                "second_price": second_price,
                "second_price_change_from_probe_pct": (
                    ((second_price / first_price) - 1.0) * 100.0
                    if second_price is not None
                    else None
                ),
                "elapsed_sec": (
                    (second_at - first_at).total_seconds()
                    if second_at is not None
                    else None
                ),
                "sizing_policy": "one_share_probe_plus_one_share_confirmation",
                "horizon_metrics": horizon_metrics,
                "counterfactual_only": True,
                "runtime_effect": False,
                "actual_order_submitted": False,
            }
        )
    primary_rows = [
        row["horizon_metrics"]["20m"]
        for row in pair_rows
        if isinstance(row.get("horizon_metrics", {}).get("20m"), dict)
    ]

    def primary_mean(key: str) -> float | None:
        values = [
            value
            for row in primary_rows
            if (value := _number(row.get(key))) is not None
        ]
        return fmean(values) if values else None

    symbol_count = len(
        {str(row.get("stock_code") or "") for row in pair_rows if row.get("stock_code")}
    )
    combined_positive_count = sum(
        row.get("combined_end_profitable_after_cost") is True for row in primary_rows
    )
    excursion_positive_count = sum(
        row.get("combined_positive_excursion_after_cost") is True
        for row in primary_rows
    )
    excursion_negative_count = len(primary_rows) - excursion_positive_count
    sample_floor_pass = bool(primary_rows)
    learning_value_pass = bool(
        sample_floor_pass
        and excursion_positive_count > 0
        and excursion_negative_count > 0
        and excursion_positive_count / len(primary_rows) >= 0.5
    )
    economics_pass = bool(
        sample_floor_pass
        and (primary_mean("combined_net_ev_pct") or 0) > 0
        and (primary_mean("second_leg_incremental_net_ev_pct") or 0) > 0
        and combined_positive_count / len(primary_rows) >= 0.5
    )
    status = (
        "scale_in_economics_pass_offline_only"
        if economics_pass
        else (
            "probe_learning_candidate_ready_economics_rejected"
            if learning_value_pass
            else "scale_in_economics_rejected_probe_floor_not_met"
        )
    )
    return {
        "schema": "entry_reversal_scale_in_counterfactual_v1",
        "status": status,
        "decision": status,
        "pair_count": len(pair_rows),
        "primary_20m_pair_count": len(primary_rows),
        "unique_symbol_count": symbol_count,
        "exclusion_counts": dict(exclusion_counts),
        "sizing_policy": "one_share_probe_plus_one_share_confirmation",
        "pair_selection_policy": (
            "first_armed_then_first_lower_price_confirmed_before_invalidation_"
            "same_exact_episode"
        ),
        "sample_floor": "one_exact_pair_starts_cumulative_probe_learning",
        "primary_decision_metric": "20m_combined_and_incremental_net_ev_pct",
        "economic_quality_pass": economics_pass,
        "probe_learning_value_pass": learning_value_pass,
        "probe_learning_minimum_favorable_rate_pct": 50.0,
        "primary_20m": {
            "combined_end_profitable_after_cost_count": combined_positive_count,
            "combined_end_profitable_after_cost_rate_pct": (
                combined_positive_count / len(primary_rows) * 100.0
                if primary_rows
                else None
            ),
            "combined_positive_excursion_after_cost_count": (excursion_positive_count),
            "combined_positive_excursion_after_cost_rate_pct": (
                excursion_positive_count / len(primary_rows) * 100.0
                if primary_rows
                else None
            ),
            "combined_net_ev_pct": primary_mean("combined_net_ev_pct"),
            "second_leg_incremental_net_ev_pct": primary_mean(
                "second_leg_incremental_net_ev_pct"
            ),
            "scale_in_vs_probe_only_net_ev_delta_pct": primary_mean(
                "scale_in_vs_probe_only_net_ev_delta_pct"
            ),
            "combined_mfe_pct": primary_mean("combined_mfe_pct"),
            "combined_mae_pct": primary_mean("combined_mae_pct"),
            "worst_combined_mae_pct": (
                min(
                    value
                    for row in primary_rows
                    if (value := _number(row.get("combined_mae_pct"))) is not None
                )
                if any(
                    _number(row.get("combined_mae_pct")) is not None
                    for row in primary_rows
                )
                else None
            ),
        },
        "runtime_promotion": {
            "status": "not_authorized_by_offline_validation",
            "required_cap": "one_share_each_leg",
            "hard_safety_unchanged": True,
            "provider_route_unchanged": True,
            "runtime_effect": False,
            "actual_order_submitted": False,
        },
        "rows": pair_rows,
        "metric_role": "ai_entry_reversal_scale_in_counterfactual_observation",
        "decision_authority": "offline_probe_learning_validation_only",
        "window_policy": (
            "second_confirmation_same_exact_episode_then_mature_5_10_20_30_60m"
        ),
        "source_quality_gate": (
            "exact_hash_route_session_completed_bar_and_no_prior_invalidation"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _build_one_share_probe_counterfactual(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    first_signals = _first_signal_episode_rows(
        [row for row in rows if row.get("reversal_armed") is True]
    )
    probe_rows: list[dict[str, Any]] = []
    for row in first_signals:
        cost = _number(row.get("conservative_execution_cost_pct"))
        probe_rows.append(
            {
                "episode_id": row.get("episode_id"),
                "decision_trace_id": row.get("decision_trace_id"),
                "stock_code": row.get("stock_code"),
                "effective_venue": row.get("effective_venue"),
                "session_bucket": row.get("session_bucket"),
                "signal_at": row.get("captured_at"),
                "signal_state": row.get("reversal_state"),
                "price": (row.get("current") or {}).get("price"),
                "conservative_execution_cost_pct": cost,
                "horizons": {
                    key: {
                        "mfe_pct": metric.get("mfe_pct"),
                        "mae_pct": metric.get("mae_pct"),
                        "end_return_pct": metric.get("end_return_pct"),
                        "favorable_excursion_after_cost_observed": bool(
                            cost is not None
                            and _number(metric.get("mfe_pct")) is not None
                            and _number(metric.get("mfe_pct")) > cost
                        ),
                        "net_end_return_pct": (
                            _number(metric.get("end_return_pct")) - cost
                            if cost is not None
                            and _number(metric.get("end_return_pct")) is not None
                            else None
                        ),
                    }
                    for key, metric in (row.get("outcomes") or {}).items()
                    if isinstance(metric, dict)
                },
                "counterfactual_only": True,
                "runtime_effect": False,
                "actual_order_submitted": False,
            }
        )
    horizon_summaries: dict[str, Any] = {}
    for horizon in REVERSAL_SEQUENCE_HORIZONS_MIN:
        horizon_key = f"{horizon}m"
        mature: list[tuple[dict[str, Any], dict[str, Any], float]] = []
        for row in first_signals:
            metric = (row.get("outcomes") or {}).get(horizon_key)
            cost = _number(row.get("conservative_execution_cost_pct"))
            if (
                not isinstance(metric, dict)
                or cost is None
                or _number(metric.get("mfe_pct")) is None
                or _number(metric.get("mae_pct")) is None
                or _number(metric.get("end_return_pct")) is None
            ):
                continue
            mature.append((row, metric, cost))
        favorable_count = sum(
            _number(metric.get("mfe_pct")) > cost for _, metric, cost in mature
        )
        net_end_values = [
            _number(metric.get("end_return_pct")) - cost for _, metric, cost in mature
        ]
        horizon_summaries[horizon_key] = {
            "horizon_min": horizon,
            "sample_count": len(mature),
            "unique_symbol_count": len(
                {
                    str(row.get("stock_code") or "")
                    for row, _, _ in mature
                    if row.get("stock_code")
                }
            ),
            "favorable_excursion_after_cost_count": favorable_count,
            "favorable_excursion_after_cost_rate_pct": (
                favorable_count / len(mature) * 100.0 if mature else None
            ),
            "net_end_profitable_count": sum(value > 0 for value in net_end_values),
            "net_end_profitable_rate_pct": (
                sum(value > 0 for value in net_end_values) / len(mature) * 100.0
                if mature
                else None
            ),
            "source_quality_adjusted_ev_pct": (
                fmean(net_end_values) if net_end_values else None
            ),
            "avg_mfe_pct": (
                fmean(_number(metric.get("mfe_pct")) for _, metric, _ in mature)
                if mature
                else None
            ),
            "avg_mae_pct": (
                fmean(_number(metric.get("mae_pct")) for _, metric, _ in mature)
                if mature
                else None
            ),
            "worst_mae_pct": (
                min(_number(metric.get("mae_pct")) for _, metric, _ in mature)
                if mature
                else None
            ),
            "mfe_to_abs_mae_ratio": (
                (
                    fmean(_number(metric.get("mfe_pct")) for _, metric, _ in mature)
                    / abs(
                        fmean(_number(metric.get("mae_pct")) for _, metric, _ in mature)
                    )
                )
                if mature
                and fmean(_number(metric.get("mae_pct")) for _, metric, _ in mature)
                != 0
                else None
            ),
            "counterfactual_only": True,
        }
    learning_horizons = [
        key
        for key, summary in horizon_summaries.items()
        if (summary.get("sample_count") or 0) > 0
        and (summary.get("favorable_excursion_after_cost_count") or 0) > 0
        and summary.get("favorable_excursion_after_cost_count")
        < summary.get("sample_count")
        and (_number(summary.get("favorable_excursion_after_cost_rate_pct")) or 0)
        >= 50.0
    ]
    primary = horizon_summaries.get("20m") or {}
    economic_quality_pass = bool(
        (_number(primary.get("source_quality_adjusted_ev_pct")) or 0) > 0
        and (_number(primary.get("net_end_profitable_rate_pct")) or 0) >= 50.0
    )
    learning_value_pass = bool(learning_horizons)
    status = (
        "one_share_probe_economics_pass_offline_only"
        if economic_quality_pass
        else (
            "one_share_probe_learning_candidate_ready_economics_rejected"
            if learning_value_pass
            else "one_share_probe_learning_floor_not_met"
        )
    )
    return {
        "schema": "entry_reversal_one_share_probe_counterfactual_v1",
        "status": status,
        "decision": status,
        "first_signal_episode_count": len(first_signals),
        "sample_floor": "one_exact_episode_starts_cumulative_probe_learning",
        "learning_minimum_favorable_rate_pct": 50.0,
        "learning_value_pass": learning_value_pass,
        "economic_quality_pass": economic_quality_pass,
        "learning_ready_horizons": learning_horizons,
        "learning_objective": (
            "holding_exit_timing_after_one_share_probe_favorable_excursion"
        ),
        "learning_value_basis": (
            "observed_outcome_diversity_not_trade_success_probability"
        ),
        "horizons": horizon_summaries,
        "interpretation": (
            "A favorable MFE above estimated cost supports one-share outcome "
            "collection. It does not prove that the excursion occurred before a "
            "hard-safety exit or that the end-of-horizon position is profitable."
        ),
        "forbidden_inference": (
            "favorable_excursion_rate_is_not_entry_accuracy_or_live_ev"
        ),
        "runtime_promotion": {
            "status": "not_authorized_by_offline_validation",
            "required_cap": "one_share_probe_only",
            "scale_in_authority": False,
            "hard_safety_unchanged": True,
            "provider_route_unchanged": True,
            "runtime_effect": False,
            "actual_order_submitted": False,
        },
        "proposed_authority_separation": {
            "status": "offline_validated_not_runtime_applied",
            "entry_ai_role": "permissive_one_share_probe_intent",
            "upstream_policy": (
                "do_not_require_retrospective_economic_quality_pass_before_"
                "one_share_probe_intent"
            ),
            "upstream_required": (
                "exact_source_and_semantic_contract_without_known_hard_safety_block"
            ),
            "final_submit_authority": (
                "existing_freshness_price_broker_account_order_cooldown_quantity_"
                "and_hard_safety_guards"
            ),
            "economic_quality_role": "cumulative_post_outcome_learning_not_submit_veto",
            "submit_guard_is_not_directional_alpha_proof": True,
            "runtime_effect": False,
            "actual_order_submitted": False,
        },
        "rows": probe_rows,
        "metric_role": "ai_entry_reversal_one_share_probe_learning_observation",
        "decision_authority": "offline_probe_learning_validation_only",
        "window_policy": (
            "first_armed_exact_episode_then_mature_5_10_20_30_60m_outcome"
        ),
        "source_quality_gate": (
            "exact_hash_route_session_completed_bar_and_first_signal_episode"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_entry_reversal_sequence_report(
    *,
    target_date: str,
    paired_report: dict[str, Any],
    labels: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    outcome_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate pre-decision reversal states without using outcome as a feature."""

    requests = {
        str(row.get("decision_trace_id") or ""): row
        for row in paired_report.get("requests") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    results = {
        str(row.get("decision_trace_id") or ""): row
        for row in paired_report.get("results") or []
        if isinstance(row, dict)
        and row.get("decision_trace_id")
        and row.get("status") == "pass"
    }
    comparisons = {
        str(row.get("decision_trace_id") or ""): row
        for row in paired_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if isinstance(row, dict)
        and row.get("decision_trace_id")
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    }
    payload_by_request = {
        str(row.get("request_id") or ""): row
        for row in payloads
        if isinstance(row, dict) and row.get("request_id")
    }
    exclusions: Counter[str] = Counter()
    snapshots: list[dict[str, Any]] = []
    for trace_id, comparison in comparisons.items():
        request = requests.get(trace_id)
        result = results.get(trace_id)
        label = label_by_trace.get(trace_id)
        payload_row = payload_by_request.get(trace_id)
        if request is None or result is None or label is None or payload_row is None:
            exclusions["required_join_missing"] += 1
            continue
        context, exclusion = _entry_reversal_snapshot_context(
            request=request,
            payload_row=payload_row,
        )
        if context is None:
            exclusions[exclusion or "snapshot_context_invalid"] += 1
            continue
        context["candidate_action"] = comparison.get("candidate_action")
        context["control_action"] = comparison.get("control_action")
        context["conservative_execution_cost_pct"] = _number(
            (request.get("anticipatory_reversal_analysis") or {})
            .get("execution_cost", {})
            .get("conservative_execution_cost_pct")
        )
        snapshots.append(context)

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for snapshot in snapshots:
        grouped[
            (
                str(snapshot.get("stock_code") or ""),
                str(snapshot.get("effective_venue") or ""),
                str(snapshot.get("session_bucket") or ""),
            )
        ].append(snapshot)
    transitioned: list[dict[str, Any]] = []
    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: str(row.get("captured_at") or ""))
        previous: dict[str, Any] | None = None
        episode_index = 0
        previous_at: datetime | None = None
        for snapshot in group_rows:
            current_at = _parse_ts(snapshot.get("captured_at"))
            if (
                previous_at is None
                or current_at is None
                or (current_at - previous_at).total_seconds()
                > REVERSAL_SEQUENCE_EPISODE_GAP_SEC
            ):
                episode_index += 1
            context = _attach_reversal_transition(snapshot, previous)
            context["episode_id"] = (
                f"reversal-episode-{_sha256((*_reversal_group_key(snapshot), episode_index))[:20]}"
            )
            transitioned.append(context)
            previous = snapshot
            previous_at = current_at

    labeled_transition_rows: list[dict[str, Any]] = []
    for context in transitioned:
        label = label_by_trace.get(str(context.get("decision_trace_id") or ""), {})
        horizon_metrics = label.get("horizon_metrics")
        horizon_metrics = horizon_metrics if isinstance(horizon_metrics, dict) else {}
        outcomes = {
            f"{horizon}m": {
                key: metric.get(key)
                for key in (
                    "mfe_pct",
                    "mae_pct",
                    "end_return_pct",
                    "profit_opportunity_observed",
                    "profit_opportunity_sequence",
                    "profit_opportunity_hit_at",
                    "pre_profit_mae_pct",
                )
            }
            for horizon in REVERSAL_SEQUENCE_HORIZONS_MIN
            if isinstance((metric := horizon_metrics.get(f"{horizon}m")), dict)
        }
        context["outcomes"] = outcomes
        context["outcome_join_key"] = label.get("label_id")
        context["counterfactual_only"] = True
        labeled_transition_rows.append(context)
    evaluation_rows = [
        context
        for context in labeled_transition_rows
        if context.get("candidate_action") == "DROP"
    ]

    cohort_predicates: dict[str, Callable[[dict[str, Any]], bool]] = {
        "all_candidate_drop": lambda row: True,
        "reversal_armed": lambda row: row.get("reversal_armed") is True,
        "reversal_confirmed": lambda row: row.get("reversal_state") == "CONFIRMED",
        "support_flush_armed": lambda row: (
            row.get("reversal_armed") is True
            and (row.get("archetypes") or {}).get("support_flush") is True
        ),
        "trend_pullback_armed": lambda row: (
            row.get("reversal_armed") is True
            and (row.get("archetypes") or {}).get("trend_pullback") is True
        ),
        "continuation_shakeout_armed": lambda row: (
            row.get("reversal_armed") is True
            and (row.get("archetypes") or {}).get("continuation_shakeout") is True
        ),
        "wide_spread_reversal_armed": lambda row: (
            row.get("reversal_armed") is True
            and (row.get("liquidity") or {}).get("wide_spread_observed") is True
        ),
    }
    cohorts: dict[str, Any] = {}
    for cohort_name, predicate in cohort_predicates.items():
        cohort_rows = [row for row in evaluation_rows if predicate(row)]
        first_signal_rows = _first_signal_episode_rows(cohort_rows)
        cohorts[cohort_name] = {
            "row_count": len(cohort_rows),
            "first_signal_episode_count": len(first_signal_rows),
            "row_level": {
                f"{horizon}m": _sequence_horizon_summary(cohort_rows, horizon)
                for horizon in REVERSAL_SEQUENCE_HORIZONS_MIN
            },
            "first_signal_episode": {
                f"{horizon}m": _sequence_horizon_summary(
                    first_signal_rows,
                    horizon,
                )
                for horizon in REVERSAL_SEQUENCE_HORIZONS_MIN
            },
        }
    confirmed_primary = (
        cohorts.get("reversal_confirmed", {})
        .get("first_signal_episode", {})
        .get("20m", {})
    )
    confirmed_ready = bool(
        (confirmed_primary.get("sample_count") or 0) >= 3
        and (confirmed_primary.get("unique_symbol_count") or 0) >= 3
        and (_number(confirmed_primary.get("source_quality_adjusted_ev_pct")) or 0) > 0
    )
    if not requests or not comparisons:
        status = "sequence_source_artifact_missing"
    elif not snapshots:
        status = "sequence_source_quality_blocked"
    elif not evaluation_rows:
        status = "sequence_candidate_drop_cohort_empty"
    elif confirmed_ready:
        status = "sequence_prompt_candidate_review_ready"
    else:
        status = "sequence_hypothesis_keep_collecting"
    clean_rows = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in evaluation_rows
    ]
    return {
        "schema": REVERSAL_SEQUENCE_SCHEMA,
        "context_schema": REVERSAL_SEQUENCE_CONTEXT_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "decision": status,
        "paired_report_status": paired_report.get("status"),
        "paired_prompt_version": (
            ((paired_report.get("requests") or [{}])[0].get("candidate") or {}).get(
                "prompt_version"
            )
            if paired_report.get("requests")
            else None
        ),
        "eligible_snapshot_count": len(snapshots),
        "candidate_drop_sequence_row_count": len(clean_rows),
        "exclusion_counts": dict(exclusions),
        "reversal_state_counts": dict(
            Counter(str(row.get("reversal_state") or "UNKNOWN") for row in clean_rows)
        ),
        "archetype_counts": {
            archetype: sum(
                (row.get("archetypes") or {}).get(archetype) is True
                for row in clean_rows
            )
            for archetype in (
                "support_flush",
                "trend_pullback",
                "continuation_shakeout",
            )
        },
        "transition_policy": {
            "previous_snapshot_max_sec": REVERSAL_SEQUENCE_MAX_PREVIOUS_SEC,
            "episode_gap_sec": REVERSAL_SEQUENCE_EPISODE_GAP_SEC,
            "reference_near_bp": REVERSAL_SEQUENCE_REFERENCE_NEAR_BP,
            "moving_average_near_bp": REVERSAL_SEQUENCE_MA_NEAR_BP,
            "max_price_decline_pct": REVERSAL_SEQUENCE_MAX_PRICE_DECLINE_PCT,
            "outcome_fields_forbidden_during_state_classification": True,
            "wide_spread_role": "observed_execution_risk_not_positive_confirmation",
        },
        "prompt_candidate_review_ready": confirmed_ready,
        "one_share_probe_counterfactual": _build_one_share_probe_counterfactual(
            evaluation_rows
        ),
        "scale_in_counterfactual": _build_scale_in_counterfactual(
            labeled_transition_rows
        ),
        "outcome_source": dict(outcome_source or {}),
        "cohorts": cohorts,
        "rows": clean_rows,
        **REVERSAL_SEQUENCE_CONTRACT,
    }


def _reversal_group_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("stock_code") or ""),
        str(row.get("effective_venue") or ""),
        str(row.get("session_bucket") or ""),
    )


def _default_sources(
    target_date: str, *, include_pipeline: bool = True
) -> dict[str, Any]:
    traces = _load_jsonl(TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl")
    payloads = _load_jsonl(PAYLOAD_DIR / f"ai_decision_payloads_{target_date}.jsonl")
    pending = _load_jsonl(OUTCOME_DIR / f"ai_decision_outcomes_{target_date}.jsonl")
    pipeline_paths: list[Path] = []
    if include_pipeline:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        has_overnight = any(
            _stage(row.get("decision_stage")) == "overnight" for row in pending
        )
        max_offset = PIPELINE_FORWARD_DAYS if has_overnight else 0
        for offset in range(max_offset + 1):
            source_date = (target + timedelta(days=offset)).isoformat()
            pipeline_paths.append(
                existing_or_gzip_path(
                    PIPELINE_DIR / f"pipeline_events_{source_date}.jsonl"
                )
            )
    return {
        "traces": traces,
        "payloads": payloads,
        "pending": pending,
        "pipeline": [],
        "pipeline_paths": pipeline_paths,
    }


def _parse_control_prompt_versions(values: list[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for value in values:
        endpoint, separator, version = str(value or "").partition("=")
        endpoint = endpoint.strip()
        version = version.strip()
        if not separator or not endpoint or not version:
            raise ValueError("control_prompt_version_must_be_ENDPOINT_equals_VERSION")
        previous = selected.get(endpoint)
        if previous and previous != version:
            raise ValueError(f"control_prompt_version_conflict:{endpoint}")
        selected[endpoint] = version
    return selected


def _candidate_execution_setup_state(row: dict[str, Any]) -> str:
    evidence = row.get("entry_setup_evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    state = str(evidence.get("setup_state") or "OTHER").strip().upper()
    return state if state in {"READY", "WAIT_CONFIRMATION"} else "OTHER"


def _checkpoint_setup_state_counts(
    requests: list[dict[str, Any]],
) -> dict[str, int]:
    return dict(Counter(_candidate_execution_setup_state(row) for row in requests))


def select_pending_candidate_execution_requests(
    pending_requests: list[dict[str, Any]],
    *,
    max_new_requests: int,
    previously_attempted_pair_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select an outcome-blind, symbol-diverse offline execution checkpoint.

    Previously attempted rows remain the retry set and consume the distinct-call
    quota.  This prevents a wrapper-level retry from advancing to a second batch
    of symbols after another venue fails.
    """

    rows = [row for row in pending_requests if isinstance(row, dict)]
    limit = int(max_new_requests)
    attempted_ids = {
        str(value) for value in (previously_attempted_pair_ids or set()) if str(value)
    }
    retry_rows = [
        row for row in rows if str(row.get("paired_replay_id") or "") in attempted_ids
    ]
    unseen_rows = [
        row
        for row in rows
        if str(row.get("paired_replay_id") or "") not in attempted_ids
    ]
    remaining_new_quota = (
        max(0, limit - len(attempted_ids)) if limit > 0 else len(unseen_rows)
    )
    if limit <= 0 or remaining_new_quota >= len(unseen_rows):
        selected_new = unseen_rows
        selected = [*retry_rows, *selected_new]
        distinct_execution_count = len(attempted_ids) + len(selected_new)
        return selected, {
            "policy": "complete_eligible_census",
            "outcome_blind": True,
            "eligible_pending_count": len(rows),
            "previously_attempted_distinct_count": len(attempted_ids),
            "retry_selected_count": len(retry_rows),
            "selected_execution_count": len(selected),
            "selected_new_count": len(selected_new),
            "deferred_new_count": 0,
            "selected_unique_symbol_count": len(
                {
                    _normalize_stock_code(row.get("stock_code"))
                    for row in selected
                    if _normalize_stock_code(row.get("stock_code"))
                }
            ),
            "distinct_execution_count": distinct_execution_count,
            "distinct_execution_cap": limit if limit > 0 else None,
            "distinct_execution_cap_pass": bool(
                limit <= 0 or distinct_execution_count <= limit
            ),
            "contract_pass": bool(limit <= 0 or distinct_execution_count <= limit),
        }

    def rank(row: dict[str, Any]) -> str:
        return _sha256(
            {
                "paired_replay_id": row.get("paired_replay_id"),
                "decision_trace_id": row.get("decision_trace_id"),
                "stock_code": _normalize_stock_code(row.get("stock_code")),
                "stage": row.get("stage"),
                "effective_venue": _venue(row.get("effective_venue")),
                "session_bucket": _session(row.get("session_bucket")),
            }
        )

    def select_diverse(
        candidates: list[dict[str, Any]],
        quota: int,
        *,
        already_selected_ids: set[str],
        already_selected_symbols: set[str],
    ) -> list[dict[str, Any]]:
        by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in candidates:
            pair_id = str(row.get("paired_replay_id") or "")
            if pair_id in already_selected_ids:
                continue
            symbol = _normalize_stock_code(row.get("stock_code")) or "UNKNOWN"
            by_symbol[symbol].append(row)
        for symbol_rows in by_symbol.values():
            symbol_rows.sort(key=rank)
        symbol_order = sorted(
            by_symbol,
            key=lambda symbol: (
                symbol in already_selected_symbols,
                _sha256(
                    {
                        "policy": CANDIDATE_EXECUTION_SELECTION_POLICY,
                        "symbol": symbol,
                    }
                ),
            ),
        )
        picked: list[dict[str, Any]] = []
        depth = 0
        while len(picked) < quota:
            added = False
            for symbol in symbol_order:
                symbol_rows = by_symbol[symbol]
                if depth < len(symbol_rows):
                    picked.append(symbol_rows[depth])
                    already_selected_ids.add(
                        str(symbol_rows[depth].get("paired_replay_id") or "")
                    )
                    already_selected_symbols.add(symbol)
                    added = True
                    if len(picked) >= quota:
                        break
            if not added:
                break
            depth += 1
        return picked

    # The checkpoint is still outcome-blind. It deliberately spends more of a
    # bounded provider budget on decision-time READY evidence so an INVALID-heavy
    # symbol census cannot make a feasible promotion/exploration sample appear
    # impossible. WAIT_CONFIRMATION remains represented for transition learning.
    stratum_weights = {"READY": 0.60, "WAIT_CONFIRMATION": 0.30, "OTHER": 0.10}
    raw_stratum_quotas = {
        key: remaining_new_quota * weight for key, weight in stratum_weights.items()
    }
    stratum_quotas = {key: int(value) for key, value in raw_stratum_quotas.items()}
    quota_remainder_order = sorted(
        stratum_weights,
        key=lambda key: (
            -(raw_stratum_quotas[key] - stratum_quotas[key]),
            {"READY": 0, "WAIT_CONFIRMATION": 1, "OTHER": 2}[key],
        ),
    )
    for key in quota_remainder_order[
        : remaining_new_quota - sum(stratum_quotas.values())
    ]:
        stratum_quotas[key] += 1
    selected_new: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_symbols: set[str] = set()
    for stratum in ("READY", "WAIT_CONFIRMATION", "OTHER"):
        selected_new.extend(
            select_diverse(
                [
                    row
                    for row in unseen_rows
                    if _candidate_execution_setup_state(row) == stratum
                ],
                stratum_quotas[stratum],
                already_selected_ids=selected_ids,
                already_selected_symbols=selected_symbols,
            )
        )
    if len(selected_new) < remaining_new_quota:
        selected_new.extend(
            select_diverse(
                unseen_rows,
                remaining_new_quota - len(selected_new),
                already_selected_ids=selected_ids,
                already_selected_symbols=selected_symbols,
            )
        )
    selected = [*retry_rows, *selected_new]
    distinct_execution_count = len(attempted_ids) + len(selected_new)
    cap_pass = bool(limit <= 0 or distinct_execution_count <= limit)
    return selected, {
        "policy": CANDIDATE_EXECUTION_SELECTION_POLICY,
        "outcome_blind": True,
        "selection_fields": [
            "paired_replay_id",
            "decision_trace_id",
            "stock_code",
            "stage",
            "effective_venue",
            "session_bucket",
            "entry_setup_evidence.setup_state",
        ],
        "forbidden_selection_fields": [
            "outcome_return_pct",
            "outcome_mfe_pct",
            "outcome_mae_pct",
            "first_hit",
            "profit_opportunity_observed",
        ],
        "eligible_pending_count": len(rows),
        "previously_attempted_distinct_count": len(attempted_ids),
        "retry_selected_count": len(retry_rows),
        "selected_execution_count": len(selected),
        "selected_new_count": len(selected_new),
        "deferred_new_count": len(unseen_rows) - len(selected_new),
        "selected_unique_symbol_count": len(
            {
                _normalize_stock_code(row.get("stock_code"))
                for row in selected
                if _normalize_stock_code(row.get("stock_code"))
            }
        ),
        "selected_setup_state_counts": dict(
            Counter(_candidate_execution_setup_state(row) for row in selected_new)
        ),
        "setup_state_target_weights": stratum_weights,
        "distinct_execution_count": distinct_execution_count,
        "distinct_execution_cap": limit if limit > 0 else None,
        "distinct_execution_cap_pass": cap_pass,
        "contract_pass": bool(
            cap_pass and len(selected_new) == min(remaining_new_quota, len(unseen_rows))
        ),
    }


def _valid_checkpoint_attempted_pair_ids(
    existing_report: dict[str, Any],
    *,
    valid_pair_ids: set[str],
    selection_contract_pass: bool,
) -> set[str]:
    """Prevent a stale selection policy from consuming the new call quota."""

    if not selection_contract_pass:
        return set()
    return {
        paired_replay_id
        for row in existing_report.get("requests") or []
        if isinstance(row, dict)
        and (paired_replay_id := str(row.get("paired_replay_id") or ""))
        and paired_replay_id in valid_pair_ids
    }


_REATTRIBUTION_REQUEST_IDENTITY_FIELDS = (
    "payload_sha256",
    "candidate_input_sha256",
    "exact_payload_analysis_sha256",
    "anticipatory_reversal_analysis_sha256",
    "entry_setup_evidence_sha256",
)

DETAILED_PREPARED_REQUEST_SNAPSHOT_SCHEMA = "ai_detailed_prepared_request_snapshot_v1"

_REATTRIBUTION_CORE_INVARIANT_FIELDS = (
    "status",
    "request_count",
    "result_count",
    "paired_comparable_count",
    "control_source_quality_adjusted_ev_pct",
    "candidate_source_quality_adjusted_ev_pct",
    "candidate_exposure_decision_count",
    "candidate_probe_arm_decision_count",
    "candidate_error_taxonomy_counts",
    "promotion_report_integrity_pass",
)


def _detailed_request_reattribution_identity(
    request: dict[str, Any],
) -> dict[str, Any]:
    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    return {
        **{
            field: request.get(field)
            for field in _REATTRIBUTION_REQUEST_IDENTITY_FIELDS
        },
        "candidate_prompt_version": candidate.get("prompt_version"),
        "candidate_prompt_sha256": candidate.get("system_prompt_sha256"),
        "candidate_contract_sha256": candidate.get("contract_sha256"),
        "candidate_model": candidate.get("model"),
    }


def _reattribution_core_invariant_sha256(report: dict[str, Any]) -> str:
    return _sha256(
        {field: report.get(field) for field in _REATTRIBUTION_CORE_INVARIANT_FIELDS}
    )


def rematerialize_detailed_replay_attribution(
    *,
    target_date: str,
    effective_venue: str,
    session_bucket: str,
    candidate_prompt_version: str,
    prepared_request_snapshot_path: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    """Rebuild attribution from immutable stored labels and candidate results.

    This path performs no price REST request and no candidate model call. It is
    intentionally fail-closed when current request construction no longer
    matches the stored evaluated request/result identities.
    """

    output_path = detailed_paired_path(
        target_date,
        candidate_prompt_version=candidate_prompt_version,
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    existing_report = _load_json(output_path)
    stored_label_path = label_report_path(target_date)
    stored_label_report = _load_json(stored_label_path)
    errors: list[str] = []
    if existing_report.get("schema") != DETAILED_PAIRED_SCHEMA:
        errors.append("existing_detailed_schema_invalid")
    if existing_report.get("target_date") != target_date:
        errors.append("existing_detailed_target_date_mismatch")
    cohort_filter = existing_report.get("cohort_filter")
    cohort_filter = cohort_filter if isinstance(cohort_filter, dict) else {}
    if _venue(cohort_filter.get("effective_venue")) != _venue(effective_venue):
        errors.append("existing_detailed_venue_mismatch")
    if _session(cohort_filter.get("session_bucket")) != _session(session_bucket):
        errors.append("existing_detailed_session_mismatch")
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
        ("promotion_report_integrity_pass", True),
    ):
        if existing_report.get(field) is not expected:
            errors.append(f"existing_detailed_{field}_invalid")
    existing_selection = existing_report.get("candidate_execution_selection")
    if not (
        isinstance(existing_selection, dict)
        and existing_selection.get("outcome_blind") is True
        and existing_selection.get("contract_pass") is True
    ):
        errors.append("existing_candidate_execution_selection_invalid")
    existing_requests = existing_report.get("requests")
    existing_results = existing_report.get("results")
    if not isinstance(existing_requests, list) or not existing_requests:
        errors.append("existing_evaluated_requests_missing")
        existing_requests = []
    if not isinstance(existing_results, list) or not existing_results:
        errors.append("existing_candidate_results_missing")
        existing_results = []
    if stored_label_report.get("schema") != LABEL_REPORT_SCHEMA:
        errors.append("stored_label_schema_invalid")
    if stored_label_report.get("target_date") != target_date:
        errors.append("stored_label_target_date_mismatch")
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if stored_label_report.get(field) is not expected:
            errors.append(f"stored_label_{field}_invalid")
    labels = stored_label_report.get("labels")
    if not isinstance(labels, list) or not labels:
        errors.append("stored_labels_missing")
        labels = []
    labels = _filter_rows_for_cohort(
        labels,
        effective_venue=effective_venue,
        session_bucket=session_bucket,
    )
    if not labels:
        errors.append("stored_cohort_labels_missing")
    if errors:
        raise RuntimeError("offline_reattribution_source_invalid:" + ",".join(errors))

    prepared_snapshot: dict[str, Any] = {}
    if prepared_request_snapshot_path is not None:
        prepared_snapshot = _load_json(prepared_request_snapshot_path)
        snapshot_errors: list[str] = []
        if prepared_snapshot.get("schema") != DETAILED_PREPARED_REQUEST_SNAPSHOT_SCHEMA:
            snapshot_errors.append("schema_invalid")
        if prepared_snapshot.get("target_date") != target_date:
            snapshot_errors.append("target_date_mismatch")
        if (
            prepared_snapshot.get("candidate_prompt_version")
            != candidate_prompt_version
        ):
            snapshot_errors.append("candidate_prompt_version_mismatch")
        snapshot_cohort = prepared_snapshot.get("cohort_filter")
        snapshot_cohort = snapshot_cohort if isinstance(snapshot_cohort, dict) else {}
        if _venue(snapshot_cohort.get("effective_venue")) != _venue(effective_venue):
            snapshot_errors.append("venue_mismatch")
        if _session(snapshot_cohort.get("session_bucket")) != _session(session_bucket):
            snapshot_errors.append("session_mismatch")
        for field, expected in (
            ("runtime_effect", False),
            ("allowed_runtime_apply", False),
            ("actual_order_submitted", False),
            ("broker_order_forbidden", True),
        ):
            if prepared_snapshot.get(field) is not expected:
                snapshot_errors.append(f"{field}_invalid")
        if prepared_snapshot.get("stored_label_report_content_sha256") != _sha256(
            stored_label_report
        ):
            snapshot_errors.append("stored_label_report_hash_mismatch")
        snapshot_content_sha256 = _sha256(prepared_snapshot)
        prior_reattribution = existing_report.get("reattribution_provenance")
        prior_reattribution = (
            prior_reattribution if isinstance(prior_reattribution, dict) else {}
        )
        source_report_hash = prepared_snapshot.get("source_report_content_sha256")
        source_report_hash_matches = source_report_hash == _sha256(existing_report)
        idempotent_source_match = bool(
            prior_reattribution.get("source_report_content_sha256")
            == source_report_hash
            and prior_reattribution.get("prepared_request_snapshot_content_sha256")
            == snapshot_content_sha256
            and prior_reattribution.get("historical_core_invariant_sha256")
            == _reattribution_core_invariant_sha256(existing_report)
        )
        if not source_report_hash_matches and not idempotent_source_match:
            snapshot_errors.append("source_report_hash_mismatch")
        source_code_commit = str(
            prepared_snapshot.get("source_code_commit") or ""
        ).strip()
        if re.fullmatch(r"[0-9a-f]{40}", source_code_commit) is None:
            snapshot_errors.append("source_code_commit_invalid")
        prepared_requests = prepared_snapshot.get("prepared_requests")
        if not isinstance(prepared_requests, list) or not prepared_requests:
            snapshot_errors.append("prepared_requests_missing")
            prepared_requests = []
        if prepared_snapshot.get("prepared_request_count") != len(prepared_requests):
            snapshot_errors.append("prepared_request_count_mismatch")
        snapshot_pass_count = sum(
            (request.get("sample_floor") or {}).get("pass") is True
            for request in prepared_requests
            if isinstance(request, dict)
        )
        if prepared_snapshot.get("sample_floor_pass_count") != snapshot_pass_count:
            snapshot_errors.append("sample_floor_pass_count_mismatch")
        existing_prepared_count = existing_report.get("prepared_request_count")
        if existing_prepared_count is not None and existing_prepared_count != len(
            prepared_requests
        ):
            snapshot_errors.append("existing_prepared_request_count_mismatch")
        existing_eligible_count = existing_selection.get("eligible_request_count")
        if (
            existing_eligible_count is not None
            and existing_eligible_count != snapshot_pass_count
        ):
            snapshot_errors.append("existing_eligible_request_count_mismatch")
        if snapshot_errors:
            raise RuntimeError(
                "offline_reattribution_snapshot_invalid:" + ",".join(snapshot_errors)
            )
    else:
        sources = _default_sources(target_date, include_pipeline=False)
        traces = _filter_rows_for_cohort(
            sources["traces"],
            effective_venue=effective_venue,
            session_bucket=session_bucket,
        )
        prepared_requests = prepare_paired_replay_requests(
            control_manifest=_load_json(
                control_path(
                    target_date,
                    effective_venue=effective_venue,
                    session_bucket=session_bucket,
                )
            ),
            traces=traces,
            payloads=sources["payloads"],
            labels=labels,
        )
        prepared_requests = prepare_detailed_paired_replay_requests(
            prepared_requests,
            candidate_prompt_version=candidate_prompt_version,
        )
    prepared_errors: list[str] = []
    if any(not isinstance(request, dict) for request in prepared_requests):
        prepared_errors.append("request_not_object")
    prepared_pair_ids = [
        str(request.get("paired_replay_id") or "")
        for request in prepared_requests
        if isinstance(request, dict)
    ]
    if any(not pair_id for pair_id in prepared_pair_ids):
        prepared_errors.append("pair_id_missing")
    if len(prepared_pair_ids) != len(set(prepared_pair_ids)):
        prepared_errors.append("pair_id_duplicate")
    if any(
        _stage(request.get("stage")) == "entry"
        and (request.get("candidate") or {}).get("prompt_version")
        != f"{candidate_prompt_version}_entry"
        for request in prepared_requests
        if isinstance(request, dict)
    ):
        prepared_errors.append("candidate_version_mismatch")
    if any(
        _venue(request.get("effective_venue")) != _venue(effective_venue)
        or _session(request.get("session_bucket")) != _session(session_bucket)
        for request in prepared_requests
        if isinstance(request, dict)
    ):
        prepared_errors.append("cohort_mismatch")
    if prepared_errors:
        raise RuntimeError(
            "offline_reattribution_prepared_invalid:" + ",".join(prepared_errors)
        )
    current_by_pair = {
        str(request.get("paired_replay_id") or ""): request
        for request in prepared_requests
        if request.get("paired_replay_id")
    }
    identity_errors: list[str] = []
    evaluated_pair_ids: set[str] = set()
    for request in existing_requests:
        if not isinstance(request, dict):
            identity_errors.append("existing_request_not_object")
            continue
        pair_id = str(request.get("paired_replay_id") or "")
        current = current_by_pair.get(pair_id)
        if not pair_id or current is None:
            identity_errors.append(f"evaluated_pair_missing_current:{pair_id or '-'}")
            continue
        evaluated_pair_ids.add(pair_id)
        stored_identity = _detailed_request_reattribution_identity(request)
        current_identity = _detailed_request_reattribution_identity(current)
        mismatched_fields = [
            field
            for field in stored_identity
            if stored_identity.get(field) != current_identity.get(field)
        ]
        if mismatched_fields:
            identity_errors.append(
                "evaluated_request_identity_mismatch:"
                f"{pair_id}:{'|'.join(mismatched_fields)}"
            )
    result_pair_ids = {
        str(result.get("paired_replay_id") or "")
        for result in existing_results
        if isinstance(result, dict) and result.get("paired_replay_id")
    }
    if result_pair_ids != evaluated_pair_ids:
        identity_errors.append("evaluated_request_result_pair_set_mismatch")
    if len(existing_requests) != len(evaluated_pair_ids):
        identity_errors.append("evaluated_request_count_mismatch")
    if len(existing_results) != len(evaluated_pair_ids):
        identity_errors.append("evaluated_result_count_mismatch")
    if identity_errors:
        raise RuntimeError(
            "offline_reattribution_identity_invalid:" + ",".join(identity_errors[:20])
        )

    # Preserve every historical decision/EV field. Re-running the current
    # composer over an older prompt result would silently reinterpret that
    # result under today's semantics. Reattribution may only add observation
    # sections computed from the immutable stored comparison rows.
    historical_core_invariant_sha256 = _reattribution_core_invariant_sha256(
        existing_report
    )
    rebuilt = deepcopy(existing_report)
    comparable_rows = rebuilt.get("paired_comparisons")
    if not isinstance(comparable_rows, list):
        raise RuntimeError("offline_reattribution_source_invalid:paired_rows_missing")
    transition_observations = _prepared_entry_transition_observations(
        prepared_requests=prepared_requests,
        comparable_rows=comparable_rows,
    )
    waiting_probe_arm_rows = [
        row
        for row in comparable_rows
        if isinstance(row, dict)
        and row.get("candidate_probe_armed") is True
        and row.get("candidate_exposure_selected") is not True
    ]
    probe_arm_transition_summary = _attach_wait_transition_continuity(
        waiting_rows=waiting_probe_arm_rows,
        observations=transition_observations,
        field_prefix="entry_probe_arm_continuity",
        contract_version="entry_probe_arm_next_exact_transition_v1",
        observation_source="full_prepared_exact_request_census",
    )
    rebuilt["entry_opportunity_funnel"] = _entry_opportunity_funnel_attribution(
        labels=labels,
        prepared_requests=prepared_requests,
        comparable_rows=comparable_rows,
        results=existing_results,
        candidate_execution_requested=bool(
            existing_results or existing_selection is not None
        ),
    )
    rebuilt["entry_probe_arm_continuity"] = {
        "schema": "entry_probe_arm_continuity_v1",
        "metric_role": "funnel_count",
        "decision_authority": "offline_sequential_continuity_attribution_only",
        "window_policy": (
            "same_symbol_venue_session_full_prepared_exact_request_census_300s"
        ),
        "sample_floor": "one_waiting_probe_arm_starts_observation",
        "primary_decision_metric": "ready_followup_observed_rate_pct",
        "source_quality_gate": "exact_v2_same_route_prepared_request_census",
        **probe_arm_transition_summary,
        "forbidden_uses": [
            "treat_waiting_probe_arm_as_submitted_order",
            "treat_candidate_budget_defer_as_ai_rejection",
            "standalone_live_prompt_promotion",
            "provider_model_threshold_price_quantity_or_cap_change",
            "broker_or_safety_guard_bypass",
            "bot_restart",
        ],
    }
    rebuilt["entry_lifecycle_replay"] = _entry_lifecycle_replay_attribution(
        comparable_rows,
        target_date=target_date,
        probe_arm_transition_summary=probe_arm_transition_summary,
    )
    invariant_mismatches = [
        field
        for field in _REATTRIBUTION_CORE_INVARIANT_FIELDS
        if rebuilt.get(field) != existing_report.get(field)
    ]
    if invariant_mismatches:
        raise RuntimeError(
            "offline_reattribution_core_metric_drift:" + ",".join(invariant_mismatches)
        )
    if (
        _reattribution_core_invariant_sha256(rebuilt)
        != historical_core_invariant_sha256
    ):
        raise RuntimeError("offline_reattribution_core_metric_hash_drift")
    rebuilt["reattribution_provenance"] = {
        "schema": "ai_detailed_replay_reattribution_provenance_v1",
        "source_report_path": str(output_path),
        "source_report_content_sha256": (
            prepared_snapshot.get("source_report_content_sha256")
            if prepared_snapshot
            else _sha256(existing_report)
        ),
        "stored_label_report_path": str(stored_label_path),
        "stored_label_report_content_sha256": _sha256(stored_label_report),
        "prepared_request_source": (
            "pinned_historical_snapshot"
            if prepared_request_snapshot_path is not None
            else "current_source_reconstruction"
        ),
        "prepared_request_snapshot_path": (
            str(prepared_request_snapshot_path)
            if prepared_request_snapshot_path is not None
            else None
        ),
        "prepared_request_snapshot_content_sha256": (
            _sha256(prepared_snapshot) if prepared_snapshot else None
        ),
        "prepared_request_source_code_commit": (
            prepared_snapshot.get("source_code_commit") if prepared_snapshot else None
        ),
        "source_generated_at": existing_report.get("generated_at"),
        "reattributed_at": datetime.now(KST).isoformat(),
        "prepared_request_count": len(prepared_requests),
        "evaluated_request_count": len(existing_requests),
        "candidate_result_count": len(existing_results),
        "historical_core_invariant_sha256": historical_core_invariant_sha256,
        "historical_decision_metrics_preserved": True,
        "historical_composer_reexecution_performed": False,
        "price_rest_request_performed": False,
        "candidate_model_call_performed": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return rebuilt, output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build offline exact AI decision-quality artifacts."
    )
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--mode",
        choices=(
            "control",
            "postclose",
            "mature",
            "baseline",
            "paired",
            "detailed",
            "correlation",
            "recovery",
            "reversal_sequence",
            "reattribute",
        ),
        required=True,
    )
    parser.add_argument("--as-of")
    parser.add_argument(
        "--outcome-price-source",
        choices=("auto", "pipeline", "kiwoom_completed_1m"),
        default="auto",
        help=(
            "Offline forward-price source (default: auto). Auto prefers "
            "route-qualified Kiwoom completed 1m rows and retains contracted "
            "pipeline rows as a fallback. Kiwoom reuses only the valid shared "
            "token and never issues a new token."
        ),
    )
    parser.add_argument(
        "--execute-candidate",
        action="store_true",
        help="Execute sample-floor-ready Prompt V2 candidates offline.",
    )
    parser.add_argument(
        "--stage",
        choices=("entry", "holding"),
        help=(
            "Restrict paired execution to one stage and write a stage-specific "
            "artifact. Valid only with --mode paired. Entry-price Bedrock replay "
            "is owned by ai_stage_coverage_replay."
        ),
    )
    parser.add_argument(
        "--venue",
        choices=("KRX", "NXT", "SOR", "PREMARKET_KRX_LIKE"),
        help=(
            "Restrict control/paired/detailed artifacts to one effective venue. "
            "The filter changes offline artifact scope only."
        ),
    )
    parser.add_argument(
        "--session-bucket",
        choices=(
            "PREMARKET_KRX_LIKE",
            "NXT_PREMARKET",
            "KRX_REGULAR",
            "NXT_REGULAR_OVERLAP",
            "NXT_AFTERMARKET",
        ),
        help=(
            "Restrict control/paired/detailed artifacts to one session bucket. "
            "Use with --venue for promotion-grade cohort isolation."
        ),
    )
    parser.add_argument("--candidate-timeout-sec", type=float, default=45.0)
    parser.add_argument("--candidate-workers", type=int, default=4)
    parser.add_argument(
        "--candidate-max-new-requests",
        type=int,
        default=0,
        help=(
            "Optional offline checkpoint limit for newly executed requests. "
            "Zero executes every pending request; existing valid results are reused."
        ),
    )
    parser.add_argument(
        "--control-prompt-version",
        action="append",
        default=[],
        metavar="ENDPOINT=VERSION",
        help=(
            "Freeze only the named natural runtime prompt version for an endpoint. "
            "Repeat per endpoint; valid only in control mode."
        ),
    )
    parser.add_argument(
        "--detailed-candidate-version",
        choices=(
            DECISION_QUALITY_DETAILED_PROMPT_VERSION,
            DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION,
            DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION,
            DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION,
            DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
            DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
            DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
            DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
            DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
        ),
        default=DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    )
    parser.add_argument(
        "--candidate-model",
        default="",
        help=(
            "Offline detailed-replay model override. It creates a separate "
            "model-comparison artifact and never changes runtime routing."
        ),
    )
    parser.add_argument(
        "--outcome-recovery-report",
        action="append",
        default=[],
        type=Path,
        help=(
            "Explicit prior same-date paired report whose route-qualified "
            "same-trace primary outcome owns recovery from a retained raw-window "
            "gap. It replaces a conflicting regenerated label for that trace. "
            "Valid only in detailed offline replay; exact payloads are never "
            "reconstructed from the report."
        ),
    )
    parser.add_argument(
        "--prepared-request-snapshot",
        type=Path,
        help=(
            "Hash-pinned historical full prepared-request census. Valid only "
            "with --mode reattribute when current request construction drifted."
        ),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.execute_candidate and (
        args.mode not in {"paired", "detailed"} or not args.write
    ):
        parser.error("--execute-candidate requires --mode paired|detailed --write")
    if args.stage and args.mode != "paired":
        parser.error("--stage requires --mode paired")
    if (args.venue or args.session_bucket) and args.mode not in {
        "control",
        "paired",
        "detailed",
        "reattribute",
    }:
        parser.error(
            "--venue/--session-bucket require "
            "--mode control|paired|detailed|reattribute"
        )
    if args.session_bucket and not args.venue:
        parser.error("--session-bucket requires --venue")
    if (
        args.mode not in {"detailed", "reattribute"}
        and args.detailed_candidate_version != DECISION_QUALITY_DETAILED_PROMPT_VERSION
    ):
        parser.error(
            "--detailed-candidate-version requires --mode detailed|reattribute"
        )
    if args.candidate_model and args.mode != "detailed":
        parser.error("--candidate-model requires --mode detailed")
    if args.candidate_model and not args.execute_candidate:
        parser.error("--candidate-model requires --execute-candidate")
    if args.outcome_recovery_report and args.mode != "detailed":
        parser.error("--outcome-recovery-report requires --mode detailed")
    if args.prepared_request_snapshot and args.mode != "reattribute":
        parser.error("--prepared-request-snapshot requires --mode reattribute")
    if args.mode == "reattribute" and not (args.venue and args.session_bucket):
        parser.error("--mode reattribute requires --venue and --session-bucket")
    if args.candidate_max_new_requests < 0:
        parser.error("--candidate-max-new-requests must be zero or positive")
    if args.candidate_max_new_requests and not args.execute_candidate:
        parser.error("--candidate-max-new-requests requires --execute-candidate")
    if args.mode != "control" and args.control_prompt_version:
        parser.error("--control-prompt-version requires --mode control")
    try:
        selected_control_prompt_versions = _parse_control_prompt_versions(
            args.control_prompt_version
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.mode == "reattribute":
        report, path = rematerialize_detailed_replay_attribution(
            target_date=args.date,
            effective_venue=args.venue,
            session_bucket=args.session_bucket,
            candidate_prompt_version=args.detailed_candidate_version,
            prepared_request_snapshot_path=args.prepared_request_snapshot,
        )
        if args.write:
            _atomic_write_json(path, report)
        print(
            json.dumps(
                {
                    "status": "detailed_replay_reattribution_complete",
                    "artifact_path": str(path),
                    "target_date": args.date,
                    "cohort_filter": report.get("cohort_filter"),
                    "entry_opportunity_funnel": report.get("entry_opportunity_funnel"),
                    "entry_probe_arm_continuity": report.get(
                        "entry_probe_arm_continuity"
                    ),
                    "entry_lifecycle_replay": report.get("entry_lifecycle_replay"),
                    "reattribution_provenance": report.get("reattribution_provenance"),
                },
                ensure_ascii=False,
            )
        )
        return 0
    sources = _default_sources(
        args.date,
        # Pipeline lifecycle rows own decision-to-order/fill correlation even
        # when forward prices come from route-qualified completed candles.
        include_pipeline=args.mode != "control",
    )
    if args.venue or args.session_bucket:
        sources["traces"] = _filter_rows_for_cohort(
            sources["traces"],
            effective_venue=args.venue,
            session_bucket=args.session_bucket,
        )
        sources["pending"] = _filter_rows_for_cohort(
            sources["pending"],
            effective_venue=args.venue,
            session_bucket=args.session_bucket,
        )
    promotion, promotion_artifact_path, promotion_source_date = (
        load_promotion_for_target_date(args.date)
    )
    if args.mode == "control":
        signature_traces = [
            trace
            for trace in sources["traces"]
            if _trace_endpoint(trace) not in selected_control_prompt_versions
            or str(trace.get("prompt_version") or "")
            == selected_control_prompt_versions.get(_trace_endpoint(trace))
        ]
        selected_control_signatures = _latest_exact_control_signatures(
            promotion=promotion,
            traces=signature_traces,
            payloads=sources["payloads"],
        )
        report = build_control_manifest(
            target_date=args.date,
            promotion=promotion,
            traces=sources["traces"],
            payloads=sources["payloads"],
            control_prompt_versions=selected_control_prompt_versions,
            control_signatures=selected_control_signatures,
            promotion_artifact_path=promotion_artifact_path,
            promotion_source_date=promotion_source_date,
        )
        path = control_path(
            args.date,
            effective_venue=args.venue,
            session_bucket=args.session_bucket,
        )
    else:
        as_of = _parse_ts(args.as_of) or datetime.now(KST)
        pending_decision_times = [
            timestamp
            for row in sources["pending"]
            if (timestamp := _parse_ts(row.get("decision_ts"))) is not None
        ]
        pipeline_window_start = (
            min(pending_decision_times) if pending_decision_times else None
        )
        pipeline_window_end = (
            max(pending_decision_times)
            + timedelta(
                days=PIPELINE_FORWARD_DAYS,
                minutes=max(HORIZONS_MIN),
            )
            if pending_decision_times
            and any(
                _stage(row.get("decision_stage")) == "overnight"
                for row in sources["pending"]
            )
            else (
                max(pending_decision_times) + timedelta(minutes=max(HORIZONS_MIN))
                if pending_decision_times
                else None
            )
        )
        pipeline_stock_codes = {
            code
            for row in sources["pending"]
            if (code := _normalize_stock_code(row.get("stock_code")))
        }
        pipeline_rows = (
            row for path in sources["pipeline_paths"] for row in _iter_jsonl(path)
        )
        pipeline_prices, lifecycle = load_pipeline_price_and_lifecycle_rows(
            pipeline_rows,
            stock_codes=pipeline_stock_codes,
            window_start=pipeline_window_start,
            window_end=pipeline_window_end,
        )
        prices = list(pipeline_prices)
        effective_outcome_price_source = "pipeline"
        price_source_provenance: list[dict[str, Any]] = []
        if args.outcome_price_source in {"auto", "kiwoom_completed_1m"}:
            from src.utils import kiwoom_utils

            token = kiwoom_utils.get_cached_kiwoom_token()
            source_route_labels = annotate_primary_cohort_eligibility(
                labels=sources["pending"],
                traces=sources["traces"],
                payloads=sources["payloads"],
                promotion=promotion,
            )
            source_route_labels = [
                row
                for row in source_route_labels
                if row.get("primary_cohort_eligible") is True
            ]

            def fetch_kiwoom_completed(
                _stock_code: str, request_code: str
            ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
                if not token:
                    return [], {"fetch_error": "cached_token_unavailable"}
                return kiwoom_utils.get_minute_candles_ka10080_with_meta(
                    token,
                    request_code,
                    limit=500,
                    explicit_request_code=True,
                    base_dt=args.date.replace("-", ""),
                )

            (
                kiwoom_prices,
                price_source_provenance,
            ) = load_kiwoom_completed_minute_price_rows(
                target_date=args.date,
                labels=source_route_labels,
                as_of=as_of,
                fetcher=fetch_kiwoom_completed,
            )
            if args.outcome_price_source == "kiwoom_completed_1m":
                prices = kiwoom_prices
                effective_outcome_price_source = "kiwoom_completed_1m"
            elif kiwoom_prices:
                prices, pipeline_price_rows_suppressed = (
                    merge_preferred_outcome_price_rows(
                        kiwoom_prices,
                        pipeline_prices,
                    )
                )
                price_source_provenance.append(
                    {
                        "source": "pipeline_fallback_merge",
                        "retained_count": len(prices) - len(kiwoom_prices),
                        "suppressed_same_route_minute_count": (
                            pipeline_price_rows_suppressed
                        ),
                        "source_quality_status": "pass_primary_precedence_applied",
                    }
                )
                effective_outcome_price_source = (
                    "kiwoom_completed_1m_with_pipeline_fallback"
                )
            else:
                effective_outcome_price_source = "pipeline_fallback"
        labels = mature_outcome_labels(
            pending_labels=sources["pending"],
            price_rows=prices,
            lifecycle_rows=lifecycle,
            as_of=as_of,
        )
        labels = annotate_primary_cohort_eligibility(
            labels=labels,
            traces=sources["traces"],
            payloads=sources["payloads"],
            promotion=promotion,
        )
        label_report = {
            "schema": LABEL_REPORT_SCHEMA,
            "target_date": args.date,
            "generated_at": datetime.now(KST).isoformat(),
            "status": (
                "mature_label_rows_available"
                if any(row["label_status"] in {"partial", "mature"} for row in labels)
                else "partial_horizons_keep_maturing"
            ),
            "summary": dict(Counter(row["label_status"] for row in labels)),
            "outcome_price_source": effective_outcome_price_source,
            "outcome_price_source_requested": args.outcome_price_source,
            "price_source_provenance": price_source_provenance,
            "outcome_as_of": as_of.isoformat(),
            "labels": labels,
            **OFFLINE_CONTRACT,
        }
        if args.mode == "mature":
            report = label_report
            path = label_report_path(args.date)
        elif args.mode == "postclose":
            materialization = build_daily_materialization_reports(
                target_date=args.date,
                promotion=promotion,
                traces=sources["traces"],
                payloads=sources["payloads"],
                labels=labels,
                label_report=label_report,
                outcome_price_source=effective_outcome_price_source,
                outcome_price_source_requested=args.outcome_price_source,
                price_source_provenance=price_source_provenance,
                promotion_artifact_path=promotion_artifact_path,
                promotion_source_date=promotion_source_date,
            )
            if args.write:
                reports = materialization["reports"]
                _atomic_write_json(control_path(args.date), reports["control"])
                _atomic_write_json(label_report_path(args.date), reports["mature"])
                _atomic_write_json(baseline_path(args.date), reports["baseline"])
                _atomic_write_json(paired_path(args.date), reports["paired"])
                _atomic_write_json(
                    candidate_lifecycle_report_path(args.date),
                    reports["candidate_lifecycle_state"],
                )
                written_reports = {
                    "control": _load_json(control_path(args.date)),
                    "mature": _load_json(label_report_path(args.date)),
                    "baseline": _load_json(baseline_path(args.date)),
                    "paired": _load_json(paired_path(args.date)),
                    "candidate_lifecycle_state": _load_json(
                        candidate_lifecycle_report_path(args.date)
                    ),
                }
                write_validation_errors = validate_daily_materialization_reports(
                    target_date=args.date,
                    reports=written_reports,
                )
                if write_validation_errors:
                    raise RuntimeError(
                        "daily_exact_quality_chain_write_validation_failed:"
                        + ",".join(write_validation_errors)
                    )
            printable = {
                key: value for key, value in materialization.items() if key != "reports"
            }
            printable["artifact_paths"] = {
                "control": str(control_path(args.date)),
                "mature": str(label_report_path(args.date)),
                "baseline": str(baseline_path(args.date)),
                "paired": str(paired_path(args.date)),
                "candidate_lifecycle_state": str(
                    candidate_lifecycle_report_path(args.date)
                ),
            }
            print(json.dumps(printable, ensure_ascii=False))
            return 0
        elif args.mode == "baseline":
            report = build_quality_baseline(target_date=args.date, labels=labels)
            report["outcome_price_source"] = effective_outcome_price_source
            report["outcome_price_source_requested"] = args.outcome_price_source
            report["price_source_provenance"] = price_source_provenance
            path = baseline_path(args.date)
        elif args.mode == "correlation":
            report = build_score_outcome_correlation_report(
                target_date=args.date,
                labels=labels,
                price_source_provenance=price_source_provenance,
            )
            report["outcome_price_source"] = effective_outcome_price_source
            report["outcome_price_source_requested"] = args.outcome_price_source
            path = score_correlation_path(args.date)
        elif args.mode == "recovery":
            report = build_recovery_trigger_report(
                target_date=args.date,
                paired_report=_load_json(paired_path(args.date)),
                labels=labels,
                payloads=sources["payloads"],
                price_rows=prices,
                price_source_provenance=price_source_provenance,
            )
            report["outcome_price_source"] = effective_outcome_price_source
            report["outcome_price_source_requested"] = args.outcome_price_source
            path = recovery_trigger_path(args.date)
        elif args.mode == "reversal_sequence":
            stored_label_path = label_report_path(args.date)
            stored_label_report = _load_json(stored_label_path)
            stored_labels = stored_label_report.get("labels")
            stored_labels_reused = bool(
                stored_label_report.get("target_date") == args.date
                and isinstance(stored_labels, list)
                and stored_labels
            )
            sequence_labels = stored_labels if stored_labels_reused else labels
            sequence_paired_path = detailed_paired_path(
                args.date,
                candidate_prompt_version=(
                    DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION
                ),
            )
            report = build_entry_reversal_sequence_report(
                target_date=args.date,
                paired_report=_load_json(sequence_paired_path),
                labels=sequence_labels,
                payloads=sources["payloads"],
                outcome_source={
                    "label_report_path": str(stored_label_path),
                    "label_report_reused": stored_labels_reused,
                    "label_schema": stored_label_report.get("schema"),
                    "outcome_price_source": (
                        stored_label_report.get("outcome_price_source")
                        if stored_labels_reused
                        else effective_outcome_price_source
                    ),
                    "paired_report_path": str(sequence_paired_path),
                },
            )
            path = reversal_sequence_path(args.date)
        else:
            replay_labels = labels
            outcome_recovery: dict[str, Any] | None = None
            if args.outcome_recovery_report:
                replay_labels, outcome_recovery = (
                    recover_same_trace_outcome_labels_from_paired_reports(
                        target_date=args.date,
                        labels=labels,
                        traces=sources["traces"],
                        payloads=sources["payloads"],
                        report_paths=args.outcome_recovery_report,
                    )
                )
            prepared_requests = prepare_paired_replay_requests(
                control_manifest=_load_json(
                    control_path(
                        args.date,
                        effective_venue=args.venue,
                        session_bucket=args.session_bucket,
                    )
                ),
                traces=sources["traces"],
                payloads=sources["payloads"],
                labels=replay_labels,
            )
            if args.stage:
                prepared_requests = [
                    request
                    for request in prepared_requests
                    if str(request.get("stage") or "").strip().lower() == args.stage
                ]
            if args.mode == "detailed":
                prepared_requests = prepare_detailed_paired_replay_requests(
                    prepared_requests,
                    candidate_prompt_version=args.detailed_candidate_version,
                    candidate_model_override=args.candidate_model or None,
                )
            requests = [
                request
                for request in prepared_requests
                if (request.get("sample_floor") or {}).get("pass") is True
            ]
            model_comparison_baseline_path: Path | None = None
            model_comparison_baseline_report: dict[str, Any] = {}
            model_comparison_baseline_model = ""
            if args.candidate_model and requests:
                model_comparison_baseline_path = detailed_paired_path(
                    args.date,
                    candidate_prompt_version=args.detailed_candidate_version,
                    effective_venue=args.venue,
                    session_bucket=args.session_bucket,
                )
                model_comparison_baseline_report = _load_json(
                    model_comparison_baseline_path
                )
                model_comparison_errors = validate_model_comparison_baseline(
                    requests,
                    model_comparison_baseline_report,
                )
                if model_comparison_errors:
                    raise RuntimeError(
                        "offline_model_comparison_baseline_invalid:"
                        + ",".join(model_comparison_errors[:20])
                    )
                model_comparison_baseline_model = str(
                    (
                        ((requests[0].get("candidate") or {}).get("model_comparison"))
                        or {}
                    ).get("baseline_model")
                    or ""
                )
            results: list[dict[str, Any]] = []
            existing_report: dict[str, Any] = {}
            existing_result_reuse_count = 0
            new_candidate_execution_count = 0
            deferred_candidate_execution_count = 0
            execution_selection: dict[str, Any] | None = None
            evaluated_requests = list(requests)
            if args.execute_candidate and requests:
                output_path = (
                    detailed_paired_path(
                        args.date,
                        candidate_prompt_version=args.detailed_candidate_version,
                        candidate_model=args.candidate_model or None,
                        effective_venue=args.venue,
                        session_bucket=args.session_bucket,
                    )
                    if args.mode == "detailed"
                    else (
                        stage_paired_path(
                            args.date,
                            args.stage,
                            effective_venue=args.venue,
                            session_bucket=args.session_bucket,
                        )
                        if args.stage
                        else paired_path(
                            args.date,
                            effective_venue=args.venue,
                            session_bucket=args.session_bucket,
                        )
                    )
                )
                existing_report = _load_json(output_path)
                existing_selection = existing_report.get(
                    "candidate_execution_selection"
                )
                existing_selection_policy = (
                    str(existing_selection.get("policy") or "")
                    if isinstance(existing_selection, dict)
                    else ""
                )
                existing_selection_contract_pass = bool(
                    isinstance(existing_selection, dict)
                    and existing_selection.get("outcome_blind") is True
                    and existing_selection.get("contract_pass") is True
                    and (
                        existing_selection_policy
                        == CANDIDATE_EXECUTION_SELECTION_POLICY
                        or (
                            args.candidate_max_new_requests <= 0
                            and existing_selection_policy == "complete_eligible_census"
                        )
                    )
                )
                request_by_pair = {
                    str(request.get("paired_replay_id") or ""): request
                    for request in requests
                }
                existing_results = [
                    row
                    for row in existing_report.get("results") or []
                    if isinstance(row, dict)
                    and existing_selection_contract_pass
                    and row.get("status") == "pass"
                    and str(row.get("paired_replay_id") or "") in request_by_pair
                    and row.get("payload_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "payload_sha256"
                    )
                    and row.get("candidate_prompt_sha256")
                    == (
                        request_by_pair[str(row.get("paired_replay_id") or "")].get(
                            "candidate"
                        )
                        or {}
                    ).get("system_prompt_sha256")
                    and row.get("candidate_contract_sha256")
                    == (
                        request_by_pair[str(row.get("paired_replay_id") or "")].get(
                            "candidate"
                        )
                        or {}
                    ).get("contract_sha256")
                    and row.get("candidate_response_schema_instance_sha256")
                    == (
                        request_by_pair[str(row.get("paired_replay_id") or "")].get(
                            "candidate"
                        )
                        or {}
                    ).get("response_schema_instance_sha256")
                    and row.get("candidate_input_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "candidate_input_sha256"
                    )
                    and row.get("exact_payload_analysis_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "exact_payload_analysis_sha256"
                    )
                    and row.get("anticipatory_reversal_analysis_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "anticipatory_reversal_analysis_sha256"
                    )
                    and _semantic_repair_provenance_matches(
                        row,
                        request_by_pair[str(row.get("paired_replay_id") or "")],
                    )
                    and _successful_candidate_result_model(row)
                    == str(
                        (
                            request_by_pair[str(row.get("paired_replay_id") or "")].get(
                                "candidate"
                            )
                            or {}
                        ).get("model")
                        or ""
                    )
                    and not validate_replay_candidate_response(
                        request_by_pair[str(row.get("paired_replay_id") or "")],
                        dict(row.get("candidate_response") or {}),
                    )
                ]
                completed_pair_ids = {
                    str(row.get("paired_replay_id") or "") for row in existing_results
                }
                existing_attempted_pair_ids = _valid_checkpoint_attempted_pair_ids(
                    existing_report,
                    valid_pair_ids=set(request_by_pair),
                    selection_contract_pass=existing_selection_contract_pass,
                )
                pending_requests = [
                    request
                    for request in requests
                    if str(request.get("paired_replay_id") or "")
                    not in completed_pair_ids
                ]
                pending_requests, execution_selection = (
                    select_pending_candidate_execution_requests(
                        pending_requests,
                        max_new_requests=args.candidate_max_new_requests,
                        previously_attempted_pair_ids=(existing_attempted_pair_ids),
                    )
                )
                deferred_candidate_execution_count = int(
                    execution_selection.get("deferred_new_count") or 0
                )
                existing_result_reuse_count = len(existing_results)
                new_candidate_execution_count = len(pending_requests)
                api_keys = _offline_openai_api_keys()

                def captured_control(request: dict[str, Any]) -> dict[str, Any]:
                    control = request.get("control") or {}
                    return {
                        "action": control.get("captured_action"),
                        "score": control.get("captured_score"),
                        "reason": control.get("captured_reason"),
                        "edge_state": control.get("captured_edge_state"),
                        "evidence": control.get("captured_evidence"),
                        "entry_probe_intent": control.get(
                            "captured_entry_probe_intent"
                        ),
                        "entry_probe_intent_status": control.get(
                            "captured_entry_probe_intent_status"
                        ),
                        "entry_probe_intent_eligibility_path": control.get(
                            "captured_entry_probe_intent_eligibility_path"
                        ),
                        "entry_probe_intent_after_cost_reward_risk": control.get(
                            "captured_entry_probe_intent_after_cost_reward_risk"
                        ),
                        "result_source": "captured_natural_control",
                    }

                def candidate_runner(request: dict[str, Any]) -> dict[str, Any]:
                    return execute_openai_prompt_v2_candidate(
                        request,
                        api_keys=api_keys,
                        timeout_sec=args.candidate_timeout_sec,
                    )

                results = existing_results + run_paired_replay_parallel(
                    pending_requests,
                    control_runner=captured_control,
                    candidate_runner=candidate_runner,
                    max_workers=args.candidate_workers,
                )
                result_order = {
                    str(request.get("paired_replay_id") or ""): index
                    for index, request in enumerate(requests)
                }
                results.sort(
                    key=lambda row: result_order.get(
                        str(row.get("paired_replay_id") or ""), len(result_order)
                    )
                )
                evaluated_pair_ids = {
                    str(row.get("paired_replay_id") or "")
                    for row in results
                    if row.get("paired_replay_id")
                }
                evaluated_requests = [
                    request
                    for request in requests
                    if str(request.get("paired_replay_id") or "") in evaluated_pair_ids
                ]
                execution_selection.update(
                    {
                        "eligible_request_count": len(requests),
                        "reused_valid_result_count": len(existing_results),
                        "evaluated_request_count": len(evaluated_requests),
                        "checkpoint_evaluated_setup_state_counts": (
                            _checkpoint_setup_state_counts(evaluated_requests)
                        ),
                        "checkpoint_evaluated_unique_symbol_count": len(
                            {
                                _normalize_stock_code(request.get("stock_code"))
                                for request in evaluated_requests
                                if _normalize_stock_code(request.get("stock_code"))
                            }
                        ),
                        "evaluation_coverage_pct": (
                            len(evaluated_requests) / len(requests) * 100.0
                            if requests
                            else None
                        ),
                        "existing_selection_contract_pass": (
                            existing_selection_contract_pass
                            if existing_report
                            else None
                        ),
                        "contract_pass": bool(
                            execution_selection.get("contract_pass") is True
                            and len(evaluated_requests) == len(results)
                        ),
                    }
                )
            report = build_paired_replay_report(
                target_date=args.date,
                requests=evaluated_requests,
                results=results,
                labels=replay_labels,
                execution_selection=execution_selection,
                prepared_requests=prepared_requests,
            )
            if args.mode == "detailed":
                report["schema"] = DETAILED_PAIRED_SCHEMA
                report["analysis_schema"] = EXACT_PAYLOAD_ANALYSIS_SCHEMA
                if args.detailed_candidate_version in {
                    DECISION_QUALITY_V2_9_ANTICIPATORY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_9_1_ANTICIPATORY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_10_BOUNDED_OPPORTUNITY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_11_CLEAN_CONTINUATION_PROMPT_VERSION,
                    DECISION_QUALITY_V2_12_SELECTIVE_RECOVERY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
                    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                    DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
                }:
                    report["supplemental_analysis_schema"] = (
                        ANTICIPATORY_REVERSAL_ANALYSIS_SCHEMA
                    )
                if args.detailed_candidate_version in {
                    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
                    DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
                    DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION,
                }:
                    report["entry_setup_evidence_schema"] = ENTRY_SETUP_EVIDENCE_SCHEMA
                    report["entry_risk_adjudication_schema"] = (
                        ENTRY_RISK_ADJUDICATION_SCHEMA
                    )
                report["three_way_comparison"] = build_detailed_three_way_comparison(
                    one_pass_report=_load_json(
                        paired_path(
                            args.date,
                            effective_venue=args.venue,
                            session_bucket=args.session_bucket,
                        )
                    ),
                    detailed_report=report,
                )
                if args.candidate_model:
                    request_model_comparison = (requests[0].get("candidate") or {}).get(
                        "model_comparison"
                    ) or {}
                    report["model_comparison_contract"] = {
                        **dict(request_model_comparison),
                        "baseline_report_path": str(
                            model_comparison_baseline_path or ""
                        ),
                    }
                    report["model_comparison"] = build_model_replay_comparison(
                        baseline_report=model_comparison_baseline_report,
                        candidate_report=report,
                        baseline_model=model_comparison_baseline_model,
                        candidate_model=args.candidate_model,
                    )
                replay_reconstruction = existing_report.get(
                    "replay_input_reconstruction"
                )
                if isinstance(replay_reconstruction, dict):
                    report["replay_input_reconstruction"] = dict(replay_reconstruction)
                if outcome_recovery is not None:
                    report["outcome_recovery"] = outcome_recovery
            if args.execute_candidate:
                report["existing_result_reuse_count"] = existing_result_reuse_count
                report["new_candidate_execution_count"] = new_candidate_execution_count
                report["deferred_candidate_execution_count"] = (
                    deferred_candidate_execution_count
                )
            _attach_paired_preparation_metadata(
                report,
                prepared_requests=prepared_requests,
                accepted_requests=requests,
                outcome_price_source=effective_outcome_price_source,
                outcome_price_source_requested=args.outcome_price_source,
                price_source_provenance=price_source_provenance,
                outcome_as_of=as_of.isoformat(),
            )
            if outcome_recovery is not None:
                report["outcome_price_source"] = (
                    "current_labels_with_prior_same_trace_paired_outcome_recovery"
                )
            path = (
                detailed_paired_path(
                    args.date,
                    candidate_prompt_version=args.detailed_candidate_version,
                    candidate_model=args.candidate_model or None,
                    effective_venue=args.venue,
                    session_bucket=args.session_bucket,
                )
                if args.mode == "detailed"
                else (
                    stage_paired_path(
                        args.date,
                        args.stage,
                        effective_venue=args.venue,
                        session_bucket=args.session_bucket,
                    )
                    if args.stage
                    else paired_path(
                        args.date,
                        effective_venue=args.venue,
                        session_bucket=args.session_bucket,
                    )
                )
            )
            if args.stage:
                report["stage_filter"] = args.stage
    if args.venue or args.session_bucket:
        report["cohort_filter"] = {
            "effective_venue": args.venue,
            "session_bucket": args.session_bucket,
            "runtime_effect": False,
        }
    if args.write:
        _atomic_write_json(path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
