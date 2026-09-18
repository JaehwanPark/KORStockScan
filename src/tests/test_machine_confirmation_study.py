from copy import deepcopy
from datetime import date
import json

import pytest

from src.tests.test_machine_entry_timing_tuning import _entry_row
from src.engine.monitoring.machine_entry_confirmation_study import (
    build_study,
    _decisions,
)
from src.engine.automation.machine_entry_timing_tuning import (
    _dynamic_baseline_observation,
    _study_economic_observer,
    build_applied_policy,
    write_outputs,
)
from src.trading.config.machine_entry_timing_policy import load_applied_policy
from src.trading.market.micro_confirmation import evaluate_dynamic_micro_confirmation


def _immediate(day, index=1):
    row = _entry_row(day, index)
    feature = row["entry_confirmation_checkpoint_ask_depletion"]["checkpoint_reports"][
        "0"
    ]["horizons"][0]
    feature["aggressive_buy_trade_backed_ratio"] = 0.8
    prior = row["dynamic_confirmation_source_only_replay"]
    point = {
        **prior["checkpoint_decisions"][0],
        "aggressive_buy_trade_backed_ratio": 0.8,
    }
    replay = evaluate_dynamic_micro_confirmation({0: point})
    replay["signal_binding"] = prior["signal_binding"]
    row["dynamic_confirmation_source_only_replay"] = replay
    return row


def test_actual_immediate_control_does_not_require_hypothetical_first_hit():
    day = date(2026, 8, 27)
    row = _immediate(day)
    row.pop("dynamic_confirmation_first_hit_outcomes")
    result = _dynamic_baseline_observation(source_date=day, row=row)
    assert result is not None
    assert result["first_hit_label_quality"] == "unavailable_or_invalid"
    assert result["counterfactual_first_hit_state"] is None
    assert result["candidate_net_pct"] == result["baseline_net_pct"]
    row["owner_outcome"]["cost_aware_net_return_pct"] = None
    assert _dynamic_baseline_observation(source_date=day, row=row) is None


def test_delayed_counterfactual_still_requires_executable_label():
    day = date(2026, 8, 27)
    row = _entry_row(day, 1)
    assert _dynamic_baseline_observation(source_date=day, row=row) is not None
    row.pop("dynamic_confirmation_first_hit_outcomes")
    assert _dynamic_baseline_observation(source_date=day, row=row) is None


def test_four_arm_research_pairs_same_population_and_keeps_holdout_separate():
    rows = [
        (day, _immediate(day, i))
        for i, day in enumerate((date(2026, 8, 26), date(2026, 8, 27)))
    ]
    result = build_study(cohort_rows=rows, economic_observer=_study_economic_observer)
    assert result["common_paired_count"] == 2
    assert result["holdout_date"] == "2026-08-27"
    assert result["runtime_effect"] is False
    assert result["allowed_runtime_apply"] is False
    for arm in result["arms"].values():
        assert arm["all"]["paired_count"] == 2
        assert arm["training"]["paired_count"] == arm["holdout"]["paired_count"] == 1
        assert arm["all"]["modeled_profit_uplift_krw"] == 0
        assert arm["all"]["net_ev_pct"] > 0


def test_missing_or_partial_outcomes_are_census_not_zero_profit():
    day = date(2026, 8, 27)
    row = _immediate(day)
    row["owner_outcome"]["quantity"] = 5
    unfilled = _immediate(day, 2)
    unfilled["owner_outcome"] = {}
    unsubmitted = _immediate(day, 3)
    unsubmitted["actual_order_submitted"] = False
    result = build_study(
        cohort_rows=[(day, row), (day, unfilled), (day, unsubmitted)],
        economic_observer=_study_economic_observer,
    )
    assert result["common_paired_count"] == 0
    assert sum(result["outcome_census"].values()) == 3
    for arm in result["arms"].values():
        assert arm["all"]["net_ev_pct"] is None
        assert arm["all"]["modeled_net_profit_krw"] is None


def test_causal_decision_is_independent_of_future_outcome_label():
    day = date(2026, 8, 27)
    row = _immediate(day)
    before = _decisions(row)
    row["dynamic_confirmation_first_hit_outcomes"] = {"fake_future": "adverse"}
    row["owner_outcome"]["cost_aware_net_return_pct"] = -999
    assert _decisions(row) == before


def test_fixed_price_refill_changes_flow_arms_but_not_bid_only():
    row = _immediate(date(2026, 8, 27))
    row["entry_confirmation_checkpoint_ask_depletion"]["checkpoint_reports"]["0"][
        "horizons"
    ][0]["refill_ratio"] = 1.0
    decisions = _decisions(row)
    assert decisions["baseline"]["terminal_action"] == "ENTER"
    assert decisions["bid_rebound"]["terminal_action"] == "ENTER"
    assert decisions["depletion_flow"]["terminal_action"] == "REJECT"
    assert decisions["combined"]["terminal_action"] == "REJECT"


def test_policy_consumes_frozen_source_after_canonical_report_refresh(tmp_path):
    report = {
        "schema": "machine_entry_timing_tuning_report_v3",
        "target_date": "2026-09-08",
        "effective_date": "2026-09-09",
        "clean_tuning_baseline_date": "2026-06-05",
        "target_source_ready": True,
        "decision": "baseline_immediate_entry_carry_forward",
        "runtime_winner": None,
        "winner": None,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "sample_floor_assessment": {},
        "per_signal_dynamic_confirmation_source_only": {},
    }
    report_dir = tmp_path / "report"
    policy_dir = tmp_path / "policy"
    canonical = report_dir / "machine_entry_timing_tuning_2026-09-08.json"
    applied = build_applied_policy(report, source_report_path=canonical)
    _, _, policy_path = write_outputs(
        report, applied, output_dir=report_dir, policy_dir=policy_dir
    )

    def load():
        return load_applied_policy(
            target_date=date(2026, 9, 9),
            policy_dir=policy_dir,
            source_report_dir=report_dir,
        )

    assert load()[1] == "ready"
    changed = {**report, "diagnostic_refresh": True}
    write_outputs(
        changed,
        build_applied_policy(changed, source_report_path=canonical),
        output_dir=report_dir,
        policy_dir=policy_dir,
        publish_policy=False,
    )
    assert load()[1] == "ready"
    frozen = json.loads(policy_path.read_text())["source_evidence_snapshot"]
    canonical.write_text(
        json.dumps({**changed, "same_stage_owner_guard": {"mutation_present": True}})
    )
    loaded, reason = load()
    assert reason == "ready"
    assert loaded["scopes"] == {}
    canonical.write_text(json.dumps(changed))
    from pathlib import Path

    Path(frozen).write_text(json.dumps(changed))
    assert load()[0] is None


