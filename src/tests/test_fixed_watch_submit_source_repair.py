"""Fixed-watch admission, exact capture and TTL regression; no live I/O."""
from copy import deepcopy
import os
from datetime import datetime

import pytest

from src.engine.monitoring.entry_attempt_identity import (
    bind_submit_attempt_machine_lineage, observe_submit_attempt,
    submit_attempt_fields, submit_attempt_machine_lineage,
)
from src.engine import sniper_state_handlers as H


def fixed():
    stock = dict(id=49145, code='403870', watch_origin='MAIN_FIXED_WATCH',
        watch_admission_id='FIXED-2026-10-07-403870-krx_regular-krx_nxt_integrated-da1360cf1587',
        watch_generation_id='d'*64, effective_venue='KRX', market_session_bucket='krx_regular')
    receipt = dict(stock, entry_primary_decision_owner='mechanistic_entry_adjudicator',
        evaluation_attempt_id='aims-db4c7c4b25e038b01f63', policy_bundle_hash='b'*64,
        entry_mechanistic_action='ENTER_NOW', entry_ai_screen_status='pass', entry_ai_screen_pass=True,
        machine_capture_status='captured', machine_observation_sha256='a'*64,
        continuous_reversal_applied=True)
    return stock, receipt


def test_fixed_watch_pass_reaches_sizing_without_scanner_identity():
    from src.engine.scalping.entry_execution_sizing_plan import compose_entry_execution_sizing_plan
    from src.tests.test_entry_execution_sizing_plan import _priced
    stock, receipt = fixed()
    original = deepcopy(stock)
    @observe_submit_attempt
    def run(stock, code):
        assert bind_submit_attempt_machine_lineage(stock, code, receipt)
        bound = submit_attempt_machine_lineage(stock, code)
        orders, fields = compose_entry_execution_sizing_plan(
            [_priced(dict(qty=10, price=10000))], expected_total_qty=10,
            action_receipt=bound, quantity_policy_version='initial-v2', split_policy_version='initial-v2')
        assert fields['entry_execution_sizing_valid']
        assert sum(order['qty'] for order in orders) == 10
        plan = fields['entry_execution_sizing_plan']
        assert plan['watch_admission_id'] == stock['watch_admission_id']
        assert plan['machine_observation_sha256'] == 'a'*64
        fields = submit_attempt_fields(stock, code)
        assert 'scanner_promotion_id' not in fields
        assert 'entry_submit_attempt_parent_promotion_id' not in fields
        assert fields['entry_submit_attempt_parent_watch_generation_id'] == 'd'*64
        return False
    assert run(stock, '403870') is False
    assert stock == original
    assert submit_attempt_machine_lineage(stock, '403870') == {}


@pytest.mark.parametrize('key,value', [
    ('watch_origin', 'SCANNER'), ('watch_admission_id', 'FIXED-other'),
    ('watch_generation_id', 'e'*64), ('watch_generation_id', None),
    ('effective_venue', 'NXT'), ('market_session_bucket', 'nxt'),
    ('machine_capture_status', 'write_failed'), ('machine_observation_sha256', None),
    ('scanner_promotion_id', 'SCANPROM-other'), ('entry_ai_screen_pass', False),
    ('policy_bundle_hash', None), ('evaluation_attempt_id', None),
])
def test_fixed_watch_rejects_incomplete_or_foreign_parent(key, value):
    stock, receipt = fixed()
    receipt[key] = value
    @observe_submit_attempt
    def run(stock, code):
        assert not bind_submit_attempt_machine_lineage(stock, code, receipt)
        assert not submit_attempt_machine_lineage(stock, code)
    run(stock, '403870')


def test_fixed_watch_retry_cannot_borrow_prior_pass_or_changed_admission():
    stock, receipt = fixed()
    @observe_submit_attempt
    def run(stock, code):
        assert bind_submit_attempt_machine_lineage(stock, code, receipt)
        assert not bind_submit_attempt_machine_lineage(stock, code, {}, replace_existing=True)
        assert not submit_attempt_machine_lineage(stock, code)
        assert bind_submit_attempt_machine_lineage(stock, code, receipt, replace_existing=True)
        stock['watch_generation_id'] = 'e'*64
        assert not bind_submit_attempt_machine_lineage(stock, code, receipt, replace_existing=True)
        assert not submit_attempt_machine_lineage(stock, code)
    run(stock, '403870')


