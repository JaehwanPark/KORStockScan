"""Real native capture/queue/reader measurement never certifies unrun Main."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.engine.automation import main_stop_performance as perf
from src.engine.scalping import main_stop_policy as policy
from src.tests.test_main_stop_policy import baseline


def scenario():
    at=1792112400.
    depth=dict(item='005930',market_route='krx_only',transport_epoch=1,observed_epoch=at,
               best_bid=9700,best_bid_qty=20,orderbook={'bids':[{'price':9700,'volume':20}]})
    quote={**depth,'source_type':'0D','depth_receipt':depth}
    stock=dict(id=1,code='005930',name='OFFLINE_STOP_TEST',strategy='SCALPING',position_tag='SCANNER',
               buy_qty=10,buy_price=10000.,status='HOLDING',
               _trailing_entry_cost_model=dict(buy_krw=10.,sell_rate=.001,known_at=at-1,source_sha256='a'*64))
    inputs=dict(snapshot={'realtime_type_snapshots_by_route':{'krx_only':{'0D':depth}}},
        quote_receipt=quote,executable_bid=9700,bid_source='fresh_ws_executable_bid',rest_snapshot=None,
        quality={'quote_consistency_state':'consistent'},nxt_quality={},quote_received_at=at,bid_received_at=at,
        market_type='REGULAR',exit_allowed_by_clock=True,price_usable=True,now_ts=at,
        evaluator='normal',holding_profit_rate_at_eval=-3.)
    return dict(stock=stock,quote_inputs=inputs,role='SCANNER',target_date='2026-10-16')


def measured(tmp_path):
    return perf.measure_capture_pair(tmp_path/'performance.json',scenarios=[scenario()],
        baseline=baseline(),candidate=replace(baseline(),grace_sec=0),source_sha256='a'*64)


def test_real_native_capture_pair_has_same_calls_and_readback_with_explicit_scope(tmp_path):
    body,ref=measured(tmp_path)
    assert json.loads((tmp_path/'performance.json').read_text())==body
    assert ref['sha256']
    assert body['execution_order']==['baseline','candidate','candidate','baseline','baseline','candidate']
    assert len(body['arms']['candidate'])==3
    assert all(run['queue']['append_confirmed']==run['decoded_rows']==2
               for runs in body['arms'].values() for run in runs)
    assert body['arms']['baseline'][0]['decision_sha256']!=body['arms']['candidate'][0]['decision_sha256']
    assert body['full_runtime_gate_status']=='blocked'
    assert body['allowed_runtime_apply'] is False
    assert perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=False)==body
    with pytest.raises(ValueError,match='full_runtime_unmeasured'):
        perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=True)


@pytest.mark.parametrize('fault',['pass','population','summary','context','code'])
def test_resealed_claim_cannot_widen_coverage_or_change_measured_population(tmp_path,fault):
    body,_=measured(tmp_path)
    if fault=='pass':body.update(status='pass',scope='runtime_and_postclose',unresolved_findings=[])
    elif fault=='population':body['arms']['candidate'][0]['decoded_rows']=3
    elif fault=='summary':body['arms']['candidate'][0]['capture']['p95_ns']=0
    elif fault=='context':body['arms']['candidate'][0]['context_sha256']='b'*64
    elif fault=='code':body['code_sha256']='b'*64
    body['performance_sha256']=policy.digest({k:v for k,v in body.items() if k!='performance_sha256'})
    with pytest.raises(ValueError,match='stop_performance_'):
        perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=False)


def test_capture_failure_restores_sink_and_never_creates_success_receipt(tmp_path):
    bad=deepcopy(scenario());bad['stock']['buy_qty']=0
    old=policy._SOURCE_SINK
    with pytest.raises(ValueError,match='capture_rejected'):
        perf.measure_capture_pair(tmp_path/'performance.json',scenarios=[bad],baseline=baseline(),
            candidate=baseline(),source_sha256='a'*64)
    assert policy._SOURCE_SINK is old
    assert not (tmp_path/'performance.json').exists()


def request_fixture(source_sha256='a'*64,repeats=3):
    """Reproducible offline request; full/unknown quantity and caller ordering."""
    from dataclasses import asdict
    from src.tests.test_main_stop_quantity_source import native_stock
    cases=[]
    for index,sequence in enumerate((
        [['fast','preset_safety'],['normal','preset_safety'],['normal','common_soft']],
        [['normal','preset_safety'],['normal','common_soft'],['fast','preset_safety']],
        [['normal','preset_safety'],['normal','common_soft']])):
        case=scenario();case['role']='SCALP_PRESET_TP'
        if index<2:
            native=native_stock(filled=10,ordered=10)
            case['stock'].update(native)
            case['stock'].update(id=index+1,status='HOLDING',exit_mode='SCALP_PRESET_TP')
        case['evaluation_sequence']=sequence
        case['stock']['id']=index+1
        cases.append(case)
    return dict(scenarios=cases,baseline=asdict(baseline()),candidate=asdict(replace(baseline(),grace_sec=0)),
                source_sha256=source_sha256,repeats=repeats)


def test_fast_normal_shared_quote_and_unknown_quantity_are_measured_without_loss(tmp_path):
    request=request_fixture()
    body,_=perf.measure_capture_pair(tmp_path/'performance.json',scenarios=request['scenarios'],
        baseline=baseline(),candidate=replace(baseline(),grace_sec=0),source_sha256='a'*64)
    for runs in body['arms'].values():
        for run in runs:
            assert run['calls']['native_capture']==3
            assert run['calls']['native_stage_receipts']==8
            assert run['decoded_rows']==run['queue']['append_confirmed']==11
            assert run['quantity_census']=={'full_fill':6,'unknown':2}


def _metric_runs(latency=10_000_000):
    # Pure comparator inputs only. These are never full producer receipts and
    # cannot enter prospective experiment/selection authority.
    run=dict(samples_ns=[latency]*512,cpu_ns=1_000_000_000,
        io_delta=dict(rchar=100000,wchar=100000),peak_rss_bytes=256*1024**2,
        warm_rss_growth_bytes=1024,peak_temp_bytes=100000)
    return {arm:[deepcopy(run) for _ in range(3)] for arm in ('baseline','candidate')}


def test_full_budget_is_frozen_before_measurement_and_noise_is_not_posthoc():
    budget=deepcopy(perf.FULL_BUDGET)
    assert perf._full_budget(budget)==budget
    for field,value in [('pairs',4),('tail_relative_noise',.5),('samples_per_arm_run',1),
                        ('min_concurrent_samples_per_run',0),('max_rss_bytes',2*1024**3)]:
        invalid=dict(budget,**{field:value})
        with pytest.raises(ValueError,match='frozen_budget_invalid'):perf._full_budget(invalid)
    arms=_metric_runs()
    assert perf._full_pair_findings(arms,budget)==[]
    arms['candidate'][0]['samples_ns']=[10_500_001]*512
    assert 'tail_regression:p99_ns:0' in perf._full_pair_findings(arms,budget)
    arms=_metric_runs(100_000_000)
    arms['candidate'][1]['samples_ns']=[101_000_001]*512
    assert 'tail_regression:p95_ns:1' in perf._full_pair_findings(arms,budget)


@pytest.mark.parametrize('role',policy.ROLES)
@pytest.mark.parametrize('market',policy.MARKETS)
def test_measurement_cell_accepts_all_native_typed_cells_without_claiming_coverage(role,market):
    cell=role+'|'+market
    assert perf._measurement_cell(cell)==cell
    cases=[]
    for name in perf.FULL_CASES:
        measured_role=role if name in ('common_soft_hold','fast_hard') else ('SCALPING' if name=='fast_hold' else 'SCALP_PRESET_TP')
        stock=dict(buy_qty=5 if name=='small_quantity_full' else 10)
        if measured_role=='SCALP_PRESET_TP':stock['exit_mode']='SCALP_PRESET_TP'
        if name=='manual_veto':stock['manual_control_auto_hard_stop_blocked']=True
        row=dict(case_id=name,role=measured_role,stock=stock,
            dispatch_order='fast_first' if name in ('fast_hard','fast_emergency','inventory_unknown','fast_hold') else 'normal_first',
            expected_semantic={'status':'HOLDING' if name in ('common_soft_hold','fast_hold','manual_veto','inventory_unknown') else 'SELL_ORDERED'})
        if name in ('normal_preset_hard','fast_emergency'):row['companions']=[{},{}]
        if name=='inventory_unknown':row['account_inventory']={'rows':[],'successful_exchanges':[]}
        cases.append(row)
    # This is only typed request validation, with no native execution or PASS.
    assert perf._full_scenarios(cases,cell)==cases
    cases[0]['role']='UNKNOWN'
    with pytest.raises(ValueError,match='scenario_contract_invalid'):
        perf._full_scenarios(cases,cell)


@pytest.mark.parametrize('cell',[None,'SCANNER|AFTERMARKET','scanner|REGULAR','SCANNER|REGULAR|EXTRA'])
def test_measurement_cell_does_not_guess_unknown_role_or_market(cell):
    with pytest.raises(ValueError,match='measurement_cell_invalid'):
        perf._measurement_cell(cell)


@pytest.mark.parametrize('fault,reason',[
    ('sample','insufficient_tail_samples'),('rss','rss_budget'),('growth','warm_rss_growth'),
    ('disk','temp_budget'),('cpu','cpu_regression'),('io','io_regression'),('absolute','absolute_p99_budget'),
    ('kernel_rss','rss_budget')])
def test_full_metric_gate_keeps_insufficient_samples_and_resource_regressions_visible(fault,reason):
    arms=_metric_runs();run=arms['candidate'][0]
    if fault=='sample':run['samples_ns']=run['samples_ns'][:10]
    elif fault=='rss':run['peak_rss_bytes']=1024**3+1
    elif fault=='growth':run['warm_rss_growth_bytes']=64*1024**2+1
    elif fault=='disk':run['peak_temp_bytes']=2*1024**3+1
    elif fault=='cpu':run['cpu_ns']=1_050_000_001
    elif fault=='io':run['io_delta']['wchar']=105001
    elif fault=='absolute':run['samples_ns']=[250_000_001]*512
    elif fault=='kernel_rss':run['process_lifetime_peak_rss_bytes']=1024**3+1
    assert any(value.startswith(reason) for value in perf._full_pair_findings(arms,perf.FULL_BUDGET))


def test_full_measurement_requires_dedicated_isolated_cli(tmp_path):
    with pytest.raises(ValueError,match='requires_dedicated_cli'):
        perf.measure_full_pair(tmp_path/'full.json',scenarios=[scenario()],baseline=baseline(),
            candidate=baseline(),postclose={},source_sha256='a'*64,budget=perf.FULL_BUDGET)
    assert not (tmp_path/'full.json').exists()


def test_full_cell_coverage_requires_same_cell_capture_guard_and_transport_in_every_arm():
    run=dict(capture_cell_phases={'SCANNER|REGULAR':{'normal:common_soft':2,'fast:preset_safety':2}},
        actual_call_cells={'SCANNER|REGULAR':{'final_guard':1,'isolated_submit':1}})
    arms={name:[deepcopy(run) for _ in range(3)] for name in ('baseline','candidate')}
    assert perf._coverage_cells(arms)==['SCANNER|REGULAR']
    arms['candidate'][1]['actual_call_cells']['SCANNER|REGULAR']['isolated_submit']=0
    assert perf._coverage_cells(arms)==[]
    arms['candidate'][1]=deepcopy(run)
    arms['baseline'][0]['capture_cell_phases']={'SCANNER|PREMARKET':run['capture_cell_phases']['SCANNER|REGULAR']}
    assert perf._coverage_cells(arms)==[]


@pytest.mark.parametrize('field',perf.FULL_LOSSES)
def test_every_native_loss_and_rejected_source_counter_is_required_zero(field):
    losses={name:0 for name in perf.FULL_LOSSES}
    assert perf._native_losses_verified(losses)
    losses[field]=1
    assert not perf._native_losses_verified(losses)
    losses.pop(field)
    assert not perf._native_losses_verified(losses)


def test_new_publication_binds_exact_cell_to_native_performance_validator(monkeypatch):
    from src.engine.scalping import main_stop_experiment as contracts
    calls=[]
    # This isolates argument propagation only. It creates no measured receipt,
    # finalized experiment, policy, or synthetic full-performance success.
    monkeypatch.setattr(contracts,'_verify_performance',lambda *args,**kwargs:calls.append(kwargs))
    contracts.require_native_publication_performance(dict(code_sha256='a'*64,source_sha256='b'*64,
        performance_receipt={'path':'unused','sha256':'c'*64},cell='SCANNER|PREMARKET',mode='prospective'))
    assert calls[0]['required_cell']=='SCANNER|PREMARKET' and calls[0]['require_native'] is True


def test_measured_policy_binding_rejects_wrong_parent_unregistered_candidate_and_wrong_winner():
    from dataclasses import asdict
    from src.engine.scalping import main_stop_experiment as contracts
    from src.tests.test_main_stop_experiment import parameters
    values=parameters();parent=deepcopy(values['candidate_grid']['parent'])
    candidate=deepcopy(values['candidate_grid']['grace_sec:0'])
    # Pure value-binding inputs, with no timing, PASS, or receipt authority.
    measured=dict(baseline_values=parent,candidate_values=candidate)
    contracts._verify_measured_parameters(measured,values,candidate)
    with pytest.raises(ValueError,match='selected_values_not_measured'):
        contracts._verify_measured_parameters(measured,values,parent)
    wrong_parent=deepcopy(measured);wrong_parent['baseline_values']['buffer_pct']=.5
    with pytest.raises(ValueError,match='parent_not_measured'):
        contracts._verify_measured_parameters(wrong_parent,values,candidate)
    unknown=deepcopy(measured);unknown['candidate_values']['buffer_pct']=.5
    with pytest.raises(ValueError,match='candidate_not_preregistered'):
        contracts._verify_measured_parameters(unknown,values,candidate)
    invalid=deepcopy(measured);invalid['candidate_values']['grace_sec']='0'
    with pytest.raises(ValueError,match='stop_policy_'):
        contracts._verify_measured_parameters(invalid,values,candidate)


def test_unmeasured_cell_cannot_reuse_otherwise_native_validator_result(tmp_path,monkeypatch):
    from src.engine.scalping import main_stop_experiment as contracts
    from src.tests.test_main_stop_policy import seal
    # Test only the consumer's cell check, after isolating the expensive native
    # validator. This intentionally incomplete object is not full evidence.
    ref=seal(tmp_path/'coverage-only.json',dict(schema=perf.FULL_SCHEMA,code_sha256='a'*64,
        coverage_cells=['SCANNER|REGULAR']))
    monkeypatch.setattr(perf,'validate_receipt',lambda *args,**kwargs:None)
    with pytest.raises(ValueError,match='cell_not_measured'):
        contracts._verify_performance(ref,'a'*64,mode='prospective',source_sha='b'*64,
            require_native=True,required_cell='SCANNER|PREMARKET')


def test_real_postclose_workload_replays_and_consumes_private_carry_without_performance_bypass(tmp_path):
    import hashlib
    from src.tests.test_main_stop_policy import publication
    from src.engine.automation import main_stop_postclose as post
    source_root=tmp_path/'source'
    bundle,report,parent,source=publication(source_root)
    protected={path:path.read_bytes() for path in (source,post.committed_path(source_root,'2026-10-12'),
        policy.policy_path(source_root,'2026-10-13'))}
    request=dict(data_root=str(source_root),source_date='2026-10-12',target_date='2026-10-13',
        parents={key:cell['parent_values'] for key,cell in bundle['cells'].items()},
        parent_receipt=parent,snapshot_receipt=report['snapshot_receipt'],
        source_files=[dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest())])
    actual=perf._run_postclose_workload(tmp_path/'work',request)
    assert [run['mode'] for run in actual['runs']]==['cold','warm']
    assert all(run['positions']==run['modeled']==4 for run in actual['runs'])
    assert all(run['calls']==dict(prepare=1,publish=1,handoff=1,load_bundle=1) for run in actual['runs'])
    assert actual['selected_policy_published'] is False
    assert all(path.read_bytes()==raw for path,raw in protected.items())
    request['source_files'][0]['sha256']='f'*64
    with pytest.raises(ValueError,match='reference_changed'):
        perf._run_postclose_workload(tmp_path/'changed',request)
    assert not (tmp_path/'changed').exists()


def test_dedicated_guard_validates_dirfd_writes_and_rejects_external_effects(tmp_path):
    import subprocess
    import sys
    scratch=tmp_path/'scratch';scratch.mkdir()
    forbidden=tmp_path/'outside.json'
    script='''
import json,os,socket,sys
from pathlib import Path
from src.engine.automation import main_stop_performance as p
scratch=Path(sys.argv[1]);outside=Path(sys.argv[2])
p._install_full_isolation(scratch,scratch/'receipt.json')
directory=os.open(scratch,os.O_DIRECTORY)
try:
    fd=os.open('native.lock',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory)
    os.write(fd,b'native');os.close(fd)
    os.unlink('native.lock',dir_fd=directory)
finally:os.close(directory)
for action in (lambda:outside.write_text('forbidden'),lambda:socket.socket().connect(('127.0.0.1',1)),
               lambda:socket.getaddrinfo('localhost',80)):
    try:action()
    except RuntimeError:pass
    else:raise AssertionError('effect escaped audit guard')
print(json.dumps(dict(denied=p._FULL_ISOLATION['denied'],data_root=p._LIVE_DATA_ROOT)))
'''
    child=subprocess.run([sys.executable,'-c',script,str(scratch),str(forbidden)],
        text=True,capture_output=True,timeout=30)
    assert child.returncode==0,child.stderr
    result=json.loads(child.stdout.splitlines()[-1])
    assert result['denied']=={'open':1,'socket.connect':1,'socket.getaddrinfo':1}
    assert not forbidden.exists() and not (scratch/'native.lock').exists()


def test_v3_experiment_dispatch_uses_native_validator_without_legacy_pass_fallback(tmp_path,monkeypatch):
    from src.engine.scalping import main_stop_experiment as contracts
    from src.tests.test_main_stop_policy import seal
    reference=seal(tmp_path/'receipt.json',dict(schema=perf.FULL_SCHEMA,code_sha256='a'*64))
    calls=[]
    def reject(body,**kwargs):
        calls.append(kwargs)
        raise ValueError('native_full_evidence_required')
    monkeypatch.setattr(perf,'validate_full_receipt',reject)
    with pytest.raises(ValueError,match='native_full_evidence_required'):
        contracts._verify_performance(reference,'a'*64,mode='prospective',source_sha='b'*64,require_native=True)
    assert calls==[dict(code_sha='a'*64,source_sha='b'*64,require_full=True)]


def test_native_arm_runs_guarded_main_monitor_and_concurrent_postclose_without_forged_full_pass(tmp_path):
    """A fresh cold CLI imports native handlers only after private isolation.

    The small integration exercises mechanics; it is never gate evidence.
    """
    import hashlib
    import subprocess
    import sys
    from src.tests.test_main_stop_policy import publication
    from src.tests.test_main_stop_runtime_workload import _native_scenario
    from dataclasses import asdict
    source_root=tmp_path/'source'
    bundle,report,parent,source=publication(source_root)
    request=dict(data_root=str(source_root),source_date='2026-10-12',target_date='2026-10-13',
        parents={key:cell['parent_values'] for key,cell in bundle['cells'].items()},
        parent_receipt=parent,snapshot_receipt=report['snapshot_receipt'],
        source_files=[dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest())])
    source_bytes={p:p.read_bytes() for p in source_root.rglob('*') if p.is_file()}
    request_path=tmp_path/'request.json';request_path.write_text(json.dumps(request))
    cases_path=tmp_path/'native-inputs.json'
    cases_path.write_text(json.dumps(dict(baseline=asdict(baseline()),
        scenarios=[_native_scenario('normal_first'),_native_scenario('fast_first')])))
    scratch=tmp_path/'scratch';scratch.mkdir()
    script='''
import json,sys
from pathlib import Path
from src.engine.automation import main_stop_performance as p
from src.utils import constants
scratch=Path(sys.argv[1]);request=json.loads(Path(sys.argv[2]).read_text())
inputs=json.loads(Path(sys.argv[3]).read_text())
assert 'src.engine.sniper_state_handlers' not in sys.modules
assert 'src.engine.kiwoom_sniper_v2' not in sys.modules
assert 'src.engine.log_archive_service' not in sys.modules
original_data=str(Path(constants.DATA_DIR).resolve())
p._install_full_isolation(scratch,scratch/'unused-full-receipt.json')
assert p._LIVE_DATA_ROOT==original_data
assert constants.DATA_DIR==scratch/'bootstrap/data'
budget=dict(p.FULL_BUDGET,warmup_samples=2,samples_per_arm_run=8)
run=p._run_full_arm(scratch/'arm',inputs['scenarios'],p.policy.StopValues.parse(inputs['baseline']),request,budget)
from src.engine import log_archive_service
assert log_archive_service.LOG_ARCHIVE_DIR.is_relative_to(scratch)
assert p._LIVE_DATA_ROOT==original_data
(scratch/'raw-arm.json').write_text(json.dumps(run))
assert not (scratch/'unused-full-receipt.json').exists()
print(json.dumps(dict(denied=p._FULL_ISOLATION['denied'])))
'''
    child=subprocess.run([sys.executable,'-c',script,str(scratch),str(request_path),str(cases_path)],
        text=True,capture_output=True,timeout=90)
    assert child.returncode==0,child.stderr[-12000:]
    assert json.loads(child.stdout.splitlines()[-1])['denied']=={}
    run=json.loads((scratch/'raw-arm.json').read_text())
    assert len(run['samples_ns'])==run['calls']['main_cycle']==8
    assert run['calls']['final_guard']>0 and run['calls']['monitor_ws_wake_dispatch']>0
    assert run['drain']['complete'] and run['drain']['loss_count']==0
    assert run['drain']['append_confirmed']==run['drain']['decoded_rows']>0
    assert run['drain']['native']['actual_order_submitted'] is False
    assert all(value==0 for value in run['losses'].values())
    assert len(run['frame_elapsed_ns'])==8 and run['clock_basis']==perf.FULL_CLOCK
    assert run['lock_metric_basis']==perf.LOCK_BASIS
    assert run['warm_rss_growth_bytes']==max(0,run['peak_rss_bytes']-run['warm_rss_bytes'])
    assert run['postclose']['selected_policy_published'] is False
    assert [stage['mode'] for stage in run['postclose']['runs']]==['cold','warm']
    assert all(p.read_bytes()==data for p,data in source_bytes.items())
    assert {p for p in source_root.rglob('*') if p.is_file()}==set(source_bytes)