def test_empty_or_duplicate_study_cannot_manufacture_economics():
    day = date(2026, 8, 27)
    row = _immediate(day)
    for rows in ([], [(day, row), (day, deepcopy(row))]):
        result = build_study(
            cohort_rows=rows, economic_observer=_study_economic_observer
        )
        assert result["common_paired_count"] == 0
        assert result["arms"]["combined"]["all"]["net_ev_pct"] is None


def test_census_separates_observed_unfilled_held_and_unknown():
    day = date(2026, 8, 27)
    rows = []
    for index, outcome in enumerate(
        (
            {
                "realized": False,
                "purchased_quantity": 0,
                "entry_fill_status": "unfilled",
            },
            {
                "realized": False,
                "purchased_quantity": 10,
                "right_censored_residual_quantity": 10,
            },
            {
                "realized": False,
                "purchased_quantity": 5,
                "right_censored_residual_quantity": 5,
            },
            {"realized": False, "quantity": 10},
            {},
        )
    ):
        row = _immediate(day, index)
        row["owner_outcome"] = outcome
        rows.append((day, row))
    result = build_study(cohort_rows=rows, economic_observer=_study_economic_observer)
    assert result["common_paired_count"] == 0
    assert result["outcome_census"] == {
        "submitted_unfilled": 1,
        "held_full_entry_fill": 1,
        "held_partial_fill_or_partial_exit": 1,
        "filled_terminal_unknown": 1,
        "submitted_fill_and_terminal_unknown": 1,
    }


def test_completed_count_alone_does_not_claim_all_sample_floors_met():
    from src.engine.automation.machine_entry_timing_tuning import (
        _cohort_sample_floor_assessment,
    )

    day = date(2026, 8, 27)
    rows = [(day, _immediate(day, i)) for i in range(8)]
    result = _cohort_sample_floor_assessment(
        cohort_key=("episode", "test", "005930", "KRX_REGULAR", "ENTRY_READY"),
        cohort_rows=rows,
        alternatives=[],
        source_report_dates={day},
        dynamic_evaluation={
            "completed_outcome_count": 8,
            "unique_decision_lifecycles": 8,
            "observed_trading_days": 1,
        },
    )
    assert result["state"] == "natural_sample_wait"
    assert result["remaining_completed_outcome_count"] == 0
    assert result["projected_additional_trading_days_at_observed_yield"] == 4


def _native_operating_source(day, *, price=80000, target_ticks=3):
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        record_native_source,
        project_native_operating_path,
        _seal,
    )
    from src.tests.test_machine_microstructure_attribution import _depth_row
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy

    start = datetime.fromisoformat(f"{day}T13:15:00+09:00")
    policy = MiddayOneSharePolicy(target_ticks=target_ticks)
    state = dict(
        trade_date=day,
        timing_native_live_eligible=True,
        signal_bar=(start - timedelta(minutes=1)).isoformat(),
        signal_features=dict(
            signal_bar=(start - timedelta(minutes=1)).isoformat(),
            signal_decision_at=start.isoformat(),
            entry_valid_completed_bars=5,
            new_entry_quantity_receipt=__import__(
                "src.trading.order.episode_quantity",
                fromlist=["new_entry_quantity_receipt"],
            ).new_entry_quantity_receipt(start),
        ),
        legs=[
            dict(
                leg_id=str(i),
                route="SOR",
                quantity=10,
                entry_price=price - i * 100,
                buy_order_no="",
                buy_filled_qty=0,
            )
            for i in range(2)
        ],
    )
    record_native_source(
        state,
        policy,
        owner="episode",
        scope_id="midday",
        now=start,
        action="two_leg_entry_armed",
        fields={},
    )
    record_native_source(
        state,
        policy,
        owner="episode",
        scope_id="midday",
        now=start,
        action="buy_submitted",
        fields={"leg_id": "0"},
    )
    contract = state["signal_features"]["timing_operating_contract"]
    assert contract.get("status") != "source_gap", contract
    rows = []
    for i in range(9):
        raw = _depth_row(
            "005930",
            (start + timedelta(seconds=i)).isoformat(),
            venue="SOR",
            session="SOR_REGULAR",
        )
        raw.update(source_sequence=i + 1, series_sequence=i + 1)
        ask = price - 100 if i < 5 else price + 300
        bid = ask - 100 if i < 5 else price + 200
        raw.update(
            best_bid=bid,
            best_ask=ask,
            bid_levels=[[1, bid, 1000]],
            ask_levels=[[1, ask, 800]],
        )
        raw["route_depth_totals"].update(
            KRX={"bid": 1000, "ask": 800}, NXT={"bid": 0, "ask": 0}
        )
        rows.append(raw)
    source = project_native_operating_path(
        contract, rows, state["signal_features"]["timing_operating_native_state"]
    )
    model = _seal(
        dict(
            contract="native_marketable_depth_then_target_v1",
            submit_latency_ms=0,
            target_ack_latency_ms=0,
            target_touch_latency_ms=0,
            maximum_depth_gap_ms=1000,
            depth_participation=1.0,
        )
    )
    decision = dict(
        terminal_action="ENTER", selected_delay_sec=0, source_quality_status="eligible"
    )
    return state, source, model, decision