def test_fixed_watch_capture_projection_retains_native_parent_and_revision():
    _, receipt = fixed()
    projected = H._machine_primary_entry_provenance_fields(receipt)
    for key in ('watch_origin', 'watch_admission_id', 'watch_generation_id', 'machine_observation_sha256'):
        assert projected[key] == receipt[key]


@pytest.mark.parametrize('age,blocked', [(2.999, False), (3.0, False), (4.867, True), (10.097, True)])
def test_continuous_reversal_authority_uses_existing_three_second_probe_ttl(monkeypatch, age, blocked):
    monkeypatch.setenv('KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED', 'true')
    monkeypatch.setenv('KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE', 'DAILY')
    monkeypatch.setenv('KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC', '3')
    monkeypatch.setattr(H.time, 'time', lambda: 1000.)
    stock, receipt = fixed()
    stock.update(strategy='SCALPING', last_watching_ai_machine_primary_fields=receipt,
        last_watching_ai_confirmed_at=1000.-age, last_watching_ai_action='BUY',
        last_watching_ai_result_source='live', last_watching_ai_score=80,
        last_watching_ai_decision_trace_id='trace', last_watching_ai_attempt_decision_trace_id='trace',
        last_watching_ai_attempt_trusted=True)
    result = H._entry_ai_submit_authority_fields(strategy='SCALPING', stock=stock,
        latency_gate=dict(ai_action='BUY', ai_score=80, ai_result_source='live'), latency_signal_score=80)
    assert result['blocked'] is blocked
    assert result['entry_ai_submit_authority_max_prior_age_sec'] == '3.0'
    if blocked:
        assert result['entry_ai_submit_authority_reason'] == 'entry_ai_result_stale_or_untrusted'


def test_fixed_watch_machine_revision_rejects_rearmed_generation():
    stock, receipt = fixed()
    stock['_machine_observation_revision'] = dict(digest='a'*64,
        key=[stock['watch_admission_id'], receipt['evaluation_attempt_id'], '403870',
             'KRX', 'krx_regular', 'b'*64, os.getpid()])
    assert H._machine_submit_revision_is_current(stock, receipt)
    stock['watch_generation_id'] = 'e'*64
    assert not H._machine_submit_revision_is_current(stock, receipt)


@pytest.mark.parametrize('index,value', [(2, '005930'), (3, 'NXT'), (4, 'nxt'), (5, 'c'*64), (6, -1)])
def test_fixed_watch_revision_rejects_foreign_symbol_route_bundle_pid(index, value):
    stock, receipt = fixed()
    key = [stock['watch_admission_id'], receipt['evaluation_attempt_id'], '403870',
           'KRX', 'krx_regular', 'b'*64, os.getpid()]
    key[index] = value
    stock['_machine_observation_revision'] = dict(key=key, digest='a'*64)
    assert not H._machine_submit_revision_is_current(stock, receipt)


def test_real_retry_has_new_evaluation_and_timeout_clears_previous_pass(monkeypatch):
    stock, receipt = fixed()
    stock['name'] = 'HPSP'
    stock['strategy'] = 'SCALPING'
    monkeypatch.setattr(H.time, 'time', lambda: 1000.)
    monkeypatch.setattr(H, '_consume_entry_price_exact_context_handoff', lambda *a, **k: (dict(
        ws_data={'curr':10000, 'evaluation_attempt_id':'old-evaluation'}, recent_ticks=[],
        recent_candles=[], candle_context={'ai_market_snapshot_v1':{'evaluation_attempt_id':'old-evaluation'}}), {}))
    monkeypatch.setattr(H, '_extract_ai_overlap_snapshot', lambda *a, **k: {})
    class TimeoutAI:
        def analyze_target(self, name, ws, *args, **kwargs):
            new_id = ws['evaluation_attempt_id']
            assert new_id.startswith('submit-retry-')
            assert kwargs['metadata_extra']['evaluation_attempt_id'] == new_id
            assert kwargs['candle_context']['ai_market_snapshot_v1']['evaluation_attempt_id'] == new_id
            raise TimeoutError('controlled provider timeout')
    @observe_submit_attempt
    def run(stock, code):
        assert bind_submit_attempt_machine_lineage(stock, code, receipt)
        result = H._retry_entry_ai_submit_authority_before_block(stock=stock, code=code,
            ws_data={}, ai_engine=TimeoutAI(), now_ts=1000., current_ai_score=80.)
        assert result['pre_submit_entry_ai_authority_retry_attempted']
        assert not result['pre_submit_entry_ai_authority_retry_success']
        assert submit_attempt_machine_lineage(stock, code) == {}
    run(stock, '403870')


