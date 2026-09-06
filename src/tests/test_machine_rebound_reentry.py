from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timedelta
from dataclasses import replace

import pytest

from src.engine.automation import machine_entry_timing_tuning as tuning
from src.engine.monitoring.machine_rebound_reentry_evaluation import (
    AUTHORITY,
    SECTION,
    SOURCE_SCHEMA,
    build_evaluation,
    evaluate_case,
)
from src.engine.monitoring.machine_rebound_reentry_source import (
    load_anchors,
    project_outcome,
)
from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.engine.risk.market_weakness_entry_guard import MarketWeaknessEntryDecision
from src.trading.config.machine_rebound_reentry_policy import (
    digest,
    load_policy,
)
from src.trading.market import machine_rebound_reentry as runtime
from src.trading.market.machine_rebound_reentry import rising_confirmation

SCOPE = {
    "owner": "episode",
    "scope_id": "midday",
    "symbol": "005930",
    "listing_market": "KOSPI",
    "venue": "SOR",
    "session": "SOR_REGULAR",
    "entry_state": "FLAT_NEW_ENTRY",
}
NOW = datetime.fromisoformat("2026-09-04T13:20:00+09:00")


def checkpoint() -> dict:
    return {
        "checkpoint_sec": 0,
        "causal_past_only": True,
        "future_outcome_input_used": False,
        "source_quality_status": "eligible",
        "bbo_observed": True,
        "depth_backed": True,
        "same_sequence_epoch": True,
        "sequence_epoch": 7,
        "best_bid": 60000,
        "best_ask": 60100,
        "best_ask_quantity": 100,
        "depth_received_at_ms": round(NOW.timestamp() * 1000),
        "bid_return_bps": 3.0,
        "bid_return_reference": "causal_pre_signal_best_bid",
        "bid_recovery_from_low_bps": 0.0,
        "bid_recovery_reference": "lowest_observed_checkpoint_bid",
        "spread_bps": 100 / 60000 * 10000,
        "quote_age_ms": 50,
        "modeled_target_price": 60300,
        "net_edge_after_cost_bps": 10.0,
        "owner_price_feasible": True,
        "aggressive_buy_trade_backed_ratio": 0.8,
        "refill_ratio": 0.1,
        "downward_reprice_observed": False,
    }


def frame(now=NOW, *, blocked=True, net=400.0) -> dict:
    contract = {
        "recipe": "regular_two_leg_fixed_tick_no_stop_v1",
        "target_ticks": 2,
        "baseline_confirmation_mode": "immediate_owner_guards",
    }
    return {
        **SCOPE,
        "observed_at": now.isoformat(),
        "trade_date": now.date().isoformat(),
        "source_signal_id": f"signal:{now.isoformat()}",
        "signal_valid_until": (now + timedelta(minutes=3)).isoformat(),
        "owner_signal_valid": True,
        "baseline_blocked": blocked,
        "baseline_confirmation_mode": "immediate_owner_guards",
        "market_fresh": True,
        "market_phase": "active" if blocked else "released",
        "checkpoint": {
            **checkpoint(),
            "depth_received_at_ms": round(now.timestamp() * 1000),
        },
        "source_quality_eligible": True,
        "modeled_owner_exit": {
            "status": "completed_full_position",
            "net_profit_krw": net,
            "actual_order_submitted": False,
        },
        "owner_contract": contract,
        "owner_contract_sha256": digest(contract),
        "legs": [
            {"leg_id": "L1", "price_role": "a", "entry_price": 60200, "quantity": 10},
            {"leg_id": "L2", "price_role": "b", "entry_price": 60100, "quantity": 10},
        ],
        "reference_price": 60100,
        "cost_contract": comparison_cost_contract(now),
        "parent_horizon_end": (now + timedelta(minutes=30)).isoformat(),
    }


