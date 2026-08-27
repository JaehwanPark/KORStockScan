"""Exact-date entry-confirmation timing policy shared by machine owners.

The policy changes only when an otherwise valid owner entry signal may be
consumed.  It has no authority over signal creation, prices, quantities,
targets, exits, broker guards, or owner custody.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping

from src.utils.constants import DATA_DIR, PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

SCHEMA = "machine_entry_timing_policy_applied_v1"
AUTHORITY = "explicit_user_directed_machine_entry_timing_tuning_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
ALLOWED_DELAYS_SEC = frozenset({0, 1, 3, 5})
MIN_OBSERVED_DAYS = 5
MIN_UNIQUE_LIFECYCLES = 20
MIN_COMPLETED_OUTCOMES = 20
MIN_BBO_COMPLETE_RATE_PCT = 95.0
MIN_DEPTH_COVERAGE_PCT = 90.0
MIN_PAIRED_COMPLETED_COVERAGE_PCT = 95.0
MIN_DELAYED_ENTRY_FEASIBILITY_RATE_PCT = 90.0
MIN_ABSOLUTE_EV_UPLIFT_PCT = 0.005
MAX_P10_DETERIORATION_PCT = 0.01
MAX_RIGHT_CENSORED_RATE_PCT = 20.0
# Lower-price episode services poll every 6 seconds in the live launcher. Keep
# enough bounded slack for one normal poll plus scheduler jitter while still
# discarding confirmations recovered after a process pause or restart.
ENTRY_CONFIRMATION_MAX_LATE_SEC = 10
REQUIRED_ROLLING_WINDOWS_DAYS = (5, 10, 20)
DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "machine_entry_timing_policy"
FILE_PREFIX = "machine_entry_timing_policy"
SOURCE_REPORT_SCHEMA = "machine_entry_timing_tuning_report_v1"
DEFAULT_SOURCE_REPORT_DIR = DATA_DIR / "report" / "machine_entry_timing_tuning"
SOURCE_REPORT_PREFIX = "machine_entry_timing_tuning"


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def scope_key(
    *,
    owner: str,
    scope_id: str,
    symbol: str,
    session: str,
    entry_state: str = "*",
) -> str:
    return "|".join((owner, scope_id, symbol, session, entry_state or "*"))


def policy_hash(scopes: Mapping[str, Any]) -> str:
    return canonical_sha256(scopes)


def policy_path(target_date: date, *, policy_dir: Path = DEFAULT_POLICY_DIR) -> Path:
    return policy_dir / f"{FILE_PREFIX}_{target_date.isoformat()}.json"


def source_report_path(
    source_date: date, *, source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR
) -> Path:
    return source_report_dir / f"{SOURCE_REPORT_PREFIX}_{source_date.isoformat()}.json"


def _next_krx_trading_day(source_date: date) -> date:
    candidate = source_date + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _evidence_integer(evidence: Mapping[str, Any], field: str) -> int:
    value = evidence.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(field)
    return value


def validate_applied_policy(payload: Any, *, target_date: date) -> tuple[bool, str]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return False, "entry_timing_policy_schema_invalid"
    if payload.get("target_date") != target_date.isoformat():
        return False, "entry_timing_policy_target_date_mismatch"
    if not is_krx_trading_day(target_date):
        return False, "entry_timing_policy_target_date_not_trading_day"
    try:
        source_date = date.fromisoformat(str(payload.get("source_date") or ""))
    except ValueError:
        return False, "entry_timing_policy_source_date_invalid"
    if (
        source_date < CLEAN_BASELINE_DATE
        or source_date >= target_date
        or not is_krx_trading_day(source_date)
        or target_date != _next_krx_trading_day(source_date)
    ):
        return False, "entry_timing_policy_source_date_contract_invalid"
    if (
        payload.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE.isoformat()
        or payload.get("decision_authority") != AUTHORITY
        or not isinstance(payload.get("source_report"), str)
        or not str(payload.get("source_report") or "").strip()
        or not isinstance(payload.get("source_report_canonical_sha256"), str)
        or len(str(payload.get("source_report_canonical_sha256"))) != 64
        or any(
            char not in "0123456789abcdef"
            for char in str(payload.get("source_report_canonical_sha256") or "")
        )
        or payload.get("runtime_effect") is not True
        or payload.get("allowed_runtime_apply") is not True
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not False
    ):
        return False, "entry_timing_policy_authority_invalid"
    scopes = payload.get("scopes")
    if not isinstance(scopes, dict):
        return False, "entry_timing_policy_scopes_invalid"
    if payload.get("policy_hash") != policy_hash(scopes):
        return False, "entry_timing_policy_hash_mismatch"
    selected_count = 0
    for key, row in scopes.items():
        if not isinstance(key, str) or not isinstance(row, dict):
            return False, "entry_timing_policy_scope_row_invalid"
        owner = str(row.get("owner") or "")
        scope_id = str(row.get("scope_id") or "")
        symbol = str(row.get("symbol") or "")
        session = str(row.get("session") or "")
        entry_state = str(row.get("entry_state") or "*")
        delay = row.get("entry_confirmation_delay_sec")
        if (
            owner not in {"widget", "episode"}
            or not scope_id
            or len(symbol) != 6
            or not symbol.isdigit()
            or not session
            or isinstance(delay, bool)
            or not isinstance(delay, int)
            or delay not in ALLOWED_DELAYS_SEC
            or delay == 0
            or key
            != scope_key(
                owner=owner,
                scope_id=scope_id,
                symbol=symbol,
                session=session,
                entry_state=entry_state,
            )
            or row.get("axis") != "entry_confirmation_delay_sec"
            or row.get("quantity_effect") is not False
            or row.get("price_effect") is not False
            or row.get("target_effect") is not False
            or row.get("exit_effect") is not False
        ):
            return False, "entry_timing_policy_scope_contract_invalid"
        if delay > 0:
            selected_count += 1
            evidence = row.get("evidence")
            try:
                evidence_ev = float(
                    evidence.get("source_quality_adjusted_ev_pct")
                    if isinstance(evidence, dict)
                    else "nan"
                )
                bbo_rate = float(
                    evidence.get("bbo_complete_rate_pct")
                    if isinstance(evidence, dict)
                    else 0
                )
                depth_rate = float(
                    evidence.get("depth_coverage_pct")
                    if isinstance(evidence, dict)
                    else 0
                )
                paired_completed_coverage_rate = float(
                    evidence.get("paired_completed_coverage_rate_pct")
                    if isinstance(evidence, dict)
                    else 0
                )
                uplift = float(
                    evidence.get("absolute_ev_uplift_pct")
                    if isinstance(evidence, dict)
                    else "nan"
                )
                baseline_p10 = float(
                    evidence.get("baseline_p10_pct")
                    if isinstance(evidence, dict)
                    else "nan"
                )
                candidate_p10 = float(
                    evidence.get("candidate_p10_pct")
                    if isinstance(evidence, dict)
                    else "nan"
                )
                right_censored_rate = float(
                    evidence.get("right_censored_rate_pct")
                    if isinstance(evidence, dict)
                    else 100
                )
                feasibility_rate = float(
                    evidence.get("delayed_entry_feasibility_rate_pct")
                    if isinstance(evidence, dict)
                    else 0
                )
                if not isinstance(evidence, dict):
                    raise ValueError("evidence")
                observed_trading_days = _evidence_integer(
                    evidence, "observed_trading_days"
                )
                unique_decision_lifecycles = _evidence_integer(
                    evidence, "unique_decision_lifecycles"
                )
                completed_outcome_count = _evidence_integer(
                    evidence, "completed_outcome_count"
                )
                latest_completed_observation_date = date.fromisoformat(
                    str(evidence.get("latest_completed_observation_date") or "")
                    if isinstance(evidence, dict)
                    else ""
                )
            except (TypeError, ValueError):
                return False, "entry_timing_policy_evidence_floor_invalid"
            rolling = (
                evidence.get("rolling_windows") if isinstance(evidence, dict) else None
            )
            rolling_ready = bool(
                isinstance(rolling, dict)
                and all(
                    isinstance(rolling.get(str(window)), dict)
                    and rolling[str(window)].get("complete") is True
                    and rolling[str(window)].get("positive_and_improved") is True
                    for window in REQUIRED_ROLLING_WINDOWS_DAYS
                )
            )
            if (
                not isinstance(evidence, dict)
                or evidence.get("ready") is not True
                or evidence.get("entry_confirmation_delay_sec") != delay
                or observed_trading_days < MIN_OBSERVED_DAYS
                or unique_decision_lifecycles < MIN_UNIQUE_LIFECYCLES
                or completed_outcome_count < MIN_COMPLETED_OUTCOMES
                or latest_completed_observation_date != source_date
                or evidence.get("target_date_in_completed_observations") is not True
                or not math.isfinite(evidence_ev)
                or evidence_ev <= 0
                or not math.isfinite(bbo_rate)
                or bbo_rate > 100
                or bbo_rate < MIN_BBO_COMPLETE_RATE_PCT
                or not math.isfinite(depth_rate)
                or depth_rate > 100
                or depth_rate < MIN_DEPTH_COVERAGE_PCT
                or not math.isfinite(paired_completed_coverage_rate)
                or paired_completed_coverage_rate > 100
                or paired_completed_coverage_rate < MIN_PAIRED_COMPLETED_COVERAGE_PCT
                or not math.isfinite(feasibility_rate)
                or feasibility_rate > 100
                or feasibility_rate < MIN_DELAYED_ENTRY_FEASIBILITY_RATE_PCT
                or not math.isfinite(uplift)
                or uplift < MIN_ABSOLUTE_EV_UPLIFT_PCT
                or not math.isfinite(baseline_p10)
                or not math.isfinite(candidate_p10)
                or candidate_p10 < baseline_p10 - MAX_P10_DETERIORATION_PCT
                or not math.isfinite(right_censored_rate)
                or right_censored_rate < 0
                or right_censored_rate > MAX_RIGHT_CENSORED_RATE_PCT
                or not rolling_ready
            ):
                return False, "entry_timing_policy_evidence_floor_invalid"
    if selected_count > 1:
        return False, "entry_timing_policy_same_stage_multi_scope_forbidden"
    expected_selection_status = (
        "select_one_next_session_entry_confirmation_delay"
        if selected_count == 1
        else "baseline_immediate_entry_carry_forward"
    )
    if payload.get("selection_status") != expected_selection_status:
        return False, "entry_timing_policy_selection_status_invalid"
    return True, "ready"


def load_applied_policy(
    *,
    target_date: date,
    policy_dir: Path = DEFAULT_POLICY_DIR,
    source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR,
) -> tuple[dict[str, Any] | None, str]:
    path = policy_path(target_date, policy_dir=policy_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"entry_timing_policy_unreadable:{type(exc).__name__}"
    valid, reason = validate_applied_policy(payload, target_date=target_date)
    if not valid:
        return None, reason
    source_date = date.fromisoformat(str(payload["source_date"]))
    source_report = Path(str(payload.get("source_report") or ""))
    if not source_report.is_absolute():
        source_report = PROJECT_ROOT / source_report
    expected_source_report = source_report_path(
        source_date, source_report_dir=source_report_dir
    )
    if source_report.resolve() != expected_source_report.resolve():
        return None, "entry_timing_source_report_path_invalid"
    try:
        source_payload = json.loads(source_report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"entry_timing_source_report_unreadable:{type(exc).__name__}"
    if (
        not isinstance(source_payload, dict)
        or source_payload.get("schema") != SOURCE_REPORT_SCHEMA
        or source_payload.get("target_date") != payload.get("source_date")
        or source_payload.get("effective_date") != payload.get("target_date")
        or payload.get("source_report_canonical_sha256")
        != canonical_sha256(source_payload)
    ):
        return None, "entry_timing_source_report_contract_invalid"
    winner = source_payload.get("winner")
    same_stage_guard = source_payload.get("same_stage_owner_guard")
    expected_decision = (
        "select_one_next_session_entry_confirmation_delay"
        if isinstance(winner, dict)
        else "baseline_immediate_entry_carry_forward"
    )
    if (
        source_payload.get("clean_tuning_baseline_date")
        != CLEAN_BASELINE_DATE.isoformat()
        or source_payload.get("target_source_ready") is not True
        or source_payload.get("runtime_effect") is not False
        or source_payload.get("actual_order_submitted") is not False
        or source_payload.get("broker_order_forbidden") is not True
        or source_payload.get("decision") != expected_decision
        or payload.get("selection_status") != expected_decision
        or (
            isinstance(winner, dict)
            and (
                not isinstance(same_stage_guard, dict)
                or same_stage_guard.get("mutation_present") is not False
            )
        )
    ):
        return None, "entry_timing_source_report_authority_invalid"
    expected_scopes: dict[str, Any] = {}
    if isinstance(winner, dict) and isinstance(winner.get("selected"), dict):
        expected_key = scope_key(
            owner=str(winner.get("owner") or ""),
            scope_id=str(winner.get("scope_id") or ""),
            symbol=str(winner.get("symbol") or ""),
            session=str(winner.get("session") or ""),
            entry_state=str(winner.get("entry_state") or "*"),
        )
        expected_scopes[expected_key] = winner["selected"]
    if set(payload["scopes"]) != set(expected_scopes) or any(
        (payload["scopes"][key].get("evidence") != evidence)
        or (
            payload["scopes"][key].get("entry_confirmation_delay_sec")
            != evidence.get("entry_confirmation_delay_sec")
        )
        for key, evidence in expected_scopes.items()
    ):
        return None, "entry_timing_source_report_selection_mismatch"
    return payload, reason


def resolve_entry_confirmation_delay(
    *,
    target_date: date,
    owner: str,
    scope_id: str,
    symbol: str,
    session: str,
    entry_state: str = "*",
    policy_dir: Path = DEFAULT_POLICY_DIR,
    source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR,
) -> tuple[int, dict[str, Any]]:
    payload, reason = load_applied_policy(
        target_date=target_date,
        policy_dir=policy_dir,
        source_report_dir=source_report_dir,
    )
    provenance = {
        "status": reason,
        "policy_path": str(policy_path(target_date, policy_dir=policy_dir)),
        "policy_hash": payload.get("policy_hash") if payload else None,
        "target_date": target_date.isoformat(),
        "source_date": payload.get("source_date") if payload else None,
        "axis": "entry_confirmation_delay_sec",
    }
    if payload is None:
        return 0, provenance
    keys = (
        scope_key(
            owner=owner,
            scope_id=scope_id,
            symbol=symbol,
            session=session,
            entry_state=entry_state,
        ),
        scope_key(
            owner=owner,
            scope_id=scope_id,
            symbol=symbol,
            session=session,
            entry_state="*",
        ),
    )
    for key in keys:
        row = payload["scopes"].get(key)
        if isinstance(row, dict):
            return int(row["entry_confirmation_delay_sec"]), {
                **provenance,
                "status": "applied",
                "scope_key": key,
                "evidence": row.get("evidence"),
            }
    return 0, {**provenance, "status": "scope_not_selected_baseline_immediate"}