def test_operating_native_producer_projection_limit_legs_cost_and_pending():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )

    state, source, model, decision = _native_operating_source("2026-09-01")
    result = replay_operating_plan(source, decision, model)
    assert result["status"] == "completed", result
    assert (
        result["modeled_filled_qty"] == 20 and result["actual_broker_profit"] is False
    )
    assert (
        result["net_pnl_krw"]
        == result["sell_notional_krw"] * (1 - source["contract"]["cost_rate"])
        - result["buy_notional_krw"]
    )
    assert result["capital_krw_minutes"] > 0 and result["net_ev_pct"] > 0
    short = _seal(
        {k: v for k, v in source.items() if k != "sha256"}
        | {"points": source["points"][:4]}
    )
    from src.engine.monitoring.policy_research_economics import digest

    short["guard_path"] = _seal(
        {k: v for k, v in short["guard_path"].items() if k != "sha256"}
        | {"path_sha256": digest(short["points"])}
    )
    short = _seal({k: v for k, v in short.items() if k != "sha256"})
    pending = replay_operating_plan(short, decision, model)
    assert pending["status"] == "pending" and pending["net_pnl_krw"] is None


def test_operating_projection_never_borrows_sell_or_assumes_guard():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )

    _, source, model, decision = _native_operating_source("2026-09-01")
    missing = _seal(
        {k: v for k, v in source.items() if k != "sha256"} | {"guard_path": None}
    )
    assert (
        replay_operating_plan(missing, decision, model)["blocker"]
        == "native_guard_path_missing_or_unbound"
    )
    broken = deepcopy(source)
    broken["points"][2]["sequence"] = 1
    broken = _seal({k: v for k, v in broken.items() if k != "sha256"})
    assert replay_operating_plan(broken, decision, model)["net_pnl_krw"] is None
    rejected = replay_operating_plan(
        source, dict(decision, terminal_action="REJECT", selected_delay_sec=None), model
    )
    assert rejected["status"] == "completed" and rejected["capital_krw_minutes"] == 0
    assert rejected["net_pnl_krw"] == 0 and rejected["actual_broker_profit"] is False


def _native_terminal_case(day, *, cheaper_after_signal=False, return_native=False):
    """Controlled native writer + canonical projection, not natural profits."""
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        record_native_source,
        project_native_operating_path,
        native_parent_anchor,
        _seal,
    )
    from src.trading.order.adaptive_exit.source import record_first_fill_observation
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy
    from src.engine.monitoring.machine_microstructure_attribution import (
        _entry_checkpoint_ask_depletion_feature,
    )
    from src.tests.test_machine_microstructure_attribution import _depth_row, _micro_row

    state, source, _, _ = _native_operating_source(day)
    start = datetime.fromisoformat(source["contract"]["decision_at"])
    contract = source["contract"]
    policy = MiddayOneSharePolicy(target_ticks=3)
    for leg in state["legs"]:
        leg.update(
            buy_order_no="controlled-buy-" + leg["leg_id"],
            target_order_no="controlled-target-" + leg["leg_id"],
            buy_owner_registry_intent_id="controlled-buy-intent-" + leg["leg_id"],
            target_owner_registry_intent_id="controlled-target-intent-" + leg["leg_id"],
            buy_filled_qty=10,
            target_filled_qty=10,
            fill_price=79900,
            target_fill_price=80200,
            target_filled_at=(start + timedelta(seconds=5)).isoformat(),
        )
        record_first_fill_observation(
            leg, previous_filled_qty=0, filled_qty=10, observed_at=start.isoformat()
        )
        for action in ("buy_submitted", "target_submitted"):
            record_native_source(
                state,
                policy,
                owner="episode",
                scope_id="midday",
                now=start,
                action=action,
                fields={"leg_id": leg["leg_id"]},
            )
    record_native_source(
        state,
        policy,
        owner="episode",
        scope_id="midday",
        now=start + timedelta(seconds=8),
        action="target_filled",
        fields={"leg_id": "1"},
    )
    depths = []
    trades = []
    for i in range(-10, 81):
        at = start + timedelta(milliseconds=i * 100)
        ask = (
            75000 if cheaper_after_signal and 1 < i < 50 else 79900 if i < 50 else 80300
        )
        bid = ask - 100 if i < 50 else 80200
        raw = _depth_row("005930", at.isoformat(), venue="SOR", session="SOR_REGULAR")
        # Depletion on one fixed price, with observed trade backing.
        quantity = 10000 - (i + 10) * 50
        raw.update(
            source_sequence=i + 11,
            series_sequence=i + 11,
            sequence_epoch=1,
            best_bid=bid,
            best_ask=ask,
            best_ask_qty=quantity,
            ask_depth=quantity,
            bid_levels=[[1, bid, 1000]],
            ask_levels=[[1, ask, quantity]],
        )
        raw["route_depth_totals"].update(
            combined={"bid": 1000, "ask": quantity},
            KRX={"bid": 1000, "ask": quantity},
            NXT={"bid": 0, "ask": 0},
        )
        depths.append(raw)
        trade = _micro_row(
            "005930", at.isoformat(), ask, venue="SOR", session="SOR_REGULAR"
        )
        trade.update(
            item="005930_AL",
            source_sequence=i + 11,
            series_sequence=i + 11,
            aggressor_side="SELL" if i <= 0 else "BUY",
            trade_qty=10000 if i == 1 else 50,
        )
        trades.append(trade)
    native = state["signal_features"]["timing_operating_native_state"]
    if (
        contract["selected_programs"]["status"]
        == "native_target_with_selected_programs"
    ):
        from types import SimpleNamespace
        from src.engine.monitoring.machine_entry_confirmation_study import (
            record_operating_owner_tick,
        )

        state["timing_operating_opportunities"] = {
            "midday:"
            + contract["signal_bar"]: dict(contract=contract, native_state=native)
        }
        original_owner = SimpleNamespace(
            policy=policy, _state=state, profit_exit_lock_held=lambda: False
        )
        for raw in depths:
            if raw["local_receive_timestamp"] >= start.isoformat():
                record_operating_owner_tick(
                    original_owner,
                    datetime.fromisoformat(raw["local_receive_timestamp"]),
                )
    source = project_native_operating_path(
        contract,
        [r for r in depths if r["local_receive_timestamp"] >= start.isoformat()],
        native,
        market_rows=trades,
    )
    row = native_parent_anchor(
        dict(
            contract=contract,
            native_state=state["signal_features"]["timing_operating_native_state"],
            actual_order_submitted=True,
        )
    )
    row["entry_timing_scope_id"] = "midday"
    row["machine_operating_source"] = source
    row["entry_confirmation_checkpoint_ask_depletion"] = dict(
        schema="machine_entry_confirmation_checkpoint_ask_depletion_v1",
        checkpoint_reports={
            str(s): _entry_checkpoint_ask_depletion_feature(
                row,
                {"raw_depth_rows": depths, "raw_market_rows": trades},
                checkpoint_sec=s,
                source_complete=True,
            )
            for s in (0, 1, 3, 5)
        },
        causal_past_only=True,
        future_outcome_input_used=False,
        runtime_effect=False,
        trading_runtime_effect=False,
        trading_decision_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    return (
        (source, _decisions(row), row, state)
        if return_native
        else (source, _decisions(row), row)
    )


def test_native_source_model_holdouts_comparison_and_no_edge():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        operating_comparison,
    )
    from src.tests.test_machine_entry_timing_tuning import _trading_dates

    days = _trading_dates(date(2026, 8, 27), 28)
    cases = [_native_terminal_case(str(d))[:2] for d in days]
    result = operating_comparison(cases, target_date=days[-1])
    assert result["model_validation"]["status"] == "validated", result
    assert result["status"] == "valid_no_edge", result
    assert result["candidate"] is None and result["primary_ev_pct"] > 0
    assert result["actual_profit"] is None


