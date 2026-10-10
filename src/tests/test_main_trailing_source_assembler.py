"""Automatic producer provenance, normal consumer and exact-source failures."""
import gzip
import json
from collections import Counter
import pytest
from src.engine.automation import main_trailing_source_assembler as source
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.automation import main_trailing_research_handoff as handoff
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.scalping.ai_decision_trace import _json_bytes
from src.engine.scalping.trailing_mechanical_policy import baseline_receipt
from src.engine.automation.runtime_policy_bootstrap import _digest_json
from src.tests.test_micro_reversion_symbol_master import _master_payload
from src.engine.lifecycle import research_storage as storage


DAY='2026-10-08'
TARGET='2026-10-12'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def fixture(root):
    master=root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json'
    write(master,_master_payload())
    parent=dict(target_date=DAY,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{DAY}.json',parent)
    event=dict(at=DAY+'T09:00:00+09:00',source_item='005930',native_epoch=1)
    row=dict(schema='mechanistic_entry_observation_v1',bundle_sha256='a'*64,
        captured_at=DAY+'T09:00:00.100+09:00',source=dict(assessment=dict(action='ENTER_NOW',event=event,
            canonical_opportunity_id='original-canonical')),label_context=dict(evaluation_attempt_id='native-1',stock_code='005930'))
    row['machine_observation_sha256']=__import__('hashlib').sha256(_json_bytes(row)).hexdigest()
    native=root/'ai_decision_payloads'/f'ai_decision_payloads_{DAY}.jsonl'
    native.parent.mkdir(parents=True);native.write_text(json.dumps(row)+'\n')
    trace=dict(schema='ai_decision_trace_v1',decision_stage='entry_screen',decision_ts=DAY+'T09:00:01+09:00',
        stock_code='005930',evaluation_attempt_id='native-1',decision_trace_id='trace-1',source_event_stage='machine_enter',
        entry_mechanistic_action='ENTER_NOW',entry_ai_risk_verdict='PASS',provider_called=True,
        decision_evaluation_status='evaluated',result_source='live',prompt_version='frozen',entry_ai_component_sha256='b'*64,
        market_data_route='KRX',session_bucket='REGULAR',machine_bundle_sha256='a'*64,
        machine_observation_sha256=row['machine_observation_sha256'])
    path=root/'ai_decision_trace'/f'ai_decision_trace_{DAY}.jsonl'
    path.parent.mkdir(parents=True);path.write_text(json.dumps(trace)+'\n')
    return path,native


def test_automatic_native_binding_warm_reuse_and_new_file_invalidation(tmp_path,monkeypatch):
    root=tmp_path/'source';path,native=fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    payload=research._sealed(manifest)
    assert payload['population_ids_ref']['count']==1
    assert payload['assembly_census']['source_gaps']['native_canonical_identity_recovered']==1
    original=source._native_index
    monkeypatch.setattr(source,'_native_index',lambda *a,**k:pytest.fail('unchanged source decoded again'))
    assert source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)==manifest
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    assert result['status']=='complete'
    assert result['common_population_evaluation']['common_ids_ref']['count']==0
    report_path=out/f'research_{DAY}.json'
    assert handoff.verify_report(report_path,target_date=TARGET)[0]==result
    # A new invalid exact-date receipt changes inventory as well as valid rows.
    write(root/'runtime/mechanistic_entry_policy/decisions'/DAY/'pid'/'new.json',{})
    with pytest.raises(ValueError,match='inventory_changed'):
        handoff.verify_report(report_path,target_date=TARGET)
    monkeypatch.setattr(source,'_native_index',original)
    source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    assert research._sealed(manifest)['assembly_input_generation_sha256']!=payload['assembly_input_generation_sha256']


