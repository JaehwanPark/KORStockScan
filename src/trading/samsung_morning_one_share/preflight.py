"""Daily PREOPEN authority gate for the Samsung morning two-leg live service."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.engine.threshold_cycle_preopen_apply import verify_runtime_env_handoff
from src.trading.order.episode_quantity import EPISODE_TOTAL_QUANTITY
from src.trading.order.samsung_entry_policy import (
    effective_target_ticks,
    operator_target_override,
)
from src.trading.samsung_morning_one_share.machine import KST
from src.trading.samsung_morning_one_share.reentry import (
    DEFAULT_REENTRY_STATE_PATH,
    prior_reentry_allows_new_first_episode,
)
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.market_day import get_krx_trading_day_status

AUTHORITY_SCHEMA = "samsung_morning_two_episode_authority_v7"
DEFAULT_AUTHORITY_PATH = (
    DATA_DIR / "runtime" / "samsung_morning_one_share_authority.json"
)


def _is_bot_main_pid(pid: int, *, proc_root: Path = Path("/proc")) -> bool:
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        cmdline = (proc_root / str(pid) / "cmdline").read_bytes()
    except OSError:
        return False
    return any(
        Path(token.decode("utf-8", errors="replace")).name == "bot_main.py"
        for token in cmdline.split(b"\0")
        if token
    )


def _parse_hhmmss(value: str) -> time:
    try:
        parsed = time.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected HH:MM:SS") from exc
    if (
        len(value) != 8
        or parsed.strftime("%H:%M:%S") != value
        or parsed.tzinfo is not None
        or parsed.microsecond != 0
    ):
        raise argparse.ArgumentTypeError("expected timezone-free HH:MM:SS")
    return parsed


def _authority_deadline_elapsed(deadline: time | None, *, now: datetime) -> bool:
    if deadline is None:
        return False
    return now.astimezone(KST).time().replace(tzinfo=None) >= deadline


@dataclass(frozen=True)
class PreflightDecision:
    ready: bool
    target_date: str
    main_bot_active: bool
    main_bot_pid: int
    main_bot_runtime_env_verified: bool
    shared_token_available: bool
    operator_exclusion_source: str
    parallel_widget_trading_allowed: bool
    independent_order_ledger_required: bool
    prior_reentry_state_clear: bool
    blockers: tuple[str, ...]


def evaluate_preflight(
    *,
    target_date: date,
    main_bot_active: bool,
    main_bot_pid: int,
    main_bot_runtime_env_verified: bool,
    shared_token_available: bool,
    operator_exclusion_source: str,
    prior_reentry_state_clear: bool = True,
) -> PreflightDecision:
    blockers: list[str] = []
    if not main_bot_active:
        blockers.append("main_bot_inactive")
    if main_bot_pid <= 0:
        blockers.append("main_bot_pid_missing")
    if not main_bot_runtime_env_verified:
        blockers.append("main_bot_runtime_env_unverified")
    if not shared_token_available:
        blockers.append("shared_token_unavailable")
    if not operator_exclusion_source:
        blockers.append("manual_operator_exclusion_missing")
    if not prior_reentry_state_clear:
        blockers.append("prior_reentry_order_or_position_unresolved")
    return PreflightDecision(
        ready=not blockers,
        target_date=target_date.isoformat(),
        main_bot_active=bool(main_bot_active),
        main_bot_pid=max(0, int(main_bot_pid)),
        main_bot_runtime_env_verified=bool(main_bot_runtime_env_verified),
        shared_token_available=bool(shared_token_available),
        operator_exclusion_source=str(operator_exclusion_source or ""),
        parallel_widget_trading_allowed=True,
        independent_order_ledger_required=True,
        prior_reentry_state_clear=bool(prior_reentry_state_clear),
        blockers=tuple(blockers),
    )


def build_authority_artifact(
    decision: PreflightDecision, *, observed_at: datetime
) -> dict:
    if not decision.ready:
        raise ValueError("preflight_not_ready")
    if observed_at.tzinfo is None:
        raise ValueError("preflight_observed_at_timezone_missing")
    observed_at = observed_at.astimezone(KST)
    target_date = date.fromisoformat(decision.target_date)
    if observed_at.date() != target_date:
        raise ValueError("preflight_target_date_not_observed_date")
    target_ticks = effective_target_ticks(
        "morning", target_date=target_date, as_of=observed_at
    )
    target_override = operator_target_override(
        target_date=target_date, as_of=observed_at
    )
    return {
        "schema": AUTHORITY_SCHEMA,
        "status": "ready",
        "target_date": decision.target_date,
        "observed_at_kst": observed_at.isoformat(),
        "valid_until_kst": datetime.combine(
            date.fromisoformat(decision.target_date), time(23, 59, 59), tzinfo=KST
        ).isoformat(),
        "decision": asdict(decision),
        "policy": {
            "symbol": "005930",
            "quantity": EPISODE_TOTAL_QUANTITY,
            "allocation": "ten_shares_base_limit_and_ten_shares_base_plus_1tick",
            "nxt_entry": "two_independent_10share_legs_from_08:00_open_until_08:10",
            "sor_regular_fallback": "each_unfilled_leg_from_09:00_open_until_09:30",
            "target": f"fill_plus_{target_ticks}_ticks",
            "operator_target_override": target_override,
            "unfilled_target": "hold_position_without_forced_exit",
            "entry_tuning": "preopen_exact_date_bounded_policy_artifact",
            "entry_tuning_bounds": "morning_baseline_only_until_observed_alternative",
            "maximum_episodes_per_day": 2,
            "sor_reentry_prerequisite": "both_opening_episode_legs_complete",
            "sor_reentry_signal": (
                "lookback15_drawdown0p75_nearlow0p35_lowhold2_reclaim1tick_until1000"
            ),
            "sor_reentry_allocation": "confirmation_close_minus_1tick_and_minus_2ticks",
            "sor_reentry_validity": "three_completed_bars",
            "sor_reentry_research_sha256": (
                "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
            ),
            "widget_relationship": "parallel_independent_strategy",
        },
        "metric_role": "operator_preopen_runtime_authority_gate",
        "decision_authority": "explicit_user_directed_morning_two_episode_live_start",
        "window_policy": "target_date_opening_episode_then_at_most_one_sor_reentry",
        "sample_floor": "not_applicable_operator_runtime_gate",
        "primary_decision_metric": "all_preopen_safety_contracts_ready",
        "source_quality_gate": "PASS",
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "rollback": {
            "trigger": (
                "any ambiguous two-leg broker write, unresolved prior entry "
                "order or ambiguous position state, source failure, or two-leg "
                "contract breach"
            ),
            "action": "fail_closed_and_disable_only_morning_two_leg_timer_and_services",
            "widget_service_effect": "none",
        },
        "forbidden_uses": [
            "quantity_above_twenty_or_leg_quantity_above_ten",
            "hard_safety_or_global_buy_pause_bypass",
            "provider_or_main_bot_policy_change",
            "use_for_other_symbol_or_strategy",
            "use_widget_orders_or_positions_as_morning_machine_ledger",
            "cancel_or_sell_widget_owned_orders_or_quantity",
            "timeout_target_cancel_or_forced_exit",
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
    path: Path = DEFAULT_AUTHORITY_PATH,
    *,
    now: datetime | None = None,
    require_live_main_bot_runtime: bool = False,
) -> tuple[bool, str]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"authority_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict) or payload.get("schema") != AUTHORITY_SCHEMA:
        return False, "authority_schema_invalid"
    if payload.get("status") != "ready":
        return False, "authority_not_ready"
    if (
        payload.get("decision_authority")
        != "explicit_user_directed_morning_two_episode_live_start"
        or payload.get("source_quality_gate") != "PASS"
        or payload.get("runtime_effect") is not True
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not False
    ):
        return False, "authority_runtime_contract_mismatch"
    if payload.get("target_date") != now.date().isoformat():
        return False, "authority_target_date_mismatch"
    try:
        observed_at = datetime.fromisoformat(str(payload.get("observed_at_kst") or ""))
    except ValueError:
        return False, "authority_observed_at_invalid"
    if observed_at.tzinfo is None:
        return False, "authority_observed_at_invalid"
    observed_at = observed_at.astimezone(KST)
    if observed_at.date().isoformat() != payload.get("target_date"):
        return False, "authority_observed_target_date_mismatch"
    if observed_at > now:
        return False, "authority_observed_in_future"
    try:
        valid_until = datetime.fromisoformat(str(payload.get("valid_until_kst") or ""))
    except ValueError:
        return False, "authority_expiry_invalid"
    if valid_until.tzinfo is None or now > valid_until.astimezone(KST):
        return False, "authority_expired"
    decision = payload.get("decision")
    if not isinstance(decision, dict) or decision.get("ready") is not True:
        return False, "authority_decision_invalid"
    if decision.get("target_date") != payload.get("target_date"):
        return False, "authority_decision_target_date_mismatch"
    if decision.get("main_bot_active") is not True:
        return False, "authority_main_bot_inactive"
    if decision.get("shared_token_available") is not True:
        return False, "authority_shared_token_unavailable"
    if not str(decision.get("operator_exclusion_source") or "").strip():
        return False, "authority_manual_operator_exclusion_missing"
    if decision.get("blockers") != []:
        return False, "authority_decision_blockers_present"
    if decision.get("parallel_widget_trading_allowed") is not True:
        return False, "authority_parallel_widget_contract_missing"
    if decision.get("independent_order_ledger_required") is not True:
        return False, "authority_independent_ledger_contract_missing"
    if decision.get("prior_reentry_state_clear") is not True:
        return False, "authority_prior_reentry_state_not_clear"
    main_bot_pid = decision.get("main_bot_pid")
    if (
        isinstance(main_bot_pid, bool)
        or not isinstance(main_bot_pid, int)
        or main_bot_pid <= 0
    ):
        return False, "authority_main_bot_pid_missing"
    if decision.get("main_bot_runtime_env_verified") is not True:
        return False, "authority_main_bot_runtime_env_unverified"
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        return False, "authority_policy_missing"
    if "max_hold_minutes" in policy:
        return False, "authority_timeout_policy_forbidden"
    if policy.get("unfilled_target") != "hold_position_without_forced_exit":
        return False, "authority_hold_policy_mismatch"
    target_ticks = effective_target_ticks("morning", target_date=now.date(), as_of=now)
    target_override = operator_target_override(target_date=now.date(), as_of=now)
    expected = {
        "symbol": "005930",
        "quantity": EPISODE_TOTAL_QUANTITY,
        "allocation": "ten_shares_base_limit_and_ten_shares_base_plus_1tick",
        "nxt_entry": "two_independent_10share_legs_from_08:00_open_until_08:10",
        "sor_regular_fallback": "each_unfilled_leg_from_09:00_open_until_09:30",
        "target": f"fill_plus_{target_ticks}_ticks",
        "operator_target_override": target_override,
        "widget_relationship": "parallel_independent_strategy",
        "entry_tuning": "preopen_exact_date_bounded_policy_artifact",
        "entry_tuning_bounds": "morning_baseline_only_until_observed_alternative",
        "maximum_episodes_per_day": 2,
        "sor_reentry_prerequisite": "both_opening_episode_legs_complete",
        "sor_reentry_signal": (
            "lookback15_drawdown0p75_nearlow0p35_lowhold2_reclaim1tick_until1000"
        ),
        "sor_reentry_allocation": "confirmation_close_minus_1tick_and_minus_2ticks",
        "sor_reentry_validity": "three_completed_bars",
        "sor_reentry_research_sha256": (
            "6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a"
        ),
    }
    if any(policy.get(key) != value for key, value in expected.items()):
        return False, "authority_sor_policy_mismatch"
    rollback = payload.get("rollback")
    if (
        not isinstance(rollback, dict)
        or rollback.get("action")
        != "fail_closed_and_disable_only_morning_two_leg_timer_and_services"
        or rollback.get("widget_service_effect") != "none"
    ):
        return False, "authority_rollback_contract_mismatch"
    if require_live_main_bot_runtime:
        if not _is_bot_main_pid(main_bot_pid):
            return False, "authority_main_bot_inactive"
        runtime_verification = verify_runtime_env_handoff(
            str(payload.get("target_date") or ""), pid=main_bot_pid
        )
        if (
            runtime_verification.get("status") != "pass"
            or runtime_verification.get("pid") != main_bot_pid
        ):
            return False, "authority_main_bot_runtime_env_unverified"
    return True, "ready"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--authority-path", type=Path, default=DEFAULT_AUTHORITY_PATH)
    parser.add_argument("--main-bot-active", action="store_true")
    parser.add_argument("--main-bot-pid", type=int, default=0)
    parser.add_argument(
        "--authority-deadline-hhmmss",
        type=_parse_hhmmss,
        default=None,
        help="Fail closed if authority publication reaches this KST deadline.",
    )
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    observed_at = datetime.now(tz=KST)
    target_date = (
        date.fromisoformat(args.target_date) if args.target_date else observed_at.date()
    )
    if target_date != observed_at.date():
        print(
            json.dumps(
                {
                    "decision": {
                        "ready": False,
                        "target_date": target_date.isoformat(),
                        "blockers": ["target_date_not_observed_date"],
                    },
                    "authority_path": str(args.authority_path),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    if _authority_deadline_elapsed(
        args.authority_deadline_hhmmss,
        now=observed_at,
    ):
        print(
            json.dumps(
                {
                    "decision": {
                        "ready": False,
                        "target_date": target_date.isoformat(),
                        "blockers": ["authority_creation_deadline_elapsed"],
                    },
                    "authority_path": str(args.authority_path),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    trading_day, trading_day_reason = get_krx_trading_day_status(target_date)
    if not trading_day:
        print(
            json.dumps(
                {
                    "decision": {
                        "ready": False,
                        "target_date": target_date.isoformat(),
                        "blockers": ["target_date_not_krx_trading_day"],
                    },
                    "authority_path": str(args.authority_path),
                    "trading_day_reason": trading_day_reason,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    prior_reentry_clear, prior_reentry_reason = prior_reentry_allows_new_first_episode(
        DEFAULT_REENTRY_STATE_PATH, target_date=target_date
    )
    main_bot_active = bool(args.main_bot_active and _is_bot_main_pid(args.main_bot_pid))
    runtime_env_verification = {"status": "not_checked", "pid": args.main_bot_pid}
    if main_bot_active:
        runtime_env_verification = verify_runtime_env_handoff(
            target_date.isoformat(), pid=args.main_bot_pid
        )
    runtime_env_verified = bool(
        runtime_env_verification.get("status") == "pass"
        and runtime_env_verification.get("pid") == args.main_bot_pid
    )
    decision = evaluate_preflight(
        target_date=target_date,
        main_bot_active=main_bot_active,
        main_bot_pid=args.main_bot_pid,
        main_bot_runtime_env_verified=runtime_env_verified,
        shared_token_available=bool(kiwoom_utils.get_cached_kiwoom_token()),
        operator_exclusion_source=manual_control_operator_exclusion_source("005930"),
        prior_reentry_state_clear=prior_reentry_clear,
    )
    output = {
        "decision": asdict(decision),
        "authority_path": str(args.authority_path),
        "prior_reentry_state_reason": prior_reentry_reason,
        "main_bot_identity_verified": main_bot_active,
        "main_bot_runtime_env_verification": runtime_env_verification,
    }
    if decision.ready and args.write:
        if _authority_deadline_elapsed(
            args.authority_deadline_hhmmss,
            now=datetime.now(tz=KST),
        ):
            output["decision"]["ready"] = False
            output["decision"]["blockers"] = ["authority_creation_deadline_elapsed"]
            print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        artifact = build_authority_artifact(decision, observed_at=observed_at)
        _atomic_write(args.authority_path, artifact)
        output["artifact"] = artifact
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