def test_semantic_policy_scope_does_not_split_on_dated_receipt_hash():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        operating_scope,
        _seal,
    )

    _, source, _, _ = _native_operating_source("2026-08-27")
    changed = deepcopy(source["contract"])
    changed["native_policy"]["runtime_policy_hash"] = "different-dated-receipt"
    changed["native_policy"]["runtime_policy_source"] = "different-dated-file"
    changed["native_policy_sha256"] = "original_identity_still_changes"
    assert operating_scope(changed) == operating_scope(source["contract"])
    changed["native_policy"]["target_ticks"] = 2
    assert operating_scope(changed) != operating_scope(source["contract"])


@pytest.mark.parametrize("supplements", [False, True])
def test_native_producer_to_holdouts_selection_dated_reader_and_scope_fallback(
    tmp_path,
    monkeypatch,
    supplements,
):
    if supplements:
        _pin_supplements(tmp_path, monkeypatch)
    from src.tests.test_machine_entry_timing_tuning import _trading_dates
    from src.engine.automation.machine_entry_timing_tuning import build_report
    from src.trading.config.machine_entry_timing_policy import (
        resolve_entry_confirmation_policy,
        validate_applied_policy,
    )
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy
    from src.engine.monitoring.machine_entry_confirmation_study import (
        validate_operating_selection,
        _seal,
    )

    days = _trading_dates(date(2026, 8, 27), 28)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for i, day in enumerate(days):
        _, _, row = _native_terminal_case(str(day), cheaper_after_signal=i >= 20)
        payload = dict(
            schema="machine_microstructure_attribution_v1",
            target_date=str(day),
            clean_tuning_baseline_date="2026-06-05",
            clean_baseline_allowed=True,
            authority=dict(
                runtime_effect=False,
                allowed_runtime_apply=False,
                actual_order_submitted=False,
                broker_order_forbidden=True,
            ),
            micro_entry_confirmation={"entry_anchors": [row]},
        )
        (source_dir / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps(payload)
        )
    report = build_report(
        target_date=days[-1],
        source_dir=source_dir,
        low_price_candidate_dir=tmp_path / "lp",
        samsung_candidate_dir=tmp_path / "samsung",
        widget_policy_dir=tmp_path / "widget",
    )
    assert report["runtime_winner"] is not None, report["cohorts"]
    selected = report["runtime_winner"]["selected"]
    assert selected["feature_arm"] == "depletion_flow"
    proof = selected["operating_economics"]
    assert proof["status"] == "candidate_ready" and proof["actual_profit"] is None
    assert (
        max(proof["model_validation"]["model_holdout_dates"])
        < min(proof["candidate_calibration_dates"])
        < proof["candidate_holdout_date"]
    )
    report_dir = tmp_path / "report"
    report_dir.mkdir()
    policy_dir = tmp_path / "policy"
    report_path = report_dir / f"machine_entry_timing_tuning_{days[-1]}.json"
    applied = build_applied_policy(report, source_report_path=report_path)
    write_outputs(report, applied, output_dir=report_dir, policy_dir=policy_dir)
    target = date.fromisoformat(report["effective_date"])
    resolved = resolve_entry_confirmation_policy(
        target_date=target,
        owner="episode",
        scope_id="midday",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="UNSPECIFIED",
        native_policy=MiddayOneSharePolicy(target_ticks=3),
        approved_leg_quantity=10,
        policy_dir=policy_dir,
        source_report_dir=report_dir,
    )
    assert resolved["mode"] == "per_signal_dynamic_0_1_3_5", resolved
    assert resolved["provenance"]["confirmation_feature_arm"] == "depletion_flow"
    wrong = resolve_entry_confirmation_policy(
        target_date=target,
        owner="episode",
        scope_id="midday",
        symbol="005930",
        session="KRX_REGULAR",
        entry_state="UNSPECIFIED",
        native_policy=MiddayOneSharePolicy(target_ticks=2),
        approved_leg_quantity=10,
        policy_dir=policy_dir,
        source_report_dir=report_dir,
    )
    assert (
        wrong["mode"] == "baseline_immediate"
        and wrong["provenance"]["status"] == "operating_runtime_scope_changed"
    )
    bad = deepcopy(proof)
    bad["model_validation"]["model_holdout_dates"] = bad["candidate_calibration_dates"][
        :1
    ]
    bad["model_validation"] = _seal(bad["model_validation"])
    bad = _seal(bad)
    assert not validate_operating_selection(bad, arm="depletion_flow")
    assert validate_applied_policy(applied, target_date=date(2026, 8, 31))[0] is False