def test_conflicting_native_or_clock_after_cutoff_is_excluded(tmp_path):
    root=tmp_path/'source';path,native=fixture(root)
    original=json.loads(native.read_text());other={**original,'label_context':{**original['label_context'],'evaluation_attempt_id':'other'}}
    # An invalid hash cannot supply a replacement native binding.
    native.write_text(json.dumps(other)+'\n')
    manifest=source.assemble(root,tmp_path/'bad',source_date=DAY,target_date=TARGET,start_date=DAY)
    value=research._sealed(manifest)
    assert value['population_ids_ref']['count']==0
    assert value['assembly_census']['source_gaps']['native_canonical_identity_missing']==1
    native.write_text(json.dumps(original)+'\n')
    cutoff=__import__('datetime').datetime.fromisoformat(DAY+'T09:00:00.500+09:00').timestamp()
    manifest=source.assemble(root,tmp_path/'early',source_date=DAY,target_date=TARGET,start_date=DAY,as_of=cutoff)
    assert research._sealed(manifest)['population_ids_ref']['count']==0


def test_plain_gzip_alias_conflict_cannot_be_ignored(tmp_path):
    root=tmp_path/'source';path,native=fixture(root)
    compressed=path.with_suffix('.jsonl.gz')
    with gzip.open(compressed,'wb') as handle:handle.write(path.read_bytes())
    assert source.select_stream(root,'ai_decision_trace',DAY,{})==path
    with gzip.open(compressed,'wb') as handle:handle.write(b'{}\n')
    with pytest.raises(ValueError,match='plain_gzip_conflict'):
        source.assemble(root,tmp_path/'bad',source_date=DAY,target_date=TARGET,start_date=DAY)


def test_holding_extension_is_verified_even_when_parent_values_carry(tmp_path):
    root=tmp_path/'source';fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    path=out/f'research_{DAY}.json'
    extension=dict(report_path=str(path),report_generation=source.byte_generation(path),status=result['status'],
        input_window_generation_sha256=result['input_window_generation_sha256'],initial_policy_sha256=result['initial_policy']['policy_sha256'],
        scope_count=result['scope']['scope_count'],allowed_runtime_apply=False)
    assert handoff.verify_extension({'date':DAY,'all_scope_trailing_research':extension},target_date=TARGET)==result
    extension['initial_policy_sha256']='c'*64
    with pytest.raises(ValueError,match='extension_binding'):
        handoff.verify_extension({'date':DAY,'all_scope_trailing_research':extension},target_date=TARGET)


def test_alphanumeric_verified_scope_remains_research_only():
    from src.engine.scalping.main_exit_scope import build_scope,validate_scope
    result=build_scope([dict(code='0123A0',known_at=1,tradable=None)],as_of=2,universe_source_sha256='a'*64)
    validate_scope(result)
    assert result['scope_count']==8 and result['allowed_runtime_apply'] is False


@pytest.mark.parametrize('boundary',[1,2,3,4])
def test_real_initial_publication_interruption_never_accepts_mixed_receipts(tmp_path,monkeypatch,boundary):
    root=tmp_path/'source';fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    original=handoff._atomic;calls=[]
    def stop(path,value):
        original(path,value);calls.append(path)
        if len(calls)==boundary:raise RuntimeError('interrupted')
    monkeypatch.setattr(handoff,'_atomic',stop)
    with pytest.raises(RuntimeError):handoff.publish_initial(root,out/f'research_{DAY}.json',target_date=TARGET)
    if boundary<4:
        with pytest.raises((ValueError,OSError)):
            handoff.verify_initial(root,result['initial_policy'],target_date=TARGET,
                parent_sha256=result['initial_policy']['parent_sha256'])
    else:
        assert handoff.verify_initial(root,result['initial_policy'],target_date=TARGET,
            parent_sha256=result['initial_policy']['parent_sha256'])['target_date']==TARGET


def test_immutable_source_successors_preserve_prior_manifest(tmp_path):
    root=tmp_path/'source';fixture(root);base=tmp_path/'assembly'
    first=source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)
    original=first.read_bytes()
    assert source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)==first
    write(root/'runtime/mechanistic_entry_policy/decisions'/DAY/'pid'/'new.json',{})
    successor=source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)
    assert successor!=first and first.read_bytes()==original