def case(now=NOW, index=0) -> dict:
    return {
        **SCOPE,
        "trade_date": now.date().isoformat(),
        "opportunity_id": f"{now.date()}:{index}",
        "basis_notional_krw": 1203000,
        "frames": [
            frame(now, net=400),
            frame(now + timedelta(minutes=1), blocked=False, net=100),
        ],
    }


def sources() -> list[dict]:
    return [
        {
            SOURCE_SCHEMA: {
                "schema": SOURCE_SCHEMA,
                **AUTHORITY,
                "cases": [
                    case(NOW - timedelta(days=offset), index)
                    for offset in range(5)
                    for index in range(2)
                ],
            }
        }
    ]


def test_pair_is_cost_net_increment_not_profit_sum():
    result = evaluate_case(case())
    assert result["status"] == "eligible"
    assert result["delta_ev_pct"] == pytest.approx(300 / 1203000 * 100)
    assert result["actual_order_submitted"] is False
    assert result["recovery_arm_status"] == "equivalent_to_control"


@pytest.mark.parametrize(
    "mutation",
    ["flat", "stale", "future", "negative_edge", "fake_trade", "wrong_epoch"],
)
def test_confirmation_rejects_unsafe_or_non_rising(mutation):
    row = frame()
    edits = {
        "flat": {"bid_return_bps": 0},
        "stale": {"quote_age_ms": 1501},
        "future": {"future_outcome_input_used": True},
        "negative_edge": {"net_edge_after_cost_bps": -1},
        "fake_trade": {"aggressive_buy_trade_backed_ratio": 0},
        "wrong_epoch": {"same_sequence_epoch": False},
    }
    row["checkpoint"].update(edits[mutation])
    assert not rising_confirmation(row)


def test_missing_control_never_becomes_zero():
    data = case()
    data["frames"].pop()
    assert evaluate_case(data)["status"] == "baseline_replay_gap"


def test_expired_candidate_and_ttl_release_do_not_create_alpha():
    data = case()
    data["frames"][0]["signal_valid_until"] = (NOW - timedelta(seconds=1)).isoformat()
    data["frames"][1]["market_fresh"] = False
    result = evaluate_case(data)
    assert result["equivalent_to_control"] is True
    assert result["recovery_arm_status"] != "equivalent_to_control"


def test_first_causal_signal_not_best_future_profit():
    data = case()
    data["frames"].insert(1, frame(NOW + timedelta(seconds=20), net=999999))
    assert evaluate_case(data)["delta_ev_pct"] == pytest.approx(300 / 1203000 * 100)


def test_partial_and_pending_are_not_zero_or_realized():
    for status in ("right_censored", "partial_fill", "owner_exit_replay_gap"):
        data = case()
        data["frames"][0]["modeled_owner_exit"]["status"] = status
        assert evaluate_case(data)["status"] == status


def test_promotion_requires_scope_window_holdout_and_no_conflict():
    result = build_evaluation(
        target_date=NOW.date(), sources=sources(), same_stage_clear=True
    )
    assert result["selected_candidate"] is not None
    assert result["eligible_pair_count"] == 10
    assert result["automatic_preopen"]["per_candidate_user_approval_required"] is False
    assert (
        build_evaluation(
            target_date=NOW.date(), sources=sources(), same_stage_clear=False
        )["selected_candidate"]
        is None
    )


def test_duplicate_parent_and_negative_holdout_cannot_promote():
    data = sources()
    data[0][SOURCE_SCHEMA]["cases"].append(deepcopy(data[0][SOURCE_SCHEMA]["cases"][0]))
    result = build_evaluation(
        target_date=NOW.date(), sources=data, same_stage_clear=True
    )
    assert result["gap_counts"]["duplicate_parent_opportunity"] == 2
    data = sources()
    for row in data[0][SOURCE_SCHEMA]["cases"][:2]:
        row["frames"][0]["modeled_owner_exit"]["net_profit_krw"] = -100
    assert (
        build_evaluation(target_date=NOW.date(), sources=data, same_stage_clear=True)[
            "selected_candidate"
        ]
        is None
    )


