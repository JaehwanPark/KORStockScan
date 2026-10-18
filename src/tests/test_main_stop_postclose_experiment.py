"""Normal publisher consumes real experiment producers and checks native rows."""
from dataclasses import asdict
import json

import pytest

from src.engine.automation import main_stop_postclose as post
from src.engine.scalping import main_stop_experiment as experiment
from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_replay import candidates
from src.tests.test_main_stop_policy import baseline, publication, seal


def prepared(tmp_path, monkeypatch, *, observed_start_delta=0, mode='prospective'):
    _, report, parent, source = publication(tmp_path)
    base=1791766800.;value=baseline()
    params=dict(parent_sha256=policy.digest(asdict(value)),code_sha256=post.code_sha(),
        operator_lock_sha256=policy.digest([]),allowed_keys=['grace_sec'],
        max_daily_change={'grace_sec':60},split_at=base+500,embargo_sec=60.,min_train=2,min_holdout=2,
        minimum_paired_ev_krw=0.,max_censoring_ratio=0.,max_standard_error_krw=0.,
        candidate_grid={k:asdict(v) for k,v in candidates(value).items() if k=='parent' or k.startswith('grace_sec:')},
        source_start_at=base,source_end_at=base+1108,hypothesis='Fixed test comparison of a known adverse path.')
    monkeypatch.setattr(experiment,'_clock',lambda:base-100 if mode=='prospective' else base+1300)
    registered=experiment.register_experiment(tmp_path/'experiments',experiment_id='native-grace',revision=1,
        cell='SCANNER|REGULAR',parameters=params,mode=mode)
    # Gate fixture only; the separately executed research harness produces real
    # offline measurements and does not claim this unit fixture is live PASS.
    performance=dict(schema='main_stop_performance_v1',code_sha256=post.code_sha(),
        status='pass',scope='runtime_and_postclose',unresolved_findings=[])
    if mode=='historical_report_only':
        performance.update(status='measured',scope='offline_research_and_pure_decisions',
            allowed_runtime_apply=False,source_sha256=report['source_sha256'],metrics={'rows':36})
    measured=seal(tmp_path/'performance.json',performance)
    monkeypatch.setattr(experiment,'_clock',lambda:base+1400)
    if mode=='prospective':
        # This legacy artifact fixture verifies downstream numeric/loader
        # contracts only. Native performance authority has separate negatives.
        from src.tests.test_main_stop_experiment import isolate_legacy_performance_gate
        isolate_legacy_performance_gate(monkeypatch)
    contract=experiment.finalize_experiment(tmp_path/'experiments',registered,
        source_inventory=report['source_inventory'],performance_receipt=measured,
        observed_start_at=base+observed_start_delta,observed_end_at=base+1108)
    return report,parent,source,contract


def republish(tmp_path, report,parent,source,contract):
    completed=json.loads((tmp_path/'costs.json').read_text())['rows']
    return post.publish(tmp_path,'2026-10-12','2026-10-13',
        parents={f'{r}|{m}':baseline() for r in policy.ROLES for m in policy.MARKETS},
        parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'],
        experiments={'SCANNER|REGULAR':contract},completed=completed,economic_sources=report['economic_sources'])


