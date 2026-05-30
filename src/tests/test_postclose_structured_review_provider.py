from src.engine.ai.postclose_review_config import PostcloseAIReviewConfig
from src.engine.ai import postclose_structured_review_provider as mod


def _config(model="gpt-5.4-mini", primary_provider="bedrock_qwen3"):
    return PostcloseAIReviewConfig(
        artifact="TEST_ARTIFACT",
        model=model,
        reasoning_effort="medium",
        timeout_sec=180,
        primary_provider=primary_provider,
        failback_provider="openai",
        bedrock_model_id="qwen.qwen3-235b-a22b-2507-v1:0",
        bedrock_region="us-west-2",
        bedrock_max_output_tokens=8192,
    )


def test_qwen3_success_skips_openai(monkeypatch):
    calls = {"bedrock": 0, "openai": 0}

    def bedrock(**kwargs):
        calls["bedrock"] += 1
        return '{"ok":true}', {"provider": "bedrock_qwen3", "status": "success"}

    def openai(**kwargs):
        calls["openai"] += 1
        return '{"openai":true}', {"provider": "openai", "status": "success"}

    monkeypatch.setattr(mod, "_call_bedrock_qwen3", bedrock)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"ok":true}'
    assert status["provider"] == "bedrock_qwen3"
    assert calls == {"bedrock": 1, "openai": 0}


def test_qwen3_unavailable_falls_back_to_openai(monkeypatch):
    def bedrock(**kwargs):
        return None, {"provider": "bedrock_qwen3", "status": "unavailable", "reason": "boom"}

    def openai(**kwargs):
        assert kwargs["failback_used"] is True
        assert kwargs["failback_reason"] == "unavailable"
        return '{"openai":true}', {"provider": "openai", "status": "success", "failback_used": True}

    monkeypatch.setattr(mod, "_call_bedrock_qwen3", bedrock)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"openai":true}'
    assert status["provider"] == "openai"
    assert status["failback_used"] is True


def test_qwen3_contract_failure_falls_back_to_openai(monkeypatch):
    def bedrock(**kwargs):
        return None, {
            "provider": "bedrock_qwen3",
            "status": "contract_failed",
            "bedrock_contract_ok": False,
            "bedrock_contract_reason": "missing_candidate_reviews",
        }

    def openai(**kwargs):
        assert kwargs["primary_status"]["bedrock_contract_reason"] == "missing_candidate_reviews"
        return '{"openai":true}', {"provider": "openai", "status": "success", "failback_used": True}

    monkeypatch.setattr(mod, "_call_bedrock_qwen3", bedrock)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"openai":true}'
    assert status["provider"] == "openai"


def test_gpt54_uses_openai_only(monkeypatch):
    calls = {"bedrock": 0, "openai": 0}

    def bedrock(**kwargs):
        calls["bedrock"] += 1
        return '{"bedrock":true}', {"provider": "bedrock_qwen3", "status": "success"}

    def openai(**kwargs):
        calls["openai"] += 1
        return '{"openai":true}', {"provider": "openai", "status": "success"}

    monkeypatch.setattr(mod, "_call_bedrock_qwen3", bedrock)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(model="gpt-5.4", primary_provider="openai"),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"openai":true}'
    assert status["provider"] == "openai"
    assert calls == {"bedrock": 0, "openai": 1}


def test_gpt54_gemini_success_skips_openai(monkeypatch):
    calls = {"gemini": 0, "openai": 0}

    def gemini(**kwargs):
        calls["gemini"] += 1
        return '{"gemini":true}', {"provider": "gemini", "status": "success", "gemini_key_slot_used": 1}

    def openai(**kwargs):
        calls["openai"] += 1
        return '{"openai":true}', {"provider": "openai", "status": "success"}

    monkeypatch.setattr(mod, "_call_gemini_3_5_flash", gemini)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(model="gpt-5.4", primary_provider="gemini_3_5_flash"),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"gemini":true}'
    assert status["provider"] == "gemini"
    assert calls == {"gemini": 1, "openai": 0}


def test_gpt54_gemini_failure_falls_back_to_openai(monkeypatch):
    def gemini(**kwargs):
        return None, {
            "provider": "gemini",
            "status": "unavailable",
            "reason": "all Gemini 3.5 Flash attempts failed",
            "gemini_key_rotation_exhausted": True,
        }

    def openai(**kwargs):
        assert kwargs["failback_used"] is True
        assert kwargs["failback_reason"] == "unavailable"
        assert kwargs["primary_status"]["gemini_key_rotation_exhausted"] is True
        return '{"openai":true}', {"provider": "openai", "status": "success", "failback_used": True}

    monkeypatch.setattr(mod, "_call_gemini_3_5_flash", gemini)
    monkeypatch.setattr(mod, "_call_openai", openai)

    raw, status = mod.call_postclose_structured_review(
        {"x": 1},
        schema_name="threshold_ai_correction_v1",
        instructions="Return JSON.",
        config=_config(model="gpt-5.4", primary_provider="gemini_3_5_flash"),
        metadata={"endpoint_name": "test", "report_type": "test"},
    )

    assert raw == '{"openai":true}'
    assert status["provider"] == "openai"
    assert status["failback_used"] is True


def test_gemini_has_lifecycle_bucket_response_schema():
    schema = mod._gemini_response_schema("lifecycle_bucket_discovery_review_v1")

    assert schema is not None
    assert "ai_tier2_proposals" in schema["properties"]
    assert "comparative_reviews" in schema["properties"]
    assert "final_conclusions" in schema["properties"]
    assert "parent_granularity_reviews" in schema["properties"]
