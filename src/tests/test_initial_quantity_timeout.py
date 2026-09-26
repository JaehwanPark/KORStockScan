"""Source-only timeout schedule and terminal transition contracts."""

import copy
import json
from datetime import datetime, timedelta

import pytest

from src.engine.scalping.initial_quantity_timeout import (
    build_bundle_timeout_schedule, next_bundle_timeout_action,
    timeout_schedule_valid,
)
from src.engine.scalping import initial_quantity_timeout_research as research
from src.engine.scalping.initial_quantity_policy import _digest, join_post_fill_paths
from src.engine.trade_profit import calculate_net_profit_rate, calculate_net_realized_pnl


def _schedule(legs=3, total=120, reserve=5):
    return build_bundle_timeout_schedule(
        quantity_type="KRX_PARENT", policy_sha256="a" * 64,
        decision_at="2026-09-23T09:29:50+09:00",
        order_start_at="2026-09-23T09:30:00+09:00", total_wait_sec=total,
        leg_count=legs, cancel_confirm_reserve_sec=reserve,
    )


def _cancelled_terminal(at):
    return {"state": "TERMINAL_CANCELLED", "terminal_confirmed": True,
            "terminal_confirmed_at_epoch": at, "broker_order_no": "101",
            "broker_terminal_receipt_id": "broker:101:terminal",
            "owner_registry_receipt_id": "owner:101:terminal",
            "account_position_receipt_id": "account:101:reconciled",
            "broker_unfilled_qty": 0, "owner_registry_terminal": True,
            "account_position_reconciled": True,
            "ordered_qty": 3, "filled_qty": 1, "cancelled_qty": 2}


def test_timeout_schedule_partitions_total_from_order_start_and_includes_probe():
    plan = _schedule()
    assert timeout_schedule_valid(plan)
    assert plan["probe_included_in_leg_count"] is True
    assert plan["per_leg_slot_sec"] == 40
    assert plan["slots"][0]["cancel_request_by_epoch"] == plan["order_start_at_epoch"] + 35
    assert plan["slots"][2]["terminal_confirm_by_epoch"] == plan["bundle_deadline_epoch"]
    assert plan["bundle_deadline_epoch"] == plan["order_start_at_epoch"] + 120
    assert plan["order_start_at_epoch"] - plan["decision_at_epoch"] == 10
    assert _schedule(legs=3, total=1200)["bundle_deadline_epoch"] == (
        plan["order_start_at_epoch"] + 1200)
    assert _schedule(legs=4, total=1200)["per_leg_slot_sec"] == 300
    forged = copy.deepcopy(plan)
    forged["slots"][1]["terminal_confirm_by_epoch"] += 10
    assert not timeout_schedule_valid(forged)


@pytest.mark.parametrize("total,legs,reserve", [(1201, 1, 5), (10, 3, 5), (90, 0, 5), (90, 2, 0)])
def test_timeout_schedule_rejects_unbounded_or_unconfirmable_windows(total, legs, reserve):
    with pytest.raises(ValueError, match="initial_quantity_timeout_contract_invalid"):
        _schedule(legs=legs, total=total, reserve=reserve)


def test_timeout_schedule_rejects_naive_decision_clock():
    with pytest.raises(ValueError, match="initial_quantity_timeout_contract_invalid"):
        build_bundle_timeout_schedule(
            quantity_type="KRX_PARENT", policy_sha256="a" * 64,
            decision_at="2026-09-23T09:30:00", total_wait_sec=60,
            order_start_at="2026-09-23T09:30:01+09:00",
            leg_count=2, cancel_confirm_reserve_sec=5)
    with pytest.raises(ValueError, match="initial_quantity_timeout_contract_invalid"):
        build_bundle_timeout_schedule(
            quantity_type="KRX_PARENT", policy_sha256="a" * 64,
            decision_at="2026-09-23T09:30:01+09:00",
            order_start_at="2026-09-23T09:30:00+09:00", total_wait_sec=60,
            leg_count=2, cancel_confirm_reserve_sec=5)


