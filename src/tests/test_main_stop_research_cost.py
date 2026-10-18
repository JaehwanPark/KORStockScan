"""Native completion + later cost overlay, custody and research-only scope."""
from copy import deepcopy
import hashlib
import json

import pytest

from src.engine.lifecycle import main_stop_research_cost as stop
from src.engine.lifecycle import broker_cost_allocation as allocation
from src.engine.lifecycle import broker_cost_reconciliation as exact
from src.engine.lifecycle import broker_cost_source as official
from src.engine.lifecycle.holding_window_generation import seal_dependency_receipt
from src.engine.lifecycle.snapshot_archive import snapshot_identity
from src.engine.sniper_trade_review_report import completed_census_manifest
from src.tests.test_broker_cost_allocation import position, source, DAY
from src.tests.test_broker_cost_reconciliation import seal as exact_seal


def registry(root, positions):
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, REGISTRY_SCHEMA
    path = root / "runtime/order_owner_registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows, previous = [], "0" * 64
    for item in positions:
        leg = item["buy_legs"][0]
        owner = "main_scalping:" + item["record_id"]
        anchor = dict(schema=REGISTRY_SCHEMA, intent_id="intent-" + item["record_id"],
            account_key="test_account", order_date=DAY, owner_type="main_scalping",
            owner_id=owner, position_id=owner, symbol=item["symbol"], side="BUY", action="NEW",
            route=leg["route"], quantity=leg["qty"])
        events = [dict(anchor, event="INTENT_RESERVED", state="INTENT_RESERVED"),
            dict(anchor, event="ORDER_BOUND", state="ORDER_BOUND", broker_order_no=leg["order_no"]),
            dict(anchor, event="FILL_RECORDED", state="ORDER_BOUND", broker_order_no=leg["order_no"],
                 execution_no=leg["execution_no"], filled_qty=leg["qty"], fill_amount=leg["qty"] * leg["price"])]
        for row in events:
            row["previous_hash"] = previous
            row["event_hash"] = hashlib.sha256(previous.encode() + OrderOwnerRegistry._canonical(row)).hexdigest()
            previous = row["event_hash"]
            rows.append(row)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    path.with_suffix(path.suffix + ".lock").touch()


