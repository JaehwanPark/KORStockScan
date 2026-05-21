from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH


DEFAULT_REGION = "ap-northeast-2"
DEFAULT_MICRO_MODEL_ID = "apac.amazon.nova-micro-v1:0"
DEFAULT_LITE_MODEL_ID = "apac.amazon.nova-lite-v1:0"
PRIMARY_AUDIT_DIR = DATA_DIR / "report" / "bedrock_nova_primary_provider"

MICRO_INPUT_USD_PER_1M = 0.035
MICRO_OUTPUT_USD_PER_1M = 0.14
MICRO_CACHE_READ_INPUT_USD_PER_1M = 0.0035
MICRO_CACHE_WRITE_INPUT_USD_PER_1M = 0.035

LITE_INPUT_USD_PER_1M = 0.06
LITE_OUTPUT_USD_PER_1M = 0.24
LITE_CACHE_READ_INPUT_USD_PER_1M = 0.006
LITE_CACHE_WRITE_INPUT_USD_PER_1M = 0.06

OPENAI_GPT5_NANO_INPUT_USD_PER_1M = 0.05
OPENAI_GPT5_NANO_OUTPUT_USD_PER_1M = 0.40
OPENAI_GPT54_MINI_INPUT_USD_PER_1M = 0.75
OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M = 4.50


class BedrockNovaProviderError(RuntimeError):
    def __init__(self, message: str, *, error_type: str = "BedrockNovaProviderError", attempts: int = 0):
        super().__init__(message)
        self.error_type = error_type
        self.attempts = attempts


@dataclass(frozen=True)
class BedrockNovaModelProfile:
    family: str
    model_id: str
    region_name: str
    max_output_tokens: int
    timeout_ms: int
    prompt_cache_enabled: bool
    input_usd_per_1m: float
    output_usd_per_1m: float
    cache_read_input_usd_per_1m: float
    cache_write_input_usd_per_1m: float


@dataclass(frozen=True)
class BedrockNovaResult:
    payload: dict[str, Any]
    raw_text: str
    parse_ok: bool
    parse_error: str
    model_id: str
    region_name: str
    key_index: int
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    cache_read_input_tokens: int | None
    cache_write_input_tokens: int | None
    total_input_tokens: int
    estimated_cost_usd: float
    attempted_key_count: int

    def transport_meta(self) -> dict[str, Any]:
        return {
            "provider": "bedrock",
            "bedrock_model_id": self.model_id,
            "bedrock_region_name": self.region_name,
            "bedrock_key_index": self.key_index,
            "bedrock_latency_ms": self.latency_ms,
            "bedrock_input_tokens": self.input_tokens,
            "bedrock_output_tokens": self.output_tokens,
            "bedrock_cache_read_input_tokens": self.cache_read_input_tokens,
            "bedrock_cache_write_input_tokens": self.cache_write_input_tokens,
            "bedrock_total_input_tokens": self.total_input_tokens,
            "bedrock_estimated_cost_usd": self.estimated_cost_usd,
            "bedrock_attempted_key_count": self.attempted_key_count,
            "bedrock_parse_ok": self.parse_ok,
            "bedrock_parse_error": self.parse_error or "",
        }


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except Exception:
        return None


