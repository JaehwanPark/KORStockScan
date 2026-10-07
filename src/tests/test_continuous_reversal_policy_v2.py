"""Native v2 publication/adoption boundary, OR policy and finite daily catalog."""
import copy
import json
from datetime import datetime
from pathlib import Path
import pytest
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import continuous_reversal_policy_v2 as V2
from src.engine.scalping import continuous_reversal_branch_postclose as R
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_policy as V1
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_auxiliary_phases as A
from src.engine.scalping import reversal_auxiliary_contract as AUX
from src.tests.test_continuous_reversal import family_reports,synthetic_family
from src.tests.test_continuous_reversal_branches import rows,state


@pytest.fixture
def native(tmp_path,monkeypatch):
 from src.tests.test_mechanistic_entry_runtime_policy import initial
 initial(tmp_path);m,a=family_reports();V1.publish(tmp_path,'2026-10-06','2026-10-06',m,a)
 old=N.load(data_root=tmp_path,target_date='2026-10-07')
 receipt=dict(schema='continuous_reversal_current_v1',bundle_sha256=old['bundle_sha256'],previous_bundle_sha256=old['continuous_reversal']['parent_bundle_sha256'],
              effective_from='2026-10-07T09:00:00+09:00',effective_date='2026-10-07',family_sha256=old['continuous_reversal']['family_sha256'])
 receipt['receipt_sha256']=P.digest(receipt);N._atomic_write_json(N.root(tmp_path)/'current.json',receipt)
 parent=N.load_effective(data_root=tmp_path,target_date='2026-10-07');family=parent['continuous_reversal']
 evidence=tmp_path/'actual.jsonl';evidence.write_text('{"offline":"fixture"}\n')
 cells=[];aux=[]
 for key in P.expected_cells():
  branches=[B.legacy_branch('ALL')]
  if key=='samsung|REGULAR|ALL':branches.append(B.pattern_branch())
  payload=B.payload(branches)
  cells.append(dict(key=key,payload=payload,payload_sha256=P.digest(payload),local_metrics=dict(wins=1,resolved=1),inherited_from=None,
                    branch_metrics={b['branch_id']:dict(wins=1,resolved=1) for b in branches}))
  phases={B.FIRST:dict(arm=AUX.ARMS[-1],binding=A.binding(B.FIRST,AUX.ARMS[-1]),local_metrics=None,carry_source=family['family_sha256'])}
  if key=='samsung|REGULAR|ALL':phases[B.CONFIRMED]=dict(arm=AUX.ARMS[-1],binding=A.binding(B.CONFIRMED,AUX.ARMS[-1]),local_metrics=dict(pass_count=1,pass_wins=1),actual_response_evidence=dict(path=str(evidence),sha256=P.file_hash(evidence)))
  payload=dict(phase_policies=phases);aux.append(dict(key=key,payload=payload,payload_sha256=P.digest(payload),local_metrics=None,inherited_from=None))
 common=dict(schema=P.SCHEMA,source_date='2026-10-07',publication_date='2026-10-07',status='completed')
 m=P.seal(dict(common,cells=cells,parent_bundle_sha256=parent['bundle_sha256'],label_contract=dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800),source_manifest_sha256='a'*64,source_receipts=[]))
 a=P.seal(dict(common,cells=aux,machine_report_sha256=m['artifact_content_sha256'],results_sources=[dict(path=str(evidence),sha256=P.file_hash(evidence))]))
 from src.engine.infrastructure import runtime_release_router as router
 monkeypatch.setattr(router,'selected_release',lambda workspace:(tmp_path/'release','a'*40))
 return tmp_path,parent,m,a


def test_candidate_never_activates_by_publication_or_date_change(native):
 root,parent,m,a=native
 dated=N.root(root)/'policy_2026-10-07.json';old=dated.read_bytes()
 candidate=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 assert V2.load_candidate(root,'2026-10-07')==candidate
 assert dated.read_bytes()==old
 assert N.load_effective(data_root=root,target_date='2026-10-07')['bundle_sha256']==parent['bundle_sha256']
 with pytest.raises(ValueError,match='code_pid'):V2.activate(root,'2026-10-07',now=datetime(2026,10,7,10,tzinfo=N.KST))
 next_candidate=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)
 assert N.load(data_root=root,target_date='2026-10-08')==next_candidate
 assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']==parent['bundle_sha256']
 assert N.preparation_path(root,'2026-10-08').parent.name=='candidates'