def native(root, positions, *, mutate=None):
    directory = root / "report/monitor_snapshots"
    directory.mkdir(parents=True, exist_ok=True)
    raw = directory / f"trade_review_{DAY}.json"
    raw.write_text('{"original_native_snapshot":true}\n')
    rows = []
    for item in positions:
        row = dict(id=int(item["record_id"]), rec_date=DAY, code=item["symbol"], status="COMPLETED",
            strategy="SCALPING", position_tag="SCALP_BASE", buy_qty=2, buy_price=10000, sell_price=10100,
            buy_time=DAY + " 10:00:00", sell_time=DAY + " 10:01:00", completion_observed_date=DAY,
            exact_sell_fill_time=item["completed_at"], sell_time_forbidden_for_intraday_horizon=False,
            buy_fill_legs=deepcopy(item["buy_legs"]), sell_fill_legs=deepcopy(item["sell_legs"]),
            buy_filled_qty=2, sell_filled_qty=2, buy_fill_amount=20000, sell_fill_amount=20200,
            sell_quantity_conserved=True, position_residual_qty=0,
            main_automatic_management_allowed=False, main_custody_source_sha256=None,
            terminal_decision_authority="broker_sell_fill_observation_only", terminal_population_scope="real_record_bound",
            strict_completion_status="excluded", strict_completion_reasons=["source_gap_broker_actual_cost_missing"],
            exit_signal={"exit_rule": "scalp_hard_stop", "exit_decision_source": "HARD_STOP", "fields": {}},
            profit_rate=None, realized_pnl_krw=None, broker_actual_fees_taxes_krw=None,
            timeline=[{"not_used": "x" * 10000}])
        contract = dict(schema="holding_exit_signal_receipt_v1", source_date=DAY,
            signal_at=DAY + "T10:00:58+09:00", signal_id="signal-" + item["record_id"],
            record_id=item["record_id"], code=item["symbol"], position_key="record:" + item["record_id"],
            buy_fill_identity="a" * 64, strategy="SCALPING", decision_owner_type="main_scalping",
            exit_rule="scalp_hard_stop")
        row["exit_signal"].update(inferred=False, binding_status="same_order_generation",
            fields={"exit_signal_contract": contract, "exit_signal_contract_sha256": exact.digest(contract),
                    "exit_signal_buy_fill_identity": "a" * 64},
            submission={"owner_id": "main_scalping:" + item["record_id"], "account_key": "test_account",
                        "order_no": item["sell_legs"][-1]["order_no"], "broker_route": "SOR",
                        "submitted_at": DAY + " 10:00:59", "sell_submit_generation": "submit-1",
                        "sell_submit_context_sha256": "b" * 64})
        if mutate:
            mutate(row)
        rows.append(row)
    value = dict(schema="trade_review_completed_projection_sidecar_v1", date=DAY,
        code=None, since=None, snapshot_identity=snapshot_identity(raw),
        metrics={"canonical_completed_trades": len(rows)},
        meta={"snapshot_profile": "postclose_exit", "sell_completed_event_ids": [r["id"] for r in rows],
              "completion_event_id_count": len(rows), "completion_event_unresolved_id_count": 0,
              "trailing_event_source_receipts": [{"source_sha256": "a" * 64}],
              "actual_cost_source_generation": exact.source_generation(root, DAY)},
        sections={"completed_trade_projection": rows})
    value["meta"]["completed_census_manifest"] = completed_census_manifest(value)
    value["artifact_sha256"] = stop._canonical(value)
    sidecar = raw.with_suffix(".completed_projection.json")
    sidecar.write_text(json.dumps(value, ensure_ascii=False))
    seal_dependency_receipt(sidecar, value)
    return rows, sidecar


def setup(tmp_path, *, mutate=None, publish=True):
    data, costs = tmp_path / "native", tmp_path / "costs"
    positions = [position(1), position(2)]
    for item in positions:
        item["custody_rows"][0]["record_id"] = item["record_id"]
    rows, sidecar = native(data, positions, mutate=mutate)
    registry(data, positions)
    observed = source(costs)
    official.atomic(official.source_path(costs, DAY), observed)
    receipts = allocation.build_research_cost_allocations({DAY: observed}, positions)
    if publish:
        allocation.persist_research_costs(costs, DAY, receipts, [DAY])
    return data, costs, rows, sidecar, receipts


def prepare(data, costs, cutoff=None):
    return stop.prepare_economic_source(data, DAY, cutoff, cost_data_root=costs)


def result(data, costs, prepared, record=1, cutoff=None):
    return stop.prepare_economic_record({"id": record}, data_root=data, source_date=DAY,
        knowledge_cutoff=cutoff, cost_data_root=costs, prepared=prepared)