def test_native_gap_preserves_parent_scope_denominator_and_optional_telemetry():
    from datetime import datetime
    from src.engine.monitoring.machine_entry_confirmation_study import (
        capture_episode_opportunity,
        native_parent_anchor,
        operating_cases,
        operating_comparison,
        instrumentation_call,
    )
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy

    now = datetime.fromisoformat("2026-09-18T13:15:00+09:00")
    state = {"trade_date": "2026-09-18"}
    capture_episode_opportunity(
        state,
        MiddayOneSharePolicy(),
        owner="episode",
        scope_id="midday",
        now=now,
        signal_bar="2026-09-18T13:14:00+09:00",
        plans=[{"leg_id": "one", "route": "SOR", "entry_price": 80000}],
        quantity=10,
        quantity_receipt={},
        live_eligible=True,
    )
    parent = native_parent_anchor(
        next(iter(state["timing_operating_opportunities"].values()))
    )
    assert (
        parent["entry_timing_scope_id"] == "midday"
        and parent["native_operating_parent"] is True
    )
    result = operating_comparison(
        operating_cases([(now.date(), parent)]), target_date=now.date()
    )
    assert result["input_count"] == 1 and result["status"] == "source_gap"
    assert (
        result["first_source_gaps"][0]["blocker"]
        == "native_frozen_operating_projection_missing"
    )

    def failing():
        raise ValueError("telemetry_fault")

    assert instrumentation_call(state, failing) is None
    assert state["timing_operating_source_gap"] == "ValueError:telemetry_fault"
    assert "orders" not in state


def _widget_native_case(*, with_adds=False):
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        capture_widget_opportunity,
        record_widget_scale_source,
        record_widget_native,
        project_native_operating_path,
        _seal,
    )
    from src.trading.widget_auto_trade.engine import SAMSUNG_DAILY_EQUAL_SHARE_POLICY
    from src.tests.test_machine_microstructure_attribution import _depth_row

    start = datetime.fromisoformat("2026-09-01T13:15:00+09:00")
    state = {"entry_signal_id": "root", "orders": []}
    capture_widget_opportunity(
        state,
        symbol="005930",
        scope_id="005930:KRX_REGULAR",
        session="KRX_REGULAR",
        route="KRX",
        source_state="ENTRY_READY",
        signal_id="root",
        reference_price=80000,
        quantity=10,
        execution_policy=SAMSUNG_DAILY_EQUAL_SHARE_POLICY,
        now=start,
        target_bps=50,
    )
    rows = []
    for i in range(9):
        at = start + timedelta(seconds=i)
        price = (
            80000 if not with_adds or i == 0 or i >= 5 else 79400 if i == 1 else 79100
        )
        record_widget_scale_source(
            state,
            now=at,
            current_price=price,
            source_status="PASS",
            permitted=True if with_adds and i in (1, 2) else None,
            stage_index=i if with_adds and i in (1, 2) else 1,
        )
        raw = _depth_row("005930", at.isoformat(), venue="SOR", session="SOR_REGULAR")
        ask = price if i < 5 else 80600
        bid = price - 100 if i < 5 else 80500
        raw.update(
            source_sequence=i + 1,
            series_sequence=i + 1,
            best_bid=bid,
            best_ask=ask,
            bid_levels=[[1, bid, 1000]],
            ask_levels=[[1, ask, 800]],
        )
        raw["route_depth_totals"].update(
            KRX={"bid": 1000, "ask": 800}, NXT={"bid": 0, "ask": 0}
        )
        rows.append(raw)
    root = state["timing_operating_opportunities"]["root"]
    buys = []
    targets = []
    for i in range(3 if with_adds else 1):
        price = [80000, 79400, 79100][i]
        common = dict(
            order_no="buy" + str(i),
            owner_registry_intent_id="intent-buy" + str(i),
            owner_registry_bind_confirmed=True,
            side="BUY",
            signal_id="root" if i == 0 else "root:ADD" + str(i),
            parent_entry_signal_id=None if i == 0 else "root",
            order_role="ENTRY_BUY" if i == 0 else "SCALE_IN_BUY",
            status="FILLED",
            filled_qty=10,
            fill_price=price,
            submitted_at=(start + timedelta(seconds=i)).isoformat(),
            timing_first_fill_observed_at=(start + timedelta(seconds=i)).isoformat(),
        )
        buys.append(common)
        final = i == (2 if with_adds else 0)
        target = dict(
            order_no="target" + str(i),
            owner_registry_intent_id="intent-target" + str(i),
            owner_registry_bind_confirmed=True,
            side="SELL",
            signal_id="root:TP" + str(i),
            parent_entry_signal_id="root",
            order_role="TAKE_PROFIT_SELL",
            submitted_at=(start + timedelta(seconds=i)).isoformat(),
            status="FILLED" if final else "CANCELED",
            filled_qty=(i + 1) * 10 if final else 0,
            fill_price=(79900 if with_adds else 80400) if final else None,
        )
        if final:
            target["timing_terminal_fill_observed_at"] = (
                start + timedelta(seconds=5)
            ).isoformat()
        else:
            target["cancel_attempted_at"] = (
                start + timedelta(seconds=i + 1)
            ).isoformat()
            target["timing_cancel_terminal_observed_at"] = target["cancel_attempted_at"]
        targets.append(target)
    state["orders"] = buys + targets
    record_widget_native(
        state,
        event=dict(
            signal_id="root", event_type="order_submitted", actual_order_submitted=True
        ),
        now=start,
    )
    record_widget_native(
        state, event={"signal_id": "root"}, now=start + timedelta(seconds=8)
    )
    source = project_native_operating_path(root["contract"], rows, root["native_state"])
    model = _seal(
        dict(
            contract="native_marketable_depth_then_target_v1",
            submit_latency_ms=0,
            target_ack_latency_ms=0,
            target_touch_latency_ms=0,
            target_cancel_latency_ms=0,
            maximum_depth_gap_ms=1000,
            depth_participation=1.0,
            scale_check_latency_ms=0,
            maximum_scale_tick_gap_ms=1000,
        )
    )
    return (
        source,
        model,
        dict(
            terminal_action="ENTER",
            selected_delay_sec=0,
            source_quality_status="eligible",
        ),
    )


