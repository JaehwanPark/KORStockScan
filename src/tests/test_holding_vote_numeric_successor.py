"""Numerical EXIT selection, sealed successor, and unchanged safety adapters.

Synthetic fixtures prove code reachability, not naturally realized economics.
"""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from src.engine.scalping import holding_vote_experiment as experiment
from src.engine.scalping import holding_path_vote_policy as policy
from src.engine.scalping.holding_path_vote_replay import summarize_holding_path_votes
from src.engine.lifecycle import research_storage as storage
from src.tests.test_holding_path_vote_replay import EMPTY_SOURCE_QUALITY

CELL = "EXIT_SOFT_STOP|REGULAR"


def write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body))
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def fixture(root):
    initial_replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    original_source = write(
        root / "report/monitor_snapshots/holding_exit_observation_2026-10-07.json",
        dict(
            date="2026-10-07",
            holding_path_vote_replay=initial_replay,
            completed_population_quality=dict(
                complete=False,
                db_completed_main_ids=[],
                strict_completed_position_ids=[],
                source_gap_ids=[],
                excluded_all_reasons={},
                source_gap_dates=[],
            ),
        ),
    )
    parent = policy.create_bundle(
        source_date="2026-10-07",
        target_date="2026-10-08",
        source_report_sha256=original_source["sha256"],
        replay=initial_replay,
        source_quality=EMPTY_SOURCE_QUALITY,
    )
    parent_path = policy.policy_path(root, "2026-10-08")
    parent_ref = write(parent_path, parent)
    write(
        root
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json",
        dict(
            holding_path_vote_policy=dict(
                status=policy.publication_status(parent),
                source_date="2026-10-07",
                target_date="2026-10-08",
                bundle_sha256=parent["bundle_sha256"],
                policy_set_sha256=parent["policy_set_sha256"],
                source_report_sha256=original_source["sha256"],
                cell_count=12,
            )
        ),
    )
    original = parent["cells"][CELL]["policy"]
    choices = experiment.grid(CELL.split("|")[0], original)
    names = [
        name
        for name, value in choices.items()
        if set(k for k in value if value[k] != original[k]) == {"max_defer_sec"}
    ]
    name = names[0]
    perf = write(
        root / "report/holding_path_vote_research/performance.json",
        dict(
            schema="holding_vote_performance_v1",
            status="pass",
            scope="runtime_and_postclose",
            code_sha256=experiment.code_sha(),
            unresolved_findings=[],
        ),
    )
    contract = dict(
        schema=experiment.SCHEMA,
        parent_sha256=parent["bundle_sha256"],
        source_sha256=policy.digest(dict(files={}, cost_generations={})),
        candidate_grid_sha256=policy.digest(choices),
        cell=CELL,
        code_sha256=experiment.code_sha(),
        approval_reference="synthetic-frozen-fixture",
        allowed_keys=["max_defer_sec"],
        max_step={"max_defer_sec": 100.0},
        frozen_at=1.0,
        split_at=1000.0,
        embargo_sec=240.0,
        min_train=2,
        min_holdout=2,
        min_train_days=2,
        min_holdout_days=2,
        minimum_paired_ev_krw=0.0,
        min_daily_delta_krw=0.0,
        max_tail_regression_krw=0.0,
        max_exposure_increase_sec=0.0,
        max_model_error_krw=1.0,
        max_standard_error_krw=100.0,
        max_censoring_ratio=0.0,
        performance_receipt=perf,
    )
    contract["experiment_sha256"] = policy.digest(contract)
    contract_file = write(
        root / "runtime/research/holding_path_vote/experiments_2026-10-08.json",
        {CELL: contract},
    )
    records = []
    for i in range(4):
        records.append(
            dict(
                position_key=f"main:{i}",
                split="train" if i < 2 else "holdout",
                day=f"2026-10-{i + 1:02}",
                actual_net_krw=0.0,
                source_sha256=policy.digest(["synthetic", i]),
                outcomes={
                    "parent": dict(
                        status="modeled", net_krw=0.0, exposure_sec=30.0, mae_pct=-0.1
                    ),
                    name: dict(
                        status="modeled", net_krw=10.0, exposure_sec=20.0, mae_pct=-0.1
                    ),
                },
            )
        )
    selected = experiment.select(records, choices, parent=original, contract=contract)
    out = root / "report/holding_path_vote_research/2026-10-08/fixture"
    out.mkdir(parents=True)
    ref = storage.write_tree(out, records)
    receipt = dict(
        selected,
        cell=CELL,
        parent_policy_sha256=policy.digest(original),
        candidate_grid_sha256=policy.digest(choices),
        contract=contract,
        outcomes_ref=ref,
        root=str(out),
        source_sha256=contract["source_sha256"],
        code_sha256=experiment.code_sha(),
        actual_profit_verified=False,
        evidence_mode="actual_entry_counterfactual_exit",
    )
    receipt["receipt_sha256"] = policy.digest(receipt)
    numeric = dict(
        schema=experiment.RESULT_SCHEMA,
        status="selected",
        parent=dict(
            path=str(parent_path),
            byte_sha256=parent_ref["sha256"],
            bundle_sha256=parent["bundle_sha256"],
            policy_set_sha256=parent["policy_set_sha256"],
            target_date="2026-10-08",
            cells={k: c["policy"] for k, c in parent["cells"].items()},
        ),
        code_sha256=experiment.code_sha(),
        source_sha256=contract["source_sha256"],
        source_inventory={},
        cost_generations={},
        vote_source_inventory={},
        cells={CELL: receipt},
        contract_file_path=contract_file["path"],
        contract_file_sha256=contract_file["sha256"],
        selected_cells={CELL: dict(policy=choices[name], receipt=receipt)},
        allowed_runtime_apply=False,
    )
    return parent, original, choices, name, contract, records, numeric