def test_normal_selection_consumes_real_batch_and_preserves_allocated_grade(tmp_path,monkeypatch):
    import shutil
    data,costs,_,_,_=setup(tmp_path)
    shutil.copytree(costs/'runtime',data/'runtime',dirs_exist_ok=True)
    calls=[];original=stop._native_projection
    def observed(*args):calls.append(args);return original(*args)
    monkeypatch.setattr(stop,'_native_projection',observed)
    before=stop.selection_source_generation(data,[DAY])
    rows=list(stop.selection_completed_evidence(data,[DAY]))
    assert len(calls)==1 and len(rows)==2
    economics=rows[0]['main_stop_economic_source']
    from src.engine import sniper_execution_receipts
    from src.engine.scalping.main_stop_quantity_source import build_quantity_source
    from src.engine.scalping.position_peak_ledger import position_cycle_id
    stock=dict(id=1,code='005930',strategy='SCALPING',entry_requested_qty=2,requested_buy_qty=2,
        pending_entry_orders=[dict(ord_no='11',qty=2,filled_qty=0,status='OPEN')])
    sniper_execution_receipts._resolve_entry_effective_fill_qty(target_stock=stock,code='005930',
        order_no='11',exec_price=10000,exec_qty=2,order_qty=2,remaining_qty=0,
        cumulative_exec_amount=20000,execution_no='101',unit_exec_qty=2,unit_exec_price=10000)
    stock.update(buy_qty=2,buy_price=10000.)
    at=allocation._clock(DAY+' 10:00:01').timestamp()
    source=dict(record_id=1,quantity=2,item='005930_AL',buy_basis_krw=20000.,at=at,
        position_key=position_cycle_id(stock),quantity_source=build_quantity_source(stock,at=at))
    assert stop.selection_grade(economics,source)=='broker_total_allocated'
    assert economics['actual_execution_cost'] is False
    assert economics['original_economics_scope']=='initial_quantity_research_only'
    assert stop.selection_source_generation(data,[DAY])==before
    wrong=deepcopy(economics);wrong['actual_execution_cost']=True
    wrong['artifact_sha256']=exact.digest({k:v for k,v in wrong.items() if k!='artifact_sha256'})
    assert stop.selection_grade(wrong,source) is None
    assert stop.selection_grade(economics,{**source,'quantity':3}) is None
    # Late cost corrections and custody mutations each invalidate the normal
    # publisher input identity; the original report stays untouched.
    path=official.source_path(data,DAY)
    raw=path.read_bytes();path.write_bytes(raw+b'\n')
    assert stop.selection_source_generation(data,[DAY])!=before


def test_normal_batch_closes_claims_after_consumer_abandonment(tmp_path,monkeypatch):
    import shutil
    data,costs,_,_,_=setup(tmp_path)
    shutil.copytree(costs/'runtime',data/'runtime',dirs_exist_ok=True)
    closed=[];original=stop.PreparedEconomicSource.close
    def close(self):closed.append(self);return original(self)
    monkeypatch.setattr(stop.PreparedEconomicSource,'close',close)
    stream=stop.selection_completed_evidence(data,[DAY])
    next(stream);stream.close()
    assert len(closed)==1 and not closed[0]._memory_claims and not closed[0].rows


def test_routine_selection_consumer_never_rehashes_large_native_reports(tmp_path,monkeypatch):
    import shutil
    data,costs,_,sidecar,_=setup(tmp_path)
    shutil.copytree(costs/'runtime',data/'runtime',dirs_exist_ok=True)
    expected=stop.selection_source_generation(data,[DAY])
    original=stop.byte_generation;reads=[]
    def counted(path):reads.append(str(path));return original(path)
    monkeypatch.setattr(stop,'byte_generation',counted)
    assert stop.verify_selection_source_generation(data,expected)
    assert reads==[]
    assert stop.verify_selection_source_generation(data,expected,verify_full=True)
    assert str(sidecar) in reads
    reads.clear()
    sidecar.write_bytes(sidecar.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='cost_generation_changed'):
        stop.verify_selection_source_generation(data,expected)
    assert reads==[]


def test_absent_native_source_appearance_invalidates_routine_selection_without_hashing(tmp_path,monkeypatch):
    expected=stop.selection_source_generation(tmp_path,[DAY])
    registry_path=tmp_path/'runtime/order_owner_registry.jsonl'
    registry_path.parent.mkdir();registry_path.write_text('{}\n')
    def forbidden(*args,**kwargs):raise AssertionError('unexpected full native hash')
    monkeypatch.setattr(stop,'byte_generation',forbidden)
    with pytest.raises(ValueError,match='cost_generation_changed'):
        stop.verify_selection_source_generation(tmp_path,expected)


