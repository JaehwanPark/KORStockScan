"""Postclose AI reviewer model/reasoning/timeout configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


VALID_REASONING_EFFORTS = {"minimal", "low", "medium", "high"}


@dataclass(frozen=True)
class PostcloseAIReviewConfig:
    artifact: str
    model: str
    reasoning_effort: str
    timeout_sec: int
    attempt_role: str = "primary"
    retry_reason: str | None = None
    env_prefix: str | None = None
    primary_provider: str = "openai"
    failback_provider: str = "openai"
    bedrock_model_id: str = "qwen.qwen3-235b-a22b-2507-v1:0"
    bedrock_region: str = "us-west-2"
    bedrock_max_output_tokens: int = 8192
    gemini_model: str = "gemini-3.5-flash"
    gemini_shard_size: int = 10
    gemini_max_output_tokens: int = 8192
    gemini_key_rotation_enabled: bool = True

    @property
    def env_prefix_name(self) -> str:
        return self.env_prefix or f"KORSTOCKSCAN_{self.artifact.upper()}_AI"

    def provider_status_fields(self) -> dict[str, object]:
        return {
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "timeout_sec": self.timeout_sec,
            "attempt_role": self.attempt_role,
            "retry_reason": self.retry_reason,
            "config_env_prefix": self.env_prefix_name,
            "primary_provider": self.primary_provider,
            "failback_provider": self.failback_provider,
            "bedrock_model_id": self.bedrock_model_id,
            "bedrock_region": self.bedrock_region,
            "bedrock_max_output_tokens": self.bedrock_max_output_tokens,
            "gemini_model": self.gemini_model,
            "gemini_shard_size": self.gemini_shard_size,
            "gemini_max_output_tokens": self.gemini_max_output_tokens,
            "gemini_key_rotation_enabled": self.gemini_key_rotation_enabled,
        }


def _env_text(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip() or default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def normalize_reasoning_effort(value: str, default: str) -> str:
    effort = str(value or "").strip().lower()
    if effort in VALID_REASONING_EFFORTS:
        return effort
    fallback = str(default or "").strip().lower()
    return fallback if fallback in VALID_REASONING_EFFORTS else "low"


def resolve_postclose_ai_review_config(
    artifact: str,
    *,
    default_model: str,
    default_reasoning_effort: str,
    default_timeout_sec: int = 180,
    attempt_role: str = "primary",
    retry_reason: str | None = None,
    env_prefix: str | None = None,
) -> PostcloseAIReviewConfig:
    prefix = env_prefix or f"KORSTOCKSCAN_{artifact.upper()}_AI"
    if attempt_role == "retry":
        model = _env_text(f"{prefix}_RETRY_MODEL", default_model)
        reasoning = _env_text(f"{prefix}_RETRY_REASONING_EFFORT", default_reasoning_effort)
    else:
        model = _env_text(f"{prefix}_MODEL", default_model)
        reasoning = _env_text(f"{prefix}_REASONING_EFFORT", default_reasoning_effort)
    timeout_sec = max(1, _env_int(f"{prefix}_TIMEOUT_SEC", default_timeout_sec))
    if model == "gpt-5.4-mini":
        default_primary_provider = "bedrock_qwen3"
    elif model == "gpt-5.4":
        default_primary_provider = "gemini_3_5_flash"
    else:
        default_primary_provider = "openai"
    primary_provider = _env_text(f"{prefix}_PRIMARY_PROVIDER", default_primary_provider).lower()
    failback_provider = _env_text(f"{prefix}_FAILBACK_PROVIDER", "openai").lower()
    bedrock_model_id = _env_text(f"{prefix}_BEDROCK_MODEL_ID", "qwen.qwen3-235b-a22b-2507-v1:0")
    bedrock_region = _env_text(f"{prefix}_BEDROCK_REGION", "us-west-2")
    bedrock_max_output_tokens = max(1, _env_int(f"{prefix}_BEDROCK_MAX_OUTPUT_TOKENS", 8192))
    gemini_model = _env_text(f"{prefix}_GEMINI_MODEL", "gemini-3.5-flash")
    gemini_shard_size = max(1, _env_int(f"{prefix}_GEMINI_SHARD_SIZE", 10))
    gemini_max_output_tokens = max(1, _env_int(f"{prefix}_GEMINI_MAX_OUTPUT_TOKENS", 8192))
    gemini_key_rotation_enabled = _env_bool(f"{prefix}_GEMINI_KEY_ROTATION_ENABLED", True)
    return PostcloseAIReviewConfig(
        artifact=artifact,
        model=model,
        reasoning_effort=normalize_reasoning_effort(reasoning, default_reasoning_effort),
        timeout_sec=timeout_sec,
        attempt_role=attempt_role,
        retry_reason=retry_reason,
        env_prefix=prefix,
        primary_provider=primary_provider,
        failback_provider=failback_provider,
        bedrock_model_id=bedrock_model_id,
        bedrock_region=bedrock_region,
        bedrock_max_output_tokens=bedrock_max_output_tokens,
        gemini_model=gemini_model,
        gemini_shard_size=gemini_shard_size,
        gemini_max_output_tokens=gemini_max_output_tokens,
        gemini_key_rotation_enabled=gemini_key_rotation_enabled,
    )


def first_wave_retry_reason(
    *,
    ai_status: str,
    audit_status: object,
    forbidden_use_violations: list[object] | None,
    missing_ai_proposal_count: int = 0,
    missing_comparative_review_count: int = 0,
    missing_final_conclusion_count: int = 0,
) -> str | None:
    if ai_status != "parsed":
        return f"ai_status_{ai_status}"
    return None


def parsed_review_followup_reasons(
    *,
    ai_status: str,
    audit_status: object,
    forbidden_use_violations: list[object] | None,
    missing_ai_proposal_count: int = 0,
    missing_comparative_review_count: int = 0,
    missing_final_conclusion_count: int = 0,
) -> list[str]:
    if ai_status != "parsed":
        return []
    reasons: list[str] = []
    if str(audit_status or "") != "pass":
        reasons.append(f"audit_status_{audit_status or 'missing'}")
    if forbidden_use_violations:
        reasons.append("forbidden_use_violation")
    if missing_ai_proposal_count > 0:
        reasons.append(f"missing_ai_tier2_proposal:{missing_ai_proposal_count}")
    if missing_comparative_review_count > 0:
        reasons.append(f"missing_comparative_review:{missing_comparative_review_count}")
    if missing_final_conclusion_count > 0:
        reasons.append(f"missing_final_conclusion:{missing_final_conclusion_count}")
    return reasons
