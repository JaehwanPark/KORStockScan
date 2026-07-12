import json
import sys
from types import SimpleNamespace

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


def test_provider_client_cache_is_separated_by_region(monkeypatch):
    created = []

    class FakeBoto3:
        def client(self, service_name, *, region_name, config):
            client = object()
            created.append((service_name, region_name, client))
            return client

    monkeypatch.setitem(sys.modules, "boto3", FakeBoto3())
    monkeypatch.setitem(sys.modules, "botocore", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "botocore.config", SimpleNamespace(Config=lambda **kwargs: kwargs))

    provider = mod.BedrockNovaProvider(api_keys=["key-1"])
    first = provider._client(key_index=0, key="key-1", region_name="us-west-2", timeout_ms=7000)
    second = provider._client(key_index=0, key="key-1", region_name="ap-northeast-2", timeout_ms=7000)
    first_again = provider._client(key_index=0, key="key-1", region_name="us-west-2", timeout_ms=7000)

    assert first is first_again
    assert first is not second
    assert [item[1] for item in created] == ["us-west-2", "ap-northeast-2"]


def test_route_mode_for_gpt5_nano_is_off_after_micro_removal():
    route_mode, profile = mod.route_mode_for_model("gpt-5-nano")

    assert route_mode == "off"
    assert profile is None


def test_route_mode_for_gpt54_nano_is_off_after_fast_model_update():
    route_mode, profile = mod.route_mode_for_model("gpt-5.4-nano")

    assert route_mode == "off"
    assert profile is None


def test_lite_v2_profile_defaults_to_inference_profile(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID", raising=False)

    profile = mod.lite_v2_profile_from_env()

    assert profile.model_id == "global.amazon.nova-2-lite-v1:0"


def test_qwen3_32b_profile_defaults_to_bedrock_model(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_QWEN3_32B_MODEL_ID", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_QWEN3_32B_REGION", raising=False)

    profile = mod.qwen3_32b_profile_from_env()

    assert profile.family == "qwen3_32b"
    assert profile.model_id == "qwen.qwen3-32b-v1:0"
    assert profile.region_name == "us-west-2"


def test_entry_price_primary_profile_can_select_qwen3_32b(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY", "qwen3_32b")

    profile = mod.entry_price_primary_profile_from_env()

    assert profile is not None
    assert profile.family == "qwen3_32b"


def test_route_mode_for_gpt54_mini_can_select_lite_v2_primary(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "primary")
    monkeypatch.setenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_FAMILY", "lite_v2")
    monkeypatch.delenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID", raising=False)

    route_mode, profile = mod.route_mode_for_model("gpt-5.4-mini")

    assert route_mode == "primary"
    assert profile is not None
    assert profile.family == "lite_v2"
    assert profile.model_id == "global.amazon.nova-2-lite-v1:0"
