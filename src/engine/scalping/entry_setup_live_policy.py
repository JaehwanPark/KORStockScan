"""Bridge a verified V2.14 replay result into a next-day KRX canary.

The postclose producer emits a bounded-live candidate.  PREOPEN validates the
candidate and its immutable source reports, then writes a date-scoped
activation artifact.  The live AI engine consumes only that activation and
falls back to the configured V2.13 owner on every contract gap.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import tempfile
import threading
from datetime import date, datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
)
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_DECISION_COMPOSER_VERSION,
    ENTRY_SETUP_EVIDENCE_VERSION,
    STRUCTURE_PHASE_POLICY_VERSION,
)
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
LIVE_CANDIDATE_SCHEMA = "entry_setup_v2_14_bounded_live_candidate_v2"
PREOPEN_ACTIVATION_SCHEMA = "entry_setup_v2_14_preopen_activation_v2"
BATCH_SCHEMA = "ai_entry_setup_paired_replay_batch_v1"
DETAILED_REPORT_SCHEMA = "ai_prompt_detailed_paired_replay_v1"
LIVE_CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"
ACTIVATION_DIR = DATA_DIR / "runtime" / "entry_setup_v2_14_live_policy"
DETAILED_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_detailed_paired_replay"
BATCH_REPORT_DIR = DATA_DIR / "report" / "ai_entry_setup_paired_replay_batch"
CANARY_ENV_KEY = "KORSTOCKSCAN_ENTRY_SETUP_V2_14_KRX_CANARY_ENABLED"
CANARY_VENUE = "KRX"
CANARY_SESSION = "KRX_REGULAR"
CANARY_POSITION_TAGS = ("SCANNER",)
CLEAN_TUNING_BASELINE_DATE = "2026-06-05"
PERFORMANCE_CANARY_MODE = "performance_bounded"
EXPLORATION_CANARY_MODE = "one_share_exploration"
EXPECTED_CANDIDATE_SELECTION_POLICY = (
    "deterministic_outcome_blind_setup_state_symbol_round_robin_v3"
)
EXPLORATION_MAX_DAILY_PROBES = 3
PREOPEN_CANDIDATE_CUTOFF_KST = dt_time(7, 35)
EFFECTIVE_DATE_POLICY = "first_available_krx_preopen_v1"
PERFORMANCE_PROMOTION_ERROR_CODES = frozenset(
    {
        "krx_batch_promotion_gate_not_passed",
        "detailed_promotion_quality_not_passed",
        "cumulative_promotion_gate_not_passed",
        "cumulative_promotion_checks_incomplete",
        "cumulative_exposure_floor_not_passed",
        "cumulative_exposure_counts_below_floor",
        "cumulative_probe_risk_budget_not_passed",
    }
)
CUMULATIVE_PROMOTION_CHECK_KEYS = (
    "cohort_isolated",
    "candidate_exposure_sample_floor_pass",
    "candidate_primary_decision_ev_positive",
    "candidate_primary_decision_ev_improved",
    "candidate_exposure_probe_cost_adjusted_ev_positive",
    "candidate_probe_bounded_risk_budget_pass",
    "opportunity_capture_expanded",
    "missed_upside_tradeoff_not_worse",
    "drawdown_recovery_capture_not_decreased",
)

_CACHE_LOCK = threading.Lock()
_ACTIVATION_CACHE: dict[str, Any] = {}
_EXPLORATION_CAP_LOCK = threading.Lock()
EXPLORATION_CAP_LEDGER_SCHEMA = "entry_setup_exploration_probe_cap_v1"


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_sha256(path: Path) -> str | None:
    try:
        return _file_sha256(path) if path.is_file() else None
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
        Path(temporary_name).replace(path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def _env_value(name: str, env: dict[str, str] | None = None) -> str | None:
    if env is None:
        return os.getenv(name)
    return env.get(name)


def _enabled_by_operator(env: dict[str, str] | None = None) -> bool:
    raw = _env_value(CANARY_ENV_KEY, env)
    if raw is None and env is not None:
        # The kill switch may be supplied by the cron/supervisor environment,
        # while all positive runtime-contract keys must come from the explicit
        # launcher env-file merge.
        raw = os.getenv(CANARY_ENV_KEY)
    if raw is None or not raw.strip():
        return True
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_bool(name: str, default: bool, env: dict[str, str] | None = None) -> bool:
    raw = _env_value(name, env)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _runtime_probe_contract_errors(
    *, target_date: str, env: dict[str, str] | None = None
) -> list[str]:
    """Verify that V2.14 can only reach the existing one-share owner."""

    errors: list[str] = []
    required_true = (
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED",
    )
    for key in required_true:
        if not _env_bool(key, False, env):
            errors.append(f"runtime_contract_disabled:{key}")
    if not _env_bool("KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED", False, env):
        errors.append("runtime_contract_threshold_auto_apply_disabled")
    runtime_apply_date = str(
        _env_value("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", env) or ""
    ).strip()
    if runtime_apply_date != target_date:
        errors.append("runtime_contract_target_date_mismatch")
    configured_prompt = str(
        _env_value("KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION", env) or ""
    ).strip()
    if configured_prompt != DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION:
        errors.append("runtime_contract_configured_v2_13_owner_missing")
    if _env_bool(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
        True,
        env,
    ):
        errors.append("runtime_contract_wait_probe_handoff_disabled")
    active_date = str(
        _env_value("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", env) or ""
    ).strip()
    if active_date.upper() not in {"DAILY", target_date}:
        errors.append("runtime_contract_probe_first_date_inactive")
    try:
        probe_qty = int(
            str(_env_value("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", env) or "0").strip()
        )
    except ValueError:
        probe_qty = 0
    if probe_qty != 1:
        errors.append("runtime_contract_probe_qty_not_one")
    return errors


def _read_shell_export_env(path: Path) -> tuple[dict[str, str], list[str]]:
    """Read generated/operator env files without executing shell content."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}, [f"runtime_env_file_unreadable:{path}"]
    values: dict[str, str] = {}
    errors: list[str] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, _, raw_value = line.partition("=")
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            errors.append(f"runtime_env_key_invalid:{path}:{line_number}")
            continue
        try:
            parts = shlex.split(raw_value.strip(), comments=False, posix=True)
        except ValueError:
            errors.append(f"runtime_env_value_invalid:{path}:{line_number}:{key}")
            continue
        if len(parts) > 1:
            errors.append(f"runtime_env_value_ambiguous:{path}:{line_number}:{key}")
            continue
        values[key] = parts[0] if parts else ""
    return values, errors


