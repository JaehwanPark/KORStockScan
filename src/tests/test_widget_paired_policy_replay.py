from __future__ import annotations

import copy
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring import widget_paired_policy_replay as replay
from src.engine.monitoring.widget_auto_trade_policy_calibration import (
    apply_paired_target_selection,
)

KST = ZoneInfo("Asia/Seoul")
DAY = date(2026, 9, 9)


def parameters():
    return dict(
        leg_quantity_each=10,
        add_trigger_bps_from_initial_fill=[],
        target_bps=100,
        max_completed_entries_per_day=3,
        reentry_cooldown_minutes=5,
        new_entry_cutoff_time="14:30:00",
        force_exit_time=None,
        source_final_exit_action="observe_only_no_forced_sell",
    )


def path(day=DAY, hour=10, *, confirmation=False):
    start = datetime.combine(day, datetime.min.time(), KST).replace(hour=hour)
    rows = []
    for sec in range(0, 1210, 10):
        at = start + timedelta(seconds=sec)
        bid = (
            9990
            if sec < 40
            else (10030 if confirmation else 10060) if sec < 90 else 9900
        )
        ask = 10040 if confirmation and sec >= 30 else 10000
        rows.append(
            dict(
                schema="widget_paired_replay_input_v1",
                symbol="005930",
                venue="KRX",
                session="KRX_REGULAR",
                observed_at=at.isoformat(),
                raw_state="ENTRY_READY" if sec < 80 else "WATCH",
                source_quality_status="PASS",
                signal_contract="test_signal_v1",
                non_confirmation_entry_blocked=False,
                bbo=dict(
                    best_bid=bid,
                    best_ask=max(ask, bid + 10),
                    best_bid_qty=1000,
                    best_ask_qty=1000,
                    received_at=at.isoformat(),
                    source="normalized_bbo",
                ),
            )
        )
    return rows


def study(*, confirmation=False):
    rows = (
        path(date(2026, 9, 8), 10, confirmation=confirmation)
        + path(date(2026, 9, 8), 11, confirmation=confirmation)
        + path(confirmation=confirmation)
    )
    params = parameters()
    if confirmation:
        params["target_bps"] = 30
    return replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=params,
        baseline_confirmations=3 if confirmation else 2,
        axis="confirmations" if confirmation else "target_bps",
        values=(2, 3) if confirmation else (30, 50, 100),
        target_date=DAY,
        source_audit={"source_hashes": {"fixture": "fixture"}},
    )


def test_small_cost_positive_target_beats_large_unresolved_target_without_zero_pnl():
    report = study()
    result = replay.select_candidate(report, previous_value=100)
    assert result["candidate_ready"] is True
    assert result["selected_value"] == 50
    assert report["actual_broker_execution_quality"] is False
    assert report["horizon_close_is_evaluation_only"] is True
    pair = report["candidates"][0]["pairs"][0]["models"]["base"]
    assert pair["baseline"]["net_pnl_krw"] < 0
    assert pair["candidate"]["net_return_pct"] == pytest.approx(0.07)
    assert pair["baseline"]["close_reason"] == "common_horizon_evaluation_only"
    assert pair["candidate"]["capital_seconds"] < pair["baseline"]["capital_seconds"]


def test_confirmation_extra_ten_seconds_changes_cost_ev_on_same_opportunity():
    report = study(confirmation=True)
    result = replay.select_candidate(report, previous_value=3)
    assert result["candidate_ready"] is True
    assert result["selected_value"] == 2
    pair = report["candidates"][0]["pairs"][0]["models"]["base"]
    assert (
        datetime.fromisoformat(pair["baseline"]["entry_at"])
        - datetime.fromisoformat(pair["candidate"]["entry_at"])
    ).total_seconds() == 10