def _safe_float(value: Any, default: float) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def _extract_json_text(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end >= start:
        return raw[start : end + 1]
    return raw


def parse_nova_response_text(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(_extract_json_text(text))
        if isinstance(payload, dict):
            return payload, None
        return None, "json_root_not_object"
    except Exception as exc:
        return None, type(exc).__name__


def _normalize_score_value(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        numeric = float(value)
        if 0.0 <= numeric <= 1.0:
            numeric *= 100.0
        return max(0, min(100, int(round(numeric))))
    except Exception:
        return None


def normalize_action_score(payload: dict[str, Any] | None) -> tuple[str, int | None]:
    data = payload if isinstance(payload, dict) else {}
    action = str(data.get("action") or data.get("decision") or data.get("recommendation") or "").strip().upper()
    score = _normalize_score_value(data.get("score"))
    if score is None:
        score = _normalize_score_value(data.get("confidence"))
    return action, score


def estimate_cost_usd(input_tokens: Any, output_tokens: Any, *, input_usd_per_1m: float, output_usd_per_1m: float) -> float:
    in_tokens = max(0, _safe_int(input_tokens) or 0)
    out_tokens = max(0, _safe_int(output_tokens) or 0)
    return round((in_tokens * float(input_usd_per_1m) + out_tokens * float(output_usd_per_1m)) / 1_000_000, 8)


def estimate_nova_cost_usd(
    *,
    input_tokens: Any,
    output_tokens: Any,
    cache_read_input_tokens: Any = None,
    cache_write_input_tokens: Any = None,
    input_usd_per_1m: float,
    output_usd_per_1m: float,
    cache_read_input_usd_per_1m: float,
    cache_write_input_usd_per_1m: float,
) -> float:
    in_tokens = max(0, _safe_int(input_tokens) or 0)
    out_tokens = max(0, _safe_int(output_tokens) or 0)
    cache_read_tokens = max(0, _safe_int(cache_read_input_tokens) or 0)
    cache_write_tokens = max(0, _safe_int(cache_write_input_tokens) or 0)
    return round(
        (
            in_tokens * float(input_usd_per_1m)
            + out_tokens * float(output_usd_per_1m)
            + cache_read_tokens * float(cache_read_input_usd_per_1m)
            + cache_write_tokens * float(cache_write_input_usd_per_1m)
        )
        / 1_000_000,
        8,
    )


def load_bedrock_api_keys_from_config(config_path: Path | None = None) -> list[str]:
    keys: list[tuple[int, str]] = []
    env_key = str(os.getenv("AWS_BEARER_TOKEN_BEDROCK") or "").strip()
    if env_key:
        keys.append((0, env_key))
    path = config_path or (CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            for name, value in payload.items():
                raw_name = str(name)
                if raw_name == "BEDROCK_API_KEY" or raw_name == "AWS_BEARER_TOKEN_BEDROCK":
                    order = 1
                elif raw_name.startswith("BEDROCK_API_KEY_"):
                    suffix = raw_name.replace("BEDROCK_API_KEY_", "", 1)
                    order = 1 + (int(suffix) if suffix.isdigit() else 9999)
                elif raw_name.startswith("AWS_BEARER_TOKEN_BEDROCK_"):
                    suffix = raw_name.replace("AWS_BEARER_TOKEN_BEDROCK_", "", 1)
                    order = 1 + (int(suffix) if suffix.isdigit() else 9999)
                else:
                    continue
                key = str(value or "").strip()
                if key:
                    keys.append((order, key))
    seen = set()
    ordered = []
    for _, key in sorted(keys, key=lambda item: item[0]):
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def configure_bedrock_api_key_env(config_path: Path | None = None) -> bool:
    keys = load_bedrock_api_keys_from_config(config_path)
    if not keys:
        return False
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = keys[0]
    return True


def _usage_int(usage: Any, key: str) -> int | None:
    if not isinstance(usage, dict):
        return None
    candidates = {key, key[:1].upper() + key[1:], key[:1].lower() + key[1:]}
    snake = []
    for ch in key:
        if ch.isupper():
            snake.append("_")
            snake.append(ch.lower())
        else:
            snake.append(ch)
    candidates.add("".join(snake).lstrip("_"))
    for candidate in candidates:
        value = usage.get(candidate)
        if value not in (None, ""):
            return _safe_int(value)
    return None


def _extract_converse_text(response: dict[str, Any]) -> str:
    content = (((response or {}).get("output") or {}).get("message") or {}).get("content") or []
    return "\n".join(str(part.get("text") or "") for part in content if isinstance(part, dict)).strip()


def _is_retryable_bedrock_error(exc: Exception) -> bool:
    text = str(exc or "").lower()
    error_type = type(exc).__name__.lower()
    retry_markers = (
        "429",
        "throttl",
        "too many",
        "timeout",
        "timed out",
        "unavailable",
        "503",
        "500",
        "server",
        "service",
        "credential",
        "unauthorized",
        "forbidden",
        "accessdenied",
    )
    return any(marker in text or marker in error_type for marker in retry_markers)


def build_system_prompt(prompt: str) -> str:
    return f"{prompt}\n\nReturn JSON only. Do not include markdown fences or explanatory prose."


class BedrockNovaProvider:
    def __init__(
        self,
        *,
        api_keys: list[str] | None = None,
        config_path: Path | None = None,
        client_factory: Callable[..., Any] | None = None,
        key_rotation_enabled: bool = True,
    ):
        self.api_keys = list(api_keys if api_keys is not None else load_bedrock_api_keys_from_config(config_path))
        self.config_path = config_path
        self.client_factory = client_factory
        self.key_rotation_enabled = bool(key_rotation_enabled)
        self._clients: dict[tuple[int, str, int], Any] = {}

    def _client(self, *, key_index: int, key: str, region_name: str, timeout_ms: int):
        if self.client_factory is not None:
            try:
                return self.client_factory(key_index=key_index, api_key=key, region_name=region_name, timeout_ms=timeout_ms)
            except TypeError:
                try:
                    return self.client_factory(key_index, key, region_name, timeout_ms)
                except TypeError:
                    return self.client_factory()
        cache_key = (key_index, region_name, int(timeout_ms))
        if cache_key in self._clients:
            return self._clients[cache_key]
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = key
        import boto3
        from botocore.config import Config

        timeout_sec = max(0.001, int(timeout_ms or 5000) / 1000.0)
        client = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
            config=Config(connect_timeout=timeout_sec, read_timeout=timeout_sec, retries={"max_attempts": 0}),
        )
        self._clients[cache_key] = client
        return client

    def converse(self, *, prompt: str, user_input: str, profile: BedrockNovaModelProfile) -> BedrockNovaResult:
        if not self.api_keys:
            raise BedrockNovaProviderError("No Bedrock API keys configured", error_type="NoBedrockApiKey", attempts=0)
        keys = self.api_keys if self.key_rotation_enabled else self.api_keys[:1]
        last_error: Exception | None = None
        for idx, key in enumerate(keys):
            started = time.perf_counter()
            try:
                system: list[dict[str, Any]] = [{"text": build_system_prompt(prompt)}]
                if profile.prompt_cache_enabled:
                    system.append({"cachePoint": {"type": "default"}})
                response = self._client(
                    key_index=idx,
                    key=key,
                    region_name=profile.region_name,
                    timeout_ms=profile.timeout_ms,
                ).converse(
                    modelId=profile.model_id,
                    system=system,
                    messages=[{"role": "user", "content": [{"text": str(user_input or "")}]}],
                    inferenceConfig={"maxTokens": int(profile.max_output_tokens), "temperature": 0},
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                text = _extract_converse_text(response)
                parsed, parse_error = parse_nova_response_text(text)
                usage = response.get("usage") if isinstance(response, dict) else {}
                input_tokens = _safe_int((usage or {}).get("inputTokens"))
                output_tokens = _safe_int((usage or {}).get("outputTokens"))
                cache_read = _usage_int(usage, "cacheReadInputTokens")
                cache_write = _usage_int(usage, "cacheWriteInputTokens")
                total_input = (input_tokens or 0) + (cache_read or 0) + (cache_write or 0)
                return BedrockNovaResult(
                    payload=dict(parsed or {}),
                    raw_text=text,
                    parse_ok=parsed is not None,
                    parse_error=parse_error or "",
                    model_id=profile.model_id,
                    region_name=profile.region_name,
                    key_index=idx,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_input_tokens=cache_read,
                    cache_write_input_tokens=cache_write,
                    total_input_tokens=total_input,
                    estimated_cost_usd=estimate_nova_cost_usd(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read_input_tokens=cache_read,
                        cache_write_input_tokens=cache_write,
                        input_usd_per_1m=profile.input_usd_per_1m,
                        output_usd_per_1m=profile.output_usd_per_1m,
                        cache_read_input_usd_per_1m=profile.cache_read_input_usd_per_1m,
                        cache_write_input_usd_per_1m=profile.cache_write_input_usd_per_1m,
                    ),
                    attempted_key_count=idx + 1,
                )
            except Exception as exc:
                last_error = exc
                if not _is_retryable_bedrock_error(exc):
                    break
        error_type = type(last_error).__name__ if last_error is not None else "BedrockNovaProviderError"
        raise BedrockNovaProviderError(str(last_error or "Bedrock Nova call failed"), error_type=error_type, attempts=len(keys))


def micro_profile_from_env() -> BedrockNovaModelProfile:
    return BedrockNovaModelProfile(
        family="micro",
        model_id=os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_MODEL_ID", DEFAULT_MICRO_MODEL_ID),
        region_name=os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_REGION", DEFAULT_REGION),
        max_output_tokens=_env_int("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_MAX_OUTPUT_TOKENS", 512),
        timeout_ms=_env_int("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_TIMEOUT_MS", 5000),
        prompt_cache_enabled=_env_bool("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_PROMPT_CACHE_ENABLED", False),
        input_usd_per_1m=_safe_float(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_INPUT_USD_PER_1M"), MICRO_INPUT_USD_PER_1M),
        output_usd_per_1m=_safe_float(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_OUTPUT_USD_PER_1M"), MICRO_OUTPUT_USD_PER_1M),
        cache_read_input_usd_per_1m=_safe_float(
            os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_CACHE_READ_INPUT_USD_PER_1M"),
            MICRO_CACHE_READ_INPUT_USD_PER_1M,
        ),
        cache_write_input_usd_per_1m=_safe_float(
            os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_CACHE_WRITE_INPUT_USD_PER_1M"),
            MICRO_CACHE_WRITE_INPUT_USD_PER_1M,
        ),
    )


def lite_profile_from_env() -> BedrockNovaModelProfile:
    return BedrockNovaModelProfile(
        family="lite",
        model_id=os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_MODEL_ID", DEFAULT_LITE_MODEL_ID),
        region_name=os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_REGION", DEFAULT_REGION),
        max_output_tokens=_env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_MAX_OUTPUT_TOKENS", 768),
        timeout_ms=_env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_TIMEOUT_MS", 7000),
        prompt_cache_enabled=_env_bool("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PROMPT_CACHE_ENABLED", False),
        input_usd_per_1m=_safe_float(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_INPUT_USD_PER_1M"), LITE_INPUT_USD_PER_1M),
        output_usd_per_1m=_safe_float(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_OUTPUT_USD_PER_1M"), LITE_OUTPUT_USD_PER_1M),
        cache_read_input_usd_per_1m=_safe_float(
            os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M"),
            LITE_CACHE_READ_INPUT_USD_PER_1M,
        ),
        cache_write_input_usd_per_1m=_safe_float(
            os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M"),
            LITE_CACHE_WRITE_INPUT_USD_PER_1M,
        ),
    )


def route_mode_for_model(model_name: str) -> tuple[str, BedrockNovaModelProfile | None]:
    model = str(model_name or "")
    if model == "gpt-5-nano":
        return str(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_MICRO_ROUTE_MODE", "shadow")).strip().lower(), micro_profile_from_env()
    if model == "gpt-5.4-mini":
        return str(os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "shadow")).strip().lower(), lite_profile_from_env()
    return "off", None


_RUNTIME_PROVIDER: BedrockNovaProvider | None = None
_RUNTIME_PROVIDER_SIGNATURE: tuple[Any, ...] | None = None


def runtime_provider() -> BedrockNovaProvider:
    global _RUNTIME_PROVIDER, _RUNTIME_PROVIDER_SIGNATURE
    keys = load_bedrock_api_keys_from_config()
    signature = (tuple(keys), _env_bool("KORSTOCKSCAN_BEDROCK_KEY_ROTATION_ENABLED", True))
    if _RUNTIME_PROVIDER is None or _RUNTIME_PROVIDER_SIGNATURE != signature:
        _RUNTIME_PROVIDER = BedrockNovaProvider(api_keys=keys, key_rotation_enabled=signature[1])
        _RUNTIME_PROVIDER_SIGNATURE = signature
    return _RUNTIME_PROVIDER


def provider_audit_row(
    *,
    request_meta: dict[str, Any],
    result: BedrockNovaResult | None,
    payload: dict[str, Any] | None,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    action, score = normalize_action_score(payload)
    row: dict[str, Any] = {
        "schema_version": 1,
        "event_type": "bedrock_nova_primary_provider",
        "request_id": str(request_meta.get("request_id") or ""),
        "openai_request_id": str(request_meta.get("openai_request_id") or request_meta.get("request_id") or ""),
        "endpoint_name": str(request_meta.get("endpoint_name") or ""),
        "prompt_type": str(request_meta.get("prompt_type") or request_meta.get("endpoint_name") or ""),
        "symbol": str(request_meta.get("symbol") or ""),
        "cache_key": str(request_meta.get("cache_key") or ""),
        "pipeline_stage": str(request_meta.get("pipeline_stage") or request_meta.get("endpoint_name") or ""),
        "record_id": str(request_meta.get("record_id") or ""),
        "sim_record_id": str(request_meta.get("sim_record_id") or ""),
        "sim_parent_record_id": str(request_meta.get("sim_parent_record_id") or ""),
        "entry_adm_candidate_id": str(request_meta.get("entry_adm_candidate_id") or ""),
        "source_event_stage": str(request_meta.get("source_event_stage") or ""),
        "pipeline_event_emitted_at": str(request_meta.get("pipeline_event_emitted_at") or ""),
        "primary_provider": "bedrock",
        "bedrock_action": action,
        "bedrock_score": score,
        "parse_ok": bool(result.parse_ok) if result else False,
        "error_type": error_type or (result.parse_error if result else ""),
        "error_message": str(error_message or "")[:240],
        "decision_authority": "runtime_primary_with_openai_failback",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if result is not None:
        row.update(
            {
                "model_id": result.model_id,
                "region_name": result.region_name,
                "bedrock_key_index": result.key_index,
                "bedrock_latency_ms": result.latency_ms,
                "bedrock_input_tokens": result.input_tokens,
                "bedrock_output_tokens": result.output_tokens,
                "bedrock_cache_read_input_tokens": result.cache_read_input_tokens,
                "bedrock_cache_write_input_tokens": result.cache_write_input_tokens,
                "bedrock_total_input_tokens": result.total_input_tokens,
                "estimated_bedrock_cost_usd": result.estimated_cost_usd,
                "raw_text_sample": str(result.raw_text or "")[:500],
            }
        )
    return row


def primary_audit_jsonl_path(target_date: str | None = None) -> Path:
    safe_date = target_date or datetime.now().strftime("%Y-%m-%d")
    return PRIMARY_AUDIT_DIR / f"bedrock_nova_primary_provider_{safe_date}.jsonl"


def write_provider_audit_row(row: dict[str, Any]) -> None:
    PRIMARY_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with primary_audit_jsonl_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