def test_train_selection_failure_never_reselects_on_holdout(tmp_path):
    _, base, choices, name, c, rows, _ = fixture(tmp_path)
    other = next(k for k in choices if k != name)
    alternate = dict(base, max_defer_sec=base["max_defer_sec"] * 0.75)
    arms = {name: choices[name], other: alternate}
    for row in rows:
        row["outcomes"][other] = dict(
            status="modeled", net_krw=5.0, exposure_sec=20.0, mae_pct=-0.1
        )
        if row["split"] == "holdout":
            row["outcomes"][name]["net_krw"] = -20.0
    result = experiment.select(rows, arms, parent=base, contract=c)
    assert result["train_selected"] == name
    assert result["status"] == "hold_no_edge" and result["selected"] is None
    rows[0]["outcomes"][name]["net_krw"] = None
    assert experiment.aggregate(rows, name, c)["train"]["n"] == 1


def test_numeric_successor_native_handoff_bootstrap_and_runtime(tmp_path, monkeypatch):
    parent, original, choices, name, c, rows, numeric = fixture(tmp_path)
    experiment.validate_contract(
        c,
        parent_sha=parent["bundle_sha256"],
        source_sha=c["source_sha256"],
        grid_sha=policy.digest(choices),
        cell=CELL,
    )
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    replay["vote_numeric_research"] = numeric
    observation = dict(
        date="2026-10-08",
        holding_path_vote_replay=replay,
        completed_population_quality=dict(
            complete=False,
            db_completed_main_ids=[],
            strict_completed_position_ids=[],
            source_gap_ids=[],
            excluded_all_reasons={},
            source_gap_dates=[],
        ),
    )
    observation_path = (
        tmp_path / "report/monitor_snapshots/holding_exit_observation_2026-10-08.json"
    )
    source = write(observation_path, observation)
    bundle = policy.create_bundle(
        source_date="2026-10-08",
        target_date="2026-10-12",
        source_report_sha256=source["sha256"],
        replay=replay,
        source_quality=EMPTY_SOURCE_QUALITY,
    )
    assert bundle["schema"] == policy.SUCCESSOR_SCHEMA
    assert bundle["cells"][CELL]["policy"] == choices[name]
    assert (
        bundle["realized_paired_ev_krw"] is None
        and bundle["actual_profit_verified"] is False
    )
    assert all(
        c["policy"] == parent["cells"][key]["policy"]
        for key, c in bundle["cells"].items()
        if key.startswith("ADD_REBOUND|")
    )
    write(policy.policy_path(tmp_path, "2026-10-12"), bundle)
    receipt = dict(
        status=policy.publication_status(bundle),
        source_date="2026-10-08",
        target_date="2026-10-12",
        bundle_sha256=bundle["bundle_sha256"],
        policy_set_sha256=bundle["policy_set_sha256"],
        source_report_sha256=source["sha256"],
        cell_count=12,
        allowed_runtime_apply=True,
    )
    write(
        tmp_path
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json",
        dict(schema_version=3, holding_path_vote_policy=receipt),
    )
    from src.engine.automation import (
        postclose_summary_handoff as handoff,
        runtime_policy_bootstrap as bootstrap,
    )
    from src.engine import build_next_stage2_checklist

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    monkeypatch.setattr(
        build_next_stage2_checklist, "_next_krx_trading_day", lambda _: "2026-10-12"
    )
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    assert (
        handoff.verify_summary_handoff(
            "2026-10-08",
            report_dir=tmp_path / "report",
            checklist_path=tmp_path / "unused.md",
            require_tower=False,
            require_checklist=False,
        )["status"]
        == "pass"
    )
    env, checked = bootstrap._holding_vote_handoff("2026-10-12")
    selected, loaded = policy.runtime_policy_from_env(
        env, data_root=tmp_path, active_date="2026-10-12"
    )
    assert loaded["status"] == "validated_successor_loaded"
    assert selected[tuple(CELL.split("|"))] == choices[name]
    altered = copy.deepcopy(bundle)
    altered["cells"]["ADD_REBOUND|REGULAR"]["policy"]["max_defer_sec"] /= 2
    altered["bundle_sha256"] = policy.digest(
        {k: v for k, v in altered.items() if k != "bundle_sha256"}
    )
    with pytest.raises(ValueError):
        policy.validate_bundle(altered, target_date="2026-10-12")
    observation_path.write_text("{}")
    with pytest.raises(ValueError, match="source_report_hash"):
        policy.verify_source_handoff(tmp_path, bundle)