def load_preopen_runtime_env(
    *,
    runtime_env_file: Path,
    operator_env_file: Path,
    dated_operator_env_file: Path | None = None,
) -> tuple[dict[str, str], dict[str, Any], list[str]]:
    """Reproduce the bot launcher's threshold -> operator -> dated env order."""

    merged: dict[str, str] = {}
    errors: list[str] = []
    sources: list[dict[str, Any]] = []
    for path, required, role in (
        (runtime_env_file, True, "threshold_runtime_env"),
        (operator_env_file, True, "operator_runtime_overrides"),
        (dated_operator_env_file, False, "dated_operator_runtime_overrides"),
    ):
        if path is None:
            continue
        if not path.is_file():
            if required:
                errors.append(f"runtime_env_required_file_missing:{path}")
            sources.append(
                {"role": role, "path": str(path), "exists": False, "sha256": None}
            )
            continue
        values, parse_errors = _read_shell_export_env(path)
        merged.update(values)
        errors.extend(parse_errors)
        sources.append(
            {
                "role": role,
                "path": str(path),
                "exists": True,
                "sha256": _safe_file_sha256(path),
                "parsed_key_count": len(values),
            }
        )
    provenance = {
        "load_order": [row["role"] for row in sources],
        "sources": sources,
        "effective_contract_sha256": _canonical_sha256(
            {
                key: merged.get(key)
                for key in sorted(
                    {
                        CANARY_ENV_KEY,
                        "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED",
                        "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE",
                        "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION",
                        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED",
                        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT",
                        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
                        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
                        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED",
                        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE",
                        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY",
                        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED",
                    }
                )
            }
        ),
    }
    return merged, provenance, list(dict.fromkeys(errors))


def _normalize_venue(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_session(value: Any) -> str:
    return str(value or "").strip().upper()


def _next_krx_trading_date(source_date: str) -> str:
    current = date.fromisoformat(source_date) + timedelta(days=1)
    for _ in range(14):
        if is_krx_trading_day(current):
            return current.isoformat()
        current += timedelta(days=1)
    raise RuntimeError(f"next_krx_trading_date_unresolved:{source_date}")


def _candidate_effective_date(
    *, source_date: str, generated_at: datetime | str
) -> str:
    source = date.fromisoformat(source_date)
    if isinstance(generated_at, str):
        current = datetime.fromisoformat(generated_at)
    elif isinstance(generated_at, datetime):
        current = generated_at
    else:
        raise TypeError("candidate_generated_at_invalid")
    current = (
        current.replace(tzinfo=KST)
        if current.tzinfo is None
        else current.astimezone(KST)
    )
    if current.date() < source:
        raise ValueError("candidate_generated_before_source_date")

    nominal = date.fromisoformat(_next_krx_trading_date(source_date))
    if current.date() < nominal:
        return nominal.isoformat()
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) < PREOPEN_CANDIDATE_CUTOFF_KST
    ):
        return current.date().isoformat()
    return _next_krx_trading_date(current.date().isoformat())


def live_candidate_path(source_date: str) -> Path:
    return (
        LIVE_CANDIDATE_DIR
        / f"entry_setup_v2_14_bounded_live_candidate_{source_date}.json"
    )


def activation_path(target_date: str) -> Path:
    return ACTIVATION_DIR / f"entry_setup_v2_14_live_policy_{target_date}.json"


def exploration_probe_cap_path(trade_date: str) -> Path:
    return ACTIVATION_DIR / f"entry_setup_exploration_probe_cap_{trade_date}.json"


def exploration_probe_cap_failure_path(trade_date: str) -> Path:
    return ACTIVATION_DIR / (
        f"entry_setup_exploration_probe_cap_{trade_date}.failed.json"
    )


def read_exploration_probe_submit_count(trade_date: str) -> int | None:
    """Return the durable daily accepted-probe count, or None on corruption."""

    path = exploration_probe_cap_path(trade_date)
    if exploration_probe_cap_failure_path(trade_date).exists():
        return None
    if not path.exists():
        return 0
    payload = _read_json(path)
    signatures = payload.get("accepted_probe_signatures")
    if (
        payload.get("schema") != EXPLORATION_CAP_LEDGER_SCHEMA
        or payload.get("trade_date") != trade_date
        or not isinstance(signatures, list)
        or any(not isinstance(value, str) or not value for value in signatures)
        or len(set(signatures)) != len(signatures)
        or payload.get("accepted_probe_count") != len(signatures)
    ):
        return None
    return len(signatures)


def mark_exploration_probe_cap_fail_closed(*, trade_date: str, reason: str) -> None:
    """Persist a same-day fail-closed marker after a ledger write failure."""

    _atomic_write_json(
        exploration_probe_cap_failure_path(trade_date),
        {
            "schema": "entry_setup_exploration_probe_cap_failure_v1",
            "trade_date": trade_date,
            "recorded_at": datetime.now(KST).isoformat(),
            "reason": str(reason or "ledger_write_failed")[:240],
            "decision_authority": "daily_one_share_exploration_submit_cap",
            "runtime_effect": True,
            "fail_closed": True,
        },
    )


