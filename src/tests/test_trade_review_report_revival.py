import hashlib
import json
import pytest

from src.engine import sniper_trade_review_report as report_mod


@pytest.fixture(autouse=True)
def _isolate_saved_structured_partition(monkeypatch, request):
    """Unit builders must not absorb the host's preserved trading archive."""

    if request.node.name == "test_structured_trailing_projection_flags_wrong_partition_and_missing_id":
        return
    monkeypatch.setattr(
        report_mod, "_load_holding_projection_events_from_structured",
        lambda _date: ([], "source_gap_structured_partition_missing", []),
    )


def test_retired_preset_profit_rule_keeps_historical_attribution():
    assert report_mod._normalize_exit_rule("scalp_preset_protect_profit") == "scalp_preset_protect_profit"
    assert report_mod._infer_exit_rule_from_reason("SCALP 출구엔진 보호선 이탈") == "scalp_preset_protect_profit"
    assert report_mod._infer_exit_decision_source(
        exit_rule="scalp_preset_protect_profit"
    ) == "PRESET_PROTECT"


def test_trailing_transitions_survive_timeline_and_projection():
    events = [
        report_mod.HoldingEvent(
            timestamp=f"2026-09-24 09:00:0{index}",
            name="TEST",
            code="123456",
            stage="scalp_trailing_input_transition",
            fields={"id": "1", "armed": str(index == 1)},
            raw_line="",
        )
        for index in (0, 1)
    ]

    timeline = report_mod._build_timeline(events)

    assert len(timeline) == 2
    assert [row["fields"]["armed"] for row in timeline] == ["False", "True"]
    assert "scalp_trailing_input_transition" in report_mod._PROJECTION_EVENT_STAGES
    assert "scalp_tp_alternative_observed" in report_mod._PROJECTION_EVENT_STAGES


def test_shared_rebound_lineage_keeps_one_position_cost_and_exact_decision_join():
    def event(stage, **fields):
        return report_mod.HoldingEvent(
            "2026-09-29 10:00:00", "TEST", "047040", stage,
            {"id": "48376", **fields}, "",
        )

    events = [
        event("avg_down_shared_rebound_blocked",
              reason="shared_main_rebound_input_preflight_blocked",
              preflight_primary_blocker="tick_context_stale"),
        event("holding_path_signal_snapshot", path_id="ADD_REBOUND",
              signal_id="signal-1", decision="PASS", buy_fill_identity="identity-1"),
        event("avg_down_shared_rebound_signal", source_signal_id="signal-1",
              position_episode_id="episode-1", scale_in_decision_id="decision-1",
              buy_fill_identity="identity-1", machine_bundle_sha256="b" * 64),
        event("scale_in_order_submitted", add_trigger="shared_main_rebound_entry",
              actual_order_submitted=True, position_episode_id="episode-1",
              scale_in_decision_id="decision-1", broker_order_no_list="0029199",
              submitted_qty=1),
        event("scale_in_executed", add_reason="shared_main_rebound_entry",
              actual_order_submitted=True, position_episode_id="episode-1",
              scale_in_decision_id="decision-1", order_no="0029199",
              execution_no="131200", fill_qty=1),
    ]
    trade = {"id": 48376, "code": "047040", "strategy": "SCALPING"}
    terminal = {"strict_completion_status": "eligible", "fill_cost_reconciled": True,
                "realized_pnl_krw": 120, "profit_rate": 0.6,
                "cost_basis": "broker_fill_prices_configured_cost_rate"}
    result = report_mod._avg_down_rebound_lineage(trade, events, terminal)
    assert result["decision_rows"][0]["status"] == "completed_exact_cost"
    assert result["decision_rows"][0]["exact_fill_legs"] == [
        {"order_no": "0029199", "execution_no": "131200", "qty": 1}
    ]
    assert result["position_terminal"]["realized_pnl_krw"] == 120
    assert "realized_pnl_krw" not in result["decision_rows"][0]
    assert result["incremental_add_effect_status"] == "unidentified_without_paired_no_add"
    assert result["blocker_counts"] == [{"reason": "shared_main_rebound_input_preflight_blocked",
                                          "primary_blocker": "tick_context_stale", "count": 1}]
    json.dumps(result)


def test_shared_rebound_lineage_does_not_join_unrelated_fill_or_invent_cost():
    def event(stage, **fields):
        return report_mod.HoldingEvent("2026-09-29 10:00:00", "TEST", "047040",
                                       stage, {"id": "48376", **fields}, "")
    events = [
        event("avg_down_shared_rebound_signal", source_signal_id="signal-1",
              position_episode_id="episode-1", scale_in_decision_id="decision-1"),
        event("scale_in_executed", add_reason="shared_main_rebound_entry",
              actual_order_submitted=True, position_episode_id="episode-other",
              scale_in_decision_id="decision-2", order_no="0029199",
              execution_no="131200", fill_qty=1),
    ]
    result = report_mod._avg_down_rebound_lineage(
        {"id": 48376, "code": "047040", "strategy": "SCALPING"}, events,
        {"strict_completion_status": "eligible", "fill_cost_reconciled": False,
         "realized_pnl_krw": None, "profit_rate": None},
    )
    assert result["unjoined_fill_count"] == 1
    assert result["decision_rows"][0]["status"] == "lineage_gap_valid_vote"
    assert result["position_terminal"]["realized_pnl_krw"] is None


def test_shared_rebound_lineage_separates_partial_add_fill_from_full_fill():
    def event(stage, **fields):
        return report_mod.HoldingEvent("2026-09-29 10:00:00", "TEST", "047040",
                                       stage, {"id": "48376", **fields}, "")
    events = [
        event("holding_path_signal_snapshot", path_id="ADD_REBOUND",
              signal_id="signal-1", decision="PASS", buy_fill_identity="identity-1"),
        event("avg_down_shared_rebound_signal", source_signal_id="signal-1",
              position_episode_id="episode-1", scale_in_decision_id="decision-1",
              buy_fill_identity="identity-1"),
        event("scale_in_order_submitted", add_trigger="shared_main_rebound_entry",
              actual_order_submitted=True, position_episode_id="episode-1",
              scale_in_decision_id="decision-1", broker_order_no_list="0029199",
              submitted_qty=2),
        event("scale_in_executed", add_reason="shared_main_rebound_entry",
              actual_order_submitted=True, position_episode_id="episode-1",
              scale_in_decision_id="decision-1", order_no="0029199",
              execution_no="131200", fill_qty=1),
    ]
    terminal = {"strict_completion_status": "eligible", "fill_cost_reconciled": True,
                "realized_pnl_krw": 120, "profit_rate": 0.6}
    result = report_mod._avg_down_rebound_lineage(
        {"id": 48376, "code": "047040", "strategy": "SCALPING"}, events, terminal,
    )
    decision = result["decision_rows"][0]
    assert decision["fill_quality"] == "partial"
    assert decision["exact_filled_qty"] == 1
    assert decision["status"] == "partial_fill_completed_exact_cost"
    assert result["incremental_add_effect_status"] == "unidentified_without_paired_no_add"


def test_structured_trailing_projection_flags_wrong_partition_and_missing_id(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    path = tmp_path / "pipeline_events" / "pipeline_events_2026-09-24.jsonl"
    path.parent.mkdir(parents=True)
    base = {
        "pipeline": "HOLDING_PIPELINE",
        "stage": "scalp_trailing_input_transition",
        "emitted_at": "2026-09-24T09:00:00+09:00",
        "storage_partition_date": "2026-09-24",
        "record_id": 123,
        "fields": {"transition_sequence": 1},
        "stock_code": "123456",
    }
    wrong_partition = {**base, "storage_partition_date": "2026-09-23"}
    missing_id = {**base, "record_id": None}
    path.write_text("\n".join(json.dumps(row) for row in (
        base, wrong_partition, missing_id
    )) + "\n")

    events, status, receipts = (
        report_mod._load_holding_projection_events_from_structured("2026-09-24")
    )
    assert len(events) == 1
    assert events[0].fields["id"] == "123"
    assert status == "source_gap_structured_projection_malformed"
    assert receipts[0]["logical_sha256"]


def test_completed_projection_keeps_full_population_beyond_display_limit(monkeypatch):
    trades = [
        {
            "id": index,
            "rec_date": "2026-09-23",
            "code": f"{index:06d}",
            "name": "test",
            "status": "COMPLETED",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 10000,
            "buy_qty": 1,
            "buy_time": "2026-09-23 09:00:00",
            "sell_price": 10100,
            "sell_time": "2026-09-23 09:10:00",
            "profit_rate": 0.77,
            "realized_pnl_krw": 77,
        }
        for index in range(1, 13)
    ]
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", lambda *_: (trades, []))
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda *_args, **_kw: [])
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *_args: None
    )

    result = report_mod.build_trade_review_report("2026-09-23")

    assert len(result["sections"]["recent_trades"]) == 10
    projection = result["sections"]["completed_trade_projection"]
    assert len(projection) == 12
    assert {row["id"] for row in projection} == set(range(1, 13))
    assert result["metrics"]["canonical_completed_trades"] == 12


