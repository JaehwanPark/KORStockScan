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
