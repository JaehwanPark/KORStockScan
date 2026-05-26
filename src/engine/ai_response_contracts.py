"""Shared AI response schema contracts for runtime AI engines."""

from __future__ import annotations


AI_REASON_LANGUAGE_POLICY = "english_ascii_only"
AI_REASON_LANGUAGE_FALLBACK = "Reason unavailable: non-English output from AI"

FLOW_STATE_LABELS = {
    "흡수": "absorption",
    "회복": "recovery",
    "분배": "distribution",
    "붕괴": "breakdown",
    "소강": "quiet",
    "absorb": "absorption",
    "absorbing": "absorption",
    "absorption": "absorption",
    "recover": "recovery",
    "recovering": "recovery",
    "recovery": "recovery",
    "distribute": "distribution",
    "distributing": "distribution",
    "distribution": "distribution",
    "break": "breakdown",
    "breaking": "breakdown",
    "breakdown": "breakdown",
    "collapse": "breakdown",
    "collapsed": "breakdown",
    "calm": "quiet",
    "quiet": "quiet",
    "neutral": "quiet",
    "sideways": "quiet",
}

CANONICAL_FLOW_STATES = {"absorption", "recovery", "distribution", "breakdown", "quiet"}
KNOWN_FLOW_STATE_SENTINELS = {
    "-",
    "unknown",
    "flow_state_unavailable",
    "ai_lock_contention",
    "engine_disabled",
    "exception",
}

GATEKEEPER_ACTION_KEYS = {
    "즉시 매수": "immediate_buy",
    "immediate buy": "immediate_buy",
    "immediate_buy": "immediate_buy",
    "buy_now": "immediate_buy",
    "buy": "immediate_buy",
    "눌림 대기": "pullback_wait",
    "눌림|대기": "pullback_wait",
    "눌림": "pullback_wait",
    "pullback wait": "pullback_wait",
    "pullback_wait": "pullback_wait",
    "wait_for_pullback": "pullback_wait",
    "보유 지속": "hold_continue",
    "hold continue": "hold_continue",
    "hold_continue": "hold_continue",
    "hold": "hold_continue",
    "일부 익절": "partial_take_profit",
    "partial take profit": "partial_take_profit",
    "partial_take_profit": "partial_take_profit",
    "trim": "partial_take_profit",
    "전량 회피": "full_avoid",
    "전량|회피": "full_avoid",
    "전량": "full_avoid",
    "full avoid": "full_avoid",
    "full_avoid": "full_avoid",
    "avoid_all": "full_avoid",
    "drop": "full_avoid",
    "스캘핑 우선": "scalping_preferred",
    "scalping preferred": "scalping_preferred",
    "scalping_preferred": "scalping_preferred",
    "스윙 우선": "swing_preferred",
    "swing preferred": "swing_preferred",
    "swing_preferred": "swing_preferred",
    "둘 다 아님": "neither",
    "둘|다|아님": "neither",
    "neither": "neither",
    "unknown": "unknown",
}

CANONICAL_GATEKEEPER_ACTION_KEYS = {
    "immediate_buy",
    "pullback_wait",
    "hold_continue",
    "partial_take_profit",
    "full_avoid",
    "scalping_preferred",
    "swing_preferred",
    "neither",
    "unknown",
}

GATEKEEPER_ACTION_DISPLAY = {
    "immediate_buy": "즉시 매수",
    "pullback_wait": "눌림 대기",
    "hold_continue": "보유 지속",
    "partial_take_profit": "일부 익절",
    "full_avoid": "전량 회피",
    "scalping_preferred": "스캘핑 우선",
    "swing_preferred": "스윙 우선",
    "neither": "둘 다 아님",
    "unknown": "UNKNOWN",
}


def normalize_flow_state_label(value: object) -> str:
    text = str(value or "-").strip().lower()
    mapped = FLOW_STATE_LABELS.get(text)
    if mapped:
        return mapped
    if text in KNOWN_FLOW_STATE_SENTINELS:
        return text
    return "unknown_flow_state"