@pytest.mark.parametrize('gap,expected', [(False, 'ready'), (True, 'warmup_after_source_stale_or_invalid')])
def test_diagnostics_never_change_kernel_event_or_auxiliary_input(monkeypatch, gap, expected):
    from src.engine.scalping import continuous_reversal as K
    from src.engine.scalping.reversal_source_diagnostics import project
    from src.tests.test_continuous_reversal import rows
    seq=rows([100]* (100 if gap else 120) + [99,100])
    if gap:seq[60][8]=0
    state=K.ReversalState()
    for row in seq:state.observe(row,symbol='036930',venue='SOR',session='SOR_REGULAR')
    snap=state.snapshot();original=deepcopy(snap)
    now=seq[-1][0]
    key=('036930','SOR','036930_AL','REGULAR',datetime.fromtimestamp(now,K.KST).date())
    monkeypatch.setattr(K,'_STATES',{key:state})
    result=project(snap,symbol='036930',venue='SOR',session='SOR_REGULAR',now=now,item='036930_AL')
    assert result['volume_ratio_source_status']==expected
    assert result['volume_ratio_observed_seconds']==(40 if gap else 121)
    assert snap==original
    assert result['runtime_effect'] is False
    exact=dict(observed_epoch=snap[0]['epoch'], item='036930_AL', transport_epoch=seq[-1][1],
               route_sequence=seq[-1][2], market_source_latency={'packet_to_normalization_ms':12})
    measured=project(snap,symbol='036930',venue='SOR',session='SOR_REGULAR',now=now,
                     item='036930_AL',envelope=exact)
    assert measured['source_latency']==exact['market_source_latency']
    exact['route_sequence'] += 1
    foreign=project(snap,symbol='036930',venue='SOR',session='SOR_REGULAR',now=now,
                    item='036930_AL',envelope=exact)
    assert 'source_latency' not in foreign
    assert snap==original
    wrong=project(snap,symbol='005930',venue='SOR',session='SOR_REGULAR',now=now,item='036930_AL')
    assert wrong['reason']=='reversal_revision_changed'


def _native_reversal_claim(monkeypatch):
    from src.engine.scalping import continuous_reversal_branches as B
    from src.tests.test_continuous_reversal import rows
    monkeypatch.setattr(B, '_STATES', {})
    monkeypatch.setattr(B, '_CLAIMS', {})
    monkeypatch.setattr(B, '_GENERATION', 'f'*64)
    monkeypatch.setattr(B, '_V2', True)
    values = rows([100, 99, 100])
    for row in values:
        row[0] += 1791344100.
        row[9] = '403870_AL'
    state = B.BranchState(session_anchor=values[0])
    for row in values:
        state.observe(row, symbol='403870', venue='SOR', session='SOR_REGULAR')
    day = datetime.fromtimestamp(values[-1][0], B.K.KST).date().isoformat()
    B._STATES[('403870', 'SOR', '403870_AL', 'REGULAR', day)] = state
    claim = B.claim_snapshot('403870', 'SOR', 'SOR_REGULAR', now=values[-1][0],
                             item='403870_AL', family_sha256='f'*64)
    return B, state, values, claim


