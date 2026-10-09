"""Main source lifecycle, immutable population and retired-command regressions.

Owned by existing runtime/postclose source consumers; isolated journals only.
"""
import copy
import gzip
import json
import threading
from pathlib import Path

import pytest

from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.scalping.micro_reversion import forward_collector as F
from src.engine.scalping.micro_reversion import path_journal as J
from src.engine.scalping.micro_reversion import canary_monitor as CM
from src.engine.scalping.micro_reversion.observation_adapter import ObserverFeatureFlags
from src.engine.scalping.micro_reversion.observer_source_quality import main_raw_epoch_validation
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_source as S
from src.trading.market.session_contract import market_source_partition_venue, market_source_session_bucket
from src.tests.test_micro_reversion_forward_collector import _snapshot, _depth_snapshot
from src.tests.test_reversal_operating_policy import parent, native, replay

DAY = '2026-10-07'


@pytest.fixture
def next_session_v6(replay, monkeypatch):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_policy_v5 as V5, continuous_reversal_policy_v6 as V6
    from src.engine.scalping import reversal_extended_registration as ER, reversal_extended_catalog as C
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.tests.test_reversal_operating_policy import authorize_initial, transport
    root, base, machine = replay
    O.prepare_inputs(root, DAY, machine, base)
    O.L.calls(O,root,DAY,transport=transport,call_limit=5)
    authorize_initial(root, base)
    auxiliary = O.auxiliary_report(root, DAY, DAY, base, publish_policy=False)
    issued = N._read(O.directory(root, DAY)/'machine.json')
    old = V5.stage(root, DAY, DAY, issued, auxiliary, target_date='2026-10-08', release_commit='a'*40)
    changes = P.seal(dict(schema='main_extended_registration_request_v1', kind='ADD',
        parent_bundle_sha256=old['bundle_sha256'], operator_receipt=ER.AUTHORITY,
        research_batch_sha256=C.RESEARCH_BATCH_SHA256, target_date='2026-10-12', source_receipts=[],
        scopes={d['symbol_group']+'|'+d['market']+'|'+d['price_band']+'|'+d['route']:dict(add=[bid],remove=[])
                for bid,d in C.NEW_DEFINITIONS.items()},
        definition_hashes={bid:P.digest(C.definition(bid)) for bid in C.NEW_DEFINITIONS}))
    P.write(ER.pending_path(root), changes)
    monkeypatch.setattr(N, 'load_effective', lambda **kwargs:old)
    source = P.seal(dict(normalized_sources=dict(partitions=[])))
    machine = O.machine_report(root,'2026-10-08','2026-10-08',old,source=source,publish_outputs=False)
    O.prepare_inputs(root,'2026-10-08',machine,old)
    auxiliary = O.auxiliary_report(root,'2026-10-08','2026-10-08',old,publish_policy=False)
    issued = N._read(O.directory(root,'2026-10-08')/'machine.json')
    candidate = V6.stage(root,'2026-10-08','2026-10-08',issued,auxiliary,target_date='2026-10-12',release_commit='a'*40)
    P.write(N.root(root)/'current.json', dict(bundle_sha256=old['bundle_sha256']))
    return root, old, candidate