def is_known_flow_state_label(value: object) -> bool:
    text = str(value or "-").strip().lower()
    return text in FLOW_STATE_LABELS or text in CANONICAL_FLOW_STATES or text in KNOWN_FLOW_STATE_SENTINELS


def normalize_gatekeeper_action_key(value: object) -> str:
    text = str(value or "UNKNOWN").strip().replace("|", " ")
    folded = " ".join(text.split()).lower()
    if folded in {"", "-", "none", "null", "nan", "unknown"}:
        return "unknown"
    key = GATEKEEPER_ACTION_KEYS.get(folded)
    if key:
        return key
    compact = text.strip().replace(" ", "|")
    key = GATEKEEPER_ACTION_KEYS.get(compact)
    if key:
        return key
    return "unknown"


def is_known_gatekeeper_action_label(value: object) -> bool:
    text = str(value or "UNKNOWN").strip().replace("|", " ")
    folded = " ".join(text.split()).lower()
    if folded in {"", "-", "none", "null", "nan", "unknown"}:
        return True
    compact = text.strip().replace(" ", "|")
    return (
        folded in GATEKEEPER_ACTION_KEYS
        or compact in GATEKEEPER_ACTION_KEYS
        or folded.replace(" ", "_") in CANONICAL_GATEKEEPER_ACTION_KEYS
    )


def display_gatekeeper_action_label(value: object) -> str:
    key = normalize_gatekeeper_action_key(value)
    return GATEKEEPER_ACTION_DISPLAY.get(key, str(value or "UNKNOWN").replace("|", " ").strip() or "UNKNOWN")


