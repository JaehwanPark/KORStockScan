from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring.low_price_two_leg_tuning import _aggregate, _sanitize_leg
from src.trading.order.manual_episode_exit_reconciliation import (
    reconcile_manual_exit,
)

KST = ZoneInfo("Asia/Seoul")


def _held_state() -> dict:
    legs = []
    for leg_id, entry_price in (
        ("signal_close", 50_000),
        ("signal_close_minus_1tick", 49_950),
    ):
        legs.append(
            {
                "leg_id": leg_id,
                "quantity": 10,
                "status": "HELD",
                "entry_price": entry_price,
                "fill_price": entry_price,
                "buy_filled_qty": 10,
                "position_qty": 10,
                "target_price": entry_price + 200,
                "target_quantity": 10,
                "target_filled_qty": 0,
                "target_fill_price": 0,
                "target_order_no": f"TARGET-{leg_id}",
                "target_order_date": "2026-08-13",
            }
        )
    return {
        "schema": "low_price_two_leg_sk_eternix_midday_state_v1",
        "trade_date": "2026-08-13",
        "status": "HELD",
        "attempt_consumed": True,
        "position_qty": 20,
        "blocked_reason": "",
        "owned_order_nos": [leg["target_order_no"] for leg in legs],
        "signal_features": {},
        "legs": legs,
        "audit": [],
    }


def _receipt(*, order_qty: int = 20, filled_qty: int = 20) -> list[dict]:
    return [
        {
            "source_api": "kt00007",
            "trade_date": "20260814",
            "code": "475150",
            "side": "매도",
            "qty": order_qty,
            "remaining_qty": order_qty - filled_qty,
            "unit_price": 49_800,
            "ord_no": "0012345",
            "raw": {
                "ord_qty": str(order_qty),
                "cntr_qty": str(filled_qty),
                "ord_remnq": str(order_qty - filled_qty),
                "cntr_uv": "49800",
            },
        }
    ]


def test_manual_exit_dry_run_preserves_state_and_reports_confirmation(tmp_path: Path):
    state_path = tmp_path / "state.json"
    payload = _held_state()
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    result = reconcile_manual_exit(
        owner_id="sk_eternix_midday",
        order_no="0012345",
        order_date="2026-08-14",
        receipt_rows=_receipt(),
        observed_at=datetime(2026, 8, 14, 9, 5, tzinfo=KST),
        apply=False,
        state_path=state_path,
        receipt_registry_path=tmp_path / "receipts.json",
    )

    assert result["status"] == "ready"
    assert result["held_qty"] == 20
    assert result["expected_confirmation"] == (
        "RECONCILE_sk_eternix_midday_2026-08-13_20_0012345"
    )
    assert json.loads(state_path.read_text(encoding="utf-8")) == payload


def test_manual_exit_applies_only_exact_whole_owner_receipt(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_held_state()), encoding="utf-8")

    result = reconcile_manual_exit(
        owner_id="sk_eternix_midday",
        order_no="0012345",
        order_date="2026-08-14",
        receipt_rows=_receipt(),
        observed_at=datetime(2026, 8, 14, 9, 5, tzinfo=KST),
        apply=True,
        confirmation="RECONCILE_sk_eternix_midday_2026-08-13_20_0012345",
        state_path=state_path,
        receipt_registry_path=tmp_path / "receipts.json",
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["status"] == "applied"
    assert state["status"] == "COMPLETE"
    assert state["position_qty"] == 0
    assert all(leg["status"] == "COMPLETE" for leg in state["legs"])
    assert all(leg["position_qty"] == 0 for leg in state["legs"])
    assert all(leg["target_filled_qty"] == 10 for leg in state["legs"])
    assert all(leg["target_fill_price"] == 49_800 for leg in state["legs"])
    assert all(
        leg["exit_fill_source"] == "broker_verified_manual_sell_receipt"
        for leg in state["legs"]
    )
    assert state["audit"][-1]["action"] == ("broker_verified_manual_exit_reconciled")
    sanitized = _sanitize_leg(state["legs"][0], 0.23)
    assert sanitized["contract_valid"] is True
    assert sanitized["profit_price_source"] == "broker_manual_sell_receipt"
    assert sanitized["realization_date"] == "2026-08-14"
    assert sanitized["net_profit_pct"] < 0
    aggregate = _aggregate(
        [
            {
                "attempted": True,
                "eligible_for_tuning": True,
                "legs": [_sanitize_leg(leg, 0.23) for leg in state["legs"]],
            }
        ]
    )
    assert aggregate["broker_priced_completed_legs"] == 2
    assert aggregate["target_price_proxy_completed_legs"] == 0


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        (_receipt(order_qty=40, filled_qty=40), "not_exact_full_exit"),
        (_receipt(order_qty=20, filled_qty=10), "not_exact_full_exit"),
    ],
)
def test_manual_exit_rejects_cross_owner_or_partial_receipt(
    tmp_path: Path, rows: list[dict], reason: str
):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_held_state()), encoding="utf-8")

    with pytest.raises(ValueError, match=reason):
        reconcile_manual_exit(
            owner_id="sk_eternix_midday",
            order_no="0012345",
            order_date="2026-08-14",
            receipt_rows=rows,
            observed_at=datetime(2026, 8, 14, 9, 5, tzinfo=KST),
            apply=False,
            state_path=state_path,
            receipt_registry_path=tmp_path / "receipts.json",
        )


