from __future__ import annotations

import argparse
import json
import os
import queue
import random
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH
from src.utils.logger import log_error


REPORT_DIR = DATA_DIR / "report" / "bedrock_nova_lite_shadow"
DECISION_AUTHORITY = "shadow_observation_only"
DEFAULT_MODEL_ID = "apac.amazon.nova-lite-v1:0"
DEFAULT_REGION = "ap-northeast-2"
OPENAI_GPT54_MINI_INPUT_USD_PER_1M = 0.75
OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M = 4.50
NOVA_LITE_INPUT_USD_PER_1M = 0.06
NOVA_LITE_OUTPUT_USD_PER_1M = 0.24
NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M = 0.006
NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M = 0.06


def load_bedrock_api_key_from_config(config_path: Path | None = None) -> str:
    path = config_path or (CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH)
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("BEDROCK_API_KEY") or payload.get("AWS_BEARER_TOKEN_BEDROCK") or "").strip()


def configure_bedrock_api_key_env(config_path: Path | None = None) -> bool:
    if os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
        return True
    api_key = load_bedrock_api_key_from_config(config_path)
    if not api_key:
        return False
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
    return True


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except Exception:
        return None


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


def normalize_action_score(payload: dict[str, Any] | None) -> tuple[str, int | None]:
    data = payload if isinstance(payload, dict) else {}
    action = str(data.get("action") or data.get("decision") or data.get("recommendation") or "").strip().upper()
    score = _normalize_score_value(data.get("score"))
    if score is None:
        score = _normalize_score_value(data.get("confidence"))
    if score is not None:
        score = max(0, min(100, score))
    return action, score


