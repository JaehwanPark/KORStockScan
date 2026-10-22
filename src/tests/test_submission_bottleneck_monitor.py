from datetime import datetime, timedelta
import hashlib
import json

import pytest

from src.engine import buy_funnel_sentinel as sentinel
from src.engine.monitoring import submission_bottleneck_monitor as monitor

START = datetime(2026, 9, 21, 8, 5)


def _observation_health_fixture():
    """Small sanitized b8079548/2026-10-14 snapshot, with additive new receipts.

    Preserve its exact clocks, zero decisions, three complete readers, historical
    incident and economic gaps. Replace bulky128-scope selection by one verified
    representative. No provider, source reader or native validator is invoked.
    """
    now = '2026-10-14T15:36:25.112259+09:00'
    day = '2026-10-14'
    source = {'schema': monitor.SCHEMA, 'as_of': '2026-10-14T15:35:12.585430+09:00',
              'latest_event_at': '2026-10-14T15:08:54.875071+09:00', 'rows': [],
              'identity_missing_events': 0, 'auxiliary_ai_semantic_issue_counts': {}}
    prior = {'schema': monitor.SCHEMA, 'date': day, 'source_as_of': '2026-10-14T15:15:18.387222+09:00',
             'incidents': {'old': {'status': 'historical_unresolved',
                 'last_seen': '2026-10-14T13:00:56.607087+09:00',
                 'issues': {'pre_submit_delay_bootstrap_env_mismatch': 1}}}}
    result = monitor.evaluate({'target_date': day, 'dry_run': False, 'submission_monitor': source}, prior, now)
    result.update(run_id='b807954859a24aad8c71f57a5991d068', execution_mode='full',
                  execution_status='completed', semantic_status='partial')
    sources = {name: {'status': 'complete', 'window_covered': True,
                     'incomplete_last_line': False, 'malformed_rows': 0, 'missing_timestamp_rows': 0,
                     'recent_count': 125 if name == 'probe' else 0, 'read_count': 1,
                     'bytes_read': 1024, 'source_size': 2048,
                     'source_identity': {'device': 66305, 'inode': 1358691 + index}}
               for index, name in enumerate(('probe', 'trace', 'pending'))}
    result['source_gap_semantics'] = {
        'schema': 'machine_auxiliary_intraday_source_semantics_v1', 'as_of': now,
        'status': 'unobservable', 'runtime_effect': False, 'decision_authority': 'report_only',
        'issues': {}, 'diagnostics': {}, 'issues_by_scope': {}, 'diagnostics_by_scope': {},
        'observed': {}, 'sources': sources, 'async_transition_projection_coverage': 'complete',
        'async_pass_projection_coverage': 'complete', 'async_pass_projection': [],
        'async_transition_projection': [], 'async_pass_unmapped_count': 0,
        'probe_route_counts': {}, 'probe_route_assessed_counts': {},
        'probe_route_source_covered_counts': {}, 'probe_route_native_no_match_counts': {},
        'fixed_watch_waits': {'schema': 'submission_monitor_fixed_watch_wait_census_v1',
            'count': 125, 'session_boundary_wait_count': 125,
            'unclassified_or_actionable_wait_count': 0, 'reason_counts': {'session_generation_mismatch': 125},
            'native_session_regime': 'session_transition', 'native_entry_allowed_by_clock': False,
            'runtime_effect': False},
    }
    from src.trading.market import session_contract
    result['source_gap_semantics']['fixed_watch_waits']['native_session_regime'] = (
        session_contract.resolve_market_session(monitor.stamp(now)).session_regime)
    result['machine_semantics'] = {
        'status': 'unobservable', 'decision_authority': 'report_only', 'issues': {},
        'observation_count': 0, 'source_invalid_count': 0, 'required_feature_guard_count': 0,
        'source_invalid_blockers': {}, 'scopes': {}, 'selection_family': 'continuous_reversal',
        'selection': {'representative': {'score_contract_valid': True}},
        'publication': {'status': 'native_frozen_family_verified', 'effective_date': day},
        'current_bundle_sha256': '99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215',
        'read_count': 1, 'read_limit_bytes': 8388608, 'bytes_read': 8362685, 'source_bytes': 8677570,
        'window_coverage': 'bounded_suffix', 'action_replay_performed': False,
    }
    result['entry_execution_tuning_semantics'] = {
        'schema': 'entry_execution_tuning_semantics_v1', 'as_of': now, 'status': 'observed',
        'decision_authority': 'report_only', 'runtime_effect': False, 'allowed_runtime_apply': False,
        'actual_order_submitted': False, 'issues': {},
        'bootstrap': {'status': 'verified', 'verify_status': 'pass', 'policy_pid_consumption_proven': False},
        'entry_split': {'status': 'source_gap', 'verification': 'verified',
            'read_mode': 'verified_monitor_projection', 'source_date': '2026-10-13',
            'policy_generation_binding': 'matched', 'prepared_effective_date': day,
            'policy_runtime_apply_allowed': False,
            'blockers': ['operating_paired_source_missing', 'operating_owner_source_invalid:actual_outcomes',
                         'clean_baseline_paired_realized_population_incomplete'],
            'primary_operating_ev_pct': None, 'paired_net_ev_delta_pct': None,
            'verification_receipt': {'verified': True, 'role': 'submission_monitor', 'source_date': '2026-10-13',
                'generation_id': 'f9224cfaead3cb85ea13f4376085a1d3bf11795f37f1051b0088c40828c364c3',
                'report_sha256': '955eda70d4de631e4fcdd06fa8670c41b94ea2ecce1100b66591060cb62bd5fc',
                'policy_sha256': 'fae051dcb3cce32d2496070481b92c31cb84a6d460a6d8e473d41f9a4c477d4d',
                'manifest_sha256': '5d5b121398a63683c654df79cfeb5dc7389263cf67362ba676c1d2d9cef89d52',
                'native_validation': {'reason': 'generation_binding_valid',
                    'scope': 'full_report_policy_native_contract', 'status': 'verified'},
                'full_report_bytes_read': 0, 'metadata_bytes_read': 18581, 'consumer_elapsed_ms': 16.671}},
        'pre_submit_delay': {'status': 'verified_policy_bound', 'bootstrap_handoff_match': True,
            'bootstrap_env_match': True, 'runtime_effect': False, 'effective_from': day, 'report_blockers': []},
    }
    return result


@pytest.mark.parametrize('damage',[None,'late_activation','wrong_lower','unbounded_index','missing_population'])
def test_source_window_health_contract_is_pure_and_cannot_expand_coverage(monkeypatch,damage):
    result=_observation_health_fixture()
    now=monitor.stamp(result['as_of']);lower=now-timedelta(seconds=monitor.SOURCE_WINDOW_SEC)
    source=result['source_gap_semantics']['sources']['probe']
    source.update(coverage_basis='verified_forward_sentinel_source_window_v1',
        coverage_started_at=(lower-timedelta(seconds=1)).isoformat(),current_window_start_at=lower.isoformat(),
        cache_schema_version=20,projection_contract='a'*64,
        historical_stage_coverage='not_backfilled_before_cache_offset',cache_generation=[1,2,3,4,5],
        indexed_raw_offset=2048,indexed_bytes_read=123,indexed_identity_bytes_read=300,bytes_read=0)
    if damage=='late_activation':source['coverage_started_at']=(lower+timedelta(seconds=1)).isoformat()
    elif damage=='wrong_lower':source['current_window_start_at']=(lower+timedelta(seconds=1)).isoformat()
    elif damage=='unbounded_index':source['indexed_identity_bytes_read']=monitor.SOURCE_TAIL_BYTES+1
    elif damage=='missing_population':source.pop('indexed_identity_bytes_read')
    from pathlib import Path
    monkeypatch.setattr(Path,'read_bytes',lambda *a:pytest.fail('pure health projection performed IO'))
    health=monitor.observation_health_projection(result)
    assert (health['status']=='warning_pending')==(damage is None),health
    if damage is not None:assert 'indexed_source_window_proof_invalid:probe' in health['unmet_conditions']


def _recorded_guard_health_fixture(*, healthy=False):
    """Reconstructed small16:00 guard contract using actual first2 hashes/IDs.

    The original full16:00 report was not retained. This is explicitly a fixture,
    not a byte-identical report capture or a fresh native validation receipt.
    """
    result = _observation_health_fixture()
    now = monitor.stamp('2026-10-14T16:00:55.026558+09:00')
    result['as_of'] = now.isoformat()
    inp = result['input_provenance']
    inp.update(evaluated_at=now.isoformat(), snapshot_as_of=(now-timedelta(seconds=50)).isoformat(),
               snapshot_age_seconds=50.0,
               latest_event_age_seconds=(now-monitor.stamp(inp['latest_event_at'])).total_seconds())
    gap, machine, execution = (result[k] for k in
        ('source_gap_semantics', 'machine_semantics', 'entry_execution_tuning_semantics'))
    gap['as_of'] = execution['as_of'] = now.isoformat()
    gap.update(status='observed_no_gap' if healthy else 'gap_observed',
        observed={'probe_results': 2, 'entry_traces': 2},
        diagnostics={} if healthy else {'machine_probe:route_snapshot_missing': 2,
            'machine_trace:source_quality_blocked_before_assessment': 2},
        diagnostics_by_scope={} if healthy else {
            'route:krx_nxt_integrated|machine_probe:route_snapshot_missing': 2,
            'KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET|route:krx_nxt_integrated|machine_trace:source_quality_blocked_before_assessment': 2},
        probe_route_counts={'krx_nxt_integrated': 2})
    gap['sources']['trace']['recent_count'] = 2
    from src.trading.market import session_contract
    context = session_contract.resolve_market_session(now)
    gap['fixed_watch_waits'].update(native_session_regime=context.session_regime,
        native_entry_allowed_by_clock=context.entry_allowed_by_clock)
    machine.update(status='observed_receipts_match' if healthy else 'source_invalid_observed',
        observation_count=2, source_invalid_count=0 if healthy else 2,
        source_invalid_blockers={} if healthy else {'candle_completed_timing_invalid': 2,
            'candle_source_quality': 2, 'candle_unknown_age': 2},
        scopes={'representative': {'matched_receipts': 2, 'live_pid_receipts': 2,
                                 'current_bundle': True}} if healthy else {})
    rows = [
        ('aims-1134842ea3b534c12091', '26fce9f47e552f2e65e95e9c7233c4f919222de04e7c0c22cd625cf33f392e4c',
         '2026-10-14T16:00:41.031593+09:00'),
        ('aims-219196881f9e972d92e0', 'c45406032abf7a2fa761a7a3e53745a18a9de95c6989bc63fdb00405febbdde0',
         '2026-10-14T16:00:54.643203+09:00')]
    machine['reversal_provider_lineage'] = {
        'status': 'observed', 'decision_authority': 'report_only', 'issues': {}, 'source_gaps': {},
        'exact_attempt_join_gap_count': 0, 'current_pid_coverage': 'exact_live_pid',
        'machine_observation_count': 2, 'trace_attempt_count': 2, 'exact_pid_filter': ['679747', '2339199'],
        'source_windows': {'requests': dict(gap['sources']['trace']), 'traces': dict(gap['sources']['trace'])},
        **{key: 0 for key in ('request_prepared_count', 'provider_transmission_attempt_count',
            'raw_response_observed_count', 'provider_timeout_count', 'enter_without_request_observed',
            'valid_pass_count', 'raw_pass_count', 'auxiliary_response_contract_valid_count',
            'execution_valid_pass_count')},
        'raw_verdict_counts': {},
        'attempt_ledger': [dict(evaluation_attempt_id=attempt, machine_observation_sha256=digest,
            decision_trace_id='trace-' + attempt,
            producer_pid='679747', producer_start_ticks='2339199',
            machine_bundle_sha256=machine['current_bundle_sha256'], trace_decision_ts=at,
            machine_action='BLOCK' if healthy else 'SOURCE_INVALID', request_prepared=False,
            effective_screen_status='not_requested_machine_nonentry' if healthy else 'not_requested_machine_source_invalid',
            raw_verdict=None, auxiliary_response_contract_valid=None, post_response_execution_valid=None,
            transmission_attempt_observed=False, raw_response_observed=False, timeout=False,
            execution_errors=[]) for attempt, digest, at in rows],
    }
    return result


def _provider_health_fixture(verdict='CAUTION', terminal='rejected'):
    result = _recorded_guard_health_fixture(healthy=True)
    lineage = result['machine_semantics']['reversal_provider_lineage']
    rows = lineage['attempt_ledger']
    for index,row in enumerate(rows):
        row.update(machine_action='ENTER_NOW', decision_trace_id='trace-' + str(index),
            effective_screen_status=verdict.lower(), raw_verdict=verdict,
            request_prepared=True, transmission_attempt_observed=True, raw_response_observed=True,
            auxiliary_response_contract_valid=True, post_response_execution_valid=True)
    for key in ('request_prepared_count', 'provider_transmission_attempt_count', 'raw_response_observed_count',
                'auxiliary_response_contract_valid_count'):
        lineage[key] = 2
    lineage.update(raw_verdict_counts={verdict: 2}, raw_pass_count=2 if verdict == 'PASS' else 0,
        valid_pass_count=2 if verdict == 'PASS' else 0, execution_valid_pass_count=2 if verdict == 'PASS' else 0)
    if verdict == 'PASS':
        attempts=[]
        for index,row in enumerate(rows):
            fields=dict(async_producer_pid=row['producer_pid'], async_producer_start_ticks=row['producer_start_ticks'],
                evaluation_attempt_id=row['evaluation_attempt_id'], ai_decision_trace_id=row['decision_trace_id'],
                entry_machine_bundle_sha256=row['machine_bundle_sha256'], async_request_id='async-' + str(index),
                async_machine_action='ENTER_NOW', async_auxiliary_verdict='PASS', async_auxiliary_status='pass',
                async_provider_called=True, async_disposition=terminal,
                async_disposition_reason='commit_allowed' if terminal == 'accepted_to_entry_path' else 'result_deadline_expired',
                async_disposition_event_id=hashlib.sha256(('terminal' + str(index)).encode()).hexdigest())
            attempts.append(dict(emitted_at=row['trace_decision_ts'], fields=fields))
            if terminal == 'accepted_to_entry_path':
                returned=dict(fields, async_disposition='entry_path_returned', async_disposition_reason='entry_cooldown_active',
                    async_disposition_event_id=hashlib.sha256(('returned' + str(index)).encode()).hexdigest())
                attempts.append(dict(emitted_at=row['trace_decision_ts'], fields=returned))
        result['async_disposition_coverage'] = dict(coverage='bounded_trace_projection_complete',
            denominator_partial=False, attempt_projection=attempts)
    return result


@pytest.mark.parametrize('verdict,terminal', [('CAUTION', 'rejected'), ('VETO', 'rejected'),
    ('PASS', 'rejected'), ('PASS', 'accepted_to_entry_path')])
def test_complete_provider_decisions_and_exact_main_closed_pass_are_observation_warning(verdict, terminal):
    result=_provider_health_fixture(verdict, terminal)
    assert monitor.observation_health_projection(result)['status']=='warning_pending'


def test_pass_native_invalidation_requires_exact_known_terminal_and_keeps_observation_pending():
    result=_provider_health_fixture('PASS')
    result['machine_semantics']['reversal_provider_lineage']['execution_valid_pass_count']=0
    for row in result['machine_semantics']['reversal_provider_lineage']['attempt_ledger']:
        row.update(post_response_execution_valid=False, execution_errors=['reversal_signal_expired'])
    for item in result['async_disposition_coverage']['attempt_projection']:
        item['fields']['async_disposition_reason']='reversal_signal_expired'
    assert monitor.observation_health_projection(result)['status']=='warning_pending'


def test_required_feature_recheck_uses_canonical_guard_screen():
    result=_recorded_guard_health_fixture()
    machine=result['machine_semantics']
    machine.update(source_invalid_count=1,required_feature_guard_count=1)
    machine['reversal_provider_lineage']['attempt_ledger'][1].update(machine_action='RECHECK',
        effective_screen_status='not_requested_required_feature_insufficient')
    assert monitor.observation_health_projection(result)['status']=='warning_pending'


@pytest.mark.parametrize('mutation', ['no_terminal', 'no_return', 'unknown_terminal', 'wrong_trace',
    'wrong_pid', 'uncertain_return', 'failed_submit', 'contradictory_submit', 'unvalidated_response',
    'unknown_verdict', 'timeout', 'unknown_contract_error', 'conflicting_event'])
def test_provider_observation_warning_cannot_hide_missing_consumption_or_contract_failure(mutation):
    from copy import deepcopy
    result=_provider_health_fixture('PASS', 'accepted_to_entry_path')
    lineage=result['machine_semantics']['reversal_provider_lineage']
    events=result['async_disposition_coverage']['attempt_projection']
    if mutation=='no_terminal':
        result['async_disposition_coverage']['attempt_projection']=[]
    elif mutation=='no_return':
        result['async_disposition_coverage']['attempt_projection']=[e for e in events if e['fields']['async_disposition']!='entry_path_returned']
    elif mutation=='unknown_terminal':events[0]['fields']['async_disposition_reason']='unknown_contract_failure'
    elif mutation=='wrong_trace':events[0]['fields']['ai_decision_trace_id']='other'
    elif mutation=='wrong_pid':events[0]['fields']['async_producer_pid']='999'
    elif mutation=='uncertain_return':events[1]['fields']['async_disposition_reason']='entry_execution_exception_or_uncertain'
    elif mutation in ('failed_submit', 'contradictory_submit'):
        for event in events:
            if event['fields']['async_disposition']=='entry_path_returned':
                event['fields'].update(async_disposition_reason='order_bundle_submitted',async_entry_submit_attempt_id='submit',
                    async_entry_broker_attempts='1',async_entry_broker_accepted=True,async_entry_submit_outcome=False)
        if mutation=='contradictory_submit':
            other=deepcopy(events[1]);other['fields']['async_entry_submit_outcome']=True
            other['fields']['async_disposition_event_id']='b'*64;events.append(other)
    elif mutation=='unvalidated_response':lineage['attempt_ledger'][0]['auxiliary_response_contract_valid']=False
    elif mutation=='unknown_verdict':lineage['attempt_ledger'][0]['raw_verdict']='UNKNOWN'
    elif mutation=='timeout':lineage['attempt_ledger'][0]['timeout']=True
    elif mutation=='unknown_contract_error':lineage['attempt_ledger'][0]['execution_errors']=['path_auxiliary_feature_input_conflict']
    elif mutation=='conflicting_event':
        other=deepcopy(events[0]);other['fields']['async_disposition_reason']='generation_superseded';events.append(other)
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('healthy', [False, True])
def test_recorded_native_guards_and_healthy_fixed_receipts_with_scanner_zero_are_warning(healthy):
    result = _recorded_guard_health_fixture(healthy=healthy)
    before = json.dumps(result, sort_keys=True)
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'warning_pending'
    assert health['reason'] == 'recorded_guard_or_cohort_pending'
    assert health['current_observation_verified'] is False and health['full_coverage_proven'] is False
    assert json.dumps(result, sort_keys=True) == before


@pytest.mark.parametrize('path,value', [
    ('source_gap_semantics.diagnostics', {'machine_probe:unknown_contract_failure': 2}),
    ('source_gap_semantics.diagnostics', {'machine_probe:route_snapshot_missing': []}),
    ('source_gap_semantics.diagnostics_by_scope', {}),
    ('source_gap_semantics.issues', {'machine_trace:path_auxiliary_feature_input_conflict': 10}),
    ('source_gap_semantics.observed.entry_traces', False),
    ('machine_semantics.observation_count', 3),
    ('machine_semantics.source_invalid_count', 1),
    ('machine_semantics.reversal_provider_lineage.status', 'partial_source_gap'),
    ('machine_semantics.reversal_provider_lineage.source_gaps', {'observation_trace_unresolved': 1}),
    ('machine_semantics.reversal_provider_lineage.exact_attempt_join_gap_count', 1),
    ('machine_semantics.reversal_provider_lineage.exact_pid_filter', ['679748', '2339199']),
    ('machine_semantics.reversal_provider_lineage.source_windows.requests.status', 'partial'),
    ('machine_semantics.reversal_provider_lineage.valid_pass_count', 1),
    ('machine_semantics.source_status', 'unobservable:FileNotFoundError'),
    ('async_disposition_coverage', {'attempt_projection': [{'fields': {'async_auxiliary_verdict': 'PASS'}}]}),
    ('async_disposition_coverage', {'attempt_projection': [{'fields': {
        'async_machine_action': 'RECHECK', 'async_provider_called': True}}]}),
])
def test_recorded_guard_warning_never_hides_contract_failure_or_unjoined_evidence(path, value):
    result = _recorded_guard_health_fixture()
    keys = path.split('.')
    target = result
    for key in keys[:-1]: target = target[key]
    target[keys[-1]] = value
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'


def test_machine_30m_receipts_and_source_10m_observations_keep_distinct_denominators():
    result = _recorded_guard_health_fixture()
    gap = result['source_gap_semantics']
    gap.update(diagnostics={}, diagnostics_by_scope={}, observed={}, status='unobservable', probe_route_counts={})
    # Earlier machine guards can remain30m after the10m source window empties.
    assert monitor.observation_health_projection(result)['status'] == 'warning_pending'


@pytest.mark.parametrize('reason', ['0B_missing','0B_age_exceeded','0D_missing','0D_age_exceeded'])
def test_known_sparse_source_availability_diagnostics_remain_warning_not_contract_success(reason):
    result=_recorded_guard_health_fixture()
    gap=result['source_gap_semantics']
    gap['diagnostics']={'machine_probe:'+reason:2}
    gap['diagnostics_by_scope']={'route:krx_nxt_integrated|machine_probe:'+reason:2}
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    gap['issues']={'machine_probe:coverage_degraded:krx_nxt_integrated':1}
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('reason',['reversal_first_signal_invalidated','reversal_first_price_hold_invalidated','reversal_signal_generation_changed',
                                  'required_feature_blocked_before_assessment'])
def test_native_validated_lifecycle_diagnostic_is_not_an_observer_failure(reason):
    result=_recorded_guard_health_fixture()
    gap=result['source_gap_semantics']
    gap['diagnostics']={'machine_trace:'+reason:2}
    gap['diagnostics_by_scope']={'KRX|KRX_REGULAR|route:krx_nxt_integrated|machine_trace:'+reason:2}
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    key=next(iter(gap['diagnostics_by_scope']))
    gap['diagnostics_by_scope'][key]=3
    assert monitor.observation_health_projection(result)['status']=='not_eligible'
    gap['diagnostics_by_scope'][key]=2
    gap['diagnostics']['machine_probe:required_feature_insufficient_unclassified']=1
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


def test_old_pass_and_other_pid_counts_are_preserved_but_not_current_health_denominator():
    from copy import deepcopy
    result=_provider_health_fixture('PASS')
    current=_observation_health_fixture()
    now=monitor.stamp(result['as_of']); actor=['679747','2339199']
    source=deepcopy(current['source_gap_semantics']);source['as_of']=now.isoformat()
    from src.trading.market import session_contract
    native=session_contract.resolve_market_session(now)
    source['fixed_watch_waits'].update(native_session_regime=native.session_regime,
        native_entry_allowed_by_clock=native.entry_allowed_by_clock)
    machine=deepcopy(current['machine_semantics'])
    result['source_gap_semantics']['current_health_cohort']=monitor._health_cohort(source,actor,now,excluded=2)
    result['machine_semantics']['current_health_cohort']=monitor._health_cohort(machine,actor,now,excluded=2)
    # Unknown historical PASS remains in the original30m record. There is no
    # fabricated current terminal or full-coverage assertion.
    result['async_disposition_coverage']={}
    result['incidents']['machine_auxiliary_intraday_source_gap']={
        'status':'historical_unresolved','current_status':'historical_not_current_cohort',
        'last_seen':now.isoformat(),'issues':{'machine_trace:path_auxiliary_feature_input_conflict':1}}
    assert result['machine_semantics']['observation_count']==2
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    result['observer_generation']={'selector_reported_pid_receipt':{'pid':999,'start_ticks':'888'}}
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('identity', ['historical','missing','conflicting'])
def test_source_health_reuses_three_loaded_reads_and_never_discards_unknown_actor(tmp_path,monkeypatch,identity):
    now=monitor.stamp('2026-10-14T16:05:00+09:00')
    trace=dict(decision_ts=now.isoformat(),decision_stage='entry_screen',stock_code='036930',
        machine_evaluation_status='assessment_contract_invalid',machine_contract_error='path_auxiliary_feature_input_conflict')
    if identity!='missing':trace.update(async_producer_pid='8',async_producer_start_ticks='80')
    if identity=='conflicting':trace['continuous_reversal_consumption']={'pid':9,'process_start_ticks':'90'}
    calls=[]
    def read(path,*a,**k):
        calls.append(path)
        return ([trace] if 'ai_decision_trace' in str(path) else []),dict(status='complete')
    monkeypatch.setattr(monitor,'_recent_source_rows',read)
    token=monitor._HEALTH_ACTOR.set(['9','90'])
    try:observed=monitor.source_gap_semantics(tmp_path,now)
    finally:monitor._HEALTH_ACTOR.reset(token)
    assert len(calls)==3
    assert observed['issues']['machine_trace:path_auxiliary_feature_input_conflict']==1
    view=observed['current_health_cohort']['view']
    assert bool(view['issues'])==(identity!='historical')
    assert observed['current_health_cohort']['excluded_observation_count']==int(identity=='historical')


@pytest.mark.parametrize('age,expected', [(600,1),(600.001,0)])
def test_provider_current_health_inclusive_600s_boundary_reuses_two_reads(tmp_path,monkeypatch,age,expected):
    _,observations,_,_,_=_current_provider_lineage_fixture(tmp_path,verdicts=('CAUTION',))
    now=monitor.stamp(observations[0]['captured_at'])+timedelta(seconds=age)
    read=monitor._recent_source_rows;calls=[]
    def counted(*a,**k):calls.append(a[0]);return read(*a,**k)
    monkeypatch.setattr(monitor,'_recent_source_rows',counted)
    token=monitor._HEALTH_ACTOR.set(['123','456'])
    try:original=monitor._reversal_provider_lineage(tmp_path,now,observations,tail_bytes=16384,pid_identity=(123,'456'))
    finally:monitor._HEALTH_ACTOR.reset(token)
    assert len(calls)==2 and original['machine_observation_count']==1
    cohort=original['current_health_cohort']
    assert cohort['window_seconds']==600 and cohort['view']['machine_observation_count']==expected
    assert cohort['view']['source_gaps']=={}
    assert cohort['excluded_observation_count']==1-expected


def test_no_applicable_b807_observations_are_warning_pending_not_pass_or_recovery(monkeypatch):
    result = _observation_health_fixture()
    before = json.dumps(result, sort_keys=True)
    monkeypatch.setattr(monitor.Path, 'open', lambda *a, **k: pytest.fail('health_projection_must_not_read'))
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'warning_pending'
    assert health['severity'] == 'warning' and health['unmet_conditions'] == []
    assert health['current_observation_verified'] is False and health['full_coverage_proven'] is False
    assert health['runtime_effect'] is False and health['allowed_runtime_apply'] is False
    assert json.dumps(result, sort_keys=True) == before
    assert result['semantic_status'] == 'partial' and result['status'] == 'unobservable'
    assert result['source_as_of'] == '2026-10-14T15:15:18.387222+09:00'
    provenance = result['input_provenance']
    assert provenance['snapshot_as_of'] == '2026-10-14T15:35:12.585430+09:00'
    assert provenance['snapshot_age_seconds'] == pytest.approx(72.526829)
    assert provenance['latest_event_age_seconds'] == pytest.approx(1650.237188)
    assert result['incidents']['old']['status'] == 'historical_unresolved'
    assert result['entry_execution_tuning_semantics']['entry_split']['primary_operating_ev_pct'] is None