def test_completed_projection_requires_exact_receipt_for_cost_and_fill_time():
    base = {
        "id": 1,
        "rec_date": "2026-09-23",
        "code": "123456",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 1,
        "buy_time": "2026-09-23 09:00:00",
        "sell_time": "2026-09-23 09:10:02",
        "profit_rate": 0.4,
        "realized_pnl_krw": 50,
        "realized_pnl_krw_source": "price_cost_model",
    }
    event = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:10:02",
        name="test",
        code="123456",
        stage="sell_completed",
        fields={
            "id": "1",
            "decision_authority": "broker_sell_fill_observation_only",
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "order_no": "S1",
            "execution_no": "SE1",
            "main_lifecycle_exit_qty": "1",
            "main_lifecycle_exit_price": "10050",
            "remaining_sell_qty": "0",
            "sell_execution_receipt_economics_complete": "True",
            "sell_execution_receipt_quantity_contract_complete": "True",
            "sell_execution_receipt_unit_fill_consistent": "True",
            "main_lifecycle_fees_taxes_krw": "10",
            "main_lifecycle_realized_net_pnl_krw": "40",
            "entry_opportunity_recheck_cost_rate": "0.001",
            "actual_order_submitted": "True",
            "broker_order_forbidden": "False",
            "cumulative_sell_qty": "1",
            "buy_qty": "1",
            "profit_rate": "0.4",
            "realized_pnl_krw_source": "broker_fill_prices_fee_aware",
            "realized_pnl_krw": "40",
            "main_lifecycle_execution_occurrence_time_source": "official_fid_908",
            "main_lifecycle_execution_occurred_at": "2026-09-23T09:10:01+09:00",
            "broker_actual_execution_venue": "UNKNOWN",
            "broker_actual_execution_venue_source": (
                "official_exchange_fields_ambiguous_or_missing"
            ),
            "broker_actual_exchange_code": "0",
            "broker_actual_exchange_name": "SOR",
            "broker_sor_flag": "Y",
        },
        raw_line="",
    )
    buy_event = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:00:00",
        name="test", code="123456", stage="position_rebased_after_fill",
        fields={
            "id": "1", "order_no": "B1", "execution_no": "BE1",
            "fill_qty": "1", "order_filled_qty": "1",
            "order_requested_qty": "1", "order_remaining_qty": "0",
            "fill_price": "10000", "fill_quality": "FULL_FILL",
            "receipt_economics_complete": "True",
            "receipt_quantity_contract_complete": "True",
            "receipt_unit_fill_consistent": "True",
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
            "pipeline_lifecycle_population_scope": "real_record_bound",
        }, raw_line="",
    )

    direct = report_mod._completed_trade_projection(base, [buy_event, event], base)

    assert direct["realized_pnl_krw"] is None
    assert direct["exact_sell_fill_time"] == "2026-09-23T09:10:01+09:00"
    assert direct["strict_completion_status"] == "excluded"
    assert direct["broker_actual_execution_venue"] == "UNKNOWN"
    assert direct["broker_actual_exchange_code"] == "0"
    assert direct["broker_actual_exchange_name"] == "SOR"
    assert direct["broker_sor_flag"] == "Y"
    assert direct["configured_fee_estimate_krw"] == 10
    assert direct["broker_actual_fees_taxes_krw"] is None
    assert direct["broker_actual_cost_observed"] is False
    assert direct["configured_cost_estimated_pnl_krw"] == 40
    assert direct["realized_pnl_krw"] is None
    assert direct["strict_completion_status"] == "excluded"
    assert "source_gap_broker_actual_cost_missing" in direct["strict_completion_reasons"]

    event.fields["main_lifecycle_execution_occurrence_time_source"] = "missing"
    no_clock = report_mod._completed_trade_projection(base, [buy_event, event], base)
    assert no_clock["strict_completion_status"] == "excluded"
    assert no_clock["realized_pnl_krw"] is None
    assert no_clock["exact_sell_fill_time"] is None

    event.fields["main_lifecycle_fees_taxes_krw"] = "0"
    no_cost = report_mod._completed_trade_projection(base, [buy_event, event], base)
    assert no_cost["strict_completion_status"] == "excluded"
    assert "source_gap_exact_cost_missing" in no_cost["strict_completion_reasons"]
    event.fields["main_lifecycle_fees_taxes_krw"] = "10"

    event.fields["decision_authority"] = "broker_balance_reconciliation_only"
    event.fields["sell_time_precision"] = "order_second_not_fill_second"
    event.fields["sell_time_forbidden_for_intraday_horizon"] = "True"
    sync_only = report_mod._completed_trade_projection(base, [buy_event, event], base)

    assert sync_only["realized_pnl_krw"] is None
    assert sync_only["modeled_realized_pnl_krw"] == 50
    assert sync_only["exact_sell_fill_time"] is None
    assert sync_only["sell_time_forbidden_for_intraday_horizon"] is True


def test_balance_reconciled_completion_preserves_missing_execution_and_cost():
    trade = {"id": 47531, "rec_date": "2026-09-23", "code": "010060",
             "status": "COMPLETED", "strategy": "SCALPING",
             "buy_price": 195100, "buy_qty": 1, "sell_price": 201000,
             "sell_time": "", "profit_rate": 2.79,
             "realized_pnl_krw": 5438,
             "realized_pnl_krw_source": "price_cost_model"}
    submitted = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:07:00", name="OCI", code="010060",
        stage="sell_order_sent", fields={"id": "47531",
            "broker_order_no": "0012375", "broker_route": "SOR",
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
            "attempt_id": "A1", "main_lifecycle_id": "M1"}, raw_line="")
    reconciled = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:07:59", name="OCI", code="010060",
        stage="sell_completed", fields={"id": "47531",
            "sell_order_no": "0012375", "sell_qty": "1",
            "decision_authority": "broker_balance_reconciliation_only",
            "reconciliation_result": "broker_exact_order_fill_recovered",
            "execution_match_reason": (
                "unique_owner_cycle_kt00007_terminal_sell_execution"),
            "sell_time_precision": "order_second_not_fill_second",
            "realized_pnl_krw": "5438"}, raw_line="")
    row = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert row["sell_terminal_source_status"] == "balance_reconciled_price_only"
    assert row["sell_reconciliation_order_no"] == "0012375"
    assert row["sell_submission_identity_status"] == "matched_source_only"
    assert row["sell_submission_attempt_id"] == "A1"
    assert row["sell_submission_lifecycle_id"] == "M1"
    assert row["sell_execution_no"] is None
    assert row["broker_actual_fees_taxes_krw"] is None
    assert row["configured_fee_estimate_krw"] is None
    assert row["realized_pnl_krw"] is None
    assert row["strict_completion_status"] == "excluded"
    assert row["sell_reconciliation_generation_status"] == "legacy_unbound"

    assert "sell_completion_reconciliation_gap" in report_mod._PROJECTION_EVENT_STAGES
    assert "sell_cancel_reconciliation_deferred" in report_mod._PROJECTION_EVENT_STAGES
    deferred = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:07:49", name="OCI", code="010060",
        stage="sell_cancel_reconciliation_deferred", fields={"id": "47531"},
        raw_line="")
    pending = report_mod._completed_trade_projection(
        trade, [submitted, deferred, reconciled], trade)
    assert pending["sell_cancel_deferred_event_count"] == 1
    assert pending["realized_pnl_krw"] is None
    contract = {
        "schema": "sell_balance_reconciliation_source_v1",
        "source_api": "kt00007", "source_date": "2026-09-23",
        "record_id": 47531, "stock_code": "010060",
        "order_no": "0012375", "order_time": "090700",
        "submitted_qty": 1, "filled_qty": 1, "remaining_qty": 0,
        "execution_price": 201000, "broker_route": "SOR",
        "broker_sor_flag": "Y", "owner_buy_time": "2026-09-23T08:38:32",
        "broker_snapshot_at": "2026-09-23T09:07:59+09:00",
    }
    raw = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    reconciled.fields.update(
        sell_price="201000", sell_reconciliation_source_date="2026-09-23",
        sell_reconciliation_source_contract=raw,
        sell_reconciliation_normalized_sha256=hashlib.sha256(
            raw.encode()).hexdigest(),
        configured_fee_estimate_krw="462",
    )
    bound = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert bound["sell_reconciliation_generation_status"] == (
        "normalized_contract_bound")
    assert bound["configured_fee_estimate_krw"] == 462
    assert bound["broker_actual_fees_taxes_krw"] is None
    assert bound["realized_pnl_krw"] is None
    reconciled.timestamp = "2026-09-24 00:00:02"
    after_midnight = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert after_midnight["sell_reconciliation_generation_status"] == (
        "normalized_contract_bound")
    assert after_midnight["completion_observed_date"] == "2026-09-24"
    reconciled.timestamp = "2026-09-23 09:07:59"
    reconciled.fields["sell_reconciliation_source_date"] = "2026-09-22"
    stale = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert stale["sell_reconciliation_generation_status"] == "invalid"
    assert stale["configured_fee_estimate_krw"] is None

    reconciled.fields["sell_reconciliation_source_date"] = "2026-09-23"
    wrong_price = report_mod._completed_trade_projection(
        {**trade, "sell_price": 202000}, [submitted, reconciled], trade)
    assert wrong_price["sell_reconciliation_generation_status"] == "invalid"
    submitted.fields["broker_order_no"] = "OTHER"
    wrong_order = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert wrong_order["sell_submission_identity_status"] == "missing"
    assert wrong_order["configured_fee_estimate_krw"] is None
    submitted.fields["broker_order_no"] = "0012375"
    submitted.fields["broker_route"] = "NXT"
    wrong_route = report_mod._completed_trade_projection(
        trade, [submitted, reconciled], trade)
    assert wrong_route["sell_reconciliation_generation_status"] == (
        "submission_route_conflict")
    assert wrong_route["configured_fee_estimate_krw"] is None
    submitted.fields["broker_route"] = "SOR"
    conflicting_duplicate = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:07:01", name="OCI", code="010060",
        stage="sell_order_sent", fields={**submitted.fields, "qty": "2"},
        raw_line="")
    conflicted = report_mod._completed_trade_projection(
        trade, [submitted, conflicting_duplicate, reconciled], trade)
    assert conflicted["sell_submission_identity_status"] == "conflicting"
    assert conflicted["configured_fee_estimate_krw"] is None

    gap = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:08:00", name="OCI", code="010060",
        stage="sell_completion_reconciliation_gap",
        fields={"id": "47531", "decision_authority": (
            "broker_balance_reconciliation_only"),
            "reconciliation_result": "broker_holding_absent_fill_receipt_missing"},
        raw_line="",
    )
    missing = report_mod._completed_trade_projection(
        trade, [submitted, gap], trade)
    assert missing["sell_terminal_source_status"] == "balance_absent_receipt_missing"
    assert missing["realized_pnl_krw"] is None


