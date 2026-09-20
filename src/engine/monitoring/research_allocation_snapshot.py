"""Read-only projections of already acquired native capacity and custody facts.

No account call, balance refresh, quantity, cap, or ownership mutation is made
here. The cash-only research bound is not a live portfolio risk limit.
"""

from __future__ import annotations

import math
from datetime import datetime, date
from zoneinfo import ZoneInfo

from src.engine.monitoring import research_closed_loop as loop
from src.trading.config.symbol_owner_policy import policy_path

KST = ZoneInfo("Asia/Seoul")


def publish_cash_context(context, *, directory=loop.DIRECTORY):
    if context.get("kt00011_cash_orderable_contract_status") != "valid" or context.get(
        "kt00011_error"
    ):
        return False
    at = datetime.fromisoformat(context["kt00011_capacity_observed_at"])
    if (
        at.tzinfo is None
        or len(str(context.get("kt00011_capacity_source_sha256") or "")) != 64
    ):
        return False
    import os

    fields = {
        key: context.get(key)
        for key in (
            "account_deposit",
            "cash_orderable_amount",
            "cash_orderable_qty_cap",
            "kt00011_requested_stock_code",
            "kt00011_capacity_source_sha256",
            "kt00011_capacity_contract_version",
        )
    }
    if any(
        type(fields.get(key)) is not int or fields[key] < 0
        for key in (
            "account_deposit",
            "cash_orderable_amount",
            "cash_orderable_qty_cap",
        )
    ):
        return False
    body = dict(
        schema=loop.SCHEMA,
        source_date=at.astimezone(KST).date().isoformat(),
        captured_at=at.isoformat(),
        producer_pid=os.getpid(),
        cash_context=fields,
        additional_account_requests=0,
        **loop.AUTHORITY,
    )
    loop.atomic_write(
        directory / "native_cash.json", {**body, "native_sha256": loop.digest(body)}
    )
    return True


def publish_inventory_context(snapshot, *, directory=loop.DIRECTORY):
    import os

    at = datetime.fromtimestamp(snapshot["captured_at"], tz=KST)
    body = dict(
        schema=loop.SCHEMA,
        source_date=at.date().isoformat(),
        captured_at=at.isoformat(),
        producer_pid=os.getpid(),
        successful_exchanges=sorted(snapshot["successful_exchanges"]),
        inventory_by_code=snapshot["inventory_by_code"],
        open_qty_by_code=snapshot["open_qty_by_code"],
        open_orders_request_succeeded=snapshot["open_orders_request_succeeded"],
        additional_account_requests=0,
        **loop.AUTHORITY,
    )
    loop.atomic_write(
        directory / "native_inventory.json",
        {**body, "native_sha256": loop.digest(body)},
    )
    return True


def native_allocator_contract(
    source_date,
    *,
    cash,
    inventory,
    owner,
    holding,
    available,
    directory,
    report_root=None,
):
    """Project the fixed machine funding rule and existing stage veto.

    The native account funding bound is not a new live portfolio risk limit.
    Native broker, custody and per-order checks remain with their order owners.
    """
    from src.utils.constants import DATA_DIR
    from src.trading.order.episode_quantity import (
        EPISODE_LEG_QUANTITY,
        new_entry_quantity,
    )
    from pathlib import Path
    from datetime import time

    root = Path(report_root or DATA_DIR / "report")
    path = (
        root
        / "machine_entry_timing_tuning"
        / f"machine_entry_timing_tuning_{source_date}.json"
    )
    stage = loop.read_object(path, limit=32 * 1024 * 1024)
    guard = stage.get("same_stage_owner_guard") or {}
    if (
        str(stage.get("target_date")) != str(source_date)
        or guard.get("mutation_present") is not False
        or guard.get("status") != "clear"
        or stage.get("runtime_effect") is not False
        or new_entry_quantity(
            datetime.combine(
                date.fromisoformat(loop.trading_dates_after(source_date, 1)[0]),
                time(9),
                KST,
            )
        )
        != EPISODE_LEG_QUANTITY
    ):
        raise ValueError("native_stage_or_quantity_contract_not_clear")
    from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract

    cost = comparison_cost_contract(source_date)
    if cost.get("buy_fee_bps") is None:
        raise ValueError("entry_fee_allocation_contract_missing")
    body = dict(
        source_date=str(source_date),
        source_quality_status="PASS",
        native_cash_sha256=cash["native_sha256"],
        native_inventory_sha256=inventory["native_sha256"],
        owner_contract_sha256=loop.digest(owner),
        owner_conflict=False,
        blocked_symbols=sorted(
            {
                symbol
                for symbol, row in owner["symbols"].items()
                if row.get("mode") in {"EXCLUSIVE_MANUAL", "COEXIST_EXIT_ONLY"}
            }
            | {
                symbol
                for symbol, row in inventory["inventory_by_code"].items()
                if row.get("qty", 0) > 0 and symbol not in owner["symbols"]
            }
        ),
        same_stage_clear=True,
        same_stage_source_sha256=loop.digest(stage),
        same_stage_source_path=str(path.resolve()),
        cooldown_contract_status="verified_native_family_policy",
        venue_session_contract="KRX/KRX_REGULAR",
        per_leg_quantity=EPISODE_LEG_QUANTITY,
        buy_fee_bps=cost["buy_fee_bps"],
        cost_contract_sha256=cost["contract_sha256"],
        exposure_limit_krw=available + holding,
        exposure_policy="native_cash_funding_bound_no_additional_live_risk_limit",
        runtime_rule_source_sha256=loop.digest(
            {
                name: __import__("hashlib")
                .sha256(Path(__file__).parents[2].joinpath(name).read_bytes())
                .hexdigest()
                for name in (
                    "trading/order/episode_quantity.py",
                    "trading/low_price_two_leg/profiles.py",
                    "trading/widget_auto_trade/engine.py",
                )
            }
        ),
        **loop.AUTHORITY,
    )
    value = {**body, "contract_sha256": loop.digest(body)}
    loop.atomic_write(directory / f"native_allocator_{source_date}.json", value)
    return value


