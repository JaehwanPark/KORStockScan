"""Same-day authority gate for one selected lower-price two-leg profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.low_price_two_leg.profiles import PROFILES, MachineProfile, get_profile
from src.trading.low_price_two_leg.policy_runtime import load_applied_profile_policy
from src.trading.order.regular_two_leg_machine import KST
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

AUTHORITY_SCHEMA = "low_price_two_leg_authority_v1"
RESEARCH_REPORT_PATH = (
    DATA_DIR
    / "report"
    / "samsung_like_machine_candidate_scan_low_price"
    / "samsung_like_machine_candidate_scan_2026-08-10.json"
)
RESEARCH_REPORT_SHA256 = (
    "4ec41693eb70c6cf3fd148d4104fac78c7278fc87e60b5ac9e16619d92fb504f"
)


def default_authority_path(profile: MachineProfile) -> Path:
    return (
        DATA_DIR
        / "runtime"
        / "low_price_two_leg"
        / f"{profile.profile_id}_authority.json"
    )


@dataclass(frozen=True)
class PreflightDecision:
    ready: bool
    target_date: str
    profile_id: str
    symbol: str
    session: str
    main_bot_active: bool
    shared_token_available: bool
    operator_exclusion_source: str
    research_evidence_ready: bool
    applied_policy_ready: bool
    applied_policy_hash: str
    independent_order_ledger_required: bool
    blockers: tuple[str, ...]


def validate_research_evidence(
    profile: MachineProfile,
    path: Path = RESEARCH_REPORT_PATH,
    *,
    expected_sha256: str = RESEARCH_REPORT_SHA256,
) -> tuple[bool, str]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"research_report_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict):
        return False, "research_report_contract_invalid"
    canonical_payload = dict(payload)
    embedded_sha256 = str(canonical_payload.pop("report_sha256", ""))
    canonical_sha256 = hashlib.sha256(
        json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()
    if (
        payload.get("schema") != "samsung_like_machine_candidate_scan_v1"
        or payload.get("start_date") != "2026-06-05"
        or payload.get("end_date") != "2026-08-10"
        or embedded_sha256 != expected_sha256
        or canonical_sha256 != expected_sha256
        or payload.get("runtime_effect") is not False
        or payload.get("actual_order_submitted") is not False
    ):
        return False, "research_report_provenance_invalid"
    symbol = (payload.get("symbols") or {}).get(profile.symbol)
    machine = (symbol or {}).get("machines", {}).get(profile.session)
    if not isinstance(machine, dict):
        return False, "research_profile_result_missing"
    if (
        machine.get("source_quality_ready") is not True
        or int(machine.get("coverage_days", 0) or 0) < 46
        or int(machine.get("completed_legs", 0) or 0) < 10
        or int(machine.get("held_legs", 0) or 0) != 0
        or float(machine.get("notional_weighted_realized_ev_pct", 0.0) or 0.0) <= 0.0
        or machine.get("status") != "implementation_candidate_source_only"
    ):
        return False, "research_profile_result_not_eligible"
    return True, "ready"


def evaluate_preflight(
    *,
    target_date: date,
    profile: MachineProfile,
    main_bot_active: bool,
    shared_token_available: bool,
    operator_exclusion_source: str,
    research_evidence_ready: bool,
    applied_policy_ready: bool,
    applied_policy_hash: str,
) -> PreflightDecision:
    blockers: list[str] = []
    if not main_bot_active:
        blockers.append("main_bot_inactive")
    if not shared_token_available:
        blockers.append("shared_token_unavailable")
    if not operator_exclusion_source:
        blockers.append("manual_operator_exclusion_missing")
    if not research_evidence_ready:
        blockers.append("research_evidence_invalid")
    if not applied_policy_ready or not applied_policy_hash:
        blockers.append("exact_date_applied_policy_invalid")
    return PreflightDecision(
        not blockers,
        target_date.isoformat(),
        profile.profile_id,
        profile.symbol,
        profile.session,
        bool(main_bot_active),
        bool(shared_token_available),
        str(operator_exclusion_source or ""),
        bool(research_evidence_ready),
        bool(applied_policy_ready),
        str(applied_policy_hash or ""),
        True,
        tuple(blockers),
    )


def _policy_contract(
    profile: MachineProfile,
    applied_policy: dict,
    applied_policy_hash: str,
) -> dict:
    policy = profile.policy
    return {
        "profile_id": profile.profile_id,
        "symbol": profile.symbol,
        "name": profile.name,
        "session": profile.session,
        "quantity": 2,
        "allocation": "one_share_signal_close_and_one_share_minus_1tick",
        "market": "SOR_regular_integrated",
        "scan_start": policy.scan_start.isoformat(),
        "scan_last_bar": policy.scan_last_bar.isoformat(),
        "lookback_bars": int(applied_policy["lookback_bars"]),
        "rolling_high_drawdown_pct": float(applied_policy["rolling_high_drawdown_pct"]),
        "rolling_low_proximity_pct": float(applied_policy["rolling_low_proximity_pct"]),
        "entry_valid_completed_bars": int(applied_policy["entry_valid_completed_bars"]),
        "target_ticks": int(applied_policy["target_ticks"]),
        "applied_policy_hash": applied_policy_hash,
        "stop_loss": "none",
        "unfilled_target": "hold_position_without_forced_exit",
        "relationship": "parallel_independent_strategy_and_order_ledger",
    }


def build_authority_artifact(
    decision: PreflightDecision,
    *,
    profile: MachineProfile,
    applied_policy: dict,
    applied_policy_hash: str,
    observed_at: datetime,
) -> dict:
    if not decision.ready:
        raise ValueError("preflight_not_ready")
    observed_at = observed_at.astimezone(KST)
    return {
        "schema": AUTHORITY_SCHEMA,
        "status": "ready",
        "target_date": decision.target_date,
        "observed_at_kst": observed_at.isoformat(),
        "valid_until_kst": datetime.combine(
            date.fromisoformat(decision.target_date), time(23, 59, 59), tzinfo=KST
        ).isoformat(),
        "decision": asdict(decision),
        "policy": _policy_contract(profile, applied_policy, applied_policy_hash),
        "evidence": {
            "path": str(RESEARCH_REPORT_PATH),
            "report_sha256": RESEARCH_REPORT_SHA256,
            "window": "2026-06-05_through_2026-08-10_46_trading_days",
            "cost_pct": 0.20,
        },
        "metric_role": "operator_runtime_authority_gate",
        "decision_authority": "explicit_user_directed_low_price_two_leg_live_implementation",
        "window_policy": "target_date_profile_once_then_terminal_or_held",
        "sample_floor": "explicit_user_selected_clean_baseline_46_day_source_replay",
        "primary_decision_metric": "runtime_contract_and_profile_evidence_ready",
        "source_quality_gate": "PASS",
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "rollback": {
            "trigger": "ambiguous broker write, unresolved owned order or position, source contract failure, or two-leg contract breach",
            "action": f"fail_closed_and_disable_only_{profile.profile_id}",
            "other_machine_effect": "none",
        },
        "forbidden_uses": [
            "quantity_above_two_or_leg_quantity_above_one",
            "non_sor_regular_route",
            "hard_safety_or_global_buy_pause_bypass",
            "use_other_machine_orders_or_positions_as_this_profile_ledger",
            "cancel_or_sell_other_machine_owned_orders_or_quantity",
            "target_timeout_cancel",
            "forced_exit_or_stop_loss",
            "symbol_or_session_not_in_immutable_profile_allowlist",
        ],
    }


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o640)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def validate_authority(
    *,
    profile: MachineProfile,
    path: Path | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    authority_path = Path(path or default_authority_path(profile))
    try:
        payload = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"authority_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict) or payload.get("schema") != AUTHORITY_SCHEMA:
        return False, "authority_schema_invalid"
    if (
        payload.get("status") != "ready"
        or payload.get("target_date") != now.date().isoformat()
    ):
        return False, "authority_not_ready_or_target_date_mismatch"
    try:
        valid_until = datetime.fromisoformat(str(payload.get("valid_until_kst") or ""))
    except ValueError:
        return False, "authority_expiry_invalid"
    if valid_until.tzinfo is None or now > valid_until.astimezone(KST):
        return False, "authority_expired"
    decision = payload.get("decision")
    if (
        not isinstance(decision, dict)
        or decision.get("ready") is not True
        or decision.get("profile_id") != profile.profile_id
        or decision.get("symbol") != profile.symbol
        or decision.get("session") != profile.session
        or decision.get("independent_order_ledger_required") is not True
        or decision.get("research_evidence_ready") is not True
        or decision.get("applied_policy_ready") is not True
        or not decision.get("applied_policy_hash")
        or not decision.get("operator_exclusion_source")
    ):
        return False, "authority_decision_contract_invalid"
    applied_policy, applied_hash, applied_reason = load_applied_profile_policy(
        profile.profile_id, target_date=now.date()
    )
    if applied_policy is None:
        return False, f"authority_applied_policy_{applied_reason}"
    if payload.get("policy") != _policy_contract(profile, applied_policy, applied_hash):
        return False, "authority_policy_mismatch"
    evidence = payload.get("evidence")
    if (
        not isinstance(evidence, dict)
        or evidence.get("report_sha256") != RESEARCH_REPORT_SHA256
    ):
        return False, "authority_evidence_mismatch"
    if any(
        key in payload.get("policy", {})
        for key in ("max_hold_minutes", "target_timeout", "stop_price")
    ):
        return False, "authority_forced_exit_policy_forbidden"
    evidence_ready, evidence_reason = validate_research_evidence(profile)
    if not evidence_ready:
        return False, f"authority_research_evidence_{evidence_reason}"
    return True, "ready"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--authority-path", type=Path, default=None)
    parser.add_argument("--main-bot-active", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    profile = get_profile(args.profile)
    observed_at = datetime.now(tz=KST)
    target_date = (
        date.fromisoformat(args.target_date) if args.target_date else observed_at.date()
    )
    evidence_ready, evidence_reason = validate_research_evidence(profile)
    applied_policy, applied_hash, applied_reason = load_applied_profile_policy(
        profile.profile_id, target_date=target_date
    )
    decision = evaluate_preflight(
        target_date=target_date,
        profile=profile,
        main_bot_active=args.main_bot_active,
        shared_token_available=bool(kiwoom_utils.get_cached_kiwoom_token()),
        operator_exclusion_source=manual_control_operator_exclusion_source(
            profile.symbol
        ),
        research_evidence_ready=evidence_ready,
        applied_policy_ready=applied_policy is not None,
        applied_policy_hash=applied_hash,
    )
    authority_path = args.authority_path or default_authority_path(profile)
    output = {
        "decision": asdict(decision),
        "evidence_reason": evidence_reason,
        "applied_policy_reason": applied_reason,
        "authority_path": str(authority_path),
    }
    if decision.ready and args.write:
        if applied_policy is None:
            raise RuntimeError("ready_preflight_missing_applied_policy")
        output["artifact"] = build_authority_artifact(
            decision,
            profile=profile,
            applied_policy=applied_policy,
            applied_policy_hash=applied_hash,
            observed_at=observed_at,
        )
        _atomic_write(authority_path, output["artifact"])
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