def test_integrated_aftermarket_is_source_only_without_cost_or_candidate():
    rows = path()
    for row in rows:
        row.update(
            venue="UNKNOWN",
            session="KRX_NXT_AFTERMARKET",
            market_data_route="krx_nxt_integrated",
            actual_execution_venue="UNKNOWN",
        )

    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_NXT_AFTERMARKET",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(30, 100),
        target_date=DAY,
        source_audit={},
    )

    assert report["status"] == "dual_aftermarket_observe_only"
    assert report["cost_status"] == "not_applicable_source_only"
    assert report["candidates"] == []
    assert report["source_only_row_count"] == len(rows)
    assert replay.select_candidate(report, previous_value=100)["candidate_ready"] is False


@pytest.mark.parametrize(
    "kind",
    [
        "stale",
        "cross_venue",
        "regression",
        "conflict",
        "gap",
        "partial",
        "malformed_state",
    ],
)
def test_bad_paths_are_excluded_not_zero_return(kind):
    rows = path()
    if kind == "stale":
        rows[2]["bbo"]["received_at"] = rows[0]["observed_at"].replace(
            "10:00:00", "09:59:00"
        )
    elif kind == "cross_venue":
        rows[2]["venue"] = "NXT"
    elif kind == "regression":
        rows[2]["bbo"]["received_at"] = rows[0]["observed_at"]
    elif kind == "conflict":
        rows[2]["source_conflict"] = True
    elif kind == "gap":
        del rows[2:6]
    elif kind == "malformed_state":
        rows[2]["raw_state"] = []
    else:
        rows[2]["bbo"]["best_ask_qty"] = 1
    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(30, 100),
        target_date=DAY,
        source_audit={},
    )
    assert not replay.select_candidate(report, previous_value=100)["candidate_ready"]
    if kind == "partial":
        outcome = report["candidates"][0]["pairs"][0]["models"]["base"]["candidate"]
        assert outcome["net_pnl_krw"] is None
        assert (
            replay.select_candidate(report, previous_value=100)["evidence_state"]
            == "paired_outcome_incomplete"
        )
    else:
        assert report["path_source_gaps"]


def profitable_paths(*, prefix_only=False):
    rows = []
    for day, hour in ((date(2026, 9, 8), 10), (date(2026, 9, 8), 11), (DAY, 10)):
        sample = path(day, hour)
        for row in sample:
            if row["bbo"]["best_bid"] >= 10060:
                row["bbo"].update(best_bid=10090, best_ask=10100)
        rows.extend(sample[:9] if prefix_only else sample)
    return rows


@pytest.mark.parametrize("prefix_only", [False, True])
def test_more_profit_at_same_frequency_is_not_rejected_by_small_profit_upper_bin(
    prefix_only,
):
    params = parameters()
    params["target_bps"] = 50
    report = replay.build_study(
        profitable_paths(prefix_only=prefix_only),
        symbol="005930",
        session="KRX_REGULAR",
        parameters=params,
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 80),
        target_date=DAY,
        source_audit={},
    )
    selection = replay.select_candidate(report, previous_value=50)
    assert selection["candidate_ready"] is True
    assert selection["selected_value"] == 80
    metrics = selection["diagnostics"][-1]["windows"]["base"]["calibration"]
    assert metrics["baseline"]["quick_small_profit_count"] == 2
    assert metrics["candidate"]["quick_small_profit_count"] == 0
    assert metrics["candidate"]["profitable_close_within_180s_count"] == 2
    assert bool(report["path_source_gaps"]) is prefix_only
    assert report["path_exclusions"] == []


def test_one_unresolved_arm_cannot_be_promoted_from_an_early_winner():
    report = replay.build_study(
        profitable_paths(prefix_only=True),
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 100),
        target_date=DAY,
        source_audit={},
    )
    selection = replay.select_candidate(report, previous_value=100)
    assert selection["candidate_ready"] is False
    pair = report["candidates"][0]["pairs"][0]["models"]["base"]
    assert pair["candidate"]["status"] == "completed_cf"
    assert pair["baseline"]["status"] == "right_censored"
    assert pair["baseline"]["net_pnl_krw"] is None