def test_widget_original_three_leg_plan_no_add_and_adds_native_pooled_target():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        model_witness,
    )

    for adds in (False, True):
        source, model, decision = _widget_native_case(with_adds=adds)
        result = replay_operating_plan(source, decision, model)
        assert result["status"] == "completed", result
        assert source["contract"]["total_quantity"] == 30
        assert result["modeled_filled_qty"] == (30 if adds else 10)
        assert result["net_pnl_krw"] == source["actual"]["net_pnl_krw"]
        witness = model_witness(source, result)
        assert (
            witness is not None
            and witness["quantity_error"] == 0
            and witness["net_error_budget_pct"] == 0
        )


def test_widget_missing_add_guard_cancel_or_tick_coverage_is_not_zero_profit():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )

    source, model, decision = _widget_native_case(with_adds=True)
    missing = _seal(model | {"target_cancel_latency_ms": None})
    assert (
        replay_operating_plan(source, decision, missing)["blocker"]
        == "independent_widget_target_cancel_model_missing"
    )
    source["guard_path"]["scale_ticks"][1]["permitted"] = None
    source["guard_path"] = _seal(source["guard_path"])
    source = _seal(source)
    result = replay_operating_plan(source, decision, model)
    assert result["status"] == "unsupported_scope" and result["net_pnl_krw"] is None


def test_partial_native_buy_is_not_per_lot_target_or_synthetic_sell():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )
    from src.engine.monitoring.policy_research_economics import digest

    _, source, model, decision = _native_operating_source("2026-09-01")
    source["points"][0]["ask_levels"][0][1] = 5
    source["guard_path"] = _seal(
        source["guard_path"] | {"path_sha256": digest(source["points"])}
    )
    result = replay_operating_plan(_seal(source), decision, model)
    assert result["status"] == "unsupported_scope"
    assert result["net_pnl_krw"] is None and not result["transitions"]


def test_native_unfilled_expiry_is_not_instant_cancel_zero_pnl():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )
    from src.engine.monitoring.policy_research_economics import digest

    _, source, model, decision = _native_operating_source("2026-09-01")
    c = source["contract"]
    c["cancel_at"] = source["points"][2]["at"]
    c = _seal(c)
    for point in source["points"]:
        point["ask_levels"] = [[90000, 800]]
    source["contract"] = c
    source["guard_path"] = _seal(
        source["guard_path"]
        | {"contract_sha256": c["sha256"], "path_sha256": digest(source["points"])}
    )
    result = replay_operating_plan(_seal(source), decision, model)
    assert result["status"] == "unsupported_scope" and result["net_pnl_krw"] is None
    assert (
        result["blocker"]
        == "unfilled_buy_requires_independently_validated_cancel_model"
    )


def _pin_supplements(tmp_path, monkeypatch):
    import hashlib
    from src.tests.test_profit_stagnation_exit import policy
    from src.trading.config import machine_profit_stagnation_policy as profit
    from src.trading.config import machine_target_ratchet_policy as ratchet

    p = policy()
    p.update(
        valid_from="2026-06-05T00:00:00+09:00",
        valid_until="9999-12-31T00:00:00+09:00",
        min_sec=180,
    )
    r = {
        k: p[k]
        for k in (
            "enabled",
            "valid_from",
            "valid_until",
            "owners",
            "round_trip_cost_pct",
            "slippage_bps",
            "cost_source_sha256",
        )
    }
    r.update(family=ratchet.FAMILY, decision_contract="machine_target_pressure_v1")
    for name, module, value in (("profit", profit, p), ("ratchet", ratchet, r)):
        raw = json.dumps(value).encode()
        path = tmp_path / (name + ".json")
        path.write_bytes(raw)
        monkeypatch.setenv(module.PATH_ENV, str(path))
        monkeypatch.setenv(module.HASH_ENV, hashlib.sha256(raw).hexdigest())