@pytest.mark.parametrize('path,value', [
    ('input_provenance', None), ('input_provenance.dry_run', True),
    ('input_provenance.snapshot_as_of', 1791960000),
    ('input_provenance.snapshot_age_seconds', True), ('input_provenance.snapshot_age_seconds', float('nan')),
    ('input_provenance.snapshot_age_seconds', 10**400),
    ('input_provenance.latest_event_age_seconds', float('inf')),
    ('input_provenance.target_date', '2026-10-13'), ('input_provenance.snapshot_schema', 'wrong'),
    ('input_provenance.row_count', True), ('input_provenance.row_count', 1),
    ('input_provenance.identity_missing_events', 1),
    ('input_provenance.auxiliary_ai_semantic_issue_counts', {'receipt_mismatch': 1}),
    ('input_provenance.snapshot_order', 'duplicate_or_reversed'),
    ('input_provenance.snapshot_as_of', '2026-10-14T15:00:00+09:00'),
    ('input_provenance.latest_event_at', '2026-10-14T15:36:26+09:00'),
    ('execution_mode', 'source_only'), ('execution_status', 'deferred'), ('runtime_effect', True),
    ('blocker', []),
    ('source_gap_semantics', {}), ('source_gap_semantics.sources.trace.status', 'unobservable'),
    ('source_gap_semantics.sources.probe.window_covered', False),
    ('source_gap_semantics.sources.pending.malformed_rows', 1),
    ('source_gap_semantics.sources.pending.incomplete_last_line', True),
    ('source_gap_semantics.sources.pending.bytes_read', True),
    ('source_gap_semantics.observed', {'probe_results': 1}),
    ('source_gap_semantics.issues', {'machine_probe:0B_missing': 1}),
    ('source_gap_semantics.diagnostics', {'machine_probe:0B_age_exceeded': 1}),
    ('source_gap_semantics.issues_by_scope', {'scope|machine_probe:0B_missing': 1}),
    ('source_gap_semantics.diagnostics_by_scope', {'scope|machine_probe:0B_age_exceeded': 1}),
    ('source_gap_semantics.fixed_watch_waits.unclassified_or_actionable_wait_count', 1),
    ('source_gap_semantics.fixed_watch_waits.reason_counts', {'route_snapshot_missing': 125}),
    ('source_gap_semantics.fixed_watch_waits.native_entry_allowed_by_clock', True),
    ('machine_semantics.selection_status', 'unobservable:policy_missing'),
    ('machine_semantics.source_status', 'unobservable:FileNotFoundError'),
    ('machine_semantics.source_status', False),
    ('machine_semantics.publication.status', 'invalid'), ('machine_semantics.read_count', 0),
    ('machine_semantics.window_coverage', []),
    ('machine_semantics.observation_count', 1), ('machine_semantics.source_invalid_count', 1),
    ('machine_semantics.observation_count', False),
    ('machine_semantics.selection.representative.score_contract_valid', False),
    ('entry_execution_tuning_semantics.bootstrap.status', 'verification_not_passed'),
    ('entry_execution_tuning_semantics.entry_split.verification', 'not_verified'),
    ('entry_execution_tuning_semantics.entry_split.status', 'unknown'),
    ('entry_execution_tuning_semantics.entry_split.status', []),
    ('entry_execution_tuning_semantics.entry_split.verification_receipt.verified', 1),
    ('entry_execution_tuning_semantics.entry_split.verification_receipt.full_report_bytes_read', 1),
    ('entry_execution_tuning_semantics.entry_split.policy_runtime_apply_allowed', True),
    ('entry_execution_tuning_semantics.pre_submit_delay.bootstrap_env_match', False),
    ('entry_execution_tuning_semantics.allowed_runtime_apply', True),
    ('incidents.current', {'status': 'active', 'last_seen': '2026-10-14T15:36:20+09:00'}),
    ('incidents.current', {'status': 'historical_unresolved', 'last_seen': '2026-10-14T15:36:20+09:00'}),
    ('incidents.current', []), ('notification_pending', ['current']),
    ('incidents.current', {'status': [], 'last_seen': '2026-10-14T15:36:20+09:00'}),
])
def test_no_applicable_health_rejects_actual_failure_missing_and_contradictory_evidence(path, value):
    result = _observation_health_fixture()
    keys = path.split('.')
    selected = result
    for key in keys[:-1]: selected = selected[key]
    selected[keys[-1]] = value
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'not_eligible' and health['severity'] == 'unchanged'
    assert health['unmet_conditions'] and health['current_observation_verified'] is False


@pytest.mark.parametrize('value', [None, [], True, 5, {}, {'as_of': True}, {'as_of': 10**400}])
def test_observation_health_malformed_envelope_never_throws_or_warns_pending(value):
    assert monitor.observation_health_projection(value)['status'] == 'not_eligible'


def test_empty_loaded_population_marker_requires_explicit_producer_count_and_exact_clock():
    result = _observation_health_fixture()
    inp = result['input_provenance']
    latest = monitor.stamp(inp['snapshot_as_of']) - timedelta(days=1)
    inp.update(latest_event_at=latest.isoformat(),
               latest_event_age_seconds=(monitor.stamp(result['as_of'])-latest).total_seconds())
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'
    marker = monitor.snapshot([], monitor.stamp(inp['snapshot_as_of']))
    assert marker['latest_event_at'] == latest.isoformat()
    inp.update(latest_event_status=marker['latest_event_status'],
               loaded_recent_event_count=marker['loaded_recent_event_count'])
    assert monitor.observation_health_projection(result)['status'] == 'warning_pending'
    inp['loaded_recent_event_count'] = False
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'
    inp['loaded_recent_event_count'] = 0
    inp['latest_event_at'] = (latest-timedelta(seconds=1)).isoformat()
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'
    inp['snapshot_as_of'] = '0001-01-01T00:00:00+09:00'
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'


def test_boundary_wait_carryover_does_not_turn_into_failure_when_current_clock_changes():
    result = _observation_health_fixture()
    prior_now = monitor.stamp(result['as_of'])
    now = monitor.stamp('2026-10-14T16:01:00+09:00')
    delta = now-prior_now
    result['as_of'] = now.isoformat()
    for key in ('source_gap_semantics', 'entry_execution_tuning_semantics'):
        result[key]['as_of'] = now.isoformat()
    inp = result['input_provenance']
    inp['evaluated_at'] = now.isoformat()
    inp['snapshot_as_of'] = (monitor.stamp(inp['snapshot_as_of'])+delta).isoformat()
    inp['latest_event_age_seconds'] += delta.total_seconds()
    from src.trading.market import session_contract
    context = session_contract.resolve_market_session(now)
    result['source_gap_semantics']['fixed_watch_waits'].update(
        native_session_regime=context.session_regime, native_entry_allowed_by_clock=context.entry_allowed_by_clock)
    assert monitor.observation_health_projection(result)['status'] == 'warning_pending'
    result['source_gap_semantics']['fixed_watch_waits']['unclassified_or_actionable_wait_count'] = 1
    assert monitor.observation_health_projection(result)['status'] == 'not_eligible'


@pytest.mark.parametrize('when,reason,flags,boundary', [
    ('15:36:00', 'session_generation_mismatch', {}, True),
    ('15:36:00', 'route_snapshot_missing', {}, False),
    ('14:36:00', 'session_generation_mismatch', {}, False),
    ('16:36:00', 'session_generation_mismatch', {}, False),
    ('15:59:00', 'session_generation_mismatch', {'_observed_at': '16:01:00'}, True),
    ('16:00:00', 'session_generation_mismatch', {'_observed_at': '16:01:00'}, False),
    ('15:36:00', 'session_generation_mismatch', {'actual_order_submitted': 0}, False),
    ('15:36:00', 'session_generation_mismatch', {'broker_order_forbidden': 1}, False),
    ('15:36:00', 'session_generation_mismatch', {'venue_source_quality_status': 'blocked'}, False),
    ('15:36:00', 'session_generation_mismatch', {'watch_origin': 'SCANNER_PROMOTION'}, False),
    ('15:36:00', 'session_generation_mismatch', {'market_session_bucket': 'nxt_premarket'}, False),
])
def test_existing_probe_read_censuses_excluded_waits_without_hiding_actionable_failure(
        tmp_path, monkeypatch, when, reason, flags, boundary):
    row_at = monitor.stamp('2026-10-14T' + when + '+09:00')
    flags = dict(flags)
    observed_at = flags.pop('_observed_at', when)
    now = monitor.stamp('2026-10-14T' + observed_at + '+09:00')
    fields = dict(watch_origin='MAIN_FIXED_WATCH', source_quality_reason=reason,
                  venue_source_quality_status='pass', effective_venue='KRX',
                  market_session_bucket='krx_regular', actual_order_submitted='False', broker_order_forbidden='True')
    fields.update(flags)
    wait = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
                stock_code='005930', emitted_at=row_at.isoformat(), fields=fields)
    calls = []
    def existing_read(path, *args, **kwargs):
        calls.append(path)
        return ([wait] if 'pipeline_events' in str(path) else []), dict(status='complete')
    monkeypatch.setattr(monitor, '_recent_source_rows', existing_read)
    semantics = monitor.source_gap_semantics(tmp_path, now)
    assert len(calls) == 3
    census = semantics['fixed_watch_waits']
    assert census['count'] == 1 and census['session_boundary_wait_count'] == int(boundary)
    assert census['unclassified_or_actionable_wait_count'] == int(not boundary)
    assert census['reason_counts'] == {reason: 1}
    assert semantics['status'] == 'unobservable' and semantics['observed'] == {}
    assert semantics['runtime_effect'] is False


@pytest.mark.parametrize('when,flags,boundary', [
    ('19:39:59', {}, False),
    ('19:40:00', {}, True),
    ('19:44:59', {}, True),
    ('19:45:00', {}, True),
    ('19:59:59', {}, True),
    ('20:00:00', {}, False),
    ('16:36:00', {}, False),
    ('15:36:00', {}, False),
    ('19:46:00', {'effective_venue': 'KRX'}, False),
    ('19:46:00', {'effective_venue': 'UNKNOWN'}, False),
    ('19:46:00', {'effective_venue': []}, False),
    ('19:46:00', {'effective_venue': {}}, False),
    ('19:46:00', {'market_session_bucket': 'krx_regular'}, False),
    ('19:46:00', {'market_session_bucket': None}, False),
    ('19:46:00', {'market_session_bucket': []}, False),
    ('19:46:00', {'market_session_bucket': {}}, False),
    ('19:46:00', {'venue_source_quality_status': None}, False),
    ('19:46:00', {'venue_source_quality_status': 'blocked'}, False),
    ('19:46:00', {'source_quality_reason': 'route_snapshot_missing'}, False),
    ('19:46:00', {'source_quality_reason': 'fixed_watch_post_receipt_warmup'}, False),
    ('19:46:00', {'watch_origin': 'SCANNER_PROMOTION'}, False),
    ('19:46:00', {'_stock_code': '999999'}, False),
    ('19:46:00', {'actual_order_submitted': True}, False),
    ('19:46:00', {'actual_order_submitted': 0}, False),
    ('19:46:00', {'broker_order_forbidden': False}, False),
    ('19:46:00', {'broker_order_forbidden': 1}, False),
    ('19:46:00', {'broker_order_forbidden': None}, False),
])
def test_aftermarket_boundary_wait_requires_exact_closed_entry_clock_route_and_safety(
        tmp_path, when, flags, boundary):
    now = monitor.stamp('2026-10-14T' + when + '+09:00')
    flags = dict(flags)
    symbol = flags.pop('_stock_code', '005930')
    fields = dict(watch_origin='MAIN_FIXED_WATCH', source_quality_reason='session_generation_mismatch',
        venue_source_quality_status='pass', effective_venue='KRX_NXT_INTEGRATED',
        market_session_bucket='KRX_NXT_AFTERMARKET', actual_order_submitted=False,
        broker_order_forbidden=True)
    fields.update(flags)
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
        stock_code=symbol, emitted_at=now.isoformat(), fields=fields)
    _source_gap_files(tmp_path, now, probes=[row])
    semantics = monitor.source_gap_semantics(tmp_path, now)
    census = semantics['fixed_watch_waits']
    assert census['count'] == 1
    assert census['session_boundary_wait_count'] == int(boundary)
    assert census['unclassified_or_actionable_wait_count'] == int(not boundary)
    assert semantics['observed'] == {} and semantics['status'] == 'unobservable'
    assert semantics['runtime_effect'] is False


@pytest.mark.parametrize('row_clock', [
    '2026-10-14T19:57:00+09:00', '2026-10-13T19:56:00+09:00', 'invalid',
])
def test_terminal_boundary_does_not_admit_future_prior_date_or_malformed_row_clock(tmp_path, row_clock):
    now = monitor.stamp('2026-10-14T19:56:20+09:00')
    fields = dict(watch_origin='MAIN_FIXED_WATCH', source_quality_reason='session_generation_mismatch',
        venue_source_quality_status='pass', effective_venue='KRX_NXT_INTEGRATED',
        market_session_bucket='KRX_NXT_AFTERMARKET', actual_order_submitted=False,
        broker_order_forbidden=True)
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
        stock_code='005930', emitted_at=row_clock, fields=fields)
    _source_gap_files(tmp_path, now, probes=[row])
    semantics = monitor.source_gap_semantics(tmp_path, now)
    assert semantics['fixed_watch_waits']['count'] == 0
    assert semantics['fixed_watch_waits']['session_boundary_wait_count'] == 0
    assert semantics['status'] == 'unobservable'


def test_terminal_boundary_census_keeps_unknown_actor_pending_source_incident(tmp_path):
    now = monitor.stamp('2026-10-14T19:56:20.472471+09:00')
    fields = dict(watch_origin='MAIN_FIXED_WATCH', source_quality_reason='session_generation_mismatch',
        venue_source_quality_status='pass', effective_venue='KRX_NXT_INTEGRATED',
        market_session_bucket='KRX_NXT_AFTERMARKET', actual_order_submitted='False',
        broker_order_forbidden='True')
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
        stock_code='005930', emitted_at=(now-timedelta(seconds=1)).isoformat(), fields=fields)
    _source_gap_files(tmp_path, now, probes=[row])
    semantics = monitor.source_gap_semantics(tmp_path, now)
    incident = dict(status='pending', first_seen='2026-10-14T18:21:44.960015+09:00',
        last_seen='2026-10-14T18:21:44.960015+09:00',
        issues={'machine_probe:coverage_degraded:krx_nxt_integrated': 1},
        issues_by_scope={'route:krx_nxt_integrated|machine_probe:coverage_degraded': 1},
        examples=[{'occurred_at': '2026-10-14T18:18:51.659169', 'reason': 'route_snapshot_missing'}])
    original = json.dumps(incident, sort_keys=True)
    result = dict(as_of=now.isoformat(), source_as_of='2026-10-14T19:15:13.589614+09:00',
        incidents={'machine_auxiliary_intraday_source_gap': incident}, notification_pending=[])
    monitor.attach_source_gap_semantics(result, semantics)
    assert json.dumps(result['incidents']['machine_auxiliary_intraday_source_gap'], sort_keys=True) == original
    assert result['source_as_of'] == '2026-10-14T19:15:13.589614+09:00'
    assert result['notification_pending'] == []
    assert semantics['fixed_watch_waits']['session_boundary_wait_count'] == 1
    assert semantics['status'] == 'unobservable' and semantics['async_pass_projection'] == []


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
    previous_stat=raw.stat()
    raw.write_text(raw.read_text().replace('355390','355391'))
    os.utime(raw,ns=(previous_stat.st_atime_ns,previous_stat.st_mtime_ns))
    rewritten=monitor.pre_submit_delay_source_semantics(tmp_path,now,healthy['cursor'])
    assert rewritten['diagnostics']['raw_generation_rewritten_or_legacy_cursor']==1
    assert rewritten['sources']['raw']=='partial'
    raw.write_text("")
    reset = monitor.pre_submit_delay_source_semantics(tmp_path, now, healthy["cursor"])
    assert reset["sources"]["raw"] == "partial"
    assert reset["status"] != "observed_no_gap"
    raw.write_text(json.dumps(event) + "\n")
    invalid_cursor = {**healthy["cursor"], "minutes": []}
    reset = monitor.pre_submit_delay_source_semantics(tmp_path, now, invalid_cursor)
    assert reset["sources"]["raw"] == "partial"
    manifest_path = next((tmp_path / 'pipeline_event_summaries').glob('*manifest*.json'))
    legacy_manifest = json.loads(manifest_path.read_text())
    legacy_manifest.pop('recent_summary', None)
    manifest_path.write_text(json.dumps(legacy_manifest))
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
    assert "observer_generation" not in saved
    assert not (tmp_path / "data/runtime/runtime_release_selection.lock").exists()


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


def test_large_split_without_verified_projection_stays_partial_without_full_read(tmp_path, monkeypatch):
    patch = _entry_axis_fixture(tmp_path)
    try:
        path = tmp_path / "report/entry_split_order_plan" / f"entry_split_order_plan_{START.date().isoformat()}.json"
        with path.open("ab") as out:
            out.write(b" " * (8 * 1024 * 1024))
        small = monitor._small_json
        def bounded_only(candidate):
            assert candidate != path, "monitor must not read the large native report"
            return small(candidate)
        monkeypatch.setattr(monitor, "_small_json", bounded_only)
        result = monitor.entry_execution_tuning_semantics(tmp_path, START)
        assert result["bootstrap"]["status"] == "verified"
        assert result["entry_split"]["status"] == "unobservable"
        assert result["entry_split"]["verification"] == "not_verified"
        assert result["status"] == "partial_unobservable"
        assert result["entry_split"].get("primary_operating_ev_pct") is None
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


def reversal_semantic_fixture(tmp_path, monkeypatch, *, turned=True):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.tests.test_continuous_reversal import family_reports, rows
    from src.engine.scalping import continuous_reversal as kernel, continuous_reversal_policy as policy
    from src.engine.scalping import ai_decision_trace as trace, entry_strategy_policy as legacy
    from src.engine.scalping.mechanistic_entry_runtime_policy import digest
    now = datetime.fromisoformat('2026-10-07T10:00:00+09:00')
    initial(tmp_path)
    policy.publish(tmp_path, '2026-10-06', '2026-10-06', *family_reports())
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective
    bundle = load_effective(data_root=tmp_path, target_date='2026-10-07')
    family = bundle['continuous_reversal']
    state = kernel.ReversalState()
    for i, row in enumerate(rows([100, 99, 100])):
        row[0] = now.timestamp() - .3 + i*.1
        state.observe(row, symbol='005930', venue='KRX', session='KRX_REGULAR')
    assessment, inp, prompt, schema = policy.assess(family, state.snapshot() if turned else None,
        symbol='005930', session='KRX_REGULAR')
    raw = dict(stock_code='005930', session_bucket='KRX_REGULAR', effective_venue='KRX',
        evaluation_attempt_id='attempt-1', entry_machine_input_as_of=now.timestamp()-.15)
    native = dict(family_sha256=family['family_sha256'], source_date=family['source_date'],
        publication_date=family['publication_date'], effective_date=family['effective_date'],
        machine_component_sha256=digest(family['machine_cells']), auxiliary_component_sha256=digest(family['auxiliary_cells']),
        arm=family['auxiliary_cells'][assessment['cell_key']]['payload']['arm'] if turned else None,
        snapshot_read_at=now.timestamp()-.01, snapshot_cutoff=raw['entry_machine_input_as_of'],
        input_sha256=digest(inp) if inp is not None else None,
        prompt_sha256=digest(prompt) if inp is not None else None,
        response_schema_sha256=digest(schema) if inp is not None else None)
    monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED', '1')
    monkeypatch.setattr(trace, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(trace, '_now', lambda: now)
    trace.capture_machine_observation(exact_payload=raw, setup_evidence={}, assessment=assessment,
        bundle_sha256=bundle['bundle_sha256'], reversal_context=native,
        reversal_request=dict(input=inp, prompt=prompt, response_schema=schema) if inp else None)
    path = tmp_path/'ai_decision_payloads/ai_decision_payloads_2026-10-07.jsonl'
    observation = json.loads(path.read_text().splitlines()[-1])
    def write(value):
        value = {k: v for k, v in value.items() if k != 'machine_observation_sha256'}
        value['machine_observation_sha256'] = __import__('hashlib').sha256(trace._json_bytes(value)).hexdigest()
        path.write_text(json.dumps(value)+'\n')
    monkeypatch.setattr(legacy, 'select', lambda *a, **k: pytest.fail('native reversal called legacy selector'))
    monkeypatch.setattr(legacy, 'machine_support_adjusted_win_rate', lambda *a: pytest.fail('native reversal called score gate'))
    return observation, write, now


@pytest.mark.parametrize('members',[
    [('unspecified_legacy','invalid'),('unspecified_legacy','required')],
    [('unspecified_legacy','invalid'),('unspecified_legacy','invalid'),('probe_observation','matched')],
    [('probe_observation','matched')],
    [('unspecified_legacy','required'),('probe_observation','invalid')],
    [('counterfactual','matched')],
    [([],'invalid')],
])
def test_real_machine_producer_role_partition_to_health_with_no_provider_calls(tmp_path,monkeypatch,members):
    from copy import deepcopy
    from src.engine.scalping.ai_decision_trace import _json_bytes
    original,write,now=reversal_semantic_fixture(tmp_path,monkeypatch)
    actor=[str(original['runtime_consumption']['pid']),original['runtime_consumption']['process_start_ticks']]
    payload=[];traces=[]
    for index,(role,kind) in enumerate(members):
        row=deepcopy(original);row['evaluation_role']=role
        row['source']['exact_payload']['evaluation_role']=role
        row['label_context']['evaluation_attempt_id']='partition-attempt-'+str(index)
        row['source']['exact_payload']['evaluation_attempt_id']=row['label_context']['evaluation_attempt_id']
        native=row['runtime_consumption']['continuous_reversal'];native['evaluation_role']=role
        native['provider_state']='probe_observation_provider_forbidden' if role=='probe_observation' else 'eligible_not_yet_requested'
        if kind!='matched':
            row['source']['assessment']=dict(schema='mechanistic_entry_source_invalid_v1' if kind=='invalid' else 'mechanistic_entry_required_feature_v1',
                action='SOURCE_INVALID' if kind=='invalid' else 'RECHECK',
                reason='ai_input_preflight_blocked' if kind=='invalid' else 'required_feature_input_insufficient',
                runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False,broker_order_forbidden=True)
            row['source']['setup_evidence'].update(source_quality_status='blocked',source_quality_blockers=['candle_unknown_age'])
            if role=='unspecified_legacy':row['runtime_consumption'].pop('continuous_reversal')
        else:
            native['exact_payload_sha256']=hashlib.sha256(_json_bytes(row['source']['exact_payload'])).hexdigest()
        write(row);path=tmp_path/'ai_decision_payloads'/f'ai_decision_payloads_{now.date()}.jsonl'
        row=json.loads(path.read_text());payload.append(row)
        if role=='unspecified_legacy':
            traces.append(dict(schema='ai_decision_trace_v1',decision_ts=now.isoformat(),decision_trace_id='trace-'+str(index),
                evaluation_attempt_id=row['label_context']['evaluation_attempt_id'],machine_observation_sha256=row['machine_observation_sha256'],
                machine_bundle_sha256=row['bundle_sha256'],async_producer_pid=actor[0],async_producer_start_ticks=actor[1],
                entry_mechanistic_action=row['source']['assessment']['action'],provider_called=False,
                entry_ai_screen_status='not_requested_machine_source_invalid' if kind=='invalid' else 'not_requested_required_feature_insufficient'))
    # A duplicate physical capture must not add a fourth semantic observation.
    path.write_text(''.join(json.dumps(row)+'\n' for row in payload+payload[:1]))
    for kind,rows in [('requests',[dict(captured_at=now.isoformat(),request_id='unrelated',endpoint='other')]),
                      ('trace',traces or [dict(decision_ts=now.isoformat(),decision_trace_id='unrelated')])]:
        source=tmp_path/('ai_decision_'+kind)/f'ai_decision_{kind}_{now.date()}.jsonl'
        source.parent.mkdir();source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    token=monitor._HEALTH_ACTOR.set(actor)
    try:semantics=monitor.machine_semantics(tmp_path,now)
    finally:monitor._HEALTH_ACTOR.reset(token)
    view=semantics['current_health_cohort']['view'];partition=view['observation_role_partition']
    if not isinstance(members[0][0],str):
        assert semantics['issues']==view['issues']=={'machine_observation_role_claim_invalid':1}
        assert partition['observation_count']==0
        return
    assert partition['observation_count']==view['observation_count']==len(members),(semantics['issues'],semantics['examples'])
    assert partition['provider_eligible_count']==sum(role=='unspecified_legacy' for role,_ in members)
    assert partition['role_counts']==dict(__import__('collections').Counter(role for role,_ in members))
    # Use the actual producer census in the real pure consumer; other stages
    # stay small fixed receipts. Rebase their clocks/date to this native fixture.
    result=_observation_health_fixture();old=monitor.stamp(result['as_of']);delta=now-old;daydelta=now.date()-old.date()
    def rebase(value):
        if isinstance(value,dict):return {k:rebase(v) for k,v in value.items()}
        if isinstance(value,list):return [rebase(v) for v in value]
        if isinstance(value,str) and len(value)>10 and value[10]=='T' and monitor.stamp(value):return (monitor.stamp(value)+delta).isoformat()
        if isinstance(value,str) and len(value)==10 and monitor.stamp(value):return (monitor.stamp(value)+daydelta).date().isoformat()
        return value
    result=rebase(result);source=result['source_gap_semantics']
    from src.trading.market import session_contract
    context=session_contract.resolve_market_session(now)
    source['fixed_watch_waits'].update(count=0,session_boundary_wait_count=0,reason_counts={},
        native_session_regime=context.session_regime,native_entry_allowed_by_clock=context.entry_allowed_by_clock)
    source['current_health_cohort']=monitor._health_cohort(deepcopy(source),actor,now)
    result['machine_semantics']=semantics
    health=monitor.observation_health_projection(result)
    assert health['status']==('not_eligible' if members[0][0]=='counterfactual' else 'warning_pending'),health
    if members[0][0]!='counterfactual':
        assert view['reversal_provider_lineage']['machine_observation_count']==partition['provider_eligible_count']
        assert health['current_observation_verified'] is False


@pytest.mark.parametrize('turned', [True, False])
def test_reversal_native_source_date_and_receipt_without_legacy_raw(tmp_path, monkeypatch, turned):
    observation, write, now = reversal_semantic_fixture(tmp_path, monkeypatch, turned=turned)
    result = monitor.machine_semantics(tmp_path, now)
    assert result['status'] == 'observed_receipts_match', result
    assert len(result['selection']) == 12
    assert result['selection_family'] == 'continuous_reversal'
    assert next(iter(result['scopes'].values()))['native_reversal_receipt'] == 1
    # Old natural captures stay auditable, without fabricated new receipts.
    del observation['runtime_consumption']['continuous_reversal']
    write(observation)
    assert monitor.machine_semantics(tmp_path, now)['status'] == 'review_required'
    del observation['capture_contract']
    write(observation)
    result = monitor.machine_semantics(tmp_path, now)
    assert result['status'] == 'observed_receipts_match'
    assert next(iter(result['scopes'].values()))['historical_reversal_capture'] == 1


@pytest.mark.parametrize('field,value', [('arm','bad'), ('family_sha256','a'*64),
    ('input_sha256',None), ('input_sha256','a'*64), ('prompt_sha256','b'*64),
    ('process_start_ticks','0'), ('snapshot_read_at',1791342001.)])
def test_reversal_native_receipt_mutation_is_not_silently_accepted(tmp_path, monkeypatch, field, value):
    observation, write, now = reversal_semantic_fixture(tmp_path, monkeypatch)
    observation['runtime_consumption']['continuous_reversal'][field] = value
    write(observation)
    result = monitor.machine_semantics(tmp_path, now)
    assert result['status'] == 'review_required'
    assert result['issues'] and 'machine_raw_input_missing' not in result['issues']


def test_reversal_request_preparation_is_not_provider_execution(tmp_path, monkeypatch):
    observation, _, now = reversal_semantic_fixture(tmp_path, monkeypatch)
    key = observation['machine_observation_sha256']
    path = tmp_path/'ai_decision_requests'/f'ai_decision_requests_{now.date()}.jsonl'
    path.parent.mkdir()
    path.write_text(json.dumps(dict(captured_at=now.isoformat(), request_id='request-1',
        continuous_reversal_request_binding=dict(machine_observation_sha256=key,binding_status='matched')))+'\n')
    result = monitor._reversal_provider_lineage(tmp_path, now, [observation], tail_bytes=8192)
    assert result['request_prepared_count'] == 1 and result['raw_response_observed_count'] == 0
    assert result['provider_called_metadata_used_as_fact'] is False
    observation['source']['assessment']['action'] = 'BLOCK'
    observation['machine_observation_sha256'] = hashlib.sha256(
        __import__('src.engine.scalping.ai_decision_trace', fromlist=['_json_bytes'])._json_bytes(
            {k: v for k, v in observation.items() if k != 'machine_observation_sha256'})).hexdigest()
    prepared = json.loads(path.read_text())
    prepared['continuous_reversal_request_binding']['machine_observation_sha256'] = observation['machine_observation_sha256']
    path.write_text(json.dumps(prepared) + '\n')
    result = monitor._reversal_provider_lineage(tmp_path, now, [observation], tail_bytes=8192)
    assert result['issues'] == {'reversal_provider_request_after_nonentry': 1}


def _current_provider_lineage_fixture(tmp_path, *, verdicts=('CAUTION', 'PASS', 'PASS', None)):
    """Use actual v1 producer fields; no absent legacy request binding is invented."""
    from src.engine.scalping.ai_decision_trace import _json_bytes
    now = datetime(2026, 10, 14, 11, 17, tzinfo=monitor.KST)
    observations, requests, traces = [], [], []
    for index, verdict in enumerate(verdicts):
        at = now - timedelta(seconds=100-index*10)
        native = dict(pid=123, process_start_ticks='456', family_sha256='f'*64,
            bundle_sha256='b'*64, input_sha256=f'{index+1:064x}', prompt_sha256='1'*64)
        observation = dict(schema='mechanistic_entry_observation_v1', captured_at=at.isoformat(),
            bundle_sha256='b'*64, runtime_consumption=dict(pid=123, process_start_ticks='456', continuous_reversal=native),
            label_context=dict(evaluation_attempt_id=f'attempt-{index}'),
            source=dict(assessment=dict(action='ENTER_NOW')))
        observation['machine_observation_sha256'] = hashlib.sha256(_json_bytes(observation)).hexdigest()
        observations.append(observation)
        # Final provider prompt bytes differ from the verified logical prompt.
        request = dict(schema='ai_decision_request_provenance_v1', captured_at=(at+timedelta(milliseconds=200)).isoformat(),
            request_id=f'request-{index}', endpoint='analyze_target', async_request_id=f'async-{index}',
            async_producer_pid=123, async_producer_start_ticks='456', prompt_sha256='2'*64,
            request_envelope_sha256=f'{index+10:064x}', payload_sha256=native['input_sha256'],
            sanitized_user_input_sha256=native['input_sha256'], sanitized_replay_context_sha256=native['input_sha256'])
        requests.append(request)
        trace = dict(schema='ai_decision_trace_v1', decision_ts=(at+timedelta(seconds=2)).isoformat(),
            decision_trace_id=request['request_id'], request_id=request['request_id'],
            evaluation_attempt_id=f'attempt-{index}', machine_observation_sha256=observation['machine_observation_sha256'],
            continuous_reversal_consumption=native, async_request_id=request['async_request_id'],
            async_producer_pid=123, async_producer_start_ticks='456', prompt_sha256=request['prompt_sha256'],
            request_envelope_sha256=request['request_envelope_sha256'],
            payload_sha256='9'*64, payload_semantic_sha256=request['sanitized_user_input_sha256'],
            provider_called=True, provider_response_id=f'response-{index}' if verdict else None,
            response_sha256='a'*64, entry_ai_raw_risk_verdict=verdict,
            entry_auxiliary_response_contract_valid=index < 2 if verdict else None,
            entry_post_response_execution_valid=index == 0,
            entry_ai_screen_status='caution' if index == 0 else 'response_invalid' if verdict else 'not_evaluated_transport',
            timeout=verdict is None, transport_timing={'openai_http_attempt_count': 1,
                'openai_http_timeout_budget_exhausted': verdict is None},
            entry_ai_contract_errors=['reversal_signal_path_changed'] if index==1 else [],
            entry_ai_raw_fields_present={k: True for k in ('risk_verdict', 'risk_codes', 'supporting_fact_ids', 'contradicting_fact_ids')},
            entry_ai_raw_fields_truncated=False, entry_ai_raw_fields_source='decoded_provider_response',
            entry_ai_raw_risk_codes=['NO_BLOCKING_RISK'] if verdict=='PASS' else ['EARLY_SIGNAL_FRAGILE'],
            entry_ai_raw_supporting_fact_ids=['observed_machine_signal'], entry_ai_raw_contradicting_fact_ids=[],
            entry_ai_raw_response_sha256='d'*64)
        traces.append(trace)
    def write(request_values=requests, trace_values=traces):
        for kind, values in (('requests', request_values), ('trace', trace_values)):
            path=tmp_path/f'ai_decision_{kind}'/f'ai_decision_{kind}_{now.date()}.jsonl'
            path.parent.mkdir(exist_ok=True)
            path.write_text(''.join(json.dumps(row)+'\n' for row in values))
    write()
    return now, observations, requests, traces, write


def test_current_provider_schema_counts_raw_valid_execution_and_http_timeout_separately(tmp_path):
    now, observations, requests, traces, _ = _current_provider_lineage_fixture(tmp_path)
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=16384)
    assert result['status'] == 'observed'
    assert result['request_prepared_count'] == result['provider_transmission_attempt_count'] == 4
    assert result['raw_response_observed_count'] == 3
    assert result['raw_verdict_counts'] == {'CAUTION': 1, 'PASS': 2}
    assert result['raw_pass_count'] == 2 and result['valid_pass_count'] == 1
    assert result['execution_valid_pass_count'] == 0 and result['provider_timeout_count'] == 1
    assert result['first_stop_counts'] == {'auxiliary_caution': 1,
        'native_signal_invalidated_after_valid_auxiliary_pass': 1,
        'auxiliary_response_contract_invalid': 1, 'original_budget_transport_timeout': 1}
    assert result['exact_attempt_join_gap_count'] == 0 and result['issues'] == {}
    assert all(row['main_commit_assessed'] is False for row in result['attempt_ledger'])


