"""Producer-sealed legacy projection streaming and native-path parity."""
import json
import pytest
from src.engine.lifecycle.research_json_stream import Reader,completed_rows
from src.engine.lifecycle import research_storage as storage
from src.tests.test_main_all_scope_trailing import position,quote
from src.engine.automation import main_trailing_source_assembler as source
from src.engine.automation import main_trailing_all_scope_research as owner
from src.tests.test_main_trailing_source_assembler import fixture,DAY,TARGET


def test_resident_native_projection_matches_legacy_stream_without_raw_read(tmp_path):
    from src.engine.lifecycle.research_json_stream import resident_completed_rows
    row=dict(id='native',strategy='SCALPING',status='COMPLETED',stock_code='123456',
        buy_fill_legs=[dict(at=DAY+'T09:00:00',qty=2,amount_krw=200)],
        sell_fill_legs=[dict(at=DAY+'T09:01:00',qty=2,amount_krw=202)],
        timeline=[dict(stage='scalp_trailing_input_transition',fields={
            'universal_trailing_quote':quote(1,DAY+'T09:00:01')})],
        unused_display='x'*100000)
    path=tmp_path/'legacy.json';path.write_text(json.dumps({'sections':{'completed_trade_projection':[row]}}))
    old=list(completed_rows(path,tmp_path/'old'))
    new=list(resident_completed_rows([row],tmp_path/'new'))
    assert storage.logical_value(old)==storage.logical_value(new)


def test_stream_keeps_every_timeline_and_fill_without_large_display_fields(tmp_path):
    event={'stage':'scalp_trailing_input_transition','fields':{'universal_trailing_quote':json.dumps(quote(1,DAY+'T09:00:01'))}}
    trade={'id':'main:1','strategy':'SCALPING','buy_filled_qty':10,'buy_fill_amount':1000,'irrelevant':'x'*(5*1024*1024),'buy_fill_legs':[{'at':DAY+'T09:00:00','qty':10,'amount_krw':1000}],
        'sell_fill_legs':[{'at':DAY+'T09:00:01'}],'timeline':[event]}
    path=tmp_path/'source.json';path.write_text(json.dumps({'meta':{'unused':[1,2]},'sections':{'completed_trade_projection':[trade]}}))
    rows=list(completed_rows(path,tmp_path/'out'));body,events=rows[0]
    assert len(rows)==1 and body['id']=='main:1' and 'irrelevant' not in body
    assert body['buy_filled_qty'] == 10 and body['buy_fill_amount'] == 1000
    assert list(storage.iter_tree(tmp_path/'out',events))==[quote(1,DAY+'T09:00:01')]
    assert list(storage.iter_tree(tmp_path/'out',body['buy_fill_legs_ref']))==trade['buy_fill_legs']


def test_stream_preserves_signal_receipts_and_strict_admission_fields(tmp_path):
    signal=dict(stage='holding_path_signal_snapshot',fields=dict(path_id='ADD_REBOUND',
        signal_id='signal-1',buy_fill_identity='a'*64,decision='PASS',vote_count=2))
    trade=dict(id=7,status='COMPLETED',strategy='SCALPING',profit_rate=.2,
        strict_completion_status='eligible',strict_completion_reasons=[],rec_date=DAY,
        terminal_population_scope='real_record_bound',timeline=[signal])
    path=tmp_path/'source.json';path.write_text(json.dumps({'sections':{'completed_trade_projection':[trade]}}))
    body,_=next(completed_rows(path,tmp_path/'out'))
    assert body['strict_completion_status']=='eligible' and body['profit_rate']==.2
    signals=list(storage.iter_tree(tmp_path/'out',body['holding_path_signal_snapshots_ref']))
    assert signals[0]['fields']['signal_id']=='signal-1'
    assert signals[0]['fields']['buy_fill_identity']=='a'*64


@pytest.mark.parametrize('raw',['{"sections":{"completed_trade_projection":[{"id":"x","id":"y"}]}}',
    '{"sections":{"completed_trade_projection":[]}} trailing',
    '{"sections":{"completed_trade_projection":[{"timeline":['])