def test_owner_exit_preserves_target_cost_full_quantity_and_common_horizon():
    row = frame()
    window = {
        "depth_points": [
            {
                "sequence_epoch": 7,
                "timestamp": NOW,
                "best_bid": 60000,
                "best_ask": 60100,
                "best_ask_qty": 100,
            },
            {
                "sequence_epoch": 7,
                "timestamp": NOW + timedelta(seconds=20),
                "best_bid": 60300,
                "best_bid_qty": 20,
            },
        ]
    }
    outcome = project_outcome(row, window, source_ready=True)["modeled_owner_exit"]
    assert outcome["status"] == "completed_full_position"
    assert outcome["net_profit_krw"] == pytest.approx(4000 - 60100 * 20 * 0.0023)
    window["depth_points"][1]["timestamp"] = NOW + timedelta(minutes=31)
    assert (
        project_outcome(row, window, source_ready=True)["modeled_owner_exit"]["status"]
        == "right_censored"
    )
    row["legs"][1]["entry_price"] = 60000
    assert (
        project_outcome(row, window, source_ready=True)["modeled_owner_exit"]["status"]
        == "passive_or_partial_entry_replay_gap"
    )


def test_source_contract_failure_blocks_outcome():
    assert (
        project_outcome(frame(), {}, source_ready=False)["source_quality_eligible"]
        is False
    )


def test_empty_source_has_explicit_census():
    result = build_evaluation(
        target_date=NOW.date(),
        sources=[{SOURCE_SCHEMA: {"schema": SOURCE_SCHEMA, **AUTHORITY, "cases": []}}],
        same_stage_clear=True,
    )
    assert result["status"] == "no_natural_opportunity"
    assert result["selected_candidate"] is None
    assert (
        build_evaluation(target_date=NOW.date(), sources=[{}], same_stage_clear=True)[
            "status"
        ]
        == "source_contract_gap"
    )


def staged(tmp_path, monkeypatch):
    section = build_evaluation(
        target_date=NOW.date(), sources=sources(), same_stage_clear=True
    )
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report = {
        "schema": tuning.REPORT_SCHEMA,
        "target_date": "2026-09-04",
        "effective_date": "2026-09-07",
        "runtime_winner": None,
        SECTION: section,
    }
    (report_dir / "machine_entry_timing_tuning_2026-09-04.json").write_text(
        json.dumps(report)
    )
    monkeypatch.setattr(
        tuning,
        "_source_reports",
        lambda **kw: ([(NOW.date(), tmp_path / "source.json", sources()[0])], []),
    )
    monkeypatch.setattr(
        tuning, "_same_stage_owner_guard", lambda **kw: {"mutation_present": False}
    )
    return report_dir


def test_preopen_applies_without_user_approval_and_runtime_consumes(
    tmp_path, monkeypatch
):
    report_dir = staged(tmp_path, monkeypatch)
    preopen = datetime.fromisoformat("2026-09-07T07:30:00+09:00")
    root = tmp_path / "policy"
    result = tuning.apply_rebound_preopen(
        target_date=preopen.date(),
        now=preopen,
        write=True,
        report_dir=report_dir,
        policy_dir=root,
    )
    assert result["status"] == "applied"
    policy, status = load_policy(
        now=preopen + timedelta(hours=2), scope=SCOPE, root=root
    )
    assert status == "applied_exact_scope" and policy is not None
    assert (
        load_policy(now=preopen + timedelta(days=1), scope=SCOPE, root=root)[0] is None
    )
    assert (
        load_policy(
            now=preopen + timedelta(hours=2), scope={**SCOPE, "venue": "KRX"}, root=root
        )[0]
        is None
    )
    # Ordinary report regeneration cannot invalidate the immutable receipt.
    (report_dir / "machine_entry_timing_tuning_2026-09-04.json").write_text("{}")
    assert (
        load_policy(now=preopen + timedelta(hours=2), scope=SCOPE, root=root)[0]
        is not None
    )
    assert (
        tuning.apply_rebound_preopen(
            target_date=preopen.date(),
            now=preopen,
            write=True,
            report_dir=report_dir,
            policy_dir=root,
        )["status"]
        == "blocked_source_report"
    )
    assert (
        load_policy(now=preopen + timedelta(hours=2), scope=SCOPE, root=root)[0] is None
    )


