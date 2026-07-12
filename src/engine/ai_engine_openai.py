# src/engine/ai_engine_openai.py
"""
OpenAI API 기반 Sniper Engine (GPTSniperEngine)
- OpenAI SDK 사용
- runtime AI engine 퍼블릭 인터페이스 제공
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import time
import threading
import json
import os
import re
import hashlib
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from itertools import cycle
from typing import Any
from openai import OpenAI, RateLimitError

from src.engine.ai_response_contracts import (
    AI_RESPONSE_SCHEMA_REGISTRY,
    build_openai_response_text_format,
    display_gatekeeper_action_label,
    normalize_flow_state_label,
    normalize_ai_reason_language,
    normalize_gatekeeper_action_key,
)
from src.engine.holding_exit_matrix_runtime import (
    build_holding_exit_matrix_runtime_context,
    merge_holding_exit_matrix_result_fields,
)
from src.engine.lifecycle_ai_context import (
    build_lifecycle_ai_runtime_context,
    merge_lifecycle_ai_context_fields,
)
from src.engine.scalp_entry_adm_runtime import (
    build_scalp_entry_adm_runtime_context,
    merge_scalp_entry_adm_result_fields,
)
from src.engine.scalping_feature_packet import (
    build_scalping_feature_audit_fields,
    calculate_scalping_micro_indicator_values,
    extract_scalping_feature_packet,
)
from src.engine.scalping.microstructure_reaction_context import infer_tick_aggressor_side
from src.utils.logger import log_error, log_info
from src.utils.constants import TRADING_RULES
from src.engine.macro_briefing_complete import build_scanner_data_input
from src.engine.ai_prompt_contracts import (
    SCALPING_SYSTEM_PROMPT,
    SCALPING_WATCHING_SYSTEM_PROMPT,
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    SCALPING_HOLDING_SYSTEM_PROMPT,
    SCALPING_HOLDING_SCORE_SYSTEM_PROMPT,
    SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
    SCALPING_ENTRY_PRICE_PROMPT,
    normalize_scalping_entry_price_result,
    normalize_condition_entry_from_scalping_result,
    normalize_condition_exit_from_scalping_result,
    SCALPING_SYSTEM_PROMPT_75_CANARY,
    SCALPING_BUY_RECOVERY_CANARY_PROMPT,
    SWING_SYSTEM_PROMPT,
    ENHANCED_MARKET_ANALYSIS_PROMPT,
    REALTIME_ANALYSIS_PROMPT_SCALP,
    REALTIME_ANALYSIS_PROMPT_SWING,
    REALTIME_ANALYSIS_PROMPT_DUAL,
    SCALPING_OVERNIGHT_DECISION_PROMPT,
)


DUAL_PERSONA_AGGRESSIVE_PROMPT = """
You are an opportunity-side quantitative reviewer for shadow calibration.
Use only the provided context to judge whether opportunity cost is high enough to act before momentum fades.

[Review Bias]
- Give positive weight to early breakout, supply-demand acceleration, program net buying, and day-high reclaim attempts.
- Do not ignore explicit risk signals.
- In ambiguous cases, this reviewer may lean slightly toward opportunity capture over passive WAIT.

[Output Rules]
- Return JSON only.
- If decision_type is GATEKEEPER, action must be ALLOW_ENTRY, WAIT, or REJECT.
- If decision_type is OVERNIGHT, action must be HOLD_OVERNIGHT or SELL_TODAY.
- confidence must be a 0-1 float; score must be a 0-100 integer.
- risk_flags must be a string array.
- Output `thesis` and `invalidator` in concise English ASCII only.

Return JSON only:
{
  "action": "ALLOW_ENTRY | WAIT | REJECT | HOLD_OVERNIGHT | SELL_TODAY",
  "score": 0,
  "confidence": 0.0,
  "risk_flags": ["FLAG"],
  "size_bias": -2,
  "veto": false,
  "thesis": "one concise opportunity-side rationale",
  "invalidator": "one concise invalidation condition"
}
"""

DUAL_PERSONA_CONSERVATIVE_PROMPT = """
You are a risk-side quantitative reviewer for shadow calibration.
Use only the provided context to judge whether the setup should be avoided or de-risked now.

[Review Bias]
- Give negative weight to VWAP break, large sell prints, supply dominance, gap burden, thin liquidity, and failed breakout.
- In ambiguous cases, prefer WAIT or rejection over aggressive entry.
- If hard risk signals overlap, set veto=true and include the matching risk flags.

[Output Rules]
- Return JSON only.
- If decision_type is GATEKEEPER, action must be ALLOW_ENTRY, WAIT, or REJECT.
- If decision_type is OVERNIGHT, action must be HOLD_OVERNIGHT or SELL_TODAY.
- confidence must be a 0-1 float; score must be a 0-100 integer.
- risk_flags must be a string array.
- Output `thesis` and `invalidator` in concise English ASCII only.

