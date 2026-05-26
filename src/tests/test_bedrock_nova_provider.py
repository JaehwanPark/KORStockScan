import json

from src.engine import bedrock_nova_provider as mod


def test_load_bedrock_api_keys_from_config_orders_suffixes(tmp_path, monkeypatch):
    config_path = tmp_path / "config_prod.json"
    config_path.write_text(
        json.dumps(
            {
                "BEDROCK_API_KEY_3": "key-3",
                "BEDROCK_API_KEY": "key-1",
                "BEDROCK_API_KEY_2": "key-2",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)

    assert mod.load_bedrock_api_keys_from_config(config_path) == ["key-1", "key-2", "key-3"]


def test_provider_rotates_keys_on_retryable_error():
    calls = []

    class Client:
        def __init__(self, key_index):
            self.key_index = key_index

        def converse(self, **kwargs):
            calls.append((self.key_index, kwargs))
            if self.key_index == 0:
                raise RuntimeError("429 throttling")
            return {
                "output": {"message": {"content": [{"text": '{"action":"WAIT","score":61}'}]}},
                "usage": {"inputTokens": 10, "outputTokens": 5},
            }

    provider = mod.BedrockNovaProvider(
        api_keys=["key-1", "key-2"],
        client_factory=lambda key_index, api_key, region_name, timeout_ms: Client(key_index),
    )
    result = provider.converse(prompt="p", user_input="u", profile=mod.lite_profile_from_env())

    assert [idx for idx, _ in calls] == [0, 1]
    assert result.payload["action"] == "WAIT"
    assert result.key_index == 1
    assert result.attempted_key_count == 2


def test_provider_result_records_parse_failure_without_raising():
    class Client:
        def converse(self, **kwargs):
            return {
                "output": {"message": {"content": [{"text": '{"action":"HOLD",'}]}},
                "usage": {"inputTokens": 10, "outputTokens": 5},
            }

    provider = mod.BedrockNovaProvider(api_keys=["key-1"], client_factory=lambda **kwargs: Client())
    result = provider.converse(prompt="p", user_input="u", profile=mod.lite_profile_from_env())

    assert result.parse_ok is False
    assert result.parse_error == "JSONDecodeError"
    assert result.payload == {}


def test_route_mode_for_gpt5_nano_is_off_after_micro_removal():
    route_mode, profile = mod.route_mode_for_model("gpt-5-nano")

    assert route_mode == "off"
    assert profile is None


def test_lite_v2_profile_defaults_to_inference_profile(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID", raising=False)

    profile = mod.lite_v2_profile_from_env()

    assert profile.model_id == "global.amazon.nova-2-lite-v1:0"
