from datetime import datetime, timedelta
import hashlib
import json

import pytest

from src.engine import buy_funnel_sentinel as sentinel
from src.engine.monitoring import submission_bottleneck_monitor as monitor

START = datetime(2026, 9, 21, 8, 5)


def test_monitor_consumes_pre_submit_prices_separately_from_terminal_and_pid(tmp_path, monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}], write=True)
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    result = monitor.entry_execution_tuning_semantics(tmp_path, datetime(2026, 10, 2, 19, 0))
    price = result["pre_submit_delay"]["price_pattern_analysis"]
    assert price["status"] == "partial" and price["analysis_complete"] is True
    assert result["pre_submit_delay"]["submit_call_terminal_count"] == 0
    assert result["pre_submit_delay"]["terminal_count_semantics"] == "submit_call_completion_not_fill_or_exit"
    assert result["pre_submit_delay"]["runtime_consumption"] == "not_proven"
    assert "pre_submit_delay_price_pattern_invalid" not in result["issues"]


def test_monitor_rejects_pre_submit_price_section_with_wrong_source_date(tmp_path, monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import pre_submit_delay_tuning as delay
    from src.engine.automation import runtime_policy_bootstrap as bootstrap
    report = _price_pattern_fixture(tmp_path, monkeypatch, [{"prices": {0: 10000, 30: 9900}}], write=True)
    report["price_pattern_analysis"]["source_date"] = "2026-10-01"
    delay.report_path("2026-10-02").write_text(json.dumps(report))
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    result = monitor.entry_execution_tuning_semantics(tmp_path, datetime(2026, 10, 2, 19, 0))
    assert result["issues"]["pre_submit_delay_price_pattern_invalid"] == 1
    assert result["pre_submit_delay"]["price_pattern_analysis"]["analysis_complete"] is False


def event(i=0, action="ENTER_NOW", screen="pass", stage="ai_confirmed", when=START, **extra):
    return sentinel.PipelineEvent(when, "ENTRY_PIPELINE", stage, "fixture", "005930", str(i), {
        "entry_primary_decision_owner": "mechanistic_entry_adjudicator",
        "evaluation_attempt_id": f"eval-{i}", "scanner_promotion_id": f"parent-{i}",
        "effective_venue": "NXT", "market_session_bucket": "nxt_premarket",
        "policy_bundle_hash": "b" * 64, "entry_mechanistic_action": action,
        "entry_ai_screen_status": screen, "entry_mechanistic_policy_version": "v1", **extra,
    })


def report(events, now):
    # Real Sentinel normalization -> exact identity/terminal ledger -> monitor.
    return {"target_date": now.date().isoformat(), "dry_run": False,
            "submission_monitor": monitor.snapshot(events, now)}


def tick(events, minutes, state=None):
    now = START + timedelta(minutes=minutes)
    # A fresh independent evaluation proves the input stream is advancing.
    fresh = event(999, "RECHECK", "not_requested_machine_nonentry", when=now)
    # Existing decision/terminal tests isolate their axis from economics; the
    # actual producer support/diagnostic projection is tested separately.
    payload = report(events + [fresh], now)
    for row in payload['submission_monitor']['rows']:
        row['economic_source'] = {'status': 'unsupported_scope', 'blocker': 'fixture_economics_not_exercised'}
    return monitor.evaluate(payload, state or {}, now)


def active(state):
    return [r for r in state["incidents"].values() if r["status"] == "active"]


@pytest.mark.parametrize('stage,reason_field', [
    ('pre_submit_weak_context_late_entry_guard_block','weak_context_guard_reason'),
    ('real_weak_pullback_entry_block','reason'),
])
def test_quality_guard_terminal_survives_exact_monitor_projection(stage, reason_field):
    lineage={'machine_revision_schema':'exact_machine_revision_v1',
             'machine_observation_sha256':'a'*64, 'machine_revision_parent_sha256':''}
    rows=[event(**lineage),event(stage=stage,when=START+timedelta(seconds=1),
        actual_order_submitted='False',broker_order_forbidden='True',
        **lineage, **{reason_field:'weak_momentum_context'})]
    row=monitor.snapshot(rows,START+timedelta(seconds=2))['rows'][0]
    assert row['conflict_reasons']==[]
    assert row['final_state']=='final_guard_blocked'
    assert row['broker_acceptance_observed'] is False
    assert row['final_guard_evidence'][0]['stage']==stage
    assert row['final_guard_evidence'][0]['reason']=='weak_momentum_context'


def test_pre_submit_intraday_monitor_catches_scanner_parity_and_quote_gap_without_false_recovery(tmp_path):
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor, execution_projection_identity

    day = "2026-09-29"
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir()
    scanner = {"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
               "stage": "scalping_scanner_fast_precheck", "stock_name": "test",
               "stock_code": "355390", "record_id": 1, "fields": {},
               "emitted_at": f"{day}T10:00:00", "emitted_date": day}
    commit = {**scanner, "stage": "pre_submit_delay_committed", "record_id": 3,
              "fields": {"delay_intent_id": "intent-1", "route": "",
                         "market_session_bucket": "krx_regular"}}
    quote = {**scanner, "stage": "pre_submit_delay_quote_observed", "record_id": 3,
             "fields": {"delay_intent_id": "intent-1", "target_delay_sec": "0",
                        "quote_route": "", "quote_valid": "False",
                        "quote_source_reason": "route_mismatch_or_missing"}}
    raw.write_text("".join(json.dumps(row) + "\n" for row in
                           (scanner, {**scanner, "record_id": 2}, commit, quote)))
    compact_dir = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    compact_dir.mkdir(parents=True)
    with (compact_dir / "part-execution-1000.jsonl").open("w") as handle:
        for event in (commit, quote):
            payload = {"schema_version": 1, "event_type": "threshold_cycle_event",
                       "family": "pre_submit_delay", **{key: event[key] for key in
                       ("pipeline", "stage", "stock_name", "stock_code", "record_id", "fields", "emitted_at", "emitted_date")},
                       "execution_source_event_sha256": execution_projection_identity(event)}
            handle.write(json.dumps(payload) + "\n")
    compactor = ProducerSummaryCompactor(summary_dir=tmp_path / "pipeline_event_summaries", mode="shadow")
    for event in (scanner, commit, quote):
        compactor.submit(event)
    compactor.flush()
    early = monitor.pre_submit_delay_source_semantics(tmp_path, datetime(2026, 9, 29, 10, 1))
    assert "producer_raw_summary_window_mismatch" not in early["issues"]
    first = monitor.pre_submit_delay_source_semantics(tmp_path, datetime(2026, 9, 29, 10, 4))
    assert first["sources"]["raw"] == "complete"
    assert first["issues"]["producer_raw_summary_window_mismatch"] == 1
    assert first["diagnostics"]["committed_route_derived_from_session"] == 1
    assert "committed_route_missing" not in first["issues"]
    assert first["issues"]["quote_source_invalid"] == 1
    assert "zero_second_quote_missing" not in first["issues"]
    manifest_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_manifest_{day}.json"
    original_manifest = manifest_path.read_text()
    slow_manifest = json.loads(original_manifest)
    slow_manifest["flush_interval_sec"] = 3600
    manifest_path.write_text(json.dumps(slow_manifest))
    slow = monitor.pre_submit_delay_source_semantics(tmp_path, datetime(2026, 9, 29, 10, 4))
    assert slow["issues"]["producer_summary_flush_interval_too_long"] == 1
    assert "producer_raw_summary_window_mismatch" not in slow["issues"]
    manifest_path.write_text(original_manifest)
    result = {"as_of": first["as_of"], "incidents": {}, "notification_pending": [],
              "status": "unobservable", "blocker": None}
    monitor.attach_pre_submit_delay_source_semantics(result, first)
    assert result["incidents"]["pre_submit_delay_intraday_source_gap"]["status"] == "active"
    sent = []
    monitor.notify(result, "monitor.json", send=sent.append)
    assert len(sent) == 1
    assert "[매수 지연 원천결손 점검]" in sent[0]
    assert "producer_raw_summary_window_mismatch" in sent[0]
    later = monitor.pre_submit_delay_source_semantics(
        tmp_path, datetime(2026, 9, 29, 10, 15), first["cursor"])
    assert later["status"] == "observed_no_gap"
    result = {"as_of": later["as_of"], "incidents": result["incidents"],
              "notification_pending": [], "status": "unobservable", "blocker": None}
    monitor.attach_pre_submit_delay_source_semantics(result, later)
    assert result["incidents"]["pre_submit_delay_intraday_source_gap"]["status"] == "historical_unresolved"
    old_scopes = result["incidents"]["pre_submit_delay_intraday_source_gap"]["issues_by_scope"]
    wrong_route = {**later, "healthy_by_scope": {
        **{scope: 1 for scope in old_scopes if not scope.startswith("quote_source_invalid|")},
        "quote_source_invalid|NXT_ONLY": 1}}
    result["as_of"] = datetime(2026, 9, 29, 10, 20, tzinfo=monitor.KST).isoformat()
    monitor.attach_pre_submit_delay_source_semantics(result, wrong_route)
    assert result["incidents"]["pre_submit_delay_intraday_source_gap"]["status"] == "historical_unresolved"
    same_route = {**later, "healthy_by_scope": {scope: 1 for scope in old_scopes}}
    result["as_of"] = datetime(2026, 9, 29, 10, 25, tzinfo=monitor.KST).isoformat()
    monitor.attach_pre_submit_delay_source_semantics(result, same_route)
    assert result["incidents"]["pre_submit_delay_intraday_source_gap"]["status"] == "recovered"
    sent.clear()
    monitor.notify(result, "monitor.json", send=sent.append)
    assert len(sent) == 1
    assert "[매수 지연 원천 정상 관측]" in sent[0]


def test_pre_submit_monitor_separates_unobservable_sources_from_count_mismatch(tmp_path, monkeypatch):
    import os
    from src.engine import pipeline_event_summary as summary_owner
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor

    day = "2026-09-29"
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir()
    event = {"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
             "stage": "scalping_scanner_fast_precheck", "stock_name": "test",
             "stock_code": "355390", "record_id": 1, "fields": {},
             "emitted_at": f"{day}T10:00:00", "emitted_date": day}
    raw.write_text(json.dumps(event) + "\n")
    now = datetime(2026, 9, 29, 10, 4)
    missing = monitor.pre_submit_delay_source_semantics(tmp_path, now)
    assert missing["sources"]["summary"] == "unobservable"
    assert missing["issues"]["producer_summary_unobservable_with_raw"] == 1
    assert "producer_raw_summary_window_mismatch" not in missing["issues"]
    compactor = ProducerSummaryCompactor(summary_dir=tmp_path / "pipeline_event_summaries", mode="shadow")
    compactor.submit(event)
    compactor.flush()
    healthy = monitor.pre_submit_delay_source_semantics(tmp_path, now)
    assert healthy["status"] == "observed_no_gap"
    assert healthy["healthy_by_scope"]["producer_summary_unobservable_with_raw|scalping_scanner_fast_precheck"] == 1
    raw.write_text("")
    reset = monitor.pre_submit_delay_source_semantics(tmp_path, now, healthy["cursor"])
    assert reset["sources"]["raw"] == "partial"
    assert reset["status"] != "observed_no_gap"
    raw.write_text(json.dumps(event) + "\n")
    invalid_cursor = {**healthy["cursor"], "minutes": []}
    reset = monitor.pre_submit_delay_source_semantics(tmp_path, now, invalid_cursor)
    assert reset["sources"]["raw"] == "partial"
    original_load = summary_owner.load_summary_rows

    def changed_during_read(path, **kwargs):
        rows = original_load(path, **kwargs)
        before = path.stat()
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        return rows

    monkeypatch.setattr(summary_owner, "load_summary_rows", changed_during_read)
    changed = monitor.pre_submit_delay_source_semantics(tmp_path, now)
    assert changed["sources"]["summary"] == "unobservable"
    assert changed["issues"]["producer_summary_unobservable_with_raw"] == 1
    assert "producer_raw_summary_window_mismatch" not in changed["issues"]
    monkeypatch.setattr(summary_owner, "load_summary_rows", original_load)
    raw.write_text(json.dumps({**event, "emitted_at": "invalid-time"}) + "\n")
    invalid_time = monitor.pre_submit_delay_source_semantics(tmp_path, now)
    assert invalid_time["issues"]["raw_malformed_event"] == 1
    assert invalid_time["sources"]["raw"] == "partial"
    raw.write_text("x" * 100)
    monkeypatch.setattr(monitor, "DELAY_RAW_BUDGET", 32)
    unbounded = monitor.pre_submit_delay_source_semantics(tmp_path, now)
    assert unbounded["sources"]["raw"] == "unobservable"
    assert unbounded["issues"]["raw_cursor_backlog"] == 1


def test_pre_submit_monitor_binds_intents_to_stock_and_record(tmp_path):
    day = "2026-09-29"
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir()
    base = {"event_type": "pipeline_event", "pipeline": "ENTRY_PIPELINE",
            "stock_name": "test", "emitted_at": f"{day}T10:00:00", "emitted_date": day}
    commits = [{**base, "stage": "pre_submit_delay_committed", "stock_code": code,
                "record_id": index, "fields": {"delay_intent_id": "same-id",
                                               "market_session_bucket": "krx_regular"}}
               for index, code in enumerate(("005930", "000660"), 1)]
    quote = {**base, "stage": "pre_submit_delay_quote_observed", "stock_code": "000660",
             "record_id": 2, "fields": {"delay_intent_id": "same-id", "target_delay_sec": 0}}
    raw.write_text("".join(json.dumps(row) + "\n" for row in (*commits, quote)))
    compact_dir = tmp_path / "threshold_cycle" / f"date={day}" / "family=pre_submit_delay"
    compact_dir.mkdir(parents=True)
    (compact_dir / "part-execution-1000.jsonl").write_text("{invalid\n")
    observed = monitor.pre_submit_delay_source_semantics(tmp_path, datetime(2026, 9, 29, 10, 4))
    assert observed["issues"]["zero_second_quote_missing"] == 1
    assert observed["sources"]["compact"] == "unobservable"
    assert observed["issues"]["compact_source_unobservable_with_raw"] == 3
    assert "raw_compact_event_missing" not in observed["issues"]
    raw.write_text("".join(json.dumps(row) + "\n" for row in
                           (*commits, {**quote, "fields": {**quote["fields"], "target_delay_sec": "nan"}})))
    invalid_horizon = monitor.pre_submit_delay_source_semantics(tmp_path, datetime(2026, 9, 29, 10, 4))
    assert invalid_horizon["issues"]["quote_horizon_invalid"] == 1


def test_pre_submit_source_cli_runs_without_sentinel_report_or_other_semantics(tmp_path, monkeypatch):
    import sys

    day = datetime.now(monitor.KST).date().isoformat()
    monkeypatch.setattr(monitor, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "source_gap_semantics", lambda *a, **k: pytest.fail("unrelated_source_called"))
    monkeypatch.setattr(monitor, "machine_semantics", lambda *a, **k: pytest.fail("machine_semantics_called"))
    monkeypatch.setattr(monitor, "notify", lambda *a, **k: None)
    monkeypatch.setattr(monitor, "pre_submit_delay_source_semantics", lambda *a, **k: {
        "schema": "pre_submit_delay_intraday_source_semantics_v1",
        "status": "unobservable", "cursor": {"date": day}, "issues": {},
        "issues_by_scope": {}, "healthy": {}, "healthy_by_scope": {},
        "sources": {"raw": "unobservable", "summary": "unobservable", "compact": "unobservable"},
        "examples": [],
    })
    monkeypatch.setattr(sys, "argv", ["monitor", "--report", str(tmp_path / "missing.json"),
                                       "--delay-source-only", "--date", day, "--notify"])
    assert monitor.main() == 0
    saved = json.loads((tmp_path / "data/report/buy_funnel_sentinel" /
                        "pre_submit_delay_source_monitor_latest.json").read_text())
    assert saved["pre_submit_delay_source_semantics"]["status"] == "unobservable"
    assert "source_gap_semantics" not in saved


def _entry_axis_fixture(data_root, *, delay_handoff=None, mismatch_split_policy=False, delay_env=None):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap_owner
    from src.engine.scalping import entry_split_order_plan as split_owner

    target = START.date().isoformat()
    bootstrap_dir = data_root / "runtime/policy_bootstrap"
    bootstrap_dir.mkdir(parents=True)
    (bootstrap_dir / f"runtime_policy_bootstrap_{target}.json").write_text(json.dumps({
        "target_date": target,
        "pre_submit_delay_handoff": delay_handoff or {"status": "not_published", "target_date": target},
        "env_overrides": delay_env or {},
    }))
    (bootstrap_dir / f"runtime_policy_bootstrap_verify_{target}.json").write_text(json.dumps({
        "target_date": target, "status": "pass", "passed": True, "pid_passed": True,
    }))

    report = {
        "schema_version": split_owner.SCHEMA_VERSION,
        "date": target,
        "recommended_policy": {
            "policy_version": "entry_split_fixture_v1",
            "entry_execution_sizing_plan_schema": split_owner.ATOMIC_EXECUTION_SIZING_SCHEMA,
            "entry_execution_sizing_policy": split_owner.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
            "entry_price_plan_schema": split_owner.ATOMIC_PRICE_PLAN_SCHEMA,
        },
        "economic_acceptance": {
            "status": "source_gap", "blockers": ["operating_paired_source_missing"],
            "primary_operating_ev_pct": None,
            "robust_paired_delta_ev_lower_bound_pct": None,
            "model_rows": 0, "consumed_holdouts": 0,
        },
        "operating_candidate_grid": [],
        "cumulative_state": {"clean_tuning_baseline_date": "2026-06-05", "source_dates": [target]},
    }
    policy = {
        "schema_version": split_owner.POLICY_SCHEMA_VERSION,
        "source_date": target,
        "policy_version": "entry_split_fixture_v1",
        "runtime_apply_allowed": False,
        "entry_execution_sizing_plan_schema": split_owner.ATOMIC_EXECUTION_SIZING_SCHEMA,
        "entry_execution_sizing_policy": split_owner.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
        "entry_price_plan_schema": split_owner.ATOMIC_PRICE_PLAN_SCHEMA,
    }
    report, policy = split_owner.bind_report_policy_generation(report, policy)
    if mismatch_split_policy:
        policy["policy_version"] = "tampered"
    report_dir = data_root / "report/entry_split_order_plan"
    policy_dir = data_root / "threshold_cycle/entry_split_order_policy"
    report_dir.mkdir(parents=True)
    policy_dir.mkdir(parents=True)
    (report_dir / f"entry_split_order_plan_{target}.json").write_text(json.dumps(report))
    (policy_dir / f"entry_split_order_policy_{target}.json").write_text(json.dumps(policy))
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(bootstrap_owner, "DATA_DIR", data_root)
    return monkeypatch


def test_entry_execution_semantics_keeps_source_gaps_separate_from_receipt_faults(tmp_path):
    patch = _entry_axis_fixture(tmp_path)
    try:
        semantics = monitor.entry_execution_tuning_semantics(tmp_path, START)
        assert semantics["status"] == "observed"
        assert semantics["axes_are_independent"] is True
        assert semantics["issues"] == {}
        assert semantics["entry_split"]["status"] == "source_gap"
        assert semantics["entry_split"]["operating_candidate_count"] == 0
        assert semantics["entry_split"]["paired_net_ev_delta_pct"] is None
        assert semantics["pre_submit_delay"]["status"] == "unpublished"
    finally:
        patch.undo()


def test_entry_execution_semantics_detects_generation_and_handoff_mismatch(tmp_path):
    patch = _entry_axis_fixture(
        tmp_path, delay_handoff={"status": "verified_candidate", "target_date": START.date().isoformat()},
        mismatch_split_policy=True,
    )
    try:
        semantics = monitor.entry_execution_tuning_semantics(tmp_path, START)
        assert semantics["status"] == "review_required"
        assert "entry_split_report_policy_generation_mismatch" in semantics["issues"]
        assert "pre_submit_delay_bootstrap_handoff_mismatch" in semantics["issues"]
    finally:
        patch.undo()


def test_entry_execution_semantics_detects_stale_delay_environment_when_unpublished(tmp_path):
    patch = _entry_axis_fixture(tmp_path, delay_env={
        "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED": "true",
        "KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE": "/old/pre_submit_delay_policy.json",
    })
    try:
        semantics = monitor.entry_execution_tuning_semantics(tmp_path, START)
        assert semantics["pre_submit_delay"]["handoff_status"] == "not_published"
        assert semantics["issues"]["pre_submit_delay_bootstrap_env_mismatch"] == 1
    finally:
        patch.undo()


def test_entry_execution_incident_persists_and_preserves_historical_gap():
    base = monitor.evaluate({}, {}, START)
    issue = {"issues": {"entry_split_report_policy_generation_mismatch": 1},
             "examples": [{"axis": "entry_split", "reason": "generation_binding_missing"}]}
    monitor.attach_entry_execution_tuning_semantics(base, issue)
    assert base["incidents"]["entry_execution_tuning_receipt_contract"]["status"] == "pending"
    later = monitor.evaluate({}, base, START + timedelta(minutes=5))
    monitor.attach_entry_execution_tuning_semantics(later, issue)
    assert later["incidents"]["entry_execution_tuning_receipt_contract"]["status"] == "active"
    resolved = monitor.evaluate({}, later, START + timedelta(minutes=10))
    monitor.attach_entry_execution_tuning_semantics(resolved, {"issues": {}, "examples": []})
    assert resolved["incidents"]["entry_execution_tuning_receipt_contract"]["status"] == "historical_unresolved"


@pytest.mark.parametrize("initial_status,initial_blocker", [
    ("guard_excluded", "common_guard_block:latency_state_danger"),
    ("source_gap", "exact_broker_capacity_missing"),
])
def test_conflicting_attempt_retains_enter_and_economic_history_without_recovery(initial_status, initial_blocker):
    early = event(stage="entry_ai_economic_source_gap", screen="caution",
        machine_observation_sha256="a" * 64,
        economic_source_monitor_projection=json.dumps({"status": initial_status,
            "blocker": initial_blocker}))
    late = event(action="BLOCK", screen="not_requested_machine_nonentry",
        stage="entry_ai_economic_source_gap", when=START + timedelta(seconds=3),
        machine_observation_sha256="b" * 64,
        economic_source_monitor_projection=json.dumps({"status": "source_gap",
            "blocker": "exact_broker_capacity_missing",
            "capacity_blocker": "capacity_observation_cache_miss_nonentry"}))
    source = report([late, early, early], START + timedelta(minutes=2))["submission_monitor"]
    row = source["rows"][0]
    assert row["mechanistic_action"] == "UNKNOWN"
    assert row["conflict_reasons"]
    assert row["enter_now_observed"] is True
    assert row["initial_observed_action"] == "ENTER_NOW"
    assert row["latest_observed_action"] == "BLOCK"
    assert len(row["decision_history"]) == 2
    assert len(row["economic_history"]) == 2
    assert row["economic_history"][0]["evidence"]["blocker"] == initial_blocker
    assert not monitor._nonentry_capacity_observation_gap(row)


def test_pending_pass_persists_then_exact_terminal_recovers():
    events = [event()]
    first = tick(events, 10)
    assert not active(first)
    second = tick(events, 15, first)
    assert [r["rule"] for r in active(second)] == ["source_or_submit_lineage_gap"]
    monitor.notify(second, "fixture.json", send=lambda text: None)
    events += [event(stage="order_bundle_submitted", when=START + timedelta(minutes=16), broker_order_no="b1")]
    final = tick(events, 20, second)
    assert not active(final)
    assert any(r["status"] == "recovered" for r in final["incidents"].values())


def revision_events():
    receipt = {"machine_revision_schema": "exact_machine_revision_v1"}
    early = event(screen="caution", machine_observation_sha256="a" * 64,
                  machine_revision_parent_sha256="", **receipt)
    late = event(action="BLOCK", screen="not_requested_machine_nonentry",
        when=START + timedelta(seconds=3), machine_observation_sha256="b" * 64,
        machine_revision_parent_sha256="a" * 64, **receipt)
    return early, late


def test_explicit_revision_chain_keeps_one_attempt_and_initial_enter():
    early, late = revision_events()
    result = sentinel._machine_primary_entry_funnel([late, early, early])
    assert len(result["evaluation_ledger"]) == 1
    row = result["evaluation_ledger"][0]
    assert row["conflict_reasons"] == []
    assert row["revision_chain_status"] == "valid"
    assert row["mechanistic_action"] == "BLOCK"
    assert row["enter_now_observed"] is True
    assert row["initial_observed_action"] == "ENTER_NOW"
    assert row["final_state"] == "machine_block_point_drop"


@pytest.mark.parametrize("mutation", ["missing", "parent", "same_hash", "owner",
    "screen", "policy", "tie", "reverse", "reopened", "prior_order", "foreign_attempt"])
def test_revision_chain_never_hides_unproven_or_executed_transition(mutation):
    early, late = revision_events()
    rows = [early, late]
    if mutation == "missing":
        late.fields.pop("machine_revision_schema")
    elif mutation == "parent":
        late.fields["machine_revision_parent_sha256"] = "c" * 64
    elif mutation == "same_hash":
        late.fields["machine_observation_sha256"] = "a" * 64
    elif mutation == "owner":
        early.fields["entry_primary_decision_owner"] = "auxiliary"
    elif mutation == "screen":
        early.fields["entry_ai_screen_status"] = "not_requested_machine_nonentry"
    elif mutation == "policy":
        late.fields["entry_mechanistic_policy_version"] = "v2"
    elif mutation in {"tie", "reverse"}:
        rows[1] = event(action="BLOCK", screen="not_requested_machine_nonentry",
            when=START if mutation == "tie" else START - timedelta(seconds=1), **{
                k: v for k, v in late.fields.items() if k.startswith("machine_")})
    elif mutation == "reopened":
        rows.append(event(when=START + timedelta(seconds=4), **early.fields))
    elif mutation == "prior_order":
        rows[0] = event(stage="order_bundle_submitted", broker_order_no="real-receipt", **early.fields)
    elif mutation == "foreign_attempt":
        late.fields["evaluation_attempt_id"] = "foreign"
    result = sentinel._machine_primary_entry_funnel(rows)
    assert any(r["conflict_reasons"] for r in result["evaluation_ledger"])


def test_revision_economics_does_not_backfill_initial_enter_gap():
    early, late = revision_events()
    early.fields["economic_source_monitor_projection"] = json.dumps(
        {"status": "source_gap", "blocker": "exact_broker_capacity_missing"})
    late.fields["economic_source_monitor_projection"] = json.dumps(
        {"status": "recorded_source_only", "seed_sha256": "later"})
    rows = [event(stage="entry_ai_economic_source_gap", when=START, **early.fields),
            event(stage="entry_ai_economic_plan_observed", when=START + timedelta(seconds=3), **late.fields)]
    row = monitor.snapshot(rows, START + timedelta(minutes=2))["rows"][0]
    assert row["revision_chain_status"] == "valid"
    assert row["economic_source"]["blocker"] == "exact_broker_capacity_missing"
    assert row["economic_source"]["machine_observation_sha256"] == "a" * 64


def test_distinct_revisions_can_have_distinct_economic_proofs():
    early, late = revision_events()
    rows = []
    for index, original in enumerate((early, late)):
        rows.append(event(stage="entry_ai_economic_plan_observed",
            when=START + timedelta(seconds=index * 3), **original.fields,
            economic_source_monitor_projection=json.dumps(
                {"status": "recorded_source_only", "seed_sha256": str(index)})))
    row = monitor.snapshot(rows, START + timedelta(minutes=2))["rows"][0]
    assert row["economic_source"]["status"] == "recorded_source_only"
    assert len(row["economic_history"]) == 2


@pytest.mark.parametrize("missing_index", [0, 1])
def test_economic_receipt_never_transfers_between_revisions(missing_index):
    originals = revision_events()
    rows = [originals[missing_index]]
    other = originals[1 - missing_index]
    rows.append(event(stage="entry_ai_economic_plan_observed", when=other.emitted_at,
        **other.fields, economic_source_monitor_projection=json.dumps(
            {"status": "recorded_source_only", "seed_sha256": "proof"})))
    row = monitor.snapshot(rows, START + timedelta(minutes=2))["rows"][0]
    assert row["economic_source"]["blocker"] == "economic_observation_event_missing"


@pytest.mark.parametrize("stage,extra", [("latency_block", {}), ("order_bundle_submitted", {"broker_order_no": "1"})])
def test_guard_and_acceptance_are_not_submission_gaps(stage, extra):
    events = [event(), event(stage=stage, when=START + timedelta(seconds=1), **extra)]
    state = tick(events, 10)
    assert not active(tick(events, 15, state))


def test_duplicate_stale_wrong_day_dry_run_never_alerts_or_recovers():
    state = tick([event()], 10)
    now = START + timedelta(minutes=10)
    payload = report([event(), event(3, when=now)], now)
    duplicate = monitor.evaluate(payload, state, now)
    assert duplicate["blocker"] == "duplicate_or_reversed_source_snapshot"
    assert duplicate["source_as_of"] == state["source_as_of"]
    for changed in ({"dry_run": True}, {"target_date": "2026-09-17"}):
        assert monitor.evaluate({**payload, **changed}, state, now)["status"] == "unobservable"
    assert monitor.evaluate(payload, state, now + timedelta(minutes=15))["status"] == "unobservable"


def test_ratios_require_new_promotions_and_policy_isolation():
    events = [event(i, "BLOCK", "not_requested_machine_nonentry") for i in range(10)]
    first = tick(events, 0)
    assert not active(tick(events, 15, first))  # same original promotions
    events += [event(30, "BLOCK", "not_requested_machine_nonentry", when=START + timedelta(minutes=15))]
    final = tick(events, 15, first)
    assert any(r["rule"] == "enter_now_scarcity" and r["category"] == "review_required" for r in active(final))
    split = [event(i, "BLOCK", "not_requested_machine_nonentry", policy_bundle_hash=str(i // 5) * 64) for i in range(10)]
    assert not active(tick(split, 15, tick(split, 0)))


def test_enter_now_scarcity_alert_is_machine_review_not_submit_failure():
    events = [event(i, "BLOCK", "not_requested_machine_nonentry") for i in range(10)]
    state = tick(events, 0)
    events.append(event(30, "RECHECK", "not_requested_machine_nonentry",
                        when=START + timedelta(minutes=15)))
    result = tick(events, 15, state)
    sent = []

    monitor.notify(result, "fixture.json", send=sent.append)

    assert len(sent) == 1
    assert sent[0].startswith("[기계판정 검토] 자동 매매 변경 없음")
    assert "BLOCK" in sent[0] and "RECHECK" in sent[0] and "ENTER_NOW" in sent[0]
    assert "주문 제출 실패·미체결 증거가 아닙니다" in sent[0]
    assert "Codex에서 원천과 제출 경로를 점검하세요" not in sent[0]


def test_enter_now_scarcity_recovers_on_new_valid_enter_now_without_fill():
    events = [event(i, "BLOCK", "not_requested_machine_nonentry") for i in range(10)]
    state = tick(events, 0)
    events.append(event(30, "BLOCK", "not_requested_machine_nonentry",
                        when=START + timedelta(minutes=15)))
    state = tick(events, 15, state)
    assert any(item["rule"] == "enter_now_scarcity" for item in active(state))

    events.append(event(31, "ENTER_NOW", "pass", when=START + timedelta(minutes=16)))
    recovered = tick(events, 20, state)
    scarcity = [item for item in recovered["incidents"].values()
                if item["rule"] == "enter_now_scarcity"]

    assert len(scarcity) == 1
    assert scarcity[0]["status"] == "recovered"
    assert recovered["runtime_effect"] is False


def test_veto_is_review_not_proven_bad_decision():
    events = [event(i, screen="veto") for i in range(10)]
    state = tick(events, 0)
    events += [event(11, screen="veto", when=START + timedelta(minutes=15))]
    result = tick(events, 15, state)
    assert active(result)[0]["rule"] == "ai_veto_concentration"
    assert active(result)[0]["category"] == "review_required"
    assert result["runtime_effect"] is False


def test_window_expiration_is_not_recovery():
    events = [event()]
    state = tick(events, 15, tick(events, 10))
    expired = tick([], 50, state)
    assert active(expired)
    assert not any(r["status"] == "recovered" for r in expired["incidents"].values())


def test_premarket_aliases_join_same_exact_attempt_but_not_distinct_attempts():
    events = [event(1, "SOURCE_INVALID", "not_requested_machine_source_invalid",
                    effective_venue="PREMARKET_KRX_LIKE", market_session_bucket=session)
              for session in ("KRX_LIKE_PREMARKET", "PREMARKET_KRX_LIKE")]
    rows = monitor.snapshot(events, START)["rows"]
    assert len(rows) == 1
    assert rows[0]["session_bucket"] == "PREMARKET_KRX_LIKE"
    assert rows[0]["economic_source"]["blocker"] is None
    events.append(event(2, "SOURCE_INVALID", "not_requested_machine_source_invalid",
                        effective_venue="PREMARKET_KRX_LIKE", market_session_bucket="KRX_LIKE_PREMARKET"))
    assert len(monitor.snapshot(events, START)["rows"]) == 2


def test_source_invalid_alert_names_actual_preflight_blocker():
    events = [event(action="SOURCE_INVALID", screen="not_requested_machine_source_invalid",
                    entry_source_invalid_primary_blocker="runtime_preflight_artifact_not_ready",
                    entry_source_invalid_blockers="runtime_preflight_artifact_not_ready")]
    state = tick(events, 15, tick(events, 10))
    sent = []
    monitor.notify(state, "fixture.json", send=sent.append)
    assert sent and "첫 결손: runtime_preflight_artifact_not_ready" in sent[0]
    assert "첫 결손: economic_observation_event_missing" not in sent[0]


def test_existing_alias_incident_is_preserved_as_superseded_not_recovered():
    import copy
    import hashlib
    events = [event(action="SOURCE_INVALID", screen="not_requested_machine_source_invalid",
                    effective_venue="PREMARKET_KRX_LIKE", market_session_bucket="PREMARKET_KRX_LIKE")]
    state = tick(events, 15, tick(events, 10))
    canonical = active(state)[0]
    old = copy.deepcopy(canonical)
    old["scope"] = old["scope"].replace("|PREMARKET_KRX_LIKE|", "|KRX_LIKE_PREMARKET|")
    old["evidence_ids"] = [x.replace("|PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE|", "|PREMARKET_KRX_LIKE|KRX_LIKE_PREMARKET|") for x in old["evidence_ids"]]
    old_key = hashlib.sha256(f"{old['scope']}|{old['rule']}".encode()).hexdigest()[:24]
    state["incidents"][old_key] = old
    result = tick(events, 20, state)
    assert len(active(result)) == 1
    assert active(result)[0]["count"] == 1
    assert result["incidents"][old_key]["status"] == "superseded_alias"
    assert result["incidents"][old_key]["evidence_ids"] == old["evidence_ids"]


def test_required_feature_recheck_is_guard_excluded_not_missing_economics():
    rows = monitor.snapshot([event(action="RECHECK", screen="not_requested_required_feature_insufficient")], START)["rows"]
    assert rows[0]["conflict_reasons"] == []
    assert rows[0]["final_state"] == "machine_recheck_observation"
    assert rows[0]["economic_source"]["status"] == "guard_excluded"
    invalid = monitor.snapshot([event(action="ENTER_NOW", screen="not_requested_required_feature_insufficient")], START)["rows"]
    assert "machine_enter_ai_screen_not_requested" in invalid[0]["conflict_reasons"]
    ordinary = monitor.snapshot([event(action="RECHECK", screen="not_requested_machine_nonentry")], START)["rows"]
    assert ordinary[0]["economic_source"]["status"] == "source_gap"


def test_auxiliary_ai_semantic_receipt_matches_effective_screen():
    policy_hash = "c" * 64
    assessment = {
        "schema": "auxiliary_effective_assessment_v1",
        "raw_verdict": "PASS", "effective_verdict": "PASS",
        "reason": "raw_verdict_preserved", "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": policy_hash, "validation_errors": [],
    }
    candidate = event(
        entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment=assessment,
        entry_ai_soft_policy_sha256=policy_hash,
        entry_ai_advisory_verdict="PASS",
        entry_ai_advisory_contract_valid="True",
    )
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert row["auxiliary_ai_semantics"]["status"] == "receipt_match"
    assert row["conflict_reasons"] == []
    projection = monitor.snapshot([candidate], START)
    assert projection["auxiliary_ai_semantic_status_counts"] == {"receipt_match": 1}
    assert projection["rows"][0]["auxiliary_ai_semantics"]["soft_policy_sha256"] == policy_hash


def test_auxiliary_legacy_python_repr_echo_keeps_valid_pass_semantics():
    assessment = {
        "schema": "auxiliary_effective_assessment_v1",
        "raw_verdict": "PASS", "effective_verdict": "PASS",
        "reason": "raw_verdict_preserved", "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": None, "validation_errors": [],
    }
    candidate = event(entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment=str(assessment), entry_ai_advisory_verdict="PASS",
        entry_ai_soft_policy_sha256="None")
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert row["auxiliary_ai_semantics"]["status"] == "receipt_match"
    assert row["conflict_reasons"] == []
    malformed = event(entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment="{'schema': unknown()}", entry_ai_advisory_verdict="PASS")
    invalid = sentinel._machine_primary_entry_funnel([malformed])["evaluation_ledger"][0]
    assert "auxiliary_assessment_schema_invalid" in invalid["conflict_reasons"]


def test_auxiliary_v2_semantic_receipt_requires_selected_profile():
    assessment = {
        "schema": "auxiliary_effective_assessment_v2",
        "raw_verdict": "VETO", "effective_verdict": "PASS",
        "reason": "soft_veto_evidence_below_policy",
        "selected_profile": "leaf_0", "selected_profile_sha256": "e" * 64,
        "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": "c" * 64, "validation_errors": [],
    }
    candidate = event(
        screen="pass", entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v2",
        entry_ai_effective_assessment=assessment,
        entry_ai_soft_policy_sha256="c" * 64,
        entry_ai_selected_profile="leaf_0",
        entry_ai_advisory_verdict="VETO",
        entry_ai_advisory_contract_valid="True",
    )
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert row["auxiliary_ai_semantics"]["status"] == "receipt_match"
    missing = event(**{**candidate.fields, "entry_ai_selected_profile": None})
    bad = sentinel._machine_primary_entry_funnel([missing])["evaluation_ledger"][0]
    assert "auxiliary_selected_profile_mismatch" in bad["conflict_reasons"]


@pytest.mark.parametrize("raw,effective,reason,policy,expected_issue", [
    ("VETO", "PASS", "soft_veto_evidence_below_policy", None,
     "auxiliary_raw_effective_transition_invalid"),
    ("PASS", "VETO", "raw_verdict_preserved", "c" * 64,
     "auxiliary_raw_effective_transition_invalid"),
    ("PASS", "PASS", "soft_veto_evidence_below_policy", "c" * 64,
     "auxiliary_transition_reason_invalid"),
])
def test_auxiliary_semantics_rejects_impossible_soft_transitions(
    raw, effective, reason, policy, expected_issue,
):
    assessment = {"schema": "auxiliary_effective_assessment_v1",
        "raw_verdict": raw, "effective_verdict": effective, "reason": reason,
        "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": policy, "validation_errors": []}
    candidate = event(screen=effective.lower(),
        entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment=assessment,
        entry_ai_soft_policy_sha256=policy, entry_ai_advisory_verdict=raw)
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert expected_issue in row["conflict_reasons"]


def test_auxiliary_current_prompt_missing_receipt_is_observable_gap():
    from src.engine.ai_prompt_contracts import ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION
    candidate = event(ai_prompt_version=ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION)
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert "auxiliary_current_receipt_missing" in row["conflict_reasons"]
    legacy = sentinel._machine_primary_entry_funnel([event()])["evaluation_ledger"][0]
    assert legacy["auxiliary_ai_semantics"]["status"] == "legacy_uninstrumented"


def test_auxiliary_current_prompt_receipt_needs_prompt_identity():
    from src.engine.ai_prompt_contracts import ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION
    assessment = {"schema": "auxiliary_effective_assessment_v1",
        "raw_verdict": "PASS", "effective_verdict": "PASS",
        "reason": "raw_verdict_preserved", "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": None, "validation_errors": []}
    candidate = event(ai_prompt_version=ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
        entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment=assessment,
        entry_ai_advisory_verdict="PASS")
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert "auxiliary_current_prompt_hash_missing_or_invalid" in row["conflict_reasons"]


def test_auxiliary_transport_without_response_is_not_economic_rejection():
    candidate = event(screen="not_evaluated_transport",
        entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v2")
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert row["auxiliary_ai_semantics"]["status"] == "not_evaluated"
    assert row["auxiliary_ai_semantics"]["issues"] == []


def test_auxiliary_ai_semantic_receipt_mismatch_is_reported_not_authorized():
    assessment = {
        "schema": "auxiliary_effective_assessment_v1",
        "raw_verdict": "VETO", "effective_verdict": "VETO",
        "validated_response_sha256": "d" * 64,
        "soft_policy_sha256": "c" * 64, "validation_errors": [],
    }
    candidate = event(
        entry_ai_auxiliary_contract_version="auxiliary_effective_assessment_v1",
        entry_ai_effective_assessment=assessment,
        entry_ai_soft_policy_sha256="c" * 64,
        entry_ai_advisory_verdict="VETO",
    )
    row = sentinel._machine_primary_entry_funnel([candidate])["evaluation_ledger"][0]
    assert row["auxiliary_ai_semantics"]["status"] == "review_required"
    assert "auxiliary_effective_verdict_screen_mismatch" in row["conflict_reasons"]
    assert row["auxiliary_ai_semantics"]["runtime_effect"] is False


@pytest.mark.parametrize("missing", [None, "None", "null", "-", "unknown", "0", ""])
def test_missing_identity_alias_does_not_mask_explicit_machine_receipt(missing):
    base = event(action="BLOCK", screen="not_requested_machine_nonentry")
    terminal = event(action="BLOCK", screen="not_requested_machine_nonentry",
        stage="ai_confirmed_terminal_no_budget", policy_bundle_hash=missing,
        machine_bundle_sha256="b" * 64, effective_venue=missing, venue="NXT",
        market_session_bucket=missing, session_bucket="nxt_premarket")
    result = monitor.snapshot([base, terminal], START)
    assert result["identity_missing_events"] == 0
    assert len(result["rows"]) == 1
    absent = event(policy_bundle_hash=missing, machine_bundle_sha256=missing)
    assert sentinel._machine_primary_evaluation_key(absent) == ""


def test_fixed_watch_admission_is_not_a_scanner_identity_gap_or_denominator():
    generation = hashlib.sha256(b"2026-09-21|005930|nxt_premarket|nxt_only").hexdigest()
    fixed = event(action="BLOCK", screen="not_requested_machine_nonentry",
        scanner_promotion_id="None", watch_origin="MAIN_FIXED_WATCH",
        watch_admission_id="FIXED-2026-09-21-005930-nxt_premarket-nxt_only-abcdef123456",
        watch_generation_id=generation)
    funnel = sentinel._machine_primary_entry_funnel([fixed])
    assert funnel["source_event_count"] == 1
    assert funnel["fixed_watch_identified_event_count"] == 1
    assert funnel["evaluation_identity_missing_event_count"] == 0
    assert funnel["count_conservation"]["identified_plus_identity_missing_equals_raw"]
    assert funnel["evaluation_count"] == 0
    assert funnel["promotion_lifecycle"]["unique_promotion_count"] == 0
    observed = monitor.snapshot([fixed], START)
    assert observed["identity_observation"]["status"] == "unobservable"
    assert observed["fixed_watch_identity_observation"]["identified_event_count"] == 1
    assert observed["missing_identity_evidence"] == []
    old = {"schema": monitor.SCHEMA, "date": START.date().isoformat(),
        "source_as_of": (START - timedelta(seconds=1)).isoformat(),
        "incidents": {"unbound_machine_identity": {
            "status": "active", "scope": "unbound", "rule": "source_identity_missing",
            "evidence_ids": observed["fixed_watch_identified_evidence"], "count": 1,
            "first_seen": START.isoformat()}}}
    corrected = monitor.evaluate(report([fixed], START), old, START)
    assert "unbound_machine_identity" not in corrected["incidents"]
    assert corrected["incidents"]["unbound_machine_identity_reclassified_fixed_watch"]["status"] == "reclassified"
    assert corrected["fixed_watch_identity_observation"]["identified_event_count"] == 1
    assert corrected["notification_pending"] == []
    quiet_at = START + timedelta(minutes=11)
    quiet = report([fixed], quiet_at)
    quiet_corrected = monitor.evaluate(quiet, old, quiet_at)
    assert quiet_corrected["status"] == "unobservable"
    assert quiet_corrected["blocker"] == "missing_stale_or_noncurrent_sentinel_evidence"
    assert "unbound_machine_identity" not in quiet_corrected["incidents"]
    assert quiet_corrected["incidents"]["unbound_machine_identity_reclassified_fixed_watch"]["status"] == "reclassified"
    wrong_date = {**quiet, "target_date": "2026-09-20"}
    assert "unbound_machine_identity" in monitor.evaluate(wrong_date, old, quiet_at)["incidents"]


def test_fixed_watch_and_scanner_machine_attempts_remain_separate():
    generation = hashlib.sha256(b"2026-09-21|005930|nxt_premarket|nxt_only").hexdigest()
    fixed = event(action="BLOCK", screen="not_requested_machine_nonentry",
        scanner_promotion_id="-", watch_origin="MAIN_FIXED_WATCH",
        watch_admission_id="FIXED-2026-09-21-005930-nxt_premarket-nxt_only-abcdef123456",
        watch_generation_id=generation)
    scanner = event(1, action="RECHECK", screen="not_requested_machine_nonentry")
    funnel = sentinel._machine_primary_entry_funnel([fixed, scanner])
    assert funnel["source_event_count"] == 2
    assert funnel["identified_source_event_count"] == 2
    assert funnel["fixed_watch_identified_event_count"] == 1
    assert funnel["scanner_identified_source_event_count"] == 1
    assert funnel["evaluation_count"] == 1
    assert funnel["evaluation_ledger"][0]["scanner_promotion_id"] == "parent-1"
    assert funnel["count_conservation"]["identified_plus_identity_missing_equals_raw"]


def test_fixed_watch_missing_or_conflicting_identity_stays_a_source_gap():
    generation = hashlib.sha256(b"2026-09-21|005930|nxt_premarket|nxt_only").hexdigest()
    base = dict(action="BLOCK", screen="not_requested_machine_nonentry",
        watch_origin="MAIN_FIXED_WATCH",
        watch_admission_id="FIXED-2026-09-21-005930-nxt_premarket-nxt_only-abcdef123456",
        watch_generation_id=generation)
    missing = event(scanner_promotion_id="None", watch_generation_id="", **{
        key: value for key, value in base.items() if key != "watch_generation_id"})
    conflict = event(1, scanner_promotion_id="scanner-claim", **base)
    malformed = event(2, scanner_promotion_id="None", watch_generation_id="f" * 64, **{
        key: value for key, value in base.items() if key != "watch_generation_id"})
    observed = monitor.snapshot([missing, conflict, malformed], START)
    assert observed["identity_observation"]["status"] == "current_gap"
    assert observed["identity_observation"]["missing_event_count"] == 3
    assert observed["fixed_watch_identity_observation"]["identity_missing_event_count"] == 3
    examples = observed["identity_observation"]["examples"]
    assert any("watch_generation_id" in row["missing_fields"] for row in examples)
    assert any("scanner_promotion_id" in row["conflicting_fields"] for row in examples)
    assert any("fixed_watch_admission_generation_invalid" in row["identity_contract_issues"]
        for row in examples)
    assert observed["rows"] == []


def test_fixed_watch_identity_alert_names_conflict_instead_of_legacy_missing_field():
    generation = hashlib.sha256(b"2026-09-21|005930|nxt_premarket|nxt_only").hexdigest()
    bad = event(action="BLOCK", screen="not_requested_machine_nonentry",
        when=START + timedelta(minutes=9), scanner_promotion_id="nan",
        watch_origin="MAIN_FIXED_WATCH",
        watch_admission_id="FIXED-2026-09-21-005930-nxt_premarket-nxt_only-abcdef123456",
        watch_generation_id=generation)
    state = tick([bad], 10)
    state = tick([bad], 15, state)
    sent = []
    monitor.notify(state, "fixture.json", send=sent.append)
    assert len(sent) == 1
    assert "충돌 필드: scanner_promotion_id" in sent[0]
    assert "누락 필드: 미확인(구형 이력)" not in sent[0]


def test_missing_identity_detected_without_fake_denominator():
    events = [event(evaluation_attempt_id="", scanner_promotion_id="")]
    state = tick(events, 10)
    result = tick(events, 15, state)
    incident = result['incidents']['unbound_machine_identity']
    assert result['identity_observation']['missing_event_count'] == 0
    assert incident['count'] == 1
    assert incident['status'] == 'historical_unresolved'
    assert incident['current_status'] == 'no_recurrence_observed'
    assert incident['examples'][0]['missing_fields'] == ['scanner_promotion_id', 'evaluation_attempt_id']
    assert not active(result)


def test_identity_delayed_history_is_silent_and_keeps_occurrence_details():
    bad = event(evaluation_attempt_id='None')
    state = tick([bad], 10)
    sent = []
    monitor.notify(state, 'fixture.json', send=sent.append)
    assert sent == []
    assert state['incidents']['unbound_machine_identity']['examples'][0]['stock_code'] == '005930'
    old = state['incidents']['unbound_machine_identity']
    expired = tick([], 50, state)
    item = expired['incidents']['unbound_machine_identity']
    assert item['status'] == 'historical_unresolved'
    for key in ('count', 'evidence_ids', 'examples', 'occurred_first_at', 'occurred_last_at'):
        assert item[key] == old[key]
    monitor.notify(expired, 'fixture.json', send=sent.append)
    assert sent == []  # Neither disappearance nor fresh good rows repair history.


def test_identity_current_recurrence_rearms_without_losing_prior_history():
    state = tick([event(evaluation_attempt_id='')], 10)
    monitor.notify(state, 'fixture.json', send=lambda _: None)
    original = state['incidents']['unbound_machine_identity'].copy()
    for minutes in (50, 55):
        bad = [event(i, evaluation_attempt_id='', when=START+timedelta(minutes=i))
               for i in (40, 49, 54) if i <= minutes]
        state = tick(bad, minutes, state)
    item = state['incidents']['unbound_machine_identity']
    assert item['status'] == 'active' and item['current_status'] == 'current_gap'
    assert item['history'][0]['evidence_ids'] == original['evidence_ids']
    assert 'unbound_machine_identity' in state['notification_pending']
    sent=[]
    monitor.notify(state,'fixture.json',send=sent.append)
    assert len(sent)==1 and 'current_gap' in sent[0]


def test_identity_no_machine_rows_stale_and_legacy_are_not_no_recurrence():
    import copy
    state = tick([event(evaluation_attempt_id='')], 10)
    before = copy.deepcopy(state)
    now = START + timedelta(minutes=50)
    market = event(when=now, entry_primary_decision_owner='', entry_mechanistic_action='')
    current = monitor.evaluate(report([market], now), state, now)
    assert current['identity_observation']['status'] == 'unobservable'
    assert current['incidents']['unbound_machine_identity']['current_status'] == 'unobservable'
    assert not current['notification_pending']
    stale = monitor.evaluate(report([market], now), state, now+timedelta(minutes=20))
    assert stale['identity_observation']['status'] == 'unobservable'
    assert stale['incidents'] == before['incidents'] and state == before
    legacy = report([event(when=now)], now)
    legacy['submission_monitor'].pop('identity_observation')
    assert monitor.evaluate(legacy,state,now)['identity_observation']['status']=='unobservable'


def test_identity_legacy_incident_preserved_and_missing_details_not_fabricated():
    state=tick([event(evaluation_attempt_id='')],10)
    old=state['incidents']['unbound_machine_identity']
    old.update(status='active',notified_status='active',examples=[],count=104)
    old.pop('occurred_first_at');old.pop('occurred_last_at')
    result=tick([],50,state)
    item=result['incidents']['unbound_machine_identity']
    assert item['count']==104 and item['evidence_ids']==old['evidence_ids']
    assert item['status']=='historical_unresolved'
    sent=[];monitor.notify(result,'fixture.json',send=sent.append)
    assert len(sent)==1 and '현재 정상 관측' in sent[0]
    assert '점검하세요' not in sent[0] and 'recovered' not in sent[0]


def test_identity_legacy_details_backfill_requires_exact_retained_hash():
    import copy
    bad = event(evaluation_attempt_id='')
    state = tick([bad],10)
    old = state['incidents']['unbound_machine_identity']
    old.update(status='active',examples=[])
    old.pop('occurred_first_at');old.pop('occurred_last_at')
    before = copy.deepcopy(state)
    result = tick([bad,event(2,evaluation_attempt_id='')],50,state)
    assert state == before
    item = result['incidents']['unbound_machine_identity']
    assert item['count']==1 and item['evidence_ids']==old['evidence_ids']
    assert len(item['examples'])==1 and item['examples'][0]['record_id']=='0'
    assert item['occurred_first_at']=='2026-09-21T08:05:00+09:00'
    assert item['detail_basis']=='existing_cache_exact_evidence_hash_match'
    assert item['status']=='historical_unresolved'


def test_new_identity_gap_rearms_immediately_and_reports_current_occurrence():
    old_bad=event(evaluation_attempt_id='')
    state=tick([old_bad],10)
    monitor.notify(state,'fixture.json',send=lambda _:None)
    now_bad=event(2,evaluation_attempt_id='',when=START+timedelta(minutes=15))
    result=tick([old_bad,now_bad],15,state)
    assert result['identity_observation']['status']=='current_gap'
    assert result['incidents']['unbound_machine_identity']['status']=='active'
    assert 'unbound_machine_identity' in result['notification_pending']
    sent=[]
    monitor.notify(result,'fixture.json',send=sent.append)
    assert '2026-09-21T08:20:00+09:00' in sent[0]
    assert '2026-09-21T08:05:00+09:00' not in sent[0]


def test_historical_identity_metadata_is_bounded_and_never_changes_current_denominator():
    events=[event(i,evaluation_attempt_id='',when=START+timedelta(seconds=i)) for i in range(200)]
    now=START+timedelta(minutes=60)
    value=monitor.snapshot(list(reversed(events))+[event(999,when=now)],now)
    assert len(value['historical_identity_samples'])==128
    assert value['identity_missing_events']==0
    assert value['missing_identity_evidence']==[]
    assert len(value['rows'])==1


def test_active_to_historical_preserves_original_count_when_window_shrinks():
    bad=event(evaluation_attempt_id='')
    state=tick([bad],10)
    item=state['incidents']['unbound_machine_identity']
    item.update(status='active',count=104,evidence_ids=item['evidence_ids']+['old-other-proof'])
    result=tick([bad],15,state)
    historical=result['incidents']['unbound_machine_identity']
    assert historical['status']=='historical_unresolved'
    assert historical['count']==104
    assert historical['evidence_ids']==item['evidence_ids']


def test_notify_failure_retries_and_success_deduplicates():
    state = tick([event()], 15, tick([event()], 10))
    def fail(text):
        raise OSError("must not log secrets")
    monitor.notify(state, "fixture.json", send=fail)
    assert state["notification_status"] == "retry_required:OSError"
    sent = []
    monitor.notify(state, "fixture.json", send=sent.append)
    assert len(sent) == 1
    next_state = tick([event()], 20, state)
    monitor.notify(next_state, "fixture.json", send=sent.append)
    assert len(sent) == 1


def test_recheck_retries_do_not_inflate_promotion_denominator():
    events = [event(i, "RECHECK", "not_requested_machine_nonentry", scanner_promotion_id="same") for i in range(20)]
    result = tick(events, 15, tick(events, 0))
    assert not active(result)
    assert max(s["unique_promotions"] for s in result["scopes"].values()) == 2


def test_stored_pipeline_normalization_retains_terminal_and_premarket(tmp_path, monkeypatch):
    import json
    path = tmp_path / "pipeline.jsonl"
    events = [event(), event(stage="latency_block", when=START + timedelta(seconds=1))]
    payloads = [{"event_type": "pipeline_event", "pipeline": e.pipeline, "stage": e.stage,
        "stock_name": e.stock_name, "stock_code": e.stock_code, "record_id": e.record_id,
        "fields": e.fields, "emitted_at": e.emitted_at.isoformat()} for e in events]
    path.write_text("\n".join(json.dumps(p) for p in payloads) + "\n")
    monkeypatch.setattr(sentinel, "_pipeline_events_path", lambda day: path)
    monkeypatch.setattr(sentinel, "_event_cache_dir", lambda: tmp_path / "cache")
    stored = sentinel.load_pipeline_events("2026-09-21", use_cache=True, exclude_summary_stages=True)
    first = tick(stored, 10)
    result = tick(stored, 15, first)
    assert not active(result)
    assert any(s["guard_blocked"] == 1 for s in result["scopes"].values())


def test_wrapper_observes_source_gaps_even_if_sentinel_fails_but_not_on_dry_run(tmp_path):
    import os
    import subprocess
    from pathlib import Path
    project = Path(__file__).resolve().parents[2]
    py = tmp_path / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    calls = tmp_path / "calls.txt"
    py.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$CALLS"\n'
                  'if [[ "$FAIL_SENTINEL" == "1" && "$*" == *"src.engine.buy_funnel_sentinel"* ]]; then exit 7; fi\n')
    py.chmod(0o755)
    env = {**os.environ, "PROJECT_DIR": str(tmp_path), "CALLS": str(calls),
        "BUY_FUNNEL_SENTINEL_COOLDOWN_SEC": "0"}
    wrapper = project / "deploy/run_buy_funnel_sentinel_intraday.sh"
    subprocess.run(["bash", str(wrapper), "2026-09-21"], env=env, check=True, capture_output=True)
    assert "submission_bottleneck_monitor" in calls.read_text()
    calls.write_text("")
    failed = subprocess.run(["bash", str(wrapper), "2026-09-21"],
        env={**env, "FAIL_SENTINEL": "1"}, capture_output=True)
    assert failed.returncode == 7
    assert "submission_bottleneck_monitor" in calls.read_text()
    assert "--source-only" in calls.read_text()
    calls.write_text("")
    subprocess.run(["bash", str(wrapper), "2026-09-21"], env={**env, "BUY_FUNNEL_SENTINEL_DRY_RUN": "1"}, check=True, capture_output=True)
    assert "submission_bottleneck_monitor" not in calls.read_text()


def test_sentinel_publishes_compact_atomic_notification_source(tmp_path, monkeypatch):
    import json
    now = START + timedelta(minutes=15)
    payload = report([event()], now)
    monkeypatch.setattr(sentinel, "_report_dir", lambda: tmp_path)
    monkeypatch.setattr(sentinel, "build_markdown", lambda report: "diagnostic")
    paths = sentinel.save_report_artifacts({**payload, "large_diagnostic": "x" * 10000})
    source = json.loads(__import__('pathlib').Path(paths["submission_monitor"]).read_text())
    assert "large_diagnostic" not in source
    assert source == payload


@pytest.mark.parametrize("valid", [True, False])
def test_known_producer_nonbudget_terminal_closes_only_exact_contract(valid):
    fields = dict(terminal_reason="first_ai_wait_big_bite_not_confirmed", source_stage="first_ai_wait",
        actual_order_submitted="false", broker_order_forbidden="true", allowed_runtime_apply="false")
    if not valid:
        fields["terminal_reason"] = "unknown_terminal_no_budget"
    events = [event(), event(stage="ai_confirmed_terminal_no_budget", when=START + timedelta(seconds=1), **fields)]
    result = tick(events, 15, tick(events, 10))
    assert bool(active(result)) is not valid


def test_missing_economic_producer_detected_even_after_successful_submission():
    events = [event(), event(stage='order_bundle_submitted', when=START+timedelta(seconds=1), broker_order_no='b1')]
    state = {}
    for minutes in (10, 15):
        now = START+timedelta(minutes=minutes)
        state = monitor.evaluate(report(events+[event(999, when=now)], now), state, now)
    gaps = [r for r in active(state) if r['rule']=='economic_producer_gap']
    assert len(gaps)==1
    assert gaps[0]['examples'][0]['economic_source']['blocker']=='economic_observation_event_missing'
    assert not any(r['rule']=='source_or_submit_lineage_gap' for r in active(state))


@pytest.mark.parametrize('status,blocker,expected', [
    ('source_gap','structured_pre_ai_observation_append_failed','source_gap'),
    ('source_gap','common_guard_block:spread','guard_excluded'),
    ('source_gap','owner_sizing_zero_or_invalid','guard_excluded'),
    ('unsupported_scope','unsupported_pre_ai_session_market_route_contract','unsupported_scope'),
    ('recorded_source_only','','source_gap'),
])
def test_economic_producer_diagnosis_keeps_guard_and_unsupported_separate(status, blocker, expected):
    fields={'entry_economic_source_status':status,'entry_economic_source_blocker':blocker}
    assert monitor.economic_evidence(fields)['status']==expected


def test_cache_retains_economic_failure_and_proof_without_full_plan():
    import json
    e=event(stage='entry_ai_economic_source_gap',entry_economic_source_status='source_gap',
            entry_economic_source_blocker='exact_broker_capacity_missing')
    raw=dict(event_type='pipeline_event',pipeline=e.pipeline,stage=e.stage,stock_name='fixture',stock_code=e.stock_code,
             record_id=e.record_id,emitted_at=e.emitted_at.isoformat(),fields=e.fields)
    cached=sentinel._payload_to_cache_row(raw,exclude_summary_stages=True)
    assert cached is not None
    assert json.loads(cached['fields']['economic_source_monitor_projection'])['blocker']=='exact_broker_capacity_missing'
    projection=monitor.snapshot([sentinel._event_from_cache_row(cached)],START+timedelta(minutes=15))
    assert projection['rows'][0]['economic_source']['status']=='source_gap'


def test_economic_incident_requires_proof_not_broker_terminal_to_recover():
    state={}
    for minutes in (10,15,20,25):
        now=START+timedelta(minutes=minutes)
        payload=report([event(),event(stage='order_bundle_submitted',when=START+timedelta(seconds=1),broker_order_no='b1'),event(999,when=now)],now)
        if minutes==25:
            payload['submission_monitor']['rows'][0]['economic_source']={'status':'recorded_source_only'}
        state=monitor.evaluate(payload,state,now)
        if minutes==20:
            assert any(r['rule']=='economic_producer_gap' for r in active(state))
    assert any(r['rule']=='economic_producer_gap' and r['status']=='recovered' for r in state['incidents'].values())


def nonentry_gap(action="BLOCK", **extra):
    return event(action=action, screen="not_requested_machine_nonentry",
        stage="entry_ai_economic_source_gap", entry_economic_source_status="source_gap",
        entry_economic_source_blocker="exact_broker_capacity_missing",
        entry_economic_capacity_blocker="capacity_observation_cache_miss_nonentry", **extra)


@pytest.mark.parametrize("action", ["BLOCK", "RECHECK"])
def test_explicit_nonentry_cache_miss_is_visible_coverage_not_submit_alert(action):
    state = {}
    for minutes in (10, 15):
        now = START + timedelta(minutes=minutes)
        payload = report([nonentry_gap(action), event(999, when=now)], now)
        state = monitor.evaluate(payload, state, now)
    scope = next(iter(state["scopes"].values()))
    assert scope["nonentry_capacity_observation_gaps"] == 1
    assert scope["economic_gap_action_counts"][action] == 1
    assert scope["economic_status_counts"]["source_gap"] == 2
    assert not any(r["rule"] == "economic_producer_gap" for r in active(state))
    row = payload["submission_monitor"]["rows"][0]
    assert row["economic_source"]["status"] == "source_gap"
    assert row["economic_source"]["valid_economics"] is False


@pytest.mark.parametrize("defect", ["enter", "unknown_reason", "conflict", "accepted", "screen", "terminal", "contract"])
def test_nonentry_coverage_never_hides_execution_or_unknown_contract_gaps(defect):
    row = monitor.snapshot([nonentry_gap()], START)["rows"][0]
    if defect == "enter": row["mechanistic_action"] = "ENTER_NOW"
    elif defect == "unknown_reason": row["economic_source"].pop("capacity_blocker")
    elif defect == "conflict": row["conflict_reasons"] = ["conflicting_machine_actions"]
    elif defect == "accepted": row["broker_acceptance_observed"] = True
    elif defect == "screen": row["ai_screen_status"] = "pass"
    elif defect == "terminal": row["final_state"] = "submit_pipeline_reached"
    else: row["economic_source"]["blocker"] = "frozen_operating_contract_missing"
    assert not monitor._nonentry_capacity_observation_gap(row)


def test_old_slim_projection_recovers_detail_only_from_retained_field():
    import json
    raw_event = nonentry_gap(economic_source_monitor_projection=json.dumps({
        "status": "source_gap", "blocker": "exact_broker_capacity_missing", "valid_economics": False}))
    raw = dict(event_type="pipeline_event", pipeline=raw_event.pipeline, stage=raw_event.stage,
        stock_name="fixture", stock_code=raw_event.stock_code, record_id=raw_event.record_id,
        emitted_at=raw_event.emitted_at.isoformat(), fields=raw_event.fields)
    cached = sentinel._payload_to_cache_row(raw, exclude_summary_stages=True)
    projection = json.loads(cached["fields"]["economic_source_monitor_projection"])
    assert projection.pop("capacity_blocker") == "capacity_observation_cache_miss_nonentry"
    cached["fields"]["economic_source_monitor_projection"] = json.dumps(projection)
    row = monitor.snapshot([sentinel._event_from_cache_row(cached)], START)["rows"][0]
    assert monitor._nonentry_capacity_observation_gap(row)
    cached["fields"].pop("entry_economic_capacity_blocker")
    row = monitor.snapshot([sentinel._event_from_cache_row(cached)], START)["rows"][0]
    assert not monitor._nonentry_capacity_observation_gap(row)


def test_reclassification_retains_history_is_not_recovery_and_rearms_real_gap():
    import copy
    state = {}
    for minutes in (10, 15, 20):
        now = START + timedelta(minutes=minutes)
        payload = report([nonentry_gap(), event(999, when=now)], now)
        if minutes < 20:
            payload["submission_monitor"]["rows"][0]["enter_now_observed"] = True
        before = copy.deepcopy(state)
        result = monitor.evaluate(payload, state, now)
        assert state == before
        state = result
        if minutes == 15:
            old = copy.deepcopy(next(r for r in active(state) if r["rule"] == "economic_producer_gap"))
            monitor.notify(state, "fixture.json", send=lambda _: None)
    item = next(r for r in state["incidents"].values() if r["rule"] == "economic_producer_gap")
    assert item["status"] == "observation_only_unresolved"
    for key in ("count", "evidence_ids", "examples", "first_seen"):
        assert item[key] == old[key]
    assert not state["notification_pending"]
    # A later real/unknown gap must start a new persistence interval.
    for minutes in (25, 30):
        now = START + timedelta(minutes=minutes)
        payload = report([nonentry_gap(), event(999, when=now)], now)
        payload["submission_monitor"]["rows"][0]["economic_source"]["capacity_blocker"] = "capacity_scope_unavailable"
        payload["submission_monitor"]["rows"][0]["enter_now_observed"] = True
        state = monitor.evaluate(payload, state, now)
    assert any(r["rule"] == "economic_producer_gap" for r in active(state))
    new = next(r for r in active(state) if r["rule"] == "economic_producer_gap")
    assert new["history"][0]["status"] == "observation_only_unresolved"
    assert new["history"][0]["evidence_ids"] == old["evidence_ids"]
    assert state["notification_pending"]


def test_economic_proof_conflict_cannot_be_overwritten_by_later_duplicate():
    import json
    events=[event(stage='entry_ai_economic_plan_observed',economic_source_monitor_projection=json.dumps({
        'status':'recorded_source_only','seed_sha256':value})) for value in ('a','b','a')]
    rows=monitor.snapshot(events,START)['rows']
    assert rows[0]['economic_source']['blocker']=='economic_observation_conflicting_proofs'


def test_cache_upgrade_requires_zero_census_for_all_new_stages(tmp_path, monkeypatch):
    import json
    from src.engine import observation_source_quality_audit as audit
    monkeypatch.setattr(sentinel, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(audit, '_read_raw_contract_projection', lambda *a: {'valid':True})
    raw=tmp_path/'raw.jsonl';raw.write_text('')
    cache=sentinel._event_cache_dir();cache.mkdir(parents=True)
    (cache/'buy_funnel_sentinel_events_2026-09-17.meta.json').write_text(json.dumps({'schema_version':12}))
    path=tmp_path/'report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.json'
    path.parent.mkdir(parents=True)
    payload={'target_date':'2026-09-17','source':{'generation':audit._raw_generation(raw),
        'contract_projection':{'key':'fixture'},'invalid_json_line_count':0,'audited_stage_counts':{}}}
    path.write_text(json.dumps(payload))
    proof=sentinel._previous_cache_schema_proof('2026-09-17',raw,13)
    assert proof['from_schema']==12
    assert 'order_leg_no_response' in proof['newly_admitted_stages']
    for stage in ('entry_ai_economic_plan_observed','order_leg_no_response'):
        payload['source']['audited_stage_counts']={stage:1};path.write_text(json.dumps(payload))
        assert sentinel._previous_cache_schema_proof('2026-09-17',raw,13) is None


def test_source_invalid_machine_does_not_require_a_nonexistent_economic_plan():
    payload=monitor.snapshot([event(action='SOURCE_INVALID',screen='not_requested_machine_source_invalid')],START)
    assert payload['rows'][0]['economic_source']['status']=='not_applicable_machine_source_invalid'


def semantic_fixture(tmp_path, monkeypatch):
    import os
    import hashlib
    from src.tests.test_entry_strategy_policy import raw, setup, policy
    from src.engine.scalping import entry_strategy_policy as strategy, mechanistic_entry_runtime_policy as runtime
    from src.engine.scalping.ai_decision_trace import _json_bytes
    payload = raw()
    evidence = setup(payload)
    evidence.update(strategy_raw_input=payload, strategy_raw_sha256=strategy.digest(payload))
    machine = policy()
    profile, selection = strategy.select(machine, payload, evidence)
    bundle = dict(all_continuous_adopted=True, scope_policies={'KRX|KRX_REGULAR': dict(machine_policy=machine)})
    bundle['bundle_sha256'] = runtime.digest(bundle)
    path = runtime.root(tmp_path) / 'generations' / (bundle['bundle_sha256'] + '.json')
    path.parent.mkdir(parents=True);path.write_text(json.dumps(bundle))
    monkeypatch.setattr(runtime, 'load_effective', lambda **kw: bundle)
    scope = dict(selection_basis=strategy.MACHINE_SELECTION_VERSION, promotion_pass=True,
        machine_evidence={'train': {'economics': dict(selected_opportunity_count=10, win_rate_pct=60., selected_path_ev_pct=-.4)}})
    scope['machine_evidence']['train']['economics']['support_adjusted_win_rate_pct'] = strategy.machine_support_adjusted_win_rate(scope['machine_evidence']['train']['economics'])
    report = dict(target_date='2026-09-21', selections={'KRX|KRX_REGULAR': scope})
    report['artifact_content_sha256'] = runtime.digest(report)
    path = tmp_path / 'report/ai_decision_action_outcome_calibration/machine_policy_2026-09-21.json'
    path.parent.mkdir(parents=True);path.write_text(json.dumps(report))
    terminal = dict(report_sha256=report['artifact_content_sha256'], status='completed', activation={'status':'activated'})
    terminal['artifact_content_sha256'] = runtime.digest(terminal)
    path.with_name('machine_policy_terminal_2026-09-21.json').write_text(json.dumps(terminal))
    observation = dict(schema='mechanistic_entry_observation_v1', captured_at=START.isoformat(),
        bundle_sha256=bundle['bundle_sha256'], label_context=dict(effective_venue='KRX', session_bucket='krx_regular'),
        source=dict(setup_evidence=evidence, assessment={'action': 'BLOCK'}),
        runtime_consumption=dict(bundle_sha256=bundle['bundle_sha256'], policy_sha256=selection['policy_sha256'],
            selector_leaf=selection['leaf'], effective_thresholds=profile, pid=os.getpid(), cwd=str(__import__('pathlib').Path.cwd()),
            process_start_ticks=__import__('pathlib').Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]))
    path = tmp_path / 'ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl'
    path.parent.mkdir()
    def write(value):
        value = {k:v for k,v in value.items() if k != 'machine_observation_sha256'}
        value['machine_observation_sha256'] = hashlib.sha256(_json_bytes(value)).hexdigest()
        path.write_text(json.dumps(value)+'\n')
    write(observation)
    return observation, write


def test_semantic_receipt_and_negative_ev_selection(tmp_path, monkeypatch):
    observation, write = semantic_fixture(tmp_path, monkeypatch)
    result = monitor.machine_semantics(tmp_path, START)
    assert result['status'] == 'observed_receipts_match'
    assert next(iter(result['scopes'].values()))['live_pid_receipts'] == 1
    assert result['selection']['KRX|KRX_REGULAR']['score_contract_valid']
    assert result['selection']['KRX|KRX_REGULAR']['mean_net_path_ev_pct'] == -.4
    observation['runtime_consumption']['effective_thresholds']['ask_wall_spread_bp'] = 80
    write(observation)
    assert monitor.machine_semantics(tmp_path, START)['issues'] == {'effective_policy_receipt_mismatch': 1}


def test_semantic_source_invalid_is_not_policy_mismatch(tmp_path, monkeypatch):
    observation, write = semantic_fixture(tmp_path, monkeypatch)
    observation['source'] = dict(assessment={'action':'source_invalid'}, setup_evidence={'source_quality_blockers':['bbo_stale']})
    write(observation)
    result = monitor.machine_semantics(tmp_path, START)
    assert result['source_invalid_count'] == 1 and not result['issues']
    assert not result['scopes'] and result['status'] == 'source_invalid_observed'


def test_semantic_hash_staleness_and_partial_tail(tmp_path, monkeypatch):
    observation, write = semantic_fixture(tmp_path, monkeypatch)
    result = monitor.machine_semantics(tmp_path, START + timedelta(hours=1))
    assert result['status'] == 'unobservable' and not result['observation_count']
    path = tmp_path / 'ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl'
    path.write_text(path.read_text().replace('krx_regular', 'nxt_regular'))
    assert monitor.machine_semantics(tmp_path, START)['issues'] == {'machine_observation_hash_invalid': 1}
    assert monitor.machine_semantics(tmp_path, START, tail_bytes=30)['tail_truncated']
    assert not monitor.machine_semantics(tmp_path, START, tail_bytes=30)['observation_count']


def test_nonentry_downstream_gaps_do_not_require_ai_or_capital():
    now = START + timedelta(minutes=15)
    payload = report([nonentry_gap(), event(999, when=now)], now)
    row = payload['submission_monitor']['rows'][0]
    row['economic_source'] = dict(status='source_gap', blocker='economic_observation_event_missing')
    result = monitor.evaluate(payload, {}, now)
    assert not any(i['rule']=='economic_producer_gap' for i in result['incidents'].values())
    assert next(iter(result['scopes'].values()))['nonentry_downstream_observation_gaps'] == 1
    row['enter_now_observed'] = True
    assert not monitor._nonentry_downstream_gap(row)


def test_valid_enter_to_recheck_revision_keeps_latest_cache_miss_observation_only():
    now = START + timedelta(minutes=15)
    payload = report([nonentry_gap(action='RECHECK'), event(999, when=now)], now)
    row = payload['submission_monitor']['rows'][0]
    evidence = row['economic_source']
    row.update(enter_now_observed=True, initial_observed_action='ENTER_NOW',
        latest_observed_action='RECHECK', revision_chain_status='valid',
        decision_history=[{'action': 'ENTER_NOW', 'machine_observation_sha256': 'a' * 64},
            {'action': 'RECHECK', 'machine_observation_sha256': 'b' * 64}],
        economic_history=[{'mechanistic_action': 'RECHECK',
            'machine_observation_sha256': 'b' * 64, 'evidence': evidence}])
    result = monitor.evaluate(payload, {}, now)
    scope = next(iter(result['scopes'].values()))
    assert scope['nonentry_capacity_observation_gaps'] == 1
    assert scope['economic_producer_gaps'] == 0
    assert not any(i['rule'] == 'economic_producer_gap' for i in result['incidents'].values())
    row['economic_history'][-1]['machine_observation_sha256'] = 'c' * 64
    assert not monitor._nonentry_downstream_gap(row)


def _source_gap_files(root, now, *, probes=(), traces=(), pending=()):
    day = now.date().isoformat()
    for directory, stem, rows in (
        ("pipeline_events", "pipeline_events", probes),
        ("ai_decision_trace", "ai_decision_trace", traces),
        ("ai_decision_outcomes", "ai_decision_outcomes", pending),
    ):
        path = root / directory / f"{stem}_{day}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def _probe_source_row(now, result, reason, *, kind="-"):
    return {"emitted_at": now.isoformat(), "pipeline": "ENTRY_PIPELINE",
        "stage": "zero_base_probe_result", "stock_code": "005930",
        "fields": {"zero_base_route": "krx_nxt_integrated",
                   "zero_base_probe_result": result, "zero_base_probe_reason": reason,
                   "machine_capture_status": "captured",
                   "machine_observation_sha256": "c" * 64,
                   "zero_base_machine_source_gap_kind": kind}}


def _auxiliary_source_row(now, *, cost_status="exact_pre_provider_replay", cost=0.1):
    return {"decision_ts": now.isoformat(), "decision_stage": "entry_screen",
        "decision_trace_id": "trace-1", "evaluation_attempt_id": "attempt-1",
        "stock_code": "005930", "effective_venue": "KRX",
        "session_bucket": "krx_regular", "market_data_route": "krx_nxt_integrated",
        "machine_evaluation_status": "assessed", "entry_mechanistic_action": "ENTER_NOW",
        "machine_capture_status": "captured", "machine_observation_sha256": "d" * 64,
        "entry_ai_screen_required": True, "entry_ai_screen_status": "not_evaluated_transport",
        "provider_called": True, "result_source": "timeout",
        "entry_cost_source_status": cost_status,
        "entry_conservative_execution_cost_pct": cost,
        "entry_cost_scope": "counterfactual_friction_no_broker_fees",
        "entry_cost_basis": "half_spread_plus_bounded_source_age_penalty",
        "entry_cost_evaluation_attempt_id": "attempt-1",
        "entry_cost_contract_sha256": "a" * 64,
        "entry_cost_replay_context_sha256": "b" * 64,
        "reference_price": 10000}


def test_intraday_source_semantics_separates_sparse_probe_from_auxiliary_cost_gap(tmp_path):
    now = START + timedelta(minutes=10)
    probe = _probe_source_row(now, "source_unavailable", "0B_missing")
    trace = _auxiliary_source_row(now, cost_status=None, cost=None)
    pending = dict(trace)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace], pending=[pending])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["diagnostics"] == {"machine_probe:0B_missing": 1}
    assert result["diagnostics_by_scope"] == {
        "route:krx_nxt_integrated|machine_probe:0B_missing": 1}
    assert result["issues"] == {"auxiliary_call:cost_receipt_missing": 1,
                                 "auxiliary_pending:cost_receipt_missing": 1}
    assert result["issues_by_scope"]["KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call:cost_receipt_missing"] == 1
    assert result["observed"]["auxiliary_called"] == 1
    assert result["sources"]["probe"]["status"] == "complete"
    assert result["runtime_effect"] is False


def test_intraday_source_semantics_exact_cost_and_short_warmup_do_not_alert(tmp_path):
    now = START + timedelta(minutes=10)
    probe = _probe_source_row(now, "assessed", "machine_assessed")
    probe["fields"]["zero_base_ws_exact_0b_count"] = "2"
    trace = _auxiliary_source_row(now)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace], pending=[dict(trace)])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["status"] == "observed_no_gap"
    assert result["issues"] == result["diagnostics"] == {}
    assert result["observed"]["auxiliary_cost_bound"] == 1
    assert result["observed"]["auxiliary_pending_bound"] == 1