def test_unarmed_native_research_carries_actual_parent_values(tmp_path, monkeypatch):
    from src.engine.automation import postclose_summary_handoff as handoff

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    parent, *_ = fixture(tmp_path)
    (
        tmp_path / "runtime/research/holding_path_vote/experiments_2026-10-08.json"
    ).unlink()
    result = experiment.native_research(tmp_path, "2026-10-08")
    assert result["status"] == "experiment_not_armed"
    assert result["parent"]["bundle_sha256"] == parent["bundle_sha256"]
    assert result["selected_cells"] == {}


def test_legacy_fifteen_cell_parent_carries_only_twelve_active_cells(
    tmp_path, monkeypatch
):
    from src.engine.automation import postclose_summary_handoff as handoff

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    parent, *_ = fixture(tmp_path)
    active_sha = parent["policy_set_sha256"]
    parent["prompt_version"] = "holding_path_vote_v10"
    for market in policy.MARKETS:
        original = parent["cells"]["EXIT_SOFT_STOP|" + market]["policy"]
        retired = dict(original, max_defer_sec=30.0)
        parent["cells"]["EXIT_BAD_ENTRY_REFINED|" + market] = dict(
            policy=retired,
            policy_sha256=policy.digest(retired),
            rollback_policy_sha256=policy.digest(retired),
            realized_paired_ev_krw=None,
            estimated_paired_ev_krw=None,
        )
    parent["policy_set_sha256"] = parent["rollback_policy_set_sha256"] = policy.digest(
        {k: v["policy_sha256"] for k, v in parent["cells"].items()}
    )
    parent["bundle_sha256"] = policy.digest(
        {k: v for k, v in parent.items() if k != "bundle_sha256"}
    )
    parent_path = policy.policy_path(tmp_path, "2026-10-08")
    write(parent_path, parent)
    summary_path = (
        tmp_path
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-07.json"
    )
    summary = json.loads(summary_path.read_text())
    summary["holding_path_vote_policy"].update(
        bundle_sha256=parent["bundle_sha256"],
        policy_set_sha256=parent["policy_set_sha256"],
        cell_count=15,
    )
    write(summary_path, summary)
    (
        tmp_path / "runtime/research/holding_path_vote/experiments_2026-10-08.json"
    ).unlink()
    before = parent_path.read_bytes()
    numeric = experiment.native_research(tmp_path, "2026-10-08")
    assert numeric["status"] == "experiment_not_armed"
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    replay["vote_numeric_research"] = numeric
    bundle = policy.create_bundle(
        source_date="2026-10-08",
        target_date="2026-10-12",
        source_report_sha256="f" * 64,
        replay=replay,
        source_quality=EMPTY_SOURCE_QUALITY,
    )
    assert len(bundle["cells"]) == 12
    assert bundle["selection_mode"] == "incumbent_carry"
    assert bundle["rollback_policy_set_sha256"] == active_sha
    assert bundle["parent"]["native_policy_set_sha256"] == parent["policy_set_sha256"]
    assert all(
        v["policy"] == parent["cells"][k]["policy"] for k, v in bundle["cells"].items()
    )
    assert not any(k.startswith("EXIT_BAD_ENTRY_REFINED|") for k in bundle["cells"])
    assert parent_path.read_bytes() == before
    observation = json.loads(
        (
            tmp_path
            / "report/monitor_snapshots/holding_exit_observation_2026-10-07.json"
        ).read_text()
    )
    observation.update(date="2026-10-08", holding_path_vote_replay=replay)
    source = write(
        tmp_path / "report/monitor_snapshots/holding_exit_observation_2026-10-08.json",
        observation,
    )
    bundle = policy.create_bundle(
        source_date="2026-10-08",
        target_date="2026-10-12",
        source_report_sha256=source["sha256"],
        replay=replay,
        source_quality=policy.source_quality_from_observation(observation),
    )
    target = policy.policy_path(tmp_path, "2026-10-12")
    write(target, bundle)
    write(
        tmp_path
        / "report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json",
        dict(
            holding_path_vote_policy=dict(
                status=policy.publication_status(bundle),
                source_date="2026-10-08",
                target_date="2026-10-12",
                bundle_sha256=bundle["bundle_sha256"],
                policy_set_sha256=bundle["policy_set_sha256"],
                source_report_sha256=source["sha256"],
                cell_count=12,
            )
        ),
    )
    policy.verify_source_handoff(tmp_path, bundle)
    selected, loaded = policy.runtime_policy_from_env(
        {
            policy.ENV_PATH: str(target),
            policy.ENV_DATE: "2026-10-12",
            policy.ENV_SHA: bundle["bundle_sha256"],
        },
        data_root=tmp_path,
        active_date="2026-10-12",
    )
    assert loaded["status"] == "verified_incumbent_loaded"
    assert len(selected) == 12


