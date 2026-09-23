"""The delay family cannot promote partial quote evidence as executable EV."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from src.engine.scalping import pre_submit_delay_tuning as delay


def test_decision_type_is_frozen_from_known_submit_inputs_and_reported_separately(tmp_path, monkeypatch):
    observed = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561, venue="KRX", session="KRX_REGULAR",
    )
    assert observed["type_key"] == "KRX|KRX_REGULAR|5_TO_10BP"
    assert observed["liquidity_band"] == "UNKNOWN"
    assert observed["volatility_band"] == "UNKNOWN"
    assert observed["market_cap_krw"] is None
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=pre_submit_delay"
    source.mkdir(parents=True)
    commit = {
        "delay_intent_id": "intent-1", "entry_action": "ENTER_NOW",
        "auxiliary_effective_action": "PASS", "planned_qty": 5,
        "owner": "main_scalping", "route": "KRX",
        "delay_decision_type": json.dumps(observed, sort_keys=True),
    }
    quote = {"delay_intent_id": "intent-1", "target_delay_sec": 30,
             "ask_price": 1550, "ask_qty": 1, "quote_valid": True, "route": "KRX"}
    with (source / "part-execution-test.jsonl").open("w", encoding="utf-8") as handle:
        for index, (stage, fields) in enumerate((
            ("pre_submit_delay_committed", commit),
            ("pre_submit_delay_quote_observed", quote),
        )):
            handle.write(json.dumps({
                "stage": stage, "fields": fields,
                "family": "pre_submit_delay", "emitted_date": "2026-09-23",
                "execution_source_event_sha256": f"{index + 1:064x}",
            }) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24")
    group = report["type_census"][0]
    assert group["type_key"] == observed["type_key"]
    assert group["eligible_attempt_count"] == 1
    assert group["candidate_grid"][1]["source_valid_attempt_count"] == 1
    assert group["candidate_grid"][1]["paired_net_ev_delta_pct"] is None
    assert report["selected_delay_sec"] is None
    assert report["first_blocker"] == "exact_submit_terminal_receipt_missing"
    policy = json.loads(delay.policy_path("2026-09-23").read_text())
    assert policy["type_policies"][observed["type_key"]]["selected_delay_sec"] is None
    assert policy["scope_policies"]["KRX|KRX_REGULAR"]["selected_delay_sec"] is None
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE",
                       str(delay.policy_path("2026-09-23")))
    loaded = delay.load_runtime_policy(
        now=datetime(2026, 9, 24, 9, tzinfo=timezone(timedelta(hours=9))),
        decision_type=observed,
    )
    assert loaded["delay_sec"] == 0  # Existing immediate-submit behavior, not a selected delay policy.
    assert loaded["status"] == "no_validated_delay_policy_source_gap"


def test_existing_post_decision_quote_is_counted_without_inventing_fill(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    source = tmp_path / "threshold_cycle" / "date=2026-09-23" / "family=dynamic_entry_price_resolver"
    source.mkdir(parents=True)
    (source / "part-execution-test.jsonl").write_text(json.dumps({
        "stage": "order_leg_sent", "emitted_date": "2026-09-23",
        "stock_code": "355390", "emitted_at": "2026-09-23T10:53:05+09:00",
    }) + "\n", encoding="utf-8")
    raw = tmp_path / "pipeline_events"
    raw.mkdir()
    with (raw / "pipeline_events_2026-09-23.jsonl").open("w", encoding="utf-8") as handle:
        for elapsed, ask in ((0, 1564), (30, 1550)):
            handle.write(json.dumps({
                "stock_code": "355390", "stage": "quote_observed",
                "emitted_at": (
                    datetime(2026, 9, 23, 10, 53, 5, tzinfo=timezone(timedelta(hours=9)))
                    + timedelta(seconds=elapsed)
                ).isoformat(),
                "fields": {"fresh_best_ask": ask},
            }) + "\n")
    report = delay.build_report("2026-09-23", effective_date="2026-09-24")
    from src.engine.automation import postclose_summary_handoff as stages
    assert stages.STAGE_REGISTRY["pre_submit_delay"][0] == ()
    assert stages._stage_output_issues(tmp_path / "report", "2026-09-23", "pre_submit_delay") == []
    census = report["existing_quote_census"]
    assert census["submit_count"] == 1
    assert census["horizon_stock_count"]["30"] == 1
    assert census["not_a_fill_or_route_validity_claim"] is True
    assert report["first_blocker"] == "exact_commit_and_horizon_quote_binding_missing"
    assert all(row["paired_net_ev_pct"] is None for row in report["candidate_grid"])
    assert delay._existing_quote_census("2026-09-23")["cache_hit"] is True

    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path("2026-09-23")))
    now = datetime(2026, 9, 24, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now)["delay_sec"] == 0
    assert delay.load_runtime_policy(now=now)["status"] == "no_validated_delay_policy_source_gap"
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    handoff_env, handoff = bootstrap._pre_submit_delay_handoff("2026-09-24")
    assert handoff["status"] == "no_validated_candidate_source_gap"
    assert handoff_env == {}
    # A self-consistent file pair still cannot promote a 30-second arm when
    # the underlying report only contains quote fields and no paired EV.
    source_report = json.loads(delay.report_path("2026-09-23").read_text())
    source_policy = json.loads(delay.policy_path("2026-09-23").read_text())
    source_report.pop("policy_sha256")
    source_policy.pop("policy_sha256")
    source_report["selected_delay_sec"] = 30.0
    source_policy.update(selected_delay_sec=30.0, runtime_apply_allowed=True,
                         selection_status="selected", model_status="validated",
                         paired_net_ev_delta_pct=1.0, holdout_net_ev_delta_pct=0.0,
                         expires_on="9999-12-31", carry_forward_until_superseded=True)
    source_policy["report_sha256"] = delay._digest(source_report)
    source_policy["policy_sha256"] = delay._digest(source_policy)
    source_report["policy_sha256"] = source_policy["policy_sha256"]
    delay._atomic_json(delay.report_path("2026-09-23"), source_report)
    delay._atomic_json(delay.policy_path("2026-09-23"), source_policy)
    assert delay.load_runtime_policy(now=now)["status"] == "policy_economics_unvalidated"
    assert bootstrap._pre_submit_delay_handoff("2026-09-24")[1]["status"] == "binding_invalid"
    delay.report_path("2026-09-23").write_text("{}\n", encoding="utf-8")
    assert delay.load_runtime_policy(now=now)["status"] == "policy_report_identity_invalid"
    assert bootstrap._pre_submit_delay_handoff("2026-09-24")[1]["status"] == "binding_invalid"


def test_source_census_aggregates_only_clean_baseline_partitions(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "DATA_DIR", tmp_path)
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report" / "pre_submit_delay_tuning")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")

    def write_day(day, identity):
        source = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
        source.mkdir(parents=True)
        (source / "part-execution-test.jsonl").write_text(json.dumps({
            "stage": "pre_submit_delay_committed",
            "fields": {"delay_intent_id": identity},
            "family": "pre_submit_delay", "emitted_date": day,
            "execution_source_event_sha256": identity.ljust(64, "0"),
        }) + "\n", encoding="utf-8")

    write_day("2026-06-04", "archive-only")
    write_day("2026-06-05", "baseline-day")
    write_day("2026-09-22", "prior-day")
    write_day("2026-09-23", "target-day")
    rows, source = delay._source_rows("2026-09-23")
    assert [row["fields"]["delay_intent_id"] for row in rows] == [
        "baseline-day", "prior-day", "target-day",
    ]
    assert source["window_policy"] == "clean_baseline_cumulative_through_target_date"
    assert source["clean_tuning_baseline_date"] == "2026-06-05"
    assert source["source_dates"] == ["2026-06-05", "2026-09-22", "2026-09-23"]


def test_live_quote_observer_keeps_small_level_one_depth_as_valid_source(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append((a, kw)))
    monkeypatch.setattr(
        handlers, "_build_quote_consistency_fields",
        lambda *a, **kw: ({"quote_consistency_state": "single_source", "quote_consistency_entry_blocked": False}, 0, 0, 0),
    )
    stock = {"_pre_submit_delay_observation": {
        "id": "exact-intent", "committed_at_epoch": 100.0,
        "remaining_sec": [30.0], "route": "KRX",
    }}
    ws = {
        "ws_route": "KRX", "orderbook": {
            "asks": [{"price": 1564, "volume": 1}],
            "bids": [{"price": 1561, "volume": 31}],
        }, "last_realtime_type_ts": {"0D": 129.8},
    }
    assert handlers.pre_submit_delay_observation_due(stock, now_ts=129.9) is False
    assert handlers.pre_submit_delay_observation_due(stock, now_ts=130.0) is True
    handlers.observe_pre_submit_delay_quote(stock, "355390", ws, now_ts=130.0)
    assert events[0][0][2] == "pre_submit_delay_quote_observed"
    assert events[0][1]["ask_qty"] == 1
    assert events[0][1]["quote_valid"] is True
    assert events[0][1]["actual_order_submitted"] is False
    assert "_pre_submit_delay_observation" not in stock


def test_due_intent_requires_same_policy_owner_quantity_cap_and_route(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    frozen_type = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561,
        venue="KRX", session="KRX_REGULAR",
    )
    due = {
        "id": "intent", "delay_sec": 30.0, "policy_sha256": "policy",
        "machine_key": ("attempt", "observation"),
        "machine_policy_sha256": "machine", "ai_policy_sha256": "ai",
        "ai_effective_assessment": "PASS", "planned_qty": 5,
        "price_cap": 1564, "route": "KRX", "decision_type": frozen_type,
    }
    policy = {"status": "loaded", "delay_sec": 30.0, "policy_sha256": "policy"}
    machine = {
        "entry_mechanistic_action": "ENTER_NOW",
        "evaluation_attempt_id": "attempt",
        "machine_observation_sha256": "observation",
        "entry_mechanistic_policy_sha256": "machine",
        "entry_ai_soft_policy_sha256": "ai",
        "entry_ai_effective_assessment": "PASS",
    }
    kwargs = dict(quote_route="KRX", requested_qty=5, final_price=1563)
    assert handlers.pre_submit_delay_due_matches(due, policy, machine, frozen_type, **kwargs)
    assert handlers.pre_submit_delay_due_matches(
        due, policy,
        {**machine, "entry_ai_effective_assessment": {"effective_verdict": "PASS"}},
        frozen_type, **kwargs,
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "final_price": 1565}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "requested_qty": 6}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine, frozen_type, **{**kwargs, "quote_route": "NXT"}
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, {**policy, "policy_sha256": "successor"}, machine, frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "entry_ai_effective_assessment": "VETO"},
        frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine,
        {**frozen_type, "session_bucket": "NXT_AFTERMARKET"}, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, machine,
        {**frozen_type, "type_key": "KRX|KRX_REGULAR|GE_10BP"}, **kwargs
    )
    assert handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "evaluation_attempt_id": "successor"},
        frozen_type, **kwargs
    )
    assert not handlers.pre_submit_delay_due_matches(
        due, policy, {**machine, "machine_observation_sha256": ""},
        frozen_type, **kwargs
    )


def test_expired_delay_does_not_submit_without_current_trigger(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **kw: events.append((a, kw)))
    stock = {"_pre_submit_delay_pending": {
        "id": "intent", "delay_sec": 30.0, "committed_at_epoch": 100.0,
        "due_monotonic": 200.0, "machine_key": ("attempt", "observation"),
    }}
    assert not handlers.expire_untriggered_pre_submit_delay(stock, "355390", now_mono=199.9)
    assert handlers.expire_untriggered_pre_submit_delay(stock, "355390", now_mono=200.0)
    assert "_pre_submit_delay_pending" not in stock
    assert events[0][0][2] == "pre_submit_delay_intent_terminal"
    assert events[0][1]["actual_order_submitted"] is False


def test_zero_delay_intent_closes_on_actual_submit_call(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    events = []
    monkeypatch.setattr(handlers, "_log_entry_pipeline",
                        lambda *args, **fields: events.append((args[2], fields)))
    monkeypatch.setattr(handlers, "submit_attempt_fields", lambda *args: {
        "entry_submit_attempt_broker_accepted": True,
        "entry_submit_attempt_return_outcome": "returned",
    })
    stock = {"_pre_submit_delay_zero_intent": {
        "id": "zero-intent", "delay_sec": 0.0,
        "committed_at_epoch": 100.0,
        "machine_observation_sha256": "observation",
    }}
    handlers._observe_entry_submit_finished(stock, "005930", True)
    stage, fields = events[0]
    assert stage == "pre_submit_delay_intent_terminal"
    assert fields["delay_intent_id"] == "zero-intent"
    assert fields["selected_delay_sec"] == 0.0
    assert fields["actual_order_submitted"] is True
    assert "_pre_submit_delay_zero_intent" not in stock


def test_type_selected_delay_never_spills_into_another_type(tmp_path, monkeypatch):
    monkeypatch.setattr(delay, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(delay, "POLICY_DIR", tmp_path / "threshold_cycle" / "pre_submit_delay_policy")
    target = "2026-09-23"
    effective = "2026-09-24"
    selected_type = delay.decision_type_snapshot(
        price=1564, ask=1564, bid=1561, venue="KRX", session="KRX_REGULAR"
    )
    other_type = delay.decision_type_snapshot(
        price=25000, ask=25000, bid=24950, venue="KRX", session="KRX_REGULAR"
    )
    assert selected_type["type_key"] != other_type["type_key"]
    row = {"delay_sec": 30.0, "candidate_passed": True,
           "paired_net_ev_delta_pct": .2, "holdout_net_ev_delta_pct": .1,
           "source_valid_attempt_count": 12, "holdout_attempt_count": 4,
           "model_fill_error": .01}
    report = {
        "schema": delay.REPORT_SCHEMA, "analysis_axis": delay.FAMILY,
        "source_date": target, "effective_date": effective,
        "selected_delay_sec": None, "status": "validated_edge",
        "model_status": "validated", "source": {"status": "ready"},
        "terminal_observation_count": 12, "candidate_grid": [],
        "scope_census": [],
        "type_census": [{"type_key": selected_type["type_key"],
                         "candidate_grid": [row]}],
        "selected_type_policies": {selected_type["type_key"]: 30.0},
    }
    policy = {
        "schema": delay.POLICY_SCHEMA, "source_date": target,
        "effective_from": effective, "expires_on": "9999-12-31",
        "carry_forward_until_superseded": True,
        "selection_status": "selected_by_type",
        "selected_delay_sec": None, "runtime_apply_allowed": True,
        "scope_policies": {},
        "type_policies": {selected_type["type_key"]: {
            "selected_delay_sec": 30.0, "runtime_apply_allowed": True,
            "selection_status": "selected", "model_status": "validated",
            "paired_net_ev_delta_pct": .2, "holdout_net_ev_delta_pct": .1,
        }},
    }
    policy["report_sha256"] = delay._digest(report)
    policy["policy_sha256"] = delay._digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    delay._atomic_json(delay.report_path(target), report)
    delay._atomic_json(delay.policy_path(target), policy)
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE", str(delay.policy_path(target)))
    now = datetime(2026, 9, 24, 10, tzinfo=timezone(timedelta(hours=9)))
    assert delay.load_runtime_policy(now=now, decision_type=selected_type)["delay_sec"] == 30.0
    assert delay.load_runtime_policy(now=now, decision_type=other_type)["delay_sec"] == 0.0
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    assert bootstrap._pre_submit_delay_handoff(effective)[1]["status"] == "verified_candidate"
    carry_env, carry_receipt = bootstrap._pre_submit_delay_handoff("2026-09-25")
    assert carry_receipt["status"] == "verified_carried_candidate"
    assert carry_env["KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE"] == "2026-09-25"
    policy["type_policies"][selected_type["type_key"]]["holdout_net_ev_delta_pct"] = -.1
    policy["report_sha256"] = delay._digest({k: v for k, v in report.items() if k != "policy_sha256"})
    policy.pop("policy_sha256")
    policy["policy_sha256"] = delay._digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    delay._atomic_json(delay.report_path(target), report)
    delay._atomic_json(delay.policy_path(target), policy)
    assert delay.load_runtime_policy(now=now, decision_type=selected_type)["delay_sec"] == 0.0
