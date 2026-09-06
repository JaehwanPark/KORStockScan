"""Contract tests for receipt-only recheck position economics."""

from copy import deepcopy

import pytest

from src.engine.scalping.entry_recheck_economics import (
    LEDGER_KEY,
    PREFIX,
    record_buy_receipt,
    recovered_fill_fields,
    terminal_economics,
)
from src.engine.scalping.entry_opportunity_recheck import attribution_fields
from src.engine.scalping.entry_recheck_policy import ATTRIBUTION_VERSION


def stock_and_receipt():
    stock = {
        PREFIX + "attempt_id": "attempt-1",
        PREFIX + "broker_order_no": "B1",
        PREFIX + "attribution_schema": ATTRIBUTION_VERSION,
        "entry_split_probe_bundle_id": "bundle-1",
    }
    receipt = {
        "order_no": "B1",
        "cumulative_qty": 1,
        "requested_qty": 1,
        "cumulative_amount": 10000,
        "economics_complete": True,
        "quantity_contract_complete": True,
        "unit_fill_consistent": True,
    }
    record_buy_receipt(stock, receipt, kind="entry")
    return stock, receipt


def sale(qty=1, amount=11000):
    return {
        "cumulative_sell_qty": qty,
        PREFIX + "sell_notional_krw": amount,
        PREFIX + "cost_rate": 0.0023,
        "sell_execution_receipt_economics_complete": True,
        "sell_execution_receipt_quantity_contract_complete": True,
        "sell_execution_receipt_unit_fill_consistent": True,
    }


@pytest.mark.parametrize(
    "qty,requested,cohort",
    [
        (1, 1, "probe_only"),
        (10, 10, "probe_residual_full_fill"),
        (6, 10, "probe_residual_partial_fill"),
    ],
)
def test_probe_and_residual_closed_position_receipts(qty, requested, cohort):
    stock, receipt = stock_and_receipt()
    if qty > 1:
        receipt = {
            **receipt,
            "order_no": "B2",
            "cumulative_qty": qty - 1,
            "requested_qty": requested - 1,
            "cumulative_amount": 10000 * (qty - 1),
        }
        record_buy_receipt(stock, receipt, kind="entry")
    before = deepcopy(stock)
    record_buy_receipt(stock, receipt, kind="entry")
    assert stock == before
    result = attribution_fields(
        stock, stage="sell_completed", event_fields=sale(qty, 11000 * qty)
    )
    assert result[PREFIX + "economics_complete"] is True
    assert result[PREFIX + "economics_decision_eligible"] is True
    assert result[PREFIX + "economics_cohort"] == cohort
    assert result[PREFIX + "realized_net_pnl_krw"] == round(
        11000 * qty * 0.9977 - 10000 * qty
    )


def test_scale_in_owner_is_diagnostic_even_when_reconciled():
    stock, receipt = stock_and_receipt()
    record_buy_receipt(stock, {**receipt, "order_no": "A1"}, kind="add")
    result = terminal_economics(stock, sale(2, 22000))
    assert result[PREFIX + "economics_complete"] is True
    assert result[PREFIX + "economics_decision_eligible"] is False
    assert result[PREFIX + "economics_cohort"] == "scale_in_mixed"


@pytest.mark.parametrize(
    "gap", ["wrong_order", "missing_quantity", "unit_conflict", "no_gap"]
)
def test_fast_fill_is_joined_only_to_verified_exact_accepted_order(gap):
    stock, receipt = stock_and_receipt()
    stock[PREFIX + "submit_observed"] = True
    stock[PREFIX + "direct_submit"] = True
    if gap == "wrong_order":
        stock[PREFIX + "broker_order_no"] = "B2"
    elif gap in {"missing_quantity", "unit_conflict"}:
        stock.pop(LEDGER_KEY)
        field = (
            "quantity_contract_complete"
            if gap == "missing_quantity"
            else "unit_fill_consistent"
        )
        record_buy_receipt(stock, {**receipt, field: False}, kind="entry")
    result = recovered_fill_fields(stock)
    assert bool(result) is (gap == "no_gap")
    if result:
        assert result[PREFIX + "fill_order_no"] == "B1"
        assert result[PREFIX + "fill_qty"] == 1
        assert PREFIX + "filled_at" not in result


