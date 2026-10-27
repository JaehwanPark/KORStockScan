"""Research allocation remains separate from canonical broker execution costs."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.engine import sniper_trade_review_report as review
from src.engine.lifecycle import broker_cost_reconciliation as exact
from src.tests.test_broker_cost_reconciliation import fixture, seal


def custody(record=1, *, qty=2, state="full"):
    return dict(
        record_id=str(record),
        state=state,
        filled_qty=qty,
        source_quality_reasons=[],
        owner_type="main_scalping",
        owner_id=f"main_scalping:{record}",
        account_key="research-test-account",
    )


def test_exact_receipt_can_bind_verified_custody_when_terminal_cost_context_is_absent():
    trade, events, ledger, context, receipt = fixture()
    events = [
        replace(
            event,
            fields={
                key: value
                for key, value in event.fields.items()
                if key
                not in {"holding_cost_owner", "holding_cost_account_scope_sha256"}
            },
        )
        for event in events
    ]
    receipt["account_scope_sha256"] = exact.digest(
        ["broker_account", "research-test-account"]
    )
    seal(receipt)
    row = review._completed_trade_projection(
        trade, events, {}, cost_receipt=receipt, cost_custody_rows=[custody()]
    )
    assert row["economics_status"] == "actual_cost_reconciled"
    assert row["broker_actual_fees_taxes_krw"] == 10
    assert row["realized_pnl_krw"] == 190


@pytest.mark.parametrize(
    "fault",
    ["owner", "quantity", "open", "missing_account", "source_gap", "explicit_conflict"],
)
def test_exact_cost_context_fallback_never_invents_custody(fault):
    trade, events, _, _, receipt = fixture()
    events = [
        replace(
            event,
            fields={
                key: value
                for key, value in event.fields.items()
                if key
                not in {"holding_cost_owner", "holding_cost_account_scope_sha256"}
            },
        )
        for event in events
    ]
    owner = custody()
    if fault == "owner":
        owner["owner_type"] = "manual"
    elif fault == "quantity":
        owner["filled_qty"] = 1
    elif fault == "open":
        owner["state"] = "cancel_pending"
    elif fault == "missing_account":
        owner["account_key"] = None
    elif fault == "source_gap":
        owner["source_quality_reasons"] = ["fill_census_mismatch"]
    else:
        events[-1] = replace(
            events[-1], fields={**events[-1].fields, "holding_cost_owner": "manual"}
        )
    receipt["account_scope_sha256"] = exact.digest(
        ["broker_account", "research-test-account"]
    )
    seal(receipt)
    row = review._completed_trade_projection(
        trade, events, {}, cost_receipt=receipt, cost_custody_rows=[owner]
    )
    assert row["broker_actual_fees_taxes_krw"] is None
    assert row["realized_pnl_krw"] is None
    assert row["economics_status"] == "actual_cost_invalid"


def setup_report(
    monkeypatch, tmp_path, *, allocation_status="research_cost_allocated", native=False
):
    from src.engine.lifecycle import broker_cost_allocation as allocation
    from src.engine.lifecycle import broker_cost_source as source

    trade, events, _, _, _ = fixture()
    trade.update(
        name="Test",
        position_tag="SCANNER",
        buy_time=events[0].timestamp,
        sell_time=events[-1].timestamp,
    )
    events = [replace(event, fields={**event.fields, "id": "1"}) for event in events]
    opened = {
        **trade,
        "id": 2,
        "status": "HOLDING",
        "rec_date": "2026-10-07",
        "buy_qty": 1,
        "buy_time": "2026-10-07 15:00:00",
        "sell_time": None,
        "sell_price": None,
        "profit_rate": None,
    }
    prior_buy = replace(
        events[0],
        timestamp="2026-10-07 15:00:00",
        fields={
            **events[0].fields,
            "id": "2",
            "order_no": "20",
            "execution_no": "21",
            "fill_qty": 1,
            "order_filled_qty": 1,
            "order_requested_qty": 1,
        },
    )
    events.append(prior_buy)
    owners = [custody(), custody(2, qty=1, state="partial_open")]
    calls = dict(
        load_dates=[], positions=[], persist=[], enqueue=[], resolve=[], events=events
    )
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    monkeypatch.setattr(review, "guard_stdin_heavy_build", lambda **kw: None)
    monkeypatch.setattr(review, "load_monitor_snapshot", lambda *a: None)
    monkeypatch.setattr(review, "_iter_target_lines", lambda *a, **kw: [])
    monkeypatch.setattr(review, "_fetch_trade_rows", lambda *a: ([trade, opened], []))
    monkeypatch.setattr(review, "_fetch_open_scalp_rows", lambda *a: ([], []))
    monkeypatch.setattr(
        review, "_fetch_completed_trade_rows_by_ids", lambda *a: ([], [])
    )
    monkeypatch.setattr(
        review,
        "_load_holding_projection_events_from_structured",
        lambda *a: (events, "structured_partition_read", []),
    )
    monkeypatch.setattr(
        review,
        "_load_buy_parent_handoff_projection",
        lambda *a: {"rows": owners, "counts": {}, "source_quality_status": "verified"},
    )
    monkeypatch.setattr(review, "_prior_entry_fill_events", lambda *a: ({}, {}))
    monkeypatch.setattr(review, "find_gatekeeper_snapshot_for_trade", lambda *a: None)
    monkeypatch.setattr(exact, "load_receipt", lambda *a: None)
    if native:
        return calls
    monkeypatch.setattr(
        exact, "source_generation", lambda *a, **kw: {"status": "unchanged"}
    )
    monkeypatch.setattr(
        source, "load_source", lambda root, day: calls["load_dates"].append(day)
    )
    receipt = dict(
        schema="initial_quantity_broker_total_allocated_cost_v1",
        status=allocation_status,
        record_id="1",
        allocated_fees_taxes_krw=(
            10 if allocation_status == "research_cost_allocated" else None
        ),
        allocated_net_pnl_krw=(
            190 if allocation_status == "research_cost_allocated" else None
        ),
        allocated_profit_rate=(
            0.95 if allocation_status == "research_cost_allocated" else None
        ),
        reason=(
            None
            if allocation_status == "research_cost_allocated"
            else "broker_cost_source_missing"
        ),
    )

    def build(sources, positions):
        calls["positions"] = deepcopy(positions)
        return {"1": receipt}

    monkeypatch.setattr(allocation, "build_research_cost_allocations", build)
    monkeypatch.setattr(
        allocation, "validate_research_cost", lambda receipt, **kw: receipt
    )
    monkeypatch.setattr(
        allocation, "persist_research_costs", lambda *a: calls["persist"].append(a)
    )
    monkeypatch.setattr(
        source, "enqueue_pending", lambda *a: calls["enqueue"].append(a)
    )
    monkeypatch.setattr(
        source, "resolve_pending", lambda *a, **kw: calls["resolve"].append((a, kw))
    )
    return calls


@pytest.mark.parametrize("write", [False, True])
def test_two_pass_report_includes_open_buy_and_keeps_allocated_cost_separate(
    monkeypatch, tmp_path, write
):
    calls = setup_report(monkeypatch, tmp_path)
    result = review.build_trade_review_report("2026-10-08", write_research_costs=write)
    positions = {row["record_id"]: row for row in calls["positions"]}
    assert set(positions) == {"1", "2"}
    assert positions["1"]["terminal_observed"] is True
    assert positions["2"]["status"] == "HOLDING"
    assert positions["2"]["buy_legs"][0]["qty"] == 1
    assert (
        positions["2"]["sell_legs"] == []
        and positions["2"]["terminal_observed"] is False
    )
    assert set(calls["load_dates"]) == {"2026-10-07", "2026-10-08"}
    completed = result["sections"]["completed_trade_projection"][0]
    assert completed["quantity_research_cost"]["allocated_net_pnl_krw"] == 190
    assert completed["broker_actual_fees_taxes_krw"] is None
    assert completed["realized_pnl_krw"] is None
    assert (
        "source_gap_broker_actual_cost_missing"
        in completed["strict_completion_reasons"]
    )
    assert completed["strict_completion_status"] == "excluded"
    facts = result["sections"]["strategy_position_fact_projection"]
    assert (
        next(row for row in facts if row["id"] == 1)["quantity_research_cost"]
        == completed["quantity_research_cost"]
    )
    assert len(calls["persist"]) == int(write)
    assert calls["enqueue"] == []
    assert len(calls["resolve"]) == int(write)


def test_unresolved_research_cost_enqueues_prior_dates_only_with_write(
    monkeypatch, tmp_path
):
    calls = setup_report(
        monkeypatch, tmp_path, allocation_status="research_cost_pending"
    )
    review.build_trade_review_report("2026-10-08")
    assert calls["persist"] == calls["enqueue"] == calls["resolve"] == []
    review.build_trade_review_report("2026-10-08", write_research_costs=True)
    assert len(calls["enqueue"]) == 1
    _, completion, dates, records, reasons = calls["enqueue"][0]
    assert completion == "2026-10-08" and dates == ["2026-10-07", "2026-10-08"]
    assert records == ["1"] and reasons == ["broker_cost_source_missing"]
    assert calls["resolve"] == []


def test_allocator_failure_keeps_original_cause_instead_of_validating_it_as_a_receipt(
    monkeypatch, tmp_path
):
    from src.engine.lifecycle import broker_cost_allocation as allocation

    calls = setup_report(
        monkeypatch, tmp_path, allocation_status="research_cost_invalid"
    )

    def forbidden(*args, **kwargs):
        pytest.fail("an allocator source gap is not an allocated receipt")

    monkeypatch.setattr(allocation, "validate_research_cost", forbidden)
    result = review.build_trade_review_report("2026-10-08", write_research_costs=True)
    row = result["sections"]["completed_trade_projection"][0]
    assert row["quantity_research_cost"]["reason"] == "broker_cost_source_missing"
    assert row["quantity_research_cost"]["allocated_net_pnl_krw"] is None
    assert row["realized_pnl_krw"] is None
    assert calls["enqueue"][0][-1] == ["broker_cost_source_missing"]


def test_filtered_report_cannot_persist_partial_research_population():
    with pytest.raises(ValueError, match="unfiltered_population"):
        review.build_trade_review_report(
            "2026-10-08", code="123456", write_research_costs=True
        )


def test_multiple_missing_dates_remain_queueable_canonical_reason_codes(tmp_path):
    from src.engine.lifecycle import broker_cost_source as source

    detail = "research_cost_official_source_missing:2026-10-07;research_cost_official_source_missing:2026-10-08"
    row = {"quantity_research_cost": {"reason": detail}}
    reasons = review._quantity_research_pending_reasons([row])
    assert reasons == ["research_cost_official_source_missing"]
    queued = source.enqueue_pending(
        tmp_path, "2026-10-08", ["2026-10-07", "2026-10-08"], ["1"], reasons
    )
    assert set(queued["dates"]) == {"2026-10-07", "2026-10-08"}
    assert row["quantity_research_cost"]["reason"] == detail


def test_cached_stdin_guard_cannot_silently_skip_requested_cost_producer(monkeypatch):
    monkeypatch.setattr(review, "load_monitor_snapshot", lambda *a: {})
    frozen = {"date": "2026-10-08", "cached": True}
    monkeypatch.setattr(review, "guard_stdin_heavy_build", lambda **kw: frozen)
    assert review.build_trade_review_report("2026-10-08") is frozen
    with pytest.raises(ValueError, match="requires_native_report_build"):
        review.build_trade_review_report("2026-10-08", write_research_costs=True)


def test_native_report_does_not_decode_an_unused_cached_snapshot(monkeypatch, tmp_path):
    setup_report(monkeypatch, tmp_path)
    monkeypatch.setattr(review, "should_guard_stdin_heavy_build", lambda _: False)

    def forbidden(*args):
        pytest.fail("native report must not decode its discarded fallback")

    monkeypatch.setattr(review, "load_monitor_snapshot", forbidden)
    report = review.build_trade_review_report("2026-10-08")
    assert report["date"] == "2026-10-08"


@pytest.mark.parametrize("compressed", [False, True])
@pytest.mark.parametrize("reason", ["census", "warning", "missing"])
def test_known_invalid_carry_header_never_loads_large_snapshot(
    monkeypatch, tmp_path, compressed, reason
):
    import gzip
    import json

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    path = directory / "trade_review_2026-10-16.json"
    if compressed:
        path = path.with_suffix(".json.gz")
    header = dict(
        date="2026-10-15" if reason == "missing" else "2026-10-16",
        meta={"warnings": ["source warning"] if reason == "warning" else []},
        metrics={
            "open_scalp_position_projection_status": "source_gap_historical_open_census_not_reconstructible"
        },
    )
    opener = gzip.open if compressed else open
    with opener(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(header)[:-1] + ', "irrelevant": "')
        for _ in range(80):
            handle.write("x" * 65536)
        handle.write('"}')
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)

    def forbidden(*args):
        pytest.fail("known invalid source must be rejected before full decoding")

    monkeypatch.setattr(review, "load_monitor_snapshot", forbidden)
    events, receipts = review._prior_entry_fill_events(
        [{"id": 1, "status": "COMPLETED", "rec_date": "2026-10-16"}], "2026-10-17"
    )
    assert events == {}
    assert receipts == {"2026-10-16": {"status": "source_gap_entry_snapshot_" + reason}}


def test_carry_header_is_not_row_or_identity_approval(monkeypatch, tmp_path):
    import json

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    snapshot = dict(
        date="2026-10-16",
        meta={"warnings": []},
        metrics={
            "open_scalp_position_projection_status": "current_db_census",
            "open_scalp_position_projection_count": 1,
        },
        sections={"open_scalp_position_projection": []},
    )
    (directory / "trade_review_2026-10-16.json").write_text(json.dumps(snapshot))
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    loaded = []

    def load(*args):
        loaded.append(args)
        return snapshot

    monkeypatch.setattr(review, "load_monitor_snapshot", load)
    events, receipts = review._prior_entry_fill_events(
        [{"id": 1, "status": "COMPLETED", "rec_date": "2026-10-16"}], "2026-10-17"
    )
    assert len(loaded) == 1
    assert events == {}
    assert receipts["2026-10-16"]["status"] == "source_gap_entry_snapshot_census"


def test_corrupt_exact_receipt_cannot_be_masked_by_whole_position_fallback(
    monkeypatch, tmp_path
):
    from src.engine.lifecycle import broker_cost_source as source

    setup_report(monkeypatch, tmp_path)
    monkeypatch.setattr(
        exact,
        "load_receipt",
        lambda *a: (_ for _ in ()).throw(ValueError("corrupt_exact_receipt")),
    )
    monkeypatch.setattr(source, "load_source", lambda *a: {"source_sha256": "a" * 64})

    def forbidden(**kwargs):
        pytest.fail(
            "corrupt exact receipt must not be replaced by a different cost basis"
        )

    monkeypatch.setattr(source, "reconcile_position", lambda *a, **kw: forbidden(**kw))
    result = review.build_trade_review_report("2026-10-08")
    row = result["sections"]["completed_trade_projection"][0]
    assert row["economics_status"] == "actual_cost_invalid"
    assert row["broker_actual_fees_taxes_krw"] is row["realized_pnl_krw"] is None
    assert row["broker_actual_cost_observed"] is False
    assert row["strict_completion_status"] == "excluded"


def test_native_research_allocation_uses_open_turnover_without_promoting_canonical_cost(
    monkeypatch, tmp_path
):
    from datetime import datetime
    from src.engine.lifecycle import broker_cost_source as source

    calls = setup_report(monkeypatch, tmp_path, native=True)
    # The known open BUY competes with the completed record for this day's cost.
    calls["events"][-1] = replace(calls["events"][-1], timestamp="2026-10-08 09:59:00")
    for index, event in enumerate(calls["events"]):
        fields = {**event.fields}
        fields["order_no"] = {"B": "11", "S": "12"}.get(
            fields["order_no"], fields["order_no"]
        )
        fields["execution_no"] = {"B1": "1", "S1": "2", "S2": "3"}.get(
            fields["execution_no"], fields["execution_no"]
        )
        calls["events"][index] = replace(event, fields=fields)

    def transport(api, request):
        response = {"return_code": 0}
        if api == "ka00001":
            response["acctNo"] = "1234567890"
        else:
            key = "trst_ovrl_trde_prps_array" if api == "kt00015" else source.LISTS[api]
            response[key] = (
                [
                    {
                        "stk_cd": "123456",
                        "buy_qty": "3",
                        "sell_qty": "2",
                        "buy_amt": "30000",
                        "sell_amt": "20200",
                        "cmsn_alm_tax": "25",
                        "pl_amt": "175",
                    }
                ]
                if api == "ka10170"
                else []
            )
        return [response], {"page_count": 1, "continuous_terminal_received": True}

    transport.account_key = "research-test-account"
    source.collect(
        tmp_path,
        "2026-10-08",
        transport=transport,
        now=datetime(2026, 10, 8, 21, tzinfo=source.KST),
    )
    result = review.build_trade_review_report("2026-10-08", write_research_costs=True)
    row = result["sections"]["completed_trade_projection"][0]
    allocated = row["quantity_research_cost"]
    assert allocated["status"] == "research_cost_allocated", allocated
    assert allocated["allocated_fees_taxes_krw"] == 20
    assert allocated["allocated_net_pnl_krw"] == 180
    assert row["broker_actual_fees_taxes_krw"] is row["realized_pnl_krw"] is None
    assert row["strict_completion_status"] == "excluded"
    index = tmp_path / "runtime/initial_quantity_research_costs/2026-10-08/index.json"
    import json

    assert json.loads(index.read_text())["source_dates"] == ["2026-10-08"]


def reobserved_sell_fixture():
    trade, events, _, _, _ = fixture()
    base = events[-1]
    original = replace(
        base,
        timestamp="2026-10-08 10:01:02",
        fields={
            **base.fields,
            "id": "1",
            "holding_path_buy_fill_identity": "a" * 64,
            "broker_execution_provenance_complete": True,
            "broker_execution_time_source": "official_fid_908",
            "broker_execution_time_raw": "100101",
            "broker_execution_observed_at": "2026-10-08T10:01:01+09:00",
            "broker_execution_received_at": "2026-10-08T10:01:01.500000+09:00",
        },
    )
    repeated = replace(
        original,
        timestamp="2026-10-08 10:20:00",
        fields={
            **original.fields,
            "native_receipt_identity_schema": "broker_position_sell_receipt_v1",
            "native_receipt_position_key": "record:1",
            "native_receipt_record_id": "1",
            "native_receipt_stock_code": "123456",
            "native_receipt_order_no": "S",
            "native_receipt_execution_no": "S2",
            "native_receipt_buy_fill_identity": "a" * 64,
            "native_receipt_observed_at": "2026-10-08T10:01:01.500000+09:00",
        },
    )
    return trade, events[:-1] + [original, repeated]


def test_native_sell_reobservation_retains_original_broker_clock_and_evidence():
    trade, events = reobserved_sell_fixture()
    before = deepcopy(events)
    ledger = review._completed_execution_ledger(trade, events)
    assert (
        "source_gap_duplicate_sell_execution" not in ledger["strict_completion_reasons"]
    )
    assert ledger["sell_filled_qty"] == 2
    assert ledger["sell_fill_legs"][-1]["at"] == "2026-10-08 10:01:01"
    audit = ledger["sell_receipt_reobservation_audit"][0]
    assert audit["reobserved_count"] == 1
    assert audit["last_observed_at"] == "2026-10-08 10:20:00"
    assert (
        len(audit["native_identity_sha256"])
        == len(audit["source_event_digests_sha256"])
        == 64
    )
    position = review._quantity_research_position(trade, events, ledger, [])
    assert position["completed_at"] == "2026-10-08T10:01:01+09:00"
    assert events == before


def unknown_venue_reobserved_sell_fixture():
    trade, events = reobserved_sell_fixture()
    common = dict(
        order_no="12",
        execution_no="3",
        sell_qty=1,
        broker_execution_provenance_complete=False,
        broker_actual_execution_venue="UNKNOWN",
        broker_actual_execution_venue_source="official_exchange_fields_ambiguous_or_missing",
        actual_execution_venue="UNKNOWN",
        exit_effective_venue="UNKNOWN",
        actual_execution_venue_source="official_exchange_fields_ambiguous_or_missing",
        broker_route="SOR",
        broker_route_requested="SOR",
        main_lifecycle_broker_raw_envelope_schema="kiwoom_websocket_order_execution_00_values_v1",
        main_lifecycle_broker_raw_source_type="00",
        broker_execution_receive_time_source="websocket_packet_ingress",
        exit_execution_received_at="2026-10-08T10:01:01.500000+09:00",
        exit_market_session_time_source="websocket_packet_ingress",
        session_contract_version="market_session_contract_v2",
        exit_rule="scalp_trailing_take_profit",
        holding_path_terminal_signal_binding="same_position_buy_generation",
        holding_path_position_key="record:1",
        holding_path_signal_id="signal-1",
        holding_path_policy_bundle_sha256="b" * 64,
        main_lifecycle_broker_reconciled=True,
        main_lifecycle_reconciled_final_exit=True,
        sell_execution_receipt_quantity_contract_complete=True,
        sell_execution_receipt_unit_fill_consistent=True,
        exit_receipt_submission_custody_committed=True,
        exit_receipt_submission_custody_source_gap=False,
        remaining_sell_qty=0,
    )
    events[-2] = replace(events[-2], fields={**events[-2].fields, **common})
    events[-1] = replace(
        events[-1],
        fields={
            **events[-1].fields,
            **common,
            "native_receipt_order_no": "12",
            "native_receipt_execution_no": "3",
            "native_receipt_execution_venue_status": "unknown_preserved",
            "native_receipt_broker_provenance_complete": False,
            "native_receipt_source_gap": "actual_execution_venue_unresolved",
        },
    )
    return trade, events


@pytest.mark.parametrize("entry_trace", [False, True])
@pytest.mark.parametrize("string_fields", [False, True])
def test_acknowledged_unknown_venue_reobservation_is_one_fill_without_promoting_venue(
    string_fields, entry_trace
):
    trade, events = unknown_venue_reobserved_sell_fixture()
    if entry_trace:
        fields = {
            k: v
            for k, v in events[-1].fields.items()
            if not k.startswith("native_receipt_")
        }
        fields.update(
            native_receipt_identity_schema="native_entry_sell_receipt_v1",
            native_receipt_entry_trace_id="analyze_target:123456:1792038802347:4a778b1f",
            native_receipt_record_id="1",
            native_receipt_stock_code="123456",
            native_receipt_observed_at="2026-10-08T10:01:01.500000+09:00",
        )
        events[-1] = replace(events[-1], fields=fields)
    if string_fields:
        events = [
            replace(
                e,
                fields={
                    k: str(v) if isinstance(v, bool) else v for k, v in e.fields.items()
                },
            )
            for e in events
        ]
    before = deepcopy(events)
    ledger = review._completed_execution_ledger(trade, events)
    assert (
        "source_gap_duplicate_sell_execution" not in ledger["strict_completion_reasons"]
    )
    assert ledger["sell_filled_qty"] == 2
    assert ledger["sell_fill_legs"][-1]["at"] == "2026-10-08 10:01:01"
    normalized, audit = review._quantity_sell_receipt_observations(events)
    assert audit[0]["reobserved_count"] == 1
    assert normalized[-1].fields["actual_execution_venue"] == "UNKNOWN"
    assert str(normalized[-1].fields["broker_execution_provenance_complete"]) == "False"
    row = review._completed_trade_projection(trade, events, {})
    assert row["realized_pnl_krw"] is row["broker_actual_fees_taxes_krw"] is None
    assert events == before


@pytest.mark.parametrize(
    "fault",
    [
        "missing_identity",
        "source_gap",
        "custody",
        "route",
        "clock",
        "terminal",
        "conflict",
    ],
)
def test_unknown_venue_reobservations_require_native_terminal_proof(fault):
    trade, events = unknown_venue_reobserved_sell_fixture()
    fields = dict(events[-1].fields)
    mutations = {
        "source_gap": ("native_receipt_source_gap", "different_gap"),
        "custody": ("exit_receipt_submission_custody_committed", False),
        "route": ("broker_route_requested", "KRX"),
        "clock": ("native_receipt_observed_at", "2026-10-08T10:02:01+09:00"),
        "terminal": ("remaining_sell_qty", 1),
        "conflict": ("main_lifecycle_exit_price", 9999),
    }
    if fault == "missing_identity":
        fields.pop("native_receipt_execution_venue_status")
    else:
        k, v = mutations[fault]
        fields[k] = v
    events[-1] = replace(events[-1], fields=fields)
    ledger = review._completed_execution_ledger(trade, events)
    assert "source_gap_duplicate_sell_execution" in ledger["strict_completion_reasons"]
    assert ledger["sell_receipt_reobservation_audit"] == []


@pytest.mark.parametrize(
    "fault", [None, "partial_venue", "partial_authority", "venue", "authority", "extra"]
)
def test_unknown_venue_metadata_extensions_are_atomic_and_exact(fault):
    from datetime import datetime
    from src.engine.sniper_execution_receipts import _native_sell_receipt_identity

    trade, events = unknown_venue_reobserved_sell_fixture()
    fields = {
        k: v
        for k, v in events[-1].fields.items()
        if not k.startswith("native_receipt_")
    }
    identity = _native_sell_receipt_identity(
        {"id": 1, "code": "123456"},
        "123456",
        "1",
        "sell_completed",
        fields,
        datetime.fromisoformat(fields["exit_execution_received_at"]),
    )
    assert "native_receipt_operational_venue" in identity
    assert "native_receipt_venue_assignment_authority" in identity
    if fault == "partial_venue":
        identity.pop("native_receipt_venue_assignment_authority")
    elif fault == "partial_authority":
        identity.pop("native_receipt_operational_venue")
    elif fault == "venue":
        identity["native_receipt_operational_venue"] = "KRX"
    elif fault == "authority":
        identity["native_receipt_venue_assignment_authority"] = "unverified_authority"
    elif fault == "extra":
        identity["native_receipt_unrecognized_metadata"] = "unknown"
    events[-1] = replace(events[-1], fields={**fields, **identity})
    before = deepcopy(events)
    ledger = review._completed_execution_ledger(trade, events)
    assert (
        "source_gap_duplicate_sell_execution" in ledger["strict_completion_reasons"]
    ) is (fault is not None)
    assert bool(ledger["sell_receipt_reobservation_audit"]) is (fault is None)
    assert events == before


@pytest.mark.parametrize(
    "fault",
    [
        "quantity",
        "fees",
        "owner",
        "account",
        "route",
        "authority",
        "clock",
        "source_gap",
        "native_identity",
        "unwrapped",
        "unknown",
    ],
)
def test_sell_identity_collision_without_full_unchanged_native_proof_stays_excluded(
    fault,
):
    trade, events = reobserved_sell_fixture()
    fields = dict(events[-1].fields)
    mutations = {
        "quantity": ("main_lifecycle_exit_qty", 2),
        "fees": ("main_lifecycle_fees_taxes_krw", 0),
        "owner": ("holding_cost_owner", "manual"),
        "account": ("holding_cost_account_scope_sha256", "c" * 64),
        "route": ("broker_route", "NXT"),
        "authority": ("actual_order_submitted", False),
        "clock": ("native_receipt_observed_at", "2026-10-08T10:02:01+09:00"),
        "source_gap": ("broker_execution_provenance_complete", False),
        "native_identity": ("native_receipt_execution_no", "S3"),
        "unknown": ("future_unclassified_field", "changed"),
    }
    if fault == "unwrapped":
        fields = {
            k: v for k, v in fields.items() if not k.startswith("native_receipt_")
        }
    else:
        key, value = mutations[fault]
        fields[key] = value
    events[-1] = replace(events[-1], fields=fields)
    ledger = review._completed_execution_ledger(trade, events)
    assert "source_gap_duplicate_sell_execution" in ledger["strict_completion_reasons"]
    assert ledger["sell_receipt_reobservation_audit"] == []


def registry_fill_fixture():
    trade, _, ledger, _, _ = fixture()
    anchor = dict(
        intent_id="intent-1",
        account_key="acct",
        order_date="2026-10-08",
        owner_id="main_scalping:1",
        owner_type="main_scalping",
        position_id="main_scalping:1",
        symbol="123456",
        side="BUY",
        action="NEW",
        route="SOR",
        quantity=2,
    )
    reserved = {**anchor, "event": "INTENT_RESERVED", "state": "INTENT_RESERVED"}
    bound = {
        **anchor,
        "event": "ORDER_BOUND",
        "state": "ORDER_BOUND",
        "broker_order_no": "B",
    }
    filled = {
        **bound,
        "event": "FILL_RECORDED",
        "execution_no": "B1",
        "filled_qty": 2,
        "fill_amount": 20000,
    }
    stale = {
        **bound,
        "event": "STALE_TERMINAL_SNAPSHOT_RECONCILED",
        "state": "ORDER_TERMINAL",
        "filled_qty": 2,
        "fill_amount": 20000,
        "event_hash": "b" * 64,
    }
    generation = dict(status="verified", sha256="a" * 64, tail_hash="b" * 64)
    return trade, ledger, [reserved, bound, filled, stale], generation


def test_prior_carry_registry_custody_requires_exact_fills_and_never_creates_parent_or_terminal():
    trade, ledger, rows, generation = registry_fill_fixture()
    proof = review._quantity_registry_fill_custody(trade, ledger, rows, generation)
    assert len(proof) == 1 and proof[0]["filled_qty"] == 2
    assert (
        proof[0]["owner_id"] == "main_scalping:1" and proof[0]["account_key"] == "acct"
    )
    assert proof[0]["state"] == "full" and proof[0]["terminal_observed"] is False
    assert "parent_id" not in proof[0] and proof[0]["cost_krw"] is None


@pytest.mark.parametrize(
    "fault",
    [
        "missing_fill",
        "wrong_fill",
        "stale_only",
        "bound_order",
        "owner",
        "account",
        "route",
        "extra_execution",
        "partial",
        "unverified",
    ],
)
def test_prior_registry_custody_rejects_ambiguous_or_stale_only_sources(fault):
    trade, ledger, rows, generation = registry_fill_fixture()
    if fault == "missing_fill":
        rows = [r for r in rows if r["event"] != "FILL_RECORDED"]
    elif fault == "wrong_fill":
        rows[2]["fill_amount"] = 19999
    elif fault == "stale_only":
        rows = rows[-1:]
    elif fault == "bound_order":
        rows.append({**rows[1], "broker_order_no": "OTHER"})
    elif fault == "owner":
        rows[0]["owner_id"] = "manual:1"
    elif fault == "account":
        rows[1]["account_key"] = "other"
    elif fault == "route":
        rows[1]["route"] = "NXT"
    elif fault == "extra_execution":
        rows.append(
            {**rows[2], "execution_no": "B2", "filled_qty": 3, "fill_amount": 30000}
        )
    elif fault == "partial":
        for row in rows:
            row["quantity"] = 3
    else:
        generation["status"] = "source_gap"
    assert review._quantity_registry_fill_custody(trade, ledger, rows, generation) == []


def test_research_registry_read_is_bounded_and_detects_source_change(
    monkeypatch, tmp_path
):
    from src.engine.lifecycle import research_input_budget as budget
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry

    trade, ledger, rows, _ = registry_fill_fixture()
    path = tmp_path / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n")
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        OrderOwnerRegistry, "verified_events_snapshot", lambda *a, **kw: deepcopy(rows)
    )
    selected, generation = review._quantity_research_custody(
        [(trade, [], {}, ledger)], []
    )
    assert selected["1"][0]["filled_qty"] == 2
    assert generation["status"] == "verified" and budget.health()["used_bytes"] == 0
    path.write_text("{}\n{}\n")
    with pytest.raises(
        ValueError, match="quantity_research_registry_changed_during_report"
    ):
        review._verify_quantity_research_registry(generation)
    with path.open("wb") as handle:
        handle.truncate(4 * 1024 * 1024 + 1)
    selected, generation = review._quantity_research_custody(
        [(trade, [], {}, ledger)], []
    )
    assert selected["1"] == [] and generation["status"] == "source_gap"
    assert generation["reason"] == "quantity_research_registry_partition_required"
    assert budget.health()["used_bytes"] == 0


def test_research_registry_budget_failure_cannot_be_silently_demoted_to_missing(
    monkeypatch, tmp_path
):
    from src.engine.lifecycle import research_input_budget as budget

    trade, ledger, _, _ = registry_fill_fixture()
    path = tmp_path / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n")
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    with budget.Claim(budget.LIMIT_BYTES):
        with pytest.raises(
            ValueError, match="shared_research_budget_partition_resume_required"
        ):
            review._quantity_research_custody([(trade, [], {}, ledger)], [])


@pytest.mark.parametrize("fault", ["owner", "account", "intent"])
def test_research_registry_rejects_foreign_claim_of_same_exact_order(fault):
    trade, ledger, rows, generation = registry_fill_fixture()
    foreign = {**rows[2]}
    foreign[
        {"owner": "owner_id", "account": "account_key", "intent": "intent_id"}[fault]
    ] = "foreign"
    rows.append(foreign)
    assert review._quantity_registry_fill_custody(trade, ledger, rows, generation) == []


@pytest.mark.parametrize("fault", ["chain", "missing_lock"])
def test_research_registry_corruption_is_local_gap_preserving_verified_native_rows(
    monkeypatch, tmp_path, fault
):
    from src.trading.order.owner_custody_registry import (
        OrderOwnerRegistry,
        OwnerRegistryError,
    )

    trade, ledger, _, _ = registry_fill_fixture()
    path = tmp_path / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n")
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)

    def broken(*a, **kw):
        if fault == "chain":
            raise OwnerRegistryError("owner_registry_hash_chain_invalid")
        raise FileNotFoundError("registry_lock_missing")

    monkeypatch.setattr(OrderOwnerRegistry, "verified_events_snapshot", broken)
    native = [custody(record=2)]
    native_ledger = {**ledger}
    other = {**trade, "id": 2}
    selected, generation = review._quantity_research_custody(
        [(trade, [], {}, ledger), (other, [], {}, native_ledger)], native
    )
    assert selected["1"] == [] and selected["2"] == native
    assert generation["status"] == "source_gap"


@pytest.mark.parametrize("fault", ["manual", "foreign_account", "explicit_conflict"])
def test_verified_registry_cannot_override_contradictory_native_custody(
    monkeypatch, tmp_path, fault
):
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry

    trade, ledger, rows, _ = registry_fill_fixture()
    path = tmp_path / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n")
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        OrderOwnerRegistry, "verified_events_snapshot", lambda *a, **kw: deepcopy(rows)
    )
    native = custody()
    native["account_key"] = "acct"
    native["filled_qty"] = 1
    if fault == "manual":
        native["owner_id"] = "manual:1"
    elif fault == "foreign_account":
        native["account_key"] = "foreign"
    else:
        native["source_quality_reasons"] = ["registry_submit_identity_mismatch"]
    selected, _ = review._quantity_research_custody([(trade, [], {}, ledger)], [native])
    assert selected["1"] == [native]


def test_registry_concurrent_change_during_native_read_is_fatal(monkeypatch, tmp_path):
    from src.trading.order.owner_custody_registry import (
        OrderOwnerRegistry,
        OwnerRegistryConflict,
    )

    trade, ledger, _, _ = registry_fill_fixture()
    path = tmp_path / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n")
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)

    def changed(*a, **kw):
        raise OwnerRegistryConflict("owner_registry_changed_during_read")

    monkeypatch.setattr(OrderOwnerRegistry, "verified_events_snapshot", changed)
    with pytest.raises(
        OwnerRegistryConflict, match="owner_registry_changed_during_read"
    ):
        review._quantity_research_custody([(trade, [], {}, ledger)], [])


def test_native_handoff_accepts_reserve_bind_exact_full_fill_and_keeps_conflicting_order_closed():
    trade, ledger, journal, _ = registry_fill_fixture()
    _, events, _, _, _ = fixture()
    fields = dict(
        actual_order_submitted=True,
        broker_order_no="B",
        buy_account_key="acct",
        buy_parent_id="parent",
        buy_child_id="parent:0",
        entry_submit_attempt_id="parent",
        owner_registry_intent_id="intent-1",
        buy_owner_id="main_scalping:1",
        buy_owner_type="main_scalping",
        broker_route="SOR",
        submitted_qty=2,
        requested_qty=2,
        buy_planned_qty=2,
        buy_registry_mode="registered",
    )
    sent = dict(
        stage="order_leg_sent",
        emitted_date="2026-10-08",
        record_id=1,
        stock_code="123456",
        fields=fields,
    )
    fills = [replace(e, fields={**e.fields, "id": "1"}) for e in events]
    result = review._buy_parent_handoff_projection(
        "2026-10-08", [sent], journal, fills, [trade]
    )
    assert result["counts"]["valid"] == 1 and result["rows"][0]["state"] == "full"
    conflict = journal + [{**journal[1], "broker_order_no": "OTHER"}]
    result = review._buy_parent_handoff_projection(
        "2026-10-08", [sent], conflict, fills, [trade]
    )
    assert result["counts"]["valid"] == 0
    assert result["rows"][0]["state"] == "quarantined"


def _large_prior_snapshot(tmp_path, *, compressed=False, fault=None):
    import gzip
    import hashlib
    import json
    from pathlib import Path

    day = "2026-10-15"
    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    logical = directory / f"trade_review_{day}.json"
    event = dict(
        stage="position_rebased_after_fill",
        timestamp=day + " 09:00:00",
        fields=dict(
            id="7", order_no="11", execution_no="1", fill_qty=2, fill_price=100
        ),
    )
    if fault == "field_order":
        event = dict(
            fields=event["fields"], stage=event["stage"], timestamp=event["timestamp"]
        )
    row = dict(
        id=7,
        code="005930",
        name="test",
        avg_down_rebound_blocker_summary=[],
        timeline=[
            dict(
                stage="irrelevant_source",
                timestamp=day + " 09:00:00",
                fields={"unused": "x" * 100000},
            ),
            event,
        ],
    )
    snapshot = dict(
        date=day,
        meta={"warnings": []},
        metrics=dict(
            open_scalp_position_projection_status="current_db_census",
            open_scalp_position_projection_count=1,
        ),
        sections=dict(
            unused_body="x" * (9 * 1024 * 1024),
            nested={"artificial_root": 1},
            open_scalp_position_projection=[row],
        ),
    )
    # Place a nested key two spaces before the streaming overlap. Without a
    # boundary sentinel its remaining indentation looks like a root key.
    probe = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    key_at = probe.index(b'      "artificial_root"')
    delta = ((1024 * 1024 - 256 - 4) - key_at) % (1024 * 1024)
    snapshot["sections"]["unused_body"] += "x" * delta
    if fault == "duplicate_id":
        snapshot["sections"]["open_scalp_position_projection"].append(deepcopy(row))
        snapshot["metrics"]["open_scalp_position_projection_count"] = 2
    body = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    physical = Path(str(logical) + ".gz") if compressed else logical
    physical.write_bytes(gzip.compress(body) if compressed else body)
    manifest = (
        directory / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    )
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps(
            dict(
                target_date=day,
                profile="postclose_exit",
                snapshot_paths={"trade_review": str(logical)},
                snapshot_sha256={
                    "trade_review": (
                        "0" * 64
                        if fault == "hash"
                        else hashlib.sha256(body).hexdigest()
                    )
                },
            )
        )
    )
    if fault == "manifest_missing":
        manifest.unlink()
    return snapshot, physical, manifest


@pytest.mark.parametrize("compressed", [False, True])
def test_large_prior_native_projection_preserves_fill_without_full_snapshot(
    tmp_path, monkeypatch, compressed
):
    snapshot, path, manifest = _large_prior_snapshot(tmp_path, compressed=compressed)
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        review,
        "load_monitor_snapshot",
        lambda *a: pytest.fail("full large snapshot decode"),
    )
    events, receipts = review._prior_entry_fill_events(
        [dict(id=7, rec_date="2026-10-15", status="COMPLETED")], "2026-10-16"
    )
    assert len(events["7"]) == 1 and events["7"][0].fields["execution_no"] == "1"
    receipt = receipts["2026-10-15"]
    assert receipt["status"] == "sealed_entry_snapshot"
    assert receipt["schema"] == "prior_entry_fill_projection_v1"
    assert receipt["source_path"] == str(path) and receipt["manifest_path"] == str(
        manifest
    )
    assert (
        len(receipt["source_decoded_sha256"]) == 64
        and len(receipt["projection_sha256"]) == 64
    )
    assert "logical_sha256" not in receipt


@pytest.mark.parametrize(
    "fault", ["hash", "manifest_missing", "field_order", "duplicate_id"]
)
def test_large_prior_projection_never_promotes_invalid_provenance_or_census(
    tmp_path, monkeypatch, fault
):
    _large_prior_snapshot(tmp_path, fault=fault)
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        review,
        "load_monitor_snapshot",
        lambda *a: pytest.fail("invalid source cannot trigger full decode"),
    )
    events, receipts = review._prior_entry_fill_events(
        [dict(id=7, rec_date="2026-10-15", status="COMPLETED")], "2026-10-16"
    )
    assert not events
    assert receipts["2026-10-15"]["status"] != "sealed_entry_snapshot"


@pytest.mark.parametrize(
    "source_format", ["typed", "log_strings", "structured", "foreign_record"]
)
def test_reobserved_broker_receipt_without_buy_lineage_collapses_without_restoring_economics(
    source_format,
):
    from datetime import datetime
    from src.engine.sniper_execution_receipts import _native_sell_receipt_identity

    _, events = unknown_venue_reobserved_sell_fixture()
    original = events[-2]
    fields = {
        k: v for k, v in original.fields.items() if not k.startswith("holding_path_")
    }
    fields.update(
        holding_path_terminal_signal_binding="source_gap_generation_mismatch",
        order_no="0000012",
        execution_no="3",
        main_lifecycle_exit_qty=1,
        main_lifecycle_exit_price=10100.0,
        sell_qty=1,
        cumulative_sell_qty=1,
        **{
            "9203": "0000012",
            "9001": "123456",
            "900": "1",
            "902": "0",
            "903": "10100",
            "905": "-매도",
            "907": "1",
            "908": "100101",
            "909": "3",
            "910": "10100",
            "911": "1",
            "913": "체결",
            "914": "10100",
            "915": "1",
            "2134": "0",
            "2135": "SOR",
            "2136": "Y",
        },
    )
    at = datetime.fromisoformat(fields["exit_execution_received_at"])
    identity = _native_sell_receipt_identity(
        {"id": 1, "code": "123456"}, "123456", 1, "sell_completed", fields, at
    )
    assert identity and identity["native_receipt_entry_lineage_status"] == "source_gap"
    original = replace(original, fields=fields)
    repeated = replace(
        original, timestamp="2026-10-08 10:20:00", fields={**fields, **identity}
    )
    if source_format in {"log_strings", "structured"}:

        def logged(event):
            return replace(
                event,
                fields={
                    k: str(v)
                    for k, v in event.fields.items()
                    if source_format != "structured" or k != "id"
                },
            )

        original, repeated = logged(original), logged(repeated)
    rows = [original, repeated]
    before = deepcopy(rows)
    normalized, audit = review._quantity_sell_receipt_observations(
        rows,
        record_id=(
            "1"
            if source_format == "structured"
            else "2" if source_format == "foreign_record" else None
        ),
    )
    if source_format == "foreign_record":
        assert normalized == rows and audit == []
        return
    assert len(normalized) == 1 and audit[0]["reobserved_count"] == 1
    assert "holding_path_buy_fill_identity" not in normalized[0].fields
    assert normalized[0].fields["broker_actual_execution_venue"] == "UNKNOWN"
    assert rows == before


@pytest.mark.parametrize("fault", [None, "missing", "clock", "foreign", "partial"])
def test_first_cost_producer_uses_same_native_buy_as_quantity_refresh(
    monkeypatch, tmp_path, fault
):
    import json
    from src.engine.lifecycle import broker_cost_allocation as allocation
    from src.engine.ai import holding_exit_vote as vote
    from src.tests.test_broker_cost_allocation import source, position
    from src.tests.test_main_stop_research_cost import registry

    day = "2026-10-08"
    item = position(1)
    registry(tmp_path, [item])
    stock = dict(
        id=1,
        code="005930",
        buy_time=day + "T10:00:00",
        buy_qty=2,
        buy_price=10000,
        entry_filled_qty=2,
        _entry_receipt_filled_by_order_no={"11": 2},
        _entry_receipt_executions_by_order_no={
            "11": {
                "101": dict(
                    cumulative_qty=2,
                    cumulative_exec_amount=20000,
                    order_qty=2,
                    remaining_qty=0,
                    unit_exec_qty=2,
                    unit_exec_price=10000,
                )
            }
        },
        _add_receipt_filled_by_order_no={},
        _add_receipt_executions_by_order_no={},
    )
    if fault == "clock":
        stock["buy_time"] += ".100000"
    if fault != "missing":
        vote.persist_buy_fill_receipt(stock, tmp_path)
        path = tmp_path / "runtime/holding_buy_fill_receipts/1.json"
        if fault in {"foreign", "partial"}:
            body = json.loads(path.read_bytes())
            if fault == "foreign":
                body["source"] = "legacy_path_vote_exact_buy_legs"
            else:
                body["receipt_fields"]["_entry_receipt_executions_by_order_no"]["11"][
                    "101"
                ].update(order_qty=3, remaining_qty=1)
            path.write_text(json.dumps(body))
    trade = dict(
        id=1,
        code="005930",
        buy_time=day + "T10:00:00",
        buy_qty=2,
        buy_price=10000,
        status="COMPLETED",
    )
    missing = [
        "source_gap_buy_fill_missing",
        "source_gap_negative_position_balance",
        "source_gap_position_quantity_not_conserved",
    ]
    ledger = dict(buy_fill_legs=[], strict_completion_reasons=missing)
    projected = {**item, "buy_legs": [], "execution_source_quality_reasons": missing}
    canonical = deepcopy(ledger)
    monkeypatch.setattr(review, "DATA_DIR", tmp_path)
    selected, generation = review._quantity_research_custody(
        [(trade, [], {}, ledger)],
        [],
        research_positions=[projected],
    )
    assert ledger == canonical  # Canonical event/quantity evidence is unchanged.
    observed = source(tmp_path)
    first = allocation.build_research_cost_allocations({day: observed}, [projected])
    if fault is None:
        assert first["1"]["status"] == "research_cost_allocated"
        assert projected["buy_legs"] and selected["1"]
        assert (
            generation["native_buy_recoveries"]["1"]["clock_source"]
            == "native_registry_fill_observed_at_kst"
        )
        review._verify_quantity_research_registry(generation)
        proof = tmp_path / "runtime/holding_buy_fill_receipts/1.json"
        proof.write_bytes(proof.read_bytes() + b" ")
        with pytest.raises(ValueError, match="research_native_buy_receipt_changed"):
            review._verify_quantity_research_registry(generation)
    else:
        assert first["1"]["status"] == "research_cost_invalid"
        assert not projected["buy_legs"]
