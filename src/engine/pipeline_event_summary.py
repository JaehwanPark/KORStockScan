from __future__ import annotations

import hashlib
import gzip
import json
import math
import time
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto


ReasonLabeler = Callable[[str, dict[str, str]], str]
IgnorePredicate = Callable[[dict[str, Any]], bool]

SUMMARY_SCHEMA_VERSION = 2
PRODUCER_SUMMARY_SCHEMA_VERSION = 1
SUMMARY_STAGES = frozenset(
    {
        "strength_momentum_observed",
        "blocked_strength_momentum",
        "blocked_swing_score_vpw",
        "blocked_overbought",
        "blocked_swing_gap",
    }
)

NUMERIC_FIELD_LIMIT = 64
SAMPLE_HASH_LIMIT = 2
SAMPLE_FIRST_LIMIT = 2
SAMPLE_LAST_LIMIT = 2
SAMPLE_FIELD_LIMIT = 24
SAMPLE_FIELD_VALUE_MAX_CHARS = 160
SAMPLE_FIELD_PRIORITY = (
    "reason",
    "block_reason",
    "blocked_reason",
    "decision",
    "action",
    "strategy",
    "selected_strategy",
    "entry_strategy",
    "origin_strategy",
    "trade_type",
    "market",
    "market_type",
    "actual_order_submitted",
    "broker_order_forbidden",
    "broker_order_submitted",
    "score",
    "ai_score",
    "current_ai_score",
    "buy_ratio",
    "exec_buy_ratio",
    "window_buy_value",
    "latest_strength",
    "strength",
    "gap_pct",
    "distance_pct",
)
NUMERIC_FIELD_EXCLUDED_NAMES = {
    "id",
    "record_id",
    "stock_code",
    "code",
    "종목코드",
}
KEY_FIELD_CANDIDATES = {
    "strategy": ("strategy", "selected_strategy", "entry_strategy", "origin_strategy", "trade_type"),
    "market": ("market", "market_type", "market_name", "universe", "market_code"),
}
ACTUAL_ORDER_FIELD_CANDIDATES = (
    "actual_order_submitted",
    "broker_order_submitted",
    "order_submitted",
)


@dataclass(frozen=True)
class SummaryEvent:
    emitted_at: datetime
    pipeline: str
    stage: str
    stock_name: str
    stock_code: str
    record_id: str
    fields: dict[str, str]
    reason_label: str
    strategy: str
    market: str
    actual_order_submitted: str
    raw_offset_start: int
    raw_offset_end: int


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _summary_paths(summary_dir: Path, target_date: str) -> tuple[Path, Path]:
    return (
        summary_dir / f"pipeline_event_summary_{target_date}.jsonl",
        summary_dir / f"pipeline_event_summary_manifest_{target_date}.json",
    )


def producer_summary_paths(summary_dir: Path, target_date: str) -> tuple[Path, Path]:
    return (
        summary_dir / f"pipeline_event_producer_summary_{target_date}.jsonl",
        summary_dir / f"pipeline_event_producer_summary_manifest_{target_date}.json",
    )