def test_later_cost_overlay_reuses_original_native_fills_without_mutation(tmp_path):
    data, costs, rows, sidecar, receipts = setup(tmp_path)
    originals = {path: path.read_bytes() for path in (sidecar, sidecar.with_suffix(sidecar.suffix + ".dependencies.json"))}
    prepared = prepare(data, costs)
    assert prepared.status == "verified", prepared.reason
    values = [result(data, costs, prepared, record) for record in (1, 2)]
    assert [v["research_net_pnl_krw"] for v in values] == [189, 190]
    for value in values:
        assert value["status"] == "eligible", value["reason"]
        assert value["evidence_grade"] == "broker_total_allocated"
        assert value["original_economics_scope"] == "initial_quantity_research_only"
        assert value["economics_scope"] == "main_stop_research_only"
        assert value["actual_execution_cost"] is value["allowed_runtime_apply"] is value["runtime_effect"] is False
        assert value["custody_status"] == "verified_registry_fill_census"
        assert value["cost_receipt_sha256"] == receipts[value["record_id"]]["receipt_sha256"]
    assert prepared.source_reference["original_cost_generation"] != prepared.cost_generation
    assert all(row["realized_pnl_krw"] is None for row in rows)
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert prepared.validate_unchanged()


def test_exact_execution_statement_is_semantically_reconciled(tmp_path):
    data, costs, rows, _, _ = setup(tmp_path)
    row = rows[0]
    legs = [dict(side=side, trade_date=DAY, route=leg["route"], order_no=leg["order_no"],
                 execution_no=leg["execution_no"], price=leg["price"], qty=leg["qty"], fee_krw=1, tax_krw=0 if side == "BUY" else 7)
            for side, items in (("BUY", row["buy_fill_legs"]), ("SELL", row["sell_fill_legs"])) for leg in items]
    receipt = dict(schema=exact.SCHEMA, status="complete", revision=1, position_key="record:1", symbol=row["code"],
        owner="main", account_scope_sha256=exact.digest(["broker_account", "test_account"]),
        buy_fill_identity=exact.digest(row["buy_fill_legs"]), completion_observed_date=DAY,
        cost_available_at=DAY + "T21:00:00+09:00", reconciled_at=DAY + "T21:00:01+09:00", legs=legs, realized_pnl_krw=191)
    exact_seal(receipt)
    path = exact.receipt_path(costs, DAY, "1")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt))
    value = result(data, costs, prepare(data, costs))
    assert value["status"] == "eligible", value["reason"]
    assert value["evidence_grade"] == "exact_execution" and value["actual_execution_cost"] is True
    assert value["research_cost_krw"] == 9 and value["research_net_pnl_krw"] == 191
    receipt["legs"][-1]["price"] = 9999
    exact_seal(receipt)
    path.write_text(json.dumps(receipt))
    rejected = result(data, costs, prepare(data, costs))
    assert rejected["status"] == "source_gap" and rejected["research_net_pnl_krw"] is None


def test_missing_and_not_yet_known_costs_remain_null(tmp_path):
    data, costs, _, _, _ = setup(tmp_path, publish=False)
    missing = result(data, costs, prepare(data, costs))
    assert missing["status"] == "pending" and missing["research_cost_krw"] is None
    data, costs, _, _, _ = setup(tmp_path / "future")
    cutoff = DAY + "T20:00:00+09:00"
    future = result(data, costs, prepare(data, costs, cutoff), cutoff=cutoff)
    assert future["status"] == "pending" and future["research_net_pnl_krw"] is None


@pytest.mark.parametrize("fault", ["manual", "partial", "authority", "bad_fill", "source_quality"])
def test_censored_or_invalid_observations_never_get_economics(tmp_path, fault):
    def change(row):
        if fault == "manual": row["exit_signal"]["exit_decision_source"] = "MANUAL"
        elif fault == "partial": row["position_residual_qty"] = 1
        elif fault == "authority": row["terminal_population_scope"] = "counterfactual"
        elif fault == "bad_fill": row["buy_fill_legs"][0]["execution_no"] = "999999"
        else: row["strict_completion_reasons"] = ["source_gap_duplicate_sell_execution"]
    data, costs, _, _, _ = setup(tmp_path, mutate=change)
    value = result(data, costs, prepare(data, costs))
    assert value["status"] == ("censored" if fault in {"manual", "partial"} else "source_gap"), value
    assert value["research_cost_krw"] is value["research_net_pnl_krw"] is value["research_profit_rate"] is None


