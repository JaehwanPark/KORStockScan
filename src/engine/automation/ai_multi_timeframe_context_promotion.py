"""Binary PREMARKET promotion for the shared scalping AI context bundle.

The promotion commit marker is written last. Runtime consumers trust only that
marker, so partially written env files cannot activate the context. This module
changes AI input inclusion only; it has no order, threshold, provider, sizing,
broker-guard, or bot-process authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import tempfile
from collections import Counter
from datetime import datetime, time
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import open_text_auto

KST = ZoneInfo("Asia/Seoul")
REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "ai_multi_timeframe_context_promotion_v1"
OBSERVATION_SCHEMA = "ai_multi_timeframe_context_first_observation_v1"
AUTHORITY_ID = "operator_full_market_context_promotion_2026-07-27"
FAMILY = "scalping_multi_timeframe_context_v1"
PROMOTION_DIR = DATA_DIR / "runtime"
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
VALIDATION_DIR = DATA_DIR / "report" / "ai_input_external_validation"
TRACE_DIR = DATA_DIR / "ai_decision_trace"
PAYLOAD_DIR = DATA_DIR / "ai_decision_payloads"

EXPECTED_ENDPOINTS = (
    "analyze_target",
    "entry_price",
    "realtime_report",
    "holding_score",
    "holding_flow",
    "overnight",
)
REQUIRED_VALIDATION_ENDPOINTS = (
    "analyze_target",
    "entry_price",
    "holding_score",
    "holding_flow",
)
EXPECTED_SESSIONS = (
    "PREMARKET_KRX_LIKE",
    "KRX_REGULAR",
    "NXT_REGULAR_OVERLAP",
    "NXT_AFTERMARKET",
)
REQUIRED_REVIEW_CHECKS = ("tests", "compile", "diff_check")
PREMARKET_REVIEW_START = time(8, 20)
PREMARKET_REVIEW_END = time(8, 40)
PREMARKET_APPLY_END = time(9, 0)
REVIEWED_SOURCE_FILES = (
    "src/engine/automation/ai_multi_timeframe_context_promotion.py",
    "src/engine/ai_engine_openai.py",
    "src/engine/scalping/multi_timeframe_context.py",
    "src/engine/scalping/entry_candle_context.py",
    "src/engine/scalping/holding_decision_context.py",
    "src/engine/scalping/ai_decision_trace.py",
    "src/engine/scalping/ai_decision_quality.py",
    "src/engine/scalping/ai_input_external_validation.py",
    "src/engine/ai_prompt_contracts.py",
)

PROMOTION_CONTRACT = {
    "metric_role": "ai_input_runtime_promotion_gate",
    "decision_authority": "operator_authorized_binary_context_inclusion_only",
    "window_policy": "target_date_premarket_exact_validation",
    "sample_floor": "one_valid_exact_request_per_required_symbol_route",
    "primary_decision_metric": "required_source_field_match_status",
    "source_quality_gate": "fresh_same_basis_conflict_free_completed_bar",
    "runtime_effect": True,
    "allowed_runtime_apply": True,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "partial_canary_or_endpoint_limited_rollout",
        "threshold_or_score_change",
        "provider_or_model_change",
        "order_price_quantity_or_cap_change",
        "broker_account_order_cooldown_guard_change",
        "hard_protect_emergency_safety_change",
        "bot_restart",
    ],
}

OBSERVATION_CONTRACT = {
    "metric_role": "ai_input_post_promotion_observation",
    "decision_authority": "context_only_rollback_observation",
    "window_policy": "first_natural_call_per_endpoint_venue_session",
    "sample_floor": "one_natural_call_per_applicable_endpoint",
    "primary_decision_metric": "exact_promoted_payload_contract_status",
    "source_quality_gate": "fresh_same_route_completed_bar_exact_payload",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "threshold_or_provider_change",
        "order_or_quantity_change",
        "broker_or_safety_guard_change",
        "bot_restart",
    ],
}


def promotion_path(target_date: str) -> Path:
    return PROMOTION_DIR / f"ai_multi_timeframe_context_promotion_{target_date}.json"


def review_path(target_date: str) -> Path:
    return PROMOTION_DIR / f"ai_multi_timeframe_context_review_{target_date}.json"


def observation_path(target_date: str) -> Path:
    return PROMOTION_DIR / (
        f"ai_multi_timeframe_context_first_observation_{target_date}.json"
    )


def runtime_manifest_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"


def runtime_env_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.env"


def validation_path(target_date: str) -> Path:
    return VALIDATION_DIR / f"ai_input_external_validation_{target_date}.json"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        value if isinstance(value, bytes) else _canonical_bytes(value)
    ).hexdigest()


def reviewed_source_hash() -> str:
    digest = hashlib.sha256()
    for relative_path in REVIEWED_SOURCE_FILES:
        path = REPO_ROOT / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"))


def full_market_env(target_date: str) -> dict[str, str]:
    return {
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_PREMARKET_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_KRX_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_NXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_PREMARKET_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_KRX_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_NXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_SCORE_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_HOLDING_FLOW_CONTEXT_ENABLED": "true",
        "KORSTOCKSCAN_OVERNIGHT_CONTEXT_ENABLED": "true",
    }


def context_only_rollback_env(target_date: str) -> dict[str, str]:
    return {
        **{
            key: "false"
            for key in full_market_env(target_date)
            if not key.endswith("_ACTIVE_DATE")
        },
        "KORSTOCKSCAN_MULTI_TIMEFRAME_AI_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_ENTRY_CANDLE_CONTEXT_ACTIVE_DATE": target_date,
        "KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ACTIVE_DATE": target_date,
    }


def _validation_findings(
    validation: dict[str, Any],
    target_date: str,
    required_symbols: Iterable[str],
) -> list[str]:
    findings: list[str] = []
    if validation.get("schema") != "ai_input_external_validation_v1":
        findings.append("validation_schema_invalid")
    if str(validation.get("date") or "") != target_date:
        findings.append("validation_target_date_mismatch")
    if validation.get("status") != "pass":
        findings.append("validation_status_not_pass")
    summary = validation.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    for field in (
        "mismatch_count",
        "payload_mismatch_count",
        "payload_source_unavailable_count",
        "provider_none_count",
    ):
        if int(summary.get(field) or 0) != 0:
            findings.append(f"validation_{field}_nonzero")
    results = {
        str(row.get("symbol") or ""): row
        for row in validation.get("results") or []
        if isinstance(row, dict)
    }
    endpoint_counts: Counter[str] = Counter()
    for symbol in required_symbols:
        row = results.get(symbol)
        if row is None:
            findings.append(f"required_symbol_missing:{symbol}")
            continue
        source_summary = row.get("summary")
        source_summary = source_summary if isinstance(source_summary, dict) else {}
        exact = row.get("ai_payload_exact_validation")
        exact = exact if isinstance(exact, dict) else {}
        exact_summary = exact.get("summary")
        exact_summary = exact_summary if isinstance(exact_summary, dict) else {}
        if source_summary.get("required_source_field_match_status") != "pass":
            findings.append(f"source_match_failed:{symbol}")
        if exact_summary.get("required_payload_match_status") != "pass":
            findings.append(f"payload_match_failed:{symbol}")
        if int(exact_summary.get("request_count") or 0) < 1:
            findings.append(f"exact_request_missing:{symbol}")
        endpoint_counts.update(
            {
                str(endpoint): int(count or 0)
                for endpoint, count in (
                    exact_summary.get("endpoint_counts") or {}
                ).items()
            }
        )
        if int(exact_summary.get("forming_bar_included_count") or 0) != 0:
            findings.append(f"forming_bar_included:{symbol}")
    for endpoint in REQUIRED_VALIDATION_ENDPOINTS:
        if endpoint_counts[endpoint] < 1:
            findings.append(f"required_endpoint_exact_request_missing:{endpoint}")
    return findings


def _review_findings(review: dict[str, Any], target_date: str) -> list[str]:
    findings: list[str] = []
    if str(review.get("target_date") or "") != target_date:
        findings.append("review_target_date_mismatch")
    if review.get("status") != "pass":
        findings.append("review_status_not_pass")
    if int(review.get("finding_count") or 0) != 0:
        findings.append("review_findings_nonzero")
    if review.get("operator_authorization_id") != AUTHORITY_ID:
        findings.append("operator_authorization_missing")
    if not _parse_ts(review.get("reviewed_at")):
        findings.append("review_timestamp_invalid")
    if review.get("reviewed_source_hash") != reviewed_source_hash():
        findings.append("reviewed_source_hash_mismatch")
    checks = review.get("checks")
    checks = checks if isinstance(checks, dict) else {}
    for name in REQUIRED_REVIEW_CHECKS:
        if checks.get(name) != "pass":
            findings.append(f"review_check_not_pass:{name}")
    return findings


def _promotion_window_status(target_date: str, now: datetime) -> str:
    current = now.astimezone(KST)
    try:
        target = current.date().fromisoformat(target_date)
    except ValueError:
        return "target_date_invalid"
    if current.date() < target or (
        current.date() == target and current.time() < PREMARKET_REVIEW_START
    ):
        return "not_yet_due"
    if current.date() > target or current.time() > PREMARKET_REVIEW_END:
        return "premarket_validation_window_closed"
    return "pass"


def evaluate_promotion(
    *,
    target_date: str,
    validation: dict[str, Any],
    review: dict[str, Any],
    runtime_manifest: dict[str, Any],
    runtime_verify: dict[str, Any],
    required_symbols: Iterable[str] = ("005930", "096770", "100090", "005930_NX"),
    now: datetime | None = None,
) -> dict[str, Any]:
    evaluated_at = now or datetime.now(KST)
    window_status = _promotion_window_status(target_date, evaluated_at)
    findings = [
        *_validation_findings(validation, target_date, required_symbols),
        *_review_findings(review, target_date),
    ]
    if window_status != "pass":
        findings.append(window_status)
    if str(runtime_manifest.get("target_date") or "") != target_date:
        findings.append("runtime_manifest_target_date_mismatch")
    if runtime_verify.get("status") != "pass" or runtime_verify.get("passed") is False:
        findings.append("runtime_env_verify_not_pass")
    if findings:
        if window_status == "not_yet_due":
            decision = "not_yet_due"
        elif any(
            "provider" in item or "payload" in item or "endpoint" in item
            for item in findings
        ):
            decision = "blocked_provider_or_schema"
        elif any("runtime" in item for item in findings):
            decision = "blocked_runtime_hook_missing"
        elif any("review" in item or "authorization" in item for item in findings):
            decision = "blocked_review_or_env"
        else:
            decision = "blocked_source_quality"
    else:
        decision = "promoted_all_market_sessions_full"
    generated_at = evaluated_at.astimezone(KST).isoformat()
    env = full_market_env(target_date) if not findings else {}
    return {
        "schema": SCHEMA,
        "target_date": target_date,
        "generated_at": generated_at,
        "promoted_at": generated_at if not findings else None,
        "promotion_window_status": window_status,
        "status": "pass" if not findings else "fail",
        "decision": decision,
        "runtime_activation": not findings,
        "operator_authorization_id": AUTHORITY_ID,
        "input_preflight_mode": "exact_v2",
        "entry_context_schema": "entry_candle_context_v1",
        "holding_context_schema": "holding_decision_context_v1",
        "input_bundle_version": FAMILY,
        "scope": {
            "symbols": "all_scalping_symbols",
            "sessions": list(EXPECTED_SESSIONS),
            "endpoints": list(EXPECTED_ENDPOINTS),
            "rollout": "binary_full_market_no_canary_no_partial_cohort",
        },
        "findings": findings,
        "env_overrides": env,
        "rollback_env_overrides": context_only_rollback_env(target_date),
        "source_hashes": {
            "validation_sha256": _sha256(validation),
            "review_sha256": _sha256(review),
            "runtime_manifest_sha256": _sha256(runtime_manifest),
            "runtime_verify_sha256": _sha256(runtime_verify),
        },
        "post_apply_observation_hook": str(observation_path(target_date)),
        **PROMOTION_CONTRACT,
    }


def _env_file_bytes(
    target_date: str,
    manifest: dict[str, Any],
    env_overrides: dict[str, Any],
) -> bytes:
    lines = [
        "# Generated by threshold_cycle_preopen_apply.py",
        f"# target_date={target_date}",
        f"# source_date={manifest.get('source_date')}",
        f"# generated_at={manifest.get('generated_at')}",
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true",
        f"export KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE={shlex.quote(target_date)}",
    ]
    for key in sorted(env_overrides):
        lines.append(f"export {key}={shlex.quote(str(env_overrides[key]))}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def apply_promotion_transaction(
    report: dict[str, Any],
    runtime_manifest: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Commit env files first and the trusted activation marker last."""

    if report.get("decision") != "promoted_all_market_sessions_full" or not report.get(
        "runtime_activation"
    ):
        raise ValueError("promotion report is not authorized")
    target_date = str(report["target_date"])
    applied_at = (now or datetime.now(KST)).astimezone(KST)
    if report.get("promotion_window_status") != "pass":
        raise ValueError("promotion report was not evaluated in PREMARKET")
    if (
        applied_at.date().isoformat() != target_date
        or applied_at.time() < PREMARKET_REVIEW_START
        or applied_at.time() >= PREMARKET_APPLY_END
    ):
        raise ValueError("promotion apply is outside the target-date PREMARKET window")
    manifest_path = runtime_manifest_path(target_date)
    env_path = runtime_env_path(target_date)
    artifact_path = promotion_path(target_date)
    original = {
        path: path.read_bytes() if path.exists() else None
        for path in (manifest_path, env_path, artifact_path)
    }
    env_overrides = dict(runtime_manifest.get("env_overrides") or {})
    env_overrides.update(report["env_overrides"])
    promoted_manifest = {
        **runtime_manifest,
        "env_overrides": env_overrides,
        "ai_multi_timeframe_context_promotion": str(artifact_path),
        "ai_multi_timeframe_context_promotion_status": report["decision"],
    }
    manifest_bytes = json.dumps(promoted_manifest, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    env_bytes = _env_file_bytes(target_date, promoted_manifest, env_overrides)
    committed_report = {
        **report,
        "runtime_manifest_path": str(manifest_path),
        "runtime_env_path": str(env_path),
        "runtime_manifest_sha256": _sha256(manifest_bytes),
        "runtime_env_sha256": _sha256(env_bytes),
        "transaction_status": "committed",
    }
    try:
        _atomic_write(env_path, env_bytes)
        _atomic_write(manifest_path, manifest_bytes)
        _atomic_write_json(artifact_path, committed_report)
    except Exception:
        for path, content in original.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, content)
        raise
    return committed_report


