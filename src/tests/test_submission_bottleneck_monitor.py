from datetime import datetime, timedelta

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
    assert result["identity_missing_events"] == 1
    assert any(r["rule"] == "source_identity_missing" for r in active(result))


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
