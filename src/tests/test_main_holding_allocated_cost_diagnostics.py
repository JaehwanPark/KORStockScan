"""Native allocation producer to a separately saved holding diagnostic."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.automation import main_holding_allocated_cost_diagnostics as D
from src.engine.lifecycle import broker_cost_allocation as A
from src.engine.lifecycle import broker_cost_source as C
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.broker_cost_reconciliation import source_generation, digest
from src.engine.lifecycle.research_input_budget import health
from src.tests.test_broker_cost_allocation import position, source
from src.tests.test_broker_cost_source import DAY, NOW


def write(path, body, *, seal=False):
    value = deepcopy(body)
    if seal:
        value.pop("artifact_sha256", None)
        value["artifact_sha256"] = digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    return value


def ref(path):
    raw = path.read_bytes()
    return dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def fixture(tmp_path):
    cost_root, input_root = tmp_path / "cost", tmp_path / "input"
    observed = source(
        cost_root, buy_qty=8, sell_qty=6, buy_amount=80000, sell_amount=60600, cost=101
    )
    C.atomic(C.source_path(cost_root, DAY), observed)
    positions = [position(1), position(2), position(3, completed=False), position(4)]
    positions[3]["buy_legs"][0]["execution_no"] = ""
    receipts = A.build_research_cost_allocations({DAY: observed}, positions)
    completed = {
        p["record_id"]: receipts[p["record_id"]]
        for p in positions
        if p["status"] == "COMPLETED"
    }
    A.persist_research_costs(cost_root, DAY, completed, [DAY])
    carrier = tmp_path / "completed_projection.json"
    write(carrier, dict(positions=positions))
    carrier_ref = {**ref(carrier), "path": carrier.name}
    normalized = []
    for p in positions + [position(5)]:
        if p["status"] != "COMPLETED":
            continue
        normalized.append(
            dict(
                position_key=p["record_id"],
                symbol=p["symbol"],
                evidence_kind="actual_completed",
                automatic_management_allowed=False,
                operating_ai_required=True,
                source_gap="original_custody_gap",
                qty=2,
                buy_basis_krw=20000,
                entry_at=datetime.fromisoformat(p["buy_legs"][0]["at"])
                .replace(tzinfo=C.KST)
                .timestamp(),
                completion_at=datetime.fromisoformat(p["completed_at"]).timestamp(),
                terminal_status="COMPLETED",
                actual_cost_reconciliation={
                    "status": "actual_cost_unallocated",
                    "exact_pnl_krw": None,
                },
                source_reference=dict(
                    id=p["record_id"],
                    path=str(carrier),
                    projection_generation=carrier_ref,
                ),
            )
        )
    normalized.append(
        dict(
            position_key="cf:6",
            evidence_kind="enter_pass_opportunity_cf",
            symbol="005930",
            automatic_management_allowed=False,
        )
    )
    partition_path = input_root / "partition.json"
    partition = write(partition_path, dict(positions=normalized), seal=True)
    partitions = storage.write_tree(
        input_root, [dict(path=partition_path.name, artifact_sha256=digest(partition))]
    )
    ids = storage.write_tree(input_root, [p["position_key"] for p in normalized])
    manifest_path = input_root / "manifest.json"
    write(
        manifest_path,
        dict(
            schema="main_all_scope_exit_input_manifest_v2",
            source_date=DAY,
            target_date=DAY,
            as_of=NOW.timestamp() + 3600,
            runtime_effect=False,
            allowed_runtime_apply=False,
            partitions_ref=partitions,
            population_ids_ref=ids,
        ),
        seal=True,
    )
    acceptance_path = tmp_path / "acceptance.json"
    write(
        acceptance_path,
        dict(
            positions=positions,
            receipts=receipts,
            consumer_receipts=completed,
            temp_generation=source_generation(cost_root, DAY),
            sidecar_extraction=dict(
                source_path=str(carrier),
                source_byte_sha256=ref(carrier)["sha256"],
                source_size=carrier.stat().st_size,
            ),
        ),
    )
    registration_path = tmp_path / "registration.json"
    output = tmp_path / "output"
    write(
        registration_path,
        dict(
            schema=D.REGISTRATION_SCHEMA,
            registered_at=NOW.timestamp() + 7200,
            allowed_runtime_apply=False,
            runtime_effect=False,
            diagnostics=dict(
                allocated_cost=dict(
                    source_acceptance=ref(acceptance_path),
                    input_manifest=ref(manifest_path),
                    cost_root=str(cost_root),
                    output_root=str(output),
                    knowledge_cutoff=NOW.timestamp() + 3600,
                    allowed_source_scope=A.SCOPE,
                    automatic_management_change=False,
                    canonical_actual_economics_change=False,
                    strategy_replay_common_population_change=False,
                )
            ),
        ),
        seal=True,
    )
    return dict(
        registration=registration_path,
        input_manifest=manifest_path,
        input_root=input_root,
        source_acceptance=acceptance_path,
        cost_root=cost_root,
        output_root=output,
    )


def update_registration(args, change=None):
    p = args["registration"]
    r = json.loads(p.read_bytes())
    spec = r["diagnostics"]["allocated_cost"]
    spec["source_acceptance"] = ref(args["source_acceptance"])
    spec["input_manifest"] = ref(args["input_manifest"])
    if change:
        change(r, spec)
    write(p, r, seal=True)


def test_native_producer_to_saved_diagnostic_preserves_all_denominators(tmp_path):
    args = fixture(tmp_path)
    before = {
        p: p.read_bytes()
        for root in (args["input_root"], args["cost_root"])
        for p in root.rglob("*")
        if p.is_file()
    }
    result = D.run(**args)
    saved = json.loads((args["output_root"] / D.OUTPUT_NAME).read_bytes())
    assert saved == result and result["artifact_sha256"] == digest(
        {k: v for k, v in result.items() if k != "artifact_sha256"}
    )
    assert result["source_date"] == result["target_date"] == DAY
    assert result["as_of"] == NOW.timestamp() + 3600
    assert result["metric_contract"] == {
        "metric_role": "funnel_count",
        "decision_authority": "report_only",
        "window_policy": "registered_source_window_and_cost_knowledge_cutoff",
        "sample_floor": "diagnostic_no_promotion",
        "primary_decision_metric": "none",
        "source_quality_gate": "native_quantity_allocation_scope_receipt_and_source_hash_exact_binding",
        "forbidden_uses": [
            "canonical_actual_pnl",
            "actual_execution_cost",
            "strategy_selection",
            "alternative_exit_cost",
            "runtime_apply",
            "custody_override",
            "AI_input_or_response_change",
        ],
    }
    assert result["population_counts"] == {
        "actual_completed": 4,
        "enter_pass_opportunity_cf": 1,
    }
    assert result["allocated_terminal_reference_count"] == 2
    rows = {r["record_id"]: r for r in result["actual_completed_rows"]}
    assert set(rows) == {"1", "2", "4", "5"}
    assert rows["4"]["allocation_status"] == "research_cost_invalid"
    assert rows["5"]["allocation_status"] == "source_unavailable"
    assert result["open_source_rows"][0]["record_id"] == "3"
    assert result["open_source_rows"][0]["status"] == "research_cost_pending"
    assert result["open_source_rows"][0]["allocated_observed_exit_net_pnl_krw"] is None
    for row in rows.values():
        assert row["automatic_management_allowed"] is False
        assert row["operating_ai_required"] is True
        assert row["original_source_gap"] == "original_custody_gap"
        assert row["paired_strategy_economic_eligible"] is False
        assert row["actual_profit_verified"] is False
    for row in (rows["1"], rows["2"]):
        assert row["source_economics_scope"] == A.SCOPE
        assert row["source_actual_execution_cost"] is False
        assert (
            row["buy_fill_identity"]
            and row["sell_fill_identity"]
            and row["custody_sha256"]
        )
    fees = result["terminal_reference_totals"]["allocated_observed_exit_fees_taxes_krw"]
    assert (
        result["terminal_reference_totals"]["allocated_observed_exit_net_pnl_krw"]
        == 400 - fees
    )
    totals = result["participating_cohort_totals"]
    assert totals["confirmed_total_cost_krw"] == 101
    assert (
        totals["known_allocated_cost_krw"] + totals["outside_allocated_cost_krw"] == 101
    )
    assert 0 < fees < totals["known_allocated_cost_krw"] < 101
    assert (
        result["economic_eligible_count"] == 0
        and result["canonical_realized_pnl_modified"] is False
    )
    assert result["budget"]["conservative_claim_bytes"] <= 64 * 1024 * 1024
    assert health()["used_bytes"] == 0
    assert all(p.read_bytes() == raw for p, raw in before.items())
    with pytest.raises(ValueError, match="already_exists"):
        D.run(**args)


@pytest.mark.parametrize("delta,expected", [(-0.001, 0), (0, 2), (0.001, 2)])
def test_cost_knowledge_cutoff_is_inclusive_and_does_not_zero_missing(
    tmp_path, delta, expected
):
    args = fixture(tmp_path)
    update_registration(
        args, lambda r, s: s.update(knowledge_cutoff=NOW.timestamp() + delta)
    )
    result = D.build(**args)
    assert result["allocated_terminal_reference_count"] == expected
    if not expected:
        assert (
            result["terminal_reference_totals"]["allocated_observed_exit_net_pnl_krw"]
            is None
        )
        assert all(
            r["allocated_observed_exit_net_pnl_krw"] is None
            for r in result["actual_completed_rows"]
        )
        assert (
            result["actual_completed_rows"][0]["reason"]
            == "research_cost_after_knowledge_cutoff"
        )


@pytest.mark.parametrize(
    "mutation",
    ["account", "id", "qty", "negative", "duplicate", "scope", "receipt", "clock"],
)
def test_registered_but_inconsistent_original_evidence_is_rejected(tmp_path, mutation):
    args = fixture(tmp_path)
    p = args["source_acceptance"]
    d = json.loads(p.read_bytes())
    row = d["positions"][0]
    if mutation == "account":
        row["custody_rows"][0]["account_key"] = "another"
    if mutation == "id":
        row["record_id"] = "999"
    if mutation == "qty":
        row["buy_legs"][0]["qty"] = 1
    if mutation == "negative":
        row["buy_legs"][0]["price"] = -1
    if mutation == "duplicate":
        row["sell_legs"].append(deepcopy(row["sell_legs"][0]))
    if mutation == "scope":
        d["receipts"]["1"]["economics_scope"] = "holding_actual_cost"
    if mutation == "receipt":
        d["receipts"]["1"]["allocated_net_pnl_krw"] += 1
    if mutation == "clock":
        d["receipts"]["1"]["cost_available_at"] = DAY + "T21:00:00"
    write(p, d)
    update_registration(args)
    with pytest.raises(ValueError):
        D.build(**args)
    assert health()["used_bytes"] == 0


def test_nan_json_and_unregistered_changed_source_fail_closed(tmp_path):
    args = fixture(tmp_path)
    args["source_acceptance"].write_text(
        args["source_acceptance"].read_text().replace("10000", "NaN", 1)
    )
    with pytest.raises(ValueError, match="physical_reference"):
        D.build(**args)
    update_registration(args)
    with pytest.raises(ValueError, match="nonfinite"):
        D.build(**args)


@pytest.mark.parametrize("clock", [True, 0, -1, "2026-10-08T21:00:00"])
def test_cutoff_has_no_boolean_nonpositive_or_naive_fallback(tmp_path, clock):
    args = fixture(tmp_path)
    update_registration(args, lambda r, s: s.update(knowledge_cutoff=clock))
    with pytest.raises(ValueError, match="clock"):
        D.build(**args)


def test_exact_normalized_record_binding_failure_stays_in_denominator(tmp_path):
    args = fixture(tmp_path)
    path = args["input_root"] / "partition.json"
    part = json.loads(path.read_bytes())
    part["positions"][0]["completion_at"] += 1
    part = write(path, part, seal=True)
    m = json.loads(args["input_manifest"].read_bytes())
    m["partitions_ref"] = storage.write_tree(
        args["input_root"], [dict(path=path.name, artifact_sha256=digest(part))]
    )
    write(args["input_manifest"], m, seal=True)
    update_registration(args)
    result = D.build(**args)
    assert result["allocated_terminal_reference_count"] == 1
    assert len(result["actual_completed_rows"]) == 4
    assert (
        result["actual_completed_rows"][0]["reason"]
        == "original_position_binding_mismatch"
    )


def test_source_change_after_native_validation_prevents_publication(
    tmp_path, monkeypatch
):
    args = fixture(tmp_path)
    original = D._source_population

    def change(*a, **kw):
        result = original(*a, **kw)
        args["source_acceptance"].write_bytes(
            args["source_acceptance"].read_bytes() + b" "
        )
        return result

    monkeypatch.setattr(D, "_source_population", change)
    with pytest.raises(ValueError, match="source_changed"):
        D.run(**args)
    assert not args["output_root"].exists()


def test_resource_admission_and_cli_required_inputs(tmp_path, monkeypatch):
    args = fixture(tmp_path)
    monkeypatch.setattr(D, "MAX_NATIVE_BYTES", 1)
    with pytest.raises(ValueError, match="native_generation_budget"):
        D.build(**args)
    assert health()["used_bytes"] == 0
    with pytest.raises(SystemExit):
        D.main([])


def test_public_cli_saved_report_never_calls_collection(tmp_path, monkeypatch, capsys):
    args = fixture(tmp_path)

    def forbidden(*a, **kw):
        raise AssertionError("a report consumer must not collect sources")

    monkeypatch.setattr(C, "collect", forbidden)
    D.main(
        [
            part
            for key, value in args.items()
            for part in ("--" + key.replace("_", "-"), str(value))
        ]
    )
    assert json.loads(capsys.readouterr().out)["economic_eligible_count"] == 0
    assert (args["output_root"] / D.OUTPUT_NAME).exists()


def test_post_build_source_cas_and_output_source_overlap(tmp_path, monkeypatch):
    args = fixture(tmp_path)
    build = D.build

    def changed(**kwargs):
        report = build(**kwargs)
        args["source_acceptance"].write_bytes(
            args["source_acceptance"].read_bytes() + b" "
        )
        return report

    monkeypatch.setattr(D, "build", changed)
    with pytest.raises(ValueError, match="before_publication"):
        D.run(**args)
    assert not args["output_root"].exists()
    monkeypatch.setattr(D, "build", build)
    with pytest.raises(ValueError, match="output_source_overlap"):
        D.build(**{**args, "output_root": args["cost_root"] / "diagnostic"})


@pytest.mark.parametrize(
    "field",
    [
        "automatic_management_change",
        "canonical_actual_economics_change",
        "strategy_replay_common_population_change",
    ],
)
def test_registration_cannot_expand_economics_or_custody_authority(tmp_path, field):
    args = fixture(tmp_path)
    update_registration(args, lambda r, s: s.update({field: True}))
    with pytest.raises(ValueError, match="registration_binding"):
        D.run(**args)
    assert not args["output_root"].exists()


def clock_bridge_fixture(tmp_path, delay=1):
    """Native receipt audit and cost producer against an older observation clock."""
    from datetime import timedelta
    from src.engine import sniper_trade_review_report as review
    from src.engine.scalping.universal_trailing_replay import completed_sources

    args = fixture(tmp_path)
    data = json.loads(args["source_acceptance"].read_bytes())
    original = data["positions"][0]
    leg = original["sell_legs"][0]
    occurred = datetime.fromisoformat(original["completed_at"])
    received = occurred + timedelta(microseconds=500000)
    first = occurred + timedelta(seconds=delay)
    fields = dict(
        id="1",
        order_no=leg["order_no"],
        execution_no=leg["execution_no"],
        holding_path_buy_fill_identity="a" * 64,
        broker_execution_provenance_complete=True,
        broker_execution_time_source="official_fid_908",
        broker_execution_time_raw=occurred.strftime("%H%M%S"),
        broker_execution_observed_at=occurred.isoformat(),
        broker_execution_received_at=received.isoformat(),
        decision_authority="broker_sell_fill_observation_only",
        pipeline_lifecycle_population_scope="real_record_bound",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        main_lifecycle_exit_qty=leg["qty"],
        main_lifecycle_sell_price=leg["price"],
        broker_route=leg["route"],
    )
    wrapper = dict(
        native_receipt_identity_schema="broker_position_sell_receipt_v1",
        native_receipt_position_key="record:1",
        native_receipt_record_id=1,
        native_receipt_stock_code=original["symbol"],
        native_receipt_order_no=leg["order_no"],
        native_receipt_execution_no=leg["execution_no"],
        native_receipt_buy_fill_identity="a" * 64,
        native_receipt_observed_at=received.isoformat(),
    )
    events = [
        review.HoldingEvent(
            first.replace(tzinfo=None).isoformat(sep=" "),
            "test",
            original["symbol"],
            "sell_completed",
            fields,
            "original",
        ),
        review.HoldingEvent(
            (first + timedelta(seconds=60)).replace(tzinfo=None).isoformat(sep=" "),
            "test",
            original["symbol"],
            "sell_completed",
            {**fields, **wrapper},
            "reobservation",
        ),
    ]
    collapsed, audits = review._quantity_sell_receipt_observations(events)
    assert len(collapsed) == 1 and len(audits) == 1
    assert collapsed[0].timestamp == occurred.replace(tzinfo=None).isoformat(sep=" ")
    data["summary"] = [
        dict(
            record_id="1",
            symbol=original["symbol"],
            status="COMPLETED",
            terminal_observed=True,
            completed_at=original["completed_at"],
            allocation_status="research_cost_allocated",
            receipt_reobservations=audits,
        )
    ]
    data["code_sha256"] = {
        str(D.NATIVE_AUDIT_PRODUCER): hashlib.sha256(
            D.NATIVE_AUDIT_PRODUCER.read_bytes()
        ).hexdigest()
    }
    legacy = dict(
        id=1,
        status="COMPLETED",
        buy_fill_legs=original["buy_legs"],
        sell_fill_legs=[{**leg, "at": first.replace(tzinfo=None).isoformat(sep=" ")}],
    )
    normalized, _ = completed_sources([legacy])
    carrier = Path(data["sidecar_extraction"]["source_path"])
    write(
        carrier,
        dict(
            legacy_completed_trade=legacy,
            native_observations=[asdict(event) for event in events],
        ),
    )
    carrier_ref = {**ref(carrier), "path": carrier.name}
    data["sidecar_extraction"].update(
        source_byte_sha256=ref(carrier)["sha256"], source_size=carrier.stat().st_size
    )
    write(args["source_acceptance"], data)
    partition_path = args["input_root"] / "partition.json"
    part = json.loads(partition_path.read_bytes())
    for row in part["positions"]:
        if row["evidence_kind"] == "actual_completed":
            row["source_reference"]["projection_generation"] = carrier_ref
        if row["position_key"] == "1":
            row["completion_at"] = normalized[0]["completion_at"]
    part = write(partition_path, part, seal=True)
    manifest = json.loads(args["input_manifest"].read_bytes())
    manifest["partitions_ref"] = storage.write_tree(
        args["input_root"],
        [dict(path=partition_path.name, artifact_sha256=digest(part))],
    )
    write(args["input_manifest"], manifest, seal=True)
    update_registration(args)
    return args


@pytest.mark.parametrize("delay", [1, 7])
def test_native_clock_bridge_preserves_exact_occurrence_receipt_and_observation(
    tmp_path, delay
):
    args = clock_bridge_fixture(tmp_path, delay)
    result = D.run(**args)
    row = result["actual_completed_rows"][0]
    assert result["allocated_terminal_reference_count"] == 2
    bridge = row["terminal_clock_binding"]
    assert bridge["mode"] == "registered_native_reobservation_audit"
    assert (
        bridge["timestamp_tolerance_seconds"] == 0
        and bridge["raw_source_events_reverified_here"] is False
    )
    assert row["original_completion_at"] - D._clock(row["completed_at"]) == delay
    audit = bridge["receipt_reobservations"][0]
    assert D._clock(audit["original_occurred_at"]) == D._clock(row["completed_at"])
    assert D._leg_clock(audit["first_observed_at"]) == row["original_completion_at"]
    assert (
        row["automatic_management_allowed"] is False
        and result["economic_eligible_count"] == 0
    )
    assert (
        result["actual_completed_rows"][2]["allocation_status"]
        == "research_cost_invalid"
    )


@pytest.mark.parametrize(
    "fault",
    [
        "record",
        "order",
        "execution",
        "native_hash",
        "event_hash",
        "received_before",
        "received_after_first",
        "first_clock",
        "occurred_clock",
        "future_last",
        "count",
        "duplicate",
        "producer",
        "missing",
    ],
)
def test_native_clock_bridge_never_uses_tolerance_or_unbound_audit(tmp_path, fault):
    args = clock_bridge_fixture(tmp_path)
    data = json.loads(args["source_acceptance"].read_bytes())
    audit = data["summary"][0]["receipt_reobservations"][0]
    if fault == "record":
        audit["record_id"] = "2"
    if fault == "order":
        audit["order_no"] = "99"
    if fault == "execution":
        audit["execution_no"] = "99"
    if fault == "native_hash":
        audit["native_identity_sha256"] = ""
    if fault == "event_hash":
        audit["source_event_digests_sha256"] = ""
    if fault == "received_before":
        audit["original_received_at"] = DAY + "T09:00:00+09:00"
    if fault == "received_after_first":
        audit["original_received_at"] = DAY + "T10:01:02+09:00"
    if fault == "first_clock":
        audit["first_observed_at"] = DAY + " 10:01:02"
    if fault == "occurred_clock":
        audit["original_occurred_at"] = DAY + "T10:00:59+09:00"
    if fault == "future_last":
        audit["last_observed_at"] = DAY + " 23:00:00"
    if fault == "count":
        audit["reobserved_count"] = 2
    if fault == "duplicate":
        data["summary"][0]["receipt_reobservations"].append(deepcopy(audit))
    if fault == "producer":
        data["code_sha256"][str(D.NATIVE_AUDIT_PRODUCER)] = "a" * 64
    if fault == "missing":
        data["summary"] = []
    write(args["source_acceptance"], data)
    update_registration(args)
    result = D.build(**args)
    assert len(result["actual_completed_rows"]) == 4
    assert result["allocated_terminal_reference_count"] == 1
    assert (
        result["actual_completed_rows"][0]["reason"]
        == "original_position_binding_mismatch"
    )


def test_native_clock_bridge_does_not_bypass_cost_knowledge_cutoff(tmp_path):
    args = clock_bridge_fixture(tmp_path)
    update_registration(
        args, lambda r, s: s.update(knowledge_cutoff=NOW.timestamp() - 0.001)
    )
    result = D.build(**args)
    assert result["allocated_terminal_reference_count"] == 0
    assert (
        result["actual_completed_rows"][0]["reason"]
        == "research_cost_after_knowledge_cutoff"
    )