def test_v6_code_refresh_preserves_issued_policy_and_current_until_exact_activation(next_session_v6, monkeypatch):
    from types import SimpleNamespace
    from datetime import datetime
    from src.engine.scalping import continuous_reversal_policy_v6 as V6, mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import runtime_release_router as router
    root, active, original = next_session_v6
    candidate_path = N.root(root)/'candidates/policy_2026-10-12.json'
    before = (N.root(root)/'current.json').read_bytes()
    source_before = {p:p.read_bytes() for p in (N.root(root)/'sources').glob('*.json')}
    pin = root/'new-code.py';pin.write_text('# New reviewed common dependency\n')
    modules = V6.contract_modules()
    monkeypatch.setattr(V6, 'contract_modules', lambda:(*modules,SimpleNamespace(__file__=str(pin))))
    original_validate = V6.validate_sources
    origins = []
    def validate(bundle, data_root, *, code_root=None):
        if code_root is not None:
            origins.append(code_root)
            assert bundle == original
            return bundle  # The origin subprocess boundary has separate tests.
        return original_validate(bundle, data_root)
    monkeypatch.setattr(V6, 'validate_sources', validate)
    monkeypatch.setattr(router, '_release_identity', lambda *args:{'source_integrity':'git_commit_and_clean_runtime_source'})
    historical = []
    def load_historical(*args, **kwargs):
        historical.append(kwargs['origin_root']);assert kwargs['origin_commit']=='a'*40;return active
    monkeypatch.setattr(V6, '_attested_activation_parent', load_historical)
    kwargs = dict(expected_bundle_sha256=original['bundle_sha256'],origin_root=root/'origin',
        activation_parent_origin_root=root/'active-origin',activation_parent_origin_commit='a'*40,release_commit='b'*40,
        reason='common_source_import_equivalence',confirm=V6.CODE_REFRESH_AUTHORITY,
        now=datetime.fromisoformat('2026-10-09T12:00:00+09:00'))
    with pytest.raises(ValueError, match='authority'):
        V6.stage_code_refresh(root,'2026-10-12',**dict(kwargs,confirm='invalid'))
    with pytest.raises(ValueError, match='future_candidate_required'):
        V6.stage_code_refresh(root,'2026-10-12',**dict(kwargs,now=datetime.fromisoformat('2026-10-12T07:30:00+09:00')))
    source_path = N.root(root)/'sources'/(original['source_file_sha256']+'.json')
    source_bytes = source_path.read_bytes()
    source_path.write_bytes(b'{}\n')
    with pytest.raises(ValueError,match='source_hash_invalid'):
        V6.stage_code_refresh(root,'2026-10-12',**kwargs)
    assert (N.root(root)/'current.json').read_bytes() == before
    source_path.write_bytes(source_bytes)
    refreshed = V6.stage_code_refresh(root,'2026-10-12',**kwargs)
    assert (N.root(root)/'current.json').read_bytes() == before
    assert all(p.read_bytes() == content for p,content in source_before.items())
    assert N._read(candidate_path) == refreshed and origins == [root/'origin']
    assert historical == [root/'active-origin']
    assert refreshed['bundle_sha256'] != original['bundle_sha256']
    assert V6._behavioral_family(refreshed['continuous_reversal']) == V6._behavioral_family(original['continuous_reversal'])
    original_validate(refreshed, root)
    unchanged = {p:p.read_bytes() for p in N.root(root).rglob('*.json')}
    assert V6.stage_code_refresh(root,'2026-10-12',**dict(kwargs,expected_bundle_sha256=refreshed['bundle_sha256'])) == refreshed
    assert unchanged == {p:p.read_bytes() for p in N.root(root).rglob('*.json')}
    assert origins == [root/'origin']
    with pytest.raises(ValueError, match='cas_failed'):
        V6.stage_code_refresh(root,'2026-10-12',**kwargs)
    tampered = copy.deepcopy(refreshed)
    cell = next(iter(tampered['continuous_reversal']['auxiliary_cells'].values()))
    next(iter(cell['routes'].values()))['payload']['arm'] = 'changed'
    with pytest.raises(ValueError, match='policy_changed'):
        V6._validate_code_refresh(tampered,root)
    pin.write_text('# Unreviewed bytes\n')
    with pytest.raises(ValueError, match='contract_code_changed'):
        original_validate(refreshed,root)
    pin.write_text('# New reviewed common dependency\n')
    monkeypatch.setattr(router,'selected_release',lambda *args:(root/'new-release','b'*40))
    def corrupt_current(**kwargs):
        raise ValueError('machine_bundle_source_hash_invalid')
    monkeypatch.setattr(N,'load_effective',corrupt_current)
    with pytest.raises(ValueError,match='source_hash_invalid'):
        V6.activate(root,'2026-10-12',now=datetime.fromisoformat('2026-10-12T07:35:00+09:00'))
    assert (N.root(root)/'current.json').read_bytes() == before
    def effective(**kwargs):
        if N._read(N.root(root)/'current.json')['bundle_sha256'] == refreshed['bundle_sha256']:
            return refreshed
        raise ValueError('v4_contract_code_changed:session_contract.py')
    monkeypatch.setattr(N,'load_effective',effective)
    out = V6.activate(root,'2026-10-12',now=datetime.fromisoformat('2026-10-12T07:35:00+09:00'))
    assert out['status'] == 'activated' and out['previous_bundle_sha256'] == active['bundle_sha256']
    assert historical[-1] == str((root/'active-origin').resolve())


@pytest.fixture(autouse=True)
def isolated_event_bus(monkeypatch):
    from src.core.event_bus import EventBus
    from src.engine import kiwoom_websocket as WS
    monkeypatch.setattr(EventBus,'_instance',None)
    bus=EventBus()
    monkeypatch.setattr(WS,'EventBus',lambda:bus)