@pytest.mark.parametrize('field,value', [('async_producer_pid',999),('async_producer_start_ticks','789'),
    ('async_request_id','different'),('request_envelope_sha256','e'*64),('prompt_sha256','e'*64),
    ('sanitized_user_input_sha256','e'*64),('sanitized_replay_context_sha256','e'*64)])
def test_provider_lineage_never_joins_symbol_or_time_when_exact_request_binding_differs(tmp_path, field, value):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    requests[0][field] = value
    write()
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192)
    assert result['request_prepared_count'] == 0
    assert result['raw_response_observed_count'] == 1
    assert result['issues']['reversal_provider_request_hash_or_identity_mismatch'] == 1
    assert result['source_gaps']['response_request_unresolved'] == 1


@pytest.mark.parametrize('tamper', [None, 'pid', 'observation', 'request', 'input', 'binding_missing', 'one_async'])
def test_synchronous_provider_lineage_requires_exact_native_binding(tmp_path, tamper):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    request, trace = requests[0], traces[0]
    for row in (request, trace):
        for field in ('async_request_id', 'async_producer_pid', 'async_producer_start_ticks'):
            row[field] = None
    binding = dict(binding_status='matched', request_id=request['request_id'],
        machine_observation_sha256=observations[0]['machine_observation_sha256'],
        continuous_reversal_consumption=dict(trace['continuous_reversal_consumption']))
    request['continuous_reversal_request_binding'] = binding
    if tamper == 'pid': binding['continuous_reversal_consumption']['pid'] = 999
    if tamper == 'observation': binding['machine_observation_sha256'] = 'e'*64
    if tamper == 'request': binding['request_id'] = 'wrong'
    if tamper == 'input': binding['continuous_reversal_consumption']['input_sha256'] = 'e'*64
    if tamper == 'binding_missing': request.pop('continuous_reversal_request_binding')
    if tamper == 'one_async': request['async_producer_pid'] = 123
    write()
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=16384)
    assert result['request_prepared_count'] == (1 if tamper is None else 0)
    if tamper is None:
        assert result['issues'] == {}
        assert result['provider_transmission_attempt_count'] == 1
    else:
        assert result['issues']['reversal_provider_request_hash_or_identity_mismatch'] == 1


def test_provider_lineage_request_only_is_unresolved_and_partial_without_fabricated_timeout(tmp_path):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=(None,))
    write(trace_values=[])
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192)
    assert result['status'] == 'partial_source_gap'
    assert result['source_gaps'] == {'request_unresolved': 1, 'observation_trace_unresolved': 1}
    assert result['provider_transmission_attempt_count'] == result['provider_timeout_count'] == 0
    assert monitor._incomplete_semantics({'status':'observed_receipts_match','reversal_provider_lineage':result})


def test_provider_lineage_deduplicates_identical_rows_but_rejects_conflicting_trace_identity(tmp_path):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    write(request_values=requests*2, trace_values=traces*2)
    assert monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192)['raw_response_observed_count'] == 1
    write(trace_values=[traces[0], dict(traces[0], response_sha256='e'*64)])
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192)
    assert result['raw_response_observed_count'] == 0
    assert result['issues'] == {'trace_identity_conflict': 1}


def test_provider_lineage_preserves_partial_tail_and_excludes_foreign_date_or_pid(tmp_path):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    foreign = dict(traces[0], decision_trace_id='foreign', decision_ts=(now-timedelta(days=1)).isoformat())
    write(trace_values=[foreign, traces[0]])
    path=tmp_path/'ai_decision_trace'/f'ai_decision_trace_{now.date()}.jsonl'
    with path.open('ab') as stream:
        stream.write(b'{"decision_ts":')
    result = monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192, pid_identity=(123,'456'))
    assert result['raw_response_observed_count'] == 1
    assert result['status'] == 'partial_source_gap'
    assert result['source_windows']['traces']['incomplete_last_line'] is True
    assert monitor._reversal_provider_lineage(tmp_path, now, observations, tail_bytes=8192,
        pid_identity=(999,'456'))['raw_response_observed_count'] == 0


def test_provider_lineage_future_trace_leaves_carry_out_unresolved(tmp_path):
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    traces[0]['decision_ts']=(now+timedelta(milliseconds=1)).isoformat()
    write()
    result=monitor._reversal_provider_lineage(tmp_path,now,observations,tail_bytes=8192)
    assert result['raw_response_observed_count']==0
    assert result['source_gaps']=={'request_unresolved':1,'observation_trace_unresolved':1}
    assert result['status']=='partial_source_gap'


def test_raw_response_received_with_malformed_verdict_remains_a_received_response(tmp_path):
    now,observations,requests,traces,write=_current_provider_lineage_fixture(tmp_path,verdicts=('PASS',))
    traces[0].update(entry_ai_raw_risk_verdict=['malformed'],entry_auxiliary_response_contract_valid=False)
    write()
    result=monitor._reversal_provider_lineage(tmp_path,now,observations,tail_bytes=8192)
    assert result['raw_response_observed_count']==1
    assert result['raw_verdict_counts']=={'UNRECOGNIZED':1}
    assert result['valid_pass_count']==0
    assert result['source_gaps']=={'raw_response_verdict_unrecognized':1}


def test_bounded_reader_missing_clock_and_rotation_cannot_publish_complete_zero(tmp_path,monkeypatch):
    from pathlib import Path
    path=tmp_path/'source.jsonl'
    path.write_text(json.dumps({'schema':'unexpected'})+'\n')
    rows,source=monitor._recent_source_rows(path,monitor.stamp(START),time_field='decision_ts')
    assert rows==[] and source['status']=='partial' and source['missing_timestamp_rows']==1
    path.write_text(json.dumps({'decision_ts':monitor.stamp(START).isoformat()})+'\n')
    replacement=tmp_path/'rotated.jsonl'
    replacement.write_bytes(path.read_bytes())
    original_stat=Path.stat
    def rotate_after_read(candidate,*args,**kwargs):
        if candidate==path and replacement.exists():
            replacement.replace(path)
        return original_stat(candidate,*args,**kwargs)
    monkeypatch.setattr(Path,'stat',rotate_after_read)
    rows,source=monitor._recent_source_rows(path,monitor.stamp(START),time_field='decision_ts')
    assert rows==[] and source['status']=='unobservable'
    assert source['reason']=='source_generation_changed'


def test_fixed_watch_and_scanner_counts_have_explicit_cohort_without_changing_scarcity_denominator():
    generation=hashlib.sha256(b'2026-09-21|005930|nxt_premarket|nxt_only').hexdigest()
    fixed=event(action='BLOCK',screen='not_requested_machine_nonentry',scanner_promotion_id='None',
        watch_origin='MAIN_FIXED_WATCH',watch_admission_id='FIXED-2026-09-21-005930-nxt_premarket-nxt_only-abcdef123456',
        watch_generation_id=generation)
    source=monitor.snapshot([fixed, fixed],START)
    counts=source['main_machine_observation']
    assert counts['scanner_evaluation_count']==0 and counts['fixed_watch_evaluation_count']==1
    assert counts['all_main_identified_evaluation_count']==1
    observed=monitor.evaluate({'target_date':START.date().isoformat(),'dry_run':False,'submission_monitor':source},{},START)
    assert observed['evaluation_cohort']=='scanner_promotions'
    assert observed['blocker']=='no_identified_scanner_machine_evaluation'
    assert observed['main_machine_observation']==counts


def test_compressed_source_never_becomes_zero_complete_window(tmp_path):
    path = tmp_path/'archived.jsonl'
    path.with_suffix('.jsonl.gz').write_bytes(b'archive')
    rows, source = monitor._recent_source_rows(path, START, time_field='captured_at')
    assert rows == [] and source['status'] == 'unobservable'
    assert source['reason'] == 'compressed_archive_not_current_bounded_source'
    assert source['window_covered'] is False


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


def test_probe_preflight_gap_example_retains_exact_attempt(tmp_path):
    now = START + timedelta(minutes=10)
    row = _probe_source_row(now, "required_feature_insufficient",
                           "source_quality_blocked_before_assessment",
                           kind="runtime_preflight_artifact_not_ready")
    row["fields"]["evaluation_attempt_id"] = "machine-source-invalid-exact"
    _source_gap_files(tmp_path, now, probes=[row])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["diagnostics"] == {"machine_probe:runtime_preflight_artifact_not_ready": 1}
    assert result["examples"][0]["evaluation_attempt_id"] == "machine-source-invalid-exact"
    assert result["runtime_effect"] is False


@pytest.mark.parametrize("missing", [None, "", "-", "None", "null", 0, [], {}])
def test_probe_missing_attempt_never_becomes_identity_or_collapses_events(tmp_path, missing):
    now = START + timedelta(minutes=10)
    rows = []
    for observed in (now - timedelta(seconds=1), now):
        row = _probe_source_row(observed, "required_feature_insufficient",
                               "source_quality_blocked_before_assessment",
                               kind="runtime_preflight_artifact_not_ready")
        row["fields"]["evaluation_attempt_id"] = missing
        rows.append(row)
    _source_gap_files(tmp_path, now, probes=rows)
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["diagnostics"] == {"machine_probe:runtime_preflight_artifact_not_ready": 2}
    assert all(row["evaluation_attempt_id"] == "" for row in result["examples"])


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
    _observer_selection_fixture(tmp_path, monkeypatch)
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
    assert saved["execution_status"] == "completed"
    assert saved["execution_mode"] == "source_only"
    assert saved["blocker"] == "missing_stale_or_noncurrent_sentinel_evidence"
    assert saved["source_as_of"] is None
    assert saved["observation_health"]["status"] == "not_eligible"
    assert saved["observation_health"]["current_observation_verified"] is False
    assert saved["observation_health"]["full_coverage_proven"] is False
    assert "monitor_state_not_quiet_full_observation" in saved["observation_health"]["unmet_conditions"]


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


def test_selected_delay_missing_is_distinct_from_unselected_observation(tmp_path):
    day='2026-09-29'
    raw=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    base=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stock_name='test',
        emitted_at=day+'T10:00:00',emitted_date=day,stock_code='005930',record_id=1)
    commit={**base,'stage':'pre_submit_delay_committed','fields':dict(delay_intent_id='one',
        selected_delay_sec=30,market_session_bucket='krx_regular')}
    raw.write_text(json.dumps(commit)+'\n')
    observed=monitor.pre_submit_delay_source_semantics(tmp_path,datetime(2026,9,29,10,4))
    assert observed['issues']['selected_due_completion_missing']==1
    commit['fields']['selected_delay_sec']=0
    raw.write_text(json.dumps(commit)+'\n')
    observed=monitor.pre_submit_delay_source_semantics(tmp_path,datetime(2026,9,29,10,4))
    assert not observed['issues'].get('selected_due_completion_missing')
    commit['fields']['selected_delay_sec']=30
    terminal={**base,'stage':'pre_submit_delay_intent_terminal','fields':dict(delay_intent_id='one',terminal_reason='deadline_expired')}
    raw.write_text(json.dumps(commit)+'\n'+json.dumps(terminal)+'\n')
    observed=monitor.pre_submit_delay_source_semantics(tmp_path,datetime(2026,9,29,10,4))
    assert not observed['issues'].get('selected_due_completion_missing')


def _native_no_match_probe(now, *, receipt_format='literal'):
    row = _probe_source_row(now, 'required_feature_insufficient',
                            'native_observation_residence_exhausted')
    receipt = dict(schema='native_observation_selection_v1',
        evaluation_role='probe_observation', observed_epoch=monitor.stamp(now).timestamp()-.1,
        runtime_effect=False, reason='no_matching_pattern', item='005930_AL', venue='SOR',
        process_pid=123, process_start_ticks='456', family_sha256='a'*64,
        scope_execution_hash='b'*64, selected_scope='samsung|REGULAR|ALL',
        selected_branch_truth={'G1': 'FALSE', 'G2': 'FALSE'}, native_epoch=2,
        native_sequence=200, observed_seconds=149.5, raw_ready_count=0, selected_ready_count=0)
    row['fields'].update(zero_base_producer_pid='123', physical_probe_lease_id='lease-1',
        zero_base_ws_wait_reason='ready', zero_base_ws_exact_0b_count='8',
        zero_base_ws_signed_0b_count='8', zero_base_ws_exact_0d_count='15',
        native_observation_receipt=(repr(receipt) if receipt_format == 'literal'
            else json.dumps(receipt) if receipt_format == 'json' else receipt))
    return row


def _health_birth_fixture(now, actor=('9', '900')):
    epoch = int(now.timestamp())-180-int(actor[1])//100
    lower = epoch+int(actor[1])/100-1.0
    proof = dict(schema='submission_monitor_actor_birth_v1', status='verified', actor=list(actor),
        observed_at=now.isoformat(), boot_epoch=epoch, clock_ticks_per_second=100,
        start_ticks=int(actor[1]), birth_lower_bound_epoch=lower,
        birth_lower_bound_at=datetime.fromtimestamp(lower, monitor.KST).isoformat(),
        process_cwd='/reviewed/release/src', runtime_effect=False, allowed_runtime_apply=False)
    generation = dict(actor_birth_proof=proof, started_at=now.isoformat(), release_root='/reviewed/release',
        selector_reported_pid_receipt=dict(pid=int(actor[0]), start_ticks=actor[1],
                                         process_cwd=proof['process_cwd']))
    return proof, generation


def _bounded_outcome_health_fixture(*, partial=True, outcome='response_invalid'):
    from copy import deepcopy
    result=_provider_health_fixture('PASS'); now=monitor.stamp(result['as_of']); actor=['679747','2339199']
    proof,generation=_health_birth_fixture(now,actor)
    generation.update(status='current',generation_current=True,selector_reported_actual_pid_consumed=True)
    result['observer_generation']=generation
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name]; view=deepcopy(original)
        token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(view,actor,now)
        finally:monitor._HEALTH_BIRTH.reset(token)
    gap=result['source_gap_semantics']['current_health_cohort']['view']
    machine=result['machine_semantics']['current_health_cohort']['view']
    machine['tail_truncated']=True
    if partial:
        gap['sources']['probe'].update(status='partial',tail_truncated=True,window_covered=False,
            first_read_at=(now-timedelta(seconds=60)).isoformat())
        gap['async_transition_projection_coverage']='partial'
    lineage=machine['reversal_provider_lineage'];row=lineage['attempt_ledger'][0]
    if outcome=='response_invalid':
        row.update(auxiliary_response_contract_valid=False,post_response_execution_valid=False,
            effective_screen_status='response_invalid',execution_errors=['union_pass_support_invalid','reversal_signal_path_changed'])
        lineage.update(auxiliary_response_contract_valid_count=1,valid_pass_count=1,execution_valid_pass_count=1)
    elif outcome=='timeout':
        row.update(raw_response_observed=False,raw_verdict=None,auxiliary_response_contract_valid=None,
            post_response_execution_valid=None,effective_screen_status='not_evaluated_transport',timeout=True)
        lineage.update(raw_response_observed_count=1,raw_pass_count=1,raw_verdict_counts={'PASS':1},
            auxiliary_response_contract_valid_count=1,valid_pass_count=1,execution_valid_pass_count=1,
            provider_timeout_count=1)
    elif outcome=='unknown_pass':
        result['async_disposition_coverage']['attempt_projection']=[]
    return result,gap,machine,lineage


def _with_role_partition(*, role='probe_observation', kind='matched'):
    result,gap,machine,lineage=_bounded_outcome_health_fixture(partial=False)
    now=monitor.stamp(result['as_of']);actor=machine_actor=result['machine_semantics']['current_health_cohort']['actor']
    records=[]
    def receipt(digest,at,role,kind):
        flags=dict(runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False,broker_order_forbidden=True)
        observation=dict(machine_observation_sha256=digest,captured_at=at,bundle_sha256=machine['current_bundle_sha256'],
            evaluation_role=role,**flags,provider_called=False,source=dict(exact_payload={'evaluation_role':role},assessment=flags),
            runtime_consumption=dict(pid=int(actor[0]),process_start_ticks=actor[1],continuous_reversal=dict(
                evaluation_role=role,provider_state='probe_observation_provider_forbidden',provider_request_observed=False)))
        proof=monitor._machine_role_receipt(observation,kind)
        return (monitor.stamp(at),(int(actor[0]),'/release/src',actor[1]),kind,[],None,True,proof)
    for row in lineage['attempt_ledger']:
        records.append(receipt(row['machine_observation_sha256'],row['trace_decision_ts'],'main_live','matched'))
    if role is not None:
        records.append(receipt('f'*64,now.isoformat(),role,kind))
        machine['observation_count']+=1
        if kind=='invalid':machine['source_invalid_count']+=1
        elif kind=='required':machine['required_feature_guard_count']+=1
        else:next(iter(machine['scopes'].values()))['matched_receipts']+=1
        machine['status']=('source_invalid_observed' if machine['source_invalid_count']+machine['required_feature_guard_count'] else 'observed_receipts_match')
    machine['observation_role_partition']=monitor._machine_role_partition(records,actor,now,machine['current_bundle_sha256'])
    return result,machine,lineage


@pytest.mark.parametrize('role,kind,expected',[(None,'matched','warning_pending'),
    ('probe_observation','matched','warning_pending'),('probe_observation','invalid','warning_pending'),
    ('probe_observation','required','warning_pending'),('counterfactual','matched','not_eligible')])
def test_role_partition_closes_all_rows_and_provider_guard_denominator(role,kind,expected):
    result,machine,lineage=_with_role_partition(role=role,kind=kind)
    health=monitor.observation_health_projection(result)
    assert health['status']==expected,health
    if expected=='warning_pending':
        assert machine['observation_role_partition']['provider_eligible_count']==lineage['machine_observation_count']==2
        assert health['current_observation_verified'] is False


@pytest.mark.parametrize('bad',['count','bool_count','hash','duplicate','actor','bundle','role_conflict','provider_allowed',
    'runtime_allowed','ledger_foreign_hash','ledger_missing_hash','missing_partition','unknown_role','malformed_role'])
def test_role_partition_rejects_tamper_unknown_roles_and_missing_population_proof(bad):
    result,machine,lineage=_with_role_partition()
    partition=machine['observation_role_partition'];row=partition['observations'][-1]
    if bad=='count':partition['excluded_nonprovider_count']=2
    elif bad=='bool_count':partition['excluded_nonprovider_count']=True
    elif bad=='hash':row['observation_sha256']='bad'
    elif bad=='duplicate':row['observation_sha256']=partition['observations'][0]['observation_sha256']
    elif bad=='actor':row['actor']=['99','99']
    elif bad=='bundle':row['bundle_sha256']='e'*64
    elif bad=='role_conflict':row['exact_role']='main_live'
    elif bad=='provider_allowed':row['native_provider_request_observed']=True
    elif bad=='runtime_allowed':row['capture_flags']['runtime_effect']=True
    elif bad=='ledger_foreign_hash':lineage['attempt_ledger'][0]['machine_observation_sha256']='e'*64
    elif bad=='ledger_missing_hash':lineage['attempt_ledger'][0]['machine_observation_sha256']=None
    elif bad=='missing_partition':machine.pop('observation_role_partition')
    elif bad=='unknown_role':row['evaluation_role']='unknown'
    elif bad=='malformed_role':row['evaluation_role']=[]
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('partial',[False,True])
@pytest.mark.parametrize('outcome',['response_invalid','timeout','unknown_pass'])
def test_completed_report_bounded_or_unverified_ai_outcomes_are_warning_not_validation(partial,outcome):
    result,gap,machine,lineage=_bounded_outcome_health_fixture(partial=partial,outcome=outcome)
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    assert health['status']=='warning_pending',health
    assert health['reason']=='bounded_source_quality_observation' and health['unmet_conditions']
    assert health['current_observation_verified'] is False and health['full_coverage_proven'] is False
    assert health['runtime_effect'] is False and health['allowed_runtime_apply'] is False
    assert json.dumps(result,sort_keys=True)==before


def test_bounded_quality_warning_preserves_pending_source_quality_notification():
    result,*_=_bounded_outcome_health_fixture()
    incident=dict(status='pending',last_seen=result['as_of'],issues={'machine_probe:coverage_degraded:krx_nxt_integrated':1})
    result['incidents']['machine_auxiliary_intraday_source_gap']=incident
    result['notification_pending']=['machine_auxiliary_intraday_source_gap']
    health=monitor.observation_health_projection(result)
    assert health['status']=='warning_pending' and 'active_current_or_unknown_incident' in health['unmet_conditions']
    assert result['incidents']['machine_auxiliary_intraday_source_gap'] is incident
    assert result['notification_pending']==['machine_auxiliary_intraday_source_gap']


@pytest.mark.parametrize('damage', [None,'aux_required','request','machine','trace_partial','pending_io',
    'request_io','trace_io','unexplained_trace','birth','pending_boolean','extra_metadata','pass'])
def test_preassessment_without_lazy_auxiliary_journals_is_bounded_warning_only(damage):
    from copy import deepcopy
    result=_observation_health_fixture();now=monitor.stamp(result['as_of']);actor=['9','900']
    proof,generation=_health_birth_fixture(now,actor)
    generation.update(status='current',generation_current=True,selector_reported_actual_pid_consumed=True)
    result['observer_generation']=generation
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name];token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(deepcopy(original),actor,now)
        finally:monitor._HEALTH_BIRTH.reset(token)
    gap=result['source_gap_semantics']['current_health_cohort']['view']
    machine=result['machine_semantics']['current_health_cohort']['view']
    absent=dict(status='unobservable',tail_truncated=False,window_covered=False,recent_count=0,reason='FileNotFoundError')
    gap.update(status='gap_observed',observed={'entry_traces':4},
        diagnostics={'machine_trace:source_quality_blocked_before_assessment':4},
        diagnostics_by_scope={'route:krx_nxt_integrated|machine_trace:source_quality_blocked_before_assessment':4})
    gap['sources']['trace']['recent_count']=4;gap['sources']['pending']=deepcopy(absent)
    machine.update(status='partial_unobservable',tail_truncated=True,provider_lineage_source_status='partial_source_gap')
    zero_keys=('machine_observation_count','trace_attempt_count','request_prepared_count',
        'provider_transmission_attempt_count','raw_response_observed_count','auxiliary_response_contract_valid_count',
        'raw_pass_count','valid_pass_count','execution_valid_pass_count','provider_timeout_count',
        'enter_without_request_observed','exact_attempt_join_gap_count')
    lineage=dict(status='partial_source_gap',issues={},decision_authority='report_only',exact_pid_filter=actor,
        current_pid_coverage='exact_live_pid',source_gaps={},attempt_ledger=[],
        source_windows={'requests':deepcopy(absent),'traces':deepcopy(gap['sources']['trace'])},
        **dict.fromkeys(zero_keys,0))
    machine['reversal_provider_lineage']=lineage
    if damage=='aux_required':gap['observed']['auxiliary_required']=1
    elif damage=='request':lineage['request_prepared_count']=1
    elif damage=='machine':machine['observation_count']=1
    elif damage=='trace_partial':gap['sources']['trace'].update(status='partial',window_covered=False)
    elif damage=='pending_io':gap['sources']['pending']['reason']='PermissionError'
    elif damage=='request_io':lineage['source_windows']['requests']['reason']='PermissionError'
    elif damage=='trace_io':gap['sources']['trace']['reason']='FileNotFoundError'
    elif damage=='unexplained_trace':gap['observed']['entry_traces']=5;gap['sources']['trace']['recent_count']=5
    elif damage=='birth':proof['boot_epoch']+=1
    elif damage=='pending_boolean':gap['sources']['pending']['recent_count']=False
    elif damage=='extra_metadata':gap['sources']['pending']['malformed_rows']=1
    elif damage=='pass':lineage['raw_pass_count']=1
    before=json.dumps(result,sort_keys=True);health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if damage is None else 'not_eligible'),health
    assert health['full_coverage_proven'] is False and health['current_observation_verified'] is False
    assert health['runtime_effect'] is False and health['allowed_runtime_apply'] is False
    if damage is None:
        assert health['reason']=='bounded_source_quality_observation'
        assert 'source_window_not_complete:pending' in health['unmet_conditions']
    assert json.dumps(result,sort_keys=True)==before



@pytest.mark.parametrize('damage',[None,'trace_partial','probe_partial','unknown_pending','count',
    'auxiliary','birth','contract'])
