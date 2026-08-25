"""Append-only AI decision trace and pending outcome-label instrumentation.

This module has no trading authority.  Failures are intentionally isolated from the
provider and runtime decision paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import jsonl_artifact_generation_lock
from src.utils.logger import log_error

TRACE_SCHEMA = "ai_decision_trace_v1"
PAYLOAD_SCHEMA = "ai_decision_payload_v1"
REQUEST_SCHEMA = "ai_decision_request_provenance_v1"
PROMPT_SCHEMA = "ai_decision_prompt_v1"
OUTCOME_SCHEMA = "ai_decision_outcome_label_v1"
CONTEXT_CANDIDATE_SCHEMA = "ai_canonical_context_candidate_v1"
OUTCOME_HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)

OBSERVATION_CONTRACT = {
    "metric_role": "ai_decision_quality_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "clean_baseline_exact_provenance_stage_venue_separated",
    "sample_floor": "row_level_not_applicable_aggregation_floor_required",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_snapshot_and_mature_forward_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "standalone_live_prompt_promotion|provider_change|threshold_relaxation|"
        "order_or_quantity_change|broker_guard_bypass|hard_safety_bypass|"
        "counterfactual_realized_pnl_merge"
    ),
}
STORAGE_SECURITY_CONTRACT = {
    "storage_security_policy": "ai_trace_payload_security_v2",
    "sensitive_value_policy": "key_and_embedded_credential_redaction_v2",
    "storage_file_mode": "0600",
    "storage_directory_mode": "0700",
    "raw_secret_storage": False,
}
CONTEXT_CANDIDATE_OBSERVATION_CONTRACT = {
    "metric_role": "ai_input_source_quality",
    "decision_authority": "forensics_only_no_runtime_change",
    "window_policy": "same_natural_decision_context_explicit_provider_call",
    "sample_floor": "one_valid_row_per_symbol_venue_session_endpoint",
    "primary_decision_metric": "required_source_field_match_status",
    "source_quality_gate": "fresh_same_basis_conflict_free",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "runtime_decision|order_submit|provider_route_change|threshold_change|"
        "price_or_quantity_change|bot_restart|live_promotion_without_review"
    ),
}

_WRITE_LOCK = threading.RLock()
_SEEN_PAYLOAD_HASHES: dict[str, set[str]] = {}
_SEEN_PROMPT_HASHES: dict[str, set[str]] = {}
_SEEN_TRACE_IDS: dict[str, set[str]] = {}
_SEEN_REQUEST_IDS: dict[str, set[str]] = {}
_SEEN_OUTCOME_LABEL_IDS: dict[str, set[str]] = {}
_SEEN_CONTEXT_CANDIDATE_HASHES: dict[str, set[str]] = {}
_SENSITIVE_KEY_SUFFIXES = (
    "api_key",
    "app_key",
    "appkey",
    "app_secret",
    "appsecret",
    "client_secret",
    "token",
    "authorization",
    "proxy_authorization",
    "cookie",
    "set_cookie",
    "credential",
    "credentials",
    "secret",
    "password",
    "passphrase",
    "private_key",
    "signing_key",
    "account_id",
    "account_no",
    "account_number",
    "acct_id",
    "acct_no",
    "acct_number",
)
_NON_SECRET_INTERNAL_TOKEN_PATHS = frozenset(
    {
        ("runtime_context", "entry_adm", "cache_token"),
        ("runtime_context", "entry_adm", "entry_adm_bucket_token"),
        ("runtime_context", "entry_adm", "entry_adm_cache_token"),
        ("runtime_context", "holding_exit_matrix", "cache_token"),
        ("runtime_context", "lifecycle_ai", "cache_token"),
    }
)
_AUTH_VALUE = re.compile(r"\b(?:bearer|basic)\s+[^\s,;]+", re.IGNORECASE)
_EMBEDDED_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b("
    r"api[_-]?key|app[_-]?(?:key|secret)|client[_-]?secret|"
    r"(?:access|refresh|session|auth|id)[_-]?token|authorization|"
    r"password|passphrase|cookie|set[_-]?cookie|"
    r"account[_-]?(?:id|no|number)|acct[_-]?(?:id|no|number)|token"
    r")(\s*[:=]\s*|=)(\"[^\"]*\"|'[^']*'|[^&\s,;]+)"
)
_OPENAI_KEY_VALUE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
_AWS_ACCESS_KEY_VALUE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_JWT_VALUE = re.compile(
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
)
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?" r"-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_ENTRY_ADM_BUCKET_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]+(?:\|[A-Za-z0-9_.:-]+){7}$")
_INTERNAL_CACHE_TOKEN = re.compile(r"^[A-Za-z0-9_.:|-]{1,1024}$")
_STAGE_BY_PROMPT_TYPE = {
    "scalping_entry": "entry_screen",
    "scalping_shared": "entry_screen",
    "entry_price": "entry_price",
    "scalping_holding_score": "holding_score",
    "holding_exit_flow": "holding_flow",
    "scalping_holding": "holding_flow",
    "scalping_overnight": "overnight",
    "realtime_gatekeeper": "gatekeeper",
}
_SCALPING_ENDPOINTS = {
    "analyze_target",
    "entry_price",
    "holding_score",
    "holding_flow",
    "overnight",
    "realtime_report",
}
_ENTRY_CONTEXT_SCHEMA = "entry_candle_context_v1"
_HOLDING_CONTEXT_SCHEMA = "holding_decision_context_v1"
_EXPECTED_CONTEXT_SCHEMA_BY_ENDPOINT = {
    "analyze_target": _ENTRY_CONTEXT_SCHEMA,
    "entry_price": _ENTRY_CONTEXT_SCHEMA,
    "realtime_report": _ENTRY_CONTEXT_SCHEMA,
    "holding_score": _HOLDING_CONTEXT_SCHEMA,
    "holding_flow": _HOLDING_CONTEXT_SCHEMA,
    "overnight": _HOLDING_CONTEXT_SCHEMA,
}
_REQUIRED_CANDIDATE_CALL_INPUTS = {
    "analyze_target": {
        "target_name",
        "ws_data",
        "recent_ticks",
        "recent_candles",
        "strategy",
        "program_net_qty",
        "cache_profile",
        "prompt_profile",
    },
    "entry_price": {
        "stock_name",
        "stock_code",
        "ws_data",
        "recent_ticks",
        "recent_candles",
        "price_ctx",
    },
    "holding_score": {
        "stock_name",
        "stock_code",
        "ws_data",
        "recent_ticks",
        "recent_candles",
        "position_ctx",
    },
    "holding_flow": {
        "stock_name",
        "stock_code",
        "ws_data",
        "recent_ticks",
        "recent_candles",
        "position_ctx",
        "flow_history",
        "decision_kind",
    },
}


def trace_enabled() -> bool:
    default = "false" if os.getenv("PYTEST_CURRENT_TEST") else "true"
    return str(
        os.getenv("KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED", default)
    ).strip().lower() in {"1", "true", "yes", "y", "on"}


def _now() -> datetime:
    return datetime.now().astimezone()


def _date_text(value: datetime | None = None) -> str:
    return (value or _now()).strftime("%Y-%m-%d")


def _trace_path(target_date: str) -> Path:
    return DATA_DIR / "ai_decision_trace" / f"ai_decision_trace_{target_date}.jsonl"


def _payload_path(target_date: str) -> Path:
    return (
        DATA_DIR / "ai_decision_payloads" / f"ai_decision_payloads_{target_date}.jsonl"
    )


def _request_path(target_date: str) -> Path:
    return (
        DATA_DIR / "ai_decision_requests" / f"ai_decision_requests_{target_date}.jsonl"
    )


def _prompt_path(target_date: str) -> Path:
    return DATA_DIR / "ai_decision_prompts" / f"ai_decision_prompts_{target_date}.jsonl"


def _outcome_path(target_date: str) -> Path:
    return (
        DATA_DIR / "ai_decision_outcomes" / f"ai_decision_outcomes_{target_date}.jsonl"
    )


def _context_candidate_path(target_date: str) -> Path:
    return (
        DATA_DIR
        / "ai_canonical_context_candidates"
        / f"ai_canonical_context_candidates_{target_date}.jsonl"
    )


def _json_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    line = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
        + "\n"
    )
    with jsonl_artifact_generation_lock(
        path,
        exclusive=True,
        blocking=True,
    ) as generation:
        descriptor = -1
        entry_name = generation.logical.name
        try:
            generation.chmod_parent(0o700)
            existing = generation.stat_name(entry_name)
            if existing is not None and not stat.S_ISREG(existing.st_mode):
                raise OSError(f"trace file is not regular: {generation.logical}")
            created = existing is None
            flags = os.O_WRONLY | os.O_APPEND
            if created:
                flags |= os.O_CREAT | os.O_EXCL
            descriptor = generation.open_name(
                entry_name,
                flags,
                0o600,
            )
            opened_identity = generation.assert_open_descriptor_name_identity(
                descriptor,
                entry_name,
            )
            if existing is not None and opened_identity != (
                existing.st_dev,
                existing.st_ino,
                existing.st_size,
                existing.st_mtime_ns,
            ):
                raise OSError(f"trace file changed before append: {generation.logical}")
            os.fchmod(descriptor, 0o600)
            encoded = line.encode("utf-8")
            written = 0
            while written < len(encoded):
                count = os.write(descriptor, encoded[written:])
                if count <= 0:
                    raise OSError(f"short write for trace file: {path}")
                written += count
            if created:
                os.fsync(descriptor)
            final_identity = generation.assert_open_descriptor_name_identity(
                descriptor,
                entry_name,
            )
            if created:
                generation.fsync_parent()
                generation.assert_name_identity(entry_name, final_identity)
        finally:
            if descriptor >= 0:
                os.close(descriptor)


def _load_seen(path: Path, field: str) -> set[str]:
    values: set[str] = set()
    if not path.exists():
        return values
    parent_descriptor = -1
    descriptor = -1
    try:
        parent_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            parent_flags |= os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            parent_flags |= os.O_NOFOLLOW
        parent_descriptor = os.open(path.parent, parent_flags)
        os.fchmod(parent_descriptor, 0o700)
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            descriptor = -1
            for line in handle:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                value = str((row or {}).get(field) or "").strip()
                if value:
                    values.add(value)
    except Exception:
        return values
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    return values


def _sanitize_text(value: str) -> tuple[str, bool]:
    cleaned = str(value)
    redacted = False
    for pattern in (
        _AUTH_VALUE,
        _OPENAI_KEY_VALUE,
        _AWS_ACCESS_KEY_VALUE,
        _JWT_VALUE,
        _PRIVATE_KEY_BLOCK,
    ):
        replaced, count = pattern.subn("[REDACTED]", cleaned)
        cleaned = replaced
        redacted = redacted or count > 0

    assignment_redacted = False

    def _redact_assignment(match: re.Match[str]) -> str:
        nonlocal assignment_redacted
        prefix = match.string[max(0, match.start() - 10) : match.start()].lower()
        raw_value = match.group(3).strip("\"'").upper()
        if (
            match.group(1).lower() == "token"
            and prefix.endswith("json enum ")
            and raw_value in {"BUY", "WAIT", "DROP"}
        ):
            return match.group(0)
        assignment_redacted = True
        return f"{match.group(1)}{match.group(2)}[REDACTED]"

    cleaned, _ = _EMBEDDED_SECRET_ASSIGNMENT.subn(
        _redact_assignment,
        cleaned,
    )
    return cleaned, bool(redacted or assignment_redacted)


def _normalized_key(value: Any) -> str:
    key_text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value or "").strip())
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        key_text.lower(),
    ).strip("_")


def _is_non_secret_internal_token(
    path: tuple[str, ...],
    value: Any,
) -> bool:
    canonical_path = path[1:] if path[:1] == ("exact_payload",) else path
    if canonical_path not in _NON_SECRET_INTERNAL_TOKEN_PATHS or not isinstance(
        value, str
    ):
        return False
    sanitized_value, redacted = _sanitize_text(value)
    if redacted or sanitized_value != value:
        return False
    if canonical_path == (
        "runtime_context",
        "entry_adm",
        "entry_adm_bucket_token",
    ):
        return bool(_ENTRY_ADM_BUCKET_TOKEN.fullmatch(value))
    if not _INTERNAL_CACHE_TOKEN.fullmatch(value):
        return False
    if canonical_path in {
        ("runtime_context", "entry_adm", "cache_token"),
        ("runtime_context", "entry_adm", "entry_adm_cache_token"),
    }:
        return value.startswith("entry_adm:")
    if canonical_path == (
        "runtime_context",
        "holding_exit_matrix",
        "cache_token",
    ):
        return value.startswith(("excluded:", "baseline:", "candidate:"))
    if canonical_path == ("runtime_context", "lifecycle_ai", "cache_token"):
        return value.startswith("lifecycle_ai_context:")
    return False


def _is_sensitive_key(key: Any) -> bool:
    normalized = _normalized_key(key)
    if not normalized:
        return False
    exact_or_suffix = any(
        normalized == suffix or normalized.endswith(f"_{suffix}")
        for suffix in _SENSITIVE_KEY_SUFFIXES
    )
    collapsed = normalized.replace("_", "")
    collapsed_match = any(
        collapsed == suffix.replace("_", "")
        or collapsed.endswith(suffix.replace("_", ""))
        for suffix in _SENSITIVE_KEY_SUFFIXES
    )
    return exact_or_suffix or collapsed_match


def _sanitize(
    value: Any,
    *,
    key: str = "",
    path: tuple[str, ...] = (),
) -> tuple[Any, bool]:
    current_path = (*path, str(key)) if key else path
    if _is_sensitive_key(key) and not _is_non_secret_internal_token(
        current_path, value
    ):
        return "[REDACTED]", True
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        redacted = False
        for index, (child_key, child_value) in enumerate(value.items(), start=1):
            safe_key, key_redacted = _sanitize_text(str(child_key))
            if key_redacted:
                safe_key = f"[REDACTED_KEY_{index}]"
                safe_value, child_redacted = "[REDACTED]", True
            else:
                safe_value, child_redacted = _sanitize(
                    child_value,
                    key=str(child_key),
                    path=current_path,
                )
            cleaned[safe_key] = safe_value
            redacted = redacted or key_redacted or child_redacted
        return cleaned, redacted
    if isinstance(value, (list, tuple)):
        cleaned_list = []
        redacted = False
        for child_value in value:
            safe_value, child_redacted = _sanitize(
                child_value,
                path=current_path,
            )
            cleaned_list.append(safe_value)
            redacted = redacted or child_redacted
        return cleaned_list, redacted
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, (bytes, bytearray)):
        return _sanitize_text(bytes(value).decode("utf-8", errors="replace"))
    if value is None or isinstance(value, (bool, int, float)):
        return value, False
    return _sanitize_text(str(value))


def sanitize_ai_trace_value(value: Any) -> tuple[Any, bool]:
    """Return a storage-safe value plus whether any credential was removed."""

    return _sanitize(value)


def _parse_user_input(user_input: Any) -> tuple[str, Any]:
    if not isinstance(user_input, str):
        return "structured", user_input
    stripped = user_input.strip()
    if stripped.startswith(("{", "[")):
        try:
            return "json_text", json.loads(stripped)
        except Exception:
            pass
    return "plain_text", user_input


def _extract_marked_json_objects(user_input: Any) -> list[Any]:
    """Extract exact canonical JSON embedded after a known prompt marker."""

    if not isinstance(user_input, str):
        return []
    decoder = json.JSONDecoder()
    extracted: list[Any] = []
    for marker in ("[HOLDING_DECISION_CONTEXT]",):
        search_from = 0
        while True:
            marker_index = user_input.find(marker, search_from)
            if marker_index < 0:
                break
            json_text = user_input[marker_index + len(marker) :].lstrip()
            try:
                value, _end = decoder.raw_decode(json_text)
            except (TypeError, ValueError):
                search_from = marker_index + len(marker)
                continue
            extracted.append(value)
            search_from = marker_index + len(marker)
    return extracted


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _first_positive_named_value(
    value: Any, keys: tuple[str, ...]
) -> tuple[str | None, Any]:
    for key in keys:
        for row in _walk(value):
            candidate = row.get(key)
            if key not in row or candidate in (None, "", "-", "None", "null"):
                continue
            try:
                if float(candidate) > 0:
                    return key, candidate
            except Exception:
                continue
    return None, None


def _first_value(value: Any, keys: tuple[str, ...]) -> Any:
    for row in _walk(value):
        for key in keys:
            if key in row and row.get(key) not in (None, "", "-", "None", "null"):
                return row.get(key)
    return None


def _safe_number(value: Any) -> int | float | None:
    if value in (None, "", "-", "None", "null"):
        return None
    try:
        number = float(value)
    except Exception:
        return None
    return int(number) if number.is_integer() else number


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return None


def _normalize_stock_code(value: Any) -> str:
    text = str(value or "").strip().upper()
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
    return match.group(1) if match else "-"


def _request_context(
    user_input: Any,
    metadata: dict[str, Any],
    *,
    endpoint_name: str | None = None,
) -> dict[str, Any]:
    _, parsed = _parse_user_input(user_input)
    endpoint = str(endpoint_name or "").strip().lower()
    if endpoint in {"holding_score", "holding_flow", "overnight"}:
        reference_keys = (
            "executable_bid",
            "best_bid",
            "current_price",
            "curr_price",
            "curr",
            "price",
        )
    elif endpoint == "entry_price":
        reference_keys = (
            "resolved_order_price",
            "executable_ask",
            "best_ask",
            "current_price",
            "curr_price",
            "curr",
            "price",
        )
    else:
        reference_keys = (
            "executable_ask",
            "best_ask",
            "current_price",
            "curr_price",
            "curr",
            "price",
        )
    reference_price_key, reference_price_value = _first_positive_named_value(
        parsed,
        reference_keys,
    )
    reference_price_type = {
        "resolved_order_price": "resolved_order_price",
        "executable_ask": "executable_ask",
        "best_ask": "executable_ask",
        "executable_bid": "executable_bid",
        "best_bid": "executable_bid",
        "current_price": "current_price",
        "curr_price": "current_price",
        "curr": "current_price",
        "price": "current_price",
    }.get(str(reference_price_key or ""))
    context = {
        "stock_code": _first_value(parsed, ("stock_code", "code", "종목코드"))
        or metadata.get("stock_code"),
        "record_id": _first_value(parsed, ("record_id", "recommendation_id"))
        or metadata.get("record_id"),
        "recommendation_id": _first_value(parsed, ("recommendation_id",)),
        "probe_bundle_id": _first_value(
            parsed,
            (
                "probe_bundle_id",
                "entry_split_probe_bundle_id",
                "entry_split_order_probe_bundle_id",
            ),
        )
        or metadata.get("probe_bundle_id"),
        "position_cycle_id": _first_value(
            parsed,
            ("position_cycle_id",),
        )
        or metadata.get("position_cycle_id"),
        "broker_order_no": _first_value(
            parsed, ("broker_order_no", "order_no", "ord_no")
        ),
        "snapshot_id": _first_value(parsed, ("snapshot_id",))
        or metadata.get("snapshot_id"),
        "effective_venue": _first_value(parsed, ("effective_venue",))
        or metadata.get("effective_venue"),
        "session_bucket": _first_value(
            parsed, ("session_bucket", "market_session_bucket")
        )
        or metadata.get("session_bucket")
        or metadata.get("market_session_bucket"),
        "broker_route": _first_value(parsed, ("broker_route",))
        or metadata.get("broker_route"),
        "market_data_route": _first_value(parsed, ("market_data_route",))
        or metadata.get("market_data_route"),
        "reference_price_type": reference_price_type,
        "reference_price": _safe_number(reference_price_value),
        "best_bid": _safe_number(_first_value(parsed, ("best_bid",))),
        "best_ask": _safe_number(_first_value(parsed, ("best_ask", "executable_ask"))),
        "target_price": _safe_number(_first_value(parsed, ("target_price",))),
        "adverse_price": _safe_number(
            _first_value(parsed, ("adverse_price", "stop_price"))
        ),
        "target_pct": _safe_number(_first_value(parsed, ("target_pct",))),
        "adverse_pct": _safe_number(_first_value(parsed, ("adverse_pct", "stop_pct"))),
    }
    return context


def _canonical_context_capture(
    user_input: Any,
    *,
    endpoint_name: str,
) -> dict[str, Any]:
    """Describe, without modifying, the canonical candle context sent to AI.

    This is provenance only.  In particular, a compact forensic request is not
    retrofitted from a later market snapshot: it remains visible as ineligible
    for the exact-v2 decision-quality cohort.
    """

    input_kind, parsed = _parse_user_input(user_input)
    endpoint = str(endpoint_name or "").strip().lower()
    expected_schema = _EXPECTED_CONTEXT_SCHEMA_BY_ENDPOINT.get(endpoint)
    candidates: list[dict[str, Any]] = []
    capture_roots = [parsed]
    if input_kind == "plain_text":
        capture_roots.extend(_extract_marked_json_objects(user_input))
    for capture_root in capture_roots:
        for row in _walk(capture_root):
            schema = str(row.get("schema") or "")
            if schema not in {_ENTRY_CONTEXT_SCHEMA, _HOLDING_CONTEXT_SCHEMA}:
                continue
            candle = row.get("candle") if schema == _HOLDING_CONTEXT_SCHEMA else row
            candle = candle if isinstance(candle, dict) else {}
            bars = candle.get("bars") if isinstance(candle.get("bars"), list) else None
            input_bundle_version = str(candle.get("input_bundle_version") or "")
            if schema == _ENTRY_CONTEXT_SCHEMA:
                forming_key = "forming"
            else:
                forming_key = "is_forming"
            completed_bar_count = sum(
                1
                for bar in (bars or [])
                if isinstance(bar, dict) and not bool(bar.get(forming_key, False))
            )
            candidates.append(
                {
                    "schema": schema,
                    "input_bundle_version": input_bundle_version or None,
                    "raw_bar_count": len(bars) if bars is not None else None,
                    "completed_bar_count": completed_bar_count,
                    "forming_bar_present": any(
                        isinstance(bar, dict) and bool(bar.get(forming_key, False))
                        for bar in (bars or [])
                    ),
                }
            )

    matching = [row for row in candidates if row["schema"] == expected_schema]
    selected = max(
        matching or candidates,
        key=lambda row: (row["completed_bar_count"], row["raw_bar_count"] or -1),
        default=None,
    )
    status = "canonical_context_missing"
    if selected is not None:
        if expected_schema and selected["schema"] != expected_schema:
            status = "canonical_context_stage_mismatch"
        elif not selected["input_bundle_version"]:
            status = "canonical_input_bundle_missing"
        elif selected["raw_bar_count"] is None:
            status = "canonical_bars_missing"
        elif selected["completed_bar_count"] <= 0:
            status = "canonical_completed_bars_missing"
        else:
            status = "exact_completed_bars_captured"
    return {
        "expected_schema": expected_schema,
        "status": status,
        "exact_v2_candidate": status == "exact_completed_bars_captured",
        "schema": selected.get("schema") if selected else None,
        "input_bundle_version": (
            selected.get("input_bundle_version") if selected else None
        ),
        "raw_bar_count": selected.get("raw_bar_count") if selected else None,
        "completed_bar_count": (
            selected.get("completed_bar_count") if selected else None
        ),
        "forming_bar_present": (
            selected.get("forming_bar_present") if selected else None
        ),
    }


def _canonical_context_application_state(merged: dict[str, Any]) -> str:
    """Classify actual-payload use separately from a forensic candidate.

    A disabled promotion can legitimately preserve an exact context candidate
    while omitting it from the live provider payload.  Treating that state as
    a failed payload application hides the promotion boundary; treating it as
    applied would be worse.  Keep the two facts explicit in every decision
    trace so coverage reports can use the appropriate denominator.
    """

    capture_status = str(
        _optional(merged, "ai_trace_canonical_context_capture_status") or ""
    ).strip()
    candidate_status = str(
        _optional(merged, "ai_context_candidate_status") or ""
    ).strip()
    if capture_status == "exact_completed_bars_captured":
        return "applied_exact"
    if candidate_status == "ready_for_explicit_provider_call":
        return "promotion_gated_forensic_exact_available"
    if candidate_status == "source_candidate_ineligible":
        return "forensic_candidate_ineligible"
    if capture_status:
        return "no_exact_payload_or_candidate"
    return "legacy_or_uninstrumented"


def capture_canonical_context_candidate(
    *,
    source_context: dict[str, Any] | None,
    model_context: dict[str, Any] | None,
    endpoint_name: str,
    symbol: str,
    call_inputs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a source-complete, non-authoritative prepromotion context.

    This does not represent an AI request and can never be promoted directly.
    The explicit validation-only probe must still send ``model_context`` to the
    real endpoint and produce the normal request/payload/response provenance.
    """

    if not trace_enabled():
        return {}
    endpoint = str(endpoint_name or "").strip().lower()
    expected_schema = _EXPECTED_CONTEXT_SCHEMA_BY_ENDPOINT.get(endpoint)
    if endpoint not in _SCALPING_ENDPOINTS or not expected_schema:
        return {}
    source = source_context if isinstance(source_context, dict) else {}
    model = model_context if isinstance(model_context, dict) else {}
    if (
        source.get("schema") != expected_schema
        or model.get("schema") != expected_schema
    ):
        return {}
    context_key = (
        "entry_candle_context"
        if expected_schema == _ENTRY_CONTEXT_SCHEMA
        else "holding_decision_context"
    )
    evidence = _canonical_context_capture(
        {context_key: model},
        endpoint_name=endpoint,
    )
    source_quality = (
        source.get("source_quality")
        if isinstance(source.get("source_quality"), dict)
        else {}
    )
    if expected_schema == _HOLDING_CONTEXT_SCHEMA:
        candle = source.get("candle") if isinstance(source.get("candle"), dict) else {}
        candle_quality = (
            candle.get("source_quality")
            if isinstance(candle.get("source_quality"), dict)
            else {}
        )
        blockers = list(source_quality.get("blockers") or []) + list(
            candle_quality.get("blockers") or []
        )
    else:
        blockers = list(source_quality.get("blockers") or [])
    source_quality_status = str(
        source_quality.get("status") or "fresh_consistent"
    ).strip()
    promotion_disabled_only = bool(
        expected_schema == _HOLDING_CONTEXT_SCHEMA
        and source.get("enabled") is False
        and source_quality_status == "disabled"
        and not blockers
    )
    eligible = bool(
        evidence.get("exact_v2_candidate")
        and not blockers
        and (source_quality_status == "fresh_consistent" or promotion_disabled_only)
    )
    now = _now()
    target_date = _date_text(now)
    safe_source, source_redacted = _sanitize(source)
    safe_model, model_redacted = _sanitize(model)
    inputs = call_inputs if isinstance(call_inputs, dict) else {}
    safe_inputs, inputs_redacted = _sanitize(inputs)
    required_call_inputs = _REQUIRED_CANDIDATE_CALL_INPUTS.get(endpoint, set())
    missing_call_inputs = sorted(required_call_inputs - set(inputs))
    call_inputs_ready = bool(required_call_inputs) and not missing_call_inputs
    candidate_sha256 = hashlib.sha256(
        _json_bytes(
            {
                "endpoint": endpoint,
                "symbol": _normalize_stock_code(symbol),
                "source_context": safe_source,
                "model_context": safe_model,
                "call_inputs": safe_inputs,
            }
        )
    ).hexdigest()
    row = {
        "schema": CONTEXT_CANDIDATE_SCHEMA,
        "captured_at": now.isoformat(),
        "candidate_sha256": candidate_sha256,
        "endpoint": endpoint,
        "symbol": _normalize_stock_code(symbol),
        "effective_venue": safe_source.get("venue"),
        "session_bucket": safe_source.get("session"),
        "expected_context_schema": expected_schema,
        "canonical_context_capture": evidence,
        "source_context": safe_source,
        "model_context": safe_model,
        "call_inputs": safe_inputs,
        "call_inputs_contract": {
            "required_keys": sorted(required_call_inputs),
            "missing_keys": missing_call_inputs,
            "ready": call_inputs_ready,
            "replay_policy": "reuse_exact_sanitized_natural_call_inputs",
        },
        "redacted": bool(source_redacted or model_redacted or inputs_redacted),
        "validation_only_eligible": eligible
        and not source_redacted
        and not model_redacted
        and not inputs_redacted
        and call_inputs_ready,
        "validation_only_status": (
            "ready_for_explicit_provider_call"
            if (
                eligible
                and not source_redacted
                and not model_redacted
                and not inputs_redacted
                and call_inputs_ready
            )
            else "source_candidate_ineligible"
        ),
        "source_quality_blockers": sorted({str(item) for item in blockers if item}),
        "source_quality_status": source_quality_status,
        "promotion_disabled_only": promotion_disabled_only,
        "source_event_stage": str(
            _sanitize_text(
                str((metadata or {}).get("source_event_stage") or "unknown")
            )[0]
        ),
        "request_capture_status": "not_called_candidate_only",
        "provider_called": False,
        "provider": "none",
        "validation_only_contract": {
            "decision_authority": "forensics_only_no_runtime_change",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "result_consumer": "artifact_only_never_runtime_decision",
        },
        **STORAGE_SECURITY_CONTRACT,
        **OBSERVATION_CONTRACT,
        **CONTEXT_CANDIDATE_OBSERVATION_CONTRACT,
    }
    try:
        with _WRITE_LOCK:
            seen = _SEEN_CONTEXT_CANDIDATE_HASHES.get(target_date)
            if seen is None:
                path = _context_candidate_path(target_date)
                seen = _load_seen(path, "candidate_sha256")
                _SEEN_CONTEXT_CANDIDATE_HASHES[target_date] = seen
            if candidate_sha256 not in seen:
                _append_jsonl(_context_candidate_path(target_date), row)
                seen.add(candidate_sha256)
        return {
            "ai_context_candidate_sha256": candidate_sha256,
            "ai_context_candidate_status": row["validation_only_status"],
            "ai_context_candidate_schema": expected_schema,
        }
    except Exception as exc:
        log_error(f"[AI_DECISION_TRACE] context candidate capture failed: {exc}")
        return {}


