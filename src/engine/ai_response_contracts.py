"""Shared AI response schema contracts for Gemini/OpenAI engines."""

from __future__ import annotations


AI_REASON_LANGUAGE_POLICY = "english_ascii_only"
AI_REASON_LANGUAGE_FALLBACK = "Reason unavailable: non-English output from AI"


AI_RESPONSE_SCHEMA_REGISTRY = {
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
