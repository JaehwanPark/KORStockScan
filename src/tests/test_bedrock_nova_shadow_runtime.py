from src.engine.bedrock_nova_provider import BedrockNovaResult, lite_v2_profile_from_env
from src.engine.bedrock_nova_shadow_runtime import BedrockNovaShadowManager, NovaShadowJob


class _Provider:
    def converse(self, *, prompt, user_input, profile):
        return BedrockNovaResult(
            payload={"action": "HOLD", "score": 55, "reason": "shadow"},
            raw_text='{"action":"HOLD","score":55,"reason":"shadow"}',
            parse_ok=True,
            parse_error="",
            model_id=profile.model_id,
            region_name=profile.region_name,
            key_index=0,
            latency_ms=321,
            input_tokens=12,
            output_tokens=7,
            cache_read_input_tokens=0,
            cache_write_input_tokens=0,
            total_input_tokens=12,
            estimated_cost_usd=0.00001,
            attempted_key_count=1,
        )


def test_lite_v2_shadow_success_row_uses_inference_profile(monkeypatch, tmp_path):
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID", raising=False)
    profile = lite_v2_profile_from_env()
    manager = BedrockNovaShadowManager(
        enabled=True,
        report_dir=tmp_path,
        event_type="bedrock_nova_lite_v2_shadow",
        target_model_name="gpt-5.4-mini",
        profile=profile,
        openai_input_usd_per_1m=0.06,
        openai_output_usd_per_1m=0.24,
        provider=_Provider(),
    )
    job = NovaShadowJob(
        prompt="p",
        user_input="u",
        openai_payload={"action": "HOLD", "score": 50},
        transport_meta={"openai_input_tokens": 10, "openai_output_tokens": 4},
        request_meta={
            "endpoint_name": "holding_flow",
            "baseline_bedrock_model_id": "apac.amazon.nova-lite-v1:0",
        },
    )

    row = manager._call_and_build_row(job)

    assert row["candidate_bedrock_model_id"] == "global.amazon.nova-2-lite-v1:0"
    assert row["v2_parse_ok"] is True
    assert row["v1_v2_action_match"] is True
    assert row["v1_v2_score_delta"] == 5
    assert row["decision_authority"] == "shadow_observation_only"
    assert row["runtime_effect"] is False