def capture_ai_request(
    *,
    prompt: Any,
    user_input: Any,
    endpoint_name: str,
    symbol: str,
    request_id: str,
    model: str,
    schema_name: str | None,
    require_json: bool,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    metadata: dict[str, Any] | None = None,
    replay_context: Any = None,
) -> dict[str, Any]:
    """Persist provider input plus an optional exact offline replay context."""
    if not trace_enabled():
        return {}
    try:
        if str(endpoint_name or "") not in _SCALPING_ENDPOINTS:
            return {}
        strategy = str((metadata or {}).get("ai_trace_strategy") or "").upper()
        if strategy in {"KOSPI_ML", "KOSDAQ_ML", "SWING"}:
            return {}
        if str(endpoint_name or "") == "realtime_report" and strategy not in {
            "SCALP",
            "SCALPING",
        }:
            return {}
        now = _now()
        target_date = _date_text(now)
        metadata_row = dict(metadata or {})
        raw_input = _json_bytes(user_input)
        payload_sha256 = hashlib.sha256(raw_input).hexdigest()
        replay_context_present = replay_context is not None
        replay_context_bytes = (
            _json_bytes(replay_context) if replay_context_present else b""
        )
        replay_context_sha256 = (
            hashlib.sha256(replay_context_bytes).hexdigest()
            if replay_context_present
            else None
        )
        prompt_sha256 = hashlib.sha256(_json_bytes(prompt)).hexdigest()
        request_envelope = {
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "require_json": bool(require_json),
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "reasoning_effort": reasoning_effort,
            "prompt_sha256": prompt_sha256,
            "user_input_sha256": payload_sha256,
        }
        if replay_context_sha256:
            request_envelope["replay_context_sha256"] = replay_context_sha256
        request_envelope_sha256 = hashlib.sha256(
            _json_bytes(request_envelope)
        ).hexdigest()
        input_format, parsed_input = _parse_user_input(user_input)
        sanitized_input, redacted = _sanitize(parsed_input)
        sanitized_user_input_sha256 = hashlib.sha256(
            _json_bytes(sanitized_input)
        ).hexdigest()
        if replay_context_present:
            replay_input_format, parsed_replay_context = _parse_user_input(
                replay_context
            )
            sanitized_replay_context, replay_context_redacted = _sanitize(
                parsed_replay_context
            )
            sanitized_replay_context_sha256 = hashlib.sha256(
                _json_bytes(sanitized_replay_context)
            ).hexdigest()
        else:
            replay_input_format = None
            parsed_replay_context = None
            sanitized_replay_context = None
            sanitized_replay_context_sha256 = None
            replay_context_redacted = False
        sanitized_prompt, prompt_redacted = _sanitize(str(prompt or ""))
        context = _request_context(
            parsed_replay_context if replay_context_present else parsed_input,
            metadata_row,
            endpoint_name=endpoint_name,
        )
        canonical_context = _canonical_context_capture(
            parsed_replay_context if replay_context_present else parsed_input,
            endpoint_name=endpoint_name,
        )
        replay_payload_fields = (
            {
                "replay_context_present": True,
                "replay_context_input_format": replay_input_format,
                "replay_context_sha256": replay_context_sha256,
                "replay_context_bytes": len(replay_context_bytes),
                "replay_context_redacted": bool(replay_context_redacted),
                "replay_context_exact": not replay_context_redacted,
                "sanitized_replay_context": sanitized_replay_context,
                "sanitized_replay_context_sha256": (sanitized_replay_context_sha256),
            }
            if replay_context_present
            else {}
        )
        replay_request_fields = (
            {
                "replay_context_sha256": replay_context_sha256,
                "replay_context_redacted": bool(replay_context_redacted),
                "replay_context_exact": not replay_context_redacted,
                "sanitized_replay_context_sha256": (sanitized_replay_context_sha256),
            }
            if replay_context_present
            else {}
        )
        replay_result_fields = (
            {
                "ai_replay_context_present": True,
                "ai_replay_context_sha256": replay_context_sha256,
                "ai_replay_context_bytes": len(replay_context_bytes),
                "ai_replay_context_redacted": bool(replay_context_redacted),
                "ai_replay_context_exact": not replay_context_redacted,
                "ai_replay_context_semantic_sha256": (sanitized_replay_context_sha256),
            }
            if replay_context_present
            else {}
        )
        trace_id = str(request_id or "").strip() or f"aidt-{uuid.uuid4().hex}"
        payload_row = {
            "schema": PAYLOAD_SCHEMA,
            "captured_at": now.isoformat(),
            "request_id": trace_id,
            "symbol": context.get("stock_code") or str(symbol or "") or None,
            "snapshot_id": context.get("snapshot_id"),
            "effective_venue": context.get("effective_venue"),
            "session_bucket": context.get("session_bucket"),
            "broker_route": context.get("broker_route"),
            "market_data_route": context.get("market_data_route"),
            "sim_record_id": (metadata or {}).get("sim_record_id"),
            "sim_parent_record_id": (metadata or {}).get("sim_parent_record_id"),
            "source_event_stage": (metadata or {}).get("source_event_stage"),
            "holding_exact_replay_context_capture_status": metadata_row.get(
                "holding_exact_replay_context_capture_status"
            ),
            "holding_exact_replay_context_capture_error_type": metadata_row.get(
                "holding_exact_replay_context_capture_error_type"
            ),
            "holding_exact_replay_context_capture_latency_ms": metadata_row.get(
                "holding_exact_replay_context_capture_latency_ms"
            ),
            "payload_sha256": payload_sha256,
            "payload_bytes": len(raw_input),
            "request_envelope_sha256": request_envelope_sha256,
            "prompt_sha256": prompt_sha256,
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "require_json": bool(require_json),
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "reasoning_effort": reasoning_effort,
            "input_format": input_format,
            "redacted": bool(redacted),
            "replay_exact": not redacted,
            "sanitized_user_input": sanitized_input,
            "sanitized_user_input_sha256": sanitized_user_input_sha256,
            **replay_payload_fields,
            "canonical_context_capture": canonical_context,
            **STORAGE_SECURITY_CONTRACT,
            **OBSERVATION_CONTRACT,
        }
        prompt_row = {
            "schema": PROMPT_SCHEMA,
            "captured_at": now.isoformat(),
            "prompt_sha256": prompt_sha256,
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "redacted": bool(prompt_redacted),
            "replay_exact": not prompt_redacted,
            "sanitized_prompt": sanitized_prompt,
            **STORAGE_SECURITY_CONTRACT,
            **OBSERVATION_CONTRACT,
        }
        request_row = {
            "schema": REQUEST_SCHEMA,
            "captured_at": now.isoformat(),
            "request_id": trace_id,
            "symbol": context.get("stock_code") or str(symbol or "") or None,
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "snapshot_id": context.get("snapshot_id"),
            "effective_venue": context.get("effective_venue"),
            "session_bucket": context.get("session_bucket"),
            "broker_route": context.get("broker_route"),
            "market_data_route": context.get("market_data_route"),
            "sim_record_id": (metadata or {}).get("sim_record_id"),
            "sim_parent_record_id": (metadata or {}).get("sim_parent_record_id"),
            "source_event_stage": (metadata or {}).get("source_event_stage"),
            "holding_exact_replay_context_capture_status": metadata_row.get(
                "holding_exact_replay_context_capture_status"
            ),
            "holding_exact_replay_context_capture_error_type": metadata_row.get(
                "holding_exact_replay_context_capture_error_type"
            ),
            "holding_exact_replay_context_capture_latency_ms": metadata_row.get(
                "holding_exact_replay_context_capture_latency_ms"
            ),
            "payload_sha256": payload_sha256,
            "request_envelope_sha256": request_envelope_sha256,
            "prompt_sha256": prompt_sha256,
            "payload_redacted": bool(redacted),
            "sanitized_user_input_sha256": sanitized_user_input_sha256,
            **replay_request_fields,
            "prompt_redacted": bool(prompt_redacted),
            "canonical_context_capture": canonical_context,
            **STORAGE_SECURITY_CONTRACT,
            **OBSERVATION_CONTRACT,
        }
        with _WRITE_LOCK:
            seen = _SEEN_PAYLOAD_HASHES.get(target_date)
            if seen is None:
                path = _payload_path(target_date)
                seen = _load_seen(path, "request_envelope_sha256")
                _SEEN_PAYLOAD_HASHES[target_date] = seen
            if request_envelope_sha256 not in seen:
                _append_jsonl(_payload_path(target_date), payload_row)
                seen.add(request_envelope_sha256)
            seen_prompts = _SEEN_PROMPT_HASHES.get(target_date)
            if seen_prompts is None:
                prompt_path = _prompt_path(target_date)
                seen_prompts = _load_seen(prompt_path, "prompt_sha256")
                _SEEN_PROMPT_HASHES[target_date] = seen_prompts
            if prompt_sha256 not in seen_prompts:
                _append_jsonl(_prompt_path(target_date), prompt_row)
                seen_prompts.add(prompt_sha256)
            # Commit the request ledger last. A request row must never point at
            # payload/prompt content that failed to persist.
            seen_requests = _SEEN_REQUEST_IDS.get(target_date)
            if seen_requests is None:
                request_path = _request_path(target_date)
                seen_requests = _load_seen(request_path, "request_id")
                _SEEN_REQUEST_IDS[target_date] = seen_requests
            if trace_id not in seen_requests:
                _append_jsonl(_request_path(target_date), request_row)
                seen_requests.add(trace_id)
        return {
            "ai_decision_trace_id": trace_id,
            "ai_prompt_sha256": prompt_sha256,
            "ai_prompt_store_date": target_date,
            "ai_prompt_redacted": bool(prompt_redacted),
            "ai_prompt_replay_exact": not prompt_redacted,
            "ai_input_payload_sha256": payload_sha256,
            "ai_input_payload_bytes": len(raw_input),
            "ai_request_envelope_sha256": request_envelope_sha256,
            "ai_request_temperature": temperature,
            "ai_request_max_output_tokens": max_output_tokens,
            "ai_request_reasoning_effort": reasoning_effort,
            "ai_request_schema_name": str(schema_name or "-") or "-",
            "ai_request_require_json": bool(require_json),
            "ai_input_payload_store_date": target_date,
            "ai_input_payload_redacted": bool(redacted),
            "ai_input_payload_replay_exact": not redacted,
            "ai_input_payload_semantic_sha256": sanitized_user_input_sha256,
            **replay_result_fields,
            "ai_trace_stock_code": context.get("stock_code") or symbol or None,
            "ai_trace_record_id": context.get("record_id"),
            "ai_trace_recommendation_id": context.get("recommendation_id"),
            "ai_trace_probe_bundle_id": context.get("probe_bundle_id"),
            "ai_trace_position_cycle_id": context.get("position_cycle_id"),
            "ai_trace_broker_order_no": context.get("broker_order_no"),
            "ai_trace_snapshot_id": context.get("snapshot_id"),
            "ai_trace_effective_venue": context.get("effective_venue"),
            "ai_trace_session_bucket": context.get("session_bucket"),
            "ai_trace_broker_route": context.get("broker_route"),
            "ai_trace_market_data_route": context.get("market_data_route"),
            "sim_record_id": (metadata or {}).get("sim_record_id"),
            "sim_parent_record_id": (metadata or {}).get("sim_parent_record_id"),
            "source_event_stage": (metadata or {}).get("source_event_stage"),
            "holding_exact_replay_context_capture_status": metadata_row.get(
                "holding_exact_replay_context_capture_status"
            ),
            "holding_exact_replay_context_capture_error_type": metadata_row.get(
                "holding_exact_replay_context_capture_error_type"
            ),
            "holding_exact_replay_context_capture_latency_ms": metadata_row.get(
                "holding_exact_replay_context_capture_latency_ms"
            ),
            "ai_trace_reference_price_type": context.get("reference_price_type"),
            "ai_trace_reference_price": context.get("reference_price"),
            "ai_trace_best_bid": context.get("best_bid"),
            "ai_trace_best_ask": context.get("best_ask"),
            "ai_trace_target_price": context.get("target_price"),
            "ai_trace_adverse_price": context.get("adverse_price"),
            "ai_trace_target_pct": context.get("target_pct"),
            "ai_trace_adverse_pct": context.get("adverse_pct"),
            "ai_trace_canonical_context_capture_status": canonical_context["status"],
            "ai_trace_canonical_context_schema": canonical_context["schema"],
            "ai_trace_canonical_context_input_bundle_version": canonical_context[
                "input_bundle_version"
            ],
            "ai_trace_canonical_context_raw_bar_count": canonical_context[
                "raw_bar_count"
            ],
            "ai_trace_canonical_context_completed_bar_count": canonical_context[
                "completed_bar_count"
            ],
            "ai_trace_canonical_context_forming_bar_present": canonical_context[
                "forming_bar_present"
            ],
        }
    except Exception as exc:
        log_error(f"[AI_DECISION_TRACE] request capture failed: {exc}")
        return {}