def _parse_iso_datetime(value: str) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _first_field(fields: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = _safe_str(fields.get(name))
        if value:
            return value
    return ""


def field_first(fields: dict[str, str], names: tuple[str, ...]) -> str:
    return _first_field(fields, names)


def default_reason_label(stage: str, fields: dict[str, str]) -> str:
    if stage == "blocked_ai_score":
        score = _first_field(fields, ("score", "ai_score", "current_ai_score"))
        reason = _first_field(fields, ("reason", "block_reason", "blocked_reason", "decision"))
        if "ai_score_50_buy_hold_override" in reason or fields.get("ai_score_50_buy_hold_override") == "True":
            return "blocked_ai_score:ai_score_50_buy_hold_override"
        if score:
            return f"blocked_ai_score:score_{score}"
    if stage == "latency_block":
        reason = _first_field(fields, ("reason", "latency_danger_reasons", "decision"))
        return f"latency_block:{reason or '-'}"
    if stage in {
        "pre_submit_price_guard_block",
        "entry_ai_price_canary_skip_order",
        "entry_ai_price_canary_fallback",
        "scale_in_price_guard_block",
    }:
        reason = _first_field(fields, ("reason", "block_reason", "resolution_reason", "action"))
        return f"{stage}:{reason or '-'}"
    if stage == "wait65_79_ev_candidate":
        score = _first_field(fields, ("ai_score", "score", "current_ai_score"))
        return f"wait65_79_ev_candidate:score_{score or '-'}"
    reason = _first_field(fields, ("reason", "block_reason", "decision", "action"))
    return f"{stage}:{reason or '-'}"


def _actual_order_text(payload: dict[str, Any], fields: dict[str, str]) -> str:
    for name in ACTUAL_ORDER_FIELD_CANDIDATES:
        if name in fields:
            return _boolish_text(fields.get(name))
        if name in payload:
            return _boolish_text(payload.get(name))
    return "unknown"


def _boolish_text(value: Any) -> str:
    text = _safe_str(value)
    lowered = text.lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return "true"
    if lowered in {"0", "false", "f", "no", "n"}:
        return "false"
    return text or "unknown"


def truthy(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "t", "yes", "y", "on"}


def _try_float(value: str) -> float | None:
    text = _safe_str(value)
    if not text:
        return None
    lowered = text.lower()
    if lowered in {"true", "false", "none", "null", "nan", "inf", "-inf"}:
        return None
    cleaned = text.replace(",", "")
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    try:
        parsed = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _is_numeric_field_name(name: str) -> bool:
    lowered = name.lower()
    if lowered in NUMERIC_FIELD_EXCLUDED_NAMES:
        return False
    if lowered.endswith("_id") or lowered.endswith("_code") or lowered.endswith("_at"):
        return False
    if "time" in lowered or "date" in lowered:
        return False
    return True


def _compact_sample(event: SummaryEvent) -> dict[str, Any]:
    return {
        "emitted_at": event.emitted_at.isoformat(timespec="seconds"),
        "pipeline": event.pipeline,
        "stage": event.stage,
        "stock_name": event.stock_name,
        "stock_code": event.stock_code,
        "record_id": event.record_id,
        "raw_offset": event.raw_offset_start,
        "fields": _compact_sample_fields(event.fields),
    }


def _compact_sample_fields(fields: dict[str, str]) -> dict[str, str]:
    compact: dict[str, str] = {}
    for key in SAMPLE_FIELD_PRIORITY:
        if key in fields:
            compact[key] = _truncate_field_value(fields[key])
        if len(compact) >= SAMPLE_FIELD_LIMIT:
            return compact
    for key in sorted(fields):
        if key in compact:
            continue
        compact[key] = _truncate_field_value(fields[key])
        if len(compact) >= SAMPLE_FIELD_LIMIT:
            break
    return compact


def _truncate_field_value(value: str) -> str:
    text = _safe_str(value)
    if len(text) <= SAMPLE_FIELD_VALUE_MAX_CHARS:
        return text
    return text[:SAMPLE_FIELD_VALUE_MAX_CHARS] + "...<truncated>"


class _SummaryAggregate:
    def __init__(
        self,
        *,
        bucket_start: datetime,
        bucket_end: datetime,
        pipeline: str,
        stage: str,
        stock_code: str,
        stock_name: str,
        strategy: str,
        market: str,
        reason_label: str,
        actual_order_submitted: str,
    ) -> None:
        self.bucket_start = bucket_start
        self.bucket_end = bucket_end
        self.pipeline = pipeline
        self.stage = stage
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.strategy = strategy
        self.market = market
        self.reason_label = reason_label
        self.actual_order_submitted = actual_order_submitted
        self.event_count = 0
        self.first_seen: datetime | None = None
        self.last_seen: datetime | None = None
        self.first_record_id = ""
        self.last_record_id = ""
        self.first_raw_offset: int | None = None
        self.last_raw_offset: int | None = None
        self.field_presence_counts: Counter[str] = Counter()
        self.numeric_stats: dict[str, dict[str, float | int]] = {}
        self.second_counts: Counter[str] = Counter()
        self.first_samples: list[dict[str, Any]] = []
        self.last_samples: deque[dict[str, Any]] = deque(maxlen=SAMPLE_LAST_LIMIT)
        self.hash_samples: list[tuple[int, dict[str, Any]]] = []

    def add(self, event: SummaryEvent) -> None:
        self.event_count += 1
        if self.first_seen is None:
            self.first_seen = event.emitted_at
            self.first_record_id = event.record_id
            self.first_raw_offset = event.raw_offset_start
        self.last_seen = event.emitted_at
        self.last_record_id = event.record_id
        self.last_raw_offset = event.raw_offset_end
        self.second_counts[event.emitted_at.replace(microsecond=0).isoformat(timespec="seconds")] += 1
        sample = _compact_sample(event)
        if len(self.first_samples) < SAMPLE_FIRST_LIMIT:
            self.first_samples.append(sample)
        self.last_samples.append(sample)
        sample_hash = int(
            hashlib.sha256(
                f"{event.stage}|{event.record_id}|{event.raw_offset_start}|{event.emitted_at.isoformat()}".encode(
                    "utf-8"
                )
            ).hexdigest(),
            16,
        )
        self.hash_samples.append((sample_hash, sample))
        self.hash_samples.sort(key=lambda item: item[0])
        if len(self.hash_samples) > SAMPLE_HASH_LIMIT:
            self.hash_samples = self.hash_samples[:SAMPLE_HASH_LIMIT]

        for key, value in event.fields.items():
            self.field_presence_counts[key] += 1
            if not _is_numeric_field_name(key):
                continue
            numeric = _try_float(value)
            if numeric is None:
                continue
            if key not in self.numeric_stats:
                if len(self.numeric_stats) >= NUMERIC_FIELD_LIMIT:
                    continue
                self.numeric_stats[key] = {
                    "count": 0,
                    "min": numeric,
                    "max": numeric,
                    "sum": 0.0,
                }
            stats = self.numeric_stats[key]
            stats["count"] = int(stats["count"]) + 1
            stats["min"] = min(float(stats["min"]), numeric)
            stats["max"] = max(float(stats["max"]), numeric)
            stats["sum"] = float(stats["sum"]) + numeric

    def _sample_events(self) -> list[dict[str, Any]]:
        by_offset: dict[int, dict[str, Any]] = {}
        ordered_samples = (
            self.first_samples
            + [sample for _, sample in self.hash_samples]
            + list(self.last_samples)
        )
        for sample in ordered_samples:
            offset = int(sample.get("raw_offset") or 0)
            by_offset.setdefault(offset, sample)
        return [by_offset[offset] for offset in sorted(by_offset)]

    def to_row(self, *, target_date: str) -> dict[str, Any]:
        numeric_stats = {}
        for key, stats in sorted(self.numeric_stats.items()):
            count = int(stats["count"])
            numeric_stats[key] = {
                "count": count,
                "min": float(stats["min"]),
                "max": float(stats["max"]),
                "sum": float(stats["sum"]),
                "avg": float(stats["sum"]) / count if count else 0.0,
            }
        samples = self._sample_events()
        return {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "target_date": target_date,
            "bucket_start": self.bucket_start.isoformat(timespec="seconds"),
            "bucket_end": self.bucket_end.isoformat(timespec="seconds"),
            "pipeline": self.pipeline,
            "stage": self.stage,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "strategy": self.strategy,
            "market": self.market,
            "reason_label": self.reason_label,
            "actual_order_submitted": self.actual_order_submitted,
            "event_count": self.event_count,
            "first_seen": self.first_seen.isoformat(timespec="seconds") if self.first_seen else None,
            "last_seen": self.last_seen.isoformat(timespec="seconds") if self.last_seen else None,
            "first_record_id": self.first_record_id,
            "last_record_id": self.last_record_id,
            "field_presence_counts": dict(sorted(self.field_presence_counts.items())),
            "numeric_stats": numeric_stats,
            "second_counts": dict(sorted(self.second_counts.items())),
            "first_raw_offset": self.first_raw_offset,
            "last_raw_offset": self.last_raw_offset,
            "sample_raw_offsets": [int(sample.get("raw_offset") or 0) for sample in samples],
            "sample_events": samples,
            "metric_role": "ops_volume_diagnostic",
            "decision_authority": "diagnostic_aggregation",
            "runtime_effect": False,
            "forbidden_uses": [
                "runtime_threshold_or_order_guard_mutation",
                "real_execution_quality_inference",
                "primary_ev_decision",
            ],
        }


def is_summary_target_stage(stage: str) -> bool:
    return _safe_str(stage) in SUMMARY_STAGES


def payload_has_lossless_authority(payload: dict[str, Any], threshold_family: str | None = None) -> bool:
    stage = _safe_str(payload.get("stage")).lower()
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
    if threshold_family:
        return True
    if any(
        token in stage
        for token in (
            "order_submitted",
            "order_bundle_submitted",
            "order_sent",
            "order_cancel",
            "order_failed",
            "order_rejected",
            "sell_order",
            "buy_order",
            "fill",
            "filled",
            "exit",
            "hard_stop",
            "protect",
            "emergency",
            "safety",
        )
    ):
        return True
    for key in ("actual_order_submitted", "broker_order_submitted", "order_submitted"):
        if truthy(payload.get(key)) or truthy(fields.get(key)):
            return True
    for key in fields:
        lowered = str(key).lower()
        if "source_quality" in lowered or "provenance" in lowered:
            return True
    return False


def _summary_event_from_payload(
    payload: dict[str, Any],
    *,
    reason_labeler: ReasonLabeler,
    ignore_payload: IgnorePredicate | None,
    line_start: int,
    line_end: int,
) -> SummaryEvent | None:
    if ignore_payload is not None and ignore_payload(payload):
        return None
    if _safe_str(payload.get("event_type")) != "pipeline_event":
        return None
    stage = _safe_str(payload.get("stage"))
    if stage not in SUMMARY_STAGES:
        return None
    emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
    if emitted_at is None:
        return None
    raw_fields = payload.get("fields") or {}
    fields = {str(k): _safe_str(v) for k, v in raw_fields.items()} if isinstance(raw_fields, dict) else {}
    record_id = payload.get("record_id")
    if record_id in (None, "", 0):
        record_id = fields.get("id") or ""
    strategy = _first_field(fields, KEY_FIELD_CANDIDATES["strategy"])
    market = _first_field(fields, KEY_FIELD_CANDIDATES["market"])
    return SummaryEvent(
        emitted_at=emitted_at,
        pipeline=_safe_str(payload.get("pipeline")),
        stage=stage,
        stock_name=_safe_str(payload.get("stock_name")),
        stock_code=_safe_str(payload.get("stock_code"))[:6],
        record_id=_safe_str(record_id),
        fields=fields,
        reason_label=reason_labeler(stage, fields),
        strategy=strategy,
        market=market,
        actual_order_submitted=_actual_order_text(payload, fields),
        raw_offset_start=line_start,
        raw_offset_end=line_end,
    )


def summary_event_from_payload(
    payload: dict[str, Any],
    *,
    reason_labeler: ReasonLabeler = default_reason_label,
    ignore_payload: IgnorePredicate | None = None,
    line_start: int = 0,
    line_end: int = 0,
) -> SummaryEvent | None:
    return _summary_event_from_payload(
        payload,
        reason_labeler=reason_labeler,
        ignore_payload=ignore_payload,
        line_start=line_start,
        line_end=line_end,
    )


def _aggregate_key(event: SummaryEvent) -> tuple[str, ...]:
    bucket_start = event.emitted_at.replace(second=0, microsecond=0)
    return (
        bucket_start.isoformat(timespec="seconds"),
        event.pipeline,
        event.stage,
        event.stock_code,
        event.stock_name,
        event.strategy,
        event.market,
        event.reason_label,
        event.actual_order_submitted,
    )


def _new_aggregate(event: SummaryEvent) -> _SummaryAggregate:
    bucket_start = event.emitted_at.replace(second=0, microsecond=0)
    bucket_end = bucket_start + timedelta(minutes=1)
    return _SummaryAggregate(
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        pipeline=event.pipeline,
        stage=event.stage,
        stock_code=event.stock_code,
        stock_name=event.stock_name,
        strategy=event.strategy,
        market=event.market,
        reason_label=event.reason_label,
        actual_order_submitted=event.actual_order_submitted,
    )


def _load_summary_rows(summary_path: Path, *, include_samples: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary_path = existing_or_gzip_path(summary_path)
    if not summary_path.exists():
        return rows
    with open_text_auto(summary_path, errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                if not include_samples:
                    rows.append(_slim_summary_row(payload))
                else:
                    rows.append(payload)
    return rows


def load_summary_rows(path: Path, *, include_samples: bool = True) -> list[dict[str, Any]]:
    return _load_summary_rows(path, include_samples=include_samples)


def _slim_summary_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "target_date": payload.get("target_date"),
        "bucket_start": payload.get("bucket_start"),
        "bucket_end": payload.get("bucket_end"),
        "pipeline": payload.get("pipeline"),
        "stage": payload.get("stage"),
        "stock_code": payload.get("stock_code"),
        "stock_name": payload.get("stock_name"),
        "strategy": payload.get("strategy"),
        "market": payload.get("market"),
        "reason_label": payload.get("reason_label"),
        "actual_order_submitted": payload.get("actual_order_submitted"),
        "event_count": payload.get("event_count"),
        "first_seen": payload.get("first_seen"),
        "last_seen": payload.get("last_seen"),
        "second_counts": payload.get("second_counts") if isinstance(payload.get("second_counts"), dict) else {},
        "decision_authority": payload.get("decision_authority"),
        "runtime_effect": payload.get("runtime_effect"),
    }


def update_and_load_pipeline_event_summaries(
    *,
    raw_path: Path,
    summary_dir: Path,
    target_date: str,
    reason_labeler: ReasonLabeler,
    ignore_payload: IgnorePredicate | None = None,
    include_samples: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_path = existing_or_gzip_path(raw_path)
    if not raw_path.exists():
        return [], {
            "enabled": True,
            "status": "raw_missing",
            "raw_path": str(raw_path),
            "summary_event_count": 0,
        }

    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path, manifest_path = _summary_paths(summary_dir, target_date)
    stat = raw_path.stat()
    is_gzip_raw = raw_path.suffix == ".gz"
    raw_inode = getattr(stat, "st_ino", None)
    manifest = _read_json(manifest_path)
    raw_offset = int(manifest.get("raw_offset") or 0)
    raw_size = max(int(stat.st_size), raw_offset) if is_gzip_raw else int(stat.st_size)
    stale_summary = (
        int(manifest.get("schema_version") or 0) != SUMMARY_SCHEMA_VERSION
        or str(manifest.get("raw_path") or "") != str(raw_path)
        or int(manifest.get("raw_inode") or -1) != int(raw_inode or -1)
        or raw_offset > raw_size
        or not summary_path.exists()
    )
    if stale_summary:
        summary_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raw_offset = 0
    summary_path.touch(exist_ok=True)

    groups: dict[tuple[str, ...], _SummaryAggregate] = {}
    appended_raw_lines = 0
    appended_source_events = 0
    decode_errors = 0
    last_good_offset = raw_offset
    raw_opener = gzip.open if is_gzip_raw else open
    with raw_opener(raw_path, "rb") as raw_handle:
        raw_handle.seek(raw_offset)
        while True:
            line_start = raw_handle.tell()
            raw_bytes = raw_handle.readline()
            if not raw_bytes:
                break
            appended_raw_lines += 1
            if not raw_bytes.endswith(b"\n"):
                break
            line_end = raw_handle.tell()
            raw_line = raw_bytes.decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                decode_errors += 1
                last_good_offset = line_end
                continue
            if isinstance(payload, dict):
                event = _summary_event_from_payload(
                    payload,
                    reason_labeler=reason_labeler,
                    ignore_payload=ignore_payload,
                    line_start=line_start,
                    line_end=line_end,
                )
                if event is not None:
                    key = _aggregate_key(event)
                    aggregate = groups.setdefault(key, _new_aggregate(event))
                    aggregate.add(event)
                    appended_source_events += 1
            last_good_offset = line_end
            if last_good_offset <= line_start:
                break

    appended_summary_rows = 0
    if groups:
        with summary_path.open("a", encoding="utf-8") as summary_handle:
            for key in sorted(groups):
                row = groups[key].to_row(target_date=target_date)
                summary_handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                appended_summary_rows += 1

    rows = _load_summary_rows(summary_path, include_samples=include_samples)
    final_stat_size = int(raw_path.stat().st_size) if raw_path.exists() else raw_size
    final_raw_size = max(final_stat_size, last_good_offset) if is_gzip_raw else final_stat_size
    new_manifest = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "raw_path": str(raw_path),
        "raw_inode": raw_inode,
        "raw_offset": last_good_offset,
        "raw_size": final_raw_size,
        "summary_path": str(summary_path),
        "summary_row_count": len(rows),
        "appended_raw_lines": appended_raw_lines,
        "appended_source_events": appended_source_events,
        "appended_summary_rows": appended_summary_rows,
        "decode_errors": decode_errors,
        "rebuilt": stale_summary,
        "complete_through_raw_offset": last_good_offset,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "summary_stages": sorted(SUMMARY_STAGES),
        "metric_role": "ops_volume_diagnostic",
        "decision_authority": "diagnostic_aggregation",
        "runtime_effect": False,
        "raw_suppression_enabled": False,
    }
    _write_json(manifest_path, new_manifest)
    return rows, {
        "enabled": True,
        "status": "ok",
        **new_manifest,
    }


class ProducerSummaryCompactor:
    def __init__(
        self,
        *,
        summary_dir: Path,
        mode: str = "off",
        flush_sec: int = 5,
        sample_per_bucket: int = 6,
        reason_labeler: ReasonLabeler = default_reason_label,
    ) -> None:
        self.summary_dir = summary_dir
        self.mode = mode if mode in {"off", "shadow", "suppress"} else "off"
        self.flush_sec = max(0, int(flush_sec or 0))
        self.sample_per_bucket = max(1, int(sample_per_bucket or 6))
        self.reason_labeler = reason_labeler
        self._groups: dict[tuple[str, ...], _SummaryAggregate] = {}
        self._last_flush_monotonic = time.monotonic()
        self._sequence = 0
        self._event_count = 0
        self._suppressed_count = 0
        self._lossless_preserved_count = 0

    @property
    def enabled(self) -> bool:
        return self.mode in {"shadow", "suppress"}

    def submit(self, payload: dict[str, Any], *, threshold_family: str | None = None) -> dict[str, Any]:
        if not self.enabled or _safe_str(payload.get("event_type")) != "pipeline_event":
            return {"mode": self.mode, "summary_recorded": False, "suppress_raw": False}

        stage = _safe_str(payload.get("stage"))
        lossless = payload_has_lossless_authority(payload, threshold_family=threshold_family)
        if stage not in SUMMARY_STAGES:
            return {"mode": self.mode, "summary_recorded": False, "suppress_raw": False, "lossless": True}

        self._sequence += 1
        event = summary_event_from_payload(
            payload,
            reason_labeler=self.reason_labeler,
            line_start=self._sequence,
            line_end=self._sequence,
        )
        if event is None:
            return {"mode": self.mode, "summary_recorded": False, "suppress_raw": False, "lossless": lossless}

        key = _aggregate_key(event)
        self._groups.setdefault(key, _new_aggregate(event)).add(event)
        self._event_count += 1
        suppress_raw = bool(self.mode == "suppress" and not lossless)
        if suppress_raw:
            self._suppressed_count += 1
        if lossless:
            self._lossless_preserved_count += 1
        if self.flush_sec == 0 or (time.monotonic() - self._last_flush_monotonic) >= self.flush_sec:
            self.flush(target_date=_safe_str(payload.get("emitted_date")))
        return {
            "mode": self.mode,
            "summary_recorded": True,
            "suppress_raw": suppress_raw,
            "lossless": lossless,
        }

    def flush(self, *, target_date: str | None = None) -> dict[str, Any]:
        if not self.enabled or not self._groups:
            return {
                "enabled": self.enabled,
                "mode": self.mode,
                "status": "no_pending_rows" if self.enabled else "disabled",
                "flushed_rows": 0,
            }
        safe_date = _safe_str(target_date)
        if not safe_date:
            latest = max(
                aggregate.last_seen for aggregate in self._groups.values() if aggregate.last_seen is not None
            )
            safe_date = latest.strftime("%Y-%m-%d")
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path, manifest_path = producer_summary_paths(self.summary_dir, safe_date)
        summary_path.touch(exist_ok=True)
        flushed_rows = 0
        flushed_events = 0
        with summary_path.open("a", encoding="utf-8") as handle:
            for key in sorted(self._groups):
                row = self._groups[key].to_row(target_date=safe_date)
                row["schema_version"] = PRODUCER_SUMMARY_SCHEMA_VERSION
                row["producer_mode"] = self.mode
                row["source"] = "pipeline_event_logger"
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                flushed_rows += 1
                flushed_events += int(row.get("event_count") or 0)
        existing = _read_json(manifest_path)
        previous_rows = int(existing.get("summary_row_count") or 0)
        previous_events = int(existing.get("summary_event_count") or 0)
        manifest = {
            "schema_version": PRODUCER_SUMMARY_SCHEMA_VERSION,
            "summary_path": str(summary_path),
            "summary_row_count": previous_rows + flushed_rows,
            "summary_event_count": previous_events + flushed_events,
            "last_flush_rows": flushed_rows,
            "last_flush_events": flushed_events,
            "mode": self.mode,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "summary_stages": sorted(SUMMARY_STAGES),
            "sample_per_bucket": self.sample_per_bucket,
            "suppressed_count": int(existing.get("suppressed_count") or 0) + self._suppressed_count,
            "lossless_preserved_count": int(existing.get("lossless_preserved_count") or 0)
            + self._lossless_preserved_count,
            "metric_role": "ops_volume_diagnostic",
            "decision_authority": "diagnostic_aggregation",
            "runtime_effect": False,
            "raw_suppression_enabled": self.mode == "suppress",
        }
        _write_json(manifest_path, manifest)
        self._groups.clear()
        self._suppressed_count = 0
        self._lossless_preserved_count = 0
        self._last_flush_monotonic = time.monotonic()
        return {"enabled": True, "mode": self.mode, "status": "ok", **manifest}