def test_active_programme_pins_supported_target_path_and_measured_tick_source(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace
    from datetime import datetime
    from src.engine.monitoring.machine_entry_confirmation_study import (
        record_operating_owner_tick,
        project_native_operating_path,
        replay_operating_plan,
        operating_runtime_matches,
        _seal,
    )
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy

    _pin_supplements(tmp_path, monkeypatch)
    state, source, model, decision = _native_operating_source("2026-09-21")
    c = source["contract"]
    assert c["selected_programs"]["status"] == "native_target_with_selected_programs"
    assert all(
        c["selected_programs"]["programs"][k]["selected"]
        for k in ("profit_stagnation", "target_ratchet")
    )
    native = state["signal_features"]["timing_operating_native_state"]
    state["timing_operating_opportunities"] = {
        "midday:" + c["signal_bar"]: dict(contract=c, native_state=native)
    }
    owner = SimpleNamespace(
        policy=MiddayOneSharePolicy(), _state=state, profit_exit_lock_held=lambda: False
    )
    for point in source["points"]:
        record_operating_owner_tick(owner, datetime.fromisoformat(point["at"]))
    source = _seal(
        source
        | dict(
            guard_path=__import__(
                "src.engine.monitoring.machine_entry_confirmation_study",
                fromlist=["native_guard_projection"],
            ).native_guard_projection(c, source["points"], native_state=native)
        )
    )
    model = _seal(model | dict(maximum_programme_tick_gap_ms=1000))
    result = replay_operating_plan(source, decision, model)
    assert result["status"] == "completed", result
    assert result["net_pnl_krw"] is not None
    assert operating_runtime_matches(
        dict(runtime_scope_contract=c),
        native_policy=MiddayOneSharePolicy(target_ticks=3),
        leg_quantity=10,
    )
    model = _seal(model | dict(maximum_programme_tick_gap_ms=None))
    assert (
        replay_operating_plan(source, decision, model)["blocker"]
        == "native_programme_write_guard_timeline_coverage_gap"
    )


def test_native_admission_time_is_shared_and_never_allows_early_cf_buy():
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )

    _, source, model, decision = _native_operating_source("2026-09-01")
    source["guard_path"] = _seal(
        source["guard_path"]
        | dict(
            entry_admission=dict(
                at=(
                    datetime.fromisoformat(source["contract"]["decision_at"])
                    + timedelta(seconds=3)
                ).isoformat(),
                permitted=True,
            )
        )
    )
    result = replay_operating_plan(_seal(source), decision, model)
    assert result["status"] == "completed"
    assert (
        min(t["at"] for t in result["transitions"] if t["action"] == "buy")
        >= source["guard_path"]["entry_admission"]["at"]
    )
    source["guard_path"] = _seal(
        source["guard_path"]
        | dict(
            entry_admission=dict(at=source["contract"]["decision_at"], permitted=False)
        )
    )
    result = replay_operating_plan(_seal(source), decision, model)
    assert (
        result["net_pnl_krw"] == 0
        and result["reason"] == "shared_native_hard_entry_guard_block"
    )


def test_selected_profit_program_reuses_native_guard_and_requires_measured_action(
    tmp_path, monkeypatch
):
    from datetime import datetime, timedelta
    from types import SimpleNamespace
    from src.tests.test_machine_microstructure_attribution import _depth_row
    from src.engine.monitoring.machine_entry_confirmation_study import (
        _OperatingPrograms,
        record_operating_owner_tick,
        project_native_operating_path,
        _seal,
    )

    _pin_supplements(tmp_path, monkeypatch)
    state, source, model, _ = _native_operating_source("2026-09-21", target_ticks=10)
    c = source["contract"]
    start = datetime.fromisoformat(c["decision_at"])
    native = state["signal_features"]["timing_operating_native_state"]
    state["timing_operating_opportunities"] = {
        "midday:" + c["signal_bar"]: dict(contract=c, native_state=native)
    }
    owner = SimpleNamespace(policy=object(), _state=state)
    monkeypatch.setattr(
        "src.trading.order.profit_stagnation_owners.guard", lambda *a, **k: True
    )
    rows = []
    for i in range(183):
        at = start + timedelta(seconds=i)
        record_operating_owner_tick(owner, at)
        raw = _depth_row("005930", at.isoformat(), venue="SOR", session="SOR_REGULAR")
        raw.update(
            source_sequence=i + 1,
            series_sequence=i + 1,
            best_bid=80500,
            best_ask=80600,
            best_ask_qty=1000,
            ask_depth=1000,
            bid_levels=[[1, 80500, 1000]],
            ask_levels=[[1, 80600, 1000]],
            route_depth_totals={
                "combined": {"bid": 1000, "ask": 1000},
                "KRX": {"bid": 1000, "ask": 1000},
                "NXT": {"bid": 0, "ask": 0},
            },
        )
        rows.append(raw)
    source = project_native_operating_path(c, rows, native)
    assert len(source["points"]) == 183 and not source["projection_errors"], source[
        "projection_errors"
    ]
    model = _seal(model | dict(maximum_programme_tick_gap_ms=1000))
    programs = _OperatingPrograms(source, model)
    with pytest.raises(
        ValueError, match="independent_profit_replace_action_model_witness_missing"
    ):
        for point in source["points"]:
            at = datetime.fromisoformat(point["at"])
            programs.update(at)
            programs.target(
                "leg", at=at, quantity=10, entry=80000, target=81000, route="SOR"
            )
    model = _seal(model | dict(profit_replace_latency_ms=0))
    programs = _OperatingPrograms(source, model)
    target = 81000
    for point in source["points"]:
        at = datetime.fromisoformat(point["at"])
        programs.update(at)
        target = programs.target(
            "leg", at=at, quantity=10, entry=80000, target=target, route="SOR"
        )
        if programs.events:
            break
    assert target == 80500 and programs.events[0]["action"] == "profit_replace"


def test_owner_guard_interval_is_bounded_and_keeps_measured_cadence(monkeypatch):
    from types import SimpleNamespace
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        record_operating_owner_tick,
        programme_clock_parameters,
    )

    state, source, _, _ = _native_operating_source("2026-09-21")
    c = source["contract"]
    native = state["signal_features"]["timing_operating_native_state"]
    state["timing_operating_opportunities"] = {
        "midday:" + c["signal_bar"]: dict(contract=c, native_state=native)
    }
    owner = SimpleNamespace(policy=object(), _state=state)
    flag = [True]
    monkeypatch.setattr(
        "src.trading.order.profit_stagnation_owners.guard", lambda *a, **kw: flag[0]
    )
    start = datetime.fromisoformat(c["decision_at"])
    for i in range(100):
        record_operating_owner_tick(owner, start + timedelta(seconds=i))
    assert len(native["programme_ticks"]) == 1
    assert native["programme_ticks"][0]["sample_count"] == 100
    assert programme_clock_parameters(native)["maximum_programme_tick_gap_ms"] == 1000
    flag[0] = False
    record_operating_owner_tick(owner, start + timedelta(seconds=100))
    assert (
        len(native["programme_ticks"]) == 2
        and native["programme_ticks"][-1]["permitted"] is False
    )


