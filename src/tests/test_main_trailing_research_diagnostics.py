"""Observed gaps and pure exit diagnostics cannot redefine selector economics."""

import json

import pytest

from src.engine.automation import main_trailing_all_scope_research as owner
from src.engine.automation import main_trailing_research_diagnostics as diagnostic
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.tests.test_main_trailing_partitioned_research import sharded
from src.tests.test_main_all_scope_trailing import position, quote, vector


def test_sealed_producer_replay_to_diagnostic_keeps_realized_floor_and_zero_delta(
    tmp_path,
):
    source, output = sharded(tmp_path)
    report = owner.run(
        source / "manifest.json", input_root=source, output_root=output, dry_run=False
    )
    prior = (output / "research_2026-10-08.json").read_bytes()
    result = diagnostic.build(
        source / "manifest.json",
        input_root=source,
        report_path=output / "research_2026-10-08.json",
    )
    assert result["population_count"] == 2
    assert result["cohort_counts"] == {"actual_completed": 2}
    assert result["exit_only_comparisons"][0]["paired_count"] == 2
    assert result["exit_only_comparisons"][0]["exit_only_paired_delta_net_krw"] == 0
    assert result["selector_metrics_redefined"] is False
    assert result["actual_profit_verified"] is False
    assert result["allowed_runtime_apply"] is False
    assert prior == (output / "research_2026-10-08.json").read_bytes()
    metrics = report["common_population_evaluation"]["strata"]["actual_completed"][
        "metrics"
    ]["incumbent"]
    # The first settlement is not known before holdout entry and stays purged.
    # The realized floor still applies to the held-out model comparison.
    assert metrics["train"]["paired_ev_pct"] is None
    assert metrics["holdout"]["paired_ev_pct"] < 0
    assert result["artifact_sha256"] == digest(
        {k: v for k, v in result.items() if k != "artifact_sha256"}
    )


def test_source_gap_has_no_zero_profit_or_success_observation(tmp_path):
    source, output = sharded(tmp_path)
    manifest = owner._sealed(source / "manifest.json")
    from src.engine.lifecycle import research_storage as storage
    from src.tests.test_main_all_scope_research import write

    refs = list(storage.iter_tree(source, manifest["partitions_ref"]))
    for ref in refs:
        part = owner._sealed(source / ref["path"])
        part.pop("artifact_sha256")
        for row in part["positions"]:
            row["automatic_management_allowed"] = False
        ref["artifact_sha256"] = write(source / ref["path"], part)
    manifest.pop("artifact_sha256")
    manifest["partitions_ref"] = storage.write_tree(source, refs)
    write(source / "manifest.json", manifest)
    owner.run(
        source / "manifest.json", input_root=source, output_root=output, dry_run=False
    )
    result = diagnostic.build(
        source / "manifest.json",
        input_root=source,
        report_path=output / "research_2026-10-08.json",
    )
    assert result["exit_only_comparisons"] == []
    assert result["economic_comparison_state"] == "source_or_execution_insufficient"
    assert (
        result["incumbent_outcomes"][0]["reason"]
        == "position_identity_or_custody_unverified"
    )
    assert result["incumbent_outcomes"][0]["count"] == 2
    assert all(
        row["complete_lifecycle_verified"] is False
        for row in result["position_observations"]
    )


@pytest.mark.parametrize(
    "damage",
    [
        "hash",
        "future",
        "wrong_route",
        "stale",
        "native_price",
        "before_entry",
        "epoch",
        "native_hash",
    ],
)
def test_quote_diagnostic_rejects_invalid_or_future_observations(damage):
    event = quote(1, "2026-10-08T09:00:01")
    cutoff = event["known_at"]
    if damage == "hash":
        event["bid"] += 1
    elif damage == "future":
        cutoff -= 0.5
    elif damage == "wrong_route":
        event["route"] = "NXT"
        event["source_sha256"] = digest(
            {k: v for k, v in event.items() if k != "source_sha256"}
        )
    else:
        if damage == "stale":
            event["known_at"] += 60
            cutoff = event["known_at"]
        elif damage == "native_price":
            event["bid"] = 999
            event["ask"] = 1001
            event["trade_peak_price"] = 1000
        elif damage == "before_entry":
            event["event_at"] = position()["entry_at"] - 60
        elif damage == "epoch":
            event["transport_epoch"] += 1
        elif damage == "native_hash":
            event["quote_snapshot_sha256"] = "0" * 64
        event["source_sha256"] = digest(
            {k: v for k, v in event.items() if k != "source_sha256"}
        )
    result = diagnostic._observation(position(), [event], vector(), cutoff)
    assert result["state"] == "unassessable"
    assert result["maximum_observed_peak_net_pct"] is None