def test_producer_bytes_are_required_not_just_eligible_status(tmp_path):
    data, costs, _, sidecar, _ = setup(tmp_path)
    sidecar.write_text(sidecar.read_text() + "\n")
    prepared = prepare(data, costs)
    assert prepared.status == "source_gap" and "dependency_invalid" in prepared.reason
    assert result(data, costs, prepared)["research_net_pnl_krw"] is None


def test_raw_official_source_change_invalidates_allocated_receipt(tmp_path):
    data, costs, _, _, _ = setup(tmp_path)
    observed = official.load_source(costs, DAY)
    observed["observations"]["ka10170"]["pages"][0]["tdy_trde_diary"][0]["cmsn_alm_tax"] = "22"
    observed["source_sha256"] = exact.digest({k: v for k, v in observed.items() if k != "source_sha256"})
    official.atomic(official.source_path(costs, DAY), observed)
    value = result(data, costs, prepare(data, costs))
    assert value["status"] == "source_gap" and "official_allocation_binding_invalid" in value["reason"]
    assert value["research_net_pnl_krw"] is None


def test_broken_registry_hash_never_grants_custody(tmp_path):
    data, costs, _, _, _ = setup(tmp_path)
    path = data / "runtime/order_owner_registry.jsonl"
    path.write_text(path.read_text().replace("test_account", "fake_account"))
    prepared = prepare(data, costs)
    assert prepared.status == "source_gap" and "registry_hash_invalid" in prepared.reason


def test_prepared_batch_reuses_native_read_and_detects_changed_dependencies(tmp_path, monkeypatch):
    data, costs, _, sidecar, _ = setup(tmp_path)
    original, calls = stop._native_projection, []
    def counted(*args):
        calls.append(args)
        return original(*args)
    monkeypatch.setattr(stop, "_native_projection", counted)
    prepared = prepare(data, costs)
    for _ in range(20):
        value = result(data, costs, prepared)
        assert value["status"] == "eligible"
        value["quantity_basis"]["buy_qty"] = 999
    assert len(calls) == 1
    assert result(data, costs, prepared)["quantity_basis"]["buy_qty"] == 2
    sidecar.write_text(sidecar.read_text() + "\n")
    with pytest.raises(ValueError, match="prepared_source_changed"):
        prepared.validate_unchanged()


def test_caller_and_prepared_context_cannot_change_native_economics(tmp_path):
    data, costs, _, _, _ = setup(tmp_path)
    prepared = prepare(data, costs)
    value = stop.prepare_economic_record({"id": 1, "buy_price": 1}, data_root=data,
        source_date=DAY, cost_data_root=costs, prepared=prepared)
    assert value["reason"] == "caller_native_record_conflict" and value["research_net_pnl_krw"] is None
    with pytest.raises(ValueError, match="prepared_context_mismatch"):
        stop.prepare_economic_record({"id": 1}, data_root=data, source_date=DAY, prepared=prepared)


def test_legacy_exact_time_absence_uses_confirmed_fill_clock(tmp_path):
    def change(row): row["exact_sell_fill_time"] = None
    data, costs, _, _, _ = setup(tmp_path, mutate=change)
    value = result(data, costs, prepare(data, costs))
    assert value["status"] == "eligible", value["reason"]
    assert value["terminal_time_basis"] == "native_sell_fill_legs"
    assert value["terminal_observation"]["exact_sell_fill_time"] is None
    assert value["terminal_observation"]["terminal_fill_time"] == DAY + "T10:01:00+09:00"