Return JSON only:
{
  "action": "ALLOW_ENTRY | WAIT | REJECT | HOLD_OVERNIGHT | SELL_TODAY",
  "score": 0,
  "confidence": 0.0,
  "risk_flags": ["FLAG"],
  "size_bias": -2,
  "veto": false,
  "thesis": "one concise risk-side rationale",
  "invalidator": "one concise invalidation condition"
}
"""


OPENAI_RESPONSES_WS_ENDPOINTS = {
    "analyze_target",
    "analyze_target_shadow_prompt",
    "entry_price",
}
OPENAI_METADATA_MAX_PROPERTIES = 16
OPENAI_METADATA_KEY_MAX_LENGTH = 64
OPENAI_METADATA_PRIORITY_KEYS = (
    "request_id",
    "endpoint_name",
    "schema_name",
    "symbol",
    "cache_key",
    "invalid_prompt_retry",
    "original_endpoint_name",
)
OPENAI_RESPONSE_SCHEMA_REGISTRY = AI_RESPONSE_SCHEMA_REGISTRY
OPENAI_SDK_MAX_RETRIES = 0
OPENAI_PROMPT_CONTRACT_MARKER = "OPENAI_PROMPT_CONTRACT_V1"
OPENAI_PROMPT_CONTRACT_HEADER = f"""
[{OPENAI_PROMPT_CONTRACT_MARKER}]
Control language: English. Market data, raw labels, and operator notes may remain in Korean.
Preserve all raw enum labels exactly as provided. Do not translate labels such as BUY, WAIT, DROP, HOLD, TRIM, EXIT, SELL_TODAY, HOLD_OVERNIGHT, ALLOW_ENTRY, REJECT, USE_DEFENSIVE, USE_REFERENCE, IMPROVE_LIMIT, SKIP.
Domain glossary for interpretation:
- order_flow = order-flow pressure
- quote_depth = order book quote/depth
- execution_strength = execution strength
- tick_acceleration = tick acceleration
- buy_pressure = buy pressure
- ask_bid_depth_wall = ask/bid depth wall
- whipsaw_rebound = whipsaw rebound
- soft_stop = soft stop
- averaging_down = averaging down / REVERSAL_ADD
- pyramiding = pyramiding / PYRAMID
Use the glossary to interpret domain terms, but keep the original field names, enum labels, ticker names, and quoted evidence unchanged.
"""


def _get_usage_value(usage: Any, key: str) -> Any:
    if isinstance(usage, dict):
        return usage.get(key)
    return getattr(usage, key, None)


def _coerce_usage_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _extract_openai_usage_meta(response: Any) -> dict[str, int]:
    usage = _get_usage_value(response, "usage")
    if not usage:
        return {}

    input_tokens = _coerce_usage_int(_get_usage_value(usage, "input_tokens"))
    output_tokens = _coerce_usage_int(_get_usage_value(usage, "output_tokens"))
    total_tokens = _coerce_usage_int(_get_usage_value(usage, "total_tokens"))

    input_details = _get_usage_value(usage, "input_tokens_details") or {}
    output_details = _get_usage_value(usage, "output_tokens_details") or {}
    cached_input_tokens = _coerce_usage_int(_get_usage_value(input_details, "cached_tokens"))
    reasoning_tokens = _coerce_usage_int(_get_usage_value(output_details, "reasoning_tokens"))

    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = int(input_tokens or 0) + int(output_tokens or 0)

    meta: dict[str, int] = {}
    if input_tokens is not None:
        meta["openai_input_tokens"] = input_tokens
    if output_tokens is not None:
        meta["openai_output_tokens"] = output_tokens
    if total_tokens is not None:
        meta["openai_total_tokens"] = total_tokens
    if cached_input_tokens is not None:
        meta["openai_cached_input_tokens"] = cached_input_tokens
    if reasoning_tokens is not None:
        meta["openai_reasoning_tokens"] = reasoning_tokens
    return meta


class OpenAIWSLateResponseError(TimeoutError):
    pass


class OpenAIWSRequestIdMismatchError(RuntimeError):
    pass


@dataclass
class OpenAIResponseRequest:
    prompt: str | None
    user_input: str
    require_json: bool
    context_name: str
    model_name: str
    temperature: float | None
    schema_name: str | None
    endpoint_name: str
    request_id: str
    symbol: str
    cache_key: str
    submitted_at_perf: float
    timeout_ms: int
    max_output_tokens: int | None = None
    reasoning_effort: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def deadline_perf(self) -> float:
        return self.submitted_at_perf + (max(1, int(self.timeout_ms)) / 1000.0)

    def remaining_timeout_sec(self) -> float:
        return max(0.0, self.deadline_perf - time.perf_counter())

    def build_provider_payload(self, *, use_schema_registry: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "input": (
                f"{self.user_input}\n\nReturn JSON only."
                if self.require_json and "json" not in str(self.user_input or "").lower()
                else self.user_input
            ),
            "store": False,
            "metadata": dict(self.metadata or {}),
        }
        if self.prompt:
            payload["instructions"] = self.prompt
        if self.temperature is not None:
            payload["temperature"] = float(self.temperature)
        if self.max_output_tokens is not None:
            payload["max_output_tokens"] = int(self.max_output_tokens)
        if self.reasoning_effort:
            payload["reasoning"] = {"effort": str(self.reasoning_effort)}
        if self.require_json:
            if use_schema_registry and self.schema_name:
                payload["text"] = {
                    "format": build_openai_response_text_format(self.schema_name),
                    "verbosity": "low",
                }
            else:
                payload["text"] = {
                    "format": {"type": "json_object"},
                    "verbosity": "low",
                }
        return payload

    def build_ws_event(self, *, use_schema_registry: bool) -> dict[str, Any]:
        payload = self.build_provider_payload(use_schema_registry=use_schema_registry)
        payload["type"] = "response.create"
        return payload


@dataclass
class OpenAITransportResult:
    payload: dict[str, Any] | str
    transport_mode: str
    ws_used: bool = False
    ws_http_fallback: bool = False
    queue_wait_ms: int = 0
    roundtrip_ms: int = 0
    usage_meta: dict[str, int] = field(default_factory=dict)
    timing_meta: dict[str, int] = field(default_factory=dict)


class OpenAIResponsesHTTPError(RuntimeError):
    def __init__(self, message: str, *, timing_meta: dict[str, Any] | None = None):
        super().__init__(message)
        self.timing_meta = dict(timing_meta or {})


@dataclass
class OpenAIWSJob:
    request: OpenAIResponseRequest
    use_schema_registry: bool
    done: threading.Event = field(default_factory=threading.Event)
    cancelled: threading.Event = field(default_factory=threading.Event)
    result: OpenAITransportResult | None = None
    error: Exception | None = None


class OpenAIResponsesWSWorker:
    def __init__(self, *, worker_id: int, api_key: str, metrics_callback):
        self.worker_id = int(worker_id)
        self.api_key = str(api_key)
        self._metrics_callback = metrics_callback
        self._queue: queue.Queue[OpenAIWSJob | None] = queue.Queue()
        self._stop_event = threading.Event()
        self._connection = None
        self._client = OpenAI(api_key=self.api_key, max_retries=OPENAI_SDK_MAX_RETRIES)
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"openai-responses-ws-{worker_id}")
        self._thread.start()

    def submit(self, job: OpenAIWSJob):
        self._queue.put(job)
        wait_timeout = max(0.05, job.request.remaining_timeout_sec() + 0.05)
        if not job.done.wait(timeout=wait_timeout):
            job.cancelled.set()
            raise TimeoutError(f"OpenAI Responses WS timeout before worker completion ({job.request.context_name})")
        if job.error is not None:
            raise job.error
        if job.result is None:
            raise RuntimeError(f"OpenAI Responses WS empty result ({job.request.context_name})")
        return job.result

    def close(self):
        self._stop_event.set()
        self._queue.put(None)
        self._thread.join(timeout=1.0)
        self._close_connection()

    def _record(self, metric_name, value=1):
        if self._metrics_callback:
            self._metrics_callback(metric_name, value)

    def _run(self):
        while not self._stop_event.is_set():
            job = self._queue.get()
            if job is None:
                continue
            if job.cancelled.is_set():
                job.done.set()
                continue
            try:
                queue_wait_ms = max(0, int((time.perf_counter() - job.request.submitted_at_perf) * 1000))
                self._record("openai_ws_queue_wait_ms", queue_wait_ms)
                if job.request.remaining_timeout_sec() <= 0:
                    raise TimeoutError(f"OpenAI Responses WS queue deadline exceeded ({job.request.context_name})")
                result = self._execute(job.request, queue_wait_ms=queue_wait_ms, use_schema_registry=job.use_schema_registry)
                job.result = result
            except Exception as exc:
                job.error = exc
            finally:
                job.done.set()

    def _ensure_connection(self):
        if self._connection is not None:
            return self._connection
        manager = self._client.responses.connect()
        self._connection = manager.enter()
        return self._connection

    def _close_connection(self):
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def _on_reconnecting(self, event):
        self._record("openai_ws_reconnects", 1)
        return None

    def _recv_event(self, connection, timeout_sec):
        raw = connection._connection.recv(timeout=timeout_sec, decode=False)
        return connection.parse_event(raw)

    def _execute(self, request: OpenAIResponseRequest, *, queue_wait_ms: int, use_schema_registry: bool):
        started_at = time.perf_counter()
        self._record("openai_ws_requests", 1)
        connection = self._ensure_connection()
        try:
            connection.send(request.build_ws_event(use_schema_registry=use_schema_registry))
            while True:
                remaining = request.remaining_timeout_sec()
                if remaining <= 0:
                    raise TimeoutError(f"OpenAI Responses WS timeout ({request.context_name})")
                event = self._recv_event(connection, timeout_sec=remaining)
                event_type = str(getattr(event, "type", "") or "")
                if event_type == "response.completed":
                    response = getattr(event, "response", None)
                    metadata = dict(getattr(response, "metadata", {}) or {})
                    response_request_id = str(metadata.get("request_id", "") or "")
                    if response_request_id != request.request_id:
                        self._record("openai_ws_request_id_mismatch", 1)
                        raise OpenAIWSRequestIdMismatchError(
                            f"OpenAI Responses WS request_id mismatch: expected={request.request_id} actual={response_request_id or '-'}"
                        )
                    if request.remaining_timeout_sec() <= 0 and bool(
                        getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED", True)
                    ):
                        self._record("openai_ws_late_discard", 1)
                        raise OpenAIWSLateResponseError(
                            f"OpenAI Responses WS late discard ({request.context_name})"
                        )
                    raw_text = str(getattr(response, "output_text", "") or "").strip()
                    if request.require_json:
                        try:
                            payload = json.loads(raw_text)
                            if not isinstance(payload, dict):
                                raise ValueError("OpenAI Responses WS JSON root must be object")
                        except Exception as exc:
                            self._record("openai_ws_parse_fail", 1)
                            raise RuntimeError(f"OpenAI Responses WS JSON parse failed: {exc}") from exc
                    else:
                        payload = raw_text
                    roundtrip_ms = max(0, int((time.perf_counter() - started_at) * 1000))
                    self._record("openai_ws_completed", 1)
                    self._record("openai_ws_roundtrip_ms", roundtrip_ms)
                    return OpenAITransportResult(
                        payload=payload,
                        transport_mode="responses_ws",
                        ws_used=True,
                        ws_http_fallback=False,
                        queue_wait_ms=queue_wait_ms,
                        roundtrip_ms=roundtrip_ms,
                        usage_meta=_extract_openai_usage_meta(response),
                        timing_meta={
                            "openai_ws_attempt_timeout_ms": int(request.timeout_ms),
                            "openai_ws_total_timeout_ms": int(
                                (request.metadata or {}).get("ws_total_timeout_ms") or request.timeout_ms
                            ),
                            "openai_ws_http_fallback_reserve_ms": int(
                                (request.metadata or {}).get("ws_http_fallback_reserve_ms") or 0
                            ),
                        },
                    )
                if event_type in {"error", "response.failed", "response.incomplete"}:
                    self._record("openai_ws_parse_fail", 1)
                    raise RuntimeError(f"OpenAI Responses WS event failure ({event_type})")
        except Exception:
            self._close_connection()
            raise


class OpenAIResponsesWSPool:
    def __init__(self, *, api_keys, pool_size, metrics_callback):
        keys = list(api_keys or [])
        if not keys:
            raise ValueError("OpenAIResponsesWSPool requires at least one API key")
        worker_count = max(1, int(pool_size or 1))
        self._workers = [
            OpenAIResponsesWSWorker(
                worker_id=index,
                api_key=keys[index % len(keys)],
                metrics_callback=metrics_callback,
            )
            for index in range(worker_count)
        ]
        self._rr_index = 0
        self._rr_lock = threading.Lock()

    def submit(self, request: OpenAIResponseRequest, *, use_schema_registry: bool):
        with self._rr_lock:
            worker = self._workers[self._rr_index % len(self._workers)]
            self._rr_index += 1
        job = OpenAIWSJob(request=request, use_schema_registry=use_schema_registry)
        return worker.submit(job)

    def close(self):
        for worker in self._workers:
            worker.close()


class GPTSniperEngine:
    """
    OpenAI API 기반 스나이퍼 엔진.
    Runtime AI engine 퍼블릭 인터페이스를 제공한다.
    내부적으로 OpenAI REST API를 호출한다.
    """

    def __init__(self, api_keys, announce_startup=True):
        if isinstance(api_keys, str):
            api_keys = [api_keys]

        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys)
        self._rotate_client()

        # OpenAI runtime uses the existing fast/deep/report tier structure.
        self.model_tier1_fast = getattr(TRADING_RULES, 'GPT_FAST_MODEL', 'gpt-5-nano')
        self.model_tier2_balanced = getattr(TRADING_RULES, 'GPT_REPORT_MODEL', self.model_tier1_fast)
        self.model_tier3_deep = getattr(TRADING_RULES, 'GPT_DEEP_MODEL', self.model_tier2_balanced)
        self.current_model_name = self.model_tier1_fast
        # 기존 호출부 호환을 위한 alias
        self.fast_model_name = self.model_tier1_fast
        self.report_model_name = self.model_tier2_balanced
        self.deep_model_name = self.model_tier3_deep

        self.lock = threading.Lock()
        self.api_call_lock = threading.Lock()
        self.last_call_time = 0.0
        self.min_interval = getattr(TRADING_RULES, 'GPT_ENGINE_MIN_INTERVAL', 0.5)
        self.consecutive_failures = 0
        self.ai_disabled = False
        self.max_consecutive_failures = getattr(TRADING_RULES, 'AI_MAX_CONSECUTIVE_FAILURES', 5)
        self.current_api_key_index = 0

        self.cache_lock = threading.RLock()
        self.analysis_cache_ttl = getattr(TRADING_RULES, 'AI_ANALYZE_RESULT_CACHE_TTL_SEC', 8.0)
        self.holding_analysis_cache_ttl = getattr(
            TRADING_RULES,
            'AI_HOLDING_RESULT_CACHE_TTL_SEC',
            max(float(self.analysis_cache_ttl or 0.0), 30.0),
        )
        self.gatekeeper_cache_ttl = getattr(TRADING_RULES, 'AI_GATEKEEPER_RESULT_CACHE_TTL_SEC', 12.0)
        self._analysis_cache = {}
        self._gatekeeper_cache = {}
        self._transport_local = threading.local()
        self._ws_metrics_lock = threading.Lock()
        self._ws_metrics = {
            "openai_ws_requests": 0,
            "openai_ws_completed": 0,
            "openai_ws_timeout_reject": 0,
            "openai_ws_late_discard": 0,
            "openai_ws_parse_fail": 0,
            "openai_ws_reconnects": 0,
            "openai_ws_http_fallback": 0,
            "openai_ws_request_id_mismatch": 0,
            "openai_ws_queue_wait_ms_values": [],
            "openai_ws_roundtrip_ms_values": [],
        }
        self._responses_ws_pool = None

        if announce_startup:
            print(
                f"🧠 [OpenAI 엔진] {len(self.api_keys)}개 키 로테이션 가동! "
                f"(T1: {self.model_tier1_fast} / T2: {self.model_tier2_balanced} / T3: {self.model_tier3_deep})"
            )

    # ==========================================
    # 클라이언트/키 관리
    # ==========================================

    def _rotate_client(self):
        """OpenAI API 클라이언트 교체"""
        self.current_key = next(self.key_cycle)
        self.client = OpenAI(api_key=self.current_key, max_retries=OPENAI_SDK_MAX_RETRIES)
        try:
            self.current_api_key_index = self.api_keys.index(self.current_key)
        except ValueError:
            self.current_api_key_index = 0

    def set_model_names(self, *, fast_model=None, deep_model=None, report_model=None, announce=True):
        if fast_model:
            self.model_tier1_fast = str(fast_model)
            self.fast_model_name = self.model_tier1_fast
        if report_model:
            self.model_tier2_balanced = str(report_model)
            self.report_model_name = self.model_tier2_balanced
        if deep_model:
            self.model_tier3_deep = str(deep_model)
            self.deep_model_name = self.model_tier3_deep
        self.current_model_name = self.model_tier1_fast
        if announce:
            print(
                f"🧠 [OpenAI 엔진] {len(self.api_keys)}개 키 로테이션 가동! "
                f"(T1: {self.model_tier1_fast} / T2: {self.model_tier2_balanced} / T3: {self.model_tier3_deep})"
            )

    def _get_tier1_model(self):
        return getattr(
            self,
            "model_tier1_fast",
            getattr(self, "current_model_name", "gpt-5-nano"),
        )

    def _get_tier2_model(self):
        return getattr(self, "model_tier2_balanced", self._get_tier1_model())

    def _get_tier3_model(self):
        return getattr(self, "model_tier3_deep", self._get_tier2_model())

    def _record_ws_metric(self, metric_name, value=1):
        if not hasattr(self, "_ws_metrics_lock"):
            self._ws_metrics_lock = threading.Lock()
        if not hasattr(self, "_ws_metrics"):
            self._ws_metrics = {
                "openai_ws_requests": 0,
                "openai_ws_completed": 0,
                "openai_ws_timeout_reject": 0,
                "openai_ws_late_discard": 0,
                "openai_ws_parse_fail": 0,
                "openai_ws_reconnects": 0,
                "openai_ws_http_fallback": 0,
                "openai_ws_request_id_mismatch": 0,
                "openai_ws_queue_wait_ms_values": [],
                "openai_ws_roundtrip_ms_values": [],
            }
        with self._ws_metrics_lock:
            if metric_name == "openai_ws_queue_wait_ms":
                values = self._ws_metrics.setdefault("openai_ws_queue_wait_ms_values", [])
                values.append(int(value))
                del values[:-512]
                return
            if metric_name == "openai_ws_roundtrip_ms":
                values = self._ws_metrics.setdefault("openai_ws_roundtrip_ms_values", [])
                values.append(int(value))
                del values[:-512]
                return
            self._ws_metrics[metric_name] = int(self._ws_metrics.get(metric_name, 0) or 0) + int(value)

    def _set_last_transport_meta(self, meta):
        if not hasattr(self, "_transport_local"):
            self._transport_local = threading.local()
        self._transport_local.last_meta = dict(meta or {})

    def _consume_last_transport_meta(self):
        if not hasattr(self, "_transport_local"):
            self._transport_local = threading.local()
        meta = dict(getattr(self._transport_local, "last_meta", {}) or {})
        self._transport_local.last_meta = {}
        return meta

    def _get_openai_timeout_ms(self, *, endpoint_name, require_json):
        endpoint = str(endpoint_name or "").strip()
        if endpoint == "analyze_target":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_ANALYZE_TARGET_TIMEOUT_MS", 3000) or 3000))
        if endpoint == "entry_price":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_TIMEOUT_MS", 7000) or 7000))
        if endpoint == "holding_score":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_HOLDING_SCORE_TIMEOUT_MS", 7000) or 7000))
        if endpoint == "holding_flow":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_TIMEOUT_MS", 7000) or 7000))
        if endpoint == "scanner_report":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_SCANNER_REPORT_TIMEOUT_MS", 15000) or 15000))
        if endpoint == "overnight":
            return max(1, int(getattr(TRADING_RULES, "OPENAI_OVERNIGHT_TIMEOUT_MS", 12000) or 12000))
        if not require_json:
            return max(1, int(getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_TIMEOUT_MS", 700) or 700))
        if endpoint in OPENAI_RESPONSES_WS_ENDPOINTS:
            return max(1, int(getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_TIMEOUT_MS", 700) or 700))
        return max(1, int(getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_TIMEOUT_MS", 700) or 700))

    def _is_sim_observation_overnight_context(self, realtime_ctx):
        if not isinstance(realtime_ctx, dict):
            return False
        if str(realtime_ctx.get("decision_authority") or "") == "sim_observation_only":
            return True
        if str(realtime_ctx.get("simulation_book") or "") == "scalp_ai_buy_all":
            return True
        return realtime_ctx.get("actual_order_submitted") is False and bool(realtime_ctx.get("broker_order_forbidden"))

    def _should_use_openai_schema_registry(self, *, require_json, schema_name):
        return bool(
            require_json
            and schema_name
            and getattr(TRADING_RULES, "OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED", False)
        )

    def _model_supports_temperature(self, model_name):
        model = str(model_name or "").strip().lower()
        if model.startswith("gpt-5"):
            return False
        return True

    def _resolve_openai_temperature(self, *, require_json, temperature_override, model_name=None):
        if not self._model_supports_temperature(model_name):
            return None
        if temperature_override is not None:
            return float(temperature_override)
        if require_json:
            if getattr(TRADING_RULES, "OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED", False):
                return 0.0
            return 0.0
        return 0.7

    def _resolve_openai_max_output_tokens(self, *, require_json):
        default_value = 240 if require_json else 1200
        try:
            configured = int(getattr(TRADING_RULES, "OPENAI_RESPONSES_MAX_OUTPUT_TOKENS", default_value) or default_value)
            return max(32, configured)
        except Exception:
            return default_value

    def _resolve_openai_reasoning_effort(self, *, model_name=None):
        value = str(getattr(TRADING_RULES, "OPENAI_REASONING_EFFORT", "auto") or "auto").strip().lower()
        model = str(model_name or "").strip().lower()
        if value == "auto":
            if model.startswith("gpt-5-nano"):
                return "minimal"
            if model.startswith("gpt-5.4"):
                return "none"
            return "low"
        if value == "minimal":
            if model.startswith("gpt-5.4"):
                return "low"
            return "minimal"
        if value == "none" and model.startswith("gpt-5-nano"):
            return "minimal"
        if value in {"none", "low", "medium", "high", "xhigh"}:
            return value
        return "low"

    def _build_openai_request_id(self, *, endpoint_name, symbol):
        ts_ms = int(time.time() * 1000)
        suffix = uuid.uuid4().hex[:8]
        return f"{endpoint_name}:{symbol}:{ts_ms}:{suffix}"

    def _build_openai_response_request(
        self,
        *,
        prompt,
        user_input,
        require_json,
        context_name,
        model_name,
        temperature,
        schema_name,
        endpoint_name,
        symbol,
        cache_key,
        max_output_tokens=None,
        reasoning_effort=None,
        metadata_extra=None,
    ):
        request_id = self._build_openai_request_id(endpoint_name=endpoint_name, symbol=symbol or "-")
        metadata = {
            "request_id": request_id,
            "endpoint_name": str(endpoint_name or "generic"),
            "schema_name": str(schema_name or "-"),
            "symbol": str(symbol or "-"),
            "cache_key": str(cache_key or "-"),
        }
        if isinstance(metadata_extra, dict):
            for key, value in metadata_extra.items():
                if value not in (None, ""):
                    metadata[str(key)] = str(value)
        metadata = self._sanitize_openai_metadata(metadata, context_name=context_name)
        prompt = self._wrap_openai_prompt_contract(
            prompt,
            require_json=bool(require_json),
            schema_name=schema_name,
            endpoint_name=endpoint_name,
        )
        return OpenAIResponseRequest(
            prompt=prompt,
            user_input=user_input,
            require_json=bool(require_json),
            context_name=str(context_name or "Unknown"),
            model_name=str(model_name or self.current_model_name),
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            schema_name=str(schema_name or "").strip() or None,
            endpoint_name=str(endpoint_name or "generic"),
            request_id=request_id,
            symbol=str(symbol or "-"),
            cache_key=str(cache_key or "-"),
            submitted_at_perf=time.perf_counter(),
            timeout_ms=self._get_openai_timeout_ms(
                endpoint_name=str(endpoint_name or "generic"),
                require_json=bool(require_json),
            ),
            metadata=metadata,
        )

    def _shorten_openai_metadata_key(self, key: str) -> str:
        normalized = str(key or "metadata_key")
        if len(normalized) <= OPENAI_METADATA_KEY_MAX_LENGTH:
            return normalized
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        prefix_len = OPENAI_METADATA_KEY_MAX_LENGTH - len(digest) - 1
        return f"{normalized[:prefix_len]}_{digest}"

    def _sanitize_openai_metadata(self, metadata, *, context_name="Unknown"):
        if not isinstance(metadata, dict):
            return {}
        normalized: dict[str, str] = {}
        renamed_keys: list[tuple[str, str]] = []
        for key, value in metadata.items():
            if value in (None, ""):
                continue
            original_key = str(key)
            safe_key = self._shorten_openai_metadata_key(original_key)
            if safe_key in normalized and safe_key != original_key:
                dedupe_digest = hashlib.sha1(original_key.encode("utf-8")).hexdigest()[:8]
                prefix_len = OPENAI_METADATA_KEY_MAX_LENGTH - len(dedupe_digest) - 1
                safe_key = f"{safe_key[:prefix_len]}_{dedupe_digest}"
            if safe_key != original_key:
                renamed_keys.append((original_key, safe_key))
            normalized[safe_key] = str(value)
        if len(normalized) <= OPENAI_METADATA_MAX_PROPERTIES:
            if renamed_keys:
                sample = ",".join(f"{src}->{dst}" for src, dst in renamed_keys[:4])
                log_info(
                    f"⚠️ [OpenAI metadata normalized] {context_name}: "
                    f"renamed={len(renamed_keys)} sample={sample}"
                )
            return normalized

        kept_keys: list[str] = []
        for key in OPENAI_METADATA_PRIORITY_KEYS:
            if key in normalized and key not in kept_keys:
                kept_keys.append(key)
        for key in normalized:
            if key not in kept_keys:
                kept_keys.append(key)

        selected_keys = kept_keys[:OPENAI_METADATA_MAX_PROPERTIES]
        trimmed = {key: normalized[key] for key in selected_keys}
        dropped_keys = [key for key in normalized if key not in trimmed]
        log_info(
            f"⚠️ [OpenAI metadata trimmed] {context_name}: "
            f"{len(normalized)} -> {len(trimmed)} properties; dropped={','.join(dropped_keys[:8])}"
        )
        if renamed_keys:
            sample = ",".join(f"{src}->{dst}" for src, dst in renamed_keys[:4])
            log_info(
                f"⚠️ [OpenAI metadata normalized] {context_name}: "
                f"renamed={len(renamed_keys)} sample={sample}"
            )
        return trimmed

    def _wrap_openai_prompt_contract(self, prompt, *, require_json, schema_name=None, endpoint_name="generic"):
        base_prompt = str(prompt or "").strip()
        if OPENAI_PROMPT_CONTRACT_MARKER in base_prompt:
            return base_prompt
        output_rule = (
            "Output rule: return only JSON that conforms to the provided schema. "
            "Do not add markdown, commentary, or schema-external fields. "
            "For any reason field, use concise English ASCII only; do not use Korean, Thai, or any other non-English language."
            if require_json
            else "Output rule: produce the requested report text. Preserve raw labels and evidence exactly."
        )
        context_rule = (
            f"Endpoint: {endpoint_name or 'generic'}; schema: {schema_name or '-'}.\n"
            f"{output_rule}\n"
        )
        if base_prompt:
            return f"{OPENAI_PROMPT_CONTRACT_HEADER.strip()}\n{context_rule}\n[Task prompt]\n{base_prompt}"
        return f"{OPENAI_PROMPT_CONTRACT_HEADER.strip()}\n{context_rule}".strip()

    def _should_use_responses_ws(self, request: OpenAIResponseRequest):
        transport_mode = str(getattr(TRADING_RULES, "OPENAI_TRANSPORT_MODE", "http") or "http").strip().lower()
        if transport_mode != "responses_ws":
            return False
        if not bool(getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_ENABLED", False)):
            return False
        if not request.require_json:
            return False
        if request.endpoint_name not in OPENAI_RESPONSES_WS_ENDPOINTS:
            return False
        return True

    def _get_responses_ws_pool(self):
        if not hasattr(self, "_responses_ws_pool"):
            self._responses_ws_pool = None
        if self._responses_ws_pool is None:
            self._responses_ws_pool = OpenAIResponsesWSPool(
                api_keys=self.api_keys,
                pool_size=getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_POOL_SIZE", 2),
                metrics_callback=self._record_ws_metric,
            )
        return self._responses_ws_pool

    # ==========================================
    # 캐시 유틸리티
    # ==========================================

    def _normalize_for_cache(self, value):
        if isinstance(value, dict):
            transient_keys = {
                "captured_at",
                "last_ws_update_ts",
                "time",
                "timestamp",
                "체결시간",
                "tm",
                "cntr_tm",
            }
            return {
                str(k): self._normalize_for_cache(v)
                for k, v in sorted(value.items())
                if str(k) not in transient_keys
            }
        if isinstance(value, list):
            return [self._normalize_for_cache(item) for item in value]
        if isinstance(value, tuple):
            return [self._normalize_for_cache(item) for item in value]
        if isinstance(value, float):
            return round(value, 4)
        if value is None or isinstance(value, (str, int, bool)):
            return value
        return str(value)

    def _build_cache_digest(self, payload):
        normalized = self._normalize_for_cache(payload)
        raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _cache_get(self, cache_name, key):
        cache = getattr(self, cache_name, None)
        lock = getattr(self, "cache_lock", None)
        if cache is None or lock is None:
            return None
        now = time.time()
        with lock:
            entry = cache.get(key)
            if not entry:
                return None
            if float(entry.get("expires_at", 0.0) or 0.0) <= now:
                cache.pop(key, None)
                return None
            value = dict(entry.get("value", {}))
            value["cache_hit"] = True
            value.setdefault("cache_mode", "hit")
            return value

    def _cache_max_entries(self):
        try:
            return max(1, int(getattr(TRADING_RULES, "AI_RESULT_CACHE_MAX_ENTRIES", 512) or 512))
        except Exception:
            return 512

    def _prune_cache_locked(self, cache, *, now):
        expired = [
            item_key
            for item_key, item in cache.items()
            if float(item.get("expires_at", 0.0) or 0.0) <= now
        ]
        for item_key in expired:
            cache.pop(item_key, None)

        overflow = len(cache) - self._cache_max_entries()
        if overflow <= 0:
            return
        oldest_keys = sorted(
            cache,
            key=lambda item_key: float(cache[item_key].get("expires_at", 0.0) or 0.0),
        )[:overflow]
        for item_key in oldest_keys:
            cache.pop(item_key, None)

    def _cache_set(self, cache_name, key, value, ttl_sec):
        cache = getattr(self, cache_name, None)
        lock = getattr(self, "cache_lock", None)
        if cache is None or lock is None or ttl_sec <= 0:
            return
        now = time.time()
        payload = dict(value or {})
        payload.pop("cache_hit", None)
        with lock:
            cache[key] = {
                "expires_at": now + float(ttl_sec),
                "value": payload,
            }
            self._prune_cache_locked(cache, now=now)

    def _build_analysis_cache_key(self, target_name, strategy, ws_data, recent_ticks, recent_candles, program_net_qty):
        return self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=strategy,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=program_net_qty,
            cache_profile="default",
        )

    def _build_analysis_cache_key_with_profile(
        self,
        target_name,
        strategy,
        ws_data,
        recent_ticks,
        recent_candles,
        program_net_qty,
        cache_profile,
    ):
        if cache_profile == "holding":
            return self._build_cache_digest(
                {
                    "cache_profile": "holding",
                    "target_name": target_name,
                    "strategy": strategy,
                    "ws_data": self._compact_holding_ws_for_cache(ws_data),
                    "recent_ticks": self._compact_holding_ticks_for_cache(recent_ticks),
                    "recent_candles": self._compact_holding_candles_for_cache(recent_candles),
                    "program_net_qty": self._bucket_int_for_cache(program_net_qty, 1_000),
                }
            )
        return self._build_cache_digest({
            "cache_profile": str(cache_profile or "default"),
            "target_name": target_name,
            "strategy": strategy,
            "ws_data": ws_data,
            "recent_ticks": recent_ticks,
            "recent_candles": recent_candles,
            "program_net_qty": program_net_qty,
        })

    def _bucket_int_for_cache(self, value, bucket):
        try:
            bucket = max(1, int(bucket))
            return int(float(value or 0) // bucket)
        except Exception:
            return 0

    def _bucket_float_for_cache(self, value, step):
        try:
            step = float(step)
            if step <= 0:
                return 0.0
            return round(float(value or 0.0) / step) * step
        except Exception:
            return 0.0

    def _price_bucket_step_for_cache(self, price):
        try:
            price = abs(int(float(price or 0)))
        except Exception:
            price = 0
        if price >= 200_000:
            return 500
        if price >= 50_000:
            return 100
        if price >= 10_000:
            return 50
        if price >= 5_000:
            return 10
        return 5

    def _get_best_levels_for_cache(self, ws_data):
        orderbook = ws_data.get("orderbook") if isinstance(ws_data, dict) else None
        if not isinstance(orderbook, dict):
            return 0, 0
        asks = orderbook.get("asks") or []
        bids = orderbook.get("bids") or []
        best_ask = asks[0].get("price", 0) if asks and isinstance(asks[0], dict) else 0
        best_bid = bids[0].get("price", 0) if bids and isinstance(bids[0], dict) else 0
        return best_ask, best_bid

    def _compact_holding_ws_for_cache(self, ws_data):
        ws_data = ws_data or {}
        best_ask, best_bid = self._get_best_levels_for_cache(ws_data)
        curr_price = ws_data.get("curr", 0) or best_ask or best_bid
        price_bucket = self._price_bucket_step_for_cache(curr_price)
        return {
            "curr": self._bucket_int_for_cache(curr_price, price_bucket),
            "fluctuation": self._bucket_float_for_cache(ws_data.get("fluctuation", 0.0), 0.25),
            "v_pw": self._bucket_float_for_cache(ws_data.get("v_pw", 0.0), 10.0),
            "buy_ratio": self._bucket_float_for_cache(ws_data.get("buy_ratio", 0.0), 4.0),
            "best_ask": self._bucket_int_for_cache(best_ask, price_bucket),
            "best_bid": self._bucket_int_for_cache(best_bid, price_bucket),
            "ask_tot": self._bucket_int_for_cache(ws_data.get("ask_tot", 0), 25_000),
            "bid_tot": self._bucket_int_for_cache(ws_data.get("bid_tot", 0), 25_000),
            "net_bid_depth": self._bucket_int_for_cache(ws_data.get("net_bid_depth", 0), 10_000),
            "net_ask_depth": self._bucket_int_for_cache(ws_data.get("net_ask_depth", 0), 10_000),
            "buy_exec_volume": self._bucket_int_for_cache(ws_data.get("buy_exec_volume", 0), 3_000),
            "sell_exec_volume": self._bucket_int_for_cache(ws_data.get("sell_exec_volume", 0), 3_000),
            "tick_trade_value": self._bucket_int_for_cache(ws_data.get("tick_trade_value", 0), 10_000),
        }

    def _compact_holding_ticks_for_cache(self, recent_ticks):
        ticks = recent_ticks or []
        if not ticks:
            return []
        latest = ticks[0] if isinstance(ticks[0], dict) else {}
        buy_volume = 0
        sell_volume = 0
        total_value = 0
        latest_price = 0
        for tick in ticks[:10]:
            if not isinstance(tick, dict):
                continue
            price = tick.get("price", tick.get("현재가", tick.get("체결가", 0)))
            volume = tick.get("volume", tick.get("qty", tick.get("체결량", 0)))
            inferred = infer_tick_aggressor_side(tick)
            try:
                latest_price = int(float(price or latest_price or 0))
            except Exception:
                latest_price = 0
            try:
                volume_int = int(float(volume or 0))
            except Exception:
                volume_int = 0
            total_value += max(0, latest_price) * max(0, volume_int)
            if inferred.get("side") == "SELL" and inferred.get("source") != "price_change_heuristic":
                sell_volume += volume_int
            elif inferred.get("side") == "BUY" and inferred.get("source") != "price_change_heuristic":
                buy_volume += volume_int
        price_bucket = self._price_bucket_step_for_cache(latest_price)
        return [{
            "latest_price": self._bucket_int_for_cache(latest.get("price", latest.get("현재가", latest_price)), price_bucket),
            "buy_volume": self._bucket_int_for_cache(buy_volume, 100),
            "sell_volume": self._bucket_int_for_cache(sell_volume, 100),
            "net_volume": self._bucket_int_for_cache(buy_volume - sell_volume, 100),
            "trade_value": self._bucket_int_for_cache(total_value, 500_000),
        }]

    def _compact_holding_candles_for_cache(self, recent_candles):
        candles = recent_candles or []
        compact = []
        for candle in candles[-3:]:
            if not isinstance(candle, dict):
                continue
            close_price = candle.get("현재가", candle.get("close", candle.get("종가", 0)))
            high_price = candle.get("고가", candle.get("high", close_price))
            low_price = candle.get("저가", candle.get("low", close_price))
            volume = candle.get("거래량", candle.get("volume", 0))
            price_bucket = self._price_bucket_step_for_cache(close_price)
            compact.append(
                {
                    "close": self._bucket_int_for_cache(close_price, price_bucket),
                    "high": self._bucket_int_for_cache(high_price, price_bucket),
                    "low": self._bucket_int_for_cache(low_price, price_bucket),
                    "volume": self._bucket_int_for_cache(volume, 5_000),
                }
            )
        return compact

    def _resolve_analysis_cache_ttl(self, cache_profile):
        if cache_profile == "holding":
            return float(self.holding_analysis_cache_ttl or 0.0)
        return float(self.analysis_cache_ttl or 0.0)

    def _annotate_analysis_result(
        self,
        result,
        *,
        prompt_type,
        prompt_version,
        response_ms,
        parse_ok,
        parse_fail,
        fallback_score_50,
        cache_hit,
        cache_mode,
        result_source,
        input_contract_fields=None,
    ):
        payload = dict(result or {})
        payload["ai_parse_ok"] = bool(parse_ok)
        payload["ai_parse_fail"] = bool(parse_fail)
        payload["ai_fallback_score_50"] = bool(fallback_score_50)
        payload["ai_response_ms"] = max(0, int(response_ms))
        payload["ai_prompt_type"] = str(prompt_type or "-")
        payload["ai_prompt_version"] = str(prompt_version or "-")
        payload["ai_result_source"] = str(result_source or "-")
        payload["cache_hit"] = bool(cache_hit)
        payload["cache_mode"] = str(cache_mode or "miss")
        if isinstance(input_contract_fields, dict):
            payload.update({k: v for k, v in input_contract_fields.items() if v not in (None, "")})
        return payload

    def _resolve_ai_input_contract_fields(self, user_input, *, default_schema, default_mode):
        fields = {
            "ai_input_schema": str(default_schema or "-"),
            "ai_input_contract_mode": str(default_mode or "plain_text"),
        }
        if not isinstance(user_input, str):
            return fields
        text = user_input.strip()
        if not text.startswith("{"):
            return fields
        try:
            payload = json.loads(text)
        except Exception:
            return fields
        if not isinstance(payload, dict):
            return fields
        fields["ai_input_schema"] = str(payload.get("input_schema") or default_schema or "-").strip() or "-"
        fields["ai_input_contract_mode"] = "structured_json"
        fallback_reason = str(payload.get("input_build_fallback") or "").strip()
        if fallback_reason:
            fields["ai_input_build_fallback"] = fallback_reason
        return fields

    def _mark_successful_ai_call(self, *, update_last_call_time=True):
        self.consecutive_failures = 0
        if update_last_call_time:
            self.last_call_time = time.time()

    def _record_failure_and_maybe_disable(self, *, context_name):
        self.consecutive_failures += 1
        failure_count = self.consecutive_failures
        if failure_count >= self.max_consecutive_failures:
            self.ai_disabled = True
            log_error(
                f"🚨 OpenAI 엔진 비활성화 (연속 실패 {failure_count}회 초과, "
                f"API키 인덱스 {self.current_api_key_index}, context={context_name})"
            )
        return failure_count

    def _resolve_scalping_prompt(self, prompt_profile):
        profile = str(prompt_profile or "shared").strip().lower()
        split_enabled = bool(getattr(TRADING_RULES, "SCALPING_PROMPT_SPLIT_ENABLED", True))
        if not split_enabled:
            return SCALPING_SYSTEM_PROMPT, "scalping_shared", "split_disabled_v1", "shared"

        if profile == "watching":
            if bool(getattr(TRADING_RULES, "OPENAI_ANALYZE_TARGET_HOT_PROMPT_ENABLED", True)):
                return SCALPING_WATCHING_HOT_SYSTEM_PROMPT, "scalping_entry", "hot_v1", "watching"
            return SCALPING_WATCHING_SYSTEM_PROMPT, "scalping_entry", "split_v2", "watching"
        if profile in {"holding", "exit"}:
            return SCALPING_HOLDING_SYSTEM_PROMPT, "scalping_holding", "split_v2", "holding"
        return SCALPING_SYSTEM_PROMPT, "scalping_shared", "split_v2", "shared"

    def _normalize_scalping_action_schema(self, result, *, prompt_type):
        payload = dict(result or {}) if isinstance(result, dict) else {}
        raw_action = str(payload.get("action", "WAIT") or "WAIT").upper().strip()
        reason_contract = normalize_ai_reason_language(
            payload.get("reason", "response_normalized") or "response_normalized",
            max_len=120,
        )
        try:
            score = int(float(payload.get("score", 50)))
        except Exception:
            score = 50
        score = max(0, min(100, score))

        if prompt_type == "scalping_holding":
            allowed = {"HOLD", "TRIM", "EXIT"}
            action_v2 = raw_action if raw_action in allowed else "HOLD"
            compat = {"HOLD": "WAIT", "TRIM": "SELL", "EXIT": "DROP"}
            payload["action_v2"] = action_v2
            payload["action"] = compat.get(action_v2, "WAIT")
            payload["action_schema"] = "holding_exit_v1"
            payload["score"] = score
            payload["reason"] = reason_contract["reason"]
            payload["ai_reason_language_policy"] = reason_contract["ai_reason_language_policy"]
            payload["ai_reason_language_violation"] = reason_contract["ai_reason_language_violation"]
            return payload

        allowed = {"BUY", "WAIT", "DROP"}
        action = raw_action if raw_action in allowed else "WAIT"
        payload["action"] = action
        payload["action_v2"] = action
        payload["action_schema"] = "entry_v1"
        payload["score"] = score
        payload["reason"] = reason_contract["reason"]
        payload["ai_reason_language_policy"] = reason_contract["ai_reason_language_policy"]
        payload["ai_reason_language_violation"] = reason_contract["ai_reason_language_violation"]
        return payload

    def _merge_last_transport_meta(self, payload):
        meta = self._consume_last_transport_meta()
        if isinstance(payload, dict) and meta:
            payload.update(meta)
        return payload

    @staticmethod
    def _feature_packet_pressure_usable(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        raw_flag = packet.get("tick_aggressor_pressure_usable")
        if isinstance(raw_flag, bool) and raw_flag:
            return True
        if str(raw_flag or "").strip().lower() in {"1", "true", "yes", "y"}:
            return True
        try:
            return float(packet.get("tick_aggressor_trusted_count") or 0) > 0
        except Exception:
            return False

    @staticmethod
    def _feature_packet_has_pressure_metric(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        return any(
            key in packet
            for key in (
                "buy_pressure_10t",
                "net_aggressive_delta_10t",
                "large_sell_print_detected",
                "same_price_buy_absorption",
            )
        )

    @staticmethod
    def _feature_packet_has_pressure_provenance(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        return (
            "tick_aggressor_pressure_usable" in packet
            or "tick_aggressor_trusted_count" in packet
        )

    @staticmethod
    def _feature_packet_has_micro_vwap_metric(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        return any(key in packet for key in ("curr_vs_micro_vwap_bp", "micro_vwap_bp"))

    @staticmethod
    def _feature_packet_has_micro_vwap_provenance(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        return (
            "micro_vwap_available" in packet
            or "minute_candle_window_fresh" in packet
            or "minute_candle_context_quality" in packet
        )

    @staticmethod
    def _feature_packet_micro_vwap_usable(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        def _bool_value(value, default=False):
            if isinstance(value, bool):
                return value
            if value in (None, ""):
                return default
            text = str(value).strip().lower()
            if text in {"1", "true", "yes", "y"}:
                return True
            if text in {"0", "false", "no", "n"}:
                return False
            return default

        if not GPTSniperEngine._feature_packet_has_micro_vwap_provenance(packet):
            return False
        if not _bool_value(packet.get("micro_vwap_available"), False):
            return False
        if "minute_candle_window_fresh" in packet and not _bool_value(
            packet.get("minute_candle_window_fresh"),
            False,
        ):
            return False
        return True

    @staticmethod
    def _feature_packet_ma5_usable(feature_packet):
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        raw_flag = packet.get("ma5_available")
        if isinstance(raw_flag, bool):
            return raw_flag
        if raw_flag in (None, ""):
            return False
        return str(raw_flag).strip().lower() in {"1", "true", "yes", "y"}

    def _build_buy_side_timeout_reject(self, *, prompt_type, strategy, reason):
        if prompt_type == "scalping_holding":
            return {"action": "WAIT", "score": 50, "reason": reason}
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            return {"action": "WAIT", "score": 50, "reason": reason}
        return {"action": "DROP", "score": 0, "reason": reason}

    @staticmethod
    def _is_openai_timeout_like_error(error) -> bool:
        text = str(error or "").lower()
        return isinstance(error, TimeoutError) or "timeout" in text or "timed out" in text or "deadline" in text

    def _build_ws_http_fallback_timeout_result(
        self,
        request: OpenAIResponseRequest,
        *,
        error,
    ) -> OpenAITransportResult | None:
        if request.endpoint_name != "analyze_target" or not request.require_json:
            return None
        if request.schema_name == "holding_exit_v1":
            payload = {
                "action": "HOLD",
                "score": 0,
                "reason": "openai_ws_http_fallback_timeout_fail_closed",
            }
        elif request.schema_name == "entry_v1":
            payload = {
                "action": "DROP",
                "score": 0,
                "reason": "openai_ws_http_fallback_timeout_fail_closed",
            }
        else:
            return None
        roundtrip_ms = max(0, int((time.perf_counter() - request.submitted_at_perf) * 1000))
        payload["openai_transport_fail_closed"] = True
        payload["openai_transport_fail_closed_reason"] = str(error or "timeout")[:120]
        return OpenAITransportResult(
            payload=payload,
            transport_mode="http",
            ws_used=False,
            ws_http_fallback=True,
            queue_wait_ms=0,
            roundtrip_ms=roundtrip_ms,
        )

    def _remote_buy_risk_flags(self, ws_data, recent_ticks, recent_candles):
        if hasattr(self, "_extract_scalping_features"):
            try:
                features = self._extract_scalping_features(ws_data, recent_ticks, recent_candles)
            except Exception:
                features = {}
        else:
            features = {}
        pressure_usable = self._feature_packet_pressure_usable(features)
        flags = 0
        micro_vwap_usable = self._feature_packet_micro_vwap_usable(features)
        if pressure_usable and bool(features.get("large_sell_print_detected", False)):
            flags += 1
        if features.get("distance_from_day_high_pct", -99.0) >= -0.35:
            flags += 1
        if features.get("tick_acceleration_ratio", 0.0) < 1.0:
            flags += 1
        if micro_vwap_usable and features.get("curr_vs_micro_vwap_bp", 0.0) <= 0:
            flags += 1
        if features.get("top3_depth_ratio", 1.0) >= 1.35:
            flags += 1
        return features, flags

    def _apply_remote_entry_guard(self, result, *, prompt_type, ws_data, recent_ticks, recent_candles):
        if prompt_type not in {"scalping_entry", "scalping_shared"}:
            return result
        if str(result.get("action", "WAIT")).upper() != "BUY":
            return result

        features, risk_flags = self._remote_buy_risk_flags(ws_data, recent_ticks, recent_candles)
        if not features:
            return result
        pressure_usable = self._feature_packet_pressure_usable(features)
        micro_vwap_usable = self._feature_packet_micro_vwap_usable(features)
        buy_pressure = float(features.get("buy_pressure_10t", 50.0) or 50.0)
        accel = float(features.get("tick_acceleration_ratio", 0.0) or 0.0)
        latest_strength = float(features.get("latest_strength", 0.0) or 0.0)
        has_reclaim = (
            (micro_vwap_usable and float(features.get("curr_vs_micro_vwap_bp", 0.0) or 0.0) > 0)
            or (pressure_usable and int(features.get("same_price_buy_absorption", 0) or 0) >= 2)
        )

        instant_strength_only = (
            pressure_usable
            and micro_vwap_usable
            and buy_pressure >= 70.0
            and accel >= 1.1
            and latest_strength >= 110.0
            and not has_reclaim
        )

        if risk_flags >= 2 or instant_strength_only:
            score = int(result.get("score", 50))
            result["action"] = "WAIT"
            result["score"] = min(score, 74)
            result["reason"] = f"{result.get('reason', '')} | remote_buy_guard(risk={risk_flags})"
        return result

    def _annotate_entry_numeric_consistency(self, result, *, prompt_type, feature_packet):
        if prompt_type not in {"scalping_entry", "scalping_shared"}:
            return result
        payload = dict(result or {}) if isinstance(result, dict) else {}
        reason = str(payload.get("reason") or "").strip()
        if not reason:
            return payload
        lowered = reason.lower()
        contradiction = False
        inconsistency_field = ""
        inconsistency_reason = ""
        detected_value = None

        def _feature_float(key, default=0.0):
            try:
                return float((feature_packet or {}).get(key, default) or default)
            except Exception:
                return float(default or 0.0)

        accel = _feature_float("tick_acceleration_ratio", 0.0)
        if "tick_acceleration_ratio" in lowered and accel >= 1.10:
            if re.search(r"tick_acceleration_ratio[^|]{0,100}<\s*1\.1", lowered):
                contradiction = True
            if re.search(r"tick_acceleration_ratio[^|]{0,100}(?:fails|not enough|not met|insufficient)", lowered):
                contradiction = True
            if re.search(r"tick_acceleration_ratio[^|]{0,100}not\s*>?=\s*1\.1", lowered):
                contradiction = True
            if contradiction:
                inconsistency_field = "tick_acceleration_ratio"
                inconsistency_reason = "tick_acceleration_pass_described_as_fail"
                detected_value = round(accel, 3)

        micro_vwap_bp = _feature_float("curr_vs_micro_vwap_bp", 0.0)
        ma5_bp = _feature_float("curr_vs_ma5_bp", 0.0)
        micro_vwap_pass = self._feature_packet_micro_vwap_usable(feature_packet) and micro_vwap_bp > 0.0
        ma5_pass = self._feature_packet_ma5_usable(feature_packet) and ma5_bp > 0.0
        position_pass = micro_vwap_pass or ma5_pass
        position_both_pass = micro_vwap_bp > 0.0 and ma5_bp > 0.0
        if not contradiction and position_pass and (
            "position" in lowered
            or "curr_vs_micro_vwap_bp" in lowered
            or "curr_vs_ma5_bp" in lowered
        ):
            position_fail_phrase = position_both_pass and (
                "position disadvantage" in lowered
                or "position deficit" in lowered
                or "position advantage not present" in lowered
            )
            both_positive_but_negated = position_both_pass and (
                "not both positive" in lowered
            )
            explicit_micro_contradiction = micro_vwap_pass and "curr_vs_micro_vwap_bp <= 0" in lowered
            explicit_ma5_contradiction = ma5_pass and "curr_vs_ma5_bp <= 0" in lowered
            if position_fail_phrase or both_positive_but_negated:
                contradiction = True
                inconsistency_field = "position_advantage"
                inconsistency_reason = "position_pass_described_as_fail"
                detected_value = {
                    "curr_vs_micro_vwap_bp": round(micro_vwap_bp, 3),
                    "curr_vs_ma5_bp": round(ma5_bp, 3),
                }
            elif explicit_micro_contradiction or explicit_ma5_contradiction:
                contradiction = True
                inconsistency_field = "position_advantage"
                inconsistency_reason = "position_value_described_with_wrong_sign"
                detected_value = {
                    "curr_vs_micro_vwap_bp": round(micro_vwap_bp, 3),
                    "curr_vs_ma5_bp": round(ma5_bp, 3),
                }

        buy_pressure = _feature_float("buy_pressure_10t", 50.0)
        net_aggressive_delta = _feature_float("net_aggressive_delta_10t", 0.0)
        pressure_usable = self._feature_packet_pressure_usable(feature_packet)
        supply_pass = pressure_usable and (buy_pressure >= 68.0 or net_aggressive_delta > 0.0)
        if not contradiction and supply_pass and (
            "buy_pressure_10t" in lowered
            or "buy pressure" in lowered
            or "supply-demand" in lowered
            or "supply demand" in lowered
            or "net_aggressive_delta_10t" in lowered
        ):
            supply_fail_phrase = (
                "buy_pressure_10t < 68" in lowered
                or "buy_pressure_10t low" in lowered
                or "supply-demand advantage not" in lowered
                or "supply demand advantage not" in lowered
            )
            if "insufficient buy pressure" in lowered and "or speed" not in lowered:
                supply_fail_phrase = True
            if supply_fail_phrase:
                contradiction = True
                inconsistency_field = "supply_demand_advantage"
                inconsistency_reason = "supply_demand_pass_described_as_fail"
                detected_value = {
                    "buy_pressure_10t": round(buy_pressure, 3),
                    "net_aggressive_delta_10t": round(net_aggressive_delta, 3),
                    "tick_aggressor_pressure_usable": bool(pressure_usable),
                    "tick_aggressor_trusted_count": (feature_packet or {}).get("tick_aggressor_trusted_count"),
                }

        action = str(payload.get("action") or "").upper()
        try:
            score = float(payload.get("score", payload.get("ai_score", 0.0)) or 0.0)
        except Exception:
            score = 0.0
        if not contradiction and action != "BUY":
            feature_pass_count = int(position_pass) + int(accel >= 1.10) + int(supply_pass)
            if feature_pass_count >= 3 and score >= 70.0 and (
                "insufficient buy" in lowered
                or "prevents buy" in lowered
                or "buy setup is incomplete" in lowered
                or "buy signals" in lowered
            ):
                contradiction = True
                inconsistency_field = "entry_feature_bundle"
                inconsistency_reason = "three_core_features_pass_described_as_no_buy"
                detected_value = {
                    "score": round(score, 3),
                    "tick_acceleration_ratio": round(accel, 3),
                    "buy_pressure_10t": round(buy_pressure, 3),
                    "tick_aggressor_pressure_usable": bool(pressure_usable),
                    "tick_aggressor_trusted_count": (feature_packet or {}).get("tick_aggressor_trusted_count"),
                    "curr_vs_micro_vwap_bp": round(micro_vwap_bp, 3),
                    "curr_vs_ma5_bp": round(ma5_bp, 3),
                }

        if not contradiction:
            return payload
        payload["ai_reason_numeric_inconsistency"] = True
        payload["ai_reason_feature_inconsistency"] = True
        payload["ai_reason_numeric_inconsistency_field"] = inconsistency_field or "entry_feature_bundle"
        payload["ai_reason_numeric_inconsistency_reason"] = (
            inconsistency_reason or "entry_feature_pass_described_as_fail"
        )
        payload["ai_reason_numeric_inconsistency_detected_value"] = detected_value
        payload["ai_reason_numeric_inconsistency_excerpt"] = reason[:120]
        return payload

    def _append_numeric_consistency_recheck_context(self, formatted_data, *, metadata_extra):
        if not isinstance(metadata_extra, dict):
            return formatted_data
        if str(metadata_extra.get("ai_numeric_consistency_recheck") or "").strip().lower() not in {
            "1",
            "true",
            "yes",
            "y",
        }:
            return formatted_data
        original_reason = str(metadata_extra.get("ai_numeric_consistency_recheck_original_reason_excerpt") or "-")[:160]
        inconsistency_field = str(metadata_extra.get("ai_numeric_consistency_recheck_inconsistency_field") or "-")[:80]
        inconsistency_reason = str(metadata_extra.get("ai_numeric_consistency_recheck_inconsistency_reason") or "-")[:120]
        detected_value = str(metadata_extra.get("ai_numeric_consistency_recheck_detected_value") or "-")[:240]
        correction_note = (
            "[Numeric consistency recheck]\n"
            f"- prior_reason_excerpt: {original_reason}\n"
            f"- contradiction_field: {inconsistency_field}\n"
            f"- contradiction_reason: {inconsistency_reason}\n"
            f"- detected_value: {detected_value}\n"
            "- Re-evaluate using the same feature packet only.\n"
            "- If the corrected decision is still WAIT, explain using non-contradictory missing conditions only.\n"
            "- Do not describe a passing quantitative feature as failed.\n"
        )
        if isinstance(formatted_data, str):
            stripped = formatted_data.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    payload = json.loads(stripped)
                except Exception:
                    payload = None
                if isinstance(payload, dict):
                    payload["numeric_consistency_recheck_context"] = {
                        "prior_reason_excerpt": original_reason,
                        "contradiction_field": inconsistency_field,
                        "contradiction_reason": inconsistency_reason,
                        "detected_value": detected_value,
                        "instruction": (
                            "Re-evaluate using the same feature packet only. "
                            "If the corrected decision is still WAIT, explain using non-contradictory missing conditions only."
                        ),
                    }
                    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
            return f"{formatted_data}\n\n{correction_note}"
        return formatted_data

    def _append_early_accel_strong_bundle_recheck_context(self, formatted_data, *, metadata_extra):
        if not isinstance(metadata_extra, dict):
            return formatted_data
        if str(metadata_extra.get("early_accel_strong_bundle_recheck") or "").strip().lower() not in {
            "1",
            "true",
            "yes",
            "y",
        }:
            return formatted_data
        original_reason = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_original_reason_excerpt") or "-"
        )[:160]
        original_action = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_original_action") or "-"
        )[:32]
        original_score = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_original_score") or "0.0"
        )[:32]
        promotion_reason = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_scanner_promotion_reason") or "-"
        )[:120]
        source_signature = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_source_signature") or "-"
        )[:160]
        price_delta = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_price_delta_since_first_seen_pct") or "0.00"
        )[:32]
        comparable_flu_delta = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_comparable_flu_delta_since_first_seen") or "0.00"
        )[:32]
        cntr_str_available = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_cntr_str_available") or "false"
        )[:8]
        cntr_str = str(metadata_extra.get("early_accel_strong_bundle_recheck_cntr_str") or "0.0")[:32]
        tick_accel = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_tick_acceleration_ratio") or "0.000"
        )[:32]
        micro_vwap_bp = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_curr_vs_micro_vwap_bp") or "0.00"
        )[:32]
        micro_vwap_available = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_micro_vwap_available") or "false"
        )[:8]
        minute_candle_context_quality = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_minute_candle_context_quality") or "unknown"
        )[:80]
        minute_candle_window_fresh = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_minute_candle_window_fresh") or "false"
        )[:8]
        minute_candle_latest_age_ms = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_minute_candle_latest_age_ms") or "0"
        )[:32]
        buy_pressure_10t = str(
            metadata_extra.get("early_accel_strong_bundle_recheck_buy_pressure_10t") or "0.00"
        )[:32]
        correction_note = (
            "[Early acceleration strong-bundle recheck]\n"
            f"- original_action: {original_action}\n"
            f"- original_score: {original_score}\n"
            f"- prior_reason_excerpt: {original_reason}\n"
            f"- scanner_promotion_reason: {promotion_reason}\n"
            f"- source_signature: {source_signature}\n"
            f"- price_delta_since_first_seen_pct: {price_delta}\n"
            f"- comparable_flu_delta_since_first_seen: {comparable_flu_delta}\n"
            f"- cntr_str_available: {cntr_str_available}\n"
            f"- cntr_str: {cntr_str}\n"
            f"- tick_acceleration_ratio: {tick_accel}\n"
            f"- curr_vs_micro_vwap_bp: {micro_vwap_bp}\n"
            f"- micro_vwap_available: {micro_vwap_available}\n"
            f"- minute_candle_context_quality: {minute_candle_context_quality}\n"
            f"- minute_candle_window_fresh: {minute_candle_window_fresh}\n"
            f"- minute_candle_latest_age_ms: {minute_candle_latest_age_ms}\n"
            f"- buy_pressure_10t: {buy_pressure_10t}\n"
            "- Re-evaluate using the same feature packet only.\n"
            "- This is not a score-threshold relaxation. BUY is allowed only if the same packet supports it.\n"
            "- If the corrected decision is still WAIT, explain using the missing conditions only.\n"
        )
        if isinstance(formatted_data, str):
            stripped = formatted_data.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    payload = json.loads(stripped)
                except Exception:
                    payload = None
                if isinstance(payload, dict):
                    payload["early_accel_strong_bundle_recheck_context"] = {
                        "original_action": original_action,
                        "original_score": original_score,
                        "prior_reason_excerpt": original_reason,
                        "scanner_promotion_reason": promotion_reason,
                        "source_signature": source_signature,
                        "price_delta_since_first_seen_pct": price_delta,
                        "comparable_flu_delta_since_first_seen": comparable_flu_delta,
                        "cntr_str_available": cntr_str_available,
                        "cntr_str": cntr_str,
                        "tick_acceleration_ratio": tick_accel,
                        "curr_vs_micro_vwap_bp": micro_vwap_bp,
                        "micro_vwap_available": micro_vwap_available,
                        "minute_candle_context_quality": minute_candle_context_quality,
                        "minute_candle_window_fresh": minute_candle_window_fresh,
                        "minute_candle_latest_age_ms": minute_candle_latest_age_ms,
                        "buy_pressure_10t": buy_pressure_10t,
                        "instruction": (
                            "Re-evaluate using the same feature packet only. "
                            "BUY is allowed only if the same packet supports it without relaxing the score gate."
                        ),
                    }
                    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
            return f"{formatted_data}\n\n{correction_note}"
        return formatted_data

    # ==========================================
    # JSON 파싱
    # ==========================================

    def _parse_json_response_text(self, raw_text):
        text = str(raw_text or "").strip()
        if not text:
            raise ValueError("OpenAI 응답 텍스트가 비어 있음")

        candidates = [text]
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            candidates.append(fence_match.group(1).strip())

        block_match = re.search(r"\{.*\}", text, re.DOTALL)
        if block_match:
            candidates.append(block_match.group().strip())

        seen = set()
        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            try:
                parsed = json.loads(normalized)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue

        raise ValueError(f"JSON 형식을 찾을 수 없음: {text[:500]}...")

    def _extract_openai_response_text(self, response) -> str:
        raw_text = str(getattr(response, "output_text", "") or "").strip()
        if raw_text:
            return raw_text

        fragments = []
        for item in list(getattr(response, "output", []) or []):
            if isinstance(item, dict):
                content_items = list(item.get("content", []) or [])
            else:
                content_items = list(getattr(item, "content", []) or [])

            for content in content_items:
                if isinstance(content, dict):
                    text_value = (
                        content.get("text")
                        or content.get("value")
                        or ((content.get("output_text") or {}).get("text") if isinstance(content.get("output_text"), dict) else None)
                    )
                else:
                    text_value = (
                        getattr(content, "text", None)
                        or getattr(content, "value", None)
                    )
                    output_text = getattr(content, "output_text", None)
                    if not text_value and output_text is not None:
                        text_value = getattr(output_text, "text", None)
                if text_value:
                    fragments.append(str(text_value))

        return "\n".join(fragment.strip() for fragment in fragments if str(fragment).strip()).strip()

    # ==========================================
    # 핵심 API 호출기: _call_openai_safe
    # ==========================================

    def _parse_openai_transport_payload(self, raw_text, *, require_json):
        if require_json:
            return self._parse_json_response_text(raw_text)
        return str(raw_text or "").strip()

    def _is_invalid_prompt_error(self, exc) -> bool:
        text = str(exc or "").lower()
        return "invalid_prompt" in text or "invalid prompt" in text

    def _build_invalid_prompt_retry_request(self, request: OpenAIResponseRequest) -> OpenAIResponseRequest:
        if request.require_json:
            if request.schema_name == "holding_score_v2":
                safe_prompt = (
                    "Score the open scalping position using only the provided JSON. "
                    "Return JSON only with action HOLD, TRIM, or EXIT; score and confidence as 0-100 integers; "
                    "position_state, score_basis, risk_factors, support_factors, data_quality, and reason in English ASCII."
                )
            elif request.schema_name == "holding_exit_v1":
                safe_prompt = (
                    "Classify the provided market data. Use only the numeric fields in the input. "
                    "Return JSON only with action HOLD, TRIM, or EXIT; score as 0-100 integer; "
                    "reason as a short neutral numeric summary in English ASCII only."
                )
            else:
                safe_prompt = (
                    "Classify the provided market data. Use only the numeric fields in the input. "
                    "Return JSON only with action BUY, WAIT, or DROP; score as 0-100 integer; "
                    "reason as a short neutral numeric summary in English ASCII only."
                )
        else:
            safe_prompt = (
                "Analyze the provided market data using only numeric fields. "
                "Return a concise neutral report."
            )
        metadata = dict(request.metadata or {})
        metadata["invalid_prompt_retry"] = "true"
        metadata["original_endpoint_name"] = str(request.endpoint_name or "generic")
        metadata = self._sanitize_openai_metadata(metadata, context_name=request.context_name)
        return replace(
            request,
            prompt=self._wrap_openai_prompt_contract(
                safe_prompt,
                require_json=request.require_json,
                schema_name=request.schema_name,
                endpoint_name=request.endpoint_name,
            ),
            metadata=metadata,
        )

    def _call_openai_responses_http(self, request: OpenAIResponseRequest):
        use_schema_registry = self._should_use_openai_schema_registry(
            require_json=request.require_json,
            schema_name=request.schema_name,
        )
        invalid_prompt_retried = bool((request.metadata or {}).get("invalid_prompt_retry") == "true")
        last_error = ""
        provider_total_ms = 0
        last_provider_ms = 0
        attempts_made = 0
        last_error_type = "-"
        last_error_timeout_like = False
        for attempt in range(len(self.api_keys)):
            attempts_made = attempt + 1
            provider_started_at = time.perf_counter()
            try:
                response = self.client.responses.create(
                    **request.build_provider_payload(use_schema_registry=use_schema_registry),
                    timeout=max(0.05, request.remaining_timeout_sec()),
                )
                provider_ms = max(0, int((time.perf_counter() - provider_started_at) * 1000))
                last_provider_ms = provider_ms
                provider_total_ms += provider_ms
                self._rotate_client()
                raw_text = self._extract_openai_response_text(response)
                payload = self._parse_openai_transport_payload(raw_text, require_json=request.require_json)
                roundtrip_ms = max(0, int((time.perf_counter() - request.submitted_at_perf) * 1000))
                return OpenAITransportResult(
                    payload=payload,
                    transport_mode="http",
                    ws_used=False,
                    ws_http_fallback=False,
                    queue_wait_ms=0,
                    roundtrip_ms=roundtrip_ms,
                    usage_meta=_extract_openai_usage_meta(response),
                    timing_meta={
                        "openai_http_provider_ms": provider_ms,
                        "openai_http_provider_total_ms": provider_total_ms,
                        "openai_http_attempt_count": attempt + 1,
                        "openai_http_sdk_max_retries": OPENAI_SDK_MAX_RETRIES,
                    },
                )
            except RateLimitError as e:
                last_provider_ms = max(0, int((time.perf_counter() - provider_started_at) * 1000))
                provider_total_ms += last_provider_ms
                last_error = str(e)
                last_error_type = type(e).__name__
                last_error_timeout_like = False
                old_key = self.current_key[-5:]
                self._rotate_client()
                warn_msg = (
                    f"⚠️ [OpenAI 한도 초과] {request.context_name} | "
                    f"{old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})"
                )
                print(warn_msg)
                log_error(warn_msg)
                remaining = request.remaining_timeout_sec()
                if remaining <= 0.05:
                    break
                time.sleep(min(0.8, max(0.0, remaining - 0.05)))
                continue
            except Exception as e:
                last_provider_ms = max(0, int((time.perf_counter() - provider_started_at) * 1000))
                provider_total_ms += last_provider_ms
                last_error = str(e).lower()
                last_error_type = type(e).__name__
                last_error_timeout_like = self._is_openai_timeout_like_error(e)
                if self._is_invalid_prompt_error(e) and not invalid_prompt_retried:
                    log_error(
                        f"⚠️ [OpenAI invalid_prompt retry] {request.context_name} | "
                        "retrying with minimal numeric JSON prompt"
                    )
                    invalid_prompt_retried = True
                    request = self._build_invalid_prompt_retry_request(request)
                    continue
                if last_error_timeout_like:
                    remaining = request.remaining_timeout_sec()
                    if remaining <= 0.05:
                        break
                    log_info(
                        f"⚠️ [OpenAI timeout retry] {request.context_name} | "
                        f"remaining_budget_ms={int(remaining * 1000)} ({attempt+1}/{len(self.api_keys)})"
                    )
                    time.sleep(min(0.8, max(0.0, remaining - 0.05)))
                    continue
                if any(
                    x in last_error
                    for x in ["429", "quota", "503", "unavailable", "server", "too_many_requests"]
                ):
                    old_key = self.current_key[-5:]
                    self._rotate_client()
                    print(
                        f"⚠️ [OpenAI 서버 에러] {request.context_name} | "
                        f"{old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})"
                    )
                    if request.remaining_timeout_sec() <= 0.05:
                        break
                    time.sleep(min(0.8, max(0.0, request.remaining_timeout_sec() - 0.05)))
                    continue
                raise RuntimeError(f"OpenAI Responses HTTP 응답/파싱 실패: {e}") from e
        if last_error_timeout_like:
            fatal_msg = (
                "OpenAI Responses HTTP timeout budget exhausted: "
                f"endpoint={request.endpoint_name}, attempts={attempts_made}, "
                f"budget_ms={int(request.timeout_ms)}, provider_total_ms={provider_total_ms}, "
                f"last_error={last_error}"
            )
            log_info(f"⚠️ [{request.context_name}] {fatal_msg}")
        else:
            fatal_msg = f"🚨 [AI 고갈] 모든 OpenAI API 키 사용 불가. 마지막 에러: {last_error}"
            log_error(fatal_msg)
        raise OpenAIResponsesHTTPError(
            fatal_msg,
            timing_meta={
                "openai_http_provider_ms": last_provider_ms,
                "openai_http_provider_total_ms": provider_total_ms,
                "openai_http_attempt_count": attempts_made,
                "openai_http_error_type": last_error_type,
                "openai_http_timeout_budget_exhausted": bool(last_error_timeout_like),
                "openai_http_sdk_max_retries": OPENAI_SDK_MAX_RETRIES,
            },
        )

    def _call_openai_responses_ws(self, request: OpenAIResponseRequest):
        pool = self._get_responses_ws_pool()
        use_schema_registry = self._should_use_openai_schema_registry(
            require_json=request.require_json,
            schema_name=request.schema_name,
        )
        return pool.submit(
            self._build_responses_ws_attempt_request(request),
            use_schema_registry=use_schema_registry,
        )

    def _build_responses_ws_attempt_request(self, request: OpenAIResponseRequest):
        remaining_ms = max(1, int(request.remaining_timeout_sec() * 1000))
        configured_ws_ms = max(
            1,
            int(getattr(TRADING_RULES, "OPENAI_RESPONSES_WS_TIMEOUT_MS", remaining_ms) or remaining_ms),
        )
        configured_reserve_ms = max(
            1,
            int(
                getattr(
                    TRADING_RULES,
                    "OPENAI_RESPONSES_WS_HTTP_FALLBACK_RESERVE_MS",
                    2000,
                )
                or 2000
            ),
        )
        min_ws_attempt_ms = min(700, max(50, remaining_ms // 2))
        reserve_ms = min(
            configured_reserve_ms,
            max(1, remaining_ms - min_ws_attempt_ms),
        )
        attempt_ms = min(configured_ws_ms, max(min_ws_attempt_ms, remaining_ms - reserve_ms))
        if attempt_ms >= remaining_ms:
            return request
        metadata = dict(request.metadata or {})
        metadata["ws_attempt_timeout_ms"] = str(attempt_ms)
        metadata["ws_http_fallback_reserve_ms"] = str(reserve_ms)
        metadata["ws_total_timeout_ms"] = str(request.timeout_ms)
        return replace(
            request,
            submitted_at_perf=time.perf_counter(),
            timeout_ms=attempt_ms,
            metadata=self._sanitize_openai_metadata(metadata, context_name=request.context_name),
        )

    def _call_openai_safe(
        self,
        prompt,
        user_input,
        require_json=True,
        context_name="Unknown",
        model_override=None,
        temperature_override=None,
        schema_name=None,
        endpoint_name="generic",
        symbol="-",
        cache_key="-",
        metadata_extra=None,
    ):
        """Responses API HTTP/WS transport와 예외 처리를 전담하는 중앙 호출기."""
        target_model = model_override if model_override else self.current_model_name
        target_temp = self._resolve_openai_temperature(
            require_json=bool(require_json),
            temperature_override=temperature_override,
            model_name=target_model,
        )
        max_output_tokens = self._resolve_openai_max_output_tokens(require_json=bool(require_json))
        reasoning_effort = self._resolve_openai_reasoning_effort(model_name=target_model)
        request = self._build_openai_response_request(
            prompt=prompt,
            user_input=user_input,
            require_json=bool(require_json),
            context_name=context_name,
            model_name=target_model,
            temperature=target_temp,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            schema_name=schema_name,
            endpoint_name=endpoint_name,
            symbol=symbol,
            cache_key=cache_key,
            metadata_extra=metadata_extra,
        )
        transport_meta = {
            "openai_transport_mode": "http",
            "openai_ws_used": False,
            "openai_ws_http_fallback": False,
            "openai_ws_queue_wait_ms": 0,
            "openai_ws_roundtrip_ms": 0,
            "openai_request_id": request.request_id,
            "openai_endpoint_name": request.endpoint_name,
            "openai_schema_name": request.schema_name or "-",
        }
        bedrock_primary_payload = self._try_bedrock_primary_provider(request=request, transport_meta=transport_meta)
        if isinstance(bedrock_primary_payload, dict):
            return bedrock_primary_payload
        result = None
        if self._should_use_responses_ws(request):
            try:
                result = self._call_openai_responses_ws(request)
                transport_meta.update(
                    {
                        "openai_transport_mode": result.transport_mode,
                        "openai_ws_used": bool(result.ws_used),
                        "openai_ws_http_fallback": bool(result.ws_http_fallback),
                        "openai_ws_queue_wait_ms": int(result.queue_wait_ms),
                        "openai_ws_roundtrip_ms": int(result.roundtrip_ms),
                    }
                )
            except Exception as e:
                remaining = request.remaining_timeout_sec()
                if isinstance(e, TimeoutError):
                    self._record_ws_metric("openai_ws_timeout_reject", 1)
                transport_meta.update(
                    {
                        "openai_transport_mode": "responses_ws",
                        "openai_ws_used": True,
                        "openai_ws_http_fallback": False,
                        "openai_ws_error_type": type(e).__name__,
                    }
                )
                if isinstance(e, (OpenAIWSRequestIdMismatchError, OpenAIWSLateResponseError)):
                    self._set_last_transport_meta(transport_meta)
                    log_error(f"🚨 [OpenAI WS fail-closed] {context_name}: {e}")
                    raise
                if remaining <= 0.05:
                    self._set_last_transport_meta(transport_meta)
                    raise
                self._record_ws_metric("openai_ws_http_fallback", 1)
                fallback_timeout_ms = max(50, int(remaining * 1000))
                transport_meta["openai_ws_elapsed_before_fallback_ms"] = max(
                    0,
                    int((time.perf_counter() - request.submitted_at_perf) * 1000),
                )
                transport_meta["openai_http_fallback_budget_ms"] = fallback_timeout_ms
                transport_meta["openai_original_timeout_ms"] = int(request.timeout_ms)
                fallback_request = OpenAIResponseRequest(
                    prompt=request.prompt,
                    user_input=request.user_input,
                    require_json=request.require_json,
                    context_name=request.context_name,
                    model_name=request.model_name,
                    temperature=request.temperature,
                    max_output_tokens=request.max_output_tokens,
                    reasoning_effort=request.reasoning_effort,
                    schema_name=request.schema_name,
                    endpoint_name=request.endpoint_name,
                    request_id=request.request_id,
                    symbol=request.symbol,
                    cache_key=request.cache_key,
                    submitted_at_perf=time.perf_counter(),
                    timeout_ms=fallback_timeout_ms,
                    metadata=dict(request.metadata or {}),
                )
                http_lock_wait_started = time.perf_counter()
                with self.api_call_lock:
                    transport_meta["openai_http_lock_wait_ms"] = max(
                        0,
                        int((time.perf_counter() - http_lock_wait_started) * 1000),
                    )
                    try:
                        result = self._call_openai_responses_http(fallback_request)
                    except Exception as fallback_error:
                        if getattr(fallback_error, "timing_meta", None):
                            transport_meta.update(fallback_error.timing_meta)
                        if not self._is_openai_timeout_like_error(fallback_error):
                            raise
                        result = self._build_ws_http_fallback_timeout_result(
                            fallback_request,
                            error=fallback_error,
                        )
                        if result is None:
                            raise
                        transport_meta["openai_ws_http_fallback_fail_closed"] = True
                        transport_meta["openai_ws_http_fallback_error_type"] = type(fallback_error).__name__
                        log_info(
                            f"⚠️ [OpenAI WS HTTP fallback fail-closed] "
                            f"{context_name}: {fallback_error}"
                        )
                result.ws_http_fallback = True
                transport_meta.update(
                    {
                        "openai_transport_mode": result.transport_mode,
                        "openai_ws_used": False,
                        "openai_ws_http_fallback": True,
                        "openai_ws_queue_wait_ms": transport_meta.get("openai_ws_queue_wait_ms", 0),
                        "openai_ws_roundtrip_ms": int(result.roundtrip_ms),
                    }
                )
                fallback_msg = f"⚠️ [OpenAI WS fallback] {context_name}: {e}"
                log_info(fallback_msg)
        else:
            http_lock_wait_started = time.perf_counter()
            with self.api_call_lock:
                transport_meta["openai_http_lock_wait_ms"] = max(
                    0,
                    int((time.perf_counter() - http_lock_wait_started) * 1000),
                )
                result = self._call_openai_responses_http(request)
            transport_meta.update(
                {
                    "openai_transport_mode": result.transport_mode,
                    "openai_ws_used": False,
                    "openai_ws_http_fallback": False,
                    "openai_ws_queue_wait_ms": 0,
                    "openai_ws_roundtrip_ms": int(result.roundtrip_ms),
                }
            )
        if getattr(result, "timing_meta", None):
            transport_meta.update(result.timing_meta)
        if getattr(result, "usage_meta", None):
            transport_meta.update(result.usage_meta)
        self._set_last_transport_meta(transport_meta)
        if isinstance(result.payload, dict):
            return result.payload
        return str(result.payload or "").strip()

    def _try_bedrock_primary_provider(self, *, request: OpenAIResponseRequest, transport_meta: dict[str, Any]):
        if not bool(request.require_json):
            return None
        model_name = str(request.model_name or "")
        if str(request.endpoint_name or "") == "entry_price":
            configured_route_mode = os.getenv("KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE", "off")
        elif model_name == "gpt-5.4-mini":
            configured_route_mode = os.getenv("KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE", "shadow")
        else:
            return None
        if str(configured_route_mode or "").strip().lower() != "primary":
            return None
        if str(request.endpoint_name or "") == "entry_price":
            return self._try_entry_price_bedrock_primary_provider(request=request, transport_meta=transport_meta)
        try:
            from src.engine.bedrock_nova_provider import (
                BedrockNovaProviderError,
                endpoint_allowed_for_lite_primary,
                provider_audit_row,
                route_mode_for_model,
                runtime_provider,
                write_provider_audit_row,
            )

            route_mode, profile = route_mode_for_model(request.model_name)
            if route_mode != "primary" or profile is None:
                return None
            if str(request.model_name or "") == "gpt-5.4-mini" and not endpoint_allowed_for_lite_primary(
                request.endpoint_name
            ):
                return None
            result = runtime_provider().converse(prompt=request.prompt or "", user_input=request.user_input, profile=profile)
            request_meta = self._build_bedrock_shadow_request_meta(request=request, transport_meta=transport_meta, roundtrip_ms=result.latency_ms)
            request_meta["request_id"] = request.request_id
            if not result.parse_ok or not isinstance(result.payload, dict) or not result.payload:
                write_provider_audit_row(
                    provider_audit_row(
                        request_meta=request_meta,
                        result=result,
                        payload=result.payload,
                        error_type=result.parse_error or "parse_failed",
                    )
                )
                raise BedrockNovaProviderError(
                    result.parse_error or "Bedrock Nova primary returned invalid JSON",
                    error_type=result.parse_error or "parse_failed",
                    attempts=result.attempted_key_count,
                )
            transport_meta.update(result.transport_meta())
            transport_meta.update(
                {
                    "openai_transport_mode": "bedrock_primary",
                    "openai_ws_used": False,
                    "openai_ws_http_fallback": False,
                    "openai_ws_roundtrip_ms": int(result.latency_ms),
                    "bedrock_primary_used": True,
                    "bedrock_failback_used": False,
                }
            )
            self._set_last_transport_meta(transport_meta)
            write_provider_audit_row(provider_audit_row(request_meta=request_meta, result=result, payload=result.payload))
            return result.payload
        except Exception as exc:
            failback_enabled = str(os.getenv("KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI", "true")).strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
                "on",
            }
            transport_meta.update(
                {
                    "bedrock_primary_used": False,
                    "bedrock_failback_used": True,
                    "bedrock_failback_error_type": type(exc).__name__,
                }
            )
            try:
                from src.engine.bedrock_nova_provider import provider_audit_row, write_provider_audit_row

                request_meta = self._build_bedrock_shadow_request_meta(request=request, transport_meta=transport_meta, roundtrip_ms=0)
                request_meta["request_id"] = request.request_id
                write_provider_audit_row(
                    provider_audit_row(
                        request_meta=request_meta,
                        result=None,
                        payload={},
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
            except Exception:
                pass
            if not failback_enabled:
                raise
            log_error(f"⚠️ [Bedrock Nova primary failback] {request.context_name}: {type(exc).__name__}")
            return None

    def _try_entry_price_bedrock_primary_provider(self, *, request: OpenAIResponseRequest, transport_meta: dict[str, Any]):
        try:
            from src.engine.bedrock_nova_provider import (
                BedrockNovaProviderError,
                entry_price_bedrock_route_mode,
                entry_price_failback_enabled,
                entry_price_failback_profile_from_env,
                entry_price_primary_profile_from_env,
                provider_audit_row,
                runtime_provider,
                write_provider_audit_row,
            )
        except Exception:
            return None

        primary_profile = entry_price_primary_profile_from_env()
        if primary_profile is None:
            return None
        request_meta = self._build_bedrock_shadow_request_meta(request=request, transport_meta=transport_meta, roundtrip_ms=0)
        request_meta["request_id"] = request.request_id
        request_meta["bedrock_primary_family"] = primary_profile.family
        request_meta["decision_authority"] = "runtime_primary_with_bedrock_failback_defensive_close"
        request_meta["route_mode"] = entry_price_bedrock_route_mode()

        try:
            provider = runtime_provider()
            result = provider.converse(prompt=request.prompt or "", user_input=request.user_input, profile=primary_profile)
            if not result.parse_ok or not isinstance(result.payload, dict) or not result.payload:
                request_meta["bedrock_model_family"] = primary_profile.family
                write_provider_audit_row(
                    provider_audit_row(
                        request_meta=request_meta,
                        result=result,
                        payload=result.payload,
                        error_type=result.parse_error or "parse_failed",
                    )
                )
                raise BedrockNovaProviderError(
                    result.parse_error or "Bedrock entry_price primary returned invalid JSON",
                    error_type=result.parse_error or "parse_failed",
                    attempts=result.attempted_key_count,
                )
            request_meta["bedrock_model_family"] = primary_profile.family
            write_provider_audit_row(provider_audit_row(request_meta=request_meta, result=result, payload=result.payload))
            transport_meta.update(result.transport_meta())
            transport_meta.update(
                {
                    "openai_transport_mode": "bedrock_primary",
                    "openai_ws_used": False,
                    "openai_ws_http_fallback": False,
                    "openai_ws_roundtrip_ms": int(result.latency_ms),
                    "bedrock_primary_used": True,
                    "bedrock_failback_used": False,
                    "bedrock_model_family": primary_profile.family,
                    "bedrock_primary_family": primary_profile.family,
                }
            )
            self._set_last_transport_meta(transport_meta)
            return result.payload
        except Exception as primary_exc:
            primary_error_type = type(primary_exc).__name__
            request_meta["bedrock_model_family"] = primary_profile.family
            request_meta["bedrock_primary_error_type"] = primary_error_type
            try:
                write_provider_audit_row(
                    provider_audit_row(
                        request_meta=request_meta,
                        result=None,
                        payload={},
                        error_type=primary_error_type,
                        error_message=str(primary_exc),
                    )
                )
            except Exception:
                pass

            failback_profile = entry_price_failback_profile_from_env() if entry_price_failback_enabled() else None
            if failback_profile is None:
                transport_meta.update(
                    {
                        "bedrock_primary_used": False,
                        "bedrock_failback_used": False,
                        "bedrock_primary_error_type": primary_error_type,
                        "bedrock_primary_family": primary_profile.family,
                    }
                )
                self._set_last_transport_meta(transport_meta)
                raise
            try:
                provider = runtime_provider()
                failback_result = provider.converse(
                    prompt=request.prompt or "",
                    user_input=request.user_input,
                    profile=failback_profile,
                )
                failback_meta = dict(request_meta)
                failback_meta.update(
                    {
                        "bedrock_model_family": failback_profile.family,
                        "bedrock_failback_family": failback_profile.family,
                        "bedrock_failback_used": True,
                        "bedrock_primary_error_type": primary_error_type,
                    }
                )
                if (
                    not failback_result.parse_ok
                    or not isinstance(failback_result.payload, dict)
                    or not failback_result.payload
                ):
                    write_provider_audit_row(
                        provider_audit_row(
                            request_meta=failback_meta,
                            result=failback_result,
                            payload=failback_result.payload,
                            error_type=failback_result.parse_error or "parse_failed",
                        )
                    )
                    raise BedrockNovaProviderError(
                        failback_result.parse_error or "Bedrock entry_price failback returned invalid JSON",
                        error_type=failback_result.parse_error or "parse_failed",
                        attempts=failback_result.attempted_key_count,
                    )
                write_provider_audit_row(
                    provider_audit_row(request_meta=failback_meta, result=failback_result, payload=failback_result.payload)
                )
                transport_meta.update(failback_result.transport_meta())
                transport_meta.update(
                    {
                        "openai_transport_mode": "bedrock_primary",
                        "openai_ws_used": False,
                        "openai_ws_http_fallback": False,
                        "openai_ws_roundtrip_ms": int(failback_result.latency_ms),
                        "bedrock_primary_used": False,
                        "bedrock_failback_used": True,
                        "bedrock_primary_error_type": primary_error_type,
                        "bedrock_model_family": failback_profile.family,
                        "bedrock_primary_family": primary_profile.family,
                        "bedrock_failback_family": failback_profile.family,
                    }
                )
                self._set_last_transport_meta(transport_meta)
                log_error(f"⚠️ [Bedrock entry_price primary failback] {request.context_name}: {primary_error_type}")
                return failback_result.payload
            except Exception as failback_exc:
                failback_meta = dict(request_meta)
                failback_meta.update(
                    {
                        "bedrock_model_family": failback_profile.family,
                        "bedrock_failback_family": failback_profile.family,
                        "bedrock_failback_used": True,
                        "bedrock_primary_error_type": primary_error_type,
                    }
                )
                try:
                    write_provider_audit_row(
                        provider_audit_row(
                            request_meta=failback_meta,
                            result=None,
                            payload={},
                            error_type=type(failback_exc).__name__,
                            error_message=str(failback_exc),
                        )
                    )
                except Exception:
                    pass
                transport_meta.update(
                    {
                        "bedrock_primary_used": False,
                        "bedrock_failback_used": True,
                        "bedrock_primary_error_type": primary_error_type,
                        "bedrock_failback_error_type": type(failback_exc).__name__,
                        "bedrock_primary_family": primary_profile.family,
                        "bedrock_failback_family": failback_profile.family,
                    }
                )
                self._set_last_transport_meta(transport_meta)
                raise

    def _build_bedrock_shadow_request_meta(self, *, request, transport_meta, roundtrip_ms=0):
        return {
            "openai_request_id": transport_meta.get("openai_request_id") or request.request_id,
            "endpoint_name": request.endpoint_name,
            "prompt_type": request.endpoint_name,
            "symbol": request.symbol,
            "cache_key": request.cache_key,
            "pipeline_stage": request.endpoint_name,
            "record_id": (request.metadata or {}).get("record_id"),
            "sim_record_id": (request.metadata or {}).get("sim_record_id"),
            "sim_parent_record_id": (request.metadata or {}).get("sim_parent_record_id"),
            "entry_adm_candidate_id": (request.metadata or {}).get("entry_adm_candidate_id"),
            "source_event_stage": (request.metadata or {}).get("source_event_stage"),
            "pipeline_event_emitted_at": (request.metadata or {}).get("pipeline_event_emitted_at"),
            "openai_latency_ms": roundtrip_ms or transport_meta.get("openai_ws_roundtrip_ms") or 0,
        }

    # ==========================================
    # 데이터 포맷팅
    # ==========================================

    def _extract_quote_snapshot(self, ws_data):
        ws = ws_data if isinstance(ws_data, dict) else {}
        orderbook = ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
        asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        best_ask = 0
        best_bid = 0
        try:
            best_ask = int(float((asks[0] or {}).get("price", 0))) if asks else 0
        except Exception:
            best_ask = 0
        try:
            best_bid = int(float((bids[0] or {}).get("price", 0))) if bids else 0
        except Exception:
            best_bid = 0
        spread = best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0
        spread_bp = round((spread / best_bid) * 10000.0, 3) if spread > 0 and best_bid > 0 else 0.0
        return {
            "best_ask": best_ask,
            "best_bid": best_bid,
            "spread": spread,
            "spread_bp": spread_bp,
            "ask_total_depth": ws.get("ask_tot"),
            "bid_total_depth": ws.get("bid_tot"),
        }

    def _compact_recent_ticks(self, recent_ticks, *, limit=5):
        return [
            {
                "time": tick.get("time"),
                "dir": self._display_tick_dir(tick),
                "aggressor_source": tick.get("aggressor_source", tick.get("dir_source", "-")),
                "aggressor_quality": tick.get("aggressor_quality", "-"),
                "price": tick.get("price", tick.get("현재가", tick.get("체결가"))),
                "volume": tick.get("volume", tick.get("qty", tick.get("체결량"))),
                "strength": tick.get("strength", 0),
            }
            for tick in (recent_ticks or [])[:limit]
            if isinstance(tick, dict)
        ]

    def _display_tick_dir(self, tick):
        if not isinstance(tick, dict):
            return "UNKNOWN"
        source = str(tick.get("aggressor_source") or tick.get("dir_source") or "").strip()
        side = str(tick.get("aggressor_side") or tick.get("dir") or tick.get("side") or "UNKNOWN").upper()
        if source == "price_change_heuristic":
            return "UNKNOWN"
        return side if side in {"BUY", "SELL"} else "UNKNOWN"

    def _compact_recent_candles(self, recent_candles, *, limit=5):
        return [
            {
                "time": candle.get("체결시간", candle.get("time")),
                "open": candle.get("시가", candle.get("open", candle.get("현재가", candle.get("close", 0)))),
                "high": candle.get("고가", candle.get("high")),
                "low": candle.get("저가", candle.get("low")),
                "close": candle.get("현재가", candle.get("close", candle.get("종가"))),
                "volume": candle.get("거래량", candle.get("volume")),
            }
            for candle in (recent_candles or [])[-limit:]
            if isinstance(candle, dict)
        ]

    def _compact_holding_score_feature_packet(self, packet, audit_fields=None):
        payload = packet if isinstance(packet, dict) else {}
        audit = audit_fields if isinstance(audit_fields, dict) else {}
        keep_keys = (
            "packet_version",
            "curr_price",
            "latest_strength",
            "spread_bp",
            "top1_depth_ratio",
            "top3_depth_ratio",
            "orderbook_total_ratio",
            "microprice_edge_bp",
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "price_change_10t_pct",
            "tick_acceleration_ratio",
            "tick_accel_source",
            "tick_sample_count",
            "tick_latest_age_ms",
            "tick_context_quality",
            "tick_aggressor_trusted_count",
            "tick_aggressor_pressure_usable",
            "tick_aggressor_cached_orderbook_touch_count",
            "quote_age_ms",
            "quote_age_source",
            "quote_stale",
            "same_price_buy_absorption",
            "large_sell_print_detected",
            "large_buy_print_detected",
            "distance_from_day_high_pct",
            "intraday_range_pct",
            "volume_ratio_pct",
            "curr_vs_micro_vwap_bp",
            "micro_vwap_available",
            "curr_vs_ma5_bp",
            "ma5_available",
            "microstructure_reaction_context_status",
            "microstructure_reaction_tick_aggressor_pressure_usable",
            "microstructure_reaction_tick_aggressor_trusted_count",
            "microstructure_reaction_ask_sweep_score",
            "microstructure_reaction_post_sweep_hold_score",
            "microstructure_reaction_bid_replenishment_score",
            "microstructure_reaction_wall_replenishment_risk_score",
            "microstructure_reaction_vi_proximity_risk",
            "microstructure_reaction_entry_reaction_quality",
            "microstructure_reaction_source_quality",
        )
        compact = {key: payload.get(key) for key in keep_keys if key in payload}
        compact["aggressor_quality"] = {
            "orderbook_touch": payload.get("tick_aggressor_orderbook_touch_count", 0),
            "cached_orderbook_touch": payload.get("tick_aggressor_cached_orderbook_touch_count", 0),
            "price_heuristic": payload.get("tick_aggressor_price_heuristic_count", 0),
            "unknown": payload.get("tick_aggressor_unknown_count", 0),
        }
        compact["source_quality_flags"] = {
            "tick_source_quality_fields_sent": bool(audit.get("tick_source_quality_fields_sent", False)),
            "microstructure_reaction_context_sent": bool(
                audit.get("microstructure_reaction_context_sent", False)
            ),
            "tick_context_stale": audit.get(
                "tick_context_stale",
                payload.get("tick_context_stale", "not_available_tick_latest_age"),
            ),
            "quote_stale": audit.get("quote_stale", payload.get("quote_stale", "not_available_quote_age")),
            "tick_aggressor_pressure_usable": payload.get("tick_aggressor_pressure_usable", False),
            "tick_aggressor_trusted_count": payload.get("tick_aggressor_trusted_count", 0),
        }
        return compact

    def _summarize_tick_windows(self, recent_ticks, *, windows=(5, 10, 20)):
        ticks = [tick for tick in (recent_ticks or []) if isinstance(tick, dict)]

        def _price(tick):
            return self._safe_float(tick.get("price", tick.get("현재가", tick.get("체결가", 0))), 0.0)

        def _volume(tick):
            return self._safe_float(tick.get("volume", tick.get("qty", tick.get("체결량", 0))), 0.0)

        def _is_buy_tick(tick):
            inferred = infer_tick_aggressor_side(tick)
            return inferred.get("side") == "BUY" and inferred.get("source") != "price_change_heuristic"

        def _is_sell_tick(tick):
            inferred = infer_tick_aggressor_side(tick)
            return inferred.get("side") == "SELL" and inferred.get("source") != "price_change_heuristic"

        summary = {}
        for window in windows:
            sample = ticks[:window]
            if not sample:
                summary[str(window)] = {"count": 0}
                continue
            buy_vol = sum(_volume(tick) for tick in sample if _is_buy_tick(tick))
            sell_vol = sum(_volume(tick) for tick in sample if _is_sell_tick(tick))
            total = buy_vol + sell_vol
            latest = _price(sample[0])
            oldest = _price(sample[-1])
            summary[str(window)] = {
                "count": len(sample),
                "price_delta_pct": round(((latest - oldest) / oldest * 100.0), 4) if oldest > 0 else 0.0,
                "buy_pressure_pct": round((buy_vol / total * 100.0), 3) if total > 0 else 0.0,
                "buy_volume": int(buy_vol),
                "sell_volume": int(sell_vol),
                "large_sell_print_count": sum(
                    1
                    for tick in sample
                    if _is_sell_tick(tick)
                    and _volume(tick) >= max(1.0, total * 0.15)
                ),
            }
        return summary

    def _summarize_candle_windows(self, recent_candles, *, windows=(3, 5, 10)):
        candles = [candle for candle in (recent_candles or []) if isinstance(candle, dict)]

        def _field(candle, *names):
            for name in names:
                if name in candle:
                    return candle.get(name)
            return 0

        summary = {}
        for window in windows:
            sample = candles[-window:]
            if len(sample) < 2:
                summary[str(window)] = {"count": len(sample)}
                continue
            first_close = self._safe_float(_field(sample[0], "현재가", "close", "종가"), 0.0)
            last_close = self._safe_float(_field(sample[-1], "현재가", "close", "종가"), 0.0)
            highs = [self._safe_float(_field(item, "고가", "high"), 0.0) for item in sample]
            lows = [self._safe_float(_field(item, "저가", "low"), 0.0) for item in sample]
            vols = [self._safe_float(_field(item, "거래량", "volume"), 0.0) for item in sample]
            avg_prev_vol = sum(vols[:-1]) / max(1, len(vols) - 1)
            summary[str(window)] = {
                "count": len(sample),
                "close_slope_pct": round(((last_close - first_close) / first_close * 100.0), 4)
                if first_close > 0
                else 0.0,
                "range_pct": round(((max(highs) - min(lows)) / min(lows) * 100.0), 4)
                if lows and min(lows) > 0
                else 0.0,
                "latest_volume_ratio": round((vols[-1] / avg_prev_vol), 4) if avg_prev_vol > 0 else 0.0,
            }
        return summary

    def _build_entry_screen_v2_payload(self, ws_data, recent_ticks, recent_candles, *, feature_packet=None):
        ws = ws_data if isinstance(ws_data, dict) else {}
        if feature_packet is None:
            feature_packet = extract_scalping_feature_packet(ws, recent_ticks, recent_candles)
        quote = self._extract_quote_snapshot(ws)
        orderbook = ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
        asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        ws_age_sec = None
        try:
            raw_ts = float(ws.get("last_ws_update_ts", 0) or 0)
            ws_age_sec = round(max(0.0, time.time() - raw_ts), 3) if raw_ts > 0 else None
        except Exception:
            ws_age_sec = None
        return {
            "input_schema": "entry_screen_v2",
            "current": {
                "price": ws.get("curr"),
                "fluctuation_pct": ws.get("fluctuation", 0.0),
                "execution_strength": ws.get("v_pw", 0.0),
                "buy_ratio": ws.get("buy_ratio", 0.0),
            },
            "features": feature_packet,
            "quote_freshness": {
                "latency_state": ws.get("latency_state"),
                "ws_age_sec": ws_age_sec,
                "quote_stale": bool(ws.get("quote_stale", False)),
                **quote,
            },
            "orderbook_top3": {
                "asks": [
                    {"price": ask.get("price"), "volume": ask.get("volume")}
                    for ask in asks[:3]
                    if isinstance(ask, dict)
                ],
                "bids": [
                    {"price": bid.get("price"), "volume": bid.get("volume")}
                    for bid in bids[:3]
                    if isinstance(bid, dict)
                ],
            },
            "tick_summary": self._summarize_tick_windows(recent_ticks, windows=(5, 10)),
            "candle_summary": self._summarize_candle_windows(recent_candles, windows=(3, 5, 10)),
            "recent_ticks_latest_first": self._compact_recent_ticks(recent_ticks, limit=5),
            "recent_candles_latest_window": self._compact_recent_candles(recent_candles, limit=5),
            "source_quality": {
                "tick_count": len([tick for tick in (recent_ticks or []) if isinstance(tick, dict)]),
                "candle_count": len([candle for candle in (recent_candles or []) if isinstance(candle, dict)]),
                "orderbook_present": bool(asks or bids),
                "tick_context_quality": feature_packet.get("tick_context_quality"),
                "tick_context_stale": feature_packet.get("tick_context_stale"),
                "tick_accel_source": feature_packet.get("tick_accel_source"),
                "quote_age_ms": feature_packet.get("quote_age_ms"),
                "quote_stale": feature_packet.get("quote_stale"),
                "tick_latest_age_ms": feature_packet.get("tick_latest_age_ms"),
                "tick_aggressor_pressure_usable": feature_packet.get("tick_aggressor_pressure_usable", False),
                "tick_aggressor_trusted_count": feature_packet.get("tick_aggressor_trusted_count", 0),
                "tick_aggressor_price_heuristic_count": feature_packet.get("tick_aggressor_price_heuristic_count", 0),
                "micro_vwap_available": feature_packet.get("micro_vwap_available", False),
                "ma5_available": feature_packet.get("ma5_available", False),
                "minute_candle_window_fresh": feature_packet.get("minute_candle_window_fresh", False),
                "minute_candle_context_quality": feature_packet.get("minute_candle_context_quality"),
                "price_change_heuristic_is_not_aggressor": True,
            },
        }

    def _clean_hot_entry_value(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, float):
            return round(value, 4)
        if isinstance(value, (str, int, bool)):
            return value
        return value

    def _clean_hot_entry_payload(self, value):
        if isinstance(value, dict):
            cleaned = {}
            for key, item in value.items():
                cleaned_item = self._clean_hot_entry_payload(self._clean_hot_entry_value(item))
                if cleaned_item not in (None, {}, []):
                    cleaned[key] = cleaned_item
            return cleaned
        if isinstance(value, list):
            cleaned_list = [
                self._clean_hot_entry_payload(self._clean_hot_entry_value(item))
                for item in value
            ]
            return [item for item in cleaned_list if item not in (None, {}, [])]
        return self._clean_hot_entry_value(value)

    def _build_entry_hot_runtime_context(self, *, matrix_runtime, entry_adm_runtime, lifecycle_ai_runtime):
        context = {}
        if isinstance(matrix_runtime, dict):
            context["holding_exit_matrix"] = {
                "status": matrix_runtime.get("status"),
                "cache_token": matrix_runtime.get("cache_token"),
            }
        if isinstance(entry_adm_runtime, dict):
            entry_context = {
                "status": entry_adm_runtime.get("status"),
                "applied": entry_adm_runtime.get("applied"),
                "cache_token": entry_adm_runtime.get("cache_token"),
            }
            fields = entry_adm_runtime.get("fields")
            if isinstance(fields, dict):
                for key, value in fields.items():
                    if not str(key).startswith("entry_adm_"):
                        continue
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        entry_context[key] = value
                    if len(entry_context) >= 12:
                        break
            context["entry_adm"] = entry_context
        if isinstance(lifecycle_ai_runtime, dict):
            context["lifecycle_ai"] = {
                "status": lifecycle_ai_runtime.get("status"),
                "applied": lifecycle_ai_runtime.get("applied"),
                "cache_token": lifecycle_ai_runtime.get("cache_token"),
            }
        return self._clean_hot_entry_payload(context)

    def _build_entry_screen_hot_payload(
        self,
        ws_data,
        recent_ticks,
        recent_candles,
        *,
        feature_packet=None,
        matrix_runtime=None,
        entry_adm_runtime=None,
        lifecycle_ai_runtime=None,
    ):
        ws = ws_data if isinstance(ws_data, dict) else {}
        ticks = [tick for tick in (recent_ticks or []) if isinstance(tick, dict)]
        candles = [candle for candle in (recent_candles or []) if isinstance(candle, dict)]
        if feature_packet is None:
            feature_packet = extract_scalping_feature_packet(ws, ticks, candles)
        quote = self._extract_quote_snapshot(ws)
        orderbook = ws.get("orderbook") if isinstance(ws.get("orderbook"), dict) else {}
        asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        latest_tick = ticks[0] if ticks else {}
        hot_feature_keys = (
            "latest_strength",
            "entry_liquidity_score",
            "entry_liquidity_status",
            "fillability_score",
            "would_fill_now",
            "top1_bid_notional",
            "top1_ask_notional",
            "top3_bid_notional",
            "top3_ask_notional",
            "quote_depth_present",
            "quote_fresh_for_entry",
            "order_flow_pressure_score",
            "entry_order_flow_status",
            "order_flow_pressure_source",
            "entry_momentum_score",
            "entry_momentum_status",
            "entry_context_quality",
            "entry_context_missing_features",
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "same_price_buy_absorption",
            "tick_acceleration_ratio",
            "recent_5tick_seconds",
            "prev_5tick_seconds",
            "price_change_10t_pct",
            "curr_vs_micro_vwap_bp",
            "curr_vs_ma5_bp",
            "distance_from_day_high_pct",
            "intraday_range_pct",
            "micro_vwap_available",
            "ma5_available",
            "large_sell_print_detected",
            "large_buy_print_detected",
            "top3_depth_ratio",
            "orderbook_total_ratio",
            "ask_depth_ratio",
            "net_ask_depth",
            "spread_bp",
            "volume_ratio_pct",
            "quote_age_ms",
            "quote_stale",
            "tick_latest_age_ms",
            "tick_context_quality",
            "tick_context_stale",
            "tick_accel_source",
            "tick_aggressor_pressure_usable",
            "tick_aggressor_trusted_count",
            "tick_aggressor_price_heuristic_count",
            "minute_candle_window_fresh",
            "minute_candle_context_quality",
        )
        features = {
            key: feature_packet.get(key)
            for key in hot_feature_keys
            if isinstance(feature_packet, dict) and key in feature_packet
        }
        payload = {
            "input_schema": "entry_screen_hot_v1",
            "current": {
                "price": ws.get("curr"),
                "fluctuation_pct": ws.get("fluctuation", 0.0),
                "execution_strength": ws.get("v_pw", 0.0),
                "buy_ratio": ws.get("buy_ratio", 0.0),
            },
            "features": features,
            "quote": {
                "latency_state": ws.get("latency_state"),
                "quote_stale": bool(ws.get("quote_stale", False)),
                **quote,
            },
            "orderbook_top1": {
                "ask": {"price": asks[0].get("price"), "volume": asks[0].get("volume")}
                if asks and isinstance(asks[0], dict)
                else {},
                "bid": {"price": bids[0].get("price"), "volume": bids[0].get("volume")}
                if bids and isinstance(bids[0], dict)
                else {},
            },
            "latest_tick": {
                "time": latest_tick.get("time"),
                "dir": self._display_tick_dir(latest_tick) if latest_tick else None,
                "aggressor_quality": latest_tick.get("aggressor_quality"),
                "price": latest_tick.get("price"),
                "volume": latest_tick.get("volume"),
                "strength": latest_tick.get("strength", 0),
            },
            "runtime_context": self._build_entry_hot_runtime_context(
                matrix_runtime=matrix_runtime,
                entry_adm_runtime=entry_adm_runtime,
                lifecycle_ai_runtime=lifecycle_ai_runtime,
            ),
            "source_quality": {
                "tick_count": len(ticks),
                "candle_count": len(candles),
                "orderbook_present": bool(asks or bids),
                "price_change_heuristic_is_not_aggressor": True,
            },
        }
        return self._clean_hot_entry_payload(payload)

    def _format_entry_screen_hot_data(self, ws_data, recent_ticks, recent_candles, *, feature_packet=None, **runtime):
        payload = self._build_entry_screen_hot_payload(
            ws_data,
            recent_ticks,
            recent_candles,
            feature_packet=feature_packet,
            **runtime,
        )
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)

    def _format_market_data(self, ws_data, recent_ticks, recent_candles=None, *, feature_packet=None):
        if recent_candles is None:
            recent_candles = []

        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        raw_orderbook = ws_data.get('orderbook')
        orderbook = raw_orderbook if isinstance(raw_orderbook, dict) else {'asks': [], 'bids': []}
        asks = orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        bids = orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        if feature_packet is None:
            feature_packet = extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)

        if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False)):
            return json.dumps(
                self._build_entry_screen_v2_payload(
                    ws_data,
                    recent_ticks,
                    recent_candles,
                    feature_packet=feature_packet,
                ),
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )

        if bool(getattr(TRADING_RULES, "OPENAI_SCALPING_COMPACT_INPUT_ENABLED", True)):
            compact_asks = [
                {"price": a.get("price"), "volume": a.get("volume")}
                for a in asks[:3]
                if isinstance(a, dict)
            ]
            compact_bids = [
                {"price": b.get("price"), "volume": b.get("volume")}
                for b in bids[:3]
                if isinstance(b, dict)
            ]
            compact_ticks = [
                {
                    "time": t.get("time"),
                    "dir": self._display_tick_dir(t),
                    "aggressor_source": t.get("aggressor_source", t.get("dir_source", "-")),
                    "aggressor_quality": t.get("aggressor_quality", "-"),
                    "price": t.get("price"),
                    "volume": t.get("volume"),
                    "strength": t.get("strength", 0),
                }
                for t in (recent_ticks or [])[:5]
                if isinstance(t, dict)
            ]
            compact_candles = [
                {
                    "time": c.get("체결시간"),
                    "open": c.get("시가", c.get("현재가", 0)),
                    "high": c.get("고가"),
                    "low": c.get("저가"),
                    "close": c.get("현재가"),
                    "volume": c.get("거래량"),
                }
                for c in (recent_candles or [])[-5:]
            ]
            compact_payload = {
                "current": {
                    "price": curr_price,
                    "fluctuation_pct": fluctuation,
                    "websocket_strength": v_pw,
                    "distance_from_day_high_pct": feature_packet["distance_from_day_high_pct"],
                },
                "features": feature_packet,
                "quote_freshness": {
                    "latency_state": ws_data.get("latency_state"),
                    "quote_stale": bool(ws_data.get("quote_stale", False)),
                    **self._extract_quote_snapshot(ws_data),
                },
                "orderbook_top3": {"asks": compact_asks, "bids": compact_bids},
                "recent_ticks_latest_first": compact_ticks,
                "recent_candles_latest_window": compact_candles,
                "source_quality": {
                    "tick_count": len([tick for tick in (recent_ticks or []) if isinstance(tick, dict)]),
                    "candle_count": len([candle for candle in (recent_candles or []) if isinstance(candle, dict)]),
                    "orderbook_present": bool(compact_asks or compact_bids),
                    "tick_context_quality": feature_packet.get("tick_context_quality"),
                    "tick_context_stale": feature_packet.get("tick_context_stale"),
                    "tick_accel_source": feature_packet.get("tick_accel_source"),
                    "quote_age_ms": feature_packet.get("quote_age_ms"),
                    "quote_stale": feature_packet.get("quote_stale"),
                    "tick_latest_age_ms": feature_packet.get("tick_latest_age_ms"),
                    "tick_aggressor_pressure_usable": feature_packet.get("tick_aggressor_pressure_usable", False),
                    "tick_aggressor_trusted_count": feature_packet.get("tick_aggressor_trusted_count", 0),
                    "tick_aggressor_price_heuristic_count": feature_packet.get("tick_aggressor_price_heuristic_count", 0),
                    "micro_vwap_available": feature_packet.get("micro_vwap_available", False),
                    "ma5_available": feature_packet.get("ma5_available", False),
                    "minute_candle_window_fresh": feature_packet.get("minute_candle_window_fresh", False),
                    "minute_candle_context_quality": feature_packet.get("minute_candle_context_quality"),
                    "price_change_heuristic_is_not_aggressor": True,
                },
            }
            return json.dumps(compact_payload, ensure_ascii=False, separators=(",", ":"), default=str)

        imbalance_str = "데이터 없음"
        if ask_tot > 0 and bid_tot > 0:
            ratio = ask_tot / bid_tot
            if ratio >= 2.0:
                imbalance_str = f"매도벽 압도적 우위 ({ratio:.1f}배) - 돌파 시 급등 패턴"
            elif ratio <= 0.5:
                imbalance_str = f"매수벽 우위 ({1/ratio:.1f}배) - 하락 방어 또는 휩소(가짜) 패턴"
            else:
                imbalance_str = f"팽팽함 (매도 {ask_tot:,} vs 매수 {bid_tot:,})"

        high_price = curr_price
        if recent_candles:
            high_price = max(c.get('고가', curr_price) for c in recent_candles)

        drawdown_str = "0.0%"
        if high_price > 0:
            drawdown = ((curr_price - high_price) / high_price) * 100
            drawdown_str = f"{drawdown:.2f}% (당일 고가 {high_price:,}원)"

        ask_str = "\n".join([
            f"매도 {5-i}호가: {a['price']:,}원 ({a['volume']:,}주)"
            for i, a in enumerate(asks)
            if isinstance(a, dict) and "price" in a and "volume" in a
        ])
        bid_str = "\n".join([
            f"매수 {i+1}호가: {b['price']:,}원 ({b['volume']:,}주)"
            for i, b in enumerate(bids)
            if isinstance(b, dict) and "price" in b and "volume" in b
        ])

        tick_summary = "틱 데이터 부족"
        tick_str = ""

        if recent_ticks and len(recent_ticks) > 0:
            inferred_rows = [
                (t, infer_tick_aggressor_side(t))
                for t in recent_ticks
                if isinstance(t, dict)
            ]
            buy_vol = sum(
                self._safe_float(t.get('volume'), 0.0)
                for t, inferred in inferred_rows
                if inferred.get("side") == "BUY" and inferred.get("source") != "price_change_heuristic"
            )
            sell_vol = sum(
                self._safe_float(t.get('volume'), 0.0)
                for t, inferred in inferred_rows
                if inferred.get("side") == "SELL" and inferred.get("source") != "price_change_heuristic"
            )
            total_vol = buy_vol + sell_vol
            buy_pressure = (buy_vol / total_vol * 100) if total_vol > 0 else 50.0
            aggressor_source_counts = {}
            for _, inferred in inferred_rows:
                source = str(inferred.get("source") or "unknown")
                aggressor_source_counts[source] = aggressor_source_counts.get(source, 0) + 1

            latest_price = recent_ticks[0]['price']
            oldest_price = recent_ticks[-1]['price']
            trend_str = "상승 돌파 중 🚀" if latest_price > oldest_price else "하락 밀림 📉" if latest_price < oldest_price else "횡보 중 ➖"
            latest_strength = recent_ticks[0].get('strength', 0.0)

            time_diff_sec = 0
            try:
                from datetime import datetime
                t1_str = str(recent_ticks[-1]['time']).replace(':', '').zfill(6)
                t2_str = str(recent_ticks[0]['time']).replace(':', '').zfill(6)
                t1 = datetime.strptime(t1_str, "%H%M%S")
                t2 = datetime.strptime(t2_str, "%H%M%S")
                time_diff_sec = (t2 - t1).total_seconds()
                if time_diff_sec < 0:
                    time_diff_sec += 86400
            except:
                time_diff_sec = 999

            speed_str = f"🚀 매우 빠름 ({len(recent_ticks)}틱에 {time_diff_sec}초)" if time_diff_sec <= 2.0 else f"보통 ({time_diff_sec}초)" if time_diff_sec <= 10.0 else f"느림 ({time_diff_sec}초 - 소강상태)"

            tick_summary = (
                f"⏱️ [최근 {len(recent_ticks)}틱 정밀 브리핑]\n"
                f"- 단기 흐름: {trend_str}\n"
                f"- 틱 체결 속도(가속도): {speed_str}\n"
                f"- 🔥 매수 압도율(Buy Pressure): {buy_pressure:.1f}% (매수 {buy_vol:,}주 vs 매도 {sell_vol:,}주)\n"
                f"- aggressor source: {aggressor_source_counts}\n"
                f"- 현재 체결강도: {latest_strength}%"
            )

            tick_str = "\n".join([
                (
                    f"[{t['time']}] {self._display_tick_dir(t)} 체결"
                    f"({t.get('aggressor_source', t.get('dir_source', 'unknown'))}/"
                    f"{t.get('aggressor_quality', 'unknown')}): "
                    f"{t['price']:,}원 ({t['volume']:,}주) | 강도:{t.get('strength', 0)}%"
                )
                for t in recent_ticks[:10]
                if isinstance(t, dict)
            ])

        candle_str = ""
        if recent_candles:
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c.get('시가', c.get('현재가', 0)):,} 고가:{c['고가']:,} 저가:{c['저가']:,} 종가:{c['현재가']:,} 거래량:{c['거래량']:,}"
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

        volume_analysis = "비교 불가 (데이터 부족)"
        if recent_candles and len(recent_candles) >= 2:
            current_volume = recent_candles[-1]['거래량']
            prev_volumes = [c['거래량'] for c in recent_candles[:-1]]
            avg_prev_volume = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0

            if avg_prev_volume > 0:
                vol_ratio = (current_volume / avg_prev_volume) * 100
                if vol_ratio >= 200:
                    volume_analysis = f"🔥 폭증! (이전 평균 대비 {vol_ratio:.0f}% 수준 / 현재 {current_volume:,}주)"
                elif vol_ratio >= 100:
                    volume_analysis = f"상승 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"
                else:
                    volume_analysis = f"감소 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"

        indicators_str = "지표 계산 불가"
        if recent_candles and len(recent_candles) >= 5:
            ind = calculate_scalping_micro_indicator_values(recent_candles)

            ma5_status = "상회" if curr_price > ind['MA5'] else "하회"
            vwap_status = "상회 (수급강세)" if curr_price > ind['Micro_VWAP'] else "하회 (수급약세)"

            indicators_str = (
                f"- 단기 5-MA: {ind['MA5']:,}원 (현재가 {ma5_status})\n"
                f"- Micro-VWAP: {ind['Micro_VWAP']:,}원 (현재가 {vwap_status})\n"
                f"- 고점 대비 이격도: {drawdown_str}\n"
                f"- 호가 불균형: {imbalance_str}"
            )

        quant_features_str = (
            f"- packet_version: {feature_packet['packet_version']}\n"
            f"- curr_price: {feature_packet['curr_price']}\n"
            f"- latest_strength: {feature_packet['latest_strength']}%\n"
            f"- spread_krw: {feature_packet['spread_krw']}\n"
            f"- spread_bp: {feature_packet['spread_bp']}\n"
            f"- top1_depth_ratio: {feature_packet['top1_depth_ratio']}\n"
            f"- top3_depth_ratio: {feature_packet['top3_depth_ratio']}\n"
            f"- orderbook_total_ratio: {feature_packet['orderbook_total_ratio']}\n"
            f"- micro_price: {feature_packet['micro_price']}\n"
            f"- microprice_edge_bp: {feature_packet['microprice_edge_bp']}\n"
            f"- buy_pressure_10t: {feature_packet['buy_pressure_10t']}%\n"
            f"- tick_aggressor_pressure_usable: {str(feature_packet.get('tick_aggressor_pressure_usable', False)).lower()}\n"
            f"- tick_aggressor_trusted_count: {feature_packet.get('tick_aggressor_trusted_count', 0)}\n"
            f"- tick_aggressor_price_heuristic_count: {feature_packet.get('tick_aggressor_price_heuristic_count', 0)}\n"
            f"- price_change_10t_pct: {feature_packet['price_change_10t_pct']}%\n"
            f"- recent_5tick_seconds: {feature_packet['recent_5tick_seconds']}\n"
            f"- prev_5tick_seconds: {feature_packet['prev_5tick_seconds']}\n"
            f"- distance_from_day_high_pct: {feature_packet['distance_from_day_high_pct']}%\n"
            f"- intraday_range_pct: {feature_packet['intraday_range_pct']}%\n"
            f"- tick_acceleration_ratio: {feature_packet['tick_acceleration_ratio']}\n"
            f"- tick_accel_source: {feature_packet.get('tick_accel_source', '-')}\n"
            f"- tick_context_quality: {feature_packet.get('tick_context_quality', 'unknown')}\n"
            f"- tick_context_stale: {feature_packet.get('tick_context_stale', 'not_available_tick_latest_age')}\n"
            f"- same_price_buy_absorption: {feature_packet['same_price_buy_absorption']}\n"
            f"- large_sell_print_detected: {str(feature_packet['large_sell_print_detected']).lower()}\n"
            f"- large_buy_print_detected: {str(feature_packet['large_buy_print_detected']).lower()}\n"
            f"- net_aggressive_delta_10t: {feature_packet['net_aggressive_delta_10t']}\n"
            f"- volume_ratio_pct: {feature_packet['volume_ratio_pct']}%\n"
            f"- curr_vs_micro_vwap_bp: {feature_packet['curr_vs_micro_vwap_bp']}\n"
            f"- micro_vwap_available: {str(feature_packet.get('micro_vwap_available', False)).lower()}\n"
            f"- minute_candle_window_fresh: {str(feature_packet.get('minute_candle_window_fresh', False)).lower()}\n"
            f"- minute_candle_context_quality: {feature_packet.get('minute_candle_context_quality', 'unknown')}\n"
            f"- curr_vs_ma5_bp: {feature_packet['curr_vs_ma5_bp']}\n"
            f"- ma5_available: {str(feature_packet.get('ma5_available', False)).lower()}\n"
            f"- micro_vwap_value: {feature_packet['micro_vwap_value']}\n"
            f"- ma5_value: {feature_packet['ma5_value']}\n"
            f"- ask_depth_ratio: {feature_packet['ask_depth_ratio']}\n"
            f"- net_ask_depth: {feature_packet['net_ask_depth']}"
        )

        user_input = f"""