def test_next_leg_requires_broker_terminal_and_never_extends_hard_deadline():
    plan = _schedule(legs=2, total=60, reserve=5)
    start = plan["order_start_at_epoch"]
    states = [{"state": "NOT_SUBMITTED"}, {"state": "NOT_SUBMITTED"}]
    assert next_bundle_timeout_action(plan, states, now_epoch=start)["action"] == "SUBMIT"
    states[0] = {"state": "OPEN", "broker_order_no": "101"}
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 26)["action"] == "CANCEL"
    states[0] = {"state": "CANCEL_REQUESTED", "broker_order_no": "101"}
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 32)["action"] == "RECONCILE"
    states[0] = _cancelled_terminal(start + 29)
    states[0]["terminal_confirmed"] = False
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 32)["action"] == "RECONCILE"
    states[0]["terminal_confirmed"] = True
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 32) == {
        "action": "SUBMIT", "leg_index": 1, "submit_before_epoch": start + 55}
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 56)["action"] == "SKIP_LEG"
    late_predecessor = copy.deepcopy(states)
    late_predecessor[0]["terminal_confirmed_at_epoch"] = start + 31
    assert next_bundle_timeout_action(
        plan, late_predecessor, now_epoch=start + 32)["action"] == "BLOCK_LATE_TERMINAL"
    states[1] = {"state": "OPEN", "broker_order_no": "102"}
    late = next_bundle_timeout_action(plan, states, now_epoch=start + 65)
    assert late["action"] == "CANCEL" and late["budget_breached"] is True
    states[1] = {"state": "CANCEL_REQUESTED", "broker_order_no": "102"}
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 70)["action"] == "RECONCILE"


def test_terminal_requires_reconciled_identity_quantity_and_observed_clock():
    plan = _schedule(legs=2, total=60, reserve=5)
    start = plan["order_start_at_epoch"]
    states = [_cancelled_terminal(start + 29), {"state": "NOT_SUBMITTED"}]
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 30)["action"] == "SUBMIT"
    for key, bad in (("broker_order_no", ""), ("broker_order_no", True),
                     ("broker_terminal_receipt_id", ""),
                     ("owner_registry_receipt_id", ""),
                     ("account_position_receipt_id", ""),
                     ("broker_unfilled_qty", 1), ("broker_unfilled_qty", False),
                     ("owner_registry_terminal", False),
                     ("account_position_reconciled", False),
                     ("filled_qty", 2), ("ordered_qty", True),
                     ("terminal_confirmed_at_epoch", start + 31)):
        forged = copy.deepcopy(states)
        forged[0][key] = bad
        assert next_bundle_timeout_action(
            plan, forged, now_epoch=start + 30)["action"] == "RECONCILE", key
    skipped = [{"state": "TERMINAL_SKIPPED", "terminal_confirmed": True,
                "terminal_confirmed_at_epoch": start + 25,
                "order_absence_confirmed": True,
                "order_absence_receipt_id": "attempt:1:leg:0:not-sent",
                "owner_registry_receipt_id": "owner:attempt:1:leg:0:absent",
                "skip_reason": "insufficient_time_for_cancel_confirmation"},
               {"state": "NOT_SUBMITTED"}]
    assert next_bundle_timeout_action(plan, skipped, now_epoch=start + 31)["action"] == "SUBMIT"
    skipped[0]["order_absence_receipt_id"] = ""
    assert next_bundle_timeout_action(plan, skipped, now_epoch=start + 31)["action"] == "RECONCILE"
    skipped[0]["order_absence_receipt_id"] = "attempt:1:leg:0:not-sent"
    skipped[0]["broker_order_no"] = "unexpected"
    assert next_bundle_timeout_action(plan, skipped, now_epoch=start + 31)["action"] == "RECONCILE"


def test_legacy_or_unbound_state_cannot_submit_a_successor_leg():
    plan = _schedule(legs=2, total=60, reserve=5)
    start = plan["order_start_at_epoch"]
    states = [{"state": "OPEN"}, {"state": "NOT_SUBMITTED"}]
    result = next_bundle_timeout_action(plan, states, now_epoch=start + 31)
    assert result["action"] == "RECONCILE"
    states[0]["broker_order_no"] = True
    assert next_bundle_timeout_action(plan, states, now_epoch=start + 31)["action"] == "RECONCILE"
    forged = {**plan, "policy_sha256": "b" * 64}
    assert next_bundle_timeout_action(forged, states, now_epoch=start)["action"] == (
        "BLOCK_INVALID_TIMEOUT_CONTRACT")


