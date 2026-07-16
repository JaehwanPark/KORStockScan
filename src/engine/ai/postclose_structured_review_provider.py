"""Structured postclose AI review provider with model-specific primary/failback routes."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from copy import deepcopy
from typing import Any, Callable

from src.engine.ai.postclose_review_config import PostcloseAIReviewConfig
from src.engine.ai_response_contracts import (
    AI_RESPONSE_SCHEMA_REGISTRY,
    build_openai_response_text_format,
)
from src.engine.bedrock_nova_provider import load_bedrock_api_keys_from_config
from src.engine.daily_threshold_cycle_report import (
    _extract_openai_response_text,
    _load_threshold_ai_gemini_keys,
    _load_threshold_ai_openai_keys,
)

ContractValidator = Callable[[str], tuple[bool, str] | bool]


def _prompt_text(context: dict[str, Any], *, ensure_ascii: bool) -> str:
    return json.dumps(context, ensure_ascii=ensure_ascii, indent=2, default=str)


def _normalize_bedrock_schema(schema: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(schema)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                props = node.get("properties")
                if isinstance(props, dict):
                    node["required"] = list(props.keys())
                    for value in props.values():
                        walk(value)
                node.setdefault("additionalProperties", False)
            elif node.get("type") == "array":
                walk(node.get("items"))
            else:
                for value in node.values():
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(normalized)
    return normalized


def _sanitize_error_message(value: object) -> str:
    text = str(value or "")
    for _, secret in _load_threshold_ai_gemini_keys():
        if secret:
            text = text.replace(secret, "[REDACTED_GEMINI_API_KEY]")
    return text[:240]


def _validator_ok(
    validator: ContractValidator | None, raw_text: str
) -> tuple[bool, str]:
    if validator is None:
        return True, ""
    try:
        result = validator(raw_text)
    except Exception as exc:
        return False, f"validator_exception:{type(exc).__name__}:{exc}"
    if isinstance(result, tuple):
        return bool(result[0]), str(result[1] or "")
    return bool(result), ""


def _gemini_status_base(
    config: PostcloseAIReviewConfig, *, schema_name: str
) -> dict[str, Any]:
    return {
        **config.provider_status_fields(),
        "provider": "gemini",
        "model": config.gemini_model,
        "schema_name": schema_name,
        "primary_provider": "gemini_3_5_flash",
        "primary_model": config.gemini_model,
        "failback_provider": config.failback_provider,
        "failback_used": False,
        "gemini_key_rotation_enabled": config.gemini_key_rotation_enabled,
    }


def _gemini_prompt(instructions: str, prompt: str, schema_name: str) -> str:
    return (
        f"{instructions}\n"
        f"Return one strict JSON object matching {schema_name}. "
        "Do not include markdown, prose, code fences, or comments. "
        "Use only enum labels shown in the input instructions. "
        "If candidate_reviews or bucket reviews are required, preserve every requested candidate id exactly.\n\n"
        f"Input context JSON:\n{prompt}"
    )


def _gemini_response_schema(schema_name: str) -> dict[str, Any] | None:
    if schema_name == "runtime_apply_gap_ai_review_v1":
        return {
            "type": "OBJECT",
            "properties": {
                "schema_version": {"type": "INTEGER"},
                "reviewer": {"type": "STRING"},
                "candidate_reviews": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "candidate_id": {"type": "STRING"},
                            "recommended_disposition": {
                                "type": "STRING",
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
                                "type": "STRING",
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
                            "confidence": {
                                "type": "STRING",
                                "enum": ["low", "medium", "high"],
                            },
                            "reason": {"type": "STRING"},
                            "required_followup": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
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
                    "type": "OBJECT",
                    "properties": {
                        "status": {
                            "type": "STRING",
                            "enum": ["pass", "retry_required", "correction_required"],
                        },
                        "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "reason": {"type": "STRING"},
                    },
                    "required": ["status", "issues", "reason"],
                },
                "codex_directives": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "directive_type": {"type": "STRING"},
                            "candidate_id": {"type": "STRING"},
                            "reason": {"type": "STRING"},
                        },
                        "required": ["directive_type", "candidate_id", "reason"],
                    },
                },
            },
            "required": [
                "schema_version",
                "reviewer",
                "candidate_reviews",
                "audit",
                "codex_directives",
            ],
        }
    if schema_name == "lifecycle_bucket_discovery_review_v1":
        bucket_relation_enum = [
            "existing_bucket_refinement",
            "new_bucket_candidate",
            "unclear",
        ]
        classification_state_enum = [
            "source_only_keep_collecting",
            "sim_auto_approved",
            "live_auto_apply_ready",
            "runtime_blocked_contract_gap",
            "code_patch_required",
            "code_review_failed",
            "automation_handoff_gap",
            "new_bucket_candidate",
        ]
        taxonomy_decision_enum = [
            "merge",
            "absorb_as_dimension",
            "create_new_metric",
            "create_new_dimension",
            "keep_bucket",
            "reject",
            "source_quality_blocker",
            "instrumentation_gap",
        ]
        return {
            "type": "OBJECT",
            "properties": {
                "schema_version": {"type": "INTEGER"},
                "interpretation": {
                    "type": "OBJECT",
                    "properties": {
                        "bucket_reviews": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "bucket_id": {"type": "STRING"},
                                    "interpreted_relation": {
                                        "type": "STRING",
                                        "enum": bucket_relation_enum,
                                    },
                                    "interpreted_state": {
                                        "type": "STRING",
                                        "enum": classification_state_enum,
                                    },
                                    "confidence": {
                                        "type": "STRING",
                                        "enum": ["low", "medium", "high"],
                                    },
                                    "reason": {"type": "STRING"},
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
                            "type": "OBJECT",
                            "properties": {
                                "status": {
                                    "type": "STRING",
                                    "enum": ["pass", "warning", "fail"],
                                },
                                "changes": {
                                    "type": "ARRAY",
                                    "items": {"type": "STRING"},
                                },
                                "reason": {"type": "STRING"},
                            },
                            "required": ["status", "changes", "reason"],
                        },
                    },
                    "required": ["bucket_reviews", "source_contract_review"],
                },
                "audit": {
                    "type": "OBJECT",
                    "properties": {
                        "status": {
                            "type": "STRING",
                            "enum": [
                                "pass",
                                "correction_required",
                                "insufficient_context",
                            ],
                        },
                        "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "reason": {"type": "STRING"},
                    },
                    "required": ["status", "issues", "reason"],
                },
                "ai_tier2_proposals": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "bucket_id": {"type": "STRING"},
                            "proposal_decision": {
                                "type": "STRING",
                                "enum": taxonomy_decision_enum,
                            },
                            "recommended_canonical_bucket": {"type": "STRING"},
                            "recommended_metric_or_dimension": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "reasoning_summary": {"type": "STRING"},
                            "confidence": {
                                "type": "STRING",
                                "enum": ["low", "medium", "high"],
                            },
                            "required_source_fields": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "forbidden_uses": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                        },
                        "required": [
                            "bucket_id",
                            "proposal_decision",
                            "recommended_canonical_bucket",
                            "recommended_metric_or_dimension",
                            "reasoning_summary",
                            "confidence",
                            "required_source_fields",
                            "forbidden_uses",
                        ],
                    },
                },
                "comparative_reviews": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "bucket_id": {"type": "STRING"},
                            "selected_decision": {
                                "type": "STRING",
                                "enum": taxonomy_decision_enum,
                            },
                            "selected_source": {
                                "type": "STRING",
                                "enum": [
                                    "deterministic",
                                    "ai_tier2",
                                    "hybrid",
                                    "reject",
                                ],
                            },
                            "recommended_canonical_bucket": {"type": "STRING"},
                            "recommended_metric_or_dimension": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "comparison_summary": {"type": "STRING"},
                            "rejected_alternative_reason": {"type": "STRING"},
                            "confidence": {
                                "type": "STRING",
                                "enum": ["low", "medium", "high"],
                            },
                            "required_source_fields": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "forbidden_uses": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "workorder_title": {"type": "STRING"},
                            "workorder_priority": {
                                "type": "STRING",
                                "enum": ["critical", "high", "medium", "low"],
                            },
                        },
                        "required": [
                            "bucket_id",
                            "selected_decision",
                            "selected_source",
                            "recommended_canonical_bucket",
                            "recommended_metric_or_dimension",
                            "comparison_summary",
                            "rejected_alternative_reason",
                            "confidence",
                            "required_source_fields",
                            "forbidden_uses",
                            "workorder_title",
                            "workorder_priority",
                        ],
                    },
                },
                "final_conclusions": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "bucket_id": {"type": "STRING"},
                            "final_bucket_relation": {
                                "type": "STRING",
                                "enum": bucket_relation_enum,
                            },
                            "final_classification_state": {
                                "type": "STRING",
                                "enum": classification_state_enum,
                            },
                            "final_decision": {
                                "type": "STRING",
                                "enum": ["keep", "correct", "block"],
                            },
                            "reason": {"type": "STRING"},
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
                "parent_granularity_reviews": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "decision": {
                                "type": "STRING",
                                "enum": [
                                    "accept_selected_level",
                                    "prefer_level",
                                    "taxonomy_gap",
                                    "source_quality_blocker",
                                    "code_patch_required",
                                ],
                            },
                            "preferred_level": {"type": "STRING"},
                            "reason": {"type": "STRING"},
                        },
                        "required": ["decision", "preferred_level", "reason"],
                    },
                },
            },
            "required": [
                "schema_version",
                "interpretation",
                "audit",
                "ai_tier2_proposals",
                "comparative_reviews",
                "final_conclusions",
                "parent_granularity_reviews",
            ],
        }
    return None


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for candidate in payload.get("candidates") or []:
        content = candidate.get("content") if isinstance(candidate, dict) else {}
        for part in (content or {}).get("parts") or []:
            if isinstance(part, dict) and part.get("text"):
                parts.append(str(part.get("text") or ""))
    return "\n".join(parts).strip()


def _gemini_usage(payload: dict[str, Any]) -> dict[str, int]:
    meta = (
        payload.get("usageMetadata")
        if isinstance(payload.get("usageMetadata"), dict)
        else {}
    )
    return {
        "input_tokens": int(meta.get("promptTokenCount") or 0),
        "output_tokens": int(meta.get("candidatesTokenCount") or 0),
        "thoughts_tokens": int(meta.get("thoughtsTokenCount") or 0),
        "total_tokens": int(meta.get("totalTokenCount") or 0),
    }


def _gemini_finish_reason(payload: dict[str, Any]) -> str:
    for candidate in payload.get("candidates") or []:
        if isinstance(candidate, dict) and candidate.get("finishReason"):
            return str(candidate.get("finishReason") or "")
    return ""


def _call_gemini_3_5_flash(
    *,
    schema_name: str,
    instructions: str,
    prompt: str,
    config: PostcloseAIReviewConfig,
    contract_validator: ContractValidator | None,
) -> tuple[str | None, dict[str, Any]]:
    status = _gemini_status_base(config, schema_name=schema_name)
    api_keys = _load_threshold_ai_gemini_keys()
    if config.gemini_key_rotation_enabled:
        api_keys = api_keys[:3]
    else:
        api_keys = api_keys[:1]
    if not api_keys:
        return None, {
            **status,
            "status": "unavailable",
            "reason": "GEMINI_API_KEY not configured",
        }
    request_prompt = _gemini_prompt(instructions, prompt, schema_name)
    errors: list[dict[str, str | int]] = []
    attempted_key_names: list[str] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        attempted_key_names.append(key_name)
        started = time.perf_counter()
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{config.gemini_model}:generateContent?key={api_key}"
            )
            body = {
                "contents": [{"role": "user", "parts": [{"text": request_prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": int(config.gemini_max_output_tokens),
                    "responseMimeType": "application/json",
                },
            }
            response_schema = _gemini_response_schema(schema_name)
            if response_schema is not None:
                body["generationConfig"]["responseSchema"] = response_schema
            req = urllib.request.Request(
                url,
                data=json.dumps(body, ensure_ascii=True).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(
                req, timeout=max(1, int(config.timeout_sec))
            ) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            raw_text = _extract_gemini_text(response_payload)
            finish_reason = _gemini_finish_reason(response_payload)
            usage = _gemini_usage(response_payload)
            contract_ok, contract_reason = _validator_ok(contract_validator, raw_text)
            gemini_status = {
                **status,
                "status": (
                    "success"
                    if contract_ok and finish_reason != "MAX_TOKENS"
                    else "contract_failed"
                ),
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_key_count": len(attempted_key_names),
                "configured_key_count": len(api_keys),
                "attempted_key_names": attempted_key_names,
                "gemini_key_slot_used": attempt_index,
                "gemini_key_rotation_attempts": len(attempted_key_names),
                "gemini_key_rotation_used": attempt_index > 1,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_context_chars": len(prompt),
                "prompt_chars": len(request_prompt),
                "output_chars": len(raw_text),
                "finish_reason": finish_reason,
                "gemini_contract_ok": bool(
                    contract_ok and finish_reason != "MAX_TOKENS"
                ),
                "gemini_contract_reason": (
                    "finish_reason_MAX_TOKENS"
                    if finish_reason == "MAX_TOKENS"
                    else contract_reason
                ),
                **usage,
            }
            if gemini_status["gemini_contract_ok"]:
                if errors:
                    gemini_status["prior_key_errors"] = errors[-3:]
                return raw_text, gemini_status
            errors.append(
                {
                    "key_name": key_name,
                    "error_type": "contract_failed",
                    "error": str(
                        gemini_status.get("gemini_contract_reason") or "contract_failed"
                    ),
                }
            )
        except urllib.error.HTTPError as exc:
            errors.append(
                {
                    "key_name": key_name,
                    "error_type": f"http_{exc.code}",
                    "error": _sanitize_error_message(
                        exc.read().decode("utf-8", errors="replace")
                    ),
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "key_name": key_name,
                    "error_type": type(exc).__name__,
                    "error": _sanitize_error_message(exc),
                }
            )
    return None, {
        **status,
        "status": "unavailable",
        "reason": "all Gemini 3.5 Flash attempts failed",
        "configured_key_count": len(api_keys),
        "attempted_key_count": len(attempted_key_names),
        "attempted_key_names": attempted_key_names,
        "gemini_key_rotation_attempts": len(attempted_key_names),
        "gemini_key_rotation_exhausted": True,
        "errors": errors[-3:],
        "gemini_contract_ok": False,
    }


def _bedrock_status_base(
    config: PostcloseAIReviewConfig, *, schema_name: str
) -> dict[str, Any]:
    return {
        **config.provider_status_fields(),
        "provider": "bedrock_qwen3",
        "model": config.bedrock_model_id,
        "schema_name": schema_name,
        "primary_provider": "bedrock_qwen3",
        "primary_model": config.bedrock_model_id,
        "failback_provider": config.failback_provider,
        "failback_used": False,
    }


def _call_bedrock_qwen3(
    *,
    schema_name: str,
    instructions: str,
    prompt: str,
    config: PostcloseAIReviewConfig,
    contract_validator: ContractValidator | None,
) -> tuple[str | None, dict[str, Any]]:
    status = _bedrock_status_base(config, schema_name=schema_name)
    schema = AI_RESPONSE_SCHEMA_REGISTRY.get(schema_name)
    if not isinstance(schema, dict):
        return None, {
            **status,
            "status": "unavailable",
            "reason": f"unknown_schema:{schema_name}",
        }
    keys = load_bedrock_api_keys_from_config()
    if not keys:
        return None, {
            **status,
            "status": "unavailable",
            "reason": "AWS_BEARER_TOKEN_BEDROCK not configured",
        }
    try:
        import boto3
        from botocore.config import Config
    except Exception as exc:
        return None, {
            **status,
            "status": "unavailable",
            "reason": f"bedrock import failed: {exc}",
        }

    errors: list[dict[str, str]] = []
    schema_payload = _normalize_bedrock_schema(schema)
    timeout_sec = max(int(config.timeout_sec), 1)
    for attempt_index, api_key in enumerate(keys, start=1):
        started = time.perf_counter()
        try:
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
            client = boto3.client(
                "bedrock-runtime",
                region_name=config.bedrock_region,
                config=Config(
                    connect_timeout=min(timeout_sec, 30),
                    read_timeout=timeout_sec,
                    retries={"max_attempts": 0},
                ),
            )
            response = client.converse(
                modelId=config.bedrock_model_id,
                system=[
                    {
                        "text": (
                            instructions
                            + "\nReturn one JSON object only. Do not include markdown or prose. "
                            + "Do not copy or echo input candidates. If candidate_reviews is required, "
                            + "its length must match the input candidate count."
                        )
                    }
                ],
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={
                    "maxTokens": int(config.bedrock_max_output_tokens),
                    "temperature": 0,
                },
                outputConfig={
                    "textFormat": {
                        "type": "json_schema",
                        "structure": {
                            "jsonSchema": {
                                "name": schema_name,
                                "description": f"{schema_name} structured postclose review",
                                "schema": json.dumps(schema_payload, ensure_ascii=True),
                            }
                        },
                    }
                },
            )
            raw_text = "\n".join(
                str(part.get("text") or "")
                for part in (
                    ((response.get("output") or {}).get("message") or {}).get("content")
                    or []
                )
                if isinstance(part, dict)
            ).strip()
            contract_ok, contract_reason = _validator_ok(contract_validator, raw_text)
            usage = response.get("usage") if isinstance(response, dict) else {}
            bedrock_status = {
                **status,
                "status": "success" if contract_ok else "contract_failed",
                "attempt_index": attempt_index,
                "attempted_key_count": len(keys),
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_tokens": int((usage or {}).get("inputTokens") or 0),
                "output_tokens": int((usage or {}).get("outputTokens") or 0),
                "total_tokens": int((usage or {}).get("totalTokens") or 0),
                "output_chars": len(raw_text),
                "bedrock_contract_ok": contract_ok,
                "bedrock_contract_reason": contract_reason,
            }
            if contract_ok:
                return raw_text, bedrock_status
            return None, bedrock_status
        except Exception as exc:
            errors.append(
                {
                    "attempt_index": str(attempt_index),
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )
    return None, {
        **status,
        "status": "unavailable",
        "reason": "all Bedrock Qwen3 attempts failed",
        "errors": errors[-3:],
        "bedrock_contract_ok": False,
    }


def _call_openai(
    *,
    schema_name: str,
    instructions: str,
    prompt: str,
    config: PostcloseAIReviewConfig,
    metadata: dict[str, str],
    contract_validator: ContractValidator | None = None,
    failback_used: bool = False,
    failback_reason: str = "",
    primary_status: dict[str, Any] | None = None,
) -> tuple[str | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
    except Exception as exc:
        return None, {
            "provider": "openai",
            "status": "unavailable",
            "reason": f"openai import failed: {exc}",
            **config.provider_status_fields(),
        }
    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {
            "provider": "openai",
            "status": "unavailable",
            "reason": "OPENAI_API_KEY not configured",
            **config.provider_status_fields(),
        }
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        started = time.perf_counter()
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=config.model,
                instructions=instructions,
                input=prompt,
                text={
                    "format": build_openai_response_text_format(schema_name),
                    "verbosity": "low",
                },
                reasoning={"effort": config.reasoning_effort},
                store=False,
                metadata={**metadata, "schema_name": schema_name},
                timeout=config.timeout_sec,
            )
            raw_text = _extract_openai_response_text(response)
            contract_ok, contract_reason = _validator_ok(contract_validator, raw_text)
            usage = getattr(response, "usage", None)
            status = {
                "provider": "openai",
                "status": "success" if contract_ok else "contract_failed",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_key_count": len(api_keys),
                "attempted_keys": len(api_keys),
                "attempted_models": [config.model],
                "model": config.model,
                "schema_name": schema_name,
                "reasoning_effort": config.reasoning_effort,
                "timeout_sec": config.timeout_sec,
                "attempt_role": config.attempt_role,
                "retry_reason": config.retry_reason,
                "config_env_prefix": config.env_prefix_name,
                "input_context_chars": len(prompt),
                "output_chars": len(raw_text),
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_tokens": (
                    int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
                ),
                "output_tokens": (
                    int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
                ),
                "total_tokens": (
                    int(getattr(usage, "total_tokens", 0) or 0) if usage else 0
                ),
                "primary_provider": config.primary_provider,
                "primary_model": (
                    config.bedrock_model_id
                    if config.primary_provider == "bedrock_qwen3"
                    else (
                        config.gemini_model
                        if config.primary_provider == "gemini_3_5_flash"
                        else config.model
                    )
                ),
                "failback_provider": config.failback_provider,
                "failback_used": bool(failback_used),
                "failback_reason": failback_reason,
                "openai_contract_ok": contract_ok,
                "openai_contract_reason": contract_reason,
            }
            if primary_status:
                status.update(
                    {
                        "primary_error_type": str(primary_status.get("status") or ""),
                        "primary_error_message": _sanitize_error_message(
                            primary_status.get("reason")
                            or primary_status.get("bedrock_contract_reason")
                            or primary_status.get("gemini_contract_reason")
                            or ""
                        ),
                        "primary_provider_status": primary_status,
                    }
                )
            if contract_ok:
                return raw_text, status
            return None, status
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "unavailable",
        "reason": "all OpenAI attempts failed",
        **config.provider_status_fields(),
        "errors": errors[-3:],
        "failback_used": bool(failback_used),
        "failback_reason": failback_reason,
    }


def call_postclose_structured_review(
    context: dict[str, Any],
    *,
    schema_name: str,
    instructions: str,
    config: PostcloseAIReviewConfig,
    metadata: dict[str, str],
    contract_validator: ContractValidator | None = None,
    ensure_ascii: bool = True,
) -> tuple[str | None, dict[str, Any]]:
    prompt = _prompt_text(context, ensure_ascii=ensure_ascii)
    if config.primary_provider == "bedrock_qwen3":
        raw_text, primary_status = _call_bedrock_qwen3(
            schema_name=schema_name,
            instructions=instructions,
            prompt=prompt,
            config=config,
            contract_validator=contract_validator,
        )
        if raw_text is not None:
            primary_status["input_context_chars"] = len(prompt)
            return raw_text, primary_status
        if config.failback_provider == "openai":
            failback_reason = str(
                primary_status.get("status") or "bedrock_qwen3_failed"
            )
            return _call_openai(
                schema_name=schema_name,
                instructions=instructions,
                prompt=prompt,
                config=config,
                metadata=metadata,
                contract_validator=contract_validator,
                failback_used=True,
                failback_reason=failback_reason,
                primary_status=primary_status,
            )
        return None, primary_status
    if config.primary_provider == "openai":
        raw_text, primary_status = _call_openai(
            schema_name=schema_name,
            instructions=instructions,
            prompt=prompt,
            config=config,
            metadata=metadata,
            contract_validator=contract_validator,
        )
        if raw_text is not None:
            return raw_text, primary_status
        if config.failback_provider == "bedrock_qwen3":
            failback_config = PostcloseAIReviewConfig(
                **{
                    **config.__dict__,
                    "primary_provider": "bedrock_qwen3",
                    "failback_provider": "none",
                    "attempt_role": "failback",
                    "retry_reason": str(
                        primary_status.get("status") or "openai_failed"
                    ),
                }
            )
            failback_raw, failback_status = _call_bedrock_qwen3(
                schema_name=schema_name,
                instructions=instructions,
                prompt=prompt,
                config=failback_config,
                contract_validator=contract_validator,
            )
            return failback_raw, {
                **failback_status,
                "primary_provider": "openai",
                "primary_model": config.model,
                "failback_provider": "bedrock_qwen3",
                "failback_model": config.bedrock_model_id,
                "failback_used": failback_raw is not None,
                "failback_reason": str(primary_status.get("status") or "openai_failed"),
                "primary_provider_status": primary_status,
                "primary_error_type": str(primary_status.get("status") or ""),
                "primary_error_message": _sanitize_error_message(
                    primary_status.get("reason")
                    or primary_status.get("openai_contract_reason")
                    or ""
                ),
            }
        return None, primary_status
    if config.primary_provider == "gemini_3_5_flash":
        raw_text, primary_status = _call_gemini_3_5_flash(
            schema_name=schema_name,
            instructions=instructions,
            prompt=prompt,
            config=config,
            contract_validator=contract_validator,
        )
        if raw_text is not None:
            primary_status["input_context_chars"] = len(prompt)
            return raw_text, primary_status
        if config.failback_provider == "openai":
            failback_reason = str(
                primary_status.get("status") or "gemini_3_5_flash_failed"
            )
            return _call_openai(
                schema_name=schema_name,
                instructions=instructions,
                prompt=prompt,
                config=config,
                metadata=metadata,
                contract_validator=contract_validator,
                failback_used=True,
                failback_reason=failback_reason,
                primary_status=primary_status,
            )
        return None, primary_status
    return _call_openai(
        schema_name=schema_name,
        instructions=instructions,
        prompt=prompt,
        config=config,
        metadata=metadata,
        contract_validator=contract_validator,
    )
