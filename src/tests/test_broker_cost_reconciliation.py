"""Exact execution statements, delayed settlement and receipt isolation contracts."""
from copy import deepcopy
from datetime import datetime
import json
from zoneinfo import ZoneInfo

import pytest
from src.engine.lifecycle import broker_cost_reconciliation as cost
from src.engine import sniper_trade_review_report as review


def fixture():
    def event(stage, clock, fields):
        return review.HoldingEvent(f"2026-10-08 {clock}", "Test", "123456", stage,
            {"pipeline_lifecycle_population_scope": "real_record_bound",
             "actual_order_submitted": True, "broker_order_forbidden": False,
             "broker_route": "SOR", **fields}, "")
    buys = [event("position_rebased_after_fill", "10:00:00", {
        "order_no": "B", "execution_no": "B1", "fill_qty": 2,
        "order_filled_qty": 2, "order_requested_qty": 2, "order_remaining_qty": 0,
        "fill_price": 10000, "fill_quality": "FULL_FILL",
        "receipt_quantity_contract_complete": True, "receipt_unit_fill_consistent": True,
        "receipt_economics_complete": True})]
    sells = [event("sell_partial_fill_progress", "10:01:00", {
        "order_no": "S", "execution_no": "S1", "main_lifecycle_exit_qty": 1,
        "main_lifecycle_exit_price": 10100, "cumulative_sell_qty": 1,
        "sell_receipt_quantity_contract_complete": True,
        "sell_receipt_unit_fill_consistent": True,
        "sell_receipt_economics_complete": False}),
        event("sell_completed", "10:01:01", {
        "order_no": "S", "execution_no": "S2", "main_lifecycle_exit_qty": 1,
        "main_lifecycle_exit_price": 10100, "cumulative_sell_qty": 2,
        "remaining_sell_qty": 0, "decision_authority": "broker_sell_fill_observation_only",
        "sell_execution_receipt_quantity_contract_complete": True,
        "sell_execution_receipt_unit_fill_consistent": True,
        "sell_execution_receipt_economics_complete": False,
        "holding_cost_owner": "main", "holding_cost_account_scope_sha256": "b" * 64,
        "main_lifecycle_execution_occurrence_time_source": "official_fid_908",
        "main_lifecycle_execution_occurred_at": "2026-10-08T10:01:01+09:00"})]
    trade = {"id": 1, "code": "123456", "rec_date": "2026-10-08",
             "strategy": "SCALPING", "status": "COMPLETED", "profit_rate": 0.8,
             "buy_qty": 2, "buy_price": 10000, "sell_price": 10100}
    events = buys + sells
    ledger = review._completed_execution_ledger(trade, events)
    context = {"position_key": "record:1", "symbol": "123456", "owner": "main",
               "account_scope_sha256": "b" * 64,
               "buy_fill_identity": cost.digest(ledger["buy_fill_legs"]),
               "completion_observed_date": "2026-10-08",
               "completed_at": datetime(2026, 10, 8, 10, 1, 1, tzinfo=cost.KST).timestamp()}
    legs = [{"side": side, "trade_date": leg["at"][:10], "route": leg["route"],
             "order_no": leg["order_no"], "execution_no": leg["execution_no"],
             "price": leg["price"], "qty": leg["qty"], "fee_krw": 0,
             "tax_krw": 0 if side == "BUY" else 5}
            for side, rows in (("BUY", ledger["buy_fill_legs"]), ("SELL", ledger["sell_fill_legs"]))
            for leg in rows]
    receipt = {"schema": cost.SCHEMA, "status": "complete", "revision": 1,
               **{k: v for k, v in context.items() if k != "completed_at"},
               "cost_available_at": "2026-10-09T08:00:00+09:00",
               "reconciled_at": "2026-10-09T08:00:01+09:00", "legs": legs,
               "realized_pnl_krw": 190}
    seal(receipt)
    return trade, events, ledger, context, receipt


def seal(receipt):
    raw = {k: receipt[k] for k in ("position_key", "symbol", "account_scope_sha256", "buy_fill_identity", "legs")}
    raw["currency"] = "KRW"
    receipt["source"] = {"kind": "broker_statement_exact_execution_costs",
        "environment": "real", "allocation_scope": "exact_execution",
        "raw_statement": raw, "raw_sha256": cost.digest(raw)}
    receipt["receipt_sha256"] = cost.digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})


def test_delayed_costs_preserve_completion_and_configured_rate_without_blocking_price_recovery():
    trade, events, ledger, context, receipt = fixture()
    before = review._completed_trade_projection(trade, events, {"entry_mode": "normal"})
    assert before["sell_quantity_conserved"] is True
    assert before["economics_status"] == "cost_source_unavailable"
    at_close = review._completed_trade_projection(trade, events, {"entry_mode": "normal"},
        cost_receipt=receipt, knowledge_cutoff=context["completed_at"])
    assert at_close["economics_status"] == "actual_cost_pending"
    fixed = review._completed_trade_projection(trade, events, {"entry_mode": "normal"}, cost_receipt=receipt)
    assert fixed["completion_observed_date"] == "2026-10-08"
    assert fixed["strict_completion_status"] == "eligible", fixed["strict_completion_reasons"]
    assert fixed["canonical_configured_profit_rate"] == 0.8
    assert fixed["profit_rate"] == pytest.approx(0.95)
    assert fixed["realized_pnl_krw"] == 190
    assert fixed["broker_actual_fees_taxes_krw"] == 10
    from src.engine.holding_exit_observation_report import _strict_completed_reasons
    assert _strict_completed_reasons(fixed, clean_start="2026-09-29") == []