[현재 상태]
- 현재가: {curr_price:,}원
- 전일대비 등락률: {fluctuation}%
- 웹소켓 체결강도: {v_pw}%

[정량형 수급 피처]
{quant_features_str}

[초단타 수급/위치 지표]
{indicators_str}

[거래량 분석]
- {volume_analysis}

{tick_summary}

[최근 1분봉 흐름 (과거 -> 최신순)]
{candle_str}

[실시간 호가창]
{ask_str}
-------------------------
{bid_str}

[최근 10틱 상세 내역 (최신순)]
{tick_str}
"""
        return user_input

    def _extract_scalping_features(self, ws_data, recent_ticks, recent_candles=None):
        return extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)

    def _format_swing_market_data(self, ws_data, recent_candles, program_net_qty=0):
        curr_price = ws_data.get('curr', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        v_pw = ws_data.get('v_pw', 0)
        today_vol = ws_data.get('volume', 0)

        candle_str = "minute candle data unavailable"
        ma5, ma20 = 0, 0
        if recent_candles and len(recent_candles) >= 20:
            closes = [c['현재가'] for c in recent_candles]
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20

            trend = "bullish_alignment" if ma5 > ma20 else "bearish_alignment"
            position = "above_ma5" if curr_price > ma5 else "below_ma5"

            candle_str = (
                f"- short_term_trend: {trend}\n"
                f"- ma5: {ma5:,.0f} / ma20: {ma20:,.0f}\n"
                f"- price_position: {position}\n"
                f"- recent_5_candle_closes: " + " -> ".join([f"{c['현재가']:,}" for c in recent_candles[-5:]])
            )

        prog_sign = "net_buy" if program_net_qty > 0 else "net_sell"

        user_input = f"""