@pytest.mark.parametrize("fault", ["unbound", "inferred", "sell_owner", "sell_account", "signal_hash"])
def test_main_buy_custody_alone_cannot_claim_main_exit(tmp_path, fault):
    def change(row):
        signal = row["exit_signal"]
        if fault == "unbound": signal["binding_status"] = "legacy_unbound"
        elif fault == "inferred": signal["inferred"] = True
        elif fault == "sell_owner": signal["submission"]["owner_id"] = "manual_operator:1"
        elif fault == "sell_account": signal["submission"]["account_key"] = "another_account"
        else: signal["fields"]["exit_signal_contract_sha256"] = "f" * 64
    data, costs, _, _, _ = setup(tmp_path, mutate=change)
    with prepare(data, costs) as prepared:
        value = result(data, costs, prepared)
        assert value["status"] == "censored"
        assert value["custody_status"] == "verified_registry_fill_census"
        assert value["research_net_pnl_krw"] is None


def test_retained_native_budget_lives_until_close_and_failure_releases(tmp_path):
    from src.engine.lifecycle.research_input_budget import health
    data, costs, _, _, _ = setup(tmp_path)
    baseline = health()["used_bytes"]
    prepared = prepare(data, costs)
    assert prepared.status == "verified", prepared.reason
    assert health()["used_bytes"] > baseline
    assert prepared.rows
    prepared.close()
    assert health()["used_bytes"] == baseline
    assert prepared.rows == {} and prepared.status == "closed"
    assert prepared.source_reference == {} and prepared.cost_generation == {}
    assert prepared.cost_generation_sha256 is None
    assert not prepared._paths and not prepared._signature and not prepared.rows.budget_claims
    with pytest.raises(ValueError, match="prepared_source_closed"):
        prepared.validate_unchanged()
    path = data / "runtime/order_owner_registry.jsonl"
    path.write_text(path.read_text().replace("test_account", "broken_account"))
    failed = prepare(data, costs)
    assert failed.status == "source_gap" and failed.rows == {}
    assert health()["used_bytes"] == baseline


def test_legacy_optional_sell_owner_fields_do_not_override_native_main_chain(tmp_path):
    def change(row):
        row["exit_signal"]["submission"].update(owner_id=None, account_key=None)
    data, costs, _, _, _ = setup(tmp_path, mutate=change)
    with prepare(data, costs) as prepared:
        value = result(data, costs, prepared)
        assert value["status"] == "eligible", value["reason"]
        assert value["main_exit_source"]["explicit_submission_owner_observed"] is False
        assert value["main_exit_source"]["seller_attribution_basis"] == "native_main_decision_same_order_generation"
        assert value["terminal_observation"]["main_automatic_management_allowed"] is False
def test_compact_budget_partition_is_explicit_and_no_display_300_limit(tmp_path, monkeypatch):
    assert stop.MAX_RECORDS == allocation.MAX_RECORDS > 300
    data, costs, _, _, _ = setup(tmp_path)
    monkeypatch.setattr(stop, "MAX_COMPACT_RESIDENT_BYTES", 1)
    prepared = prepare(data, costs)
    assert prepared.status == "source_gap"
    assert prepared.reason == "stop_research_compact_census_partition_required"
    assert prepared.rows == {}


def test_native_whole_position_actual_cost_is_not_claimed_as_per_fill(tmp_path):
    data, costs = tmp_path / "native", tmp_path / "costs"
    item = position(1)
    item["custody_rows"][0]["record_id"] = "1"
    observed = source(costs, buy_qty=2, sell_qty=2, buy_amount=20000, sell_amount=20200, cost=10)
    official.atomic(official.source_path(costs, DAY), observed)
    actual = official.reconcile_position(observed, target_date=DAY, record_id=1, stock_code=item["symbol"],
        buy_legs=item["buy_legs"], sell_legs=item["sell_legs"], custody_rows=item["custody_rows"], peer_records=[1])
    assert actual["status"] == "actual_cost_reconciled"
    def change(row): row["actual_cost_reconciliation"] = actual
    native(data, [item], mutate=change)
    registry(data, [item])
    with prepare(data, costs) as prepared:
        value = result(data, costs, prepared)
        assert value["status"] == "eligible", value["reason"]
        assert value["evidence_grade"] == "exact_position_total" and value["research_net_pnl_krw"] == 190
        assert value["actual_execution_cost"] is False and value["actual_position_cost"] is True