def test_preopen_rejects_intraday_and_does_not_write(tmp_path, monkeypatch):
    report_dir = staged(tmp_path, monkeypatch)
    root = tmp_path / "policy"
    result = tuning.apply_rebound_preopen(
        target_date=date(2026, 9, 7),
        now=datetime.fromisoformat("2026-09-07T08:00:00+09:00"),
        write=True,
        report_dir=report_dir,
        policy_dir=root,
    )
    assert result["status"] == "blocked_not_exact_preopen"
    assert not root.exists()


def test_preopen_recomputes_modified_sources(tmp_path, monkeypatch):
    report_dir = staged(tmp_path, monkeypatch)
    monkeypatch.setattr(
        tuning,
        "_source_reports",
        lambda **kw: ([(NOW.date(), tmp_path / "source.json", {})], []),
    )
    result = tuning.apply_rebound_preopen(
        target_date=date(2026, 9, 7),
        now=datetime.fromisoformat("2026-09-07T07:00:00+09:00"),
        write=True,
        report_dir=report_dir,
        policy_dir=tmp_path / "policy",
    )
    assert result["status"] == "blocked_source_revalidation"


def test_initial_preopen_does_not_treat_missing_historical_section_as_crash(
    tmp_path, monkeypatch
):
    report_dir = staged(tmp_path, monkeypatch)
    path = report_dir / "machine_entry_timing_tuning_2026-09-04.json"
    report = json.loads(path.read_text())
    report.pop(SECTION)
    path.write_text(json.dumps(report))
    result = tuning.apply_rebound_preopen(
        target_date=date(2026, 9, 7),
        now=datetime.fromisoformat("2026-09-07T07:00:00+09:00"),
        write=True,
        report_dir=report_dir,
        policy_dir=tmp_path / "policy",
    )
    assert result["status"] == "baseline_no_candidate"
    assert result["reason"] == "pre_instrumentation_source_section_unavailable"


def test_recording_is_no_order_and_deduplicates_poll_source_windows(
    tmp_path, monkeypatch
):
    decision = MarketWeaknessEntryDecision(
        True,
        "entry_blocked_market_weakness_active",
        "005930",
        "episode",
        "KOSPI",
        "active",
        ("KOSPI",),
        NOW.date().isoformat(),
        "receipt",
        NOW.isoformat(),
        "loaded",
        "state.json",
        "symbols.json",
        state_fresh=True,
    )
    monkeypatch.setattr(
        runtime,
        "advance_live_dynamic_confirmation",
        lambda **kw: {"checkpoints": {"0": checkpoint()}},
    )
    state = {}
    row = frame()
    args = dict(
        state=state,
        decision=decision,
        scope_id="midday",
        session="SOR_REGULAR",
        source_signal_id="signal",
        signal_valid_until=NOW + timedelta(minutes=3),
        owner_contract=row["owner_contract"],
        legs=row["legs"],
        reference_price=60100,
        route="SOR",
        source_root=tmp_path / "machine_rebound_reentry_observations",
        policy_root=tmp_path / "no_policy",
    )
    for seconds in (0, 2, 4):
        result = runtime.observe_owner_decision(
            now=NOW + timedelta(seconds=seconds), **args
        )
        assert result["allow_market_exception"] is False
    args["decision"] = replace(decision, blocked=False, phase="released")
    runtime.observe_owner_decision(now=NOW + timedelta(seconds=6), **args)
    anchors, source = load_anchors(NOW.date().isoformat(), tmp_path)
    assert source["journal_artifact_count"] == 2
    assert len(source["cases"]) == 1
    assert len(anchors) == 2
    assert all(anchor["actual_order_submitted"] is False for anchor in anchors)