def rollback_context_transaction(
    *,
    target_date: str,
    observation: dict[str, Any],
) -> dict[str, Any]:
    """Disable only the promoted context and invalidate the runtime commit marker."""

    if observation.get("rollback_required") is not True:
        raise ValueError("observation does not authorize context rollback")
    artifact_path = promotion_path(target_date)
    current = _load_json(artifact_path)
    if current.get("decision") != "promoted_all_market_sessions_full":
        raise ValueError("active full-market promotion is missing")
    manifest_path = runtime_manifest_path(target_date)
    env_path = runtime_env_path(target_date)
    runtime_manifest = _load_json(manifest_path)
    if str(runtime_manifest.get("target_date") or "") != target_date:
        raise ValueError("runtime manifest target date mismatch")
    original = {
        path: path.read_bytes() if path.exists() else None
        for path in (manifest_path, env_path, artifact_path)
    }
    env_overrides = dict(runtime_manifest.get("env_overrides") or {})
    env_overrides.update(current.get("rollback_env_overrides") or {})
    rolled_manifest = {
        **runtime_manifest,
        "env_overrides": env_overrides,
        "ai_multi_timeframe_context_promotion_status": "rolled_back_context_only",
    }
    manifest_bytes = json.dumps(rolled_manifest, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    env_bytes = _env_file_bytes(target_date, rolled_manifest, env_overrides)
    rolled_artifact = {
        **current,
        "status": "fail",
        "decision": "rolled_back_context_only",
        "runtime_activation": False,
        "transaction_status": "rolled_back",
        "rolled_back_at": datetime.now(KST).isoformat(),
        "rollback_reason_artifact": str(observation_path(target_date)),
        "rollback_reason_sha256": _sha256(observation),
        "runtime_manifest_sha256": _sha256(manifest_bytes),
        "runtime_env_sha256": _sha256(env_bytes),
    }
    try:
        _atomic_write(env_path, env_bytes)
        _atomic_write(manifest_path, manifest_bytes)
        _atomic_write_json(artifact_path, rolled_artifact)
    except Exception:
        for path, content in original.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, content)
        raise
    return rolled_artifact


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with open_text_auto(path) as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _trace_sort_key(row: dict[str, Any]) -> datetime:
    return _parse_ts(row.get("decision_ts")) or datetime.max.replace(tzinfo=KST)