def replay_source_input(payload_row: Any) -> Any:
    """Return the exact offline source while keeping provider input truthful."""

    row = payload_row if isinstance(payload_row, dict) else {}
    if row.get("replay_context_present") is True:
        if (
            row.get("replay_context_exact") is True
            and row.get("sanitized_replay_context") is not None
        ):
            return row.get("sanitized_replay_context")
        return None
    if (
        row.get("replay_context_exact") is True
        and row.get("sanitized_replay_context") is not None
    ):
        return row.get("sanitized_replay_context")
    return row.get("sanitized_user_input")


def _decision_stage(prompt_type: str, explicit_stage: str | None = None) -> str:
    if explicit_stage:
        return str(explicit_stage)
    return _STAGE_BY_PROMPT_TYPE.get(
        str(prompt_type or ""), str(prompt_type or "unknown")
    )


def _optional(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, "", "-", "None", "null"):
            return value
    return None


def _provider_actual(payload: dict[str, Any], provider_called: bool) -> str | None:
    if not provider_called:
        return None
    explicit = _optional(payload, "ai_provider_actual", "provider_actual", "provider")
    if explicit:
        return str(explicit)
    if payload.get("bedrock_primary_used"):
        return "bedrock"
    if payload.get("bedrock_fallback_used"):
        return "bedrock"
    if payload.get("bedrock_failback_used"):
        transport_mode = str(payload.get("openai_transport_mode") or "").lower()
        if transport_mode in {"bedrock_primary", "bedrock_fallback"}:
            return "bedrock"
        return "openai"
    if provider_called:
        return "openai"
    return None