[CURRENT_STATE_SWING_VIEW]
- current_price: {curr_price:,} (change_pct {fluctuation:+.2f}%)
- intraday_cumulative_volume: {today_vol:,}
- execution_strength: {v_pw}%

[MAJOR_FLOW]
- program_flow: {prog_sign} ({program_net_qty:,})

[CHART_POSITION]
{candle_str}
"""
        return user_input

    def _infer_realtime_mode(self, realtime_ctx):
        strat_label = str(realtime_ctx.get("strat_label", "")).upper()
        position_status = str(realtime_ctx.get("position_status", "NONE")).upper()
        fluctuation = float(realtime_ctx.get("fluctuation", 0.0) or 0.0)
        vol_ratio = float(realtime_ctx.get("vol_ratio", 0.0) or 0.0)
        v_pw_now = float(realtime_ctx.get("v_pw_now", 0.0) or 0.0)
        v_pw_3m = float(realtime_ctx.get("v_pw_3m", 0.0) or 0.0)
        prog_delta_qty = int(realtime_ctx.get("prog_delta_qty", 0) or 0)
        curr_price = int(realtime_ctx.get("curr_price", 0) or 0)
        vwap_price = int(realtime_ctx.get("vwap_price", 0) or 0)
        high_breakout_status = str(realtime_ctx.get("high_breakout_status", ""))
        daily_setup_desc = str(realtime_ctx.get("daily_setup_desc", ""))
        session_stage = str(realtime_ctx.get("session_stage", "REGULAR")).upper()
        captured_at = str(realtime_ctx.get("captured_at", ""))

        if strat_label in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "MIDTERM", "POSITION"}:
            return "SWING"

        scalp_score = 0
        swing_score = 0

        if position_status == "HOLDING":
            swing_score += 2

        hhmm = ""
        if captured_at and len(captured_at) >= 16:
            hhmm = captured_at[11:16].replace(":", "")
        if not hhmm:
            hhmm = time.strftime("%H%M")

        if session_stage in {"PREOPEN", "OPENING"} or "0900" <= hhmm <= "1030":
            scalp_score += 2
        elif "1300" <= hhmm <= "1500":
            swing_score += 1

        if abs(fluctuation) >= 3.0:
            scalp_score += 1
        if vol_ratio >= 150:
            scalp_score += 2
        elif 70 <= vol_ratio <= 130:
            swing_score += 1

        if v_pw_now >= 120 and (v_pw_now - v_pw_3m) >= 10:
            scalp_score += 2

        if prog_delta_qty > 0:
            scalp_score += 1
            swing_score += 1

        if curr_price > 0 and vwap_price > 0 and curr_price >= vwap_price:
            scalp_score += 1
        if "돌파" in high_breakout_status:
            scalp_score += 1

        if any(k in daily_setup_desc for k in ["정배열", "눌림", "전고점", "추세", "돌파"]):
            swing_score += 2
        if any(k in daily_setup_desc for k in ["급등후", "과열", "이격", "장대음봉"]):
            swing_score -= 1

        if abs(scalp_score - swing_score) <= 1:
            return "DUAL"
        return "SCALP" if scalp_score > swing_score else "SWING"

    def _get_realtime_prompt(self, selected_mode):
        if selected_mode == "SCALP":
            return REALTIME_ANALYSIS_PROMPT_SCALP
        if selected_mode == "SWING":
            return REALTIME_ANALYSIS_PROMPT_SWING
        return REALTIME_ANALYSIS_PROMPT_DUAL

    def _build_realtime_quant_packet(self, stock_name, stock_code, realtime_ctx, selected_mode):
        def i(key, default=0):
            try:
                return int(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        def f(key, default=0.0):
            try:
                return float(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        curr_price = i("curr_price")
        vwap_price = i("vwap_price")
        ask_tot = i("ask_tot")
        bid_tot = i("bid_tot")
        orderbook_imbalance = f("orderbook_imbalance")
        best_ask = i("best_ask")
        best_bid = i("best_bid")
        tick_trade_value = i("tick_trade_value")
        cum_trade_value = i("cum_trade_value")
        buy_exec_volume = i("buy_exec_volume")
        sell_exec_volume = i("sell_exec_volume")
        net_buy_exec_volume = i("net_buy_exec_volume")
        buy_exec_single = i("buy_exec_single")
        sell_exec_single = i("sell_exec_single")
        prog_buy_qty = i("prog_buy_qty")
        prog_sell_qty = i("prog_sell_qty")
        prog_buy_amt = i("prog_buy_amt")
        prog_sell_amt = i("prog_sell_amt")

        common_block = f"""[기본]