def _research_trade_path():
    decision_at = datetime.fromisoformat("2026-09-23T09:30:00+09:00")
    fill_at = decision_at + timedelta(seconds=5)
    trade = {
        "trade_id": "fact:1", "record_id": "1", "entry_date": "2026-09-23",
        "exit_date": "2026-09-23", "buy_price": 100.0, "sell_price": 102.0,
        "buy_qty": 4, "profit_rate": calculate_net_profit_rate(100, 102),
        "realized_net_pnl_krw": calculate_net_realized_pnl(100, 102, 4),
        "entry_at_fact_buy_time": fill_at.isoformat(),
        "exit_at": (decision_at + timedelta(minutes=4)).isoformat(),
    }
    path = {
        "source_gap": [],
        "decisions": [{"at": decision_at, "stage": "entry_execution_sizing_plan",
                       "fields": {"effective_venue": "KRX", "source_signature": "A",
                                  "reference_time": decision_at.isoformat(),
                                  "market_session_bucket": "krx_regular",
                                  "classifier_route_key": "KRX_0D",
                                  "classifier_transport_epoch": "epoch-1", "price_krw": 100}}],
        "fills": [{"at": fill_at, "price": 100.0, "qty": 4, "venue": "KRX",
                   "order_no": "101", "execution_no": "1",
                   "clock_source": "broker_execution_observed_at"}],
        "order_starts": [{"at": decision_at + timedelta(seconds=1),
                          "order_no": "101",
                          "source": "entry_cancel_wait_submission_context_frozen_at"}],
        "prices": [
            {"at": decision_at + timedelta(seconds=10), "price": 100.0,
             "venue": "KRX", "route": "KRX_0D", "epoch": "epoch-1"},
            {"at": decision_at + timedelta(seconds=20), "price": 100.0,
             "venue": "KRX", "route": "KRX_0D", "epoch": "epoch-1"},
            {"at": decision_at + timedelta(seconds=35), "price": 98.0,
             "venue": "KRX", "route": "KRX_0D", "epoch": "epoch-1"},
        ],
    }
    return trade, path


def test_timeout_research_uses_decision_to_following_lower_price_and_sequential_slots():
    trade, path = _research_trade_path()
    short = research._timeout_case(trade, path, shape="two_leg_0_1tick",
                                   horizon_sec=30, reserve_sec=5, policy_sha256="0" * 64)
    long = research._timeout_case(trade, path, shape="two_leg_0_1tick",
                                  horizon_sec=60, reserve_sec=5, policy_sha256="0" * 64)
    assert short["fill_state"] == "no_cross_observed"
    assert long["fill_state"] == "price_cross_conditional"
    assert long["verified_route_epoch_price_cross_count"] == 1
    assert long["first_post_fill_lower_elapsed_sec"] == 35
    assert long["order_start_at"] == (
        datetime.fromisoformat("2026-09-23T09:30:01+09:00").isoformat())
    assert long["candidate_net_pnl_krw"] > short["candidate_net_pnl_krw"]
    missing_second_slot = copy.deepcopy(path)
    missing_second_slot["prices"] = missing_second_slot["prices"][:1]
    assert research._timeout_case(
        trade, missing_second_slot, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)["status"] == "leg_window_source_gap"
    early_exit = {**trade, "exit_at": (
        datetime.fromisoformat("2026-09-23T09:30:00+09:00")
        + timedelta(seconds=25)).isoformat()}
    assert research._timeout_case(
        early_exit, path, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)["fill_state"] == "no_cross_observed"
    path["fills"][0]["clock_source"] = "position_rebased_emitted_at_proxy"
    proxy = research._timeout_case(trade, path, shape="two_leg_0_1tick",
                                   horizon_sec=60, reserve_sec=5, policy_sha256="0" * 64)
    assert proxy["verified_route_epoch_price_cross_count"] == 0


def test_timeout_research_requires_matching_order_start_receipt():
    trade, path = _research_trade_path()
    path["order_starts"][0]["order_no"] = "different-order"
    assert research._timeout_case(
        trade, path, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)["status"] == "order_start_receipt_missing"