def test_intraday_source_semantics_route_conflict_is_actionable_and_tail_is_bounded(tmp_path):
    now = START + timedelta(minutes=10)
    probe = _probe_source_row(now, "required_feature_insufficient", "machine_not_assessed",
                              kind="source_route_conflict")
    _source_gap_files(tmp_path, now, probes=[probe], traces=[], pending=[])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"] == {"machine_probe:source_route_conflict": 1}
    assert result["status"] == "gap_observed"
    assert result["sources"]["trace"]["status"] == "unobservable"
    partial = monitor.source_gap_semantics(tmp_path, now, tail_bytes=20)
    assert partial["sources"]["probe"]["status"] == "partial"
    assert partial["status"] == "unobservable"


def test_probe_source_gap_keeps_candle_failure_reason(tmp_path):
    now=START+timedelta(minutes=10)
    row=_probe_source_row(now,"required_feature_insufficient","candle_source_missing")
    _source_gap_files(tmp_path,now,probes=[row])
    result=monitor.source_gap_semantics(tmp_path,now)
    assert result["diagnostics"]=={"machine_probe:candle_source_missing":1}


def test_intraday_source_incident_requires_same_stage_recovery_receipt():
    now = START + timedelta(minutes=10)
    result = {"as_of": now.isoformat(), "incidents": {}, "notification_pending": []}
    gap = {"issues": {"auxiliary_call:cost_receipt_missing": 1}, "examples": [],
           "issues_by_scope": {"KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call:cost_receipt_missing": 1},
           "sources": {"probe": {"status": "complete"}, "trace": {"status": "complete"},
                       "pending": {"status": "complete"}}, "observed": {"entry_traces": 1}}
    monitor.attach_source_gap_semantics(result, gap)
    result["as_of"] = (now + timedelta(minutes=5)).isoformat()
    monitor.attach_source_gap_semantics(result, gap)
    incident = result["incidents"]["machine_auxiliary_intraday_source_gap"]
    assert incident["status"] == "active"
    assert result["notification_pending"]
    no_call = {**gap, "issues": {}, "observed": {"probe_assessed": 1, "machine_assessed": 1}}
    monitor.attach_source_gap_semantics(result, no_call)
    assert incident["status"] == "active"
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "historical_unresolved"
    recovered = {**no_call, "observed": {"auxiliary_cost_bound": 1},
                 "healthy_by_scope": {"KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call": 1}}
    monitor.attach_source_gap_semantics(result, recovered)
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "recovered"
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["historical_source_repaired"] is False