def test_incomplete_duplicate_or_trailing_source_cannot_publish(tmp_path,raw):
    path=tmp_path/'source.json';path.write_text(raw)
    with pytest.raises(ValueError):list(completed_rows(path,tmp_path/'out'))


def test_large_verified_completed_projection_is_automatically_assembled(tmp_path,monkeypatch):
    from src.engine.log_archive_service import _save_trade_review_completed_projection
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    root=tmp_path/'source';fixture(root);p=position()
    row=dict(id='main:1',strategy='SCALPING',status='COMPLETED',stock_code='123456',
        completion_observed_date=DAY,main_automatic_management_allowed=True,holding_ai_required=False,
        buy_fill_legs=[dict(at=DAY+'T09:00:00',qty=10,amount_krw=1000)],sell_fill_legs=[dict(at=DAY+'T09:00:01')],
        trailing_replay_cost_model=p['cost_model'],actual_cost_reconciliation=p['actual_cost_reconciliation'],
        timeline=[dict(stage='scalp_trailing_input_transition',fields={'universal_trailing_quote':quote(1,DAY+'T09:00:01')})],
        unused_display='x'*(5*1024*1024))
    report=dict(date=DAY,code=None,since=None,
        meta=dict(warnings=[],snapshot_profile='postclose_exit',sell_completed_event_ids=['main:1'],
            actual_cost_source_generation=source_generation(root,DAY)),
        sections=dict(completed_trade_projection=[row],open_scalp_position_projection=[]),
        metrics=dict(canonical_completed_trades=1))
    report['meta']['completed_census_manifest']=completed_census_manifest(report)
    raw=root/'report/monitor_snapshots'/f'trade_review_{DAY}.json';raw.parent.mkdir(parents=True);raw.write_text(json.dumps(report))
    _save_trade_review_completed_projection(raw,report)
    manifest=source.assemble(root,tmp_path/'assembly',source_date=DAY,target_date=TARGET,start_date=DAY)
    value=owner._sealed(manifest)
    assert value['population_ids_ref']['count']==3  # Actual, alternative, and native CF are separate.
    result=owner.run(manifest,input_root=tmp_path/'assembly',output_root=tmp_path/'out',dry_run=False)
    assert result['status']=='complete'
    from src.engine.automation.main_trailing_partitioned_research import checkpoint_results
    outcomes={}
    for reference in storage.iter_tree(tmp_path/'out',result['partition_results_ref']):
        checkpoint=owner._sealed(tmp_path/'out'/reference['path'])
        for part in checkpoint_results(checkpoint,tmp_path/'out'):
            parent=part['candidate_aliases']['incumbent']
            outcomes.update({identity:value[parent]['status'] for identity,value in part['minimal_results'].items()})
    assert outcomes['main:1']==outcomes['alternative:main:1']=='modeled_full_exit'
    from src.engine.holding_exit_observation_report import build_holding_exit_observation_report
    from src.engine import log_archive_service as archive
    holding=build_holding_exit_observation_report(target_date=DAY,input_root=root,all_scope_research=True,
        research_input_root=tmp_path/'normal-input',research_output_root=tmp_path/'normal-output')
    holding['meta']['snapshot_profile']='postclose_exit'
    monkeypatch.setattr(archive,'DATA_DIR',root)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',raw.parent)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_MANIFEST_DIR',raw.parent/'manifests')
    saved=archive.save_monitor_snapshot('holding_exit_observation',DAY,holding)
    manifest_path=archive.save_monitor_snapshot_manifest(DAY,profile='postclose_exit',
        snapshots={'trade_review':str(raw),'holding_exit_observation':str(saved)})
    assert json.loads(manifest_path.read_bytes())['input_window_generation_sha256']==holding['input_window_generation_sha256']
    from src.engine.scalping.holding_path_vote_policy import (
        create_bundle, source_quality_from_observation, validate_bundle,
    )
    quality = source_quality_from_observation(holding)
    assert quality['completed_population_complete'] is False
    assert quality['replay_cohort_status'] == 'sealed_partition_vote_inputs'
    assert quality['excluded_by_id']['main:1']
    assert quality['available_actual_population_count'] == 1
    assert quality['available_actual_population_ids_ref']['count'] == 1
    assert holding['holding_path_vote_replay']['economic_replay_observed'] is False
    import hashlib
    report_sha = hashlib.sha256(saved.read_bytes()).hexdigest()
    bundle = create_bundle(source_date=DAY, target_date=TARGET,
        source_report_sha256=report_sha, replay=holding['holding_path_vote_replay'],
        source_quality=quality)
    validate_bundle(bundle, target_date=TARGET, source_report_sha256=report_sha)
    assert bundle['source_quality']['strict_population_count'] == 0


