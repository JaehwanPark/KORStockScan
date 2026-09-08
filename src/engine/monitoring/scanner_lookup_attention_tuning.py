"""Postclose auto-promotion for the scanner lookup-attention weight.

The producer joins an exact scanner promotion to a broker-receipt-confirmed
full fill and a completed main-scalping lifecycle.  It first arms a forward
holdout without runtime effect, then requires an independent future sample
before emitting bounded next-PREOPEN runtime authority.

The resulting policy only adds a score inside the candidate's existing
scanner priority tier.  It cannot change eligibility, slots, order ownership,
prices, quantity, providers, or safety guards.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta
import gzip
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.engine.scalping.scanner_lookup_attention_policy import (
    ACTIVATION_MODE,
    LEGACY_ACTIVATION_MODE,
    DECISION_AUTHORITY,
    DECISION_CONTRACT_VERSION,
    LEGACY_DECISION_CONTRACT_VERSION,
    ELIGIBLE_SESSION_BUCKETS,
    ELIGIBLE_VENUES,
    MAX_FUTURE_SKEW_SEC,
    MAX_BONUS_POINTS,
    MAX_SOURCE_AGE_SEC,
    MAX_TAIL_DEGRADATION_PCT,
    MIN_COHORT_COMPLETED,
    MIN_COHORT_DATES,
    MIN_EV_UPLIFT_PCT,
    NET_ECONOMIC_CONTRACT,
    NET_ECONOMIC_EFFECTIVE_FROM,
    net_edge_reasons,
    MIN_SCORE,
    MIN_TOTAL_COMPLETED,
    MIN_TRADING_DATES,
    MIN_WORST_NET_RETURN_PCT,
    POLICY_DIR,
    PREOPEN_DIR,
    POLICY_VERSION,
    REPORT_TYPE as POLICY_REPORT_TYPE,
    SCHEMA_VERSION as POLICY_SCHEMA_VERSION,
    USER_AUTHORITY,
    TUNING_REPORT_SCHEMA_VERSION,
    canonical_sha256,
    validate_policy_payload,
    load_active_policy,
)
from src.utils.market_day import count_krx_trading_days, is_krx_trading_day
from src.engine.scalping.scanner_lookup_attention_resource import (
    allocation_book,
    compact_evidence_rows,
    event_row as parse_resource_event,
    valid_row as valid_resource_row,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVENT_DIR = PROJECT_ROOT / "data" / "pipeline_events"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "scanner_lookup_attention_tuning"
SOURCE_AUDIT_DIR = PROJECT_ROOT / "data" / "report" / "observation_source_quality_audit"
SYMBOL_MASTER_DIR = (
    PROJECT_ROOT / "data" / "report" / "micro_reversion_economic_reference"
)
REPORT_TYPE = "scanner_lookup_attention_tuning"
SCHEMA_VERSION = TUNING_REPORT_SCHEMA_VERSION
ROLLOUT_DATE = date(2026, 9, 2)
ROLLING_CALENDAR_DAYS = 90
COST_EFFECTIVE_FROM = date(2026, 8, 18)
COST_CONTRACT = {
    "contract_version": "scanner_lookup_attention_fixed_comparison_cost_v1",
    "effective_from": COST_EFFECTIVE_FROM.isoformat(),
    "buy_fee_bps": 1.5,
    "sell_fee_bps": 1.5,
    "statutory_sell_tax_bps": 20.0,
    "provider_cost_krw": 0.0,
}
FULL_FILL_CONTRACT = (
    "position_rebased_after_fill:buy_side:FULL_FILL;requested=filled;remaining=0;"
    "receipt_quantity_contract_complete=true;same_trade_date_venue_session=true"
)
FORBIDDEN_USES = [
    "priority_tier_or_slot_ownership_change",
    "candidate_pool_or_source_eligibility_change",
    "buy_drop_threshold_or_provider_change",
    "order_price_quantity_cap_or_broker_guard_change",
    "stale_conflict_or_hard_safety_bypass",
]
RESOURCE_CAPACITY_PRUNE_REASONS = {
    "general_slot_limit",
    "market_gainer_reserved_full",
    "max_new_codes_reached",
    "no_remaining_capacity",
    "owner_quota",
    "promotion_partition_capacity_satisfied",
    "replacement_probe_rank_cutoff",
    "reserved_limit_down_capacity",
}
KST = ZoneInfo("Asia/Seoul")


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _strict_int(value: Any) -> int | None:
    """Parse an integer without silently truncating a fractional quantity/id."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() else None
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?\d+", text):
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true"}:
        return True
    if normalized in {"0", "false"}:
        return False
    return None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    )


def _event_path(day: date) -> Path | None:
    raw = EVENT_DIR / f"pipeline_events_{day.isoformat()}.jsonl"
    compressed = raw.with_suffix(raw.suffix + ".gz")
    if raw.exists():
        return raw
    return compressed if compressed.exists() else None


def _iter_events(
    path: Path, *, parse_stats: dict[str, int] | None = None
) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if parse_stats is not None:
                    parse_stats["malformed_json_line_count"] += 1
                continue
            if isinstance(row, dict):
                yield row
            elif parse_stats is not None:
                parse_stats["non_object_json_line_count"] += 1


def _observation_key(fields: dict[str, Any], stock_code: Any) -> tuple[int, str, str]:
    return (
        _strict_int(
            fields.get("runtime_record_id") or fields.get("main_lifecycle_record_id")
        )
        or 0,
        str(
            fields.get("scanner_promotion_id")
            or fields.get("main_lifecycle_attempt_id")
            or fields.get("attempt_id")
            or ""
        ).strip(),
        str(stock_code or "").strip()[:6],
    )


def _source_age_sec(event: dict[str, Any], fields: dict[str, Any]) -> float | None:
    emitted_date = str(event.get("emitted_date") or "")
    source_date = str(fields.get("realtime_lookup_source_date") or "")
    source_time = str(fields.get("realtime_lookup_source_time") or "")
    try:
        source_at = datetime.strptime(
            source_date + source_time, "%Y%m%d%H%M%S"
        ).replace(tzinfo=KST)
        emitted_at = datetime.fromisoformat(str(event.get("emitted_at") or ""))
    except ValueError:
        return None
    if emitted_at.tzinfo is None:
        emitted_at = emitted_at.replace(tzinfo=KST)
    else:
        emitted_at = emitted_at.astimezone(KST)
    if (
        source_date != emitted_date.replace("-", "")
        or emitted_at.date().isoformat() != emitted_date
    ):
        return None
    return (emitted_at - source_at).total_seconds()


def _source_timestamp_valid(event: dict[str, Any], fields: dict[str, Any]) -> bool:
    age_sec = _source_age_sec(event, fields)
    return bool(
        age_sec is not None and -MAX_FUTURE_SKEW_SEC <= age_sec <= MAX_SOURCE_AGE_SEC
    )


def _receipt_side(fields: dict[str, Any]) -> str:
    side_text = str(fields.get("905") or fields.get("order_side") or "").strip()
    side_code = str(fields.get("907") or fields.get("buy_sell_type") or "").strip()
    text_side = "buy" if "매수" in side_text else "sell" if "매도" in side_text else ""
    code_side = "buy" if side_code == "2" else "sell" if side_code == "1" else ""
    if text_side and code_side and text_side != code_side:
        return "conflict"
    return text_side or code_side or "missing"


def _receipt_is_buy(fields: dict[str, Any]) -> bool:
    return _receipt_side(fields) == "buy"


def _runtime_policy_artifact_matches(
    observation_date: date,
    source_date: date,
    artifact_sha256: str,
) -> bool:
    """Rebind active runtime provenance to the exact immutable policy/report pair."""

    receipt_path = (
        PREOPEN_DIR / f"scanner_lookup_attention_preopen_{observation_date}.json"
    )
    if receipt_path.exists():
        selected = load_active_policy(observation_date, applied_dir=PREOPEN_DIR)
        return bool(
            selected["active"]
            and selected["policy_source_date"] == source_date.isoformat()
            and selected["policy_artifact_sha256"] == artifact_sha256
        )

    policy_payload = _load_json(
        POLICY_DIR / f"scanner_lookup_attention_policy_{source_date.isoformat()}.json"
    )
    if policy_payload.get("decision_contract_version") == DECISION_CONTRACT_VERSION:
        return False
    report_payload = _load_json(
        REPORT_DIR / f"scanner_lookup_attention_tuning_{source_date.isoformat()}.json"
    )
    return bool(
        is_krx_trading_day(observation_date)
        and is_krx_trading_day(source_date)
        and count_krx_trading_days(source_date, observation_date) == 1
        and policy_payload.get("artifact_sha256") == artifact_sha256
        and policy_payload.get("status") == "live_auto_apply_ready"
        and not validate_artifact_pair(
            report_payload,
            policy_payload,
            target=source_date,
        )
    )


def _previous_krx_trading_date(value: date) -> date:
    candidate = value - timedelta(days=1)
    for _ in range(14):
        if is_krx_trading_day(candidate):
            return candidate
        candidate -= timedelta(days=1)
    raise ValueError("previous_krx_trading_date_unresolved")


def _runtime_policy_expectation(observation_date: date) -> dict[str, Any]:
    """Resolve whether the exact previous trading-day artifact required live use."""

    receipt_path = (
        PREOPEN_DIR / f"scanner_lookup_attention_preopen_{observation_date}.json"
    )
    if receipt_path.exists():
        selected = load_active_policy(observation_date, applied_dir=PREOPEN_DIR)
        return {
            "state": (
                "active"
                if selected["active"]
                else (
                    "invalid"
                    if selected["reason"] == "preopen_receipt_invalid"
                    else "inactive"
                )
            ),
            "source_date": selected.get("policy_source_date"),
            "artifact_sha256": selected.get("policy_artifact_sha256"),
            "preopen_artifact_sha256": selected.get("preopen_artifact_sha256"),
        }

    try:
        source_date = _previous_krx_trading_date(observation_date)
    except ValueError:
        return {"state": "invalid", "reason": "prior_trading_date_unresolved"}
    policy_path = (
        POLICY_DIR / f"scanner_lookup_attention_policy_{source_date.isoformat()}.json"
    )
    report_path = REPORT_DIR / (
        f"scanner_lookup_attention_tuning_{source_date.isoformat()}.json"
    )
    if not policy_path.exists() and not report_path.exists():
        return {
            "state": "inactive",
            "source_date": source_date.isoformat(),
            "reason": "prior_artifact_pair_absent",
        }
    policy_payload = _load_json(policy_path)
    report_payload = _load_json(report_path)
    issues = validate_artifact_pair(report_payload, policy_payload, target=source_date)
    if issues:
        return {
            "state": "invalid",
            "source_date": source_date.isoformat(),
            "reason": "prior_artifact_pair_invalid",
            "issues": issues,
        }
    if policy_payload.get("status") != "live_auto_apply_ready":
        return {
            "state": "inactive",
            "source_date": source_date.isoformat(),
            "reason": "prior_policy_not_live",
        }
    if policy_payload.get("decision_contract_version") == DECISION_CONTRACT_VERSION:
        return {
            "state": "invalid",
            "reason": "preopen_receipt_missing",
            "source_date": source_date.isoformat(),
        }
    return {
        "state": "active",
        "source_date": source_date.isoformat(),
        "artifact_sha256": str(policy_payload.get("artifact_sha256") or ""),
    }