@pytest.mark.parametrize('version', ['v5', 'v6'])
@pytest.mark.parametrize('case,expected', [
    ('down', 'reversal_first_signal_invalidated'),
    ('expire', 'reversal_signal_expired'),
    ('epoch', None), ('invalid_source', None), ('bad_quote', None),
])
def test_operating_claim_lifecycle_requires_exact_cell_and_intact_source(monkeypatch, tmp_path, version, case, expected):
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_source_diagnostics as DIAG
    from src.engine.scalping import reversal_extended_runtime as V6
    from src.engine.scalping import reversal_operating_runtime as V5
    from src.engine.scalping import reversal_extended_state as E
    from src.engine.scalping.reversal_path_catalog import cell_key
    from src.tests.test_reversal_path_policy import row
    from src.engine.monitoring.submission_bottleneck_monitor import _reversal_lifecycle_diagnostic, source_gap_semantics
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files
    B = V6 if version == 'v6' else V5
    values = [row(i, 100) for i in range(121)] + [row(121, 99), row(122, 100)]
    for r in values:
        r[9] = '403870_AL'
    state = E.State(branch_ids=['legacy_dd5_ge_0_4_v1'], generation='a'*64)
    for r in values:
        state.observe(r, symbol='403870', venue='SOR', session='SOR_REGULAR')
    at = values[-1][0]
    day = datetime.fromtimestamp(at, B.K.KST).date().isoformat()
    cell = cell_key('403870', 'REGULAR', 100)
    key = ('403870', 'SOR', '403870_AL', 'REGULAR', day, cell)
    monkeypatch.setattr(B, '_STATES', {key: state})
    monkeypatch.setattr(B, '_CLAIMS', {})
    monkeypatch.setattr(B, '_GENERATION', 'f'*64)
    monkeypatch.setattr(B, '_FAMILY', dict(family_sha256='f'*64,
        machine_cells={cell: dict(routes={'SOR': dict(scope_execution_hash='a'*64)})}))
    monkeypatch.setattr(D, 'backend', lambda *args: B)
    monkeypatch.setattr(DIAG.time, 'time', lambda: at)
    claim = DIAG.claim_snapshot_with_receipt('403870', 'SOR', 'SOR_REGULAR',
        now=at, item='403870_AL', family_sha256='f'*64)
    assert claim and claim['backend'] == 'operating_'+version
    now = at + (6 if case == 'expire' else 1)
    if case == 'expire':
        for offset in range(123, 128):
            tick = row(offset, 100)
            tick[9] = '403870_AL'
            state.observe(tick, symbol='403870', venue='SOR', session='SOR_REGULAR')
    update = row(128 if case == 'expire' else 123, 99)
    update[9] = '403870_AL'
    if case == 'epoch': update[1] += 1
    if case == 'invalid_source': update[8] = 0
    if case == 'bad_quote': update[4:6] = [101, 99]
    state.observe(update, symbol='403870', venue='SOR', session='SOR_REGULAR')
    monkeypatch.setattr(DIAG.time, 'time', lambda: now)
    before = deepcopy((claim, B._CLAIMS))
    with pytest.raises(ValueError) as native:
        B.validate_claim(claim, 'f'*64, now=now)
    with pytest.raises(ValueError) as measured:
        DIAG.validate_claim_with_receipt(claim, 'f'*64, now=now,
            evaluation_attempt_id='attempt-operating', machine_bundle_sha256='b'*64)
    assert str(native.value) == str(measured.value)
    assert (claim, B._CLAIMS) == before
    receipt = measured.value.reversal_source_receipt
    trace = dict(stock_code='403870', decision_ts=B.K.iso(now+.01),
        decision_stage='entry_screen', machine_evaluation_status='assessment_contract_invalid',
        market_data_route='krx_nxt_integrated', evaluation_attempt_id='attempt-operating',
        machine_bundle_sha256='b'*64, machine_contract_error=str(measured.value),
        provider_called=False, continuous_reversal_rejected_claim_receipt=receipt)
    assert _reversal_lifecycle_diagnostic(trace) == expected
    clock = datetime.fromtimestamp(now+.1, B.K.KST)
    _source_gap_files(tmp_path, clock, traces=[trace])
    result = source_gap_semantics(tmp_path, clock)
    assert result['issues'] == ({} if expected else {'machine_trace:'+str(native.value): 1})
    if expected:
        assert result['diagnostics'] == {'machine_trace:'+expected: 1}
        for field in ('stored_envelope_family_sha256', 'state_generation',
                      'active_scope_execution_hash', 'source_registration_receipt',
                      'active_generation', 'snapshot_sha256'):
            broken = dict(receipt, **{field: None})
            assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=broken)) is None
        for field, value in [('state_observed_epoch', now+6), ('price_path_segment_start', now),
                             ('scope', ['foreign']), ('claim_token', 'c'*64)]:
            broken = dict(receipt, **{field: value})
            assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=broken)) is None
        # Old receipts cannot prove the separate cell-to-family binding.
        old = dict(receipt, schema='continuous_reversal_claim_source_receipt_v3')
        assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=old)) is None