def collect(tmp_path, *, depth=False, timestamp=None):
    c = F.ForwardObservationCollector(flags=ObserverFeatureFlags(observer_enabled=True,path_capture_enabled=True,depth_capture_enabled=depth),
        config=F.ForwardCollectorConfig(output_root=tmp_path,writer_flush_interval_sec=.005,worker_poll_interval_sec=.005))
    c.start()
    stamp = timestamp or int(__import__('datetime').datetime.fromisoformat(DAY+'T09:00:00.010+09:00').timestamp()*1000)
    c.observe_kiwoom_0b('000001', _snapshot(received_at_ms=stamp),realtime_type='0B')
    if depth:c.observe_kiwoom_0d('000001', _depth_snapshot(received_at_ms=stamp),realtime_type='0D')
    c.close()
    return c


def payload(c):
    snap=c.runtime_snapshot().as_dict()
    guard=CM.evaluate_canary_snapshot(snap,CM.load_canary_guard())
    return dict(generated_at=DAY+'T20:10:00+09:00',collector_snapshot=snap,canary_guard=guard)


def test_runtime_raw_never_instantiates_retired_detector_or_references(tmp_path,monkeypatch):
    monkeypatch.setattr(F,'MultiHorizonShockDetector',lambda:pytest.fail('retired detector instantiated'))
    c=collect(tmp_path,depth=True);snap=c.runtime_snapshot().as_dict()
    assert c._detector is None
    assert not c._ring._points and c._ring._last_sequence
    assert snap['raw_reconciliation_completed'] is True
    assert snap['reference_reconciliation_completed'] is None
    assert snap['shock_event_count'] is None
    assert not list(tmp_path.rglob('*references*'))
    assert snap['enqueued_count']==snap['worker_processed_count']==snap['writer_persisted_envelope_count']==1
    assert snap['depth_enqueued_count']==snap['depth_writer_persisted_envelope_count']==1
    assert payload(c)['canary_guard']['status']=='stopped_clean'
    assert main_raw_epoch_validation(payload(c),source_date=DAY)['eligible'] is True


def test_raw_ordering_without_history_matches_archive_quality_and_resets():
    from src.tests.test_micro_reversion_path_capture import _envelope
    from src.engine.scalping.micro_reversion.path_capture import PreEventRingBuffer
    raw = PreEventRingBuffer(retain_observations=False)
    archive = PreEventRingBuffer()
    rows = [_envelope(1,0), _envelope(1,0), _envelope(3,10), _envelope(2,11),
            _envelope(4,9), _envelope(5,12)]
    for row in rows:
        assert raw.order_assessment(row) == archive.order_assessment(row)
        assert raw.add(row) == archive.add(row)
        assert raw.counters() == archive.counters()
    assert not raw._points and archive._points
    raw.drop_symbol(rows[0].symbol)
    assert not raw._last_sequence and not raw._last_timestamp_ms and not raw._last_receive_timestamp_ms
    assert raw.add(rows[0])
    assert raw.reset_transport_epoch() == 0 and not raw._last_sequence


@pytest.mark.parametrize('kind', ['0B', '0D'])
def test_writer_start_does_not_block_producer_or_shutdown_drain(tmp_path, monkeypatch, kind):
    entered, release, accepted = threading.Event(), threading.Event(), threading.Event()
    observed = threading.Event()
    original = J.NonBlockingPathJournalWriter.start
    def slow_start(writer):
        entered.set()
        assert release.wait(5)
        original(writer)
    monkeypatch.setattr(J.NonBlockingPathJournalWriter, 'start', slow_start)
    c = F.ForwardObservationCollector(
        flags=ObserverFeatureFlags(observer_enabled=True, path_capture_enabled=True, depth_capture_enabled=True),
        config=F.ForwardCollectorConfig(output_root=tmp_path, writer_flush_interval_sec=.005, worker_poll_interval_sec=.005))
    c.start()
    observe = c.observe_kiwoom_0b if kind == '0B' else c.observe_kiwoom_0d
    snapshot = _snapshot if kind == '0B' else _depth_snapshot
    errors = []
    def producer():
        try:
            observe('000001', snapshot(), realtime_type=kind)
            accepted.set()
        except Exception as exc:
            errors.append(exc)
    worker = threading.Thread(target=producer)
    diagnostic = threading.Thread(target=lambda: (c.runtime_snapshot(), observed.set()))
    try:
        observe('000001', snapshot(), realtime_type=kind)
        assert entered.wait(5)
        worker.start()
        diagnostic.start()
        # This is synchronization, not a scheduler-dependent millisecond gate:
        # the callback must finish while writer.start is deliberately blocked.
        assert accepted.wait(2)
        assert observed.wait(2)
        with pytest.raises(RuntimeError, match='shutdown'):
            c.close(timeout_sec=.01)
        assert c._writers_closing is False
    finally:
        release.set()
        if worker.ident is not None:
            worker.join(5)
        if diagnostic.ident is not None:
            diagnostic.join(5)
        c.close(timeout_sec=10)
    assert not errors and not worker.is_alive()
    snap = c.runtime_snapshot()
    count = snap.writer_persisted_envelope_count if kind == '0B' else snap.depth_writer_persisted_envelope_count
    assert count == 2 and snap.raw_reconciliation_completed is True