@pytest.mark.parametrize("received_index", [5, 6])
def test_late_conflicting_quote_invalidates_resolved_prefix(received_index):
    rows = profitable_paths(prefix_only=True)
    rows[7]["bbo"]["received_at"] = rows[received_index]["bbo"]["received_at"]
    rows[7]["bbo"]["best_bid_qty"] += 1
    params = parameters()
    params["target_bps"] = 50
    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=params,
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 80),
        target_date=DAY,
        source_audit={},
    )
    assert report["path_exclusions"][0]["reason"] == "same_quote_identity_conflict"
    assert report["path_count"] == 2
    assert not replay.select_candidate(report, previous_value=50)["candidate_ready"]


def test_observed_signal_end_before_confirmation_is_known_no_entry():
    rows = path()[:2]
    rows[1]["raw_state"] = "WATCH"
    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 100),
        target_date=DAY,
        source_audit={},
    )
    for model in report["candidates"][0]["pairs"][0]["models"].values():
        for outcome in model.values():
            assert outcome["status"] == "no_entry"
            assert outcome["net_pnl_krw"] == 0


def test_unconfirmed_short_prefix_is_censored_not_zero_profit():
    report = replay.build_study(
        path()[:1],
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 100),
        target_date=DAY,
        source_audit={},
    )
    outcome = report["candidates"][0]["pairs"][0]["models"]["base"]["baseline"]
    assert outcome["status"] == "right_censored"
    assert outcome["net_pnl_krw"] is None
    assert not replay.select_candidate(report, previous_value=100)["candidate_ready"]


def test_scale_in_recipe_carries_instead_of_using_bbo_as_runtime_trigger():
    params = parameters()
    params["add_trigger_bps_from_initial_fill"] = [-40]
    report = replay.build_study(
        profitable_paths(),
        symbol="005930",
        session="KRX_REGULAR",
        parameters=params,
        baseline_confirmations=2,
        axis="target_bps",
        values=(50, 100),
        target_date=DAY,
        source_audit={},
    )
    selection = replay.select_candidate(report, previous_value=100)
    assert selection["candidate_ready"] is False
    assert selection["selected_value"] == 100
    assert selection["evidence_state"] == "scale_in_runtime_trigger_source_missing"
    assert report["candidates"] == []
    assert replay.selection_valid(
        report,
        selection,
        symbol="005930",
        session="KRX_REGULAR",
        target_date=DAY,
        axis="target_bps",
        selected_value=100,
    )


def test_holdout_missing_keeps_incumbent():
    report = study()
    for candidate in report["candidates"]:
        candidate["pairs"] = candidate["pairs"][:-1]
    report["content_hash"] = replay.digest(
        {k: v for k, v in report.items() if k != "content_hash"}
    )
    result = replay.select_candidate(report, previous_value=100)
    assert result["selected_value"] == 100
    assert result["evidence_state"] == "paired_sample_floor_not_met"


def test_old_pairs_cannot_become_a_new_policy_without_recent_source():
    report = study()
    report["target_date"] = "2026-11-30"
    report["content_hash"] = replay.digest(
        {k: v for k, v in report.items() if k != "content_hash"}
    )
    result = replay.select_candidate(report, previous_value=100)
    assert result["selected_value"] == 100
    assert result["evidence_state"] == "rolling_evidence_expired"


def test_enough_complete_pairs_without_uplift_are_not_called_source_shortage():
    report = study()
    report["candidates"] = [r for r in report["candidates"] if r["value"] == 100]
    report["content_hash"] = replay.digest(
        {k: v for k, v in report.items() if k != "content_hash"}
    )
    result = replay.select_candidate(report, previous_value=100)
    assert result["candidate_ready"] is False
    assert result["evidence_state"] == "economic_guard_not_met"


