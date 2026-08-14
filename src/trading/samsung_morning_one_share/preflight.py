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

AUTHORITY_SCHEMA = "samsung_morning_two_episode_authority_v6"
DEFAULT_AUTHORITY_PATH = (
    DATA_DIR / "runtime" / "samsung_morning_one_share_authority.json"
)


@dataclass(frozen=True)
class PreflightDecision:
    ready: bool
    target_date: str
    main_bot_active: bool
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
    shared_token_available: bool,
    operator_exclusion_source: str,
    prior_reentry_state_clear: bool = True,
) -> PreflightDecision:
    blockers: list[str] = []
    if not main_bot_active:
        blockers.append("main_bot_inactive")
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
    observed_at = observed_at.astimezone(KST)
    target_date = date.fromisoformat(decision.target_date)
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
            "action": "fail_closed_and_disable_only_morning_two_leg_timers_and_service",
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
    path: Path = DEFAULT_AUTHORITY_PATH, *, now: datetime | None = None
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
    if payload.get("target_date") != now.date().isoformat():
        return False, "authority_target_date_mismatch"
    try:
        valid_until = datetime.fromisoformat(str(payload.get("valid_until_kst") or ""))
    except ValueError:
        return False, "authority_expiry_invalid"
    if valid_until.tzinfo is None or now > valid_until.astimezone(KST):
        return False, "authority_expired"
    decision = payload.get("decision")
    if not isinstance(decision, dict) or decision.get("ready") is not True:
        return False, "authority_decision_invalid"
    if decision.get("parallel_widget_trading_allowed") is not True:
        return False, "authority_parallel_widget_contract_missing"
    if decision.get("independent_order_ledger_required") is not True:
        return False, "authority_independent_ledger_contract_missing"
    if decision.get("prior_reentry_state_clear") is not True:
        return False, "authority_prior_reentry_state_not_clear"
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
    return True, "ready"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--authority-path", type=Path, default=DEFAULT_AUTHORITY_PATH)
    parser.add_argument("--main-bot-active", action="store_true")
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    observed_at = datetime.now(tz=KST)
    target_date = (
        date.fromisoformat(args.target_date) if args.target_date else observed_at.date()
    )
    prior_reentry_clear, prior_reentry_reason = prior_reentry_allows_new_first_episode(
        DEFAULT_REENTRY_STATE_PATH, target_date=target_date
    )
    decision = evaluate_preflight(
        target_date=target_date,
        main_bot_active=args.main_bot_active,
        shared_token_available=bool(kiwoom_utils.get_cached_kiwoom_token()),
        operator_exclusion_source=manual_control_operator_exclusion_source("005930"),
        prior_reentry_state_clear=prior_reentry_clear,
    )
    output = {
        "decision": asdict(decision),
        "authority_path": str(args.authority_path),
        "prior_reentry_state_reason": prior_reentry_reason,
    }
    if decision.ready and args.write:
        artifact = build_authority_artifact(decision, observed_at=observed_at)
        _atomic_write(args.authority_path, artifact)
        output["artifact"] = artifact
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