def record_exploration_probe_submission(
    *, trade_date: str, stock_code: str, broker_order_no: str
) -> int:
    """Durably deduplicate a broker-accepted one-share exploration probe."""

    normalized_code = str(stock_code or "").strip()[:6]
    normalized_order_no = str(broker_order_no or "").strip()
    if not normalized_code or not normalized_order_no:
        raise ValueError("exploration_probe_identity_missing")
    signature = hashlib.sha256(
        f"{trade_date}:{normalized_code}:{normalized_order_no}".encode("utf-8")
    ).hexdigest()
    with _EXPLORATION_CAP_LOCK:
        path = exploration_probe_cap_path(trade_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = path.with_suffix(f"{path.suffix}.lock")
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            current_count = read_exploration_probe_submit_count(trade_date)
            if current_count is None:
                raise ValueError("exploration_probe_cap_ledger_invalid")
            payload = _read_json(path) if path.exists() else {}
            signatures = list(payload.get("accepted_probe_signatures") or [])
            if signature not in signatures:
                signatures.append(signature)
            _atomic_write_json(
                path,
                {
                    "schema": EXPLORATION_CAP_LEDGER_SCHEMA,
                    "trade_date": trade_date,
                    "updated_at": datetime.now(KST).isoformat(),
                    "accepted_probe_count": len(signatures),
                    "accepted_probe_signatures": signatures,
                    "identity_contract": (
                        "sha256(trade_date:stock_code:broker_order_no)"
                    ),
                    "decision_authority": "daily_one_share_exploration_submit_cap",
                    "runtime_effect": True,
                    "actual_order_submitted": True,
                    "forbidden_uses": [
                        "order_submission",
                        "quantity_or_cap_increase",
                        "broker_or_safety_guard_bypass",
                    ],
                },
            )
            return len(signatures)


def detailed_report_path(source_date: str) -> Path:
    return DETAILED_REPORT_DIR / (
        "ai_prompt_detailed_paired_replay_"
        f"{source_date}_{DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION}"
        "_venue_krx_session_krx_regular.json"
    )


def batch_report_path(source_date: str) -> Path:
    return BATCH_REPORT_DIR / f"ai_entry_setup_paired_replay_batch_{source_date}.json"


def _batch_evidence(batch_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": batch_report.get("schema"),
        "target_date": batch_report.get("target_date"),
        "status": batch_report.get("status"),
        "candidate_prompt_version": batch_report.get("candidate_prompt_version"),
        "cohorts": batch_report.get("cohorts"),
        "runtime_effect": batch_report.get("runtime_effect"),
        "allowed_runtime_apply": batch_report.get("allowed_runtime_apply"),
        "actual_order_submitted": batch_report.get("actual_order_submitted"),
        "broker_order_forbidden": batch_report.get("broker_order_forbidden"),
    }


def _selection_checkpoint_contract_pass(
    selection: dict[str, Any], *, evaluated_request_count: int
) -> bool:
    counts = selection.get("checkpoint_evaluated_setup_state_counts")
    if not isinstance(counts, dict) or not counts:
        return False
    if set(counts) - {"READY", "WAIT_CONFIRMATION", "OTHER"}:
        return False
    try:
        normalized = [int(value) for value in counts.values()]
    except (TypeError, ValueError):
        return False
    return bool(
        all(value >= 0 for value in normalized)
        and sum(normalized) == int(evaluated_request_count)
    )


def _candidate_source_errors(
    *,
    source_date: str,
    batch_report: dict[str, Any],
    detailed_report: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if batch_report.get("schema") != BATCH_SCHEMA:
        errors.append("batch_schema_invalid")
    if batch_report.get("target_date") != source_date:
        errors.append("batch_target_date_mismatch")
    if batch_report.get("status") not in {
        "completed_offline_only",
        "completed_offline_only_with_cohort_failures",
    }:
        errors.append("batch_not_completed")
    if (
        batch_report.get("runtime_effect") is not False
        or batch_report.get("allowed_runtime_apply") is not False
        or batch_report.get("actual_order_submitted") is not False
        or batch_report.get("broker_order_forbidden") is not True
    ):
        errors.append("batch_authority_contract_invalid")
    krx_rows = [
        row
        for row in batch_report.get("cohorts") or []
        if isinstance(row, dict)
        and _normalize_venue(row.get("effective_venue")) == CANARY_VENUE
        and _normalize_session(row.get("session_bucket")) == CANARY_SESSION
    ]
    if len(krx_rows) != 1 or krx_rows[0].get("status") != "completed_offline_only":
        errors.append("krx_cohort_not_completed")
    if len(krx_rows) == 1:
        selection = krx_rows[0].get("candidate_execution_selection")
        if (
            not isinstance(selection, dict)
            or selection.get("outcome_blind") is not True
            or selection.get("contract_pass") is not True
        ):
            errors.append("krx_execution_selection_invalid")
        elif selection.get("policy") != EXPECTED_CANDIDATE_SELECTION_POLICY:
            errors.append("krx_execution_selection_policy_stale")
        elif not _selection_checkpoint_contract_pass(
            selection,
            evaluated_request_count=int(
                krx_rows[0].get("evaluated_request_count") or 0
            ),
        ):
            errors.append("krx_execution_selection_checkpoint_invalid")
        if krx_rows[0].get("promotion_quality_gate_pass") is not True:
            errors.append("krx_batch_promotion_gate_not_passed")

    cohort_filter = detailed_report.get("cohort_filter")
    cohort_filter = cohort_filter if isinstance(cohort_filter, dict) else {}
    if detailed_report.get("schema") != DETAILED_REPORT_SCHEMA:
        errors.append("detailed_schema_invalid")
    if detailed_report.get("target_date") != source_date:
        errors.append("detailed_target_date_mismatch")
    if (
        _normalize_venue(cohort_filter.get("effective_venue")) != CANARY_VENUE
        or _normalize_session(cohort_filter.get("session_bucket")) != CANARY_SESSION
    ):
        errors.append("detailed_cohort_not_krx_regular")
    request_versions = {
        str((row.get("candidate") or {}).get("prompt_version") or "")
        for row in detailed_report.get("requests") or []
        if isinstance(row, dict) and isinstance(row.get("candidate"), dict)
    }
    expected_request_version = (
        f"{DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION}_entry"
    )
    if request_versions != {expected_request_version}:
        errors.append("detailed_candidate_prompt_contract_mismatch")
    request_evidence_versions = {
        str((row.get("candidate") or {}).get("entry_setup_evidence_version") or "")
        for row in detailed_report.get("requests") or []
        if isinstance(row, dict) and isinstance(row.get("candidate"), dict)
    }
    request_composer_versions = {
        str((row.get("candidate") or {}).get("entry_decision_composer_version") or "")
        for row in detailed_report.get("requests") or []
        if isinstance(row, dict) and isinstance(row.get("candidate"), dict)
    }
    request_phase_versions = {
        str(
            (row.get("candidate") or {}).get("entry_structure_phase_policy_version")
            or ""
        )
        for row in detailed_report.get("requests") or []
        if isinstance(row, dict) and isinstance(row.get("candidate"), dict)
    }
    if detailed_report.get(
        "entry_setup_evidence_version"
    ) != ENTRY_SETUP_EVIDENCE_VERSION or request_evidence_versions != {
        ENTRY_SETUP_EVIDENCE_VERSION
    }:
        errors.append("detailed_entry_setup_evidence_version_stale")
    if detailed_report.get(
        "entry_decision_composer_version"
    ) != ENTRY_DECISION_COMPOSER_VERSION or request_composer_versions != {
        ENTRY_DECISION_COMPOSER_VERSION
    }:
        errors.append("detailed_entry_decision_composer_version_stale")
    if detailed_report.get(
        "entry_structure_phase_policy_version"
    ) != STRUCTURE_PHASE_POLICY_VERSION or request_phase_versions != {
        STRUCTURE_PHASE_POLICY_VERSION
    }:
        errors.append("detailed_entry_structure_phase_policy_version_stale")
    selection = detailed_report.get("candidate_execution_selection")
    if (
        not isinstance(selection, dict)
        or selection.get("outcome_blind") is not True
        or selection.get("contract_pass") is not True
    ):
        errors.append("detailed_execution_selection_invalid")
    elif selection.get("policy") != EXPECTED_CANDIDATE_SELECTION_POLICY:
        errors.append("detailed_execution_selection_policy_stale")
    elif not _selection_checkpoint_contract_pass(
        selection,
        evaluated_request_count=int(detailed_report.get("request_count") or 0),
    ):
        errors.append("detailed_execution_selection_checkpoint_invalid")
    if detailed_report.get("promotion_report_integrity_pass") is not True:
        errors.append("detailed_promotion_integrity_not_passed")
    if detailed_report.get("promotion_quality_gate_pass") is not True:
        errors.append("detailed_promotion_quality_not_passed")
    if detailed_report.get("provider_failed_count") != 0:
        errors.append("detailed_provider_failure")
    if detailed_report.get("candidate_provider_none_count") != 0:
        errors.append("detailed_provider_none")
    if (
        detailed_report.get("runtime_effect") is not False
        or detailed_report.get("allowed_runtime_apply") is not False
        or detailed_report.get("actual_order_submitted") is not False
        or detailed_report.get("broker_order_forbidden") is not True
    ):
        errors.append("detailed_authority_contract_invalid")
    cumulative = detailed_report.get("cumulative_learning")
    cumulative = cumulative if isinstance(cumulative, dict) else {}
    if cumulative.get("schema") != "anticipatory_reversal_cumulative_learning_v2":
        errors.append("cumulative_schema_invalid")
    if cumulative.get("status") != "cumulative_learning_updated":
        errors.append("cumulative_status_not_updated")
    if cumulative.get("as_of_date") != source_date:
        errors.append("cumulative_as_of_date_mismatch")
    if cumulative.get("clean_tuning_baseline_date") != CLEAN_TUNING_BASELINE_DATE:
        errors.append("cumulative_clean_baseline_invalid")
    if (
        cumulative.get("runtime_effect") is not False
        or cumulative.get("allowed_runtime_apply") is not False
    ):
        errors.append("cumulative_authority_contract_invalid")
    if cumulative.get("promotion_quality_gate_pass") is not True:
        errors.append("cumulative_promotion_gate_not_passed")
    cumulative_checks = cumulative.get("promotion_quality_checks")
    cumulative_checks = cumulative_checks if isinstance(cumulative_checks, dict) else {}
    if any(
        cumulative_checks.get(key) is not True
        for key in CUMULATIVE_PROMOTION_CHECK_KEYS
    ):
        errors.append("cumulative_promotion_checks_incomplete")
    cumulative_scope = cumulative.get("cohort_scope")
    cumulative_scope = cumulative_scope if isinstance(cumulative_scope, dict) else {}
    if (
        cumulative_scope.get("isolated") is not True
        or _normalize_venue(cumulative_scope.get("effective_venue")) != CANARY_VENUE
        or _normalize_session(cumulative_scope.get("session_bucket")) != CANARY_SESSION
    ):
        errors.append("cumulative_cohort_not_krx_regular")
    if cumulative.get("candidate_contract_sha256") != detailed_report.get(
        "candidate_contract_sha256"
    ):
        errors.append("cumulative_candidate_contract_mismatch")
    cumulative_floor = cumulative.get("promotion_evidence_floor")
    cumulative_floor = cumulative_floor if isinstance(cumulative_floor, dict) else {}
    if cumulative_floor.get("pass") is not True:
        errors.append("cumulative_exposure_floor_not_passed")
    try:
        cumulative_exposure_count = int(
            cumulative.get("candidate_exposure_decision_count") or 0
        )
        cumulative_symbol_count = int(
            cumulative.get("candidate_exposure_unique_symbol_count") or 0
        )
    except (TypeError, ValueError):
        cumulative_exposure_count = 0
        cumulative_symbol_count = 0
    if cumulative_exposure_count < 10 or cumulative_symbol_count < 3:
        errors.append("cumulative_exposure_counts_below_floor")
    cumulative_risk_budget = cumulative.get("candidate_probe_risk_budget")
    cumulative_risk_budget = (
        cumulative_risk_budget if isinstance(cumulative_risk_budget, dict) else {}
    )
    if cumulative_risk_budget.get("pass") is not True:
        errors.append("cumulative_probe_risk_budget_not_passed")
    if not str(detailed_report.get("candidate_contract_sha256") or ""):
        errors.append("candidate_contract_sha256_missing")
    return list(dict.fromkeys(errors))


def _exploration_source_errors(
    *,
    source_errors: list[str],
    detailed_report: dict[str, Any],
) -> list[str]:
    """Validate learning authority without weakening performance promotion."""

    errors = [
        error
        for error in source_errors
        if error not in PERFORMANCE_PROMOTION_ERROR_CODES
    ]
    daily_floor = detailed_report.get("candidate_probe_arm_sample_floor")
    daily_floor = daily_floor if isinstance(daily_floor, dict) else {}
    cumulative = detailed_report.get("cumulative_learning")
    cumulative = cumulative if isinstance(cumulative, dict) else {}
    cumulative_floor = cumulative.get("exploration_evidence_floor")
    cumulative_floor = cumulative_floor if isinstance(cumulative_floor, dict) else {}
    if daily_floor.get("pass") is not True:
        errors.append("daily_probe_arm_floor_not_passed")
    if cumulative_floor.get("pass") is not True:
        errors.append("cumulative_probe_arm_floor_not_passed")
    try:
        arm_rows = int(cumulative.get("candidate_probe_arm_decision_count") or 0)
        arm_symbols = int(
            cumulative.get("candidate_probe_arm_unique_symbol_count") or 0
        )
    except (TypeError, ValueError):
        arm_rows = 0
        arm_symbols = 0
    if arm_rows < 10 or arm_symbols < 3:
        errors.append("cumulative_probe_arm_counts_below_floor")
    return list(dict.fromkeys(errors))


def build_live_candidate(
    *,
    source_date: str,
    batch_report: dict[str, Any],
    detailed_report: dict[str, Any],
    detailed_path: Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    current = generated_at or datetime.now(KST)
    current = (
        current.replace(tzinfo=KST)
        if current.tzinfo is None
        else current.astimezone(KST)
    )
    errors = _candidate_source_errors(
        source_date=source_date,
        batch_report=batch_report,
        detailed_report=detailed_report,
    )
    detailed_sha256 = _safe_file_sha256(detailed_path)
    if not detailed_sha256:
        errors.append("detailed_report_file_unreadable")
    performance_ready = not errors
    exploration_errors = _exploration_source_errors(
        source_errors=errors,
        detailed_report=detailed_report,
    )
    exploration_ready = bool(not performance_ready and not exploration_errors)
    ready = performance_ready or exploration_ready
    canary_mode = (
        PERFORMANCE_CANARY_MODE
        if performance_ready
        else EXPLORATION_CANARY_MODE if exploration_ready else None
    )
    cumulative = detailed_report.get("cumulative_learning")
    cumulative = cumulative if isinstance(cumulative, dict) else {}
    opportunity = detailed_report.get("opportunity_capture_tradeoff")
    opportunity = opportunity if isinstance(opportunity, dict) else {}
    cumulative_opportunity = cumulative.get("opportunity_capture_tradeoff")
    cumulative_opportunity = (
        cumulative_opportunity if isinstance(cumulative_opportunity, dict) else {}
    )
    candidate = {
        "schema": LIVE_CANDIDATE_SCHEMA,
        "source_date": source_date,
        "effective_date": _candidate_effective_date(
            source_date=source_date,
            generated_at=current,
        ),
        "effective_date_policy": EFFECTIVE_DATE_POLICY,
        "preopen_candidate_cutoff_kst": PREOPEN_CANDIDATE_CUTOFF_KST.isoformat(),
        "generated_at": current.isoformat(),
        "status": (
            "live_auto_apply_ready"
            if performance_ready
            else "bounded_exploration_apply_ready" if exploration_ready else "blocked"
        ),
        "canary_mode": canary_mode,
        "blocking_reasons": exploration_errors if not ready else [],
        "performance_promotion_blocking_reasons": errors,
        "selected_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        "rollback_prompt_version": (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "effective_venue": CANARY_VENUE,
        "session_bucket": CANARY_SESSION,
        "candidate_contract_sha256": detailed_report.get("candidate_contract_sha256"),
        "entry_setup_evidence_version": ENTRY_SETUP_EVIDENCE_VERSION,
        "entry_decision_composer_version": ENTRY_DECISION_COMPOSER_VERSION,
        "entry_structure_phase_policy_version": STRUCTURE_PHASE_POLICY_VERSION,
        "promotion_metrics": {
            "promotion_quality_gate_basis": detailed_report.get(
                "promotion_quality_gate_basis"
            ),
            "daily_candidate_exposure_decision_count": detailed_report.get(
                "candidate_exposure_decision_count"
            ),
            "daily_candidate_exposure_unique_symbol_count": detailed_report.get(
                "candidate_exposure_unique_symbol_count"
            ),
            "candidate_exposure_decision_count": cumulative.get(
                "candidate_exposure_decision_count"
            ),
            "candidate_exposure_unique_symbol_count": cumulative.get(
                "candidate_exposure_unique_symbol_count"
            ),
            "daily_candidate_probe_arm_decision_count": detailed_report.get(
                "candidate_probe_arm_decision_count"
            ),
            "daily_candidate_probe_arm_unique_symbol_count": detailed_report.get(
                "candidate_probe_arm_unique_symbol_count"
            ),
            "candidate_probe_arm_decision_count": cumulative.get(
                "candidate_probe_arm_decision_count"
            ),
            "candidate_probe_arm_unique_symbol_count": cumulative.get(
                "candidate_probe_arm_unique_symbol_count"
            ),
            "candidate_primary_decision_ev_pct": cumulative.get(
                "candidate_primary_decision_ev_pct"
            ),
            "candidate_execution_cost_adjusted_ev_pct": cumulative.get(
                "candidate_exposure_probe_cost_adjusted_ev_pct"
            ),
            "daily_net_missed_upside_value_pct": opportunity.get(
                "net_missed_upside_value_pct"
            ),
            "net_missed_upside_value_pct": cumulative_opportunity.get(
                "net_missed_upside_value_pct"
            ),
            "bounded_probe_risk_budget": cumulative.get("candidate_probe_risk_budget"),
            "probe_arm_counterfactual_risk": cumulative.get(
                "candidate_probe_arm_risk_budget"
            ),
        },
        "source_provenance": {
            "batch_report_path": str(batch_report_path(source_date)),
            "batch_evidence_sha256": _canonical_sha256(_batch_evidence(batch_report)),
            "detailed_report_path": str(detailed_path),
            "detailed_report_sha256": detailed_sha256,
        },
        "activation_mode": "first_available_krx_trading_date_preopen_only",
        "operator_approval_required": False,
        "operator_disable_env": CANARY_ENV_KEY,
        "risk_contract": {
            "eligible_position_tags": list(CANARY_POSITION_TAGS),
            "one_share_probe_first_required": True,
            "ai_full_entry_forbidden": True,
            "fresh_submit_revalidation_required": True,
            "post_probe_direction_recheck_required": True,
            "residual_multi_leg_existing_owner_required": performance_ready,
            "residual_multi_leg_forbidden": exploration_ready,
            "scale_in_forbidden": exploration_ready,
            "maximum_daily_exploration_probes": (
                EXPLORATION_MAX_DAILY_PROBES if exploration_ready else None
            ),
            "account_order_quantity_cooldown_guards_required": True,
            "hard_protect_emergency_exit_guards_required": True,
            "same_stage_prompt_owner_count": 1,
            "nxt_promotion_separate": True,
        },
        "metric_role": "bounded_krx_entry_prompt_live_candidate",
        "decision_authority": "preopen_date_scoped_krx_prompt_selection_only",
        "window_policy": (
            "clean_baseline_cumulative_same_contract_krx_regular_plus_current_full_day"
        ),
        "sample_floor": (
            "candidate_exposure_10_rows_3_symbols"
            if performance_ready
            else "candidate_probe_arm_10_rows_3_symbols"
        ),
        "primary_decision_metric": (
            "candidate_probe_cost_adjusted_ev_pct"
            if performance_ready
            else "guard_filtered_one_share_probe_outcome"
        ),
        "source_quality_gate": (
            "promotion_integrity_and_cumulative_quality_pass"
            if performance_ready
            else "report_integrity_and_cumulative_probe_arm_floor_pass"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": ready,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "nxt_or_premarket_prompt_selection",
            "provider_model_price_quantity_or_cap_change",
            "direct_full_entry_from_ai",
            "broker_or_safety_guard_bypass",
            "intraday_cross_venue_promotion",
            "bot_process_control",
        ],
    }
    candidate["artifact_sha256"] = _canonical_sha256(candidate)
    return candidate


def publish_live_candidate(
    *,
    source_date: str,
    batch_report: dict[str, Any],
    write: bool,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    detailed_path = detailed_report_path(source_date)
    candidate = build_live_candidate(
        source_date=source_date,
        batch_report=batch_report,
        detailed_report=_read_json(detailed_path),
        detailed_path=detailed_path,
        generated_at=generated_at,
    )
    path = live_candidate_path(source_date)
    if write:
        _atomic_write_json(path, candidate)
    return {
        "path": str(path),
        "status": candidate["status"],
        "canary_mode": candidate.get("canary_mode"),
        "blocking_reasons": candidate["blocking_reasons"],
        "performance_promotion_blocking_reasons": candidate.get(
            "performance_promotion_blocking_reasons"
        ),
        "effective_date": candidate["effective_date"],
        "artifact_sha256": candidate["artifact_sha256"],
        "allowed_runtime_apply": candidate["allowed_runtime_apply"],
    }


def _validate_candidate_artifact(
    candidate: dict[str, Any],
    *,
    target_date: str,
    candidate_path: Path,
    runtime_env: dict[str, str] | None = None,
) -> list[str]:
    errors: list[str] = []
    source_date = str(candidate.get("source_date") or "")
    try:
        expected_effective_date = _candidate_effective_date(
            source_date=source_date,
            generated_at=candidate.get("generated_at"),
        )
    except (TypeError, ValueError, RuntimeError):
        expected_effective_date = None
        errors.append("candidate_effective_date_schedule_invalid")
    if expected_effective_date != target_date:
        errors.append("candidate_effective_date_schedule_mismatch")
    if (
        candidate.get("effective_date_policy") != EFFECTIVE_DATE_POLICY
        or candidate.get("preopen_candidate_cutoff_kst")
        != PREOPEN_CANDIDATE_CUTOFF_KST.isoformat()
        or candidate.get("activation_mode")
        != "first_available_krx_trading_date_preopen_only"
    ):
        errors.append("candidate_effective_date_policy_invalid")
    if candidate.get("schema") != LIVE_CANDIDATE_SCHEMA:
        errors.append("candidate_schema_invalid")
    canary_mode = str(candidate.get("canary_mode") or "")
    expected_status = (
        "live_auto_apply_ready"
        if canary_mode == PERFORMANCE_CANARY_MODE
        else (
            "bounded_exploration_apply_ready"
            if canary_mode == EXPLORATION_CANARY_MODE
            else None
        )
    )
    if not expected_status or candidate.get("status") != expected_status:
        errors.append("candidate_not_live_ready")
    if candidate.get("effective_date") != target_date:
        errors.append("candidate_effective_date_mismatch")
    if candidate.get("allowed_runtime_apply") is not True:
        errors.append("candidate_runtime_apply_not_allowed")
    if (
        candidate.get("runtime_effect") is not False
        or candidate.get("actual_order_submitted") is not False
        or candidate.get("broker_order_forbidden") is not True
        or candidate.get("effective_date_policy") != EFFECTIVE_DATE_POLICY
        or candidate.get("preopen_candidate_cutoff_kst")
        != PREOPEN_CANDIDATE_CUTOFF_KST.isoformat()
        or candidate.get("activation_mode")
        != "first_available_krx_trading_date_preopen_only"
    ):
        errors.append("candidate_authority_contract_invalid")
    if (
        _normalize_venue(candidate.get("effective_venue")) != CANARY_VENUE
        or _normalize_session(candidate.get("session_bucket")) != CANARY_SESSION
    ):
        errors.append("candidate_cohort_invalid")
    if candidate.get("selected_prompt_version") != (
        DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    ):
        errors.append("candidate_selected_prompt_invalid")
    if candidate.get("rollback_prompt_version") != (
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
    ):
        errors.append("candidate_rollback_prompt_invalid")
    if candidate.get("entry_setup_evidence_version") != ENTRY_SETUP_EVIDENCE_VERSION:
        errors.append("candidate_entry_setup_evidence_version_stale")
    if (
        candidate.get("entry_decision_composer_version")
        != ENTRY_DECISION_COMPOSER_VERSION
    ):
        errors.append("candidate_entry_decision_composer_version_stale")
    if (
        candidate.get("entry_structure_phase_policy_version")
        != STRUCTURE_PHASE_POLICY_VERSION
    ):
        errors.append("candidate_entry_structure_phase_policy_version_stale")
    artifact_sha = str(candidate.get("artifact_sha256") or "")
    if artifact_sha != _canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    ):
        errors.append("candidate_artifact_sha256_invalid")
    provenance = candidate.get("source_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    batch_path = Path(str(provenance.get("batch_report_path") or ""))
    detailed_path = Path(str(provenance.get("detailed_report_path") or ""))
    if batch_path != batch_report_path(source_date):
        errors.append("candidate_batch_path_invalid")
    batch = _read_json(batch_path) if batch_path.is_file() else {}
    if not batch_path.is_file() or _canonical_sha256(
        _batch_evidence(batch)
    ) != provenance.get("batch_evidence_sha256"):
        errors.append("candidate_batch_evidence_mismatch")
    if detailed_path != detailed_report_path(source_date):
        errors.append("candidate_detailed_path_invalid")
    detailed_sha256 = _safe_file_sha256(detailed_path)
    if not detailed_sha256 or detailed_sha256 != provenance.get(
        "detailed_report_sha256"
    ):
        errors.append("candidate_detailed_report_hash_mismatch")
    detailed = _read_json(detailed_path) if detailed_sha256 else {}
    source_errors = _candidate_source_errors(
        source_date=source_date,
        batch_report=batch,
        detailed_report=detailed,
    )
    if canary_mode == EXPLORATION_CANARY_MODE:
        source_errors = _exploration_source_errors(
            source_errors=source_errors,
            detailed_report=detailed,
        )
    errors.extend(source_errors)
    if candidate_path != live_candidate_path(source_date):
        errors.append("candidate_path_invalid")
    errors.extend(
        _runtime_candidate_contract_errors(candidate, target_date=target_date)
    )
    errors.extend(
        _runtime_probe_contract_errors(target_date=target_date, env=runtime_env)
    )
    return list(dict.fromkeys(errors))


def _runtime_candidate_contract_errors(
    candidate: dict[str, Any], *, target_date: str
) -> list[str]:
    errors: list[str] = []
    expected_artifact_sha = _canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    )
    if candidate.get("artifact_sha256") != expected_artifact_sha:
        errors.append("runtime_candidate_artifact_sha256_invalid")
    canary_mode = str(candidate.get("canary_mode") or "")
    expected_status = (
        "live_auto_apply_ready"
        if canary_mode == PERFORMANCE_CANARY_MODE
        else (
            "bounded_exploration_apply_ready"
            if canary_mode == EXPLORATION_CANARY_MODE
            else None
        )
    )
    if (
        candidate.get("schema") != LIVE_CANDIDATE_SCHEMA
        or not expected_status
        or candidate.get("status") != expected_status
        or candidate.get("effective_date") != target_date
        or candidate.get("selected_prompt_version")
        != DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        or candidate.get("rollback_prompt_version")
        != DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        or candidate.get("entry_setup_evidence_version") != ENTRY_SETUP_EVIDENCE_VERSION
        or candidate.get("entry_decision_composer_version")
        != ENTRY_DECISION_COMPOSER_VERSION
        or candidate.get("entry_structure_phase_policy_version")
        != STRUCTURE_PHASE_POLICY_VERSION
        or candidate.get("allowed_runtime_apply") is not True
        or candidate.get("runtime_effect") is not False
        or candidate.get("actual_order_submitted") is not False
        or candidate.get("broker_order_forbidden") is not True
        or candidate.get("effective_date_policy") != EFFECTIVE_DATE_POLICY
        or candidate.get("preopen_candidate_cutoff_kst")
        != PREOPEN_CANDIDATE_CUTOFF_KST.isoformat()
        or candidate.get("activation_mode")
        != "first_available_krx_trading_date_preopen_only"
    ):
        errors.append("runtime_candidate_authority_contract_invalid")
    if (
        _normalize_venue(candidate.get("effective_venue")) != CANARY_VENUE
        or _normalize_session(candidate.get("session_bucket")) != CANARY_SESSION
    ):
        errors.append("runtime_candidate_cohort_invalid")
    risk_contract = candidate.get("risk_contract")
    risk_contract = risk_contract if isinstance(risk_contract, dict) else {}
    if risk_contract.get("eligible_position_tags") != list(CANARY_POSITION_TAGS):
        errors.append("runtime_candidate_position_owner_scope_invalid")
    for key in (
        "one_share_probe_first_required",
        "ai_full_entry_forbidden",
        "fresh_submit_revalidation_required",
        "post_probe_direction_recheck_required",
        "account_order_quantity_cooldown_guards_required",
        "hard_protect_emergency_exit_guards_required",
        "nxt_promotion_separate",
    ):
        if risk_contract.get(key) is not True:
            errors.append(f"runtime_candidate_risk_contract_invalid:{key}")
    if risk_contract.get("same_stage_prompt_owner_count") != 1:
        errors.append("runtime_candidate_same_stage_owner_invalid")
    if canary_mode == PERFORMANCE_CANARY_MODE:
        if risk_contract.get("residual_multi_leg_existing_owner_required") is not True:
            errors.append(
                "runtime_candidate_risk_contract_invalid:"
                "residual_multi_leg_existing_owner_required"
            )
        if (
            risk_contract.get("residual_multi_leg_forbidden") is not False
            or risk_contract.get("scale_in_forbidden") is not False
        ):
            errors.append("runtime_candidate_performance_expansion_contract_invalid")
    elif canary_mode == EXPLORATION_CANARY_MODE:
        if (
            risk_contract.get("residual_multi_leg_existing_owner_required") is not False
            or risk_contract.get("residual_multi_leg_forbidden") is not True
            or risk_contract.get("scale_in_forbidden") is not True
            or risk_contract.get("maximum_daily_exploration_probes")
            != EXPLORATION_MAX_DAILY_PROBES
        ):
            errors.append("runtime_candidate_exploration_risk_contract_invalid")
    return errors


def build_preopen_activation(
    *,
    target_date: str,
    runtime_env: dict[str, str] | None = None,
    runtime_env_provenance: dict[str, Any] | None = None,
    runtime_env_load_errors: list[str] | None = None,
) -> dict[str, Any]:
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for path in LIVE_CANDIDATE_DIR.glob(
        "entry_setup_v2_14_bounded_live_candidate_*.json"
    ):
        payload = _read_json(path)
        if payload.get("effective_date") == target_date:
            candidates.append((str(payload.get("source_date") or ""), path, payload))
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = candidates[0] if candidates else None
    errors: list[str] = list(runtime_env_load_errors or [])
    if not _enabled_by_operator(runtime_env):
        errors.append("operator_disabled")
    if selected is None:
        errors.append("no_effective_date_candidate")
    candidate_path = selected[1] if selected else None
    candidate = selected[2] if selected else {}
    if selected is not None:
        errors.extend(
            _validate_candidate_artifact(
                candidate,
                target_date=target_date,
                candidate_path=selected[1],
                runtime_env=runtime_env,
            )
        )
    candidate_file_sha256 = (
        _safe_file_sha256(candidate_path) if candidate_path else None
    )
    if selected is not None and not candidate_file_sha256:
        errors.append("candidate_file_unreadable")
    active = not errors
    canary_mode = candidate.get("canary_mode") if active else None
    candidate_risk_contract = candidate.get("risk_contract")
    candidate_risk_contract = (
        candidate_risk_contract if isinstance(candidate_risk_contract, dict) else {}
    )
    activation = {
        "schema": PREOPEN_ACTIVATION_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": "active_bounded_canary" if active else "inactive_fallback_v2_13",
        "canary_mode": canary_mode,
        "blocking_reasons": list(dict.fromkeys(errors)),
        "selected_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            if active
            else DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "rollback_prompt_version": (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "effective_venue": CANARY_VENUE,
        "session_bucket": CANARY_SESSION,
        "source_date": candidate.get("source_date"),
        "candidate_path": str(candidate_path) if candidate_path else None,
        "candidate_file_sha256": candidate_file_sha256,
        "candidate_artifact_sha256": candidate.get("artifact_sha256"),
        "candidate_contract_sha256": candidate.get("candidate_contract_sha256"),
        "entry_setup_evidence_version": candidate.get("entry_setup_evidence_version"),
        "entry_decision_composer_version": candidate.get(
            "entry_decision_composer_version"
        ),
        "entry_structure_phase_policy_version": candidate.get(
            "entry_structure_phase_policy_version"
        ),
        "runtime_env_provenance": dict(runtime_env_provenance or {}),
        "runtime_effect": active,
        "allowed_runtime_apply": active,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "activation_contract": {
            "preopen_only": True,
            "eligible_position_tags": candidate_risk_contract.get(
                "eligible_position_tags"
            ),
            "one_share_probe_first_required": True,
            "ai_full_entry_forbidden": True,
            "residual_multi_leg_forbidden": candidate_risk_contract.get(
                "residual_multi_leg_forbidden"
            ),
            "scale_in_forbidden": candidate_risk_contract.get("scale_in_forbidden"),
            "maximum_daily_exploration_probes": candidate_risk_contract.get(
                "maximum_daily_exploration_probes"
            ),
            "nxt_control_unchanged": True,
            "configured_v2_13_owner_required": True,
            "automatic_fallback_on_any_contract_gap": True,
        },
    }
    activation["artifact_sha256"] = _canonical_sha256(activation)
    return activation


def write_preopen_activation(
    *,
    target_date: str,
    runtime_env: dict[str, str] | None = None,
    runtime_env_provenance: dict[str, Any] | None = None,
    runtime_env_load_errors: list[str] | None = None,
) -> dict[str, Any]:
    activation = build_preopen_activation(
        target_date=target_date,
        runtime_env=runtime_env,
        runtime_env_provenance=runtime_env_provenance,
        runtime_env_load_errors=runtime_env_load_errors,
    )
    _atomic_write_json(activation_path(target_date), activation)
    return activation


def _load_activation_cached(target_date: str) -> dict[str, Any]:
    path = activation_path(target_date)
    try:
        stat = path.stat()
    except OSError:
        return {}
    cache_key = f"{path}:{stat.st_mtime_ns}:{stat.st_size}"
    with _CACHE_LOCK:
        if _ACTIVATION_CACHE.get("cache_key") == cache_key:
            return dict(_ACTIVATION_CACHE.get("payload") or {})
        payload = _read_json(path)
        _ACTIVATION_CACHE.clear()
        _ACTIVATION_CACHE.update({"cache_key": cache_key, "payload": payload})
        return dict(payload)


def resolve_live_prompt_policy(
    *,
    configured_prompt_version: str,
    effective_venue: Any,
    session_bucket: Any,
    position_tag: Any = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = (now or datetime.now(KST)).astimezone(KST)
    target_date = current.date().isoformat()
    fallback = str(configured_prompt_version or "").strip()
    result = {
        "enabled": False,
        "status": "fallback_configured_prompt",
        "selected_prompt_version": fallback,
        "rollback_prompt_version": (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "target_date": target_date,
        "effective_venue": _normalize_venue(effective_venue),
        "session_bucket": _normalize_session(session_bucket),
        "position_tag": str(position_tag or "").strip().upper(),
        "activation_path": str(activation_path(target_date)),
        "runtime_effect": False,
        "canary_mode": None,
    }
    if fallback != DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION:
        result["status"] = "fallback_same_stage_owner_conflict"
        return result
    if not _enabled_by_operator():
        result["status"] = "fallback_operator_disabled"
        return result
    if (
        result["effective_venue"] != CANARY_VENUE
        or result["session_bucket"] != CANARY_SESSION
    ):
        result["status"] = "fallback_non_krx_regular_cohort"
        return result
    if result["position_tag"] not in CANARY_POSITION_TAGS:
        result["status"] = "fallback_position_owner_out_of_scope"
        return result
    runtime_contract_errors = _runtime_probe_contract_errors(target_date=target_date)
    if runtime_contract_errors:
        result["status"] = "fallback_probe_first_runtime_contract_invalid"
        result["runtime_contract_errors"] = runtime_contract_errors
        return result
    activation = _load_activation_cached(target_date)
    artifact_sha = str(activation.get("artifact_sha256") or "")
    if artifact_sha != _canonical_sha256(
        {key: value for key, value in activation.items() if key != "artifact_sha256"}
    ):
        result["status"] = "fallback_activation_hash_invalid"
        return result
    candidate_path = Path(str(activation.get("candidate_path") or ""))
    activation_contract = activation.get("activation_contract")
    activation_contract = (
        activation_contract if isinstance(activation_contract, dict) else {}
    )
    candidate_file_sha256 = str(activation.get("candidate_file_sha256") or "")
    canary_mode = str(activation.get("canary_mode") or "")
    activation_mode_contract_valid = bool(
        (
            canary_mode == PERFORMANCE_CANARY_MODE
            and activation_contract.get("residual_multi_leg_forbidden") is False
            and activation_contract.get("scale_in_forbidden") is False
            and activation_contract.get("maximum_daily_exploration_probes") is None
        )
        or (
            canary_mode == EXPLORATION_CANARY_MODE
            and activation_contract.get("residual_multi_leg_forbidden") is True
            and activation_contract.get("scale_in_forbidden") is True
            and activation_contract.get("maximum_daily_exploration_probes")
            == EXPLORATION_MAX_DAILY_PROBES
        )
    )
    if (
        activation.get("schema") != PREOPEN_ACTIVATION_SCHEMA
        or activation.get("target_date") != target_date
        or activation.get("status") != "active_bounded_canary"
        or activation.get("runtime_effect") is not True
        or activation.get("allowed_runtime_apply") is not True
        or activation.get("actual_order_submitted") is not False
        or activation.get("broker_order_forbidden") is not True
        or activation.get("selected_prompt_version")
        != DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        or activation.get("rollback_prompt_version") != fallback
        or activation.get("entry_setup_evidence_version")
        != ENTRY_SETUP_EVIDENCE_VERSION
        or activation.get("entry_decision_composer_version")
        != ENTRY_DECISION_COMPOSER_VERSION
        or activation.get("entry_structure_phase_policy_version")
        != STRUCTURE_PHASE_POLICY_VERSION
        or _normalize_venue(activation.get("effective_venue")) != CANARY_VENUE
        or _normalize_session(activation.get("session_bucket")) != CANARY_SESSION
        or activation_contract.get("preopen_only") is not True
        or activation_contract.get("eligible_position_tags")
        != list(CANARY_POSITION_TAGS)
        or activation_contract.get("one_share_probe_first_required") is not True
        or activation_contract.get("ai_full_entry_forbidden") is not True
        or activation_contract.get("nxt_control_unchanged") is not True
        or activation_contract.get("configured_v2_13_owner_required") is not True
        or activation_contract.get("automatic_fallback_on_any_contract_gap") is not True
        or not activation_mode_contract_valid
        or not candidate_path.is_file()
        or not candidate_file_sha256
        or _safe_file_sha256(candidate_path) != candidate_file_sha256
    ):
        result["status"] = "fallback_activation_contract_invalid"
        return result
    candidate = _read_json(candidate_path)
    candidate_errors = _runtime_candidate_contract_errors(
        candidate,
        target_date=target_date,
    )
    if candidate.get("artifact_sha256") != activation.get("candidate_artifact_sha256"):
        candidate_errors.append("runtime_candidate_activation_sha_mismatch")
    if candidate.get("candidate_contract_sha256") != activation.get(
        "candidate_contract_sha256"
    ):
        candidate_errors.append("runtime_candidate_prompt_contract_sha_mismatch")
    if candidate.get("canary_mode") != canary_mode:
        candidate_errors.append("runtime_candidate_canary_mode_mismatch")
    if candidate.get("entry_setup_evidence_version") != activation.get(
        "entry_setup_evidence_version"
    ):
        candidate_errors.append("runtime_candidate_evidence_version_mismatch")
    if candidate.get("entry_decision_composer_version") != activation.get(
        "entry_decision_composer_version"
    ):
        candidate_errors.append("runtime_candidate_composer_version_mismatch")
    if candidate.get("entry_structure_phase_policy_version") != activation.get(
        "entry_structure_phase_policy_version"
    ):
        candidate_errors.append("runtime_candidate_structure_phase_version_mismatch")
    if candidate_errors:
        result["status"] = "fallback_candidate_contract_invalid"
        result["runtime_contract_errors"] = list(dict.fromkeys(candidate_errors))
        return result
    result.update(
        {
            "enabled": True,
            "status": "active_bounded_krx_canary",
            "selected_prompt_version": (
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ),
            "source_date": activation.get("source_date"),
            "candidate_contract_sha256": activation.get("candidate_contract_sha256"),
            "entry_setup_evidence_version": activation.get(
                "entry_setup_evidence_version"
            ),
            "entry_decision_composer_version": activation.get(
                "entry_decision_composer_version"
            ),
            "entry_structure_phase_policy_version": activation.get(
                "entry_structure_phase_policy_version"
            ),
            "activation_artifact_sha256": artifact_sha,
            "canary_mode": canary_mode,
            "maximum_daily_exploration_probes": (
                EXPLORATION_MAX_DAILY_PROBES
                if canary_mode == EXPLORATION_CANARY_MODE
                else None
            ),
            "runtime_effect": True,
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize the date-scoped V2.14 KRX PREOPEN activation."
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--runtime-env-file")
    parser.add_argument("--operator-env-file")
    parser.add_argument("--dated-operator-env-file")
    args = parser.parse_args(argv)
    date.fromisoformat(args.target_date)
    runtime_env = None
    runtime_env_provenance = None
    runtime_env_load_errors = None
    if args.runtime_env_file or args.operator_env_file or args.dated_operator_env_file:
        if not args.runtime_env_file or not args.operator_env_file:
            parser.error(
                "--runtime-env-file and --operator-env-file must be provided together"
            )
        runtime_env, runtime_env_provenance, runtime_env_load_errors = (
            load_preopen_runtime_env(
                runtime_env_file=Path(args.runtime_env_file),
                operator_env_file=Path(args.operator_env_file),
                dated_operator_env_file=(
                    Path(args.dated_operator_env_file)
                    if args.dated_operator_env_file
                    else None
                ),
            )
        )
    activation = (
        write_preopen_activation(
            target_date=args.target_date,
            runtime_env=runtime_env,
            runtime_env_provenance=runtime_env_provenance,
            runtime_env_load_errors=runtime_env_load_errors,
        )
        if args.write
        else build_preopen_activation(
            target_date=args.target_date,
            runtime_env=runtime_env,
            runtime_env_provenance=runtime_env_provenance,
            runtime_env_load_errors=runtime_env_load_errors,
        )
    )
    print(json.dumps(activation, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