def test_v2_producer_contract_reaches_normal_publisher_and_exact_changed_cell(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    bundle,result=republish(tmp_path,report,parent,source,contract)
    assert bundle['cells']['SCANNER|REGULAR']['status']=='selected'
    assert bundle['cells']['SCANNER|REGULAR']['values']['grace_sec']==0
    assert sum(c['status']=='selected' for c in bundle['cells'].values())==1
    env,_=post.handoff(tmp_path,'2026-10-13')
    policy.preload(env)
    try:
        pin=policy.pin(position_key='target:999:005930',role='SCANNER',market='REGULAR',
            target='2026-10-13',baseline=baseline())
        assert policy.pin_values(pin,'target:999:005930').grace_sec==0
    finally:policy.preload({})


def test_native_v2_routine_reader_and_loader_reuse_sealed_sources_but_preflight_reads_bytes(tmp_path,monkeypatch):
    from src.engine.lifecycle import holding_window_generation as generation
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    republish(tmp_path,report,parent,source,contract)
    native=generation.byte_generation
    reads=[]
    def observe(path,*args,**kwargs):
        if str(path)==str(source):reads.append(str(path))
        return native(path,*args,**kwargs)
    monkeypatch.setattr(generation,'byte_generation',observe)
    monkeypatch.setattr(post,'byte_generation',observe)
    post.read_committed(tmp_path,'2026-10-12')
    env,_=post.handoff(tmp_path,'2026-10-13')
    policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE])
    policy.preload(env)
    try:
        pin=policy.pin(position_key='record:1001',role='SCANNER',market='REGULAR',
            target=env[policy.ENV_DATE],baseline=baseline())
        assert policy.pin_values(pin,'record:1001').grace_sec==0
    finally:policy.preload({})
    assert reads==[]
    post.read_committed(tmp_path,'2026-10-12',verify_full=True)
    assert reads


@pytest.mark.parametrize('mutation',['same_size_replace','new_source','source_removed'])
def test_native_v2_loader_rejects_source_identity_or_catalog_change(tmp_path,monkeypatch,mutation):
    import os
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    republish(tmp_path,report,parent,source,contract)
    env,_=post.handoff(tmp_path,'2026-10-13')
    if mutation=='same_size_replace':
        before=source.stat();raw=source.read_bytes();replacement=source.with_suffix('.replacement')
        replacement.write_bytes(raw)
        os.utime(replacement,ns=(before.st_atime_ns,before.st_mtime_ns))
        replacement.replace(source)
    elif mutation=='new_source':
        source.with_name('pipeline_events_2026-10-12.late.jsonl').write_text('{}\n')
    else:source.unlink()
    with pytest.raises((ValueError,FileNotFoundError),match='source|No such file'):
        policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE])


@pytest.mark.parametrize('damage',[None,'receipt_removed','archive_changed'])
def test_v2_native_archive_loader_preserves_logical_source_without_routine_decode(tmp_path,monkeypatch,damage):
    from pathlib import Path
    from src.engine.compress_db_backfilled_files import _gzip_file
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    republish(tmp_path,report,parent,source,contract)
    env,_=post.handoff(tmp_path,'2026-10-13')
    assert _gzip_file(source,dry_run=False)[0] is True
    archive=Path(str(source)+'.gz')
    if damage=='receipt_removed':Path(str(archive)+'.archive_receipt.json').unlink()
    elif damage=='archive_changed':archive.write_bytes(archive.read_bytes()+b'\n')
    original=post._vote_watch_content;reads=[]
    def decode(path,**kwargs):
        if path==archive:reads.append(str(path))
        return original(path,**kwargs)
    monkeypatch.setattr(post,'_vote_watch_content',decode)
    if damage:
        with pytest.raises((ValueError,OSError)):
            policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE])
        assert not reads
    else:
        policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE])
        assert not reads
        post.read_committed(tmp_path,'2026-10-12',verify_full=True)
        assert len(reads)==1


def test_approved_code_handoff_semantics_run_inside_native_source_context(tmp_path,monkeypatch):
    from src.engine.automation import intraday_release_handoff as handoff
    publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    monkeypatch.setattr(policy,'implementation_sha',lambda:'e'*64)
    seen=[]
    def verify(day,**kwargs):
        assert experiment._PUBLISHED_SOURCES.get()
        seen.append(day)
        return dict(status='verified_intraday_consumer_repair',policy_effect='unchanged',
            policy_sha256=kwargs['policy_sha'],code_contract_sha256=kwargs['expected'],
            runtime_code_contract_sha256=kwargs['actual'])
    monkeypatch.setattr(handoff,'verify_entry_consumer_code',verify)
    policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE])
    assert seen==['2026-10-13']
    with pytest.raises(ValueError,match='code_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12',verify_full=True)