def test_complete_current_quiet_cohort_with_only_lazy_pending_missing_is_warning(damage):
    from copy import deepcopy
    result=_observation_health_fixture();now=monitor.stamp(result['as_of']);actor=['9','900']
    proof,generation=_health_birth_fixture(now,actor)
    generation.update(status='current',generation_current=True,selector_reported_actual_pid_consumed=True)
    result['observer_generation']=generation
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name];token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(deepcopy(original),actor,now)
        finally:monitor._HEALTH_BIRTH.reset(token)
    gap=result['source_gap_semantics']['current_health_cohort']['view']
    result['machine_semantics']['current_health_cohort']['view']['tail_truncated']=True
    gap['sources']['pending']=dict(status='unobservable',tail_truncated=False,
        window_covered=False,recent_count=0,reason='FileNotFoundError')
    if damage=='trace_partial':gap['sources']['trace'].update(status='partial',window_covered=False)
    elif damage=='probe_partial':gap['sources']['probe'].update(status='partial',window_covered=False)
    elif damage=='unknown_pending':gap['sources']['pending']['reason']='PermissionError'
    elif damage=='count':gap['observed']['entry_traces']=True
    elif damage=='auxiliary':gap['observed']['auxiliary_called']=1
    elif damage=='birth':proof['boot_epoch']+=1
    elif damage=='contract':result['entry_execution_tuning_semantics']['pre_submit_delay']['bootstrap_handoff_match']=False
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if damage is None else 'not_eligible'),health
    if damage is None:
        assert health['unmet_conditions']==['source_window_not_complete:pending']
    assert health['full_coverage_proven'] is False and health['current_observation_verified'] is False
    assert health['allowed_runtime_apply'] is False and health['runtime_effect'] is False
    assert json.dumps(result,sort_keys=True)==before

@pytest.mark.parametrize('hour,missing',[(hour,missing) for hour in ('07:55','08:44','09:00','16:10') for missing in ('all','aux')])
@pytest.mark.parametrize('damage',[None,'entry_open','classification','io','empty','malformed',
    'birth','selection','assessment','provider','bootstrap','stale','incident','async','source_partial'])
def test_native_pre_entry_lazy_sources_are_pending_without_proving_coverage(monkeypatch, hour, missing, damage):
    from copy import deepcopy
    result=_observation_health_fixture()
    old=monitor.stamp(result['as_of']);now=old.replace(hour=int(hour[:2]),minute=int(hour[3:]))
    delta=now-old
    def shift(value):
        if isinstance(value,dict):return {k:shift(v) for k,v in value.items()}
        if isinstance(value,list):return [shift(v) for v in value]
        if isinstance(value,str) and len(value)>10 and value[10]=='T' and monitor.stamp(value):
            return (monitor.stamp(value)+delta).isoformat()
        return value
    result=shift(result)
    inp=result['input_provenance'];at=monitor.stamp(inp['snapshot_as_of'])
    inp.update(sentinel_classification='NOT_YET_DUE',latest_event_status='no_recent_loaded_events',
        loaded_recent_event_count=0,latest_event_at=(at-timedelta(days=1)).isoformat(),
        latest_event_age_seconds=(now-at).total_seconds()+86400)
    actor=['9','900'];proof,generation=_health_birth_fixture(now,actor)
    generation.update(status='current',generation_current=True,selector_reported_actual_pid_consumed=True)
    result['observer_generation']=generation
    from src.trading.market import session_contract
    context=session_contract.resolve_market_session(now)
    result['source_gap_semantics']['fixed_watch_waits'].update(count=0,session_boundary_wait_count=0,
        reason_counts={},native_session_regime=context.session_regime,
        native_entry_allowed_by_clock=context.entry_allowed_by_clock)
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name];token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(deepcopy(original),actor,now)
        finally:monitor._HEALTH_BIRTH.reset(token)
    gap=result['source_gap_semantics']['current_health_cohort']['view']
    machine=result['machine_semantics']['current_health_cohort']['view']
    absent=dict(status='unobservable',tail_truncated=False,window_covered=False,recent_count=0,reason='FileNotFoundError')
    for name in (('probe','trace','pending') if missing=='all' else ('trace','pending')):
        gap['sources'][name]=deepcopy(absent)
    gap['async_pass_projection_coverage']='partial'
    if missing=='all':
        machine['source_status']='unobservable:FileNotFoundError'
        for key in ('read_count','bytes_read','source_bytes','window_coverage','read_limit_bytes'):
            machine.pop(key,None)
    else:machine['tail_truncated']=True
    if damage=='entry_open':
        from dataclasses import replace
        monkeypatch.setattr(session_contract,'resolve_market_session',lambda _: replace(context,entry_allowed_by_clock=True))
    if damage=='classification':inp.pop('sentinel_classification')
    elif damage=='io':gap['sources']['trace']['reason']='PermissionError'
    elif damage=='empty':gap['sources']['trace']['reason']='empty_source'
    elif damage=='malformed':gap['sources']['trace']['malformed_rows']=1
    elif damage=='birth':proof['boot_epoch']+=1
    elif damage=='selection':machine['selection']['representative']['score_contract_valid']=False
    elif damage=='assessment':gap['observed']['entry_traces']=1
    elif damage=='provider':machine['observation_count']=1
    elif damage=='bootstrap':result['entry_execution_tuning_semantics']['bootstrap']['status']='missing'
    elif damage=='stale':inp['snapshot_age_seconds']+=1
    elif damage=='incident':result['incidents']['new']=dict(status='active',last_seen=now.isoformat(),issues={'unknown':1})
    elif damage=='async':gap['async_pass_unmapped_count']=1
    elif damage=='source_partial':gap['sources']['trace']['status']='partial'
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    expected=damage is None and int(hour[:2]) < 9
    assert health['status']==('warning_pending' if expected else 'not_eligible'),health
    if expected:assert health['reason']=='native_pre_entry_observation_not_due'
    assert not any(health[k] for k in ('current_observation_verified','full_coverage_proven',
        'runtime_effect','allowed_runtime_apply'))
    assert json.dumps(result,sort_keys=True)==before


@pytest.mark.parametrize('damage',[None,'unaccounted_probe','missing_probe','partial_probe','unknown_wait',
    'missing_trace_io','assessment','async','birth','selection','payload_missing'])
def test_complete_native_wait_census_explains_lazy_trace_without_source_validation(damage):
    from copy import deepcopy
    result=_observation_health_fixture();now=monitor.stamp(result['as_of']);actor=['9','900']
    proof,generation=_health_birth_fixture(now,actor)
    generation.update(status='current',generation_current=True,selector_reported_actual_pid_consumed=True)
    result['observer_generation']=generation
    inp=result['input_provenance'];at=monitor.stamp(inp['snapshot_as_of'])
    inp.update(latest_event_status='no_recent_loaded_events',loaded_recent_event_count=0,
        latest_event_at=(at-timedelta(days=1)).isoformat(),latest_event_age_seconds=(now-at).total_seconds()+86400)
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name];token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(deepcopy(original),actor,now)
        finally:monitor._HEALTH_BIRTH.reset(token)
    gap=result['source_gap_semantics']['current_health_cohort']['view']
    machine=result['machine_semantics']['current_health_cohort']['view'];machine['tail_truncated']=True
    absent=dict(status='unobservable',tail_truncated=False,window_covered=False,recent_count=0,reason='FileNotFoundError')
    gap['sources']['trace']=deepcopy(absent);gap['sources']['pending']=deepcopy(absent)
    gap['async_pass_projection_coverage']='partial'
    if damage=='unaccounted_probe':gap['sources']['probe']['recent_count']+=1
    elif damage=='missing_probe':gap['sources']['probe']=deepcopy(absent)
    elif damage=='partial_probe':gap['sources']['probe'].update(status='partial',window_covered=False)
    elif damage=='unknown_wait':gap['fixed_watch_waits']['unclassified_or_actionable_wait_count']=1
    elif damage=='missing_trace_io':gap['sources']['trace']['reason']='PermissionError'
    elif damage=='assessment':gap['observed']['entry_traces']=1
    elif damage=='async':gap['async_pass_unmapped_count']=1
    elif damage=='birth':proof['boot_epoch']+=1
    elif damage=='selection':machine['selection']['representative']['score_contract_valid']=False
    elif damage=='payload_missing':machine['source_status']='unobservable:FileNotFoundError'
    health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if damage is None else 'not_eligible'),health
    if damage is None:assert health['reason']=='bounded_source_quality_observation'
    assert not health['current_observation_verified'] and not health['full_coverage_proven']
    assert not health['runtime_effect'] and not health['allowed_runtime_apply']


def _derived_coverage_health_fixture(route='krx_nxt_integrated'):
    result,gap,machine,lineage=_bounded_outcome_health_fixture(partial=False)
    gap.update(status='gap_observed',issues={'machine_probe:coverage_degraded:'+route:1},
        issues_by_scope={'route:'+route+'|machine_probe:coverage_degraded':1},
        probe_route_counts={route:20},probe_route_source_covered_counts={route:3},
        coverage_alert_floor='10_same_route_unique_probes_below_20pct_source_covered',
        coverage_success_contract='valid_machine_capture_or_exact_native_all_false_receipt')
    gap['observed']['probe_results']=20
    result['incidents']['machine_auxiliary_intraday_source_gap']=dict(status='active',last_seen=result['as_of'],
        issues=dict(gap['issues']))
    result['notification_pending']=['machine_auxiliary_intraday_source_gap']
    return result,gap


@pytest.mark.parametrize('route',['krx_only','nxt_only','krx_nxt_integrated'])
def test_exact_recomputed_route_coverage_quality_preserves_issue_and_domain_alert(route):
    result,gap=_derived_coverage_health_fixture(route)
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    assert health['status']=='warning_pending' and health['reason']=='bounded_source_quality_observation'
    assert 'current_failure_or_diagnostic_present' in health['unmet_conditions']
    assert health['current_observation_verified'] is False and health['full_coverage_proven'] is False
    assert gap['issues']=={'machine_probe:coverage_degraded:'+route:1}
    assert result['notification_pending']==['machine_auxiliary_intraday_source_gap']
    assert result['incidents']['machine_auxiliary_intraday_source_gap']['status']=='active'
    assert json.dumps(result,sort_keys=True)==before


@pytest.mark.parametrize('diagnostic', ['reversal_first_signal_invalidated', 'unknown_cancellation'])
def test_first_turn_cancellation_does_not_hide_remaining_route_coverage(diagnostic):
    result, gap = _derived_coverage_health_fixture()
    gap['observed'].update(probe_results=33, probe_native_invalidated=1)
    gap.update(probe_route_counts={'krx_nxt_integrated': 32},
               probe_route_source_covered_counts={'krx_nxt_integrated': 6},
               diagnostics={'machine_probe:'+diagnostic: 1},
               diagnostics_by_scope={'route:krx_nxt_integrated|machine_probe:'+diagnostic: 1})
    before = json.dumps(result, sort_keys=True)
    health = monitor.observation_health_projection(result)
    assert health['status'] == ('warning_pending' if diagnostic == 'reversal_first_signal_invalidated'
                               else 'not_eligible')
    assert gap['issues'] == {'machine_probe:coverage_degraded:krx_nxt_integrated': 1}
    assert result['notification_pending'] == ['machine_auxiliary_intraday_source_gap']
    assert not health['full_coverage_proven'] and not health['current_observation_verified']
    assert json.dumps(result, sort_keys=True) == before


@pytest.mark.parametrize('bad',['issue_bool','issue_count','scope_bool','scope_count','wrong_scope','unknown_route',
    'below_floor','healthy_coverage','denominator_bool','numerator_negative','numerator_string','partial_reader',
    'extra_contract_issue','machine_issue','execution_issue','cross_route_overcount','unknown_extra','orphan',
    'floor_bool','wrong_floor','wrong_success_contract'])
def test_route_coverage_quality_requires_exact_math_typed_counts_complete_reader_and_scope(bad):
    result,gap=_derived_coverage_health_fixture();route='krx_nxt_integrated'
    if bad=='issue_bool':gap['issues']['machine_probe:coverage_degraded:'+route]=True
    elif bad=='issue_count':gap['issues']['machine_probe:coverage_degraded:'+route]=2
    elif bad=='scope_bool':gap['issues_by_scope']['route:'+route+'|machine_probe:coverage_degraded']=True
    elif bad=='scope_count':gap['issues_by_scope']['route:'+route+'|machine_probe:coverage_degraded']=2
    elif bad=='wrong_scope':gap['issues_by_scope']={'route:nxt_only|machine_probe:coverage_degraded':1}
    elif bad=='unknown_route':gap['issues']={'machine_probe:coverage_degraded:unknown':1}
    elif bad=='below_floor':gap['probe_route_counts'][route]=9
    elif bad=='healthy_coverage':gap['probe_route_source_covered_counts'][route]=4
    elif bad=='denominator_bool':gap['probe_route_counts'][route]=True
    elif bad=='numerator_negative':gap['probe_route_source_covered_counts'][route]=-1
    elif bad=='numerator_string':gap['probe_route_source_covered_counts'][route]='3'
    elif bad=='cross_route_overcount':
        gap['probe_route_counts']['nxt_only']=1
        gap['probe_route_assessed_counts']['nxt_only']=2
        gap['observed']['probe_results']=21
    elif bad=='unknown_extra':
        gap['probe_route_counts']['unknown']=1
        gap['observed']['probe_results']=21
    elif bad=='orphan':gap['probe_route_source_covered_counts']['nxt_only']=1
    elif bad=='floor_bool':gap['coverage_alert_floor']=True
    elif bad=='wrong_floor':gap['coverage_alert_floor']='1_same_route_unique_probes_below_20pct_source_covered'
    elif bad=='wrong_success_contract':gap['coverage_success_contract']='unverified_source_is_success'
    elif bad=='partial_reader':gap['sources']['probe'].update(status='partial',window_covered=False,
        tail_truncated=True,first_read_at=(monitor.stamp(result['as_of'])-timedelta(seconds=30)).isoformat())
    elif bad=='extra_contract_issue':gap['issues']['machine_trace:path_auxiliary_feature_input_conflict']=1
    elif bad=='machine_issue':result['machine_semantics']['current_health_cohort']['view']['issues']={'contract_invalid':1}
    elif bad=='execution_issue':result['entry_execution_tuning_semantics']['issues']={'contract_invalid':1}
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('bad',['malformed','io','stage_issue','stage_scope_issue','hash','hash_none','actor','bundle','count','clock',
    'bootstrap','split','unknown_diagnostic','birth','reader_identity','unknown_incident'])
def test_bounded_quality_warning_never_hides_intrinsic_contract_or_reader_failure(bad):
    result,gap,machine,lineage=_bounded_outcome_health_fixture()
    row=lineage['attempt_ledger'][0]
    if bad=='malformed':gap['sources']['probe']['malformed_rows']=1
    elif bad=='io':gap['sources']['probe']['reason']='PermissionError'
    elif bad=='stage_issue':gap['issues']={'machine_trace:path_auxiliary_feature_input_conflict':1}
    elif bad=='stage_scope_issue':machine['issues_by_scope']={'scope':1}
    elif bad=='hash':row['machine_observation_sha256']='invalid'
    elif bad=='hash_none':row['machine_observation_sha256']=None
    elif bad=='actor':row['producer_pid']='999'
    elif bad=='bundle':row['machine_bundle_sha256']='e'*64
    elif bad=='count':lineage['raw_response_observed_count']=-1
    elif bad=='clock':row['trace_decision_ts']='2027-01-01T00:00:00+09:00'
    elif bad=='bootstrap':result['entry_execution_tuning_semantics']['bootstrap']['status']='unverified'
    elif bad=='split':result['entry_execution_tuning_semantics']['entry_split']['verification']='unverified'
    elif bad=='unknown_diagnostic':
        gap['diagnostics']={'machine_probe:unknown_contract_failure':1}
        gap['diagnostics_by_scope']={'scope|machine_probe:unknown_contract_failure':1}
    elif bad=='birth':result['observer_generation']['actor_birth_proof']['birth_lower_bound_epoch']=0
    elif bad=='reader_identity':gap['sources']['probe']['source_identity']['inode']=0
    elif bad=='unknown_incident':result['incidents']['unknown']={'status':'active','last_seen':result['as_of'],'issues':{'bad':1}}
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


def test_bounded_native_birth_attestation_matches_actual_kernel_identity(monkeypatch):
    import os
    from pathlib import Path
    root=Path(monitor.__file__).resolve().parents[3]
    monkeypatch.chdir(root/'src')
    pid=os.getpid(); ticks=(Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1].split()[19]
    now=datetime.now(monitor.KST)
    generation=dict(release_root=str(root),started_at=now.isoformat(),
        selector_reported_pid_receipt=dict(pid=pid,start_ticks=ticks,process_cwd=str(root/'src')))
    proof=monitor._attest_health_actor_birth(generation,now)
    generation['actor_birth_proof']=proof
    assert proof['status']=='verified'
    assert monitor._verified_health_actor_birth(proof,[str(pid),ticks],now,generation) is not None


@pytest.mark.parametrize('mutation', [None, 'boot_epoch', 'clock_ticks_per_second', 'start_ticks',
    'birth_lower_bound_epoch', 'birth_lower_bound_at', 'observed_at', 'process_cwd', 'runtime_effect'])
def test_native_birth_receipt_math_and_generation_binding(mutation):
    from copy import deepcopy
    now=monitor.stamp('2026-10-14T16:45:00+09:00')
    proof,generation=_health_birth_fixture(now)
    if mutation:
        bad={'boot_epoch':True,'clock_ticks_per_second':0,'start_ticks':901,
             'birth_lower_bound_epoch':float('nan'),'birth_lower_bound_at':now.isoformat(),
             'observed_at':(now+timedelta(seconds=1)).isoformat(),'process_cwd':'/other/src','runtime_effect':True}
        proof=deepcopy(proof);proof[mutation]=bad[mutation]
    assert (monitor._verified_health_actor_birth(proof,['9','900'],now,generation) is not None)==(mutation is None)


@pytest.mark.parametrize('unknown_age,partial_start_age,expected', [(200,300,False),(100,300,True),(200,100,False)])
def test_current_lifetime_excludes_only_prebirth_unknown_and_covers_tail_without_rereads(
        tmp_path,monkeypatch,unknown_age,partial_start_age,expected):
    now=monitor.stamp('2026-10-14T16:45:00+09:00')
    proof,generation=_health_birth_fixture(now)
    trace=dict(decision_ts=(now-timedelta(seconds=unknown_age)).isoformat(),decision_stage='entry_screen',
        stock_code='036930',machine_evaluation_status='assessment_contract_invalid',
        machine_contract_error='path_auxiliary_feature_input_conflict')
    calls=[]
    def read(path,*args,**kwargs):
        calls.append(path)
        return ([trace] if 'ai_decision_trace' in str(path) else []),dict(status='partial',window_covered=False,
            malformed_rows=0,missing_timestamp_rows=0,incomplete_last_line=False,
            first_read_at=(now-timedelta(seconds=partial_start_age)).isoformat())
    monkeypatch.setattr(monitor,'_recent_source_rows',read)
    with monitor._health_actor_scope(generation):
        original=monitor.source_gap_semantics(tmp_path,now)
    assert len(calls)==3 and original['issues']=={'machine_trace:path_auxiliary_feature_input_conflict':1}
    cohort=original['current_health_cohort'];view=cohort['view']
    assert bool(view['issues']) is expected
    assert cohort['actor_birth_proof']==proof
    assert view['excluded_pre_actor_birth_count']==int(unknown_age==200)
    assert (view['sources']['trace']['status']=='complete')==(partial_start_age==300)
    assert original['sources']['trace']['status']=='partial'  # Preserve original10m evidence.


def test_pure_projection_requires_identical_generation_birth_and_complete_lifetime_tail():
    from copy import deepcopy
    result=_observation_health_fixture();now=monitor.stamp(result['as_of'])
    proof,generation=_health_birth_fixture(now)
    result['observer_generation']=generation
    for name in ('source_gap_semantics','machine_semantics'):
        original=result[name]; view=deepcopy(original)
        token=monitor._HEALTH_BIRTH.set(proof)
        try:original['current_health_cohort']=monitor._health_cohort(view,['9','900'],now,excluded=1)
        finally:monitor._HEALTH_BIRTH.reset(token)
    source=result['source_gap_semantics']['current_health_cohort']['view']['sources']['trace']
    source.update(coverage_basis='current_actor_lifetime_bounded_tail',original_window_status='partial',
        first_read_at=(now-timedelta(seconds=300)).isoformat(),
        current_window_start_at=proof['birth_lower_bound_at'])
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    source['first_read_at']=now.isoformat()
    assert monitor.observation_health_projection(result)['status']=='not_eligible'
    source['first_read_at']=(now-timedelta(seconds=300)).isoformat()
    result['machine_semantics']['current_health_cohort']['actor_birth_proof']={**proof,'boot_epoch':123}
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('reason', ['post_receipt_observation_warmup','fixed_watch_post_receipt_warmup','exact_0B_missing'])
@pytest.mark.parametrize('bad', [False,True])
def test_active_session_known_fixed_source_waits_are_warning_only_with_exact_safety(tmp_path,monkeypatch,reason,bad):
    now=monitor.stamp('2026-10-14T16:45:00+09:00')
    fields=dict(watch_origin='MAIN_FIXED_WATCH',source_quality_reason=reason,venue_source_quality_status='pass',
        effective_venue='KRX_NXT_INTEGRATED',market_session_bucket='KRX_NXT_AFTERMARKET',
        actual_order_submitted='False',broker_order_forbidden='True')
    if bad:fields['broker_order_forbidden']=1
    row=dict(pipeline='ENTRY_PIPELINE',stage='main_fixed_watch_observation_wait',stock_code='005930',
             emitted_at=now.isoformat(),fields=fields)
    def read(path,*args,**kwargs):return ([row] if 'pipeline_events' in str(path) else []),dict(status='complete')
    monkeypatch.setattr(monitor,'_recent_source_rows',read)
    census=monitor.source_gap_semantics(tmp_path,now)['fixed_watch_waits']
    assert census['known_source_wait_count']==int(not bad)
    assert census['unclassified_or_actionable_wait_count']==int(bad)
    assert census['reason_counts']=={reason:1}


@pytest.mark.parametrize('receipt_format', ['dict','json','literal'])
def test_native_pending_unknown_censored_observation_is_not_a_no_match_or_admission(tmp_path,receipt_format):
    now=monitor.stamp('2026-10-14T16:45:00+09:00')
    row=_native_no_match_probe(now,receipt_format='dict')
    row['fields'].update(zero_base_probe_result='observation_incomplete',
                         zero_base_probe_reason='confirmation_pending_at_residence_end')
    receipt=row['fields']['native_observation_receipt']
    receipt.update(reason='required_window_incomplete',native_source_current=True,
        selected_branch_truth={'G1':'UNKNOWN','G2':'UNKNOWN'},selected_pending_count=1,source_censored_count=57,
        selected_lifecycle_counts={'G1':{'UNKNOWN':29},'G2':{'UNKNOWN':29}})
    if receipt_format != 'dict':
        row['fields']['native_observation_receipt']=(json.dumps(receipt) if receipt_format=='json' else repr(receipt))
    assert monitor._probe_verified_pending(row)=={'pending_count':1,'unknown_count':58,'source_censored_count':57}
    _source_gap_files(tmp_path,now,probes=[row])
    gap=monitor.source_gap_semantics(tmp_path,now)
    assert gap['observed']['probe_observation_incomplete']==1
    assert gap['probe_route_native_no_match_counts']=={} and gap['probe_route_assessed_counts']=={}
    census=gap['native_pending_observations']
    assert census['verified_pending_count']==1 and census['unknown_count']==58 and census['source_censored_count']==57
    assert census['machine_admission_proven'] is False and census['pattern_no_match_proven'] is False
    result=_observation_health_fixture(); result['source_gap_semantics'].update(
        observed={'probe_results':1,'probe_observation_incomplete':1},status='gap_observed',
        native_pending_observations=census,diagnostics=gap['diagnostics'],diagnostics_by_scope=gap['diagnostics_by_scope'],
        probe_route_counts=gap['probe_route_counts'],probe_route_source_covered_counts=gap['probe_route_source_covered_counts'])
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    census['unclassified_count']=1
    assert monitor.observation_health_projection(result)['status']=='not_eligible'
    receipt['selected_ready_count']=1
    row['fields']['native_observation_receipt']=receipt
    assert monitor._probe_verified_pending(row) is None


@pytest.mark.parametrize('raw_ready,historical_true,unknown', [(0, 0, 9), (1, 0, 9), (0, 4, 9), (1, 4, 0)])
def test_pending_selected_scope_keeps_latest_truth_and_historical_populations_separate(raw_ready, historical_true, unknown):
    now = monitor.stamp('2026-10-15T08:10:00+09:00')
    row = _native_no_match_probe(now, receipt_format='dict')
    row['fields'].update(zero_base_probe_result='observation_incomplete',
        zero_base_probe_reason='confirmation_pending_at_residence_end')
    receipt = row['fields']['native_observation_receipt']
    receipt.update(reason='no_matching_pattern', native_source_current=True,
        selected_branch_truth={'G1': 'FALSE'}, selected_pending_count=2,
        raw_ready_count=raw_ready, selected_ready_count=0, source_censored_count=0,
        selected_lifecycle_counts={'G1': {'TRUE': historical_true, 'FALSE': 10, 'UNKNOWN': unknown}})
    before = json.dumps(row, sort_keys=True)
    assert monitor._probe_verified_pending(row) == dict(pending_count=2, unknown_count=unknown, source_censored_count=0)
    assert json.dumps(row, sort_keys=True) == before
    assert monitor._probe_verified_no_match(row) is False
    receipt['selected_ready_count'] = 1
    assert monitor._probe_verified_pending(row) is None
    receipt['selected_ready_count'] = 0
    receipt['selected_branch_truth']['G1'] = 'TRUE'
    assert monitor._probe_verified_pending(row) is None
    receipt['selected_branch_truth']['G1'] = 'FALSE'
    receipt['native_source_current'] = False
    assert monitor._probe_verified_pending(row) is None


def test_verified_native_false_is_warning_without_machine_admission_and_tampered_count_fails(tmp_path):
    now=monitor.stamp('2026-10-14T16:45:00+09:00')
    row=_native_no_match_probe(now,receipt_format='dict')
    _source_gap_files(tmp_path,now,probes=[row])
    gap=monitor.source_gap_semantics(tmp_path,now)
    result=_observation_health_fixture(); result['source_gap_semantics'].update(
        observed=gap['observed'],status=gap['status'],diagnostics=gap['diagnostics'],
        diagnostics_by_scope=gap['diagnostics_by_scope'],probe_route_counts=gap['probe_route_counts'],
        probe_route_source_covered_counts=gap['probe_route_source_covered_counts'],
        probe_route_native_no_match_counts=gap['probe_route_native_no_match_counts'])
    assert monitor.observation_health_projection(result)['status']=='warning_pending'
    assert result['machine_semantics']['observation_count']==0
    result['source_gap_semantics']['probe_route_native_no_match_counts']['krx_nxt_integrated']=2
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('receipt_format', ['literal', 'json', 'dict'])
def test_native_all_false_is_source_coverage_without_machine_admission(tmp_path, receipt_format):
    now = START + timedelta(minutes=10)
    rows = [_probe_source_row(now-timedelta(seconds=i), 'source_unavailable',
                             '0B_missing') for i in range(8)]
    for i in range(2):
        row = _native_no_match_probe(now-timedelta(seconds=20+i), receipt_format=receipt_format)
        row['fields']['physical_probe_lease_id'] = f'lease-{i}'
        rows.append(row)
    _source_gap_files(tmp_path, now, probes=rows)
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result['issues'] == {}
    assert result['probe_route_counts'] == {'krx_nxt_integrated': 10}
    assert result['probe_route_source_covered_counts'] == {'krx_nxt_integrated': 2}
    assert result['probe_route_native_no_match_counts'] == {'krx_nxt_integrated': 2}
    assert result['probe_route_assessed_counts'] == {}
    assert result['diagnostics']['machine_probe:0B_missing'] == 8
    assert result['diagnostics']['machine_probe:native_no_matching_pattern'] == 2
    assert result['healthy_by_scope'] == {'route:krx_nxt_integrated|machine_probe:coverage_degraded': 1}
    state = {'as_of': now.isoformat(), 'incidents': {}, 'notification_pending': []}
    gap = {**result, 'issues': {'machine_probe:coverage_degraded:krx_nxt_integrated': 1},
        'issues_by_scope': {'route:krx_nxt_integrated|machine_probe:coverage_degraded': 1}}
    monitor.attach_source_gap_semantics(state, gap)
    monitor.attach_source_gap_semantics(state, result)
    assert state['incidents']['machine_auxiliary_intraday_source_gap']['status'] == 'recovered'
    assert state['incidents']['machine_auxiliary_intraday_source_gap']['historical_source_repaired'] is False