def build_snapshot(
    source_date, *, directory=loop.DIRECTORY, owner_policy_path=None, report_root=None, source_directory_root=None
):
    """Require same-generation native cash/custody; unknown exposure is a gap."""
    blocked = dict(
        schema="machine_research_allocator_snapshot_v1",
        source_date=source_date.isoformat(),
        source_quality_status="source_gap",
        reason="native_cash_custody_or_owner_contract_missing",
        **loop.AUTHORITY,
    )
    try:
        source_root = source_directory_root or directory
        source_directory = source_root / "native_capacity" / str(source_date)
        cash_path = source_directory / "native_cash.json"
        inventory_path = source_directory / "native_inventory.json"
        cash = loop.read_object(cash_path)
        inventory = loop.read_object(inventory_path)
        acquisition = loop.read_object(
            source_root / f"capacity_source_{source_date}.json"
        )
        if (
            acquisition.get("status") != "complete"
            or acquisition.get("source_date") != str(source_date)
            or acquisition.get("receipt_sha256")
            != loop.digest(
                {k: v for k, v in acquisition.items() if k != "receipt_sha256"}
            )
            or acquisition.get("native_cash_sha256") != cash.get("native_sha256")
            or acquisition.get("native_inventory_sha256")
            != inventory.get("native_sha256")
            or any(acquisition.get(k) is not v for k, v in loop.AUTHORITY.items())
        ):
            return {**blocked, "reason": "native_source_acquisition_generation_invalid"}
        for value in (cash, inventory):
            body = {k: v for k, v in value.items() if k != "native_sha256"}
            if (
                value.get("schema") != loop.SCHEMA
                or value.get("source_date") != source_date.isoformat()
                or value.get("native_sha256") != loop.digest(body)
                or any(value.get(k) is not v for k, v in loop.AUTHORITY.items())
            ):
                return blocked
        if (
            cash["producer_pid"] != inventory["producer_pid"]
            or not 0
            <= (
                datetime.fromisoformat(cash["captured_at"])
                - datetime.fromisoformat(inventory["captured_at"])
            ).total_seconds()
            <= 30
        ):
            return {
                **blocked,
                "reason": "native_capacity_custody_generation_or_clock_gap",
            }
        if (
            set(inventory["successful_exchanges"]) != {"KRX", "NXT"}
            or inventory["open_orders_request_succeeded"] is not True
        ):
            return {**blocked, "reason": "native_custody_scope_incomplete"}
        holding = reserved = 0
        for row in inventory["inventory_by_code"].values():
            qty, price = row.get("qty"), row.get("buy_price")
            if (
                type(qty) is not int
                or qty < 0
                or type(price) not in (int, float)
                or not math.isfinite(price)
                or price <= 0
            ):
                return {**blocked, "reason": "native_inventory_notional_missing"}
            holding += qty * price
        # Unknown reservation prices cannot be replaced by zero. The native
        # publisher exposes quantity, so only a verified no-open-order snapshot
        # currently has a complete reservation-notional contract.
        if any(
            row.get("open_buy_qty") != 0
            for row in inventory["open_qty_by_code"].values()
        ):
            return {**blocked, "reason": "native_reservation_notional_missing"}
        owner = loop.read_object(owner_policy_path or policy_path(source_date))
        if acquisition.get("capacity_role") == "opening_fixed_budget" and acquisition.get("owner_contract_sha256") != loop.digest(owner):
            return {**blocked, "reason": "opening_owner_generation_conflict"}
        from src.trading.config.symbol_owner_policy import _canonical_hash

        if (
            owner.get("policy_hash") != _canonical_hash(owner)
            or owner.get("active_date") != source_date.isoformat()
            or owner.get("schema") != "symbol_owner_policy_v2"
            or not isinstance(owner.get("symbols"), dict)
        ):
            return {**blocked, "reason": "exact_date_owner_contract_invalid"}
        from src.trading.config.symbol_owner_policy import _validate_symbol_entry

        generated = datetime.fromisoformat(owner.get("generated_at_kst") or "")
        if (
            not owner.get("policy_id")
            or generated.tzinfo is None
            or generated > datetime.fromisoformat(cash["captured_at"])
        ):
            return {**blocked, "reason": "native_owner_metadata_invalid"}
        for symbol, row in owner["symbols"].items():
            _validate_symbol_entry(
                row,
                normalized_symbol=symbol,
                day=source_date,
                policy_id=owner["policy_id"],
            )
        available = min(
            cash["cash_context"]["account_deposit"],
            cash["cash_context"]["cash_orderable_amount"],
        )
        # A cash projection is not proof of the existing allocator's risk,
        # stage, quantity, cooldown or session contract. Consume a native
        # read-only contract when its producer has all of those facts; absence
        # remains an explicit allocation gap, never an invented limit.
        try:
            constraints = native_allocator_contract(
                source_date,
                cash=cash,
                inventory=inventory,
                owner=owner,
                holding=holding,
                available=available,
                directory=directory,
                report_root=report_root,
            )
        except (FileNotFoundError, ValueError):
            return {
                **blocked,
                "reason": "native_allocator_constraints_missing",
                "available_cash_krw": available,
                "native_cash_sha256": cash["native_sha256"],
                "native_inventory_sha256": inventory["native_sha256"],
            }
        constraint_body = {
            k: v for k, v in constraints.items() if k != "contract_sha256"
        }
        if (
            constraints.get("contract_sha256") != loop.digest(constraint_body)
            or constraints.get("source_date") != str(source_date)
            or constraints.get("native_cash_sha256") != cash["native_sha256"]
            or constraints.get("native_inventory_sha256") != inventory["native_sha256"]
            or constraints.get("owner_contract_sha256") != loop.digest(owner)
            or any(constraints.get(k) is not v for k, v in loop.AUTHORITY.items())
            or constraints.get("source_quality_status") != "PASS"
        ):
            return {**blocked, "reason": "native_allocator_constraints_invalid"}
        body = dict(
            schema="machine_research_allocator_snapshot_v1",
            source_date=source_date.isoformat(),
            source_quality_status="PASS",
            account_scope_sha256=acquisition.get("account_scope_sha256"),
            capacity_role=acquisition.get("capacity_role", "postclose_diagnostic"),
            available_cash_krw=available,
            holding_notional_krw=holding,
            reserved_notional_krw=reserved,
            exposure_limit_krw=constraints.get("exposure_limit_krw"),
            exposure_limit_basis="native_existing_allocator_contract",
            constraints=constraints,
            owner_contract_sha256=loop.digest(owner),
            owner_policy_path=str(
                (owner_policy_path or policy_path(source_date)).resolve()
            ),
            owner_conflict=constraints.get("owner_conflict"),
            native_cash_sha256=cash["native_sha256"],
            native_inventory_sha256=inventory["native_sha256"],
            captured_at=max(cash["captured_at"], inventory["captured_at"]),
            native_acquisition_path=str(
                (source_root / f"capacity_source_{source_date}.json").resolve()
            ),
            native_acquisition_sha256=acquisition["receipt_sha256"],
            native_cash_path=str(cash_path.resolve()),
            native_inventory_path=str(inventory_path.resolve()),
            allocator_rule="fixed_existing_allocator_no_research_arbitration",
            **loop.AUTHORITY,
        )
        return {**body, "snapshot_sha256": loop.digest(body)}
    except (OSError, ValueError, TypeError, KeyError, RuntimeError):
        return blocked


def write_snapshot(source_date, *, directory=loop.DIRECTORY, report_root=None):
    opening = directory / "opening_capacity"
    owner = opening / "native_capacity" / str(source_date) / "owner_policy.json"
    # Intraday economics may only consume the earlier, immutable acquisition.
    # Postclose cash remains available separately as an operational diagnostic.
    snapshot = build_snapshot(source_date, directory=directory, report_root=report_root,
        source_directory_root=opening, owner_policy_path=owner)
    loop.atomic_write(directory / f"allocator_{source_date.isoformat()}.json", snapshot)
    return snapshot
