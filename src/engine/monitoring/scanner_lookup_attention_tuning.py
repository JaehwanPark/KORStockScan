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
    DECISION_AUTHORITY,
    DECISION_CONTRACT_VERSION,
    ELIGIBLE_SESSION_BUCKETS,
    ELIGIBLE_VENUES,
    MAX_FUTURE_SKEW_SEC,
    MAX_BONUS_POINTS,
    MAX_SOURCE_AGE_SEC,
    MAX_TAIL_DEGRADATION_PCT,
    MIN_COHORT_COMPLETED,
    MIN_COHORT_DATES,
    MIN_EV_UPLIFT_PCT,
    MIN_SCORE,
    MIN_TOTAL_COMPLETED,
    MIN_TRADING_DATES,
    MIN_WORST_NET_RETURN_PCT,
    POLICY_DIR,
    POLICY_VERSION,
    REPORT_TYPE as POLICY_REPORT_TYPE,
    RESOURCE_PAIR_CONTRACT_VERSION,
    SCHEMA_VERSION as POLICY_SCHEMA_VERSION,
    USER_AUTHORITY,
    TUNING_REPORT_SCHEMA_VERSION,
    bonus_points_for_score,
    canonical_sha256,
    validate_policy_payload,
)
from src.utils.market_day import count_krx_trading_days, is_krx_trading_day

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
RESOURCE_PAIR_MIN_GENERATIONS = 20
RESOURCE_PAIR_MIN_TRADING_DATES = 5
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

    policy_payload = _load_json(
        POLICY_DIR / f"scanner_lookup_attention_policy_{source_date.isoformat()}.json"
    )
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
    invalid_resource_pair_count = 0
    event_file_count = 0
    cursor = start
    while cursor <= target:
        event_file_date = cursor
        path = _event_path(event_file_date)
        cursor += timedelta(days=1)
        if path is None:
            continue
        event_file_count += 1
        for event in _iter_events(path, parse_stats=parse_stats):
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            stage = str(event.get("stage") or "")
            if stage in {
                "scalping_scanner_candidate_promoted",
                "scalping_scanner_candidate_pruned",
            }:
                effective_venue = (
                    str(fields.get("effective_venue") or fields.get("venue") or "")
                    .strip()
                    .upper()
                )
                session = str(fields.get("market_session_bucket") or "").strip()
                resource_contract = str(
                    fields.get("lookup_attention_resource_pair_contract_version") or ""
                ).strip()
                resource_eligible = _bool(
                    fields.get("lookup_attention_resource_pair_eligible")
                )
                if resource_contract and (
                    resource_contract != RESOURCE_PAIR_CONTRACT_VERSION
                    or resource_eligible is None
                    or (
                        resource_eligible is True
                        and (
                            effective_venue not in ELIGIBLE_VENUES
                            or session not in ELIGIBLE_SESSION_BUCKETS
                        )
                    )
                ):
                    invalid_resource_pair_count += 1
                    continue
                if (
                    resource_contract == RESOURCE_PAIR_CONTRACT_VERSION
                    and resource_eligible is True
                    and effective_venue in ELIGIBLE_VENUES
                    and session in ELIGIBLE_SESSION_BUCKETS
                ):
                    generation_id = str(
                        fields.get("scanner_scan_generation_id") or ""
                    ).strip()
                    code = str(event.get("stock_code") or "").strip()[:6]
                    event_date_text = str(event.get("emitted_date") or "").strip()
                    score = _finite(
                        fields.get("lookup_attention_resource_snapshot_score")
                    )
                    base_priority_score = _finite(
                        fields.get(
                            "scanner_rank_priority_score_without_lookup_attention"
                        )
                    )
                    candidate_priority_score = _finite(
                        fields.get("scanner_rank_priority_score_with_lookup_attention")
                    )
                    formula_bonus = _finite(
                        fields.get(
                            "lookup_attention_resource_counterfactual_bonus_points"
                        )
                    )
                    scan_rank = _strict_int(fields.get("scanner_scan_rank"))
                    ranked_count = _strict_int(
                        fields.get("scanner_ranked_candidate_count")
                    )
                    rank_partition = _strict_int(
                        fields.get("scanner_rank_priority_rank_partition")
                    )
                    source_priority = _strict_int(
                        fields.get("scanner_rank_priority_source_rank")
                    )
                    flu_rate = _finite(fields.get("scanner_rank_priority_flu_rate"))
                    priority_tier = str(
                        fields.get("scanner_rank_priority_tier") or ""
                    ).strip()
                    watch_budget_owner = str(
                        fields.get("scanner_watch_budget_owner") or ""
                    ).strip()
                    market_gainer_partition = _bool(
                        fields.get("scanner_rank_priority_market_gainer_partition")
                    )
                    reserved_partition = str(
                        fields.get("scanner_rank_priority_reserved_partition") or ""
                    ).strip()
                    try:
                        event_date = date.fromisoformat(event_date_text)
                    except ValueError:
                        event_date = None
                    expected_bonus = bonus_points_for_score(score)
                    valid_resource = bool(
                        generation_id.startswith("SCANGEN-")
                        and re.fullmatch(r"\d{6}", code) is not None
                        and event_date is not None
                        and event_date == event_file_date
                        and is_krx_trading_day(event_date)
                        and score is not None
                        and 0.0 <= score <= 1.0
                        and base_priority_score is not None
                        and candidate_priority_score is not None
                        and formula_bonus is not None
                        and abs(formula_bonus - expected_bonus) <= 1e-6
                        and abs(
                            candidate_priority_score
                            - base_priority_score
                            - formula_bonus
                        )
                        <= 1e-6
                        and scan_rank is not None
                        and ranked_count is not None
                        and 1 <= scan_rank <= ranked_count
                        and rank_partition in {0, 1}
                        and source_priority is not None
                        and source_priority >= 0
                        and flu_rate is not None
                        and priority_tier.startswith("tier_")
                        and watch_budget_owner
                        and market_gainer_partition is not None
                        and reserved_partition
                    )
                    if not valid_resource:
                        invalid_resource_pair_count += 1
                    else:
                        resource_key = (event_date_text, generation_id, code)
                        prune_reason = str(
                            fields.get("scanner_prune_reason") or ""
                        ).strip()
                        terminal = (
                            "promoted"
                            if stage == "scalping_scanner_candidate_promoted"
                            else (
                                "capacity_pruned"
                                if prune_reason in RESOURCE_CAPACITY_PRUNE_REASONS
                                else "other_guard_pruned"
                            )
                        )
                        resource_row = {
                            "observation_date": event_date_text,
                            "scan_generation_id": generation_id,
                            "stock_code": code,
                            "scan_rank": scan_rank,
                            "ranked_candidate_count": ranked_count,
                            "rank_partition": rank_partition,
                            "source_priority": source_priority,
                            "flu_rate": flu_rate,
                            "priority_tier": priority_tier,
                            "watch_budget_owner": watch_budget_owner,
                            "market_gainer_partition": market_gainer_partition,
                            "reserved_partition": reserved_partition,
                            "lookup_attention_snapshot_score": score,
                            "base_priority_score": base_priority_score,
                            "candidate_priority_score": candidate_priority_score,
                            "counterfactual_bonus_points": formula_bonus,
                            "terminal": terminal,
                            "prune_reason": prune_reason,
                        }
                        if resource_key not in conflicted_resource_keys:
                            existing_resource = resource_rows.get(resource_key)
                            if (
                                existing_resource is not None
                                and existing_resource != resource_row
                            ):
                                invalid_resource_pair_count += 1
                                resource_rows.pop(resource_key, None)
                                conflicted_resource_keys.add(resource_key)
                            else:
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
                if expectation.get("state") == "invalid":
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
        "invalid_resource_pair_count": invalid_resource_pair_count,
        "resource_pair_row_count": len(resource_rows),
        "_resource_pair_rows": list(resource_rows.values()),
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


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(row["net_return_pct"]) for row in rows]
    total_notional = sum(float(row["buy_notional_krw"]) for row in rows)
    total_pnl = sum(float(row["net_pnl_krw"]) for row in rows)
    return {
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


def _cohort_book(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = [row for row in rows if row["cohort"] == "candidate"]
    control = [row for row in rows if row["cohort"] == "control"]
    candidate_metrics = _metrics(candidate)
    control_metrics = _metrics(control)
    candidate_ev = candidate_metrics["source_quality_adjusted_ev_pct"]
    control_ev = control_metrics["source_quality_adjusted_ev_pct"]
    uplift = (
        round(float(candidate_ev) - float(control_ev), 8)
        if candidate_ev is not None and control_ev is not None
        else None
    )
    return {
        "all": _metrics(rows),
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
    """Compare baseline and proposed ordering inside immutable rank partitions."""

    groups: defaultdict[
        tuple[str, str, int, str, str, bool, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in rows:
        if row.get("terminal") not in {"promoted", "capacity_pruned"}:
            continue
        groups[
            (
                str(row.get("observation_date") or ""),
                str(row.get("scan_generation_id") or ""),
                int(row.get("rank_partition") or 0),
                str(row.get("priority_tier") or ""),
                str(row.get("watch_budget_owner") or ""),
                bool(row.get("market_gainer_partition")),
                str(row.get("reserved_partition") or ""),
            )
        ].append(row)

    paired_generation_keys: set[tuple[str, str]] = set()
    paired_dates: set[str] = set()
    paired_rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    reordered_generation_keys: set[tuple[str, str]] = set()
    moved_in_count = 0
    moved_out_count = 0
    for group_key, group_rows in groups.items():
        promoted_count = sum(row.get("terminal") == "promoted" for row in group_rows)
        pruned_count = sum(
            row.get("terminal") == "capacity_pruned" for row in group_rows
        )
        if promoted_count <= 0 or pruned_count <= 0:
            continue
        (
            observation_date,
            generation_id,
            _partition,
            _tier,
            _owner,
            _market,
            _reserved,
        ) = group_key
        generation_key = (observation_date, generation_id)
        paired_generation_keys.add(generation_key)
        paired_dates.add(observation_date)
        for row in group_rows:
            paired_rows[(observation_date, generation_id, row["stock_code"])] = row
        baseline = sorted(
            group_rows,
            key=lambda row: (
                -float(row["base_priority_score"]),
                int(row["source_priority"]),
                -float(row["flu_rate"]),
                int(row["scan_rank"]),
            ),
        )
        proposed = sorted(
            group_rows,
            key=lambda row: (
                -float(row["candidate_priority_score"]),
                int(row["source_priority"]),
                -float(row["flu_rate"]),
                int(row["scan_rank"]),
            ),
        )
        baseline_top = {row["stock_code"] for row in baseline[:promoted_count]}
        proposed_top = {row["stock_code"] for row in proposed[:promoted_count]}
        moved_in = proposed_top - baseline_top
        moved_out = baseline_top - proposed_top
        if moved_in or moved_out:
            reordered_generation_keys.add(generation_key)
            moved_in_count += len(moved_in)
            moved_out_count += len(moved_out)

    paired_values = list(paired_rows.values())
    candidate_count = sum(
        float(row["lookup_attention_snapshot_score"]) > MIN_SCORE
        for row in paired_values
    )
    control_count = len(paired_values) - candidate_count
    paired_generation_count = len(paired_generation_keys)
    trading_date_count = len(paired_dates)
    floors_pass = bool(
        paired_generation_count >= RESOURCE_PAIR_MIN_GENERATIONS
        and trading_date_count >= RESOURCE_PAIR_MIN_TRADING_DATES
        and candidate_count >= MIN_COHORT_COMPLETED
        and control_count >= MIN_COHORT_COMPLETED
    )
    ready = bool(invalid_row_count == 0 and floors_pass and reordered_generation_keys)
    status = (
        "not_observed"
        if not rows and invalid_row_count == 0
        else (
            "contract_invalid"
            if invalid_row_count > 0
            else (
                "hold_sample"
                if not floors_pass
                else "hold_no_effect" if not reordered_generation_keys else "ready"
            )
        )
    )
    return {
        "metric_role": "causal_runtime_hook_gate",
        "decision_authority": "bounded_same_tier_ordering_gate_only",
        "window_policy": f"rolling_{ROLLING_CALENDAR_DAYS}_calendar_days_clean_post_rollout",
        "sample_floor": (
            f"paired_generation_count>={RESOURCE_PAIR_MIN_GENERATIONS}_and_"
            f"trading_date_count>={RESOURCE_PAIR_MIN_TRADING_DATES}_and_"
            f"candidate_and_control_each>={MIN_COHORT_COMPLETED}"
        ),
        "primary_decision_metric": "counterfactual_top_set_reorder_count",
        "source_quality_gate": (
            "exact_generation_code_rank_partition_tier_and_formula_scores"
        ),
        "forbidden_uses": FORBIDDEN_USES,
        "status": status,
        "ready_for_live_gate": ready,
        "invalid_row_count": invalid_row_count,
        "paired_generation_count": paired_generation_count,
        "trading_date_count": trading_date_count,
        "paired_candidate_observation_count": candidate_count,
        "paired_control_observation_count": control_count,
        "reordered_generation_count": len(reordered_generation_keys),
        "counterfactual_moved_in_count": moved_in_count,
        "counterfactual_moved_out_count": moved_out_count,
        "unpaired_or_guard_pruned_row_count": max(0, len(rows) - len(paired_values)),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


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
    if uplift is None or uplift < MIN_EV_UPLIFT_PCT:
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


def _base_rows_for_prior(
    outcomes: list[dict[str, Any]], prior_policy: dict[str, Any]
) -> list[dict[str, Any]]:
    if prior_policy.get("status") not in {
        "forward_holdout_armed",
        "live_auto_apply_ready",
    }:
        return list(outcomes)
    try:
        holdout_since = date.fromisoformat(
            str(prior_policy.get("holdout_armed_since") or "")
        )
    except ValueError:
        return []
    return [
        row
        for row in outcomes
        if date.fromisoformat(str(row.get("rec_date") or "")) <= holdout_since
    ]


def _latest_prior_policy(target: date) -> dict[str, Any]:
    candidates: list[tuple[date, Path]] = []
    for path in POLICY_DIR.glob("scanner_lookup_attention_policy_*.json"):
        try:
            source_date = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
        except ValueError:
            continue
        if source_date < target and is_krx_trading_day(source_date):
            candidates.append((source_date, path))
    if not candidates:
        return {}
    expected_next_date = target
    blocked_bridge_dates: list[str] = []
    blocked_bridge_holdout = ""
    for source_date, path in sorted(candidates, key=lambda item: item[0], reverse=True):
        if count_krx_trading_days(source_date, expected_next_date) != 1:
            return {}
        payload = _load_json(path)
        report = _load_json(
            REPORT_DIR
            / f"scanner_lookup_attention_tuning_{source_date.isoformat()}.json"
        )
        if validate_artifact_pair(report, payload, target=source_date):
            return {}
        holdout_text = str(payload.get("holdout_armed_since") or "")
        try:
            holdout_date = date.fromisoformat(holdout_text)
        except ValueError:
            return {}
        if not (
            is_krx_trading_day(source_date)
            and is_krx_trading_day(holdout_date)
            and holdout_date <= source_date
        ):
            return {}
        status = str(payload.get("status") or "")
        if status in {"forward_holdout_armed", "live_auto_apply_ready"}:
            if blocked_bridge_holdout and blocked_bridge_holdout != holdout_text:
                return {}
            return {
                **payload,
                "campaign_continuity_bridge_dates": list(
                    reversed(blocked_bridge_dates)
                ),
            }
        if status != "source_quality_blocked":
            return {}
        if blocked_bridge_holdout and blocked_bridge_holdout != holdout_text:
            return {}
        blocked_bridge_holdout = holdout_text
        blocked_bridge_dates.append(source_date.isoformat())
        expected_next_date = source_date
    return {}


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
    live_predecessor = prior_policy.get("status") == "live_auto_apply_ready"
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
        {date.fromisoformat(str(row["rec_date"])) for row in outcomes},
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
        "holdout_armed_since": decision["holdout_armed_since"],
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
        "rollback": {
            "trigger": "missing_invalid_stale_policy_or_any_source_evidence_guard_failure",
            "bonus_points": 0.0,
            "effect": "legacy_same_tier_sort_score_restored",
        },
    }
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
    issues: list[str] = []
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
    if report_decision_contract or policy_decision_contract:
        if report_decision_contract != DECISION_CONTRACT_VERSION:
            issues.append("report_decision_contract_version_invalid")
        if policy_decision_contract != DECISION_CONTRACT_VERSION:
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
        "activation_mode": ACTIVATION_MODE,
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
        resource_integer_keys = (
            "paired_generation_count",
            "trading_date_count",
            "paired_candidate_observation_count",
            "paired_control_observation_count",
            "reordered_generation_count",
            "counterfactual_moved_in_count",
            "counterfactual_moved_out_count",
            "unpaired_or_guard_pruned_row_count",
            "invalid_row_count",
        )
        resource_counts_valid = not any(
            not isinstance(resource_pair.get(key), int)
            or isinstance(resource_pair.get(key), bool)
            or int(resource_pair.get(key)) < 0
            for key in resource_integer_keys
        )
        if not resource_counts_valid:
            issues.append("resource_allocation_pair_count_contract_invalid")
        resource_counts = {
            key: int(resource_pair[key]) if resource_counts_valid else 0
            for key in resource_integer_keys
        }
        if resource_pair.get("counterfactual_moved_in_count") != resource_pair.get(
            "counterfactual_moved_out_count"
        ):
            issues.append("resource_allocation_pair_movement_unbalanced")
        if lineage_counts_valid and (
            resource_pair.get("invalid_row_count")
            != lineage.get("invalid_resource_pair_count")
        ):
            issues.append("resource_allocation_pair_invalid_count_mismatch")
        resource_total_rows = sum(
            resource_counts[key]
            for key in (
                "paired_candidate_observation_count",
                "paired_control_observation_count",
                "unpaired_or_guard_pruned_row_count",
            )
        )
        if lineage_counts_valid and (
            resource_total_rows != lineage.get("resource_pair_row_count")
        ):
            issues.append("resource_allocation_pair_row_count_mismatch")
        resource_ready = bool(
            resource_counts["paired_generation_count"] >= RESOURCE_PAIR_MIN_GENERATIONS
            and resource_counts["trading_date_count"] >= RESOURCE_PAIR_MIN_TRADING_DATES
            and resource_counts["paired_candidate_observation_count"]
            >= MIN_COHORT_COMPLETED
            and resource_counts["paired_control_observation_count"]
            >= MIN_COHORT_COMPLETED
            and resource_counts["reordered_generation_count"] > 0
            and resource_counts["invalid_row_count"] == 0
        )
        if not isinstance(resource_pair.get("ready_for_live_gate"), bool):
            issues.append("resource_allocation_pair_ready_type_invalid")
        elif resource_pair.get("ready_for_live_gate") != resource_ready:
            issues.append("resource_allocation_pair_ready_state_invalid")
        expected_resource_status = (
            "contract_invalid"
            if resource_counts["invalid_row_count"] > 0
            else (
                "not_observed"
                if resource_total_rows == 0
                else (
                    "hold_sample"
                    if not (
                        resource_counts["paired_generation_count"]
                        >= RESOURCE_PAIR_MIN_GENERATIONS
                        and resource_counts["trading_date_count"]
                        >= RESOURCE_PAIR_MIN_TRADING_DATES
                        and resource_counts["paired_candidate_observation_count"]
                        >= MIN_COHORT_COMPLETED
                        and resource_counts["paired_control_observation_count"]
                        >= MIN_COHORT_COMPLETED
                    )
                    else (
                        "hold_no_effect"
                        if resource_counts["reordered_generation_count"] == 0
                        else "ready"
                    )
                )
            )
        )
        if resource_pair.get("status") != expected_resource_status:
            issues.append("resource_allocation_pair_status_invalid")
        if expected_allowed and not resource_ready:
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
            f"- candidate/control observations: `{candidate_funnel.get('valid_observation_count', 0)}/{control_funnel.get('valid_observation_count', 0)}`",
            f"- candidate/control full-fill: `{candidate_funnel.get('full_fill_observation_count', 0)}/{control_funnel.get('full_fill_observation_count', 0)}`",
            f"- resource allocation pair: `{resource_pair.get('status', 'not_observed')}` generations=`{resource_pair.get('paired_generation_count', 0)}` dates=`{resource_pair.get('trading_date_count', 0)}` reordered=`{resource_pair.get('reordered_generation_count', 0)}`",
            f"- forward holdout completed/dates: `{holdout['all']['completed_outcome_count']}/{holdout['all']['trading_date_count']}`",
            f"- post-apply status: `{post_apply['status']}`",
            f"- post-apply completed/dates: `{post_apply['book']['all']['completed_outcome_count']}/{post_apply['book']['all']['trading_date_count']}`",
            f"- post-apply rollback: `{post_apply['rollback_triggered']}`",
            f"- source quality/master: `{report['source_quality']['status']}` / `{report['official_symbol_master']['status']}`",
            f"- runtime handoff allowed: `{report['allowed_runtime_apply']}`",
            "- scope: same-priority-tier bounded score only; rollback bonus is 0.",
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
        if args.write:
            write_artifacts(report, policy)
    issues = validate_artifact_pair(report, policy, target=target)
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