def test_failed_source_write_never_grants_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runtime,
        "write_json_object_generation_safe",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr(
        runtime,
        "advance_live_dynamic_confirmation",
        lambda **kw: {"checkpoints": {"0": checkpoint()}},
    )
    decision = MarketWeaknessEntryDecision(
        True,
        "entry_blocked_market_weakness_active",
        "005930",
        "episode",
        "KOSPI",
        "active",
        ("KOSPI",),
        NOW.date().isoformat(),
        "receipt",
        NOW.isoformat(),
        "loaded",
        "state.json",
        "symbols.json",
        state_fresh=True,
    )
    row = frame()
    result = runtime.observe_owner_decision(
        state={},
        now=NOW,
        decision=decision,
        scope_id="midday",
        session="SOR_REGULAR",
        source_signal_id="signal",
        signal_valid_until=NOW + timedelta(minutes=3),
        owner_contract=row["owner_contract"],
        legs=row["legs"],
        reference_price=60100,
        route="SOR",
        source_root=tmp_path,
    )
    assert result["allow_market_exception"] is False
    assert result["status"].startswith("source_write_failed")


def test_report_only_rejects_production_output(monkeypatch):
    with pytest.raises(SystemExit):
        tuning.main(
            ["--target-date", "2026-09-04", "--report-only-dir", str(tuning.OUTPUT_DIR)]
        )


def test_raw_quote_must_reconcile_with_live_checkpoint():
    row = frame()
    window = {
        "depth_points": [
            {
                "sequence_epoch": 7,
                "timestamp": NOW,
                "best_bid": 60000,
                "best_ask": 60050,
                "best_ask_qty": 100,
            },
            {
                "sequence_epoch": 7,
                "timestamp": NOW + timedelta(seconds=20),
                "best_bid": 60300,
                "best_bid_qty": 20,
            },
        ]
    }
    result = project_outcome(row, window, source_ready=True)
    assert result["source_quality_eligible"] is False
    assert result["modeled_owner_exit"]["status"] == "live_quote_raw_reconciliation_gap"


def test_raw_and_runtime_epoch_namespaces_are_bound_not_equated():
    row = frame()
    window = {
        "depth_points": [
            {
                "sequence_epoch": 1788660100000000000,
                "timestamp": NOW,
                "best_bid": 60000,
                "best_ask": 60100,
                "best_ask_qty": 100,
            },
            {
                "sequence_epoch": 1788660100000000000,
                "timestamp": NOW + timedelta(seconds=20),
                "best_bid": 60300,
                "best_bid_qty": 20,
            },
        ]
    }
    result = project_outcome(row, window, source_ready=True)
    assert result["modeled_owner_exit"]["status"] == "completed_full_position"
    assert result["epoch_binding"]["runtime_transport_epoch"] == 7
    assert result["epoch_binding"]["raw_sequence_epoch"] == 1788660100000000000
    window["depth_points"].append({**window["depth_points"][0], "sequence_epoch": 99})
    assert not project_outcome(row, window, source_ready=True)[
        "source_quality_eligible"
    ]


def test_initial_basis_cannot_be_changed_to_improve_ev():
    data = case()
    data["basis_notional_krw"] /= 10
    assert evaluate_case(data)["status"] == "source_contract_gap"