def _provider_decision_origin(payload: dict[str, Any]) -> str | None:
    explicit = _optional(payload, "ai_provider_actual", "provider_actual", "provider")
    if explicit:
        return str(explicit)
    transport_mode = str(payload.get("openai_transport_mode") or "").lower()
    if (
        payload.get("bedrock_primary_used")
        or payload.get("bedrock_fallback_used")
        or (
            payload.get("bedrock_failback_used")
            and transport_mode in {"bedrock_primary", "bedrock_fallback"}
        )
    ):
        return "bedrock"
    if _optional(payload, "openai_model", "ai_model"):
        return "openai"
    return None


def _model_actual(payload: dict[str, Any]) -> str | None:
    explicit = _optional(payload, "ai_model_actual")
    if explicit:
        return str(explicit)
    transport_mode = str(payload.get("openai_transport_mode") or "").lower()
    if (
        payload.get("bedrock_primary_used")
        or payload.get("bedrock_fallback_used")
        or (
            payload.get("bedrock_failback_used")
            and transport_mode in {"bedrock_primary", "bedrock_fallback"}
        )
    ):
        return _optional(
            payload,
            "bedrock_model_family",
            "bedrock_failback_family",
            "bedrock_fallback_family",
        )
    value = _optional(payload, "ai_model", "openai_model")
    return str(value) if value is not None else None