def test_runtime_rest_response_recovers_prior_receipt_without_new_order():
    from src.engine import sniper_state_handlers as handlers

    stock, _ = stock_and_receipt()
    stock.pop(PREFIX + "broker_order_no")
    stock[PREFIX + "armed"] = True
    stock[PREFIX + "armed_at"] = 1000.0
    fields = handlers._mark_entry_opportunity_recheck_submission(
        stock,
        "005930",
        broker_order_no="B1",
        requested_qty=1,
        now_ts=1001.0,
    )
    assert fields[PREFIX + "fill_observed"] is True
    assert fields[PREFIX + "fill_order_no"] == "B1"
    assert LEDGER_KEY not in fields
    assert LEDGER_KEY in stock


def test_terminal_outbox_preserves_full_position_economics_after_custody_reset(
    monkeypatch,
):
    from datetime import datetime, timedelta, timezone
    from src.engine import sniper_execution_receipts as receipts

    stock, receipt = stock_and_receipt()
    stock.update(id=7, code="005930", name="EXACT")
    record_buy_receipt(
        stock,
        {
            **receipt,
            "order_no": "B2",
            "cumulative_qty": 9,
            "requested_qty": 9,
            "cumulative_amount": 90000,
        },
        kind="entry",
    )
    leg = receipts._build_sell_lifecycle_outbox_leg(
        stock,
        code="005930",
        target_id=7,
        now=datetime(2026, 9, 7, 10, tzinfo=timezone(timedelta(hours=9))),
        stage="sell_completed",
        event_fields=sale(10, 110000),
    )
    stock.clear()
    emitted = []

    def emit(pipeline, name, code, stage, *, record_id=None, fields=None):
        normalized = {str(k): str(v) for k, v in fields.items()}
        emitted.append((stage, normalized))
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": code,
            "record_id": record_id,
            "fields": normalized,
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(receipts, "emit_pipeline_event", emit)
    monkeypatch.setattr(
        receipts, "_sell_lifecycle_outbox_event_contract_valid", lambda **kwargs: True
    )
    assert receipts._emit_standard_sell_partial_lifecycle_outbox_leg(leg)
    assert len(emitted) == 2
    for _, fields in emitted:
        assert fields[PREFIX + "economics_complete"] == "True"
        assert fields[PREFIX + "economics_cohort"] == "probe_residual_full_fill"
        assert float(fields[PREFIX + "realized_net_pnl_krw"]) == 9747


@pytest.mark.parametrize(
    "gap",
    [
        "missing_buy",
        "partial_sell",
        "conflict",
        "different_bundle",
        "incomplete_buy",
        "incomplete_sell",
        "nonfinite",
        "wrong_attempt",
    ],
)
def test_incomplete_or_conflicting_receipts_never_promote(gap):
    stock, receipt = stock_and_receipt()
    fields = sale()
    if gap == "missing_buy":
        stock.pop(LEDGER_KEY)
    elif gap == "partial_sell":
        fields["cumulative_sell_qty"] = 0
    elif gap == "conflict":
        record_buy_receipt(stock, {**receipt, "cumulative_amount": 9000}, kind="entry")
    elif gap == "different_bundle":
        stock["entry_split_probe_bundle_id"] = "another"
        record_buy_receipt(stock, {**receipt, "order_no": "B2"}, kind="entry")
        fields = sale(2, 22000)
    elif gap == "incomplete_buy":
        stock[LEDGER_KEY]["orders"]["B1"]["economics_complete"] = False
    elif gap == "incomplete_sell":
        fields["sell_execution_receipt_quantity_contract_complete"] = False
    elif gap == "nonfinite":
        fields[PREFIX + "sell_notional_krw"] = float("nan")
    else:
        stock[PREFIX + "attempt_id"] = "different"
    result = attribution_fields(stock, stage="sell_completed", event_fields=fields)
    assert result[PREFIX + "economics_complete"] is False
    assert result[PREFIX + "cost_adjusted_profit_pct"] is None