def test_union_one_primary_request_and_raw_fraction(native):
 root,_,m,a=native
 bundle=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 family=copy.deepcopy(bundle['continuous_reversal']);snapshot=state(rows()).snapshot(state(rows()).ready[0])
 # This confirmed tick is not another first uptick: only the pattern applies.
 verdict,inp,prompt,schema=V2.assess(family,snapshot,symbol='005930',session='SOR_REGULAR')
 assert verdict['action']=='ENTER_NOW' and verdict['primary_branch']==B.BRANCH
 assert verdict['matched_branches']==[B.BRANCH] and verdict['decision_phase']==B.CONFIRMED
 assert inp['observation_phase']['stage']==B.CONFIRMED and prompt.isascii()
 bad=copy.deepcopy(snapshot);bad[0]['source_item']='005930'
 verdict,*_=V2.assess(family,bad,symbol='005930',session='SOR_REGULAR')
 assert verdict['action']=='BLOCK'
 bad=copy.deepcopy(snapshot);bad[0]['entry_ask']=None
 verdict,*_=V2.assess(family,bad,symbol='005930',session='SOR_REGULAR')
 assert verdict['action']=='RECHECK'
 # Coincident sources are one decision. Exact raw fraction, then frozen order.
 both=copy.deepcopy(snapshot);both[0]['coincident_first']=copy.deepcopy(both[0]);both[0]['coincident_first_input']=both[1]
 verdict,*_=V2.assess(family,both,symbol='005930',session='SOR_REGULAR')
 assert len(verdict['matched_branches'])==2 and verdict['primary_branch']==B.legacy_branch('ALL')['branch_id']
 family['machine_cells']['samsung|REGULAR|ALL']['branch_metrics'][B.legacy_branch('ALL')['branch_id']]=dict(wins=999,resolved=1000)
 family['family_sha256']=P.digest({k:v for k,v in family.items() if k!='family_sha256'})
 verdict,*_=V2.assess(family,both,symbol='005930',session='SOR_REGULAR')
 assert verdict['primary_branch']==B.BRANCH


def test_frozen_contract_tamper_and_machine_parent(native):
 root,_,m,a=native
 bad=copy.deepcopy(a);bad['machine_report_sha256']='0'*64;bad=P.seal(bad)
 with pytest.raises(ValueError,match='machine_parent'):V2.stage(root,'2026-10-07','2026-10-07',m,bad,target_date='2026-10-08',release_commit='a'*40)
 bundle=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)
 family=copy.deepcopy(bundle['continuous_reversal']);family['auxiliary_cells']['samsung|REGULAR|ALL']['payload']['phase_policies'].pop(B.CONFIRMED)
 family['family_sha256']=P.digest({k:v for k,v in family.items() if k!='family_sha256'})
 with pytest.raises(ValueError):V2.validate_family(family)
 (root/'actual.jsonl').write_text('{}\n')
 with pytest.raises(ValueError):V2.load_candidate(root,'2026-10-08')


def test_finite_catalog_incumbent_tie_and_applicable_regular_inheritance():
 parent=synthetic_family();e=state(rows()).snapshot(state(rows()).ready[0])[0]
 point=dict(event_id=e['event_id'],phase=B.CONFIRMED,event=e,outcome=dict(status='WIN'))
 assert len(R.catalog('samsung|REGULAR|ALL'))==27
 assert len(R.catalog('other|REGULAR|LT_20000'))==13
 cells=R.select_machine([point],parent)
 regular=next(c for c in cells if c['key']=='samsung|REGULAR|ALL')
 assert len(regular['payload']['branches'])==2
 assert any(c['status']=='scope_gap' for c in regular['candidates'])
 pre=next(c for c in cells if c['key']=='samsung|PRE|ALL')
 assert pre['payload']==B.payload([B.legacy_branch('ALL')])
 assert pre['local_metrics'] is None and pre['parent_payload_sha256']==pre['payload_sha256']
 first=copy.deepcopy(point);first['phase']=B.FIRST;first['event'].pop('decision_phase',None)
 parent['machine_cells']['samsung|REGULAR|ALL']['payload']=dict(rule='DD5_GE_0_4')
 parent['machine_cells']['samsung|REGULAR|ALL']['payload_sha256']=P.digest(dict(rule='DD5_GE_0_4'))
 result=R.select_machine([first],parent)
 assert next(c for c in result if c['key']=='samsung|REGULAR|ALL')['payload']==B.payload([B.legacy_branch('DD5_GE_0_4')])