- 종목명: {stock_name}
- 종목코드: {stock_code}
- 시가총액: {i('market_cap'):,}원
- 분석모드: {selected_mode}
- 감시전략: {realtime_ctx.get('strat_label', 'AUTO')}
- 보유상태: {realtime_ctx.get('position_status', 'NONE')}
- 평균단가: {i('avg_price'):,}원
- 현재손익률: {f('pnl_pct'):+.2f}%
- 현재가격: {curr_price:,}원 (전일비 {f('fluctuation'):+.2f}%)
- 기계목표가: {i('target_price'):,}원 (사유: {realtime_ctx.get('target_reason', '')})
- 익절/손절: {f('trailing_pct'):.2f}% / {f('stop_pct'):.2f}%
- 퀀트 점수: 추세 {f('trend_score'):.1f} / 수급 {f('flow_score'):.1f} / 호가 {f('orderbook_score'):.1f} / 타점 {f('timing_score'):.1f} / 종합 {f('score'):.1f}
- 퀀트 엔진 결론: {realtime_ctx.get('conclusion', '')}

[수급/체결]
- 누적거래량: {i('today_vol'):,}주 (20일 평균대비 {f('vol_ratio'):.1f}%)
- 거래대금: {i('today_turnover'):,}원
- 체결강도 현재/1분/3분/5분: {f('v_pw_now'):.1f} / {f('v_pw_1m'):.1f} / {f('v_pw_3m'):.1f} / {f('v_pw_5m'):.1f}
- 매수세 현재/1분/3분: {f('buy_ratio_now'):.1f}% / {f('buy_ratio_1m'):.1f}% / {f('buy_ratio_3m'):.1f}%
- 프로그램 순매수 현재/증감: {i('prog_net_qty'):+,}주 / {i('prog_delta_qty'):+,}주
- 프로그램 절대 매수/매도: {prog_buy_qty:+,}주 / {prog_sell_qty:+,}주 | {prog_buy_amt:+,} / {prog_sell_amt:+,}
- 외인/기관 당일 가집계: 외인 {i('foreign_net'):+,}주 / 기관 {i('inst_net'):+,}주
- 외인+기관 합산: {i('smart_money_net'):+,}주
- 순간 체결대금/누적: {tick_trade_value:,} / {cum_trade_value:,}
- 매수/매도 체결량: {buy_exec_volume:+,} / {sell_exec_volume:+,} (순매수 {net_buy_exec_volume:+,})
- 체결 매수비율(WS): {f('buy_ratio_ws'):.1f}% / 체결량 기준 {f('exec_buy_ratio'):.1f}%
- 단건 체결: 매수 {buy_exec_single:+,} / 매도 {sell_exec_single:+,}
- 수급 요약: {realtime_ctx.get('micro_flow_desc', '')} / {realtime_ctx.get('program_flow_desc', '')}

[호가/구조]
- 최우선 매도/매수호가: {best_ask:,} / {best_bid:,}
- 매도잔량/매수잔량: {ask_tot:,} / {bid_tot:,}
- 호가 불균형비: {orderbook_imbalance:.2f}
- 스프레드: {i('spread_tick')}틱
- 체결 편향: {realtime_ctx.get('tape_bias', '중립')}
- 매도벽 소화 여부: {realtime_ctx.get('ask_absorption_status', '')}
- 잔량 개선: 매수 {i('net_bid_depth'):+,} ({f('bid_depth_ratio'):.1f}%) / 매도 {i('net_ask_depth'):+,} ({f('ask_depth_ratio'):.1f}%)
- 잔량 요약: {realtime_ctx.get('depth_flow_desc', '')}
- VWAP: {vwap_price:,}원 ({realtime_ctx.get('vwap_status', '정보없음')})
- 시가 위치: {realtime_ctx.get('open_position_desc', '')}
- 고가 돌파 여부: {realtime_ctx.get('high_breakout_status', '')}
- 최근 5분 박스 상단/하단: {i('box_high'):,} / {i('box_low'):,}
"""

        scalp_block = f"""
[스캘핑 관점]
- 체결강도 가속도: {f('v_pw_now') - f('v_pw_3m'):+.1f}
- 체결 signed 수량: {i('trade_qty_signed_now'):+,}주
- 프로그램 delta: {i('prog_delta_qty'):+,}주
- 눌림/돌파 즉시성 체크: VWAP / 고가 / 스프레드 / 테이프 편향
"""

        swing_block = f"""