def test_intraday_source_incident_cannot_recover_from_other_route_or_partial_tail():
    now = START + timedelta(minutes=10)
    result = {"as_of": now.isoformat(), "incidents": {}, "notification_pending": []}
    gap = {"issues": {"auxiliary_call:cost_receipt_missing": 1}, "examples": [],
           "issues_by_scope": {"KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call:cost_receipt_missing": 1},
           "sources": {"trace": {"status": "complete"}}, "observed": {}}
    monitor.attach_source_gap_semantics(result, gap)
    result["as_of"] = (now + timedelta(minutes=5)).isoformat()
    monitor.attach_source_gap_semantics(result, gap)
    healthy = {**gap, "issues": {}, "issues_by_scope": {},
               "healthy_by_scope": {"KRX|KRX_REGULAR|route:nxt_only|auxiliary_call": 1}}
    monitor.attach_source_gap_semantics(result, healthy)
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "historical_unresolved"
    healthy["healthy_by_scope"] = {"KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call": 1}
    healthy["sources"] = {"trace": {"status": "partial"}}
    monitor.attach_source_gap_semantics(result, healthy)
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "historical_unresolved"
    healthy["sources"] = {"trace": {"status": "complete"}}
    monitor.attach_source_gap_semantics(result, healthy)
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "recovered"