def test_first_cache_request_identity_is_exact_legacy():
 e,inp=state(rows()).snapshot(state(rows()).ready[0]);row=dict(event_id=e['event_id'],input=inp,phase=B.FIRST,event=e)
 for arm in AUX.ARMS:assert R.request(row,arm)==P.actual_request(row,arm)


def test_native_intraday_activation_cas_and_original_preopen_survives(native,monkeypatch):
 root,parent,m,a=native
 from src.engine.automation import intraday_release_handoff as handoff
 identity=dict(pid=123,start_ticks='111',cwd=str(root/'release/src'))
 monkeypatch.setattr(handoff,'_identity',lambda pid:identity)
 proof=root/'code-consumed.json';proof.write_text('{}')
 evidence=dict(schema='intraday_main_policy_code_pid_v1',target_date='2026-10-07',release_commit='a'*40,pid_identity=identity,
               consumed_path=str(proof),consumed_sha256=P.file_hash(proof))
 dated=N.root(root)/'policy_2026-10-07.json';before=dated.read_bytes()
 candidate=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 bad=copy.deepcopy(evidence);bad['release_commit']='b'*40
 with pytest.raises(ValueError,match='code_pid'):V2.activate(root,'2026-10-07',now=datetime(2026,10,7,10,tzinfo=N.KST),intraday_evidence=bad)
 receipt=V2.activate(root,'2026-10-07',now=datetime(2026,10,7,10,tzinfo=N.KST),intraday_evidence=evidence)
 assert receipt['status']=='activated' and dated.read_bytes()==before
 assert N.load_effective(data_root=root,target_date='2026-10-07')==candidate
 assert N.load_effective(data_root=root,target_date='2026-10-08')==candidate
 assert V2.activate(root,'2026-10-07',now=datetime(2026,10,7,10,tzinfo=N.KST),intraday_evidence=evidence)['status']=='already_active'


@pytest.mark.parametrize('mode',['confirmed','first','no_signal','missing_quote'])
def test_v2_capture_reaches_semantic_consumer_without_legacy_rule(native,monkeypatch,mode):
 root,_,m,a=native
 from src.engine.scalping import ai_decision_trace as trace
 from src.engine.monitoring import submission_bottleneck_monitor as monitor
 bundle=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 family=bundle['continuous_reversal'];s=state(rows());snapshot=s.snapshot(s.ready[0])
 if mode=='first':
  snapshot[0]['decision_phase']=B.FIRST
 if mode=='missing_quote':snapshot[0]['entry_ask']=None
 if mode=='no_signal':snapshot=None
 assessment,inp,prompt,schema=V2.assess(family,snapshot,symbol='005930',session='SOR_REGULAR')
 clock=rows()[-1][0]+.2;now=datetime.fromtimestamp(clock,N.KST)
 raw=dict(stock_code='005930',session_bucket='SOR_REGULAR',effective_venue='INTEGRATED',evaluation_attempt_id='v2-attempt',entry_machine_input_as_of=clock-.1)
 receipt=dict(family_sha256=family['family_sha256'],source_date=family['source_date'],publication_date=family['publication_date'],effective_date=family['effective_date'],
              machine_component_sha256=P.digest(family['machine_cells']),auxiliary_component_sha256=P.digest(family['auxiliary_cells']),
              arm=assessment.get('auxiliary_arm'),phase=assessment.get('decision_phase',B.FIRST),primary_branch=assessment.get('primary_branch'),
              matched_branches=assessment.get('matched_branches'),signal_id=assessment.get('signal_id'),branch_definition_sha256=assessment.get('branch_definition_sha256'),
              snapshot_read_at=clock-.05,input_sha256=P.digest(inp) if inp else None,prompt_sha256=P.digest(prompt) if inp else None,response_schema_sha256=P.digest(schema) if inp else None)
 monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED','1');monkeypatch.setattr(trace,'DATA_DIR',root);monkeypatch.setattr(trace,'_now',lambda:now)
 trace.capture_machine_observation(exact_payload=raw,setup_evidence={},assessment=assessment,bundle_sha256=bundle['bundle_sha256'],reversal_context=receipt,
                                 reversal_request=dict(input=inp,prompt=prompt,response_schema=schema) if inp else None)
 observation=json.loads((root/'ai_decision_payloads/ai_decision_payloads_2026-10-07.jsonl').read_text().splitlines()[-1])
 monitor._reversal_observation_receipt(bundle,observation)
 if mode=='confirmed':
  observation['runtime_consumption']['continuous_reversal']['phase']=B.FIRST
  with pytest.raises(ValueError,match='phase'):monitor._reversal_observation_receipt(bundle,observation)