def _source_quality_conflicted(value: Any) -> bool:
    bad_tokens = {"conflict", "conflicted", "duplicate", "duplicated", "invalid"}
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if any(token in normalized_key for token in bad_tokens):
                if isinstance(child, bool) and child:
                    return True
                try:
                    if "count" in normalized_key and float(child) > 0:
                        return True
                except (TypeError, ValueError):
                    pass
            if normalized_key in {
                "status",
                "quality",
                "source_quality",
                "reason",
                "state",
            }:
                normalized_value = str(child or "").strip().lower()
                if normalized_value in bad_tokens or any(
                    normalized_value.startswith(f"{token}:") for token in bad_tokens
                ):
                    return True
            if _source_quality_conflicted(child):
                return True
        return False
    if isinstance(value, list):
        return any(_source_quality_conflicted(child) for child in value)
    return False


def _payload_context_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    schemas: set[str] = set()
    bundle_versions: set[str] = set()
    venues: set[str] = set()
    forming = False
    conflicts: list[str] = []
    for item in _walk(payload.get("sanitized_user_input")):
        if not isinstance(item, dict):
            continue
        schema = str(item.get("schema") or "")
        if schema in {"entry_candle_context_v1", "holding_decision_context_v1"}:
            schemas.add(schema)
            if item.get("venue"):
                venues.add(str(item["venue"]).upper())
        bundle = str(item.get("input_bundle_version") or "")
        if bundle:
            bundle_versions.add(bundle)
            multi = item.get("multi_timeframe_context")
            multi = multi if isinstance(multi, dict) else item
            for derived_item in _walk(multi):
                if not isinstance(derived_item, dict):
                    continue
                if (
                    derived_item.get("forming") is True
                    or derived_item.get("partial_volume") is True
                ):
                    forming = True
            if _source_quality_conflicted(multi.get("source_quality")):
                conflicts.append("source_quality_conflict")
    return {
        "context_schemas": sorted(schemas),
        "input_bundle_versions": sorted(bundle_versions),
        "context_venues": sorted(venues),
        "forming_or_partial_bar_present": forming,
        "source_quality_conflicts": sorted(set(conflicts)),
    }