@pytest.mark.parametrize('case,cause,lifecycle', [
    ('expire', 'reversal_signal_expired', True),
    ('down', 'reversal_first_signal_invalidated', True),
    ('tamper', 'reversal_signal_snapshot_changed', False),
    ('future', 'reversal_signal_clock_invalid', False),
    ('epoch', 'reversal_first_signal_invalidated', False),
    ('invalid_source', 'reversal_first_signal_invalidated', False),
])
def test_rejected_claim_preserves_guard_and_exact_source(monkeypatch, tmp_path, case, cause, lifecycle):
    from src.engine.scalping.reversal_source_diagnostics import validate_claim_with_receipt
    from src.engine.monitoring.submission_bottleneck_monitor import _reversal_lifecycle_diagnostic
    B, state, values, claim = _native_reversal_claim(monkeypatch)
    now = values[-1][0] + (6 if case == 'expire' else -1 if case == 'future' else 1)
    monkeypatch.setattr('src.engine.scalping.reversal_source_diagnostics.time.time', lambda: now)
    row = values[-1][:]
    row[0] = now
    row[2] += 1
    if case in {'down', 'epoch', 'invalid_source'}:
        row[3] = 98.
    if case == 'epoch':
        row[1] += 1
    if case == 'invalid_source':
        row[8] = 0
    if case != 'future':
        state.observe(row, symbol='403870', venue='SOR', session='SOR_REGULAR')
    if case == 'tamper':
        claim['snapshot'][0]['low_price'] += 1
    before = deepcopy((B._STATES, B._CLAIMS, claim))
    with pytest.raises(ValueError) as baseline:
        B.validate_claim(claim, 'f'*64, now=now)
    with pytest.raises(ValueError) as instrumented:
        validate_claim_with_receipt(claim, 'f'*64, now=now,
                                   evaluation_attempt_id='attempt-exact', machine_bundle_sha256='b'*64)
    assert str(instrumented.value) == str(baseline.value)
    receipt = instrumented.value.reversal_source_receipt
    assert receipt['state_observed_epoch'] == now
    assert receipt['failure_cause'] == cause
    assert receipt['snapshot'] == before[1][claim['token']]['snapshot']
    assert B._CLAIMS == before[1] and claim == before[2]
    assert receipt['latest_native_observation'] == state.legacy.last
    trace_row = dict(stock_code='403870', decision_ts=B.K.iso(now+.01),
        decision_stage='entry_screen', machine_evaluation_status='assessment_contract_invalid',
        market_data_route='krx_nxt_integrated',
        evaluation_attempt_id='attempt-exact', machine_bundle_sha256='b'*64,
        machine_contract_error=str(instrumented.value), provider_called=False,
        continuous_reversal_rejected_claim_receipt=receipt)
    assert _reversal_lifecycle_diagnostic(trace_row) == (cause if lifecycle else None)
    legacy = dict(receipt, schema='continuous_reversal_claim_source_receipt_v1')
    legacy.pop('state_observed_epoch')
    assert _reversal_lifecycle_diagnostic(dict(trace_row,
        continuous_reversal_rejected_claim_receipt=legacy)) == (cause if lifecycle else None)
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files
    from src.engine.monitoring.submission_bottleneck_monitor import source_gap_semantics
    clock = datetime.fromtimestamp(now+.1, B.K.KST)
    _source_gap_files(tmp_path, clock, traces=[trace_row])
    result = source_gap_semantics(tmp_path, clock)
    if lifecycle:
        assert result['issues'] == {}
        assert result['diagnostics'] == {'machine_trace:'+cause: 1}
    else:
        assert result['issues'] == {'machine_trace:'+str(baseline.value): 1}
    for key, value in [('evaluation_attempt_id', 'foreign'), ('provider_called', True),
                       ('machine_bundle_sha256', 'other'), ('stock_code', '005930')]:
        foreign = dict(trace_row, **{key: value})
        assert _reversal_lifecycle_diagnostic(foreign) is None
    assert _reversal_lifecycle_diagnostic({**trace_row,
        'continuous_reversal_rejected_claim_receipt': None}) is None