@pytest.mark.parametrize("broken", ["{invalid json\n", "[]\n", '"invalid row"\n'])
def test_native_research_rejects_unidentifiable_raw_population(
    tmp_path, monkeypatch, broken
):
    from src.engine.automation import postclose_summary_handoff as handoff
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    parent, _, _, _, contract, _, _ = fixture(tmp_path)
    path = tmp_path / "pipeline_events/pipeline_events_2026-10-08.jsonl"
    path.parent.mkdir()
    path.write_text(broken)
    contract["source_sha256"] = policy.digest(
        dict(
            files={str(path): byte_generation(path)},
            cost_generations={"2026-10-08": source_generation(tmp_path, "2026-10-08")},
        )
    )
    contract["experiment_sha256"] = policy.digest(
        {k: v for k, v in contract.items() if k != "experiment_sha256"}
    )
    write(
        tmp_path / "runtime/research/holding_path_vote/experiments_2026-10-08.json",
        {CELL: contract},
    )
    result = experiment.native_research(tmp_path, "2026-10-08")
    assert result["status"] == "source_gap"
    assert result["blocker"] == "holding_vote_unidentifiable_source_census"
    assert result["parent"]["bundle_sha256"] == parent["bundle_sha256"]
    assert result["selected_cells"] == {}