def collect_lineage(target: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect exact lookup observations and full-fill receipt classifications."""

    start = max(ROLLOUT_DATE, target - timedelta(days=ROLLING_CALENDAR_DAYS - 1))
    observations: dict[tuple[int, str, str], dict[str, Any]] = {}
    conflicted_observation_keys: set[tuple[int, str, str]] = set()
    fill_receipts: defaultdict[tuple[int, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    invalid_observation_count = 0
    invalid_runtime_policy_provenance_count = 0
    parse_stats = {
        "malformed_json_line_count": 0,
        "non_object_json_line_count": 0,
    }
    runtime_policy_artifact_cache: dict[tuple[date, date, str], bool] = {}
    runtime_policy_expectation_cache: dict[date, dict[str, Any]] = {}
    resource_rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    conflicted_resource_keys: set[tuple[str, str, str]] = set()
    resource_evidence_rows: list[dict[str, Any]] = []
    resource_capture_diagnostics: dict[str, Any] = {}
    resource_start = _resource_window_start(target)
    event_file_count = 0
    observed_event_dates = []
    cursor = start
    while cursor <= target:
        event_file_date = cursor
        path = _event_path(event_file_date)
        cursor += timedelta(days=1)
        if path is None:
            continue
        resource_rows = {}
        conflicted_resource_keys = set()
        event_file_count += 1
        observed_event_dates.append(event_file_date.isoformat())
        for event in _iter_events(path, parse_stats=parse_stats):
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            stage = str(event.get("stage") or "")
            if event_file_date >= resource_start and stage in {
                "scalping_scanner_candidate_promoted",
                "scalping_scanner_candidate_pruned",
            }:
                resource_row = parse_resource_event(event)
                if (
                    resource_row is not None
                    and resource_row["effective_venue"] == "KRX"
                    and resource_row["market_session_bucket"] == "krx_regular"
                ):
                    if resource_row["observation_date"] != event_file_date.isoformat():
                        resource_row["eligible_source"] = False
                    resource_key = (
                        event_file_date.isoformat(),
                        resource_row["scan_generation_id"],
                        resource_row["stock_code"],
                    )
                    if resource_key in conflicted_resource_keys:
                        continue
                    existing = resource_rows.get(resource_key)
                    if existing is not None and existing != resource_row:
                        resource_row["eligible_source"] = False
                        conflicted_resource_keys.add(resource_key)
                    resource_rows[resource_key] = resource_row
            if stage == "scalping_scanner_runtime_target_attach":
                if fields.get("lookup_attention_state") != "observed_source_only":
                    continue
                key = _observation_key(fields, event.get("stock_code"))
                score = _finite(fields.get("lookup_attention_snapshot_score"))
                try:
                    event_date = date.fromisoformat(
                        str(event.get("emitted_date") or "")
                    )
                except ValueError:
                    event_date = None
                valid = bool(
                    key[0] > 0
                    and key[1].startswith("SCANPROM-")
                    and re.fullmatch(r"\d{6}", key[2]) is not None
                    and score is not None
                    and 0.0 <= score <= 1.0
                    and _source_timestamp_valid(event, fields)
                    and event_date is not None
                    and is_krx_trading_day(event_date)
                    and _bool(fields.get("lookup_attention_runtime_effect")) is False
                    and _bool(fields.get("lookup_attention_allowed_runtime_apply"))
                    is False
                    and _bool(fields.get("lookup_attention_actual_order_submitted"))
                    is False
                    and _bool(fields.get("lookup_attention_broker_order_forbidden"))
                    is True
                )
                if not valid:
                    invalid_observation_count += 1
                    continue
                policy_source_date = str(
                    fields.get("lookup_attention_weight_policy_source_date") or ""
                ).strip()
                policy_allowed = _bool(
                    fields.get("lookup_attention_weight_allowed_runtime_apply")
                )
                policy_applied = _bool(
                    fields.get("lookup_attention_weight_policy_applied")
                )
                policy_runtime_effect = _bool(
                    fields.get("lookup_attention_weight_runtime_effect")
                )
                policy_bonus = _finite(
                    fields.get("lookup_attention_weight_bonus_points")
                )
                policy_artifact_sha256 = str(
                    fields.get("lookup_attention_weight_policy_artifact_sha256") or ""
                ).strip()
                event_effective_venue = (
                    str(fields.get("effective_venue") or fields.get("venue") or "")
                    .strip()
                    .upper()
                )
                event_session = str(fields.get("market_session_bucket") or "").strip()
                event_in_policy_scope = bool(
                    event_effective_venue in ELIGIBLE_VENUES
                    and event_session in ELIGIBLE_SESSION_BUCKETS
                )
                runtime_policy_eligible = False
                runtime_policy_provenance_invalid = False
                expectation = runtime_policy_expectation_cache.get(event_date)
                if expectation is None:
                    expectation = _runtime_policy_expectation(event_date)
                    runtime_policy_expectation_cache[event_date] = expectation
                if expectation.get("state") == "invalid" and event_in_policy_scope:
                    runtime_policy_provenance_invalid = True
                elif (
                    expectation.get("state") == "active"
                    and event_in_policy_scope
                    and policy_allowed is not True
                ):
                    runtime_policy_provenance_invalid = True
                elif (
                    expectation.get("state") != "active" or not event_in_policy_scope
                ) and policy_allowed is True:
                    runtime_policy_provenance_invalid = True
                if policy_allowed is True:
                    try:
                        parsed_policy_source_date = date.fromisoformat(
                            policy_source_date
                        )
                        observation_date = date.fromisoformat(
                            str(event.get("emitted_date") or "")
                        )
                    except ValueError:
                        runtime_policy_provenance_invalid = True
                    else:
                        artifact_key = (
                            observation_date,
                            parsed_policy_source_date,
                            policy_artifact_sha256,
                        )
                        artifact_valid = runtime_policy_artifact_cache.get(artifact_key)
                        if artifact_valid is None:
                            artifact_valid = _runtime_policy_artifact_matches(
                                observation_date,
                                parsed_policy_source_date,
                                policy_artifact_sha256,
                            )
                            runtime_policy_artifact_cache[artifact_key] = artifact_valid
                        policy_same_tier_only = _bool(
                            fields.get(
                                "lookup_attention_weight_same_priority_tier_only"
                            )
                        )
                        policy_source_fresh = _bool(
                            fields.get("lookup_attention_weight_source_fresh")
                        )
                        weight_source_age_sec = _finite(
                            fields.get("lookup_attention_weight_source_age_sec")
                        )
                        weight_effective_venue = (
                            str(
                                fields.get("lookup_attention_weight_effective_venue")
                                or ""
                            )
                            .strip()
                            .upper()
                        )
                        weight_session = str(
                            fields.get("lookup_attention_weight_market_session_bucket")
                            or ""
                        ).strip()
                        expected_bonus = round(
                            max(
                                0.0,
                                MAX_BONUS_POINTS
                                * (float(score) - MIN_SCORE)
                                / max(1e-9, 1.0 - MIN_SCORE),
                            ),
                            6,
                        )
                        expected_bonus = min(MAX_BONUS_POINTS, expected_bonus)
                        expected_policy_state = (
                            "applied_same_priority_tier"
                            if expected_bonus > 0.0
                            else (
                                "loaded_at_floor"
                                if float(score) == MIN_SCORE
                                else "loaded_below_threshold"
                            )
                        )
                        expected_policy_reason = (
                            "bounded_linear_bonus"
                            if expected_bonus > 0.0
                            else (
                                "policy_floor_zero_bonus"
                                if float(score) == MIN_SCORE
                                else "lookup_attention_score_below_policy_minimum"
                            )
                        )
                        runtime_forbidden_uses = {
                            item.strip()
                            for item in str(
                                fields.get("lookup_attention_weight_forbidden_uses")
                                or ""
                            ).split(",")
                            if item.strip()
                        }
                        runtime_policy_eligible = bool(
                            is_krx_trading_day(parsed_policy_source_date)
                            and is_krx_trading_day(observation_date)
                            and count_krx_trading_days(
                                parsed_policy_source_date, observation_date
                            )
                            == 1
                            and artifact_valid
                            and (
                                not expectation.get("preopen_artifact_sha256")
                                or fields.get(
                                    "lookup_attention_weight_preopen_artifact_sha256"
                                )
                                == expectation["preopen_artifact_sha256"]
                            )
                            and expectation.get("state") == "active"
                            and expectation.get("source_date") == policy_source_date
                            and expectation.get("artifact_sha256")
                            == policy_artifact_sha256
                            and fields.get("lookup_attention_weight_policy_version")
                            == POLICY_VERSION
                            and fields.get("lookup_attention_weight_decision_authority")
                            == DECISION_AUTHORITY
                            and policy_same_tier_only is True
                            and str(
                                fields.get("lookup_attention_weight_eligible_venues")
                                or ""
                            )
                            == ",".join(ELIGIBLE_VENUES)
                            and str(
                                fields.get(
                                    "lookup_attention_weight_eligible_session_buckets"
                                )
                                or ""
                            )
                            == ",".join(ELIGIBLE_SESSION_BUCKETS)
                            and weight_effective_venue == event_effective_venue == "KRX"
                            and weight_session == event_session == "krx_regular"
                            and policy_source_fresh is True
                            and weight_source_age_sec is not None
                            and -MAX_FUTURE_SKEW_SEC
                            <= weight_source_age_sec
                            <= MAX_SOURCE_AGE_SEC
                            and _finite(
                                fields.get("lookup_attention_weight_max_source_age_sec")
                            )
                            == MAX_SOURCE_AGE_SEC
                            and _bool(
                                fields.get(
                                    "lookup_attention_weight_actual_order_submitted"
                                )
                            )
                            is False
                            and _bool(
                                fields.get(
                                    "lookup_attention_weight_broker_order_forbidden"
                                )
                            )
                            is True
                            and re.fullmatch(r"[0-9a-f]{64}", policy_artifact_sha256)
                            is not None
                            and policy_bonus is not None
                            and 0.0 <= policy_bonus <= MAX_BONUS_POINTS
                            and abs(policy_bonus - expected_bonus) <= 1e-6
                            and fields.get("lookup_attention_weight_policy_state")
                            == expected_policy_state
                            and fields.get("lookup_attention_weight_policy_reason")
                            == expected_policy_reason
                            and _finite(
                                fields.get(
                                    "lookup_attention_weight_rollback_bonus_points"
                                )
                            )
                            == 0.0
                            and set(FORBIDDEN_USES).issubset(runtime_forbidden_uses)
                            and policy_applied is (policy_bonus > 0.0)
                            and policy_runtime_effect is policy_applied
                        )
                        runtime_policy_provenance_invalid = bool(
                            runtime_policy_provenance_invalid
                            or not runtime_policy_eligible
                        )
                elif policy_applied is True or policy_runtime_effect is True:
                    runtime_policy_provenance_invalid = True
                if runtime_policy_provenance_invalid:
                    invalid_runtime_policy_provenance_count += 1
                observation = {
                    "recommendation_id": key[0],
                    "scanner_promotion_id": key[1],
                    "stock_code": key[2],
                    "observation_date": str(event.get("emitted_date") or ""),
                    "observed_at": str(event.get("emitted_at") or ""),
                    "lookup_attention_snapshot_score": score,
                    "effective_venue": str(
                        fields.get("effective_venue") or fields.get("venue") or ""
                    )
                    .strip()
                    .upper(),
                    "market_session_bucket": str(
                        fields.get("market_session_bucket") or ""
                    ).strip(),
                    "source_timestamp": (
                        f"{fields.get('realtime_lookup_source_date')}"
                        f"T{fields.get('realtime_lookup_source_time')}"
                    ),
                    "lookup_attention_source_age_sec": round(
                        float(_source_age_sec(event, fields) or 0.0), 6
                    ),
                    "lookup_attention_weight_policy_source_date": policy_source_date,
                    "lookup_attention_weight_policy_version": str(
                        fields.get("lookup_attention_weight_policy_version") or ""
                    ),
                    "lookup_attention_weight_policy_artifact_sha256": (
                        policy_artifact_sha256
                    ),
                    "lookup_attention_weight_allowed_runtime_apply": policy_allowed,
                    "lookup_attention_weight_policy_applied": policy_applied,
                    "lookup_attention_weight_runtime_effect": policy_runtime_effect,
                    "lookup_attention_weight_bonus_points": policy_bonus,
                    "lookup_attention_weight_runtime_policy_eligible": (
                        runtime_policy_eligible
                    ),
                    "lookup_attention_weight_runtime_policy_provenance_invalid": (
                        runtime_policy_provenance_invalid
                    ),
                }
                if key in conflicted_observation_keys:
                    continue
                existing = observations.get(key)
                existing_signature = (
                    {
                        name: value
                        for name, value in existing.items()
                        if name != "observed_at"
                    }
                    if existing is not None
                    else None
                )
                observation_signature = {
                    name: value
                    for name, value in observation.items()
                    if name != "observed_at"
                }
                if (
                    existing_signature is not None
                    and existing_signature != observation_signature
                ):
                    invalid_observation_count += 1
                    observations.pop(key, None)
                    conflicted_observation_keys.add(key)
                    continue
                observations[key] = observation
                continue
            if stage != "position_rebased_after_fill":
                continue
            key = _observation_key(fields, event.get("stock_code"))
            receipt_side = _receipt_side(fields)
            if (
                key[0] <= 0
                or not key[1].startswith("SCANPROM-")
                or re.fullmatch(r"\d{6}", key[2]) is None
            ):
                continue
            if receipt_side == "sell":
                continue
            requested = _strict_int(fields.get("order_requested_qty"))
            filled = _strict_int(fields.get("order_filled_qty"))
            remaining = _strict_int(fields.get("order_remaining_qty"))
            full = bool(
                receipt_side == "buy"
                and str(fields.get("fill_quality") or "") == "FULL_FILL"
                and requested is not None
                and requested > 0
                and filled == requested
                and remaining == 0
                and _bool(fields.get("receipt_quantity_contract_complete")) is True
            )
            partial = bool(
                receipt_side == "buy"
                and str(fields.get("fill_quality") or "") == "PARTIAL_FILL"
            )
            fill_receipts[key].append(
                {
                    "classification": (
                        "full" if full else "partial" if partial else "invalid"
                    ),
                    "effective_venue": str(
                        fields.get("main_lifecycle_venue")
                        or fields.get("effective_venue")
                        or ""
                    )
                    .strip()
                    .upper(),
                    "market_session_bucket": str(
                        fields.get("main_lifecycle_session_bucket")
                        or fields.get("market_session_bucket")
                        or ""
                    ).strip(),
                    "trade_date": str(
                        fields.get("main_lifecycle_trade_date")
                        or event.get("emitted_date")
                        or ""
                    ),
                }
            )

        if resource_rows:
            retained, diagnostics = compact_evidence_rows(
                list(resource_rows.values()),
                capacity_reasons=RESOURCE_CAPACITY_PRUNE_REASONS,
            )
            resource_evidence_rows.extend(retained)
            resource_capture_diagnostics[event_file_date.isoformat()] = diagnostics

    rows: list[dict[str, Any]] = []
    invalid_fill_contract_count = 0
    for key, observation in observations.items():
        receipts = fill_receipts.get(key, [])
        matching_receipts = [
            receipt
            for receipt in receipts
            if receipt["effective_venue"] == observation["effective_venue"]
            and receipt["market_session_bucket"] == observation["market_session_bucket"]
            and receipt["trade_date"] == observation["observation_date"]
        ]
        invalid_fill_contract_count += sum(
            receipt["classification"] == "invalid" for receipt in matching_receipts
        ) + (len(receipts) - len(matching_receipts))
        states = {receipt["classification"] for receipt in matching_receipts}
        fill_class = (
            "full_fill"
            if "full" in states
            else (
                "partial_fill"
                if "partial" in states
                else (
                    "fill_contract_invalid"
                    if "invalid" in states
                    else "fill_receipt_missing"
                )
            )
        )
        rows.append({**observation, "fill_class": fill_class})
    rows.sort(
        key=lambda row: (
            row["observation_date"],
            row["observed_at"],
            row["recommendation_id"],
        )
    )
    return rows, {
        "window_start": start.isoformat(),
        "window_end": target.isoformat(),
        "event_file_count": event_file_count,
        "observed_event_dates": observed_event_dates,
        "valid_observation_count": len(rows),
        "invalid_observation_count": invalid_observation_count,
        "invalid_fill_contract_count": invalid_fill_contract_count,
        "invalid_runtime_policy_provenance_count": (
            invalid_runtime_policy_provenance_count
        ),
        "malformed_json_line_count": parse_stats["malformed_json_line_count"],
        "non_object_json_line_count": parse_stats["non_object_json_line_count"],
        "runtime_policy_artifact_check_count": len(runtime_policy_artifact_cache),
        "runtime_policy_expectation_date_count": len(runtime_policy_expectation_cache),
        "full_fill_observation_count": sum(
            row["fill_class"] == "full_fill" for row in rows
        ),
        "partial_fill_observation_count": sum(
            row["fill_class"] == "partial_fill" for row in rows
        ),
        "fill_contract_invalid_observation_count": sum(
            row["fill_class"] == "fill_contract_invalid" for row in rows
        ),
        "fill_receipt_missing_count": sum(
            row["fill_class"] == "fill_receipt_missing" for row in rows
        ),
        "invalid_resource_pair_count": sum(
            not valid_resource_row(row) for row in resource_evidence_rows
        ),
        "resource_pair_row_count": len(resource_evidence_rows),
        "resource_capture_window_start": max(start, resource_start).isoformat(),
        "resource_capture_diagnostics": resource_capture_diagnostics,
        "_resource_pair_rows": resource_evidence_rows,
    }


def load_completed_facts(start: date, target: date) -> list[dict[str, Any]]:
    """Load exact completed main-scanner facts without opening a DB at import time."""

    from src.database.db_manager import DBManager
    from src.database.models import RecommendationHistory, TradePerformanceFact

    db = DBManager()
    with db.get_session() as session:
        rows = (
            session.query(TradePerformanceFact, RecommendationHistory)
            .join(
                RecommendationHistory,
                RecommendationHistory.id == TradePerformanceFact.recommendation_id,
            )
            .filter(
                TradePerformanceFact.rec_date >= start,
                TradePerformanceFact.rec_date <= target,
                TradePerformanceFact.status == "COMPLETED",
                TradePerformanceFact.strategy == "SCALPING",
                TradePerformanceFact.position_tag == "SCANNER",
            )
            .all()
        )
    return [
        {
            "recommendation_id": int(fact.recommendation_id),
            "rec_date": fact.rec_date.isoformat(),
            "stock_code": str(fact.stock_code or "")[:6],
            "scanner_promotion_id": str(history.scanner_promotion_id or ""),
            "status": str(fact.status or ""),
            "strategy": str(fact.strategy or ""),
            "position_tag": str(fact.position_tag or ""),
            "buy_price": _finite(fact.buy_price),
            "buy_qty": _strict_int(fact.buy_qty),
            "sell_price": _finite(fact.sell_price),
            "buy_time": fact.buy_time.isoformat() if fact.buy_time else None,
            "sell_time": fact.sell_time.isoformat() if fact.sell_time else None,
            "profit_rate": _finite(fact.profit_rate),
            "add_count": _strict_int(fact.add_count),
            "avg_down_count": _strict_int(fact.avg_down_count),
            "pyramid_count": _strict_int(fact.pyramid_count),
        }
        for fact, history in rows
    ]


def _latest_symbol_master(target: date) -> tuple[set[str], dict[str, Any]]:
    candidates: list[tuple[date, Path]] = []
    for path in SYMBOL_MASTER_DIR.glob("micro_reversion_symbol_master_*.json*"):
        name = path.name.removesuffix(".gz").removesuffix(".json")
        suffix = name.removeprefix("micro_reversion_symbol_master_")
        try:
            source_date = date.fromisoformat(suffix)
        except ValueError:
            continue
        if source_date <= target:
            candidates.append((source_date, path))
    if not candidates:
        return set(), {"status": "missing"}
    source_date = max(item[0] for item in candidates)
    latest_paths = sorted(
        path for item_date, path in candidates if item_date == source_date
    )
    if len(latest_paths) != 1:
        return set(), {
            "status": "ambiguous_latest_artifact",
            "source_date": source_date.isoformat(),
            "paths": [str(path) for path in latest_paths],
        }
    path = latest_paths[0]
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return set(), {"status": "unreadable", "path": str(path)}
    records = payload.get("records") if isinstance(payload.get("records"), list) else []
    source_artifacts = (
        payload.get("source_artifacts")
        if isinstance(payload.get("source_artifacts"), list)
        else []
    )
    source = source_artifacts[0] if len(source_artifacts) == 1 else {}
    census = payload.get("census") if isinstance(payload.get("census"), dict) else {}
    census_record_count = _strict_int(census.get("record_count"))
    census_symbol_count = _strict_int(census.get("symbol_count"))
    source_record_count = _strict_int(source.get("record_count"))
    expected_size_bytes = _strict_int(source.get("expected_size_bytes"))
    observed_size_bytes = _strict_int(source.get("observed_size_bytes"))
    try:
        expected_content_hash = canonical_sha256(
            {key: value for key, value in payload.items() if key != "content_sha256"}
        )
    except (TypeError, ValueError):
        expected_content_hash = ""
    valid = bool(
        payload.get("schema") == "scalp_micro_reversion_symbol_master_v1"
        and is_krx_trading_day(source_date)
        and count_krx_trading_days(source_date, target) <= 1
        and expected_content_hash
        and payload.get("content_sha256") == expected_content_hash
        and payload.get("verified") is True
        and payload.get("verification_status") == "verified"
        and source.get("source_id")
        == f"kis-official-common-stock-master-{source_date.isoformat()}"
        and source.get("verified") is True
        and source.get("status") == "verified"
        and re.fullmatch(r"[0-9a-f]{64}", str(source.get("expected_sha256") or ""))
        is not None
        and source.get("expected_sha256") == source.get("observed_sha256")
        and source.get("kind") == "symbol_product_master"
        and source.get("payload_schema")
        == "micro_reversion_raw_symbol_product_master_v3"
        and source.get("effective_from") == source_date.isoformat()
        and source_record_count == len(records)
        and census_record_count == len(records)
        and census_symbol_count == len(records)
        and expected_size_bytes is not None
        and expected_size_bytes > 0
        and observed_size_bytes == expected_size_bytes
    )
    symbols: set[str] = set()
    invalid_record_count = 0
    for row in records:
        if not isinstance(row, dict):
            invalid_record_count += 1
            continue
        symbol = str(row.get("symbol") or "")
        try:
            effective_from = date.fromisoformat(str(row.get("effective_from") or ""))
            effective_to = (
                date.fromisoformat(str(row.get("effective_to")))
                if row.get("effective_to")
                else None
            )
        except ValueError:
            invalid_record_count += 1
            continue
        if (
            re.fullmatch(r"\d{6}", symbol) is not None
            and row.get("metadata_source") == "official_symbol_product_master_v2"
            and row.get("instrument_type") == "EQUITY"
            and row.get("listing_market") in {"KOSPI", "KOSDAQ"}
            and row.get("conflict_status") == "clean"
            and effective_from <= target
            and (effective_to is None or effective_to >= target)
        ):
            symbols.add(symbol)
        else:
            invalid_record_count += 1
    valid = bool(
        valid
        and invalid_record_count == 0
        and len(symbols) == len(records)
        and len(source_artifacts) == 1
    )
    return symbols if valid else set(), {
        "status": "pass" if valid else "contract_invalid",
        "path": str(path),
        "source_date": source_date.isoformat(),
        "content_sha256": str(payload.get("content_sha256") or ""),
        "upstream_sha256": str(source.get("observed_sha256") or ""),
        "eligible_common_stock_count": len(symbols) if valid else 0,
        "invalid_record_count": invalid_record_count,
        "source_artifact_count": len(source_artifacts),
    }


def _source_quality(
    target: date, input_dates: set[date] | None = None
) -> dict[str, Any]:
    audit_dates = sorted({target, *(input_dates or set())})
    audits: list[dict[str, Any]] = []
    for audit_date in audit_dates:
        path = SOURCE_AUDIT_DIR / (
            f"observation_source_quality_audit_{audit_date.isoformat()}.json"
        )
        payload = _load_json(path)
        summary = (
            payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        )
        audit_status = str(payload.get("status") or "missing")
        hard_gap_count = _strict_int(summary.get("hard_blocking_contract_gap_count"))
        excluded_row_count = _strict_int(
            summary.get("hard_blocking_excluded_row_count")
        )
        current_excluded_row_count = _strict_int(
            summary.get("current_scan_hard_blocking_excluded_row_count")
        )
        post_exclusion_row_count = _strict_int(
            summary.get("post_exclusion_hard_blocking_excluded_row_count")
        )
        review_warning_count = _strict_int(summary.get("review_warning_count"))
        row_exclusion_applied = _bool(summary.get("raw_row_exclusion_applied"))
        exclusion_revalidation_required = _bool(
            summary.get("raw_row_exclusion_revalidation_required")
        )
        deferred_writer_active = _bool(
            summary.get("raw_row_exclusion_deferred_writer_active")
        )
        if excluded_row_count == 0:
            row_exclusion_resolved = True
        else:
            row_exclusion_resolved = bool(
                excluded_row_count is not None
                and excluded_row_count > 0
                and row_exclusion_applied is True
                and current_excluded_row_count == 0
                and post_exclusion_row_count == 0
                and exclusion_revalidation_required is False
                and deferred_writer_active is False
                and str(summary.get("raw_row_exclusion_manifest") or "").strip()
            )
        valid = bool(
            payload.get("report_type") == "observation_source_quality_audit"
            and payload.get("target_date") == audit_date.isoformat()
            and audit_status not in {"fail", "missing", "invalid"}
            and summary.get("tuning_input_allowed") is True
            and hard_gap_count == 0
            and row_exclusion_resolved
            and review_warning_count is not None
            and review_warning_count >= 0
            and not summary.get("blocked_reason")
        )
        audits.append(
            {
                "target_date": audit_date.isoformat(),
                "path": str(path),
                "status": "pass" if valid else "source_quality_blocked",
                "audit_status": audit_status,
                "tuning_input_allowed": summary.get("tuning_input_allowed"),
                "hard_blocking_contract_gap_count": hard_gap_count,
                "hard_blocking_excluded_row_count": excluded_row_count,
                "current_scan_hard_blocking_excluded_row_count": (
                    current_excluded_row_count
                ),
                "post_exclusion_hard_blocking_excluded_row_count": (
                    post_exclusion_row_count
                ),
                "raw_row_exclusion_applied": row_exclusion_applied,
                "raw_row_exclusion_revalidation_required": (
                    exclusion_revalidation_required
                ),
                "raw_row_exclusion_deferred_writer_active": deferred_writer_active,
                "row_exclusion_resolved": row_exclusion_resolved,
                "review_warning_count": review_warning_count,
            }
        )
    return {
        "status": (
            "pass"
            if audits and all(row["status"] == "pass" for row in audits)
            else "source_quality_blocked"
        ),
        "audit_date_count": len(audits),
        "blocked_dates": [
            row["target_date"] for row in audits if row["status"] != "pass"
        ],
        "audits": audits,
    }


def join_completed_outcomes(
    observations: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    *,
    eligible_symbols: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Join exact immutable identities and apply economics/source exclusions."""

    facts_by_id: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in facts:
        facts_by_id[int(row.get("recommendation_id") or 0)].append(row)
    exclusions: defaultdict[str, int] = defaultdict(int)
    outcomes: list[dict[str, Any]] = []
    for observation in observations:
        if observation.get("fill_class") != "full_fill":
            exclusions[
                str(observation.get("fill_class") or "fill_contract_invalid")
            ] += 1
            continue
        if (
            observation.get("effective_venue") not in ELIGIBLE_VENUES
            or observation.get("market_session_bucket") not in ELIGIBLE_SESSION_BUCKETS
        ):
            exclusions["venue_or_session_out_of_policy_scope"] += 1
            continue
        matching_facts = facts_by_id.get(int(observation["recommendation_id"]), [])
        if not matching_facts:
            exclusions["completed_fact_missing_or_right_censored"] += 1
            continue
        if len(matching_facts) != 1:
            exclusions["completed_fact_identity_ambiguous"] += 1
            continue
        fact = matching_facts[0]
        if (
            fact.get("status") != "COMPLETED"
            or fact.get("strategy") != "SCALPING"
            or fact.get("position_tag") != "SCANNER"
        ):
            exclusions["completed_main_scanner_owner_contract_mismatch"] += 1
            continue
        if fact.get("stock_code") != observation.get("stock_code") or fact.get(
            "scanner_promotion_id"
        ) != observation.get("scanner_promotion_id"):
            exclusions["exact_identity_mismatch"] += 1
            continue
        if str(fact.get("rec_date") or "") != observation.get("observation_date"):
            exclusions["exact_trade_date_mismatch"] += 1
            continue
        if fact.get("stock_code") not in eligible_symbols:
            exclusions["official_common_stock_master_excluded"] += 1
            continue
        scale_counts: list[int] = []
        scale_count_invalid = False
        for key in ("add_count", "avg_down_count", "pyramid_count"):
            raw_count = fact.get(key)
            parsed_count = 0 if raw_count in (None, "") else _strict_int(raw_count)
            if parsed_count is None or parsed_count < 0:
                scale_count_invalid = True
                break
            scale_counts.append(parsed_count)
        if scale_count_invalid:
            exclusions["scale_in_count_contract_invalid"] += 1
            continue
        if any(count > 0 for count in scale_counts):
            exclusions["scale_in_or_average_down_confounded"] += 1
            continue
        buy_price = _finite(fact.get("buy_price"))
        sell_price = _finite(fact.get("sell_price"))
        profit_rate = _finite(fact.get("profit_rate"))
        qty = _strict_int(fact.get("buy_qty"))
        try:
            rec_date = date.fromisoformat(str(fact.get("rec_date") or ""))
        except ValueError:
            exclusions["rec_date_invalid"] += 1
            continue
        if (
            buy_price is None
            or sell_price is None
            or profit_rate is None
            or buy_price <= 0
            or sell_price <= 0
            or qty is None
            or qty <= 0
        ):
            exclusions["economics_input_invalid"] += 1
            continue
        if rec_date < COST_EFFECTIVE_FROM:
            exclusions["cost_contract_not_effective"] += 1
            continue
        buy_notional = buy_price * qty
        sell_notional = sell_price * qty
        costs = (
            buy_notional * COST_CONTRACT["buy_fee_bps"] / 10_000.0
            + sell_notional * COST_CONTRACT["sell_fee_bps"] / 10_000.0
            + sell_notional * COST_CONTRACT["statutory_sell_tax_bps"] / 10_000.0
        )
        net_pnl = sell_notional - buy_notional - costs
        if not all(
            math.isfinite(v) for v in (buy_notional, sell_notional, costs, net_pnl)
        ):
            exclusions["economics_arithmetic_nonfinite"] += 1
            continue
        # Optional capital-time diagnostic; absence must not invent zero duration
        # or become another economic approval floor.
        capital_hours = None
        try:
            entered = datetime.fromisoformat(str(fact.get("buy_time") or ""))
            exited = datetime.fromisoformat(str(fact.get("sell_time") or ""))
            elapsed = (exited - entered).total_seconds() / 3600.0
            if elapsed > 0 and entered.date() == rec_date and exited.date() >= rec_date:
                capital_hours = buy_notional * elapsed
        except (TypeError, ValueError, OverflowError):
            pass
        score = float(observation["lookup_attention_snapshot_score"])
        outcomes.append(
            {
                **observation,
                "rec_date": rec_date.isoformat(),
                "cohort": "candidate" if score > MIN_SCORE else "control",
                "buy_notional_krw": round(buy_notional, 6),
                "sell_notional_krw": round(sell_notional, 6),
                "comparison_cost_krw": round(costs, 6),
                "net_pnl_krw": round(net_pnl, 6),
                "net_return_pct": round(net_pnl / buy_notional * 100.0, 8),
                "capital_hours_krw": capital_hours,
            }
        )
    outcomes.sort(key=lambda row: (row["rec_date"], row["recommendation_id"]))
    return outcomes, dict(sorted(exclusions.items()))


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _metrics(rows: list[dict[str, Any]], *, economic_contract=True) -> dict[str, Any]:
    returns = [float(row["net_return_pct"]) for row in rows]
    total_notional = sum(float(row["buy_notional_krw"]) for row in rows)
    total_pnl = sum(float(row["net_pnl_krw"]) for row in rows)
    metrics = {
        "completed_outcome_count": len(rows),
        "trading_date_count": len({row["rec_date"] for row in rows}),
        "equal_weight_avg_profit_pct": (
            round(sum(returns) / len(returns), 8) if returns else None
        ),
        "notional_weighted_ev_pct": (
            round(total_pnl / total_notional * 100.0, 8) if total_notional > 0 else None
        ),
        "source_quality_adjusted_ev_pct": (
            round(sum(returns) / len(returns), 8) if returns else None
        ),
        "downside_p10_pct": round(_percentile(returns, 0.10), 8) if returns else None,
        "worst_net_return_pct": round(min(returns), 8) if returns else None,
        "diagnostic_win_rate_pct": (
            round(sum(value > 0 for value in returns) / len(returns) * 100.0, 6)
            if returns
            else None
        ),
        "buy_notional_krw": round(total_notional, 6),
        "net_pnl_krw": round(total_pnl, 6),
    }
    if not economic_contract:
        return metrics
    n = len(returns)
    days = metrics["trading_date_count"]
    se = None
    if n > 1 and days > 1:
        mean = math.fsum(returns) / n
        residuals = defaultdict(float)
        for row, value in zip(rows, returns):
            residuals[row["rec_date"]] += value - mean
        iid_variance = math.fsum((v - mean) ** 2 for v in returns) / (n - 1) / n
        cluster_variance = (
            days / (days - 1) * math.fsum(v * v for v in residuals.values()) / n**2
        )
        se = math.sqrt(max(iid_variance, cluster_variance))
    hours = [_finite(row.get("capital_hours_krw")) for row in rows]
    duration_complete = bool(rows and all(v is not None and v > 0 for v in hours))
    metrics.update(
        net_return_robust_se_pct=se,
        net_uncertainty_method="max_trade_se_day_cluster_se_not_causal_ci",
        completed_per_outcome_day=n / days if days else None,
        net_per_outcome_day_krw=total_pnl / days if days else None,
        capital_time_covered_count=sum(v is not None and v > 0 for v in hours),
        net_per_capital_hour=(
            total_pnl / math.fsum(hours) if duration_complete else None
        ),
    )
    return metrics


def _cohort_book(
    rows: list[dict[str, Any]], *, economic_contract=True
) -> dict[str, Any]:
    candidate = [row for row in rows if row["cohort"] == "candidate"]
    control = [row for row in rows if row["cohort"] == "control"]
    candidate_metrics = _metrics(candidate, economic_contract=economic_contract)
    control_metrics = _metrics(control, economic_contract=economic_contract)
    candidate_ev = candidate_metrics["source_quality_adjusted_ev_pct"]
    control_ev = control_metrics["source_quality_adjusted_ev_pct"]
    uplift = (
        round(float(candidate_ev) - float(control_ev), 8)
        if candidate_ev is not None and control_ev is not None
        else None
    )
    return {
        **(
            {"economic_contract_version": NET_ECONOMIC_CONTRACT}
            if economic_contract
            else {}
        ),
        "all": _metrics(rows, economic_contract=economic_contract),
        "candidate": candidate_metrics,
        "control": control_metrics,
        "candidate_control_ev_uplift_pct": uplift,
    }


def _lineage_contract_pass(lineage: dict[str, Any]) -> bool:
    """Accept isolated bad observations but reject unresolved joined contracts."""

    return bool(
        lineage.get("invalid_fill_contract_count") == 0
        and lineage.get("invalid_runtime_policy_provenance_count") == 0
        and lineage.get("malformed_json_line_count") == 0
        and lineage.get("non_object_json_line_count") == 0
    )


def _cohort_funnel(
    observations: list[dict[str, Any]], outcomes: list[dict[str, Any]]
) -> dict[str, Any]:
    """Expose where lookup-attention evidence is depleted before completion."""

    def cohort_for_score(value: Any) -> str | None:
        score = _finite(value)
        if score is None or not 0.0 <= score <= 1.0:
            return None
        return "candidate" if score > MIN_SCORE else "control"

    def empty() -> dict[str, Any]:
        return {
            "valid_observation_count": 0,
            "trading_date_count": 0,
            "full_fill_observation_count": 0,
            "partial_fill_observation_count": 0,
            "fill_contract_invalid_count": 0,
            "fill_receipt_missing_count": 0,
            "completed_outcome_count": 0,
            "full_fill_rate_pct": None,
            "completed_per_observation_rate_pct": None,
        }

    books = {"all": empty(), "candidate": empty(), "control": empty()}
    dates: dict[str, set[str]] = {name: set() for name in books}
    completed_by_cohort = {"candidate": 0, "control": 0}
    for outcome in outcomes:
        cohort = str(outcome.get("cohort") or "")
        if cohort in completed_by_cohort:
            completed_by_cohort[cohort] += 1
    for observation in observations:
        cohort = cohort_for_score(observation.get("lookup_attention_snapshot_score"))
        if cohort is None:
            continue
        for name in ("all", cohort):
            books[name]["valid_observation_count"] += 1
            observation_date = str(observation.get("observation_date") or "")
            if observation_date:
                dates[name].add(observation_date)
            fill_class = str(observation.get("fill_class") or "")
            field = {
                "full_fill": "full_fill_observation_count",
                "partial_fill": "partial_fill_observation_count",
                "fill_contract_invalid": "fill_contract_invalid_count",
                "fill_receipt_missing": "fill_receipt_missing_count",
            }.get(fill_class)
            if field:
                books[name][field] += 1
    for cohort in ("candidate", "control"):
        books[cohort]["completed_outcome_count"] = completed_by_cohort[cohort]
    books["all"]["completed_outcome_count"] = sum(completed_by_cohort.values())
    for name, book in books.items():
        observed = int(book["valid_observation_count"])
        book["trading_date_count"] = len(dates[name])
        book["full_fill_rate_pct"] = (
            round(int(book["full_fill_observation_count"]) / observed * 100.0, 6)
            if observed
            else None
        )
        book["completed_per_observation_rate_pct"] = (
            round(int(book["completed_outcome_count"]) / observed * 100.0, 6)
            if observed
            else None
        )
    return {
        "metric_role": "funnel_count",
        "decision_authority": "diagnostic_only_no_standalone_live_promotion",
        "window_policy": f"rolling_{ROLLING_CALENDAR_DAYS}_calendar_days_clean_post_rollout",
        "sample_floor": "one_valid_lookup_attention_observation",
        "primary_decision_metric": "completed_per_observation_rate_pct",
        "source_quality_gate": "exact_lookup_observation_and_fill_lineage",
        "forbidden_uses": FORBIDDEN_USES,
        "all": books["all"],
        "candidate": books["candidate"],
        "control": books["control"],
    }


def _resource_allocation_pair_book(
    rows: list[dict[str, Any]], *, invalid_row_count: int = 0
) -> dict[str, Any]:
    return allocation_book(
        rows,
        invalid_row_count=invalid_row_count,
        capacity_reasons=RESOURCE_CAPACITY_PRUNE_REASONS,
        cost_bps=(
            COST_CONTRACT["buy_fee_bps"],
            COST_CONTRACT["sell_fee_bps"],
            COST_CONTRACT["statutory_sell_tax_bps"],
        ),
    )


def _resource_window_start(target: date) -> date:
    start = target
    dates = int(is_krx_trading_day(target))
    while dates < 20:
        start -= timedelta(days=1)
        dates += int(is_krx_trading_day(start))
    return max(ROLLOUT_DATE, start)


def _book_passes(book: dict[str, Any]) -> tuple[bool, list[str]]:
    all_metrics = book["all"]
    candidate = book["candidate"]
    control = book["control"]
    reasons: list[str] = []
    if all_metrics["completed_outcome_count"] < MIN_TOTAL_COMPLETED:
        reasons.append("total_completed_sample_floor")
    if all_metrics["trading_date_count"] < MIN_TRADING_DATES:
        reasons.append("total_trading_date_floor")
    for name, metrics in (("candidate", candidate), ("control", control)):
        if metrics["completed_outcome_count"] < MIN_COHORT_COMPLETED:
            reasons.append(f"{name}_completed_sample_floor")
        if metrics["trading_date_count"] < MIN_COHORT_DATES:
            reasons.append(f"{name}_trading_date_floor")
    candidate_ev = candidate["source_quality_adjusted_ev_pct"]
    uplift = book["candidate_control_ev_uplift_pct"]
    if candidate_ev is None or candidate_ev <= 0.0:
        reasons.append("candidate_positive_ev_missing")
    if book.get("economic_contract_version") is not None:
        # An empty/one-day book legitimately has no estimable uncertainty.
        # Keep it a sample wait, not a deterministic schema failure.
        if _sample_floor_passes(book):
            reasons.extend(net_edge_reasons(book))
    elif uplift is None or uplift < MIN_EV_UPLIFT_PCT:
        reasons.append("candidate_control_ev_uplift_floor")
    candidate_p10 = candidate["downside_p10_pct"]
    control_p10 = control["downside_p10_pct"]
    if (
        candidate_p10 is None
        or control_p10 is None
        or candidate_p10 < control_p10 - MAX_TAIL_DEGRADATION_PCT
    ):
        reasons.append("candidate_tail_degradation_guard")
    candidate_worst = candidate["worst_net_return_pct"]
    if candidate_worst is None or candidate_worst < MIN_WORST_NET_RETURN_PCT:
        reasons.append("candidate_worst_loss_guard")
    return not reasons, reasons


def _sample_floor_passes(book: dict[str, Any]) -> bool:
    return bool(
        book["all"]["completed_outcome_count"] >= MIN_TOTAL_COMPLETED
        and book["all"]["trading_date_count"] >= MIN_TRADING_DATES
        and book["candidate"]["completed_outcome_count"] >= MIN_COHORT_COMPLETED
        and book["candidate"]["trading_date_count"] >= MIN_COHORT_DATES
        and book["control"]["completed_outcome_count"] >= MIN_COHORT_COMPLETED
        and book["control"]["trading_date_count"] >= MIN_COHORT_DATES
    )


def _campaign_valid(campaign: Any, target: date) -> bool:
    if (
        not isinstance(campaign, dict)
        or campaign.get("contract_version") != "scanner_lookup_frozen_base_v1"
    ):
        return False
    try:
        arm = date.fromisoformat(campaign["arm_date"])
        rows = campaign["outcomes"]
        return bool(
            ROLLOUT_DATE <= arm <= target
            and is_krx_trading_day(arm)
            and rows
            and all(
                ROLLOUT_DATE <= date.fromisoformat(row["rec_date"]) <= arm
                for row in rows
            )
            and len({row["recommendation_id"] for row in rows}) == len(rows)
            and campaign["base_book"]
            == _cohort_book(
                rows,
                economic_contract=bool(
                    campaign["base_book"].get("economic_contract_version")
                ),
            )
            and _book_passes(campaign["base_book"])[0]
            and campaign["source_quality_at_arm"] == "pass"
            and campaign["cost_contract_sha256"] == canonical_sha256(COST_CONTRACT)
            and campaign["full_fill_contract"] == FULL_FILL_CONTRACT
            and campaign["decision_contract_version"] == DECISION_CONTRACT_VERSION
            and campaign["artifact_sha256"]
            == canonical_sha256(
                {k: v for k, v in campaign.items() if k != "artifact_sha256"}
            )
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def _freeze_base(rows, arm_date):
    campaign = {
        "contract_version": "scanner_lookup_frozen_base_v1",
        "arm_date": arm_date,
        "outcomes": rows,
        "base_book": _cohort_book(rows),
        "source_quality_at_arm": "pass",
        "cost_contract_sha256": canonical_sha256(COST_CONTRACT),
        "full_fill_contract": FULL_FILL_CONTRACT,
        "decision_contract_version": DECISION_CONTRACT_VERSION,
    }
    campaign["artifact_sha256"] = canonical_sha256(campaign)
    return campaign


def _base_rows_for_prior(
    outcomes: list[dict[str, Any]], prior_policy: dict[str, Any]
) -> list[dict[str, Any]]:
    campaign = prior_policy.get("campaign_base")
    if isinstance(campaign, dict) and campaign:
        return (
            list(campaign["outcomes"])
            if _campaign_valid(
                campaign, date.fromisoformat(prior_policy["target_date"])
            )
            else []
        )
    if prior_policy.get("status") not in {
        "forward_holdout_armed",
        "live_auto_apply_ready",
    }:
        return list(outcomes)
    try:
        since = date.fromisoformat(str(prior_policy.get("holdout_armed_since") or ""))
    except ValueError:
        return []
    return [row for row in outcomes if date.fromisoformat(row["rec_date"]) <= since]


def _latest_prior_policy(target: date) -> dict[str, Any]:
    candidates = []
    for path in POLICY_DIR.glob("scanner_lookup_attention_policy_*.json"):
        try:
            source_date = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
        except ValueError:
            continue
        if source_date < target and is_krx_trading_day(source_date):
            candidates.append((source_date, path))
    if not candidates:
        return {}
    source_date, path = max(candidates)
    payload = _load_json(path)
    report = _load_json(
        REPORT_DIR / f"scanner_lookup_attention_tuning_{source_date}.json"
    )
    if validate_artifact_pair(report, payload, target=source_date):
        return {}
    if payload.get("status") not in {
        "forward_holdout_armed",
        "live_auto_apply_ready",
        "source_quality_blocked",
    }:
        return {}
    if not _campaign_valid(payload.get("campaign_base"), source_date):
        return {}
    # Missing producer days cannot erase immutable evidence.  Explicit negative
    # economic policy or invalid latest evidence still starts a new campaign.
    return {
        **payload,
        "status": (
            "forward_holdout_armed"
            if payload["status"] == "source_quality_blocked"
            else payload["status"]
        ),
        "campaign_continuity_bridge_dates": (
            [source_date.isoformat()]
            if payload["status"] == "source_quality_blocked"
            else []
        ),
    }


def decide_promotion(
    target: date,
    base_book: dict[str, Any],
    outcomes: list[dict[str, Any]],
    *,
    source_quality_pass: bool,
    prior_policy: dict[str, Any] | None = None,
    resource_allocation_ready: bool = True,
    resource_allocation_status: str = "ready",
) -> dict[str, Any]:
    prior = prior_policy or {}
    prior_status = str(prior.get("status") or "")
    holdout_since = str(prior.get("holdout_armed_since") or "")
    base_pass, base_reasons = _book_passes(base_book)
    if not source_quality_pass:
        return {
            "status": "source_quality_blocked",
            "holdout_armed_since": holdout_since or None,
            "base_pass": False,
            "base_reasons": ["current_source_quality_audit_blocked"],
            "forward_holdout_book": _cohort_book([]),
            "forward_holdout_pass": False,
            "forward_holdout_reasons": ["current_source_quality_audit_blocked"],
        }
    if not base_pass:
        return {
            "status": (
                "hold_sample"
                if any(
                    "sample_floor" in reason or "date_floor" in reason
                    for reason in base_reasons
                )
                else "hold_no_edge"
            ),
            "holdout_armed_since": None,
            "base_pass": False,
            "base_reasons": base_reasons,
            "forward_holdout_book": _cohort_book([]),
            "forward_holdout_pass": False,
            "forward_holdout_reasons": ["base_gate_not_passed"],
        }
    if (
        prior_status not in {"forward_holdout_armed", "live_auto_apply_ready"}
        or not holdout_since
    ):
        return {
            "status": "forward_holdout_armed",
            "holdout_armed_since": target.isoformat(),
            "base_pass": True,
            "base_reasons": [],
            "forward_holdout_book": _cohort_book([]),
            "forward_holdout_pass": False,
            "forward_holdout_reasons": ["independent_forward_holdout_not_started"],
        }
    try:
        since = date.fromisoformat(holdout_since)
    except ValueError:
        since = target
        holdout_since = target.isoformat()
    holdout_rows = [
        row for row in outcomes if date.fromisoformat(row["rec_date"]) > since
    ]
    holdout_book = _cohort_book(holdout_rows)
    holdout_pass, holdout_reasons = _book_passes(holdout_book)
    if holdout_pass and not resource_allocation_ready:
        holdout_reasons = [f"resource_allocation_gate:{resource_allocation_status}"]
    return {
        "status": (
            "live_auto_apply_ready"
            if holdout_pass and resource_allocation_ready
            else "forward_holdout_armed"
        ),
        "holdout_armed_since": holdout_since,
        "base_pass": True,
        "base_reasons": [],
        "forward_holdout_book": holdout_book,
        "forward_holdout_pass": holdout_pass,
        "forward_holdout_reasons": holdout_reasons,
    }


def evaluate_post_apply(
    prior_policy: dict[str, Any], outcomes: list[dict[str, Any]]
) -> dict[str, Any]:
    try:
        campaign_start = date.fromisoformat(
            str(prior_policy.get("holdout_armed_since") or "")
        )
    except ValueError:
        campaign_start = None
    rows: list[dict[str, Any]] = []
    if campaign_start is not None:
        for row in outcomes:
            if row.get("lookup_attention_weight_runtime_policy_eligible") is not True:
                continue
            try:
                policy_source_date = date.fromisoformat(
                    str(row.get("lookup_attention_weight_policy_source_date") or "")
                )
            except ValueError:
                continue
            if policy_source_date >= campaign_start:
                rows.append(row)
    book = _cohort_book(rows)
    mature = _sample_floor_passes(book)
    passed, reasons = _book_passes(book)
    candidate_worst = book["candidate"]["worst_net_return_pct"]
    live_predecessor = (
        prior_policy.get("status") == "live_auto_apply_ready"
        or prior_policy.get("campaign_live_started") is True
    )
    emergency_rollback = bool(
        live_predecessor
        and candidate_worst is not None
        and candidate_worst < MIN_WORST_NET_RETURN_PCT
    )
    rollback = bool(
        live_predecessor and (emergency_rollback or (mature and not passed))
    )
    status = (
        "not_applicable_before_live_apply"
        if not live_predecessor
        else (
            "rollback_worst_loss_guard"
            if emergency_rollback
            else (
                "rollback_mature_ev_or_tail_failure"
                if rollback
                else "pass_mature" if mature and passed else "collecting"
            )
        )
    )
    return {
        "status": status,
        "mature": mature,
        "pass": passed if mature else None,
        "reasons": reasons,
        "rollback_triggered": rollback,
        "campaign_start": campaign_start.isoformat() if campaign_start else None,
        "book": book,
    }


def _evidence(
    base: dict[str, Any],
    holdout: dict[str, Any],
    post_apply: dict[str, Any],
    *,
    post_apply_mature: bool,
) -> dict[str, Any]:
    return {
        **(
            {
                "economic_contract_version": NET_ECONOMIC_CONTRACT,
                **{
                    prefix + name + "_" + field: book[name].get(field)
                    for prefix, book in (
                        ("", base),
                        ("forward_holdout_", holdout),
                        ("post_apply_", post_apply),
                    )
                    for name in ("candidate", "control")
                    for field in ("net_pnl_krw", "net_return_robust_se_pct")
                },
            }
            if base.get("economic_contract_version") == NET_ECONOMIC_CONTRACT
            else {}
        ),
        "completed_outcome_count": base["all"]["completed_outcome_count"],
        "trading_date_count": base["all"]["trading_date_count"],
        "candidate_completed_outcome_count": base["candidate"][
            "completed_outcome_count"
        ],
        "candidate_trading_date_count": base["candidate"]["trading_date_count"],
        "control_completed_outcome_count": base["control"]["completed_outcome_count"],
        "control_trading_date_count": base["control"]["trading_date_count"],
        "candidate_source_quality_adjusted_ev_pct": base["candidate"][
            "source_quality_adjusted_ev_pct"
        ],
        "control_source_quality_adjusted_ev_pct": base["control"][
            "source_quality_adjusted_ev_pct"
        ],
        "candidate_control_ev_uplift_pct": base["candidate_control_ev_uplift_pct"],
        "candidate_downside_p10_pct": base["candidate"]["downside_p10_pct"],
        "control_downside_p10_pct": base["control"]["downside_p10_pct"],
        "candidate_worst_net_return_pct": base["candidate"]["worst_net_return_pct"],
        "forward_holdout_completed_outcome_count": holdout["all"][
            "completed_outcome_count"
        ],
        "forward_holdout_trading_date_count": holdout["all"]["trading_date_count"],
        "forward_holdout_candidate_completed_outcome_count": holdout["candidate"][
            "completed_outcome_count"
        ],
        "forward_holdout_candidate_trading_date_count": holdout["candidate"][
            "trading_date_count"
        ],
        "forward_holdout_control_completed_outcome_count": holdout["control"][
            "completed_outcome_count"
        ],
        "forward_holdout_control_trading_date_count": holdout["control"][
            "trading_date_count"
        ],
        "forward_holdout_candidate_source_quality_adjusted_ev_pct": holdout[
            "candidate"
        ]["source_quality_adjusted_ev_pct"],
        "forward_holdout_control_source_quality_adjusted_ev_pct": holdout["control"][
            "source_quality_adjusted_ev_pct"
        ],
        "forward_holdout_candidate_control_ev_uplift_pct": holdout[
            "candidate_control_ev_uplift_pct"
        ],
        "forward_holdout_candidate_downside_p10_pct": holdout["candidate"][
            "downside_p10_pct"
        ],
        "forward_holdout_control_downside_p10_pct": holdout["control"][
            "downside_p10_pct"
        ],
        "forward_holdout_candidate_worst_net_return_pct": holdout["candidate"][
            "worst_net_return_pct"
        ],
        "post_apply_mature": post_apply_mature,
        "post_apply_completed_outcome_count": post_apply["all"][
            "completed_outcome_count"
        ],
        "post_apply_trading_date_count": post_apply["all"]["trading_date_count"],
        "post_apply_candidate_completed_outcome_count": post_apply["candidate"][
            "completed_outcome_count"
        ],
        "post_apply_candidate_trading_date_count": post_apply["candidate"][
            "trading_date_count"
        ],
        "post_apply_control_completed_outcome_count": post_apply["control"][
            "completed_outcome_count"
        ],
        "post_apply_control_trading_date_count": post_apply["control"][
            "trading_date_count"
        ],
        "post_apply_candidate_source_quality_adjusted_ev_pct": post_apply["candidate"][
            "source_quality_adjusted_ev_pct"
        ],
        "post_apply_control_source_quality_adjusted_ev_pct": post_apply["control"][
            "source_quality_adjusted_ev_pct"
        ],
        "post_apply_candidate_control_ev_uplift_pct": post_apply[
            "candidate_control_ev_uplift_pct"
        ],
        "post_apply_candidate_downside_p10_pct": post_apply["candidate"][
            "downside_p10_pct"
        ],
        "post_apply_control_downside_p10_pct": post_apply["control"][
            "downside_p10_pct"
        ],
        "post_apply_candidate_worst_net_return_pct": post_apply["candidate"][
            "worst_net_return_pct"
        ],
    }


def _economic_acceptance(report: dict[str, Any]) -> dict[str, Any]:
    """Bounded maintenance evidence, never an additional promotion/BUY gate."""
    lineage = report.get("lineage") or {}
    audited = {
        row["target_date"]
        for row in (report.get("natural_observation_audit") or {}).get("audits", [])
        if row.get("status") == "pass"
    }
    days = sorted(audited & set(lineage.get("observed_event_dates", [])))
    rows = report.get("outcomes") or []
    valid_rows = [row for row in rows if row["rec_date"] in days]
    total_net = math.fsum(row["net_pnl_krw"] for row in valid_rows)
    receipt_rows = [
        row
        for row in rows
        if row["rec_date"] == report["target_date"]
        and row.get("lookup_attention_weight_runtime_policy_eligible") is True
    ]
    status = report["status"]
    due = len(days) >= 20
    next_action = (
        "verify_next_preopen_receipt_then_runtime_consumption_and_net"
        if status == "live_auto_apply_ready"
        else (
            "repair_source"
            if status == "source_quality_blocked"
            else (
                "review_integrate_or_retire_no_evidence_or_edge"
                if due
                else "keep_collecting"
            )
        )
    )
    return {
        "schema": "scanner_lookup_attention_natural_acceptance_v1",
        "metric_role": "funnel_count",
        "decision_authority": "diagnostic_only_no_runtime_mutation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "valid_observation_dates": days,
        "valid_observation_day_count": len(days),
        "bounded_review_after_valid_days": 20,
        "maintenance_review_due": due,
        "next_action": next_action,
        "blocking_stage": (
            "lookup_observation"
            if not lineage.get("valid_observation_count")
            else (
                "receipt_or_completed_cost_join"
                if not rows
                else (
                    "independent_forward_holdout"
                    if status == "forward_holdout_armed"
                    else status
                )
            )
        ),
        "full_completed_per_valid_source_day": (
            len(valid_rows) / len(days) if days else None
        ),
        "net_per_valid_source_day_krw": (
            total_net / len(days) if days and valid_rows else None
        ),
        "net_scope": "completed_full_only_excludes_open_missing_and_partial",
        "current_date_policy_bound_completed_count": len(receipt_rows),
        "pid_consumption_status": (
            "policy_bound_outcomes_observed" if receipt_rows else "not_observed"
        ),
        "incremental_profit_status": "not_proven_observational_cohorts_not_causal_pairs",
        "cost_basis": "actual_fill_prices_with_fixed_comparison_fees_and_tax_not_broker_cost_reconciliation",
        "missing_capital_time_is_diagnostic_only": True,
    }


def build_artifacts(target: date) -> tuple[dict[str, Any], dict[str, Any]]:
    observations, lineage = collect_lineage(target)
    resource_pair_rows = list(lineage.pop("_resource_pair_rows", []))
    resource_allocation = _resource_allocation_pair_book(
        resource_pair_rows,
        invalid_row_count=int(lineage["invalid_resource_pair_count"]),
    )
    start = date.fromisoformat(lineage["window_start"])
    facts = load_completed_facts(start, target)
    symbols, master = _latest_symbol_master(target)
    outcomes, exclusions = join_completed_outcomes(
        observations, facts, eligible_symbols=symbols
    )
    prior_policy = _latest_prior_policy(target)
    base_rows = _base_rows_for_prior(outcomes, prior_policy)
    base_book = _cohort_book(base_rows)
    cohort_funnel = _cohort_funnel(observations, outcomes)
    quality = _source_quality(
        target,
        {date.fromisoformat(str(row["rec_date"])) for row in outcomes + base_rows}
        | {
            date.fromisoformat(row["observation_date"])
            for row in resource_allocation["pairs"]
        },
    )
    lineage_contract_pass = _lineage_contract_pass(lineage)
    decision = decide_promotion(
        target,
        base_book,
        outcomes,
        source_quality_pass=(
            quality["status"] == "pass"
            and master["status"] == "pass"
            and lineage_contract_pass
        ),
        prior_policy=prior_policy,
        resource_allocation_ready=resource_allocation["ready_for_live_gate"],
        resource_allocation_status=str(resource_allocation["status"]),
    )
    status = decision["status"]
    combined_source_quality_pass = bool(
        quality["status"] == "pass"
        and master["status"] == "pass"
        and lineage_contract_pass
    )
    post_apply_attribution = evaluate_post_apply(prior_policy, outcomes)
    post_apply_book = post_apply_attribution["book"]
    post_apply_mature = post_apply_attribution["mature"]
    if post_apply_attribution["rollback_triggered"]:
        status = "hold_no_edge"
    campaign = dict(prior_policy.get("campaign_base") or {})
    if campaign and not campaign["base_book"].get("economic_contract_version"):
        # Re-evaluate verified frozen real rows, preserving the original arm
        # boundary and immutable predecessor hash. Never mix in forward rows.
        predecessor_hash = campaign["artifact_sha256"]
        campaign = _freeze_base(base_rows, campaign["arm_date"])
        campaign["predecessor_campaign_sha256"] = predecessor_hash
        campaign["artifact_sha256"] = canonical_sha256(
            {k: v for k, v in campaign.items() if k != "artifact_sha256"}
        )
    if decision["holdout_armed_since"] and not campaign and decision["base_pass"]:
        campaign = _freeze_base(base_rows, decision["holdout_armed_since"])
    if not decision["holdout_armed_since"] or status == "hold_no_edge":
        campaign = {}
    evidence = _evidence(
        base_book,
        decision["forward_holdout_book"],
        post_apply_book,
        post_apply_mature=post_apply_mature,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target.isoformat(),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "decision_contract_version": DECISION_CONTRACT_VERSION,
        "metric_role": "primary_ev",
        "decision_authority": DECISION_AUTHORITY,
        "window_policy": f"rolling_{ROLLING_CALENDAR_DAYS}_calendar_days_clean_post_rollout",
        "sample_floor": "base_and_independent_forward_holdout_each_total20_dates5_candidate10_control10_cohort_dates3",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "daily_audit_exact_lineage_full_fill_official_common_stock_and_effective_cost",
        "forbidden_uses": FORBIDDEN_USES,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": status == "live_auto_apply_ready",
        "operator_approval_required": False,
        "user_authority": USER_AUTHORITY,
        "lineage": lineage,
        "lineage_row_exclusion": {
            "status": "applied",
            "excluded_invalid_observation_count": lineage["invalid_observation_count"],
            "included_valid_observation_count": lineage["valid_observation_count"],
            "whole_window_blocked": False,
            "policy": "exclude_exact_invalid_lookup_observation_rows",
        },
        "cohort_funnel": cohort_funnel,
        "resource_allocation_pair": resource_allocation,
        "resource_pair_rows": resource_pair_rows,
        "source_quality": quality,
        "official_symbol_master": master,
        "runtime_policy_provenance_status": (
            "pass" if lineage_contract_pass else "blocked"
        ),
        "cost_contract": {
            **COST_CONTRACT,
            "contract_sha256": canonical_sha256(COST_CONTRACT),
        },
        "full_fill_contract": FULL_FILL_CONTRACT,
        "exclusions": exclusions,
        "base_book": base_book,
        "base_outcomes": base_rows,
        "holdout_armed_since": decision["holdout_armed_since"],
        "campaign_base": campaign,
        "campaign_live_started": bool(
            campaign
            and (
                prior_policy.get("campaign_live_started")
                or status == "live_auto_apply_ready"
            )
        ),
        "base_gate": {
            "pass": decision["base_pass"],
            "reasons": decision["base_reasons"],
        },
        "forward_holdout_book": decision["forward_holdout_book"],
        "forward_holdout_gate": {
            "pass": decision["forward_holdout_pass"],
            "reasons": decision["forward_holdout_reasons"],
        },
        "post_apply_attribution": post_apply_attribution,
        "policy_evidence_sha256": canonical_sha256(evidence),
        "outcome_count": len(outcomes),
        "outcomes": outcomes,
        "natural_observation_audit": _source_quality(
            target,
            {date.fromisoformat(d) for d in lineage.get("observed_event_dates", [])},
        ),
        "rollback": {
            "trigger": "missing_invalid_stale_policy_or_any_source_evidence_guard_failure",
            "bonus_points": 0.0,
            "effect": "legacy_same_tier_sort_score_restored",
        },
    }
    report["economic_acceptance"] = _economic_acceptance(report)
    report["artifact_sha256"] = canonical_sha256(report)
    policy = {
        "schema_version": POLICY_SCHEMA_VERSION,
        "report_type": POLICY_REPORT_TYPE,
        "target_date": target.isoformat(),
        "status": status,
        "decision_contract_version": DECISION_CONTRACT_VERSION,
        "decision_authority": DECISION_AUTHORITY,
        "activation_mode": ACTIVATION_MODE,
        "user_authority": USER_AUTHORITY,
        "operator_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": status == "live_auto_apply_ready",
        "source_quality_status": (
            "pass" if combined_source_quality_pass else "blocked"
        ),
        "holdout_armed_since": decision["holdout_armed_since"],
        "campaign_base": campaign,
        "campaign_live_started": report["campaign_live_started"],
        "source_report_artifact_sha256": report["artifact_sha256"],
        "policy": {
            "policy_version": POLICY_VERSION,
            "min_lookup_attention_score": MIN_SCORE,
            "max_bonus_points": MAX_BONUS_POINTS,
            "max_source_age_sec": MAX_SOURCE_AGE_SEC,
            "rollback_bonus_points": 0.0,
            "same_priority_tier_only": True,
            "priority_tier_or_slot_change_allowed": False,
            "weight_formula": "linear_above_min_score_capped_at_max_bonus",
            "eligible_venues": ELIGIBLE_VENUES,
            "eligible_session_buckets": ELIGIBLE_SESSION_BUCKETS,
        },
        "evidence": evidence,
        "forbidden_uses": FORBIDDEN_USES,
    }
    policy["artifact_sha256"] = canonical_sha256(policy)
    return report, policy


def validate_artifact_pair(
    report: dict[str, Any], policy: dict[str, Any], *, target: date
) -> list[str]:
    if not isinstance(report, dict) or not isinstance(policy, dict):
        return ["report_or_policy_not_object"]
    issues: list[str] = []
    new_economics = (
        isinstance(policy.get("evidence"), dict)
        and policy["evidence"].get("economic_contract_version") == NET_ECONOMIC_CONTRACT
    )
    if target >= NET_ECONOMIC_EFFECTIVE_FROM and not new_economics:
        issues.append("net_economic_contract_required")
    expected_report_scalar = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target.isoformat(),
        "metric_role": "primary_ev",
        "decision_authority": DECISION_AUTHORITY,
        "window_policy": (
            f"rolling_{ROLLING_CALENDAR_DAYS}_calendar_days_clean_post_rollout"
        ),
        "sample_floor": "base_and_independent_forward_holdout_each_total20_dates5_candidate10_control10_cohort_dates3",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "daily_audit_exact_lineage_full_fill_official_common_stock_and_effective_cost",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "operator_approval_required": False,
        "user_authority": USER_AUTHORITY,
        "full_fill_contract": FULL_FILL_CONTRACT,
    }
    for key, expected in expected_report_scalar.items():
        if report.get(key) != expected:
            issues.append(f"report_contract_mismatch:{key}")
    try:
        report_forbidden_uses = set(report.get("forbidden_uses") or [])
    except TypeError:
        report_forbidden_uses = set()
    if not set(FORBIDDEN_USES).issubset(report_forbidden_uses):
        issues.append("report_forbidden_uses_incomplete")
    cost_contract = (
        report.get("cost_contract")
        if isinstance(report.get("cost_contract"), dict)
        else {}
    )
    if any(cost_contract.get(key) != value for key, value in COST_CONTRACT.items()):
        issues.append("report_cost_contract_invalid")
    if cost_contract.get("contract_sha256") != canonical_sha256(COST_CONTRACT):
        issues.append("report_cost_contract_sha256_invalid")
    try:
        report_hash = canonical_sha256(
            {key: value for key, value in report.items() if key != "artifact_sha256"}
        )
    except (TypeError, ValueError):
        report_hash = ""
    if report.get("artifact_sha256") != report_hash:
        issues.append("report_artifact_sha256_invalid")
    if policy.get("source_report_artifact_sha256") != report.get("artifact_sha256"):
        issues.append("policy_report_hash_mismatch")
    try:
        policy_evidence_hash = canonical_sha256(policy.get("evidence"))
    except (TypeError, ValueError):
        policy_evidence_hash = ""
    if (
        not policy_evidence_hash
        or report.get("policy_evidence_sha256") != policy_evidence_hash
    ):
        issues.append("policy_report_evidence_hash_mismatch")
    base_book = report.get("base_book")
    holdout_book = report.get("forward_holdout_book")
    post_apply = report.get("post_apply_attribution")
    post_apply_payload = post_apply if isinstance(post_apply, dict) else {}
    post_apply_mature_value = post_apply_payload.get("mature")
    if new_economics:
        try:
            rows = report["outcomes"]
            arm = report.get("holdout_armed_since")
            campaign = report.get("campaign_base") or {}
            if (
                not isinstance(rows, list)
                or any(
                    not isinstance(row, dict)
                    or row.get("cohort") not in {"candidate", "control"}
                    or not (
                        ROLLOUT_DATE.isoformat()
                        <= row["rec_date"]
                        <= target.isoformat()
                    )
                    or not is_krx_trading_day(date.fromisoformat(row["rec_date"]))
                    or _finite(row.get("net_return_pct")) is None
                    or _finite(row.get("net_pnl_krw")) is None
                    or _finite(row.get("buy_notional_krw")) is None
                    or row["buy_notional_krw"] <= 0
                    or not math.isclose(
                        row["net_return_pct"],
                        row["net_pnl_krw"] / row["buy_notional_krw"] * 100,
                        abs_tol=1e-7,
                    )
                    for row in rows
                )
                or len({r["recommendation_id"] for r in rows}) != len(rows)
            ):
                raise ValueError("outcome_contract_invalid")
            if report.get("outcome_count") != len(rows):
                raise ValueError("outcome_count_invalid")
            base_rows = report.get(
                "base_outcomes", campaign["outcomes"] if campaign else rows
            )
            if campaign and base_rows != campaign["outcomes"]:
                issues.append("frozen_base_outcomes_mismatch")
            expected_base = _cohort_book(base_rows)
            # Blocked source and pre-arm reports intentionally have empty holdout.
            source_pass = (
                report.get("source_quality", {}).get("status") == "pass"
                and report.get("official_symbol_master", {}).get("status") == "pass"
                and report.get("runtime_policy_provenance_status") == "pass"
            )
            holdout_rows = (
                [r for r in rows if r["rec_date"] > arm] if arm and source_pass else []
            )
            if base_book != expected_base or holdout_book != _cohort_book(holdout_rows):
                issues.append("economic_books_not_reproducible")
            expected_post = evaluate_post_apply(policy, rows)
            if post_apply_payload.get("book") != expected_post["book"]:
                issues.append("post_apply_book_not_reproducible")
            if post_apply_mature_value is not expected_post["mature"]:
                issues.append("post_apply_maturity_not_reproducible")
            if report.get("economic_acceptance") != _economic_acceptance(report):
                issues.append("economic_acceptance_not_reproducible")
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            issues.append("real_economic_outcomes_invalid")
    if not isinstance(post_apply_mature_value, bool):
        issues.append("post_apply_mature_not_boolean")
    if not isinstance(post_apply_payload.get("rollback_triggered"), bool):
        issues.append("post_apply_rollback_not_boolean")
    try:
        expected_evidence = _evidence(
            base_book,
            holdout_book,
            post_apply_payload["book"],
            post_apply_mature=post_apply_mature_value,
        )
    except (KeyError, TypeError, ValueError):
        expected_evidence = None
        issues.append("report_evidence_source_books_invalid")
    if expected_evidence is not None and policy.get("evidence") != expected_evidence:
        issues.append("policy_evidence_not_derived_from_report_books")
    try:
        policy_hash = canonical_sha256(
            {key: value for key, value in policy.items() if key != "artifact_sha256"}
        )
    except (TypeError, ValueError):
        policy_hash = ""
    if policy.get("artifact_sha256") != policy_hash:
        issues.append("policy_artifact_sha256_invalid")
    if policy.get("status") != report.get("status"):
        issues.append("policy_report_status_mismatch")
    status = str(report.get("status") or "")
    allowed_statuses = {
        "hold_sample",
        "hold_no_edge",
        "source_quality_blocked",
        "forward_holdout_armed",
        "live_auto_apply_ready",
    }
    if status not in allowed_statuses:
        issues.append("promotion_status_invalid")
    expected_allowed = report.get("status") == "live_auto_apply_ready"
    report_decision_contract = str(
        report.get("decision_contract_version") or ""
    ).strip()
    policy_decision_contract = str(
        policy.get("decision_contract_version") or ""
    ).strip()
    if report_decision_contract != policy_decision_contract:
        issues.append("policy_report_decision_contract_mismatch")
    if report_decision_contract or policy_decision_contract:
        if report_decision_contract != DECISION_CONTRACT_VERSION and not (
            not expected_allowed
            and report_decision_contract == LEGACY_DECISION_CONTRACT_VERSION
        ):
            issues.append("report_decision_contract_version_invalid")
        if policy_decision_contract != DECISION_CONTRACT_VERSION and not (
            not expected_allowed
            and policy_decision_contract == LEGACY_DECISION_CONTRACT_VERSION
        ):
            issues.append("policy_decision_contract_version_invalid")
    elif expected_allowed:
        issues.append("live_policy_decision_contract_version_missing")
    if (
        policy.get("allowed_runtime_apply") is not expected_allowed
        or report.get("allowed_runtime_apply") is not expected_allowed
    ):
        issues.append("allowed_runtime_apply_mismatch")
    expected_policy_scalar = {
        "schema_version": POLICY_SCHEMA_VERSION,
        "report_type": POLICY_REPORT_TYPE,
        "target_date": target.isoformat(),
        "decision_authority": DECISION_AUTHORITY,
        "activation_mode": (
            ACTIVATION_MODE
            if policy_decision_contract == DECISION_CONTRACT_VERSION
            else LEGACY_ACTIVATION_MODE
        ),
        "user_authority": USER_AUTHORITY,
        "operator_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    for key, expected in expected_policy_scalar.items():
        if policy.get(key) != expected:
            issues.append(f"policy_contract_mismatch:{key}")
    policy_values = (
        policy.get("policy") if isinstance(policy.get("policy"), dict) else {}
    )
    expected_policy_values = {
        "policy_version": POLICY_VERSION,
        "min_lookup_attention_score": MIN_SCORE,
        "max_bonus_points": MAX_BONUS_POINTS,
        "max_source_age_sec": MAX_SOURCE_AGE_SEC,
        "rollback_bonus_points": 0.0,
        "same_priority_tier_only": True,
        "priority_tier_or_slot_change_allowed": False,
        "weight_formula": "linear_above_min_score_capped_at_max_bonus",
        "eligible_venues": ELIGIBLE_VENUES,
        "eligible_session_buckets": ELIGIBLE_SESSION_BUCKETS,
    }
    for key, expected in expected_policy_values.items():
        if policy_values.get(key) != expected:
            issues.append(f"policy_value_mismatch:{key}")
    try:
        forbidden_uses = set(policy.get("forbidden_uses") or [])
    except TypeError:
        forbidden_uses = set()
    if not set(FORBIDDEN_USES).issubset(forbidden_uses):
        issues.append("policy_forbidden_uses_incomplete")
    if not isinstance(policy.get("evidence"), dict):
        issues.append("policy_evidence_missing")
    holdout_text = str(policy.get("holdout_armed_since") or "")
    if holdout_text:
        try:
            holdout_date = date.fromisoformat(holdout_text)
        except ValueError:
            issues.append("holdout_armed_since_invalid")
        else:
            if holdout_date > target or not is_krx_trading_day(holdout_date):
                issues.append("holdout_armed_since_out_of_range")
        if report.get("holdout_armed_since") != holdout_text:
            issues.append("policy_report_holdout_mismatch")
    elif status in {"forward_holdout_armed", "live_auto_apply_ready"}:
        issues.append("holdout_armed_since_invalid")

    if report_decision_contract == DECISION_CONTRACT_VERSION:
        campaign = report.get("campaign_base")
        if campaign != policy.get("campaign_base"):
            issues.append("campaign_base_report_policy_mismatch")
        if report.get("campaign_live_started") != policy.get(
            "campaign_live_started"
        ) or not isinstance(report.get("campaign_live_started"), bool):
            issues.append("campaign_live_state_invalid")
        if campaign or status in {"forward_holdout_armed", "live_auto_apply_ready"}:
            if not _campaign_valid(campaign, target):
                issues.append("campaign_base_contract_invalid")
            elif (
                campaign["base_book"] != base_book
                or campaign["arm_date"] != holdout_text
            ):
                issues.append("campaign_base_not_frozen")
        lineage = (
            report.get("lineage") if isinstance(report.get("lineage"), dict) else {}
        )
        row_exclusion = (
            report.get("lineage_row_exclusion")
            if isinstance(report.get("lineage_row_exclusion"), dict)
            else {}
        )
        cohort_funnel = (
            report.get("cohort_funnel")
            if isinstance(report.get("cohort_funnel"), dict)
            else {}
        )
        resource_pair = (
            report.get("resource_allocation_pair")
            if isinstance(report.get("resource_allocation_pair"), dict)
            else {}
        )
        lineage_count_keys = (
            "valid_observation_count",
            "invalid_observation_count",
            "invalid_fill_contract_count",
            "invalid_runtime_policy_provenance_count",
            "malformed_json_line_count",
            "non_object_json_line_count",
            "full_fill_observation_count",
            "partial_fill_observation_count",
            "fill_contract_invalid_observation_count",
            "fill_receipt_missing_count",
            "invalid_resource_pair_count",
            "resource_pair_row_count",
        )
        lineage_counts_valid = not any(
            not isinstance(lineage.get(key), int)
            or isinstance(lineage.get(key), bool)
            or int(lineage.get(key)) < 0
            for key in lineage_count_keys
        )
        if not lineage_counts_valid:
            issues.append("lineage_count_contract_invalid")
        else:
            classified_observations = sum(
                int(lineage[key])
                for key in (
                    "full_fill_observation_count",
                    "partial_fill_observation_count",
                    "fill_contract_invalid_observation_count",
                    "fill_receipt_missing_count",
                )
            )
            if classified_observations != lineage["valid_observation_count"]:
                issues.append("lineage_fill_class_conservation_invalid")
            expected_lineage_status = (
                "pass" if _lineage_contract_pass(lineage) else "blocked"
            )
            if (
                report.get("runtime_policy_provenance_status")
                != expected_lineage_status
            ):
                issues.append("lineage_runtime_status_mismatch")
        if not (
            row_exclusion.get("status") == "applied"
            and row_exclusion.get("excluded_invalid_observation_count")
            == lineage.get("invalid_observation_count")
            and row_exclusion.get("included_valid_observation_count")
            == lineage.get("valid_observation_count")
            and row_exclusion.get("whole_window_blocked") is False
        ):
            issues.append("lineage_row_exclusion_contract_invalid")
        funnel_books = [
            cohort_funnel.get(name) if isinstance(cohort_funnel.get(name), dict) else {}
            for name in ("all", "candidate", "control")
        ]
        funnel_count_keys = (
            "valid_observation_count",
            "full_fill_observation_count",
            "partial_fill_observation_count",
            "fill_contract_invalid_count",
            "fill_receipt_missing_count",
            "completed_outcome_count",
        )
        if any(
            not isinstance(book.get(key), int)
            or isinstance(book.get(key), bool)
            or int(book.get(key)) < 0
            for book in funnel_books
            for key in funnel_count_keys
        ):
            issues.append("cohort_funnel_count_contract_invalid")
        else:
            all_book, candidate_book, control_book = funnel_books
            for key in funnel_count_keys:
                if all_book[key] != candidate_book[key] + control_book[key]:
                    issues.append(f"cohort_funnel_conservation_invalid:{key}")
            expected_funnel_counts = {
                "valid_observation_count": lineage.get("valid_observation_count"),
                "full_fill_observation_count": lineage.get(
                    "full_fill_observation_count"
                ),
                "partial_fill_observation_count": lineage.get(
                    "partial_fill_observation_count"
                ),
                "fill_contract_invalid_count": lineage.get(
                    "fill_contract_invalid_observation_count"
                ),
                "fill_receipt_missing_count": lineage.get("fill_receipt_missing_count"),
                "completed_outcome_count": report.get("outcome_count"),
            }
            for key, expected in expected_funnel_counts.items():
                if all_book.get(key) != expected:
                    issues.append(f"cohort_funnel_lineage_mismatch:{key}")
        resource_rows = report.get("resource_pair_rows")
        resource_start = _resource_window_start(target).isoformat()
        if isinstance(resource_rows, list) and any(
            not isinstance(row, dict)
            or not (
                resource_start
                <= str(row.get("observation_date") or "")
                <= target.isoformat()
            )
            for row in resource_rows
        ):
            issues.append("resource_row_date_out_of_scope")
        try:
            expected_resource = (
                _resource_allocation_pair_book(
                    resource_rows,
                    invalid_row_count=lineage["invalid_resource_pair_count"],
                )
                if isinstance(resource_rows, list)
                else None
            )
        except (KeyError, TypeError, ValueError, OverflowError):
            expected_resource = None
        if expected_resource is None or resource_pair != expected_resource:
            issues.append("resource_allocation_evidence_not_reproducible")
        if isinstance(resource_rows, list) and len(resource_rows) != lineage.get(
            "resource_pair_row_count"
        ):
            issues.append("resource_allocation_pair_row_count_mismatch")
        if isinstance(resource_rows, list) and sum(
            not valid_resource_row(row) for row in resource_rows
        ) != lineage.get("invalid_resource_pair_count"):
            issues.append("invalid_resource_pair_count_mismatch")
        if expected_allowed and (
            not expected_resource or not expected_resource["ready_for_live_gate"]
        ):
            issues.append("live_policy_resource_allocation_pair_not_ready")
    source_quality = (
        report.get("source_quality")
        if isinstance(report.get("source_quality"), dict)
        else {}
    )
    symbol_master = (
        report.get("official_symbol_master")
        if isinstance(report.get("official_symbol_master"), dict)
        else {}
    )
    expected_source_quality = (
        "pass"
        if source_quality.get("status") == "pass"
        and symbol_master.get("status") == "pass"
        and report.get("runtime_policy_provenance_status") == "pass"
        else "blocked"
    )
    if policy.get("source_quality_status") != expected_source_quality:
        issues.append("policy_source_quality_status_mismatch")
    base_gate = (
        report.get("base_gate") if isinstance(report.get("base_gate"), dict) else {}
    )
    holdout_gate = (
        report.get("forward_holdout_gate")
        if isinstance(report.get("forward_holdout_gate"), dict)
        else {}
    )
    try:
        calculated_base_pass, _ = _book_passes(base_book)
        calculated_holdout_pass, _ = _book_passes(holdout_book)
    except (KeyError, TypeError, ValueError):
        calculated_base_pass = False
        calculated_holdout_pass = False
        issues.append("report_gate_source_books_invalid")
    if status in {"forward_holdout_armed", "live_auto_apply_ready"}:
        if expected_source_quality != "pass":
            issues.append("promotion_policy_source_quality_not_pass")
        if base_gate.get("pass") is not True or not calculated_base_pass:
            issues.append("promotion_policy_base_gate_not_pass")
        if holdout_gate.get("pass") is not calculated_holdout_pass:
            issues.append("promotion_policy_holdout_gate_inconsistent")
    resource_ready_for_live = bool(
        isinstance(report.get("resource_allocation_pair"), dict)
        and report["resource_allocation_pair"].get("ready_for_live_gate") is True
    )
    if (
        status == "forward_holdout_armed"
        and calculated_holdout_pass
        and resource_ready_for_live
    ):
        issues.append("forward_holdout_status_stale_after_gate_pass")
    if expected_allowed:
        if expected_source_quality != "pass":
            issues.append("live_policy_source_quality_not_pass")
        if base_gate.get("pass") is not True:
            issues.append("live_policy_base_gate_not_pass")
        if holdout_gate.get("pass") is not True:
            issues.append("live_policy_forward_holdout_gate_not_pass")
        if post_apply_payload.get("rollback_triggered") is True:
            issues.append("live_policy_post_apply_rollback_triggered")
    if expected_allowed:
        issues.extend(validate_policy_payload(policy, source_date=target))
    return issues


def _markdown(report: dict[str, Any]) -> str:
    base = report["base_book"]
    holdout = report["forward_holdout_book"]
    post_apply = report["post_apply_attribution"]
    funnel = report.get("cohort_funnel") or {}
    candidate_funnel = funnel.get("candidate") or {}
    control_funnel = funnel.get("control") or {}
    resource_pair = report.get("resource_allocation_pair") or {}
    return "\n".join(
        [
            f"# Scanner lookup-attention tuning — {report['target_date']}",
            "",
            f"- decision: `{report['status']}`",
            f"- base completed/dates: `{base['all']['completed_outcome_count']}/{base['all']['trading_date_count']}`",
            f"- base candidate/control EV: `{base['candidate']['source_quality_adjusted_ev_pct']}` / `{base['control']['source_quality_adjusted_ev_pct']}`",
            f"- base EV uplift: `{base['candidate_control_ev_uplift_pct']}`",
            f"- economic contract: `{base.get('economic_contract_version', 'legacy_fixed_uplift')}`; candidate/control robust SE: `{base['candidate'].get('net_return_robust_se_pct')}` / `{base['control'].get('net_return_robust_se_pct')}`",
            "- economic rule: positive candidate net and candidate/control increment after 2-SE robustness margins; no fixed minimum uplift; not a causal confidence interval.",
            f"- natural acceptance / bounded maintenance: `{report.get('economic_acceptance', {})}`",
            f"- candidate net per capital-hour: `{base['candidate'].get('net_per_capital_hour')}`; missing duration remains null, not an approval blocker.",
            f"- candidate/control observations: `{candidate_funnel.get('valid_observation_count', 0)}/{control_funnel.get('valid_observation_count', 0)}`",
            f"- candidate/control full-fill: `{candidate_funnel.get('full_fill_observation_count', 0)}/{control_funnel.get('full_fill_observation_count', 0)}`",
            f"- resource allocation pair: `{resource_pair.get('status', 'not_observed')}` generations=`{resource_pair.get('paired_generation_count', 0)}` dates=`{resource_pair.get('trading_date_count', 0)}` reordered=`{resource_pair.get('reordered_generation_count', 0)}`",
            f"- resolved marginal pairs/dates: `{resource_pair.get('resolved_pair_count', 0)}/{resource_pair.get('resolved_date_count', 0)}`; missing observed labels=`{resource_pair.get('unobserved_pair_count', 0)}`",
            f"- marginal snapshot net uplift / incoming return: `{resource_pair.get('source_quality_adjusted_ev_pct')}` / `{resource_pair.get('incoming_snapshot_ev_pct')}` (source-only opportunity proxy, not real execution EV)",
            f"- resource retention review: `{resource_pair.get('retention_review', 'collecting')}`; excluded partitions=`{resource_pair.get('excluded_partition_counts', {})}`",
            f"- immutable base arm: `{(report.get('campaign_base') or {}).get('arm_date', 'not_armed')}`",
            f"- forward holdout completed/dates: `{holdout['all']['completed_outcome_count']}/{holdout['all']['trading_date_count']}`",
            f"- post-apply status: `{post_apply['status']}`",
            f"- post-apply completed/dates: `{post_apply['book']['all']['completed_outcome_count']}/{post_apply['book']['all']['trading_date_count']}`",
            f"- post-apply rollback: `{post_apply['rollback_triggered']}`",
            f"- source quality/master: `{report['source_quality']['status']}` / `{report['official_symbol_master']['status']}`",
            f"- runtime handoff allowed: `{report['allowed_runtime_apply']}`",
            "- scope: same-priority-tier bounded score only; rollback bonus is 0.",
            "- automation: validated candidate -> next PREOPEN immutable exact-date receipt -> runtime; no additional operator approval. No receipt means zero bonus.",
            "",
        ]
    )


def write_artifacts(
    report: dict[str, Any], policy: dict[str, Any]
) -> tuple[Path, Path, Path]:
    target = str(report["target_date"])
    report_json = REPORT_DIR / f"scanner_lookup_attention_tuning_{target}.json"
    report_md = REPORT_DIR / f"scanner_lookup_attention_tuning_{target}.md"
    policy_json = POLICY_DIR / f"scanner_lookup_attention_policy_{target}.json"
    _atomic_json(report_json, report)
    _atomic_write(report_md, _markdown(report))
    _atomic_json(policy_json, policy)
    return report_json, report_md, policy_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", "--date", dest="target_date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        target = date.fromisoformat(args.target_date)
    except ValueError as exc:
        parser.error(str(exc))
    if args.verify_only:
        report = _load_json(
            REPORT_DIR / f"scanner_lookup_attention_tuning_{target}.json"
        )
        policy = _load_json(
            POLICY_DIR / f"scanner_lookup_attention_policy_{target}.json"
        )
    else:
        report, policy = build_artifacts(target)
    issues = validate_artifact_pair(report, policy, target=target)
    if args.write and not args.verify_only and not issues:
        write_artifacts(report, policy)
    print(
        json.dumps(
            {
                "target_date": target.isoformat(),
                "status": report.get("status"),
                "issues": issues,
            },
            ensure_ascii=False,
        )
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