def test_invalid_candidate_or_corrupt_policy_is_fail_closed(tmp_path, monkeypatch):
    from src.trading.config.machine_rebound_reentry_policy import (
        policy_path,
        valid_candidate,
    )

    candidate = build_evaluation(
        target_date=NOW.date(), sources=sources(), same_stage_clear=True
    )["selected_candidate"]
    assert valid_candidate(candidate)
    for field, value in (
        ("unique_days", 1),
        ("coverage_pct", float("nan")),
        ("owner", "widget"),
        ("source_through_date", "2026-09-03"),
    ):
        assert not valid_candidate({**candidate, field: value})
    invalid_cost = deepcopy(candidate)
    invalid_cost["executable_confirmation"]["cost_contract_sha256"] = "bad"
    assert not valid_candidate(invalid_cost)
    path = policy_path(date(2026, 9, 7), tmp_path)
    path.write_text("[]")
    assert (
        load_policy(
            now=datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            scope=SCOPE,
            root=tmp_path,
        )[0]
        is None
    )


def test_runtime_permit_is_exact_batch_and_never_cancels(tmp_path, monkeypatch):
    row = frame()
    decision = MarketWeaknessEntryDecision(
        True,
        "entry_blocked_market_weakness_active",
        "005930",
        "episode",
        "KOSPI",
        "active",
        ("KOSPI",),
        NOW.date().isoformat(),
        "receipt",
        NOW.isoformat(),
        "loaded",
        "state.json",
        "symbols.json",
        state_fresh=True,
    )
    monkeypatch.setattr(
        runtime,
        "advance_live_dynamic_confirmation",
        lambda **kw: {"checkpoints": {"0": checkpoint()}},
    )
    policy = {
        "policy_hash": "reviewed",
        "candidate": {
            "owner_contract_sha256": digest(row["owner_contract"]),
            "executable_confirmation": {
                "mode": "fresh_rebound_checkpoint0",
                "round_trip_cost_pct": row["cost_contract"]["round_trip_cost_pct"],
                "cost_trade_date": row["cost_contract"]["trade_date"],
                "cost_contract_sha256": row["cost_contract"]["contract_sha256"],
            },
        },
    }
    monkeypatch.setattr(
        runtime, "load_policy", lambda **kw: (policy, "applied_exact_scope")
    )
    state = {}
    permit = runtime.observe_owner_decision(
        state=state,
        now=NOW,
        decision=decision,
        scope_id="midday",
        session="SOR_REGULAR",
        source_signal_id="signal",
        signal_valid_until=NOW + timedelta(minutes=3),
        owner_contract=row["owner_contract"],
        legs=row["legs"],
        reference_price=60100,
        route="SOR",
        source_root=tmp_path,
    )
    assert permit["allow_market_exception"] is True
    assert decision.exact_market_open_buy_cancel_allowed is True
    state["rebound_reentry_permit"] = permit
    state["legs"] = [
        {**leg, "status": "PLANNED", "buy_order_no": "", "position_qty": 0}
        for leg in row["legs"]
    ]
    assert runtime.permit_allows_initial_plan(state=state, decision=decision, now=NOW)
    assert not runtime.permit_allows_initial_plan(
        state=state, decision=decision, now=NOW + timedelta(seconds=2)
    )
    state["legs"][0]["position_qty"] = 1
    assert not runtime.permit_allows_initial_plan(
        state=state, decision=decision, now=NOW
    )


def test_runtime_cost_mismatch_cannot_grant_permit(tmp_path, monkeypatch):
    row = frame()
    decision = MarketWeaknessEntryDecision(
        True,
        "entry_blocked_market_weakness_active",
        "005930",
        "episode",
        "KOSPI",
        "active",
        ("KOSPI",),
        NOW.date().isoformat(),
        "receipt",
        NOW.isoformat(),
        "loaded",
        "state.json",
        "symbols.json",
        state_fresh=True,
    )
    monkeypatch.setattr(
        runtime,
        "advance_live_dynamic_confirmation",
        lambda **kw: {"checkpoints": {"0": checkpoint()}},
    )
    monkeypatch.setattr(
        runtime,
        "load_policy",
        lambda **kw: (
            {
                "policy_hash": "reviewed",
                "candidate": {
                    "owner_contract_sha256": digest(row["owner_contract"]),
                    "executable_confirmation": {
                        "mode": "fresh_rebound_checkpoint0",
                        "round_trip_cost_pct": 0.20,
                        "cost_trade_date": NOW.date().isoformat(),
                        "cost_contract_sha256": "0" * 64,
                    },
                },
            },
            "applied_exact_scope",
        ),
    )
    result = runtime.observe_owner_decision(
        state={},
        now=NOW,
        decision=decision,
        scope_id="midday",
        session="SOR_REGULAR",
        source_signal_id="signal",
        signal_valid_until=NOW + timedelta(minutes=3),
        owner_contract=row["owner_contract"],
        legs=row["legs"],
        reference_price=60100,
        route="SOR",
        source_root=tmp_path,
    )
    assert result["allow_market_exception"] is False
    assert result["status"] == "runtime_cost_contract_mismatch"