def test_carry_actual_refresh_is_original_root_and_asof_bound_only(tmp_path):
    from datetime import datetime
    from src.engine.monitoring.machine_entry_confirmation_study import (
        refresh_completed_operating_actuals,
        record_native_source,
        _seal,
        applied_operating_performance,
    )
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy

    source, decisions, _, state = _native_terminal_case(
        "2026-09-01", return_native=True
    )
    absent = _seal(source | dict(actual=None, actual_disposition="pending"))
    for leg in state["legs"]:
        leg["target_filled_at"] = "2026-09-02T09:10:00+09:00"
    record_native_source(
        state,
        MiddayOneSharePolicy(target_ticks=3),
        owner="episode",
        scope_id="midday",
        now=datetime.fromisoformat("2026-09-02T09:10:00+09:00"),
        action="target_filled",
        fields={"leg_id": "1"},
    )
    native = state["signal_features"]["timing_operating_native_state"]
    state["timing_operating_opportunities"] = {
        "root": dict(contract=source["contract"], native_state=native)
    }
    (tmp_path / "samsung_midday_one_share_state.json").write_text(json.dumps(state))
    before, errors = refresh_completed_operating_actuals(
        [(absent, decisions)], target_date="2026-09-01", state_dir=tmp_path
    )
    assert before[0][0]["actual"] is None and not errors
    after, errors = refresh_completed_operating_actuals(
        [(absent, decisions)], target_date="2026-09-02", state_dir=tmp_path
    )
    refreshed = after[0][0]
    assert refreshed["actual"]["knowledge_date"] == "2026-09-02" and not errors
    assert (
        refreshed["actual"]["capital_krw_minutes"]
        > source["actual"]["capital_krw_minutes"]
    )
    assert (
        refreshed["points"] == source["points"]
        and refreshed["guard_path"] == source["guard_path"]
    )
    assert refreshed["actual"]["net_pnl_krw"] == source["actual"]["net_pnl_krw"]
    # Duplicate root contributes once, and a different contract cannot use its terminal.
    perf = applied_operating_performance([*after, *after])
    assert len(perf["versions"]) == 1
    assert next(iter(perf["versions"].values()))["cumulative"]["episode_count"] == 1
    wrong = _seal(
        absent | dict(contract=_seal(source["contract"] | dict(target_ticks=2)))
    )
    mismatch, _ = refresh_completed_operating_actuals(
        [(wrong, decisions)], target_date="2026-09-02", state_dir=tmp_path
    )
    assert mismatch[0][0]["actual"] is None


def test_widget_add_guard_cannot_cross_native_stage():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        replay_operating_plan,
        _seal,
    )

    source, model, decision = _widget_native_case(with_adds=True)
    source["guard_path"]["scale_ticks"][1]["stage_index"] = 2
    source["guard_path"] = _seal(source["guard_path"])
    result = replay_operating_plan(_seal(source), decision, model)
    assert (
        result["blocker"] == "changed_widget_add_requires_its_own_native_guard_receipt"
    )
    assert result["net_pnl_krw"] is None


def test_widget_observation_venue_never_substitutes_sor_execution_book():
    from src.engine.monitoring.machine_entry_confirmation_study import (
        project_native_operating_path,
    )

    source, _, _ = _widget_native_case()
    c = source["contract"]
    assert c["market_data_venue"] == "KRX"
    assert c["execution_data_venue"] == "SOR"
    assert all(p["venue"] == "SOR" for p in source["points"])
    krx = [
        dict(r, venue="KRX", session_bucket="KRX_REGULAR")
        for r in source["programme_rows"]
    ]
    missing = project_native_operating_path(c, krx, {})
    assert missing["points"] == []


def test_native_recheck_admission_replaces_earlier_block_only_at_real_buy():
    from datetime import datetime, timedelta
    from src.engine.monitoring.machine_entry_confirmation_study import (
        record_native_source,
    )
    from src.trading.samsung_midday_one_share.policy import MiddayOneSharePolicy

    state, source, _, _ = _native_operating_source("2026-09-01")
    native = state["signal_features"]["timing_operating_native_state"]
    at = datetime.fromisoformat(source["contract"]["decision_at"])
    native["entry_admission"] = dict(at=at.isoformat(), permitted=False)
    record_native_source(
        state,
        MiddayOneSharePolicy(target_ticks=3),
        owner="episode",
        scope_id="midday",
        now=at + timedelta(seconds=2),
        action="buy_submitted",
        fields={"leg_id": "0"},
    )
    assert native["entry_admission"]["permitted"] is True
    assert native["entry_admission"]["at"] == (at + timedelta(seconds=2)).isoformat()


def test_widget_registry_terminal_is_bound_to_own_identity(monkeypatch):
    from types import SimpleNamespace
    from src.engine.monitoring.machine_entry_confirmation_study import (
        project_widget_registry_terminal,
    )

    order = dict(
        order_no="sell",
        order_date="2026-09-21",
        filled_qty=10,
        owner_id="own",
        owner_position_id="root",
        side="SELL",
        owner_registry_intent_id="intent",
    )
    row = dict(
        owner_type="widget_auto_trade",
        owner_id="own",
        position_id="root",
        symbol="005930",
        side="SELL",
        intent_id="intent",
        filled_qty=10,
        fill_amount=805000,
        fill_observed_at_kst="2026-09-21T13:20:00+09:00",
    )
    monkeypatch.setattr(
        "src.engine.monitoring.machine_entry_confirmation_study.bounded_custody_terminal_lookup",
        lambda *a, **k: row,
    )
    copy = dict(order)
    project_widget_registry_terminal(SimpleNamespace(), copy)
    assert copy["fill_price"] == 80500
    assert "fill_price" not in order
    row["position_id"] = "another-root"
    wrong = dict(order)
    project_widget_registry_terminal(SimpleNamespace(), wrong)
    assert "fill_price" not in wrong
