"""Producer-sealed legacy projection streaming and native-path parity."""
import json
import pytest
from src.engine.lifecycle.research_json_stream import Reader,completed_rows
from src.engine.lifecycle import research_storage as storage
from src.tests.test_main_all_scope_trailing import position,quote
from src.engine.automation import main_trailing_source_assembler as source
from src.engine.automation import main_trailing_all_scope_research as owner
from src.tests.test_main_trailing_source_assembler import fixture,DAY,TARGET


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