def test_terminal_no_entry_proof_closes_zero_control_without_faking_receipt(tmp_path):
    now = NOW.replace(hour=13, minute=30)
    data = case()
    data["frames"].pop()
    history = {
        "opportunity_id": data["opportunity_id"],
        "scope": SCOPE,
        "basis_notional_krw": data["basis_notional_krw"],
        "last_heartbeat_at": (now - timedelta(seconds=2)).isoformat(),
        "scan_last_bar": "13:29:00",
        "trace_complete": True,
        "source_root": str(tmp_path),
    }
    state = {
        "rebound_reentry_observation": history,
        "status": "NO_TRADE",
        "legs": [],
        "attempt_consumed": False,
    }
    assert runtime.observe_owner_terminal(state=state, now=now)
    terminal = json.loads(
        next((tmp_path / now.date().isoformat()).glob("*.json")).read_text()
    )
    assert terminal["no_entry_confirmed"] is True
    data["baseline_no_entry_receipt"] = terminal
    result = evaluate_case(data)
    assert result["status"] == "eligible"
    assert result["control_ev_pct"] == 0
    assert result["delta_ev_pct"] == pytest.approx(
        400 / data["basis_notional_krw"] * 100
    )
    terminal["observed_at"] = (NOW - timedelta(minutes=1)).isoformat()
    assert evaluate_case(data)["status"] == "baseline_replay_gap"


def test_wall_clock_cutoff_alone_cannot_assert_owner_no_entry(tmp_path):
    now = NOW.replace(hour=13, minute=30)
    history = {
        "opportunity_id": "parent",
        "scope": SCOPE,
        "basis_notional_krw": 100,
        "last_heartbeat_at": (now - timedelta(seconds=2)).isoformat(),
        "scan_last_bar": "13:29:00",
        "trace_complete": True,
        "source_root": str(tmp_path),
    }
    state = {"rebound_reentry_observation": history, "status": "READY", "legs": []}
    assert not runtime.observe_owner_terminal(state=state, now=now)
    assert not list(tmp_path.glob("**/*.json"))


@pytest.mark.parametrize("failure", ["gap", "source", "owned"])
def test_terminal_unknown_or_owned_state_is_not_zero_control(tmp_path, failure):
    now = NOW.replace(hour=13, minute=30)
    history = {
        "opportunity_id": "parent",
        "scope": SCOPE,
        "basis_notional_krw": 100,
        "last_heartbeat_at": (
            now - timedelta(seconds=31 if failure == "gap" else 2)
        ).isoformat(),
        "scan_last_bar": "13:29:00",
        "trace_complete": True,
        "source_root": str(tmp_path),
    }
    state = {
        "rebound_reentry_observation": history,
        "status": "NO_TRADE",
        "blocked_reason": "source_unavailable" if failure == "source" else "",
        "legs": [{"status": "POSITION_OPEN"}] if failure == "owned" else [],
    }
    assert runtime.observe_owner_terminal(state=state, now=now)
    terminal = json.loads(
        next((tmp_path / now.date().isoformat()).glob("*.json")).read_text()
    )
    assert terminal["no_entry_confirmed"] is False