@pytest.mark.parametrize('key,value', [
    ('reason', 'required_window_incomplete'), ('item', '005930_NX'), ('venue', 'NXT'),
    ('process_pid', 124), ('process_start_ticks', ''), ('family_sha256', '-'),
    ('scope_execution_hash', 'g'*64), ('selected_scope', ''),
    ('selected_branch_truth', {'G1': 'UNKNOWN'}), ('selected_branch_truth', {'G1': 'TRUE'}),
    ('selected_branch_truth', {}), ('runtime_effect', True), ('observed_epoch', 0),
    ('observed_epoch', float('nan')), ('native_epoch', False), ('native_sequence', 0),
    ('observed_seconds', float('inf')), ('raw_ready_count', -1), ('raw_ready_count', False),
    ('selected_ready_count', 1), ('schema', 'other'), ('evaluation_role', 'claim'),
])
def test_native_no_match_requires_exact_complete_receipt(key, value):
    row = _native_no_match_probe(START, receipt_format='dict')
    row['fields']['native_observation_receipt'][key] = value
    assert monitor._probe_verified_no_match(row) is False


@pytest.mark.parametrize('key,value', [
    ('zero_base_route', 'krx_only'), ('zero_base_producer_pid', '124'),
    ('zero_base_ws_wait_reason', '0B_age_exceeded'), ('zero_base_ws_exact_0b_count', '0'),
    ('zero_base_ws_signed_0b_count', '0'), ('zero_base_ws_exact_0d_count', '0'),
    ('native_observation_receipt', 'x'*8193), ('native_observation_receipt', '{}'),
    ('native_observation_receipt', 'not-a-literal'),
    ('zero_base_probe_result', 'source_unavailable'),
])
def test_native_no_match_rejects_missing_or_conflicting_outer_source(key, value):
    row = _native_no_match_probe(START)
    row['fields'][key] = value
    assert monitor._probe_verified_no_match(row) is False


def test_probe_coverage_deduplicates_physical_lease_not_distinct_attempts(tmp_path):
    now = START + timedelta(minutes=10)
    row = _native_no_match_probe(now)
    rows = [json.loads(json.dumps(row)) for _ in range(12)]
    for i, copy in enumerate(rows):
        copy['emitted_at'] = (now+timedelta(milliseconds=i)).isoformat()
    _source_gap_files(tmp_path, now, probes=rows)
    result = monitor.source_gap_semantics(tmp_path, now+timedelta(seconds=1))
    assert result['observed']['probe_results'] == 1
    assert result['probe_route_source_covered_counts'] == {'krx_nxt_integrated': 1}
    assert not result['healthy_by_scope']  # Below route recovery floor.


def test_missing_capture_does_not_count_as_source_coverage(tmp_path):
    now = START + timedelta(minutes=10)
    rows = [_probe_source_row(now-timedelta(seconds=i), 'assessed', 'machine_assessed')
            for i in range(10)]
    for row in rows:
        row['fields']['machine_capture_status'] = 'failed'
    _source_gap_files(tmp_path, now, probes=rows)
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result['probe_route_assessed_counts'] == {'krx_nxt_integrated': 10}
    assert not result['probe_route_source_covered_counts']
    assert result['issues']['machine_probe:capture_receipt_missing_or_invalid'] == 10
    assert result['issues']['machine_probe:coverage_degraded:krx_nxt_integrated'] == 1


def test_native_no_match_does_not_recover_missing_machine_capture(tmp_path):
    now = START + timedelta(minutes=10)
    rows = [_native_no_match_probe(now-timedelta(seconds=i)) for i in range(10)]
    for i, row in enumerate(rows):
        row['fields']['physical_probe_lease_id'] = f'lease-{i}'
    _source_gap_files(tmp_path, now, probes=rows)
    result = monitor.source_gap_semantics(tmp_path, now)
    state = {'as_of': now.isoformat(), 'incidents': {
        'machine_auxiliary_intraday_source_gap': {'status': 'active',
          'issues_by_scope': {'route:krx_nxt_integrated|machine_probe:capture_receipt_missing_or_invalid': 1}}},
        'notification_pending': []}
    monitor.attach_source_gap_semantics(state, result)
    assert state['incidents']['machine_auxiliary_intraday_source_gap']['status'] == 'historical_unresolved'


def test_native_no_match_uses_final_native_window_not_initial_warmup_target():
    row = _native_no_match_probe(START)
    row['fields'].update(zero_base_ws_exact_0b_count='3', zero_base_ws_signed_0b_count='3',
                         zero_base_ws_sample_target='5', zero_base_ws_sample_target_met='False')
    assert monitor._probe_verified_no_match(row) is True


def test_explicit_native_no_match_reason_keeps_strict_truth_contract():
    row = _native_no_match_probe(START+timedelta(minutes=10), receipt_format='dict')
    row['fields']['zero_base_probe_reason'] = 'native_observation_no_matching_pattern'
    assert monitor._probe_verified_no_match(row)
    row['fields']['native_observation_receipt']['selected_branch_truth']['G2'] = 'UNKNOWN'
    assert not monitor._probe_verified_no_match(row)


def test_new_native_results_require_lifecycle_and_keep_incomplete_distinct():
    row=_native_no_match_probe(START+timedelta(minutes=10),receipt_format='dict')
    row['fields'].update(zero_base_probe_result='pattern_not_matched',zero_base_probe_reason='native_observation_no_matching_pattern')
    receipt=row['fields']['native_observation_receipt'];receipt['native_source_current']=True
    assert not monitor._probe_verified_no_match(row)
    receipt['selected_lifecycle_counts']={b:{'FALSE':10} for b in receipt['selected_branch_truth']}
    assert monitor._probe_verified_no_match(row)
    receipt['selected_pending_count']=1
    assert not monitor._probe_verified_no_match(row)
    row['fields']['zero_base_probe_result']='observation_incomplete'
    assert monitor._probe_verified_no_match(row,allow_incomplete=True)


def _no_match_with_unselected_ready():
    row=_native_no_match_probe(START+timedelta(minutes=10),receipt_format='dict')
    fields=row['fields'];receipt=fields['native_observation_receipt']
    fields.update(zero_base_probe_result='pattern_not_matched',zero_base_probe_result_schema='zero_base_probe_result_v2',
                  zero_base_probe_reason='native_observation_no_matching_pattern')
    receipt.update(raw_ready_count=1,native_source_current=True,selected_pending_count=0,source_censored_count=0,
                   selected_lifecycle_counts={b:{'TRUE':0,'FALSE':10} for b in receipt['selected_branch_truth']})
    fields['zero_base_branch_readiness']=dict(schema='native_branch_residence_requirements_v2',status='observed',
        runtime_effect=False,decision_authority='none',scope_changed=False,price_basis='exact_native_trade',
        route=fields['zero_base_route'],policy_scope=receipt['selected_scope'],
        **{k:receipt[k] for k in ('item','family_sha256','scope_execution_hash','native_epoch','native_sequence')},
        branch_descriptors={b:dict(detector_truth=v) for b,v in receipt['selected_branch_truth'].items()})
    return row


@pytest.mark.parametrize('encoding',['dict','json','literal'])
def test_other_cell_ready_is_bound_no_match_without_machine_admission(tmp_path,encoding):
    row=_no_match_with_unselected_ready()
    if encoding!='dict':
        for key in ('native_observation_receipt','zero_base_branch_readiness'):
            row['fields'][key]=(json.dumps if encoding=='json' else repr)(row['fields'][key])
    assert monitor._probe_verified_no_match(row)
    now=monitor.stamp(row['emitted_at'])
    _source_gap_files(tmp_path,now,probes=[row])
    result=monitor.source_gap_semantics(tmp_path,now)
    assert result['probe_route_native_no_match_counts']=={'krx_nxt_integrated':1}
    assert not result['probe_route_assessed_counts']


@pytest.mark.parametrize('target,key,value',[
    ('receipt','selected_ready_count',1),('receipt','selected_pending_count',1),
    ('receipt','native_source_current',False),('receipt','process_pid',124),
    ('receipt','selected_scope','other_non_fixed|AFTER|LT_20000'),
    ('receipt','selected_branch_truth',{'G1':'TRUE','G2':'FALSE'}),
    ('receipt','selected_lifecycle_counts',{'G1':{'TRUE':1,'FALSE':10},'G2':{'FALSE':10}}),
    ('receipt','selected_lifecycle_counts',{'G1':None,'G2':{'FALSE':10}}),
    ('receipt','selected_lifecycle_counts',{'G1':{'FALSE':True},'G2':{'FALSE':10}}),
    ('readiness','scope_execution_hash','c'*64),('readiness','native_sequence',199),
    ('readiness','scope_changed',True),('readiness','runtime_effect',True),
])
def test_other_cell_ready_never_hides_selected_or_unbound_failure(target,key,value):
    row=_no_match_with_unselected_ready()
    field='native_observation_receipt' if target=='receipt' else 'zero_base_branch_readiness'
    row['fields'][field][key]=value
    assert not monitor._probe_verified_no_match(row)


def _observer_selection_fixture(tmp_path, monkeypatch):
    root = tmp_path.resolve(); release = root / "release"
    release.mkdir()
    code = dict(release_root=str(release), git_commit="b" * 40, observer_code_sha256="c" * 64)
    monkeypatch.setattr(monitor, "_observer_code_identity", lambda: dict(code))
    selection = dict(schema="runtime_release_selection_v1", release_root=str(release), git_commit="b" * 40,
        selected_at_kst="2026-10-14T14:35:00+09:00", actual_pid_consumed=True,
        actual_pid_receipt={"schema": "runtime_release_pid_receipt_v1", "pid": 42,
            "start_ticks": "123", "release_root": str(release), "git_commit": "b" * 40,
            "process_cwd": str(release / "src"), "recorded_at_kst": "2026-10-14T14:36:00+09:00"})
    path = root / "data/runtime/runtime_release_selection.json"
    path.parent.mkdir(parents=True); path.write_text(json.dumps(selection))
    path.with_suffix(".lock").write_text("")
    return root, path, selection, code


@pytest.mark.parametrize('with_notify,change_selection',[(False,False),(True,False),(True,True)])
def test_real_main_seals_final_generation_and_notification_before_health_publication(
        tmp_path,monkeypatch,capsys,with_notify,change_selection):
    """Exercise parser/evaluate/attach/lease/two finishes/notify/real atomic writes.

    Expensive semantic readers use small deterministic receipts; birth proof is
    read from the current test process's native kernel identity. No live report,
    provider, Telegram or trading process is accessed.
    """
    import os
    from copy import deepcopy
    from pathlib import Path
    root,selector,selection,_=_observer_selection_fixture(tmp_path,monkeypatch)
    release=Path(selection['release_root']);(release/'src').mkdir()
    monkeypatch.chdir(release/'src')
    ticks=(Path('/proc')/str(os.getpid())/'stat').read_text().split(') ',1)[1].split()[19]
    actor=[str(os.getpid()),ticks]
    selection['actual_pid_receipt'].update(pid=os.getpid(),start_ticks=ticks)
    selector.write_text(json.dumps(selection))
    now=datetime.now(monitor.KST)
    fixture=_observation_health_fixture(); old=monitor.stamp(fixture['as_of']);delta=now-old
    def shift(value):
        if isinstance(value,dict):return {k:shift(v) for k,v in value.items()}
        if isinstance(value,list):return [shift(v) for v in value]
        if isinstance(value,str) and len(value)>10 and value[10]=='T' and monitor.stamp(value):
            return (monitor.stamp(value)+delta).isoformat()
        if isinstance(value, str) and len(value) == 10 and monitor.stamp(value):
            # Policy effective dates move with this live-clock fixture too.
            return (monitor.stamp(value).date() + (now.date() - old.date())).isoformat()
        return value
    fixture=shift(fixture)
    from src.trading.market import session_contract
    context=session_contract.resolve_market_session(now)
    fixture['source_gap_semantics']['fixed_watch_waits'].update(count=0,session_boundary_wait_count=0,
        reason_counts={},native_session_regime=context.session_regime,native_entry_allowed_by_clock=context.entry_allowed_by_clock)
    # Real evaluate receives the same current input contract as the fixture.
    inp=fixture['input_provenance']
    raw=root/'source.json';raw.write_text(json.dumps(dict(target_date=now.date().isoformat(),dry_run=False,
        submission_monitor=dict(schema=monitor.SCHEMA,as_of=inp['snapshot_as_of'],latest_event_at=inp['latest_event_at'],
            rows=[],identity_missing_events=0,auxiliary_ai_semantic_issue_counts={}))))
    class Clock(datetime):
        calls=0
        @classmethod
        def now(cls,tz=None):
            value=now+timedelta(seconds=cls.calls);cls.calls+=1
            return value if tz else value.replace(tzinfo=None)
    monkeypatch.setattr(monitor,'datetime',Clock)
    monkeypatch.setattr(monitor,'PROJECT_ROOT',root)
    for key in ('source_gap_semantics','machine_semantics','entry_execution_tuning_semantics'):
        def reader(*args,_key=key,**kwargs):
            result=deepcopy(fixture[_key])
            if _key!='entry_execution_tuning_semantics':
                result['current_health_cohort']=monitor._health_cohort(deepcopy(result),actor,now)
            return result
        monkeypatch.setattr(monitor,key,reader)
    finishes=[];finish=monitor._finish_observer_generation
    def recorded_finish(*args,**kwargs):
        result=finish(*args,**kwargs);finishes.append(deepcopy(result));return result
    monkeypatch.setattr(monitor,'_finish_observer_generation',recorded_finish)
    def fake_notify(result,path):
        assert len(finishes)==1
        result['notification_status']='fake_sent_no_network'
        result['last_notification_at']=now.isoformat()
        result['incidents']['notification_fixture']=dict(status='recovered',last_seen=now.isoformat(),issues={})
        if change_selection:selector.write_text(json.dumps({**selection,'actual_pid_consumed':False}))
    monkeypatch.setattr(monitor,'notify',fake_notify)
    projections=[];project=monitor.observation_health_projection
    def project_after_final(result):
        assert len(finishes)==2
        generation=result['observer_generation']
        assert generation==finishes[-1] and generation['sha256']==monitor._observer_seal(generation)
        assert generation['actor_birth_proof']['status']=='verified'
        if with_notify:assert result['notification_status']=='fake_sent_no_network'
        value=project(result);projections.append(deepcopy(value));return value
    monkeypatch.setattr(monitor,'observation_health_projection',project_after_final)
    argv=['--report',str(raw)]+(['--notify'] if with_notify else [])
    assert monitor.main(argv)==(75 if change_selection else 0)
    terminal=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    output=root/'data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json'
    if change_selection:
        assert not output.exists() and terminal['publication']=={} and projections==[]
        return
    latest=json.loads(output.read_text());state=json.loads((root/'tmp/submission_bottleneck_monitor_state.json').read_text())
    dated=json.loads(output.with_name('submission_bottleneck_monitor_'+now.date().isoformat()+'.json').read_text())
    assert latest==dated and latest['observation_health']==project(latest)==projections[0]
    assert state['incidents']==latest['incidents'] and state['run_id']==latest['run_id']
    assert state['last_notification_at']==latest['last_notification_at']
    assert 'observation_health' not in state and state['persistence_schema']=='submission_monitor_continuation_v1'
    assert latest['observation_health']['status']=='warning_pending',latest['observation_health']
    assert latest['observer_generation']['completed_at']==finishes[-1]['completed_at']
    assert terminal['publication']==dict(state=True,latest=True,dated=True)


def test_observer_generation_seals_selected_bytes_code_and_reported_pid(tmp_path, monkeypatch):
    root, path, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    started = datetime.fromisoformat("2026-10-14T14:40:00+09:00")
    generation = monitor._observer_generation_snapshot(root, run_id="d" * 32,
        target_date="2026-10-14", started_at=started)
    assert generation["generation_current"] is True
    assert generation["selection_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert generation["selector_reported_pid_receipt"] == selection["actual_pid_receipt"]
    assert generation["policy_pid_consumption_proven"] is False
    final = monitor._finish_observer_generation(generation, root, completed_at=started + timedelta(seconds=25))
    assert final["generation_current"] is True and final["status"] == "current"
    assert final["sha256"] == monitor._observer_seal(final)


def _ordered_observer_fixture(tmp_path, monkeypatch, phase="starting"):
    root, selector, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    now = datetime.now(monitor.KST)
    day = now.date().isoformat()
    path = root / "data/runtime/release_transitions" / day / code["git_commit"] / "status.json"
    path.parent.mkdir(parents=True)
    transition = dict(schema="ordered_intraday_deployment_v1",
        authority="APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART", policy_effect="unchanged",
        target_date=day, candidate_root=code["release_root"], candidate_commit=code["git_commit"],
        phase=phase, status="pass" if phase == "complete" else "running",
        successor_identity=dict(pid=42, start_ticks="123", cwd=code["release_root"] + "/src"))
    selection.update(approval_scope="ordered_intraday_deploy_and_restart", approved_by="user",
        selected_at_kst=(now - timedelta(minutes=2)).isoformat(), deployment_transition=str(path))
    selector.write_text(json.dumps(selection)); path.write_text(json.dumps(transition))
    return root, selector, selection, path, transition, now


@pytest.mark.parametrize("phase", ["selected", "prepared", "starting"])
@pytest.mark.parametrize("consumed", [False, True])
def test_ordered_startup_does_not_replace_frozen_report_or_state(
        tmp_path, monkeypatch, capsys, phase, consumed):
    root, selector, selection, transition_path, transition, now = _ordered_observer_fixture(tmp_path, monkeypatch, phase)
    selection["actual_pid_consumed"] = consumed
    if not consumed: selection.pop("actual_pid_receipt")
    selector.write_text(json.dumps(selection))
    monkeypatch.setattr(monitor, "PROJECT_ROOT", root)
    raw = root / "source.json"; raw.write_text("{}")
    saved = [root / "tmp/submission_bottleneck_monitor_state.json",
        root / "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json",
        root / "data/report/buy_funnel_sentinel" / f"submission_bottleneck_monitor_{now.date()}.json"]
    for path in saved:
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'{"original_source_gap":"preserved"}')
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in saved}
    monkeypatch.setattr(monitor, "evaluate", lambda *a: pytest.fail("startup performed observer work"))
    monkeypatch.setattr(monitor, "notify", lambda *a: pytest.fail("startup sent a notification"))
    assert monitor.main(["--report", str(raw), "--notify"]) == 75
    terminal = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert terminal["execution_status"] == "deferred" and terminal["publication"] == {}
    assert terminal["blocker"] == "observer_waiting_ordered_startup_completion"
    assert terminal["observer_generation"]["generation_current"] is False
    assert {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in saved} == before
    # Only the next independent run may carry the newly attested selector.
    transition.update(phase="complete", status="pass"); transition_path.write_text(json.dumps(transition))
    selection.update(actual_pid_consumed=True, actual_pid_receipt=dict(pid=42))
    selector.write_text(json.dumps(selection))
    fresh = monitor._observer_generation_snapshot(root, run_id="e" * 32,
        target_date=now.date().isoformat(), started_at=now)
    assert fresh["generation_current"] is True
    final = monitor._finish_observer_generation(terminal["observer_generation"], root, completed_at=now)
    assert final["generation_current"] is False


@pytest.mark.parametrize("damage", ["failed", "wrong_date", "wrong_commit", "wrong_authority", "wrong_approval", "path", "missing", "malformed", "changed_after_read"])
def test_ordered_observer_never_publishes_for_invalid_or_changed_transition(tmp_path, monkeypatch, damage):
    root, selector, selection, path, transition, now = _ordered_observer_fixture(tmp_path, monkeypatch, "complete")
    original = monitor._observer_generation_snapshot(root, run_id="e" * 32,
        target_date=now.date().isoformat(), started_at=now)
    assert original["generation_current"] is True
    if damage == "failed": transition.update(phase="failed", status="fail")
    elif damage == "wrong_date": transition["target_date"] = "2026-01-01"
    elif damage == "wrong_commit": transition["candidate_commit"] = "f" * 40
    elif damage == "wrong_authority": transition["authority"] = "unknown"
    elif damage == "wrong_approval": selection["approved_by"] = "unknown"
    elif damage == "path": selection["deployment_transition"] = str(root / "elsewhere.json")
    elif damage == "changed_after_read": transition["updated_at"] = now.isoformat()
    path.write_text(json.dumps(transition)); selector.write_text(json.dumps(selection))
    if damage == "missing": path.unlink()
    elif damage == "malformed": path.write_text("[]")
    final = monitor._finish_observer_generation(original, root, completed_at=now)
    assert final["generation_current"] is False
    assert final["policy_pid_consumption_proven"] is False


@pytest.mark.parametrize("change", ["selector", "code", "wrong_root", "missing", "malformed"])
def test_observer_publication_cannot_claim_changed_or_unknown_generation(tmp_path, monkeypatch, change):
    root, path, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    started = datetime.fromisoformat("2026-10-14T14:40:00+09:00")
    original = monitor._observer_generation_snapshot(root, run_id="d" * 32,
        target_date="2026-10-14", started_at=started)
    if change == "selector": path.write_text(json.dumps({**selection, "actual_pid_consumed": False}))
    elif change == "code": code["observer_code_sha256"] = "f" * 64
    elif change == "wrong_root": code["release_root"] = str(root / "other")
    elif change == "missing": path.unlink()
    else: path.write_text("[]")
    final = monitor._finish_observer_generation(original, root, completed_at=started + timedelta(seconds=1))
    assert final["generation_current"] is False
    assert final["status"] == "changed_or_unavailable"
    assert final["policy_pid_consumption_proven"] is False


def test_main_defers_without_overwriting_when_selection_changes_before_publication(tmp_path, monkeypatch, capsys):
    root, path, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "PROJECT_ROOT", root)
    raw = root / "source.json"; raw.write_text("{}")
    def changed_source(*args, **kwargs):
        path.write_text(json.dumps({**selection, "actual_pid_consumed": False}))
        return {"status": "observed", "issues": {"real_source_gap": 1}}
    monkeypatch.setattr(monitor, "source_gap_semantics", changed_source)
    monkeypatch.setattr(monitor, "attach_source_gap_semantics", lambda result, sem: result.update(source_gap_semantics=sem))
    monkeypatch.setattr(monitor, "notify", lambda *args: pytest.fail("changed generation notified current result"))
    assert monitor.main(["--report", str(raw), "--source-only", "--notify"]) == 75
    terminal = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert terminal["execution_status"] == "deferred"
    assert terminal["semantic_status"] == "partial"
    assert terminal["publication"] == {}
    assert terminal["observer_generation"]["generation_current"] is False
    assert terminal["source_gap_status"] == "observed"
    assert not list((root / "data/report/buy_funnel_sentinel").glob("*.json"))


@pytest.mark.parametrize("with_notify,costs,expected,reserve", [
    (False, (4, 5, 3), 0, 5),
    (True, (4, 5, 3), 75, 15),
    (False, (4, 9, 9), 75, 5),
])
def test_cli_reserves_only_requested_notification_work(
        tmp_path, monkeypatch, capsys, with_notify, costs, expected, reserve):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from src.engine.monitoring import observation_budget

    root, _, _, _ = _observer_selection_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "PROJECT_ROOT", root)
    clock = [0.0]
    monkeypatch.setattr(monitor, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    limits = []

    @contextmanager
    def computation_budget(deadline):
        limits.append(deadline)
        if clock[0] >= deadline:
            raise observation_budget.ObservationDeadline("validation_deferred:deadline")
        yield
        if clock[0] > deadline:
            raise observation_budget.ObservationDeadline("validation_deferred:deadline")

    monkeypatch.setattr(observation_budget, "computation_budget", computation_budget)
    for name, cost in zip(("source_gap_semantics", "entry_execution_tuning_semantics",
                           "machine_semantics"), costs):
        def read(*args, _cost=cost, **kwargs):
            clock[0] += _cost
            return dict(status="unobservable", issues={})
        monkeypatch.setattr(monitor, name, read)
        monkeypatch.setattr(monitor, "attach_" + name,
                            lambda result, value, _name=name: result.update({_name: value}))
    monkeypatch.setattr(monitor, "notify", lambda *args: None)
    raw = root / "source.json"
    raw.write_text("{}")
    args = ["--report", str(raw), "--budget-seconds", "25"]
    if with_notify:
        args.append("--notify")
    assert monitor.main(args) == expected
    terminal = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert limits == [25 - reserve] * 3
    assert terminal["execution_status"] == ("completed" if expected == 0 else "deferred")
    report = json.loads((root / "data/report/buy_funnel_sentinel" /
                         "submission_bottleneck_monitor_latest.json").read_text())
    assert report["execution_status"] == terminal["execution_status"]
    assert report["execution_budget"] == terminal["execution_budget"] == dict(
        total_seconds=25, computation_reserve_seconds=reserve,
        notification_requested=with_notify)
    assert report["semantic_status"] == "partial"
    assert clock[0] <= 25


def test_observer_publication_lease_serializes_existing_selector_writer(tmp_path, monkeypatch):
    root, path, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    lock_path = path.with_suffix(".lock")
    inode = lock_path.stat().st_ino
    with monitor._observer_publication_lease(root):
        with lock_path.open("rb") as writer:
            with pytest.raises(BlockingIOError):
                monitor.fcntl.flock(writer, monitor.fcntl.LOCK_EX | monitor.fcntl.LOCK_NB)
    with lock_path.open("rb") as writer:
        monitor.fcntl.flock(writer, monitor.fcntl.LOCK_EX | monitor.fcntl.LOCK_NB)
    assert lock_path.stat().st_ino == inode


def test_main_selector_change_during_notify_preserves_existing_canonical_bytes(tmp_path, monkeypatch, capsys):
    root, path, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "PROJECT_ROOT", root)
    raw = root / "source.json"; raw.write_text("{}")
    names = [root / "tmp/submission_bottleneck_monitor_state.json",
             root / "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json",
             root / "data/report/buy_funnel_sentinel" / f"submission_bottleneck_monitor_{datetime.now(monitor.KST).date().isoformat()}.json"]
    for saved in names:
        saved.parent.mkdir(parents=True, exist_ok=True); saved.write_text(json.dumps(dict(prior='preserved',schema=monitor.SCHEMA,incidents={})))
    before = {saved: saved.read_bytes() for saved in names}
    monkeypatch.setattr(monitor, "source_gap_semantics", lambda *args: {"status": "observed", "issues": {}})
    monkeypatch.setattr(monitor, "attach_source_gap_semantics", lambda result, sem: result.update(source_gap_semantics=sem))
    # Simulate a writer violating the existing lease. The second identity
    # check still refuses canonical publication; lawful writers are serialized.
    monkeypatch.setattr(monitor, "notify", lambda *args: path.write_text(json.dumps({**selection, "actual_pid_consumed": False})))
    assert monitor.main(["--report", str(raw), "--source-only", "--notify"]) == 75
    assert {saved: saved.read_bytes() for saved in names} == before
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["publication"] == {}


@pytest.mark.parametrize("which", ["selector", "lock"])
def test_observer_fifo_paths_fail_bounded_without_open_wait(tmp_path, monkeypatch, which):
    import multiprocessing
    import os
    root, selector, selection, code = _observer_selection_fixture(tmp_path, monkeypatch)
    path = selector if which == "selector" else selector.with_suffix(".lock")
    path.unlink(); os.mkfifo(path)
    context = multiprocessing.get_context("fork"); queue = context.Queue()
    def attempt():
        try:
            if which == "selector":
                result = monitor._observer_generation_snapshot(root, run_id="d" * 32,
                    target_date="2026-10-14", started_at=datetime.fromisoformat("2026-10-14T14:40:00+09:00"))
                queue.put((result["generation_current"], result["reason"]))
            else:
                with monitor._observer_publication_lease(root): queue.put((True, "unexpected lease"))
        except Exception as exc:
            queue.put((False, str(exc)))
    child = context.Process(target=attempt); child.start(); child.join(timeout=2)
    if child.is_alive():
        child.terminate(); child.join(timeout=2)
        pytest.fail("observer blocked on FIFO")
    valid, reason = queue.get(timeout=1)
    assert valid is False
    assert "regular_file_required" in reason or "lease_unavailable" in reason
    assert path.is_fifo()


def test_observer_read_open_race_fifo_replacement_uses_nonblocking_fd(tmp_path, monkeypatch):
    import os
    from pathlib import Path
    root, path, _, _ = _observer_selection_fixture(tmp_path, monkeypatch)
    real_open = monitor.os.open
    def replacement(selected, flags, *args, **kwargs):
        if Path(selected) == path:
            assert flags & os.O_NOFOLLOW
            assert flags & os.O_NONBLOCK
            path.unlink(); os.mkfifo(path)
        return real_open(selected, flags, *args, **kwargs)
    monkeypatch.setattr(monitor.os, "open", replacement)
    with pytest.raises(ValueError, match="regular_file_required"):
        monitor._observer_regular_bytes(path, limit=1024 * 1024)