@pytest.mark.parametrize(
    "kind",
    [
        "cost",
        "future",
        "duplicate",
        "other_axis",
        "scale_in",
        "missing_entry",
        "future_close",
        "tamper",
    ],
)
def test_consumer_recomputes_identity_cost_and_date_not_pass_claim(kind):
    report = study()
    if kind == "cost":
        report["candidates"][0]["pairs"][0]["models"]["base"]["candidate"][
            "cost_contract_hash"
        ] = "bad"
    elif kind == "future":
        report["candidates"][0]["pairs"][0]["source_date"] = "2026-09-10"
    elif kind == "duplicate":
        report["candidates"][0]["pairs"].append(
            copy.deepcopy(report["candidates"][0]["pairs"][0])
        )
    elif kind == "other_axis":
        report["candidates"][0]["parameters"]["leg_quantity_each"] = 20
    elif kind == "scale_in":
        report["baseline_parameters"]["add_trigger_bps_from_initial_fill"] = [-40]
        for candidate in report["candidates"]:
            candidate["parameters"]["add_trigger_bps_from_initial_fill"] = [-40]
    elif kind in {"missing_entry", "future_close"}:
        outcome = report["candidates"][0]["pairs"][0]["models"]["base"]["candidate"]
        if kind == "missing_entry":
            outcome.pop("entry_at")
        else:
            outcome["closed_at"] = "2026-09-10T10:00:00+09:00"
    else:
        report["content_hash"] = "wrong"
    if kind != "tamper":
        report["content_hash"] = replay.digest(
            {k: v for k, v in report.items() if k != "content_hash"}
        )
    assert not replay.select_candidate(report, previous_value=100)["candidate_ready"]


def test_input_trace_carries_normalized_bbo_and_load_deduplicates(tmp_path):
    from src.engine.monitoring.samsung_widget_advisory import AdvisoryPromotionFilter

    row = path()[0]
    advisory = dict(
        observed_at=row["observed_at"],
        session="KRX_REGULAR",
        state="ENTRY_READY",
        source_quality={"status": "PASS"},
    )
    advisory["execution_replay_input"] = replay.capture_input(
        advisory, symbol="005930", venue="KRX", bbo=row["bbo"]
    )
    result = AdvisoryPromotionFilter().apply(advisory)
    record = json.dumps({"advisory": result})
    source = tmp_path / "samsung_widget_advisory_20260909.jsonl"
    source.write_text(record + "\n" + record + "\n")
    rows, audit = replay.load_inputs([source], symbol="005930", target_date=DAY)
    assert len(rows) == 1
    assert audit["conflicting_observations"] == 0
    assert rows[0]["bbo"] == row["bbo"]


def test_canonical_current_input_is_not_lost_without_promotion_trace(tmp_path):
    row = path()[0]
    source = tmp_path / "samsung_widget_advisory_20260909.jsonl"
    source.write_text(
        json.dumps(
            {
                "advisory": {
                    "observed_at": row["observed_at"],
                    "session": "KRX_REGULAR",
                    "execution_replay_input": row,
                }
            }
        )
        + "\n"
    )
    rows, audit = replay.load_inputs([source], symbol="005930", target_date=DAY)
    assert len(rows) == 1
    assert audit["target_date_sessions"]["KRX_REGULAR"] == {
        "observation_count": 1,
        "replay_input_count": 1,
    }


def test_legacy_observations_are_not_reported_as_economic_sample_shortage(tmp_path):
    source = tmp_path / "samsung_widget_advisory_20260909.jsonl"
    source.write_text(
        json.dumps(
            {
                "advisory": {
                    "observed_at": path()[0]["observed_at"],
                    "session": "KRX_REGULAR",
                    "state": "WATCH",
                }
            }
        )
        + "\n"
    )
    rows, audit = replay.load_inputs([source], symbol="005930", target_date=DAY)
    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(30, 100),
        target_date=DAY,
        source_audit=audit,
    )
    result = replay.select_candidate(report, previous_value=100)
    assert result["selected_value"] == 100
    assert result["candidate_ready"] is False
    assert result["evidence_state"] == "source_gap"
    assert result["source_diagnostic"] == (
        "observation_present_replay_input_missing_check_collector_generation"
    )
    report["session"] = "NXT_AFTERMARKET"
    report["content_hash"] = replay.digest(
        {k: v for k, v in report.items() if k != "content_hash"}
    )
    assert replay.select_candidate(report, previous_value=100)["source_diagnostic"] == (
        "target_session_source_not_observed_check_schedule_and_owner"
    )