def test_claimed_source_bounds_cannot_replace_actual_consumed_position_bounds(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch,observed_start_delta=1)
    before=post.committed_path(tmp_path,'2026-10-12').read_bytes()
    with pytest.raises(ValueError,match='observed_window_unverified'):
        republish(tmp_path,report,parent,source,contract)
    assert post.committed_path(tmp_path,'2026-10-12').read_bytes()==before


def test_historical_real_registration_has_no_normal_policy_publication_authority(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch,mode='historical_report_only')
    before=post.committed_path(tmp_path,'2026-10-12').read_bytes()
    with pytest.raises(ValueError,match='historical_experiment_report_only'):
        republish(tmp_path,report,parent,source,contract)
    assert post.committed_path(tmp_path,'2026-10-12').read_bytes()==before


def native_grade_case(tmp_path,monkeypatch,*,grade='broker_total_allocated',missing_record=None):
    """Native fill/custody/cost/stage producers; only full perf gate is isolated.

    This fixture tests publisher economics, not full Main performance approval.
    The measured capture receipt remains blocked outside this test boundary.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine import sniper_execution_receipts
    from src.engine.automation import main_stop_performance as perf
    from src.engine.lifecycle import main_stop_research_cost as costs
    from src.engine.scalping.position_peak_ledger import position_cycle_id
    from src.tests import test_main_stop_research_cost as native
    from src.tests.test_main_stop_runtime_source import research_quote,research_evaluation
    from src.tests.test_main_stop_performance import scenario
    root=tmp_path/'native';root.mkdir()
    day=native.DAY;target='2026-10-09';base=datetime.fromisoformat(day+'T10:00:00+09:00').timestamp()
    offsets={1:0,2:100,3:1000,4:1100}
    def stamp(at):return datetime.fromtimestamp(at,ZoneInfo('Asia/Seoul')).isoformat()
    positions=[];population=[]
    for record,offset in offsets.items():
        at=base+offset;item=native.position(record,qty=10)
        item['custody_rows'][0]['record_id']=item['record_id']
        item['buy_legs'][0]['at']=stamp(at-1)
        item['sell_legs'][0]['at']=stamp(at+9);item['completed_at']=stamp(at+9)
        positions.append(item)
        order=str(record*10+1)
        stock=dict(id=record,code='005930',strategy='SCALPING',entry_requested_qty=10,requested_buy_qty=10,
            pending_entry_orders=[dict(ord_no=order,qty=10,filled_qty=0,status='OPEN')])
        result=sniper_execution_receipts._resolve_entry_effective_fill_qty(target_stock=stock,code='005930',
            order_no=order,exec_price=10000,exec_qty=10,order_qty=10,remaining_qty=0,
            cumulative_exec_amount=100000,execution_no=str(record*100+1),unit_exec_qty=10,unit_exec_price=10000)
        assert result['status']!='invalid'
        stock.update(buy_qty=10,buy_price=10000.,status='HOLDING')
        stock['main_stop_policy_pin']=policy.pin(position_key=position_cycle_id(stock),role='SCANNER',
            market='REGULAR',target=day,baseline=baseline())
        for n in range(9):
            bid=9990 if n<2 else 9650 if n<6 else 9580
            quote=research_quote(stock,at=at+n,bid=bid,profit=round((bid*10*.999-100010)/100000*100,2),
                cost=dict(buy_cost_krw=10.,sell_cost_rate=.001,known_at=at-10,source_sha256='a'*64))
            population.extend((quote,research_evaluation(stock,quote)))
    def fix_clock(row):
        at=base+offsets[row['id']]
        row.update(buy_qty=10,buy_filled_qty=10,sell_filled_qty=10,buy_fill_amount=100000,sell_fill_amount=101000)
        signal=row['exit_signal'];signal['fields']['exit_signal_contract']['signal_at']=stamp(at+8)
        signal['fields']['exit_signal_contract_sha256']=policy.digest(signal['fields']['exit_signal_contract'])
        signal['submission']['submitted_at']=stamp(at+8)
        if row['id']==missing_record:row['exit_signal']={}
    native.native(root,positions,mutate=fix_clock);native.registry(root,positions)
    observed=native.source(root,buy_qty=40,sell_qty=40,buy_amount=400000,sell_amount=404000,cost=80)
    native.official.atomic(native.official.source_path(root,day),observed)
    receipts=native.allocation.build_research_cost_allocations({day:observed},positions)
    native.allocation.persist_research_costs(root,day,receipts,[day])
    source=root/'pipeline_events'/f'pipeline_events_{day}.jsonl';source.parent.mkdir()
    source.write_text(''.join(json.dumps(dict(stage='main_stop_source',fields={'main_stop_source':row}))+'\n' for row in population))
    parent=seal(root/'parent.json',{'values':asdict(baseline())});snapshot=seal(root/'snapshot.json',{'date':day})
    inventory={str(source):post.byte_generation(source)}
    params=dict(parent_sha256=policy.digest(asdict(baseline())),code_sha256=post.code_sha(),
        operator_lock_sha256=policy.digest([]),allowed_keys=['grace_sec'],max_daily_change={'grace_sec':60},
        split_at=base+500,embargo_sec=60.,min_train=2,min_holdout=2,minimum_paired_ev_krw=0.,
        max_censoring_ratio=0.,max_standard_error_krw=0.,selection_cost_grade=grade,
        candidate_grid={k:asdict(v) for k,v in candidates(baseline()).items() if k=='parent' or k.startswith('grace_sec:')},
        source_start_at=base,source_end_at=base+1108,hypothesis='Test native grade consumer on an adverse path.')
    if grade is None:params.pop('selection_cost_grade')
    monkeypatch.setattr(experiment,'_clock',lambda:base-100)
    ref=experiment.register_experiment(root/'experiments',experiment_id='native-grade',revision=1,
        cell='SCANNER|REGULAR',parameters=params)
    _,performance=perf.measure_capture_pair(root/'capture-performance.json',scenarios=[scenario()],
        baseline=baseline(),candidate=baseline(),source_sha256=policy.digest(inventory))
    verify=experiment._verify_performance
    def isolated_performance(reference,code_sha,*,mode,source_sha,require_native=False):
        return verify(reference,code_sha,mode='historical_report_only',source_sha=source_sha,require_native=False)
    monkeypatch.setattr(experiment,'_verify_performance',isolated_performance)
    monkeypatch.setattr(experiment,'_clock',lambda:base+1200)
    contract=experiment.finalize_experiment(root/'experiments',ref,source_inventory=inventory,
        performance_receipt=performance,observed_start_at=base,observed_end_at=base+1108)
    kwargs=dict(parents={f'{r}|{m}':baseline() for r in policy.ROLES for m in policy.MARKETS},
        parent_receipt=parent,source_paths=[source],snapshot_receipt=snapshot,experiments={'SCANNER|REGULAR':contract})
    return root,day,target,kwargs


def test_native_allocated_grade_reaches_normal_selector_publisher_loader_without_actual_relabel(tmp_path,monkeypatch):
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch)
    bundle,report=post.publish(root,day,target,**kwargs)
    cell=bundle['cells']['SCANNER|REGULAR']
    assert cell['status']=='selected',[(x['economic_source_status'],x['economic_source_reason'],x['economic_grade']) for x in report['examples']]
    evidence=cell['selection_evidence']['cost_selection']
    assert evidence['selection_cost_grade']=='broker_total_allocated'
    assert evidence['actual_profit_claimed'] is False
    for row in evidence['aggregates_by_grade']['broker_total_allocated'].values():
        assert row['train_n']==row['holdout_n']==row['train_total']==row['holdout_total']==2
    assert all(row['train_n']==row['holdout_n']==0
        for row in evidence['aggregates_by_grade']['exact_execution'].values())
    assert all(x['actual_execution_cost'] is False for x in report['examples'])
    env,_=post.handoff(root,target);policy.preload(env)
    try:
        pinned=policy.pin(position_key='target:999:005930',role='SCANNER',market='REGULAR',target=target,baseline=baseline())
        assert policy.pin_values(pinned,'target:999:005930').grace_sec==0
    finally:policy.preload({})


@pytest.mark.parametrize('fault',['other_grade','unknown_source'])
def test_normal_grade_denominator_does_not_pool_other_grade_or_drop_unknown_source(tmp_path,monkeypatch,fault):
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch,
        grade='exact_execution' if fault=='other_grade' else 'broker_total_allocated',
        missing_record=4 if fault=='unknown_source' else None)
    bundle,_=post.publish(root,day,target,**kwargs)
    cell=bundle['cells']['SCANNER|REGULAR']
    assert cell['status']=='hold_sample'
    grade=cell['selection_evidence']['cost_selection']['selection_cost_grade']
    stats=cell['selection_evidence']['cost_selection']['aggregates_by_grade'][grade]
    assert all(x['holdout_total']==2 for x in stats.values())
    assert all(x['holdout_n']==(0 if fault=='other_grade' else 1) for x in stats.values())


def test_late_native_cost_revision_invalidates_selection_and_reuses_price_replay(tmp_path,monkeypatch):
    from src.engine.lifecycle import main_stop_research_cost as costs
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch)
    first,report=post.publish(root,day,target,**kwargs)
    raw=root/'report/monitor_snapshots'/f'trade_review_{day}.completed_projection.json'
    original=raw.read_bytes()
    # A semantically unchanged but byte-distinct official receipt still has a
    # new native source generation. No previous selection receipt can hide it.
    source=costs.official.source_path(root,day)
    source.write_bytes(source.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='cost_generation_changed'):
        post.read_committed(root,day)
    def forbidden(*args,**kwargs):raise AssertionError('cost-only change replayed unchanged prices')
    monkeypatch.setattr(post,'replay',forbidden)
    second,new=post.publish(root,day,target,**kwargs)
    assert first['research_sha256']!=second['research_sha256']
    assert second['cells']['SCANNER|REGULAR']['status']=='selected'
    assert second['cells']['SCANNER|REGULAR']['selection_evidence']['aggregates']==first['cells']['SCANNER|REGULAR']['selection_evidence']['aggregates']
    assert raw.read_bytes()==original


@pytest.mark.parametrize('name',['pipeline_events_2026-10-08.bad.jsonl','anything_2026-10-08.jsonl','pipeline_events_2026-10-18.jsonl'])
def test_native_cost_date_partition_is_validated_before_any_publication(tmp_path,name):
    with pytest.raises(ValueError,match='partition_invalid'):
        post.source_dates(tmp_path,[tmp_path/'pipeline_events'/name],'2026-10-09')
    assert post.source_dates(tmp_path,[tmp_path/'pipeline_events/pipeline_events_2026-10-08.late.jsonl.gz'],
                             '2026-10-09')==['2026-10-08']


def private_preparation(tmp_path,monkeypatch):
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch)
    contracts=kwargs['experiments']
    inputs={key:experiment.prepare_experiment(c['preregistration'],c['source_seal']) for key,c in contracts.items()}
    ready,ref=post.prepare_policy_candidate(root,day,target,output_root=tmp_path/'preparation',
        **dict(kwargs,experiments=inputs))
    return root,day,target,kwargs,contracts,ready,ref


@pytest.mark.parametrize('archived',[False,True])
def test_private_preparation_and_final_commit_share_native_results_without_replay(tmp_path,monkeypatch,archived):
    root,day,target,kwargs,contracts,ready,ref=private_preparation(tmp_path,monkeypatch)
    assert ready['schema']=='main_stop_policy_preparation_v1'
    assert ready['cells']['SCANNER|REGULAR']['status']=='selected'
    assert all(cell['authority']=={} for cell in ready['cells'].values())
    assert not post.committed_path(root,day).exists()
    assert not policy.policy_path(root,target).exists()
    if archived:
        from src.engine.compress_db_backfilled_files import _gzip_file
        assert _gzip_file(kwargs['source_paths'][0],dry_run=False)[0] is True
    def no_replay(*args,**kwargs):raise AssertionError('prepared selection replayed')
    monkeypatch.setattr(post,'replay',no_replay)
    bundle,_=post.commit_prepared_policy(root,ref,experiments=contracts)
    selected=bundle['cells']['SCANNER|REGULAR']
    assert selected['values']==ready['cells']['SCANNER|REGULAR']['values']
    assert selected['selection_evidence']['aggregates']==ready['cells']['SCANNER|REGULAR']['selection_evidence']['aggregates']
    env,_=post.handoff(root,target)
    assert policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],target)==bundle


@pytest.mark.parametrize('mutation',['source','cost','result','contract'])
def test_prepared_final_commit_rejects_changed_inputs_or_results_before_publication(tmp_path,monkeypatch,mutation):
    from copy import deepcopy
    from pathlib import Path
    root,day,target,kwargs,contracts,ready,ref=private_preparation(tmp_path,monkeypatch)
    if mutation=='source':
        kwargs['source_paths'][0].write_bytes(kwargs['source_paths'][0].read_bytes()+b'\n')
    elif mutation=='cost':
        from src.engine.lifecycle import main_stop_research_cost as costs
        path=costs.official.source_path(root,day);path.write_bytes(path.read_bytes()+b'\n')
    elif mutation=='contract':
        contracts=deepcopy(contracts)
        contracts['SCANNER|REGULAR']['min_holdout']=3
        c=contracts['SCANNER|REGULAR'];c['experiment_sha256']=policy.digest({k:v for k,v in c.items() if k!='experiment_sha256'})
    else:
        ready=deepcopy(ready);ready['cells']['SCANNER|REGULAR']['values']['grace_sec']=30
        ready['preparation_sha256']=policy.digest({k:v for k,v in ready.items() if k!='preparation_sha256'})
        ref=experiment._write_immutable(Path(ref['path']).with_name('damaged.json'),ready,'preparation_sha256')
    with pytest.raises(ValueError):post.commit_prepared_policy(root,ref,experiments=contracts)
    assert not post.committed_path(root,day).exists()
    assert not policy.policy_path(root,target).exists()


def test_preparation_does_not_require_performance_but_final_commit_does(tmp_path,monkeypatch):
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch)
    contracts=kwargs['experiments']
    inputs={key:experiment.prepare_experiment(c['preregistration'],c['source_seal']) for key,c in contracts.items()}
    def unavailable(*args,**kwargs):raise ValueError('full_performance_still_unmeasured')
    monkeypatch.setattr(experiment,'_verify_performance',unavailable)
    # Preserve unrelated native aliases and committed state byte for byte.
    sentinels=[post.committed_path(root,day),policy.policy_path(root,target),post.report_path(root,day)]
    for path in sentinels:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('preserve original evidence\n')
    before={path:path.read_bytes() for path in sentinels}
    ready,ref=post.prepare_policy_candidate(root,day,target,output_root=tmp_path/'preparation',
        **dict(kwargs,experiments=inputs))
    assert ready['status']=='prepared_report_only'
    assert all(path.read_bytes()==raw for path,raw in before.items())
    with pytest.raises(ValueError,match='full_performance_still_unmeasured'):
        post.commit_prepared_policy(root,ref,experiments=contracts)
    assert all(path.read_bytes()==raw for path,raw in before.items())


@pytest.mark.parametrize('missing_reference',[False,True])
def test_existing_legacy_selected_artifact_reads_but_cannot_grant_new_numeric_authority(tmp_path,missing_reference):
    from copy import deepcopy
    bundle,report,_,_=publication(tmp_path,experiment=True)
    # Original approved artifacts retain exactly their old reader semantics.
    env,_=post.handoff(tmp_path,'2026-10-13')
    assert policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],'2026-10-13')==bundle
    protected=[post.committed_path(tmp_path,'2026-10-12'),policy.policy_path(tmp_path,'2026-10-13'),
               post.report_path(tmp_path,'2026-10-12')]
    before={path:path.read_bytes() for path in protected}
    cells=deepcopy(bundle['cells'])
    if missing_reference:cells['SCANNER|REGULAR']['selection_evidence']['experiment'].pop('performance_receipt')
    research={k:v for k,v in report.items() if k not in {'research_sha256','status','policy_sha256','report_sha256'}}
    directory=tmp_path/'threshold_cycle/main_stop_confirmation/generations'/('f'*64)
    with pytest.raises(ValueError,match='publication_experiment_unverified|native_producer_required'):
        post._commit_candidate(tmp_path,'2026-10-12','2026-10-13',directory,'f'*64,
            research,cells,bundle['operator_sources'])
    assert not directory.exists()
    assert all(path.read_bytes()==raw for path,raw in before.items())


@pytest.mark.parametrize('grade',[None,'exact_execution','broker_total_allocated'])
def test_new_prospective_and_selected_gate_reject_real_capture_only_measurement(tmp_path,monkeypatch,grade):
    original=experiment._verify_performance
    root,day,target,kwargs=native_grade_case(tmp_path,monkeypatch,grade=grade)
    contract=kwargs['experiments']['SCANNER|REGULAR']
    monkeypatch.setattr(experiment,'_verify_performance',original)
    seal,_=post.bounded(contract['source_seal']['path'])
    with pytest.raises(ValueError,match='full_runtime_unmeasured'):
        experiment.finalize_experiment(root/'experiments',contract['preregistration'],
            source_inventory=seal['source_inventory'],performance_receipt=contract['performance_receipt'],
            observed_start_at=seal['observed_start_at'],observed_end_at=seal['observed_end_at'])
    with pytest.raises(ValueError,match='full_runtime_unmeasured'):
        experiment.require_native_publication_performance(contract)
    assert not post.committed_path(root,day).exists()


def test_legacy_no_selection_preparation_carries_parent_without_new_performance_gate(tmp_path,monkeypatch):
    report,parent,source,contract=prepared(tmp_path,monkeypatch)
    # Freeze a second legacy-compatible acceptance contract with no economic
    # winner. Its archived performance validator remains valid for carry.
    registered,_=post.bounded(contract['preregistration']['path'])
    params=dict(registered['parameters'],minimum_paired_ev_krw=100000.)
    monkeypatch.setattr(experiment,'_clock',lambda:registered['frozen_at'])
    ref=experiment.register_experiment(tmp_path/'experiments',experiment_id='no-edge',revision=1,
        cell='SCANNER|REGULAR',parameters=params)
    monkeypatch.setattr(experiment,'_clock',lambda:params['source_end_at']+100.)
    oldseal,_=post.bounded(contract['source_seal']['path'])
    carried=experiment.finalize_experiment(tmp_path/'experiments',ref,source_inventory=report['source_inventory'],
        performance_receipt=contract['performance_receipt'],observed_start_at=oldseal['observed_start_at'],
        observed_end_at=oldseal['observed_end_at'])
    inp=experiment.prepare_experiment(carried['preregistration'],carried['source_seal'])
    completed=json.loads((tmp_path/'costs.json').read_text())['rows']
    ready,reference=post.prepare_policy_candidate(tmp_path,'2026-10-12','2026-10-13',
        output_root=tmp_path.with_name(tmp_path.name+'-private'),
        parents={f'{r}|{m}':baseline() for r in policy.ROLES for m in policy.MARKETS},parent_receipt=parent,
        source_paths=[source],snapshot_receipt=report['snapshot_receipt'],experiments={'SCANNER|REGULAR':inp},
        completed=completed,economic_sources=report['economic_sources'])
    assert ready['cells']['SCANNER|REGULAR']['status']=='hold_no_edge'
    # If new numeric authority were consulted for a carry this sentinel fails.
    monkeypatch.setattr(experiment,'require_native_publication_performance',
        lambda *a,**k:pytest.fail('baseline carry acquired new numeric performance gate'))
    bundle,_=post.commit_prepared_policy(tmp_path,reference,experiments={'SCANNER|REGULAR':carried})
    assert all(cell['status']!='selected' and cell['values']==cell['parent_values'] for cell in bundle['cells'].values())