def test_observed_peak_never_claims_full_lifecycle_and_add_does_not_reuse_initial_basis():
    event = quote(1, "2026-10-08T09:00:01")
    later = quote(2, "2026-10-08T09:00:04", peak=200)
    result = diagnostic._observation(
        position(), [event, {"kind": "ADD"}, later], vector(), later["known_at"]
    )
    assert result["state"] == "observed_start_reached"
    assert result["maximum_observed_peak_net_pct"] < 1
    assert result["lifecycle_changed"] is True
    assert result["complete_lifecycle_verified"] is False
    assert result["counts"]["observed_gaps_over_two_seconds"] == 1


def test_observation_uses_runtime_market_route_and_item_overrides():
    event = quote(1, "2026-10-08T09:00:01")
    p = position()
    p.update(
        route="NXT",
        item="123456_NX",
        routes_by_market={"REGULAR": "KRX"},
        items_by_market={"REGULAR": "123456"},
    )
    result = diagnostic._observation(p, [event], vector(), event["known_at"])
    assert result["counts"]["source_verified_observed_quotes"] == 1


def test_diagnostic_rejects_resealed_report_with_wrong_manifest_binding(tmp_path):
    source, output = sharded(tmp_path)
    owner.run(
        source / "manifest.json", input_root=source, output_root=output, dry_run=False
    )
    path = output / "research_2026-10-08.json"
    report = json.loads(path.read_bytes())
    report.pop("artifact_sha256")
    report["input_manifest_path"] = str(source / "other.json")
    from src.tests.test_main_all_scope_research import write

    write(path, report)
    with pytest.raises(ValueError, match="report_binding_invalid"):
        diagnostic.build(source / "manifest.json", input_root=source, report_path=path)


@pytest.mark.parametrize("partitioned", [False, True])
@pytest.mark.parametrize(
    "available", ["2026-10-08T09:00:01+09:00", "2026-10-09T09:00:01+09:00", None]
)
def test_native_actual_cost_is_available_only_before_research_cutoff(
    tmp_path, partitioned, available
):
    from src.tests.test_main_all_scope_research import fixture, write
    from src.engine.lifecycle import research_storage as storage

    source, output = sharded(tmp_path) if partitioned else fixture(tmp_path)
    manifest = owner._sealed(source / "manifest.json")
    refs = (
        list(storage.iter_tree(source, manifest["partitions_ref"]))
        if partitioned
        else manifest["partitions"]
    )
    for ref in refs:
        part = owner._sealed(source / ref["path"])
        part.pop("artifact_sha256")
        for row in part["positions"]:
            actual = row["actual_cost_reconciliation"]
            actual.pop("known_at", None)
            actual.update(cost_available_at=available, reconciled_at=available)
        ref["artifact_sha256"] = write(source / ref["path"], part)
    manifest.pop("artifact_sha256")
    if partitioned:
        manifest["partitions_ref"] = storage.write_tree(source, refs)
    write(source / "manifest.json", manifest)
    result = owner.run(
        source / "manifest.json", input_root=source, output_root=output, dry_run=False
    )
    if partitioned:
        outcomes = []
        for ref in storage.iter_tree(output, result["partition_results_ref"]):
            part = owner._sealed(output / ref["path"])
            for row in storage.iter_tree(output, part["result_records_ref"]):
                outcomes.extend(
                    storage.expand_outcomes(output, row)["outcomes"].values()
                )
    else:
        outcomes = []
        for part in output.glob("partitions/*.json"):
            checkpoint = owner._sealed(part)
            for values in checkpoint["result"]["minimal_results"].values():
                outcomes.extend(values.values())
    assert outcomes
    assert all(
        (row["actual_pnl_krw"] is not None)
        == (available == "2026-10-08T09:00:01+09:00")
        for row in outcomes
    )