[스윙 관점]
- 일봉 구조: {realtime_ctx.get('daily_setup_desc', '')}
- 5/20/60일선 상태: {realtime_ctx.get('ma5_status', '')}, {realtime_ctx.get('ma20_status', '')}, {realtime_ctx.get('ma60_status', '')}
- 전일 고점/저점: {i('prev_high'):,} / {i('prev_low'):,}
- 최근 20일 신고가 근접도: {f('near_20d_high_pct'):.2f}%
- 고가 대비 눌림폭: {f('drawdown_from_high_pct'):.2f}%
"""

        if selected_mode == "SCALP":
            return common_block + scalp_block
        if selected_mode == "SWING":
            return common_block + swing_block
        return common_block + scalp_block + swing_block

    # ==========================================
    # 게이트키퍼 캐시
    # ==========================================

    def _compact_gatekeeper_ctx_for_cache(self, realtime_ctx):
        ctx = realtime_ctx or {}
        curr_price = ctx.get("curr_price", 0)
        target_price = ctx.get("target_price", 0)
        vwap_price = ctx.get("vwap_price", 0)
        prev_high = ctx.get("prev_high", 0)
        price_bucket = self._price_bucket_step_for_cache(curr_price)
        return {
            "strat_label": str(ctx.get("strat_label", "") or ""),
            "position_status": str(ctx.get("position_status", "") or ""),
            "curr_price": self._bucket_int_for_cache(curr_price, price_bucket),
            "target_price": self._bucket_int_for_cache(target_price, price_bucket),
            "vwap_price": self._bucket_int_for_cache(vwap_price, price_bucket),
            "prev_high": self._bucket_int_for_cache(prev_high, price_bucket),
            "market_cap": self._bucket_int_for_cache(ctx.get("market_cap", 0), 50_000_000_000),
            "fluctuation": self._bucket_float_for_cache(ctx.get("fluctuation", 0.0), 0.3),
            "score": self._bucket_float_for_cache(ctx.get("score", 0.0), 10.0),
            "v_pw_now": self._bucket_float_for_cache(ctx.get("v_pw_now", 0.0), 5.0),
            "buy_ratio_ws": self._bucket_float_for_cache(ctx.get("buy_ratio_ws", 0.0), 4.0),
            "exec_buy_ratio": self._bucket_float_for_cache(ctx.get("exec_buy_ratio", 0.0), 8.0),
            "prog_net_qty": self._bucket_int_for_cache(ctx.get("prog_net_qty", 0), 10_000),
            "prog_delta_qty": self._bucket_int_for_cache(ctx.get("prog_delta_qty", 0), 2_000),
            "tick_trade_value": self._bucket_int_for_cache(ctx.get("tick_trade_value", 0), 25_000),
            "net_buy_exec_volume": self._bucket_int_for_cache(ctx.get("net_buy_exec_volume", 0), 500),
            "net_bid_depth": self._bucket_int_for_cache(ctx.get("net_bid_depth", 0), 10_000),
            "net_ask_depth": self._bucket_int_for_cache(ctx.get("net_ask_depth", 0), 10_000),
            "spread_tick": self._bucket_int_for_cache(ctx.get("spread_tick", 0), 1),
            "vol_ratio": self._bucket_float_for_cache(ctx.get("vol_ratio", 0.0), 25.0),
            "today_vol": self._bucket_int_for_cache(ctx.get("today_vol", 0), 100_000),
        }

    def _build_gatekeeper_cache_key(self, stock_name, stock_code, realtime_ctx, analysis_mode):
        return self._build_cache_digest({
            "stock_name": stock_name,
            "stock_code": stock_code,
            "analysis_mode": analysis_mode,
            "realtime_ctx": self._compact_gatekeeper_ctx_for_cache(realtime_ctx),
        })

    def _prepare_realtime_report_request(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        selected_mode = (analysis_mode or "AUTO").upper()
        realtime_ctx = input_data_text if isinstance(input_data_text, dict) else None

        if realtime_ctx is not None:
            if selected_mode == "AUTO":
                selected_mode = self._infer_realtime_mode(realtime_ctx)
            prompt = self._get_realtime_prompt(selected_mode)
            packet_text = self._build_realtime_quant_packet(stock_name, stock_code, realtime_ctx, selected_mode)
            user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 전술 패킷]
{packet_text}"""
            context_name = f"실시간 분석({selected_mode})"
        else:
            if selected_mode == "AUTO":
                selected_mode = "DUAL"
            prompt = self._get_realtime_prompt(selected_mode)
            user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 분석 입력]
{str(input_data_text)}"""
            context_name = f"실시간 분석(LEGACY:{selected_mode})"

        return {
            "selected_mode": selected_mode,
            "prompt": prompt,
            "user_input": user_input,
            "context_name": context_name,
        }

    def _generate_realtime_report_payload(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        total_started_at = time.perf_counter()
        lock_started_at = time.perf_counter()
        with self.lock:
            lock_wait_ms = int((time.perf_counter() - lock_started_at) * 1000)

            build_started_at = time.perf_counter()
            request = self._prepare_realtime_report_request(
                stock_name=stock_name,
                stock_code=stock_code,
                input_data_text=input_data_text,
                analysis_mode=analysis_mode,
            )
            packet_build_ms = int((time.perf_counter() - build_started_at) * 1000)

            model_started_at = time.perf_counter()
            report_error = ""
            try:
                report = self._call_openai_safe(
                    request["prompt"],
                    request["user_input"],
                    require_json=False,
                    context_name=request["context_name"],
                    model_override=self._get_tier2_model(),
                    endpoint_name="realtime_report",
                    symbol=stock_code,
                )
            except Exception as e:
                report_error = str(e)
                log_error(f"🚨 [{request['context_name']}] OpenAI 에러: {e}")
                report = f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
            model_call_ms = int((time.perf_counter() - model_started_at) * 1000)

        total_ms = int((time.perf_counter() - total_started_at) * 1000)
        return {
            "report": report,
            "selected_mode": request["selected_mode"],
            "context_name": request["context_name"],
            "lock_wait_ms": lock_wait_ms,
            "packet_build_ms": packet_build_ms,
            "model_call_ms": model_call_ms,
            "total_ms": total_ms,
            "error": report_error,
        }

    # ==========================================
    # 퍼블릭 메서드: analyze_target (핵심 실시간 분석)
    # ==========================================

    def _build_scalping_entry_price_raw_input(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        price_ctx,
    ):
        return json.dumps(
            {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "ws_data": ws_data or {},
                "recent_ticks": (recent_ticks or [])[:20],
                "recent_candles": (recent_candles or [])[:20],
                "price_context": price_ctx or {},
            },
            ensure_ascii=True,
            default=str,
        )

    def _compact_entry_price_orderbook(self, ws_data, *, limit=10):
        orderbook = (ws_data or {}).get("orderbook") if isinstance(ws_data, dict) else {}
        if not isinstance(orderbook, dict):
            orderbook = {}
        return {
            "asks": [
                {"price": item.get("price"), "volume": item.get("volume")}
                for item in (orderbook.get("asks") or [])[:limit]
                if isinstance(item, dict)
            ],
            "bids": [
                {"price": item.get("price"), "volume": item.get("volume")}
                for item in (orderbook.get("bids") or [])[:limit]
                if isinstance(item, dict)
            ],
        }

    def _compact_entry_price_ws_data(self, ws_data):
        ws = ws_data if isinstance(ws_data, dict) else {}
        return {
            "curr": ws.get("curr"),
            "current_price": ws.get("current_price"),
            "v_pw": ws.get("v_pw"),
            "buy_ratio": ws.get("buy_ratio"),
            "fluctuation": ws.get("fluctuation"),
            "ask_tot": ws.get("ask_tot"),
            "bid_tot": ws.get("bid_tot"),
            "net_ask_depth": ws.get("net_ask_depth"),
            "ask_depth_ratio": ws.get("ask_depth_ratio"),
            "orderbook": self._compact_entry_price_orderbook(ws, limit=10),
        }

    def _compact_entry_price_ticks(self, recent_ticks):
        return [
            {
                "time": tick.get("time"),
                "price": tick.get("price"),
                "volume": tick.get("volume"),
                "dir": tick.get("dir", tick.get("side", "NEUTRAL")),
                "strength": tick.get("strength", 0),
            }
            for tick in (recent_ticks or [])[:20]
            if isinstance(tick, dict)
        ]

    def _compact_entry_price_candles(self, recent_candles):
        return [
            {
                "체결시간": candle.get("체결시간", candle.get("time")),
                "시가": candle.get("시가", candle.get("open", candle.get("현재가", candle.get("close", 0)))),
                "현재가": candle.get("현재가", candle.get("close")),
                "고가": candle.get("고가", candle.get("high")),
                "저가": candle.get("저가", candle.get("low")),
                "거래량": candle.get("거래량", candle.get("volume")),
            }
            for candle in (recent_candles or [])[:20]
            if isinstance(candle, dict)
        ]

    def _compact_entry_price_context(self, price_ctx):
        ctx = price_ctx if isinstance(price_ctx, dict) else {}
        micro = ctx.get("orderbook_micro") if isinstance(ctx.get("orderbook_micro"), dict) else {}
        spread = 0
        best_ask = int(self._safe_float(ctx.get("best_ask"), 0))
        best_bid = int(self._safe_float(ctx.get("best_bid"), 0))
        if best_ask > 0 and best_bid > 0:
            spread = best_ask - best_bid
        spread_bp = micro.get("spread_bp")
        if spread_bp is None and spread > 0 and best_bid > 0:
            spread_bp = round((spread / best_bid) * 10000.0, 3)
        return {
            "strategy": ctx.get("strategy"),
            "position_tag": ctx.get("position_tag"),
            "current_price": ctx.get("current_price"),
            "best_bid": ctx.get("best_bid"),
            "best_ask": ctx.get("best_ask"),
            "spread": spread,
            "reference_target_price": ctx.get("reference_target_price"),
            "defensive_order_price": ctx.get("defensive_order_price"),
            "normal_defensive_order_price": ctx.get("normal_defensive_order_price"),
            "resolved_order_price": ctx.get("resolved_order_price"),
            "latency_guard": {
                "latency_state": ctx.get("latency_state"),
                "ws_age_ms": ctx.get("ws_age_ms"),
                "ws_jitter_ms": ctx.get("ws_jitter_ms"),
                "spread_ratio": ctx.get("spread_ratio"),
                "quote_stale": ctx.get("quote_stale"),
            },
            "entry_price_guard": {
                "resolution_reason": ctx.get("resolution_reason"),
                "price_below_bid_bps": ctx.get("price_below_bid_bps"),
                "reference_target_below_bid_bps": ctx.get("reference_target_below_bid_bps"),
                "signal_score": ctx.get("signal_score"),
            },
            "orderbook_micro": {
                "ready": micro.get("ready"),
                "reason": micro.get("reason"),
                "micro_state": micro.get("micro_state"),
                "qi": micro.get("qi"),
                "ofi": micro.get("ofi_norm", micro.get("ofi")),
                "ofi_z": micro.get("ofi_z"),
                "top_depth_ratio": micro.get("top_depth_ratio", micro.get("depth_ewma")),
                "spread_bp": spread_bp,
                "spread_ticks": micro.get("spread_ticks"),
                "sample_quote_count": micro.get("sample_quote_count"),
                "ofi_threshold_source": micro.get("ofi_threshold_source"),
                "ofi_threshold_bucket_key": micro.get("ofi_threshold_bucket_key", micro.get("ofi_bucket_key")),
                "ofi_calibration_warning": micro.get("ofi_calibration_warning"),
            },
        }

    def _compact_entry_context_features(self, ws_data, recent_ticks, recent_candles, price_ctx=None):
        keys = (
            "entry_liquidity_score",
            "entry_liquidity_status",
            "fillability_score",
            "would_fill_now",
            "quote_depth_present",
            "quote_fresh_for_entry",
            "order_flow_pressure_score",
            "entry_order_flow_status",
            "order_flow_pressure_source",
            "entry_momentum_score",
            "entry_momentum_status",
            "entry_context_quality",
            "entry_context_missing_features",
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "micro_vwap_available",
            "minute_candle_window_fresh",
            "quote_age_ms",
            "quote_stale",
            "top3_depth_ratio",
            "spread_bp",
        )
        ws = ws_data if isinstance(ws_data, dict) else {}
        ctx = price_ctx if isinstance(price_ctx, dict) else {}
        nested_ctx = ctx.get("entry_context_features") if isinstance(ctx.get("entry_context_features"), dict) else {}
        try:
            packet = extract_scalping_feature_packet(ws, recent_ticks or [], recent_candles or [])
        except Exception:
            packet = {}
        summary = {}
        for key in keys:
            for source in (nested_ctx, packet, ctx, ws):
                if isinstance(source, dict) and key in source:
                    value = source.get(key)
                    if value is not None and str(value).strip() not in {"", "-", "None", "none", "null"}:
                        summary[key] = value
                        break
        summary.update(
            {
                "context_role": "pre_submit_entry_quality_context",
                "runtime_authority": "advisory_input_only",
                "forbidden_use": "standalone_buy_submit_or_guard_bypass",
            }
        )
        if not any(key in summary for key in keys):
            summary["status"] = "not_available"
        return summary

    def _compact_entry_time_context(self, position_ctx):
        ctx = position_ctx if isinstance(position_ctx, dict) else {}
        raw = ctx.get("entry_time_context") if isinstance(ctx.get("entry_time_context"), dict) else {}
        keys = (
            "entry_liquidity_score",
            "entry_liquidity_status",
            "fillability_score",
            "would_fill_now",
            "quote_depth_present",
            "quote_fresh_for_entry",
            "order_flow_pressure_score",
            "entry_order_flow_status",
            "order_flow_pressure_source",
            "entry_momentum_score",
            "entry_momentum_status",
            "entry_context_quality",
            "entry_context_missing_features",
            "ai_input_source_quality_status",
            "ai_input_source_quality_reason",
            "tick_context_quality",
            "tick_context_stale",
            "quote_age_ms",
            "quote_stale",
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "micro_vwap_available",
            "minute_candle_window_fresh",
            "top3_depth_ratio",
            "spread_bp",
        )
        summary = {}
        for key in keys:
            for source in (raw, ctx):
                if isinstance(source, dict) and key in source:
                    value = source.get(key)
                    if value is not None and str(value).strip() not in {"", "-", "None", "none", "null"}:
                        summary[key] = value
                        break
        for key in ("observed_at", "age_sec", "source"):
            if key in raw:
                summary[key] = raw.get(key)
        summary.update(
            {
                "context_role": "entry_time_provenance_only",
                "current_flow_evidence": False,
                "runtime_authority": "explain_bad_entry_vs_live_deterioration_only",
            }
        )
        if not any(key in summary for key in keys):
            summary["status"] = "not_available"
        return summary

    def _price_bps_from_bid(self, price, best_bid):
        price_value = self._safe_float(price, 0.0)
        bid_value = self._safe_float(best_bid, 0.0)
        if price_value <= 0 or bid_value <= 0:
            return 0.0
        return round(((price_value - bid_value) / bid_value) * 10000.0, 3)

    def _build_scalping_entry_price_v2_input(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        price_ctx,
    ):
        ctx = price_ctx if isinstance(price_ctx, dict) else {}
        start_quote = {
            "current_price": ctx.get("current_price"),
            "best_bid": ctx.get("best_bid"),
            "best_ask": ctx.get("best_ask"),
        }
        start_best_bid = int(self._safe_float(ctx.get("best_bid"), 0))
        start_best_ask = int(self._safe_float(ctx.get("best_ask"), 0))
        start_spread = start_best_ask - start_best_bid if start_best_ask > 0 and start_best_bid > 0 else 0
        start_quote["spread"] = start_spread
        current_quote = self._extract_quote_snapshot(ws_data)
        micro = ctx.get("orderbook_micro") if isinstance(ctx.get("orderbook_micro"), dict) else {}
        current_micro = (ws_data or {}).get("orderbook_micro") if isinstance((ws_data or {}).get("orderbook_micro"), dict) else {}
        current_micro_state = current_micro.get("micro_state", micro.get("micro_state"))
        tick_size = max(1, int(self._safe_float(ctx.get("tick_size"), 1) or 1))
        best_bid_delta = int(current_quote.get("best_bid") or 0) - start_best_bid if start_best_bid > 0 else 0
        best_ask_delta = int(current_quote.get("best_ask") or 0) - start_best_ask if start_best_ask > 0 else 0
        spread_delta = int(current_quote.get("spread") or 0) - start_spread
        defensive_price = ctx.get("defensive_order_price")
        reference_price = ctx.get("reference_target_price")
        resolved_price = ctx.get("resolved_order_price")
        compact_ctx = self._compact_entry_price_context(ctx)
        payload = {
            "input_schema": "entry_price_v2",
            "stock_name": stock_name,
            "stock_code": stock_code,
            "ws_data": self._compact_entry_price_ws_data(ws_data),
            "quote_change": {
                "decision_start_quote": start_quote,
                "current_quote": current_quote,
                "best_bid_delta_ticks": round(best_bid_delta / tick_size, 3),
                "best_ask_delta_ticks": round(best_ask_delta / tick_size, 3),
                "spread_delta_ticks": round(spread_delta / tick_size, 3),
                "micro_state_start": micro.get("micro_state"),
                "micro_state_current": current_micro_state,
                "micro_state_changed": bool(current_micro_state and current_micro_state != micro.get("micro_state")),
            },
            "candidate_prices": {
                "defensive_order_price": defensive_price,
                "reference_target_price": reference_price,
                "resolved_order_price": resolved_price,
                "defensive_vs_bid_bps": self._price_bps_from_bid(defensive_price, start_best_bid),
                "reference_vs_bid_bps": self._price_bps_from_bid(reference_price, start_best_bid),
                "resolved_vs_bid_bps": self._price_bps_from_bid(resolved_price, start_best_bid),
            },
            "freshness": {
                "latency_state": ctx.get("latency_state"),
                "ws_age_ms": ctx.get("ws_age_ms"),
                "ws_jitter_ms": ctx.get("ws_jitter_ms"),
                "quote_stale": bool(ctx.get("quote_stale")),
            },
            "fill_probability_hints": {
                "execution_strength": (ws_data or {}).get("v_pw"),
                "buy_ratio": (ws_data or {}).get("buy_ratio"),
                "spread_bp": compact_ctx["orderbook_micro"].get("spread_bp") or current_quote.get("spread_bp"),
                "top_depth_ratio": compact_ctx["orderbook_micro"].get("top_depth_ratio"),
                "micro_state": micro.get("micro_state"),
                "ofi": compact_ctx["orderbook_micro"].get("ofi"),
                "qi": compact_ctx["orderbook_micro"].get("qi"),
            },
            "entry_context_features": self._compact_entry_context_features(
                ws_data,
                recent_ticks,
                recent_candles,
                price_ctx=ctx,
            ),
            "price_context": compact_ctx,
            "tick_summary": self._summarize_tick_windows(recent_ticks, windows=(5, 10, 20)),
            "candle_summary": self._summarize_candle_windows(recent_candles, windows=(3, 5, 10)),
            "recent_ticks_latest_first": self._compact_recent_ticks(recent_ticks, limit=5),
            "recent_candles_latest_window": self._compact_recent_candles(recent_candles, limit=5),
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)

    def _build_scalping_entry_price_user_input(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        price_ctx,
    ):
        payload = {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "ws_data": self._compact_entry_price_ws_data(ws_data),
            "recent_ticks": self._compact_entry_price_ticks(recent_ticks),
            "recent_candles": self._compact_entry_price_candles(recent_candles),
            "price_context": self._compact_entry_price_context(price_ctx),
            "entry_context_features": self._compact_entry_context_features(
                ws_data,
                recent_ticks,
                recent_candles,
                price_ctx=price_ctx,
            ),
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)

    def _build_scalping_entry_price_runtime_input(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        price_ctx,
    ):
        if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED", True)):
            if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_V2_INPUT_ENABLED", False)):
                return self._build_scalping_entry_price_v2_input(
                    stock_name=stock_name,
                    stock_code=stock_code,
                    ws_data=ws_data,
                    recent_ticks=recent_ticks,
                    recent_candles=recent_candles,
                    price_ctx=price_ctx,
                )
            return self._build_scalping_entry_price_user_input(
                stock_name=stock_name,
                stock_code=stock_code,
                ws_data=ws_data,
                recent_ticks=recent_ticks,
                recent_candles=recent_candles,
                price_ctx=price_ctx,
            )
        return self._build_scalping_entry_price_raw_input(
            stock_name=stock_name,
            stock_code=stock_code,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            price_ctx=price_ctx,
        )

    def evaluate_scalping_entry_price(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        price_ctx,
        metadata_extra=None,
    ):
        started = time.perf_counter()
        fallback_price = int((price_ctx or {}).get("resolved_order_price", 0) or 0)
        input_contract_fields = {
            "ai_input_schema": (
                "entry_price_v2"
                if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_V2_INPUT_ENABLED", False))
                else "entry_price_compact_v1"
                if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED", True))
                else "entry_price_raw_v1"
            ),
            "ai_input_contract_mode": (
                "structured_json"
                if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED", True))
                else "plain_text"
            ),
            "ai_input_build_fallback": "not_built",
        }
        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                normalize_scalping_entry_price_result(
                    {
                        "action": "USE_DEFENSIVE",
                        "order_price": fallback_price,
                        "confidence": 0,
                        "reason": "ai_lock_contention_use_defensive_fallback",
                        "max_wait_sec": 90,
                    },
                    fallback_price=fallback_price,
                ),
                prompt_type="entry_price",
                prompt_version="entry_price_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="lock_contention",
                input_contract_fields=input_contract_fields,
            )

        try:
            if self.ai_disabled:
                return self._annotate_analysis_result(
                    normalize_scalping_entry_price_result(
                        {
                            "action": "USE_DEFENSIVE",
                            "order_price": fallback_price,
                            "confidence": 0,
                            "reason": "engine_disabled_use_defensive_fallback",
                            "max_wait_sec": 90,
                        },
                        fallback_price=fallback_price,
                    ),
                    prompt_type="entry_price",
                    prompt_version="entry_price_v1",
                    response_ms=int((time.perf_counter() - started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=False,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="engine_disabled",
                    input_contract_fields=input_contract_fields,
                )

            user_input = self._build_scalping_entry_price_runtime_input(
                stock_name=stock_name,
                stock_code=stock_code,
                ws_data=ws_data or {},
                recent_ticks=recent_ticks or [],
                recent_candles=recent_candles or [],
                price_ctx=price_ctx or {},
            )
            input_contract_fields = self._resolve_ai_input_contract_fields(
                user_input,
                default_schema=(
                    "entry_price_v2"
                    if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_V2_INPUT_ENABLED", False))
                    else "entry_price_compact_v1"
                    if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED", True))
                    else "entry_price_raw_v1"
                ),
                default_mode=(
                    "structured_json"
                    if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_PRICE_COMPACT_INPUT_ENABLED", True))
                    else "plain_text"
                ),
            )
            result = self._call_openai_safe(
                SCALPING_ENTRY_PRICE_PROMPT,
                user_input,
                require_json=True,
                context_name=f"ENTRY_PRICE:{stock_name}:{stock_code}",
                model_override=self._get_tier2_model(),
                schema_name="entry_price_v1",
                endpoint_name="entry_price",
                symbol=stock_code,
                metadata_extra=metadata_extra,
            )
            result = self._merge_last_transport_meta(result)
            normalized = normalize_scalping_entry_price_result(result, fallback_price=fallback_price)
            normalized["ai_model"] = self._get_tier2_model()
            for key, value in result.items():
                if str(key).startswith("openai_"):
                    normalized[key] = value
            self._mark_successful_ai_call(update_last_call_time=False)
            return self._annotate_analysis_result(
                normalized,
                prompt_type="entry_price",
                prompt_version="entry_price_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
                input_contract_fields=input_contract_fields,
            )
        except Exception as e:
            failure_count = self._record_failure_and_maybe_disable(
                context_name=f"ENTRY_PRICE:{stock_name}:{stock_code}"
            )
            log_error(f"🚨 [ENTRY_PRICE] OpenAI 가격결정 에러 ({stock_name}, 연속 실패 {failure_count}회): {e}")
            return self._annotate_analysis_result(
                normalize_scalping_entry_price_result(
                    {
                        "action": "USE_DEFENSIVE",
                        "order_price": fallback_price,
                        "confidence": 0,
                        "reason": "ai_failure_use_defensive_fallback",
                        "max_wait_sec": 90,
                    },
                    fallback_price=fallback_price,
                ),
                prompt_type="entry_price",
                prompt_version="entry_price_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="error",
                input_contract_fields=input_contract_fields,
            )
        finally:
            self.lock.release()

    def analyze_target(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        strategy="SCALPING",
        program_net_qty=0,
        cache_profile="default",
        prompt_profile="shared",
        metadata_extra=None,
    ):
        analysis_started = time.perf_counter()
        prompt_version = "default_v1"
        cache_strategy = strategy
        normalized_profile = "shared"
        matrix_runtime = None
        entry_adm_runtime = None
        lifecycle_ai_runtime = None
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            prompt_type = "swing"
            prompt = SWING_SYSTEM_PROMPT
        else:
            prompt, prompt_type, prompt_version, normalized_profile = self._resolve_scalping_prompt(prompt_profile)
            matrix_runtime = build_holding_exit_matrix_runtime_context(
                prompt_profile=normalized_profile,
                ws_data=ws_data if isinstance(ws_data, dict) else {},
                recent_candles=recent_candles if isinstance(recent_candles, list) else [],
                advisory_enabled=bool(
                    getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED", False)
                    or getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
                ),
            )
            if normalized_profile == "holding":
                entry_adm_runtime = None
            else:
                entry_adm_runtime = build_scalp_entry_adm_runtime_context(
                    prompt_profile=normalized_profile,
                    ws_data=ws_data if isinstance(ws_data, dict) else {},
                    advisory_enabled=bool(
                        getattr(TRADING_RULES, "SCALP_ENTRY_ADM_ADVISORY_ENABLED", False)
                        or getattr(TRADING_RULES, "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED", False)
                    ),
                )
            lifecycle_ai_runtime = build_lifecycle_ai_runtime_context(prompt_profile=normalized_profile)
            cache_strategy = f"{strategy}:{normalized_profile}"
            cache_strategy = f"{cache_strategy}:adm:{matrix_runtime.get('cache_token', 'disabled')}"
            entry_adm_cache_token = (
                entry_adm_runtime.get("cache_token", "disabled")
                if isinstance(entry_adm_runtime, dict)
                else "entry_adm:excluded_holding_profile"
            )
            cache_strategy = f"{cache_strategy}:{entry_adm_cache_token}"
            cache_strategy = f"{cache_strategy}:{lifecycle_ai_runtime.get('cache_token', 'disabled')}"
        use_hot_entry_input = (
            strategy not in ["KOSPI_ML", "KOSDAQ_ML"]
            and prompt_type == "scalping_entry"
            and normalized_profile == "watching"
            and bool(getattr(TRADING_RULES, "OPENAI_ANALYZE_TARGET_HOT_INPUT_ENABLED", True))
            and not bool(getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False))
        )
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            input_contract_fields = {
                "ai_input_schema": "swing_market_text_v1",
                "ai_input_contract_mode": "plain_text",
                "ai_input_build_fallback": "not_built",
            }
        else:
            input_contract_fields = {
                "ai_input_schema": (
                    "entry_screen_v2"
                    if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False))
                    else "entry_screen_hot_v1"
                    if use_hot_entry_input
                    else "entry_screen_compact_v1"
                    if bool(getattr(TRADING_RULES, "OPENAI_SCALPING_COMPACT_INPUT_ENABLED", True))
                    else "entry_screen_legacy_text_v1"
                ),
                "ai_input_contract_mode": (
                    "structured_json"
                    if bool(
                        getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False)
                        or use_hot_entry_input
                        or getattr(TRADING_RULES, "OPENAI_SCALPING_COMPACT_INPUT_ENABLED", True)
                    )
                    else "plain_text"
                ),
                "ai_input_build_fallback": "not_built",
            }
        def _merge_runtime_fields(payload: dict[str, Any] | None) -> dict[str, Any]:
            merged = merge_holding_exit_matrix_result_fields(payload, matrix_runtime)
            if isinstance(entry_adm_runtime, dict):
                merged = merge_scalp_entry_adm_result_fields(merged, entry_adm_runtime)
            return merge_lifecycle_ai_context_fields(merged, lifecycle_ai_runtime)

        cache_key = self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=cache_strategy,
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=program_net_qty,
            cache_profile=cache_profile,
        )
        cached_result = self._cache_get("_analysis_cache", cache_key)
        if cached_result is not None:
            cached_result = _merge_runtime_fields(cached_result)
            return self._annotate_analysis_result(
                cached_result,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                cache_hit=True,
                cache_mode="hit",
                result_source="cache",
                input_contract_fields=input_contract_fields,
            )

        lock_wait_ms = max(
            0,
            int(getattr(TRADING_RULES, "OPENAI_ANALYZE_TARGET_LOCK_WAIT_MS", 250) or 0),
        )
        lock_wait_started = time.perf_counter()
        if lock_wait_ms > 0:
            lock_acquired = self.lock.acquire(timeout=lock_wait_ms / 1000.0)
        else:
            lock_acquired = self.lock.acquire(blocking=False)
        lock_wait_elapsed_ms = max(0, int((time.perf_counter() - lock_wait_started) * 1000))
        if not lock_acquired:
            return self._annotate_analysis_result(
                _merge_runtime_fields(
                    {
                        "action": "WAIT" if prompt_type == "scalping_holding" else "DROP",
                        "score": 0,
                        "reason": "ai_lock_contention_retry_exhausted",
                        "ai_lock_wait_ms": lock_wait_elapsed_ms,
                        "ai_lock_wait_limit_ms": lock_wait_ms,
                        "ai_retry_attempted": bool(lock_wait_ms > 0),
                        "ai_retry_result": "lock_contention_retry_exhausted",
                    }
                ),
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="lock_contention",
                input_contract_fields=input_contract_fields,
            )

        try:
            cached_result = self._cache_get("_analysis_cache", cache_key)
            if cached_result is not None:
                cached_result = _merge_runtime_fields(cached_result)
                return self._annotate_analysis_result(
                    cached_result,
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                    parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                    fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                    cache_hit=True,
                    cache_mode="hit",
                    result_source="cache",
                    input_contract_fields=input_contract_fields,
                )

            if self.ai_disabled:
                return self._annotate_analysis_result(
                    _merge_runtime_fields({"action": "DROP", "score": 0, "reason": "AI 엔진 일시 중단 (연속 실패)"}),
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=False,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="engine_disabled",
                    input_contract_fields=input_contract_fields,
                )

            min_interval_wait_ms = 0
            min_interval_remaining = float(self.min_interval or 0.0) - (time.time() - self.last_call_time)
            if min_interval_remaining > 0:
                time.sleep(min_interval_remaining)
                min_interval_wait_ms = int(round(min_interval_remaining * 1000))

            if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
                formatted_data = self._format_swing_market_data(ws_data, recent_candles, program_net_qty)
                target_model = self._get_tier2_model()
                feature_audit_fields = {}
                input_contract_fields = self._resolve_ai_input_contract_fields(
                    formatted_data,
                    default_schema="swing_market_text_v1",
                    default_mode="plain_text",
                )
            else:
                feature_packet = extract_scalping_feature_packet(ws_data, recent_ticks, recent_candles)
                if use_hot_entry_input:
                    formatted_data = self._format_entry_screen_hot_data(
                        ws_data,
                        recent_ticks,
                        recent_candles,
                        feature_packet=feature_packet,
                        matrix_runtime=matrix_runtime,
                        entry_adm_runtime=entry_adm_runtime,
                        lifecycle_ai_runtime=lifecycle_ai_runtime,
                    )
                else:
                    try:
                        formatted_data = self._format_market_data(
                            ws_data,
                            recent_ticks,
                            recent_candles,
                            feature_packet=feature_packet,
                        )
                    except TypeError:
                        formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
                if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False)):
                    try:
                        structured_input = json.loads(formatted_data)
                    except Exception:
                        structured_input = {
                            "input_schema": "entry_screen_v2",
                            "input_build_fallback": "legacy_text_payload",
                            "legacy_context": formatted_data,
                        }
                    structured_input["runtime_advisory_context"] = {
                        "holding_exit_matrix": (matrix_runtime or {}).get("prompt_context", ""),
                        "entry_adm": (entry_adm_runtime or {}).get("prompt_context", ""),
                        "lifecycle_ai": (lifecycle_ai_runtime or {}).get("prompt_context", ""),
                    }
                    formatted_data = json.dumps(
                        structured_input,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        default=str,
                    )
                elif not use_hot_entry_input:
                    if matrix_runtime and matrix_runtime.get("prompt_context"):
                        formatted_data = f"{formatted_data}\n\n{matrix_runtime['prompt_context']}"
                    if entry_adm_runtime and entry_adm_runtime.get("prompt_context"):
                        formatted_data = f"{formatted_data}\n\n{entry_adm_runtime['prompt_context']}"
                    if lifecycle_ai_runtime and lifecycle_ai_runtime.get("prompt_context"):
                        formatted_data = f"{formatted_data}\n\n{lifecycle_ai_runtime['prompt_context']}"
                formatted_data = self._append_numeric_consistency_recheck_context(
                    formatted_data,
                    metadata_extra=metadata_extra,
                )
                formatted_data = self._append_early_accel_strong_bundle_recheck_context(
                    formatted_data,
                    metadata_extra=metadata_extra,
                )
                target_model = self._get_tier1_model()
                feature_audit_fields = build_scalping_feature_audit_fields(feature_packet)
                input_contract_fields = self._resolve_ai_input_contract_fields(
                    formatted_data,
                    default_schema=(
                        "entry_screen_v2"
                        if bool(getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False))
                        else "entry_screen_hot_v1"
                        if use_hot_entry_input
                        else "entry_screen_compact_v1"
                        if bool(getattr(TRADING_RULES, "OPENAI_SCALPING_COMPACT_INPUT_ENABLED", True))
                        else "entry_screen_legacy_text_v1"
                    ),
                    default_mode=(
                        "structured_json"
                        if bool(
                            getattr(TRADING_RULES, "OPENAI_ENTRY_SCREEN_V2_INPUT_ENABLED", False)
                            or use_hot_entry_input
                            or getattr(TRADING_RULES, "OPENAI_SCALPING_COMPACT_INPUT_ENABLED", True)
                        )
                        else "plain_text"
                    ),
                )

            result = self._call_openai_safe(
                prompt,
                formatted_data,
                require_json=True,
                context_name=f"{target_name}({strategy}:{prompt_type})",
                model_override=target_model,
                schema_name="holding_exit_v1" if prompt_type == "scalping_holding" else "entry_v1",
                endpoint_name="analyze_target",
                symbol=target_name,
                cache_key=cache_key,
                metadata_extra=metadata_extra,
            )
            result = self._merge_last_transport_meta(result)

            if strategy not in ["KOSPI_ML", "KOSDAQ_ML"]:
                result = self._apply_remote_entry_guard(
                    result,
                    prompt_type=prompt_type,
                    ws_data=ws_data,
                    recent_ticks=recent_ticks,
                    recent_candles=recent_candles,
                )
                result = self._normalize_scalping_action_schema(result, prompt_type=prompt_type)
                result.update(feature_audit_fields)
                result = self._annotate_entry_numeric_consistency(
                    result,
                    prompt_type=prompt_type,
                    feature_packet=feature_packet,
                )
                result["ai_model"] = target_model

            result = _merge_runtime_fields(result)
            result["openai_min_interval_wait_ms"] = min_interval_wait_ms
            self._mark_successful_ai_call()
            self._cache_set(
                "_analysis_cache",
                cache_key,
                result,
                self._resolve_analysis_cache_ttl(cache_profile),
            )
            return self._annotate_analysis_result(
                result,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
                input_contract_fields=input_contract_fields,
            )

        except Exception as e:
            failure_count = self._record_failure_and_maybe_disable(
                context_name=f"{target_name}({strategy}:{prompt_type})"
            )
            log_error(f"🚨 [{target_name}][{strategy}] OpenAI 실시간 분석 에러 (연속 실패 {failure_count}회, API키 인덱스 {self.current_api_key_index}): {e}")

            fallback_payload = (
                self._build_buy_side_timeout_reject(
                    prompt_type=prompt_type,
                    strategy=strategy,
                    reason=f"에러: {e}",
                )
                if getattr(TRADING_RULES, "OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED", True)
                else {"action": "WAIT", "score": 50, "reason": f"에러: {e}"}
            )
            fallback_payload = self._merge_last_transport_meta(fallback_payload)
            fallback_payload = _merge_runtime_fields(fallback_payload)
            try:
                fallback_score_50 = float(fallback_payload.get("score")) == 50.0
            except Exception:
                fallback_score_50 = False
            return self._annotate_analysis_result(
                fallback_payload,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=fallback_score_50,
                cache_hit=False,
                cache_mode="miss",
                result_source="exception",
                input_contract_fields=input_contract_fields,
            )
        finally:
            self.lock.release()

    # ==========================================
    # 퍼블릭 메서드: analyze_target_shadow_prompt (그림자 프롬프트)
    # ==========================================

    def analyze_target_shadow_prompt(
        self,
        target_name,
        ws_data,
        recent_ticks,
        recent_candles,
        *,
        strategy="SCALPING",
        prompt_override=None,
        prompt_type="scalping_shadow",
        cache_profile="shadow",
        metadata_extra=None,
    ):
        if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "shadow unsupported for swing"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=0,
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_unsupported",
            )

        analysis_started = time.perf_counter()
        cache_key = self._build_analysis_cache_key_with_profile(
            target_name=target_name,
            strategy=f"{strategy}:{prompt_type}",
            ws_data=ws_data,
            recent_ticks=recent_ticks,
            recent_candles=recent_candles,
            program_net_qty=0,
            cache_profile=cache_profile,
        )
        cached_result = self._cache_get("_analysis_cache", cache_key)
        if cached_result is not None:
            return self._annotate_analysis_result(
                cached_result,
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                cache_hit=True,
                cache_mode="hit",
                result_source="shadow_cache",
            )

        if self.ai_disabled:
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "engine_disabled_skip_shadow_call"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_engine_disabled",
            )

        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": "AI shadow 경합"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_lock_contention",
            )

        try:
            cached_result = self._cache_get("_analysis_cache", cache_key)
            if cached_result is not None:
                return self._annotate_analysis_result(
                    cached_result,
                    prompt_type=prompt_type,
                    prompt_version="shadow_v1",
                    response_ms=int((time.perf_counter() - analysis_started) * 1000),
                    parse_ok=bool(cached_result.get("ai_parse_ok", False)),
                    parse_fail=bool(cached_result.get("ai_parse_fail", False)),
                    fallback_score_50=bool(cached_result.get("ai_fallback_score_50", False)),
                    cache_hit=True,
                    cache_mode="hit",
                    result_source="shadow_cache",
                )

            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            active_prompt = prompt_override if prompt_override else SCALPING_SYSTEM_PROMPT_75_CANARY

            result = self._call_openai_safe(
                active_prompt,
                formatted_data,
                require_json=True,
                context_name=f"{target_name}(shadow:{prompt_type})",
                model_override=self._get_tier1_model(),
                schema_name="holding_exit_v1" if prompt_type == "scalping_holding" else "entry_v1",
                endpoint_name="analyze_target_shadow_prompt",
                symbol=target_name,
                cache_key=cache_key,
                metadata_extra=metadata_extra,
            )
            result = self._merge_last_transport_meta(result)
            result["ai_model"] = self._get_tier1_model()

            self._cache_set(
                "_analysis_cache",
                cache_key,
                result,
                self._resolve_analysis_cache_ttl(cache_profile),
            )
            return self._annotate_analysis_result(
                result,
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_live",
            )
        except Exception as e:
            log_error(f"🚨 [{target_name}] OpenAI shadow 분석 에러: {e}")
            return self._annotate_analysis_result(
                {"action": "WAIT", "score": 50, "reason": f"shadow 에러: {e}"},
                prompt_type=prompt_type,
                prompt_version="shadow_v1",
                response_ms=int((time.perf_counter() - analysis_started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=True,
                cache_hit=False,
                cache_mode="miss",
                result_source="shadow_exception",
            )
        finally:
            self.lock.release()

    # ==========================================
    # 퍼블릭 메서드: analyze_scanner_results (시장 브리핑)
    # ==========================================

    def analyze_scanner_results(self, total_count, survived_count, stats_text, macro_text=""):
        """텔레그램 아침 브리핑 (Macro + Scanner 통합) - OpenAI Tier3 사용"""
        with self.lock:
            data_input = build_scanner_data_input(
                total_count=total_count,
                survived_count=survived_count,
                stats_text=stats_text,
                macro_text=macro_text,
            )

            now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            enriched_input = f"""현재 UTC 시각: {now_utc}

    {data_input}"""

            try:
                return self._call_openai_safe(
                    ENHANCED_MARKET_ANALYSIS_PROMPT,
                    enriched_input,
                    require_json=False,
                    context_name="시장 브리핑",
                    model_override=self._get_tier3_model(),
                    endpoint_name="scanner_report",
                    symbol="-",
                )
            except Exception as e:
                log_error(f"🚨 [시장 브리핑] OpenAI 에러: {e}")
                return f"⚠️ AI 시장 진단 생성 중 에러 발생: {e}"

    # ==========================================
    # 퍼블릭 메서드: 실시간 리포트/게이트키퍼
    # ==========================================

    def generate_realtime_report(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        """실시간 종목 분석 리포트 생성"""
        return self._generate_realtime_report_payload(
            stock_name=stock_name,
            stock_code=stock_code,
            input_data_text=input_data_text,
            analysis_mode=analysis_mode,
        )["report"]

    def extract_realtime_gatekeeper_action(self, report_text):
        """실시간 리포트 본문에서 최종 행동 라벨을 추출합니다."""
        if not isinstance(report_text, str) or not report_text:
            return "UNKNOWN"

        action_labels = [
            "[즉시 매수]",
            "[눌림 대기]",
            "[보유 지속]",
            "[일부 익절]",
            "[전량 회피]",
            "[스캘핑 우선]",
            "[스윙 우선]",
            "[둘 다 아님]",
        ]
        for label in action_labels:
            if label in report_text:
                return label.strip("[]")
        return "UNKNOWN"

    def evaluate_realtime_gatekeeper(self, stock_name, stock_code, realtime_ctx, analysis_mode="AUTO"):
        """generate_realtime_report 결과를 마지막 진입 게이트 판단용으로 정규화합니다."""
        cache_key = self._build_gatekeeper_cache_key(
            stock_name=stock_name,
            stock_code=stock_code,
            realtime_ctx=realtime_ctx,
            analysis_mode=analysis_mode,
        )
        cached_gatekeeper = self._cache_get("_gatekeeper_cache", cache_key)
        if cached_gatekeeper is not None:
            return cached_gatekeeper

        report_payload = self._generate_realtime_report_payload(
            stock_name=stock_name,
            stock_code=stock_code,
            input_data_text=realtime_ctx,
            analysis_mode=analysis_mode,
        )
        report = report_payload["report"]
        action_label = self.extract_realtime_gatekeeper_action(report)
        action_key = normalize_gatekeeper_action_key(action_label)
        action_label = display_gatekeeper_action_label(action_key)
        allow_entry = action_key == "immediate_buy"
        result = {
            "allow_entry": allow_entry,
            "action_label": action_label,
            "action_key": action_key,
            "report": report,
            "selected_mode": report_payload.get("selected_mode", ""),
            "lock_wait_ms": int(report_payload.get("lock_wait_ms", 0) or 0),
            "packet_build_ms": int(report_payload.get("packet_build_ms", 0) or 0),
            "model_call_ms": int(report_payload.get("model_call_ms", 0) or 0),
            "total_internal_ms": int(report_payload.get("total_ms", 0) or 0),
            "cache_hit": False,
            "cache_mode": "miss",
        }
        self._cache_set("_gatekeeper_cache", cache_key, result, self.gatekeeper_cache_ttl)
        return result

    # ==========================================
    # 퍼블릭 메서드: 오버나이트 의사결정
    # ==========================================

    def _format_scalping_overnight_context(self, realtime_ctx):
        ctx = realtime_ctx or {}
        lines = [
            f"- 포지션상태: {ctx.get('position_status', 'UNKNOWN')}",
            f"- 평균단가: {int(ctx.get('avg_price', 0) or 0):,}원",
            f"- 현재가: {int(ctx.get('curr_price', 0) or 0):,}원 (손익 {float(ctx.get('pnl_pct', 0.0) or 0.0):+.2f}%)",
            f"- 보유분수: {float(ctx.get('held_minutes', 0.0) or 0.0):.1f}분",
            f"- 현재 전략라벨: {ctx.get('strat_label', 'SCALPING')}",
            f"- VWAP: {int(ctx.get('vwap_price', 0) or 0):,}원 / 상태: {ctx.get('vwap_status', '')}",
            f"- 체결강도 현재/3분전/5분전: {float(ctx.get('v_pw_now', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_3m', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_5m', 0.0) or 0.0):.1f}",
            f"- 프로그램 순매수 현재/증감: {int(ctx.get('prog_net_qty', 0) or 0):,}주 / {int(ctx.get('prog_delta_qty', 0) or 0):+,}주",
            f"- 외인/기관 순매수: {int(ctx.get('foreign_net', 0) or 0):,}주 / {int(ctx.get('inst_net', 0) or 0):,}주",
            f"- 고가돌파 상태: {ctx.get('high_breakout_status', '')}",
            f"- 일봉 구조: {ctx.get('daily_setup_desc', '')}",
            f"- 5/20/60일선 상태: {ctx.get('ma5_status', '')}, {ctx.get('ma20_status', '')}, {ctx.get('ma60_status', '')}",
            f"- 전일 고점/저점: {int(ctx.get('prev_high', 0) or 0):,} / {int(ctx.get('prev_low', 0) or 0):,}",
            f"- 최근 20일 신고가 근접도: {float(ctx.get('near_20d_high_pct', 0.0) or 0.0):+.2f}%",
            f"- 퀀트 종합점수/결론: {float(ctx.get('score', 0.0) or 0.0):.1f} / {ctx.get('conclusion', '')}",
            f"- 주문상태 참고: {ctx.get('order_status_note', '')}",
        ]
        return "\n".join(lines)

    def _safe_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _summarize_flow_ticks(self, recent_ticks):
        ticks = [tick for tick in (recent_ticks or []) if isinstance(tick, dict)]
        if not ticks:
            return "틱 데이터 없음"

        def _price(tick):
            return self._safe_float(tick.get("price", tick.get("현재가", tick.get("체결가", 0))), 0.0)

        def _volume(tick):
            return self._safe_float(tick.get("volume", tick.get("qty", tick.get("체결량", 0))), 0.0)

        lines = []
        for window in (10, 20, 30):
            sample = ticks[:window]
            if not sample:
                continue
            inferred_rows = [(tick, infer_tick_aggressor_side(tick)) for tick in sample]
            buy_vol = sum(
                _volume(tick)
                for tick, inferred in inferred_rows
                if inferred.get("side") == "BUY" and inferred.get("source") != "price_change_heuristic"
            )
            sell_vol = sum(
                _volume(tick)
                for tick, inferred in inferred_rows
                if inferred.get("side") == "SELL" and inferred.get("source") != "price_change_heuristic"
            )
            total = buy_vol + sell_vol
            buy_pressure = (buy_vol / total * 100.0) if total > 0 else 0.0
            latest = _price(sample[0])
            oldest = _price(sample[-1])
            price_delta = ((latest - oldest) / oldest * 100.0) if oldest > 0 else 0.0
            large_sell = sum(
                1
                for tick, inferred in inferred_rows
                if inferred.get("side") == "SELL"
                and inferred.get("source") != "price_change_heuristic"
                and _volume(tick) >= max(1.0, total * 0.15)
            )
            lines.append(
                f"- 최근 {len(sample)}틱: 가격변화 {price_delta:+.2f}%, 매수압도 {buy_pressure:.1f}%, 대형매도틱 {large_sell}건"
            )
        return "\n".join(lines)

    def _summarize_flow_candles(self, recent_candles):
        candles = [candle for candle in (recent_candles or []) if isinstance(candle, dict)]
        if not candles:
            return "분봉 데이터 없음"

        def _field(candle, *names):
            for name in names:
                if name in candle:
                    return candle.get(name)
            return 0

        lines = []
        for window in (3, 5, 10):
            sample = candles[-window:]
            if len(sample) < 2:
                continue
            first_close = self._safe_float(_field(sample[0], "현재가", "close", "종가"), 0.0)
            last_close = self._safe_float(_field(sample[-1], "현재가", "close", "종가"), 0.0)
            highs = [self._safe_float(_field(item, "고가", "high"), 0.0) for item in sample]
            lows = [self._safe_float(_field(item, "저가", "low"), 0.0) for item in sample]
            vols = [self._safe_float(_field(item, "거래량", "volume"), 0.0) for item in sample]
            slope = ((last_close - first_close) / first_close * 100.0) if first_close > 0 else 0.0
            range_pct = ((max(highs) - min(lows)) / min(lows) * 100.0) if lows and min(lows) > 0 else 0.0
            vol_change = (vols[-1] / (sum(vols[:-1]) / max(1, len(vols) - 1))) if len(vols) > 1 and sum(vols[:-1]) > 0 else 0.0
            lines.append(f"- 최근 {window}분: 종가 기울기 {slope:+.2f}%, 범위 {range_pct:.2f}%, 최신 거래량배율 {vol_change:.2f}x")
        return "\n".join(lines) if lines else "분봉 데이터 부족"

    def _format_flow_history(self, flow_history):
        rows = []
        for item in (flow_history or [])[-5:]:
            if not isinstance(item, dict):
                continue
            flow_state = self._normalize_flow_state_label(item.get("flow_state", "-"))
            rows.append(
                f"- {item.get('time', '-')}: action={item.get('action', '-')}, "
                f"state={flow_state}, pnl={item.get('profit_rate', '-')}, "
                f"rule={item.get('exit_rule', '-')}, reason={item.get('reason', '-')}"
            )
        return "\n".join(rows) if rows else "no_previous_flow_review"

    @staticmethod
    def _normalize_flow_state_label(value):
        return normalize_flow_state_label(value)

    @staticmethod
    def _normalize_holding_score_data_quality(value, *, fallback="partial"):
        text = str(value or "").strip().lower()
        if text in {"fresh", "stale", "partial", "insufficient"}:
            return text
        return fallback

    @staticmethod
    def _compact_holding_score_factors(value, *, limit=6):
        if isinstance(value, list):
            items = value
        elif value in (None, "", "-", []):
            items = []
        else:
            items = [value]
        out = []
        for item in items[:limit]:
            text = str(item or "").replace("\n", " ").strip()
            if text:
                out.append(text[:160])
        return out

    def _derive_holding_score_source_quality(self, feature_packet, audit_fields):
        audit = audit_fields if isinstance(audit_fields, dict) else {}
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        stale_reasons = []
        partial_reasons = []
        fresh_labels = {"fresh", "fresh_computed", "usable", "ok", "pass"}
        stale_labels = {"missing_ticks", "missing_tick_time", "stale_tick", "insufficient"}
        for key in ("tick_context_stale", "quote_stale"):
            raw_value = audit.get(key, packet.get(key))
            text = str(raw_value or "").strip().lower()
            if raw_value is True or text in {"true", "1", "yes", "stale"}:
                stale_reasons.append(key)
        for key in ("tick_context_quality", "ai_input_source_quality_status"):
            text = str(audit.get(key, packet.get(key, "")) or "").strip().lower()
            if text in stale_labels:
                stale_reasons.append(f"{key}:{text}")
            elif text and text not in fresh_labels:
                partial_reasons.append(f"{key}:{text}")
        if self._feature_packet_has_pressure_metric(packet):
            if not self._feature_packet_has_pressure_provenance(packet):
                partial_reasons.append("tick_aggressor_pressure_provenance_missing")
            elif not self._feature_packet_pressure_usable(packet):
                partial_reasons.append("tick_aggressor_pressure_unusable")
        if self._feature_packet_has_micro_vwap_metric(packet):
            if not self._feature_packet_has_micro_vwap_provenance(packet):
                partial_reasons.append("micro_vwap_provenance_missing")
            elif not self._feature_packet_micro_vwap_usable(packet):
                partial_reasons.append("micro_vwap_unavailable")
        micro_quality = str(
            audit.get(
                "microstructure_reaction_source_quality",
                packet.get("microstructure_reaction_source_quality", ""),
            )
            or ""
        ).strip().lower()
        if micro_quality:
            if micro_quality in {"stale", "stale_tick", "stale_quote"}:
                stale_reasons.append(f"microstructure_reaction_source_quality:{micro_quality}")
            elif micro_quality in {"stale_tick_or_quote", "missing", "insufficient", "not_evaluated"}:
                partial_reasons.append(f"microstructure_reaction_source_quality:{micro_quality}")
            elif micro_quality not in fresh_labels | {"fresh_short_window"}:
                partial_reasons.append(f"microstructure_reaction_source_quality:{micro_quality}")
        if not packet:
            return {
                "data_quality": "insufficient",
                "source_quality_reason": "feature_packet_missing",
            }
        if stale_reasons:
            return {
                "data_quality": "stale",
                "source_quality_reason": ",".join(stale_reasons),
            }
        if partial_reasons:
            return {
                "data_quality": "partial",
                "source_quality_reason": ",".join(partial_reasons),
            }
        return {
            "data_quality": "fresh",
            "source_quality_reason": "feature_packet_fresh",
        }

    def _build_scalping_holding_score_v2_context(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        *,
        feature_packet=None,
        feature_audit_fields=None,
    ):
        ctx = position_ctx if isinstance(position_ctx, dict) else {}
        ws = ws_data if isinstance(ws_data, dict) else {}
        packet = feature_packet if isinstance(feature_packet, dict) else {}
        audit = feature_audit_fields if isinstance(feature_audit_fields, dict) else {}
        curr_price = int(self._safe_float(ws.get("curr", ctx.get("curr_price", 0)), 0))
        buy_price = self._safe_float(ctx.get("buy_price", ctx.get("avg_price", 0)), 0.0)
        profit_rate = self._safe_float(ctx.get("profit_rate", ctx.get("pnl_pct", 0.0)), 0.0)
        peak_profit = self._safe_float(ctx.get("peak_profit", profit_rate), profit_rate)
        drawdown = max(0.0, self._safe_float(ctx.get("drawdown_from_peak_pct", peak_profit - profit_rate), 0.0))
        source_quality = self._derive_holding_score_source_quality(packet, audit)
        compact_features = self._compact_holding_score_feature_packet(packet, audit)
        payload = {
            "input_schema": "holding_score_v2",
            "position_context": {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "record_id": ctx.get("record_id"),
                "buy_price": buy_price,
                "curr_price": curr_price,
                "profit_rate": round(profit_rate, 4),
                "peak_profit": round(peak_profit, 4),
                "drawdown_from_peak_pct": round(drawdown, 4),
                "held_sec": int(self._safe_float(ctx.get("held_sec"), 0.0)),
                "buy_qty": int(self._safe_float(ctx.get("buy_qty"), 0.0)),
                "position_tag": ctx.get("position_tag", "-"),
                "entry_source": ctx.get("entry_source", "-"),
                "condition_profile": ctx.get("condition_profile", "-"),
                "avg_down_count": int(self._safe_float(ctx.get("avg_down_count"), 0.0)),
                "pyramid_count": int(self._safe_float(ctx.get("pyramid_count"), 0.0)),
            },
            "entry_time_context": self._compact_entry_time_context(ctx),
            "pnl_context": {
                "profit_rate": round(profit_rate, 4),
                "peak_profit": round(peak_profit, 4),
                "drawdown_from_peak_pct": round(drawdown, 4),
                "distance_to_profit_peak_pct": round(drawdown, 4),
            },
            "market_flow_features": {
                "compact_features": compact_features,
                "tick_summary": self._summarize_tick_windows(recent_ticks, windows=(5, 10, 20)),
                "candle_summary": self._summarize_candle_windows(recent_candles, windows=(3, 5, 10)),
                "live_supply_demand_orderbook": {
                    "execution_strength": ws.get("v_pw", 0.0),
                    "buy_ratio": ws.get("buy_ratio", 0.0),
                    "buy_exec_volume": ws.get("buy_exec_volume", 0),
                    "sell_exec_volume": ws.get("sell_exec_volume", 0),
                    "ask_total_depth": ws.get("ask_tot", 0),
                    "bid_total_depth": ws.get("bid_tot", 0),
                    **self._extract_quote_snapshot(ws),
                },
            },
            "source_quality": {
                **source_quality,
                "aggressor_quality_preserved": True,
                "price_change_heuristic_is_not_aggressor": True,
            },
            "prior_score_context": {
                "prior_score": ctx.get("prior_score"),
                "prior_effective_score": ctx.get("prior_effective_score"),
                "prior_score_source": ctx.get("prior_score_source", "-"),
                "prior_data_quality": ctx.get("prior_data_quality", "-"),
                "prior_score_age_sec": ctx.get("prior_score_age_sec"),
                "prior_effective_usable": bool(ctx.get("prior_effective_usable", False)),
            },
            "hard_guard_context": {
                "hard_guards_remain_authoritative": True,
                "threshold_mutation_forbidden": True,
                "provider_route_change_forbidden": True,
                "broker_order_guard_bypass_forbidden": True,
                "quantity_cap_change_forbidden": True,
                "active_hard_guard": ctx.get("active_hard_guard", "-"),
            },
            "decision_request": {
                "score_contract": "80-100 continuation_favored; 50-79 mixed_hold_neutral; 0-49 exit_risk_favored",
                "return_schema": "holding_score_v2",
            },
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)

    def _normalize_holding_score_result(self, result, *, source_quality=None):
        payload = dict(result or {}) if isinstance(result, dict) else {}
        raw_action = str(payload.get("action", "HOLD") or "HOLD").upper().strip()
        action = raw_action if raw_action in {"HOLD", "TRIM", "EXIT"} else "HOLD"
        score = max(0, min(100, int(self._safe_float(payload.get("score"), 50))))
        confidence = max(0, min(100, int(self._safe_float(payload.get("confidence"), 0))))
        source_quality = source_quality if isinstance(source_quality, dict) else {}
        model_quality = self._normalize_holding_score_data_quality(payload.get("data_quality"))
        derived_quality = self._normalize_holding_score_data_quality(
            source_quality.get("data_quality"),
            fallback=model_quality,
        )
        if derived_quality in {"stale", "insufficient"}:
            data_quality = derived_quality
        elif model_quality in {"stale", "insufficient"}:
            data_quality = model_quality
        elif "partial" in {derived_quality, model_quality}:
            data_quality = "partial"
        else:
            data_quality = "fresh"
        reason_payload = normalize_ai_reason_language(str(payload.get("reason", "") or "holding_score_v2_result"))
        score_basis = normalize_ai_reason_language(
            str(payload.get("score_basis", "") or reason_payload.get("reason") or "holding_score_v2_basis")
        )
        return {
            "action": action,
            "score": score,
            "confidence": confidence,
            "position_state": str(payload.get("position_state", "-") or "-")[:80],
            "score_basis": score_basis.get("reason", "holding_score_v2_basis"),
            "risk_factors": self._compact_holding_score_factors(payload.get("risk_factors")),
            "support_factors": self._compact_holding_score_factors(payload.get("support_factors")),
            "data_quality": data_quality,
            "reason": reason_payload.get("reason", "holding_score_v2_result"),
            "raw": payload,
        }

    def _neutral_holding_score_result(
        self,
        reason,
        *,
        started,
        result_source,
        parse_fail=False,
        input_contract_fields=None,
    ):
        reason_text = str(reason or result_source or "holding_score_unusable")
        payload = {
            "action": "HOLD",
            "score": 50,
            "confidence": 0,
            "position_state": "stale_or_insufficient",
            "score_basis": reason_text,
            "risk_factors": [reason_text],
            "support_factors": [],
            "data_quality": "insufficient",
            "reason": reason_text,
            "holding_score_input_schema": "holding_score_v2",
            "holding_score_data_quality": "insufficient",
            "holding_score_confidence": 0,
            "holding_score_basis": reason_text,
            "holding_score_raw": 50,
            "holding_score_effective": 50,
            "holding_score_source": result_source,
            "holding_score_raw_source": result_source,
            "holding_score_raw_data_quality": "insufficient",
            "holding_score_effective_source": result_source,
            "holding_score_effective_from_prior": False,
            "holding_score_effective_usable": False,
            "holding_score_excluded_reason": reason_text,
            "holding_score_age_sec": 0,
        }
        return self._annotate_analysis_result(
            payload,
            prompt_type="scalping_holding_score",
            prompt_version="holding_score_v2",
            response_ms=int((time.perf_counter() - started) * 1000),
            parse_ok=False,
            parse_fail=bool(parse_fail),
            fallback_score_50=True,
            cache_hit=False,
            cache_mode="miss",
            result_source=result_source,
            input_contract_fields=input_contract_fields
            or {
                "ai_input_schema": "holding_score_v2",
                "ai_input_contract_mode": "structured_json",
                "ai_input_build_fallback": "not_built",
            },
        )

    def evaluate_scalping_holding_score(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        metadata_extra=None,
    ):
        started = time.perf_counter()
        input_contract_fields = {
            "ai_input_schema": "holding_score_v2",
            "ai_input_contract_mode": "structured_json",
            "ai_input_build_fallback": "not_built",
        }
        lock_wait_ms = max(
            0,
            int(getattr(TRADING_RULES, "OPENAI_ANALYZE_TARGET_LOCK_WAIT_MS", 250) or 0),
        )
        lock_wait_started = time.perf_counter()
        if lock_wait_ms > 0:
            lock_acquired = self.lock.acquire(timeout=lock_wait_ms / 1000.0)
        else:
            lock_acquired = self.lock.acquire(blocking=False)
        lock_wait_elapsed_ms = max(0, int((time.perf_counter() - lock_wait_started) * 1000))
        if not lock_acquired:
            payload = self._neutral_holding_score_result(
                "lock_contention",
                started=started,
                result_source="lock_contention",
                input_contract_fields=input_contract_fields,
            )
            payload.update(
                {
                    "ai_lock_wait_ms": lock_wait_elapsed_ms,
                    "ai_lock_wait_limit_ms": lock_wait_ms,
                    "ai_retry_attempted": bool(lock_wait_ms > 0),
                    "ai_retry_result": "lock_contention_retry_exhausted",
                }
            )
            return payload

        try:
            if self.ai_disabled:
                return self._neutral_holding_score_result(
                    "engine_disabled",
                    started=started,
                    result_source="engine_disabled",
                    input_contract_fields=input_contract_fields,
                )

            feature_packet = extract_scalping_feature_packet(ws_data or {}, recent_ticks or [], recent_candles or [])
            feature_audit_fields = build_scalping_feature_audit_fields(feature_packet)
            source_quality = self._derive_holding_score_source_quality(feature_packet, feature_audit_fields)
            user_input = self._build_scalping_holding_score_v2_context(
                stock_name,
                stock_code,
                ws_data or {},
                recent_ticks or [],
                recent_candles or [],
                position_ctx or {},
                feature_packet=feature_packet,
                feature_audit_fields=feature_audit_fields,
            )
            input_contract_fields = self._resolve_ai_input_contract_fields(
                user_input,
                default_schema="holding_score_v2",
                default_mode="structured_json",
            )
            result = self._call_openai_safe(
                SCALPING_HOLDING_SCORE_SYSTEM_PROMPT,
                user_input,
                require_json=True,
                context_name=f"HOLDING_SCORE:{stock_name}",
                model_override=self._get_tier1_model(),
                schema_name="holding_score_v2",
                endpoint_name="holding_score",
                symbol=stock_code,
                metadata_extra=metadata_extra,
            )
            transport_meta = self._consume_last_transport_meta()
            if isinstance(result, dict) and transport_meta:
                result.update(transport_meta)
            normalized = self._normalize_holding_score_result(result, source_quality=source_quality)
            normalized.update(feature_audit_fields)
            meta_source = result if isinstance(result, dict) else transport_meta
            for key, value in meta_source.items():
                if str(key).startswith("openai_"):
                    normalized[key] = value
            normalized.update(
                {
                    "ai_model": self._get_tier1_model(),
                    "holding_score_input_schema": "holding_score_v2",
                    "holding_score_data_quality": normalized["data_quality"],
                    "holding_score_confidence": normalized["confidence"],
                    "holding_score_basis": normalized["score_basis"],
                    "holding_score_raw": normalized["score"],
                    "holding_score_effective": normalized["score"],
                    "holding_score_source": "live",
                    "holding_score_raw_source": "live",
                    "holding_score_raw_data_quality": normalized["data_quality"],
                    "holding_score_effective_source": "live",
                    "holding_score_effective_from_prior": False,
                    "holding_score_age_sec": 0,
                    "holding_score_effective_usable": normalized["data_quality"] in {"fresh", "partial"},
                    "holding_score_excluded_reason": "-"
                    if normalized["data_quality"] in {"fresh", "partial"}
                    else normalized["data_quality"],
                    "holding_score_source_quality_reason": source_quality.get("source_quality_reason", "-"),
                }
            )
            self._mark_successful_ai_call(update_last_call_time=False)
            return self._annotate_analysis_result(
                normalized,
                prompt_type="scalping_holding_score",
                prompt_version="holding_score_v2",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
                input_contract_fields=input_contract_fields,
            )
        except Exception as e:
            failure_count = self._record_failure_and_maybe_disable(context_name=f"HOLDING_SCORE:{stock_name}")
            timeout_like = self._is_openai_timeout_like_error(e)
            result_source = "timeout" if timeout_like else "exception"
            log_error(
                f"🚨 [HOLDING_SCORE] OpenAI score {result_source} fail-closed "
                f"({stock_name}, failures {failure_count}): {e}"
            )
            payload = self._neutral_holding_score_result(
                result_source,
                started=started,
                result_source=result_source,
                parse_fail=True,
                input_contract_fields=input_contract_fields,
            )
            timing_meta = getattr(e, "timing_meta", None)
            if isinstance(timing_meta, dict):
                payload.update({key: value for key, value in timing_meta.items() if str(key).startswith("openai_")})
            payload["holding_score_timeout_like"] = bool(timeout_like)
            payload["holding_score_transport_fail_closed"] = True
            payload["holding_score_transport_fail_closed_reason"] = str(e)[:160]
            return payload
        finally:
            self.lock.release()

    def _build_scalping_holding_flow_v2_context(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        *,
        flow_history=None,
        decision_kind="intraday_exit",
        matrix_runtime=None,
        lifecycle_ai_runtime=None,
    ):
        ctx = position_ctx or {}
        ws = ws_data if isinstance(ws_data, dict) else {}
        curr_price = int(self._safe_float(ws.get("curr", ctx.get("curr_price", 0)), 0))
        buy_price = self._safe_float(ctx.get("buy_price", ctx.get("avg_price", 0)), 0.0)
        peak_profit = self._safe_float(ctx.get("peak_profit", 0.0), 0.0)
        pnl = self._safe_float(ctx.get("profit_rate", ctx.get("pnl_pct", 0.0)), 0.0)
        day_high = self._safe_float(ctx.get("day_high", 0), 0.0)
        distance_from_day_high = (
            ((curr_price - day_high) / day_high * 100.0)
            if curr_price > 0 and day_high > 0
            else self._safe_float(ctx.get("distance_from_day_high_pct", 0), 0.0)
        )
        prior_reviews = []
        for item in (flow_history or [])[-5:]:
            if not isinstance(item, dict):
                continue
            prior_reviews.append(
                {
                    "time": item.get("time"),
                    "action": item.get("action"),
                    "flow_state": self._normalize_flow_state_label(item.get("flow_state", "-")),
                    "profit_rate": item.get("profit_rate"),
                    "exit_rule": item.get("exit_rule"),
                    "reason": item.get("reason"),
                }
            )
        orderbook_micro = ctx.get("orderbook_micro") if isinstance(ctx.get("orderbook_micro"), dict) else {}
        payload = {
            "input_schema": "holding_flow_v2",
            "decision_type": {
                "kind": decision_kind,
                "stock_name": stock_name,
                "stock_code": stock_code,
                "candidate_exit_rule": ctx.get("exit_rule", "-"),
            },
            "position": {
                "average_entry_price": buy_price,
                "current_price": curr_price,
                "current_pnl_pct": round(pnl, 4),
                "peak_pnl_pct": round(peak_profit, 4),
                "drawdown_from_peak_pct": round(self._safe_float(ctx.get("drawdown", peak_profit - pnl), 0.0), 4),
                "held_sec": int(self._safe_float(ctx.get("held_sec", self._safe_float(ctx.get("held_minutes", 0.0)) * 60.0), 0.0)),
                "current_ai_score": round(self._safe_float(ctx.get("current_ai_score", ctx.get("score", 0.0)), 0.0), 3),
                "distance_from_day_high_pct": round(distance_from_day_high, 4),
                "allowed_worsen_pct": self._safe_float(ctx.get("worsen_pct", 0.80), 0.80),
            },
            "entry_time_context": self._compact_entry_time_context(ctx),
            "prior_flow_reviews": prior_reviews,
            "deterministic_guard_state": {
                "candidate_exit_rule": ctx.get("exit_rule", "-"),
                "sell_reason_type": ctx.get("sell_reason_type", "-"),
                "guard_reason": ctx.get("reason", "-"),
                "system_guards_remain_authoritative": True,
            },
            "ofi_smoothing_state": {
                "regime": ctx.get("holding_flow_ofi_regime", ctx.get("ofi_regime")),
                "micro_score_raw": ctx.get("holding_flow_ofi_micro_score_raw"),
                "micro_score_smooth": ctx.get("holding_flow_ofi_micro_score_smooth"),
                "snapshot_age_ms": ctx.get("holding_flow_ofi_snapshot_age_ms"),
            },
            "orderbook_micro": orderbook_micro,
            "live_supply_demand_orderbook": {
                "execution_strength": ws.get("v_pw", 0.0),
                "buy_ratio": ws.get("buy_ratio", 0.0),
                "buy_exec_volume": ws.get("buy_exec_volume", 0),
                "sell_exec_volume": ws.get("sell_exec_volume", 0),
                "ask_total_depth": ws.get("ask_tot", 0),
                "bid_total_depth": ws.get("bid_tot", 0),
                **self._extract_quote_snapshot(ws),
            },
            "tick_summary": self._summarize_tick_windows(recent_ticks, windows=(5, 10, 20, 30)),
            "candle_summary": self._summarize_candle_windows(recent_candles, windows=(3, 5, 10)),
            "recent_ticks_latest_first": self._compact_recent_ticks(recent_ticks, limit=5),
            "recent_candles_latest_window": self._compact_recent_candles(recent_candles, limit=5),
            "runtime_advisory_context": {
                "holding_exit_matrix": (matrix_runtime or {}).get("prompt_context", ""),
                "lifecycle_ai": (lifecycle_ai_runtime or {}).get("prompt_context", ""),
            },
            "decision_request": {
                "flow_states": ["absorption", "recovery", "distribution", "breakdown", "quiet"],
                "score_is_confidence_only": True,
                "hard_guards_override_ai": True,
            },
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)

    def _format_scalping_holding_flow_context(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        flow_history=None,
        decision_kind="intraday_exit",
    ):
        ctx = position_ctx or {}
        curr_price = int(self._safe_float(ws_data.get("curr", ctx.get("curr_price", 0)) if isinstance(ws_data, dict) else ctx.get("curr_price", 0), 0))
        buy_price = self._safe_float(ctx.get("buy_price", ctx.get("avg_price", 0)), 0.0)
        day_high = self._safe_float(ctx.get("day_high", 0), 0.0)
        distance_from_day_high = ((curr_price - day_high) / day_high * 100.0) if curr_price > 0 and day_high > 0 else self._safe_float(ctx.get("distance_from_day_high_pct", 0), 0.0)
        cadence_guide = (
            "For overnight SELL_TODAY re-checks, this should be one-shot. Use next_review_sec=0 unless another review is clearly required; otherwise use 300-600 seconds."
            if str(decision_kind or "") == "overnight_sell_today"
            else "For intraday exit-candidate re-checks, request only 30-90 seconds. Choose HOLD/TRIM only with strong evidence."
        )
        entry_time_context = json.dumps(
            self._compact_entry_time_context(ctx),
            ensure_ascii=True,
            separators=(",", ":"),
            default=str,
        )
        return f"""