def test_identifiable_oversized_field_isolated_and_next_trade_retained(tmp_path):
    path=tmp_path/'source.json'
    path.write_text(json.dumps({'sections':{'completed_trade_projection':[
        {'id':'bad','trailing_replay_cost_model':{'x':'x'*100000}}, {'id':'healthy'}]}}))
    rows=list(completed_rows(path,tmp_path/'out'))
    assert [r[0]['id'] for r in rows]==['bad','healthy']
    assert rows[0][0]['projection_source_gap']=='normalized_field_unbounded'
    assert 'projection_source_gap' not in rows[1][0]


@pytest.mark.parametrize('compressed',[False,True])
def test_original_stream_hashes_exact_utf8_and_crlf_without_second_read(tmp_path,compressed):
    import gzip,hashlib
    text=json.dumps({'sections':{'completed_trade_projection':[{'id':'unicode-가','status':'COMPLETED'}]}},ensure_ascii=False,indent=2)
    raw=text.replace('\n','\r\n').encode('utf-8');path=tmp_path/'original.json'
    if compressed:path.with_suffix('.json.gz').write_bytes(gzip.compress(raw))
    else:path.write_bytes(raw)
    generation=dict(path=path.name,size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    assert len(list(completed_rows(path,tmp_path/'out',expected_generation=generation)))==1
    with pytest.raises(ValueError,match='logical_generation_changed'):
        list(completed_rows(path,tmp_path/'changed',expected_generation={**generation,'sha256':'0'*64}))


def test_selected_object_drains_large_census_without_resident_value():
    import io
    from src.engine.lifecycle.research_json_stream import selected_object
    source = {'sections': {'recent_trades': [{'id': 1}], 'census': [{'id': i} for i in range(10000)]}, 'meta': {'warnings': ['w']}}
    assert selected_object(io.StringIO(json.dumps(source)), {'sections': {'recent_trades': None}, 'meta': None}) == {
        'sections': {'recent_trades': [{'id': 1}]}, 'meta': {'warnings': ['w']}}
    with pytest.raises(ValueError):
        selected_object(io.StringIO('{"ignored":[garbage],"meta":{}}'), {'meta': None})


@pytest.mark.parametrize('raw', ['[1.25,2e-12,3.0]', '[123456789,1e+30,-2.2]', '{"value":1.23}'])
def test_structural_reader_preserves_numbers_at_chunk_boundaries(raw):
    import io
    class Chunks(io.StringIO):
        def read(self, size=-1):return super().read(min(size, 2))
    reader = Reader(Chunks(raw), budgeted=False)
    if raw.startswith('['):
        value = list(reader.array(lambda r: r.value()))
    else:
        value = {}
        def visit(key, r):
            value[key] = r.value()
            return ()
        for _ in reader.fields(visit):pass
    reader.finish()
    assert value == json.loads(raw)


def test_structural_projection_rejects_non_json_whitespace():
    import io
    from src.engine.lifecycle.research_json_stream import selected_object
    with pytest.raises(ValueError):
        selected_object(io.StringIO('{\v"meta":{}}'), {'meta': None})


def test_large_single_json_value_uses_geometric_refill():
    import io
    class Measured(io.StringIO):
        def __init__(self, text):super().__init__(text);self.reads = 0
        def read(self, size=-1):self.reads += 1;return super().read(size)
    value = {'evidence': 'x' * (2 * 1024 * 1024)}
    handle = Measured(json.dumps(value))
    reader = Reader(handle, budgeted=False)
    assert reader.value(4 * 1024 * 1024) == value
    reader.finish()
    assert handle.reads < 12  # Fixed 64KiB retries previously read/decode >32 times.