def test_second_precision_broker_fill_can_follow_same_second_order_start():
    trade, path = _research_trade_path()
    second = path["decisions"][0]["at"]
    path["decisions"][0]["at"] = second + timedelta(milliseconds=174)
    path["order_starts"][0]["at"] = second + timedelta(milliseconds=744)
    path["fills"][0]["at"] = second
    path["fills"][0]["emitted_at"] = second + timedelta(seconds=1)
    path["fills"][0]["clock_precision_sec"] = 1
    modeled = research._timeout_case(
        trade, path, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)
    assert modeled["status"] == "modeled"
    assert modeled["quantity_type"] == "KRX_THIN_HIGH_TICK"
    assert modeled["order_start_at"] == (
        second + timedelta(milliseconds=744)).isoformat()
    path["fills"][0]["clock_precision_sec"] = 0
    assert research._timeout_case(
        trade, path, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)["status"] == "decision_clock_missing"


def test_native_pipeline_request_and_sent_bound_order_start_by_attempt(tmp_path):
    day = "2026-09-23"
    root = tmp_path / "pipeline_events"
    root.mkdir()
    path = root / f"pipeline_events_{day}.jsonl"
    identity = {"entry_submit_attempt_id": "attempt-1",
                "entry_execution_sizing_plan_sha256": "a" * 64,
                "tag": "entry_split_probe_0"}
    events = [
        {"record_id": 1, "stock_code": "000001", "stage": "order_leg_request",
         "emitted_at": f"{day}T09:30:00.200000+09:00", "fields": identity},
        {"record_id": 1, "stock_code": "000001", "stage": "order_leg_sent",
         "emitted_at": f"{day}T09:30:00.600000+09:00",
         "fields": {**identity, "broker_order_no": "101",
                    "actual_order_submitted": "True"}},
        {"record_id": 1, "stock_code": "000001", "stage": "position_rebased_after_fill",
         "emitted_at": f"{day}T09:30:00.900000+09:00",
         "fields": {"entry_mode": "normal", "fill_price": "100",
                    "fill_qty": "4", "order_no": "101",
                    "broker_execution_observed_at": f"{day}T09:30:00+09:00"}},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in events))
    trade = {"trade_id": "fact:1", "record_id": "1", "entry_date": day,
             "stock_code": "000001", "entry_at_fact_buy_time": f"{day}T09:30:00+09:00",
             "exit_at": f"{day}T09:35:00+09:00", "buy_qty": 4}
    joined = join_post_fill_paths([trade], data_dir=tmp_path,
                                  price_horizon_seconds=1200)["fact:1"]
    assert joined["order_starts"] == [{
        "at": datetime.fromisoformat(f"{day}T09:30:00.200000+09:00"),
        "latest_at": datetime.fromisoformat(f"{day}T09:30:00.600000+09:00"),
        "order_no": "101", "probe_applied": True,
        "source": "order_leg_request_to_sent_bracket"}]
    assert joined["fills"][0]["clock_precision_sec"] == 1
    duplicate_sent = copy.deepcopy(events[1])
    duplicate_sent["fields"]["broker_order_no"] = "102"
    path.write_text("".join(json.dumps(row) + "\n"
                            for row in [*events, duplicate_sent]))
    ambiguous = join_post_fill_paths([trade], data_dir=tmp_path)["fact:1"]
    assert ambiguous["order_starts"] == []


def test_probe_one_share_is_first_slot_before_candidate_split_legs():
    trade, path = _research_trade_path()
    decision_at = path["decisions"][0]["at"]
    path["order_starts"][0]["probe_applied"] = True
    path["fills"][0]["qty"] = 1
    path["fills"].append({"at": decision_at + timedelta(seconds=6),
                          "price": 100.0, "qty": 3, "venue": "KRX",
                          "order_no": "102", "execution_no": "2",
                          "clock_source": "broker_execution_observed_at"})
    path["prices"].append({"at": decision_at + timedelta(seconds=45),
                           "price": 97.0, "venue": "KRX", "route": "KRX_0D",
                           "epoch": "epoch-1"})
    modeled = research._timeout_case(
        trade, path, shape="two_leg_0_1tick", horizon_sec=60,
        reserve_sec=5, policy_sha256="0" * 64)
    assert modeled["status"] == "modeled"
    assert modeled["probe_included_in_leg_count"] is True
    assert modeled["modeled_leg_count"] == 3
    assert modeled["conditional_crossed_leg_count"] == 2