def build_first_observation_report(
    *,
    target_date: str,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        promotion.get("decision") != "promoted_all_market_sessions_full"
        or promotion.get("runtime_activation") is not True
        or promotion.get("transaction_status") != "committed"
    ):
        return {
            "schema": OBSERVATION_SCHEMA,
            "target_date": target_date,
            "generated_at": datetime.now(KST).isoformat(),
            "status": "promotion_not_authorized",
            "observations": [],
            **OBSERVATION_CONTRACT,
        }
    promoted_at = _parse_ts(promotion.get("promoted_at"))
    payload_by_key = {
        (str(row.get("payload_sha256")), str(row.get("endpoint") or "")): row
        for row in payloads
        if row.get("payload_sha256")
    }
    payload_hash_counts = Counter(
        str(row.get("payload_sha256")) for row in payloads if row.get("payload_sha256")
    )
    payload_by_unique_hash = {
        str(row.get("payload_sha256")): row
        for row in payloads
        if row.get("payload_sha256")
        and payload_hash_counts[str(row.get("payload_sha256"))] == 1
    }
    first: dict[tuple[str, str, str], dict[str, Any]] = {}
    for trace in sorted(traces, key=_trace_sort_key):
        decision_ts = _parse_ts(trace.get("decision_ts"))
        if promoted_at and (not decision_ts or decision_ts < promoted_at):
            continue
        endpoint = str(trace.get("endpoint") or "")
        if endpoint not in EXPECTED_ENDPOINTS:
            continue
        venue = str(trace.get("effective_venue") or "UNKNOWN").upper()
        session = str(trace.get("session_bucket") or "UNKNOWN").upper()
        key = (endpoint, venue, session)
        if key in first:
            continue
        payload_hash = str(trace.get("payload_sha256") or "")
        payload = payload_by_key.get(
            (payload_hash, endpoint),
            payload_by_unique_hash.get(payload_hash, {}),
        )
        evidence = _payload_context_evidence(payload)
        violations: list[str] = []
        expected_schema = (
            "entry_candle_context_v1"
            if endpoint in {"analyze_target", "entry_price", "realtime_report"}
            else "holding_decision_context_v1"
        )
        if expected_schema not in evidence["context_schemas"]:
            violations.append("stage_context_schema_missing")
        if FAMILY not in evidence["input_bundle_versions"]:
            violations.append("multi_timeframe_bundle_missing")
        if evidence["forming_or_partial_bar_present"]:
            violations.append("forming_or_partial_bar_present")
        if evidence["source_quality_conflicts"]:
            violations.append("source_quality_conflict")
        provider = str(trace.get("provider_actual") or "none").lower()
        if provider == "none":
            violations.append("provider_none")
        if not trace.get("payload_replay_exact"):
            violations.append("payload_not_exact")
        if not trace.get("payload_sha256"):
            violations.append("payload_hash_missing")
        if not trace.get("response_sha256"):
            violations.append("response_hash_missing")
        context_venues = set(evidence["context_venues"])
        if context_venues and venue not in context_venues:
            if not (venue == "PREMARKET_KRX_LIKE" and context_venues == {"NXT"}):
                violations.append("cross_venue_context")
        first[key] = {
            "endpoint": endpoint,
            "effective_venue": venue,
            "session_bucket": session,
            "decision_trace_id": trace.get("decision_trace_id"),
            "payload_sha256": trace.get("payload_sha256"),
            "response_sha256": trace.get("response_sha256"),
            "provider_actual": provider,
            "status": "pass" if not violations else "fail",
            "violations": violations,
            **evidence,
        }
    observed_endpoints = {key[0] for key in first}
    observed_sessions = {key[2] for key in first}
    pending = [
        endpoint
        for endpoint in EXPECTED_ENDPOINTS
        if endpoint not in observed_endpoints
    ]
    pending_sessions = [
        session for session in EXPECTED_SESSIONS if session not in observed_sessions
    ]
    failed = [row for row in first.values() if row["status"] == "fail"]
    status = (
        "rolled_back_context_only"
        if failed
        else (
            "all_market_first_observation_pass"
            if not pending and not pending_sessions
            else "global_runtime_full_pending_natural_endpoint"
        )
    )
    return {
        "schema": OBSERVATION_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "promotion_artifact": str(promotion_path(target_date)),
        "promotion_sha256": _sha256(promotion),
        "observations": list(first.values()),
        "pending_natural_endpoints": pending,
        "pending_natural_sessions": pending_sessions,
        "failed_observation_count": len(failed),
        "rollback_required": bool(failed),
        "rollback_scope": "multi_timeframe_context_only" if failed else None,
        **OBSERVATION_CONTRACT,
    }


