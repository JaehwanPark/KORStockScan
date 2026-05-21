from __future__ import annotations

from typing import Any

from src.engine.bedrock_nova_provider import (
    OPENAI_GPT54_MINI_INPUT_USD_PER_1M,
    OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M,
    lite_profile_from_env,
)
from src.engine.bedrock_nova_shadow_runtime import BedrockNovaShadowManager, env_bool, env_float, env_int
from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report" / "bedrock_nova_lite_shadow"
EVENT_TYPE = "bedrock_nova_lite_shadow"
TARGET_MODEL_NAME = "gpt-5.4-mini"

_RUNTIME_MANAGER: BedrockNovaShadowManager | None = None
_RUNTIME_SIGNATURE: tuple[Any, ...] | None = None


def runtime_manager() -> BedrockNovaShadowManager:
    global _RUNTIME_MANAGER, _RUNTIME_SIGNATURE
    profile = lite_profile_from_env()
    signature = (
        env_bool("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED", False),
        profile,
        env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_WORKERS", 1),
        env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_QUEUE_MAX", 200),
        env_float("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SAMPLE_RATE", 1.0),
    )
    if _RUNTIME_MANAGER is None or _RUNTIME_SIGNATURE != signature:
        _RUNTIME_MANAGER = BedrockNovaShadowManager(
            enabled=signature[0],
            report_dir=REPORT_DIR,
            event_type=EVENT_TYPE,
            target_model_name=TARGET_MODEL_NAME,
            profile=profile,
            openai_input_usd_per_1m=OPENAI_GPT54_MINI_INPUT_USD_PER_1M,
            openai_output_usd_per_1m=OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M,
            workers=signature[2],
            queue_max=signature[3],
            sample_rate=signature[4],
        )
        _RUNTIME_SIGNATURE = signature
    return _RUNTIME_MANAGER


def enqueue_runtime_shadow(
    *,
    model_name: str,
    require_json: bool,
    prompt: str,
    user_input: str,
    openai_payload: dict[str, Any],
    transport_meta: dict[str, Any],
    request_meta: dict[str, Any],
) -> bool:
    manager = runtime_manager()
    if not manager.should_shadow(model_name=model_name, require_json=require_json):
        return False
    return manager.enqueue(
        prompt=prompt,
        user_input=user_input,
        openai_payload=openai_payload,
        transport_meta=transport_meta,
        request_meta=request_meta,
    )