def test_observer_lease_does_not_reclassify_real_publication_failure(tmp_path, monkeypatch):
    root, *_ = _observer_selection_fixture(tmp_path, monkeypatch)
    with pytest.raises(OSError, match="disk failure"):
        with monitor._observer_publication_lease(root):
            raise OSError("disk failure")


def test_main_source_report_fifo_is_bounded(tmp_path, monkeypatch):
    import multiprocessing
    import os
    root, *_ = _observer_selection_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "PROJECT_ROOT", root)
    fifo = root / "source.json"; os.mkfifo(fifo)
    monkeypatch.setattr(monitor, "source_gap_semantics", lambda *args: {"status": "observed", "issues": {}})
    monkeypatch.setattr(monitor, "attach_source_gap_semantics", lambda result, sem: result.update(source_gap_semantics=sem))
    context = multiprocessing.get_context("fork"); queue = context.Queue()
    child = context.Process(target=lambda: queue.put(monitor.main(["--report", str(fifo), "--source-only"])))
    child.start(); child.join(timeout=2)
    if child.is_alive():
        child.terminate(); child.join(timeout=2)
        pytest.fail("observer main blocked on source FIFO")
    assert queue.get(timeout=1) == 0
    assert fifo.is_fifo()


@pytest.mark.parametrize('partial', [False, True])
@pytest.mark.parametrize('outcome', ['response_invalid', 'timeout', 'unknown_pass'])
def test_active_observations_keep_bounded_inflight_outcomes_as_warning(partial, outcome):
    result, *_ = _bounded_outcome_health_fixture(partial=partial, outcome=outcome)
    result.update(status='observing', blocker=None, scopes={'KRX|krx_regular|bundle': {}})
    result['input_provenance']['row_count'] = 1
    before = json.dumps(result, sort_keys=True)
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'warning_pending', health
    assert health['reason'] == 'bounded_source_quality_observation'
    assert set(health['unmet_conditions']) >= {'monitor_state_not_quiet_full_observation',
                                             'current_input_provenance_invalid'}
    assert not any(health[k] for k in ('current_observation_verified', 'full_coverage_proven',
                                     'runtime_effect', 'allowed_runtime_apply'))
    assert json.dumps(result, sort_keys=True) == before


@pytest.mark.parametrize('bad', ['status', 'blocker', 'failed', 'dry', 'authority', 'date',
    'stale', 'row_bool', 'row_negative', 'row_missing', 'row_zero', 'scopes_missing',
    'scopes_type', 'scopes_malformed', 'order', 'identity', 'source_malformed', 'source_missing',
    'foreign_actor', 'unconsumed', 'birth_missing', 'source_issue', 'active_incident'])
def test_active_report_warning_rejects_invalid_publication_and_source_contracts(bad):
    result, gap, machine, lineage = _bounded_outcome_health_fixture(partial=False)
    result.update(status='observing', blocker=None, scopes={'KRX|krx_regular|bundle': {}})
    inp = result['input_provenance']; inp['row_count'] = 1
    if bad == 'status': result['status'] = 'unknown'
    elif bad == 'blocker': result['blocker'] = 'machine_identity_missing_events'
    elif bad == 'failed': result['execution_status'] = 'failed'
    elif bad == 'dry': inp['dry_run'] = True
    elif bad == 'authority': result['runtime_effect'] = True
    elif bad == 'date': inp['target_date'] = '2026-10-13'
    elif bad == 'stale':
        inp['snapshot_as_of'] = (monitor.stamp(result['as_of'])-timedelta(seconds=421)).isoformat()
        inp['snapshot_age_seconds'] = 421
    elif bad == 'row_bool': inp['row_count'] = True
    elif bad == 'row_negative': inp['row_count'] = -1
    elif bad == 'row_missing': inp.pop('row_count')
    elif bad == 'row_zero': inp['row_count'] = 0
    elif bad == 'scopes_missing': result.pop('scopes')
    elif bad == 'scopes_type': result['scopes'] = []
    elif bad == 'scopes_malformed': result['scopes'] = {'': None}
    elif bad == 'order': inp['snapshot_order'] = 'reversed'
    elif bad == 'identity': inp['identity_missing_events'] = 1
    elif bad == 'source_malformed': gap['sources']['probe']['malformed_rows'] = 1
    elif bad == 'source_missing': gap['sources'].pop('probe')
    elif bad == 'foreign_actor': lineage['attempt_ledger'][0]['producer_pid'] = '999'
    elif bad == 'unconsumed': result['observer_generation']['selector_reported_actual_pid_consumed'] = False
    elif bad == 'birth_missing': result['observer_generation'].pop('actor_birth_proof')
    elif bad == 'source_issue': gap['issues'] = {'machine_probe:source_contract_missing': 1}
    elif bad == 'active_incident':
        result['incidents']['current_submit_gap'] = dict(status='active', last_seen=result['as_of'],
                                                        issues={'source_or_submit_lineage_gap': 1})
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'not_eligible', health


@pytest.mark.parametrize('reason', ['exact_0B_missing', 'fixed_watch_post_receipt_warmup',
                                   'post_receipt_observation_warmup', 'exact_route_item_missing'])
@pytest.mark.parametrize('bad', [None, 'before_open', 'after_premarket', 'generation', 'admission',
    'signature', 'resolution', 'venue', 'bucket', 'symbol', 'symbol_type', 'submitted', 'forbidden',
    'unknown_reason', 'quality'])
def test_premarket_fixed_watch_wait_requires_native_route_generation_and_safety(tmp_path, monkeypatch, reason, bad):
    from src.engine.scalping.main_fixed_watch import generation_id, session_route
    now = monitor.stamp('2026-10-15T08:28:44.575705+09:00')
    route = session_route(now.timestamp(), '196170')
    admission = 'FIXED-2026-10-15-196170-krx_like_premarket-nxt_only-04d5219cff7e'
    fields = dict(watch_origin='MAIN_FIXED_WATCH', watch_admission_id=admission,
        watch_generation_id=generation_id(now.timestamp(), route),
        source_signature='MAIN_FIXED_WATCH:'+admission, venue_resolution='main_fixed_watch_session_route',
        source_quality_reason=reason, venue_source_quality_status='pass',
        effective_venue='PREMARKET_KRX_LIKE', market_session_bucket='krx_like_premarket',
        actual_order_submitted='False', broker_order_forbidden='True')
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait', stock_code='196170',
               emitted_at=now.isoformat(), fields=fields)
    if bad == 'before_open': row['emitted_at'] = '2026-10-15T07:59:59+09:00'
    elif bad == 'after_premarket': row['emitted_at'] = '2026-10-15T09:00:00+09:00'
    elif bad == 'generation': fields['watch_generation_id'] = '0'*64
    elif bad == 'admission': fields['watch_admission_id'] = admission.replace('nxt_only', 'krx_only')
    elif bad == 'signature': fields['source_signature'] = 'MAIN_FIXED_WATCH:foreign'
    elif bad == 'resolution': fields['venue_resolution'] = 'inferred'
    elif bad == 'venue': fields['effective_venue'] = 'KRX'
    elif bad == 'bucket': fields['market_session_bucket'] = 'krx_regular'
    elif bad == 'symbol': row['stock_code'] = '999999'
    elif bad == 'symbol_type': row['stock_code'] = []
    elif bad == 'submitted': fields['actual_order_submitted'] = 0
    elif bad == 'forbidden': fields['broker_order_forbidden'] = 1
    elif bad == 'unknown_reason': fields['source_quality_reason'] = 'new_unknown_reason'
    elif bad == 'quality': fields['venue_source_quality_status'] = 'unknown'
    def read(path, *args, **kwargs):
        return ([row] if 'pipeline_events' in str(path) else []), dict(status='complete')
    monkeypatch.setattr(monitor, '_recent_source_rows', read)
    census = monitor.source_gap_semantics(tmp_path, now)['fixed_watch_waits']
    assert census['known_source_wait_count'] == int(bad is None)
    assert census['unclassified_or_actionable_wait_count'] == int(bad is not None)
    assert census['native_entry_allowed_by_clock'] is False
    assert census['runtime_effect'] is False


@pytest.mark.parametrize('bad', [None, 'too_short', 'malformed', 'missing_clock', 'incomplete', 'io', 'not_tail'])
def test_current_lineage_recomputes_narrower_coverage_from_same_loaded_suffix(tmp_path, bad):
    from copy import deepcopy
    now = monitor.stamp('2026-10-15T08:30:13.312471+09:00')
    source = dict(status='partial', window_covered=False, tail_truncated=True,
        first_read_at='2026-10-15T08:05:32.969671+09:00', malformed_rows=0,
        missing_timestamp_rows=0, incomplete_last_line=False, read_count=1,
        bytes_read=8367448, source_size=12577010, source_identity=dict(device=66305, inode=531689))
    if bad == 'too_short': source['first_read_at'] = (now-timedelta(seconds=604)).isoformat()
    elif bad == 'malformed': source['malformed_rows'] = 1
    elif bad == 'missing_clock': source['missing_timestamp_rows'] = 1
    elif bad == 'incomplete': source['incomplete_last_line'] = True
    elif bad == 'io': source['reason'] = 'PermissionError'
    elif bad == 'not_tail': source['tail_truncated'] = False
    before = deepcopy(source)
    result = monitor._reversal_provider_lineage(tmp_path, now, [], tail_bytes=8*1024*1024,
        window_sec=600, pid_identity=['1481448','8438079'], _loaded=([],source,[],source))
    assert source == before
    for window in result['source_windows'].values():
        assert window['status'] == ('complete' if bad is None else 'partial')
        if bad is None:
            assert window['original_window_status'] == 'partial'
            assert window['current_window_seconds'] == 605
            assert monitor.stamp(window['current_window_start_at']) == now-timedelta(seconds=605)
            for field in ('first_read_at','bytes_read','read_count','source_identity'):
                assert window[field] == source[field]


@pytest.mark.parametrize('bad', [None, 'lower', 'first', 'window', 'bool_window', 'origin', 'tail'])
def test_bounded_health_verifies_narrowed_lineage_coverage_receipt(bad):
    result, gap, machine, lineage = _bounded_outcome_health_fixture(partial=False)
    now = monitor.stamp(result['as_of']); window = lineage['source_windows']['traces']
    window.update(status='complete', window_covered=True, original_window_status='partial', tail_truncated=True,
        coverage_basis='current_lineage_window_bounded_tail', current_window_seconds=605,
        first_read_at=(now-timedelta(seconds=1000)).isoformat(),
        current_window_start_at=(now-timedelta(seconds=605)).isoformat())
    if bad == 'lower': window['current_window_start_at'] = now.isoformat()
    elif bad == 'first': window['first_read_at'] = now.isoformat()
    elif bad == 'window': window['current_window_seconds'] = 600
    elif bad == 'bool_window': window['current_window_seconds'] = True
    elif bad == 'origin': window['original_window_status'] = 'unknown'
    elif bad == 'tail': window['tail_truncated'] = False
    assert monitor.observation_health_projection(result)['status'] == ('warning_pending' if bad is None else 'not_eligible')


@pytest.mark.parametrize('bad', [None, 'unknown_blocker', 'scope_present', 'stale', 'bool_row', 'dry',
    'index_generation', 'index_schema', 'index_contract', 'index_clock', 'index_bytes', 'index_malformed',
    'incident_new', 'incident_unknown', 'birth_invalid'])
def test_quiet_current_pid_with_old_scanner_rows_and_verified_index_preserves_history(bad):
    result, gap, machine, lineage = _bounded_outcome_health_fixture(partial=False)
    result.update(status='unobservable', blocker='missing_stale_or_noncurrent_sentinel_evidence', scopes={})
    result['input_provenance']['row_count'] = 1
    now = monitor.stamp(result['as_of'])
    birth = result['observer_generation']['actor_birth_proof']
    lower = max(now.timestamp()-600, birth['birth_lower_bound_epoch'])
    probe = gap['sources']['probe']
    probe.update(bytes_read=0, coverage_basis='verified_forward_sentinel_source_window_v1',
        coverage_started_at=(now-timedelta(seconds=600)).isoformat(),
        current_window_start_at=datetime.fromtimestamp(lower,monitor.KST).isoformat(),
        actor_lifetime_bound=True, cache_schema_version=20, projection_contract='a'*64,
        historical_stage_coverage='not_backfilled_before_cache_offset', cache_generation=[1,2,3,4,5],
        indexed_raw_offset=2048, indexed_bytes_read=400, indexed_identity_bytes_read=100)
    key='machine_auxiliary_intraday_source_gap'
    incident=dict(status='historical_unresolved',
        last_seen=datetime.fromtimestamp(birth['birth_lower_bound_epoch']-1,monitor.KST).isoformat(),
        issues={'machine_trace:entry_machine_input_deadline_expired':1})
    result['incidents'][key]=incident
    if bad=='unknown_blocker':result['blocker']='unknown'
    elif bad=='scope_present':result['scopes']={'unexpected':{}}
    elif bad=='stale':result['input_provenance']['snapshot_age_seconds']=500
    elif bad=='bool_row':result['input_provenance']['row_count']=True
    elif bad=='dry':result['input_provenance']['dry_run']=True
    elif bad=='index_generation':probe['cache_generation']=[1]
    elif bad=='index_schema':probe['cache_schema_version']=0
    elif bad=='index_contract':probe['projection_contract']='bad'
    elif bad=='index_clock':probe['current_window_start_at']=now.isoformat()
    elif bad=='index_bytes':probe['indexed_bytes_read']=True
    elif bad=='index_malformed':probe['malformed_rows']=1
    elif bad=='incident_new':incident['last_seen']=now.isoformat()
    elif bad=='incident_unknown':result['incidents']['unknown']=result['incidents'].pop(key)
    elif bad=='birth_invalid':birth['boot_epoch']+=1
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if bad is None else 'not_eligible'),health
    assert json.dumps(result,sort_keys=True)==before
    assert health['current_observation_verified'] is False and health['runtime_effect'] is False


@pytest.mark.parametrize('clock', ['08:45:00', '10:00:00', '16:00:00'])
@pytest.mark.parametrize('failure', ['fixed_watch_warmup', 'route_snapshot_missing',
    'exact_route_item_missing', 'exact_0B_missing', 'exact_0D_missing',
    'post_admission_0B_missing', 'post_admission_0D_missing', 'price_missing',
    'fixed_watch_post_receipt_warmup'])
def test_actual_fixed_watch_producer_waits_have_bounded_report_census(tmp_path, monkeypatch, clock, failure):
    from src.engine.scalping import main_fixed_watch as producer
    now = monitor.stamp('2026-10-15T'+clock+'+09:00')
    epoch = now.timestamp()
    route = producer.session_route(epoch, '005930')
    target = dict(code='005930', watch_generation_id=producer.generation_id(epoch, route),
                  entry_armed_at_epoch=epoch-30, _fixed_first_exact_receipt_epoch=epoch-20)
    snapshot = dict(last_ws_item=route['item'], curr=100,
        last_realtime_type_item={kind:route['item'] for kind in ('0B','0D')},
        last_realtime_type_ts={kind:epoch-1 for kind in ('0B','0D')})
    if failure == 'fixed_watch_warmup': target['entry_armed_at_epoch'] = epoch-1
    elif failure == 'route_snapshot_missing': snapshot = {}
    elif failure == 'exact_route_item_missing': snapshot['last_ws_item'] = '005930'
    elif failure.startswith('exact_'): snapshot['last_realtime_type_item'].pop(failure.split('_')[1])
    elif failure.startswith('post_admission_'): snapshot['last_realtime_type_ts'][failure.split('_')[2]] = epoch-60
    elif failure == 'price_missing': snapshot['curr'] = 0
    else: target['_fixed_first_exact_receipt_epoch'] = 0
    ready, reason = producer.observation_ready(target, snapshot, now_epoch=epoch)
    assert not ready and reason == failure
    admission = f"FIXED-{now.date()}-005930-{route['bucket']}-{route['route']}-0123456789ab"
    fields = dict(watch_origin='MAIN_FIXED_WATCH', watch_admission_id=admission,
        watch_generation_id=target['watch_generation_id'], source_signature='MAIN_FIXED_WATCH:'+admission,
        venue_resolution='main_fixed_watch_session_route', source_quality_reason=reason,
        venue_source_quality_status='pass', effective_venue=route['venue'],
        market_session_bucket=route['bucket'], actual_order_submitted=False, broker_order_forbidden=True)
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
               stock_code='005930', emitted_at=now.isoformat(), fields=fields)
    monkeypatch.setattr(monitor, '_recent_source_rows', lambda path,*a,**k:
        ([row] if 'pipeline_events' in str(path) else [], dict(status='complete')))
    census = monitor.source_gap_semantics(tmp_path,now)['fixed_watch_waits']
    assert census['known_source_wait_count'] == 1
    assert census['unclassified_or_actionable_wait_count'] == 0
    assert census['reason_counts'] == {failure:1}
    assert census['runtime_effect'] is False
    fields['watch_generation_id'] = '0'*64
    # Legacy reasons retain their prior regular-session contract; every newly
    # recognized reason requires exact native generation even in regular hours.
    if failure not in {'fixed_watch_post_receipt_warmup','exact_0B_missing'} or clock.startswith('08'):
        assert monitor.source_gap_semantics(tmp_path,now)['fixed_watch_waits']['unclassified_or_actionable_wait_count'] == 1


@pytest.mark.parametrize('damage', [None, 'late', 'generation', 'admission', 'signature',
    'venue', 'bucket', 'submitted', 'forbidden', 'reason'])
def test_native_session_rollover_wait_requires_original_generation_within_warmup(tmp_path, monkeypatch, damage):
    from src.engine.scalping import main_fixed_watch as producer
    now = monitor.stamp('2026-10-15T09:00:00.100000+09:00')
    route = producer.session_route(now.timestamp()-producer.MIN_WARMUP_SEC, '005930')
    generation = producer.generation_id(now.timestamp(),route)
    ready, reason = producer.observation_ready(dict(code='005930', watch_generation_id=generation),
                                              {}, now_epoch=now.timestamp())
    assert not ready and reason == 'session_generation_mismatch'
    admission = f"FIXED-{now.date()}-005930-{route['bucket']}-{route['route']}-0123456789ab"
    fields = dict(watch_origin='MAIN_FIXED_WATCH', watch_admission_id=admission,
        watch_generation_id=generation, source_signature='MAIN_FIXED_WATCH:'+admission,
        venue_resolution='main_fixed_watch_session_route', source_quality_reason=reason,
        venue_source_quality_status='pass', effective_venue=route['venue'], market_session_bucket=route['bucket'],
        actual_order_submitted=False, broker_order_forbidden=True)
    if damage == 'late': now += __import__('datetime').timedelta(seconds=producer.MIN_WARMUP_SEC)
    elif damage == 'generation': fields['watch_generation_id'] = '0'*64
    elif damage == 'admission': fields['watch_admission_id'] = admission.replace('2026-10-15','2026-10-14')
    elif damage == 'signature': fields['source_signature'] = 'MAIN_FIXED_WATCH:foreign'
    elif damage == 'venue': fields['effective_venue'] = 'KRX'
    elif damage == 'bucket': fields['market_session_bucket'] = 'krx_regular'
    elif damage == 'submitted': fields['actual_order_submitted'] = True
    elif damage == 'forbidden': fields['broker_order_forbidden'] = False
    elif damage == 'reason': fields['source_quality_reason'] = 'unknown_wait'
    row = dict(pipeline='ENTRY_PIPELINE', stage='main_fixed_watch_observation_wait',
               stock_code='005930', emitted_at=now.isoformat(), fields=fields)
    monkeypatch.setattr(monitor, '_recent_source_rows', lambda path,*a,**k:
        ([row] if 'pipeline_events' in str(path) else [], dict(status='complete')))
    census = monitor.source_gap_semantics(tmp_path,now)['fixed_watch_waits']
    assert census['session_boundary_wait_count'] == int(damage is None)
    assert census['unclassified_or_actionable_wait_count'] == int(damage is not None)
    assert census['native_entry_allowed_by_clock'] is True



def test_observer_large_legacy_state_is_read_and_compacted_without_losing_incidents(tmp_path,monkeypatch):
    _observer_selection_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(monitor,'PROJECT_ROOT',tmp_path)
    monkeypatch.setattr(monitor,'source_gap_semantics',lambda *a,**k:dict(
        status='gap_observed',issues={'machine_probe:source_route_conflict':1},
        examples=[],sources={},observed={},large_observation='x'*(3*1024*1024)))
    args=['--report',str(tmp_path/'missing.json'),'--source-only']
    assert monitor.main(args)==0
    state=tmp_path/'tmp/submission_bottleneck_monitor_state.json'
    report=tmp_path/'data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json'
    original=report.read_bytes(); assert len(original)>2*1024*1024
    large=json.loads(original)
    large['incidents']['historical_original'] = dict(status='recovered',last_seen=large['as_of'],
        notified_status='recovered',issues={'original_source_gap':1})
    large['last_notification_at']=large['as_of']
    state.write_text(json.dumps(large))  # Actual preceding full-report state format.
    assert monitor._load_state(state)['incidents']==large['incidents']
    assert monitor.main(args)==0
    compact=monitor._load_state(state)
    assert state.stat().st_size<16384 and report.stat().st_size>2*1024*1024
    assert compact['incidents']['historical_original']==large['incidents']['historical_original']
    assert compact['last_notification_at']==large['last_notification_at']
    assert compact['persistence_schema']=='submission_monitor_continuation_v1'
    assert compact['incidents']==json.loads(report.read_bytes())['incidents']
    assert monitor.main(args)==0  # Compact form is accepted by the next run too.


@pytest.mark.parametrize('damage',['oversize','symlink','dangling','fifo','malformed','duplicate','foreign','incidents'])
def test_observer_state_rejects_untrusted_input_without_rewriting(tmp_path,damage):
    import os
    path=tmp_path/'state.json'
    good=dict(schema=monitor.SCHEMA,incidents={})
    if damage=='oversize':path.write_bytes(b'x'*(8*1024*1024+1))
    elif damage in ('symlink','dangling'):
        target=tmp_path/'target.json'
        if damage=='symlink':target.write_text(json.dumps(good))
        path.symlink_to(target)
    elif damage=='fifo':os.mkfifo(path)
    elif damage=='malformed':path.write_text('{')
    elif damage=='duplicate':path.write_text('{"schema":"a","schema":"b"}')
    elif damage=='foreign':path.write_text(json.dumps(dict(good,schema='notifier')))
    else:path.write_text(json.dumps(dict(good,incidents=[])))
    before=path.lstat()
    with pytest.raises((OSError,ValueError)):monitor._load_state(path)
    after=path.lstat()
    assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)


def test_observer_continuation_keeps_delay_cursor_and_accepted_source_clock():
    source=dict(schema=monitor.SCHEMA,date='2026-10-15',as_of='2026-10-15T09:25:00+09:00',
        source_as_of='2026-10-15T09:20:00+09:00',incidents={'unresolved':{'status':'active'}},
        pre_submit_delay_source_cursor={'offset':12345,'generation':'original'},last_notification_at='original',
        large_observation='discarded_from_continuation_only')
    from copy import deepcopy
    original=deepcopy(source); saved=monitor._continuation_state(source)
    assert source==original
    assert all(saved[k]==source[k] for k in ('pre_submit_delay_source_cursor','incidents','source_as_of','last_notification_at'))
    assert 'large_observation' not in saved



def test_observer_state_disappearance_during_read_is_not_a_first_run(tmp_path,monkeypatch):
    path=tmp_path/'state.json';path.write_text(json.dumps(dict(schema=monitor.SCHEMA,incidents={})))
    real_read=monitor.os.read
    def removed(fd,size):
        raw=real_read(fd,size)
        path.unlink(missing_ok=True)
        return raw
    monkeypatch.setattr(monitor.os,'read',removed)
    with pytest.raises((FileNotFoundError,ValueError)):monitor._load_state(path)


@pytest.mark.parametrize('reason,historical_true', [
    ('feature_window_incomplete', 0), ('native_confirmation_not_consumed_before_expiry', 2)])
@pytest.mark.parametrize('damage', [None, 'pending', 'ready', 'wrong_reason', 'stale_source',
    'source_route', 'missing_unknown_or_true', 'current_truth'])
def test_native_incomplete_population_matches_producer_without_admission(tmp_path, reason, historical_true, damage):
    from src.engine.scalping.zero_base_probe import native_wait_result
    now = monitor.stamp('2026-10-15T10:03:38+09:00')
    row = _native_no_match_probe(now, receipt_format='dict')
    row['fields'].update(zero_base_probe_result='observation_incomplete', zero_base_probe_reason=reason)
    receipt = row['fields']['native_observation_receipt']
    receipt.update(reason='required_window_incomplete', native_source_current=True,
        selected_branch_truth={'G4': 'UNKNOWN'}, selected_pending_count=0,
        selected_ready_count=0, source_censored_count=0,
        selected_lifecycle_counts={'G4': {'TRUE': historical_true, 'FALSE': 40, 'UNKNOWN': 31}})
    assert native_wait_result(receipt, {}) == ('observation_incomplete', reason)
    if damage == 'pending': receipt['selected_pending_count'] = 1
    elif damage == 'ready': receipt['selected_ready_count'] = 1
    elif damage == 'wrong_reason': row['fields']['zero_base_probe_reason'] = 'unknown_pending'
    elif damage == 'stale_source': receipt['native_source_current'] = False
    elif damage == 'source_route': receipt['item'] = '999999_AL'
    elif damage == 'missing_unknown_or_true':
        receipt['selected_lifecycle_counts']['G4']['TRUE' if historical_true else 'UNKNOWN'] = 0
    elif damage == 'current_truth': receipt['selected_branch_truth']['G4'] = 'UNRECOGNIZED'
    before = json.dumps(row, sort_keys=True)
    observed = monitor._probe_verified_pending(row)
    assert json.dumps(row, sort_keys=True) == before
    if damage:
        assert observed is None
        return
    assert observed == dict(pending_count=0, unknown_count=31, source_censored_count=0)
    assert monitor._probe_verified_no_match(row) is False
    _source_gap_files(tmp_path, now, probes=[row])
    gap = monitor.source_gap_semantics(tmp_path, now)
    census = gap['native_pending_observations']
    assert census['verified_pending_count'] == 1 and census['unclassified_count'] == 0
    assert census['machine_admission_proven'] is False and census['pattern_no_match_proven'] is False
    assert gap['probe_route_native_no_match_counts'] == {} and gap['probe_route_assessed_counts'] == {}
    result = _observation_health_fixture()
    result['source_gap_semantics'].update(observed={'probe_results': 1, 'probe_observation_incomplete': 1},
        status='gap_observed', native_pending_observations=census, diagnostics=gap['diagnostics'],
        diagnostics_by_scope=gap['diagnostics_by_scope'], probe_route_counts=gap['probe_route_counts'],
        probe_route_source_covered_counts=gap['probe_route_source_covered_counts'])
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'warning_pending'
    assert health['full_coverage_proven'] is False


@pytest.mark.parametrize('damage', [None, 'current_pid', 'active', 'unknown_issue', 'empty_issue',
    'bad_count', 'scope', 'rule', 'birth', 'new_issue', 'bootstrap', 'pid_unverified',
    'split', 'delay', 'policy_hash', 'stale_contract'])
def test_prior_pid_delay_contract_incident_requires_current_native_proof(damage):
    result, _, _, _ = _bounded_outcome_health_fixture(partial=False)
    now = monitor.stamp(result['as_of']); birth = result['observer_generation']['actor_birth_proof']
    key = 'entry_execution_tuning_receipt_contract'
    item = dict(status='historical_unresolved', rule=key, scope='entry_split|pre_submit_delay',
        last_seen=datetime.fromtimestamp(birth['birth_lower_bound_epoch']-1,monitor.KST).isoformat(),
        issues={'pre_submit_delay_bootstrap_handoff_mismatch':1,
                'pre_submit_delay_bootstrap_env_mismatch':1}, notified_status='active')
    result['incidents'][key] = item
    execution = result['entry_execution_tuning_semantics']
    execution['bootstrap']['pid_passed'] = True
    execution['pre_submit_delay']['policy_sha256'] = 'a'*64
    if damage == 'current_pid': item['last_seen'] = now.isoformat()
    elif damage == 'active': item['status'] = 'active'
    elif damage == 'unknown_issue': item['issues'] = {'unknown_contract':1}
    elif damage == 'empty_issue': item['issues'] = {}
    elif damage == 'bad_count': item['issues']['pre_submit_delay_bootstrap_env_mismatch'] = True
    elif damage == 'scope': item['scope'] = 'unknown'
    elif damage == 'rule': item['rule'] = 'unknown'
    elif damage == 'birth': birth['boot_epoch'] += 1
    elif damage == 'new_issue': execution['issues'] = {'pre_submit_delay_bootstrap_env_mismatch':1}
    elif damage == 'bootstrap': execution['bootstrap']['status'] = 'unverified'
    elif damage == 'pid_unverified': execution['bootstrap']['pid_passed'] = False
    elif damage == 'split': execution['entry_split']['verification'] = 'unverified'
    elif damage == 'delay': execution['pre_submit_delay']['bootstrap_env_match'] = False
    elif damage == 'policy_hash': execution['pre_submit_delay']['policy_sha256'] = 'invalid'
    elif damage == 'stale_contract': execution['as_of'] = (now-timedelta(minutes=1)).isoformat()
    before = json.dumps(result,sort_keys=True)
    health = monitor.observation_health_projection(result)
    assert health['status'] == ('warning_pending' if damage is None else 'not_eligible'),health
    assert json.dumps(result,sort_keys=True) == before
    assert item['status'] == ('active' if damage == 'active' else 'historical_unresolved')
    assert health['current_observation_verified'] is False and health['runtime_effect'] is False