@pytest.mark.parametrize("mutation", ["missing_leg", "duplicate", "route", "account", "owner",
                                      "missing_tax", "cumulative", "nan", "wrong_pnl"])
def test_exact_cost_rejects_ambiguous_allocation_and_identity(mutation):
    _, _, ledger, context, receipt = fixture()
    if mutation == "missing_leg": receipt["legs"].pop()
    if mutation == "duplicate": receipt["legs"].append(deepcopy(receipt["legs"][0]))
    if mutation == "route": receipt["legs"][0]["route"] = "KRX"
    if mutation == "account": receipt["account_scope_sha256"] = "c" * 64
    if mutation == "owner": receipt["owner"] = "episode"
    if mutation == "missing_tax": receipt["legs"][0].pop("tax_krw")
    if mutation == "wrong_pnl": receipt["realized_pnl_krw"] = 191
    if mutation != "nan": seal(receipt)
    if mutation == "cumulative":
        receipt["source"]["allocation_scope"] = "daily_symbol_total"
        receipt["receipt_sha256"] = cost.digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    if mutation == "nan": receipt["realized_pnl_krw"] = float("nan")
    result = cost.reconcile(receipt, context=context, buy_legs=ledger["buy_fill_legs"], sell_legs=ledger["sell_fill_legs"])
    assert result["status"] == "actual_cost_invalid"
    assert result["exact_pnl_krw"] is None


def test_cost_revision_changes_source_generation_and_invalid_rows_stay_isolated(tmp_path):
    _, _, _, _, receipt = fixture()
    path = cost.receipt_path(tmp_path, "2026-10-08", "1")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt))
    generation = cost.source_generation(tmp_path, "2026-10-08")
    assert generation == cost.source_generation(tmp_path, "2026-10-08")
    receipt["revision"] = 2
    seal(receipt)
    path.write_text(json.dumps(receipt))
    assert generation != cost.source_generation(tmp_path, "2026-10-08")
    broken = path.with_name("2.json")
    broken.write_text("invalid")
    assert cost.source_generation(tmp_path, "2026-10-08")["count"] == 2
    assert cost.load_receipt(tmp_path, "2026-10-08", "1") == receipt
    with pytest.raises(ValueError): cost.load_receipt(tmp_path, "2026-10-08", "2")


def test_initial_partial_buys_and_additional_buy_costs_are_all_required():
    _, _, ledger, context, receipt = fixture()
    initial = ledger["buy_fill_legs"][0]
    buy_legs = [dict(initial, qty=1, amount_krw=10000),
                dict(initial, qty=1, amount_krw=10000, execution_no="B2"),
                dict(initial, qty=1, amount_krw=10050, order_no="ADD", execution_no="A1", price=10050)]
    sell_legs = [ledger["sell_fill_legs"][0], dict(ledger["sell_fill_legs"][1], qty=2)]
    context["buy_fill_identity"] = receipt["buy_fill_identity"] = cost.digest(buy_legs)
    receipt["legs"] = [{"side": side, "trade_date": leg["at"][:10], "route": leg["route"],
        "order_no": leg["order_no"], "execution_no": leg["execution_no"], "qty": leg["qty"],
        "price": leg["price"], "fee_krw": 1, "tax_krw": 0 if side == "BUY" else 5}
        for side, rows in (("BUY", buy_legs), ("SELL", sell_legs)) for leg in rows]
    receipt["realized_pnl_krw"] = 235
    seal(receipt)
    verified = cost.reconcile(receipt, context=context, buy_legs=buy_legs, sell_legs=sell_legs)
    assert verified["exact_pnl_krw"] == 235
    assert verified["actual_fees_taxes_krw"] == 15
    receipt["legs"] = [leg for leg in receipt["legs"] if leg["order_no"] != "ADD"]
    seal(receipt)
    assert cost.reconcile(receipt, context=context, buy_legs=buy_legs, sell_legs=sell_legs)["status"] == "actual_cost_invalid"


def test_explicit_actual_zero_costs_and_zero_profit_are_valid_not_missing():
    _, _, ledger, context, receipt = fixture()
    for leg in receipt["legs"]:
        leg["fee_krw"] = leg["tax_krw"] = 0
    receipt["realized_pnl_krw"] = 200
    seal(receipt)
    result = cost.reconcile(receipt, context=context, buy_legs=ledger["buy_fill_legs"], sell_legs=ledger["sell_fill_legs"])
    assert result["status"] == "actual_cost_reconciled"
    assert result["actual_fees_taxes_krw"] == 0
    for leg in receipt["legs"]:
        if leg["side"] == "SELL": leg["tax_krw"] = 100
    receipt["realized_pnl_krw"] = 0
    seal(receipt)
    result = cost.reconcile(receipt, context=context, buy_legs=ledger["buy_fill_legs"], sell_legs=ledger["sell_fill_legs"])
    assert result["status"] == "actual_cost_reconciled"
    assert result["exact_profit_rate"] == 0


def test_finite_execution_numbers_cannot_overflow_to_verified_nan_profit():
    _, _, ledger, context, receipt = fixture()
    for leg in ledger["buy_fill_legs"] + ledger["sell_fill_legs"] + receipt["legs"]:
        leg["price"] = 1e308
    seal(receipt)
    result = cost.reconcile(receipt, context=context, buy_legs=ledger["buy_fill_legs"],
                            sell_legs=ledger["sell_fill_legs"])
    assert result["status"] == "actual_cost_invalid"
    assert result["exact_pnl_krw"] is None