def test_completed_execution_ledger_requires_buy_fill_and_conserves_all_sell_legs():
    def event(stage, second, **fields):
        return report_mod.HoldingEvent(
            timestamp=f"2026-09-24 09:00:{second:02d}", name="test",
            code="123456", stage=stage,
            fields={"pipeline_lifecycle_population_scope": "real_record_bound",
                    "actual_order_submitted": "True",
                    "broker_order_forbidden": "False",
                    "sell_receipt_economics_complete": "True",
                    "sell_receipt_quantity_contract_complete": "True",
                    "sell_receipt_unit_fill_consistent": "True",
                    "sell_execution_receipt_economics_complete": "True",
                    "sell_execution_receipt_quantity_contract_complete": "True",
                    "sell_execution_receipt_unit_fill_consistent": "True",
                    "main_lifecycle_fees_taxes_krw": "10",
                    "main_lifecycle_realized_net_pnl_krw": "40", **fields}, raw_line="",
        )

    buy_base = {
        "order_no": "B1", "order_requested_qty": "2", "fill_price": "10000",
        "receipt_economics_complete": "True",
        "receipt_quantity_contract_complete": "True",
        "receipt_unit_fill_consistent": "True",
    }
    events = [
        event("position_rebased_after_fill", 1, **buy_base, execution_no="BEX1",
              fill_qty="1", order_filled_qty="1", order_remaining_qty="1"),
        event("position_rebased_after_fill", 2, **buy_base, execution_no="BEX2",
              fill_qty="1", order_filled_qty="2", order_remaining_qty="0"),
        event("sell_partial_fill_progress", 3, order_no="S1", execution_no="SEX1",
              main_lifecycle_exit_qty="1", main_lifecycle_exit_price="10050",
              cumulative_sell_qty="1", remaining_sell_qty="1"),
        event("sell_completed", 4, order_no="S1", execution_no="SEX2",
              main_lifecycle_exit_qty="1", main_lifecycle_exit_price="10060",
              cumulative_sell_qty="2", remaining_sell_qty="0"),
    ]
    trade = {"buy_qty": 2, "buy_price": 10000}
    ledger = report_mod._completed_execution_ledger(trade, events)
    assert ledger["strict_completion_status"] == "eligible"
    assert ledger["buy_filled_qty"] == ledger["sell_filled_qty"] == 2
    assert ledger["sell_fill_amount"] == 20110
    assert ledger["sell_fill_fees_taxes_krw"] == 20

    second_order = event(
        "sell_completed", 4, order_no="S2", execution_no="SEX2",
        main_lifecycle_exit_qty="1", main_lifecycle_exit_price="10060",
        cumulative_sell_qty="2", remaining_sell_qty="0",
    )
    multi_order = report_mod._completed_execution_ledger(
        trade, events[:-1] + [second_order]
    )
    assert multi_order["strict_completion_status"] == "eligible"
    assert multi_order["sell_order_count"] == 2

    no_buy = report_mod._completed_execution_ledger(trade, events[2:])
    assert "source_gap_buy_fill_missing" in no_buy["strict_completion_reasons"]
    duplicate = report_mod._completed_execution_ledger(trade, events[:2] + [events[1]] + events[2:])
    assert "source_gap_duplicate_buy_execution" in duplicate["strict_completion_reasons"]
    partial = report_mod._completed_execution_ledger(trade, events[:-1])
    assert "source_gap_position_quantity_not_conserved" in partial["strict_completion_reasons"]

    # A later BUY cannot retroactively fund an earlier SELL even when totals match.
    late_buy = event("position_rebased_after_fill", 5, **buy_base,
                     execution_no="BEX2", fill_qty="1", order_filled_qty="2",
                     order_remaining_qty="0")
    out_of_order = report_mod._completed_execution_ledger(
        trade, [events[0], late_buy, events[2], events[3]]
    )
    assert "source_gap_negative_position_balance" in out_of_order["strict_completion_reasons"]


