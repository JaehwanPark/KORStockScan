"""Confirmed broker total allocation, custody, revisions and research isolation."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import json

import pytest

from src.engine.lifecycle import broker_cost_allocation as A
from src.engine.lifecycle import broker_cost_source as C
from src.engine.lifecycle.broker_cost_reconciliation import digest, source_generation
from src.tests.test_broker_cost_source import broker_fixture, DAY, NOW


def position(record, *, qty=2, price=10000, completed=True, buy_day=DAY):
    def leg(side, day, value):
        return {
            "at": day + (" 10:00:00" if side == "BUY" else " 10:01:00"),
            "order_no": str(record * 10 + (1 if side == "BUY" else 2)),
            "execution_no": str(record * 100 + (1 if side == "BUY" else 2)),
            "qty": qty,
            "price": value,
            "route": "SOR",
        }

    return {
        "record_id": str(record),
        "symbol": "005930",
        "status": "COMPLETED" if completed else "HOLDING",
        "terminal_observed": completed,
        "completion_observed_date": DAY,
        "completed_at": DAY + "T10:01:00+09:00",
        "buy_legs": [leg("BUY", buy_day, price)],
        "sell_legs": [leg("SELL", DAY, price + 100)] if completed else [],
        "custody_rows": [
            {
                "record_id": record,
                "owner_type": "main_scalping",
                "owner_id": "main_scalping:" + str(record),
                "account_key": "test_account",
                "filled_qty": qty,
                "state": "full" if completed else "cancel_pending",
                "source_quality_reasons": [],
            }
        ],
    }


def source(
    tmp_path, *, buy_qty=4, sell_qty=4, buy_amount=40000, sell_amount=40400, cost=21
):
    value, _, _, _ = broker_fixture(tmp_path)
    row = value["observations"]["ka10170"]["pages"][0]["tdy_trde_diary"][0]
    row.update(
        buy_qty=str(buy_qty),
        sell_qty=str(sell_qty),
        buy_amt=str(buy_amount),
        sell_amt=str(sell_amount),
        cmsn_alm_tax=str(cost),
    )
    value["source_sha256"] = digest(
        {k: v for k, v in value.items() if k != "source_sha256"}
    )
    return value


def allocated(tmp_path):
    observed = source(tmp_path)
    positions = [position(1), position(2)]
    return (
        observed,
        positions,
        A.build_research_cost_allocations({DAY: observed}, positions),
    )


def test_multirecord_total_is_conserved_without_claiming_exact_execution_cost(tmp_path):
    observed, positions, receipts = allocated(tmp_path)
    assert [receipts[str(i)]["allocated_fees_taxes_krw"] for i in (1, 2)] == [11, 10]
    assert sum(r["allocated_fees_taxes_krw"] for r in receipts.values()) == 21
    for item in positions:
        receipt = receipts[item["record_id"]]
        assert receipt["actual_execution_cost"] is False
        assert receipt["economics_scope"] == "initial_quantity_research_only"
        assert "exact_pnl_krw" not in receipt and "actual_fees_taxes_krw" not in receipt
        assert (
            A.validate_research_cost(
                receipt,
                record_id=item["record_id"],
                symbol=item["symbol"],
                buy_legs=item["buy_legs"],
                sell_legs=item["sell_legs"],
                custody_rows=item["custody_rows"],
                completion_date=DAY,
            )
            == receipt
        )
    assert (
        A.build_research_cost_allocations({DAY: observed}, list(reversed(positions)))
        == receipts
    )


def test_outside_manual_or_missing_activity_keeps_its_cost_share(tmp_path):
    observed = source(tmp_path)
    result = A.build_research_cost_allocations({DAY: observed}, [position(1)])["1"]
    assert result["allocated_fees_taxes_krw"] == 11
    group = result["sources"][0]
    assert group["outside_turnover_krw"] == 40200
    assert group["outside_allocated_cost_krw"] == 10
    assert group["known_allocated_cost_krw"] + group["outside_allocated_cost_krw"] == 21


def test_confirmed_open_fills_participate_without_fabricated_terminal(tmp_path):
    observed = source(tmp_path, sell_qty=2, sell_amount=20200, cost=30)
    values = A.build_research_cost_allocations(
        {DAY: observed}, [position(1), position(2, completed=False)]
    )
    assert values["1"]["allocated_fees_taxes_krw"] == 20
    assert values["1"]["sources"][0]["known_record_count"] == 2
    assert values["1"]["sources"][0]["outside_turnover_krw"] == 0
    assert values["2"]["status"] == "research_cost_pending"
    assert values["2"]["allocated_net_pnl_krw"] is None


def shift_source(value, day):
    result = deepcopy(value)
    result["source_date"] = day
    result["observed_at"] = day + "T21:00:00+09:00"
    for name, obs in result["observations"].items():
        obs["observed_at"] = result["observed_at"]
        if name == "ka10170":
            obs["request"]["base_dt"] = day.replace("-", "")
        if name.startswith("kt00015"):
            obs["request"]["strt_dt"] = obs["request"]["end_dt"] = day.replace("-", "")
    result["source_sha256"] = digest(
        {k: v for k, v in result.items() if k != "source_sha256"}
    )
    return result


def test_overnight_uses_entry_and_completion_dates_not_one_day_total(tmp_path):
    old = "2026-10-07"
    buy = shift_source(
        source(
            tmp_path / "b",
            buy_qty=2,
            sell_qty=0,
            buy_amount=20000,
            sell_amount=0,
            cost=4,
        ),
        old,
    )
    sell = source(
        tmp_path / "s", buy_qty=0, sell_qty=2, buy_amount=0, sell_amount=20200, cost=6
    )
    values = A.build_research_cost_allocations(
        {old: buy, DAY: sell}, [position(1, buy_day=old)]
    )
    assert values["1"]["status"] == "research_cost_allocated"
    assert values["1"]["allocated_fees_taxes_krw"] == 10
    assert values["1"]["allocated_net_pnl_krw"] == 190
    assert {p["source_date"] for p in values["1"]["sources"]} == {old, DAY}
    missing = A.build_research_cost_allocations(
        {DAY: sell}, [position(1, buy_day=old)]
    )["1"]
    assert missing["status"] == "research_cost_invalid"
    assert "official_source_missing:" + old in missing["reason"]


@pytest.mark.parametrize(
    "mutation",
    [
        "custody",
        "account",
        "quantity",
        "terminal",
        "quality",
        "identity",
        "sourcehash",
        "future",
    ],
)
def test_unproven_sources_do_not_get_allocated_cost(tmp_path, mutation):
    observed, positions, _ = allocated(tmp_path)
    target = positions[0]
    if mutation == "custody":
        target["custody_rows"][0]["owner_type"] = "manual"
    if mutation == "account":
        target["custody_rows"][0]["account_key"] = "another"
    if mutation == "quantity":
        target["custody_rows"][0]["filled_qty"] = 1
    if mutation == "terminal":
        target["terminal_observed"] = False
    if mutation == "quality":
        target["execution_source_quality_reasons"] = [
            "source_gap_buy_quantity_or_price"
        ]
    if mutation == "identity":
        target["buy_legs"][0]["execution_no"] = ""
    if mutation == "sourcehash":
        observed["source_sha256"] = "a" * 64
    if mutation == "future":
        target["sell_legs"][0]["at"] = DAY + " 23:00:00"
    result = A.build_research_cost_allocations({DAY: observed}, positions)["1"]
    assert result["status"] != "research_cost_allocated"
    assert result["allocated_fees_taxes_krw"] is None


def test_fill_ownership_conflict_and_volume_overcoverage_fail_the_cohort(tmp_path):
    observed, positions, _ = allocated(tmp_path)
    positions[1]["buy_legs"] = deepcopy(positions[0]["buy_legs"])
    results = A.build_research_cost_allocations({DAY: observed}, positions)
    assert all("ownership_conflict" in r["reason"] for r in results.values())
    observed = source(tmp_path / "small", buy_qty=1, buy_amount=10000)
    assert (
        "exceeds_broker"
        in A.build_research_cost_allocations({DAY: observed}, [position(1)])["1"][
            "reason"
        ]
    )


def reseal(receipt):
    receipt["receipt_sha256"] = digest(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )


def test_fact_amount_clock_and_cohort_membership_are_verified(tmp_path):
    _, _, values = allocated(tmp_path)
    receipt = values["1"]
    context = dict(
        record_id="1",
        symbol="005930",
        buy_qty=2,
        buy_price=10000,
        sell_qty=2,
        sell_price=10100,
        completion_date=DAY,
    )
    assert (
        A.validate_research_fact_cost(receipt, **context)["status"]
        == "research_cost_allocated"
    )
    assert (
        A.validate_research_fact_cost(receipt, **{**context, "sell_price": 10101})[
            "status"
        ]
        == "research_cost_invalid"
    )
    assert (
        A.validate_research_fact_cost(
            receipt, **context, knowledge_cutoff=NOW.timestamp() - 1
        )["status"]
        == "research_cost_pending"
    )
    tampered = deepcopy(receipt)
    tampered["sources"][0]["allocated_cost_krw"] += 1
    reseal(tampered)
    assert (
        A.validate_research_fact_cost(tampered, **context)["status"]
        == "research_cost_invalid"
    )


def test_missing_configured_fee_nan_does_not_destroy_fill_identity(tmp_path):
    observed = source(tmp_path)
    item = position(1)
    item["sell_legs"][0]["net_pnl_krw"] = float("nan")
    item["execution_source_quality_reasons"] = ["source_gap_sell_leg_configured_cost"]
    assert (
        A.build_research_cost_allocations({DAY: observed}, [item])["1"]["status"]
        == "research_cost_allocated"
    )


def test_zero_confirmed_cost_is_valid_and_no_inputs_are_mutated(tmp_path):
    observed = source(tmp_path, cost=0)
    items = [position(1), position(2)]
    before = deepcopy((observed, items))
    result = A.build_research_cost_allocations({DAY: observed}, items)
    assert all(row["allocated_fees_taxes_krw"] == 0 for row in result.values())
    assert (observed, items) == before


def test_persist_and_prior_source_correction_invalidate_only_dependent_generation(
    tmp_path,
):
    observed, positions, receipts = allocated(tmp_path)
    old_generation = source_generation(tmp_path, DAY)
    C.atomic(C.source_path(tmp_path, DAY), observed)
    A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    first = source_generation(tmp_path, DAY)
    assert first != old_generation
    index = tmp_path / "runtime/initial_quantity_research_costs" / DAY / "index.json"
    before = index.stat().st_mtime_ns
    A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    assert index.stat().st_mtime_ns == before
    observed["observed_at"] = DAY + "T22:00:00+09:00"
    observed["source_sha256"] = digest(
        {k: v for k, v in observed.items() if k != "source_sha256"}
    )
    C.atomic(C.source_path(tmp_path, DAY), observed)
    assert source_generation(tmp_path, DAY) != first
    assert len(list((index.parent / "generations").glob("*.json"))) == 2


def test_many_positions_keep_proof_size_bounded_and_total_cost_conserved(tmp_path):
    count = 256
    observed = source(
        tmp_path,
        buy_qty=count * 2,
        sell_qty=count * 2,
        buy_amount=count * 20000,
        sell_amount=count * 20200,
        cost=12345,
    )
    receipts = A.build_research_cost_allocations(
        {DAY: observed}, [position(i) for i in range(1, count + 1)]
    )
    assert len(receipts) == count
    assert sum(x["allocated_fees_taxes_krw"] for x in receipts.values()) == 12345
    assert max(len(json.dumps(x)) for x in receipts.values()) < 5000
    assert (
        max(
            len(x["sources"][0]["allocation_membership_proof"])
            for x in receipts.values()
        )
        == 8
    )


def test_completed_sell_before_buy_is_invalid_even_with_later_official_source(tmp_path):
    observed = source(tmp_path)
    item = position(1)
    item["buy_legs"][0]["at"] = DAY + " 11:00:00"
    result = A.build_research_cost_allocations({DAY: observed}, [item])["1"]
    assert "sell_precedes_buy" in result["reason"]


@pytest.mark.parametrize("cutoff", [float("nan"), float("inf"), True])
def test_invalid_knowledge_cutoff_cannot_admit_future_cost(tmp_path, cutoff):
    _, _, values = allocated(tmp_path)
    result = A.validate_research_fact_cost(
        values["1"],
        record_id="1",
        symbol="005930",
        buy_qty=2,
        buy_price=10000,
        sell_qty=2,
        sell_price=10100,
        completion_date=DAY,
        knowledge_cutoff=cutoff,
    )
    assert result["status"] == "research_cost_invalid"


def test_publisher_cannot_rebind_old_allocations_to_changed_official_cost(tmp_path):
    observed, _, receipts = allocated(tmp_path)
    changed = deepcopy(observed)
    changed["observed_at"] = DAY + "T22:00:00+09:00"
    changed["source_sha256"] = digest(
        {k: v for k, v in changed.items() if k != "source_sha256"}
    )
    C.atomic(C.source_path(tmp_path, DAY), changed)
    with pytest.raises(ValueError, match="source_changed_before_publication"):
        A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    assert not (
        tmp_path / "runtime/initial_quantity_research_costs" / DAY / "index.json"
    ).exists()


def test_native_generation_reads_committed_immutable_receipts_not_mutable_aliases(
    tmp_path,
):
    observed, _, receipts = allocated(tmp_path)
    C.atomic(C.source_path(tmp_path, DAY), observed)
    A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    before = source_generation(tmp_path, DAY)
    alias = tmp_path / "runtime/initial_quantity_research_costs" / DAY / "1.json"
    alias.write_text('{"an_uncommitted_writer": true}')
    assert source_generation(tmp_path, DAY) == before


@pytest.mark.parametrize("invalid", ["[]", "not-json"])
def test_invalid_official_dependency_stays_visible_without_global_decode_failure(
    tmp_path, invalid
):
    observed, _, receipts = allocated(tmp_path)
    C.atomic(C.source_path(tmp_path, DAY), observed)
    A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    C.source_path(tmp_path, DAY).write_text(invalid)
    generation = source_generation(tmp_path, DAY)
    source = generation["quantity_research_cost_generation"]["source_dates"][0]
    assert source["status"] == "source_invalid"
    assert source["source_sha256"] is None


def test_record_generation_projection_is_bounded_and_keeps_global_parent(tmp_path):
    from src.engine.lifecycle.broker_cost_reconciliation import record_source_projector

    observed, _, receipts = allocated(tmp_path)
    C.atomic(C.source_path(tmp_path, DAY), observed)
    A.persist_research_costs(tmp_path, DAY, receipts, [DAY])
    generation = source_generation(tmp_path, DAY)
    project = record_source_projector(generation)
    compact = project("1", receipts["1"])
    part = compact["quantity_research_cost_generation"]
    assert part["projection_scope"] == "record"
    assert len(part["receipts"]) == len(part["source_dates"]) == 1
    assert compact["sha256"] == part["parent_generation_sha256"] == generation["sha256"]
    assert len(generation["quantity_research_cost_generation"]["receipts"]) == 2
    assert part["research_generation_sha256"] == digest(
        generation["quantity_research_cost_generation"]
    )


def test_fractional_sell_average_preserves_exact_fill_money_and_binds_db_reference(
    tmp_path,
):
    observed = source(
        tmp_path, buy_qty=3, sell_qty=3, buy_amount=30000, sell_amount=30100, cost=10
    )
    item = position(1, qty=3)
    item["sell_legs"] = [
        {**item["sell_legs"][0], "qty": 2, "price": 10000},
        {**item["sell_legs"][0], "qty": 1, "price": 10100, "execution_no": "103"},
    ]
    item["fact_buy_price"], item["fact_sell_price"] = 10000, 10033
    receipt = A.build_research_cost_allocations({DAY: observed}, [item])["1"]
    assert receipt["status"] == "research_cost_allocated"
    assert receipt["allocated_net_pnl_krw"] == 90
    assert receipt["sell_amount_krw"] == 30100
    assert receipt["fact_sell_price"] == 10033
    assert (
        A.validate_research_fact_cost(
            receipt,
            record_id="1",
            symbol="005930",
            buy_qty=3,
            buy_price=10000,
            sell_qty=3,
            sell_price=10033,
            completion_date=DAY,
        )["status"]
        == "research_cost_allocated"
    )
    assert (
        A.validate_research_fact_cost(
            receipt,
            record_id="1",
            symbol="005930",
            buy_qty=3,
            buy_price=10000,
            sell_qty=3,
            sell_price=10034,
            completion_date=DAY,
        )["status"]
        == "research_cost_invalid"
    )
