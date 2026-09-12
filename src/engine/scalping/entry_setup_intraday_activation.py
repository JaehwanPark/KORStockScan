"""Operator-authorized, same-day scheduling exception for the existing KRX owner.

Never rewrite a scheduled candidate, reset quota, or grant quantity/order powers.
The launcher must explicitly pin the approval path AND its content hash. The
ordinary PREOPEN resolver remains unchanged when no intraday approval is pinned.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, time
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.engine.scalping import entry_setup_live_policy as policy
from src.utils.constants import PROJECT_ROOT

SCHEMA = "entry_setup_operator_intraday_approval_v1"
PATH_ENV = "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH"
SHA_ENV = "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_SHA256"
CONFIRM = "APPLY_KRX_ONE_SHARE_INTRADAY"
SUPPORTED_DAILY_LIMITS = (
    policy.EXPLORATION_MAX_DAILY_PROBES,
    policy.KRX_EXPLORATION_MAX_DAILY_PROBES,
)
CODE_PATHS = (
    "src/engine/scalping/entry_setup_intraday_activation.py",
    "src/engine/scalping/entry_setup_live_policy.py",
    "src/engine/scalping/entry_setup_evidence.py",
    "src/engine/ai_prompt_contracts.py",
    "src/engine/ai_engine_openai.py",
    "src/utils/constants.py",
    "restart.sh",
    "src/run_bot.sh",
    "src/engine/scalping/micro_reversion/forward_collector.py",
    "src/engine/scalping/multi_timeframe_context.py",
)


def _budget_errors(limit: int, env: dict[str, str] | None = None) -> list[str]:
    if type(limit) is not int or limit not in SUPPORTED_DAILY_LIMITS:
        return ["intraday_exploration_budget_unsupported"]
    if limit == policy.EXPLORATION_MAX_DAILY_PROBES:
        return []
    if policy.expanded_exploration_budget_errors(env):
        return ["intraday_exploration_budget_env_mismatch"]
    return []


@lru_cache(maxsize=32)
def _digest_generation(path: str, mtime_ns: int, ctime_ns: int, size: int) -> str:
    return policy._file_sha256(Path(path))


def _digest(path: Path) -> str:
    stat = path.stat()
    return _digest_generation(
        str(path), stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size
    )


def _stamp(value: Any) -> datetime:
    stamp = datetime.fromisoformat(str(value))
    if stamp.tzinfo is None:
        raise ValueError("intraday_timestamp_timezone_missing")
    return stamp.astimezone(policy.KST)


def _window_errors(approval: dict[str, Any], now: datetime) -> list[str]:
    start = _stamp(approval["not_before"])
    end = _stamp(approval["expires_at"])
    generated = _stamp(approval["generated_at"])
    if (
        now.tzinfo is None
        or approval["target_date"] != now.date().isoformat()
        or start.date() != now.date()
        or end.date() != now.date()
        or generated.date() != now.date()
        or not policy.is_krx_trading_day(now.date())
        or start.time() < time(9, 0)
        or end.time() > time(15, 30)
        or not generated <= start <= now < end
    ):
        return ["intraday_window_inactive_or_invalid"]
    return []


def _candidate_errors(
    candidate: dict[str, Any],
    candidate_path: Path,
    *,
    now: datetime,
    runtime_env: dict[str, str] | None,
) -> list[str]:
    generated = _stamp(candidate["generated_at"])
    if generated.date() != now.date() or generated > now:
        return ["intraday_candidate_not_generated_today"]
    if (
        candidate.get("canary_mode") != policy.EXPLORATION_CANARY_MODE
        or candidate.get("selected_prompt_version")
        != policy.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    ):
        return ["intraday_requires_krx_v2_14_one_share"]
    return policy._validate_candidate_artifact(
        candidate,
        target_date=candidate["effective_date"],
        candidate_path=candidate_path,
        cohort=policy.DEFAULT_COHORT,
        source_bundle_root=candidate_path.parent.parent,
        runtime_target_date=now.date().isoformat(),
        runtime_env=runtime_env,
    )


def build_approval(
    *,
    candidate_path: Path,
    expected_candidate_sha256: str,
    operator_instruction_ref: str,
    expires_at: datetime,
    now: datetime,
    runtime_env: dict[str, str] | None = None,
    maximum_daily_exploration_probes: int = policy.EXPLORATION_MAX_DAILY_PROBES,
) -> dict[str, Any]:
    """Validate the exact original source; the caller supplies operator authority."""
    if now.tzinfo is None:
        raise ValueError("intraday_timestamp_timezone_missing")
    now = now.astimezone(policy.KST)
    candidate_path = candidate_path.absolute()
    if (
        not operator_instruction_ref.strip()
        or _digest(candidate_path) != expected_candidate_sha256
    ):
        raise ValueError("intraday_operator_reference_or_candidate_pin_invalid")
    if not policy._enabled_by_operator(runtime_env):
        raise ValueError("intraday_operator_disabled")
    candidate = policy._read_json(candidate_path)
    errors = _candidate_errors(
        candidate, candidate_path, now=now, runtime_env=runtime_env
    )
    errors.extend(_budget_errors(maximum_daily_exploration_probes, runtime_env))
    if errors:
        raise ValueError(";".join(errors))
    provenance = candidate["source_provenance"]
    sources = [
        candidate_path,
        Path(provenance["batch_report_path"]),
        Path(provenance["detailed_report_path"]),
    ]
    approval = {
        "schema": SCHEMA,
        "target_date": now.date().isoformat(),
        "generated_at": now.isoformat(),
        "not_before": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "operator_instruction_ref": operator_instruction_ref.strip(),
        "approval_mode": "operator_intraday_scheduling_exception",
        "owner": "entry_setup_live_policy",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "canary_mode": policy.EXPLORATION_CANARY_MODE,
        "candidate_path": str(candidate_path),
        "candidate_artifact_sha256": candidate["artifact_sha256"],
        "original_effective_date": candidate["effective_date"],
        "source_hashes": {str(path): _digest(path) for path in sources},
        "code_hashes": {path: _digest(PROJECT_ROOT / path) for path in CODE_PATHS},
        "maximum_daily_exploration_probes": maximum_daily_exploration_probes,
        "source_maximum_daily_exploration_probes": candidate["risk_contract"][
            "maximum_daily_exploration_probes"
        ],
        "daily_quota_reset_forbidden": True,
        "residual_multi_leg_forbidden": False,
        "scale_in_forbidden": False,
        "quantity_policy_owner": "position_sizing_dynamic_formula",
        "residual_policy_owner": "entry_split_order_plan",
        "scale_in_policy_owner": "scale_in_split_order_plan",
        "rollback_prompt_version": policy.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    errors = _window_errors(approval, now)
    if errors:
        raise ValueError(";".join(errors))
    approval["artifact_sha256"] = policy._canonical_sha256(approval)
    return approval


def resolve_intraday(result: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    """Called only after the existing owner/scope/probe/freshness-independent vetoes."""
    result = dict(result)
    result["status"] = "fallback_intraday_approval_invalid"
    try:
        path = Path(os.environ[PATH_ENV])
        expected_hash = os.environ[SHA_ENV]
        approval = policy._read_json(path)
        actual_hash = policy._canonical_sha256(
            {k: v for k, v in approval.items() if k != "artifact_sha256"}
        )
        errors = []
        if (
            not expected_hash
            or expected_hash != actual_hash
            or approval.get("artifact_sha256") != actual_hash
        ):
            errors.append("intraday_approval_hash_mismatch")
        if (
            approval.get("schema") != SCHEMA
            or approval.get("owner") != "entry_setup_live_policy"
            or approval.get("approval_mode") != "operator_intraday_scheduling_exception"
            or not isinstance(approval.get("operator_instruction_ref"), str)
            or not approval["operator_instruction_ref"].strip()
            or (approval.get("effective_venue"), approval.get("session_bucket"))
            != policy.DEFAULT_COHORT
            or approval.get("canary_mode") != policy.EXPLORATION_CANARY_MODE
            or approval.get("source_maximum_daily_exploration_probes")
            not in SUPPORTED_DAILY_LIMITS
            or approval.get("daily_quota_reset_forbidden") is not True
            or approval.get("residual_multi_leg_forbidden") is not False
            or approval.get("scale_in_forbidden") is not False
            or approval.get("quantity_policy_owner")
            != "position_sizing_dynamic_formula"
            or approval.get("residual_policy_owner") != "entry_split_order_plan"
            or approval.get("scale_in_policy_owner") != "scale_in_split_order_plan"
            or approval.get("runtime_effect") is not True
            or approval.get("allowed_runtime_apply") is not True
            or approval.get("actual_order_submitted") is not False
            or approval.get("broker_order_forbidden") is not True
            or approval.get("rollback_prompt_version")
            != result["selected_prompt_version"]
        ):
            errors.append("intraday_authority_contract_invalid")
        errors.extend(_window_errors(approval, now))
        errors.extend(_budget_errors(approval.get("maximum_daily_exploration_probes")))
        if errors:
            raise ValueError(";".join(errors))
        if set(approval["code_hashes"]) != set(CODE_PATHS):
            raise ValueError("intraday_code_manifest_incomplete")
        for name, digest in approval["code_hashes"].items():
            if _digest(PROJECT_ROOT / name) != digest:
                raise ValueError("intraday_code_generation_changed")
        candidate_path = Path(approval["candidate_path"])
        candidate = policy._read_json(candidate_path)
        provenance = candidate["source_provenance"]
        expected_sources = {
            str(candidate_path),
            provenance["batch_report_path"],
            provenance["detailed_report_path"],
        }
        if set(approval["source_hashes"]) != expected_sources:
            raise ValueError("intraday_source_manifest_incomplete")
        for name, digest in approval["source_hashes"].items():
            if _digest(Path(name)) != digest:
                raise ValueError("intraday_source_generation_changed")
        if (
            candidate.get("artifact_sha256") != approval["candidate_artifact_sha256"]
            or candidate.get("effective_date") != approval["original_effective_date"]
            or (candidate.get("risk_contract") or {}).get(
                "maximum_daily_exploration_probes"
            )
            != approval["source_maximum_daily_exploration_probes"]
        ):
            raise ValueError("intraday_original_candidate_changed")
        # Runtime rechecks the original contract; the full report/source gate was
        # closed by the producer and its immutable bytes remain pinned above.
        errors = policy._runtime_candidate_contract_errors(
            candidate, target_date=candidate["effective_date"]
        )
        if (
            candidate.get("canary_mode") != policy.EXPLORATION_CANARY_MODE
            or candidate.get("selected_prompt_version")
            != policy.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ):
            errors.append("intraday_requires_krx_v2_14_one_share")
        if errors:
            raise ValueError(";".join(errors))
        candidate_fields = {
            key: candidate[key]
            for key in (
                "selected_prompt_version",
                "candidate_contract_sha256",
                "entry_setup_evidence_version",
                "entry_decision_composer_version",
                "entry_structure_phase_policy_version",
                "source_date",
            )
        }
        result.update(
            enabled=True,
            status="active_bounded_krx_canary",
            runtime_effect=True,
            activation_path=str(path),
            activation_artifact_sha256=actual_hash,
            activation_mode=approval["approval_mode"],
            canary_mode=policy.EXPLORATION_CANARY_MODE,
            maximum_daily_exploration_probes=approval[
                "maximum_daily_exploration_probes"
            ],
            source_date=candidate["source_date"],
            intraday_expires_at=approval["expires_at"],
        )
        result.update(candidate_fields)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result["runtime_contract_errors"] = [str(exc)]
    return result


def write_new_approval(path: Path, approval: dict[str, Any]) -> None:
    """Exclusive creation: an existing operator receipt is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(approval, handle, sort_keys=True, ensure_ascii=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--operator-instruction-ref", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--runtime-env-file", type=Path, required=True)
    parser.add_argument("--operator-env-file", type=Path, required=True)
    parser.add_argument("--dated-operator-env-file", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--confirm")
    parser.add_argument(
        "--maximum-daily-exploration-probes",
        type=int,
        choices=SUPPORTED_DAILY_LIMITS,
        default=policy.EXPLORATION_MAX_DAILY_PROBES,
    )
    args = parser.parse_args(argv)
    if args.output and args.confirm != CONFIRM:
        parser.error("--output requires explicit --confirm " + CONFIRM)
    env, _, errors = policy.load_preopen_runtime_env(
        runtime_env_file=args.runtime_env_file,
        operator_env_file=args.operator_env_file,
        dated_operator_env_file=args.dated_operator_env_file,
    )
    try:
        if errors:
            raise ValueError(";".join(errors))
        approval = build_approval(
            candidate_path=args.candidate,
            expected_candidate_sha256=args.candidate_sha256,
            operator_instruction_ref=args.operator_instruction_ref,
            expires_at=_stamp(args.expires_at),
            now=datetime.now(policy.KST),
            runtime_env=env,
            maximum_daily_exploration_probes=args.maximum_daily_exploration_probes,
        )
        if args.output:
            write_new_approval(args.output, approval)
        print(json.dumps(approval, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(
            json.dumps(
                {"status": "blocked", "errors": [str(exc)], "runtime_effect": False}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