[DECISION_TYPE]
- kind: {decision_kind}
- stock: {stock_name}({stock_code})
- candidate_exit_rule: {ctx.get('exit_rule', '-')}
- review_cadence: {cadence_guide}

[POSITION_CONTEXT]
- average_entry_price: {buy_price:,.2f}
- current_price: {curr_price:,}
- current_pnl_pct: {self._safe_float(ctx.get('profit_rate', ctx.get('pnl_pct', 0.0))):+.2f}
- peak_pnl_pct: {self._safe_float(ctx.get('peak_profit', 0.0)):+.2f}
- drawdown_from_peak_pct: {self._safe_float(ctx.get('drawdown', 0.0)):.2f}
- held_sec: {int(self._safe_float(ctx.get('held_sec', self._safe_float(ctx.get('held_minutes', 0.0)) * 60.0), 0.0))}
- current_ai_score: {self._safe_float(ctx.get('current_ai_score', ctx.get('score', 0.0))):.1f}
- distance_from_day_high_pct: {distance_from_day_high:+.2f}
- allowed_worsen_pct: {self._safe_float(ctx.get('worsen_pct', 0.80)):.2f}

[ENTRY_TIME_CONTEXT]
{entry_time_context}

[RECENT_FLOW_REVIEW]
{self._format_flow_history(flow_history)}