@pytest.mark.parametrize('fault',['writer_error_count','observation_queue_full_count','depth_writer_error_count','raw_reconciliation_error_count','unsupported','unaccounted_exclusion','close_failed','wrong_date'])
def test_raw_epoch_receipt_never_approves_loss_or_unknown_contract(tmp_path,fault):
    value=payload(collect(tmp_path,depth=True))
    if fault=='unsupported':value['collector_snapshot']['source_contract']='unknown'
    elif fault=='unaccounted_exclusion':value['canary_guard']['raw_row_exclusion_required']=True
    elif fault=='close_failed':value['collector_snapshot']['collector_lifecycle']='close_failed'
    elif fault=='wrong_date':value['generated_at']='2026-10-08T20:00:00+09:00'
    else:value['collector_snapshot'][fault]=1
    assert main_raw_epoch_validation(value,source_date=DAY)['eligible'] is False


@pytest.mark.parametrize('venue,item',[('KRX','000001'),('NXT','000001_NX'),('SOR','000001_AL')])
def test_receive_exchange_session_boundary_preserves_original_mapping(venue,item):
    from datetime import time
    assert market_source_partition_venue(item)==venue
    assert market_source_session_bucket(venue,time(8,59,59))==venue+'_PREMARKET'
    assert market_source_session_bucket(venue,time(9))==('NXT_REGULAR_OVERLAP' if venue=='NXT' else venue+'_REGULAR')
    assert market_source_session_bucket(venue,time(15,30))==venue+'_AFTERMARKET'
    assert market_source_session_bucket(venue,time(0))==venue+'_PREMARKET'