def test_microsecond_decision_and_second_precision_submit_use_native_clock_bound(tmp_path):
    def change(row):
        fields = row["exit_signal"]["fields"]
        fields["exit_signal_contract"]["signal_at"] = DAY + "T10:00:59.123456+09:00"
        fields["exit_signal_contract_sha256"] = exact.digest(fields["exit_signal_contract"])
    data, costs, _, _, _ = setup(tmp_path, mutate=change)
    with prepare(data, costs) as prepared:
        assert result(data, costs, prepared)["status"] == "eligible"


def test_later_official_whole_position_cost_needs_no_old_economics_or_allocation_index(tmp_path):
    data, costs = tmp_path / "native", tmp_path / "costs"
    item = position(1)
    item["custody_rows"][0]["record_id"] = "1"
    rows, sidecar = native(data, [item])
    original = sidecar.read_bytes()
    registry(data, [item])
    assert rows[0].get("actual_cost_reconciliation") is None
    with prepare(data, costs) as prepared:
        assert result(data, costs, prepared)["status"] == "pending"
    observed = source(costs, buy_qty=2, sell_qty=2, buy_amount=20000, sell_amount=20200, cost=10)
    official.atomic(official.source_path(costs, DAY), observed)
    with prepare(data, costs) as prepared:
        value = result(data, costs, prepared)
        assert value["status"] == "eligible", value["reason"]
        assert value["evidence_grade"] == "exact_position_total"
        assert value["cost_overlay_basis"] == "later_official_whole_position_reconciled"
        assert value["research_cost_krw"] == 10 and value["research_net_pnl_krw"] == 190
        assert value["actual_execution_cost"] is False
    assert sidecar.read_bytes() == original
    assert not (costs / "runtime/initial_quantity_research_costs").exists()


def test_refreshed_whole_position_cost_pins_new_generation_and_keeps_prior_receipt(tmp_path):
    data, costs = tmp_path / "native", tmp_path / "costs"
    item = position(1)
    item["custody_rows"][0]["record_id"] = "1"
    observed = source(costs, buy_qty=2, sell_qty=2, buy_amount=20000, sell_amount=20200, cost=10)
    official.atomic(official.source_path(costs, DAY), observed)
    old = official.reconcile_position(observed, target_date=DAY, record_id=1, stock_code=item["symbol"],
        buy_legs=item["buy_legs"], sell_legs=item["sell_legs"], custody_rows=item["custody_rows"], peer_records=[1])
    def change(row): row["actual_cost_reconciliation"] = old
    _, sidecar = native(data, [item], mutate=change)
    original = sidecar.read_bytes()
    registry(data, [item])
    refreshed = deepcopy(observed)
    refreshed["observed_at"] = DAY + "T21:01:00+09:00"
    for observation in refreshed["observations"].values():
        observation["observed_at"] = refreshed["observed_at"]
    refreshed["source_sha256"] = exact.digest({k: v for k, v in refreshed.items() if k != "source_sha256"})
    official.atomic(official.source_path(costs, DAY), refreshed)
    with prepare(data, costs) as prepared:
        value = result(data, costs, prepared)
        assert value["status"] == "eligible", value["reason"]
        assert value["evidence_grade"] == "exact_position_total"
        assert value["cost_overlay_basis"] == "later_official_whole_position_reconciled"
        assert value["raw_source_sha256"] == refreshed["source_sha256"]
        assert value["prior_native_actual_source_sha256"] == observed["source_sha256"]
        assert value["prior_native_actual_receipt_sha256"] == old["receipt_sha256"]
        assert value["research_net_pnl_krw"] == 190
    assert sidecar.read_bytes() == original