def test_intraday_source_incident_new_route_resets_timer_and_recurrence_renotifies():
    now = START + timedelta(minutes=10)
    result = {"as_of": now.isoformat(), "incidents": {}, "notification_pending": []}
    base = {"issues": {"auxiliary_call:cost_receipt_missing": 1},
            "issues_by_scope": {"KRX|KRX_REGULAR|route:nxt_only|auxiliary_call:cost_receipt_missing": 1},
            "sources": {"trace": {"status": "complete"}}, "observed": {}, "examples": []}
    monitor.attach_source_gap_semantics(result, base)
    result["as_of"] = (now + timedelta(minutes=5)).isoformat()
    monitor.attach_source_gap_semantics(result, base)
    incident = result["incidents"]["machine_auxiliary_intraday_source_gap"]
    assert incident["status"] == "active"
    incident["notified_status"] = "active"
    other_route = {**base, "issues_by_scope": {
        "KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call:cost_receipt_missing": 1}}
    monitor.attach_source_gap_semantics(result, other_route)
    incident = result["incidents"]["machine_auxiliary_intraday_source_gap"]
    assert incident["status"] == "pending" and incident["first_seen"] == result["as_of"]
    assert incident["notified_status"] is None
    result["as_of"] = (now + timedelta(minutes=10)).isoformat()
    monitor.attach_source_gap_semantics(result, other_route)
    result["incidents"]["machine_auxiliary_intraday_source_gap"]["notified_status"] = "active"
    monitor.attach_source_gap_semantics(result, {**other_route, "issues": {}, "issues_by_scope": {}})
    assert result["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "historical_unresolved"
    monitor.attach_source_gap_semantics(result, other_route)
    result["as_of"] = (now + timedelta(minutes=15)).isoformat()
    monitor.attach_source_gap_semantics(result, other_route)
    incident = result["incidents"]["machine_auxiliary_intraday_source_gap"]
    assert incident["status"] == "active" and incident["notified_status"] is None
    assert "machine_auxiliary_intraday_source_gap" in result["notification_pending"]


def test_intraday_source_semantics_missing_pending_requires_complete_source(tmp_path):
    now = START + timedelta(minutes=10)
    trace = _auxiliary_source_row(now - timedelta(minutes=2))
    trace["outcome_label_eligible"] = True
    _source_gap_files(tmp_path, now,
                      probes=[_probe_source_row(now, "assessed", "machine_assessed")],
                      traces=[trace], pending=[])
    empty = monitor.source_gap_semantics(tmp_path, now)
    assert "auxiliary_pending:label_receipt_missing" not in empty["issues"]
    _source_gap_files(tmp_path, now,
                      probes=[_probe_source_row(now, "assessed", "machine_assessed")],
                      traces=[trace], pending=[{**trace, "decision_trace_id": "other-trace"}])
    observed = monitor.source_gap_semantics(tmp_path, now)
    assert observed["issues"]["auxiliary_pending:label_receipt_missing"] == 1


def test_intraday_source_semantics_reports_systemic_probe_coverage_without_broker_claim(tmp_path):
    now = START + timedelta(minutes=10)
    probes = [_probe_source_row(now - timedelta(seconds=index), "source_unavailable",
                                "route_snapshot_missing") for index in range(10)]
    _source_gap_files(tmp_path, now, probes=probes, traces=[], pending=[])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["diagnostics"] == {"machine_probe:route_snapshot_missing": 10}
    assert result["issues"] == {"machine_probe:coverage_degraded:krx_nxt_integrated": 1}
    assert result["probe_route_assessed_counts"] == {}
    assert result["remediation"][0]["automatic_repair_attempted"] is False
    state = {"as_of": now.isoformat(), "incidents": {}, "notification_pending": []}
    monitor.attach_source_gap_semantics(state, result)
    assert state["incidents"]["machine_auxiliary_intraday_source_gap"]["category"] == "review_required"


def test_intraday_probe_coverage_requires_complete_tail_and_counts_distinct_symbols(tmp_path):
    now = START + timedelta(minutes=10)
    probes = []
    for index in range(10):
        row = _probe_source_row(now, "source_unavailable", "route_snapshot_missing")
        row["stock_code"] = f"{index:06d}"
        probes.append(row)
    _source_gap_files(tmp_path, now, probes=probes)
    complete = monitor.source_gap_semantics(tmp_path, now)
    assert complete["diagnostics"]["machine_probe:route_snapshot_missing"] == 10
    assert complete["issues"]["machine_probe:coverage_degraded:krx_nxt_integrated"] == 1
    path = tmp_path / "pipeline_events" / f"pipeline_events_{now.date()}.jsonl"
    with path.open("ab") as stream:
        stream.write(b'{"emitted_at":')
    partial = monitor.source_gap_semantics(tmp_path, now)
    assert partial["sources"]["probe"]["status"] == "partial"
    assert "machine_probe:coverage_degraded:krx_nxt_integrated" not in partial["issues"]


def test_intraday_auxiliary_pending_detects_cross_source_binding_mismatch(tmp_path):
    now = START + timedelta(minutes=10)
    trace = _auxiliary_source_row(now - timedelta(minutes=2))
    trace["outcome_label_eligible"] = True
    pending = {**trace, "entry_cost_contract_sha256": "f" * 64}
    _source_gap_files(tmp_path, now, traces=[trace], pending=[pending])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"]["auxiliary_pending:trace_binding_mismatch"] == 1


def test_intraday_machine_trace_invalid_contract_preserves_sparse_vs_missing_cause(tmp_path):
    now = START + timedelta(minutes=10)
    sparse = _auxiliary_source_row(now)
    sparse.update(decision_trace_id="trace-sparse", machine_evaluation_status="assessment_contract_invalid",
                  machine_source_gap_kind="trusted_tape_source_insufficient",
                  machine_contract_error="strategy_tape_score_source_missing",
                  entry_mechanistic_action=None, entry_ai_screen_required=False, provider_called=False)
    missing = {**sparse, "decision_trace_id": "trace-missing", "machine_source_gap_kind": None,
               "machine_contract_error": None}
    capture = {**_auxiliary_source_row(now), "decision_trace_id": "trace-capture",
               "machine_capture_status": "write_failed", "entry_ai_screen_required": False}
    _source_gap_files(tmp_path, now, traces=[sparse, missing, capture])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["diagnostics"] == {"machine_trace:trusted_tape_source_insufficient": 1}
    assert result["issues"]["machine_trace:contract_error_receipt_missing"] == 1
    assert result["issues"]["machine_trace:capture_receipt_missing_or_invalid"] == 1


def test_intraday_nonfinite_machine_contract_has_specific_source_reason(tmp_path):
    now = START + timedelta(minutes=10)
    error = "Out of range float values are not JSON compliant: nan"
    probe = _probe_source_row(now, "policy_unavailable", "assessment_contract_invalid")
    probe["fields"]["zero_base_machine_contract_error"] = error
    trace = _auxiliary_source_row(now)
    trace.update(machine_evaluation_status="assessment_contract_invalid",
                 machine_contract_error=error, entry_mechanistic_action=None,
                 entry_ai_screen_required=False, provider_called=False)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"]["machine_probe:machine_source_nonfinite"] == 1
    assert result["issues"]["machine_trace:machine_source_nonfinite"] == 1


def test_intraday_probe_contract_failure_is_visible_without_trace(tmp_path):
    now = START + timedelta(minutes=10)
    sparse = _probe_source_row(now, "policy_unavailable", "assessment_contract_invalid",
                               kind="trusted_tape_source_insufficient")
    missing = _probe_source_row(now + timedelta(seconds=1), "policy_unavailable",
                                "assessment_contract_invalid")
    _source_gap_files(tmp_path, now, probes=[sparse, missing])
    result = monitor.source_gap_semantics(tmp_path, now + timedelta(seconds=2))
    assert result["diagnostics"]["machine_probe:trusted_tape_source_insufficient"] == 1
    assert result["issues"]["machine_probe:contract_error_receipt_missing"] == 1
    assert result["probe_route_counts"]["krx_nxt_integrated"] == 2


def test_intraday_source_semantics_catches_missing_capture_and_pending_source(tmp_path):
    now = START + timedelta(minutes=10)
    probe = _probe_source_row(now, "assessed", "machine_assessed")
    probe["fields"]["machine_capture_status"] = "write_failed"
    trace = _auxiliary_source_row(now - timedelta(minutes=2))
    trace["outcome_label_eligible"] = True
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    (tmp_path / "ai_decision_outcomes" / f"ai_decision_outcomes_{now.date()}.jsonl").unlink()
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"]["machine_probe:capture_receipt_missing_or_invalid"] == 1
    assert result["issues"]["auxiliary_pending:source_file_missing"] == 1
    assert result["sources"]["pending"]["status"] == "unobservable"


def test_source_only_monitor_runs_when_sentinel_report_is_absent(tmp_path, monkeypatch):
    import sys
    monkeypatch.setattr(monitor, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(monitor, "machine_semantics", lambda *args, **kwargs:
                        pytest.fail("source-only must not run policy receipt audit"))
    monkeypatch.setattr(monitor, "entry_execution_tuning_semantics", lambda *args, **kwargs:
                        pytest.fail("source-only must not run tuning receipt audit"))
    monkeypatch.setattr(monitor, "source_gap_semantics", lambda *args, **kwargs: {
        "status": "gap_observed", "issues": {"machine_probe:source_route_conflict": 1},
        "examples": [], "sources": {}, "observed": {},
    })
    monkeypatch.setattr(sys, "argv", ["monitor", "--report", str(tmp_path / "missing.json"),
                                       "--source-only"])
    assert monitor.main() == 0
    saved = json.loads((tmp_path / "data/report/buy_funnel_sentinel/"
                        "submission_bottleneck_monitor_latest.json").read_text())
    assert saved["status"] == "unobservable"
    assert saved["source_gap_semantics"]["status"] == "gap_observed"
    assert saved["incidents"]["machine_auxiliary_intraday_source_gap"]["status"] == "pending"


def test_intraday_source_alert_names_cause_without_order_claim():
    now = START + timedelta(minutes=10)
    result = {"as_of": now.isoformat(), "incidents": {}, "notification_pending": [],
              "scopes": {}, "identity_observation": {}, "notification_status": "idle"}
    semantics = {"issues": {"auxiliary_call:cost_receipt_missing": 1},
                 "issues_by_scope": {"KRX|KRX_REGULAR|route:krx_nxt_integrated|auxiliary_call:cost_receipt_missing": 1},
                 "examples": [{"stock_code": "005930", "route": "krx_nxt_integrated",
                               "reason": "cost_receipt_missing"}],
                 "sources": {"trace": {"status": "complete"}},
                 "observed": {"auxiliary_called": 1}}
    monitor.attach_source_gap_semantics(result, semantics)
    result["as_of"] = (now + timedelta(minutes=5)).isoformat()
    monitor.attach_source_gap_semantics(result, semantics)
    messages = []
    monitor.notify(result, "monitor.json", send=messages.append)
    assert len(messages) == 1
    assert "판정 원천결손 점검" in messages[0]
    assert "auxiliary_call:cost_receipt_missing" in messages[0]
    assert "주문 수 아님" in messages[0]
    assert "자동 매매 변경 없음" in messages[0]


@pytest.mark.parametrize('mismatch', [None, 'action', 'screen', 'owner', 'before', 'partial_receipt'])
def test_sparse_submit_terminal_is_not_new_machine_revision(mismatch):
    decision = event(screen='pass', machine_revision_schema='exact_machine_revision_v1',
        machine_observation_sha256='a'*64, machine_revision_parent_sha256='')
    terminal = event(stage='entry_submit_attempt_finished', screen='pass', when=START+timedelta(seconds=2))
    if mismatch == 'action': terminal.fields['entry_mechanistic_action'] = 'BLOCK'
    if mismatch == 'screen': terminal.fields['entry_ai_screen_status'] = 'veto'
    if mismatch == 'owner': terminal.fields['entry_primary_decision_owner'] = 'other'
    if mismatch == 'partial_receipt': terminal.fields['machine_revision_schema'] = 'exact_machine_revision_v1'
    rows = [terminal, decision] if mismatch == 'before' else [decision, terminal]
    selected, status, errors = sentinel._machine_revision_rows(rows)
    assert bool(errors) == bool(mismatch)
    if not mismatch:
        assert terminal in selected
        ledger = sentinel._machine_primary_entry_funnel(rows)['evaluation_ledger'][0]
        assert not ledger['conflict_reasons'] and len(ledger['decision_history']) == 1


def test_receipt_incident_requires_persistence_and_does_not_fake_recovery():
    semantics = dict(issues={'effective_policy_receipt_mismatch':1}, examples=[], current_bundle_sha256='a'*64)
    result = dict(as_of=START.isoformat(), incidents={}, notification_pending=[])
    monitor.attach_machine_semantics(result, semantics)
    assert not result['notification_pending']
    result['as_of'] = (START+timedelta(minutes=5)).isoformat()
    monitor.attach_machine_semantics(result, semantics)
    assert result['incidents']['machine_policy_receipt_contract']['status'] == 'active'
    result['notification_pending'] = []
    monitor.attach_machine_semantics(result, {'issues':{}})
    assert result['incidents']['machine_policy_receipt_contract']['status'] == 'historical_unresolved'
    assert not result['notification_pending']


def test_required_feature_guard_has_no_selected_threshold_receipt(tmp_path, monkeypatch):
    observation, write = semantic_fixture(tmp_path, monkeypatch)
    observation['source'] = dict(assessment=dict(schema='mechanistic_entry_required_feature_v1', action='RECHECK', reason='required_feature_input_insufficient'),
        setup_evidence=dict(source_quality_status='blocked', source_quality_blockers=['required_feature_tape_stale']))
    write(observation)
    result = monitor.machine_semantics(tmp_path, START)
    assert result['required_feature_guard_count'] == 1 and not result['issues']
    observation['source']['assessment']['action'] = 'ENTER_NOW'
    write(observation)
    assert monitor.machine_semantics(tmp_path, START)['issues'] == {'machine_raw_input_missing': 1}


def test_historical_policy_receipt_is_not_compared_to_new_current(tmp_path, monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
    observation, write = semantic_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(runtime, 'load_effective', lambda **kw: {'bundle_sha256':'c'*64})
    result = monitor.machine_semantics(tmp_path, START)
    assert not result['issues']
    assert not next(iter(result['scopes'].values()))['current_bundle']
    assert result['current_bundle_sha256'] == 'c'*64


@pytest.mark.parametrize('mismatch', [None, 'hash', 'action', 'screen', 'owner'])
def test_exact_hash_downstream_echo_requires_existing_consistent_revision(mismatch):
    decision = event(action='RECHECK', screen='not_requested_required_feature_insufficient',
        stage='ai_confirmed_terminal_no_budget', machine_revision_schema='exact_machine_revision_v1',
        machine_observation_sha256='a'*64, machine_revision_parent_sha256='')
    echo = event(action='RECHECK', screen='not_requested_required_feature_insufficient',
        stage='blocked_ai_score', when=START+timedelta(seconds=1), machine_observation_sha256='a'*64)
    field = dict(hash='machine_observation_sha256', action='entry_mechanistic_action', screen='entry_ai_screen_status', owner='entry_primary_decision_owner')
    if mismatch: echo.fields[field[mismatch]] = 'different'
    _, _, errors = sentinel._machine_revision_rows([decision, echo])
    assert bool(errors) == bool(mismatch)
    # Without an initial explicit receipt, the echo remains legacy, not verified.
    assert sentinel._machine_revision_rows([echo])[1] == 'legacy_unverified'


def test_source_invalid_echo_uses_canonical_action_spelling():
    first = event(action='SOURCE_INVALID', screen='not_requested_machine_source_invalid',
        machine_revision_schema='exact_machine_revision_v1', machine_observation_sha256='a'*64, machine_revision_parent_sha256='')
    echo = event(action='source_invalid', screen='not_requested_machine_source_invalid',
        stage='blocked_ai_score', machine_observation_sha256='a'*64, when=START+timedelta(seconds=1))
    _, status, errors = sentinel._machine_revision_rows([first, echo])
    assert status == 'single_revision' and not errors
    assert sentinel._machine_primary_entry_funnel([first, echo])['evaluation_ledger'][0]['mechanistic_action'] == 'SOURCE_INVALID'


def test_current_identity_loss_alerts_immediately_then_normal_notice_once():
    state = tick([event(evaluation_attempt_id='')], 0)
    sent = []
    monitor.notify(state, 'fixture.json', send=sent.append)
    assert len(sent) == 1 and 'current_gap' in sent[-1]
    assert '점검하세요' in sent[-1]
    cleared = tick([], 11, state)
    monitor.notify(cleared, 'fixture.json', send=sent.append)
    assert len(sent) == 2 and '현재 정상 관측' in sent[-1]
    assert '점검하세요' not in sent[-1]
    assert cleared['incidents']['unbound_machine_identity']['status'] == 'historical_unresolved'
    assert cleared['incidents']['unbound_machine_identity']['normal_observation_notified_at']
    monitor.notify(cleared, 'fixture.json', send=sent.append)
    later = tick([], 20, cleared)
    monitor.notify(later, 'fixture.json', send=sent.append)
    assert len(sent) == 2
    recurrent = tick([event(2, evaluation_attempt_id='', when=START+timedelta(minutes=21))], 21, later)
    monitor.notify(recurrent, 'fixture.json', send=sent.append)
    assert len(sent) == 3 and 'current_gap' in sent[-1]
    assert recurrent['incidents']['unbound_machine_identity']['history']


def test_normal_identity_notice_waits_for_fresh_evidence_and_retries_failure():
    state = tick([event(evaluation_attempt_id='')], 0)
    monitor.notify(state, 'fixture.json', send=lambda _: None)
    now = START+timedelta(minutes=11)
    unobserved = monitor.evaluate(report([], now), state, now)
    sent = []
    monitor.notify(unobserved, 'fixture.json', send=sent.append)
    assert not sent
    normal = tick([], 12, unobserved)
    def fail(text):
        raise OSError('redacted')
    monitor.notify(normal, 'fixture.json', send=fail)
    assert normal['notification_status'] == 'retry_required:OSError'
    assert normal['incidents']['unbound_machine_identity']['normal_observation_pending']
    retry = tick([], 13, normal)
    monitor.notify(retry, 'fixture.json', send=sent.append)
    assert len(sent) == 1 and '현재 정상 관측' in sent[0]


def test_existing_historical_state_does_not_generate_migration_notice():
    state = tick([event(evaluation_attempt_id='')], 11)
    state['incidents']['unbound_machine_identity']['notified_status'] = 'historical_unresolved'
    next_state = tick([], 12, state)
    # Even a persisted old notification queue must not send a historical alert.
    next_state['notification_pending'] = ['unbound_machine_identity']
    sent = []
    monitor.notify(next_state, 'fixture.json', send=sent.append)
    assert not sent


def test_normal_and_current_alert_batch_keeps_actionable_request():
    state = tick([event(evaluation_attempt_id='')], 0)
    monitor.notify(state, 'fixture.json', send=lambda _: None)
    normal = tick([], 11, state)
    normal['incidents']['another'] = dict(scope='test',rule='test',status='active',count=1,category='structural_evidence')
    normal['notification_pending'].append('another')
    sent = []
    monitor.notify(normal, 'fixture.json', send=sent.append)
    assert len(sent) == 1 and '현재 정상 관측' in sent[0] and '점검하세요' in sent[0]


def test_normal_notice_survives_cooldown_without_duplicate_ack():
    state = tick([event(evaluation_attempt_id='')], 0)
    monitor.notify(state, 'fixture.json', send=lambda _: None)
    normal = tick([], 11, state)
    normal['last_notification_at'] = (START+timedelta(minutes=10)).isoformat()
    sent=[]
    monitor.notify(normal, 'fixture.json', send=sent.append)
    assert not sent and normal['notification_status']=='cooldown'
    assert normal['incidents']['unbound_machine_identity']['normal_observation_pending']
    ready=tick([],16,normal)
    monitor.notify(ready,'fixture.json',send=sent.append)
    assert len(sent)==1 and '현재 정상 관측' in sent[0]


def test_cancel_wait_intraday_projection_preserves_null_without_duplicate_alert(tmp_path, monkeypatch):
    from src.tests.test_entry_cancel_wait_tuning import _reconciliation_fixture
    _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=True)
    now = datetime.fromisoformat('2026-10-02T22:00:00+09:00')
    result = monitor.entry_execution_tuning_semantics(tmp_path/'data', now)
    cancel = result['entry_cancel_wait']
    assert cancel['daily_zero_is_verified'] is True
    assert cancel['unresolved_prior_custody_count'] is None
    assert cancel['notification_owner'] == 'artifact_freshness'
    assert not any('cancel_wait' in key for key in result['issues'])