@pytest.mark.parametrize(
    "field,value",
    [
        ("performance_receipt", ["not a receipt"]),
        ("max_step", ["max_defer_sec"]),
        ("allowed_keys", [["max_defer_sec"]]),
    ],
)
def test_malformed_frozen_contract_carries_parent(tmp_path, monkeypatch, field, value):
    from src.engine.automation import postclose_summary_handoff as handoff

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    parent, _, _, _, contract, _, _ = fixture(tmp_path)
    contract[field] = value
    contract["experiment_sha256"] = policy.digest(
        {k: v for k, v in contract.items() if k != "experiment_sha256"}
    )
    write(
        tmp_path / "runtime/research/holding_path_vote/experiments_2026-10-08.json",
        {CELL: contract},
    )
    result = experiment.native_research(tmp_path, "2026-10-08")
    assert result["status"] == "source_gap"
    assert result["blocker"] == "holding_vote_frozen_contract_invalid"
    assert result["parent"]["bundle_sha256"] == parent["bundle_sha256"]


@pytest.mark.parametrize("conflicting", [False, True])
def test_native_metadata_duplicate_is_deduplicated_or_gap(
    tmp_path, monkeypatch, conflicting
):
    from src.engine.automation import main_stop_postclose as producer
    from src.engine.automation import postclose_summary_handoff as handoff

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    parent, *_ = fixture(tmp_path)
    row = dict(
        id=7, status="COMPLETED", actual_cost_reconciliation=dict(exact_pnl_krw=1.0)
    )
    other = copy.deepcopy(row)
    if conflicting:
        other["actual_cost_reconciliation"]["exact_pnl_krw"] = 2.0
    monkeypatch.setattr(producer, "completed_evidence", lambda *_: iter([row, other]))
    result = experiment.native_research(tmp_path, "2026-10-08")
    assert result["status"] == ("source_gap" if conflicting else "incumbent_carry")
    if conflicting:
        assert result["blocker"] == "holding_vote_actual_metadata_conflict"
    assert result["parent"]["bundle_sha256"] == parent["bundle_sha256"]
    assert result["selected_cells"] == {}


@pytest.mark.parametrize("field", ["source_inventory", "vote_source_inventory"])
def test_successor_rejects_source_substitution_outside_frozen_contract(tmp_path, field):
    from src.engine.lifecycle.holding_window_generation import byte_generation

    *_, numeric = fixture(tmp_path)
    path = tmp_path / "different-source.json"
    path.write_text("{}")
    numeric[field][str(path)] = byte_generation(path)
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    replay["vote_numeric_research"] = numeric
    with pytest.raises(
        ValueError, match="holding_vote_successor_source_binding_invalid"
    ):
        policy.create_bundle(
            source_date="2026-10-08",
            target_date="2026-10-12",
            source_report_sha256="f" * 64,
            replay=replay,
            source_quality=EMPTY_SOURCE_QUALITY,
        )


def test_selected_receipt_cannot_use_discovery_only_source_check(tmp_path):
    _, base, _, _, _, _, numeric = fixture(tmp_path)
    receipt = numeric["selected_cells"][CELL]["receipt"]
    receipt["source_sha256"] = None
    receipt["receipt_sha256"] = policy.digest(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )
    with pytest.raises(ValueError, match="holding_vote_comparison_receipt_invalid"):
        experiment.verify_receipt(receipt, parent=base, source_sha=None, cell=CELL)