[TICK_FLOW_SUMMARY]
{self._summarize_flow_ticks(recent_ticks)}

[MINUTE_CANDLE_FLOW_SUMMARY]
{self._summarize_flow_candles(recent_candles)}

[LIVE_SUPPLY_DEMAND_AND_ORDERBOOK]
- execution_strength: {self._safe_float((ws_data or {}).get('v_pw', 0.0)):.1f}
- buy_ratio: {self._safe_float((ws_data or {}).get('buy_ratio', 0.0)):.1f}
- buy_exec_volume: {int(self._safe_float((ws_data or {}).get('buy_exec_volume', 0))):,}
- sell_exec_volume: {int(self._safe_float((ws_data or {}).get('sell_exec_volume', 0))):,}
- ask_total_depth: {int(self._safe_float((ws_data or {}).get('ask_tot', 0))):,}
- bid_total_depth: {int(self._safe_float((ws_data or {}).get('bid_tot', 0))):,}

[DECISION_REQUEST]
Do not cut by a single score cutoff. First classify the flow as closest to absorption, recovery, distribution, breakdown, or quiet, then choose HOLD, TRIM, or EXIT.
"""

    def _normalize_holding_flow_result(self, result, *, decision_kind="intraday_exit"):
        payload = dict(result or {}) if isinstance(result, dict) else {}
        raw_action = str(payload.get("action", "EXIT") or "EXIT").upper().strip()
        action = raw_action if raw_action in {"HOLD", "TRIM", "EXIT"} else "EXIT"
        try:
            score = int(float(payload.get("score", 0)))
        except Exception:
            score = 0
        evidence = payload.get("evidence")
        if not isinstance(evidence, list):
            evidence = [str(evidence)] if evidence else []
        next_review_default = 60 if decision_kind != "overnight_sell_today" else 0
        next_review_raw = int(self._safe_float(payload.get("next_review_sec", next_review_default), next_review_default))
        if decision_kind == "overnight_sell_today":
            next_review_sec = max(0, min(600, next_review_raw))
        else:
            next_review_sec = max(30, min(90, next_review_raw))
        return {
            "action": action,
            "score": max(0, min(100, score)),
            "flow_state": self._normalize_flow_state_label(payload.get("flow_state", "-")),
            "raw_flow_state": str(payload.get("flow_state", "-") or "-")[:80],
            "thesis": str(payload.get("thesis", "-") or "-")[:160],
            "evidence": [str(item).replace("\n", " ")[:160] for item in evidence[:5]],
            "reason": str(payload.get("reason", "-") or "-").replace("\n", " ")[:180],
            "next_review_sec": next_review_sec,
            "raw": payload,
        }

    def evaluate_scalping_holding_flow(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        position_ctx,
        flow_history=None,
        decision_kind="intraday_exit",
        metadata_extra=None,
    ):
        started = time.perf_counter()
        input_contract_fields = {
            "ai_input_schema": (
                "holding_flow_v2"
                if bool(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED", False))
                else "holding_flow_text_v1"
            ),
            "ai_input_contract_mode": (
                "structured_json"
                if bool(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED", False))
                else "plain_text"
            ),
            "ai_input_build_fallback": "not_built",
        }
        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                {
                    "action": "EXIT",
                    "score": 0,
                    "flow_state": "ai_lock_contention",
                    "thesis": "ai_lock_contention",
                    "evidence": ["lock_contention"],
                    "reason": "ai_lock_contention_keep_exit_candidate",
                    "next_review_sec": 30,
                },
                prompt_type="holding_exit_flow",
                prompt_version="flow_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="lock_contention",
                input_contract_fields=input_contract_fields,
            )

        try:
            if self.ai_disabled:
                return self._annotate_analysis_result(
                    {
                        "action": "EXIT",
                        "score": 0,
                        "flow_state": "engine_disabled",
                        "thesis": "engine_disabled",
                        "evidence": ["engine_disabled"],
                        "reason": "engine_disabled_keep_exit_candidate",
                        "next_review_sec": 30,
                    },
                    prompt_type="holding_exit_flow",
                    prompt_version="flow_v1",
                    response_ms=int((time.perf_counter() - started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=False,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="engine_disabled",
                    input_contract_fields=input_contract_fields,
                )

            matrix_runtime = build_holding_exit_matrix_runtime_context(
                prompt_profile="holding",
                ws_data=ws_data if isinstance(ws_data, dict) else {},
                recent_candles=recent_candles if isinstance(recent_candles, list) else [],
                advisory_enabled=bool(
                    getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED", False)
                    or getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
                ),
            )
            lifecycle_ai_runtime = build_lifecycle_ai_runtime_context(prompt_profile="holding", stage="holding")
            if bool(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED", False)):
                user_input = self._build_scalping_holding_flow_v2_context(
                    stock_name,
                    stock_code,
                    ws_data or {},
                    recent_ticks or [],
                    recent_candles or [],
                    position_ctx or {},
                    flow_history=flow_history,
                    decision_kind=decision_kind,
                    matrix_runtime=matrix_runtime,
                    lifecycle_ai_runtime=lifecycle_ai_runtime,
                )
            else:
                user_input = self._format_scalping_holding_flow_context(
                    stock_name,
                    stock_code,
                    ws_data or {},
                    recent_ticks or [],
                    recent_candles or [],
                    position_ctx or {},
                    flow_history=flow_history,
                    decision_kind=decision_kind,
                )
                if matrix_runtime.get("prompt_context"):
                    user_input = f"{user_input}\n\n{matrix_runtime['prompt_context']}"
                if lifecycle_ai_runtime.get("prompt_context"):
                    user_input = f"{user_input}\n\n{lifecycle_ai_runtime['prompt_context']}"
            input_contract_fields = self._resolve_ai_input_contract_fields(
                user_input,
                default_schema=(
                    "holding_flow_v2"
                    if bool(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED", False))
                    else "holding_flow_text_v1"
                ),
                default_mode=(
                    "structured_json"
                    if bool(getattr(TRADING_RULES, "OPENAI_HOLDING_FLOW_V2_INPUT_ENABLED", False))
                    else "plain_text"
                ),
            )
            result = self._call_openai_safe(
                SCALPING_HOLDING_FLOW_SYSTEM_PROMPT,
                user_input,
                require_json=True,
                context_name=f"HOLDING_FLOW:{stock_name}:{decision_kind}",
                model_override=self._get_tier2_model(),
                schema_name="holding_exit_flow_v1",
                endpoint_name="holding_flow",
                symbol=stock_code,
                metadata_extra=metadata_extra,
            )
            normalized = self._normalize_holding_flow_result(result, decision_kind=decision_kind)
            normalized = merge_holding_exit_matrix_result_fields(
                normalized,
                matrix_runtime,
                position_ctx=position_ctx if isinstance(position_ctx, dict) else {},
            )
            normalized = merge_lifecycle_ai_context_fields(normalized, lifecycle_ai_runtime)
            normalized["ai_model"] = self._get_tier2_model()
            self._mark_successful_ai_call(update_last_call_time=False)
            return self._annotate_analysis_result(
                normalized,
                prompt_type="holding_exit_flow",
                prompt_version="flow_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
                input_contract_fields=input_contract_fields,
            )
        except Exception as e:
            failure_count = self._record_failure_and_maybe_disable(
                context_name=f"HOLDING_FLOW:{stock_name}:{decision_kind}"
            )
            log_error(f"🚨 [HOLDING_FLOW] OpenAI 판정 에러 ({stock_name}/{decision_kind}, 연속 실패 {failure_count}회): {e}")
            return self._annotate_analysis_result(
                {
                    "action": "EXIT",
                    "score": 0,
                    "flow_state": "exception",
                    "thesis": "ai_flow_failure",
                    "evidence": [str(e)],
                    "reason": "ai_flow_failure_keep_exit_candidate",
                    "next_review_sec": 30,
                },
                prompt_type="holding_exit_flow",
                prompt_version="flow_v1",
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="exception",
                input_contract_fields=input_contract_fields,
            )
        finally:
            self.lock.release()

    def evaluate_scalping_overnight_decision(self, stock_name, stock_code, realtime_ctx):
        """장마감 전 SCALPING 포지션의 오버나이트/당일청산 의사결정을 JSON으로 반환합니다."""
        started = time.perf_counter()
        prompt_type = "scalping_overnight"
        prompt_version = "overnight_v1"
        if not self.lock.acquire(blocking=False):
            return self._annotate_analysis_result(
                {
                    'action': 'SELL_TODAY',
                    'confidence': 0,
                    'reason': 'ai_lock_contention',
                    'risk_note': 'lock_contention',
                    'raw': {},
                },
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="lock_contention",
            )
        try:
            if self.ai_disabled:
                return self._annotate_analysis_result(
                    {
                        'action': 'SELL_TODAY',
                        'confidence': 0,
                        'reason': 'engine_disabled_sell_today_fallback',
                        'risk_note': 'engine_disabled',
                        'raw': {},
                    },
                    prompt_type=prompt_type,
                    prompt_version=prompt_version,
                    response_ms=int((time.perf_counter() - started) * 1000),
                    parse_ok=False,
                    parse_fail=False,
                    fallback_score_50=False,
                    cache_hit=False,
                    cache_mode="miss",
                    result_source="engine_disabled",
                )
            user_input = (
                f"[SCALPING_OVERNIGHT_DECISION_REQUEST]\n"
                f"stock_name: {stock_name}\nstock_code: {stock_code}\n\n"
                f"[DECISION_INPUT]\n{self._format_scalping_overnight_context(realtime_ctx)}"
            )
            result = self._call_openai_safe(
                SCALPING_OVERNIGHT_DECISION_PROMPT,
                user_input,
                require_json=True,
                context_name=f"SCALP_OVERNIGHT:{stock_name}",
                model_override=self._get_tier2_model(),
                schema_name="overnight_v1",
                endpoint_name="overnight",
                symbol=stock_code,
                metadata_extra={
                    "sim_record_id": realtime_ctx.get("sim_record_id") if isinstance(realtime_ctx, dict) else None,
                    "sim_parent_record_id": realtime_ctx.get("sim_parent_record_id") if isinstance(realtime_ctx, dict) else None,
                    "source_event_stage": "scalp_sim_overnight_decision",
                },
            )
            result = self._merge_last_transport_meta(result)
            action = str(result.get('action', 'SELL_TODAY') or 'SELL_TODAY').upper()
            if action not in {'SELL_TODAY', 'HOLD_OVERNIGHT'}:
                action = 'SELL_TODAY'
            try:
                confidence = int(float(result.get('confidence', 0) or 0))
            except Exception:
                confidence = 0
            payload = {
                'action': action,
                'confidence': max(0, min(100, confidence)),
                'reason': str(result.get('reason', '') or 'reason_unavailable'),
                'risk_note': str(result.get('risk_note', '') or 'risk_unavailable'),
                'ai_model': self._get_tier2_model(),
                'raw': result,
            }
            for key, value in result.items():
                if str(key).startswith("openai_"):
                    payload[key] = value
            self._mark_successful_ai_call(update_last_call_time=False)
            return self._annotate_analysis_result(
                payload,
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=True,
                parse_fail=False,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="live",
            )
        except Exception as e:
            sim_observation_only = self._is_sim_observation_overnight_context(realtime_ctx)
            if sim_observation_only:
                failure_count = self.consecutive_failures + 1
            else:
                failure_count = self._record_failure_and_maybe_disable(
                    context_name=f"SCALP_OVERNIGHT:{stock_name}:{stock_code}"
                )
            log_error(f"🚨 [SCALPING 오버나이트 판정] OpenAI 에러 ({stock_name}, 연속 실패 {failure_count}회): {e}")
            return self._annotate_analysis_result(
                {
                    'action': 'SELL_TODAY',
                    'confidence': 0,
                    'reason': 'ai_failure_sell_today_fallback',
                    'risk_note': 'ai_response_error_or_insufficient_context',
                    'ai_exception_type': type(e).__name__,
                    'ai_exception_message': str(e),
                    'sim_observation_failure_isolated': sim_observation_only,
                    'raw': {},
                },
                prompt_type=prompt_type,
                prompt_version=prompt_version,
                response_ms=int((time.perf_counter() - started) * 1000),
                parse_ok=False,
                parse_fail=True,
                fallback_score_50=False,
                cache_hit=False,
                cache_mode="miss",
                result_source="exception",
            )
        finally:
            self.lock.release()

    # ==========================================
    # 퍼블릭 메서드: 조건검색식 진입/청산 판단
    # ==========================================

    def evaluate_condition_entry(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile):
        """조건검색식 진입 판단: 전용 prompt 대신 기존 scalping entry route를 재사용한다."""
        try:
            result = self.analyze_target(
                stock_name,
                ws_data,
                recent_ticks,
                recent_candles,
                strategy="SCALPING",
                cache_profile="condition_entry",
                prompt_profile="watching",
            )
            return normalize_condition_entry_from_scalping_result(result)
        except Exception as e:
            log_error(f"🚨 [조건검색식 진입 판단] OpenAI 에러: {e}")
            return {
                "decision": "SKIP",
                "confidence": 0,
                "order_type": "NONE",
                "position_size_ratio": 0.0,
                "invalidation_price": 0,
                "reasons": [f"AI 판정 실패: {e}"],
                "risks": ["데이터 부족 또는 AI 응답 오류"],
            }

    def evaluate_condition_exit(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile, profit_rate, peak_profit, current_ai_score):
        """조건검색식 청산 판단: scalping holding score contract에 명시적 PnL context를 전달한다."""
        try:
            profile = condition_profile if isinstance(condition_profile, dict) else {}
            curr_price = 0
            if isinstance(ws_data, dict):
                curr_price = int(self._safe_float(ws_data.get("curr", ws_data.get("current_price", 0)), 0))
            position_ctx = {
                "record_id": profile.get("record_id"),
                "buy_price": profile.get("buy_price") or profile.get("avg_price"),
                "curr_price": curr_price,
                "profit_rate": profit_rate,
                "peak_profit": peak_profit,
                "drawdown_from_peak_pct": max(0.0, self._safe_float(peak_profit, 0.0) - self._safe_float(profit_rate, 0.0)),
                "held_sec": int(self._safe_float(profile.get("held_sec", profile.get("held_minutes", 0) or 0), 0)),
                "buy_qty": int(self._safe_float(profile.get("buy_qty", 0), 0)),
                "position_tag": profile.get("position_tag", "CONDITION"),
                "entry_source": "condition_exit",
                "condition_profile": {
                    "name": profile.get("name"),
                    "strategy": profile.get("strategy"),
                    "condition_id": profile.get("condition_id"),
                },
                "prior_score": current_ai_score,
                "prior_effective_score": current_ai_score,
                "prior_score_source": "condition_exit_arg",
                "prior_data_quality": "partial",
                "prior_effective_usable": True,
            }
            result = self.evaluate_scalping_holding_score(
                stock_name,
                stock_code,
                ws_data,
                recent_ticks,
                recent_candles,
                position_ctx,
                metadata_extra={
                    "source_event_stage": "condition_exit",
                    "condition_profile_name": profile.get("name"),
                },
            )
            return normalize_condition_exit_from_scalping_result(result)
        except Exception as e:
            log_error(f"🚨 [조건검색식 청산 판단] OpenAI 에러: {e}")
            return {
                "decision": "HOLD",
                "confidence": 0,
                "trim_ratio": 0.0,
                "new_stop_price": 0,
                "reason_primary": f"AI 판정 실패: {e}",
                "warning": "데이터 부족 또는 AI 응답 오류",
            }

class OpenAIDualPersonaShadowEngine(GPTSniperEngine):
    """Shadow-only dual persona engine for gatekeeper / overnight calibration."""

    HARD_RISK_FLAGS = {
        "VWAP_BELOW",
        "LARGE_SELL_PRINT",
        "GAP_TOO_HIGH",
        "THIN_LIQUIDITY",
        "WEAK_PROGRAM_FLOW",
        "FAILED_BREAKOUT",
    }

    def __init__(self, api_keys):
        super().__init__(api_keys)
        worker_count = max(1, int(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_WORKERS", 2) or 2))
        self.shadow_executor = ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="openai-dual-shadow",
        )
        self.shadow_enabled = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_ENABLED", True))
        self.shadow_mode = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_SHADOW_MODE", True))
        print(
            f"🧠 [OpenAI 듀얼 페르소나] shadow={'ON' if self.shadow_mode else 'OFF'} "
            f"/ workers={worker_count}"
        )

    def _coerce_bool(self, value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    def _normalize_confidence(self, value):
        try:
            conf = float(value)
        except Exception:
            conf = 0.0
        if conf > 1.0:
            conf = conf / 100.0
        return max(0.0, min(1.0, conf))

    def _normalize_risk_flags(self, value):
        if isinstance(value, list):
            raw_items = value
        elif value in (None, "", "None"):
            raw_items = []
        else:
            raw_items = str(value).replace("|", ",").split(",")
        flags = []
        for item in raw_items:
            text = str(item or "").strip().upper().replace(" ", "_")
            if text:
                flags.append(text)
        return flags[:8]

    def _normalize_shadow_result(self, result, decision_type):
        allowed_actions = {
            "gatekeeper": {"ALLOW_ENTRY", "WAIT", "REJECT"},
            "overnight": {"HOLD_OVERNIGHT", "SELL_TODAY"},
        }[decision_type]

        if not isinstance(result, dict):
            result = {}

        action = str(result.get("action", "WAIT" if decision_type == "gatekeeper" else "SELL_TODAY")).upper().strip()
        if action not in allowed_actions:
            action = "WAIT" if decision_type == "gatekeeper" else "SELL_TODAY"

        try:
            score = int(float(result.get("score", 50)))
        except Exception:
            score = 50
        score = max(0, min(100, score))

        try:
            size_bias = int(float(result.get("size_bias", 0)))
        except Exception:
            size_bias = 0
        size_bias = max(-2, min(2, size_bias))

        return {
            "action": action,
            "score": score,
            "confidence": self._normalize_confidence(result.get("confidence", 0.0)),
            "risk_flags": self._normalize_risk_flags(result.get("risk_flags", [])),
            "size_bias": size_bias,
            "veto": self._coerce_bool(result.get("veto", False)),
            "thesis": str(result.get("thesis", "") or "").replace("\n", " ").strip()[:160],
            "invalidator": str(result.get("invalidator", "") or "").replace("\n", " ").strip()[:160],
        }

    def _build_shadow_payload(self, decision_type, stock_name, stock_code, strategy, realtime_ctx):
        return {
            "decision_type": decision_type.upper(),
            "stock_name": stock_name,
            "stock_code": stock_code,
            "strategy": str(strategy or "").upper(),
            "shadow_mode": "SHADOW",
            "context": realtime_ctx or {},
        }

    def _call_persona(self, decision_type, persona_prompt, payload, context_name):
        raw_result = self._call_openai_safe(
            persona_prompt,
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            require_json=True,
            context_name=context_name,
            model_override=self.fast_model_name,
            temperature_override=0.05,
            endpoint_name=f"dual_persona_{decision_type}",
            symbol=stock_code if (stock_code := str(payload.get('stock_code', '') or '-')) else "-",
        )
        return self._normalize_shadow_result(raw_result, decision_type)

    def _gemini_baseline(self, decision_type, gemini_result):
        gemini_result = gemini_result or {}
        if decision_type == "gatekeeper":
            action_label = str(gemini_result.get("action_label", "UNKNOWN") or "UNKNOWN")
            action_key = normalize_gatekeeper_action_key(gemini_result.get("action_key") or action_label)
            action_label = display_gatekeeper_action_label(action_key)
            allow_entry = bool(gemini_result.get("allow_entry", False))
            if allow_entry:
                return {"action": "ALLOW_ENTRY", "score": 85, "confidence": 0.85, "action_label": action_label, "action_key": action_key}
            if action_key in {"full_avoid", "neither"}:
                return {"action": "REJECT", "score": 20, "confidence": 0.75, "action_label": action_label, "action_key": action_key}
            return {"action": "WAIT", "score": 55, "confidence": 0.6, "action_label": action_label, "action_key": action_key}

        action = str(gemini_result.get("action", "SELL_TODAY") or "SELL_TODAY").upper()
        confidence = self._normalize_confidence(gemini_result.get("confidence", 0))
        if action not in {"HOLD_OVERNIGHT", "SELL_TODAY"}:
            action = "SELL_TODAY"
        return {
            "action": action,
            "score": 75 if action == "HOLD_OVERNIGHT" else 25,
            "confidence": confidence,
            "action_label": action,
        }

    def _resolve_weights(self, decision_type):
        if decision_type == "gatekeeper":
            return (
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_G_WEIGHT", 0.50) or 0.50),
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_A_WEIGHT", 0.20) or 0.20),
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_C_WEIGHT", 0.30) or 0.30),
            )
        return (
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_G_WEIGHT", 0.45) or 0.45),
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_A_WEIGHT", 0.10) or 0.10),
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_C_WEIGHT", 0.45) or 0.45),
        )

    def _agreement_bucket(self, gemini_action, aggr_action, cons_action):
        actions = {gemini_action, aggr_action, cons_action}
        if len(actions) == 1:
            return "all_agree"
        if len(actions) == 3:
            return "all_conflict"
        if gemini_action == aggr_action and gemini_action != cons_action:
            return "gemini_vs_cons_conflict"
        if gemini_action == cons_action and gemini_action != aggr_action:
            return "aggr_vs_pair_conflict"
        if aggr_action == cons_action and gemini_action != aggr_action:
            return "gemini_vs_openai_conflict"
        return "partial_conflict"

    def _fuse_results(self, decision_type, gemini, aggressive, conservative):
        w_gemini, w_aggr, w_cons = self._resolve_weights(decision_type)
        hard_flags = sorted(flag for flag in conservative.get("risk_flags", []) if flag in self.HARD_RISK_FLAGS)
        cons_veto = bool(conservative.get("veto")) and bool(hard_flags)
        fused_score = (
            float(gemini.get("score", 0)) * w_gemini
            + float(aggressive.get("score", 0)) * w_aggr
            + float(conservative.get("score", 0)) * w_cons
        )
        if cons_veto:
            fused_score = max(0.0, fused_score - 15.0)

        if decision_type == "gatekeeper":
            if cons_veto:
                fused_action = "WAIT"
            elif fused_score >= 70.0:
                fused_action = "ALLOW_ENTRY"
            elif fused_score <= 35.0:
                fused_action = "REJECT"
            else:
                fused_action = "WAIT"
        else:
            if cons_veto:
                fused_action = "SELL_TODAY"
            elif fused_score >= 60.0:
                fused_action = "HOLD_OVERNIGHT"
            else:
                fused_action = "SELL_TODAY"

        agreement_bucket = self._agreement_bucket(
            gemini.get("action", ""),
            aggressive.get("action", ""),
            conservative.get("action", ""),
        )
        if cons_veto and fused_action != gemini.get("action"):
            winner = "conservative_veto"
        elif fused_action == aggressive.get("action") and fused_action != gemini.get("action"):
            winner = "aggressive_promote"
        elif fused_action == gemini.get("action"):
            winner = "gemini_hold"
        else:
            winner = "blended"

        return {
            "fused_action": fused_action,
            "fused_score": int(round(max(0.0, min(100.0, fused_score)))),
            "agreement_bucket": agreement_bucket,
            "winner": winner,
            "cons_veto": cons_veto,
            "hard_flags": hard_flags,
        }

    def _is_enabled_for(self, decision_type):
        if not self.shadow_enabled or not self.shadow_mode:
            return False
        if decision_type == "gatekeeper":
            return bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER", True))
        if decision_type == "overnight":
            return bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_APPLY_OVERNIGHT", True))
        return False

    def _evaluate_shadow(self, decision_type, stock_name, stock_code, strategy, realtime_ctx, gemini_result):
        started_at = time.perf_counter()
        try:
            payload = self._build_shadow_payload(
                decision_type=decision_type,
                stock_name=stock_name,
                stock_code=stock_code,
                strategy=strategy,
                realtime_ctx=realtime_ctx,
            )
            aggressive = self._call_persona(
                decision_type,
                DUAL_PERSONA_AGGRESSIVE_PROMPT,
                payload,
                context_name=f"DUAL-{decision_type.upper()}-A:{stock_name}",
            )
            conservative = self._call_persona(
                decision_type,
                DUAL_PERSONA_CONSERVATIVE_PROMPT,
                payload,
                context_name=f"DUAL-{decision_type.upper()}-C:{stock_name}",
            )
            gemini = self._gemini_baseline(decision_type, gemini_result)
            fused = self._fuse_results(decision_type, gemini, aggressive, conservative)
            return {
                "mode": "shadow",
                "decision_type": decision_type,
                "strategy": str(strategy or "").upper(),
                "gemini_action": gemini.get("action"),
                "gemini_score": gemini.get("score"),
                "gemini_action_label": gemini.get("action_label", ""),
                "aggr_action": aggressive.get("action"),
                "aggr_score": aggressive.get("score"),
                "cons_action": conservative.get("action"),
                "cons_score": conservative.get("score"),
                "cons_veto": fused.get("cons_veto", False),
                "fused_action": fused.get("fused_action"),
                "fused_score": fused.get("fused_score"),
                "winner": fused.get("winner"),
                "agreement_bucket": fused.get("agreement_bucket"),
                "hard_flags": fused.get("hard_flags", []),
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }
        except Exception as e:
            return {
                "mode": "shadow",
                "decision_type": decision_type,
                "strategy": str(strategy or "").upper(),
                "error": str(e),
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }

    def _submit_shadow(self, decision_type, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        if not self._is_enabled_for(decision_type):
            return None
        future = self.shadow_executor.submit(
            self._evaluate_shadow,
            decision_type,
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
        )
        if callback is not None:
            def _emit_result(done_future):
                try:
                    callback(done_future.result())
                except Exception as exc:
                    log_error(f"🚨 [OpenAI 듀얼 페르소나 callback] {decision_type}:{stock_name} 실패: {exc}")
            future.add_done_callback(_emit_result)
        return future

    def submit_gatekeeper_shadow(self, *, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        return self._submit_shadow(
            "gatekeeper",
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
            callback=callback,
        )

    def submit_overnight_shadow(self, *, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        return self._submit_shadow(
            "overnight",
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
            callback=callback,
        )

    def _normalize_shared_prompt_result(self, result):
        if not isinstance(result, dict):
            result = {}
        action = str(result.get("action", "WAIT") or "WAIT").upper().strip()
        if action not in {"BUY", "WAIT", "DROP"}:
            action = "WAIT"
        try:
            score = int(float(result.get("score", 50)))
        except Exception:
            score = 50
        return {
            "action": action,
            "score": max(0, min(100, score)),
            "reason": str(result.get("reason", "") or "").replace("\n", " ").strip()[:160],
        }

    def _evaluate_watching_shared_prompt_shadow(
        self,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        gemini_result,
    ):
        started_at = time.perf_counter()
        try:
            formatted = self._format_market_data(ws_data, recent_ticks, recent_candles)
            result = self._call_openai_safe(
                SCALPING_SYSTEM_PROMPT,
                formatted,
                require_json=True,
                context_name=f"WATCHING-SHARED:{stock_name}",
                model_override=self.fast_model_name,
                temperature_override=0.1,
                schema_name="entry_v1",
                endpoint_name="watching_shared_shadow",
                symbol=stock_code,
            )
            normalized = self._normalize_shared_prompt_result(result)
            gemini_action = str((gemini_result or {}).get("action", "WAIT") or "WAIT").upper()
            gemini_score = int(float((gemini_result or {}).get("score", 50) or 50))
            return {
                "mode": "shadow",
                "strategy": "SCALPING",
                "gemini_action": gemini_action,
                "gemini_score": gemini_score,
                "gpt_action": normalized.get("action", "WAIT"),
                "gpt_score": normalized.get("score", 50),
                "gpt_reason": normalized.get("reason", ""),
                "action_diverged": gemini_action != normalized.get("action", "WAIT"),
                "score_gap": int(normalized.get("score", 50)) - gemini_score,
                "gpt_model": self.fast_model_name,
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }
        except Exception as e:
            return {
                "mode": "shadow",
                "strategy": "SCALPING",
                "error": str(e),
                "gpt_model": self.fast_model_name,
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }

    def submit_watching_shared_prompt_shadow(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        gemini_result,
        callback=None,
    ):
        future = self.shadow_executor.submit(
            self._evaluate_watching_shared_prompt_shadow,
            stock_name,
            stock_code,
            ws_data,
            recent_ticks,
            recent_candles,
            gemini_result,
        )
        if callback is not None:
            def _emit_result(done_future):
                try:
                    callback(done_future.result())
                except Exception as exc:
                    log_error(f"🚨 [WATCHING shared prompt shadow callback] {stock_name}({stock_code}) 실패: {exc}")
            future.add_done_callback(_emit_result)
        return future

    def submit_watching_score_projection(
        self,
        *,
        stock_name,
        stock_code,
        ws_data,
        recent_ticks,
        recent_candles,
        record_id=None,
        callback=None,
    ):
        """Run the exact WATCHING contract on the isolated shadow engine."""
        future = self.shadow_executor.submit(
            self.analyze_target,
            stock_name,
            ws_data,
            recent_ticks,
            recent_candles,
            prompt_profile="watching",
            metadata_extra={
                "record_id": record_id,
                "stock_code": stock_code,
                "source_event_stage": "ai_watching_score_projection",
                "decision_authority": "report_only_no_runtime_effect",
            },
        )
        if callback is not None:
            def _emit_result(done_future):
                try:
                    callback(done_future.result())
                except Exception as exc:
                    log_error(f"[WATCHING score projection callback] {stock_name}({stock_code}) failed: {exc}")
            future.add_done_callback(_emit_result)
        return future