def test_cost_and_registry_decodes_are_admitted_to_shared_budget_before_read(tmp_path, monkeypatch):
    from src.engine.lifecycle import research_input_budget as budget
    data, costs, _, _, _ = setup(tmp_path)
    baseline = budget.health()["used_bytes"]
    calls = []
    registry_read = stop._registry
    def checked_registry(root):
        calls.append(budget.health()["used_bytes"])
        return registry_read(root)
    monkeypatch.setattr(stop, "_registry", checked_registry)
    with prepare(data, costs) as prepared:
        assert prepared.status == "verified", prepared.reason
        retained = budget.health()["used_bytes"]
        assert calls and calls[0] > retained > baseline
    assert budget.health()["used_bytes"] == baseline
    # The native rows fit; adding the current cost + registry decoders does not.
    native_rows, _, _ = stop._native_projection(data, DAY)
    native_size = budget.health()["used_bytes"] - baseline
    for claim in native_rows.budget_claims: claim.close()
    monkeypatch.setattr(budget, "LIMIT_BYTES", baseline + native_size + 100)
    with pytest.raises(ValueError, match="shared_research_budget_partition_resume_required"):
        prepare(data, costs)
    assert budget.health()["used_bytes"] == baseline


def test_owned_one_record_context_closes_explicitly_even_with_retained_traceback(tmp_path):
    from src.engine.lifecycle.research_input_budget import health
    data, costs, _, _, _ = setup(tmp_path)
    baseline = health()["used_bytes"]
    value = stop.prepare_economic_record({"id": 1}, data_root=data, source_date=DAY, cost_data_root=costs)
    assert value["status"] == "eligible"
    assert health()["used_bytes"] == baseline
    retained_error = None
    try:
        stop.prepare_economic_record({"id": False}, data_root=data, source_date=DAY, cost_data_root=costs)
    except ValueError as exc:
        retained_error = exc
    assert retained_error is not None and retained_error.__traceback__ is not None
    assert health()["used_bytes"] == baseline


def test_native_projection_failure_closes_claims_before_traceback_is_released(tmp_path):
    from src.engine.lifecycle.research_input_budget import health
    data, costs, _, sidecar, _ = setup(tmp_path)
    # Keep the producer byte receipt valid while breaking a semantic census binding.
    value = json.loads(sidecar.read_text())
    value["snapshot_identity"]["inode"] += 1
    value["artifact_sha256"] = stop._canonical({k:v for k,v in value.items() if k != "artifact_sha256"})
    sidecar.write_text(json.dumps(value))
    seal_dependency_receipt(sidecar, value)
    baseline, retained_error = health()["used_bytes"], None
    try:
        stop._native_projection(data, DAY)
    except ValueError as exc:
        retained_error = exc
    assert retained_error is not None and retained_error.__traceback__ is not None
    assert health()["used_bytes"] == baseline


def test_native_metadata_admitted_before_decode_and_released_after_batch(tmp_path, monkeypatch):
    from src.engine.lifecycle.research_input_budget import health
    data, costs, _, sidecar, _ = setup(tmp_path)
    original_read = stop._read
    baseline, observed = health()["used_bytes"], []
    def checked_read(path, maximum):
        if str(path).endswith(".dependencies.json") or path == sidecar:
            assert health()["used_bytes"] - baseline >= path.stat().st_size * 12
            observed.append(path)
        return original_read(path, maximum)
    monkeypatch.setattr(stop, "_read", checked_read)
    with prepare(data, costs) as prepared:
        assert prepared.status == "verified", prepared.reason
    assert observed and health()["used_bytes"] == baseline
    sidecar.with_name(sidecar.name + ".dependencies.json").unlink()
    with prepare(data, costs) as prepared:
        assert prepared.status == "verified", prepared.reason
    assert sidecar in observed and health()["used_bytes"] == baseline
