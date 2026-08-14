"""Same-day authority gate for the Samsung midday two-leg live service."""

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
from src.trading.samsung_midday_one_share.machine import KST
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

AUTHORITY_SCHEMA = "samsung_midday_two_leg_authority_v4"
DEFAULT_AUTHORITY_PATH = (
    DATA_DIR / "runtime" / "samsung_midday_one_share_authority.json"
)


@dataclass(frozen=True)
class PreflightDecision:
    ready: bool
    target_date: str
    main_bot_active: bool
    shared_token_available: bool
    operator_exclusion_source: str
    morning_parallel_independent: bool
    afternoon_parallel_independent: bool
    widget_parallel_independent: bool
    independent_order_ledger_required: bool
    blockers: tuple[str, ...]


def evaluate_preflight(
    *,
    target_date: date,
    main_bot_active: bool,
    shared_token_available: bool,
    operator_exclusion_source: str,
) -> PreflightDecision:
    blockers: list[str] = []
    if not main_bot_active:
        blockers.append("main_bot_inactive")
    if not shared_token_available:
        blockers.append("shared_token_unavailable")
    if not operator_exclusion_source:
        blockers.append("manual_operator_exclusion_missing")
    return PreflightDecision(
        not blockers,
        target_date.isoformat(),
        bool(main_bot_active),
        bool(shared_token_available),
        str(operator_exclusion_source or ""),
        True,
        True,
        True,
        True,
        tuple(blockers),
    )


def build_authority_artifact(
    decision: PreflightDecision, *, observed_at: datetime
) -> dict:
    if not decision.ready:
        raise ValueError("preflight_not_ready")
    observed_at = observed_at.astimezone(KST)
    target_date = date.fromisoformat(decision.target_date)
    target_ticks = effective_target_ticks(
        "midday", target_date=target_date, as_of=observed_at
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
            "allocation": "ten_shares_signal_close_and_ten_shares_minus_1tick",
            "market": "SOR_regular_integrated",
            "scan": "completed_1m_bars_13:15_through_13:54_13:55_exclusive",
            "signal": "30bar_high_drawdown_gte_1.25pct_and_low_proximity_lte_0.20pct",
            "entry": "two_independent_10share_legs_valid_for_next_5_completed_bars",
            "target": f"fill_plus_{target_ticks}_ticks",
            "operator_target_override": target_override,
            "stop_loss": "none",
            "unfilled_target": "hold_position_without_forced_exit",
            "entry_tuning": "preopen_exact_date_bounded_policy_artifact",
            "entry_tuning_bounds": "drawdown_1.25_to_1.50_near_low_0.20_to_0.10_tightening_only",
            "morning_relationship": "parallel_independent_strategy",
            "afternoon_relationship": "parallel_independent_strategy",
            "widget_relationship": "parallel_independent_strategy",
        },
        "metric_role": "operator_runtime_authority_gate",
        "decision_authority": "explicit_user_directed_midday_two_leg_live_start",
        "window_policy": "target_date_midday_once_then_terminal_or_held",
        "sample_floor": "research_46_days_below_60_day_promotion_floor",
        "primary_decision_metric": "all_runtime_safety_contracts_ready",
        "source_quality_gate": "PASS",
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "rollback": {
            "trigger": "ambiguous broker write, unresolved owned order or position, source contract failure, or two-leg contract breach",
            "action": "fail_closed_and_disable_only_midday_machine",
            "morning_service_effect": "none",
            "afternoon_service_effect": "none",
            "widget_service_effect": "none",
        },
        "forbidden_uses": [
            "quantity_above_twenty_or_leg_quantity_above_ten",
            "non_sor_regular_route",
            "hard_safety_or_global_buy_pause_bypass",
            "use_other_machine_orders_or_positions_as_midday_ledger",
            "cancel_or_sell_other_machine_owned_orders_or_quantity",
            "target_timeout_cancel",
            "forced_exit_or_stop_loss",
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
    decision, policy = payload.get("decision"), payload.get("policy")
    if (
        not isinstance(decision, dict)
        or decision.get("ready") is not True
        or decision.get("morning_parallel_independent") is not True
        or decision.get("afternoon_parallel_independent") is not True
        or decision.get("widget_parallel_independent") is not True
        or decision.get("independent_order_ledger_required") is not True
    ):
        return False, "authority_independence_contract_invalid"
    target_ticks = effective_target_ticks("midday", target_date=now.date(), as_of=now)
    expected = {
        "symbol": "005930",
        "quantity": EPISODE_TOTAL_QUANTITY,
        "allocation": "ten_shares_signal_close_and_ten_shares_minus_1tick",
        "market": "SOR_regular_integrated",
        "scan": "completed_1m_bars_13:15_through_13:54_13:55_exclusive",
        "signal": "30bar_high_drawdown_gte_1.25pct_and_low_proximity_lte_0.20pct",
        "entry": "two_independent_10share_legs_valid_for_next_5_completed_bars",
        "target": f"fill_plus_{target_ticks}_ticks",
        "operator_target_override": operator_target_override(
            target_date=now.date(), as_of=now
        ),
        "stop_loss": "none",
        "unfilled_target": "hold_position_without_forced_exit",
        "morning_relationship": "parallel_independent_strategy",
        "afternoon_relationship": "parallel_independent_strategy",
        "widget_relationship": "parallel_independent_strategy",
        "entry_tuning": "preopen_exact_date_bounded_policy_artifact",
        "entry_tuning_bounds": "drawdown_1.25_to_1.50_near_low_0.20_to_0.10_tightening_only",
    }
    if not isinstance(policy, dict) or any(
        policy.get(key) != value for key, value in expected.items()
    ):
        return False, "authority_policy_mismatch"
    if any(
        key in policy for key in ("max_hold_minutes", "target_timeout", "stop_price")
    ):
        return False, "authority_forced_exit_policy_forbidden"
    return True, "ready"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--authority-path", type=Path, default=DEFAULT_AUTHORITY_PATH)
    parser.add_argument("--main-bot-active", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    observed_at = datetime.now(tz=KST)
    target_date = (
        date.fromisoformat(args.target_date) if args.target_date else observed_at.date()
    )
    decision = evaluate_preflight(
        target_date=target_date,
        main_bot_active=args.main_bot_active,
        shared_token_available=bool(kiwoom_utils.get_cached_kiwoom_token()),
        operator_exclusion_source=manual_control_operator_exclusion_source("005930"),
    )
    output = {"decision": asdict(decision), "authority_path": str(args.authority_path)}
    if decision.ready and args.write:
        output["artifact"] = build_authority_artifact(decision, observed_at=observed_at)
        _atomic_write(args.authority_path, output["artifact"])
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
