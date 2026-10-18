"""Main stop pure decisions, real producer adapters and committed consumers."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import pytest
from src.engine.scalping import main_stop_policy as p
from src.engine.scalping import main_stop_replay as r
from src.engine.automation import main_stop_postclose as post
from src.engine.scalping.position_peak_ledger import PositionPeakRuntimeLedger, position_cycle_id
from src.tests.test_main_stop_runtime_source import evaluation_stream


def replay_scenario(source, *args, **kwargs):
    return r.replay(evaluation_stream(source), *args, **kwargs)


def holding_scenario(source):
    return r.holding_contracts(evaluation_stream(source))


def test_retired_pyramid_cannot_create_or_replace_a_protect_line():
    from src.engine.sniper_execution_receipts import _apply_scale_in_protection
    before = dict(buy_price=10000, trailing_stop_price=10050, protect_profit_pct=.2,
        soft_stop_micro_grace_started_at=100, soft_stop_micro_grace_extension_used=True)
    retired = dict(before)
    assert _apply_scale_in_protection(retired, 'PYRAMID') is False
    assert retired == before
    average = dict(before)
    assert _apply_scale_in_protection(average, 'AVG_DOWN') is True
    assert average['trailing_stop_price'] == before['trailing_stop_price']
    assert average['protect_profit_pct'] == before['protect_profit_pct']
    assert 'soft_stop_micro_grace_started_at' not in average
    assert average['soft_stop_reset_after_avg_down'] is True
    assert p.protect_line_origin({}) == 'not_applicable_no_active_line'
    assert p.protect_line_origin(dict(before, manual_control_exclusion_blocked=True)) == 'manual_existing'
    assert p.protect_line_origin(dict(before, pyramid_count=1)) == 'legacy_retired'
    assert p.protect_line_origin(before) == 'unverified_existing'


@pytest.mark.parametrize('namespace', ['ai_decision_payloads', 'ai_decision_prompts', 'ai_decision_requests'])
def test_vote_watch_ignores_unused_compression_companion_but_detects_source_changes(tmp_path, namespace):
    import gzip
    directory=tmp_path/namespace;directory.mkdir()
    raw=directory/(namespace+'_2026-10-08.jsonl');raw.write_bytes(b'{"source":1}\n')
    before=post.vote_watch(tmp_path,'2026-10-12')
    compressed=raw.with_suffix('.jsonl.gz')
    compressed.write_bytes(gzip.compress(b'{"unused":2}\n'))
    assert post.vote_watch(tmp_path,'2026-10-12')==before
    raw.write_bytes(b'{"source":3,"changed":true}\n')
    changed=post.vote_watch(tmp_path,'2026-10-12')
    assert changed!=before
    raw.unlink()
    compressed_only=post.vote_watch(tmp_path,'2026-10-12')
    assert compressed_only!=changed
    compressed.write_bytes(gzip.compress(b'{"source":4}\n'))
    assert post.vote_watch(tmp_path,'2026-10-12')!=compressed_only


def test_vote_watch_does_not_hide_gzip_behind_foreign_symlink(tmp_path):
    import gzip
    directory=tmp_path/'ai_decision_payloads';directory.mkdir()
    foreign=tmp_path/'foreign.jsonl';foreign.write_bytes(b'{}\n')
    raw=directory/'ai_decision_payloads_2026-10-08.jsonl';raw.symlink_to(foreign)
    before=post.vote_watch(tmp_path,'2026-10-12')
    raw.with_suffix('.jsonl.gz').write_bytes(gzip.compress(b'{}\n'))
    assert post.vote_watch(tmp_path,'2026-10-12')!=before


@pytest.mark.parametrize('namespace', ['ai_decision_payloads', 'ai_decision_prompts', 'ai_decision_requests'])
def test_native_stop_accepts_only_sealed_lossless_compression(tmp_path, namespace):
    import gzip
    folder=tmp_path/namespace;folder.mkdir()
    raw=folder/(namespace+'_2026-10-08.jsonl');content=b'{"original":1}\n'
    raw.write_bytes(content)
    _, report, _, _=publication(tmp_path)
    compressed=raw.with_suffix('.jsonl.gz')
    compressed.write_bytes(gzip.compress(content));raw.unlink()
    assert post.vote_watch(tmp_path,'2026-10-12') != report['vote_watch_sha256']
    assert post.read_committed(tmp_path,'2026-10-12')[1] == report
    assert post.read_committed(tmp_path,'2026-10-12',verify_full=True)[1] == report
    assert post.handoff(tmp_path,'2026-10-13')[1]['status'] == 'verified_carried'
    compressed.write_bytes(gzip.compress(b'{"original":2}\n'))
    with pytest.raises(ValueError,match='compressed_content_changed'):
        post.read_committed(tmp_path,'2026-10-12')


def test_compression_binding_keeps_missing_new_and_replaced_sources_invalid(tmp_path):
    import gzip
    folder=tmp_path/'ai_decision_requests';folder.mkdir()
    raw=folder/'ai_decision_requests_2026-10-08.jsonl';content=b'{}\n'
    raw.write_bytes(content);binding=post.capture_vote_watch_binding(tmp_path,'2026-10-12')
    new=folder/'ai_decision_requests_2026-10-09.jsonl';new.write_bytes(content)
    with pytest.raises(ValueError,match='source_set_changed'):
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',binding)


    new.unlink();replacement=folder/'replace';replacement.write_bytes(content);replacement.replace(raw)
    with pytest.raises(ValueError,match='source_set_changed'):
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',binding)
    raw.unlink()
    with pytest.raises(ValueError,match='source_set_changed'):
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',binding)
    raw.with_suffix('.jsonl.gz').write_bytes(gzip.compress(content))
    post.verify_vote_watch_binding(tmp_path,'2026-10-12',binding)
    raw.symlink_to(raw.with_suffix('.jsonl.gz'))
    with pytest.raises(ValueError,match='source_set_changed'):
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',binding)


@pytest.mark.parametrize('damage', ['truncated', 'expanded'])
def test_native_stop_rejects_invalid_or_expanded_compressed_source(tmp_path, damage):
    import gzip
    folder=tmp_path/'ai_decision_requests';folder.mkdir()
    raw=folder/'ai_decision_requests_2026-10-08.jsonl';raw.write_bytes(b'{}\n')
    publication(tmp_path)
    compressed=raw.with_suffix('.jsonl.gz')
    compressed.write_bytes(gzip.compress(b'{}\n')[:-2] if damage == 'truncated' else gzip.compress(b'{}\n'*100))
    raw.unlink()
    with pytest.raises(ValueError,match='compressed_content_(invalid|changed)'):
        post.read_committed(tmp_path,'2026-10-12')


def test_holding_request_index_and_watch_share_original_compression_contract(tmp_path):
    import gzip
    from src.engine.ai.holding_vote_replay_source import _request_index
    namespaces={'ai_decision_payloads':('request_envelope_sha256','payload'),
        'ai_decision_prompts':('prompt_sha256','prompt'),
        'ai_decision_requests':('request_id','request')}
    raws=[]
    for namespace,(key,identity) in namespaces.items():
        directory=tmp_path/namespace;directory.mkdir()
        raw=directory/(namespace+'_2026-10-08.jsonl')
        raw.write_text(json.dumps({'endpoint':'holding_path_vote',key:identity})+'\n')
        raws.append(raw)
    output=tmp_path/'index';output.mkdir();sources={}
    db=_request_index(tmp_path,output,'2026-10-08',sources)
    assert db.execute('SELECT count(*) FROM original').fetchone()[0]==3;db.close()
    before=post.vote_watch(tmp_path,'2026-10-12')
    for raw in raws:
        raw.with_suffix('.jsonl.gz').write_bytes(gzip.compress(b'{"endpoint":"holding_path_vote","request_id":"unused"}\n'))
    assert post.vote_watch(tmp_path,'2026-10-12')==before
    db=_request_index(tmp_path,output,'2026-10-08',sources)
    assert db.execute('SELECT count(*) FROM original').fetchone()[0]==3;db.close()
    assert set(sources)=={str(path) for path in raws}
    raws[-1].unlink()
    assert post.vote_watch(tmp_path,'2026-10-12')!=before
    with pytest.raises(ValueError,match='holding_request_index_stale'):
        _request_index(tmp_path,output,'2026-10-08',sources)


def baseline():
    return p.StopValues(-3.,60,20,8,3,.67,1.,-5.,-4.,-2.,-.3)


def seal(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True))
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def rows(base=1791766800., record=1):
    value=baseline();stock=dict(id=record,code='005930',strategy='SCALPING',position_tag='SCANNER',buy_price=10000.,buy_qty=10)
    stock['main_stop_policy_pin']=p.pin(position_key=position_cycle_id(stock),role='SCANNER',market='REGULAR',target='2026-10-12',baseline=value)
    for n in range(9):
        bid=9990 if n<2 else 9650 if n<6 else 9580
        yield p.source_row(stock,at=base+n,bid=bid,bid_qty=100,
            decision_profit_pct=round((bid*10*.999-100000-10)/100000*100,2),
            quote=dict(market_route='krx_nxt_integrated',item='005930_AL',transport_epoch=1,observed_epoch=base+n),
            coverage_complete=True,automatic_management_allowed=True,
            runtime_flags=dict(grace_enabled=True,protect_enabled=True,handoff_enabled=False,vote_max_worsen_pct=.8),cost_model=dict(buy_cost_krw=10.,sell_cost_rate=.001,known_at=base-10,source_sha256='a'*64),vote_source=None)


def reseal(row):
    row['source_sha256'] = p.digest({k:v for k,v in row.items() if k != 'source_sha256'})
    return row


@pytest.mark.parametrize('zone', ['+09:00', '+00:00', 'Z'])
def test_native_cost_iso_replays_identically_without_mutating_source(zone):
    from datetime import datetime, timezone, timedelta
    import copy
    source = list(rows())
    expected = replay_scenario(source, replace(baseline(), grace_sec=0))
    for row in source:
        epoch = row['cost_model']['known_at']
        tz = timezone(timedelta(hours=9)) if zone == '+09:00' else timezone.utc
        row['cost_model']['known_at'] = datetime.fromtimestamp(epoch, tz).isoformat()
        if zone == 'Z':
            row['cost_model']['known_at'] = row['cost_model']['known_at'].replace('+00:00', 'Z')
        row['cost_model']['actual_broker_cost'] = False
        reseal(row)
    frozen = copy.deepcopy(source)
    actual=replay_scenario(source, replace(baseline(), grace_sec=0))
    actual_start=actual.pop('comparison_start');expected_start=expected.pop('comparison_start')
    assert actual==expected
    assert actual_start['source_sha256']==source[0]['source_sha256']
    assert actual_start['source_sha256']!=expected_start['source_sha256']
    assert {k:v for k,v in actual_start.items() if k!='source_sha256'}=={k:v for k,v in expected_start.items() if k!='source_sha256'}
    assert source == frozen
    source[0]['cost_model']['known_at'] = source[0]['cost_model']['known_at'].replace('2026', '2025')
    assert replay_scenario(source, baseline())['reason'] == 'quote_source_invalid'


@pytest.mark.parametrize('clock', [True, False, None, '', 'bad', '1791766790',
    '2026-10-12T09:00:00', -1, 0, '2100-01-01T00:00:00+09:00'])
def test_invalid_or_future_cost_clock_stays_source_gap(clock):
    source = list(rows())
    source[0]['cost_model']['known_at'] = clock
    reseal(source[0])
    result = replay_scenario(source, baseline())
    assert result['reason'] == 'cost_model_source_missing'
    assert result['modeled_net_krw'] is None


def test_nonfinite_cost_clock_is_not_a_source():
    for clock in (float('nan'), float('inf'), float('-inf')):
        assert r.cost_known_epoch(clock) is None


def preset_sources(profits=(-.2, -1.42), *, grace=0, emergency=-2.4, handoff=True):
    stock = dict(id=99, code='036930', strategy='SCALPING', position_tag='SCALPING',
        buy_qty=1, buy_price=210000., exit_mode='SCALP_PRESET_TP',
        hard_stop_pct=-1.4, hard_stop_grace_sec=grace, hard_stop_emergency_pct=emergency)
    stock['main_stop_policy_pin'] = p.pin(position_key=position_cycle_id(stock),
        role='SCALP_PRESET_TP', market='REGULAR', target='2026-10-12', baseline=baseline())
    result = []
    for n, profit in enumerate(profits):
        at = 1791766800. + n
        preset = p.preset_stop_receipt(stock, at=at, evaluator='normal', hard_pct=-1.4,
            grace_sec=grace, emergency_pct=emergency, held_sec=60+n, enabled=True)
        result.append(p.source_row(stock, at=at, bid=210000*(1+profit/100), bid_qty=1,
            quote=dict(market_route='krx_nxt_integrated', item='036930_AL', transport_epoch=1, observed_epoch=at),
            coverage_complete=True, automatic_management_allowed=True,
            cost_model=dict(buy_cost_krw=0., sell_cost_rate=.0023,
                known_at='2026-10-12T08:59:59+09:00', source_sha256='a'*64, actual_broker_cost=False),
            vote_source=None, preset_stop=preset, decision_profit_pct=profit,
            runtime_flags=dict(grace_enabled=True, protect_enabled=True, handoff_enabled=handoff, vote_max_worsen_pct=.8)))
    return stock, result


def handoff_fixture(stock, at, registered=True):
    preset = p.preset_stop_receipt(stock, at=at, evaluator='normal', hard_pct=-1.4,
        grace_sec=0, emergency_pct=-2.4, held_sec=65, enabled=True)
    return p.handoff_source(stock, at=at, registered=registered,
        exit_rule='scalp_preset_hard_stop_pct', profit_pct=-1.42,
        source_stage='fixture_after_quote_guard', preset_stop=preset)


@pytest.mark.parametrize('profit,grace,handoff,rule,disposition', [
    (-1.42, 0, True, 'scalp_hard_stop_pct', 'manual_handoff'),
    (-1.42, 0, False, 'scalp_hard_stop_pct', 'exit_candidate'),
    (-2.5, 90, True, 'scalp_hard_stop_emergency', 'exit_candidate')])
def test_preset_precedes_research_and_common_stop(profit, grace, handoff, rule, disposition):
    stock, source = preset_sources(profits=(-.2, profit), grace=grace, handoff=handoff)
    result = replay_scenario(source, baseline())
    assert result['reason'] == 'native_preset_safety_precedes_common_soft'
    assert result['operating_rule'] == rule and result['operating_disposition'] == disposition
    assert result['modeled_net_krw'] is None and not result['actual_order_submitted']
    contract = holding_scenario(source)
    assert contract['common_stop_values']['soft_stop_pct'] == -3.
    assert contract['effective_preset']['hard_stop_pct'] == -1.4
    assert contract['manual_handoff']['status'] == 'not_observed'


def test_preset_grace_missing_contract_and_pending_or_actual_handoff_are_distinct():
    stock, source = preset_sources(grace=90)
    assert replay_scenario(source, baseline())['reason'] == 'crossing_not_observed'
    source[0].pop('preset_stop'); reseal(source[0])
    assert replay_scenario(source, baseline())['reason'] == 'normal_preset_predecessor_unbound'
    stock, source = preset_sources()
    pending = handoff_fixture(stock, source[-1]['at']+1, registered=False)
    registered = handoff_fixture(stock, pending['at']+5)
    result = holding_scenario(source+[pending, registered])
    assert result['manual_handoff']['status'] == 'registered'
    assert result['manual_handoff']['attempts'] == 2
    assert result['manual_handoff']['source_sha256'] == registered['source_sha256']
    assert result['actual_realized_net_krw'] is None
    assert holding_scenario(source+[pending])['manual_handoff']['status'] == 'pending'
    assert replay_scenario([registered], baseline())['reason'] == 'manual_handoff_not_sell'
    registered['position_key'] = 'another_position'; reseal(registered)
    assert holding_scenario(source+[registered])['reason'] == 'holding_contract_identity_changed'


@pytest.mark.parametrize('mutation', ['hash', 'clock', 'pin', 'stop', 'stage'])
def test_handoff_and_effective_preset_reject_unbound_evidence(mutation):
    from src.engine.automation import main_stop_source_index as idx
    stock, source = preset_sources()
    receipt = handoff_fixture(stock, source[-1]['at']+1)
    if mutation == 'hash': receipt['decision_profit_pct'] = -2.
    elif mutation == 'clock': receipt['at'] -= 100; reseal(receipt)
    elif mutation == 'pin': receipt['pin_sha256'] = 'b'*64; reseal(receipt)
    elif mutation == 'stop': receipt['preset_stop']['hard_stop_pct'] = -3.; reseal(receipt)
    else:
        with pytest.raises(ValueError, match='stop_handoff_stage_invalid'):
            idx.extract(dict(stage='hard_stop_manual_control_handoff_deferred', fields=dict(main_stop_handoff_source=receipt)))
        return
    assert holding_scenario(source+[receipt])['status'] == 'source_gap'


@pytest.mark.parametrize('registered', [True, False])
def test_actual_handoff_adapter_binds_current_cycle_after_registration(monkeypatch, registered):
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as h
    stock, source = preset_sources()
    stock['status'] = 'HOLDING'
    emitted = []
    monkeypatch.setattr(h, '_env_or_rule_bool', lambda *a, **k: True)
    monkeypatch.setattr(h, '_is_scalp_simulated_position', lambda *a: False)
    monkeypatch.setattr(h, '_has_active_sell_order_pending', lambda *a: False)
    monkeypatch.setattr(h, '_resolve_holding_elapsed_sec', lambda *a, **k: 600.)
    monkeypatch.setattr(h, 'add_manual_control_exclusion_code', lambda *a, **k: SimpleNamespace(
        excluded=registered, reason='fixture', source='fixture', code='036930', as_log_fields=lambda: {}))
    monkeypatch.setattr(h, '_log_holding_pipeline', lambda *a, **k: emitted.append((a[2], k)))
    assert h._handoff_hard_stop_to_manual_control_if_enabled(stock, '036930', strategy='SCALPING',
        sell_reason_type='LOSS', exit_rule='scalp_preset_hard_stop_pct', profit_rate=-1.42,
        peak_profit=-.23, curr_price=207500, buy_price=210000., now_ts=source[-1]['at']+1,
        source_stage='normal_after_quote_guard')
    receipt = json.loads(emitted[-1][1]['main_stop_handoff_source'])
    assert r.valid_handoff(receipt) and receipt['registered'] is registered
    assert receipt['preset_stop']['hard_stop_pct'] == -1.4
    assert receipt['position_key'] == source[0]['position_key']
    assert not stock.get('exit_requested')
    assert stock['manual_control_hard_stop_handoff_pending'] is not registered


@pytest.mark.parametrize('evaluator', ['normal', 'fast', 'fast_rest_confirmed', 'fast_prearm'])
def test_preset_observation_matches_evaluator_values_and_never_arms_prearm(monkeypatch, evaluator):
    from src.engine import sniper_state_handlers as h
    stock, source = preset_sources()
    monkeypatch.setattr(h, '_resolve_holding_elapsed_sec', lambda *a, **k: 600.)
    monkeypatch.setattr(h, '_scalp_fast_exit_guard_active', lambda **k: True)
    receipt = h._main_stop_preset_observation(stock, now_ts=source[0]['at'], evaluator=evaluator)
    assert receipt['hard_stop_pct'] == -1.4 and receipt['emergency_pct'] == -2.4
    assert receipt['grace_sec'] == 0 and receipt['held_sec'] == 600.
    assert receipt['enabled'] is (evaluator != 'fast_prearm')
    assert receipt['position_key'] == source[0]['position_key']


@pytest.mark.parametrize('bad_pin', [None, ['malformed']])
def test_missing_pin_observation_cannot_unblock_an_actual_handoff(monkeypatch, bad_pin):
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as h
    stock, source = preset_sources()
    stock['main_stop_policy_pin'] = bad_pin
    stock['status'] = 'HOLDING'
    emitted = []
    monkeypatch.setattr(h, '_env_or_rule_bool', lambda *a, **k: True)
    monkeypatch.setattr(h, '_is_scalp_simulated_position', lambda *a: False)
    monkeypatch.setattr(h, '_has_active_sell_order_pending', lambda *a: False)
    monkeypatch.setattr(h, 'add_manual_control_exclusion_code', lambda *a, **k: SimpleNamespace(
        excluded=True, reason='fixture', source='fixture', code='036930', as_log_fields=lambda: {}))
    monkeypatch.setattr(h, '_log_holding_pipeline', lambda *a, **k: emitted.append(k))
    assert h._handoff_hard_stop_to_manual_control_if_enabled(stock, '036930', strategy='SCALPING',
        sell_reason_type='LOSS', exit_rule='scalp_preset_hard_stop_pct', profit_rate=-1.42,
        peak_profit=-.23, curr_price=207500, buy_price=210000., now_ts=source[-1]['at']+1,
        source_stage='normal_after_quote_guard')
    assert stock['manual_control_exclusion_blocked'] is True
    assert not stock.get('exit_requested') and not stock['manual_control_hard_stop_handoff_pending']
    assert 'main_stop_handoff_source_gap' in emitted[-1]
    assert 'main_stop_handoff_source' not in emitted[-1]


def test_manual_custody_does_not_reactivate_emergency_in_operating_projection():
    stock, source = preset_sources(profits=(-.2, -.3, -5.))
    registered = handoff_fixture(stock, source[1]['at'])
    after = source[2]
    after.update(manual=True, automatic_management_allowed=False)
    reseal(after)
    result = holding_scenario(source[:2]+[registered, after])
    assert result['manual_handoff']['status'] == 'registered'
    assert result['preset_crossing']['source_sha256'] == registered['source_sha256']
    assert result['preset_crossing']['rule'] == 'scalp_hard_stop_pct'
    assert r.preset_decision(after) is None
    after.update(manual=False, automatic_management_allowed=True); reseal(after)
    assert holding_scenario(source[:2]+[registered, after])['reason'] == 'automatic_source_after_manual_handoff'


def test_native_auto_release_is_distinct_from_unexplained_manual_custody_regression():
    from src.engine.automation import main_stop_source_index as idx
    stock,source=preset_sources(profits=(-.2,-.3,.1))
    handoff=handoff_fixture(stock,source[1]['at']+.1)
    release=p.release_source(stock,at=source[1]['at']+.2,auto_source='auto_hard_stop_handoff',
        average_price=210000,current_price=210000,quote_at=source[1]['at'],quote_max_age_sec=3)
    event=dict(stage='manual_control_auto_released_at_average_price',fields={
        'main_stop_release_source':json.dumps(release)})
    assert idx.extract(event)==release
    result=holding_scenario(source[:2]+[handoff,release,source[2]])
    assert result['status']=='observed'
    assert result['manual_handoff']['status']=='released'
    assert result['manual_handoff']['source_sha256']==handoff['source_sha256']
    assert result['manual_release']['source_sha256']==release['source_sha256']
    release['auto_source']='manual_operator';reseal(release)
    assert holding_scenario(source[:2]+[handoff,release,source[2]])['reason']=='manual_release_receipt_invalid'


@pytest.mark.parametrize('field,value', [('coverage_complete', False), ('quote_at', 0),
    ('route', ''), ('transport_epoch', None)])
def test_incomplete_quote_is_not_a_preset_crossing_but_does_not_erase_actual_registration(field, value):
    stock, source = preset_sources()
    actual=list(evaluation_stream(source))
    changed=next(row for row in actual if row['schema']=='main_stop_source_v1' and row['at']==source[-1]['at'])
    prior_sha=changed['source_sha256'];changed[field]=value;reseal(changed)
    for event in actual:
        if event.get('quote_source_sha256')==prior_sha:
            event['quote_source_sha256']=changed['source_sha256']
            if field in ('quote_at','route','transport_epoch'):event[field]=value
            reseal(event)
    result=r.holding_contracts(actual)
    assert result['preset_crossing'] is None and result['status']=='source_gap'
    receipt=handoff_fixture(stock,source[-1]['at']+1)
    result=r.holding_contracts(actual+[receipt])
    assert result['manual_handoff']['status']=='registered'
    assert result['preset_crossing']['source_sha256']==receipt['source_sha256']
    assert result['status']=='source_gap'


def test_postclose_reports_research_preset_and_actual_manual_axes_separately(tmp_path):
    stock, source = preset_sources()
    handoff = handoff_fixture(stock, source[-1]['at'])
    events = [dict(stage='main_stop_source', fields=dict(main_stop_source=json.dumps(row))) for row in evaluation_stream(source)]
    events.append(dict(stage='hard_stop_manual_control_handoff', fields=dict(main_stop_handoff_source=json.dumps(handoff))))
    events.append(dict(stage='hard_stop_manual_control_handoff', fields=dict(runtime_record_id=99)))
    path = tmp_path/'raw.jsonl'
    path.write_text(''.join(json.dumps(event)+'\n' for event in events))
    parents = {f'{role}|{market}': baseline() for role in p.ROLES for market in p.MARKETS}
    args = dict(parents=parents, parent_receipt=seal(tmp_path/'parent.json', {}),
        snapshot_receipt=seal(tmp_path/'snapshot.json', {}), source_paths=[path])
    bundle, report = post.publish(tmp_path, '2026-10-12', '2026-10-13', **args)
    comparison = report['examples'][0]['operating_contract']
    assert report['auxiliary_research_reference']['stop_net_pct'] == -3.
    assert comparison['common_stop_values']['hard_stop_pct'] == -5.
    assert comparison['effective_preset']['hard_stop_pct'] == -1.4
    assert comparison['manual_handoff']['status'] == 'registered'
    assert comparison['actual_realized_net_krw'] is None
    assert report['census']['unbound_handoff_events'] == 1
    assert not report['actual_profit_verified']
    assert all(cell['status'] != 'selected' for cell in bundle['cells'].values())
    assert post.publish(tmp_path, '2026-10-12', '2026-10-13', **args)[1] == report


def test_single_grace_clock_hard_priority_and_reset():
    v=baseline();first=p.soft_decision(v,profit_pct=-3.1,now=100)
    assert first.disposition=='defer_until' and first.due_at==160
    assert p.soft_decision(v,profit_pct=-3.1,now=159,touch_at=100).due_at==160
    assert p.soft_decision(v,profit_pct=-3.1,now=160,touch_at=100).disposition=='exit_candidate'
    assert p.soft_decision(v,profit_pct=-2.9,now=150,touch_at=100).touch_at is None
    for now in (101,159):
        assert p.soft_decision(v,profit_pct=-5.,now=now,touch_at=100).rule=='scalp_hard_stop_pct'
    assert p.soft_decision(v,profit_pct=-3.1,now=110,touch_at=100,after_add=True).disposition=='exit_candidate'
    assert p.soft_decision(v,profit_pct=-3.1,now=99,touch_at=100).disposition=='exit_candidate'


def test_safety_manual_protect_emergency_and_preset_grace():
    args=dict(hard_pct=-1.4,emergency_pct=-2.4,protect_pct=None,handoff_enabled=True)
    assert p.safety_decision(profit_pct=-1.5,held_sec=10,preset_grace_sec=20,**args).disposition=='hold'
    assert p.safety_decision(profit_pct=-1.5,held_sec=21,preset_grace_sec=20,**args).disposition=='manual_handoff'
    assert p.safety_decision(profit_pct=-2.5,held_sec=1,preset_grace_sec=20,**args).rule=='scalp_hard_stop_emergency'
    assert p.safety_decision(profit_pct=-5.,manual=True,**args).rule=='manual_custody'
    assert p.safety_decision(profit_pct=-1.5,**{**args,'protect_pct':-.5}).rule=='scalp_protect_profit_stop'


def test_samples_horizon_duplicate_capacity_and_protect():
    v=replace(baseline(),window_sec=30,min_span_sec=25,buffer_pct=0.,protect_exit_floor_pct=-999.)
    samples=[]
    for n in range(41):samples,quality=p.append_sample(samples,at=100+n,price=9900)
    assert samples[0]['ts']==110 and len(samples)==31
    assert p.protect_confirmed(v,samples,now=140,price_line=9950,profit_pct=-1.)[0]
    assert not p.protect_confirmed(v,samples,now=170,price_line=9950,profit_pct=-1.)[0]
    assert p.append_sample(samples,at=140,price=9900)[1]=='duplicate'
    assert p.append_sample(samples,at=141,price=9900,cap=2)[1]=='capacity_censored'


def test_native_capture_causal_replay_and_missing_cost():
    source=list(rows());a=replay_scenario(source,baseline());b=replay_scenario(source,replace(baseline(),grace_sec=0))
    assert a['status']==b['status']=='modeled'
    assert b['crossing_at']<a['crossing_at'] and b['modeled_net_krw']>a['modeled_net_krw']
    invalid=[dict(x,cost_model=None) for x in source]
    for x in invalid:x['source_sha256']=p.digest({k:v for k,v in x.items() if k!='source_sha256'})
    assert replay_scenario(invalid,baseline())['modeled_net_krw'] is None
    assert replay_scenario(source[3:],baseline())['status']=='censored'


def test_durable_pin_clock_survives_add_and_restart(tmp_path):
    ledger=PositionPeakRuntimeLedger(tmp_path/'peaks.json')
    stock=dict(id=42,code='005930',buy_price=10000.,buy_qty=10)
    ledger.record(stock,peak_price=10000,observed_at=100,reason='fill')
    value=p.pin(position_key=position_cycle_id(stock),role='SCANNER',market='REGULAR',target='2026-10-12',baseline=baseline())
    stock['main_stop_policy_pin']=value
    assert ledger.record_stop_pin(stock,value)
    assert ledger.record_stop_clock(stock,110.)
    stock.update(buy_price=9900,buy_qty=20)
    ledger.record(stock,peak_price=10200,observed_at=120,reason='add')
    restored=PositionPeakRuntimeLedger(tmp_path/'peaks.json').get_for_stock(stock)
    assert restored['main_stop_policy_pin']==value and restored['main_stop_touch_at']==110
    with pytest.raises(ValueError):
        ledger.record_stop_pin(stock,{**value,'pin_sha256':'x'})
    with pytest.raises(ValueError):p.pin_values(value,'target:43:005930')


def publication(tmp_path, *, experiment=False, actual=True):
    p.preload({})
    value=baseline();parents={f'{role}|{market}':value for role in p.ROLES for market in p.MARKETS}
    parent=seal(tmp_path/'parent.json',{'values':asdict(value)})
    snapshot=seal(tmp_path/'snapshot.json',{'date':'2026-10-12'})
    source=tmp_path/'pipeline_events/pipeline_events_2026-10-12.jsonl';source.parent.mkdir(parents=True)
    base=1791766800.
    population=list(rows(base,1))+list(rows(base+100,2))+list(rows(base+1000,3))+list(rows(base+1100,4))
    source.write_text(''.join(json.dumps(dict(stage='main_stop_source',fields={'main_stop_source':row}))+'\n' for row in evaluation_stream(population)))
    contract={}
    if experiment:
        performance=seal(tmp_path/'performance.json',dict(schema='main_stop_performance_v1',status='pass',
            code_sha256=post.code_sha(),scope='runtime_and_postclose',unresolved_findings=[]))
        body=dict(schema='main_stop_experiment_v1',parent_sha256=p.digest(asdict(value)),
            source_sha256=p.digest({str(source):post.byte_generation(source)}),code_sha256=post.code_sha(),
            operator_lock_sha256=p.digest([]),frozen_at=base-100,split_at=base+500,
            min_train=2,min_holdout=2,minimum_paired_ev_krw=0.,allowed_keys=['grace_sec'],embargo_sec=60.,
            max_censoring_ratio=0.,max_standard_error_krw=0.,max_daily_change={'grace_sec':60},performance_receipt=performance)
        body['experiment_sha256']=p.digest(body);contract={'SCANNER|REGULAR':body}
    complete=[dict(id=n,status='COMPLETED',source_date='2026-10-12',main_automatic_management_allowed=True,
        actual_cost_reconciliation=dict(status='actual_cost_reconciled',exact_pnl_krw=-4310.,exact_profit_rate=-4.31,
            receipt_sha256='a'*64,raw_sha256='b'*64)) for n in (1,2,3,4)] if actual else []
    cost=seal(tmp_path/'costs.json',{'rows':complete})
    # Archived v1 policy fixture for downstream numeric/artifact contracts.
    # Isolate only the NEW publication-performance authority seam while making
    # this historical fixture; its old label is never native full-Main proof.
    # The guard is restored before callers exercise readers or new publication.
    from src.engine.scalping import main_stop_experiment as contracts
    with pytest.MonkeyPatch.context() as legacy_fixture:
        if experiment:
            legacy_fixture.setattr(contracts,'require_native_publication_performance',lambda contract,**kwargs:None)
        bundle,report=post.publish(tmp_path,'2026-10-12','2026-10-13',parents=parents,parent_receipt=parent,
            snapshot_receipt=snapshot,source_paths=[source],experiments=contract,completed=complete,economic_sources=dict(files={cost['path']:post.byte_generation(Path(cost['path']))},cost_generations={}))
    return bundle,report,parent,source


def test_actual_producer_publication_loader_pin_and_partial_cells(tmp_path):
    bundle,report,_,_=publication(tmp_path,experiment=True)
    assert bundle['cells']['SCANNER|REGULAR']['status']=='selected'
    assert bundle['cells']['SCANNER|REGULAR']['values']['grace_sec']==0
    assert sum(c['status']=='selected' for c in bundle['cells'].values())==1
    env,receipt=post.handoff(tmp_path,'2026-10-13')
    assert receipt['actual_pid_consumed'] is False
    p.preload(env)
    value=p.pin(position_key='target:44:005930',role='SCANNER',market='REGULAR',target='2026-10-13',baseline=baseline())
    assert p.pin_values(value,'target:44:005930').grace_sec==0
    assert p.pin(position_key='x',role='SCANNER',market='PREMARKET',target='2026-10-13',baseline=baseline())['values']['grace_sec']==60
    p.preload({})


def test_no_cost_no_challenger_and_source_revision_invalidates_handoff(tmp_path):
    bundle,_,parent,_=publication(tmp_path,experiment=True,actual=False)
    assert all(c['status']!='selected' for c in bundle['cells'].values())
    Path(parent['path']).write_text('{}')
    with pytest.raises(ValueError,match='source_changed'):post.handoff(tmp_path,'2026-10-13')


def test_policy_cannot_change_safety_under_carried_status(tmp_path):
    bundle,_,_,_=publication(tmp_path)
    bundle['cells']['SCANNER|REGULAR']['values']['hard_stop_pct']=-6.
    bundle['policy_sha256']=p.digest({k:v for k,v in bundle.items() if k!='policy_sha256'})
    with pytest.raises(ValueError,match='carry_changed'):p.validate_bundle(bundle,'2026-10-13')


def test_stage_and_monitor_uninstalled_vs_committed(tmp_path):
    from src.engine.automation.postclose_summary_handoff import active_stage_names,stage_artifacts,_stage_output_issues
    from src.engine.error_detectors.artifact_freshness import _main_stop_semantics
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now=datetime(2026,10,13,7,tzinfo=ZoneInfo('Asia/Seoul'))
    assert 'main_stop_confirmation' not in active_stage_names('2026-10-08')
    assert 'main_stop_confirmation' in active_stage_names('2026-10-12')
    assert _main_stop_semantics(tmp_path,'2026-10-08',now=now)['status']=='not_installed'
    assert _main_stop_semantics(tmp_path,'2026-10-12',now=now)['expected_overdue']
    publication(tmp_path/'data')
    assert _stage_output_issues(tmp_path/'data/report','2026-10-12','main_stop_confirmation')==[]
    assert _main_stop_semantics(tmp_path,'2026-10-12',now=now)['native_validated']


def test_cost_only_revision_invalidates_native_commit_without_replaying(tmp_path, monkeypatch):
    publication(tmp_path, experiment=True)
    cost=tmp_path/'costs.json'
    raw=json.loads(cost.read_text());raw['rows'][0]['actual_cost_reconciliation']['exact_pnl_krw']=-4400
    cost.write_text(json.dumps(raw))
    monkeypatch.setattr(post,'replay',lambda *a,**k:pytest.fail('monitor must not replay'))
    with pytest.raises(ValueError,match='source_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12')


def test_native_check_avoids_full_raw_hash_in_steady_state(tmp_path,monkeypatch):
    publication(tmp_path)
    original=post.byte_generation
    def bounded_hash(path):
        if 'pipeline_events' in str(path):pytest.fail('steady-state full raw hash')
        return original(path)
    monkeypatch.setattr(post,'byte_generation',bounded_hash)
    assert post.read_committed(tmp_path,'2026-10-12')[1]['opportunity_census']['count']==4


def test_operator_veto_is_not_a_stop_key_successor(tmp_path):
    from src.engine.automation.operator_policy_succession import stop_key_authority
    directory=tmp_path/'threshold_cycle/operator_runtime_env_locks'
    seal(directory/'manual.json',dict(family='main_stop_confirmation',manual_veto=True,
        env_overrides={'KORSTOCKSCAN_SCALP_STOP':-3.}))
    with pytest.raises(ValueError,match='veto'):
        stop_key_authority(tmp_path,'2026-10-13',['soft_stop_pct'])
    with pytest.raises(ValueError,match='subset'):
        stop_key_authority(tmp_path,'2026-10-13',['hard_stop_pct'])


def test_runtime_safety_override_cannot_be_hidden_by_stop_bundle(tmp_path):
    bundle,*_=publication(tmp_path)
    env={'KORSTOCKSCAN_'+p.KEYS[k]:str(v) for k,v in asdict(baseline()).items()}
    p.validate_runtime_environment(bundle,env)
    env['KORSTOCKSCAN_SCALP_HARD_STOP']='-6'
    with pytest.raises(ValueError,match='environment_changed'):
        p.validate_runtime_environment(bundle,env)


def test_stale_quote_and_missing_runtime_flags_are_source_gaps():
    from copy import deepcopy
    original=list(evaluation_stream(rows()))
    stale=deepcopy(original)
    stale[0]['quote_at']=1;reseal(stale[0])
    stale[1]['quote_at']=1;stale[1]['quote_source_sha256']=stale[0]['source_sha256'];reseal(stale[1])
    assert r.replay(stale,baseline())['status']=='source_gap'
    missing=deepcopy(original)
    missing[1]['decision_inputs']['grace_enabled']=None;reseal(missing[1])
    assert r.replay(missing,baseline())['status']=='source_gap'


def test_original_soft_emergency_safety_never_requires_new_ai_votes():
    source=[]
    for row in rows():
        row['holding_ai_required']=True
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
        source.append(row)
    outcome=replay_scenario(source,replace(baseline(),grace_sec=0),
        vote_reader=lambda *args:pytest.fail('existing emergency releases VETO'))
    assert outcome['status']=='modeled'


@pytest.mark.parametrize('name',[
    '_holding_strong_trailing_enabled','_build_soft_stop_whipsaw_confirmation_decision',
    '_attempt_stop_line_touch_mandatory_avg_down','_evaluate_late_loss_avg_down_retry',
    '_evaluate_soft_stop_line_touch_avg_down_defer','_defensive_avg_down_unfilled_recheck_decision',
    '_emit_scalp_hard_time_stop_shadow','_emit_same_symbol_soft_stop_cooldown_shadow',
    '_holding_exit_ai_reason_label','_loss_recovery_intercepts_sell',
])
def test_retired_stop_entrypoints_cannot_be_reenabled(name):
    from src.engine import sniper_state_handlers as handlers
    assert not hasattr(handlers,name)


def test_holdout_cannot_choose_an_alternative_train_winner():
    contract=dict(allowed_keys=['grace_sec'],min_train=2,min_holdout=2,minimum_paired_ev_krw=0,
                  max_censoring_ratio=0.,max_standard_error_krw=100.)
    def result(delta,held_bad):
        return dict(train_n=10,train_total=10,train_delta=delta,train_delta_sq=delta*delta,
                    holdout_n=10,holdout_total=10,holdout_delta=10.,holdout_delta_sq=100.,
                    train_safety_regressions=0,holdout_safety_regressions=held_bad)
    # Better training winner fails holdout; do not look back for a runner-up.
    assert r.choose({'grace_sec:0':result(100,1),'grace_sec:15':result(50,0)},contract)==(None,'hold_no_edge')


def test_old_observed_policy_does_not_exclude_current_parent_comparison():
    source=list(rows())
    previous=replace(baseline(),grace_sec=30)
    for row in source:
        row['source_stop_values']=asdict(previous)
        row['parent_values_sha256']=p.digest(asdict(previous))
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
    assert replay_scenario(source,baseline())['status']=='modeled'


def test_dependency_mutation_between_hash_and_stat_is_rejected(tmp_path,monkeypatch):
    path=tmp_path/'source';path.write_text('old')
    expected=post.byte_generation(path)
    original=post.byte_generation
    def mutate(value):
        receipt=original(value)
        value.write_text('new')
        return receipt
    monkeypatch.setattr(post,'byte_generation',mutate)
    with pytest.raises(ValueError,match='source_changed'):
        post.verified_dependency_stats({str(path):expected})


def test_restart_without_original_touch_never_gets_new_grace(tmp_path,monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    p.preload({})
    monkeypatch.setattr(handlers,'POSITION_PEAK_LEDGER',PositionPeakRuntimeLedger(tmp_path/'ledger.json'))
    stock=dict(id=8,code='005930',strategy='SCALPING',buy_price=10000.,buy_qty=10,
               buy_time=100.,main_stop_restoring_position=True)
    handlers._main_stop_values(stock,1791766800.)
    assert stock['main_stop_clock_unobserved'] is True
    assert stock['main_stop_policy_pin']['origin']=='effective_legacy_rules'


def test_cost_delta_reuses_position_replay_and_nochange_skips_decode(tmp_path,monkeypatch):
    _,report,parent,source=publication(tmp_path)
    cost=tmp_path/'costs.json';cost.write_text(json.dumps({'revision':2}))
    parents={f'{role}|{market}':baseline() for role in p.ROLES for market in p.MARKETS}
    args=dict(parents=parents,parent_receipt=parent,source_paths=[source],
        snapshot_receipt=report['snapshot_receipt'],economic_sources=dict(files={str(cost):post.byte_generation(cost)},cost_generations={}))
    monkeypatch.setattr(post,'replay',lambda *a,**k:pytest.fail('cost correction replayed price path'))
    monkeypatch.setattr(post,'source_events',lambda *a,**k:pytest.fail('unchanged source file decoded raw'))
    bundle,changed=post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    assert changed['research_sha256']!=report['research_sha256']
    assert changed['opportunity_census']['count']==4
    monkeypatch.setattr(post,'source_events',lambda *a,**k:pytest.fail('unchanged generation decoded raw'))
    assert post.publish(tmp_path,'2026-10-12','2026-10-13',**args)[0]==bundle


def test_native_loader_receipt_and_pin_are_observed_without_executing_exit(tmp_path):
    bundle,*_=publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    p.preload(env)
    receipt=p.record_loaded_policy(tmp_path)
    assert receipt and p.record_loaded_policy(tmp_path) is None
    result=post.runtime_consumption(tmp_path,bundle)
    assert result['actual_pid_consumed'] and result['status']=='loader_observed'
    raw=json.loads(receipt.read_text());raw['loaded_cells_sha256']='b'*64
    raw['receipt_sha256']=p.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
    receipt.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='loaded_map'):post.runtime_consumption(tmp_path,bundle)
    p.preload({})


def test_manual_registration_does_not_hold_entry_lock_or_duplicate(tmp_path,monkeypatch):
    import threading
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as h
    started,finish=threading.Event(),threading.Event()
    stock=dict(id=12,code='005930',status='HOLDING',strategy='SCALPING',buy_qty=10)
    calls=[]
    def register(*args,**kwargs):
        calls.append(1);started.set()
        assert finish.wait(3)
        return SimpleNamespace(excluded=False,reason='isolated_failure',source='fixture',code='005930',as_log_fields=lambda:{})
    monkeypatch.setattr(h,'add_manual_control_exclusion_code',register)
    monkeypatch.setattr(h,'_env_or_rule_bool',lambda *a,**k:True)
    monkeypatch.setattr(h,'_is_scalp_simulated_position',lambda *a:False)
    monkeypatch.setattr(h,'_has_active_sell_order_pending',lambda *a:False)
    monkeypatch.setattr(h,'_log_holding_pipeline',lambda *a,**k:None)
    monkeypatch.setattr(h,'log_error',lambda *a:None)
    args=dict(strategy='SCALPING',sell_reason_type='LOSS',exit_rule='scalp_hard_stop_pct',profit_rate=-5.,peak_profit=0.,curr_price=9500,buy_price=10000,now_ts=100.,source_stage='fixture')
    result=[]
    thread=threading.Thread(target=lambda:result.append(h._handoff_hard_stop_to_manual_control_if_enabled(stock,'005930',**args)))
    thread.start()
    try:
        assert started.wait(3)
        assert h.ENTRY_LOCK.acquire(timeout=.2)
        h.ENTRY_LOCK.release()
        assert h._handoff_hard_stop_to_manual_control_if_enabled(stock,'005930',**args)
        assert calls==[1]
    finally:
        finish.set();thread.join(3)
    assert result==[True] and stock['manual_control_hard_stop_handoff_pending']
    assert not stock.get('exit_requested')


@pytest.mark.parametrize('deferred',[False,True])
def test_stop_capture_uses_shared_queue_immutable_envelope_and_drop_marker(monkeypatch,deferred):
    from contextlib import nullcontext
    from concurrent.futures import ThreadPoolExecutor
    from src.utils import pipeline_event_logger as logger
    events=[]
    monkeypatch.setattr(logger,'emit_pipeline_event',lambda *a,**k:events.append((a,k)) or {'structured_append_succeeded':True})
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue=logger.BoundedObservationQueue(executor)
        p.configure_source_sink(queue.submit)
        row=next(rows());row.pop('source_sha256')
        with p.defer_source_capture() if deferred else nullcontext():
            assert p.enqueue_source({'id':1},'005930',row)
            row['bid']=1
        queue.close(timeout=2)
    p.configure_source_sink(None)
    captured=json.loads(events[0][1]['fields']['main_stop_source'])
    assert captured['bid']==9990 and captured['source_sha256']==p.digest({k:v for k,v in captured.items() if k!='source_sha256'})
    assert events[0][1]['observed_at_epoch']==captured['at']
    assert not p.enqueue_source({'id':1},'005930',row)
    source=list(rows());source[1]['capture_rejected_count']=1
    source[1]['source_sha256']=p.digest({k:v for k,v in source[1].items() if k!='source_sha256'})
    assert replay_scenario(source,baseline())['status']=='source_gap'


def test_runtime_crossing_and_modeled_cost_are_separate():
    source=list(rows())
    for row in source:
        row['decision_profit_pct']=0.
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
    assert replay_scenario(source,replace(baseline(),grace_sec=0))['reason']=='crossing_not_observed'
    actual=list(evaluation_stream(source))
    actual[1]['decision_profit_pct']=None;reseal(actual[1])
    assert r.replay(actual,baseline())['status']=='source_gap'


def test_legacy_protection_number_does_not_invent_a_main_generator():
    source=list(rows());source[0]['protect_line']=9800.
    source[0]['source_sha256']=p.digest({k:v for k,v in source[0].items() if k!='source_sha256'})
    assert replay_scenario(source,baseline())['reason']=='protect_line_producer_unidentified'


def test_partitioned_reference_index_deduplicates_without_copying_raw(tmp_path):
    from src.engine.automation import main_stop_source_index as idx
    from collections import Counter
    source=tmp_path/'raw.jsonl'
    population=list(rows())
    event=lambda row:dict(stage='main_stop_source',fields={'main_stop_source':row})
    source.write_text(''.join(json.dumps(event(row))+'\n' for row in population+population))
    census=Counter();inventory={str(source):post.byte_generation(source)}
    prepared=idx.prepare(tmp_path/'cache',inventory,post.source_events,census)
    assert census['raw']==18
    positions=list()
    for position in idx.positions(prepared,tmp_path/'scratch',census):
        positions.append(list(position.rows()))
    assert positions==[population]
    for path in (tmp_path/'cache').rglob('*.json'):
        raw=path.read_text()
        assert '"cost_model"' not in raw and '"buy_basis_krw"' not in raw
    assert census['deduplicated']==9


def test_vote_new_file_and_same_bytes_replacement_regenerate_native_generation(tmp_path):
    _,report,parent,source=publication(tmp_path)
    args=dict(parents={f'{role}|{market}':baseline() for role in p.ROLES for market in p.MARKETS},
        parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'])
    # Discovery of a formerly absent original is part of native invalidation.
    vote=tmp_path/'runtime/holding_path_votes/new.jsonl';vote.parent.mkdir(parents=True);vote.write_text('{}\n')
    with pytest.raises(ValueError,match='vote_source_set_changed'):post.read_committed(tmp_path,'2026-10-12')
    post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    before=post.read_committed(tmp_path,'2026-10-12')[2]['generation']
    replacement=tmp_path/'copy.jsonl';replacement.write_bytes(source.read_bytes());replacement.replace(source)
    post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    assert post.read_committed(tmp_path,'2026-10-12')[2]['generation']!=before


def test_performance_evidence_cannot_be_missing_or_changed(tmp_path):
    bundle,*_=publication(tmp_path,experiment=True)
    (tmp_path/'performance.json').write_text('{}')
    with pytest.raises(ValueError,match='performance_gate'):p.validate_bundle(bundle,'2026-10-13')


def test_bounded_reader_rejects_path_replaced_during_read(tmp_path,monkeypatch):
    path=tmp_path/'source.json';path.write_text('{"x":1}')
    original=Path.open
    class Changing:
        def __init__(self,handle):self.handle=handle
        def __enter__(self):self.handle.__enter__();return self
        def __exit__(self,*args):return self.handle.__exit__(*args)
        def fileno(self):return self.handle.fileno()
        def read(self,size):
            raw=self.handle.read(size)
            replacement=tmp_path/'next.json';replacement.write_text('{"x":2}');replacement.replace(path)
            return raw
    def open_path(self,*args,**kwargs):
        handle=original(self,*args,**kwargs)
        return Changing(handle) if self==path and args==('rb',) else handle
    monkeypatch.setattr(Path,'open',open_path)
    with pytest.raises(ValueError,match='changed_during_read'):p.bounded_object(path)


def test_nested_census_shard_change_is_detected_without_raw_replay(tmp_path):
    publication(tmp_path)
    _,report,_,directory=post.read_committed(tmp_path,'2026-10-12')
    dependencies=report['census_dependencies']
    leaf=next(directory/name for name in dependencies if '"rows"' in (directory/name).read_text())
    raw=json.loads(leaf.read_text());raw['rows'][0]['reason']='tampered';leaf.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='census_shard_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12')


def test_source_discovery_includes_native_late_partition(tmp_path):
    import gzip
    directory=tmp_path/'pipeline_events';directory.mkdir()
    base=directory/'pipeline_events_2026-10-12.jsonl';base.write_text('{}\n')
    late=directory/'pipeline_events_2026-10-12.late.jsonl.gz'
    with gzip.open(late,'wt') as handle:handle.write('{}\n')
    assert post.sources(tmp_path,'2026-10-12')==[base,late]


def test_new_late_source_invalidates_handoff_and_must_enter_new_census(tmp_path):
    _,report,parent,source=publication(tmp_path)
    before=post.read_committed(tmp_path,'2026-10-12')[2]['generation']
    late=source.with_name('pipeline_events_2026-10-12.late.jsonl')
    late.write_text(''.join(json.dumps(dict(stage='main_stop_source',
        fields={'main_stop_source':row}))+'\n' for row in rows(record=5)))
    with pytest.raises(ValueError,match='raw_source_set_changed'):
        post.handoff(tmp_path,'2026-10-13')
    args=dict(parents={f'{r}|{m}':baseline() for r in p.ROLES for m in p.MARKETS},
        parent_receipt=parent,snapshot_receipt=report['snapshot_receipt'])
    with pytest.raises(ValueError,match='source_catalog_not_consumed'):
        post.publish(tmp_path,'2026-10-12','2026-10-13',source_paths=[source],**args)
    post.publish(tmp_path,'2026-10-12','2026-10-13',source_paths=post.sources(tmp_path,'2026-10-12'),**args)
    _,current,pointer,_=post.read_committed(tmp_path,'2026-10-12',verify_full=True)
    assert pointer['generation']!=before
    assert current['opportunity_census']['count']==5
    assert str(late) in current['source_inventory']


def test_budget_interruption_preserves_committed_pointer_and_records_resume(tmp_path,monkeypatch):
    _,report,parent,source=publication(tmp_path)
    pointer=post.committed_path(tmp_path,'2026-10-12');before=pointer.read_bytes()
    monkeypatch.setattr(post,'MAX_RESEARCH_SECONDS',0)
    with pytest.raises(ValueError,match='deadline_exceeded'):
        post.publish(tmp_path,'2026-10-12','2026-10-13',parents={f'{r}|{m}':baseline() for r in p.ROLES for m in p.MARKETS},
            parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'])
    assert pointer.read_bytes()==before
    receipt=json.loads((tmp_path/'report/main_stop_confirmation/resume_2026-10-12.json').read_text())
    assert receipt['status']=='incomplete' and receipt['target_policy_published'] is False


@pytest.mark.parametrize('compressed,terminated', [(False, True), (True, True), (False, False)])
def test_oversized_source_record_is_isolated_and_later_rows_remain_visible(tmp_path, compressed, terminated):
    from collections import Counter
    import gzip
    oversized = json.dumps({'stage': 'unknown', 'body': 'x' * (2 * 1024 * 1024 + 64)})
    valid = json.dumps({'stage': 'main_stop_source', 'fields': {'main_stop_source': next(iter(rows()))}})
    body = (oversized + '\n' + valid + '\n') if terminated else oversized
    path = tmp_path / ('raw.jsonl.gz' if compressed else 'raw.jsonl')
    if compressed:
        with gzip.open(path, 'wt') as stream:
            stream.write(body)
    else:
        path.write_text(body)
    census = Counter()
    result = list(post.source_events(path, census, references=True))
    assert census['oversized_raw_rows'] == 1
    assert census['unidentifiable_raw_rows'] == 1
    assert census['oversized_raw_bytes'] == len((oversized + ('\n' if terminated else '')).encode())
    assert census['oversized_unterminated_raw_rows'] == (0 if terminated else 1)
    assert len(result) == (1 if terminated else 0)
    if terminated:
        assert result[0][0]['stage'] == 'main_stop_source'
        assert result[0][2] == hashlib.sha256((valid + '\n').encode()).hexdigest()
    assert any(key.startswith('oversized_raw_record:') and key.endswith(
        hashlib.sha256((oversized + ('\n' if terminated else '')).encode()).hexdigest()) for key in census)


def test_oversized_source_publishes_explicit_gap_carry_with_unchanged_parent(tmp_path):
    _, report, parent, source = publication(tmp_path)
    with source.open('a') as stream:
        stream.write(json.dumps({'stage': 'main_stop_source', 'fields': {'unreadable': 'x' * (2 * 1024 * 1024)}}) + '\n')
    bundle, successor = post.publish(tmp_path, '2026-10-12', '2026-10-13',
        parents={f'{r}|{m}': baseline() for r in p.ROLES for m in p.MARKETS},
        parent_receipt=parent, source_paths=[source], snapshot_receipt=report['snapshot_receipt'])
    assert successor['census']['oversized_raw_rows'] == 1
    assert successor['actual_profit_verified'] is False
    assert all(cell['status'] == 'source_gap' and cell['values'] == asdict(baseline())
               and not cell['authority'] for cell in bundle['cells'].values())
    actual, saved, _, _ = post.read_committed(tmp_path, '2026-10-12', verify_full=True)
    assert actual == bundle and saved == successor


def test_stop_source_index_invalidates_when_native_decoder_code_changes(tmp_path, monkeypatch):
    from collections import Counter
    from src.engine.automation import main_stop_source_index as idx
    source = tmp_path / 'source.jsonl'
    source.write_text(json.dumps({'stage': 'main_stop_source', 'fields': {
        'main_stop_source': next(iter(rows()))}}) + '\n')
    inventory = {str(source): post.byte_generation(source)}
    first = idx.prepare(tmp_path / 'index', inventory, post.source_events, Counter())
    read_bytes = Path.read_bytes
    decoder = Path(post.__file__).resolve()
    def changed_code(path):
        value = read_bytes(path)
        return value + b'\n# changed native decoder\n' if path.resolve() == decoder else value
    monkeypatch.setattr(Path, 'read_bytes', changed_code)
    second = idx.prepare(tmp_path / 'index', inventory, post.source_events, Counter())
    assert first[0][0] != second[0][0]
    assert first[0][1]['generation'] == second[0][1]['generation']
    assert second[0][1]['census']['raw'] == 1


def test_historical_parent_values_can_migrate_but_old_code_cannot_load_live(tmp_path,monkeypatch):
    _,*_=publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    monkeypatch.setattr(p,'implementation_sha',lambda:'e'*64)
    with pytest.raises(ValueError,match='code_generation_changed'):
        p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],env[p.ENV_DATE])
    parent=p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],env[p.ENV_DATE],require_current_code=False)
    assert parent['cells']['SCANNER|REGULAR']['values']==asdict(baseline())


@pytest.mark.parametrize('fault', [None, 'missing', 'policy', 'code', 'status'])
def test_reviewed_incumbent_stop_consumer_preserves_original_policy_and_full_research_pin(tmp_path, monkeypatch, fault):
    from src.engine.automation import intraday_release_handoff as H
    _,*_=publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    original=Path(env[p.ENV_FILE]).read_bytes()
    bundle=json.loads(original)
    monkeypatch.setattr(p,'implementation_sha',lambda:'e'*64)
    calls=[]
    def verify(day, **kw):
        calls.append(kw)
        assert day=='2026-10-13' and kw['family']=='main_stop'
        assert kw['policy_sha']==bundle['policy_sha256'] and kw['expected']==bundle['code_sha256']
        if fault=='missing':raise ValueError('native consumption missing')
        return dict(status='fail' if fault=='status' else 'verified_intraday_consumer_repair',
            policy_effect='unchanged', policy_sha256='changed' if fault=='policy' else kw['policy_sha'],
            code_contract_sha256=kw['expected'],runtime_code_contract_sha256='changed' if fault=='code' else kw['actual'])
    monkeypatch.setattr(H,'verify_entry_consumer_code',verify)
    if fault:
        with pytest.raises(ValueError,match='code_generation_changed'):
            p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],'2026-10-13')
    else:
        loaded=p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],'2026-10-13')
        assert loaded==bundle
        post.read_committed(tmp_path,'2026-10-12')
    called=len(calls)
    with pytest.raises(ValueError,match='code_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12',verify_full=True)
    assert len(calls)==called
    assert Path(env[p.ENV_FILE]).read_bytes()==original


def test_selected_stop_successor_cannot_use_incumbent_code_handoff(tmp_path, monkeypatch):
    from src.engine.automation import intraday_release_handoff as H
    bundle,*_=publication(tmp_path,experiment=True)
    assert any(c['status']=='selected' for c in bundle['cells'].values())
    env,_=post.handoff(tmp_path,'2026-10-13')
    monkeypatch.setattr(p,'implementation_sha',lambda:'e'*64)
    monkeypatch.setattr(H,'verify_entry_consumer_code',lambda *a,**kw:pytest.fail('selected policy cannot use incumbent proof'))
    with pytest.raises(ValueError,match='code_generation_changed'):
        p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],'2026-10-13')


def test_malformed_durable_pin_keeps_typed_hard_safety(monkeypatch):
    from src.engine import sniper_state_handlers as h
    from types import SimpleNamespace
    p.preload({})
    stock=dict(id=7,code='005930',strategy='SCALPING',buy_price=10000.,buy_qty=10,main_stop_policy_pin={})
    value=h._main_stop_values(stock,1791766800.)
    assert value.hard_stop_pct<value.soft_stop_pct
    assert stock['main_stop_pin_persistence']=='invalid_pin_safety_only'
    assert '_main_stop_source_values' not in stock
    assert p.soft_decision(value,profit_pct=-10.,now=1791766800.).disposition=='exit_candidate'


def test_fast_source_admission_follows_disposition_and_freezes_input():
    calls=[];stock={'id':1,'name':'fixture'};row={'at':100.,'cost_model':{'fee':10}}
    p.configure_source_sink(lambda *a,**k:calls.append((a,k)) or {'status':'queued'})
    try:
        with p.defer_source_capture():
            assert p.enqueue_source(stock,'005930',row)
            row['cost_model']['fee']=999
            assert calls==[]
            with p.defer_source_capture():
                assert calls==[]
        assert len(calls)==1 and json.loads(calls[0][0][-1])['cost_model']['fee']==10
    finally:p.configure_source_sink(None)


def test_fast_source_queue_failure_never_masks_exit_or_original_exception():
    stock={'id':1}
    def fail(*a,**k):raise OSError('writer unavailable')
    p.configure_source_sink(fail)
    try:
        with pytest.raises(RuntimeError,match='original_exit_error'):
            with p.defer_source_capture():
                assert p.enqueue_source(stock,'005930',{'at':100.})
                raise RuntimeError('original_exit_error')
        assert stock['main_stop_source_rejected_count']==1
        assert stock['main_stop_source_gap']=='observation_queue_rejected'
    finally:p.configure_source_sink(None)


def test_fast_source_local_buffer_stays_bounded():
    stock={'id':1}
    with p.defer_source_capture():
        assert p.enqueue_source(stock,'005930',{'at':100.})
        assert p.enqueue_source(stock,'005930',{'at':101.})
        assert not p.enqueue_source(stock,'005930',{'at':102.})


def test_unsealed_observation_vector_refreshes_all_inputs_and_cannot_be_mutated(monkeypatch):
    from src.engine.scalping import trailing_mechanical_policy as policy
    monkeypatch.delenv(policy.VECTOR_SHA_ENV_KEY,raising=False)
    env_key=policy.MARKET_ENV_KEYS['SCALP_TRAILING_START_PCT']['REGULAR']
    monkeypatch.delenv(env_key,raising=False)
    scalar=dict(policy.DEFAULTS)
    first=policy.runtime_policy_vector_snapshot(scalar)
    first[0]['REGULAR']['SCALP_TRAILING_START_PCT']=999
    assert policy.runtime_policy_vector_snapshot(scalar)[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.4
    monkeypatch.setenv(env_key,'.6')
    second=policy.runtime_policy_vector_snapshot(scalar)
    assert second[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.6 and second[3]!=first[3]
    monkeypatch.delenv(env_key)
    scalar['SCALP_TRAILING_START_PCT']=.5
    assert policy.runtime_policy_vector_snapshot(scalar)[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.5
    monkeypatch.setenv(env_key,'bad')
    with pytest.raises(ValueError):policy.runtime_policy_vector_snapshot(scalar)


def _later_vote_bytes(day='2026-10-13', **changes):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    value=dict(schema='holding_path_vote_v10',position_key='record:91',session_key=day,
        requested_at=datetime.fromisoformat(day+'T10:00:00').replace(tzinfo=ZoneInfo('Asia/Seoul')).timestamp())
    value.update(changes)
    return json.dumps(value).encode()+b'\n'


@pytest.mark.parametrize('new_file',[False,True])
@pytest.mark.parametrize('damage',[None,'past','session','position','schema','nan','overflow','partial','replaced','prefix','source','selected'])
def test_carried_stop_partitions_only_future_unconsumed_votes(tmp_path,new_file,damage):
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path=path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    original=_later_vote_bytes('2026-10-12')
    if not new_file:path.write_bytes(original)
    bundle,report,_,_=publication(tmp_path,experiment=damage=='selected')
    generation=(post.committed_path(tmp_path,'2026-10-12')).read_bytes()
    suffix=_later_vote_bytes()
    if damage=='past':suffix=_later_vote_bytes('2026-10-12')
    elif damage=='session':suffix=_later_vote_bytes(session_key='2026-10-14')
    elif damage=='position':suffix=_later_vote_bytes(position_key='foreign')
    elif damage=='schema':suffix=_later_vote_bytes(schema='foreign')
    elif damage=='nan':suffix=_later_vote_bytes(requested_at=float('nan'))
    elif damage=='overflow':suffix=_later_vote_bytes(requested_at=1e300)
    elif damage=='partial':suffix=suffix.rstrip(b'\n')
    if damage=='prefix' and not new_file:
        with path.open('r+b') as out:out.write(original.replace(b'record:91',b'record:92'))
    if damage=='replaced' and not new_file:
        replacement=path.with_suffix('.replacement');replacement.write_bytes(original+suffix);replacement.replace(path)
    else:
        with path.open('ab') as out:out.write(suffix)
    path.with_suffix('.jsonl.lock').touch()
    if damage=='source':
        source=tmp_path/'pipeline_events/pipeline_events_2026-10-12.jsonl'
        with source.open('a') as out:out.write('{}\n')
    accepted=damage is None or (damage in {'replaced','prefix'} and new_file)
    if accepted:
        loaded,saved,_,_=post.read_committed(tmp_path,'2026-10-12')
        assert loaded==bundle and saved==report
        assert report['vote_source_inventory']=={}
        assert post.handoff(tmp_path,'2026-10-13')[1]['status']=='verified_carried'
    else:
        with pytest.raises((ValueError,OSError)):
            post.read_committed(tmp_path,'2026-10-12')
    with pytest.raises(ValueError):post.read_committed(tmp_path,'2026-10-12',verify_full=True)
    assert post.committed_path(tmp_path,'2026-10-12').read_bytes()==generation


def test_vote_tail_cannot_relax_consumed_source_or_incomplete_original(tmp_path):
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path=path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    path.write_bytes(_later_vote_bytes('2026-10-12').rstrip(b'\n'))
    bound=post.capture_vote_watch_binding(tmp_path,'2026-10-12')
    with path.open('ab') as out:out.write(_later_vote_bytes())
    path.with_suffix('.jsonl.lock').touch()
    with pytest.raises(ValueError,match='boundary_invalid'):
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',bound,future_unconsumed=True)
    with pytest.raises(ValueError):post.verify_vote_watch_binding(tmp_path,'2026-10-12',bound)


@pytest.mark.parametrize('damage', [None, 'prefix', 'past', 'partial', 'replace', 'race', 'unsealed'])
def test_carried_stop_preserves_consumed_vote_prefix_before_future_tail(tmp_path, monkeypatch, damage):
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path = path_vote_store_path(tmp_path, 'record:91')
    path.parent.mkdir(parents=True)
    original = _later_vote_bytes('2026-10-12')
    path.write_bytes(original)
    # Exercise the native publisher with a consumed, hashed vote dependency.
    def consumed(root, directory, source, inventory):
        inventory[str(path)] = post.byte_generation(path)
        return None
    from src.engine.ai import holding_vote_replay_source
    monkeypatch.setattr(holding_vote_replay_source, 'assemble_votes', consumed)
    original_rows = rows
    def with_vote_source(*args, **kwargs):
        from src.tests.test_main_stop_runtime_source import stage_stock
        from src.engine.ai.holding_exit_vote import buy_fill_identity_from_runtime
        for row in original_rows(*args, **kwargs):
            native = stage_stock(record=row['record_id'],quantity=row['quantity'])
            source = holding_vote_replay_source.runtime_source(native,position_key=f"record:{row['record_id']}",
                buy_fill_identity=buy_fill_identity_from_runtime(native),market=row['market'],now=row['at'],policy={},
                data_root=tmp_path,model='fixture-model',path_id='EXIT_SOFT_STOP')
            yield reseal(dict(row,holding_vote_source=source,holding_ai_required=True))
    monkeypatch.setitem(globals(), 'rows', with_vote_source)
    if damage == 'unsealed':
        capture = post.capture_vote_watch_binding
        def legacy_binding(*args):
            binding = capture(*args)
            binding[str(path)].pop('decoded_sha256')
            return binding
        monkeypatch.setattr(post, 'capture_vote_watch_binding', legacy_binding)
    bundle, report, _, _ = publication(tmp_path)
    assert str(path) in report['vote_source_inventory']
    suffix = _later_vote_bytes('2026-10-12' if damage == 'past' else '2026-10-13')
    if damage == 'partial': suffix = suffix.rstrip(b'\n')
    if damage == 'prefix': path.write_bytes(original.replace(b'record:91', b'record:92'))
    if damage == 'replace':
        other = path.with_suffix('.replacement');other.write_bytes(original);other.replace(path)
    with path.open('ab') as out: out.write(suffix)
    path.with_suffix('.jsonl.lock').touch()
    if damage == 'race':
        verify = post.verify_vote_watch_binding
        def append_after_verification(*args, **kwargs):
            observed = verify(*args, **kwargs)
            with path.open('ab') as out: out.write(_later_vote_bytes())
            return observed
        monkeypatch.setattr(post, 'verify_vote_watch_binding', append_after_verification)
    if damage is None:
        loaded, saved, _, _ = post.read_committed(tmp_path, '2026-10-12')
        assert loaded == bundle and saved == report
        assert post.handoff(tmp_path, '2026-10-13')[1]['status'] == 'verified_carried'
    else:
        with pytest.raises((OSError, ValueError)):
            post.read_committed(tmp_path, '2026-10-12')
    with pytest.raises(ValueError):
        post.read_committed(tmp_path, '2026-10-12', verify_full=True)


@pytest.mark.parametrize('new_file', [False, True])
@pytest.mark.parametrize('damage', [None, 'past', 'prefix', 'replace'])
def test_carried_vote_revalidates_append_between_file_read_and_census_end(tmp_path, monkeypatch, new_file, damage):
    import fcntl
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path=path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    original=_later_vote_bytes('2026-10-12')
    if not new_file:path.write_bytes(original)
    bound=post.capture_vote_watch_binding(tmp_path,'2026-10-12')
    with path.open('ab') as out:out.write(_later_vote_bytes())
    lock=path.with_suffix('.jsonl.lock');lock.touch()
    real=post._vote_watch_files;calls=0
    def concurrent_append(root, day):
        nonlocal calls
        files=real(root,day);calls+=1
        if calls==2:
            with lock.open('rb') as guard:
                fcntl.flock(guard,fcntl.LOCK_EX)
                if damage=='replace':
                    other=path.with_suffix('.replacement');other.write_bytes(path.read_bytes());other.replace(path)
                elif damage=='prefix':
                    with path.open('r+b') as out:out.write(b'!')
                else:
                    with path.open('ab') as out:out.write(_later_vote_bytes('2026-10-12' if damage=='past' else '2026-10-14'))
        return files
    monkeypatch.setattr(post,'_vote_watch_files',concurrent_append)
    if damage:
        with pytest.raises((ValueError,OSError)):
            post.verify_vote_watch_binding(tmp_path,'2026-10-12',bound,future_unconsumed=True)
    else:
        post.verify_vote_watch_binding(tmp_path,'2026-10-12',bound,future_unconsumed=True)
    assert calls==2


def test_future_vote_reader_uses_native_writer_lock(tmp_path, monkeypatch):
    import fcntl
    from concurrent.futures import ThreadPoolExecutor
    from src.engine.ai import holding_exit_vote as votes
    path=votes.path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    path.write_bytes(_later_vote_bytes());lock=path.with_suffix('.jsonl.lock');lock.touch()
    real=votes.path_vote_store_path;blocked=[]
    def writer_probe():
        with lock.open('rb') as writer:
            try:fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:return True
            return False
    def inspect_lock(root,key):
        with ThreadPoolExecutor(max_workers=1) as executor:
            blocked.append(executor.submit(writer_probe).result(timeout=2))
        return real(root,key)
    monkeypatch.setattr(votes,'path_vote_store_path',inspect_lock)
    before=path.read_bytes()
    post._future_unconsumed_vote_tail(tmp_path,'2026-10-12',path,None)
    assert blocked==[True] and path.read_bytes()==before


@pytest.mark.parametrize('damage', ['missing','symlink','fifo','busy','replaced'])
def test_future_vote_lock_is_bounded_native_and_never_created_by_reader(tmp_path, monkeypatch, damage):
    import fcntl, os, time
    from src.engine.ai import holding_exit_vote as votes
    path=votes.path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    path.write_bytes(_later_vote_bytes());lock=path.with_suffix('.jsonl.lock')
    held=None
    if damage=='symlink':
        target=tmp_path/'foreign';target.touch();lock.symlink_to(target)
    elif damage=='fifo':os.mkfifo(lock)
    elif damage!='missing':lock.touch()
    if damage=='busy':
        held=lock.open('rb');fcntl.flock(held,fcntl.LOCK_EX)
    if damage=='replaced':
        real=votes.path_vote_store_path
        def replace_lock(root,key):
            other=tmp_path/'other-lock';other.touch();other.replace(lock)
            return real(root,key)
        monkeypatch.setattr(votes,'path_vote_store_path',replace_lock)
    start=time.monotonic()
    try:
        with pytest.raises((ValueError,OSError)):
            post._future_unconsumed_vote_tail(tmp_path,'2026-10-12',path,None)
    finally:
        if held:held.close()
    assert time.monotonic()-start<2
    if damage=='missing':assert not lock.exists()


def test_future_vote_waits_for_native_partial_append_to_finish(tmp_path, monkeypatch):
    import fcntl
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path=path_vote_store_path(tmp_path,'record:91');path.parent.mkdir(parents=True)
    lock=path.with_suffix('.jsonl.lock');lock.touch()
    partial,reader_waiting=Event(),Event();raw=_later_vote_bytes()
    real=fcntl.flock
    def traced_flock(fd,operation):
        if operation==fcntl.LOCK_SH|fcntl.LOCK_NB:reader_waiting.set()
        return real(fd,operation)
    monkeypatch.setattr(fcntl,'flock',traced_flock)
    def writer():
        with lock.open('rb') as guard:
            real(guard,fcntl.LOCK_EX)
            with path.open('wb') as out:
                out.write(raw[:len(raw)//2]);out.flush();partial.set()
                assert reader_waiting.wait(2)
                out.write(raw[len(raw)//2:]);out.flush()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(writer);assert partial.wait(2)
        result=post._future_unconsumed_vote_tail(tmp_path,'2026-10-12',path,None)
        future.result(timeout=2)
    assert result[2]==len(raw) and path.read_bytes()==raw


@pytest.mark.parametrize('damage', [None, 'hash', 'size', 'inode', 'path', 'receipt', 'new_source', 'bytes', 'symlink'])
def test_pipeline_archive_preserves_native_stop_binding_only_for_exact_source(tmp_path, damage):
    import gzip
    _, report, _, raw = publication(tmp_path)
    content = raw.read_bytes()
    archive = Path(str(raw)+'.gz')
    archive.write_bytes(gzip.compress(content))
    raw.unlink()
    st = archive.stat()
    receipt = dict(schema='pipeline_raw_archive_identity_v1', logical_path=str(raw),
        logical_content_sha256=report['source_inventory'][str(raw)]['sha256'],
        logical_size_bytes=len(content), runtime_effect=False, allowed_runtime_apply=False,
        archive_generation=dict(device=st.st_dev,inode=st.st_ino,size_bytes=st.st_size,mtime_ns=st.st_mtime_ns))
    if damage == 'hash':receipt['logical_content_sha256']='0'*64
    if damage == 'size':receipt['logical_size_bytes']+=1
    if damage == 'inode':receipt['archive_generation']['inode']+=1
    if damage == 'path':receipt['logical_path']=str(raw)+'foreign'
    sidecar=Path(str(archive)+'.archive_receipt.json');sidecar.write_text(json.dumps(receipt))
    if damage == 'receipt':sidecar.unlink()
    if damage == 'new_source':raw.with_name(raw.stem+'.late.jsonl').write_text('{}\n')
    if damage == 'bytes':archive.write_bytes(gzip.compress(b'changed'))
    if damage == 'symlink':raw.symlink_to(tmp_path/'absent')
    if damage:
        with pytest.raises((ValueError,OSError)):
            post.read_committed(tmp_path,'2026-10-12')
    else:
        result=post.read_committed(tmp_path,'2026-10-12',verify_full=True)
        assert result[1] == report
        assert post.handoff(tmp_path,'2026-10-13')[1]['status']=='verified_carried'


@pytest.mark.parametrize('damage', [None, 'ctime', 'self_digest', 'verification_contract', 'unknown_generation_field'])
def test_native_archiver_ctime_seal_survives_stop_and_future_handoff(tmp_path, damage):
    from src.engine.compress_db_backfilled_files import _gzip_file
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    _, report, _, raw = publication(tmp_path)
    assert _gzip_file(raw, dry_run=False)[0] is True
    archive = Path(str(raw) + '.gz')
    receipt_path = Path(str(archive) + '.archive_receipt.json')
    receipt = json.loads(receipt_path.read_bytes())
    assert 'ctime_ns' in receipt['archive_generation']
    if damage == 'ctime': receipt['archive_generation']['ctime_ns'] += 1
    elif damage == 'self_digest': receipt['artifact_content_sha256'] = '0' * 64
    elif damage == 'verification_contract': receipt['verification_contract'] = 'unverified'
    elif damage == 'unknown_generation_field': receipt['archive_generation']['future_unknown'] = 1
    if damage:
        if damage != 'self_digest':
            receipt['artifact_content_sha256'] = content_sha256({k:v for k,v in receipt.items() if k != 'artifact_content_sha256'})
        receipt_path.write_text(json.dumps(receipt))
        with pytest.raises((ValueError, OSError)):
            post.read_committed(tmp_path, '2026-10-12')
    else:
        assert post.read_committed(tmp_path, '2026-10-12', verify_full=True)[1] == report
        assert post.handoff(tmp_path, '2026-10-13')[1]['status'] == 'verified_carried'