def test_buy_parent_handoff_requires_exact_owner_and_conserves_filled_not_planned_qty():
    day = "2026-09-28"
    def sent(order, intent, record=42, owner="main_scalping:42", account="acct-a"):
        return {"stage": "order_leg_sent", "emitted_date": day,
                "record_id": record, "stock_code": "123456",
                "emitted_at": day + "T09:00:00+09:00", "fields": {
                    "actual_order_submitted": "True", "broker_order_no": order,
                    "requested_qty": "2", "submitted_qty": "2",
                    "buy_planned_qty": "3",
                    "entry_submit_attempt_id": "attempt-42", "buy_parent_id": "attempt-42",
                    "buy_child_id": "attempt-42:probe", "owner_registry_intent_id": intent,
                    "buy_owner_type": "main_scalping", "buy_owner_id": owner,
                    "buy_account_key": account, "broker_route": "SOR",
                    "market_session_bucket": "krx_regular"}}
    def journal(intent="intent-1", owner="main_scalping:42", account="acct-a"):
        return [{"event": "ORDER_BOUND", "intent_id": intent,
                 "owner_type": "main_scalping", "owner_id": owner,
                 "account_key": account, "order_date": day, "side": "BUY",
                 "action": "NEW", "broker_order_no": "B1", "symbol": "123456",
                 "route": "SOR", "quantity": 2, "state": "ORDER_BOUND"},
                {"event": "FILL_RECORDED", "intent_id": intent,
                 "owner_type": "main_scalping", "owner_id": owner,
                 "account_key": account, "order_date": day, "side": "BUY",
                 "action": "NEW", "broker_order_no": "B1", "symbol": "123456",
                 "route": "SOR", "quantity": 2, "filled_qty": 1,
                 "execution_no": "E1", "state": "ORDER_BOUND"}]
    fill = report_mod.HoldingEvent(day + " 09:00:01", "x", "123456",
        "position_rebased_after_fill", {"id": "42", "order_no": "B1",
        "execution_no": "E1", "fill_qty": "1", "order_requested_qty": "2",
        "order_filled_qty": "1", "order_remaining_qty": "1",
        "pipeline_lifecycle_population_scope": "real_record_bound",
        "actual_order_submitted": "True", "broker_order_forbidden": "False"}, "")
    result = report_mod._buy_parent_handoff_projection(day, [sent("B1", "intent-1")],
        journal(), [fill], [{"id": 42, "code": "123456", "buy_qty": 1,
                            "status": "HOLDING"}])
    assert result["counts"] == {"raw": 1, "valid": 1, "excluded": 0,
                                "quarantined": 0, "unobserved": 0}
    row = result["rows"][0]
    assert row["filled_qty"] == row["sellable_qty"] == 1
    assert row["unsubmitted_qty"] == 1
    assert row["state"] == "partial_open"
    assert row["cost_krw"] is None
    assert row["execution_ids"] == ["E1"]
    assert report_mod._buy_parent_handoff_projection(day, [sent("B1", "intent-1")],
        journal(owner="episode:1"), [fill], [])["rows"][0]["sellable_qty"] is None
    assert report_mod._buy_parent_handoff_projection(day, [sent("B1", "intent-1")],
        journal(), [], [])["rows"][0]["sellable_qty"] is None
    assert report_mod._buy_parent_handoff_projection(day, [sent("B1", "")],
        journal(), [fill], [])["rows"][0]["parent_id"] is None
    duplicate = sent("B1", "intent-1")
    duplicate["fields"]["broker_route"] = "NXT"
    conflict = report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1"), duplicate], journal(), [fill],
        [{"id": 42, "code": "123456", "buy_qty": 1, "status": "HOLDING"}])
    assert conflict["counts"]["valid"] == 0
    assert conflict["counts"]["quarantined"] == 2
    assert all(row["sellable_qty"] is None for row in conflict["rows"])

    terminal = report_mod.HoldingEvent(day + " 09:00:02", "x", "123456",
        "entry_buy_order_terminal_confirmed", {"id": "42", "orig_ord_no": "B1",
        "order_requested_qty": "2", "order_filled_qty": "1",
        "terminal_reason": "terminal_absence_and_inventory_exact"}, "")
    closed_journal = journal() + [{**journal()[0], "event": "STATE_TRANSITION",
        "state": "ORDER_TERMINAL", "terminal_reconciliation": True}]
    sale = report_mod.HoldingEvent(day + " 09:00:03", "x", "123456",
        "sell_partial_fill_progress", {"id": "42", "order_no": "S1",
        "execution_no": "SE1", "main_lifecycle_exit_qty": "1",
        "cumulative_sell_qty": "1",
        "pipeline_lifecycle_population_scope": "real_record_bound",
        "actual_order_submitted": "True", "broker_order_forbidden": "False"}, "")
    closed = report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1")], closed_journal, [fill, terminal, sale],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "SELL_ORDERED"}])["rows"][0]
    assert closed["state"] == "partial_terminal"
    assert closed["sellable_qty"] == 0
    pending = report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1")], journal(), [fill, sale],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "SELL_ORDERED"}])["rows"][0]
    assert pending["state"] == "partial_open"
    assert pending["sellable_qty"] == 0
    cancel = {"stage": "entry_order_cancel_requested", "emitted_date": day,
        "record_id": 42, "fields": {"orig_ord_no": "B1"}}
    cancel_ack = {**cancel, "stage": "entry_order_cancel_confirmed"}
    cancel_pending = report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1"), cancel], journal(), [fill],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "HOLDING"}])["rows"][0]
    assert cancel_pending["state"] == "cancel_pending"
    ack_pending = report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1"), cancel, cancel_ack], journal(), [fill],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "HOLDING"}])["rows"][0]
    assert ack_pending["state"] == "cancel_ack_terminal_pending"
    simulated = report_mod.HoldingEvent(fill.timestamp, fill.name, fill.code,
        fill.stage, {**fill.fields,
        "pipeline_lifecycle_population_scope": "sim_observation_only"}, "")
    assert report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1")], journal(), [simulated],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "HOLDING"}])["rows"][0]["sellable_qty"] is None
    legacy = sent("B1", "")
    legacy["fields"].update(buy_registry_mode="single_owner_unregistered",
        buy_owner_policy_date=day, buy_owner_policy_selected=False,
        buy_owner_policy_coexistence=False,
        buy_owner_policy_reason="exact_date_policy_missing_legacy_exclusion_retained",
        buy_owner_policy_hash="")
    generation = {"123456": (
        "exact_date_policy_missing_legacy_exclusion_retained", "")}
    legacy_result = report_mod._buy_parent_handoff_projection(day, [legacy], [],
        [fill], [{"id": 42, "code": "123456", "buy_qty": 1,
                  "status": "HOLDING"}], generation)
    assert legacy_result["rows"][0]["sellable_qty"] == 1
    assert legacy_result["rows"][0]["intent_id"] is None
    # A new reader process gets the same custody result from persisted rows.
    restored_sent = json.loads(json.dumps(legacy))
    restored_fill = report_mod.HoldingEvent(**json.loads(json.dumps(fill.__dict__)))
    restarted = report_mod._buy_parent_handoff_projection(day,
        [restored_sent], [], [restored_fill],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "HOLDING"}], generation)
    assert restarted["rows"][0]["sellable_qty"] == 1
    full_fill = report_mod.HoldingEvent(fill.timestamp, fill.name, fill.code,
        fill.stage, {**fill.fields, "fill_qty": "2",
        "order_filled_qty": "2", "order_remaining_qty": "0"}, "")
    full = report_mod._buy_parent_handoff_projection(day, [legacy], [],
        [full_fill], [{"id": 42, "code": "123456", "buy_qty": 2,
                     "status": "HOLDING"}], generation)["rows"][0]
    assert full["state"] == "full" and full["sellable_qty"] == 2
    early_fill = report_mod.HoldingEvent(day + " 08:59:59", fill.name,
        fill.code, fill.stage, dict(fill.fields), "")
    assert report_mod._buy_parent_handoff_projection(day, [legacy], [],
        [early_fill], [{"id": 42, "code": "123456", "buy_qty": 1,
                       "status": "HOLDING"}], generation)["rows"][0]["sellable_qty"] == 1
    second_fill = report_mod.HoldingEvent(day + " 09:00:04", fill.name,
        fill.code, fill.stage, {**fill.fields, "execution_no": "E2",
        "order_filled_qty": "2", "order_remaining_qty": "0"}, "")
    interleaved = report_mod._buy_parent_handoff_projection(day, [legacy], [],
        [fill, sale, second_fill], [{"id": 42, "code": "123456",
            "buy_qty": 2, "status": "HOLDING"}], generation)["rows"][0]
    assert interleaved["filled_qty"] == 2
    assert interleaved["sellable_qty"] == 1
    assert report_mod._buy_parent_handoff_projection(day, [legacy], journal(),
        [fill], [{"id": 42, "code": "123456", "buy_qty": 1,
                  "status": "HOLDING"}], generation)["rows"][0]["sellable_qty"] is None
    stale = report_mod._buy_parent_handoff_projection(day, [legacy], [],
        [fill], [{"id": 42, "code": "123456", "buy_qty": 1,
                  "status": "HOLDING"}], {"123456": ("changed", "")})
    assert stale["rows"][0]["sellable_qty"] is None
    extra_buy = report_mod.HoldingEvent(fill.timestamp, fill.name, fill.code,
        fill.stage, {**fill.fields, "order_no": "B2"}, "")
    assert report_mod._buy_parent_handoff_projection(day,
        [sent("B1", "intent-1")], journal(), [fill, extra_buy],
        [{"id": 42, "code": "123456", "buy_qty": 1,
          "status": "HOLDING"}])["rows"][0]["sellable_qty"] is None
    uncertain = {"stage": "order_leg_no_response", "emitted_date": day,
        "record_id": 43, "fields": {"entry_submit_attempt_id": "attempt-43"}}
    result = report_mod._buy_parent_handoff_projection(day, [uncertain], [], [], [])
    assert result["counts"]["raw"] == 0
    assert result["response_uncertain_attempts"][0]["sellable_qty"] is None


def test_buy_handoff_first_reader_keeps_source_gap_and_valid_empty_distinct(monkeypatch):
    from src.engine.scalping import entry_split_order_plan as entry
    monkeypatch.setattr(entry, "_execution_registry_snapshot", lambda: (
        [], {"status": "verified", "tail_hash": "0" * 64}))
    monkeypatch.setattr(entry, "_bounded_execution_projection", lambda *a, **k: (
        [], {"status": "ready", "sources": []}))
    result = report_mod._load_buy_parent_handoff_projection(
        "2026-09-28", [], [], "structured_partition_read")
    assert result["source_quality_status"] == "valid_empty"
    monkeypatch.setattr(entry, "_bounded_execution_projection", lambda *a, **k: (
        [], {"status": "source_gap", "reason": "missing"}))
    result = report_mod._load_buy_parent_handoff_projection(
        "2026-09-28", [], [], "structured_partition_read")
    assert result["source_quality_status"] == "source_gap_buy_handoff_generation"
    assert result["counts"]["raw"] is None


def test_completed_execution_ledger_rejects_unresolved_buy_order():
    trade = {"buy_qty": 1, "buy_price": 10000}
    buy = report_mod.HoldingEvent(
        timestamp="2026-09-24 09:00:00", name="test", code="123456",
        stage="position_rebased_after_fill", raw_line="",
        fields={
            "order_no": "B1", "execution_no": "BE1", "fill_qty": "1",
            "order_filled_qty": "1", "order_requested_qty": "2",
            "order_remaining_qty": "1", "fill_price": "10000",
            "receipt_quantity_contract_complete": "True",
            "receipt_unit_fill_consistent": "True",
            "receipt_economics_complete": "True",
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
            "pipeline_lifecycle_population_scope": "real_record_bound",
        },
    )
    sell = report_mod.HoldingEvent(
        timestamp="2026-09-24 09:01:00", name="test", code="123456",
        stage="sell_completed", raw_line="",
        fields={
            "order_no": "S1", "execution_no": "SE1",
            "main_lifecycle_exit_qty": "1", "main_lifecycle_exit_price": "10050",
            "cumulative_sell_qty": "1", "remaining_sell_qty": "0",
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "sell_execution_receipt_economics_complete": "True",
            "sell_execution_receipt_quantity_contract_complete": "True",
            "sell_execution_receipt_unit_fill_consistent": "True",
            "main_lifecycle_fees_taxes_krw": "10",
            "main_lifecycle_realized_net_pnl_krw": "40",
        },
    )
    ledger = report_mod._completed_execution_ledger(trade, [buy, sell])
    assert ledger["position_residual_qty"] == 0
    assert "source_gap_buy_order_terminal_missing" in ledger["strict_completion_reasons"]

    terminal = report_mod.HoldingEvent(
        timestamp="2026-09-24 09:00:30", name="test", code="123456",
        stage="entry_buy_order_terminal_confirmed", raw_line="",
        fields={
            "orig_ord_no": "B1", "order_filled_qty": "1",
            "order_requested_qty": "2",
            "terminal_reason": "terminal_absence_and_inventory_exact",
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
        },
    )
    closed = report_mod._completed_execution_ledger(trade, [buy, terminal, sell])
    assert closed["strict_completion_status"] == "eligible"
    assert closed["buy_fill_quality"] == "unknown"

    terminal.fields["order_filled_qty"] = "2"
    mismatched = report_mod._completed_execution_ledger(trade, [buy, terminal, sell])
    assert "source_gap_buy_order_terminal_missing" in mismatched["strict_completion_reasons"]