def test_claim_clock_records_state_after_lock_without_changing_guard(monkeypatch):
    from src.engine.scalping.reversal_source_diagnostics import validate_claim_with_receipt
    from src.engine.monitoring.submission_bottleneck_monitor import _reversal_lifecycle_diagnostic
    B, state, values, claim = _native_reversal_claim(monkeypatch)
    decision_at = values[-1][0] + .112
    row = values[-1][:]
    row[0] = decision_at + .015724
    row[2] += 1
    row[3] = 98.
    state.observe(row, symbol='403870', venue='SOR', session='SOR_REGULAR')
    observed_at = decision_at + .02
    monkeypatch.setattr('src.engine.scalping.reversal_source_diagnostics.time.time', lambda: observed_at)
    with pytest.raises(ValueError) as baseline:
        B.validate_claim(claim, 'f'*64, now=decision_at)
    with pytest.raises(ValueError) as measured:
        validate_claim_with_receipt(claim, 'f'*64, now=decision_at,
            evaluation_attempt_id='clock-race', machine_bundle_sha256='b'*64)
    assert str(baseline.value) == str(measured.value) == 'reversal_first_signal_invalidated'
    receipt = measured.value.reversal_source_receipt
    assert receipt['validation_epoch'] == decision_at
    assert receipt['state_observed_epoch'] == observed_at
    assert receipt['signal_age_seconds'] == decision_at-claim['snapshot'][0]['epoch']
    trace = dict(stock_code='403870', decision_ts=B.K.iso(observed_at+.01),
        evaluation_attempt_id='clock-race', machine_bundle_sha256='b'*64,
        market_data_route='krx_nxt_integrated', provider_called=False,
        machine_contract_error=str(measured.value), continuous_reversal_rejected_claim_receipt=receipt)
    assert _reversal_lifecycle_diagnostic(trace) == 'reversal_first_signal_invalidated'
    # Old receipts without an independently measured state clock stay unresolved.
    legacy = dict(receipt, schema='continuous_reversal_claim_source_receipt_v1')
    legacy.pop('state_observed_epoch')
    assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=legacy)) is None
    for invalid in [decision_at-.01, row[0]-.001, observed_at+.1, float('nan'), None]:
        corrupt = dict(receipt, state_observed_epoch=invalid)
        assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=corrupt)) is None
    missing = dict(receipt)
    missing.pop('state_observed_epoch')
    assert _reversal_lifecycle_diagnostic(dict(trace, continuous_reversal_rejected_claim_receipt=missing)) is None


def test_claim_telemetry_never_changes_success_or_native_generation_rejection(monkeypatch):
    from src.engine.scalping.reversal_source_diagnostics import validate_claim_with_receipt
    B, state, values, claim = _native_reversal_claim(monkeypatch)
    now = values[-1][0]
    assert validate_claim_with_receipt(claim, 'f'*64, now=now) == B.validate_claim(claim, 'f'*64, now=now)
    claim['generation'] = 'foreign'
    claim['snapshot'][0]['epoch'] = float('nan')
    with pytest.raises(ValueError, match='reversal_signal_generation_changed') as error:
        validate_claim_with_receipt(claim, 'f'*64, now=now)
    assert error.value.reversal_source_receipt['status'] == 'unobservable'


@pytest.mark.parametrize('damage', [None, 'missing_registration', 'registration_hash',
    'active_generation', 'snapshot', 'scope', 'scope_session', 'scope_date',
    'registration_clock', 'unexpired', 'source_invalid'])