def _reason_codes(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("reason_codes")
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    value = payload.get("reason_code")
    return [str(value)] if value not in (None, "", "-") else []


def _total_tokens(payload: dict[str, Any]) -> float | int | None:
    openai_total = _safe_number(payload.get("openai_total_tokens"))
    if openai_total is not None:
        return openai_total
    bedrock_input = _safe_number(payload.get("bedrock_total_input_tokens"))
    bedrock_output = _safe_number(payload.get("bedrock_output_tokens"))
    if bedrock_input is None and bedrock_output is None:
        return None
    return int(bedrock_input or 0) + int(bedrock_output or 0)


def _timeout_like_decision_failure(
    payload: dict[str, Any], result_source: str | None
) -> bool:
    if str(result_source or "").strip().lower() == "timeout":
        return True
    if any(
        bool(payload.get(key))
        for key in (
            "openai_timeout_like",
            "openai_ws_http_fallback_fail_closed",
            "openai_http_timeout_budget_exhausted",
            "holding_score_timeout_like",
        )
    ):
        return True
    reason = " ".join(
        str(payload.get(key) or "")
        for key in (
            "reason",
            "error",
            "openai_transport_fail_closed_reason",
            "holding_score_transport_fail_closed_reason",
        )
    ).lower()
    return any(
        marker in reason
        for marker in (
            "timeout budget exhausted",
            "request timed out",
            "timed out",
        )
    )


def record_ai_decision_trace(
    result: dict[str, Any] | None,
    *,
    prompt_type: str,
    prompt_version: str,
    result_source: str,
    input_contract_fields: dict[str, Any] | None = None,
    decision_stage: str | None = None,
    stock_code: str | None = None,
    provider_called: bool | None = None,
) -> dict[str, Any]:
    """Append the immutable final decision and create its pending outcome row."""
    if not trace_enabled():
        return {}
    try:
        if str(prompt_type or "") not in _STAGE_BY_PROMPT_TYPE:
            return {}
        now = _now()
        target_date = _date_text(now)
        payload = dict(result or {})
        contract = dict(input_contract_fields or {})
        merged = {**contract, **payload}
        if str(prompt_type or "") == "realtime_gatekeeper" and str(
            _optional(merged, "ai_trace_strategy", "selected_mode") or ""
        ).upper() not in {"SCALP", "SCALPING"}:
            return {}
        decision_result_sha256 = hashlib.sha256(_json_bytes(payload)).hexdigest()
        trace_id = (
            str(
                _optional(merged, "ai_decision_trace_id", "openai_request_id") or ""
            ).strip()
            or f"aidt-{uuid.uuid4().hex}"
        )
        request_capture_markers = (
            _optional(merged, "ai_prompt_sha256"),
            _optional(merged, "ai_prompt_store_date"),
            _optional(merged, "ai_input_payload_sha256"),
            _optional(merged, "ai_input_payload_store_date"),
            _optional(merged, "ai_request_envelope_sha256"),
        )
        if all(request_capture_markers):
            request_capture_status = "captured"
        elif any(request_capture_markers):
            request_capture_status = "partial"
        else:
            request_capture_status = "missing"
        if provider_called is None:
            raw_provider_called = (
                payload.get("provider_called")
                if "provider_called" in payload
                else str(result_source or "") == "live"
            )
            normalized_provider_called = _safe_bool(raw_provider_called)
            provider_called = (
                normalized_provider_called
                if normalized_provider_called is not None
                else bool(raw_provider_called)
            )
        else:
            normalized_provider_called = _safe_bool(provider_called)
            if normalized_provider_called is not None:
                provider_called = normalized_provider_called
        timeout_like = _timeout_like_decision_failure(merged, result_source)
        if (
            timeout_like
            and (_safe_number(merged.get("openai_http_attempt_count")) or 0) > 0
        ):
            provider_called = True
        normalized_result_source = (
            "timeout"
            if timeout_like
            and str(result_source or "").strip().lower()
            in {"timeout", "exception", "error"}
            else str(result_source or "-")
        )
        preflight_status = (
            str(_optional(merged, "ai_input_preflight_status") or "").strip().lower()
        )
        preflight_allowed = (
            _safe_bool(merged.get("ai_input_preflight_allowed"))
            if "ai_input_preflight_allowed" in merged
            else None
        )
        outcome_label_exclusion_reasons: list[str] = []
        if not bool(provider_called):
            outcome_label_exclusion_reasons.append("provider_not_called")
        requested_outcome_eligible = _safe_bool(
            merged.get("ai_decision_outcome_eligible", True)
        )
        if requested_outcome_eligible is False:
            outcome_label_exclusion_reasons.append(
                "explicit_ai_decision_outcome_ineligible"
            )
        if preflight_allowed is False:
            outcome_label_exclusion_reasons.append("input_preflight_not_allowed")
        if (
            preflight_status
            in {
                "blocked",
                "fail",
                "failed",
                "source_quality_blocked",
            }
            or normalized_result_source == "input_preflight_blocked"
        ):
            outcome_label_exclusion_reasons.append("input_preflight_blocked")
        outcome_label_exclusion_reasons = sorted(set(outcome_label_exclusion_reasons))
        stage = _decision_stage(prompt_type, decision_stage)
        reference_price_type = _optional(merged, "ai_trace_reference_price_type")
        reference_price = _safe_number(_optional(merged, "ai_trace_reference_price"))
        if stage == "entry_price":
            decision_order_price = _safe_number(_optional(merged, "order_price"))
            if decision_order_price is not None and decision_order_price > 0:
                reference_price_type = "resolved_order_price"
                reference_price = decision_order_price
        stock_identifier = str(
            stock_code
            or _optional(
                merged,
                "ai_trace_stock_code",
                "ai_market_snapshot_stock_code",
                "ai_input_stock_code",
            )
            or "-"
        ).strip()
        trace_row = {
            "schema": TRACE_SCHEMA,
            "decision_trace_id": trace_id,
            "request_id": _optional(merged, "openai_request_id", "ai_decision_trace_id")
            or trace_id,
            "decision_ts": now.isoformat(),
            "decision_stage": stage,
            "decision_evaluation_status": (
                "not_evaluated_transport_timeout"
                if timeout_like
                else (
                    "evaluated"
                    if str(normalized_result_source).strip().lower()
                    in {"live", "prior_valid"}
                    else "not_evaluated_provider_or_preflight"
                )
            ),
            "stock_code": _normalize_stock_code(stock_identifier),
            "stock_identifier": stock_identifier[:40],
            "effective_venue": _optional(
                merged,
                "ai_trace_effective_venue",
                "ai_market_snapshot_effective_venue",
                "ai_input_effective_venue",
            ),
            "session_bucket": _optional(
                merged,
                "ai_trace_session_bucket",
                "ai_market_snapshot_session_bucket",
            ),
            "broker_route": _optional(
                merged,
                "ai_trace_broker_route",
                "ai_market_snapshot_broker_route",
                "ai_input_broker_route",
            ),
            "market_data_route": _optional(
                merged,
                "ai_trace_market_data_route",
                "ai_market_snapshot_market_data_route",
                "ai_input_market_data_route",
            ),
            "record_id": _optional(merged, "ai_trace_record_id", "record_id"),
            "sim_record_id": _optional(merged, "sim_record_id"),
            "sim_parent_record_id": _optional(merged, "sim_parent_record_id"),
            "source_event_stage": _optional(merged, "source_event_stage"),
            "recommendation_id": _optional(
                merged, "ai_trace_recommendation_id", "recommendation_id"
            ),
            "probe_bundle_id": _optional(
                merged, "ai_trace_probe_bundle_id", "probe_bundle_id"
            ),
            "position_cycle_id": _optional(
                merged, "ai_trace_position_cycle_id", "position_cycle_id"
            ),
            "broker_order_no": _optional(
                merged, "ai_trace_broker_order_no", "broker_order_no"
            ),
            "snapshot_id": _optional(
                merged,
                "ai_trace_snapshot_id",
                "ai_input_snapshot_id",
                "ai_market_snapshot_id",
            ),
            "endpoint": _optional(
                merged,
                "ai_trace_endpoint_name",
                "openai_endpoint_name",
            )
            or prompt_type,
            "provider_expected": _optional(
                merged,
                "holding_context_provider_expected",
                "provider_expected",
            ),
            "provider_actual": _provider_actual(merged, bool(provider_called)),
            "provider_decision_origin": _provider_decision_origin(merged),
            "provider_response_id": _optional(
                merged,
                "openai_response_id",
                "provider_response_id",
                "bedrock_response_id",
            ),
            "openai_response_schema_registry_used": (
                bool(merged.get("openai_response_schema_registry_used"))
                if "openai_response_schema_registry_used" in merged
                else None
            ),
            "openai_response_schema_mode": _optional(
                merged, "openai_response_schema_mode"
            ),
            "response_schema_sha256": _optional(
                merged,
                "openai_response_schema_sha256",
                "response_schema_sha256",
            ),
            "response_schema_application": _optional(
                merged,
                "openai_response_schema_application",
                "response_schema_application",
            ),
            "openai_entry_risk_dynamic_fact_schema_applied": (
                bool(merged.get("openai_entry_risk_dynamic_fact_schema_applied"))
                if "openai_entry_risk_dynamic_fact_schema_applied" in merged
                else None
            ),
            "model": _model_actual(merged),
            "model_requested": _optional(merged, "openai_model", "ai_model"),
            "model_id": _optional(
                merged,
                "bedrock_model_id",
                "openai_model",
                "ai_model",
            ),
            "provider_region": _optional(
                merged, "bedrock_region_name", "provider_region"
            ),
            "failback_chain": merged.get(
                "provider_failback_chain",
                merged.get("failback_chain", []),
            ),
            "prompt_type": str(prompt_type or "-"),
            "prompt_version": str(prompt_version or "-"),
            "prompt_sha256": _optional(merged, "ai_prompt_sha256"),
            "prompt_store_date": _optional(merged, "ai_prompt_store_date"),
            "prompt_redacted": bool(merged.get("ai_prompt_redacted", False)),
            "prompt_replay_exact": bool(merged.get("ai_prompt_replay_exact", False)),
            "payload_sha256": _optional(merged, "ai_input_payload_sha256"),
            "payload_semantic_sha256": _optional(
                merged, "ai_input_payload_semantic_sha256"
            ),
            "payload_bytes": _safe_number(_optional(merged, "ai_input_payload_bytes")),
            "payload_store_date": _optional(merged, "ai_input_payload_store_date"),
            "request_envelope_sha256": _optional(merged, "ai_request_envelope_sha256"),
            "request_temperature": _safe_number(
                _optional(merged, "ai_request_temperature")
            ),
            "request_max_output_tokens": _safe_number(
                _optional(merged, "ai_request_max_output_tokens")
            ),
            "request_reasoning_effort": _optional(
                merged, "ai_request_reasoning_effort"
            ),
            "schema_name": _optional(
                merged, "ai_request_schema_name", "openai_schema_name"
            ),
            "require_json": _safe_bool(
                _optional(
                    merged,
                    "ai_request_require_json",
                    "openai_require_json",
                )
            ),
            "semantic_validator_version": _optional(
                merged, "semantic_validator_version"
            ),
            "expected_semantic_validator_version": _optional(
                merged, "expected_semantic_validator_version"
            ),
            "semantic_validator_applied": _safe_bool(
                _optional(merged, "semantic_validator_applied")
            ),
            "semantic_validation_status": _optional(
                merged, "semantic_validation_status"
            ),
            "holding_exact_replay_context_capture_status": _optional(
                merged, "holding_exact_replay_context_capture_status"
            ),
            "holding_exact_replay_context_capture_error_type": _optional(
                merged, "holding_exact_replay_context_capture_error_type"
            ),
            "holding_exact_replay_context_capture_latency_ms": _safe_number(
                _optional(
                    merged,
                    "holding_exact_replay_context_capture_latency_ms",
                )
            ),
            "request_capture_status": request_capture_status,
            "payload_redacted": bool(merged.get("ai_input_payload_redacted", False)),
            "payload_replay_exact": bool(
                merged.get("ai_input_payload_replay_exact", False)
            ),
            "replay_context_present": bool(
                merged.get("ai_replay_context_present", False)
            ),
            "replay_context_sha256": _optional(merged, "ai_replay_context_sha256"),
            "replay_context_semantic_sha256": _optional(
                merged, "ai_replay_context_semantic_sha256"
            ),
            "replay_context_bytes": _safe_number(
                _optional(merged, "ai_replay_context_bytes")
            ),
            "replay_context_redacted": bool(
                merged.get("ai_replay_context_redacted", False)
            ),
            "replay_context_exact": (
                bool(merged.get("ai_replay_context_exact"))
                if "ai_replay_context_exact" in merged
                else None
            ),
            "canonical_context_capture_status": _optional(
                merged, "ai_trace_canonical_context_capture_status"
            ),
            "canonical_context_schema": _optional(
                merged, "ai_trace_canonical_context_schema"
            ),
            "canonical_context_input_bundle_version": _optional(
                merged, "ai_trace_canonical_context_input_bundle_version"
            ),
            "canonical_context_raw_bar_count": _safe_number(
                _optional(merged, "ai_trace_canonical_context_raw_bar_count")
            ),
            "canonical_context_completed_bar_count": _safe_number(
                _optional(merged, "ai_trace_canonical_context_completed_bar_count")
            ),
            "canonical_context_forming_bar_present": (
                bool(merged.get("ai_trace_canonical_context_forming_bar_present"))
                if "ai_trace_canonical_context_forming_bar_present" in merged
                else None
            ),
            "canonical_context_candidate_status": _optional(
                merged, "ai_context_candidate_status"
            ),
            "canonical_context_candidate_schema": _optional(
                merged, "ai_context_candidate_schema"
            ),
            "canonical_context_application_state": _canonical_context_application_state(
                merged
            ),
            "provider_called": bool(provider_called),
            "transport": _optional(merged, "openai_transport_mode"),
            "response_ms": _safe_number(
                _optional(
                    merged,
                    "ai_response_ms",
                    "openai_ws_roundtrip_ms",
                    "bedrock_latency_ms",
                )
            ),
            "response_sha256": _optional(
                merged,
                "ai_response_sha256",
                "openai_response_sha256",
                "bedrock_response_sha256",
            )
            or decision_result_sha256,
            "input_tokens": _safe_number(
                _optional(
                    merged,
                    "openai_input_tokens",
                    "bedrock_input_tokens",
                )
            ),
            "output_tokens": _safe_number(
                _optional(
                    merged,
                    "openai_output_tokens",
                    "bedrock_output_tokens",
                )
            ),
            "total_tokens": _total_tokens(merged),
            "cache_hit": bool(merged.get("cache_hit", False)),
            "timeout": timeout_like,
            "parse_ok": bool(merged.get("ai_parse_ok", False)),
            "result_source": normalized_result_source,
            "attempt": _safe_number(merged.get("forensic_attempt")),
            "attempt_final": (
                bool(merged.get("forensic_attempt_final"))
                if "forensic_attempt_final" in merged
                else None
            ),
            "semantic_errors": (
                list(merged.get("forensic_semantic_errors") or [])
                if isinstance(merged.get("forensic_semantic_errors"), list)
                else []
            ),
            "entry_price_v2_5_contract_status": _optional(
                merged, "entry_price_v2_5_contract_status"
            ),
            "entry_price_v2_5_contract_errors": (
                [
                    str(error)
                    for error in merged.get("entry_price_v2_5_contract_errors") or []
                ]
                if isinstance(merged.get("entry_price_v2_5_contract_errors"), list)
                else []
            ),
            "entry_price_v1_contract_status": _optional(
                merged, "entry_price_v1_contract_status"
            ),
            "entry_price_v1_contract_errors": (
                [
                    str(error)
                    for error in merged.get("entry_price_v1_contract_errors") or []
                ]
                if isinstance(merged.get("entry_price_v1_contract_errors"), list)
                else []
            ),
            "decision_quality_contract_status": _optional(
                merged, "decision_quality_contract_status"
            ),
            "decision_quality_live_adapter": _optional(
                merged, "decision_quality_live_adapter"
            ),
            "decision_quality_contract_errors": (
                [
                    str(error)
                    for error in merged.get("decision_quality_contract_errors") or []
                ]
                if isinstance(merged.get("decision_quality_contract_errors"), list)
                else []
            ),
            "decision_quality_model_action": _optional(
                merged, "decision_quality_model_action"
            ),
            "decision_quality_model_edge_state": _optional(
                merged, "decision_quality_model_edge_state"
            ),
            "decision_quality_model_expected_upside_pct": _safe_number(
                merged.get("decision_quality_model_expected_upside_pct")
            ),
            "decision_quality_model_expected_downside_pct": _safe_number(
                merged.get("decision_quality_model_expected_downside_pct")
            ),
            "decision_quality_model_reason_codes": (
                [
                    str(code)
                    for code in merged.get("decision_quality_model_reason_codes") or []
                ]
                if isinstance(merged.get("decision_quality_model_reason_codes"), list)
                else []
            ),
            "decision_quality_model_evidence": (
                {
                    str(key): str(value)
                    for key, value in merged.get(
                        "decision_quality_model_evidence", {}
                    ).items()
                }
                if isinstance(merged.get("decision_quality_model_evidence"), dict)
                else {}
            ),
            "decision_quality_contract_repair_applied": bool(
                merged.get("decision_quality_contract_repair_applied", False)
            ),
            "decision_quality_contract_repair_codes": (
                [
                    str(code)
                    for code in merged.get("decision_quality_contract_repair_codes")
                    or []
                ]
                if isinstance(
                    merged.get("decision_quality_contract_repair_codes"), list
                )
                else []
            ),
            "decision_quality_contract_original_errors": (
                [
                    str(error)
                    for error in merged.get("decision_quality_contract_original_errors")
                    or []
                ]
                if isinstance(
                    merged.get("decision_quality_contract_original_errors"), list
                )
                else []
            ),
            "decision_quality_contract_invalid_reason_codes": (
                [
                    str(code)
                    for code in merged.get(
                        "decision_quality_contract_invalid_reason_codes"
                    )
                    or []
                ]
                if isinstance(
                    merged.get("decision_quality_contract_invalid_reason_codes"),
                    list,
                )
                else []
            ),
            "entry_setup_family": _optional(merged, "entry_setup_family"),
            "entry_setup_state": _optional(merged, "entry_setup_state"),
            "entry_structure_phase": _optional(merged, "entry_structure_phase"),
            "entry_structure_phase_policy_version": _optional(
                merged, "entry_structure_phase_policy_version"
            ),
            "entry_structure_phase_sha256": _optional(
                merged, "entry_structure_phase_sha256"
            ),
            "entry_structure_phase_bar_end": _optional(
                merged, "entry_structure_phase_bar_end"
            ),
            "entry_execution_readiness_state": _optional(
                merged, "entry_execution_readiness_state"
            ),
            "entry_ai_risk_verdict": _optional(merged, "entry_ai_risk_verdict"),
            "entry_ai_risk_codes": (
                [str(code) for code in merged.get("entry_ai_risk_codes") or []]
                if isinstance(merged.get("entry_ai_risk_codes"), list)
                else []
            ),
            "entry_ai_raw_risk_verdict": _optional(merged, "entry_ai_raw_risk_verdict"),
            "entry_ai_raw_risk_codes": (
                [str(code) for code in merged.get("entry_ai_raw_risk_codes") or []]
                if isinstance(merged.get("entry_ai_raw_risk_codes"), list)
                else []
            ),
            "entry_ai_raw_confidence": _optional(merged, "entry_ai_raw_confidence"),
            "entry_ai_raw_supporting_fact_ids": (
                [
                    str(value)
                    for value in merged.get("entry_ai_raw_supporting_fact_ids") or []
                ][:8]
                if isinstance(merged.get("entry_ai_raw_supporting_fact_ids"), list)
                else []
            ),
            "entry_ai_raw_contradicting_fact_ids": (
                [
                    str(value)
                    for value in merged.get("entry_ai_raw_contradicting_fact_ids") or []
                ][:8]
                if isinstance(merged.get("entry_ai_raw_contradicting_fact_ids"), list)
                else []
            ),
            "entry_ai_invalid_supporting_fact_ids": (
                [
                    str(value)
                    for value in merged.get("entry_ai_invalid_supporting_fact_ids")
                    or []
                ][:8]
                if isinstance(merged.get("entry_ai_invalid_supporting_fact_ids"), list)
                else []
            ),
            "entry_ai_invalid_contradicting_fact_ids": (
                [
                    str(value)
                    for value in merged.get("entry_ai_invalid_contradicting_fact_ids")
                    or []
                ][:8]
                if isinstance(
                    merged.get("entry_ai_invalid_contradicting_fact_ids"), list
                )
                else []
            ),
            "entry_ai_rejected_unexpected_fields": (
                [
                    str(value)
                    for value in merged.get("entry_ai_rejected_unexpected_fields") or []
                ][:12]
                if isinstance(merged.get("entry_ai_rejected_unexpected_fields"), list)
                else []
            ),
            "entry_ai_veto_corroborated": (
                bool(merged.get("entry_ai_veto_corroborated"))
                if "entry_ai_veto_corroborated" in merged
                else None
            ),
            "entry_setup_live_policy_status": _optional(
                merged, "entry_setup_live_policy_status"
            ),
            "entry_setup_live_policy_mode": _optional(
                merged, "entry_setup_live_policy_mode"
            ),
            "entry_setup_live_policy_max_daily_exploration_probes": _optional(
                merged, "entry_setup_live_policy_max_daily_exploration_probes"
            ),
            "entry_setup_live_policy_source_date": _optional(
                merged, "entry_setup_live_policy_source_date"
            ),
            "entry_setup_live_policy_target_date": _optional(
                merged, "entry_setup_live_policy_target_date"
            ),
            "entry_setup_live_policy_activation_sha256": _optional(
                merged, "entry_setup_live_policy_activation_sha256"
            ),
            "entry_setup_live_policy_candidate_contract_sha256": _optional(
                merged, "entry_setup_live_policy_candidate_contract_sha256"
            ),
            "entry_setup_live_policy_runtime_effect": (
                bool(merged.get("entry_setup_live_policy_runtime_effect"))
                if "entry_setup_live_policy_runtime_effect" in merged
                else None
            ),
            "main_ai_quality_live_policy_status": _optional(
                merged, "main_ai_quality_live_policy_status"
            ),
            "main_ai_quality_live_policy_target_date": _optional(
                merged, "main_ai_quality_live_policy_target_date"
            ),
            "main_ai_quality_live_policy_candidate_id": _optional(
                merged, "main_ai_quality_live_policy_candidate_id"
            ),
            "main_ai_quality_live_policy_candidate_sha256": _optional(
                merged, "main_ai_quality_live_policy_candidate_sha256"
            ),
            "main_ai_quality_live_policy_activation_sha256": _optional(
                merged, "main_ai_quality_live_policy_activation_sha256"
            ),
            "main_ai_quality_live_policy_runtime_effect": (
                bool(merged.get("main_ai_quality_live_policy_runtime_effect"))
                if "main_ai_quality_live_policy_runtime_effect" in merged
                else None
            ),
            "entry_probe_first_required": (
                bool(merged.get("entry_probe_first_required"))
                if "entry_probe_first_required" in merged
                else None
            ),
            "entry_ai_full_entry_forbidden": (
                bool(merged.get("entry_ai_full_entry_forbidden"))
                if "entry_ai_full_entry_forbidden" in merged
                else None
            ),
            "entry_probe_intent": (
                bool(merged.get("entry_probe_intent"))
                if "entry_probe_intent" in merged
                else None
            ),
            "entry_probe_intent_status": _optional(merged, "entry_probe_intent_status"),
            "entry_probe_intent_prompt_version": _optional(
                merged, "entry_probe_intent_prompt_version"
            ),
            "entry_probe_intent_eligibility_path": _optional(
                merged, "entry_probe_intent_eligibility_path"
            ),
            "entry_probe_intent_after_cost_reward_risk": _safe_number(
                _optional(merged, "entry_probe_intent_after_cost_reward_risk")
            ),
            "entry_probe_intent_rollback_condition": _optional(
                merged, "entry_probe_intent_rollback_condition"
            ),
            "entry_probe_intent_authority": _optional(
                merged, "entry_probe_intent_authority"
            ),
            "entry_probe_intent_submit_guard_required": (
                bool(merged.get("entry_probe_intent_submit_guard_required"))
                if "entry_probe_intent_submit_guard_required" in merged
                else None
            ),
            "entry_probe_intent_actual_order_submitted": (
                bool(merged.get("entry_probe_intent_actual_order_submitted"))
                if "entry_probe_intent_actual_order_submitted" in merged
                else None
            ),
            "entry_recent_exit_context_status": _optional(
                merged, "entry_recent_exit_context_status"
            ),
            "entry_recent_exit_probe_blocked": (
                bool(merged.get("entry_recent_exit_probe_blocked"))
                if "entry_recent_exit_probe_blocked" in merged
                else None
            ),
            "entry_recent_exit_price_vs_exit_pct": _safe_number(
                _optional(merged, "entry_recent_exit_price_vs_exit_pct")
            ),
            "action": _optional(
                merged, "action_v2", "action", "action_key", "action_label"
            ),
            "score": _safe_number(_optional(merged, "score", "ai_score")),
            "confidence": _safe_number(_optional(merged, "confidence")),
            "reason": str(_optional(merged, "reason", "report") or "")[:500],
            "reason_codes": _reason_codes(merged),
            "holding_score_model_action": _optional(
                merged, "holding_score_model_action"
            ),
            "holding_score_model_score": _safe_number(
                merged.get("holding_score_model_score")
            ),
            "holding_score_model_confidence": _safe_number(
                merged.get("holding_score_model_confidence")
            ),
            "holding_score_model_reason": str(
                merged.get("holding_score_model_reason") or ""
            )[:500],
            "holding_score_model_data_quality": _optional(
                merged, "holding_score_model_data_quality"
            ),
            "holding_score_effective_action": _optional(
                merged, "holding_score_effective_action"
            ),
            "holding_score_source_quality_override_applied": _safe_bool(
                merged.get("holding_score_source_quality_override_applied")
            ),
            "holding_score_source_quality_override_reason": _optional(
                merged, "holding_score_source_quality_override_reason"
            ),
            "holding_score_source_quality_override_blockers": (
                [
                    str(blocker)
                    for blocker in merged.get(
                        "holding_score_source_quality_override_blockers", []
                    )
                ]
                if isinstance(
                    merged.get("holding_score_source_quality_override_blockers"),
                    list,
                )
                else []
            ),
            "decision_result_sha256": decision_result_sha256,
            "parent_decision_trace_id": _optional(
                merged, "ai_decision_parent_trace_id"
            ),
            "parent_snapshot_id": _optional(
                merged, "ai_input_parent_snapshot_id", "parent_snapshot_id"
            ),
            "parent_source_event_stage": _optional(
                merged, "ai_parent_source_event_stage"
            ),
            "input_preflight_status": _optional(merged, "ai_input_preflight_status"),
            "input_preflight_mode": _optional(
                merged, "ai_input_runtime_preflight_mode"
            ),
            "input_preflight_allowed": preflight_allowed,
            "position_reconciliation_mode": _optional(
                merged, "ai_input_preflight_position_reconciliation_mode"
            ),
            "simulation_position_reconciled": (
                bool(merged.get("ai_input_preflight_simulation_position_reconciled"))
                if "ai_input_preflight_simulation_position_reconciled" in merged
                else None
            ),
            "input_blockers": merged.get("ai_input_preflight_blockers", []),
            "input_quality_warnings": merged.get(
                "ai_input_preflight_quality_warnings", []
            ),
            "missing_sources": merged.get("ai_input_preflight_missing_sources", []),
            "venue_consistent": (
                bool(merged.get("ai_input_preflight_venue_consistent"))
                if "ai_input_preflight_venue_consistent" in merged
                else None
            ),
            "max_source_skew_ms": _safe_number(
                merged.get("ai_input_preflight_max_source_skew_ms")
            ),
            "reference_price_type": (
                reference_price_type
                or (
                    "executable_ask"
                    if _optional(merged, "ai_trace_best_ask") is not None
                    else "best_available_input_price"
                )
            ),
            "reference_price": reference_price,
            "best_bid": _safe_number(_optional(merged, "ai_trace_best_bid")),
            "best_ask": _safe_number(_optional(merged, "ai_trace_best_ask")),
            "target_price": _safe_number(_optional(merged, "ai_trace_target_price")),
            "adverse_price": _safe_number(_optional(merged, "ai_trace_adverse_price")),
            "target_pct": _safe_number(_optional(merged, "ai_trace_target_pct")),
            "adverse_pct": _safe_number(_optional(merged, "ai_trace_adverse_pct")),
            "actual_order_authority": bool(merged.get("actual_order_authority", False)),
            "outcome_label_eligible": not outcome_label_exclusion_reasons,
            "outcome_label_exclusion_reasons": outcome_label_exclusion_reasons,
            **STORAGE_SECURITY_CONTRACT,
            **OBSERVATION_CONTRACT,
        }
        sanitized_trace_row, trace_redacted = _sanitize(trace_row)
        trace_row = dict(sanitized_trace_row)
        trace_row["trace_storage_redacted"] = bool(trace_redacted)
        pending_row = {
            "schema": OUTCOME_SCHEMA,
            "label_id": f"{trace_id}:v1",
            "decision_trace_id": trace_id,
            "label_version": 1,
            "created_at": now.isoformat(),
            "label_status": "pending",
            "decision_stage": stage,
            "stock_code": trace_row["stock_code"],
            "stock_identifier": trace_row["stock_identifier"],
            "decision_ts": trace_row["decision_ts"],
            "effective_venue": trace_row["effective_venue"],
            "session_bucket": trace_row["session_bucket"],
            "broker_route": trace_row["broker_route"],
            "market_data_route": trace_row["market_data_route"],
            "record_id": trace_row["record_id"],
            "recommendation_id": trace_row["recommendation_id"],
            "probe_bundle_id": trace_row["probe_bundle_id"],
            "position_cycle_id": trace_row["position_cycle_id"],
            "broker_order_no": trace_row["broker_order_no"],
            "snapshot_id": trace_row["snapshot_id"],
            "action": trace_row["action"],
            "score": trace_row["score"],
            "confidence": trace_row["confidence"],
            "reason_codes": trace_row["reason_codes"],
            "holding_score_model_action": trace_row["holding_score_model_action"],
            "holding_score_model_score": trace_row["holding_score_model_score"],
            "holding_score_model_confidence": trace_row[
                "holding_score_model_confidence"
            ],
            "holding_score_model_data_quality": trace_row[
                "holding_score_model_data_quality"
            ],
            "holding_score_effective_action": trace_row[
                "holding_score_effective_action"
            ],
            "holding_score_source_quality_override_applied": trace_row[
                "holding_score_source_quality_override_applied"
            ],
            "holding_score_source_quality_override_reason": trace_row[
                "holding_score_source_quality_override_reason"
            ],
            "holding_score_source_quality_override_blockers": trace_row[
                "holding_score_source_quality_override_blockers"
            ],
            "entry_setup_family": trace_row["entry_setup_family"],
            "entry_setup_state": trace_row["entry_setup_state"],
            "entry_structure_phase": trace_row["entry_structure_phase"],
            "entry_structure_phase_policy_version": trace_row[
                "entry_structure_phase_policy_version"
            ],
            "entry_structure_phase_sha256": trace_row["entry_structure_phase_sha256"],
            "entry_structure_phase_bar_end": trace_row["entry_structure_phase_bar_end"],
            "entry_execution_readiness_state": trace_row[
                "entry_execution_readiness_state"
            ],
            "entry_ai_risk_verdict": trace_row["entry_ai_risk_verdict"],
            "entry_ai_risk_codes": trace_row["entry_ai_risk_codes"],
            "entry_ai_veto_corroborated": trace_row["entry_ai_veto_corroborated"],
            "entry_setup_live_policy_status": trace_row[
                "entry_setup_live_policy_status"
            ],
            "entry_setup_live_policy_mode": trace_row["entry_setup_live_policy_mode"],
            "entry_setup_live_policy_max_daily_exploration_probes": trace_row[
                "entry_setup_live_policy_max_daily_exploration_probes"
            ],
            "entry_setup_live_policy_source_date": trace_row[
                "entry_setup_live_policy_source_date"
            ],
            "entry_setup_live_policy_target_date": trace_row[
                "entry_setup_live_policy_target_date"
            ],
            "entry_setup_live_policy_activation_sha256": trace_row[
                "entry_setup_live_policy_activation_sha256"
            ],
            "entry_setup_live_policy_candidate_contract_sha256": trace_row[
                "entry_setup_live_policy_candidate_contract_sha256"
            ],
            "entry_setup_live_policy_runtime_effect": trace_row[
                "entry_setup_live_policy_runtime_effect"
            ],
            "main_ai_quality_live_policy_status": trace_row[
                "main_ai_quality_live_policy_status"
            ],
            "main_ai_quality_live_policy_target_date": trace_row[
                "main_ai_quality_live_policy_target_date"
            ],
            "main_ai_quality_live_policy_candidate_id": trace_row[
                "main_ai_quality_live_policy_candidate_id"
            ],
            "main_ai_quality_live_policy_candidate_sha256": trace_row[
                "main_ai_quality_live_policy_candidate_sha256"
            ],
            "main_ai_quality_live_policy_activation_sha256": trace_row[
                "main_ai_quality_live_policy_activation_sha256"
            ],
            "main_ai_quality_live_policy_runtime_effect": trace_row[
                "main_ai_quality_live_policy_runtime_effect"
            ],
            "entry_probe_first_required": trace_row["entry_probe_first_required"],
            "entry_ai_full_entry_forbidden": trace_row["entry_ai_full_entry_forbidden"],
            "entry_probe_intent": trace_row["entry_probe_intent"],
            "entry_probe_intent_status": trace_row["entry_probe_intent_status"],
            "entry_probe_intent_prompt_version": trace_row[
                "entry_probe_intent_prompt_version"
            ],
            "entry_probe_intent_eligibility_path": trace_row[
                "entry_probe_intent_eligibility_path"
            ],
            "entry_probe_intent_after_cost_reward_risk": trace_row[
                "entry_probe_intent_after_cost_reward_risk"
            ],
            "entry_probe_intent_rollback_condition": trace_row[
                "entry_probe_intent_rollback_condition"
            ],
            "entry_probe_intent_authority": trace_row["entry_probe_intent_authority"],
            "entry_probe_intent_submit_guard_required": trace_row[
                "entry_probe_intent_submit_guard_required"
            ],
            "entry_probe_intent_actual_order_submitted": trace_row[
                "entry_probe_intent_actual_order_submitted"
            ],
            "entry_recent_exit_context_status": trace_row[
                "entry_recent_exit_context_status"
            ],
            "entry_recent_exit_probe_blocked": trace_row[
                "entry_recent_exit_probe_blocked"
            ],
            "entry_recent_exit_price_vs_exit_pct": trace_row[
                "entry_recent_exit_price_vs_exit_pct"
            ],
            "result_source": trace_row["result_source"],
            "input_preflight_status": trace_row["input_preflight_status"],
            "input_preflight_mode": trace_row["input_preflight_mode"],
            "input_quality_warnings": trace_row["input_quality_warnings"],
            "reference_price_type": trace_row["reference_price_type"],
            "reference_price": trace_row["reference_price"],
            "best_bid": trace_row["best_bid"],
            "best_ask": trace_row["best_ask"],
            "target_price": trace_row["target_price"],
            "adverse_price": trace_row["adverse_price"],
            "target_pct": trace_row["target_pct"],
            "adverse_pct": trace_row["adverse_pct"],
            "matured_horizons_min": [],
            "pending_horizons_min": list(OUTCOME_HORIZONS_MIN),
            "source_quality_status": (
                "pending_future_window"
                if trace_row["reference_price"] is not None
                else "pending_reference_price_gap"
            ),
            "invalid_reasons": (
                []
                if trace_row["reference_price"] is not None
                else ["reference_price_missing"]
            ),
            **STORAGE_SECURITY_CONTRACT,
            **OBSERVATION_CONTRACT,
        }
        with _WRITE_LOCK:
            seen = _SEEN_TRACE_IDS.get(target_date)
            if seen is None:
                path = _trace_path(target_date)
                seen = _load_seen(path, "decision_trace_id")
                _SEEN_TRACE_IDS[target_date] = seen
            if trace_id not in seen:
                _append_jsonl(_trace_path(target_date), trace_row)
                seen.add(trace_id)
            if trace_row["outcome_label_eligible"]:
                seen_outcomes = _SEEN_OUTCOME_LABEL_IDS.get(target_date)
                if seen_outcomes is None:
                    outcome_path = _outcome_path(target_date)
                    seen_outcomes = _load_seen(outcome_path, "label_id")
                    _SEEN_OUTCOME_LABEL_IDS[target_date] = seen_outcomes
                label_id = str(pending_row["label_id"])
                if label_id not in seen_outcomes:
                    _append_jsonl(_outcome_path(target_date), pending_row)
                    seen_outcomes.add(label_id)
        return {
            "ai_decision_trace_schema": TRACE_SCHEMA,
            "ai_decision_trace_id": trace_id,
            "ai_decision_outcome_label_status": (
                "pending"
                if trace_row["outcome_label_eligible"]
                else (
                    "not_applicable_input_preflight_blocked"
                    if any(
                        reason.startswith("input_preflight_")
                        for reason in trace_row["outcome_label_exclusion_reasons"]
                    )
                    else (
                        "not_applicable_provider_not_called"
                        if "provider_not_called"
                        in trace_row["outcome_label_exclusion_reasons"]
                        else "not_applicable_rejected_attempt"
                    )
                )
            ),
            "ai_decision_outcome_label_exclusion_reasons": trace_row[
                "outcome_label_exclusion_reasons"
            ],
        }
    except Exception as exc:
        log_error(f"[AI_DECISION_TRACE] decision append failed: {exc}")
        return {}
