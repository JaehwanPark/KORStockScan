from __future__ import annotations

import json
import os
import queue
import random
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.bedrock_nova_provider import (
    BedrockNovaModelProfile,
    BedrockNovaProvider,
    estimate_cost_usd,
    normalize_action_score,
)
from src.utils.logger import log_error


DECISION_AUTHORITY = "shadow_observation_only"


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except Exception:
        return None


@dataclass(frozen=True)
class NovaShadowJob:
    prompt: str
    user_input: str
    openai_payload: dict[str, Any]
    transport_meta: dict[str, Any]
    request_meta: dict[str, Any]


class BedrockNovaShadowManager:
    def __init__(
        self,
        *,
        enabled: bool = False,
        report_dir: Path,
        event_type: str,
        target_model_name: str,
        target_model_names: set[str] | None = None,
        profile: BedrockNovaModelProfile,
        openai_input_usd_per_1m: float,
        openai_output_usd_per_1m: float,
        provider: BedrockNovaProvider | None = None,
        workers: int = 1,
        queue_max: int = 200,
        sample_rate: float = 1.0,
        baseline_provider_label: str = "openai",
        candidate_provider_label: str = "nova",
    ):
        self.is_enabled = bool(enabled)
        self.report_dir = report_dir
        self.event_type = str(event_type)
        self.target_model_name = str(target_model_name)
        configured_targets = {str(item or "").strip() for item in (target_model_names or set()) if str(item or "").strip()}
        self.target_model_names = configured_targets or {self.target_model_name}
        self.profile = profile
        self.openai_input_usd_per_1m = float(openai_input_usd_per_1m)
        self.openai_output_usd_per_1m = float(openai_output_usd_per_1m)
        self.provider = provider or BedrockNovaProvider()
        self.workers = max(1, int(workers or 1))
        self.queue_max = max(1, int(queue_max or 200))
        self.sample_rate = max(0.0, min(1.0, float(sample_rate if sample_rate is not None else 1.0)))
        self.baseline_provider_label = str(baseline_provider_label or "openai")
        self.candidate_provider_label = str(candidate_provider_label or "nova")
        self._queue: queue.Queue[NovaShadowJob] | None = None
        self._threads: list[threading.Thread] = []
        self._lock = threading.Lock()

    def should_shadow(self, *, model_name: str, require_json: bool) -> bool:
        return bool(self.is_enabled and require_json and str(model_name or "") in self.target_model_names)

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
                thread = threading.Thread(target=self._worker_loop, name=f"{self.event_type}-{idx}", daemon=True)
                thread.start()
                self._threads.append(thread)

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
        result = self.provider.converse(prompt=job.prompt, user_input=job.user_input, profile=self.profile)
        nova_action, nova_score = normalize_action_score(result.payload)
        openai_action, openai_score = normalize_action_score(job.openai_payload)
        row = self._base_row(job.request_meta, job.transport_meta, job.openai_payload)
        row.update(
            {
                "model_id": result.model_id,
                "region_name": result.region_name,
                "nova_action": nova_action,
                "nova_score": nova_score,
                "baseline_action": openai_action,
                "baseline_score": openai_score,
                "candidate_action": nova_action,
                "candidate_score": nova_score,
                "action_match": bool(openai_action and nova_action and openai_action == nova_action),
                "score_delta": (nova_score - openai_score) if nova_score is not None and openai_score is not None else None,
                "nova_latency_ms": result.latency_ms,
                "openai_input_tokens": _safe_int(job.transport_meta.get("openai_input_tokens")),
                "openai_output_tokens": _safe_int(job.transport_meta.get("openai_output_tokens")),
                "nova_input_tokens": result.input_tokens,
                "nova_output_tokens": result.output_tokens,
                "nova_prompt_cache_enabled": self.profile.prompt_cache_enabled,
                "nova_cache_read_input_tokens": result.cache_read_input_tokens,
                "nova_cache_write_input_tokens": result.cache_write_input_tokens,
                "nova_total_input_tokens": result.total_input_tokens,
                "nova_cache_pricing_note": "inputTokens excludes cache read/write tokens when Bedrock prompt caching is enabled",
                "estimated_openai_cost_usd": estimate_cost_usd(
                    job.transport_meta.get("openai_input_tokens"),
                    job.transport_meta.get("openai_output_tokens"),
                    input_usd_per_1m=self.openai_input_usd_per_1m,
                    output_usd_per_1m=self.openai_output_usd_per_1m,
                ),
                "estimated_nova_cost_usd": result.estimated_cost_usd,
                "parse_ok": result.parse_ok,
                "error_type": result.parse_error or "",
                "raw_text_sample": str(result.raw_text or "")[:500],
            }
        )
        if self.event_type == "bedrock_nova_lite_v2_shadow":
            row.update(
                {
                    "target_run_date": str(job.request_meta.get("target_run_date") or ""),
                    "target_endpoint_scope": "tier2_gpt_5_4_mini",
                    "candidate_model_family": "lite_v2",
                    "baseline_bedrock_model_id": str(job.request_meta.get("baseline_bedrock_model_id") or ""),
                    "candidate_bedrock_model_id": result.model_id,
                    "v1_v2_action_match": bool(openai_action and nova_action and openai_action == nova_action),
                    "v1_v2_score_delta": (nova_score - openai_score) if nova_score is not None and openai_score is not None else None,
                    "v2_parse_ok": result.parse_ok,
                    "v2_latency_ms": result.latency_ms,
                    "v2_estimated_cost_usd": result.estimated_cost_usd,
                }
            )
        return row

    def _base_row(self, request_meta: dict[str, Any], transport_meta: dict[str, Any], openai_payload: dict[str, Any]) -> dict[str, Any]:
        openai_action, openai_score = normalize_action_score(openai_payload)
        return {
            "schema_version": 1,
            "event_type": self.event_type,
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
            "baseline_provider": self.baseline_provider_label,
            "candidate_provider": self.candidate_provider_label,
            "baseline_model_id": str(request_meta.get("baseline_model_id") or request_meta.get("baseline_bedrock_model_id") or ""),
            "candidate_model_family": self.profile.family,
            "baseline_action": openai_action,
            "baseline_score": openai_score,
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
                "model_id": self.profile.model_id,
                "region_name": self.profile.region_name,
                "nova_action": "",
                "nova_score": None,
                "action_match": False,
                "score_delta": None,
                "nova_latency_ms": None,
                "openai_input_tokens": _safe_int(transport_meta.get("openai_input_tokens")),
                "openai_output_tokens": _safe_int(transport_meta.get("openai_output_tokens")),
                "nova_input_tokens": None,
                "nova_output_tokens": None,
                "nova_prompt_cache_enabled": self.profile.prompt_cache_enabled,
                "nova_cache_read_input_tokens": None,
                "nova_cache_write_input_tokens": None,
                "nova_total_input_tokens": None,
                "nova_cache_pricing_note": "inputTokens excludes cache read/write tokens when Bedrock prompt caching is enabled",
                "estimated_openai_cost_usd": estimate_cost_usd(
                    transport_meta.get("openai_input_tokens"),
                    transport_meta.get("openai_output_tokens"),
                    input_usd_per_1m=self.openai_input_usd_per_1m,
                    output_usd_per_1m=self.openai_output_usd_per_1m,
                ),
                "estimated_nova_cost_usd": 0.0,
                "parse_ok": False,
                "error_type": error_type,
                "error_message": error_message,
            }
        )
        return row

    def _jsonl_path(self) -> Path:
        return self.report_dir / f"{self.event_type}_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def _write_row(self, row: dict[str, Any]) -> None:
        try:
            self.report_dir.mkdir(parents=True, exist_ok=True)
            with self._jsonl_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception as exc:
            log_error(f"[{self.event_type}] write failed: {exc}")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except Exception:
        return default