AI_RESPONSE_SCHEMA_REGISTRY = {
    "swing_model_tier2_review_v1": {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer"},
            "status": {"type": "string", "enum": ["parsed", "parse_rejected", "unavailable"]},
            "decision": {"type": "string", "enum": ["approved", "blocked"]},
            "blocking_reasons": {"type": "array", "items": {"type": "string"}},
            "reviewed_candidate_family": {"type": "string"},
            "reviewed_bull_mode": {"type": "string", "enum": ["enabled", "disabled", "hold_current"]},
            "checks": {
                "type": "object",
                "properties": {
                    "label_leakage": {"type": "string", "enum": ["pass", "block", "warning"]},
                    "source_quality": {"type": "string", "enum": ["pass", "block", "warning"]},
                    "schema_compatibility": {"type": "string", "enum": ["pass", "block", "warning"]},
                    "metric_interpretation": {"type": "string", "enum": ["pass", "block", "warning"]},
                    "forbidden_use": {"type": "string", "enum": ["pass", "block", "warning"]},
                },
                "required": [
                    "label_leakage",
                    "source_quality",
                    "schema_compatibility",
                    "metric_interpretation",
                    "forbidden_use",
                ],
                "additionalProperties": False,
            },
        },
        "required": [
            "schema_version",
            "status",
            "decision",
            "blocking_reasons",
            "reviewed_candidate_family",
            "reviewed_bull_mode",
            "checks",
        ],
        "additionalProperties": False,
    },
    "entry_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["BUY", "WAIT", "DROP"]},
            "score": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["action", "score", "reason"],
    },
    "entry_price_v1": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["USE_DEFENSIVE", "USE_REFERENCE", "IMPROVE_LIMIT", "SKIP"],
            },
            "order_price": {"type": "integer"},
            "confidence": {"type": "integer"},
            "reason": {"type": "string"},
            "max_wait_sec": {"type": "integer"},
        },
        "required": ["action", "order_price", "confidence", "reason", "max_wait_sec"],
    },
    "holding_exit_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["HOLD", "TRIM", "EXIT"]},
            "score": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["action", "score", "reason"],
    },
    "holding_exit_flow_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["HOLD", "TRIM", "EXIT"]},
            "score": {"type": "integer"},
            "flow_state": {"type": "string"},
            "thesis": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
            "next_review_sec": {"type": "integer"},
        },
        "required": ["action", "score", "flow_state", "thesis", "evidence", "reason", "next_review_sec"],
    },
    "overnight_v1": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["SELL_TODAY", "HOLD_OVERNIGHT"]},
            "confidence": {"type": "integer"},
            "reason": {"type": "string"},
            "risk_note": {"type": "string"},
        },
        "required": ["action", "confidence", "reason", "risk_note"],
    },
    "condition_entry_v1": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["BUY", "WAIT", "SKIP"]},
            "confidence": {"type": "integer"},
            "order_type": {"type": "string", "enum": ["MARKET", "LIMIT_TOP", "NONE"]},
            "position_size_ratio": {"type": "number"},
            "invalidation_price": {"type": "integer"},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "decision",
            "confidence",
            "order_type",
            "position_size_ratio",
            "invalidation_price",
            "reasons",
            "risks",
        ],
    },
    "condition_exit_v1": {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["HOLD", "TRIM", "EXIT"]},
            "confidence": {"type": "integer"},
            "trim_ratio": {"type": "number"},
            "new_stop_price": {"type": "integer"},
            "reason_primary": {"type": "string"},
            "warning": {"type": "string"},
        },
        "required": [
            "decision",
            "confidence",
            "trim_ratio",
            "new_stop_price",
            "reason_primary",
            "warning",
        ],
    },
    "threshold_ai_correction_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "corrections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "family": {"type": "string"},
                        "anomaly_type": {"type": "string"},
                        "ai_review_state": {
                            "type": "string",
                            "enum": [
                                "agree",
                                "correction_proposed",
                                "caution",
                                "insufficient_context",
                                "safety_concern",
                                "unavailable",
                            ],
                        },
                        "correction_proposal": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "proposed_state": {
                                    "type": ["string", "null"],
                                    "enum": [
                                        "adjust_up",
                                        "adjust_down",
                                        "hold",
                                        "hold_sample",
                                        "freeze",
                                        None,
                                    ],
                                },
                                "proposed_value": {
                                    "type": ["number", "integer", "boolean", "string", "null"],
                                },
                                "anomaly_route": {
                                    "type": ["string", "null"],
                                    "enum": [
                                        "threshold_candidate",
                                        "incident",
                                        "instrumentation_gap",
                                        "normal_drift",
                                        None,
                                    ],
                                },
                                "sample_window": {
                                    "type": ["string", "null"],
                                    "enum": [
                                        "daily_intraday",
                                        "rolling_5d",
                                        "rolling_10d",
                                        "cumulative",
                                        None,
                                    ],
                                },
                            },
                            "required": ["proposed_state", "proposed_value", "anomaly_route", "sample_window"],
                        },
                        "correction_reason": {"type": "string"},
                        "required_evidence": {"type": "array", "items": {"type": "string"}},
                        "risk_flags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "family",
                        "anomaly_type",
                        "ai_review_state",
                        "correction_proposal",
                        "correction_reason",
                        "required_evidence",
                        "risk_flags",
                    ],
                },
            },
        },
        "required": ["schema_version", "corrections"],
    },
    "lifecycle_bucket_discovery_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "interpretation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "bucket_reviews": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "bucket_id": {"type": "string"},
                                "interpreted_relation": {
                                    "type": "string",
                                    "enum": ["existing_bucket_refinement", "new_bucket_candidate", "unclear"],
                                },
                                "interpreted_state": {
                                    "type": "string",
                                    "enum": [
                                        "source_only_keep_collecting",
                                        "sim_auto_approved",
                                        "live_auto_apply_ready",
                                        "runtime_blocked_contract_gap",
                                        "code_patch_required",
                                        "code_review_failed",
                                        "automation_handoff_gap",
                                        "new_bucket_candidate",
                                    ],
                                },
                                "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                                "reason": {"type": "string"},
                            },
                            "required": [
                                "bucket_id",
                                "interpreted_relation",
                                "interpreted_state",
                                "confidence",
                                "reason",
                            ],
                        },
                    },
                    "source_contract_review": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "status": {"type": "string", "enum": ["pass", "warning", "fail"]},
                            "changes": {"type": "array", "items": {"type": "string"}},
                            "reason": {"type": "string"},
                        },
                        "required": ["status", "changes", "reason"],
                    },
                },
                "required": ["bucket_reviews", "source_contract_review"],
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pass", "correction_required", "insufficient_context"],
                    },
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["status", "issues", "reason"],
            },
            "final_conclusions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "bucket_id": {"type": "string"},
                        "final_bucket_relation": {
                            "type": "string",
                            "enum": ["existing_bucket_refinement", "new_bucket_candidate", "unclear"],
                        },
                        "final_classification_state": {
                            "type": "string",
                            "enum": [
                                "source_only_keep_collecting",
                                "sim_auto_approved",
                                "live_auto_apply_ready",
                                "runtime_blocked_contract_gap",
                                "code_patch_required",
                                "code_review_failed",
                                "automation_handoff_gap",
                                "new_bucket_candidate",
                            ],
                        },
                        "final_decision": {
                            "type": "string",
                            "enum": ["keep", "correct", "block"],
                        },
                        "reason": {"type": "string"},
                    },
                    "required": [
                        "bucket_id",
                        "final_bucket_relation",
                        "final_classification_state",
                        "final_decision",
                        "reason",
                    ],
                },
            },
        },
        "required": ["schema_version", "interpretation", "audit", "final_conclusions"],
    },
    "pattern_lab_ai_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "interpretation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "review_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "review_id": {"type": "string"},
                                "domain": {"type": "string", "enum": ["scalping", "swing", "cross_domain"]},
                                "interpreted_state": {
                                    "type": "string",
                                    "enum": [
                                        "source_only_keep_collecting",
                                        "automation_handoff_gap",
                                        "source_quality_gap",
                                        "ai_review_gap",
                                        "code_patch_required",
                                    ],
                                },
                                "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                                "reason": {"type": "string"},
                            },
                            "required": ["review_id", "domain", "interpreted_state", "confidence", "reason"],
                        },
                    },
                    "source_feedback_status": {
                        "type": "string",
                        "enum": ["pass", "warning", "fail", "insufficient_context"],
                    },
                },
                "required": ["review_items", "source_feedback_status"],
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "correction_required", "insufficient_context"]},
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "forbidden_use_violations": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["status", "issues", "forbidden_use_violations", "reason"],
            },
            "final_conclusions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "review_id": {"type": "string"},
                        "domain": {"type": "string", "enum": ["scalping", "swing", "cross_domain"]},
                        "final_state": {
                            "type": "string",
                            "enum": [
                                "source_only_keep_collecting",
                                "automation_handoff_gap",
                                "source_quality_gap",
                                "ai_review_gap",
                                "code_patch_required",
                            ],
                        },
                        "final_decision": {"type": "string", "enum": ["keep", "surface_workorder", "block_runtime_use"]},
                        "reason": {"type": "string"},
                        "required_followup": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "review_id",
                        "domain",
                        "final_state",
                        "final_decision",
                        "reason",
                        "required_followup",
                    ],
                },
            },
        },
        "required": ["schema_version", "interpretation", "audit", "final_conclusions"],
    },
    "runtime_apply_gap_ai_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "reviewer": {"type": "string", "enum": ["runtime_apply_gap_ai_review"]},
            "candidate_reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "recommended_disposition": {
                            "type": "string",
                            "enum": [
                                "live_auto_apply_ready",
                                "sim_auto_approved",
                                "approval_required",
                                "code_patch_required",
                                "runtime_blocked_contract_gap",
                                "source_quality_blocker",
                                "safety_veto",
                                "post_apply_attribution_pending",
                            ],
                        },
                        "route_decision": {
                            "type": "string",
                            "enum": [
                                "push_runtime",
                                "keep_sim_policy",
                                "require_approval",
                                "require_code_patch",
                                "block_source_quality",
                                "block_safety",
                                "retry_handoff",
                            ],
                        },
                        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                        "reason": {"type": "string"},
                        "required_followup": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "candidate_id",
                        "recommended_disposition",
                        "route_decision",
                        "confidence",
                        "reason",
                        "required_followup",
                    ],
                },
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "retry_required", "correction_required"]},
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["status", "issues", "reason"],
            },
            "codex_directives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "directive_type": {
                            "type": "string",
                            "enum": [
                                "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET",
                                "IMPLEMENT_SCALE_IN_POLICY_CONTRACT",
                                "FIX_PRODUCER_CONSUMER_HANDOFF",
                                "ADD_POST_APPLY_ATTRIBUTION",
                                "RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE",
                                "PROMOTE_APPROVAL_READY_DRY_RUN_AXIS",
                                "RETRY_FAILED_AI_REVIEW",
                                "RETRY_MISSING_ARTIFACT_CHAIN",
                            ],
                        },
                        "candidate_id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["directive_type", "candidate_id", "reason"],
                },
            },
        },
        "required": ["schema_version", "reviewer", "candidate_reviews", "audit", "codex_directives"],
    },
    "swing_bottom_rebound_policy_ai_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "interpretation": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "policy_edge_state": {
                        "type": "string",
                        "enum": ["candidate_policy_better", "keep_current_policy", "insufficient_context"],
                    },
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["policy_edge_state", "evidence"],
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pass", "correction_required", "insufficient_context"],
                    },
                    "explicit_gaps": {"type": "array", "items": {"type": "string"}},
                    "forbidden_use_violations": {"type": "array", "items": {"type": "string"}},
                    "runtime_authority_preserved": {"type": "boolean"},
                },
                "required": [
                    "status",
                    "explicit_gaps",
                    "forbidden_use_violations",
                    "runtime_authority_preserved",
                ],
            },
            "final_conclusion": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "classification_state": {
                        "type": "string",
                        "enum": ["sim_auto_approved", "source_only_keep_collecting", "code_patch_required"],
                    },
                    "promote_policy": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["classification_state", "promote_policy", "reason"],
            },
        },
        "required": ["schema_version", "interpretation", "audit", "final_conclusion"],
    },
    "producer_gap_discovery_ai_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "reviewer": {"type": "string", "enum": ["producer_gap_discovery_ai_review"]},
            "candidate_reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "pattern_type": {
                            "type": "string",
                            "enum": [
                                "stop_recovery_counterfactual_missing",
                                "missed_fill_recovery_counterfactual_missing",
                                "swing_sim_probe_label_gap_missing",
                                "scale_in_counterfactual_gap_missing",
                                "time_window_policy_exception_missing",
                                "volatile_runner_exit_counterfactual_missing",
                                "limit_up_plateau_breakdown_exit_missing",
                                "sim_entry_selection_gap_missing",
                                "sim_submit_fill_quality_gap_missing",
                                "sim_holding_runner_gap_missing",
                                "sim_exit_plateau_breakdown_gap_missing",
                                "sim_stop_recovery_gap_missing",
                                "sim_scale_in_counterfactual_gap_missing",
                                "sim_time_window_exception_gap_missing",
                                "sim_source_quality_join_gap_missing",
                                "sim_first_coverage_gap",
                            ],
                        },
                        "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                        "recommended_route": {
                            "type": "string",
                            "enum": ["implement_now", "defer_evidence", "block_source_quality"],
                        },
                        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                        "target_subsystem": {"type": "string"},
                        "reason": {"type": "string"},
                        "implementation_requirements": {"type": "array", "items": {"type": "string"}},
                        "acceptance_tests": {"type": "array", "items": {"type": "string"}},
                        "files_likely_touched": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "candidate_id",
                        "pattern_type",
                        "priority",
                        "recommended_route",
                        "confidence",
                        "target_subsystem",
                        "reason",
                        "implementation_requirements",
                        "acceptance_tests",
                        "files_likely_touched",
                    ],
                },
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "correction_required", "insufficient_context"]},
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "forbidden_use_violations": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["status", "issues", "forbidden_use_violations", "reason"],
            },
        },
        "required": ["schema_version", "reviewer", "candidate_reviews", "audit"],
    },
    "stage_hook_workorder_discovery_ai_review_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "reviewer": {"type": "string", "enum": ["stage_hook_workorder_discovery_ai_review"]},
            "candidate_reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "candidate_id": {"type": "string"},
                        "hook_name": {"type": "string"},
                        "hook_class": {
                            "type": "string",
                            "enum": [
                                "entry_policy_hook_candidate",
                                "submit_quality_hook_candidate",
                                "runtime_arbitration_hook",
                                "scale_in_policy_hook_candidate",
                                "source_schema_provenance_hook",
                            ],
                        },
                        "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                        "recommended_readiness_tier": {
                            "type": "string",
                            "enum": [
                                "observe_only",
                                "producer_needed",
                                "hook_design_ready",
                                "implementation_workorder_ready",
                                "blocked_by_source_quality",
                            ],
                        },
                        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                        "target_subsystem": {"type": "string"},
                        "reason": {"type": "string"},
                        "implementation_requirements": {"type": "array", "items": {"type": "string"}},
                        "acceptance_tests": {"type": "array", "items": {"type": "string"}},
                        "files_likely_touched": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "candidate_id",
                        "hook_name",
                        "hook_class",
                        "priority",
                        "recommended_readiness_tier",
                        "confidence",
                        "target_subsystem",
                        "reason",
                        "implementation_requirements",
                        "acceptance_tests",
                        "files_likely_touched",
                    ],
                },
            },
            "audit": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "status": {"type": "string", "enum": ["pass", "correction_required", "insufficient_context"]},
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "forbidden_use_violations": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["status", "issues", "forbidden_use_violations", "reason"],
            },
        },
        "required": ["schema_version", "reviewer", "candidate_reviews", "audit"],
    },
    "lifecycle_ai_context_v1": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "stage_contexts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "stage": {
                            "type": "string",
                            "enum": ["entry", "submit", "holding", "scale_in", "exit"],
                        },
                        "policy_key": {"type": "string"},
                        "alignment_hint": {"type": "string"},
                        "context_summary": {"type": "string"},
                        "risk_notes": {"type": "array", "items": {"type": "string"}},
                        "forbidden_uses": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "stage",
                        "policy_key",
                        "alignment_hint",
                        "context_summary",
                        "risk_notes",
                        "forbidden_uses",
                    ],
                },
            },
        },
        "required": ["schema_version", "stage_contexts"],
    },
}


def resolve_ai_response_schema(schema_name):
    normalized = str(schema_name or "").strip()
    if not normalized:
        return None
    schema = AI_RESPONSE_SCHEMA_REGISTRY.get(normalized)
    if schema is None:
        raise ValueError(f"Unknown AI response schema: {normalized}")
    return schema


def build_openai_response_text_format(schema_name, *, strict=True):
    schema = resolve_ai_response_schema(schema_name)
    if schema is None:
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "name": str(schema_name),
        "schema": schema,
        "strict": bool(strict),
    }


def normalize_ai_reason_language(reason, *, max_len=120):
    text = str(reason or "").replace("\n", " ").strip()
    violation = any(ord(ch) > 127 for ch in text)
    if violation:
        text = AI_REASON_LANGUAGE_FALLBACK
    if not text:
        text = "Reason unavailable"
    return {
        "reason": text[:max_len],
        "ai_reason_language_policy": AI_REASON_LANGUAGE_POLICY,
        "ai_reason_language_violation": bool(violation),
    }