def test_carry_partial_sell_reconciles_prior_and_final_fill_legs():
    def event(stage, day, order, execution, quantity, cumulative, price, fee):
        fields = {
            "id": "42", "order_no": order, "execution_no": execution,
            "actual_order_submitted": "True", "broker_order_forbidden": "False",
            "pipeline_lifecycle_population_scope": "real_record_bound",
        }
        if stage == "position_rebased_after_fill":
            fields.update({
                "fill_qty": str(quantity), "order_filled_qty": str(cumulative),
                "order_requested_qty": "2", "order_remaining_qty": str(2-cumulative),
                "fill_price": str(price), "receipt_economics_complete": "True",
                "receipt_quantity_contract_complete": "True",
                "receipt_unit_fill_consistent": "True",
            })
        else:
            fields.update({
                "main_lifecycle_exit_qty": str(quantity),
                "main_lifecycle_exit_price": str(price),
                "cumulative_sell_qty": str(cumulative),
                "remaining_sell_qty": str(2-cumulative),
                "sell_receipt_economics_complete": "True",
                "sell_receipt_quantity_contract_complete": "True",
                "sell_receipt_unit_fill_consistent": "True",
                "sell_execution_receipt_economics_complete": "True",
                "sell_execution_receipt_quantity_contract_complete": "True",
                "sell_execution_receipt_unit_fill_consistent": "True",
                "main_lifecycle_fees_taxes_krw": str(fee),
                "main_lifecycle_realized_net_pnl_krw": str(price-10000-fee),
            })
        return report_mod.HoldingEvent(
            timestamp=f"{day} 09:00:00", name="test", code="123456",
            stage=stage, fields=fields, raw_line="",
        )

    events = [
        event("position_rebased_after_fill", "2026-09-23", "B1", "BE1", 2, 2, 10000, 0),
        event("sell_partial_fill_progress", "2026-09-23", "S1", "SE1", 1, 1, 10100, 10),
        event("sell_completed", "2026-09-24", "S2", "SE2", 1, 2, 10200, 10),
    ]
    trade = {"buy_qty": 1, "buy_price": 10000, "sell_price": 10150}
    ledger = report_mod._completed_execution_ledger(trade, events)
    assert ledger["strict_completion_status"] == "eligible"
    assert ledger["buy_filled_qty"] == ledger["sell_filled_qty"] == 2
    assert ledger["sell_order_count"] == 2
    assert ledger["sell_fill_fees_taxes_krw"] == 20


def test_prior_entry_fill_events_require_sealed_same_id_snapshot(monkeypatch):
    snapshot = {
        "date": "2026-09-23", "meta": {"warnings": []},
        "metrics": {"open_scalp_position_projection_status": "current_db_census",
                    "open_scalp_position_projection_count": 1},
        "sections": {"open_scalp_position_projection": [{
            "id": 42, "code": "123456", "avg_down_rebound_blocker_summary": [],
            "timeline": [{
                "stage": "position_rebased_after_fill",
                "timestamp": "2026-09-23 09:00:00",
                "fields": {"id": "42", "order_no": "B1", "execution_no": "BE1"},
            }],
        }]},
    }
    monkeypatch.setattr(report_mod, "load_monitor_snapshot", lambda *args: snapshot)
    trade = {"id": 42, "rec_date": "2026-09-23", "status": "COMPLETED"}
    events, receipts = report_mod._prior_entry_fill_events([trade], "2026-09-24")
    assert len(events["42"]) == 1
    assert receipts["2026-09-23"]["status"] == "sealed_entry_snapshot"

    snapshot["sections"]["open_scalp_position_projection"][0]["timeline"][0]["fields"]["id"] = "99"
    events, _ = report_mod._prior_entry_fill_events([trade], "2026-09-24")
    assert events == {}


def test_prior_fill_events_include_intermediate_day_scale_in(monkeypatch):
    def snapshot(day):
        stage = "position_rebased_after_fill" if day == "2026-09-22" else "scale_in_executed"
        return {
            "date": day, "meta": {"warnings": []},
            "metrics": {"open_scalp_position_projection_status": "current_db_census",
                        "open_scalp_position_projection_count": 1},
            "sections": {"open_scalp_position_projection": [{
                "id": 42, "code": "123456", "avg_down_rebound_blocker_summary": [],
                "timeline": [{
                    "stage": stage, "timestamp": f"{day} 09:00:00",
                    "fields": {"id": "42", "order_no": "B1" if day.endswith("22") else "B2",
                               "execution_no": "BE1" if day.endswith("22") else "BE2"},
                }],
            }]},
        }

    monkeypatch.setattr(report_mod, "load_monitor_snapshot", lambda _, day: snapshot(day))
    events, receipts = report_mod._prior_entry_fill_events(
        [{"id": 42, "rec_date": "2026-09-22", "status": "COMPLETED"}],
        "2026-09-24",
    )
    assert [event.stage for event in events["42"]] == [
        "position_rebased_after_fill", "scale_in_executed"
    ]
    assert set(receipts) == {"2026-09-22", "2026-09-23"}


def test_open_position_rebound_blockers_carry_as_bounded_prior_day_counts(monkeypatch):
    trade = {"id": 42, "rec_date": "2026-09-23", "status": "HOLDING",
             "strategy": "SCALPING", "code": "123456", "buy_qty": 1}
    blocked = [report_mod.HoldingEvent(
        "2026-09-23 10:00:00", "TEST", "123456",
        "avg_down_shared_rebound_blocked",
        {"id": "42", "reason": "shared_main_rebound_input_preflight_blocked",
         "preflight_primary_blocker": "tick_context_stale"}, "",
    ) for _ in range(3)]
    projection = report_mod._open_scalp_position_projection(trade, blocked)
    assert projection["timeline"] == []
    assert projection["avg_down_rebound_blocker_summary"] == [{
        "reason": "shared_main_rebound_input_preflight_blocked",
        "primary_blocker": "tick_context_stale", "machine_action": "-", "count": 3,
    }]
    snapshot = {"date": "2026-09-23", "meta": {"warnings": []},
                "metrics": {"open_scalp_position_projection_status": "current_db_census",
                            "open_scalp_position_projection_count": 1},
                "sections": {"open_scalp_position_projection": [projection]}}
    monkeypatch.setattr(report_mod, "load_monitor_snapshot", lambda *_: snapshot)
    completed_trade = {**trade, "status": "COMPLETED"}
    prior, receipts = report_mod._prior_entry_fill_events(
        [completed_trade], "2026-09-24",
    )
    assert receipts["2026-09-23"]["status"] == "sealed_entry_snapshot"
    lineage = report_mod._avg_down_rebound_lineage(completed_trade, prior["42"], None)
    assert lineage["blocked_observation_count"] == 3
    assert lineage["preflight_blocked_count"] == 3
    assert lineage["prior_blocker_summary_gap_count"] == 0


def test_prior_position_snapshot_without_rebound_summary_preserves_gap(monkeypatch):
    snapshot = {"date": "2026-09-23", "meta": {"warnings": []},
                "metrics": {"open_scalp_position_projection_status": "current_db_census",
                            "open_scalp_position_projection_count": 1},
                "sections": {"open_scalp_position_projection": [
                    {"id": 42, "code": "123456", "timeline": []},
                ]}}
    monkeypatch.setattr(report_mod, "load_monitor_snapshot", lambda *_: snapshot)
    trade = {"id": 42, "rec_date": "2026-09-23", "status": "COMPLETED",
             "strategy": "SCALPING", "code": "123456"}
    prior, _ = report_mod._prior_entry_fill_events([trade], "2026-09-24")
    assert report_mod._avg_down_rebound_lineage(trade, prior["42"], None) is None
    current_signal = report_mod.HoldingEvent(
        "2026-09-24 10:00:00", "TEST", "123456",
        "avg_down_shared_rebound_signal",
        {"id": "42", "source_signal_id": "signal-1",
         "position_episode_id": "episode-1", "scale_in_decision_id": "decision-1"}, "",
    )
    lineage = report_mod._avg_down_rebound_lineage(
        trade, [*prior["42"], current_signal], None,
    )
    assert lineage["prior_blocker_summary_gap_count"] == 1
    assert lineage["blocked_observation_count"] == 0