def test_daily_native_producer_actual_phase_cache_and_nextday_handoff(native,monkeypatch):
 root,parent,m,a=native
 import gzip
 from src.engine.scalping import ai_decision_quality as provider
 from src.engine.automation import intraday_release_handoff as handoff
 identity=dict(pid=123,start_ticks='111',cwd=str(root/'release/src'))
 monkeypatch.setattr(handoff,'_identity',lambda pid:identity)
 proof=root/'code-consumed.json';proof.write_text('{}')
 evidence=dict(schema='intraday_main_policy_code_pid_v1',target_date='2026-10-07',release_commit='a'*40,pid_identity=identity,consumed_path=str(proof),consumed_sha256=P.file_hash(proof))
 V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 V2.activate(root,'2026-10-07',now=datetime(2026,10,7,10,tzinfo=N.KST),intraday_evidence=evidence)
 parent=N.load_effective(data_root=root,target_date='2026-10-07')
 r=rows();last=r[-1][:];last[0]+=10;last[2]+=1;last[3]=last[5]=105.;last[4]=104.99;r.append(last)
 normalized=root/'normalized.json.gz';normalized.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':r})).encode()))
 source=P.seal(dict(source_date='2026-10-07',normalized_sources=dict(partitions=[dict(day='2026-10-07',venue='SOR',session='SOR_REGULAR',path=str(normalized),sha256=P.file_hash(normalized))]),reviewed_events=[],selected_routes={}))
 monkeypatch.setattr(P,'ensure_population',lambda *args:source);monkeypatch.setattr(P,'completed_bars',lambda *args:({},[]))
 P.write(P.directory(root,'2026-10-07')/'source.json',source)
 machine=R.machine_report(root,'2026-10-07','2026-10-07',parent)
 points=R.prepare_daily_inputs(root,'2026-10-07',machine)
 assert points and {p['phase'] for p in points}=={B.FIRST,B.CONFIRMED}
 sequence=[]
 def actual(req,**kwargs):
  assert 'outcome' not in req['candidate_input']
  sequence.append(req['paired_replay_id'])
  phase=(req['candidate_input'].get('observation_phase') or {}).get('stage')
  support=['first_price_uptick','observed_price_decline']+(['additional_higher_trade'] if phase==B.CONFIRMED else [])
  return dict(candidate_response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=support,contradicting_fact_ids=[],confidence=70),provider_provenance=dict(response_id=req['paired_replay_id']))
 monkeypatch.setattr(provider,'execute_openai_prompt_v2_candidate',actual)
 path=R.directory(root,'2026-10-07')/'daily-provider-inputs.json'
 R.calls(root,'2026-10-07',inputs_path=path);first_count=len(sequence)
 R.calls(root,'2026-10-07',inputs_path=path)
 assert first_count==len(points)*5 and len(sequence)==first_count
 # Issue a native next-session candidate; it cannot affect today's active PID.
 import subprocess
 monkeypatch.setattr(subprocess,'check_output',lambda *args,**kwargs:'a'*40+'\n')
 auxiliary=R.auxiliary_report(root,'2026-10-07','2026-10-07',parent)
 assert auxiliary['staged']['target_date']=='2026-10-08'
 assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']==parent['bundle_sha256']
 handoff=V1.direct_handoff(root,'2026-10-07')
 assert handoff['policy_bundle_sha256']==N.load(data_root=root,target_date='2026-10-08')['bundle_sha256']
 assert handoff['machine_cell_count']==12


def test_coincident_primary_first_uses_its_own_low_and_fact_bytes(native):
 root,_,m,a=native
 bundle=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
 r=rows();extra=r[-1][:];extra[0]+=.2;extra[2]+=1
 r[-1][3]=103.35;extra[3]=103.5;r.append(extra)
 s=state(r);snapshot=s.snapshot(s.ready[0])
 verdict,inp,_,_=V2.assess(bundle['continuous_reversal'],snapshot,symbol='005930',session='SOR_REGULAR')
 assert verdict['decision_phase']==B.FIRST
 assert verdict['event']['low_price']==103.3
 assert verdict['auxiliary_event']['low_price']==103.35
 assert inp['entry_setup_evidence_v1']['facts']['low_price']==103.35