def test_common_wall_clock_mapping_matches_legacy_for_every_minute():
    from datetime import time,timezone
    for venue in ('KRX','NXT','SOR','UNKNOWN'):
        prefix=venue if venue in ('SOR','NXT') else 'KRX'
        for minute in range(1440):
            clock=time(minute//60,minute%60,59,999999,tzinfo=timezone.utc)
            expected=prefix+('_PREMARKET' if minute<540 else '_REGULAR_OVERLAP' if minute<930 and venue=='NXT' else '_REGULAR' if minute<930 else '_AFTERMARKET')
            assert market_source_session_bucket(venue,clock)==expected


def test_batched_percentiles_preserve_all_original_ranks():
    from src.engine.scalping.micro_reversion.observation_adapter import _percentiles
    for values in ((), (1.23456789,), tuple((i * 173 % 4099) / 19 for i in range(4096))):
        expected = tuple(round(sorted(values)[round((len(values)-1)*p/100)], 6)
                         if values else 0.0 for p in (50, 95, 99))
        assert _percentiles(values, (50, 95, 99)) == expected


@pytest.mark.parametrize('origin_valid', [False, True])
def test_v4_historical_pin_inventory_is_checked_by_attested_origin(parent, tmp_path, monkeypatch, origin_valid):
    import subprocess
    from src.engine.scalping import continuous_reversal_policy_v4 as V4
    from src.engine.infrastructure import runtime_release_router as router
    root, bundle = parent
    origin = tmp_path / 'origin'
    origin.mkdir()
    seen = []
    def identity(*args):
        assert args[-1] == bundle['continuous_reversal']['release_commit']
        return {'source_integrity': 'git_commit_and_clean_runtime_source'}
    monkeypatch.setattr(router, '_release_identity', identity)
    monkeypatch.setattr(V4, 'contract_modules', lambda: pytest.fail('current pin inventory used for origin'))
    def invoke(args, **kwargs):
        seen.append((args, kwargs))
        assert kwargs['cwd'] == origin
        assert kwargs['env']['PYTHONPATH'] == str(origin)
        assert json.loads(kwargs['input']) == bundle
        assert kwargs['check'] is True and kwargs['timeout'] == 120
        if not origin_valid:
            raise subprocess.CalledProcessError(1, args, stderr='v4_report_snapshot_changed')
    monkeypatch.setattr(subprocess, 'run', invoke)
    if origin_valid:
        assert V4.validate_sources(bundle, root, code_root=origin) == bundle
    else:
        with pytest.raises(subprocess.CalledProcessError):
            V4.validate_sources(bundle, root, code_root=origin)
    assert len(seen) == 1


@pytest.mark.parametrize('failure', ['dirty_origin', 'source_rejected', 'no_current', None])
def test_code_refresh_parent_uses_full_strict_old_release_validator(parent, tmp_path, monkeypatch, failure):
    import subprocess
    from types import SimpleNamespace
    from src.engine.scalping import continuous_reversal_policy_v6 as V6
    from src.engine.infrastructure import runtime_release_router as router
    root, bundle = parent
    origin = tmp_path/'old-reviewed-release';origin.mkdir()
    calls = []
    def identity(*args):
        assert args[-1] == 'c'*40  # The reviewed container may postdate the policy.
        return {'source_integrity':'dirty' if failure == 'dirty_origin' else 'git_commit_and_clean_runtime_source'}
    def invoke(args, **kwargs):
        calls.append(args)
        assert 'historical_code_root' not in args[2]
        assert '_load_current_uncached' in args[2]
        assert kwargs['check'] is True and kwargs['cwd'] == origin
        if failure == 'source_rejected':raise subprocess.CalledProcessError(1,args)
        return SimpleNamespace(stdout='none\n' if failure == 'no_current' else bundle['bundle_sha256']+'\n')
    monkeypatch.setattr(router,'_release_identity',identity)
    monkeypatch.setattr(subprocess,'run',invoke)
    kwargs=dict(origin_root=origin,origin_commit='c'*40)
    if failure is not None:
        with pytest.raises((ValueError,subprocess.CalledProcessError)):
            V6._attested_activation_parent(root,'2026-10-12',**kwargs)
    else:
        assert V6._attested_activation_parent(root,'2026-10-12',**kwargs) == bundle
    assert len(calls) == (0 if failure == 'dirty_origin' else 1)


@pytest.mark.parametrize('item',['005930','005930_NX','005930_AL'])
def test_retired_manifest_cannot_replace_main_route_or_schedule_deferred_reg(item):
    manager=KiwoomWSManager('unused')
    manager.subscribed_codes.add('005930');manager._registered_items_by_code['005930']=(item,)
    manager._exact_probe_item_leases[item]={'lease_id':'main-original'}
    before=copy.deepcopy(manager._registered_items_by_code)
    manager.execute_subscribe=lambda *a,**k:pytest.fail('retired command registered')
    manager.execute_unsubscribe=lambda *a,**k:pytest.fail('retired command removed')
    assert manager._configure_micro_reversion_observation_items(['196170_AL'],source='old') is False
    assert manager._handle_micro_reversion_observation_set({'registration_items':['196170_AL']}) is False
    assert manager.retain_micro_reversion_as_observation_only('005930') is False
    assert manager._defer_missing_micro_registration(['005930'],source='old') is None
    assert manager._registered_items_by_code==before
    assert manager._exact_probe_item_leases[item]['lease_id']=='main-original'


def test_main_receipt_requires_requested_type_and_resets_on_transport_epoch():
    manager=KiwoomWSManager('unused');manager._market_data_transport_epoch=7
    with manager.lock:
        manager._record_main_source_registration_locked('005930_AL',['0B'],source='scanner_main')
        manager._record_micro_reversion_registration_receipt(item='005930_AL',realtime_type='0D',observed_at_epoch=1)
    snap=manager._finish_main_source_registration_receipt(copy.deepcopy(manager._micro_reversion_registration_receipt),{'005930_AL'})
    assert snap['items']['005930_AL']['source_status']=='awaiting_first_type'
    assert snap['broker_ack_observed'] is None
    with manager.lock:manager._record_micro_reversion_registration_receipt(item='005930_AL',realtime_type='0B',observed_at_epoch=2)
    snap=manager._finish_main_source_registration_receipt(copy.deepcopy(manager._micro_reversion_registration_receipt),{'005930_AL'})
    assert snap['items']['005930_AL']['source_status']=='received'
    assert snap['summary']['connection_rate']==1
    manager._market_data_transport_epoch=8
    with manager.lock:manager._record_main_source_registration_locked('005930_AL',['0B','0D'],source='reconnect')
    assert manager._micro_reversion_registration_receipt['items']['005930_AL']['received_realtime_types']==[]


def test_retired_observation_only_probe_never_wakes_main_exit(tmp_path):
    manager=KiwoomWSManager('unused');seen=[];manager._fast_exit_wakeup=seen.append
    manager._micro_reversion_observation_only_codes.add('000001')
    manager._queue_tick_event('000001',_snapshot(),observation_only=True)
    assert seen==[] and not manager._pending_tick_events
    manager._queue_tick_event('000001',_snapshot(),observation_only=False)
    assert seen==['000001'] and '000001' in manager._pending_tick_events


def test_writer_single_encoding_has_identical_bytes_and_retains_partial_write_handling(tmp_path,monkeypatch):
    from src.tests.test_micro_reversion_path_capture import _envelope
    from src.engine.scalping.micro_reversion.path_capture import to_market_stream_point
    point=to_market_stream_point(_envelope(1,0));expected=(json.dumps(point.as_dict(),ensure_ascii=False,sort_keys=True)+'\n').encode()
    calls=[];old=type(point).as_dict
    monkeypatch.setattr(type(point),'as_dict',lambda self:(calls.append(1),old(self))[1])
    writer=J.NonBlockingPathJournalWriter(tmp_path/'stream.jsonl',max_batch_size=1,flush_interval_sec=.005)
    original_write=J.os.write
    monkeypatch.setattr(J.os,'write',lambda fd,buf:original_write(fd,buf[:max(1,len(buf)//2)]))
    writer.start();assert writer.submit(point);writer.close()
    assert (tmp_path/'stream.jsonl').read_bytes()==expected
    # Manifest encoding is separate from the one market-row encoding.
    assert sum(1 for line in (tmp_path/'stream.jsonl').read_text().splitlines())==1
    assert len(calls)==1
    assert writer.metrics().persisted_envelope_count==1


def test_new_raw_freezer_requires_exact_closed_epoch_and_preserves_all_rows(tmp_path):
    data=tmp_path/'data';raw=data/'observations/scalp_micro_reversion_forward'
    c=collect(raw);value=payload(c)
    receipt=data/'runtime/scalp_micro_reversion_forward_collector/latest.json';receipt.parent.mkdir(parents=True);receipt.write_text(json.dumps(value))
    outputs=S.freeze_normalized_sources(data,DAY,tmp_path/'valid')
    body=json.loads(gzip.decompress(Path(outputs[0]['path']).read_bytes()))
    assert body['symbols']['000001'][0][8]==1
    assert body['source_quality_receipt']['allowed_sequence_epoch']==c._sequence_epoch
    value['collector_snapshot']['sequence_epoch']+=1;receipt.write_text(json.dumps(value))
    outputs=S.freeze_normalized_sources(data,DAY,tmp_path/'wrong')
    body=json.loads(gzip.decompress(Path(outputs[0]['path']).read_bytes()))
    assert len(body['symbols']['000001'])==1 and body['symbols']['000001'][0][8]==0


def test_population_warm_resume_validates_hashes_without_reparse_and_explicit_generation_never_falls_back(tmp_path,monkeypatch):
    data=tmp_path/'data';source=P.ensure_population(data,DAY)
    before=(P.directory(data,DAY)/'source.json').read_bytes()
    monkeypatch.setattr(S,'freeze_normalized_sources',lambda *a:pytest.fail('same source reparsed'))
    assert P.ensure_population(data,DAY)==source
    with pytest.raises(ValueError,match='generation_missing'):P.ensure_population(data,DAY,source_generation='new',expected_sha256='a'*64)
    with pytest.raises(ValueError,match='generation_invalid'):P.ensure_population(data,DAY,source_generation='../escape')
    assert (P.directory(data,DAY)/'source.json').read_bytes()==before
    bad=dict(source,new_raw_partition_count=999);P.write(P.directory(data,DAY)/'source.json',bad)
    with pytest.raises(ValueError,match='manifest_invalid'):P.ensure_population(data,DAY)


def test_explicit_population_generation_isolated_from_original_and_locked_for_concurrent_resume(tmp_path):
    data=tmp_path/'data';original=P.ensure_population(data,DAY);old=(P.directory(data,DAY)/'source.json').read_bytes()
    newer=P.ensure_population(data,DAY,source_generation='source-v2')
    assert original['artifact_content_sha256']!=newer['artifact_content_sha256']
    values=[];errors=[]
    def resume():
        try:values.append(P.ensure_population(data,DAY,source_generation='source-v2',expected_sha256=newer['artifact_content_sha256']))
        except Exception as exc:errors.append(exc)
    threads=[threading.Thread(target=resume) for _ in range(3)]
    for t in threads:t.start()
    for t in threads:t.join(2)
    assert not errors and values==[newer]*3
    assert (P.directory(data,DAY)/'source.json').read_bytes()==old


@pytest.mark.parametrize('item,route,key',[('000001_AL','krx_nxt_integrated','_AL|krx_nxt_integrated'),('000001_NX','nxt_only','_NX|nxt_only'),('000001','krx_only','KRX|krx_only')])
def test_main_callback_keeps_native_namespace_separate_from_collector_epoch(tmp_path,item,route,key):
    c=F.ForwardObservationCollector(flags=ObserverFeatureFlags(observer_enabled=True,path_capture_enabled=True,depth_capture_enabled=True),config=F.ForwardCollectorConfig(output_root=tmp_path))
    c.start();manager=KiwoomWSManager('unused');manager._micro_reversion_forward_collector=c
    stamp=int(__import__('datetime').datetime.fromisoformat(DAY+'T09:00:00.010+09:00').timestamp()*1000)
    venue=market_source_partition_venue(item)
    for kind,factory in [('0B',_snapshot),('0D',_depth_snapshot)]:
        frame=factory(item=item,venue=venue,received_at_ms=stamp)
        frame['last_trade_tick' if kind=='0B' else 'last_depth_tick'].update(transport_epoch=7,route_sequence=19)
        frame['realtime_type_snapshots_by_route']={key:{kind:dict(transport_epoch=7,route_sequence=19)}}
        manager._queue_tick_event('000001',frame,realtime_type=kind,observation_only=True)
    c.close()
    rows=[json.loads(line) for p in tmp_path.rglob('*.jsonl') for line in p.read_text().splitlines()]
    assert len(rows)==2
    assert all(r['native_transport_epoch']==7 and r['native_route_sequence']==19 and r['sequence_epoch']!=7 for r in rows)
    assert manager._micro_reversion_forward_collector_error==''


def test_closed_receipt_survives_later_boot_and_binds_all_reconciled_transport_segments(tmp_path):
    import time
    c=F.ForwardObservationCollector(flags=ObserverFeatureFlags(observer_enabled=True,path_capture_enabled=True),config=F.ForwardCollectorConfig(output_root=tmp_path/'data/observations/scalp_micro_reversion_forward'))
    c.start();stamp=int(__import__('datetime').datetime.fromisoformat(DAY+'T09:00:00.010+09:00').timestamp()*1000)
    c.observe_kiwoom_0b('000001',_snapshot(received_at_ms=stamp),realtime_type='0B')
    deadline=time.monotonic()+2
    while c.runtime_snapshot().worker_processed_count!=1 and time.monotonic()<deadline:time.sleep(.005)
    first=c._sequence_epoch;c.begin_transport_epoch()
    c.observe_kiwoom_0b('000001',_snapshot(received_at_ms=stamp+1000),realtime_type='0B');c.close()
    assert set(c.runtime_snapshot().reconciled_sequence_epochs)=={first,c._sequence_epoch}
    latest=tmp_path/'data/runtime/scalp_micro_reversion_forward_collector/latest.json'
    from datetime import datetime
    CM.write_canary_runtime_snapshot(c.runtime_snapshot().as_dict(),output_path=latest,now=datetime.fromisoformat(DAY+'T20:10:00+09:00'))
    original=next((latest.parent/'closed').glob('*.json')).read_bytes()
    latest.write_text(json.dumps(dict(generated_at=DAY+'T20:20:00+09:00',collector_snapshot=dict(source_contract='main_market_source_v1',collector_lifecycle='running'))))
    frozen=S.freeze_normalized_sources(tmp_path/'data',DAY,tmp_path/'freeze')
    body=json.loads(gzip.decompress(Path(frozen[0]['path']).read_bytes()))
    assert len(body['symbols']['000001'])==2 and all(r[8]==1 for r in body['symbols']['000001'])
    assert next((latest.parent/'closed').glob('*.json')).read_bytes()==original


def test_freezer_rejects_conflicting_compressed_alias_and_accepts_identical_archive(tmp_path):
    c=collect(tmp_path/'data/observations/scalp_micro_reversion_forward')
    path=next((tmp_path/'data').rglob('market_stream.jsonl'))
    archive=path.with_suffix(path.suffix+'.gz');archive.write_bytes(gzip.compress(path.read_bytes()))
    assert len(S.discover(tmp_path/'data',DAY)[0]['files'])==1
    archive.write_bytes(gzip.compress(path.read_bytes()+b'{}\n'))
    with pytest.raises(ValueError,match='alias_conflict'):S.discover(tmp_path/'data',DAY)


def test_selected_generation_receipt_and_invalid_cli_do_not_mutate_sources(tmp_path,monkeypatch):
    source=P.ensure_population(tmp_path,DAY,source_generation='gen-2');receipt=P.population_receipt(source)
    assert receipt['source_generation']=='gen-2' and receipt['sha256']==P.file_hash(source['source_manifest_path'])
    monkeypatch.setattr(P,'ensure_population',lambda *a,**k:pytest.fail('invalid CLI created source'))
    with pytest.raises(SystemExit):P.main(['--date',DAY,'--source-generation','gen-3','--evaluate-only'])
    with pytest.raises(SystemExit):P.main(['--date',DAY,'--source-generation','gen-3','--seed-research','unused'])


def test_frozen_generation_rejects_changed_partition(tmp_path):
    data=tmp_path/'data';collect(data/'observations/scalp_micro_reversion_forward')
    source=P.ensure_population(data,DAY);partition=Path(source['normalized_sources']['partitions'][0]['path'])
    partition.write_bytes(partition.read_bytes()+b'corrupt')
    with pytest.raises(ValueError,match='frozen_source_changed'):P.ensure_population(data,DAY)


def test_common_helper_is_policy_pinned_and_tamper_fails_closed(parent,tmp_path,monkeypatch):
    from src.engine.scalping import continuous_reversal_policy_v4 as V4
    from src.engine.scalping import continuous_reversal_policy_v5 as V5
    from src.engine.scalping import continuous_reversal_policy_v6 as V6
    from src.trading.market import session_contract as COMMON
    root,bundle=parent
    assert all(COMMON in version.contract_modules() for version in (V4,V5,V6))
    assert bundle['continuous_reversal']['contract_file_sha256']['session_contract.py']==P.file_hash(COMMON.__file__)
    changed=tmp_path/'session_contract.py';changed.write_bytes(Path(COMMON.__file__).read_bytes()+b'\n# altered mapping\n')
    monkeypatch.setattr(COMMON,'__file__',str(changed))
    with pytest.raises(ValueError,match='contract_code_changed:session_contract.py'):V4.validate_sources(bundle,root)


def test_native_reader_consumes_main_closed_raw_without_retired_references(tmp_path):
    from datetime import datetime
    from src.engine.scalping import native_packet_validation as N
    data=tmp_path/'data';raw=data/'observations/scalp_micro_reversion_forward'
    c=collect(raw,depth=True)
    receipt=data/'runtime/scalp_micro_reversion_forward_collector/latest.json'
    at=datetime.fromisoformat(DAY+'T20:10:00+09:00')
    CM.write_canary_runtime_snapshot(c.runtime_snapshot().as_dict(),output_path=receipt,now=at)
    summary,inventory,_=N._micro_context(DAY,raw,{'000001'},[],N.DEFAULT_SOURCE_EXCLUSION_MANIFEST,receipt,at)
    assert summary['canary_source_quality']['main_raw_epoch_validation']['eligible'] is True
    assert inventory['000001']['observed_row_count']==1 and inventory['000001']['depth_row_count']==1
    assert summary['unverified_canary_epoch_row_count']==0


@pytest.mark.parametrize('epochs',[1,'invalid',{'epoch':1},[1,[]]])
def test_malformed_closed_epoch_receipt_does_not_crash_or_override_conflicting_proof(tmp_path,epochs):
    from datetime import datetime
    data=tmp_path/'data';raw=data/'observations/scalp_micro_reversion_forward'
    c=collect(raw)
    receipt=data/'runtime/scalp_micro_reversion_forward_collector/latest.json'
    value=CM.write_canary_runtime_snapshot(c.runtime_snapshot().as_dict(),output_path=receipt,
        now=datetime.fromisoformat(DAY+'T20:10:00+09:00'))
    value['collector_snapshot']['reconciled_sequence_epochs']=epochs
    receipt.write_text(json.dumps(value))
    quality=S._source_quality_receipt(data,DAY)
    assert quality['eligible'] is False
    assert c._sequence_epoch in quality['denied_sequence_epochs']


def test_warm_operating_replay_reuses_derived_points_without_provider_calls(replay,monkeypatch):
    from src.engine.scalping import continuous_reversal_operating_postclose as PC
    from src.engine.ai import offline_comparison_store as STORE
    root,bundle,first=replay
    rec=first['partitions'][0]['normalized_source']
    source=P.seal(dict(normalized_sources=dict(partitions=[rec])))
    monkeypatch.setattr(PC.R.State,'observe',lambda *a,**k:pytest.fail('cached source recalculated'))
    monkeypatch.setattr(PC.LIVE,'snapshot',lambda *a,**k:pytest.fail('cached native input recalculated'))
    second=PC.machine_report(root,DAY,DAY,bundle,source=source)
    assert second['partitions']==first['partitions']
    assert second['proposal_metrics']==first['proposal_metrics']
    with STORE.Store(root) as store:
        assert store.db.execute('select count(*) from requests').fetchone()[0]==0