def _native_feature_gap_probe(now):
    row = _native_no_match_probe(now, receipt_format='dict')
    fields = row['fields']
    fields.update(zero_base_probe_result_schema='zero_base_probe_result_v2',
                  zero_base_probe_reason='required_branch_feature_missing')
    receipt = fields['native_observation_receipt']
    receipt.update(reason='required_window_incomplete', native_source_current=True,
        selected_branch_truth={'G1':'FALSE','G2':'UNKNOWN'}, selected_pending_count=0,
        source_censored_count=0, selected_lifecycle_counts={
            'G1':{'FALSE':35,'UNKNOWN':1}, 'G2':{'UNKNOWN':36}})
    fields['zero_base_branch_readiness'] = dict(
        schema='native_branch_residence_requirements_v2', status='observed',
        runtime_effect=False, decision_authority='none', scope_changed=False,
        price_basis='exact_native_trade', route='krx_nxt_integrated',
        policy_scope=receipt['selected_scope'],
        **{k:receipt[k] for k in ('item','family_sha256','scope_execution_hash','native_epoch','native_sequence')},
        branch_descriptors={
            'G1':dict(detector_truth='FALSE', feature_availability='complete',missing_inputs=[]),
            'G2':dict(detector_truth='UNKNOWN', feature_availability='incomplete',
                      missing_inputs=['ret','volume','backward_window'])})
    return row


@pytest.mark.parametrize('format', ['dict','json','literal'])
def test_required_feature_gap_keeps_source_shortfall_without_unclassified_failure(tmp_path, format):
    now=monitor.stamp('2026-10-14T16:45:00+09:00');row=_native_feature_gap_probe(now)
    for key in ('native_observation_receipt','zero_base_branch_readiness'):
        value=row['fields'][key]
        if format!='dict':row['fields'][key]=json.dumps(value) if format=='json' else repr(value)
    original=json.dumps(row,sort_keys=True)
    assert monitor._probe_verified_no_match(row) is False
    assert monitor._probe_verified_pending(row) is None
    assert monitor._probe_verified_pending(row,feature_gap=True)['unknown_count']==37
    _source_gap_files(tmp_path,now,probes=[row]);gap=monitor.source_gap_semantics(tmp_path,now)
    census=gap['native_feature_gap_observations']
    assert census['count']==census['verified_count']==1 and census['unclassified_count']==0
    assert gap['diagnostics']=={'machine_probe:required_branch_feature_missing':1}
    assert gap['probe_route_assessed_counts']==gap['probe_route_source_covered_counts']=={}
    assert gap['probe_route_native_no_match_counts']=={} and gap['native_pending_observations']['count']==0
    assert census['source_coverage_proven'] is False and census['machine_admission_proven'] is False
    assert json.dumps(row,sort_keys=True)==original


@pytest.mark.parametrize('damage', ['missing_readiness','schema','scope','item','generation','sequence',
    'branch_set','truth','missing_inputs','available','authority','source_current','pending','censored',
    'historical_true','no_unknown','pid','stale','bool_count','bool_epoch','float_sequence','oversize'])
def test_feature_gap_requires_exact_native_receipt_and_missing_branch_inputs(damage):
    now=monitor.stamp('2026-10-14T16:45:00+09:00');row=_native_feature_gap_probe(now)
    f=row['fields'];r=f['native_observation_receipt'];b=f['zero_base_branch_readiness']
    if damage=='missing_readiness':f.pop('zero_base_branch_readiness')
    elif damage=='schema':f['zero_base_probe_result_schema']='legacy'
    elif damage=='scope':b['policy_scope']='foreign'
    elif damage=='item':b['item']='005930_NX'
    elif damage=='generation':b['scope_execution_hash']='e'*64
    elif damage=='sequence':b['native_sequence']+=1
    elif damage=='branch_set':b['branch_descriptors']['foreign']=b['branch_descriptors']['G2']
    elif damage=='truth':b['branch_descriptors']['G2']['detector_truth']='FALSE'
    elif damage=='missing_inputs':b['branch_descriptors']['G2']['missing_inputs']=[]
    elif damage=='available':b['branch_descriptors']['G2']['feature_availability']='complete'
    elif damage=='authority':b['runtime_effect']=True
    elif damage=='source_current':r['native_source_current']=False
    elif damage=='pending':r['selected_pending_count']=1
    elif damage=='censored':r['source_censored_count']=1
    elif damage=='historical_true':r['selected_lifecycle_counts']['G1']['TRUE']=1
    elif damage=='no_unknown':r['selected_branch_truth']['G2']='FALSE'
    elif damage=='pid':r['process_pid']=999
    elif damage=='stale':r['observed_epoch']-=10
    elif damage=='bool_count':r['selected_lifecycle_counts']['G2']['UNKNOWN']=True
    elif damage=='bool_epoch':r['native_epoch']=1;b['native_epoch']=True
    elif damage=='float_sequence':b['native_sequence']=float(r['native_sequence'])
    elif damage=='oversize':f['zero_base_branch_readiness']='x'*65537
    assert monitor._probe_verified_pending(row,feature_gap=True) is None


@pytest.mark.parametrize('damage', [None,'count','bool_count','verified','unknown','unclassified',
    'coverage','admission','no_match','schema','missing','diagnostic'])
def test_feature_gap_health_requires_verified_census_and_never_grants_coverage(tmp_path,damage):
    result=_observation_health_fixture();now=monitor.stamp(result['as_of'])
    _source_gap_files(tmp_path,now,probes=[_native_feature_gap_probe(now)])
    actual=monitor.source_gap_semantics(tmp_path,now);gap=result['source_gap_semantics']
    for key in ('observed','diagnostics','diagnostics_by_scope','native_feature_gap_observations',
                'probe_route_counts','probe_route_assessed_counts','probe_route_source_covered_counts',
                'probe_route_native_no_match_counts'):
        gap[key]=actual[key]
    gap['status']='gap_observed';gap['sources']['probe']['recent_count']=1
    census=gap['native_feature_gap_observations']
    if damage=='count':census['count']=2
    elif damage=='bool_count':census['count']=True
    elif damage=='verified':census['verified_count']=0
    elif damage=='unknown':census['unknown_count']=0
    elif damage=='unclassified':census['unclassified_count']=1
    elif damage=='coverage':census['source_coverage_proven']=True
    elif damage=='admission':census['machine_admission_proven']=True
    elif damage=='no_match':census['pattern_no_match_proven']=True
    elif damage=='schema':census['schema']='other'
    elif damage=='missing':gap.pop('native_feature_gap_observations')
    elif damage=='diagnostic':gap['diagnostics']['machine_probe:required_branch_feature_missing']=2
    original=json.dumps(result,sort_keys=True);health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if damage is None else 'not_eligible'),health
    assert health['full_coverage_proven'] is False and health['runtime_effect'] is False
    assert json.dumps(result,sort_keys=True)==original


@pytest.mark.parametrize('signed_trades', [0, '0', 1, '1'])
@pytest.mark.parametrize('duration', [0, 0.0, -1, float('nan')])
def test_first_exact_trade_feature_gap_is_not_an_observer_contract_failure(tmp_path, duration, signed_trades):
    now = monitor.stamp('2026-10-16T14:56:50+09:00')
    row = _native_feature_gap_probe(now)
    f = row['fields']; r = f['native_observation_receipt']; b = f['zero_base_branch_readiness']
    f['zero_base_ws_signed_0b_count'] = signed_trades
    r.update(observed_seconds=duration, native_sequence=1, selected_branch_truth={'G2':'UNKNOWN'},
             selected_lifecycle_counts={'G2':{'UNKNOWN':1}})
    b.update(native_sequence=1, branch_descriptors={'G2':b['branch_descriptors']['G2']})
    proof = monitor._probe_verified_pending(row, feature_gap=True)
    assert (proof is not None) == (duration == 0)
    assert monitor._probe_verified_no_match(row) is False
    assert monitor._probe_verified_pending(row) is None
    _source_gap_files(tmp_path, now, probes=[row])
    gap = monitor.source_gap_semantics(tmp_path, now)
    assert gap['probe_route_source_covered_counts'] == {}
    assert gap['native_feature_gap_observations']['verified_count'] == int(duration == 0)
    assert gap['probe_route_assessed_counts'] == gap['probe_route_native_no_match_counts'] == {}
    assert gap['native_feature_gap_observations']['machine_admission_proven'] is False


@pytest.mark.parametrize('signed_trades', [None, -1, '-1', True, False, 0.0, '0.0', 'invalid'])
def test_feature_gap_rejects_invalid_signed_trade_count(signed_trades):
    row = _native_feature_gap_probe(monitor.stamp('2026-10-16T16:39:22+09:00'))
    if signed_trades is None:
        row['fields'].pop('zero_base_ws_signed_0b_count')
    else:
        row['fields']['zero_base_ws_signed_0b_count'] = signed_trades
    assert monitor._probe_verified_pending(row, feature_gap=True) is None


@pytest.mark.parametrize('duration', [149.5, 0, 0.0, -1, float('nan'), float('inf'), True, False])
@pytest.mark.parametrize('defect', [None, 'zero_history','current','pid','epoch','bad_counts'])
def test_history_receipt_is_separate_from_current_source_and_cannot_grant_coverage(tmp_path, defect, duration):
    now = monitor.stamp('2026-10-16T14:56:50+09:00')
    row = _native_no_match_probe(now, receipt_format='dict'); f = row['fields']; r = f['native_observation_receipt']
    f.update(zero_base_probe_result='observation_incomplete',
             zero_base_probe_reason='native_history_observed_current_source_stale')
    r.update(native_source_current=False, source_censored_count=1, observed_seconds=duration,
             selected_lifecycle_counts={'G1':{'FALSE':20},'G2':{'FALSE':10}})
    if defect == 'zero_history': r['selected_lifecycle_counts'] = {'G1':{'UNKNOWN':1},'G2':{'UNKNOWN':2}}
    if defect == 'current': r['native_source_current'] = True
    if defect == 'pid': r['process_pid'] = 999
    if defect == 'epoch': r['native_epoch'] = 0
    if defect == 'bad_counts': r['selected_lifecycle_counts']['G1']['FALSE'] = True
    valid = defect is None and type(duration) in (int, float) and duration >= 0 and duration != float('inf')
    assert (monitor._probe_verified_history(row) is not None) == valid
    assert monitor._probe_verified_no_match(row) is False
    assert monitor._probe_verified_pending(row) is None
    _source_gap_files(tmp_path, now, probes=[row]); gap = monitor.source_gap_semantics(tmp_path,now)
    assert gap['probe_route_source_covered_counts'] == {}
    assert gap['native_history_observations']['verified_count'] == int(valid)
    assert gap['native_history_observations']['current_source_coverage_proven'] is False


def test_reset_segment_history_keeps_diagnostic_without_observer_contract_failure(tmp_path):
    result = _observation_health_fixture(); now = monitor.stamp(result['as_of'])
    rows = []
    for index, (duration, known) in enumerate(((0, 4), (72.37, 6), (114.9, 5), (0, 41))):
        row = _native_no_match_probe(now, receipt_format='dict'); fields = row['fields']
        fields.update(zero_base_probe_result='observation_incomplete',
            zero_base_probe_reason='native_history_observed_current_source_stale',
            physical_probe_lease_id=f'history-{index}')
        fields['native_observation_receipt'].update(observed_seconds=duration,
            native_source_current=False, source_censored_count=int(duration == 0),
            reason='required_window_incomplete', selected_branch_truth={'G4':'UNKNOWN'},
            selected_lifecycle_counts={'G4':{'FALSE':known,'UNKNOWN':2}})
        rows.append(row)
    duplicate = json.loads(json.dumps(rows[0]))
    duplicate['fields']['evaluation_attempt_id'] = 'different-summary-label-same-native-lease'
    rows.append(duplicate)
    _source_gap_files(tmp_path, now, probes=rows)
    actual = monitor.source_gap_semantics(tmp_path, now); gap = result['source_gap_semantics']
    for key in ('observed','diagnostics','diagnostics_by_scope','native_history_observations',
                'probe_route_counts','probe_route_assessed_counts','probe_route_source_covered_counts',
                'probe_route_native_no_match_counts'):
        gap[key] = actual[key]
    gap['status'] = 'gap_observed'; gap['sources']['probe']['recent_count'] = 4
    assert gap['native_history_observations']['verified_count'] == 4
    assert gap['native_history_observations']['known_count'] == 56
    assert gap['diagnostics'] == {'machine_probe:native_history_observed_current_source_stale':4}
    assert gap['probe_route_source_covered_counts'] == gap['probe_route_native_no_match_counts'] == {}
    health = monitor.observation_health_projection(result)
    assert health['status'] == 'warning_pending', health
    assert health['unmet_conditions'] == []
    assert health['current_observation_verified'] is health['full_coverage_proven'] is False


def test_delay_signal_observation_complete_has_no_submit_terminal_requirement(tmp_path):
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor,execution_projection_identity
    day='2026-10-16';now=monitor.stamp(day+'T10:06:00+09:00')
    base=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stock_code='005930',stock_name='test',
        record_id=9,emitted_date=day)
    fields=dict(delay_intent_id='signal',anchor_kind='signal_ready',market_session_bucket='krx_regular',route='KRX_NXT_INTEGRATED')
    rows=[dict(base,stage='pre_submit_delay_committed',emitted_at=day+'T10:00:00+09:00',fields=fields)]
    for delay in (0,30,60,120,180):
        at=monitor.stamp(day+'T10:00:00+09:00')+timedelta(seconds=delay)
        rows.append(dict(base,stage='pre_submit_delay_quote_observed',emitted_at=at.isoformat(),
            fields=dict(fields,target_delay_sec=delay,quote_route='KRX_NXT_INTEGRATED',quote_valid=True)))
    raw=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    compact=tmp_path/'threshold_cycle'/f'date={day}'/'family=pre_submit_delay';compact.mkdir(parents=True)
    (compact/'part-execution-1000.jsonl').write_text(''.join(json.dumps(dict(r,family='pre_submit_delay',
        execution_source_event_sha256=execution_projection_identity(r)))+'\n' for r in rows))
    producer=ProducerSummaryCompactor(summary_dir=tmp_path/'pipeline_event_summaries',mode='shadow')
    for r in rows:producer.submit(r)
    producer.flush()
    # A selected release's data symlink is the same physical canonical source.
    alias=tmp_path/'release-data';alias.symlink_to(tmp_path,target_is_directory=True)
    result=monitor.pre_submit_delay_source_semantics(alias,now)
    assert result['sources']=={'raw':'complete','summary':'complete','compact':'complete'}
    assert result['issues']=={}
    assert result['healthy_by_scope']['intent_terminal_missing|KRX_NXT_INTEGRATED']==1
    assert result['diagnostics']['summary_bounded_projection_used']==1
    manifest=next((tmp_path/'pipeline_event_summaries').glob('*manifest*.json'))
    value=json.loads(manifest.read_text());value['recent_summary']['rows'][0]['event_count']+=1
    manifest.write_text(json.dumps(value))
    assert monitor.pre_submit_delay_source_semantics(alias,now)['sources']['summary']=='unobservable'


def test_delay_cursor_migration_waits_for_window_without_new_source_gap(tmp_path,monkeypatch):
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor
    day='2026-10-16';now=monitor.stamp(day+'T10:05:00+09:00')
    event=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stage='scalping_scanner_fast_precheck',
        stock_code='005930',record_id=1,emitted_date=day,emitted_at=day+'T10:02:00+09:00',fields={})
    raw=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir();raw.write_text(json.dumps(event)+'\n')
    writer=ProducerSummaryCompactor(summary_dir=tmp_path/'pipeline_event_summaries',mode='shadow');writer.submit(event);writer.flush()
    prior=dict(date=day,offset=raw.stat().st_size,minutes={},delay_events=[],coverage_started_at=day+'T00:00:00+09:00')
    result=monitor.pre_submit_delay_source_semantics(tmp_path,now,prior)
    assert result['sources']['raw']=='partial' and result['sources']['summary']=='complete'
    assert result['issues']=={} and result['status']=='unobservable'
    assert result['diagnostics']['raw_observation_window_pending']==1
    assert result['healthy'].get('raw_source_unobservable_with_summary',0)==0


@pytest.mark.parametrize('stage', ['scalp_trailing_mechanical_input',
    'scalping_scanner_fast_precheck', 'pre_submit_delay_quote_observed'])
def test_delay_cursor_retains_post_asof_rows_without_future_intent_effects(tmp_path, stage):
    import copy
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor
    day='2026-10-16';now=monitor.stamp(day+'T10:05:00+09:00')
    base=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stock_code='196170',
        record_id=49346,stage=stage,emitted_date=day,fields=dict(
            delay_intent_id='future-intent',target_delay_sec='invalid',quote_valid=False))
    rows=[dict(base,emitted_at=(now+timedelta(milliseconds=1)).isoformat()),
          dict(base,record_id=49347,emitted_at=(now-timedelta(seconds=2)).isoformat())]
    raw=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    writer=ProducerSummaryCompactor(summary_dir=tmp_path/'pipeline_event_summaries',mode='shadow')
    for row in rows:writer.submit(row)
    writer.flush()
    first=monitor.pre_submit_delay_source_semantics(tmp_path,now)
    assert first['cursor']['offset']==raw.stat().st_size
    assert first['diagnostics']['raw_future_events_deferred']==1
    assert sum(v['count'] for v in first['cursor']['minutes'].values())==2
    if stage=='pre_submit_delay_quote_observed':
        assert first['issues']['quote_horizon_invalid']==1  # Only the past row.
    original=copy.deepcopy(first['cursor'])
    again=monitor.pre_submit_delay_source_semantics(tmp_path,now,first['cursor'])
    assert first['cursor']==original
    assert again['cursor']['minutes']==original['minutes']
    later=monitor.pre_submit_delay_source_semantics(tmp_path,now+timedelta(minutes=3),again['cursor'])
    fresh=monitor.pre_submit_delay_source_semantics(tmp_path,now+timedelta(minutes=3))
    assert later['cursor']['minutes']==fresh['cursor']['minutes']
    assert later['cursor']['delay_events']==fresh['cursor']['delay_events']
    assert 'producer_raw_summary_window_mismatch' not in later['issues']
    if stage=='pre_submit_delay_quote_observed':assert later['issues']['quote_horizon_invalid']==2


def test_delay_cursor_partial_append_and_legacy_generation_do_not_lose_boundary(tmp_path):
    from copy import deepcopy
    day='2026-10-16';now=monitor.stamp(day+'T10:05:00+09:00')
    row=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stage='scalp_trailing_mechanical_input',
        stock_code='196170',record_id=49346,emitted_date=day,
        emitted_at=(now+timedelta(milliseconds=1)).isoformat(),fields={})
    wire=(json.dumps(row)+'\n').encode();raw=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl'
    raw.parent.mkdir();raw.write_bytes(wire[:len(wire)//2])
    first=monitor.pre_submit_delay_source_semantics(tmp_path,now)
    assert first['cursor']['offset']==0
    with raw.open('ab') as handle:handle.write(wire[len(wire)//2:])
    second=monitor.pre_submit_delay_source_semantics(tmp_path,now,first['cursor'])
    assert sum(v['count'] for v in second['cursor']['minutes'].values())==1
    legacy=deepcopy(second['cursor']);legacy.update(delay_cursor_contract_version=2,minutes={})
    migrated=monitor.pre_submit_delay_source_semantics(tmp_path,now+timedelta(seconds=1),legacy)
    assert migrated['diagnostics']['raw_cursor_contract_migrated']==1
    assert migrated['sources']['raw']=='partial'
    assert sum(v['count'] for v in migrated['cursor']['minutes'].values())==1
    replacement=raw.with_suffix('.new');replacement.write_bytes(wire.replace(b'49346',b'49347'))
    replacement.replace(raw)
    changed=monitor.pre_submit_delay_source_semantics(tmp_path,now+timedelta(seconds=1),second['cursor'])
    assert changed['sources']['raw']=='partial'
    assert sum(v['count'] for v in changed['cursor']['minutes'].values())==1


def _delay_semantic_fixture(tmp_path, *, grid=False, anchor='signal_ready', observation_only=None,
                            quote_horizons=(0,), selected=0, terminal=None, recheck=None,
                            commit_updates=None, quote_updates=None, extra_terminals=(), record_id=9, writer=None):
    """Create all three physical source paths with the same exact rows."""
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor, execution_projection_identity
    day = '2026-10-16'
    started = monitor.stamp(day + 'T10:00:00+09:00')
    base = dict(event_type='pipeline_event', pipeline='ENTRY_PIPELINE', stock_code='005930',
                stock_name='test', record_id=record_id, emitted_date=day)
    fields = dict(delay_intent_id='source-intent', anchor_kind=anchor,
                  market_session_bucket='krx_regular', route='KRX_NXT_INTEGRATED',
                  decision_committed_at_epoch=started.timestamp(), decision_source_sha256='a'*64,
                  selected_delay_sec=selected)
    if observation_only is not None:
        fields['observation_only'] = observation_only
    if grid:
        fields.update(observation_grid_version='legacy_and_short_clock_v1',
                      observation_horizons_sec=[0, 1, 3, 5, 30, 60, 120, 180],
                      observation_tolerance_sec=.25)
    fields.update(commit_updates or {})
    rows = [dict(base, stage='pre_submit_delay_committed', emitted_at=started.isoformat(), fields=fields)]
    for horizon in quote_horizons:
        quote = dict(fields, target_delay_sec=horizon, quote_valid=True,
                     quote_route='KRX_NXT_INTEGRATED', quote_observed_at_epoch=started.timestamp()+horizon,
                     quote_offset_sec=horizon)
        if horizon in (1, 3, 5):
            quote.update(quote_contract_version=2, target_due_at_epoch=started.timestamp()+horizon)
        quote.update((quote_updates or {}).get(horizon, {}))
        rows.append(dict(base, stage='pre_submit_delay_quote_observed',
                         emitted_at=(started+timedelta(seconds=horizon)).isoformat(), fields=quote))
    receipts = [('pre_submit_delay_intent_terminal', terminal),
                ('pre_submit_delay_recheck_observed', recheck)]
    receipts.extend(('pre_submit_delay_intent_terminal', row) for row in extra_terminals)
    for stage, receipt in receipts:
        if receipt is not None:
            offset, payload = receipt
            rows.append(dict(base, stage=stage,
                emitted_at=(started+timedelta(seconds=offset)).isoformat(), fields=dict(fields, **payload)))
    raw = tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl'
    raw.parent.mkdir(exist_ok=True)
    raw.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    compact = tmp_path/'threshold_cycle'/f'date={day}'/'family=pre_submit_delay'
    compact.mkdir(parents=True, exist_ok=True)
    (compact/'part-execution-1000.jsonl').write_text(''.join(json.dumps(dict(row,
        family='pre_submit_delay', execution_source_event_sha256=execution_projection_identity(row)))+'\n'
        for row in rows))
    writer = writer or ProducerSummaryCompactor(summary_dir=tmp_path/'pipeline_event_summaries', mode='shadow')
    for row in rows:
        writer.submit(row)
    writer.flush()
    return started, rows


@pytest.mark.parametrize('anchor,observation_only', [('signal_ready', None), ('price_ready', True),
                                                    ('price_ready', 'True')])
def test_delay_incomplete_observation_reports_horizons_without_order_terminal_requirement(
        tmp_path, anchor, observation_only):
    started, _ = _delay_semantic_fixture(tmp_path, anchor=anchor, observation_only=observation_only)
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert 'intent_terminal_missing' not in result['issues']
    assert result['issues']['observation_horizon_missing'] == 4
    assert result['horizon_states'] == {'missing': 4, 'observed_valid': 1}
    assert result['diagnostics']['observation_only_no_order_terminal_required'] == 1


@pytest.mark.parametrize('grid,horizons,total', [(False, (0,30,60,120,180), 5),
                                               (True, (0,1,3,5,30,60,120,180), 8)])
def test_delay_expected_horizons_are_bound_to_each_source_grid(tmp_path, grid, horizons, total):
    started, _ = _delay_semantic_fixture(tmp_path, grid=grid, quote_horizons=horizons)
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['sources'] == {'raw':'complete', 'summary':'complete', 'compact':'complete'}
    assert result['issues'] == {}
    assert result['horizon_states'] == {'observed_valid': total}
    assert result['healthy']['observation_completed'] == 1


def test_delay_short_grid_distinguishes_not_due_and_persistence_pending(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, grid=True)
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=2))
    assert result['horizon_states'] == {'not_due': 6, 'observed_valid': 1, 'persistence_pending': 1}
    assert result['issues'] == {}
    assert not any('queue_pending' in key for key in result['diagnostics'])


def test_delay_early_censor_does_not_hide_previously_overdue_horizon(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, grid=True, terminal=(61, {
        'observation_only': True, 'terminal_reason':'process_shutdown_observation_censored'}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['horizon_states'] == {'censored': 3, 'missing': 4, 'observed_valid': 1}
    assert result['issues']['observation_horizon_missing'] == 4
    assert 'intent_terminal_missing' not in result['issues']


def test_delay_observation_terminal_cannot_close_actual_armed_intent(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        quote_horizons=(0,30,60,120,180), terminal=(183, {
            'observation_only':True, 'terminal_reason':'observation_expired_without_quote'}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues']['intent_terminal_missing'] == 1
    assert result['issues']['selected_due_completion_missing'] == 1
    assert result['diagnostics']['observation_terminal_does_not_close_order_intent'] == 1


def test_delay_direct_expiry_terminal_closes_actual_intent_without_erasing_research_missing(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        terminal=(61, {'terminal_reason':'recheck_not_ready_before_expiry'}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert 'intent_terminal_missing' not in result['issues']
    assert 'selected_due_completion_missing' not in result['issues']
    assert result['issues']['observation_horizon_missing'] == 4
    assert result['horizon_states'].get('censored', 0) == 0


def test_delay_recheck_admission_is_pending_only_until_its_exact_deadline(tmp_path):
    started = monitor.stamp('2026-10-16T10:00:00+09:00')
    _, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        recheck=(31, {'recheck_status':'admitted', 'successor_request_id':'successor',
                     'due_at_epoch':started.timestamp()+30,
                     'recheck_submitted_at_epoch':started.timestamp()+31,
                     'recheck_deadline_epoch':started.timestamp()+100}))
    pending = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=70))
    assert pending['recheck_states'] == {'admitted':1}
    assert pending['diagnostics']['selected_due_recheck_pending'] == 1
    assert 'selected_due_completion_missing' not in pending['issues']
    expired = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=101))
    assert expired['issues']['selected_due_completion_missing'] == 1


@pytest.mark.parametrize("selected", [1, 3, 5])
def test_delay_short_selected_policy_keeps_due_receipt_monitoring(tmp_path, selected):
    started = monitor.stamp('2026-10-16T10:00:00+09:00')
    _delay_semantic_fixture(tmp_path, grid=True, anchor='price_ready', selected=selected,
        recheck=(selected+1, {'recheck_status': 'admitted', 'successor_request_id': 'successor',
            'due_at_epoch': started.timestamp()+selected,
            'recheck_submitted_at_epoch': started.timestamp()+selected+1,
            'recheck_deadline_epoch': started.timestamp()+100}))
    pending = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=70))
    assert pending['recheck_states'] == {'admitted': 1}
    assert pending['diagnostics']['selected_due_recheck_pending'] == 1
    assert 'selected_due_instrumentation_gap' not in pending['diagnostics']
    assert 'recheck_receipt_invalid' not in pending['issues']
    expired = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=101))
    assert expired['issues']['selected_due_completion_missing'] == 1