def test_sell_day_completion_event_recovers_prior_entry_by_exact_id(monkeypatch):
    prior_entry = {
        "id": 42,
        "rec_date": "2026-09-22",
        "code": "123456",
        "name": "test",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10000,
        "buy_qty": 1,
        "buy_time": "2026-09-22 15:00:00",
        "sell_price": 10100,
        "sell_time": "2026-09-23 09:10:00",
        "profit_rate": 0.77,
        "realized_pnl_krw": 77,
    }
    recovered_ids = []
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", lambda *_: ([], []))
    monkeypatch.setattr(
        report_mod,
        "_fetch_completed_trade_rows_by_ids",
        lambda ids: (recovered_ids.append(ids) or [prior_entry], []),
    )
    monkeypatch.setattr(
        report_mod,
        "_iter_target_lines",
        lambda *_args, **_kw: [
            "[2026-09-23 09:10:00] [HOLDING_PIPELINE] test(123456) "
            "stage=sell_completed id=42 sell_price=10100"
        ],
    )
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *_args: None
    )

    result = report_mod.build_trade_review_report("2026-09-23")

    assert recovered_ids == [{42}]
    assert result["metrics"]["completed_trades"] == 0
    assert result["metrics"]["carry_completed_rows"] == 1
    assert result["sections"]["completed_trade_projection"][0]["id"] == 42


def test_completed_projection_uses_sell_day_not_later_db_status(monkeypatch):
    trade = {
        "id": 42,
        "rec_date": "2026-09-22",
        "code": "123456",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_time": "2026-09-22 15:00:00",
        "sell_time": "2026-09-23 09:10:00",
        "profit_rate": 0.77,
    }
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", lambda *_: ([trade], []))
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda *_args, **_kw: [])
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *_args: None
    )

    report = report_mod.build_trade_review_report("2026-09-22")

    assert report["sections"]["completed_trade_projection"] == []
    assert report["metrics"]["canonical_completed_trades"] == 0


def test_sync_completion_without_sell_time_keeps_event_day_census(monkeypatch):
    trade = {
        "id": 42,
        "rec_date": "2026-09-23",
        "code": "123456",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_time": "2026-09-23 09:00:00",
        "sell_time": "",
        "profit_rate": 0.77,
    }
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", lambda *_: ([trade], []))
    monkeypatch.setattr(
        report_mod,
        "_iter_target_lines",
        lambda *_args, **_kw: [
            "[2026-09-23 09:10:00] [HOLDING_PIPELINE] test(123456) "
            "stage=sell_completed id=42 "
            "decision_authority=broker_balance_reconciliation_only"
        ],
    )
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *_args: None
    )

    report = report_mod.build_trade_review_report("2026-09-23")
    row = report["sections"]["completed_trade_projection"][0]

    assert row["completion_observed_date"] == "2026-09-23"
    assert row["completion_day_basis"] == "terminal_event"
    assert row["exact_sell_fill_time"] is None
    assert row["realized_pnl_krw"] is None


def test_sell_completed_event_with_open_db_row_blocks_census(monkeypatch):
    trade = {
        "id": 42,
        "rec_date": "2026-09-23",
        "code": "123456",
        "status": "OPEN",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_time": "2026-09-23 09:00:00",
        "profit_rate": None,
    }
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", lambda *_: ([trade], []))
    monkeypatch.setattr(
        report_mod,
        "_iter_target_lines",
        lambda *_args, **_kw: [
            "[2026-09-23 09:10:00] [HOLDING_PIPELINE] test(123456) "
            "stage=sell_completed id=42"
        ],
    )
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *_args: None
    )

    report = report_mod.build_trade_review_report("2026-09-23")

    assert report["meta"]["sell_completed_event_ids"] == [42]
    assert report["sections"]["completed_trade_projection"] == []
    assert any("sell_completed" in item for item in report["meta"]["warnings"])


def test_completed_projection_rejects_receipt_profit_rate_mismatch():
    trade = {
        "id": 1,
        "status": "COMPLETED",
        "buy_qty": 1,
        "profit_rate": 0.5,
    }
    event = report_mod.HoldingEvent(
        timestamp="2026-09-23 09:10:02",
        name="test",
        code="123456",
        stage="sell_completed",
        fields={
            "decision_authority": "broker_sell_fill_observation_only",
            "actual_order_submitted": "True",
            "broker_order_forbidden": "False",
            "cumulative_sell_qty": "1",
            "profit_rate": "1.0",
            "realized_pnl_krw_source": "broker_fill_prices_fee_aware",
            "realized_pnl_krw": "40",
        },
        raw_line="",
    )

    row = report_mod._completed_trade_projection(trade, [event], trade)

    assert row["terminal_profit_rate_reconciled"] is False
    assert row["realized_pnl_krw"] is None


def test_explicit_exit_signal_precedes_later_terminal_inferred_rule():
    def event(stage, time, rule):
        return report_mod.HoldingEvent(
            timestamp=time,
            name="test",
            code="123456",
            stage=stage,
            fields={"exit_rule": rule},
            raw_line="",
        )

    events = [
        event("exit_signal", "2026-09-23 09:10:00", "scalp_soft_stop_pct"),
        event("sell_order_sent", "2026-09-23 09:10:01", "scalp_soft_stop_pct"),
        event("sell_completed", "2026-09-23 09:10:02", "scalp_soft_stop_pct"),
    ]

    signal = report_mod._build_exit_signal(events)

    assert signal.get("inferred") is True
    assert signal["binding_status"] == "legacy_unbound"
    assert signal["exit_rule"] == "scalp_soft_stop_pct"

    events.insert(
        1,
        event("exit_signal", "2026-09-23 09:10:00.500", "scalp_hard_stop_pct"),
    )
    signal = report_mod._build_exit_signal(events)
    assert signal.get("inferred") is True


