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


def test_lifecycle_bucket_shard_defaults_split_live_and_source_only(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)

    live = lifecycle_mod._ai_review_config_for_shard("live_contract_review")
    source = lifecycle_mod._ai_review_config_for_shard("sim_policy_review")

    assert live.model == "gpt-5.4"
    assert live.reasoning_effort == "low"
    assert source.model == "gpt-5.4-mini"
    assert source.reasoning_effort == "medium"


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


def test_swing_lifecycle_bucket_discovery_uses_source_only_mini_medium_default(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY"):
            monkeypatch.delenv(key, raising=False)

    config = swing_bucket_mod._ai_review_config()

    assert config.model == "gpt-5.4-mini"
    assert config.reasoning_effort == "medium"
    assert config.timeout_sec == 180


def test_swing_threshold_review_uses_individual_mini_medium_default(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("KORSTOCKSCAN_SWING_THRESHOLD_AI_REVIEW"):
            monkeypatch.delenv(key, raising=False)

    config = swing_audit_mod._swing_threshold_ai_review_config()

    assert config.model == "gpt-5.4-mini"
    assert config.reasoning_effort == "medium"
    assert config.timeout_sec == 180


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