def write_first_observation_report(target_date: str) -> dict[str, Any]:
    report = build_first_observation_report(
        target_date=target_date,
        promotion=_load_json(promotion_path(target_date)),
        traces=_iter_jsonl(TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl"),
        payloads=_iter_jsonl(PAYLOAD_DIR / f"ai_decision_payloads_{target_date}.jsonl"),
    )
    _atomic_write_json(observation_path(target_date), report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote or observe the binary full-market scalping AI context."
    )
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--mode",
        choices=("evaluate", "apply", "observe", "rollback"),
        default="evaluate",
    )
    parser.add_argument("--review-artifact")
    parser.add_argument("--runtime-verify")
    parser.add_argument("--required-symbols", default="005930,096770,100090,005930_NX")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.mode in {"observe", "rollback"}:
        report = write_first_observation_report(args.date)
        if args.mode == "rollback" and report.get("rollback_required") is True:
            report = rollback_context_transaction(
                target_date=args.date, observation=report
            )
        print(json.dumps(report, ensure_ascii=False))
        if args.mode == "rollback":
            return 0 if report.get("decision") == "rolled_back_context_only" else 1
        return 1 if report.get("rollback_required") else 0
    review = _load_json(
        Path(args.review_artifact) if args.review_artifact else review_path(args.date)
    )
    runtime_verify_file = (
        Path(args.runtime_verify)
        if args.runtime_verify
        else RUNTIME_ENV_DIR / f"threshold_runtime_env_verify_{args.date}.json"
    )
    manifest = _load_json(runtime_manifest_path(args.date))
    report = evaluate_promotion(
        target_date=args.date,
        validation=_load_json(validation_path(args.date)),
        review=review,
        runtime_manifest=manifest,
        runtime_verify=_load_json(runtime_verify_file),
        required_symbols=[
            item.strip() for item in args.required_symbols.split(",") if item.strip()
        ],
    )
    if args.mode == "apply" and report.get("status") == "pass":
        report = apply_promotion_transaction(report, manifest)
    elif args.write:
        _atomic_write_json(promotion_path(args.date), report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
