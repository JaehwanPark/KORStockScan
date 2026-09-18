"""Bounded postclose account-source acquisition; never a policy/order writer.

Reuse native authenticated/read-governed helpers. Requests are independent of
research symbol/grid/revision counts. Missing native capacity remains unknown.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time
import time as clocks
from zoneinfo import ZoneInfo

from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring.research_allocation_snapshot import (
    publish_cash_context,
    publish_inventory_context,
)

KST = ZoneInfo("Asia/Seoul")


def acquire(day, *, directory=loop.DIRECTORY, token=None, adapters=None):
    try:
        with loop.writer_lock(directory / "source_acquisition", blocking=False):
            return _acquire(day, directory=directory, token=token, adapters=adapters)
    except BlockingIOError:
        return dict(
            status="waiting",
            reason="native_source_acquisition_running",
            **loop.AUTHORITY,
        )


def _acquire(day, *, directory=loop.DIRECTORY, token=None, adapters=None):
    started = clocks.monotonic()
    body = dict(
        schema=loop.SCHEMA,
        source_date=str(day),
        status="source_gap",
        scope="native_account_once_not_per_candidate",
        order_requests=0,
        authentication_refresh_requests=0,
        **loop.AUTHORITY,
    )
    loop.atomic_write(
        directory / f"capacity_source_{day}.json", {**body, "status": "running"}
    )
    try:
        now = datetime.now(KST)
        if now.date() != day or now.time() < time(20, 5):
            raise ValueError("native_source_requires_current_completed_date_after_20_05")
        if adapters is None:
            from src.utils import kiwoom_utils as native
            from src.engine import kiwoom_orders as orders

            token = token or native.get_cached_kiwoom_token()
            adapters = dict(
                inventory=native.get_account_balance_kt00005_with_meta,
                unfilled=native.get_unfilled_order_snapshot_ka10075_with_meta,
                deposit=orders.get_deposit,
                deposit_meta=orders.get_last_deposit_meta,
                capacity=native.get_orderable_by_margin_kt00011,
            )
        if not token:
            raise ValueError("cached_authenticated_account_source_missing")
        # One existing KRX cash-capacity instrument, never inferred from a
        # research winner. Cash funding is conservatively bounded by native
        # 100 percent cash amount and unadjusted kt00001 orderable cash.
        inventory, venues, meta = adapters["inventory"](token)
        unfilled, order_meta = adapters["unfilled"](token)
        if (
            set(venues) != {"KRX", "NXT"}
            or meta.get("normalization_contract_complete") is not True
            or order_meta.get("normalization_contract_complete") is not True
            or order_meta.get("request_succeeded") is not True
        ):
            raise ValueError("native_account_normalization_scope_incomplete")
        captured = datetime.now(KST)
        if captured.date() != day:
            raise ValueError("native_source_date_not_current")
        open_qty = {}
        for row in unfilled:
            quantity = row["remaining_qty"]
            if (
                type(quantity) is not int
                or quantity < 0
                or row["side"] not in {"매수", "매도"}
            ):
                raise ValueError("native_unfilled_contract_invalid")
            scope = open_qty.setdefault(
                row["code"], dict(open_buy_qty=0, open_sell_qty=0)
            )
            scope["open_buy_qty" if row["side"] == "매수" else "open_sell_qty"] += (
                quantity
            )
        adapters["deposit"](token)
        deposit = adapters["deposit_meta"]()
        if (
            deposit.get("source") != "api_fresh"
            or deposit.get("fallback_used")
            or type(deposit.get("raw_amount")) is not int
            or deposit["raw_amount"] < 0
        ):
            raise ValueError("unadjusted_fresh_native_deposit_missing")
        capacity = adapters["capacity"](token, "005930", is_nxt=False)
        context = dict(
            account_deposit=deposit["raw_amount"],
            cash_orderable_amount=capacity.get("cash_only_orderable_amount"),
            cash_orderable_qty_cap=capacity.get("cash_only_orderable_qty"),
        )
        for key in (
            "cash_orderable_contract_status",
            "capacity_observed_at",
            "requested_stock_code",
            "capacity_source_sha256",
            "capacity_contract_version",
            "error",
        ):
            context["kt00011_" + key] = capacity.get(key)
        snapshot = dict(
            captured_at=captured.timestamp(),
            successful_exchanges=venues,
            inventory_by_code={row["code"]: row for row in inventory},
            open_qty_by_code=open_qty,
            open_orders_request_succeeded=True,
        )
        cash_clock = datetime.fromisoformat(context["kt00011_capacity_observed_at"])
        if (
            cash_clock.tzinfo is None
            or not 0 <= (cash_clock - captured).total_seconds() <= 30
        ):
            raise ValueError("native_acquisition_clock_gap")
        source_directory = directory / "native_capacity" / str(day)
        with loop.writer_lock(directory / "capacity_source", blocking=False):
            if not publish_inventory_context(snapshot, directory=source_directory):
                raise ValueError("native_inventory_projection_invalid")
            if not publish_cash_context(context, directory=source_directory):
                raise ValueError("native_cash_projection_invalid")
        body.update(
            status="complete",
            captured_at=cash_clock.isoformat(),
            native_cash_sha256=loop.read_object(source_directory / "native_cash.json")[
                "native_sha256"
            ],
            native_inventory_sha256=loop.read_object(
                source_directory / "native_inventory.json"
            )["native_sha256"],
            base_helper_invocations=4,
            research_count_dependent_requests=0,
        )
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        body["reason"] = str(exc)
    body["source_acquisition_seconds"] = clocks.monotonic() - started
    value = {**body, "receipt_sha256": loop.digest(body)}
    loop.atomic_write(directory / f"capacity_source_{day}.json", value)
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", type=date.fromisoformat, required=True)
    parser.add_argument("--write", action="store_true", required=True)
    args = parser.parse_args(argv)
    now = datetime.now(KST)
    if args.source_date != now.date() or now.time() < time(20, 5):
        parser.error(
            "native source acquisition requires current completed date after 20:05 KST"
        )
    result = acquire(args.source_date)
    print(result["status"])
    # The downstream phase records allocation_blocked and preserves custody;
    # an unavailable account source is never fabricated as a funding PASS.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