def test_manual_exit_rejects_live_target_or_partial_prior_exit(tmp_path: Path):
    payload = _held_state()
    payload["legs"][0]["status"] = "TARGET_OPEN"
    payload["legs"][0]["target_filled_qty"] = 1
    payload["legs"][0]["position_qty"] = 9
    payload["position_qty"] = 19
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="closed_targets_and_no_partial_exit"):
        reconcile_manual_exit(
            owner_id="sk_eternix_midday",
            order_no="0012345",
            order_date="2026-08-14",
            receipt_rows=_receipt(order_qty=19, filled_qty=19),
            observed_at=datetime(2026, 8, 14, 9, 5, tzinfo=KST),
            apply=False,
            state_path=state_path,
            receipt_registry_path=tmp_path / "receipts.json",
        )


def test_manual_exit_receipt_cannot_be_reused_by_another_owner(tmp_path: Path):
    first_state = tmp_path / "first.json"
    first_state.write_text(json.dumps(_held_state()), encoding="utf-8")
    registry = tmp_path / "receipts.json"
    kwargs = {
        "order_no": "0012345",
        "order_date": "2026-08-14",
        "receipt_rows": _receipt(),
        "observed_at": datetime(2026, 8, 14, 9, 5, tzinfo=KST),
        "receipt_registry_path": registry,
    }
    reconcile_manual_exit(
        owner_id="sk_eternix_midday",
        apply=True,
        confirmation="RECONCILE_sk_eternix_midday_2026-08-13_20_0012345",
        state_path=first_state,
        **kwargs,
    )
    second_payload = _held_state()
    second_payload["schema"] = "low_price_two_leg_sk_eternix_morning_state_v1"
    second_state = tmp_path / "second.json"
    second_state.write_text(json.dumps(second_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="already_reserved_or_applied"):
        reconcile_manual_exit(
            owner_id="sk_eternix_morning",
            apply=False,
            state_path=second_state,
            **kwargs,
        )


def test_manual_exit_fails_closed_on_corrupt_registry_or_state_quantity(
    tmp_path: Path,
):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_held_state()), encoding="utf-8")
    registry = tmp_path / "receipts.json"
    registry.write_text(json.dumps({"receipts": []}), encoding="utf-8")
    kwargs = {
        "owner_id": "sk_eternix_midday",
        "order_no": "0012345",
        "order_date": "2026-08-14",
        "receipt_rows": _receipt(),
        "observed_at": datetime(2026, 8, 14, 9, 5, tzinfo=KST),
        "apply": False,
        "state_path": state_path,
        "receipt_registry_path": registry,
    }

    with pytest.raises(ValueError, match="registry_contract_invalid"):
        reconcile_manual_exit(**kwargs)

    registry.unlink()
    state = _held_state()
    state["legs"][0]["buy_filled_qty"] = 9
    state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(ValueError, match="closed_targets_and_no_partial_exit"):
        reconcile_manual_exit(**kwargs)

    state = _held_state()
    state["legs"][0]["target_filled_qty"] = "not-a-number"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(ValueError, match="state_leg_numeric_contract_invalid"):
        reconcile_manual_exit(**kwargs)


def test_manual_exit_rejects_malformed_raw_receipt_numbers(tmp_path: Path):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_held_state()), encoding="utf-8")
    rows = _receipt()
    rows[0]["raw"]["ord_remnq"] = "not-a-number"
    rows[0]["remaining_qty"] = 0

    with pytest.raises(ValueError, match="not_exact_full_exit"):
        reconcile_manual_exit(
            owner_id="sk_eternix_midday",
            order_no="0012345",
            order_date="2026-08-14",
            receipt_rows=rows,
            observed_at=datetime(2026, 8, 14, 9, 5, tzinfo=KST),
            apply=False,
            state_path=state_path,
            receipt_registry_path=tmp_path / "receipts.json",
        )
