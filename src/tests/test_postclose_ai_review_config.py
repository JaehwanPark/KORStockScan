import os

from src.engine.ai.postclose_review_config import (
    first_wave_retry_reason,
    parsed_review_followup_reasons,
    resolve_postclose_ai_review_config,
)
from src.engine import lifecycle_bucket_discovery as lifecycle_mod
from src.engine import runtime_apply_gap_audit as runtime_gap_mod
from src.engine import swing_lifecycle_audit as swing_audit_mod
from src.engine import swing_lifecycle_bucket_discovery as swing_bucket_mod
from src.engine.ai import postclose_structured_review_provider as provider_mod


def test_artifact_env_overrides_global_default(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_MODEL", "gpt-custom")
    monkeypatch.setenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_REASONING_EFFORT", "high")
    monkeypatch.setenv("KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_TIMEOUT_SEC", "77")

    config = resolve_postclose_ai_review_config(
        "PRODUCER_GAP_DISCOVERY",
        default_model="gpt-deep-fallback",
        default_reasoning_effort="low",
        default_timeout_sec=180,
    )

    assert config.model == "gpt-custom"
    assert config.reasoning_effort == "high"
    assert config.timeout_sec == 77
    assert config.env_prefix_name == "KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI"
    assert config.provider_status_fields()["config_env_prefix"] == "KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI"


def test_lifecycle_bucket_shard_defaults_preserve_scalping_review_contract(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)

    live = lifecycle_mod._ai_review_config_for_shard("live_contract_review")
    source = lifecycle_mod._ai_review_config_for_shard("sim_policy_review")

    assert live.model == "gpt-5.4"
    assert live.reasoning_effort == "low"
    assert live.primary_provider == "openai"
    assert live.failback_provider == "openai"
    assert source.model == "gpt-5.4"
    assert source.reasoning_effort == "low"
    assert source.primary_provider == "openai"
    assert source.failback_provider == "openai"


def test_lifecycle_bucket_source_only_env_overrides_do_not_affect_live(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI_MODEL", "gpt-source-only")
    monkeypatch.setenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI_REASONING_EFFORT", "high")
    monkeypatch.setenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_TIMEOUT_SEC", "91")

    live = lifecycle_mod._ai_review_config_for_shard("live_contract_review")
    source = lifecycle_mod._ai_review_config_for_shard("gap_workorder_review")

    assert live.model == "gpt-5.4"
    assert live.reasoning_effort == "low"
    assert live.timeout_sec == 91
    assert source.model == "gpt-source-only"
    assert source.reasoning_effort == "high"
    assert source.timeout_sec == 91


def test_lifecycle_bucket_primary_provider_env_override_is_preserved(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI_PRIMARY_PROVIDER", "bedrock_qwen3")
    monkeypatch.setenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI_FAILBACK_PROVIDER", "none")

    source = lifecycle_mod._ai_review_config_for_shard("sim_policy_review")

    assert source.primary_provider == "bedrock_qwen3"
    assert source.failback_provider == "none"


def test_swing_lifecycle_bucket_discovery_uses_29_baseline_mini_medium_default(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)

    config = swing_bucket_mod._ai_review_config()

    assert config.model == "gpt-5.4-mini"
    assert config.reasoning_effort == "medium"
    assert config.timeout_sec == 180
    assert config.primary_provider == "bedrock_qwen3"
    assert config.failback_provider == "openai"


def test_swing_lifecycle_bucket_discovery_primary_provider_env_override_is_preserved(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PRIMARY_PROVIDER", "openai")
    monkeypatch.setenv("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_FAILBACK_PROVIDER", "bedrock_qwen3")

    config = swing_bucket_mod._ai_review_config()

    assert config.primary_provider == "openai"
    assert config.failback_provider == "bedrock_qwen3"


def test_swing_threshold_review_uses_individual_mini_medium_default(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_SWING_THRESHOLD_AI_REVIEW"):
            monkeypatch.delenv(key, raising=False)

    config = swing_audit_mod._swing_threshold_ai_review_config()

    assert config.model == "gpt-5.4-mini"
    assert config.reasoning_effort == "medium"
    assert config.timeout_sec == 180
    assert config.primary_provider == "bedrock_qwen3"
    assert config.failback_provider == "openai"
    assert config.bedrock_model_id == "qwen.qwen3-235b-a22b-2507-v1:0"
    assert config.bedrock_region == "us-west-2"
    assert config.bedrock_max_output_tokens == 8192


def test_postclose_common_defaults_preserve_existing_provider_mapping(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_TEST_ARTIFACT_AI"):
            monkeypatch.delenv(key, raising=False)

    mini = resolve_postclose_ai_review_config(
        "TEST_ARTIFACT",
        default_model="gpt-5.4-mini",
        default_reasoning_effort="medium",
    )
    deep = resolve_postclose_ai_review_config(
        "TEST_ARTIFACT",
        default_model="gpt-5.4",
        default_reasoning_effort="medium",
    )

    assert mini.primary_provider == "bedrock_qwen3"
    assert mini.failback_provider == "openai"
    assert deep.primary_provider == "gemini_3_5_flash"
    assert deep.failback_provider == "openai"


def test_postclose_qwen3_env_overrides(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_TEST_ARTIFACT_AI"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_PRIMARY_PROVIDER", "openai")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_FAILBACK_PROVIDER", "none")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_BEDROCK_MODEL_ID", "qwen.custom")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_BEDROCK_REGION", "ap-northeast-2")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_BEDROCK_MAX_OUTPUT_TOKENS", "1234")

    config = resolve_postclose_ai_review_config(
        "TEST_ARTIFACT",
        default_model="gpt-5.4-mini",
        default_reasoning_effort="medium",
    )

    assert config.primary_provider == "openai"
    assert config.failback_provider == "none"
    assert config.bedrock_model_id == "qwen.custom"
    assert config.bedrock_region == "ap-northeast-2"
    assert config.bedrock_max_output_tokens == 1234


def test_postclose_gpt54_keeps_gemini_fields_compat_default(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_TEST_ARTIFACT_AI"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_GEMINI_MODEL", "gemini-custom")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_GEMINI_SHARD_SIZE", "7")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_GEMINI_MAX_OUTPUT_TOKENS", "4096")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_GEMINI_KEY_ROTATION_ENABLED", "false")

    config = resolve_postclose_ai_review_config(
        "TEST_ARTIFACT",
        default_model="gpt-5.4",
        default_reasoning_effort="low",
    )

    assert config.primary_provider == "gemini_3_5_flash"
    assert config.failback_provider == "openai"
    assert config.gemini_model == "gemini-custom"
    assert config.gemini_shard_size == 7
    assert config.gemini_max_output_tokens == 4096
    assert config.gemini_key_rotation_enabled is False


def test_structured_review_openai_contract_failure_uses_bedrock_qwen3_failback(monkeypatch):
    calls = []
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_PRIMARY_PROVIDER", "openai")
    monkeypatch.setenv("KORSTOCKSCAN_TEST_ARTIFACT_AI_FAILBACK_PROVIDER", "bedrock_qwen3")
    config = resolve_postclose_ai_review_config(
        "TEST_ARTIFACT",
        default_model="gpt-5.4",
        default_reasoning_effort="medium",
    )

    def fake_openai(**kwargs):
        calls.append(("openai", kwargs["config"].model))
        return None, {"provider": "openai", "status": "contract_failed", "openai_contract_reason": "parse_rejected"}

    def fake_bedrock(**kwargs):
        calls.append(("bedrock_qwen3", kwargs["config"].model))
        return "{}", {"provider": "bedrock_qwen3", "status": "success"}

    monkeypatch.setattr(provider_mod, "_call_openai", fake_openai)
    monkeypatch.setattr(provider_mod, "_call_bedrock_qwen3", fake_bedrock)

    raw, status = provider_mod.call_postclose_structured_review(
        {"candidate_ids": ["a"]},
        schema_name="runtime_apply_gap_ai_review_v1",
        instructions="Return JSON.",
        config=config,
        metadata={"endpoint_name": "test"},
        contract_validator=lambda raw_text: (True, ""),
    )

    assert raw == "{}"
    assert calls == [("openai", "gpt-5.4"), ("bedrock_qwen3", "gpt-5.4")]
    assert status["primary_provider"] == "openai"
    assert status["failback_provider"] == "bedrock_qwen3"
    assert status["failback_used"] is True


def test_runtime_apply_gap_audit_uses_individual_env_not_global_deep(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_RUNTIME_APPLY_GAP_AUDIT") or key.startswith("RUNTIME_APPLY_GAP_AI_REVIEW"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_RUNTIME_APPLY_GAP_AUDIT_AI_MODEL", "gpt-runtime-gap")
    monkeypatch.setenv("KORSTOCKSCAN_RUNTIME_APPLY_GAP_AUDIT_AI_REASONING_EFFORT", "medium")
    monkeypatch.setenv("KORSTOCKSCAN_RUNTIME_APPLY_GAP_AUDIT_AI_TIMEOUT_SEC", "123")

    config = runtime_gap_mod._ai_review_config()

    assert config.model == "gpt-runtime-gap"
    assert config.reasoning_effort == "medium"
    assert config.timeout_sec == 123
    assert config.env_prefix_name == "KORSTOCKSCAN_RUNTIME_APPLY_GAP_AUDIT_AI"


def test_retry_reason_is_limited_to_unparsed_ai_response():
    assert (
        first_wave_retry_reason(
            ai_status="parse_rejected",
            audit_status=None,
            forbidden_use_violations=None,
        )
        == "ai_status_parse_rejected"
    )
    assert (
        first_wave_retry_reason(
            ai_status="parsed",
            audit_status="correction_required",
            forbidden_use_violations=[],
            missing_ai_proposal_count=1,
        )
        is None
    )


def test_parsed_review_followup_reasons_are_not_retry_reasons():
    reasons = parsed_review_followup_reasons(
        ai_status="parsed",
        audit_status="correction_required",
        forbidden_use_violations=["attempted_runtime_apply"],
        missing_ai_proposal_count=2,
        missing_comparative_review_count=1,
    )

    assert "audit_status_correction_required" in reasons
    assert "forbidden_use_violation" in reasons
    assert "missing_ai_tier2_proposal:2" in reasons
    assert "missing_comparative_review:1" in reasons
