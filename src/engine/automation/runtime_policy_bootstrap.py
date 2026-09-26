"""Compose approved runtime policy state without running a tuning search.

The bootstrap carries the latest verified incumbent environment, overlays
explicit operator locks, and reapplies permanent retirement settings.  It does
not call providers, brokers, order code, or create economic candidates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation import operator_policy_succession
from src.engine.ai.holding_exit_vote import path_policy_baseline_receipt
from src.engine.scalping.holding_path_vote_policy import (
    ENV_DATE as HOLDING_VOTE_ENV_DATE,
    ENV_PATH as HOLDING_VOTE_ENV_PATH,
    ENV_SHA as HOLDING_VOTE_ENV_SHA,
    load_bundle as load_holding_vote_bundle,
    policy_path as holding_vote_policy_path,
    verify_source_handoff as verify_holding_vote_source_handoff,
)
from src.engine.lifecycle.retirement import (
    RETIRED_FAMILIES,
    retirement_env,
    without_retired_env,
)
from src.engine.scalping.trailing_mechanical_policy import (
    CLASSIFIER_ENV_KEY as SCALP_TRAILING_CLASSIFIER_ENV_KEY,
    CLASSIFIER_MARKET_ENV_KEYS as SCALP_TRAILING_CLASSIFIER_MARKET_ENV_KEYS,
    MARKET_ENV_KEYS as SCALP_TRAILING_MARKET_ENV_KEYS,
    TP_KEYS as SCALP_TRAILING_THRESHOLD_KEYS,
    VECTOR_SHA_ENV_KEY as SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY,
    baseline_receipt as scalp_trailing_bootstrap_receipt,
    selected_policy_env as scalp_trailing_selected_policy_env,
)
from src.utils.constants import DATA_DIR

SCHEMA_VERSION = 1
REPORT_TYPE = "runtime_policy_bootstrap"
BOOTSTRAP_DIR = DATA_DIR / "runtime" / "policy_bootstrap"
LEGACY_RUNTIME_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
OPERATOR_LOCK_DIR = DATA_DIR / "threshold_cycle" / "operator_runtime_env_locks"
RISING_MISSED_REPORT_DIR = DATA_DIR / "report" / "rising_missed_classifier_prior"
RISING_MISSED_ENV_BY_AXIS = {
    "positive_support_min": "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN",
    "spread_caution_ratio": "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO",
    "chase_delta_pct": "KORSTOCKSCAN_RISING_MISSED_TP1_CHASE_DELTA_PCT",
}
EXACT_DATE_HANDOFF_ENV = {
    "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED": "true",
}
PRE_SUBMIT_DELAY_ENV_KEYS = (
    "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED",
    "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE",
    "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE",
)
HOLDING_VOTE_ENV_KEYS = (HOLDING_VOTE_ENV_PATH, HOLDING_VOTE_ENV_SHA,
                         HOLDING_VOTE_ENV_DATE)


def _holding_vote_handoff(target_date: str) -> tuple[dict[str, str], dict[str, Any]]:
    """Bind the exact target-date bundle to its postclose report bytes."""
    policy_file = holding_vote_policy_path(DATA_DIR, target_date)
    receipt: dict[str, Any] = {
        "status": "baseline_policy_not_published", "target_date": target_date,
        "path": str(policy_file), "allowed_runtime_apply": False,
    }
    if not policy_file.exists():
        return {}, receipt
    try:
        bundle = load_holding_vote_bundle(DATA_DIR, target_date)
        source_date = bundle["source_date"]
        verify_holding_vote_source_handoff(DATA_DIR, bundle)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        receipt["status"] = "baseline_policy_rejected"
        receipt["reason"] = str(exc)
        return {}, receipt
    receipt.update({
        "status": "estimated_provisional_verified",
        "source_date": source_date,
        "source_report_sha256": bundle["source_report_sha256"],
        "bundle_sha256": bundle["bundle_sha256"],
        "policy_set_sha256": bundle["policy_set_sha256"],
        "cell_count": len(bundle["cells"]),
        "evidence_grade": bundle["evidence_grade"],
        "realized_paired_ev_krw": None,
        "allowed_runtime_apply": True,
    })
    return {
        HOLDING_VOTE_ENV_PATH: str(policy_file),
        HOLDING_VOTE_ENV_SHA: bundle["bundle_sha256"],
        HOLDING_VOTE_ENV_DATE: target_date,
    }, receipt


def _pre_submit_delay_handoff(target_date: str) -> tuple[dict[str, str], dict[str, Any]]:
    """Carry the newest validated positive delay policy until superseded."""
    from src.engine.scalping.pre_submit_delay_tuning import (
        DELAYS_SEC, _digest, _number, _validated_candidate, report_path,
    )

    directory = DATA_DIR / "threshold_cycle" / "pre_submit_delay_policy"
    matches: list[tuple[str, str, Path, dict[str, Any]]] = []
    for path in directory.glob("pre_submit_delay_policy_????-??-??.json"):
        if path.is_symlink() or path.stat().st_size > 1024 * 1024:
            continue
        try:
            policy = _load_json(path)
        except (OSError, ValueError):
            continue
        effective_from = str(policy.get("effective_from") or "")
        expires_on = str(policy.get("expires_on") or "")
        if effective_from <= target_date <= expires_on:
            matches.append((effective_from, str(policy.get("source_date") or ""), path, policy))
    if not matches:
        return {}, {"status": "not_published", "target_date": target_date}
    saw_source_gap = False
    saw_invalid = False
    for effective_from, source_date, path, policy in sorted(matches, reverse=True):
        report_file = report_path(source_date)
        try:
            report = _load_json(report_file)
        except (OSError, ValueError):
            continue
        digest = policy.get("policy_sha256")
        valid = (
            policy.get("schema") == "pre_submit_delay_policy_v1"
            and report.get("schema") == "pre_submit_delay_tuning_v1"
            and policy.get("source_date") == report.get("source_date") == source_date
            and policy.get("effective_from") == report.get("effective_date") == effective_from
            and source_date < effective_from <= target_date
            and policy.get("expires_on", "") >= target_date
            and policy.get("carry_forward_until_superseded") is True
            and digest == _digest({key: value for key, value in policy.items() if key != "policy_sha256"})
            and report.get("policy_sha256") == digest
            and policy.get("report_sha256")
            == _digest({key: value for key, value in report.items() if key != "policy_sha256"})
        )
        selected = _number(policy.get("selected_delay_sec"))
        selector_only = (
            selected is None
            and policy.get("selection_status") == "selected_by_type"
            and policy.get("runtime_apply_allowed") is True
        )
        unresolved = selected is None and not selector_only
        if unresolved:
            saw_source_gap = True
            valid = bool(valid
                         and policy.get("selection_status") == "unselected_source_gap"
                         and policy.get("runtime_apply_allowed") is False
                         and report.get("status") == "source_gap"
                         and report.get("runtime_effect") is False
                         and report.get("selected_delay_sec") is None)
        else:
            valid = bool(valid and policy.get("runtime_apply_allowed") is True)
        if selected is not None:
            valid = bool(valid and selected in DELAYS_SEC and selected > 0
                         and _validated_candidate(policy, report))
        branch_delays = []
        for family, evidence_key, key_name in (
            ("scope_policies", "scope_census", "scope_key"),
            ("type_policies", "type_census", "type_key"),
        ):
            branches = policy.get(family, {})
            evidence_rows = report.get(evidence_key, [])
            if not isinstance(branches, dict):
                valid = False
                continue
            for key, branch in branches.items():
                delay_sec = _number(branch.get("selected_delay_sec")) if isinstance(branch, dict) else None
                branch_delays.append(delay_sec)
                unresolved_branch = (
                    delay_sec is None and unresolved and isinstance(branch, dict)
                    and branch.get("selection_status") == "unselected_source_gap"
                    and branch.get("runtime_apply_allowed") is False
                )
                if unresolved_branch:
                    continue
                if (delay_sec not in DELAYS_SEC or delay_sec <= 0
                        or not any(isinstance(row, dict) and row.get(key_name) == key for row in evidence_rows)
                        or not _validated_candidate(policy, report, **{key_name: key})):
                    valid = False
        if not valid:
            saw_invalid = True
            continue
        if unresolved:
            continue
        if not any(value and value > 0 for value in [selected, *branch_delays]):
            continue
        return {
            "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED": "true",
            "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE": str(path.resolve()),
            "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE": target_date,
        }, {
            "status": "verified_candidate" if effective_from == target_date else "verified_carried_candidate",
            "target_date": target_date,
            "source_date": source_date,
            "effective_from": effective_from,
            "policy_sha256": digest,
            "source_receipt": _file_receipt(path),
            "report_receipt": _file_receipt(report_file),
        }
    return {}, {
        "status": (
            "no_validated_candidate_source_gap" if saw_source_gap
            else "binding_invalid" if saw_invalid
            else "not_published"
        ),
        "target_date": target_date,
        "runtime_policy_bound": False,
    }


def env_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_{target_date}.env"


def manifest_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_{target_date}.json"


def verify_path(target_date: str) -> Path:
    return BOOTSTRAP_DIR / f"runtime_policy_bootstrap_verify_{target_date}.json"


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_json(value: Any) -> str:
    return _digest_bytes(
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"object_required:{path}")
    return payload


def _file_receipt(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "sha256": _digest_bytes(raw),
        "size_bytes": len(raw),
    }


def _publish(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _manifest_candidates(target_date: str) -> list[Path]:
    maximum = date.fromisoformat(target_date)
    rows: list[tuple[date, int, Path]] = []
    patterns = (
        (BOOTSTRAP_DIR, "runtime_policy_bootstrap_*.json", 1),
        (LEGACY_RUNTIME_DIR, "threshold_runtime_env_*.json", 0),
    )
    for directory, pattern, priority in patterns:
        for path in directory.glob(pattern):
            if "verify" in path.stem:
                continue
            try:
                payload_date = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
            except ValueError:
                continue
            # A same-date bootstrap is an output of this command. Reusing it as
            # its own incumbent would make source_incumbent point at a file
            # that is replaced later in the same write and fail verification.
            eligible = (
                payload_date < maximum
                if directory == BOOTSTRAP_DIR
                else payload_date <= maximum
            )
            if eligible:
                rows.append((payload_date, priority, path))
    return [row[2] for row in sorted(rows, reverse=True)]


def _legacy_common_handoff_migration_allowed(
    payload: dict[str, Any], verification: dict[str, Any], source_date: str
) -> bool:
    """Allow the one-time Daily/EV cutover when family policy checks passed.

    The retired common handoff could mark the legacy verification as failed
    even though every selected family and dated override was verified.  Do not
    generalize that state into an accepted failure: only the known unselected
    integrated-axis handoff findings are eligible.
    """

    if verification.get("target_date") not in (None, source_date):
        return False
    if verification.get("status") != "fail" or verification.get("passed") is not False:
        return False
    if verification.get("fail_reason") != "runtime_env_handoff_missing":
        return False
    for key in (
        "runtime_policy_fail_count",
        "dated_runtime_override_fail_count",
        "unverified_selected_family_count",
        "missing_family_count",
    ):
        if verification.get(key) != 0:
            return False
    if set(verification.get("selected_families") or []) != set(
        payload.get("selected_families") or []
    ):
        return False
    allowed_details = {
        "integrated_axis_unconfigured",
        "integrated_axis_policy_date_mismatch",
        "integrated_axis_shared_policy_hash_mismatch",
    }
    findings = verification.get("findings")
    return bool(findings) and all(
        isinstance(row, dict)
        and row.get("family") == "integrated_entry_axis_bundle"
        and row.get("severity") == "runtime_policy_unusable"
        and row.get("detail") in allowed_details
        for row in findings
    )


def _load_incumbent(target_date: str) -> tuple[dict[str, Any], Path, str]:
    for path in _manifest_candidates(target_date):
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        values = payload.get("env_overrides")
        source_date = str(payload.get("target_date") or path.stem.rsplit("_", 1)[-1])
        if path.parent == BOOTSTRAP_DIR:
            try:
                verification = _load_json(
                    BOOTSTRAP_DIR / f"runtime_policy_bootstrap_verify_{source_date}.json"
                )
            except (OSError, ValueError, json.JSONDecodeError):
                verification = {}
            unsigned = {
                key: value for key, value in payload.items() if key != "manifest_sha256"
            }
            verified = (
                verification.get("status") == "pass"
                and payload.get("manifest_sha256") == _digest_json(unsigned)
            )
            verification_basis = "bootstrap_self_hash_and_verify_pass"
        else:
            try:
                verification = _load_json(
                    LEGACY_RUNTIME_DIR / f"threshold_runtime_env_verify_{source_date}.json"
                )
            except (OSError, ValueError, json.JSONDecodeError):
                verification = {}
            if verification.get("status") == "pass":
                verified = True
                verification_basis = "legacy_verification_pass"
            else:
                verified = _legacy_common_handoff_migration_allowed(
                    payload, verification, source_date
                )
                verification_basis = "legacy_common_handoff_migration"
        if verified and isinstance(values, dict) and values:
            return payload, path, verification_basis
    raise ValueError("approved_incumbent_runtime_env_missing")


def _date_in_lock_window(lock: dict[str, Any], target_date: str) -> bool:
    active_from = str(
        lock.get("active_from_date") or lock.get("created_date") or ""
    ).strip()
    if active_from and target_date < active_from:
        return False
    if bool(lock.get("lock_until_explicit_close")) or bool(
        lock.get("explicit_close_required")
    ):
        return True
    active_until = str(
        lock.get("min_observation_until_date")
        or lock.get("expires_after_source_date")
        or lock.get("target_date")
        or ""
    ).strip()
    return not active_until or target_date <= active_until


def _load_locks(target_date: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for path in sorted(OPERATOR_LOCK_DIR.glob("*.json")):
        try:
            lock = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "reason": f"unreadable:{type(exc).__name__}",
                }
            )
            continue
        lock["path"] = str(path.resolve())
        lock["source_receipt"] = _file_receipt(path)
        if not lock.get("family") or not operator_policy_succession.lock_values(lock):
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "lock_id": lock.get("lock_id"),
                    "family": lock.get("family"),
                    "source_receipt": lock["source_receipt"],
                    "reason": "lock_identity_or_env_missing",
                }
            )
            continue
        if not _date_in_lock_window(lock, target_date):
            rejected.append(
                {
                    "path": str(path.resolve()),
                    "lock_id": lock.get("lock_id"),
                    "family": lock.get("family"),
                    "source_receipt": lock["source_receipt"],
                    "reason": "outside_active_window",
                }
            )
            continue
        rows.append(lock)
    return rows, rejected


def _receipt_date_state(payload: dict[str, Any], target_date: str) -> tuple[bool, str]:
    target = str(payload.get("target_date") or "").strip()
    effective = str(
        payload.get("effective_date")
        or payload.get("prepared_effective_date")
        or ""
    ).strip()
    publication = str(payload.get("publication_date") or "").strip()
    source = str(payload.get("source_date") or payload.get("date") or "").strip()
    if target:
        return target == target_date, "target_date"
    if effective:
        return effective == target_date, "effective_date"
    if publication and publication > target_date:
        return False, "future_publication_date"
    if source and source > target_date:
        return False, "future_source_date"
    if source or publication:
        return True, "carried_source_date"
    return False, "date_identity_missing"


def _receipt_family(payload: dict[str, Any], path: Path) -> str:
    raw = str(
        payload.get("runtime_family")
        or payload.get("family")
        or payload.get("report_type")
        or payload.get("schema")
        or path.stem.rsplit("_", 1)[0]
    ).strip()
    if raw == "scanner_lookup_attention_preopen":
        return "scanner_lookup_attention"
    if raw == "machine_microstructure_policy_approval":
        return "machine_microstructure"
    if raw == "machine_entry_timing_tuning":
        return "machine_entry_timing"
    if raw.startswith("low_price_two_leg"):
        return "low_price_two_leg"
    return raw


def _receipt_runtime_apply_allowed(payload: dict[str, Any]) -> bool:
    if payload.get("allowed_runtime_apply") is True or payload.get(
        "runtime_apply_allowed"
    ) is True:
        return True
    if payload.get("report_type") == "scanner_lookup_attention_preopen":
        source_policy = (
            payload.get("source_policy")
            if isinstance(payload.get("source_policy"), dict)
            else {}
        )
        return payload.get("active") is True and source_policy.get(
            "allowed_runtime_apply"
        ) is True
    return False


def direct_policy_digest(payload: dict[str, Any]) -> str:
    canonical = {key: value for key, value in payload.items() if key != "policy_sha256"}
    canonical_env = dict(canonical.get("runtime_env_overrides") or {})
    canonical_env.pop("KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256", None)
    canonical["runtime_env_overrides"] = canonical_env
    return _digest_json(canonical)


def validate_rising_missed_policy_binding(
    policy: dict[str, Any], source_report: dict[str, Any]
) -> str | None:
    source_date = str(policy.get("source_date") or "").strip()
    if (
        source_report.get("schema_version") != 2
        or source_report.get("report_type") != "rising_missed_classifier_prior"
        or str(source_report.get("target_date") or "") != source_date
    ):
        return "source_report_contract_invalid"
    report_semantic_sha = _digest_json(
        {
            key: value
            for key, value in source_report.items()
            if key != "artifact_sha256"
        }
    )
    if (
        source_report.get("artifact_sha256") != report_semantic_sha
        or policy.get("source_report_sha256") != report_semantic_sha
    ):
        return "source_report_sha256_mismatch"
    if policy.get("consumer_schema") != "rising_missed_tp1_selector_bounded_env_v1":
        return "consumer_schema_invalid"
    status = str(policy.get("status") or "")
    runtime_env = policy.get("runtime_env_overrides")
    economic = (
        source_report.get("economic_evaluation")
        if isinstance(source_report.get("economic_evaluation"), dict)
        else {}
    )
    if status == "validated_edge":
        if (
            source_report.get("status") != "validated_edge"
            or economic.get("comparison_status") != "validated_edge"
            or economic.get("allowed_runtime_apply") is not True
            or int(economic.get("validated_candidate_count") or 0) != 1
            or policy.get("runtime_effect") is not True
            or not isinstance(runtime_env, dict)
            or not runtime_env
        ):
            return "validated_edge_source_state_mismatch"
    elif status == "incumbent_preserved":
        if (
            source_report.get("status") == "validated_edge"
            or policy.get("runtime_effect") is not False
            or runtime_env not in ({}, None)
        ):
            return "incumbent_source_state_mismatch"
    else:
        return "policy_status_invalid"
    return None


def _direct_runtime_env(
    family: str, payload: dict[str, Any], target_date: str
) -> tuple[dict[str, str], str | None]:
    raw = payload.get("runtime_env_overrides")
    if family == "scalp_trailing_four_axis_selector":
        return {}, "legacy_ai_tp_policy_retired"
    if family == "scalp_trailing_mechanical_three_axis_selector":
        if not isinstance(raw, dict) or set(raw) != {
            env_key for markets in SCALP_TRAILING_MARKET_ENV_KEYS.values()
            for env_key in markets.values()
        } | {
            env_key for markets in SCALP_TRAILING_CLASSIFIER_MARKET_ENV_KEYS.values()
            for env_key in markets.values()
        }:
            return {}, "scalp_trailing_market_env_keys_invalid"
        return {str(key): str(value) for key, value in raw.items()}, None
    if raw in (None, {}):
        if family == "rising_missed_tp1_selector" and payload.get(
            "policy_sha256"
        ) != direct_policy_digest(payload):
            return {}, "policy_sha256_mismatch"
        return {}, None
    if not isinstance(raw, dict):
        return {}, "runtime_env_overrides_invalid"
    if family != "rising_missed_tp1_selector":
        return {}, "runtime_env_overrides_family_not_allowlisted"
    allowed = {
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE",
        "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO",
        "KORSTOCKSCAN_RISING_MISSED_TP1_CHASE_DELTA_PCT",
        "KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256",
    }
    if set(raw) - allowed:
        return {}, "runtime_env_key_not_allowlisted"
    values = {str(key): str(value) for key, value in raw.items()}
    if values.get("KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED") != "true":
        return {}, "selector_enabled_value_invalid"
    if values.get("KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE") != target_date:
        return {}, "selector_active_date_invalid"
    tuned_keys = set(values).intersection(RISING_MISSED_ENV_BY_AXIS.values())
    if len(tuned_keys) != 1:
        return {}, "runtime_env_single_axis_required"
    selected_axis = str(payload.get("selected_axis") or "")
    if RISING_MISSED_ENV_BY_AXIS.get(selected_axis) not in tuned_keys:
        return {}, "selected_axis_env_mismatch"
    try:
        if "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN" in values and not (
            1 <= int(values["KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN"]) <= 3
        ):
            raise ValueError
        if "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO" in values and not (
            0.0015
            <= float(values["KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO"])
            <= 0.0025
        ):
            raise ValueError
        if "KORSTOCKSCAN_RISING_MISSED_TP1_CHASE_DELTA_PCT" in values and not (
            2.5 <= float(values["KORSTOCKSCAN_RISING_MISSED_TP1_CHASE_DELTA_PCT"]) <= 3.5
        ):
            raise ValueError
    except ValueError:
        return {}, "runtime_env_value_out_of_bounds"
    digest = values.get("KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256", "")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        return {}, "policy_sha256_invalid"
    if payload.get("policy_sha256") != direct_policy_digest(payload) or digest != payload.get(
        "policy_sha256"
    ):
        return {}, "policy_sha256_mismatch"
    return values, None


def validate_rising_missed_policy_receipt(
    policy: dict[str, Any], source_report: dict[str, Any], effective_date: str
) -> str | None:
    """Apply the same semantic checks used by the PREOPEN consumer."""
    _, runtime_env_error = _direct_runtime_env(
        "rising_missed_tp1_selector", policy, effective_date
    )
    if runtime_env_error:
        return runtime_env_error
    return validate_rising_missed_policy_binding(policy, source_report)


def _load_direct_receipts(
    target_date: str, receipt_paths: Iterable[Path]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for raw_path in receipt_paths:
        path = Path(raw_path).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            payload = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            rejected.append(
                {"path": str(path), "reason": f"unreadable:{type(exc).__name__}"}
            )
            continue
        valid_date, date_basis = _receipt_date_state(payload, target_date)
        family = _receipt_family(payload, path)
        runtime_apply_allowed = _receipt_runtime_apply_allowed(payload)
        runtime_env, runtime_env_error = _direct_runtime_env(
            family, payload, target_date
        )
        source_binding_error = None
        if family == "rising_missed_tp1_selector" and runtime_env_error is None:
            source_date = str(payload.get("source_date") or "").strip()
            try:
                source_report = _load_json(
                    RISING_MISSED_REPORT_DIR
                    / f"rising_missed_classifier_prior_{source_date}.json"
                )
            except (OSError, ValueError, json.JSONDecodeError):
                source_binding_error = "source_report_unreadable"
            else:
                source_binding_error = validate_rising_missed_policy_receipt(
                    payload, source_report, target_date
                )
        if family == "scalp_trailing_mechanical_three_axis_selector" and runtime_env_error is None:
            source_date = str(payload.get("source_date") or "")
            try:
                if date.fromisoformat(source_date).isoformat() != source_date:
                    raise ValueError("source_date_format")
                source_path = (DATA_DIR / "report" / "monitor_snapshots"
                               / f"holding_exit_observation_{source_date}.json")
                if source_path.stat().st_size > 64 * 1024 * 1024:
                    raise ValueError("source_report_exceeds_read_limit")
                source_bytes = source_path.read_bytes()
                source_report = json.loads(source_bytes)
                manifest_path = (DATA_DIR / "report" / "monitor_snapshots" / "manifests"
                                 / f"monitor_snapshot_manifest_{source_date}_postclose_exit.json")
                manifest_bytes = manifest_path.read_bytes()
                source_manifest = json.loads(manifest_bytes)
                if (source_manifest.get("profile") != "postclose_exit"
                        or source_manifest.get("target_date") != source_date
                        or source_manifest.get("snapshot_sha256", {}).get(
                            "holding_exit_observation") != _digest_bytes(source_bytes)
                        or Path(source_manifest.get("snapshot_paths", {}).get(
                            "holding_exit_observation", "")).resolve() != source_path.resolve()
                        or payload.get("source_manifest_sha256") != _digest_bytes(manifest_bytes)):
                    raise ValueError("postclose_exit_manifest_binding_invalid")
                expected_env = scalp_trailing_selected_policy_env(
                    payload, source_report, target_date=target_date,
                    report_sha256=_digest_bytes(source_bytes),
                )
                if runtime_env != expected_env:
                    raise ValueError("selected_env_mismatch")
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                source_binding_error = f"scalp_trailing_selection_invalid:{exc}"
        row = {
            "family": family,
            "source_receipt": _file_receipt(path),
            "date_basis": date_basis,
            "source_date": payload.get("source_date") or payload.get("date"),
            "target_date": payload.get("target_date"),
            "effective_date": payload.get("effective_date")
            or payload.get("prepared_effective_date"),
            "status": payload.get("status")
            or payload.get("decision")
            or payload.get("selection_status"),
            "allowed_runtime_apply": runtime_apply_allowed,
            "runtime_effect": payload.get("runtime_effect"),
            "runtime_env_overrides": runtime_env,
        }
        if not family:
            rejected.append({**row, "reason": "family_identity_missing"})
        elif not valid_date:
            rejected.append({**row, "reason": f"date_invalid:{date_basis}"})
        elif not runtime_apply_allowed:
            rejected.append({**row, "reason": "runtime_apply_not_authorized"})
        elif runtime_env_error:
            rejected.append({**row, "reason": runtime_env_error})
        elif source_binding_error:
            rejected.append({**row, "reason": source_binding_error})
        else:
            accepted.append(row)
    return accepted, rejected


def _operator_overrides(target_date: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    values: dict[str, str] = {}
    receipts: list[dict[str, Any]] = []
    for name in (
        "operator_runtime_overrides.env",
        f"operator_runtime_overrides_{target_date}.env",
    ):
        path = LEGACY_RUNTIME_DIR / name
        if not path.exists():
            continue
        parsed = operator_policy_succession.read_operator_env(path)
        values.update(without_retired_env(parsed))
        receipts.append({**_file_receipt(path), "env_keys": sorted(parsed)})
    return values, receipts


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def build_manifest(
    target_date: str, *, receipt_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    incumbent, incumbent_path, incumbent_verification_basis = _load_incumbent(
        target_date
    )
    incumbent_values = {
        str(key): str(value)
        for key, value in (incumbent.get("env_overrides") or {}).items()
    }
    values = without_retired_env(incumbent_values)
    for key in PRE_SUBMIT_DELAY_ENV_KEYS:
        values.pop(key, None)
    # These are bootstrap-consumption coordinates, not tuning values.  Refresh
    # them for the manifest's exact date instead of inheriting a stale source
    # date.  The operator layer is applied afterwards and therefore retains
    # explicit veto authority over the handoff.
    values.update(EXACT_DATE_HANDOFF_ENV)
    values["KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE"] = target_date
    operator_values, operator_sources = _operator_overrides(target_date)
    values.update(operator_values)
    direct_receipts, rejected_receipts = _load_direct_receipts(
        target_date, receipt_paths
    )
    if any(row.get("family") == "scalp_trailing_mechanical_three_axis_selector"
           and row.get("allowed_runtime_apply") is True
           for row in rejected_receipts):
        raise ValueError("selected_scalp_trailing_policy_invalid_fail_closed")
    delay_env, delay_handoff = _pre_submit_delay_handoff(target_date)
    locks, invalid_locks = _load_locks(target_date)
    applied_locks: list[dict[str, Any]] = []
    rejected_locks: list[dict[str, Any]] = list(invalid_locks)
    env_owners = {key: "approved_incumbent" for key in values}
    for key in (
        *EXACT_DATE_HANDOFF_ENV,
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE",
    ):
        if key not in operator_values:
            env_owners[key] = "runtime_policy_bootstrap_exact_date_handoff"
    env_owners.update({key: "operator_runtime_override" for key in operator_values})
    incumbent_trailing = incumbent.get("scalp_trailing_mechanical_policy_receipt") or {}
    prior_selected_trailing = (
        incumbent_trailing.get("source") == "reviewed_selected_candidate"
        and isinstance(incumbent_trailing.get("market_values_sha256"), str)
    )
    # The 2026-09-25 operator direction supersedes the inherited 0.6% baseline.
    # A later reviewed selector may replace it through an exact rollback parent.
    start_keys = (
        "KORSTOCKSCAN_SCALP_TRAILING_START_PCT",
        *(SCALP_TRAILING_MARKET_ENV_KEYS["SCALP_TRAILING_START_PCT"].values()),
    )
    start_directive_active = target_date >= "2026-09-25" and not prior_selected_trailing
    if start_directive_active:
        for key in start_keys:
            values[key] = "0.4"
            env_owners[key] = "operator_directed_2026_09_25"
    accepted_direct_receipts = []
    for receipt in direct_receipts:
        if receipt["family"] in {
            "nxt_rising_missed_tp1_partial_runner", "scalp_mfe_protect_exit"
        }:
            rejected_receipts.append({**receipt, "reason": "exit_owner_retired"})
            continue
        if receipt["family"] == "scalp_trailing_mechanical_three_axis_selector":
            if any(row["family"] == receipt["family"] for row in accepted_direct_receipts):
                rejected_receipts.append({**receipt, "reason": "multiple_same_stage_candidates"})
                continue
            selected_env = receipt["runtime_env_overrides"]
            operator_conflicts = sorted(
                key for key, value in selected_env.items()
                if key in operator_values and operator_values[key] != value
                and not (start_directive_active and key in start_keys)
            )
            lock_conflicts = sorted({
                key for lock in locks
                if operator_policy_succession.classify(lock) != "inactive_archive"
                for key, value in operator_policy_succession.lock_values(lock).items()
                if key in selected_env and str(value) != selected_env[key]
                and not (start_directive_active and key in start_keys)
            })
            if operator_conflicts or lock_conflicts:
                rejected_receipts.append({
                    **receipt, "reason": "operator_or_lock_veto_conflict",
                    "env_keys": sorted(set(operator_conflicts + lock_conflicts)),
                })
                continue
            parent_values = {
                key: value for key, value in values.items()
                if key not in {
                    f"KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_{market}"
                    for market in ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")
                } and key not in {
                    "KORSTOCKSCAN_SCALP_TRAILING_MARKET_VECTOR_SHA256",
                    "KORSTOCKSCAN_SCALP_TRAILING_VALUE_SHA256",
                    "KORSTOCKSCAN_SCALP_TRAILING_START_BY_MARKET_SHA256",
                    SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY,
                }
            }
            parent = scalp_trailing_bootstrap_receipt(parent_values, source="rollback_incumbent")[
                "market_values_sha256"
            ]
            try:
                policy = _load_json(Path(receipt["source_receipt"]["path"]))
            except (OSError, ValueError, json.JSONDecodeError):
                rejected_receipts.append({**receipt, "reason": "selected_receipt_unreadable"})
                continue
            if policy.get("rollback_market_values_sha256") != parent:
                raise ValueError("selected_scalp_trailing_rollback_parent_hash_mismatch")
            candidate_receipt = scalp_trailing_bootstrap_receipt(
                {**parent_values, **selected_env}, source="reviewed_selected_candidate"
            )
            parent_receipt = scalp_trailing_bootstrap_receipt(
                parent_values, source="rollback_incumbent"
            )
            changed_markets = [
                market for market in candidate_receipt["market_values"]
                if (candidate_receipt["market_values"][market]
                    != parent_receipt["market_values"][market]
                    or candidate_receipt["classifier_parameters"][market]
                    != parent_receipt["classifier_parameters"][market])
            ]
            if len(changed_markets) != 1 or policy.get("changed_market") != changed_markets[0]:
                raise ValueError("selected_scalp_trailing_one_market_canary_invalid")
        for key, value in receipt.get("runtime_env_overrides", {}).items():
            values[key] = str(value)
            env_owners[key] = f"direct_policy:{receipt['family']}"
        accepted_direct_receipts.append(receipt)
    direct_receipts = accepted_direct_receipts
    for key, value in delay_env.items():
        if key not in operator_values:
            values[key] = value
            env_owners[key] = "pre_submit_delay_exact_date_policy"
    for lock in locks:
        classification = operator_policy_succession.classify(lock)
        row = {
            "lock_id": lock.get("lock_id"),
            "family": lock.get("family"),
            "classification": classification,
            "source_receipt": lock["source_receipt"],
        }
        if classification == "inactive_archive":
            rejected_locks.append({**row, "reason": "inactive_archive"})
            continue
        lock_env = without_retired_env(operator_policy_succession.lock_values(lock))
        superseded_start_keys = (
            sorted(set(lock_env).intersection(start_keys))
            if start_directive_active else []
        )
        for key in superseded_start_keys:
            lock_env.pop(key, None)
        if superseded_start_keys and not lock_env:
            rejected_locks.append({
                **row, "reason": "superseded_start_0p4_directive",
                "env_keys": superseded_start_keys,
            })
            continue
        legacy_tp_score_keys = {
            f"KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_{market}"
            for market in ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")
        }
        if legacy_tp_score_keys.intersection(lock_env):
            rejected_locks.append({**row, "reason": "legacy_ai_tp_market_override_retired"})
            continue
        conflicts = sorted(
            key
            for key, value in lock_env.items()
            if key in env_owners
            and env_owners[key].startswith("operator_lock:")
            and values.get(key) != str(value)
        )
        if conflicts:
            rejected_locks.append(
                {**row, "reason": "operator_lock_env_conflict", "env_keys": conflicts}
            )
            continue
        for key, value in lock_env.items():
            values[key] = str(value)
            env_owners[key] = f"operator_lock:{lock.get('lock_id') or lock.get('family')}"
        applied_locks.append({
            **row, "env_keys": sorted(lock_env),
            "superseded_env_keys": superseded_start_keys,
        })
    # Retired exit deferrals must not return through operator or direct receipts.
    retired_keys = set(values) - set(without_retired_env(values))
    values = without_retired_env(values)
    env_owners = {key: owner for key, owner in env_owners.items() if key in values}
    off_values = retirement_env()
    values.update(off_values)
    env_owners.update({key: "explicit_retirement_off" for key in off_values})
    if any(f"KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_{market}" in operator_values
           for market in ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")):
        raise ValueError("operator_legacy_ai_tp_market_override_requires_removal")
    for market in ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET"):
        legacy_score = f"KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_{market}"
        values.pop(legacy_score, None)
        env_owners.pop(legacy_score, None)
    for legacy_hash in (
        "KORSTOCKSCAN_SCALP_TRAILING_MARKET_VECTOR_SHA256",
        "KORSTOCKSCAN_SCALP_TRAILING_VALUE_SHA256",
        "KORSTOCKSCAN_SCALP_TRAILING_START_BY_MARKET_SHA256",
        SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY,
    ):
        values.pop(legacy_hash, None)
        env_owners.pop(legacy_hash, None)
    selected_direct = next((
        row for row in direct_receipts
        if row["family"] == "scalp_trailing_mechanical_three_axis_selector"
    ), None)
    current_trailing_hash = scalp_trailing_bootstrap_receipt(
        values, source="rollback_incumbent"
    )["market_values_sha256"]
    carried_selection = bool(
        not selected_direct and prior_selected_trailing
        and current_trailing_hash == incumbent_trailing["market_values_sha256"]
    )
    trailing_source = (
        "reviewed_selected_candidate"
        if selected_direct or carried_selection
        else "operator_directed_m1_baseline"
    )
    if start_directive_active and trailing_source == "operator_directed_m1_baseline":
        for key in start_keys:
            values[key] = "0.4"
            env_owners[key] = "operator_directed_2026_09_25"
    trailing_receipt = scalp_trailing_bootstrap_receipt(values, source=trailing_source)
    trailing_selection_lineage = (
        {"origin_target_date": target_date,
         "origin_receipt": selected_direct["source_receipt"],
         "market_values_sha256": trailing_receipt["market_values_sha256"],
         "status": "newly_selected"}
        if selected_direct else
        {**(incumbent.get("scalp_trailing_selection_lineage") or {}),
         "market_values_sha256": trailing_receipt["market_values_sha256"],
         "status": "carried_selected"}
        if carried_selection else None
    )
    for key in SCALP_TRAILING_THRESHOLD_KEYS:
        env_key = f"KORSTOCKSCAN_{key}"
        if env_key not in values:
            values[env_key] = str(trailing_receipt["scalar_values"][key])
            env_owners[env_key] = "code_default"
    for threshold, markets in SCALP_TRAILING_MARKET_ENV_KEYS.items():
        for market, env_key in markets.items():
            if env_key not in values:
                values[env_key] = str(trailing_receipt["market_values"][market][threshold])
                env_owners[env_key] = env_owners.get(
                    f"KORSTOCKSCAN_{threshold}", "code_default"
                )
    for axis, markets in SCALP_TRAILING_CLASSIFIER_MARKET_ENV_KEYS.items():
        for market, env_key in markets.items():
            if env_key not in values:
                values[env_key] = str(trailing_receipt["classifier_parameters"][market][axis])
                env_owners[env_key] = "scalp_trailing_mechanical_policy_receipt"
    values[SCALP_TRAILING_CLASSIFIER_ENV_KEY] = trailing_receipt["classifier_version"]
    env_owners[SCALP_TRAILING_CLASSIFIER_ENV_KEY] = "scalp_trailing_mechanical_policy_receipt"
    values[SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY] = trailing_receipt[
        "market_values_sha256"
    ]
    env_owners[SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY] = (
        "scalp_trailing_mechanical_policy_receipt"
    )
    for key in HOLDING_VOTE_ENV_KEYS:
        values.pop(key, None)
        env_owners.pop(key, None)
    holding_vote_env, holding_vote_receipt = _holding_vote_handoff(target_date)
    values.update(holding_vote_env)
    env_owners.update({key: "holding_path_vote_policy" for key in holding_vote_env})
    selected_families = sorted(
        str(item)
        for item in incumbent.get("selected_families") or []
        if str(item) not in RETIRED_FAMILIES
        and str(item) not in {
            "nxt_rising_missed_tp1_partial_runner", "scalp_mfe_protect_exit"
        }
        and str(item) != "scalp_trailing_four_axis_selector"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "producer_code_sha": _git_sha(),
        "selected_release_sha": _git_sha(),
        "source_incumbent": _file_receipt(incumbent_path),
        "source_incumbent_verification_basis": incumbent_verification_basis,
        "source_incumbent_target_date": incumbent.get("target_date"),
        "rollback_env_overrides": dict(
            sorted(without_retired_env(incumbent_values).items())
        ),
        "rollback_owner": "verified_source_incumbent",
        "selection_policy": "retain_approved_incumbent_and_explicit_operator_locks",
        "selected_families": selected_families,
        "selection_changes": [
            {"family": family, "change_class": "retained_approved"}
            for family in selected_families
        ]
        + [
            {
                "family": row.get("family"),
                "change_class": (
                    "explicit_off"
                    if row.get("classification") == "protected_veto"
                    else "operator_lock_preserved"
                ),
            }
            for row in applied_locks
        ]
        + [
            {"family": row["family"], "change_class": "policy_refreshed"}
            for row in direct_receipts
        ],
        "operator_locks_applied": applied_locks,
        "operator_locks_rejected": rejected_locks,
        "operator_override_sources": operator_sources,
        "direct_family_receipts": direct_receipts,
        "pre_submit_delay_handoff": delay_handoff,
        "direct_family_receipts_rejected": rejected_receipts,
        "env_key_owners": env_owners,
        "scalp_trailing_mechanical_policy_receipt": trailing_receipt,
        "scalp_trailing_selection_lineage": trailing_selection_lineage,
        "holding_path_vote_baseline_receipt": path_policy_baseline_receipt(),
        "holding_path_vote_policy_receipt": holding_vote_receipt,
        "env_overrides": dict(sorted(values.items())),
        "retired_key_scrubbed": sorted(
            retired_keys | (set(incumbent_values) - set(without_retired_env(incumbent_values)))
        ),
        "assertions": {
            "provider_called": False,
            "broker_called": False,
            "order_submitted": False,
            "economic_candidate_created": False,
        },
    }


def write_bootstrap(
    target_date: str, *, receipt_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    manifest = build_manifest(target_date, receipt_paths=receipt_paths)
    lines = [
        "# Generated by runtime_policy_bootstrap.py",
        f"# target_date={target_date}",
        "export KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_ENABLED=true",
        f"export KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE={shlex.quote(target_date)}",
    ]
    for key, value in manifest["env_overrides"].items():
        lines.append(f"export {key}={shlex.quote(str(value))}")
    env_content = "\n".join(lines) + "\n"
    manifest["env_file"] = str(env_path(target_date))
    manifest["env_sha256"] = _digest_bytes(env_content.encode("utf-8"))
    unsigned = dict(manifest)
    manifest["manifest_sha256"] = _digest_json(unsigned)
    _publish(env_path(target_date), env_content)
    _publish(
        manifest_path(target_date),
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def _read_proc_env(pid: int) -> dict[str, str]:
    raw = Path(f"/proc/{pid}/environ").read_bytes()
    return {
        key.decode(): value.decode()
        for item in raw.split(b"\0")
        if item and b"=" in item
        for key, value in [item.split(b"=", 1)]
    }


def _launcher_ai_context_overlay(target_date: str) -> dict[str, str]:
    """Resolve the same final context layer sourced by ``src/run_bot.sh``."""

    from src.engine.automation.ai_multi_timeframe_context_promotion import (
        authoritative_runtime_env,
    )

    return authoritative_runtime_env(target_date)


def verify_bootstrap(target_date: str, *, pid: int | None = None, write: bool = True) -> dict[str, Any]:
    findings: list[str] = []
    pid_mismatches: list[str] = []
    pid_env_available = pid is None
    manifest_file = manifest_path(target_date)
    runtime_file = env_path(target_date)
    try:
        manifest = _load_json(manifest_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest = {}
        findings.append(f"manifest_unreadable:{type(exc).__name__}")
    if manifest.get("target_date") != target_date:
        findings.append("target_date_mismatch")
    if manifest.get("report_type") != REPORT_TYPE:
        findings.append("report_type_mismatch")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not manifest.get("manifest_sha256") or manifest.get("manifest_sha256") != _digest_json(unsigned):
        findings.append("manifest_hash_mismatch")
    try:
        raw_env = runtime_file.read_bytes()
    except OSError:
        raw_env = b""
        findings.append("env_unreadable")
    if manifest.get("env_sha256") != _digest_bytes(raw_env):
        findings.append("env_hash_mismatch")
    if manifest.get("assertions") != {
        "provider_called": False,
        "broker_called": False,
        "order_submitted": False,
        "economic_candidate_created": False,
    }:
        findings.append("authority_assertion_mismatch")
    manifest_env = manifest.get("env_overrides")
    if not isinstance(manifest_env, dict):
        findings.append("manifest_env_overrides_invalid")
        manifest_env = {}
    trailing_receipt = manifest.get("scalp_trailing_mechanical_policy_receipt")
    if manifest.get("holding_path_vote_baseline_receipt") != path_policy_baseline_receipt():
        findings.append("holding_path_vote_baseline_receipt_mismatch")
    expected_vote_env, expected_vote_receipt = _holding_vote_handoff(target_date)
    if manifest.get("holding_path_vote_policy_receipt") != expected_vote_receipt:
        findings.append("holding_path_vote_policy_receipt_mismatch")
    if any(manifest_env.get(key) != value for key, value in expected_vote_env.items()):
        findings.append("holding_path_vote_policy_env_mismatch")
    if not expected_vote_env and any(key in manifest_env for key in HOLDING_VOTE_ENV_KEYS):
        findings.append("holding_path_vote_policy_stale_env")
    if trailing_receipt is None:
        findings.append("scalp_trailing_mechanical_policy_receipt_missing")
    else:
        owners = manifest.get("env_key_owners")
        trailing_keys = [f"KORSTOCKSCAN_{key}" for key in SCALP_TRAILING_THRESHOLD_KEYS]
        trailing_keys.extend(
            env_key for markets in SCALP_TRAILING_MARKET_ENV_KEYS.values()
            for env_key in markets.values()
        )
        trailing_keys.extend(
            env_key for markets in SCALP_TRAILING_CLASSIFIER_MARKET_ENV_KEYS.values()
            for env_key in markets.values()
        )
        trailing_keys.extend((SCALP_TRAILING_CLASSIFIER_ENV_KEY,
                              SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY))
        if (
            not isinstance(owners, dict)
            or any(key not in manifest_env or not owners.get(key) for key in trailing_keys)
        ):
            findings.append("scalp_trailing_mechanical_env_or_owner_missing")
            owners = {}
        try:
            source = (
                "reviewed_selected_candidate"
                if any(isinstance(row, dict) and row.get("family")
                       == "scalp_trailing_mechanical_three_axis_selector"
                       for row in manifest.get("direct_family_receipts") or [])
                else "operator_directed_m1_baseline"
            )
            expected_trailing = scalp_trailing_bootstrap_receipt(manifest_env, source=source)
        except (KeyError, TypeError, ValueError):
            findings.append("scalp_trailing_mechanical_policy_receipt_invalid")
        else:
            if trailing_receipt != expected_trailing or manifest_env.get(
                SCALP_TRAILING_MARKET_VECTOR_SHA_ENV_KEY
            ) != expected_trailing["market_values_sha256"] or manifest_env.get(
                SCALP_TRAILING_CLASSIFIER_ENV_KEY
            ) != expected_trailing["classifier_version"]:
                findings.append("scalp_trailing_mechanical_policy_receipt_mismatch")
        if any(f"KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_{market}" in manifest_env
               for market in ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")):
            findings.append("legacy_ai_tp_market_override_present")
    if target_date >= "2026-09-23":
        current_delay_env, current_delay_handoff = _pre_submit_delay_handoff(target_date)
        if manifest.get("pre_submit_delay_handoff") != current_delay_handoff:
            findings.append("pre_submit_delay_generation_changed")
        for key, value in current_delay_env.items():
            if (manifest.get("env_key_owners") or {}).get(key) == "pre_submit_delay_exact_date_policy" and manifest_env.get(key) != value:
                findings.append(f"pre_submit_delay_env_mismatch:{key}")
    if (
        str(
            manifest_env.get(
                "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED"
            )
            or ""
        ).lower()
        != "true"
    ):
        findings.append("exact_date_runtime_auto_apply_disabled")
    if (
        str(manifest_env.get("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE") or "")
        != target_date
    ):
        findings.append("exact_date_runtime_apply_date_mismatch")
    receipt_rows = [manifest.get("source_incumbent")]
    receipt_rows.extend(manifest.get("operator_override_sources") or [])
    receipt_rows.extend(
        row.get("source_receipt")
        for row in (manifest.get("operator_locks_applied") or [])
        if isinstance(row, dict)
    )
    receipt_rows.extend(
        row.get("source_receipt")
        for row in (manifest.get("direct_family_receipts") or [])
        if isinstance(row, dict)
    )
    for receipt in receipt_rows:
        if not isinstance(receipt, dict) or not receipt.get("path"):
            findings.append("source_receipt_missing")
            continue
        source_path = Path(str(receipt["path"]))
        try:
            current = _file_receipt(source_path)
        except OSError:
            findings.append(f"source_receipt_unreadable:{source_path}")
            continue
        if current.get("sha256") != receipt.get("sha256"):
            findings.append(f"source_receipt_hash_mismatch:{source_path}")
    for row in manifest.get("direct_family_receipts") or []:
        if not isinstance(row, dict) or row.get("family") not in {
            "rising_missed_tp1_selector", "scalp_trailing_mechanical_three_axis_selector"
        }:
            continue
        receipt = row.get("source_receipt") or {}
        accepted, rejected = _load_direct_receipts(
            target_date, [Path(str(receipt.get("path") or ""))]
        )
        if not accepted or rejected:
            reason = rejected[0].get("reason") if rejected else "receipt_missing"
            label = (
                "rising_missed_source_binding_invalid"
                if row.get("family") == "rising_missed_tp1_selector"
                else "scalp_trailing_source_binding_invalid"
            )
            findings.append(f"{label}:{reason}")
    if pid is not None and raw_env:
        expected = operator_policy_succession.read_operator_env(runtime_file)
        try:
            expected.update(_launcher_ai_context_overlay(target_date))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            findings.append(
                f"launcher_ai_context_overlay_invalid:{type(exc).__name__}:{exc}"
            )
        try:
            actual = _read_proc_env(pid)
        except OSError as exc:
            findings.append(f"pid_env_unreadable:{type(exc).__name__}")
        else:
            pid_env_available = True
            missing = sorted(key for key, value in expected.items() if actual.get(key) != value)
            if missing:
                pid_mismatches.extend(missing)
                findings.append("pid_env_mismatch:" + ",".join(missing))
    passed = not findings
    result = {
        "schema_version": 1,
        "report_type": "runtime_policy_bootstrap_verify",
        "target_date": target_date,
        "status": "pass" if passed else "fail",
        "passed": passed,
        "findings": findings,
        "manifest_file": str(manifest_file),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "env_file": str(runtime_file),
        "pid": pid,
        "pid_passed": passed if pid is not None else None,
        "pid_env_available": pid_env_available,
        "pid_missing": [] if pid is None or pid_env_available else [pid],
        "pid_mismatches": pid_mismatches,
        "runtime_policy_fail_count": len(findings),
        "dated_runtime_override_fail_count": 0,
        "unverified_selected_family_count": 0,
        "verified_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if write:
        _publish(verify_path(target_date), json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", "--target-date", dest="target_date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--write-verify-artifact",
        action="store_true",
        help="persist the explicit verification result as the current receipt",
    )
    parser.add_argument("--pid", type=int)
    parser.add_argument("--receipt", action="append", type=Path, default=[])
    args = parser.parse_args(argv)
    if args.write == args.verify:
        parser.error("select exactly one of --write or --verify")
    if args.write_verify_artifact and not args.verify:
        parser.error("--write-verify-artifact requires --verify")
    if args.write:
        result = write_bootstrap(args.target_date, receipt_paths=args.receipt)
        verification = verify_bootstrap(args.target_date)
        result["verification"] = verification
        print(json.dumps(result, ensure_ascii=False))
        return 0 if verification["status"] == "pass" else 1
    result = verify_bootstrap(
        args.target_date,
        pid=args.pid,
        write=args.write_verify_artifact,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
