from datetime import datetime, timedelta
import json

import pytest

from src.engine import buy_funnel_sentinel as sentinel
from src.engine.monitoring import submission_bottleneck_monitor as monitor

START = datetime(2026, 9, 21, 8, 5)


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


def test_identity_delayed_alert_is_historical_and_keeps_occurrence_details():
    bad = event(evaluation_attempt_id='None')
    state = tick([bad], 10)
    sent = []
    monitor.notify(state, 'fixture.json', send=sent.append)
    assert len(sent) == 1
    assert 'historical_unresolved' in sent[0] and '주문 수 아님' in sent[0]
    assert '005930' in sent[0] and 'evaluation_attempt_id' in sent[0]
    assert '2026-09-21T08:05:00+09:00' in sent[0]
    assert '[]' not in sent[0]
    old = state['incidents']['unbound_machine_identity']
    expired = tick([], 50, state)
    item = expired['incidents']['unbound_machine_identity']
    assert item['status'] == 'historical_unresolved'
    for key in ('count', 'evidence_ids', 'examples', 'occurred_first_at', 'occurred_last_at'):
        assert item[key] == old[key]
    monitor.notify(expired, 'fixture.json', send=sent.append)
    assert len(sent) == 1  # Neither disappearance nor fresh good rows repair history.


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
    assert len(sent)==1 and '미확인(구형 이력)' in sent[0]
    assert 'recovered' not in sent[0] and '[]' not in sent[0]


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


def test_old_evidence_with_new_immature_gap_does_not_rearm_old_alert():
    old_bad=event(evaluation_attempt_id='')
    state=tick([old_bad],10)
    monitor.notify(state,'fixture.json',send=lambda _:None)
    now_bad=event(2,evaluation_attempt_id='',when=START+timedelta(minutes=15))
    result=tick([old_bad,now_bad],15,state)
    assert result['identity_observation']['status']=='current_gap'
    assert result['incidents']['unbound_machine_identity']['status']=='historical_unresolved'
    assert 'unbound_machine_identity' not in result['notification_pending']


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


def test_wrapper_notifies_only_after_success_and_not_on_replay(tmp_path):
    import os
    import subprocess
    from pathlib import Path
    project = Path(__file__).resolve().parents[2]
    py = tmp_path / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    calls = tmp_path / "calls.txt"
    py.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$CALLS"\n')
    py.chmod(0o755)
    env = {**os.environ, "PROJECT_DIR": str(tmp_path), "CALLS": str(calls),
        "BUY_FUNNEL_SENTINEL_COOLDOWN_SEC": "0"}
    wrapper = project / "deploy/run_buy_funnel_sentinel_intraday.sh"
    subprocess.run(["bash", str(wrapper), "2026-09-21"], env=env, check=True, capture_output=True)
    assert "submission_bottleneck_monitor" in calls.read_text()
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
