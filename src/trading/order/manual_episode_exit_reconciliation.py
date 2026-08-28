"""Broker-receipt reconciliation for manually exited episode inventory.

The command never submits, cancels, or replaces an order.  It closes exactly
one profile ledger only after a completed manual sell receipt matches that
profile's whole held quantity.  Cross-profile or partial allocation is refused.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.sniper_config import CONF
from src.trading.low_price_two_leg.profiles import PROFILES
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
DEFAULT_RECEIPT_REGISTRY_PATH = (
    DATA_DIR / "runtime" / "episode_manual_exit_receipts.json"
)
OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "9180debf7aea0074715dd8f7a15af432afbfc403",
    "retrieved_at_kst": "2026-08-28T14:58:17+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": ["kt00007"],
}


@dataclass(frozen=True)
class EpisodeOwner:
    owner_id: str
    symbol: str
    state_path: Path
    schema: str


def _owner_registry() -> dict[str, EpisodeOwner]:
    runtime_dir = DATA_DIR / "runtime"
    owners = {
        profile_id: EpisodeOwner(
            owner_id=profile_id,
            symbol=profile.symbol,
            state_path=runtime_dir / "low_price_two_leg" / f"{profile_id}_state.json",
            schema=f"low_price_two_leg_{profile_id}_state_v1",
        )
        for profile_id, profile in PROFILES.items()
    }
    owners.update(
        {
            "samsung_morning": EpisodeOwner(
                "samsung_morning",
                "005930",
                runtime_dir / "samsung_morning_one_share_state.json",
                "samsung_morning_two_leg_state_v2",
            ),
            "samsung_morning_reentry": EpisodeOwner(
                "samsung_morning_reentry",
                "005930",
                runtime_dir / "samsung_morning_sor_reentry_state.json",
                "samsung_morning_sor_reentry_two_leg_state_v1",
            ),
            "samsung_midday": EpisodeOwner(
                "samsung_midday",
                "005930",
                runtime_dir / "samsung_midday_one_share_state.json",
                "samsung_midday_two_leg_state_v2",
            ),
            "samsung_afternoon": EpisodeOwner(
                "samsung_afternoon",
                "005930",
                runtime_dir / "samsung_afternoon_one_share_state.json",
                "samsung_afternoon_two_leg_state_v2",
            ),
        }
    )
    return owners


OWNERS = _owner_registry()


def _positive_int(value: object) -> int:
    parsed = _exact_nonnegative_int(value)
    return parsed if parsed is not None else 0


def _exact_nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        text = str(value).replace(",", "").strip()
    except (TypeError, ValueError):
        return None
    if not text or not text.isascii() or not text.isdigit():
        return None
    return int(text)


def _same_order_no(left: object, right: object) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    return bool(
        left_text
        and right_text
        and (left_text == right_text or left_text.lstrip("0") == right_text.lstrip("0"))
    )


def _split_order_nos(value: object) -> list[str]:
    order_nos = [item.strip() for item in str(value or "").split(",") if item.strip()]
    canonical = [item.lstrip("0") or "0" for item in order_nos]
    if not order_nos or len(canonical) != len(set(canonical)):
        raise ValueError("manual_sell_order_numbers_invalid_or_duplicate")
    return order_nos


def load_manual_sell_receipts(
    token: str, order_date: str, symbol: str
) -> list[dict[str, Any]]:
    rows = kiwoom_utils.get_order_reference_snapshot_kt00007(
        token,
        ord_dt=order_date.replace("-", ""),
        qry_tp="1",
        stk_bond_tp="0",
        sell_tp="0",
        stk_cd=symbol,
        dmst_stex_tp="%",
    )
    # kt00007 is explicitly scoped by ``ord_dt``, but the broker response does
    # not consistently echo that date at the response or row level.  Preserve
    # the request-scoped date on normalized rows so receipt verification does
    # not silently reject an otherwise exact broker receipt.
    requested_date = order_date.replace("-", "")
    return [
        {
            **row,
            "trade_date": str(row.get("trade_date") or requested_date),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def _read_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"state_unreadable:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise ValueError("state_payload_invalid")
    return payload


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _verified_receipts(
    *,
    rows: list[dict[str, Any]],
    order_nos: list[str],
    order_date: str,
    symbol: str,
    expected_qty: int,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for order_no in order_nos:
        matches = [
            row
            for row in rows
            if _same_order_no(row.get("ord_no"), order_no)
            and kiwoom_utils.normalize_stock_code(str(row.get("code") or "")) == symbol
            and str(row.get("side") or "") == "매도"
            and str(row.get("trade_date") or "").replace("-", "")
            == order_date.replace("-", "")
        ]
        if len(matches) != 1:
            raise ValueError(
                f"manual_sell_receipt_unique_match_required:{order_no}:{len(matches)}"
            )
        row = matches[0]
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        order_qty = _exact_nonnegative_int(raw.get("ord_qty"))
        filled_qty = _exact_nonnegative_int(raw.get("cntr_qty"))
        remaining_qty = _exact_nonnegative_int(raw.get("ord_remnq"))
        fill_price = _exact_nonnegative_int(raw.get("cntr_uv"))
        if (
            order_qty is None
            or filled_qty is None
            or remaining_qty is None
            or fill_price is None
            or order_qty <= 0
            or filled_qty != order_qty
            or remaining_qty != 0
            or fill_price <= 0
        ):
            raise ValueError("manual_sell_receipt_not_exact_full_exit")
        receipts.append(
            {
                "source_api": "kt00007",
                "order_no": str(row.get("ord_no") or ""),
                "order_date": order_date,
                "symbol": symbol,
                "filled_qty": filled_qty,
                "fill_price": fill_price,
            }
        )
    if expected_qty <= 0 or sum(row["filled_qty"] for row in receipts) != expected_qty:
        raise ValueError("manual_sell_receipt_not_exact_full_exit")
    return receipts


def _verified_prior_day_unfilled_target(
    *,
    rows: list[dict[str, Any]],
    order_no: str,
    order_date: str,
    symbol: str,
    expected_qty: int,
) -> dict[str, Any]:
    matches = [
        row
        for row in rows
        if _same_order_no(row.get("ord_no"), order_no)
        and kiwoom_utils.normalize_stock_code(str(row.get("code") or "")) == symbol
        and str(row.get("side") or "") == "매도"
        and str(row.get("trade_date") or "").replace("-", "")
        == order_date.replace("-", "")
    ]
    if len(matches) != 1:
        raise ValueError(f"prior_target_unique_match_required:{len(matches)}")
    raw = matches[0].get("raw") if isinstance(matches[0].get("raw"), dict) else {}
    order_qty = _exact_nonnegative_int(raw.get("ord_qty"))
    filled_qty = _exact_nonnegative_int(raw.get("cntr_qty"))
    fill_price = _exact_nonnegative_int(raw.get("cntr_uv"))
    if (
        expected_qty <= 0
        or order_qty != expected_qty
        or filled_qty != 0
        or fill_price != 0
    ):
        raise ValueError("prior_target_not_exact_unfilled_order")
    return {
        "source_api": "kt00007",
        "order_no": str(matches[0].get("ord_no") or ""),
        "order_date": order_date,
        "symbol": symbol,
        "order_qty": order_qty,
        "filled_qty": filled_qty,
        "fill_price": fill_price,
    }


def reconcile_manual_exit(
    *,
    owner_id: str,
    order_no: str,
    order_date: str,
    receipt_rows: list[dict[str, Any]],
    target_order_rows: list[dict[str, Any]] | None = None,
    observed_at: datetime,
    apply: bool,
    confirmation: str = "",
    state_path: Path | None = None,
    receipt_registry_path: Path = DEFAULT_RECEIPT_REGISTRY_PATH,
) -> dict[str, Any]:
    owner = OWNERS.get(owner_id)
    if owner is None:
        raise ValueError("episode_owner_not_allowed")
    parsed_order_date = date.fromisoformat(order_date)
    if observed_at.tzinfo is None:
        raise ValueError("observed_at_timezone_required")
    observed_at = observed_at.astimezone(KST)
    path = Path(state_path or owner.state_path)
    lock_path = path.with_suffix(".lock")
    registry_path = Path(receipt_registry_path)
    registry_lock_path = registry_path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    registry_lock_path.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        registry_lock_handle = stack.enter_context(
            registry_lock_path.open("a+", encoding="ascii")
        )
        fcntl.flock(registry_lock_handle.fileno(), fcntl.LOCK_EX)
        lock_handle = stack.enter_context(lock_path.open("a+", encoding="ascii"))
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("episode_service_or_reconciliation_lock_active") from exc
        state = _read_state(path)
        if state.get("schema") != owner.schema:
            raise ValueError("state_schema_or_owner_mismatch")
        try:
            trade_date = date.fromisoformat(str(state.get("trade_date") or ""))
        except ValueError as exc:
            raise ValueError("state_trade_date_invalid") from exc
        if parsed_order_date < trade_date or parsed_order_date > observed_at.date():
            raise ValueError("manual_sell_order_date_outside_custody_window")
        legs = state.get("legs")
        if not isinstance(legs, list) or len(legs) != 2:
            raise ValueError("state_two_leg_contract_invalid")
        state_numeric_fields = (
            "quantity",
            "entry_price",
            "fill_price",
            "buy_filled_qty",
            "position_qty",
            "target_price",
            "target_quantity",
            "target_filled_qty",
            "target_fill_price",
        )
        if any(
            not isinstance(leg, dict)
            or any(
                _exact_nonnegative_int(leg.get(field)) is None
                for field in state_numeric_fields
            )
            for leg in legs
        ):
            raise ValueError("state_leg_numeric_contract_invalid")
        held_legs = [leg for leg in legs if _positive_int(leg.get("position_qty")) > 0]
        held_qty = sum(_positive_int(leg.get("position_qty")) for leg in held_legs)
        if held_qty <= 0 or _positive_int(state.get("position_qty")) != held_qty:
            raise ValueError("state_has_no_exact_held_inventory")
        if any(
            _positive_int(leg.get("position_qty")) == 0
            and str(leg.get("status") or "") not in {"COMPLETE", "NO_FILL"}
            for leg in legs
        ):
            raise ValueError("manual_exit_requires_other_legs_terminal")
        requested_order_nos = _split_order_nos(order_no)
        receipts = _verified_receipts(
            rows=receipt_rows,
            order_nos=requested_order_nos,
            order_date=order_date,
            symbol=owner.symbol,
            expected_qty=held_qty,
        )
        if len(receipts) == 1:
            leg_receipts = [receipts[0] for _leg in held_legs]
        elif len(receipts) == len(held_legs) and [
            row["filled_qty"] for row in receipts
        ] == [_positive_int(leg.get("position_qty")) for leg in held_legs]:
            # Multiple manual orders must be passed in the same order as the
            # owner ledger legs.  This preserves exact per-leg realized prices
            # without inventing a cross-leg allocation.
            leg_receipts = list(receipts)
        else:
            raise ValueError("manual_sell_receipts_require_exact_leg_allocation")
        order_nos = [str(row["order_no"]) for row in receipts]
        receipt_summary = (
            dict(receipts[0])
            if len(receipts) == 1
            else {
                "source_api": "kt00007",
                "order_no": ",".join(order_nos),
                "order_nos": order_nos,
                "order_date": order_date,
                "symbol": owner.symbol,
                "filled_qty": held_qty,
                "receipts": receipts,
            }
        )
        superseded_target_legs: list[dict[str, Any]] = []
        for leg in held_legs:
            leg_status = str(leg.get("status") or "")
            no_prior_exit = (
                _positive_int(leg.get("target_filled_qty")) == 0
                and _positive_int(leg.get("target_fill_price")) == 0
                and _positive_int(leg.get("buy_filled_qty"))
                == _positive_int(leg.get("position_qty"))
            )
            if leg_status == "HELD" and no_prior_exit:
                continue
            if leg_status != "TARGET_OPEN" or not no_prior_exit:
                raise ValueError(
                    "manual_exit_requires_closed_targets_and_no_partial_exit"
                )
            try:
                target_order_date = date.fromisoformat(
                    str(leg.get("target_order_date") or "")
                )
            except ValueError as exc:
                raise ValueError("manual_exit_prior_target_order_date_invalid") from exc
            target_order_no = str(leg.get("target_order_no") or "").strip()
            if not target_order_no or target_order_date >= parsed_order_date:
                raise ValueError(
                    "manual_exit_requires_closed_targets_and_no_partial_exit"
                )
            superseded_target_legs.append(
                {
                    "leg_id": str(leg.get("leg_id") or ""),
                    **_verified_prior_day_unfilled_target(
                        rows=list(target_order_rows or []),
                        order_no=target_order_no,
                        order_date=target_order_date.isoformat(),
                        symbol=owner.symbol,
                        expected_qty=_positive_int(leg.get("target_quantity")),
                    ),
                }
            )
        if registry_path.exists():
            registry = _read_state(registry_path)
            registry_rows = registry.get("receipts")
            if (
                registry.get("schema") != "episode_manual_exit_receipt_registry_v1"
                or not isinstance(registry_rows, list)
                or any(not isinstance(item, dict) for item in registry_rows)
            ):
                raise ValueError("manual_exit_receipt_registry_contract_invalid")
        else:
            registry = {}
            registry_rows = []
        registered_identities = {
            (
                str(item.get("order_date") or ""),
                str(item.get("symbol") or ""),
                str(item.get("order_no") or "").lstrip("0") or "0",
            )
            for item in registry_rows
            if isinstance(item, dict)
        }
        if any(
            (
                receipt["order_date"],
                receipt["symbol"],
                str(receipt["order_no"]).lstrip("0") or "0",
            )
            in registered_identities
            for receipt in receipts
        ):
            raise ValueError("manual_sell_receipt_already_reserved_or_applied")
        confirmation_order_nos = "+".join(order_nos)
        expected_confirmation = (
            f"RECONCILE_{owner_id}_{trade_date.isoformat()}_"
            f"{held_qty}_{confirmation_order_nos}"
        )
        result = {
            "status": "ready" if not apply else "applied",
            "owner_id": owner_id,
            "symbol": owner.symbol,
            "state_path": str(path),
            "trade_date": trade_date.isoformat(),
            "held_qty": held_qty,
            "receipt": receipt_summary,
            "receipts": receipts,
            "prior_day_target_resolution": {
                "mode": (
                    "superseded_by_later_exact_full_manual_sell"
                    if superseded_target_legs
                    else "already_reconciled_held"
                ),
                "targets": superseded_target_legs,
            },
            "expected_confirmation": expected_confirmation,
            "runtime_effect": False,
            "actual_order_submitted": False,
        }
        if not apply:
            return result
        if confirmation != expected_confirmation:
            raise ValueError("manual_exit_confirmation_mismatch")
        new_registry_rows = []
        for receipt in receipts:
            registry_row = {
                **receipt,
                "owner_id": owner_id,
                "entry_trade_date": trade_date.isoformat(),
                "status": "reserved",
                "reserved_at_kst": observed_at.isoformat(),
            }
            registry_rows.append(registry_row)
            new_registry_rows.append(registry_row)
        registry = {
            "schema": "episode_manual_exit_receipt_registry_v1",
            "receipts": registry_rows,
        }
        _atomic_write(registry_path, registry)
        for leg, receipt in zip(held_legs, leg_receipts, strict=True):
            leg_qty = _positive_int(leg.get("position_qty"))
            if str(leg.get("status") or "") == "TARGET_OPEN":
                leg["prior_target_resolution"] = {
                    "mode": "superseded_by_later_exact_full_manual_sell",
                    "target_order_no": str(leg.get("target_order_no") or ""),
                    "target_order_date": str(leg.get("target_order_date") or ""),
                    "manual_sell_order_no": receipt["order_no"],
                    "manual_sell_order_date": receipt["order_date"],
                }
            leg.update(
                {
                    "status": "COMPLETE",
                    "position_qty": 0,
                    "target_filled_qty": _positive_int(leg.get("buy_filled_qty")),
                    "target_fill_price": receipt["fill_price"],
                    "target_filled_at": observed_at.isoformat(),
                    "exit_fill_source": "broker_verified_manual_sell_receipt",
                    "manual_exit_receipt": {
                        **receipt,
                        "allocated_qty": leg_qty,
                        "allocation_authority": "explicit_owner_whole_position_exit",
                    },
                }
            )
        state.update(
            {
                "status": "COMPLETE",
                "position_qty": 0,
                "blocked_reason": "",
                "last_action": "broker_verified_manual_exit_reconciled",
                "updated_at": observed_at.isoformat(),
            }
        )
        audit = state.get("audit")
        if not isinstance(audit, list):
            audit = []
            state["audit"] = audit
        audit_row = {
            "at_kst": observed_at.isoformat(),
            "action": "broker_verified_manual_exit_reconciled",
            "owner_id": owner_id,
            "order_no": receipt_summary["order_no"],
            "order_nos": order_nos,
            "order_date": order_date,
            "filled_qty": held_qty,
            "receipts": receipts,
            "prior_day_target_resolution": result["prior_day_target_resolution"],
        }
        if len(receipts) == 1:
            audit_row["fill_price"] = receipts[0]["fill_price"]
        audit.append(audit_row)
        state["audit"] = audit[-100:]
        _atomic_write(path, state)
        for registry_row in new_registry_rows:
            registry_row["status"] = "applied"
            registry_row["applied_at_kst"] = observed_at.isoformat()
        _atomic_write(registry_path, registry)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True, choices=sorted(OWNERS))
    parser.add_argument(
        "--order-no",
        required=True,
        help="one order number or comma-separated per-leg order numbers",
    )
    parser.add_argument("--order-date", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        order_date = date.fromisoformat(args.order_date).isoformat()
    except ValueError as exc:
        parser.error(f"invalid --order-date: {exc}")
    token = str(kiwoom_utils.get_cached_kiwoom_token(CONF) or "").strip()
    if not token:
        raise SystemExit("shared_cached_token_unavailable")
    owner = OWNERS[args.owner]
    rows = load_manual_sell_receipts(token, order_date, owner.symbol)
    state = _read_state(owner.state_path)
    target_order_dates = sorted(
        {
            str(leg.get("target_order_date") or "")
            for leg in state.get("legs") or []
            if isinstance(leg, dict)
            and str(leg.get("status") or "") == "TARGET_OPEN"
            and str(leg.get("target_order_date") or "") < order_date
        }
    )
    target_rows = [
        row
        for target_order_date in target_order_dates
        for row in load_manual_sell_receipts(token, target_order_date, owner.symbol)
    ]
    result = reconcile_manual_exit(
        owner_id=args.owner,
        order_no=args.order_no,
        order_date=order_date,
        receipt_rows=rows,
        target_order_rows=target_rows,
        observed_at=datetime.now(tz=KST),
        apply=args.apply,
        confirmation=args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
