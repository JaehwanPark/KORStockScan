import json

from src.engine import bedrock_nova_lite_shadow as runtime_mod
from src.tests import bedrock_nova_lite_shadow as mod


def test_shadow_disabled_does_not_enqueue():
    manager = mod.BedrockNovaLiteShadowManager(enabled=False)
    assert manager.should_shadow(model_name="gpt-5.4-mini", require_json=True) is False


def test_shadow_filter_only_accepts_gpt54_mini_json():
    manager = mod.BedrockNovaLiteShadowManager(enabled=True)
    assert manager.should_shadow(model_name="gpt-5.4-mini", require_json=True) is True
    assert manager.should_shadow(model_name="gpt-5-nano", require_json=True) is False
    assert manager.should_shadow(model_name="gpt-5.4", require_json=True) is False
    assert manager.should_shadow(model_name="gpt-5.4-mini", require_json=False) is False


def test_runtime_manager_can_target_gpt5_nano_only(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_TARGET_MODELS", "gpt-5-nano")
    monkeypatch.setattr(runtime_mod, "_RUNTIME_MANAGER", None)
    monkeypatch.setattr(runtime_mod, "_RUNTIME_SIGNATURE", None)

    manager = runtime_mod.runtime_manager()

    assert manager.should_shadow(model_name="gpt-5-nano", require_json=True) is True
    assert manager.should_shadow(model_name="gpt-5.4-mini", require_json=True) is False
    assert manager.openai_input_usd_per_1m == 0.05
    assert manager.openai_output_usd_per_1m == 0.40


def test_loads_bedrock_api_key_from_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config_prod.json"
    config_path.write_text(json.dumps({"BEDROCK_API_KEY": "test-key"}), encoding="utf-8")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)

    assert mod.load_bedrock_api_key_from_config(config_path) == "test-key"
    assert mod.configure_bedrock_api_key_env(config_path) is True
    assert mod.os.environ["AWS_BEARER_TOKEN_BEDROCK"] == "test-key"


def test_parse_normalize_and_cost():
    parsed, error = mod.parse_nova_response_text("```json\n{\"action\":\"wait\",\"score\":\"66\"}\n```")
    assert error is None
    assert parsed == {"action": "wait", "score": "66"}
    assert mod.normalize_action_score(parsed) == ("WAIT", 66)
    assert mod.normalize_action_score({"action": "hold", "confidence": 0.85}) == ("HOLD", 85)
    assert mod.estimate_cost_usd(1_000_000, 1_000_000, input_usd_per_1m=0.035, output_usd_per_1m=0.14) == 0.175
    assert (
        mod.estimate_nova_cost_usd(
            input_tokens=100,
            output_tokens=10,
            cache_read_input_tokens=1000,
            cache_write_input_tokens=2000,
            input_usd_per_1m=1.0,
            output_usd_per_1m=2.0,
            cache_read_input_usd_per_1m=0.1,
            cache_write_input_usd_per_1m=1.25,
        )
        == 0.00272
    )


def test_worker_error_and_queue_full_do_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date=None: tmp_path / "rows.jsonl")

    class FailingClient:
        def converse(self, **kwargs):
            raise RuntimeError("aws down")

    manager = mod.BedrockNovaLiteShadowManager(
        enabled=True,
        client_factory=lambda: FailingClient(),
        queue_max=1,
        workers=1,
    )
    assert manager.enqueue(
        prompt="p",
        user_input="u",
        openai_payload={"action": "WAIT", "score": 50},
        transport_meta={"openai_request_id": "req-1"},
        request_meta={"endpoint_name": "analyze_target", "symbol": "000001"},
    ) in {True, False}
    manager._queue.join()
    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["error_type"] == "RuntimeError"
    assert rows[0]["decision_authority"] == "shadow_observation_only"


def test_successful_worker_writes_comparison_row(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date=None: tmp_path / "rows.jsonl")

    class Client:
        def converse(self, **kwargs):
            return {
                "output": {"message": {"content": [{"text": '{"action":"BUY","score":79}'}]}},
                "usage": {"inputTokens": 90, "outputTokens": 12},
            }

    manager = mod.BedrockNovaLiteShadowManager(enabled=True, client_factory=lambda: Client(), workers=1)
    assert manager.enqueue(
        prompt="p",
        user_input="u",
        openai_payload={"action": "BUY", "score": 81},
        transport_meta={"openai_request_id": "req-1", "openai_input_tokens": 100, "openai_output_tokens": 20},
        request_meta={
            "endpoint_name": "analyze_target",
            "symbol": "000001",
            "cache_key": "ck",
            "record_id": "101",
            "sim_record_id": "SIM-1",
            "sim_parent_record_id": "PARENT-1",
            "entry_adm_candidate_id": "ADM-1",
            "source_event_stage": "scalp_sim_holding_review",
        },
    )
    manager._queue.join()
    row = json.loads((tmp_path / "rows.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["nova_action"] == "BUY"
    assert row["action_match"] is True
    assert row["score_delta"] == -2
    assert row["cache_key"] == "ck"
    assert row["record_id"] == "101"
    assert row["sim_record_id"] == "SIM-1"
    assert row["sim_parent_record_id"] == "PARENT-1"
    assert row["entry_adm_candidate_id"] == "ADM-1"
    assert row["source_event_stage"] == "scalp_sim_holding_review"
    assert row["region_name"] == "ap-northeast-2"


def test_prompt_cache_adds_cachepoint_and_records_cache_usage(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date=None: tmp_path / "rows.jsonl")
    calls = []

    class Client:
        def converse(self, **kwargs):
            calls.append(kwargs)
            return {
                "output": {"message": {"content": [{"text": '{"action":"WAIT","score":55}'}]}},
                "usage": {
                    "inputTokens": 40,
                    "outputTokens": 9,
                    "cacheReadInputTokens": 1000,
                    "cacheWriteInputTokens": 1200,
                },
            }

    manager = mod.BedrockNovaLiteShadowManager(
        enabled=True,
        client_factory=lambda: Client(),
        workers=1,
        prompt_cache_enabled=True,
    )
    assert manager.enqueue(
        prompt="p",
        user_input="u",
        openai_payload={"action": "WAIT", "score": 55},
        transport_meta={"openai_request_id": "req-1", "openai_input_tokens": 100, "openai_output_tokens": 20},
        request_meta={"endpoint_name": "analyze_target", "symbol": "000001"},
    )
    manager._queue.join()
    assert calls[0]["system"][-1] == {"cachePoint": {"type": "default"}}
    row = json.loads((tmp_path / "rows.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["nova_prompt_cache_enabled"] is True
    assert row["nova_cache_read_input_tokens"] == 1000
    assert row["nova_cache_write_input_tokens"] == 1200
    assert row["nova_total_input_tokens"] == 2240