def test_timeout_research_counts_primary_miss_in_parent_trade_denominator():
    trade, path = _research_trade_path()
    decision_at = path["decisions"][0]["at"]
    path["fills"][0]["at"] = decision_at + timedelta(seconds=20)
    missed = research._timeout_case(
        trade, path, shape="two_leg_0_1tick", horizon_sec=30,
        reserve_sec=5, policy_sha256="0" * 64)
    assert missed["status"] == "modeled"
    assert missed["fill_state"] == "primary_missed"
    assert missed["candidate_net_pnl_krw"] == 0.0
    assert missed["parent_net_pnl_krw"] == trade["realized_net_pnl_krw"]


def test_timeout_research_retains_completed_denominator_when_source_blocked(monkeypatch):
    trade, path = _research_trade_path()
    blocked = {**trade, "trade_id": "fact:2", "record_id": "2"}
    census = {
        "all_completed_initial_trades": 2,
        "input_fact_rows": [trade, blocked],
        "input_manifest_sha256": _digest([trade, blocked]),
        "source_quality_by_entry_date": {"2026-09-23": {"tuning_input_allowed": True}},
        "source_quality_by_exit_date": {"2026-09-23": {"tuning_input_allowed": True}},
    }
    monkeypatch.setattr(research, "completed_trade_fact_census",
                        lambda *_a, **_k: ([trade, blocked], census))
    monkeypatch.setattr(research, "join_post_fill_paths",
                        lambda *_a, **_k: {"fact:1": path})
    report = research.build_timeout_research(
        "2026-09-23", horizons=(30, 60), reserves=(5,))
    assert report["census"]["all_completed_initial_trades"] == 2
    assert report["quantity_type_counts"] == {"KRX_THIN_HIGH_TICK": 1, "SAFE_UNKNOWN": 1}
    assert report["selections"]["KRX_THIN_HIGH_TICK"]["first_post_fill_lower_count"] == 1
    winner = report["selections"]["KRX_THIN_HIGH_TICK"]
    assert winner["winner_count"] == 1
    assert winner["winner_weight_sum_krw"] == trade["realized_net_pnl_krw"]
    assert winner["winner_weighted_parent_ev_pct"] == round(trade["profit_rate"], 6)
    assert winner["winner_weighted_first_post_fill_lower_sec"] == 35
    assert winner["candidate_metrics"]["two_leg_0_1tick:5:60"][
        "winner_modeled_count"] == 1
    assert report["selections"]["KRX_THIN_HIGH_TICK"]["decision_to_order_start_count"] == 1
    assert report["runtime_apply_allowed"] is False
    assert report["selections"]["KRX_THIN_HIGH_TICK"]["policy_selected_total_wait_sec"] is None
    assert research.timeout_research_valid(report)
    forged = copy.deepcopy(report)
    forged["selections"]["KRX_THIN_HIGH_TICK"]["candidate_metrics"][
        "two_leg_0_1tick:5:60"]["verified_cross_count"] = 2
    forged["report_content_sha256"] = _digest({
        key: value for key, value in forged.items() if key != "report_content_sha256"})
    assert not research.timeout_research_valid(forged)
    forged_source = copy.deepcopy(report)
    forged_source["selections"]["KRX_THIN_HIGH_TICK"]["candidate_metrics"][
        "two_leg_0_1tick:5:60"]["order_start_source_counts"] = {}
    forged_source["report_content_sha256"] = _digest({
        key: value for key, value in forged_source.items()
        if key != "report_content_sha256"})
    assert not research.timeout_research_valid(forged_source)
    no_start = copy.deepcopy(path)
    no_start["order_starts"] = []
    monkeypatch.setattr(research, "join_post_fill_paths",
                        lambda *_a, **_k: {"fact:1": no_start})
    report_without_start = research.build_timeout_research(
        "2026-09-23", horizons=(30, 60), reserves=(5,))
    assert report_without_start["selections"]["KRX_THIN_HIGH_TICK"][
        "first_post_fill_lower_count"] == 1
    assert report_without_start["selections"]["KRX_THIN_HIGH_TICK"][
        "decision_to_order_start_count"] == 0