@pytest.mark.parametrize("status,basis,evidence", [
    ('unsupported_existing_behavior', None, 'indeterminate'),
    ('loaded', 'paired_quote_immediate', 'immediate_supported_on_observed_pairs'),
    ('loaded', 'paired_quote_holdout_immediate', 'indeterminate'),
])
def test_delay_zero_policy_evidence_is_not_source_loss(tmp_path, status, basis, evidence):
    started = monitor.stamp('2026-10-16T10:00:00+09:00')
    _delay_semantic_fixture(tmp_path, grid=True, anchor='price_ready', selected=0,
        quote_horizons=(0, 1, 3, 5, 30, 60, 120, 180),
        commit_updates={'delay_policy_status': status, 'delay_selection_basis': basis,
                        'delay_evidence_verdict': 'positive_delay_supported'},
        terminal=(2, {'terminal_reason': 'submitted', 'submit_call_outcome': 'returned_true',
                      'submit_finished_at_epoch': started.timestamp()+2}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {}
    assert result['policy_status_counts'] == {status: 1}
    assert result['policy_evidence_counts'] == {evidence: 1}
    assert result['selected_delay_counts'] == {'0': 1}
    assert result['commit_to_submit_return_sec'] == {'n': 1, 'sum_sec': 2, 'max_sec': 2}


def test_delay_wrong_parent_terminal_cannot_satisfy_intent(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        quote_horizons=(0,30,60,120,180), terminal=(61, {
            'decision_source_sha256':'b'*64, 'terminal_reason':'recheck_not_ready_before_expiry'}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues']['intent_decision_binding_invalid'] == 1
    assert result['issues']['intent_terminal_missing'] == 1


def test_delay_unknown_grid_does_not_invent_new_horizon_expectations(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, grid=True, quote_horizons=(0,),
        commit_updates={'observation_grid_version':'future_unrecognized_grid'})
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues']['observation_grid_contract_invalid'] == 1
    assert 'observation_horizon_missing' not in result['issues']
    assert 'zero_second_quote_missing' not in result['issues']
    assert result['horizon_states'] == {}


def test_delay_recorded_invalid_short_contract_is_not_called_absent(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, grid=True,
        quote_horizons=(0,1,3,5,30,60,120,180), quote_updates={1:{'quote_contract_version':1}})
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {'short_quote_contract_invalid':1}
    assert result['horizon_states'] == {'observed_invalid':1, 'observed_valid':7}


def test_delay_late_short_quote_cannot_claim_valid_clock(tmp_path):
    started = monitor.stamp('2026-10-16T10:00:00+09:00')
    _delay_semantic_fixture(tmp_path, grid=True, quote_horizons=(0,1,3,5,30,60,120,180),
        quote_updates={1:{'quote_observed_at_epoch':started.timestamp()+1.251, 'quote_offset_sec':1.251}})
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {'quote_clock_validity_conflict':1}
    assert result['horizon_states'] == {'observed_late_or_early':1, 'observed_valid':7}


@pytest.mark.parametrize('outcome', ['broker_accepted', 'returned_true', 'returned_false', 'returned_other', 'raised'])
def test_delay_legacy_submit_outcome_is_an_actual_terminal_receipt(tmp_path, outcome):
    started, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        quote_horizons=(0,30,60,120,180), terminal=(61, {'submit_call_outcome':outcome}))
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {}
    assert result['healthy']['intent_terminal_missing'] == 1


def test_delay_short_clock_accepts_real_producer_offset_precision(tmp_path):
    started = monitor.stamp('2026-10-16T10:00:00+09:00')
    _delay_semantic_fixture(tmp_path, grid=True, quote_horizons=(0,1,3,5,30,60,120,180),
        quote_updates={3:{'quote_observed_at_epoch':started.timestamp()+3.23456,
                          'actual_offset_sec':3.235}})
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {}
    assert result['horizon_states'] == {'observed_valid':8}


def test_delay_duplicate_actual_terminals_are_visible_without_losing_either_receipt(tmp_path):
    started, _ = _delay_semantic_fixture(tmp_path, anchor='price_ready', selected=30,
        quote_horizons=(0,30,60,120,180), terminal=(61, {'submit_call_outcome':'returned_false'}),
        extra_terminals=[(62, {'terminal_reason':'recheck_not_ready_before_expiry'})])
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['issues'] == {'intent_terminal_duplicate':1}
    assert sum(row['stage'] == 'pre_submit_delay_intent_terminal'
               for row in result['cursor']['delay_events']) == 2


def _old_scanner_observation(now, birth, actor):
    from src.engine.scalping.ai_decision_trace import _json_bytes
    at=datetime.fromtimestamp(birth-60,monitor.KST).isoformat()
    row=dict(schema='mechanistic_entry_observation_v1', evaluation_role='main_live',
        captured_at=at, scanner_promotion_id='ZBPROM-exact', bundle_sha256='a'*64,
        label_context=dict(scanner_promotion_id='ZBPROM-exact',evaluation_attempt_id='aims-old',
            stock_code='376300',effective_venue='PREMARKET_KRX_LIKE',session_bucket='premarket_krx_like'),
        runtime_consumption=dict(pid=8,process_start_ticks='800',consumed_at=at,bundle_sha256='a'*64),
        source=dict(assessment={'action':'ENTER_NOW','original_missing_receipt':True}))
    row['machine_observation_sha256']=hashlib.sha256(_json_bytes(row)).hexdigest()
    return row


@pytest.mark.parametrize('damage',[None,'hash','actor','start','at','date','scope','rule','count','missing',
    'unknown','duplicate','promotion','new_issue','birth','oversize','conflicting_native'])
@pytest.mark.parametrize('coverage_order',['none','first','last'])
@pytest.mark.parametrize('notification_pending', [False, True])
def test_historical_scanner_health_requires_all_exact_original_evidence(damage,coverage_order,notification_pending):
    from src.engine.scalping.ai_decision_trace import _json_bytes
    if coverage_order=='none':
        result,_,_,_=_bounded_outcome_health_fixture(partial=False)
    else:
        result,gap=_derived_coverage_health_fixture()
    now=monitor.stamp(result['as_of']);generation=result['observer_generation']
    birth=generation['actor_birth_proof']['birth_lower_bound_epoch']
    actor=generation['actor_birth_proof']['actor']
    row=_old_scanner_observation(now,birth,actor)
    identity=monitor._scanner_observation_identity(row);scope='|'.join(identity.split('|')[-3:])
    rule='economic_producer_gap';key=hashlib.sha256(f'{scope}|{rule}'.encode()).hexdigest()[:24]
    item=dict(scope=scope,rule=rule,category='structural_evidence',status='active',
        first_seen=row['captured_at'],last_seen=now.isoformat(),count=1,evidence_ids=[identity],
        notified_status='active',examples=[{'economic_source':{'status':'source_gap'}}])
    result['incidents'][key]=item
    if notification_pending:
        result['notification_pending'].append(key)
    evidence={identity:row};result['machine_semantics']['historical_scanner_observations']=evidence
    if damage=='hash':row['machine_observation_sha256']='f'*64
    elif damage=='actor':row['runtime_consumption'].update(pid=actor[0],process_start_ticks=actor[1])
    elif damage=='start':row['runtime_consumption']['process_start_ticks']=str(int(actor[1])+1)
    elif damage=='at':row['captured_at']=now.isoformat()
    elif damage=='date':row['captured_at']=(now-timedelta(days=1)).isoformat()
    elif damage=='scope':item['scope']='unknown'
    elif damage=='rule':item['rule']='unknown'
    elif damage=='count':item['count']=True
    elif damage=='missing':evidence.clear()
    elif damage=='unknown':result['incidents']['unknown']=result['incidents'].pop(key)
    elif damage=='duplicate':item['evidence_ids']*=2;item['count']=2
    elif damage=='promotion':row['label_context']['scanner_promotion_id']='other'
    elif damage=='new_issue':result['incidents']['new']={**item,'rule':'unknown'}
    elif damage=='birth':generation['actor_birth_proof']['boot_epoch']+=1
    elif damage=='oversize':row['extra']='x'*(128*1024)
    elif damage=='conflicting_native':row['runtime_consumption']['continuous_reversal']={'pid':9}
    if damage not in (None,'hash'):
        row['machine_observation_sha256']=hashlib.sha256(_json_bytes({k:v for k,v in row.items()
            if k!='machine_observation_sha256'})).hexdigest()
    if coverage_order=='last':result['incidents']=dict(reversed(list(result['incidents'].items())))
    before=json.dumps(result,sort_keys=True)
    health=monitor.observation_health_projection(result)
    assert health['status']==('warning_pending' if damage is None else 'not_eligible'),health
    assert json.dumps(result,sort_keys=True)==before
    assert item['status']=='active' and item['examples'][0]['economic_source']['status']=='source_gap'
    assert health['runtime_effect'] is False and health['full_coverage_proven'] is False
    if coverage_order!='none':
        assert gap['issues']=={'machine_probe:coverage_degraded:krx_nxt_integrated':1}
        assert result['notification_pending']==['machine_auxiliary_intraday_source_gap'] + ([key] if notification_pending else [])
        assert result['incidents']['machine_auxiliary_intraday_source_gap']['status']=='active'


def test_machine_reader_preserves_exact_old_scanner_bytes_across_bounded_tail(tmp_path,monkeypatch):
    observation,write=semantic_fixture(tmp_path,monkeypatch)
    now=START+timedelta(hours=1)
    row=_old_scanner_observation(now,START.timestamp()+60,['9','900'])
    identity=monitor._scanner_observation_identity(row);write(row)
    path=tmp_path/'ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl'
    original=json.loads(path.read_bytes())
    result=monitor.machine_semantics(tmp_path,now,incident_evidence_ids=[identity])
    assert result['observation_count']==0
    assert result['historical_scanner_observations']=={identity:original}
    state={'schema':monitor.SCHEMA,'incidents':{}}
    monitor.attach_machine_semantics(state,result)
    cached=monitor._continuation_state(state)['historical_scanner_observations']
    # The immutable original evidence survives ordinary bounded-tail expiry.
    write(observation)
    result=monitor.machine_semantics(tmp_path,now,incident_evidence_ids=[identity],
        historical_scanner_observations=cached)
    assert result['historical_scanner_observations']=={identity:original}
    # A second native observation with the same exact key but changed bytes
    # cannot replace or silently supersede the preserved original.
    row['source']['assessment']['action']='BLOCK';write(row)
    result=monitor.machine_semantics(tmp_path,now,incident_evidence_ids=[identity],
        historical_scanner_observations=cached)
    assert result['historical_scanner_observations']=={}
    assert cached=={identity:original}
    assert result['historical_scanner_conflicts']==[identity]
    result=monitor.machine_semantics(tmp_path,now,incident_evidence_ids=[identity],
        historical_scanner_observations={},historical_scanner_conflicts=[identity])
    assert result['historical_scanner_observations']=={}


@pytest.mark.parametrize('damage',[None,'provider','order','clock','snapshot','pid','attempt','hash',
    'action','capture','authority','kind','missing_safety','future_snapshot'])
def test_preprovider_input_deadline_is_diagnostic_only_with_exact_safe_terminal(tmp_path,damage):
    now=START
    row=dict(schema='ai_decision_trace_v1',decision_ts=now.isoformat(),decision_stage='entry_screen',
        machine_evaluation_status='assessment_contract_invalid',
        machine_contract_error='entry_machine_input_deadline_expired',
        decision_evaluation_status='not_evaluated_provider_or_preflight',
        result_source='mechanistic_pre_adjudication_rejected',action='DROP',
        reason='mechanistic_input_contract_invalid',provider_called=False,actual_order_submitted=False,
        runtime_effect=False,allowed_runtime_apply=False,broker_order_forbidden=True,
        machine_observation_sha256=None,request_capture_status='missing',
        async_producer_pid=9,async_producer_start_ticks='900',async_request_id='exact-async',
        evaluation_attempt_id='exact-attempt',decision_trace_id='exact-trace',
        effective_venue='KRX',session_bucket='krx_regular',market_data_route='krx_nxt_integrated',
        machine_bundle_sha256='a'*64,async_origin_deadline_epoch=now.timestamp()-5,
        input_source_clock_captured_at=(now-timedelta(seconds=10)).isoformat())
    if damage=='provider':row['provider_called']=True
    elif damage=='order':row['actual_order_submitted']=True
    elif damage=='clock':row['async_origin_deadline_epoch']=now.timestamp()+1
    elif damage=='snapshot':row.pop('input_source_clock_captured_at')
    elif damage=='pid':row.pop('async_producer_start_ticks')
    elif damage=='attempt':row.pop('evaluation_attempt_id')
    elif damage=='hash':row['machine_bundle_sha256']='bad'
    elif damage=='action':row['action']='BUY'
    elif damage=='capture':row['machine_observation_sha256']='b'*64
    elif damage=='authority':row['runtime_effect']=True
    elif damage=='kind':row['machine_source_gap_kind']='source_route_conflict'
    elif damage=='missing_safety':row.pop('broker_order_forbidden')
    elif damage=='future_snapshot':row['input_source_clock_captured_at']=(now+timedelta(seconds=1)).isoformat()
    assert bool(monitor._entry_input_deadline_guard(row))==(damage is None)
    _source_gap_files(tmp_path,now,traces=[row])
    result=monitor.source_gap_semantics(tmp_path,now)
    key='machine_trace:'+row.get('machine_source_gap_kind','entry_machine_input_deadline_expired')
    assert result['diagnostics'].get(key,0)==int(damage is None)
    assert result['issues'].get(key,0)==int(damage is not None)


@pytest.mark.parametrize('key', [{}, [], None, True, 'unknown_new_incident'])
def test_pending_notification_unknown_or_malformed_key_remains_actionable(key):
    result,*_=_bounded_outcome_health_fixture(partial=False)
    result['notification_pending']=[key]
    assert monitor.observation_health_projection(result)['status']=='not_eligible'


@pytest.mark.parametrize('format', ['dict','json','literal'])
def test_native_feature_gap_false_branch_with_missing_features_is_verified(tmp_path, format):
    from src.engine.scalping.zero_base_probe import native_wait_result
    now = monitor.stamp('2026-10-21T08:32:48+09:00')
    row = _native_feature_gap_probe(now)
    f = row['fields']; receipt = f['native_observation_receipt']
    readiness = f['zero_base_branch_readiness']
    readiness['branch_descriptors']['G1'].update(feature_availability='incomplete',
        missing_inputs=['ret', 'backward_window'])
    assert native_wait_result(receipt, readiness) == (
        'required_feature_insufficient', 'required_branch_feature_missing')
    for key in ('native_observation_receipt', 'zero_base_branch_readiness'):
        value = f[key]
        if format != 'dict': f[key] = json.dumps(value) if format == 'json' else repr(value)
    before = json.dumps(row, sort_keys=True)
    assert monitor._probe_verified_pending(row, feature_gap=True)['unknown_count'] == 37
    _source_gap_files(tmp_path, now, probes=[row])
    gap = monitor.source_gap_semantics(tmp_path, now)
    census = gap['native_feature_gap_observations']
    assert census['count'] == census['verified_count'] == 1 and census['unclassified_count'] == 0
    assert not census['source_coverage_proven'] and not census['machine_admission_proven']
    assert gap['probe_route_assessed_counts'] == gap['probe_route_source_covered_counts'] == {}
    assert json.dumps(row, sort_keys=True) == before


@pytest.mark.parametrize("reason", ["entry_split_probe_first_deferred", "main_entry_order_route_invalid"])
@pytest.mark.parametrize("tamper", [None, "missing_reason", "unknown_reason", "accepted", "raised", "parent", "schema", "call", "record", "before", "other_call", "missing_record", "conflicting_finish", "duplicate"])
def test_call_local_terminal_reason_reaches_monitor_without_inventing_old_outcomes(tamper, reason):
    from dataclasses import replace
    fields = dict(entry_submit_attempt_id="call-one", entry_submit_attempt_schema="call_local_submit_attempt_v1",
        entry_submit_attempt_authority="observation_only", entry_submit_attempt_parent_promotion_id="parent-1",
        entry_submit_attempt_broker_accepted=False, entry_submit_attempt_return_outcome="returned_false",
        entry_submit_attempt_terminal_schema="call_local_terminal_v1",
        entry_submit_attempt_terminal_reason=reason,
        submit_call_outcome="returned_false", submit_call_return_outcome="returned_false", submit_call_broker_accepted=False)
    if tamper == "missing_reason": fields.pop("entry_submit_attempt_terminal_reason")
    if tamper == "unknown_reason": fields["entry_submit_attempt_terminal_reason"] = "unknown_guard"
    if tamper == "accepted": fields["entry_submit_attempt_broker_accepted"] = True
    if tamper == "raised": fields["submit_call_return_outcome"] = "raised"
    if tamper == "parent": fields["entry_submit_attempt_parent_promotion_id"] = "parent-foreign"
    if tamper == "schema": fields["entry_submit_attempt_terminal_schema"] = "unverified"
    if tamper == "call": fields["entry_submit_attempt_id"] = "call-foreign"
    decision = event(1, entry_submit_attempt_id="call-one")
    terminal = event(1, stage="entry_submit_attempt_finished", when=START + timedelta(seconds=1), **fields)
    if tamper == "missing_record": terminal = replace(terminal, record_id="")
    if tamper == "record": terminal = replace(terminal, record_id="foreign-record")
    if tamper == "before": terminal = replace(terminal, emitted_at=START - timedelta(seconds=1))
    # Exercise the actual source cache parser, not only the classification helper.
    cached = sentinel._payload_to_cache_row(dict(event_type="pipeline_event", emitted_at=terminal.emitted_at.isoformat(),
        pipeline=terminal.pipeline, stage=terminal.stage, stock_name=terminal.stock_name,
        stock_code=terminal.stock_code, record_id=terminal.record_id, fields=terminal.fields))
    terminal = replace(terminal, fields=cached["fields"])
    rows = [decision, terminal]
    if tamper == "other_call": rows.append(event(1, stage="latency_pass", entry_submit_attempt_id="unresolved-call"))
    if tamper in {"conflicting_finish", "duplicate"}:
        duplicate = replace(terminal, fields=dict(terminal.fields))
        if tamper == "conflicting_finish": duplicate.fields['entry_submit_attempt_terminal_schema'] = 'unknown'
        rows.append(duplicate)
    valid = tamper in {None, "duplicate"}
    row = monitor.snapshot(rows, START + timedelta(seconds=2))["rows"][0]
    assert row["final_guard_blocked"] is valid
    assert row["broker_acceptance_observed"] is False
    if valid:
        assert row["final_state"] == "final_guard_blocked"
        assert row["final_guard_evidence"][0]["reason"] == reason
    else:
        assert row["final_state"] not in {"final_guard_blocked", "broker_rejected", "submit_pipeline_reached"}


@pytest.mark.parametrize("reason", ["entry_split_probe_first_deferred", "main_entry_order_route_invalid"])
def test_submit_return_site_to_native_logger_cache_and_monitor(monkeypatch, reason):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.monitoring.entry_attempt_identity import bind_submit_attempt_machine_lineage, observe_submit_attempt
    stock = {'id': 1, 'code': '005930', 'name': 'fixture', 'strategy': 'SCALPING', 'scanner_promotion_id': 'parent-1'}
    receipt = dict(event(1).fields, entry_ai_screen_pass=True)
    events = []
    def emit(*args, **kwargs):
        payload = dict(event_type='pipeline_event', emitted_at=(START + timedelta(seconds=len(events))).isoformat(),
            pipeline=args[0], stage=args[3], stock_name=args[1], stock_code=args[2], record_id=kwargs['record_id'], fields=kwargs['fields'])
        cached = sentinel._payload_to_cache_row(payload)
        events.append(sentinel._event_from_cache_row(cached))
    monkeypatch.setattr(handlers, 'emit_pipeline_event', emit)
    for name in ('_remember_scanner_terminal_block', 'observe_candidate_transition_safe',
                 '_maybe_register_rising_missed_nxt_downstream_block_sampler'):
        monkeypatch.setattr(handlers, name, lambda *a, **kw: None)
    @observe_submit_attempt(on_finish=handlers._observe_entry_submit_finished)
    def run(stock, code):
        assert bind_submit_attempt_machine_lineage(stock, code, receipt)
        handlers._log_entry_pipeline(stock, code, 'latency_pass')
        handlers._set_async_terminal(stock, reason)
        return False
    assert run(stock, stock['code']) is False
    assert [e.stage for e in events] == ['latency_pass', 'entry_submit_attempt_finished']
    row = monitor.snapshot(events, START + timedelta(seconds=3))['rows'][0]
    assert row['final_state'] == 'final_guard_blocked'
    assert row['final_guard_evidence'][0]['reason'] == reason
    assert row['broker_acceptance_observed'] is False
    assert '_async_consumption_guard' not in stock


def test_nonterminal_machine_rows_do_not_read_new_terminal_payload():
    class NonterminalFields(dict):
        def get(self, key, default=None):
            if key == 'entry_submit_attempt_terminal_reason':
                pytest.fail('nonterminal payload decoded for unrelated submit completion')
            return super().get(key, default)
    from dataclasses import replace
    decision = event(1)
    decision = replace(decision, fields=NonterminalFields(decision.fields))
    result = sentinel._machine_primary_entry_funnel([decision])
    assert result['evaluation_ledger'][0]['final_state'] == 'pending'


@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('damage', [None, 'raw_changed', 'index_stale', 'missing_clock', 'budget'])
def test_lineage_native_index_reads_exact_entry_rows_outside_large_irrelevant_suffix(tmp_path, monkeypatch, damage, legacy):
    from src.engine.automation import main_trailing_source_store as store
    from pathlib import Path
    if legacy or damage == 'raw_changed':
        project = store.project
        def original_projection(*args):
            value = project(*args)
            if value is not None:value.pop('lineage_projection_version', None)
            return value
        monkeypatch.setattr(store, 'project', original_projection)
    now, observations, requests, traces, write = _current_provider_lineage_fixture(tmp_path, verdicts=('PASS',))
    trace = traces[0]
    trace['decision_stage'] = 'entry_screen'
    if damage == 'missing_clock':
        trace.pop('decision_ts')
    path = tmp_path/'ai_decision_trace'/f'ai_decision_trace_{now.date()}.jsonl'
    path.parent.mkdir(exist_ok=True);path.write_bytes(b'')
    def append(value):
        before = store.signature(path.stat());raw = json.dumps(value).encode()+b'\n'
        with path.open('ab') as stream:stream.write(raw)
        assert store.record_append(tmp_path,path,before=before,after=store.signature(path.stat()),raw=raw,row=value)
    append(trace)
    # A large holding row displaces a valid entry trace from the bounded tail.
    append(dict(schema='ai_decision_trace_v1',decision_stage='holding_screen',
        decision_ts=now.isoformat(),padding='x'*32768))
    if damage == 'index_stale':
        with path.open('ab') as stream:stream.write(b'{}\n')
    elif damage == 'raw_changed':
        # Keep the native index identity pinned so the exact-byte check, rather
        # than only metadata, must detect the mismatched original line.
        generation = store.generation(tmp_path,path)
        original_signature = store.signature
        with path.open('r+b') as stream:stream.write(b'!')
        monkeypatch.setattr(store,'signature',lambda metadata:generation['source_stat'])
        monkeypatch.setattr(store,'generation',lambda *a:generation)
    original_open = Path.open;reads=[]
    class ObservedStream:
        def __init__(self,stream):self.stream=stream
        def __getattr__(self,key):return getattr(self.stream,key)
        def __enter__(self):self.stream.__enter__();return self
        def __exit__(self,*args):return self.stream.__exit__(*args)
        def read(self,size=-1):
            assert size >= 0
            value=self.stream.read(size);reads.append(len(value));return value
    def observed_open(candidate,*args,**kwargs):
        stream=original_open(candidate,*args,**kwargs)
        return ObservedStream(stream) if candidate==path else stream
    monkeypatch.setattr(Path,'open',observed_open)
    budget = 100 if damage == 'budget' else 16384
    joined=monitor._reversal_provider_lineage(tmp_path,now,observations,tail_bytes=budget,pid_identity=(123,'456'))
    source=joined['source_windows']['traces']
    assert sum(reads) <= budget
    if damage:
        assert source['status'] != 'complete' and joined['status'] != 'observed'
        return
    assert joined['source_gaps'] == joined['issues'] == {}, joined
    assert joined['trace_attempt_count'] == joined['raw_response_observed_count'] == 1
    assert source['coverage_basis']=='native_index_projection_or_exact_raw_offset_size_sha256'
    assert source['window_covered'] is True and source['read_count']==int(legacy)
    assert source['bytes_read']+source['index_bytes_read'] <= budget
    assert source['bytes_read'] < path.stat().st_size/2


@pytest.mark.parametrize('cumulative', [False, True])
@pytest.mark.parametrize('damage', [None, 'no_breach', 'ready', 'predicate_missing', 'source',
    'epoch', 'scope', 'registration', 'route', 'bundle', 'branch_phase', 'late'])
def test_registered_native_first_hold_breach_is_diagnostic_only(tmp_path, monkeypatch, cumulative, damage):
    from copy import deepcopy
    from src.engine.scalping import reversal_extended_runtime as B
    from src.engine.scalping import reversal_current_backend as dispatch
    from src.engine.scalping import reversal_source_diagnostics as source
    from src.engine.scalping.reversal_extended_state import State
    from src.engine.scalping.reversal_path_catalog import cell_key
    from src.tests.test_reversal_manual_registration import bid_for, hold_rows
    from src.tests.test_reversal_path_policy import row
    bid = 'manual_cumulative_a2a227bdaaad838d381a774c' if cumulative else bid_for('other_non_fixed', 'FIRST_HOLD3')
    symbol = '034020' if cumulative else '000001'
    values = hold_rows()
    for tick in values:
        if cumulative: tick[3:6] = [x*59000/99.5 for x in tick[3:6]]
        tick[9] = symbol+'_NX'
    state = State(branch_ids=[bid], session_anchor=values[0], generation='a'*64)
    for tick in values: state.observe(tick, symbol=symbol, venue='NXT', session='NXT_PREMARKET')
    assert state.ready
    at = values[-1][0]; day = datetime.fromtimestamp(at, B.K.KST).date().isoformat()
    cell = cell_key(symbol, 'PRE', values[-1][3])
    monkeypatch.setattr(B, '_STATES', {(symbol,'NXT',symbol+'_NX','PRE',day,cell):state})
    monkeypatch.setattr(B, '_CLAIMS', {})
    monkeypatch.setattr(B, '_GENERATION', 'f'*64)
    monkeypatch.setattr(B, '_FAMILY', dict(family_sha256='f'*64,
        machine_cells={cell:dict(routes={'NXT':dict(scope_execution_hash='a'*64)})}))
    monkeypatch.setattr(dispatch, 'backend', lambda *args:B)
    monkeypatch.setattr(source.time, 'time', lambda:at)
    claim = source.claim_snapshot_with_receipt(symbol,'NXT','NXT_PREMARKET',now=at,
        item=symbol+'_NX',family_sha256='f'*64)
    assert claim
    # The actual native owner retires the held signal when its floor breaks.
    price = 58999 if cumulative else 99.49
    update = row(126,price); update[9]=symbol+'_NX'
    state.observe(update,symbol=symbol,venue='NXT',session='NXT_PREMARKET')
    monkeypatch.setattr(source.time, 'time', lambda:at+1)
    with pytest.raises(ValueError) as error:
        source.validate_claim_with_receipt(claim,'f'*64,now=at+1,
            evaluation_attempt_id='aims-held',machine_bundle_sha256='b'*64)
    assert str(error.value)=='reversal_signal_path_changed'
    receipt=deepcopy(error.value.reversal_source_receipt)
    trace=dict(schema='ai_decision_trace_v1',stock_code=symbol,decision_trace_id='held-trace',
        decision_ts=B.K.iso(at+1.01),decision_stage='entry_screen',provider_called=False,
        actual_order_submitted=False,machine_evaluation_status='assessment_contract_invalid',
        market_data_route='nxt_only',evaluation_attempt_id='aims-held',machine_bundle_sha256='b'*64,
        machine_contract_error='reversal_signal_path_changed',continuous_reversal_rejected_claim_receipt=receipt)
    if damage=='no_breach':receipt['latest_native_observation'][3]=values[-1][3]
    elif damage=='ready':receipt['registered_signal_ready']=True
    elif damage=='predicate_missing':receipt['native_predicates'].pop('first_signal_turn_matches')
    elif damage=='source':receipt['latest_native_observation'][8]=0
    elif damage=='epoch':receipt['latest_native_observation'][1]+=1
    elif damage=='scope':receipt['scope'][0]='foreign'
    elif damage=='registration':receipt['source_registration_receipt']['sha256']='c'*64
    elif damage=='route':trace['market_data_route']='krx_only'
    elif damage=='bundle':trace['machine_bundle_sha256']='c'*64
    elif damage=='branch_phase':next(iter(receipt['snapshot'][0]['branch_signals'].values()))['decision_phase']='FIRST_UPTICK'
    elif damage=='late':receipt['state_observed_epoch']+=10
    _source_gap_files(tmp_path,datetime.fromtimestamp(at+1.1,B.K.KST),traces=[trace])
    before=deepcopy(trace)
    result=monitor.source_gap_semantics(tmp_path,datetime.fromtimestamp(at+1.1,B.K.KST))
    assert result['issues']==({} if damage is None else {'machine_trace:reversal_signal_path_changed':1})
    if damage is None:
        assert result['diagnostics']=={'machine_trace:reversal_first_price_hold_invalidated':1}
    assert trace==before