def joint_path():
    from src.tests.test_scalp_trailing_mechanical_strength import (
        _snapshot,
        _depth,
        _trade,
    )

    p = position()
    p.update(qty=1, buy_basis_krw=96200.0)
    depths, trades, events = [], [], []
    for seq, bid in enumerate((96800, 96900, 96800, 96700, 96600, 96400, 96200), 1):
        stamp = p["entry_at"] + seq / 10
        d = _depth(seq, int(stamp * 1000), 10 + seq * 10, 10)
        d["bid_levels"][0]["price"] = bid
        d["ask_levels"][0]["price"] = bid + 100
        depths.append(d)
        t = _trade(
            seq, int(stamp * 1000), "BUY" if seq < 3 else "SELL", 10 if seq < 3 else 100
        )
        t["price"] = 97000 if seq == 2 else bid
        trades.append(t)
        ws = _snapshot(list(depths), list(trades))
        from src.engine.scalping.universal_trailing_replay import quote_projection

        events.append(
            quote_projection(
                ws,
                known_at=stamp,
                event_at=stamp,
                route="KRX",
                item="123456",
                transport_epoch=1,
                sequence=seq,
                bid=bid,
                ask=bid + 100,
                bid_qty=10 + seq * 10,
                peak=97000 if seq >= 2 else 96800,
                quantity=1,
                coverage_complete=True,
                entry_cost_model=p["cost_model"],
            )
        )
    return p, events


def test_joint_study_computes_floor_and_strength_release_without_live_policy():
    p, events = joint_path()
    result = diagnostic._observation(p, iter(events), vector(), p["entry_at"] + 1)[
        "joint_trailing_observation"
    ]
    assert result["hypothesis_count"] == 72
    assert result["evaluations"] <= 72 * len(events)

    def selected(floor, release):
        return next(
            r
            for r in result["hypotheses"]
            if r["start_delta_pct"] == 0
            and r["weak_multiplier"] == 1
            and r["strong_multiplier"] == 1
            and r["net_floor_pct"] == floor
            and r["release"] == release
        )

    parent = selected(None, "incumbent")["crossing"]
    flow = selected(None, "flow_and_tape_two")["crossing"]
    floor = selected(0.0, "incumbent")["crossing"]
    assert parent["bid"] == 96200
    assert flow["bid"] == 96600 and flow["strength"] == "WEAK"
    assert floor["bid"] == 96400 and floor["trigger"] == "net_floor_breach"
    # A cost floor does not promise breakeven: the next tick can undershoot it.
    assert floor["observed_quote_net_pct"] < 0
    assert parent["observed_quote_net_pct"] == pytest.approx(-0.23)
    assert result["primary_ev"] is None and result["selected_candidate"] is None
    assert result["allowed_runtime_apply"] is False


@pytest.mark.parametrize(
    "fault", ["hash", "route", "clock", "cost", "quantity", "gap", "add"]
)
def test_joint_study_censors_invalid_evidence_and_missing_cost(fault):
    p, events = joint_path()
    if fault == "cost":
        p["cost_model"] = {}
    if fault == "hash":
        for e in events:
            e["source_sha256"] = "0" * 64
    if fault == "route":
        p["route"] = "nxt_only"
    if fault == "clock":
        events = list(reversed(events))
    if fault == "quantity":
        p["qty"] = 1000
    if fault == "gap":
        events.insert(1, {"status": "source_gap", "reason": "historical_missing"})
    if fault == "add":
        events.insert(1, {"kind": "ADD"})
    result = diagnostic._observation(p, iter(events), vector(), p["entry_at"] + 1)[
        "joint_trailing_observation"
    ]
    crossings = [r["crossing"] for r in result["hypotheses"] if r["crossing"]]
    if fault in ("hash", "route", "cost", "add", "quantity"):
        assert all(c["observed_quote_net_pct"] is None for c in crossings)
    else:
        assert result["gaps"]
    assert result["actual_profit_verified"] is False


def test_joint_consumer_publishes_bounded_rows_under_native_tree(tmp_path):
    source, output = sharded(tmp_path)
    owner.run(
        source / "manifest.json", input_root=source, output_root=output, dry_run=False
    )
    result = diagnostic.build(
        source / "manifest.json",
        input_root=source,
        report_path=output / "research_2026-10-08.json",
    )
    from src.engine.lifecycle import research_storage as storage

    rows = list(storage.iter_tree(output, result["joint_trailing_observations_ref"]))
    assert rows and all(r["hypothesis_count"] == 72 for r in rows)
    assert all(
        "joint_trailing_observation" not in r for r in result["position_observations"]
    )


def test_joint_cost_projection_accepts_native_numeric_serialization():
    from copy import deepcopy

    p, events = joint_path()
    expected = diagnostic._observation(p, iter(events), vector(), p["entry_at"] + 1)
    p = deepcopy(p)
    p["qty"], p["buy_basis_krw"] = str(p["qty"]), str(p["buy_basis_krw"])
    for key in ("buy_cost_krw", "sell_cost_rate"):
        p["cost_model"][key] = str(p["cost_model"][key])
    actual = diagnostic._observation(p, iter(events), vector(), p["entry_at"] + 1)
    assert actual == expected