def test_existing_target_selector_freezes_cap_quantity_and_other_axes():
    previous = parameters()
    previous["take_profit_bps_from_equal_share_average"] = previous.pop("target_bps")
    previous.update(new_entry_runtime_eligible=True, policy_id="verified-incumbent")
    rows = path(date(2026, 9, 8), 10) + path(date(2026, 9, 8), 11) + path()
    calibration = {"decision": "old_large_target_winner"}
    apply_paired_target_selection(
        calibration,
        inputs=rows,
        source_audit={},
        symbol="005930",
        session="KRX_REGULAR",
        target_date=DAY,
        previous=previous,
        values=(30, 50, 100),
        confirmations=2,
    )
    assert calibration["decision"] == "widget_auto_trade_policy_candidate_ready"
    assert calibration["runtime_selected_policy"]["target_bps"] == 50
    assert calibration["runtime_selected_policy"]["max_completed_entries_per_day"] == 3
    apply_paired_target_selection(
        calibration,
        inputs=rows,
        source_audit={},
        symbol="005930",
        session="KRX_REGULAR",
        target_date=DAY,
        previous=previous,
        values=(30, 50, 100),
        confirmations=2,
        confirmation_axis_changed=True,
    )
    assert calibration["decision"] == "carry_forward_previous_verified_policy"
    assert calibration["runtime_selected_policy"]["target_bps"] == 100


def test_unreplayed_source_exit_and_missing_baseline_cannot_promote():
    params = parameters()
    params["source_final_exit_action"] = "sell_own_filled_quantity"
    report = replay.build_study(
        path(),
        symbol="034020",
        session="KRX_REGULAR",
        parameters=params,
        baseline_confirmations=2,
        axis="target_bps",
        values=(30, 100),
        target_date=DAY,
        source_audit={},
    )
    assert report["status"] == "baseline_contract_missing"
    selection = replay.select_candidate(report, previous_value=100)
    assert not selection["candidate_ready"]
    assert selection["evidence_state"] == "baseline_contract_missing"


def test_advisory_producer_to_loader_recomputes_paired_selection(tmp_path, monkeypatch):
    from dataclasses import replace
    from src.engine.monitoring import widget_advisory_calibration as calibration
    from src.engine.monitoring.widget_advisory_calibration_policy import (
        _selection_from_payload,
    )
    from src.tests.test_widget_advisory_calibration import _daily_report, _spec

    spec = replace(_spec(tmp_path), symbol="005930")
    daily = _daily_report(DAY)
    daily["symbol"] = "005930"
    params = parameters()
    params["take_profit_bps_from_equal_share_average"] = params.pop("target_bps")
    params.update(new_entry_runtime_eligible=True)
    monkeypatch.setattr(
        replay,
        "load_inputs",
        lambda *args, **kwargs: (
            [],
            {
                "target_date": DAY.isoformat(),
                "target_date_sessions": {
                    "KRX_REGULAR": {"observation_count": 30, "replay_input_count": 0}
                },
            },
        ),
    )
    policy, report = calibration.build_calibration_policy(
        target_date=DAY,
        daily_reports={"005930": daily},
        policy_dir=tmp_path,
        specs=(spec,),
        execution_baselines={"005930": {"KRX_REGULAR": params}},
    )
    assert report["all_daily_reports_verified"] is True
    args = dict(symbol="005930", session="KRX_REGULAR", observed_date=date(2026, 9, 10))
    selection = _selection_from_payload(policy, **args)
    assert selection["required_actionable_confirmations"] == 2
    assert selection["reason"] == "source_gap"
    assert (
        selection["paired_source_diagnostic"]
        == "observation_present_replay_input_missing_check_collector_generation"
    )
    policy["symbols"]["005930"]["sessions"]["KRX_REGULAR"][
        "required_actionable_confirmations"
    ] = 3
    assert _selection_from_payload(policy, **args) is None