def test_exit_signal_requires_exact_submission_generation_and_order():
    contract = {
        "schema": "holding_exit_signal_receipt_v1",
        "source_date": "2026-09-28", "signal_id": "decision-1",
        "signal_at": "2026-09-28T09:10:00.500000+09:00",
        "record_id": "42", "code": "123456",
        "position_key": "record:42", "buy_fill_identity": "buy-generation-1",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "decision_owner_type": "main_scalping",
        "exit_rule": "scalp_trailing_take_profit",
        "policy_sha256": "a" * 64,
        "threshold_key": "SCALP_TRAILING_LIMIT_WEAK",
        "threshold_effective_pct": 0.4,
        "context_venue": "KRX", "context_session": "krx_regular",
        "decision_inputs": {
            "exit_threshold_key": "SCALP_TRAILING_LIMIT_WEAK",
            "exit_threshold_effective_pct": 0.4,
            "exit_threshold_executable_bid": 10060,
        },
    }
    digest = hashlib.sha256(json.dumps(
        contract, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    submit_contract = {
        "schema": "sell_submit_pending_context_v1",
        "generation": "submit-1", "target_id": 42, "code": "123456",
        "requested_qty": 1, "owner_position_qty": 1,
        "started_at": 1790554201.0, "intended_route": "SOR",
        "intended_effective_venue": "KRX",
        "intended_session_bucket": "KRX_REGULAR",
    }
    submit_sha = hashlib.sha256(json.dumps(
        submit_contract, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    decision_fields = {
        "id": "42", "exit_rule": contract["exit_rule"],
        "exit_signal_id": contract["signal_id"],
        "exit_signal_contract": json.dumps(contract, sort_keys=True,
                                           separators=(",", ":")),
        "exit_signal_contract_sha256": digest,
        "exit_signal_position_key": contract["position_key"],
        "exit_signal_buy_fill_identity": contract["buy_fill_identity"],
        "exit_signal_source_date": contract["source_date"],
        "exit_threshold_key": contract["threshold_key"],
        "exit_threshold_effective_pct": contract["threshold_effective_pct"],
        "exit_threshold_executable_bid": 10060,
        "scalp_trailing_policy_value_sha256": contract["policy_sha256"],
        "holding_context_venue": contract["context_venue"],
        "holding_context_session": contract["context_session"],
        "pipeline_lifecycle_population_scope": "real_record_bound",
    }
    submission_fields = {
        "id": "42", "exit_rule": contract["exit_rule"],
        "ord_no": "SELL-1", "exit_signal_id": "decision-1",
        "exit_signal_contract_sha256": digest,
        "exit_signal_position_key": "record:42",
        "exit_signal_buy_fill_identity": "buy-generation-1",
        "exit_signal_source_date": "2026-09-28",
        "exit_signal_at": contract["signal_at"],
        "exit_signal_binding_status": "same_position_buy_generation",
        "exit_signal_submit_intended_route": "SOR",
        "sell_submit_generation": "submit-1",
        "sell_submit_context_sha256": submit_sha,
        "sell_submit_context_contract": json.dumps(
            submit_contract, sort_keys=True, separators=(",", ":")),
        "broker_route": "SOR", "market_session_bucket": "krx_regular",
        "qty": "1", "actual_order_submitted": "True",
        "pipeline_lifecycle_population_scope": "real_record_bound",
    }
    def event(stage, timestamp, fields):
        return report_mod.HoldingEvent(timestamp, "test", "123456", stage,
                                       fields, "")
    decision = event("exit_signal", "2026-09-28 09:10:00", decision_fields)
    submission = event("sell_order_sent", "2026-09-28 09:10:01",
                       submission_fields)
    terminal = event("sell_completed", "2026-09-28 09:10:02", {
        "id": "42", "exit_rule": contract["exit_rule"],
        "order_no": "SELL-1",
    })

    linked = report_mod._build_exit_signal([decision, submission, terminal])
    assert linked["inferred"] is False
    assert linked["binding_status"] == "same_order_generation"
    assert linked["policy_binding_status"] == "observed_sha_bootstrap_unverified"
    assert linked["submission"]["order_no"] == "SELL-1"
    assert linked["submission"]["sell_submit_context_sha256"] == submit_sha
    trade = {
        "id": 42, "code": "123456", "strategy": "SCALPING",
        "position_tag": "SCANNER", "buy_time": "2026-09-28 09:00:00",
        "sell_time": "2026-09-28 09:10:02",
    }
    assert report_mod._build_exit_signal([
        decision, submission, terminal
    ], trade)["binding_status"] == "same_order_generation"
    assert report_mod._build_exit_signal([
        decision, submission, terminal
    ], {**trade, "position_tag": "MANUAL"})["binding_status"] == (
        "source_gap_trade_custody_mismatch"
    )

    # The requested SOR route and broker-selected route are separate evidence.
    broker_krx = event("sell_order_sent", submission.timestamp,
                       {**submission_fields, "broker_route": "KRX"})
    assert report_mod._build_exit_signal([
        decision, broker_krx, terminal
    ])["binding_status"] == "same_order_generation"
    assert report_mod._build_exit_signal([
        decision, submission, submission, terminal
    ])["binding_status"] == "same_order_generation"
    partial_context = {**submit_contract, "requested_qty": 2,
                       "owner_position_qty": 2}
    partial_sha = hashlib.sha256(json.dumps(
        partial_context, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    partial_submission = event("sell_order_sent", submission.timestamp, {
        **submission_fields, "qty": "2", "submitted_qty": "2",
        "sell_submit_context_contract": json.dumps(
            partial_context, sort_keys=True, separators=(",", ":")),
        "sell_submit_context_sha256": partial_sha,
    })
    partial = event("sell_partial_fill_progress", "2026-09-28 09:10:01", {
        "id": "42", "order_no": "SELL-1", "filled_qty": "1",
        "remaining_qty": "1",
    })
    assert report_mod._build_exit_signal([
        decision, partial_submission, partial, terminal
    ])["binding_status"] == "same_order_generation"
    cancel_pending = event("sell_cancel_reconciliation_deferred",
                           "2026-09-28 09:10:02", {
                               "id": "42", "order_no": "SELL-1",
                           })
    open_signal = report_mod._build_exit_signal([
        decision, partial_submission, partial, cancel_pending
    ])
    assert open_signal["binding_status"] == "same_order_generation"
    assert open_signal["submission"]["order_no"] == "SELL-1"

    for changed in (
        {"exit_signal_id": "stale-decision"},
        {"ord_no": "SELL-OLD"},
        {"sell_submit_context_sha256": ""},
        {"qty": "2"},
        {"exit_signal_source_date": "2026-09-27"},
        {"broker_route": "UNKNOWN"},
        {"pipeline_lifecycle_population_scope": "sim_observation_only"},
    ):
        invalid = event("sell_order_sent", submission.timestamp,
                        {**submission_fields, **changed})
        result = report_mod._build_exit_signal([decision, invalid, terminal])
        assert result["inferred"] is True
        assert result["binding_status"] != "same_order_generation"
    changed_quote = event("exit_signal", decision.timestamp,
                          {**decision_fields,
                           "exit_threshold_executable_bid": 9999})
    assert report_mod._build_exit_signal([
        changed_quote, submission, terminal
    ])["binding_status"] == "source_gap_decision_submit_contract_mismatch"
    duplicate = event("exit_signal", decision.timestamp,
                      {**decision_fields, "exit_signal_contract_sha256": "c" * 64})
    result = report_mod._build_exit_signal([decision, duplicate, submission,
                                            terminal])
    assert result["inferred"] is True
    conflicting_submit = event("sell_order_sent", submission.timestamp,
                               {**submission_fields, "qty": "2"})
    assert report_mod._build_exit_signal([
        decision, submission, conflicting_submit, terminal
    ])["binding_status"] == "source_gap_conflicting_submission"
    assert report_mod._build_exit_signal([
        submission, terminal
    ])["binding_status"] == "source_gap_explicit_signal_missing"


def test_trade_review_restores_completed_trade_from_holding_events(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:08:57] [HOLDING_PIPELINE] 심텍(222800) stage=holding_started id=1085 fill_price=57000 fill_qty=10 buy_price=57000.00 buy_qty=10 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:14:45] [HOLDING_PIPELINE] 심텍(222800) stage=exit_signal id=1085 profit_rate=-1.58 buy_price=57000.0 buy_qty=10 curr_price=56100 exit_rule=scalp_soft_stop_pct",
        "[2026-04-06 09:14:46] [HOLDING_PIPELINE] 심텍(222800) stage=sell_completed id=1085 sell_price=56100 profit_rate=-1.58 revive=True new_watch_id=1103",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1085,
                    "rec_date": target_date,
                    "code": "222800",
                    "name": "심텍",
                    "status": "WATCHING",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 0.0,
                    "buy_qty": 10,
                    "buy_time": "2026-04-06 09:08:57",
                    "sell_price": 56100,
                    "sell_time": "2026-04-06 09:14:45",
                    "profit_rate": -1.58,
                    "realized_pnl_krw": 0,
                },
                {
                    "id": 1103,
                    "rec_date": target_date,
                    "code": "222800",
                    "name": "심텍",
                    "status": "WATCHING",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 0.0,
                    "buy_qty": 0,
                    "buy_time": "",
                    "sell_price": 0,
                    "sell_time": "",
                    "profit_rate": 0.0,
                    "realized_pnl_krw": 0,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-04-06")

    assert report["metrics"]["completed_trades"] == 1
    assert report["metrics"]["open_trades"] == 0
    assert report["metrics"]["realized_pnl_krw"] == -10290
    assert report["metrics"]["realized_pnl_krw_basis"] == (
        "legacy_display_configured_cost_model"
    )
    assert report["metrics"]["broker_actual_realized_pnl_krw"] is None
    assert report["metrics"]["modeled_display_pnl_krw"] == -10290

    trade = report["sections"]["completed_trades"][0]
    assert trade["id"] == 1085
    assert trade["status"] == "COMPLETED"
    assert trade["buy_price"] == 57000.0
    assert trade["sell_price"] == 56100
    assert trade["realized_pnl_krw"] == -10290
    assert trade["result_icon"] == "▼"
    assert trade["result_label"] == "손절"
    assert trade["result_tone"] == "bad"


def test_trade_review_restores_entry_mode_from_holding_events(monkeypatch):
    holding_lines = [
        "[2026-04-09 09:08:57] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=77 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER entry_mode=fallback",
        "[2026-04-09 09:09:45] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=77 sell_price=9900 profit_rate=-1.00 exit_rule=scalp_scanner_fallback_never_green",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 77,
                    "rec_date": target_date,
                    "code": "123456",
                    "name": "테스트",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 10000.0,
                    "buy_qty": 1,
                    "buy_time": "2026-04-09 09:08:57",
                    "sell_price": 9900,
                    "sell_time": "2026-04-09 09:09:45",
                    "profit_rate": -1.0,
                    "realized_pnl_krw": -100,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-04-09")
    trade = report["sections"]["completed_trades"][0]

    assert trade["entry_mode"] == "fallback"


def test_trade_review_compacts_long_timeline(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:00:01] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=1 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:00:10] [HOLDING_PIPELINE] 테스트(123456) stage=preset_exit_setup id=1 preset_tp_price=10150",
        "[2026-04-06 09:00:20] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=61 profit_rate=+0.10",
        "[2026-04-06 09:00:30] [HOLDING_PIPELINE] 테스트(123456) stage=scale_in_executed id=1 add_count=1 new_buy_qty=2",
        "[2026-04-06 09:00:40] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=58 profit_rate=-0.20",
        "[2026-04-06 09:00:50] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_reuse_bypass id=1 reason_codes=age_expired",
        "[2026-04-06 09:01:00] [HOLDING_PIPELINE] 테스트(123456) stage=exit_signal id=1 profit_rate=-0.80 exit_rule=scalp_ai_early_exit",
        "[2026-04-06 09:01:01] [HOLDING_PIPELINE] 테스트(123456) stage=sell_order_sent id=1 qty=2 ord_no=0001",
        "[2026-04-06 09:01:02] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=1 sell_price=9920 profit_rate=-0.80",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1,
                    "rec_date": target_date,
                    "code": "123456",
                    "name": "테스트",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 10000.0,
                    "buy_qty": 2,
                    "buy_time": "2026-04-06 09:00:01",
                    "sell_price": 9920,
                    "sell_time": "2026-04-06 09:01:02",
                    "profit_rate": -0.8,
                    "realized_pnl_krw": -160,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-04-06")
    trade = report["sections"]["recent_trades"][0]

    assert len(trade["timeline"]) == 9
    assert len(trade["compact_timeline"]) == 8
    omitted = trade["compact_timeline"][4]
    assert omitted["stage"] == "omitted"
    assert omitted["label"] == "중간 2단계 생략"
    assert trade["timeline_hidden_count"] == 2


def test_trade_review_builds_ai_review_summary(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:00:01] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=1 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:00:20] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=60 profit_rate=+0.07 low_score_hits=0/3",
        "[2026-04-06 09:00:30] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=45 profit_rate=-0.14 low_score_hits=1/3",
        "[2026-04-06 09:00:40] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=28 profit_rate=-1.06 low_score_hits=3/3",
        "[2026-04-06 09:00:41] [HOLDING_PIPELINE] 테스트(123456) stage=exit_signal id=1 profit_rate=-1.06 exit_rule=scalp_ai_early_exit",
        "[2026-04-06 09:00:42] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=1 sell_price=9890 profit_rate=-1.06",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1,
                    "rec_date": target_date,
                    "code": "123456",
                    "name": "테스트",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 10000.0,
                    "buy_qty": 1,
                    "buy_time": "2026-04-06 09:00:01",
                    "sell_price": 9890,
                    "sell_time": "2026-04-06 09:00:42",
                    "profit_rate": -1.06,
                    "realized_pnl_krw": -110,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-04-06")
    summary = report["sections"]["recent_trades"][0]["ai_review_summary"]

    assert summary["headline"] == "AI 하방 경고 누적"
    assert "최근 3회 기준 AI 60→28점" in summary["summary"]
    assert any(item["value"] == "3/3" for item in summary["chips"])


def test_trade_review_hides_unrealistic_holding_age_sec(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:00:01] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=1 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:00:20] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_reuse_bypass id=1 age_sec=1775526427.3 reason_codes=sig_changed,age_expired",
        "[2026-04-06 09:00:42] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=1 sell_price=10100 profit_rate=+1.00",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1,
                    "rec_date": target_date,
                    "code": "123456",
                    "name": "테스트",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 10000.0,
                    "buy_qty": 1,
                    "buy_time": "2026-04-06 09:00:01",
                    "sell_price": 10100,
                    "sell_time": "2026-04-06 09:00:42",
                    "profit_rate": 1.0,
                    "realized_pnl_krw": 100,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-04-06")
    timeline = report["sections"]["recent_trades"][0]["timeline"]
    bypass_event = next(
        item for item in timeline if item["stage"] == "ai_holding_reuse_bypass"
    )

    assert all(detail["label"] != "재사용 나이" for detail in bypass_event["details"])


def test_trade_review_infers_scalp_preset_hard_stop_from_sell_completed(monkeypatch):
    holding_lines = [
        "[2026-04-08 09:53:20] [HOLDING_PIPELINE] 산일전기(062040) stage=holding_started id=1407 fill_price=145700 fill_qty=25 buy_price=145700.00 buy_qty=25 strategy=SCALPING position_tag=SCALP_BASE",
        "[2026-04-08 09:53:20] [HOLDING_PIPELINE] 산일전기(062040) stage=preset_exit_setup id=1407 preset_tp_price=147900 qty=25 ord_no=0033457",
        "[2026-04-08 09:55:29] [HOLDING_PIPELINE] 산일전기(062040) stage=sell_completed id=1407 sell_price=145000 profit_rate=-0.71 exit_rule=- revive=True new_watch_id=1426",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1407,
                    "rec_date": target_date,
                    "code": "062040",
                    "name": "산일전기",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCALP_BASE",
                    "buy_price": 145707.0,
                    "buy_qty": 26,
                    "buy_time": "2026-04-08 09:54:52",
                    "sell_price": 145000,
                    "sell_time": "2026-04-08 09:55:29",
                    "profit_rate": -0.71,
                    "realized_pnl_krw": -27053,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(
        target_date="2026-04-08", code="062040", scope="all"
    )
    trade = report["sections"]["recent_trades"][0]
    timeline_stages = [item["stage"] for item in trade["compact_timeline"]]
    taxonomy_rows = {
        item["key"]: item for item in report["sections"]["hard_stop_taxonomy"]["rows"]
    }

    assert trade["exit_signal"]["exit_rule"] == "scalp_preset_hard_stop_pct"
    assert trade["exit_signal"]["exit_decision_source"] == "PRESET_HARD_STOP"
    assert trade["exit_signal"]["sell_reason_type"] == "LOSS"
    assert trade["exit_signal"]["inferred"] is True
    assert timeline_stages == [
        "holding_started",
        "preset_exit_setup",
        "exit_signal",
        "sell_completed",
    ]
    assert taxonomy_rows["scalp_preset_hard_stop_pct"]["count"] == 1
    assert (
        report["sections"]["hard_stop_taxonomy"]["metrics"]["shadow_hard_stop_events"]
        == 0
    )


def test_trade_review_restores_exit_rule_from_sell_order_sent(monkeypatch):
    holding_lines = [
        "[2026-04-09 09:45:10] [HOLDING_PIPELINE] 현대건설(000720) stage=holding_started id=1501 fill_price=34400 fill_qty=10 buy_price=34400.00 buy_qty=10 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-09 09:52:33] [HOLDING_PIPELINE] 현대건설(000720) stage=sell_order_sent id=1501 sell_reason_type=LOSS reason=🧯|SCANNER|fallback|지연손절|보정 exit_rule=scalp_scanner_fallback_never_green qty=10 ord_no=0099911",
        "[2026-04-09 09:52:34] [HOLDING_PIPELINE] 현대건설(000720) stage=sell_completed id=1501 sell_price=34120 profit_rate=-0.81 exit_rule=- revive=False",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 1501,
                    "rec_date": target_date,
                    "code": "000720",
                    "name": "현대건설",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 34400.0,
                    "buy_qty": 10,
                    "buy_time": "2026-04-09 09:45:10",
                    "sell_price": 34120,
                    "sell_time": "2026-04-09 09:52:34",
                    "profit_rate": -0.81,
                    "realized_pnl_krw": -2800,
                },
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(
        target_date="2026-04-09", code="000720", scope="all"
    )
    trade = report["sections"]["recent_trades"][0]

    assert trade["exit_signal"]["exit_rule"] == "scalp_scanner_fallback_never_green"
    assert trade["exit_signal"]["exit_decision_source"] == "MANUAL"
    assert trade["exit_signal"]["inferred"] is True


def test_trade_review_reconciles_completed_economics_without_losing_raw_event(
    monkeypatch,
):
    holding_lines = [
        "[2026-08-24 09:40:42] [HOLDING_PIPELINE] 한화투자증권(003530) stage=holding_started id=2401 fill_price=5110 fill_qty=1 buy_price=5110 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-08-24 09:45:25] [HOLDING_PIPELINE] 한화투자증권(003530) stage=sell_order_sent id=2401 profit_rate=+0.40 qty=1 exit_rule=scalp_trailing_profit_protect",
        "[2026-08-24 09:45:26] [HOLDING_PIPELINE] 한화투자증권(003530) stage=sell_completed id=2401 sell_price=5070 profit_rate=-1.02 realized_pnl_krw=-52 main_lifecycle_realized_net_pnl_krw=-52 exit_rule=scalp_trailing_profit_protect",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return (
            [
                {
                    "id": 2401,
                    "rec_date": target_date,
                    "code": "003530",
                    "name": "한화투자증권",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "position_tag": "SCANNER",
                    "buy_price": 5040.0,
                    "buy_qty": 1,
                    "buy_time": "2026-08-24 09:40:42",
                    "sell_price": 5070,
                    "sell_time": "2026-08-24 09:45:26",
                    "profit_rate": 0.36,
                    "realized_pnl_krw": 18,
                }
            ],
            [],
        )

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(
        report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None
    )

    report = report_mod.build_trade_review_report(target_date="2026-08-24")
    trade = report["sections"]["completed_trades"][0]
    sell_completed = next(
        item for item in trade["timeline"] if item["stage"] == "sell_completed"
    )
    sell_order_sent = next(
        item for item in trade["timeline"] if item["stage"] == "sell_order_sent"
    )

    assert report["metrics"]["realized_pnl_krw"] == 18
    assert report["metrics"]["broker_actual_realized_pnl_krw"] is None
    assert report["metrics"]["modeled_display_pnl_krw"] == 18
    assert trade["profit_rate"] == 0.36
    assert trade["exit_signal"]["fields"]["buy_price"] == "5040.0"
    assert trade["exit_signal"]["fields"]["profit_rate"] == "0.36"
    assert sell_completed["fields"]["realized_pnl_krw"] == "18"
    assert sell_completed["fields"]["main_lifecycle_realized_net_pnl_krw"] == "18"
    assert sell_completed["fields"]["trade_review_raw_event_profit_rate"] == "-1.02"
    assert sell_completed["fields"]["trade_review_raw_event_realized_pnl_krw"] == "-52"
    assert (
        sell_completed["fields"][
            "trade_review_raw_event_main_lifecycle_realized_net_pnl_krw"
        ]
        == "-52"
    )
    assert sell_completed["fields"]["trade_review_economics_reconciled"] == "True"
    assert sell_order_sent["fields"]["profit_rate"] == "+0.40"
    assert "trade_review_economics_reconciled" not in sell_order_sent["fields"]