def test_post_add_aggregate_and_hard_priority_are_independent_of_votes():
    from src.tests.test_main_stop_policy import rows, baseline
    from src.engine.scalping import main_stop_replay as replay
    from src.engine.scalping.main_stop_policy import digest

    values = list(rows())
    # Rebaseline from a completed actual ADD; no candidate ADD is simulated.
    first = values[0]
    aggregate = dict(
        schema="verified_post_add_generation_v1",
        position_key=first["position_key"],
        quantity=first["quantity"],
        buy_basis_krw=first["buy_basis_krw"],
        cost_source_sha256=first["cost_model"]["source_sha256"],
        completed_at=first["at"] - 1,
        add_receipt_sha256="b" * 64,
        pending_add=False,
        partial_fill=False,
    )
    aggregate["sha256"] = digest(aggregate)
    for row in values:
        row["post_add_generation"] = aggregate
        row["add_count"] = 1
        row["post_add_failure_inputs"] = dict(
            active=False,
            executed_at=first["at"] - 1,
            floor=0.0,
            eval_sec=100.0,
            feature_usable=False,
            large_sell_print=False,
            tick_acceleration=1.0,
        )
        row["bid"] = 9500.0 if row is values[-1] else 9990.0
        row["decision_profit_pct"] = -5.2 if row is values[-1] else -0.2
        row["source_sha256"] = digest(
            {k: v for k, v in row.items() if k != "source_sha256"}
        )
    result = replay.replay(
        values,
        baseline(),
        post_add_generation=True,
        vote_reader=lambda *_: pytest.fail("hard safety requested AI"),
    )
    assert result["status"] == "modeled" and result["reason"] == "scalp_hard_stop_pct"
    values[2]["pending_add"] = True
    values[2]["source_sha256"] = digest(
        {k: v for k, v in values[2].items() if k != "source_sha256"}
    )
    assert (
        replay.replay(values, baseline(), post_add_generation=True)["status"]
        == "source_gap"
    )