def test_target_policy_loader_binds_economics_and_unchanged_knobs(tmp_path):
    from src.tests.test_widget_auto_trade_policy import _policy
    from src.trading.widget_auto_trade.policy import WidgetAutoTradePolicyLoader

    report = study()
    incumbent = _policy(effective_date="2026-09-09")
    incumbent_row = {
        **parameters(),
        "enabled": True,
        "take_profit_bps_from_equal_share_average": 100,
    }
    incumbent_row.pop("target_bps")
    incumbent["symbols"] = {"005930": {"sessions": {"KRX_REGULAR": incumbent_row}}}
    incumbent_path = tmp_path / "incumbent.json"
    incumbent_path.write_text(json.dumps(incumbent))
    replay.bind_incumbent(
        report,
        {"policy_path": str(incumbent_path), "policy_id": incumbent["policy_version"]},
    )
    selected = replay.select_candidate(report, previous_value=100)
    payload = _policy(effective_date="2026-09-10")
    payload["source_target_date"] = "2026-09-09"
    session = payload["symbols"].pop("034020")["sessions"]["KRX_REGULAR"]
    session.update(parameters())
    session.pop("target_bps")
    session.update(
        take_profit_bps_from_equal_share_average=50,
        force_flat_at_session_end=False,
        overnight_forbidden=False,
        paired_selection=selected,
    )
    payload["symbols"]["005930"] = {"sessions": {"KRX_REGULAR": session}}
    policy_path = tmp_path / "widget_auto_trade_policy_2026-09-10.json"
    report_path = tmp_path / "report.json"
    session["evidence_artifact"] = str(report_path)
    payload["evidence_report_path"] = str(report_path)
    evidence = dict(
        status="complete",
        source_quality_status="PASS",
        target_date="2026-09-09",
        effective_date="2026-09-10",
        policy_verification=dict(status="pass", policy_path=str(policy_path)),
        symbols={
            "005930": {
                "sessions": {
                    "KRX_REGULAR": {
                        "paired_economics": {"study": report, "selection": selected}
                    }
                }
            }
        },
    )
    report_path.write_text(json.dumps(evidence))
    policy_path.write_text(json.dumps(payload))

    def loader():
        return WidgetAutoTradePolicyLoader(
            tmp_path, include_symbol_expansion=False
        ).resolve_all(observed_date=date(2026, 9, 10))

    assert (
        loader()["005930"]["KRX_REGULAR"]["take_profit_bps_from_equal_share_average"]
        == 50
    )
    session["max_completed_entries_per_day"] = 5
    policy_path.write_text(json.dumps(payload))
    assert loader() == {}


def test_existing_timing_owner_sees_confirmation_axis_handoff(tmp_path):
    from src.engine.automation.machine_entry_timing_tuning import (
        _same_stage_owner_guard,
    )

    payload = dict(
        schema="widget_auto_trade_policy_v1",
        effective_date="2026-09-10",
        runtime_effect=True,
        symbols={
            "005930": {
                "sessions": {"KRX_REGULAR": {"advisory_confirmation_changed": True}}
            }
        },
    )
    (tmp_path / "widget_auto_trade_policy_2026-09-10.json").write_text(
        json.dumps(payload)
    )
    guard = _same_stage_owner_guard(
        target_date=DAY,
        low_price_candidate_dir=tmp_path,
        samsung_candidate_dir=tmp_path,
        widget_policy_dir=tmp_path,
    )
    assert guard["mutation_present"] is True
    assert any(
        owner.get("reason") == "existing_widget_advisory_confirmation_axis_selected"
        for owner in guard["owners"]
    )


def test_non_confirmation_exit_conflict_is_not_an_entry():
    rows = path()
    for row in rows:
        row["non_confirmation_entry_blocked"] = True
    report = replay.build_study(
        rows,
        symbol="005930",
        session="KRX_REGULAR",
        parameters=parameters(),
        baseline_confirmations=2,
        axis="target_bps",
        values=(30, 100),
        target_date=DAY,
        source_audit={},
    )
    assert report["path_count"] == 0
    assert not replay.select_candidate(report, previous_value=100)["candidate_ready"]