def _normalize_score_value(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        numeric = float(value)
        if 0.0 <= numeric <= 1.0:
            numeric *= 100.0
        return int(round(numeric))
    except Exception:
        return None


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
    input_usd_per_1m: float = NOVA_LITE_INPUT_USD_PER_1M,
    output_usd_per_1m: float = NOVA_LITE_OUTPUT_USD_PER_1M,
    cache_read_input_usd_per_1m: float = NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M,
    cache_write_input_usd_per_1m: float = NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M,
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


def shadow_jsonl_path(target_date: str | None = None) -> Path:
    safe_date = target_date or datetime.now().strftime("%Y-%m-%d")
    return REPORT_DIR / f"bedrock_nova_lite_shadow_{safe_date}.jsonl"


@dataclass(frozen=True)
class NovaShadowJob:
    prompt: str
    user_input: str
    openai_payload: dict[str, Any]
    transport_meta: dict[str, Any]
    request_meta: dict[str, Any]


class BedrockNovaLiteShadowManager:
    def __init__(
        self,
        *,
        enabled: bool = False,
        client_factory=None,
        model_id: str = DEFAULT_MODEL_ID,
        region_name: str = DEFAULT_REGION,
        workers: int = 1,
        queue_max: int = 200,
        timeout_ms: int = 5000,
        sample_rate: float = 1.0,
        max_output_tokens: int = 512,
        prompt_cache_enabled: bool = False,
        cache_read_input_usd_per_1m: float = NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M,
        cache_write_input_usd_per_1m: float = NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M,
        config_path: Path | None = None,
    ):
        self.is_enabled = bool(enabled)
        self.client_factory = client_factory
        self.model_id = str(model_id or DEFAULT_MODEL_ID)
        self.region_name = str(region_name or DEFAULT_REGION)
        self.workers = max(1, int(workers or 1))
        self.queue_max = max(1, int(queue_max or 200))
        self.timeout_ms = max(1, int(timeout_ms or 5000))
        self.sample_rate = max(0.0, min(1.0, float(sample_rate if sample_rate is not None else 1.0)))
        self.max_output_tokens = max(32, int(max_output_tokens or 512))
        self.prompt_cache_enabled = bool(prompt_cache_enabled)
        self.cache_read_input_usd_per_1m = float(cache_read_input_usd_per_1m)
        self.cache_write_input_usd_per_1m = float(cache_write_input_usd_per_1m)
        self.config_path = config_path
        self._queue: queue.Queue[NovaShadowJob] | None = None
        self._threads: list[threading.Thread] = []
        self._lock = threading.Lock()
        self._client = None

    def should_shadow(self, *, model_name: str, require_json: bool) -> bool:
        return bool(self.is_enabled and require_json and str(model_name or "") == "gpt-5.4-mini")

    def enqueue(self, *, prompt: str, user_input: str, openai_payload: dict[str, Any], transport_meta: dict[str, Any], request_meta: dict[str, Any]) -> bool:
        if not self.is_enabled:
            return False
        if self.sample_rate < 1.0 and random.random() > self.sample_rate:
            return False
        self._ensure_started()
        if self._queue is None:
            return False
        try:
            self._queue.put_nowait(
                NovaShadowJob(
                    prompt=str(prompt or ""),
                    user_input=str(user_input or ""),
                    openai_payload=dict(openai_payload or {}),
                    transport_meta=dict(transport_meta or {}),
                    request_meta=dict(request_meta or {}),
                )
            )
            return True
        except queue.Full:
            self._write_row(self._error_row(request_meta, transport_meta, openai_payload, "queue_full"))
            return False

    def _ensure_started(self) -> None:
        if self._queue is not None:
            return
        with self._lock:
            if self._queue is not None:
                return
            self._queue = queue.Queue(maxsize=self.queue_max)
            for idx in range(self.workers):
                thread = threading.Thread(target=self._worker_loop, name=f"bedrock-nova-lite-shadow-test-{idx}", daemon=True)
                thread.start()
                self._threads.append(thread)

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self.client_factory is not None:
            self._client = self.client_factory()
            return self._client
        configure_bedrock_api_key_env(self.config_path)
        import boto3
        from botocore.config import Config

        timeout_sec = self.timeout_ms / 1000.0
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=self.region_name,
            config=Config(connect_timeout=timeout_sec, read_timeout=timeout_sec, retries={"max_attempts": 0}),
        )
        return self._client

    def _worker_loop(self) -> None:
        assert self._queue is not None
        while True:
            job = self._queue.get()
            try:
                row = self._call_and_build_row(job)
            except Exception as exc:
                row = self._error_row(job.request_meta, job.transport_meta, job.openai_payload, type(exc).__name__, str(exc)[:240])
            self._write_row(row)
            self._queue.task_done()

    def _call_and_build_row(self, job: NovaShadowJob) -> dict[str, Any]:
        started = time.perf_counter()
        response = self._get_client().converse(
            modelId=self.model_id,
            system=self._build_system(job.prompt),
            messages=[{"role": "user", "content": [{"text": job.user_input}]}],
            inferenceConfig={"maxTokens": self.max_output_tokens, "temperature": 0},
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        text = self._extract_converse_text(response)
        parsed, parse_error = parse_nova_response_text(text)
        nova_action, nova_score = normalize_action_score(parsed)
        openai_action, openai_score = normalize_action_score(job.openai_payload)
        usage = response.get("usage") if isinstance(response, dict) else {}
        nova_input_tokens = _safe_int((usage or {}).get("inputTokens"))
        nova_output_tokens = _safe_int((usage or {}).get("outputTokens"))
        nova_cache_read_input_tokens = self._usage_int(usage, "cacheReadInputTokens")
        nova_cache_write_input_tokens = self._usage_int(usage, "cacheWriteInputTokens")
        nova_total_input_tokens = (nova_input_tokens or 0) + (nova_cache_read_input_tokens or 0) + (nova_cache_write_input_tokens or 0)
        row = self._base_row(job.request_meta, job.transport_meta, job.openai_payload)
        row.update(
            {
                "model_id": self.model_id,
                "region_name": self.region_name,
                "nova_action": nova_action,
                "nova_score": nova_score,
                "action_match": bool(openai_action and nova_action and openai_action == nova_action),
                "score_delta": (nova_score - openai_score) if nova_score is not None and openai_score is not None else None,
                "nova_latency_ms": latency_ms,
                "openai_input_tokens": _safe_int(job.transport_meta.get("openai_input_tokens")),
                "openai_output_tokens": _safe_int(job.transport_meta.get("openai_output_tokens")),
                "nova_input_tokens": nova_input_tokens,
                "nova_output_tokens": nova_output_tokens,
                "nova_prompt_cache_enabled": self.prompt_cache_enabled,
                "nova_cache_read_input_tokens": nova_cache_read_input_tokens,
                "nova_cache_write_input_tokens": nova_cache_write_input_tokens,
                "nova_total_input_tokens": nova_total_input_tokens,
                "nova_cache_pricing_note": "inputTokens excludes cache read/write tokens when Bedrock prompt caching is enabled",
                "estimated_openai_cost_usd": estimate_cost_usd(
                    job.transport_meta.get("openai_input_tokens"),
                    job.transport_meta.get("openai_output_tokens"),
                    input_usd_per_1m=OPENAI_GPT54_MINI_INPUT_USD_PER_1M,
                    output_usd_per_1m=OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M,
                ),
                "estimated_nova_cost_usd": estimate_nova_cost_usd(
                    input_tokens=nova_input_tokens,
                    output_tokens=nova_output_tokens,
                    cache_read_input_tokens=nova_cache_read_input_tokens,
                    cache_write_input_tokens=nova_cache_write_input_tokens,
                    input_usd_per_1m=NOVA_LITE_INPUT_USD_PER_1M,
                    output_usd_per_1m=NOVA_LITE_OUTPUT_USD_PER_1M,
                    cache_read_input_usd_per_1m=self.cache_read_input_usd_per_1m,
                    cache_write_input_usd_per_1m=self.cache_write_input_usd_per_1m,
                ),
                "parse_ok": parsed is not None,
                "error_type": parse_error or "",
                "raw_text_sample": str(text or "")[:500],
            }
        )
        return row

    def _build_system(self, prompt: str) -> list[dict[str, Any]]:
        system: list[dict[str, Any]] = [{"text": self._system_prompt(prompt)}]
        if self.prompt_cache_enabled:
            system.append({"cachePoint": {"type": "default"}})
        return system

    @staticmethod
    def _system_prompt(prompt: str) -> str:
        return f"{prompt}\n\nReturn JSON only. Do not include markdown fences or explanatory prose."

    @staticmethod
    def _usage_int(usage: Any, key: str) -> int | None:
        if not isinstance(usage, dict):
            return None
        candidates = {
            key,
            key[:1].upper() + key[1:],
            key[:1].lower() + key[1:],
        }
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

    @staticmethod
    def _extract_converse_text(response: dict[str, Any]) -> str:
        content = (((response or {}).get("output") or {}).get("message") or {}).get("content") or []
        return "\n".join(str(part.get("text") or "") for part in content if isinstance(part, dict)).strip()

    def _base_row(self, request_meta: dict[str, Any], transport_meta: dict[str, Any], openai_payload: dict[str, Any]) -> dict[str, Any]:
        openai_action, openai_score = normalize_action_score(openai_payload)
        return {
            "schema_version": 1,
            "event_type": "bedrock_nova_lite_shadow",
            "request_id": str(uuid.uuid4()),
            "openai_request_id": str(transport_meta.get("openai_request_id") or request_meta.get("openai_request_id") or ""),
            "endpoint_name": str(request_meta.get("endpoint_name") or transport_meta.get("openai_endpoint_name") or ""),
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
            "openai_action": openai_action,
            "openai_score": openai_score,
            "openai_latency_ms": _safe_int(request_meta.get("openai_latency_ms") or transport_meta.get("openai_ws_roundtrip_ms")),
            "decision_authority": DECISION_AUTHORITY,
            "runtime_effect": False,
            "broker_order_forbidden": True,
            "actual_order_submitted": False,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }

    def _error_row(self, request_meta: dict[str, Any], transport_meta: dict[str, Any], openai_payload: dict[str, Any], error_type: str, error_message: str = "") -> dict[str, Any]:
        row = self._base_row(request_meta, transport_meta, openai_payload)
        row.update(
            {
                "model_id": self.model_id,
                "region_name": self.region_name,
                "nova_action": "",
                "nova_score": None,
                "action_match": False,
                "score_delta": None,
                "nova_latency_ms": None,
                "openai_input_tokens": _safe_int(transport_meta.get("openai_input_tokens")),
                "openai_output_tokens": _safe_int(transport_meta.get("openai_output_tokens")),
                "nova_input_tokens": None,
                "nova_output_tokens": None,
                "nova_prompt_cache_enabled": self.prompt_cache_enabled,
                "nova_cache_read_input_tokens": None,
                "nova_cache_write_input_tokens": None,
                "nova_total_input_tokens": None,
                "nova_cache_pricing_note": "inputTokens excludes cache read/write tokens when Bedrock prompt caching is enabled",
                "estimated_openai_cost_usd": estimate_cost_usd(
                    transport_meta.get("openai_input_tokens"),
                    transport_meta.get("openai_output_tokens"),
                    input_usd_per_1m=OPENAI_GPT54_MINI_INPUT_USD_PER_1M,
                    output_usd_per_1m=OPENAI_GPT54_MINI_OUTPUT_USD_PER_1M,
                ),
                "estimated_nova_cost_usd": 0.0,
                "parse_ok": False,
                "error_type": error_type,
                "error_message": error_message,
            }
        )
        return row

    @staticmethod
    def _write_row(row: dict[str, Any]) -> None:
        try:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            with shadow_jsonl_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception as exc:
            log_error(f"[BedrockNovaLiteShadowTest] write failed: {exc}")


_RUNTIME_MANAGER: BedrockNovaLiteShadowManager | None = None
_RUNTIME_SIGNATURE: tuple[Any, ...] | None = None


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


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def runtime_manager() -> BedrockNovaLiteShadowManager:
    global _RUNTIME_MANAGER, _RUNTIME_SIGNATURE
    enabled = _env_bool("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED", False)
    model_id = os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_MODEL_ID", DEFAULT_MODEL_ID)
    region_name = os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_REGION", DEFAULT_REGION)
    signature = (
        enabled,
        model_id,
        region_name,
        _env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_WORKERS", 1),
        _env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_QUEUE_MAX", 200),
        _env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_TIMEOUT_MS", 5000),
        _env_float("KORSTOCKSCAN_BEDROCK_NOVA_LITE_SAMPLE_RATE", 1.0),
        _env_int("KORSTOCKSCAN_BEDROCK_NOVA_LITE_MAX_OUTPUT_TOKENS", 512),
        _env_bool("KORSTOCKSCAN_BEDROCK_NOVA_LITE_PROMPT_CACHE_ENABLED", False),
        _env_float("KORSTOCKSCAN_BEDROCK_NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M", NOVA_LITE_CACHE_READ_INPUT_USD_PER_1M),
        _env_float("KORSTOCKSCAN_BEDROCK_NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M", NOVA_LITE_CACHE_WRITE_INPUT_USD_PER_1M),
    )
    if _RUNTIME_MANAGER is None or _RUNTIME_SIGNATURE != signature:
        _RUNTIME_MANAGER = BedrockNovaLiteShadowManager(
            enabled=enabled,
            model_id=model_id,
            region_name=region_name,
            workers=signature[3],
            queue_max=signature[4],
            timeout_ms=signature[5],
            sample_rate=signature[6],
            max_output_tokens=signature[7],
            prompt_cache_enabled=signature[8],
            cache_read_input_usd_per_1m=signature[9],
            cache_write_input_usd_per_1m=signature[10],
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one test-only Bedrock Nova Lite shadow request.")
    parser.add_argument("--prompt", default="Return JSON only with action and score.")
    parser.add_argument("--user-input", default='{"action_request":"classify","symbol":"TEST"}')
    parser.add_argument("--openai-action", default="WAIT")
    parser.add_argument("--openai-score", type=int, default=50)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--region", default=DEFAULT_REGION)
    args = parser.parse_args(argv)
    manager = BedrockNovaLiteShadowManager(
        enabled=True,
        model_id=args.model_id,
        region_name=args.region,
        workers=1,
        queue_max=1,
    )
    ok = manager.enqueue(
        prompt=args.prompt,
        user_input=args.user_input,
        openai_payload={"action": args.openai_action, "score": args.openai_score},
        transport_meta={"openai_request_id": "manual-test", "openai_input_tokens": 0, "openai_output_tokens": 0},
        request_meta={"endpoint_name": "manual_bedrock_nova_lite_test", "symbol": "TEST", "cache_key": "manual"},
    )
    if manager._queue is not None:
        manager._queue.join()
    print(json.dumps({"enqueued": ok, "jsonl": str(shadow_jsonl_path()), "region": args.region}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