def test_registered_claim_expiry_retains_native_rejection_and_exact_source(monkeypatch, tmp_path, damage):
    from src.engine.scalping import reversal_source_diagnostics as D
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic, source_gap_semantics)
    B, state, values, baseline = _native_reversal_claim(monkeypatch)
    native_claims = deepcopy(B._CLAIMS)
    def state_values():
        return deepcopy((state.legacy.rows, state.legacy.turn, state.legacy.segment_start, state.ready, state.counts))
    native_state_values = state_values()
    B._CLAIMS.clear()
    at = values[-1][0]
    monkeypatch.setattr(D.time, 'time', lambda: at)
    claim = D.claim_snapshot_with_receipt('403870', 'SOR', 'SOR_REGULAR', now=at,
        item='403870_AL', family_sha256='f'*64)
    assert {k:v for k,v in claim.items() if k!='source_registration_receipt'} == baseline
    assert B._CLAIMS == native_claims and state_values() == native_state_values
    assert B.validate_claim(claim, 'f'*64, now=at) == B.validate_claim(baseline, 'f'*64, now=at)
    now = at + (4 if damage == 'unexpired' else 6)
    # Exercise native cleanup, which removes expired registered claims even
    # when an unrelated scope is checked. Unexpired disappearance is unexplained.
    if damage == 'unexpired':
        B._CLAIMS.pop(claim['token'])
    else:
        assert B.claim_snapshot('005930', 'SOR', 'SOR_REGULAR', now=now,
            item='005930_AL', family_sha256='f'*64) is None
    assert claim['token'] not in B._CLAIMS
    if damage == 'missing_registration':
        claim.pop('source_registration_receipt')
    elif damage == 'registration_hash':
        claim['source_registration_receipt']['sha256'] = 'corrupt'
    elif damage == 'active_generation':
        B._GENERATION = 'changed'
    elif damage == 'snapshot':
        claim['snapshot'][0]['low_price'] += 1
    elif damage in {'scope', 'scope_session', 'scope_date', 'registration_clock'}:
        proof = claim['source_registration_receipt']
        if damage == 'scope': proof['scope'][0] = '005930'
        elif damage == 'scope_session': proof['scope'][3] = 'AFTER'
        elif damage == 'scope_date': proof['scope'][4] = '2026-10-06'
        else: proof['observed_epoch'] = now+1
        proof['sha256'] = B.digest({k:v for k,v in proof.items() if k!='sha256'})
    latest = values[-1][:]
    latest[0] = now; latest[2] += 1
    if damage == 'source_invalid': latest[8] = 0
    state.observe(latest, symbol='403870', venue='SOR', session='SOR_REGULAR')
    monkeypatch.setattr(D.time, 'time', lambda: now)
    with pytest.raises(ValueError, match='reversal_signal_generation_changed') as original:
        B.validate_claim(claim, 'f'*64, now=now)
    with pytest.raises(ValueError, match='reversal_signal_generation_changed') as measured:
        D.validate_claim_with_receipt(claim, 'f'*64, now=now,
            evaluation_attempt_id='registered-expiry', machine_bundle_sha256='b'*64)
    assert str(measured.value) == str(original.value)
    receipt = measured.value.reversal_source_receipt
    assert receipt['registered_claim_present'] is False and receipt['snapshot'] is None
    assert receipt['supplied_snapshot'] == claim['snapshot']
    row = dict(stock_code='403870', decision_ts=B.K.iso(now+.01),
        decision_stage='entry_screen', machine_evaluation_status='assessment_contract_invalid',
        evaluation_attempt_id='registered-expiry', machine_bundle_sha256='b'*64,
        market_data_route='krx_nxt_integrated', provider_called=False,
        machine_contract_error=str(measured.value), continuous_reversal_rejected_claim_receipt=receipt)
    expected = 'reversal_signal_expired' if damage is None else None
    assert _reversal_lifecycle_diagnostic(row) == expected
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files
    clock = datetime.fromtimestamp(now+.1, B.K.KST)
    _source_gap_files(tmp_path, clock, traces=[row])
    result = source_gap_semantics(tmp_path, clock)
    if damage is None:
        assert result['issues'] == {} and result['diagnostics'] == {'machine_trace:reversal_signal_expired': 1}
    else:
        assert result['issues'] == {'machine_trace:reversal_signal_generation_changed': 1}


def test_registration_telemetry_failure_preserves_native_admission(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as D
    B, _, values, original = _native_reversal_claim(monkeypatch)
    registered = deepcopy(B._CLAIMS)
    B._CLAIMS.clear()
    monkeypatch.setattr(D.time, 'time', lambda: float('nan'))
    claim = D.claim_snapshot_with_receipt('403870', 'SOR', 'SOR_REGULAR', now=values[-1][0],
        item='403870_AL', family_sha256='f'*64)
    assert {k:v for k,v in claim.items() if k!='source_registration_receipt'} == original
    assert B._CLAIMS == registered
    assert claim['source_registration_receipt']['status'] == 'unobservable'
    assert D.verified_registration(claim, claim['source_registration_receipt']) is None
    assert B.validate_claim(claim, 'f'*64, now=values[-1][0]) == B.validate_claim(original, 'f'*64, now=values[-1][0])