def test_original_request_stop_replay_reaches_selector_and_successor(
    tmp_path, monkeypatch
):
    """Full recorded request bytes drive the modeled arms and native publisher."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from dataclasses import replace
    from src.engine.ai import (
        holding_exit_vote as vote,
        holding_vote_replay_source as evidence,
    )
    from src.engine.scalping import (
        main_stop_policy as stop,
        ai_decision_trace as writer,
    )
    from src.engine.scalping.position_peak_ledger import position_cycle_id
    from src.tests.test_holding_path_vote_replay import _events, BUY_IDENTITY
    from src.tests.test_main_stop_policy import baseline

    parent, original, choices, name, contract, _, numeric = fixture(tmp_path)
    monkeypatch.setattr(writer, "DATA_DIR", tmp_path)
    monkeypatch.setattr(writer, "trace_enabled", lambda: True)
    records = []
    completed = []
    inventory = {}
    for i, day in enumerate(("2026-09-30", "2026-10-01", "2026-10-05", "2026-10-06")):
        at = datetime.fromisoformat(day + "T09:00:00+09:00").timestamp()
        monkeypatch.setattr(
            writer,
            "_now",
            lambda at=at: datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul")),
        )
        stock = dict(
            id=i + 100,
            code="005930",
            strategy="SCALPING",
            position_tag="SCANNER",
            buy_price=100.0,
            buy_qty=1,
        )
        position = position_cycle_id(stock)
        values = replace(baseline(), soft_stop_pct=-0.5, grace_sec=0)
        stock["main_stop_policy_pin"] = stop.pin(
            position_key=position,
            role="SCANNER",
            market="REGULAR",
            target=day,
            baseline=values,
        )
        votes = _events(
            "EXIT_SOFT_STOP",
            "REGULAR",
            verdicts=("VETO", "VETO"),
            position_key=position,
            session_key=day,
            base_at=at + 2,
        )
        store = vote.path_vote_store_path(tmp_path, position)
        for j, event in enumerate(votes):
            payload = dict(
                input_schema=vote.PATH_PROMPT_VERSION,
                requested_paths=["EXIT_SOFT_STOP"],
                position_key=position,
                buy_fill_identity=BUY_IDENTITY,
                market="REGULAR",
                session_key=day,
                position={"buy_price": 100, "curr_price": 100},
                source={"route": "krx_only", "transport_epoch": "1"},
                flow={},
                quote={},
                source_quality={"allowed": True},
            )
            hashes = vote.path_vote_input_hashes(payload, model=event["model"])
            payload["input_snapshot_id"] = hashes["input_snapshot_id"]
            captured = writer.capture_ai_request(
                prompt="Frozen original holding prompt",
                user_input=json.dumps(payload),
                endpoint_name="holding_path_vote",
                request_id=f"original-{i}-{j}",
                symbol="005930",
                require_json=True,
                model=event["model"],
                schema_name=vote.PATH_PROMPT_VERSION,
                metadata={
                    "holding_provider_contract": dict(
                        instructions="Frozen original holding prompt",
                        model=event["model"],
                        text={"format": "json"},
                    )
                },
            )
            event.update(
                route="krx_only",
                transport_epoch="1",
                request_payload_sha256=hashes["request_payload_sha256"],
                input_snapshot_id=hashes["input_snapshot_id"],
                prompt_sha256=captured["ai_prompt_sha256"],
                actual_request_reference=dict(
                    schema="holding_actual_request_reference_v1",
                    date=captured["ai_input_payload_store_date"],
                    request_id=captured["ai_decision_trace_id"],
                    request_envelope_sha256=captured["ai_request_envelope_sha256"],
                    payload_sha256=captured["ai_input_payload_sha256"],
                    prompt_sha256=captured["ai_prompt_sha256"],
                    response_sha256="e" * 64,
                    replay_exact=True,
                ),
            )
            monkeypatch.setattr(
                vote.time, "time", lambda event=event: event["received_at"] + 0.1
            )
            assert (
                vote.append_path_events_file(store, position, [event])[1] == "appended"
            )
        source = dict(
            schema=evidence.SCHEMA,
            path_id="EXIT_SOFT_STOP",
            required=True,
            position_key=position,
            buy_fill_identity=BUY_IDENTITY,
            store_name=store.name,
            market="REGULAR",
            model=votes[0]["model"],
            policy=original,
            policy_sha256=vote.input_snapshot_id(original),
            coverage_started_at=at,
            coverage_checked_at=at,
            coverage_complete=True,
            observed_at=at,
        )
        out = tmp_path / f"original_votes_{i}"
        out.mkdir()
        reference = evidence.assemble_votes(tmp_path, out, source, inventory)
        assert reference["status"] == "source_bound"
        rows = []
        for n in range(150):
            bid = 99.9 if n < 30 else 99.2 - (n - 30) * 0.005
            rows.append(
                stop.source_row(
                    stock,
                    at=at + n,
                    bid=bid,
                    bid_qty=100,
                    decision_profit_pct=bid - 100,
                    quote=dict(
                        market_route="krx_only",
                        item="005930",
                        transport_epoch="1",
                        observed_epoch=at + n,
                    ),
                    coverage_complete=True,
                    automatic_management_allowed=True,
                    runtime_flags=dict(
                        grace_enabled=True,
                        protect_enabled=True,
                        handoff_enabled=False,
                        vote_max_worsen_pct=0.8,
                    ),
                    cost_model=dict(
                        buy_cost_krw=0.0,
                        sell_cost_rate=0.0,
                        known_at=at - 1,
                        source_sha256="a" * 64,
                    ),
                    vote_source=dict(source, observed_at=at + n),
                )
            )
        reader = evidence.PreparedVotes(reference, out)
        try:
            outcomes = experiment.stop_outcomes(
                lambda: iter(rows),
                {"parent": original, name: choices[name]},
                prepared_votes=reader,
                path="EXIT_SOFT_STOP",
            )
        finally:
            reader.close()
        assert all(x["status"] == "modeled" for x in outcomes.values()), {
            k: (v["status"], v.get("reason")) for k, v in outcomes.items()
        }
        assert outcomes[name]["net_krw"] > outcomes["parent"]["net_krw"]
        pipeline = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
        pipeline.parent.mkdir(exist_ok=True)
        pipeline.write_text(
            "".join(
                json.dumps(
                    dict(stage="main_stop_source", fields=dict(main_stop_source=row))
                )
                + "\n"
                for row in rows
            )
        )
        completed.append(
            dict(
                id=stock["id"],
                status="COMPLETED",
                main_automatic_management_allowed=True,
                actual_cost_reconciliation=dict(
                    status="actual_cost_reconciled",
                    receipt_sha256="a" * 64,
                    raw_sha256="b" * 64,
                    exact_pnl_krw=outcomes["parent"]["net_krw"],
                ),
            )
        )
        records.append(
            dict(
                position_key=position,
                split="train" if i < 2 else "holdout",
                day=day,
                actual_net_krw=outcomes["parent"]["net_krw"],
                outcomes=outcomes,
                source_sha256=policy.digest(rows),
            )
        )
    # These frozen actual-amount witnesses are synthetic, never natural PnL.
    selected = experiment.select(records, choices, parent=original, contract=contract)
    assert selected["selected"] == name
    receipt = numeric["selected_cells"][CELL]["receipt"]
    receipt.update(
        selected, outcomes_ref=storage.write_tree(Path(receipt["root"]), records)
    )
    receipt["receipt_sha256"] = policy.digest(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    replay["vote_numeric_research"] = numeric
    bundle = policy.create_bundle(
        source_date="2026-10-08",
        target_date="2026-10-12",
        source_report_sha256="f" * 64,
        replay=replay,
        source_quality=EMPTY_SOURCE_QUALITY,
    )
    assert bundle["selection_mode"] == "validated_successor"
    assert bundle["cells"][CELL]["policy"] == choices[name]
    assert (
        bundle["actual_profit_verified"] is False
        and bundle["realized_paired_ev_krw"] is None
    )

    # The actual native assembler must bind these same recorded requests before
    # evaluating arms. A frozen contract omitting them cannot authorize replay.
    from src.engine.automation import main_stop_postclose as producer
    from src.engine.automation import postclose_summary_handoff as handoff
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation

    monkeypatch.setattr(handoff, "stage_receipt_issues", lambda *_: [])
    monkeypatch.setattr(producer, "completed_evidence", lambda *_: iter(completed))
    files = {
        str(p): byte_generation(p) for p in producer.sources(tmp_path, "2026-10-08")
    }
    costs = {r["day"]: source_generation(tmp_path, r["day"]) for r in records}
    contract.update(
        source_sha256=policy.digest(
            dict(files={**files, **inventory}, cost_generations=costs)
        ),
        frozen_at=datetime.fromisoformat("2026-09-29T00:00:00+09:00").timestamp(),
        split_at=datetime.fromisoformat("2026-10-03T00:00:00+09:00").timestamp(),
    )
    contract["experiment_sha256"] = policy.digest(
        {k: v for k, v in contract.items() if k != "experiment_sha256"}
    )
    write(
        tmp_path / "runtime/research/holding_path_vote/experiments_2026-10-08.json",
        {CELL: contract},
    )
    native = experiment.native_research(tmp_path, "2026-10-08")
    assert native["status"] == "selected", native
    assert native["selected_cells"][CELL]["policy"] == choices[name]
    assert native["vote_source_inventory"] == inventory
    assert native["source_sha256"] == contract["source_sha256"]

    # A source-only byte revision must fail before even the first modeled arm.
    request = next(Path(p) for p in inventory if "/ai_decision_requests/" in p)
    raw = request.read_bytes()
    request.write_bytes(raw + b" ")
    monkeypatch.setattr(
        experiment,
        "stop_outcomes",
        lambda *a, **k: pytest.fail("unfrozen source evaluated"),
    )
    rejected = experiment.native_research(tmp_path, "2026-10-08")
    assert rejected["status"] == "source_gap" and rejected["selected_cells"] == {}
    assert rejected["blocker"] == "holding_vote_frozen_contract_invalid"
